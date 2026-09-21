"""User-facing resume regressions using synthetic, hash-only route evidence.

No numerical code is executed here; workbook bytes only qualify routing fixtures.
Native numerical and workbook validation are covered by the execution smoke tests.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from project_snapshot import _solver_observations
from resolve_runtime import resolve_runtime
from sync_project import synchronize
from tests.test_sync_project import framework_text, write_state
from tests.test_v900_semantic_identity_binding import (
    framework, identity, structured_question, write_project,
)


def string_values(value):
    if isinstance(value, dict):
        return {text for child in value.values() for text in string_values(child)}
    if isinstance(value, list):
        return {text for child in value for text in string_values(child)}
    return {value} if isinstance(value, str) else set()


def legacy_primary_project(root: Path, *, analysis_backend: str | None = None):
    directory = root / "问题一求解"
    directory.mkdir()
    code = directory / "问题一求解.py"
    code.write_text("def main():\n    return 1\n", encoding="utf-8")
    workbook = directory / "问题一求解结果.xlsx"
    workbook.write_bytes(b"synthetic hash-only route evidence; not a numerical workbook")
    hashes = {"primary_code": hashlib.sha256(code.read_bytes()).hexdigest(),
              "solution_workbook": hashlib.sha256(workbook.read_bytes()).hexdigest()}
    entry = structured_question()
    entry.update(
        classification={"objective": "optimization", "structures": []},
        status="solved", code=code.relative_to(root).as_posix(),
        primary_code_sha256=hashes["primary_code"],
        primary_execution_status="accepted", result_quality_status="passed",
        result_analysis_status="pending", analysis_execution_status="pending",
        solution_workbook=workbook.relative_to(root).as_posix(),
        artifact_hashes=hashes, validated_artifact_hashes=dict(hashes),
    )
    if analysis_backend:
        entry["solver_execution"] = {"analysis": {
            "backend": analysis_backend, "selection_reason": "Required analysis library",
        }}
    write_project(root, state_question=entry, framework_text=framework(identity()))
    return entry


class SolverBackendRuntimeResumeTests(unittest.TestCase):
    def test_old_python_resume_without_new_parameters_retains_legacy_projection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            legacy_primary_project(root)
            plan = resolve_runtime(request="继续求解", project_root=root, question="Q1")
        self.assertIn("modules/03_solve_validate.md", plan["modules"])
        self.assertIn("python_code", plan["terminal_outputs"])
        self.assertNotIn("solver_backend", plan)
        self.assertEqual(plan["assurance"]["status"], "pass")

    def test_full_workflow_resumes_legacy_python_primary_into_selected_matlab_analysis(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            legacy_primary_project(root, analysis_backend="matlab")
            before = (root / "state/project_state.yaml").read_bytes()
            plan = resolve_runtime("full_workflow", project_root=root, question="Q1")
            self.assertEqual(before, (root / "state/project_state.yaml").read_bytes())
        self.assertIn("modules/03_result_analysis.md", plan["modules"])
        self.assertNotIn("modules/03_solve_validate.md", plan["modules"])
        self.assertEqual(plan["solver_backend"]["stage"], "analysis")
        self.assertEqual(plan["solver_backend"]["resolved"], "matlab")
        self.assertEqual(plan["assurance"]["status"], "pass")
        self.assertIn("templates/code/matlab/q1_analysis.m", plan["templates"])
        self.assertNotIn("templates/code/matlab/q1_solver.m", plan["templates"])
        self.assertNotIn("templates/code/starter/README.md", plan["templates"])
        for interface in (plan["pre_delivery_gates"], plan["reading_plan"]["tool_interfaces"]):
            self.assertIn("stage_code", string_values(interface))
        self.assertFalse({"python_code", "stage_python_code"} & string_values(plan))

    def test_explicit_new_analysis_backend_precedes_default_primary_inheritance(self):
        for intent in ("result_analysis", "full_workflow"):
            with self.subTest(intent=intent), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                legacy_primary_project(root)
                before = (root / "state/project_state.yaml").read_bytes()
                plan = resolve_runtime(intent, project_root=root, question="Q1", solver_backend="matlab")
                self.assertEqual(before, (root / "state/project_state.yaml").read_bytes())
                self.assertEqual(plan["solver_backend"]["stage"], "analysis")
                self.assertEqual(plan["solver_backend"]["resolved"], "matlab")
                self.assertEqual(plan["solver_backend"]["by_question"]["Q1"]["source"], "explicit")
                self.assertEqual(plan["assurance"]["context"]["conflicts"], [])
                self.assertIn("templates/code/matlab/q1_analysis.m", plan["templates"])
                self.assertNotIn("templates/code/starter/README.md", plan["templates"])

    def test_existing_analysis_selection_remains_protected_from_conflicting_request(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            legacy_primary_project(root, analysis_backend="matlab")
            before = (root / "state/project_state.yaml").read_bytes()
            plan = resolve_runtime("result_analysis", project_root=root, question="Q1", solver_backend="python")
            self.assertEqual(before, (root / "state/project_state.yaml").read_bytes())
        self.assertEqual(plan["solver_backend"]["resolved"], "matlab")
        self.assertEqual(plan["assurance"]["status"], "review_required")
        self.assertTrue(any("Q1.analysis requested backend python conflicts with current matlab" in issue
                            for issue in plan["assurance"]["context"]["conflicts"]))

    def test_selection_only_empty_directory_does_not_fail_design_sync(self):
        for backend in ("python", "matlab"):
            with self.subTest(backend=backend), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                (root / "问题一求解").mkdir()
                (root / "模型论文框架.md").write_text(framework_text(), encoding="utf-8")
                write_state(root, status="designed", phase="model_design")
                state_path = root / "state/project_state.yaml"
                state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
                entry = state["subproblems"]["Q1"]
                entry["solver_execution"] = {"primary": {
                    "backend": backend, "selection_reason": "Selected during model design",
                }}
                state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
                before = state_path.read_bytes()
                observed, paths, issues = _solver_observations(root, "问题一", entry)
                self.assertEqual((observed, paths, issues), ({}, {"primary": None, "analysis": None}, []))
                report = synchronize(root, write=False, delivery_scope="design")
                self.assertEqual(report["issues"], [])
                self.assertEqual(before, state_path.read_bytes())

    def test_registered_missing_entry_still_fails_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "问题一求解").mkdir()
            entry = {"code": "问题一求解/q1_solver.m", "primary_code_sha256": "a" * 64,
                     "solver_execution": {"primary": {"backend": "matlab", "selection_reason": "Delivered"}}}
            observed, paths, issues = _solver_observations(root, "问题一", entry)
        self.assertIsNone(paths["primary"])
        self.assertTrue(observed["primary"]["binding_issues"])
        self.assertTrue(any("已登记阶段入口不存在" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
