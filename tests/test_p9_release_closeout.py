from pathlib import Path
import json
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = "9.7.1"


class P9ReleaseCloseoutTests(unittest.TestCase):
    def test_release_carriers_are_current(self):
        bootstrap = yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8")) or {}
        plugin = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(str(bootstrap["skill_version"]), EXPECTED)
        self.assertEqual(str(plugin["version"]), EXPECTED)
        root_skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        packaged = (ROOT / "skills/mathmodel-skill/SKILL.md").read_text(encoding="utf-8")
        self.assertEqual(root_skill, packaged)
        self.assertIn(f"version: {EXPECTED}", root_skill)
        self.assertIn(f"# HSK 数学建模模块化工作流 v{EXPECTED}", root_skill)
        self.assertTrue((ROOT / "README.md").read_text(encoding="utf-8").startswith(f"# mathmodel-skill v{EXPECTED}"))
        self.assertTrue((ROOT / "core/hsk_core_policy.md").read_text(encoding="utf-8").startswith(f"# HSK Core Policy v{EXPECTED}"))
        for relative in (
            "core/workflow_router.yaml",
            "core/module_manifest.yaml",
            "core/output_contract.yaml",
            "core/writing_runtime_contract.yaml",
            "config/prose_audit_patterns.yaml",
        ):
            data = yaml.safe_load((ROOT / relative).read_text(encoding="utf-8")) or {}
            self.assertEqual(str(data["version"]), EXPECTED, relative)

    def test_legacy_execution_paths_are_read_only_with_major_exit_condition(self):
        contract = yaml.safe_load((ROOT / "core/user_execution_contract.yaml").read_text(encoding="utf-8")) or {}
        delivery = contract["code_delivery"]
        self.assertEqual(delivery["canonical_config_name"], "RUN_CONFIG")
        self.assertEqual(delivery["legacy_config_names"], ["FULL_FIDELITY_CONFIG", "FULL_RUN_CONFIG"])
        window = delivery["compatibility_window"]
        self.assertTrue(window["legacy_full_config_read_only"])
        self.assertTrue(window["p5a_versionless_receipt_read_only"])
        self.assertTrue(window["new_writer_must_use_run_config"])
        self.assertTrue(window["new_writer_receipt_protocol_required"])
        self.assertEqual(window["earliest_removal_skill_major"], 10)
        self.assertIn("explicit_major_migration", window["removal_requires"])
        self.assertTrue(delivery["run_receipt_protocol"]["new_writer_required"])
        self.assertTrue(delivery["run_receipt_protocol"]["p5a_transitional_missing_marker_read_supported"])
        receipt = contract["returned_workbook"]["versioned_receipt"]
        self.assertTrue(receipt["p5a_transitional_missing_version_read_supported"])
        self.assertTrue(receipt["legacy_full_config_missing_version_read_supported"])
        self.assertEqual(receipt["declared_unknown_version_policy"], "fail_closed")

    def test_release_docs_record_current_and_compatibility_decision(self):
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertTrue(changelog.startswith(f"# Changelog\n\n## Current release: {EXPECTED}"))
        self.assertIn("## Previous release: 9.4.1", changelog)
        self.assertIn("## Previous release: 9.4.0", changelog)
        self.assertIn("## Previous release: 9.3.1", changelog)
        self.assertIn("## Previous release: 9.3.0", changelog)
        self.assertIn("## Previous release: 9.2.1", changelog)
        self.assertIn("## Previous release: 9.2.0", changelog)
        record = (ROOT / "docs/p9_release_closeout.md").read_text(encoding="utf-8")
        self.assertIn("最早 v10", record)
        self.assertIn("未知", record)
        self.assertIn("fail closed", record.lower())
        writing_release = (ROOT / "docs/writing_readability_w5_release_closeout.md").read_text(encoding="utf-8")
        self.assertIn("目标版本：** 9.4.0", writing_release)
        self.assertIn("变更等级：** minor", writing_release)
        self.assertIn("无强制用户迁移", writing_release)
        self.assertIn("T01–T18", writing_release)


if __name__ == "__main__":
    unittest.main()
