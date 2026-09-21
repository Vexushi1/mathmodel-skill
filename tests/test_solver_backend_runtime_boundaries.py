"""Regression scenarios for actual stage recovery and returned-workbook paths."""
from copy import deepcopy
import ctypes
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from resolve_runtime import resolve_runtime
import validate_user_execution as RECEIPT
from tests import test_solver_backends as fixtures
from tests.test_solver_backend_runtime_resume import legacy_primary_project


class StageRecoveryTests(unittest.TestCase):
    def test_analysis_request_recovery_uses_actual_primary_stage(self):
        for intent in ("result_analysis", "validation"):
            for primary, analysis in (("python", "matlab"), ("matlab", "python")):
                with self.subTest(intent=intent, primary=primary), tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    legacy_primary_project(root, analysis_backend=analysis)
                    path = root / "state/project_state.yaml"
                    state = yaml.safe_load(path.read_text(encoding="utf-8"))
                    entry = state["subproblems"]["Q1"]
                    entry.update(primary_execution_status="pending", result_quality_status="pending", status="designed")
                    # This recovery fixture has a selected primary but no delivered implementation.
                    entry.pop("code")
                    entry.pop("primary_code_sha256")
                    entry["solver_execution"]["primary"] = {"backend": primary, "selection_reason": "selected model implementation"}
                    path.write_text(yaml.safe_dump(state, allow_unicode=True), encoding="utf-8")
                    before = path.read_bytes()
                    for requested in (None, "auto", analysis):
                        plan = resolve_runtime(intent, project_root=root, question="Q1", solver_backend=requested)
                        self.assertIn("modules/03_solve_validate.md", plan["modules"])
                        self.assertNotIn("modules/03_result_analysis.md", plan["modules"])
                        self.assertEqual(plan["solver_backend"]["stage"], "primary")
                        self.assertEqual(plan["solver_backend"]["resolved"], primary)
                        self.assertEqual(plan["assurance"]["status"], "review_required" if requested == analysis else "pass")
                        expected = "templates/code/matlab/q1_solver.m" if primary == "matlab" else "templates/code/starter/README.md"
                        self.assertIn(expected, plan["templates"])
                        self.assertIn(expected, {r["path"] for r in plan["reading_plan"]["read_now"]})
                        self.assertNotIn("templates/code/matlab/q1_analysis.m", plan["templates"])
                        self.assertEqual(before, path.read_bytes())

    def test_legacy_primary_recovery_keeps_omitted_parameter_projection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy_primary_project(root, analysis_backend="matlab")
            path = root / "state/project_state.yaml"
            state = yaml.safe_load(path.read_text(encoding="utf-8"))
            state["subproblems"]["Q1"]["primary_execution_status"] = "pending"
            path.write_text(yaml.safe_dump(state, allow_unicode=True), encoding="utf-8")
            plan = resolve_runtime("result_analysis", project_root=root, question="Q1")
        self.assertNotIn("solver_backend", plan)
        self.assertIn("python_code", plan["terminal_outputs"])


class ReturnedWorkbookPathTests(unittest.TestCase):
    def fixture(self, root):
        fixture = fixtures.SolverBackendTests()
        fixture.root = root
        (root / "问题一求解").mkdir(parents=True)
        config = fixture.config()
        source = fixture.source(config)
        entry = fixture.entry(source, config)
        state = fixture.state(entry)
        book = fixture.primary_workbook(source, config, entry["solver_execution"]["primary"]["bundle_sha256"])
        return book, state

    def run_cli(self, root, workbook, *, write=False):
        command = [sys.executable, str(ROOT / "scripts/validate_user_execution.py"), str(root),
                   "--workbook", str(workbook), "--strict"]
        if write:
            command.append("--write")
        return subprocess.run(command, capture_output=True, encoding="utf-8", env={**os.environ, "PYTHONUTF8": "1"})

    def test_absolute_relative_paths_and_writing_share_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "returned workbook 中文"
            book, state = self.fixture(root)
            for workbook in (book, book.relative_to(root)):
                result = self.run_cli(root, workbook, write=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            entry = yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8"))["subproblems"]["Q1"]
            self.assertEqual(entry["primary_execution_status"], "accepted")
            self.assertEqual(entry["solution_workbook"], book.relative_to(root).as_posix())

    @unittest.skipUnless(os.name == "nt", "Windows 8.3 path identity")
    def test_windows_short_absolute_workbook_acceptance_and_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "returned workbook 中文"
            book, state = self.fixture(root)
            buffer = ctypes.create_unicode_buffer(32768)
            self.assertGreater(ctypes.windll.kernel32.GetShortPathNameW(str(root), buffer, len(buffer)), 0)
            if buffer.value == str(root):
                self.skipTest("The filesystem has no distinct 8.3 alias")
            short_root = Path(buffer.value)
            short_book = short_root / book.relative_to(root)
            for project in (root, short_root):
                for write in (False, True):
                    with self.subTest(project=project, write=write):
                        result = self.run_cli(project, short_book, write=write)
                        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                        self.assertNotIn("Traceback", result.stderr)
            self.assertEqual(RECEIPT.validate_one(root, short_book, deepcopy(state), True), [])

    def test_outside_workbook_is_rejected_without_read_or_state_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            _, state = self.fixture(root)
            outside = Path(tmp) / "问题一求解结果.xlsx"
            outside.write_text("not an Excel file: must reject the boundary before reading")
            state_path = root / "state/project_state.yaml"
            before = state_path.read_bytes()
            result = self.run_cli(root, outside, write=True)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("越出项目根目录", result.stdout)
            self.assertNotIn("Traceback", result.stderr)
            self.assertEqual(before, state_path.read_bytes())
            self.assertEqual(RECEIPT.validate_one(root, outside, state, True), ["工作簿路径越出项目根目录"])


if __name__ == "__main__":
    unittest.main()
