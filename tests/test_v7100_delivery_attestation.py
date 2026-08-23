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


class TestV7100DeliveryAttestation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = load_module("audit_v7100", SCRIPTS / "audit_latex_project.py")
        cls.delivery = load_module("delivery_v7100", SCRIPTS / "latex_delivery.py")
        cls.render = load_module("render_v7100", SCRIPTS / "render_paper.py")
        cls.pack = load_module("pack_v7100", SCRIPTS / "hsk_pack_submission.py")
        cls.package_validator = load_module("package_validator_v7100", SCRIPTS / "validate_submission_package.py")

    def test_formal_audit_report_binds_source_and_framework(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            final = project / "final_latex"
            final.mkdir()
            main = final / "main.tex"
            main.write_text("\\documentclass{article}\n\\begin{document}\n正文。\n\\end{document}\n", encoding="utf-8")
            framework = project / "模型论文框架.md"
            framework.write_text("# 模型论文框架\n", encoding="utf-8")
            findings = self.audit.audit_project(main, framework_path=framework, require_framework=True)
            report = self.audit.write_audit_report(
                main_file=main,
                findings=findings,
                framework_path=framework,
                mode="formal",
            )
            self.assertEqual(report["audit_schema_version"], "1.0.0")
            self.assertEqual(report["source_bundle_sha256"], self.delivery.source_bundle_snapshot(main)["source_bundle_sha256"])
            self.assertEqual(report["framework_sha256"], self.delivery.sha256_file(framework))

    def test_formal_audit_blocks_missing_framework(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = root / "main.tex"
            main.write_text("\\documentclass{article}\\begin{document}x\\end{document}", encoding="utf-8")
            findings = self.audit.audit_project(
                main,
                framework_path=root / "missing.md",
                require_framework=True,
            )
            self.assertTrue(any(item.code == "latex_framework_missing" and item.severity == "blocking" for item in findings))

    def test_compile_report_without_log_cannot_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            main = project / "main.tex"
            pdf = project / "main.pdf"
            main.write_text("\\documentclass{article}\\begin{document}x\\end{document}", encoding="utf-8")
            pdf.write_bytes(b"pdf")
            audit_report = {
                "audit_schema_version": "1.0.0",
                "status": "passed",
                "mode": "template_smoke",
                "source_bundle_sha256": self.delivery.source_bundle_snapshot(main)["source_bundle_sha256"],
                "framework_sha256": None,
            }
            (project / "latex_audit_report.yaml").write_text(
                yaml.safe_dump(audit_report, allow_unicode=True), encoding="utf-8"
            )
            report = self.delivery.write_compile_report(
                project=project,
                main=main,
                profile="cumcm",
                engine="xelatex",
                bibliography="biber",
                sequence=["xelatex", "biber", "xelatex", "xelatex"],
                profile_config={
                    "engine": "xelatex",
                    "bibliography": "biber",
                    "sequence": ["xelatex", "biber", "xelatex", "xelatex"],
                },
                attestation_mode="template_smoke",
            )
            self.assertEqual(report["status"], "failed")
            self.assertFalse(report["log_present"])

    def test_compile_report_detects_profile_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            main = project / "main.tex"
            pdf = project / "main.pdf"
            main.write_text("\\documentclass{article}\\begin{document}x\\end{document}", encoding="utf-8")
            pdf.write_bytes(b"pdf")
            (project / "main.log").write_text("This is XeTeX\n", encoding="utf-8")
            snapshot = self.delivery.source_bundle_snapshot(main)["source_bundle_sha256"]
            audit_report = {
                "audit_schema_version": "1.0.0",
                "status": "passed",
                "mode": "formal",
                "source_bundle_sha256": snapshot,
                "framework_sha256": None,
            }
            (project / "latex_audit_report.yaml").write_text(yaml.safe_dump(audit_report), encoding="utf-8")
            report = self.delivery.write_compile_report(
                project=project,
                main=main,
                profile="cumcm",
                engine="xelatex",
                bibliography="biber",
                sequence=["xelatex", "biber", "xelatex", "xelatex"],
                profile_config={"engine": "xelatex", "bibliography": "biber", "sequence": ["xelatex"]},
                attestation_mode="template_smoke",
            )
            self.assertTrue(report["compile_profile_sha256"])

    def test_render_materializes_cumcm_class_before_audit(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            self.assertFalse((project / "cumcmthesis.cls").exists())
            self.render.prepare_profile_files(project, "cumcm")
            class_file = project / "cumcmthesis.cls"
            self.assertTrue(class_file.is_file())
            text = class_file.read_text(encoding="utf-8")
            self.assertIn("IfFontExistsTF", text)

    def test_official_packaging_refuses_unverified_rules(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(SystemExit):
                self.pack.official_files(root, "CUMCM")

    def test_reproducibility_manifest_detects_stale_packaged_pdf(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            final = root / "final_latex"
            final.mkdir()
            (final / "main.pdf").write_bytes(b"pdf-v1")
            (root / "模型论文框架.md").write_text("framework", encoding="utf-8")
            (root / "q.py").write_text("print(1)", encoding="utf-8")
            (root / "r.xlsx").write_bytes(b"xlsx")
            (root / "q.m").write_text("disp(1)", encoding="utf-8")
            state_dir = root / "state"
            state_dir.mkdir()
            (state_dir / "project_state.yaml").write_text(
                yaml.safe_dump({"artifacts": {"compiled_pdf": "final_latex/main.pdf"}}), encoding="utf-8"
            )
            package = root / "package.zip"
            files = self.pack.reproducibility_files(root, package)
            manifest = self.pack.build_manifest(root, files, kind="reproducibility", metadata={
                "competition_profile": None,
                "rule_verification_status": None,
                "rule_verified_at": None,
                "rule_source": None,
                "submission_files_allowlist": None,
            })
            import zipfile
            with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as archive:
                for path in files:
                    archive.write(path, path.relative_to(root).as_posix())
                archive.writestr("submission_manifest.yaml", yaml.safe_dump(manifest, allow_unicode=True))
            self.assertEqual(self.package_validator.validate_package(root, package)["status"], "passed")
            (final / "main.pdf").write_bytes(b"pdf-v2")
            report = self.package_validator.validate_package(root, package)
            self.assertEqual(report["status"], "failed")
            self.assertTrue(any("compiled_pdf" in item or "当前项目版本" in item for item in report["issues"]), report)


if __name__ == "__main__":
    unittest.main()
