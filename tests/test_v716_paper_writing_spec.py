import importlib.util
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


AUDIT = load_module("audit_v716", ROOT / "scripts/audit_paper_prose.py")


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

    def test_prose_audit_reviews_more_than_four_question_subsections_only(self):
        tex = r"""
\begin{document}
\section{问题一模型建立及求解}
\subsection{模型建立}模型。
\subsection{核心模型汇总}汇总。
\subsection{模型求解}求解。
\subsection{结果分析}结果。
\subsection{独立验证}验证。
\end{document}
"""
        findings = AUDIT.audit_text(tex)
        item = next((x for x in findings if x.code == "question_subsection_granularity"), None)
        self.assertIsNotNone(item, findings)
        self.assertEqual(item.severity, "review_required")
        self.assertIn("不代表结构自动错误", item.message)

        compact = r"""
\begin{document}
\section{问题一模型建立及求解}
\subsection{模型建立}变量、目标、约束和核心模型汇总在本节连续说明。
\subsection{模型求解}求解。
\subsection{结果分析}结果。
\subsection{模型检验}检验。
\end{document}
"""
        compact_findings = AUDIT.audit_text(compact)
        self.assertFalse(any(x.code == "question_subsection_granularity" for x in compact_findings), compact_findings)

    def test_core_model_summary_need_not_be_a_named_subsection(self):
        tex = r"""
\begin{document}
\section{问题一模型建立及求解}
\subsection{模型建立}
先定义决策变量，再给出目标函数和约束，最后在同一节末尾汇总最终优化模型。
\subsection{模型求解}采用当前结构匹配的求解器。
\subsection{结果分析}给出关键结果和解释。
\end{document}
"""
        findings = AUDIT.audit_text(tex)
        codes = {x.code for x in findings}
        self.assertNotIn("no_named_core_model_summary", codes)
        self.assertNotIn("missing_solution_result_section", codes)

    def test_framework_pending_objective_and_granularity_require_review(self):
        framework = """
### Q1：测试
- 优化目标摘要闭合：`pending`
- 小节颗粒度：`review_required`
"""
        findings = AUDIT.audit_framework_consistency("\\begin{document}正文\\end{document}", framework)
        codes = {x.code: x.severity for x in findings}
        self.assertEqual(codes["optimization_abstract_objective_pending"], "review_required")
        self.assertEqual(codes["framework_subsection_granularity_pending"], "review_required")

    def test_framework_blocks_explicit_heuristic_global_optimum_scope_conflict(self):
        framework = """
### Q1：测试
- Headline Claim Evidence Level：`HEURISTIC`
- 可入文答案：证明达到全局最优。
"""
        findings = AUDIT.audit_framework_consistency("\\begin{document}正文\\end{document}", framework)
        item = next((x for x in findings if x.code == "heuristic_global_optimum_scope_conflict"), None)
        self.assertIsNotNone(item, findings)
        self.assertEqual(item.severity, "blocking")

    def test_raw_strong_claim_wording_is_warning_not_automatic_semantic_failure(self):
        tex = r"""
\begin{document}
当前方案达到全局最优，并显著提高了目标值。
\end{document}
"""
        findings = AUDIT.audit_text(tex)
        relevant = [x for x in findings if x.code in {"global_optimum_wording", "significance_wording"}]
        self.assertTrue(relevant, findings)
        self.assertTrue(all(x.severity == "warning" for x in relevant), relevant)


if __name__ == "__main__":
    unittest.main()
