"""Project-level Figure backend identity regression (no solver/diagram changes)."""
from __future__ import annotations

import ast
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from plot_backend import (PlotBackendError, inspect_plotting, resolve_question_script)


class ProjectPlotBackendTests(unittest.TestCase):
    def test_legacy_matlab_is_still_current(self):
        state = {"subproblems": {"Q1": {"matlab_script": "问题一求解/q1_plot.m"}}}
        report = inspect_plotting(state)
        self.assertEqual(report["kind"], "historical_matlab")
        with tempfile.TemporaryDirectory() as temporary:
            ref = resolve_question_script(temporary, state, "Q1", "问题一", 1)
            self.assertEqual(ref.backend, "matlab")
            self.assertEqual(ref.hash_field, "matlab_script")
            self.assertEqual(ref.relative, "问题一求解/q1_plot.m")

    def test_plot_backend_not_inferred_from_solver(self):
        state = {"execution": {"solver_backend": "matlab"},
                 "plotting": {"backend": "python", "selection_reason": "whole-project Figure requirements"},
                 "subproblems": {"Q1": {"plot_script": "问题一求解/q1_plot.py"},
                                 "Q2": {"plot_script": "问题二求解/q2_plot.py"}}}
        self.assertEqual(inspect_plotting(state)["kind"], "selected")
        with tempfile.TemporaryDirectory() as temporary:
            ref = resolve_question_script(temporary, state, "Q2", "问题二", 2)
            self.assertEqual(ref.backend, "python")
            self.assertEqual(ref.hash_field, "plot_script")
            self.assertEqual(ref.relative, "问题二求解/q2_plot.py")

    def test_mixed_question_backends_are_rejected(self):
        state = {"plotting": {"backend": "python", "selection_reason": "Figure plan"},
                 "subproblems": {"Q1": {"plot_script": "问题一求解/q1_plot.py"},
                                 "Q2": {"matlab_script": "问题二求解/q2_plot.m"}}}
        self.assertEqual(inspect_plotting(state)["kind"], "conflict")
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(PlotBackendError):
                resolve_question_script(temporary, state, "Q1", "问题一", 1)

    def test_python_source_requires_explicit_project_selection(self):
        state = {"subproblems": {"Q1": {"plot_script": "问题一求解/q1_plot.py"}}}
        self.assertEqual(inspect_plotting(state)["kind"], "conflict")

    def test_unselected_project_stays_unselected(self):
        self.assertEqual(inspect_plotting({"subproblems": {"Q1": {}}})["kind"], "unselected")

    def test_wrong_registered_path_is_rejected(self):
        state = {"plotting": {"backend": "python", "selection_reason": "Figure plan"},
                 "subproblems": {"Q1": {"plot_script": "问题一求解/other.py"}}}
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(PlotBackendError):
                resolve_question_script(temporary, state, "Q1", "问题一", 1)

    def test_python_templates_are_valid_source_files(self):
        folder = ROOT / "templates" / "plot" / "python"
        for name in ("q1_plot.py", "data_process.py"):
            with self.subTest(name=name):
                ast.parse((folder / name).read_text(encoding="utf-8"), filename=name)


if __name__ == "__main__":
    unittest.main()
