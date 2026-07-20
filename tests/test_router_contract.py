import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class TestRouterContract(unittest.TestCase):
    def test_output_contract(self):
        text=(ROOT/'core/output_contract.yaml').read_text(encoding='utf-8')
        self.assertIn('结果数据表/问题{中文序号}/问题{中文序号}结果数据/', text)
        self.assertIn('问题{中文序号}求解结果.xlsx', text)
        self.assertIn('问题{中文序号}敏感性与鲁棒性结果.xlsx', text)
    def test_latex_compile_route(self):
        text=(ROOT/'core/workflow_router.yaml').read_text(encoding='utf-8')
        self.assertIn('modules/05_latex_compile_quality.md', text)
    def test_no_legacy_route(self):
        text=(ROOT/'core/workflow_router.yaml').read_text(encoding='utf-8')
        self.assertNotIn('legacy/', text)

if __name__=='__main__': unittest.main()
