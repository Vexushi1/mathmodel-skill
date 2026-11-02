#!/usr/bin/env python3
"""Project-wide Figure rendering backend selection and script resolution.

Read-only, language-neutral adapter: never performs drawing or creates approvals.
Legacy MATLAB project identity remains current and writable.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any


BACKENDS = {"python", "matlab"}


class PlotBackendError(ValueError):
    """Project-wide plotting backend declarations are invalid or ambiguous."""


@dataclass(frozen=True)
class FigureScriptRef:
    backend: str
    path: Path
    relative: str
    hash_field: str
    origin: str


def inspect_plotting(state: Mapping[str, Any]) -> dict[str, Any]:
    """Report selected, historical_matlab, unselected or conflict without writing."""
    setting = state.get("plotting")
    selected: str | None = None
    issues: list[str] = []
    if setting is not None:
        if not isinstance(setting, Mapping):
            issues.append("plotting must be a mapping")
        else:
            selected = setting.get("backend")
            if selected not in BACKENDS:
                issues.append("plotting.backend must be python or matlab")
            reason = setting.get("selection_reason")
            if not isinstance(reason, str) or not reason.strip():
                issues.append("plotting.selection_reason must be nonempty")
    questions = state.get("subproblems") or {}
    if not isinstance(questions, Mapping):
        issues.append("subproblems must be a mapping")
        questions = {}
    has_python = has_matlab = False
    for key, entry in questions.items():
        if not isinstance(entry, Mapping):
            issues.append(f"{key}: invalid question entry")
            continue
        py, ml = entry.get("plot_script"), entry.get("matlab_script")
        has_python |= bool(py)
        has_matlab |= bool(ml)
        if py and (not isinstance(py, str) or not py.endswith(".py")):
            issues.append(f"{key}: plot_script must be a Python file")
        if ml and (not isinstance(ml, str) or not ml.endswith(".m")):
            issues.append(f"{key}: matlab_script must be a MATLAB file")
        if py and ml:
            issues.append(f"{key}: ambiguous dual current Figure scripts")
    if selected == "python" and has_matlab or selected == "matlab" and has_python:
        issues.append("current Figure script conflicts with project backend")
    if selected is None and has_python:
        issues.append("Python plotting script requires explicit project selection")
    if issues:
        kind = "conflict"
    elif selected in BACKENDS:
        kind = "selected"
    elif has_matlab:
        kind = "historical_matlab"
        selected = "matlab"
    else:
        kind = "unselected"
    return {"kind": kind, "backend": selected if selected in BACKENDS else None,
            "issues": issues}


def resolve_question_script(root: str | Path, state: Mapping[str, Any],
                            question: str, chinese_name: str,
                            number: int) -> FigureScriptRef:
    """Find the canonical single active script and its existing hash layer.

    Missing scripts are normal during model design; formal delivery gates decide
    whether an existing file and accepted source identity are required.
    """
    report = inspect_plotting(state)
    if report["issues"]:
        raise PlotBackendError("; ".join(report["issues"]))
    if not re.fullmatch(r"Q[1-9][0-9]*", question) or number < 1:
        raise PlotBackendError(f"Invalid question {question!r}")
    backend = report["backend"] or "matlab"
    field = "plot_script" if backend == "python" else "matlab_script"
    extension = ".py" if backend == "python" else ".m"
    relative = f"{chinese_name}求解/q{number}_plot{extension}"
    entry = (state.get("subproblems") or {}).get(question) or {}
    declared = entry.get(field)
    if declared and declared != relative:
        raise PlotBackendError(f"{question}: expected {field}={relative!r}, got {declared!r}")
    project_root = Path(root).resolve()
    path = (project_root / relative).resolve()
    if not path.is_relative_to(project_root):
        raise PlotBackendError(f"{question}: path escapes project root")
    return FigureScriptRef(
        backend=backend, relative=relative, path=path, hash_field=field,
        origin=report["kind"] if report["kind"] != "unselected" else "legacy_observation",
    )
