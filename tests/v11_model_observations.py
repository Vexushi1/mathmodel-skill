"""Synthetic model/receipt observations for the v11 maintenance baseline."""

from copy import deepcopy
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

import openpyxl
import yaml

from tests import test_solver_backend_preprocessing as preprocessing_fixture
from tests import test_user_execution_contract as execution_fixture
from tests import test_v900_semantic_governance as semantic_fixture
from primary_quality_specification import normalize_specification
from validate_model_approval import validate_state
from validate_numerical_evidence import validate_primary_numerical_evidence
from validate_user_execution import PREPROCESSING_EVIDENCE_SHEETS


def downstream_approval(edge_registered, change_objective, *, independent=False):
    """Can Q2 still consume its approval after the change? All state is synthetic."""
    with TemporaryDirectory() as folder:
        root = Path(folder)
        state = yaml.safe_load((semantic_fixture.ROOT / "state/project_state.example.yaml").read_bytes())
        state["requirements"] = {"total": 2, "completed": [], "pending": ["Q1", "Q2"]}
        q1 = state["subproblems"]["Q1"]
        q1["framework_section"] = "### Q1：第一问"
        q2 = deepcopy(q1)
        q2.update(framework_section="### Q2：第二问",
                  depends_on=[{"question": "Q1", "kind": "model"}] if edge_registered else [])
        state["subproblems"]["Q2"] = q2
        upstream = semantic_fixture.identity_payload()
        dependencies = [] if independent else [{"question": "Q1", "kind": "model"}]
        downstream = dict(deepcopy(upstream), question="Q2", dependencies=dependencies)
        section = semantic_fixture.framework(downstream).split("### Q1：第一问", 1)[1]
        section = section.replace("BEGIN Q1 -->", "BEGIN Q2 -->").replace("END Q1 -->", "END Q2 -->")
        suffix = "\n### Q2：第二问" + section
        state_file = semantic_fixture.write_project(root, state, semantic_fixture.framework(upstream) + suffix)
        validate = semantic_fixture.SEMANTIC.validate_project
        initial = validate(root, write=True, strict=True)
        if initial["status"] != "passed":
            if edge_registered or independent:
                raise RuntimeError(initial)
            return "inconsistent dependency blocked at intake"

        state = yaml.safe_load(state_file.read_bytes())
        for entry in state["subproblems"].values():
            entry.update(human_model_approval_status="approved",
                         approved_semantic_revision=entry["semantic_revision"],
                         approved_semantic_identity_hash=entry["semantic_identity_hash"])
        state_file.write_text(yaml.safe_dump(state, allow_unicode=True), encoding="utf-8")
        initial_issues = validate_state(state_file, ["Q1", "Q2"], project_root=root)
        if initial_issues:
            if edge_registered or independent:
                raise RuntimeError(initial_issues)
            return "inconsistent dependency blocked at intake"
        state["subproblems"]["Q1"].update(semantic_revision=2, semantic_change_categories=["objective"])
        if change_objective:
            upstream["objective"]["sense"] = "maximize"
        semantic_fixture.write_project(root, state, semantic_fixture.framework(upstream) + suffix)
        report = validate(root, write=True, strict=True)
        if report["status"] != "passed" and (edge_registered or independent):
            raise RuntimeError(report)
        return "blocked" if validate_state(state_file, ["Q2"], project_root=root) else "allowed"


def preprocessing(source):
    with TemporaryDirectory() as folder:
        sample = preprocessing_fixture.SolverBackendPreprocessingTests()
        sample.prepare_root(Path(folder))
        sample.preprocessing_workbook()
        book = openpyxl.load_workbook(sample.pre_workbook)
        try:
            index = book["绘图数据索引"]
            if source == "self":
                for sheet in list(book.sheetnames):
                    if sheet not in PREPROCESSING_EVIDENCE_SHEETS:
                        del book[sheet]
                index["C2"] = index.title
            elif source == "missing_field":
                index["D1"], index["D2"] = "横轴字段", "不存在的日期字段"
            elif source == "missing_table":
                index["C2"] = "不存在的底层表"
            book.save(sample.pre_workbook)
        finally:
            book.close()
        issues = execution_fixture.RECEIPT.validate_one(sample.root, sample.pre_workbook, sample.state, True)
        return not issues and sample.state["preprocessing"]["status"] == "accepted"


def primary_receipt(metric=1, *, drop_metrics=False, interval=None):
    with TemporaryDirectory() as folder:
        root = Path(folder)
        sample = execution_fixture.UserExecutionContractTests()
        code = sample.make_project(root)
        issues, config = execution_fixture.CODE.validate_script(root, code, "primary")
        if issues:
            raise RuntimeError(issues)
        execution_fixture.CODE.update_state(root, config, code)
        path = sample.make_primary_workbook(root, code)
        state = sample.read_state(root)
        question = state["subproblems"]["Q1"]
        book = openpyxl.load_workbook(path)
        try:
            book["核心指标"]["B2"].value = metric
            if drop_metrics:
                del book["核心指标"]
            if interval is not None:
                gate = book["主结果质量门"]
                gate["H2"], gate["B2"], gate["D2"] = "不确定性区间", "区间检查", "见不确定性区间"
                sheet = book.create_sheet("不确定性区间")
                sheet.append(["指标", "下界", "上界", "置信水平"])
                sheet.append(["已批准的预测", *interval, 0.95])
                question["capabilities"] = {"requires_uncertainty_quantification": True}
            book.save(path)
        finally:
            book.close()
        issues = execution_fixture.RECEIPT.validate_one(root, path, state, True)
        accepted = question.get("primary_execution_status") == "accepted"
        solved = question.get("status") == "solved"
        recorded = bool(question.get("validated_artifact_hashes", {}).get("solution_workbook"))
        if (accepted, solved, recorded) not in [(True, True, True), (False, False, False)] or accepted == bool(issues):
            raise RuntimeError(f"Inconsistent receipt state: {(accepted, solved, recorded, issues)}")
        return accepted


def workbook_bytes(sheets):
    book = openpyxl.Workbook()
    book.remove(book.active)
    try:
        for name, rows in sheets.items():
            sheet = book.create_sheet(name)
            for row in rows:
                sheet.append(row)
        stream = BytesIO()
        book.save(stream)
        return stream.getvalue()
    finally:
        book.close()


def residual(value, unit):
    specification = normalize_specification({"version": "1.0.0", "items": [{
        "id": "PQ-Q1-01", "metric": "平衡位置误差", "relation": "<=", "threshold": 1, "unit": "m",
        "threshold_source": "locked_model_tolerance", "evidence_sheet": "均衡残差",
    }]}, "Q1")
    book = workbook_bytes({
        "主结果质量门": [
            ["Verification ID", "检查项", "是否通过", "证据", "判定关系", "阈值或容差", "实际值", "证据工作表", "阈值来源", "单位"],
            ["PQ-Q1-01", "平衡位置误差", True, "测量", "<=", 1, 0.5, "均衡残差", "locked_model_tolerance", "m"],
        ],
        "均衡残差": [["主体或均衡", "残差", "容差", "是否满足", "单位"], ["A", value, max(value, 1), True, unit]],
    })
    passed, _, _ = validate_primary_numerical_evidence(
        book, {"requires_equilibrium_residual": True}, approved_specification=specification)
    return passed


def legacy_id(marker, *, has_column=True, force_strict=None):
    header, row = ["检查项", "是否通过", "证据"], ["完整性", True, "合成样例"]
    if has_column:
        header.append("Verification ID")
        row.append(marker)
    passed, _, _ = validate_primary_numerical_evidence(
        workbook_bytes({"主结果质量门": [header, row]}), force_strict=force_strict)
    return passed
