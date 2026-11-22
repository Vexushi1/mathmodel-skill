from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import initialize_project as INITIALIZE
import project_transaction as TX
import validate_model_paper_framework as FRAMEWORK
import validate_project_state as STATE
import validate_semantic_governance as SEMANTIC

from tests.test_v900_semantic_governance import identity_payload


def specification(count: int = 3) -> dict:
    if count not in (1, 3, 5):
        raise AssertionError("fixture expects 1, 3 or 5 questions")
    keys = [f"Q{number}" for number in range(1, count + 1)]
    model_identity = identity_payload()
    question_entries = {}
    for key in keys:
        dependency = [{"question": "Q1", "kind": "result"}] if key == "Q2" else []
        question_entries[key] = {
            "title": f"第{key[1:]}问",
            "problem_contract": f"{key} 目标、输入、边界与输出已由题目审计确定。",
            "classification": {
                "objective": "optimization" if key == "Q1" else (
                    "prediction" if key == "Q2" else "explanation"
                ),
                "structures": ["network"] if key == "Q1" else (
                    ["temporal"] if key == "Q2" else ["physical_mechanism"]
                ),
            },
            "capabilities": {},
            "depends_on": dependency,
        }
    question_entries["Q1"]["proposed_model"] = {
        "name": "MILP",
        "reason": "题面约束可表达为混合整数线性规划",
        "model_text": "本问主模型为容量约束下的混合整数规划，尚未经过独立挑战与人工批准。",
        "semantic_identity": model_identity,
        "semantic_closure": "passed",
        "complexity_sanity": "passed",
        "complexity_sanity_note": "已独立核对题面与模型规模；仍待 Model Challenge。",
    }
    return {
        "project": {"name": "合成三问安全初始化", "competition": "CUMCM", "problem": "A"},
        "preprocessing": {
            "decision": "not_needed",
            "evidence": ["已审查输入字段和单位，当前主模型无需项目级清洗。"],
        },
        "questions": question_entries,
    }


def put_spec(root: Path, data: dict) -> Path:
    path = root / "authored_project_start.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


class ProjectInitializationTests(unittest.TestCase):
    def test_one_three_five_questions_form_exact_pending_roster(self):
        for count in (1, 3, 5):
            with self.subTest(count=count), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source = put_spec(root, specification(count))
                preview = INITIALIZE.initialize_project(root, source)
                self.assertEqual(preview["status"], "ready_for_initialization")
                self.assertFalse((root / "state/project_state.yaml").exists())
                self.assertFalse((root / "模型论文框架.md").exists())

                committed = INITIALIZE.initialize_project(root, source, write=True)
                self.assertEqual(committed["status"], "initialized")
                self.assertEqual(committed["generation"], 1)
                state_path = root / "state/project_state.yaml"
                framework_path = root / "模型论文框架.md"
                state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
                framework = framework_path.read_text(encoding="utf-8")
                self.assertEqual(state["project"]["state_generation"], 1)
                self.assertEqual(state["requirements"]["total"], count)
                self.assertEqual(state["requirements"]["pending"], [f"Q{i}" for i in range(1, count + 1)])
                self.assertEqual(state["requirements"]["completed"], [])
                self.assertEqual(set(state["subproblems"]), set(state["requirements"]["pending"]))
                self.assertEqual(state["subproblems"]["Q1"]["status"], "designed")
                self.assertNotIn("semantic_identity_hash", state["subproblems"]["Q1"])
                self.assertEqual(state["subproblems"]["Q1"]["human_model_approval_status"], "pending")
                self.assertEqual(state["subproblems"]["Q1"]["model_challenge_status"], "pending")
                for i in range(2, count + 1):
                    entry = state["subproblems"][f"Q{i}"]
                    self.assertEqual(entry["status"], "audited")
                    self.assertEqual(entry["selected_model"], "")
                    self.assertEqual(entry["result_quality_status"], "pending")
                    self.assertEqual(entry["result_analysis_status"], "pending")
                    self.assertEqual(entry["human_model_approval_status"], "pending")
                    self.assertNotIn("approved_semantic_revision", entry)
                    self.assertNotIn("semantic_identity_hash", entry)
                    self.assertIn(entry["framework_section"], framework)
                self.assertEqual(state["artifacts"]["code"], [])
                self.assertEqual(state["artifacts"]["results"], [])
                self.assertNotIn("| T1 |", framework)
                self.assertNotIn("| N1 |", framework)
                self.assertNotIn("| paper.abstract.q1 |", framework)
                self.assertNotIn("| TC1 |", framework)
                self.assertFalse((root / TX.JOURNAL_RELATIVE_PATH).exists())
                self.assertEqual(STATE.validate_state_payload(state, project_root=root), [])
                self.assertEqual(FRAMEWORK.validate_framework_text(
                    framework, state=state, strict=False, mode="compact", project_root=root,
                ), [])

                before_state, before_framework = state_path.read_bytes(), framework_path.read_bytes()
                after = INITIALIZE.initialize_project(root, source, write=True)
                self.assertEqual(after["status"], "already_initialized")
                self.assertEqual((state_path.read_bytes(), framework_path.read_bytes()),
                                 (before_state, before_framework))
                self.assertEqual(yaml.safe_load(state_path.read_text())["project"]["state_generation"], 1)

    def test_full_framework_uses_canonical_template_and_validates(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = put_spec(root, specification(3))
            report = INITIALIZE.initialize_project(root, source, mode="full", write=True)
            self.assertEqual(report["status"], "initialized")
            state = yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8"))
            text = (root / "模型论文框架.md").read_text(encoding="utf-8")
            self.assertEqual(state["paper_framework"]["mode"], "full")
            self.assertIn("## 论文整体框架", text)
            self.assertEqual(FRAMEWORK.validate_framework_text(
                text, state=state, strict=False, mode="full", project_root=root,
            ), [])

    def test_proposed_identity_can_gain_validation_without_gaining_approval(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = put_spec(root, specification())
            INITIALIZE.initialize_project(root, source, write=True)
            read = SEMANTIC.validate_project(root, write=False, strict=True)
            self.assertEqual(read["status"], "failed")
            self.assertEqual(read["migration_sources"], ["Q1"])
            result = SEMANTIC.validate_project(root, write=True, strict=True)
            self.assertEqual(result["status"], "passed", result)
            saved = yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8"))
            self.assertEqual(saved["project"]["state_generation"], 2)
            self.assertEqual(saved["subproblems"]["Q1"]["human_model_approval_status"], "pending")
            self.assertNotIn("approved_semantic_identity_hash", saved["subproblems"]["Q1"])
            self.assertEqual(saved["subproblems"]["Q2"]["selected_model"], "")
            self.assertEqual(saved["subproblems"]["Q3"]["selected_model"], "")

    def test_reject_incomplete_or_fabricated_proposed_model(self):
        original = specification()
        cases = []
        changed = deepcopy(original)
        changed["questions"]["Q1"]["proposed_model"]["semantic_identity"]["question"] = "Q2"
        cases.append(changed)
        changed = deepcopy(original)
        changed["questions"]["Q1"]["proposed_model"]["semantic_identity"]["objective"]["expression"] = "__UNKNOWN__"
        cases.append(changed)
        changed = deepcopy(original)
        changed["questions"]["Q1"]["proposed_model"]["semantic_closure"] = "pending"
        cases.append(changed)
        changed = deepcopy(original)
        changed["questions"]["Q1"]["proposed_model"]["reason"] = ""
        cases.append(changed)
        changed = deepcopy(original)
        changed["questions"]["Q2"]["proposed_model"] = deepcopy(changed["questions"]["Q1"]["proposed_model"])
        cases.append(changed)
        changed = deepcopy(original)
        changed["questions"]["Q2"]["depends_on"][0]["question"] = "Q99"
        cases.append(changed)
        for bad in cases:
            with self.subTest(case=cases.index(bad)), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source = put_spec(root, bad)
                with self.assertRaises(INITIALIZE.InitializationError):
                    INITIALIZE.initialize_project(root, source, write=True)
                self.assertFalse((root / "state/project_state.yaml").exists())
                self.assertFalse((root / "模型论文框架.md").exists())

    def test_existing_partial_and_historical_projects_require_explicit_recovery(self):
        for kind in ("state_only", "framework_only", "historical_solver", "journal"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source = put_spec(root, specification())
                if kind == "state_only":
                    path = root / "state/project_state.yaml"
                    path.parent.mkdir()
                    path.write_text("project: {competition: prior}")
                if kind == "framework_only":
                    (root / "模型论文框架.md").write_text("old framework")
                if kind == "historical_solver":
                    (root / "问题一求解").mkdir()
                if kind == "journal":
                    path = root / TX.JOURNAL_RELATIVE_PATH
                    path.parent.mkdir()
                    path.write_text("status: prepared")
                with self.assertRaises(INITIALIZE.RecoveryRequired):
                    INITIALIZE.initialize_project(root, source, write=True)
                if kind == "state_only":
                    self.assertEqual((root / "state/project_state.yaml").read_text(),
                                     "project: {competition: prior}")
                else:
                    self.assertFalse((root / "state/project_state.yaml").exists())
                if kind == "framework_only":
                    self.assertEqual((root / "模型论文框架.md").read_text(), "old framework")
                else:
                    self.assertFalse((root / "模型论文框架.md").exists())

    def test_changed_spec_does_not_overwrite_current_project(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = put_spec(root, specification())
            INITIALIZE.initialize_project(root, source, write=True)
            state = root / "state/project_state.yaml"
            framework = root / "模型论文框架.md"
            before = (state.read_bytes(), framework.read_bytes())
            edited = specification()
            edited["questions"]["Q1"]["proposed_model"]["reason"] = "changed"
            put_spec(root, edited)
            with self.assertRaises(INITIALIZE.RecoveryRequired):
                INITIALIZE.initialize_project(root, source, write=True)
            self.assertEqual((state.read_bytes(), framework.read_bytes()), before)

    def test_source_read_set_detects_change_during_staging(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = put_spec(root, specification())
            def mutate(step: str) -> None:
                if step == "after_stage":
                    source.write_bytes(source.read_bytes() + b"\n# changed during preflight\n")
            with self.assertRaises(TX.ReadSetConflictError):
                INITIALIZE.initialize_project(root, source, write=True, failure_hook=mutate)
            self.assertFalse((root / TX.JOURNAL_RELATIVE_PATH).exists())
            self.assertFalse((root / "state/project_state.yaml").exists())
            self.assertFalse((root / "模型论文框架.md").exists())

    def test_interruption_requires_explicit_recovery_and_keeps_both_files(self):
        for stage in ("after_journal_prepared", "after_replace:模型论文框架.md",
                      "after_replace:state/project_state.yaml"):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                source = put_spec(root, specification())
                def interrupt(step: str) -> None:
                    if step == stage:
                        raise RuntimeError(f"synthetic crash at {step}")
                with self.assertRaises(RuntimeError):
                    INITIALIZE.initialize_project(root, source, write=True, failure_hook=interrupt)
                self.assertTrue((root / TX.JOURNAL_RELATIVE_PATH).is_file())
                with self.assertRaises(INITIALIZE.RecoveryRequired):
                    INITIALIZE.initialize_project(root, source, write=True)
                recovery = TX.recover_project_transaction(root)
                self.assertEqual(recovery["status"], "rolled_forward")
                self.assertTrue((root / "state/project_state.yaml").is_file())
                self.assertTrue((root / "模型论文框架.md").is_file())
                self.assertFalse((root / TX.JOURNAL_RELATIVE_PATH).exists())
                self.assertEqual(INITIALIZE.initialize_project(root, source)["status"], "already_initialized")


if __name__ == "__main__":
    unittest.main()
