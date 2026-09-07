from __future__ import annotations

import hashlib
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import project_transaction as TX
import validate_code_delivery as CODE
import validate_semantic_governance as SEMANTIC
from tests.test_sync_project import load_syncer, setup_project
from tests.test_v900_semantic_governance import framework, identity_payload


class TransactionalWriterContractTests(unittest.TestCase):
    def test_schema_adds_optional_generation_for_legacy_read_compatibility(self):
        schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        project = schema["properties"]["project"]
        generation = project["properties"]["state_generation"]
        self.assertEqual(generation["type"], "integer")
        self.assertEqual(generation["minimum"], 0)
        self.assertEqual(generation["default"], 0)
        self.assertNotIn("state_generation", project["required"])
        example = yaml.safe_load((ROOT / "state/project_state.example.yaml").read_text(encoding="utf-8"))
        self.assertEqual(example["project"]["state_generation"], 0)

    def test_control_plane_writers_do_not_bypass_transaction_helper(self):
        for relative in (
            "scripts/sync_project.py",
            "scripts/validate_semantic_governance.py",
            "scripts/validate_code_delivery.py",
            "scripts/validate_user_execution.py",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("project_transaction", text, relative)
            self.assertNotIn("state_path.write_text", text, relative)
        sync_text = (ROOT / "scripts/sync_project.py").read_text(encoding="utf-8")
        self.assertNotIn("_update_framework_header", sync_text)
        self.assertIn("writes_before_state", sync_text)
        self.assertIn("writes_after_state", sync_text)

    def test_code_delivery_write_advances_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "state").mkdir()
            folder = root / "问题一求解"
            folder.mkdir()
            script = folder / "问题一求解.py"
            script.write_text("print('full')\n", encoding="utf-8")
            state = {
                "project": {
                    "competition": "test",
                    "problem": "A",
                    "current_phase": "solve_validate",
                },
                "subproblems": {"Q1": {"status": "designed"}},
            }
            (root / "state/project_state.yaml").write_text(
                yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            config = {
                "problem_name": "问题一",
                "stage": "primary",
                "data_sha256": "a" * 64,
            }
            CODE.update_state(root, config, script)
            updated = yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8"))
            self.assertEqual(updated["project"]["state_generation"], 1)
            self.assertEqual(
                updated["subproblems"]["Q1"]["primary_code_sha256"],
                hashlib.sha256(script.read_bytes()).hexdigest(),
            )
            self.assertFalse((root / TX.JOURNAL_RELATIVE_PATH).exists())

    def test_semantic_governance_structured_write_advances_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "state").mkdir()
            state = {
                "semantic_governance_version": "1.0.0",
                "project": {
                    "competition": "test",
                    "problem": "A",
                    "current_phase": "model_design",
                },
                "subproblems": {
                    "Q1": {
                        "status": "designed",
                        "problem_contract_status": "frozen",
                        "semantic_closure_status": "passed",
                        "complexity_sanity_status": "passed",
                        "complexity_sanity_flags": [],
                        "semantic_revision": 1,
                        "semantic_change_categories": ["initial_design"],
                        "result_quality_status": "pending",
                        "result_analysis_status": "pending",
                        "result_summary_status": "pending",
                        "depends_on": [],
                    }
                },
                "paper_framework": {"paper_fragments": [], "sync_status": "current"},
            }
            (root / "state/project_state.yaml").write_text(
                yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            (root / "模型论文框架.md").write_text(
                framework(identity_payload()), encoding="utf-8"
            )
            report = SEMANTIC.validate_project(root, write=True, strict=True)
            self.assertEqual(report["status"], "passed", report)
            self.assertEqual(report["legacy_write_blocked_sources"], [])
            updated = yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8"))
            self.assertEqual(updated["project"]["state_generation"], 1)
            self.assertIn("semantic_identity_hash", updated["subproblems"]["Q1"])
            self.assertNotIn("semantic_hash", updated["subproblems"]["Q1"])
            self.assertFalse((root / TX.JOURNAL_RELATIVE_PATH).exists())

    def test_repeated_sync_is_transition_idempotent_and_generation_monotonic(self):
        syncer = load_syncer()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_project(root, status="designed", phase="model_design")
            first = syncer.synchronize(root, write=True)
            state1 = yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8"))
            self.assertEqual(state1["project"]["state_generation"], 1)
            self.assertFalse((root / TX.JOURNAL_RELATIVE_PATH).exists())

            second = syncer.synchronize(root, write=True)
            state2 = yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8"))
            self.assertEqual(state2["project"]["state_generation"], 2)
            self.assertEqual(second["state_transitions"], [])
            self.assertEqual(second["stale_questions"], first["stale_questions"])
            self.assertFalse((root / TX.JOURNAL_RELATIVE_PATH).exists())


if __name__ == "__main__":
    unittest.main()
