import importlib.util
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "result_io", ROOT / "templates/code/hsk_pipeline/result_io.py"
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


class TestResultIO(unittest.TestCase):
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
            self.assertEqual(MOD.find_project_root(script), Path(directory))

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


if __name__ == "__main__":
    unittest.main()
