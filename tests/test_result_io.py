import sys
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import pandas as pd
import openpyxl

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from templates.code.hsk_pipeline import result_io as MOD



class TestResultIO(unittest.TestCase):
    def test_captured_workbook_bytes_share_the_file_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.xlsx"
            MOD.write_workbook(path, self.solution_tables())
            raw = path.read_bytes()
            validator = MOD.WORKBOOK_VALIDATION
            schema = MOD.load_workbook_schema()
            from_file = validator.validate_workbook_file(path, "solution", schema=schema)
            from_bytes = validator.validate_workbook_file(raw, "solution", schema=schema)
            self.assertEqual([name for name, _ in from_file], [name for name, _ in from_bytes])
            for (_, file_table), (_, byte_table) in zip(from_file, from_bytes):
                pd.testing.assert_frame_equal(file_table, byte_table)
            book = openpyxl.load_workbook(io.BytesIO(raw))
            del book["核心指标"]
            buffer = io.BytesIO()
            book.save(buffer)
            book.close()
            with self.assertRaisesRegex(ValueError, "核心指标"):
                validator.validate_workbook_file(buffer.getvalue(), "solution", schema=schema)

    def test_empty_trailing_header_only_ignores_an_unused_column(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.xlsx"
            MOD.write_workbook(path, self.solution_tables())
            book = openpyxl.load_workbook(path)
            book["核心指标"].cell(1, 3).number_format = "0.000"
            book.save(path)
            MOD.validate_workbook_file(path, "solution")
            book["核心指标"].cell(2, 3, 99.0)
            book.save(path)
            book.close()
            with self.assertRaisesRegex(ValueError, "空字段名"):
                MOD.validate_workbook_file(path, "solution")

    def quality_table(self):
        return pd.DataFrame(
            {"检查项": ["收敛"], "是否通过": [True], "证据": ["达到终止条件"]}
        )

    def run_config(self, stage="primary"):
        return pd.DataFrame({"项目": ["execution_owner", "execution_profile", "stage"], "值": ["user", "full_fidelity", stage]})

    def solution_tables(self):
        return {
            "运行配置": self.run_config("primary"),
            "核心指标": pd.DataFrame({"指标": ["目标值"], "数值": [1.0]}),
            "数据审计": pd.DataFrame(
                {"等级": ["Info"], "检查项": ["字段"], "信息": ["通过"], "处理方式": ["无"]}
            ),
            "主结果质量门": self.quality_table(),
        }

    def analysis_tables(self):
        return {
            "运行配置": self.run_config("analysis"),
            "分析设计": pd.DataFrame(
                {
                    "风险来源": ["局部最优"],
                    "分析问题": ["算法是否偶然"],
                    "方法": ["多算法一致性"],
                    "指标": ["目标值差异"],
                    "通过标准": ["差异小于1%"],
                }
            ),
            "算法一致性": pd.DataFrame(
                {"算法": ["A"], "重复编号": [1], "目标值": [1.0], "是否可行": [True]}
            ),
            "结论稳定性汇总": pd.DataFrame(
                {"核心结论": ["方案A最优"], "分析方法": ["算法一致性"], "稳定范围": ["三种算法"], "是否保持": [True]}
            ),
        }

    def all_capabilities(self, **updates):
        values = {
            "has_explicit_constraints": False,
            "requires_feasibility_check": False,
            "requires_equilibrium_residual": False,
            "requires_conservation_residual": False,
            "requires_discretization_check": False,
            "requires_convergence_diagnostic": False,
            "requires_out_of_sample_validation": False,
            "requires_uncertainty_quantification": False,
            "requires_leakage_check": False,
            "requires_calibration_check": False,
            "requires_identifiability_check": False,
        }
        values.update(updates)
        return values

    def test_paths_and_workbooks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            solve, analysis = MOD.workbook_paths(root, "问题一")
            self.assertEqual(solve.relative_to(root).as_posix(), "问题一求解/问题一求解结果.xlsx")
            self.assertEqual(analysis.relative_to(root).as_posix(), "问题一求解/问题一结果深化分析.xlsx")
            MOD.write_workbook(solve, self.solution_tables())
            MOD.write_workbook(analysis, self.analysis_tables())
            self.assertTrue(solve.exists())
            self.assertTrue(analysis.exists())

    def test_project_root_defaults_to_script_directory_on_first_run(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / "问题一求解"
            folder.mkdir()
            script = folder / "问题一求解.py"
            script.write_text("", encoding="utf-8")
            self.assertEqual(MOD.find_project_root(script), Path(directory).resolve())

    def test_empty_worksheet_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.xlsx"
            with self.assertRaisesRegex(ValueError, "禁止写入空工作表"):
                MOD.write_workbook(path, {"参数敏感性": pd.DataFrame()})

    def test_required_columns_are_enforced(self):
        tables = self.solution_tables()
        tables["核心指标"] = pd.DataFrame({"结果": [1.0]})
        with self.assertRaisesRegex(ValueError, "缺少必需字段"):
            MOD.validate_workbook_tables(tables, "solution")

    def test_only_logical_quality_row_may_omit_unit_without_audit(self):
        tables = self.solution_tables()
        tables["主结果质量门"] = pd.DataFrame({
            "检查项": ["收敛", "残差"],
            "是否通过": [True, True],
            "证据": ["达到终止条件", "由结果重算"],
            "判定关系": ["bool_true", "<="],
            "单位": [None, "1"],
        })
        MOD.validate_workbook_tables(tables, "solution")

        for row, column in ((1, "单位"), (0, "证据")):
            with self.subTest(row=row, column=column):
                invalid = {name: frame.copy() for name, frame in tables.items()}
                invalid["主结果质量门"].loc[row, column] = None
                with self.assertRaisesRegex(ValueError, "缺失值.*数据审计"):
                    MOD.validate_workbook_tables(invalid, "solution")

    def test_failed_quality_gate_is_rejected_for_downstream(self):
        tables = self.solution_tables()
        tables["主结果质量门"].loc[0, "是否通过"] = False
        with self.assertRaisesRegex(ValueError, "质量门存在未通过项"):
            MOD.validate_workbook_tables(tables, "solution")

    def test_failed_quality_gate_can_be_persisted_structurally(self):
        tables = self.solution_tables()
        tables["主结果质量门"].loc[0, "是否通过"] = False
        prepared = MOD.validate_workbook_tables(
            tables,
            "solution",
            require_quality_passed=False,
        )
        self.assertIn("主结果质量门", {name for name, _ in prepared})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "问题一求解结果.xlsx"
            MOD.write_workbook(
                path,
                tables,
                workbook_kind="solution",
                require_quality_passed=False,
            )
            self.assertTrue(path.is_file())
            with self.assertRaisesRegex(ValueError, "质量门存在未通过项"):
                MOD.validate_workbook_file(path, "solution")

    def test_legacy_optimization_fallback_requires_constraint_sheet(self):
        with self.assertRaisesRegex(ValueError, "约束违反检查"):
            MOD.validate_workbook_tables(self.solution_tables(), "solution", problem_types=("optimization",))

    def test_explicit_capabilities_override_problem_type_fallback(self):
        prepared = MOD.validate_workbook_tables(
            self.solution_tables(),
            "solution",
            problem_types=("mechanism",),
            capabilities=self.all_capabilities(),
        )
        self.assertEqual({name for name, _ in prepared}, {"运行配置", "核心指标", "数据审计", "主结果质量门"})

    def test_constraint_capability_requires_and_checks_sheet(self):
        tables = self.solution_tables()
        with self.assertRaisesRegex(ValueError, "约束违反检查"):
            MOD.validate_workbook_tables(
                tables,
                "solution",
                capabilities=self.all_capabilities(has_explicit_constraints=True),
            )
        tables["约束违反检查"] = pd.DataFrame(
            {
                "约束编号": ["C1"],
                "约束含义": ["容量"],
                "违反量": [0.0],
                "容差": [1e-8],
                "是否满足": [True],
            }
        )
        MOD.validate_workbook_tables(
            tables,
            "solution",
            capabilities=self.all_capabilities(has_explicit_constraints=True),
        )

    def test_duplicate_record_key_is_rejected(self):
        tables = self.solution_tables()
        tables["明细结果"] = pd.DataFrame({"记录键": ["A", "A"], "数值": [1.0, 2.0]})
        with self.assertRaisesRegex(ValueError, "重复值"):
            MOD.validate_workbook_tables(tables, "solution")

    def test_result_analysis_requires_plan_summary_and_substantive_sheet(self):
        with self.assertRaisesRegex(ValueError, "缺少必需工作表"):
            MOD.validate_workbook_tables(
                {"算法一致性": self.analysis_tables()["算法一致性"]},
                "result_analysis",
            )
        only_headers = {
            "运行配置": self.analysis_tables()["运行配置"],
            "分析设计": self.analysis_tables()["分析设计"],
            "结论稳定性汇总": self.analysis_tables()["结论稳定性汇总"],
        }
        with self.assertRaisesRegex(ValueError, "至少需要一个实质分析表"):
            MOD.validate_workbook_tables(only_headers, "result_analysis")
        MOD.validate_workbook_tables(self.analysis_tables(), "result_analysis")

    def test_result_analysis_rejects_unregistered_placeholder_sheet(self):
        tables = self.analysis_tables()
        tables["适用性说明"] = pd.DataFrame({"原因": ["无"]})
        with self.assertRaisesRegex(ValueError, "未登记工作表"):
            MOD.validate_workbook_tables(tables, "result_analysis")

    def test_legacy_robustness_kind_is_read_compatible(self):
        MOD.validate_workbook_tables(self.analysis_tables(), "robustness")

    def test_selected_ordinary_methods_need_each_evidence_table(self):
        tables = self.analysis_tables()
        tables["参数敏感性"] = pd.DataFrame(
            {"参数": ["a"], "基准值": [0], "变化值": [1], "结果指标": [0]}
        )
        methods = ["parameter_sensitivity", "场景压力测试"]
        with self.assertRaisesRegex(ValueError, "缺少已选择的普通证据表.*场景压力测试"):
            MOD.validate_workbook_tables(tables, "result_analysis", analysis_methods=methods)
        tables["场景压力测试"] = pd.DataFrame(
            {"场景": ["S1"], "变化条件": [" "], "结果指标": [0], "是否可行": [False]}
        )
        with self.assertRaisesRegex(ValueError, "场景压力测试.*必需字段完整的实质记录"):
            MOD.validate_workbook_tables(tables, "result_analysis", analysis_methods=methods)
        tables["场景压力测试"].loc[0, "变化条件"] = "低容量"
        tables["结论稳定性汇总"].loc[0, "是否保持"] = False
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "问题一结果深化分析.xlsx"
            MOD.write_workbook(path, tables, analysis_methods=methods)
            restored = dict(MOD.validate_workbook_file(
                path, "result_analysis", analysis_methods=["parameter_sensitivity", "scenario_stress_testing"],
            ))
        self.assertEqual(restored["场景压力测试"].iloc[0]["结果指标"], 0)
        self.assertEqual(restored["场景压力测试"].iloc[0]["是否可行"], False)

    def test_unmapped_ordinary_method_remains_compatible(self):
        MOD.validate_workbook_tables(
            self.analysis_tables(), "result_analysis", analysis_methods=["项目专用重采样检验"],
        )

    def test_standalone_fallback_has_current_ordinary_method_schema(self):
        current = MOD.load_workbook_schema()["result_analysis_workbook"]
        fallback = MOD._FALLBACK_SCHEMA["result_analysis_workbook"]
        mapping = current["ordinary_method_sheets"]
        self.assertEqual(mapping, fallback["ordinary_method_sheets"])
        self.assertFalse(set(mapping).intersection(current["comparison_method_sheets"]))
        self.assertFalse(set(mapping.values()).intersection(current["comparison_method_sheets"].values()))
        for sheet in set(mapping.values()):
            self.assertEqual(current["sheet_schemas"][sheet]["required_columns"],
                             fallback["sheet_schemas"][sheet]["required_columns"])
        for key in ("version", "observation_statuses", "dispositions"):
            self.assertEqual(current["ordinary_experiment_protocol"][key],
                             fallback["ordinary_experiment_protocol"][key])

    def ordinary_experiment_book(self):
        plan = [
            {"id": key, "method": "scenario_stress_testing", "target": f"改变{key}是否可行",
             "claim": f"{key}上升后方案仍可行"} for key in ("a", "b")
        ]
        config = self.run_config("analysis")
        config.loc[len(config)] = ["ordinary_experiment_protocol_version", "1.0.0"]
        design, detail, summary = [], [], []
        for row in plan:
            key = row["id"]
            design.append({"检验ID": key, "分析问题": row["target"], "方法": "场景压力测试",
                           "风险来源": "供给不足", "指标": "是否可行", "通过标准": "可行"})
            for change in ("低", "高"):
                detail.append({"检验ID": key, "场景": key, "变化条件": change, "结果指标": 0,
                               "是否可行": key == "a", "观测状态": "completed"})
            summary.append({"检验ID": key, "核心结论": row["claim"], "分析方法": "场景压力测试",
                            "证据工作表": "场景压力测试", "稳定范围": "测试的两种供给水平",
                            "是否保持": key == "a", "主张处置": "support" if key == "a" else "reject"})
        return plan, {"运行配置": config, "分析设计": pd.DataFrame(design),
                      "场景压力测试": pd.DataFrame(detail), "结论稳定性汇总": pd.DataFrame(summary)}

    def test_ordinary_experiments_round_trip_and_standalone_copied_package(self):
        plan, tables = self.ordinary_experiment_book()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "问题一结果深化分析.xlsx"
            MOD.write_workbook(path, tables, ordinary_experiments=plan)
            restored = dict(MOD.WORKBOOK_VALIDATION.validate_workbook_file(
                path.read_bytes(), "result_analysis", schema=MOD.load_workbook_schema(),
                ordinary_experiments=plan))
            self.assertEqual(restored["场景压力测试"]["结果指标"].tolist(), [0] * 4)
            self.assertEqual(restored["场景压力测试"]["是否可行"].tolist(), [True, True, False, False])
            for name in ("result_io.py", "workbook_validation.py"):
                shutil.copy(Path(MOD.__file__).with_name(name), root / name)
            program = """
import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
os.environ.pop("HSK_WORKBOOK_SCHEMA", None)
import result_io
assert result_io.load_workbook_schema() is result_io._FALLBACK_SCHEMA
plan = json.loads(sys.argv[2])
path = Path(sys.argv[1])
tables = dict(result_io.validate_workbook_file(path, "result_analysis", ordinary_experiments=plan))
tables["场景压力测试"] = tables["场景压力测试"].query("检验ID == 'a'")
try:
    result_io.write_workbook(path, tables, ordinary_experiments=plan)
except ValueError as exc:
    assert "b" in str(exc) and "实质观测" in str(exc), str(exc)
else:
    raise AssertionError("isolated writer accepted absent experiment b")
"""
            before = path.read_bytes()
            subprocess.run([sys.executable, "-I", "-c", program, str(path), json.dumps(plan)],
                           cwd=root, check=True, capture_output=True)
            self.assertEqual(path.read_bytes(), before)

    def test_missing_rows_are_reported_for_every_id_and_its_claim(self):
        plan, tables = self.ordinary_experiment_book()
        for name in ("分析设计", "场景压力测试", "结论稳定性汇总"):
            tables[name] = tables[name].iloc[:0]
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "partial.xlsx"
            with pd.ExcelWriter(file, engine="openpyxl") as writer:
                for name, frame in tables.items():
                    frame.to_excel(writer, sheet_name=name, index=False)
            with self.assertRaises(ValueError) as caught:
                MOD.validate_workbook_file(file, "result_analysis", ordinary_experiments=plan)
        issue = str(caught.exception)
        for row in plan:
            for missing in ("设计", "观测", "处置"):
                self.assertTrue(any(row["id"] in s and row["claim"] in s and missing in s
                                    for s in issue.split("；")), issue)

    def test_design_observation_and_claim_are_bound_to_the_same_experiment(self):
        for sheet, column, value, message in (
            ("分析设计", "分析问题", "改变a是否可行", "目标"),
            ("结论稳定性汇总", "核心结论", "a上升后方案仍可行", "主张"),
            ("结论稳定性汇总", "分析方法", "参数敏感性", "方法"),
            ("结论稳定性汇总", "证据工作表", "参数敏感性", "证据工作表"),
            ("结论稳定性汇总", "主张处置", "", "处置"),
            ("结论稳定性汇总", "主张处置", "support", "矛盾"),
            ("结论稳定性汇总", "是否保持", True, "矛盾"),
            ("场景压力测试", "观测状态", "technical_failure", "实质观测"),
            ("场景压力测试", "观测状态", "exploratory", "实质观测"),
            ("场景压力测试", "结果指标", "待填", "实质观测"),
            ("场景压力测试", "结果指标", "=A1+1", "实质观测"),
        ):
            with self.subTest(sheet=sheet, column=column, value=value):
                plan, tables = self.ordinary_experiment_book()
                tables[sheet][column] = tables[sheet][column].astype(object)
                tables[sheet].loc[tables[sheet]["检验ID"] == "b", column] = value
                with self.assertRaisesRegex(ValueError, f"b.*{message}"):
                    MOD.validate_workbook_tables(tables, "result_analysis", ordinary_experiments=plan)

    def test_uncached_excel_formula_cannot_be_the_observation(self):
        plan, tables = self.ordinary_experiment_book()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "问题一结果深化分析.xlsx"
            MOD.write_workbook(path, tables, ordinary_experiments=plan)
            book = openpyxl.load_workbook(path)
            detail = book["场景压力测试"]
            for row in detail.iter_rows(min_row=2):
                if row[0].value == "b":
                    row[3].value = "=4-4"
            book.save(path)
            book.close()
            with self.assertRaisesRegex(ValueError, "b.*实质观测"):
                MOD.validate_workbook_file(path, "result_analysis", ordinary_experiments=plan)

    def test_unregistered_ordinary_summary_cannot_claim_support(self):
        for identifier in ("c", None):
            with self.subTest(identifier=identifier):
                plan, tables = self.ordinary_experiment_book()
                summaries = tables["结论稳定性汇总"]
                extra = {**summaries.iloc[0].to_dict(), "检验ID": identifier, "核心结论": "额外主张"}
                tables["结论稳定性汇总"] = pd.concat([summaries, pd.DataFrame([extra])], ignore_index=True)
                with self.assertRaisesRegex(ValueError, "未登记.*额外主张"):
                    MOD.validate_workbook_tables(tables, "result_analysis", ordinary_experiments=plan)
                extra.update({"主张处置": None, "是否保持": None, "说明": "探索记录，结论待检验"})
                tables["结论稳定性汇总"] = pd.concat([summaries, pd.DataFrame([extra])], ignore_index=True)
                MOD.validate_workbook_tables(tables, "result_analysis", ordinary_experiments=plan)

    def test_optional_technical_failure_does_not_acquit_a_required_id(self):
        plan, tables = self.ordinary_experiment_book()
        plan[1]["required"] = False
        rows = tables["场景压力测试"]
        rows.loc[rows["检验ID"] == "b", "观测状态"] = "technical_failure"
        rows.loc[rows["检验ID"] == "b", "结果指标"] = None
        tables["结论稳定性汇总"] = tables["结论稳定性汇总"].iloc[:1]
        MOD.validate_workbook_tables(tables, "result_analysis", ordinary_experiments=plan)
        rows.loc[rows["检验ID"] == "a", "观测状态"] = "exploratory"
        with self.assertRaisesRegex(ValueError, "a.*实质观测"):
            MOD.validate_workbook_tables(tables, "result_analysis", ordinary_experiments=plan)

    def test_source_plan_rejects_duplicate_or_wrong_method_and_false_flags(self):
        plan, _ = self.ordinary_experiment_book()
        check = MOD.WORKBOOK_VALIDATION.ordinary_experiment_plan_issues
        schema = MOD.load_workbook_schema()
        self.assertFalse(check(plan, schema=schema, analysis_methods=["场景压力测试"]))
        for changes in ({"id": "a"}, {"method": "多模型检验"}, {"required": "false"},
                        {"claim": "   "}, {"target": "待填"}, {"require": False}):
            with self.subTest(changes=changes):
                self.assertTrue(check([plan[0], {**plan[1], **changes}], schema=schema))
        self.assertTrue(check(plan, schema=schema, analysis_methods=["异质性分析"]))

    def test_selected_comparison_cannot_be_replaced_by_legacy_algorithm_table(self):
        with self.assertRaisesRegex(ValueError, "缺少已选择的比较证据表"):
            MOD.validate_workbook_tables(self.analysis_tables(), "result_analysis", analysis_methods=["多模型检验"])
        with self.assertRaisesRegex(ValueError, "同模型多算法检验"):
            MOD.validate_workbook_tables(self.analysis_tables(), "result_analysis", comparison_plan={
                "checks": [{"kind": "algorithm_comparison", "requirement": "required"}]})

    def test_comparison_tables_require_finite_numeric_values_and_unique_keys(self):
        tables = self.analysis_tables()
        columns = MOD.load_workbook_schema()["result_analysis_workbook"]["sheet_schemas"]["多模型检验"]["required_columns"]
        record = dict.fromkeys(columns, "declared")
        record.update({"记录键": "R1", "主模型数值": 16.0, "对照模型数值": 11.0, "差异": -5.0, "判定": True})
        tables["多模型检验"] = pd.DataFrame([record])
        MOD.validate_workbook_tables(tables, "result_analysis", analysis_methods=["多模型检验"])
        for invalid in ("11", float("nan"), True):
            tables["多模型检验"] = pd.DataFrame([{**record, "对照模型数值": invalid}])
            with self.assertRaises(ValueError):
                MOD.validate_workbook_tables(tables, "result_analysis")
        tables["多模型检验"] = pd.DataFrame([record, record])
        with self.assertRaisesRegex(ValueError, "重复值"):
            MOD.validate_workbook_tables(tables, "result_analysis")

    def test_standalone_fallback_has_current_comparison_schema(self):
        current = MOD.load_workbook_schema()["result_analysis_workbook"]
        fallback = MOD._FALLBACK_SCHEMA["result_analysis_workbook"]
        self.assertEqual(current["comparison_method_sheets"], fallback["comparison_method_sheets"])
        for sheet in ("多模型检验", "同模型多算法检验"):
            self.assertEqual(current["sheet_schemas"][sheet]["required_columns"], fallback["sheet_schemas"][sheet]["required_columns"])
            self.assertEqual(fallback["sheet_schemas"][sheet]["optional_columns"], ["差异单位"])
            self.assertEqual(current["sheet_schemas"][sheet]["optional_columns"].count("差异单位"), 1)


if __name__ == "__main__":
    unittest.main()
