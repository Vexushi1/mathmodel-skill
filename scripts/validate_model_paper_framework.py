#!/usr/bin/env python3
"""Validate current-state 模型论文框架.md with mode-aware requirements.

The validator checks deterministic project-memory structure. It does not infer mathematical
correctness, citation semantics, terminology equivalence, algorithm correctness, or whether a
displayed precision is scientifically correct.
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
V08_HEADINGS = (
    "### Terminology Registry",
    "### Numeric Profile",
)
V08_FULL_HEADINGS = (
    "#### Title Claim Gate",
    "### Paper Fragment Dependency Map",
)
CROSS_QUESTION_HEADING_ALIASES = (
    "## 综合检验与跨问结论",
    "## 综合检验与跨问判断",
)
VALID_MODES = {"compact", "full"}
SOLVED_STATUSES = {"solved", "analyzed", "validated", "written", "completed"}
FRAMEWORK_REQUIRED_PHASES = {
    "model_design", "solve_validate", "figure_evidence", "writing_docx",
    "writing_latex", "ai_cleanup", "latex_compile_quality",
    "review_delivery", "completed",
}
PROPOSITION_DEFAULT_BUDGET = 4
PROPOSITION_ID_PATTERN = re.compile(r"^P[1-9][0-9]*$")
PROPOSITION_STATE_FIELDS = {
    "proposition_limit", "proposition_default_budget", "proposition_count",
    "proposition_status", "proposition_budget_status", "propositions",
}
TERM_ID_PATTERN = re.compile(r"^T[1-9][0-9]*$")
NUMERIC_ID_PATTERN = re.compile(r"^N[1-9][0-9]*$")
TITLE_CLAIM_ID_PATTERN = re.compile(r"^TC[1-9][0-9]*$")
PAPER_FRAGMENT_ID_PATTERN = re.compile(r"^paper\.[A-Za-z0-9_.-]+$")
ALGORITHM_ID_PATTERN = re.compile(r"^A[1-9][0-9]*$")
ALGORITHM_PRESENTATION_MODES = {"not_needed", "stepwise", "pseudocode"}
ALGORITHM_TRACE_MODES = {"stepwise", "pseudocode"}
ALGORITHM_TRACE_STATUSES = {"current", "stale"}
QUESTION_HEADING_RE = re.compile(r"^###\s+(Q\d+)[:：].*$", re.MULTILINE)


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


def infer_framework_version(text: str, state: Mapping[str, Any] | None) -> str:
    if isinstance(state, Mapping):
        value = str((state.get("paper_framework", {}) or {}).get("version", "")).strip()
        if value:
            return value
    match = re.search(r"(?mi)^-\s*框架版本\s*[:：]\s*`?([^`\n]+)`?\s*$", text)
    return match.group(1).strip() if match else ""


def _uses_fragment_stale(version: str, state: Mapping[str, Any] | None) -> bool:
    if version.startswith("v0.8"):
        return True
    if isinstance(state, Mapping):
        return "paper_fragments" in (state.get("paper_framework", {}) or {})
    return False


def required_headings(mode: str) -> tuple[str, ...]:
    return COMPACT_HEADINGS if mode == "compact" else (*COMPACT_HEADINGS, *FULL_EXTRA_HEADINGS)


def _extract_int(text: str, label: str) -> int | None:
    match = re.search(rf"{re.escape(label)}\s*[:：]\s*`?(\d+)`?", text)
    return int(match.group(1)) if match else None


def _extract_scalar(text: str, label: str) -> str | None:
    match = re.search(rf"(?mi)^-?\s*{re.escape(label)}\s*[:：]\s*`?([^`\n]+?)`?\s*$", text)
    return match.group(1).strip() if match else None


def _section_between(text: str, heading: str) -> str:
    start = text.find(heading)
    if start < 0:
        return ""
    tail = text[start + len(heading):]
    next_heading = re.search(r"\n#{1,4}\s+", tail)
    return tail[:next_heading.start()] if next_heading else tail


def _question_sections(text: str) -> dict[str, str]:
    matches = list(QUESTION_HEADING_RE.finditer(text))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[match.group(1)] = text[match.start():end]
    return sections


def _proposition_section(text: str) -> str:
    return _section_between(text, "### 命题与证明规划")


def _proposition_rows(text: str) -> list[tuple[str, list[str]]]:
    rows: list[tuple[str, list[str]]] = []
    for line in _proposition_section(text).splitlines():
        match = re.match(r"^\|\s*(P\d+)\s*\|", line)
        if match:
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            rows.append((match.group(1), cells))
    return rows


def _algorithm_rows(text: str) -> list[tuple[str, list[str]]]:
    rows: list[tuple[str, list[str]]] = []
    for line in _section_between(text, "### Algorithm Trace").splitlines():
        match = re.match(r"^\|\s*(A\d+)\s*\|", line)
        if not match:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(not value for value in cells[1:]):
            continue
        rows.append((match.group(1), cells))
    return rows


def _table_ids(section: str, pattern: re.Pattern[str]) -> list[str]:
    ids: list[str] = []
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        first = line.strip().strip("|").split("|", 1)[0].strip()
        if pattern.fullmatch(first):
            ids.append(first)
    return ids


def _validate_unique_ids(name: str, ids: list[str]) -> list[str]:
    return [f"duplicate {name} IDs: {sorted({item for item in ids if ids.count(item) > 1})}"] if len(ids) != len(set(ids)) else []


def _validate_v08_semantic_tables(text: str, *, mode: str, strict: bool) -> tuple[list[str], dict[str, set[str]]]:
    issues: list[str] = []
    sections = {
        "terminology": _section_between(text, "### Terminology Registry"),
        "numeric": _section_between(text, "### Numeric Profile"),
        "title": _section_between(text, "#### Title Claim Gate"),
        "fragments": _section_between(text, "### Paper Fragment Dependency Map"),
    }
    ids = {
        "terminology": set(_table_ids(sections["terminology"], TERM_ID_PATTERN)),
        "numeric": set(_table_ids(sections["numeric"], NUMERIC_ID_PATTERN)),
        "title": set(_table_ids(sections["title"], TITLE_CLAIM_ID_PATTERN)),
        "fragments": set(_table_ids(sections["fragments"], PAPER_FRAGMENT_ID_PATTERN)),
    }
    for name, section, pattern in (
        ("Terminology", sections["terminology"], TERM_ID_PATTERN),
        ("Numeric", sections["numeric"], NUMERIC_ID_PATTERN),
        ("Title Claim", sections["title"], TITLE_CLAIM_ID_PATTERN),
        ("Paper Fragment", sections["fragments"], PAPER_FRAGMENT_ID_PATTERN),
    ):
        issues.extend(_validate_unique_ids(name, _table_ids(section, pattern)))

    if strict:
        if "核心答案是否属于高精度评分项" not in text:
            issues.append("v0.8 framework must record whether core answers are high-precision scoring items")
        if mode == "full" and "Title Claim Gate" in text and "选定题目：" not in text:
            issues.append("full v0.8 framework must record the selected title before Title Claim Gate")
    return issues, ids


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


def _validate_algorithm_trace(
    text: str,
    *,
    state: Mapping[str, Any] | None,
) -> list[str]:
    issues: list[str] = []
    rows = _algorithm_rows(text)
    row_ids = [algorithm_id for algorithm_id, _ in rows]
    if len(row_ids) != len(set(row_ids)):
        issues.append("duplicate Algorithm Trace IDs")

    by_id: dict[str, list[str]] = {}
    question_sections = _question_sections(text)
    state_subproblems = (state.get("subproblems", {}) or {}) if isinstance(state, Mapping) else {}

    for algorithm_id, cells in rows:
        if not ALGORITHM_ID_PATTERN.fullmatch(algorithm_id):
            issues.append(f"Algorithm Trace ID must match A1, A2, ...: {algorithm_id}")
            continue
        if len(cells) < 12:
            issues.append(f"{algorithm_id} Algorithm Trace row must contain all twelve project fields")
            continue
        by_id[algorithm_id] = cells
        required_indexes = {
            1: "question",
            2: "role",
            3: "inputs/state",
            4: "core operations",
            7: "termination",
            8: "outputs",
            10: "presentation mode",
            11: "status",
        }
        missing = [label for index, label in required_indexes.items() if not cells[index]]
        if missing:
            issues.append(f"{algorithm_id} Algorithm Trace missing required fields: {missing}")
        if cells[10] and cells[10] not in ALGORITHM_TRACE_MODES:
            issues.append(f"{algorithm_id} Algorithm Trace mode must be stepwise or pseudocode")
        if cells[11] and cells[11] not in ALGORITHM_TRACE_STATUSES:
            issues.append(f"{algorithm_id} Algorithm Trace status must be current or stale")
        question = cells[1]
        if question and question not in question_sections:
            issues.append(f"{algorithm_id} references unknown question: {question}")
        subproblem = state_subproblems.get(question, {}) if isinstance(state_subproblems, Mapping) else {}
        status = str(subproblem.get("status", "")) if isinstance(subproblem, Mapping) else ""
        if cells[11] == "current" and status in SOLVED_STATUSES and not cells[9]:
            issues.append(f"{algorithm_id} current solved Algorithm Trace requires a Python code anchor")

    for question, section in question_sections.items():
        presentation = _extract_scalar(section, "算法流程呈现")
        if presentation is None:
            continue
        linked_algorithm = _extract_scalar(section, "关联 Algorithm ID") or ""
        if presentation not in ALGORITHM_PRESENTATION_MODES:
            issues.append(
                f"{question}.算法流程呈现 must resolve to one of not_needed/stepwise/pseudocode, got: {presentation}"
            )
            continue
        if presentation == "not_needed":
            if linked_algorithm:
                issues.append(f"{question} is not_needed but still links Algorithm ID {linked_algorithm}")
            continue
        if not linked_algorithm:
            issues.append(f"{question} uses {presentation} but has no 关联 Algorithm ID")
            continue
        if not ALGORITHM_ID_PATTERN.fullmatch(linked_algorithm):
            issues.append(f"{question}.关联 Algorithm ID must match A1, A2, ...: {linked_algorithm}")
            continue
        trace = by_id.get(linked_algorithm)
        if trace is None:
            issues.append(f"{question} links missing Algorithm Trace: {linked_algorithm}")
            continue
        if len(trace) < 12:
            continue
        if trace[1] != question:
            issues.append(f"{question} links {linked_algorithm}, but trace question is {trace[1] or 'empty'}")
        if trace[10] != presentation:
            issues.append(
                f"{question} presentation mode {presentation} does not match {linked_algorithm} mode {trace[10] or 'empty'}"
            )
        if trace[11] != "current":
            issues.append(f"{question} links non-current Algorithm Trace {linked_algorithm}: {trace[11] or 'empty'}")
    return issues


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
    framework_version = infer_framework_version(text, state)
    fragment_mode = _uses_fragment_stale(framework_version, state)

    headings = list(required_headings(resolved_mode))
    if framework_version.startswith("v0.8"):
        headings.extend(V08_HEADINGS)
        if resolved_mode == "full":
            headings.extend(V08_FULL_HEADINGS)
    for heading in headings:
        count = text.count(heading)
        if count == 0:
            issues.append(f"missing required heading for {resolved_mode}: {heading}")
        elif count > 1:
            issues.append(f"duplicate required heading: {heading}")

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

    semantic_ids: dict[str, set[str]] = {"terminology": set(), "numeric": set(), "title": set(), "fragments": set()}
    if framework_version.startswith("v0.8"):
        semantic_issues, semantic_ids = _validate_v08_semantic_tables(text, mode=resolved_mode, strict=strict)
        issues.extend(semantic_issues)

    proposition_ids: set[str] = set()
    declared_count: int | None = None
    if "### 命题与证明规划" in text:
        proposition_issues, declared_count, proposition_ids = _validate_proposition_plan(text, strict=strict)
        issues.extend(proposition_issues)
    elif resolved_mode == "full":
        issues.append("full framework requires proposition planning section")

    issues.extend(_validate_algorithm_trace(text, state=state))

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
    if fragment_mode and framework.get("sync_status") != "current":
        issues.append("paper_framework.sync_status must be current for v0.8+; local stale is tracked by paper_fragments")
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

    if framework_version.startswith("v0.8"):
        state_map = {
            "terminology": {str(item.get("id", "")) for item in framework.get("terminology_registry", []) or [] if isinstance(item, Mapping)},
            "numeric": {str(item.get("id", "")) for item in framework.get("numeric_profile", []) or [] if isinstance(item, Mapping)},
            "title": {str(item.get("id", "")) for item in framework.get("title_claims", []) or [] if isinstance(item, Mapping)},
            "fragments": {str(item.get("id", "")) for item in framework.get("paper_fragments", []) or [] if isinstance(item, Mapping)},
        }
        for name, ids in state_map.items():
            ids.discard("")
            if semantic_ids[name] and ids != semantic_ids[name]:
                issues.append(f"project-state {name} IDs do not match 模型论文框架.md")

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
