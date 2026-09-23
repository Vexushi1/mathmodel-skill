"""Project-level solver policy at the current delivery and receipt boundary.

The executed scalar program is the repository's isolated maintenance fixture,
not a competition model or a claim about native MATLAB execution.
"""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import openpyxl
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import analysis_prerequisites as PREREQUISITES
import validate_code_delivery as DELIVERY
import validate_user_execution as RECEIPT
from tests.test_copied_support_source_closure import instantiate
from tests.test_solver_backend_end_to_end import prepare as prepare_matlab


class ProjectDeliveryReceiptTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.code, self.config = instantiate(self.root, minimal=True)
        self.state_path = self.root / "state/project_state.yaml"
        state = self.state()
        state["execution"] = {
            "solver_backend": "python",
            "solver_backend_selection_reason": "全题数值需求及环境已审视",
        }
        state["subproblems"]["Q1"]["solver_execution"] = {"primary": {}}
        self.save(state)
        self.workbook = self.root / self.config["expected_workbook"]

    def state(self):
        return yaml.safe_load(self.state_path.read_text(encoding="utf-8"))

    def save(self, state):
        self.state_path.write_text(
            yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")

    def deliver(self):
        issues, parsed = DELIVERY.validate_script(self.root, self.code, "primary")
        self.assertEqual(issues, [])
        self.assertEqual(parsed, self.config)
        DELIVERY.update_state(self.root, parsed, self.code)
        return self.state()

    def execute(self):
        environment = {key: value for key, value in os.environ.items()
                       if key not in {"PYTHONPATH", "HSK_WORKBOOK_SCHEMA"}}
        environment["PYTHONUTF8"] = "1"
        before = self.state_path.read_bytes()
        result = subprocess.run(
            [sys.executable, "-B", str(self.code)], cwd=self.root, env=environment,
            capture_output=True, encoding="utf-8", timeout=45,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.state_path.read_bytes(), before)
        self.assertTrue(self.workbook.is_file())

    def test_delivery_uses_project_policy_and_records_only_bundle_identity(self):
        state = self.deliver()
        entry = state["subproblems"]["Q1"]
        binding = entry["solver_execution"]["primary"]
        self.assertEqual(entry["primary_execution_status"], "awaiting_user_execution")
        self.assertIn("bundle_sha256", binding)
        self.assertNotIn("validated_bundle_sha256", binding)
        self.assertNotIn("backend", binding)
        self.assertNotIn("selection_reason", binding)

    def test_unregistered_standard_file_requires_explicit_delivery(self):
        self.assertEqual(DELIVERY.discover_scripts(self.root), [])
        self.assertEqual(DELIVERY.validate_script(self.root, self.code, "primary")[0], [])
        self.deliver()
        self.assertEqual(DELIVERY.discover_scripts(self.root), [self.code])

    def test_missing_or_conflicting_policy_cannot_deliver(self):
        state = self.state()
        state.pop("execution")
        self.save(state)
        before = self.state_path.read_bytes()
        self.assertTrue(DELIVERY.validate_script(self.root, self.code)[0])
        with self.assertRaises(ValueError):
            DELIVERY.update_state(self.root, self.config, self.code)
        self.assertEqual(self.state_path.read_bytes(), before)

        state["execution"] = {
            "solver_backend": "matlab",
            "solver_backend_selection_reason": "完整项目复核",
        }
        self.save(state)
        before = self.state_path.read_bytes()
        self.assertTrue(any("项目后端" in item for item in DELIVERY.validate_script(self.root, self.code)[0]))
        with self.assertRaisesRegex(ValueError, "项目后端"):
            DELIVERY.update_state(self.root, self.config, self.code)
        self.assertEqual(self.state_path.read_bytes(), before)

    def test_write_rechecks_current_preprocessing_decision_after_static_validation(self):
        issues, parsed = DELIVERY.validate_script(self.root, self.code, "primary")
        self.assertEqual(issues, [])
        state = self.state()
        state["preprocessing"].update(decision="project_level", status="pending", quality_status="pending")
        self.save(state)
        before = self.state_path.read_bytes()
        with self.assertRaisesRegex(ValueError, "必须先验收数据预处理结果"):
            DELIVERY.update_state(self.root, parsed, self.code)
        self.assertEqual(self.state_path.read_bytes(), before)

    def test_matlab_source_obeys_the_same_project_policy_without_native_execution(self):
        root = self.root / "matlab_project"
        prepare_matlab(root)
        state_path = root / "state/project_state.yaml"
        state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
        state["execution"] = {
            "solver_backend": "matlab",
            "solver_backend_selection_reason": "全题数值需求及环境已审视",
        }
        record = state["subproblems"]["Q1"]["solver_execution"]["primary"]
        self.assertNotIn("backend", record)
        self.assertNotIn("selection_reason", record)
        state_path.write_text(yaml.safe_dump(state, allow_unicode=True), encoding="utf-8")
        source = root / state["subproblems"]["Q1"]["code"]
        issues, _ = DELIVERY.validate_script(root, source, "primary")
        self.assertEqual(issues, [])

    def test_successful_receipt_validates_bundle_without_adding_stage_selection(self):
        self.deliver()
        self.execute()
        state = self.state()
        self.assertEqual(RECEIPT.validate_one(self.root, self.workbook, state, True), [])
        entry = state["subproblems"]["Q1"]
        binding = entry["solver_execution"]["primary"]
        self.assertEqual(entry["primary_execution_status"], "accepted")
        self.assertEqual(binding["validated_bundle_sha256"], binding["bundle_sha256"])
        self.assertNotIn("backend", binding)

    def test_retired_workbook_and_opposite_receipt_cannot_mutate_current_state(self):
        self.deliver()
        self.execute()
        state = self.state()
        retired = deepcopy(state)
        entry = retired["subproblems"]["Q1"]
        entry.pop("code")
        entry.pop("primary_code_sha256")
        entry["solver_execution"]["primary"].clear()
        before = deepcopy(retired)
        issues = RECEIPT.validate_one(self.root, self.workbook, retired, True)
        self.assertTrue(any("历史工作簿" in item for item in issues))
        self.assertEqual(retired, before)

        book = openpyxl.load_workbook(self.workbook)
        try:
            sheet = book["运行配置"]
            row = next(row for row in sheet.iter_rows(min_row=2)
                       if row[0].value == "solver_backend")
            row[1].value = "matlab"
            book.save(self.workbook)
        finally:
            book.close()
        before = deepcopy(state)
        issues = RECEIPT.validate_one(self.root, self.workbook, state, True)
        self.assertTrue(any("项目后端" in item for item in issues))
        self.assertEqual(state, before)

    def test_old_state_is_read_only_for_analysis_prerequisites(self):
        state = self.state()
        state.pop("execution")
        entry = state["subproblems"]["Q1"]
        self.assertTrue(any("historical" in item or "project backend" in item
                            for item in PREREQUISITES.analysis_issues(
                                self.root, state, entry, require_project_policy=True)))


if __name__ == "__main__":
    unittest.main()
