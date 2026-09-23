"""Archive-bound recovery remains explicit for read-only and sync entry points."""
from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import project_transaction as TX  # noqa: E402
import runtime_assurance as ASSURANCE  # noqa: E402
import sync_project as SYNC  # noqa: E402
import validate_project_state as STATE  # noqa: E402


class RecoveryReadBoundaryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "state").mkdir()
        self.state = {"project": {"state_generation": 0, "current_phase": "model_design"},
                      "subproblems": {}}
        self.state_path = self.root / TX.STATE_RELATIVE_PATH
        self.state_path.write_text(yaml.safe_dump(self.state), encoding="utf-8")
        self.framework = self.root / "模型论文框架.md"
        self.framework.write_text("# 模型论文框架\n", encoding="utf-8")

    def interrupted_archive_commit(self):
        expected = {
            TX.STATE_RELATIVE_PATH: TX.sha256_file(self.state_path),
            "模型论文框架.md": TX.sha256_file(self.framework),
            "sync_report.yaml": None,
        }
        ref = TX.prepare_history_archive(
            self.root, "state/backend_history/" + "a" * 32,
            expected_generation=0, expected_file_hashes=expected,
        )

        def stop(point):
            if point == "after_journal_prepared":
                raise RuntimeError("interrupted")

        with self.assertRaisesRegex(RuntimeError, "interrupted"):
            TX.commit_project_state(
                self.root, self.state, expected_generation=0,
                expected_file_hashes=expected, preserved_archives=[ref],
                writes_before_state=[("模型论文框架.md", "# new framework\n")],
                writes_after_state=[("sync_report.yaml", "status: new\n")],
                failure_hook=stop,
            )
        return self.root / TX.JOURNAL_RELATIVE_PATH

    def test_readers_report_recovery_required_and_writers_do_not_auto_recover_v2(self):
        original_state, original_framework = self.state_path.read_bytes(), self.framework.read_bytes()
        journal = self.interrupted_archive_commit()
        original_journal = journal.read_bytes()
        self.assertTrue(any("recovery_required" in issue for issue in STATE.validate_state_file(
            self.state_path, project_root=self.root,
        )))
        for write in (False, True):
            with self.subTest(write=write), self.assertRaises(ASSURANCE.ProjectStateReadError) as error:
                SYNC.synchronize(self.root, write=write)
            self.assertEqual(error.exception.code, "recovery_required")
        with self.assertRaisesRegex(TX.TransactionRecoveryError, "explicit recovery"):
            TX.load_state_for_update(self.root)
        with self.assertRaisesRegex(TX.TransactionRecoveryError, "explicit recovery"):
            TX.commit_project_state(self.root, self.state, expected_generation=0)
        self.assertEqual(journal.read_bytes(), original_journal)
        self.assertEqual(self.state_path.read_bytes(), original_state)
        self.assertEqual(self.framework.read_bytes(), original_framework)
        self.assertEqual(TX.recover_project_transaction(self.root)["status"], "rolled_forward")
        self.assertFalse(journal.exists())

    def test_sync_write_rejects_framework_change_after_its_snapshot(self):
        original_state = self.state_path.read_bytes()
        original_header = SYNC._framework_header_text

        def edit_after_read(path, scope, stale):
            result = original_header(path, scope, stale)
            self.framework.write_text("external change\n", encoding="utf-8")
            return result

        with patch.object(SYNC, "_framework_header_text", side_effect=edit_after_read):
            with self.assertRaises(TX.ReadSetConflictError):
                SYNC.synchronize(self.root, write=True, delivery_scope="design")
        self.assertEqual(self.state_path.read_bytes(), original_state)
        self.assertEqual(self.framework.read_text(encoding="utf-8"), "external change\n")
        self.assertFalse((self.root / TX.JOURNAL_RELATIVE_PATH).exists())


if __name__ == "__main__":
    unittest.main()
