import importlib.util
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("result_io", ROOT / "templates/code/hsk_pipeline/result_io.py")
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


class TestResultIO(unittest.TestCase):
    def test_paths_and_workbooks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            solve, robust = MOD.workbook_paths(root, "问题一")
            self.assertEqual(solve.relative_to(root).as_posix(), "结果数据表/问题一/问题一结果数据/问题一求解结果.xlsx")
            self.assertEqual(robust.relative_to(root).as_posix(), "结果数据表/问题一/问题一结果数据/问题一敏感性与鲁棒性结果.xlsx")
            MOD.write_workbook(solve, {"核心指标": pd.DataFrame({"指标": ["目标值"], "数值": [1.0]})})
            self.assertTrue(solve.exists())
            with pd.ExcelFile(solve) as workbook:
                self.assertEqual(workbook.sheet_names, ["核心指标"])

    def test_empty_worksheet_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.xlsx"
            with self.assertRaisesRegex(ValueError, "禁止写入空工作表"):
                MOD.write_workbook(path, {"参数敏感性": pd.DataFrame()})

    def test_applicability_table_matches_schema(self):
        table = MOD.not_applicable_table("没有外生扰动参数")
        self.assertEqual(list(table.columns[:3]), ["分析类型", "不适用原因", "替代检验"])
        self.assertEqual(table.loc[0, "不适用原因"], "没有外生扰动参数")


if __name__ == "__main__":
    unittest.main()
