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
        profiles = yaml.safe_load(
            (ROOT / "core/compile_profiles.yaml").read_text(encoding="utf-8")
        )
        for name in ("cumcm", "mcm_icm", "diangong"):
            self.assertIn(name, profiles["profiles"])
            profile = profiles["profiles"][name]
            self.assertTrue(profile["sequence"])
            self.assertIn(profile["engine"], {"xelatex", "pdflatex", "lualatex"})
        self.assertIn("biber", profiles["profiles"]["cumcm"]["sequence"])

    def test_packager_excludes_multisuffix_latex_files(self):
        module = load_module(
            "hsk_pack_submission", ROOT / "scripts/hsk_pack_submission.py"
        )
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
        module = load_module(
            "hsk_check_artifact", ROOT / "scripts/hsk_check_artifact.py"
        )
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

    def test_artifact_checker_rejects_missing_required_columns(self):
        module = load_module(
            "hsk_check_artifact_columns", ROOT / "scripts/hsk_check_artifact.py"
        )
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "solution.xlsx"
            workbook = Workbook()
            core = workbook.active
            core.title = "核心指标"
            core.append(["结果"])
            core.append([1.0])
            audit = workbook.create_sheet("数据审计")
            audit.append(["等级", "检查项", "信息", "处理方式"])
            audit.append(["Info", "字段", "通过", "无"])
            workbook.save(path)

            issues = module.inspect_workbook(path, "solution")
            self.assertTrue(
                any("missing required columns" in issue for issue in issues),
                issues,
            )

    def test_artifact_checker_enforces_conditional_constraint_sheet(self):
        module = load_module(
            "hsk_check_artifact_constraints", ROOT / "scripts/hsk_check_artifact.py"
        )
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "solution.xlsx"
            workbook = Workbook()
            core = workbook.active
            core.title = "核心指标"
            core.append(["指标", "数值"])
            core.append(["目标值", 1.0])
            audit = workbook.create_sheet("数据审计")
            audit.append(["等级", "检查项", "信息", "处理方式"])
            audit.append(["Info", "字段", "通过", "无"])
            workbook.save(path)

            issues = module.inspect_workbook(
                path,
                "solution",
                problem_types=("optimization",),
            )
            self.assertTrue(any("约束违反检查" in issue for issue in issues), issues)

    def test_render_paper_refuses_ambiguous_profile(self):
        module = load_module("render_paper", ROOT / "scripts/render_paper.py")
        profiles = module.load_profiles()
        with tempfile.TemporaryDirectory() as temp:
            main = Path(temp) / "main.tex"
            main.write_text(
                "\\documentclass{article}\n"
                "\\begin{document}\n"
                "test\n"
                "\\end{document}\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SystemExit, "cannot safely infer"):
                module.infer_profile(main, profiles)

    def test_matlab_templates_use_root_finder_font_fallback_and_preserve_columns(self):
        plotting = (
            ROOT / "templates/matlab/plot_from_workbook.m"
        ).read_text(encoding="utf-8")
        style = (
            ROOT / "templates/matlab/hsk_apply_scientific_style.m"
        ).read_text(encoding="utf-8")
        reader = (
            ROOT / "templates/matlab/hsk_read_result_workbooks.m"
        ).read_text(encoding="utf-8")
        self.assertIn("hsk_find_project_root", plotting)
        self.assertIn("listfonts", style)
        self.assertIn("Noto Sans CJK SC", style)
        self.assertIn('VariableNamingRule", "preserve"', reader)
        self.assertIn("missingColumns", reader)


if __name__ == "__main__":
    unittest.main()
