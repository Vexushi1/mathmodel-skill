from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class ActiveAuthorityHygieneTests(unittest.TestCase):
    def test_paper_writing_protocol_title_is_release_neutral(self):
        first_line = read("modules/05_writing/paper_writing_protocol.md").splitlines()[0]
        self.assertEqual(first_line, "# Module 05A：Paper Writing Protocol")
        self.assertIsNone(re.search(r"v\d+\.\d+\.\d+", first_line, re.I))

    def test_docx_module_has_distinct_optional_branch_label(self):
        first_line = read("modules/05_writing/docx.md").splitlines()[0]
        self.assertEqual(first_line, "# Module 05E：可选 DOCX 审阅分支")

    def test_artifact_packs_route_body_authority_to_protocol(self):
        for relative in ("packs/artifact/docx.md", "packs/artifact/latex.md"):
            text = read(relative)
            with self.subTest(relative=relative):
                self.assertIn("modules/05_writing/paper_writing_protocol.md", text)
                self.assertNotIn("正文结构与表达服从 `modules/05_writing/latex.md`", text)
        self.assertIn("LaTeX Adapter", read("packs/artifact/docx.md"))
        self.assertIn("只负责 LaTeX 载体", read("packs/artifact/latex.md"))

    def test_readme_authority_map_matches_template_first_architecture(self):
        text = read("README.md")
        self.assertIn("`modules/05_writing/paper_writing_protocol.md`：普通正文结构与表达", text)
        self.assertIn("`modules/05_writing/latex.md`：LaTeX Adapter 与载体接口", text)
        self.assertNotIn("`modules/05_writing/latex.md`：正文结构与表达", text)

    def test_matlab_mechanism_guidance_preserves_monochrome_boundary(self):
        readme = read("templates/matlab/README.md")
        mechanism = read("templates/matlab/draw_mechanism_structure.m")
        self.assertIn("数据驱动主结果图", readme)
        self.assertIn("正式机理/推导图不继承该调色板", readme)
        self.assertIn("monochrome-first", mechanism)
        for forbidden in ("#1478FF", "#F04444", "#16B364", "#F79009", "#7A5AF8"):
            self.assertNotIn(forbidden, mechanism)


if __name__ == "__main__":
    unittest.main()
