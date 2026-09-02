from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class TestV803CoreModelSummaryVocabulary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reasoning = yaml.safe_load((ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8"))
        cls.manifest = yaml.safe_load((ROOT / "templates/latex/cumcm/hsk/template_manifest.yaml").read_text(encoding="utf-8"))
        cls.protocol = (ROOT / "modules/05_writing/paper_writing_protocol.md").read_text(encoding="utf-8")

    def test_semantic_and_rendering_modes_are_explicitly_distinct(self):
        summary = self.reasoning["adaptive_core_model_summary"]
        rendering = self.manifest["core_model_summary_rendering"]
        self.assertEqual(summary["semantic_summary_mode"]["field_role"], "mathematical_narrative_need")
        self.assertEqual(summary["semantic_summary_mode"]["values"], ["required", "inline", "not_applicable"])
        self.assertEqual(rendering["rendering_mode"]["field_role"], "cumcm_presentation")
        self.assertEqual(rendering["rendering_mode"]["values"], ["displayed", "inline", "omitted"])

    def test_single_authoritative_mapping_is_preserved_with_read_aliases(self):
        compat = self.reasoning["v8_compatibility"]["adaptive_core_model_summary"]
        expected = {"required": "displayed", "inline": "inline", "not_applicable": "omitted"}
        self.assertEqual(compat["semantic_to_rendering_mode"], expected)
        self.assertEqual(compat["old_to_new_modes"], expected)
        self.assertEqual(compat["legacy_mapping_field"]["canonical_field"], "semantic_to_rendering_mode")
        self.assertEqual(self.manifest["core_model_summary_rendering"]["semantic_mapping_authority"], "core/writing_reasoning_contract.yaml#v8_compatibility.adaptive_core_model_summary.semantic_to_rendering_mode")

    def test_legacy_aliases_remain_readable_until_v9(self):
        summary = self.reasoning["adaptive_core_model_summary"]
        rendering = self.manifest["core_model_summary_rendering"]
        self.assertEqual(summary["modes"], summary["semantic_summary_mode"]["values"])
        self.assertEqual(rendering["modes"], rendering["rendering_mode"]["values"])
        self.assertEqual(str(summary["legacy_modes_field"]["removal_not_before_skill_version"]), "9.0.0")
        self.assertEqual(str(rendering["legacy_modes_field"]["removal_not_before_skill_version"]), "9.0.0")

    def test_protocol_describes_two_layers_without_creating_second_mapping(self):
        self.assertIn("semantic_summary_mode", self.protocol)
        self.assertIn("rendering_mode", self.protocol)
        self.assertIn("唯一映射", self.protocol)
        self.assertNotIn("semantic_to_rendering_mode:", self.protocol)

    def test_rendering_behavior_and_simple_problem_boundary_are_unchanged(self):
        rendering = self.manifest["core_model_summary_rendering"]
        self.assertFalse(rendering["independent_named_subsection_default"])
        self.assertTrue(rendering["simple_problem_anti_bloat"])
        question = (ROOT / "templates/latex/cumcm/hsk/sections/06_question1.tex").read_text(encoding="utf-8")
        self.assertNotIn(r"\subsection{核心模型汇总}", question)


if __name__ == "__main__":
    unittest.main()
