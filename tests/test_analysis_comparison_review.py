"""Scoped optional review consumption; synthetic receipts are not human review."""
from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import review_receipt_consumption as CONSUMPTION
import review_receipts as REVIEW
import test_review_receipt_consumption as fixtures


class ComparisonReviewTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.ReviewReceiptConsumptionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.state["subproblems"]["Q1"]["analysis_comparison"] = {
            "protocol_version": "1.0.0", "scope_sha256": "b" * 64,
        }
        self.fixture.save()

    def inspect(self, *, comparison=True):
        return CONSUMPTION.evaluate_gate(
            self.fixture.root, "model_challenge", questions=["Q1"],
            comparison_scope=comparison)

    def install(self, *, object_present=True, snapshot_present=True):
        fixture = self.fixture
        requirement = fixture.activate("model_challenge")
        if object_present:
            requirement["object_ids"].append("Q1:analysis_comparison")
        fixture.save()
        records = []
        for index, role_spec in enumerate(requirement["roles"]):
            record = fixture.receipt("model_challenge", role_spec, str(index + 1),
                                     requirement["object_ids"])
            if snapshot_present:
                record["snapshot"]["state_fields"].append({
                    "pointer": "/subproblems/Q1/analysis_comparison/scope_sha256",
                    "sha256": REVIEW.state_field_sha256("b" * 64),
                })
            snapshot = record["snapshot"]
            snapshot["fingerprint_sha256"] = REVIEW.snapshot_fingerprint(
                snapshot["state_fields"], snapshot["project_files"], snapshot["authorities"],
                gate=record["gate"], role=record["role"], scope=record["scope"],
                criteria_version=record["criteria_version"])
            records.append(record)
        fixture.state["review_receipts"] = {"protocol_version": "1.0.0", "records": records}
        fixture.save()

    def test_primary_receipts_do_not_authorize_comparison(self):
        self.install(object_present=False, snapshot_present=False)
        self.assertEqual(self.inspect(comparison=False)["status"], "passed")
        result = self.inspect()
        self.assertEqual(result["status"], "failed")
        self.assertTrue(any("comparison scope" in issue for issue in result["issues"]))

    def test_scope_identity_must_be_in_both_snapshots(self):
        self.install(snapshot_present=False)
        result = self.inspect()
        self.assertEqual(result["status"], "failed")
        self.assertTrue(any("outside the review snapshot" in issue for issue in result["issues"]))

    def test_current_scoped_pair_is_eligible_but_never_human_approval(self):
        self.install()
        result = self.inspect()
        self.assertEqual(result["status"], "passed", result["issues"])
        self.assertEqual(result["human_model_approval"], "not_granted")
        self.fixture.state["subproblems"]["Q1"]["analysis_comparison"]["scope_sha256"] = "c" * 64
        self.fixture.save()
        self.assertEqual(self.inspect()["status"], "failed")


if __name__ == "__main__":
    unittest.main()
