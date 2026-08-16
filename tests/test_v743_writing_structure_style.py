from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TestV743WritingStructureStyle(unittest.TestCase):
    def test_latex_authority_locks_cumcm_structure(self):
        latex = (ROOT / "modules/05_writing/latex.md").read_text(encoding="utf-8")
        for token in (
            "问题背景通常 1 个自然段",
            "问题分析中禁止出现数学公式",
            "模型假设”与“符号说明”在正式论文中为两个独立一级章节",
            "不得显示 `H1/H2`、`A1/A2`",
            "核心模型汇总：推导后、求解前必须出现",
            "问题一模型建立及求解",
            "模型的评价与推广",
            "证据驱动的本科生学术表达",
        ):
            self.assertIn(token, latex)
        for token in ("（Source）", "（Derivation）", "（Destination）"):
            self.assertIn(token, latex)
        self.assertIn("可增加第 2 个短段", latex)
        self.assertIn("不能只介绍全文结构和章节安排", latex)

    def test_cleanup_locks_anti_template_and_reasoning_language(self):
        cleanup = (ROOT / "modules/05_writing/ai_cleanup.md").read_text(encoding="utf-8")
        for token in (
            "问题分析禁公式结果",
            "假设与符号拆章",
            "核心模型汇总检查",
            "因果模板检查",
            "主语去重复",
            "科研初学者式学术表达（证据驱动的本科生学术表达）",
            "核心公式 Source 检查",
            "核心公式 Destination 检查",
            "数值参数依据检查",
            "表题必须位于表格正上方",
            "图题位于图片正下方",
        ):
            self.assertIn(token, cleanup)

    def test_cumcm_hsk_template_implements_structure_without_forcing_all_proofs_to_lists(self):
        tex = (ROOT / "templates/latex/cumcm/hsk/hsk_main.tex").read_text(encoding="utf-8")
        self.assertIn("\\section{模型假设}", tex)
        self.assertIn("\\section{符号说明}", tex)
        self.assertNotIn("\\section{模型假设与符号说明}", tex)
        self.assertIn("\\section{问题一模型建立及求解}", tex)
        self.assertIn("\\subsection{核心模型汇总}", tex)
        self.assertIn("\\section{模型的评价与推广}", tex)
        self.assertNotIn("\\section{模型检验}", tex)
        self.assertNotIn("\\section{敏感性与鲁棒性分析}", tex)
        self.assertNotIn("breakable,", tex)
        self.assertIn("短证明默认自然分段", tex)
        self.assertNotIn("% \\begin{enumerate}[label=\\arabic*.,leftmargin=2.2em]", tex)

    def test_proof_pack_preserves_nonbreaking_proof_and_downstream_consequence(self):
        proof = (ROOT / "packs/artifact/proposition_proof.md").read_text(encoding="utf-8")
        self.assertIn("分段优先，分点按需", proof)
        self.assertIn("正文 B 级证明的第一选择是**自然分段 + 必要公式**", proof)
        self.assertIn("只有下列情形适合分点", proof)
        self.assertIn("命题框原则上不可分页", proof)
        self.assertIn("不通过缩小字号硬塞", proof)
        self.assertIn("模型作用与下游计算落点", proof)

    def test_caption_and_docx_checks_lock_table_figure_positions(self):
        caption = (ROOT / "templates/writing/caption_explanation.md").read_text(encoding="utf-8")
        docx = (ROOT / "templates/writing/docx_check.md").read_text(encoding="utf-8")
        self.assertIn("图题必须位于图片正下方", caption)
        self.assertIn("表题必须位于表格正上方", caption)
        self.assertIn("水平、垂直居中", caption)
        self.assertIn("表题是否严格位于表格正上方", docx)
        self.assertIn("图题是否严格位于图片正下方", docx)


if __name__ == "__main__":
    unittest.main()
