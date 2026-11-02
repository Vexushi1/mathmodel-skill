"""Real Python Figure rendering smoke, run in a dedicated Matplotlib CI job."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import matplotlib
matplotlib.use("Agg")
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
            fig = plot.make_figure(x, y, color=(.2, .4, .6),
                                   x_label="时刻 / s", y_label="误差率 / %",
                                   series_label="误差", connect=True)
            self.assertEqual(fig.axes[0].get_title(), "")
            self.assertEqual(fig.axes[0].lines[0].get_ydata()[0], 1.2)
            output = Path(tmp) / "q1_evidence.png"
            fig.savefig(output)
            self.assertGreater(output.stat().st_size, 1000)
            import matplotlib.pyplot as plt
            plt.close(fig)

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



if __name__ == "__main__":
    unittest.main()
