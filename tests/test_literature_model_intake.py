"""P2: research intake is a modeling input, never approval, task execution or a new stage."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from resolve_runtime import resolve_runtime
from resolve_workflow import resolve_workflow

AUTHORITY = "core/literature_research_contract.yaml"
PACK = "packs/artifact/literature_research.md"


class LiteratureModelIntakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))
        cls.contract = yaml.safe_load((ROOT / AUTHORITY).read_text(encoding="utf-8"))
        cls.approval = yaml.safe_load((ROOT / "core/model_approval_contract.yaml").read_text(encoding="utf-8"))

    def test_new_model_intent_loads_real_research_authority_and_original_pause(self):
        p = resolve_runtime("new_problem_design", objective="optimization", structures=[])
        self.assertIn(AUTHORITY, p["load_order"])
        self.assertIn(PACK, p["load_order"])
        self.assertEqual(p["load_order"].count(AUTHORITY), 1)
        self.assertEqual(p["load_order"].count(PACK), 1)
        self.assertIn("modules/01_problem_audit.md", p["modules"])
        self.assertIn("modules/02_model_design.md", p["modules"])
        self.assertEqual(p["pause_state"], "awaiting_model_approval")
        self.assertEqual([g["name"] for g in p["pre_delivery_gates"]], ["semantic_governance"])
        self.assertFalse(p["task_code_execution_allowed"])
        self.assertNotIn("modules/03_solve_validate.md", p["modules"])
        paths = [row["path"] for row in p["reading_plan"]["read_now"]]
        self.assertIn(AUTHORITY, paths)
        self.assertIn(PACK, paths)

    def test_full_request_before_approval_includes_research_but_not_code(self):
        for intent in ("full_solution", "full_workflow", "code_and_solution"):
            with self.subTest(intent=intent):
                p = resolve_runtime(intent, objective="prediction", structures=["temporal"])
                self.assertIn(AUTHORITY, p["load_order"])
                self.assertIn(PACK, p["load_order"])
                self.assertEqual(p["pause_state"], "awaiting_model_approval")
                self.assertEqual([g["name"] for g in p["pre_delivery_gates"]], ["semantic_governance"])
                self.assertNotIn("modules/03_solve_validate.md", p["modules"])

    def test_already_locked_code_route_keeps_original_code_gate_without_search(self):
        p = resolve_workflow("code_and_solution", available_artifacts=["locked_model_spec"])
        self.assertNotIn(AUTHORITY, p["load_order"])
        self.assertNotIn(PACK, p["load_order"])
        self.assertEqual(p["pause_state"], "awaiting_user_execution")
        self.assertEqual([g["name"] for g in p["pre_delivery_gates"]],
                         ["semantic_governance", "model_approval", "code_delivery"])

    def test_simple_problem_audit_does_not_launch_literature_or_model_design(self):
        p = resolve_runtime("problem_analysis")
        self.assertNotIn(AUTHORITY, p["load_order"])
        self.assertNotIn(PACK, p["load_order"])
        self.assertNotIn("modules/02_model_design.md", p["modules"])
        self.assertEqual(p["pre_delivery_gates"], [])
        self.assertIsNone(p["pause_state"])

    def test_model_selection_and_advanced_method_load_literature_even_when_approved(self):
        for intent in ("model_selection", "advanced_method"):
            p = resolve_workflow(intent, available_artifacts=["locked_model_spec"])
            self.assertIn(AUTHORITY, p["load_order"])
            self.assertIn(PACK, p["load_order"])
            self.assertEqual(p["delivery_scope"], "design")
            self.assertEqual(p["pre_delivery_gates"], [])

    def test_explicit_auditor_remains_readonly_not_scholarly_search(self):
        p = resolve_runtime("literature_evidence_audit")
        self.assertEqual(p["pre_delivery_gates"], [])
        self.assertEqual(p["modules"], [])
        self.assertEqual(p["terminal_outputs"], ["literature_evidence_validation_report"])
        self.assertNotIn("locked_model_spec", p["terminal_outputs"])
        self.assertFalse(p["task_code_execution_allowed"])
        self.assertIn("scripts/literature_evidence.py", p["load_order"])

    def test_contract_preserves_report_protocol_and_separates_actual_search(self):
        self.assertEqual(self.contract["version"], "1.1.0")
        self.assertEqual(self.contract["properties"]["protocol_version"]["const"], "1.0.0")
        policy = self.contract["x-research"]
        self.assertEqual(policy["model_design_intake"]["approval_authority"], "core/model_approval_contract.yaml")
        self.assertEqual(policy["model_design_intake"]["framework_creation"],
                         "only_after_proposed_model_spec_under_existing_output_contract")
        self.assertFalse(policy["report_validation_attests_search_executed"])
        self.assertFalse(policy["report_validation_grants_approval_or_numerical_acceptance"])

    def test_model_challenge_has_conditional_literature_checks_but_same_human_gate(self):
        check = self.approval["model_challenge"]
        self.assertIn("literature_method_transfer_when_used", check["reviewer_pass"]["must_check"])
        self.assertIn("literature_recency_anchor_and_novelty_bias_when_used",
                      check["devils_advocate_pass"]["must_check"])
        self.assertTrue(self.approval["human_approval"]["explicit_only"])
        self.assertTrue(self.approval["human_approval"]["silence_is_not_approval"])
        self.assertEqual(self.approval["states"]["pause_state"], "awaiting_model_approval")
        self.assertEqual(self.router["execution_contract"]["workflow_order"][0:2],
                         ["problem_audit", "model_design"])


if __name__ == "__main__":
    unittest.main()
