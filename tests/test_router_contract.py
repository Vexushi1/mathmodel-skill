import importlib.util
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_resolver():
    spec = importlib.util.spec_from_file_location("resolve_workflow", ROOT / "scripts/resolve_workflow.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestRouterContract(unittest.TestCase):
    def setUp(self):
        self.router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))
        self.resolver = load_resolver()

    def test_bootstrap_and_sync_route_exist(self):
        self.assertEqual(self.router["bootstrap"], "core/bootstrap.yaml")
        self.assertIn("project_sync", self.router["routing"])

    def test_multi_intent_merge_order_and_outputs(self):
        plan = self.resolver.resolve_workflow(
            ["code_and_solution", "figures"],
            objective="optimization",
            structures=["stochastic"],
            competition="CUMCM",
        )
        self.assertLess(plan["modules"].index("modules/03_solve_validate.md"), plan["modules"].index("modules/04_figure_evidence.md"))
        self.assertIn("model_paper_framework", plan["terminal_outputs"])
        self.assertIn("sync_report", plan["terminal_outputs"])
        self.assertTrue(plan["sync_required_before_delivery"])

    def test_request_inference(self):
        plan = self.resolver.resolve_workflow(
            request="继续求解问题三并生成MATLAB敏感性图",
            objective="optimization",
            structures=["stochastic"],
        )
        self.assertIn("modules/03_solve_validate.md", plan["modules"])
        self.assertIn("modules/04_figure_evidence.md", plan["modules"])

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
