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


def load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


RUNTIME = load_module("p7_runtime_assurance", "scripts/runtime_assurance.py")
SNAPSHOT = load_module("p7_project_snapshot", "scripts/project_snapshot.py")
SYNC = load_module("p7_sync_project", "scripts/sync_project.py")


class TestP7ConditionalAnalysisAppendix(unittest.TestCase):
    def _state(self, digest: str, *, reason: str | None):
        q1 = {
            "status": "analyzed",
            "selected_model": "demo",
            "capabilities": {
                "has_explicit_constraints": False,
                "requires_feasibility_check": False,
                "requires_equilibrium_residual": False,
                "requires_conservation_residual": False,
                "requires_discretization_check": False,
                "requires_convergence_diagnostic": False,
            },
            "result_quality_status": "passed",
            "result_analysis_status": "not_required",
            "framework_section": "Q1",
            "result_summary_status": "current",
            "primary_execution_status": "accepted",
            "analysis_execution_status": "pending",
            "solution_workbook": "问题一求解/问题一求解结果.xlsx",
            "artifact_hashes": {"solution_workbook": digest},
            "validated_artifact_hashes": {"solution_workbook": digest},
        }
        if reason is not None:
            q1["result_analysis_requirement_reason"] = reason
        return {
            "project": {"competition": "demo", "problem": "A", "current_phase": "figure_evidence"},
            "requirements": {"total": 1, "completed": [], "pending": []},
            "decisions": {},
            "subproblems": {"Q1": q1},
            "variables": {"locked": [], "source": {}},
            "paper_framework": {
                "path": "模型论文框架.md", "version": "v0.8-project-memory",
                "sync_status": "current", "last_sync_scope": "results",
                "proposition_count": 0, "proposition_status": "not_assessed", "propositions": [],
            },
            "artifacts": {"code": [], "results": [], "figures": [], "papers": []},
            "risks": [],
            "next_gate": {"module": "figure_evidence", "condition": "validated_results"},
        }

    def test_runtime_promotes_validated_results_without_fake_analysis_workbook(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workbook = root / "问题一求解" / "问题一求解结果.xlsx"
            workbook.parent.mkdir(parents=True)
            workbook.write_bytes(b"accepted-primary")
            digest = hashlib.sha256(workbook.read_bytes()).hexdigest()
            state = self._state(digest, reason="题目与计划正文只使用当前计算世界，且无未关闭的03B风险。")
            (root / "state").mkdir()
            (root / "state/project_state.yaml").write_text(
                yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            hydration = RUNTIME.hydrate_project_context(root, "Q1")
            self.assertIn("accepted_solution_workbook", hydration["verified_artifacts"])
            self.assertIn("validated_results", hydration["verified_artifacts"])
            self.assertNotIn("accepted_result_analysis_workbook", hydration["verified_artifacts"])
            self.assertNotIn("result_analysis_workbook", hydration["verified_artifacts"])
            skip = [row for row in hydration["artifact_evidence"] if row["artifact"] == "result_analysis_not_required"]
            self.assertEqual(skip[0]["status"], "verified")

    def test_not_required_without_reason_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workbook = root / "问题一求解" / "问题一求解结果.xlsx"
            workbook.parent.mkdir(parents=True)
            workbook.write_bytes(b"accepted-primary")
            digest = hashlib.sha256(workbook.read_bytes()).hexdigest()
            state = self._state(digest, reason=None)
            (root / "state").mkdir()
            (root / "state/project_state.yaml").write_text(
                yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            hydration = RUNTIME.hydrate_project_context(root, "Q1")
            self.assertNotIn("validated_results", hydration["verified_artifacts"])
            issues = SYNC._formal_state_issues({"result_analysis_report"}, state)
            self.assertTrue(any("requirement_reason" in item for item in issues))

    def test_contracts_make_analysis_and_appendix_conditional(self):
        router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))
        manifest = yaml.safe_load((ROOT / "core/module_manifest.yaml").read_text(encoding="utf-8"))
        template = yaml.safe_load((ROOT / "templates/latex/cumcm/hsk/template_manifest.yaml").read_text(encoding="utf-8"))
        self.assertIn("result_analysis", router["execution_contract"]["conditional_modules"])
        self.assertIn("validated_results", router["runtime_segments"]["analysis_execution"]["satisfied_when"]["any"])
        self.assertTrue(manifest["modules"]["result_analysis"]["conditional"])
        self.assertNotIn("result_analysis_workbook", manifest["modules"]["figure_evidence"]["inputs"])
        self.assertEqual(
            manifest["modules"]["figure_evidence"]["conditional_inputs"]["result_analysis_workbook"]["when"],
            "result_analysis_status == passed",
        )
        appendix = next(item for item in template["paper_skeleton"]["ordered_slots"] if item["id"] == "appendix")
        self.assertFalse(appendix["required"])
        self.assertFalse(appendix["default_active"])
        main = (ROOT / "templates/latex/cumcm/hsk/hsk_main.tex").read_text(encoding="utf-8")
        active_appendix = [line for line in main.splitlines() if line.strip() == r"\input{appendices/appendices}"]
        self.assertEqual(active_appendix, [])

    def test_user_execution_and_matlab_template_follow_conditional_analysis(self):
        execution = yaml.safe_load((ROOT / "core/user_execution_contract.yaml").read_text(encoding="utf-8"))
        self.assertEqual(
            execution["code_delivery"]["stage_activation"]["analysis"],
            "accepted_primary_workbook and analysis_necessity_gate == required",
        )
        analysis_policy = execution["three_stage_policy"]["analysis"]
        self.assertIn("Gate=required", analysis_policy["activation"])
        self.assertIn("Gate=not_required", analysis_policy["role"])

        matlab = (ROOT / "templates/matlab/q1_plot.m").read_text(encoding="utf-8")
        self.assertIn("resultAnalysisBook = fullfile", matlab)
        self.assertIn("sourceBook = solutionBook;", matlab)
        self.assertNotIn("assert(isfile(resultAnalysisBook)", matlab)
        self.assertIn("assert(isfile(sourceBook)", matlab)


if __name__ == "__main__":
    unittest.main()