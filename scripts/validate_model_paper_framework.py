#!/usr/bin/env python3
"""Validate current-state 模型论文框架.md with mode-aware requirements.

The validator checks deterministic project-memory structure. It does not infer mathematical
correctness, citation semantics, terminology equivalence, or whether a writing choice is good.
"""
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
    "## 同步检查",
)
V08_FULL_HEADINGS = (
    "### Terminology Registry",
    "### Numeric Profile",
    "### Title Claim Gate",
    "### 正文局部状态映射",
)
CROSS_QUESTION_HEADING_ALIASES = (
    "## 综合检验与跨问结论",
    "## 综合检验与跨问判断",
)
VALID_MODES = {"compact", "full"}
SOLVED_STATUSES = {"solved", "analyzed", "validated", "written", "completed"}
FRAMEWORK_REQUIRED_PHASES = {
    "model_design", "solve_validate", "result_analysis", "figure_evidence", "writing_docx",
    "writing_latex", "ai_cleanup", "latex_compile_quality", "review_delivery", "completed",
}
PROPOSITION_DEFAULT_BUDGET = 4
PROPOSITION_ID_PATTERN = re.compile(r"^P[1-9][0-9]*$")
TERM_ID_PATTERN = re.compile(r"^T[1-9][0-9]*$")
METRIC_ID_PATTERN = re.compile(r"^N[1-9][0-9]*$")
TITLE_CLAIM_ID_PATTERN = re.compile(r"^TC[1-9][0-9]*$")
PAPER_FRAGMENT_ID_PATTERN = re.compile(r"^PF[1-9][0-9]*$")
PROPOSITION_STATE_FIELDS = {
    "proposition_limit", "proposition_default_budget", "proposition_count",
    "proposition_status", "proposition_budget_status", "propositions",
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


def _framework_version(text: str) -> str:
    match = re.search(r"(?mi)^-\s*框架版本\s*[:：]\s*`?([^`\n]+)`?\s*$", text)
    return match.group(1).strip() if match else ""


def required_headings(mode: str) -> tuple[str, ...]:
    return COMPACT_HEADINGS if mode == "compact" else (*COMPACT_HEADINGS, *FULL_EXTRA_HEADINGS)


def _extract_int(text: str, label: str) -> int | None:
    match = re.search(rf"{re.escape(label)}\s*[:：]\s*`?(\d+)`?", text)
    return int(match.group(1)) if match else None


def _extract_scalar(text: str, label: str) -> str | None:
    match = re.search(rf"(?mi)^-?\s*{re.escape(label)}\s*[:：]\s*`?([^`\n]+?)`?\s*$", text)
    return match.group(1).strip() if match else None


def _section_after_heading(text: str, heading: str) -> str:
    start = text.find(heading)
    if start < 0:
        return ""
    tail = text[start + len(heading):]
    current_level = len(heading) - len(heading.lstrip("#"))
    match = re.search(r"(?m)^#{1,%d}\s+" % current_level, tail)
    return tail[:match.start()] if match else tail


def _table_rows(text: str, heading: str, id_pattern: re.Pattern[str]) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in _section_after_heading(text, heading).splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and id_pattern.fullmatch(cells[0]):
            rows.append(cells)
    return rows


def _split_aliases(value: str) -> set[str]:
    if not value.strip():
        return set()
    return {item.strip() for item in re.split(r"[/、,，;；]", value) if item.strip() and item.strip() not in {"无", "-", "—"}}


def _validate_v08_project_memory(text: str, *, strict: bool) -> list[str]:
    issues: list[str] = []
    for heading in V08_FULL_HEADINGS:
        if heading not in text:
            issues.append(f"v0.8 full framework missing semantic-governance heading: {heading}")

    term_rows = _table_rows(text, "### Terminology Registry", TERM_ID_PATTERN)
    term_ids = [row[0] for row in term_rows]
    if len(term_ids) != len(set(term_ids)):
        issues.append("Terminology Registry contains duplicate Term IDs")
    alias_owner: dict[str, str] = {}
    for row in term_rows:
        if len(row) < 9:
            issues.append(f"{row[0]} terminology row must contain all nine project fields")
            continue
        canonical = row[1]
        if strict and (not canonical or not row[2]):
            issues.append(f"{row[0]} terminology row requires canonical term and definition in strict mode")
        for alias in _split_aliases(row[4]) | _split_aliases(row[5]):
            owner = alias_owner.get(alias)
            if owner and owner != canonical:
                issues.append(f"terminology alias {alias!r} maps to multiple canonical terms: {owner!r}, {canonical!r}")
            alias_owner[alias] = canonical

    metric_rows = _table_rows(text, "### Numeric Profile", METRIC_ID_PATTERN)
    metric_ids = [row[0] for row in metric_rows]
    if len(metric_ids) != len(set(metric_ids)):
        issues.append("Numeric Profile contains duplicate Metric IDs")
    for row in metric_rows:
        if len(row) < 10:
            issues.append(f"{row[0]} numeric row must contain all ten project fields")
            continue
        if strict and (not row[1] or not row[5] or not row[9]):
            issues.append(f"{row[0]} numeric row requires metric, required precision and precision basis in strict mode")

    title_rows = _table_rows(text, "### Title Claim Gate", TITLE_CLAIM_ID_PATTERN)
    title_ids = [row[0] for row in title_rows]
    if len(title_ids) != len(set(title_ids)):
        issues.append("Title Claim Gate contains duplicate Claim IDs")
    for row in title_rows:
        if len(row) < 9:
            issues.append(f"{row[0]} title claim row must contain all nine project fields")
            continue
        if strict and row[8] == "current" and any(not value for value in row[1:8]):
            issues.append(f"{row[0]} current title claim has empty closure fields")

    fragment_rows = _table_rows(text, "### 正文局部状态映射", PAPER_FRAGMENT_ID_PATTERN)
    fragment_ids = [row[0] for row in fragment_rows]
    if len(fragment_ids) != len(set(fragment_ids)):
        issues.append("正文局部状态映射 contains duplicate Fragment IDs")
    for row in fragment_rows:
        if len(row) < 7:
            issues.append(f"{row[0]} paper fragment row must contain all seven project fields")
            continue
        if row[5] == "stale" and strict and not row[6]:
            issues.append(f"{row[0]} stale paper fragment requires stale reason / repair action")
    return issues


def _proposition_section(text: str) -> str:
    return _section_after_heading(text, "### 命题与证明规划")


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
    declared_count = _extract_int(text, "当前计划命题数")
    rows = _proposition_rows(text)
    row_ids = [item[0] for item in rows]
    unique_ids = set(row_ids)

    if declared_count is None:
        issues.append("framework must declare 当前计划命题数")
    elif declared_count < 0:
        issues.append("当前计划命题数 must be >= 0")

    invalid_ids = sorted({item for item in row_ids if not PROPOSITION_ID_PATTERN.fullmatch(item)})
    if invalid_ids:
        issues.append(f"proposition IDs must match P1, P2, ...: {invalid_ids}")
    if len(row_ids) != len(unique_ids):
        issues.append("duplicate proposition IDs in 命题与证明规划")
    if declared_count is not None and declared_count != len(unique_ids):
        issues.append(
            f"当前计划命题数 ({declared_count}) does not match proposition table rows ({len(unique_ids)})"
        )

    if declared_count is not None and declared_count > PROPOSITION_DEFAULT_BUDGET:
        budget_status = _extract_scalar(text, "超预算状态") or ""
        reason = _extract_scalar(text, "超预算说明（若适用）") or _extract_scalar(text, "超预算说明") or ""
        if budget_status not in {"justified", "已说明", "已论证"}:
            issues.append(
                f"proposition count {declared_count} exceeds default budget {PROPOSITION_DEFAULT_BUDGET}; "
                "set 超预算状态=justified after necessity review"
            )
        if strict and not reason:
            issues.append("over-budget proposition plan requires 超预算说明 in strict mode")

    for proposition_id, cells in rows:
        if len(cells) < 9:
            issues.append(f"{proposition_id} proposition row must contain all nine project fields")
            continue
        if strict and cells[8].lower() == "current":
            missing = [index + 1 for index, value in enumerate(cells[:9]) if not value]
            if missing:
                issues.append(f"{proposition_id} current proposition has empty project fields: {missing}")
            if cells[5] not in {"A", "B", "C"}:
                issues.append(f"{proposition_id} proof level must be A, B or C")
    return issues, declared_count, unique_ids


def _framework_fragment_statuses(text: str) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for row in _table_rows(text, "### 正文局部状态映射", PAPER_FRAGMENT_ID_PATTERN):
        if len(row) >= 6:
            statuses[row[0]] = row[5]
    return statuses


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

    version = _framework_version(text)
    if resolved_mode == "full" and version.startswith("v0.8"):
        issues.extend(_validate_v08_project_memory(text, strict=strict))

    cross_heading_count = sum(text.count(heading) for heading in CROSS_QUESTION_HEADING_ALIASES)
    if resolved_mode == "full":
        if cross_heading_count == 0:
            issues.append(
                "missing required full-framework cross-question heading: "
                + " or ".join(CROSS_QUESTION_HEADING_ALIASES)
            )
        elif cross_heading_count > 1:
            issues.append("full framework must contain exactly one cross-question synthesis heading")
    elif cross_heading_count > 1:
        issues.append("duplicate optional cross-question synthesis heading")

    if "只保留" not in text or ("当前有效" not in text and "current" not in text):
        issues.append("framework must state that only the current effective project state is retained")

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
        state_count = framework.get("proposition_count")
        if declared_count is not None and state_count is not None and state_count != declared_count:
            issues.append("paper_framework.proposition_count does not match 当前计划命题数")
        if isinstance(state_count, int) and state_count != len(entries):
            issues.append("paper_framework.proposition_count does not match propositions array length")
        unknown_state_ids = sorted(item for item in state_ids if not PROPOSITION_ID_PATTERN.fullmatch(item))
        if unknown_state_ids:
            issues.append(f"project-state proposition IDs must match P1, P2, ...: {unknown_state_ids}")
        if proposition_ids and state_ids != proposition_ids:
            issues.append("project-state proposition IDs do not match 模型论文框架.md")
        if not proposition_ids and state_ids and resolved_mode == "full":
            issues.append("project-state propositions exist but full framework has no proposition rows")

    state_fragments = framework.get("paper_fragments", []) or []
    if state_fragments:
        text_statuses = _framework_fragment_statuses(text)
        state_statuses = {
            str(item.get("id", "")): str(item.get("status", ""))
            for item in state_fragments if isinstance(item, Mapping) and item.get("id")
        }
        if set(text_statuses) != set(state_statuses):
            issues.append("project-state paper fragment IDs do not match 正文局部状态映射")
        else:
            mismatched = sorted(key for key in state_statuses if text_statuses.get(key) != state_statuses[key])
            if mismatched:
                issues.append(f"paper fragment statuses differ between project-state and framework: {mismatched}")

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
