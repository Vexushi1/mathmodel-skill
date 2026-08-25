import importlib.util
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_resolver():
    path = ROOT / "scripts/resolve_workflow.py"
    spec = importlib.util.spec_from_file_location("contract_closure_resolver", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestContractClosure(unittest.TestCase):
    def setUp(self):
        self.manifest = yaml.safe_load((ROOT / "core/module_manifest.yaml").read_text(encoding="utf-8"))
        self.router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))
        self.resolver = load_resolver()

    def test_all_module_and_gate_artifacts_are_catalogued(self):
        known = set(self.manifest["artifact_catalog"]) | set(self.manifest["external_artifacts"])
        for name, module in self.manifest["modules"].items():
            for field in ("inputs", "outputs"):
                self.assertEqual(set(module[field]) - known, set(), f"{name}.{field}")
        for name, gate in self.manifest["utility_gates"].items():
            for field in ("inputs", "outputs"):
                self.assertEqual(set(gate[field]) - known, set(), f"gate {name}.{field}")

    def test_initial_full_workflow_closes_at_primary_user_execution_boundary(self):
        available = set(self.manifest["modules"]["model_design"]["outputs"])
        available.add("locked_model_spec")
        plan = self.resolver.resolve_workflow(
            "full_workflow",
            objective="optimization",
            structures=["stochastic"],
            available_artifacts=sorted(available),
            preprocessing_decision="not_needed",
        )
        self.assertEqual(plan["pause_state"], "awaiting_user_execution")
        self.assertIn("modules/03_solve_validate.md", plan["modules"])
        self.assertNotIn("modules/03_result_analysis.md", plan["modules"])
        self.assertEqual(
            [item["name"] for item in plan["pre_delivery_gates"]],
            ["semantic_governance", "model_approval", "code_delivery"],
        )

    def test_user_execution_receipt_produces_accepted_results(self):
        gate = self.manifest["utility_gates"]["user_execution_receipt"]
        outputs = set(gate["outputs"])
        self.assertTrue({"accepted_solution_workbook", "result_quality_report", "solved_results", "accepted_result_analysis_workbook", "validated_results"}.issubset(outputs))
        self.assertEqual(gate["path"], "scripts/validate_user_execution.py")

    def test_project_sync_is_real_producer(self):
        gate = self.manifest["utility_gates"]["project_sync"]
        self.assertEqual(gate["path"], "scripts/sync_project.py")
        self.assertTrue((ROOT / gate["path"]).is_file())
        self.assertEqual(set(gate["outputs"]), {"project_state", "sync_report"})
        self.assertIn("<delivery_scope>", gate["command"])

    def test_cleanup_precedes_compile_in_router_order(self):
        order = self.router["execution_contract"]["workflow_order"]
        self.assertLess(order.index("writing_latex"), order.index("ai_cleanup"))
        self.assertLess(order.index("ai_cleanup"), order.index("latex_compile_quality"))
        compile_inputs = set(self.manifest["modules"]["latex_compile_quality"]["inputs"])
        self.assertIn("latex_source", compile_inputs)
        self.assertNotIn("latex_source_draft", compile_inputs)


if __name__ == "__main__":
    unittest.main()
