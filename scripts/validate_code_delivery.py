#!/usr/bin/env python3
"""Validate a full-fidelity code handoff without importing or executing task code."""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "core" / "user_execution_contract.yaml"
FALSE_FLAGS = (
    "allow_reduced_data", "allow_coarser_grid", "allow_shorter_horizon",
    "allow_fewer_repetitions", "allow_relaxed_tolerance",
    "allow_silent_solver_fallback",
)
PLACEHOLDERS = ("TODO", "FIXME", "__QUESTION_NAME__", "NotImplementedError")


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def infer_stage(config: dict[str, Any]) -> str:
    stage = str(config.get("stage", "")).strip()
    if stage not in {"primary", "analysis"}:
        raise ValueError("stage必须为primary或analysis")
    return stage


def validate_config(project_root: Path, config_path: Path) -> tuple[list[str], dict[str, Any], Path]:
    issues: list[str] = []
    config = load_yaml(config_path)
    contract = load_yaml(CONTRACT)
    required = contract["code_delivery"]["required_config_fields"]
    for field in required:
        if field not in config or config[field] in (None, "", []):
            issues.append(f"完整运行配置缺少字段: {field}")
    try:
        stage = infer_stage(config)
    except ValueError as exc:
        issues.append(str(exc))
        stage = "primary"
    if config.get("execution_owner") != "user":
        issues.append("execution_owner必须为user")
    if config.get("execution_profile") != "full_fidelity":
        issues.append("execution_profile必须为full_fidelity")
    for flag in FALSE_FLAGS:
        if config.get(flag) is not False:
            issues.append(f"{flag}必须显式为false")
    code_path = project_root / str(config.get("code_path", ""))
    if not code_path.is_file():
        issues.append(f"代码文件不存在: {code_path}")
        return issues, config, code_path
    text = code_path.read_text(encoding="utf-8", errors="ignore")
    for marker in PLACEHOLDERS:
        if marker in text:
            issues.append(f"正式代码仍含占位标记: {marker}")
    if "if __name__ == \"__main__\":" not in text and "if __name__ == '__main__':" not in text:
        issues.append("正式代码缺少main入口")
    declared = str(config.get("code_sha256", "")).lower()
    actual = sha256(code_path)
    if declared != actual:
        issues.append(f"code_sha256不匹配: declared={declared}, actual={actual}")
    expected_suffix = "结果深化分析.py" if stage == "analysis" else "求解.py"
    if not code_path.name.endswith(expected_suffix):
        issues.append(f"{stage}阶段代码文件名应以{expected_suffix}结尾")
    instructions = config_path.with_name(
        config_path.name.replace("完整运行配置.yaml", "本地运行说明.md")
    )
    if not instructions.is_file():
        issues.append(f"缺少本地运行说明: {instructions.name}")
    return issues, config, code_path


def update_state(project_root: Path, config: dict[str, Any], code_path: Path) -> None:
    state_path = project_root / "state" / "project_state.yaml"
    if not state_path.is_file():
        return
    state = load_yaml(state_path)
    problem = str(config["problem_name"])
    order = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    suffix = problem.removeprefix("问题")
    key = f"Q{order.index(suffix) + 1}" if suffix in order else problem
    entry = state.setdefault("subproblems", {}).setdefault(key, {})
    relative = code_path.relative_to(project_root).as_posix()
    stage = infer_stage(config)
    if stage == "primary":
        entry["code"] = relative
        entry["primary_code_sha256"] = sha256(code_path)
        entry["primary_execution_status"] = "awaiting_user_execution"
        entry.setdefault("analysis_execution_status", "pending")
    else:
        if entry.get("primary_execution_status") != "accepted":
            raise ValueError("主工作簿未accepted，禁止交付最终结果深化分析代码")
        entry["result_analysis_code"] = relative
        entry["analysis_code_sha256"] = sha256(code_path)
        entry["analysis_execution_status"] = "awaiting_user_execution"
    execution = state.setdefault("execution", {})
    execution.update({
        "owner": "user",
        "profile": "full_fidelity",
        "assistant_task_execution_allowed": False,
        **{flag: False for flag in FALSE_FLAGS},
    })
    state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    root = args.project_root.resolve()
    configs = [args.config] if args.config else sorted(root.glob("问题*完整运行配置.yaml")) + sorted(root.glob("问题*结果深化完整运行配置.yaml"))
    issues: list[str] = []
    checked: list[str] = []
    for raw in configs:
        path = raw if raw.is_absolute() else root / raw
        item_issues, config, code_path = validate_config(root, path)
        issues.extend(f"{path.name}: {item}" for item in item_issues)
        checked.append(path.relative_to(root).as_posix())
        if args.write and not item_issues:
            update_state(root, config, code_path)
    report = {"status": "passed" if not issues else "failed", "checked_configs": checked, "issues": issues, "task_code_executed": False}
    (root / "code_delivery_report.yaml").write_text(yaml.safe_dump(report, allow_unicode=True, sort_keys=False), encoding="utf-8")
    if issues:
        print("\n".join(issues))
        return 1 if args.strict else 0
    print("full-fidelity code delivery validated without executing task code")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
