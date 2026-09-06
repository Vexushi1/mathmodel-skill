from __future__ import annotations

import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import artifact_identity as ARTIFACT_IDENTITY


def load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SYNC = load_module("v900_phase_e_sync", "scripts/sync_project.py")
STATE_VALIDATION = load_module("v900_phase_e_state_validation", "scripts/validate_project_state.py")
RUNTIME = load_module("v900_phase_e_runtime", "scripts/runtime_assurance.py")
CODE = load_module("v900_phase_e_code_delivery", "scripts/validate_code_delivery.py")
TRANSITIONS = load_module("v900_phase_e_transitions", "scripts/state_transitions.py")
CONTRACT = yaml.safe_load((ROOT / "core/state_transition_contract.yaml").read_text(encoding="utf-8"))


class ArtifactAliasTests(unittest.TestCase):
    def test_legacy_model_alias_reads_as_primary_code(self):
        digest = "a" * 64
        normalized = ARTIFACT_IDENTITY.normalize_artifact_hashes({"model": digest})
        self.assertEqual(normalized["primary_code"], digest)
        self.assertNotIn("model", normalized)

    def test_equal_old_and_new_alias_is_readable_but_canonicalized(self):
        digest = "a" * 64
        normalized = ARTIFACT_IDENTITY.normalize_artifact_hashes(
            {"model": digest.upper(), "primary_code": digest}
        )
        self.assertEqual(normalized["primary_code"], digest)
        self.assertNotIn("model", normalized)

    def test_conflicting_old_and_new_alias_blocks(self):
        with self.assertRaisesRegex(ARTIFACT_IDENTITY.ArtifactIdentityError, "conflicts"):
            ARTIFACT_IDENTITY.normalize_artifact_hashes(
                {"model": "a" * 64, "primary_code": "b" * 64}
            )

    def test_model_hash_is_read_only_primary_code_fallback(self):
        digest = "c" * 64
        current, validated, issues = STATE_VALIDATION._normalized_hashes(
            {"model_hash": digest, "validated_model_hash": digest}
        )
        self.assertEqual(issues, [])
        self.assertEqual(current["primary_code"], digest)
        self.assertEqual(validated["primary_code"], digest)
        self.assertNotIn("model", current)


class CanonicalWriteTests(unittest.TestCase):
    def test_sync_snapshot_writes_primary_and_analysis_code_not_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "问题一求解"
            folder.mkdir(parents=True)
            primary = folder / "问题一求解.py"
            analysis = folder / "问题一结果深化分析.py"
            primary.write_text("print('primary')\n", encoding="utf-8")
            analysis.write_text("print('analysis')\n", encoding="utf-8")
            (root / "模型论文框架.md").write_text("# 模型论文框架\n\n### Q1\n", encoding="utf-8")
            schema = SYNC.load_yaml(SYNC.DEFAULT_SCHEMA_PATH)
            snapshot = SYNC._snapshot_question(
                root,
                "问题一",
                {
                    "status": "designed",
                    "framework_section": "### Q1",
                    "analysis_code_sha256": hashlib.sha256(analysis.read_bytes()).hexdigest(),
                },
                schema,
                None,
                None,
            )
        self.assertEqual(snapshot["artifact_hashes"]["primary_code"], snapshot["primary_code_sha256"])
        self.assertEqual(snapshot["artifact_hashes"]["analysis_code"], snapshot["analysis_code_sha256"])
        self.assertNotIn("model", snapshot["artifact_hashes"])

    def test_code_delivery_primary_write_uses_only_primary_code_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "state").mkdir()
            folder = root / "问题一求解"
            folder.mkdir()
            script = folder / "问题一求解.py"
            script.write_text("print('primary')\n", encoding="utf-8")
            state = {
                "project": {"current_phase": "solve_validate"},
                "subproblems": {"Q1": {"status": "designed"}},
            }
            (root / "state" / "project_state.yaml").write_text(
                yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            CODE.update_state(
                root,
                {"problem_name": "问题一", "stage": "primary", "data_sha256": "a" * 64},
                script,
            )
            expected_hash = hashlib.sha256(script.read_bytes()).hexdigest()
            updated = yaml.safe_load((root / "state" / "project_state.yaml").read_text(encoding="utf-8"))
        hashes = updated["subproblems"]["Q1"]["artifact_hashes"]
        self.assertEqual(hashes["primary_code"], expected_hash)
        self.assertNotIn("model", hashes)


class TransitionAndRuntimeTests(unittest.TestCase):
    def _entry(self):
        return {
            "status": "validated",
            "depends_on": [],
            "model_challenge_status": "passed",
            "human_model_approval_status": "approved",
            "primary_execution_status": "accepted",
            "analysis_execution_status": "accepted",
            "result_quality_status": "passed",
            "result_analysis_status": "passed",
            "validation_status": "passed",
            "result_summary_status": "current",
            "artifacts_stale": False,
            "stale_layers": [],
        }

    def test_primary_change_does_not_invalidate_mathematical_approval(self):
        state = {"subproblems": {"Q1": self._entry()}}
        TRANSITIONS.apply_transition(
            state, event="primary_code_changed", source_question="Q1", contract=CONTRACT
        )
        q1 = state["subproblems"]["Q1"]
        self.assertEqual(q1["model_challenge_status"], "passed")
        self.assertEqual(q1["human_model_approval_status"], "approved")
        self.assertIn("primary_code", q1["stale_layers"])

    def test_analysis_change_does_not_stale_primary_result(self):
        state = {"subproblems": {"Q1": self._entry()}}
        TRANSITIONS.apply_transition(
            state, event="analysis_code_changed", source_question="Q1", contract=CONTRACT
        )
        q1 = state["subproblems"]["Q1"]
        self.assertEqual(q1["result_quality_status"], "passed")
        self.assertNotIn("solution_workbook", q1["stale_layers"])
        self.assertIn("analysis_code", q1["stale_layers"])

    def test_runtime_reports_alias_conflict_instead_of_selecting_a_hash(self):
        item = {
            "artifact_hashes": {"model": "a" * 64, "primary_code": "b" * 64},
            "validated_artifact_hashes": {},
        }
        issues = ARTIFACT_IDENTITY.entry_alias_issues(item, scope="Q1")
        self.assertTrue(any("conflicts" in issue for issue in issues))
        self.assertIsNone(RUNTIME._expected_hash(item, "primary_code"))


if __name__ == "__main__":
    unittest.main()
