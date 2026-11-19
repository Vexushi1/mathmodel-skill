"""Validate a frozen execution-scale plan against a receipt and captured workbook."""
from __future__ import annotations

import hashlib
import io
import json
import math
import re
from collections.abc import Mapping
from typing import Any
from zipfile import BadZipFile

SCALE_RECEIPT_VERSION = "1.4.0"
SCALE_PLAN_FIELD = "execution_scale_plan"
SCALE_PLAN_SHA_FIELD = "execution_scale_plan_sha256"
SCALE_COUNT_FIELD = "actual_scale_count"
STOP_EVIDENCE_SHEET = "执行停止证据"

_NUMERIC_RELATIONS = ("<=", ">=", "abs<=", "==")


def _positive_integer(value: Any) -> bool:
    return type(value) is int and value > 0


def _observed_count(value: Any) -> int | None:
    if _positive_integer(value):
        return value
    if type(value) is float and math.isfinite(value) and value.is_integer() and value > 0:
        return int(value)
    return None


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def normalize_scale_plan(value: Any, stage: str) -> dict[str, Any]:
    """Canonicalize the exact plan shape supported for the selected stage."""
    if stage not in ("primary", "analysis") or not isinstance(value, Mapping):
        raise ValueError(f"{SCALE_PLAN_FIELD} must be a mapping on a primary or analysis stage")
    axis, mode = value.get("axis"), value.get("mode")
    if axis == "iterations":
        if stage != "primary" or mode != "adaptive_stop":
            raise ValueError(f"{SCALE_PLAN_FIELD} iterations requires primary adaptive_stop")
        if set(value) != {"axis", "mode", "minimum_count", "maximum_count", "pqs_id"}:
            raise ValueError("adaptive_stop requires minimum_count, maximum_count and pqs_id")
        minimum, maximum, pqs_id = value["minimum_count"], value["maximum_count"], _text(value["pqs_id"])
        if not _positive_integer(minimum) or not _positive_integer(maximum) or maximum < minimum:
            raise ValueError("adaptive_stop requires 0 < minimum_count <= maximum_count as integers")
        if not pqs_id:
            raise ValueError("adaptive_stop must name an approved PQS item")
        return {"axis": axis, "mode": mode, "minimum_count": minimum, "maximum_count": maximum, "pqs_id": pqs_id}

    if axis not in ("repetitions", "scenarios") or mode not in ("exact", "minimum"):
        raise ValueError(f"{SCALE_PLAN_FIELD} requires exact/minimum repetitions or scenarios, or adaptive_stop iterations")
    fields = {"axis", "mode", "count"}
    if axis == "scenarios":
        fields.add("required_scenario_ids")
    elif stage != "primary":
        raise ValueError("repetition scale is supported only for the primary stage")
    if set(value) != fields or not _positive_integer(value["count"]):
        raise ValueError(f"{SCALE_PLAN_FIELD} {axis} requires positive integer count and exactly {sorted(fields)}")
    plan = dict(value)
    if axis == "scenarios":
        raw_ids = value["required_scenario_ids"]
        if not isinstance(raw_ids, list) or not raw_ids:
            raise ValueError("required_scenario_ids must be a nonempty list of scenario IDs")
        ids = [_text(item) for item in raw_ids]
        if not all(ids) or len(set(ids)) != len(ids):
            raise ValueError("required_scenario_ids must be nonblank text without duplicate IDs")
        if mode == "exact" and len(ids) != value["count"]:
            raise ValueError("exact scenario count must match the length of required_scenario_ids")
        plan["required_scenario_ids"] = sorted(ids)
    return plan


def scale_plan_sha256(plan: Mapping[str, Any]) -> str:
    """Hash a normalized plan for the source and receipt echo."""
    payload = json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256((payload + "\n").encode("utf-8")).hexdigest()


def inspect_scale_plan(config: Mapping[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    active = config.get("run_receipt_protocol_version") == SCALE_RECEIPT_VERSION
    declared = any(field in config for field in (SCALE_PLAN_FIELD, SCALE_PLAN_SHA_FIELD, SCALE_COUNT_FIELD))
    if not active:
        return None, (["execution scale fields require RUN_RECEIPT 1.4.0"] if declared else [])
    if SCALE_COUNT_FIELD in config:
        return None, [f"{SCALE_COUNT_FIELD} is recorded only in RUN_RECEIPT"]
    try:
        plan = normalize_scale_plan(config.get(SCALE_PLAN_FIELD), config.get("stage"))
    except ValueError as exc:
        return None, [str(exc)]
    digest = config.get(SCALE_PLAN_SHA_FIELD)
    if (not isinstance(digest, str) or re.fullmatch(r"[0-9a-fA-F]{64}", digest) is None
            or digest.lower() != scale_plan_sha256(plan)):
        return None, [f"RUN_CONFIG.{SCALE_PLAN_SHA_FIELD} does not match the normalized {SCALE_PLAN_FIELD}"]
    return plan, []


def _count_issues(plan: Mapping[str, Any], receipt: Mapping[str, Any], count: int | None) -> list[str]:
    if count is None:
        return [f"RUN_RECEIPT.{SCALE_COUNT_FIELD} must be a positive numeric integer"]
    if plan["mode"] == "exact" and count != plan["count"]:
        return [f"{SCALE_COUNT_FIELD}={count} differs from exact {plan['axis']} count {plan['count']}"]
    if plan["mode"] == "minimum" and count < plan["count"]:
        return [f"{SCALE_COUNT_FIELD}={count} is below minimum {plan['axis']} count {plan['count']}"]
    if plan["mode"] != "adaptive_stop":
        return []
    issues = []
    if not plan["minimum_count"] <= count <= plan["maximum_count"]:
        issues.append(f"{SCALE_COUNT_FIELD}={count} is outside the adaptive_stop count range")
    if receipt.get("actual_stop_reason") != "criterion_met":
        issues.append("adaptive_stop requires actual_stop_reason=criterion_met")
    return issues


def scale_receipt_issues(receipt: Mapping[str, Any], delivered: Mapping[str, Any]) -> list[str]:
    active = (delivered.get("run_receipt_protocol_version") == SCALE_RECEIPT_VERSION
              or receipt.get("run_receipt_version") == SCALE_RECEIPT_VERSION
              or any(field in value for value in (delivered, receipt)
                     for field in (SCALE_PLAN_FIELD, SCALE_PLAN_SHA_FIELD, SCALE_COUNT_FIELD)))
    if not active:
        return []
    plan, issues = inspect_scale_plan(delivered)
    if plan is None:
        return issues or ["RUN_RECEIPT execution scale has no delivered 1.4.0 scale plan"]
    if receipt.get("run_receipt_version") != SCALE_RECEIPT_VERSION or receipt.get("stage") != delivered.get("stage"):
        issues.append("execution scale must return RUN_RECEIPT 1.4.0 for the delivered stage")
    if SCALE_PLAN_FIELD in receipt:
        issues.append(f"RUN_RECEIPT must echo {SCALE_PLAN_SHA_FIELD}, not a replacement {SCALE_PLAN_FIELD}")
    digest = receipt.get(SCALE_PLAN_SHA_FIELD)
    if not isinstance(digest, str) or digest.lower() != scale_plan_sha256(plan):
        issues.append(f"RUN_RECEIPT.{SCALE_PLAN_SHA_FIELD} differs from the delivered execution scale plan")
    paths = receipt.get("data_paths")
    if isinstance(paths, str):
        try:
            paths = json.loads(paths)
        except json.JSONDecodeError:
            paths = None
    if not isinstance(paths, list) or paths != delivered.get("data_paths"):
        issues.append("RUN_RECEIPT.data_paths differs from delivered execution scale inputs")
    if receipt.get("data_identity_mode") != delivered.get("data_identity_mode", "combined"):
        issues.append("RUN_RECEIPT.data_identity_mode differs from delivered execution scale inputs")
    return issues + _count_issues(plan, receipt, _observed_count(receipt.get(SCALE_COUNT_FIELD)))


def _approved_stop_item(plan: Mapping[str, Any], specification: Mapping[str, Any] | None) -> Mapping[str, Any]:
    items = specification.get("items", []) if isinstance(specification, Mapping) else []
    if not isinstance(items, list):
        items = []
    matches = [item for item in items if isinstance(item, Mapping) and item.get("id") == plan["pqs_id"]]
    if len(matches) != 1:
        raise ValueError(f"adaptive_stop requires current approved PQS item {plan['pqs_id']}")
    item = matches[0]
    if (item.get("evidence_sheet") != STOP_EVIDENCE_SHEET or item.get("relation") not in _NUMERIC_RELATIONS
            or not _text(item.get("metric")) or not _text(item.get("unit"))):
        raise ValueError(f"adaptive_stop approved PQS item {plan['pqs_id']} must use a numeric criterion "
                         f"with a unit and evidence sheet {STOP_EVIDENCE_SHEET}")
    return item


def adaptive_plan_issues(plan: Mapping[str, Any] | None, approved_specification: Mapping[str, Any] | None) -> list[str]:
    if plan is None or plan["mode"] != "adaptive_stop":
        return []
    try:
        _approved_stop_item(plan, approved_specification)
    except ValueError as exc:
        return [str(exc)]
    return []


def _required_rows(book, sheet: str, fields: tuple[str, ...]) -> list[dict[str, Any]]:
    from validate_numerical_evidence import _sheet_records

    headers, rows = _sheet_records(book, sheet)
    missing = [field for field in fields if field not in headers]
    if missing:
        raise ValueError(f"{sheet} is missing execution scale evidence columns: {missing}")
    if not rows:
        raise ValueError(f"{sheet} contains no execution scale evidence rows")
    return rows


def _material_id(value: Any) -> str:
    if type(value) is int:
        return str(value)
    if type(value) is float and math.isfinite(value) and value.is_integer():
        return str(int(value))
    return _text(value)


def _observed_ids(book, stage: str, axis: str) -> set[str]:
    from validate_numerical_evidence import _as_bool, _as_number

    pressure = stage == "analysis" and axis == "scenarios"
    if pressure:
        sheet, label = "场景压力测试", "场景"
        fields = (label, "变化条件", "结果指标", "是否可行")
    elif axis == "scenarios":
        sheet, label = "逐场景结果", "场景"
        fields = (label, "指标", "数值")
    else:
        sheet, label = "重复试验结果", "重复编号"
        fields = (label, "指标", "数值")
    seen_ids = set()
    for index, row in enumerate(_required_rows(book, sheet, fields), start=2):
        identifier = _material_id(row[label])
        if pressure:
            condition = _text(row["变化条件"]) or _as_number(row["变化条件"]) is not None
            result = _text(row["结果指标"]) or _as_number(row["结果指标"]) is not None
            substantive = condition and result and _as_bool(row["是否可行"]) is not None
        else:
            substantive = _text(row["指标"]) and _as_number(row["数值"]) is not None
        if not identifier or not substantive:
            raise ValueError(f"{sheet} row {index} lacks a substantive execution scale record")
        seen_ids.add(identifier)
    return seen_ids


def _adaptive_evidence_issues(book, item: Mapping[str, Any], count: int) -> list[str]:
    from validate_numerical_evidence import _as_number, _relation_result

    rows = _required_rows(book, STOP_EVIDENCE_SHEET, ("迭代或样本数", "指标", "数值", "单位"))
    checkpoints: dict[int, float] = {}
    for row in rows:
        if _text(row["指标"]) != item["metric"]:
            continue
        step = _observed_count(row["迭代或样本数"])
        value = _as_number(row["数值"])
        if step is None or value is None or _text(row["单位"]) != item["unit"]:
            return [f"{STOP_EVIDENCE_SHEET} requires positive integer checkpoints, finite {item['metric']} "
                    f"values and the approved PQS unit {item['unit']!r}"]
        if step in checkpoints:
            return [f"{STOP_EVIDENCE_SHEET} has duplicate checkpoints for {item['metric']} at iteration {step}"]
        checkpoints[step] = value
    if not checkpoints:
        return [f"{STOP_EVIDENCE_SHEET} is missing the approved PQS metric {item['metric']!r}"]
    final_step = max(checkpoints)
    if final_step != count:
        return [f"{STOP_EVIDENCE_SHEET} last checkpoint {final_step} differs from {SCALE_COUNT_FIELD}={count}"]
    passed, detail = _relation_result(item["relation"], checkpoints[final_step], item["threshold"])
    if passed is not True:
        description = f"{item['metric']} at iteration {final_step} does not satisfy approved PQS {item['id']}"
        return [f"{description}: {detail}" if detail else description]
    return []


def scale_evidence_issues(
    workbook_bytes: bytes, plan: Mapping[str, Any], receipt: Mapping[str, Any], *,
    approved_specification: Mapping[str, Any] | None = None,
) -> list[str]:
    """Check distinct recorded identities or one attained terminal criterion."""
    from openpyxl import load_workbook
    from openpyxl.utils.exceptions import InvalidFileException

    count = _observed_count(receipt.get(SCALE_COUNT_FIELD))
    issues = _count_issues(plan, receipt, count)
    if count is None:
        return issues
    try:
        book = load_workbook(io.BytesIO(workbook_bytes), read_only=True, data_only=True)
        try:
            if plan["mode"] == "adaptive_stop":
                item = _approved_stop_item(plan, approved_specification)
                return issues + _adaptive_evidence_issues(book, item, count)
            ids = _observed_ids(book, receipt.get("stage"), plan["axis"])
        finally:
            book.close()
    except (OSError, SyntaxError, ValueError, TypeError, KeyError, OverflowError, BadZipFile, InvalidFileException) as exc:
        return issues + [f"execution scale workbook evidence: {exc}"]
    if len(ids) != count:
        issues.append(f"observed {len(ids)} distinct {plan['axis']} IDs differ from {SCALE_COUNT_FIELD}={count}")
    if plan["axis"] == "scenarios":
        required = set(plan["required_scenario_ids"])
        missing = required - ids
        if missing:
            issues.append(f"missing required scenario IDs: {sorted(missing)}")
        if plan["mode"] == "exact" and ids - required:
            issues.append(f"unexpected scenario IDs: {sorted(ids - required)}")
    return issues
