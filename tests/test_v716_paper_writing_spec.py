import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class TestV716PaperWritingSpec(unittest.TestCase):
    def setUp(self):
        self.contract = yaml.safe_load(
            (ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8")
        )
        self.latex = (ROOT / "modules/05_writing/latex.md").read_text(encoding="utf-8")
        self.cleanup = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        self.framework = (ROOT / "templates/model/model_paper_framework.md").read_text(encoding="utf-8")
        self.optimization = (ROOT / "packs/task/optimization.md").read_text(encoding="utf-8")
        self.review = (ROOT / "modules/06_review_delivery.md").read_text(encoding="utf-8")

    def test_model_solver_validator_are_explicitly_separated(self):
        roles = self.contract["model_solver_validator_roles"]
        self.assertEqual(roles["governance_level"], "default")
        self.assertIn("model", roles["definitions"])
        self.assertIn("solver", roles["definitions"])
        self.assertIn("validator", roles["definitions"])
        self.assertIn("MODEL      = 数学上求什么", self.optimization)
        self.assertIn("solver / validator", self.latex)

    def test_optimization_abstract_requires_objective_semantics(self):
        abstract = self.contract["optimization_model_expression"]["abstract_minimum"]
        self.assertIn("objective_function_meaning", abstract["required_semantics"])
        self.assertIn("优化类摘要如果只列决策变量和算法，却没有说明目标函数含义", self.latex)
        self.assertIn("优化类小问的摘要是否明确“优化什么”", self.framework)

    def test_optimization_paper_order_puts_model_before_solver(self):
        order = self.contract["optimization_model_expression"]["paper_information_order"]
        self.assertLess(order.index("decision_variables"), order.index("solver_and_validation"))
        self.assertLess(order.index("objective_function"), order.index("solver_and_validation"))
        self.assertLess(order.index("constraints_grouped_by_source"), order.index("solver_and_validation"))
        self.assertIn("标准模型类型与现实优化目标", self.latex)
        self.assertIn("核心模型汇总", self.latex)

    def test_model_naming_requires_standard_mathematical_type(self):
        naming = self.contract["model_naming"]
        self.assertEqual(naming["governance_level"], "default")
        self.assertIn("continuous_optimization", naming["standard_type_examples"])
        self.assertIn("mixed_integer_optimization", naming["standard_type_examples"])
        self.assertIn("标准模型类型", self.framework)
        self.assertIn("题目专属名称可以保留", self.latex)

    def test_solver_justification_covers_first_repeated_changed_and_alternative(self):
        rule = self.contract["solver_justification"]
        self.assertIn("first_use_chain", rule)
        self.assertIn("repeated_use_rule", rule)
        self.assertIn("changed_solver_rule", rule)
        self.assertIn("alternative_method_rule", rule)
        self.assertIn("第一次作为主求解器出现", self.latex)
        self.assertIn("后问沿用同一算法", self.latex)
        self.assertIn("更换算法", self.latex)
        self.assertIn("baseline / alternative / validator", self.latex)

    def test_subsection_rule_targets_question_subsections_not_top_level_sections(self):
        granularity = self.contract["subsection_granularity"]
        self.assertEqual(granularity["scope"], "within_question_sections_only")
        self.assertFalse(granularity["hard_count_limit"])
        self.assertIn("不限制全文一级章节数量", self.latex)
        self.assertIn("不限制一级章节数量", self.cleanup)
        self.assertIn("问题章节内部二级小节超过默认 3--4 个", self.review)
        combined = "\n".join([self.latex, self.cleanup, self.review])
        self.assertNotIn("一级章节最多", combined)
        self.assertNotIn("一级章节不得超过", combined)

    def test_claim_strength_levels_and_no_global_optimum_upgrade(self):
        calibration = self.contract["claim_strength_calibration"]
        self.assertEqual(
            set(calibration["evidence_levels"]),
            {"PROVEN", "VERIFIED_NUMERIC", "COMPARATIVE", "OBSERVED", "HEURISTIC"},
        )
        prohibited = "\n".join(calibration["prohibited_upgrades"])
        self.assertIn("global_optimum", prohibited)
        self.assertIn("独立算法未发现更优", self.latex)
        self.assertIn("全局最优", self.cleanup)
        self.assertIn("Headline Claim Evidence Level", self.framework)

    def test_framework_preserves_paper_ready_model_identity(self):
        required_fragments = [
            "标准模型类型",
            "正式模型名称（可含题目专属机制）",
            "主要 Model / Solver / Validator 角色",
            "优化目标摘要闭合",
            "问题章节二级小节计划",
            "Headline Claim Evidence Level",
            "Headline Claim Scope",
        ]
        for fragment in required_fragments:
            self.assertIn(fragment, self.framework)

    def test_cleanup_detects_teacher_feedback_risks_without_becoming_second_authority(self):
        self.assertIn("不建立第二套正文写作规则", self.cleanup)
        self.assertIn("优化类模型先出现 DE、GA、PSO、ALNS、Dual Annealing", self.cleanup)
        self.assertIn("自定义模型名", self.cleanup)
        self.assertIn("一个二级小节只有一个公式、一张表或一幅图", self.cleanup)
        self.assertIn("摘要中用“先进、高效、精确、最优、显著、强鲁棒”", self.cleanup)

    def test_review_keeps_granularity_default_not_blocking(self):
        self.assertIn("本规则只检查**问题章节内部二级小节**", self.review)
        self.assertIn("超过该颗粒度不自动失败", self.review)
        self.assertIn("以下**不再自动列为 Blocking**：问题章节内部二级小节超过默认 3--4 个", self.review)


if __name__ == "__main__":
    unittest.main()
