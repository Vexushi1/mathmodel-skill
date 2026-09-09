import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestV910PublicationRendering(unittest.TestCase):
    def test_v910_release_carrier_is_current(self):
        bootstrap = (ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("skill_version: 9.1.0", bootstrap)
        self.assertTrue(changelog.startswith("# Changelog\n\n## Current release: 9.1.0\n"))

    def test_figure_authority_owns_publication_rendering_grammar(self):
        module = (ROOT / "modules/04_figure_evidence.md").read_text(encoding="utf-8")
        for token in (
            "Publication Rendering Grammar",
            "competition_high_contrast",
            "journal_balanced",
            "monochrome_print",
            "Adaptive Canvas",
            "Dedicated Legend Tile",
            "Axis Range / Baseline Honesty",
            "Explicit Export Profile",
        ):
            self.assertIn(token, module)
        self.assertIn("Module 04", (ROOT / "templates/figure/chart_selection.md").read_text(encoding="utf-8"))

    def test_publication_pattern_library_covers_c9_to_c16_and_layouts(self):
        patterns = (ROOT / "templates/figure/figure_enhancement_patterns.md").read_text(encoding="utf-8")
        for token in (
            "C9 Multi-Metric Comparison Strip",
            "C10 Ordered Ablation Ladder",
            "C11 Composition / Decomposition",
            "C12 Evidence Matrix",
            "C13 Milestone-aware Trend",
            "C14 Normalized Multi-Criteria Radar",
            "C15 Density / Manifold / State-Space Evidence",
            "C16 Comparative Performance Matrix",
            "L1 Dedicated Legend Tile",
            "L2 Adaptive Canvas",
            "L3 Open-axis Publication Frame",
        ):
            self.assertIn(token, patterns)

    def test_style_kernel_profiles_and_backward_aliases(self):
        style = (ROOT / "templates/matlab/hsk_apply_scientific_style.m").read_text(encoding="utf-8")
        for token in (
            'profile (1,1) string = "competition_high_contrast"',
            'case "competition_high_contrast"',
            'case "journal_balanced"',
            'case "monochrome_print"',
            "palette.primary",
            "palette.comparison",
            "palette.series",
            '"Box", "off"',
            '"TickDir", "out"',
            '"Box", "off"',
            "palette.deepBlue = palette.brightBlue",
            "palette.darkRed = palette.vividRed",
        ):
            self.assertIn(token, style)
        self.assertNotIn("exportgraphics", style)

    def test_entry_templates_prefer_shared_kernel_but_remain_standalone(self):
        for relative in ("templates/matlab/q1_plot.m", "templates/matlab/data_process.m"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn('exist("hsk_apply_scientific_style", "file") == 2', text)
            self.assertIn('hsk_apply_scientific_style(fig, profile)', text)
            self.assertIn("local_publication_palette", text)
            self.assertIn("palette.primary", text)
            self.assertIn("palette.comparison", text)
            code = "\n".join(line.split("%", 1)[0] for line in text.splitlines())
            self.assertNotIn("title(", code)
            self.assertNotIn("sgtitle(", code)
            self.assertNotIn("exportgraphics", code)
        self.assertIn("每问五文件", (ROOT / "templates/matlab/README.md").read_text(encoding="utf-8"))

    def test_qa_covers_publication_honesty_and_print_safety(self):
        qa = (ROOT / "templates/figure/result_figure_qa.md").read_text(encoding="utf-8")
        for token in (
            "Publication palette profile",
            "legend 是否遮挡核心证据",
            "Adaptive Canvas",
            "bar / stacked bar 的零基线",
            "heatmap / performance matrix",
            "radar 若使用",
            "黑白打印/色觉安全",
        ):
            self.assertIn(token, qa)


if __name__ == "__main__":
    unittest.main()
