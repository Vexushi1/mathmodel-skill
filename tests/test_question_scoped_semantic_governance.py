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
import validate_semantic_governance as SEMANTIC
from tests.test_project_initialization import put_spec, specification


def project(root: Path, *, model_edge: bool = False) -> tuple[Path, Path]:
    authored = specification(3)
    if model_edge:
        authored["questions"]["Q2"]["depends_on"] = [{"question": "Q1", "kind": "model"}]
    source = put_spec(root, authored)
    result = INITIALIZE.initialize_project(root, source, write=True)
    assert result["status"] == "initialized", result
    return root / "state/project_state.yaml", root / "模型论文框架.md"


def state_file(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def write_state(path: Path, state: dict) -> None:
    path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")


class QuestionScopedSemanticGovernanceTests(unittest.TestCase):
    def test_q1_not_blocked_by_unrelated_unfinished_q3_or_model_without_sib(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_path, _ = project(root)
            state = state_file(state_path)
            state["subproblems"]["Q3"]["status"] = "designed"
            write_state(state_path, state)
            q3_before = deepcopy(state["subproblems"]["Q3"])
            all_questions = SEMANTIC.validate_project(root, write=False, strict=True)
            self.assertEqual(all_questions["status"], "failed", all_questions)
            self.assertTrue(any("Q3" in issue for issue in all_questions["issues"]))
            scoped = SEMANTIC.validate_project(root, write=True, strict=True, question="Q1")
            self.assertEqual(scoped["status"], "passed", scoped)
            self.assertEqual(scoped["scoped_questions"], ["Q1"])
            saved = state_file(state_path)
            self.assertEqual(saved["subproblems"]["Q3"], q3_before)
            self.assertNotIn("validated_semantic_identity_hash", saved["subproblems"]["Q3"])
            again = SEMANTIC.validate_project(root, write=True, strict=True, question="Q1")
            self.assertEqual(again["status"], "passed", again)
            self.assertEqual(state_file(state_path)["project"]["state_generation"],
                             saved["project"]["state_generation"], "identical scoped write must not bump generation")

    def test_q2_model_dependency_checks_necessary_upstream_semantics(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_path, framework_path = project(root, model_edge=True)
            self.assertEqual(SEMANTIC.validate_project(
                root, write=True, strict=True, question="Q1"
            )["status"], "passed")
            valid = SEMANTIC.validate_project(root, write=False, strict=True, question="Q2")
            self.assertEqual(valid["status"], "passed", valid)
            self.assertEqual(valid["scoped_questions"], ["Q1", "Q2"])
            original = framework_path.read_text(encoding="utf-8")
            self.assertIn("sum_i c_i * x_i", original)
            framework_path.write_text(original.replace("sum_i c_i * x_i",
                                                       "sum_i c_i * x_i + penalty", 1), encoding="utf-8")
            before = state_path.read_bytes()
            blocked = SEMANTIC.validate_project(root, write=False, strict=True, question="Q2")
            self.assertEqual(blocked["status"], "failed", blocked)
            self.assertTrue(any("Q1" in issue for issue in blocked["issues"]))
            self.assertEqual(state_path.read_bytes(), before)

    def test_changed_q1_stales_model_dependent_q2_not_independent_q3(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_path, _ = project(root, model_edge=True)
            first = SEMANTIC.validate_project(root, write=True, strict=True, question="Q1")
            self.assertEqual(first["status"], "passed", first)
            current = state_file(state_path)
            before_q3 = deepcopy(current["subproblems"]["Q3"])
            current["subproblems"]["Q1"]["semantic_revision"] += 1
            current["subproblems"]["Q1"]["semantic_change_categories"] = ["objective"]
            write_state(state_path, current)
            report = SEMANTIC.validate_project(root, write=True, strict=True, question="Q1")
            self.assertEqual(report["status"], "passed", report)
            self.assertEqual(report["changed_sources"], ["Q1"])
            self.assertEqual(report["affected_questions"], ["Q1", "Q2"])
            saved = state_file(state_path)
            self.assertEqual(saved["subproblems"]["Q3"], before_q3)
            self.assertTrue(saved["subproblems"]["Q2"]["artifacts_stale"])

    def test_scoped_semantic_gate_rejects_global_schema_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_path, _ = project(root)
            original = state_file(state_path)
            del original["subproblems"]["Q3"]["capabilities"]["requires_convergence_diagnostic"]
            write_state(state_path, original)
            before = state_path.read_bytes()
            for write in (False, True):
                result = SEMANTIC.validate_project(root, write=write, strict=True, question="Q1")
                self.assertEqual(result["status"], "failed", result)
                self.assertTrue(any("schema" in issue and "Q3" in issue for issue in result["issues"]), result)
                self.assertEqual(state_path.read_bytes(), before)

    def test_actual_resolver_targets_semantic_gate_only_in_question_stage(self):
        from tests.test_v712_runtime_assurance import load_runtime

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project(root)
            runtime = load_runtime()
            plan = runtime.resolve_runtime("full_solution", project_root=root, question="Q1")
            named = {row["name"]: row["command"] for row in plan["pre_delivery_gates"]}
            self.assertIn("semantic_governance", named, named)
            self.assertIn('--question "Q1"', named["semantic_governance"])

            full = runtime.resolve_runtime("review", project_root=root, question="Q1")
            for gate in full["pre_delivery_gates"]:
                if gate["name"] == "semantic_governance":
                    self.assertNotIn("--question", gate["command"])

    def test_unknown_question_fails_closed_and_preserves_state(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_path, _ = project(root)
            before = state_path.read_bytes()
            result = SEMANTIC.validate_project(root, write=True, strict=True, question="Q9")
            self.assertEqual(result["status"], "failed")
            self.assertTrue(any("Q9" in issue for issue in result["issues"]))
            self.assertEqual(state_path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
