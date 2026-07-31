import importlib.util
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_resolver():
    spec = importlib.util.spec_from_file_location("resolve_workflow", ROOT / "scripts/resolve_workflow.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestRouterContract(unittest.TestCase):
    def setUp(self):
        self.router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))
        self.resolver = load_resolver()

    def test_bootstrap_and_sync_route_exist(self):
        self.assertEqual(self.router["bootstrap"], "core/bootstrap.yaml")
        self.assertIn("project_sync", self.router["routing"])
        self.assertEqual(self.router["execution_contract"]["formal_delivery_gates"], ["project_sync"])

    def test_multi_intent_merge_orders_solve_analysis_and_figures(self):
        plan = self.resolver.resolve_workflow(
            ["code_and_solution", "figures"],
            objective="optimization",
            structures=["stochastic"],
            competition="CUMCM",
        )
        solve = plan["modules"].index("modules/03_solve_validate.md")
        analysis = plan["modules"].index("modules/03_result_analysis.md")
        figures = plan["modules"].index("modules/04_figure_evidence.md")
        self.assertLess(solve, analysis)
        self.assertLess(analysis, figures)
        self.assertIn("model_paper_framework", plan["module_terminal_outputs"])
        self.assertNotIn("sync_report", plan["available_after_modules"])
        self.assertEqual([item["name"] for item in plan["pre_delivery_gates"]], ["project_sync"])
        self.assertEqual(plan["delivery_scope"], "figures")
        self.assertIn("--delivery-scope figures", plan["pre_delivery_gates"][0]["command"])
        self.assertIn("sync_report", plan["available_after_plan"])
        self.assertIn("sync_report", plan["terminal_outputs"])
        self.assertTrue(plan["sync_required_before_delivery"])

    def test_nonformal_route_has_no_gate(self):
        plan = self.resolver.resolve_workflow("problem_analysis")
        self.assertEqual(plan["pre_delivery_gates"], [])
        self.assertFalse(plan["sync_required_before_delivery"])
        self.assertNotIn("sync_report", plan["available_after_plan"])

    def test_request_inference(self):
        plan = self.resolver.resolve_workflow(
            request="继续求解问题三并生成MATLAB敏感性图",
            objective="optimization",
            structures=["stochastic"],
        )
        self.assertIn("modules/03_solve_validate.md", plan["modules"])
        self.assertIn("modules/03_result_analysis.md", plan["modules"])
        self.assertIn("modules/04_figure_evidence.md", plan["modules"])

    def test_result_analysis_request_does_not_reload_primary_solve(self):
        plan = self.resolver.resolve_workflow(
            "result_analysis", objective="prediction", structures=["temporal"]
        )
        self.assertIn("modules/03_result_analysis.md", plan["modules"])
        self.assertNotIn("modules/03_solve_validate.md", plan["modules"])
        self.assertIn("result_analysis_workbook", plan["module_terminal_outputs"])

    def test_legacy_labels_remain_compatible(self):
        plan = self.resolver.resolve_workflow("full_solution", primary="mechanism", secondary=["optimization"])
        self.assertEqual(plan["classification"]["objective"], "explanation")
        self.assertIn("packs/task/mechanism.md", plan["packs"])
        self.assertIn("packs/task/optimization.md", plan["packs"])

    def test_proposition_pack_is_lazy(self):
        ordinary = self.resolver.resolve_workflow("model_selection", objective="optimization")
        proof = self.resolver.resolve_workflow("proposition_proof")
        self.assertNotIn("packs/artifact/proposition_proof.md", ordinary["packs"])
        self.assertIn("packs/artifact/proposition_proof.md", proof["packs"])


if __name__ == "__main__":
    unittest.main()
