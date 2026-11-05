from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
TESTS = str(Path(__file__).resolve().parent)
if TESTS not in sys.path:
    sys.path.insert(0, TESTS)

from reading_plan_evidence import (
    BODY_READING_AUTHORITY_VERSIONS,
    FIGURE_HANDOFF_AUTHORITY_VERSIONS,
    FIGURE_HANDOFF_WRITING_DELTAS,
    FULL_WORKFLOW_READING_AUTHORITY_VERSIONS,
    MIXED_FIGURE_READING_AUTHORITY_VERSIONS,
    PDF_REVIEW_AUTHORITY_VERSIONS,
    PDF_REVIEW_WRITING_DELTAS,
    REVIEW_SPLIT_AUTHORITY_VERSIONS,
    REVIEW_SPLIT_WRITING_DELTAS,
    STAGE_READING_AUTHORITY_VERSIONS,
    USER_CHECKER_WORKFLOW_AUTHORITY_VERSIONS,
    review_split_writing_predecessor,
)


# Frozen CUMCM writing carrier and its historical Phase G golden stay unchanged.
CUMCM_HEADING_AUTHORITY_VERSIONS = {
    **MIXED_FIGURE_READING_AUTHORITY_VERSIONS, "skill": "10.23.3",
}
# v10.24.0 changes the Figure backend only. Pin this new carrier explicitly
# while requiring the exact existing CUMCM writing projection to remain equal.
PLOT_BACKEND_RELEASE_VERSIONS = {
    **CUMCM_HEADING_AUTHORITY_VERSIONS, "skill": "10.24.0",
}
CUMCM_2026_A1_RELEASE_VERSIONS = {
    **PLOT_BACKEND_RELEASE_VERSIONS, "skill": "10.25.0",
}
CUMCM_B_WRITING_RELEASE_VERSIONS = {
    **CUMCM_2026_A1_RELEASE_VERSIONS, "skill": "10.26.0",
}
CUMCM_C_HANDOFF_RELEASE_VERSIONS = {
    **CUMCM_B_WRITING_RELEASE_VERSIONS, "skill": "10.26.1",
}
CUMCM_D_CLEANUP_RELEASE_VERSIONS = {
    **CUMCM_C_HANDOFF_RELEASE_VERSIONS, "skill": "10.26.2",
}
# Phase C: pin the exact review reads separately from the historical
# Review Split migration and unchanged Phase G golden. Unregistered additions,
# removals, order changes, or selector substitutions must fail projection.
C_REVIEW_STAGE_PINNED_READS = {
    "draft_semantic_review": [
        "core/writing_reasoning_contract.yaml",
        "core/output_contract.yaml#per_question",
        "core/workbook_schema.yaml",
        "modules/05_writing/paper_writing_protocol.md#2-模板与写作职责",
        "modules/05_writing/paper_writing_protocol.md#3-每问的四个功能槽",
        "modules/05_writing/paper_writing_protocol.md#4-Local-Narrative-Chain",
        "modules/05_writing/paper_writing_protocol.md#5-Paragraph-Handoff-Test",
        "modules/05_writing/paper_writing_protocol.md#6-前置章节内容",
        "modules/05_writing/paper_writing_protocol.md#7-模型建立",
        "modules/05_writing/paper_writing_protocol.md#8-模型求解",
        "modules/05_writing/paper_writing_protocol.md#9-求解结果数值与术语",
        "modules/05_writing/paper_writing_protocol.md#10-结果与验证的分层",
        "modules/05_writing/paper_writing_protocol.md#11-Result-Validation-Bridge",
        "modules/05_writing/paper_writing_protocol.md#12-跨问递进",
        "modules/05_writing/paper_writing_protocol.md#13.0-CUMCM-图表的正文落点先论证职责后图型",
        "modules/05_writing/paper_writing_protocol.md#14-摘要",
        "modules/05_writing/paper_writing_protocol.md#15-模型评价逐问结论与附录",
        "modules/05_writing/paper_writing_protocol.md#16-引用与正文语言",
        "modules/06_review_delivery.md",
        "modules/06_review/content_review.md",
        "modules/04_figure_evidence.md#C 类：各问结果图合同",
        "modules/04_figure_evidence.md#Figure Evidence 层级",
        "modules/04_figure_evidence.md#Figure Portfolio Scientific Quality Gate",
        "modules/04_figure_evidence.md#Missing Scientific Evidence Check",
        "modules/04_figure_evidence.md#图题、配色与风格",
        "modules/04_figure_evidence.md#入文闭环",
        "templates/latex/cumcm/hsk/template_manifest.yaml#paper_skeleton",
        "modules/05_writing/paper_writing_protocol.md#5A-Cross-File-Chapter-Handoff",
        "current_model_paper_framework#Chapter-Handoff-Map"
    ],
    "final_review_and_delivery": [
        "core/writing_reasoning_contract.yaml",
        "core/output_contract.yaml#per_question",
        "core/workbook_schema.yaml",
        "modules/05_writing/paper_writing_protocol.md#2-模板与写作职责",
        "modules/05_writing/paper_writing_protocol.md#3-每问的四个功能槽",
        "modules/05_writing/paper_writing_protocol.md#4-Local-Narrative-Chain",
        "modules/05_writing/paper_writing_protocol.md#5-Paragraph-Handoff-Test",
        "modules/05_writing/paper_writing_protocol.md#6-前置章节内容",
        "modules/05_writing/paper_writing_protocol.md#7-模型建立",
        "modules/05_writing/paper_writing_protocol.md#8-模型求解",
        "modules/05_writing/paper_writing_protocol.md#9-求解结果数值与术语",
        "modules/05_writing/paper_writing_protocol.md#10-结果与验证的分层",
        "modules/05_writing/paper_writing_protocol.md#11-Result-Validation-Bridge",
        "modules/05_writing/paper_writing_protocol.md#12-跨问递进",
        "modules/05_writing/paper_writing_protocol.md#13.0-CUMCM-图表的正文落点先论证职责后图型",
        "modules/05_writing/paper_writing_protocol.md#14-摘要",
        "modules/05_writing/paper_writing_protocol.md#15-模型评价逐问结论与附录",
        "modules/05_writing/paper_writing_protocol.md#16-引用与正文语言",
        "modules/05_writing/paper_writing_protocol.md#5A-Cross-File-Chapter-Handoff",
        "current_model_paper_framework#Chapter-Handoff-Map",
        "modules/06_review_delivery.md",
        "modules/06_review/content_review.md",
        "modules/06_review/final_delivery.md",
        "modules/04_figure_evidence.md#C 类：各问结果图合同",
        "modules/04_figure_evidence.md#Figure Evidence 层级",
        "modules/04_figure_evidence.md#Figure Portfolio Scientific Quality Gate",
        "modules/04_figure_evidence.md#Missing Scientific Evidence Check",
        "modules/04_figure_evidence.md#图题、配色与风格",
        "modules/04_figure_evidence.md#入文闭环",
        "templates/latex/cumcm/hsk/template_manifest.yaml#paper_skeleton",
        "modules/05_latex_compile_quality.md#终稿检查",
        "core/compile_profiles.yaml",
        "config/competition_profiles.yaml",
        "packs/competition/cumcm.md",
        "templates/review/final_review_matrix.yaml",
        "current_latex_audit_and_compile_reports"
    ]
}


CUMCM_D_CLEANUP_GATE_OLD = "只清除模板感、空话、机械重复和证据越界，不删除章节必要建模理由/适用边界、推导、约束、solver 前提、命题、伪代码、结果或验证内容，也不按标题数量/字数机械合并或拆分。"
CUMCM_D_CLEANUP_GATE_NEW = "只清除普通自然语言中的模板感、空话及纯重复；公式、中文推导、证明、伪代码、算法、数值及显示格式、术语定义、引用、图表实体、章节标题与层级均只读。数学或证据问题返回既有前置审查，不在 Cleanup 改写；改后在原有 Review 中复核受保护内容，不新增门禁。"


def load_runtime():
    path = ROOT / "scripts/resolve_runtime.py"
    spec = importlib.util.spec_from_file_location("resolve_runtime_phase_g", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load resolve_runtime.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["resolve_runtime_phase_g"] = module
    spec.loader.exec_module(module)
    return module


class PhaseGCompetitionRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = load_runtime()
        cls.profiles = yaml.safe_load(
            (ROOT / "config/competition_profiles.yaml").read_text(encoding="utf-8")
        )
        cls.golden = yaml.safe_load(
            (ROOT / "tests/fixtures/phase_g_cumcm_runtime_golden.yaml").read_text(encoding="utf-8")
        )

    def _projection(self, plan):
        writing = copy.deepcopy(plan.get("writing_runtime"))
        if writing is not None:
            # Phase C review-read integration is a separate, exact reversible
            # delta. Keep the original v10.22 Review Split golden and historical
            # projection immutable, including stage gates and output targets.
            for stage_id, expected_reads in C_REVIEW_STAGE_PINNED_READS.items():
                candidates = [stage for stage in writing["authoring_sequence"] if stage["id"] == stage_id]
                self.assertEqual(len(candidates), 1)
                self.assertEqual(candidates[0]["read_now"], expected_reads)
                predecessors = [current for _, name, _, current in REVIEW_SPLIT_WRITING_DELTAS
                                if name == stage_id]
                self.assertEqual(len(predecessors), 1)
                candidates[0]["read_now"] = copy.deepcopy(predecessors[0])
            final_review = next(stage for stage in writing["authoring_sequence"]
                                if stage["id"] == "final_review_and_delivery")
            self.assertEqual(final_review.pop("run_now", None), ["assembled_seam_sweep"])
            # v10.18 adds one declared fallback condition, not a changed route or
            # an actual fallback decision. Require the exact new list before
            # projecting that clause back to the frozen Phase G metadata.
            previous = self.golden["routes"]["latex"]["writing_runtime"]["fallback_triggers"]
            comparison_trigger = "model_or_algorithm_comparison_claim_exceeds_accepted_evidence_scope"
            self.assertEqual(previous[-1], "final_review_requires_full_authority")
            self.assertNotIn(comparison_trigger, previous)
            self.assertEqual(writing.get("fallback_triggers"), [*previous[:-1], comparison_trigger, previous[-1]])
            writing["fallback_triggers"] = list(previous)
            # Only v10.26.2 adds an authorized Cleanup gate change;
            # invert that exact leaf before comparing against the golden.
            if plan["version"] == CUMCM_D_CLEANUP_RELEASE_VERSIONS["skill"]:
                cleanup_stages = [stage for stage in writing["authoring_sequence"]
                                  if stage["id"] == "ai_cleanup"]
                self.assertEqual(len(cleanup_stages), 1)
                self.assertEqual(cleanup_stages[0]["gate"], CUMCM_D_CLEANUP_GATE_NEW)
                cleanup_stages[0]["gate"] = CUMCM_D_CLEANUP_GATE_OLD
            # v10.25.0 adds exactly two CUMCM edition-specific write targets.
            if plan["version"] in (CUMCM_2026_A1_RELEASE_VERSIONS["skill"], CUMCM_B_WRITING_RELEASE_VERSIONS["skill"], CUMCM_C_HANDOFF_RELEASE_VERSIONS["skill"], CUMCM_D_CLEANUP_RELEASE_VERSIONS["skill"]):
                stage = writing["authoring_sequence"][5]
                historical = self.golden["routes"]["latex"]["writing_runtime"]["authoring_sequence"][5]
                self.assertEqual(stage["id"], "evaluation_references_conclusion_appendix")
                self.assertEqual(
                    stage["write_now"],
                    [
                        "templates/latex/cumcm/hsk/sections/09_evaluation.tex",
                        "templates/latex/cumcm/hsk/sections/10_ai_tool_statement.tex when verified_2026_cumcm",
                        "templates/latex/cumcm/hsk/references.bib",
                        "templates/latex/cumcm/hsk/appendices/appendices.tex when verified_2026_cumcm_or_other_required_material",
                    ],
                )
                stage["write_now"] = copy.deepcopy(historical["write_now"])
            # v10.23.3 adds one manifest selector to each of two CUMCM
            # writing stages. Verify the exact read list before projecting
            # back to the unchanged historical Phase G golden.
            selector = "templates/latex/cumcm/hsk/template_manifest.yaml#paper_skeleton"
            for index, stage_id in (
                (2, "problem_analysis"),
                (5, "evaluation_references_conclusion_appendix"),
            ):
                historical = self.golden["routes"]["latex"]["writing_runtime"]["authoring_sequence"][index]
                current = writing["authoring_sequence"][index]
                self.assertEqual(historical["id"], stage_id)
                self.assertEqual(current["id"], stage_id)
                self.assertEqual(current["read_now"], [selector, *historical["read_now"]])
                current["read_now"] = copy.deepcopy(historical["read_now"])
            # v10.19.3 adds exactly three question-stage handoff declarations.
            # Actual values come from the real resolver; expectations are the
            # separately pinned deltas, whose old values must also match the
            # unchanged historical golden before inverse projection.
            # v10.20.3 changes only the registered release carrier on this
            # writing path; its stage leaves keep the exact v10.19.3 values.
            self.assertIn(plan.get("version"), (
                FIGURE_HANDOFF_AUTHORITY_VERSIONS["skill"],
                USER_CHECKER_WORKFLOW_AUTHORITY_VERSIONS["skill"],
                PDF_REVIEW_AUTHORITY_VERSIONS["skill"],
                STAGE_READING_AUTHORITY_VERSIONS["skill"],
                BODY_READING_AUTHORITY_VERSIONS["skill"],
                REVIEW_SPLIT_AUTHORITY_VERSIONS["skill"],
                FULL_WORKFLOW_READING_AUTHORITY_VERSIONS["skill"],
                MIXED_FIGURE_READING_AUTHORITY_VERSIONS["skill"],
                CUMCM_HEADING_AUTHORITY_VERSIONS["skill"],
                PLOT_BACKEND_RELEASE_VERSIONS["skill"],
                CUMCM_2026_A1_RELEASE_VERSIONS["skill"],
                CUMCM_B_WRITING_RELEASE_VERSIONS["skill"],
                CUMCM_C_HANDOFF_RELEASE_VERSIONS["skill"],
                CUMCM_D_CLEANUP_RELEASE_VERSIONS["skill"],
            ))
            if plan["version"] in (
                REVIEW_SPLIT_AUTHORITY_VERSIONS["skill"],
                FULL_WORKFLOW_READING_AUTHORITY_VERSIONS["skill"],
                MIXED_FIGURE_READING_AUTHORITY_VERSIONS["skill"],
                CUMCM_HEADING_AUTHORITY_VERSIONS["skill"],
                PLOT_BACKEND_RELEASE_VERSIONS["skill"],
                CUMCM_2026_A1_RELEASE_VERSIONS["skill"],
                CUMCM_B_WRITING_RELEASE_VERSIONS["skill"],
                CUMCM_C_HANDOFF_RELEASE_VERSIONS["skill"],
                CUMCM_D_CLEANUP_RELEASE_VERSIONS["skill"],
            ):
                try:
                    writing = review_split_writing_predecessor(
                        self.golden["routes"]["latex"]["writing_runtime"], writing,
                    )
                except ValueError as exc:
                    self.fail(str(exc))
            old_stage = self.golden["routes"]["latex"]["writing_runtime"]["authoring_sequence"][4]
            current_stage = writing["authoring_sequence"][4]
            self.assertEqual(old_stage["id"], "question_model_solution_result_validation")
            self.assertEqual(current_stage["id"], old_stage["id"])
            for path, previous_value, current_value in FIGURE_HANDOFF_WRITING_DELTAS:
                baseline, candidate = old_stage, current_stage
                for key in path[:-1]:
                    baseline, candidate = baseline[key], candidate[key]
                self.assertEqual(baseline[path[-1]], previous_value)
                self.assertEqual(candidate[path[-1]], current_value)
                candidate[path[-1]] = copy.deepcopy(previous_value)
            # v10.20.4 removes only the redundant standalone audit command;
            # v10.20.5 changes reading consumption only and preserves that two-command shape.
            # Older carriers must retain the original three-command shape.
            old_assembly = self.golden["routes"]["latex"]["writing_runtime"]["authoring_sequence"][9]
            current_assembly = writing["authoring_sequence"][9]
            self.assertEqual(old_assembly["id"], "latex_assembly_audit_and_compile")
            self.assertEqual(current_assembly["id"], old_assembly["id"])
            for path, previous_value, current_value in PDF_REVIEW_WRITING_DELTAS:
                baseline, candidate = old_assembly, current_assembly
                for key in path[:-1]:
                    baseline, candidate = baseline[key], candidate[key]
                self.assertEqual(baseline[path[-1]], previous_value)
                expected = current_value if plan["version"] in (
                    PDF_REVIEW_AUTHORITY_VERSIONS["skill"],
                    STAGE_READING_AUTHORITY_VERSIONS["skill"],
                    BODY_READING_AUTHORITY_VERSIONS["skill"],
                    REVIEW_SPLIT_AUTHORITY_VERSIONS["skill"],
                    FULL_WORKFLOW_READING_AUTHORITY_VERSIONS["skill"],
                    MIXED_FIGURE_READING_AUTHORITY_VERSIONS["skill"],
                CUMCM_HEADING_AUTHORITY_VERSIONS["skill"],
                PLOT_BACKEND_RELEASE_VERSIONS["skill"],
                CUMCM_2026_A1_RELEASE_VERSIONS["skill"],
                CUMCM_B_WRITING_RELEASE_VERSIONS["skill"],
                CUMCM_C_HANDOFF_RELEASE_VERSIONS["skill"],
                CUMCM_D_CLEANUP_RELEASE_VERSIONS["skill"],
                ) else previous_value
                self.assertEqual(candidate[path[-1]], expected)
                candidate[path[-1]] = copy.deepcopy(previous_value)
        return {
            "load_order": list(plan.get("load_order", [])),
            "contracts": list(plan.get("contracts", [])),
            "templates": list(plan.get("templates", [])),
            "writing_runtime": writing,
        }

    def test_comparison_fallback_is_declared_without_preloading_latex_full_authority(self):
        plan = self.runtime.resolve_runtime("latex", competition="CUMCM")
        triggers = list(plan["writing_runtime"]["fallback_triggers"])
        self.assertEqual(self._projection(plan), self.golden["routes"]["latex"])
        self.assertEqual(plan["writing_runtime"]["fallback_triggers"], triggers)
        self.assertFalse(plan["writing_runtime"]["full_reasoning_authority_preloaded"])
        self.assertNotIn("core/writing_reasoning_contract.yaml", plan["load_order"])
        altered = copy.deepcopy(plan)
        altered["writing_runtime"]["fallback_triggers"].insert(-1, "unapproved_fallback_reason")
        with self.assertRaises(AssertionError):
            self._projection(altered)

    def test_cumcm_routes_match_pre_migration_golden(self):
        for intent, expected in self.golden["routes"].items():
            with self.subTest(intent=intent):
                kwargs = {"primary": "mechanism"} if intent == "full_workflow" else {}
                actual = self.runtime.resolve_runtime(intent, competition="CUMCM", **kwargs)
                self.assertEqual(self._projection(actual), expected)

    def test_handoff_projection_preserves_resolver_and_golden_inputs(self):
        plan = self.runtime.resolve_runtime("latex", competition="CUMCM")
        before = copy.deepcopy((plan, self.golden, FIGURE_HANDOFF_WRITING_DELTAS, PDF_REVIEW_WRITING_DELTAS))
        self.assertEqual(self._projection(plan), self.golden["routes"]["latex"])
        self.assertEqual((plan, self.golden, FIGURE_HANDOFF_WRITING_DELTAS, PDF_REVIEW_WRITING_DELTAS), before)

    def test_review_split_projection_binds_canonical_scopes_without_waiving_stage_fields(self):
        plan = self.runtime.resolve_runtime("latex", competition="CUMCM")
        self.assertEqual(plan["version"], CUMCM_D_CLEANUP_RELEASE_VERSIONS["skill"])
        saved = copy.deepcopy((plan, self.golden, REVIEW_SPLIT_WRITING_DELTAS))
        for index, stage_id, previous_reads, current_reads in REVIEW_SPLIT_WRITING_DELTAS:
            historical = self.golden["routes"]["latex"]["writing_runtime"]["authoring_sequence"][index]
            stage = plan["writing_runtime"]["authoring_sequence"][index]
            self.assertEqual(historical["id"], stage_id)
            self.assertEqual(historical["read_now"], previous_reads)
            self.assertEqual(stage["id"], stage_id)
            self.assertEqual(stage["read_now"], C_REVIEW_STAGE_PINNED_READS[stage_id])
        self.assertEqual(self._projection(plan), self.golden["routes"]["latex"])
        self.assertEqual((plan, self.golden, REVIEW_SPLIT_WRITING_DELTAS), saved)
        for index, _, _, _ in REVIEW_SPLIT_WRITING_DELTAS:
            for mutation in ("missing_content", "extra", "order", "id", "gate", "write_now"):
                with self.subTest(index=index, mutation=mutation):
                    altered = copy.deepcopy(plan)
                    stage = altered["writing_runtime"]["authoring_sequence"][index]
                    if mutation == "missing_content":
                        stage["read_now"].remove("modules/06_review/content_review.md")
                    elif mutation == "extra":
                        stage["read_now"].append("modules/06_review/final_delivery.md")
                    elif mutation == "order":
                        stage["read_now"].reverse()
                    elif mutation == "id":
                        stage["id"] = "unregistered_review"
                    elif mutation == "gate":
                        stage["gate"] = "passed"
                    else:
                        stage["write_now"] = ["unregistered_output"]
                    with self.assertRaises(AssertionError):
                        self.assertEqual(self._projection(altered), self.golden["routes"]["latex"])

    def test_projection_binds_exact_carriers_to_their_assembly_command_shape(self):
        plan = self.runtime.resolve_runtime("latex", competition="CUMCM")
        historical = ["scripts/validate_template_manifest.py", "scripts/audit_latex_project.py", "scripts/render_paper.py"]
        current = ["scripts/validate_template_manifest.py", "scripts/render_paper.py"]
        for version in ("10.19.3", "10.20.3", "10.20.4",
                        STAGE_READING_AUTHORITY_VERSIONS["skill"],
                        BODY_READING_AUTHORITY_VERSIONS["skill"],
                        REVIEW_SPLIT_AUTHORITY_VERSIONS["skill"],
                        FULL_WORKFLOW_READING_AUTHORITY_VERSIONS["skill"],
                        MIXED_FIGURE_READING_AUTHORITY_VERSIONS["skill"],
                         CUMCM_HEADING_AUTHORITY_VERSIONS["skill"],
                         PLOT_BACKEND_RELEASE_VERSIONS["skill"],
                         CUMCM_2026_A1_RELEASE_VERSIONS["skill"]):
            with self.subTest(version=version):
                declared = copy.deepcopy(plan)
                declared["version"] = version
                # Simulated historical carriers retain their real old gate.
                historical_cleanup = [stage for stage in declared["writing_runtime"]["authoring_sequence"]
                                      if stage["id"] == "ai_cleanup"]
                self.assertEqual(len(historical_cleanup), 1)
                historical_cleanup[0]["gate"] = CUMCM_D_CLEANUP_GATE_OLD
                if version not in (CUMCM_2026_A1_RELEASE_VERSIONS["skill"], CUMCM_B_WRITING_RELEASE_VERSIONS["skill"], CUMCM_C_HANDOFF_RELEASE_VERSIONS["skill"], CUMCM_D_CLEANUP_RELEASE_VERSIONS["skill"]):
                    stage = declared["writing_runtime"]["authoring_sequence"][5]
                    stage["write_now"] = copy.deepcopy(
                        self.golden["routes"]["latex"]["writing_runtime"]["authoring_sequence"][5]["write_now"]
                    )
                if version not in (
                    REVIEW_SPLIT_AUTHORITY_VERSIONS["skill"],
                    FULL_WORKFLOW_READING_AUTHORITY_VERSIONS["skill"],
                    MIXED_FIGURE_READING_AUTHORITY_VERSIONS["skill"],
                CUMCM_HEADING_AUTHORITY_VERSIONS["skill"],
                PLOT_BACKEND_RELEASE_VERSIONS["skill"],
                CUMCM_2026_A1_RELEASE_VERSIONS["skill"],
                CUMCM_B_WRITING_RELEASE_VERSIONS["skill"],
                CUMCM_C_HANDOFF_RELEASE_VERSIONS["skill"],
                CUMCM_D_CLEANUP_RELEASE_VERSIONS["skill"],
                ):
                    for index, _, previous_reads, _ in REVIEW_SPLIT_WRITING_DELTAS:
                        declared["writing_runtime"]["authoring_sequence"][index]["read_now"] = copy.deepcopy(previous_reads)
                stage = declared["writing_runtime"]["authoring_sequence"][9]
                stage["run_now"] = list(current if version in (
                    PDF_REVIEW_AUTHORITY_VERSIONS["skill"],
                    STAGE_READING_AUTHORITY_VERSIONS["skill"],
                    BODY_READING_AUTHORITY_VERSIONS["skill"],
                    REVIEW_SPLIT_AUTHORITY_VERSIONS["skill"],
                    FULL_WORKFLOW_READING_AUTHORITY_VERSIONS["skill"],
                    MIXED_FIGURE_READING_AUTHORITY_VERSIONS["skill"],
                CUMCM_HEADING_AUTHORITY_VERSIONS["skill"],
                PLOT_BACKEND_RELEASE_VERSIONS["skill"],
                CUMCM_2026_A1_RELEASE_VERSIONS["skill"],
                CUMCM_B_WRITING_RELEASE_VERSIONS["skill"],
                CUMCM_C_HANDOFF_RELEASE_VERSIONS["skill"],
                CUMCM_D_CLEANUP_RELEASE_VERSIONS["skill"],
                ) else historical)
                self.assertEqual(self._projection(declared), self.golden["routes"]["latex"])
                stage["run_now"] = list(historical if version in (
                    PDF_REVIEW_AUTHORITY_VERSIONS["skill"],
                    STAGE_READING_AUTHORITY_VERSIONS["skill"],
                    BODY_READING_AUTHORITY_VERSIONS["skill"],
                    REVIEW_SPLIT_AUTHORITY_VERSIONS["skill"],
                    FULL_WORKFLOW_READING_AUTHORITY_VERSIONS["skill"],
                    MIXED_FIGURE_READING_AUTHORITY_VERSIONS["skill"],
                CUMCM_HEADING_AUTHORITY_VERSIONS["skill"],
                PLOT_BACKEND_RELEASE_VERSIONS["skill"],
                CUMCM_2026_A1_RELEASE_VERSIONS["skill"],
                CUMCM_B_WRITING_RELEASE_VERSIONS["skill"],
                CUMCM_C_HANDOFF_RELEASE_VERSIONS["skill"],
                CUMCM_D_CLEANUP_RELEASE_VERSIONS["skill"],
                ) else current)
                with self.assertRaises(AssertionError):
                    self._projection(declared)
        for version in (None, "10.19.4", "10.20.6", "10.21.1", "10.22.1", "10.23.0", "10.24.1", "11.0.0"):
            with self.subTest(version=version):
                altered = copy.deepcopy(plan)
                altered["version"] = version
                with self.assertRaises(AssertionError):
                    self._projection(altered)

    def test_assembly_projection_preserves_manifest_render_order_and_other_stage_fields(self):
        plan = self.runtime.resolve_runtime("latex", competition="CUMCM")
        for mutation in ("reversed", "missing_manifest", "missing_render", "duplicate_render",
                         "extra_command", "gate", "read_now", "write_now", "stage_id", "stage_order"):
            with self.subTest(mutation=mutation):
                altered = copy.deepcopy(plan)
                writing = altered["writing_runtime"]
                stage = writing["authoring_sequence"][9]
                commands = stage["run_now"]
                if mutation == "reversed":
                    commands.reverse()
                elif mutation == "missing_manifest":
                    commands.pop(0)
                elif mutation == "missing_render":
                    commands.pop()
                elif mutation == "duplicate_render":
                    commands.append(commands[-1])
                elif mutation == "extra_command":
                    commands.append("scripts/audit_paper_prose.py")
                elif mutation == "gate":
                    stage["gate"] = "全部通过"
                elif mutation in ("read_now", "write_now"):
                    stage[mutation] = []
                elif mutation == "stage_id":
                    stage["id"] = "another_compile_stage"
                else:
                    writing["authoring_sequence"][8:10] = reversed(writing["authoring_sequence"][8:10])
                with self.assertRaises(AssertionError):
                    self.assertEqual(self._projection(altered), self.golden["routes"]["latex"])

    def test_assembly_projection_rejects_changed_historical_baseline(self):
        plan = self.runtime.resolve_runtime("latex", competition="CUMCM")
        original = copy.deepcopy(self.golden)
        try:
            for mutation in ("list", "id"):
                with self.subTest(mutation=mutation):
                    self.golden = copy.deepcopy(original)
                    stage = self.golden["routes"]["latex"]["writing_runtime"]["authoring_sequence"][9]
                    if mutation == "list":
                        stage["run_now"].reverse()
                    else:
                        stage["id"] = "another_compile_stage"
                    with self.assertRaises(AssertionError):
                        self._projection(plan)
        finally:
            self.golden = original

    def test_handoff_projection_rejects_unregistered_question_changes(self):
        plan = self.runtime.resolve_runtime("latex", competition="CUMCM")
        for mutation in ("extra_read", "read_order", "missing_read", "preflight_gate",
                         "completion_gate", "dispatch", "stage_order", "version"):
            with self.subTest(mutation=mutation):
                altered = copy.deepcopy(plan)
                writing = altered["writing_runtime"]
                stage = writing["authoring_sequence"][4]
                preflight = stage["before_write_preflight"]
                if mutation == "extra_read":
                    preflight["read_now"].append("core/writing_reasoning_contract.yaml")
                elif mutation == "read_order":
                    preflight["read_now"].reverse()
                elif mutation == "missing_read":
                    preflight["read_now"].pop()
                elif mutation == "preflight_gate":
                    preflight["gate"] += "未授权规则。"
                elif mutation == "completion_gate":
                    stage["gate"] = "已完成"
                elif mutation == "dispatch":
                    preflight["dispatch_from_project_state"] = False
                elif mutation == "stage_order":
                    writing["authoring_sequence"][3:5] = reversed(writing["authoring_sequence"][3:5])
                else:
                    altered["version"] = "10.19.4"
                with self.assertRaises(AssertionError):
                    self.assertEqual(self._projection(altered), self.golden["routes"]["latex"])

    def test_handoff_projection_rejects_historical_baseline_drift(self):
        plan = self.runtime.resolve_runtime("latex", competition="CUMCM")
        original = copy.deepcopy(self.golden)
        try:
            for path, _, _ in FIGURE_HANDOFF_WRITING_DELTAS:
                with self.subTest(path=path):
                    self.golden = copy.deepcopy(original)
                    target = self.golden["routes"]["latex"]["writing_runtime"]["authoring_sequence"][4]
                    for key in path[:-1]:
                        target = target[key]
                    value = target[path[-1]]
                    target[path[-1]] = [*value, "unapproved"] if isinstance(value, list) else value + "未授权规则。"
                    with self.assertRaises(AssertionError):
                        self._projection(plan)
        finally:
            self.golden = original

    def test_cumcm_aliases_keep_canonical_runtime_output(self):
        expected = self.golden["routes"]["latex"]
        for token in ("CUMCM", "cumcm", "国赛"):
            with self.subTest(token=token):
                plan = self.runtime.resolve_runtime("latex", competition=token)
                self.assertEqual(self._projection(plan), expected)
                self.assertEqual(plan["writing_runtime"]["mode"], "compact")
                self.assertIn(
                    "templates/latex/cumcm/hsk/template_manifest.yaml",
                    plan["load_order"],
                )
                self.assertIn("templates/latex/cumcm/hsk/hsk_main.tex", plan["load_order"])
                self.assertEqual(plan["writing_runtime"]["competition"], "CUMCM")

    def test_non_cumcm_profiles_keep_full_reasoning_fallback(self):
        for token in ("MCM", "ICM", "diangong", "电工杯", "certification cup"):
            with self.subTest(token=token):
                plan = self.runtime.resolve_runtime("latex", competition=token)
                self.assertIn("core/writing_reasoning_contract.yaml", plan["load_order"])
                self.assertNotIn("templates/latex/cumcm/hsk/template_manifest.yaml", plan["load_order"])
                self.assertNotEqual((plan.get("writing_runtime") or {}).get("mode"), "compact")

    def test_unknown_competition_uses_generic_writing_authority(self):
        plan = self.runtime.resolve_runtime("latex", competition="Synthetic Contest")
        self.assertIn("core/writing_reasoning_contract.yaml", plan["load_order"])
        self.assertIn("packs/competition/auto.md", plan["packs"])
        self.assertNotIn(
            "templates/latex/cumcm/hsk/template_manifest.yaml",
            plan["load_order"],
        )
        self.assertNotEqual((plan.get("writing_runtime") or {}).get("mode"), "compact")

    def test_nonwriting_route_does_not_require_competition_writing_profile(self):
        plan = self.runtime.resolve_runtime(
            "new_problem_design",
            competition="Synthetic Contest",
        )
        self.assertIn("packs/competition/auto.md", plan["packs"])
        self.assertNotIn(
            "templates/latex/cumcm/hsk/template_manifest.yaml",
            plan["load_order"],
        )

    def test_profiles_declare_runtime_modes(self):
        profiles = self.profiles["profiles"]
        self.assertEqual(profiles["cumcm"]["stable"]["writing_runtime"]["mode"], "template_first_progressive")
        for name in ("mcm_icm", "diangong", "certification_cup"):
            self.assertEqual(
                profiles[name]["stable"]["writing_runtime"]["mode"],
                "full_reasoning_fallback",
            )

    def test_declared_but_missing_template_manifest_uses_full_reasoning_fallback(self):
        missing_manifest = "templates/latex/cumcm/hsk/__missing_manifest_fixture__.yaml"
        self.assertFalse((ROOT / missing_manifest).is_file())

        synthetic = copy.deepcopy(self.profiles)
        synthetic["profiles"]["cumcm"]["stable"]["writing_runtime"][
            "template_manifest"
        ] = missing_manifest
        canonical_manifest = "templates/latex/cumcm/hsk/template_manifest.yaml"
        canonical_entry = "templates/latex/cumcm/hsk/hsk_main.tex"
        plan = {
            "intents": ["full_submission"],
            "competition": "CUMCM",
            "load_order": [
                "core/hsk_core_policy.md",
                "core/writing_runtime_contract.yaml",
                canonical_manifest,
                canonical_entry,
                "modules/05_writing/paper_writing_protocol.md",
                "modules/05_writing/latex.md",
            ],
            "contracts": [
                "core/hsk_core_policy.md",
                "core/writing_runtime_contract.yaml",
            ],
            "templates": [canonical_manifest, canonical_entry],
        }

        self.runtime._apply_profile_writing_runtime(plan, profiles=synthetic)

        self.assertIn("core/writing_reasoning_contract.yaml", plan["load_order"])
        self.assertIn("modules/05_writing/paper_writing_protocol.md", plan["load_order"])
        self.assertIn("modules/05_writing/latex.md", plan["load_order"])
        for path in (missing_manifest, canonical_manifest, canonical_entry):
            with self.subTest(path=path):
                self.assertNotIn(path, plan["load_order"])
                self.assertNotIn(path, plan["templates"])
        self.assertNotIn("writing_runtime", plan)
        self.assertEqual(
            plan["contracts"],
            [path for path in plan["load_order"] if path.startswith("core/")],
        )
        self.assertEqual(
            plan["templates"],
            [path for path in plan["load_order"] if path.startswith("templates/")],
        )

    def test_empty_or_missing_template_manifest_still_fails_closed(self):
        for missing_value in ("absent", "empty"):
            with self.subTest(missing_value=missing_value):
                synthetic = copy.deepcopy(self.profiles)
                runtime_profile = synthetic["profiles"]["cumcm"]["stable"]["writing_runtime"]
                if missing_value == "absent":
                    runtime_profile.pop("template_manifest", None)
                else:
                    runtime_profile["template_manifest"] = ""
                plan = {
                    "intents": ["full_submission"],
                    "competition": "CUMCM",
                    "load_order": [
                        "core/hsk_core_policy.md",
                        "core/writing_runtime_contract.yaml",
                        "modules/05_writing/latex.md",
                    ],
                }
                with self.assertRaisesRegex(ValueError, "requires template_manifest"):
                    self.runtime._apply_profile_writing_runtime(plan, profiles=synthetic)

    def test_missing_writing_runtime_profile_fails_closed(self):
        plan = {
            "intents": ["latex"],
            "competition": "Synthetic",
            "load_order": [
                "core/hsk_core_policy.md",
                "core/writing_reasoning_contract.yaml",
                "modules/05_writing/latex.md",
            ],
        }
        synthetic = {
            "profiles": {
                "synthetic": {"aliases": ["Synthetic"], "stable": {}}
            }
        }
        with self.assertRaisesRegex(ValueError, "lacks stable.writing_runtime"):
            self.runtime._apply_profile_writing_runtime(plan, profiles=synthetic)

    def test_resolver_has_no_cumcm_writing_constants(self):
        text = (ROOT / "scripts/resolve_runtime.py").read_text(encoding="utf-8")
        self.assertNotIn("COMPACT_WRITING_COMPETITIONS", text)
        self.assertNotIn("CUMCM_WRITING_PACKAGE_INTENTS", text)
        self.assertIn("COMPETITION_PROFILES_PATH", text)

    def test_runtime_fingerprint_includes_competition_profiles(self):
        contract = yaml.safe_load(
            (ROOT / "core/runtime_assurance_contract.yaml").read_text(encoding="utf-8")
        )
        self.assertIn(
            "config/competition_profiles.yaml",
            contract["authority_fingerprint"]["ordered_sources"],
        )


if __name__ == "__main__":
    unittest.main()
