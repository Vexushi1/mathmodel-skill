"""Read-only project-wide backend declaration checks in the shared layer."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from stage_code import inspect_project_backend_declarations


def selected(backend: str = "python") -> dict:
    return {
        "execution": {
            "solver_backend": backend,
            "solver_backend_selection_reason": "全题数值能力与运行环境已审视",
        },
        "subproblems": {},
    }


def historical(backend: str = "python") -> dict:
    return {"backend": backend, "selection_reason": "historical selection"}


class SharedProjectBackendPolicyTests(unittest.TestCase):
    def test_unselected_project_does_not_infer_backend_from_environment(self):
        for state in ({}, {"execution": {"python_version": "3.12", "matlab_version": "R2025b"}},
                      {"project": {"version": "10.0.0"}, "subproblems": {"Q1": {"status": "designed"}}}):
            with self.subTest(state=state):
                report = inspect_project_backend_declarations(state, requested_backend="auto")
                self.assertEqual(report["kind"], "unselected")
                self.assertIsNone(report["selected_backend"])
                self.assertIsNone(report["candidate_backend"])
                self.assertFalse(report["execution_authorized"])

    def test_root_selection_requires_complete_valid_pair(self):
        invalid = (
            {"solver_backend": "python"},
            {"solver_backend_selection_reason": "reviewed"},
            {"solver_backend": "auto", "solver_backend_selection_reason": "reviewed"},
            {"solver_backend": True, "solver_backend_selection_reason": "reviewed"},
            {"solver_backend": "matlab", "solver_backend_selection_reason": " \n\t"},
        )
        for execution in invalid:
            with self.subTest(execution=execution):
                report = inspect_project_backend_declarations({"execution": execution})
                self.assertEqual(report["kind"], "invalid")
                self.assertTrue(report["issues"])
                self.assertFalse(report["execution_authorized"])

    def test_whole_project_conflict_in_other_question_is_visible(self):
        state = selected("python")
        state["subproblems"] = {
            "Q1": {"code": "问题一求解/问题一求解.py"},
            "Q2": {"code": "问题二求解/q2_solver.m"},
        }
        before = deepcopy(state)
        report = inspect_project_backend_declarations(state, requested_backend="python")
        self.assertEqual(report["kind"], "invalid")
        self.assertTrue(any("Q2.primary" in issue and "suffix" in issue for issue in report["issues"]))
        self.assertEqual(report["selected_backend"], "python")
        self.assertEqual(state, before)

    def test_legacy_consistent_candidate_and_mixed_history(self):
        consistent = {"subproblems": {
            "Q1": {"solver_execution": {"primary": historical()}},
            "Q2": {"solver_execution": {"primary": historical(), "analysis": historical()}},
        }}
        report = inspect_project_backend_declarations(consistent)
        self.assertEqual(report["kind"], "legacy_consistent")
        self.assertEqual(report["candidate_backend"], "python")
        self.assertIsNone(report["selected_backend"])
        self.assertTrue(all(not row["artifact_identity_verified"] for row in report["declarations"]))

        mixed = deepcopy(consistent)
        mixed["subproblems"]["Q2"]["solver_execution"]["analysis"] = historical("matlab")
        report = inspect_project_backend_declarations(mixed)
        self.assertEqual(report["kind"], "legacy_mixed")
        self.assertIsNone(report["candidate_backend"])
        self.assertIsNone(report["selected_backend"])

    def test_opposite_request_reports_conflict_without_mutating_policy(self):
        state = selected("matlab")
        state["subproblems"]["Q1"] = {"solver_execution": {"primary": {"bundle_sha256": "a" * 64}}}
        before = deepcopy(state)
        report = inspect_project_backend_declarations(state, requested_backend="python")
        self.assertEqual(report["kind"], "canonical_declarations")
        self.assertEqual(report["selected_backend"], "matlab")
        self.assertTrue(report["request_conflict"])
        self.assertTrue(any("conflicts with project backend" in issue for issue in report["issues"]))
        self.assertFalse(report["execution_authorized"])
        self.assertEqual(state, before)
        self.assertFalse(inspect_project_backend_declarations(state, requested_backend="auto")["request_conflict"])


if __name__ == "__main__":
    unittest.main()
