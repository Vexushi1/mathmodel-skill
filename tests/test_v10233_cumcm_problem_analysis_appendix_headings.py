"""CUMCM question-analysis and appendix heading hierarchy regression (10.23.3)."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "templates/latex/cumcm/hsk/template_manifest.yaml"


def load_module(name: str, file: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / file)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class CUMCMHeadingHierarchyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = load_module("audit_paper_prose_v10233", "scripts/audit_paper_prose.py")
        cls.validator = load_module("template_validator_v10233", "scripts/validate_template_manifest.py")
        cls.manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))

    @staticmethod
    def _paper(numbers=("一", "二"), observed=None, appendix=""):
        if observed is None:
            observed = [f"问题{n}的分析" for n in numbers]
        analysis = "\n".join(r"\subsection{" + n + "}\n本问围绕实际条件展开数学分析。" for n in observed)
        questions = "\n".join(r"\section{问题" + n + "模型建立及求解}\n"
                              + r"\subsection{求解结果}" + "\n得到该问结果。"
                              for n in numbers)
        return (r"\begin{document}" + "\n" + r"\section{问题分析}" + "\n"
                + analysis + "\n" + questions + "\n" + appendix + "\n"
                + r"\end{document}")

    def _codes(self, tex):
        return {x.code for x in self.audit.audit_text(tex)}

    def test_authority_and_conditional_slot(self):
        slots = {x["id"]: x for x in self.manifest["paper_skeleton"]["ordered_slots"]}
        analysis = slots["problem_analysis"]["heading_structure"]
        appendix = slots["appendix"]["heading_structure"]
        self.assertEqual(analysis["title_pattern"], "问题{N}的分析")
        self.assertEqual(analysis["level"], "subsection")
        self.assertTrue(analysis["exactly_one_per_question"])
        self.assertEqual(appendix["parent_title"], "附录")
        self.assertEqual(appendix["child_title_pattern"], "附录{letter}")
        self.assertFalse(slots["appendix"]["required"])
        self.assertFalse(slots["appendix"]["default_active"])
        self.assertEqual(self.validator.validate_template_manifest(MANIFEST), [])

    def test_variable_question_counts(self):
        for n in (1, 2, 3, 5):
            with self.subTest(n=n):
                questions = ("一", "二", "三", "四", "五")[:n]
                self.assertNotIn(
                    "cumcm_problem_analysis_heading_mismatch",
                    self._codes(self._paper(numbers=questions)),
                )

    def test_missing_duplicate_reversed_extra_and_renamed_headings(self):
        for headings in (
            ["问题一的分析"],
            ["问题二的分析", "问题一的分析"],
            ["问题一的分析", "问题一的分析"],
            ["问题一的分析", "问题二的分析", "问题三的分析"],
            ["问题一求解思路", "问题二的分析"],
        ):
            with self.subTest(headings=headings):
                self.assertIn("cumcm_problem_analysis_heading_mismatch",
                              self._codes(self._paper(observed=headings)))

    def test_commented_example_does_not_count_as_heading(self):
        tex = self._paper().replace(r"\section{问题分析}",
                                    "% " + r"\subsection{问题三的分析}" + "\n"
                                    + r"\section{问题分析}")
        self.assertNotIn("cumcm_problem_analysis_heading_mismatch", self._codes(tex))

    def test_appendix_optional_and_sequential(self):
        self.assertNotIn("cumcm_appendix_parent_heading", self._codes(self._paper(appendix="")))
        for labels in (("A",), ("A", "B"), ("A", "B", "C")):
            appendix = (r"\begin{appendices}" + "\n" + r"\section*{附录}" + "\n"
                        + "\n".join(r"\subsection*{附录" + n + "}\n真实附录材料。"
                                    for n in labels)
                        + "\n" + r"\end{appendices}")
            with self.subTest(labels=labels):
                codes = self._codes(self._paper(appendix=appendix))
                self.assertFalse(codes & {"cumcm_appendix_parent_heading",
                                          "cumcm_appendix_child_headings",
                                          "cumcm_empty_appendix_item"}, codes)

    def test_appendix_parent_child_errors_and_empty_item(self):
        cases = [
            (r"\begin{appendices}\section*{附录A}\section*{附录B}\end{appendices}",
             "cumcm_appendix_parent_heading"),
            (r"\begin{appendices}\subsection*{附录A}材料\end{appendices}",
             "cumcm_appendix_parent_heading"),
            (r"\begin{appendices}\section*{附录}\subsubsection*{附录A}材料\end{appendices}",
             "cumcm_appendix_child_headings"),
            (r"\begin{appendices}\section*{附录}\subsection*{附录B}材料\end{appendices}",
             "cumcm_appendix_child_headings"),
            (r"\begin{appendices}\section*{附录}\subsection*{附录A}\end{appendices}",
             "cumcm_empty_appendix_item"),
        ]
        for appendix, code in cases:
            with self.subTest(code=code):
                self.assertIn(code, self._codes(self._paper(appendix=appendix)))

    def test_appendices_environment_and_legacy_appendix_boundary(self):
        for appendix in (r"\begin{appendices}\section*{附录}\subsection*{附录A}材料\end{appendices}",
                         r"\appendix\section*{附录}\subsection*{附录A}材料"):
            body = self.audit._document_body(self._paper(appendix=appendix))
            main = self.audit._main_text_before_appendix(body)
            self.assertNotIn(r"\subsection*{附录A}", main)
        commented = self._paper(appendix=(r"\begin{appendices}"
                                            r"\section*{附录}\subsection*{附录A}材料"
                                            r"\end{appendices}"))
        commented = commented.replace(r"\section{问题分析}",
                                       "% " + r"\begin{appendices}" + "\n"
                                       + r"\section{问题分析}")
        self.assertIn(r"\section{问题分析}",
                      self.audit._main_text_before_appendix(
                          self.audit._document_body(commented)))

    def test_other_competition_not_scoped(self):
        tex = (r"\begin{document}\section{Method}内容。"
               r"\appendix\section{Extra}材料。\end{document}")
        self.assertFalse(any(x.code.startswith("cumcm_") for x in self.audit.audit_text(tex)))

    def test_read_stage_uses_existing_yaml_selectors(self):
        runtime = yaml.safe_load((ROOT / "core/writing_runtime_contract.yaml").read_text(encoding="utf-8"))
        stages = {x["id"]: x for x in runtime["template_first_progressive_authoring"]["stages"]}
        source = "templates/latex/cumcm/hsk/template_manifest.yaml#paper_skeleton"
        for name in ("problem_analysis", "evaluation_references_conclusion_appendix"):
            self.assertIn(source, stages[name]["read_now"])
            self.assertTrue(all(isinstance(x, str) for x in stages[name]["read_now"]))


if __name__ == "__main__":
    unittest.main()
