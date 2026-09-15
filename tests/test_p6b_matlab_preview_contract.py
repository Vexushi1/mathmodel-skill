from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "optimization-baseline.yml"
HARNESS = ROOT / "tests" / "matlab" / "p6b_publication_preview.m"
P6A_DOC = ROOT / "docs" / "p6a_figure_reference_profile_split.md"
P6B_DOC = ROOT / "docs" / "p6b_matlab_rendering_preview.md"


class P6bMatlabPreviewContractTests(unittest.TestCase):
    def test_p6a_keeps_real_rendering_in_p6b(self) -> None:
        text = P6A_DOC.read_text(encoding="utf-8")
        self.assertIn("P6b 才负责真实 rendering/preview 证据", text)
        self.assertIn("不能用静态检查冒充", text)

    def test_registered_optimization_workflow_runs_real_mathworks_actions(self) -> None:
        raw = WORKFLOW.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
        jobs = data["jobs"]
        self.assertIn("source_snapshot", jobs)
        self.assertIn("characterize", jobs)
        self.assertIn("real_matlab_preview", jobs)
        job = jobs["real_matlab_preview"]
        self.assertEqual(job["name"], "Real MATLAB publication preview")
        self.assertEqual(job["runs-on"], "ubuntu-latest")
        self.assertLessEqual(job["timeout-minutes"], 40)
        self.assertIn("Detect preview-relevant changes", raw)
        self.assertIn("steps.preview_scope.outputs.run == 'true'", raw)
        self.assertIn("matlab-actions/setup-matlab@v3", raw)
        self.assertIn("matlab-actions/run-command@v3", raw)
        self.assertIn("release: R2024b", raw)
        self.assertIn("fonts-noto-cjk", raw)
        self.assertIn("actions/upload-artifact@v7", raw)
        self.assertIn("test -z \"$(git status --porcelain)\"", raw)
        self.assertIn("if-no-files-found: error", raw)
        self.assertNotIn("octave", raw.lower())
        self.assertNotIn("python tests/matlab", raw.lower())

    def test_preview_relevant_paths_trigger_registered_workflow(self) -> None:
        raw = WORKFLOW.read_text(encoding="utf-8")
        for path in (
            "templates/matlab/hsk_publication_profile.m",
            "templates/matlab/hsk_apply_scientific_style.m",
            "tests/matlab/p6b_publication_preview.m",
            "tests/test_p6b_matlab_preview_contract.py",
            "docs/p6b_matlab_rendering_preview.md",
            ".github/workflows/optimization-baseline.yml",
        ):
            self.assertIn(f"- {path}", raw)
        self.assertNotIn("matlab-publication-preview.yml", raw)

    def test_harness_consumes_p6a_api_and_exports_real_files(self) -> None:
        text = HARNESS.read_text(encoding="utf-8")
        for token in (
            'hsk_publication_profile(profile)',
            'hsk_apply_scientific_style(fig, profile)',
            '"competition_high_contrast"',
            '"journal_balanced"',
            '"monochrome_print"',
            'exportgraphics(fig, pngPath',
            'exportgraphics(fig, pdfPath',
            'imread(pngPath)',
            'findall(fig, "Type", "legend")',
            'findall(fig, "Type", "colorbar")',
            'monochrome_print palette is not grayscale/print-safe',
            'Preview output boundary violated',
            'preview_report.json',
        ):
            self.assertIn(token, text)
        self.assertNotIn("saveas", text)
        self.assertNotIn("print(fig", text)

    def test_p6b_doc_does_not_promote_preview_to_figure_approval(self) -> None:
        text = P6B_DOC.read_text(encoding="utf-8")
        self.assertIn("不等同于用户项目 `approved_for_paper`", text)
        self.assertIn("禁止用 Python/静态 lint/伪造图片替代真实 MATLAB preview", text)
        self.assertIn("synthetic", text.lower())


if __name__ == "__main__":
    unittest.main()
