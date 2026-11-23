from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

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
                   selector: str | None = None,
                   selectors: tuple[str, ...] | None = None) -> None:
    """Change synthetic State and current SIB together, with exact hash bindings."""
    state_path = root / "state/project_state.yaml"
    framework_path = root / "模型论文框架.md"
    state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    dependency = {"question": source, "kind": kind}
    state["subproblems"][target]["depends_on"] = [dependency]
    identity = identity_payload()
    identity["question"] = target
    requested = selectors if selectors is not None else ((selector,) if selector else ())
    identity["dependencies"] = ([dict(dependency, selector=name) for name in requested]
                                if requested else [dependency])
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


def set_approved_upstream_parameters(
    root: Path, *, second: bool = True, p2_value: object = 5.0,
    p2_source: str = "合成参数 P2 的已审核来源",
) -> None:
    """Bind file-backed Q1 approved SIB with one or two independent parameters."""
    state_path, framework_path = root / "state/project_state.yaml", root / "模型论文框架.md"
    state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    identity = identity_payload()
    identity["parameters"][0].update(value=7.0, source="合成参数 P1 的已审核来源")
    if second:
        second_param = deepcopy(identity["parameters"][0])
        second_param.update(id="P2", symbol="theta", value=p2_value, source=p2_source)
        identity["parameters"].append(second_param)
    digest = semantic_identity.semantic_identity_hash(identity)
    for field in ("semantic_identity_hash", "validated_semantic_identity_hash",
                  "approved_semantic_identity_hash"):
        state["subproblems"]["Q1"][field] = digest
    text = framework_path.read_text(encoding="utf-8")
    start, stop = text.index("### Q1：第一问"), text.index("### Q2：第一问")
    section = framework(identity, question="Q1").split("## 各问模型与结果\n", 1)[1]
    framework_path.write_text(text[:start] + section + text[stop:], encoding="utf-8")
    state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False),
                          encoding="utf-8")
    set_dependency(root, "Q2", "Q1", "parameter", selectors=("P1", "P2"))


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

    def test_exact_approved_parameter_value_and_selector_can_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_path, framework_path = build_three_question_project(root)
            upstream = identity_payload()
            upstream["parameters"][0]["value"] = 7.0
            upstream["parameters"][0]["source"] = "合成题面参数已审计"
            digest = semantic_identity.semantic_identity_hash(upstream)
            state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
            q1 = state["subproblems"]["Q1"]
            for name in ("semantic_identity_hash", "validated_semantic_identity_hash",
                         "approved_semantic_identity_hash"):
                q1[name] = digest
            state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
            text = framework_path.read_text(encoding="utf-8")
            first, following = text.index("### Q1：第一问"), text.index("### Q2：第一问")
            section = framework(upstream, question="Q1").split(
                "## 各问模型与结果\n", 1,
            )[1]
            framework_path.write_text(text[:first] + section + text[following:],
                                      encoding="utf-8")
            set_dependency(root, "Q2", "Q1", "parameter", selector="P1")
            good = GATE.inspect(root, "Q2")
            self.assertEqual(good["status"], "passed", good)
            changed = framework_path.read_text(encoding="utf-8")
            self.assertIn("value: 7.0", changed)
            framework_path.write_text(changed.replace("value: 7.0", "value: 8.0", 1),
                                      encoding="utf-8")
            stale = GATE.inspect(root, "Q2")
            self.assertEqual(stale["status"], "failed", stale)
            self.assertTrue(any("Q1/parameter" in issue for issue in stale["issues"]))

    def test_two_individually_proven_approved_parameters_are_eligible(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            build_three_question_project(root)
            set_approved_upstream_parameters(root)
            original_state = (root / "state/project_state.yaml").read_bytes()
            accepted = GATE.inspect(root, "Q2")
            self.assertEqual(accepted["status"], "passed", accepted)
            self.assertEqual(accepted["checked_edges"][0]["kind"], "parameter")
            self.assertEqual((root / "state/project_state.yaml").read_bytes(), original_state)

    def test_each_parameter_selector_must_resolve_to_exact_finite_sourced_value(self):
        for case in ("missing_second", "empty_source", "boolean_value"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                build_three_question_project(root)
                set_approved_upstream_parameters(
                    root, second=case != "missing_second",
                    p2_source="" if case == "empty_source" else "合成参数来源",
                    p2_value=True if case == "boolean_value" else 5.0,
                )
                result = GATE.inspect(root, "Q2")
                self.assertEqual(result["status"], "failed", result)
                self.assertTrue(any("P2" in issue for issue in result["issues"]), result)

    def test_framework_drift_after_qualification_cannot_rebind_late_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, framework_path = build_three_question_project(root)
            set_dependency(root, "Q2", "Q1", "model")
            original_source = GATE.hydrate_project_context
            initial_state = (root / "state/project_state.yaml").read_bytes()

            def rewrite_after_qualification(*args, **kwargs):
                qualified = original_source(*args, **kwargs)
                framework_path.write_bytes(framework_path.read_bytes() + b"\n<!-- changed after qualification -->\n")
                return qualified

            with patch.object(GATE, "hydrate_project_context",
                              side_effect=rewrite_after_qualification):
                result = GATE.inspect(root, "Q2")
            self.assertEqual(result["status"], "failed", result)
            self.assertTrue(any("模型论文框架.md" in issue for issue in result["issues"]), result)
            self.assertEqual((root / "state/project_state.yaml").read_bytes(), initial_state)

    def test_accepted_workbook_drift_after_qualification_cannot_rebind_late_hash(self):
        from tests.test_v10_project_delivery_receipt import ProjectDeliveryReceiptTests

        case = ProjectDeliveryReceiptTests(
            "test_missing_upstream_result_is_diagnostic_and_verified_artifact_clears_it"
        )
        case.setUp()
        try:
            case.approved_question_scope()
            case.approve_additional_question("Q2", depends_on=[
                {"question": "Q1", "kind": "result"},
            ])
            case.accept_primary_fixture()
            state = case.state()
            state["subproblems"]["Q1"]["result_analysis_status"] = "not_required"
            state["subproblems"]["Q1"]["result_analysis_requirement_reason"] = (
                "合成测试已审计不需要额外03B；不代表实际用户数值验证"
            )
            case.save(state)
            stable = GATE.inspect(case.root, "Q2")
            self.assertEqual(stable["status"], "passed", stable)
            workbook = case.root / state["subproblems"]["Q1"]["solution_workbook"]
            original_source = GATE.hydrate_project_context
            original_state = case.state_path.read_bytes()

            def replace_after_qualification(*args, **kwargs):
                qualified = original_source(*args, **kwargs)
                workbook.write_bytes(workbook.read_bytes() + b"changed-after-qualification")
                return qualified

            with patch.object(GATE, "hydrate_project_context",
                              side_effect=replace_after_qualification):
                rejected = GATE.inspect(case.root, "Q2")
            self.assertEqual(rejected["status"], "failed", rejected)
            self.assertTrue(any("solution_workbook" in issue or "xlsx" in issue
                                for issue in rejected["issues"]), rejected)
            self.assertEqual(case.state_path.read_bytes(), original_state)
        finally:
            case.doCleanups()

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

    def test_mixed_model_result_cycle_does_not_block_explicit_q2_model_approval(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_path, _ = build_three_question_project(root)
            # Q2 needs Q1's approved MODEL; Q1 consumes Q2's RESULT later.
            # No model-only cycle exists, so the numerical ordering does not
            # require an extra Human Model Approval or a different question.
            set_dependency(root, "Q2", "Q1", "model")
            set_dependency(root, "Q1", "Q2", "result")
            before = state_path.read_bytes()
            self.assertEqual(APPROVAL.validate_state(
                state_path, ["Q2"], project_root=root,
            ), [])
            eligible = GATE.inspect(root, "Q2")
            self.assertEqual(eligible["status"], "passed", eligible)
            self.assertEqual(APPROVAL.validate_state(
                state_path, ["Q3"], project_root=root,
            ), [])
            self.assertEqual(state_path.read_bytes(), before)

    def test_real_model_only_cycle_still_blocks_q2_without_blocking_q3(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_path, _ = build_three_question_project(root)
            set_dependency(root, "Q2", "Q1", "model")
            set_dependency(root, "Q1", "Q2", "model")
            failures = APPROVAL.validate_state(state_path, ["Q2"], project_root=root)
            self.assertTrue(any("model prerequisite cycle" in issue
                                for issue in failures), failures)
            self.assertEqual(APPROVAL.validate_state(
                state_path, ["Q3"], project_root=root,
            ), [])

    def test_mixed_cycle_does_not_waive_unapproved_upstream_model(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_path, _ = build_three_question_project(root)
            set_dependency(root, "Q2", "Q1", "model")
            set_dependency(root, "Q1", "Q2", "result")
            state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
            state["subproblems"]["Q1"]["human_model_approval_status"] = "pending"
            state_path.write_text(yaml.safe_dump(
                state, allow_unicode=True, sort_keys=False), encoding="utf-8")
            failures = APPROVAL.validate_state(state_path, ["Q2"], project_root=root)
            self.assertTrue(any("Q1" in issue and "human_model_approval_status" in issue
                                for issue in failures), failures)
            self.assertFalse(any("model prerequisite cycle" in issue
                                 for issue in failures), failures)

    def test_result_only_cycle_is_not_an_approval_cycle_but_blocks_code_delivery(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_path, _ = build_three_question_project(root)
            set_dependency(root, "Q2", "Q1", "result")
            set_dependency(root, "Q1", "Q2", "result")
            self.assertEqual(APPROVAL.validate_state(
                state_path, ["Q2"], project_root=root,
            ), [])
            blocked = GATE.inspect(root, "Q2")
            self.assertEqual(blocked["status"], "failed", blocked)
            self.assertTrue(any("Q1/result" in issue for issue in blocked["issues"]), blocked)

    def test_legacy_dependency_keeps_model_approval_read_compatibility_but_blocks_delivery(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_path, _ = build_three_question_project(root)
            current = yaml.safe_load(state_path.read_text(encoding="utf-8"))
            current["subproblems"]["Q2"]["depends_on"] = ["Q1"]
            state_path.write_text(yaml.safe_dump(current, allow_unicode=True, sort_keys=False), encoding="utf-8")
            # Historical string dependencies are read-compatible for the
            # mathematical Model Approval itself (no invented kind here).
            self.assertEqual(APPROVAL.validate_state(state_path, ["Q2"], project_root=root), [])
            # New numerical execution cannot assume the untyped edge is result,
            # model, data or parameter; the code-delivery prerequisite stays hard.
            delivery = GATE.inspect(root, "Q2")
            self.assertEqual(delivery["status"], "failed", delivery)
            self.assertTrue(any("legacy" in issue for issue in delivery["issues"]), delivery)

    def test_malformed_dependency_is_reported_without_crashing_unrelated_model_approval(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_path, _ = build_three_question_project(root)
            state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
            state["subproblems"]["Q2"]["depends_on"] = 7
            state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
            invalid = APPROVAL.validate_state(state_path, ["Q2"], project_root=root)
            self.assertTrue(any("depends_on" in issue for issue in invalid), invalid)
            # Q3 is independent: one malformed Q2 list cannot raise TypeError
            # or revoke the unrelated current Model Approval.
            self.assertEqual(APPROVAL.validate_state(state_path, ["Q3"], project_root=root), [])

    def test_accepted_primary_only_does_not_clear_required_analysis_wait(self):
        from tests.test_v10_project_delivery_receipt import ProjectDeliveryReceiptTests
        from runtime_assurance import hydrate_project_context

        case = ProjectDeliveryReceiptTests(
            "test_missing_upstream_result_is_diagnostic_and_verified_artifact_clears_it"
        )
        case.setUp()
        try:
            case.approved_question_scope()
            case.approve_additional_question("Q2", depends_on=[
                {"question": "Q1", "kind": "result"},
            ])
            case.accept_primary_fixture()
            incomplete = GATE.inspect(case.root, "Q2")
            self.assertEqual(incomplete["status"], "failed", incomplete)
            self.assertIn("accepted_solution_workbook",
                          hydrate_project_context(case.root, "Q1")["verified_artifacts"])
            self.assertNotIn("validated_results",
                             hydrate_project_context(case.root, "Q1")["verified_artifacts"])
            state = case.state()
            entry = state["subproblems"]["Q1"]
            entry["result_analysis_status"] = "not_required"
            entry["result_analysis_requirement_reason"] = (
                "已审计当前主结果不需03B；此为合成Fixture，不是用户成果验收"
            )
            case.save(state)
            self.assertIn("validated_results",
                          hydrate_project_context(case.root, "Q1")["verified_artifacts"])
            eligible = GATE.inspect(case.root, "Q2")
            self.assertEqual(eligible["status"], "passed", eligible)
        finally:
            case.doCleanups()

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
