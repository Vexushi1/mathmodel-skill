#!/usr/bin/env python3
"""Static delivery and engineering-quality validation for stage-specific task Python scripts."""
from __future__ import annotations

import argparse
import ast
import hashlib
from pathlib import Path
from typing import Any

import yaml

SKILL_ROOT = Path(__file__).resolve().parents[1]
QUALITY_CONTRACT = SKILL_ROOT / "core" / "code_quality_contract.yaml"
FALSE_FLAGS = (
    "allow_reduced_data", "allow_coarser_grid", "allow_shorter_horizon",
    "allow_fewer_repetitions", "allow_relaxed_tolerance", "allow_silent_solver_fallback",
)
PLACEHOLDERS = ("TODO", "FIXME", "__QUESTION_NAME__", "NotImplementedError")
CONFIG_NAMES = {"FULL_FIDELITY_CONFIG", "FULL_RUN_CONFIG", "RUN_CONFIG"}
REQUIRED_FIELDS = {
    "execution_owner", "execution_profile", "stage", "problem_name", "data_paths",
    "data_sha256", "solver", "solver_version", "random_seed", "tolerance",
    "iteration_or_time_limit", "expected_workbook", *FALSE_FLAGS,
}
ANALYSIS_STALE_LAYERS = {
    "result_analysis_workbook", "matlab_script", "figure_bundle", "framework",
}
PRIMARY_STALE_LAYERS = {
    "solution_workbook", "result_analysis_workbook", "matlab_script", "figure_bundle", "framework",
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
    allowed = {f"{problem}求解.py", f"{problem}结果深化分析.py"}
    if script.name not in allowed:
        raise ValueError(f"脚本名必须为{problem}求解.py或{problem}结果深化分析.py")
    return problem


def stage_from_filename(script: Path, problem: str) -> str:
    return "analysis" if script.name == f"{problem}结果深化分析.py" else "primary"


def _param_count(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    args = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
    return sum(arg.arg not in {"self", "cls"} for arg in args)


def _complexity(node: ast.AST) -> int:
    branch_nodes = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.IfExp, ast.Match, ast.comprehension)
    score = 1 + sum(isinstance(item, branch_nodes) for item in ast.walk(node))
    score += sum(max(0, len(item.values) - 1) for item in ast.walk(node) if isinstance(item, ast.BoolOp))
    return score


def code_quality_findings(
    text: str,
    config: dict[str, Any] | None = None,
) -> tuple[list[str], list[str], dict[str, Any]]:
    """Return blocking issues, warnings and lightweight static metrics without executing task code."""
    contract = load_yaml(QUALITY_CONTRACT)
    errors: list[str] = []
    warnings: list[str] = []
    metrics: dict[str, Any] = {}
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return [f"Python语法错误: {exc}"], [], metrics

    nonblank = sum(bool(line.strip()) for line in text.splitlines())
    metrics["nonblank_lines"] = nonblank
    line_policy = contract["line_count"]
    exemption = (config or {}).get(line_policy["exemption_field"], {})
    valid_exemption = (
        isinstance(exemption, dict)
        and exemption.get("enabled") is True
        and len(str(exemption.get("reason", "")).strip()) >= int(line_policy["exemption_reason_min_chars"])
    )
    if nonblank > int(line_policy["exemption_max"]):
        errors.append(f"代码{nonblank}行，超过绝对上限{line_policy['exemption_max']}行")
    elif nonblank > int(line_policy["hard_max"]):
        if valid_exemption:
            warnings.append(f"代码{nonblank}行，已使用复杂题豁免；仍应继续精简")
        else:
            errors.append(
                f"代码{nonblank}行，超过{line_policy['hard_max']}行；"
                "复杂题需在FULL_FIDELITY_CONFIG提供code_quality_exemption"
            )
    elif nonblank > int(line_policy["target_max"]):
        warnings.append(f"代码{nonblank}行，超过目标{line_policy['target_max']}行")

    function_policy = contract["function_size"]
    parameter_policy = contract["parameter_count"]
    complexity_policy = contract["complexity"]
    functions = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    metrics["function_count"] = len(functions)
    for node in functions:
        span = (node.end_lineno or node.lineno) - node.lineno + 1
        params = _param_count(node)
        complexity = _complexity(node)
        if span > int(function_policy["hard_max"]):
            errors.append(f"函数{node.name}共{span}行，超过{function_policy['hard_max']}行硬上限")
        elif span > int(function_policy["target_max"]):
            warnings.append(f"函数{node.name}共{span}行，超过{function_policy['target_max']}行目标")
        if params > int(parameter_policy["hard_max"]):
            errors.append(f"函数{node.name}有{params}个参数，超过{parameter_policy['hard_max']}个硬上限")
        elif params > int(parameter_policy["target_max"]):
            warnings.append(f"函数{node.name}有{params}个参数，超过{parameter_policy['target_max']}个目标")
        if complexity > int(complexity_policy["hard_max"]):
            errors.append(f"函数{node.name}静态复杂度{complexity}，超过{complexity_policy['hard_max']}")
        elif complexity > int(complexity_policy["warning_max"]):
            warnings.append(f"函数{node.name}静态复杂度{complexity}偏高")

    imported: dict[str, str] = {}
    used = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)}
    forbidden_imports = set(contract["forbidden_import_roots"])
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in forbidden_imports:
                    errors.append(f"正式求解脚本禁止导入绘图库: {root}")
                imported[alias.asname or root] = alias.name
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in forbidden_imports:
                errors.append(f"正式求解脚本禁止导入绘图库: {root}")
            for alias in node.names:
                if alias.name == "*":
                    errors.append("禁止通配import")
                else:
                    imported[alias.asname or alias.name] = f"{node.module}.{alias.name}"
        elif isinstance(node, ast.ExceptHandler) and node.type is None:
            errors.append("禁止裸except")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "breakpoint":
                errors.append("正式代码禁止breakpoint()")
            if (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "pdb"
                and node.func.attr == "set_trace"
            ):
                errors.append("正式代码禁止pdb.set_trace()")

    unused = sorted(name for name in imported if name not in used and name != "annotations")
    if unused:
        warnings.append("可能存在未使用import: " + ", ".join(unused))

    print_count = sum(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print"
        for node in ast.walk(tree)
    )
    metrics["print_calls"] = print_count
    if print_count > int(contract["print_calls"]["hard_count"]):
        errors.append(f"print调用{print_count}次，疑似调试输出过多")
    elif print_count >= int(contract["print_calls"]["warning_count"]):
        warnings.append(f"存在{print_count}处print；最终版优先使用必要日志或工作簿记录")

    top_names = [
        node.name for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    duplicates = sorted({name for name in top_names if top_names.count(name) > 1})
    if duplicates:
        errors.append("重复顶层定义: " + ", ".join(duplicates))

    return list(dict.fromkeys(errors)), list(dict.fromkeys(warnings)), metrics


def validate_script(
    project_root: Path,
    script: Path,
    expected_stage: str | None = None,
) -> tuple[list[str], dict[str, Any]]:
    issues: list[str] = []
    try:
        problem = problem_from_path(script)
    except ValueError as exc:
        return [str(exc)], {}
    filename_stage = stage_from_filename(script, problem)

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
    if stage and stage != filename_stage:
        issues.append(f"脚本文件名对应{filename_stage}阶段，但FULL_FIDELITY_CONFIG.stage={stage}")
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

    quality_errors, _, _ = code_quality_findings(text, config)
    issues.extend(quality_errors)
    return list(dict.fromkeys(issues)), config


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
    new_hash = sha256(script)
    entry["data_hash"] = str(config["data_sha256"]).lower()

    if stage == "primary":
        old_hash = entry.get("primary_code_sha256")
        accepted = entry.get("primary_execution_status") == "accepted"
        phase = str((state.get("project") or {}).get("current_phase", ""))
        if accepted and old_hash and old_hash != new_hash and phase != "solve_validate":
            raise ValueError("主求解脚本已accepted并冻结；如需修改必须先显式回退solve_validate")
        entry["code"] = relative
        entry["primary_code_sha256"] = new_hash
        entry["primary_execution_status"] = "awaiting_user_execution"
        entry.setdefault("analysis_execution_status", "pending")
        if old_hash and old_hash != new_hash:
            entry["status"] = "designed"
            entry["result_quality_status"] = "pending"
            entry["result_analysis_status"] = "pending"
            entry["analysis_execution_status"] = "pending"
            entry["result_summary_status"] = "stale"
            entry["artifacts_stale"] = True
            entry["stale_layers"] = sorted(set(entry.get("stale_layers", [])) | PRIMARY_STALE_LAYERS)
    else:
        if entry.get("primary_execution_status") != "accepted":
            raise ValueError("主工作簿未accepted，禁止交付最终结果深化分析脚本")
        old_hash = entry.get("analysis_code_sha256")
        entry["result_analysis_code"] = relative
        entry["analysis_code_sha256"] = new_hash
        entry["analysis_execution_status"] = "awaiting_user_execution"
        if old_hash != new_hash:
            entry["status"] = "solved"
            entry["result_analysis_status"] = "pending"
            entry["result_summary_status"] = "stale"
            entry["artifacts_stale"] = True
            entry["stale_layers"] = sorted(set(entry.get("stale_layers", [])) | ANALYSIS_STALE_LAYERS)
            state.setdefault("project", {})["current_phase"] = "result_analysis"

    state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")


def discover_scripts(root: Path) -> list[Path]:
    patterns = (
        "问题*求解/问题*求解.py",
        "问题*求解/问题*结果深化分析.py",
    )
    return sorted({path for pattern in patterns for path in root.glob(pattern)})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--script", type=Path)
    parser.add_argument("--stage", choices=("primary", "analysis"))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    root = args.project_root.resolve()
    scripts = (
        [args.script if args.script and args.script.is_absolute() else root / args.script]
        if args.script else discover_scripts(root)
    )
    issues: list[str] = []
    warnings: list[str] = []
    metrics: dict[str, Any] = {}
    checked: list[str] = []
    for script in scripts:
        item_issues, config = validate_script(root, script, args.stage)
        issues.extend(f"{script.name}: {item}" for item in item_issues)
        _, item_warnings, item_metrics = code_quality_findings(
            script.read_text(encoding="utf-8"), config
        )
        warnings.extend(f"{script.name}: {item}" for item in item_warnings)
        metrics[script.relative_to(root).as_posix()] = item_metrics
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
        "warnings": warnings,
        "code_quality_metrics": metrics,
        "task_code_executed": False,
        "report_persisted": False,
    }
    print(yaml.safe_dump(report, allow_unicode=True, sort_keys=False).rstrip())
    return 1 if issues and args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
