"""Real Python Figure rendering smoke, run in a dedicated Matplotlib CI job."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

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
            x, before, after = plot.read_before_after(
                path, "逐时结果", "时刻", "处理前", "处理后"
            )
            self.assertEqual(x, [0.0, 1.0, 2.0])
            self.assertTrue(np.isnan(before[1]))
            self.assertEqual(after, [10.0, 13.0, 14.0])


if __name__ == "__main__":
    unittest.main()
