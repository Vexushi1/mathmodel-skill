#!/usr/bin/env python3
"""HSK project_level preprocessing evidence plot (read-only workbook consumer).

Instantiate from the accepted preprocessing workbook, never from raw data
reprocessing, model fitting, interpolation or inferred sample trajectories.
"""
from __future__ import annotations

import math
import numbers
from pathlib import Path

import matplotlib.pyplot as plt
from openpyxl import load_workbook

WORKSHEET = "__ACTUAL_SHEET_NAME__"
X_HEADER = "__ACTUAL_X_HEADER__"
BEFORE_HEADER = "__ACTUAL_BEFORE_HEADER__"
AFTER_HEADER = "__ACTUAL_AFTER_HEADER__"
X_LABEL = "__ACTUAL_X_LABEL_WITH_UNIT__"
Y_LABEL = "__ACTUAL_Y_LABEL_WITH_UNIT__"
BEFORE_LABEL = "__ACTUAL_BEFORE_LABEL__"
AFTER_LABEL = "__ACTUAL_AFTER_LABEL__"
SERIES_COLORS = None  # Explicit pair of RGB triples in [0, 1], chosen for Figure Contract.
EXPORT_FILE = None  # Default interactive preview; optional "data_process_...png" export.


def _value(raw: object, *, missing: bool, row: int, header: str) -> float:
    if raw is None or isinstance(raw, str) and not raw.strip():
        if missing:
            return float("nan")
        raise ValueError(f"{header}, data row {row}: missing")
    if isinstance(raw, bool):
        raise ValueError(f"{header}, data row {row}: boolean is not numeric")
    if isinstance(raw, str):
        try:
            raw = float(raw.strip())
        except ValueError as exc:
            raise ValueError(f"{header}, data row {row}: not numeric") from exc
    if not isinstance(raw, numbers.Real):
        raise ValueError(f"{header}, data row {row}: expected real scalar")
    val = float(raw)
    if math.isnan(val) and missing:
        return val
    if not math.isfinite(val):
        raise ValueError(f"{header}, data row {row}: not finite")
    return val


def read_before_after(workbook: Path, sheet: str, x_header: str,
                      before_header: str, after_header: str):
    """Read already persisted before/after evidence in the original row order."""
    if not workbook.is_file():
        raise FileNotFoundError(workbook)
    book = load_workbook(workbook, read_only=True, data_only=True)
    try:
        if sheet not in book.sheetnames:
            raise ValueError(f"{workbook}: worksheet {sheet!r} does not exist")
        rows = book[sheet].iter_rows(values_only=True)
        first = next(rows, None)
        if first is None:
            raise ValueError("Empty worksheet")
        headers = [v.strip() if isinstance(v, str) else v for v in first]
        def index(value: str):
            positions = [i for i, h in enumerate(headers) if h == value.strip()]
            if len(positions) != 1:
                raise ValueError(f"Missing or duplicated column: {value!r}")
            return positions[0]
        ix, ib, ia = (index(x_header), index(before_header), index(after_header))
        x, before, after = [], [], []
        for i, row in enumerate(rows, 2):
            x.append(_value(row[ix], missing=False, row=i, header=x_header))
            before.append(_value(row[ib], missing=True, row=i, header=before_header))
            after.append(_value(row[ia], missing=True, row=i, header=after_header))
    finally:
        book.close()
    if not x or not any(math.isfinite(v) for v in [*before, *after]):
        raise ValueError("No plottable recorded preprocessing evidence")
    return x, before, after


def main():
    actual = (WORKSHEET, X_HEADER, BEFORE_HEADER, AFTER_HEADER,
              X_LABEL, Y_LABEL, BEFORE_LABEL, AFTER_LABEL)
    if any(v.startswith("__ACTUAL_") for v in actual) or SERIES_COLORS is None:
        raise ValueError("Instantiate the actual accepted workbook and explicit colors")
    if len(SERIES_COLORS) != 2 or any(
        len(c) != 3 or any(not 0 <= v <= 1 for v in c) for c in SERIES_COLORS
    ):
        raise ValueError("Expected exactly two explicit RGB colors")
    directory = Path(__file__).resolve().parent
    workbook = directory / "数据预处理结果.xlsx"
    x, before, after = read_before_after(
        workbook, WORKSHEET, X_HEADER, BEFORE_HEADER, AFTER_HEADER
    )
    fig, ax = plt.subplots(figsize=(8.4, 5.2), layout="constrained")
    for values, name, color in (
        (before, BEFORE_LABEL, SERIES_COLORS[0]),
        (after, AFTER_LABEL, SERIES_COLORS[1]),
    ):
        ax.plot(x, values, marker="o", linestyle="-", color=color,
                label=name, linewidth=1.6, markersize=4.5)
    ax.set_xlabel(X_LABEL)
    ax.set_ylabel(Y_LABEL)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False)
    if EXPORT_FILE:
        out = (directory / EXPORT_FILE).resolve()
        if not out.is_relative_to(directory) or not out.stem.startswith("data_process"):
            raise ValueError("Preprocessing Figure export must use data_process stem")
        fig.savefig(out, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    main()
