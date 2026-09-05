from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "templates/latex/cumcm/hsk/template_manifest.yaml"
QUESTION_PATH = ROOT / "templates/latex/cumcm/hsk/sections/06_question1.tex"
MAIN_PATH = ROOT / "templates/latex/cumcm/hsk/hsk_main.tex"
EVALUATION_PATH = ROOT / "templates/latex/cumcm/hsk/sections/09_evaluation.tex"
AI_STATEMENT_PATH = ROOT / "templates/latex/cumcm/hsk/sections/10_ai_tool_statement.tex"


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
        cls.main = MAIN_PATH.read_text(encoding="utf-8")
        cls.evaluation = EVALUATION_PATH.read_text(encoding="utf-8")
        cls.ai_statement = AI_STATEMENT_PATH.read_text(encoding="utf-8")
        cls.validator = load_validator_module()

    def test_manifest_is_template_authority_not_writing_authority(self):
        self.assertEqual(self.manifest["schema_version"], "1.0.0")
        self.assertEqual(self.manifest["template_id"], "hsk_cumcm_v8")
        owned = set(self.manifest["authority_boundary"]["template_owns"])
        forbidden = set(self.manifest["authority_boundary"]["forbidden_template_authority"])
        self.assertIn("top_level_paper_skeleton", owned)
        self.assertIn("cumcm_question_section_title_pattern", owned)
        self.assertIn("ai_disclosure_slot_placement", owned)
        self.assertIn("choose_model", forbidden)
        self.assertIn("choose_solver", forbidden)
        self.assertIn("force_internal_subsection_names", forbidden)
        self.assertIn("invent_ai_use_fact", forbidden)

    def test_cumcm_question_title_is_locked_but_internal_structure_is_adaptive(self):
        question = self.manifest["cumcm_question_section"]
        self.assertEqual(question["title_pattern"], "问题{N}模型建立及求解")
        self.assertTrue(question["title_locked"])
        self.assertEqual(question["internal_structure"], "adaptive")
        self.assertEqual(question["functional_slots"], ["model", "solve", "result", "validate"])
        self.assertIn(r"\section{问题一模型建立及求解}", self.question)

    def test_a196_inspired_skeleton_keeps_model_preparation_and_local_closure(self):
        skeleton = self.manifest["paper_skeleton"]
        self.assertEqual(skeleton["architecture_reference"], "a196_inspired")
        slots = {slot["id"]: slot for slot in skeleton["ordered_slots"]}
        self.assertIn("model_preparation", slots)
        self.assertFalse(slots["model_preparation"]["required"])
        self.assertIn(r"\input{sections/05_model_preparation}", self.main)
        for heading in ("模型建立", "模型求解", "求解结果", "结果的分析与验证"):
            self.assertIn(rf"\subsection{{{heading}}}", self.question)
        self.assertIn(r"\section{模型的评价与推广}", self.evaluation)
        self.assertFalse(slots["model_preparation"]["default_active"])
        self.assertIn("% \\input{sections/05_model_preparation}", self.main)

    def test_ai_disclosure_is_conditional_truth_bound_slot_before_references(self):
        ordered = self.manifest["paper_skeleton"]["ordered_slots"]
        ids = [slot["id"] for slot in ordered]
        self.assertLess(ids.index("evaluation"), ids.index("ai_disclosure"))
        self.assertLess(ids.index("ai_disclosure"), ids.index("references"))
        slot = next(slot for slot in ordered if slot["id"] == "ai_disclosure")
        self.assertEqual(slot["source"], "sections/10_ai_tool_statement.tex")
        self.assertFalse(slot["required"])
        self.assertFalse(slot["default_active"])
        self.assertIn("verified_current_edition_rule", slot["activation"])
        self.assertIn("confirmed_actual_use_facts", slot["activation"])
        self.assertIn("% \\input{sections/10_ai_tool_statement}", self.main)
        self.assertNotIn("本参赛队在论文撰写、程序开发与结果整理过程中合理使用了 AI", self.ai_statement)
        self.assertIn("不陈述任何具体参赛队的 AI 使用事实", self.ai_statement)

    def test_core_model_summary_is_rendering_mode_not_named_subsection(self):
        rendering = self.manifest["core_model_summary_rendering"]
        self.assertEqual(rendering["rendering_mode"]["values"], ["displayed", "inline", "omitted"])
        self.assertEqual(rendering["modes"], ["displayed", "inline", "omitted"])
        self.assertEqual(rendering["legacy_modes_field"]["canonical_field"], "rendering_mode.values")
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

    def test_reference_exemplars_are_imported_and_present(self):
        canonical = self.manifest["canonical_template"]
        self.assertEqual(canonical["external_reference_status"], "adapted_verified")
        self.assertEqual(canonical["framework_reference_status"], "imported_verified")
        external = ROOT / "templates/latex/cumcm/hsk" / canonical["external_reference_exemplar"]
        framework = ROOT / "templates/latex/cumcm/hsk" / canonical["framework_reference"]
        self.assertTrue(external.is_file())
        self.assertTrue(framework.is_file())
        self.assertNotIn("AI工具使用声明", external.read_text(encoding="utf-8"))
        provenance = self.manifest["reference_provenance"]
        for key in ("source_sha256", "stored_sha256"):
            self.assertRegex(provenance["user_template_source"][key], r"^[0-9a-f]{64}$")
            self.assertRegex(provenance["framework_source"][key], r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
