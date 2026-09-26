"""B2's opt-in inspection route must leave ordinary delivery plans unchanged."""
from pathlib import Path
import sys
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from resolve_runtime import resolve_runtime


class ClaimConsumptionRouteTests(unittest.TestCase):
    def test_explicit_route_is_read_only_and_exposes_one_tool(self):
        plan = resolve_runtime("claim_consumption_audit")
        self.assertEqual(plan["modules"], [])
        self.assertEqual(plan["terminal_outputs"], ["claim_consumption_report"])
        self.assertEqual([gate["name"] for gate in plan["pre_delivery_gates"]], ["claim_consumption"])
        self.assertFalse(plan["task_code_execution_allowed"])
        self.assertFalse(plan["sync_required_before_delivery"])
        self.assertEqual(plan["reading_plan"]["tool_interfaces"][0]["name"], "claim_consumption")
        self.assertIn("core/claim_consumption_contract.yaml", plan["load_order"])
        self.assertNotIn("--write", plan["pre_delivery_gates"][0]["command"])

    def test_inferred_route_does_not_select_b1_or_writing(self):
        plan = resolve_runtime(request="论文主张消费核验")
        self.assertEqual(plan["intents"], ["claim_consumption_audit"])
        self.assertEqual(plan["assurance"]["intent_resolution"]["selected_intents"], ["claim_consumption_audit"])

    def test_ordinary_routes_and_b1_do_not_gain_b2_resource_or_gate(self):
        for intent in (
            "claim_evidence_audit", "new_problem_design", "code_and_solution",
            "returned_workbook_validation", "result_analysis", "figures", "latex", "review",
        ):
            with self.subTest(intent=intent):
                plan = resolve_runtime(intent, objective="optimization")
                self.assertNotIn("claim_consumption", [gate["name"] for gate in plan["pre_delivery_gates"]])
                self.assertNotIn("core/claim_consumption_contract.yaml", plan["load_order"])
                self.assertNotIn("scripts/claim_consumption.py", plan["load_order"])

    def test_manifest_command_and_output_are_inspection_only(self):
        manifest = yaml.safe_load((ROOT / "core/module_manifest.yaml").read_text(encoding="utf-8"))
        gate = manifest["utility_gates"]["claim_consumption"]
        self.assertEqual(gate["path"], "scripts/claim_consumption.py")
        self.assertEqual(gate["outputs"], ["claim_consumption_report"])
        self.assertIn("--tex-main final_latex/main.tex", gate["command"])
        self.assertNotIn("--write", gate["command"])

    def test_enforced_text_resources_are_conditional_on_project_and_formal_scope(self):
        example = yaml.safe_load((ROOT / "state/project_state.example.yaml").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / "state").mkdir()
            state_path = project / "state/project_state.yaml"
            for policy in (None, {"protocol_version": "1.0.0", "mode": "observe"},
                           {"protocol_version": "1.2.0", "mode": "enforce_latex_text"}):
                state = yaml.safe_load(yaml.safe_dump(example, allow_unicode=True))
                if policy is not None:
                    state["paper_framework"]["claim_consumption_policy"] = policy
                state_path.write_text(yaml.safe_dump(state, allow_unicode=True), encoding="utf-8")
                plan = resolve_runtime("latex", project_root=project)
                gates = [gate["name"] for gate in plan["pre_delivery_gates"]]
                self.assertIn("project_sync", gates)
                self.assertNotIn("claim_consumption", gates)
                enabled = policy is not None and policy["mode"] == "enforce_latex_text"
                self.assertEqual("claim_consumption_integration" in plan, enabled)
                self.assertEqual("core/claim_consumption_contract.yaml" in plan["load_order"], enabled)
                self.assertEqual("scripts/claim_consumption.py" in plan["load_order"], enabled)
                if enabled:
                    self.assertEqual(plan["claim_consumption_integration"]["human_semantic_coverage"],
                                     "not_assessed")
                    figures = resolve_runtime("figures", project_root=project)
                    self.assertNotIn("claim_consumption_integration", figures)


if __name__ == "__main__":
    unittest.main()
