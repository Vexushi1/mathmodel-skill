"""G1A checks; baseline P1/P2 drivers and fixtures stay untouched."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v10270_runtime_measurement as MEASURE

ROOT = Path(__file__).resolve().parents[1]


def report() -> dict:
    return {
        "schema_version": 1, "source_commit": MEASURE.BASELINE,
        "cases_sha256": "corpus", "driver_sha256": "driver",
        "cases": [{
            "id": "x", "behavior": {"intents": ["figures"], "pause_state": None},
            "source_identity": {"authority_sha256": "source-A"},
            "measurement": {"resolver_wall_seconds": 0.1, "actual_read_tokens": None},
        }],
    }


class G1ABaselineTests(unittest.TestCase):
    def test_corpus_is_distinct_and_typed(self):
        cases = MEASURE.load_cases(ROOT / "tests/fixtures/v10270_runtime_cases.yaml")
        self.assertGreaterEqual(len(cases), 6)
        self.assertEqual(len({row["id"] for row in cases}), len(cases))
        self.assertFalse(any("expected_actions" in row for row in cases))

    def test_changed_driver_and_corpus_cannot_be_compared(self):
        a = report()
        for key in ("driver_sha256", "cases_sha256"):
            b = deepcopy(a)
            b[key] = "other"
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, key):
                MEASURE.compare(a, b)

    def test_wrong_frozen_baseline_and_order_block(self):
        a = report()
        a["source_commit"] = "not-approved"
        with self.assertRaisesRegex(ValueError, "frozen"):
            MEASURE.compare(a, report())
        a = report()
        b = report()
        b["cases"][0]["id"] = "different"
        with self.assertRaisesRegex(ValueError, "order/identity"):
            MEASURE.compare(a, b)

    def test_source_sha_change_is_separately_reported(self):
        a = report()
        b = deepcopy(a)
        b["source_commit"] = "candidate"
        b["cases"][0]["source_identity"]["authority_sha256"] = "source-B"
        result = MEASURE.compare(a, b)
        self.assertEqual(result["status"], "pass")
        self.assertTrue(result["cases"][0]["source_identity_changed"])
        self.assertEqual(result["approved_delta_count"], 0)

    def test_unapproved_behavior_change_is_blocked(self):
        a = report()
        b = deepcopy(a)
        b["cases"][0]["behavior"]["pause_state"] = "awaiting_model_approval"
        result = MEASURE.compare(a, b)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["unapproved_delta_count"], 1)
        self.assertEqual(result["cases"][0]["unapproved_behavior_deltas"][0]["path"],
                         "pause_state")

    def test_exact_approval_is_not_a_wildcard(self):
        a, b = report(), report()
        b["cases"][0]["behavior"]["intents"] = ["latex"]
        allowed = [{
            "case_id": "x", "path": "intents[0]", "before": "figures", "after": "latex",
            "reason": "synthetic approved change test", "authorization": "example-only",
            "test_id": "G1A-TEST-EXACT",
        }]
        self.assertEqual(MEASURE.compare(a, b, allowed)["status"], "pass")
        mismatch = deepcopy(allowed)
        mismatch[0]["after"] = "docx"
        with self.assertRaisesRegex(ValueError, "unused or mismatched"):
            MEASURE.compare(a, b, mismatch)

    def test_approvals_require_provenance_and_reject_wildcards(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "approvals.json"
            good = {"schema_version": 1, "approved_behavior_deltas": [{
                "case_id": "x", "path": "intents[0]", "before": "figures", "after": "latex",
                "reason": "synthetic", "authorization": "synthetic-test-only",
                "test_id": "G1A-TEST",
            }]}
            p.write_text(json.dumps(good), encoding="utf-8")
            self.assertEqual(len(MEASURE.approved_changes(p)), 1)
            good["approved_behavior_deltas"][0]["path"] = "*"
            p.write_text(json.dumps(good), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "wildcard"):
                MEASURE.approved_changes(p)

    def test_no_eager_inference_from_plan_metrics(self):
        a = report()
        self.assertIsNone(a["cases"][0]["measurement"]["actual_read_tokens"])
        self.assertEqual(MEASURE.compare(a, deepcopy(a))["unapproved_delta_count"], 0)


if __name__ == "__main__":
    unittest.main()
