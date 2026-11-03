from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = ROOT / "templates/latex/cumcm/hsk"
VALIDATOR_PATH = ROOT / "scripts/validate_template_manifest.py"


def load_validator_module():
    spec = importlib.util.spec_from_file_location("validate_template_manifest_v872", VALIDATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator_module()


class TestV872TemplateAssemblyConsistency(unittest.TestCase):
    def _copy_template(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temp = tempfile.TemporaryDirectory()
        target = Path(temp.name) / "hsk"
        shutil.copytree(TEMPLATE_ROOT, target)
        return temp, target

    def test_current_canonical_manifest_and_main_pass(self):
        errors = VALIDATOR.validate_template_manifest(TEMPLATE_ROOT / "template_manifest.yaml")
        self.assertEqual([], errors, errors)

    def test_current_ai_disclosure_and_appendix_are_active_in_2026(self):
        main = (TEMPLATE_ROOT / "hsk_main.tex").read_text(encoding="utf-8")
        active_inputs = VALIDATOR._extract_active_body_inputs(main)
        self.assertIn("sections/10_ai_tool_statement.tex", active_inputs)
        self.assertIn("appendices/appendices.tex", active_inputs)
        self.assertIn(r"\documentclass[withoutpreface]{cumcmthesis}", main)

    def test_undeclared_active_body_input_fails(self):
        temp, target = self._copy_template()
        self.addCleanup(temp.cleanup)
        main_path = target / "hsk_main.tex"
        main = main_path.read_text(encoding="utf-8")
        main = main.replace(
            r"\printbibliography[title={参考文献}]",
            "\\input{sections/undeclared_active}\n\n\\printbibliography[title={参考文献}]",
        )
        main_path.write_text(main, encoding="utf-8")
        (target / "sections/undeclared_active.tex").write_text("% synthetic\n", encoding="utf-8")
        errors = VALIDATOR.validate_template_manifest(target / "template_manifest.yaml")
        self.assertIn("undeclared active body input: sections/undeclared_active.tex", errors)

    def test_commented_undeclared_input_does_not_count_as_active(self):
        temp, target = self._copy_template()
        self.addCleanup(temp.cleanup)
        main_path = target / "hsk_main.tex"
        main = main_path.read_text(encoding="utf-8")
        main = main.replace(
            r"\printbibliography[title={参考文献}]",
            "% \\input{sections/commented_only}\n\\printbibliography[title={参考文献}]",
        )
        main_path.write_text(main, encoding="utf-8")
        errors = VALIDATOR.validate_template_manifest(target / "template_manifest.yaml")
        self.assertFalse(any("commented_only" in error for error in errors), errors)

    def test_2026_required_ai_disclosure_cannot_be_disabled(self):
        temp, target = self._copy_template()
        self.addCleanup(temp.cleanup)
        path = target / "hsk_main.tex"
        main = path.read_text(encoding="utf-8")
        main = main.replace(
            r"\input{sections/10_ai_tool_statement}",
            r"% \input{sections/10_ai_tool_statement}",
            1,
        )
        path.write_text(main, encoding="utf-8")
        errors = VALIDATOR.validate_template_manifest(target / "template_manifest.yaml")
        self.assertTrue(any("active main template token missing" in x for x in errors), errors)

    def test_appendix_allows_one_child_or_only_no_material_statements(self):
        samples = (
            r"\begin{appendices}" + "\n" + r"\section*{附录}" + "\n"
            + "本论文没有用到程序。本论文没有支撑材料。\n"
            + r"\end{appendices}",
            r"\begin{appendices}" + "\n" + r"\section*{附录}" + "\n"
            + r"\subsection*{附录A}" + "\n"
            + "附录A记录真实源程序。\n" + r"\end{appendices}",
        )
        for sample in samples:
            with self.subTest(sample=sample):
                temp, target = self._copy_template()
                self.addCleanup(temp.cleanup)
                (target / "appendices/appendices.tex").write_text(
                    sample, encoding="utf-8")
                self.assertEqual([], VALIDATOR.validate_template_manifest(
                    target / "template_manifest.yaml"))

    def test_infrastructure_inputs_before_document_are_not_body_slots(self):
        main = (TEMPLATE_ROOT / "hsk_main.tex").read_text(encoding="utf-8")
        active_inputs = VALIDATOR._extract_active_body_inputs(main)
        self.assertNotIn("config/preamble.tex", active_inputs)
        self.assertNotIn("config/commands.tex", active_inputs)
        self.assertNotIn("config/metadata.tex", active_inputs)

    def test_manifest_declared_raw_order_places_ai_slot_before_references(self):
        manifest = yaml.safe_load((TEMPLATE_ROOT / "template_manifest.yaml").read_text(encoding="utf-8"))
        main = (TEMPLATE_ROOT / "hsk_main.tex").read_text(encoding="utf-8")
        positions = VALIDATOR._declared_slot_positions(manifest, TEMPLATE_ROOT, main)
        ordered_sources = [source for _, source in positions]
        self.assertLess(
            ordered_sources.index("sections/09_evaluation.tex"),
            ordered_sources.index("sections/10_ai_tool_statement.tex"),
        )
        self.assertLess(
            ordered_sources.index("sections/10_ai_tool_statement.tex"),
            ordered_sources.index("references.bib"),
        )


if __name__ == "__main__":
    unittest.main()
