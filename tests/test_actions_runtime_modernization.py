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
        self.assertEqual(jobs["windows-unit"]["name"], "Windows Python 3.14")
        self.assertEqual(jobs["matlab-solver-smoke"]["name"], "MATLAB R2024b native solver contracts")
        self.assertEqual(jobs["latex-smoke"]["name"], "LaTeX ${{ matrix.name }}")
        self.assertEqual(jobs["production-latex-attestation"]["name"], "Production LaTeX attestation")
        self.assertEqual(jobs["generated-files"]["name"], "Generated file contract")

    def test_formal_python_full_regression_is_windows_310_and_314_only(self):
        jobs = self.ci["jobs"]
        matrix = jobs["unit-matrix"]
        self.assertEqual(matrix["runs-on"], "windows-latest")
        self.assertEqual(matrix["strategy"]["matrix"]["python-version"], ["3.10"])
        windows = jobs["windows-unit"]
        self.assertEqual(windows["runs-on"], "windows-latest")
        self.assertEqual(
            next(step["with"]["python-version"] for step in windows["steps"]
                 if step.get("uses", "").startswith("actions/setup-python@")),
            "3.14",
        )
        for version, worker_id, gate_id in (
            ("3.10", "unit-matrix-shards", "unit-matrix"),
            ("3.14", "windows-unit-shards", "windows-unit"),
        ):
            worker = jobs[worker_id]
            self.assertEqual(worker["runs-on"], "windows-latest")
            self.assertEqual(worker["env"]["PYTHONUTF8"], "1")
            self.assertEqual(worker["strategy"]["matrix"]["shard"], [0, 1, 2, 3])
            self.assertFalse(worker["strategy"]["fail-fast"])
            self.assertIn("generated-files", worker["needs"])
            self.assertIn("== 'true'", worker["if"])
            setup = next(step for step in worker["steps"]
                         if step.get("uses", "").startswith("actions/setup-python@"))
            self.assertEqual(setup["with"]["python-version"], version)
            commands = "\n".join(step.get("run", "") for step in worker["steps"])
            self.assertIn("ci_unittest.py run --shard-index", commands)
            self.assertIn("--shard-count 4", commands)
            self.assertNotIn("--modules", commands)
            self.assertIn("exit $testExit", commands)
            artifact = next(step for step in worker["steps"]
                            if step.get("uses", "").startswith("actions/upload-artifact@"))
            self.assertEqual(artifact["if"], "always()")
            self.assertIn("timings.json", artifact["with"]["path"])
            gate = jobs[gate_id]
            self.assertIn(worker_id, gate["needs"])
            self.assertIn("always()", gate["if"])
            self.assertIn("needs.test-plan.result != 'success'", gate["if"])
            commands = "\n".join(step.get("run", "") for step in gate["steps"])
            self.assertIn("$env:SHARD_RESULT -ne 'success'", commands)
            self.assertIn("gh run download $env:GITHUB_RUN_ID", commands)
            self.assertIn(f"--python-version {version}", commands)
            self.assertIn("ci_unittest.py verify", commands)

    def test_development_is_targeted_and_pr_freeze_or_main_has_full_path(self):
        events = self.ci.get("on", self.ci.get(True))
        self.assertEqual(events["push"]["branches"], ["main"])
        self.assertIn("ready_for_review", events["pull_request"]["types"])
        options = events["workflow_dispatch"]["inputs"]["python_test_mode"]
        self.assertEqual(options["options"], ["targeted", "full"])
        self.assertEqual(options["default"], "full")
        mode = self.ci["jobs"]["test-plan"]["steps"][0]["run"]
        self.assertIn("full=true", mode)
        self.assertIn('"$CI_DRAFT" == true', mode)
        self.assertIn('"$CI_MODE" == targeted', mode)
        targeted = self.ci["jobs"]["python-targeted"]
        self.assertIn("!= 'true'", targeted["if"])
        self.assertIn("--modules", str(targeted["steps"]))
        self.assertIn("github.event_name", self.ci["concurrency"]["group"])
        self.assertIn("python_test_mode", self.ci["concurrency"]["group"])

    def test_all_ci_gates_checkout_the_same_source_head(self):
        expected = "${{ github.event.pull_request.head.sha || github.sha }}"
        self.assertEqual(self.ci["env"]["HSK_SOURCE_SHA"], expected)
        for job_id, job in self.ci["jobs"].items():
            for step in job["steps"]:
                if step.get("uses", "").startswith("actions/checkout@"):
                    self.assertEqual(step["with"]["ref"], expected, job_id)

    def test_ci_business_commands_and_third_party_latex_action_are_preserved(self):
        for token in (
            "python scripts/lint_skill.py --skip-generated",
            "python scripts/resolve_runtime.py full_solution",
            "python scripts/ci_unittest.py run --shard-index",
            "xu-cheng/latex-action@v4",
            "python scripts/render_paper.py",
            "python scripts/generate_indexes.py",
        ):
            self.assertIn(token, self.ci_text)

    def test_native_matlab_windows_ci_preserves_the_full_evidence_chain(self):
        job = self.ci["jobs"]["matlab-solver-smoke"]
        self.assertEqual(job["runs-on"], "windows-2022")
        self.assertEqual(job["defaults"]["run"]["shell"], "pwsh")
        steps = job["steps"]
        names = [step.get("name") for step in steps if step.get("name")]
        required = (
            "Configure and verify licensed MATLAB CI launcher",
            "Deliver primary only after real native Code Analyzer passes",
            "Run native MATLAB primary solver",
            "Accept native primary workbook and prepare required analysis",
            "Run native MATLAB analysis solver",
            "Verify analysis and original primary preservation",
            "Prepare separate same-backend projects and execute Python Q1/Q2/analysis",
            "Run native MATLAB Q2 consuming accepted MATLAB Q1 workbook",
            "Accept same-backend stages and reject mixed numerical delivery",
            "Prepare accepted preprocessing 1.0 fixture and deliver MATLAB 1.1 primary",
            "Run native primary from accepted preprocessing XLSX",
            "Accept preprocessed-input primary and deliver analysis",
            "Run native analysis from accepted preprocessing XLSX",
            "Verify preprocessing identity and workbook preservation",
            "Verify uppercase source input and accepted-primary hashes in native stages",
            "Verify native auxiliary-input receipt 1.2 without changing preprocessing identity",
            "Verify A2 opted-in structural delivery and receipt bindings natively",
            "Read native primary and analysis evidence through opt-in B1",
            "Assert nonempty Windows MATLAB evidence",
            "Upload actual MATLAB execution evidence",
        )
        indices = [names.index(name) for name in required]
        self.assertEqual(indices, sorted(indices))
        self.assertEqual(next(step["with"]["release"] for step in steps
                              if step.get("uses") == "matlab-actions/setup-matlab@v3"), "R2024b")
        self.assertEqual(sum(step.get("uses") == "matlab-actions/run-command@v3" for step in steps), 5)
        launcher = next(step["run"] for step in steps if step.get("name") == required[0])
        self.assertIn("/dist/bin/win64/run-matlab-command.exe", launcher)
        self.assertIn('args[0] != "-batch"', launcher)
        self.assertIn("start.ArgumentList.Add(args[1])", launcher)
        self.assertIn("return process.ExitCode", launcher)
        self.assertIn("HSK_MATLAB_CI_COMMAND=$adapter", launcher)
        self.assertIn("MW_BATCH_LICENSING_ONLINE=true", launcher)
        self.assertIn("version('-release'),'2024b'", launcher)
        self.assertIn("fullfile('$quotedRoot','引号''分号;圆括号(测试).txt')", launcher)
        self.assertIn("HSK_EXPECTED_LAUNCH_FAILURE", launcher)
        self.assertIn("$global:LASTEXITCODE = 0", launcher)
        self.assertNotIn("glnxa64", str(job))
        self.assertNotIn("chmod", str(job))
        self.assertFalse(any(step.get("shell") == "bash" for step in steps))
        self.assertIn("if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }",
                      next(step["run"] for step in steps
                           if step.get("name") == "Accept native primary workbook and prepare required analysis"))
        artifact = next(step for step in steps if step.get("name") == "Upload actual MATLAB execution evidence")
        self.assertEqual(artifact["with"]["if-no-files-found"], "error")

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
