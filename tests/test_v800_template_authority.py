from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "templates/latex/cumcm/hsk/template_manifest.yaml"
QUESTION_PATH = ROOT / "templates/latex/cumcm/hsk/sections/06_question1.tex"


def load_validator_module():
    path = ROOT / "scripts/validate_template_manifest.py"
    spec = importlib.util.spec_from_file_location("validate_template_manifest_v800", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestV800TemplateAuthority(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.question = QUESTION_PATH.read_text(encoding="utf-8")
        cls.validator = load_validator_module()

    def test_manifest_is_template_authority_not_writing_authority(self):
        self.assertEqual(self.manifest["schema_version"], "1.0.0")
        self.assertEqual(self.manifest["template_id"], "hsk_cumcm_v8")
        owned = set(self.manifest["authority_boundary"]["template_owns"])
        forbidden = set(self.manifest["authority_boundary"]["forbidden_template_authority"])
        self.assertIn("top_level_paper_skeleton", owned)
        self.assertIn("cumcm_question_section_title_pattern", owned)
        self.assertIn("choose_model", forbidden)
        self.assertIn("choose_solver", forbidden)
        self.assertIn("force_internal_subsection_names", forbidden)

    def test_cumcm_question_title_is_locked_but_internal_structure_is_adaptive(self):
        question = self.manifest["cumcm_question_section"]
        self.assertEqual(question["title_pattern"], "问题{N}模型建立及求解")
        self.assertTrue(question["title_locked"])
        self.assertEqual(question["internal_structure"], "adaptive")
        self.assertEqual(question["functional_slots"], ["model", "solve", "result", "validate"])
        self.assertIn(r"\section{问题一模型建立及求解}", self.question)

    def test_core_model_summary_is_rendering_mode_not_named_subsection(self):
        rendering = self.manifest["core_model_summary_rendering"]
        self.assertEqual(rendering["modes"], ["displayed", "inline", "omitted"])
        self.assertFalse(rendering["independent_named_subsection_default"])
        self.assertTrue(rendering["simple_problem_anti_bloat"])
        self.assertNotIn(r"\subsection{核心模型汇总}", self.question)

    def test_optimization_objective_is_outside_constraint_brace(self):
        objective = self.question.find(r"\min_{\mathbf{x}}")
        constraints = self.question.find(r"\text{s.t.}\quad")
        brace = self.question.find(r"\left\{", constraints)
        self.assertGreaterEqual(objective, 0)
        self.assertGreater(constraints, objective)
        self.assertGreater(brace, constraints)

    def test_template_validator_passes_current_template(self):
        errors = self.validator.validate_template_manifest(MANIFEST_PATH)
        self.assertEqual(errors, [], errors)

    def test_external_reference_is_explicitly_pending_not_invented(self):
        canonical = self.manifest["canonical_template"]
        self.assertIsNone(canonical["external_reference_exemplar"])
        self.assertEqual(canonical["external_reference_status"], "pending_import")


if __name__ == "__main__":
    unittest.main()
