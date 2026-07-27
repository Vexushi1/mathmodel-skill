#!/usr/bin/env python3
"""Check HSK project structure, framework, three-axis workbooks and ownership."""
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
MATLAB_TITLE_TOKENS = ("title(", "sgtitle(")


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    parent = str(path.parent)
    added = parent not in sys.path
    if added:
        sys.path.insert(0, parent)
    try:
        sys.modules[name] = module
        spec.loader.exec_module(module)
    finally:
        if added:
            sys.path.remove(parent)
    return module


WORKBOOK_VALIDATOR = _load_module("hsk_workbook_validator", ROOT / "templates/code/hsk_pipeline/workbook_validation.py")
WORKBOOK_SCHEMA = yaml.safe_load((ROOT / "core/workbook_schema.yaml").read_text(encoding="utf-8")) or {}
STATE_VALIDATOR = _load_module("hsk_state_validator", ROOT / "scripts/validate_project_state.py")
FRAMEWORK_VALIDATOR = _load_module("hsk_framework_validator", ROOT / "scripts/validate_model_paper_framework.py")


def _question_number(question_name: str) -> str | None:
    mapping = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    value = mapping.get(question_name.removeprefix("问题"))
    return f"Q{value}" if value is not None else None


def _plot_filename(question_name: str) -> str | None:
    token = _question_number(question_name)
    return f"q{token[1:]}_plot.m" if token else None


def _question_directories(base: Path) -> list[Path]:
    return [path for path in base.iterdir() if path.is_dir() and re.fullmatch(rf"问题[{CN_NUM}]+", path.name)]


def check_code(root: Path) -> list[str]:
    issues: list[str] = []
    python_files = [path for path in root.glob("*.py") if any(key in path.stem for key in ("求解", "敏感性", "鲁棒性", "检验"))]
    if not python_files:
        issues.append("missing: 项目根目录中没有问题求解/检验 Python 脚本")
    for path in python_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(token in text for token in PY_PLOT_TOKENS):
            issues.append(f"Python formal-plot ownership violation: {path.relative_to(root)}")
        if "if __name__" not in text:
            issues.append(f"Python main script lacks entry point: {path.relative_to(root)}")
    result_root = root / "结果数据表"
    if result_root.exists():
        for question in _question_directories(result_root):
            expected = _plot_filename(question.name)
            if not expected:
                continue
            plot_path = question / expected
            if not plot_path.is_file():
                issues.append(f"missing: {plot_path.relative_to(root)}")
            else:
                text = plot_path.read_text(encoding="utf-8", errors="ignore")
                if not any(token in text for token in MATLAB_TITLE_TOKENS):
                    issues.append(f"MATLAB formal figure title missing: {plot_path.relative_to(root)}")
    return issues


def inspect_workbook(
    path: Path,
    kind: str,
    problem_types: Sequence[str] = (),
    capabilities: Mapping[str, bool] | None = None,
    *,
    objective: str | None = None,
    structures: Sequence[str] = (),
) -> list[str]:
    try:
        WORKBOOK_VALIDATOR.validate_workbook_file(
            path, kind, schema=WORKBOOK_SCHEMA, problem_types=problem_types,
            capabilities=capabilities, objective=objective, structures=structures,
        )
    except Exception as exc:  # noqa: BLE001
        return [f"workbook contract violation: {path}: {exc}"]
    return []


def load_project_state(root: Path) -> dict[str, Any]:
    path = root / "state" / "project_state.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {} if path.is_file() else {}


def resolve_question_contract(
    root: Path,
    question_name: str,
    explicit_types: Sequence[str],
    explicit_objective: str | None = None,
    explicit_structures: Sequence[str] = (),
) -> tuple[str | None, tuple[str, ...], tuple[str, ...], Mapping[str, bool] | None]:
    state = load_project_state(root)
    subproblems = state.get("subproblems", {})
    candidates = [question_name, _question_number(question_name)]
    entry = next((subproblems.get(key) for key in candidates if key and key in subproblems), None)
    if isinstance(entry, Mapping):
        classification = entry.get("classification", {}) or {}
        objective = classification.get("objective")
        structures = tuple(classification.get("structures", []) or [])
        types = entry.get("problem_types", {}) or {}
        labels = [types.get("primary"), *(types.get("secondary", []) or [])]
        problem_types = tuple(dict.fromkeys(str(item) for item in labels if item))
        capabilities = entry.get("capabilities")
        return objective, structures, problem_types, capabilities if isinstance(capabilities, Mapping) else None
    return explicit_objective, tuple(explicit_structures), tuple(dict.fromkeys(explicit_types)), None


def check_results(
    root: Path,
    explicit_types: Sequence[str],
    explicit_objective: str | None = None,
    explicit_structures: Sequence[str] = (),
) -> list[str]:
    issues: list[str] = []
    base = root / "结果数据表"
    if not base.exists():
        return ["missing: 结果数据表/"]
    questions = _question_directories(base)
    if not questions:
        return ["missing: no 结果数据表/问题X/ directories"]
    for question in questions:
        objective, structures, problem_types, capabilities = resolve_question_contract(
            root, question.name, explicit_types, explicit_objective, explicit_structures
        )
        legacy_dir = question / f"{question.name}结果数据"
        if legacy_dir.exists():
            issues.append(f"obsolete nested directory: {legacy_dir.relative_to(root)}")
        pairs = (
            (question / f"{question.name}求解结果.xlsx", "solution"),
            (question / f"{question.name}敏感性与鲁棒性结果.xlsx", "robustness"),
        )
        for path, kind in pairs:
            if not path.is_file():
                issues.append(f"missing: {path.relative_to(root)}")
            else:
                issues.extend(inspect_workbook(
                    path, kind, problem_types, capabilities,
                    objective=objective, structures=structures,
                ))
    return issues


def check_figures(root: Path) -> list[str]:
    issues: list[str] = []
    base = root / "结果数据表"
    if not base.exists():
        return issues
    for question in _question_directories(base):
        figure_dir = question / "图表"
        if not figure_dir.exists():
            continue
        for path in figure_dir.rglob("*"):
            if path.is_file() and path.suffix.lower() in FIG_EXT and any(ord(char) >= 128 for char in path.name):
                issues.append(f"figure filename should be ASCII: {path.relative_to(root)}")
    return issues


def check_framework(root: Path) -> list[str]:
    framework = root / "模型论文框架.md"
    state = root / "state" / "project_state.yaml"
    return [
        f"model paper framework violation: {item}"
        for item in FRAMEWORK_VALIDATOR.validate_framework_file(framework, state_path=state if state.is_file() else None)
    ]


def check_state(root: Path) -> list[str]:
    state = root / "state" / "project_state.yaml"
    if not state.is_file():
        return []
    return [f"project state violation: {item}" for item in STATE_VALIDATOR.validate_state_file(state, project_root=root)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", nargs="?", default=".")
    parser.add_argument("--mode", choices=["full", "code", "data", "figures", "framework", "state"], default="full")
    parser.add_argument("--objective")
    parser.add_argument("--structures", nargs="*", default=[])
    parser.add_argument("--problem-types", nargs="*", default=[], help="旧项目兼容标签")
    args = parser.parse_args()
    root = Path(args.project).resolve()
    issues: list[str] = []
    if args.mode in {"full", "framework"}: issues += check_framework(root)
    if args.mode in {"full", "code"}: issues += check_code(root)
    if args.mode in {"full", "data"}: issues += check_results(root, args.problem_types, args.objective, args.structures)
    if args.mode in {"full", "figures"}: issues += check_figures(root)
    if args.mode in {"full", "state"}: issues += check_state(root)
    if issues:
        print("HSK artifact check: ISSUES FOUND")
        for item in issues: print("-", item)
        return 1
    print("HSK artifact check: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
