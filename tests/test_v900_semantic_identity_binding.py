from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def load_module(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {relative}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SEMANTIC = load_module("semantic_identity_v900_binding", "scripts/semantic_identity.py")
APPROVAL = load_module("validate_model_approval_v900_binding", "scripts/validate_model_approval.py")
RUNTIME = load_module("runtime_assurance_v900_binding", "scripts/runtime_assurance.py")


def identity() -> dict:
    return {
        "schema_version": "1.0.0",
        "question": "Q1",
        "research_object": "城市配送车辆调度",
        "data_scope": [{"id": "D1", "source": "附件1", "role": "输入"}],
        "variables": [
            {"id": "V1", "symbol": "x_i", "role": "decision", "domain": "binary"},
        ],
        "parameters": [{"id": "P1", "symbol": "c_i", "unit": "CNY"}],
        "assumptions": [{"id": "A1", "statement": "需求在决策周期内保持给定"}],
        "objective": {"sense": "minimize", "expression": "C(x)"},
        "constraints": [{"id": "C1", "expression": "x_i in {0,1}"}],
        "preprocessing_decision": "question_local",
        "algorithm_semantics": {"model_family": "MILP", "solver_role": "exact_or_gap_bounded"},
        "dependencies": [],
    }


def framework(payload: dict, *, prose: str = "当前说明文字。") -> str:
    yaml_text = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    return (
        "# 模型论文框架\n\n"
        "### Q1：第一问\n"
        "#### 当前模型口径\n"
        "<!-- HSK_SEMANTIC_IDENTITY_BEGIN Q1 -->\n"
        "```yaml\n"
        f"{yaml_text}"
        "```\n"
        "<!-- HSK_SEMANTIC_IDENTITY_END Q1 -->\n\n"
        f"{prose}\n"
        "#### 结果摘要\n"
        "待求解。\n"
    )


def legacy_framework() -> str:
    return (
        "# 模型论文框架\n\n"
        "### Q1：第一问\n"
        "#### 当前模型口径\n"
        "- 目标：min f(x)\n"
        "- 约束：x >= 0\n"
        "#### 结果摘要\n"
        "历史结果。\n"
    )


def structured_question(payload: dict | None = None) -> dict:
    payload = payload or identity()
    digest = SEMANTIC.semantic_identity_hash(payload)
    inspected = SEMANTIC.inspect_question_semantics(
        SEMANTIC.question_sections(framework(payload))["Q1"], "Q1"
    )
    return {
        "model_challenge_status": "passed",
        "human_model_approval_status": "approved",
        "semantic_revision": 3,
        "approved_semantic_revision": 3,
        "semantic_identity_schema_version": "1.0.0",
        "semantic_identity_hash": digest,
        "validated_semantic_identity_hash": digest,
        "approved_semantic_identity_hash": digest,
        "semantic_text_hash": inspected["semantic_text_hash"],
    }


def write_project(root: Path, *, state_question: dict, framework_text: str) -> None:
    (root / "state").mkdir(parents=True, exist_ok=True)
    state = {
        "project": {"competition": "CUMCM", "problem": "A", "current_phase": "solve_validate"},
        "preprocessing": {"decision": "not_needed", "status": "not_applicable"},
        "subproblems": {"Q1": state_question},
    }
    (root / "state" / "project_state.yaml").write_text(
        yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    (root / "模型论文框架.md").write_text(framework_text, encoding="utf-8")


def locked_row(hydration: dict) -> dict:
    return next(
        item
        for item in hydration["artifact_evidence"]
        if item["artifact"] == "locked_model_spec" and item["scope"] == "Q1"
    )


class StructuredApprovalTests(unittest.TestCase):
    def test_current_validated_and_approved_identity_passes(self):
        errors = APPROVAL.validate_question("Q1", structured_question())
        self.assertEqual(errors, [])

    def test_partial_structured_state_never_falls_back_to_legacy(self):
        digest = "a" * 64
        spec = {
            "model_challenge_status": "passed",
            "human_model_approval_status": "approved",
            "semantic_revision": 2,
            "approved_semantic_revision": 2,
            "semantic_identity_hash": digest,
            "semantic_hash": digest,
            "approved_semantic_hash": digest,
        }
        errors = APPROVAL.validate_question("Q1", spec)
        self.assertTrue(any("semantic_identity_schema_version" in item for item in errors))
        self.assertTrue(any("validated_semantic_identity_hash" in item for item in errors))
        self.assertTrue(any("approved_semantic_identity_hash" in item for item in errors))
        self.assertFalse(any("legacy semantic_hash approval is read-only" in item for item in errors))

    def test_legacy_approval_is_readable_but_pre_code_gate_requires_migration(self):
        digest = "b" * 64
        spec = {
            "model_challenge_status": "passed",
            "human_model_approval_status": "approved",
            "semantic_revision": 2,
            "approved_semantic_revision": 2,
            "semantic_hash": digest,
            "approved_semantic_hash": digest,
        }
        errors = APPROVAL.validate_question("Q1", spec)
        self.assertTrue(any("read-only compatibility" in item for item in errors))
        self.assertEqual(
            APPROVAL.validate_question("Q1", spec, allow_legacy_read_only=True),
            [],
        )


class RuntimeIdentityEvidenceTests(unittest.TestCase):
    def test_structured_chain_verifies_current_framework_identity(self):
        payload = identity()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root, state_question=structured_question(payload), framework_text=framework(payload))
            hydration = RUNTIME.hydrate_project_context(root, "Q1")
        row = locked_row(hydration)
        expected = SEMANTIC.semantic_identity_hash(payload)
        self.assertEqual(row["status"], "verified")
        self.assertEqual(row["identity_mode"], "semantic_identity_v1")
        self.assertEqual(row["identity_schema_version"], "1.0.0")
        self.assertEqual(row["expected_sha256"], expected)
        self.assertEqual(row["actual_sha256"], expected)
        self.assertIn("locked_model_spec", hydration["verified_artifacts"])

    def test_wording_only_change_does_not_invalidate_structured_lock(self):
        payload = identity()
        first = framework(payload, prose="模型以总成本最小为目标。")
        second = framework(payload, prose="这里换一种说明措辞，但数学身份不变。")
        first_semantics = SEMANTIC.inspect_question_semantics(
            SEMANTIC.question_sections(first)["Q1"], "Q1"
        )
        second_semantics = SEMANTIC.inspect_question_semantics(
            SEMANTIC.question_sections(second)["Q1"], "Q1"
        )
        self.assertEqual(
            first_semantics["semantic_identity_hash"],
            second_semantics["semantic_identity_hash"],
        )
        self.assertNotEqual(
            first_semantics["semantic_text_hash"], second_semantics["semantic_text_hash"]
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root, state_question=structured_question(payload), framework_text=second)
            row = locked_row(RUNTIME.hydrate_project_context(root, "Q1"))
        self.assertEqual(row["status"], "verified")

    def test_framework_identity_drift_is_stale_even_when_state_self_matches(self):
        approved = identity()
        changed = deepcopy(approved)
        changed["objective"]["sense"] = "maximize"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root, state_question=structured_question(approved), framework_text=framework(changed))
            hydration = RUNTIME.hydrate_project_context(root, "Q1")
        row = locked_row(hydration)
        self.assertEqual(row["status"], "stale")
        self.assertNotEqual(row["expected_sha256"], row["actual_sha256"])
        self.assertNotIn("locked_model_spec", hydration["verified_artifacts"])

    def test_malformed_sib_fails_closed(self):
        malformed = framework(identity()).replace(
            "<!-- HSK_SEMANTIC_IDENTITY_END Q1 -->", "<!-- missing end marker -->"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root, state_question=structured_question(), framework_text=malformed)
            hydration = RUNTIME.hydrate_project_context(root, "Q1")
        row = locked_row(hydration)
        self.assertEqual(row["status"], "malformed")
        self.assertNotIn("locked_model_spec", hydration["verified_artifacts"])

    def test_legacy_lock_is_review_required_not_verified(self):
        text = legacy_framework()
        section = SEMANTIC.question_sections(text)["Q1"]
        digest = SEMANTIC.inspect_question_semantics(section, "Q1")["semantic_text_hash"]
        legacy = {
            "model_challenge_status": "passed",
            "human_model_approval_status": "approved",
            "semantic_revision": 2,
            "approved_semantic_revision": 2,
            "semantic_hash": digest,
            "approved_semantic_hash": digest,
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_project(root, state_question=legacy, framework_text=text)
            hydration = RUNTIME.hydrate_project_context(root, "Q1")
        row = locked_row(hydration)
        self.assertEqual(row["status"], "legacy_review_required")
        self.assertEqual(row["expected_sha256"], digest)
        self.assertEqual(row["actual_sha256"], digest)
        self.assertNotIn("locked_model_spec", hydration["verified_artifacts"])


class PhaseCPlanSurfaceTests(unittest.TestCase):
    def test_framework_template_has_inert_sib_slot_not_fake_live_identity(self):
        text = (ROOT / "templates/model/model_paper_framework.md").read_text(encoding="utf-8")
        self.assertIn("Semantic Identity Block", text)
        self.assertIn("SIB SLOT", text)
        self.assertIn("Approved semantic identity hash", text)
        self.assertNotIn("HSK_SEMANTIC_IDENTITY_BEGIN", text)
        self.assertNotIn("HSK_SEMANTIC_IDENTITY_END", text)

    def test_model_design_documents_structured_binding_and_legacy_migration(self):
        text = (ROOT / "modules/02_model_design.md").read_text(encoding="utf-8")
        self.assertIn("approved_semantic_identity_hash", text)
        self.assertIn("semantic_identity_hash", text)
        self.assertIn("SIB", text)
        self.assertIn("只读", text)
        self.assertIn("不得根据旧 prose", text)


if __name__ == "__main__":
    unittest.main()
