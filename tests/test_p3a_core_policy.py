from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "p3a_global_policy_source_map.yaml"
POLICY = ROOT / "core" / "hsk_core_policy.md"


class GlobalPolicyDedupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapping = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
        cls.policy_text = POLICY.read_text(encoding="utf-8")

    def test_fixture_is_maintenance_mapping_not_new_authority(self):
        self.assertEqual(self.mapping["schema_version"], 1)
        self.assertIn("does not create a new business Authority", self.mapping["purpose"])

    def test_default_policy_is_smaller_than_frozen_p2_baseline(self):
        baseline = int(self.mapping["baseline"]["core_policy_bytes"])
        self.assertLess(len(POLICY.read_bytes()), baseline)

    def test_cross_stage_invariants_remain_explicit(self):
        for marker in self.mapping["retained_global_markers"]:
            with self.subTest(marker=marker):
                self.assertIn(marker, self.policy_text)

    def test_stage_specific_examples_do_not_return_to_default_policy(self):
        for marker in self.mapping["removed_detail_markers"]:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, self.policy_text)

    def test_every_removed_detail_has_a_reachable_active_authority(self):
        seen = set()
        for row in self.mapping["source_mappings"]:
            with self.subTest(mapping=row["id"]):
                self.assertNotIn(row["id"], seen)
                seen.add(row["id"])
                path = ROOT / row["authority"]
                self.assertTrue(path.is_file(), row["authority"])
                self.assertIn(row["marker"], path.read_text(encoding="utf-8"))

    def test_policy_points_to_each_authority_family_after_dedup(self):
        families = {
            "modules/01_problem_audit.md", "modules/02_model_design.md",
            "core/model_approval_contract.yaml", "core/project_state.schema.yaml",
            "core/state_transition_contract.yaml", "core/global_preprocessing_contract.yaml",
            "core/output_contract.yaml", "core/workbook_schema.yaml",
            "core/user_execution_contract.yaml", "core/numerical_verification_contract.yaml",
            "modules/03_solve_validate.md", "modules/03_result_analysis.md",
            "modules/04_figure_evidence.md", "core/writing_reasoning_contract.yaml",
            "modules/05_writing/paper_writing_protocol.md", "core/writing_runtime_contract.yaml",
            "modules/06_review_delivery.md",
        }
        for path in families:
            with self.subTest(authority=path):
                self.assertIn(path, self.policy_text)


if __name__ == "__main__":
    unittest.main()
