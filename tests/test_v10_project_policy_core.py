"""The current numerical policy has one project owner and no stage fallback."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import stage_code
import validate_project_state


class ProjectPolicyCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.example = yaml.safe_load((ROOT / "state/project_state.example.yaml").read_text(encoding="utf-8"))
        cls.schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(cls.schema)

    def test_early_state_is_unselected_then_root_pair_is_canonical(self):
        state = deepcopy(self.example)
        self.assertEqual(validate_project_state.validate_state_payload(state, project_root=ROOT), [])
        self.assertIsNone(stage_code.current_project_backend(state))
        with self.assertRaisesRegex(stage_code.StageCodeError, "explicit project backend"):
            stage_code.current_project_backend(state, required=True)
        state["execution"] = {
            "solver_backend": "matlab", "solver_backend_selection_reason": "全题需求和可用工具箱已核查",
        }
        self.assertEqual(list(Draft202012Validator(self.schema).iter_errors(state)), [])
        self.assertEqual(validate_project_state.validate_state_payload(state, project_root=ROOT), [])
        self.assertEqual(stage_code.current_project_backend(state), "matlab")

    def test_incomplete_policy_and_stage_selection_cannot_enter_current_state(self):
        for execution in ({"solver_backend": "python"},
                          {"solver_backend": "auto", "solver_backend_selection_reason": "reason"},
                          {"solver_backend": "python", "solver_backend_selection_reason": " \n "}):
            with self.subTest(execution=execution):
                state = deepcopy(self.example)
                state["execution"] = execution
                self.assertTrue(validate_project_state.validate_state_payload(state, project_root=ROOT))
        state = deepcopy(self.example)
        state["execution"] = {"solver_backend": "python", "solver_backend_selection_reason": "全题核查"}
        state["subproblems"]["Q1"]["solver_execution"] = {
            "primary": {"backend": "python", "selection_reason": "old"},
        }
        self.assertTrue(validate_project_state.validate_state_payload(state, project_root=ROOT))
        with self.assertRaisesRegex(stage_code.StageCodeError, "coexist"):
            stage_code.current_project_backend(state)

    def test_unselected_project_cannot_carry_delivered_or_validated_numerical_identity(self):
        for fields in (
            {"primary_execution_status": "code_delivered"},
            {"primary_execution_status": "accepted"},
            {"analysis_execution_status": "accepted"},
            {"primary_code_sha256": "a" * 64},
            {"validated_artifact_hashes": {"primary_code": "a" * 64}},
            {"artifact_hashes": {"solution_workbook": "a" * 64}},
        ):
            with self.subTest(fields=fields):
                state = deepcopy(self.example)
                state["subproblems"]["Q1"].update(fields)
                issues = validate_project_state.validate_state_payload(state, project_root=ROOT)
                self.assertTrue(any("project backend" in issue for issue in issues), issues)

    def test_another_question_conflict_blocks_narrow_request(self):
        state = {"execution": {"solver_backend": "python", "solver_backend_selection_reason": "全题核查"},
                 "subproblems": {"Q1": {}, "Q2": {"code": "问题二求解/q2_solver.m"}}}
        with self.assertRaisesRegex(stage_code.StageCodeError, "Q2.primary"):
            stage_code.current_project_backend(state, requested_backend="python", required=True)

    def test_nonmapping_state_fails_closed_as_validation_issue(self):
        self.assertEqual(validate_project_state.validate_state_payload([], project_root=ROOT),
                         ["schema <root>: project state must be a mapping"])

    def test_selected_matlab_never_discovers_a_stray_python_entry(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "问题一求解"
            folder.mkdir()
            (folder / "问题一求解.py").write_text("pass\n", encoding="utf-8")
            with self.assertRaises(stage_code.StageCodeMissingError):
                stage_code.resolve_stage_code(root, "Q1", "primary", project_backend="matlab")

    def test_current_binding_uses_root_backend_and_stage_bundle_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "问题一求解"
            folder.mkdir()
            script = folder / "问题一求解.py"
            config = {"solver_backend": "python", "stage": "primary", "problem_name": "问题一",
                      "run_receipt_protocol_version": "1.1.0", "code_dependencies": []}
            script.write_text(f"RUN_CONFIG = {config!r}\n\ndef main():\n    return 0\n", encoding="utf-8")
            entry = {"code": "问题一求解/问题一求解.py",
                     "primary_code_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
                     "solver_execution": {"primary": {"bundle_sha256":
                         stage_code.stage_code_fingerprint(root, script)["bundle_sha256"]}}}
            self.assertEqual(stage_code.validate_stage_binding(root, entry, "primary", project_backend="python"), [])
            self.assertTrue(stage_code.validate_stage_binding(root, entry, "primary", project_backend="matlab"))


if __name__ == "__main__":
    unittest.main()
