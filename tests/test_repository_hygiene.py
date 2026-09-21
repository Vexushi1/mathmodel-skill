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

    def test_project_instructions_use_conditional_three_plus_two_contract(self) -> None:
        text = read("PROJECT_INSTRUCTIONS.md")
        self.assertIn("core/output_contract.yaml", text)
        self.assertIn("基础三文件", text)
        for token in ("问题X求解.py", "问题X求解结果.xlsx", "qX_plot.m"):
            self.assertIn(token, text)
        self.assertIn("仅当 Analysis Necessity Gate=`required` 时追加", text)
        self.assertIn("问题X结果深化分析.py + 问题X结果深化分析.xlsx", text)
        self.assertIn("Gate=`not_required`", text)
        self.assertIn("非空理由", text)
        self.assertIn("不得据此声称稳健性或稳定性已通过", text)
        self.assertIn("旧表述“最终默认恰好包含五个文件”只适用于 Gate=`required`", text)
        self.assertNotIn("最终默认恰好保留五个文件", text)
        self.assertNotIn("不得另建结果深化分析 Python 脚本", text)
        self.assertNotIn("覆盖更新同一个 `问题X求解.py`", text)

    def test_output_contract_keeps_conditional_three_five_default_files(self) -> None:
        contract = yaml.safe_load(read("core/output_contract.yaml"))
        per_question = contract["per_question"]
        self.assertEqual(
            per_question["base_default_files"],
            [
                "问题{中文序号}求解.py",
                "问题{中文序号}求解结果.xlsx",
                "q{阿拉伯序号}_plot.m",
            ],
        )
        self.assertEqual(
            per_question["analysis_required_additional_files"],
            [
                "问题{中文序号}结果深化分析.py",
                "问题{中文序号}结果深化分析.xlsx",
            ],
        )
        self.assertEqual(len(set(per_question["base_default_files"] + per_question["analysis_required_additional_files"])), 5)
        self.assertTrue(per_question["no_auxiliary_files_by_default"])
        self.assertNotIn("single_python_update_policy", per_question)
        self.assertEqual(
            contract["result_policy"]["result_analysis_activation"],
            "conditional_after_primary_acceptance_via_analysis_necessity_gate",
        )
        self.assertEqual(
            contract["project_sync"]["formal_state_requirements"]["result_analysis_status"],
            ["passed", "not_required"],
        )
        self.assertNotIn("result_analysis_code", contract["project_sync"]["stage_requirements"]["results"])
        self.assertIn("result_analysis_report", contract["project_sync"]["stage_requirements"]["results"])

    def test_lint_validates_p7_conditionals_without_obsolete_filter(self) -> None:
        base = read("scripts/lint_skill_checks.py")
        adapter = read("scripts/lint_skill.py")
        for token in (
            "base_default_files",
            "analysis_required_additional_files",
            "results base scope must not unconditionally require result-analysis code",
            "results scope must retain auditable result-analysis gate/report state",
            "formal delivery must accept only passed or reasoned not_required result-analysis status",
            "draw.io integration must acknowledge conditional rather than fixed five-file layout",
        ):
            self.assertIn(token, base)
        for obsolete in (
            "per-question default must be exact five-file two-script layout",
            "results scope must require independent result-analysis code",
            "draw.io integration must preserve the per-question five-file layout",
        ):
            self.assertNotIn(obsolete, base)
            self.assertNotIn(obsolete, adapter)
        self.assertNotIn("_P7_OBSOLETE_CONTRACT_ERRORS", adapter)
        self.assertIn("_p7_conditional_analysis_contract_errors", adapter)
        self.assertIn("errors.extend(_p7_conditional_analysis_contract_errors(output))", adapter)

    def test_review_and_submission_packs_use_current_contract(self) -> None:
        review = read("packs/artifact/review.md")
        submission = read("packs/artifact/full_submission.md")

        self.assertIn("conditional per-question layout contract", review)
        self.assertIn("基础三文件", review)
        self.assertIn("仅 Analysis Necessity Gate=`required` 时追加 03B代码 与 workbook", review)
        self.assertIn("Gate=`not_required`", review)
        self.assertIn("不构成 layout finding", review)
        self.assertNotIn("新项目每问数值目录必须符合当前五文件合同", review)
        self.assertNotIn("四文件合同", review)

        self.assertIn("current conditional layout", submission)
        self.assertIn("基础三文件始终收集", submission)
        self.assertIn("Gate=`required` 时再收集实际存在且 current 的 03B 两文件", submission)
        self.assertIn("Gate=`not_required` 且理由非空", submission)
        self.assertIn("不得为了凑固定结构伪造", submission)
        self.assertIn("问题X结果深化分析.py", submission)
        self.assertNotIn("不得创建独立结果深化脚本", submission)
        self.assertIn("internal_metadata/", submission)
        self.assertIn("不得把这些文件塞入 `问题X求解/`", submission)
        self.assertNotIn("也不得破坏每问五文件合同", submission)

    def test_active_templates_use_conditional_two_stage_question_directory(self) -> None:
        policy = read("core/hsk_core_policy.md")
        self.assertIn("具体目录、工作簿字段、每问文件集合", policy)
        self.assertIn("core/output_contract.yaml", policy)
        self.assertIn("legacy/", policy)

        execution = yaml.safe_load(read("core/user_execution_contract.yaml"))
        delivery = execution["code_delivery"]
        self.assertEqual(
            delivery["stage_scripts"],
            {
                "primary": "问题X求解/问题X求解.py",
                "analysis": "问题X求解/问题X结果深化分析.py",
            },
        )
        self.assertEqual(
            delivery["stage_activation"]["analysis"],
            "accepted_primary_workbook and analysis_necessity_gate == required",
        )
        analysis_stage = execution["three_stage_policy"]["analysis"]
        self.assertIn("仅Gate=required时激活", analysis_stage["activation"])
        self.assertIn("Gate=not_required时记录非空理由且不生成03B代码/工作簿", analysis_stage["role"])
        self.assertIn("主工作簿accepted后该脚本冻结", execution["three_stage_policy"]["primary"]["role"])

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

    def test_no_active_source_references_removed_auxiliary_contracts(self) -> None:
        forbidden = (
            "full_fidelity_config.yaml",
            "user_execution_instructions.md",
            "matlab_handoff.py",
            "hsk_check_artifact.py",
            "robustness_check.md",
            "hsk_pipeline/config.yaml",
        )
        allow = {"CHANGELOG.md", "README.md", "SKILL_CHANGE_GOVERNANCE.md"}
        for path in ROOT.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            relative = path.relative_to(ROOT).as_posix()
            if relative.startswith("legacy/") or relative.startswith("docs/") or relative.startswith("tests/"):
                continue
            if relative in allow:
                continue
            text = path.read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, text, relative)

    def test_old_version_markers_are_not_in_active_templates(self) -> None:
        for path in (ROOT / "templates").rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            text = path.read_text(encoding="utf-8")
            for marker in OBSOLETE_ACTIVE_TEMPLATE_MARKERS:
                self.assertNotIn(marker, text, path.relative_to(ROOT).as_posix())

    def test_current_result_analysis_naming_is_consistent(self) -> None:
        files = (
            "modules/03_result_analysis.md",
            "core/workbook_schema.yaml",
            "templates/code/hsk_pipeline/README.md",
            "templates/writing/code_appendix_description.md",
        )
        for relative in files:
            text = read(relative)
            self.assertIn("结果深化分析", text, relative)
            self.assertNotIn(LEGACY_WORKBOOK, text, relative)

    def test_no_deprecated_four_file_contract_in_active_tree(self) -> None:
        pattern = re.compile(r"四文件合同|最终默认恰好包含四个文件|最终默认恰好保留四个文件")
        for path in ROOT.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            relative = path.relative_to(ROOT).as_posix()
            if relative.startswith("legacy/") or relative.startswith("docs/") or relative.startswith("tests/"):
                continue
            self.assertIsNone(pattern.search(path.read_text(encoding="utf-8")), relative)


if __name__ == "__main__":
    unittest.main()
