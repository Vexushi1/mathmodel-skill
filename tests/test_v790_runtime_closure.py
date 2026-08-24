from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def load_module(name: str, path: Path):
    parent = str(path.parent)
    added = parent not in sys.path
    if added:
        sys.path.insert(0, parent)
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        if added:
            sys.path.remove(parent)


class TestV790RuntimeClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resolver = load_module("resolver_v790_runtime", SCRIPTS / "resolve_workflow.py")
        cls.audit = load_module("audit_v790_runtime", SCRIPTS / "audit_latex_project.py")
        cls.delivery = load_module("latex_delivery_v790", SCRIPTS / "latex_delivery.py")
        cls.sync = load_module("sync_v790_runtime", SCRIPTS / "sync_project.py")

    def test_full_workflow_loads_downstream_artifact_packs_and_final_package(self):
        plan = self.resolver.resolve_workflow(
            "full_workflow",
            objective="optimization",
            competition="CUMCM",
            available_artifacts=[
                "solution_workbook", "accepted_solution_workbook", "result_quality_report",
                "result_analysis_workbook", "accepted_result_analysis_workbook", "validated_results",
            ],
        )
        for pack in (
            "packs/artifact/figure.md",
            "packs/artifact/latex.md",
            "packs/artifact/review.md",
            "packs/artifact/full_submission.md",
        ):
            self.assertIn(pack, plan["packs"])
        self.assertIn("validated_submission_package", plan["terminal_outputs"])
        self.assertIn("submission_package_validation_report", plan["terminal_outputs"])
        gate_names = {item["name"] for item in plan["pre_delivery_gates"]}
        self.assertIn("submission_package_validation", gate_names)

    def test_cumcm_current_project_template_authority_is_hsk(self):
        compile_profiles = yaml.safe_load((ROOT / "core/compile_profiles.yaml").read_text(encoding="utf-8"))
        competition = yaml.safe_load((ROOT / "config/competition_profiles.yaml").read_text(encoding="utf-8"))
        self.assertEqual(compile_profiles["profiles"]["cumcm"]["template_directory"], "templates/latex/cumcm/hsk")
        self.assertEqual(competition["profiles"]["cumcm"]["stable"]["latex_template"], "templates/latex/cumcm/hsk/")
        pack = (ROOT / "packs/competition/cumcm.md").read_text(encoding="utf-8")
        module = (ROOT / "modules/05_writing/latex.md").read_text(encoding="utf-8")
        self.assertIn("templates/latex/cumcm/hsk/", pack)
        self.assertIn("templates/latex/cumcm/hsk/", module)

    def test_public_latex_audit_entrypoint_is_project_wrapper(self):
        output = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        self.assertEqual(output["writing_policy"]["latex_audit_entrypoint"], "scripts/audit_latex_project.py")
        for relative in (
            "SKILL.md", "PROJECT_INSTRUCTIONS.md", "RUNTIME_ROUTER.md",
            "modules/05_writing/latex.md", "modules/05_writing/ai_cleanup.md",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("audit_latex_project.py", text, relative)
            self.assertNotIn("python scripts/audit_paper_prose.py final_latex/main.tex", text, relative)

    def test_current_paper_fragment_source_must_be_in_active_include_graph(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            final = project / "final_latex"
            (final / "sections").mkdir(parents=True)
            main = final / "main.tex"
            active = final / "sections/q1.tex"
            orphan = final / "sections/orphan.tex"
            main.write_text(r"\documentclass{article}\begin{document}\input{sections/q1}\end{document}", encoding="utf-8")
            active.write_text("active", encoding="utf-8")
            orphan.write_text("orphan", encoding="utf-8")
            framework = project / "模型论文框架.md"
            framework.write_text(
                "### Paper Fragment Dependency Map\n\n"
                "| Fragment ID | 类型 | 范围 | 依赖对象 | 正文/摘要锚点 | LaTeX 源码文件（可选） | 状态 |\n"
                "|---|---|---|---|---|---|---|\n"
                "| paper.q1 | question_model_text | Q1 | Q1.model | x | `final_latex/sections/q1.tex` | current |\n",
                encoding="utf-8",
            )
            findings = self.audit.audit_project(main, framework_path=framework)
            self.assertFalse(any(item.code.startswith("paper_fragment_source_") for item in findings), findings)
            framework.write_text(
                framework.read_text(encoding="utf-8").replace("q1.tex", "orphan.tex"), encoding="utf-8"
            )
            findings = self.audit.audit_project(main, framework_path=framework)
            self.assertTrue(
                any(item.code == "paper_fragment_source_not_in_active_graph" and item.severity == "blocking" for item in findings),
                findings,
            )

    def test_source_bundle_hash_changes_with_child_tex_and_graphic(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "sections").mkdir()
            (root / "figures").mkdir()
            main = root / "main.tex"
            child = root / "sections/q1.tex"
            image = root / "figures/a.png"
            main.write_text(
                r"\documentclass{article}\begin{document}\input{sections/q1}\end{document}", encoding="utf-8"
            )
            child.write_text(r"value\includegraphics{figures/a.png}", encoding="utf-8")
            image.write_bytes(b"image-a")
            first = self.delivery.source_bundle_snapshot(main)["source_bundle_sha256"]
            child.write_text(r"value2\includegraphics{figures/a.png}", encoding="utf-8")
            second = self.delivery.source_bundle_snapshot(main)["source_bundle_sha256"]
            self.assertNotEqual(first, second)
            image.write_bytes(b"image-b")
            third = self.delivery.source_bundle_snapshot(main)["source_bundle_sha256"]
            self.assertNotEqual(second, third)

    def test_compile_report_and_sync_detect_post_compile_source_change(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            final = project / "final_latex"
            (final / "sections").mkdir(parents=True)
            main = final / "main.tex"
            child = final / "sections/q1.tex"
            pdf = final / "main.pdf"
            framework = project / "模型论文框架.md"
            main.write_text(r"\documentclass{article}\begin{document}\input{sections/q1}\end{document}", encoding="utf-8")
            child.write_text("v1", encoding="utf-8")
            pdf.write_bytes(b"pdf-v1")
            framework.write_text("framework", encoding="utf-8")
            (final / "main.log").write_text("This is XeTeX\n", encoding="utf-8")
            source_hash = self.delivery.source_bundle_snapshot(main)["source_bundle_sha256"]
            audit_report = {
                "audit_schema_version": "1.0.0",
                "status": "passed",
                "mode": "formal",
                "source_bundle_sha256": source_hash,
                "framework_sha256": self.delivery.sha256_file(framework),
            }
            (final / "latex_audit_report.yaml").write_text(
                yaml.safe_dump(audit_report, allow_unicode=True), encoding="utf-8"
            )
            profiles = yaml.safe_load((ROOT / "core/compile_profiles.yaml").read_text(encoding="utf-8"))
            cumcm_profile = profiles["profiles"]["cumcm"]
            report = self.delivery.write_compile_report(
                project=final,
                main=main,
                profile="cumcm",
                engine="xelatex",
                bibliography="biber",
                sequence=cumcm_profile["sequence"],
                profile_config=cumcm_profile,
            )
            self.assertEqual(report["status"], "passed")
            state = {
                "artifacts": {
                    "latex_source": "final_latex/main.tex",
                    "compiled_pdf": "final_latex/main.pdf",
                    "compile_report": "final_latex/compile_report.yaml",
                }
            }
            self.assertEqual(self.sync._compile_artifact_issues(project, state), [])
            child.write_text("v2", encoding="utf-8")
            issues = self.sync._compile_artifact_issues(project, state)
            self.assertTrue(any("source bundle" in item and "stale" in item for item in issues), issues)

    def test_one_shot_migration_artifacts_are_absent(self):
        self.assertFalse((ROOT / "scripts/_v790_runtime_closure_migration.py").exists())
        refresh = (ROOT / ".github/workflows/refresh-generated.yml").read_text(encoding="utf-8")
        self.assertNotIn("Apply one-shot v7.9.0 runtime closure", refresh)
        self.assertNotIn("Patch one-shot migration runner", refresh)

    def test_render_paper_is_the_compile_report_producer(self):
        text = (ROOT / "scripts/render_paper.py").read_text(encoding="utf-8")
        self.assertIn("write_compile_report", text)
        self.assertIn("compile_report.yaml", text)
        self.assertIn("create_audit_attestation", text)


if __name__ == "__main__":
    unittest.main()
