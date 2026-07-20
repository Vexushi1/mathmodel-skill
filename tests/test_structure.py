import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestStructure(unittest.TestCase):
    def test_required_dirs(self):
        for relative in [
            "core",
            "modules",
            "packs/task",
            "packs/competition",
            "packs/artifact",
            "templates/code",
            "templates/matlab",
            "templates/latex",
            "scripts",
            "tests",
            "legacy",
            ".github/workflows",
        ]:
            self.assertTrue((ROOT / relative).exists(), relative)

    def test_plugin_wrapper(self):
        self.assertTrue((ROOT / ".codex-plugin/plugin.json").exists())
        self.assertTrue((ROOT / "skills/mathmodel-skill/SKILL.md").exists())

    def test_machine_readable_contracts(self):
        for relative in [
            "core/compile_profiles.yaml",
            "core/output_contract.yaml",
            "core/workbook_schema.yaml",
            "core/project_state.schema.yaml",
        ]:
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_legal_notices(self):
        self.assertTrue((ROOT / "LICENSE").is_file())
        self.assertTrue((ROOT / "THIRD_PARTY_NOTICES.md").is_file())


if __name__ == "__main__":
    unittest.main()
