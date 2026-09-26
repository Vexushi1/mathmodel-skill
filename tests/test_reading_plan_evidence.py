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

    def test_v10_skill_carrier_is_registered_without_masking_other_changes(self):
        before, after = self.pair()
        after["plan"]["version"] = "10.0.0"
        self.assertTrue(self.compare(before, after)["legacy_behavior_equal_except_approved_changes"])
        after["plan"]["version"] = "11.0.0"
        self.assertIn("version", self.compare(before, after)["unexpected_legacy_changes"])

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


class AuditClosureProjectionTests(unittest.TestCase):
    def pair(self, identifier="facts_current"):
        old = {"version": "<EXPECTED_P9_RELEASE_CARRIER_CHANGE>", "runtime_plan": {},
               "assurance": {"schema_version": "1.2.0", "context": {"field_provenance": {}}}}
        new = deepcopy(old)
        new["version"] = "10.1.0"
        new["assurance"]["schema_version"] = "2.1.0"
        solver = {"scope": "project", "request": "auto", "stage": None, "resolved": "python",
                  "candidate_backend": None, "selection_complete": True, "source": "project_state",
                  "conflicts": [], "environment_verified": False,
                  "decision_contract": "core/user_execution_contract.yaml#solver_backends"}
        if identifier == "facts_unscoped":
            solver.update(scope="stateless", resolved=None, selection_complete=False, source="unresolved")
            new["assurance"]["context"].update(backend_policy=None)
            new["assurance"]["context"]["field_provenance"]["solver_backend"] = "unresolved"
        new["solver_backend"] = deepcopy(solver)
        new["runtime_plan"]["solver_backend"] = deepcopy(solver)
        return old, new

    def test_exact_registered_changes_are_visible_and_inputs_are_immutable(self):
        for case in (*EVIDENCE.A7_HYDRATED_PROVENANCE_CASES, "facts_unscoped"):
            with self.subTest(case=case):
                old, new = self.pair(case)
                saved = deepcopy((old, new))
                projected, changes = EVIDENCE.approved_v1010_audit_changes(case, old, new)
                self.assertEqual(projected, old)
                self.assertNotEqual(new, old)
                self.assertEqual(len(changes), 6 if case == "facts_unscoped" else 4)
                self.assertEqual((old, new), saved)

    def test_unknown_case_or_version_gets_no_projection(self):
        for case, version in (("future_case", "10.1.0"), ("facts_current", "10.2.0")):
            old, new = self.pair()
            new["version"] = version
            projected, changes = EVIDENCE.approved_v1010_audit_changes(case, old, new)
            self.assertEqual(changes, [])
            self.assertEqual(projected, new)

    def test_unapproved_solver_fields_and_extra_metadata_remain_visible(self):
        for key, value in (("environment_verified", True), ("environment_verified", 0), ("resolved", "matlab"),
                           ("selection_complete", False), ("source", "explicit"),
                           ("unexpected_field", "cannot be discarded")):
            with self.subTest(key=key):
                old, new = self.pair()
                new["solver_backend"][key] = value
                projected, _ = EVIDENCE.approved_v1010_audit_changes("facts_current", old, new)
                self.assertNotEqual(projected, old)
                self.assertEqual(projected["solver_backend"][key], value)

    def test_existing_null_is_not_absent_and_unknown_protocol_is_not_approved(self):
        old, new = self.pair()
        old["solver_backend"] = None
        projected, _ = EVIDENCE.approved_v1010_audit_changes("facts_current", old, new)
        self.assertNotEqual(projected, old)
        old, new = self.pair()
        new["assurance"]["schema_version"] = "2.2.0"
        projected, _ = EVIDENCE.approved_v1010_audit_changes("facts_current", old, new)
        self.assertEqual(projected["assurance"]["schema_version"], "2.2.0")

    def test_stateless_selection_and_non_numeric_projections_are_not_waived(self):
        old, new = self.pair("facts_unscoped")
        new["solver_backend"].update(resolved="python", selection_complete=True)
        projected, _ = EVIDENCE.approved_v1010_audit_changes("facts_unscoped", old, new)
        self.assertNotEqual(projected, old)
        old, new = self.pair()
        for case in ("mechanism", "style_unscoped", "cumcm_writing", "receipt"):
            projected, _ = EVIDENCE.approved_v1010_audit_changes(case, old, new)
            self.assertIn("solver_backend", projected)

    def test_full_comparison_keeps_unrelated_assurance_and_gate_changes(self):
        old, new = self.pair()
        for plan in (old, new):
            plan["assurance"]["authority_fingerprint"] = {"sha256": "same", "sources": []}
            plan["reading_plan"] = {"metrics": {"planned_skill_read_bytes": 1,
                                    "planned_project_read_bytes": 0},
                                    "profile": "test", "status": "planned"}
        before = {"id": "facts_current", "plan": old, "legacy_declared_bytes": 1}
        after = {"id": "facts_current", "plan": new, "legacy_declared_bytes": 1}
        row = EVIDENCE.compare([before], [after])[0]
        self.assertTrue(row["legacy_behavior_equal_except_approved_changes"])
        self.assertFalse(row["legacy_behavior_equal"])
        new["assurance"]["status"] = "invented_acceptance"
        new["pre_delivery_gates"] = []
        row = EVIDENCE.compare([before], [after])[0]
        self.assertIn("assurance", row["unexpected_legacy_changes"])
        self.assertIn("pre_delivery_gates", row["unexpected_legacy_changes"])

    def test_b2_carrier_reuses_exact_predecessor_projection(self):
        for case in (*EVIDENCE.A7_HYDRATED_PROVENANCE_CASES, "facts_unscoped"):
            with self.subTest(case=case):
                old, new = self.pair(case)
                new["version"] = "10.5.0"
                new["assurance"]["schema_version"] = "2.2.0"
                saved = deepcopy((old, new))
                projected, changes = EVIDENCE.approved_b2_carrier_change(case, old, new)
                self.assertEqual(projected, old)
                self.assertEqual((old, new), saved)
                self.assertEqual([(item["candidate"], item["approval"])
                                  for item in changes if item["path"] == "version"],
                                 [("10.5.0", "B2 opt-in 10.5.0 carrier only; all old qualification differences remain checked")])

    def test_b2_carrier_rejects_unknown_case_and_version(self):
        for case, version in (("future_case", "10.5.0"), ("facts_current", "10.5.1"),
                              ("facts_current", "11.0.0")):
            with self.subTest(case=case, version=version):
                old, new = self.pair(case)
                new["version"] = version
                new["assurance"]["schema_version"] = "2.2.0"
                projected, changes = EVIDENCE.approved_b2_carrier_change(case, old, new)
                self.assertEqual(projected, new)
                self.assertEqual(changes, [])

    def test_b2_carrier_rejects_assurance_protocol_regression(self):
        for protocol in ("1.2.0", "2.1.0", "2.3.0", None):
            with self.subTest(protocol=protocol):
                old, new = self.pair()
                new["version"] = "10.5.0"
                new["assurance"]["schema_version"] = protocol
                projected, changes = EVIDENCE.approved_b2_carrier_change("facts_current", old, new)
                self.assertEqual(projected, new)
                self.assertEqual(changes, [])

    def test_b2_full_comparison_keeps_unrelated_changes(self):
        old, new = self.pair()
        new["version"] = "10.5.0"
        new["assurance"]["schema_version"] = "2.2.0"
        for plan in (old, new):
            plan["assurance"]["authority_fingerprint"] = {"sha256": "same", "sources": []}
            plan["reading_plan"] = {"metrics": {"planned_skill_read_bytes": 1,
                                    "planned_project_read_bytes": 0},
                                    "profile": "test", "status": "planned"}
        before = {"id": "facts_current", "plan": old, "legacy_declared_bytes": 1}
        after = {"id": "facts_current", "plan": new, "legacy_declared_bytes": 1}
        row = EVIDENCE.compare([before], [after])[0]
        self.assertTrue(row["legacy_behavior_equal_except_approved_changes"])
        self.assertEqual(row["unexpected_legacy_changes"], [])
        new["assurance"]["status"] = "invented_acceptance"
        new["pre_delivery_gates"] = []
        row = EVIDENCE.compare([before], [after])[0]
        self.assertIn("assurance", row["unexpected_legacy_changes"])
        self.assertIn("pre_delivery_gates", row["unexpected_legacy_changes"])
        new["assurance"].pop("status")
        new.pop("pre_delivery_gates")
        new["assurance"]["schema_version"] = "2.1.0"
        row = EVIDENCE.compare([before], [after])[0]
        self.assertFalse(row["legacy_behavior_equal_except_approved_changes"])
        self.assertIn("assurance", row["unexpected_legacy_changes"])
        self.assertIn("version", row["unexpected_legacy_changes"])

    def test_b2b1_carrier_is_exact_and_keeps_other_changes_visible(self):
        for case in (*EVIDENCE.A7_HYDRATED_PROVENANCE_CASES, "facts_unscoped"):
            with self.subTest(case=case):
                old, new = self.pair(case)
                new["version"] = "10.6.0"
                new["assurance"]["schema_version"] = "2.2.0"
                saved = deepcopy((old, new))
                projected, changes = EVIDENCE.approved_b2b1_carrier_change(case, old, new)
                self.assertEqual(projected, old)
                self.assertEqual((old, new), saved)
                self.assertEqual([item["candidate"] for item in changes if item["path"] == "version"],
                                 ["10.6.0"])
        old, new = self.pair()
        new["version"] = "10.6.0"
        new["assurance"]["schema_version"] = "2.2.0"
        new["pre_delivery_gates"] = []
        projected, _ = EVIDENCE.approved_b2b1_carrier_change("facts_current", old, new)
        self.assertEqual(projected["pre_delivery_gates"], [])

    def test_b2b1_carrier_rejects_unknown_and_protocol_regression(self):
        for case, version, protocol in (("future_case", "10.6.0", "2.2.0"),
                                         ("facts_current", "10.6.1", "2.2.0"),
                                         ("facts_current", "10.6.0", "2.1.0"),
                                         ("facts_current", "10.6.0", None)):
            with self.subTest(case=case, version=version, protocol=protocol):
                old, new = self.pair()
                new["version"] = version
                new["assurance"]["schema_version"] = protocol
                projected, changes = EVIDENCE.approved_b2b1_carrier_change(case, old, new)
                self.assertEqual(projected, new)
                self.assertEqual(changes, [])
        old, new = self.pair()
        new["version"] = "10.6.0"
        new["assurance"] = "malformed"
        projected, changes = EVIDENCE.approved_b2b1_carrier_change("facts_current", old, new)
        self.assertEqual(projected, new)
        self.assertEqual(changes, [])

    def test_b2b2_carrier_is_exact_and_preserves_unrelated_differences(self):
        for case in (*EVIDENCE.A7_HYDRATED_PROVENANCE_CASES, "facts_unscoped"):
            with self.subTest(case=case):
                old, new = self.pair(case)
                new["version"] = "10.7.0"
                new["assurance"]["schema_version"] = "2.2.0"
                projected, changes = EVIDENCE.approved_b2b2_carrier_change(case, old, new)
                self.assertEqual(projected, old)
                self.assertEqual([item["candidate"] for item in changes if item["path"] == "version"],
                                 ["10.7.0"])
        old, new = self.pair()
        new["version"] = "10.7.0"
        new["assurance"]["schema_version"] = "2.2.0"
        new["pre_delivery_gates"] = []
        projected, _ = EVIDENCE.approved_b2b2_carrier_change("facts_current", old, new)
        self.assertEqual(projected["pre_delivery_gates"], [])
        for case, version, protocol in (("future_case", "10.7.0", "2.2.0"),
                                         ("facts_current", "10.7.1", "2.2.0"),
                                         ("facts_current", "10.7.0", "2.1.0")):
            with self.subTest(case=case, version=version):
                old, new = self.pair()
                new["version"] = version
                new["assurance"]["schema_version"] = protocol
                projected, changes = EVIDENCE.approved_b2b2_carrier_change(case, old, new)
                self.assertEqual(projected, new)
                self.assertEqual(changes, [])

    def test_b2b3a_carrier_is_exact_and_preserves_unrelated_differences(self):
        for case in (*EVIDENCE.A7_HYDRATED_PROVENANCE_CASES, "facts_unscoped"):
            with self.subTest(case=case):
                old, new = self.pair(case)
                new["version"] = "10.8.0"
                new["assurance"]["schema_version"] = "2.2.0"
                projected, changes = EVIDENCE.approved_b2b3a_carrier_change(case, old, new)
                self.assertEqual(projected, old)
                self.assertEqual([item["candidate"] for item in changes if item["path"] == "version"],
                                 ["10.8.0"])
        old, new = self.pair()
        new["version"] = "10.8.0"
        new["assurance"]["schema_version"] = "2.2.0"
        new["pre_delivery_gates"] = []
        projected, _ = EVIDENCE.approved_b2b3a_carrier_change("facts_current", old, new)
        self.assertEqual(projected["pre_delivery_gates"], [])
        for case, version, protocol in (("future_case", "10.8.0", "2.2.0"),
                                         ("facts_current", "10.8.1", "2.2.0"),
                                         ("facts_current", "10.8.0", "2.1.0")):
            with self.subTest(case=case, version=version):
                old, new = self.pair()
                new["version"] = version
                new["assurance"]["schema_version"] = protocol
                projected, changes = EVIDENCE.approved_b2b3a_carrier_change(case, old, new)
                self.assertEqual(projected, new)
                self.assertEqual(changes, [])

    def test_b2b3b_carrier_is_exact_and_preserves_unrelated_differences(self):
        for case in (*EVIDENCE.A7_HYDRATED_PROVENANCE_CASES, "facts_unscoped"):
            with self.subTest(case=case):
                old, new = self.pair(case)
                new["version"] = "10.9.0"
                new["assurance"]["schema_version"] = "2.2.0"
                projected, changes = EVIDENCE.approved_b2b3b_carrier_change(case, old, new)
                self.assertEqual(projected, old)
                self.assertEqual([item["candidate"] for item in changes if item["path"] == "version"],
                                 ["10.9.0"])
        old, new = self.pair()
        new["version"] = "10.9.0"
        new["assurance"]["schema_version"] = "2.2.0"
        new["pre_delivery_gates"] = []
        projected, _ = EVIDENCE.approved_b2b3b_carrier_change("facts_current", old, new)
        self.assertEqual(projected["pre_delivery_gates"], [])
        for case, version, protocol in (("future_case", "10.9.0", "2.2.0"),
                                         ("facts_current", "10.9.1", "2.2.0"),
                                         ("facts_current", "10.9.0", "2.1.0")):
            with self.subTest(case=case, version=version):
                old, new = self.pair()
                new["version"] = version
                new["assurance"]["schema_version"] = protocol
                projected, changes = EVIDENCE.approved_b2b3b_carrier_change(case, old, new)
                self.assertEqual(projected, new)
                self.assertEqual(changes, [])


if __name__ == "__main__":
    unittest.main()
