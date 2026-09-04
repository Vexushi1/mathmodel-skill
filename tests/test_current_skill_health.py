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

        self.assertEqual(bootstrap.get("skill_version"), "8.4.0")
        self.assertEqual(str(plugin.get("version")), "8.4.0")
        self.assertEqual(root_skill, packaged_skill)
        self.assertIn("version: 8.4.0", root_skill)
        self.assertIn("# HSK 数学建模模块化工作流 v8.4.0", root_skill)
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

        self.assertEqual(str(contract.get("version")), "8.4.0")
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
        self.assertNotIn("主比较允许中高饱和高对比色", text)

    def test_completed_architecture_notes_are_archived(self):
        archived = (
            "authority_duplication_matrix_v7.11.1.md",
            "v7.14_primary_numerical_validity_plan.md",
            "v7.14.1_skill_health_hygiene_plan.md",
            "v7.15_scientific_figure_elevation_plan.md",
            "v7.16_paper_writing_skill_rollback_and_optimization_plan.md",
            "v7.17_mechanism_structural_validity_hardening_plan.md",
            "v7.18_model_establishment_solution_writing_style_hardening_plan.md",
            "v7.19_main_body_architecture_detail_figure_writing_hardening_plan.md",
        )
        for name in archived:
            self.assertTrue((ROOT / "legacy/architecture" / name).is_file(), name)

        for relative in (
            "V7_15_0_SCIENTIFIC_FIGURE_ELEVATION_PLAN.md",
            "docs/paper-writing-skill-rollback-and-optimization-plan.md",
            "docs/mechanism-structural-validity-hardening-plan.md",
            "docs/model-establishment-solution-writing-style-hardening-plan.md",
            "docs/main-body-architecture-detail-figure-writing-hardening-plan.md",
        ):
            self.assertFalse((ROOT / relative).exists(), relative)

        legacy_readme = (ROOT / "legacy/README.md").read_text(encoding="utf-8")
        self.assertIn("architecture/", legacy_readme)
        architecture_readme = (ROOT / "legacy/architecture/README.md").read_text(encoding="utf-8")
        self.assertIn("v7.19_main_body_architecture_detail_figure_writing_hardening_plan.md", architecture_readme)

    def test_v622_compatibility_pointers_are_retained(self):
        for relative in (
            "PROJECT_INSTRUCTIONS_HSK_V622.md",
            "HSK_RUNTIME_ROUTER_V622.md",
            "HSK_SKILL_FILE_INDEX_V622.md",
            "HSK_TEMPLATE_INDEX_V622.md",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_primary_quality_and_result_analysis_boundary_is_unchanged(self):
        primary = (ROOT / "modules/03_solve_validate.md").read_text(encoding="utf-8")
        analysis = (ROOT / "modules/03_result_analysis.md").read_text(encoding="utf-8")

        self.assertIn("Primary Quality Specification", primary)
        self.assertIn("Primary Evidence Capture", primary)
        self.assertIn("主工作簿 accepted", analysis)
        for token in ("参数敏感性", "压力场景", "替代算法"):
            self.assertIn(token, analysis)

    def test_current_health_suite_uses_unversioned_filename(self):
        self.assertTrue((ROOT / "tests/test_current_skill_health.py").is_file())
        self.assertFalse((ROOT / "tests/test_v7141_skill_health.py").exists())


if __name__ == "__main__":
    unittest.main()
