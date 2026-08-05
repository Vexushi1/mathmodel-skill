#!/usr/bin/env python3
"""静态校验每问唯一Python脚本，不运行赛题代码，也不生成额外报告文件。"""
from __future__ import annotations

import argparse
import ast
import hashlib
from pathlib import Path
from typing import Any

import yaml

FALSE_FLAGS = (
    "allow_reduced_data", "allow_coarser_grid", "allow_shorter_horizon",
    "allow_fewer_repetitions", "allow_relaxed_tolerance",
    "allow_silent_solver_fallback",
)
PLACEHOLDERS = ("TODO", "FIXME", "__QUESTION_NAME__", "NotImplementedError")
CONFIG_NAMES = {"FULL_FIDELITY_CONFIG", "FULL_RUN_CONFIG", "RUN_CONFIG"}
REQUIRED_FIELDS = {
    "execution_owner", "execution_profile", "stage", "problem_name", "data_paths",
    "data_sha256", "solver", "solver_version", "random_seed", "tolerance",
    "iteration_or_time_limit", "expected_workbook", *FALSE_FLAGS,
}


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_sha256(value: Any) -> bool:
    text = str(value).strip().lower()
    return len(text) == 64 and all(character in "0123456789abcdef" for character in text)


def embedded_config(text: str) -> dict[str, Any]:
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id in CONFIG_NAMES for target in targets):
                value = ast.literal_eval(node.value)
                if not isinstance(value, dict):
                    raise ValueError("FULL_FIDELITY_CONFIG必须为字典常量")
                return value
    raise ValueError("缺少FULL_FIDELITY_CONFIG字典常量")


def problem_from_path(script: Path) -> str:
    folder = script.parent.name
    if not folder.endswith("求解"):
        raise ValueError("Python脚本必须位于问题X求解目录")
    problem = folder.removesuffix("求解")
    if script.name != f"{problem}求解.py":
        raise ValueError(f"脚本名必须为{problem}求解.py")
    return problem


def validate_script(project_root: Path, script: Path, expected_stage: str | None = None) -> tuple[list[str], dict[str, Any]]:
    issues: list[str] = []
    try:
        problem = problem_from_path(script)
    except ValueError as exc:
        return [str(exc)], {}
    text = script.read_text(encoding="utf-8", errors="strict")
    for marker in PLACEHOLDERS:
        if marker in text:
            issues.append(f"正式代码仍含占位标记: {marker}")
    if 'if __name__ == "__main__":' not in text and "if __name__ == '__main__':" not in text:
        issues.append("正式代码缺少main入口")
    try:
        config = embedded_config(text)
    except (SyntaxError, ValueError) as exc:
        issues.append(str(exc))
        config = {}
    for field in sorted(REQUIRED_FIELDS):
        if field not in config or config[field] in (None, "", []):
            issues.append(f"嵌入运行配置缺少字段: {field}")
    stage = str(config.get("stage", ""))
    if stage not in {"primary", "analysis"}:
        issues.append("stage必须为primary或analysis")
    if expected_stage and stage != expected_stage:
        issues.append(f"stage应为{expected_stage}")
    if config.get("problem_name") != problem:
        issues.append("problem_name与目录名不一致")
    if config.get("execution_owner") != "user":
        issues.append("execution_owner必须为user")
    if config.get("execution_profile") != "full_fidelity":
        issues.append("execution_profile必须为full_fidelity")
    for flag in FALSE_FLAGS:
        if config.get(flag) is not False:
            issues.append(f"{flag}必须显式为false")
    if not is_sha256(config.get("data_sha256")):
        issues.append("data_sha256必须是64位十六进制SHA-256")
    expected = f"{problem}求解结果.xlsx" if stage == "primary" else f"{problem}结果深化分析.xlsx"
    if Path(str(config.get("expected_workbook", ""))).name != expected:
        issues.append(f"expected_workbook必须指向同目录{expected}")
    return issues, config


def update_state(project_root: Path, config: dict[str, Any], script: Path) -> None:
    state_path = project_root / "state" / "project_state.yaml"
    if not state_path.is_file():
        return
    state = load_yaml(state_path)
    problem = str(config["problem_name"])
    order = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    suffix = problem.removeprefix("问题")
    key = f"Q{order.index(suffix) + 1}" if suffix in order else problem
    entry = state.setdefault("subproblems", {}).setdefault(key, {})
    relative = script.relative_to(project_root).as_posix()
    stage = str(config["stage"])
    entry["data_hash"] = str(config["data_sha256"]).lower()
    entry["code"] = relative
    if stage == "primary":
        entry["primary_code_sha256"] = sha256(script)
        entry["primary_execution_status"] = "awaiting_user_execution"
        entry.setdefault("analysis_execution_status", "pending")
    else:
        if entry.get("primary_execution_status") != "accepted":
            raise ValueError("主工作簿未accepted，禁止写入最终结果深化分析实现")
        entry["analysis_code_sha256"] = sha256(script)
        entry["analysis_execution_status"] = "awaiting_user_execution"
    state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")


def discover_scripts(root: Path) -> list[Path]:
    return sorted(root.glob("问题*求解/问题*求解.py"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--script", type=Path)
    parser.add_argument("--stage", choices=("primary", "analysis"))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    root = args.project_root.resolve()
    scripts = [args.script if args.script and args.script.is_absolute() else root / args.script] if args.script else discover_scripts(root)
    issues: list[str] = []
    checked: list[str] = []
    for script in scripts:
        item_issues, config = validate_script(root, script, args.stage)
        issues.extend(f"{script.name}: {item}" for item in item_issues)
        checked.append(script.relative_to(root).as_posix())
        if args.write and not item_issues:
            try:
                update_state(root, config, script)
            except ValueError as exc:
                issues.append(f"{script.name}: {exc}")
    report = {
        "status": "passed" if not issues else "failed",
        "checked_scripts": checked,
        "issues": issues,
        "task_code_executed": False,
        "report_persisted": False,
    }
    print(yaml.safe_dump(report, allow_unicode=True, sort_keys=False).rstrip())
    return 1 if issues and args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
