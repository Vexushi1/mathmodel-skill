"""2026 CUMCM edition-bound formal text checks, no real contestant facts."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_latex_project import audit_cumcm_2026_compliance  # noqa: E402


class Cumcm2026FormalComplianceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "state").mkdir()
        (self.root / "final_latex").mkdir()
        self.main = self.root / "final_latex/main.tex"

    def _state(self, edition="2026", *, competition="CUMCM"):
        project = {"competition": competition}
        if edition is not None:
            project["competition_edition"] = edition
        (self.root / "state/project_state.yaml").write_text(
            yaml.safe_dump({"project": project}, allow_unicode=True),
            encoding="utf-8",
        )

    @staticmethod
    def _paper(ai="本参赛队在竞赛过程中未使用任何AI工具。",
               appendix="本论文没有用到程序。本论文没有支撑材料。"):
        return (
            r"\begin{document}" + "\n"
            + r"\section*{AI工具使用声明}" + "\n" + ai + "\n"
            + r"\printbibliography[title={参考文献}]" + "\n"
            + r"\begin{appendices}" + "\n"
            + r"\section*{附录}" + "\n" + appendix + "\n"
            + r"\end{appendices}" + "\n"
            + r"\end{document}"
        )

    def _codes(self, text):
        return {item.code for item in
                audit_cumcm_2026_compliance(self.main, text)}

    def test_used_and_unused_declared_statements_are_structurally_valid(self):
        self._state()
        self.assertEqual(set(), self._codes(self._paper()))
        used = "本参赛队在竞赛过程中使用了AI工具，主要用于语言润色和代码调试，详细使用情况见支撑材料。"
        self.assertEqual(set(), self._codes(self._paper(ai=used)))

    def test_unfilled_or_conflicting_ai_statement_is_blocked(self):
        self._state()
        self.assertIn(
            "cumcm_2026_ai_unfilled_or_conflicting",
            self._codes(self._paper(ai="【待填写：请确认使用情况。】")),
        )
        both = ("本参赛队在竞赛过程中未使用任何AI工具。"
                "本参赛队在竞赛过程中使用了AI工具，主要用于代码调试，详细使用情况见支撑材料。")
        self.assertIn("cumcm_2026_ai_unfilled_or_conflicting",
                      self._codes(self._paper(ai=both)))

    def test_missing_or_unfilled_appendix_is_blocked(self):
        self._state()
        self.assertIn("cumcm_2026_appendix_unfilled",
                      self._codes(self._paper(appendix="【待填写：真实代码。】")))
        self.assertIn("cumcm_2026_appendix_empty",
                      self._codes(self._paper(appendix="")))
        self.assertIn(
            "cumcm_2026_appendix_missing_or_order",
            self._codes(self._paper().replace(r"\begin{appendices}",
                                              r"\begin{not_appendices}")),
        )

    def test_edition_unknown_cannot_qualify_and_historical_not_forced(self):
        self._state(None)
        self.assertIn("cumcm_edition_unknown", self._codes(self._paper()))
        self._state("2025")
        self.assertEqual(set(), self._codes(self._paper(ai="", appendix="")))
        self._state("2027")
        self.assertEqual(set(), self._codes(self._paper(ai="", appendix="")))

    def test_other_competition_and_template_smoke_not_scoped(self):
        self._state(edition=None, competition="MCM")
        self.assertEqual(set(), self._codes(""))
        (self.root / "state/project_state.yaml").unlink()
        self.assertEqual(set(), self._codes(""))


if __name__ == "__main__":
    unittest.main()
