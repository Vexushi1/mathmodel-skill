from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CI = ROOT / ".github/workflows/ci.yml"
REFRESH = ROOT / ".github/workflows/refresh-generated.yml"


class TestActionsRuntimeModernization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ci_text = CI.read_text(encoding="utf-8")
        cls.refresh_text = REFRESH.read_text(encoding="utf-8")
        cls.ci = yaml.safe_load(cls.ci_text)
        cls.refresh = yaml.safe_load(cls.refresh_text)

    def test_deprecated_official_action_majors_are_gone(self):
        combined = self.ci_text + "\n" + self.refresh_text
        for token in ("actions/checkout@v4", "actions/setup-python@v5", "actions/upload-artifact@v4"):
            self.assertNotIn(token, combined)
        self.assertIn("actions/checkout@v7", combined)
        self.assertIn("actions/setup-python@v7", combined)
        self.assertIn("actions/upload-artifact@v7", self.ci_text)

    def test_required_ci_display_names_are_unchanged(self):
        jobs = self.ci["jobs"]
        self.assertEqual(jobs["static-lint"]["name"], "Static contract lint")
        self.assertEqual(jobs["unit-matrix"]["name"], "Python ${{ matrix.python-version }}")
        self.assertEqual(jobs["latex-smoke"]["name"], "LaTeX ${{ matrix.name }}")
        self.assertEqual(jobs["production-latex-attestation"]["name"], "Production LaTeX attestation")
        self.assertEqual(jobs["generated-files"]["name"], "Generated file contract")

    def test_ci_business_commands_and_third_party_latex_action_are_preserved(self):
        for token in (
            "python scripts/lint_skill.py --skip-generated",
            "python scripts/resolve_runtime.py full_solution",
            "python -m unittest discover -s tests",
            "xu-cheng/latex-action@v4",
            "python scripts/render_paper.py",
            "python scripts/generate_indexes.py",
        ):
            self.assertIn(token, self.ci_text)

    def test_refresh_generated_permission_boundary_is_preserved(self):
        self.assertEqual(self.refresh["permissions"]["contents"], "read")
        feature = self.refresh["jobs"]["refresh-feature-branch"]
        main = self.refresh["jobs"]["verify-main"]
        self.assertEqual(feature["permissions"]["contents"], "write")
        self.assertEqual(main["permissions"]["contents"], "read")
        self.assertIn("github.ref_name != 'main'", str(feature["if"]))
        self.assertIn("github.ref_name == 'main'", str(main["if"]))
        self.assertIn("git push", str(feature["steps"]))
        self.assertNotIn("git push", str(main["steps"]))
        self.assertIn("python scripts/generate_indexes.py --check", str(main["steps"]))


if __name__ == "__main__":
    unittest.main()
