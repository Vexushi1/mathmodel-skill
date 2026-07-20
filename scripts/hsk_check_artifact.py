#!/usr/bin/env python3
"""Check HSK v6.2.2 project structure, workbook contract and software ownership."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from openpyxl import load_workbook

CN_NUM = "一二三四五六七八九十"
FIG_EXT = {".png", ".pdf", ".svg", ".jpg", ".jpeg", ".tif", ".tiff"}
PY_PLOT_TOKENS = ("matplotlib", "seaborn", "savefig(", "plt.show(")
SOLUTION_REQUIRED = {"核心指标", "数据审计"}
ROBUSTNESS_ALLOWED = {"参数敏感性", "鲁棒性区间", "扰动明细", "算法稳定性", "适用性说明"}


def check_code(root: Path) -> list[str]:
    issues: list[str] = []
    py_dir, matlab_dir = root / "Python求解", root / "MATLAB绘图"
    if not py_dir.exists():
        issues.append("missing: Python求解/")
    if not matlab_dir.exists():
        issues.append("missing: MATLAB绘图/")
    for path in py_dir.rglob("*.py") if py_dir.exists() else []:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(token in text for token in PY_PLOT_TOKENS):
            issues.append(f"Python formal-plot ownership violation: {path.relative_to(root)}")
        if "if __name__" not in text and any(key in path.stem for key in ("求解", "敏感性", "鲁棒性")):
            issues.append(f"Python main script lacks entry point: {path.relative_to(root)}")
    return issues


def worksheet_has_data(worksheet) -> bool:
    for row_index, row in enumerate(worksheet.iter_rows(values_only=True), start=1):
        if row_index == 1:
            continue
        if any(value not in (None, "") for value in row):
            return True
    return False


def inspect_workbook(path: Path, kind: str) -> list[str]:
    issues: list[str] = []
    try:
        workbook = load_workbook(path, read_only=True, data_only=True)
    except Exception as exc:  # noqa: BLE001
        return [f"cannot open workbook {path}: {exc}"]
    try:
        names = set(workbook.sheetnames)
        if kind == "solution":
            missing = SOLUTION_REQUIRED - names
            if missing:
                issues.append(f"solution workbook missing sheets {sorted(missing)}: {path}")
        elif not (names & ROBUSTNESS_ALLOWED):
            issues.append(f"robustness workbook lacks analysis or applicability sheet: {path}")
        for worksheet in workbook.worksheets:
            if len(worksheet.title) > 31:
                issues.append(f"worksheet name exceeds 31 characters: {path} -> {worksheet.title}")
            if not worksheet_has_data(worksheet):
                issues.append(f"empty worksheet is forbidden: {path} -> {worksheet.title}")
    finally:
        workbook.close()
    return issues


def check_results(root: Path) -> list[str]:
    issues: list[str] = []
    base = root / "结果数据表"
    if not base.exists():
        return ["missing: 结果数据表/"]
    questions = [path for path in base.iterdir() if path.is_dir() and re.fullmatch(rf"问题[{CN_NUM}]+", path.name)]
    if not questions:
        return ["missing: no 结果数据表/问题X/ directories"]
    for question in questions:
        data_dir = question / f"{question.name}结果数据"
        if not data_dir.exists():
            issues.append(f"missing: {data_dir.relative_to(root)}")
            continue
        solution = data_dir / f"{question.name}求解结果.xlsx"
        robustness = data_dir / f"{question.name}敏感性与鲁棒性结果.xlsx"
        for path, kind in ((solution, "solution"), (robustness, "robustness")):
            if not path.is_file():
                issues.append(f"missing: {path.relative_to(root)}")
            else:
                issues.extend(inspect_workbook(path, kind))
    return issues


def check_figures(root: Path) -> list[str]:
    issues: list[str] = []
    for dirname in ("figures", "figures_editable"):
        directory = root / dirname
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if path.is_file() and path.suffix.lower() in FIG_EXT and any(ord(char) >= 128 for char in path.name):
                issues.append(f"figure filename should be ASCII: {path.relative_to(root)}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", nargs="?", default=".")
    parser.add_argument("--mode", choices=["full", "code", "data", "figures"], default="full")
    args = parser.parse_args()
    root = Path(args.project).resolve()
    issues: list[str] = []
    if args.mode in {"full", "code"}:
        issues += check_code(root)
    if args.mode in {"full", "data"}:
        issues += check_results(root)
    if args.mode in {"full", "figures"}:
        issues += check_figures(root)
    if issues:
        print("HSK artifact check: ISSUES FOUND")
        for item in issues:
            print("-", item)
        return 1
    print("HSK artifact check: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
