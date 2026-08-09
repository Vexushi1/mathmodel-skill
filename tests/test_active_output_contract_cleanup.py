import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class TestActiveOutputContractCleanup(unittest.TestCase):
    def test_obsolete_active_files_are_removed(self):
        for relative in (
            "templates/code/full_fidelity_config.yaml",
            "templates/code/user_execution_instructions.md",
            "templates/code/hsk_pipeline/matlab_handoff.py",
            "scripts/hsk_check_artifact.py",
        ):
            self.assertFalse((ROOT / relative).exists(), relative)

    def test_output_contract_keeps_exact_five_default_files(self):
        contract = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        per_question = contract["per_question"]
        self.assertEqual(
            per_question["exact_default_files"],
            [
                "问题{中文序号}求解.py",
                "问题{中文序号}求解结果.xlsx",
                "问题{中文序号}结果深化分析.py",
                "问题{中文序号}结果深化分析.xlsx",
                "q{阿拉伯序号}_plot.m",
            ],
        )
        self.assertTrue(per_question["no_auxiliary_files_by_default"])
        self.assertNotIn("single_python_update_policy", per_question)

    def test_active_templates_use_self_contained_two_script_question_directory(self):
        policy = (ROOT / "core/hsk_core_policy.md").read_text(encoding="utf-8")
        self.assertIn("默认恰好包含", policy)
        self.assertIn("问题X结果深化分析.py", policy)
        self.assertIn("只读兼容", policy)
        self.assertIn("冻结", policy)

        checks = {
            "templates/code/starter/README.md": ("问题一求解/问题一求解.py", "问题一结果深化分析.py"),
            "templates/code/hsk_pipeline/README.md": ("问题一求解/问题一求解结果.xlsx", "问题一结果深化分析.py"),
            "templates/writing/code_appendix_description.md": ("问题X求解/问题X求解.py", "问题X结果深化分析.py"),
            "templates/figure/result_figure_contract.md": ("问题X求解/qX_plot.m",),
            "packs/artifact/figure.md": ("问题X求解/qX_plot.m",),
            "templates/review/result_manifest.yaml": ("问题一求解/问题一求解结果.xlsx",),
        }
        for relative, required_tokens in checks.items():
            text = (ROOT / relative).read_text(encoding="utf-8")
            for token in required_tokens:
                self.assertIn(token, text, relative)
            self.assertNotIn("结果数据表/问题X", text, relative)

    def test_active_figure_files_do_not_default_to_auxiliary_outputs(self):
        for relative in (
            "templates/figure/result_figure_contract.md",
            "packs/artifact/figure.md",
            "templates/matlab/README.md",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("写入同级 `图表/`", text, relative)
            self.assertNotIn("figure_evidence.yaml", text, relative)
        matlab = (ROOT / "templates/matlab/README.md").read_text(encoding="utf-8")
        self.assertIn("不创建图表子目录", matlab)
        self.assertIn("不批量导出", matlab)

    def test_matlab_reader_prefers_current_directory_and_has_no_figure_dir(self):
        text = (ROOT / "templates/matlab/hsk_read_result_workbooks.m").read_text(encoding="utf-8")
        self.assertIn('fullfile(location, problemName + "求解")', text)
        self.assertNotIn('resultDir = fullfile(location, "结果数据表", problemName)', text)
        self.assertNotIn("books.figureDir", text)
        self.assertIn("仅作只读兼容", text)


if __name__ == "__main__":
    unittest.main()
