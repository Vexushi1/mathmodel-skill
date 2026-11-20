#!/usr/bin/env python3
"""Independently recheck intrinsic primary-solve numerical evidence.

This validator never runs task-specific model code. It reads a returned primary
workbook, applies the capability-driven contract in
``core/numerical_verification_contract.yaml``, and reports contradictions between
bottom-level evidence and the main quality summary.
"""
from __future__ import annotations

import argparse
import io
import math
import re
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping

import openpyxl
import yaml

SCRIPT_DIR = str(Path(__file__).resolve().parent)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
from primary_quality_specification import PrimaryQualitySpecificationError, numeric_threshold  # noqa: E402


def _as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "是", "通过", "满足"}:
        return True
    if text in {"false", "0", "no", "否", "未通过", "不满足"}:
        return False
    return None


def _as_number(value: Any) -> float | None:
    if isinstance(value, bool) or value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _contract_candidates(explicit: Path | None) -> list[Path]:
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(Path(explicit))
    here = Path(__file__).resolve()
    candidates.extend(parent / "core" / "numerical_verification_contract.yaml" for parent in here.parents)
    return candidates


def load_contract(path: Path | None = None) -> dict[str, Any]:
    for candidate in _contract_candidates(path):
        if candidate.is_file():
            return yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
    raise FileNotFoundError("找不到core/numerical_verification_contract.yaml")


def _sheet_records(book: openpyxl.Workbook, sheet: str) -> tuple[list[str], list[dict[str, Any]]]:
    if sheet not in book.sheetnames:
        return [], []
    rows = list(book[sheet].iter_rows(values_only=True))
    if not rows:
        return [], []
    headers = ["" if item is None else str(item).strip() for item in rows[0]]
    while headers and not headers[-1] and all(
        len(row) < len(headers) or row[len(headers) - 1] in (None, "") for row in rows[1:]
    ):
        headers.pop()
    if any(not header for header in headers):
        raise ValueError(f"工作表“{sheet}”存在空字段名")
    if len(headers) != len(set(headers)):
        raise ValueError(f"工作表“{sheet}”包含重复字段")
    records: list[dict[str, Any]] = []
    for row in rows[1:]:
        if not any(value not in (None, "") for value in row[: len(headers)]):
            continue
        records.append({headers[index]: row[index] if index < len(row) else None for index in range(len(headers))})
    return headers, records


def _numeric_equal(left: float, right: float | Fraction, contract: Mapping[str, Any]) -> bool:
    tolerance = (contract.get("numeric_consistency") or {}).get("comparison_tolerance") or {}
    absolute = float(tolerance.get("absolute", 1.0e-12))
    relative = float(tolerance.get("relative", 1.0e-9))
    if isinstance(right, Fraction):
        left = Fraction(str(left))
        absolute = Fraction(str(absolute))
        relative = Fraction(str(relative))
    return abs(left - right) <= max(absolute, relative * max(abs(left), abs(right)))


def _relation_result(relation: str, actual: Any, threshold: Any) -> tuple[bool | None, str | None]:
    if relation == "bool_true":
        parsed = _as_bool(actual)
        return parsed is True, None if parsed is not None else "实际值无法解析为布尔值"

    actual_number = actual if isinstance(actual, Fraction) else _as_number(actual)
    threshold_number = _as_number(threshold)
    if isinstance(actual, Fraction) and threshold_number is not None:
        threshold_number = Fraction(str(threshold_number))
    if actual_number is None or threshold_number is None:
        return None, "实际值/阈值必须为有限数值"
    if relation == "<=":
        return actual_number <= threshold_number, None
    if relation == ">=":
        return actual_number >= threshold_number, None
    if relation == "abs<=":
        if threshold_number < 0:
            return None, "abs<=阈值/容差不得为负数"
        return abs(actual_number) <= threshold_number, None
    if relation == "==":
        return actual_number == threshold_number, None
    return None, f"未知判定关系: {relation}"


def _require_columns(sheet: str, headers: list[str], columns: list[str]) -> list[str]:
    return [f"{sheet}缺少字段: {column}" for column in columns if column not in headers]


def _residual_observations(
    sheet: str,
    headers: list[str],
    records: list[dict[str, Any]],
    value_column: str,
) -> tuple[list[tuple[int, dict[str, Any], float]], list[str]]:
    issues = _require_columns(sheet, headers, [value_column, "容差", "是否满足"])
    if issues:
        return [], issues
    if not records:
        return [], [f"{sheet}没有实质数据"]
    observations = []
    for index, record in enumerate(records, start=2):
        value = _as_number(record.get(value_column))
        tolerance = _as_number(record.get("容差"))
        actual = _as_bool(record.get("是否满足"))
        if value is None or tolerance is None:
            issues.append(f"{sheet}第{index}行{value_column}/容差必须为有限数值")
            continue
        if tolerance < 0:
            issues.append(f"{sheet}第{index}行容差不得为负数")
            continue
        if value_column == "违反量" and value < 0:
            issues.append(f"{sheet}第{index}行违反量不得为负数")
            continue
        expected = abs(value) <= tolerance
        if actual is None or actual != expected:
            issues.append(f"{sheet}第{index}行是否满足与{value_column}/容差不一致")
        observations.append((index, record, abs(value)))
    return observations, issues


def _row_residual_metric(
    sheet: str, headers: list[str], records: list[dict[str, Any]], value_column: str,
) -> tuple[float | None, list[str]]:
    observations, issues = _residual_observations(sheet, headers, records, value_column)
    return max((value for _, _, value in observations), default=None), issues


def _unit_label(raw: Any, context: str) -> str:
    # Excel may store the dimensionless unit 1 as a numeric cell.
    if type(raw) in (float, int) and raw == 1:
        return "1"
    if raw is None:
        return ""
    if isinstance(raw, str) and raw.strip().lower() not in {"not_applicable", "unknown", "未知"}:
        return raw.strip()
    raise ValueError(f"{context}: 残差的单位必须为明确的单位标记: {raw!r}")


def _residuals_by_id(
    sheet: str, headers: list[str], records: list[dict[str, Any]], target_units: Mapping[str, str],
    contract: Mapping[str, Any],
) -> tuple[dict[str, Fraction], list[str]]:
    """Take each maximum in its own criterion's unit after checking row identity."""
    groups = contract["recheck_modes"]["max_abs_residual"].get("unit_powers_of_ten", {})
    only_id = next(iter(target_units)) if len(target_units) == 1 else ""
    maxima: dict[str, Fraction] = {}
    observations, issues = _residual_observations(sheet, headers, records, "残差")
    for index, record, value in observations:
        raw_id = record.get("Verification ID")
        label = "" if raw_id is None else str(raw_id).strip()
        identifier = label or only_id
        if identifier not in target_units:
            issues.append(f"{sheet}第{index}行Verification ID缺失或未在该表登记: {identifier!r}")
            continue
        source_unit = _unit_label(record.get("单位"), f"{identifier} {sheet}第{index}行")
        target_unit = target_units[identifier]
        power = 0
        if source_unit != target_unit:
            common = next((units for units in groups.values() if source_unit in units and target_unit in units), None)
            if common is None:
                issues.append(f"{identifier}: {sheet}第{index}行单位无法核对: {source_unit!r} -> {target_unit!r}")
                continue
            power = common[source_unit] - common[target_unit]
        if source_unit:
            # A rounded text literal cannot supply a verified metric at the threshold.
            try:
                numeric_threshold(record["残差"], identifier)
                numeric_threshold(record["容差"], identifier)
            except PrimaryQualitySpecificationError as exc:
                issues.append(f"{sheet}第{index}行: {exc}")
                continue
        converted = Fraction(str(value)) * Fraction(10) ** power
        maxima[identifier] = max(maxima.get(identifier, converted), converted)
    for identifier in sorted(target_units.keys() - maxima.keys()):
        issues.append(f"{identifier}: {sheet}缺少可核对的残差观测")
    return maxima, issues


def _marked_relative_metric(
    sheet: str,
    headers: list[str],
    records: list[dict[str, Any]],
) -> tuple[float | None, list[str]]:
    issues = _require_columns(sheet, headers, ["相对变化", "用于主判定"])
    if issues:
        return None, issues
    marked = [record for record in records if _as_bool(record.get("用于主判定")) is True]
    if not marked:
        return None, [f"{sheet}至少需要一行用于主判定=true的离散精度证据"]
    values: list[float] = []
    for record in marked:
        value = _as_number(record.get("相对变化"))
        if value is None:
            issues.append(f"{sheet}用于主判定行的相对变化必须为有限数值")
        else:
            values.append(abs(value))
    return (max(values) if values else None), issues


def _marked_boolean_metric(
    sheet: str,
    headers: list[str],
    records: list[dict[str, Any]],
) -> tuple[bool | None, list[str]]:
    issues = _require_columns(sheet, headers, ["判定", "用于主判定"])
    if issues:
        return None, issues
    marked = [record for record in records if _as_bool(record.get("用于主判定")) is True]
    if not marked:
        return None, [f"{sheet}至少需要一行用于主判定=true的收敛证据"]
    parsed = [_as_bool(record.get("判定")) for record in marked]
    if any(value is None for value in parsed):
        issues.append(f"{sheet}用于主判定行的判定必须为可解析布尔值")
        return None, issues
    return all(value is True for value in parsed), issues


def _all_boolean_metric(
    sheet: str,
    headers: list[str],
    records: list[dict[str, Any]],
) -> tuple[bool | None, list[str]]:
    issues = _require_columns(sheet, headers, ["是否通过"])
    if issues:
        return None, issues
    if not records:
        return None, [f"{sheet}没有实质数据"]
    parsed = [_as_bool(record.get("是否通过")) for record in records]
    if any(value is None for value in parsed):
        issues.append(f"{sheet}的是否通过必须为可解析布尔值")
        return None, issues
    return all(value is True for value in parsed), issues


def _recheck_evidence(
    mode: str,
    sheet: str,
    headers: list[str],
    records: list[dict[str, Any]],
) -> tuple[Any, list[str]]:
    if mode == "max_violation":
        return _row_residual_metric(sheet, headers, records, "违反量")
    if mode == "marked_relative_change":
        return _marked_relative_metric(sheet, headers, records)
    if mode == "marked_boolean":
        return _marked_boolean_metric(sheet, headers, records)
    if mode == "all_boolean":
        return _all_boolean_metric(sheet, headers, records)
    if mode == "summary_criterion":
        return None, []
    return None, [f"未实现的numerical verification recheck_mode: {mode}"]


def _approved_quality_row_issues(
    row: Mapping[str, Any], approved: Mapping[str, Any], verification_id: str,
) -> list[str]:
    """Compare admissibility criteria independently of returned measurements."""
    issues = []
    for column, field in (
        ("检查项", "metric"), ("判定关系", "relation"), ("单位", "unit"),
        ("证据工作表", "evidence_sheet"), ("阈值来源", "threshold_source"),
    ):
        actual = row.get(column)
        text = "" if actual is None else str(actual).strip()
        if text != approved.get(field, ""):
            issues.append(f"{verification_id} PQS: {column} differs from approved {field}")
    threshold = row.get("阈值或容差")
    if approved["relation"] == "bool_true":
        matches = _as_bool(threshold) is True
    else:
        try:
            matches = numeric_threshold(threshold, verification_id) == approved["threshold"]
        except PrimaryQualitySpecificationError:
            matches = False
    if not matches:
        issues.append(f"{verification_id} PQS: threshold differs from the approved threshold")
    return issues


def validate_primary_numerical_evidence(
    workbook: Path | bytes,
    capabilities: Mapping[str, bool] | None = None,
    *,
    contract_path: Path | None = None,
    force_strict: bool | None = None,
    contract: Mapping[str, Any] | None = None,
    approved_specification: Mapping[str, Any] | None = None,
) -> tuple[bool, list[str], dict[str, Any]]:
    """Validate one primary workbook without executing task-specific code."""
    contract = load_contract(contract_path) if contract is None else contract
    book = openpyxl.load_workbook(
        io.BytesIO(workbook) if isinstance(workbook, bytes) else Path(workbook),
        read_only=True, data_only=True,
    )
    issues: list[str] = []
    try:
        quality_headers, quality_rows = _sheet_records(book, "主结果质量门")
        if not quality_headers:
            return False, ["缺少主结果质量门工作表"], {"mode": "invalid", "strict": False}

        marker_present = "Verification ID" in quality_headers and any(
            str(row.get("Verification ID", "")).strip() for row in quality_rows
        )
        strict = (approved_specification is not None
                  or (marker_present if force_strict is None else bool(force_strict)))

        protocol_map = contract.get("capability_protocols") or {}
        active_capabilities = sorted(
            capability for capability, enabled in (capabilities or {}).items()
            if enabled and capability in protocol_map
        )

        # Legacy v7.13 read compatibility: preserve old Boolean-gate admission while
        # still detecting contradictions in residual sheets that already exist.
        if not strict:
            for sheet, value_column in (
                ("约束违反检查", "违反量"),
                ("均衡残差", "残差"),
                ("守恒残差", "残差"),
            ):
                headers, records = _sheet_records(book, sheet)
                if headers:
                    _, row_issues = _row_residual_metric(sheet, headers, records, value_column)
                    issues.extend(row_issues)
            report = {
                "mode": "legacy_read",
                "strict": False,
                "active_capabilities": active_capabilities,
                "checked_verification_ids": [],
            }
            return not issues, list(dict.fromkeys(issues)), report

        strict_contract = contract.get("strict_v714_trace") or {}
        specification = contract.get("primary_quality_specification") or {}
        id_pattern = str(specification.get("id_pattern", r"^PQ-Q[1-9][0-9]*-[0-9]{2,}$"))
        threshold_sources = {str(item) for item in specification.get("threshold_sources", [])}
        required_columns = [str(item) for item in strict_contract.get("required_columns_when_active", [])]
        issues.extend(_require_columns("主结果质量门", quality_headers, required_columns))
        if not quality_rows:
            issues.append("主结果质量门至少需要一行严格Verification证据")
        if issues:
            return False, list(dict.fromkeys(issues)), {
                "mode": "v7.14_strict", "strict": True, "active_capabilities": active_capabilities,
            }

        allowed_relations = {str(item) for item in strict_contract.get("allowed_relations", [])}
        seen_ids: set[str] = set()
        referenced_sheets: set[str] = set()
        computed_by_sheet: dict[str, Any] = {}
        has_observations: dict[str, bool] = {}
        modes_by_sheet: dict[str, set[str]] = {}
        required_relations_by_sheet: dict[str, str] = {}

        approved_items = (
            {item["id"]: item for item in approved_specification["items"]}
            if approved_specification is not None else None
        )
        residual_units: dict[str, dict[str, str]] = {}
        residual_maxima: dict[str, dict[str, Fraction]] = {}
        residual_sheets = {spec["evidence_sheet"] for spec in protocol_map.values()
                           if spec.get("recheck_mode") == "max_abs_residual"}
        for row in quality_rows:
            sheet = str(row.get("证据工作表", "")).strip()
            if sheet in residual_sheets:
                identifier = str(row.get("Verification ID", "")).strip()
                item = (approved_items or {}).get(identifier)
                unit = item.get("unit") if item is not None else row.get("单位")
                residual_units.setdefault(sheet, {})[identifier] = _unit_label(unit, f"{identifier} 主结果质量门")
                modes_by_sheet.setdefault(sheet, set()).add("max_abs_residual")

        for capability in active_capabilities:
            spec = protocol_map[capability] or {}
            sheet = str(spec.get("evidence_sheet", "")).strip()
            mode = str(spec.get("recheck_mode", "")).strip()
            if sheet:
                modes_by_sheet.setdefault(sheet, set()).add(mode)

        # Recompute bottom-level evidence once per sheet/mode.
        for sheet, modes in modes_by_sheet.items():
            headers, records = _sheet_records(book, sheet)
            has_observations[sheet] = bool(records)
            if not headers:
                issues.append(f"启用的primary capability需要工作表但不存在: {sheet}")
                continue
            if not records:
                issues.append(f"启用的primary capability证据工作表无实质数据: {sheet}")
                continue
            if len(modes) > 1:
                issues.append(f"同一证据工作表映射到多个不兼容recheck_mode: {sheet} -> {sorted(modes)}")
                continue
            mode = next(iter(modes))
            mode_contract = (contract.get("recheck_modes") or {}).get(mode) or {}
            required_relation = str(mode_contract.get("quality_relation", "")).strip()
            if required_relation:
                required_relations_by_sheet[sheet] = required_relation
            if mode == "max_abs_residual":
                residual_maxima[sheet], evidence_issues = _residuals_by_id(
                    sheet, headers, records, residual_units.get(sheet, {}), contract,
                )
            else:
                computed, evidence_issues = _recheck_evidence(mode, sheet, headers, records)
                computed_by_sheet[sheet] = computed
                if required_relation == "bool_true" and computed is False:
                    issues.append(f"{sheet}用于主判定的布尔证据未通过")
            issues.extend(evidence_issues)
            if mode in {"max_violation", "max_abs_residual"}:
                failed_rows = [
                    index for index, record in enumerate(records, start=2)
                    if _as_bool(record.get("是否满足")) is False
                ]
                if failed_rows:
                    issues.append(f"{sheet}存在未满足容差的主数值证据行: {failed_rows}")

        checked_ids: list[str] = []
        for row_number, row in enumerate(quality_rows, start=2):
            verification_id = str(row.get("Verification ID", "")).strip()
            if not verification_id:
                issues.append(f"主结果质量门第{row_number}行缺少Verification ID")
                continue
            if re.fullmatch(id_pattern, verification_id) is None:
                issues.append(f"主结果质量门第{row_number}行Verification ID不符合PQS格式: {verification_id}")
            if verification_id in seen_ids:
                issues.append(f"主结果质量门Verification ID重复: {verification_id}")
            seen_ids.add(verification_id)
            checked_ids.append(verification_id)
            approved = approved_items.get(verification_id) if approved_items is not None else None
            if approved_items is not None:
                if approved is None:
                    issues.append(f"{verification_id} PQS: unapproved verification ID")
                else:
                    issues.extend(_approved_quality_row_issues(row, approved, verification_id))

            evidence_sheet = str(row.get("证据工作表", "")).strip()
            if not evidence_sheet:
                issues.append(f"{verification_id}缺少证据工作表")
            elif evidence_sheet not in book.sheetnames:
                issues.append(f"{verification_id}引用不存在的证据工作表: {evidence_sheet}")
            else:
                if evidence_sheet not in has_observations:
                    _, evidence_records = _sheet_records(book, evidence_sheet)
                    has_observations[evidence_sheet] = bool(evidence_records)
                if not has_observations[evidence_sheet]:
                    issues.append(f"{verification_id}引用的证据工作表无实质数据: {evidence_sheet}")
                referenced_sheets.add(evidence_sheet)

            threshold_source = str(row.get("阈值来源", "")).strip()
            if not threshold_source:
                issues.append(f"{verification_id}缺少阈值来源")
            elif threshold_sources and threshold_source not in threshold_sources:
                issues.append(f"{verification_id}使用未登记阈值来源: {threshold_source}")

            relation = str(row.get("判定关系", "")).strip()
            required_relation = required_relations_by_sheet.get(evidence_sheet)
            if required_relation and relation != required_relation:
                issues.append(f"{verification_id}引用{evidence_sheet}必须使用判定关系{required_relation}")
            if relation not in allowed_relations:
                issues.append(f"{verification_id}使用未登记判定关系: {relation}")
                continue
            evaluation_relation = approved["relation"] if approved is not None else relation
            evaluation_threshold = approved["threshold"] if approved is not None else row.get("阈值或容差")
            expected_pass, relation_issue = _relation_result(
                evaluation_relation, row.get("实际值"), evaluation_threshold,
            )
            if relation_issue:
                issues.append(f"{verification_id}: {relation_issue}")
                continue
            declared_pass = _as_bool(row.get("是否通过"))
            if declared_pass is None or declared_pass != expected_pass:
                issues.append(f"{verification_id}的是否通过与实际值/阈值/判定关系不一致")
            if expected_pass is not True:
                issues.append(f"{verification_id}未达到主质量判据")

            computed = (residual_maxima[evidence_sheet].get(verification_id) if evidence_sheet in residual_maxima
                        else computed_by_sheet.get(evidence_sheet))
            if computed is not None:
                computed_pass, computed_issue = _relation_result(
                    evaluation_relation, computed, evaluation_threshold,
                )
                if computed_issue:
                    issues.append(f"{verification_id}重算指标: {computed_issue}")
                elif computed_pass is not True:
                    issues.append(f"{verification_id}重算指标未达到主质量判据")
                if isinstance(computed, bool):
                    actual_bool = _as_bool(row.get("实际值"))
                    if actual_bool is None or actual_bool != computed:
                        issues.append(f"{verification_id}实际值与{evidence_sheet}重算布尔结果不一致")
                else:
                    actual_number = _as_number(row.get("实际值"))
                    if actual_number is None or not _numeric_equal(actual_number, computed, contract):
                        issues.append(f"{verification_id}实际值与{evidence_sheet}重算指标不一致")

        if approved_items is not None:
            issues.extend(f"{verification_id} PQS: missing approved verification ID"
                          for verification_id in sorted(set(approved_items) - seen_ids))
        required_sheets = {
            str((protocol_map[capability] or {}).get("evidence_sheet", "")).strip()
            for capability in active_capabilities
            if str((protocol_map[capability] or {}).get("evidence_sheet", "")).strip()
        }
        for sheet in sorted(required_sheets - referenced_sheets):
            issues.append(f"主结果质量门未追溯启用capability的证据工作表: {sheet}")

        report = {
            "mode": "v7.14_strict",
            "strict": True,
            "active_capabilities": active_capabilities,
            "required_evidence_sheets": sorted(required_sheets),
            "referenced_evidence_sheets": sorted(referenced_sheets),
            "checked_verification_ids": checked_ids,
            "task_code_executed": False,
        }
        return not issues, list(dict.fromkeys(issues)), report
    except ValueError as exc:
        return False, [str(exc)], {"mode": "invalid", "strict": bool(force_strict)}
    finally:
        book.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--capability", action="append", default=[])
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    capabilities = {name: True for name in args.capability}
    passed, issues, report = validate_primary_numerical_evidence(
        args.workbook,
        capabilities,
        contract_path=args.contract,
        force_strict=True if args.strict else None,
    )
    report["status"] = "passed" if passed else "failed"
    report["issues"] = issues
    print(yaml.safe_dump(report, allow_unicode=True, sort_keys=False).rstrip())
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
