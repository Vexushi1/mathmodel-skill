from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LATEX_ADAPTER = ROOT / "modules" / "05_writing" / "latex.md"
CUMCM_MAIN = ROOT / "templates" / "latex" / "cumcm" / "hsk" / "hsk_main.tex"


class TestV871ActiveReleaseLabelHygiene(unittest.TestCase):
    def test_active_latex_adapter_title_is_release_neutral(self):
        first_line = LATEX_ADAPTER.read_text(encoding="utf-8").splitlines()[0]
        self.assertEqual("# Module 05B：LaTeX Adapter", first_line)
        self.assertIsNone(re.search(r"v\d+\.\d+(?:\.\d+)?", first_line, flags=re.I))

    def test_latex_adapter_preserves_history_as_explicit_provenance(self):
        text = LATEX_ADAPTER.read_text(encoding="utf-8")
        self.assertIn("architecture introduced in v8.0.1", text)
        self.assertIn("当前 Skill release 版本只由活动 release carriers", text)

    def test_cumcm_main_old_release_number_is_provenance_not_current_carrier(self):
        text = CUMCM_MAIN.read_text(encoding="utf-8")
        self.assertNotIn("% v8.0.1 A196-inspired canonical template:", text)
        self.assertIn("layout lineage: introduced in v8.0.1", text)
        self.assertIn("provenance only", text)
        self.assertIn("current Skill release is declared by active release carriers", text)


if __name__ == "__main__":
    unittest.main()
