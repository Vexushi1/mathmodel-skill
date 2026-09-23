"""Project backend routing regressions using synthetic state and source evidence."""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from resolve_runtime import resolve_runtime
from tests import test_solver_backends as solver_fixtures
from tests.test_solver_backend_runtime_resume import legacy_primary_project


def save(root: Path, state: dict) -> bytes:
    path = root / "state/project_state.yaml"
    path.parent.mkdir(exist_ok=True)
    path.write_text(yaml.safe_dump(state, allow_unicode=True), encoding="utf-8")
    return path.read_bytes()


def project(backend: str | None, *, question: str = "Q1") -> dict:
    state = {"project": {"current_phase": "solve_validate"},
             "preprocessing": {"decision": "not_needed"},
             "subproblems": {question: {"status": "designed"}}}
    if backend:
        state["execution"] = {"solver_backend": backend,
                              "solver_backend_selection_reason": "全题需求与运行环境已审视"}
    return state


class ProjectRuntimePolicyTests(unittest.TestCase):
    def test_q1_scope_still_reports_q2_policy_conflict_without_reading_q2_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = project("python")
            state["subproblems"]["Q2"] = {"code": "问题二求解/q2_solver.m"}
            before = save(root, state)
            plan = resolve_runtime("code_and_solution", objective="optimization",
                                   project_root=root, question="Q1")
            self.assertEqual((root / "state/project_state.yaml").read_bytes(), before)
        self.assertEqual(plan["assurance"]["status"], "review_required")
        self.assertTrue(any("Q2.primary" in issue and "suffix" in issue
                            for issue in plan["assurance"]["context"]["conflicts"]))
        self.assertIsNone(plan["solver_backend"]["resolved"])
        self.assertFalse(plan["solver_backend"]["selection_complete"])
        self.assertNotIn("templates/code/matlab/q1_solver.m", plan["templates"])

    def test_only_root_policy_resumes_q3_with_auto_or_omitted_parameter(self):
        for requested in (None, "auto"):
            with self.subTest(requested=requested), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                before = save(root, project("matlab", question="Q3"))
                plan = resolve_runtime("code_and_solution", objective="optimization",
                                       project_root=root, question="Q3", solver_backend=requested)
                self.assertEqual((root / "state/project_state.yaml").read_bytes(), before)
                self.assertEqual(plan["solver_backend"]["scope"], "project")
                self.assertEqual(plan["solver_backend"]["resolved"], "matlab")
                self.assertTrue(plan["solver_backend"]["selection_complete"])
                self.assertNotEqual(plan["solver_backend"]["source"], "explicit_candidate")

    def test_opposite_request_never_changes_root_or_loads_opposite_template(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            legacy_primary_project(root)
            path = root / "state/project_state.yaml"
            state = yaml.safe_load(path.read_text(encoding="utf-8"))
            state["execution"] = project("python")["execution"]
            before = save(root, state)
            plan = resolve_runtime("code_and_solution", objective="optimization", project_root=root,
                                   question="Q1", solver_backend="matlab")
            self.assertEqual((root / "state/project_state.yaml").read_bytes(), before)
        self.assertEqual(plan["solver_backend"]["resolved"], "python")
        self.assertEqual(plan["assurance"]["status"], "review_required")
        self.assertTrue(any("requested backend matlab conflicts" in issue
                            for issue in plan["assurance"]["context"]["conflicts"]))
        self.assertIn("templates/code/starter/README.md", plan["templates"])
        self.assertNotIn("templates/code/matlab/q1_solver.m", plan["templates"])

    def test_unselected_and_historical_projects_do_not_promote_a_request(self):
        for historical in (False, True):
            with self.subTest(historical=historical), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                state = project(None)
                if historical:
                    state["subproblems"]["Q1"]["solver_execution"] = {
                        "primary": {"backend": "python", "selection_reason": "旧项目声明"}}
                save(root, state)
                plan = resolve_runtime("code_and_solution", objective="optimization", project_root=root,
                                       question="Q1", solver_backend="python")
                self.assertIsNone(plan["solver_backend"]["resolved"])
                self.assertFalse(plan["solver_backend"]["selection_complete"])
                self.assertNotIn("templates/code/starter/README.md", plan["templates"])
                if historical:
                    self.assertEqual(plan["solver_backend"]["source"], "historical_read_only")
                    self.assertEqual(plan["assurance"]["status"], "review_required")

    def test_stateless_explicit_backend_remains_only_a_planning_candidate(self):
        plan = resolve_runtime("code_and_solution", objective="optimization", solver_backend="matlab",
                               available_artifacts=["locked_model_spec"])
        self.assertEqual(plan["solver_backend"]["scope"], "stateless")
        self.assertEqual(plan["solver_backend"]["candidate_backend"], "matlab")
        self.assertFalse(plan["solver_backend"]["selection_complete"])
        self.assertIn("templates/code/matlab/q1_solver.m", plan["templates"])

    def test_resumed_stage_uses_one_root_backend_for_primary_and_analysis(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "问题一求解").mkdir()
            fixture = solver_fixtures.SolverBackendTests()
            fixture.root = root
            config = fixture.config("matlab")
            source = fixture.source(config)
            entry = fixture.entry(source, config, accepted=True)
            record = entry["solver_execution"]["primary"]
            record.pop("backend", None)
            record.pop("selection_reason", None)
            workbook = root / "问题一求解/问题一求解结果.xlsx"
            workbook.write_bytes(b"synthetic route evidence, not numerical validation")
            code_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            workbook_hash = hashlib.sha256(workbook.read_bytes()).hexdigest()
            entry.update(primary_execution_status="accepted", result_quality_status="passed",
                         analysis_execution_status="pending", result_analysis_status="pending",
                         solution_workbook=workbook.relative_to(root).as_posix(),
                         artifact_hashes={"primary_code": code_hash, "solution_workbook": workbook_hash},
                         validated_artifact_hashes={"primary_code": code_hash,
                                                    "solution_workbook": workbook_hash})
            state = project("matlab")
            state["subproblems"]["Q1"] = entry
            save(root, state)
            analysis = resolve_runtime("result_analysis", objective="optimization", project_root=root,
                                       question="Q1", solver_backend="auto")
            self.assertEqual(analysis["solver_backend"]["stage"], "analysis")
            self.assertEqual(analysis["solver_backend"]["resolved"], "matlab")
            self.assertIn("templates/code/matlab/q1_analysis.m", analysis["templates"])
            self.assertNotIn("templates/code/matlab/q1_solver.m", analysis["templates"])
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            legacy_primary_project(root)
            path = root / "state/project_state.yaml"
            state = yaml.safe_load(path.read_text(encoding="utf-8"))
            state["execution"] = project("python")["execution"]
            state["subproblems"]["Q1"]["primary_execution_status"] = "pending"
            save(root, state)
            primary = resolve_runtime("result_analysis", objective="optimization", project_root=root,
                                      question="Q1", solver_backend="auto")
            self.assertEqual(primary["solver_backend"]["stage"], "primary")
            self.assertEqual(primary["solver_backend"]["resolved"], "python")
            self.assertIn("templates/code/starter/README.md", primary["templates"])
            self.assertNotIn("templates/code/matlab/q1_analysis.m", primary["templates"])


if __name__ == "__main__":
    unittest.main()
