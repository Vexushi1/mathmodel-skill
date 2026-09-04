"""v8.6 Model Construction & Solution Rationale contracts.

These tests protect semantic authorities, anti-template boundaries and fixed trial
facts. They do not score prose quality, infer mathematical validity from strings,
or impose heading-count/length quotas.
"""
from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "core/writing_reasoning_contract.yaml"
MODEL_DESIGN = ROOT / "modules/02_model_design.md"
PROTOCOL = ROOT / "modules/05_writing/paper_writing_protocol.md"
CLEANUP = ROOT / "modules/05_writing/ai_cleanup.md"
REVIEW = ROOT / "modules/06_review_delivery.md"
EXAMPLES = ROOT / "modules/05_writing/references/model_construction_solution_rationale_examples.md"
FIXTURE = ROOT / "tests/fixtures/model_construction_solution_cases.yaml"


def read(path):
    return path.read_text(encoding="utf-8")


class ModelConstructionRationaleContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = yaml.safe_load(read(CONTRACT))
        cls.model_design = read(MODEL_DESIGN)
        cls.protocol = read(PROTOCOL)
        cls.cleanup = read(CLEANUP)
        cls.review = read(REVIEW)
        cls.examples = read(EXAMPLES)

    def test_schema_and_single_reasoning_authority(self):
        self.assertEqual(self.contract["schema_version"], "1.8.0")
        rationale = self.contract["model_construction_rationale"]
        self.assertEqual(rationale["governance_level"], "default")
        self.assertEqual(
            rationale["rationale_chain"],
            [
                "current_problem_structure",
                "modeling_gap",
                "chosen_mathematical_structure",
                "why_structure_closes_gap",
                "applicability_condition",
                "downstream_role",
            ],
        )
        self.assertIn("Model Construction Rationale", self.protocol)
        self.assertIn("Model Construction Rationale", self.model_design)
        self.assertIn("Model Construction & Solution Rationale Review", self.review)

    def test_applicability_is_local_and_not_a_forced_standalone_section(self):
        applicability = self.contract["model_construction_rationale"]["applicability"]
        self.assertIn("局部说明", applicability["principle"])
        self.assertIn("默认不机械新增", applicability["principle"])
        self.assertIn("模型适用性", self.protocol)
        self.assertIn("默认不要求独立“模型适用性分析”小节", self.review)
        for token in (
            "generic_model_is_widely_applicable",
            "generic_model_is_accurate_without_evidence",
        ):
            self.assertIn(token, self.contract["model_construction_rationale"]["anti_boilerplate"])

    def test_reduction_provenance_has_distinct_claim_boundaries(self):
        language = self.contract["model_construction_rationale"]["reduction_language"]
        self.assertEqual(set(language), {"exact", "proven_sufficient", "heuristic"})
        self.assertIn("等价", language["exact"])
        self.assertIn("证明", language["proven_sufficient"])
        self.assertIn("启发式", language["heuristic"])
        self.assertIn("Reduction Provenance", self.protocol)
        self.assertIn("启发式缩域", self.review)

    def test_solver_preconditions_are_explicit_without_algorithm_name_inference(self):
        solver = self.contract["solver_justification"]
        self.assertEqual(
            solver["precondition_chain"],
            [
                "solver_required_property",
                "current_model_evidence_for_property",
                "local_or_global_scope",
                "solver_invocation",
            ],
        )
        self.assertIn("root_or_boundary_search", solver["precondition_profiles"])
        self.assertIn("enumeration", solver["precondition_profiles"])
        self.assertIn("decomposition", solver["precondition_profiles"])
        self.assertIn("solver_precondition_satisfaction_from_algorithm_name_only", solver["machine_audit_scope"]["must_not_claim"])
        self.assertIn("Solver Preconditions", self.protocol)

    def test_numerical_parameter_rationale_is_not_forced_robustness(self):
        evidence = self.contract["numerical_parameter_evidence"]
        for field in (
            "parameter_role",
            "candidate_range_or_source",
            "evidence_metric",
            "selection_rule",
            "final_value",
        ):
            self.assertIn(field, evidence["rationale_fields"])
        self.assertTrue(evidence["no_forced_sensitivity_rule"])
        self.assertIn("03A", evidence["boundary_with_validation"])
        self.assertIn("03B", evidence["boundary_with_validation"])
        self.assertIn("Numerical Parameter Rationale", self.protocol)

    def test_heading_minimality_has_no_hard_character_limit(self):
        headings = self.contract["model_establishment_solution_narrative"]["professional_heading_semantics"]
        self.assertFalse(headings["title_minimality"]["hard_character_limit"])
        self.assertIn("heading_compression_test", headings["title_minimality"])
        self.assertIn("Section Title Minimality", self.protocol)
        self.assertIn("Heading Compression Test", self.cleanup)
        boundary = set(self.contract["machine_audit_boundary"]["must_not_claim"])
        self.assertIn("heading_quality_from_character_count_only", boundary)

    def test_adaptive_separation_protects_both_fragmentation_and_overmerge(self):
        arch = self.contract["model_establishment_solution_narrative"]["within_question_subsection_architecture"]
        adaptive = arch["adaptive_separation"]
        self.assertIn("independent_structural_reduction", adaptive["separate_when_any"])
        self.assertIn("independent_numerical_parameter_evidence", adaptive["separate_when_any"])
        self.assertIn("same_argument_chain", adaptive["keep_continuous_when_all"])
        self.assertIn("subsection_overmerged_despite_independent_tasks", arch["machine_audit_scope"]["may_review"])
        self.assertIn("subsection_fragmented_without_independent_task", arch["machine_audit_scope"]["may_review"])
        self.assertIn("Adaptive Subsection Separation", self.protocol)
        for action in ("Keep", "Compress", "Merge", "Split"):
            self.assertIn(action, self.cleanup)

    def test_author_reasoning_voice_remains_unmodified_in_semantic_shape(self):
        trace = self.contract["prose_style"]["human_reasoning_trace"]
        self.assertEqual(trace["subject_roles"]["quota"], "none")
        self.assertIn("pronoun_frequency_target", trace["prohibit"])
        self.assertIn("authorship_inference_from_voice", trace["prohibit"])
        self.assertEqual(
            trace["claim_strength_alignment"]["rule"],
            "prose_claim_strength_must_not_exceed_evidence_strength",
        )

    def test_examples_are_explicitly_non_template_and_cover_anti_bloat(self):
        for phrase in (
            "不是当前项目事实、算法推荐表或固定句式库",
            "Model Construction Rationale 是重要选择的闭环，不是所有题的扩写器",
            "不设置标题硬字数限制",
            "启发式不能写成",
        ):
            self.assertIn(phrase, self.examples)

    def test_cleanup_and_review_reject_regex_style_scoring(self):
        self.assertIn("不得由“,""因为/因此""", self.cleanup)
        self.assertIn("标题字符数", self.cleanup)
        self.assertIn("不得由“因为/因此”等连接词判断", self.review)
        self.assertIn("不能仅因标题较长", self.review)


class FixedModelConstructionCaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = yaml.safe_load(read(FIXTURE))
        cls.cases = {case["id"]: case for case in data["cases"]}

    def test_fixture_contains_twelve_distinct_cases(self):
        self.assertEqual(len(self.cases), 12)
        self.assertEqual(len(set(self.cases)), 12)

    def test_event_predicate_case_requires_gap_before_solver(self):
        case = self.cases["event_predicate_gap"]
        self.assertTrue(case["facts"]["trajectories_known"])
        self.assertFalse(case["facts"]["event_predicate_known"])
        self.assertTrue(case["expected"]["requires_modeling_gap"])
        self.assertFalse(case["expected"]["solver_before_predicate"])

    def test_boundary_case_has_two_local_brackets_not_one_global_monotone_interval(self):
        case = self.cases["boundary_search_precondition"]
        self.assertEqual(case["facts"]["global_state_pattern"], [0, 1, 0])
        self.assertEqual(len(case["facts"]["local_brackets"]), 2)
        self.assertFalse(case["expected"]["whole_domain_bisection_without_segmentation"])

    def test_proven_and_heuristic_reductions_remain_distinct(self):
        proven = self.cases["proven_reduction"]
        heuristic = self.cases["heuristic_reduction"]
        self.assertEqual(proven["facts"]["provenance"], "proven_sufficient")
        self.assertTrue(proven["facts"]["proof_anchor_exists"])
        self.assertEqual(heuristic["facts"]["provenance"], "heuristic")
        self.assertFalse(heuristic["facts"]["global_certificate"])
        self.assertFalse(heuristic["expected"]["global_optimum_allowed"])

    def test_discretization_case_selects_first_candidate_on_declared_plateau(self):
        case = self.cases["discretization_selection"]
        f = case["facts"]
        selected_index = f["candidates"].index(f["selected"])
        next_change = abs(f["headline_values"][selected_index + 1] - f["headline_values"][selected_index])
        self.assertLess(next_change, f["tolerance"])
        self.assertTrue(case["expected"]["selected_from_plateau"])
        self.assertFalse(case["expected"]["is_real_world_robustness"])

    def test_solver_escalation_has_actual_structural_delta(self):
        case = self.cases["solver_escalation"]
        f = case["facts"]
        self.assertGreater(f["current_dimension"], f["previous_dimension"])
        self.assertTrue(f["new_discrete_assignment"])
        self.assertTrue(f["new_cross_agent_coupling"])
        self.assertTrue(case["expected"]["solver_change_requires_structural_delta"])

    def test_heading_profiles_allow_both_split_and_continuous_forms(self):
        complex_case = self.cases["complex_heading_profile"]
        simple_case = self.cases["simple_heading_profile"]
        self.assertTrue(complex_case["expected"]["short_subheadings_allowed"])
        self.assertFalse(complex_case["expected"]["forced_merge"])
        self.assertTrue(simple_case["expected"]["continuous_model_construction_preferred"])
        self.assertFalse(simple_case["expected"]["fixed_four_subheadings_required"])

    def test_direct_case_preserves_anti_bloat(self):
        case = self.cases["direct_analytic_anti_bloat"]
        self.assertTrue(case["facts"]["direct_relation_sufficient"])
        self.assertFalse(case["facts"]["solver_needed"])
        self.assertFalse(case["expected"]["long_rationale_required"])
        self.assertFalse(case["expected"]["standalone_applicability_section_required"])


if __name__ == "__main__":
    unittest.main()
