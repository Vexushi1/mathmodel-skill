"""M4: real scoped Sync behavior; only maintenance synthetic fixtures are touched."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

import yaml

from tests.test_sync_project import setup_project, capabilities, load_syncer
from tests.test_question_runtime_integration import add_unfinished_questions_to_sync_project

SYNC = load_syncer()


def three_question_project(root: Path) -> Path:
    setup_project(
        root, status="designed", phase="solve_validate",
        include_solution=False, include_analysis=False, include_analysis_code=False,
    )
    add_unfinished_questions_to_sync_project(root)
    path = root / "state/project_state.yaml"
    state = yaml.safe_load(path.read_text(encoding="utf-8"))
    state["requirements"] = {"total": 3, "completed": [], "pending": ["Q1", "Q2", "Q3"]}
    for q in ("Q2", "Q3"):
        entry = state["subproblems"][q]
        entry.update(
            status="audited", selected_model="", capabilities=capabilities(),
            primary_execution_status="pending", analysis_execution_status="pending",
            problem_contract_status="frozen", semantic_closure_status="pending",
            complexity_sanity_status="pending",
        )
        for field in ("semantic_revision", "validated_semantic_revision",
                      "approved_semantic_revision", "semantic_identity_hash",
                      "validated_semantic_identity_hash", "approved_semantic_identity_hash"):
            entry.pop(field, None)
    state["subproblems"]["Q2"]["depends_on"] = [{"question": "Q1", "kind": "result"}]
    path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False),
                    encoding="utf-8")
    return path


class QuestionScopedSyncTests(unittest.TestCase):
    def test_scoped_q1_code_is_not_blocked_by_missing_independent_q2_q3_code(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            three_question_project(root)
            full = SYNC.synchronize(root, write=False, delivery_scope="code")
            self.assertTrue(any("缺少标准主求解脚本" in item for item in full["issues"]), full)
            scoped = SYNC.synchronize(root, write=False, delivery_scope="code", question="Q1")
            self.assertEqual(set(scoped["questions"]), {"Q1"}, scoped)
            self.assertEqual(scoped["target_question"], "Q1")
            self.assertNotIn("Q2", scoped["upstream_question_snapshots"])
            self.assertFalse(any("缺少标准主求解脚本" in item for item in scoped["issues"]), scoped)

    def test_result_dependency_observes_only_necessary_upstream_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            three_question_project(root)
            scoped = SYNC.synchronize(root, write=False, delivery_scope="code", question="Q2")
            self.assertEqual(set(scoped["questions"]), {"Q2"})
            self.assertEqual(set(scoped["upstream_question_snapshots"]), {"Q1"})
            self.assertNotIn("Q3", scoped["questions"])
            self.assertNotIn("Q3", scoped["upstream_question_snapshots"])

    def test_model_dependency_does_not_demand_upstream_numeric_code(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = three_question_project(root)
            state = yaml.safe_load(path.read_text(encoding="utf-8"))
            state["subproblems"]["Q2"]["depends_on"] = [{"question": "Q1", "kind": "model"}]
            path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False),
                            encoding="utf-8")
            scoped = SYNC.synchronize(root, write=False, delivery_scope="design", question="Q2")
            self.assertEqual(set(scoped["questions"]), {"Q2"})
            self.assertFalse(scoped["upstream_question_snapshots"])
            self.assertIn("Q1", scoped["upstream_question_evidence"])
            self.assertFalse(any("Q1: 当前源码缺少" in item for item in scoped["issues"]), scoped)

    def test_changed_q1_uses_global_graph_to_stale_q2_not_independent_q3(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = three_question_project(root)
            state = yaml.safe_load(path.read_text(encoding="utf-8"))
            before_q3 = deepcopy(state["subproblems"]["Q3"])
            source = root / "问题一求解/问题一求解.py"
            source.write_bytes(source.read_bytes() + b"\n# M4 synthetic drift\n")
            report = SYNC.synchronize(root, write=True, delivery_scope="code", question="Q1")
            saved = yaml.safe_load(path.read_text(encoding="utf-8"))
            self.assertIn("Q2", report["stale_questions"], report)
            self.assertTrue(saved["subproblems"]["Q2"]["artifacts_stale"])
            self.assertEqual(saved["subproblems"]["Q3"], before_q3)

    def test_repeating_an_unchanged_question_sync_does_not_rewrite_state(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = three_question_project(root)
            first = SYNC.synchronize(root, write=True, delivery_scope="code", question="Q1")
            before = path.read_bytes()
            generation = yaml.safe_load(before)["project"].get("state_generation", 0)
            second = SYNC.synchronize(root, write=True, delivery_scope="code", question="Q1")
            after = path.read_bytes()
            self.assertEqual(after, before, (first, second))
            self.assertEqual(yaml.safe_load(after)["project"].get("state_generation", 0),
                             generation)
            self.assertFalse(second["state_write_performed"], second)
            self.assertTrue((root / "sync_report.yaml").is_file())

    def test_global_backend_conflict_is_not_hidden_by_question_scope(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = three_question_project(root)
            state = yaml.safe_load(path.read_text(encoding="utf-8"))
            state["execution"]["solver_backend"] = "matlab"
            path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False),
                            encoding="utf-8")
            report = SYNC.synchronize(root, write=False, delivery_scope="code", question="Q1")
            self.assertEqual(report["status"], "failed")
            self.assertTrue(any("后端" in item or "backend" in item for item in report["issues"]), report)

    def test_unknown_question_and_final_delivery_scope_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            three_question_project(root)
            with self.assertRaisesRegex(ValueError, "Q9"):
                SYNC.synchronize(root, write=False, delivery_scope="code", question="Q9")
            for scope in ("docx", "latex", "submission", "mechanism"):
                with self.subTest(scope=scope), self.assertRaises(ValueError):
                    SYNC.synchronize(root, write=False, delivery_scope=scope, question="Q1")

    def test_unchanged_unscoped_sync_keeps_legacy_all_questions_behavior(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            three_question_project(root)
            report = SYNC.synchronize(root, write=False, delivery_scope="code")
            self.assertEqual(set(report["questions"]), {"Q1", "Q2", "Q3"})
            self.assertNotIn("target_question", report)


if __name__ == "__main__":
    unittest.main()
