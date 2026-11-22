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
    def question(name: str, depends_on=None):
        return {
            "status": "designed" if name == "Q1" else "audited",
            "problem_contract_status": "frozen",
            "model_challenge_status": "passed" if name == "Q1" else "pending",
            "human_model_approval_status": "approved" if name == "Q1" else "pending",
            "primary_execution_status": "pending",
            "result_quality_status": "pending",
            "result_analysis_status": "pending",
            "depends_on": list(depends_on or ()),
        }
    return {
        "subproblems": {
            "Q1": question("Q1"),
            "Q2": question("Q2", [{"question": "Q1", "kind": "result"}]),
            "Q3": question("Q3"),
        },
        "preprocessing": {"decision": "not_needed"},
    }


def select(state: dict, *, question=None, request="", verified=None, intents=("full_solution",)):
    return SCHEDULER.select_question(
        state, explicit_question=question, selected_intents=intents,
        request=request, verified_artifacts=verified,
    )


class QuestionSchedulerTests(unittest.TestCase):
    def test_first_available_question_and_result_dependency_blocker(self):
        source = state_fixture()
        snapshot = deepcopy(source)
        result = select(source)
        self.assertEqual(result["scope_kind"], "question")
        self.assertEqual(result["selected_question"], "Q1")
        self.assertEqual(result["selection_reason"], "first_unblocked_actionable")
        self.assertEqual(result["candidate_questions"][0]["next_action"], "primary_code_delivery")
        self.assertEqual(result["blocked_questions"]["Q2"][0]["kind"], "result")
        self.assertEqual(result["blocked_questions"]["Q2"][0]["reason"],
                         "upstream_validated_results_unverified")
        self.assertNotIn("Q3", result["blocked_questions"])
        self.assertEqual(source, snapshot)
        self.assertTrue(result["diagnostic_only"])

    def test_explicit_blocked_question_never_switches_to_independent_question(self):
        result = select(state_fixture(), question="Q2")
        self.assertEqual(result["selected_question"], "Q2")
        self.assertEqual(result["selection_reason"], "explicit_question")
        self.assertTrue(result["blocked_questions"]["Q2"])
        self.assertEqual(result["prerequisite_closure"],
                         [{"question": "Q2", "upstream": "Q1", "kind": "result"}])

    def test_unregistered_question_does_not_get_implicitly_registered(self):
        result = select(state_fixture(), question="Q4")
        self.assertEqual(result["selected_question"], "Q4")
        self.assertEqual(result["blocked_questions"]["Q4"][0]["reason"],
                         "question_not_registered")

    def test_unique_user_wait_is_reported_without_claiming_execution(self):
        source = state_fixture()
        source["subproblems"]["Q1"]["primary_execution_status"] = "awaiting_user_execution"
        result = select(source, request="继续")
        self.assertEqual(result["selected_question"], "Q1")
        self.assertEqual(result["selection_reason"], "resume_unique_wait")
        self.assertEqual(result["waiting_action"], "user_execution")
        # A generic next action can instead be the independent Q3 while Q1 awaits a run.
        alternative = select(source)
        self.assertEqual(alternative["selected_question"], "Q3")
        self.assertEqual(source["subproblems"]["Q1"]["primary_execution_status"],
                         "awaiting_user_execution")

    def test_model_only_dependency_does_not_wait_for_numeric_results(self):
        source = state_fixture()
        source["subproblems"]["Q2"]["depends_on"] = [{"question": "Q1", "kind": "model"}]
        result = select(source, question="Q2", verified={"Q1": ["locked_model_spec"]})
        self.assertEqual(result["selected_question"], "Q2")
        self.assertNotIn("Q2", result["blocked_questions"])
        self.assertEqual(result["prerequisite_closure"][0]["kind"], "model")

    def test_result_only_dependency_requires_verified_validated_results(self):
        source = state_fixture()
        result = select(source, verified={"Q1": ["accepted_solution_workbook"]}, question="Q2")
        self.assertIn("Q2", result["blocked_questions"])
        result = select(source, verified={"Q1": ["validated_results"]})
        self.assertEqual(result["selected_question"], "Q2")
        self.assertNotIn("Q2", result["blocked_questions"])

    def test_parameter_data_and_legacy_edges_remain_ambiguous_not_auto_passed(self):
        source = state_fixture()
        for edge, expected in (
            ({"question": "Q1", "kind": "parameter"}, "parameter_source_requires_review"),
            ({"question": "Q1", "kind": "data"}, "data_source_requires_review"),
            ("Q1", "legacy_dependency_kind_unresolved"),
        ):
            with self.subTest(edge=edge):
                source["subproblems"]["Q2"]["depends_on"] = [edge]
                result = select(source, question="Q2",
                                verified={"Q1": ["validated_results", "locked_model_spec"]})
                self.assertEqual(result["blocked_questions"]["Q2"][0]["reason"], expected)

    def test_project_preprocessing_is_a_global_prerequisite_not_machine_proof(self):
        source = state_fixture()
        source["preprocessing"] = {"decision": "project_level", "status": "pending"}
        source["subproblems"]["Q2"]["depends_on"] = [{"question": "Q1", "kind": "data"}]
        blocked = select(source, question="Q2")
        self.assertEqual(blocked["blocked_questions"]["Q2"][0]["reason"],
                         "project_preprocessing_unverified")
        source["execution"] = {"platform": "unreported", "python_version": "unreported"}
        still = select(source, question="Q2")
        self.assertEqual(still["blocked_questions"], blocked["blocked_questions"])
        self.assertNotIn("platform", still)
        self.assertNotIn("machine_verified", still)

    def test_numeric_question_order_and_cycle_isolation(self):
        source = state_fixture()
        source["subproblems"] = {
            "Q10": deepcopy(source["subproblems"]["Q3"]),
            "Q2": deepcopy(source["subproblems"]["Q3"]),
            "Q1": deepcopy(source["subproblems"]["Q1"]),
        }
        source["subproblems"]["Q1"]["status"] = "audited"
        source["subproblems"]["Q1"]["model_challenge_status"] = "pending"
        self.assertEqual(
            [row["question"] for row in select(source)["candidate_questions"]],
            ["Q1", "Q2", "Q10"],
        )
        source["subproblems"]["Q1"]["depends_on"] = [{"question": "Q2", "kind": "model"}]
        source["subproblems"]["Q2"]["depends_on"] = [{"question": "Q1", "kind": "model"}]
        result = select(source)
        self.assertEqual(result["selected_question"], "Q10")
        self.assertTrue(any(row["kind"] == "cycle" for row in result["blocked_questions"]["Q1"]))
        self.assertTrue(any(row["kind"] == "cycle" for row in result["blocked_questions"]["Q2"]))
        self.assertNotIn("Q10", result["blocked_questions"])

    def test_all_verified_results_switch_to_finalization_without_writing_state(self):
        source = state_fixture()
        original = deepcopy(source)
        verified = {"Q1": ["validated_results"], "Q2": ["validated_results"],
                    "Q3": ["validated_results"]}
        result = select(source, verified=verified)
        self.assertEqual(result["scope_kind"], "finalization")
        self.assertIsNone(result["selected_question"])
        self.assertEqual(result["selection_reason"], "all_required_results_verified")
        self.assertEqual(source, original)

    def test_project_routes_remain_project_scoped(self):
        source = state_fixture()
        for intent in ("problem_analysis", "project_sync", "full_submission", "review"):
            with self.subTest(intent=intent):
                result = select(source, intents=(intent,))
                self.assertEqual(result["scope_kind"], "project")
                self.assertIsNone(result["selected_question"])

    def test_real_resolver_autoselects_question_without_aggregating_classification(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build_three_question_project(root)
            runtime = load_runtime()
            plan = runtime.resolve_runtime("full_solution", project_root=root)
            self.assertEqual(plan["assurance"]["context"]["question"], "Q1")
            self.assertEqual(plan["classification"]["objective"], "optimization")
            self.assertEqual(plan["runtime_plan"]["selected_question"], "Q1")
            self.assertEqual(plan["runtime_plan"]["scope_kind"], "question")
            self.assertEqual(plan["question_selection"]["blocked_questions"]["Q2"][0]["kind"], "result")
            self.assertTrue(plan["question_selection"]["diagnostic_only"])
            self.assertFalse(plan["solver_backend"]["environment_verified"])

    def test_explicit_q1_does_not_read_unrelated_question_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build_three_question_project(root)
            runtime = load_runtime()
            original = runtime.hydrate_project_context
            visited = []

            def observed_hydration(project_root, question=None, **kwargs):
                visited.append(question)
                if question in {"Q2", "Q3"}:
                    raise AssertionError("Q1 continuation must not hydrate unrelated Q2/Q3 files")
                return original(project_root, question, **kwargs)

            with patch.object(runtime, "hydrate_project_context",
                              side_effect=observed_hydration):
                plan = runtime.resolve_runtime(
                    "full_solution", project_root=root, question="Q1",
                )
            self.assertEqual(plan["assurance"]["context"]["question"], "Q1")
            self.assertEqual(set(visited), {"Q1"})
            self.assertNotIn("question_selection", plan)
            self.assertIn("code_delivery", plan["runtime_plan"]["pre_delivery_gate_names"])

    def test_real_resolver_explicit_blocked_q2_retains_its_scope(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build_three_question_project(root)
            runtime = load_runtime()
            plan = runtime.resolve_runtime("full_solution", project_root=root, question="Q2")
            self.assertEqual(plan["assurance"]["context"]["question"], "Q2")
            self.assertNotIn("question_selection", plan)
            dependency = plan["assurance"]["context"]["dependency_diagnostics"]
            self.assertEqual(
                [(row["question"], row["upstream"]) for row in dependency["result_dependencies"]],
                [("Q2", "Q1")],
            )
            self.assertIn("code_delivery", plan["runtime_plan"]["pre_delivery_gate_names"])


if __name__ == "__main__":
    unittest.main()
