import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_TEXT_DIRS = (
    "core",
    "modules",
    "packs",
    "templates",
    "scripts",
    "skills",
    "state",
    "config",
    "agents",
    ".codex-plugin",
    ".github",
)
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".py", ".m", ".tex", ".bib"}
OBSOLETE_ROOT_ARTIFACTS = (
    "HSK_RUNTIME_ROUTER_V621.md",
    "HSK_SKILL_FILE_INDEX_V621.md",
    "HSK_TEMPLATE_INDEX_V621.md",
    "PROJECT_INSTRUCTIONS_HSK_V621.md",
)
OLD_TITLE_PHRASES = (
    "图内不重复总标题",
    "图内不重复放总标题",
    "图题由 LaTeX 图注承担",
    "图内是否没有重复总标题",
)


class TestStructure(unittest.TestCase):
    def test_required_dirs(self):
        for relative in [
            "core",
            "modules",
            "packs/task",
            "packs/competition",
            "packs/artifact",
            "templates/code",
            "templates/model",
            "templates/matlab",
            "templates/latex",
            "scripts",
            "tests",
            "legacy",
            ".github/workflows",
        ]:
            self.assertTrue((ROOT / relative).exists(), relative)

    def test_required_active_modules(self):
        for relative in [
            "modules/01_problem_audit.md",
            "modules/02_model_design.md",
            "modules/03_solve_validate.md",
            "modules/03_result_analysis.md",
            "modules/04_figure_evidence.md",
            "modules/05_writing/latex.md",
            "modules/05_writing/docx.md",
            "modules/05_writing/ai_cleanup.md",
            "modules/05_latex_compile_quality.md",
            "modules/06_review_delivery.md",
        ]:
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_plugin_wrapper(self):
        self.assertTrue((ROOT / ".codex-plugin/plugin.json").exists())
        self.assertTrue((ROOT / "skills/mathmodel-skill/SKILL.md").exists())

    def test_machine_readable_contracts_and_framework_tools(self):
        for relative in [
            "core/compile_profiles.yaml",
            "core/output_contract.yaml",
            "core/workbook_schema.yaml",
            "core/project_state.schema.yaml",
            "templates/model/model_paper_framework.md",
            "scripts/validate_model_paper_framework.py",
        ]:
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_repository_change_governance_is_installed(self):
        governance = ROOT / "SKILL_CHANGE_GOVERNANCE.md"
        pr_template = ROOT / ".github/pull_request_template.md"
        self.assertTrue(governance.is_file())
        self.assertTrue(pr_template.is_file())
        text = governance.read_text(encoding="utf-8")
        for token in (
            "每个新聊天的强制启动顺序",
            "修改简报",
            "单一事实源",
            "一次聊天一个分支",
            "一个 PR 一个主题",
            "禁止直接写 main",
            "生成文件规则",
            "测试与验收",
        ):
            self.assertIn(token, text)

    def test_bootstrap_requires_governance_before_repository_write(self):
        payload = yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))
        maintenance = payload["repository_maintenance"]
        self.assertEqual(maintenance["governance"], "SKILL_CHANGE_GOVERNANCE.md")
        self.assertTrue(maintenance["mandatory_before_write"])
        self.assertEqual(maintenance["read_from_ref"], "main")
        self.assertTrue(maintenance["branch_required"])
        self.assertTrue(maintenance["pull_request_required"])
        self.assertFalse(maintenance["direct_main_write_allowed"])

    def test_legal_notices(self):
        self.assertTrue((ROOT / "LICENSE").is_file())
        self.assertTrue((ROOT / "THIRD_PARTY_NOTICES.md").is_file())

    def test_obsolete_v621_root_artifacts_are_removed(self):
        for relative in OBSOLETE_ROOT_ARTIFACTS:
            self.assertFalse((ROOT / relative).exists(), relative)

    def test_versioned_root_changelogs_are_removed(self):
        stale = sorted(path.name for path in ROOT.glob("CHANGELOG_V*.md") if path.is_file())
        self.assertEqual(stale, [])

    def test_active_files_do_not_reference_v621(self):
        stale = re.compile(r"\bv6\.2\.1\b|\bV621\b", flags=re.IGNORECASE)
        violations = []
        for directory in ACTIVE_TEXT_DIRS:
            base = ROOT / directory
            if not base.exists():
                continue
            for path in base.rglob("*"):
                if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
                    text = path.read_text(encoding="utf-8-sig", errors="strict")
                    if stale.search(text):
                        violations.append(path.relative_to(ROOT).as_posix())
        self.assertEqual(violations, [])

    def test_active_files_do_not_keep_old_no_title_rules(self):
        violations = []
        skipped = {
            Path(__file__).resolve(),
            (ROOT / "scripts/lint_skill.py").resolve(),
        }
        for directory in ACTIVE_TEXT_DIRS:
            base = ROOT / directory
            if not base.exists():
                continue
            for path in base.rglob("*"):
                if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                    continue
                if path.resolve() in skipped:
                    continue
                text = path.read_text(encoding="utf-8-sig", errors="strict")
                for phrase in OLD_TITLE_PHRASES:
                    if phrase in text:
                        violations.append(f"{path.relative_to(ROOT).as_posix()}: {phrase}")
        self.assertEqual(violations, [])

    def test_gitattributes_forces_lf(self):
        attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn("* text=auto eol=lf", attributes)

    def test_matlab_has_one_standard_problem_plot_entry(self):
        matlab_dir = ROOT / "templates/matlab"
        self.assertTrue((matlab_dir / "q1_plot.m").is_file())
        self.assertFalse((matlab_dir / "plot_from_workbook.m").exists())
        self.assertFalse((matlab_dir / "plot_sensitivity_robustness.m").exists())

    def test_framework_template_is_not_installed_as_project_state(self):
        self.assertTrue((ROOT / "templates/model/model_paper_framework.md").is_file())
        self.assertFalse((ROOT / "模型论文框架.md").exists())

    def test_result_analysis_is_registered_after_primary_solve(self):
        router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))
        manifest = yaml.safe_load((ROOT / "core/module_manifest.yaml").read_text(encoding="utf-8"))
        order = router["execution_contract"]["workflow_order"]
        self.assertLess(order.index("solve_validate"), order.index("result_analysis"))
        self.assertLess(order.index("result_analysis"), order.index("figure_evidence"))
        self.assertNotIn("workflow_order", manifest)
        self.assertNotIn("workflow_profiles", manifest)
        self.assertEqual(
            manifest["modules"]["result_analysis"]["path"],
            "modules/03_result_analysis.md",
        )

    def test_active_documentation_matches_current_skill_version_and_taxonomy(self):
        bootstrap = yaml.safe_load((ROOT / "core/bootstrap.yaml").read_text(encoding="utf-8"))
        scripts_readme = (ROOT / "scripts/README.md").read_text(encoding="utf-8")
        legacy_readme = (ROOT / "legacy/README.md").read_text(encoding="utf-8")

        self.assertEqual(scripts_readme.splitlines()[0], "# Scripts")
        for token in ("objective", "structures", "capabilities"):
            self.assertIn(token, scripts_readme)
        self.assertNotIn("主/次题型", scripts_readme)
        self.assertIn("不属于当前默认运行链路", legacy_readme)


if __name__ == "__main__":
    unittest.main()
