"""Prepare synthetic fixtures and verify outputs of an actual MATLAB process.

Ordinary unittest discovery also runs the Python analysis template in an isolated
project. Native-output tests read a completed MATLAB run from HSK_MATLAB_SOLVER_OUTPUT.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from numbers import Real
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

import openpyxl
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
from templates.code.hsk_pipeline import result_io
QUESTION = "问题一求解"
NEGATIVE_ANALYSIS = Path("negative/ordinary-claim")
CONFIG = re.compile(r"RUN_CONFIG = jsondecode\('([^\n]*)'\);")
R2_FIXTURE = ROOT / "tests/fixtures/r2_answer_delivery"


def load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reference_digest(root: Path, paths: list[str]) -> str:
    """Independent protocol reference used to compare MATLAB's byte-level output."""
    digest = hashlib.sha256()
    for relative in sorted(paths, key=lambda item: item.encode("utf-8")):
        digest.update(relative.encode("utf-8") + b"\0")
        digest.update(bytes.fromhex(file_hash(root / relative)))
    return digest.hexdigest()


def check_ordinary_experiments(book, expected, kept):
    def records(sheet):
        rows = book[sheet].iter_rows(values_only=True)
        headers = next(rows)
        return [dict(zip(headers, row)) for row in rows]

    design = {row["检验ID"]: row for row in records("分析设计")}
    summary = {row["检验ID"]: row for row in records("结论稳定性汇总")}
    detail = records("参数敏感性")
    assert set(design) == set(summary) == set(expected) == {row["检验ID"] for row in detail}
    observed = {}
    for identifier, values in expected.items():
        rows = [row for row in detail if row["检验ID"] == identifier]
        observed[identifier] = [row["结果指标"] for row in rows]
        assert observed[identifier] == values
        assert all(row["观测状态"] == "completed" for row in rows)
        claim = summary[identifier]
        assert claim["是否保持"] == kept[identifier]
        assert claim["主张处置"] == ("support" if kept[identifier] else "reject")
        assert claim["证据工作表"] == "参数敏感性"
    return observed


def verify_r2_answer_workbook(path: Path, scenario: str, *, submission_formats: bool = False) -> None:
    expected = json.loads((R2_FIXTURE / "expected.json").read_text(encoding="utf-8"))[scenario]
    template = json.loads((R2_FIXTURE / "submission_template.json").read_text(encoding="utf-8"))
    book = openpyxl.load_workbook(path, data_only=True)
    try:
        assert {"站点峰值", "执行停止证据", "事件状态", "核心指标"}.issubset(book.sheetnames)
        sheet = book[template["sheet"]]
        rows = list(sheet.iter_rows(values_only=True))
        assert list(rows[0]) == template["columns"], "提交模板列不完整或顺序改变"
        observed = rows[1:]
        expected_rows = expected["peaks"]
        assert len(observed) == len(expected_rows), "必答记录或并列峰时遗漏"
        assert len({row[0] for row in observed}) == len(observed), "答案记录键重复"
        for actual, (station, peak, time) in zip(observed, expected_rows):
            assert actual[0] == f"{scenario}-{station}-{time}", "提交模板行键不匹配"
            assert actual[1] == station, "站点集合或顺序错误"
            for value, target in ((actual[2], peak), (actual[3], time)):
                assert isinstance(value, Real) and not isinstance(value, bool), "必答数值为空或类型错误"
                assert math.isclose(value, target, rel_tol=0, abs_tol=1e-12), "必答数值或峰时错误"
            assert actual[4:] == ("1", "s")
        if scenario == "baseline":
            assert [row[0] for row in observed] == template["baseline_record_keys"]
        if submission_formats:
            for column, number_format in template["number_formats"].items():
                index = template["columns"].index(column) + 1
                assert all(sheet.cell(row, index).number_format == number_format
                           for row in range(2, sheet.max_row + 1)), "提交显示精度不符"
        stop = list(book["执行停止证据"].iter_rows(values_only=True))
        assert stop == [("迭代或样本数", "指标", "数值", "单位"), (4, "末采样时刻", 6, "s")]
        events = list(book["事件状态"].iter_rows(values_only=True))
        assert events == [("站点", "状态", "时刻", "原因"),
                          ("A", "未触发", None, "全部采样值低于阈值"),
                          ("B", "未触发", None, "全部采样值低于阈值")]
        metrics = dict(book["核心指标"].iter_rows(min_row=2, values_only=True))
        assert math.isclose(metrics["全网峰值"], expected["network_peak"], rel_tol=0, abs_tol=1e-12)
    finally:
        book.close()


def instantiate(root: Path, stage: str, **updates) -> Path:
    name = "q1_solver.m" if stage == "primary" else "q1_analysis.m"
    source = (ROOT / "templates/code/matlab" / name).read_text(encoding="utf-8")
    match = CONFIG.search(source)
    assert match is not None
    config = json.loads(match.group(1).replace("''", "'"))
    config.update(updates)
    if "data_sha256" not in updates:
        config["data_sha256"] = reference_digest(root, config["data_paths"])
    literal = json.dumps(config, ensure_ascii=False, separators=(",", ":")).replace("'", "''")
    source = source[:match.start(1)] + literal + source[match.end(1):]
    path = root / QUESTION / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8", newline="\n")
    return path


def stage_state(root: Path, stage: str, code: Path) -> dict:
    return {"bundle_sha256": reference_digest(root, [code.relative_to(root).as_posix()])}


def save_state(root: Path, state: dict) -> None:
    (root / "state").mkdir(exist_ok=True)
    (root / "state/project_state.yaml").write_text(
        yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")


def prepare_approved_primary_quality(root: Path) -> None:
    from tests.test_v900_semantic_identity_binding import framework, identity, structured_question
    from primary_quality_specification import normalize_specification, specification_sha256

    project = root / "approved-primary-quality"
    project.mkdir()
    for filename in ("input.json", "synthetic_fixture.json"):
        shutil.copyfile(root / filename, project / filename)

    payload = identity()
    payload.update(
        research_object="scalar linear equation",
        data_scope=[{"id": "D1", "source": "input.json", "role": "input"}],
        variables=[{"id": "V1", "symbol": "x", "role": "solution", "domain": "real"}],
        parameters=[{"id": "P1", "symbol": "a", "unit": "1"}, {"id": "P2", "symbol": "b", "unit": "1"}],
        assumptions=[{"id": "A1", "statement": "a is finite and nonzero and b is finite"}],
        objective={"expression": "solve a*x=b"},
        constraints=[{"id": "C1", "expression": "a*x=b"}],
        preprocessing_decision="not_needed",
        algorithm_semantics={"model_family": "scalar linear system", "solver_role": "direct"},
    )
    payload["extensions"] = {"primary_quality_specification": {"version": "1.0.0", "items": [{
        "id": "PQ-Q1-01", "metric": "方程残差", "relation": "abs<=", "threshold": 1e-10,
        "threshold_source": "solver_tolerance", "evidence_sheet": "均衡残差", "unit": "1",
    }]}}
    specification = normalize_specification(payload["extensions"]["primary_quality_specification"], "Q1")
    digest = specification_sha256(specification)
    code = instantiate(project, "primary", run_receipt_protocol_version="1.3.0",
                       primary_quality_protocol_version="1.1.0", primary_quality_spec_sha256=digest)
    state = yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8"))
    state["subproblems"]["Q1"].update(
        structured_question(payload), primary_code_sha256=file_hash(code),
        solver_execution={"primary": stage_state(project, "primary", code)},
    )
    (project / "模型论文框架.md").write_text(framework(payload), encoding="utf-8")
    save_state(project, state)


def prepare_execution_scale(root: Path) -> None:
    from execution_scale import normalize_scale_plan, scale_plan_sha256

    approved = root / "approved-primary-quality"
    project = root / "execution-scale"
    project.mkdir()
    for filename in ("input.json", "synthetic_fixture.json", "模型论文框架.md"):
        shutil.copyfile(approved / filename, project / filename)

    approved_code = approved / QUESTION / "q1_solver.m"
    approved_config = json.loads(CONFIG.search(approved_code.read_text(encoding="utf-8")).group(1))
    plan = normalize_scale_plan({"axis": "repetitions", "mode": "exact", "count": 1}, "primary")
    code = instantiate(
        project, "primary", run_receipt_protocol_version="1.4.0", execution_scale_plan=plan,
        execution_scale_plan_sha256=scale_plan_sha256(plan), primary_quality_protocol_version="1.1.0",
        primary_quality_spec_sha256=approved_config["primary_quality_spec_sha256"],
    )
    state = yaml.safe_load((approved / "state/project_state.yaml").read_text(encoding="utf-8"))
    state["subproblems"]["Q1"].update(
        primary_code_sha256=file_hash(code), solver_execution={"primary": stage_state(project, "primary", code)},
    )
    save_state(project, state)


def prepare(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    if (root / QUESTION / "问题一求解结果.xlsx").exists():
        raise ValueError("Use a fresh output directory; existing numerical results are not overwritten by preparation.")
    shutil.copyfile(ROOT / "tests/fixtures/solver_backends/input.json", root / "input.json")
    (root / "synthetic_fixture.json").write_text(
        json.dumps({"fixture": "solver_backend_native_v1", "purpose": "repository_test"}), encoding="utf-8")
    code = instantiate(root, "primary")
    state = {"project": {"competition": "test", "problem": "synthetic", "current_phase": "solve_validate"},
             "preprocessing": {"decision": "not_needed", "status": "not_applicable", "quality_status": "not_applicable"},
             "execution": {"solver_backend": "matlab",
                           "solver_backend_selection_reason": "Synthetic whole-project native workbook integration"},
             "subproblems": {"Q1": {
                 "status": "designed", "selected_model": "a*x=b", "capabilities": {"requires_equilibrium_residual": True},
                 "code": code.relative_to(root).as_posix(), "primary_code_sha256": file_hash(code),
                 "data_hash": reference_digest(root, ["input.json"]), "result_quality_status": "pending",
                 "result_analysis_status": "pending", "primary_execution_status": "awaiting_user_execution",
                 "solver_execution": {"primary": stage_state(root, "primary", code)},
             }}}
    save_state(root, state)
    prepare_approved_primary_quality(root)
    prepare_execution_scale(root)
    writer = (ROOT / "templates/code/matlab/q1_solver.m").read_text(encoding="utf-8")
    writer = writer[writer.index("function write_workbook("):]
    probe = '''function native_writer_probe(filename,mode)
cells = {'记录键','数值','标记'; '0001',1.5,true; '9007199254740993',"",false};
if mode == "duplicate_header", cells{1,2} = '记录键'; end
if mode == "duplicate_key", cells{3,1} = '0001'; end
if mode == "infinite", cells{2,2} = Inf; end
sheets = {'类型往返',cells};
if mode == "duplicate_sheet", sheets = {'Probe',cells;'probe',cells}; end
if mode == "empty_sheet", sheets = {'',cells}; end
write_workbook(filename,sheets);
end

'''
    (root / "native_writer_probe.m").write_text(probe + writer, encoding="utf-8", newline="\n")
    answer_root = root / "r2-answers"
    answer_root.mkdir()
    shutil.copyfile(R2_FIXTURE / "input.json", answer_root / "input.json")
    answer_probe = (R2_FIXTURE / "r2_answer_probe.m").read_text(encoding="utf-8")
    (root / "r2_answer_probe.m").write_text(answer_probe + writer, encoding="utf-8", newline="\n")
    source = (ROOT / "templates/code/matlab/q1_solver.m").read_text(encoding="utf-8")
    hashes = source[source.index("function path = project_path("):source.index("function receipt = make_receipt(")]
    probe = '''function native_hash_probe(root)
root = fullfile(string(root),"hash-probe");
result = files_digest(root,["\ue000.txt";"\U0001f600.txt";"a.txt"]);
fid = fopen(fullfile(root,"digest.txt"),'w');
assert(fid >= 0);
cleanup = onCleanup(@() fclose(fid));
fwrite(fid,result,'char');
end

'''
    (root / "native_hash_probe.m").write_text(probe + hashes, encoding="utf-8", newline="\n")
    (root / "hash-probe").mkdir()
    for name in ("\ue000.txt", "\U0001f600.txt", "a.txt"):
        (root / "hash-probe" / name).write_text(name, encoding="utf-8")
    for case in ("input_hash", "missing_input", "nonfinite_result"):
        destination = root / "negative" / case
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / "input.json", destination / "input.json")
        if case == "nonfinite_result":
            payload = {"coefficient": 1e-308, "right_hand_side": 1e308, "sensitivity_coefficients": [1.5, 2, 3]}
            (destination / "input.json").write_text(json.dumps(payload), encoding="utf-8")
        instantiate(destination, "primary")
        if case == "input_hash":
            with (destination / "input.json").open("a", encoding="utf-8") as handle:
                handle.write(" ")
        elif case == "missing_input":
            (destination / "input.json").unlink()


def prepare_preprocessed(root: Path) -> None:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    fixture = load_module("native_preprocessing_fixture", "tests/test_solver_backend_preprocessing.py")
    state, digest = fixture.prepare_native_preprocessing(root)
    (root / "synthetic_fixture.json").write_text(json.dumps({
        "fixture": "solver_backend_native_v1", "purpose": "repository_test"}), encoding="utf-8")
    (root / "preprocessing_native_fixture.json").write_text(json.dumps({
        "preprocessing": state["preprocessing"], "workbook_sha256": digest,
        "upstream_is_synthetic_receipt_fixture": True, "python_preprocessing_executed": False,
    }, ensure_ascii=False), encoding="utf-8")
    code = instantiate(root, "primary", data_paths=["数据预处理/数据预处理结果.xlsx"],
                       data_sha256=digest, data_identity_mode="preprocessing_workbook")
    state["project"]["current_phase"] = "solve_validate"
    state["execution"] = {"solver_backend": "matlab",
                          "solver_backend_selection_reason": "Synthetic whole-project native workbook integration"}
    state["subproblems"]["Q1"].update(
        selected_model="a*x=b", capabilities={"requires_equilibrium_residual": True},
        code=code.relative_to(root).as_posix(), primary_code_sha256=file_hash(code), data_hash=digest,
        result_quality_status="pending", result_analysis_status="pending",
        primary_execution_status="awaiting_user_execution",
        solver_execution={"primary": stage_state(root, "primary", code)})
    save_state(root, state)


def verify(root: Path, stage: str) -> None:
    runtime_report = json.loads((root / f"{stage}_matlab_report.json").read_text(encoding="utf-8"))
    assert runtime_report["actual_matlab_execution"] is True and runtime_report["status"] == "passed"
    assert runtime_report["matlab_release"]
    receipt = load_module("native_smoke_receipt", "scripts/validate_user_execution.py")
    io = result_io
    state = yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8"))
    entry = state["subproblems"]["Q1"]
    workbook = root / QUESTION / ("问题一求解结果.xlsx" if stage == "primary" else "问题一结果深化分析.xlsx")
    code = root / entry["code" if stage == "primary" else "result_analysis_code"]
    config, issues = receipt.configuration_map(workbook)
    if issues:
        raise AssertionError(issues)
    assert config["solver_backend"] == "matlab"
    assert config["run_receipt_version"] == "1.1.0"
    assert config["code_sha256"] == file_hash(code)
    assert config["code_bundle_sha256"] == reference_digest(root, [code.relative_to(root).as_posix()])
    io.validate_workbook_file(workbook, "solution" if stage == "primary" else "result_analysis",
                              capabilities=entry["capabilities"] if stage == "primary" else {})
    issues = receipt.validate_one(root, workbook, state, True)
    if issues:
        raise AssertionError(issues)
    book = openpyxl.load_workbook(workbook, data_only=True)
    try:
        if stage == "primary":
            values = {row[0]: row[1] for row in book["核心指标"].iter_rows(min_row=2, values_only=True)}
            assert abs(values["解"] - 3) < 1e-12
            assert values["绝对方程残差"] <= 1e-10
            assert book["状态明细"]["A2"].value == "0001"
        else:
            assert config["ordinary_experiment_protocol_version"] == "1.0.0"
            check_ordinary_experiments(book, {"SENS-Q1-SIGN": [4, 3, 2], "SENS-Q1-CHANGE": [1, 0, 1]},
                                       {"SENS-Q1-SIGN": True, "SENS-Q1-CHANGE": True})
    finally:
        book.close()
    if stage == "primary" and runtime_report.get("type_probe") == "text_keys_logicals_missing_rows_and_rejections_passed":
        digest_root = root / "hash-probe"
        assert (digest_root / "digest.txt").read_text(encoding="utf-8") == reference_digest(
            digest_root, ["\ue000.txt", "\U0001f600.txt", "a.txt"])
        book = openpyxl.load_workbook(root / "type-probe" / QUESTION / "问题一求解结果.xlsx", data_only=True)
        try:
            rows = list(book["类型往返"].iter_rows(values_only=True))
            assert rows[1] == ("0001", 1.5, True)
            assert rows[2] == ("9007199254740993", None, False)
        finally:
            book.close()
    if stage == "primary" and not (root / "preprocessing_native_fixture.json").exists():
        assert runtime_report["answer_delivery_probe"] == "baseline_ties_precision_passed"
        for scenario in ("baseline", "ties", "precision"):
            answers = root / "r2-answers" / scenario / QUESTION / "问题一求解结果.xlsx"
            result_io.validate_workbook_file(answers, "solution")
            verify_r2_answer_workbook(answers, scenario)
    if (root / "preprocessing_native_fixture.json").exists():
        baseline = json.loads((root / "preprocessing_native_fixture.json").read_text(encoding="utf-8"))
        assert state["preprocessing"] == baseline["preprocessing"]
        assert config["data_sha256"] == baseline["workbook_sha256"]
        assert file_hash(root / "数据预处理/数据预处理结果.xlsx") == baseline["workbook_sha256"]
        assert runtime_report["preprocessing_workbook_unchanged"]
    save_state(root, state)
    if stage == "primary" and (root / "approved-primary-quality").is_dir():
        verify_approved_primary_quality(root, runtime_report, receipt)
    if stage == "primary" and (root / "execution-scale").is_dir():
        verify_execution_scale(root, runtime_report, receipt)
    if stage == "analysis":
        # Exercise read-only migration preflight against the actual native receipts.
        # This is not execution/confirmation of a backend migration.
        inspector = load_module("native_migration_preview", "scripts/project_solver_backend.py")
        before = {p.relative_to(root).as_posix(): file_hash(p) for p in root.rglob("*") if p.is_file()}
        same = inspector.preview_migration(root, target_backend="matlab", reason="Native same-backend retention check")
        assert same["status"] == "ready_for_review", same["issues"]
        assert all(row["evidence_status"] == "accepted_rechecked" for row in same["stages"]), same["stages"]
        assert same["effects"]["retired_stages"] == [], same["effects"]
        other = inspector.preview_migration(root, target_backend="python", reason="Native retirement proposal check")
        assert other["status"] == "ready_for_review", other["issues"]
        assert {(row["question"], row["stage"]) for row in other["effects"]["retired_stages"]} == {
            ("Q1", "primary"), ("Q1", "analysis")}, other["effects"]
        assert not other["migration_authorized"] and not other["write_supported"]
        assert {p.relative_to(root).as_posix(): file_hash(p) for p in root.rglob("*") if p.is_file()} == before


def verify_approved_primary_quality(root: Path, runtime_report: dict, receipt) -> None:
    project = root / "approved-primary-quality"
    workbook = project / QUESTION / "问题一求解结果.xlsx"
    assert Path(runtime_report["approved_primary_quality_workbook"]).resolve() == workbook.resolve()
    state = yaml.safe_load((project / "state/project_state.yaml").read_text(encoding="utf-8"))
    code = project / QUESTION / "q1_solver.m"
    delivered = json.loads(CONFIG.search(code.read_text(encoding="utf-8")).group(1))
    config, issues = receipt.configuration_map(workbook)
    assert not issues, issues
    assert config["run_receipt_version"] == "1.3.0"
    assert config["primary_quality_protocol_version"] == "1.1.0"
    assert config["primary_quality_spec_sha256"] == delivered["primary_quality_spec_sha256"]
    assert json.loads(config["data_paths"]) == delivered["data_paths"]
    assert config["data_identity_mode"] == delivered.get("data_identity_mode", "combined")
    book = openpyxl.load_workbook(workbook, data_only=True)
    try:
        assert book["主结果质量门"]["J1"].value == "单位"
        assert book["主结果质量门"]["J2"].value == "1"
        assert book["均衡残差"]["E1"].value == "单位"
        assert book["均衡残差"]["E2"].value == "1"
    finally:
        book.close()
    result_io.validate_workbook_file(
        workbook, "solution", capabilities=state["subproblems"]["Q1"]["capabilities"],
    )
    issues = receipt.validate_one(project, workbook, state, True)
    assert not issues, issues
    assert state["subproblems"]["Q1"]["primary_execution_status"] == "accepted"
    save_state(project, state)


def verify_execution_scale(root: Path, runtime_report: dict, receipt) -> None:
    project = root / "execution-scale"
    workbook = project / QUESTION / "问题一求解结果.xlsx"
    assert Path(runtime_report["execution_scale_workbook"]).resolve() == workbook.resolve()
    code = project / QUESTION / "q1_solver.m"
    delivered = json.loads(CONFIG.search(code.read_text(encoding="utf-8")).group(1))
    config, issues = receipt.configuration_map(workbook)
    assert not issues, issues
    assert config["run_receipt_version"] == "1.4.0"
    assert config["execution_scale_plan_sha256"] == delivered["execution_scale_plan_sha256"]
    assert config["primary_quality_spec_sha256"] == delivered["primary_quality_spec_sha256"]
    assert json.loads(config["data_paths"]) == delivered["data_paths"]
    assert config["data_identity_mode"] == delivered.get("data_identity_mode", "combined")
    book = openpyxl.load_workbook(workbook, data_only=True)
    try:
        rows = list(book["重复试验结果"].values)
        assert rows == [("重复编号", "指标", "数值"), ("1", "解", 3)]
        assert config["actual_scale_count"] == len(rows) - 1
    finally:
        book.close()
    state = yaml.safe_load((project / "state/project_state.yaml").read_text(encoding="utf-8"))
    result_io.validate_workbook_file(
        workbook, "solution", capabilities=state["subproblems"]["Q1"]["capabilities"],
    )
    issues = receipt.validate_one(project, workbook, state, True)
    assert not issues, issues
    assert state["subproblems"]["Q1"]["primary_execution_status"] == "accepted"
    save_state(project, state)


def prepare_analysis(root: Path, *, tolerance: float | None = None) -> None:
    state = yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8"))
    entry = state["subproblems"]["Q1"]
    assert entry["primary_execution_status"] == "accepted"
    primary = root / QUESTION / "问题一求解结果.xlsx"
    updates = {"primary_workbook_sha256": file_hash(primary)}
    if tolerance is not None:
        updates["tolerance"] = tolerance
    if state["preprocessing"]["decision"] == "project_level":
        updates.update(data_identity_mode="preprocessing_workbook", data_paths=["数据预处理/数据预处理结果.xlsx"],
                       data_sha256=file_hash(root / "数据预处理/数据预处理结果.xlsx"))
    code = instantiate(root, "analysis", **updates)
    entry.update(result_analysis_requirement_reason="Test the declared coefficient range", analysis_methods=["参数敏感性"],
                 result_analysis_code=code.relative_to(root).as_posix(), analysis_code_sha256=file_hash(code),
                 analysis_execution_status="awaiting_user_execution")
    entry["solver_execution"]["analysis"] = stage_state(root, "analysis", code)
    save_state(root, state)


def require_synthetic_fixture(root: Path) -> None:
    marker = json.loads((root / "synthetic_fixture.json").read_text(encoding="utf-8"))
    assert marker["fixture"] == "solver_backend_native_v1" and marker["purpose"] == "repository_test"


def prepare_negative_analysis(root: Path) -> None:
    require_synthetic_fixture(root)
    project = root / NEGATIVE_ANALYSIS
    for name in ("synthetic_fixture.json", "input.json", "state/project_state.yaml",
                 f"{QUESTION}/q1_solver.m", f"{QUESTION}/问题一求解结果.xlsx"):
        target = project / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / name, target)
    # Maximum observed deviation is 1. Raise the predeclared threshold to 2.
    prepare_analysis(project, tolerance=2)


def run_negative_analysis(root: Path, matlab_command: str) -> None:
    project = root / NEGATIVE_ANALYSIS
    require_synthetic_fixture(project)
    folder = project / QUESTION
    primary = folder / "问题一求解结果.xlsx"
    baseline_hash = file_hash(root / QUESTION / primary.name)
    assert file_hash(primary) == baseline_hash
    code = folder / "q1_analysis.m"
    quote = str(code.parent).replace("'", "''")
    # MATLAB resolves the current directory first. Launch beside the delivered file in a fresh process.
    expression = (f"cd('{quote}'); a=which('q1_analysis'); b=fullfile(pwd,'q1_analysis.m'); "
                  "assert(strcmp(a,b) || (ispc && strcmpi(a,b))); q1_analysis();")
    process = subprocess.run([matlab_command, "-batch", expression], capture_output=True, encoding="utf-8",
                             errors="replace", timeout=300)
    (project / "analysis_native.log").write_text(process.stdout + process.stderr, encoding="utf-8")
    assert process.returncode == 0, process.stdout + process.stderr
    assert file_hash(primary) == file_hash(root / QUESTION / primary.name) == baseline_hash
    workbook = folder / "问题一结果深化分析.xlsx"
    state = yaml.safe_load((project / "state/project_state.yaml").read_text(encoding="utf-8"))
    entry = state["subproblems"]["Q1"]
    # The validator distinguishes a completed counterexample from an invalid receipt.
    receipt = load_module("native_negative_receipt", "scripts/validate_user_execution.py")
    issues = receipt.validate_one(project, workbook, state, True)
    assert issues == ["存在核心结论未保持"], issues
    assert entry["analysis_execution_status"] == entry["result_analysis_status"] == "redo_required"
    assert entry["primary_execution_status"] == "accepted"
    with workbook.open("rb") as stream:
        book = openpyxl.load_workbook(stream, read_only=True, data_only=True)
        try:
            observed = check_ordinary_experiments(book, {"SENS-Q1-SIGN": [4, 3, 2], "SENS-Q1-CHANGE": [1, 0, 1]},
                                                  {"SENS-Q1-SIGN": True, "SENS-Q1-CHANGE": False})
            assert type(observed["SENS-Q1-CHANGE"][1]) in (int, float)
        finally:
            book.close()
    save_state(project, state)


def deliver(root: Path, stage: str, matlab_command: str) -> None:
    require_synthetic_fixture(root)
    state = yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8"))
    entry = state["subproblems"]["Q1"]
    assert entry.get(f"{stage}_execution_status") != "accepted"
    fields = ("code", "primary_code_sha256") if stage == "primary" else ("result_analysis_code", "analysis_code_sha256")
    for field in fields:
        entry.pop(field, None)
    selection = entry["solver_execution"][stage]
    selection.pop("bundle_sha256", None)
    selection.pop("validated_bundle_sha256", None)
    entry[f"{stage}_execution_status"] = "pending"
    save_state(root, state)
    script = f"{QUESTION}/q1_{'solver' if stage == 'primary' else 'analysis'}.m"
    process = subprocess.run([sys.executable, str(ROOT / "scripts/validate_code_delivery.py"), str(root),
                              "--script", script, "--stage", stage, "--write", "--strict",
                              "--matlab-command", matlab_command], capture_output=True, encoding="utf-8",
                             env={**os.environ, "PYTHONUTF8": "1"})
    (root / f"{stage}_delivery_report.yaml").write_text(process.stdout + process.stderr, encoding="utf-8")
    assert process.returncode == 0, process.stdout + process.stderr
    report = yaml.safe_load(process.stdout)
    assert report["status"] == "passed" and report["task_code_executed"] is False
    assert report["code_quality_metrics"][script]["native_analysis_status"] == "passed"
    state = yaml.safe_load((root / "state/project_state.yaml").read_text(encoding="utf-8"))
    entry = state["subproblems"]["Q1"]
    assert entry[f"{stage}_execution_status"] == "awaiting_user_execution"
    assert entry["solver_execution"][stage]["bundle_sha256"] == reference_digest(root, [script])
    assert "validated_bundle_sha256" not in entry["solver_execution"][stage]
    if stage == "analysis" and (root / NEGATIVE_ANALYSIS).is_dir():
        deliver(root / NEGATIVE_ANALYSIS, stage, matlab_command)
    if stage == "primary":
        for profile in ("approved-primary-quality", "execution-scale"):
            if (root / profile).is_dir():
                deliver(root / profile, stage, matlab_command)


class SolverBackendFixtureTests(unittest.TestCase):
    def test_ordinary_python_analysis_runs_with_statically_bound_matlab_equivalent_plan(self):
        from validate_user_execution import analysis_passed
        import stage_code

        template = ROOT / "templates/code/starter/q1_analysis.py"
        matlab = ROOT / "templates/code/matlab/q1_analysis.m"
        expected_plan = stage_code.parse_stage_config(matlab, "matlab")[1]["ordinary_experiments"]
        for rhs in (6, 0):
            with self.subTest(right_hand_side=rhs), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                folder = root / QUESTION
                folder.mkdir()
                primary = folder / "问题一求解结果.xlsx"
                book = openpyxl.Workbook()
                book.active.title = "核心指标"
                book.active.append(["指标", "数值"])
                book.active.append(["解", rhs / 2])
                book.save(primary)
                book.close()
                before = primary.read_bytes()
                (root / "input.json").write_text(json.dumps({
                    "coefficient": 2, "right_hand_side": rhs, "sensitivity_coefficients": [1.5, 2, 3],
                }), encoding="utf-8")
                script = folder / "问题一结果深化分析.py"
                source = template.read_text(encoding="utf-8").replace("__ACCEPTED_PRIMARY_SHA256__", file_hash(primary))
                script.write_text(source.replace("__DATA_SHA256__", reference_digest(root, ["input.json"])),
                                  encoding="utf-8", newline="\n")
                config = stage_code.parse_stage_config(script, "python")[1]
                self.assertEqual(config["ordinary_experiments"], expected_plan)
                process = subprocess.run([sys.executable, str(script)], cwd=root, capture_output=True,
                                         encoding="utf-8", env={**os.environ, "PYTHONUTF8": "1"})
                self.assertEqual(process.returncode, 0, process.stderr)
                workbook = root / config["expected_workbook"]
                result_io.validate_workbook_file(workbook, "result_analysis", analysis_methods=["参数敏感性"],
                                                 ordinary_experiments=expected_plan)
                observed_status = analysis_passed(workbook, ordinary_experiments=expected_plan)
                self.assertEqual(observed_status[:2], (True, "passed") if rhs else (False, "redo_required"))
                with workbook.open("rb") as stream:
                    book = openpyxl.load_workbook(stream, read_only=True, data_only=True)
                    try:
                        check_ordinary_experiments(book, {"SENS-Q1-SIGN": [4, 3, 2] if rhs else [0, 0, 0],
                                                         "SENS-Q1-CHANGE": [1, 0, 1] if rhs else [0, 0, 0]},
                                                   {"SENS-Q1-SIGN": bool(rhs), "SENS-Q1-CHANGE": bool(rhs)})
                        receipt = dict(list(book["运行配置"].values)[1:])
                        self.assertEqual(receipt["ordinary_experiment_protocol_version"], "1.0.0")
                        self.assertEqual(receipt["code_sha256"], file_hash(script))
                        self.assertEqual(receipt["code_bundle_sha256"], reference_digest(root, [script.relative_to(root).as_posix()]))
                        self.assertEqual(receipt["primary_workbook_sha256"], file_hash(primary))
                    finally:
                        book.close()
                self.assertEqual(primary.read_bytes(), before)

    def test_instantiation_binds_real_input_bytes_without_running_matlab(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            prepare(root)
            source = (root / QUESTION / "q1_solver.m").read_text(encoding="utf-8")
            config = json.loads(CONFIG.search(source).group(1))
            self.assertEqual(config["data_sha256"], reference_digest(root, ["input.json"]))
            self.assertEqual(config["solver_backend"], "matlab")
            self.assertFalse(list(root.rglob("*.xlsx")))
            self.assertEqual((root / "r2-answers/input.json").read_bytes(), (R2_FIXTURE / "input.json").read_bytes())
            writer = (ROOT / "templates/code/matlab/q1_solver.m").read_text(encoding="utf-8")
            self.assertTrue((root / "r2_answer_probe.m").read_text(encoding="utf-8").endswith(
                writer[writer.index("function write_workbook("):]))
            self.assertTrue((root / "negative/nonfinite_result" / QUESTION / "q1_solver.m").is_file())
            approved_code = root / "approved-primary-quality" / QUESTION / "q1_solver.m"
            approved = json.loads(CONFIG.search(approved_code.read_text(encoding="utf-8")).group(1))
            self.assertEqual(approved["run_receipt_protocol_version"], "1.3.0")
            self.assertEqual(approved["primary_quality_protocol_version"], "1.1.0")
            self.assertRegex(approved["primary_quality_spec_sha256"], r"^[0-9a-f]{64}$")
            scale_source = root / "execution-scale" / QUESTION / "q1_solver.m"
            scale = json.loads(CONFIG.search(scale_source.read_text(encoding="utf-8")).group(1))
            self.assertEqual(scale["run_receipt_protocol_version"], "1.4.0")
            self.assertEqual(scale["execution_scale_plan"], {"axis": "repetitions", "count": 1, "mode": "exact"})
            self.assertRegex(scale["execution_scale_plan_sha256"], r"^[0-9a-f]{64}$")

    def test_analysis_template_does_not_call_primary_or_write_its_workbook(self):
        source = (ROOT / "templates/code/matlab/q1_analysis.m").read_text(encoding="utf-8")
        self.assertNotIn("q1_solver(", source)
        self.assertIn("primary_workbook_sha256", source)
        self.assertIn("workbook ~= primary", source)


@unittest.skipUnless(os.environ.get("HSK_MATLAB_SOLVER_OUTPUT"), "real MATLAB outputs were not supplied")
class NativeMatlabOutputTests(unittest.TestCase):
    def test_native_workbooks_pass_common_python_acceptance(self):
        root = Path(os.environ["HSK_MATLAB_SOLVER_OUTPUT"])
        verify(root, "primary")
        verify(root, "analysis")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in {"prepare", "prepare-preprocessed", "verify-primary", "prepare-analysis", "verify-analysis", "deliver-primary", "deliver-analysis"}:
        parser = argparse.ArgumentParser()
        parser.add_argument("action")
        parser.add_argument("--project", type=Path, required=True)
        parser.add_argument("--matlab-command", default=os.environ.get("HSK_MATLAB_CI_COMMAND", "matlab"))
        args = parser.parse_args()
        if args.action == "prepare":
            prepare(args.project.resolve())
        elif args.action == "prepare-preprocessed":
            prepare_preprocessed(args.project.resolve())
        elif args.action == "prepare-analysis":
            if not (args.project / "preprocessing_native_fixture.json").exists():
                prepare_negative_analysis(args.project.resolve())
            prepare_analysis(args.project.resolve())
        elif args.action.startswith("deliver-"):
            deliver(args.project.resolve(), args.action.removeprefix("deliver-"), args.matlab_command)
        else:
            if args.action == "verify-analysis" and not (args.project / "preprocessing_native_fixture.json").exists():
                run_negative_analysis(args.project.resolve(), args.matlab_command)
            verify(args.project.resolve(), args.action.removeprefix("verify-"))
    else:
        unittest.main()
