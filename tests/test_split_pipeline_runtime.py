import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
PIPELINE_ROOT = ROOT / "templates" / "code"
if str(PIPELINE_ROOT) not in sys.path:
    sys.path.insert(0, str(PIPELINE_ROOT))

from hsk_pipeline import (  # noqa: E402
    PipelineConfig,
    ResultAnalysisResult,
    REQUIRED_CAPABILITIES,
    run_primary_pipeline,
)
from hsk_pipeline.result_io import read_workbook_tables, validate_answer_tables, write_workbook  # noqa: E402
# Explicit historical in-memory adapter, not the current package-level 03B API.
from hsk_pipeline.main_pipeline import AuditLog, build_solution_tables, run_result_analysis_pipeline  # noqa: E402


def framework_text() -> str:
    return "# 模型论文框架\n\n> 本文件只保留当前有效版本。\n\n### Q1：测试\n"


def config(root: Path) -> PipelineConfig:
    framework = root / "模型论文框架.md"
    framework.write_text(framework_text(), encoding="utf-8")
    return PipelineConfig(
        project_root=root,
        framework_path=framework,
        framework_section="### Q1：测试",
        problem_name="问题一",
        objective="optimization",
        structures=(),
        capabilities={name: False for name in REQUIRED_CAPABILITIES},
    )


def load_data(cfg, audit):
    return {"原始数据": pd.DataFrame({"x": [1.0]})}


def preprocess(raw, cfg, audit):
    return raw


def build_features(clean, cfg):
    return {"x": 1.0}


def run_config(stage):
    return pd.DataFrame({"项目": ["execution_owner", "execution_profile", "stage"], "值": ["user", "full_fidelity", stage]})


def solve(features, cfg):
    return {
        "运行配置": run_config("primary"),
        "核心指标": pd.DataFrame({"指标": ["目标值"], "数值": [1.0]}),
        "推荐方案": pd.DataFrame({"方案": ["A"]}),
    }


def constraints(solution, cfg):
    return None


def station_observations(ties=False):
    rows = [("A", 1, 3), ("A", 2, 9), ("A", 3, 4), ("B", 1, 2), ("B", 4, 7), ("B", 5, 1)]
    if ties:
        rows.extend([("A", 5, 9), ("B", 6, 7)])
    return pd.DataFrame(rows, columns=["站点", "时刻", "观测值"])


def solve_stations(features, cfg):
    observations = features["观测"]
    maxima = observations.groupby("站点")["观测值"].transform("max")
    peaks = observations.loc[observations["观测值"].eq(maxima)].copy()
    peaks = peaks.rename(columns={"观测值": "峰值"})
    peaks["记录键"] = peaks["站点"] + "@" + peaks["时刻"].astype(str)
    events = []
    for station, group in observations.groupby("站点"):
        triggered = group.loc[group["观测值"].ge(10), "时刻"]
        events.append({"站点": station, "事件时刻": None if triggered.empty else triggered.min(),
                       "状态": "未触发" if triggered.empty else "已触发",
                       "原因": "未达到阈值10" if triggered.empty else "首次达到阈值10"})
    return {
        "运行配置": run_config("primary"),
        "核心指标": pd.DataFrame({"指标": ["观测总量"], "数值": [observations["观测值"].sum()]}),
        "推荐方案": pd.DataFrame({"方案": ["保留各站全部并列峰值"]}),
        "站点峰值": peaks,
        "站点事件": pd.DataFrame(events),
        "执行停止证据": pd.DataFrame({"迭代或样本数": [len(observations)], "指标": ["已处理观测"],
                                    "数值": [len(observations)], "单位": ["条"]}),
    }


def station_quality(context, checked):
    expected = {}
    total = 0
    for station, time, value in context.raw_data["观测"].itertuples(index=False, name=None):
        total += value
        if station not in expected or value > expected[station][0]:
            expected[station] = (value, [time])
        elif value == expected[station][0]:
            expected[station][1].append(time)
    wanted = {(station, time, value) for station, (value, times) in expected.items() for time in times}
    peaks = context.solution.get("站点峰值")
    actual = set()
    complete = isinstance(peaks, pd.DataFrame) and {"站点", "时刻", "峰值"}.issubset(peaks.columns)
    if complete:
        complete = not peaks[["站点", "时刻", "峰值"]].isna().any().any()
        actual = set(peaks[["站点", "时刻", "峰值"]].itertuples(index=False, name=None))
        complete = bool(complete and actual == wanted and len(peaks) == len(wanted))
    total_matches = context.solution["核心指标"].iloc[0]["数值"] == total
    return pd.DataFrame({"检查项": ["各站峰值及全部发生时刻", "观测总量"],
                         "是否通过": [complete, bool(total_matches)],
                         "证据": [f"原始观测独立重算: {sorted(wanted)}", f"逐条求和: {total}"]})


class TestSplitPipelineRuntime(unittest.TestCase):
    def run_stations(self, root, *, ties=False, mutate=None, answer_sheets=("站点峰值", "站点事件")):
        def load(cfg, audit):
            audit.record("Info", "缺失时刻", "未触发事件的时刻为空；必答峰值时刻缺失由质量门报告", "按事件状态记录")
            return {"观测": station_observations(ties)}

        def solver(features, cfg):
            result = solve_stations(features, cfg)
            if mutate is not None:
                mutate(result)
            return result

        return run_primary_pipeline(
            config(root), load_data_hook=load, preprocess_hook=preprocess,
            build_features_hook=lambda clean, cfg: clean, solve_hook=solver,
            constraint_hook=constraints, quality_hook=station_quality, answer_sheets=answer_sheets,
        )

    def test_declared_answers_and_stopping_evidence_round_trip_through_primary(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            primary = self.run_stations(root)
            tables = read_workbook_tables(primary.solution_path)
            self.assertEqual(list(tables), ["运行配置", "核心指标", "数据审计", "主结果质量门",
                                            "推荐方案", "执行停止证据", "站点峰值", "站点事件"])
            actual = list(tables["站点峰值"][["站点", "峰值", "时刻"]].itertuples(index=False, name=None))
            self.assertEqual(actual, [("A", 9, 2), ("B", 7, 4)])
            self.assertEqual(tables["核心指标"].loc[0, "数值"], 26)
            self.assertEqual(tables["执行停止证据"].loc[0, "数值"], 6)
            events = tables["站点事件"]
            self.assertEqual(list(events["站点"]), ["A", "B"])
            self.assertTrue(events["事件时刻"].isna().all())
            self.assertEqual(list(events["状态"]), ["未触发", "未触发"])
            self.assertEqual(list(events["原因"]), ["未达到阈值10", "未达到阈值10"])
            direct = root / "direct.xlsx"
            validate_answer_tables(tables, ("站点峰值", "站点事件"))
            write_workbook(direct, tables, workbook_kind="solution")
            pd.testing.assert_frame_equal(read_workbook_tables(direct)["站点峰值"], tables["站点峰值"])

    def test_all_tied_peak_times_are_retained(self):
        with tempfile.TemporaryDirectory() as temp:
            primary = self.run_stations(Path(temp), ties=True)
            peaks = read_workbook_tables(primary.solution_path)["站点峰值"]
            actual = set(peaks[["站点", "峰值", "时刻"]].itertuples(index=False, name=None))
            self.assertEqual(actual, {("A", 9, 2), ("A", 9, 5), ("B", 7, 4), ("B", 7, 6)})
            self.assertTrue(peaks["记录键"].is_unique)
            with self.assertRaisesRegex(RuntimeError, "失败证据已写入"):
                self.run_stations(Path(temp), ties=True, mutate=lambda result: result.update(
                    {"站点峰值": result["站点峰值"].drop_duplicates("站点")}
                ))

    def test_wrong_station_time_and_missing_required_time_fail_independent_quality(self):
        def wrong_station(result):
            result["站点峰值"].loc[result["站点峰值"]["站点"].eq("B"), "站点"] = "C"

        def swapped_times(result):
            result["站点峰值"]["时刻"] = [4, 2]

        def missing_time(result):
            result["站点峰值"].loc[result["站点峰值"]["站点"].eq("B"), "时刻"] = None

        for mutation in (wrong_station, swapped_times, missing_time):
            with self.subTest(mutation=mutation.__name__), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                with self.assertRaisesRegex(RuntimeError, "失败证据已写入"):
                    self.run_stations(root, mutate=mutation)
                tables = read_workbook_tables(root / "问题一求解/问题一求解结果.xlsx")
                self.assertFalse(bool(tables["主结果质量门"].loc[0, "是否通过"]))
                self.assertEqual(len(tables["站点峰值"]), 2)

    def test_missing_answer_does_not_overwrite_passed_workbook(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            primary = self.run_stations(root)
            original = primary.solution_path.read_bytes()
            with self.assertRaisesRegex(ValueError, "缺少必答结果表.*额外答案"):
                self.run_stations(root, answer_sheets=("站点峰值", "额外答案"))
            self.assertEqual(primary.solution_path.read_bytes(), original)

    def test_failed_quality_with_missing_answer_keeps_available_diagnostics(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(RuntimeError, "失败证据已写入.*缺少必答结果表.*站点峰值"):
                self.run_stations(root, mutate=lambda result: result.pop("站点峰值"))
            tables = read_workbook_tables(root / "问题一求解/问题一求解结果.xlsx")
            self.assertNotIn("站点峰值", tables)
            self.assertIn("站点事件", tables)
            self.assertEqual(tables["执行停止证据"].loc[0, "数值"], 6)
            self.assertFalse(bool(tables["主结果质量门"].loc[0, "是否通过"]))

    def test_standard_answer_sources_cannot_be_replaced_by_solver_tables(self):
        audit = AuditLog()
        audit.record("Info", "真实审计", "来自输入", "保留")
        quality = pd.DataFrame({"检查项": ["真实检查"], "是否通过": [True], "证据": ["实算"]})
        checked = pd.DataFrame({"约束编号": ["C1"], "约束含义": ["非负"], "违反量": [0],
                                "容差": [0], "是否满足": [True]})
        solution = solve({}, None)
        for name in ("数据审计", "主结果质量门", "约束违反检查"):
            solution[name] = pd.DataFrame({"伪造": [1]})
        solution["未声明答案"] = pd.DataFrame({"值": [9]})
        names = ("核心指标", "数据审计", "主结果质量门", "约束违反检查", "推荐方案")
        tables = build_solution_tables(solution, checked, quality, audit, answer_sheets=names)
        self.assertEqual(list(tables), ["运行配置", "核心指标", "数据审计", "主结果质量门", "推荐方案", "约束违反检查"])
        self.assertEqual(tables["数据审计"], audit.table())
        self.assertIs(tables["主结果质量门"], quality)
        self.assertIs(tables["约束违反检查"], checked)
        self.assertNotIn("未声明答案", tables)
        with self.assertRaisesRegex(ValueError, "缺少必答结果表.*约束违反检查"):
            build_solution_tables(solution, None, quality, audit, answer_sheets=("约束违反检查",))
        with self.assertRaisesRegex(ValueError, "标准表冲突"):
            build_solution_tables(solution, None, quality, audit, answer_sheets=("pareto结果",))

    def test_registered_answer_extension_uses_override_schema_columns(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            schema = yaml.safe_load((ROOT / "core/workbook_schema.yaml").read_text(encoding="utf-8"))
            schema["solution_workbook"]["common_recommended_sheets"]["站点峰值"] = {
                "required_columns": ["记录键", "站点", "峰值", "时刻"],
            }
            schema_path = root / "workbook_schema.yaml"
            schema_path.write_text(yaml.safe_dump(schema, allow_unicode=True), encoding="utf-8")
            with patch.dict(os.environ, {"HSK_WORKBOOK_SCHEMA": str(schema_path)}):
                primary = self.run_stations(root)
                peaks = read_workbook_tables(primary.solution_path)["站点峰值"]
                self.assertEqual(list(peaks[["站点", "峰值", "时刻"]].itertuples(index=False, name=None)),
                                 [("A", 9, 2), ("B", 7, 4)])
                original = primary.solution_path.read_bytes()
                with self.assertRaisesRegex(ValueError, "站点峰值.*缺少必需字段.*记录键"):
                    self.run_stations(root, mutate=lambda result: result.update(
                        {"站点峰值": result["站点峰值"].drop(columns=["记录键"])}
                    ))
                self.assertEqual(primary.solution_path.read_bytes(), original)

    def test_primary_run_uses_numerical_inputs_without_reading_framework(self):
        for framework_bytes in (None, b"unrelated project notes", b"\xff\xfe"):
            with self.subTest(framework_bytes=framework_bytes), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                cfg = config(root)
                if framework_bytes is None:
                    cfg.framework_path.unlink()
                else:
                    cfg.framework_path.write_bytes(framework_bytes)

                result = run_primary_pipeline(
                    cfg,
                    load_data_hook=load_data,
                    preprocess_hook=preprocess,
                    build_features_hook=build_features,
                    solve_hook=solve,
                    constraint_hook=constraints,
                    quality_hook=lambda context, checked: pd.DataFrame(
                        {"检查项": ["目标值"], "是否通过": [True], "证据": ["1.0"]}
                    ),
                )
                tables = read_workbook_tables(result.solution_path)
                self.assertEqual(float(tables["核心指标"].loc[0, "数值"]), 1.0)
                self.assertEqual(result.solution_path, root / "问题一求解/问题一求解结果.xlsx")
                if framework_bytes is not None:
                    self.assertEqual(cfg.framework_path.read_bytes(), framework_bytes)
                else:
                    self.assertFalse(cfg.framework_path.exists())

    def test_failed_primary_quality_is_written_before_blocking(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cfg = config(root)

            def quality(context, checked):
                return pd.DataFrame(
                    {"检查项": ["收敛"], "是否通过": [False], "证据": ["迭代上限"]}
                )

            with self.assertRaisesRegex(RuntimeError, "失败证据已写入"):
                run_primary_pipeline(
                    cfg,
                    load_data_hook=load_data,
                    preprocess_hook=preprocess,
                    build_features_hook=build_features,
                    solve_hook=solve,
                    constraint_hook=constraints,
                    quality_hook=quality,
                )
            workbook = root / "问题一求解/问题一求解结果.xlsx"
            self.assertTrue(workbook.is_file())
            quality_table = read_workbook_tables(workbook)["主结果质量门"]
            self.assertFalse(bool(quality_table.loc[0, "是否通过"]))

    def test_redo_required_persists_analysis_without_mutating_state(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cfg = config(root)
            state_dir = root / "state"
            state_dir.mkdir()
            state = {
                "project": {"current_phase": "result_analysis"},
                "subproblems": {
                    "Q1": {
                        "status": "solved",
                        "result_quality_status": "passed",
                        "result_analysis_status": "pending",
                        "result_summary_status": "current",
                        "result_summary_anchor": "### Q1：测试",
                        "framework_section": "### Q1：测试",
                        "artifacts_stale": False,
                        "stale_layers": [],
                        "proposition_refs": [],
                        "artifact_hashes": {},
                        "validated_artifact_hashes": {},
                    }
                },
                "paper_framework": {"sync_status": "current"},
            }
            state_path = state_dir / "project_state.yaml"
            state_path.write_text("# keep original state bytes\n" + yaml.safe_dump(state, allow_unicode=True), encoding="utf-8")
            original_state = state_path.read_bytes()
            original_framework = cfg.framework_path.read_bytes()

            def quality(context, checked):
                return pd.DataFrame(
                    {"检查项": ["收敛"], "是否通过": [True], "证据": ["通过"]}
                )

            primary = run_primary_pipeline(
                cfg,
                load_data_hook=load_data,
                preprocess_hook=preprocess,
                build_features_hook=build_features,
                solve_hook=solve,
                constraint_hook=constraints,
                quality_hook=quality,
            )

            tables = {
                "运行配置": run_config("analysis"),
                "分析设计": pd.DataFrame(
                    {
                        "风险来源": ["结构"],
                        "分析问题": ["结论是否依赖模型形式"],
                        "方法": ["结构稳健性"],
                        "指标": ["方案变化"],
                        "通过标准": ["方案保持"],
                    }
                ),
                "结构稳健性": pd.DataFrame(
                    {
                        "替代结构": ["B"],
                        "核心设定": ["替代损失"],
                        "结果指标": [2.0],
                        "与主模型差异": [1.0],
                    }
                ),
                "结论稳定性汇总": pd.DataFrame(
                    {
                        "核心结论": ["方案A最优"],
                        "分析方法": ["结构稳健性"],
                        "稳定范围": ["仅主结构"],
                        "是否保持": [False],
                    }
                ),
            }

            def analyze(result):
                return ResultAnalysisResult(
                    tables=tables,
                    status="redo_required",
                    methods=("结构稳健性",),
                    reason="替代结构改变最优方案",
                    restart_phase="model_design",
                )

            with self.assertRaisesRegex(RuntimeError, "回退到 model_design"):
                run_result_analysis_pipeline(
                    primary,
                    analysis_hook=analyze,
                )
            analysis_path = root / "问题一求解/问题一结果深化分析.xlsx"
            self.assertTrue(analysis_path.is_file())
            tables_returned = read_workbook_tables(analysis_path)
            self.assertFalse(bool(tables_returned["结论稳定性汇总"].loc[0, "是否保持"]))
            self.assertEqual(float(tables_returned["结构稳健性"].loc[0, "结果指标"]), 2.0)
            # The authorized breaking change removes task-template state ownership.
            # Control-plane stale propagation is tested in transactional-writer suites.
            self.assertEqual(state_path.read_bytes(), original_state)
            self.assertEqual(cfg.framework_path.read_bytes(), original_framework)


if __name__ == "__main__":
    unittest.main()
