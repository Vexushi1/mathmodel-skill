from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class MechanismTemplateCompatibilityHygieneTests(unittest.TestCase):
    def test_legacy_mechanism_template_paths_are_compatibility_pointers(self):
        placeholder = read("templates/figure/mechanism_placeholder.md")
        per_question = read("templates/figure/per_question_mechanism_plan.md")

        for text in (placeholder, per_question):
            self.assertIn("deprecated compatibility pointer", text)
            self.assertIn("modules/04_figure_evidence.md", text)
            self.assertIn("templates/figure/mechanism_contract.md", text)
            self.assertIn("模型论文框架.md", text)

    def test_old_placeholder_and_duplicate_plan_grammars_do_not_return(self):
        placeholder = read("templates/figure/mechanism_placeholder.md")
        per_question = read("templates/figure/per_question_mechanism_plan.md")

        for forbidden in (
            "SVG / PPT / GeoGebra / Python / 不画",
            "【图 X 占位：图名】",
            "\\fbox{\\parbox",
        ):
            self.assertNotIn(forbidden, placeholder)

        self.assertNotIn("| 小问 | 建模疑问 | 推荐图类型 |", per_question)

    def test_current_runtime_and_figure_pack_do_not_load_compatibility_pointers(self):
        consumers = {
            "core/workflow_router.yaml": read("core/workflow_router.yaml"),
            "packs/artifact/figure.md": read("packs/artifact/figure.md"),
            "SKILL.md": read("SKILL.md"),
            "RUNTIME_ROUTER.md": read("RUNTIME_ROUTER.md"),
        }
        deprecated_paths = (
            "templates/figure/mechanism_placeholder.md",
            "templates/figure/per_question_mechanism_plan.md",
        )
        for relative, text in consumers.items():
            for deprecated in deprecated_paths:
                with self.subTest(relative=relative, deprecated=deprecated):
                    self.assertNotIn(deprecated, text)

    def test_current_practical_check_remains_an_active_substantive_checklist(self):
        practical = read("templates/figure/mechanism_practical_check.md")
        self.assertIn("图前六问", practical)
        self.assertIn("spec_draft → drawio_generated → structure_checked → preview_rendered → visual_reviewed → approved_for_paper", practical)
        self.assertNotIn("deprecated compatibility pointer", practical)


if __name__ == "__main__":
    unittest.main()
