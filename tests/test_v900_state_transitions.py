from __future__ import annotations

import importlib.util
import sys
import unittest
from copy import deepcopy
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def load_module(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {relative}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


TRANSITIONS = load_module("v900_state_transitions", "scripts/state_transitions.py")
CONTRACT = yaml.safe_load((ROOT / "core/state_transition_contract.yaml").read_text(encoding="utf-8"))


def entry(*, depends_on=None) -> dict:
    return {
        "status": "validated",
        "depends_on": list(depends_on or []),
        "model_challenge_status": "passed",
        "human_model_approval_status": "approved",
        "primary_execution_status": "accepted",
        "analysis_execution_status": "accepted",
        "result_quality_status": "passed",
        "result_analysis_status": "passed",
        "validation_status": "passed",
        "result_summary_status": "current",
        "artifacts_stale": False,
        "stale_layers": [],
    }


def state_with_dependency(kind: str | None) -> dict:
    dependency = "Q1" if kind is None else {"question": "Q1", "kind": kind}
    return {
        "subproblems": {
            "Q1": entry(),
            "Q2": entry(depends_on=[dependency]),
        }
    }


class StateTransitionAuthorityTests(unittest.TestCase):
    def test_contract_owns_phase_d_rules(self):
        self.assertEqual(CONTRACT["version"], "1.0.0")
        self.assertIn("semantic_identity_changed", CONTRACT["transition_events"])
        self.assertEqual(
            set(CONTRACT["dependency_rules"]),
            {"model", "result", "parameter", "data", "legacy_untyped"},
        )
        self.assertEqual(CONTRACT["compatibility"]["legacy_string_dependency_policy"], "conservative_full_invalidation")

    def test_engine_has_no_project_file_io(self):
        text = (ROOT / "scripts/state_transitions.py").read_text(encoding="utf-8")
        self.assertNotIn("write_text(", text)
        self.assertNotIn("read_text(", text)
        self.assertNotIn("yaml.safe_load", text)


class TypedPropagationTests(unittest.TestCase):
    EVENT_EXPECTATIONS = {
        "semantic_identity_changed": {"model", "result", "parameter", "data"},
        "primary_code_changed": {"result"},
        "analysis_code_changed": set(),
        "data_changed": {"data", "parameter", "result"},
        "solution_workbook_changed": {"result"},
        "analysis_workbook_changed": set(),
        "matlab_script_changed": set(),
        "figure_bundle_changed": set(),
    }

    def test_eight_events_x_four_dependency_kinds(self):
        for event, expected_kinds in self.EVENT_EXPECTATIONS.items():
            for kind in ("data", "parameter", "model", "result"):
                with self.subTest(event=event, kind=kind):
                    state = state_with_dependency(kind)
                    context = (
                        {"semantic_change_categories": ["parameter", "data_scope"]}
                        if event == "semantic_identity_changed"
                        else {}
                    )
                    report = TRANSITIONS.apply_transition(
                        state,
                        event=event,
                        source_question="Q1",
                        contract=CONTRACT,
                        context=context,
                    )
                    downstream = [
                        row for row in report["transitions"]
                        if row["scope"] == "downstream" and row["question"] == "Q2"
                    ]
                    self.assertEqual(bool(downstream), kind in expected_kinds)
                    if kind in expected_kinds:
                        self.assertIn("Q2", report["affected_questions"])
                    else:
                        self.assertNotIn("Q2", report["affected_questions"])

    def test_model_dependency_invalidates_approval_but_result_dependency_preserves_it(self):
        model_state = state_with_dependency("model")
        TRANSITIONS.apply_transition(
            model_state,
            event="semantic_identity_changed",
            source_question="Q1",
            contract=CONTRACT,
        )
        self.assertEqual(model_state["subproblems"]["Q2"]["model_challenge_status"], "stale")
        self.assertEqual(model_state["subproblems"]["Q2"]["human_model_approval_status"], "stale")

        result_state = state_with_dependency("result")
        TRANSITIONS.apply_transition(
            result_state,
            event="semantic_identity_changed",
            source_question="Q1",
            contract=CONTRACT,
        )
        self.assertEqual(result_state["subproblems"]["Q2"]["model_challenge_status"], "passed")
        self.assertEqual(result_state["subproblems"]["Q2"]["human_model_approval_status"], "approved")
        self.assertEqual(result_state["subproblems"]["Q2"]["primary_execution_status"], "pending")
        self.assertEqual(result_state["subproblems"]["Q2"]["result_quality_status"], "pending")

    def test_parameter_dependency_requires_parameter_impact(self):
        unchanged = state_with_dependency("parameter")
        report = TRANSITIONS.apply_transition(
            unchanged,
            event="semantic_identity_changed",
            source_question="Q1",
            contract=CONTRACT,
            context={"semantic_change_categories": ["objective"]},
        )
        self.assertEqual(report["affected_questions"], ["Q1"])

        changed = state_with_dependency("parameter")
        report = TRANSITIONS.apply_transition(
            changed,
            event="semantic_identity_changed",
            source_question="Q1",
            contract=CONTRACT,
            context={"semantic_change_categories": ["parameter"]},
        )
        self.assertEqual(report["affected_questions"], ["Q1", "Q2"])
        self.assertEqual(changed["subproblems"]["Q2"]["model_challenge_status"], "passed")

    def test_data_dependency_ignores_figure_only_change(self):
        state = state_with_dependency("data")
        report = TRANSITIONS.apply_transition(
            state,
            event="figure_bundle_changed",
            source_question="Q1",
            contract=CONTRACT,
        )
        self.assertEqual(report["affected_questions"], ["Q1"])
        self.assertFalse(state["subproblems"]["Q2"]["artifacts_stale"])

    def test_legacy_untyped_dependency_is_conservatively_invalidated(self):
        state = state_with_dependency(None)
        report = TRANSITIONS.apply_transition(
            state,
            event="analysis_code_changed",
            source_question="Q1",
            contract=CONTRACT,
        )
        self.assertEqual(report["affected_questions"], ["Q1", "Q2"])
        q2 = state["subproblems"]["Q2"]
        self.assertEqual(q2["model_challenge_status"], "stale")
        self.assertEqual(q2["human_model_approval_status"], "stale")
        self.assertIn("model", q2["stale_layers"])


class DeterminismTests(unittest.TestCase):
    def test_dependency_cycle_is_reported_deterministically_and_terminates(self):
        state = {
            "subproblems": {
                "Q1": entry(depends_on=[{"question": "Q2", "kind": "result"}]),
                "Q2": entry(depends_on=[{"question": "Q1", "kind": "result"}]),
            }
        }
        report = TRANSITIONS.apply_transition(
            state,
            event="solution_workbook_changed",
            source_question="Q1",
            contract=CONTRACT,
        )
        self.assertEqual(report["dependency_cycles"], ["Q1 -> Q2 -> Q1"])
        self.assertEqual(report["affected_questions"], ["Q1", "Q2"])
        self.assertLessEqual(len(report["transitions"]), 3)

    def test_same_transition_is_state_idempotent(self):
        state = state_with_dependency("result")
        TRANSITIONS.apply_transition(
            state,
            event="primary_code_changed",
            source_question="Q1",
            contract=CONTRACT,
        )
        once = deepcopy(state)
        TRANSITIONS.apply_transition(
            state,
            event="primary_code_changed",
            source_question="Q1",
            contract=CONTRACT,
        )
        self.assertEqual(state, once)

    def test_merge_reports_preserves_edge_provenance(self):
        state = {
            "subproblems": {
                "Q1": entry(),
                "Q2": entry(depends_on=[{"question": "Q1", "kind": "result"}]),
                "Q3": entry(depends_on=[{"question": "Q2", "kind": "result"}]),
            }
        }
        first = TRANSITIONS.apply_transition(
            state,
            event="primary_code_changed",
            source_question="Q1",
            contract=CONTRACT,
        )
        merged = TRANSITIONS.merge_transition_reports([first])
        self.assertEqual(merged["affected_questions"], ["Q1", "Q2", "Q3"])
        self.assertTrue(
            any(
                row["scope"] == "downstream"
                and row["source"] == "Q2"
                and row["question"] == "Q3"
                and row["dependency_kind"] == "result"
                for row in merged["transitions"]
            )
        )


if __name__ == "__main__":
    unittest.main()
