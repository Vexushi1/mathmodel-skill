"""v10.26.2 AI Cleanup permissions and existing-stage regressions.

This suite checks the declared source contract and the existing Runtime/Authority
boundary. It does NOT claim to prove mathematical equivalence of edited papers.
"""
from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class ProseOnlyCleanupContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cleanup = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        cls.runtime = yaml.safe_load(
            (ROOT / "core/writing_runtime_contract.yaml").read_text(encoding="utf-8")
        )
        cls.reasoning = yaml.safe_load(
            (ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8")
        )
        cls.protocol = (ROOT / "modules/05_writing/paper_writing_protocol.md").read_text(encoding="utf-8")

    def test_cleanup_is_a_prose_consumer_not_another_math_editor(self):
        text = self.cleanup
        self.assertLess(len(text.encode("utf-8")), 15000)
        for phrase in (
            "普通自然语言润色消费者",
            "本阶段数学与事实只读",
            "即使认为形式等价，也不得自行改动",
            "不在 Cleanup 越权修复",
            "原文已经自然且准确时 Keep 即可",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
        for unauthorized in (
            "再决定 Keep / Compress / Re-locate / Delete",
            "执行 **Core Derivation Body Closure Test** 后才能 Compress",
            "routine_algebra`：优先压缩或删除",
            "只调整问题章节内部二级/三级标题",
            "过宽表优先拆分真实比较维度",
        ):
            with self.subTest(unauthorized=unauthorized):
                self.assertNotIn(unauthorized, text)

    def test_formula_and_chinese_derivation_remain_exact_in_cleanup_scope(self):
        text = self.cleanup
        for protected in (
            "内联、行间与 LaTeX math 环境",
            "前提→变换→结论",
            "均逐字保留",
            "定义、关键近似、约束来源、初边值、误差",
            "公式来源、推导、命题证明、伪代码及求解细节",
            "中文句子也是受保护推理",
            "即使认为形式等价",
        ):
            with self.subTest(protected=protected):
                self.assertIn(protected, text)
        for role in self.reasoning["formula_reasoning_chain"]["formula_role_taxonomy"]["values"]:
            self.assertIn(role, text)
        # The upstream may omit routine algebra before Cleanup; 05C cannot edit drafted content.
        self.assertEqual(
            self.reasoning["formula_reasoning_chain"]["formula_role_taxonomy"]["roles"]["routine_algebra"]["paper_policy"],
            "compress_or_omit",
        )
        self.assertIn("不能以旧 Formula Role", text)

    def test_proof_solver_algorithm_and_claim_do_not_gain_rewrite_authority(self):
        for protected in (
            "stepwise/pseudocode Algorithm Trace",
            "用户本轮没有再次提到这些能力",
            "只报告给上游",
            "不能以旧 Formula Role",
            "solver precondition",
            "不在 Cleanup 直接修补",
            "数值实验不能成为数学证明",
            "全局最优",
            "不替作者编造理由",
        ):
            with self.subTest(protected=protected):
                self.assertIn(protected, self.cleanup)

    def test_numbers_terms_and_citations_are_all_read_only(self):
        for protected in (
            "包括非关键说明数字",
            "不舍入、不重写、不改变显示格式",
            "不改 accepted 工作簿",
            "Terminology Registry",
            "首次准确解释",
            "Citation Evidence",
            "BibTeX key",
            "绝对/相对误差",
            "百分比/百分点",
        ):
            with self.subTest(protected=protected):
                self.assertIn(protected, self.cleanup)
        # The numeric presentation decision still exists upstream; 05C cannot execute it.
        self.assertEqual(
            self.reasoning["numeric_style_contract"]["ordinary_display_default"]["decimal_places"], 2
        )
        self.assertIn("一般非关键、非评分敏感的说明性连续数值", self.protocol)

    def test_headings_figure_entities_and_latex_labels_are_protected(self):
        for protected in (
            "章标题、小节名称及层级",
            "caption、表头、行列、图例、标签与交叉引用命令均只读",
            "连按其他理由主动拆合标题也没有权限",
            "不要求每张图固定使用相同句数、句序和词语",
            "LaTeX 源码有真实文字变更时",
        ):
            with self.subTest(protected=protected):
                self.assertIn(protected, self.cleanup)
        self.assertIn("Section Title Minimality", self.protocol)

    def test_plain_style_actions_only_touch_separable_non_factual_text(self):
        for protected in (
            "仅编辑普通自然语言的表达层",
            "已被当前结果、图表或引用支持的结果说明",
            "保持对象、数值、范围、条件、比较基准、指标方向、引用范围与 Claim Strength 不变",
            "Keep / Compress / Re-subject / Delete",
            "只操作与受保护内容可明确分离的过渡句、纯冗余句、语序，以及上述已被证据支持的结果叙述",
            "原研究对象、事实、语气、结论强度",
            "无法证明可分离时，不作局部替换",
        ):
            self.assertIn(protected, self.cleanup)

    def test_defensive_wording_examples_preserve_results_and_qualifiers(self):
        protocol_section = self.protocol.split(
            "### 7.3.7 事实来源、团队经历与反模板边界", 1
        )[1].split("## 8.", 1)[0]
        for phrase in (
            "不承载事实的道歉或自我辩解前缀",
            "真实负向结果",
            "题目指定指标",
            "不得把未开展的验证写成已完成",
        ):
            self.assertIn(phrase, protocol_section)

        cleanup_section = self.cleanup.split("### C1. 普通自然语言去模板化", 1)[1].split("### C2.", 1)[0]
        for phrase in (
            "只允许移除包装，不得顺带改写其后的事实",
            "差异方向与数值",
            "不是禁词",
            "真实负面结果",
            "题目要求的指标比较",
            "Keep 并报告",
        ):
            self.assertIn(phrase, cleanup_section)

        fixture = yaml.safe_load(
            (ROOT / "tests/fixtures/defensive_writing_expression_cases.yaml").read_text(encoding="utf-8")
        )
        cases = {case["id"]: case for case in fixture["cases"]}
        self.assertEqual(
            set(cases),
            {
                "apology_wrapper_only",
                "measured_negative_comparison",
                "mathematical_condition",
                "scoped_non_significance",
                "required_metric_comparison",
                "applicability_limit",
                "unperformed_validation",
            },
        )
        for case in cases.values():
            for fragment in case["must_preserve"]:
                self.assertIn(fragment, case["input"])
                self.assertIn(fragment, case["safe_example"])
        for case_id in (
            "mathematical_condition",
            "scoped_non_significance",
            "required_metric_comparison",
            "applicability_limit",
            "unperformed_validation",
        ):
            self.assertEqual(cases[case_id]["safe_example"], cases[case_id]["input"])
        for case_id in ("apology_wrapper_only", "measured_negative_comparison"):
            self.assertEqual(
                cases[case_id]["input"].replace("遗憾的是，", ""),
                cases[case_id]["safe_example"],
            )
        self.assertIn("invent_metrics", fixture["prohibited_operations"])
        self.assertIn("delete_negative_result", fixture["prohibited_operations"])
        self.assertIn("replace_required_metric", fixture["prohibited_operations"])
        self.assertIn("invent_unperformed_validation", fixture["prohibited_operations"])

    def test_existing_runtime_sequence_and_stage_interface_are_preserved(self):
        stages = self.runtime["template_first_progressive_authoring"]["stages"]
        ids = [stage["id"] for stage in stages]
        self.assertEqual(ids.count("ai_cleanup"), 1)
        self.assertLess(ids.index("draft_semantic_review"), ids.index("ai_cleanup"))
        self.assertLess(ids.index("ai_cleanup"), ids.index("latex_assembly_audit_and_compile"))
        self.assertLess(ids.index("latex_assembly_audit_and_compile"), ids.index("final_review_and_delivery"))
        cleanup_stage = next(stage for stage in stages if stage["id"] == "ai_cleanup")
        self.assertEqual(cleanup_stage["write_now"], ["cleaned_paper_text"])
        self.assertEqual(cleanup_stage["read_now"], [
            "modules/05_writing/ai_cleanup.md",
            "modules/05_writing/paper_writing_protocol.md#5-Paragraph-Handoff-Test",
            "modules/05_writing/paper_writing_protocol.md#7.3-作者视角与建模解释",
            "resolved_draft_review_findings",
        ])
        for protected in ("公式、中文推导", "数值及显示格式", "章节标题与层级均只读"):
            self.assertIn(protected, cleanup_stage["gate"])
        self.assertNotIn("run_now", cleanup_stage)

    def test_no_user_checker_or_new_human_approval_is_declared(self):
        for phrase in (
            "不新增项目状态、审批、逐句哈希台账或用户本地 checker",
            "机器审计不得自动重写正文",
            "不据表面自然度升级为 Hard 错误",
        ):
            self.assertIn(phrase, self.cleanup)
        self.assertNotIn("ai_cleanup_checker:", self.cleanup)
        self.assertNotIn("formula_role_taxonomy:", self.cleanup)
        self.assertNotIn("claim_strength_calibration:", self.cleanup)


if __name__ == "__main__":
    unittest.main()
