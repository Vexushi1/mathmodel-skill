from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CI = ROOT / ".github/workflows/ci.yml"
OPTIMIZATION = ROOT / ".github/workflows/optimization-baseline.yml"
TARGETED_PATTERNS = ("-p test_optimization_baseline.py", "-p test_reading_plan.py")


class TestCiPlatformPolicy(unittest.TestCase):
    def test_full_unittest_only_runs_in_two_windows_jobs(self):
        full_jobs = []
        workflows = sorted({*ROOT.glob(".github/workflows/*.yml"), *ROOT.glob(".github/workflows/*.yaml")})
        for workflow in workflows:
            jobs = yaml.safe_load(workflow.read_text(encoding="utf-8"))["jobs"]
            for job_id, job in jobs.items():
                commands = "\n".join(str(step.get("run", "")) for step in job.get("steps", []))
                for line in commands.splitlines():
                    if "python -m unittest discover -s tests" not in line:
                        continue
                    pattern = re.search(r"(?:^|\s)-p\s+['\"]?([^'\"\s]+)", line)
                    if pattern and pattern.group(1) != "test_*.py":
                        continue
                    self.assertEqual(job["runs-on"], "windows-latest", (workflow.name, job_id, line))
                    full_jobs.append((workflow.name, job_id))
        self.assertEqual(full_jobs, [("ci.yml", "unit-matrix"), ("ci.yml", "windows-unit")])

    def test_optimization_characterization_uses_windows_314_and_targeted_tests(self):
        jobs = yaml.safe_load(OPTIMIZATION.read_text(encoding="utf-8"))["jobs"]
        self.assertEqual(jobs["source_snapshot"]["runs-on"], "ubuntu-latest")
        characterize = jobs["characterize"]
        self.assertEqual(characterize["runs-on"], "windows-latest")
        setup = next(step for step in characterize["steps"]
                     if step.get("uses", "").startswith("actions/setup-python@"))
        self.assertEqual(setup["with"]["python-version"], "3.14")
        commands = "\n".join(str(step.get("run", "")) for step in characterize["steps"])
        unittest_lines = [line for line in commands.splitlines() if "python -m unittest" in line]
        self.assertEqual(len(unittest_lines), 2)
        self.assertTrue(any(TARGETED_PATTERNS[0] in line for line in unittest_lines))
        self.assertTrue(any(TARGETED_PATTERNS[1] in line for line in unittest_lines))


if __name__ == "__main__":
    unittest.main()
