"""The first project backend choice uses one byte-bound state/framework commit."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from unittest import mock
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import project_solver_backend as BACKEND
import project_transaction as TX
from runtime_assurance import ProjectStateReadError
import sync_project as SYNC
import validate_project_state as STATE


class SelectProjectBackendTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.state_path = self.root / TX.STATE_RELATIVE_PATH
        self.state_path.parent.mkdir()
        self.framework_path = self.root / "模型论文框架.md"
        self.state = yaml.safe_load((ROOT / "state/project_state.example.yaml").read_text(encoding="utf-8"))
        self.state["requirements"].update(total=1, completed=["Q1"], pending=[])
        self.state_path.write_text(yaml.safe_dump(self.state, allow_unicode=True, sort_keys=False), encoding="utf-8")
        framework = (ROOT / "templates/model/model_paper_framework.md").read_text(encoding="utf-8")
        framework = framework.replace("### Q1：__QUESTION_NAME__", "### Q1：填写问题名称")
        # Placeholder data rows are not current project memories.
        framework = "\n".join(line for line in framework.splitlines()
                              if not line.startswith(("| T1 |", "| N1 |", "| TC1 |", "| paper.abstract.q1 |"))) + "\n"
        self.framework_path.write_text(framework, encoding="utf-8")
        self.assertEqual(STATE.validate_state_payload(self.state, project_root=self.root), [])

    def current(self):
        return yaml.safe_load(self.state_path.read_text(encoding="utf-8"))

    def select(self, backend="matlab", reason="全题模型与数值能力已审视；许可证仍待用户核验", generation=0):
        return BACKEND.select_project_backend(
            self.root, backend=backend, reason=reason, expected_generation=generation,
        )

    def test_first_choice_commits_state_and_framework_together_without_approval_or_stale(self):
        before = deepcopy(self.state)
        result = self.select()
        current = self.current()
        self.assertEqual(result["status"], "committed")
        self.assertEqual(current["project"]["state_generation"], 1)
        self.assertEqual(current["execution"]["solver_backend"], "matlab")
        self.assertIn("许可证仍待用户核验", current["execution"]["solver_backend_selection_reason"])
        self.assertEqual(current["subproblems"], before["subproblems"])
        self.assertEqual(current["subproblems"]["Q1"]["human_model_approval_status"], "pending")
        self.assertFalse(current["subproblems"]["Q1"]["artifacts_stale"])
        self.assertFalse(result["environment_verified"])
        self.assertFalse(result["execution_authorized"])
        self.assertEqual(STATE.validate_state_payload(current, project_root=self.root), [])
        self.assertEqual(list(self.root.glob("*.txn-*")), [])
        self.assertFalse((self.root / TX.JOURNAL_RELATIVE_PATH).exists())

    def test_identical_request_is_read_only_and_reason_revision_does_not_stale_model(self):
        self.select()
        before_state, before_framework = self.state_path.read_bytes(), self.framework_path.read_bytes()
        unchanged = self.select(generation=1)
        self.assertEqual(unchanged["status"], "unchanged")
        self.assertEqual(self.state_path.read_bytes(), before_state)
        self.assertEqual(self.framework_path.read_bytes(), before_framework)
        revised = self.select(reason="全题条件已复核；MATLAB 工具箱可用性待确认", generation=1)
        current = self.current()
        self.assertEqual(revised["state_generation"], 2)
        self.assertEqual(current["subproblems"], self.state["subproblems"])
        self.assertEqual(current["execution"]["solver_backend"], "matlab")
        self.assertEqual(STATE.validate_state_payload(current, project_root=self.root), [])

    def test_opposite_choice_and_stale_generation_require_explicit_new_action(self):
        self.select()
        before = self.state_path.read_bytes(), self.framework_path.read_bytes()
        with self.assertRaisesRegex(BACKEND.ProjectBackendSelectionError, "migration"):
            self.select("python", generation=1)
        with self.assertRaises(TX.GenerationConflictError):
            self.select(generation=0)
        self.assertEqual((self.state_path.read_bytes(), self.framework_path.read_bytes()), before)

    def test_legacy_stage_policy_even_same_backend_requires_migration(self):
        self.state["subproblems"]["Q1"]["solver_execution"] = {
            "primary": {"backend": "matlab", "selection_reason": "旧阶段选择"},
        }
        self.state_path.write_text(yaml.safe_dump(self.state, allow_unicode=True), encoding="utf-8")
        before = self.state_path.read_bytes(), self.framework_path.read_bytes()
        with self.assertRaisesRegex(BACKEND.ProjectBackendSelectionError, "migration"):
            self.select()
        self.assertEqual((self.state_path.read_bytes(), self.framework_path.read_bytes()), before)

    def test_explicit_choice_needs_design_records_and_nonempty_reason(self):
        for backend, reason in (("auto", "whole project"), ("matlab", " \t ")):
            with self.subTest(backend=backend, reason=reason):
                with self.assertRaises(BACKEND.ProjectBackendSelectionError):
                    self.select(backend, reason)
        self.state["subproblems"]["Q1"]["selected_model"] = ""
        self.state_path.write_text(yaml.safe_dump(self.state, allow_unicode=True), encoding="utf-8")
        with self.assertRaisesRegex(BACKEND.ProjectBackendSelectionError, "capability review"):
            self.select()

    def test_missing_known_question_record_blocks_whole_project_choice(self):
        self.state["requirements"].update(total=2, completed=["Q1"], pending=["Q2"])
        self.state_path.write_text(yaml.safe_dump(self.state, allow_unicode=True), encoding="utf-8")
        with self.assertRaisesRegex(BACKEND.ProjectBackendSelectionError, "Q2"):
            self.select()

    def test_preexisting_framework_hash_drift_cannot_be_overwritten_by_selection(self):
        self.state["paper_framework"]["sha256"] = "0" * 64
        self.state_path.write_text(yaml.safe_dump(self.state, allow_unicode=True), encoding="utf-8")
        before = self.state_path.read_bytes(), self.framework_path.read_bytes()
        with self.assertRaisesRegex(BACKEND.ProjectBackendSelectionError, "current project state/framework"):
            self.select()
        self.assertEqual((self.state_path.read_bytes(), self.framework_path.read_bytes()), before)

    def test_prepared_journal_blocks_without_implicit_recovery(self):
        journal = self.root / TX.JOURNAL_RELATIVE_PATH
        journal.write_text("incomplete: true\n", encoding="utf-8")
        before = self.state_path.read_bytes(), self.framework_path.read_bytes()
        with self.assertRaisesRegex(ProjectStateReadError, "recovery_required"):
            self.select()
        self.assertEqual((self.state_path.read_bytes(), self.framework_path.read_bytes()), before)
        self.assertTrue(journal.exists())

    def test_framework_changes_after_snapshot_fail_read_set_before_commit(self):
        render = SYNC.render_project_backend_memory

        def third_party_edit(text, state):
            result = render(text, state)
            self.framework_path.write_text(text + "\nthird party change\n", encoding="utf-8")
            return result

        with mock.patch.object(SYNC, "render_project_backend_memory", side_effect=third_party_edit):
            with self.assertRaises(TX.ReadSetConflictError):
                self.select()
        self.assertNotIn("solver_backend", self.current()["execution"])
        self.assertIn("third party change", self.framework_path.read_text(encoding="utf-8"))
        self.assertFalse((self.root / TX.JOURNAL_RELATIVE_PATH).exists())

    def test_invalid_staged_framework_fails_before_journal_and_preserves_live_bytes(self):
        before = self.state_path.read_bytes(), self.framework_path.read_bytes()
        render = SYNC.render_project_backend_memory

        def invalid_render(text, state):
            return render(text, state).replace("## 当前有效口径", "## damaged heading")

        with mock.patch.object(SYNC, "render_project_backend_memory", side_effect=invalid_render):
            with self.assertRaisesRegex(BACKEND.ProjectBackendSelectionError, "candidate project state/framework"):
                self.select()
        self.assertEqual((self.state_path.read_bytes(), self.framework_path.read_bytes()), before)
        self.assertFalse((self.root / TX.JOURNAL_RELATIVE_PATH).exists())

    def test_staged_framework_hash_mismatch_is_checked_against_new_bytes(self):
        before = self.state_path.read_bytes(), self.framework_path.read_bytes()
        import validate_model_paper_framework as FRAMEWORK
        with mock.patch.object(FRAMEWORK, "sha256_text", return_value="0" * 64):
            with self.assertRaisesRegex(BACKEND.ProjectBackendSelectionError, "paper_framework.sha256"):
                self.select()
        self.assertEqual((self.state_path.read_bytes(), self.framework_path.read_bytes()), before)
        self.assertFalse((self.root / TX.JOURNAL_RELATIVE_PATH).exists())


if __name__ == "__main__":
    unittest.main()
