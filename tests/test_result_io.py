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
    def solution_tables(self):
        return {
            "核心指标": pd.DataFrame({"指标": ["目标值"], "数值": [1.0]}),
            "数据审计": pd.DataFrame(
                {
                    "等级": ["Info"],
                    "检查项": ["字段"],
                    "信息": ["通过"],
                    "处理方式": ["无"],
                }
            ),
        }

    def test_paths_and_workbooks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            solve, robust = MOD.workbook_paths(root, "问题一")
            self.assertEqual(
                solve.relative_to(root).as_posix(),
                "结果数据表/问题一/问题一结果数据/问题一求解结果.xlsx",
            )
            self.assertEqual(
                robust.relative_to(root).as_posix(),
                "结果数据表/问题一/问题一结果数据/问题一敏感性与鲁棒性结果.xlsx",
            )
            MOD.write_workbook(solve, self.solution_tables())
            self.assertTrue(solve.exists())
            with pd.ExcelFile(solve) as workbook:
                self.assertEqual(workbook.sheet_names, ["核心指标", "数据审计"])

    def test_empty_worksheet_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.xlsx"
            with self.assertRaisesRegex(ValueError, "禁止写入空工作表"):
                MOD.write_workbook(path, {"参数敏感性": pd.DataFrame()})

    def test_applicability_table_matches_schema(self):
        table = MOD.not_applicable_table("没有外生扰动参数")
        self.assertEqual(list(table.columns[:3]), ["分析类型", "不适用原因", "替代检验"])
        self.assertEqual(table.loc[0, "不适用原因"], "没有外生扰动参数")

    def test_required_columns_are_enforced(self):
        tables = self.solution_tables()
        tables["核心指标"] = pd.DataFrame({"结果": [1.0]})
        with self.assertRaisesRegex(ValueError, "缺少必需字段"):
            MOD.validate_workbook_tables(tables, "solution")

    def test_constraint_sheet_is_conditional(self):
        tables = self.solution_tables()
        with self.assertRaisesRegex(ValueError, "约束违反检查"):
            MOD.validate_workbook_tables(
                tables,
                "solution",
                problem_types=("optimization",),
            )

    def test_constraint_sheet_passes_for_optimization(self):
        tables = self.solution_tables()
        tables["约束违反检查"] = pd.DataFrame(
            {
                "约束编号": ["C1"],
                "约束含义": ["容量"],
                "违反量": [0.0],
                "容差": [1e-8],
                "是否满足": [True],
            }
        )
        prepared = MOD.validate_workbook_tables(
            tables,
            "solution",
            problem_types=("optimization",),
        )
        self.assertIn("约束违反检查", {name for name, _ in prepared})

    def test_duplicate_record_key_is_rejected(self):
        tables = self.solution_tables()
        tables["明细结果"] = pd.DataFrame(
            {"记录键": ["A", "A"], "数值": [1.0, 2.0]}
        )
        with self.assertRaisesRegex(ValueError, "重复值"):
            MOD.validate_workbook_tables(tables, "solution")

    def test_prediction_requires_task_specific_sheet(self):
        tables = self.solution_tables()
        with self.assertRaisesRegex(ValueError, "prediction"):
            MOD.validate_workbook_tables(
                tables,
                "solution",
                problem_types=("prediction",),
            )

    def test_robustness_requires_known_analysis_sheet(self):
        with self.assertRaisesRegex(ValueError, "至少需要一个工作表"):
            MOD.validate_workbook_tables(
                {"汇总": pd.DataFrame({"指标": ["均值"], "数值": [1.0]})},
                "robustness",
            )


if __name__ == "__main__":
    unittest.main()
