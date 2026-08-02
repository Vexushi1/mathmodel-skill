from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parent.parent


class LatexFirstVersionlessDocsTests(unittest.TestCase):
    def test_initial_full_workflow_pauses_before_writing(self):
        router = yaml.safe_load(
            (ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8")
        )
        full = router["routing"]["full_workflow"]
        loaded = list(full.get("load", [])) + list(full.get("then", []))
        self.assertNotIn("modules/05_writing/docx.md", loaded)
        self.assertNotIn("packs/artifact/docx.md", loaded)
        self.assertNotIn("modules/05_writing/latex.md", loaded)
        self.assertIn("modules/03_solve_validate.md", loaded)
        self.assertTrue(full["pause_for_user_execution"])
        self.assertEqual(full["delivery_scope"], "code")

    def test_explicit_latex_and_docx_routes_remain_available(self):
        router = yaml.safe_load(
            (ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8")
        )
        latex = router["routing"]["latex"]
        self.assertEqual(latex["delivery_scope"], "latex")
        self.assertIn("modules/05_writing/latex.md", latex["load"])
        docx = router["routing"]["docx"]
        self.assertEqual(docx["delivery_scope"], "docx")
        self.assertIn("modules/05_writing/docx.md", docx["load"])

    def test_manifest_and_output_contract_are_latex_first(self):
        manifest = yaml.safe_load(
            (ROOT / "core/module_manifest.yaml").read_text(encoding="utf-8")
        )
        profile = manifest["workflow_profiles"]["full_workflow"]["modules"]
        self.assertNotIn("writing_docx", profile)
        self.assertNotIn("writing_latex", profile)
        self.assertIn("writing_docx", manifest["modules"])
        self.assertIn("writing_latex", manifest["modules"])
        output = yaml.safe_load(
            (ROOT / "core/output_contract.yaml").read_text(encoding="utf-8")
        )
        policy = output["writing_policy"]
        self.assertEqual(policy["default_mode"], "latex_first")
        self.assertEqual(policy["docx_mode"], "explicit_only_independent")
        self.assertFalse(policy["docx_is_latex_prerequisite"])

    def test_versionless_active_documents_and_legacy_pointers(self):
        pairs = {
            "PROJECT_INSTRUCTIONS_HSK_V622.md": "PROJECT_INSTRUCTIONS.md",
            "HSK_RUNTIME_ROUTER_V622.md": "RUNTIME_ROUTER.md",
            "HSK_SKILL_FILE_INDEX_V622.md": "SKILL_FILE_INDEX.md",
            "HSK_TEMPLATE_INDEX_V622.md": "TEMPLATE_INDEX.md",
        }
        for legacy, active in pairs.items():
            self.assertTrue((ROOT / active).is_file())
            pointer = (ROOT / legacy).read_text(encoding="utf-8")
            self.assertIn(active, pointer)
            self.assertIn("Compatibility Pointer", pointer)

    def test_generator_targets_stable_names(self):
        text = (ROOT / "scripts/generate_indexes.py").read_text(encoding="utf-8")
        self.assertIn('SKILL_INDEX = ROOT / "SKILL_FILE_INDEX.md"', text)
        self.assertIn('TEMPLATE_INDEX = ROOT / "TEMPLATE_INDEX.md"', text)
        self.assertIn(
            'LEGACY_SKILL_INDEX = ROOT / "HSK_SKILL_FILE_INDEX_V622.md"', text
        )
        self.assertIn(
            'LEGACY_TEMPLATE_INDEX = ROOT / "HSK_TEMPLATE_INDEX_V622.md"', text
        )


if __name__ == "__main__":
    unittest.main()
