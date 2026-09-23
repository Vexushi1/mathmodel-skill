"""Project declaration diagnostics: never selection, migration or artifact acceptance."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from project_solver_backend import inspect_backend_declarations, inspect_project
from project_transaction import JOURNAL_RELATIVE_PATH, STATE_RELATIVE_PATH


def policy(backend="python"):
    return {"execution": {"solver_backend": backend, "solver_backend_selection_reason": "全题需求审视"},
            "subproblems": {}}


def legacy(backend="python"):
    return {"backend": backend, "selection_reason": "historical declaration"}


class ProjectBackendDeclarationTests(unittest.TestCase):
    def test_empty_and_environment_only_states_do_not_default_to_python(self):
        for state in ({}, {"execution": {"python_version": "3.12", "matlab_version": "R2024b"}},
                      {"project": {"version": "10.0.0"}}):
            with self.subTest(state=state):
                result = inspect_backend_declarations(state, requested_backend="auto")
                self.assertEqual(result["kind"], "unselected")
                self.assertIsNone(result["selected_backend"])
                self.assertIsNone(result["candidate_backend"])
                self.assertFalse(result["execution_authorized"])

    def test_canonical_declarations_are_diagnostic_not_schema_or_execution_approval(self):
        for backend in ("python", "matlab"):
            state = policy(backend)
            state["subproblems"]["Q1"] = {"solver_execution": {
                "primary": {"bundle_sha256": "a"*64, "validated_bundle_sha256": "b"*64},
                "analysis": {"bundle_sha256": "c"*64}}}
            before = deepcopy(state)
            result = inspect_backend_declarations(state)
            self.assertEqual(result["kind"], "canonical_declarations")
            self.assertEqual(result["selected_backend"], backend)
            for field in ("schema_validated", "environment_verified", "execution_authorized"):
                self.assertFalse(result[field])
            self.assertEqual(state, before)

    def test_incomplete_invalid_or_whitespace_project_policy_is_rejected(self):
        for execution in ({"solver_backend": "python"}, {"solver_backend_selection_reason": "reason"},
                          {"solver_backend": "auto", "solver_backend_selection_reason": "reason"},
                          {"solver_backend": True, "solver_backend_selection_reason": "reason"},
                          {"solver_backend": [], "solver_backend_selection_reason": "reason"},
                          {"solver_backend": "python", "solver_backend_selection_reason": " \n\t"},
                          {"solver_backend": "python", "solver_backend_selection_reason": 3}):
            with self.subTest(execution=execution):
                result = inspect_backend_declarations({"execution": execution})
                self.assertEqual(result["kind"], "invalid")
                self.assertTrue(result["issues"])

    def test_current_policy_cannot_coexist_with_even_same_language_stage_selectors(self):
        for backend in ("python", "matlab"):
            state = policy()
            state["subproblems"]["Q2"] = {"solver_execution": {"primary": legacy(backend)}}
            result = inspect_backend_declarations(state)
            self.assertEqual(result["kind"], "invalid")
            self.assertTrue(any("coexist" in item for item in result["issues"]))

    def test_consistent_history_proposes_only_an_unverified_candidate(self):
        state = {"subproblems": {"Q1": {"solver_execution": {"primary": legacy()}},
                                 "Q2": {"solver_execution": {"primary": legacy(), "analysis": legacy()}}}}
        result = inspect_backend_declarations(state)
        self.assertEqual(result["kind"], "legacy_consistent")
        self.assertEqual(result["candidate_backend"], "python")
        self.assertIsNone(result["selected_backend"])
        self.assertTrue(all(not row["artifact_identity_verified"] for row in result["declarations"]))

    def test_mixed_questions_or_stages_never_vote_for_a_majority(self):
        states = (
            {"Q1": {"solver_execution": {"primary": legacy(), "analysis": legacy("matlab")}}},
            {"Q1": {"solver_execution": {"primary": legacy()}},
             "Q2": {"solver_execution": {"primary": legacy()}},
             "Q3": {"solver_execution": {"primary": legacy("matlab")}}},
        )
        for subproblems in states:
            result = inspect_backend_declarations({"subproblems": subproblems})
            self.assertEqual(result["kind"], "legacy_mixed")
            self.assertIsNone(result["candidate_backend"])

    def test_paths_or_bundle_only_history_are_not_backend_selection(self):
        for entry in ({"code": "问题一求解/问题一.py"}, {"solution_workbook": "old.xlsx"},
                      {"solver_execution": {"primary": {"bundle_sha256": "a"*64}}},
                      {"primary_execution_status": "accepted"}):
            result = inspect_backend_declarations({"subproblems": {"Q1": entry}})
            self.assertEqual(result["kind"], "legacy_unresolved")
            self.assertIsNone(result["candidate_backend"])

    def test_unknown_backend_of_another_numerical_question_prevents_uniform_candidate(self):
        state = {"subproblems": {"Q1": {"solver_execution": {"primary": legacy()}},
                                 "Q2": {"solution_workbook": "historical-result.xlsx"}}}
        result = inspect_backend_declarations(state)
        self.assertEqual(result["kind"], "legacy_unresolved")
        self.assertIsNone(result["candidate_backend"])

    def test_wrong_language_in_any_question_is_visible_but_figure_language_is_not_solver(self):
        state = policy()
        state["subproblems"]["Q1"] = {"code": "问题一求解/问题一.py", "matlab_script": "q1_plot.m"}
        self.assertFalse(inspect_backend_declarations(state)["issues"])
        state["subproblems"]["Q3"] = {"code": "问题三求解/q3_solver.m"}
        result = inspect_backend_declarations(state)
        self.assertTrue(any("Q3.primary" in issue for issue in result["issues"]))

    def test_request_conflict_does_not_change_the_existing_selection(self):
        state = policy()
        before = deepcopy(state)
        report = inspect_backend_declarations(state, requested_backend="matlab")
        self.assertTrue(report["request_conflict"])
        self.assertEqual(report["selected_backend"], "python")
        self.assertFalse(report["execution_authorized"])
        self.assertEqual(state, before)
        for request in (None, "auto", "python"):
            self.assertFalse(inspect_backend_declarations(state, requested_backend=request)["request_conflict"])

    def test_malformed_containers_unknown_stages_and_bundles_are_reported(self):
        cases = ({"execution": []}, {"subproblems": []}, {"subproblems": {"Q1": []}},
                 {"subproblems": {"Q1": {"solver_execution": []}}},
                 {"subproblems": {"Q1": {"solver_execution": {"extra": {}}}}},
                 {"subproblems": {"Q1": {"solver_execution": {"primary": None}}}},
                 {"subproblems": {"Q1": {"solver_execution": {"primary": {"allow_override": True}}}}},
                 {"subproblems": {"Q1": {"solver_execution": {"primary": {"validated_bundle_sha256": "a"*64}}}}},
                 {"subproblems": {"Q1": {"solver_execution": {"primary": {"bundle_sha256": "not-a-hash"}}}}})
        for state in cases:
            with self.subTest(state=state):
                self.assertEqual(inspect_backend_declarations(state)["kind"], "invalid")

    def test_unknown_request_and_nonmapping_state_raise_without_coercion(self):
        with self.assertRaises(ValueError):
            inspect_backend_declarations({}, requested_backend="julia")
        with self.assertRaises(ValueError):
            inspect_backend_declarations([])


class ProjectBackendInspectCLITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / STATE_RELATIVE_PATH
        self.path.parent.mkdir()
        self.path.write_text(yaml.safe_dump(policy()), encoding="utf-8")

    def tree(self):
        return {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.root.rglob("*") if p.is_file()}

    def command(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "scripts/project_solver_backend.py"), *args],
                              text=True, capture_output=True, timeout=20)

    def test_inspect_reads_exact_bytes_and_does_not_create_lock_or_state(self):
        before = self.tree()
        result = inspect_project(self.root, requested_backend="auto")
        self.assertEqual(result["state_snapshot"]["sha256"], before[STATE_RELATIVE_PATH])
        self.assertEqual(before, self.tree())
        missing = self.root / "missing"
        self.assertEqual(inspect_project(missing)["kind"], "unselected")
        self.assertFalse(missing.exists())

    def test_cli_request_conflict_returns_nonzero_and_preserves_all_files(self):
        before = self.tree()
        proc = self.command("inspect", "--project-root", str(self.root), "--requested-backend", "matlab")
        self.assertEqual(proc.returncode, 2)
        self.assertTrue(yaml.safe_load(proc.stdout)["request_conflict"])
        self.assertEqual(before, self.tree())

    def test_cli_recovery_required_preserves_journal_without_recovering(self):
        (self.root / JOURNAL_RELATIVE_PATH).write_text("status: prepared\n", encoding="utf-8")
        before = self.tree()
        proc = self.command("inspect", "--project-root", str(self.root))
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(yaml.safe_load(proc.stdout)["status"], "recovery_required")
        self.assertEqual(before, self.tree())

    def test_select_and_migrate_require_explicit_write_parameters(self):
        before = self.tree()
        for operation in ("select", "migrate"):
            self.assertEqual(self.command(operation, "--help").returncode, 0)
            proc = self.command(operation, "--project-root", str(self.root))
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("required", proc.stderr)
        self.assertEqual(before, self.tree())


if __name__ == "__main__":
    unittest.main()
