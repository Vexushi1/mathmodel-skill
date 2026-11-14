"""P4: per-question research snapshots bind actual raw project sources, not state authority."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import literature_snapshot as SNAP


class LiteratureSnapshotTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "Q1_problem_contract.md").write_text(
            "Q1: cylindrical diffusion problem contract; variables and boundary assumptions are frozen.",
            encoding="utf-8")
        self.report = {
            "protocol_version": "1.0.0",
            "scope": {
                "mode": "model_design",
                "question": "Q1", "problem_contract_status": "frozen",
                "problem_contract_anchor": "Q1_problem_contract.md#Q1",
                "independent_problem_structure": "Model a cylindrical conservation equation with its boundary.",
                "research_questions": ["Which original method conditions are applicable?"],
            },
            "search": {
                "depth": "targeted", "status": "unavailable",
                "attempts": [], "stop_reason": "No external search available",
            },
            "sources": [], "methods": [],
            "decision": {
                "evidence_status": "insufficient",
                "independent_model_reasoning": "The equation must be derived from the task's actual boundary.",
                "unresolved_gaps": ["External physical parameters have not been verified"],
            },
        }
        (self.root / "research.json").write_text(
            json.dumps(self.report, ensure_ascii=False), encoding="utf-8")

    def preview(self):
        return SNAP.preview(
            self.root, "Q1", "Q1_problem_contract.md", "research.json")

    def commit(self):
        before = self.preview()
        return SNAP.record(
            self.root, "Q1", "Q1_problem_contract.md", "research.json",
            expected_contract_sha256=before["contract"]["sha256"],
            expected_report_sha256=before["report_source"]["sha256"],
            write=True,
        )

    def test_preview_readonly_then_explicit_commit_and_current_inspection(self):
        before = {p.name: p.read_bytes() for p in self.root.iterdir() if p.is_file()}
        preview = self.preview()
        self.assertFalse(preview["target_exists"])
        self.assertEqual(preview["model_approval"], "not_granted")
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir() if p.is_file()})
        self.assertFalse((self.root / "research_evidence").exists())
        result = self.commit()
        self.assertEqual(result["status"], "recorded")
        snapshot = self.root / "research_evidence/Q1.snapshot.json"
        self.assertTrue(snapshot.is_file())
        inspection = SNAP.inspect(self.root, "Q1")
        self.assertEqual(inspection["status"], "current", inspection["issues"])
        self.assertEqual(inspection["citation_candidates"], [])
        self.assertEqual(inspection["source_authenticity"], "not_assessed")
        self.assertEqual(inspection["model_approval"], "not_granted")
        self.assertFalse((self.root / "state/project_state.yaml").exists())
        self.assertFalse((self.root / "模型论文框架.md").exists())

    def test_contract_changed_or_missing_is_stale_without_implicit_model_change(self):
        self.commit()
        (self.root / "Q1_problem_contract.md").write_text("Changed the task boundary.", encoding="utf-8")
        item = SNAP.inspect(self.root, "Q1")
        self.assertEqual(item["status"], "stale")
        self.assertIn("contract_changed", item["issues"])
        self.assertFalse(item["state_write"])
        (self.root / "Q1_problem_contract.md").unlink()
        item = SNAP.inspect(self.root, "Q1")
        self.assertIn("contract_missing_or_invalid", item["issues"])

    def test_report_changed_or_missing_is_stale(self):
        self.commit()
        (self.root / "research.json").write_text("{}", encoding="utf-8")
        self.assertIn("report_source_changed", SNAP.inspect(self.root, "Q1")["issues"])
        (self.root / "research.json").unlink()
        self.assertIn("report_source_missing_or_invalid", SNAP.inspect(self.root, "Q1")["issues"])

    def test_read_set_guard_and_no_overwrite(self):
        preview = self.preview()
        (self.root / "Q1_problem_contract.md").write_text("Different assumptions.", encoding="utf-8")
        with self.assertRaisesRegex(SNAP.SnapshotError, "source_read_set_changed"):
            SNAP.record(
                self.root, "Q1", "Q1_problem_contract.md", "research.json",
                expected_contract_sha256=preview["contract"]["sha256"],
                expected_report_sha256=preview["report_source"]["sha256"],
                write=True,
            )
        self.assertFalse((self.root / "research_evidence").exists())
        self.commit()
        snapshot = self.root / "research_evidence/Q1.snapshot.json"
        old = snapshot.read_bytes()
        with self.assertRaisesRegex(SNAP.SnapshotError, "snapshot_already_exists"):
            self.commit()
        self.assertEqual(snapshot.read_bytes(), old)

    def test_record_requires_explicit_write_and_digest(self):
        p = self.preview()
        with self.assertRaisesRegex(SNAP.SnapshotError, "explicit_write_flag_required"):
            SNAP.record(
                self.root, "Q1", "Q1_problem_contract.md", "research.json",
                expected_contract_sha256=p["contract"]["sha256"],
                expected_report_sha256=p["report_source"]["sha256"],
                write=False,
            )
        with self.assertRaisesRegex(SNAP.SnapshotError, "source_read_set_changed"):
            SNAP.record(
                self.root, "Q1", "Q1_problem_contract.md", "research.json",
                expected_contract_sha256="0" * 64,
                expected_report_sha256=p["report_source"]["sha256"], write=True)
        self.assertFalse((self.root / "research_evidence").exists())

    def test_mismatched_question_and_not_frozen_report_rejected(self):
        with self.assertRaisesRegex(SNAP.SnapshotError, "research_scope_or_freeze_not_bound"):
            SNAP.preview(self.root, "Q2", "Q1_problem_contract.md", "research.json")
        bad = deepcopy(self.report)
        bad["scope"]["problem_contract_status"] = "not_applicable"
        (self.root / "research.json").write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(SNAP.SnapshotError):
            self.preview()

    def test_safe_paths_and_snapshot_self_input_denied(self):
        for invalid in ("../secret.json", "/etc/passwd", r"C:\Windows\system.ini"):
            with self.subTest(path=invalid), self.assertRaises(SNAP.SnapshotError):
                SNAP.preview(self.root, "Q1", invalid, "research.json")
        self.commit()
        with self.assertRaisesRegex(SNAP.SnapshotError, "snapshot_cannot_be_its_own_source"):
            SNAP.preview(self.root, "Q1", "research_evidence/Q1.snapshot.json", "research.json")

    def test_symlink_boundaries_refuse_laundering(self):
        target = self.root / "Q1_problem_contract.md"
        alias = self.root / "alias.md"
        try:
            alias.symlink_to(target)
        except (NotImplementedError, OSError):
            self.skipTest("symlink creation unavailable on this runner")
        with self.assertRaisesRegex(SNAP.SnapshotError, "symlink"):
            SNAP.preview(self.root, "Q1", "alias.md", "research.json")

    def test_tampered_embedded_report_is_rejected(self):
        self.commit()
        path = self.root / "research_evidence/Q1.snapshot.json"
        obj = json.loads(path.read_text(encoding="utf-8"))
        obj["research"]["decision"]["evidence_status"] = "sufficient"
        path.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
        report = SNAP.inspect(self.root, "Q1")
        self.assertEqual(report["status"], "stale")
        self.assertIn("embedded_report_digest_mismatch", report["issues"])
        self.assertIn("embedded_report_invalid", report["issues"])

    def test_qualified_citation_is_a_candidate_only(self):
        source = {
            "id": "L1", "title": "Synthetic method metadata for tests",
            "source_url": "https://example.org/paper", "origin": "user_supplied",
            "access_level": "method", "evidence_level": "E2",
            "method_anchor": "section 2, equation 3",
        }
        self.report["sources"] = [source]
        self.report["methods"] = [{
            "id": "M1", "source_id": "L1",
            "method_summary": "A diffusion equation with exact stated assumptions",
            "transferability": "conditional", "disposition": "adapt_to_problem",
            "applicability_reason": "Current task boundary differs from source's geometry.",
        }]
        (self.root / "research.json").write_text(
            json.dumps(self.report, ensure_ascii=False), encoding="utf-8")
        self.commit()
        result = SNAP.inspect(self.root, "Q1")
        self.assertEqual(result["status"], "current")
        self.assertEqual(result["citation_candidates"][0]["method_id"], "M1")
        self.assertIsNone(result["citation_candidates"][0]["citation_key"])
        self.assertEqual(result["source_authenticity"], "not_assessed")
        self.assertEqual(result["model_approval"], "not_granted")


if __name__ == "__main__":
    unittest.main()
