from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
ROOT_SKILL = ROOT / "SKILL.md"
PACKAGED_SKILL = ROOT / "skills/mathmodel-skill/SKILL.md"
START = "<!-- HSK_RUNTIME_ENTRY_CONTRACT_START -->"
END = "<!-- HSK_RUNTIME_ENTRY_CONTRACT_END -->"


def extract_contract(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if text.count(START) != 1 or text.count(END) != 1:
        raise AssertionError(f"runtime contract markers invalid: {path}")
    return text.split(START, 1)[1].split(END, 1)[0].strip()


def frontmatter_version(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^version:\s*([^\s]+)", text, flags=re.MULTILINE)
    if not match:
        raise AssertionError(f"frontmatter version missing: {path}")
    return match.group(1)


class EntrypointParityTests(unittest.TestCase):
    def test_root_and_packaged_runtime_contracts_are_identical(self):
        self.assertEqual(extract_contract(ROOT_SKILL), extract_contract(PACKAGED_SKILL))

    def test_runtime_contract_delegates_to_single_authority_chain(self):
        block = extract_contract(ROOT_SKILL)
        for token in (
            "core/bootstrap.yaml", "core/workflow_router.yaml", "core/hsk_core_policy.md",
            "scripts/resolve_workflow.py", "core/writing_reasoning_contract.yaml",
            "模型论文框架.md", "legacy/",
        ):
            self.assertIn(token, block)
        for stale in (
            "HSK_RUNTIME_ROUTER_V622.md", "HSK_SKILL_FILE_INDEX_V622.md",
            "HSK_TEMPLATE_INDEX_V622.md", "PROJECT_INSTRUCTIONS_HSK_V622.md",
        ):
            self.assertNotIn(stale, block)
        self.assertIn("不作为模型、预处理、求解、绘图或写作规则的独立权威", block)

    def test_all_release_carriers_follow_bootstrap(self):
        current = str(yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))["skill_version"])
        plugin = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(frontmatter_version(ROOT_SKILL), current)
        self.assertEqual(frontmatter_version(PACKAGED_SKILL), current)
        self.assertEqual(str(plugin["version"]), current)
        self.assertEqual(plugin["skills"], "./skills/")
        self.assertTrue((ROOT / "README.md").read_text(encoding="utf-8").startswith(f"# mathmodel-skill v{current}"))
        self.assertTrue((ROOT / "core/hsk_core_policy.md").read_text(encoding="utf-8").startswith(f"# HSK Core Policy v{current}"))
        for relative in ("core/workflow_router.yaml", "core/module_manifest.yaml", "core/output_contract.yaml"):
            data = yaml.safe_load((ROOT / relative).read_text(encoding="utf-8"))
            self.assertEqual(str(data["version"]), current, relative)

    def test_current_changelog_matches_bootstrap(self):
        current = str(yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))["skill_version"])
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn(f"## Current release: {current}", changelog)
        self.assertIn("## Previous release: 7.6.0", changelog)

    def test_stable_docs_and_resolver_do_not_create_extra_release_carriers(self):
        self.assertEqual((ROOT / "scripts/README.md").read_text(encoding="utf-8").splitlines()[0], "# Scripts")
        legacy = (ROOT / "legacy/README.md").read_text(encoding="utf-8")
        self.assertIn("不属于当前默认运行链路", legacy)
        resolver = (ROOT / "scripts/resolve_workflow.py").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"HSK v\d+\.\d+\.\d+ execution plan", resolver))

    def test_one_shot_v752_migration_files_are_absent(self):
        paths = (
            "scripts/_v752_entrypoint_parity_migration.py",
            ".github/workflows/v752-entrypoint-parity-migration.yml",
        )
        manifest = (ROOT / "MANIFEST.sha256").read_text(encoding="utf-8")
        for relative in paths:
            self.assertFalse((ROOT / relative).exists(), relative)
            self.assertNotIn(relative, manifest)


if __name__ == "__main__":
    unittest.main()
