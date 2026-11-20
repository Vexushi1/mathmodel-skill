"""Real Python Figure rendering smoke, run in a dedicated Matplotlib CI job."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import warnings
from xml.etree import ElementTree

import matplotlib
matplotlib.use("Agg")
from matplotlib import font_manager, image as mpl_image
import matplotlib.pyplot as plt
import numpy as np
from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates" / "plot" / "python"


def module(name: str):
    spec = importlib.util.spec_from_file_location(name, TEMPLATES / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PlotRenderingSmoke(unittest.TestCase):
    def cjk_family(self):
        font_file = os.environ.get("HSK_TEST_CJK_FONT")
        if font_file:
            font_manager.fontManager.addfont(font_file)
            return font_manager.FontProperties(fname=font_file).get_name()
        for family in ("Noto Sans CJK SC", "Source Han Sans SC", "Microsoft YaHei", "SimHei", "PingFang SC"):
            try:
                font_manager.findfont(family, fallback_to_default=False)
            except ValueError:
                continue
            return family
        self.skipTest("The export check needs a CJK font (HSK_TEST_CJK_FONT)")

    def _book(self, path: Path, headers, rows):
        book = Workbook()
        sheet = book.active
        sheet.title = "逐时结果"
        sheet.append(headers)
        for row in rows:
            sheet.append(row)
        book.save(path)

    def test_result_figure_reads_real_headers_and_preserves_nan(self):
        plot = module("q1_plot")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "问题一求解结果.xlsx"
            self._book(path, ["时刻", "误差率", "备注"], [
                [0, 1.2, "a"], [1, None, "b"], [2, 2.8, "c"],
            ])
            x, y = plot.read_xy(path, "逐时结果", "时刻", "误差率",
                                allow_y_missing=True)
            self.assertEqual(x.tolist(), [0, 1, 2])
            self.assertTrue(np.isnan(y[1]))
            plot.FONT_FAMILY = self.cjk_family()
            fig = plot.make_figure(x, y, color=(.2, .4, .6),
                                   x_label="时刻 / s", y_label="误差率 / %",
                                   series_label="误差", connect=True)
            self.assertEqual(fig.axes[0].get_title(), "")
            self.assertEqual(fig.axes[0].lines[0].get_ydata()[0], 1.2)
            output = Path(tmp) / "q1_evidence.png"
            with warnings.catch_warnings():
                warnings.filterwarnings("error", message=r"Glyph \d+ .*missing from .*font")
                fig.savefig(output)
            self.assertGreater(float(mpl_image.imread(output)[..., :3].std()), .01)
            plt.close(fig)

    def test_exported_svg_contains_each_chinese_label_glyph(self):
        family = self.cjk_family()
        for name in ("q1_plot", "data_process"):
            with self.subTest(template=name), tempfile.TemporaryDirectory() as tmp:
                plot = module(name)
                directory = Path(tmp) / "问题一求解"
                directory.mkdir()
                plot.__file__ = str(directory / (name + ".py"))
                plot.WORKSHEET = "逐时结果"
                plot.X_HEADER, plot.X_LABEL = "时刻", "时刻 / s"
                if name == "q1_plot":
                    workbook = "问题一求解结果.xlsx"
                    headers = ["时刻", "误差率"]
                    rows = [[0, 2], [1, 1]]
                    plot.Y_HEADER, plot.Y_LABEL = "误差率", "误差率 / %"
                    plot.SERIES_LABEL, plot.SERIES_RGB = "预测误差", (.2, .4, .6)
                    labels = [plot.X_LABEL, plot.Y_LABEL, plot.SERIES_LABEL]
                else:
                    workbook = "数据预处理结果.xlsx"
                    headers = ["时刻", "处理前", "处理后"]
                    rows = [[0, 2, 1], [1, 4, 3]]
                    plot.BEFORE_HEADER, plot.AFTER_HEADER = headers[1:]
                    plot.Y_LABEL = "温度变化 / K"
                    plot.BEFORE_LABEL, plot.AFTER_LABEL = "处理前能耗", "处理后能耗"
                    plot.SERIES_COLORS = ((.2, .4, .6), (.7, .3, .1))
                    labels = [plot.X_LABEL, plot.Y_LABEL, plot.BEFORE_LABEL, plot.AFTER_LABEL]
                self._book(directory / workbook, headers, rows)
                plot.EXPORT_FILE = name + ".svg"
                output = directory / plot.EXPORT_FILE
                try:
                    with mock.patch.object(plt, "show"), matplotlib.rc_context({"svg.fonttype": "path"}):
                        output.write_bytes(b"prior export")
                        plot.FONT_FAMILY = "DejaVu Sans"
                        with self.assertRaisesRegex(UserWarning, "Glyph"):
                            plot.main()
                        self.assertEqual(output.read_bytes(), b"prior export")
                        plot.FONT_FAMILY = family
                        plot.main()
                    root = ElementTree.parse(output).getroot()
                    paths = {p.get("id"): p.get("d") for p in root.findall(".//{*}path")}
                    uses = {u.get("{http://www.w3.org/1999/xlink}href", "").lstrip("#")
                            for u in root.findall(".//{*}use")}
                    chars = set(c for text in labels for c in text if "\u4e00" <= c <= "\u9fff")
                    outlines = set()
                    for char in chars:
                        matches = [key for key in uses if key.endswith(f"-{ord(char):x}")]
                        self.assertEqual(len(matches), 1, char)
                        self.assertTrue(paths.get(matches[0]), char)
                        outlines.add(paths[matches[0]])
                    self.assertEqual(len(outlines), len(chars), "distinct Chinese glyph outlines")
                finally:
                    plt.close("all")

    def test_raw_duplicate_headers_do_not_get_silently_renamed(self):
        plot = module("q1_plot")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "duplicate.xlsx"
            self._book(path, ["时间", "时间", "能耗"], [[0, 0, 5.2]])
            with self.assertRaisesRegex(ValueError, "duplicate"):
                plot.read_xy(path, "逐时结果", "时间", "能耗")

    def test_result_figure_rejects_identical_x_y_headers(self):
        plot = module("q1_plot")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "one_column.xlsx"
            self._book(path, ["时刻", "能耗"], [[0, 2.], [1, 3.]])
            with self.assertRaisesRegex(ValueError, "distinct"):
                plot.read_xy(path, "逐时结果", "能耗", "能耗")

    def test_result_figure_missing_tokens_preserve_real_zeros(self):
        plot = module("q1_plot")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing_tokens.xlsx"
            self._book(path, ["时刻", "误差率"], [
                [0, "缺测"], [1, 0.], [2, 2.5],
            ])
            with mock.patch.object(plot, "MISSING_TOKENS", ("0",)):
                with self.assertRaisesRegex(ValueError, "finite number"):
                    plot.read_xy(path, "逐时结果", "时刻", "误差率",
                                 allow_y_missing=True)
            with mock.patch.object(plot, "MISSING_TOKENS", ("缺测", "缺测")):
                with self.assertRaisesRegex(ValueError, "unique"):
                    plot.read_xy(path, "逐时结果", "时刻", "误差率",
                                 allow_y_missing=True)
            with mock.patch.object(plot, "MISSING_TOKENS", ("缺测",)):
                x, y = plot.read_xy(path, "逐时结果", "时刻", "误差率",
                                    allow_y_missing=True)
                self.assertEqual(x.tolist(), [0., 1., 2.])
                self.assertTrue(np.isnan(y[0]))
                self.assertEqual(y[1:].tolist(), [0., 2.5])

    def test_missing_analysis_workbook_fails_without_main_fallback(self):
        plot = module("q1_plot")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "问题一结果深化分析.xlsx"
            with self.assertRaises(FileNotFoundError):
                plot.read_xy(path, "逐时结果", "时刻", "误差率")

    def test_project_preprocessing_only_consumes_recorded_workbook(self):
        plot = module("data_process")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "数据预处理结果.xlsx"
            self._book(path, ["时刻", "处理前", "处理后"], [
                [0, 12, 10], [1, None, 13], [2, 15, 14],
            ])
            with self.assertRaisesRegex(ValueError, "missing"):
                plot.read_before_after(
                    path, "逐时结果", "时刻", "处理前", "处理后"
                )
            x, before, after = plot.read_before_after(
                path, "逐时结果", "时刻", "处理前", "处理后",
                allow_missing_headers=("处理前",),
            )
            self.assertEqual(x, [0.0, 1.0, 2.0])
            self.assertTrue(np.isnan(before[1]))
            self.assertEqual(after, [10.0, 13.0, 14.0])

            self.assertEqual(plot.recorded_order(
                [2., 0., 1.], [12., 10., 11.], [9., 7., 8.],
                sort_by_x=True, sort_reason="recorded chronological order",
            ), ([0., 1., 2.], [10., 11., 12.], [7., 8., 9.]))
            with self.assertRaisesRegex(ValueError, "unique"):
                plot.recorded_order(
                    [1., 1.], [2., 3.], [4., 5.],
                    sort_by_x=True, sort_reason="chronology",
                )
            self.assertEqual(
                plot.visible_marker_indices([1., float("nan"), 3., float("nan"), 5.],
                                            connected=True, every=10),
                [0, 2, 4],
            )
            self.assertEqual(
                plot.visible_marker_indices([1., float("nan"), 3.],
                                            connected=False, every=10),
                [0, 1, 2],
            )

    def test_preprocessing_declared_missing_tokens_are_strict(self):
        plot = module("data_process")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "数据预处理结果.xlsx"
            self._book(path, ["时刻", "处理前", "处理后"],
                       [[0, "缺测", 3.], [1, 4., 5.]])
            with self.assertRaisesRegex(ValueError, "not numeric"):
                plot.read_before_after(
                    path, "逐时结果", "时刻", "处理前", "处理后",
                    allow_missing_headers=("处理前",),
                )
            x, before, after = plot.read_before_after(
                path, "逐时结果", "时刻", "处理前", "处理后",
                allow_missing_headers=("处理前",), missing_tokens=("缺测",),
            )
            self.assertTrue(np.isnan(before[0]))
            self.assertEqual((x, after), ([0., 1.], [3., 5.]))
            with self.assertRaisesRegex(ValueError, "finite number"):
                plot.read_before_after(
                    path, "逐时结果", "时刻", "处理前", "处理后",
                    allow_missing_headers=("处理前",), missing_tokens=("0",),
                )
            with self.assertRaisesRegex(ValueError, "unique"):
                plot.read_before_after(
                    path, "逐时结果", "时刻", "处理前", "处理前",
                )



    def test_result_figure_text_nan_requires_explicit_missing_token(self):
        plot = module("q1_plot")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "text_nan.xlsx"
            self._book(path, ["时刻", "误差率"], [[0, "NaN"], [1, 0.], [2, 2.5]])
            with self.assertRaisesRegex(ValueError, "text NaN"):
                plot.read_xy(path, "逐时结果", "时刻", "误差率",
                             allow_y_missing=True)
            with mock.patch.object(plot, "MISSING_TOKENS", ("NaN",)):
                x, y = plot.read_xy(path, "逐时结果", "时刻", "误差率",
                                    allow_y_missing=True)
            self.assertEqual(x.tolist(), [0., 1., 2.])
            self.assertTrue(np.isnan(y[0]))
            self.assertEqual(y[1:].tolist(), [0., 2.5])

    def test_preprocessing_text_nan_requires_explicit_missing_token(self):
        plot = module("data_process")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "text_nan_preprocessing.xlsx"
            self._book(path, ["时刻", "处理前", "处理后"],
                       [[0, "NaN", 3.], [1, 0., 5.]])
            with self.assertRaisesRegex(ValueError, "text NaN"):
                plot.read_before_after(
                    path, "逐时结果", "时刻", "处理前", "处理后",
                    allow_missing_headers=("处理前",),
                )
            x, before, after = plot.read_before_after(
                path, "逐时结果", "时刻", "处理前", "处理后",
                allow_missing_headers=("处理前",), missing_tokens=("NaN",),
            )
            self.assertEqual((x, after), ([0., 1.], [3., 5.]))
            self.assertTrue(np.isnan(before[0]))
            self.assertEqual(before[1], 0.)


if __name__ == "__main__":
    unittest.main()
