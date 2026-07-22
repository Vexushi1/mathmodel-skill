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

    def test_single_matlab_plot_entry_is_visible_and_self_contained(self):
        template=ROOT/'templates/matlab/QX_plot.m'
        self.assertTrue(template.is_file())
        text=template.read_text(encoding='utf-8')
        self.assertIn('function figureRegistry = QX_plot()', text)
        self.assertIn('plot_core_result', text)
        self.assertIn('plot_sensitivity', text)
        self.assertIn('plot_robustness_interval', text)
        self.assertIn('function projectRoot = find_project_root', text)
        self.assertIn('function apply_scientific_style', text)
        self.assertIn('function export_figure', text)
        self.assertNotIn('"Visible", "off"', text)
        self.assertNotIn('close(fig)', text)
        self.assertIn('exportFigures = false', text)

    def test_split_plot_templates_are_removed(self):
        self.assertFalse((ROOT/'templates/matlab/plot_from_workbook.m').exists())
        self.assertFalse((ROOT/'templates/matlab/plot_sensitivity_robustness.m').exists())

    def test_output_contract_requires_one_plot_file_per_question(self):
        text=(ROOT/'core/output_contract.yaml').read_text(encoding='utf-8')
        self.assertIn('matlab_plot_script: MATLAB绘图/问题{中文序号}/Q{阿拉伯序号}_plot.m', text)
        self.assertIn('Each question has exactly one delivered MATLAB plotting file', text)
        self.assertIn('QX_plot.m must be self-contained', text)

    def test_mechanism_template_has_no_generic_default_nodes(self):
        text=(ROOT/'templates/matlab/draw_mechanism_structure.m').read_text(encoding='utf-8')
        self.assertNotIn('输入', text)
        self.assertNotIn('模型', text)
        self.assertNotIn('结果', text)

if __name__=='__main__': unittest.main()
