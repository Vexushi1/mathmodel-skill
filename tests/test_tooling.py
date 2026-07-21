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

    def test_artifact_checker_rejects_missing_schema_columns(self):
        module = load_module("hsk_check_artifact_invalid", ROOT / "scripts/hsk_check_artifact.py")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            solution = root / "solution.xlsx"
            robustness = root / "robustness.xlsx"

            workbook = Workbook()
            core = workbook.active
            core.title = "核心指标"
            core.append(["指标", "错误字段"])
            core.append(["目标值", 1.0])
            audit = workbook.create_sheet("数据审计")
            audit.append(["等级", "检查项", "信息", "处理方式"])
            audit.append(["Info", "字段", "通过", "无"])
            workbook.save(solution)

            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "适用性说明"
            sheet.append(["分析类型", "不适用原因"])
            sheet.append(["参数敏感性", "无外生参数"])
            workbook.save(robustness)

            solution_issues = module.inspect_workbook(solution, "solution")
            robustness_issues = module.inspect_workbook(robustness, "robustness")
            self.assertTrue(any("数值" in issue and "核心指标" in issue for issue in solution_issues))
            self.assertTrue(any("替代检验" in issue and "适用性说明" in issue for issue in robustness_issues))

    def test_artifact_checker_enforces_problem_type_conditional_sheets(self):
        module = load_module("hsk_check_artifact_conditional", ROOT / "scripts/hsk_check_artifact.py")
        with tempfile.TemporaryDirectory() as temp:
            solution = Path(temp) / "solution.xlsx"
            workbook = Workbook()
            core = workbook.active
            core.title = "核心指标"
            core.append(["指标", "数值"])
            core.append(["目标值", 1.0])
            audit = workbook.create_sheet("数据审计")
            audit.append(["等级", "检查项", "信息", "处理方式"])
            audit.append(["Info", "字段", "通过", "无"])
            workbook.save(solution)

            issues = module.inspect_workbook(solution, "solution", problem_type="optimization")
            self.assertTrue(any("约束违反检查" in issue for issue in issues))

    def test_manifest_digest_normalizes_text_line_endings(self):
        module = load_module("generate_indexes", ROOT / "scripts/generate_indexes.py")
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "sample.txt"
            path.write_bytes(b"alpha\r\nbeta\r\n")
            crlf_digest = module.digest_file(path)
            path.write_bytes(b"alpha\nbeta\n")
            lf_digest = module.digest_file(path)
            self.assertEqual(crlf_digest, lf_digest)

    def test_matlab_templates_use_root_finder_and_font_fallback(self):
        plotting = (ROOT / "templates/matlab/plot_from_workbook.m").read_text(encoding="utf-8")
        style = (ROOT / "templates/matlab/hsk_apply_scientific_style.m").read_text(encoding="utf-8")
        self.assertIn("hsk_find_project_root", plotting)
        self.assertIn("listfonts", style)
        self.assertIn("Noto Sans CJK SC", style)


if __name__ == "__main__":
    unittest.main()
