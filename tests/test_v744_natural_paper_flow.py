from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class NaturalPaperFlowV744Tests(unittest.TestCase):
    def test_writing_contract_delegates_natural_flow_to_authorities(self):
        data = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        policy = data["writing_policy"]
        current = str(yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))["skill_version"])
        self.assertEqual(str(data["version"]), current)
        self.assertEqual(policy["expression_authority"], "modules/05_writing/latex.md")
        self.assertEqual(policy["reasoning_contract"], "core/writing_reasoning_contract.yaml")
        self.assertEqual(policy["core_model_summary_policy"], "adaptive_required_inline_not_applicable")
        self.assertEqual(policy["prose_audit_script"], "scripts/audit_paper_prose.py")
        self.assertEqual(policy["prose_audit_strict_blocks_on"], ["blocking", "review_required"])

        latex = (ROOT / "modules/05_writing/latex.md").read_text(encoding="utf-8")
        for token in (
            "问题重述：问题背景 + 问题提出",
            "问题分析：逐问解释难点与抓手",
            "优先正向叙述",
            "中文国赛默认不设置独立“结论”一级章",
            "核心模型汇总：自适应而非机械必设",
            "每张正文核心图、核心表至少有一次邻近的显式编号引用",
        ):
            self.assertIn(token, latex)

    def test_cumcm_template_uses_problem_statement_and_adaptive_local_results(self):
        text = (ROOT / "templates/latex/cumcm/hsk/hsk_main.tex").read_text(encoding="utf-8")
        self.assertIn("\\subsection{问题背景}", text)
        self.assertIn("\\subsection{问题提出}", text)
        self.assertIn("\\textbf{问题一：}", text)
        self.assertIn("\\textbf{问题二：}", text)
        self.assertNotIn("\\subsection{问题要求}", text)
        self.assertIn("required / inline / not_applicable", text)
        self.assertIn("\\subsection{求解结果}", text)
        self.assertNotIn("\n\\section{结论}\n", text)
        self.assertIn("\\renewcommand{\\theproposition}{\\arabic{section}.\\arabic{proposition}}", text)
        self.assertIn("短证明默认自然分段", text)

    def test_proposition_pack_is_paragraph_first_and_budget_is_recommendation(self):
        text = (ROOT / "packs/artifact/proposition_proof.md").read_text(encoding="utf-8")
        self.assertIn("证明组织：分段优先，分点按需", text)
        self.assertIn("正文 B 级证明优先采用自然分段 + 必要公式", text)
        self.assertIn("适合分点的典型情形", text)
        self.assertIn("3--8 行、2--6 个步骤等均为 Recommendation", text)
        self.assertIn("命题 4.1", text)
        self.assertIn("默认短证明：", text)
        self.assertIn("下游模型/计算作用", text)
        self.assertIn("0--4 是默认正文阅读预算，不是绝对上限", text)

    def test_cleanup_reviews_negation_density_evidence_and_body_references(self):
        text = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        for token in (
            "多次使用“本文不是……而是……”",
            "连续多段无真实冲突的否定/转折",
            "核心图表",
            "显式编号引用",
            "模板段与元话语清理",
            "证明循环论证",
            "引用证据清理",
            "机器审计",
        ):
            self.assertIn(token, text)

    def test_caption_contract_requires_explicit_numbered_reference(self):
        text = (ROOT / "templates/writing/caption_explanation.md").read_text(encoding="utf-8")
        self.assertIn("显式编号引用", text)
        self.assertIn("图~\\ref{...}", text)
        self.assertIn("表~\\ref{...}", text)
        self.assertIn("编号引用", text)
        self.assertIn("模型机制或题目含义", text)
        self.assertIn("这些只是表达方式示例，不是可复制句库", text)

    def test_diangong_active_template_uses_current_adaptive_writing_skeleton(self):
        text = (ROOT / "templates/latex/diangong/main.tex").read_text(encoding="utf-8")
        current = str(yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))["skill_version"])
        self.assertIn(f"v{current}", text)
        self.assertIn("\\subsection{问题提出}", text)
        self.assertIn("\\subsection{求解结果}", text)
        self.assertIn("required / inline / not_applicable", text)
        self.assertNotIn("\\section{模型假设与符号说明}", text)
        self.assertNotIn("\\subsection{问题要求}", text)
        self.assertNotIn("\n\\section{结论}\n", text)
        self.assertNotIn("模板 v6.2.2", text)

    def test_framework_remembers_current_project_writing_choices_without_copying_manual(self):
        text = (ROOT / "templates/model/model_paper_framework.md").read_text(encoding="utf-8")
        for token in (
            "v0.7-project-memory",
            "### 当前写作选择",
            "正文总体结构",
            "共享基础与跨问递进",
            "各问核心模型收束状态",
            "求解、结果、局部验证和深化证据布局",
            "特殊结构例外",
            "### 核心公式 Trace",
            "### Citation Evidence",
            "### 正文章节与交付映射",
        ):
            self.assertIn(token, text)
        self.assertIn("独立结论", text)
        self.assertNotIn("连续推理优先 3--8 行自然分段", text)


if __name__ == "__main__":
    unittest.main()
