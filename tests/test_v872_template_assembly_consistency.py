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

    def test_current_ai_disclosure_input_is_declared_but_inactive(self):
        main = (TEMPLATE_ROOT / "hsk_main.tex").read_text(encoding="utf-8")
        active_inputs = VALIDATOR._extract_active_body_inputs(main)
        self.assertNotIn("sections/10_ai_tool_statement.tex", active_inputs)
        self.assertIn("% \\input{sections/10_ai_tool_statement}", main)

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

    def test_declared_conditional_ai_disclosure_can_be_activated(self):
        temp, target = self._copy_template()
        self.addCleanup(temp.cleanup)
        main_path = target / "hsk_main.tex"
        main = main_path.read_text(encoding="utf-8").replace(
            "% \\input{sections/10_ai_tool_statement}",
            r"\input{sections/10_ai_tool_statement}",
        )
        main_path.write_text(main, encoding="utf-8")

        manifest_path = target / "template_manifest.yaml"
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        token = r"\input{sections/10_ai_tool_statement}"
        inactive = manifest["fixed_template_checks"]["optional_default_inactive_tokens"]
        manifest["fixed_template_checks"]["optional_default_inactive_tokens"] = [
            item for item in inactive if item != token
        ]
        manifest_path.write_text(yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False), encoding="utf-8")

        errors = VALIDATOR.validate_template_manifest(manifest_path)
        self.assertEqual([], errors, errors)
        active_inputs = VALIDATOR._extract_active_body_inputs(main)
        self.assertIn("sections/10_ai_tool_statement.tex", active_inputs)

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
