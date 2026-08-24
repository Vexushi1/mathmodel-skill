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

    def test_canonical_formal_audit_command_persists_attestation(self):
        text = (ROOT / "packs/artifact/latex.md").read_text(encoding="utf-8")
        for token in ("--mode formal", "--require-framework", "--write-report", "--strict"):
            self.assertIn(token, text)

    def test_submission_pack_documents_unique_zip_fallback(self):
        text = (ROOT / "packs/artifact/full_submission.md").read_text(encoding="utf-8")
        self.assertIn("恰好存在一个 ZIP", text)
        self.assertIn("存在多个 ZIP", text)
        self.assertIn("submission/submission.zip", text)


if __name__ == "__main__":
    unittest.main()
