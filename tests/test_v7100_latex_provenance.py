from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/latex_delivery.py"


def load_delivery_module():
    spec = importlib.util.spec_from_file_location("delivery_v7100_provenance", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestV7100LatexProvenance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.delivery = load_delivery_module()

    def test_transitive_project_local_style_changes_source_bundle_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = root / "main.tex"
            main.write_text(
                "\\documentclass{article}\n"
                "\\usepackage{outer}\n"
                "\\begin{document}x\\end{document}\n",
                encoding="utf-8",
            )
            (root / "outer.sty").write_text(
                "\\NeedsTeXFormat{LaTeX2e}\n\\RequirePackage{inner}\n",
                encoding="utf-8",
            )
            inner = root / "inner.sty"
            inner.write_text("\\ProvidesPackage{inner}\n", encoding="utf-8")

            before = self.delivery.source_bundle_snapshot(main)
            paths = {item["path"] for item in before["source_files"]}
            self.assertEqual(paths, {"main.tex", "outer.sty", "inner.sty"})

            inner.write_text("\\ProvidesPackage{inner}\n% changed\n", encoding="utf-8")
            after = self.delivery.source_bundle_snapshot(main)
            self.assertNotEqual(before["source_bundle_sha256"], after["source_bundle_sha256"])

    def test_compile_verifier_rejects_post_compile_log_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            final = project / "final_latex"
            final.mkdir()
            main = final / "main.tex"
            pdf = final / "main.pdf"
            log = final / "main.log"
            framework = project / "模型论文框架.md"
            main.write_text("\\documentclass{article}\\begin{document}x\\end{document}", encoding="utf-8")
            pdf.write_bytes(b"pdf")
            log.write_text("This is XeTeX\n", encoding="utf-8")
            framework.write_text("# 模型论文框架\n", encoding="utf-8")

            source_hash = self.delivery.source_bundle_snapshot(main)["source_bundle_sha256"]
            audit = {
                "audit_schema_version": "1.0.0",
                "status": "passed",
                "mode": "formal",
                "source_bundle_sha256": source_hash,
                "framework_sha256": self.delivery.sha256_file(framework),
            }
            (final / "latex_audit_report.yaml").write_text(
                yaml.safe_dump(audit, allow_unicode=True), encoding="utf-8"
            )
            profiles = yaml.safe_load((ROOT / "core/compile_profiles.yaml").read_text(encoding="utf-8"))
            profile = profiles["profiles"]["cumcm"]
            report = self.delivery.write_compile_report(
                project=final,
                main=main,
                profile="cumcm",
                engine="xelatex",
                bibliography="biber",
                sequence=profile["sequence"],
                profile_config=profile,
            )
            self.assertTrue(report["log_sha256"])
            self.assertEqual(
                self.delivery.verify_compile_report(project=final, main=main, pdf=pdf, report=report),
                [],
            )
            self.assertEqual(
                self.delivery.verify_compile_report(project=project, main=main, pdf=pdf, report=report),
                [],
            )

            log.write_text("This is XeTeX\npost-compile mutation\n", encoding="utf-8")
            issues = self.delivery.verify_compile_report(
                project=project,
                main=main,
                pdf=pdf,
                report=report,
            )
            self.assertTrue(any("编译日志" in item and "哈希" in item for item in issues), issues)

    def test_compile_verifier_rejects_missing_bound_log(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            final = project / "final_latex"
            final.mkdir()
            main = final / "main.tex"
            pdf = final / "main.pdf"
            log = final / "main.log"
            framework = project / "模型论文框架.md"
            main.write_text("\\documentclass{article}\\begin{document}x\\end{document}", encoding="utf-8")
            pdf.write_bytes(b"pdf")
            log.write_text("This is XeTeX\n", encoding="utf-8")
            framework.write_text("# 模型论文框架\n", encoding="utf-8")

            source_hash = self.delivery.source_bundle_snapshot(main)["source_bundle_sha256"]
            audit = {
                "audit_schema_version": "1.0.0",
                "status": "passed",
                "mode": "formal",
                "source_bundle_sha256": source_hash,
                "framework_sha256": self.delivery.sha256_file(framework),
            }
            (final / "latex_audit_report.yaml").write_text(
                yaml.safe_dump(audit, allow_unicode=True), encoding="utf-8"
            )
            profiles = yaml.safe_load((ROOT / "core/compile_profiles.yaml").read_text(encoding="utf-8"))
            profile = profiles["profiles"]["cumcm"]
            report = self.delivery.write_compile_report(
                project=final,
                main=main,
                profile="cumcm",
                engine="xelatex",
                bibliography="biber",
                sequence=profile["sequence"],
                profile_config=profile,
            )
            log.unlink()
            issues = self.delivery.verify_compile_report(
                project=project,
                main=main,
                pdf=pdf,
                report=report,
            )
            self.assertTrue(any("编译日志不存在" in item for item in issues), issues)


if __name__ == "__main__":
    unittest.main()
