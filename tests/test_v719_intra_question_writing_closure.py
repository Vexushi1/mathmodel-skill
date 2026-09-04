import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class TestV719IntraQuestionWritingClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract_path = ROOT / "core/writing_reasoning_contract.yaml"
        cls.contract_text = cls.contract_path.read_text(encoding="utf-8")
        cls.contract = yaml.safe_load(cls.contract_text)
        cls.narrative = cls.contract["model_establishment_solution_narrative"]
        cls.protocol = (ROOT / "modules/05_writing/paper_writing_protocol.md").read_text(encoding="utf-8")
        cls.cleanup = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        cls.project_instructions = (ROOT / "PROJECT_INSTRUCTIONS.md").read_text(encoding="utf-8")
        cls.module02 = (ROOT / "modules/02_model_design.md").read_text(encoding="utf-8")
        cls.taxonomy = (ROOT / "core/task_taxonomy.yaml").read_text(encoding="utf-8")
        cls.numerical = (ROOT / "core/numerical_verification_contract.yaml").read_text(encoding="utf-8")
        cls.approval = (ROOT / "core/model_approval_contract.yaml").read_text(encoding="utf-8")
        cls.workbook = (ROOT / "core/workbook_schema.yaml").read_text(encoding="utf-8")
        cls.project_state = (ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8")
        cls.router = (ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8")

    def test_reasoning_schema_and_single_authority(self):
        self.assertEqual(self.contract["schema_version"], "1.8.0")
        for key in (
            "within_question_subsection_architecture",
            "detail_allocation_governance",
            "figure_result_narrative",
            "question_section_narrative_closure",
        ):
            self.assertIn(key, self.narrative)
            self.assertEqual(self.narrative[key]["governance_level"], "default")
        for relative in (
            "core/main_body_writing_contract.yaml",
            "core/intra_question_writing_contract.yaml",
            "core/figure_narrative_contract.yaml",
            "core/detail_allocation_contract.yaml",
            "modules/intra_question_writing.md",
        ):
            self.assertFalse((ROOT / relative).exists(), relative)

    def test_top_level_paper_skeleton_is_frozen(self):
        architecture = self.narrative["within_question_subsection_architecture"]
        boundary = architecture["scope_boundary"]
        self.assertTrue(boundary["preserves_top_level_paper_skeleton"])
        self.assertFalse(boundary["may_reorder_top_level_sections"])
        self.assertFalse(boundary["may_reorder_question_sections"])
        self.assertIn("符号说明", architecture["top_level_skeleton_rule"])
        self.assertIn("问题一", architecture["top_level_skeleton_rule"])
        self.assertIn("问题二", architecture["top_level_skeleton_rule"])
        self.assertIn("没有权限重排上述一级大章节", self.protocol)
        self.assertIn("不改变问题章节顺序", self.protocol)
        self.assertIn("写作顺序优化也没有权限重排既定一级大章节", self.cleanup)
        self.assertIn("既定论文大章节骨架保持不变", self.project_instructions)

    def test_within_question_order_uses_local_dependency(self):
        architecture = self.narrative["within_question_subsection_architecture"]
        self.assertEqual(
            architecture["ordering_basis"],
            [
                "local_mathematical_dependency",
                "local_solution_reasoning_sequence",
                "model_before_solver",
                "evidence_before_local_conclusion",
            ],
        )
        self.assertIn("solver 不早于", architecture["local_dependency_rule"])
        self.assertIn("数学认知顺序", architecture["python_log_rule"])
        self.assertIn("局部数学依赖与求解认知顺序", self.protocol)
        self.assertIn("程序执行步骤直接变成论文小节", self.cleanup)

    def test_adaptive_separation_protects_navigation_without_reordering(self):
        architecture = self.narrative["within_question_subsection_architecture"]
        adaptive = architecture["adaptive_separation"]
        self.assertIn("independent_structural_reduction", adaptive["separate_when_any"])
        self.assertIn("independent_numerical_parameter_evidence", adaptive["separate_when_any"])
        self.assertIn("same_argument_chain", adaptive["keep_continuous_when_all"])
        self.assertIn("Adaptive Subsection Separation", self.protocol)
        self.assertIn("Split 不能由字数触发，Merge 不能由标题数量触发", self.cleanup)

    def test_data_and_shared_sections_are_internal_only(self):
        architecture = self.narrative["within_question_subsection_architecture"]
        self.assertEqual(
            architecture["data_section_internal_order"],
            [
                "model_required_data_object_or_field",
                "necessary_quality_treatment",
                "necessary_transform_or_constructed_quantity",
                "direct_input_to_downstream_model",
            ],
        )
        self.assertEqual(
            architecture["shared_foundation_internal_order"],
            [
                "shared_object_coordinate_or_index",
                "shared_definition",
                "shared_core_relation",
                "common_output_actually_consumed_by_later_questions",
            ],
        )
        self.assertIn("只是大章节**内部**的组织顺序", self.protocol)

    def test_detail_allocation_is_decisiveness_based(self):
        detail = self.narrative["detail_allocation_governance"]
        for token in (
            "determines_model_structure",
            "determines_predicate_or_boundary",
            "nontrivial_reduction_or_transformation",
            "determines_solver_fit",
            "determines_answer",
            "determines_validation_claim",
        ):
            self.assertIn(token, detail["expand_when_any"])
        for token in (
            "routine_algebra",
            "repeated_symbol_translation",
            "unchanged_inherited_relation",
            "generic_algorithm_background",
            "table_or_curve_repetition",
        ):
            self.assertIn(token, detail["compress_when_any"])
        self.assertTrue(detail["no_word_count_rule"])
        self.assertTrue(detail["simple_problem_anti_bloat"])
        self.assertIn("详写意味着关键信息链完整，不等于字数更长", detail["principle"])
        self.assertIn("简单解析或直接计算问题执行 anti-bloat", self.protocol)
        self.assertIn("不得以字数、句数、公式数", self.cleanup)

    def test_solver_detail_is_problem_specific(self):
        detail = self.narrative["detail_allocation_governance"]["solver_rules"]
        for token in (
            "solver_fit",
            "problem_specific_encoding",
            "objective_evaluation",
            "constraint_handling",
            "key_parameters_initialization_accuracy_termination",
            "output_mapping",
        ):
            self.assertIn(token, detail["expand"])
        for token in (
            "algorithm_history",
            "generic_advantages",
            "unrelated_standard_update_equations",
            "unchanged_standard_operator_detail",
        ):
            self.assertIn(token, detail["compress"])
        self.assertIn("Detail Allocation 在 solver 段同样适用", self.protocol)

    def test_figure_result_narrative_has_adaptive_function_chain(self):
        figure = self.narrative["figure_result_narrative"]
        self.assertEqual(
            figure["functional_sequence"],
            [
                "identify_relation_and_local_role",
                "characterize_decisive_feature",
                "quantify_decisive_value_when_needed",
                "connect_feature_to_current_question",
                "explain_supported_reason_when_available",
                "close_to_answer_or_next_step_when_needed",
            ],
        )
        for token in (
            "not_caption_repetition",
            "not_point_by_point_reading",
            "not_fixed_sentence_count",
            "not_same_pattern_for_every_figure",
            "reason_must_be_supported_by_model_or_evidence",
        ):
            self.assertIn(token, figure["rules"])
        self.assertIn("不得只写“结果如图X所示”", figure["identity_rule"])
        self.assertIn("不为“分析充分”编造机制", figure["cause_rule"])
        self.assertIn("Figure Result Narrative 是信息功能链，不是固定六句话", self.protocol)
        self.assertIn("为什么此时需要这张图", self.cleanup)

    def test_figure_profiles_are_not_curve_only(self):
        profiles = self.narrative["figure_result_narrative"]["adaptive_profiles"]
        self.assertEqual(
            set(profiles),
            {
                "parameter_response_or_sensitivity",
                "optimization_convergence",
                "prediction_or_fit",
                "spatial_or_network",
                "mechanism_or_geometry",
            },
        )
        self.assertIn("多面板图先说明整张图共同回答的问题", self.protocol)
        self.assertIn("空间/网络图", self.cleanup)
        self.assertIn("机理/几何图", self.cleanup)

    def test_question_section_closure_is_local(self):
        closure = self.narrative["question_section_narrative_closure"]
        for token in (
            "local_prerequisite_before_use",
            "model_rationale_recoverable_when_nontrivial",
            "model_semantics_closed_before_solver",
            "solver_preconditions_closed_when_material",
            "solver_output_mapped_to_model_variable_or_answer",
            "decisive_result_has_nearby_interpretation",
            "current_question_directly_answered",
            "no_question_specific_content_moved_across_top_level_question_sections",
        ):
            self.assertIn(token, closure["closure_checks"])
        self.assertIn("没有权限重排全文大章节", closure["principle"])
        self.assertIn("不机械追加“小问结论”", self.protocol)

    def test_new_risks_are_review_only_not_blocking(self):
        audit = self.contract["machine_audit_boundary"]
        new_risks = {
            "subsection_order_breaks_local_dependency",
            "question_subsection_overmerge_risk",
            "question_subsection_fragmentation_risk",
            "top_level_framework_reordered_by_writing_rule",
            "decisive_derivation_overcompressed",
            "routine_content_overexpanded",
            "figure_without_identity_or_local_role",
            "figure_feature_without_question_link",
            "unsupported_figure_cause",
            "detached_figure_summary",
            "local_question_section_not_closed_to_answer",
        }
        self.assertTrue(new_risks <= set(audit["may_review"]))
        self.assertTrue(new_risks.isdisjoint(set(audit["may_block"])))
        self.assertIn("detail_quality_from_word_count_only", audit["must_not_claim"])
        self.assertIn("top_level_reordering_permission_from_local_dependency_only", audit["must_not_claim"])
        self.assertIn("subsection_quality_from_heading_length_only", audit["must_not_claim"])

    def test_no_runtime_or_modeling_gate_schema_expansion(self):
        forbidden_tokens = (
            "within_question_subsection_gate",
            "detail_allocation_gate",
            "figure_result_narrative_gate",
            "requires_intra_question_writing",
        )
        protected = "\n".join(
            [
                self.taxonomy,
                self.numerical,
                self.approval,
                self.workbook,
                self.project_state,
                self.router,
                self.module02,
            ]
        )
        for token in forbidden_tokens:
            self.assertNotIn(token, protected)
        self.assertNotIn("within_question_subsection_architecture:", self.module02)
        self.assertNotIn("detail_allocation_governance:", self.module02)
        self.assertNotIn("figure_result_narrative:", self.module02)
        self.assertIn("Human Model Approval", self.module02)


if __name__ == "__main__":
    unittest.main()
