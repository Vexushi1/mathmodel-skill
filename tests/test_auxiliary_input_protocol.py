"""AUD-02: fail-closed receipt 1.2, actual input drift, and downstream closure."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import execution_protocol as protocol
import stage_code
import stage_inputs
import sync_project
import runtime_assurance
import validate_user_execution as receipts
from artifact_fingerprint import combined_hash
from tests.audit_auxiliary_smoke import prepare_project, deliver_stage, run_smoke
from tests.test_audit_closure_regressions import project_bytes
from tests.test_solver_backend_end_to_end import save_state, file_hash
from tests.test_solver_backend_downstream_identity import package_fixture
from tests.test_audit_package_completeness import archive, VALIDATOR
from submission_requirements import reproducibility_requirements


class AuxiliaryInputProtocolTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.state = prepare_project(self.root, "python")
        self.state, self.code, self.config, _ = deliver_stage(self.root, "python", "primary", self.state)

    def observation(self, config=None):
        return stage_inputs.observe_inputs(self.root, config or self.config, self.state)

    def test_base_identity_is_unchanged_and_all_input_paths_are_visible(self):
        row = self.observation()
        self.assertEqual(row["issues"], [])
        self.assertEqual(row["data_sha256"], self.state["preprocessing"]["workbook_sha256"])
        self.assertEqual(row["paths"], [*self.config["data_paths"], "constraints.json"])

    def test_writer_rejects_auxiliary_wrong_stage_or_version_without_mutation(self):
        import validate_code_delivery
        for updates in ({"stage": "preprocessing"}, {"run_receipt_protocol_version": "1.1.0"}):
            with self.subTest(updates=updates):
                before = project_bytes(self.root)
                with self.assertRaises(ValueError):
                    validate_code_delivery.update_state(self.root, {**self.config, **updates}, self.code)
                self.assertEqual(project_bytes(self.root), before)

    def test_unextended_11_keeps_accepted_xlsx_identity(self):
        config = {key: value for key, value in self.config.items() if key not in protocol.AUXILIARY_FIELDS}
        config["run_receipt_protocol_version"] = "1.1.0"
        row = self.observation(config)
        self.assertEqual(row["issues"], [])
        self.assertEqual(row["paths"], config["data_paths"])
        self.assertNotIn("auxiliary_data_sha256", row)

    def test_unsupported_version_or_partial_fields_fail_closed(self):
        cases = [{**self.config, "run_receipt_protocol_version": value} for value in ("1.0.0", "1.1.0", "1.3.0")]
        cases += [{key: value for key, value in self.config.items() if key != field} for field in protocol.AUXILIARY_FIELDS]
        cases += [{**self.config, "auxiliary_data_paths": value} for value in ([], None, "constraints.json", [None])]
        cases += [{**self.config, "stage": "preprocessing"}, {**self.config, "data_identity_mode": "combined"}]
        for config in cases:
            with self.subTest(config=config), self.assertRaises(ValueError):
                self.observation(config)

    def test_auxiliary_mutation_and_deletion_are_not_silently_ignored(self):
        path = self.root / "constraints.json"
        path.write_text("{}", encoding="utf-8")
        self.assertTrue(self.observation()["issues"])
        path.unlink()
        with self.assertRaises(ValueError):
            self.observation()

    def test_missing_or_changed_preprocessing_is_also_rejected(self):
        path = self.root / self.config["data_paths"][0]
        path.write_bytes(b"changed")
        self.assertTrue(self.observation()["issues"])
        path.unlink()
        with self.assertRaises(ValueError):
            self.observation()

    def test_bad_paths_duplicate_base_and_covered_raw_sources_are_rejected(self):
        candidates = (["../outside.json"], ["/tmp/x"], ["C:/x"], ["./constraints.json"],
                      ["constraints.json", "constraints.json"], ["CONSTRAINTS.json"],
                      self.config["data_paths"], ["data/raw.csv"])
        for paths in candidates:
            with self.subTest(paths=paths), self.assertRaises(ValueError):
                self.observation({**self.config, "auxiliary_data_paths": paths})

    def test_hardlink_alias_is_not_a_second_input(self):
        alias = self.root / "alias.json"
        os.link(self.root / "constraints.json", alias)
        with self.assertRaises(ValueError):
            self.observation({**self.config, "auxiliary_data_paths": ["constraints.json", "alias.json"]})
        alias.unlink()
        os.link(self.root / self.config["data_paths"][0], alias)
        with self.assertRaises(ValueError):
            self.observation({**self.config, "auxiliary_data_paths": ["alias.json"]})

    def test_symbolic_alias_is_rejected_before_reading(self):
        alias = self.root / "alias.json"
        try:
            alias.symlink_to(self.root / "constraints.json")
        except OSError as exc:
            if os.name == "nt" and getattr(exc, "winerror", None) == 1314:
                self.skipTest("Windows runner does not grant symlink creation")
            raise
        with self.assertRaises(ValueError):
            self.observation({**self.config, "auxiliary_data_paths": ["alias.json"]})

    def test_multiple_auxiliaries_use_existing_order_independent_digest(self):
        (self.root / "second.json").write_text('{"right_hand_side_offset":1}', encoding="utf-8")
        paths = ["second.json", "constraints.json"]
        digest = combined_hash([self.root / path for path in paths], self.root)
        config = {**self.config, "auxiliary_data_paths": paths, "auxiliary_data_sha256": digest.upper()}
        self.assertEqual(self.observation(config)["issues"], [])
        config["auxiliary_data_paths"] = list(reversed(paths))
        self.assertEqual(self.observation(config)["auxiliary_data_sha256"], digest)

    def test_receipt_json_pair_binding_and_version_downgrade(self):
        metadata = {field: self.config[field] for field in receipts.RUN_RECEIPT_ECHO_FIELDS}
        metadata.update(run_receipt_version="1.2.0", solver_backend="python", code_bundle_sha256="a"*64,
                        data_identity_mode="preprocessing_workbook", auxiliary_data_paths='["constraints.json"]',
                        auxiliary_data_sha256=self.config["auxiliary_data_sha256"].upper())
        self.assertEqual(receipts.validate_run_receipt_binding(metadata, self.config), [])
        variants = [{**metadata, field: value} for field, value in (
            ("auxiliary_data_paths", "not json"), ("auxiliary_data_paths", '"constraints.json"'),
            ("auxiliary_data_paths", "[]"), ("auxiliary_data_sha256", "0"*64),
            ("run_receipt_version", "1.1.0"), ("data_identity_mode", "combined"))]
        variants += [{key: value for key, value in metadata.items() if key != field} for field in protocol.AUXILIARY_FIELDS]
        for variant in variants:
            with self.subTest(variant=variant):
                self.assertTrue(receipts.validate_run_receipt_binding(variant, self.config))

    def test_12_config_mutation_is_subject_to_modern_parser_guards(self):
        self.code.write_text(self.code.read_text(encoding="utf-8") + "\nRUN_CONFIG['tolerance'] = 1\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            stage_code.parse_stage_config(self.code)

    def test_read_only_input_observation_never_refreshes_expected_hashes(self):
        (self.root / "constraints.json").write_text("{}", encoding="utf-8")
        before = project_bytes(self.root)
        self.assertTrue(self.observation()["issues"])
        self.assertEqual(project_bytes(self.root), before)

    def test_matlab_12_instantiation_static_checks_and_bundle_work(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = prepare_project(root, "matlab")
            state, code, config, native = deliver_stage(root, "matlab", "primary", state)
            self.assertEqual(config["run_receipt_protocol_version"], "1.2.0")
            self.assertEqual(stage_code.validate_stage_binding(root, state["subproblems"]["Q1"], "primary", project_backend="matlab"), [])
            self.assertNotEqual(native.get("status"), "passed")  # Static test is not native Code Analyzer proof.

    def test_native_python_detects_input_change_before_receipt(self):
        marker = '    assert observe(root, code, config) == identity'
        text = self.code.read_text(encoding="utf-8")
        self.code.write_text(text.replace(marker, '    (root / "constraints.json").write_text("{}", encoding="utf-8")\n' + marker), encoding="utf-8")
        result = subprocess.run([sys.executable, "-B", str(self.code)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("SyntaxError", result.stderr)
        self.assertIn("AssertionError", result.stderr)
        self.assertFalse((self.root / self.config["expected_workbook"]).exists())

    def test_native_python_detects_source_change_before_receipt(self):
        marker = '    assert observe(root, code, config) == identity'
        text = self.code.read_text(encoding="utf-8")
        self.code.write_text(text.replace(marker, '    code.write_text(code.read_text(encoding="utf-8") + "\\n# changed", encoding="utf-8")\n' + marker), encoding="utf-8")
        result = subprocess.run([sys.executable, "-B", str(self.code)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("SyntaxError", result.stderr)
        self.assertIn("AssertionError", result.stderr)
        self.assertFalse((self.root / self.config["expected_workbook"]).exists())


class AuxiliaryDownstreamTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.smoke = run_smoke(self.root, "python")
        self.state = yaml.safe_load((self.root / "state/project_state.yaml").read_text(encoding="utf-8"))

    def test_native_python_primary_analysis_and_preprocessing_preservation(self):
        self.assertTrue(self.smoke["auxiliary_changes_answer"])
        self.assertTrue(self.smoke["primary_preserved"])
        self.assertTrue(self.smoke["preprocessing_preserved"])

    def test_runtime_qualifies_12_then_rejects_unsynced_auxiliary_drift(self):
        self.assertIn("validated_results", runtime_assurance.hydrate_project_context(self.root)["verified_artifacts"])
        (self.root / "constraints.json").write_text("{}", encoding="utf-8")
        before = project_bytes(self.root)
        self.assertNotIn("accepted_solution_workbook", runtime_assurance.hydrate_project_context(self.root)["verified_artifacts"])
        self.assertEqual(before, project_bytes(self.root))

    def test_receipt_revalidation_does_not_promote_changed_auxiliary(self):
        entry = self.state["subproblems"]["Q1"]
        old_validated = deepcopy(entry["validated_artifact_hashes"])
        (self.root / "constraints.json").unlink()
        self.assertTrue(receipts.validate_one(self.root, self.root / entry["solution_workbook"], self.state, True))
        self.assertEqual(entry["primary_execution_status"], "rejected")
        self.assertEqual(entry["validated_artifact_hashes"], old_validated)

    def test_snapshot_input_issue_causes_data_stale_without_revoking_model_approval(self):
        entry = self.state["subproblems"]["Q1"]
        entry.update(model_challenge_status="passed", human_model_approval_status="approved")
        snapshot = {"artifact_hashes": deepcopy(entry["validated_artifact_hashes"]),
                    "primary_code_sha256": entry["primary_code_sha256"], "analysis_code_sha256": entry["analysis_code_sha256"],
                    "project_backend": "python", "solver_execution_observed": {}}
        for stage, field in (("primary", "code"), ("analysis", "result_analysis_code")):
            snapshot["solver_execution_observed"][stage] = {"backend": "python", "entrypoint": entry[field],
                "bundle_sha256": entry["solver_execution"][stage]["bundle_sha256"], "inputs": {"issues": []}}
        snapshot["solver_execution_observed"]["primary"]["inputs"]["issues"] = ["actual auxiliary hash changed"]
        events = sync_project._snapshot_transition_events(entry, snapshot)
        self.assertIn("data_changed", events)
        sync_project.STATE_TRANSITIONS.apply_transition(self.state, event="data_changed", source_question="Q1",
                                                       contract=sync_project.STATE_TRANSITION_CONTRACT)
        self.assertIn("solution_workbook", entry["stale_layers"])
        self.assertEqual(entry["human_model_approval_status"], "approved")

    def test_analysis_only_input_event_preserves_primary(self):
        before = deepcopy(self.state["subproblems"]["Q1"])
        sync_project.STATE_TRANSITIONS.apply_transition(self.state, event="analysis_inputs_changed", source_question="Q1",
                                                       contract=sync_project.STATE_TRANSITION_CONTRACT)
        after = self.state["subproblems"]["Q1"]
        self.assertEqual(after["primary_execution_status"], before["primary_execution_status"])
        self.assertEqual(after["data_hash"], before["data_hash"])
        self.assertNotIn("solution_workbook", after["stale_layers"])

    def test_actual_sync_observes_auxiliary_drift_without_washing_accepted_identity(self):
        before = project_bytes(self.root)
        current = sync_project.synchronize(self.root)
        # This fixture exercises numerical provenance, not full model/framework qualification.
        observed = current["questions"]["Q1"]["solver_execution_observed"]
        self.assertEqual(observed["primary"]["inputs"]["issues"], [])
        self.assertIn("constraints.json", observed["primary"]["inputs"]["paths"])
        self.assertEqual(project_bytes(self.root), before)
        (self.root / "constraints.json").write_text("{}", encoding="utf-8")
        before = project_bytes(self.root)
        report = sync_project.synchronize(self.root)
        self.assertTrue(report["questions"]["Q1"]["solver_execution_observed"]["primary"]["inputs"]["issues"])
        self.assertTrue(any(row["event"] == "data_changed" for row in report["state_transitions"]))
        self.assertEqual(project_bytes(self.root), before)

    def test_migration_preview_archives_all_inputs_and_rejects_changed_auxiliary(self):
        import project_solver_backend
        before = project_bytes(self.root)
        report = project_solver_backend.preview_migration(self.root, target_backend="matlab", reason="Synthetic input archive test")
        self.assertEqual(report["status"], "ready_for_review", report["issues"])
        self.assertEqual(report["expected_file_hashes"]["constraints.json"], file_hash(self.root / "constraints.json"))
        for row in report["stages"]:
            if row["active"]:
                self.assertIn("constraints.json", row["inputs"])
        self.assertEqual(project_bytes(self.root), before)
        (self.root / "constraints.json").write_text("{}", encoding="utf-8")
        before = project_bytes(self.root)
        report = project_solver_backend.preview_migration(self.root, target_backend="matlab", reason="Synthetic input archive test")
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(project_bytes(self.root), before)

    def test_input_or_source_changed_during_quality_recheck_cannot_be_accepted(self):
        for stage in ("primary", "analysis"):
            for target_kind in ("input", "source"):
                with self.subTest(stage=stage, target=target_kind):
                    state = deepcopy(self.state)
                    entry = state["subproblems"]["Q1"]
                    old_validated = deepcopy(entry["validated_artifact_hashes"])
                    target = self.root / ("constraints.json" if target_kind == "input" else entry["code" if stage == "primary" else "result_analysis_code"])
                    old_bytes = target.read_bytes()
                    owner = receipts.NUMERICAL_VALIDATION if stage == "primary" else receipts
                    name = "validate_primary_numerical_evidence" if stage == "primary" else "analysis_passed"
                    original = getattr(owner, name)
                    def changed(*args, **kwargs):
                        result = original(*args, **kwargs)
                        target.write_bytes(old_bytes + b"\n# changed during quality read\n")
                        return result
                    try:
                        with patch.object(owner, name, side_effect=changed):
                            errors = receipts.validate_one(self.root, self.root / entry["solution_workbook" if stage == "primary" else "result_analysis_workbook"], state, True)
                        self.assertTrue(errors)
                        self.assertEqual(entry[f"{stage}_execution_status"], "rejected")
                        self.assertEqual(entry["validated_artifact_hashes"], old_validated)
                    finally:
                        target.write_bytes(old_bytes)

    def test_reproducibility_includes_auxiliary_and_rejects_omission(self):
        package_fixture(self.root, self.state)
        (self.root / "数据预处理/data_process.m").write_text("% synthetic package only", encoding="utf-8")
        required, issues = reproducibility_requirements(self.root, self.state)
        self.assertEqual(issues, [])
        self.assertIn("constraints.json", required)
        good = archive(self.root)
        self.assertEqual(VALIDATOR.validate_package(self.root, good)["status"], "passed")
        bad = archive(self.root, omit=["constraints.json"])
        self.assertNotEqual(VALIDATOR.validate_package(self.root, bad)["status"], "passed")


if __name__ == "__main__":
    unittest.main()
