"""Observe real Excel reads under the Python Figure dependencies."""

import importlib.util
import math
from pathlib import Path
from tempfile import TemporaryDirectory

import openpyxl


def template(path):
    spec = importlib.util.spec_from_file_location("v11_" + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def plot_observations():
    folder = Path(__file__).resolve().parents[1] / "templates/plot/python"
    primary = template(folder / "q1_plot.py")
    preprocessing = template(folder / "data_process.py")
    observed = {}
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "series.xlsx"
        for label, value in [("missing", None), ("uncached", "=1+2"), ("numeric", 3)]:
            book = openpyxl.Workbook()
            sheet = book.active
            sheet.title = "observed"
            for row in [["t", "before", "after"], [0, 0, 0], [1, value, 0], [2, 0, 0]]:
                sheet.append(row)
            book.save(path)
            book.close()
            for name, read, args, kwargs in [
                ("question", primary.read_xy, ("t", "before"), {"allow_y_missing": True}),
                ("preprocessing", preprocessing.read_before_after, ("t", "before", "after"),
                 {"allow_missing_headers": ("before",)}),
            ]:
                try:
                    middle = read(path, "observed", *args, **kwargs)[1][1]
                except ValueError:
                    observed[name + "_" + label] = "rejected"
                else:
                    observed[name + "_" + label] = "gap" if math.isnan(middle) else middle
    return observed
