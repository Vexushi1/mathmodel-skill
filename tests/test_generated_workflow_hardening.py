from __future__ import annotations

import hashlib
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/refresh-generated.yml"
CI_WORKFLOW = ROOT / ".github/workflows/ci.yml"
OPT_WORKFLOW = ROOT / ".github/workflows/optimization-baseline.yml"


class TestGeneratedWorkflowHardening(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")
        cls.workflow = yaml.safe_load(cls.text)
        cls.jobs = cls.workflow["jobs"]
        cls.ci_text = CI_WORKFLOW.read_text(encoding="utf-8")
        cls.opt_text = OPT_WORKFLOW.read_text(encoding="utf-8")

    def test_default_token_is_read_only(self):
        self.assertEqual(self.workflow["permissions"]["contents"], "read")

    def test_case_index_is_managed_and_new_files_are_not_hidden(self):
        path = "knowledge/case_memory/index.json"
        events = self.workflow.get("on", self.workflow.get(True))
        self.assertIn(path, events["push"]["paths-ignore"])
        script = next(step["run"] for step in self.jobs["refresh-feature-branch"]["steps"]
                      if step.get("name") == "Commit generated metadata and validate final head")
        self.assertIn("git status --porcelain --", script)
        self.assertIn(path, next(line for line in script.splitlines() if "git add " in line))
        ci_job = yaml.safe_load(self.ci_text)["jobs"]["generated-files"]
        artifact = next(step for step in ci_job["steps"] if step.get("uses", "").startswith("actions/upload-artifact@"))
        self.assertIn(path, artifact["with"]["path"])
        commands = "\n".join(step.get("run", "") for step in ci_job["steps"])
        self.assertIn("git ls-files --others --exclude-standard -- " + path, commands)

    def test_derived_stage_guide_is_committed_and_checked_by_existing_generator_chain(self):
        path = "core/stage_reading_guide.md"
        events = self.workflow.get("on", self.workflow.get(True))
        self.assertIn(path, events["push"]["paths-ignore"])
        script = next(step["run"] for step in self.jobs["refresh-feature-branch"]["steps"]
                      if step.get("name") == "Commit generated metadata and validate final head")
        self.assertIn(path, next(line for line in script.splitlines() if "git add " in line))
        self.assertIn(path, next(line for line in script.splitlines() if "git status --porcelain" in line))
        ci_job = yaml.safe_load(self.ci_text)["jobs"]["generated-files"]
        artifact = next(step for step in ci_job["steps"] if step.get("uses", "").startswith("actions/upload-artifact@"))
        self.assertIn(path, artifact["with"]["path"])
        commands = "\n".join(step.get("run", "") for step in ci_job["steps"])
        self.assertIn(path, commands)
        self.assertIn("git ls-files --others --exclude-standard --", commands)

    def test_full_reading_directory_is_staged_checked_and_uploaded(self):
        path = "core/full_reading"
        events = self.workflow.get("on", self.workflow.get(True))
        ignored = events["push"]["paths-ignore"]
        self.assertIn(f"{path}/manifest.json", ignored)
        self.assertIn(f"{path}/volumes/[0-9][0-9][0-9].md", ignored)
        step = next(step for step in self.jobs["refresh-feature-branch"]["steps"]
                    if step.get("name") == "Commit generated metadata and validate final head")
        for operation in ("git add ", "git status --porcelain"):
            self.assertIn(path, next(line for line in step["run"].splitlines() if operation in line))
        jobs = yaml.safe_load(self.ci_text)["jobs"]
        steps = jobs["generated-files"]["steps"]
        uploaded = next(step for step in steps if step.get("name") == "Upload regenerated metadata")
        self.assertIn(path, uploaded["with"]["path"].splitlines())
        checks = next(step for step in steps if step.get("name") == "Reject stale generated files")["run"]
        tracked, untracked = checks.split("git ls-files --others --exclude-standard --")
        self.assertIn(path, tracked)
        self.assertIn(path, untracked)
        targeted = next(step for step in jobs["python-targeted"]["steps"]
                        if step.get("name") == "Run affected development tests")
        for module in ("test_rule_corpus", "test_formal_reading"):
            self.assertIn(module, targeted["run"])

    def test_every_corpus_generator_job_installs_only_its_light_dependencies(self):
        ci_job = yaml.safe_load(self.ci_text)["jobs"]["generated-files"]
        for job in (self.jobs["refresh-feature-branch"], self.jobs["verify-main"], ci_job):
            with self.subTest(job=job):
                commands = [step.get("run", "") for step in job["steps"]]
                install = next(index for index, command in enumerate(commands)
                               if 'pip install "PyYAML>=6.0" "jsonschema>=4.22"' in command)
                generate = next(index for index, command in enumerate(commands)
                                if "python scripts/generate_indexes.py" in command)
                self.assertLess(install, generate)
                self.assertNotIn("unittest discover", "\n".join(commands))

    def test_feature_branch_writer_is_explicit_and_not_main(self):
        job = self.jobs["refresh-feature-branch"]
        self.assertEqual(job["permissions"]["contents"], "write")
        self.assertEqual(job["permissions"]["actions"], "write")
        self.assertEqual(job["permissions"]["pull-requests"], "read")
        condition = str(job["if"])
        self.assertIn("github.ref_name != 'main'", condition)
        self.assertIn("github.actor != 'github-actions[bot]'", condition)
        step_text = "\n".join(str(step) for step in job["steps"])
        self.assertIn("git push", step_text)

    def test_main_is_read_only_check_path(self):
        job = self.jobs["verify-main"]
        self.assertEqual(job["permissions"]["contents"], "read")
        self.assertNotIn("actions", job["permissions"])
        self.assertIn("github.ref_name == 'main'", str(job["if"]))
        step_text = "\n".join(str(step) for step in job["steps"])
        self.assertIn("python scripts/generate_indexes.py --check", step_text)
        self.assertNotIn("git push", step_text)
        self.assertNotIn("git commit", step_text)
        self.assertNotIn("gh workflow run", step_text)

    def test_only_feature_writer_has_contents_write_permission(self):
        writers = [
            name
            for name, job in self.jobs.items()
            if (job.get("permissions") or {}).get("contents") == "write"
        ]
        self.assertEqual(writers, ["refresh-feature-branch"])

    def test_only_feature_writer_has_actions_write_permission(self):
        writers = [
            name
            for name, job in self.jobs.items()
            if (job.get("permissions") or {}).get("actions") == "write"
        ]
        self.assertEqual(writers, ["refresh-feature-branch"])

    def test_full_gate_workflows_expose_explicit_dispatch(self):
        self.assertIn("  workflow_dispatch:\n", self.ci_text)
        self.assertIn("  push:\n", self.ci_text)
        self.assertIn("  pull_request:\n", self.ci_text)
        self.assertIn('branches: [main]', self.ci_text)
        self.assertIn('ready_for_review', self.ci_text)
        self.assertIn("  workflow_dispatch:\n", self.opt_text)

    def test_generated_commit_dispatches_both_existing_full_gate_workflows(self):
        job = self.jobs["refresh-feature-branch"]
        step = next(
            item for item in job["steps"] if item.get("name") == "Commit generated metadata and validate final head"
        )
        script = step["run"]
        self.assertEqual(step["env"]["GH_TOKEN"], "${{ github.token }}")
        self.assertIn("set -euo pipefail", script)
        self.assertIn('gh workflow run ci.yml --ref "$GITHUB_REF_NAME"', script)
        self.assertIn('gh workflow run optimization-baseline.yml --ref "$GITHUB_REF_NAME"', script)
        self.assertLess(script.index("git push"), script.index("gh workflow run ci.yml"))
        self.assertLess(
            script.index("git push"),
            script.index("gh workflow run optimization-baseline.yml"),
        )
        self.assertNotIn("continue-on-error", str(step))

    def test_no_diff_still_has_validation_and_draft_success_is_not_full_evidence(self):
        script = next(step["run"] for step in self.jobs["refresh-feature-branch"]["steps"]
                      if step.get("name") == "Commit generated metadata and validate final head")
        self.assertNotIn("exit 0", script)
        self.assertIn("mode=targeted", script)
        self.assertIn(".draft == false", script)
        self.assertIn('python_test_mode=$mode', script)
        self.assertIn('"head_sha=$final_head"', script)
        self.assertIn('.name == "Python 3.10"', script)
        self.assertIn('.name == "Windows Python 3.14"', script)
        self.assertIn('.conclusion == "success"', script)


class FullReadingOutputLifecycleTests(unittest.TestCase):
    """Exercise the real generator and CLI around a deterministic, resizing corpus."""

    def setUp(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("full_reading_generator", ROOT / "scripts/generate_indexes.py")
        self.generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.generator)
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        outputs = {key: self.root / getattr(self.generator, key).relative_to(ROOT) for key in
                   ("BOOTSTRAP", "SKILL_INDEX", "TEMPLATE_INDEX", "LEGACY_SKILL_INDEX",
                    "LEGACY_TEMPLATE_INDEX", "MANIFEST")}
        outputs["BOOTSTRAP"].parent.mkdir()
        outputs["BOOTSTRAP"].write_text("skill_version: 10.35.3\n", encoding="utf-8")
        patched_paths = patch.multiple(self.generator, ROOT=self.root, **outputs)
        patched_paths.start()
        self.addCleanup(patched_paths.stop)
        self.directory = self.root / "core/full_reading"
        self.first = self.directory / "volumes/001.md"
        self.second = self.directory / "volumes/002.md"
        self.generated = {self.directory / "manifest.json": "{}\n", self.first: "甲\n", self.second: "乙\n"}
        corpus = SimpleNamespace(generated_payloads=lambda root: self.generated.copy())
        patched_builder = patch.dict(sys.modules, {"rule_corpus": corpus})
        patched_builder.start()
        self.addCleanup(patched_builder.stop)

    def run_generator(self, *args):
        with patch.object(sys, "argv", ["generate_indexes.py", *args]), redirect_stdout(io.StringIO()):
            return self.generator.main()

    def test_add_retire_check_without_writes_and_rerun(self):
        self.assertEqual(self.run_generator("--check"), 1)
        self.assertFalse(self.directory.exists())
        self.assertEqual(self.run_generator(), 0)
        self.assertEqual(self.run_generator("--check"), 0)
        digest = hashlib.sha256(self.generated[self.first].encode("utf-8")).hexdigest()
        manifest = self.generator.MANIFEST.read_text(encoding="utf-8")
        self.assertIn(f"{digest}  core/full_reading/volumes/001.md\n", manifest)
        self.assertEqual(self.second.read_text(encoding="utf-8"), "乙\n")
        del self.generated[self.second]
        self.assertEqual(self.run_generator("--check"), 1)
        self.assertTrue(self.second.is_file())
        self.assertEqual(self.run_generator(), 0)
        self.assertFalse(self.second.exists())
        for index in (self.generator.SKILL_INDEX, self.generator.MANIFEST):
            self.assertNotIn("core/full_reading/volumes/002.md", index.read_text(encoding="utf-8"))
        self.assertEqual(self.run_generator("--check"), 0)

    def test_exact_returned_bytes_and_unowned_paths(self):
        self.assertEqual(self.run_generator(), 0)
        self.first.write_bytes("甲\r\n".encode("utf-8"))
        self.assertEqual(self.run_generator("--check"), 1)
        self.assertEqual(self.run_generator(), 0)
        self.assertEqual(self.first.read_bytes(), self.generated[self.first].encode("utf-8"))
        unrelated = self.first.with_name("notes.md")
        unrelated.write_text("保留", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unexpected file"):
            self.run_generator()
        self.assertEqual(unrelated.read_text(encoding="utf-8"), "保留")


if __name__ == "__main__":
    unittest.main()
