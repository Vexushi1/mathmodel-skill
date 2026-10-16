"""CUMCM subsection and figure-placement default policy regression (v10.18.3)."""

from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


class CUMCMQuestionWritingStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reasoning = yaml.safe_load(
            (ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8")
        )
        cls.narrative = cls.reasoning["model_establishment_solution_narrative"]
        cls.architecture = cls.narrative["within_question_subsection_architecture"]
        cls.policy = cls.architecture["cumcm_default_second_level"]
        cls.writing = (
            ROOT / "modules/05_writing/paper_writing_protocol.md"
        ).read_text(encoding="utf-8")
        cls.template = yaml.safe_load(
            (ROOT / "templates/latex/cumcm/hsk/template_manifest.yaml").read_text(encoding="utf-8")
        )

    def test_complex_question_default_heading_roles(self):
        self.assertEqual(self.policy["functional_order"], ["model", "solve", "result", "validate"])
        self.assertEqual(self.policy["scope"], "CUMCM_question_sections_with_independent_complex_tasks")
        self.assertEqual(self.policy["governance_level"], "default")
        headings = self.policy["heading_by_role"]
        self.assertEqual(headings["model"], "XX模型的建立")
        self.assertEqual(headings["solve"], "模型求解")
        self.assertEqual(headings["result"], "模型求解结果与分析")
        self.assertEqual(headings["validate_without_comparison"], "模型检验")
        self.assertEqual(headings["validate_with_comparison"], "模型检验与对照")
        for section in ("XX模型的建立", "模型求解", "模型求解结果与分析",
                        "模型检验", "模型检验与对照"):
            self.assertIn(section, self.writing)

    def test_second_level_stays_functional_and_third_level_is_reader_facing(self):
        heading = self.narrative["professional_heading_semantics"]["cumcm_heading_level_precedence"]
        self.assertEqual(heading["readability_primary_target"], "third_level_heading")
        self.assertIn("不因为 Heading Compression", heading["second_level_role"])
        self.assertIn("三级标题", heading["third_level_role"])
        self.assertIn("充分例外", heading["second_level_exception_boundary"])
        self.assertIn("不能因为", self.policy["non_arbitrary_rename_rule"])
        self.assertIn("正常情况保持", self.policy["heading_choice_rule"])
        self.assertIn("模型求解结果与分析", self.policy["normal_title_preservation"])
        self.assertEqual(len(self.policy["documented_exception_categories"]), 4)
        self.assertIn("常规复杂问优先保留", self.writing)
        self.assertIn("二级导航稳定，三级任务可读", self.writing)

    def test_tertiary_titles_reveal_tasks_without_erasing_technical_accuracy(self):
        r = self.architecture["third_level_judge_readability"]
        self.assertEqual(r["reader_assumption"], "mathematical_modeling_literate_not_domain_specialist")
        self.assertEqual(r["priority"], "task_recoverability_before_jargon_display_or_shortest_wording")
        self.assertEqual(r["selection_sequence"][0],
                         "decide_whether_an_independent_mathematical_task_needs_a_third_level_heading")
        self.assertIn("对象", r["judge_readability_question"])
        self.assertIn("KKT", r["necessary_terminology_exception"])
        self.assertIn("不对首选二级", r["title_compression_order"])
        self.assertIn("仅概括", r["accuracy_boundary"])
        self.assertIn("不建立强制替换词表", self.writing)
        self.assertEqual(
            self.reasoning["subsection_granularity"]["cumcm_third_level_readability_authority"],
            "model_establishment_solution_narrative.within_question_subsection_architecture.third_level_judge_readability"
        )

    def test_tertiary_examples_are_conditional_not_fixed_replacement_dictionary(self):
        r = self.architecture["third_level_judge_readability"]
        examples = {e["original"]: e for e in r["examples"]}
        self.assertEqual(examples["FV-BDF-Radau 一致性"]["preferred"], "状态方程求解结果的一致性检验")
        self.assertEqual(examples["Sobol 全局敏感性分解"]["preferred"], "关键参数对最终结果的影响")
        self.assertEqual(examples["数据处理"]["preferred"], "观测时间的统一")
        for case in examples.values():
            self.assertTrue(case["condition"], case)
        self.assertIn("不能拿", self.writing)
        self.assertFalse(self.reasoning["subsection_granularity"]["hard_title_length_limit"])

    def test_no_comparator_does_not_imply_comparison_heading(self):
        self.assertIn("敏感性", self.policy["comparison_naming_rule"])
        self.assertIn("同一数学模型的不同算法", self.policy["comparison_naming_rule"])
        self.assertIn("accepted evidence", self.policy["comparison_naming_rule"])
        self.assertIn("不设置", self.policy["optional_validation_rule"])
        self.assertIn(
            "simple_analytic_or_direct_computation_no_independent_solve",
            self.policy["documented_exception_categories"],
        )
        self.assertIn("不要求使用完全相同字面标题", self.policy["heading_choice_rule"])

    def test_result_subheadings_and_detail_priority_are_adaptive(self):
        self.assertIn(
            "independent_result_task_with_distinct_answer_or_interpretation",
            self.architecture["adaptive_separation"]["separate_when_any"],
        )
        self.assertIn("模型求解结果与分析", self.reasoning["subsection_granularity"]["result_third_level_rule"])
        self.assertFalse(self.reasoning["subsection_granularity"]["hard_count_limit"])
        self.assertFalse(self.reasoning["subsection_granularity"]["hard_title_length_limit"])
        detail = self.narrative["detail_allocation_governance"]
        self.assertIn("核心推导", detail["role_allocation_review"])
        self.assertTrue(detail["simple_problem_anti_bloat"])
        self.assertTrue(detail["no_word_count_rule"])

    def test_figure_location_is_evidence_role_not_chart_type(self):
        f = self.narrative["figure_result_narrative"]["cumcm_evidence_slot_placement"]
        self.assertEqual(set(f["default_by_primary_role"]), {"model", "solve", "result", "validate"})
        self.assertIn("Figure role", f["exception_rule"])
        self.assertIn("同形态参数曲线", f["exception_rule"])
        self.assertIn("03B", f["reuse_existing_evidence"])
        self.assertIn("不触发", f["revision_boundary"])
        self.assertIn("Figure Contract", self.writing)
        self.assertIn("首次证明该判断", self.writing)

    def test_cumcm_template_keeps_example_not_runtime_fixed_titles(self):
        t = self.template["cumcm_question_section"]
        self.assertEqual(t["title_pattern"], "问题{N}模型建立及求解")
        self.assertEqual(t["functional_slots"], ["model", "solve", "result", "validate"])
        self.assertEqual(t["default_complex_question_headings_role"], "maintained_example_profile_only")
        self.assertIn("runtime_required_headings", self.template["fixed_template_checks"]["must_not_infer"])
        self.assertEqual(self.architecture["formal_heading_depth_policy"]["maximum_semantic_level"], 3)

    def test_existing_framework_and_preflight_are_reused(self):
        framework = (
            ROOT / "templates/model/model_paper_framework.md"
        ).read_text(encoding="utf-8")
        runtime = yaml.safe_load(
            (ROOT / "core/writing_runtime_contract.yaml").read_text(encoding="utf-8")
        )
        self.assertIn("各问题章节二级/三级小节规划", framework)
        self.assertIn("论文与图表映射", framework)
        self.assertIn("Figure ID", framework)
        self.assertEqual(
            runtime["per_question_writing_capability_preflight"]["mode"],
            "mandatory_before_each_question_write",
        )
        self.assertEqual(self.reasoning["schema_version"], "1.11.0")


if __name__ == "__main__":
    unittest.main()
