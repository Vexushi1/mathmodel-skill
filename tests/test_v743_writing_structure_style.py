from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TestV743WritingStructureStyle(unittest.TestCase):
    def test_latex_authority_locks_current_cumcm_defaults_without_hardening_recommendations(self):
        latex = (ROOT / "modules/05_writing/latex.md").read_text(encoding="utf-8")
        for token in (
            "问题背景用于从题目现实对象收束到本题数学问题，通常一个自然段",
            "正式公式、最终数值、最优方案编号和性能结果默认不放在问题分析中",
            "“模型假设”和“符号说明”默认分开",
            "核心模型汇总：自适应而非机械必设",
            "`required`",
            "`inline`",
            "`not_applicable`",
            "问题一模型建立及求解",
            "模型的评价与推广",
            "Source → Derivation → Destination",
        ):
            self.assertIn(token, latex)
        self.assertIn("段数属于 Recommendation", latex)
        self.assertIn("不是固定模板", latex)

    def test_cleanup_is_anti_template_consumer_not_second_structure_authority(self):
        cleanup = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        self.assertIn("不建立第二套正文写作规则", cleanup)
        self.assertIn("modules/05_writing/latex.md", cleanup)
        self.assertIn("core/writing_reasoning_contract.yaml", cleanup)
        for token in (
            "模板段与元话语清理",
            "把对象名替换成另一赛题后仍完全成立的通用段落",
            "连续展示公式之间几乎没有解释",
            "数值参数直接赋值",
            "逐格复述表格",
            "证明循环论证",
            "引用证据清理",
            "机器审计",
        ):
            self.assertIn(token, cleanup)

    def test_cumcm_hsk_template_implements_adaptive_structure_without_forcing_all_proofs_to_lists(self):
        tex = (ROOT / "templates/latex/cumcm/hsk/hsk_main.tex").read_text(encoding="utf-8")
        self.assertIn("\\section{模型假设}", tex)
        self.assertIn("\\section{符号说明}", tex)
        self.assertNotIn("\\section{模型假设与符号说明}", tex)
        self.assertIn("\\section{问题一模型建立及求解}", tex)
        self.assertIn("required / inline / not_applicable", tex)
        self.assertIn("inline，则把最终一两个计算/判定关系留在模型建立末尾并删除本小节", tex)
        self.assertIn("not_applicable", tex)
        self.assertIn("\\section{模型的评价与推广}", tex)
        self.assertNotIn("breakable,", tex)
        self.assertIn("短证明默认自然分段", tex)
        self.assertNotIn("% \\begin{enumerate}[label=\\arabic*.,leftmargin=2.2em]", tex)

    def test_proof_pack_preserves_paragraph_first_proof_and_downstream_consequence(self):
        proof = (ROOT / "packs/artifact/proposition_proof.md").read_text(encoding="utf-8")
        self.assertIn("证明组织：分段优先，分点按需", proof)
        self.assertIn("正文 B 级证明优先采用自然分段 + 必要公式", proof)
        self.assertIn("适合分点的典型情形", proof)
        self.assertIn("命题框原则上保持同页", proof)
        self.assertIn("模型作用与计算落点", proof)
        self.assertIn("3--8 行、2--6 个步骤等均为 Recommendation", proof)

    def test_caption_and_docx_checks_lock_table_figure_positions(self):
        caption = (ROOT / "templates/writing/caption_explanation.md").read_text(encoding="utf-8")
        docx = (ROOT / "templates/writing/docx_check.md").read_text(encoding="utf-8")
        self.assertIn("图题必须位于图片正下方", caption)
        self.assertIn("表题必须位于表格正上方", caption)
        self.assertIn("水平、垂直居中", caption)
        self.assertIn("表题是否位于表格正上方", docx)
        self.assertIn("图题位于图片正下方", docx)


if __name__ == "__main__":
    unittest.main()
