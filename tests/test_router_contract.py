import importlib.util
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_resolver():
    spec = importlib.util.spec_from_file_location(
        "resolve_workflow", ROOT / "scripts/resolve_workflow.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestRouterContract(unittest.TestCase):
    def setUp(self):
        self.router = yaml.safe_load(
            (ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8")
        )
        self.resolver = load_resolver()

    def test_bootstrap_and_execution_routes_exist(self):
        self.assertEqual(self.router["bootstrap"], "core/bootstrap.yaml")
        self.assertIn("project_sync", self.router["routing"])
        self.assertIn("returned_workbook_validation", self.router["routing"])
        self.assertEqual(
            self.router["execution_contract"]["formal_delivery_gates"],
            ["semantic_governance", "project_sync"],
        )
        self.assertEqual(
            self.router["execution_contract"]["code_stage_gates"],
            ["semantic_governance", "code_delivery"],
        )
        self.assertFalse(
            self.router["execution_contract"]["task_code_execution_allowed"]
        )

    def test_code_plus_figures_stops_at_primary_user_gate(self):
        plan = self.resolver.resolve_workflow(
            ["code_and_solution", "figures"],
            objective="optimization",
            structures=["stochastic"],
            competition="CUMCM",
        )
        self.assertIn("modules/03_solve_validate.md", plan["modules"])
        self.assertNotIn("modules/03_result_analysis.md", plan["modules"])
        self.assertNotIn("modules/04_figure_evidence.md", plan["modules"])
        self.assertEqual(plan["delivery_scope"], "code")
        self.assertEqual(
            [item["name"] for item in plan["pre_delivery_gates"]],
            ["semantic_governance", "code_delivery"],
        )
        self.assertIn("python_code", plan["terminal_outputs"])
        self.assertIn("semantic_governance_report", plan["terminal_outputs"])
        self.assertIn("awaiting_user_execution", plan["terminal_outputs"])
        self.assertNotIn("sync_report", plan["terminal_outputs"])
        self.assertTrue(plan["pause_for_user_execution"])
        self.assertFalse(plan["task_code_execution_allowed"])

    def test_nonformal_route_has_no_gate(self):
        plan = self.resolver.resolve_workflow("problem_analysis")
        self.assertEqual(plan["pre_delivery_gates"], [])
        self.assertFalse(plan["sync_required_before_delivery"])
        self.assertNotIn("sync_report", plan["available_after_plan"])

    def test_request_inference_respects_primary_gate(self):
        plan = self.resolver.resolve_workflow(
            request="继续求解问题三并生成MATLAB敏感性图",
            objective="optimization",
            structures=["stochastic"],
        )
        self.assertIn("modules/03_solve_validate.md", plan["modules"])
        self.assertNotIn("modules/03_result_analysis.md", plan["modules"])
        self.assertNotIn("modules/04_figure_evidence.md", plan["modules"])
        self.assertTrue(plan["pause_for_user_execution"])
        self.assertEqual(
            [item["name"] for item in plan["pre_delivery_gates"]],
            ["semantic_governance", "code_delivery"],
        )

    def test_result_analysis_without_accepted_primary_returns_primary_code(self):
        plan = self.resolver.resolve_workflow(
            "result_analysis", objective="prediction", structures=["temporal"]
        )
        self.assertFalse(plan["dependency_closure_applied"])
        self.assertIn("modules/03_solve_validate.md", plan["modules"])
        self.assertNotIn("modules/03_result_analysis.md", plan["modules"])
        self.assertIn("python_code", plan["module_terminal_outputs"])
        self.assertTrue(plan["pause_for_user_execution"])
        self.assertEqual(
            [item["name"] for item in plan["pre_delivery_gates"]],
            ["semantic_governance", "code_delivery"],
        )

    def test_result_analysis_empty_state_returns_primary_code(self):
        plan = self.resolver.resolve_workflow(
            "result_analysis",
            objective="prediction",
            structures=["temporal"],
            available_artifacts=[],
        )
        self.assertTrue(plan["dependency_closure_applied"])
        self.assertIn("modules/03_solve_validate.md", plan["modules"])
        self.assertNotIn("modules/03_result_analysis.md", plan["modules"])

    def test_result_analysis_reuses_accepted_primary_workbook(self):
        plan = self.resolver.resolve_workflow(
            "result_analysis",
            objective="prediction",
            structures=["temporal"],
            available_artifacts=[
                "accepted_solution_workbook",
                "result_quality_report",
            ],
        )
        self.assertTrue(plan["dependency_closure_applied"])
        self.assertNotIn("modules/03_solve_validate.md", plan["modules"])
        self.assertIn("modules/03_result_analysis.md", plan["modules"])
        self.assertIn("result_analysis_code", plan["module_terminal_outputs"])
        self.assertTrue(plan["pause_for_user_execution"])
        self.assertEqual(
            [item["name"] for item in plan["pre_delivery_gates"]],
            ["semantic_governance", "code_delivery"],
        )

    def test_full_workflow_continues_after_both_workbooks_are_accepted(self):
        plan = self.resolver.resolve_workflow(
            "full_workflow",
            objective="optimization",
            structures=["stochastic"],
            competition="CUMCM",
            available_artifacts=[
                "solution_workbook",
                "accepted_solution_workbook",
                "result_quality_report",
                "result_analysis_workbook",
                "accepted_result_analysis_workbook",
                "validated_results",
            ],
        )
        expected = [
            "modules/04_figure_evidence.md",
            "modules/05_writing/latex.md",
            "modules/05_writing/ai_cleanup.md",
            "modules/05_latex_compile_quality.md",
            "modules/06_review_delivery.md",
        ]
        for module in expected:
            self.assertIn(module, plan["modules"])
        positions = [plan["modules"].index(module) for module in expected]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("modules/03_solve_validate.md", plan["modules"])
        self.assertNotIn("modules/03_result_analysis.md", plan["modules"])
        self.assertEqual(plan["delivery_scope"], "submission")
        self.assertEqual(
            [item["name"] for item in plan["pre_delivery_gates"]],
            ["semantic_governance", "project_sync", "submission_package_validation"],
        )
        self.assertFalse(plan["pause_for_user_execution"])
        self.assertTrue(plan["sync_required_before_delivery"])

    def test_legacy_labels_remain_compatible(self):
        plan = self.resolver.resolve_workflow(
            "full_solution", primary="mechanism", secondary=["optimization"]
        )
        self.assertEqual(plan["classification"]["objective"], "explanation")
        self.assertIn("packs/task/mechanism.md", plan["packs"])
        self.assertIn("packs/task/optimization.md", plan["packs"])

    def test_proposition_pack_is_lazy(self):
        ordinary = self.resolver.resolve_workflow(
            "model_selection", objective="optimization"
        )
        proof = self.resolver.resolve_workflow("proposition_proof")
        self.assertNotIn("packs/artifact/proposition_proof.md", ordinary["packs"])
        self.assertIn("packs/artifact/proposition_proof.md", proof["packs"])
        self.assertEqual(
            [item["name"] for item in ordinary["pre_delivery_gates"]],
            ["semantic_governance", "project_sync"],
        )


if __name__ == "__main__":
    unittest.main()
