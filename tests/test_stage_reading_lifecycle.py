"""Consume real routed sources across boundaries without advancing a project.

These are repository integration tests, not competition runs or proof that a
model understood a source. Name-only compatibility inputs below deliberately
remain declared_unverified. Synthetic workbook fixtures test existing provenance
and disposition rules; no numerical code or delivery gate is executed here.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import read_stage
from reading_plan import validate_chunk_coverage
from reading_plan_cases import build_project
from resolve_runtime import resolve_runtime


def project_bytes(root: Path) -> dict[str, bytes]:
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*") if path.is_file()}


class StageReadingLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The source checkout is the actual CI commit. No current-file snapshot
        # is mocked as a Git blob, and no entire repository fixture is copied.
        cls.commit = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    def consume(self, plan, path, *, surface="read_now", stage_id=None,
                condition=None, chunk_lines=4096):
        before = deepcopy(plan)
        original = (ROOT / path).read_bytes()
        options = {"stage_id": stage_id, "condition": condition,
                   "chunk_lines": chunk_lines}
        first = read_stage.extract(
            plan, ROOT, self.commit, surface, path, **options)
        outputs = [first] + [
            read_stage.extract(plan, ROOT, self.commit, surface, path,
                               chunk_index=index, **options)
            for index in range(1, first["chunk_count"])
        ]
        chunks = [output["returned_chunk"] for output in outputs]
        coverage = validate_chunk_coverage(first["required_ranges"], chunks)
        self.assertTrue(coverage["complete"], coverage)
        lines = original.decode("utf-8").splitlines(keepends=True)
        expected = "".join("".join(lines[start - 1:end])
                           for start, end in first["required_ranges"])
        text = "".join(chunk["text"] for chunk in chunks)
        self.assertEqual(text, expected)
        self.assertTrue(text.strip())
        for output in outputs:
            self.assertEqual(output["status"], "source_text_returned_not_stage_or_gate_passed")
            self.assertEqual(output["gate_status"], "not_executed_by_reader")
            self.assertEqual(output["source_identity"]["selected_commit"], self.commit)
            self.assertEqual(output["source_identity"]["sha256"],
                             hashlib.sha256(original).hexdigest())
        # This protects every current plan field, including future additive
        # assurance fields, instead of maintaining another list of gate names.
        self.assertEqual(plan, before)
        self.assertEqual((ROOT / path).read_bytes(), original)
        return text, outputs

    def test_real_routes_return_body_without_advancing_the_resolved_plan(self):
        cases = (
            ("problem_analysis", {}, "modules/01_problem_audit.md", None),
            ("new_problem_design", {"objective": "optimization"},
             "modules/02_model_design.md", "awaiting_model_approval"),
            ("code_and_solution", {
                "objective": "optimization", "solver_backend": "python",
                "preprocessing_decision": "not_needed",
                "available_artifacts": ["locked_model_spec"],
            }, "modules/03_solve_validate.md", "awaiting_user_execution"),
            ("returned_workbook_validation", {}, "core/user_execution_contract.yaml", None),
            ("editable_mechanism_diagram", {"request": "绘制可编辑机理图。"},
             "modules/04_figure_evidence.md", None),
            ("latex", {"competition": "MCM"},
             "modules/05_writing/paper_writing_protocol.md", None),
            ("full_submission", {"competition": "CUMCM"},
             "modules/06_review/final_delivery.md", None),
        )
        for intent, arguments, path, pause in cases:
            with self.subTest(intent=intent):
                plan = resolve_runtime(intent, **arguments)
                self.assertEqual(plan["pause_state"], pause)
                self.assertFalse(plan["task_code_execution_allowed"])
                self.consume(plan, path)
                if intent == "code_and_solution":
                    declaration = next(row for row in plan["assurance"]["artifact_assurance"]["evidence"]
                                       if row["artifact"] == "locked_model_spec")
                    self.assertEqual(declaration["status"], "declared_unverified")
                    self.assertNotIn("accepted_solution_workbook",
                                     plan["assurance"]["artifact_assurance"]["effective_artifacts"])
                elif intent == "returned_workbook_validation":
                    self.assertEqual(plan["assurance"]["artifact_assurance"]["effective_artifacts"], [])
                elif intent == "latex":
                    self.assertEqual(plan["reading_plan"]["profile"], "full")
                    self.assertNotEqual((plan.get("writing_runtime") or {}).get("mode"), "compact")
                    self.assertIn("core/writing_reasoning_contract.yaml", plan["load_order"])

    def test_preprocessing_dispositions_keep_their_original_execution_pause(self):
        for decision in ("not_needed", "question_local", "project_level"):
            with self.subTest(decision=decision):
                plan = resolve_runtime(
                    "full_solution", objective="optimization", solver_backend="python",
                    available_artifacts=["locked_model_spec"],
                    preprocessing_decision=decision,
                )
                if decision == "project_level":
                    self.assertEqual(plan["pause_state"], "awaiting_user_preprocessing")
                    self.assertNotIn("modules/03_solve_validate.md", plan["modules"])
                    path = "modules/03_data_preprocessing.md"
                else:
                    self.assertEqual(plan["pause_state"], "awaiting_user_execution")
                    self.assertNotIn("modules/03_data_preprocessing.md", plan["modules"])
                    path = "modules/03_solve_validate.md"
                self.consume(plan, path)
                self.assertFalse(plan["task_code_execution_allowed"])

    def test_not_required_disposition_needs_reason_and_never_creates_analysis(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            build_project(ROOT, project, "current")
            state_path = project / "state/project_state.yaml"
            state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
            question = state["subproblems"]["Q1"]
            for field in ("result_analysis_code", "result_analysis_workbook", "robustness_workbook"):
                relative = question.pop(field, None)
                if relative and (project / relative).is_file():
                    (project / relative).unlink()
            question.pop("analysis_code_sha256", None)
            question["solver_execution"].pop("analysis", None)
            for field in ("artifact_hashes", "validated_artifact_hashes"):
                for layer in ("analysis_code", "result_analysis_workbook", "robustness_workbook"):
                    question.get(field, {}).pop(layer, None)
            question.update(result_analysis_status="not_required", analysis_execution_status="pending")
            for reason in ("Synthetic primary result needs no independent analysis.", ""):
                with self.subTest(has_reason=bool(reason)):
                    question["result_analysis_requirement_reason"] = reason
                    state_path.write_text(
                        yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
                    before = project_bytes(project)
                    plan = resolve_runtime("full_workflow", project_root=project, question="Q1")
                    disposition = next(
                        row for row in plan["assurance"]["artifact_assurance"]["evidence"]
                        if row["artifact"] == "result_analysis_not_required")
                    self.assertEqual(disposition["status"], "verified" if reason else "not_accepted")
                    if reason:
                        self.assertNotIn("modules/03_result_analysis.md", plan["modules"])
                        self.assertNotIn("result_analysis_code", plan["module_terminal_outputs"])
                    self.consume(plan, "core/user_execution_contract.yaml")
                    self.assertEqual(project_bytes(project), before)

    def test_question_and_chapter_boundaries_return_text_again_at_same_commit(self):
        texts = []
        for question in ("Q1", "Q2"):
            plan = resolve_runtime("latex", competition="CUMCM", question=question)
            self.assertEqual(plan["assurance"]["context"]["question"], question)
            self.assertFalse(plan["assurance"]["context"]["project_state_loaded"])
            text, _ = self.consume(
                plan, "modules/05_writing/paper_writing_protocol.md",
                surface="writing_stage", stage_id="question_model_solution_result_validation")
            texts.append(text)
        self.assertEqual(texts[0], texts[1])

        # This starts from a deliberately lossy summary, not from an assertion
        # that a platform compression event has occurred or been detected.
        summary = {"next_stage": "problem_analysis", "question": "Q2"}
        recovered = resolve_runtime("latex", competition="CUMCM", question=summary["question"])
        recovered_text, _ = self.consume(
            recovered, "modules/05_writing/paper_writing_protocol.md",
            surface="writing_stage", stage_id=summary["next_stage"])
        restatement, _ = self.consume(
            recovered, "modules/05_writing/paper_writing_protocol.md",
            surface="writing_stage", stage_id="problem_restatement")
        self.assertNotEqual(recovered_text, restatement)
        # An unscoped source read restores rules, not current project facts.
        self.assertFalse(recovered["assurance"]["context"]["project_state_loaded"])

    def test_unknown_capabilities_require_explicit_body_selection_and_stay_unadjudicated(self):
        plan = resolve_runtime("latex", competition="CUMCM", question="Q1")
        stage = "question_model_solution_result_validation"
        before = deepcopy(plan)
        _, pending = read_stage.select_sources(plan, ROOT, "writing_stage", stage_id=stage)
        self.assertTrue(any(row["status"] == "unresolved_condition" for row in pending))
        for condition, path in (
            ("proposition_or_proof", "packs/artifact/proposition_proof.md"),
            ("stepwise_or_pseudocode", "packs/artifact/algorithm_flow.md"),
        ):
            with self.subTest(condition=condition):
                with self.assertRaisesRegex(ValueError, "not uniquely selected"):
                    read_stage.extract(plan, ROOT, self.commit, "writing_stage", path, stage_id=stage)
                _, outputs = self.consume(
                    plan, path, surface="writing_stage", stage_id=stage, condition=condition)
                self.assertTrue(any(
                    row["status"] == "requires_current_project_fact_adjudication"
                    for row in outputs[0]["unresolved_inputs_or_conditions"]))
        self.assertEqual(plan, before)

    def test_real_source_chunks_detect_gaps_and_mixed_identity_before_complete_reassembly(self):
        plan = resolve_runtime("problem_analysis")
        _, outputs = self.consume(plan, "modules/01_problem_audit.md", chunk_lines=20)
        chunks = [output["returned_chunk"] for output in outputs]
        ranges = outputs[0]["required_ranges"]
        self.assertGreater(len(chunks), 1)
        self.assertFalse(outputs[0]["all_required_ranges_returned_in_this_response"])
        missing = validate_chunk_coverage(ranges, chunks[:-1])
        self.assertFalse(missing["complete"])
        self.assertTrue(missing["missing_ranges"])
        truncated = deepcopy(chunks)
        truncated[-1]["text"] = ""
        self.assertFalse(validate_chunk_coverage(ranges, truncated)["complete"])
        mixed = deepcopy(chunks)
        mixed[-1]["source_commit"] = "0" * 40
        self.assertFalse(validate_chunk_coverage(ranges, mixed)["complete"])
        self.assertTrue(validate_chunk_coverage(ranges, chunks)["complete"])

    def test_mixed_intent_keeps_conservative_full_sources_after_consumption(self):
        plan = resolve_runtime(["figures", "framework_sync"], request="绘图并修改框架。")
        self.assertEqual(plan["reading_plan"]["profile"], "full")
        self.assertTrue(plan["reading_plan"]["reasons"])
        self.consume(plan, "modules/04_figure_evidence.md")
        self.assertFalse(plan["task_code_execution_allowed"])


if __name__ == "__main__":
    unittest.main()
