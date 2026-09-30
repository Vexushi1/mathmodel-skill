"""C2 guards the existing submission gates without changing legacy projects."""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml

from tests.test_sync_project import setup_project

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import sync_project as SYNC
import validate_submission_package as PACKAGE


class C2SubmissionGateTests(unittest.TestCase):
    @staticmethod
    def _activate(root: Path) -> bytes:
        path = root / "state/project_state.yaml"
        state = yaml.safe_load(path.read_text(encoding="utf-8"))
        state["review_receipt_policy"] = {
            "protocol_version": "1.0.0", "mode": "enforce_scoped",
            "requirements": [{"gate": "final_review_and_delivery", "questions": ["Q1"],
                              "object_ids": ["final_latex/main.tex"],
                              "roles": [{"role": "semantic_reviewer", "check_ids": ["fit"]},
                                        {"role": "adversarial_reviewer", "check_ids": ["fit"]}]}],
        }
        path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
        return path.read_bytes()

    @staticmethod
    def _failed_gate() -> dict:
        return {"status": "failed", "issues": ["required final review is stale"],
                "receipt_ids": [], "coverage_boundary": "declared_scope_only",
                "observed_sources": {"project": {}, "skill": {}}}

    def test_submission_sync_consumes_opt_in_final_review_and_does_not_write_on_failure(self):
        sync = SYNC
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            setup_project(root, status="designed")
            state_bytes = self._activate(root)
            with patch("review_receipt_consumption.evaluate_gate", return_value=self._failed_gate()) as gate:
                report = sync.synchronize(root, write=True, delivery_scope="submission")
            gate.assert_called_once()
            self.assertEqual(report["review_receipt_gate"]["status"], "failed")
            self.assertTrue(any("required final review is stale" in issue for issue in report["issues"]))
            self.assertEqual((root / "state/project_state.yaml").read_bytes(), state_bytes)

    def test_legacy_submission_sync_does_not_require_receipts(self):
        sync = SYNC
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            setup_project(root, status="designed")
            with patch("review_receipt_consumption.evaluate_gate") as gate:
                report = sync.synchronize(root, write=False, delivery_scope="submission")
            gate.assert_not_called()
            self.assertNotIn("review_receipt_gate", report)

    def test_undeclared_final_gate_retains_the_original_submission_write_path(self):
        sync = SYNC
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            setup_project(root, status="designed")
            self._activate(root)
            state_path = root / "state/project_state.yaml"
            state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
            requirement = state["review_receipt_policy"]["requirements"][0]
            requirement["gate"] = "model_challenge"
            requirement["object_ids"] = ["Q1:model"]
            challenge = yaml.safe_load((ROOT / "core/model_approval_contract.yaml").read_text(encoding="utf-8"))
            requirement["roles"] = [
                {"role": challenge["model_challenge"][name]["role"],
                 "check_ids": challenge["model_challenge"][name]["must_check"]}
                for name in ("reviewer_pass", "devils_advocate_pass")
            ]
            state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
            not_assessed = {"status": "not_assessed", "issues": [], "receipt_ids": [],
                            "coverage_boundary": "declared_scope_only",
                            "observed_sources": {"project": {}, "skill": {}}}
            with patch("review_receipt_consumption.evaluate_gate", return_value=not_assessed):
                report = sync.synchronize(root, write=True, delivery_scope="submission")
            self.assertTrue(report["write"])
            self.assertEqual(report["review_receipt_gate"]["status"], "not_assessed")

    def test_final_pass_replays_submission_without_rewriting_reviewed_files(self):
        sync = SYNC
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            setup_project(root, status="designed")
            sync.synchronize(root, write=True, delivery_scope="design")
            self._activate(root)
            state_path = root / "state/project_state.yaml"
            watched = [state_path, root / "模型论文框架.md", root / "sync_report.yaml"]
            before = {path: path.read_bytes() for path in watched}
            receipt_pass = {"status": "passed", "issues": [], "receipt_ids": ["R1", "R2"],
                            "coverage_boundary": "declared_scope_only", "selected_snapshots": [],
                            "observed_sources": {"project": {}, "skill": {}}}
            with patch("review_receipt_consumption.evaluate_gate", return_value=receipt_pass):
                report = sync.synchronize(root, write=True, delivery_scope="submission")
            self.assertFalse(report["write"])
            self.assertTrue(report["write_requested"])
            self.assertEqual(report["review_receipt_gate"]["status"], "passed")
            self.assertEqual({path: path.read_bytes() for path in watched}, before)

    def test_final_read_only_replay_rejects_source_changed_after_observation(self):
        sync = SYNC
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            setup_project(root, status="designed")
            state_before = self._activate(root)
            receipt_pass = {"status": "passed", "issues": [], "receipt_ids": ["R1", "R2"],
                            "coverage_boundary": "declared_scope_only", "selected_snapshots": [],
                            "observed_sources": {"project": {}, "skill": {}}}

            def change_input_after_observation(*_args):
                (root / "input.json").write_text('{"changed": true}', encoding="utf-8")

            with (patch("review_receipt_consumption.evaluate_gate", return_value=receipt_pass),
                  patch.object(sync.CONFORMANCE, "assert_observed", side_effect=change_input_after_observation)):
                with self.assertRaises(sync.PROJECT_TX.ReadSetConflictError):
                    sync.synchronize(root, write=True, delivery_scope="submission")
            self.assertEqual((root / "state/project_state.yaml").read_bytes(), state_before)

    def test_direct_package_validation_rechecks_opt_in_final_review(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "state").mkdir()
            state_path = root / "state/project_state.yaml"
            state_path.write_text(yaml.safe_dump({"subproblems": {"Q1": {}},
                                                  "review_receipt_policy": {
                                                      "protocol_version": "1.0.0",
                                                      "mode": "enforce_scoped", "requirements": []}},
                                                 sort_keys=False), encoding="utf-8")
            state_hash = hashlib.sha256(state_path.read_bytes()).hexdigest()
            claim_gate = {"status": "failed", "issues": ["unrelated missing claim proof"],
                          "observed_sources": {"project": {"state/project_state.yaml": state_hash},
                                               "skill": {}}}
            with (patch("claim_consumption.formal_text_gate", return_value=claim_gate),
                  patch("review_receipt_consumption.evaluate_gate", return_value=self._failed_gate()) as gate):
                report = PACKAGE.validate_package(root, root / "submission/missing.zip")
            gate.assert_called_once()
            self.assertEqual(report["status"], "failed")
            self.assertTrue(any("required final review is stale" in issue for issue in report["issues"]))


if __name__ == "__main__":
    unittest.main()
