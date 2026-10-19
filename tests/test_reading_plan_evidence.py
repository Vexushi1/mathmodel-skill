from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

import yaml

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

    def prepare_b2b6(self, old, new):
        old["assurance"]["authority_fingerprint"] = {"sha256": "same", "sources": []}
        new["assurance"]["authority_fingerprint"] = {
            "sha256": "same",
            "sources": [
                {"path": "core/project_state.schema.yaml", "sha256": "bound-schema"},
                {"path": "core/state_transition_contract.yaml", "sha256": "bound-transition"},
            ],
        }
        new["version"] = "10.12.0"
        new["assurance"]["schema_version"] = "2.3.0"

    def prepare_b2c(self, old, new):
        self.prepare_b2b6(old, new)
        new["version"] = "10.13.0"
        new["assurance"]["schema_version"] = "2.4.0"

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
        for protocol in ("1.2.0", "2.1.0", "2.4.0", None):
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

    def test_b2b3c_carrier_is_exact_and_preserves_unrelated_differences(self):
        for case in (*EVIDENCE.A7_HYDRATED_PROVENANCE_CASES, "facts_unscoped"):
            with self.subTest(case=case):
                old, new = self.pair(case)
                new["version"] = "10.10.0"
                new["assurance"]["schema_version"] = "2.2.0"
                projected, changes = EVIDENCE.approved_b2b3c_carrier_change(case, old, new)
                self.assertEqual(projected, old)
                self.assertEqual([item["candidate"] for item in changes if item["path"] == "version"],
                                 ["10.10.0"])
        old, new = self.pair()
        new["version"] = "10.10.0"
        new["assurance"]["schema_version"] = "2.2.0"
        new["pre_delivery_gates"] = []
        projected, _ = EVIDENCE.approved_b2b3c_carrier_change("facts_current", old, new)
        self.assertEqual(projected["pre_delivery_gates"], [])
        for case, version, protocol in (("future_case", "10.10.0", "2.2.0"),
                                         ("facts_current", "10.10.1", "2.2.0"),
                                         ("facts_current", "10.10.0", "2.1.0")):
            with self.subTest(case=case, version=version):
                old, new = self.pair()
                new["version"] = version
                new["assurance"]["schema_version"] = protocol
                projected, changes = EVIDENCE.approved_b2b3c_carrier_change(case, old, new)
                self.assertEqual(projected, new)
                self.assertEqual(changes, [])

    def test_b2_patch_carrier_is_exact_and_preserves_unrelated_differences(self):
        for case in (*EVIDENCE.A7_HYDRATED_PROVENANCE_CASES, "facts_unscoped"):
            with self.subTest(case=case):
                old, new = self.pair(case)
                new["version"] = "10.10.1"
                new["assurance"]["schema_version"] = "2.2.0"
                projected, changes = EVIDENCE.approved_b2_patch_carrier_change(case, old, new)
                self.assertEqual(projected, old)
                self.assertEqual([item["candidate"] for item in changes if item["path"] == "version"],
                                 ["10.10.1"])
        old, new = self.pair()
        new["version"] = "10.10.1"
        new["assurance"]["schema_version"] = "2.2.0"
        new["pre_delivery_gates"] = []
        projected, _ = EVIDENCE.approved_b2_patch_carrier_change("facts_current", old, new)
        self.assertEqual(projected["pre_delivery_gates"], [])
        for case, version, protocol in (("future_case", "10.10.1", "2.2.0"),
                                         ("facts_current", "10.10.2", "2.2.0"),
                                         ("facts_current", "10.10.1", "2.1.0")):
            with self.subTest(case=case, version=version):
                old, new = self.pair()
                new["version"] = version
                new["assurance"]["schema_version"] = protocol
                projected, changes = EVIDENCE.approved_b2_patch_carrier_change(case, old, new)
                self.assertEqual(projected, new)
                self.assertEqual(changes, [])

    def test_b2b4_carrier_is_exact_and_preserves_unrelated_differences(self):
        for case in (*EVIDENCE.A7_HYDRATED_PROVENANCE_CASES, "facts_unscoped"):
            with self.subTest(case=case):
                old, new = self.pair(case)
                new["version"] = "10.11.0"
                new["assurance"]["schema_version"] = "2.2.0"
                projected, changes = EVIDENCE.approved_b2b4_carrier_change(case, old, new)
                self.assertEqual(projected, old)
                self.assertEqual([item["candidate"] for item in changes if item["path"] == "version"],
                                 ["10.11.0"])
        old, new = self.pair()
        new["version"] = "10.11.0"
        new["assurance"]["schema_version"] = "2.2.0"
        new["pre_delivery_gates"] = []
        projected, _ = EVIDENCE.approved_b2b4_carrier_change("facts_current", old, new)
        self.assertEqual(projected["pre_delivery_gates"], [])
        for case, version, protocol in (("future_case", "10.11.0", "2.2.0"),
                                         ("facts_current", "10.11.1", "2.2.0"),
                                         ("facts_current", "10.11.0", "2.1.0")):
            with self.subTest(case=case, version=version):
                old, new = self.pair()
                new["version"] = version
                new["assurance"]["schema_version"] = protocol
                projected, changes = EVIDENCE.approved_b2b4_carrier_change(case, old, new)
                self.assertEqual(projected, new)
                self.assertEqual(changes, [])


    def test_b2b5_carrier_is_exact_and_preserves_unrelated_differences(self):
        for case in (*EVIDENCE.A7_HYDRATED_PROVENANCE_CASES, "facts_unscoped"):
            with self.subTest(case=case):
                old, new = self.pair(case)
                new["version"] = "10.11.1"
                new["assurance"]["schema_version"] = "2.2.0"
                original = deepcopy(new)
                projected, changes = EVIDENCE.approved_b2b5_carrier_change(case, old, new)
                self.assertEqual(projected, old)
                self.assertEqual(new, original)
                self.assertEqual([item["candidate"] for item in changes if item["path"] == "version"],
                                 ["10.11.1"])
        old, new = self.pair()
        new["version"] = "10.11.1"
        new["assurance"]["schema_version"] = "2.2.0"
        new["pre_delivery_gates"] = []
        projected, _ = EVIDENCE.approved_b2b5_carrier_change("facts_current", old, new)
        self.assertEqual(projected["pre_delivery_gates"], [])
        for case, version, protocol in (("future_case", "10.11.1", "2.2.0"),
                                         ("facts_current", "10.11.2", "2.2.0"),
                                         ("facts_current", "10.11.1", "2.1.0")):
            with self.subTest(case=case, version=version):
                old, new = self.pair()
                new["version"] = version
                new["assurance"]["schema_version"] = protocol
                projected, changes = EVIDENCE.approved_b2b5_carrier_change(case, old, new)
                self.assertEqual(projected, new)
                self.assertEqual(changes, [])


    def test_b2b6_historical_carrier_keeps_its_exact_version_set(self):
        old, new = self.pair()
        self.prepare_b2b6(old, new)
        projected, changes = EVIDENCE.approved_b2b6_carrier_change(
            "facts_current", old, new, deepcopy(EVIDENCE.B2B6_AUTHORITY_VERSIONS)
        )
        self.assertEqual(projected, old)
        self.assertEqual(
            [item["candidate"] for item in changes if item["path"] == "version"],
            ["10.12.0"],
        )

    def test_b2c_carrier_requires_the_exact_six_version_set(self):
        carriers = deepcopy(EVIDENCE.B2C_AUTHORITY_VERSIONS)
        for case in (*EVIDENCE.A7_HYDRATED_PROVENANCE_CASES, "facts_unscoped"):
            with self.subTest(case=case):
                old, new = self.pair(case)
                self.prepare_b2c(old, new)
                original = deepcopy(new)
                projected, changes = EVIDENCE.approved_b2c_carrier_change(
                    case, old, new, carriers
                )
                self.assertEqual(projected, old)
                self.assertEqual(new, original)
                version_changes = [item for item in changes if item["path"] == "version"]
                self.assertEqual([item["candidate"] for item in version_changes], ["10.13.0"])
                self.assertEqual(version_changes[0]["authority_versions"], carriers)

    def test_c1_carrier_requires_only_exact_opt_in_versions(self):
        carriers = deepcopy(EVIDENCE.C1_AUTHORITY_VERSIONS)
        for case in (*EVIDENCE.A7_HYDRATED_PROVENANCE_CASES, "facts_unscoped"):
            with self.subTest(case=case):
                old, new = self.pair(case)
                self.prepare_b2c(old, new)
                new["version"] = "10.14.0"
                projected, changes = EVIDENCE.approved_c1_carrier_change(case, old, new, carriers)
                self.assertEqual(projected, old)
                version_changes = [item for item in changes if item["path"] == "version"]
                self.assertEqual([item["candidate"] for item in version_changes], ["10.14.0"])
                self.assertEqual(version_changes[0]["authority_versions"], carriers)
                bad = deepcopy(carriers)
                bad["project_state"] = "8.13.1"
                self.assertEqual(EVIDENCE.approved_c1_carrier_change(case, old, new, bad), (new, []))

    def test_windows_python_ci_patch_changes_only_the_exact_skill_carrier(self):
        carriers = deepcopy(EVIDENCE.WINDOWS_PYTHON_CI_AUTHORITY_VERSIONS)
        for case in (*EVIDENCE.A7_HYDRATED_PROVENANCE_CASES, "facts_unscoped"):
            with self.subTest(case=case):
                old, new = self.pair(case)
                self.prepare_b2c(old, new)
                new["version"] = "10.14.1"
                projected, changes = EVIDENCE.approved_windows_python_ci_carrier_change(case, old, new, carriers)
                self.assertEqual(projected, old)
                version_changes = [item for item in changes if item["path"] == "version"]
                self.assertEqual([item["candidate"] for item in version_changes], ["10.14.1"])
                self.assertEqual(version_changes[0]["authority_versions"], carriers)
                bad_carriers = {**carriers, "project_state": "8.13.1"}
                self.assertEqual(EVIDENCE.approved_windows_python_ci_carrier_change(
                    case, old, new, bad_carriers), (new, []))
                unrelated = deepcopy(new)
                unrelated["pre_delivery_gates"] = []
                self.assertEqual(EVIDENCE.approved_windows_python_ci_carrier_change(
                    case, old, unrelated, carriers), (unrelated, []))

    def test_windows_matlab_ci_patch_changes_only_the_exact_skill_carrier(self):
        carriers = deepcopy(EVIDENCE.WINDOWS_MATLAB_CI_AUTHORITY_VERSIONS)
        for case in (*EVIDENCE.A7_HYDRATED_PROVENANCE_CASES, "facts_unscoped"):
            with self.subTest(case=case):
                old, new = self.pair(case)
                self.prepare_b2c(old, new)
                new["version"] = "10.14.2"
                projected, changes = EVIDENCE.approved_windows_matlab_ci_carrier_change(
                    case, old, new, carriers)
                self.assertEqual(projected, old)
                version_changes = [item for item in changes if item["path"] == "version"]
                self.assertEqual([item["candidate"] for item in version_changes], ["10.14.2"])
                self.assertEqual(version_changes[0]["authority_versions"], carriers)
                bad_carriers = {**carriers, "project_state": "8.13.1"}
                self.assertEqual(EVIDENCE.approved_windows_matlab_ci_carrier_change(
                    case, old, new, bad_carriers), (new, []))
                unrelated = deepcopy(new)
                unrelated["pre_delivery_gates"] = []
                self.assertEqual(EVIDENCE.approved_windows_matlab_ci_carrier_change(
                    case, old, unrelated, carriers), (unrelated, []))

    def test_c2_carrier_requires_exact_scoped_authority_and_preserves_legacy_gates(self):
        carriers = deepcopy(EVIDENCE.C2_AUTHORITY_VERSIONS)
        for case in (*EVIDENCE.A7_HYDRATED_PROVENANCE_CASES, "facts_unscoped"):
            with self.subTest(case=case):
                old, new = self.pair(case)
                self.prepare_b2c(old, new)
                new["version"] = "10.15.0"
                original = deepcopy(new)
                projected, changes = EVIDENCE.approved_c2_carrier_change(
                    case, old, new, carriers)
                self.assertEqual(projected, old)
                self.assertEqual(new, original)
                version_changes = [item for item in changes if item["path"] == "version"]
                self.assertEqual([item["candidate"] for item in version_changes], ["10.15.0"])
                self.assertEqual(version_changes[0]["authority_versions"], carriers)
                for bad_carriers in (
                    {**carriers, "project_state": "8.13.0"},
                    {**carriers, "review_receipt_consumption": "1.0.1"},
                    {key: value for key, value in carriers.items()
                     if key != "review_receipt_consumption"},
                ):
                    self.assertEqual(EVIDENCE.approved_c2_carrier_change(
                        case, old, new, bad_carriers), (new, []))
                unrelated = deepcopy(new)
                unrelated["pre_delivery_gates"] = []
                self.assertEqual(EVIDENCE.approved_c2_carrier_change(
                    case, old, unrelated, carriers), (unrelated, []))

    def test_python_ci_performance_patch_changes_only_exact_carriers(self):
        carriers = deepcopy(EVIDENCE.PYTHON_CI_PERFORMANCE_AUTHORITY_VERSIONS)
        for case in (*EVIDENCE.A7_HYDRATED_PROVENANCE_CASES, "facts_unscoped"):
            with self.subTest(case=case):
                old, new = self.pair(case)
                self.prepare_b2c(old, new)
                new["version"] = "10.15.1"
                original = deepcopy(new)
                projected, changes = EVIDENCE.approved_python_ci_performance_carrier_change(
                    case, old, new, carriers)
                self.assertEqual(projected, old)
                self.assertEqual(new, original)
                version_changes = [item for item in changes if item["path"] == "version"]
                self.assertEqual([item["candidate"] for item in version_changes], ["10.15.1"])
                self.assertEqual(version_changes[0]["authority_versions"], carriers)
                for bad_carriers in (
                    {**carriers, "project_state": "8.14.1"},
                    {**carriers, "review_receipt_consumption": "1.0.1"},
                    {**carriers, "runtime_assurance": "2.4.1"},
                    {key: value for key, value in carriers.items()
                     if key != "review_receipt_consumption"},
                ):
                    self.assertEqual(EVIDENCE.approved_python_ci_performance_carrier_change(
                        case, old, new, bad_carriers), (new, []))
                for field, value in (("pre_delivery_gates", []), ("version", "10.15.2")):
                    unrelated = deepcopy(new)
                    unrelated[field] = value
                    self.assertEqual(EVIDENCE.approved_python_ci_performance_carrier_change(
                        case, old, unrelated, carriers), (unrelated, []))

    def test_d1_carrier_keeps_exact_c2_protocols_and_immutable_inputs(self):
        carriers = deepcopy(EVIDENCE.D1_AUTHORITY_VERSIONS)
        self.assertEqual(carriers, {**EVIDENCE.C2_AUTHORITY_VERSIONS, "skill": "10.16.0"})
        for case in (*EVIDENCE.A7_HYDRATED_PROVENANCE_CASES, "facts_unscoped"):
            with self.subTest(case=case):
                old, new = self.pair(case)
                self.prepare_b2c(old, new)
                new["version"] = "10.16.0"
                original = deepcopy(new)
                projected, changes = EVIDENCE.approved_d1_carrier_change(case, old, new, carriers)
                self.assertEqual(projected, old)
                self.assertEqual(new, original)
                version_changes = [item for item in changes if item["path"] == "version"]
                self.assertEqual([item["candidate"] for item in version_changes], ["10.16.0"])
                self.assertEqual(version_changes[0]["authority_versions"], carriers)
                for bad_carriers in (
                    *({**carriers, key: "unknown"} for key in carriers),
                    {key: value for key, value in carriers.items() if key != "project_state"},
                    {**carriers, "case_memory": "1.0.0"},
                ):
                    self.assertEqual(EVIDENCE.approved_d1_carrier_change(
                        case, old, new, bad_carriers), (new, []))

    def test_d1_does_not_hide_case_loading_qualification_gate_or_unknown_version_changes(self):
        old, new = self.pair()
        self.prepare_b2c(old, new)
        new["version"] = "10.16.0"
        carriers = deepcopy(EVIDENCE.D1_AUTHORITY_VERSIONS)
        for field, value in (
            ("pre_delivery_gates", []),
            ("load_order", ["knowledge/case_memory/cases/synthetic.yaml"]),
            ("version", "10.16.1"),
        ):
            with self.subTest(field=field):
                changed = deepcopy(new)
                changed[field] = value
                self.assertEqual(EVIDENCE.approved_d1_carrier_change(
                    "facts_current", old, changed, carriers), (changed, []))
        changed = deepcopy(new)
        changed["assurance"]["qualification"] = "accepted"
        self.assertEqual(EVIDENCE.approved_d1_carrier_change(
            "facts_current", old, changed, carriers), (changed, []))
        changed = deepcopy(new)
        changed["assurance"]["authority_fingerprint"]["sources"].append(
            {"path": "knowledge/case_memory/schema.yaml", "sha256": "case-schema"}
        )
        self.assertEqual(EVIDENCE.approved_d1_carrier_change(
            "facts_current", old, changed, carriers), (changed, []))
        self.assertEqual(EVIDENCE.approved_d1_carrier_change(
            "future_case", old, new, carriers), (new, []))
        wrong_baseline = deepcopy(old)
        wrong_baseline["version"] = "10.15.1"
        self.assertEqual(EVIDENCE.approved_d1_carrier_change(
            "facts_current", wrong_baseline, new, carriers), (new, []))

    def test_current_comparison_runtime_metadata_excludes_independent_corpus_schema(self):
        # The 10.18.2 submission patch stays an immutable comparison checkpoint.
        # A later Skill patch changes only the live Skill carrier, not the
        # independently versioned protocol authorities or the historical fixture.
        historical = EVIDENCE.SUBMISSION_PATCH_AUTHORITY_VERSIONS
        self.assertEqual(historical["skill"], "10.18.2")
        current = yaml.safe_load((EVIDENCE.HERE.parents[1] / "core/bootstrap.yaml").read_text(encoding="utf-8"))["skill_version"]
        self.assertEqual(
            EVIDENCE.authority_versions(EVIDENCE.HERE.parents[1]),
            {**historical, "skill": str(current)},
        )

    def test_e1_patch_retains_d2_history_and_rejects_qualification_or_loading_drift(self):
        carriers = deepcopy(EVIDENCE.E1_AUTHORITY_VERSIONS)
        self.assertEqual(carriers, {**EVIDENCE.D2_AUTHORITY_VERSIONS, "skill": "10.17.1"})
        for case in (*EVIDENCE.A7_HYDRATED_PROVENANCE_CASES, "facts_unscoped"):
            with self.subTest(case=case):
                old, new = self.pair(case)
                self.prepare_b2c(old, new)
                new["version"] = "10.17.1"
                original = deepcopy(new)
                projected, changes = EVIDENCE.approved_e1_carrier_change(case, old, new, carriers)
                self.assertEqual(projected, old)
                self.assertEqual(new, original)
                self.assertEqual([c["candidate"] for c in changes if c["path"] == "version"], ["10.17.1"])
                for bad in ({**carriers, "project_state": "8.16.0"},
                            {**carriers, "skill": "10.17.2"},
                            {**carriers, "case_memory_retrieval": "1.0.0"}):
                    self.assertEqual(EVIDENCE.approved_e1_carrier_change(case, old, new, bad), (new, []))
                for field, value in (("load_order", ["knowledge/case_memory/index.json"]),
                                     ("pre_delivery_gates", []), ("formal_delivery", True),
                                     ("version", "10.17.2")):
                    changed = deepcopy(new)
                    changed[field] = value
                    self.assertEqual(EVIDENCE.approved_e1_carrier_change(case, old, changed, carriers), (changed, []))
                changed = deepcopy(new)
                changed["assurance"]["qualification"] = "accepted"
                self.assertEqual(EVIDENCE.approved_e1_carrier_change(case, old, changed, carriers), (changed, []))

    def test_comparison_carrier_preserves_inactive_runtime_and_rejects_unregistered_drift(self):
        carriers = deepcopy(EVIDENCE.COMPARISON_AUTHORITY_VERSIONS)
        for case in (*EVIDENCE.A7_HYDRATED_PROVENANCE_CASES, "facts_unscoped"):
            with self.subTest(case=case):
                old, new = self.pair(case)
                self.prepare_b2c(old, new)
                new["version"] = "10.18.0"
                new["assurance"]["schema_version"] = "2.5.0"
                original = deepcopy(new)
                projected, changes = EVIDENCE.approved_comparison_carrier_change(case, old, new, carriers)
                self.assertEqual(projected, old)
                self.assertTrue(changes)
                self.assertEqual(new, original)
                for field, value in (("pre_delivery_gates", []), ("formal_delivery", True),
                                     ("load_order", ["scripts/analysis_comparison.py"])):
                    changed = deepcopy(new)
                    changed[field] = value
                    self.assertEqual(EVIDENCE.approved_comparison_carrier_change(
                        case, old, changed, carriers), (changed, []))
                changed = deepcopy(new)
                changed["assurance"]["qualification"] = "accepted"
                self.assertEqual(EVIDENCE.approved_comparison_carrier_change(
                    case, old, changed, carriers), (changed, []))
                bad = {**carriers, "project_state": "8.17.0"}
                self.assertEqual(EVIDENCE.approved_comparison_carrier_change(case, old, new, bad), (new, []))

    def test_audit_patch_carrier_does_not_hide_behavior_or_protocol_changes(self):
        carriers = deepcopy(EVIDENCE.AUDIT_PATCH_AUTHORITY_VERSIONS)
        for case in (*EVIDENCE.A7_HYDRATED_PROVENANCE_CASES, "facts_unscoped"):
            with self.subTest(case=case):
                old, new = self.pair(case)
                self.prepare_b2c(old, new)
                new["version"] = "10.18.1"
                new["assurance"]["schema_version"] = "2.5.0"
                original = deepcopy(new)
                projected, changes = EVIDENCE.approved_audit_patch_carrier_change(case, old, new, carriers)
                self.assertEqual(projected, old)
                self.assertTrue(changes)
                self.assertEqual(new, original)
                for field, value in (("version", "10.18.2"), ("pre_delivery_gates", []),
                                     ("formal_delivery", True), ("load_order", ["scripts/semantic_identity.py"])):
                    changed = deepcopy(new)
                    changed[field] = value
                    self.assertEqual(EVIDENCE.approved_audit_patch_carrier_change(
                        case, old, changed, carriers), (changed, []))
                changed = deepcopy(new)
                changed["assurance"]["qualification"] = "accepted"
                self.assertEqual(EVIDENCE.approved_audit_patch_carrier_change(case, old, changed, carriers), (changed, []))
                bad = {**carriers, "project_state": "8.17.0"}
                self.assertEqual(EVIDENCE.approved_audit_patch_carrier_change(case, old, new, bad), (new, []))

    def test_submission_patch_carrier_preserves_behavior_and_protocol_checks(self):
        carriers = deepcopy(EVIDENCE.SUBMISSION_PATCH_AUTHORITY_VERSIONS)
        for case in (*EVIDENCE.A7_HYDRATED_PROVENANCE_CASES, "facts_unscoped"):
            with self.subTest(case=case):
                old, new = self.pair(case)
                self.prepare_b2c(old, new)
                new["version"] = "10.18.2"
                new["assurance"]["schema_version"] = "2.5.0"
                original = deepcopy(new)
                projected, changes = EVIDENCE.approved_submission_patch_carrier_change(
                    case, old, new, carriers)
                self.assertEqual(projected, old)
                self.assertTrue(changes)
                self.assertEqual(new, original)
                for field, value in (("version", "10.18.3"), ("pre_delivery_gates", []),
                                     ("formal_delivery", True), ("load_order", ["scripts/semantic_identity.py"])):
                    changed = deepcopy(new)
                    changed[field] = value
                    self.assertEqual(EVIDENCE.approved_submission_patch_carrier_change(
                        case, old, changed, carriers), (changed, []))
                changed = deepcopy(new)
                changed["assurance"]["qualification"] = "accepted"
                self.assertEqual(EVIDENCE.approved_submission_patch_carrier_change(
                    case, old, changed, carriers), (changed, []))
                bad = {**carriers, "project_state": "8.17.0"}
                self.assertEqual(EVIDENCE.approved_submission_patch_carrier_change(
                    case, old, new, bad), (new, []))

    def test_v10183_writing_patch_only_projects_exact_skill_carrier(self):
        carriers = deepcopy(EVIDENCE.WRITING_PATCH_AUTHORITY_VERSIONS)
        self.assertEqual(carriers, {
            **EVIDENCE.SUBMISSION_PATCH_AUTHORITY_VERSIONS, "skill": "10.18.3"
        })
        for case in (*EVIDENCE.A7_HYDRATED_PROVENANCE_CASES, "facts_unscoped"):
            with self.subTest(case=case):
                old, new = self.pair(case)
                self.prepare_b2c(old, new)
                new["version"] = "10.18.3"
                new["assurance"]["schema_version"] = "2.5.0"
                original = deepcopy(new)
                projected, changes = EVIDENCE.approved_writing_patch_carrier_change(
                    case, old, new, carriers
                )
                self.assertEqual(projected, old)
                self.assertEqual(new, original)
                self.assertEqual([c["candidate"] for c in changes if c["path"] == "version"],
                                 ["10.18.3"])
                for field, value in (("version", "10.18.4"),
                                     ("formal_delivery", True),
                                     ("load_order", ["scripts/semantic_identity.py"]),
                                     ("pre_delivery_gates", [])):
                    altered = deepcopy(new)
                    altered[field] = value
                    self.assertEqual(EVIDENCE.approved_writing_patch_carrier_change(
                        case, old, altered, carriers
                    ), (altered, []))
                altered = deepcopy(new)
                altered["assurance"]["qualification"] = "accepted"
                self.assertEqual(EVIDENCE.approved_writing_patch_carrier_change(
                    case, old, altered, carriers
                ), (altered, []))
                for bad in ({**carriers, "project_state": "8.17.0"},
                            {**carriers, "writing_reasoning": "1.12.0"},
                            {**carriers, "skill": "10.18.4"}):
                    self.assertEqual(EVIDENCE.approved_writing_patch_carrier_change(
                        case, old, new, bad
                    ), (new, []))
                # This class has no compare() fixture helper. Exercise the real
                # comparator directly so every approved version transition and
                # every unrelated runtime field still receives strict checking.
                # compare() validates the actual P2 reading-plan contract
                # before projecting legacy fields. Supply the same complete
                # plan fixture used by the existing full-comparison tests.
                reading_plan = {
                    "metrics": {
                        "planned_skill_read_bytes": 1,
                        "planned_project_read_bytes": 0,
                    },
                    "profile": "test",
                    "status": "planned",
                }
                old["reading_plan"] = deepcopy(reading_plan)
                new["reading_plan"] = deepcopy(reading_plan)
                row = EVIDENCE.compare(
                    [{"id": case, "plan": old, "legacy_declared_bytes": 1}],
                    [{"id": case, "plan": new, "legacy_declared_bytes": 1,
                      "authority_versions": carriers}],
                )[0]
                self.assertTrue(row["legacy_behavior_equal_except_approved_changes"])
                self.assertEqual(row["unexpected_legacy_changes"], [])
                self.assertIn("10.18.3", [x["candidate"] for x in row["expected_legacy_changes"]
                                          if x["path"] == "version"])

    def figure_handoff_pair(self, case):
        if case == "cumcm_writing":
            old, new = self.comparison_writing_pair()
            for runtime in (new["writing_runtime"], new["runtime_plan"]["writing_runtime"]):
                stage = runtime["authoring_sequence"][4]
                for path, previous, current in EVIDENCE.FIGURE_HANDOFF_WRITING_DELTAS:
                    target = stage
                    for key in path[:-1]:
                        target = target[key]
                    self.assertEqual(target[path[-1]], previous)
                    target[path[-1]] = deepcopy(current)
        else:
            old, new = self.pair(case)
            self.prepare_b2c(old, new)
            new["assurance"]["schema_version"] = "2.5.0"
        new["version"] = "10.19.3"
        for plan in (old, new):
            plan["reading_plan"] = {
                "metrics": {"planned_skill_read_bytes": 1, "planned_project_read_bytes": 0},
                "profile": "test", "status": "planned",
            }
        return old, new

    def test_v10193_handoff_carrier_composes_without_rewriting_history(self):
        carriers = deepcopy(EVIDENCE.FIGURE_HANDOFF_AUTHORITY_VERSIONS)
        self.assertEqual(carriers, {**EVIDENCE.WRITING_PATCH_AUTHORITY_VERSIONS, "skill": "10.19.3"})
        self.assertEqual(EVIDENCE.WRITING_PATCH_AUTHORITY_VERSIONS["skill"], "10.18.3")
        for case in (*sorted(EVIDENCE.A7_HYDRATED_PROVENANCE_CASES), "facts_unscoped", "cumcm_writing"):
            with self.subTest(case=case):
                old, new = self.figure_handoff_pair(case)
                saved = deepcopy((old, new, carriers))
                row = EVIDENCE.compare(
                    [{"id": case, "plan": old, "legacy_declared_bytes": 1}],
                    [{"id": case, "plan": new, "legacy_declared_bytes": 1,
                      "authority_versions": carriers}],
                )[0]
                self.assertFalse(row["legacy_behavior_equal"])
                self.assertTrue(row["legacy_behavior_equal_except_approved_changes"])
                self.assertEqual(row["unexpected_legacy_changes"], [])
                version_changes = [item for item in row["expected_legacy_changes"] if item["path"] == "version"]
                self.assertEqual([item["candidate"] for item in version_changes], ["10.19.3"])
                self.assertEqual(version_changes[0]["authority_versions"], carriers)
                handoff_changes = [item for item in row["expected_legacy_changes"]
                                   if "authoring_sequence.4." in item["path"]]
                self.assertEqual(len(handoff_changes), 6 if case == "cumcm_writing" else 0)
                self.assertEqual((old, new, carriers), saved)

    def test_v10193_handoff_carrier_rejects_unregistered_decisions_and_versions(self):
        carriers = deepcopy(EVIDENCE.FIGURE_HANDOFF_AUTHORITY_VERSIONS)
        for case in ("facts_current", "cumcm_writing"):
            with self.subTest(case=case):
                old, new = self.figure_handoff_pair(case)
                for bad in (None, {**carriers, "skill": "10.19.4"},
                            {**carriers, "project_state": "8.17.0"},
                            {**carriers, "writing_reasoning": "1.12.0"},
                            {k: v for k, v in carriers.items() if k != "runtime_assurance"}):
                    self.assertEqual(EVIDENCE.approved_figure_handoff_carrier_change(
                        case, old, new, bad), (new, []))
                for field, value in (("version", "10.19.4"), ("formal_delivery", True),
                                     ("load_order", ["scripts/semantic_identity.py"]),
                                     ("pre_delivery_gates", [])):
                    changed = deepcopy(new)
                    changed[field] = value
                    self.assertEqual(EVIDENCE.approved_figure_handoff_carrier_change(
                        case, old, changed, carriers), (changed, []))
                changed = deepcopy(new)
                changed["assurance"]["qualification"] = "accepted"
                self.assertEqual(EVIDENCE.approved_figure_handoff_carrier_change(
                    case, old, changed, carriers), (changed, []))
                if case == "cumcm_writing":
                    changed = deepcopy(new)
                    changed["runtime_plan"]["writing_runtime"]["full_reasoning_authority_preloaded"] = True
                    self.assertEqual(EVIDENCE.approved_figure_handoff_carrier_change(
                        case, old, changed, carriers), (changed, []))
        old, new = self.figure_handoff_pair("facts_current")
        self.assertEqual(EVIDENCE.approved_figure_handoff_carrier_change(
            "future_case", old, new, carriers), (new, []))

    def test_v10193_handoff_projection_pins_each_leaf_and_keeps_other_stage_fields(self):
        carriers = EVIDENCE.FIGURE_HANDOFF_AUTHORITY_VERSIONS
        for location in ("top", "nested"):
            for mutation in ("extra_read", "read_order", "missing_read", "preflight_gate",
                             "completion_gate", "dispatch", "missing_stage", "old_gate"):
                with self.subTest(location=location, mutation=mutation):
                    old, new = self.figure_handoff_pair("cumcm_writing")
                    runtime = new["writing_runtime"] if location == "top" else new["runtime_plan"]["writing_runtime"]
                    stage = runtime["authoring_sequence"][4]
                    preflight = stage["before_write_preflight"]
                    if mutation == "extra_read":
                        preflight["read_now"].append("core/writing_reasoning_contract.yaml")
                    elif mutation == "read_order":
                        preflight["read_now"].reverse()
                    elif mutation == "missing_read":
                        preflight["read_now"].pop()
                    elif mutation == "preflight_gate":
                        preflight["gate"] += "额外规则。"
                    elif mutation == "completion_gate":
                        stage["gate"] = "已完成"
                    elif mutation == "dispatch":
                        preflight["dispatch_from_project_state"] = False
                    elif mutation == "missing_stage":
                        runtime["authoring_sequence"].pop(4)
                    else:
                        baseline = old["writing_runtime"] if location == "top" else old["runtime_plan"]["writing_runtime"]
                        baseline["authoring_sequence"][4]["gate"] += "未授权基线变化。"
                    self.assertEqual(EVIDENCE.approved_figure_handoff_carrier_change(
                        "cumcm_writing", old, new, carriers), (new, []))

    def test_v10203_workflow_carrier_preserves_handoff_history_and_input_identity(self):
        carriers = deepcopy(EVIDENCE.USER_CHECKER_WORKFLOW_AUTHORITY_VERSIONS)
        self.assertEqual(carriers, {**EVIDENCE.FIGURE_HANDOFF_AUTHORITY_VERSIONS, "skill": "10.20.3"})
        self.assertEqual(EVIDENCE.FIGURE_HANDOFF_AUTHORITY_VERSIONS["skill"], "10.19.3")
        for case in (*sorted(EVIDENCE.A7_HYDRATED_PROVENANCE_CASES), "facts_unscoped", "cumcm_writing"):
            with self.subTest(case=case):
                old, new = self.figure_handoff_pair(case)
                new["version"] = "10.20.3"
                saved = deepcopy((old, new, carriers))
                row = EVIDENCE.compare(
                    [{"id": case, "plan": old, "legacy_declared_bytes": 1}],
                    [{"id": case, "plan": new, "legacy_declared_bytes": 1,
                      "authority_versions": carriers}],
                )[0]
                self.assertFalse(row["legacy_behavior_equal"])
                self.assertTrue(row["legacy_behavior_equal_except_approved_changes"])
                self.assertEqual(row["unexpected_legacy_changes"], [])
                version_changes = [item for item in row["expected_legacy_changes"] if item["path"] == "version"]
                self.assertEqual([item["candidate"] for item in version_changes], ["10.20.3"])
                self.assertEqual(version_changes[0]["authority_versions"], carriers)
                handoff_changes = [item for item in row["expected_legacy_changes"]
                                   if "authoring_sequence.4." in item["path"]]
                self.assertEqual(len(handoff_changes), 6 if case == "cumcm_writing" else 0)
                self.assertEqual((old, new, carriers), saved)

    def test_v10203_workflow_carrier_does_not_waive_runtime_or_authority_changes(self):
        carriers = EVIDENCE.USER_CHECKER_WORKFLOW_AUTHORITY_VERSIONS
        for case in ("facts_current", "cumcm_writing"):
            with self.subTest(case=case):
                old, new = self.figure_handoff_pair(case)
                new["version"] = "10.20.3"
                for bad in (None, {**carriers, "skill": "10.20.4"},
                            {**carriers, "project_state": "8.17.0"},
                            {**carriers, "writing_reasoning": "1.12.0"},
                            {k: v for k, v in carriers.items() if k != "runtime_assurance"}):
                    self.assertEqual(EVIDENCE.approved_user_checker_workflow_carrier_change(
                        case, old, new, bad), (new, []))
                for field, value in (("version", "10.20.4"), ("formal_delivery", True),
                                     ("load_order", ["scripts/semantic_identity.py"]),
                                     ("pre_delivery_gates", [])):
                    changed = deepcopy(new)
                    changed[field] = value
                    self.assertEqual(EVIDENCE.approved_user_checker_workflow_carrier_change(
                        case, old, changed, carriers), (changed, []))
                changed = deepcopy(new)
                changed["assurance"]["qualification"] = "accepted"
                self.assertEqual(EVIDENCE.approved_user_checker_workflow_carrier_change(
                    case, old, changed, carriers), (changed, []))
                if case == "cumcm_writing":
                    for runtime_path in (("writing_runtime",), ("runtime_plan", "writing_runtime")):
                        for suffix, _, _ in EVIDENCE.FIGURE_HANDOFF_WRITING_DELTAS:
                            changed = deepcopy(new)
                            target = changed
                            for key in (*runtime_path, "authoring_sequence", 4, *suffix[:-1]):
                                target = target[key]
                            value = target[suffix[-1]]
                            target[suffix[-1]] = [*value, "unapproved"] if isinstance(value, list) else value + "未授权规则。"
                            self.assertEqual(EVIDENCE.approved_user_checker_workflow_carrier_change(
                                case, old, changed, carriers), (changed, []))
        old, new = self.figure_handoff_pair("facts_current")
        new["version"] = "10.20.3"
        self.assertEqual(EVIDENCE.approved_user_checker_workflow_carrier_change(
            "future_case", old, new, carriers), (new, []))

    def pdf_review_pair(self, case):
        old, new = self.figure_handoff_pair(case)
        new["version"] = "10.20.4"
        if case == "cumcm_writing":
            for runtime in (new["writing_runtime"], new["runtime_plan"]["writing_runtime"]):
                stage = runtime["authoring_sequence"][9]
                self.assertEqual(stage["id"], "latex_assembly_audit_and_compile")
                self.assertEqual(stage["run_now"], [
                    "scripts/validate_template_manifest.py", "scripts/audit_latex_project.py",
                    "scripts/render_paper.py",
                ])
                stage["run_now"] = ["scripts/validate_template_manifest.py", "scripts/render_paper.py"]
        return old, new

    def test_v10204_pdf_review_carrier_projects_only_two_assembly_lists(self):
        carriers = deepcopy(EVIDENCE.PDF_REVIEW_AUTHORITY_VERSIONS)
        self.assertEqual(carriers, {**EVIDENCE.USER_CHECKER_WORKFLOW_AUTHORITY_VERSIONS, "skill": "10.20.4"})
        self.assertEqual(EVIDENCE.USER_CHECKER_WORKFLOW_AUTHORITY_VERSIONS["skill"], "10.20.3")
        self.assertEqual(EVIDENCE.PDF_REVIEW_WRITING_DELTAS, (
            (("run_now",),
             ["scripts/validate_template_manifest.py", "scripts/audit_latex_project.py", "scripts/render_paper.py"],
             ["scripts/validate_template_manifest.py", "scripts/render_paper.py"]),
        ))
        for case in (*sorted(EVIDENCE.A7_HYDRATED_PROVENANCE_CASES), "facts_unscoped", "cumcm_writing"):
            with self.subTest(case=case):
                old, new = self.pdf_review_pair(case)
                saved = deepcopy((old, new, carriers, EVIDENCE.PDF_REVIEW_WRITING_DELTAS))
                row = EVIDENCE.compare(
                    [{"id": case, "plan": old, "legacy_declared_bytes": 1}],
                    [{"id": case, "plan": new, "legacy_declared_bytes": 1,
                      "authority_versions": carriers}],
                )[0]
                self.assertFalse(row["legacy_behavior_equal"])
                self.assertTrue(row["legacy_behavior_equal_except_approved_changes"])
                self.assertEqual(row["unexpected_legacy_changes"], [])
                versions = [item for item in row["expected_legacy_changes"] if item["path"] == "version"]
                self.assertEqual([item["candidate"] for item in versions], ["10.20.4"])
                self.assertEqual(versions[0]["authority_versions"], carriers)
                assembly = [item for item in row["expected_legacy_changes"]
                            if "authoring_sequence.9." in item["path"]]
                self.assertEqual([item["path"] for item in assembly], [
                    "writing_runtime.authoring_sequence.9.run_now",
                    "runtime_plan.writing_runtime.authoring_sequence.9.run_now",
                ] if case == "cumcm_writing" else [])
                handoff = [item for item in row["expected_legacy_changes"]
                           if "authoring_sequence.4." in item["path"]]
                self.assertEqual(len(handoff), 6 if case == "cumcm_writing" else 0)
                self.assertEqual((old, new, carriers, EVIDENCE.PDF_REVIEW_WRITING_DELTAS), saved)

    def test_v10204_pdf_review_carrier_requires_exact_authority_and_unchanged_runtime(self):
        carriers = EVIDENCE.PDF_REVIEW_AUTHORITY_VERSIONS
        for case in ("facts_current", "cumcm_writing"):
            with self.subTest(case=case):
                old, new = self.pdf_review_pair(case)
                for bad in (None, {**carriers, "skill": "10.20.3"},
                            {**carriers, "skill": "10.20.5"},
                            {**carriers, "project_state": "8.17.0"},
                            {**carriers, "writing_reasoning": "1.12.0"},
                            {**carriers, "undeclared_authority": "1.0.0"},
                            {key: value for key, value in carriers.items() if key != "runtime_assurance"}):
                    self.assertEqual(EVIDENCE.approved_pdf_review_carrier_change(
                        case, old, new, bad), (new, []))
                for field, value in (("version", "10.20.3"), ("version", "10.20.5"),
                                     ("formal_delivery", True), ("pre_delivery_gates", []),
                                     ("load_order", ["scripts/render_paper.py"])):
                    altered = deepcopy(new)
                    altered[field] = value
                    self.assertEqual(EVIDENCE.approved_pdf_review_carrier_change(
                        case, old, altered, carriers), (altered, []))
                altered = deepcopy(new)
                altered["assurance"]["qualification"] = "accepted"
                self.assertEqual(EVIDENCE.approved_pdf_review_carrier_change(
                    case, old, altered, carriers), (altered, []))
        old, new = self.pdf_review_pair("facts_current")
        self.assertEqual(EVIDENCE.approved_pdf_review_carrier_change(
            "future_case", old, new, carriers), (new, []))

    def test_v10204_pdf_review_projection_pins_both_mirrors_and_stage_fields(self):
        carriers = EVIDENCE.PDF_REVIEW_AUTHORITY_VERSIONS
        for location in ("top", "nested"):
            for mutation in ("legacy_list", "reversed_list", "missing_manifest", "missing_render",
                             "extra_command", "duplicate_render", "gate", "read_now", "write_now",
                             "stage_id", "missing_stage", "stage_order", "baseline_list", "baseline_id"):
                with self.subTest(location=location, mutation=mutation):
                    old, new = self.pdf_review_pair("cumcm_writing")
                    runtime = new["writing_runtime"] if location == "top" else new["runtime_plan"]["writing_runtime"]
                    baseline = old["writing_runtime"] if location == "top" else old["runtime_plan"]["writing_runtime"]
                    stage = runtime["authoring_sequence"][9]
                    commands = stage["run_now"]
                    if mutation == "legacy_list":
                        commands.insert(1, "scripts/audit_latex_project.py")
                    elif mutation == "reversed_list":
                        commands.reverse()
                    elif mutation == "missing_manifest":
                        commands.pop(0)
                    elif mutation == "missing_render":
                        commands.pop()
                    elif mutation == "extra_command":
                        commands.append("scripts/audit_paper_prose.py")
                    elif mutation == "duplicate_render":
                        commands.append(commands[-1])
                    elif mutation == "gate":
                        stage["gate"] = "全部通过"
                    elif mutation in ("read_now", "write_now"):
                        stage[mutation] = []
                    elif mutation == "stage_id":
                        stage["id"] = "another_compile_stage"
                    elif mutation == "missing_stage":
                        runtime["authoring_sequence"].pop(9)
                    elif mutation == "stage_order":
                        runtime["authoring_sequence"][8:10] = reversed(runtime["authoring_sequence"][8:10])
                    elif mutation == "baseline_list":
                        baseline["authoring_sequence"][9]["run_now"].reverse()
                    else:
                        baseline["authoring_sequence"][9]["id"] = "another_compile_stage"
                    saved = deepcopy((old, new, carriers))
                    self.assertEqual(EVIDENCE.approved_pdf_review_carrier_change(
                        "cumcm_writing", old, new, carriers), (new, []))
                    self.assertEqual((old, new, carriers), saved)

    def stage_reading_pair(self, case):
        old, new = self.pdf_review_pair(case)
        new["version"] = "10.20.5"
        return old, new

    def test_v10205_stage_reading_carrier_projects_only_exact_protocol_versions(self):
        carriers = deepcopy(EVIDENCE.STAGE_READING_AUTHORITY_VERSIONS)
        self.assertEqual(carriers, {
            **EVIDENCE.PDF_REVIEW_AUTHORITY_VERSIONS,
            "skill": "10.20.5",
            "runtime_assurance": "2.5.1",
        })
        for case in (*sorted(EVIDENCE.A7_HYDRATED_PROVENANCE_CASES), "facts_unscoped", "cumcm_writing"):
            with self.subTest(case=case):
                old, new = self.stage_reading_pair(case)
                saved = deepcopy((old, new, carriers))
                row = EVIDENCE.compare(
                    [{"id": case, "plan": old, "legacy_declared_bytes": 1}],
                    [{"id": case, "plan": new, "legacy_declared_bytes": 1,
                      "authority_versions": carriers}],
                )[0]
                self.assertFalse(row["legacy_behavior_equal"])
                self.assertTrue(row["legacy_behavior_equal_except_approved_changes"])
                self.assertEqual(row["unexpected_legacy_changes"], [])
                version_changes = [
                    item for item in row["expected_legacy_changes"]
                    if item["path"] == "version" and item["candidate"] == "10.20.5"
                ]
                self.assertEqual(len(version_changes), 1)
                self.assertEqual(version_changes[0]["authority_versions"], carriers)
                assembly = [
                    item for item in row["expected_legacy_changes"]
                    if "authoring_sequence.9." in item["path"]
                ]
                self.assertEqual(len(assembly), 2 if case == "cumcm_writing" else 0)
                self.assertEqual((old, new, carriers), saved)

    def test_v10205_stage_reading_carrier_rejects_unregistered_versions_and_behavior(self):
        carriers = EVIDENCE.STAGE_READING_AUTHORITY_VERSIONS
        old, new = self.stage_reading_pair("facts_current")
        for bad in (
            None,
            {**carriers, "skill": "10.20.4"},
            {**carriers, "runtime_assurance": "2.5.0"},
            {**carriers, "project_state": "8.17.0"},
            {key: value for key, value in carriers.items() if key != "runtime_assurance"},
        ):
            self.assertEqual(
                EVIDENCE.approved_stage_reading_carrier_change("facts_current", old, new, bad),
                (new, []),
            )
        for field, value in (
            ("version", "10.20.4"),
            ("pre_delivery_gates", []),
            ("load_order", ["scripts/render_paper.py"]),
        ):
            altered = deepcopy(new)
            altered[field] = value
            self.assertEqual(
                EVIDENCE.approved_stage_reading_carrier_change(
                    "facts_current", old, altered, carriers
                ),
                (altered, []),
            )
        altered = deepcopy(new)
        altered["assurance"]["qualification"] = "accepted"
        self.assertEqual(
            EVIDENCE.approved_stage_reading_carrier_change(
                "facts_current", old, altered, carriers
            ),
            (altered, []),
        )

    def comparison_writing_pair(self):
        old, new = self.pair("cumcm_writing")
        new.pop("solver_backend")
        new["runtime_plan"].pop("solver_backend")
        self.prepare_b2c(old, new)
        new["version"] = "10.18.0"
        new["assurance"]["schema_version"] = "2.5.0"
        golden = yaml.safe_load((EVIDENCE.HERE.parent / "fixtures/phase_g_cumcm_runtime_golden.yaml").read_text(encoding="utf-8"))
        writing = golden["routes"]["latex"]["writing_runtime"]
        for plan in (old, new):
            plan["writing_runtime"] = deepcopy(writing)
            plan["runtime_plan"]["writing_runtime"] = deepcopy(writing)
        for runtime in (new["writing_runtime"], new["runtime_plan"]["writing_runtime"]):
            runtime["fallback_triggers"].insert(-1, EVIDENCE.COMPARISON_WRITING_TRIGGER)
        return old, new

    def test_comparison_cumcm_declared_trigger_projects_only_two_exact_leaf_lists(self):
        old, new = self.comparison_writing_pair()
        saved = deepcopy((old, new))
        projected, changes = EVIDENCE.approved_comparison_carrier_change(
            "cumcm_writing", old, new, EVIDENCE.COMPARISON_AUTHORITY_VERSIONS)
        self.assertEqual(projected, old)
        declarations = [item for item in changes if item["path"].endswith("fallback_triggers")]
        self.assertEqual([item["path"] for item in declarations], [
            "writing_runtime.fallback_triggers", "runtime_plan.writing_runtime.fallback_triggers"])
        self.assertTrue(all(item["baseline"] == old["writing_runtime"]["fallback_triggers"]
                            and item["candidate"] == new["writing_runtime"]["fallback_triggers"]
                            for item in declarations))
        self.assertFalse(new["writing_runtime"]["full_reasoning_authority_preloaded"])
        self.assertEqual((old, new), saved)
        new["reading_plan"] = {"metrics": {"planned_skill_read_bytes": 1, "planned_project_read_bytes": 0},
                               "profile": "progressive_writing", "status": "delegated"}
        row = EVIDENCE.compare(
            [{"id": "cumcm_writing", "plan": old, "legacy_declared_bytes": 1}],
            [{"id": "cumcm_writing", "plan": new, "legacy_declared_bytes": 1,
              "authority_versions": EVIDENCE.COMPARISON_AUTHORITY_VERSIONS}])[0]
        self.assertTrue(row["legacy_behavior_equal_except_approved_changes"])
        self.assertEqual(row["unexpected_legacy_changes"], [])

    def test_comparison_cumcm_trigger_does_not_waive_other_lists_or_runtime_decisions(self):
        carriers = EVIDENCE.COMPARISON_AUTHORITY_VERSIONS
        for location in ("top", "nested"):
            for mutation in ("extra", "duplicate", "missing", "order", "preloaded", "stage"):
                with self.subTest(location=location, mutation=mutation):
                    old, new = self.comparison_writing_pair()
                    runtime = new["writing_runtime"] if location == "top" else new["runtime_plan"]["writing_runtime"]
                    triggers = runtime["fallback_triggers"]
                    if mutation == "extra":
                        triggers.insert(-1, "unapproved_fallback_reason")
                    elif mutation == "duplicate":
                        triggers.insert(-1, EVIDENCE.COMPARISON_WRITING_TRIGGER)
                    elif mutation == "missing":
                        triggers.remove(EVIDENCE.COMPARISON_WRITING_TRIGGER)
                    elif mutation == "order":
                        triggers.reverse()
                    elif mutation == "preloaded":
                        runtime["full_reasoning_authority_preloaded"] = True
                    else:
                        runtime["authoring_sequence"][0]["read_now"].append("scripts/analysis_comparison.py")
                    self.assertEqual(EVIDENCE.approved_comparison_carrier_change(
                        "cumcm_writing", old, new, carriers), (new, []))
        for field, value in (("pre_delivery_gates", []), ("load_order", []), ("formal_delivery", True)):
            old, new = self.comparison_writing_pair()
            new[field] = value
            self.assertEqual(EVIDENCE.approved_comparison_carrier_change(
                "cumcm_writing", old, new, carriers), (new, []))
        old, new = self.comparison_writing_pair()
        new["assurance"]["qualification"] = "accepted"
        self.assertEqual(EVIDENCE.approved_comparison_carrier_change(
            "cumcm_writing", old, new, carriers), (new, []))
        old, new = self.comparison_writing_pair()
        for case in ("facts_current", "future_case"):
            self.assertEqual(EVIDENCE.approved_comparison_carrier_change(case, old, new, carriers), (new, []))
        self.assertEqual(EVIDENCE.approved_comparison_carrier_change(
            "cumcm_writing", old, new, {**carriers, "writing_reasoning": "1.11.1"}), (new, []))
        old, new = self.comparison_writing_pair()
        old["writing_runtime"]["fallback_triggers"].reverse()
        self.assertEqual(EVIDENCE.approved_comparison_carrier_change(
            "cumcm_writing", old, new, carriers), (new, []))
        old, new = self.comparison_writing_pair()
        del new["runtime_plan"]["writing_runtime"]["fallback_triggers"]
        self.assertEqual(EVIDENCE.approved_comparison_carrier_change(
            "cumcm_writing", old, new, carriers), (new, []))

    def test_d2_exact_carrier_preserves_d1_history_and_blocks_default_behavior_drift(self):
        carriers = deepcopy(EVIDENCE.D2_AUTHORITY_VERSIONS)
        self.assertEqual(carriers, {**EVIDENCE.D1_AUTHORITY_VERSIONS,
                                   "skill": "10.17.0", "project_state": "8.15.0"})
        for case in (*EVIDENCE.A7_HYDRATED_PROVENANCE_CASES, "facts_unscoped"):
            with self.subTest(case=case):
                old, new = self.pair(case)
                self.prepare_b2c(old, new)
                new["version"] = "10.17.0"
                original = deepcopy(new)
                projected, changes = EVIDENCE.approved_d2_carrier_change(case, old, new, carriers)
                self.assertEqual(projected, old)
                self.assertEqual(new, original)
                self.assertEqual([c["candidate"] for c in changes if c["path"] == "version"], ["10.17.0"])
                for bad in ({**carriers, "project_state": "8.16.0"},
                            {**carriers, "case_memory_retrieval": "1.0.0"},
                            {k: v for k, v in carriers.items() if k != "project_state"}):
                    self.assertEqual(EVIDENCE.approved_d2_carrier_change(case, old, new, bad), (new, []))
                for field, value in (("load_order", ["knowledge/case_memory/index.json"]),
                                     ("pre_delivery_gates", []), ("version", "10.17.1")):
                    changed = deepcopy(new)
                    changed[field] = value
                    self.assertEqual(EVIDENCE.approved_d2_carrier_change(case, old, changed, carriers), (changed, []))
                changed = deepcopy(new)
                changed["assurance"]["qualification"] = "accepted"
                self.assertEqual(EVIDENCE.approved_d2_carrier_change(case, old, changed, carriers), (changed, []))

    def test_d1_full_comparison_requires_metadata_and_rejects_new_runtime_behavior(self):
        old, new = self.pair()
        self.prepare_b2c(old, new)
        new["version"] = "10.16.0"
        for plan in (old, new):
            plan["reading_plan"] = {
                "metrics": {"planned_skill_read_bytes": 1, "planned_project_read_bytes": 0},
                "profile": "test", "status": "planned",
            }
        before = {"id": "facts_current", "plan": old, "legacy_declared_bytes": 1}
        after = {"id": "facts_current", "plan": new, "legacy_declared_bytes": 1}
        missing = EVIDENCE.compare([before], [after])[0]
        self.assertFalse(missing["legacy_behavior_equal_except_approved_changes"])
        self.assertIn("version", missing["unexpected_legacy_changes"])
        after["authority_versions"] = deepcopy(EVIDENCE.D1_AUTHORITY_VERSIONS)
        accepted = EVIDENCE.compare([before], [after])[0]
        self.assertTrue(accepted["legacy_behavior_equal_except_approved_changes"])
        self.assertEqual(accepted["unexpected_legacy_changes"], [])
        for field, value in (
            ("pre_delivery_gates", []),
            ("load_order", ["knowledge/case_memory/schema.yaml"]),
        ):
            with self.subTest(field=field):
                changed = deepcopy(after)
                changed["plan"][field] = value
                rejected = EVIDENCE.compare([before], [changed])[0]
                self.assertFalse(rejected["legacy_behavior_equal_except_approved_changes"])
                self.assertIn(field, rejected["unexpected_legacy_changes"])

    def test_b2c_carrier_keeps_unrelated_differences_visible(self):
        old, new = self.pair()
        self.prepare_b2c(old, new)
        new["pre_delivery_gates"] = []
        projected, _ = EVIDENCE.approved_b2c_carrier_change(
            "facts_current", old, new, deepcopy(EVIDENCE.B2C_AUTHORITY_VERSIONS)
        )
        self.assertEqual(projected["pre_delivery_gates"], [])

    def test_b2c_carrier_composes_with_registered_solver_fingerprint_sources(self):
        old, new = self.pair()
        self.prepare_b2c(old, new)
        solver_sources = [
            {"path": path, "sha256": f"bound-{index}"}
            for index, path in enumerate((
                "core/user_execution_contract.yaml",
                "core/output_contract.yaml",
                "core/code_quality_contract.yaml",
            ))
        ]
        new["assurance"]["authority_fingerprint"]["sources"].extend(solver_sources)
        projected, changes = EVIDENCE.approved_b2c_carrier_change(
            "facts_current", old, new, deepcopy(EVIDENCE.B2C_AUTHORITY_VERSIONS)
        )
        self.assertEqual(projected, old)
        source_changes = [
            item for item in changes
            if item["path"] == "assurance.authority_fingerprint.sources"
        ]
        self.assertEqual(len(source_changes), 2)
        self.assertEqual(source_changes[-1]["baseline"], solver_sources)

    def test_b2c_carrier_keeps_unknown_fingerprint_source_visible(self):
        old, new = self.pair()
        self.prepare_b2c(old, new)
        new["assurance"]["authority_fingerprint"]["sources"].append(
            {"path": "core/unregistered.yaml", "sha256": "unknown"}
        )
        projected, changes = EVIDENCE.approved_b2c_carrier_change(
            "facts_current", old, new, deepcopy(EVIDENCE.B2C_AUTHORITY_VERSIONS)
        )
        self.assertEqual(projected, new)
        self.assertEqual(changes, [])

    def test_b2c_carrier_rejects_unknown_case_skill_or_authority_version(self):
        mutations = [
            ("future_case", "10.13.0", None),
            ("facts_current", "10.13.1", None),
            ("facts_current", "10.13.0", ("project_state", "8.12.1")),
            ("facts_current", "10.13.0", ("claim_consumption", "1.8.1")),
            ("facts_current", "10.13.0", ("state_transition", "1.6.1")),
            ("facts_current", "10.13.0", ("writing_reasoning", "1.10.1")),
            ("facts_current", "10.13.0", ("runtime_assurance", "2.4.1")),
        ]
        for case, version, authority_mutation in mutations:
            with self.subTest(case=case, version=version, mutation=authority_mutation):
                old, new = self.pair()
                self.prepare_b2c(old, new)
                new["version"] = version
                carriers = deepcopy(EVIDENCE.B2C_AUTHORITY_VERSIONS)
                if authority_mutation:
                    carriers[authority_mutation[0]] = authority_mutation[1]
                projected, changes = EVIDENCE.approved_b2c_carrier_change(
                    case, old, new, carriers
                )
                self.assertEqual(projected, new)
                self.assertEqual(changes, [])

    def test_b2c_compare_requires_authority_metadata_and_accepts_exact_set(self):
        old, new = self.pair()
        self.prepare_b2c(old, new)
        old["assurance"]["authority_fingerprint"]["sha256"] = "same"
        new["assurance"]["authority_fingerprint"]["sha256"] = "same"
        for plan in (old, new):
            plan["reading_plan"] = {
                "metrics": {"planned_skill_read_bytes": 1, "planned_project_read_bytes": 0},
                "profile": "test", "status": "planned",
            }
        before = {"id": "facts_current", "plan": old, "legacy_declared_bytes": 1}
        after = {"id": "facts_current", "plan": new, "legacy_declared_bytes": 1}
        missing = EVIDENCE.compare([before], [after])[0]
        self.assertFalse(missing["legacy_behavior_equal_except_approved_changes"])
        self.assertIn("version", missing["unexpected_legacy_changes"])

        after["authority_versions"] = deepcopy(EVIDENCE.B2C_AUTHORITY_VERSIONS)
        accepted = EVIDENCE.compare([before], [after])[0]
        self.assertTrue(accepted["legacy_behavior_equal_except_approved_changes"])
        self.assertEqual(accepted["unexpected_legacy_changes"], [])
        self.assertEqual(accepted["candidate_authority_versions"],
                         EVIDENCE.B2C_AUTHORITY_VERSIONS)


if __name__ == "__main__":
    unittest.main()
