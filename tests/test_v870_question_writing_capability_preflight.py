import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "core" / "writing_runtime_contract.yaml"
REASONING = ROOT / "core" / "writing_reasoning_contract.yaml"
OUTPUT = ROOT / "core" / "output_contract.yaml"
FIXTURE = ROOT / "tests" / "fixtures" / "writing_capability_preflight_cases.yaml"
PROTOCOL = ROOT / "modules" / "05_writing" / "paper_writing_protocol.md"
CLEANUP = ROOT / "modules" / "05_writing" / "ai_cleanup.md"
REVIEW = ROOT / "modules" / "06_review_delivery.md"
FRAMEWORK = ROOT / "templates" / "model" / "model_paper_framework.md"


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class TestV870QuestionWritingCapabilityPreflight(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = load_yaml(RUNTIME)
        cls.reasoning = load_yaml(REASONING)
        cls.output = load_yaml(OUTPUT)
        cls.cases = load_yaml(FIXTURE)["cases"]
        cls.protocol = read(PROTOCOL)
        cls.cleanup = read(CLEANUP)
        cls.review = read(REVIEW)
        cls.framework = read(FRAMEWORK)
        cls.preflight = cls.runtime["per_question_writing_capability_preflight"]
        cls.activation = cls.preflight["activation"]

    def activation_for(self, case):
        state = case["project_state"]
        active = set()
        overall = "current"

        summary = state.get("core_model_summary", "missing")
        summary_rule = self.activation["core_model_summary"]["rules"].get(summary)
        if summary_rule is None:
            overall = "needs_adjudication"
        else:
            active.update(summary_rule.get("activate", []))
            if summary_rule.get("status") == "needs_adjudication":
                overall = "needs_adjudication"

        proposition = state.get("proposition_proof", "missing")
        proposition_rule = self.activation["proposition_proof"]["rules"].get(proposition)
        if proposition_rule is None:
            overall = "needs_adjudication"
        else:
            active.update(proposition_rule.get("activate", []))
            if proposition_rule.get("status") == "review_required":
                overall = "review_required"
            elif proposition_rule.get("status") == "needs_adjudication" and overall != "review_required":
                overall = "needs_adjudication"

        algorithm = state.get("algorithm_presentation", "missing")
        algorithm_rule = self.activation["algorithm_presentation"]["rules"].get(algorithm)
        if algorithm_rule is None:
            overall = "needs_adjudication"
        else:
            active.update(algorithm_rule.get("activate", []))
            if algorithm_rule.get("status") == "needs_adjudication" and overall != "review_required":
                overall = "needs_adjudication"

        if not state.get("formula_roles") and overall == "current":
            overall = "needs_adjudication"

        return overall, active

    def test_preflight_is_mandatory_inside_each_question_stage(self):
        self.assertEqual("mandatory_before_each_question_write", self.preflight["mode"])
        stages = {
            stage["id"]: stage
            for stage in self.runtime["template_first_progressive_authoring"]["stages"]
        }
        question = stages["question_model_solution_result_validation"]
        before = question["before_write_preflight"]
        self.assertTrue(before["required_before_write_now"])
        self.assertTrue(before["dispatch_from_project_state"])
        self.assertIn("current_question_evidence_bundle", before["read_now"])
        self.assertIn("逐问写作能力预检", " ".join(before["read_now"]))

    def test_current_question_bundle_has_explicit_composition(self):
        bundle = self.runtime["current_question_evidence_bundle"]
        self.assertEqual(
            {
                "current_question_model_facts",
                "current_question_formula_trace",
                "current_question_core_model_summary_state",
                "current_question_proposition_plan",
                "current_question_algorithm_trace",
                "current_question_numeric_result_evidence",
                "current_question_validation_evidence",
                "current_question_figure_map",
            },
            set(bundle["includes"]),
        )
        self.assertEqual(
            "current_question_model_formula_algorithm_result_and_figure_evidence",
            bundle["legacy_token"],
        )

    def test_core_model_summary_is_first_class_compact_capability(self):
        ordinary = self.runtime["semantic_capabilities"]["ordinary_writing"]
        self.assertIn("adaptive_core_model_summary", ordinary)
        summary = self.activation["core_model_summary"]
        self.assertEqual(
            "core/writing_reasoning_contract.yaml#adaptive_core_model_summary",
            summary["authority"],
        )
        self.assertIn(
            "adaptive_core_model_summary",
            summary["rules"]["required"]["activate"],
        )

    def test_project_state_activates_capabilities_without_user_keywords(self):
        for case in self.cases:
            with self.subTest(case=case["id"]):
                status, active = self.activation_for(case)
                expected = case["expect"]
                self.assertEqual(expected["status"], status)
                for item in expected.get("activate", []):
                    self.assertIn(item, active)
                for item in expected.get("do_not_activate", []):
                    self.assertNotIn(item, active)
                if not case.get("user_prompt_mentions_capability", False):
                    self.assertFalse(case["user_prompt_mentions_capability"])

    def test_missing_state_is_not_silently_defaulted(self):
        missing = next(case for case in self.cases if case["id"] == "missing_states_require_adjudication")
        status, _ = self.activation_for(missing)
        self.assertEqual("needs_adjudication", status)
        for family in ("core_model_summary", "proposition_proof", "algorithm_presentation"):
            rule = self.activation[family]["rules"]["missing"]
            self.assertEqual("needs_adjudication", rule["status"])
            self.assertIn("silently", rule["prohibition"])

    def test_stale_proposition_cannot_surface_as_current(self):
        stale = self.activation["proposition_proof"]["rules"]["stale"]
        self.assertEqual("review_required", stale["status"])
        self.assertEqual("stale_proposition_must_not_surface_as_current", stale["prohibition"])
        self.assertIn("packs/artifact/proposition_proof.md", stale["activate"])

    def test_algorithm_not_needed_keeps_compact_runtime(self):
        self.assertEqual([], self.activation["algorithm_presentation"]["rules"]["not_needed"]["activate"])
        preload = self.runtime["ordinary_writing_resource_order"]
        self.assertNotIn("core/writing_reasoning_contract.yaml", preload)
        self.assertNotIn("packs/artifact/proposition_proof.md", preload)
        self.assertNotIn("packs/artifact/algorithm_flow.md", preload)
        self.assertFalse(self.preflight["compact_runtime_boundary"]["full_reasoning_authority_eager_preload"])

    def test_high_signal_proposition_review_does_not_auto_create(self):
        not_assessed = self.activation["proposition_proof"]["rules"]["not_assessed"]
        self.assertTrue(not_assessed["high_signal_review_when_any"])
        self.assertEqual("semantic_proposition_necessity_review_only", not_assessed["high_signal_action"])
        self.assertIn("must_not_auto_create", not_assessed["prohibition"])

    def test_formula_role_taxonomy_is_authoritative_and_traceable(self):
        chain = self.reasoning["formula_reasoning_chain"]
        taxonomy = chain["formula_role_taxonomy"]
        self.assertEqual(
            [
                "final_model_relation",
                "key_bridge_relation",
                "supporting_derivation",
                "routine_algebra",
            ],
            taxonomy["values"],
        )
        self.assertIn("role", chain["internal_trace"]["required_fields"])
        self.assertEqual("normally_not_registered", taxonomy["roles"]["routine_algebra"]["trace_policy"])
        self.assertIn("不是最终 solver 方程", taxonomy["bridge_preservation_rule"])
        self.assertIn("must_not_claim", taxonomy["machine_boundary"])

    def test_summary_uses_final_relations_and_only_needed_bridges(self):
        summary = self.reasoning["adaptive_core_model_summary"]
        content = summary["summary_content"]
        self.assertEqual(["final_model_relation"], content["include_by_default"])
        self.assertEqual(["key_bridge_relation"], content["include_when_recoverability_requires"])
        self.assertEqual(["supporting_derivation", "routine_algebra"], content["exclude_by_default"])
        self.assertTrue(content["no_formula_dump_rule"])
        self.assertIn("final_model_relation", self.protocol)
        self.assertIn("key_bridge_relation", self.protocol)
        self.assertIn("公式大全", self.protocol)

    def test_protocol_requires_preflight_without_prompt_keyword(self):
        self.assertIn("### 1.1 Per-Question Writing Capability Preflight", self.protocol)
        self.assertIn("用户未再次提醒", self.protocol)
        self.assertIn("missing", self.protocol)
        self.assertIn("stale", self.protocol)
        self.assertIn("求解段开始前再次消费本问 Preflight", self.protocol)

    def test_cleanup_preserves_final_and_bridge_relations(self):
        self.assertIn("final_model_relation", self.cleanup)
        self.assertIn("key_bridge_relation", self.cleanup)
        self.assertIn("routine_algebra", self.cleanup)
        self.assertIn("不能仅因“不是最终模型公式”删除", self.cleanup)
        self.assertIn("用户本轮没有再次提到这些能力", self.cleanup)

    def test_review_checks_state_to_activation_instead_of_keywords(self):
        self.assertIn("### Question Writing Capability Activation Review", self.review)
        self.assertIn("项目状态是否在该出现时真的激活了相应能力", self.review)
        self.assertIn("planned/current", self.review)
        self.assertIn("stepwise/pseudocode", self.review)
        self.assertIn("Compact Runtime Boundary", self.review)

    def test_output_contract_exposes_current_pointers_without_deleting_v7_alias(self):
        policy = self.output["writing_policy"]
        self.assertEqual(
            "core/writing_reasoning_contract.yaml#formula_reasoning_chain.formula_role_taxonomy",
            policy["formula_role_contract"],
        )
        self.assertEqual(
            "core/writing_reasoning_contract.yaml#adaptive_core_model_summary",
            policy["core_model_summary_contract"],
        )
        self.assertEqual(
            "core/writing_runtime_contract.yaml#per_question_writing_capability_preflight",
            policy["per_question_writing_preflight_contract"],
        )
        self.assertEqual("deprecated_v7_read_compatibility", policy["core_model_summary_policy_status"])

    def test_framework_records_preflight_and_formula_roles_as_project_facts(self):
        self.assertIn("### 逐问写作能力预检", self.framework)
        self.assertIn("Formula Roles", self.framework)
        self.assertIn("Writing Capability Preflight", self.framework)
        self.assertIn("final_model_relation / key_bridge_relation / supporting_derivation", self.framework)
        self.assertIn("不依赖用户再次提醒", self.framework)


if __name__ == "__main__":
    unittest.main()
