from copy import deepcopy
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml
import openpyxl

import test_user_execution_contract as fixtures

ROOT = Path(__file__).resolve().parents[1]
CODE = fixtures.CODE
RECEIPT = fixtures.RECEIPT
STATE = fixtures.load_module("audit_analysis_state", ROOT / "scripts/validate_project_state.py")
TRANSITIONS = fixtures.load_module("audit_analysis_transitions", ROOT / "scripts/state_transitions.py")
CONTRACT = yaml.safe_load((ROOT / "core/state_transition_contract.yaml").read_text(encoding="utf-8"))


class AnalysisBoundaryTests(unittest.TestCase):
    def project(self, root, *, delivered=True):
        fixture = fixtures.UserExecutionContractTests()
        primary = fixture.make_project(root)
        state = fixture.accept_primary(root, primary)
        entry = state["subproblems"]["Q1"]
        entry.update(result_analysis_requirement_reason="A boundary risk requires parameter sensitivity",
                     analysis_methods=["参数敏感性"])
        fixture.write_state(root, state)
        code = fixture.make_analysis_code(root)
        if delivered:
            issues, config = CODE.validate_script(root, code, "analysis")
            self.assertEqual(issues, [])
            CODE.update_state(root, config, code)
            state = fixture.read_state(root)
        return fixture, state, code

    def test_delivery_and_receipt_reject_invalid_primary_and_gate_without_mutation(self):
        cases = ("pending", "quality_failed", "missing_primary", "tampered_primary", "numeric_stale",
                 "missing_reason", "missing_methods", "not_required")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                fixture, state, code = self.project(root)
                entry = state["subproblems"]["Q1"]
                if case == "pending":
                    entry["primary_execution_status"] = "pending"
                elif case == "quality_failed":
                    entry["result_quality_status"] = "failed"
                elif case == "missing_primary":
                    (root / entry["solution_workbook"]).unlink()
                elif case == "tampered_primary":
                    (root / entry["solution_workbook"]).write_bytes(b"changed")
                elif case == "numeric_stale":
                    entry.update(artifacts_stale=True, stale_layers=["solution_workbook"])
                elif case == "missing_reason":
                    entry.pop("result_analysis_requirement_reason")
                elif case == "missing_methods":
                    entry["analysis_methods"] = []
                else:
                    entry["result_analysis_status"] = "not_required"
                fixture.write_state(root, state)
                before = deepcopy(state)
                issues, config = CODE.validate_script(root, code, "analysis")
                self.assertTrue(issues)
                with self.assertRaises(ValueError):
                    CODE.update_state(root, config, code)
                self.assertEqual(fixture.read_state(root), before)
                workbook = fixture.make_analysis_workbook(root, code)
                for write in (False, True):
                    issues = RECEIPT.validate_one(root, workbook, state, write)
                    self.assertTrue(issues)
                    self.assertEqual(state, before)

    def test_existing_analysis_file_alone_does_not_authorize_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture, state, code = self.project(root, delivered=False)
            entry = state["subproblems"]["Q1"]
            entry.update(result_analysis_code=code.relative_to(root).as_posix(),
                         analysis_code_sha256=hashlib.sha256(code.read_bytes()).hexdigest())
            workbook = fixture.make_analysis_workbook(root, code)
            before = deepcopy(state)
            self.assertTrue(RECEIPT.validate_one(root, workbook, state, True))
            self.assertEqual(state, before)

    def test_required_chain_and_figure_only_stale_remain_usable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture, state, code = self.project(root)
            entry = state["subproblems"]["Q1"]
            entry.update(artifacts_stale=True, stale_layers=["figure_bundle"])
            workbook = fixture.make_analysis_workbook(root, code)
            self.assertEqual(RECEIPT.validate_one(root, workbook, state, False), [])
            self.assertEqual(RECEIPT.validate_one(root, workbook, state, True), [])
            self.assertEqual(entry["analysis_execution_status"], "accepted")
            self.assertEqual(entry["result_analysis_status"], "passed")

    def test_analysis_cli_read_and_write_refuse_not_required(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture, state, code = self.project(root)
            state["subproblems"]["Q1"]["result_analysis_status"] = "not_required"
            fixture.write_state(root, state)
            workbook = fixture.make_analysis_workbook(root, code)
            before = (root / "state/project_state.yaml").read_bytes()
            for writer in (False, True):
                for script, option, path in (
                    ("validate_code_delivery.py", "--script", code),
                    ("validate_user_execution.py", "--workbook", workbook),
                ):
                    command = [sys.executable, str(ROOT / "scripts" / script), str(root),
                               option, str(path), "--strict"] + (["--write"] if writer else [])
                    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertEqual((root / "state/project_state.yaml").read_bytes(), before)

    def test_accepted_historical_read_does_not_require_new_gate_reason(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture, state, code = self.project(root)
            workbook = fixture.make_analysis_workbook(root, code)
            self.assertEqual(RECEIPT.validate_one(root, workbook, state, True), [])
            entry = state["subproblems"]["Q1"]
            entry.pop("result_analysis_requirement_reason")
            before = deepcopy(state)
            self.assertEqual(RECEIPT.validate_one(root, workbook, state, False), [])
            self.assertTrue(RECEIPT.validate_one(root, workbook, state, True))
            self.assertEqual(state, before)

    def test_analysis_delivery_cannot_replace_the_primary_data_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture, state, code = self.project(root)
            original = state["subproblems"]["Q1"]["data_hash"]
            code.write_text(code.read_text(encoding="utf-8").replace(original, "b" * 64), encoding="utf-8")
            issues, config = CODE.validate_script(root, code, "analysis")
            self.assertTrue(any("data_sha256" in item for item in issues), issues)
            with self.assertRaisesRegex(ValueError, "data_sha256"):
                CODE.update_state(root, config, code)
            self.assertEqual(fixture.read_state(root), state)

    def test_project_level_preprocessing_must_remain_verified(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture, state, code = self.project(root)
            preprocessing = root / "preprocessing.xlsx"
            preprocessing.write_bytes(b"accepted preprocessing")
            digest = hashlib.sha256(preprocessing.read_bytes()).hexdigest()
            state["preprocessing"].update(decision="project_level", status="accepted", quality_status="passed",
                                          workbook="preprocessing.xlsx", workbook_sha256=digest)
            entry = state["subproblems"]["Q1"]
            entry.update(data_hash=digest, validated_data_hash=digest)
            entry["artifact_hashes"]["data"] = digest
            entry["validated_artifact_hashes"]["data"] = digest
            helper = CODE.ANALYSIS_PREREQUISITES
            self.assertEqual(helper.primary_issues(root, state, state["subproblems"]["Q1"]), [])
            preprocessing.write_bytes(b"changed preprocessing")
            self.assertTrue(helper.primary_issues(root, state, state["subproblems"]["Q1"]))
            state["preprocessing"]["status"] = "pending"
            self.assertTrue(helper.primary_issues(root, state, state["subproblems"]["Q1"]))

    def test_successful_receipts_close_only_their_verified_numeric_layers(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture, state, code = self.project(root)
            entry = state["subproblems"]["Q1"]
            entry.update(artifacts_stale=True, stale_layers=[
                "data", "primary_code", "solution_workbook", "analysis_code",
                "result_analysis_workbook", "matlab_script", "figure_bundle", "framework",
            ])
            primary = root / entry["solution_workbook"]
            self.assertEqual(RECEIPT.validate_one(root, primary, state, True), [])
            self.assertEqual(set(entry["stale_layers"]), {
                "analysis_code", "result_analysis_workbook", "matlab_script", "figure_bundle", "framework",
            })
            self.assertEqual(entry["validated_data_hash"], entry["data_hash"])
            self.assertEqual(entry["validated_artifact_hashes"]["data"], entry["data_hash"])
            self.assertEqual(STATE._validate_hashes("Q1", entry, "designed"), [])
            workbook = fixture.make_analysis_workbook(root, code)
            self.assertEqual(RECEIPT.validate_one(root, workbook, state, True), [])
            self.assertEqual(set(entry["stale_layers"]), {"matlab_script", "figure_bundle", "framework"})
            self.assertTrue(entry["artifacts_stale"])
            self.assertEqual(STATE._validate_hashes("Q1", entry, "designed"), [])

    def test_changed_primary_receipt_invalidates_gate_analysis_and_result_dependents(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture, state, code = self.project(root)
            workbook = fixture.make_analysis_workbook(root, code)
            self.assertEqual(RECEIPT.validate_one(root, workbook, state, True), [])
            entry = state["subproblems"]["Q1"]
            dependent = deepcopy(entry)
            dependent["depends_on"] = [{"question": "Q1", "kind": "result"}]
            state["subproblems"]["Q2"] = dependent
            primary = root / entry["solution_workbook"]
            code_hash = entry["primary_code_sha256"]
            self.assertEqual(RECEIPT.validate_one(root, primary, state, True), [])
            self.assertIn("result_analysis_requirement_reason", entry)
            self.assertEqual(dependent["primary_execution_status"], "accepted")
            book = openpyxl.load_workbook(primary)
            book.create_sheet("补充证据").append(["Updated primary evidence"])
            book.save(primary)
            book.close()
            self.assertEqual(RECEIPT.validate_one(root, primary, state, True), [])
            self.assertEqual(entry["primary_code_sha256"], code_hash)
            self.assertEqual(entry["primary_execution_status"], "accepted")
            self.assertEqual(entry["result_analysis_status"], "pending")
            self.assertEqual(entry["analysis_execution_status"], "pending")
            self.assertNotIn("result_analysis_requirement_reason", entry)
            self.assertNotIn("solution_workbook", entry["stale_layers"])
            self.assertIn("result_analysis_workbook", entry["stale_layers"])
            self.assertEqual(dependent["primary_execution_status"], "pending")
            self.assertNotIn("result_analysis_requirement_reason", dependent)
            self.assertIn("solution_workbook", dependent["stale_layers"])


class ConditionalAnalysisStateTests(unittest.TestCase):
    def state(self, root, status):
        state = yaml.safe_load((ROOT / "state/project_state.example.yaml").read_text(encoding="utf-8"))
        state["execution"].update(solver_backend="python",
                                  solver_backend_selection_reason="全题维护微例已审视")
        entry = state["subproblems"]["Q1"]
        workbook = root / "primary.xlsx"
        workbook.write_bytes(b"accepted primary fixture")
        digest = hashlib.sha256(workbook.read_bytes()).hexdigest()
        code = root / "问题一求解/问题一求解.py"
        code.parent.mkdir()
        config = {
            "stage": "primary", "problem_name": "问题一", "solver_backend": "python",
            "run_receipt_protocol_version": "1.1.0", "code_dependencies": [],
            "data_paths": ["primary.xlsx"], "data_sha256": digest,
            "solver": "fixture", "random_seed": 2026, "tolerance": 1e-8,
            "iteration_or_time_limit": "direct", "expected_workbook": "问题一求解/问题一求解结果.xlsx",
            "primary_quality_protocol_version": "1.0.0",
        }
        code.write_text(f"RUN_CONFIG = {config!r}\n\ndef main():\n    return 0\n", encoding="utf-8")
        code_digest = hashlib.sha256(code.read_bytes()).hexdigest()
        bundle = CODE.STAGE_CODE.stage_code_fingerprint(root, code)["bundle_sha256"]
        hashes = {name: digest for name in ("data", "primary_code", "solution_workbook", "framework")}
        hashes["primary_code"] = code_digest
        entry.update(status=status, primary_execution_status="accepted", result_quality_status="passed",
                     result_analysis_status="not_required", result_analysis_requirement_reason="Only current-world claims",
                     code=code.relative_to(root).as_posix(), primary_code_sha256=code_digest,
                     solver_execution={"primary": {"bundle_sha256": bundle, "validated_bundle_sha256": bundle}},
                     solution_workbook="primary.xlsx", result_summary_status="current", result_summary_anchor="Q1 result",
                     capabilities={key: False for key in entry["capabilities"]}, artifact_hashes=hashes, validated_artifact_hashes=dict(hashes),
                     validation_status="passed", evidence=["Accepted primary"])
        return state

    def test_not_required_allows_later_states_without_analysis_artifacts(self):
        for status in ("validated", "written", "completed"):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                state = self.state(root, status)
                self.assertEqual(STATE.validate_state_payload(state, project_root=root), [])

    def test_not_required_is_not_analyzed_and_needs_accepted_primary_and_reason(self):
        for case in ("analyzed", "pending_primary", "missing_reason"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                state = self.state(root, "analyzed" if case == "analyzed" else "validated")
                entry = state["subproblems"]["Q1"]
                if case == "pending_primary":
                    entry["primary_execution_status"] = "pending"
                if case == "missing_reason":
                    entry.pop("result_analysis_requirement_reason")
                self.assertTrue(STATE.validate_state_payload(state, project_root=root))

    def test_primary_changes_clear_gate_decision_but_analysis_and_figure_changes_do_not(self):
        for event in ("primary_code_changed", "data_changed", "solution_workbook_changed",
                      "semantic_identity_changed", "analysis_code_changed", "figure_bundle_changed"):
            with self.subTest(event=event):
                entry = {"result_analysis_requirement_reason": "Previously required",
                         "analysis_methods": ["sensitivity"], "result_analysis_status": "pending"}
                report = TRANSITIONS.apply_local_event(entry, event, CONTRACT)
                cleared = event not in {"analysis_code_changed", "figure_bundle_changed"}
                self.assertEqual("result_analysis_requirement_reason" not in entry, cleared)
                self.assertEqual(entry["analysis_methods"], ["sensitivity"])
                if cleared:
                    self.assertIsNone(report["status_updates"]["result_analysis_requirement_reason"])

    def test_dependency_transition_clears_old_gate_and_has_valid_stale_coverage(self):
        from test_v900_state_transitions import state_with_dependency
        state = state_with_dependency("result")
        for entry in state["subproblems"].values():
            entry.update(result_analysis_requirement_reason="Old decision",
                         artifact_hashes={"primary_code": "b" * 64},
                         validated_artifact_hashes={"primary_code": "a" * 64})
        TRANSITIONS.apply_transition(state, event="primary_code_changed", source_question="Q1", contract=CONTRACT)
        for entry in state["subproblems"].values():
            self.assertNotIn("result_analysis_requirement_reason", entry)
        own = state["subproblems"]["Q1"]
        self.assertEqual(STATE._validate_hashes("Q1", own, "designed"), [])
        own["stale_layers"].append("robustness_workbook")
        self.assertTrue(STATE._validate_hashes("Q1", own, "designed"))


if __name__ == "__main__":
    unittest.main()
