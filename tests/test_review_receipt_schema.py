"""C1 receipt shape and additive Project State compatibility."""
from copy import deepcopy
from pathlib import Path
import unittest

import yaml
from jsonschema import Draft202012Validator

from tests.claim_schema_reference import previous_c1_schema


ROOT = Path(__file__).resolve().parents[1]
DIGEST = "a" * 64


def receipt():
    return {
        "review_id": "R1", "gate": "model_challenge", "role": "positive_fitness_review",
        "criteria_version": "1.1.0",
        "scope": {"questions": ["Q1"], "object_ids": ["model:Q1"]},
        "snapshot": {
            "state_generation": 1,
            "state_fields": [{"pointer": "/subproblems/Q1/semantic_identity_hash", "sha256": DIGEST}],
            "project_files": [],
            "authorities": [{"path": "core/model_approval_contract.yaml", "sha256": DIGEST}],
            "fingerprint_sha256": DIGEST,
        },
        "execution": {"method": "separated_passes", "source_kind": "self_declared", "pass_id": "pass-1"},
        "checks": [{"id": "contract_fit", "object_ids": ["model:Q1"],
                    "result": "pass", "evidence_locator": "模型论文框架.md#Q1"}],
        "findings": [], "uncovered": [], "verdict": "pass",
    }


class ReviewReceiptSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        cls.example = yaml.safe_load((ROOT / "state/project_state.example.yaml").read_text(encoding="utf-8"))
        cls.validator = Draft202012Validator(cls.schema)

    def candidate(self, record=None):
        state = deepcopy(self.example)
        state["review_receipts"] = {"protocol_version": "1.0.0", "records": [record or receipt()]}
        return state

    def test_closed_optional_record_and_historical_projection(self):
        Draft202012Validator.check_schema(self.schema)
        self.assertEqual(self.schema["version"], "8.15.0")
        self.assertFalse(list(self.validator.iter_errors(self.example)))
        self.assertFalse(list(self.validator.iter_errors(self.candidate())))
        empty = self.candidate()
        empty["review_receipts"]["records"] = []
        self.assertFalse(list(self.validator.iter_errors(empty)))
        self.assertEqual(previous_c1_schema(self.schema)["version"], "8.12.0")

    def test_partial_unknown_and_self_referential_records_rejected(self):
        bad = []
        candidate = self.candidate()
        candidate["review_receipts"]["protocol_version"] = "2.0.0"
        bad.append(candidate)
        candidate = self.candidate()
        candidate["review_receipts"]["records"][0].pop("criteria_version")
        bad.append(candidate)
        candidate = self.candidate()
        candidate["review_receipts"]["records"][0]["independent"] = True
        bad.append(candidate)
        candidate = self.candidate()
        candidate["review_receipts"]["records"][0]["checks"] = []
        bad.append(candidate)
        candidate = self.candidate()
        candidate["review_receipts"]["records"][0]["snapshot"]["state_fields"] = []
        bad.append(candidate)
        for pointer in ("", "/review_receipts", "/review_receipts/records/0",
                        "/project/state_generation"):
            candidate = self.candidate()
            candidate["review_receipts"]["records"][0]["snapshot"]["state_fields"][0]["pointer"] = pointer
            bad.append(candidate)
        candidate = self.candidate()
        candidate["review_receipts"]["records"][0]["execution"]["method"] = "independent"
        bad.append(candidate)
        candidate = self.candidate()
        candidate["review_receipts"]["records"][0]["execution"]["exit_code"] = True
        bad.append(candidate)
        candidate = self.candidate()
        candidate["review_receipts"]["records"][0]["snapshot"]["authorities"][0]["path"] = "../outside"
        bad.append(candidate)
        for state in bad:
            with self.subTest(record=state["review_receipts"]):
                self.assertTrue(list(self.validator.iter_errors(state)))


if __name__ == "__main__":
    unittest.main()
