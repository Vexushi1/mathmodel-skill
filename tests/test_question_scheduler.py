from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import question_scheduler as SCHEDULER
from tests.test_question_runtime_integration import build_three_question_project
from tests.test_v712_runtime_assurance import load_runtime


def state_fixture() -> dict:
    return {
        "subproblems": {
            "Q1": {"status": "designed", "depends_on": []},
            "Q2": {"status": "audited", "depends_on": [
                {"question": "Q1", "kind": "result"}]},
            "Q3": {"status": "audited", "depends_on": []},
        },
        "preprocessing": {"decision": "not_needed"},
    }


def select(state: dict, *, question=None, request="", intents=("full_solution",)):
    return SCHEDULER.select_question(
        state, explicit_question=question, selected_intents=intents, request=request,
    )


class ExplicitQuestionScopeTests(unittest.TestCase):
    def test_no_question_never_selects_first_or_next_action(self):
        state = state_fixture()
        frozen = deepcopy(state)
        result = select(state)
        self.assertEqual(result["scope_kind"], "project")
        self.assertIsNone(result["selected_question"])
        self.assertEqual(result["selection_reason"], "explicit_question_required")
        self.assertEqual(result["blocked_questions"], {})
        self.assertEqual(result["waiting_action"], None)
        self.assertEqual(state, frozen)

    def test_resume_request_does_not_autoselect_waiting_question(self):
        state = state_fixture()
        state["subproblems"]["Q1"]["primary_execution_status"] = "awaiting_user_execution"
        for request in ("继续", "恢复求解", "resume", "continue"):
            with self.subTest(request=request):
                result = select(state, request=request)
                self.assertIsNone(result["selected_question"])
                self.assertEqual(result["selection_reason"], "explicit_question_required")

    def test_mixed_dependency_graph_does_not_choose_independent_sibling(self):
        state = state_fixture()
        state["subproblems"]["Q3"]["depends_on"] = [
            {"question": "Q2", "kind": "model"}]
        state["subproblems"]["Q1"]["depends_on"] = [
            {"question": "Q3", "kind": "result"}]
        result = select(state)
        self.assertIsNone(result["selected_question"])
        self.assertEqual(result["blocked_questions"], {})
        self.assertEqual(result["prerequisite_closure"], [])

    def test_explicit_question_is_only_target_and_does_not_recheck_siblings(self):
        state = state_fixture()
        state["subproblems"]["Q2"]["depends_on"] = [
            {"question": "Q1", "kind": "model"}]
        state["subproblems"]["Q1"]["depends_on"] = [
            {"question": "Q3", "kind": "result"}]
        original = deepcopy(state)
        result = select(state, question="Q2")
        self.assertEqual(result["scope_kind"], "question")
        self.assertEqual(result["selected_question"], "Q2")
        self.assertEqual(result["selection_reason"], "explicit_question")
        self.assertEqual(result["blocked_questions"], {})
        self.assertEqual(state, original)

    def test_unregistered_question_fails_scope_without_implicit_registration(self):
        result = select(state_fixture(), question="Q9")
        self.assertEqual(result["selected_question"], "Q9")
        self.assertEqual(result["blocked_questions"]["Q9"][0]["reason"],
                         "question_not_registered")

    def test_project_routes_stay_project_scoped(self):
        for intent in ("problem_analysis", "project_sync", "full_submission", "review"):
            with self.subTest(intent=intent):
                result = select(state_fixture(), intents=(intent,))
                self.assertEqual(result["scope_kind"], "project")
                self.assertIsNone(result["selected_question"])
                self.assertEqual(result["selection_reason"], "project_level_route")

    def test_question_listing_uses_natural_number_order_without_selection(self):
        state = state_fixture()
        state["subproblems"] = {
            "Q10": state["subproblems"]["Q3"], "Q2": state["subproblems"]["Q2"],
            "Q1": state["subproblems"]["Q1"],
        }
        result = select(state)
        self.assertEqual([x["question"] for x in result["candidate_questions"]],
                         ["Q1", "Q2", "Q10"])
        self.assertIsNone(result["selected_question"])

    def test_loaded_resolver_requires_explicit_q_before_any_artifact_hydration(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build_three_question_project(root)
            runtime = load_runtime()
            for request in (None, "继续求解"):
                with self.subTest(request=request):
                    with patch.object(
                        runtime, "hydrate_project_context",
                        side_effect=AssertionError("must not hydrate siblings"),
                    ):
                        with self.assertRaisesRegex(ValueError, "question Qn"):
                            runtime.resolve_runtime(
                                "full_solution", request=request, project_root=root,
                            )

    def test_loaded_resolver_explicit_q1_does_not_read_unrelated_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build_three_question_project(root)
            runtime = load_runtime()
            original = runtime.hydrate_project_context
            visited = []

            def scoped(project_root, question=None, **kwargs):
                visited.append(question)
                if question in {"Q2", "Q3"}:
                    raise AssertionError("unrelated question artifacts hydrated")
                return original(project_root, question, **kwargs)

            with patch.object(runtime, "hydrate_project_context", side_effect=scoped):
                plan = runtime.resolve_runtime(
                    "full_solution", project_root=root, question="Q1",
                )
            self.assertEqual(plan["assurance"]["context"]["question"], "Q1")
            self.assertEqual(set(visited), {"Q1"})
            self.assertNotIn("question_selection", plan)
            self.assertIn("code_delivery",
                          plan["runtime_plan"]["pre_delivery_gate_names"])

    def test_loaded_project_level_request_remains_available_without_q(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build_three_question_project(root)
            runtime = load_runtime()
            plan = runtime.resolve_runtime("problem_analysis", project_root=root)
            self.assertIsNone(plan["assurance"]["context"]["question"])
            self.assertNotIn("question_selection", plan)

    def test_stateless_generic_question_level_planning_remains_available(self):
        runtime = load_runtime()
        plan = runtime.resolve_runtime("full_solution", objective="optimization",
                                       structures=[])
        self.assertFalse(plan["assurance"]["context"]["project_state_loaded"])


if __name__ == "__main__":
    unittest.main()
