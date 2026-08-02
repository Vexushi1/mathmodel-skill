from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY_WORKBOOK = "敏感性与鲁棒性结果.xlsx"
CURRENT_WORKBOOK = "结果深化分析.xlsx"


class ActiveResidueCleanupTests(unittest.TestCase):
    def test_current_generation_templates_do_not_emit_legacy_workbook_name(self) -> None:
        active_templates = [
            "templates/matlab/q1_plot.m",
            "templates/matlab/README.md",
            "templates/figure/result_figure_contract.md",
            "templates/figure/figure_paper_closure.md",
            "templates/review/result_manifest.yaml",
            "templates/writing/code_appendix_description.md",
        ]
        for relative in active_templates:
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn(LEGACY_WORKBOOK, text, relative)
            self.assertIn(CURRENT_WORKBOOK, text, relative)

    def test_matlab_starter_uses_current_variable_and_filename(self) -> None:
        text = (ROOT / "templates/matlab/q1_plot.m").read_text(encoding="utf-8")
        self.assertIn("resultAnalysisBook", text)
        self.assertIn('"问题一结果深化分析.xlsx"', text)
        self.assertNotIn("robustnessBook", text)

    def test_result_manifest_uses_current_field_name(self) -> None:
        text = (ROOT / "templates/review/result_manifest.yaml").read_text(encoding="utf-8")
        self.assertIn("result_analysis_workbook:", text)
        self.assertNotIn("sensitivity_robustness_workbook:", text)

    def test_agent_entrypoint_is_latex_first(self) -> None:
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("LaTeX is the default paper and final-PDF path", text)
        self.assertIn("DOCX is an explicit optional review branch", text)
        self.assertIn("问题X结果深化分析.xlsx", text)

    def test_v651_obsolete_templates_are_absent(self) -> None:
        self.assertFalse((ROOT / "templates/review/robustness_check.md").exists())
        self.assertFalse((ROOT / "templates/code/hsk_pipeline/config.yaml").exists())
        self.assertTrue((ROOT / "templates/review/result_analysis_check.md").is_file())
        self.assertTrue((ROOT / "templates/code/full_fidelity_config.yaml").is_file())

    def test_current_starters_stop_at_primary_user_execution_gate(self) -> None:
        for path in (ROOT / "templates/code/starter").glob("*.py"):
            text = path.read_text(encoding="utf-8")
            self.assertIn("run_primary_pipeline(", text, path.name)
            self.assertNotIn("run_pipeline(", text, path.name)
            self.assertNotIn("analyze_results", text, path.name)

    def test_root_and_packaged_skill_versions_match(self) -> None:
        root_skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        packaged_skill = (ROOT / "skills/mathmodel-skill/SKILL.md").read_text(encoding="utf-8")
        pattern = re.compile(r"^version:\s*([^\s]+)", re.MULTILINE)
        root_match = pattern.search(root_skill)
        packaged_match = pattern.search(packaged_skill)
        self.assertIsNotNone(root_match)
        self.assertIsNotNone(packaged_match)
        self.assertEqual(root_match.group(1), packaged_match.group(1))


if __name__ == "__main__":
    unittest.main()
