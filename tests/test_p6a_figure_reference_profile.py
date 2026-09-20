import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class TestP6aFigureReferenceProfile(unittest.TestCase):
    def test_reference_index_is_additive_and_closed_over_existing_assets(self):
        data = yaml.safe_load((ROOT / "assets/figure_assets.yaml").read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], "1.1.0")
        self.assertFalse(data["default_load"])
        self.assertEqual(data["skill_compatibility"], ">=7.4.2,<10.0.0")

        assets = data["assets"]
        index = data["reference_index"]
        self.assertEqual(
            set(index),
            {"evidence_structures", "publication_patterns", "layout_needs"},
        )
        for group in index.values():
            self.assertIsInstance(group, dict)
            self.assertTrue(group)
            for lookup_name, keys in group.items():
                self.assertTrue(keys, lookup_name)
                self.assertEqual(len(keys), len(set(keys)), lookup_name)
                for key in keys:
                    self.assertIn(key, assets, f"{lookup_name}: unknown asset key {key}")

        # P6a indexes the already-vendored visual references; it does not add an
        # external archive or silently turn examples into runtime dependencies.
        for key, meta in assets.items():
            paths = [meta["path"]] if "path" in meta else meta["paths"]
            self.assertIn("use_for", meta, key)
            for relative in paths:
                self.assertTrue(relative.startswith("assets/nature_figure/"), relative)
                self.assertTrue((ROOT / relative).is_file(), relative)

    def test_reference_index_remains_non_authoritative(self):
        asset_text = (ROOT / "assets/figure_assets.yaml").read_text(encoding="utf-8")
        chart_index = (ROOT / "templates/figure/chart_selection.md").read_text(encoding="utf-8")
        module = (ROOT / "modules/04_figure_evidence.md").read_text(encoding="utf-8")
        self.assertIn("不拥有 Figure 决策权", asset_text)
        self.assertIn("assets/figure_assets.yaml", chart_index)
        self.assertIn("单一通用 Authority", module)

    def test_profile_registry_is_pure_configuration(self):
        profile = (ROOT / "templates/matlab/hsk_publication_profile.m").read_text(encoding="utf-8")
        for token in (
            'case "competition_high_contrast"',
            'case "journal_balanced"',
            'case "monochrome_print"',
            "spec.palette = palette",
            "spec.typography.axes_font_size",
            "spec.frame.axes_line_width",
            "palette.deepBlue = palette.brightBlue",
            "palette.darkRed = palette.vividRed",
        ):
            self.assertIn(token, profile)
        code = "\n".join(line.split("%", 1)[0] for line in profile.splitlines()).lower()
        for forbidden in (
            "figure(",
            "gcf",
            "set(",
            "findall(",
            "readtable(",
            "readmatrix(",
            "xlsread(",
            "exportgraphics",
            "saveas(",
        ):
            self.assertNotIn(forbidden, code)

    def test_style_kernel_applies_registry_without_duplicating_profiles(self):
        style = (ROOT / "templates/matlab/hsk_apply_scientific_style.m").read_text(encoding="utf-8")
        self.assertIn("spec = hsk_publication_profile(profile);", style)
        self.assertIn("palette = spec.palette;", style)
        for duplicated in (
            'case "competition_high_contrast"',
            'case "journal_balanced"',
            'case "monochrome_print"',
        ):
            self.assertNotIn(duplicated, style)
        self.assertNotIn("exportgraphics", style)
        self.assertIn('profile (1,1) string = ""', style)
        self.assertIn("if ~isempty(fieldnames(palette))", style)
        self.assertIn("apply_base_style(fig, style, defaults, spec.frame)", style)

    def test_empty_profile_returns_no_palette_before_any_rgb_assignment(self):
        # Source contract only: no MATLAB execution or simulated renderer.
        text = (ROOT / "templates/matlab/hsk_publication_profile.m").read_text(encoding="utf-8")
        self.assertIn('profile (1,1) string = ""', text)
        empty_branch = re.search(r"if strlength\(profile\) == 0\s+(.*?)\nend", text, re.S)
        self.assertIsNotNone(empty_branch)
        self.assertEqual(empty_branch.group(1).strip(), "spec = base_spec(profile, struct());\n    return;")
        self.assertLess(empty_branch.end(), text.index("switch profile"))
        before_switch = text[:text.index("switch profile")]
        self.assertNotRegex(before_switch, r"palette\.\w+\s*=|series\s*=")
        base = text.split("function spec = base_spec(profile, palette)", 1)[1]
        self.assertIn("spec.palette = palette;", base)
        self.assertNotRegex(base, r"(?m)^\s*palette\.\w+\s*=")

    def test_shared_and_standalone_typography_implementations_are_identical(self):
        marker = "function fontName = apply_base_style(fig, overrides, defaults, frame)"
        shared = (ROOT / "templates/matlab/hsk_apply_scientific_style.m").read_text(encoding="utf-8")
        self.assertEqual(shared.count(marker), 1)
        shared_tail = shared[shared.index(marker):]
        for relative in ("templates/matlab/q1_plot.m", "templates/matlab/data_process.m"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertEqual(text.count(marker), 1, relative)
            self.assertEqual(text[text.index(marker):], shared_tail, relative)
        for signature in ("function style = checked_style", "function fontName = select_style_font"):
            self.assertEqual(shared_tail.count(signature), 1)
        self.assertLess(shared_tail.index("checked_style(overrides, defaults)"), shared_tail.index("set(ax,"))
        for token in ("unknown = setdiff(names, fieldnames(style))", "assert(isempty(unknown)",
                      "isfinite(value) && value > 0", 'isgraphics(ruler.Label, "text")',
                      'isa(chart, "matlab.graphics.chart.HeatmapChart")'):
            self.assertIn(token, shared_tail)

    def test_fallback_defaults_equal_the_registry_and_forward_script_overrides(self):
        registry = (ROOT / "templates/matlab/hsk_publication_profile.m").read_text(encoding="utf-8")
        shared = (ROOT / "templates/matlab/hsk_apply_scientific_style.m").read_text(encoding="utf-8")
        fields = {
            "axesFontSize": "typography.axes_font_size",
            "labelFontSize": "typography.label_font_size",
            "legendFontSize": "typography.legend_font_size",
            "colorbarFontSize": "typography.colorbar_font_size",
            "axesLineWidth": "frame.axes_line_width",
            "colorbarLineWidth": "frame.colorbar_line_width",
        }
        for relative in ("templates/matlab/q1_plot.m", "templates/matlab/data_process.m"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            fallback = text.split("function apply_publication_style(fig, style)", 1)[1].split(
                "function fontName = apply_base_style", 1)[0]
            self.assertIn('hsk_apply_scientific_style(fig, "", style);\n    return;', fallback)
            self.assertIn("apply_base_style(fig, style, defaults, frame);", fallback)
            self.assertNotIn("palette", "\n".join(line for line in fallback.splitlines()
                                                    if not line.lstrip().startswith("%")))
            self.assertIn('"fontName", ""', fallback)
            for field, source in fields.items():
                assignment = re.search(r"spec\." + re.escape(source) + r"\s*=\s*([^;]+);", registry)
                self.assertIsNotNone(assignment, source)
                self.assertRegex(fallback, '"' + field + r'",\s*' + re.escape(assignment.group(1).strip()) + r'(?=[,)])')
                self.assertIn(f'"{field}", spec.{source}', shared)
            for field in ("box", "tick_dir", "grid"):
                value = re.search(r"spec\.frame\." + field + r'\s*=\s*("[^"]+");', registry).group(1)
                self.assertIn(f'"{field}", {value}', fallback)

    def test_style_paths_do_not_set_data_or_background_colors(self):
        for relative in ("templates/matlab/hsk_apply_scientific_style.m",
                         "templates/matlab/q1_plot.m", "templates/matlab/data_process.m"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            if relative.endswith(("q1_plot.m", "data_process.m")):
                text = text[text.index("function apply_publication_style(fig, style)"):]
            source = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("%"))
            self.assertNotRegex(source, r'"(?:Color|ColorOrder|FaceColor|EdgeColor|MarkerFaceColor|MarkerEdgeColor)"\s*,')
            self.assertNotRegex(source, r"\b(?:colormap|colororder)\s*\(")
            self.assertNotIn('case "competition_high_contrast"', source)
            self.assertNotIn('profile (1,1) string = "competition_high_contrast"', source)

    def test_formal_project_interface_stays_five_file_and_standalone(self):
        readme = (ROOT / "templates/matlab/README.md").read_text(encoding="utf-8")
        self.assertIn("每问五文件", readme)
        self.assertIn("hsk_publication_profile.m", readme)
        self.assertIn("共享 style helper/profile helper 仍不是必须复制到每问目录的额外产物", readme)
        self.assertIn("不新增第六个必交文件", readme)
        for relative in ("templates/matlab/q1_plot.m", "templates/matlab/data_process.m"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("function apply_publication_style(fig, style)", text)
            self.assertIn("apply_base_style(fig, style, defaults, frame)", text)
            self.assertNotIn("local_publication_palette", text)
            self.assertNotIn("hsk_publication_profile(", text)

    def test_p6a_does_not_claim_real_preview(self):
        evidence = (ROOT / "docs/p6a_figure_reference_profile_split.md").read_text(encoding="utf-8")
        self.assertIn("P6b 才负责真实 rendering/preview 证据", evidence)
        self.assertIn("不能用静态检查冒充", evidence)


if __name__ == "__main__":
    unittest.main()
