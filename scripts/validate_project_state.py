#!/usr/bin/env python3
"""Validate an HSK project-state file against structure and stage semantics."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "core" / "project_state.schema.yaml"
VALIDATED_STATUSES = {"validated", "written", "completed"}
WRITTEN_STATUSES = {"written", "completed"}


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _artifact_exists(project_root: Path, value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    return (project_root / value).exists()


def validate_state_payload(
    payload: Mapping[str, Any],
    *,
    project_root: Path,
    schema_path: Path = SCHEMA_PATH,
) -> list[str]:
    """Return structural and semantic violations without mutating the state."""
    issues: list[str] = []
    schema = load_yaml(schema_path)
    validator = Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(payload), key=lambda item: list(item.path)):
        location = "/".join(str(part) for part in error.path) or "<root>"
        issues.append(f"schema {location}: {error.message}")

    requirements = payload.get("requirements", {})
    completed = set(requirements.get("completed", []))
    pending = set(requirements.get("pending", []))
    if completed.intersection(pending):
        issues.append("requirements.completed and requirements.pending must be disjoint")
    if requirements.get("total") != len(completed | pending):
        issues.append("requirements.total must equal the number of unique completed and pending items")

    for name, state in payload.get("subproblems", {}).items():
        if not isinstance(state, Mapping):
            continue
        status = str(state.get("status", ""))
        capabilities = state.get("capabilities", {}) or {}
        if status in VALIDATED_STATUSES:
            for field in ("solution_workbook", "robustness_workbook"):
                if not _artifact_exists(project_root, state.get(field)):
                    issues.append(f"{name}.{field} must exist when status is {status}")
            if not state.get("evidence"):
                issues.append(f"{name}.evidence must be non-empty when status is {status}")
            if state.get("validation_status") != "passed":
                issues.append(f"{name}.validation_status must be passed when status is {status}")
            if state.get("artifacts_stale") is True:
                issues.append(f"{name} cannot be {status} while artifacts_stale is true")
            data_hash = state.get("data_hash")
            validated_data_hash = state.get("validated_data_hash")
            if data_hash and validated_data_hash and data_hash != validated_data_hash:
                issues.append(f"{name} validated_data_hash does not match current data_hash")
            model_hash = state.get("model_hash")
            validated_model_hash = state.get("validated_model_hash")
            if model_hash and validated_model_hash and model_hash != validated_model_hash:
                issues.append(f"{name} validated_model_hash does not match current model_hash")
            if capabilities.get("has_explicit_constraints"):
                value = state.get("max_constraint_violation")
                tolerance = state.get("tolerance")
                if value is None or tolerance is None:
                    issues.append(f"{name} requires tolerance and max_constraint_violation")
                elif float(value) > float(tolerance):
                    issues.append(f"{name} maximum constraint violation exceeds tolerance")
            if state.get("optimality_claim") in {"proven_optimal", "global"}:
                if state.get("optimality_gap") is None:
                    issues.append(f"{name} global/proven optimality claim requires optimality_gap")
        if status in WRITTEN_STATUSES:
            paper = state.get("paper_source")
            if paper and not _artifact_exists(project_root, paper):
                issues.append(f"{name}.paper_source does not exist")

    project = payload.get("project", {})
    if project.get("current_phase") == "completed":
        if pending:
            issues.append("completed project cannot retain pending requirements")
        if payload.get("next_gate", {}).get("module") != "completed":
            issues.append("completed project must set next_gate.module to completed")
    return issues


def validate_state_file(path: Path, *, project_root: Path | None = None) -> list[str]:
    root = (project_root or path.parent.parent).resolve()
    return validate_state_payload(load_yaml(path), project_root=root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("state", nargs="?", default="state/project_state.yaml")
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()
    state_path = Path(args.state).resolve()
    if not state_path.is_file():
        raise SystemExit(f"project state not found: {state_path}")
    issues = validate_state_file(state_path, project_root=Path(args.project_root).resolve())
    if issues:
        print("HSK project state: ISSUES FOUND")
        for issue in issues:
            print("-", issue)
        return 1
    print("HSK project state: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
