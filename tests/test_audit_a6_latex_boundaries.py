from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import audit_latex_project as project_audit
import audit_paper_prose as prose
import latex_delivery as delivery


class TestA6LatexBoundaries(unittest.TestCase):
    def test_appendix_labels_share_the_document_namespace(self):
        text = r"""\begin{document}
\label{eq:main}See Appendix~\ref{app:detail}.
\appendix
\section{Details}\label{app:detail}See~\ref{eq:main}.
\end{document}"""
        self.assertFalse([x for x in prose.audit_text(text) if x.severity == "blocking"])
        duplicate = text.replace(r"\label{app:detail}", r"\label{app:detail}\label{eq:main}")
        self.assertIn("duplicate_label", {x.code for x in prose.audit_text(duplicate)})
        missing = text.replace(r"\label{app:detail}", "")
        self.assertIn("missing_ref_label", {x.code for x in prose.audit_text(missing)})

    def test_claim_conflict_is_question_scoped_and_uses_declared_claims(self):
        cases = (
            ("Headline Claim Evidence Level：`HEURISTIC`\n当前主张：全局最优", True),
            ("### Q1\n- Headline Claim Evidence Level：`HEURISTIC`\n- 可入文答案：证明达到全局最优。", True),
            ("### Q1\n- Headline Claim Evidence Level：`HEURISTIC`\n- 可入文答案：不声称全局最优。", False),
            ("### Q1\n- Headline Claim Evidence Level：`HEURISTIC`\n- 可入文答案：当前只有可行解，不声称全局最优。", False),
            ("### Q1\n- Headline Claim Evidence Level：`HEURISTIC`\n- 可入文答案：可行解。\n"
             "### Q2\n- Headline Claim Evidence Level：`PROVEN`\n- 可入文答案：证明达到全局最优。", False),
            ("### Q1\n- Headline Claim Evidence Level：`HEURISTIC`\n"
             "用两至四句记录答案，不把启发式结果升级成全局最优。", False),
            ("### Q1\n- Headline Claim Evidence Level：`HEURISTIC`\n"
             "**可入文答案表述**\n证明达到全局最优。\n**证据位置**\n", True),
            ("### Q1\n- Headline Claim Evidence Level：`HEURISTIC`\n"
             "**可入文答案表述**\n用两至四句记录答案，不把启发式结果升级成全局最优。\n"
             "不声称全局最优。\n**证据位置**\n", False),
        )
        for framework, blocked in cases:
            with self.subTest(framework=framework):
                findings = prose.audit_framework_consistency("", framework)
                self.assertEqual(any(x.severity == "blocking" for x in findings), blocked, findings)

    def test_ambiguous_claim_is_reviewed_not_declared_a_proven_conflict(self):
        framework = ("### Q1\n- Headline Claim Evidence Level：`HEURISTIC`\n"
                     "- Headline Claim Scope：若满足尚待核验的凸性条件则全局最优。")
        findings = prose.audit_framework_consistency("", framework)
        self.assertTrue(any(x.severity == "review_required" for x in findings), findings)
        self.assertFalse(any(x.severity == "blocking" for x in findings), findings)

    def test_conditional_support_appearance_change_and_deletion_change_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = root / "main.tex"
            main.write_text(r"\documentclass{article}\usepackage{local}\begin{document}x\end{document}")
            (root / "local.sty").write_text(r"\InputIfFileExists{values.cfg}{}{}")
            absent = delivery.source_bundle_snapshot(main)["source_bundle_sha256"]
            cfg = root / "values.cfg"
            cfg.write_text(r"\InputIfFileExists{nested.def}{}{}")
            nested = root / "nested.def"
            nested.write_text(r"\newcommand{\Value}{1}")
            before = delivery.source_bundle_snapshot(main)
            self.assertEqual({x["path"] for x in before["source_files"]},
                             {"main.tex", "local.sty", "values.cfg", "nested.def"})
            self.assertNotEqual(absent, before["source_bundle_sha256"])
            nested.write_text(r"\newcommand{\Value}{2}")
            self.assertNotEqual(before["source_bundle_sha256"], delivery.source_bundle_snapshot(main)["source_bundle_sha256"])
            cfg.unlink()
            self.assertEqual(absent, delivery.source_bundle_snapshot(main)["source_bundle_sha256"])

    def test_unresolved_or_outside_conditional_input_is_not_silently_ignored(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = root / "main.tex"
            for token in (r"\DynamicFile", "../outside.cfg"):
                with self.subTest(token=token):
                    main.write_text(r"\documentclass{article}\InputIfFileExists{" + token + r"}{}{}\begin{document}x\end{document}")
                    with self.assertRaises(ValueError):
                        delivery.source_bundle_snapshot(main)

    def test_includeonly_formal_rejected_but_preview_and_comments_remain_legal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = root / "main.tex"
            (root / "q1.tex").write_text("one")
            (root / "q2.tex").write_text("two")
            base = r"\documentclass{article}" + "\n{}\n" + r"\begin{document}\include{q1}\include{q2}\end{document}"
            for declaration in (r"\includeonly{q1}", r"\includeonly{}"):
                main.write_text(base.replace("{}", declaration, 1))
                findings = project_audit.audit_project(main)
                formal = project_audit.write_audit_report(main_file=main, findings=findings, mode="formal")
                self.assertEqual(formal["status"], "failed")
                preview = project_audit.write_audit_report(main_file=main, findings=findings, mode="template_smoke")
                self.assertEqual(preview["status"], "passed")
            main.write_text(base.replace("{}", "% " + r"\includeonly{q1}", 1))
            findings = project_audit.audit_project(main)
            self.assertEqual(project_audit.write_audit_report(main_file=main, findings=findings)["status"], "passed")

    def test_recorder_requires_actual_known_project_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = root / "main.tex"
            main.write_text(r"\documentclass{article}\begin{document}x\end{document}")
            self.assertTrue(delivery.recorded_input_snapshot(main)["dependency_issues"])
            recorder = main.with_suffix(".fls")
            recorder.write_text(f"PWD {root}\nINPUT ./main.tex\nINPUT main.aux\nOUTPUT main.aux\n")
            positive = delivery.recorded_input_snapshot(main)
            self.assertEqual(positive["dependency_issues"], [])
            self.assertEqual([x["path"] for x in positive["actual_input_files"]], ["main.tex"])
            (root / "dynamic.tex").write_text("unobserved by static audit")
            recorder.write_text(f"PWD {root}\nINPUT main.tex\nINPUT dynamic.tex\n")
            self.assertTrue(any("未被静态审计覆盖" in x for x in delivery.recorded_input_snapshot(main)["dependency_issues"]))
            (root / "custom.aux").write_text("input source with an auxiliary suffix")
            recorder.write_text(f"PWD {root}\nINPUT main.tex\nINPUT custom.aux\n")
            self.assertTrue(any("未被静态审计覆盖: custom.aux" in x for x in delivery.recorded_input_snapshot(main)["dependency_issues"]))

    def test_old_v3_report_cannot_claim_actual_input_evidence(self):
        issues = delivery.verify_compile_report(project=Path("."), main=Path("main.tex"),
                                                pdf=Path("main.pdf"), report={"report_schema_version": "3.0.0"})
        self.assertTrue(any("v4" in x and "重审" in x for x in issues), issues)

    def test_formal_assembly_failure_is_returned_as_an_issue(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = root / "main.tex"
            main.write_text(r"\documentclass{article}\begin{document}x\end{document}")
            report = {"audit_schema_version": "1.0.0", "status": "passed", "mode": "formal",
                      "source_bundle_sha256": delivery.source_bundle_snapshot(main)["source_bundle_sha256"]}
            with patch.object(delivery, "formal_assembly_issues", side_effect=ValueError("changed input")):
                issues = delivery.verify_audit_report(project=root, main=main, report=report)
            self.assertTrue(any("正式全量装配无法核对" in item for item in issues), issues)

    def test_bad_recorder_encoding_and_dynamic_source_produce_failed_reports(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = root / "main.tex"
            main.write_text(r"\documentclass{article}\begin{document}x\end{document}")
            (root / "main.pdf").write_bytes(b"synthetic PDF unit fixture")
            (root / "main.log").write_text("synthetic successful log\n")
            recorder = main.with_suffix(".fls")
            recorder.write_bytes(b"\xff\xfeinvalid UTF8")
            report = delivery.write_compile_report(project=root, main=main, profile="mcm_icm",
                engine="pdflatex", bibliography="none", sequence=["pdflatex"])
            self.assertEqual(report["status"], "failed")
            self.assertTrue(any("实际编译输入证明无法重建" in item for item in report["dependency_issues"]))
            main.write_text(r"\InputIfFileExists{\DynamicFile}{}{}")
            report = delivery.write_compile_report(project=root, main=main, profile="mcm_icm",
                engine="pdflatex", bibliography="none", sequence=["pdflatex"])
            self.assertEqual(report["status"], "failed")
            self.assertIsNone(report["source_bundle_sha256"])
            self.assertTrue(any("source bundle无法重建" in item for item in report["audit_issues"]))

    def test_recorder_unknown_external_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            outer = Path(temp)
            root = outer / "project"
            root.mkdir()
            main = root / "main.tex"
            main.write_text(r"\documentclass{article}\begin{document}x\end{document}")
            (outer / "outside.tex").write_text("external project content")
            main.with_suffix(".fls").write_text(f"PWD {root}\nINPUT main.tex\nINPUT ../outside.tex\n")
            self.assertTrue(any("越出工程" in x for x in delivery.recorded_input_snapshot(main)["dependency_issues"]))

    def test_recorder_detects_omitted_chapter_even_if_selection_uses_a_macro(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = root / "main.tex"
            main.write_text(r"\documentclass{article}\csname includeonly\endcsname{q1}"
                            r"\begin{document}\include{q1}\include{q2}\end{document}")
            for name in ("q1", "q2"):
                (root / f"{name}.tex").write_text(name)
            main.with_suffix(".fls").write_text(f"PWD {root}\nINPUT main.tex\nINPUT q1.tex\n")
            self.assertTrue(any("正文未被实际编译读取: q2.tex" in x
                                for x in delivery.recorded_input_snapshot(main)["dependency_issues"]))

    def test_v4_recorder_hash_and_input_hash_are_verified(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            root = project / "final_latex"
            root.mkdir()
            main = root / "main.tex"
            main.write_text(r"\documentclass{article}\begin{document}x\end{document}")
            (root / "main.pdf").write_bytes(b"synthetic PDF unit fixture")
            (root / "main.log").write_text("synthetic successful log\n")
            recorder = main.with_suffix(".fls")
            recorder.write_text(f"PWD {root}\nINPUT main.tex\n")
            framework = project / "模型论文框架.md"
            framework.write_text("# framework", encoding="utf-8")
            findings = project_audit.audit_project(main, framework_path=framework)
            project_audit.write_audit_report(main_file=main, findings=findings, framework_path=framework)
            report = delivery.write_compile_report(project=root, main=main, profile="mcm_icm",
                engine="pdflatex", bibliography="none", sequence=["pdflatex"])
            def verify():
                return delivery.verify_compile_report(project=root, main=main, pdf=root / "main.pdf", report=report)
            self.assertEqual(verify(), [])
            recorder.write_text(recorder.read_text() + "INPUT ./main.tex\n")
            self.assertTrue(any("recorder_sha256" in x for x in verify()))
            recorder.unlink()
            self.assertTrue(any("recorder" in x for x in verify()))


if __name__ == "__main__":
    unittest.main()
