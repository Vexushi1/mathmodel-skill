import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestV910PublicationRendering(unittest.TestCase):
    def test_v910_release_is_preserved_after_current_release(self):
        bootstrap = (ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("skill_version: 10.6.0", bootstrap)
        self.assertTrue(changelog.startswith("# Changelog\n\n## Unreleased: 10.6.0\n"))
        self.assertIn("## Previous release: 9.7.1", changelog)
        self.assertIn("## Previous release: 9.4.1", changelog)
        self.assertIn("## Previous release: 9.4.0", changelog)
        self.assertIn("## Previous release: 9.3.1", changelog)
        self.assertIn("## Previous release: 9.3.0", changelog)
        self.assertIn("## Previous release: 9.2.1", changelog)
        self.assertIn("## Previous release: 9.2.0", changelog)
        self.assertIn("9.1.0", changelog)

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
        profile = (ROOT / "templates/matlab/hsk_publication_profile.m").read_text(encoding="utf-8")
        style = (ROOT / "templates/matlab/hsk_apply_scientific_style.m").read_text(encoding="utf-8")
        for token in (
            'profile (1,1) string = ""',
            'case "competition_high_contrast"',
            'case "journal_balanced"',
            'case "monochrome_print"',
            "palette.primary",
            "palette.comparison",
            "palette.series",
            "palette.deepBlue = palette.brightBlue",
            "palette.darkRed = palette.vividRed",
        ):
            self.assertIn(token, profile)
        for token in (
            'profile (1,1) string = ""',
            "spec = hsk_publication_profile(profile)",
            "palette = spec.palette",
            '"Box", frame.box',
            '"TickDir", frame.tick_dir',
        ):
            self.assertIn(token, style)
        self.assertNotIn('case "journal_balanced"', style)
        self.assertNotIn("exportgraphics", style)
        self.assertNotIn("exportgraphics", profile)

    def test_entry_templates_prefer_shared_kernel_but_remain_standalone(self):
        for relative in ("templates/matlab/q1_plot.m", "templates/matlab/data_process.m"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn('exist("hsk_apply_scientific_style", "file") == 2', text)
            self.assertIn('hsk_apply_scientific_style(fig, "", style)', text)
            self.assertIn("apply_base_style(fig, style, defaults, frame)", text)
            self.assertIn("seriesColors = zeros(0, 3)", text)
            self.assertNotIn("local_publication_palette", text)
            self.assertNotIn('apply_publication_style(fig, "competition_high_contrast")', text)
            code = "\n".join(line.split("%", 1)[0] for line in text.splitlines())
            self.assertNotIn("title(", code)
            self.assertNotIn("sgtitle(", code)
            self.assertNotIn("exportgraphics", code)
        self.assertIn("每问五文件", (ROOT / "templates/matlab/README.md").read_text(encoding="utf-8"))

    def test_static_entry_rgb_validation_precedes_any_figure_creation(self):
        # These inspect source contracts; they do not run MATLAB or a renderer.
        for relative, required_rows in (("templates/matlab/q1_plot.m", 1),
                                        ("templates/matlab/data_process.m", 2)):
            text = (ROOT / relative).read_text(encoding="utf-8")
            body = text.split("\nfunction ", 1)[0]
            for token in ("seriesColors = zeros(0, 3);", "isnumeric(seriesColors)",
                          "ismatrix(seriesColors)", "size(seriesColors, 2) == 3",
                          f"size(seriesColors, 1) >= {required_rows}", "isreal(seriesColors)",
                          "all(isfinite(seriesColors(:)))",
                          "all(seriesColors(:) >= 0 & seriesColors(:) <= 1)"):
                self.assertIn(token, body, relative)
            self.assertLess(body.index("assert(isnumeric(seriesColors)"), body.index("fig = figure("))
            self.assertNotIn("hsk_publication_profile(", body)
            self.assertNotRegex(body, r"(?m)^\s*(?:colormap|colororder)\s*\(")
            self.assertEqual(len(re.findall(r"(?m)^seriesColors\s*=", body)), 1)

    def test_static_parameter_flow_is_explicit_and_local_overrides_are_last(self):
        for relative in ("templates/matlab/q1_plot.m", "templates/matlab/data_process.m"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            body = text.split("\nfunction ", 1)[0]
            calls = list(re.finditer(r"(?m)^apply_publication_style\(fig, style\);", body))
            self.assertEqual(len(calls), 1, relative)
            call_at = calls[0].start()
            for object_call in ("plot(ax,", "xlabel(ax,", "ylabel(ax,", "legend(ax,"):
                self.assertLess(body.index(object_call), call_at, relative)
            for token in ('"Position", figurePosition', '"LineWidth", lineWidth',
                          '"MarkerIndices", markerIndices', '"MarkerSize", markerSize',
                          '"Location", legendLocation'):
                self.assertIn(token, body, relative)
            for override in ("grid(ax, gridMode)", "ax.Box = axesBox", "xlim(ax, xLimits)", "ylim(ax, yLimits)"):
                self.assertGreater(body.index(override), call_at, relative)
            self.assertRegex(body, r'grid\(ax, gridMode\);\s+if gridMode == "on"\s+ax.Layer = "bottom";')
            self.assertEqual(len(re.findall(r"(?m)^\s*apply_publication_style\s*\(", body)), 1)
            self.assertIn("connectPoints = false;", body)
            self.assertIn('lineStyle = "none";', body)
            for parameter in ("lineWidth", "markerSize", "markerEvery"):
                self.assertIn(f"validateattributes({parameter},", body)

    def test_static_single_series_uses_one_line_object_and_markers_keep_full_data(self):
        q1 = (ROOT / "templates/matlab/q1_plot.m").read_text(encoding="utf-8")
        process = (ROOT / "templates/matlab/data_process.m").read_text(encoding="utf-8")
        for text in (q1, process):
            body = text.split("\nfunction ", 1)[0]
            self.assertEqual(len(re.findall(r"(?m)^\s*plot\(ax,", body)), 1)
            self.assertNotRegex(body, r"(?m)^\s*scatter\s*\(")
            self.assertEqual(body.count('"DisplayName",'), 1)
            self.assertNotIn("x(markerIndices)", body)
            self.assertNotIn("y(markerIndices)", body)
        self.assertIn('plot(ax, x, y, "LineStyle", lineStyle', q1)
        self.assertIn('"Color", seriesColors(1, :), "Marker", markerSymbol', q1)
        self.assertIn("visible_marker_indices(y, markerEvery, lineStyle, markerSymbol)", q1)
        self.assertIn("values = [before, after];", process)
        self.assertIn("visible_marker_indices(values(:, j), markerEvery, lineStyle, markerSymbols(j))", process)
        self.assertIn('plot(ax, x, values(:, j), "LineStyle", lineStyle', process)
        self.assertIn('"Color", seriesColors(j, :), "Marker", markerSymbols(j)', process)

    def test_static_marker_thinning_keeps_isolated_evidence_and_standalone_parity(self):
        marker = "function indices = visible_marker_indices(values, every, lineStyle, marker)"
        bodies = []
        for relative in ("templates/matlab/q1_plot.m", "templates/matlab/data_process.m"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            body = text.split(marker, 1)[1].split("function column = exact_header_column", 1)[0]
            bodies.append(body)
            self.assertIn("indices = 1:numel(values);", body)
            branch = re.search(r'if lineStyle == "none"\s+(.*?)\nend', body, re.S)
            self.assertIsNotNone(branch)
            self.assertIn('assert(marker ~= "none"', branch.group(1))
            self.assertIn("return;", branch.group(1))
            self.assertIn("isolated = finite & ~[false; finite(1:end-1)] & ~[finite(2:end); false];", body)
            self.assertIn('assert(marker ~= "none" || ~any(isolated)', body)
            self.assertIn("indices = unique([1:every:numel(values), find(isolated)']);", body)
        self.assertEqual(bodies[0], bodies[1])

    def test_qa_covers_publication_honesty_and_print_safety(self):
        qa = (ROOT / "templates/figure/result_figure_qa.md").read_text(encoding="utf-8")
        for token in (
            "RGB / colormap",
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
