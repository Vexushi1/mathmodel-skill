#!/usr/bin/env python3
"""HSK Figure Evidence Python example: one question, one workbook-driven plot.

Instantiate this file from the accepted workbook and its Figure Contract.
It is a rendering example, not a model selection, data processing, or solver.
"""
from __future__ import annotations

import math
import numbers
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from openpyxl import load_workbook

# Replace from the real accepted workbook and the approved Figure Contract.
SOURCE_KIND = "solution"  # "solution" or "analysis" (only if 03B is accepted)
WORKSHEET = "__ACTUAL_SHEET_NAME__"
X_HEADER = "__ACTUAL_X_HEADER__"
Y_HEADER = "__ACTUAL_Y_HEADER__"
X_LABEL = "__ACTUAL_X_LABEL_WITH_UNIT__"
Y_LABEL = "__ACTUAL_Y_LABEL_WITH_UNIT__"
SERIES_LABEL = "__ACTUAL_SERIES_LABEL__"
SERIES_RGB = None  # Set an explicit (R, G, B) tuple in [0, 1]; no implicit palette.
ALLOW_Y_MISSING = False  # True only when the workbook/figure evidence permits missing y.
MISSING_TOKENS: tuple[str, ...] = ()  # Only actual, declared text missing tokens.
SORT_BY_X = False
SORT_REASON = ""  # Required for an evidence-supported chronological/continuous sort.
CONNECT_POINTS = False  # Only when a meaningful order/continuity exists.
EXPORT_FILE = None  # None: open the figure for human review; explicit path: export after review.


def _numeric(value: object, *, missing: bool, context: str) -> float:
    if value is None or isinstance(value, str) and not value.strip():
        if missing:
            return float("nan")
        raise ValueError(f"{context}: unexpected missing value")
    if isinstance(value, str):
        value = value.strip()
        if value in MISSING_TOKENS and missing:
            return float("nan")
        try:
            value = float(value)
        except ValueError as exc:
            raise ValueError(f"{context}: not a numeric value: {value!r}") from exc
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise ValueError(f"{context}: finite real scalar expected")
    numeric = float(value)
    if math.isnan(numeric) and missing:
        return numeric
    if not math.isfinite(numeric):
        raise ValueError(f"{context}: non-finite value is not permitted")
    return numeric


def _validate_missing_tokens() -> None:
    """Textual gaps must never reinterpret real measured zero/infinity as missing."""
    if len(set(MISSING_TOKENS)) != len(MISSING_TOKENS):
        raise ValueError("Missing tokens must be unique")
    for token in MISSING_TOKENS:
        if not isinstance(token, str) or not token.strip() or token != token.strip():
            raise ValueError("Missing tokens must be nonempty normalized text")
        try:
            numeric = float(token)
        except ValueError:
            continue
        if math.isfinite(numeric) or math.isinf(numeric):
            raise ValueError("Missing token must not encode a finite number or infinity")


def read_xy(workbook: Path, sheet: str, x_header: str, y_header: str,
            *, allow_y_missing: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """Read actual first-row headers, preserving input row positions and NaN gaps."""
    if not workbook.is_file():
        raise FileNotFoundError(f"Figure workbook is missing: {workbook}")
    if not sheet or not x_header.strip() or not y_header.strip():
        raise ValueError("Actual worksheet and column headers are required")
    if x_header.strip() == y_header.strip():
        raise ValueError("Figure x/y evidence headers must be distinct")
    _validate_missing_tokens()
    book = load_workbook(workbook, read_only=True, data_only=True)
    try:
        if sheet not in book.sheetnames:
            raise ValueError(f"{workbook}: missing worksheet {sheet!r}")
        rows = book[sheet].iter_rows(values_only=True)
        raw_headers = next(rows, None)
        if raw_headers is None:
            raise ValueError(f"{workbook}/{sheet}: empty worksheet")
        headers = [v.strip() if isinstance(v, str) else v for v in raw_headers]
        def column(header: str) -> int:
            matches = [i for i, item in enumerate(headers) if item == header.strip()]
            if len(matches) != 1:
                raise ValueError(f"{workbook}/{sheet}: missing or duplicate header {header!r}")
            return matches[0]
        ix, iy = column(x_header), column(y_header)
        x_values: list[float] = []
        y_values: list[float] = []
        for row_number, row in enumerate(rows, 2):
            x_values.append(_numeric(row[ix], missing=False,
                                     context=f"{workbook}/{sheet}/{x_header}/row{row_number}"))
            y_values.append(_numeric(row[iy], missing=allow_y_missing,
                                     context=f"{workbook}/{sheet}/{y_header}/row{row_number}"))
    finally:
        book.close()
    if not x_values or not np.isfinite(y_values).any():
        raise ValueError(f"{workbook}/{sheet}: no finite evidence to plot")
    return np.asarray(x_values, dtype=float), np.asarray(y_values, dtype=float)


def make_figure(x: np.ndarray, y: np.ndarray, *, color: tuple[float, float, float],
                x_label: str, y_label: str, series_label: str, connect: bool = False):
    """Render the already-chosen Figure Contract, without changing its numerical data."""
    if len(color) != 3 or any(not 0 <= c <= 1 for c in color):
        raise ValueError("Provide an explicit RGB triple with components in [0, 1]")
    fig, ax = plt.subplots(figsize=(8.4, 5.2), layout="constrained")
    ax.plot(x, y, linestyle="-" if connect else "None", marker="o",
            linewidth=1.6, markersize=4.8, color=color, label=series_label)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False)
    # No figure/axes title: the formal caption is owned by LaTeX/DOCX.
    return fig


def main() -> None:
    actual = (WORKSHEET, X_HEADER, Y_HEADER, X_LABEL, Y_LABEL, SERIES_LABEL)
    if any(value.startswith("__ACTUAL_") for value in actual) or SERIES_RGB is None:
        raise ValueError("Instantiate actual workbook fields, evidence labels and explicit RGB first")
    if SOURCE_KIND not in {"solution", "analysis"}:
        raise ValueError("SOURCE_KIND must be 'solution' or 'analysis'")
    result_dir = Path(__file__).resolve().parent
    question = result_dir.name.removesuffix("求解")
    suffix = "求解结果.xlsx" if SOURCE_KIND == "solution" else "结果深化分析.xlsx"
    book = result_dir / f"{question}{suffix}"
    x, y = read_xy(book, WORKSHEET, X_HEADER, Y_HEADER,
                   allow_y_missing=ALLOW_Y_MISSING)
    if SORT_BY_X:
        if not SORT_REASON.strip() or len(np.unique(x)) != len(x):
            raise ValueError("Sorting requires a reason and unique continuous x values")
        order = np.argsort(x, kind="stable")
        x, y = x[order], y[order]
    fig = make_figure(x, y, color=SERIES_RGB, x_label=X_LABEL, y_label=Y_LABEL,
                      series_label=SERIES_LABEL, connect=CONNECT_POINTS)
    if EXPORT_FILE:
        out = (result_dir / EXPORT_FILE).resolve()
        if not out.is_relative_to(result_dir):
            raise ValueError("Figure export must stay inside the question directory")
        fig.savefig(out, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    main()
