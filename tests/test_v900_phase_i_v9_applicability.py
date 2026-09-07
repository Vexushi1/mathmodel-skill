from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class PhaseIV9ApplicabilityTests(unittest.TestCase):
    def load(self, relative: str):
        return yaml.safe_load((ROOT / relative).read_text(encoding="utf-8")) or {}

    def test_governance_is_explicitly_renewed_for_v9(self):
        text = (ROOT / "SKILL_CHANGE_GOVERNANCE.md").read_text(encoding="utf-8")
        frontmatter = yaml.safe_load(text.split("---", 2)[1]) or {}
        self.assertEqual(str(frontmatter["governance_version"]), "1.0.3")
        self.assertEqual(str(frontmatter["applies_to_skill"]), ">=6.3.0,<10.0.0")

    def test_active_contract_applicability_covers_v9(self):
        expected = {
            "core/task_taxonomy.yaml": ">=6.3.1,<10.0.0",
            "core/workbook_schema.yaml": ">=6.3.2,<10.0.0",
            "core/global_preprocessing_contract.yaml": ">=7.4.2,<10.0.0",
            "core/user_execution_contract.yaml": ">=7.4.2,<10.0.0",
            "core/code_quality_contract.yaml": ">=7.4.2,<10.0.0",
            "assets/figure_assets.yaml": ">=7.4.2,<10.0.0",
            "core/runtime_assurance_contract.yaml": ">=7.12.0,<10.0.0",
            "core/numerical_verification_contract.yaml": ">=7.14.0,<10.0.0",
        }
        for relative, compatibility in expected.items():
            with self.subTest(relative=relative):
                data = self.load(relative)
                self.assertEqual(str(data["skill_compatibility"]), compatibility)
                self.assertNotIn("<9.0.0", str(data["skill_compatibility"]))

    def test_i4a_does_not_publish_v9_release_carrier(self):
        bootstrap = self.load("core/bootstrap.yaml")
        self.assertEqual(str(bootstrap["skill_version"]), "8.9.0")

    def test_historical_pre_i4_records_are_not_rewritten(self):
        historical = (
            "docs/v801_skill_health_remediation_plan.md",
            "docs/phase_i_compatibility_removal_readiness.md",
            "docs/v900_migration_contract.md",
        )
        for relative in historical:
            with self.subTest(relative=relative):
                self.assertIn("<9.0.0", (ROOT / relative).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
