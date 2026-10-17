"""Synthetic XLSX boundary regressions; no task-specific entrypoint is executed."""
from __future__ import annotations

from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import openpyxl
import yaml

from tests import test_user_execution_contract as fixtures
from tests import test_solver_backend_preprocessing as preprocessing_fixtures

CODE = fixtures.CODE
RECEIPT = fixtures.RECEIPT


class ReceiptContextBoundaryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.fixture = fixtures.UserExecutionContractTests()

    def primary(self, *, accepted=False):
        code = self.fixture.make_project(self.root)
        if accepted:
            state = self.fixture.accept_primary(self.root, code)
            workbook = self.root / "问题一求解/问题一求解结果.xlsx"
        else:
            issues, config = CODE.validate_script(self.root, code, "primary")
            self.assertEqual(issues, [])
            CODE.update_state(self.root, config, code)
            workbook = self.fixture.make_primary_workbook(self.root, code)
            state = self.fixture.read_state(self.root)
        return code, workbook, state

    def analysis(self):
        code = self.fixture.make_project(self.root)
        self.fixture.accept_primary(self.root, code)
        self.fixture.activate_analysis(self.root)
        analysis = self.fixture.make_analysis_code(self.root)
        issues, config = CODE.validate_script(self.root, analysis, "analysis")
        self.assertEqual(issues, [])
        CODE.update_state(self.root, config, analysis)
        workbook = self.fixture.make_analysis_workbook(self.root, analysis)
        return code, analysis, workbook, self.fixture.read_state(self.root)

    def mutate_workbook(self, workbook, mutate):
        book = openpyxl.load_workbook(workbook)
        mutate(book)
        book.save(workbook)
        book.close()

    def run_cli(self, workbook):
        output = io.StringIO()
        with mock.patch("sys.argv", ["validate_user_execution.py", str(self.root),
                                     "--workbook", str(workbook), "--write", "--strict"]), redirect_stdout(output):
            result = RECEIPT._main()
        return result, output.getvalue()

    def test_missing_primary_source_or_input_is_pending_in_api_and_strict_cli(self):
        for missing in ("source", "input"):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as temp:
                # Each iteration has independently delivered source and captured XLSX.
                self.root = Path(temp)
                code, workbook, state = self.primary()
                (code if missing == "source" else self.root / "data.csv").unlink()
                before = deepcopy(state)
                observed = {"project": {}, "skill": {}}
                issues = RECEIPT.validate_one(self.root, workbook, state, True,
                                              conformance_read_set=observed)
                self.assertTrue(any("验收资料不完整" in item for item in issues), issues)
                self.assertEqual(state, before)
                missing_relative = code.relative_to(self.root).as_posix() if missing == "source" else "data.csv"
                self.assertIsNone(observed["project"][missing_relative])
                state_path = self.root / "state/project_state.yaml"
                original_bytes = state_path.read_bytes()
                result, output = self.run_cli(workbook)
                self.assertEqual(result, 1)
                self.assertIn("task_code_executed: false", output)
                self.assertEqual(state_path.read_bytes(), original_bytes)

    def test_missing_state_binding_metadata_is_not_a_workbook_counterexample(self):
        code, workbook, state = self.primary()
        entry = state["subproblems"]["Q1"]
        entry.pop("code")
        entry.pop("primary_code_sha256")
        entry.pop("data_hash")
        before = deepcopy(state)
        issues = RECEIPT.validate_one(self.root, workbook, state, True)
        self.assertTrue(any("项目状态缺少已交付代码哈希" in item for item in issues), issues)
        self.assertEqual(state, before)
        self.assertTrue(code.is_file())

    def test_unreadable_input_is_unfinished_without_fake_missing_hash_or_state_rejection(self):
        _, workbook, state = self.primary()
        before = deepcopy(state)
        original = RECEIPT.sha256_file

        def unreadable(path):
            if Path(path) == self.root / "data.csv":
                raise PermissionError("assistant cannot read this input")
            return original(path)

        observed = {"project": {}, "skill": {}}
        with mock.patch.object(RECEIPT, "sha256_file", side_effect=unreadable):
            issues = RECEIPT.validate_one(self.root, workbook, state, True,
                                          conformance_read_set=observed)
            result, output = self.run_cli(workbook)
        self.assertTrue(any("尚不可读取" in item for item in issues), issues)
        self.assertEqual(state, before)
        self.assertNotIn("data.csv", observed["project"])
        self.assertEqual(result, 1)
        self.assertIn("验收资料不完整", output)
        self.assertEqual(self.fixture.read_state(self.root), before)

    def test_missing_material_does_not_restore_or_rewrite_old_accepted_identity(self):
        code, workbook, state = self.primary(accepted=True)
        # An old accepted artifact may be read, but absence cannot close stale.
        entry = state["subproblems"]["Q1"]
        entry["stale_layers"] = ["solution_workbook"]
        entry["artifacts_stale"] = True
        before = deepcopy(state)
        code.unlink()
        issues = RECEIPT.validate_one(self.root, workbook, state, True)
        self.assertTrue(issues)
        self.assertEqual(state, before)

    def test_primary_missing_source_still_reports_numerical_counterexample_and_invalidates_current(self):
        code, workbook, state = self.primary(accepted=True)
        self.mutate_workbook(workbook, lambda book: setattr(book["主结果质量门"]["G2"], "value", False))
        # Simulate a historically accepted artifact whose same bytes are now
        # independently checked. Hash equality must not substitute for evidence.
        digest = hashlib.sha256(workbook.read_bytes()).hexdigest()
        entry = state["subproblems"]["Q1"]
        entry["validated_artifact_hashes"]["solution_workbook"] = digest
        entry["artifact_hashes"]["solution_workbook"] = digest
        before_hashes = deepcopy(entry["validated_artifact_hashes"])
        code.unlink()
        issues = RECEIPT.validate_one(self.root, workbook, state, True)
        self.assertTrue(any("数值" in item or "实际值" in item or "证据" in item for item in issues), issues)
        self.assertIn("solution_workbook", entry["stale_layers"])
        self.assertNotEqual(entry["result_quality_status"], "passed")
        self.assertEqual(entry["validated_artifact_hashes"], before_hashes)
        self.assertNotEqual(entry.get("primary_execution_status"), "rejected")

    def test_missing_source_and_schema_error_are_both_reported_before_cli_commit(self):
        code, workbook, state = self.primary(accepted=True)
        self.mutate_workbook(workbook, lambda book: book.remove(book["核心指标"]))
        digest = hashlib.sha256(workbook.read_bytes()).hexdigest()
        entry = state["subproblems"]["Q1"]
        entry["validated_artifact_hashes"]["solution_workbook"] = digest
        entry["artifact_hashes"]["solution_workbook"] = digest
        self.fixture.write_state(self.root, state)
        code.unlink()
        result, output = self.run_cli(workbook)
        self.assertEqual(result, 1)
        self.assertIn("工作簿结构Schema未通过", output)
        self.assertIn("验收资料不完整", output)
        saved = self.fixture.read_state(self.root)["subproblems"]["Q1"]
        self.assertIn("solution_workbook", saved["stale_layers"])
        self.assertEqual(saved["validated_artifact_hashes"]["solution_workbook"], digest)
        self.assertNotEqual(saved["result_quality_status"], "passed")

    def test_missing_input_does_not_mask_observed_source_or_helper_drift(self):
        for changed in ("source", "helper"):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as temp:
                self.root = Path(temp)
                code, workbook, state = self.primary(accepted=True)
                if changed == "source":
                    code.write_text(code.read_text(encoding="utf-8") + "\n# actual changed delivery\n", encoding="utf-8")
                else:
                    helper = self.root / "helper.py"
                    helper.write_text("VALUE = 1\n", encoding="utf-8")
                    config = self.fixture.config("primary", "问题一求解结果.xlsx")
                    config["code_dependencies"] = [{"path": "helper.py", "sha256": hashlib.sha256(helper.read_bytes()).hexdigest()}]
                    self.fixture.write_code(code, config)
                    # Keep the entry bound to this declared source; only the
                    # helper changes afterward, alongside an absent input.
                    state["subproblems"]["Q1"]["primary_code_sha256"] = hashlib.sha256(code.read_bytes()).hexdigest()
                    helper.write_text("VALUE = 2\n", encoding="utf-8")
                (self.root / "data.csv").unlink()
                hashes = deepcopy(state["subproblems"]["Q1"]["validated_artifact_hashes"])
                issues = RECEIPT.validate_one(self.root, workbook, state, True)
                self.assertTrue(any("SHA-256" in item for item in issues), issues)
                self.assertIn("primary_code", state["subproblems"]["Q1"]["stale_layers"])
                self.assertEqual(state["subproblems"]["Q1"]["validated_artifact_hashes"], hashes)

    def test_context_issues_block_acceptance_even_when_original_binding_would_pass(self):
        code, workbook, state = self.primary()
        # Current input violates strict project-relative spelling; the bundle
        # still exists, so issues must be present before the acceptance write.
        config = self.fixture.config("primary", "问题一求解结果.xlsx")
        config["data_paths"] = ["../outside.csv"]
        self.fixture.write_code(code, config)
        entry = state["subproblems"]["Q1"]
        entry["primary_code_sha256"] = hashlib.sha256(code.read_bytes()).hexdigest()
        issues = RECEIPT.validate_one(self.root, workbook, state, True)
        self.assertTrue(any("路径" in item for item in issues), issues)
        self.assertNotEqual(entry.get("primary_execution_status"), "accepted")
        self.assertNotIn("solution_workbook", entry.get("validated_artifact_hashes", {}))

    def test_missing_analysis_source_preserves_primary_and_pending_analysis(self):
        _, analysis, workbook, state = self.analysis()
        before = deepcopy(state)
        analysis.unlink()
        issues = RECEIPT.validate_one(self.root, workbook, state, True)
        self.assertTrue(any("验收资料不完整" in item for item in issues), issues)
        self.assertEqual(state, before)

    def test_analysis_prerequisite_early_failure_does_not_hide_returned_schema_failure(self):
        primary, _, workbook, state = self.analysis()
        self.mutate_workbook(workbook, lambda book: book.remove(book["参数敏感性"]))
        primary.unlink()
        primary_hashes = deepcopy(state["subproblems"]["Q1"]["validated_artifact_hashes"])
        issues = RECEIPT.validate_one(self.root, workbook, state, True)
        self.assertTrue(any("工作簿结构Schema未通过" in item for item in issues), issues)
        entry = state["subproblems"]["Q1"]
        self.assertIn("result_analysis_workbook", entry["stale_layers"])
        self.assertNotIn("solution_workbook", entry["stale_layers"])
        self.assertEqual(entry["validated_artifact_hashes"], primary_hashes)

    def test_analysis_missing_source_and_changed_accepted_primary_propagate_known_drift(self):
        _, analysis, workbook, state = self.analysis()
        primary = self.root / state["subproblems"]["Q1"]["solution_workbook"]
        self.mutate_workbook(primary, lambda book: setattr(book["核心指标"]["B2"], "value", 2))
        analysis.unlink()
        issues = RECEIPT.validate_one(self.root, workbook, state, True)
        self.assertTrue(any("accepted主工作簿当前SHA-256" in item for item in issues), issues)
        self.assertIn("solution_workbook", state["subproblems"]["Q1"]["stale_layers"])

    def test_preprocessing_missing_raw_input_preserves_state_but_real_quality_failure_invalidates(self):
        fixture = preprocessing_fixtures.SolverBackendPreprocessingTests()
        fixture.prepare_root(self.root)
        fixture.preprocessing_workbook()
        (self.root / "data/raw.csv").unlink()
        before = deepcopy(fixture.state)
        issues = RECEIPT.validate_one(self.root, fixture.pre_workbook, fixture.state, True)
        self.assertTrue(any("验收资料不完整" in item for item in issues), issues)
        self.assertEqual(fixture.state, before)
        self.mutate_workbook(fixture.pre_workbook, lambda book: setattr(book["预处理质量门"]["B2"], "value", False))
        issues = RECEIPT.validate_one(self.root, fixture.pre_workbook, fixture.state, True)
        self.assertTrue(any("预处理质量门未通过" in item for item in issues), issues)
        self.assertEqual(fixture.state["preprocessing"]["status"], "stale")
        self.assertNotEqual(fixture.state["preprocessing"]["quality_status"], "passed")

    def test_missing_input_remains_strict_in_underlying_gate_and_does_not_hide_later_aliases(self):
        from stage_inputs import InputUnavailableError, input_files, observe_inputs
        (self.root / "data.csv").write_text("x\n1\n", encoding="utf-8")
        with self.assertRaises(InputUnavailableError):
            input_files(self.root, ["missing.csv", "data.csv"])
        with self.assertRaises(ValueError) as captured:
            input_files(self.root, ["missing.csv", "data.csv", "DATA.csv"])
        self.assertNotIsInstance(captured.exception, InputUnavailableError)
        with self.assertRaises(ValueError) as captured:
            input_files(self.root, ["missing.csv", "../outside.csv"])
        self.assertNotIsInstance(captured.exception, InputUnavailableError)
        config = self.fixture.config("primary", "问题一求解结果.xlsx")
        config["data_paths"] = ["missing.csv"]
        with self.assertRaises(InputUnavailableError):
            observe_inputs(self.root, config, {"preprocessing": {"decision": "not_needed"}})

    def test_missing_input_observation_is_rechecked_before_typed_state_changes(self):
        code, workbook, state = self.primary(accepted=True)
        code.write_text(code.read_text(encoding="utf-8") + "\n# changed\n", encoding="utf-8")
        missing = self.root / "data.csv"
        missing.unlink()
        before = deepcopy(state)
        original = RECEIPT._validate_captured_receipt

        def material_appears(*args, **kwargs):
            issues = original(*args, **kwargs)
            missing.write_text("value\n1\n", encoding="utf-8")
            return issues

        with mock.patch.object(RECEIPT, "_validate_captured_receipt", side_effect=material_appears):
            with self.assertRaises(RECEIPT.PROJECT_TX.ReadSetConflictError):
                RECEIPT.validate_one(self.root, workbook, state, True)
        self.assertEqual(state, before)

    def test_helper_current_bytes_are_rechecked_before_receipt_acceptance(self):
        code, workbook, state = self.primary()
        original = RECEIPT.validate_execution_evidence

        def source_changes(*args, **kwargs):
            issues = original(*args, **kwargs)
            code.write_text(code.read_text(encoding="utf-8") + "\n# mutation during receipt\n", encoding="utf-8")
            return issues

        with mock.patch.object(RECEIPT, "validate_execution_evidence", side_effect=source_changes):
            with self.assertRaises(RECEIPT.PROJECT_TX.ReadSetConflictError):
                RECEIPT.validate_one(self.root, workbook, state, True)
        self.assertNotEqual(state["subproblems"]["Q1"].get("primary_execution_status"), "accepted")
        self.assertNotIn("solution_workbook", state["subproblems"]["Q1"].get("validated_artifact_hashes", {}))


if __name__ == "__main__":
    unittest.main()
