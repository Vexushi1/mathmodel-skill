from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
import sys

SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import project_transaction as TX


class ProjectTransactionTests(unittest.TestCase):
    def make_project(self, root: Path, generation: int | None = 0) -> dict:
        (root / "state").mkdir(parents=True, exist_ok=True)
        project = {"competition": "test", "problem": "A", "current_phase": "model_design"}
        if generation is not None:
            project["state_generation"] = generation
        state = {"project": project, "subproblems": {}}
        (root / "state/project_state.yaml").write_text(
            yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )
        (root / "模型论文框架.md").write_text("old framework\n", encoding="utf-8")
        (root / "sync_report.yaml").write_text("status: old\n", encoding="utf-8")
        return state

    def read_state(self, root: Path) -> dict:
        return yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8"))

    def test_atomic_single_file_replace(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested/value.txt"
            path.parent.mkdir()
            path.write_text("old", encoding="utf-8")
            TX.atomic_write_text(path, "new")
            self.assertEqual(path.read_text(encoding="utf-8"), "new")
            self.assertEqual(list(path.parent.glob(f".{path.name}.*.tmp")), [])

    def test_missing_generation_is_legacy_zero_and_first_write_persists_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = self.make_project(root, generation=None)
            self.assertEqual(TX.state_generation(state), 0)
            TX.commit_project_state(root, state, expected_generation=0)
            self.assertEqual(self.read_state(root)["project"]["state_generation"], 1)

    def test_generation_conflict_rejects_stale_writer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root, generation=0)
            _, first, generation = TX.load_state_for_update(root)
            _, stale, stale_generation = TX.load_state_for_update(root)
            self.assertEqual(generation, 0)
            self.assertEqual(stale_generation, 0)
            first["project"]["current_phase"] = "solve_validate"
            TX.commit_project_state(root, first, expected_generation=generation)
            stale["project"]["current_phase"] = "result_analysis"
            with self.assertRaisesRegex(TX.GenerationConflictError, "stale project writer"):
                TX.commit_project_state(root, stale, expected_generation=stale_generation)
            live = self.read_state(root)
            self.assertEqual(live["project"]["state_generation"], 1)
            self.assertEqual(live["project"]["current_phase"], "solve_validate")

    def test_validation_failure_leaves_all_live_files_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = self.make_project(root, generation=0)
            before_state = (root / "state/project_state.yaml").read_text(encoding="utf-8")
            before_framework = (root / "模型论文框架.md").read_text(encoding="utf-8")

            def reject(_staged):
                raise ValueError("simulated staged validation failure")

            state["project"]["current_phase"] = "solve_validate"
            with self.assertRaisesRegex(ValueError, "simulated staged validation failure"):
                TX.commit_project_state(
                    root,
                    state,
                    expected_generation=0,
                    writes_before_state=[("模型论文框架.md", "new framework\n")],
                    validators=[reject],
                )
            self.assertEqual((root / "state/project_state.yaml").read_text(encoding="utf-8"), before_state)
            self.assertEqual((root / "模型论文框架.md").read_text(encoding="utf-8"), before_framework)
            self.assertFalse((root / TX.JOURNAL_RELATIVE_PATH).exists())
            self.assertEqual(list(root.rglob("*.stage")), [])
            self.assertEqual(list(root.rglob("*.bak")), [])

    def _crash_and_recover(self, point: str) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = self.make_project(root, generation=0)
            state["project"]["current_phase"] = "solve_validate"

            def crash(current: str):
                if current == point:
                    raise RuntimeError(f"crash at {point}")

            with self.assertRaisesRegex(RuntimeError, "crash at"):
                TX.commit_project_state(
                    root,
                    state,
                    expected_generation=0,
                    writes_before_state=[("模型论文框架.md", "new framework\n")],
                    writes_after_state=[("sync_report.yaml", "status: new\n")],
                    failure_hook=crash,
                )
            self.assertTrue((root / TX.JOURNAL_RELATIVE_PATH).is_file())
            recovered = TX.recover_project_transaction(root)
            self.assertTrue(recovered["recovered"])
            self.assertEqual(recovered["status"], "rolled_forward")
            self.assertEqual((root / "模型论文框架.md").read_text(encoding="utf-8"), "new framework\n")
            self.assertEqual((root / "sync_report.yaml").read_text(encoding="utf-8"), "status: new\n")
            self.assertEqual(self.read_state(root)["project"]["state_generation"], 1)
            self.assertFalse((root / TX.JOURNAL_RELATIVE_PATH).exists())
            self.assertEqual(list(root.rglob("*.stage")), [])
            self.assertEqual(list(root.rglob("*.bak")), [])

    def test_recovery_after_framework_replace_before_state_replace(self):
        self._crash_and_recover("after_replace:模型论文框架.md")

    def test_recovery_after_state_replace_before_report_replace(self):
        self._crash_and_recover("after_replace:state/project_state.yaml")

    def test_recovery_rejects_unknown_third_party_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = self.make_project(root, generation=0)

            def crash(point: str):
                if point == "after_replace:模型论文框架.md":
                    raise RuntimeError("crash")

            with self.assertRaises(RuntimeError):
                TX.commit_project_state(
                    root,
                    state,
                    expected_generation=0,
                    writes_before_state=[("模型论文框架.md", "new framework\n")],
                    writes_after_state=[("sync_report.yaml", "status: new\n")],
                    failure_hook=crash,
                )
            live = self.read_state(root)
            live["project"]["state_generation"] = 7
            TX.atomic_write_text(
                root / "state/project_state.yaml",
                yaml.safe_dump(live, allow_unicode=True, sort_keys=False),
            )
            with self.assertRaisesRegex(TX.GenerationConflictError, "cannot recover transaction"):
                TX.recover_project_transaction(root)

    def test_generation_change_after_staging_aborts_without_journal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = self.make_project(root, generation=0)

            def concurrent(point: str):
                if point == "after_stage":
                    live = self.read_state(root)
                    live["project"]["state_generation"] = 1
                    live["project"]["current_phase"] = "external_writer"
                    TX.atomic_write_text(
                        root / "state/project_state.yaml",
                        yaml.safe_dump(live, allow_unicode=True, sort_keys=False),
                    )

            with self.assertRaisesRegex(TX.GenerationConflictError, "before commit"):
                TX.commit_project_state(
                    root,
                    state,
                    expected_generation=0,
                    failure_hook=concurrent,
                )
            self.assertFalse((root / TX.JOURNAL_RELATIVE_PATH).exists())
            self.assertEqual(list(root.rglob("*.stage")), [])
            self.assertEqual(list(root.rglob("*.bak")), [])
            self.assertEqual(self.read_state(root)["project"]["current_phase"], "external_writer")

    def test_successful_commit_cleans_journal_and_backups(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = self.make_project(root, generation=3)
            state["project"]["current_phase"] = "result_analysis"
            result = TX.commit_project_state(
                root,
                state,
                expected_generation=3,
                writes_before_state=[("模型论文框架.md", "new framework\n")],
                writes_after_state=[("sync_report.yaml", "status: passed\n")],
            )
            self.assertEqual(result["base_generation"], 3)
            self.assertEqual(result["target_generation"], 4)
            self.assertEqual(self.read_state(root)["project"]["state_generation"], 4)
            self.assertFalse((root / TX.JOURNAL_RELATIVE_PATH).exists())
            self.assertEqual(list(root.rglob("*.stage")), [])
            self.assertEqual(list(root.rglob("*.bak")), [])


if __name__ == "__main__":
    unittest.main()
