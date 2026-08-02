import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class TestContractClosure(unittest.TestCase):
    def setUp(self):
        self.manifest = yaml.safe_load(
            (ROOT / "core/module_manifest.yaml").read_text(encoding="utf-8")
        )

    def test_all_module_and_gate_artifacts_are_catalogued(self):
        known = set(self.manifest["artifact_catalog"]) | set(
            self.manifest["external_artifacts"]
        )
        for name, module in self.manifest["modules"].items():
            for field in ("inputs", "outputs"):
                self.assertEqual(set(module[field]) - known, set(), f"{name}.{field}")
        for name, gate in self.manifest["utility_gates"].items():
            for field in ("inputs", "outputs"):
                self.assertEqual(set(gate[field]) - known, set(), f"gate {name}.{field}")

    def test_initial_full_workflow_closes_at_code_delivery_gate(self):
        available = set(self.manifest["external_artifacts"])
        modules = self.manifest["modules"]
        profile = self.manifest["workflow_profiles"]["full_workflow"]
        self.assertEqual(
            profile["modules"], ["problem_audit", "model_design", "solve_validate"]
        )
        for name in profile["modules"]:
            missing = set(modules[name]["inputs"]) - available
            self.assertEqual(missing, set(), name)
            available.update(modules[name]["outputs"])
        self.assertNotIn("solution_workbook", available)
        for gate_name in profile["pre_delivery_gates"]:
            gate = self.manifest["utility_gates"][gate_name]
            self.assertEqual(
                set(gate["inputs"])
                - available
                - set(self.manifest["external_artifacts"]),
                set(),
            )
            available.update(gate["outputs"])
        self.assertTrue(set(profile["terminal_outputs"]).issubset(available))
        self.assertIn("awaiting_user_execution", available)
        self.assertIn("project_state", available)
        self.assertNotIn("sync_report", available)

    def test_user_execution_receipt_produces_accepted_results(self):
        gate = self.manifest["utility_gates"]["user_execution_receipt"]
        outputs = set(gate["outputs"])
        self.assertTrue(
            {
                "accepted_solution_workbook",
                "result_quality_report",
                "solved_results",
                "accepted_result_analysis_workbook",
                "validated_results",
            }.issubset(outputs)
        )
        self.assertEqual(gate["path"], "scripts/validate_user_execution.py")

    def test_project_sync_is_real_producer(self):
        gate = self.manifest["utility_gates"]["project_sync"]
        self.assertEqual(gate["path"], "scripts/sync_project.py")
        self.assertTrue((ROOT / gate["path"]).is_file())
        self.assertEqual(set(gate["outputs"]), {"project_state", "sync_report"})
        self.assertIn("<delivery_scope>", gate["command"])

    def test_cleanup_precedes_compile_in_global_workflow(self):
        order = self.manifest["workflow_order"]
        self.assertLess(order.index("writing_latex"), order.index("ai_cleanup"))
        self.assertLess(order.index("ai_cleanup"), order.index("latex_compile_quality"))
        compile_inputs = set(
            self.manifest["modules"]["latex_compile_quality"]["inputs"]
        )
        self.assertIn("latex_source", compile_inputs)
        self.assertNotIn("latex_source_draft", compile_inputs)


if __name__ == "__main__":
    unittest.main()
