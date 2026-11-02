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
ALLOW_MISSING_HEADERS: tuple[str, ...] = ()  # Explicit actual before/after columns only.
MISSING_TOKENS: tuple[str, ...] = ()  # Declared nonnumeric missing markers only.
SORT_BY_X = False
SORT_REASON = ""  # A justified chronological/continuous order, never inferred.
CONNECT_POINTS = False  # MATLAB parity: don't imply continuity without evidence.
MARKER_EVERY = 1  # Sparse marks on a connected line must preserve isolated points.
EXPORT_FILE = None  # Default interactive preview; optional "data_process_...png" export.


def _value(raw: object, *, missing: bool, row: int, header: str,
           missing_tokens: tuple[str, ...] = ()) -> float:
    if raw is None or isinstance(raw, str) and not raw.strip():
        if missing:
            return float("nan")
        raise ValueError(f"{header}, data row {row}: missing")
    if isinstance(raw, bool):
        raise ValueError(f"{header}, data row {row}: boolean is not numeric")
    if isinstance(raw, str):
        raw = raw.strip()
        if raw in missing_tokens:
            if missing:
                return float("nan")
            raise ValueError(f"{header}, data row {row}: missing token not permitted")
        try:
            raw = float(raw)
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
                      before_header: str, after_header: str, *,
                      allow_missing_headers: tuple[str, ...] = (),
                      missing_tokens: tuple[str, ...] = ()):
    """Read accepted, actual header-aligned rows; preserve declared NaN gaps."""
    selected = {before_header.strip(), after_header.strip()}
    if (not x_header.strip() or x_header.strip() in selected
            or len(selected) != 2
            or any(h not in selected for h in allow_missing_headers)
            or len(set(allow_missing_headers)) != len(allow_missing_headers)):
        raise ValueError("Missing allowances must name unique before/after columns")
    for token in missing_tokens:
        if not isinstance(token, str) or not token.strip():
            raise ValueError("Missing tokens must be nonempty text")
        try:
            numeric = float(token)
        except ValueError:
            continue
        if math.isfinite(numeric) or math.isinf(numeric):
            raise ValueError("Missing token must not encode a finite number or infinity")
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
            x.append(_value(row[ix], missing=False, row=i, header=x_header,
                            missing_tokens=missing_tokens))
            before.append(_value(row[ib], missing=before_header in allow_missing_headers,
                                 row=i, header=before_header, missing_tokens=missing_tokens))
            after.append(_value(row[ia], missing=after_header in allow_missing_headers,
                                row=i, header=after_header, missing_tokens=missing_tokens))
    finally:
        book.close()
    if not x or not any(math.isfinite(v) for v in [*before, *after]):
        raise ValueError("No plottable recorded preprocessing evidence")
    return x, before, after


def recorded_order(x, before, after, *, sort_by_x: bool, sort_reason: str):
    """Sorting reorders complete records, never separately filters either series."""
    if not sort_by_x:
        return x, before, after
    if not sort_reason.strip() or len(set(x)) != len(x):
        raise ValueError("Sorting requires a reason and unique chronological/continuous x")
    order = sorted(range(len(x)), key=x.__getitem__)
    return ([x[i] for i in order], [before[i] for i in order],
            [after[i] for i in order])


def visible_marker_indices(values, *, connected: bool, every: int):
    """Show every raw point without lines; preserve isolated points with lines."""
    if isinstance(every, bool) or not isinstance(every, int) or every < 1:
        raise ValueError("MARKER_EVERY must be a positive integer")
    if not connected:
        return list(range(len(values)))
    finite = [math.isfinite(v) for v in values]
    indices = set(range(0, len(values), every))
    indices.update(i for i, valid in enumerate(finite)
                   if valid and (i == 0 or not finite[i - 1])
                   and (i == len(finite) - 1 or not finite[i + 1]))
    return sorted(indices)


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
        workbook, WORKSHEET, X_HEADER, BEFORE_HEADER, AFTER_HEADER,
        allow_missing_headers=ALLOW_MISSING_HEADERS, missing_tokens=MISSING_TOKENS,
    )
    x, before, after = recorded_order(
        x, before, after, sort_by_x=SORT_BY_X, sort_reason=SORT_REASON,
    )
    fig, ax = plt.subplots(figsize=(8.4, 5.2), layout="constrained")
    for values, name, color in (
        (before, BEFORE_LABEL, SERIES_COLORS[0]),
        (after, AFTER_LABEL, SERIES_COLORS[1]),
    ):
        ax.plot(x, values, marker="o", linestyle="-" if CONNECT_POINTS else "None",
                markevery=visible_marker_indices(
                    values, connected=CONNECT_POINTS, every=MARKER_EVERY,
                ),
                color=color, label=name, linewidth=1.6, markersize=4.5)
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
