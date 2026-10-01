"""B2b6 structured rejection return on the accepted B2b5 fixture."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import subprocess
import sys
import unittest

from jsonschema import Draft202012Validator
import yaml

from tests import test_b2b5_continuous_acceptance as b2b5
from tests.test_model_code_conformance import save
import claim_consumption
import resolve_runtime as runtime_resolver
import resolve_workflow
import runtime_assurance
import sync_project as synchronizer
import validate_project_state
import validate_submission_package as package_validator

ROOT = Path(__file__).resolve().parents[1]


class B2b6SchemaTests(unittest.TestCase):
    def test_schema_adds_exact_1_4_pair_and_structured_disposition_fields(self):
        schema = yaml.safe_load((ROOT / "core/project_state.schema.yaml").read_text(encoding="utf-8"))
        policy = schema["$defs"]["claim_consumption_policy"]
        self.assertIn("1.4.0", policy["properties"]["protocol_version"]["enum"])
        validator = Draft202012Validator({
            "$ref": "#/$defs/analysis_evidence_entry", "$defs": schema["$defs"],
        })
        core = {
            "id": "E1", "method_or_source": "Synthetic accepted analysis review",
            "target_claim": "answer_claim", "disposition": "reject",
            "impact_scope": "core_answer", "return_stage": "solve_validate",
            "key_finding": "Synthetic rejection-return acceptance finding.",
            "required_action": "Apply the declared structured disposition.", "status": "current",
        }
        self.assertTrue(validator.is_valid(core))
        wrong = deepcopy(core)
        wrong["return_stage"] = "model_design"
        self.assertFalse(validator.is_valid(wrong))

    def test_runtime_guard_projects_structured_rejection_through_dependencies(self):
        policy = {
            "protocol_version": "1.4.0", "mode": "enforce_latex_text_and_figure_chain",
            "required_consumptions": [{
                "claim_id": "Q1_answer", "fragment_kinds": ["question_result_text"],
            }],
            "figure_bindings": [{
                "figure_id": "Q1_F01", "fragment_id": "paper.q1.figure",
                "latex_label": "fig:q1", "image_path": "figures/q1.png",
                "source_bindings": [{
                    "source_id": "Q1_answer", "sheet": "主结果",
                    "required_headers": ["指标", "数值"],
                }],
            }],
        }
        core = {
            "analysis_evidence_dispositions": [{
                "id": "E1", "disposition": "reject", "status": "current",
                "impact_scope": "core_answer", "return_stage": "solve_validate",
                "method_or_source": "Synthetic review", "target_claim": "core",
                "key_finding": "The core answer is rejected.",
                "required_action": "Recompute the primary result.",
            }],
        }
        model = {
            "analysis_evidence_dispositions": [{
                "id": "E2", "disposition": "reject", "status": "current",
                "impact_scope": "model_validity", "return_stage": "model_design",
                "method_or_source": "Synthetic review", "target_claim": "model",
                "key_finding": "The model is rejected.",
                "required_action": "Revise and reapprove the model.",
            }],
        }
        state = {
            "paper_framework": {"claim_consumption_policy": policy},
            "subproblems": {
                "Q1": core,
                "Q2": {"depends_on": [{"question": "Q1", "kind": "model"}]},
                "Q3": {"depends_on": [{"question": "Q1", "kind": "result"}]},
                "Q4": {"depends_on": [{"question": "Q1", "kind": "parameter"}]},
                "Q5": {"depends_on": [{"question": "Q1", "kind": "data"}]},
                "Q6": {"depends_on": ["Q1"]},
                "Q7": model,
                "Q8": {"depends_on": [{"question": "Q7", "kind": "model"}]},
                "Q9": {"depends_on": [{"question": "Q7", "kind": "result"}]},
                "Q10": {"depends_on": [{"question": "Q7", "kind": "parameter"}]},
                "Q11": {"depends_on": [{"question": "Q7", "kind": "data"}]},
                "Q12": {"depends_on": ["Q7"]},
                "Q13": {},
            },
        }
        scoped = runtime_assurance._current_structured_rejections(
            state, state["subproblems"],
        )
        for question in ("Q2", "Q4", "Q5", "Q13"):
            self.assertFalse(scoped[question]["blocks_primary"], question)
            self.assertFalse(scoped[question]["blocks_model"], question)
        self.assertTrue(scoped["Q3"]["blocks_primary"])
        self.assertFalse(scoped["Q3"]["blocks_model"])
        self.assertTrue(scoped["Q6"]["blocks_primary"])
        self.assertTrue(scoped["Q6"]["blocks_model"])
        for question in ("Q8", "Q12"):
            self.assertTrue(scoped[question]["blocks_primary"], question)
            self.assertTrue(scoped[question]["blocks_model"], question)
        for question in ("Q9", "Q10", "Q11"):
            self.assertTrue(scoped[question]["blocks_primary"], question)
            self.assertFalse(scoped[question]["blocks_model"], question)

        incomplete = deepcopy(state)
        incomplete["paper_framework"]["claim_consumption_policy"].pop("figure_bindings")
        incomplete_guard = runtime_assurance._current_structured_rejections(incomplete, ["Q1"])
        self.assertTrue(incomplete_guard["Q1"]["blocks_primary"])
        self.assertTrue(incomplete_guard["Q1"]["blocks_model"])
        self.assertTrue(incomplete_guard["Q1"]["conflicts"])

        duplicate = deepcopy(state)
        duplicate_row = deepcopy(core["analysis_evidence_dispositions"][0])
        duplicate_row["impact_scope"] = "auxiliary_wording"
        duplicate_row.pop("return_stage")
        duplicate["subproblems"] = {
            "Q1": {"analysis_evidence_dispositions": [duplicate_row, deepcopy(duplicate_row)]},
        }
        duplicate_guard = runtime_assurance._current_structured_rejections(duplicate, ["Q1"])
        self.assertTrue(duplicate_guard["Q1"]["blocks_primary"])
        self.assertTrue(duplicate_guard["Q1"]["blocks_model"])
        self.assertTrue(duplicate_guard["Q1"]["conflicts"])


class B2b6RejectionReturnTests(unittest.TestCase):
    """Exercise the new policy without weakening the historical 1.3.0 fixture."""

    save_projection = b2b5.B2b5ContinuousAcceptanceTests.save_projection
    set_caption = b2b5.B2b5ContinuousAcceptanceTests.set_caption
    reload = b2b5.B2b5ContinuousAcceptanceTests.reload
    assert_accepted = b2b5.B2b5ContinuousAcceptanceTests.assert_accepted
    assert_old_proof_rejected = b2b5.B2b5ContinuousAcceptanceTests.assert_old_proof_rejected
    assert_current_proof = b2b5.B2b5ContinuousAcceptanceTests.assert_current_proof
    numerical_snapshot = b2b5.B2b5ContinuousAcceptanceTests.numerical_snapshot
    proof = b2b5.B2b5ContinuousAcceptanceTests.proof
    package = b2b5.B2b5ContinuousAcceptanceTests.package

    @classmethod
    def setUpClass(cls):
        b2b5.B2b5ContinuousAcceptanceTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        b2b5.B2b5ContinuousAcceptanceTests.tearDownClass.__func__(cls)

    def setUp(self):
        b2b5.B2b5ContinuousAcceptanceTests.setUp(self)
        policy = self.state["paper_framework"]["claim_consumption_policy"]
        policy["protocol_version"] = "1.4.0"
        self.state["project"]["current_phase"] = "writing_latex"
        self.state["next_gate"] = {
            "module": "writing_latex", "condition": "Synthetic downstream state",
        }
        save(self.root, self.state)

    def tearDown(self):
        b2b5.B2b5ContinuousAcceptanceTests.tearDown(self)

    def disposition(self, *, identifier: str, target: str, action: str,
                    impact_scope: str, return_stage: str | None = None):
        row = {
            "id": identifier,
            "method_or_source": "Synthetic accepted analysis review",
            "target_claim": target,
            "disposition": action,
            "impact_scope": impact_scope,
            "key_finding": "Synthetic rejection-return acceptance finding.",
            "required_action": "Apply the declared structured disposition.",
            "status": "current",
        }
        if return_stage is not None:
            row["return_stage"] = return_stage
        return row

    def sync_with(self, *rows: dict):
        self.state["subproblems"]["Q1"]["analysis_evidence_dispositions"] = list(rows)
        save(self.root, self.state)
        report = synchronizer.synchronize(self.root, write=True)
        self.assertTrue(report["write_performed"], report)
        self.reload()
        return report

    def runtime_plan(self):
        context = runtime_assurance.hydrate_project_context(self.root)
        entry = self.state["subproblems"]["Q1"]
        classification = entry["classification"]
        plan = resolve_workflow.resolve_workflow(
            "full_workflow",
            objective=classification["objective"],
            structures=classification["structures"],
            available_artifacts=context["verified_artifacts"],
            preprocessing_decision=self.state["preprocessing"]["decision"],
        )
        return context, plan

    def assert_result_qualification_revoked(self, context):
        for artifact in (
            "accepted_solution_workbook", "solution_workbook", "result_quality_report",
            "accepted_result_analysis_workbook", "result_analysis_workbook", "validated_results",
        ):
            self.assertNotIn(artifact, context["verified_artifacts"])

    def test_1_4_inherits_current_figure_chain_and_v5_delivery_options(self):
        import claim_consumption
        import latex_delivery

        gate = claim_consumption.formal_figure_gate(self.root)
        self.assertEqual(gate["status"], "passed", gate)
        self.assertEqual(gate["policy_protocol_version"], "1.4.0")
        options = latex_delivery._v5_live_figure_options(self.latex / "main.tex")
        self.assertTrue(options["allowed_external_graphics"])
        audit, compile_report = self.proof()
        self.assertEqual(audit["audit_schema_version"], "2.0.0")
        self.assertEqual(compile_report["report_schema_version"], "5.0.0")
        self.package()

    def test_auxiliary_reject_keeps_numerical_and_model_acceptance(self):
        before = self.numerical_snapshot()
        report = self.sync_with(self.disposition(
            identifier="E12", target="aux_claim", action="reject",
            impact_scope="auxiliary_wording",
        ))
        self.assertEqual(report["claim_rejection_transitions"], [])
        self.assertEqual(self.state["project"]["current_phase"], "writing_latex")
        self.assertEqual(self.numerical_snapshot(), before)
        self.assert_accepted()

    def test_core_answer_reject_returns_to_solve_and_removes_result_qualification(self):
        old_audit, old_compile = self.proof()
        old_package = self.package()
        report = self.sync_with(self.disposition(
            identifier="E12", target="answer_claim", action="reject",
            impact_scope="core_answer", return_stage="solve_validate",
        ))
        entry = self.state["subproblems"]["Q1"]
        self.assertEqual(report["claim_rejection_transitions"][0]["event"], "core_answer_rejected")
        self.assertEqual(self.state["project"]["current_phase"], "solve_validate")
        self.assertEqual(self.state["next_gate"]["module"], "solve_validate")
        self.assertEqual(entry["status"], "designed")
        self.assertEqual(entry["result_analysis_status"], "redo_required")
        self.assertEqual(entry["analysis_execution_status"], "redo_required")
        self.assertIn("solution_workbook", entry["stale_layers"])
        state_issues = validate_project_state.validate_state_file(
            self.root / "state/project_state.yaml", project_root=self.root)
        self.assertEqual(state_issues, [])
        self.assertEqual(claim_consumption.formal_figure_gate(self.root)["status"], "failed")
        self.assert_old_proof_rejected(old_audit, old_compile)
        self.assertEqual(package_validator.validate_package(self.root, old_package)["status"], "failed")
        context, plan = self.runtime_plan()
        self.assertIn("locked_model_spec", context["verified_artifacts"])
        self.assert_result_qualification_revoked(context)
        self.assertIn("modules/03_solve_validate.md", plan["modules"])
        self.assertNotIn("modules/03_result_analysis.md", plan["modules"])

    def test_model_validity_reject_returns_to_model_design_and_revokes_approval(self):
        report = self.sync_with(self.disposition(
            identifier="E12", target="answer_claim", action="reject",
            impact_scope="model_validity", return_stage="model_design",
        ))
        entry = self.state["subproblems"]["Q1"]
        self.assertEqual(report["claim_rejection_transitions"][0]["event"], "model_validity_rejected")
        self.assertEqual(self.state["project"]["current_phase"], "model_design")
        self.assertEqual(self.state["next_gate"]["module"], "model_design")
        self.assertEqual(entry["status"], "audited")
        self.assertEqual(entry["model_challenge_status"], "stale")
        self.assertEqual(entry["human_model_approval_status"], "stale")
        self.assertEqual(entry["result_analysis_status"], "redo_required")
        state_issues = validate_project_state.validate_state_file(
            self.root / "state/project_state.yaml", project_root=self.root)
        self.assertEqual(state_issues, [])
        self.assertEqual(claim_consumption.formal_figure_gate(self.root)["status"], "failed")
        context, plan = self.runtime_plan()
        self.assertNotIn("locked_model_spec", context["verified_artifacts"])
        self.assert_result_qualification_revoked(context)
        self.assertNotIn("modules/03_solve_validate.md", plan["modules"])
        self.assertTrue(plan["pause_for_model_approval"])

        self.state["project"]["current_phase"] = "problem_audit"
        self.state["next_gate"] = {
            "module": "problem_audit", "condition": "Resolve an earlier independent audit gate",
        }
        save(self.root, self.state)
        state_issues = validate_project_state.validate_state_file(
            self.root / "state/project_state.yaml", project_root=self.root)
        self.assertEqual(state_issues, [])

    def test_handwritten_core_reject_cannot_keep_accepted_runtime_qualification(self):
        entry = self.state["subproblems"]["Q1"]
        entry["analysis_evidence_dispositions"] = [self.disposition(
            identifier="E12", target="answer_claim", action="reject",
            impact_scope="core_answer", return_stage="solve_validate",
        )]
        save(self.root, self.state)
        issues = validate_project_state.validate_state_file(
            self.root / "state/project_state.yaml", project_root=self.root)
        self.assertTrue(any("current core_answer rejection requires" in issue for issue in issues), issues)
        context, plan = self.runtime_plan()
        self.assertIn("locked_model_spec", context["verified_artifacts"])
        self.assert_result_qualification_revoked(context)
        self.assertIn("modules/03_solve_validate.md", plan["modules"])
        resolved = runtime_resolver.resolve_runtime(
            "full_workflow", project_root=self.root, question="Q1",
        )
        self.assertIn("modules/03_solve_validate.md", resolved["modules"])
        self.assertNotIn("modules/03_result_analysis.md", resolved["modules"])

    def test_handwritten_model_reject_cannot_keep_model_or_result_qualification(self):
        entry = self.state["subproblems"]["Q1"]
        entry["analysis_evidence_dispositions"] = [self.disposition(
            identifier="E12", target="answer_claim", action="reject",
            impact_scope="model_validity", return_stage="model_design",
        )]
        save(self.root, self.state)
        issues = validate_project_state.validate_state_file(
            self.root / "state/project_state.yaml", project_root=self.root)
        self.assertTrue(any("project.current_phase" in issue for issue in issues), issues)
        self.assertTrue(any("human_model_approval_status=stale" in issue for issue in issues), issues)
        context, plan = self.runtime_plan()
        self.assertNotIn("locked_model_spec", context["verified_artifacts"])
        self.assert_result_qualification_revoked(context)
        self.assertTrue(plan["pause_for_model_approval"])
        resolved = runtime_resolver.resolve_runtime(
            "full_workflow", project_root=self.root, question="Q1",
        )
        self.assertTrue(resolved["pause_for_model_approval"])
        self.assertNotIn("modules/03_solve_validate.md", resolved["modules"])

    def test_unsynced_core_reject_revokes_typed_dependent_runtime_qualification(self):
        dependent = self.state["subproblems"]["Q1"]
        source = deepcopy(dependent)
        source["analysis_evidence_dispositions"] = []
        dependent["depends_on"] = [{"question": "Q2", "kind": "result"}]
        self.state["subproblems"]["Q2"] = source
        save(self.root, self.state)
        baseline = runtime_assurance.hydrate_project_context(self.root, "Q1")
        self.assertIn("accepted_solution_workbook", baseline["verified_artifacts"])

        source["analysis_evidence_dispositions"] = [self.disposition(
            identifier="E12", target="answer_claim", action="reject",
            impact_scope="core_answer", return_stage="solve_validate",
        )]
        save(self.root, self.state)
        dependent["depends_on"] = [{"question": "q2", "kind": "result"}]
        save(self.root, self.state)
        malformed_dependency = runtime_assurance.hydrate_project_context(self.root, "Q1")
        self.assertNotIn("locked_model_spec", malformed_dependency["verified_artifacts"])
        self.assert_result_qualification_revoked(malformed_dependency)
        self.assertTrue(any(
            "dependency declarations" in item for item in malformed_dependency["conflicts"]
        ), malformed_dependency)

        dependent["depends_on"] = [{"question": "Q2", "kind": "result"}]
        save(self.root, self.state)
        rejected = runtime_assurance.hydrate_project_context(self.root, "Q1")
        self.assert_result_qualification_revoked(rejected)
        primary = next(
            row for row in rejected["artifact_evidence"]
            if row["artifact"] == "accepted_solution_workbook" and row["scope"] == "Q1"
        )
        self.assertIn("depends on rejected Q2 through result", primary["reason"])
        resolved = runtime_resolver.resolve_runtime(
            "full_workflow", project_root=self.root, question="Q1",
        )
        self.assertIn("modules/03_solve_validate.md", resolved["modules"])

    def test_malformed_current_reject_fails_closed_only_under_exact_1_4_policy(self):
        row = self.disposition(
            identifier="E12", target="answer_claim", action="reject",
            impact_scope="core_answer", return_stage="solve_validate",
        )
        row.pop("impact_scope")
        row.pop("return_stage")
        self.state["subproblems"]["Q1"]["analysis_evidence_dispositions"] = [row]
        save(self.root, self.state)
        exact = runtime_assurance.hydrate_project_context(self.root)
        self.assertNotIn("locked_model_spec", exact["verified_artifacts"])
        self.assert_result_qualification_revoked(exact)
        self.assertTrue(any("current B2 1.4" in item for item in exact["conflicts"]), exact)

        row["impact_scope"] = ["core_answer"]
        save(self.root, self.state)
        malformed_issues = validate_project_state.validate_state_file(
            self.root / "state/project_state.yaml", project_root=self.root)
        self.assertTrue(malformed_issues)
        unhashable = runtime_assurance.hydrate_project_context(self.root)
        self.assertNotIn("locked_model_spec", unhashable["verified_artifacts"])
        self.assert_result_qualification_revoked(unhashable)
        self.assertTrue(unhashable["conflicts"], unhashable)

        row.update(
            impact_scope="core_answer", return_stage="solve_validate", status=["current"],
        )
        save(self.root, self.state)
        malformed_status = runtime_assurance.hydrate_project_context(self.root)
        self.assertNotIn("locked_model_spec", malformed_status["verified_artifacts"])
        self.assert_result_qualification_revoked(malformed_status)
        self.assertTrue(malformed_status["conflicts"], malformed_status)

        row.update(
            status="current", disposition=["reject"], impact_scope="core_answer",
            return_stage="solve_validate",
        )
        save(self.root, self.state)
        malformed_disposition_issues = validate_project_state.validate_state_file(
            self.root / "state/project_state.yaml", project_root=self.root)
        self.assertTrue(malformed_disposition_issues)
        malformed_disposition = runtime_assurance.hydrate_project_context(self.root)
        self.assertNotIn("locked_model_spec", malformed_disposition["verified_artifacts"])
        self.assert_result_qualification_revoked(malformed_disposition)
        self.assertTrue(malformed_disposition["conflicts"], malformed_disposition)

        row["disposition"] = "reject"
        row["impact_scope"] = "auxiliary_wording"
        row["return_stage"] = None
        save(self.root, self.state)
        explicit_null = runtime_assurance.hydrate_project_context(self.root)
        self.assertNotIn("locked_model_spec", explicit_null["verified_artifacts"])
        self.assert_result_qualification_revoked(explicit_null)
        self.assertTrue(explicit_null["conflicts"], explicit_null)

        row.update(impact_scope="core_answer", return_stage="solve_validate")
        row.pop("required_action")
        save(self.root, self.state)
        missing_required = runtime_assurance.hydrate_project_context(self.root)
        self.assertNotIn("locked_model_spec", missing_required["verified_artifacts"])
        self.assert_result_qualification_revoked(missing_required)
        self.assertTrue(missing_required["conflicts"], missing_required)
        row["required_action"] = "Apply the declared structured disposition."

        self.state["subproblems"]["Q1"]["depends_on"] = {
            "question": "Q2", "kind": "result",
        }
        save(self.root, self.state)
        malformed_dependencies = runtime_assurance.hydrate_project_context(self.root)
        self.assertNotIn("locked_model_spec", malformed_dependencies["verified_artifacts"])
        self.assert_result_qualification_revoked(malformed_dependencies)
        self.assertTrue(any(
            "dependency declarations" in item for item in malformed_dependencies["conflicts"]
        ), malformed_dependencies)
        self.state["subproblems"]["Q1"].pop("depends_on")

        row["disposition"] = "modify"
        row.pop("impact_scope")
        row.pop("return_stage")
        save(self.root, self.state)
        malformed_modify = runtime_assurance.hydrate_project_context(self.root)
        self.assertNotIn("locked_model_spec", malformed_modify["verified_artifacts"])
        self.assert_result_qualification_revoked(malformed_modify)
        self.assertTrue(malformed_modify["conflicts"], malformed_modify)

        row.update(
            disposition="reject", impact_scope="core_answer", return_stage="solve_validate",
        )
        self.state["paper_framework"]["claim_consumption_policy"]["mode"] = "observe"
        save(self.root, self.state)
        partial_policy = runtime_assurance.hydrate_project_context(self.root)
        self.assertNotIn("locked_model_spec", partial_policy["verified_artifacts"])
        self.assert_result_qualification_revoked(partial_policy)
        self.assertTrue(any("policy pair" in item for item in partial_policy["conflicts"]), partial_policy)

        row.pop("impact_scope")
        row.pop("return_stage")
        row["status"] = "current"
        self.state["paper_framework"]["claim_consumption_policy"].update(
            protocol_version="1.3.0", mode="enforce_latex_text_and_figure_chain",
        )
        save(self.root, self.state)
        legacy = runtime_assurance.hydrate_project_context(self.root)
        self.assertIn("locked_model_spec", legacy["verified_artifacts"])
        self.assertIn("accepted_solution_workbook", legacy["verified_artifacts"])
        self.assertFalse(any("invalid current B2 1.4 rejection" in item for item in legacy["conflicts"]))

    def test_malformed_subproblem_and_validator_containers_do_not_crash(self):
        original = deepcopy(self.state["subproblems"]["Q1"])
        self.state["subproblems"]["Q1"] = "malformed"
        save(self.root, self.state)
        context = runtime_assurance.hydrate_project_context(self.root, "Q1")
        self.assertNotIn("locked_model_spec", context["verified_artifacts"])
        self.assert_result_qualification_revoked(context)
        self.assertTrue(context["conflicts"], context)
        self.assertTrue(context["ambiguities"], context)

        self.state["subproblems"]["Q1"] = original
        original["analysis_evidence_dispositions"] = 1
        save(self.root, self.state)
        container_issues = validate_project_state.validate_state_file(
            self.root / "state/project_state.yaml", project_root=self.root)
        self.assertTrue(container_issues)

        original["analysis_evidence_dispositions"] = [self.disposition(
            identifier="E12", target="answer_claim", action="reject",
            impact_scope="core_answer", return_stage="solve_validate",
        )]
        original["stale_layers"] = [{}]
        save(self.root, self.state)
        stale_issues = validate_project_state.validate_state_file(
            self.root / "state/project_state.yaml", project_root=self.root)
        self.assertTrue(stale_issues)

    def test_malformed_identity_and_preprocessing_do_not_escape_real_validation_clis(self):
        original = deepcopy(self.state)

        def hashes():
            return {path.relative_to(self.root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in self.root.rglob("*") if path.is_file()}

        for field in ("legal", "question", "preprocessing", "artifact_hashes", "validated_artifact_hashes", "stale_layers"):
            with self.subTest(field=field):
                state = deepcopy(original)
                if field == "question":
                    state["subproblems"]["Q1"] = "broken"
                elif field == "preprocessing":
                    state[field] = "broken"
                elif field != "legal":
                    state["subproblems"]["Q1"][field] = [{}]
                save(self.root, state)
                before = hashes()
                for script in ("validate_user_execution.py", "validate_code_delivery.py"):
                    for write_args in ([], ["--write"]) if field != "legal" else ([],):
                        completed = subprocess.run(
                            [sys.executable, "-B", str(ROOT / "scripts" / script), str(self.root), "--strict", *write_args],
                            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
                        )
                        self.assertNotIn("Traceback (most recent call last)", completed.stderr, script)
                        report = yaml.safe_load(completed.stdout)
                        self.assertEqual(report["status"], "passed" if field == "legal" else "failed", script)
                        self.assertEqual(completed.returncode, 0 if field == "legal" else 1, script)
                        self.assertFalse(report["task_code_executed"])
                        self.assertFalse(report["report_persisted"])
                        self.assertEqual(before, hashes(), script)

    def test_model_design_wins_when_core_and_model_rejects_coexist(self):
        self.sync_with(
            self.disposition(
                identifier="E12", target="answer_claim", action="reject",
                impact_scope="core_answer", return_stage="solve_validate",
            ),
            self.disposition(
                identifier="E13", target="answer_claim", action="reject",
                impact_scope="model_validity", return_stage="model_design",
            ),
        )
        self.assertEqual(self.state["project"]["current_phase"], "model_design")
        self.assertEqual(self.state["subproblems"]["Q1"]["status"], "audited")
        state_issues = validate_project_state.validate_state_file(
            self.root / "state/project_state.yaml", project_root=self.root)
        self.assertEqual(state_issues, [])

    def test_core_reject_validator_accepts_conservative_model_design_rewind(self):
        self.sync_with(self.disposition(
            identifier="E12", target="answer_claim", action="reject",
            impact_scope="core_answer", return_stage="solve_validate",
        ))
        for phase in ("problem_audit", "model_design", "data_preprocessing", "solve_validate"):
            with self.subTest(phase=phase):
                self.state["project"]["current_phase"] = phase
                self.state["next_gate"] = {
                    "module": phase,
                    "condition": "Resolve an earlier independent lifecycle gate.",
                }
                save(self.root, self.state)
                state_issues = validate_project_state.validate_state_file(
                    self.root / "state/project_state.yaml", project_root=self.root)
                self.assertEqual(state_issues, [])

    def test_new_policy_requires_modify_and_reject_impact_scope_but_legacy_remains_readable(self):
        for action in ("modify", "reject"):
            with self.subTest(action=action):
                row = self.disposition(
                    identifier="E12", target="answer_claim", action=action,
                    impact_scope="core_answer",
                    return_stage="solve_validate" if action == "reject" else None,
                )
                row.pop("impact_scope")
                row.pop("return_stage", None)
                self.state["subproblems"]["Q1"]["analysis_evidence_dispositions"] = [row]
                save(self.root, self.state)
                blocked = synchronizer.synchronize(self.root, write=True)
                self.assertEqual(blocked["status"], "failed")
                self.assertFalse(blocked["write_performed"])
                self.assertTrue(any("impact_scope" in issue for issue in blocked["issues"]), blocked)

        self.state["paper_framework"]["claim_consumption_policy"]["protocol_version"] = "1.3.0"
        save(self.root, self.state)
        legacy = synchronizer.synchronize(self.root, write=True)
        self.assertTrue(legacy["write_performed"], legacy["issues"])
        self.reload()
        self.assertEqual(self.state["project"]["current_phase"], "writing_latex")


if __name__ == "__main__":
    unittest.main()
