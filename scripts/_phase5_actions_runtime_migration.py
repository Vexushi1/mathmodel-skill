from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_checked(path: str, old: str, new: str, minimum: int = 1) -> None:
    text = read(path)
    count = text.count(old)
    if count < minimum:
        raise RuntimeError(f"{path}: expected at least {minimum} occurrences of {old!r}, got {count}")
    write(path, text.replace(old, new))


# Official actions only. Keep third-party latex action and all job logic unchanged.
replace_checked(".github/workflows/ci.yml", "actions/checkout@v4", "actions/checkout@v7", minimum=5)
replace_checked(".github/workflows/ci.yml", "actions/setup-python@v5", "actions/setup-python@v7", minimum=5)
replace_checked(".github/workflows/ci.yml", "actions/upload-artifact@v4", "actions/upload-artifact@v7", minimum=5)
replace_checked(".github/workflows/refresh-generated.yml", "actions/checkout@v4", "actions/checkout@v7", minimum=2)
replace_checked(".github/workflows/refresh-generated.yml", "actions/setup-python@v5", "actions/setup-python@v7", minimum=2)

# Regression locks runtime modernization without weakening Phase 1A main/feature permissions.
test = '''from __future__ import annotations\n\nimport unittest\nfrom pathlib import Path\n\nimport yaml\n\nROOT = Path(__file__).resolve().parents[1]\nCI = ROOT / ".github/workflows/ci.yml"\nREFRESH = ROOT / ".github/workflows/refresh-generated.yml"\n\n\nclass TestActionsRuntimeModernization(unittest.TestCase):\n    @classmethod\n    def setUpClass(cls):\n        cls.ci_text = CI.read_text(encoding="utf-8")\n        cls.refresh_text = REFRESH.read_text(encoding="utf-8")\n        cls.ci = yaml.safe_load(cls.ci_text)\n        cls.refresh = yaml.safe_load(cls.refresh_text)\n\n    def test_deprecated_official_action_majors_are_gone(self):\n        combined = self.ci_text + "\\n" + self.refresh_text\n        for token in ("actions/checkout@v4", "actions/setup-python@v5", "actions/upload-artifact@v4"):\n            self.assertNotIn(token, combined)\n        self.assertIn("actions/checkout@v7", combined)\n        self.assertIn("actions/setup-python@v7", combined)\n        self.assertIn("actions/upload-artifact@v7", self.ci_text)\n\n    def test_required_ci_display_names_are_unchanged(self):\n        jobs = self.ci["jobs"]\n        self.assertEqual(jobs["static-lint"]["name"], "Static contract lint")\n        self.assertEqual(jobs["unit-matrix"]["name"], "Python ${{ matrix.python-version }}")\n        self.assertEqual(jobs["latex-smoke"]["name"], "LaTeX ${{ matrix.name }}")\n        self.assertEqual(jobs["production-latex-attestation"]["name"], "Production LaTeX attestation")\n        self.assertEqual(jobs["generated-files"]["name"], "Generated file contract")\n\n    def test_ci_business_commands_and_third_party_latex_action_are_preserved(self):\n        for token in (\n            "python scripts/lint_skill.py --skip-generated",\n            "python scripts/resolve_runtime.py full_solution",\n            "python -m unittest discover -s tests",\n            "xu-cheng/latex-action@v4",\n            "python scripts/render_paper.py",\n            "python scripts/generate_indexes.py",\n        ):\n            self.assertIn(token, self.ci_text)\n\n    def test_refresh_generated_permission_boundary_is_preserved(self):\n        self.assertEqual(self.refresh["permissions"]["contents"], "read")\n        feature = self.refresh["jobs"]["refresh-feature-branch"]\n        main = self.refresh["jobs"]["verify-main"]\n        self.assertEqual(feature["permissions"]["contents"], "write")\n        self.assertEqual(main["permissions"]["contents"], "read")\n        self.assertIn("github.ref_name != 'main'", str(feature["if"]))\n        self.assertIn("github.ref_name == 'main'", str(main["if"]))\n        self.assertIn("git push", str(feature["steps"]))\n        self.assertNotIn("git push", str(main["steps"]))\n        self.assertIn("python scripts/generate_indexes.py --check", str(main["steps"]))\n\n\nif __name__ == "__main__":\n    unittest.main()\n'''
write("tests/test_actions_runtime_modernization.py", test)

# Remediation status is descriptive only; update it to current execution state.
status_path = "docs/v801_skill_health_remediation_status.md"
status = read(status_path)
old = "| Phase 5 | pending | GitHub Actions Runtime Modernization |"
new = "| Phase 5 | complete | 官方 Actions runtime 已升级到 Node-24-native v7 majors；CI job 名称与执行语义保持不变 |"
if old not in status:
    raise RuntimeError("Phase 5 pending status line not found")
write(status_path, status.replace(old, new, 1))

print("Phase 5 Actions runtime migration applied")
