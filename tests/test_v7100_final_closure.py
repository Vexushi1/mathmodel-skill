from __future__ import annotations

import hashlib
import importlib.util
import sys
import tempfile
import unittest
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


class TestV7100FinalClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = load_module("audit_v7100_final", SCRIPTS / "audit_latex_project.py")
        cls.render = load_module("render_v7100_final", SCRIPTS / "render_paper.py")
        cls.profiles = yaml.safe_load((ROOT / "core/compile_profiles.yaml").read_text(encoding="utf-8"))["profiles"]

    def test_cumcm_profile_rejects_article_document_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            main = Path(temp) / "main.tex"
            main.write_text("\\documentclass{article}\\begin{document}x\\end{document}", encoding="utf-8")
            with self.assertRaises(SystemExit):
                self.render.validate_profile_identity(main, "cumcm", self.profiles["cumcm"])

    def test_cumcm_profile_accepts_cumcmthesis_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            main = Path(temp) / "main.tex"
            main.write_text(
                "\\documentclass[withoutpreface]{cumcmthesis}\\begin{document}x\\end{document}",
                encoding="utf-8",
            )
            self.render.validate_profile_identity(main, "cumcm", self.profiles["cumcm"])

    def test_explicit_missing_framework_blocks_without_require_flag(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = root / "main.tex"
            main.write_text("\\documentclass{article}\\begin{document}x\\end{document}", encoding="utf-8")
            findings = self.audit.audit_project(main, framework_path=root / "missing.md")
            self.assertTrue(
                any(item.code == "latex_framework_missing" and item.severity == "blocking" for item in findings),
                findings,
            )

    def test_normal_render_runs_one_formal_audit_and_persists_before_compiling(self):
        # Run the production render coordinator and audit writer. Stop at the
        # external compiler boundary: this unit fixture does not claim a TeX run.
        # Use LF fixture bytes so independent raw hashes also match the existing
        # normalized UTF-8/LF source-attestation hashes on Windows.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            final = root / "final_latex"
            final.mkdir()
            main = final / "main.tex"
            main.write_text(
                "\\documentclass{article}\n\\begin{document}\n"
                "\\input{sections/result}\n\\end{document}\n",
                encoding="utf-8", newline="\n",
            )
            (final / "sections").mkdir()
            result = final / "sections/result.tex"
            result.write_text("A bounded result.\n", encoding="utf-8", newline="\n")
            framework = root / "模型论文框架.md"
            framework.write_text("# 模型论文框架\n", encoding="utf-8", newline="\n")
            profile = {"engine": "xelatex", "bibliography": "none", "sequence": ["xelatex"]}
            report_path = final / "latex_audit_report.yaml"

            class CompilerBoundaryReached(RuntimeError):
                pass

            def stop_at_compiler(*args):
                self.assertTrue(report_path.is_file())
                report = yaml.safe_load(report_path.read_text(encoding="utf-8"))
                self.assertEqual(report["status"], "passed", report)
                self.assertEqual(report["mode"], "formal")
                self.assertEqual(report["main"], "main.tex")
                self.assertEqual(report["framework_sha256"], hashlib.sha256(framework.read_bytes()).hexdigest())
                sources = {item["path"]: item["sha256"] for item in report["source_files"]}
                self.assertEqual(sources["main.tex"], hashlib.sha256(main.read_bytes()).hexdigest())
                self.assertEqual(sources["sections/result.tex"], hashlib.sha256(result.read_bytes()).hexdigest())
                raise CompilerBoundaryReached

            with patch.object(sys, "argv", ["render_paper.py", str(final), "--profile", "audit_test"]), \
                    patch.object(self.render, "load_profiles", return_value={"audit_test": profile}), \
                    patch.object(self.render, "audit_project", wraps=self.render.audit_project) as audit, \
                    patch.object(self.render, "write_audit_report", wraps=self.render.write_audit_report) as writer, \
                    patch.object(self.render, "compile_project", side_effect=stop_at_compiler) as compiler, \
                    patch.object(self.render, "write_compile_report") as compile_writer:
                with self.assertRaises(CompilerBoundaryReached):
                    self.render.main()
            audit.assert_called_once_with(main, framework_path=framework, require_framework=True, formal=True)
            self.assertEqual(writer.call_count, 1)
            self.assertEqual(writer.call_args.kwargs["mode"], "formal")
            compiler.assert_called_once()
            compile_writer.assert_not_called()

    def test_normal_render_missing_framework_never_compiles_or_creates_attestation(self):
        with tempfile.TemporaryDirectory() as temp:
            final = Path(temp).resolve() / "final_latex"
            final.mkdir()
            main = final / "main.tex"
            main.write_text(
                "\\documentclass{article}\\begin{document}x\\end{document}",
                encoding="utf-8", newline="\n",
            )
            profile = {"engine": "xelatex", "bibliography": "none", "sequence": ["xelatex"]}
            with patch.object(sys, "argv", ["render_paper.py", str(final), "--profile", "audit_test"]), \
                    patch.object(self.render, "load_profiles", return_value={"audit_test": profile}), \
                    patch.object(self.render, "compile_project") as compiler:
                with self.assertRaisesRegex(SystemExit, "requires current framework"):
                    self.render.main()
            compiler.assert_not_called()
            self.assertFalse((final / "latex_audit_report.yaml").exists())

    def test_render_audit_persists_real_failure_and_blocks_compile(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            final = root / "final_latex"
            final.mkdir()
            main = final / "main.tex"
            main.write_text(
                "\\documentclass{article}\\begin{document}"
                "\\label{same}\\label{same}x\\end{document}", encoding="utf-8", newline="\n",
            )
            (root / "模型论文框架.md").write_text("# 模型论文框架\n", encoding="utf-8", newline="\n")
            profile = {"engine": "xelatex", "bibliography": "none", "sequence": ["xelatex"]}
            with patch.object(sys, "argv", ["render_paper.py", str(final), "--profile", "audit_test"]), \
                    patch.object(self.render, "load_profiles", return_value={"audit_test": profile}), \
                    patch.object(self.render, "compile_project") as compiler:
                with self.assertRaisesRegex(SystemExit, "LaTeX project audit failed"):
                    self.render.main()
            compiler.assert_not_called()
            report = yaml.safe_load((final / "latex_audit_report.yaml").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "failed")
            self.assertEqual(report["mode"], "formal")
            self.assertTrue(any(item["code"] == "duplicate_label" for item in report["findings"]))

    def test_submission_pack_documents_unique_zip_fallback(self):
        text = (ROOT / "packs/artifact/full_submission.md").read_text(encoding="utf-8")
        self.assertIn("恰好存在一个 ZIP", text)
        self.assertIn("存在多个 ZIP", text)
        self.assertIn("submission/submission.zip", text)


if __name__ == "__main__":
    unittest.main()
