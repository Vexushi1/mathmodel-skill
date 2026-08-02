#!/usr/bin/env python3
"""Validate user-produced workbooks and advance state only after evidence passes."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

import openpyxl
import yaml

FALSE_FLAGS = (
    "allow_reduced_data", "allow_coarser_grid", "allow_shorter_horizon",
    "allow_fewer_repetitions", "allow_relaxed_tolerance",
    "allow_silent_solver_fallback",
)
TRUE_VALUES = {True, 1, "1", "true", "yes", "是", "通过", "满足"}


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def question_key(problem: str) -> str:
    order = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    suffix = problem.removeprefix("问题")
    return f"Q{order.index(suffix) + 1}" if suffix in order else problem


def as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "是", "通过", "满足"}:
        return True
    if text in {"false", "0", "no", "否", "未通过", "不满足"}:
        return False
    return None


def configuration_map(workbook: Path) -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []
    book = openpyxl.load_workbook(workbook, read_only=True, data_only=True)
    if "运行配置" not in book.sheetnames:
        return {}, ["缺少运行配置工作表"]
    sheet = book["运行配置"]
    rows = list(sheet.iter_rows(values_only=True))
    if not rows or tuple(rows[0][:2]) != ("项目", "值"):
        return {}, ["运行配置表头必须为项目|值"]
    mapping = {str(row[0]).strip(): row[1] for row in rows[1:] if row and row[0] not in (None, "")}
    required = {
        "execution_owner", "execution_profile", "stage", "problem_name", "code_sha256",
        "data_sha256", "solver", "solver_version", "tolerance", "iteration_or_time_limit",
        "actual_stop_reason", "random_seed", "repetitions_or_scenarios", "grid_or_time_range",
        "fallback_used", "platform",
    }
    missing = sorted(required - set(mapping))
    issues.extend(f"运行配置缺少项目: {item}" for item in missing)
    return mapping, issues


def quality_passed(workbook: Path) -> tuple[bool, list[str]]:
    book = openpyxl.load_workbook(workbook, read_only=True, data_only=True)
    if "主结果质量门" not in book.sheetnames:
        return False, ["缺少主结果质量门工作表"]
    rows = list(book["主结果质量门"].iter_rows(values_only=True))
    if not rows:
        return False, ["主结果质量门为空"]
    headers = [str(item) if item is not None else "" for item in rows[0]]
    if "是否通过" not in headers:
        return False, ["主结果质量门缺少是否通过列"]
    index = headers.index("是否通过")
    failures = [str(row[0]) for row in rows[1:] if row and as_bool(row[index] if len(row) > index else None) is not True]
    return not failures, [f"质量门未通过: {item}" for item in failures]


def analysis_passed(workbook: Path) -> tuple[bool, str, list[str]]:
    book = openpyxl.load_workbook(workbook, read_only=True, data_only=True)
    required = {"分析设计", "结论稳定性汇总"}
    missing = sorted(required - set(book.sheetnames))
    if missing:
        return False, "failed", [f"缺少工作表: {missing}"]
    rows = list(book["结论稳定性汇总"].iter_rows(values_only=True))
    if len(rows) < 2:
        return False, "failed", ["结论稳定性汇总无实质数据"]
    headers = [str(item) if item is not None else "" for item in rows[0]]
    if "是否保持" not in headers:
        return False, "failed", ["结论稳定性汇总缺少是否保持列"]
    index = headers.index("是否保持")
    unstable = [row for row in rows[1:] if row and as_bool(row[index] if len(row) > index else None) is not True]
    return (not unstable, "passed" if not unstable else "redo_required", ["存在核心结论未保持"] if unstable else [])


def validate_one(root: Path, workbook: Path, state: dict[str, Any], write: bool) -> list[str]:
    issues: list[str] = []
    config, config_issues = configuration_map(workbook)
    issues.extend(config_issues)
    stage = str(config.get("stage", ""))
    problem = str(config.get("problem_name", ""))
    key = question_key(problem)
    entry = (state.get("subproblems") or {}).get(key, {})
    if config.get("execution_owner") != "user":
        issues.append("execution_owner必须为user")
    if config.get("execution_profile") != "full_fidelity":
        issues.append("execution_profile必须为full_fidelity")
    if as_bool(config.get("fallback_used")) is not False:
        issues.append("fallback_used必须为false")
    for flag in FALSE_FLAGS:
        if flag in config and as_bool(config.get(flag)) is not False:
            issues.append(f"{flag}必须为false")
    expected_hash = entry.get("analysis_code_sha256") if stage == "analysis" else entry.get("primary_code_sha256")
    if not expected_hash:
        issues.append("项目状态缺少已交付代码哈希")
    elif str(config.get("code_sha256", "")).lower() != str(expected_hash).lower():
        issues.append("工作簿code_sha256与已交付代码不一致")
    if stage == "primary":
        passed, quality_issues = quality_passed(workbook)
        issues.extend(quality_issues)
        if write:
            entry["primary_execution_status"] = "accepted" if not issues and passed else "rejected"
            entry["result_quality_status"] = "passed" if not issues and passed else "failed"
            entry["solution_workbook"] = workbook.relative_to(root).as_posix()
            entry.setdefault("artifact_hashes", {})["solution_workbook"] = file_hash(workbook)
            if not issues and passed:
                entry.setdefault("validated_artifact_hashes", {})["solution_workbook"] = file_hash(workbook)
                entry["status"] = "solved"
    elif stage == "analysis":
        passed, result_status, analysis_issues = analysis_passed(workbook)
        issues.extend(analysis_issues)
        if write:
            entry["analysis_execution_status"] = "accepted" if not issues and passed else ("redo_required" if result_status == "redo_required" else "rejected")
            entry["result_analysis_status"] = result_status
            entry["result_analysis_workbook"] = workbook.relative_to(root).as_posix()
            entry.setdefault("artifact_hashes", {})["result_analysis_workbook"] = file_hash(workbook)
            if not issues and passed:
                entry.setdefault("validated_artifact_hashes", {})["result_analysis_workbook"] = file_hash(workbook)
                entry["status"] = "analyzed"
            elif result_status == "redo_required":
                entry["artifacts_stale"] = True
                entry["stale_layers"] = ["result_analysis_workbook", "matlab_script", "figure_bundle", "framework"]
                entry["result_summary_status"] = "stale"
                state.setdefault("project", {})["current_phase"] = "solve_validate"
    else:
        issues.append("运行配置stage必须为primary或analysis")
    return issues


def discover(root: Path) -> list[Path]:
    return sorted((root / "结果数据表").glob("问题*/问题*求解结果.xlsx")) + sorted((root / "结果数据表").glob("问题*/问题*结果深化分析.xlsx"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--workbook", type=Path)
    parser.add_argument("--scope", default="results")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    root = args.project_root.resolve()
    state_path = root / "state" / "project_state.yaml"
    if not state_path.is_file():
        raise SystemExit("缺少state/project_state.yaml")
    state = load_yaml(state_path)
    workbooks = [args.workbook if args.workbook.is_absolute() else root / args.workbook] if args.workbook else discover(root)
    all_issues: list[str] = []
    checked: list[str] = []
    for workbook in workbooks:
        issues = validate_one(root, workbook, state, args.write)
        all_issues.extend(f"{workbook.name}: {item}" for item in issues)
        checked.append(workbook.relative_to(root).as_posix())
    if args.write:
        state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
    report = {"status": "passed" if not all_issues else "failed", "checked_workbooks": checked, "issues": all_issues, "task_code_executed": False}
    (root / "user_execution_validation_report.yaml").write_text(yaml.safe_dump(report, allow_unicode=True, sort_keys=False), encoding="utf-8")
    if all_issues:
        print("\n".join(all_issues))
        return 1 if args.strict else 0
    print("user-produced workbooks accepted without executing task code")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
