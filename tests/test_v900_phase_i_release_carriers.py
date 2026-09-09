from pathlib import Path
import json
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = str(yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))["skill_version"])
HISTORICAL_RELEASE = "9.0.0"


class PhaseII4bReleaseCarrierTests(unittest.TestCase):
    def test_all_active_release_carriers_are_v9(self):
        bootstrap = yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8")) or {}
        plugin = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        root_skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        packaged_skill = (ROOT / "skills/mathmodel-skill/SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(str(bootstrap["skill_version"]), EXPECTED)
        self.assertEqual(str(plugin["version"]), EXPECTED)
        self.assertEqual(root_skill, packaged_skill)
        self.assertIn(f"version: {EXPECTED}", root_skill)
        self.assertIn(f"# HSK 数学建模模块化工作流 v{EXPECTED}", root_skill)
        self.assertTrue((ROOT / "README.md").read_text(encoding="utf-8").startswith(f"# mathmodel-skill v{EXPECTED}"))
        self.assertTrue((ROOT / "core/hsk_core_policy.md").read_text(encoding="utf-8").startswith(f"# HSK Core Policy v{EXPECTED}"))
        changelog_lines = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()
        self.assertEqual(changelog_lines[:3], ["# Changelog", "", f"## Current release: {EXPECTED}"])
        for relative in (
            "core/workflow_router.yaml",
            "core/module_manifest.yaml",
            "core/output_contract.yaml",
            "core/writing_runtime_contract.yaml",
            "config/prose_audit_patterns.yaml",
        ):
            data = yaml.safe_load((ROOT / relative).read_text(encoding="utf-8")) or {}
            self.assertEqual(str(data["version"]), EXPECTED, relative)

    def test_historical_v890_phase_i_baselines_are_preserved(self):
        for relative in (
            "docs/v900_migration_contract.md",
            "docs/phase_i_legacy_writer_retirement.md",
            "docs/phase_i_artifact_alias_retirement.md",
            "docs/phase_i_artifact_state_surface_removal.md",
            "docs/phase_i_v9_applicability_renewal.md",
            "tests/fixtures/v900_phase_i_migration_matrix.yaml",
            "tests/fixtures/v900_phase_i_writer_retirement_inventory.yaml",
        ):
            with self.subTest(relative=relative):
                self.assertIn("8.9.0", (ROOT / relative).read_text(encoding="utf-8"))

    def test_i4a_applicability_and_i4b_scope_remain_explicit(self):
        governance = (ROOT / "SKILL_CHANGE_GOVERNANCE.md").read_text(encoding="utf-8")
        record = (ROOT / "docs/phase_i_v9_release_carrier_transition.md").read_text(encoding="utf-8")
        self.assertIn('applies_to_skill: ">=6.3.0,<10.0.0"', governance)
        self.assertIn("runtime_authority: false", record)
        self.assertIn(f"target_skill_version: {HISTORICAL_RELEASE}", record)
        self.assertIn("github_release_or_tag_created: false", record)
        self.assertIn("不创建 GitHub tag 或 GitHub Release", record)
        self.assertIn("Phase I I5", record)


if __name__ == "__main__":
    unittest.main()
