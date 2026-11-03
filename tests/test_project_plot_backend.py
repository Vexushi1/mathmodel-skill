"""Project-level Figure backend identity regression (no solver/diagram changes)."""
from __future__ import annotations

import ast
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from plot_backend import (PlotBackendError, inspect_plotting, resolve_question_script, select_project_plot_backend, preview_project_plot_backend_migration)
from project_transaction import GenerationConflictError, ReadSetConflictError, JOURNAL_RELATIVE_PATH


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

    def test_legacy_result_directory_matlab_is_not_lost_by_resolver(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            legacy = root / "结果数据表/问题一/q1_plot.m"
            legacy.parent.mkdir(parents=True)
            legacy.write_text('readcell("问题一求解结果.xlsx");\n', encoding="utf-8")
            state = {"subproblems": {"Q1": {}}}
            ref = resolve_question_script(root, state, "Q1", "问题一", 1)
            self.assertEqual(ref.relative, "结果数据表/问题一/q1_plot.m")
            self.assertEqual(ref.hash_field, "matlab_script")
            state["subproblems"]["Q1"]["matlab_script"] = ref.relative
            self.assertEqual(resolve_question_script(root, state, "Q1", "问题一", 1).relative, ref.relative)
            # A modern explicitly registered source must not be silently replaced.
            state["subproblems"]["Q1"]["matlab_script"] = "问题一求解/q1_plot.m"
            self.assertEqual(resolve_question_script(root, state, "Q1", "问题一", 1).relative,
                             "问题一求解/q1_plot.m")

    def test_output_contract_selected_figure_roles_all_solver_combinations(self):
        # Legacy YAML role names are projected at the actual scope consumer.
        # All four solver x Figure combinations must select exactly one renderer.
        from sync_project import stage_requirements

        output = yaml.safe_load((ROOT / "core/output_contract.yaml").read_text(encoding="utf-8"))
        projection = output["project_sync"]["plotting_backend_contract"]
        self.assertEqual(projection["stage_role_projection"], "scripts/sync_project.py#stage_requirements")
        self.assertEqual(projection["active_script_resolution"], "scripts/plot_backend.py#resolve_question_script")
        for solver in ("python", "matlab"):
            for plot in ("python", "matlab"):
                with self.subTest(solver=solver, plot=plot):
                    state = {
                        "execution": {"solver_backend": solver},
                        "plotting": {"backend": plot, "selection_reason": "whole-project Figure plan"},
                        "preprocessing": {"decision": "project_level"},
                        "subproblems": {"Q1": {}},
                    }
                    expected = "preprocessing_python_plot_script" if plot == "python" else "preprocessing_matlab_script"
                    excluded = "preprocessing_matlab_script" if plot == "python" else "preprocessing_python_plot_script"
                    for scope in ("figures", "docx", "latex", "submission"):
                        roles = stage_requirements(scope, output, state)
                        self.assertIn(expected, roles, (scope, solver, plot))
                        self.assertNotIn(excluded, roles, (scope, solver, plot))
                        if scope == "figures":
                            self.assertIn("plot_scripts" if plot == "python" else "matlab_scripts", roles)
                            self.assertNotIn("matlab_scripts" if plot == "python" else "plot_scripts", roles)
                    state["preprocessing"]["decision"] = "not_needed"
                    for scope in ("figures", "docx", "latex", "submission"):
                        roles = stage_requirements(scope, output, state)
                        self.assertNotIn("preprocessing_matlab_script", roles)
                        self.assertNotIn("preprocessing_python_plot_script", roles)

        historical = {
            "preprocessing": {"decision": "project_level"},
            "subproblems": {"Q1": {"matlab_script": "问题一求解/q1_plot.m"}},
        }
        self.assertIn("matlab_scripts", stage_requirements("figures", output, historical))
        self.assertIn("preprocessing_matlab_script",
                      stage_requirements("figures", output, historical))

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

    def test_submission_python_figure_source_must_be_canonical_and_validated(self):
        # Package collection is not Figure approval, but it must not accept an
        # arbitrary Python file or a changed source under an old Figure hash.
        import hashlib
        from submission_requirements import reproducibility_requirements

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / "问题一求解"
            directory.mkdir()
            script = directory / "q1_plot.py"
            script.write_text("print('Figure only')\n", encoding="utf-8")
            relative = "问题一求解/q1_plot.py"
            digest = hashlib.sha256(script.read_bytes()).hexdigest()
            state = {
                "plotting": {"backend": "python", "selection_reason": "whole-project Figure"},
                "execution": {"solver_backend": "python"},
                "preprocessing": {"decision": "not_needed"},
                "paper_framework": {"path": "模型论文框架.md"},
                "artifacts": {},
                "subproblems": {
                    "Q1": {
                        "plot_script": relative,
                        "validated_artifact_hashes": {"plot_script": digest},
                    },
                },
            }
            observed = []
            required, issues = reproducibility_requirements(
                root, state, observe=lambda path, raw: observed.append(path.resolve())
            )
            self.assertIn(relative, required)
            self.assertIn(script.resolve(), observed)
            self.assertFalse([issue for issue in issues if "plot_script" in issue], issues)

            script.write_text("print('Changed Figure')\n", encoding="utf-8")
            _, issues = reproducibility_requirements(root, state)
            self.assertTrue(any("plot_script" in issue and "SHA-256" in issue for issue in issues), issues)
            script.write_text("print('Figure only')\n", encoding="utf-8")

            del state["subproblems"]["Q1"]["validated_artifact_hashes"]["plot_script"]
            _, issues = reproducibility_requirements(root, state)
            self.assertTrue(any("plot_script" in issue and "缺少已验收" in issue for issue in issues), issues)
            state["subproblems"]["Q1"]["validated_artifact_hashes"]["plot_script"] = digest

            state["subproblems"]["Q1"]["plot_script"] = "问题一求解/other.py"
            (directory / "other.py").write_text("print('Unrelated')\n", encoding="utf-8")
            _, issues = reproducibility_requirements(root, state)
            self.assertTrue(any("plot_script" in issue and "当前身份不合法" in issue for issue in issues), issues)
            state["subproblems"]["Q1"]["plot_script"] = relative

            script.unlink()
            _, issues = reproducibility_requirements(root, state)
            self.assertTrue(any("plot_script" in issue and "不存在" in issue for issue in issues), issues)

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

    def test_python_declared_export_alias_is_verified_without_evaluating_code(self):
        from project_snapshot import _parse_python_plot
        from sync_project import _preprocessing_artifact_issues

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / "数据预处理"
            folder.mkdir()
            source = folder / "data_process.py"
            source.write_text(
                'from pathlib import Path\n'
                'from openpyxl import load_workbook\n'
                'EXPORT_FILE = "data_process_evidence.svg"\n'
                'directory = Path(__file__).resolve().parent\n'
                'out = (directory / EXPORT_FILE).resolve()\n'
                'load_workbook("数据预处理结果.xlsx", read_only=True)\n'
                'if EXPORT_FILE:\n'
                '    fig.savefig(out)\n',
                encoding="utf-8",
            )
            title, refs, exports = _parse_python_plot(source)
            self.assertFalse(title)
            self.assertIn("数据预处理结果.xlsx", refs)
            self.assertEqual(exports, ["data_process_evidence.svg"])
            required = {"preprocessing_python_plot_script"}
            state = {"preprocessing": {"decision": "project_level"}}
            missing = _preprocessing_artifact_issues(root, required, state)
            self.assertTrue(any("声明导出的图不存在" in issue for issue in missing), missing)
            (folder / "data_process_evidence.svg").write_text("<svg/>", encoding="utf-8")
            self.assertFalse(any("声明导出的图不存在" in issue
                                 for issue in _preprocessing_artifact_issues(root, required, state)))

            source.write_text(
                'EXPORT_FILE = None\n'
                'directory = Path(__file__).parent\n'
                'out = (directory / EXPORT_FILE).resolve()\n'
                'fig.savefig(out)\n',
                encoding="utf-8",
            )
            self.assertEqual(_parse_python_plot(source)[2], [])

            source.write_text(
                'EXPORT_FILE = "unused.svg"\n'
                'fig.savefig("actual.svg")\n'
                'fig.savefig(fname="keyword.svg")\n',
                encoding="utf-8",
            )
            self.assertEqual(_parse_python_plot(source)[2], ["actual.svg", "keyword.svg"])

    def test_question_python_declared_export_path_is_detected(self):
        from project_snapshot import _parse_python_plot

        with tempfile.TemporaryDirectory() as temp:
            script = Path(temp) / "q1_plot.py"
            script.write_text(
                'from pathlib import Path\n'
                'EXPORT_FILE = "q1_result.pdf"\n'
                'result_dir = Path(__file__).resolve().parent\n'
                'out = (result_dir / EXPORT_FILE).resolve()\n'
                'if EXPORT_FILE:\n'
                '    fig.savefig(out, bbox_inches="tight")\n',
                encoding="utf-8",
            )
            self.assertEqual(_parse_python_plot(script)[2], ["q1_result.pdf"])

    def test_question_python_export_cannot_escape_registered_question_directory(self):
        from project_snapshot import _snapshot_question

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / "问题一求解"
            folder.mkdir()
            script = folder / "q1_plot.py"
            script.write_text(
                'from pathlib import Path\n'
                'EXPORT_FILE = "../unrelated.svg"\n'
                'result_dir = Path(__file__).resolve().parent\n'
                'out = (result_dir / EXPORT_FILE).resolve()\n'
                'load_workbook("问题一求解结果.xlsx")\n'
                'fig.savefig(out)\n',
                encoding="utf-8",
            )
            # Even a real file outside this question must not be treated as
            # an approved output of its current Figure source.
            (root / "unrelated.svg").write_text("<svg/>", encoding="utf-8")
            state = {
                "plotting": {"backend": "python", "selection_reason": "whole-project Figure"},
                "subproblems": {"Q1": {}},
            }
            snapshot = _snapshot_question(
                root, "问题一", {}, {}, None, "figures",
                state=state, project_backend="python",
            )
            self.assertTrue(
                any("越出当前问题目录" in issue for issue in snapshot["issues"]),
                snapshot["issues"],
            )

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


    def test_shared_python_preprocessing_rejects_actual_imputation(self):
        from sync_project import _preprocessing_artifact_issues

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / "数据预处理"
            folder.mkdir()
            (folder / "data_process.py").write_text(
                'from openpyxl import load_workbook\n'
                'book = load_workbook("数据预处理结果.xlsx", read_only=True)\n'
                'cleaned = df.fillna(0)\n',
                encoding="utf-8",
            )
            issues = _preprocessing_artifact_issues(
                root, {"preprocessing_python_plot_script"},
                {"preprocessing": {"decision": "project_level"}},
            )
            self.assertTrue(any("fillna" in issue for issue in issues), issues)

    def test_python_figure_ast_detects_actual_recomputation_not_plotting(self):
        from project_snapshot import python_figure_forbidden_calls

        with tempfile.TemporaryDirectory() as temp:
            script = Path(temp) / "q1_plot.py"
            script.write_text(
                '# model.fit(X, y) is only a comment\n'
                'note = "predict() appears in an annotation, not a call"\n'
                'ax.plot(x, y)\n'
                'np.asarray(x)\n'
                'fig.savefig("q1.svg")\n',
                encoding="utf-8",
            )
            self.assertEqual(python_figure_forbidden_calls(script), [])
            script.write_text(
                'model.fit(X, y)\n'
                'clean = df.fillna(0)\n'
                'wb.save("问题一求解结果.xlsx")\n',
                encoding="utf-8",
            )
            self.assertEqual(
                python_figure_forbidden_calls(script),
                ["fillna", "fit", "workbook.save"],
            )

    @staticmethod
    def selection_fixture(root: Path):
        path = root / "state" / "project_state.yaml"
        path.parent.mkdir(parents=True)
        state = yaml.safe_load(
            (ROOT / "state" / "project_state.example.yaml").read_text(encoding="utf-8")
        )
        state["requirements"].update(total=1, completed=["Q1"], pending=[])
        path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False),
                        encoding="utf-8")
        framework_path = root / "模型论文框架.md"
        framework = (ROOT / "templates/model/model_paper_framework.md").read_text(encoding="utf-8")
        framework = framework.replace("### Q1：__QUESTION_NAME__", "### Q1：填写问题名称")
        framework = "\n".join(line for line in framework.splitlines()
                              if not line.startswith(("| T1 |", "| N1 |", "| TC1 |",
                                                      "| paper.abstract.q1 |"))) + "\n"
        framework_path.write_text(framework, encoding="utf-8")
        return path, framework_path, state

    def test_first_plot_choice_uses_existing_atomic_state_framework_transaction(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path, framework_path, state = self.selection_fixture(root)
            before_questions = yaml.safe_dump(state["subproblems"], allow_unicode=True)
            before_framework = framework_path.read_text(encoding="utf-8")
            result = select_project_plot_backend(
                root, backend="python", reason="Full-project Figure needs",
                expected_generation=0,
            )
            current = yaml.safe_load(path.read_text(encoding="utf-8"))
            updated_framework = framework_path.read_text(encoding="utf-8")
            self.assertEqual(result["status"], "committed")
            self.assertEqual(result["framework_path"], "模型论文框架.md")
            self.assertEqual(current["plotting"]["backend"], "python")
            self.assertEqual(current["project"]["state_generation"], 1)
            self.assertEqual(yaml.safe_dump(current["subproblems"], allow_unicode=True),
                             before_questions)
            self.assertEqual(current["subproblems"]["Q1"]["human_model_approval_status"],
                             state["subproblems"]["Q1"]["human_model_approval_status"])
            self.assertIn("### 全项目科研绘图", updated_framework)
            self.assertIn("- 项目绘图后端：", updated_framework)
            self.assertIn("Full-project Figure needs", updated_framework)
            self.assertIn("## 图表证据链", updated_framework)
            self.assertIn("## 图表证据链", before_framework)
            import validate_project_state as STATE
            import validate_model_paper_framework as FRAMEWORK
            self.assertEqual(STATE.validate_state_payload(current, project_root=root), [])
            self.assertEqual(FRAMEWORK.validate_framework_text(
                updated_framework, state=current, project_root=root), [])
            self.assertEqual(current["paper_framework"]["sha256"],
                             FRAMEWORK.sha256_text(updated_framework))
            self.assertFalse((root / JOURNAL_RELATIVE_PATH).exists())

            before_bytes = path.read_bytes(), framework_path.read_bytes()
            repeated = select_project_plot_backend(
                root, backend="python", reason="Full-project Figure needs",
                expected_generation=1,
            )
            self.assertEqual(repeated["status"], "unchanged")
            self.assertEqual((path.read_bytes(), framework_path.read_bytes()), before_bytes)
            with self.assertRaises(GenerationConflictError):
                select_project_plot_backend(
                    root, backend="python", reason="Full-project Figure needs",
                    expected_generation=0,
                )
            with self.assertRaises(PlotBackendError):
                select_project_plot_backend(
                    root, backend="matlab", reason="Opposite after first Figure choice",
                    expected_generation=1,
                )
            self.assertEqual((path.read_bytes(), framework_path.read_bytes()), before_bytes)

    def test_figure_choice_rejects_missing_or_drifted_framework_without_state_write(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path, framework_path, state = self.selection_fixture(root)
            original = path.read_bytes()
            framework_path.unlink()
            with self.assertRaisesRegex(PlotBackendError, "framework is missing"):
                select_project_plot_backend(root, backend="python", reason="Whole project",
                                            expected_generation=0)
            self.assertEqual(path.read_bytes(), original)
            framework_path.write_text("invalid", encoding="utf-8")
            state["paper_framework"]["sha256"] = "0" * 64
            path.write_text(yaml.safe_dump(state, allow_unicode=True), encoding="utf-8")
            with self.assertRaisesRegex(PlotBackendError, "current project state/framework"):
                select_project_plot_backend(root, backend="python", reason="Whole project",
                                            expected_generation=0)

    def test_figure_selection_framework_read_set_conflict_preserves_third_party_edit(self):
        import sync_project as SYNC
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path, framework_path, _ = self.selection_fixture(root)
            before = path.read_bytes()
            render = SYNC.render_project_plot_backend_memory

            def concurrent_edit(text, state):
                result = render(text, state)
                framework_path.write_text(text + "\nthird-party change\n", encoding="utf-8")
                return result

            with mock.patch.object(SYNC, "render_project_plot_backend_memory",
                                   side_effect=concurrent_edit):
                with self.assertRaises(ReadSetConflictError):
                    select_project_plot_backend(root, backend="python",
                                                reason="Whole project", expected_generation=0)
            self.assertEqual(path.read_bytes(), before)
            self.assertIn("third-party change", framework_path.read_text(encoding="utf-8"))
            self.assertFalse((root / JOURNAL_RELATIVE_PATH).exists())

    def test_figure_selection_invalid_staged_framework_rolls_back_both_files(self):
        import sync_project as SYNC
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path, framework_path, _ = self.selection_fixture(root)
            before = path.read_bytes(), framework_path.read_bytes()
            render = SYNC.render_project_plot_backend_memory

            def invalid_render(text, state):
                return render(text, state).replace(
                    "## 当前有效口径", "## broken current-state heading"
                )

            with mock.patch.object(SYNC, "render_project_plot_backend_memory",
                                   side_effect=invalid_render):
                with self.assertRaisesRegex(PlotBackendError, "Candidate project Figure selection"):
                    select_project_plot_backend(root, backend="python",
                                                reason="Whole project", expected_generation=0)
            self.assertEqual((path.read_bytes(), framework_path.read_bytes()), before)
            self.assertFalse((root / JOURNAL_RELATIVE_PATH).exists())

    def test_plot_framework_projection_is_idempotent_and_rejects_duplicate_memory(self):
        import sync_project as SYNC
        state = {"plotting": {"backend": "matlab", "selection_reason": "Unified plots"},
                 "subproblems": {"Q1": {}}}
        original = "## 当前有效口径\n\n### 全项目数值实现\n\n- 项目求解后端：`python`\n\n### 题目对象与核心关系\n\n## 各问模型与结果\n"
        rendered = SYNC.render_project_plot_backend_memory(original, state)
        self.assertEqual(SYNC.render_project_plot_backend_memory(rendered, state), rendered)
        self.assertIn("- 项目求解后端：`python`", rendered)
        self.assertIn("- 项目绘图后端：`matlab`", rendered)
        with self.assertRaisesRegex(ValueError, "outside"):
            SYNC.render_project_plot_backend_memory(
                original + "- 项目绘图后端：`python`\n", state
            )
        with self.assertRaisesRegex(ValueError, "duplicate"):
            SYNC.render_project_plot_backend_memory(
                rendered.replace("- 项目绘图后端：`matlab`",
                                 "- 项目绘图后端：`matlab`\n- 项目绘图后端：`matlab`"),
                state,
            )


    def test_read_only_migration_preview_lists_entire_figure_and_paper_impact(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_path, framework_path, _ = self.selection_fixture(root)
            select_project_plot_backend(root, backend="python",
                                        reason="Whole project Figure", expected_generation=0)
            current = yaml.safe_load(state_path.read_text(encoding="utf-8"))
            figure = root / "问题一求解" / "q1.svg"
            figure.parent.mkdir()
            figure.write_text("<svg/>", encoding="utf-8")
            script = figure.parent / "q1_plot.py"
            script.write_text("print('Figure only')\n", encoding="utf-8")
            current["subproblems"]["Q1"]["plot_script"] = "问题一求解/q1_plot.py"
            current["subproblems"]["Q1"]["solution_workbook"] = "问题一求解/问题一求解结果.xlsx"
            current["artifacts"]["approved_figures"] = ["问题一求解/q1.svg"]
            current["artifacts"]["papers"] = ["论文.pdf"]
            (root / "论文.pdf").write_bytes(b"synthetic paper placeholder")
            current["preprocessing"]["decision"] = "project_level"
            shared = root / "数据预处理" / "data_process.py"
            shared.parent.mkdir()
            shared.write_text("# shared Figure\n", encoding="utf-8")
            state_path.write_text(yaml.safe_dump(current, allow_unicode=True), encoding="utf-8")
            before = state_path.read_bytes(), framework_path.read_bytes()
            report = preview_project_plot_backend_migration(root, target_backend="matlab")
            self.assertEqual(report["status"], "preview_only")
            self.assertEqual(report["current_backend"], "python")
            self.assertEqual(report["target_backend"], "matlab")
            self.assertEqual(report["question_scripts"][0]["current"], "问题一求解/q1_plot.py")
            self.assertEqual(report["question_scripts"][0]["target"], "问题一求解/q1_plot.m")
            self.assertTrue(report["question_scripts"][0]["current_exists"])
            self.assertEqual(report["shared_preprocessing_figure"]["target"],
                             "数据预处理/data_process.m")
            self.assertTrue(report["shared_preprocessing_figure"]["current_exists"])
            self.assertEqual(report["approved_figures_to_revalidate"][0]["path"],
                             "问题一求解/q1.svg")
            self.assertTrue(any(row["path"] == "模型论文框架.md"
                                for row in report["paper_dependencies_to_review"]))
            self.assertTrue(any(row["path"] == "论文.pdf"
                                for row in report["paper_dependencies_to_review"]))
            self.assertIn("问题一求解/问题一求解结果.xlsx",
                          report["numerical_workbooks_to_preserve"])
            self.assertFalse(report["execution_authorized"])
            self.assertFalse(report["accepted_numerical_results_changed"])
            self.assertEqual((state_path.read_bytes(), framework_path.read_bytes()), before)
            self.assertEqual(preview_project_plot_backend_migration(
                root, target_backend="python")["status"], "unchanged")

    def test_migration_preview_requires_active_nonconflicting_backend(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_path, _, state = self.selection_fixture(root)
            with self.assertRaisesRegex(PlotBackendError, "No active"):
                preview_project_plot_backend_migration(root, target_backend="python")
            state["plotting"] = {"backend": "python", "selection_reason": "whole project"}
            state["subproblems"]["Q1"]["matlab_script"] = "问题一求解/q1_plot.m"
            state_path.write_text(yaml.safe_dump(state, allow_unicode=True), encoding="utf-8")
            with self.assertRaisesRegex(PlotBackendError, "conflicts"):
                preview_project_plot_backend_migration(root, target_backend="matlab")


if __name__ == "__main__":
    unittest.main()
