from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class NaturalPaperFlowV744Tests(unittest.TestCase):
    def test_writing_contract_freezes_natural_flow(self):
        data = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        policy = data["writing_policy"]
        current = str(yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))["skill_version"])
        self.assertEqual(str(data["version"]), current)
        self.assertEqual(policy["problem_restatement_second_section"], "问题提出")
        self.assertTrue(policy["problem_statement_per_question_required"])
        self.assertTrue(policy["problem_statement_method_result_forbidden"])
        self.assertTrue(policy["affirmative_statement_preferred"])
        self.assertTrue(policy["negation_contrast_density_review"])
        self.assertTrue(policy["paragraph_logic_continuity_review"])
        self.assertEqual(policy["proof_structure_default"], "paragraph_first")
        self.assertTrue(policy["proof_logical_units_required"])
        self.assertTrue(policy["proof_numbered_steps_when_needed"])
        self.assertNotIn("proposition_proof_segmented_steps", policy)
        self.assertTrue(policy["figure_table_text_reference_required"])
        self.assertTrue(policy["figure_table_adjacent_explanation_required"])
        self.assertEqual(policy["question_result_section_default"], "求解结果")
        self.assertFalse(policy["standalone_question_conclusion_default"])
        self.assertFalse(policy["standalone_paper_conclusion_default"])
        self.assertEqual(policy["prose_audit_script"], "scripts/audit_paper_prose.py")

    def test_cumcm_template_uses_problem_statement_and_local_results(self):
        text = (ROOT / "templates/latex/cumcm/hsk/hsk_main.tex").read_text(encoding="utf-8")
        self.assertIn("\\subsection{问题背景}", text)
        self.assertIn("\\subsection{问题提出}", text)
        self.assertIn("\\textbf{问题一：}", text)
        self.assertIn("\\textbf{问题二：}", text)
        self.assertNotIn("\\subsection{问题要求}", text)
        self.assertIn("\\subsection{核心模型汇总}", text)
        self.assertIn("\\subsection{求解结果}", text)
        self.assertNotIn("\n\\section{结论}\n", text)
        self.assertIn("\\renewcommand{\\theproposition}{\\arabic{section}.\\arabic{proposition}}", text)
        self.assertIn("短证明默认自然分段", text)

    def test_proposition_pack_is_paragraph_first(self):
        text = (ROOT / "packs/artifact/proposition_proof.md").read_text(encoding="utf-8")
        self.assertIn("分段优先，分点按需", text)
        self.assertIn("3--8 行自然分段", text)
        self.assertIn("明显独立阶段", text)
        self.assertIn("2--6 个编号步骤", text)
        self.assertIn("命题 4.1", text)
        self.assertIn("默认短证明：自然分段", text)
        self.assertIn("下游模型/计算作用", text)

    def test_cleanup_reviews_negation_density_and_body_references(self):
        text = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        for token in (
            "问题提出逐问化",
            "核心图表显式引用",
            "正向叙述优先",
            "否定—转折密度复查",
            "段落逻辑连续性检查",
            "独立结论章检查",
            "证明结构默认自然分段",
            "核心公式 Source 检查",
            "成稿机器审计",
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

    def test_diangong_active_template_no_longer_uses_v6_writing_skeleton(self):
        text = (ROOT / "templates/latex/diangong/main.tex").read_text(encoding="utf-8")
        self.assertIn("v7.4.4", text)
        self.assertIn("\\subsection{问题提出}", text)
        self.assertIn("\\subsection{求解结果}", text)
        self.assertNotIn("\\section{模型假设与符号说明}", text)
        self.assertNotIn("\\subsection{问题要求}", text)
        self.assertNotIn("\n\\section{结论}\n", text)
        self.assertNotIn("模板 v6.2.2", text)

    def test_framework_remembers_new_writing_choices(self):
        text = (ROOT / "templates/model/model_paper_framework.md").read_text(encoding="utf-8")
        for token in (
            "问题重述口径",
            "问题提出",
            "正向叙述策略",
            "求解结果",
            "正文显式引用位置",
            "连续推理优先 3--8 行自然分段",
            "核心公式链索引",
            "跨问模型增量",
        ):
            self.assertIn(token, text)
        self.assertIn("独立“结论”一级章", text)


if __name__ == "__main__":
    unittest.main()
