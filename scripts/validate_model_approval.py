#!/usr/bin/env python3
"""Validate Model Challenge and Human Model Approval before task-code delivery."""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml
from semantic_identity import (
    dependency_alignment_issues,
    framework_semantic_evidence,
    past_approval_conflict,
    read_framework_semantic_evidence,
    semantic_revision_issues,
    validated_semantic_changes,
)

APPROVED = "approved"
CHALLENGE_PASSED = "passed"
SEMANTIC_IDENTITY_SCHEMA_VERSION = "1.0.0"
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
STRUCTURED_IDENTITY_FIELDS = {
    "semantic_identity_schema_version",
    "semantic_identity_hash",
    "validated_semantic_identity_hash",
    "approved_semantic_identity_hash",
    "semantic_text_hash",
}


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


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and bool(SHA256_RE.fullmatch(value))


def _uses_structured_identity(spec: dict[str, Any]) -> bool:
    """Any structured field opts the question into structured identity; never partial-fallback."""
    return any(name in spec for name in STRUCTURED_IDENTITY_FIELDS)


def validate_question(
    question: str,
    spec: dict[str, Any],
    *,
    allow_legacy_read_only: bool = False,
) -> list[str]:
    errors: list[str] = []
    challenge = spec.get("model_challenge_status")
    approval = spec.get("human_model_approval_status")
    current_revision = spec.get("semantic_revision")
    approved_revision = spec.get("approved_semantic_revision")

    if challenge != CHALLENGE_PASSED:
        errors.append(
            f"{question}: model_challenge_status must be '{CHALLENGE_PASSED}', got {challenge!r}"
        )
    if approval != APPROVED:
        errors.append(
            f"{question}: human_model_approval_status must be '{APPROVED}', got {approval!r}"
        )
    errors.extend(f"{question}: {issue}" for issue in semantic_revision_issues(
        spec, required=("semantic_revision", "approved_semantic_revision")))
    if approved_revision != current_revision:
        errors.append(
            f"{question}: approved_semantic_revision {approved_revision!r} does not match current semantic_revision {current_revision!r}"
        )

    if _uses_structured_identity(spec):
        schema_version = spec.get("semantic_identity_schema_version")
        current_hash = spec.get("semantic_identity_hash")
        validated_hash = spec.get("validated_semantic_identity_hash")
        approved_hash = spec.get("approved_semantic_identity_hash")
        if schema_version != SEMANTIC_IDENTITY_SCHEMA_VERSION:
            errors.append(
                f"{question}: semantic_identity_schema_version must be '{SEMANTIC_IDENTITY_SCHEMA_VERSION}', got {schema_version!r}"
            )
        if not _is_sha256(current_hash):
            errors.append(
                f"{question}: current semantic_identity_hash must be a 64-character SHA256 hex string"
            )
        if not _is_sha256(validated_hash):
            errors.append(
                f"{question}: validated_semantic_identity_hash must be a 64-character SHA256 hex string"
            )
        elif _is_sha256(current_hash) and validated_hash != current_hash:
            errors.append(
                f"{question}: validated_semantic_identity_hash does not match current semantic_identity_hash"
            )
        if not _is_sha256(approved_hash):
            errors.append(
                f"{question}: approved_semantic_identity_hash must be a 64-character SHA256 hex string"
            )
        elif _is_sha256(current_hash) and approved_hash != current_hash:
            errors.append(
                f"{question}: approved_semantic_identity_hash does not match current semantic_identity_hash"
            )
        return errors

    current_hash = spec.get("semantic_hash")
    approved_hash = spec.get("approved_semantic_hash")
    if not _is_sha256(current_hash):
        errors.append(f"{question}: current semantic_hash must be a 64-character SHA256 hex string")
    if not _is_sha256(approved_hash):
        errors.append(f"{question}: approved_semantic_hash must be a 64-character SHA256 hex string")
    elif _is_sha256(current_hash) and approved_hash != current_hash:
        errors.append(f"{question}: approved_semantic_hash does not match current semantic_hash")
    if not allow_legacy_read_only:
        errors.append(
            f"{question}: legacy semantic_hash approval is read-only compatibility; establish and validate a current SIB, rerun Model Challenge, and explicitly approve semantic_identity_hash before task-code delivery"
        )
    return errors


def pending_semantic_approval_issues(
    subproblems: Mapping[str, Any], inspections: Mapping[str, Mapping[str, Any]],
    *, transition_contract: Mapping[str, Any] | None = None,
) -> dict[str, list[str]]:
    """Project unsynchronized changes through the same typed rules used by the writer."""
    if not isinstance(subproblems, Mapping):
        return {}
    causes = dependency_alignment_issues(subproblems, inspections)
    for question, entry in subproblems.items():
        if not isinstance(entry, Mapping):
            continue
        inspection = inspections.get(question, {})
        if _is_sha256(entry.get("validated_semantic_identity_hash")) and inspection.get("mode") != "semantic_identity_v1":
            detail = inspection.get("error") or "current framework lacks a previously validated SIB"
            causes.setdefault(question, []).append(f"{question}: {detail}")
            continue
        identity_changed, revision_changed = validated_semantic_changes(entry, inspection)
        if identity_changed:
            causes.setdefault(question, []).append(f"{question}: current SIB differs from the validated semantic identity")
        if revision_changed:
            causes.setdefault(question, []).append(
                f"{question}: semantic_revision {entry.get('semantic_revision')!r} is not bound to validated_semantic_revision "
                f"{entry.get('validated_semantic_revision')!r}"
            )
        if past_approval_conflict(entry, inspection):
            causes.setdefault(question, []).append(
                f"{question}: recorded approval binds an older or different model than the validated SIB and revision"
            )
    if not causes:
        return {}

    from validate_semantic_governance import STATE_TRANSITION_CONTRACT_PATH, apply_semantic_transitions

    if transition_contract is None:
        transition_contract = load_yaml(STATE_TRANSITION_CONTRACT_PATH)

    # Only graph inputs are needed. The writer mutates the projection, never the supplied state.
    projection = {"subproblems": {
        question: {
            "depends_on": entry.get("depends_on") if isinstance(entry.get("depends_on"), list) else [],
            "semantic_change_categories": entry.get("semantic_change_categories", []),
            "model_challenge_status": entry.get("model_challenge_status"),
        }
        for question, entry in subproblems.items() if isinstance(entry, Mapping)
    }}
    blockers: dict[str, list[str]] = {}
    for report in apply_semantic_transitions(projection, causes, transition_contract):
        source = report["source"]
        for row in report["transitions"]:
            if row["status_updates"].get("model_challenge_status") != "stale":
                continue
            question = row["question"]
            target_issues = blockers.setdefault(question, [])
            for issue in causes[source]:
                message = issue if source == question else f"{question}: upstream approval is stale ({issue})"
                if message not in target_issues:
                    target_issues.append(message)
    return blockers


def _evaluate_model_receipts(project_root: Path, question: str) -> Mapping[str, Any]:
    from review_receipt_consumption import evaluate_gate
    return evaluate_gate(project_root, gate="model_challenge", questions=[question])


def validate_comparison_approval(
    project_root: Path, state: Mapping[str, Any], entry: Mapping[str, Any], question: str,
    *, specs=None, review_report=None, transition_contract=None,
) -> list[str]:
    """Reuse Model Approval for a separately identified analysis comparison scope.

    A recorded scope verdict is not a numerical acceptance or a replacement for
    the current primary lock. Opt-in C review qualification remains separately owned.
    """
    from analysis_comparison import enabled, inspect_plan, scope_sha256

    if not enabled(entry):
        return []
    errors = validate_question(question, dict(entry))
    try:
        # Extracted comparison specs contain no primary SIB or upstream sections.
        framework = (specs if isinstance(specs, str)
                     else (Path(project_root) / "模型论文框架.md").read_text(encoding="utf-8"))
        inspections, framework_error = framework_semantic_evidence(framework)
        if framework_error:
            errors.append(framework_error)
        issues = pending_semantic_approval_issues(state.get("subproblems", {}), inspections,
                                                transition_contract=transition_contract)
        errors.extend(issues.get(question, []))
        actual = inspections.get(question, {}).get("semantic_identity_hash")
        if actual != entry.get("semantic_identity_hash"):
            errors.append(f"{question}: comparison baseline differs from current primary framework SIB")
        report = inspect_plan(entry, question=question, specs=framework)
        errors.extend(f"{question}: {issue}" for issue in report["issues"])
        if specs is not None and not isinstance(specs, str) and scope_sha256(specs) != report["scope_sha256"]:
            errors.append(f"{question}: supplied comparison scope differs from the current framework")
        if "review_receipt_policy" in state:
            from review_receipt_consumption import evaluate_gate

            receipt = (review_report if review_report is not None else
                       evaluate_gate(Path(project_root), gate="model_challenge", questions=[question], comparison_scope=True))
            if not isinstance(receipt, Mapping):
                errors.append(f"{question}: comparison scope receipt returned no structured report")
                return list(dict.fromkeys(errors))
            if receipt.get("status") != "not_assessed" or receipt.get("issues"):
                if (receipt.get("status") != "passed" or receipt.get("qualification") != "scoped_receipt_eligible"
                        or receipt.get("issues")):
                    errors.append(f"{question}: comparison-scope review receipt qualification is incomplete")
                    errors.extend(f"{question}: {issue}" for issue in receipt.get("issues", []))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        errors.append(f"{question}: comparison approval inspection failed: {exc}")
    return list(dict.fromkeys(errors))


def _necessary_model_upstreams(
    subproblems: Mapping[str, Any], targets: Iterable[str],
) -> tuple[list[str], list[str]]:
    """Return only typed model prerequisites; preserve legacy model read behavior.

    Malformed dependency declarations are reported by the existing semantic
    alignment authority. Normalize ONLY this traversal's temporary graph so
    one malformed Qn cannot crash unrelated model approval validation.
    Historical untyped strings remain readable here, but code-delivery's
    separate execution-dependency gate still fails closed until typed.
    """
    from state_transitions import dependency_cycles, dependency_edges
    incoming: dict[str, set[str]] = {}
    issues: list[str] = []
    safe_graph = {
        name: (
            entry if isinstance(entry, Mapping)
            and isinstance(entry.get("depends_on", []), list)
            else {"depends_on": []}
        )
        for name, entry in subproblems.items()
    }
    edges = dependency_edges(safe_graph)
    for edge in edges:
        if edge["kind"] == "model":
            incoming.setdefault(edge["target"], set()).add(edge["source"])
    origins = set(targets)
    visited: set[str] = set()
    queue = list(origins)
    while queue:
        question = queue.pop()
        if question in visited:
            continue
        if question not in subproblems:
            issues.append(f"{question}: upstream model dependency is not registered")
            continue
        visited.add(question)
        queue.extend(incoming.get(question, ()))
    # Historical string dependencies do not revoke a current mathematical
    # Model Approval by themselves. Typed execution input qualification is
    # enforced independently by question_dependency_gate at Code Delivery.
    for cycle in dependency_cycles(safe_graph):
        chain = set(cycle.split(" -> "))
        if chain and chain.issubset(visited):
            issues.append(f"model prerequisite cycle requires joint-model review: {cycle}")
    return sorted(visited - origins, key=lambda q: int(q[1:])), list(dict.fromkeys(issues))


def validate_state(
    path: Path,
    questions: Iterable[str],
    *,
    allow_legacy_read_only: bool = False,
    project_root: Path | None = None,
    comparison_scope: bool = False,
) -> list[str]:
    state = load_yaml(path)
    subproblems = state.get("subproblems", {})
    errors: list[str] = []
    requested = list(questions)
    selected_questions = iter_questions(state, requested)
    upstreams, upstream_issues = (
        _necessary_model_upstreams(subproblems, selected_questions)
        if requested else ([], [])
    )
    errors.extend(upstream_issues)
    questions_to_validate = list(dict.fromkeys([*selected_questions, *upstreams]))
    for question in questions_to_validate:
        spec = subproblems.get(question, {})
        if not isinstance(spec, dict):
            errors.append(f"{question}: subproblem state must be a mapping")
            continue
        errors.extend(
            validate_question(
                question,
                spec,
                allow_legacy_read_only=allow_legacy_read_only,
            )
        )
    root = Path(project_root).resolve() if project_root is not None else None
    state_path = Path(path).resolve()
    if root is None and state_path.name == "project_state.yaml" and state_path.parent.name == "state":
        root = state_path.parent.parent
    if root is not None:
        inspections, framework_error = read_framework_semantic_evidence(root / "模型论文框架.md")
        blockers = pending_semantic_approval_issues(subproblems, inspections)
        for question in questions_to_validate:
            issues = blockers.get(question, [])
            if issues and framework_error:
                errors.append(f"{question}: {framework_error}")
            errors.extend(issues)
            # A current approved upstream model must also match actual file-backed
            # SIB bytes, not just equal hash fields in the State mapping.
            if question in upstreams and _uses_structured_identity(dict(subproblems.get(question, {}))):
                inspection = inspections.get(question) or {}
                if (inspection.get("mode") != "semantic_identity_v1"
                        or inspection.get("semantic_identity_hash") !=
                        subproblems[question].get("semantic_identity_hash")):
                    errors.append(
                        f"{question}: necessary upstream current SIB does not match its approved State identity"
                    )
    if comparison_scope:
        if root is None:
            errors.append("comparison approval requires an explicit project root")
        else:
            for question in selected_questions:
                errors.extend(validate_comparison_approval(root, state, subproblems[question], question))
    policy_active = "review_receipt_policy" in state
    if root is not None and state_path != (root / "state/project_state.yaml").resolve():
        canonical_path = root / "state/project_state.yaml"
        canonical_state = (load_yaml(canonical_path)
                           if not policy_active and canonical_path.is_file() else {})
        if policy_active or "review_receipt_policy" in canonical_state:
            errors.append(
                "model_challenge review receipts require the canonical state/project_state.yaml "
                "for this project root"
            )
            return errors
    if policy_active:
        if root is None:
            errors.append("model_challenge review receipts require an explicit project root")
        else:
            # A model dependency is not approved merely because its State
            # hashes agree; activated independent challenge receipts for every
            # necessary upstream model remain part of the same existing gate.
            for question in questions_to_validate:
                try:
                    result = _evaluate_model_receipts(root, question)
                except Exception as exc:
                    errors.append(
                        f"{question}: model_challenge review receipt evaluation failed ({type(exc).__name__})"
                    )
                    continue
                if not isinstance(result, Mapping):
                    errors.append(f"{question}: model_challenge review receipt evaluation returned no report")
                    continue
                status = result.get("status")
                issues = result.get("issues")
                if status == "not_assessed" and not issues:
                    continue
                if (status == "passed" and result.get("qualification") == "scoped_receipt_eligible"
                        and not issues):
                    continue
                errors.append(f"{question}: model_challenge review receipt status is {status!r}")
                if isinstance(issues, list):
                    errors.extend(
                        f"{question}: model_challenge review receipt: {issue}"
                        for issue in issues if isinstance(issue, str)
                    )
    return errors


def resolve_state_path(project_root: Path, explicit_state: str | None) -> Path:
    if explicit_state:
        path = Path(explicit_state)
        return path if path.is_absolute() else project_root / path
    return project_root / "state" / "project_state.yaml"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="project root containing state/project_state.yaml",
    )
    parser.add_argument(
        "--state",
        default=None,
        help="optional state YAML path, absolute or relative to project_root",
    )
    parser.add_argument(
        "--question",
        action="append",
        default=[],
        help="question id such as Q1; repeat for multiple questions; default validates all",
    )
    parser.add_argument(
        "--comparison-scope", action="store_true",
        help="also validate activated analysis comparison scopes without changing the primary lock",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="accepted for gate CLI parity; approval mismatches and legacy migration requirements are always hard failures",
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    state_path = resolve_state_path(project_root, args.state)
    try:
        errors = validate_state(state_path, args.question, project_root=project_root,
                                comparison_scope=args.comparison_scope)
    except (FileNotFoundError, ValueError) as exc:
        print("MODEL_APPROVAL: FAIL")
        print(f"- {exc}")
        return 1

    if errors:
        print("MODEL_APPROVAL: FAIL")
        for item in errors:
            print(f"- {item}")
        return 1

    print("MODEL_APPROVAL: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
