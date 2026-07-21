import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_TEXT_DIRS = (
    "core",
    "modules",
    "packs",
    "templates",
    "scripts",
    "skills",
    "state",
    "config",
    "agents",
    ".codex-plugin",
    ".github",
)
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".py", ".m", ".tex", ".bib"}
OBSOLETE_ROOT_ARTIFACTS = (
    "HSK_RUNTIME_ROUTER_V621.md",
    "HSK_SKILL_FILE_INDEX_V621.md",
    "HSK_TEMPLATE_INDEX_V621.md",
    "PROJECT_INSTRUCTIONS_HSK_V621.md",
)


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

    def test_obsolete_v621_runtime_artifacts_are_removed(self):
        for relative in OBSOLETE_ROOT_ARTIFACTS:
            self.assertFalse((ROOT / relative).exists(), relative)

    def test_active_files_do_not_reference_v621(self):
        stale = re.compile(r"\bv6\.2\.1\b|\bV621\b", flags=re.IGNORECASE)
        violations = []
        for directory in ACTIVE_TEXT_DIRS:
            base = ROOT / directory
            if not base.exists():
                continue
            for path in base.rglob("*"):
                if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
                    text = path.read_text(encoding="utf-8-sig", errors="strict")
                    if stale.search(text):
                        violations.append(path.relative_to(ROOT).as_posix())
        self.assertEqual(violations, [])

    def test_gitattributes_forces_lf(self):
        attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn("* text=auto eol=lf", attributes)


if __name__ == "__main__":
    unittest.main()
