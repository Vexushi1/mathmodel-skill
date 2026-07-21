#!/usr/bin/env python3
"""Check HSK v6.2.2 project structure, workbook schema and software ownership."""
from __future__ import annotations

import argparse
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from openpyxl import load_workbook

CN_NUM = "一二三四五六七八九十"
FIG_EXT = {".png", ".pdf", ".svg", ".jpg", ".jpeg", ".tif", ".tiff"}
PY_PLOT_TOKENS = ("matplotlib", "seaborn", "savefig(", "plt.show(")
PROBLEM_TYPES = (
    "mechanism",
    "optimization",
    "prediction",
    "evaluation",
    "statistics_ml",
    "simulation",
    "spatial",
    "graph_network",
    "scheduling",
    "game_decision",
)
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "core" / "workbook_schema.yaml"


@lru_cache(maxsize=1)
def load_workbook_schema() -> dict[str, Any]:
    if not SCHEMA_PATH.is_file():
        raise FileNotFoundError(f"workbook schema not found: {SCHEMA_PATH}")
    schema = yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))
    if not isinstance(schema, dict):
        raise ValueError(f"workbook schema must be a mapping: {SCHEMA_PATH}")
    return schema


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


def worksheet_headers(worksheet) -> list[str]:
    row = next(worksheet.iter_rows(min_row=1, max_row=1, values_only=True), ())
    return [str(value).strip() for value in row if value not in (None, "")]


def workbook_contract(
    schema: dict[str, Any],
    kind: str,
    problem_type: str | None,
) -> tuple[set[str], set[str], dict[str, dict[str, Any]]]:
    if kind == "solution":
        contract = schema["solution_workbook"]
        required = set(contract.get("common_required_sheets", {}))
        specs: dict[str, dict[str, Any]] = {}
        for section in ("common_required_sheets", "common_recommended_sheets"):
            specs.update(contract.get(section, {}) or {})

        if problem_type:
            for rule in (contract.get("conditional_requirements", {}) or {}).values():
                if problem_type in set(rule.get("problem_types", [])):
                    required.update(rule.get("required_sheets", []))
            profile = (contract.get("task_profiles", {}) or {}).get(problem_type, {})
            required_any = set(profile.get("required_any", []))
        else:
            required_any = set()
        return required, required_any, specs

    if kind == "robustness":
        contract = schema["sensitivity_robustness_workbook"]
        required_any = set(contract.get("required_any_sheets", []))
        specs = contract.get("sheet_schemas", {}) or {}
        return set(), required_any, specs

    raise ValueError(f"unsupported workbook kind: {kind}")


def inspect_workbook(path: Path, kind: str, problem_type: str | None = None) -> list[str]:
    issues: list[str] = []
    try:
        schema = load_workbook_schema()
    except Exception as exc:  # noqa: BLE001
        return [f"cannot load workbook schema {SCHEMA_PATH}: {exc}"]

    try:
        workbook = load_workbook(path, read_only=True, data_only=False)
    except Exception as exc:  # noqa: BLE001
        return [f"cannot open workbook {path}: {exc}"]

    try:
        names = set(workbook.sheetnames)
        required, required_any, specs = workbook_contract(schema, kind, problem_type)
        missing = required - names
        if missing:
            issues.append(f"{kind} workbook missing sheets {sorted(missing)}: {path}")
        if required_any and not (names & required_any):
            issues.append(f"{kind} workbook lacks one of required sheets {sorted(required_any)}: {path}")

        max_name_length = int(schema.get("global_rules", {}).get("worksheet_name_max_length", 31))
        for worksheet in workbook.worksheets:
            location = f"{path} -> {worksheet.title}"
            if len(worksheet.title) > max_name_length:
                issues.append(f"worksheet name exceeds {max_name_length} characters: {location}")
            if not worksheet_has_data(worksheet):
                issues.append(f"empty worksheet is forbidden: {location}")

            headers = worksheet_headers(worksheet)
            duplicate_headers = sorted({header for header in headers if headers.count(header) > 1})
            if duplicate_headers:
                issues.append(f"worksheet has duplicate headers {duplicate_headers}: {location}")

            sheet_spec = specs.get(worksheet.title)
            if not sheet_spec:
                continue
            required_columns = set(sheet_spec.get("required_columns", []))
            missing_columns = sorted(required_columns - set(headers))
            if missing_columns:
                issues.append(f"worksheet missing required columns {missing_columns}: {location}")
    finally:
        workbook.close()
    return issues


def check_results(root: Path, problem_type: str | None = None) -> list[str]:
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
                issues.extend(inspect_workbook(path, kind, problem_type))
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
    parser.add_argument(
        "--problem-type",
        choices=PROBLEM_TYPES,
        help="enforce problem-type-dependent workbook sheets from core/workbook_schema.yaml",
    )
    args = parser.parse_args()
    root = Path(args.project).resolve()
    issues: list[str] = []
    if args.mode in {"full", "code"}:
        issues += check_code(root)
    if args.mode in {"full", "data"}:
        issues += check_results(root, args.problem_type)
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
