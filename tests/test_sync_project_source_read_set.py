"""Sync must not commit observations after their original source bytes change."""
from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml

from tests.test_sync_project import load_syncer, setup_project


class SyncSourceReadSetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.result = setup_project(
            self.root, status="solved", phase="solve_validate",
            include_analysis=False, include_analysis_code=False,
        )
        self.state_path = self.root / "state/project_state.yaml"
        self.framework_path = self.root / "模型论文框架.md"
        self.sync = load_syncer()

    def _accept_current_bytes(self):
        initial = self.sync.synchronize(self.root, write=False)
        state = yaml.safe_load(self.state_path.read_text(encoding="utf-8"))
        entry = state["subproblems"]["Q1"]
        entry["artifact_hashes"] = initial["questions"]["Q1"]["artifact_hashes"]
        entry["validated_artifact_hashes"] = dict(entry["artifact_hashes"])
        self.state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
        self.assertEqual(self.sync.synchronize(self.root, write=False)["stale_questions"], [])

    def _assert_concurrent_edit_is_blocked(self, target: Path):
        before_state = self.state_path.read_bytes()
        before_framework = self.framework_path.read_bytes()
        original = self.sync.PROJECT_TX.commit_project_state

        def interleave(*args, **kwargs):
            target.write_bytes(target.read_bytes() + b"\n# concurrent edit\n")
            return original(*args, **kwargs)

        with patch.object(self.sync.PROJECT_TX, "commit_project_state", side_effect=interleave):
            with self.assertRaises(self.sync.PROJECT_TX.ReadSetConflictError):
                self.sync.synchronize(self.root, write=True)
        self.assertEqual(self.state_path.read_bytes(), before_state)
        self.assertEqual(self.framework_path.read_bytes(), before_framework)
        self.assertFalse((self.root / "sync_report.yaml").exists())
        self.assertFalse((self.root / self.sync.PROJECT_TX.JOURNAL_RELATIVE_PATH).exists())

    def test_post_observation_edits_of_code_input_and_workbook_are_blocked(self):
        for relative in (
            "问题一求解/问题一求解.py", "input.json", "问题一求解/问题一求解结果.xlsx",
        ):
            with self.subTest(relative=relative):
                # Each case gets fresh original bytes and accepted identities.
                with tempfile.TemporaryDirectory() as temp:
                    self.root = Path(temp)
                    self.result = setup_project(
                        self.root, status="solved", phase="solve_validate",
                        include_analysis=False, include_analysis_code=False,
                    )
                    self.state_path = self.root / "state/project_state.yaml"
                    self.framework_path = self.root / "模型论文框架.md"
                    self._accept_current_bytes()
                    self._assert_concurrent_edit_is_blocked(self.root / relative)

    def test_declared_helper_edit_after_observation_is_blocked(self):
        helper = self.result / "helper.py"
        helper.write_text("VALUE = 1\n", encoding="utf-8")
        source = self.result / "问题一求解.py"
        _, config = self.sync.STAGE_CODE.parse_stage_config(source)
        config["code_dependencies"] = [{
            "path": helper.relative_to(self.root).as_posix(),
            "sha256": hashlib.sha256(helper.read_bytes()).hexdigest(),
        }]
        source.write_text("RUN_CONFIG = " + repr(config) + "\n\ndef main():\n    return 0\n", encoding="utf-8")
        fingerprint = self.sync.STAGE_CODE.stage_code_fingerprint(
            self.root, source, config["code_dependencies"],
        )
        state = yaml.safe_load(self.state_path.read_text(encoding="utf-8"))
        entry = state["subproblems"]["Q1"]
        entry["primary_code_sha256"] = fingerprint["entry_sha256"]
        entry["solver_execution"]["primary"]["bundle_sha256"] = fingerprint["bundle_sha256"]
        entry["solver_execution"]["primary"]["validated_bundle_sha256"] = fingerprint["bundle_sha256"]
        self.state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
        self._accept_current_bytes()
        self._assert_concurrent_edit_is_blocked(helper)

    def test_workbook_edit_during_snapshot_is_not_late_captured(self):
        self._accept_current_bytes()
        workbook = self.result / "问题一求解结果.xlsx"
        original = self.sync._snapshot_question

        def interleave(*args, **kwargs):
            snapshot = original(*args, **kwargs)
            workbook.write_bytes(workbook.read_bytes() + b"\n# changed after validation\n")
            return snapshot

        before_state = self.state_path.read_bytes()
        with patch.object(self.sync, "_snapshot_question", side_effect=interleave):
            with self.assertRaises(self.sync.PROJECT_TX.ReadSetConflictError):
                self.sync.synchronize(self.root, write=True)
        self.assertEqual(self.state_path.read_bytes(), before_state)
        self.assertFalse((self.root / "sync_report.yaml").exists())


if __name__ == "__main__":
    unittest.main()
