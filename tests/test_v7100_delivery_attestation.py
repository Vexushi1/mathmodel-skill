from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

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

    def test_audit_attestation_separates_gate_status_from_highest_severity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = root / "main.tex"
            main.write_text("\\documentclass{article}\\begin{document}x\\end{document}", encoding="utf-8")
            warning = [self.audit.Finding("warning", "w", "warning-only")]
            formal_warning = self.audit.write_audit_report(main_file=main, findings=warning, mode="formal")
            self.assertEqual(formal_warning["status"], "passed")
            self.assertEqual(formal_warning["highest_severity"], "warning")
            review = [self.audit.Finding("review_required", "r", "needs review")]
            formal_review = self.audit.write_audit_report(main_file=main, findings=review, mode="formal")
            self.assertEqual(formal_review["status"], "failed")
            smoke_review = self.audit.write_audit_report(main_file=main, findings=review, mode="template_smoke")
            self.assertEqual(smoke_review["status"], "passed")
            self.assertEqual(smoke_review["highest_severity"], "review_required")

    def test_failed_audit_report_is_persisted_for_invalid_source_graph(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = root / "main.tex"
            main.write_text(
                r"\documentclass{article}\begin{document}\input{sections/missing}\end{document}",
                encoding="utf-8",
            )
            findings = self.audit.audit_project(main)
            self.assertTrue(any(item.code == "latex_include_missing" for item in findings), findings)
            report_path = root / "latex_audit_report.yaml"
            report = self.audit.write_audit_report(
                main_file=main,
                findings=findings,
                report_path=report_path,
                mode="formal",
            )
            self.assertTrue(report_path.is_file())
            self.assertEqual(report["status"], "failed")
            self.assertIsNone(report["source_bundle_sha256"])
            self.assertTrue(report["source_snapshot_error"])

    def test_render_stops_when_persisted_audit_attestation_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            final = project / "final_latex"
            final.mkdir()
            main = final / "main.tex"
            main.write_text("\\documentclass{article}\\begin{document}x\\end{document}", encoding="utf-8")
            (project / "模型论文框架.md").write_text("# 模型论文框架\n", encoding="utf-8")
            with patch.object(self.render, "audit_project", return_value=[]), patch.object(
                self.render,
                "write_audit_report",
                return_value={"status": "failed", "highest_severity": "warning"},
            ):
                with self.assertRaises(SystemExit):
                    self.render.create_audit_attestation(final, main, template_smoke=False)

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

    def test_source_bundle_ignores_literal_include_inside_verbatim(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = root / "main.tex"
            main.write_text(
                "\\documentclass{article}\n"
                "\\begin{document}\n"
                "\\begin{verbatim}\n"
                "\\input{sections/missing}\n"
                "\\end{verbatim}\n"
                "正文。\n"
                "\\end{document}\n",
                encoding="utf-8",
            )
            snapshot = self.delivery.source_bundle_snapshot(main)
            self.assertEqual([item["path"] for item in snapshot["source_files"]], ["main.tex"])

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

    def test_compile_verifier_detects_profile_definition_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            final = project / "final_latex"
            final.mkdir()
            main = final / "main.tex"
            pdf = final / "main.pdf"
            framework = project / "模型论文框架.md"
            main.write_text("\\documentclass{article}\\begin{document}x\\end{document}", encoding="utf-8")
            pdf.write_bytes(b"pdf")
            (final / "main.log").write_text("This is XeTeX\n", encoding="utf-8")
            framework.write_text("# 模型论文框架\n", encoding="utf-8")
            snapshot = self.delivery.source_bundle_snapshot(main)["source_bundle_sha256"]
            audit_report = {
                "audit_schema_version": "1.0.0",
                "status": "passed",
                "mode": "formal",
                "source_bundle_sha256": snapshot,
                "framework_sha256": self.delivery.sha256_file(framework),
            }
            (final / "latex_audit_report.yaml").write_text(
                yaml.safe_dump(audit_report, allow_unicode=True), encoding="utf-8"
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
            drifted = dict(profile)
            drifted["sequence"] = ["xelatex", "xelatex"]
            with patch.object(self.delivery, "current_profile_config", return_value=drifted):
                issues = self.delivery.verify_compile_report(
                    project=final,
                    main=main,
                    pdf=pdf,
                    report=report,
                )
            self.assertTrue(any("编译profile定义已变化" in item for item in issues), issues)

    def test_compile_verifier_detects_override_flag_tampering(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            final = project / "final_latex"
            final.mkdir()
            main = final / "main.tex"
            pdf = final / "main.pdf"
            framework = project / "模型论文框架.md"
            main.write_text("\\documentclass{article}\\begin{document}x\\end{document}", encoding="utf-8")
            pdf.write_bytes(b"pdf")
            (final / "main.log").write_text("This is XeTeX\n", encoding="utf-8")
            framework.write_text("# 模型论文框架\n", encoding="utf-8")
            snapshot = self.delivery.source_bundle_snapshot(main)["source_bundle_sha256"]
            audit_report = {
                "audit_schema_version": "1.0.0",
                "status": "passed",
                "mode": "formal",
                "source_bundle_sha256": snapshot,
                "framework_sha256": self.delivery.sha256_file(framework),
            }
            (final / "latex_audit_report.yaml").write_text(
                yaml.safe_dump(audit_report, allow_unicode=True), encoding="utf-8"
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
            tampered = dict(report)
            tampered["profile_override_used"] = True
            issues = self.delivery.verify_compile_report(
                project=final,
                main=main,
                pdf=pdf,
                report=tampered,
            )
            self.assertTrue(any("profile_override_used" in item for item in issues), issues)

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

    def test_official_package_positive_path_uses_verified_exact_allowlist(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            final = root / "final_latex"
            final.mkdir()
            pdf = final / "main.pdf"
            pdf.write_bytes(b"official-pdf")
            state_dir = root / "state"
            state_dir.mkdir()
            (state_dir / "project_state.yaml").write_text(
                yaml.safe_dump({"artifacts": {"compiled_pdf": "final_latex/main.pdf"}}), encoding="utf-8"
            )
            profiles_path = root / "competition_profiles.yaml"
            profiles_path.write_text(
                yaml.safe_dump(
                    {
                        "profiles": {
                            "demo": {
                                "aliases": ["DEMO"],
                                "edition_rules": {
                                    "verification_status": "verified",
                                    "verified_at": "2026-08-24",
                                    "source": "official-demo-rule",
                                    "submission_files": ["final_latex/main.pdf"],
                                },
                            }
                        }
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            package = root / "submission.zip"
            with patch.object(self.pack, "COMPETITION_PROFILES", profiles_path), patch.object(
                self.package_validator, "COMPETITION_PROFILES", profiles_path
            ):
                files, metadata = self.pack.official_files(root, "DEMO")
                manifest = self.pack.build_manifest(root, files, kind="official", metadata=metadata)
                with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as archive:
                    for path in files:
                        archive.write(path, path.relative_to(root).as_posix())
                    archive.writestr("submission_manifest.yaml", yaml.safe_dump(manifest, allow_unicode=True))
                report = self.package_validator.validate_package(root, package, competition="DEMO")
            self.assertEqual(report["status"], "passed", report)

    def test_declared_package_path_refuses_ambiguous_zip_selection(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            submission = root / "submission"
            submission.mkdir()
            (submission / "submission.zip").write_bytes(b"one")
            (submission / "reproducibility.zip").write_bytes(b"two")
            with self.assertRaises(SystemExit):
                self.package_validator.declared_package_path(root, {})

    def test_reproducibility_package_requires_framework(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            final = root / "final_latex"
            final.mkdir()
            pdf = final / "main.pdf"
            pdf.write_bytes(b"pdf")
            py_file = root / "q.py"
            py_file.write_text("print(1)", encoding="utf-8")
            workbook = root / "r.xlsx"
            workbook.write_bytes(b"xlsx")
            matlab = root / "q.m"
            matlab.write_text("disp(1)", encoding="utf-8")
            state_dir = root / "state"
            state_dir.mkdir()
            (state_dir / "project_state.yaml").write_text(
                yaml.safe_dump({"artifacts": {"compiled_pdf": "final_latex/main.pdf"}}), encoding="utf-8"
            )
            files = [pdf, py_file, workbook, matlab]
            metadata = {
                "competition_profile": None,
                "rule_verification_status": None,
                "rule_verified_at": None,
                "rule_source": None,
                "submission_files_allowlist": None,
            }
            manifest = self.pack.build_manifest(root, files, kind="reproducibility", metadata=metadata)
            package = root / "package.zip"
            with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as archive:
                for path in files:
                    archive.write(path, path.relative_to(root).as_posix())
                archive.writestr("submission_manifest.yaml", yaml.safe_dump(manifest, allow_unicode=True))
            report = self.package_validator.validate_package(root, package)
            self.assertEqual(report["status"], "failed")
            self.assertTrue(any("模型论文框架.md" in item for item in report["issues"]), report)

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
            with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as archive:
                for path in files:
                    archive.write(path, path.relative_to(root).as_posix())
                archive.writestr("submission_manifest.yaml", yaml.safe_dump(manifest, allow_unicode=True))
            self.assertEqual(self.package_validator.validate_package(root, package)["status"], "passed")
            (final / "main.pdf").write_bytes(b"pdf-v2")
            report = self.package_validator.validate_package(root, package)
            self.assertEqual(report["status"], "failed")
            self.assertTrue(any("compiled_pdf" in item or "当前项目版本" in item for item in report["issues"]), report)

    def test_submission_package_is_promoted_only_after_validation_gate(self):
        manifest = yaml.safe_load((ROOT / "core/module_manifest.yaml").read_text(encoding="utf-8"))
        output = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        review_outputs = manifest["modules"]["review_delivery"]["outputs"]
        gate = manifest["utility_gates"]["submission_package_validation"]
        submission_requirements = output["project_sync"]["stage_requirements"]["submission"]
        self.assertIn("submission_package", review_outputs)
        self.assertNotIn("validated_submission_package", review_outputs)
        self.assertIn("submission_package", gate["inputs"])
        self.assertIn("validated_submission_package", gate["outputs"])
        self.assertIn("submission_package", submission_requirements)
        self.assertNotIn("validated_submission_package", submission_requirements)


if __name__ == "__main__":
    unittest.main()
