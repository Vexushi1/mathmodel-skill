from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reading_plan_evidence as EVIDENCE


class ApprovedReadingEvidenceChangesTests(unittest.TestCase):
    def pair(self, case="facts_current"):
        artifacts = ["accepted_result_analysis_workbook", "locked_model_spec",
                     "result_analysis_workbook", "validated_results"]
        plan = {
            "version": "9.1.0",
            "assurance": {
                "schema_version": "1.2.0", "status": "pass",
                "context": {"sources": {"question": "explicit_argument"}},
                "dependency_closure": {"contracts": ["core/user_execution_contract.yaml"]},
                "authority_fingerprint": {"sha256": "old", "sources": []},
                "artifact_assurance": {
                    "effective_artifacts": list(artifacts),
                    "evidence": [
                        {"artifact": "locked_model_spec", "status": "verified"},
                        {"artifact": "accepted_solution_workbook", "status": "hash_mismatch", "actual_sha256": "old"},
                        {"artifact": "accepted_result_analysis_workbook", "scope": "Q1", "status": "verified",
                         "reason": "result-analysis execution and stability status are accepted"},
                    ],
                },
            },
            "available_after_modules": [*artifacts, "sync_report"],
            "available_after_plan": [*artifacts, "project_state"],
            "reading_plan": {"metrics": {"planned_skill_read_bytes": 10, "planned_project_read_bytes": 0},
                             "profile": "test", "status": "planned"},
        }
        before = {"id": case, "plan": plan, "legacy_declared_bytes": 20}
        after = deepcopy(before)
        after["plan"]["version"] = "9.5.5"
        after["plan"]["assurance"]["schema_version"] = "1.2.1"
        if case == "facts_hash_drift":
            candidate = after["plan"]
            artifact = candidate["assurance"]["artifact_assurance"]
            artifact["evidence"][2].update(status="not_accepted",
                reason="result-analysis execution or stability status is not accepted")
            for parent, key in ((artifact, "effective_artifacts"), (candidate, "available_after_modules"),
                                (candidate, "available_after_plan")):
                parent[key] = [item for item in parent[key] if item not in {
                    "accepted_result_analysis_workbook", "result_analysis_workbook", "validated_results"}]
        return before, after

    def compare(self, before, after):
        return EVIDENCE.compare([before], [after])[0]

    def test_exact_schema_transition_is_visible_and_not_reported_as_unchanged(self):
        before, after = self.pair()
        saved = deepcopy((before, after))
        row = self.compare(before, after)
        self.assertFalse(row["legacy_behavior_equal"])
        self.assertTrue(row["legacy_behavior_equal_except_approved_changes"])
        self.assertEqual(row["unexpected_legacy_changes"], [])
        self.assertEqual([(item["path"], item["baseline"], item["candidate"])
                          for item in row["expected_legacy_changes"]],
                         [("assurance.schema_version", "1.2.0", "1.2.1")])
        self.assertEqual((before, after), saved)

    def test_hash_drift_registers_only_exact_analysis_revocation(self):
        before, after = self.pair("facts_hash_drift")
        row = self.compare(before, after)
        self.assertFalse(row["legacy_behavior_equal"])
        self.assertTrue(row["legacy_behavior_equal_except_approved_changes"])
        self.assertEqual(row["unexpected_legacy_changes"], [])
        self.assertEqual(len(row["expected_legacy_changes"]), 6)

    def test_unknown_versions_and_real_assurance_behavior_remain_unexpected(self):
        mutations = {
            "unknown_version": lambda p: p["assurance"].update(schema_version="1.2.2"),
            "status": lambda p: p["assurance"].update(status="review_required"),
            "context": lambda p: p["assurance"]["context"]["sources"].update(question="project_state"),
            "new_provenance": lambda p: p["assurance"]["context"].update(field_sources={"question": "project_state"}),
            "dependency": lambda p: p["assurance"]["dependency_closure"].update(contracts=[]),
            "primary_hash": lambda p: p["assurance"]["artifact_assurance"]["evidence"][1].update(actual_sha256="new"),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                before, after = self.pair()
                mutate(after["plan"])
                row = self.compare(before, after)
                self.assertFalse(row["legacy_behavior_equal_except_approved_changes"])
                self.assertIn("assurance", row["unexpected_legacy_changes"])

    def test_unregistered_case_or_diagnostic_does_not_receive_hash_drift_exception(self):
        before, after = self.pair("facts_hash_drift")
        before["id"] = after["id"] = "facts_current"
        self.assertFalse(self.compare(before, after)["legacy_behavior_equal_except_approved_changes"])
        before, after = self.pair("facts_hash_drift")
        after["plan"]["assurance"]["artifact_assurance"]["evidence"][2]["reason"] = "unregistered diagnostic"
        self.assertIn("assurance", self.compare(before, after)["unexpected_legacy_changes"])

    def test_additional_artifact_addition_removal_and_reordering_are_not_hidden(self):
        for mode in ("addition", "removal", "reordering"):
            with self.subTest(mode=mode):
                before, after = self.pair("facts_hash_drift")
                values = after["plan"]["available_after_modules"]
                if mode == "addition":
                    values.append("invented_artifact")
                elif mode == "removal":
                    values.remove("locked_model_spec")
                else:
                    values.reverse()
                row = self.compare(before, after)
                self.assertIn("available_after_modules", row["unexpected_legacy_changes"])

    def test_approval_cannot_be_applied_to_a_different_baseline_or_evidence_identity(self):
        before, after = self.pair()
        before["plan"]["assurance"]["schema_version"] = "1.1.0"
        self.assertIn("assurance", self.compare(before, after)["unexpected_legacy_changes"])
        before, after = self.pair("facts_hash_drift")
        for row in (before, after):
            row["plan"]["assurance"]["artifact_assurance"]["evidence"][2]["scope"] = "Q2"
        self.assertIn("assurance", self.compare(before, after)["unexpected_legacy_changes"])

    def a7_pair(self, case="facts_current"):
        before, after = self.pair(case)
        provenance = {"competition": "explicit", "classification": "project_state"}
        for row in (before, after):
            row["plan"]["assurance"]["context"]["field_provenance"] = deepcopy(provenance)
            row["plan"]["classification"] = {"objective": "optimization", "structures": ["network", "stochastic"]}
        after["plan"]["assurance"]["context"]["field_provenance"].update({
            f"classification.{axis}": "project_state" for axis in ("objective", "structures", "capabilities")
        })
        return before, after

    def test_a7_exact_leaf_additions_are_visible_for_only_the_measured_cases(self):
        cases = ("facts_current", "facts_model_change", "facts_ambiguous", "facts_stale_framework",
                 "facts_hash_drift", "facts_identity_drift", "facts_stale_dependency", "style_current",
                 "style_data_change", "style_figure_drift", "style_no_approval", "mixed")
        for case in cases:
            with self.subTest(case=case):
                before, after = self.a7_pair(case)
                saved = deepcopy((before, after))
                row = self.compare(before, after)
                self.assertFalse(row["legacy_behavior_equal"])
                self.assertTrue(row["legacy_behavior_equal_except_approved_changes"])
                additions = [item for item in row["expected_legacy_changes"] if item["approval"].startswith("A7")]
                self.assertEqual({item["path"] for item in additions}, {
                    f"assurance.context.field_provenance.classification.{axis}"
                    for axis in ("objective", "structures", "capabilities")
                })
                self.assertTrue(all(item["baseline_present"] is False and item["candidate"] == "project_state"
                                    for item in additions))
                self.assertEqual((before, after), saved)

    def test_a7_other_cases_or_additional_provenance_are_still_rejected(self):
        for case in ("facts_unscoped", "new_field", "style_unscoped", "mechanism", "project_sync", "receipt", "cumcm_writing", "future_case"):
            with self.subTest(case=case):
                self.assertIn("assurance", self.compare(*self.a7_pair(case))["unexpected_legacy_changes"])
        before, after = self.a7_pair()
        after["plan"]["assurance"]["context"]["field_provenance"]["classification.extra"] = "project_state"
        self.assertIn("assurance", self.compare(before, after)["unexpected_legacy_changes"])

    def test_a7_changed_sources_and_present_null_are_not_treated_as_exact_additions(self):
        for value in ("explicit", None):
            with self.subTest(value=value):
                before, after = self.a7_pair()
                after["plan"]["assurance"]["context"]["field_provenance"]["classification.objective"] = value
                self.assertIn("assurance", self.compare(before, after)["unexpected_legacy_changes"])
        before, after = self.a7_pair()
        before["plan"]["assurance"]["context"]["field_provenance"]["classification.objective"] = None
        self.assertIn("assurance", self.compare(before, after)["unexpected_legacy_changes"])

    def test_a7_does_not_normalize_classification_values_or_set_order(self):
        for mode in ("objective", "membership", "order"):
            with self.subTest(mode=mode):
                before, after = self.a7_pair()
                classification = after["plan"]["classification"]
                if mode == "objective":
                    classification["objective"] = "prediction"
                elif mode == "membership":
                    classification["structures"].append("dynamic")
                else:
                    classification["structures"].reverse()
                self.assertIn("classification", self.compare(before, after)["unexpected_legacy_changes"])

    def test_a7_approved_provenance_does_not_hide_other_assurance_changes(self):
        for mode in ("status", "dependency"):
            with self.subTest(mode=mode):
                before, after = self.a7_pair()
                if mode == "status":
                    after["plan"]["assurance"]["status"] = "review_required"
                else:
                    after["plan"]["assurance"]["dependency_closure"]["contracts"] = []
                self.assertIn("assurance", self.compare(before, after)["unexpected_legacy_changes"])


if __name__ == "__main__":
    unittest.main()
