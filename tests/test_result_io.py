import importlib.util, tempfile, unittest
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('result_io', ROOT/'templates/code/hsk_pipeline/result_io.py')
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)

class TestResultIO(unittest.TestCase):
    def test_paths_and_workbooks(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            solve, robust=MOD.workbook_paths(root,'问题一')
            self.assertEqual(solve.relative_to(root).as_posix(), '结果数据表/问题一/问题一结果数据/问题一求解结果.xlsx')
            self.assertEqual(robust.relative_to(root).as_posix(), '结果数据表/问题一/问题一结果数据/问题一敏感性与鲁棒性结果.xlsx')
            MOD.write_workbook(solve, {'核心指标': pd.DataFrame({'指标':['目标值'],'数值':[1.0]})})
            self.assertTrue(solve.exists())
            with pd.ExcelFile(solve) as workbook:
                self.assertEqual(workbook.sheet_names, ['核心指标'])

if __name__=='__main__': unittest.main()
