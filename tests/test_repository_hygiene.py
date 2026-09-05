from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
LEGACY_WORKBOOK = "敏感性与鲁棒性结果.xlsx"
CURRENT_WORKBOOK = "结果深化分析.xlsx"
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".py", ".m", ".tex", ".txt", ".json"}
OBSOLETE_ACTIVE_TEMPLATE_MARKERS = ("v6.6.0",)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class RepositoryHygieneTests(unittest.TestCase):
    """Current repository-level residue checks consolidated from one-off cleanup tests."""

    def test_obsolete_active_files_are_absent(self) -> None:
        obsolete = (
            "templates/code/full_fidelity_config.yaml",
            "templates/code/user_execution_instructions.md",
            "templates/code/hsk_pipeline/matlab_handoff.py",
            "scripts/hsk_check_artifact.py",
            "templates/review/robustness_check.md",
            "templates/code/hsk_pipeline/config.yaml",
        )
        for relative in obsolete:
            self.assertFalse((ROOT / relative).exists(), relative)
        self.assertTrue((ROOT / "templates/review/result_analysis_check.md").is_file())

    def test_project_instructions_use_five_file_two_python_contract(self) -> None:
        text = read("PROJECT_INSTRUCTIONS.md")
        self.assertIn("问题X结果深化分析.py", text)
        self.assertTrue("最终默认恰好保留五个文件" in text or "最终默认恰好包含" in text)
        self.assertNotIn("不得另建结果深化分析 Python 脚本", text)
        self.assertNotIn("覆盖更新同一个 `问题X求解.py`", text)

    def test_output_contract_keeps_exact_five_default_files(self) -> None:
        contract = yaml.safe_load(read("core/output_contract.yaml"))
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

    def test_review_and_submission_packs_use_current_contract(self) -> None:
        review = read("packs/artifact/review.md")
        submission = read("packs/artifact/full_submission.md")
        self.assertIn("五文件合同", review)
        self.assertNotIn("四文件合同", review)
        self.assertIn("问题X结果深化分析.py", submission)
        self.assertNotIn("不得创建独立结果深化脚本", submission)
        self.assertIn("internal_metadata/", submission)
        self.assertIn("不得把这些文件塞入 `问题X求解/`", submission)

    def test_active_templates_use_self_contained_two_script_question_directory(self) -> None:
        policy = read("core/hsk_core_policy.md")
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
            text = read(relative)
            for token in required_tokens:
                self.assertIn(token, text, relative)
            self.assertNotIn("结果数据表/问题X", text, relative)

    def test_active_figure_templates_do_not_generate_legacy_result_paths(self) -> None:
        for relative in (
            "templates/figure/figure_plan.md",
            "templates/figure/figure_paper_closure.md",
        ):
            text = read(relative)
            self.assertIn("问题一求解/", text, relative)
            self.assertNotIn("结果数据表/问题一/", text, relative)
            self.assertNotIn("结果数据表/问题二/", text, relative)

    def test_active_figure_files_do_not_default_to_auxiliary_outputs(self) -> None:
        for relative in (
            "templates/figure/result_figure_contract.md",
            "packs/artifact/figure.md",
            "templates/matlab/README.md",
        ):
            text = read(relative)
            self.assertNotIn("写入同级 `图表/`", text, relative)
            self.assertNotIn("figure_evidence.yaml", text, relative)
        matlab = read("templates/matlab/README.md")
        self.assertIn("不创建图表子目录", matlab)
        self.assertIn("不批量导出", matlab)

    def test_current_generation_templates_do_not_emit_legacy_workbook_name(self) -> None:
        active_templates = (
            "templates/matlab/q1_plot.m",
            "templates/matlab/README.md",
            "templates/figure/result_figure_contract.md",
            "templates/figure/figure_paper_closure.md",
            "templates/review/result_manifest.yaml",
            "templates/writing/code_appendix_description.md",
        )
        for relative in active_templates:
            text = read(relative)
            self.assertNotIn(LEGACY_WORKBOOK, text, relative)
            self.assertIn(CURRENT_WORKBOOK, text, relative)

    def test_matlab_starter_uses_current_variable_and_filename(self) -> None:
        text = read("templates/matlab/q1_plot.m")
        self.assertIn("resultAnalysisBook", text)
        self.assertIn('"问题一结果深化分析.xlsx"', text)
        self.assertNotIn("robustnessBook", text)

    def test_matlab_reader_prefers_current_directory_and_has_no_figure_dir(self) -> None:
        text = read("templates/matlab/hsk_read_result_workbooks.m")
        self.assertIn('fullfile(location, problemName + "求解")', text)
        self.assertNotIn('resultDir = fullfile(location, "结果数据表", problemName)', text)
        self.assertNotIn("books.figureDir", text)
        self.assertIn("仅作只读兼容", text)

    def test_result_manifest_uses_current_field_name(self) -> None:
        text = read("templates/review/result_manifest.yaml")
        self.assertIn("result_analysis_workbook:", text)
        self.assertNotIn("sensitivity_robustness_workbook:", text)

    def test_current_starters_stop_at_primary_user_execution_gate(self) -> None:
        for path in (ROOT / "templates/code/starter").glob("*.py"):
            text = path.read_text(encoding="utf-8")
            self.assertIn("run_primary_pipeline(", text, path.name)
            self.assertNotIn("run_pipeline(", text, path.name)
            self.assertNotIn("analyze_results", text, path.name)

    def test_runtime_router_exposes_conditional_preprocessing_and_user_gates(self) -> None:
        text = read("RUNTIME_ROUTER.md")
        self.assertIn("project_level → data_preprocessing", text)
        self.assertIn("用户本地运行预处理 Python", text)
        self.assertIn("用户本地运行主求解 Python", text)
        self.assertIn("用户本地运行深化分析 Python", text)
        self.assertIn("不会跨越用户执行边界", text)

    def test_project_state_example_locks_preprocessing_decision(self) -> None:
        state = yaml.safe_load(read("state/project_state.example.yaml"))
        preprocessing = state.get("preprocessing", {})
        self.assertEqual(preprocessing.get("decision"), "not_needed")
        self.assertEqual(preprocessing.get("level"), "none")
        self.assertEqual(preprocessing.get("downstream_data_source"), "raw")
        self.assertEqual(state.get("data", {}).get("active_source_mode"), "raw")

    def test_generated_index_version_comes_from_bootstrap(self) -> None:
        generator = read("scripts/generate_indexes.py")
        bootstrap = yaml.safe_load(read("core/bootstrap.yaml"))
        self.assertIn("current_skill_version", generator)
        self.assertIn('BOOTSTRAP = ROOT / "core" / "bootstrap.yaml"', generator)
        self.assertNotIn('VERSION = "7.2.1"', generator)
        expected = str(bootstrap["skill_version"])
        for relative in ("SKILL_FILE_INDEX.md", "TEMPLATE_INDEX.md"):
            self.assertIn(f"当前 Skill 版本：{expected}", read(relative), relative)

    def test_agent_entrypoint_is_latex_first(self) -> None:
        text = read("AGENTS.md")
        self.assertIn("LaTeX is the default paper and final-PDF path", text)
        self.assertIn("DOCX is an explicit optional review branch", text)
        self.assertIn("问题X结果深化分析.xlsx", text)

    def test_active_files_do_not_depend_on_old_stage(self) -> None:
        for top in ("core", "modules", "packs"):
            for path in (ROOT / top).rglob("*"):
                if path.suffix not in {".md", ".yaml"}:
                    continue
                text = path.read_text(encoding="utf-8")
                self.assertNotRegex(text, r"references/hsk_stage_", str(path))
                self.assertNotRegex(text, r"feedback_layer[1-4]", str(path))

    def test_active_template_index_has_no_obsolete_release_marker(self) -> None:
        index_text = read("TEMPLATE_INDEX.md")
        relative_paths = sorted(set(re.findall(r"`(templates/[^`]+)`", index_text)))
        self.assertTrue(relative_paths)
        for relative in relative_paths:
            path = ROOT / relative
            self.assertTrue(path.is_file(), relative)
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for marker in OBSOLETE_ACTIVE_TEMPLATE_MARKERS:
                self.assertNotIn(marker, text, relative)

    def test_historical_v660_marker_remains_legacy_only(self) -> None:
        legacy = ROOT / "legacy/v660_self_contained_output_migration.md"
        self.assertTrue(legacy.is_file())
        self.assertIn("v6.6.0", legacy.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
