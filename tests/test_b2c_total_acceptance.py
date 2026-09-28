"""End-to-end acceptance for the B2 1.5 selected-paper claim chain.

These tests keep the existing synthetic accepted workbook and Figure-source
chain.  They change only the selected paper carrier so the new protocol is
exercised against live B1 evidence instead of mocked gate reports.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest
import zipfile
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import claim_consumption as claims  # noqa: E402
import runtime_assurance  # noqa: E402
import sync_project  # noqa: E402
from tests import test_b2b4_formal_figure_gate as legacy_fixture  # noqa: E402
from tests.test_model_code_conformance import save  # noqa: E402


SELECTED_PAIR = ("1.5.0", "enforce_selected_paper_claim_chain")


class B2cSelectedLatexAcceptanceTests(unittest.TestCase):
    """Reuse the accepted B1/Figure fixture with the 1.5 LaTeX carrier."""

    save_projection = legacy_fixture.B2b4FormalFigureGateTests.save_projection
    set_caption = legacy_fixture.B2b4FormalFigureGateTests.set_caption

    @classmethod
    def setUpClass(cls):
        legacy_fixture.B2b4FormalFigureGateTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        legacy_fixture.B2b4FormalFigureGateTests.tearDownClass.__func__(cls)

    def setUp(self):
        legacy_fixture.B2b4FormalFigureGateTests.setUp(self)
        policy = self.state["paper_framework"]["claim_consumption_policy"]
        policy.update(
            protocol_version=SELECTED_PAIR[0],
            mode=SELECTED_PAIR[1],
            paper_source={"format": "latex", "entrypoint": "final_latex/main.tex"},
        )
        self.binding = policy["figure_bindings"][0]
        label = self.binding.pop("latex_label")
        self.binding["carrier_locator"] = {"kind": "latex_label", "value": label}
        self.save_projection()
        self._baseline_state = deepcopy(self.state)
        self._baseline_registry = self.registry_row
        self._baseline_files = {
            path.relative_to(self.root).as_posix(): path.read_bytes()
            for path in (
                self.latex / "main.tex",
                self.latex / "abstract.tex",
                self.latex / "body.tex",
                self.latex / "result.tex",
                self.root / self.state["subproblems"]["Q1"]["solution_workbook"],
            )
        }

    def tearDown(self):
        legacy_fixture.B2b4FormalFigureGateTests.tearDown(self)

    def _restore_baseline(self) -> None:
        self.state = deepcopy(self._baseline_state)
        self.fragments = self.state["paper_framework"]["paper_fragments"]
        self.binding = self.state["paper_framework"]["claim_consumption_policy"][
            "figure_bindings"
        ][0]
        self.registry_row = self._baseline_registry
        for relative, payload in self._baseline_files.items():
            (self.root / relative).write_bytes(payload)
        self.save_projection()

    def assert_failed_without_human_approval(self, gate: dict) -> None:
        self.assertEqual(gate["status"], "failed", gate)
        self.assertEqual(gate["human_semantic_coverage"], "not_assessed", gate)

    def test_static_modular_latex_is_a_real_selected_carrier_pass(self):
        audit = claims.inspect_project(self.root)
        gate = claims.formal_paper_gate(self.root)
        self.assertEqual(audit["carrier_format"], "latex", audit)
        self.assertEqual(audit["paper_scan"]["status"], "scanned", audit)
        self.assertGreaterEqual(len(audit["paper_scan"]["active_files"]), 4, audit)
        self.assertEqual(gate["status"], "passed", gate)
        self.assertEqual((gate["policy_protocol_version"], gate["mode"]), SELECTED_PAIR)
        self.assertEqual(gate["figure_image_paths"], ["figures/q1_f01.png"])
        self.assertEqual(audit["human_semantic_coverage"], "not_assessed")
        self.assertEqual(gate["human_semantic_coverage"], "not_assessed")

    def test_static_single_file_latex_is_in_scope(self):
        main_text = (
            "\\documentclass{article}\n"
            "\\usepackage{graphicx}\n"
            "\\begin{document}\n"
            "Answer: 100.0.\n"
            "Result: 100.00.\n"
            "\\begin{figure}\n"
            "\\centering\n"
            "\\includegraphics{../figures/q1_f01.png}\n"
            "\\caption{Result evidence 100.00 ratio.}\n"
            "\\label{fig:q1-f01}\n"
            "\\end{figure}\n"
            "See Figure~\\ref{fig:q1-f01}.\n"
            "\\end{document}\n"
        )
        (self.latex / "main.tex").write_text(main_text, encoding="utf-8")
        for fragment in self.fragments:
            fragment["source_file"] = "final_latex/main.tex"
        cells = self.registry_row.split("|")
        cells[-2] = " final_latex/main.tex:12 "
        self.registry_row = "|".join(cells)
        self.save_projection()

        audit = claims.inspect_project(self.root)
        gate = claims.formal_paper_gate(self.root)
        self.assertEqual(audit["paper_scan"]["active_files"], ["final_latex/main.tex"], audit)
        self.assertEqual(gate["status"], "passed", gate)
        self.assertEqual(gate["human_semantic_coverage"], "not_assessed")

    def test_latex_selection_rejects_explicit_docx_scope_after_running_same_gate(self):
        report = sync_project.synchronize(self.root, write=False, delivery_scope="docx")
        self.assertEqual(report["claim_paper_gate"]["status"], "passed", report)
        self.assertTrue(any("conflicts with selected B2 paper_source format latex" in issue
                            for issue in report["issues"]), report)

    def test_dynamic_include_and_macro_generated_caption_fail_closed(self):
        main = self.latex / "main.tex"
        main.write_text(
            main.read_text(encoding="utf-8").replace(
                "\\input{body}",
                "\\newcommand{\\selectedbody}{body}\n\\input{\\selectedbody}",
            ),
            encoding="utf-8",
        )
        self.assert_failed_without_human_approval(claims.formal_paper_gate(self.root))

        self._restore_baseline()
        result = self.latex / "result.tex"
        result.write_text(
            result.read_text(encoding="utf-8").replace(
                "\\caption{Result evidence 100.00 ratio.}",
                "\\newcommand{\\acceptedcaption}{Result evidence 100.00 ratio.}\n"
                "\\caption{\\acceptedcaption}",
            ),
            encoding="utf-8",
        )
        gate = claims.formal_paper_gate(self.root)
        self.assert_failed_without_human_approval(gate)
        self.assertTrue(
            gate.get("audit_status") != "observed"
            or any(row.get("identity_status") != "matched"
                   for row in gate.get("figure_identity_checks", [])),
            gate,
        )

    def test_claim_visibility_macro_fails_but_literal_text_formatting_passes(self):
        body = self.latex / "body.tex"
        original = body.read_text(encoding="utf-8")
        body.write_text("\\phantom{" + original.strip() + "}\n", encoding="utf-8")
        gate = claims.formal_paper_gate(self.root)
        self.assert_failed_without_human_approval(gate)
        self.assertTrue(any("rendering macro" in issue for issue in gate["issues"]), gate)

        body.write_text(
            "\\makeatletter\\@gobble{" + original.strip() + "}\\makeatother\n",
            encoding="utf-8",
        )
        gate = claims.formal_paper_gate(self.root)
        self.assert_failed_without_human_approval(gate)
        self.assertTrue(any("unassessed body macro" in issue
                            for issue in gate["issues"]), gate)

        body.write_text("\\makeatletter\\@gobble Result: 100.00.\n", encoding="utf-8")
        gate = claims.formal_paper_gate(self.root)
        self.assert_failed_without_human_approval(gate)
        self.assertTrue(any("unassessed body macro" in issue
                            for issue in gate["issues"]), gate)

        body.write_text(
            "\\makeatletter\\@gobbletwo XResult: 100.00.\n", encoding="utf-8"
        )
        gate = claims.formal_paper_gate(self.root)
        self.assert_failed_without_human_approval(gate)
        self.assertTrue(any("unassessed body macro" in issue
                            for issue in gate["issues"]), gate)

        body.write_text(
            "\\begin{lrbox}{\\somebox}\n" + original.strip()
            + "\n\\end{lrbox}\n",
            encoding="utf-8",
        )
        gate = claims.formal_paper_gate(self.root)
        self.assert_failed_without_human_approval(gate)
        self.assertTrue(any("unassessed body environment" in issue
                            for issue in gate["issues"]), gate)

        body.write_text("\\textbf{" + original.strip() + "}\n", encoding="utf-8")
        gate = claims.formal_paper_gate(self.root)
        self.assertEqual(gate["status"], "passed", gate)

    def test_project_local_macro_generated_claim_fails_but_unrelated_macro_continues(self):
        main = self.latex / "main.tex"
        main.write_text(
            main.read_text(encoding="utf-8").replace(
                "\\documentclass{article}",
                "\\documentclass{article}\n\\usepackage{localclaims}",
            ),
            encoding="utf-8",
        )
        (self.latex / "localclaims.sty").write_text(
            "\\input{localdefs}\n",
            encoding="utf-8",
        )
        (self.latex / "localdefs.tex").write_text(
            "\\DeclareRobustCommand{\\hiddenclaim}{Globally optimal.}\n"
            "\\newcommand{\\decorative}{Decorative note.}\n",
            encoding="utf-8",
        )
        body = self.latex / "body.tex"
        body_original = body.read_text(encoding="utf-8")
        body.write_text(body_original + "\\hiddenclaim\n", encoding="utf-8")
        self.state["subproblems"]["Q1"]["optimality_claim"] = "heuristic"
        self.save_projection()
        gate = claims.formal_paper_gate(self.root)
        self.assert_failed_without_human_approval(gate)
        self.assertTrue(any("custom macro" in issue for issue in gate["issues"]), gate)

        (self.latex / "localclaims.sty").write_text(
            "\\input localdefs.tex\n", encoding="utf-8"
        )
        gate = claims.formal_paper_gate(self.root)
        self.assert_failed_without_human_approval(gate)
        self.assertEqual(gate.get("audit_status"), "not_assessed", gate)
        (self.latex / "localclaims.sty").write_text(
            "\\input{localdefs}\n", encoding="utf-8"
        )

        (self.latex / "localdefs.tex").write_text(
            "\\NewDocumentCommand{\\hiddenclaim}{}{Globally optimal.}\n"
            "\\newcommand{\\decorative}{Decorative note.}\n",
            encoding="utf-8",
        )
        self.assert_failed_without_human_approval(claims.formal_paper_gate(self.root))

        (self.latex / "localdefs.tex").write_text(
            "\\newcommand{\\strongclaim}{Globally optimal.}\n"
            "\\let\\hiddenclaim\\strongclaim\n"
            "\\newcommand{\\decorative}{Decorative note.}\n",
            encoding="utf-8",
        )
        self.assert_failed_without_human_approval(claims.formal_paper_gate(self.root))

        (self.latex / "localdefs.tex").write_text(
            "\\makeatletter\\let\\textbf\\@gobble\\makeatother\n"
            "\\newcommand{\\decorative}{Decorative note.}\n",
            encoding="utf-8",
        )
        body.write_text("\\textbf{" + body_original.strip() + "}\n", encoding="utf-8")
        self.assert_failed_without_human_approval(claims.formal_paper_gate(self.root))

        (self.latex / "localdefs.tex").write_text(
            "\\newcommand{\\decorative}[1]{Decorative note.}\n",
            encoding="utf-8",
        )
        body.write_text("\\decorative{" + body_original.strip() + "}\n", encoding="utf-8")
        self.assert_failed_without_human_approval(claims.formal_paper_gate(self.root))

        (self.latex / "localclaims.sty").write_text(
            "\\RequirePackage{etoolbox}\n\\csdef{textbf}#1{}\n",
            encoding="utf-8",
        )
        body.write_text("\\textbf{" + body_original.strip() + "}\n", encoding="utf-8")
        gate = claims.formal_paper_gate(self.root)
        self.assert_failed_without_human_approval(gate)
        self.assertEqual(gate.get("audit_status"), "not_assessed", gate)
        (self.latex / "localclaims.sty").write_text(
            "\\input{localdefs}\n", encoding="utf-8"
        )

        main_text = main.read_text(encoding="utf-8")
        main.write_text(
            main_text.replace(
                "\\documentclass{article}",
                "\\documentclass{article}\n"
                "\\makeatletter\\@namedef{textbf}#1{}\\makeatother",
            ),
            encoding="utf-8",
        )
        gate = claims.formal_paper_gate(self.root)
        self.assert_failed_without_human_approval(gate)
        self.assertEqual(gate.get("audit_status"), "not_assessed", gate)
        main.write_text(main_text, encoding="utf-8")

        (self.latex / "localdefs.tex").write_text(
            "\\ExplSyntaxOn\n"
            "\\cs_new:Npn \\hiddenclaim {Globally optimal.}\n"
            "\\ExplSyntaxOff\n"
            "\\newcommand{\\decorative}{Decorative note.}\n",
            encoding="utf-8",
        )
        body.write_text(body_original + "\\hiddenclaim\n", encoding="utf-8")
        self.assert_failed_without_human_approval(claims.formal_paper_gate(self.root))

        (self.latex / "extra.tex").write_text("Globally optimal.\n", encoding="utf-8")
        (self.latex / "localdefs.tex").write_text(
            "\\newcommand{\\more}{\\input{extra}}\n"
            "\\newcommand{\\decorative}{Decorative note.}\n",
            encoding="utf-8",
        )
        body.write_text(body.read_text(encoding="utf-8").replace("\\hiddenclaim", "\\more"),
                        encoding="utf-8")
        self.assert_failed_without_human_approval(claims.formal_paper_gate(self.root))

        (self.latex / "localdefs.tex").write_text(
            "\\newcommand{\\numericclaim}{Other result 99.00.}\n"
            "\\newcommand{\\decorative}{Decorative note.}\n",
            encoding="utf-8",
        )
        body.write_text(body.read_text(encoding="utf-8").replace("\\more", ""),
                        encoding="utf-8")
        main.write_text(main.read_text(encoding="utf-8").replace(
            "\\begin{document}", "\\begin{document}\n\\numericclaim"), encoding="utf-8")
        self.assert_failed_without_human_approval(claims.formal_paper_gate(self.root))

        main.write_text(main.read_text(encoding="utf-8").replace("\\numericclaim", "\\decorative"),
                        encoding="utf-8")
        gate = claims.formal_paper_gate(self.root)
        self.assertEqual(gate["status"], "passed", gate)

    def test_unbounded_tex_definitions_and_preamble_rendering_fail_closed(self):
        main = self.latex / "main.tex"
        body = self.latex / "body.tex"
        main_original = main.read_text(encoding="utf-8")
        body_original = body.read_text(encoding="utf-8")

        main.write_text(
            main_original.replace(
                "\\documentclass{article}",
                "\\documentclass{article}\n\\def\\!#1{}",
            ),
            encoding="utf-8",
        )
        body.write_text("\\!{" + body_original.strip() + "}\n", encoding="utf-8")
        gate = claims.formal_paper_gate(self.root)
        self.assert_failed_without_human_approval(gate)
        self.assertTrue(any("unbounded TeX redefinition" in issue
                            for issue in gate["issues"]), gate)

        main.write_text(
            main_original.replace(
                "\\documentclass{article}",
                "\\documentclass{article}\n"
                "\\ExplSyntaxOn\n\\cs_set:cpn { textbf } #1 {}\n\\ExplSyntaxOff",
            ),
            encoding="utf-8",
        )
        body.write_text("\\textbf{" + body_original.strip() + "}\n", encoding="utf-8")
        gate = claims.formal_paper_gate(self.root)
        self.assert_failed_without_human_approval(gate)
        self.assertTrue(any("unbounded TeX redefinition" in issue
                            for issue in gate["issues"]), gate)

        main.write_text(
            main_original.replace(
                "\\documentclass{article}",
                "\\documentclass{article}\n\\everypar{\\color{white}}",
            ),
            encoding="utf-8",
        )
        body.write_text(body_original, encoding="utf-8")
        gate = claims.formal_paper_gate(self.root)
        self.assert_failed_without_human_approval(gate)
        self.assertTrue(any("global TeX rendering assignment" in issue
                            for issue in gate["issues"]), gate)

        main.write_text(
            main_original.replace(
                "\\documentclass{article}",
                "\\documentclass{article}\n\\color{white}",
            ),
            encoding="utf-8",
        )
        gate = claims.formal_paper_gate(self.root)
        self.assert_failed_without_human_approval(gate)
        self.assertTrue(any("preamble rendering command" in issue
                            for issue in gate["issues"]), gate)

        main.write_text(
            main_original.replace(
                "\\documentclass{article}",
                "\\documentclass{article}\n"
                "\\usepackage{atbegshi}\n\\AtBeginShipoutDiscard",
            ),
            encoding="utf-8",
        )
        gate = claims.formal_paper_gate(self.root)
        self.assert_failed_without_human_approval(gate)
        self.assertEqual(gate.get("audit_status"), "not_assessed", gate)

    def test_preamble_layout_and_indirect_rendering_fail_closed(self):
        main = self.latex / "main.tex"
        original = main.read_text(encoding="utf-8")
        variants = {
            "dimension": "\\hoffset=100in\n\\voffset=100in",
            "setlength": "\\setlength{\\textwidth}{0pt}",
            "geometry": "\\usepackage{geometry}\n"
                        "\\geometry{paperwidth=1pt,paperheight=1pt}",
            "transparent": "\\usepackage{transparent}\n\\transparent{0}",
            "custom_rendering": "\\usepackage{xcolor}\n"
                                "\\newcommand{\\hideclaims}{\\color{white}}\n"
                                "\\hideclaims",
        }
        for name, preamble in variants.items():
            with self.subTest(name=name):
                main.write_text(
                    original.replace("\\documentclass{article}",
                                     "\\documentclass{article}\n" + preamble),
                    encoding="utf-8",
                )
                self.assert_failed_without_human_approval(
                    claims.formal_paper_gate(self.root))
                main.write_text(original, encoding="utf-8")

    def test_preamble_endinput_and_caret_notation_fail_closed(self):
        main = self.latex / "main.tex"
        original = main.read_text(encoding="utf-8")
        for token in ("\\endinput", "\\end^^69nput"):
            with self.subTest(token=token):
                main.write_text(
                    original.replace("\\documentclass{article}",
                                     "\\documentclass{article}\n" + token),
                    encoding="utf-8",
                )
                gate = claims.formal_paper_gate(self.root)
                self.assert_failed_without_human_approval(gate)
                self.assertEqual(gate.get("audit_status"), "not_assessed", gate)
                main.write_text(original, encoding="utf-8")

    def test_nonrendered_tex_argument_cannot_satisfy_claim(self):
        body = self.latex / "body.tex"
        body.write_text("Result: \\label{claim-100.00}.\n", encoding="utf-8")
        audit = claims.inspect_project(self.root)
        body_check = next(row for row in audit["numeric_checks"]
                          if row.get("fragment_id") == "paper.body.q1")
        self.assertEqual(body_check["status"], "needs_review", body_check)
        self.assertIn("no scalar literal", body_check["reason"])
        self.assert_failed_without_human_approval(claims.formal_paper_gate(self.root))

    def test_body_rendering_state_propagates_across_static_inputs(self):
        main = self.latex / "main.tex"
        original = main.read_text(encoding="utf-8")
        for command in ("\\color{white}", "\\fontsize{0pt}{0pt}\\selectfont"):
            with self.subTest(command=command):
                main.write_text(
                    original.replace("\\begin{document}",
                                     "\\begin{document}\n" + command),
                    encoding="utf-8",
                )
                self.assert_failed_without_human_approval(
                    claims.formal_paper_gate(self.root))
                main.write_text(original, encoding="utf-8")

    def test_unbound_figure_strong_wording_fails_selected_gate(self):
        extra = self.latex / "extra.tex"
        extra.write_text(
            "\\begin{figure}\n"
            "\\includegraphics{../figures/q1_f01.png}\n"
            "\\caption{This is globally optimal.}\n"
            "\\label{fig:unbound}\n"
            "\\end{figure}\n"
            "See Figure~\\ref{fig:unbound}.\n",
            encoding="utf-8",
        )
        main = self.latex / "main.tex"
        main.write_text(
            main.read_text(encoding="utf-8").replace(
                "\\end{document}", "\\input{extra}\n\\end{document}"
            ),
            encoding="utf-8",
        )
        audit = claims.inspect_project(self.root)
        self.assertTrue(any(row["code"] == "unregistered_global_optimality"
                            for row in audit["unregistered_wording_candidates"]), audit)
        self.assert_failed_without_human_approval(claims.formal_paper_gate(self.root))

    def test_b01_b09_b10_b11_b12_b16_acceptance_matrix(self):
        # B16: machine checks may pass while human semantic coverage stays open.
        gate = claims.formal_paper_gate(self.root)
        self.assertEqual(gate["status"], "passed", gate)
        self.assertEqual(gate["human_semantic_coverage"], "not_assessed")

        # B01: the same accepted metric cannot disagree between summary and body.
        (self.latex / "abstract.tex").write_text("Answer: 99.9.\n", encoding="utf-8")
        audit = claims.inspect_project(self.root)
        self.assertIn("conflict", {row["status"] for row in audit["numeric_checks"]}, audit)
        self.assert_failed_without_human_approval(claims.formal_paper_gate(self.root))

        # B09 and B10: registered method/analysis limits constrain strong wording.
        self._restore_baseline()
        self.state["subproblems"]["Q1"].update(
            optimality_claim="heuristic", result_analysis_status="not_required"
        )
        (self.latex / "body.tex").write_text(
            "Result: 100.00. Globally optimal and robust across all cases.\n",
            encoding="utf-8",
        )
        self.save_projection()
        audit = claims.inspect_project(self.root)
        self.assertEqual(
            {"global_optimality_exceeds_registered_status",
             "broad_robustness_without_required_analysis"},
            {row["code"] for row in audit["wording_findings"]},
            audit,
        )
        self.assert_failed_without_human_approval(claims.formal_paper_gate(self.root))

        # B11: identical selected values do not waive accepted-workbook byte drift.
        self._restore_baseline()
        workbook = self.root / self.state["subproblems"]["Q1"]["solution_workbook"]
        workbook.write_bytes(workbook.read_bytes() + b"\n")
        audit = claims.inspect_project(self.root)
        self.assertNotEqual(audit["b1_status"], "evidence_checked", audit)
        self.assert_failed_without_human_approval(claims.formal_paper_gate(self.root))

        # B12: an auxiliary wording rejection does not revoke the primary answer.
        self._restore_baseline()
        self.state["subproblems"]["Q1"]["analysis_evidence_dispositions"] = [{
            "id": "E12",
            "method_or_source": "Synthetic accepted analysis review",
            "target_claim": "answer_claim",
            "disposition": "reject",
            "impact_scope": "auxiliary_wording",
            "key_finding": "Wording exceeds the accepted evidence.",
            "required_action": "Remove the unsupported wording.",
            "status": "current",
        }]
        scoped = runtime_assurance._current_structured_rejections(self.state, ["Q1"])
        self.assertFalse(scoped["Q1"]["blocks_primary"], scoped)
        self.assertFalse(scoped["Q1"]["blocks_model"], scoped)
        self.assertEqual(scoped["Q1"]["conflicts"], [], scoped)


CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
DOCX_VALID_DRAWING = (
    '<w:drawing><wp:inline><wp:extent cx="1" cy="1"/>'
    '<wp:docPr id="1" name="Picture 1"/><a:graphic>'
    '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
    '<pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="figure.png"/>'
    '<pic:cNvPicPr/></pic:nvPicPr><pic:blipFill>'
    '<a:blip r:embed="rImg1"/><a:stretch><a:fillRect/></a:stretch>'
    '</pic:blipFill><pic:spPr><a:xfrm/><a:prstGeom prst="rect">'
    '<a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
    '</a:graphicData></a:graphic></wp:inline></w:drawing>'
)


class B2cSelectedDocxAcceptanceTests(unittest.TestCase):
    """Exercise the full DOCX adapter over the same live B1/Figure evidence."""

    save_projection = legacy_fixture.B2b4FormalFigureGateTests.save_projection
    set_caption = legacy_fixture.B2b4FormalFigureGateTests.set_caption

    @classmethod
    def setUpClass(cls):
        legacy_fixture.B2b4FormalFigureGateTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        legacy_fixture.B2b4FormalFigureGateTests.tearDownClass.__func__(cls)

    def setUp(self):
        legacy_fixture.B2b4FormalFigureGateTests.setUp(self)
        self.docx_relative = "draft_docx/paper.docx"
        self.docx = self.root / self.docx_relative
        self.docx.parent.mkdir(exist_ok=True)
        self.image_bytes = (self.root / "figures/q1_f01.png").read_bytes()
        policy = self.state["paper_framework"]["claim_consumption_policy"]
        policy.update(
            protocol_version=SELECTED_PAIR[0],
            mode=SELECTED_PAIR[1],
            paper_source={"format": "docx", "entrypoint": self.docx_relative},
        )
        self.binding = policy["figure_bindings"][0]
        self.binding.pop("latex_label")
        self.binding["carrier_locator"] = {
            "kind": "docx_bookmark",
            "value": "fig_q1",
            "body_reference": "See accepted result figure.",
        }
        for fragment in self.fragments:
            fragment["source_file"] = self.docx_relative
        cells = self.registry_row.split("|")
        cells[2] = " Result evidence 100.00 ratio. "
        cells[-2] = f" {self.docx_relative}:p4 "
        self.registry_row = "|".join(cells)
        self._write_docx()
        self.save_projection()

    def tearDown(self):
        legacy_fixture.B2b4FormalFigureGateTests.tearDown(self)

    def _document_xml(
        self,
        *,
        abstract: str = "Answer: 100.0.",
        body: str = "Result: 100.00.",
        caption: str = "Result evidence 100.00 ratio.",
        body_reference: str = "See accepted result figure.",
        body_reference_relationship_id: str | None = None,
        extra_markup: str = "",
        drawing: str = DOCX_VALID_DRAWING,
    ) -> str:
        relationship = (
            f' r:id="{escape(body_reference_relationship_id)}"'
            if body_reference_relationship_id else ""
        )
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
 xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
 <w:body>
  <w:p><w:r><w:t>{escape(abstract)}</w:t></w:r></w:p>
  <w:p><w:r><w:t>{escape(body)}</w:t></w:r></w:p>
  <w:p><w:bookmarkStart w:id="7" w:name="fig_q1"/>
   <w:r>{drawing}</w:r>
   <w:r><w:t>{escape(caption)}</w:t></w:r><w:bookmarkEnd w:id="7"/></w:p>
   <w:p><w:hyperlink w:anchor="fig_q1"{relationship}><w:r><w:t>{escape(body_reference)}</w:t></w:r></w:hyperlink></w:p>
  {extra_markup}
  <w:sectPr/>
 </w:body>
</w:document>'''

    def _write_docx(
        self,
        *,
        abstract: str = "Answer: 100.0.",
        body: str = "Result: 100.00.",
        caption: str = "Result evidence 100.00 ratio.",
        body_reference: str = "See accepted result figure.",
        body_reference_relationship_id: str | None = None,
        embedded_image: bytes | None = None,
        extra_markup: str = "",
        external_relationship: bool = False,
        drawing: str = DOCX_VALID_DRAWING,
    ) -> None:
        rels = '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rImg1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/figure.png"/>
'''
        if external_relationship:
            rels += ('  <Relationship Id="rExt" '
                     'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" '
                     'Target="https://example.invalid" TargetMode="External"/>\n')
        rels += "</Relationships>"
        document = self._document_xml(
            abstract=abstract, body=body, caption=caption,
            body_reference=body_reference,
            body_reference_relationship_id=body_reference_relationship_id,
            extra_markup=extra_markup,
            drawing=drawing,
        )
        with zipfile.ZipFile(self.docx, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", CONTENT_TYPES)
            archive.writestr("_rels/.rels", ROOT_RELS)
            archive.writestr("word/document.xml", document)
            archive.writestr("word/_rels/document.xml.rels", rels)
            archive.writestr(
                "word/media/figure.png",
                self.image_bytes if embedded_image is None else embedded_image,
            )

    def assert_failed_without_human_approval(self, gate: dict) -> None:
        self.assertEqual(gate["status"], "failed", gate)
        self.assertEqual(gate["human_semantic_coverage"], "not_assessed", gate)

    def test_docx_body_caption_bookmark_reference_and_media_bytes_pass(self):
        audit = claims.inspect_project(self.root)
        gate = claims.formal_paper_gate(self.root)
        self.assertEqual(audit["carrier_format"], "docx", audit)
        self.assertEqual(audit["docx_scan"]["status"], "scanned", audit)
        self.assertEqual(audit["docx_scan"]["paragraph_count"], 4, audit)
        self.assertEqual(audit["figure_identity_checks"][0]["identity_status"], "matched", audit)
        self.assertEqual(audit["figure_caption_numeric_checks"][0]["status"], "matched", audit)
        self.assertEqual(gate["status"], "passed", gate)
        self.assertEqual(gate["figure_image_paths"], ["figures/q1_f01.png"])
        self.assertEqual(gate["figure_graphic_bindings"], [])
        self.assertEqual(audit["human_semantic_coverage"], "not_assessed")
        self.assertEqual(gate["human_semantic_coverage"], "not_assessed")

    def test_docx_literal_figure_number_is_structural_not_a_result_claim(self):
        caption = "Figure 1. Result evidence 100.00 ratio."
        cells = self.registry_row.split("|")
        cells[2] = f" {caption} "
        self.registry_row = "|".join(cells)
        self._write_docx(caption=caption)
        self.save_projection()
        audit = claims.inspect_project(self.root)
        self.assertNotIn("1", {row["literal"] for row in audit["unregistered_candidates"]}, audit)
        self.assertEqual(audit["figure_caption_numeric_checks"][0]["status"], "matched", audit)
        self.assertEqual(claims.formal_paper_gate(self.root)["status"], "passed")

    def test_body_reference_search_excludes_every_bound_figure_range(self):
        text = "See Figure.\nCaption See Figure."
        inside_start = text.rfind("Caption")
        self.assertEqual(
            claims._literal_hits_outside_ranges(
                text, "See Figure.", [(inside_start, len(text))]
            ),
            [0],
        )

    def test_docx_numeric_body_reference_is_structural_only_and_sync_consumes_gate(self):
        locator = self.binding["carrier_locator"]
        locator["body_reference"] = "See Figure 1."
        self._write_docx(body_reference="See Figure 1.")
        self.save_projection()

        audit = claims.inspect_project(self.root)
        self.assertNotIn("1", {row["literal"] for row in audit["unregistered_candidates"]}, audit)
        gate = claims.formal_paper_gate(self.root)
        self.assertEqual(gate["status"], "passed", gate)
        report = sync_project.synchronize(self.root, write=False, delivery_scope="docx")
        self.assertEqual(report["claim_paper_gate"]["status"], "passed", report)
        self.assertFalse(any("compile_report" in issue or "编译" in issue
                             for issue in report["issues"]), report)
        submission = sync_project.synchronize(
            self.root, write=False, delivery_scope="submission"
        )
        self.assertEqual(submission["claim_paper_gate"]["status"], "passed", submission)
        self.assertEqual(submission["status"], "failed", submission)
        self.assertTrue(any("no supported rendered submission proof" in issue
                            for issue in submission["issues"]), submission)

    def test_docx_body_reference_result_number_is_not_structural(self):
        caption = "Figure 1. Result evidence 100.00 ratio."
        reference = "See Figure 1 with result 110.00."
        self.binding["carrier_locator"]["body_reference"] = reference
        cells = self.registry_row.split("|")
        cells[2] = f" {caption} "
        self.registry_row = "|".join(cells)
        self._write_docx(caption=caption, body_reference=reference)
        self.save_projection()
        audit = claims.inspect_project(self.root)
        self.assertIn("110.00",
                      {row["literal"] for row in audit["unregistered_candidates"]}, audit)
        self.assert_failed_without_human_approval(claims.formal_paper_gate(self.root))

    def test_docx_bookmark_reference_must_not_carry_relationship_id(self):
        self._write_docx(body_reference_relationship_id="rImg1")
        self.save_projection()
        audit = claims.inspect_project(self.root)
        identity = audit["figure_identity_checks"][0]
        self.assertEqual(identity["identity_status"], "needs_review", identity)
        self.assertTrue(any("not uniquely linked" in issue for issue in identity["issues"]),
                        identity)
        self.assert_failed_without_human_approval(claims.formal_paper_gate(self.root))

    def test_docx_selection_rejects_explicit_latex_scope_after_running_same_gate(self):
        report = sync_project.synchronize(self.root, write=False, delivery_scope="latex")
        self.assertEqual(report["claim_paper_gate"]["status"], "passed", report)
        self.assertTrue(any("conflicts with selected B2 paper_source format docx" in issue
                            for issue in report["issues"]), report)

    def test_arbitrary_unique_text_cannot_satisfy_docx_body_reference(self):
        self.binding["carrier_locator"]["body_reference"] = "Answer:"
        cells = self.registry_row.split("|")
        cells[-2] = f" {self.docx_relative}:p1 "
        self.registry_row = "|".join(cells)
        self._write_docx(body_reference="Unrelated closing note.")
        self.save_projection()
        audit = claims.inspect_project(self.root)
        identity = audit["figure_identity_checks"][0]
        self.assertEqual(identity["identity_status"], "needs_review", audit)
        self.assertTrue(any("not uniquely linked" in issue
                            for issue in identity["issues"]), identity)
        self.assert_failed_without_human_approval(claims.formal_paper_gate(self.root))

    def test_docx_generated_visible_structures_fail_closed(self):
        variants = {
            "chart": (
                '<w:p><w:r><w:drawing><a:graphic><a:graphicData '
                'uri="http://schemas.openxmlformats.org/drawingml/2006/chart">'
                '<c:chart xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" '
                'r:id="rChart1"/></a:graphicData></a:graphic></w:drawing></w:r></w:p>'
            ),
            "numbering": (
                '<w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/>'
                '</w:numPr></w:pPr><w:r><w:t>Visible item</w:t></w:r></w:p>'
            ),
        }
        for name, markup in variants.items():
            with self.subTest(name=name):
                self._write_docx(extra_markup=markup)
                audit = claims.inspect_project(self.root)
                self.assertEqual(audit["docx_scan"]["status"], "not_assessed", audit)
                self.assert_failed_without_human_approval(claims.formal_paper_gate(self.root))

        alternate = DOCX_VALID_DRAWING.replace(
            '<a:blip r:embed="rImg1"/>',
            '<a:blip r:embed="rImg1"><a:extLst><a:ext uri="svg">'
            '<asvg:svgBlip '
            'xmlns:asvg="http://schemas.microsoft.com/office/drawing/2016/SVG/main" '
            'r:embed="rImg2"/></a:ext></a:extLst></a:blip>',
        )
        self._write_docx(drawing=alternate)
        audit = claims.inspect_project(self.root)
        self.assertEqual(audit["docx_scan"]["status"], "not_assessed", audit)
        self.assert_failed_without_human_approval(claims.formal_paper_gate(self.root))

    def test_docx_body_reference_crossing_bookmark_boundary_fails(self):
        self.binding["carrier_locator"]["body_reference"] = "Prefix Result evidence"
        document = self._document_xml().replace(
            '<w:p><w:bookmarkStart w:id="7" w:name="fig_q1"/>',
            '<w:p><w:r><w:t>Prefix </w:t></w:r>'
            '<w:bookmarkStart w:id="7" w:name="fig_q1"/>',
        )
        with zipfile.ZipFile(self.docx, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", CONTENT_TYPES)
            archive.writestr("_rels/.rels", ROOT_RELS)
            archive.writestr("word/document.xml", document)
            archive.writestr(
                "word/_rels/document.xml.rels",
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rImg1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/figure.png"/>'
                '</Relationships>',
            )
            archive.writestr("word/media/figure.png", self.image_bytes)
        self.save_projection()
        audit = claims.inspect_project(self.root)
        self.assertNotEqual(audit["status"], "observed", audit)
        self.assert_failed_without_human_approval(claims.formal_paper_gate(self.root))

    def test_docx_embedded_image_byte_drift_fails_closed(self):
        self._write_docx(embedded_image=b"different embedded image bytes")
        audit = claims.inspect_project(self.root)
        identity = audit["figure_identity_checks"][0]
        self.assertEqual(identity["identity_status"], "needs_review", audit)
        self.assertTrue(any("embedded image bytes differ" in issue
                            for issue in identity["issues"]), audit)
        self.assert_failed_without_human_approval(claims.formal_paper_gate(self.root))

    def test_docx_caption_and_body_numeric_conflicts_fail_closed(self):
        self._write_docx(body="Result: 110.00.")
        audit = claims.inspect_project(self.root)
        body_check = next(row for row in audit["numeric_checks"]
                          if row["fragment_id"] == "paper.body.q1")
        self.assertEqual(body_check["status"], "conflict", audit)
        self.assert_failed_without_human_approval(claims.formal_paper_gate(self.root))

        cells = self.registry_row.split("|")
        cells[2] = " Result evidence 110.00 ratio. "
        self.registry_row = "|".join(cells)
        self._write_docx(caption="Result evidence 110.00 ratio.")
        self.save_projection()
        audit = claims.inspect_project(self.root)
        self.assertEqual(audit["figure_identity_checks"][0]["identity_status"], "matched", audit)
        self.assertEqual(audit["figure_caption_numeric_checks"][0]["status"], "conflict", audit)
        self.assert_failed_without_human_approval(claims.formal_paper_gate(self.root))

    def test_docx_b09_b10_strong_wording_fails_closed(self):
        self.state["subproblems"]["Q1"].update(
            optimality_claim="heuristic", result_analysis_status="not_required"
        )
        self._write_docx(body=(
            "Result: 100.00. Globally optimal and robust across all cases."
        ))
        self.save_projection()
        audit = claims.inspect_project(self.root)
        self.assertEqual(
            {"global_optimality_exceeds_registered_status",
             "broad_robustness_without_required_analysis"},
            {row["code"] for row in audit["wording_findings"]},
            audit,
        )
        self.assert_failed_without_human_approval(claims.formal_paper_gate(self.root))

    def test_docx_tracked_changes_fields_and_external_relationship_fail_closed(self):
        cases = {
            "tracked": {
                "extra_markup": '<w:p><w:ins w:id="1"><w:r><w:t>changed</w:t></w:r></w:ins></w:p>',
                "scan_status": "not_assessed",
            },
            "field": {
                "extra_markup": ('<w:p><w:r><w:fldChar w:fldCharType="begin"/>'
                                 '<w:instrText> REF target </w:instrText></w:r></w:p>'),
                "scan_status": "not_assessed",
            },
            "external_relationship": {
                "external_relationship": True,
                "scan_status": "blocked",
            },
        }
        for name, options in cases.items():
            with self.subTest(case=name):
                expected = options.pop("scan_status")
                self._write_docx(**options)
                audit = claims.inspect_project(self.root)
                self.assertEqual(audit["docx_scan"]["status"], expected, audit)
                self.assertEqual(audit["human_semantic_coverage"], "not_assessed")
                self.assert_failed_without_human_approval(claims.formal_paper_gate(self.root))


if __name__ == "__main__":
    unittest.main()
