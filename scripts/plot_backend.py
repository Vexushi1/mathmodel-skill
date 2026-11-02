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
    return {"kind": kind, "backend": selected if isinstance(selected, str) and selected in BACKENDS else None,
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

    if not isinstance(backend, str) or backend not in BACKENDS or not isinstance(reason, str) or not reason.strip():
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
    if not state.get("subproblems"):
        raise PlotBackendError("Choose the Figure backend after the whole-question scope is registered")
    requirements = state.get("requirements") or {}
    if isinstance(requirements, Mapping):
        declared = {q for key in ("completed", "pending")
                    for q in requirements.get(key, []) if isinstance(q, str)
                    and re.fullmatch(r"Q[1-9][0-9]*", q)}
        absent = declared - set(state["subproblems"])
        if absent:
            raise PlotBackendError(f"Figure backend selection lacks whole-project question records: {sorted(absent)}")

    import hashlib
    import sync_project
    import validate_model_paper_framework as framework_validator

    framework = state.get("paper_framework")
    if not isinstance(framework, Mapping) or not isinstance(framework.get("path"), str):
        raise PlotBackendError("Figure selection requires a registered model framework")
    framework_relative = framework["path"]
    framework_path = transaction._guarded_path(root, framework_relative)
    if not framework_path.is_file():
        raise PlotBackendError(f"registered model framework is missing: {framework_relative}")
    framework_raw = framework_path.read_bytes()
    try:
        framework_text = framework_raw.decode("utf-8")
    except UnicodeError as exc:
        raise PlotBackendError("model framework must be UTF-8") from exc
    baseline_issues = state_validator.validate_state_payload(state, project_root=root)
    baseline_issues.extend(framework_validator.validate_framework_text(
        framework_text, state=state, project_root=root,
    ))
    if baseline_issues:
        raise PlotBackendError(
            "current project state/framework validation failed: " + "; ".join(baseline_issues)
        )

    candidate = deepcopy(state)
    candidate["plotting"] = {"backend": backend, "selection_reason": reason.strip()}
    rendered = sync_project.render_project_plot_backend_memory(framework_text, candidate)
    candidate["paper_framework"]["sha256"] = framework_validator.sha256_text(rendered)
    read_set = {
        transaction.STATE_RELATIVE_PATH: snapshot.describe()["sha256"],
        framework_relative: hashlib.sha256(framework_raw).hexdigest(),
    }
    snapshot.assert_current()
    transaction._check_read_set(root, read_set)

    def validate_candidate(staged: Mapping[str, Path]) -> None:
        import yaml
        staged_framework = staged[framework_relative]
        new_state = yaml.safe_load(
            staged[transaction.STATE_RELATIVE_PATH].read_text(encoding="utf-8")
        )
        problems = state_validator.validate_state_payload(
            new_state, project_root=root, framework_path_override=staged_framework,
        )
        problems.extend(framework_validator.validate_framework_text(
            staged_framework.read_text(encoding="utf-8"),
            state=new_state, project_root=root,
        ))
        if problems:
            raise PlotBackendError(
                "Candidate project Figure selection invalid: " + "; ".join(problems)
            )

    if candidate == state and rendered == framework_text:
        # A repeated identical request is genuinely read-only.
        snapshot.assert_current()
        transaction._check_read_set(root, read_set)
        return {"status": "unchanged", "backend": backend, "state_generation": generation}

    result = transaction.commit_project_state(
        root, candidate, expected_generation=generation,
        expected_file_hashes=read_set,
        writes_before_state=[(framework_relative, rendered)],
        validators=[validate_candidate],
    )
    return {"status": result["status"], "backend": backend,
            "state_generation": result["target_generation"],
            "framework_path": framework_relative,
            "environment_verified": False, "figure_approved": False}



def preview_project_plot_backend_migration(project_root: str | Path, *,
                                           target_backend: str) -> dict[str, Any]:
    """Read-only whole-project Figure migration impact; never execute migration.

    Enumerate registered evidence and publication dependencies without treating
    an unregistered file as an approved Figure or changing numerical acceptance.
    """
    import project_transaction as transaction
    import stage_code as stage
    from runtime_assurance import ProjectStateSnapshot

    if target_backend not in BACKENDS:
        raise PlotBackendError("Migration target must be python or matlab")
    snapshot = ProjectStateSnapshot.capture(project_root)
    if snapshot.raw is None:
        raise PlotBackendError("Migration preview requires existing project state")
    root, state = snapshot.root, snapshot.payload()
    report = inspect_plotting(state)
    if report["issues"]:
        raise PlotBackendError("; ".join(report["issues"]))
    if report["kind"] == "unselected":
        raise PlotBackendError("No active Figure backend; use first-selection transaction")
    current = report["backend"]
    if target_backend == current:
        snapshot.assert_current()
        return {"status": "unchanged", "backend": current,
                "state_generation": snapshot.describe()["state_generation"]}

    question_scripts = []
    numerical_workbooks = []
    for question in sorted(state.get("subproblems") or {}):
        name = stage.question_name(question)
        number = stage.question_number(name)
        if number is None:
            raise PlotBackendError(f"Cannot resolve Figure scope: {question}")
        ref = resolve_question_script(root, state, question, name, number)
        target = f"{name}求解/q{number}_plot.{ 'py' if target_backend == 'python' else 'm'}"
        question_scripts.append({
            "question": question, "current": ref.relative,
            "current_exists": ref.path.is_file(), "target": target,
            "current_hash_field": ref.hash_field,
        })
        entry = state["subproblems"][question]
        for field in ("solution_workbook", "result_analysis_workbook", "robustness_workbook"):
            if entry.get(field):
                numerical_workbooks.append(entry[field])

    artifacts = state.get("artifacts") or {}
    approved = artifacts.get("approved_figures") or []
    if not isinstance(approved, list):
        raise PlotBackendError("approved_figures must be an array")
    approved_figures = []
    for relative in approved:
        path = transaction._guarded_path(root, relative)
        approved_figures.append({"path": relative, "exists": path.is_file()})
    publication = set()
    for field in ("papers", "docx"):
        entries = artifacts.get(field) or []
        if not isinstance(entries, list):
            raise PlotBackendError(f"artifacts.{field} must be an array")
        publication.update(item for item in entries if isinstance(item, str) and item)
    for field in ("latex_source", "compiled_pdf", "compile_report"):
        if artifacts.get(field):
            publication.add(artifacts[field])
    framework = (state.get("paper_framework") or {}).get("path")
    if framework:
        publication.add(framework)
    paper_dependencies = [
        {"path": relative, "exists": transaction._guarded_path(root, relative).is_file()}
        for relative in sorted(publication)
    ]
    preprocessing = state.get("preprocessing") or {}
    shared = None
    if preprocessing.get("decision") == "project_level":
        current_ext = "py" if current == "python" else "m"
        target_ext = "py" if target_backend == "python" else "m"
        source = f"数据预处理/data_process.{current_ext}"
        shared = {"current": source,
                  "current_exists": transaction._guarded_path(root, source).is_file(),
                  "target": f"数据预处理/data_process.{target_ext}"}
    snapshot.assert_current()
    return {
        "status": "preview_only", "current_backend": current,
        "target_backend": target_backend,
        "state_generation": snapshot.describe()["state_generation"],
        "question_scripts": question_scripts,
        "shared_preprocessing_figure": shared,
        "approved_figures_to_revalidate": approved_figures,
        "paper_dependencies_to_review": paper_dependencies,
        "numerical_workbooks_to_preserve": sorted(set(numerical_workbooks)),
        "requires_new_figure_review": True,
        "execution_authorized": False,
        "model_approval_changed": False,
        "accepted_numerical_results_changed": False,
    }


def main() -> int:
    """Inspect or select one backend; returns real state facts, never approvals."""
    import argparse
    import json
    import project_transaction as transaction
    from runtime_assurance import ProjectStateSnapshot

    parser = argparse.ArgumentParser(description="Project-level Figure backend control")
    commands = parser.add_subparsers(dest="action", required=True)
    inspect = commands.add_parser("inspect", help="Read current Figure backend choice")
    inspect.add_argument("project_root", type=Path)
    select = commands.add_parser("select", help="Choose Python/MATLAB once using CAS")
    select.add_argument("project_root", type=Path)
    select.add_argument("--backend", choices=sorted(BACKENDS), required=True)
    select.add_argument("--reason", required=True)
    select.add_argument("--expected-generation", required=True, type=int)
    preview = commands.add_parser("preview", help="Read-only whole-project Figure migration impact")
    preview.add_argument("project_root", type=Path)
    preview.add_argument("--target-backend", choices=sorted(BACKENDS), required=True)
    args = parser.parse_args()
    try:
        if args.action == "inspect":
            snap = ProjectStateSnapshot.capture(args.project_root)
            result = {"plotting": inspect_plotting(snap.payload()),
                      "state_snapshot": snap.describe()}
            snap.assert_current()
        elif args.action == "preview":
            result = preview_project_plot_backend_migration(
                args.project_root, target_backend=args.target_backend,
            )
        else:
            result = select_project_plot_backend(
                args.project_root, backend=args.backend,
                reason=args.reason, expected_generation=args.expected_generation,
            )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if args.action != "inspect" or not result["plotting"]["issues"] else 2
    except (OSError, ValueError, transaction.ProjectTransactionError) as exc:
        print(json.dumps({"status": "blocked", "issues": [str(exc)]}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
