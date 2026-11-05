"""Cross-layer regressions for the eleven-issue repair; no user task execution."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import itertools
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]

import read_stage
from reading_plan import validate_chunk_coverage
from resolve_runtime import resolve_runtime
import resolve_workflow
import plot_backend
import sync_project
from reading_plan_cases import build_project
from test_v900_semantic_identity_binding import identity, structured_question, framework
from test_sync_project import write_state, framework_text
from test_v830_editable_mechanism_diagram import base_spec, GENERATOR


def file_bytes(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


class ActionAndProjectionTests(unittest.TestCase):
    def test_review_carrier_is_not_an_authoring_intent(self):
        for request in ("终审 LaTeX 论文，只审查，不修改", "审稿 Word 论文", "只审查 LaTeX，不修改", "请审查数学建模论文",
                        "审查Python绘图脚本，只读", "审阅MATLAB代码，给出修改建议，不修改文件"):
            with self.subTest(request=request):
                plan = resolve_runtime(request=request, competition="CUMCM")
                self.assertEqual(plan["intents"], ["review"])
                self.assertIn("review_report", plan["terminal_outputs"])
                self.assertFalse({"docx_draft", "latex_source", "compiled_pdf"}.intersection(plan["terminal_outputs"]))
                self.assertFalse(any("--write" in gate["command"] for gate in plan["pre_delivery_gates"]))

    def test_explicit_edit_conflict_fails_and_negated_review_still_writes(self):
        with self.assertRaisesRegex(ValueError, "review-only"):
            resolve_runtime("latex", request="只审查 LaTeX，不修改")
        plan = resolve_runtime(request="不审稿，生成 Word 草稿")
        self.assertEqual(plan["intents"], ["docx"])
        router = yaml.safe_load((ROOT / "core/workflow_router.yaml").read_bytes())
        self.assertFalse(resolve_workflow.review_only_request("不修改模型，只调整图例", router))

    def test_python_and_matlab_plot_requests(self):
        for text in ("Python绘图", "Python 绘图", "请用Python绘图", "python  绘图", "MATLAB绘图"):
            self.assertEqual(resolve_runtime(request=text)["intents"], ["figures"])

    def test_all_solver_plot_preprocessing_analysis_role_combinations(self):
        output = yaml.safe_load((ROOT / "core/output_contract.yaml").read_bytes())
        for solver, plot, decision, analysis in itertools.product(
            ("python", "matlab"), ("python", "matlab"),
            ("not_needed", "question_local", "project_level"), ("required", "not_required"),
        ):
            with self.subTest(solver=solver, plot=plot, decision=decision, analysis=analysis):
                state = {"execution": {"solver_backend": solver},
                         "plotting": {"backend": plot, "selection_reason": "synthetic whole-project choice"},
                         "preprocessing": {"decision": decision}, "subproblems": {"Q1": {"result_analysis_status": analysis}}}
                roles = plot_backend.project_figure_roles(
                    ["matlab_scripts", "preprocessing_matlab_script", "preprocessing_figures"], output, plot, decision)
                expected = "plot_scripts" if plot == "python" else "matlab_scripts"
                other = "matlab_scripts" if plot == "python" else "plot_scripts"
                self.assertIn(expected, roles)
                self.assertNotIn(other, roles)
                self.assertEqual("preprocessing_figures" in roles, decision == "project_level")
                required = sync_project.stage_requirements("figures", output, state)
                self.assertIn(expected, required)
                self.assertNotIn(other, required)

    def test_actual_project_plan_and_read_source_agree(self):
        for backend in ("python", "matlab"):
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                build_project(ROOT, root, "current")
                path = root / "state/project_state.yaml"
                state = yaml.safe_load(path.read_bytes())
                if backend == "python":
                    q = state["subproblems"]["Q1"]
                    q.pop("matlab_script")
                    script = root / "问题一求解/q1_plot.py"
                    script.write_text("# synthetic source; not executed\n", encoding="utf-8")
                    q["plot_script"] = script.relative_to(root).as_posix()
                    q["validated_artifact_hashes"]["plot_script"] = hashlib.sha256(script.read_bytes()).hexdigest()
                    state["plotting"] = {"backend": "python", "selection_reason": "synthetic whole-project choice"}
                    path.write_text(yaml.safe_dump(state, allow_unicode=True), encoding="utf-8")
                before = file_bytes(root)
                plan = resolve_runtime("figures", request="只改配色和线宽", project_root=root, question="Q1")
                expected = "plot_scripts" if backend == "python" else "matlab_scripts"
                self.assertIn(expected, plan["terminal_outputs"])
                self.assertNotIn("preprocessing_matlab_script", plan["terminal_outputs"])
                self.assertEqual(file_bytes(root), before)

    def test_missing_optional_pack_falls_back_without_missing_loads(self):
        original = Path.is_file
        absent = ROOT / "packs/competition/cumcm.md"
        with mock.patch.object(Path, "is_file", lambda p: False if p == absent else original(p)):
            for intent in ("new_problem_design", "latex"):
                plan = resolve_runtime(intent, competition="CUMCM")
                self.assertNotIn("packs/competition/cumcm.md", plan["load_order"])
                self.assertIn("packs/competition/auto.md", plan["load_order"])
                self.assertTrue(plan["resource_fallbacks"])
        with mock.patch.object(resolve_workflow, "resolve_competition_pack", return_value="../unsafe.md"):
            with self.assertRaisesRegex(ValueError, "escapes"):
                resolve_workflow.available_competition_pack("CUMCM", {})


class CurrentPlanReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.commit = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()

    def test_stale_version_fingerprint_and_stage_selection_are_rejected(self):
        plan = resolve_runtime("latex", competition="CUMCM")
        for mutation in ("version", "fingerprint", "stages", "schema"):
            changed = deepcopy(plan)
            if mutation == "version":
                changed["version"] = "10.26.2"
            elif mutation == "fingerprint":
                changed["reading_plan"]["authority_fingerprint"]["sha256"] = "0" * 64
            elif mutation == "stages":
                changed["reading_plan"]["delegated_writing_sequence"]["authoring_sequence"][0]["read_now"] = []
            else:
                changed["reading_plan"]["schema_version"] = "unknown"
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, "rerun resolve_runtime"):
                read_stage.extract(changed, ROOT, self.commit, "read_now", "core/hsk_core_policy.md")

    def test_figure_backend_preamble_is_actually_read(self):
        for intent in ("figures", "review"):
            plan = resolve_runtime(intent)
            out = read_stage.extract(plan, ROOT, self.commit, "read_now", "modules/04_figure_evidence.md", chunk_lines=4096)
            self.assertIn("plotting.backend=python|matlab", out["returned_chunk"]["text"])

    def test_project_sources_keep_separate_snapshot_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            build_project(ROOT, project, "current")
            plan = resolve_runtime("figures", request="只改配色和线宽", project_root=project, question="Q1")
            before = file_bytes(project)
            for path in ("模型论文框架.md", "state/project_state.yaml", "问题一求解/q1_plot.m"):
                with self.subTest(path=path):
                    first = read_stage.extract(plan, ROOT, self.commit, "read_now", path, project_root=project, chunk_lines=50)
                    chunks = [first["returned_chunk"]] + [
                        read_stage.extract(plan, ROOT, self.commit, "read_now", path, project_root=project,
                                           chunk_lines=50, chunk_index=i)["returned_chunk"]
                        for i in range(1, first["chunk_count"])
                    ]
                    self.assertIsNone(first["source_identity"]["selected_commit"])
                    self.assertEqual(first["source_identity"]["skill_source_commit"], self.commit)
                    self.assertTrue(validate_chunk_coverage(first["required_ranges"], chunks)["complete"])
            self.assertEqual(file_bytes(project), before)
            with self.assertRaisesRegex(ValueError, "project-root"):
                read_stage.extract(plan, ROOT, self.commit, "read_now", "模型论文框架.md")
            state = project / "state/project_state.yaml"
            state.write_bytes(state.read_bytes() + b"\n# same generation, changed bytes\n")
            with self.assertRaisesRegex(ValueError, "snapshot changed"):
                read_stage.extract(plan, ROOT, self.commit, "read_now", "模型论文框架.md", project_root=project)


class MechanismScopeTests(unittest.TestCase):
    def make_project(self, root):
        write_state(root, phase="model_design")
        path = root / "state/project_state.yaml"
        state = yaml.safe_load(path.read_bytes())
        model = identity()
        model["preprocessing_decision"] = "not_needed"
        q = state["subproblems"]["Q1"]
        q.update(structured_question(model), framework_section="### Q1：第一问")
        state["preprocessing"] = {"decision": "not_needed", "status": "not_applicable"}
        text = framework_text().replace("### Q1\n", framework(model).split("# 模型论文框架\n\n", 1)[1])
        (root / "模型论文框架.md").write_text(text, encoding="utf-8")
        state["paper_framework"]["sha256"] = hashlib.sha256(text.encode()).hexdigest()
        spec = base_spec()
        spec["semantic_anchors"]["code"] = []
        image = b'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"><rect width="10" height="10"/></svg>'
        xml = GENERATOR.generate_drawio(spec)
        artifact = spec["artifact"]
        artifact.update(preview="figures/preview/q1_occlusion.svg", final_exports=["figures/q1_occlusion.svg"],
                        spec_sha256=GENERATOR.canonical_spec_sha256(spec), drawio_sha256=hashlib.sha256(xml).hexdigest(),
                        preview_sha256=hashlib.sha256(image).hexdigest(), validation_status="passed", visual_review_status="approved_for_paper")
        for relative, data in ((artifact["preview"], image), (artifact["final_exports"][0], image), (artifact["editable_source"], xml)):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        (root / artifact["spec_source"]).write_text(yaml.safe_dump(spec, allow_unicode=True), encoding="utf-8")
        state["artifacts"]["approved_figures"] = artifact["final_exports"]
        path.write_text(yaml.safe_dump(state, allow_unicode=True), encoding="utf-8")
        return spec

    def test_current_model_only_diagram_no_numeric_artifacts_and_no_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_project(root)
            before = file_bytes(root)
            plan = resolve_runtime("editable_mechanism_diagram", project_root=root, question="Q1")
            self.assertEqual(plan["delivery_scope"], "mechanism")
            self.assertNotIn("figure_evidence:solution_workbook", plan["missing_prerequisites"])
            report = sync_project.synchronize(root, delivery_scope="mechanism", write=True)
            self.assertEqual(report["status"], "passed", report["issues"])
            self.assertFalse(report["write"])
            self.assertEqual(file_bytes(root), before)

    def test_numeric_evidence_and_unreviewed_preview_cannot_use_exemption(self):
        for mutation in ("numeric", "review", "preview"):
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                spec = self.make_project(root)
                if mutation == "numeric":
                    spec["semantic_anchors"]["result_evidence"] = ["问题一求解结果.xlsx#核心指标"]
                elif mutation == "review":
                    spec["artifact"]["visual_review_status"] = "pending"
                else:
                    (root / spec["artifact"]["preview"]).write_bytes(b"not a preview")
                (root / spec["artifact"]["spec_source"]).write_text(yaml.safe_dump(spec, allow_unicode=True), encoding="utf-8")
                self.assertEqual(sync_project.synchronize(root, delivery_scope="mechanism")["status"], "failed")
            output = yaml.safe_load((ROOT / "core/output_contract.yaml").read_bytes())
            self.assertIn("solution_workbook", sync_project.stage_requirements("figures", output))
