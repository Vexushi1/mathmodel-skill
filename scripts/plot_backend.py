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
            if not isinstance(selected, str) or selected not in BACKENDS:
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


def select_project_plot_backend(project_root: str | Path, *,
                                backend: str, reason: str,
                                expected_generation: int) -> dict[str, Any]:
    """Commit a first project plotting choice through the existing CAS transaction.

    A previously selected or historical active MATLAB project cannot be
    silently converted. The request never changes the numerical solver backend.
    """
    from copy import deepcopy
    import project_transaction as transaction
    import validate_project_state as state_validator
    from runtime_assurance import ProjectStateSnapshot

    if backend not in BACKENDS or not isinstance(reason, str) or not reason.strip():
        raise PlotBackendError("Selection requires python/matlab and nonempty reason")
    if isinstance(expected_generation, bool) or not isinstance(expected_generation, int) or expected_generation < 0:
        raise PlotBackendError("expected_generation must be a nonnegative integer")
    snapshot = ProjectStateSnapshot.capture(project_root)
    if snapshot.raw is None:
        raise PlotBackendError("Project state must exist before choosing a Figure backend")
    root, state = snapshot.root, snapshot.payload()
    generation = snapshot.describe()["state_generation"]
    if generation != expected_generation:
        raise transaction.GenerationConflictError(
            f"Plot backend generation changed: expected {expected_generation}, live {generation}"
        )
    report = inspect_plotting(state)
    if report["issues"]:
        raise PlotBackendError("; ".join(report["issues"]))
    if report["kind"] == "historical_matlab":
        if backend != "matlab":
            raise PlotBackendError("Historical MATLAB Figure identity requires explicit migration")
        snapshot.assert_current()
        return {"status": "unchanged", "backend": "matlab", "state_generation": generation}
    if report["kind"] == "selected":
        old = state["plotting"]
        if old["backend"] != backend or old["selection_reason"].strip() != reason.strip():
            raise PlotBackendError("Plot backend is already selected; use an explicit migration preview")
        snapshot.assert_current()
        return {"status": "unchanged", "backend": backend, "state_generation": generation}
    if not state.get("subproblems"):
        raise PlotBackendError("Choose the Figure backend after the whole-question scope is registered")
    candidate = deepcopy(state)
    candidate["plotting"] = {"backend": backend, "selection_reason": reason.strip()}
    raw = snapshot.describe()["sha256"]
    read_set = {transaction.STATE_RELATIVE_PATH: raw}
    snapshot.assert_current()
    transaction._check_read_set(root, read_set)

    def validate_candidate(staged: Mapping[str, Path]) -> None:
        import yaml
        new_state = yaml.safe_load(
            staged[transaction.STATE_RELATIVE_PATH].read_text(encoding="utf-8")
        )
        problems = state_validator.validate_state_payload(new_state, project_root=root)
        if problems:
            raise PlotBackendError("Candidate project Figure selection invalid: " + "; ".join(problems))

    result = transaction.commit_project_state(
        root, candidate, expected_generation=generation,
        expected_file_hashes=read_set, validators=[validate_candidate],
    )
    return {"status": result["status"], "backend": backend,
            "state_generation": result["target_generation"],
            "environment_verified": False, "figure_approved": False}
