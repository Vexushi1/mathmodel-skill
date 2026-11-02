"""Project-level Figure backend identity regression (no solver/diagram changes)."""
from __future__ import annotations

import ast
from pathlib import Path
import sys
import tempfile
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from plot_backend import (PlotBackendError, inspect_plotting, resolve_question_script, select_project_plot_backend)
from project_transaction import GenerationConflictError


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


    def test_shared_python_preprocessing_figure_checks_actual_ast_not_comments(self):
        from sync_project import _preprocessing_artifact_issues

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / "数据预处理"
            folder.mkdir()
            source = folder / "data_process.py"
            state = {"preprocessing": {"decision": "project_level"}}
            required = {"preprocessing_python_plot_script"}
            source.write_text(
                '# 数据预处理结果.xlsx in a comment is not evidence of a workbook reference\n'
                'import matplotlib.pyplot as plt\n'
                'fig, ax = plt.subplots()\n'
                'ax.set_title("forbidden overall title")\n'
                'fig.savefig("not_yet_created.svg")\n',
                encoding="utf-8",
            )
            problems = _preprocessing_artifact_issues(root, required, state)
            self.assertTrue(any("title" in issue for issue in problems), problems)
            self.assertTrue(any("必须引用" in issue for issue in problems), problems)
            self.assertTrue(any("不存在" in issue for issue in problems), problems)

            source.write_text(
                'from openpyxl import load_workbook\n'
                'from pathlib import Path\n'
                'book = load_workbook(Path(__file__).parent / "数据预处理结果.xlsx", read_only=True)\n'
                '# ax.set_title("comment is not a title call")\n',
                encoding="utf-8",
            )
            self.assertEqual(_preprocessing_artifact_issues(root, required, state), [])

    def test_shared_python_preprocessing_export_cannot_escape_project(self):
        from sync_project import _preprocessing_artifact_issues

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            folder = root / "数据预处理"
            folder.mkdir(parents=True)
            source = folder / "data_process.py"
            source.write_text(
                'from openpyxl import load_workbook\n'
                'load_workbook("数据预处理结果.xlsx", read_only=True)\n'
                'fig.savefig("../../outside.svg")\n',
                encoding="utf-8",
            )
            problems = _preprocessing_artifact_issues(
                root, {"preprocessing_python_plot_script"},
                {"preprocessing": {"decision": "project_level"}},
            )
            self.assertTrue(any("越出项目根目录" in issue for issue in problems), problems)


    def test_python_figure_ast_detects_actual_recomputation_not_plotting(self):
        from project_snapshot import python_figure_forbidden_calls

        with tempfile.TemporaryDirectory() as temp:
            script = Path(temp) / "q1_plot.py"
            script.write_text(
                '# model.fit(X, y) is only a comment\\n'
                'note = "predict() appears in an annotation, not a call"\\n'
                'ax.plot(x, y)\\n'
                'np.asarray(x)\\n'
                'fig.savefig("q1.svg")\\n',
                encoding="utf-8",
            )
            self.assertEqual(python_figure_forbidden_calls(script), [])
            script.write_text(
                'model.fit(X, y)\\n'
                'clean = df.fillna(0)\\n'
                'wb.save("问题一求解结果.xlsx")\\n',
                encoding="utf-8",
            )
            self.assertEqual(
                python_figure_forbidden_calls(script),
                ["fillna", "fit", "workbook.save"],
            )

    def test_first_plot_choice_uses_existing_transaction(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "state" / "project_state.yaml"
            path.parent.mkdir(parents=True)
            state = yaml.safe_load((ROOT / "state" / "project_state.example.yaml").read_text(encoding="utf-8"))
            state["requirements"].update(total=1, completed=["Q1"], pending=[])
            path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False),
                            encoding="utf-8")
            before_questions = yaml.safe_dump(state["subproblems"], allow_unicode=True)
            result = select_project_plot_backend(root, backend="python",
                                                 reason="Full-project Figure needs",
                                                 expected_generation=0)
            current = yaml.safe_load(path.read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "committed")
            self.assertEqual(current["plotting"]["backend"], "python")
            self.assertEqual(current["project"]["state_generation"], 1)
            self.assertEqual(yaml.safe_dump(current["subproblems"], allow_unicode=True),
                             before_questions)
            before_bytes = path.read_bytes()
            repeated = select_project_plot_backend(root, backend="python",
                                                   reason="Full-project Figure needs",
                                                   expected_generation=1)
            self.assertEqual(repeated["status"], "unchanged")
            self.assertEqual(path.read_bytes(), before_bytes)
            with self.assertRaises(GenerationConflictError):
                select_project_plot_backend(root, backend="python",
                                            reason="Full-project Figure needs",
                                            expected_generation=0)
            with self.assertRaises(PlotBackendError):
                select_project_plot_backend(root, backend="matlab",
                                            reason="Opposite after first Figure choice",
                                            expected_generation=1)


if __name__ == "__main__":
    unittest.main()
