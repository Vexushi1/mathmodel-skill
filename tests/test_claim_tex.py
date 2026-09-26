"""B2 static TeX graph and physical source-position boundaries."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from claim_tex import scan_static_latex, source_location


class ClaimTexTests(unittest.TestCase):
    def project(self, directory: str) -> tuple[Path, Path]:
        root = Path(directory)
        latex = root / "final_latex"
        latex.mkdir()
        return root, latex

    def test_nested_static_includes_preserve_body_and_crlf_bom_source_location(self):
        with tempfile.TemporaryDirectory() as temp:
            root, latex = self.project(temp)
            (latex / "sections").mkdir()
            (latex / "main.tex").write_bytes(
                b"\\documentclass{article}\r\n\\input{sections/preamble}\r\n"
                b"\\begin{document}\r\n\\input{sections/chapter}\r\n\\end{document}\r\n"
            )
            (latex / "sections/preamble.tex").write_text("Preamble only.\n", encoding="utf-8")
            (latex / "sections/chapter.tex").write_text(
                "Before.\n\\input{sections/result}\nAfter.\n", encoding="utf-8"
            )
            raw = "Header.\r\n% fake 999\r\n结果为 100。\r\n".encode("utf-8-sig")
            (latex / "sections/result.tex").write_bytes(raw)

            result = scan_static_latex(root, Path("final_latex/main.tex"))
            self.assertEqual(result["status"], "scanned", result["issues"])
            self.assertEqual(result["active_files"], [
                "final_latex/main.tex", "final_latex/sections/preamble.tex",
                "final_latex/sections/chapter.tex", "final_latex/sections/result.tex",
            ])
            source = result["files"]["final_latex/sections/result.tex"]
            self.assertEqual(source["text"], "Header.\r\n% fake 999\r\n结果为 100。\r\n")
            self.assertEqual(len(source["masked"]), len(source["text"]))
            self.assertNotIn("999", source["masked"])
            offset = source["masked"].index("结果为 100")
            self.assertEqual(source_location(result["files"], "final_latex/sections/result.tex", offset), {
                "line": 3, "byte_offset": len("Header.\r\n% fake 999\r\n".encode("utf-8")) + 3,
            })
            body = [item for item in result["segments"] if item["in_document"]]
            self.assertTrue(any(item["path"] == "final_latex/sections/result.tex"
                                and item["start"] <= offset < item["end"] for item in body))
            self.assertTrue(any(item["path"] == "final_latex/sections/preamble.tex"
                                and not item["in_document"] for item in result["segments"]))

    def test_comment_and_verbatim_fake_includes_and_numbers_are_masked(self):
        with tempfile.TemporaryDirectory() as temp:
            root, latex = self.project(temp)
            main = latex / "main.tex"
            main.write_text(
                "\\documentclass{article}\n\\begin{document}\n"
                "% \\input{missing_comment}\n"
                "\\begin{verbatim}\n\\input{missing_verbatim}\nValue 999\n\\end{verbatim}\n"
                "\\verb|\\input{missing_inline} 888|\n"
                "\\\\input{missing_escaped} is a line break followed by text.\n"
                "Value 100 \\% literal percent.\n\\end{document}\n",
                encoding="utf-8",
            )
            result = scan_static_latex(root, main)
            self.assertEqual(result["status"], "scanned", result["issues"])
            self.assertEqual(result["active_files"], ["final_latex/main.tex"])
            code = result["files"]["final_latex/main.tex"]["masked"]
            for fake in ("missing_comment", "missing_verbatim", "missing_inline", "999", "888"):
                self.assertNotIn(fake, code)
            self.assertIn("Value 100", code)

    def test_includeonly_conditional_and_macro_include_are_unassessed(self):
        samples = (
            "\\includeonly{q1}\n\\begin{document}x\\end{document}",
            "\\begin{document}\\iffalse Hidden \\fi\\end{document}",
            "\\begin{document}\\iffalse\\input{missing}\\fi\\end{document}",
            "\\begin{document}\\InputIfFileExists{q1}{}{}\\end{document}",
            "\\newcommand{\\loadit}{\\input{q1}}\\begin{document}x\\end{document}",
            "\\begin{document}\\newcommand{\\answer}{100}x\\end{document}",
            "\\begin{document}\\input{\\chaptername}\\end{document}",
        )
        for source in samples:
            with self.subTest(source=source), tempfile.TemporaryDirectory() as temp:
                root, latex = self.project(temp)
                (latex / "main.tex").write_text("\\documentclass{article}\n" + source, encoding="utf-8")
                (latex / "q1.tex").write_text("Maybe active", encoding="utf-8")
                result = scan_static_latex(root, latex / "main.tex")
                self.assertEqual(result["status"], "not_assessed", result["issues"])
                self.assertTrue(result["issues"])

    def test_other_insertion_commands_cannot_certify_static_active_graph(self):
        for command in (r"\import{sections/}{result}", r"\subimport{sections/}{result}",
                        r"\subfile{sections/result}", r"\inputfrom{sections/}{result}"):
            with self.subTest(command=command), tempfile.TemporaryDirectory() as temp:
                root, latex = self.project(temp)
                (latex / "main.tex").write_text(
                    "\\documentclass{article}\\begin{document}" + command + "\\end{document}",
                    encoding="utf-8",
                )
                result = scan_static_latex(root, latex / "main.tex")
                self.assertEqual(result["status"], "not_assessed", result["issues"])
                self.assertIn("unsupported_active_graph", {item["code"] for item in result["issues"]})

    def test_preamble_macro_used_in_body_makes_literal_numeric_scan_unassessed(self):
        for definition in (r"\newcommand{\answer}{110}", r"\def\answer{110}"):
            with self.subTest(definition=definition), tempfile.TemporaryDirectory() as temp:
                root, latex = self.project(temp)
                (latex / "main.tex").write_text(
                    "\\documentclass{article}" + definition
                    + "\\begin{document}Metric 100 \\answer.\\end{document}", encoding="utf-8",
                )
                result = scan_static_latex(root, latex / "main.tex")
                self.assertEqual(result["status"], "not_assessed", result["issues"])
                self.assertIn("custom_macro_in_body", {item["code"] for item in result["issues"]})

    def test_unsafe_paths_and_cycles_block(self):
        with tempfile.TemporaryDirectory() as temp:
            root, latex = self.project(temp)
            (root / "outside.tex").write_text("Outside", encoding="utf-8")
            main = latex / "main.tex"
            main.write_text(
                "\\documentclass{article}\\begin{document}\\input{../outside}\\end{document}",
                encoding="utf-8",
            )
            report = scan_static_latex(root, main)
            self.assertEqual(report["status"], "blocked")
            self.assertIn("include_outside_project", {x["code"] for x in report["issues"]})

            main.write_text(
                "\\documentclass{article}\\begin{document}\\input{loop}\\end{document}",
                encoding="utf-8",
            )
            (latex / "loop.tex").write_text("\\input{loop}", encoding="utf-8")
            report = scan_static_latex(root, main)
            self.assertEqual(report["status"], "blocked")
            self.assertIn("include_cycle", {x["code"] for x in report["issues"]})

    def test_repeated_include_is_explicitly_unassessed(self):
        with tempfile.TemporaryDirectory() as temp:
            root, latex = self.project(temp)
            (latex / "main.tex").write_text(
                "\\documentclass{article}\\begin{document}"
                "\\input{q1}\\input{q1}\\end{document}", encoding="utf-8",
            )
            (latex / "q1.tex").write_text("Repeated answer 100", encoding="utf-8")
            report = scan_static_latex(root, latex / "main.tex")
            self.assertEqual(report["status"], "not_assessed", report["issues"])
            self.assertEqual(report["active_files"].count("final_latex/q1.tex"), 2)
            self.assertIn("repeated_include", {x["code"] for x in report["issues"]})


if __name__ == "__main__":
    unittest.main()
