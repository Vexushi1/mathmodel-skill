from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/refresh-generated.yml"


class TestGeneratedWorkflowHardening(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")
        cls.workflow = yaml.safe_load(cls.text)
        cls.jobs = cls.workflow["jobs"]

    def test_default_token_is_read_only(self):
        self.assertEqual(self.workflow["permissions"]["contents"], "read")

    def test_feature_branch_writer_is_explicit_and_not_main(self):
        job = self.jobs["refresh-feature-branch"]
        self.assertEqual(job["permissions"]["contents"], "write")
        condition = str(job["if"])
        self.assertIn("github.ref_name != 'main'", condition)
        self.assertIn("github.actor != 'github-actions[bot]'", condition)
        step_text = "\n".join(str(step) for step in job["steps"])
        self.assertIn("git push", step_text)

    def test_main_is_read_only_check_path(self):
        job = self.jobs["verify-main"]
        self.assertEqual(job["permissions"]["contents"], "read")
        self.assertIn("github.ref_name == 'main'", str(job["if"]))
        step_text = "\n".join(str(step) for step in job["steps"])
        self.assertIn("python scripts/generate_indexes.py --check", step_text)
        self.assertNotIn("git push", step_text)
        self.assertNotIn("git commit", step_text)

    def test_only_feature_writer_has_write_permission(self):
        writers = [
            name
            for name, job in self.jobs.items()
            if (job.get("permissions") or {}).get("contents") == "write"
        ]
        self.assertEqual(writers, ["refresh-feature-branch"])


if __name__ == "__main__":
    unittest.main()
