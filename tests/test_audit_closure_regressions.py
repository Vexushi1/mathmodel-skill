"""AUD-01/03/04/05 regressions on actual repository entrypoints.

All numerical files below are explicitly synthetic test fixtures. These tests do
not execute a user model or infer mathematical validity from an artifact hash.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import analysis_prerequisites as prerequisites
import runtime_assurance as assurance
import validate_model_approval as approval
import validate_semantic_governance as governance
from resolve_runtime import resolve_runtime
from resolve_workflow import resolve_workflow
from tests.test_solver_backend_downstream_identity import project_fixture
from tests import test_v900_semantic_identity_binding as semantic_fixtures


def project_bytes(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


class CurrentInputQualificationTests(unittest.TestCase):
    def test_unchanged_primary_and_both_backends_are_current(self):
        for backend in ("python", "matlab"):
            with self.subTest(backend=backend), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                state = project_fixture(root, (backend,))
                self.assertEqual(prerequisites.primary_issues(root, state, state["subproblems"]["Q1"], require_project_policy=True), [])

    def test_unsynced_raw_input_change_or_deletion_is_rejected(self):
        for backend in ("python", "matlab"):
            for operation in ("change", "delete"):
                with self.subTest(backend=backend, operation=operation), tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    state = project_fixture(root, (backend,))
                    source = root / "input.json"
                    source.unlink() if operation == "delete" else source.write_text('{"coefficient":99}', encoding="utf-8")
                    before = project_bytes(root)
                    self.assertTrue(prerequisites.primary_issues(root, state, state["subproblems"]["Q1"], require_project_policy=True))
                    self.assertEqual(project_bytes(root), before)

    def test_runtime_does_not_promote_unsynced_changed_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_fixture(root, ("python",))
            self.assertIn("accepted_solution_workbook", assurance.hydrate_project_context(root)["verified_artifacts"])
            (root / "input.json").write_text("{}", encoding="utf-8")
            before = project_bytes(root)
            self.assertNotIn("accepted_solution_workbook", assurance.hydrate_project_context(root)["verified_artifacts"])
            self.assertEqual(project_bytes(root), before)

    def test_analysis_prerequisite_rejects_unsynced_changed_primary_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = project_fixture(root, ("python",), analysis=True)
            self.assertEqual(prerequisites.analysis_issues(root, state, state["subproblems"]["Q1"], require_project_policy=True), [])
            (root / "input.json").unlink()
            self.assertTrue(prerequisites.analysis_issues(root, state, state["subproblems"]["Q1"], require_project_policy=True))


class SemanticRevisionTypeTests(unittest.TestCase):
    def test_valid_revision_control(self):
        self.assertEqual(approval.validate_question("Q1", semantic_fixtures.structured_question()), [])

    def test_all_declared_revisions_reject_non_positive_integer_types(self):
        for field in ("semantic_revision", "approved_semantic_revision", "validated_semantic_revision"):
            for value in (True, False, 1.0, "1", 0, -1, None):
                with self.subTest(field=field, value=value):
                    entry = semantic_fixtures.structured_question()
                    entry[field] = value
                    self.assertTrue(approval.validate_question("Q1", entry))

    def test_boolean_approval_cli_fails_without_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = semantic_fixtures.structured_question()
            entry.update(semantic_revision=True, approved_semantic_revision=True)
            (root / "state").mkdir()
            state = root / "state/project_state.yaml"
            state.write_text(yaml.safe_dump({"subproblems": {"Q1": entry}}), encoding="utf-8")
            before = project_bytes(root)
            result = subprocess.run([sys.executable, str(ROOT / "scripts/validate_model_approval.py"), str(root), "--strict"], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertEqual(project_bytes(root), before)

    def test_governance_does_not_accept_boolean_or_float_revisions(self):
        for field in ("semantic_revision", "approved_semantic_revision", "validated_semantic_revision"):
            with self.subTest(field=field):
                entry = semantic_fixtures.structured_question()
                entry[field] = True
                self.assertTrue(governance._gate_issues("Q1", entry))

    def test_runtime_does_not_verify_invalid_revision_lock(self):
        for field in ("semantic_revision", "approved_semantic_revision", "validated_semantic_revision"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                entry = semantic_fixtures.structured_question()
                entry[field] = True
                semantic_fixtures.write_project(root, state_question=entry,
                    framework_text=semantic_fixtures.framework(semantic_fixtures.identity()))
                result = assurance.hydrate_project_context(root)
                self.assertNotIn("locked_model_spec", result["verified_artifacts"])


class AssuredEntryAndDelegationTests(unittest.TestCase):
    def test_omitted_numerical_backend_is_auto_not_python_projection(self):
        args = dict(primary="mechanism", competition="CUMCM")
        omitted = resolve_runtime("full_solution", **args)
        explicit = resolve_runtime("full_solution", solver_backend="auto", **args)
        self.assertIn("solver_backend", omitted)
        self.assertEqual(omitted["solver_backend"], explicit["solver_backend"])
        self.assertIsNone(omitted["solver_backend"]["resolved"])
        self.assertFalse(omitted["solver_backend"]["selection_complete"])
        self.assertEqual(omitted["terminal_outputs"], explicit["terminal_outputs"])

    def test_legacy_resolver_projection_is_retained(self):
        plan = resolve_workflow("code_and_solution", primary="mechanism",
                                available_artifacts=["locked_model_spec"], preprocessing_decision="not_needed")
        self.assertNotIn("solver_backend", plan)
        self.assertIn("python_code", plan["terminal_outputs"])

    def test_pure_non_numerical_route_does_not_force_backend_templates(self):
        plan = resolve_runtime("latex", competition="CUMCM")
        self.assertFalse(any(path.startswith("templates/code/") for path in plan["templates"]))

    def test_scripts_navigation_delegates_prose_to_protocol(self):
        text = (ROOT / "scripts/README.md").read_text(encoding="utf-8")
        self.assertNotIn("正文结构与表达由 `modules/05_writing/latex.md` 管理", text)
        self.assertIn("正文结构与表达由 `modules/05_writing/paper_writing_protocol.md` 管理", text)


if __name__ == "__main__":
    unittest.main()
