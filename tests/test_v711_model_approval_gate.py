from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_validator():
    path = ROOT / "scripts" / "validate_model_approval.py"
    spec = importlib.util.spec_from_file_location("validate_model_approval", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load validate_model_approval.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ModelApprovalContractTests(unittest.TestCase):
    def test_contract_defines_two_independent_passes_and_explicit_approval(self):
        contract = yaml.safe_load((ROOT / "core" / "model_approval_contract.yaml").read_text(encoding="utf-8"))
        self.assertEqual(contract["states"]["pause_state"], "awaiting_model_approval")
        self.assertEqual(contract["model_challenge"]["principle"], "independent_two_pass_review")
        self.assertIn("reviewer_pass", contract["model_challenge"])
        self.assertIn("devils_advocate_pass", contract["model_challenge"])
        self.assertTrue(contract["human_approval"]["explicit_only"])
        self.assertTrue(contract["human_approval"]["silence_is_not_approval"])
        self.assertEqual(contract["lock_semantics"]["before_approval"], "proposed_model_spec")
        self.assertEqual(contract["lock_semantics"]["after_approval"], "locked_model_spec")

    def test_solve_module_requires_model_approval_validator(self):
        text = (ROOT / "modules" / "03_solve_validate.md").read_text(encoding="utf-8")
        self.assertIn("scripts/validate_model_approval.py", text)
        self.assertIn("model_challenge_status=passed", text)
        self.assertIn("human_model_approval_status=approved", text)
        self.assertIn("awaiting_model_approval", text)

    def test_model_design_distinguishes_proposed_and_locked_specs(self):
        text = (ROOT / "modules" / "02_model_design.md").read_text(encoding="utf-8")
        self.assertIn("Independent Model Challenge", text)
        self.assertIn("Devil's Advocate", text)
        self.assertIn("proposed_model_spec", text)
        self.assertIn("Human Model Approval", text)
        self.assertIn("approved_semantic_hash", text)


class ModelApprovalValidatorTests(unittest.TestCase):
    def setUp(self):
        self.validator = load_validator()
        self.hash_value = "a" * 64

    def write_state(self, subproblem: dict) -> Path:
        temp = tempfile.NamedTemporaryFile("w", suffix=".yaml", encoding="utf-8", delete=False)
        with temp:
            yaml.safe_dump({"subproblems": {"Q1": subproblem}}, temp, allow_unicode=True, sort_keys=False)
        return Path(temp.name)

    def test_approved_matching_revision_and_hash_passes(self):
        path = self.write_state({
            "model_challenge_status": "passed",
            "human_model_approval_status": "approved",
            "semantic_revision": 3,
            "approved_semantic_revision": 3,
            "semantic_hash": self.hash_value,
            "approved_semantic_hash": self.hash_value,
        })
        try:
            self.assertEqual(self.validator.validate_state(path, ["Q1"]), [])
        finally:
            path.unlink(missing_ok=True)

    def test_pending_approval_fails(self):
        path = self.write_state({
            "model_challenge_status": "passed",
            "human_model_approval_status": "pending",
            "semantic_revision": 3,
            "approved_semantic_revision": 3,
            "semantic_hash": self.hash_value,
            "approved_semantic_hash": self.hash_value,
        })
        try:
            errors = self.validator.validate_state(path, ["Q1"])
            self.assertTrue(any("human_model_approval_status" in item for item in errors))
        finally:
            path.unlink(missing_ok=True)

    def test_semantic_revision_or_hash_drift_fails(self):
        path = self.write_state({
            "model_challenge_status": "passed",
            "human_model_approval_status": "approved",
            "semantic_revision": 4,
            "approved_semantic_revision": 3,
            "semantic_hash": "b" * 64,
            "approved_semantic_hash": self.hash_value,
        })
        try:
            errors = self.validator.validate_state(path, ["Q1"])
            self.assertTrue(any("approved_semantic_revision" in item for item in errors))
            self.assertTrue(any("approved_semantic_hash" in item for item in errors))
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
