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

    def test_formal_project_interface_stays_five_file_and_standalone(self):
        readme = (ROOT / "templates/matlab/README.md").read_text(encoding="utf-8")
        self.assertIn("每问五文件", readme)
        self.assertIn("hsk_publication_profile.m", readme)
        self.assertIn("不新增“必须复制一个 style helper/profile helper”的第六文件", readme)
        for relative in ("templates/matlab/q1_plot.m", "templates/matlab/data_process.m"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("local_publication_palette", text)
            self.assertNotIn("hsk_publication_profile(", text)

    def test_p6a_does_not_claim_real_preview(self):
        evidence = (ROOT / "docs/p6a_figure_reference_profile_split.md").read_text(encoding="utf-8")
        self.assertIn("P6b 才负责真实 rendering/preview 证据", evidence)
        self.assertIn("不能用静态检查冒充", evidence)


if __name__ == "__main__":
    unittest.main()
