from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import claim_consumption  # noqa: E402
import latex_delivery as delivery  # noqa: E402


class FigureProofFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name).resolve()
        self.latex = self.project / "final_latex"
        self.figures = self.project / "figures"
        self.latex.mkdir()
        self.figures.mkdir()
        self.main = self.latex / "main.tex"
        self.image = self.figures / "q1.png"
        self.image.write_bytes(b"image bytes")
        self.main.write_text(
            "\\documentclass{article}\n\\begin{document}\n"
            "\\begin{figure}\\includegraphics{../figures/q1.png}"
            "\\caption{Result}\\label{fig:q1}\\end{figure}\n"
            "See \\ref{fig:q1}.\\end{document}\n", encoding="utf-8")
        self.options = {"project_root": self.project,
                        "allowed_external_graphics": {"../figures/q1.png": self.image}}

    def recorder(self, *extra):
        self.main.with_suffix(".fls").write_text(
            f"PWD {self.latex}\nINPUT main.tex\n" +
            "".join(f"INPUT {item}\n" for item in extra), encoding="utf-8")


class V5SourceAndRecorderTests(FigureProofFixture):
    def test_v5_paths_hash_and_actual_image_input(self):
        self.recorder("../figures/q1.png")
        snapshot = delivery.source_bundle_snapshot(self.main, **self.options)
        self.assertEqual([item["path"] for item in snapshot["source_files"]],
                         ["figures/q1.png", "final_latex/main.tex"])
        actual = delivery.recorded_input_snapshot(self.main, **self.options)
        self.assertEqual(actual["dependency_issues"], [])
        self.assertEqual([item["path"] for item in actual["actual_input_files"]],
                         ["figures/q1.png", "final_latex/main.tex"])
        old = delivery.source_bundle_snapshot(self.main)
        self.assertEqual([item["path"] for item in old["source_files"]], ["main.tex"])
        self.image.write_bytes(b"different image bytes")
        self.assertNotEqual(snapshot["source_bundle_sha256"],
                            delivery.source_bundle_snapshot(self.main, **self.options)["source_bundle_sha256"])

    def test_v5_requires_recorder_image_and_rejects_unknown_project_input(self):
        self.recorder()
        issues = delivery.recorded_input_snapshot(self.main, **self.options)["dependency_issues"]
        self.assertTrue(any("Figure 图片未被实际编译读取" in item for item in issues), issues)
        (self.project / "other.tex").write_text("unbound", encoding="utf-8")
        self.recorder("../figures/q1.png", "../other.tex")
        issues = delivery.recorded_input_snapshot(self.main, **self.options)["dependency_issues"]
        self.assertTrue(any("不属于 final_latex" in item for item in issues), issues)
        self.assertTrue(any("未被静态审计覆盖" in item for item in issues), issues)

    def test_v5_rejects_unbound_dynamic_and_ambiguous_graphics(self):
        with self.assertRaisesRegex(ValueError, "not approved"):
            delivery.source_bundle_snapshot(self.main, project_root=self.project,
                                            allowed_external_graphics={})
        original = self.main.read_text(encoding="utf-8")
        for changed, reason in (
            (original.replace("{../figures/q1.png}", "{\\imagefile}"), "literal"),
            ("\\graphicspath{{../figures/}}\n" + original, "graphicspath"),
            (original.replace("{../figures/q1.png}", "{../figures/../figures/q1.png}"),
             "not approved"),
        ):
            with self.subTest(reason=reason):
                self.main.write_text(changed, encoding="utf-8")
                with self.assertRaises(ValueError):
                    delivery.source_bundle_snapshot(self.main, **self.options)
        self.main.write_text(original, encoding="utf-8")

    def test_v5_rejects_image_alias_when_supported(self):
        alias = self.figures / "alias.png"
        try:
            alias.symlink_to(self.image)
        except OSError:
            self.skipTest("symlink creation unavailable on this platform")
        with self.assertRaisesRegex(ValueError, "alias"):
            delivery.source_bundle_snapshot(
                self.main, project_root=self.project,
                allowed_external_graphics={"../figures/q1.png": alias})

    def test_v5_requires_explicit_extension_for_local_graphic(self):
        (self.latex / "plot.png").write_bytes(b"local image")
        self.main.write_text(self.main.read_text(encoding="utf-8").replace(
            "\\end{document}", "\\includegraphics{plot}\\end{document}"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "explicit file extension"):
            delivery.source_bundle_snapshot(self.main, **self.options)
        self.assertIn("plot.png", {row["path"] for row in
                      delivery.source_bundle_snapshot(self.main)["source_files"]})

    def test_v5_rejects_alias_nested_in_nonstandard_tex_input(self):
        real = self.latex / "real.tex"
        real.write_text("Nested text.\n", encoding="utf-8")
        alias = self.latex / "alias.tex"
        try:
            alias.symlink_to(real)
        except OSError:
            self.skipTest("symlink creation unavailable on this platform")
        (self.latex / "payload.txt").write_text("\\input{alias.tex}\n", encoding="utf-8")
        self.main.write_text(self.main.read_text(encoding="utf-8").replace(
            "\\end{document}", "\\input{payload.txt}\\end{document}"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "alias"):
            delivery.source_bundle_snapshot(self.main, **self.options)


class V5ReportTests(FigureProofFixture):
    def setUp(self):
        super().setUp()
        state_path = self.project / "state" / "project_state.yaml"
        state_path.parent.mkdir()
        state_path.write_text(yaml.safe_dump({"paper_framework": {
            "claim_consumption_policy": {
                "protocol_version": "1.3.0", "mode": "enforce_latex_text_and_figure_chain"}}}),
            encoding="utf-8")
        self.state_path = state_path
        self.framework = self.project / "模型论文框架.md"
        self.framework.write_text("# framework", encoding="utf-8")
        self.main.with_suffix(".pdf").write_bytes(b"unit PDF")
        self.main.with_suffix(".log").write_text("synthetic success\n", encoding="utf-8")
        self.recorder("../figures/q1.png")
        self.gate = {
            "status": "passed", "policy_protocol_version": "1.3.0",
            "mode": "enforce_latex_text_and_figure_chain", "human_semantic_coverage": "not_assessed",
            "observed_sources": {"project": {"state/project_state.yaml": "test"}},
            "issues": [], "figure_image_paths": ["figures/q1.png"],
            "figure_graphic_bindings": [
                {"image_token": "../figures/q1.png", "image_path": "figures/q1.png"}],
        }
        audit = {
            "audit_schema_version": "2.0.0", "status": "passed", "mode": "formal",
            "main": "main.tex",
            **delivery.source_bundle_snapshot(self.main, **self.options),
            "framework_sha256": delivery.sha256_file(self.framework),
            "claim_figure_gate": self.gate,
        }
        self.audit_path = self.latex / "latex_audit_report.yaml"
        self.audit_path.write_text(yaml.safe_dump(audit, allow_unicode=True), encoding="utf-8")

    def test_v5_report_replays_live_figure_gate_and_disallows_v4_fallback(self):
        with patch.object(claim_consumption, "formal_figure_gate", return_value=self.gate):
            report = delivery.write_compile_report(
                project=self.latex, main=self.main, profile="mcm_icm",
                engine="pdflatex", bibliography="none", sequence=["pdflatex"])
            self.assertEqual(report["report_schema_version"], "5.0.0")
            self.assertEqual(report["status"], "passed", report)
            self.assertEqual(delivery.verify_compile_report(
                project=self.latex, main=self.main, pdf=self.main.with_suffix(".pdf"), report=report), [])
            self.image.write_bytes(b"changed")
            self.assertTrue(delivery.verify_compile_report(
                project=self.latex, main=self.main, pdf=self.main.with_suffix(".pdf"), report=report))
            self.image.write_bytes(b"image bytes")
            stale_gate = dict(self.gate, figure_image_paths=["figures/other.png"])
            with patch.object(claim_consumption, "formal_figure_gate", return_value=stale_gate):
                self.assertTrue(delivery.verify_compile_report(
                    project=self.latex, main=self.main, pdf=self.main.with_suffix(".pdf"), report=report))
            self.state_path.write_text(yaml.safe_dump({"paper_framework": {
                "claim_consumption_policy": {
                    "protocol_version": "1.2.0", "mode": "enforce_latex_text"}}}), encoding="utf-8")
            self.assertTrue(any("v4" in issue for issue in delivery.verify_compile_report(
                project=self.latex, main=self.main, pdf=self.main.with_suffix(".pdf"), report=report)))

    def test_old_v4_report_cannot_satisfy_live_v5_policy(self):
        issues = delivery.verify_compile_report(project=self.latex, main=self.main,
                                                pdf=self.main.with_suffix(".pdf"),
                                                report={"report_schema_version": "4.0.0"})
        self.assertTrue(any("v5" in issue for issue in issues), issues)


if __name__ == "__main__":
    unittest.main()
