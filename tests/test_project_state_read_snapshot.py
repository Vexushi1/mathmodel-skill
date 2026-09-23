"""Read-only, consistent-state regressions; synthetic fixtures are not numerical evidence."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
import reading_plan as READING
import resolve_runtime as RESOLVER
import runtime_assurance as ASSURANCE
import stage_code as STAGE_CODE
from project_transaction import JOURNAL_RELATIVE_PATH, STATE_RELATIVE_PATH
from reading_plan_cases import build_project
from tests import test_solver_backends as solver_fixtures


def hashes(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


class ProjectStateReadSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        build_project(ROOT, self.root, "current")
        self.path = self.root / STATE_RELATIVE_PATH
        self.state = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        fixture = solver_fixtures.SolverBackendTests()
        fixture.root = self.root
        source = fixture.source(fixture.config("python"))
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        bundle = STAGE_CODE.stage_code_fingerprint(self.root, source)["bundle_sha256"]
        question = self.state["subproblems"]["Q1"]
        question.update(code=source.relative_to(self.root).as_posix(), primary_code_sha256=digest)
        question["solver_execution"] = {"primary": {
            "bundle_sha256": bundle, "validated_bundle_sha256": bundle}}
        for field in ("artifact_hashes", "validated_artifact_hashes"):
            question.setdefault(field, {})["primary_code"] = digest
        self.state["execution"] = {
            "solver_backend": "python", "solver_backend_selection_reason": "Synthetic whole-problem review"}
        self.save(self.state)

    def save(self, state):
        self.path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")

    def resolve(self, intent="framework_sync"):
        return RESOLVER.resolve_runtime(intent, project_root=self.root, question="Q1",
                                        competition="CUMCM", request="仅同步已验收结果摘要，不修改模型。")

    def test_unchanged_scoped_read_uses_original_bytes_and_keeps_null_consumption(self):
        before = hashes(self.root)
        plan = self.resolve()
        reading = plan["reading_plan"]
        self.assertEqual(reading["profile"], "framework_result_sync")
        row = next(r for r in reading["read_now"] if r["path"] == STATE_RELATIVE_PATH)
        self.assertEqual(row["sha256"], before[STATE_RELATIVE_PATH])
        self.assertEqual(row["source_bytes"], len(self.path.read_bytes()))
        self.assertIsNone(reading["metrics"]["actual_read_bytes"])
        self.assertIsNone(reading["metrics"]["actual_read_tokens"])
        self.assertEqual(before, hashes(self.root))

    def test_payload_is_defensive_and_raw_snapshot_is_frozen(self):
        snapshot = ASSURANCE.ProjectStateSnapshot.capture(self.root)
        value = snapshot.payload()
        value["project"]["state_generation"] = 500
        self.assertEqual(snapshot.payload(), self.state)
        with self.assertRaises(FrozenInstanceError):
            snapshot.raw = b"other"
        snapshot.assert_current()

    def test_generation_and_backend_change_between_hydration_and_reading_is_rejected(self):
        original = RESOLVER.build_reading_plan
        def interleave(*args, **kwargs):
            updated = deepcopy(self.state)
            updated["project"]["state_generation"] = 1
            updated["execution"]["solver_backend"] = "matlab"
            self.save(updated)
            return original(*args, **kwargs)
        with patch.object(RESOLVER, "build_reading_plan", side_effect=interleave):
            with self.assertRaisesRegex(ASSURANCE.ProjectStateReadError, "project_state_changed"):
                self.resolve()

    def test_same_generation_byte_change_is_rejected(self):
        snapshot = ASSURANCE.ProjectStateSnapshot.capture(self.root)
        self.path.write_bytes(self.path.read_bytes() + b"\n# same generation but new bytes\n")
        with self.assertRaisesRegex(ASSURANCE.ProjectStateReadError, "project_state_changed"):
            snapshot.assert_current()

    def test_change_during_artifact_hydration_is_rejected(self):
        original = ASSURANCE._framework_semantic_evidence
        def interleave(*args, **kwargs):
            result = original(*args, **kwargs)
            self.path.write_bytes(self.path.read_bytes() + b"\n# changed during hydration\n")
            return result
        with patch.object(ASSURANCE, "_framework_semantic_evidence", side_effect=interleave):
            with self.assertRaisesRegex(ASSURANCE.ProjectStateReadError, "project_state_changed"):
                ASSURANCE.hydrate_project_context(self.root, "Q1")

    def test_change_during_source_description_is_rejected(self):
        original = READING.SourceReader.describe
        changed = False
        def interleave(reader, spec):
            nonlocal changed
            row = original(reader, spec)
            if reader.origin == "project" and spec["path"] == STATE_RELATIVE_PATH and not changed:
                changed = True
                self.path.write_bytes(self.path.read_bytes() + b"\n# after cached description\n")
            return row
        with patch.object(READING.SourceReader, "describe", interleave):
            with self.assertRaisesRegex(ASSURANCE.ProjectStateReadError, "project_state_changed"):
                self.resolve()
        self.assertTrue(changed)

    def test_change_after_reading_builder_returns_is_rejected(self):
        original = RESOLVER.build_reading_plan
        def interleave(*args, **kwargs):
            result = original(*args, **kwargs)
            self.path.write_bytes(self.path.read_bytes() + b"\n# at resolver final boundary\n")
            return result
        with patch.object(RESOLVER, "build_reading_plan", side_effect=interleave):
            with self.assertRaisesRegex(ASSURANCE.ProjectStateReadError, "project_state_changed"):
                self.resolve()

    def test_all_project_routes_not_only_narrow_ones_reject_state_changes(self):
        for intent in ("project_sync", "returned_workbook_validation", "latex", "code_and_solution"):
            with self.subTest(intent=intent):
                self.save(self.state)
                original = RESOLVER.build_reading_plan
                def interleave(*args, **kwargs):
                    self.path.write_bytes(self.path.read_bytes() + b"\n# route boundary\n")
                    return original(*args, **kwargs)
                with patch.object(RESOLVER, "build_reading_plan", side_effect=interleave):
                    with self.assertRaisesRegex(ASSURANCE.ProjectStateReadError, "project_state_changed"):
                        self.resolve(intent)

    def test_existing_journal_is_not_implicitly_recovered_or_removed(self):
        journal = self.root / JOURNAL_RELATIVE_PATH
        for content in (b"status: prepared\n", b"status: committed\n", b"broken: [\n"):
            with self.subTest(content=content):
                journal.write_bytes(content)
                before = hashes(self.root)
                with self.assertRaisesRegex(ASSURANCE.ProjectStateReadError, "recovery_required"):
                    self.resolve()
                self.assertEqual(before, hashes(self.root))

    def test_journal_appearing_during_planning_is_rejected_without_recovery(self):
        original = RESOLVER.build_reading_plan
        def interleave(*args, **kwargs):
            (self.root / JOURNAL_RELATIVE_PATH).write_text("status: prepared\n", encoding="utf-8")
            return original(*args, **kwargs)
        with patch.object(RESOLVER, "build_reading_plan", side_effect=interleave):
            with self.assertRaisesRegex(ASSURANCE.ProjectStateReadError, "recovery_required"):
                self.resolve()
        self.assertTrue((self.root / JOURNAL_RELATIVE_PATH).exists())

    def test_missing_state_remains_unavailable_without_creating_files(self):
        root = self.root / "nonexistent-project"
        hydration = ASSURANCE.hydrate_project_context(root)
        self.assertFalse(hydration["loaded"])
        self.assertFalse(root.exists())

    def test_state_appearance_and_disappearance_are_changes(self):
        snapshot = ASSURANCE.ProjectStateSnapshot.capture(self.root)
        self.path.unlink()
        with self.assertRaisesRegex(ASSURANCE.ProjectStateReadError, "project_state_changed"):
            snapshot.assert_current()
        missing = ASSURANCE.ProjectStateSnapshot.capture(self.root)
        self.save(self.state)
        with self.assertRaisesRegex(ASSURANCE.ProjectStateReadError, "project_state_changed"):
            missing.assert_current()

    def test_invalid_encoding_yaml_shape_and_generation_fail_before_assurance(self):
        cases = (b"\xff", b"project: [\n", b"[]\n", b"false\n", b"project: 2\n",
                 b"subproblems: []\n", b"project: {state_generation: true}\n",
                 b"project: {state_generation: -1}\n", b"project: {state_generation: '0'}\n")
        for raw in cases:
            with self.subTest(raw=raw):
                self.path.write_bytes(raw)
                with self.assertRaisesRegex(ASSURANCE.ProjectStateReadError, "invalid_project_state"):
                    ASSURANCE.hydrate_project_context(self.root)
                self.assertEqual(self.path.read_bytes(), raw)

    def test_dependency_hydration_reuses_the_same_snapshot(self):
        self.state["subproblems"]["Q1"]["depends_on"] = [
            {"question": "Q2", "kind": "model", "note": "test snapshot dependency"}]
        self.state["subproblems"]["Q2"] = {}  # Intentionally unapproved; narrow read must widen.
        self.save(self.state)
        observed = []
        original = ASSURANCE.hydrate_project_context
        def capture(*args, **kwargs):
            observed.append(kwargs.get("state_snapshot"))
            return original(*args, **kwargs)
        with patch.object(ASSURANCE, "hydrate_project_context", side_effect=capture):
            plan = self.resolve()
        self.assertEqual(len(observed), 1)
        self.assertIsInstance(observed[0], ASSURANCE.ProjectStateSnapshot)
        self.assertEqual(observed[0].raw, self.path.read_bytes())
        self.assertEqual(plan["reading_plan"]["profile"], "full")

    def test_standalone_projection_without_original_snapshot_cannot_narrow(self):
        plan = self.resolve()
        before = deepcopy(plan)
        router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"))
        manifest = yaml.safe_load((ROOT / "core/module_manifest.yaml").read_text(encoding="utf-8"))
        reading = READING.build_reading_plan(ROOT, plan, router, manifest,
                                            "仅同步已验收结果摘要，不修改模型。")
        self.assertEqual(reading["profile"], "full")
        self.assertTrue(any("snapshot unavailable" in r for r in reading["reasons"]))
        self.assertEqual(plan, before)

    def test_snapshot_from_another_project_is_rejected(self):
        snapshot = ASSURANCE.ProjectStateSnapshot.capture(self.root)
        with self.assertRaisesRegex(ASSURANCE.ProjectStateReadError, "snapshot_project_mismatch"):
            ASSURANCE.hydrate_project_context(self.root / "other", state_snapshot=snapshot)

    def test_state_symlink_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "outside.yaml"
            target.write_bytes(self.path.read_bytes())
            self.path.unlink()
            try:
                self.path.symlink_to(target)
            except OSError as exc:
                if getattr(exc, "winerror", None) == 1314:
                    self.skipTest("Windows account lacks symbolic-link privilege")
                raise
            with self.assertRaisesRegex(ASSURANCE.ProjectStateReadError, "state_path_outside_project_root"):
                ASSURANCE.ProjectStateSnapshot.capture(self.root)

    def test_cli_fails_without_emitting_a_success_plan_for_invalid_state(self):
        self.path.write_bytes(b"\xff")
        proc = subprocess.run([sys.executable, str(ROOT / "scripts/resolve_runtime.py"), "project_sync",
                               "--project-root", str(self.root)], capture_output=True, text=True, timeout=20)
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "")
        self.assertIn("invalid_project_state", proc.stderr)

    def test_crlf_state_hash_and_byte_count_use_the_original_bytes(self):
        self.path.write_bytes(self.path.read_bytes().replace(b"\n", b"\r\n"))
        plan = self.resolve()
        row = next(r for r in plan["reading_plan"]["read_now"] if r["path"] == STATE_RELATIVE_PATH)
        self.assertEqual(row["source_bytes"], len(self.path.read_bytes()))
        self.assertEqual(row["sha256"], hashlib.sha256(self.path.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
