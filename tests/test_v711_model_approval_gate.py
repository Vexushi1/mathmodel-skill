from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml

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


class ModelApprovalSemanticInvalidationTests(unittest.TestCase):
    def setUp(self):
        self.semantic = load_semantic_governance()

    def test_semantic_change_marks_challenge_and_human_approval_stale(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "state").mkdir()

            old_scope = "#### 当前模型口径\n\n目标：旧目标"
            new_scope = "#### 当前模型口径\n\n目标：新目标"
            old_hash = self.semantic.sha256_text(old_scope)

            state = {
                "semantic_governance_version": "1.0.0",
                "subproblems": {
                    "Q1": {
                        "status": "designed",
                        "problem_contract_status": "frozen",
                        "semantic_closure_status": "passed",
                        "complexity_sanity_status": "passed",
                        "complexity_sanity_flags": [],
                        "semantic_revision": 2,
                        "validated_semantic_revision": 1,
                        "semantic_change_categories": ["objective"],
                        "semantic_hash": old_hash,
                        "validated_semantic_hash": old_hash,
                        "model_challenge_status": "passed",
                        "human_model_approval_status": "approved",
                        "approved_semantic_revision": 1,
                        "approved_semantic_hash": old_hash,
                        "result_quality_status": "passed",
                        "result_analysis_status": "passed",
                        "validation_status": "passed",
                        "result_summary_status": "current",
                        "depends_on": [],
                    }
                },
                "paper_framework": {"paper_fragments": [], "sync_status": "current"},
            }
            (root / "state" / "project_state.yaml").write_text(
                yaml.safe_dump(state, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            (root / "模型论文框架.md").write_text(
                "# 模型论文框架\n\n### Q1：测试\n\n"
                + new_scope
                + "\n\n#### 结果摘要\n\n待更新\n",
                encoding="utf-8",
            )

            report = self.semantic.validate_project(root, write=True, strict=True)
            self.assertEqual(report["status"], "passed", report)
            self.assertEqual(report["changed_sources"], ["Q1"])

            updated = yaml.safe_load((root / "state" / "project_state.yaml").read_text(encoding="utf-8"))
            q1 = updated["subproblems"]["Q1"]
            self.assertEqual(q1["model_challenge_status"], "stale")
            self.assertEqual(q1["human_model_approval_status"], "stale")
            self.assertEqual(q1["approved_semantic_revision"], 1)
            self.assertEqual(q1["approved_semantic_hash"], old_hash)
            self.assertIn("model", q1["stale_layers"])
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
        self.assertIn("model", entry["stale_layers"])


if __name__ == "__main__":
    unittest.main()
