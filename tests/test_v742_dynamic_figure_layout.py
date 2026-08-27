import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestV742DynamicFigureLayout(unittest.TestCase):
    def test_figure_module_has_dynamic_layout_gate(self):
        text = (ROOT / "modules/04_figure_evidence.md").read_text(encoding="utf-8")
        for token in (
            "Figure Layout Gate",
            "不存在固定默认版式",
            "单图",
            "1×2",
            "2×1",
            "1×3",
            "2×2",
            "Primary question",
            "Evidence level",
            "Split decision",
            "视觉注意力预算",
        ):
            self.assertIn(token, text)
        self.assertIn("任一条件不满足", text)
        self.assertIn("拆成两个 1×2", text)
        self.assertIn("四个 panel 是否同时通过 2×2 六项条件", text)

    def test_layout_is_not_hardcoded_to_one_panel_count(self):
        text = (ROOT / "modules/04_figure_evidence.md").read_text(encoding="utf-8")
        self.assertNotIn("默认采用 2×2", text)
        self.assertNotIn("默认采用1×2", text)
        self.assertNotIn("默认采用 1×2", text)
        self.assertIn("先问：单图能否闭合核心结论", text)
        self.assertIn("按 Primary question / Evidence level 拆成多张 Figure", text)

    def test_high_contrast_palette_is_default_and_semantically_hierarchical(self):
        text = (ROOT / "modules/04_figure_evidence.md").read_text(encoding="utf-8")
        for token in (
            "高对比、中高饱和",
            "#1478FF",
            "#F04444",
            "#16B364",
            "#F79009",
            "#7A5AF8",
            "#252B37",
            "#E9EAEB",
        ):
            self.assertIn(token, text)
        self.assertIn("亮蓝 vs 鲜红", text)
        self.assertIn("辅助对象", text)
        self.assertIn("禁止 rainbow", text)
        self.assertNotIn("主色默认采用**实体、深色、低饱和", text)

    def test_formal_figure_title_is_caption_owned(self):
        module = (ROOT / "modules/04_figure_evidence.md").read_text(encoding="utf-8")
        matlab = (ROOT / "templates/matlab/README.md").read_text(encoding="utf-8")
        q1 = (ROOT / "templates/matlab/q1_plot.m").read_text(encoding="utf-8")
        for text in (module, matlab):
            self.assertIn("caption", text)
            self.assertIn("title", text)
            self.assertIn("sgtitle", text)
        self.assertIn("不设置整体", module)
        self.assertIn("不设置整体", matlab)
        code = "\n".join(line.split("%", 1)[0] for line in q1.splitlines())
        self.assertNotIn("title(", code)
        self.assertNotIn("sgtitle(", code)

    def test_matlab_template_delegates_to_authority(self):
        text = (ROOT / "templates/matlab/README.md").read_text(encoding="utf-8")
        self.assertIn("modules/04_figure_evidence.md", text)
        self.assertIn("动态决定单图、1×2、2×1、1×3、2×2 或拆图", text)
        self.assertIn("Scientific Figure Synthesis Gate", text)
        self.assertIn("高对比、中高饱和", text)
        self.assertIn("Composite Encoding Preference", text)

    def test_preprocessing_figure_style_does_not_conflict(self):
        text = (ROOT / "core/global_preprocessing_contract.yaml").read_text(encoding="utf-8")
        self.assertIn("完全服从modules/04_figure_evidence.md", text)
        self.assertIn("本合同不另定义配色、整体标题或网格规则", text)
        self.assertIn("MATLAB图内不设置整体title/sgtitle", text)


if __name__ == "__main__":
    unittest.main()
