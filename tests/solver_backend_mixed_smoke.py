"""Real mixed-backend smoke orchestration; all results come from executing code.

The MATLAB step runs between prepare and verify. Python is only the preparation
and acceptance client for MATLAB, never its numerical fallback.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import shutil
import subprocess
import sys

import openpyxl
import yaml

from test_solver_backend_end_to_end import (
    ROOT, QUESTION, CONFIG, file_hash, load_module, prepare_analysis,
    reference_digest, save_state, result_io,
)


def accept(root: Path, question: str, backend: str, expected: float) -> None:
    receipt = load_module("mixed_smoke_receipt", "scripts/validate_user_execution.py")
    state = yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8"))
    workbook = root / f"{question}求解" / f"{question}求解结果.xlsx"
    result_io.validate_workbook_file(workbook, "solution", capabilities={"requires_equilibrium_residual": True})
    config, issues = receipt.configuration_map(workbook)
    assert issues == [], issues
    assert config["solver_backend"] == backend and config["run_receipt_version"] == "1.1.0"
    issues = receipt.validate_one(root, workbook, state, True)
    assert issues == [], issues
    book = openpyxl.load_workbook(workbook, data_only=True)
    try:
        values = dict(book["核心指标"].iter_rows(min_row=2, values_only=True))
        assert values["解"] == expected and values["绝对方程残差"] <= 1e-10
    finally:
        book.close()
    save_state(root, state)


def register(root: Path, question: str, code: Path, backend: str, paths: list[str]) -> None:
    path = root / "state/project_state.yaml"
    state = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {
        "project": {"competition": "test", "problem": "synthetic", "current_phase": "solve_validate"},
        "preprocessing": {"decision": "not_needed", "status": "not_applicable", "quality_status": "not_applicable"},
        "subproblems": {},
    }
    key = "Q1" if question == "问题一" else "Q2"
    relative = code.relative_to(root).as_posix()
    state["subproblems"][key] = {
        "status": "designed", "selected_model": "a*x=b", "capabilities": {"requires_equilibrium_residual": True},
        "code": relative, "primary_code_sha256": file_hash(code), "data_hash": reference_digest(root, paths),
        "result_quality_status": "pending", "result_analysis_status": "pending",
        "primary_execution_status": "awaiting_user_execution",
        "solver_execution": {"primary": {"backend": backend, "selection_reason": "Real mixed-backend synthetic smoke",
                                           "bundle_sha256": reference_digest(root, [relative])}},
    }
    save_state(root, state)


def python_primary(root: Path, question: str, upstream: bool) -> None:
    paths = [f"{QUESTION}/问题一求解结果.xlsx"] if upstream else ["input.json"]
    folder = root / f"{question}求解"
    folder.mkdir(parents=True, exist_ok=True)
    config = dict(stage="primary", problem_name=question, solver_backend="python", data_paths=paths,
                  data_sha256=reference_digest(root, paths), solver="scalar_division", random_seed=2026,
                  tolerance=1e-10, iteration_or_time_limit="direct", expected_workbook=f"{folder.name}/{question}求解结果.xlsx",
                  run_receipt_protocol_version="1.1.0", primary_quality_protocol_version="1.0.0",
                  code_dependencies=[], input_mode="upstream" if upstream else "json")
    source = (ROOT / "tests/fixtures/solver_backends/python_primary.py").read_text(encoding="utf-8")
    source = source.replace("RUN_CONFIG = {}", "RUN_CONFIG = " + repr(config), 1)
    ast.parse(source)
    code = folder / f"{question}求解.py"
    code.write_text(source, encoding="utf-8", newline="\n")
    (root / "requirements.txt").write_text("openpyxl>=3.1\n", encoding="utf-8")
    register(root, question, code, "python", paths)
    process = subprocess.run([sys.executable, str(code)], cwd=root, capture_output=True, text=True, check=True)
    report = json.loads(process.stdout)
    assert report["actual_python_execution"] and report["status"] == "passed"
    (root / f"{question}_python_report.json").write_text(json.dumps(report), encoding="utf-8")
    accept(root, question, "python", 1.5 if upstream else 3)


def matlab_downstream(root: Path) -> None:
    source = (ROOT / "templates/code/matlab/q1_solver.m").read_text(encoding="utf-8")
    source = source.replace("q1_solver()", "q2_solver()", 1)
    match = CONFIG.search(source)
    config = json.loads(match.group(1))
    paths = ["input.json", f"{QUESTION}/问题一求解结果.xlsx"]
    config.update(problem_name="问题二", data_paths=paths, data_sha256=reference_digest(root, paths),
                  expected_workbook="问题二求解/问题二求解结果.xlsx")
    literal = json.dumps(config, ensure_ascii=False, separators=(",", ":"))
    source = source[:match.start(1)] + literal + source[match.end(1):]
    needle = "validateattributes(input.coefficient,"
    native_read = '''upstream = readcell(project_path(root, RUN_CONFIG.data_paths{2}), 'Sheet', '核心指标');
row = find(string(upstream(:, 1)) == "解");
assert(isscalar(row), 'HSK:Upstream', 'One upstream accepted solution is required.');
input.right_hand_side = upstream{row, 2};
'''
    source = source.replace(needle, native_read + needle, 1)
    folder = root / "问题二求解"
    folder.mkdir(exist_ok=True)
    code = folder / "q2_solver.m"
    code.write_text(source, encoding="utf-8", newline="\n")
    register(root, "问题二", code, "matlab", paths)


def prepare(source_root: Path, project: Path) -> None:
    if project.exists():
        raise ValueError("Mixed smoke requires a fresh project directory.")
    source_state = yaml.safe_load((source_root / "state/project_state.yaml").read_text(encoding="utf-8"))
    assert source_state["subproblems"]["Q1"]["primary_execution_status"] == "accepted"
    matlab_report = json.loads((source_root / "primary_matlab_report.json").read_text(encoding="utf-8"))
    assert matlab_report["actual_matlab_execution"] and matlab_report["status"] == "passed"
    forward = project / "matlab-to-python"
    forward.mkdir(parents=True)
    shutil.copytree(source_root / QUESTION, forward / QUESTION)
    shutil.copyfile(source_root / "input.json", forward / "input.json")
    save_state(forward, source_state)
    python_primary(forward, "问题二", True)
    reverse = project / "python-to-matlab"
    reverse.mkdir()
    shutil.copyfile(source_root / "input.json", reverse / "input.json")
    python_primary(reverse, "问题一", False)
    prepare_analysis(reverse)
    matlab_downstream(reverse)
    (project / "synthetic_fixture.json").write_text(json.dumps({
        "fixture": "mixed_solver_native_v1", "source_matlab_sha256": file_hash(source_root / QUESTION / "问题一求解结果.xlsx"),
        "purpose": "repository_test"}), encoding="utf-8")


def verify(project: Path) -> None:
    report = json.loads((project / "mixed_matlab_report.json").read_text(encoding="utf-8"))
    assert report["actual_matlab_execution"] and report["status"] == "passed"
    accept(project / "matlab-to-python", "问题二", "python", 1.5)
    reverse = project / "python-to-matlab"
    accept(reverse, "问题一", "python", 3)
    accept(reverse, "问题二", "matlab", 1.5)
    receipt = load_module("mixed_analysis_receipt", "scripts/validate_user_execution.py")
    state = yaml.safe_load((reverse / "state/project_state.yaml").read_text(encoding="utf-8"))
    workbook = reverse / QUESTION / "问题一结果深化分析.xlsx"
    result_io.validate_workbook_file(workbook, "result_analysis", capabilities={})
    issues = receipt.validate_one(reverse, workbook, state, True)
    assert issues == [], issues
    book = openpyxl.load_workbook(workbook, data_only=True)
    try:
        assert [row[3] for row in book["参数敏感性"].iter_rows(min_row=2, values_only=True)] == [4, 3, 2]
    finally:
        book.close()
    save_state(reverse, state)
    (project / "mixed_acceptance_report.json").write_text(json.dumps({"status": "passed", "cases": [
        "Q1 MATLAB accepted primary -> Q2 real Python primary = 1.5",
        "Q1 Python accepted primary -> Q2 real MATLAB primary = 1.5",
        "Q1 Python accepted primary -> Q1 real MATLAB analysis = [4,3,2]"],
        "common_receipt_version": "1.1.0", "matlab_release": report["matlab_release"]}), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "verify"])
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    if args.action == "prepare":
        assert args.source is not None
        prepare(args.source.resolve(), args.project.resolve())
    else:
        verify(args.project.resolve())
