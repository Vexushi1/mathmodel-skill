#!/usr/bin/env python3
"""Read-only project-backend preflight for the planned v10 state transition.

This inspector classifies declarations, not complete Schema/receipt validity. It
neither selects a backend nor grants execution eligibility. Current v9 runtime
selection remains in its existing Authority until the coordinated cutover.
"""
from __future__ import annotations

import argparse
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from runtime_assurance import ProjectStateReadError, ProjectStateSnapshot
from stage_code import BACKENDS

POLICY_FIELDS = ("solver_backend", "solver_backend_selection_reason")
STAGE_FIELDS = {"backend", "selection_reason", "bundle_sha256", "validated_bundle_sha256"}
NUMERICAL_FIELDS = ("code", "result_analysis_code", "solution_workbook", "result_analysis_workbook")


def _backend(value: Any) -> bool:
    return isinstance(value, str) and value in BACKENDS


def _reason(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def inspect_backend_declarations(
    state: Mapping[str, Any], *, requested_backend: str | None = None,
) -> dict[str, Any]:
    """Classify the whole project's declarations without reading files or mutating state."""
    if not isinstance(state, Mapping):
        raise ValueError("project state must be a mapping")
    if requested_backend is not None and requested_backend not in ("auto", "python", "matlab"):
        raise ValueError("requested backend must be auto, python or matlab")
    issues: list[str] = []
    execution = state.get("execution", {})
    if not isinstance(execution, Mapping):
        issues.append("execution must be a mapping")
        execution = {}
    subproblems = state.get("subproblems", {})
    if not isinstance(subproblems, Mapping):
        issues.append("subproblems must be a mapping")
        subproblems = {}
    present = [name in execution for name in POLICY_FIELDS]
    selected = execution.get(POLICY_FIELDS[0])
    if any(present):
        if not all(present):
            issues.append("project backend and selection reason must be present together")
        if not _backend(selected):
            issues.append("execution.solver_backend must be python or matlab, never auto")
        if not _reason(execution.get(POLICY_FIELDS[1])):
            issues.append("project backend selection reason must be a non-empty string")

    declarations: list[dict[str, Any]] = []
    has_numerical_state = False
    has_legacy_selectors = False
    missing_stage_backend = False
    for question, entry in sorted(subproblems.items(), key=lambda item: str(item[0])):
        if not isinstance(question, str) or not isinstance(entry, Mapping):
            issues.append(f"subproblem {question!r} must have a string key and mapping record")
            continue
        has_numerical_state |= any(entry.get(name) for name in NUMERICAL_FIELDS)
        stages = entry.get("solver_execution", {})
        if not isinstance(stages, Mapping):
            issues.append(f"{question}.solver_execution must be a mapping")
            continue
        if set(stages) - {"primary", "analysis"}:
            issues.append(f"{question}.solver_execution contains unknown stages")
        for stage, code_field in (("primary", "code"), ("analysis", "result_analysis_code")):
            record = stages.get(stage, {})
            if not isinstance(record, Mapping):
                issues.append(f"{question}.{stage} must be a mapping")
                continue
            has_numerical_state |= stage in stages
            if set(record) - STAGE_FIELDS:
                issues.append(f"{question}.{stage} contains unknown execution fields")
            legacy = "backend" in record or "selection_reason" in record
            has_legacy_selectors |= legacy
            actual = record.get("backend")
            if legacy and (not _backend(actual) or not _reason(record.get("selection_reason"))):
                issues.append(f"{question}.{stage} legacy backend/reason pair is malformed")
            for field in ("bundle_sha256", "validated_bundle_sha256"):
                value = record.get(field)
                if field in record and (not isinstance(value, str) or len(value) != 64
                                        or any(c not in "0123456789abcdefABCDEF" for c in value)):
                    issues.append(f"{question}.{stage}.{field} must be a SHA-256 string")
            if "validated_bundle_sha256" in record and "bundle_sha256" not in record:
                issues.append(f"{question}.{stage} validated bundle requires a delivered bundle")
            code = entry.get(code_field)
            if code is not None and not isinstance(code, str):
                issues.append(f"{question}.{code_field} must be a string")
            workbook_field = "solution_workbook" if stage == "primary" else "result_analysis_workbook"
            execution_field = "primary_execution_status" if stage == "primary" else "analysis_execution_status"
            numerical_record = bool(entry.get(workbook_field)) or entry.get(execution_field) in (
                "code_delivered", "awaiting_user_execution", "workbook_received", "accepted", "rejected", "redo_required",
            )
            has_numerical_state |= numerical_record
            if record or code or stage in stages or numerical_record:
                declarations.append({
                    "question": question, "stage": stage,
                    "declared_backend": actual if _backend(actual) else None,
                    "code": code if isinstance(code, str) else None,
                    "artifact_identity_verified": False,
                })
                missing_stage_backend |= not _backend(actual)
            expected = selected if _backend(selected) else actual
            if isinstance(code, str) and code and _backend(expected):
                if Path(code).suffix.lower() != BACKENDS[expected]:
                    issues.append(f"{question}.{stage} declared code suffix conflicts with backend {expected}")

    candidates = {row["declared_backend"] for row in declarations if row["declared_backend"]}
    if any(present) and has_legacy_selectors:
        issues.append("root policy and legacy stage selectors cannot coexist in canonical state")
    if issues:
        kind = "invalid"
    elif any(present):
        kind = "canonical_declarations"
    elif has_legacy_selectors:
        kind = "legacy_mixed" if len(candidates) > 1 else (
            "legacy_unresolved" if missing_stage_backend else "legacy_consistent"
        )
    elif has_numerical_state:
        kind = "legacy_unresolved"
    else:
        kind = "unselected"
    request_conflict = bool(_backend(selected) and requested_backend not in (None, "auto", selected))
    if request_conflict:
        issues.append(f"requested backend {requested_backend} conflicts with project backend {selected}")
    return {
        "scope": "project", "kind": kind, "diagnostic_only": True,
        "selected_backend": selected if _backend(selected) else None,
        "candidate_backend": next(iter(candidates)) if kind == "legacy_consistent" else None,
        "candidate_evidence": "declarations_only_not_artifact_validation",
        "requested_backend": requested_backend, "request_conflict": request_conflict,
        "declarations": declarations, "issues": issues,
        "schema_validated": False, "environment_verified": False, "execution_authorized": False,
    }


def inspect_project(project_root: str | Path, *, requested_backend: str | None = None) -> dict[str, Any]:
    """Inspect one consistent state snapshot; do not create files or recover journals."""
    snapshot = ProjectStateSnapshot.capture(project_root)
    report = inspect_backend_declarations(snapshot.payload(), requested_backend=requested_backend)
    report["state_snapshot"] = snapshot.describe()
    snapshot.assert_current()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    operations = parser.add_subparsers(dest="operation", required=True)
    inspect = operations.add_parser("inspect", help="read-only diagnostic; not selection or migration")
    inspect.add_argument("--project-root", required=True)
    inspect.add_argument("--requested-backend", choices=["auto", "python", "matlab"])
    args = parser.parse_args()
    try:
        report = inspect_project(args.project_root, requested_backend=args.requested_backend)
    except ProjectStateReadError as exc:
        report = {"diagnostic_only": True, "status": exc.code, "issues": [str(exc)],
                  "execution_authorized": False}
        print(yaml.safe_dump(report, allow_unicode=True, sort_keys=False))
        return 2
    print(yaml.safe_dump(report, allow_unicode=True, sort_keys=False))
    return 2 if report["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
