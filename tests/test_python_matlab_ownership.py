import ast, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class TestOwnership(unittest.TestCase):
    def test_python_templates_have_no_formal_plot_imports(self):
        for f in (ROOT/'templates/code').rglob('*.py'):
            text=f.read_text(encoding='utf-8')
            self.assertNotIn('matplotlib', text, str(f))
            self.assertNotIn('seaborn', text, str(f))
            self.assertNotIn('savefig(', text, str(f))
            ast.parse(text)
    def test_matlab_plot_template_visible_and_manual_export(self):
        text=(ROOT/'templates/matlab/plot_from_workbook.m').read_text(encoding='utf-8')
        self.assertNotIn('"Visible", "off"', text)
        self.assertNotIn('close(fig)', text)
        self.assertIn('% hsk_export_figure', text)
    def test_mechanism_template_has_no_generic_default_nodes(self):
        text=(ROOT/'templates/matlab/draw_mechanism_structure.m').read_text(encoding='utf-8')
        self.assertNotIn('输入', text)
        self.assertNotIn('模型', text)
        self.assertNotIn('结果', text)

if __name__=='__main__': unittest.main()
