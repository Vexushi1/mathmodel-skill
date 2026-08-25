#!/usr/bin/env python3
"""Validate Model Challenge and Human Model Approval before task-code delivery."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable

import yaml

APPROVED = "approved"
CHALLENGE_PASSED = "passed"


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def iter_questions(state: dict[str, Any], requested: Iterable[str]) -> list[str]:
    subproblems = state.get("subproblems", {})
    if not isinstance(subproblems, dict) or not subproblems:
        raise ValueError("project state has no subproblems")
    wanted = [item for item in requested if item]
    if not wanted:
        return sorted(str(key) for key in subproblems)
    missing = [item for item in wanted if item not in subproblems]
    if missing:
        raise ValueError(f"unknown subproblems: {missing}")
    return wanted


def validate_question(question: str, spec: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    challenge = spec.get("model_challenge_status")
    approval = spec.get("human_model_approval_status")
    current_revision = spec.get("semantic_revision")
    approved_revision = spec.get("approved_semantic_revision")
    current_hash = spec.get("semantic_hash")
    approved_hash = spec.get("approved_semantic_hash")

    if challenge != CHALLENGE_PASSED:
        errors.append(
            f"{question}: model_challenge_status must be '{CHALLENGE_PASSED}', got {challenge!r}"
        )
    if approval != APPROVED:
        errors.append(
            f"{question}: human_model_approval_status must be '{APPROVED}', got {approval!r}"
        )
    if not isinstance(current_revision, int) or current_revision < 1:
        errors.append(f"{question}: semantic_revision must be a positive integer")
    if approved_revision != current_revision:
        errors.append(
            f"{question}: approved_semantic_revision {approved_revision!r} does not match current semantic_revision {current_revision!r}"
        )
    if not isinstance(current_hash, str) or len(current_hash) != 64:
        errors.append(f"{question}: current semantic_hash must be a 64-character SHA256 hex string")
    if approved_hash != current_hash:
        errors.append(
            f"{question}: approved_semantic_hash does not match current semantic_hash"
        )
    return errors


def validate_state(path: Path, questions: Iterable[str]) -> list[str]:
    state = load_yaml(path)
    subproblems = state.get("subproblems", {})
    errors: list[str] = []
    for question in iter_questions(state, questions):
        spec = subproblems.get(question, {})
        if not isinstance(spec, dict):
            errors.append(f"{question}: subproblem state must be a mapping")
            continue
        errors.extend(validate_question(question, spec))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--state",
        default="state/project_state.yaml",
        help="project state YAML path",
    )
    parser.add_argument(
        "--question",
        action="append",
        default=[],
        help="question id such as Q1; repeat for multiple questions; default validates all",
    )
    args = parser.parse_args()

    try:
        errors = validate_state(Path(args.state), args.question)
    except (FileNotFoundError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc

    if errors:
        print("MODEL_APPROVAL: FAIL")
        for item in errors:
            print(f"- {item}")
        return 1

    print("MODEL_APPROVAL: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
