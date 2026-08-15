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

    def test_high_contrast_palette_is_first_class_but_hierarchical(self):
        text = (ROOT / "modules/04_figure_evidence.md").read_text(encoding="utf-8")
        for token in ("中高饱和", "高对比", "#1478FF", "#F04444", "#16B364", "#F79009", "#7A5AF8"):
            self.assertIn(token, text)
        self.assertIn("亮蓝 vs 鲜红", text)
        self.assertIn("辅助对象", text)
        self.assertIn("透明度降权", text)
        self.assertIn("禁止彩虹色", text)
        self.assertNotIn("默认白底、细轴、低饱和深色", text)

    def test_matlab_template_delegates_to_authority(self):
        text = (ROOT / "templates/matlab/README.md").read_text(encoding="utf-8")
        self.assertIn("modules/04_figure_evidence.md", text)
        self.assertIn("动态决定单图、1×2、2×1、1×3、2×2 或拆图", text)
        self.assertIn("高对比", text)
        self.assertNotIn("低饱和、深色", text)

    def test_preprocessing_figure_style_does_not_conflict(self):
        text = (ROOT / "core/global_preprocessing_contract.yaml").read_text(encoding="utf-8")
        self.assertIn("版式动态选择单图/多面板", text)
        self.assertIn("中高饱和高对比色", text)
        self.assertNotIn("白底、低饱和", text)


if __name__ == "__main__":
    unittest.main()
