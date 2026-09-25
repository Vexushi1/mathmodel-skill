#!/usr/bin/env python3
"""Static delivery and engineering-quality validation for active numerical stages."""
from __future__ import annotations

import argparse
import ast
import hashlib
import sys
from pathlib import Path
from typing import Any, Mapping

import yaml

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = str(Path(__file__).resolve().parent)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
import state_transitions as STATE_TRANSITIONS  # noqa: E402
import artifact_identity as ARTIFACT_IDENTITY  # noqa: E402
import project_transaction as PROJECT_TX  # noqa: E402
import run_config_parser as RUN_CONFIG_PARSER  # noqa: E402
import analysis_prerequisites as ANALYSIS_PREREQUISITES  # noqa: E402
import stage_code as STAGE_CODE  # noqa: E402
import conformance_gate as CONFORMANCE  # noqa: E402
from execution_protocol import SOURCE_RECEIPT_VERSIONS, is_source_receipt, auxiliary_config_issues
from stage_inputs import observe_inputs
import matlab_code_checks as MATLAB_CHECKS  # noqa: E402
STATE_TRANSITION_CONTRACT = yaml.safe_load(
    (SKILL_ROOT / "core" / "state_transition_contract.yaml").read_text(encoding="utf-8")
) or {}
QUALITY_CONTRACT = SKILL_ROOT / "core" / "code_quality_contract.yaml"
FALSE_FLAGS = (
    "allow_reduced_data", "allow_coarser_grid", "allow_shorter_horizon",
    "allow_fewer_repetitions", "allow_relaxed_tolerance", "allow_silent_solver_fallback",
)
PLACEHOLDERS = ("TODO", "FIXME", "__QUESTION_NAME__", "NotImplementedError")
CONFIG_NAMES = RUN_CONFIG_PARSER.CONFIG_NAMES
LEGACY_CONFIG_NAMES = {"FULL_FIDELITY_CONFIG", "FULL_RUN_CONFIG"}
TASK_REQUIRED_FIELDS = {
    "stage", "problem_name", "data_paths", "data_sha256", "solver", "random_seed",
    "tolerance", "iteration_or_time_limit", "expected_workbook",
}
POLICY_INVARIANTS = {
    "execution_owner": "user",
    "execution_profile": "full_fidelity",
    **{flag: False for flag in FALSE_FLAGS},
}
LEGACY_REQUIRED_FIELDS = {
    *TASK_REQUIRED_FIELDS, "solver_version", *POLICY_INVARIANTS,
}
PRIMARY_QUALITY_PROTOCOL_VERSION = "1.0.0"
PRIMARY_REQUIRED_FIELDS = {"primary_quality_protocol_version"}
RUN_RECEIPT_PROTOCOL_VERSION = "1.0.0"
SOLVER_RECEIPT_PROTOCOL_VERSION = "1.1.0"
VALID_PREPROCESSING_DECISIONS = {"not_needed", "question_local", "project_level"}
DATA_READER_NAMES = {
    "open", "ExcelFile", "read_csv", "read_excel", "read_table", "read_fwf",
    "read_json", "read_parquet", "read_feather", "read_pickle", "read_hdf",
    "load", "loadtxt", "genfromtxt",
}
DATA_READER_PATH_KEYWORDS = {"path", "filepath", "filename", "fname", "io", "filepath_or_buffer"}


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_sha256(value: Any) -> bool:
    text = str(value).strip().lower()
    return len(text) == 64 and all(character in "0123456789abcdef" for character in text)


def embedded_config(text: str) -> tuple[str, dict[str, Any]]:
    """Return the single supported top-level config using the shared P5 parser."""
    return RUN_CONFIG_PARSER.parse_embedded_config(
        text,
        messages=RUN_CONFIG_PARSER.DELIVERY_MESSAGES,
    )

def script_identity(script: Path) -> tuple[str, str]:
    identity = STAGE_CODE.script_identity(script)
    return identity.problem_name, identity.stage


def _stage_selection(entry: Mapping[str, Any], stage: str) -> Mapping[str, Any]:
    if not isinstance(entry, Mapping):
        raise ValueError("阶段状态必须为映射")
    execution = entry.get("solver_execution")
    if execution is not None and not isinstance(execution, Mapping):
        raise ValueError("solver_execution必须为映射")
    selection = (execution or {}).get(stage)
    if selection is not None and not isinstance(selection, Mapping):
        raise ValueError(f"solver_execution.{stage}必须为映射")
    return selection or {}


def problem_from_path(script: Path) -> str:
    return script_identity(script)[0]


def stage_from_filename(script: Path, problem: str | None = None) -> str:
    return script_identity(script)[1]


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
                "复杂题需在嵌入运行配置提供code_quality_exemption"
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
                    errors.append(f"正式数值脚本禁止导入绘图库: {root}")
                imported[alias.asname or root] = alias.name
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in forbidden_imports:
                errors.append(f"正式数值脚本禁止导入绘图库: {root}")
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


def _normalize_path_token(value: Any) -> str:
    text = str(value or "").strip().replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    return text.casefold()


def _path_matches(candidate: Any, target: Any) -> bool:
    left = _normalize_path_token(candidate)
    right = _normalize_path_token(target)
    if not left or not right:
        return False
    return left == right or left.endswith("/" + right) or right.endswith("/" + left)


def _call_leaf_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _literal_path_argument(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Call) and _call_leaf_name(node.func) in {"Path", "str"} and node.args:
        return _literal_path_argument(node.args[0])
    return None


def literal_data_reader_paths(text: str) -> list[str]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or _call_leaf_name(node.func) not in DATA_READER_NAMES:
            continue
        candidate: ast.AST | None = node.args[0] if node.args else None
        if candidate is None:
            candidate = next(
                (item.value for item in node.keywords if item.arg in DATA_READER_PATH_KEYWORDS),
                None,
            )
        if candidate is not None:
            value = _literal_path_argument(candidate)
            if value:
                found.append(value)
    return list(dict.fromkeys(found))


def _decision_gate_issues(
    project_root: Path,
    stage: str,
    data_hash: str | None = None,
    data_paths: Any = None,
    code_text: str = "",
    backend: str = "python",
    data_identity_mode: Any = "combined",
    modern: bool = False,
    state: dict[str, Any] | None = None,
) -> list[str]:
    state_path = project_root / "state" / "project_state.yaml"
    if state is None and not state_path.is_file():
        return (["preprocessing_workbook模式必须有已验收的项目级预处理状态"]
                if modern and data_identity_mode == "preprocessing_workbook" else [])
    if state is None:
        state = load_yaml(state_path)
    preprocessing = state.get("preprocessing") or {}
    decision = str(preprocessing.get("decision", "")).strip()
    if decision not in VALID_PREPROCESSING_DECISIONS:
        return ["项目状态缺少有效preprocessing.decision；正式代码前必须先锁定not_needed/question_local/project_level"]
    issues: list[str] = []
    if stage == "preprocessing":
        if decision != "project_level":
            issues.append("只有preprocessing.decision=project_level时才允许交付数据预处理.py")
        return issues
    if modern and data_identity_mode == "preprocessing_workbook" and decision != "project_level":
        issues.append("preprocessing_workbook模式只允许已验收的project_level预处理")
    if stage in {"primary", "analysis"} and decision == "project_level":
        if preprocessing.get("status") != "accepted" or preprocessing.get("quality_status") != "passed":
            issues.append("project_level项目必须先验收数据预处理结果.xlsx并通过预处理质量门")
        expected = str(preprocessing.get("workbook_sha256", "")).lower()
        if expected and data_hash and expected != str(data_hash).lower():
            issues.append(f"{stage}阶段data_sha256必须等于已验收数据预处理结果.xlsx哈希")

        covered = [str(item) for item in (preprocessing.get("covered_raw_sources") or []) if str(item).strip()]
        if not covered:
            issues.append("project_level必须在state.preprocessing.covered_raw_sources声明被统一工作簿替代的原始数据源")
        configured_paths = [str(item) for item in (data_paths or [])] if isinstance(data_paths, (list, tuple)) else []
        workbook = str(preprocessing.get("workbook") or "数据预处理/数据预处理结果.xlsx")
        if modern:
            if data_identity_mode != "preprocessing_workbook":
                issues.append("新1.1 project_level阶段必须显式data_identity_mode=preprocessing_workbook")
            try:
                accepted_path = (project_root / workbook).resolve()
                if (not accepted_path.is_relative_to(project_root.resolve()) or accepted_path.suffix.lower() != ".xlsx"
                        or not accepted_path.is_file()):
                    issues.append("preprocessing_workbook模式必须绑定项目内真实已验收xlsx")
                elif not is_sha256(expected) or sha256(accepted_path) != expected:
                    issues.append("已验收预处理工作簿当前文件SHA-256不一致")
                if (len(configured_paths) != 1
                        or (project_root / configured_paths[0]).resolve() != accepted_path):
                    issues.append("preprocessing_workbook模式data_paths必须恰含唯一已登记预处理工作簿")
            except (OSError, ValueError) as exc:
                issues.append(f"preprocessing_workbook路径或身份无法核验: {exc}")
        if stage == "primary" and not any(_path_matches(item, workbook) for item in configured_paths):
            issues.append("project_level主求解嵌入运行配置.data_paths必须包含已验收数据预处理结果.xlsx")
        for item in configured_paths:
            if any(_path_matches(item, source) for source in covered):
                issues.append(f"project_level下游data_paths不得重新声明已覆盖共享原始数据源: {item}")
        reader_paths = (MATLAB_CHECKS.literal_data_reader_paths(code_text) if backend == "matlab"
                        else literal_data_reader_paths(code_text))
        for item in reader_paths:
            if any(_path_matches(item, source) for source in covered):
                issues.append(f"project_level下游代码不得重新读取已覆盖共享原始数据源: {item}")
    return list(dict.fromkeys(issues))


def validate_script(
    project_root: Path,
    script: Path,
    expected_stage: str | None = None,
    *,
    matlab_command: str | None = None,
    require_native: bool = False,
    native_report: dict[str, Any] | None = None,
) -> tuple[list[str], dict[str, Any]]:
    issues: list[str] = []
    try:
        problem, filename_stage = script_identity(script)
    except ValueError as exc:
        return [str(exc)], {}

    identity = STAGE_CODE.script_identity(script)
    backend = identity.backend
    try:
        script.resolve().relative_to(project_root.resolve())
    except ValueError:
        return ["阶段代码路径越出项目根目录"], {}
    source_bytes = script.read_bytes()
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    text = source_bytes.decode("utf-8-sig", errors="strict")
    for marker in PLACEHOLDERS:
        if marker in text:
            issues.append(f"正式代码仍含占位标记: {marker}")
    if backend == "python" and 'if __name__ == "__main__":' not in text and "if __name__ == '__main__':" not in text:
        issues.append("正式代码缺少main入口")

    config_name = ""
    try:
        config_name, config = RUN_CONFIG_PARSER.parse_embedded_config(
            text, messages=RUN_CONFIG_PARSER.DELIVERY_MESSAGES, backend=backend)
    except (SyntaxError, ValueError) as exc:
        issues.append(str(exc))
        config = {}

    if config_name:
        required_fields = TASK_REQUIRED_FIELDS if config_name == "RUN_CONFIG" else LEGACY_REQUIRED_FIELDS
        for field in sorted(required_fields):
            if field not in config or config[field] in (None, "", []):
                issues.append(f"{config_name}缺少字段: {field}")

    stage = str(config.get("stage", ""))
    if stage not in {"preprocessing", "primary", "analysis"}:
        issues.append("stage必须为preprocessing、primary或analysis")
    receipt_protocol = str(config.get("run_receipt_protocol_version", "")).strip()
    allowed_protocols = {RUN_RECEIPT_PROTOCOL_VERSION} if stage == "preprocessing" else {
        RUN_RECEIPT_PROTOCOL_VERSION, *SOURCE_RECEIPT_VERSIONS}
    if receipt_protocol and receipt_protocol not in allowed_protocols:
        issues.append(f"run_receipt_protocol_version不支持当前阶段: {receipt_protocol}")
    if backend == "matlab" and not is_source_receipt(receipt_protocol):
        issues.append("新MATLAB阶段必须声明run_receipt_protocol_version=1.1.0/1.2.0")
    modern = is_source_receipt(receipt_protocol)
    issues.extend(auxiliary_config_issues(config))
    source_fingerprint = None
    data_identity_mode = config.get("data_identity_mode", "combined")
    if "data_identity_mode" in config and (not modern or data_identity_mode not in ("combined", "preprocessing_workbook")):
        issues.append("data_identity_mode仅1.1阶段允许combined或preprocessing_workbook")
    if stage == "preprocessing" and ("solver_backend" in config or "code_dependencies" in config):
        issues.append("项目级预处理本期保持1.0协议，不接受solver_backend/code_dependencies扩展")
    if modern:
        if config.get("solver_backend") != backend:
            issues.append("solver_backend必须与阶段源码后端一致")
        for field in ("tolerance", "iteration_or_time_limit"):
            if isinstance(config.get(field), (dict, list, tuple, bool)):
                issues.append(f"{field}仅支持标量，不支持嵌套结构")
        if "code_bundle_sha256" in config:
            issues.append("RUN_CONFIG不得嵌入包含入口自身的bundle摘要")
        try:
            source_fingerprint = STAGE_CODE.stage_code_fingerprint(project_root, script, config.get("code_dependencies", []))
            issues.extend(STAGE_CODE.dependency_reference_issues(project_root, script, config))
        except (OSError, ValueError, SyntaxError, TypeError, KeyError) as exc:
            issues.append(str(exc))
    elif "solver_backend" in config or config.get("code_dependencies"):
        issues.append("后端与源码依赖扩展必须使用1.1.0/1.2.0回执协议")
    state_path = project_root / "state" / "project_state.yaml"
    if stage in {"primary", "analysis"}:
        state = load_yaml(state_path) if state_path.is_file() else {}
        try:
            selected_backend = STAGE_CODE.current_project_backend(state, required=True)
            if selected_backend != backend or config.get("solver_backend") != selected_backend or not modern:
                issues.append("项目后端与源码/RUN_CONFIG/协议不一致，不得静默替换或降级")
        except STAGE_CODE.StageCodeError as exc:
            issues.append(str(exc))
    if stage == "primary":
        for field in sorted(PRIMARY_REQUIRED_FIELDS):
            if field not in config or config[field] in (None, "", []):
                issues.append(f"primary嵌入运行配置缺少字段: {field}")
        if config.get("primary_quality_protocol_version") not in (None, "", PRIMARY_QUALITY_PROTOCOL_VERSION):
            issues.append(f"primary_quality_protocol_version必须为{PRIMARY_QUALITY_PROTOCOL_VERSION}")
    elif config.get("primary_quality_protocol_version") not in (None, ""):
        issues.append("primary_quality_protocol_version只允许出现在primary阶段运行配置")
    if stage and stage != filename_stage:
        issues.append(f"脚本文件名对应{filename_stage}阶段，但{config_name or '嵌入运行配置'}.stage={stage}")
    if expected_stage and stage != expected_stage:
        issues.append(f"stage应为{expected_stage}")
    if config.get("problem_name") != problem:
        issues.append("problem_name与目录/阶段身份不一致")

    if config_name == "RUN_CONFIG":
        for field, expected_value in POLICY_INVARIANTS.items():
            if field in config and config[field] != expected_value:
                issues.append(f"RUN_CONFIG不得覆盖全局执行政策: {field}必须为{expected_value!r}")
    elif config_name in LEGACY_CONFIG_NAMES:
        if config.get("execution_owner") != "user":
            issues.append("execution_owner必须为user")
        if config.get("execution_profile") != "full_fidelity":
            issues.append("execution_profile必须为full_fidelity")
        for flag in FALSE_FLAGS:
            if config.get(flag) is not False:
                issues.append(f"{flag}必须显式为false")

    if not is_sha256(config.get("data_sha256")):
        issues.append("data_sha256必须是64位十六进制SHA-256")

    expected = {
        "preprocessing": "数据预处理结果.xlsx",
        "primary": f"{problem}求解结果.xlsx",
        "analysis": f"{problem}结果深化分析.xlsx",
    }.get(stage, "")
    if expected and Path(str(config.get("expected_workbook", ""))).name != expected:
        issues.append(f"expected_workbook必须指向{expected}")

    issues.extend(_decision_gate_issues(
        project_root, stage, str(config.get("data_sha256", "")),
        config.get("data_paths"), text, backend,
        data_identity_mode, modern,
    ))
    if modern:
        try:
            state = load_yaml(state_path) if state_path.is_file() else {}
            issues.extend(observe_inputs(project_root, config, state)["issues"])
        except (OSError, ValueError, TypeError) as exc:
            issues.append(f"阶段实际输入无法核验: {exc}")
    if stage == "analysis":
        state_path = project_root / "state" / "project_state.yaml"
        state = load_yaml(state_path) if state_path.is_file() else {}
        entry = (state.get("subproblems") or {}).get(_question_key(problem), {})
        issues.extend(ANALYSIS_PREREQUISITES.analysis_issues(
            project_root, state, entry, data_hash=config.get("data_sha256"),
            require_project_policy=True))
        if modern:
            expected_primary = (entry.get("validated_artifact_hashes") or {}).get("solution_workbook")
            if not is_sha256(config.get("primary_workbook_sha256")):
                issues.append("1.1 analysis必须声明有效primary_workbook_sha256")
            elif not expected_primary or str(config["primary_workbook_sha256"]).lower() != str(expected_primary).lower():
                issues.append("1.1 analysis必须绑定当前accepted主工作簿SHA-256")
    if backend == "matlab":
        quality_errors, _, _ = MATLAB_CHECKS.matlab_code_findings(
            text, config, contract=load_yaml(QUALITY_CONTRACT), filename=script.name)
        if require_native or matlab_command:
            native = MATLAB_CHECKS.native_code_analysis(script, matlab_command)
            if native_report is not None:
                native_report.update(native)
            quality_errors.extend(native["issues"])
            if native.get("source_sha256") and native["source_sha256"] != source_sha256:
                quality_errors.append("MATLAB原生检查源码与本次配置/工程检查源码不一致")
            for item in native.get("complexity_metrics", []):
                if item["value"] > load_yaml(QUALITY_CONTRACT)["complexity"]["hard_max"]:
                    quality_errors.append(f"MATLAB原生复杂度L{item['line']}={item['value']}超过硬上限")
    else:
        quality_errors, _, _ = code_quality_findings(text, config)
    issues.extend(quality_errors)
    dependency_reports: dict[str, Any] = {}
    dependency_warnings: list[str] = []
    if source_fingerprint is not None:
        for record in source_fingerprint["files"]:
            helper = project_root / record["path"]
            if helper.resolve() == script.resolve():
                continue
            try:
                helper_text = helper.read_text(encoding="utf-8-sig")
            except (OSError, ValueError) as exc:
                issues.append(f"源码依赖无法读取: {record['path']}: {exc}")
                continue
            if helper.suffix.lower() == ".m":
                errors, warnings, metrics = MATLAB_CHECKS.matlab_code_findings(
                    helper_text, {}, contract=load_yaml(QUALITY_CONTRACT), filename=helper.name)
                native = None
                if require_native or matlab_command:
                    native = MATLAB_CHECKS.native_code_analysis(helper, matlab_command)
                    errors.extend(native["issues"])
                    warnings.extend(native.get("warnings", []))
                    metrics["native_analysis_status"] = native["status"]
                    metrics["native_release"] = native.get("release")
                    metrics["native_source_sha256"] = native.get("source_sha256")
                    metrics["native_complexity"] = native.get("complexity_metrics", [])
                    if native.get("source_sha256") and native["source_sha256"] != record["sha256"]:
                        errors.append("MATLAB依赖原生检查源码与本次bundle不一致")
                    if any(item["value"] > load_yaml(QUALITY_CONTRACT)["complexity"]["hard_max"]
                           for item in native.get("complexity_metrics", [])):
                        errors.append("MATLAB依赖原生复杂度超过硬上限")
            else:
                errors, warnings, metrics = code_quality_findings(helper_text, {})
            issues.extend(f"{record['path']}: {error}" for error in errors)
            dependency_warnings.extend(f"{record['path']}: {warning}" for warning in warnings)
            dependency_reports[record["path"]] = metrics
        try:
            if STAGE_CODE.stage_code_fingerprint(project_root, script, config.get("code_dependencies", [])) != source_fingerprint:
                issues.append("源码bundle在工程/原生检查期间改变，必须重新检查")
        except (OSError, ValueError) as exc:
            issues.append(f"源码bundle在工程/原生检查期间改变: {exc}")
        if native_report is not None:
            native_report["validated_bundle_sha256"] = source_fingerprint["bundle_sha256"]
            native_report["dependency_code_quality"] = dependency_reports
            native_report["dependency_warnings"] = dependency_warnings
    try:
        if sha256(script) != source_sha256:
            issues.append("源码在代码检查期间改变，必须重新检查")
    except OSError as exc:
        issues.append(f"源码在代码检查期间无法读取: {exc}")
    if stage in {"primary", "analysis"}:
        state = load_yaml(state_path) if state_path.is_file() else {}
        conformance = CONFORMANCE.inspect_gate(project_root, state, _question_key(problem), stage)
        issues.extend(conformance["issues"])
        binding = conformance.get("delivery_candidate")
        if binding and binding["entrypoint"] != script.relative_to(project_root).as_posix():
            issues.append("conformance: inspected entry differs from the delivered script")
        if native_report is not None and conformance["enabled"]:
            native_report["conformance"] = conformance
    return list(dict.fromkeys(issues)), config


def _question_key(problem: str) -> str:
    order = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    suffix = problem.removeprefix("问题")
    return f"Q{order.index(suffix) + 1}" if suffix in order else problem


def update_state(project_root: Path, config: dict[str, Any], script: Path, *,
                 expected_source_sha256: str | None = None,
                 expected_bundle_sha256: str | None = None) -> list[dict[str, Any]]:
    configuration_issues = auxiliary_config_issues(config)
    if configuration_issues:
        raise ValueError("; ".join(configuration_issues))
    state_path = project_root / "state" / "project_state.yaml"
    if not state_path.is_file():
        if config.get("stage") == "preprocessing":
            return []
        raise ValueError("缺少项目状态与已锁项目后端，禁止正式数值代码交付")
    observed_state = load_yaml(state_path)
    if any(CONFORMANCE.present(entry) for entry in (observed_state.get("subproblems") or {}).values()):
        from runtime_assurance import ProjectStateSnapshot
        snapshot = ProjectStateSnapshot.capture(project_root)
        state = snapshot.payload()
        base_generation = PROJECT_TX.state_generation(state)
    else:
        _, state, base_generation = PROJECT_TX.load_state_for_update(project_root)
    problem = str(config["problem_name"])
    stage = str(config["stage"])
    if stage in {"primary", "analysis"}:
        project_backend = STAGE_CODE.current_project_backend(state, required=True)
    new_hash = sha256(script)
    if expected_source_sha256 is not None and new_hash != expected_source_sha256.lower():
        raise ValueError("源码在代码检查后改变，禁止登记未验证版本")
    relative = script.relative_to(project_root).as_posix()
    modern = is_source_receipt(config.get("run_receipt_protocol_version"))
    if stage in {"primary", "analysis"}:
        actual_backend = STAGE_CODE.script_identity(script).backend
        if not modern or config.get("solver_backend") != project_backend or actual_backend != project_backend:
            raise ValueError("项目后端与源码/RUN_CONFIG/协议不一致，禁止交付")
    fingerprint = STAGE_CODE.stage_code_fingerprint(project_root, script, config.get("code_dependencies", [])) if modern else None
    if expected_bundle_sha256 is not None and (fingerprint is None or fingerprint["bundle_sha256"] != expected_bundle_sha256.lower()):
        raise ValueError("源码bundle在代码检查后改变，禁止登记未验证版本")
    if stage in {"primary", "analysis"}:
        gate_issues = _decision_gate_issues(
            project_root, stage, str(config.get("data_sha256", "")), config.get("data_paths"),
            script.read_text(encoding="utf-8-sig"), project_backend,
            config.get("data_identity_mode", "combined"), modern, state=state)
        if modern:
            try:
                gate_issues.extend(observe_inputs(project_root, config, state)["issues"])
            except (OSError, ValueError, TypeError) as exc:
                gate_issues.append(f"阶段实际输入无法核验: {exc}")
        if gate_issues:
            raise ValueError("; ".join(gate_issues))
    transition_reports: list[dict[str, Any]] = []

    if stage == "preprocessing":
        preprocessing = state.setdefault("preprocessing", {})
        if preprocessing.get("decision") != "project_level":
            raise ValueError("只有project_level项目允许写入预处理执行状态")
        old_hash = preprocessing.get("code_sha256")
        preprocessing["code"] = relative
        preprocessing["code_sha256"] = new_hash
        preprocessing["status"] = "awaiting_user_preprocessing"
        preprocessing["quality_status"] = "pending"
        data = state.setdefault("data", {})
        data.setdefault("version_hashes", {})["preprocessing_input"] = str(config["data_sha256"]).lower()
        data["active_source_mode"] = "raw"
        state.setdefault("project", {})["current_phase"] = "data_preprocessing"
        if old_hash and old_hash != new_hash:
            preprocessing["workbook"] = ""
            preprocessing["workbook_sha256"] = ""
            for key, entry in (state.get("subproblems") or {}).items():
                if not isinstance(entry, dict):
                    continue
                local = STATE_TRANSITIONS.apply_local_event(
                    entry, "data_changed", STATE_TRANSITION_CONTRACT
                )
                transition_reports.append({
                    "event": "data_changed",
                    "source": "project.preprocessing",
                    "affected_questions": [str(key)],
                    "dependency_cycles": [],
                    "transitions": [{
                        "question": str(key),
                        "scope": "own",
                        "source": "project.preprocessing",
                        "dependency_kind": "data",
                        "profile": local["profile"],
                        "stale_layers": local["stale_layers"],
                        "status_updates": local["status_updates"],
                        "emitted_impacts": local["emitted_impacts"],
                        "reason": "project-level preprocessing code changed",
                    }],
                })
        PROJECT_TX.commit_project_state(
            project_root, state, expected_generation=base_generation
        )
        return transition_reports

    key = _question_key(problem)
    entry = state.setdefault("subproblems", {}).setdefault(key, {})
    conformance = CONFORMANCE.inspect_gate(project_root, state, key, stage)
    if conformance["issues"]:
        raise ValueError("; ".join(conformance["issues"]))
    conformance_binding = conformance.get("delivery_candidate")
    if conformance_binding and CONFORMANCE.digest("HSK-conformance-config-v1", config) != conformance.get("observed_config_sha256"):
        raise ValueError("conformance: caller configuration differs from captured source RUN_CONFIG")
    if conformance_binding and conformance_binding["entrypoint"] != relative:
        raise ValueError("conformance: inspected entry differs from delivery target")
    selection = _stage_selection(entry, stage)
    old_path = entry.get("code" if stage == "primary" else "result_analysis_code")
    binding_changed = bool(
        (old_path and old_path != relative)
        or (modern and selection.get("bundle_sha256") and str(selection["bundle_sha256"]).lower() != fingerprint["bundle_sha256"])
    )
    conformance_changed = bool(conformance_binding and selection.get("bundle_sha256")
                               and selection.get(CONFORMANCE.DELIVERY) != conformance_binding)
    if stage == "analysis":
        prerequisite_issues = ANALYSIS_PREREQUISITES.analysis_issues(
            project_root, state, entry, data_hash=config.get("data_sha256"),
            require_project_policy=True)
        if prerequisite_issues:
            raise ValueError("; ".join(prerequisite_issues))
    try:
        ARTIFACT_IDENTITY.canonicalize_entry_hashes(entry)
    except ARTIFACT_IDENTITY.ArtifactIdentityError as exc:
        raise ValueError(f"artifact identity alias conflict: {exc}") from exc
    if stage == "primary":
        entry["data_hash"] = str(config["data_sha256"]).lower()
        old_hash = entry.get("primary_code_sha256")
        accepted = entry.get("primary_execution_status") == "accepted"
        unchanged_conformance = not conformance_binding or (
            selection.get(CONFORMANCE.DELIVERY) == conformance_binding
            and (selection.get(CONFORMANCE.ACCEPTANCE) or {}).get("applicability") == "current")
        unchanged_accepted = accepted and old_hash == new_hash and not binding_changed and unchanged_conformance
        phase = str((state.get("project") or {}).get("current_phase", ""))
        if accepted and old_hash and (old_hash != new_hash or binding_changed) and phase != "solve_validate":
            raise ValueError("主求解脚本已accepted并冻结；如需修改必须先显式回退solve_validate")
        entry["code"] = relative
        entry["primary_code_sha256"] = new_hash
        entry.setdefault("artifact_hashes", {})["primary_code"] = new_hash
        entry.setdefault("analysis_execution_status", "pending")
        if not unchanged_accepted:
            entry["primary_execution_status"] = "awaiting_user_execution"
        if old_hash and (old_hash != new_hash or binding_changed):
            transition_reports.append(
                STATE_TRANSITIONS.apply_transition(
                    state,
                    event="primary_code_changed",
                    source_question=key,
                    contract=STATE_TRANSITION_CONTRACT,
                )
            )
            entry["status"] = "designed"
            entry["primary_execution_status"] = "awaiting_user_execution"
        elif conformance_changed:
            transition_reports.append(STATE_TRANSITIONS.apply_transition(
                state, event="primary_conformance_changed", source_question=key,
                contract=STATE_TRANSITION_CONTRACT))
            entry["status"] = "designed"
            entry["primary_execution_status"] = "awaiting_user_execution"
            state.setdefault("project", {})["current_phase"] = "solve_validate"
    else:
        if entry.get("primary_execution_status") != "accepted":
            raise ValueError("主工作簿未accepted，禁止交付最终结果深化分析脚本")
        old_hash = entry.get("analysis_code_sha256")
        entry["result_analysis_code"] = relative
        entry["analysis_code_sha256"] = new_hash
        entry.setdefault("artifact_hashes", {})["analysis_code"] = new_hash
        if old_hash != new_hash or binding_changed:
            transition_reports.append(
                STATE_TRANSITIONS.apply_transition(
                    state,
                    event="analysis_code_changed",
                    source_question=key,
                    contract=STATE_TRANSITION_CONTRACT,
                )
            )
            entry["status"] = "solved"
            state.setdefault("project", {})["current_phase"] = "result_analysis"
        elif conformance_changed:
            transition_reports.append(STATE_TRANSITIONS.apply_transition(
                state, event="analysis_conformance_changed", source_question=key,
                contract=STATE_TRANSITION_CONTRACT))
            entry["status"] = "solved"
            state.setdefault("project", {})["current_phase"] = "result_analysis"
        entry["analysis_execution_status"] = "awaiting_user_execution"

    if modern:
        target = entry.setdefault("solver_execution", {}).setdefault(stage, {})
        target["bundle_sha256"] = fingerprint["bundle_sha256"]
        if str(target.get("validated_bundle_sha256", "")).lower() != fingerprint["bundle_sha256"]:
            target.pop("validated_bundle_sha256", None)

    if sha256(script) != new_hash or (modern and STAGE_CODE.stage_code_fingerprint(
            project_root, script, config.get("code_dependencies", [])) != fingerprint):
        raise ValueError("源码集合在交付提交前改变，必须重新检查")
    if modern:
        final_input_issues = observe_inputs(project_root, config, state)["issues"]
        if final_input_issues:
            raise ValueError("; ".join(final_input_issues))
    if conformance_binding:
        target = entry["solver_execution"][stage]
        if CONFORMANCE.ACCEPTANCE in target and (
                target.get(CONFORMANCE.DELIVERY) != conformance_binding
                or entry.get(f"{stage}_execution_status") != "accepted"):
            target[CONFORMANCE.ACCEPTANCE]["applicability"] = "stale"
        target[CONFORMANCE.DELIVERY] = conformance_binding
    observed = conformance["observed_sources"]
    CONFORMANCE.assert_observed(project_root, observed)
    PROJECT_TX.commit_project_state(
        project_root, state, expected_generation=base_generation,
        expected_file_hashes=observed["project"] or None,
        validators=[CONFORMANCE.skill_validator(observed)] if conformance["enabled"] else (),
    )
    return transition_reports


def discover_scripts(root: Path) -> list[Path]:
    state_path = root / "state/project_state.yaml"
    state = load_yaml(state_path) if state_path.is_file() else {}
    scripts = [root / "数据预处理/数据预处理.py"] if (root / "数据预处理/数据预处理.py").is_file() else []
    for folder in sorted(root.glob("问题*求解")):
        if not folder.is_dir():
            continue
        problem = folder.name.removesuffix("求解")
        entry = (state.get("subproblems") or {}).get(_question_key(problem), {})
        for stage in ("primary", "analysis"):
            field = "code" if stage == "primary" else "result_analysis_code"
            if not isinstance(entry, Mapping) or not entry.get(field):
                continue  # An orphan standard filename does not grant delivery eligibility.
            project_backend = STAGE_CODE.current_project_backend(state, required=True)
            code = STAGE_CODE.resolve_stage_code(
                root, problem, stage, entry=entry, project_backend=project_backend)
            if code:
                scripts.append(code.path)
    return sorted(set(scripts))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--script", type=Path)
    parser.add_argument("--stage", choices=("preprocessing", "primary", "analysis"))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--matlab-command", help="MATLAB executable for native static Code Analyzer")
    args = parser.parse_args()
    root = args.project_root.resolve()
    try:
        scripts = ([args.script if args.script.is_absolute() else root / args.script]
                   if args.script else discover_scripts(root))
    except ValueError as exc:
        print(str(exc))
        return 1
    if not scripts:
        print("未发现可交付的当前阶段代码")
        return 1
    issues: list[str] = []
    warnings: list[str] = []
    metrics: dict[str, Any] = {}
    checked: list[str] = []
    transition_reports: list[dict[str, Any]] = []
    for script in scripts:
        script = STAGE_CODE._expand_windows_short_path(script.absolute())
        checked_source_sha256 = sha256(script)
        native_report: dict[str, Any] = {}
        item_issues, config = validate_script(root, script, args.stage, matlab_command=args.matlab_command,
                                             require_native=args.write or args.strict, native_report=native_report)
        issues.extend(f"{script.name}: {item}" for item in item_issues)
        if script.suffix.lower() == ".m":
            _, item_warnings, item_metrics = MATLAB_CHECKS.matlab_code_findings(
                script.read_text(encoding="utf-8-sig"), config, contract=load_yaml(QUALITY_CONTRACT), filename=script.name)
            if "status" in native_report:
                item_metrics["native_analysis_status"] = native_report["status"]
                item_metrics["native_release"] = native_report.get("release")
                item_metrics["native_source_sha256"] = native_report.get("source_sha256")
                item_metrics["native_complexity"] = native_report.get("complexity_metrics", [])
                item_warnings.extend(native_report.get("warnings", []))
        else:
            _, item_warnings, item_metrics = code_quality_findings(script.read_text(encoding="utf-8"), config)
        if native_report.get("dependency_code_quality"):
            item_metrics["dependency_code_quality"] = native_report["dependency_code_quality"]
            if any(item.get("native_analysis_status") == "unverified" for item in native_report["dependency_code_quality"].values()):
                item_metrics["native_analysis_status"] = "unverified"
            item_warnings.extend(native_report.get("dependency_warnings", []))
        warnings.extend(f"{script.name}: {item}" for item in item_warnings)
        metrics[script.relative_to(root).as_posix()] = item_metrics
        checked.append(script.relative_to(root).as_posix())
        if args.write and not item_issues:
            try:
                transition_reports.extend(update_state(root, config, script,
                                                       expected_source_sha256=checked_source_sha256,
                                                       expected_bundle_sha256=native_report.get("validated_bundle_sha256")))
            except ValueError as exc:
                issues.append(f"{script.name}: {exc}")

    report = {
        "status": ("failed" if issues else "unverified" if any(
            item.get("native_analysis_status") == "unverified" for item in metrics.values()) else "passed"),
        "checked_scripts": checked,
        "issues": issues,
        "warnings": warnings,
        "code_quality_metrics": metrics,
        "state_transitions": transition_reports,
        "task_code_executed": False,
        "report_persisted": False,
    }
    print(yaml.safe_dump(report, allow_unicode=True, sort_keys=False).rstrip())
    return 1 if issues and args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
