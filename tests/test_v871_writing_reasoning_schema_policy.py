from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "core" / "writing_reasoning_contract.yaml"
POLICY = ROOT / "docs" / "v871_writing_reasoning_schema_version_policy.md"


class TestV871WritingReasoningSchemaPolicy(unittest.TestCase):
    def test_current_reasoning_schema_family_remains_180(self):
        contract = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual("1.8.0", contract["schema_version"])

    def test_policy_defines_parser_compatibility_not_skill_release_mirroring(self):
        text = POLICY.read_text(encoding="utf-8")
        self.assertIn("machine-consumer compatibility-family version", text)
        self.assertIn("not a mirror of the top-level Skill release", text)
        self.assertIn("removing or renaming an existing machine-readable field", text)
        self.assertIn("adding an optional/additive semantic node", text)
        self.assertIn("intentionally retained", text)

    def test_policy_does_not_permanently_freeze_schema(self):
        text = POLICY.read_text(encoding="utf-8")
        self.assertIn("does **not** freeze the contract forever at 1.8.0", text)
        self.assertIn("parser/migration criteria", text)


if __name__ == "__main__":
    unittest.main()
