#!/usr/bin/env python3
"""Validate problem-contract, semantic-closure and local paper-stale gates without running task code."""
from __future__ import annotations

import argparse
from copy import deepcopy
import sys
from pathlib import Path
from typing import Any, Mapping

import yaml

SCRIPT_DIR = str(Path(__file__).resolve().parent)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from semantic_identity import (  # noqa: E402
    SemanticIdentityError,
    inspect_question_semantics,
    question_sections as _question_sections,
    semantic_scope as _semantic_scope,
    sha256_text,
)
import state_transitions as STATE_TRANSITIONS  # noqa: E402
import project_transaction as PROJECT_TX  # noqa: E402

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
    issues: list[str] = []
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
    if not isinstance(revision, int) or revision < 1:
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
    if not isinstance(validated_revision, int) or not isinstance(revision, int) or revision <= validated_revision:
        issues.append(f"{key}: 语义身份已变化，但semantic_revision未递增")
    categories = set(entry.get("semantic_change_categories", []) or [])
    if not categories or categories == {"initial_design"}:
        issues.append(f"{key}: 语义变化必须记录具体semantic_change_categories")
    return issues


def validate_project(root: Path, *, write: bool, strict: bool) -> dict[str, Any]:
    state_path = root / "state" / "project_state.yaml"
    framework_path = root / "模型论文框架.md"
    if write and state_path.is_file():
        _, state, base_generation = PROJECT_TX.load_state_for_update(root)
    else:
        state = load_yaml(state_path)
        base_generation = PROJECT_TX.state_generation(state)
    issues: list[str] = []
    warnings: list[str] = []

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

    framework_text = framework_path.read_text(encoding="utf-8") if framework_path.is_file() else ""
    sections = _question_sections(framework_text)
    semantic_hashes: dict[str, str] = {}
    semantic_identity_hashes: dict[str, str] = {}
    semantic_text_hashes: dict[str, str] = {}
    identity_modes: dict[str, str] = {}
    changed_sources: set[str] = set()
    text_changed_sources: set[str] = set()
    migration_sources: set[str] = set()
    inspections: dict[str, dict[str, Any]] = {}

    for key, raw_entry in subproblems.items():
        if not isinstance(raw_entry, Mapping):
            issues.append(f"{key}: subproblem必须为mapping")
            continue
        entry = raw_entry
        question = str(key)
        issues.extend(_gate_issues(question, entry))
        if str(entry.get("status", "pending")) not in DESIGNED_OR_LATER:
            continue
        section = sections.get(question)
        if section is None:
            issues.append(f"{key}: 模型论文框架缺少对应### {key}章节")
            continue
        try:
            inspection = inspect_question_semantics(section, question)
        except SemanticIdentityError as exc:
            issues.append(f"{key}: {exc}")
            continue
        inspections[question] = inspection
        mode = str(inspection["mode"])
        identity_modes[question] = mode
        text_hash = str(inspection["semantic_text_hash"])
        semantic_text_hashes[question] = text_hash

        if mode == "legacy_text_hash":
            # Preserve the v8 contract exactly for framework sections without SIB.
            semantic_hashes[question] = text_hash
            validated_hash = str(entry.get("validated_semantic_hash", "")).strip()
            changed = bool(validated_hash) and validated_hash != text_hash
            if changed:
                changed_sources.add(question)
            issues.extend(_revision_change_issues(question, entry, changed=changed))
            continue

        current_identity_hash = str(inspection["semantic_identity_hash"])
        semantic_identity_hashes[question] = current_identity_hash
        previous_text_hash = str(entry.get("semantic_text_hash", "")).strip()
        if previous_text_hash and previous_text_hash != text_hash:
            text_changed_sources.add(question)

        validated_identity_hash = str(entry.get("validated_semantic_identity_hash", "")).strip()
        if not validated_identity_hash:
            migration_sources.add(question)
            message = (
                f"{question}: structured semantic identity尚未建立validated baseline；"
                "使用--write初始化后，C3再完成Model Approval新hash绑定"
            )
            if strict and not write:
                issues.append(message)
            else:
                warnings.append(message)
            changed = False
        else:
            changed = validated_identity_hash != current_identity_hash
            if changed:
                changed_sources.add(question)
        issues.extend(_revision_change_issues(question, entry, changed=changed))

    transition_state = state if write else deepcopy(state)
    transition_reports: list[dict[str, Any]] = []
    for key in sorted(changed_sources):
        transition_entry = ((transition_state.get("subproblems") or {}).get(key) or {})
        transition_reports.append(
            STATE_TRANSITIONS.apply_transition(
                transition_state,
                event="semantic_identity_changed",
                source_question=key,
                contract=STATE_TRANSITION_CONTRACT,
                context={
                    "semantic_change_categories": list(
                        transition_entry.get("semantic_change_categories", []) or []
                    )
                },
            )
        )
    merged_transitions = STATE_TRANSITIONS.merge_transition_reports(transition_reports)
    affected = set(merged_transitions["affected_questions"])
    dependency_cycles = (
        merged_transitions["dependency_cycles"]
        or STATE_TRANSITIONS.dependency_cycles(subproblems)
    )
    if dependency_cycles:
        warnings.append("检测到跨问依赖环: " + "; ".join(dependency_cycles))

    stale_fragments: list[str] = []
    if write and changed_sources:
        paper_framework = state.setdefault("paper_framework", {})
        stale_fragments = _mark_paper_fragments_stale(paper_framework, affected)
        # sync_status means the framework/state record is synchronized, not that every fragment is current.
        paper_framework["sync_status"] = "current"

    if write:
        for key, inspection in inspections.items():
            entry = subproblems.get(key)
            if not isinstance(entry, dict):
                continue
            mode = str(inspection["mode"])
            text_hash = str(inspection["semantic_text_hash"])
            if mode == "legacy_text_hash":
                entry["semantic_hash"] = text_hash
                current_hash = text_hash
                prior_validated = str(entry.get("validated_semantic_hash", "")).strip()
                hash_changed = bool(prior_validated) and prior_validated != current_hash
                if not _gate_issues(key, entry):
                    revision = entry.get("semantic_revision")
                    validated_revision = entry.get("validated_semantic_revision")
                    revision_ok = not hash_changed or (
                        isinstance(revision, int)
                        and (not isinstance(validated_revision, int) or revision > validated_revision)
                    )
                    categories = set(entry.get("semantic_change_categories", []) or [])
                    category_ok = not hash_changed or bool(categories - {"initial_design"})
                    if revision_ok and category_ok:
                        entry["validated_semantic_hash"] = current_hash
                        entry["validated_semantic_revision"] = revision
                continue

            current_identity_hash = str(inspection["semantic_identity_hash"])
            schema_version = str(inspection["semantic_identity_schema_version"])
            prior_validated = str(entry.get("validated_semantic_identity_hash", "")).strip()
            hash_changed = bool(prior_validated) and prior_validated != current_identity_hash
            entry["semantic_identity_schema_version"] = schema_version
            entry["semantic_identity_hash"] = current_identity_hash
            entry["semantic_text_hash"] = text_hash
            if not _gate_issues(key, entry):
                revision = entry.get("semantic_revision")
                validated_revision = entry.get("validated_semantic_revision")
                revision_ok = not hash_changed or (
                    isinstance(revision, int)
                    and (not isinstance(validated_revision, int) or revision > validated_revision)
                )
                categories = set(entry.get("semantic_change_categories", []) or [])
                category_ok = not hash_changed or bool(categories - {"initial_design"})
                if revision_ok and category_ok:
                    entry["validated_semantic_identity_hash"] = current_identity_hash
                    entry["validated_semantic_revision"] = revision
        if state_path.is_file():
            PROJECT_TX.commit_project_state(
                root, state, expected_generation=base_generation
            )

    return {
        "status": "passed" if not issues else "failed",
        "semantic_governance_version": governance_version or None,
        "identity_modes": identity_modes,
        "semantic_hashes": semantic_hashes,
        "semantic_identity_hashes": semantic_identity_hashes,
        "semantic_text_hashes": semantic_text_hashes,
        "migration_sources": sorted(migration_sources),
        "text_changed_sources": sorted(text_changed_sources),
        "changed_sources": sorted(changed_sources),
        "affected_questions": sorted(affected),
        "stale_paper_fragments": stale_fragments,
        "state_transitions": transition_reports,
        "dependency_cycles": dependency_cycles,
        "issues": sorted(set(issues)),
        "warnings": sorted(set(warnings)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    report = validate_project(args.project_root.resolve(), write=args.write, strict=args.strict)
    print(yaml.safe_dump(report, allow_unicode=True, sort_keys=False))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
