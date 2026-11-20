"""Rehearse candidate entry, existing-project recovery and historical read-only use."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml

from tests import claim_fixture
from tests import test_v900_phase_i_migration_matrix as legacy
from tests import test_v900_semantic_governance as governance
from tests.test_model_code_conformance import bytes_in

ROOT = Path(__file__).resolve().parents[1]


class ProjectMigrationTests(unittest.TestCase):
    def test_running_project_preview_snapshot_recovery_and_repeat_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "project"
            state_path = governance.dependency_project(root)
            self.assertEqual(governance.SEMANTIC.validate_project(root, write=True, strict=True)["status"], "passed")
            state = yaml.safe_load(state_path.read_bytes())
            for item in state["subproblems"].values():
                item.update(approved_semantic_identity_hash=item["validated_semantic_identity_hash"],
                            approved_semantic_revision=item["validated_semantic_revision"],
                            model_challenge_status="passed", human_model_approval_status="approved")
            state_path.write_text(yaml.safe_dump(state), encoding="utf-8")
            (root / "saved-project-instructions.txt").write_text("Use the project's original 10.x pin.", encoding="utf-8")
            # The workbook is a snapshot payload. This test does not grant it receipt eligibility.
            (root / "observations.xlsx").write_bytes(claim_fixture.workbook())
            original = bytes_in(root)
            snapshot = Path(tmp) / "snapshot"
            shutil.copytree(root, snapshot)

            for _ in range(2):
                preview = governance.SEMANTIC.validate_project(root, write=False, strict=True)
                self.assertEqual(preview["status"], "passed", preview)
                self.assertFalse(preview["affected_questions"], preview)
            self.assertEqual(bytes_in(root), original)

            (root / "saved-project-instructions.txt").write_text("Explicit candidate trial.", encoding="utf-8")
            state["subproblems"]["Q2"]["depends_on"] = []
            state_path.write_text(yaml.safe_dump(state), encoding="utf-8")
            before_failure = bytes_in(root)
            failure = governance.SEMANTIC.validate_project(root, write=True, strict=True)
            self.assertEqual(failure["status"], "failed", failure)
            self.assertEqual(bytes_in(root), before_failure)

            restored = Path(tmp) / "restored"
            shutil.copytree(snapshot, restored)
            self.assertEqual(bytes_in(restored), original)
            state_path = restored / "state/project_state.yaml"
            state = yaml.safe_load(state_path.read_bytes())
            state["subproblems"]["Q1"]["semantic_revision"] += 1
            state_path.write_text(yaml.safe_dump(state), encoding="utf-8")
            result = governance.SEMANTIC.validate_project(restored, write=True, strict=True)
            self.assertEqual(result["status"], "passed", result)
            self.assertEqual(result["affected_questions"], ["Q1", "Q2", "Q3", "Q5"])
            updated = yaml.safe_load(state_path.read_bytes())["subproblems"]
            self.assertEqual(updated["Q1"]["human_model_approval_status"], "stale")
            self.assertEqual(updated["Q4"], state["subproblems"]["Q4"])
            self.assertEqual((restored / "observations.xlsx").read_bytes(), original["observations.xlsx"])

    def test_historical_resume_keeps_text_hash_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            framework = legacy.legacy_framework()
            question = legacy.legacy_question(framework)
            legacy.write_project(root, question, framework)
            before = bytes_in(root)
            for _ in range(2):
                hydration = legacy.ASSURANCE.hydrate_project_context(root, "Q1")
                self.assertNotIn("locked_model_spec", hydration["verified_artifacts"])
                self.assertEqual(legacy.APPROVAL.validate_question("Q1", question, allow_legacy_read_only=True), [])
                self.assertTrue(legacy.APPROVAL.validate_question("Q1", question))
            self.assertEqual(bytes_in(root), before)

    def test_old_cli_and_opt_in_new_project_use_the_selected_source(self):
        head = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
        with tempfile.TemporaryDirectory() as tmp:
            command = [sys.executable, str(ROOT / "scripts/resolve_workflow.py"), "problem_analysis",
                       "--primary", "optimization"]
            old = yaml.safe_load(subprocess.check_output(command, cwd=tmp))
            self.assertEqual(old["classification"]["objective"], "optimization")
            self.assertNotIn("startup_reading", old)
            args = dict(project_root=Path(tmp), candidate_startup_event="new_contest", source_commit=head)
            result = legacy.RESOLVER.resolve_runtime("problem_analysis", **args)
            self.assertEqual(result["startup_reading"]["profile"], "formal")
            self.assertEqual(result["startup_reading"]["source_commit"], head)
            self.assertEqual(result["startup_reading"]["status"], "selection_only")
            self.assertNotIn("startup_reading", legacy.RESOLVER.resolve_runtime("problem_analysis", project_root=Path(tmp)))
            with self.assertRaisesRegex(ValueError, "requires both"):
                legacy.RESOLVER.resolve_runtime("problem_analysis", candidate_startup_event="new_contest")
            args["source_commit"] = "0" * 40
            with self.assertRaisesRegex(ValueError, "source checkout changed"):
                legacy.RESOLVER.resolve_runtime("problem_analysis", **args)
            self.assertEqual(bytes_in(Path(tmp)), {})
