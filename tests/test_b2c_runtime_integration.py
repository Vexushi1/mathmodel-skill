"""Peripheral runtime and LaTeX integration for the B2 1.5 selected carrier."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import audit_latex_project  # noqa: E402
import claim_consumption  # noqa: E402
import latex_delivery  # noqa: E402
import render_paper  # noqa: E402
import resolve_runtime  # noqa: E402
import runtime_assurance  # noqa: E402
import validate_submission_package  # noqa: E402
import validate_user_execution  # noqa: E402
import validate_project_state  # noqa: E402
import sync_project  # noqa: E402
from submission_requirements import bound_compile_files, reproducibility_requirements  # noqa: E402
from tests import test_b2b6_rejection_return as rejection_fixture  # noqa: E402


def selected_policy(carrier: str) -> dict:
    suffix = "tex" if carrier == "latex" else "docx"
    folder = "final_latex" if carrier == "latex" else "draft_docx"
    locator = ({"kind": "latex_label", "value": "fig:q1"}
               if carrier == "latex" else
               {"kind": "docx_bookmark", "value": "fig_q1", "body_reference": "见图1"})
    return {
        "protocol_version": "1.5.0",
        "mode": "enforce_selected_paper_claim_chain",
        "paper_source": {"format": carrier, "entrypoint": f"{folder}/paper.{suffix}"},
        "required_consumptions": [{
            "claim_id": "Q1_answer", "fragment_kinds": ["question_result_text"],
        }],
        "figure_bindings": [{
            "figure_id": "Q1_F01", "fragment_id": "paper.q1.figure",
            "carrier_locator": locator, "image_path": "figures/q1.png",
            "source_bindings": [{
                "source_id": "Q1_answer", "sheet": "主结果",
                "required_headers": ["指标", "数值"],
            }],
        }],
    }


class SelectedCarrierRuntimeTests(unittest.TestCase):
    def test_runtime_contract_2_4_declares_both_structured_policies(self):
        contract = yaml.safe_load(
            (ROOT / "core/runtime_assurance_contract.yaml").read_text(encoding="utf-8")
        )
        self.assertEqual(contract["version"], "2.4.0")
        rules = "\n".join(contract["runtime_context"]["rules"])
        self.assertIn("1.4.0 and 1.5.0", rules)
        analysis_module = (ROOT / "modules/03_result_analysis.md").read_text(encoding="utf-8")
        self.assertIn("1.5.0/enforce_selected_paper_claim_chain", analysis_module)
        self.assertIn("B2 1.4.0/1.5.0 current modify/reject", analysis_module)

    def test_1_5_inherits_structured_rejection_runtime(self):
        state = {
            "paper_framework": {"claim_consumption_policy": selected_policy("latex")},
            "subproblems": {
                "Q1": {"analysis_evidence_dispositions": [{
                    "id": "E1", "method_or_source": "accepted analysis",
                    "target_claim": "core", "disposition": "reject",
                    "impact_scope": "core_answer", "return_stage": "solve_validate",
                    "key_finding": "core result failed", "required_action": "recompute",
                    "status": "current",
                }]},
                "Q2": {"depends_on": [{"question": "Q1", "kind": "result"}]},
            },
        }
        result = runtime_assurance._current_structured_rejections(state, ["Q1", "Q2"])
        self.assertTrue(result["Q1"]["blocks_primary"], result)
        self.assertTrue(result["Q2"]["blocks_primary"], result)
        self.assertTrue(any("B2 1.5" in item for item in result["Q1"]["primary_reasons"]))
        self.assertTrue(validate_user_execution._uses_structured_rejection_policy(state))

    def test_1_0_to_1_3_do_not_activate_structured_rejection_runtime(self):
        disposition = {
            "id": "E1", "method_or_source": "accepted analysis",
            "target_claim": "core", "disposition": "reject",
            "impact_scope": "core_answer", "return_stage": "solve_validate",
            "key_finding": "core result failed", "required_action": "recompute",
            "status": "current",
        }
        for version, mode in (
            ("1.0.0", "observe"),
            ("1.1.0", "propagate"),
            ("1.2.0", "enforce_latex_text"),
            ("1.3.0", "enforce_latex_text_and_figure_chain"),
        ):
            with self.subTest(version=version):
                policy = selected_policy("latex")
                policy.update(protocol_version=version, mode=mode)
                policy.pop("paper_source")
                for binding in policy["figure_bindings"]:
                    binding["latex_label"] = binding.pop("carrier_locator")["value"]
                state = {
                    "paper_framework": {"claim_consumption_policy": policy},
                    "subproblems": {"Q1": {
                        "analysis_evidence_dispositions": [deepcopy(disposition)]
                    }},
                }
                result = runtime_assurance._current_structured_rejections(state, ["Q1"])
                self.assertFalse(result["Q1"]["blocks_primary"], result)
                self.assertFalse(result["Q1"]["blocks_model"], result)
                self.assertEqual(result["Q1"]["conflicts"], [], result)
                self.assertFalse(validate_user_execution._uses_structured_rejection_policy(state))

    def test_resolver_loads_only_the_selected_carrier_adapter(self):
        example = yaml.safe_load((ROOT / "state/project_state.example.yaml").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / "state").mkdir()
            state_path = project / "state/project_state.yaml"

            latex_state = deepcopy(example)
            latex_state["paper_framework"]["claim_consumption_policy"] = selected_policy("latex")
            state_path.write_text(yaml.safe_dump(latex_state, allow_unicode=True), encoding="utf-8")
            latex_plan = resolve_runtime.resolve_runtime("latex", project_root=project)
            self.assertIn("scripts/latex_delivery.py", latex_plan["load_order"])
            self.assertNotIn("scripts/claim_docx.py", latex_plan["load_order"])
            self.assertEqual(latex_plan["claim_consumption_integration"]["entrypoint"],
                             "final_latex/paper.tex")

            docx_state = deepcopy(example)
            docx_state["paper_framework"]["claim_consumption_policy"] = selected_policy("docx")
            state_path.write_text(yaml.safe_dump(docx_state, allow_unicode=True), encoding="utf-8")
            docx_plan = resolve_runtime.resolve_runtime("docx", project_root=project)
            self.assertIn("scripts/claim_docx.py", docx_plan["load_order"])
            self.assertNotIn("scripts/latex_delivery.py", docx_plan["claim_consumption_integration"]["resources"])
            self.assertEqual(docx_plan["claim_consumption_integration"]["carrier_format"], "docx")
            wrong_carrier = resolve_runtime.resolve_runtime("latex", project_root=project)
            self.assertNotIn("claim_consumption_integration", wrong_carrier)

            legacy_state = deepcopy(example)
            legacy_state["paper_framework"]["claim_consumption_policy"] = {
                "protocol_version": "1.1.0", "mode": "propagate",
                "required_consumptions": [{
                    "claim_id": "Q1_answer", "fragment_kinds": ["question_result_text"],
                }],
            }
            state_path.write_text(
                yaml.safe_dump(legacy_state, allow_unicode=True), encoding="utf-8"
            )
            propagate_plan = resolve_runtime.resolve_runtime("latex", project_root=project)
            self.assertNotIn("claim_consumption_integration", propagate_plan)
            self.assertNotIn("scripts/claim_docx.py", propagate_plan["load_order"])

    def test_docx_artifact_list_cannot_substitute_an_unselected_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / "draft_docx").mkdir()
            (project / "draft_docx/selected.docx").write_bytes(b"selected")
            (project / "draft_docx/other.docx").write_bytes(b"other")
            state = {
                "paper_framework": {"claim_consumption_policy": selected_policy("docx")},
                "artifacts": {"docx": ["draft_docx/other.docx"]},
            }
            state["paper_framework"]["claim_consumption_policy"]["paper_source"][
                "entrypoint"
            ] = "draft_docx/selected.docx"
            issues = sync_project._docx_issues(project, state)
            self.assertIn("artifacts.docx未包含选定B2 paper_source", issues)


class SelectedLatexEntrypointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name).resolve()
        (self.project / "state").mkdir()
        (self.project / "final_latex").mkdir()
        (self.project / "figures").mkdir()
        self.main = self.project / "final_latex/paper.tex"
        self.image = self.project / "figures/q1.png"
        self.image.write_bytes(b"figure bytes")
        self.main.write_text(
            "\\documentclass{article}\n\\usepackage{graphicx}\n\\begin{document}\n"
            "\\begin{figure}\\includegraphics{../figures/q1.png}"
            "\\caption{Result}\\label{fig:q1}\\end{figure}\n"
            "See \\ref{fig:q1}.\\end{document}\n", encoding="utf-8",
        )
        (self.project / "state/project_state.yaml").write_text(yaml.safe_dump({
            "paper_framework": {"claim_consumption_policy": selected_policy("latex")},
        }, allow_unicode=True), encoding="utf-8")
        self.gate = {
            "status": "passed", "policy_protocol_version": "1.5.0",
            "mode": "enforce_selected_paper_claim_chain", "carrier_format": "latex",
            "human_semantic_coverage": "not_assessed", "issues": [],
            "observed_sources": {"project": {}, "skill": {}},
            "figure_image_paths": ["figures/q1.png"],
            "figure_graphic_bindings": [{
                "image_token": "../figures/q1.png", "image_path": "figures/q1.png",
            }],
        }

    def test_v5_uses_declared_entrypoint_and_live_selected_paper_gate(self):
        self.assertTrue(latex_delivery._v5_policy_declared(self.main))
        with patch.object(claim_consumption, "formal_paper_gate", return_value=self.gate):
            options = latex_delivery._v5_live_figure_options(self.main)
            snapshot = latex_delivery.source_bundle_snapshot(self.main, **options)
        self.assertEqual([row["path"] for row in snapshot["source_files"]],
                         ["figures/q1.png", "final_latex/paper.tex"])

    def test_render_paper_prefers_declared_entrypoint_over_legacy_main(self):
        legacy = self.project / "final_latex/main.tex"
        legacy.write_text("\\documentclass{article}\n", encoding="utf-8")
        selected = render_paper.resolve_main(
            self.main.parent, None, {"project_main": "main.tex"},
        )
        self.assertEqual(selected.resolve(), self.main.resolve())

    def test_selected_entrypoint_gets_current_v5_audit_and_compile_proof(self):
        framework = self.project / "模型论文框架.md"
        framework.write_text("# framework", encoding="utf-8")
        pdf = self.main.with_suffix(".pdf")
        pdf.write_bytes(b"unit PDF")
        self.main.with_suffix(".log").write_text("synthetic success\n", encoding="utf-8")
        self.main.with_suffix(".fls").write_text(
            f"PWD {self.main.parent}\nINPUT paper.tex\nINPUT ../figures/q1.png\n",
            encoding="utf-8",
        )
        options = {
            "project_root": self.project,
            "allowed_external_graphics": {"../figures/q1.png": self.image},
        }
        audit = {
            "audit_schema_version": "2.0.0", "status": "passed", "mode": "formal",
            "main": "paper.tex",
            **latex_delivery.source_bundle_snapshot(self.main, **options),
            "framework_sha256": latex_delivery.sha256_file(framework),
            "claim_figure_gate": self.gate,
        }
        (self.main.parent / "latex_audit_report.yaml").write_text(
            yaml.safe_dump(audit, allow_unicode=True), encoding="utf-8",
        )
        with patch.object(claim_consumption, "formal_paper_gate", return_value=self.gate):
            report = latex_delivery.write_compile_report(
                project=self.main.parent, main=self.main, profile="mcm_icm",
                engine="pdflatex", bibliography="none", sequence=["pdflatex"],
            )
            issues = latex_delivery.verify_compile_report(
                project=self.main.parent, main=self.main, pdf=pdf, report=report,
            )
        self.assertEqual(report["report_schema_version"], "5.0.0")
        self.assertEqual(report["main"], "paper.tex")
        self.assertEqual(report["recorder"], "paper.fls")
        self.assertEqual(issues, [])

    def test_latex_audit_rejects_a_nonselected_entrypoint(self):
        other = self.project / "final_latex/main.tex"
        other.write_text(self.main.read_text(encoding="utf-8"), encoding="utf-8")
        with patch.object(claim_consumption, "formal_paper_gate", return_value=self.gate):
            kind, gate = audit_latex_project._claim_gate(other)
        self.assertEqual(kind, "figure")
        self.assertEqual(gate["status"], "failed")
        self.assertTrue(any("paper_source" in issue for issue in gate["issues"]))

    def test_docx_policy_never_selects_latex_v5(self):
        state_path = self.project / "state/project_state.yaml"
        state_path.write_text(yaml.safe_dump({
            "paper_framework": {"claim_consumption_policy": selected_policy("docx")},
        }, allow_unicode=True), encoding="utf-8")
        self.assertFalse(latex_delivery._v5_policy_declared(self.main))


class DocxSubmissionClosureTests(unittest.TestCase):
    def test_docx_submission_fails_closed_without_pdf_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve()
            (project / "state").mkdir()
            (project / "draft_docx").mkdir()
            (project / "draft_docx/paper.docx").write_bytes(b"docx")
            (project / "state/project_state.yaml").write_text(yaml.safe_dump({
                "paper_framework": {"claim_consumption_policy": selected_policy("docx")},
            }, allow_unicode=True), encoding="utf-8")
            gate = {
                "status": "passed", "policy_protocol_version": "1.5.0",
                "mode": "enforce_selected_paper_claim_chain", "carrier_format": "docx",
                "human_semantic_coverage": "not_assessed", "issues": [],
                "observed_sources": {"project": {}, "skill": {}},
                "figure_image_paths": ["figures/q1.png"],
            }
            with (patch.object(claim_consumption, "formal_paper_gate", return_value=gate),
                  patch.object(latex_delivery, "verify_compile_report") as compile_verifier):
                report = validate_submission_package.validate_package(
                    project, project / "submission/missing.zip")
            compile_verifier.assert_not_called()
            self.assertEqual(report["status"], "failed")
            self.assertTrue(any("DOCX到正式PDF编译证明" in issue
                                for issue in report["issues"]), report)


class SelectedPolicyStructuredSyncTests(unittest.TestCase):
    """Prove exact 1.5 inherits the existing atomic B12 rejection writer."""

    save_projection = rejection_fixture.B2b6RejectionReturnTests.save_projection
    set_caption = rejection_fixture.B2b6RejectionReturnTests.set_caption
    reload = rejection_fixture.B2b6RejectionReturnTests.reload
    assert_accepted = rejection_fixture.B2b6RejectionReturnTests.assert_accepted
    assert_old_proof_rejected = rejection_fixture.B2b6RejectionReturnTests.assert_old_proof_rejected
    assert_current_proof = rejection_fixture.B2b6RejectionReturnTests.assert_current_proof
    numerical_snapshot = rejection_fixture.B2b6RejectionReturnTests.numerical_snapshot
    package = rejection_fixture.B2b6RejectionReturnTests.package
    disposition = rejection_fixture.B2b6RejectionReturnTests.disposition
    sync_with = rejection_fixture.B2b6RejectionReturnTests.sync_with

    @classmethod
    def setUpClass(cls):
        rejection_fixture.B2b6RejectionReturnTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        rejection_fixture.B2b6RejectionReturnTests.tearDownClass.__func__(cls)

    def setUp(self):
        rejection_fixture.B2b6RejectionReturnTests.setUp(self)
        policy = self.state["paper_framework"]["claim_consumption_policy"]
        policy.update(
            protocol_version="1.5.0",
            mode="enforce_selected_paper_claim_chain",
            paper_source={"format": "latex", "entrypoint": "final_latex/main.tex"},
        )
        for binding in policy["figure_bindings"]:
            label = binding.pop("latex_label")
            binding["carrier_locator"] = {"kind": "latex_label", "value": label}
        for fragment in self.state["paper_framework"]["paper_fragments"]:
            fragment.setdefault("source_file", "final_latex/main.tex")
        self.save_projection()

    def tearDown(self):
        rejection_fixture.B2b6RejectionReturnTests.tearDown(self)

    def proof(self, *, real_compile=False):
        entrypoint = self.state["paper_framework"]["claim_consumption_policy"][
            "paper_source"
        ]["entrypoint"]
        main = self.root / entrypoint
        findings = audit_latex_project.audit_project(
            main, framework_path=self.root / "模型论文框架.md", require_framework=True,
        )
        self.assertEqual(findings, [], findings)
        audit = audit_latex_project.write_audit_report(
            main_file=main, findings=findings,
            framework_path=self.root / "模型论文框架.md",
        )
        self.assertEqual(audit["status"], "passed", audit)
        if real_compile:
            command = [
                "xelatex", "-interaction=nonstopmode", "-halt-on-error",
                "-file-line-error", "-recorder", main.name,
            ]
            for _ in range(2):
                compiled = subprocess.run(
                    command, cwd=main.parent, capture_output=True, text=True,
                    encoding="utf-8", errors="replace", check=False,
                )
                self.assertEqual(
                    compiled.returncode, 0,
                    compiled.stdout[-3000:] + compiled.stderr[-3000:],
                )
        else:
            main.with_suffix(".pdf").write_bytes(b"%PDF-synthetic-B2c-proof-fixture")
            main.with_suffix(".log").write_text(
                "This is XeTeX\nSynthetic B2c recorder fixture.\n", encoding="utf-8",
            )
            gate = claim_consumption.formal_paper_gate(self.root)
            options = {
                "project_root": self.root,
                "allowed_external_graphics": {
                    row["image_token"]: self.root / row["image_path"]
                    for row in gate["figure_graphic_bindings"]
                },
            }
            inputs = latex_delivery.source_bundle_files(main, **options)
            with main.with_suffix(".fls").open("w", encoding="utf-8") as recorder:
                recorder.write(f"PWD {main.parent.resolve()}\n")
                for path in inputs:
                    token = (
                        path.relative_to(main.parent).as_posix()
                        if path.is_relative_to(main.parent)
                        else "../" + path.relative_to(self.root).as_posix()
                    )
                    recorder.write(f"INPUT {token}\n")
        profile = latex_delivery.current_profile_config("diangong")
        report = latex_delivery.write_compile_report(
            project=main.parent, main=main, profile="diangong", engine="xelatex",
            bibliography="none", sequence=["xelatex", "xelatex"],
            profile_config=profile,
        )
        self.assertEqual(
            latex_delivery.verify_audit_report(
                project=main.parent, main=main, report=audit,
            ), [],
        )
        self.assertEqual(
            latex_delivery.verify_compile_report(
                project=main.parent, main=main,
                pdf=main.with_suffix(".pdf"), report=report,
            ), [],
        )
        return audit, report

    def test_live_1_5_gate_compile_proof_and_submission_package_replay(self):
        selected = self.latex / "paper.tex"
        (self.latex / "main.tex").replace(selected)
        self.state["paper_framework"]["claim_consumption_policy"]["paper_source"][
            "entrypoint"
        ] = "final_latex/paper.tex"
        self.save_projection()
        self.reload()

        gate = claim_consumption.formal_paper_gate(self.root)
        self.assertEqual(gate["status"], "passed", gate)
        self.assertEqual(gate["policy_protocol_version"], "1.5.0")
        self.assertEqual(gate["human_semantic_coverage"], "not_assessed")

        audit, compile_report = self.proof()
        self.assertEqual(audit["audit_schema_version"], "2.0.0", audit)
        self.assertEqual(compile_report["report_schema_version"], "5.0.0", compile_report)
        self.assertEqual(compile_report["main"], "paper.tex", compile_report)
        self.assertEqual(compile_report["recorder"], "paper.fls", compile_report)
        proof = audit["claim_figure_gate"]
        self.assertEqual(proof["status"], "passed", proof)
        self.assertEqual(proof["policy_protocol_version"], "1.5.0", proof)
        self.assertEqual(proof["human_semantic_coverage"], "not_assessed", proof)
        audit_path = self.latex / "latex_audit_report.yaml"
        self.assertEqual(compile_report["audit_status"], "passed", compile_report)
        self.assertEqual(compile_report["latex_audit_report"], "latex_audit_report.yaml")
        self.assertEqual(
            compile_report["latex_audit_report_sha256"],
            latex_delivery.sha256_file(audit_path),
        )

        tampered_audit = deepcopy(audit)
        tampered_audit["main"] = "../paper.tex"
        audit_issues = latex_delivery.verify_audit_report(
            project=self.latex, main=selected, report=tampered_audit,
        )
        self.assertTrue(any("latex_audit_report.main" in issue
                            for issue in audit_issues), audit_issues)
        for field, value in (
            ("main", "C:/outside/paper.tex"),
            ("pdf", "../paper.pdf"),
        ):
            with self.subTest(tampered_compile_field=field):
                tampered_compile = deepcopy(compile_report)
                tampered_compile[field] = value
                compile_issues = latex_delivery.verify_compile_report(
                    project=self.latex, main=selected,
                    pdf=selected.with_suffix(".pdf"), report=tampered_compile,
                )
                self.assertTrue(any(f"compile_report.{field}" in issue
                                    for issue in compile_issues), compile_issues)

        bound, bound_issues = bound_compile_files(self.root, self.state)
        self.assertEqual(bound_issues, [], bound_issues)
        self.assertEqual(
            {path.relative_to(self.root).as_posix() for path in bound},
            {"final_latex/paper.fls", "final_latex/paper.log"},
        )
        required, requirement_issues = reproducibility_requirements(self.root, self.state)
        self.assertEqual(requirement_issues, [], requirement_issues)
        self.assertIn("final_latex/paper.tex", required)
        self.assertIn("final_latex/paper.pdf", required)
        self.assertNotIn("final_latex/main.tex", required)
        self.assertNotIn("final_latex/main.pdf", required)

        package = self.package()
        with zipfile.ZipFile(package) as archive:
            packed = set(archive.namelist())
        self.assertTrue({
            "final_latex/paper.tex", "final_latex/paper.pdf",
            "final_latex/paper.fls", "final_latex/paper.log",
        }.issubset(packed), packed)
        self.assertNotIn("final_latex/main.tex", packed)
        self.assertNotIn("final_latex/main.pdf", packed)
        package_report = validate_submission_package.validate_package(self.root, package)
        self.assertEqual(package_report["status"], "passed", package_report)
        sync_report = sync_project.synchronize(
            self.root, write=False, delivery_scope="submission"
        )
        self.assertEqual(sync_report["claim_paper_gate"]["status"], "passed", sync_report)
        self.assertEqual(sync_report["status"], "passed", sync_report)

    def test_compile_report_main_must_match_selected_entrypoint_without_artifact_hint(self):
        report_path = self.latex / "compile_report.yaml"
        report_path.write_text(yaml.safe_dump({
            "report_schema_version": "5.0.0",
            "main": "other.tex",
            "recorder": "other.fls",
            "log": "other.log",
        }), encoding="utf-8")
        _, issues = bound_compile_files(self.root, self.state)
        self.assertTrue(any("选定B2 paper_source" in issue for issue in issues), issues)

    def test_selected_entrypoint_fixes_pdf_identity_despite_conflicting_artifact(self):
        self.state.setdefault("artifacts", {})["compiled_pdf"] = "final_latex/other.pdf"
        required, issues = reproducibility_requirements(self.root, self.state)
        self.assertIn("final_latex/main.pdf", required)
        self.assertNotIn("final_latex/other.pdf", required)
        self.assertTrue(any("artifacts.compiled_pdf" in issue for issue in issues), issues)
        _, selected_pdf, _ = sync_project._latex_artifact_paths(self.root, self.state)
        self.assertEqual(selected_pdf, self.latex / "main.pdf")
        self.assertTrue(any("artifacts.compiled_pdf" in issue for issue in
                            sync_project._compile_artifact_issues(self.root, self.state)))
        self.assertEqual(
            validate_submission_package._current_compiled_pdf(self.root, self.state),
            self.latex / "main.pdf",
        )

    @unittest.skipUnless(shutil.which("xelatex"), "XeLaTeX is not installed")
    def test_real_xelatex_1_5_selected_carrier_proof_and_package(self):
        gate = claim_consumption.formal_paper_gate(self.root)
        self.assertEqual(gate["status"], "passed", gate)
        audit, compile_report = self.proof(real_compile=True)
        self.assertEqual(audit["audit_schema_version"], "2.0.0", audit)
        self.assertEqual(compile_report["report_schema_version"], "5.0.0", compile_report)
        package = self.package()
        package_report = validate_submission_package.validate_package(self.root, package)
        self.assertEqual(package_report["status"], "passed", package_report)

    def test_auxiliary_rejection_keeps_primary_state_under_1_5(self):
        before = self.state["subproblems"]["Q1"]["result_quality_status"]
        report = self.sync_with(self.disposition(
            identifier="E15", target="aux_claim", action="reject",
            impact_scope="auxiliary_wording",
        ))
        self.assertEqual(report["claim_rejection_transitions"], [], report)
        self.assertEqual(self.state["project"]["current_phase"], "writing_latex")
        self.assertEqual(self.state["subproblems"]["Q1"]["result_quality_status"], before)

    def test_core_rejection_returns_to_solve_validate_under_1_5(self):
        report = self.sync_with(self.disposition(
            identifier="E15", target="answer_claim", action="reject",
            impact_scope="core_answer", return_stage="solve_validate",
        ))
        self.assertEqual(report["claim_rejection_transitions"][0]["event"],
                         "core_answer_rejected", report)
        self.assertEqual(self.state["project"]["current_phase"], "solve_validate")
        self.assertEqual(self.state["next_gate"]["module"], "solve_validate")

    def test_model_rejection_returns_to_model_design_under_1_5(self):
        report = self.sync_with(self.disposition(
            identifier="E15", target="answer_claim", action="reject",
            impact_scope="model_validity", return_stage="model_design",
        ))
        self.assertEqual(report["claim_rejection_transitions"][0]["event"],
                         "model_validity_rejected", report)
        self.assertEqual(self.state["project"]["current_phase"], "model_design")
        self.assertEqual(self.state["next_gate"]["module"], "model_design")
        self.assertEqual(self.state["subproblems"]["Q1"]["human_model_approval_status"],
                         "stale")

    def test_1_5_state_validator_enforces_structured_rejection_profile(self):
        row = self.disposition(
            identifier="E15", target="answer_claim", action="reject",
            impact_scope="core_answer", return_stage="solve_validate",
        )
        row.pop("impact_scope")
        row.pop("return_stage")
        self.state["subproblems"]["Q1"]["analysis_evidence_dispositions"] = [row]
        self.save_projection()
        issues = validate_project_state.validate_state_file(
            self.root / "state/project_state.yaml", project_root=self.root)
        self.assertTrue(any("impact_scope" in issue for issue in issues), issues)

        row["impact_scope"] = "core_answer"
        row["return_stage"] = "model_design"
        self.save_projection()
        issues = validate_project_state.validate_state_file(
            self.root / "state/project_state.yaml", project_root=self.root)
        self.assertTrue(any("return_stage must be solve_validate" in issue
                            for issue in issues), issues)
        self.assertTrue(any("project.current_phase" in issue for issue in issues), issues)
        self.assertTrue(any("next_gate.module" in issue for issue in issues), issues)

    def test_legacy_1_0_to_1_4_do_not_activate_selected_paper_gate(self):
        policy = self.state["paper_framework"]["claim_consumption_policy"]
        policy.pop("paper_source")
        for binding in policy["figure_bindings"]:
            binding["latex_label"] = binding.pop("carrier_locator")["value"]
        main = self.latex / "main.tex"
        main.write_text(main.read_text(encoding="utf-8").replace(
            "\\documentclass{article}",
            "\\documentclass{article}\n"
            "\\DeclareRobustCommand{\\fmt}[1]{\\textbf{#1}}",
        ).replace("\\begin{document}", "\\begin{document}\n\\fmt{Introduction.}"),
                        encoding="utf-8")
        for version, mode in (
            ("1.0.0", "observe"),
            ("1.1.0", "propagate"),
            ("1.2.0", "enforce_latex_text"),
            ("1.3.0", "enforce_latex_text_and_figure_chain"),
            ("1.4.0", "enforce_latex_text_and_figure_chain"),
        ):
            with self.subTest(version=version):
                policy.update(protocol_version=version, mode=mode)
                self.save_projection()
                gate = claim_consumption.formal_paper_gate(self.root)
                self.assertEqual(gate["status"], "not_applicable", gate)
                self.assertEqual(gate["figure_image_paths"], [])
        policy.update(protocol_version="1.4.0",
                      mode="enforce_latex_text_and_figure_chain")
        self.save_projection()
        legacy_gate = claim_consumption.formal_figure_gate(self.root)
        self.assertEqual(legacy_gate["status"], "passed", legacy_gate)


if __name__ == "__main__":
    unittest.main()
