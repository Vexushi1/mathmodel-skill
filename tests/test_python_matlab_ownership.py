import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestOwnership(unittest.TestCase):
    def test_python_templates_have_no_formal_plot_imports(self):
        for file in (ROOT / "templates/code").rglob("*.py"):
            text = file.read_text(encoding="utf-8")
            self.assertNotIn("matplotlib", text, str(file))
            self.assertNotIn("seaborn", text, str(file))
            self.assertNotIn("savefig(", text, str(file))
            ast.parse(text)

    def test_matlab_plot_template_is_colocated_and_does_not_export_by_default(self):
        text = (ROOT / "templates/matlab/q1_plot.m").read_text(encoding="utf-8")
        self.assertNotIn("close(fig)", text)
        self.assertNotIn("hsk_find_project_root", text)
        self.assertNotIn("hsk_read_result_workbooks", text)
        self.assertIn('fullfile(resultDir, "问题一求解结果.xlsx")', text)
        self.assertIn('fullfile(resultDir, "问题一结果深化分析.xlsx")', text)
        self.assertNotIn('fullfile(resultDir, "图表")', text)
        self.assertNotIn("EXPORT_FIGURES", text)
        self.assertNotIn("exportgraphics", text)
        self.assertIn("默认不自动导出文件", text)
        self.assertIn("信息效率", text)

    def test_mechanism_template_has_no_generic_default_nodes(self):
        text = (ROOT / "templates/matlab/draw_mechanism_structure.m").read_text(encoding="utf-8")
        self.assertNotIn("输入", text)
        self.assertNotIn("模型", text)
        self.assertNotIn("结果", text)


if __name__ == "__main__":
    unittest.main()
