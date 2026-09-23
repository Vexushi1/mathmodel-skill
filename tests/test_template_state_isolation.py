"""Repository maintenance fixtures: task templates never own control-plane writes.

These are IO/isolation tests, not accepted-model or current 03B admission proofs.
The historical analysis adapter is imported explicitly, never from package exports.
"""
import ast
import dataclasses
import importlib
import inspect
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

from tests import test_split_pipeline_runtime as fixtures
from hsk_pipeline import main_pipeline as pipeline
from hsk_pipeline.result_io import read_workbook_tables

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "templates/code/hsk_pipeline"
STARTERS = ("classification", "evaluation", "optimization", "prediction", "simulation")


def passed_quality(context, constraints):
    return pd.DataFrame({"检查项": ["收敛"], "是否通过": [True], "证据": ["维护微例"]})


def primary_kwargs():
    return {
        "load_data_hook": fixtures.load_data,
        "preprocess_hook": fixtures.preprocess,
        "build_features_hook": fixtures.build_features,
        "solve_hook": fixtures.solve,
        "constraint_hook": fixtures.constraints,
        "quality_hook": passed_quality,
    }


def analysis_result(status):
    return pipeline.ResultAnalysisResult(
        tables={
            "运行配置": fixtures.run_config("analysis"),
            "分析设计": pd.DataFrame({
                "风险来源": ["结构"], "分析问题": ["形式依赖"],
                "方法": ["结构稳健性"], "指标": ["方案变化"], "通过标准": ["方案保持"],
            }),
            "结构稳健性": pd.DataFrame({
                "替代结构": ["B"], "核心设定": ["替代损失"],
                "结果指标": [2.0], "与主模型差异": [1.0],
            }),
            "结论稳定性汇总": pd.DataFrame({
                "核心结论": ["方案A"], "分析方法": ["结构稳健性"],
                "稳定范围": ["维护夹具"], "是否保持": [status == "passed"],
            }),
        },
        status=status,
        methods=("结构稳健性",),
        reason="维护证据，不是数学审批",
        restart_phase="model_design",
    )


def file_snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


class TestTemplateStateIsolation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = fixtures.config(self.root)
        self.state_path = self.root / "state/project_state.yaml"
        self.state_path.parent.mkdir()
        # Opaque policy/approval bytes must neither be interpreted nor rewritten by
        # this mathematical skeleton. Formal admission remains outside this fixture.
        self.state_path.write_bytes((
            "# preserve comments and CRLF\r\n"
            "state_generation: 17\r\n"
            "execution: {solver_backend: matlab, solver_selection_reason: 已确认}\r\n"
            "subproblems:\r\n"
            "  Q1: {model_approval_status: approved, semantic_revision: 8}\r\n"
            "  Q2: {status: solved, result_quality_status: passed}\r\n"
        ).encode("utf-8"))
        self.state_bytes = self.state_path.read_bytes()
        self.framework_bytes = self.config.framework_path.read_bytes()

    def run_primary(self, **overrides):
        kwargs = primary_kwargs()
        kwargs.update(overrides)
        return pipeline.run_primary_pipeline(self.config, **kwargs)

    def assert_control_unchanged(self):
        self.assertEqual(self.state_path.read_bytes(), self.state_bytes)
        self.assertEqual(self.config.framework_path.read_bytes(), self.framework_bytes)

    def test_primary_success_writes_workbook_not_state_or_framework(self):
        before = file_snapshot(self.root)
        result = self.run_primary()
        tables = read_workbook_tables(result.solution_path)
        self.assertEqual(float(tables["核心指标"].loc[0, "数值"]), 1.0)
        self.assertTrue(bool(tables["主结果质量门"].loc[0, "是否通过"]))
        self.assert_control_unchanged()
        self.assertEqual(set(file_snapshot(self.root)) - set(before), {"问题一求解/问题一求解结果.xlsx"})

    def test_primary_failure_preserves_failed_evidence_not_state(self):
        def failed(context, constraints):
            return pd.DataFrame({"检查项": ["收敛"], "是否通过": [False], "证据": ["迭代上限"]})
        with self.assertRaisesRegex(RuntimeError, "失败证据已写入"):
            self.run_primary(quality_hook=failed)
        table = read_workbook_tables(self.root / "问题一求解/问题一求解结果.xlsx")["主结果质量门"]
        self.assertFalse(bool(table.loc[0, "是否通过"]))
        self.assertEqual(table.loc[0, "证据"], "迭代上限")
        self.assert_control_unchanged()

    def test_primary_without_state_does_not_create_state_directory(self):
        self.state_path.unlink()
        self.state_path.parent.rmdir()
        result = self.run_primary()
        self.assertTrue(result.solution_path.is_file())
        self.assertFalse(self.state_path.parent.exists())
        self.assertEqual(self.config.framework_path.read_bytes(), self.framework_bytes)

    def test_opaque_state_bytes_are_not_read_or_reformatted(self):
        for value in (b"", b"[malformed YAML", b"\xff\x00opaque-state"):
            with self.subTest(value=value):
                self.state_path.write_bytes(value)
                result = self.run_primary()
                self.assertTrue(result.solution_path.is_file())
                self.assertEqual(self.state_path.read_bytes(), value)
                self.assertEqual(self.config.framework_path.read_bytes(), self.framework_bytes)

    def test_external_state_update_during_hook_is_not_overwritten(self):
        updated = self.state_bytes + b"# externally revised without template ownership\r\n"
        def load(config, audit):
            self.state_path.write_bytes(updated)
            return fixtures.load_data(config, audit)
        self.run_primary(load_data_hook=load)
        self.assertEqual(self.state_path.read_bytes(), updated)
        self.assertEqual(self.config.framework_path.read_bytes(), self.framework_bytes)

    def test_external_framework_update_during_hook_is_not_overwritten(self):
        updated = self.framework_bytes + "\n人工补充的当前口径\n".encode("utf-8")
        def quality(context, constraints):
            self.config.framework_path.write_bytes(updated)
            return passed_quality(context, constraints)
        self.run_primary(quality_hook=quality)
        self.assertEqual(self.config.framework_path.read_bytes(), updated)
        self.assertEqual(self.state_path.read_bytes(), self.state_bytes)

    def test_all_math_hook_errors_leave_control_plane_and_outputs_unchanged(self):
        before = file_snapshot(self.root)
        for hook in primary_kwargs():
            with self.subTest(hook=hook):
                with self.assertRaisesRegex(ValueError, "isolated hook failure"):
                    self.run_primary(**{hook: mock.Mock(side_effect=ValueError("isolated hook failure"))})
                self.assertEqual(file_snapshot(self.root), before)

    def test_workbook_write_failure_does_not_trigger_state_fallback(self):
        with mock.patch.object(pipeline, "write_workbook", side_effect=OSError("disk failure")):
            with self.assertRaisesRegex(OSError, "disk failure"):
                self.run_primary()
        self.assert_control_unchanged()
        self.assertFalse((self.root / "问题一求解/问题一求解结果.xlsx").exists())

    def test_invalid_quality_table_is_blocked_without_control_write(self):
        for table in (pd.DataFrame(), pd.DataFrame(columns=["检查项", "是否通过", "证据"])):
            with self.subTest(columns=list(table.columns)):
                with self.assertRaises(ValueError):
                    self.run_primary(quality_hook=mock.Mock(return_value=table))
                self.assert_control_unchanged()
                self.assertFalse((self.root / "问题一求解/问题一求解结果.xlsx").exists())

    def assert_analysis_outcome(self, status):
        primary = self.run_primary()
        primary_bytes = primary.solution_path.read_bytes()
        analysis_path = self.root / "问题一求解/问题一结果深化分析.xlsx"
        hook = mock.Mock(return_value=analysis_result(status))
        if status == "passed":
            self.assertEqual(pipeline.run_result_analysis_pipeline(primary, analysis_hook=hook), analysis_path)
        else:
            expected = "结果深化分析未通过" if status == "failed" else "回退到 model_design"
            with self.assertRaisesRegex(RuntimeError, expected) as captured:
                pipeline.run_result_analysis_pipeline(primary, analysis_hook=hook)
            self.assertNotIn("已标记", str(captured.exception))
        hook.assert_called_once_with(primary)
        tables = read_workbook_tables(analysis_path)
        self.assertEqual(float(tables["结构稳健性"].loc[0, "结果指标"]), 2.0)
        self.assertEqual(bool(tables["结论稳定性汇总"].loc[0, "是否保持"]), status == "passed")
        self.assertEqual(primary.solution_path.read_bytes(), primary_bytes)
        self.assert_control_unchanged()

    def test_historical_analysis_passed_writes_only_analysis_workbook(self):
        self.assert_analysis_outcome("passed")

    def test_historical_analysis_failed_keeps_evidence_without_state_promotion(self):
        self.assert_analysis_outcome("failed")

    def test_historical_analysis_redo_keeps_evidence_without_claiming_stale_written(self):
        self.assert_analysis_outcome("redo_required")

    def test_historical_analysis_hook_error_preserves_primary_and_control(self):
        primary = self.run_primary()
        before = file_snapshot(self.root)
        with self.assertRaisesRegex(ValueError, "analysis hook failure"):
            pipeline.run_result_analysis_pipeline(primary, analysis_hook=mock.Mock(side_effect=ValueError("analysis hook failure")))
        self.assertEqual(file_snapshot(self.root), before)

    def test_local_failed_primary_quality_blocks_historical_analysis_hook(self):
        primary = self.run_primary()
        invalid = dataclasses.replace(primary, quality_report=pd.DataFrame({"检查项": ["失败"], "是否通过": [False], "证据": ["维护"]}))
        hook = mock.Mock(return_value=analysis_result("passed"))
        before = file_snapshot(self.root)
        with self.assertRaisesRegex(RuntimeError, "禁止进入"):
            pipeline.run_result_analysis_pipeline(invalid, analysis_hook=hook)
        hook.assert_not_called()
        self.assertEqual(file_snapshot(self.root), before)

    def test_obsolete_primary_framework_hook_fails_before_computation(self):
        hooks = {name: mock.Mock() for name in primary_kwargs()}
        sync = mock.Mock()
        before = file_snapshot(self.root)
        with self.assertRaisesRegex(TypeError, "framework_sync_hook"):
            pipeline.run_primary_pipeline(self.config, framework_sync_hook=sync, **hooks)
        for hook in [*hooks.values(), sync]:
            hook.assert_not_called()
        self.assertEqual(file_snapshot(self.root), before)

    def test_obsolete_analysis_framework_hook_fails_before_computation(self):
        primary = self.run_primary()
        analysis, sync = mock.Mock(), mock.Mock()
        before = file_snapshot(self.root)
        with self.assertRaisesRegex(TypeError, "framework_sync_hook"):
            pipeline.run_result_analysis_pipeline(primary, analysis_hook=analysis, framework_sync_hook=sync)
        analysis.assert_not_called()
        sync.assert_not_called()
        self.assertEqual(file_snapshot(self.root), before)

    def test_retired_combined_runner_rejects_before_any_hook_or_write(self):
        before = file_snapshot(self.root)
        hooks = {name: mock.Mock() for name in (*primary_kwargs(), "analysis_hook", "framework_sync_hook")}
        with self.assertRaisesRegex(RuntimeError, "已退出活动接口"):
            pipeline.run_pipeline(self.config, **hooks)
        for hook in hooks.values():
            hook.assert_not_called()
        self.assertEqual(file_snapshot(self.root), before)

    def test_package_exports_only_primary_runner(self):
        package = importlib.import_module("hsk_pipeline")
        self.assertIn("run_primary_pipeline", package.__all__)
        for name in ("run_pipeline", "run_result_analysis_pipeline"):
            self.assertNotIn(name, package.__all__)
            self.assertFalse(hasattr(package, name))
        for runner in (pipeline.run_primary_pipeline, pipeline.run_result_analysis_pipeline):
            self.assertNotIn("framework_sync_hook", inspect.signature(runner).parameters)

    def test_pipeline_has_no_state_or_framework_writer_helpers(self):
        tree = ast.parse((PACKAGE / "main_pipeline.py").read_text(encoding="utf-8"))
        names = {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
        forbidden = {"_load_state", "_write_state", "_update_primary_state", "_update_analysis_state", "sync_primary_framework", "sync_analysis_framework"}
        self.assertFalse(names & forbidden)
        calls = {node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        self.assertFalse(calls & {"safe_dump", "write_text", "write_bytes"})

    def test_five_starters_bind_to_current_primary_signature(self):
        for name in STARTERS:
            with self.subTest(starter=name):
                module = importlib.import_module(f"starter.{name}")
                with mock.patch.object(module, "build_config", return_value=self.config), mock.patch.object(module, "run_primary_pipeline", autospec=True) as runner:
                    module.main()
                runner.assert_called_once()
                inspect.signature(pipeline.run_primary_pipeline).bind(*runner.call_args.args, **runner.call_args.kwargs)
                self.assertNotIn("framework_sync_hook", runner.call_args.kwargs)
        self.assert_control_unchanged()

    def test_missing_package_dependency_is_not_masked_by_global_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            copied = root / "copied_pipeline"
            shutil.copytree(PACKAGE, copied, ignore=shutil.ignore_patterns("__pycache__"))
            (copied / "workbook_validation.py").unlink()
            (root / "result_io.py").write_text(
                "from pathlib import Path\nPath('fallback_used').write_text('bad')\n"
                "def find_project_root(*args): pass\ndef workbook_paths(*args): pass\ndef write_workbook(*args, **kwargs): pass\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            run = subprocess.run([sys.executable, "-B", "-c", "import copied_pipeline"], cwd=root, env=env, capture_output=True, text=True, timeout=45)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn("workbook_validation", run.stderr)
            self.assertFalse((root / "fallback_used").exists())

    def test_historical_flat_import_is_explicit_and_has_no_outputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("main_pipeline.py", "result_io.py", "workbook_validation.py"):
                shutil.copy2(PACKAGE / name, root / name)
            before = file_snapshot(root)
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            run = subprocess.run([sys.executable, "-B", "-c", "import main_pipeline; assert callable(main_pipeline.run_primary_pipeline)"], cwd=root, env=env, capture_output=True, text=True, timeout=45)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(file_snapshot(root), before)


if __name__ == "__main__":
    unittest.main()
