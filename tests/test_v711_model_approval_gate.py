from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from tests.test_v900_semantic_governance import framework, identity_payload

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {relative}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_validator():
    return load_module("validate_model_approval", "scripts/validate_model_approval.py")


def load_semantic_governance():
    return load_module("validate_semantic_governance_v711", "scripts/validate_semantic_governance.py")


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

    def test_contract_interprets_legacy_route_fields_with_v930_minimal_sufficient_semantics(self):
        contract = yaml.safe_load((ROOT / "core" / "model_approval_contract.yaml").read_text(encoding="utf-8"))
        semantics = contract["model_challenge"]["check_semantics"]
        self.assertIn("minimal-sufficient main model", semantics["route_selection_fit"])
        self.assertIn("Condition -> Consequence", semantics["route_selection_fit"])
        self.assertIn("before solver selection", semantics["structure_before_algorithm"])
        self.assertIn("minimal-sufficiency check", semantics["simpler_baseline_may_be_sufficient"])

        fields = contract["human_approval"]["approval_brief_fields"]
        self.assertIn("structural_simplification", fields)
        self.assertIn("rejected_route_reason", fields)
        field_semantics = contract["human_approval"]["approval_brief_field_semantics"]
        self.assertIn("minimal-sufficiency rationale", field_semantics["structural_simplification"])
        self.assertIn("may be not_applicable", field_semantics["rejected_route_reason"])
        self.assertIn("fixed two-route comparison", field_semantics["rejected_route_reason"])

    def test_solve_module_requires_model_approval_validator(self):
        text = (ROOT / "modules" / "03_solve_validate.md").read_text(encoding="utf-8")
        self.assertIn("scripts/validate_model_approval.py", text)
        self.assertIn("core/model_approval_contract.yaml", text)
        self.assertIn("不复制第二套检查清单", text)
        self.assertIn("awaiting_model_approval", text)
        self.assertNotIn("model_challenge_status=passed", text)
        self.assertNotIn("human_model_approval_status=approved", text)

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

    def write_state(self, subproblem: dict, *, review_receipt_policy: dict | None = None,
                    project_root: Path | None = None) -> Path:
        state = {"subproblems": {"Q1": subproblem}}
        if review_receipt_policy is not None:
            state["review_receipt_policy"] = review_receipt_policy
        if project_root is not None:
            path = project_root / "state/project_state.yaml"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
            return path
        temp = tempfile.NamedTemporaryFile("w", suffix=".yaml", encoding="utf-8", delete=False)
        with temp:
            yaml.safe_dump(state, temp, allow_unicode=True, sort_keys=False)
        return Path(temp.name)

    def current_structured_model(self, *, approval: str = "approved") -> dict:
        return {
            "model_challenge_status": "passed",
            "human_model_approval_status": approval,
            "semantic_revision": 3,
            "approved_semantic_revision": 3,
            "semantic_identity_schema_version": "1.0.0",
            "semantic_identity_hash": self.hash_value,
            "validated_semantic_identity_hash": self.hash_value,
            "approved_semantic_identity_hash": self.hash_value,
        }

    @staticmethod
    def active_model_receipt_policy() -> dict:
        return {
            "protocol_version": "1.0.0", "mode": "enforce_scoped", "requirements": [
                {"gate": "model_challenge", "questions": ["Q1"], "object_ids": ["Q1:model"],
                 "roles": [
                     {"role": "positive_fitness_review", "check_ids": ["problem_contract_fit"]},
                     {"role": "adversarial_model_challenge", "check_ids": ["alternative_problem_interpretation"]},
                 ]},
            ],
        }

    def test_approved_matching_legacy_revision_and_hash_is_read_only_compatible(self):
        path = self.write_state({
            "model_challenge_status": "passed",
            "human_model_approval_status": "approved",
            "semantic_revision": 3,
            "approved_semantic_revision": 3,
            "semantic_hash": self.hash_value,
            "approved_semantic_hash": self.hash_value,
        })
        try:
            errors = self.validator.validate_state(path, ["Q1"])
            self.assertTrue(any("read-only compatibility" in item for item in errors))
            self.assertEqual(
                self.validator.validate_state(path, ["Q1"], allow_legacy_read_only=True),
                [],
            )
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

    def test_c12_receipt_pass_cannot_replace_pending_human_approval(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = self.write_state(
                self.current_structured_model(approval="pending"),
                review_receipt_policy=self.active_model_receipt_policy(), project_root=root,
            )
            receipt_pass = {"status": "passed", "issues": [],
                            "qualification": "scoped_receipt_eligible"}
            with patch.object(self.validator, "_evaluate_model_receipts", return_value=receipt_pass) as evaluate:
                errors = self.validator.validate_state(path, ["Q1"], project_root=root)
            evaluate.assert_called_once_with(root.resolve(), "Q1")
            self.assertTrue(any("human_model_approval_status" in issue for issue in errors), errors)
            self.assertFalse(any("review receipt" in issue for issue in errors), errors)

    def test_c12_active_receipt_failure_blocks_otherwise_approved_model(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = self.write_state(
                self.current_structured_model(),
                review_receipt_policy=self.active_model_receipt_policy(), project_root=root,
            )
            receipt_fail = {"status": "failed", "issues": ["missing second review pass"],
                            "qualification": "not_granted"}
            with patch.object(self.validator, "_evaluate_model_receipts", return_value=receipt_fail):
                errors = self.validator.validate_state(path, ["Q1"], project_root=root)
            self.assertIn("Q1: model_challenge review receipt: missing second review pass", errors)
            self.assertFalse(any("human_model_approval_status" in issue for issue in errors), errors)

    def test_c12_explicit_state_cannot_mix_canonical_review_policy(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_state(self.current_structured_model(),
                             review_receipt_policy=self.active_model_receipt_policy(),
                             project_root=root)
            alternative = root / "alternate.yaml"
            alternative.write_text(yaml.safe_dump({"subproblems": {"Q1": self.current_structured_model()}}),
                                   encoding="utf-8")
            with patch.object(self.validator, "_evaluate_model_receipts") as evaluate:
                errors = self.validator.validate_state(alternative, ["Q1"], project_root=root)
            evaluate.assert_not_called()
            self.assertTrue(any("canonical state/project_state.yaml" in issue for issue in errors), errors)

    def test_c12_explicit_policy_state_must_be_canonical(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_state(self.current_structured_model(), project_root=root)
            alternative = root / "alternate.yaml"
            alternative.write_text(yaml.safe_dump({
                "subproblems": {"Q1": self.current_structured_model()},
                "review_receipt_policy": self.active_model_receipt_policy(),
            }), encoding="utf-8")
            with patch.object(self.validator, "_evaluate_model_receipts") as evaluate:
                errors = self.validator.validate_state(alternative, ["Q1"], project_root=root)
            evaluate.assert_not_called()
            self.assertTrue(any("canonical state/project_state.yaml" in issue for issue in errors), errors)

    def test_c12_no_policy_preserves_existing_approval_gate(self):
        path = self.write_state(self.current_structured_model())
        try:
            with patch.object(self.validator, "_evaluate_model_receipts", side_effect=AssertionError("not activated")):
                self.assertEqual(self.validator.validate_state(path, ["Q1"]), [])
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


class ModelApprovalSemanticInvalidationTests(unittest.TestCase):
    def setUp(self):
        self.semantic = load_semantic_governance()

    def test_structured_semantic_change_marks_challenge_and_human_approval_stale(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "state").mkdir()
            state_path = root / "state" / "project_state.yaml"
            state = {
                "semantic_governance_version": "1.0.0",
                "subproblems": {
                    "Q1": {
                        "status": "designed",
                        "problem_contract_status": "frozen",
                        "semantic_closure_status": "passed",
                        "complexity_sanity_status": "passed",
                        "complexity_sanity_flags": [],
                        "semantic_revision": 1,
                        "semantic_change_categories": ["initial_design"],
                        "model_challenge_status": "passed",
                        "human_model_approval_status": "approved",
                        "approved_semantic_revision": 1,
                        "result_quality_status": "passed",
                        "result_analysis_status": "passed",
                        "validation_status": "passed",
                        "result_summary_status": "current",
                        "depends_on": [],
                        "artifacts_stale": False,
                        "stale_layers": [],
                    }
                },
                "paper_framework": {"paper_fragments": [], "sync_status": "current"},
            }
            state_path.write_text(
                yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            (root / "模型论文框架.md").write_text(
                framework(identity_payload()), encoding="utf-8"
            )

            first = self.semantic.validate_project(root, write=True, strict=True)
            self.assertEqual(first["status"], "passed", first)
            state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
            q1 = state["subproblems"]["Q1"]
            old_identity = q1["semantic_identity_hash"]
            q1["approved_semantic_identity_hash"] = old_identity
            q1["approved_semantic_revision"] = 1
            q1["model_challenge_status"] = "passed"
            q1["human_model_approval_status"] = "approved"
            q1["semantic_revision"] = 2
            q1["semantic_change_categories"] = ["objective"]
            state_path.write_text(
                yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            (root / "模型论文框架.md").write_text(
                framework(identity_payload(objective_expression="sum_i (c_i + 1) * x_i")),
                encoding="utf-8",
            )

            report = self.semantic.validate_project(root, write=True, strict=True)
            self.assertEqual(report["status"], "passed", report)
            self.assertEqual(report["changed_sources"], ["Q1"])

            updated = yaml.safe_load(state_path.read_text(encoding="utf-8"))
            q1 = updated["subproblems"]["Q1"]
            self.assertEqual(q1["model_challenge_status"], "stale")
            self.assertEqual(q1["human_model_approval_status"], "stale")
            self.assertEqual(q1["approved_semantic_revision"], 1)
            self.assertEqual(q1["approved_semantic_identity_hash"], old_identity)
            self.assertNotEqual(q1["semantic_identity_hash"], old_identity)
            self.assertIn("primary_code", q1["stale_layers"])
            self.assertTrue(q1["artifacts_stale"])

    def test_old_project_without_approval_fields_is_not_backfilled(self):
        entry = {
            "result_quality_status": "passed",
            "result_analysis_status": "passed",
            "validation_status": "passed",
            "result_summary_status": "current",
        }
        self.semantic._mark_stale(entry)
        self.assertNotIn("model_challenge_status", entry)
        self.assertNotIn("human_model_approval_status", entry)
        self.assertIn("primary_code", entry["stale_layers"])


if __name__ == "__main__":
    unittest.main()
