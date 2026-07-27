#!/usr/bin/env python3
"""Validate current-state 模型论文框架.md with mode-aware requirements."""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path
from typing import Any, Mapping

import yaml

COMPACT_HEADINGS = (
    "# 模型论文框架",
    "## 当前有效口径",
    "## 各问模型与结果",
    "## 图表证据链",
    "## 待办与缺口",
)
FULL_EXTRA_HEADINGS = (
    "## 论文整体框架",
    "### 命题与证明规划",
    "## 综合检验与跨问结论",
    "## 同步检查",
)
VALID_MODES = {"compact", "full"}
SOLVED_STATUSES = {"solved", "validated", "written", "completed"}
FRAMEWORK_REQUIRED_PHASES = {
    "model_design", "solve_validate", "figure_evidence", "writing_docx",
    "writing_latex", "ai_cleanup", "latex_compile_quality",
    "review_delivery", "completed",
}
PROPOSITION_LIMIT = 4
PROPOSITION_ID_PATTERN = re.compile(r"^P([1-4])$")
PROPOSITION_STATE_FIELDS = {
    "proposition_limit", "proposition_count", "proposition_status", "propositions",
}


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def sha256_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def infer_mode(text: str, state: Mapping[str, Any] | None, explicit: str | None) -> str:
    if explicit:
        mode = explicit
    elif isinstance(state, Mapping):
        mode = str((state.get("paper_framework", {}) or {}).get("mode", "")).strip()
    else:
        mode = ""
    if not mode:
        match = re.search(r"(?mi)^-\s*(?:框架模式|mode)\s*[:：]\s*`?(compact|full)`?\s*$", text)
        mode = match.group(1).lower() if match else "compact"
    if mode not in VALID_MODES:
        raise ValueError(f"unknown framework mode: {mode}")
    return mode


def required_headings(mode: str) -> tuple[str, ...]:
    return COMPACT_HEADINGS if mode == "compact" else (*COMPACT_HEADINGS, *FULL_EXTRA_HEADINGS)


def _extract_int(text: str, label: str) -> int | None:
    match = re.search(rf"{re.escape(label)}\s*[:：]\s*(\d+)", text)
    return int(match.group(1)) if match else None


def _proposition_section(text: str) -> str:
    heading = "### 命题与证明规划"
    start = text.find(heading)
    if start < 0:
        return ""
    tail = text[start + len(heading):]
    next_heading = re.search(r"\n(?:##|###)\s+", tail)
    return tail[:next_heading.start()] if next_heading else tail


def _proposition_rows(text: str) -> list[tuple[str, list[str]]]:
    rows: list[tuple[str, list[str]]] = []
    for line in _proposition_section(text).splitlines():
        match = re.match(r"^\|\s*(P\d+)\s*\|", line)
        if match:
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            rows.append((match.group(1), cells))
    return rows


def _validate_proposition_plan(text: str, *, strict: bool) -> tuple[list[str], int | None, set[str]]:
    issues: list[str] = []
    declared_limit = _extract_int(text, "全文命题上限")
    declared_count = _extract_int(text, "当前计划命题数")
    rows = _proposition_rows(text)
    row_ids = [item[0] for item in rows]
    unique_ids = set(row_ids)
    if declared_limit is None:
        issues.append("framework must declare 全文命题上限")
    elif declared_limit != PROPOSITION_LIMIT:
        issues.append(f"全文命题上限 must be {PROPOSITION_LIMIT}, got {declared_limit}")
    if declared_count is None:
        issues.append("framework must declare 当前计划命题数")
    elif not 0 <= declared_count <= PROPOSITION_LIMIT:
        issues.append(f"当前计划命题数 must be between 0 and {PROPOSITION_LIMIT}")
    invalid_ids = sorted({item for item in row_ids if not PROPOSITION_ID_PATTERN.fullmatch(item)})
    if invalid_ids:
        issues.append(f"proposition IDs must be P1--P4: {invalid_ids}")
    if len(row_ids) != len(unique_ids):
        issues.append("duplicate proposition IDs in 命题与证明规划")
    if declared_count is not None and declared_count != len(unique_ids):
        issues.append(
            f"当前计划命题数 ({declared_count}) does not match proposition table rows ({len(unique_ids)})"
        )
    for proposition_id, cells in rows:
        if len(cells) < 9:
            issues.append(f"{proposition_id} proposition row must contain all nine contract fields")
            continue
        if strict and cells[8].lower() == "current":
            missing = [index + 1 for index, value in enumerate(cells[:9]) if not value]
            if missing:
                issues.append(f"{proposition_id} current proposition has empty contract fields: {missing}")
            if cells[5] not in {"A", "B", "C"}:
                issues.append(f"{proposition_id} proof level must be A, B or C")
    return issues, declared_count, unique_ids


def validate_framework_text(
    text: str,
    *,
    state: Mapping[str, Any] | None = None,
    strict: bool = False,
    mode: str | None = None,
) -> list[str]:
    issues: list[str] = []
    try:
        resolved_mode = infer_mode(text, state, mode)
    except ValueError as exc:
        return [str(exc)]
    for heading in required_headings(resolved_mode):
        count = text.count(heading)
        if count == 0:
            issues.append(f"missing required heading for {resolved_mode}: {heading}")
        elif count > 1:
            issues.append(f"duplicate required heading: {heading}")
    for heading in set(COMPACT_HEADINGS + FULL_EXTRA_HEADINGS):
        if heading not in required_headings(resolved_mode) and text.count(heading) > 1:
            issues.append(f"duplicate optional heading: {heading}")
    if "只保留当前有效" not in text and "当前有效版本" not in text:
        issues.append("framework must state that only the current effective version is retained")

    proposition_ids: set[str] = set()
    declared_count: int | None = None
    if "### 命题与证明规划" in text:
        proposition_issues, declared_count, proposition_ids = _validate_proposition_plan(text, strict=strict)
        issues.extend(proposition_issues)
    elif resolved_mode == "full":
        issues.append("full framework requires proposition planning section")

    if strict:
        unresolved = sorted({token for token in text.split() if token.startswith("__") and token.endswith("__")})
        if unresolved:
            issues.append(f"unresolved framework placeholders: {unresolved}")
    if not isinstance(state, Mapping):
        return issues

    framework = state.get("paper_framework", {}) or {}
    state_mode = str(framework.get("mode", resolved_mode))
    if state_mode != resolved_mode:
        issues.append(f"paper_framework.mode ({state_mode}) does not match validated mode ({resolved_mode})")
    if framework.get("sync_status") != "current":
        issues.append("paper_framework.sync_status must be current")
    expected_hash = framework.get("sha256")
    if expected_hash and expected_hash.lower() != sha256_text(text):
        issues.append("paper_framework.sha256 does not match 模型论文框架.md")

    state_ids: set[str] = set()
    if PROPOSITION_STATE_FIELDS.intersection(framework):
        entries = framework.get("propositions", []) or []
        state_ids = {
            str(item.get("id", "")) for item in entries
            if isinstance(item, Mapping) and str(item.get("id", "")).strip()
        }
        if framework.get("proposition_limit") != PROPOSITION_LIMIT:
            issues.append(f"paper_framework.proposition_limit must be {PROPOSITION_LIMIT}")
        state_count = framework.get("proposition_count")
        if declared_count is not None and state_count != declared_count:
            issues.append("paper_framework.proposition_count does not match 当前计划命题数")
        if isinstance(state_count, int) and state_count != len(entries):
            issues.append("paper_framework.proposition_count does not match propositions array length")
        if proposition_ids and state_ids != proposition_ids:
            issues.append("project-state proposition IDs do not match 模型论文框架.md")
        if not proposition_ids and state_ids and resolved_mode == "full":
            issues.append("project-state propositions exist but full framework has no proposition rows")

    for name, subproblem in (state.get("subproblems", {}) or {}).items():
        if not isinstance(subproblem, Mapping):
            continue
        section = str(subproblem.get("framework_section", "")).strip()
        if not section:
            issues.append(f"{name}.framework_section is empty")
        elif section not in text:
            issues.append(f"{name}.framework_section is not present in 模型论文框架.md: {section}")
        refs = set(subproblem.get("proposition_refs", []) or [])
        unknown_refs = sorted(refs - state_ids)
        if refs and unknown_refs:
            issues.append(f"{name}.proposition_refs contain unknown IDs: {unknown_refs}")
        status = str(subproblem.get("status", ""))
        summary_status = str(subproblem.get("result_summary_status", ""))
        anchor = str(subproblem.get("result_summary_anchor", "")).strip()
        if status in SOLVED_STATUSES:
            if summary_status != "current":
                issues.append(f"{name}.result_summary_status must be current when status is {status}")
            if not anchor:
                issues.append(f"{name}.result_summary_anchor is required when status is {status}")
            elif anchor not in text:
                issues.append(f"{name}.result_summary_anchor is not present in 模型论文框架.md: {anchor}")
        if subproblem.get("artifacts_stale") is True and summary_status == "current":
            issues.append(f"{name}.result_summary_status cannot be current while artifacts_stale is true")
    return issues


def validate_framework_file(
    framework_path: Path,
    *,
    state_path: Path | None = None,
    strict: bool = False,
    mode: str | None = None,
) -> list[str]:
    if not framework_path.is_file():
        return [f"framework file not found: {framework_path}"]
    state = load_yaml(state_path) if state_path and state_path.is_file() else None
    return validate_framework_text(
        framework_path.read_text(encoding="utf-8"), state=state, strict=strict, mode=mode
    )


def framework_required_from_state(state: Mapping[str, Any]) -> bool:
    phase = str((state.get("project", {}) or {}).get("current_phase", ""))
    return phase in FRAMEWORK_REQUIRED_PHASES


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("framework", nargs="?", default="模型论文框架.md")
    parser.add_argument("--state", default="state/project_state.yaml")
    parser.add_argument("--mode", choices=sorted(VALID_MODES))
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    framework_path = Path(args.framework).resolve()
    state_path = Path(args.state).resolve()
    state = load_yaml(state_path) if state_path.is_file() else {}
    if state and not framework_path.is_file() and not framework_required_from_state(state):
        print("HSK model paper framework: NOT REQUIRED YET")
        return 0
    issues = validate_framework_file(
        framework_path,
        state_path=state_path if state_path.is_file() else None,
        strict=args.strict,
        mode=args.mode,
    )
    if issues:
        print("HSK model paper framework: ISSUES FOUND")
        for issue in issues:
            print("-", issue)
        return 1
    print("HSK model paper framework: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
