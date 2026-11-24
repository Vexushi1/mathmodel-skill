#!/usr/bin/env python3
"""Validate problem-contract, semantic-closure and local paper-stale gates without running task code."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml
from jsonschema import Draft202012Validator

SCRIPT_DIR = str(Path(__file__).resolve().parent)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from semantic_identity import (  # noqa: E402
    SemanticIdentityError,
    dependency_alignment_issues,
    past_approval_conflict,
    validated_semantic_changes,
    is_semantic_revision,
    semantic_revision_issues,
    inspect_question_semantics,
    question_sections as _question_sections,
    semantic_scope as _semantic_scope,
    sha256_text,
)
import state_transitions as STATE_TRANSITIONS  # noqa: E402
import project_transaction as PROJECT_TX  # noqa: E402
import stage_code as STAGE_CODE  # noqa: E402

SEMANTIC_GOVERNANCE_VERSION = "1.0.0"
STATE_TRANSITION_CONTRACT_PATH = Path(__file__).resolve().parents[1] / "core" / "state_transition_contract.yaml"
DESIGNED_OR_LATER = {"designed", "solved", "analyzed", "validated", "written", "completed"}
CHANGE_CATEGORIES = {
    "initial_design",
    "problem_definition",
    "data_scope",
    "variable",
    "parameter",
    "assumption",
    "objective",
    "constraint",
    "preprocessing",
    "algorithm",
    "dependency",
}


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


STATE_TRANSITION_CONTRACT = load_yaml(STATE_TRANSITION_CONTRACT_PATH)


def _mark_stale(entry: dict[str, Any]) -> None:
    """Compatibility helper; the transition policy itself lives in the shared Authority."""
    STATE_TRANSITIONS.apply_local_event(
        entry, "semantic_identity_changed", STATE_TRANSITION_CONTRACT
    )


def _dependency_hits_question(dependency: str, question: str) -> bool:
    return dependency == question or dependency.startswith(f"{question}.") or dependency.startswith(f"{question}:")


def _mark_paper_fragments_stale(framework: dict[str, Any], affected_questions: set[str]) -> list[str]:
    """Mark only paper fragments that actually depend on affected questions/fragments."""
    fragments = framework.get("paper_fragments", []) or []
    by_id = {
        str(item.get("id")): item
        for item in fragments
        if isinstance(item, dict) and str(item.get("id", "")).strip()
    }
    stale_ids: set[str] = set()
    for fragment_id, fragment in by_id.items():
        scope = str(fragment.get("scope", ""))
        dependencies = [str(item) for item in fragment.get("depends_on", []) or []]
        if scope in affected_questions or any(
            _dependency_hits_question(dep, question)
            for dep in dependencies
            for question in affected_questions
        ):
            stale_ids.add(fragment_id)

    changed = True
    while changed:
        changed = False
        for fragment_id, fragment in by_id.items():
            if fragment_id in stale_ids:
                continue
            dependencies = {str(item) for item in fragment.get("depends_on", []) or []}
            if dependencies & stale_ids:
                stale_ids.add(fragment_id)
                changed = True

    for fragment_id in stale_ids:
        by_id[fragment_id]["status"] = "stale"
    return sorted(stale_ids)


def _gate_issues(key: str, entry: Mapping[str, Any]) -> list[str]:
    issues: list[str] = [f"{key}: {issue}" for issue in semantic_revision_issues(entry)]
    status = str(entry.get("status", "pending"))
    if status not in DESIGNED_OR_LATER:
        return issues
    if entry.get("problem_contract_status") != "frozen":
        issues.append(f"{key}: problem_contract_status必须为frozen")
    if entry.get("semantic_closure_status") != "passed":
        issues.append(f"{key}: semantic_closure_status必须为passed")
    complexity = entry.get("complexity_sanity_status")
    if complexity != "passed":
        issues.append(f"{key}: complexity_sanity_status必须为passed，当前为{complexity or 'missing'}")
    flags = list(entry.get("complexity_sanity_flags", []) or [])
    if flags and not str(entry.get("complexity_sanity_note", "")).strip():
        issues.append(f"{key}: complexity_sanity_flags非空时必须记录复审结论")
    revision = entry.get("semantic_revision")
    if not is_semantic_revision(revision):
        issues.append(f"{key}: semantic_revision必须为>=1的整数")
    categories = set(entry.get("semantic_change_categories", []) or [])
    unknown = categories - CHANGE_CATEGORIES
    if unknown:
        issues.append(f"{key}: 未知semantic_change_categories={sorted(unknown)}")
    if not categories:
        issues.append(f"{key}: semantic_change_categories不能为空")
    return issues


def _revision_change_issues(
    key: str,
    entry: Mapping[str, Any],
    *,
    changed: bool,
) -> list[str]:
    if not changed:
        return []
    issues: list[str] = []
    revision = entry.get("semantic_revision")
    validated_revision = entry.get("validated_semantic_revision")
    if not is_semantic_revision(validated_revision) or not is_semantic_revision(revision) or revision <= validated_revision:
        issues.append(f"{key}: 语义身份已变化，但semantic_revision未递增")
    categories = set(entry.get("semantic_change_categories", []) or [])
    if not categories or categories == {"initial_design"}:
        issues.append(f"{key}: 语义变化必须记录具体semantic_change_categories")
    return issues


def _legacy_write_issue(question: str) -> str:
    return (
        f"{question}: legacy semantic_hash / validated_semantic_hash 已转为历史只读兼容；"
        "--write 需要当前模型框架提供有效SIB。不得刷新legacy semantic hash；"
        "建立structured identity后，新的task-code delivery仍必须重新通过Model Challenge与显式Human Approval"
    )


def apply_semantic_transitions(
    state: dict[str, Any], sources: Iterable[str], contract: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Apply the authority's typed transition to each source in the supplied state."""
    reports = []
    for question in sorted(set(sources)):
        entry = state["subproblems"][question]
        reports.append(STATE_TRANSITIONS.apply_transition(
            state, event="semantic_identity_changed", source_question=question, contract=contract,
            context={"semantic_change_categories": list(entry.get("semantic_change_categories") or [])},
        ))
    return reports


def _semantic_scope_questions(subproblems: Mapping[str, Any], target: str) -> tuple[list[str], list[str]]:
    """Read target plus necessary incoming model/legacy semantic dependencies.

    Result/data/parameter execution sources are qualified by the code delivery
    consumer, not by revalidating unrelated upstream numerical models here.
    """
    if target not in subproblems:
        return [], [f"{target}: 当前小问未在project_state.subproblems登记"]
    from state_transitions import dependency_edges
    incoming: dict[str, set[str]] = {}
    for edge in dependency_edges(subproblems):
        if edge["kind"] in {"model", "legacy_untyped"}:
            incoming.setdefault(edge["target"], set()).add(edge["source"])
    visited: set[str] = set()
    pending = [target]
    issues = []
    while pending:
        name = pending.pop()
        if name in visited:
            continue
        if name not in subproblems:
            issues.append(f"{target}: model/legacy upstream {name} is unregistered")
            continue
        visited.add(name)
        pending.extend(sorted(incoming.get(name, ()), reverse=True))
    return sorted(visited, key=lambda name: (int(name[1:]) if name.startswith("Q") and name[1:].isdigit() else 10**9, name)), issues


def _scoped_global_invariant_issues(state: Mapping[str, Any]) -> list[str]:
    """Keep complete global Schema and backend checks, without sibling artifact gates."""
    from runtime_assurance import validate_consumed_state_shapes, ProjectStateShapeError
    root = Path(__file__).resolve().parents[1]
    schema = load_yaml(root / "core/project_state.schema.yaml")
    result = []
    # Current M1 projects have a complete requirements roster and must satisfy
    # the entire State Schema. Older read-compatible states retain the original
    # *unscoped* gate; lacking a roster must NOT silently downgrade the new
    # scoped gate to an incomplete schema check.
    if "requirements" not in state:
        result.append("global State schema: scoped governance requires the complete registered requirements roster; use the legacy unscoped gate or explicit State migration")
    else:
        for error in Draft202012Validator(schema).iter_errors(state):
            location = "/".join(str(item) for item in error.path) or "<root>"
            result.append(f"schema {location}: {error.message}")
    try:
        validate_consumed_state_shapes(state)
    except ProjectStateShapeError as exc:
        result.append(f"global State shape: {exc}")
    backend = STAGE_CODE.inspect_project_backend_declarations(state)
    if backend["kind"] not in {"unselected", "canonical_declarations"}:
        result.append(f"global project backend: {backend['kind']}")
    result.extend(f"global project backend: {issue}" for issue in backend["issues"])
    return sorted(set(result))


def validate_project(
    root: Path, *, write: bool, strict: bool, question: str | None = None,
) -> dict[str, Any]:
    state_path = root / "state" / "project_state.yaml"
    framework_path = root / "模型论文框架.md"
    # A question-scoped write consumes the original raw State bytes as well as
    # current framework bytes. Neither generation alone nor a missing state key
    # may authorize the guarded transaction.
    scoped_state_bytes = (
        state_path.read_bytes() if question is not None and state_path.is_file() else None
    )
    if write and state_path.is_file():
        _, state, base_generation = PROJECT_TX.load_state_for_update(root)
    else:
        state = load_yaml(state_path)
        base_generation = PROJECT_TX.state_generation(state)
    issues: list[str] = []
    warnings: list[str] = []
    original_state = deepcopy(state) if question is not None else None
    if question is not None:
        issues.extend(_scoped_global_invariant_issues(state))

    if not state_path.is_file():
        issues.append("缺少 state/project_state.yaml")
    if not framework_path.is_file():
        issues.append("缺少 模型论文框架.md")
    governance_version = str(state.get("semantic_governance_version", "")).strip()
    if governance_version != SEMANTIC_GOVERNANCE_VERSION:
        message = (
            f"semantic_governance_version应为{SEMANTIC_GOVERNANCE_VERSION}；"
            "旧项目在重新进入审题/模型设计时需要迁移当前语义门字段"
        )
        if strict:
            issues.append(message)
        else:
            warnings.append(message)

    subproblems = state.get("subproblems", {}) or {}
    if not isinstance(subproblems, Mapping) or not subproblems:
        issues.append("project_state缺少subproblems")
        subproblems = {}

    scoped_questions: list[str] = []
    if question is not None:
        scoped_questions, scope_issues = _semantic_scope_questions(subproblems, question)
        issues.extend(scope_issues)
    framework_bytes = framework_path.read_bytes() if framework_path.is_file() else b""
    framework_text = framework_bytes.decode("utf-8") if framework_bytes else ""
    semantic_parse_failed = False
    try:
        sections = _question_sections(framework_text)
    except SemanticIdentityError as exc:
        issues.append(str(exc))
        sections = {}
        semantic_parse_failed = True
    semantic_hashes: dict[str, str] = {}
    semantic_identity_hashes: dict[str, str] = {}
    semantic_text_hashes: dict[str, str] = {}
    identity_modes: dict[str, str] = {}
    changed_sources: set[str] = set()
    text_changed_sources: set[str] = set()
    invalid_baselines: set[str] = set()
    migration_sources: set[str] = set()
    legacy_write_blocked_sources: set[str] = set()
    inspections: dict[str, dict[str, Any]] = {}

    for key, raw_entry in subproblems.items():
        if question is not None and key not in scoped_questions:
            continue
        if not isinstance(raw_entry, Mapping):
            issues.append(f"{key}: subproblem必须为mapping")
            continue
        entry = raw_entry
        item_question = str(key)
        issues.extend(_gate_issues(item_question, entry))
        if str(entry.get("status", "pending")) not in DESIGNED_OR_LATER:
            continue
        section = sections.get(item_question)
        if section is None:
            issues.append(f"{key}: 模型论文框架缺少对应### {key}章节")
            continue
        try:
            inspection = inspect_question_semantics(section, item_question)
        except SemanticIdentityError as exc:
            issues.append(f"{key}: {exc}")
            semantic_parse_failed = True
            continue
        inspections[item_question] = inspection
        mode = str(inspection["mode"])
        identity_modes[item_question] = mode
        text_hash = str(inspection["semantic_text_hash"])
        semantic_text_hashes[item_question] = text_hash

        if mode == "legacy_text_hash":
            # Legacy Markdown hashes remain historical provenance only. Read/diagnose them,
            # but active writes must migrate to a current SIB first.
            semantic_hashes[item_question] = text_hash
            validated_hash = str(entry.get("validated_semantic_hash", "")).strip()
            changed = bool(validated_hash) and validated_hash != text_hash
            if changed:
                changed_sources.add(item_question)
            issues.extend(_revision_change_issues(item_question, entry, changed=changed))
            if write:
                legacy_write_blocked_sources.add(item_question)
                migration_sources.add(item_question)
                issues.append(_legacy_write_issue(item_question))
            continue

        current_identity_hash = str(inspection["semantic_identity_hash"])
        semantic_identity_hashes[item_question] = current_identity_hash
        previous_text_hash = str(entry.get("semantic_text_hash", "")).strip()
        if previous_text_hash and previous_text_hash != text_hash:
            text_changed_sources.add(item_question)

        validated_identity_hash = str(entry.get("validated_semantic_identity_hash", "")).strip()
        if not validated_identity_hash:
            migration_sources.add(item_question)
            message = (
                f"{item_question}: structured semantic identity尚未建立validated baseline；"
                "使用--write初始化后，C3再完成Model Approval新hash绑定"
            )
            if strict and not write:
                issues.append(message)
            else:
                warnings.append(message)
        hash_changed, revision_changed = validated_semantic_changes(entry, inspection)
        if past_approval_conflict(entry, inspection):
            warnings.append(f"{item_question}: 已验证的当前语义与旧批准绑定不匹配，须按依赖类型重新确认")
            changed_sources.add(item_question)
        elif hash_changed or revision_changed:
            changed_sources.add(item_question)
        change_issues = _revision_change_issues(item_question, entry, changed=hash_changed)
        revision = entry.get("semantic_revision")
        validated_revision = entry.get("validated_semantic_revision")
        if (revision_changed and is_semantic_revision(revision)
                and is_semantic_revision(validated_revision) and revision < validated_revision):
            change_issues.append(f"{item_question}: semantic_revision不得低于validated_semantic_revision")
        if change_issues:
            invalid_baselines.add(item_question)
            issues.extend(change_issues)

    all_conflicts = dependency_alignment_issues(subproblems, inspections)
    conflicts = (
        all_conflicts if question is None
        else {key: messages for key, messages in all_conflicts.items() if key in scoped_questions}
    )
    for messages in conflicts.values():
        issues.extend(messages)
    # An ambiguous graph cannot advance even an upstream baseline. Report the typed
    # reach on a copy so that reconciling the declarations can replay the original change.
    # Preserve the legacy-writer retirement guard verbatim; question-scoped
    # failures add a separate fail-closed requirement.
    write_allowed = write and not legacy_write_blocked_sources and not semantic_parse_failed and not conflicts
    if question is not None and issues:
        write_allowed = False
    transition_state = state if write_allowed else deepcopy(state)
    for conflicted in conflicts:
        # An unreadable incoming edge list has no usable edges for the diagnostic
        # traversal. The conflict still seeds its consumer and all known outgoing edges.
        projected = transition_state["subproblems"][conflicted]
        if not isinstance(projected.get("depends_on", []), list):
            projected["depends_on"] = []
    transition_reports = apply_semantic_transitions(
        transition_state, changed_sources | conflicts.keys(), STATE_TRANSITION_CONTRACT
    )
    merged_transitions = STATE_TRANSITIONS.merge_transition_reports(transition_reports)
    affected = set(merged_transitions["affected_questions"])
    dependency_cycles = (
        merged_transitions["dependency_cycles"]
        or STATE_TRANSITIONS.dependency_cycles(transition_state.get("subproblems") or {})
    )
    if dependency_cycles:
        warnings.append("检测到跨问依赖环: " + "; ".join(dependency_cycles))

    stale_fragments: list[str] = []
    if write_allowed and changed_sources:
        paper_framework = state.setdefault("paper_framework", {})
        stale_fragments = _mark_paper_fragments_stale(paper_framework, affected)
        # sync_status means the framework/state record is synchronized, not that every fragment is current.
        paper_framework["sync_status"] = "current"

    if write_allowed:
        for key, inspection in inspections.items():
            entry = subproblems.get(key)
            if not isinstance(entry, dict):
                continue
            mode = str(inspection["mode"])
            text_hash = str(inspection["semantic_text_hash"])
            if mode == "legacy_text_hash":
                # write_allowed guarantees this branch is unreachable for active legacy state.
                continue

            current_identity_hash = str(inspection["semantic_identity_hash"])
            schema_version = str(inspection["semantic_identity_schema_version"])
            entry["semantic_identity_schema_version"] = schema_version
            entry["semantic_identity_hash"] = current_identity_hash
            entry["semantic_text_hash"] = text_hash
            if key not in invalid_baselines and not _gate_issues(key, entry):
                entry["validated_semantic_identity_hash"] = current_identity_hash
                entry["validated_semantic_revision"] = entry.get("semantic_revision")
        if state_path.is_file() and (question is None or state != original_state):
            expected_files = (
                {"模型论文框架.md": hashlib.sha256(framework_bytes).hexdigest(),
                 PROJECT_TX.STATE_RELATIVE_PATH: hashlib.sha256(scoped_state_bytes).hexdigest()}
                if question is not None and scoped_state_bytes is not None else None
            )
            PROJECT_TX.commit_project_state(
                root, state, expected_generation=base_generation,
                **({"expected_file_hashes": expected_files} if expected_files is not None else {}),
            )

    return {
        "status": "passed" if not issues else "failed",
        **({"scoped_questions": scoped_questions, "scope_kind": "question"} if question is not None else {}),
        "semantic_governance_version": governance_version or None,
        "identity_modes": identity_modes,
        "semantic_hashes": semantic_hashes,
        "semantic_identity_hashes": semantic_identity_hashes,
        "semantic_text_hashes": semantic_text_hashes,
        "migration_sources": sorted(migration_sources),
        "legacy_write_blocked_sources": sorted(legacy_write_blocked_sources),
        "text_changed_sources": sorted(text_changed_sources),
        "changed_sources": sorted(changed_sources),
        "affected_questions": sorted(affected),
        "stale_paper_fragments": stale_fragments,
        "state_transitions": transition_reports,
        "dependency_cycles": dependency_cycles,
        "dependency_conflicts": conflicts,
        "issues": sorted(set(issues)),
        "warnings": sorted(set(warnings)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--question", help="scope semantic checks to Qn and its necessary model dependencies")
    args = parser.parse_args()
    report = validate_project(
        args.project_root.resolve(), write=args.write, strict=args.strict, question=args.question,
    )
    print(yaml.safe_dump(report, allow_unicode=True, sort_keys=False))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
