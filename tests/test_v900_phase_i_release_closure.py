from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class PhaseII5ReleaseClosureTests(unittest.TestCase):
    def test_final_migration_contract_and_matrix_close_phase_i(self):
        bootstrap = yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))
        matrix = yaml.safe_load((ROOT / "tests/fixtures/v900_phase_i_migration_matrix.yaml").read_text(encoding="utf-8"))
        contract = (ROOT / "docs/v900_migration_contract.md").read_text(encoding="utf-8")
        self.assertTrue(str(bootstrap["skill_version"]).startswith("9."))
        self.assertEqual(matrix["schema_version"], "1.3.0")
        self.assertEqual(matrix["baseline_skill_version"], "8.9.0")
        self.assertEqual(matrix["current_skill_version"], "9.0.0")
        self.assertEqual(matrix["migration_contract"]["status"], "phase_i_i5_final_v900_release_closure")
        self.assertTrue(all(matrix["phase_i_gates"].values()))
        self.assertIn("status: final_v900_release_contract", contract)
        self.assertIn("phase_i_release_documentation_complete: true", contract)
        self.assertIn("destructive_compatibility_removal_authorized: true", contract)

    def test_i5_record_preserves_initial_v9_historical_reader_boundary(self):
        record = (ROOT / "docs/phase_i_v9_release_closure.md").read_text(encoding="utf-8")
        for token in (
            "runtime_authority: false",
            "phase_i_complete: true",
            "github_release_or_tag_created: false",
            "L0 historical project",
            "explicit Human Approval",
            "v9.0.0 之后的独立兼容性决策",
            "34100869380",
            "34100869385",
        ):
            self.assertIn(token, record)

    def test_current_release_docs_no_longer_describe_i5_as_pending(self):
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        current_release = changelog.split("## Previous release: 8.9.0", 1)[0]
        self.assertIn("Phase I I5 closes", current_release)
        self.assertNotIn("remain Phase I I5 work", current_release)
        self.assertIn("Phase I I5 已完成", readme)
        self.assertNotIn("继续由 Phase I I5 完成", readme)


if __name__ == "__main__":
    unittest.main()
