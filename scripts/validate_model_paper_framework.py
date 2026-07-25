#!/usr/bin/env python3
"""Validate the current-state 模型论文框架.md and its project-state linkage."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any, Mapping

import yaml

REQUIRED_HEADINGS = (
    "# 模型论文框架",
    "## 当前有效口径",
    "## 论文整体框架",
    "## 各问模型与结果",
    "## 综合检验与跨问结论",
    "## 图表证据链",
    "## 待办与缺口",
    "## 同步检查",
)
SOLVED_STATUSES = {"solved", "validated", "written", "completed"}
FRAMEWORK_REQUIRED_PHASES = {
    "model_design",
    "solve_validate",
    "figure_evidence",
    "writing_docx",
    "writing_latex",
    "ai_cleanup",
    "latex_compile_quality",
    "review_delivery",
    "completed",
}


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def sha256_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def validate_framework_text(
    text: str,
    *,
    state: Mapping[str, Any] | None = None,
    strict: bool = False,
) -> list[str]:
    """Return framework violations without changing the file."""
    issues: list[str] = []
    for heading in REQUIRED_HEADINGS:
        count = text.count(heading)
        if count == 0:
            issues.append(f"missing required heading: {heading}")
        elif count > 1:
            issues.append(f"duplicate required heading: {heading}")

    if "只保留当前有效" not in text and "当前有效版本" not in text:
        issues.append("framework must state that only the current effective version is retained")

    if strict:
        unresolved = sorted({token for token in text.split() if token.startswith("__") and token.endswith("__")})
        if unresolved:
            issues.append(f"unresolved framework placeholders: {unresolved}")

    if not isinstance(state, Mapping):
        return issues

    framework = state.get("paper_framework", {}) or {}
    if framework.get("sync_status") != "current":
        issues.append("paper_framework.sync_status must be current")

    expected_hash = framework.get("sha256")
    if expected_hash and expected_hash.lower() != sha256_text(text):
        issues.append("paper_framework.sha256 does not match 模型论文框架.md")

    for name, subproblem in (state.get("subproblems", {}) or {}).items():
        if not isinstance(subproblem, Mapping):
            continue
        section = str(subproblem.get("framework_section", "")).strip()
        if not section:
            issues.append(f"{name}.framework_section is empty")
        elif section not in text:
            issues.append(f"{name}.framework_section is not present in 模型论文框架.md: {section}")

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
) -> list[str]:
    if not framework_path.is_file():
        return [f"framework file not found: {framework_path}"]
    state = load_yaml(state_path) if state_path and state_path.is_file() else None
    return validate_framework_text(
        framework_path.read_text(encoding="utf-8"),
        state=state,
        strict=strict,
    )


def framework_required_from_state(state: Mapping[str, Any]) -> bool:
    phase = str((state.get("project", {}) or {}).get("current_phase", ""))
    return phase in FRAMEWORK_REQUIRED_PHASES


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("framework", nargs="?", default="模型论文框架.md")
    parser.add_argument("--state", default="state/project_state.yaml")
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
