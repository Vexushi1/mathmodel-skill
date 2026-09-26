"""B2b3a bounded Figure registry and literal TeX source parser tests."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from claim_figure import inspect_static_figures, parse_framework_figure_rows
from claim_tex import scan_static_latex


HEADER = (
    "| 图号 | DOCX/LaTeX 图注 | 图型/作用 | 源工作簿 | 工作表/精确唯一表头 | "
    "绘图程序 | 导出文件 | 正文支撑判断 | 正文引用位置 |\n"
    "|---|---|---|---|---|---|---|---|---|\n"
)
ROW = (
    "| 图1 | 核心趋势 | 时间变化 | `q1/result.xlsx` | Sheet1 / 年份、结果 | "
    "`q1/q1_plot.m` | `figures/q1.png` | 增长 | §3.1 |\n"
)


def framework(table: str = HEADER + ROW) -> str:
    return "# 模型论文框架\n## 图表证据链\n\n" + table + "\n## 待办与缺口\n"


class FigureRegistryParserTests(unittest.TestCase):
    def test_exact_nine_column_table_and_normalized_code_cells(self):
        rows = parse_framework_figure_rows(framework())
        self.assertEqual(set(rows), {"图1"})
        self.assertEqual(rows["图1"], {
            "figure_id": "图1", "paper_caption": "核心趋势", "figure_role": "时间变化",
            "workbook": "q1/result.xlsx", "worksheet_headers": "Sheet1 / 年份、结果",
            "plotting_program": "q1/q1_plot.m", "export_file": "figures/q1.png",
            "body_support": "增长", "body_reference": "§3.1",
        })
        self.assertEqual(parse_framework_figure_rows(framework(HEADER + "| | | | | | | | | |\n")), {})
        self.assertEqual(parse_framework_figure_rows(framework().replace("\n", "\r\n")), rows)

    def test_malformed_ambiguous_or_duplicate_registry_rejected(self):
        cases = (
            framework(ROW),
            framework(HEADER.replace("绘图程序", "脚本") + ROW),
            framework(HEADER + ROW + ROW),
            framework(HEADER + ROW + "\n" + HEADER + ROW),
            framework(HEADER + "| | 核心趋势 | | | | | | | |\n"),
            framework(HEADER + ROW.rstrip("\n") + " extra |\n"),
            framework() + "## 图表证据链\n" + HEADER + ROW,
        )
        for index, text in enumerate(cases):
            with self.subTest(index=index), self.assertRaises(ValueError):
                parse_framework_figure_rows(text)


class StaticFigureParserTests(unittest.TestCase):
    def scan(self, main: str, child: str | None = None) -> dict:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            latex = root / "final_latex"
            latex.mkdir()
            (latex / "main.tex").write_text(main, encoding="utf-8")
            if child is not None:
                (latex / "q1.tex").write_text(child, encoding="utf-8")
            return scan_static_latex(root, Path("final_latex/main.tex"))

    def main(self, body: str) -> str:
        return "\\documentclass{article}\n\\begin{document}\n" + body + "\n\\end{document}\n"

    def test_modular_literal_figure_with_physical_locations(self):
        scan = self.scan(self.main("\\input{q1}\n如图~\\ref{fig:q1}。"),
                         "结果如下。\n\\begin{figure}[ht]\n\\centering\n"
                         "\\includegraphics[width=.8\\linewidth]{figures/q1.png}\n"
                         "\\caption{核心趋势}\\label{fig:q1}\n\\end{figure}\n")
        self.assertEqual(scan["status"], "scanned", scan["issues"])
        result = inspect_static_figures(scan)
        self.assertEqual(result["status"], "scanned", result)
        self.assertEqual(len(result["figures"]), 1)
        figure = result["figures"][0]
        self.assertEqual(figure["status"], "located", figure)
        self.assertEqual((figure["label"], figure["caption"], figure["image"]),
                         ("fig:q1", "核心趋势", "figures/q1.png"))
        self.assertEqual(figure["begin_location"]["source_file"], "final_latex/q1.tex")
        self.assertEqual(figure["begin_location"]["line"], 2)
        self.assertEqual(figure["caption_location"]["line"], 5)
        self.assertEqual(figure["body_ref_locations"][0]["source_file"], "final_latex/main.tex")
        self.assertLess(figure["begin_offset"], figure["caption_location"]["char_offset"])
        self.assertLess(figure["caption_location"]["char_offset"], figure["end_offset"])

    def test_missing_caption_label_image_and_reference_never_located(self):
        for content, reason in (
            (r"\includegraphics{f.png}\label{fig:q1}", "missing_literal_caption"),
            (r"\includegraphics{f.png}\caption{C}", "missing_literal_label"),
            (r"\caption{C}\label{fig:q1}", "missing_literal_image"),
        ):
            with self.subTest(reason=reason):
                scan = self.scan(self.main(r"\begin{figure}" + content + r"\end{figure}"))
                result = inspect_static_figures(scan)
                self.assertEqual(result["status"], "not_assessed")
                self.assertIn(reason, result["figures"][0]["issues"])
        scan = self.scan(self.main(r"\begin{figure}\includegraphics{f.png}"
                                        r"\caption{C}\label{fig:q1}\end{figure}"))
        self.assertIn("missing_literal_body_ref", inspect_static_figures(scan)["figures"][0]["issues"])

    def test_duplicate_label_dynamic_commands_and_nested_structure_fail_closed(self):
        cases = (
            (r"\begin{figure}\includegraphics{f.png}\caption{C}\label{fig:q1}"
             r"\end{figure}\label{fig:q1}\ref{fig:q1}", "figure_label_not_unique_in_active_body"),
            (r"\begin{figure}\includegraphics{f.png}\caption{C}\label{\dynamic}"
             r"\end{figure}\ref{fig:q1}", "dynamic_or_malformed_label"),
            (r"\begin{figure}\includegraphics{\imagefile}\caption{C}\label{fig:q1}"
             r"\end{figure}\ref{fig:q1}", "dynamic_or_malformed_includegraphics"),
            (r"\begin{figure}\begin{minipage}{.8\linewidth}\includegraphics{f.png}"
             r"\end{minipage}\caption{C}\label{fig:q1}\end{figure}\ref{fig:q1}",
             "nested_figure_structure"),
            ("\\begin{figure}\\includegraphics{f.png}\\caption{A % masked text\nB}"
             "\\label{fig:q1}\\end{figure}\\ref{fig:q1}", "dynamic_or_malformed_caption"),
        )
        for body, reason in cases:
            with self.subTest(reason=reason):
                scan = self.scan(self.main(body))
                self.assertEqual(scan["status"], "scanned", scan["issues"])
                row = inspect_static_figures(scan)["figures"][0]
                self.assertEqual(row["status"], "not_assessed", row)
                self.assertIn(reason, row["issues"])

    def test_figure_environment_names_must_match_exactly(self):
        for opening, closing in (("figure", "figure*"), ("figure*", "figure")):
            with self.subTest(opening=opening, closing=closing):
                body = (rf"\begin{{{opening}}}\includegraphics{{f.png}}\caption{{C}}"
                        rf"\label{{fig:q1}}\end{{{closing}}}\ref{{fig:q1}}")
                scan = self.scan(self.main(body))
                self.assertEqual(scan["status"], "scanned", scan["issues"])
                result = inspect_static_figures(scan)
                self.assertEqual(result["status"], "not_assessed")
                self.assertIn("mismatched_figure_environment", result["figures"][0]["issues"])

    def test_inactive_comment_verbatim_and_escaped_commands_are_ignored(self):
        body = (r"% \graphicspath{{wrong/}} \begin{figure}\includegraphics{fake.png}\caption{Fake}\label{fig:fake}\end{figure}" "\n"
                r"\begin{verbatim}\graphicspath{{wrong/}}\begin{figure}\includegraphics{fake.png}\end{figure}\end{verbatim}" "\n"
                r"\\begin{figure} escaped text" "\n"
                r"\begin{figure}\includegraphics{real.png}\caption{Real}\label{fig:real}\end{figure}" "\n"
                r"As shown in \ref{fig:real}.")
        scan = self.scan(self.main(body))
        result = inspect_static_figures(scan)
        self.assertEqual(result["status"], "scanned", result)
        self.assertEqual(len(result["figures"]), 1)
        self.assertEqual(result["figures"][0]["image"], "real.png")

    def test_active_graphicspath_prevents_source_file_identity_claim(self):
        main = (r"\documentclass{article}" "\n" r"\graphicspath{{alternate/}}" "\n"
                r"\begin{document}\begin{figure}\includegraphics{real.png}"
                r"\caption{Real}\label{fig:real}\end{figure}"
                r"As shown in \ref{fig:real}.\end{document}")
        scan = self.scan(main)
        self.assertEqual(scan["status"], "scanned", scan["issues"])
        result = inspect_static_figures(scan)
        self.assertEqual(result["status"], "not_assessed")
        self.assertIn("active_graphicspath_unsupported", result["issues"])

    def test_literal_unicode_question_folder_image_is_located(self):
        body = (r"\begin{figure}\includegraphics{../问题二求解/当前图.pdf}"
                r"\caption{结果}\label{fig:q2}\end{figure}\ref{fig:q2}")
        scan = self.scan(self.main(body))
        result = inspect_static_figures(scan)
        self.assertEqual(result["status"], "scanned", result)
        self.assertEqual(result["figures"][0]["image"], "../问题二求解/当前图.pdf")

    def test_split_segment_and_unscanned_graph_are_not_assessed(self):
        scan = self.scan(self.main(r"\begin{figure}\input{q1}\caption{C}"
                                        r"\label{fig:q1}\end{figure}\ref{fig:q1}"),
                         r"\includegraphics{f.png}")
        self.assertEqual(scan["status"], "scanned", scan["issues"])
        result = inspect_static_figures(scan)
        self.assertEqual(result["status"], "not_assessed")
        self.assertIn("figure_not_closed_in_same_segment", result["figures"][0]["issues"])
        self.assertIn("figure_end_without_begin_in_segment", result["issues"])
        self.assertEqual(inspect_static_figures({"status": "not_assessed"})["status"], "not_assessed")


if __name__ == "__main__":
    unittest.main()
