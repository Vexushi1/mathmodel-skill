from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import question_dependency_gate as GATE
import validate_model_approval as APPROVAL
import validate_code_delivery as DELIVERY
import semantic_identity
from tests.test_question_runtime_integration import build_three_question_project
from tests.test_v900_semantic_governance import framework, identity_payload


def set_dependency(root: Path, target: str, source: str, kind: str, *,
                   selector: str | None = None) -> None:
    """Change synthetic State and current SIB together, with exact hash bindings."""
    state_path = root / "state/project_state.yaml"
    framework_path = root / "模型论文框架.md"
    state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    dependency = {"question": source, "kind": kind}
    state["subproblems"][target]["depends_on"] = [dependency]
    identity = identity_payload()
    identity["question"] = target
    identity["dependencies"] = [dict(dependency, **({"selector": selector} if selector else {}))]
    digest = semantic_identity.semantic_identity_hash(identity)
    entry = state["subproblems"][target]
    for key in ("semantic_identity_hash", "validated_semantic_identity_hash",
                "approved_semantic_identity_hash"):
        entry[key] = digest
    section = framework(identity, question=target).split("## 各问模型与结果\n", 1)[1]
    old = framework_path.read_text(encoding="utf-8")
    first = old.index(f"### {target}：第一问")
    next_head = old.find("\n### Q", first + 5)
    rewritten = old[:first] + section + (
        old[next_head + 1:] if next_head > 0 else ""
    )
    framework_path.write_text(rewritten, encoding="utf-8")
    state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")


class TypedQuestionDependencyGateTests(unittest.TestCase):
    def test_result_dependency_is_blocked_without_validated_results(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_three_question_project(root)
            result = GATE.inspect(root, "Q2")
            self.assertEqual(result["status"], "failed")
            self.assertTrue(any("Q1/result" in issue for issue in result["issues"]), result)
            self.assertEqual(result["checked_edges"][0]["kind"], "result")
            self.assertIn("模型论文框架.md", result["observed_sources"]["project"])

    def test_independent_q3_does_not_wait_for_q1_q2(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_three_question_project(root)
            result = GATE.inspect(root, "Q3")
            self.assertEqual(result["status"], "passed", result)
            self.assertEqual(result["checked_edges"], [])

    def test_model_only_edge_uses_model_lock_not_upstream_result(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_three_question_project(root)
            set_dependency(root, "Q2", "Q1", "model")
            passed = GATE.inspect(root, "Q2")
            self.assertEqual(passed["status"], "passed", passed)
            self.assertEqual(passed["checked_edges"][0]["kind"], "model")
            state_path = root / "state/project_state.yaml"
            state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
            state["subproblems"]["Q1"]["human_model_approval_status"] = "pending"
            state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
            rejected = GATE.inspect(root, "Q2")
            self.assertEqual(rejected["status"], "failed", rejected)
            self.assertTrue(any("Q1/model" in issue for issue in rejected["issues"]), rejected)

    def test_legacy_and_missing_parameter_source_are_not_silently_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_path, _ = build_three_question_project(root)
            state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
            state["subproblems"]["Q2"]["depends_on"] = ["Q1"]
            state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
            legacy = GATE.inspect(root, "Q2")
            self.assertEqual(legacy["status"], "failed", legacy)
            self.assertTrue(any("legacy" in issue for issue in legacy["issues"]))
            set_dependency(root, "Q2", "Q1", "parameter", selector="P1")
            param = GATE.inspect(root, "Q2")
            self.assertEqual(param["status"], "failed", param)
            self.assertTrue(any("parameter selector/value/source" in issue for issue in param["issues"]))

    def test_unbound_raw_data_dependency_is_not_approved_by_filenames(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_three_question_project(root)
            set_dependency(root, "Q2", "Q1", "data")
            result = GATE.inspect(root, "Q2", config={
                "data_paths": ["synthetic-input.csv"],
                "data_sha256": "0" * 64,
            })
            self.assertEqual(result["status"], "failed")
            self.assertTrue(any("Q1/data" in issue for issue in result["issues"]))

    def test_only_unresolved_upstream_cycle_blocks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_three_question_project(root)
            set_dependency(root, "Q1", "Q2", "result")
            result = GATE.inspect(root, "Q2")
            self.assertEqual(result["status"], "failed")
            self.assertTrue(any("cycle" in issue for issue in result["issues"]), result)

    def test_scoped_model_approval_checks_model_upstream_not_unrelated_result(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_path, _ = build_three_question_project(root)
            current = yaml.safe_load(state_path.read_text(encoding="utf-8"))
            current["subproblems"]["Q1"]["human_model_approval_status"] = "pending"
            state_path.write_text(yaml.safe_dump(current, allow_unicode=True, sort_keys=False), encoding="utf-8")
            self.assertEqual(
                APPROVAL.validate_state(state_path, ["Q2"], project_root=root), [],
            )
            set_dependency(root, "Q2", "Q1", "model")
            missing = APPROVAL.validate_state(state_path, ["Q2"], project_root=root)
            self.assertTrue(any("Q1" in item and "human_model_approval_status" in item
                                for item in missing), missing)
            current = yaml.safe_load(state_path.read_text(encoding="utf-8"))
            current["subproblems"]["Q1"]["human_model_approval_status"] = "approved"
            state_path.write_text(yaml.safe_dump(current, allow_unicode=True, sort_keys=False), encoding="utf-8")
            self.assertEqual(APPROVAL.validate_state(state_path, ["Q2"], project_root=root), [])

    def test_scoped_model_approval_rejects_untyped_legacy_edge(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_path, _ = build_three_question_project(root)
            current = yaml.safe_load(state_path.read_text(encoding="utf-8"))
            current["subproblems"]["Q2"]["depends_on"] = ["Q1"]
            state_path.write_text(yaml.safe_dump(current, allow_unicode=True, sort_keys=False), encoding="utf-8")
            rejected = APPROVAL.validate_state(state_path, ["Q2"], project_root=root)
            self.assertTrue(any("legacy_untyped" in issue for issue in rejected), rejected)

    def test_static_and_transactional_code_delivery_both_reject_missing_result(self):
        from tests.test_v10_project_delivery_receipt import ProjectDeliveryReceiptTests

        case = ProjectDeliveryReceiptTests(
            "test_missing_upstream_result_is_diagnostic_and_verified_artifact_clears_it"
        )
        case.setUp()
        try:
            case.approved_question_scope(depends_on=[{"question": "Q2", "kind": "result"}])
            case.approve_additional_question("Q2")
            original = case.state_path.read_bytes()
            problems, parsed = DELIVERY.validate_script(case.root, case.code, "primary")
            self.assertTrue(any("Q2/result" in issue for issue in problems), problems)
            with self.assertRaisesRegex(ValueError, "Q2/result"):
                DELIVERY.update_state(case.root, parsed, case.code)
            self.assertEqual(case.state_path.read_bytes(), original)
        finally:
            case.doCleanups()

    def test_unregistered_question_does_not_acquire_implicit_qualification(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_three_question_project(root)
            result = GATE.inspect(root, "Q9")
            self.assertEqual(result["status"], "failed")
            self.assertTrue(any("Q9" in issue for issue in result["issues"]))


if __name__ == "__main__":
    unittest.main()
