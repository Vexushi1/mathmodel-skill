import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml
from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestTooling(unittest.TestCase):
    def test_compile_profiles_are_complete(self):
        profiles = yaml.safe_load((ROOT / "core/compile_profiles.yaml").read_text(encoding="utf-8"))
        for name in ("cumcm", "mcm_icm", "diangong"):
            self.assertIn(name, profiles["profiles"])
            profile = profiles["profiles"][name]
            self.assertTrue(profile["sequence"])
            self.assertIn(profile["engine"], {"xelatex", "pdflatex", "lualatex"})
        self.assertIn("biber", profiles["profiles"]["cumcm"]["sequence"])

    def test_packager_excludes_multisuffix_latex_files(self):
        module = load_module("hsk_pack_submission", ROOT / "scripts/hsk_pack_submission.py")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "package.zip"
            for name in ("main.synctex.gz", "main.run.xml", "main.bcf", "main.pdf"):
                (root / name).write_text("x", encoding="utf-8")
            self.assertTrue(module.should_exclude(root / "main.synctex.gz", root, output))
            self.assertTrue(module.should_exclude(root / "main.run.xml", root, output))
            self.assertTrue(module.should_exclude(root / "main.bcf", root, output))
            self.assertFalse(module.should_exclude(root / "main.pdf", root, output))

    def test_artifact_checker_accepts_nonempty_standard_workbooks(self):
        module = load_module("hsk_check_artifact", ROOT / "scripts/hsk_check_artifact.py")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            solution = root / "solution.xlsx"
            robustness = root / "robustness.xlsx"

            workbook = Workbook()
            core = workbook.active
            core.title = "核心指标"
            core.append(["指标", "数值"])
            core.append(["目标值", 1.0])
            audit = workbook.create_sheet("数据审计")
            audit.append(["等级", "检查项", "信息", "处理方式"])
            audit.append(["Info", "字段", "通过", "无"])
            workbook.save(solution)

            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "适用性说明"
            sheet.append(["分析类型", "不适用原因", "替代检验"])
            sheet.append(["参数敏感性", "无外生参数", "边界条件检查"])
            workbook.save(robustness)

            self.assertEqual(module.inspect_workbook(solution, "solution"), [])
            self.assertEqual(module.inspect_workbook(robustness, "robustness"), [])

    def test_qx_plot_is_self_contained_and_has_font_fallback(self):
        plotting = (ROOT / "templates/matlab/QX_plot.m").read_text(encoding="utf-8")
        self.assertIn("function projectRoot = find_project_root", plotting)
        self.assertIn("function apply_scientific_style", plotting)
        self.assertIn("function export_figure", plotting)
        self.assertIn("listfonts", plotting)
        self.assertIn("Noto Sans CJK SC", plotting)

    def test_matlab_handoff_rejects_multiple_scripts(self):
        module = load_module(
            "matlab_handoff", ROOT / "templates/code/hsk_pipeline/matlab_handoff.py"
        )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            problem = "问题一"
            result_dir = root / "结果数据表" / problem / f"{problem}结果数据"
            result_dir.mkdir(parents=True)
            for name in (f"{problem}求解结果.xlsx", f"{problem}敏感性与鲁棒性结果.xlsx"):
                (result_dir / name).write_bytes(b"placeholder")
            figures = [
                {
                    "figure_id": "图1",
                    "workbook": "求解结果",
                    "worksheet": "明细结果",
                    "matlab_script": "Q1_plot.m",
                    "local_plot_function": "plot_core_result",
                },
                {
                    "figure_id": "图2",
                    "workbook": "敏感性与鲁棒性结果",
                    "worksheet": "参数敏感性",
                    "matlab_script": "Q2_plot.m",
                    "local_plot_function": "plot_sensitivity",
                },
            ]
            with self.assertRaises(ValueError):
                module.write_matlab_handoff(root, problem, figures)


if __name__ == "__main__":
    unittest.main()
