from __future__ import annotations

import json
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import optimization_baseline as BASELINE

ROOT = Path(__file__).resolve().parents[1]


class MeasurementUnitTests(unittest.TestCase):
    def test_utf8_bytes_and_deduplication_not_character_estimate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sample.md").write_bytes("中文\n".encode("utf-8"))
            rows = BASELINE.resource_rows(root, ["sample.md", "sample.md#anchor", "sample.md"])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["bytes"], 7)
        self.assertEqual(rows[0]["lines"], 1)

    def test_missing_resource_fails_not_zero_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                BASELINE.read_resource(Path(tmp), "missing.md")

    def test_resource_cannot_escape_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                BASELINE.read_resource(Path(tmp), "../outside.md")

    def test_unknown_case_fields_are_not_silently_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cases.yaml"
            path.write_text("schema_version: 1\ncases:\n- id: x\n  typo: true\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                BASELINE.load_cases(path)

    def test_duplicate_case_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cases.yaml"
            path.write_text("schema_version: 1\ncases:\n- id: x\n- id: x\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                BASELINE.load_cases(path)

    def test_comparison_rejects_changed_inputs_or_driver(self):
        source = {"cases_sha256": "a", "measurement_driver_sha256": "b", "cases": []}
        for field in ("cases_sha256", "measurement_driver_sha256"):
            changed = deepcopy(source)
            changed[field] = "different"
            with self.subTest(field=field), self.assertRaises(ValueError):
                BASELINE.compare(source, changed)

    def test_comparison_detects_behavior_and_resource_changes(self):
        source = {
            "source_commit": "test", "cases_sha256": "a", "measurement_driver_sha256": "b",
            "cases": [{"id": "x", "behavior": {"pause_state": "awaiting_model_approval"},
                       "authority_fingerprint": {"sha256": "c"},
                       "measurement": {"declared_resource_bytes": 100}}],
        }
        self.assertTrue(BASELINE.compare(source, deepcopy(source))["all_equal"])
        changed = deepcopy(source)
        changed["cases"][0]["behavior"]["pause_state"] = None
        self.assertFalse(BASELINE.compare(source, changed)["all_equal"])
        changed = deepcopy(source)
        changed["cases"][0]["measurement"]["declared_resource_bytes"] = 90
        self.assertEqual(BASELINE.compare(source, changed)["cases"][0]["declared_bytes_delta"], -10)


class AssuredResolverCharacterizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = BASELINE.collect(ROOT, BASELINE.DEFAULT_CASES)
        cls.cases = {row["id"]: row for row in cls.report["cases"]}

    def test_every_declared_case_was_measured(self):
        expected = {row["id"] for row in BASELINE.load_cases(BASELINE.DEFAULT_CASES)["cases"]}
        self.assertEqual(set(self.cases), expected)
        self.assertGreaterEqual(len(self.cases), 16)

    def test_metrics_do_not_claim_actual_read_tokens(self):
        for identifier, row in self.cases.items():
            with self.subTest(case=identifier):
                metric = row["measurement"]
                self.assertIsNone(metric["required_read_bytes"])
                self.assertIsNone(metric["actual_read_tokens"])
                self.assertIsNone(metric["repeat_read_bytes"])
                self.assertEqual(metric["declared_resource_bytes"],
                                 sum(resource["bytes"] for resource in metric["resources"]))
                self.assertGreater(metric["declared_resource_bytes"], 0)

    def test_machine_contracts_and_authority_are_not_dropped(self):
        for identifier, row in self.cases.items():
            with self.subTest(case=identifier):
                self.assertEqual(row["behavior"]["dependency_closure"]["missing_aliases"], [])
                fingerprint = row["authority_fingerprint"]
                self.assertEqual(len(fingerprint["sha256"]), 64)
                self.assertTrue(fingerprint["sources"])
                self.assertTrue(all(item["sha256"] for item in fingerprint["sources"]))

    def test_no_approval_never_crosses_user_approval_boundary(self):
        for identifier in ("full_solution_no_approval", "hydrated_unapproved", "hydrated_identity_drift", "hydrated_legacy"):
            with self.subTest(case=identifier):
                behavior = self.cases[identifier]["behavior"]
                self.assertEqual(behavior["pause_state"], "awaiting_model_approval")
                self.assertNotIn("solve_validate", behavior["modules"])

    def test_approved_and_wording_only_keep_user_execution_boundary(self):
        for identifier in ("hydrated_approved", "hydrated_wording_only"):
            with self.subTest(case=identifier):
                behavior = self.cases[identifier]["behavior"]
                self.assertEqual(behavior["pause_state"], "awaiting_user_execution")
                self.assertIn("solve_validate", behavior["modules"])
                self.assertNotIn("result_analysis", behavior["modules"])
                self.assertIn("locked_model_spec", behavior["artifact_assurance"]["effective_artifacts"])

    def test_hydrated_cases_do_not_write_to_project(self):
        for identifier, row in self.cases.items():
            if row["input"].get("project_fixture"):
                with self.subTest(case=identifier):
                    self.assertTrue(row["project_read_only"])
                    self.assertTrue(row["project_read_only_applicable"])
                    self.assertTrue(row["behavior"]["context"]["project_state_loaded"])
                    self.assertNotIn("hsk-opt-synthetic-", json.dumps(row["behavior"]))

    def test_explicit_intent_precedes_mentioned_other_tasks(self):
        self.assertEqual(self.cases["explicit_intent_precedence"]["behavior"]["intents"], ["figures"])

    def test_cumcm_progressive_writing_not_misreported_as_full_preload(self):
        row = self.cases["latex_cumcm"]
        runtime = row["behavior"]["runtime_plan"]["writing_runtime"]
        self.assertEqual(runtime["execution_mode"], "template_first_progressive_authoring")
        self.assertEqual(runtime["mode"], "compact")
        self.assertEqual(row["measurement"]["route_load_semantics"]["latex"], "resource_availability_only")


if __name__ == "__main__":
    unittest.main()
