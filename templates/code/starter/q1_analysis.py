"""Instantiate in the question folder after acceptance of the primary solution to a*x=b."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import platform
import random
import tempfile
import time

import openpyxl


RUN_CONFIG = {
    "stage": "analysis", "problem_name": "问题一", "solver_backend": "python",
    "solver": "analytic_parameter_sweep", "random_seed": 2026,
    "tolerance": 1e-10, "iteration_or_time_limit": 3,
    "data_paths": ["input.json"], "data_sha256": "__DATA_SHA256__",
    "code_dependencies": [], "run_receipt_protocol_version": "1.1.0",
    "primary_workbook": "问题一求解/问题一求解结果.xlsx",
    "primary_workbook_sha256": "__ACCEPTED_PRIMARY_SHA256__",
    "expected_workbook": "问题一求解/问题一结果深化分析.xlsx",
    "ordinary_experiment_protocol_version": "1.0.0",
    "ordinary_experiments": [
        {"id": "SENS-Q1-SIGN", "method": "parameter_sensitivity",
         "target": "系数扰动后解是否始终为正", "claim": "声明的系数范围内解保持正值"},
        {"id": "SENS-Q1-CHANGE", "method": "parameter_sensitivity",
         "target": "系数扰动是否改变已验收解", "claim": "至少一个声明场景的解偏离基准超过容差"},
    ],
}


def project_path(root, relative):
    if not isinstance(relative, str) or "\\" in relative or ":" in relative:
        raise ValueError("Use a project-relative POSIX path")
    if PurePosixPath(relative).is_absolute() or any(part in ("", ".", "..") for part in relative.split("/")):
        raise ValueError(f"Invalid relative path: {relative}")
    path = root / relative
    if path.resolve() != path:
        raise ValueError(f"Project path uses an alias: {relative}")
    return path


def file_hash(path):
    with path.open("rb") as stream:
        digest = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def one_file_bundle(relative, digest):
    return hashlib.sha256(relative.encode("utf-8") + b"\0" + bytes.fromhex(digest)).hexdigest()


def observe(root, code, config):
    if (config["stage"], config["solver_backend"], config["run_receipt_protocol_version"]) != (
            "analysis", "python", "1.1.0"):
        raise ValueError("This analysis example uses the Python 1.1 receipt")
    if config["code_dependencies"] or len(config["data_paths"]) != 1:
        raise ValueError("This self-contained example uses one model input")
    relative = config["data_paths"][0]
    data_hash = file_hash(project_path(root, relative))
    mode = config.get("data_identity_mode", "combined")
    if mode == "combined":
        data_hash = one_file_bundle(relative, data_hash)
    elif mode != "preprocessing_workbook" or not relative.lower().endswith(".xlsx"):
        raise ValueError("Unsupported input identity mode")
    primary_hash = file_hash(project_path(root, config["primary_workbook"]))
    if data_hash != config["data_sha256"].lower() or primary_hash != config["primary_workbook_sha256"].lower():
        raise ValueError("Input or accepted primary workbook identity changed")
    code_hash = file_hash(code)
    return {"data_sha256": data_hash, "primary_workbook_sha256": primary_hash,
            "code_sha256": code_hash, "code_bundle_sha256": one_file_bundle(code.relative_to(root).as_posix(), code_hash)}


def records(path, sheet_name):
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        rows = book[sheet_name].iter_rows(values_only=True)
        headers = next(rows, ())
        if not headers or None in headers or len(set(headers)) != len(headers):
            raise ValueError(f"Missing or duplicate headers in {sheet_name}")
        return [dict(zip(headers, row)) for row in rows]
    finally:
        book.close()


def number(value):
    if type(value) not in (float, int) or not math.isfinite(value):
        raise ValueError(f"Expected a finite real number, got {value!r}")
    return value


def model_inputs(root, config):
    path = project_path(root, config["data_paths"][0])
    if config.get("data_identity_mode") == "preprocessing_workbook":
        row, = records(path, "模型输入")
        row["sensitivity_coefficients"] = json.loads(row["sensitivity_coefficients"])
    else:
        row = json.loads(path.read_text(encoding="utf-8"))
    coefficient = number(row["coefficient"])
    grid = [number(value) for value in row["sensitivity_coefficients"]]
    if not coefficient or not grid or 0 in grid or len(grid) != config["iteration_or_time_limit"]:
        raise ValueError("Use all declared nonzero coefficient scenarios and a nonzero baseline coefficient")
    return coefficient, number(row["right_hand_side"]), grid


def analysis_tables(config, coefficient, baseline, grid, values):
    tolerance = number(config["tolerance"])
    if tolerance <= 0 or config["ordinary_experiment_protocol_version"] != "1.0.0":
        raise ValueError("Require positive tolerance and a supported ordinary experiment protocol")
    delta = [number(abs(value - baseline)) for value in values]
    checks = {
        "SENS-Q1-SIGN": ("x", "基准及全部场景的解均为正", values, baseline > 0 and all(value > 0 for value in values)),
        "SENS-Q1-CHANGE": ("|x-x0|", f"至少一个场景 |x-x0| > {tolerance:.17g}", delta, max(delta) > tolerance),
    }
    plans = config["ordinary_experiments"]
    if len(plans) != len(checks) or {plan["id"] for plan in plans} != set(checks):
        raise ValueError("Experiment declarations must match the implemented parameter checks")
    design = [["风险来源", "分析问题", "方法", "指标", "通过标准", "检验ID"]]
    detail = [["参数", "基准值", "变化值", "结果指标", "检验ID", "观测状态"]]
    summary = [["核心结论", "分析方法", "稳定范围", "是否保持", "检验ID", "证据工作表", "主张处置"]]
    domain = f"a in [{min(grid):.17g}, {max(grid):.17g}]"
    for plan in plans:
        test_id = plan["id"]
        if plan["method"] != "parameter_sensitivity":
            raise ValueError("The experiment must name the implemented parameter sensitivity method")
        metric, criterion, observations, kept = checks[test_id]
        design.append(["系数变化", plan["target"], "参数敏感性", metric, criterion, test_id])
        detail.extend(["a", coefficient, a, value, test_id, "completed"] for a, value in zip(grid, observations))
        summary.append([plan["claim"], "参数敏感性", domain, kept, test_id, "参数敏感性", "support" if kept else "reject"])
    return {"分析设计": design, "参数敏感性": detail, "结论稳定性汇总": summary}


def make_receipt(config, identity, elapsed, count):
    receipt = {key: config[key] for key in ("problem_name", "stage", "solver_backend", "solver", "random_seed",
                                            "tolerance", "iteration_or_time_limit", "ordinary_experiment_protocol_version")}
    receipt.update(identity, run_receipt_version=config["run_receipt_protocol_version"], execution_owner="user",
                   execution_profile="full_fidelity", solver_version=platform.python_version(),
                   actual_stop_reason="all_scenarios_completed", repetitions_or_scenarios=count,
                   grid_or_time_range="all declared inputs", fallback_used=False, platform=platform.platform(),
                   elapsed_seconds=elapsed)
    for key in ("allow_reduced_data", "allow_coarser_grid", "allow_shorter_horizon", "allow_fewer_repetitions",
                "allow_relaxed_tolerance", "allow_silent_solver_fallback"):
        receipt[key] = False
    return receipt


def main():
    config = RUN_CONFIG
    code = Path(__file__).resolve()
    root = code.parents[1]
    if config["solver"] != "analytic_parameter_sweep":
        raise ValueError("Instantiate the actual analytic solver")
    started = time.perf_counter()
    identity = observe(root, code, config)
    primary = project_path(root, config["primary_workbook"])
    output = project_path(root, config["expected_workbook"])
    if (output != code.parent / f"{config['problem_name']}结果深化分析.xlsx"
            or output in (primary, project_path(root, config["data_paths"][0]))):
        raise ValueError("Use the analysis workbook's own path in the question folder")
    random.seed(config["random_seed"])
    matches = [row["数值"] for row in records(primary, "核心指标") if row["指标"] == "解"]
    if len(matches) != 1:
        raise ValueError("The accepted primary workbook must contain exactly one solution")
    baseline = number(matches[0])
    coefficient, rhs, grid = model_inputs(root, config)
    values = [number(rhs / a) for a in grid]
    tables = analysis_tables(config, coefficient, baseline, grid, values)
    receipt = make_receipt(config, identity, time.perf_counter() - started, len(grid))
    tables["运行配置"] = [["项目", "值"], *receipt.items()]
    book = openpyxl.Workbook()
    book.remove(book.active)
    with tempfile.NamedTemporaryFile(dir=output.parent, suffix=".xlsx", delete=False) as staging:
        temporary = Path(staging.name)
    try:
        for name, rows in tables.items():
            sheet = book.create_sheet(name)
            for row in rows:
                sheet.append(row)
        book.save(temporary)
        if observe(root, code, config) != identity:
            raise ValueError("Source, inputs or accepted primary workbook changed during analysis")
        temporary.replace(output)
    finally:
        book.close()
        temporary.unlink(missing_ok=True)
    return output


if __name__ == "__main__":
    main()
