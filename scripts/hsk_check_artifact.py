#!/usr/bin/env python3
"""Check HSK project structure, per-subproblem workbook contracts and software ownership."""
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

ROOT = Path(__file__).resolve().parent.parent
CN_NUM = "一二三四五六七八九十百"
FIG_EXT = {".png", ".pdf", ".svg", ".jpg", ".jpeg", ".tif", ".tiff"}
PY_PLOT_TOKENS = ("matplotlib", "seaborn", "savefig(", "plt.show(")


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    parent = str(path.parent)
    added = parent not in sys.path
    if added:
        sys.path.insert(0, parent)
    try:
        spec.loader.exec_module(module)
    finally:
        if added:
            sys.path.remove(parent)
    return module


RESULT_IO = _load_module("hsk_result_io", ROOT / "templates/code/hsk_pipeline/result_io.py")
STATE_VALIDATOR = _load_module("hsk_state_validator", ROOT / "scripts/validate_project_state.py")


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


def inspect_workbook(
    path: Path,
    kind: str,
    problem_types: Sequence[str] = (),
    capabilities: Mapping[str, bool] | None = None,
) -> list[str]:
    try:
        RESULT_IO.validate_workbook_file(
            path,
            kind,
            problem_types=problem_types,
            capabilities=capabilities,
        )
    except Exception as exc:  # noqa: BLE001
        return [f"workbook contract violation: {path}: {exc}"]
    return []


def _question_number(question_name: str) -> str | None:
    mapping = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    token = question_name.removeprefix("问题")
    value = mapping.get(token)
    return f"Q{value}" if value is not None else None


def load_project_state(root: Path) -> dict[str, Any]:
    path = root / "state" / "project_state.yaml"
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def resolve_question_contract(
    root: Path,
    question_name: str,
    explicit_types: Sequence[str],
) -> tuple[tuple[str, ...], Mapping[str, bool] | None]:
    state = load_project_state(root)
    subproblems = state.get("subproblems", {})
    candidates = [question_name, _question_number(question_name)]
    entry = next((subproblems.get(key) for key in candidates if key and key in subproblems), None)
    if isinstance(entry, Mapping):
        types = entry.get("problem_types", {}) or {}
        labels = [types.get("primary"), *types.get("secondary", [])]
        problem_types = tuple(dict.fromkeys(str(item) for item in labels if item))
        capabilities = entry.get("capabilities")
        return problem_types, capabilities if isinstance(capabilities, Mapping) else None
    if explicit_types:
        return tuple(dict.fromkeys(explicit_types)), None
    legacy = state.get("project", {}).get("problem_types", [])
    return tuple(str(item) for item in legacy), None


def check_results(root: Path, explicit_types: Sequence[str]) -> list[str]:
    issues: list[str] = []
    base = root / "结果数据表"
    if not base.exists():
        return ["missing: 结果数据表/"]
    questions = [
        path for path in base.iterdir()
        if path.is_dir() and re.fullmatch(rf"问题[{CN_NUM}]+", path.name)
    ]
    if not questions:
        return ["missing: no 结果数据表/问题X/ directories"]
    for question in questions:
        problem_types, capabilities = resolve_question_contract(root, question.name, explicit_types)
        data_dir = question / f"{question.name}结果数据"
        if not data_dir.exists():
            issues.append(f"missing: {data_dir.relative_to(root)}")
            continue
        pairs = (
            (data_dir / f"{question.name}求解结果.xlsx", "solution"),
            (data_dir / f"{question.name}敏感性与鲁棒性结果.xlsx", "robustness"),
        )
        for path, kind in pairs:
            if not path.is_file():
                issues.append(f"missing: {path.relative_to(root)}")
            else:
                issues.extend(inspect_workbook(path, kind, problem_types, capabilities))
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


def check_state(root: Path) -> list[str]:
    state = root / "state" / "project_state.yaml"
    if not state.is_file():
        return []
    return [f"project state violation: {item}" for item in STATE_VALIDATOR.validate_state_file(state, project_root=root)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", nargs="?", default=".")
    parser.add_argument("--mode", choices=["full", "code", "data", "figures", "state"], default="full")
    parser.add_argument(
        "--problem-types",
        nargs="*",
        default=[],
        help="旧项目兼容标签；新项目优先读取 state/project_state.yaml 的每问 problem_types/capabilities",
    )
    args = parser.parse_args()
    root = Path(args.project).resolve()

    issues: list[str] = []
    if args.mode in {"full", "code"}:
        issues += check_code(root)
    if args.mode in {"full", "data"}:
        issues += check_results(root, args.problem_types)
    if args.mode in {"full", "figures"}:
        issues += check_figures(root)
    if args.mode in {"full", "state"}:
        issues += check_state(root)
    if issues:
        print("HSK artifact check: ISSUES FOUND")
        for item in issues:
            print("-", item)
        return 1
    print("HSK artifact check: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
