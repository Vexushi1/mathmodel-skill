#!/usr/bin/env python3
"""Validate problem-contract, semantic-closure and complexity gates without running task code."""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path
from typing import Any, Mapping

import yaml

SEMANTIC_GOVERNANCE_VERSION = "1.1.0"
SUPPORTED_GOVERNANCE_VERSIONS = {"1.0.0", "1.1.0"}
PRIMARY_STALE_LAYERS = {
    "model",
    "solution_workbook",
    "result_analysis_workbook",
    "matlab_script",
    "figure_bundle",
    "framework",
}
DESIGNED_OR_LATER = {"designed", "solved", "analyzed", "validated", "written", "completed"}
Q_HEADING_RE = re.compile(r"^###\s+(Q\d+)[:：].*$", re.MULTILINE)
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


def sha256_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip() + "\n"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _question_sections(text: str) -> dict[str, str]:
    matches = list(Q_HEADING_RE.finditer(text))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[match.group(1)] = text[match.start():end]
    return sections


def _semantic_scope(section: str) -> str | None:
    marker = "#### 当前模型口径"
    start = section.find(marker)
    if start < 0:
        return None
    end = section.find("#### 结果摘要", start + len(marker))
    if end < 0:
        end = len(section)
    return section[start:end].strip()


def _dependency_questions(entry: Mapping[str, Any]) -> set[str]:
    values: set[str] = set()
    for item in entry.get("depends_on", []) or []:
        if isinstance(item, str):
            values.add(item)
        elif isinstance(item, Mapping) and item.get("question"):
            values.add(str(item["question"]))
    return values


def _dependent_closure(subproblems: Mapping[str, Any], sources: set[str]) -> set[str]:
    affected = set(sources)
    changed = True
    while changed:
        changed = False
        for key, entry in subproblems.items():
            if key in affected or not isinstance(entry, Mapping):
                continue
            if _dependency_questions(entry) & affected:
                affected.add(str(key))
                changed = True
    return affected


def _fragment_dependency_questions(fragment: Mapping[str, Any]) -> set[str]:
    questions = {str(item) for item in (fragment.get("source_questions", []) or []) if str(item).strip()}
    for item in fragment.get("depends_on", []) or []:
        token = str(item).strip()
        match = re.match(r"^(Q[1-9][0-9]*)(?:\.|$)", token)
        if match:
            questions.add(match.group(1))
    return questions


def _affected_paper_fragment_ids(framework: Mapping[str, Any], affected_questions: set[str]) -> set[str]:
    affected_ids: set[str] = set()
    for raw in framework.get("paper_fragments", []) or []:
        if not isinstance(raw, Mapping):
            continue
        if _fragment_dependency_questions(raw) & affected_questions:
            fragment_id = str(raw.get("id", "")).strip()
            if fragment_id:
                affected_ids.add(fragment_id)
    return affected_ids


def _mark_paper_fragments_stale(framework: dict[str, Any], affected_questions: set[str]) -> set[str]:
    stale_ids: set[str] = set()
    for raw in framework.get("paper_fragments", []) or []:
        if not isinstance(raw, dict):
            continue
        dependencies = _fragment_dependency_questions(raw)
        hit = sorted(dependencies & affected_questions)
        if not hit or raw.get("status") == "not_applicable":
            continue
        raw["status"] = "stale"
        raw.setdefault("stale_reason", f"source question changed: {', '.join(hit)}")
        raw.setdefault("required_action", "revalidate this paper fragment against the current source question(s)")
        fragment_id = str(raw.get("id", "")).strip()
        if fragment_id:
            stale_ids.add(fragment_id)
    return stale_ids


def _mark_stale(entry: dict[str, Any]) -> None:
    entry["artifacts_stale"] = True
    entry["stale_layers"] = sorted(set(entry.get("stale_layers", []) or []) | PRIMARY_STALE_LAYERS)
    entry["result_quality_status"] = "pending"
    entry["result_analysis_status"] = "pending"
    entry["validation_status"] = "pending"
    entry["result_summary_status"] = "stale"
    if "primary_execution_status" in entry:
        entry["primary_execution_status"] = "pending"
    if "analysis_execution_status" in entry:
        entry["analysis_execution_status"] = "pending"


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


def validate_project(root: Path, *, write: bool, strict: bool) -> dict[str, Any]:
    state_path = root / "state" / "project_state.yaml"
    framework_path = root / "模型论文框架.md"
    state = load_yaml(state_path)
    issues: list[str] = []
    warnings: list[str] = []

    if not state_path.is_file():
        issues.append("缺少 state/project_state.yaml")
    if not framework_path.is_file():
        issues.append("缺少 模型论文框架.md")
    governance_version = str(state.get("semantic_governance_version", "")).strip()
    if governance_version not in SUPPORTED_GOVERNANCE_VERSIONS:
        message = (
            f"semantic_governance_version应为支持版本{sorted(SUPPORTED_GOVERNANCE_VERSIONS)}；"
            "旧项目在重新进入审题/模型设计时需要迁移当前语义门字段"
        )
        if strict:
            issues.append(message)
        else:
            warnings.append(message)
    elif governance_version != SEMANTIC_GOVERNANCE_VERSION:
        warnings.append(
            f"semantic_governance_version={governance_version}为兼容读取版本；当前写入版本为{SEMANTIC_GOVERNANCE_VERSION}"
        )

    subproblems = state.get("subproblems", {}) or {}
    if not isinstance(subproblems, Mapping) or not subproblems:
        issues.append("project_state缺少subproblems")
        subproblems = {}

    framework_text = framework_path.read_text(encoding="utf-8") if framework_path.is_file() else ""
    sections = _question_sections(framework_text)
    semantic_hashes: dict[str, str] = {}
    changed_sources: set[str] = set()

    for key, raw_entry in subproblems.items():
        if not isinstance(raw_entry, Mapping):
            issues.append(f"{key}: subproblem必须为mapping")
            continue
        entry = raw_entry
        issues.extend(_gate_issues(str(key), entry))
        if str(entry.get("status", "pending")) not in DESIGNED_OR_LATER:
            continue
        section = sections.get(str(key))
        if section is None:
            issues.append(f"{key}: 模型论文框架缺少对应### {key}章节")
            continue
        semantic_text = _semantic_scope(section)
        if not semantic_text:
            issues.append(f"{key}: 框架缺少#### 当前模型口径语义区")
            continue
        current_hash = sha256_text(semantic_text)
        semantic_hashes[str(key)] = current_hash
        validated_hash = str(entry.get("validated_semantic_hash", "")).strip()
        revision = entry.get("semantic_revision")
        validated_revision = entry.get("validated_semantic_revision")
        if validated_hash and validated_hash != current_hash:
            changed_sources.add(str(key))
            if not isinstance(validated_revision, int) or not isinstance(revision, int) or revision <= validated_revision:
                issues.append(f"{key}: 语义内容已变化，但semantic_revision未递增")
            categories = set(entry.get("semantic_change_categories", []) or [])
            if not categories or categories == {"initial_design"}:
                issues.append(f"{key}: 语义变化必须记录具体semantic_change_categories")

    affected = _dependent_closure(subproblems, changed_sources)
    framework_state = state.get("paper_framework", {}) or {}
    predicted_fragments = _affected_paper_fragment_ids(framework_state, affected)
    stale_paper_fragments: set[str] = set()

    if write and changed_sources:
        for key in affected:
            entry = subproblems.get(key)
            if isinstance(entry, dict):
                _mark_stale(entry)
        if isinstance(framework_state, dict):
            stale_paper_fragments = _mark_paper_fragments_stale(framework_state, affected)
            # State has changed before the human-readable framework table is resynchronized.
            framework_state["sync_status"] = "stale"
        state["semantic_governance_version"] = SEMANTIC_GOVERNANCE_VERSION

    if write:
        for key, current_hash in semantic_hashes.items():
            entry = subproblems.get(key)
            if not isinstance(entry, dict):
                continue
            entry["semantic_hash"] = current_hash
            if not _gate_issues(key, entry):
                revision = entry.get("semantic_revision")
                validated_revision = entry.get("validated_semantic_revision")
                hash_changed = bool(entry.get("validated_semantic_hash")) and entry.get("validated_semantic_hash") != current_hash
                revision_ok = not hash_changed or (
                    isinstance(revision, int)
                    and (not isinstance(validated_revision, int) or revision > validated_revision)
                )
                categories = set(entry.get("semantic_change_categories", []) or [])
                category_ok = not hash_changed or bool(categories - {"initial_design"})
                if revision_ok and category_ok:
                    entry["validated_semantic_hash"] = current_hash
                    entry["validated_semantic_revision"] = revision
        if state_path.is_file():
            state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")

    return {
        "status": "passed" if not issues else "failed",
        "semantic_governance_version": governance_version or None,
        "current_semantic_governance_version": SEMANTIC_GOVERNANCE_VERSION,
        "semantic_hashes": semantic_hashes,
        "changed_sources": sorted(changed_sources),
        "affected_questions": sorted(affected),
        "affected_paper_fragments": sorted(stale_paper_fragments or predicted_fragments),
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
