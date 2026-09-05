from pathlib import Path
import re
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class CurrentSkillHealthTests(unittest.TestCase):
    def test_release_carriers_and_skill_entrypoints_match(self):
        bootstrap = yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8")) or {}
        plugin = yaml.safe_load((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8")) or {}
        root_skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        packaged_skill = (ROOT / "skills/mathmodel-skill/SKILL.md").read_text(encoding="utf-8")

        self.assertEqual(bootstrap.get("skill_version"), "8.7.3")
        self.assertEqual(str(plugin.get("version")), "8.7.3")
        self.assertEqual(root_skill, packaged_skill)
        self.assertIn("version: 8.7.3", root_skill)
        self.assertIn("# HSK 数学建模模块化工作流 v8.7.3", root_skill)
        self.assertIn("Template Manifest", root_skill)
        self.assertIn("Paper Writing Protocol", root_skill)
        self.assertIn("Cross-File Chapter Handoff", root_skill)
        self.assertIn("Primary Evidence Capture", root_skill)
        self.assertIn("Scientific Figure Synthesis", root_skill)
        self.assertIn("Model/Solver/Validator", root_skill)
        self.assertIn("Claim Strength Calibration", root_skill)
        self.assertIn("within-question local dependency architecture", root_skill)
        self.assertIn("decisiveness-based detail allocation", root_skill)
        self.assertIn("adaptive figure-result narrative", root_skill)
        self.assertIn("Final Review Compliance & Evidence Sweep", root_skill)
        self.assertIn("Editable Mechanism Diagram", root_skill)

    def test_active_skill_authority_targets_exist(self):
        root_skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        authority = root_skill.split("## Authority 导航", 1)[1].split("\n## ", 1)[0]
        targets = re.findall(
            r"`((?:core|modules|templates|scripts|config|packs)/[^`]+)`",
            authority,
        )

        self.assertIn("templates/model/model_paper_framework.md", targets)
        self.assertNotIn("core/project_memory_contract.yaml", targets)
        self.assertTrue(targets)
        for relative in targets:
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_output_contract_preserves_caption_owned_titles_and_adds_scientific_synthesis(self):
        contract = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8")) or {}
        figure = contract.get("matlab_figure_contract", {})
        writing = contract.get("writing_policy", {})

        self.assertEqual(str(contract.get("version")), "8.7.3")
        self.assertFalse(figure.get("title_required"))
        self.assertTrue(figure.get("embedded_overall_title_forbidden"))
        self.assertEqual(figure.get("formal_title_owner"), "DOCX_or_LaTeX_caption")
        self.assertEqual(figure.get("single_panel_title"), "none")
        self.assertEqual(figure.get("multi_panel_title"), "panel_labels_only")
        self.assertFalse(figure.get("keep_title_in_export_by_default"))
        self.assertEqual(
            figure.get("preprocessing_source_workbook"),
            "数据预处理/数据预处理结果.xlsx",
        )
        self.assertTrue(figure.get("scientific_synthesis_required_for_core_figures"))
        self.assertTrue(figure.get("basic_form_challenge_required_for_core_figures"))
        self.assertTrue(figure.get("portfolio_scientific_quality_review_required"))
        self.assertTrue(figure.get("high_contrast_primary_palette_required"))
        self.assertEqual(
            writing.get("optimization_expression_contract"),
            "core/writing_reasoning_contract.yaml#optimization_model_expression",
        )
        self.assertEqual(
            writing.get("claim_strength_contract"),
            "core/writing_reasoning_contract.yaml#claim_strength_calibration",
        )
        self.assertEqual(
            writing.get("model_solution_narrative_contract"),
            "core/writing_reasoning_contract.yaml#model_establishment_solution_narrative",
        )

    def test_preprocessing_contract_delegates_figure_style(self):
        text = (ROOT / "core/global_preprocessing_contract.yaml").read_text(encoding="utf-8")
        self.assertIn("完全服从modules/04_figure_evidence.md", text)
        self.assertIn("MATLAB图内不设置整体title/sgtitle", text)


if __name__ == "__main__":
    unittest.main()
