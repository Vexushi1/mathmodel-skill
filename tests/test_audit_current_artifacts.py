from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

import yaml

from tests.test_sync_project import ROOT, load_syncer, setup_project

SYNC = load_syncer()
SPEC = importlib.util.spec_from_file_location("audit_reading_plan", ROOT / "scripts/reading_plan.py")
READING = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(READING)


def write_state(root, state):
    (root / "state/project_state.yaml").write_text(yaml.safe_dump(state, allow_unicode=True), encoding="utf-8")


def figure_table(rows):
    text = "| 图号 | 绘图程序 | 导出文件 |\n|---|---|---|\n"
    return text + "".join(f"| {identifier} | {script} | {output} |\n" for identifier, script, output in rows)


def make_current_project(root, *, root_figure=False):
    folder = setup_project(root, status="validated", phase="writing_docx")
    script = folder / "q1_plot.m"
    script.write_text('readcell("问题一求解结果.xlsx");\n', encoding="utf-8")
    figure = (root / "figures/当前图.pdf") if root_figure else (folder / "当前图.pdf")
    figure.parent.mkdir(exist_ok=True)
    figure.write_bytes(b"%PDF synthetic figure v1")
    framework = root / "模型论文框架.md"
    if root_figure:
        framework.write_text(framework.read_text(encoding="utf-8").replace(
            "## 图表证据链\n", "## 图表证据链\n" + figure_table([
                ("F1", "问题一求解/q1_plot.m", "figures/当前图.pdf")
            ])
        ), encoding="utf-8")
    (root / "paper.docx").write_bytes(b"synthetic existence fixture")
    (root / "input.csv").write_text("x,y\n1,2\n", encoding="utf-8")
    state = yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8"))
    state["data"] = {"sources": [{"name": "fixture", "path": "input.csv", "role": "input"}]}
    state["artifacts"].update(approved_figures=[figure.relative_to(root).as_posix()], docx=["paper.docx"])
    entry = state["subproblems"]["Q1"]
    entry.update(solution_workbook="问题一求解/问题一求解结果.xlsx",
                 result_analysis_workbook="问题一求解/问题一结果深化分析.xlsx",
                 matlab_script="问题一求解/q1_plot.m")
    write_state(root, state)
    snapshot = SYNC.synchronize(root, delivery_scope="docx")["questions"]["Q1"]
    entry["artifact_hashes"] = deepcopy(snapshot["artifact_hashes"])
    entry["validated_artifact_hashes"] = deepcopy(snapshot["artifact_hashes"])
    state["paper_framework"]["sha256"] = SYNC.sha256_text(framework.read_text(encoding="utf-8"))
    write_state(root, state)
    return state, figure


class CurrentArtifactTests(unittest.TestCase):
    def test_first_source_change_fails_same_formal_check_in_read_and_write_modes(self):
        reports = []
        for write in (False, True):
            with self.subTest(write=write), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                state, _ = make_current_project(root)
                self.assertEqual(SYNC.synchronize(root, strict=True, delivery_scope="docx")["status"], "passed")
                (root / "问题一求解/问题一求解.py").write_text("# changed\n", encoding="utf-8")
                before = (root / "state/project_state.yaml").read_bytes()
                report = SYNC.synchronize(root, write=write, strict=True, delivery_scope="docx")
                reports.append((report["status"], report["issues"], report["stale_questions"]))
                self.assertEqual(report["status"], "failed")
                self.assertIn("Q1", report["stale_questions"])
                if not write:
                    self.assertEqual((root / "state/project_state.yaml").read_bytes(), before)
                else:
                    saved = yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8"))
                    self.assertTrue(saved["subproblems"]["Q1"]["artifacts_stale"])
                    self.assertEqual(saved["subproblems"]["Q1"]["validated_artifact_hashes"],
                                     state["subproblems"]["Q1"]["validated_artifact_hashes"])
        self.assertEqual(reports[0], reports[1])

    def test_root_figure_mapping_is_hashed_and_changes_invalidate_without_reapproval(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state, figure = make_current_project(root, root_figure=True)
            baseline = SYNC.synchronize(root, delivery_scope="docx")
            snapshot = baseline["questions"]["Q1"]
            self.assertEqual(baseline["status"], "passed", baseline["issues"])
            self.assertEqual(snapshot["figures"], ["figures/当前图.pdf"])
            self.assertEqual(READING._figure_binding(root, state, "Q1"), [])
            figure.write_bytes(b"%PDF synthetic figure v2")
            changed = SYNC.synchronize(root, delivery_scope="docx")
            self.assertEqual(changed["status"], "failed")
            self.assertIn("Q1", changed["stale_questions"])
            self.assertTrue(READING._figure_binding(root, state, "Q1"))
            self.assertEqual(yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8")), state)

    def test_approved_root_figure_without_mapping_is_diagnosed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state, figure = make_current_project(root)
            target = root / "figures/q1.pdf"
            target.parent.mkdir()
            figure.rename(target)
            state["artifacts"]["approved_figures"] = ["figures/q1.pdf"]
            write_state(root, state)
            report = SYNC.synchronize(root, delivery_scope="docx")
            self.assertTrue(any("映射" in item for item in report["warnings"]), report["warnings"])

    def test_scoped_discovery_shared_files_deduplicates_and_does_not_guess_names(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "figures").mkdir()
            for name in ("shared.pdf", "same.pdf", "q1_unregistered.pdf"):
                (root / "figures" / name).write_bytes(name.encode())
            scripts = []
            for number in (1, 2):
                folder = root / f"question{number}"
                folder.mkdir()
                script = folder / "plot.m"
                script.write_text("% fixture\n")
                scripts.append(script)
            (root / "模型论文框架.md").write_text("## 图表证据链\n" + figure_table([
                ("shared", "question1/plot.m; question2/plot.m", "figures/shared.pdf"),
                ("one", "question1/plot.m", "figures/same.pdf; figures/shared.pdf"),
            ]), encoding="utf-8")
            first, issues = SYNC.PROJECT_SNAPSHOT.scoped_figure_files(root, scripts[0])
            second, second_issues = SYNC.PROJECT_SNAPSHOT.scoped_figure_files(root, scripts[1])
            self.assertEqual(issues + second_issues, [])
            self.assertEqual({p.name for p in first}, {"same.pdf", "shared.pdf"})
            self.assertEqual([p.name for p in second], ["shared.pdf"])

    def test_declared_export_deletion_and_escape_are_diagnosed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state, figure = make_current_project(root, root_figure=True)
            figure.unlink()
            report = SYNC.synchronize(root, delivery_scope="docx")
            self.assertEqual(report["status"], "failed")
            self.assertIn("Q1", report["stale_questions"])
            framework = root / "模型论文框架.md"
            framework.write_text("## 图表证据链\n" + figure_table([
                ("F1", "问题一求解/q1_plot.m", "../outside.pdf")
            ]), encoding="utf-8")
            _, issues = SYNC.PROJECT_SNAPSHOT.scoped_figure_files(root, root / "问题一求解/q1_plot.m")
            self.assertTrue(any("越出" in item for item in issues))

    def test_independent_global_figure_is_reported_without_blocking_question_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state, _ = make_current_project(root)
            global_figure = root / "独立机理图.svg"
            global_figure.write_text("<svg/>", encoding="utf-8")
            state["artifacts"]["approved_figures"].append(global_figure.name)
            write_state(root, state)
            report = SYNC.synchronize(root, delivery_scope="docx")
            self.assertEqual(report["status"], "passed", report["issues"])
            self.assertTrue(any(global_figure.name in item for item in report["warnings"]))
            self.assertNotIn(global_figure.name, report["questions"]["Q1"]["figures"])

    def test_newly_discovered_approved_bundle_requires_existing_manual_binding(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state, _ = make_current_project(root, root_figure=True)
            state["subproblems"]["Q1"]["validated_artifact_hashes"].pop("figure_bundle")
            write_state(root, state)
            report = SYNC.synchronize(root, write=True, delivery_scope="docx")
            self.assertTrue(any("需人工复核绑定" in issue for issue in report["issues"]))
            saved = yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8"))
            self.assertNotIn("figure_bundle", saved["subproblems"]["Q1"]["validated_artifact_hashes"])
            self.assertEqual(saved["artifacts"]["approved_figures"], state["artifacts"]["approved_figures"])

    def test_literal_exports_and_exact_figure_id_support_non_matlab_carriers(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / "问题一求解"
            folder.mkdir()
            (root / "figures").mkdir()
            script = folder / "q1_plot.m"
            script.write_text("exportgraphics(gcf, '../figures/line.pdf');\n", encoding="utf-8")
            (root / "figures/line.pdf").write_bytes(b"line")
            (root / "figures/mechanism.svg").write_bytes(b"mechanism")
            (root / "模型论文框架.md").write_text(
                "### Q1\n| Figure ID | MATLAB 脚本 |\n|---|---|\n| mechanism | |\n"
                "## 图表证据链\n" + figure_table([
                    ("mechanism", "figures/mechanism.drawio", "figures/mechanism.svg")
                ]), encoding="utf-8")
            figures, issues = SYNC.PROJECT_SNAPSHOT.scoped_figure_files(root, script, {"framework_section": "### Q1"})
            self.assertEqual(issues, [])
            self.assertEqual({path.name for path in figures}, {"line.pdf", "mechanism.svg"})

    def test_same_filename_in_other_directory_and_unrelated_picture_do_not_change_bundle(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state, figure = make_current_project(root, root_figure=True)
            (root / "unrelated").mkdir()
            other = root / "unrelated" / figure.name
            other.write_bytes(b"different unrelated figure")
            report = SYNC.synchronize(root, delivery_scope="docx")
            self.assertEqual(report["status"], "passed", report["issues"])
            self.assertEqual(report["stale_questions"], [])
            self.assertEqual(report["questions"]["Q1"]["individual_figure_hashes"],
                             {"figures/当前图.pdf": SYNC.sha256_file(figure)})

    def test_invalid_current_mapping_warns_in_discovery_but_blocks_formal_figure_scope(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state, figure = make_current_project(root, root_figure=True)
            figure.unlink()
            ordinary = SYNC.synchronize(root)
            formal = SYNC.synchronize(root, delivery_scope="figures")
            diagnostic = "图表映射声明的文件不存在"
            self.assertTrue(any(diagnostic in message for message in ordinary["warnings"]))
            self.assertFalse(any(diagnostic in message for message in ordinary["issues"]))
            self.assertTrue(any(diagnostic in message for message in formal["issues"]))

    def test_read_only_sync_propagates_fragment_stale_without_writing_it(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state, figure = make_current_project(root)
            state["paper_framework"]["paper_fragments"] = [
                {"id": "result", "scope": "Q1", "depends_on": [], "status": "current"},
                {"id": "abstract", "scope": "global", "depends_on": ["result"], "status": "current"},
                {"id": "unrelated", "scope": "Q2", "depends_on": [], "status": "current"},
            ]
            write_state(root, state)
            figure.write_bytes(b"changed")
            before = (root / "state/project_state.yaml").read_bytes()
            report = SYNC.synchronize(root, delivery_scope="docx")
            self.assertEqual(report["stale_paper_fragments"], ["abstract", "result"])
            self.assertTrue(any("stale paper fragments" in item for item in report["issues"]))
            self.assertEqual((root / "state/project_state.yaml").read_bytes(), before)

    def test_source_change_propagates_to_result_dependency_but_not_independent_question(self):
        for dependent in (True, False):
            with self.subTest(dependent=dependent), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                state, _ = make_current_project(root)
                folder = root / "问题二求解"
                shutil.copytree(root / "问题一求解", folder)
                for path in list(folder.iterdir()):
                    replacement = path.name.replace("问题一", "问题二").replace("q1_plot", "q2_plot")
                    if replacement != path.name:
                        path.rename(path.with_name(replacement))
                state["subproblems"]["Q2"] = yaml.safe_load(yaml.safe_dump(
                    state["subproblems"]["Q1"], allow_unicode=True
                ).replace("问题一", "问题二").replace("q1_plot", "q2_plot").replace("Q1", "Q2"))
                second = state["subproblems"]["Q2"]
                second["depends_on"] = [{"question": "Q1", "kind": "result"}] if dependent else []
                framework = root / "模型论文框架.md"
                framework.write_text(framework.read_text(encoding="utf-8").replace(
                    "## 图表证据链", "### Q2\n\n## 图表证据链"
                ), encoding="utf-8")
                state["paper_framework"]["sha256"] = SYNC.sha256_text(framework.read_text(encoding="utf-8"))
                state["artifacts"]["approved_figures"].append("问题二求解/当前图.pdf")
                write_state(root, state)
                snapshots = SYNC.synchronize(root, delivery_scope="docx")["questions"]
                for key, snapshot in snapshots.items():
                    state["subproblems"][key]["artifact_hashes"] = deepcopy(snapshot["artifact_hashes"])
                    state["subproblems"][key]["validated_artifact_hashes"] = deepcopy(snapshot["artifact_hashes"])
                write_state(root, state)
                baseline = SYNC.synchronize(root, delivery_scope="docx")
                self.assertEqual(baseline["status"], "passed", baseline["issues"])
                (root / "问题一求解/问题一求解.py").write_text("# current source changed\n", encoding="utf-8")
                changed = SYNC.synchronize(root, delivery_scope="docx")
                self.assertEqual(changed["status"], "failed")
                self.assertEqual(changed["stale_questions"], ["Q1", "Q2"] if dependent else ["Q1"])


if __name__ == "__main__":
    unittest.main()
