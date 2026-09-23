"""Backend routing, identity propagation, and package boundary regression tests.

These tests use explicitly synthetic qualification records. Actual MATLAB
numerical execution is exercised separately by the native solver smoke job.
"""
from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import project_snapshot as snapshot
import stage_code
import sync_project as sync
from resolve_runtime import resolve_runtime
from resolve_workflow import resolve_workflow
from runtime_assurance import hydrate_project_context
from submission_requirements import reproducibility_requirements
from validate_model_paper_framework import _implementation_anchor_issues
from tests.test_solver_backend_end_to_end import prepare, instantiate, file_hash, save_state
from tests.test_audit_package_completeness import archive, VALIDATOR
from tests.test_v900_state_transitions import state_with_dependency


def qualified_fixture(root, *, helper=False):
    prepare(root)
    state = yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8"))
    state["project"]["competition"] = "CUMCM"
    state["execution"] = {"solver_backend": "matlab",
                          "solver_backend_selection_reason": "Synthetic whole-problem review"}
    entry = state["subproblems"]["Q1"]
    entry["solver_execution"]["primary"].pop("backend", None)
    entry["solver_execution"]["primary"].pop("selection_reason", None)
    entry["classification"] = {"objective": "optimization", "structures": []}
    dependencies = []
    if helper:
        auxiliary = root / "问题一求解/helper.m"
        auxiliary.write_text("function y = helper(x)\ny = x;\nend\n", encoding="utf-8")
        dependencies.append({"path": auxiliary.relative_to(root).as_posix(), "sha256": file_hash(auxiliary)})
    code = instantiate(root, "primary", code_dependencies=dependencies)
    fingerprint = stage_code.stage_code_fingerprint(root, code, dependencies)
    entry["primary_code_sha256"] = fingerprint["entry_sha256"]
    entry["solver_execution"]["primary"].update(
        bundle_sha256=fingerprint["bundle_sha256"], validated_bundle_sha256=fingerprint["bundle_sha256"],
    )
    workbook = root / "问题一求解/问题一求解结果.xlsx"
    workbook.write_bytes(b"synthetic qualification record; not a numerical workbook")
    entry.update(solution_workbook=workbook.relative_to(root).as_posix(), primary_execution_status="accepted",
                 result_quality_status="passed", result_analysis_status="not_required",
                 result_analysis_requirement_reason="Only current-world claims", validated_data_hash=entry["data_hash"])
    entry["artifact_hashes"] = {"data": entry["data_hash"], "primary_code": file_hash(code), "solution_workbook": file_hash(workbook)}
    entry["validated_artifact_hashes"] = dict(entry["artifact_hashes"])
    save_state(root, state)
    return state


class SolverBackendIntegrationTests(unittest.TestCase):
    def test_legacy_omission_and_explicit_auto_have_distinct_output_contracts(self):
        kwargs = {"objective": "optimization", "available_artifacts": ["locked_model_spec"]}
        old = resolve_workflow("code_and_solution", **kwargs)
        new = resolve_workflow("code_and_solution", solver_backend="auto", **kwargs)
        self.assertIn("python_code", old["terminal_outputs"])
        self.assertIn("primary_code", new["terminal_outputs"])
        self.assertNotIn("python_code", new["terminal_outputs"])
        self.assertIn("solver_backend_selection", new["missing_prerequisites"])
        self.assertFalse(any("templates/code/matlab" in path for path in new["load_order"]))

    def test_selected_matlab_loads_only_the_current_stage_template(self):
        plan = resolve_runtime("code_and_solution", objective="optimization", solver_backend="matlab",
                               available_artifacts=["locked_model_spec"])
        self.assertIn("templates/code/matlab/q1_solver.m", plan["templates"])
        self.assertNotIn("templates/code/matlab/q1_analysis.m", plan["templates"])
        self.assertNotIn("python_code", plan["terminal_outputs"])
        self.assertFalse(plan["task_code_execution_allowed"])
        self.assertTrue(any(item["path"] == "templates/code/matlab/q1_solver.m" for item in plan["reading_plan"]["read_now"]))

    def test_matlab_solve_does_not_infer_a_figure_intent(self):
        plan = resolve_runtime(request="MATLAB求解", objective="optimization", solver_backend="matlab")
        self.assertNotIn("figures", plan["intents"])
        with self.assertRaisesRegex(ValueError, "no workflow intent"):
            resolve_runtime(request="MATLAB")

    def test_selected_state_wins_over_conflicting_new_preference_without_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            qualified_fixture(root)
            before = (root / "state/project_state.yaml").read_bytes()
            plan = resolve_runtime("figures", project_root=root, question="Q1", solver_backend="python")
            self.assertEqual(plan["solver_backend"]["resolved"], "matlab")
            self.assertEqual(plan["assurance"]["status"], "review_required")
            self.assertTrue(any("requested backend" in issue for issue in plan["assurance"]["context"]["conflicts"]))
            self.assertEqual(before, (root / "state/project_state.yaml").read_bytes())

    def test_matlab_state_is_respected_when_legacy_cli_omits_backend(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            qualified_fixture(root)
            plan = resolve_runtime("figures", project_root=root, question="Q1")
            self.assertEqual(plan["solver_backend"]["resolved"], "matlab")
            self.assertFalse(any("templates/code/matlab" in path for path in plan["load_order"]))

    def test_helper_drift_blocks_runtime_before_sync_and_uses_primary_event(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = qualified_fixture(root, helper=True)
            self.assertIn("validated_results", hydrate_project_context(root, "Q1")["verified_artifacts"])
            entry = state["subproblems"]["Q1"]
            delivered = deepcopy(entry["solver_execution"])
            (root / "问题一求解/helper.m").write_text("function y = helper(x)\ny = x + 1;\nend\n", encoding="utf-8")
            self.assertNotIn("validated_results", hydrate_project_context(root, "Q1")["verified_artifacts"])
            observed, paths, issues = snapshot._solver_observations(
                root, "问题一", entry, project_backend="matlab", current_state=True)
            self.assertTrue(issues)
            current = {"key": "Q1", "chinese_name": "问题一", "artifact_hashes": dict(entry["artifact_hashes"]),
                       "primary_code_sha256": file_hash(paths["primary"]), "solver_execution_observed": observed,
                       "project_backend": "matlab"}
            self.assertIn("primary_code_changed", sync._snapshot_transition_events(entry, current))
            sync._apply_snapshot_to_state(root, state, current)
            self.assertEqual(delivered, state["subproblems"]["Q1"]["solver_execution"])
            self.assertIn("primary_code", state["subproblems"]["Q1"]["stale_layers"])

    def test_analysis_bundle_drift_does_not_invalidate_primary_qualification(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = qualified_fixture(root)
            entry = state["subproblems"]["Q1"]
            code = instantiate(root, "analysis", primary_workbook_sha256=file_hash(root / entry["solution_workbook"]))
            fingerprint = stage_code.stage_code_fingerprint(root, code)
            analysis = root / "问题一求解/问题一结果深化分析.xlsx"
            analysis.write_bytes(b"synthetic analysis qualification record")
            entry.update(result_analysis_code=code.relative_to(root).as_posix(), analysis_code_sha256=file_hash(code),
                         result_analysis_workbook=analysis.relative_to(root).as_posix(), analysis_execution_status="accepted",
                         result_analysis_status="passed", analysis_methods=["coefficient sensitivity"])
            entry["solver_execution"]["analysis"] = {
                "bundle_sha256": fingerprint["bundle_sha256"], "validated_bundle_sha256": fingerprint["bundle_sha256"]}
            for field in ("artifact_hashes", "validated_artifact_hashes"):
                entry[field].update(analysis_code=file_hash(code), result_analysis_workbook=file_hash(analysis))
            save_state(root, state)
            self.assertIn("validated_results", hydrate_project_context(root, "Q1")["verified_artifacts"])
            code.write_text(code.read_text(encoding="utf-8") + "\n% edited after execution\n", encoding="utf-8")
            verified = hydrate_project_context(root, "Q1")["verified_artifacts"]
            self.assertIn("accepted_solution_workbook", verified)
            self.assertNotIn("validated_results", verified)

    def test_matlab_package_requires_real_solver_and_all_helpers(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = qualified_fixture(root, helper=True)
            state["artifacts"] = {"compiled_pdf": "final_latex/main.pdf", "latex_source": "final_latex/main.tex"}
            state["subproblems"]["Q1"]["matlab_script"] = "问题一求解/q1_plot.m"
            for relative in ("模型论文框架.md", "final_latex/main.pdf", "final_latex/main.tex", "问题一求解/q1_plot.m"):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("synthetic package boundary fixture", encoding="utf-8")
            save_state(root, state)
            required, issues = reproducibility_requirements(root, state)
            self.assertEqual(issues, [])
            self.assertIn("问题一求解/helper.m", required)
            self.assertFalse(any(path.endswith(".py") for path in required))
            self.assertEqual(VALIDATOR.validate_package(root, archive(root))["status"], "passed")
            for missing in ("问题一求解/q1_solver.m", "问题一求解/helper.m"):
                self.assertEqual(VALIDATOR.validate_package(root, archive(root, omit=[missing]))["status"], "failed")

    def test_trace_current_matlab_anchor_checks_role_and_function(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            entry = qualified_fixture(root)["subproblems"]["Q1"]
            anchor = entry["code"] + "#q1_solver"
            self.assertEqual(_implementation_anchor_issues(anchor, entry, root, project_backend="matlab"), [])
            self.assertTrue(_implementation_anchor_issues(entry["code"] + "#missing_function", entry, root,
                                                           project_backend="matlab"))
            self.assertTrue(_implementation_anchor_issues("问题一求解/q1_plot.m", entry, root,
                                                           project_backend="matlab"))
            code = root / entry["code"]
            code.write_text(code.read_text(encoding="utf-8") + "\n%{\nfunction ghost()\n%}\n", encoding="utf-8")
            fingerprint = stage_code.stage_code_fingerprint(root, code)
            entry["primary_code_sha256"] = fingerprint["entry_sha256"]
            entry["solver_execution"]["primary"].update(bundle_sha256=fingerprint["bundle_sha256"],
                                                       validated_bundle_sha256=fingerprint["bundle_sha256"])
            self.assertEqual(_implementation_anchor_issues(anchor, entry, root, project_backend="matlab"), [])
            self.assertTrue(_implementation_anchor_issues(entry["code"] + "#ghost", entry, root,
                                                           project_backend="matlab"))

    def test_selection_reason_change_does_not_invalidate_current_result(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = qualified_fixture(root)
            entry = state["subproblems"]["Q1"]
            state["execution"]["solver_backend_selection_reason"] = "Updated explanation, identical source"
            observed, paths, issues = snapshot._solver_observations(
                root, "问题一", entry, project_backend="matlab", current_state=True)
            self.assertEqual(issues, [])
            current = {"artifact_hashes": dict(entry["artifact_hashes"]),
                       "primary_code_sha256": file_hash(paths["primary"]), "solver_execution_observed": observed,
                       "project_backend": "matlab"}
            self.assertEqual(sync._snapshot_transition_events(entry, current), [])

    def test_same_backend_result_dependencies_propagate_source_drift(self):
        for backend in ("python", "matlab"):
            for event in ("primary_code_changed", "analysis_code_changed"):
                with self.subTest(backend=backend, event=event):
                    state = state_with_dependency("result")
                    state["execution"] = {"solver_backend": backend,
                                          "solver_backend_selection_reason": "Synthetic whole-problem review"}
                    report = sync.STATE_TRANSITIONS.apply_transition(
                        state, event=event, source_question="Q1", contract=sync.STATE_TRANSITION_CONTRACT)
                    q2 = state["subproblems"]["Q2"]
                    self.assertEqual("Q2" in report["affected_questions"], event == "primary_code_changed")
                    self.assertEqual(q2["human_model_approval_status"], "approved")
                    self.assertEqual(q2["primary_execution_status"], "pending" if event == "primary_code_changed" else "accepted")

    def test_python_11_cannot_lose_metadata_to_evade_bundle_consumers(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = qualified_fixture(root)
            state["execution"] = {"solver_backend": "python",
                                  "solver_backend_selection_reason": "Synthetic whole-problem review"}
            entry = state["subproblems"]["Q1"]
            matlab = root / entry["code"]
            _, config = stage_code.parse_stage_config(matlab)
            helper = root / "问题一求解/helper.py"
            helper.write_text("def solve():\n    return 3.0\n", encoding="utf-8")
            config.update(solver_backend="python", code_dependencies=[{
                "path": helper.relative_to(root).as_posix(), "sha256": file_hash(helper)}])
            code = root / "问题一求解/问题一求解.py"
            code.write_text("RUN_CONFIG = " + repr(config) + "\n", encoding="utf-8")
            matlab.unlink()
            entry.update(code=code.relative_to(root).as_posix(), primary_code_sha256=file_hash(code))
            entry.pop("solver_execution")
            for field in ("artifact_hashes", "validated_artifact_hashes"):
                entry[field]["primary_code"] = file_hash(code)
            save_state(root, state)
            required, issues = reproducibility_requirements(root, state)
            self.assertIn(helper.relative_to(root).as_posix(), required)
            self.assertTrue(issues, issues)
            observed, paths, issues = snapshot._solver_observations(
                root, "问题一", entry, project_backend="python", current_state=True)
            self.assertTrue(issues)
            current = {"artifact_hashes": dict(entry["artifact_hashes"]),
                       "primary_code_sha256": file_hash(code), "solver_execution_observed": observed,
                       "project_backend": "python"}
            self.assertIn("primary_code_changed", sync._snapshot_transition_events(entry, current))
            self.assertTrue(_implementation_anchor_issues("unresolvable legacy prose", entry, root,
                                                           project_backend="python"))


if __name__ == "__main__":
    unittest.main()
