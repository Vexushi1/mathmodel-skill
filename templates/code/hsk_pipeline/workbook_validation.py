"""Shared workbook contract validation for writers, artifact checks and project sync."""
from __future__ import annotations

from contextlib import closing, nullcontext
import math
import io
from numbers import Real
from pathlib import Path
from typing import Any, BinaryIO, Callable, Mapping, NamedTuple, Sequence

import pandas as pd
from openpyxl import load_workbook

VALID_WORKBOOK_KINDS = {"solution", "result_analysis"}
WORKBOOK_KIND_ALIASES = {"robustness": "result_analysis"}


def _normalize_kind(kind: str) -> str:
    normalized = WORKBOOK_KIND_ALIASES.get(kind, kind)
    if normalized not in VALID_WORKBOOK_KINDS:
        allowed = sorted(VALID_WORKBOOK_KINDS | set(WORKBOOK_KIND_ALIASES))
        raise ValueError(f"workbook_kind 必须为 {allowed}")
    return normalized


def _as_frame(value: Any, *, allow_empty: bool = False, dtype: str | None = None) -> pd.DataFrame:
    if isinstance(value, pd.DataFrame):
        frame = value.copy()
    elif isinstance(value, Mapping):
        frame = pd.DataFrame([dict(value)], dtype=dtype)
    elif isinstance(value, (list, tuple)):
        frame = pd.DataFrame(value, dtype=dtype)
    else:
        frame = pd.DataFrame({"数值": [value]})
    frame = frame.dropna(how="all").reset_index(drop=True)
    if frame.empty and not allow_empty:
        raise ValueError("禁止写入空工作表")
    if allow_empty and frame.empty and not len(frame.columns):
        return frame
    columns = [str(column).strip() for column in frame.columns]
    if not columns or any(not column for column in columns):
        raise ValueError("工作表至少需要一个非空字段")
    if len(columns) != len(set(columns)):
        raise ValueError("工作表包含重复字段")
    frame.columns = columns
    return frame


def prepare_tables(
    tables: Mapping[str, Any],
    *,
    name_normalizer: Callable[[str], str] | None = None,
    allow_empty: bool = False,
) -> list[tuple[str, pd.DataFrame]]:
    if not tables:
        raise ValueError("没有可写入的结果表")
    prepared: list[tuple[str, pd.DataFrame]] = []
    used: set[str] = set()
    for raw_name, value in tables.items():
        name = name_normalizer(str(raw_name)) if name_normalizer else str(raw_name).strip()
        if not name:
            raise ValueError("工作表名称不能为空")
        if len(name) > 31:
            raise ValueError(f"工作表名称超过31字符: {name}")
        if name in used:
            raise ValueError(f"工作表名称重复: {name}")
        used.add(name)
        # Preserve Excel's distinction between a blank return and a non-finite number.
        dtype = "object" if name == "核心指标" else None
        prepared.append((name, _as_frame(value, allow_empty=allow_empty, dtype=dtype)))
    return prepared


def _worksheet_values(worksheet) -> list[tuple]:
    if worksheet.title != "核心指标":
        return list(worksheet.iter_rows(values_only=True))
    rows = []
    for row in worksheet.iter_rows():
        for cell in row:
            if cell.data_type == "e":
                raise ValueError(f"核心指标单元格 {cell.coordinate} 含 Excel 错误值 {cell.value}")
        rows.append(tuple(cell.value for cell in row))
    return rows


def _worksheet_headers(rows: list[tuple]) -> list[str]:
    headers = ["" if value is None else str(value).strip() for value in rows[0]]
    while headers and not headers[-1] and all(
        len(row) < len(headers) or row[len(headers) - 1] in (None, "") for row in rows[1:]
    ):
        headers.pop()
    return headers


def _check_optional_metric_formulas(source: BinaryIO, headers: list[str], rows: list[tuple]) -> None:
    """Excel's cached-value view represents uncalculated formulas and empty cells as None."""
    if not {"数值", "是否必需"}.issubset(headers):
        return
    value = headers.index("数值")
    required = headers.index("是否必需")
    blanks = {number for number, row in enumerate(rows, 2) if row[required] is False and row[value] is None}
    if not blanks:
        return
    with closing(load_workbook(source, read_only=True, data_only=False)) as book:
        for number, (cell,) in enumerate(book["核心指标"].iter_rows(
                min_row=2, max_row=max(blanks), min_col=value + 1, max_col=value + 1), 2):
            if number in blanks and cell.data_type == "f":
                raise ValueError(f"核心指标第 {number} 行的未计算公式不能登记为可选缺失")


def read_workbook_tables(
    path: Path | bytes | BinaryIO, *, only_sheets: set[str] | None = None, allow_empty: bool = False,
) -> dict[str, pd.DataFrame]:
    if hasattr(path, "read"):
        handle = nullcontext(path)
    else:
        handle = io.BytesIO(path) if isinstance(path, bytes) else Path(path).open("rb")
    tables: dict[str, pd.DataFrame] = {}
    with handle as source, closing(load_workbook(source, read_only=True, data_only=True)) as workbook:
        for worksheet in workbook.worksheets:
            if only_sheets is not None and worksheet.title not in only_sheets:
                continue
            rows = _worksheet_values(worksheet)
            if not rows and not allow_empty:
                raise ValueError(f"工作表“{worksheet.title}”为空")
            headers = _worksheet_headers(rows) if rows else []
            if allow_empty and not headers:
                tables[worksheet.title] = pd.DataFrame()
                continue
            if not headers or any(not header for header in headers):
                raise ValueError(f"工作表“{worksheet.title}”存在空字段名")
            if len(headers) != len(set(headers)):
                raise ValueError(f"工作表“{worksheet.title}”包含重复字段")
            if worksheet.title == "核心指标":
                _check_optional_metric_formulas(source, headers, rows[1:])
            data = [
                tuple(row[: len(headers)])
                for row in rows[1:]
                if any(value is not None for value in row[: len(headers)])
            ]
            if not data and not allow_empty:
                raise ValueError(f"工作表“{worksheet.title}”为空")
            dtype = "object" if worksheet.title == "核心指标" else None
            tables[worksheet.title] = pd.DataFrame(data, columns=headers, dtype=dtype)
    return tables


def _required_sheet_schemas(
    schema: Mapping[str, Any], kind: str,
) -> tuple[set[str], dict[str, Mapping[str, Any]]]:
    if kind == "solution":
        section = schema["solution_workbook"]
        required = dict(section.get("common_required_sheets", {}))
        all_schemas = {**required, **dict(section.get("common_recommended_sheets", {}))}
        return set(required), all_schemas
    section = schema["result_analysis_workbook"]
    required = dict(section.get("common_required_sheets", {}))
    all_schemas = {**required, **dict(section.get("sheet_schemas", {}))}
    return set(required), all_schemas


def _conditional_required_sheets(
    schema: Mapping[str, Any],
    problem_types: Sequence[str],
    capabilities: Mapping[str, bool] | None,
) -> set[str]:
    contract = schema.get("capability_contract", {})
    required: set[str] = set()
    if capabilities is not None:
        allowed = set(contract.get("allowed", []))
        unknown = sorted(set(capabilities) - allowed)
        if unknown:
            raise ValueError(f"未知验证能力标志: {unknown}")
        for capability, enabled in capabilities.items():
            if enabled:
                required.update(contract.get("required_sheets", {}).get(capability, []))
        return required
    fallback = contract.get("legacy_problem_type_fallback", {})
    if set(problem_types).intersection(fallback.get("problem_types", [])):
        required.update(fallback.get("required_sheets", []))
    return required


def _profile_requirements(
    schema: Mapping[str, Any],
    objective: str | None,
    structures: Sequence[str],
    problem_types: Sequence[str],
) -> list[tuple[str, set[str]]]:
    section = schema.get("solution_workbook", {})
    requirements: list[tuple[str, set[str]]] = []
    if objective:
        required = set(section.get("objective_profiles", {}).get(objective, {}).get("required_any", []))
        if required:
            requirements.append((f"objective:{objective}", required))
    for structure in structures:
        required = set(section.get("structure_profiles", {}).get(structure, {}).get("required_any", []))
        if required:
            requirements.append((f"structure:{structure}", required))
    if not objective and not structures:
        profiles = section.get("task_profiles", {})
        for problem_type in problem_types:
            required = set((profiles.get(problem_type, {}) or {}).get("required_any", []))
            if required:
                requirements.append((f"legacy:{problem_type}", required))
    return requirements


def _check_required_columns(sheet: str, frame: pd.DataFrame, spec: Mapping[str, Any]) -> None:
    missing = [str(column) for column in spec.get("required_columns", []) if str(column) not in frame.columns]
    if missing:
        raise ValueError(f"工作表“{sheet}”缺少必需字段: {missing}")


def _check_record_keys(sheet: str, frame: pd.DataFrame) -> None:
    for key in ("记录键", "样本键"):
        if key not in frame.columns:
            continue
        series = frame[key]
        if series.isna().any() or series.astype(str).str.strip().eq("").any():
            raise ValueError(f"工作表“{sheet}”的主键字段“{key}”存在空值")
        if series.duplicated().any():
            duplicate = series[series.duplicated()].iloc[0]
            raise ValueError(f"工作表“{sheet}”的主键字段“{key}”存在重复值: {duplicate}")
        break


def _check_finite_numbers(sheet: str, frame: pd.DataFrame) -> None:
    for column in frame.select_dtypes(include="number").columns:
        values = frame[column].dropna()
        if not values.map(lambda value: math.isfinite(float(value))).all():
            raise ValueError(f"工作表“{sheet}”的数值字段“{column}”包含 NaN 以外的非有限值")


def _blank_cell(value: Any) -> bool:
    return pd.api.types.is_scalar(value) and (pd.isna(value) or isinstance(value, str) and not value.strip())


def _finite_number(value: Any) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool) and math.isfinite(value)


def _metric_rows(sheet: str, frame: pd.DataFrame):
    for index, row in enumerate(frame.to_dict("records"), start=2):
        metric = row["指标"]
        location = f"{sheet}第 {index} 行（{metric}）"
        if not isinstance(metric, str) or not _substantive(metric):
            raise ValueError(f"{location} 缺少有效指标名称")
        yield location, row


def _check_core_metrics(frame: pd.DataFrame) -> None:
    observed = False
    for location, row in _metric_rows("核心指标", frame):
        role = row.get("值类型")
        role = "数值" if _blank_cell(role) else role
        if role not in ("数值", "逻辑", "文本"):
            raise ValueError(f"{location} 值类型必须为数值、逻辑或文本")
        required = row.get("是否必需")
        if not _blank_cell(required) and not isinstance(required, bool):
            raise ValueError(f"{location} 是否必需必须为布尔值")
        value = row["数值"]
        if isinstance(value, Real) and not math.isfinite(value):
            raise ValueError(f"{location} 含非有限值，不能登记为可选缺失")
        if _blank_cell(value):
            if required is not False:
                raise ValueError(f"{location} 缺少必需的指标值")
            reason = row.get("缺失原因")
            if (not isinstance(reason, str) or not _substantive(reason)
                    or reason.strip().casefold() in {"无", "无缺失", "缺失", "数据缺失", "missing", "no missing"}):
                raise ValueError(f"{location} 可选缺失必须在本行登记具体缺失原因")
            continue
        if role == "数值" and not _finite_number(value):
            raise ValueError(f"{location} 数值须为有限数，布尔值和字符串不能替代")
        if role == "逻辑" and not isinstance(value, bool):
            raise ValueError(f"{location} 逻辑指标须为布尔值")
        if role == "文本" and not (isinstance(value, str) and _substantive(value)):
            raise ValueError(f"{location} 文本指标须为非占位的文字")
        observed = True
    if not observed:
        raise ValueError("核心指标至少需要一条有实际观测的指标")


def _check_interval_basis(row: Mapping[str, Any], field: str, location: str) -> None:
    shared = row.get(field)
    lower = row.get("下界" + field)
    upper = row.get("上界" + field)
    if _blank_cell(lower) and _blank_cell(upper):
        return
    lower = shared if _blank_cell(lower) else lower
    upper = shared if _blank_cell(upper) else upper
    declared = [lower, upper] if _blank_cell(shared) else [shared, lower, upper]
    if (not all(isinstance(value, str) and _substantive(value) for value in declared)
            or len({value.strip() for value in declared}) != 1):
        raise ValueError(f"{location} 的上下界{field}必须一致且可识别")


def _check_uncertainty_intervals(frame: pd.DataFrame) -> None:
    for location, row in _metric_rows("不确定性区间", frame):
        lower, upper = row["下界"], row["上界"]
        if not _finite_number(lower) or not _finite_number(upper):
            raise ValueError(f"{location} 的上下界必须为有限数")
        if lower > upper:
            raise ValueError(f"{location} 的下界不得大于上界")
        _check_interval_basis(row, "单位", location)
        _check_interval_basis(row, "统计口径", location)


def _as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "是", "满足", "通过"}:
        return True
    if text in {"false", "0", "no", "否", "不满足", "未通过"}:
        return False
    return None


def _check_residual_consistency(sheet: str, frame: pd.DataFrame) -> None:
    value_column = "违反量" if "违反量" in frame.columns else "残差" if "残差" in frame.columns else None
    if value_column is None or "容差" not in frame.columns or "是否满足" not in frame.columns:
        return
    for index, row in frame.iterrows():
        if pd.isna(row[value_column]) or pd.isna(row["容差"]):
            continue
        expected = abs(float(row[value_column])) <= float(row["容差"])
        actual = _as_bool(row["是否满足"])
        if actual is None or actual != expected:
            raise ValueError(f"工作表“{sheet}”第 {index + 2} 行的是否满足与残差/容差不一致")


def _check_quality_gate(prepared: Sequence[tuple[str, pd.DataFrame]]) -> None:
    frame = next((item for name, item in prepared if name == "主结果质量门"), None)
    if frame is None:
        return
    failed = []
    for _, row in frame.iterrows():
        if _as_bool(row["是否通过"]) is not True:
            failed.append(str(row["检查项"]))
    if failed:
        raise ValueError(f"主结果质量门存在未通过项: {failed}")


def _check_missing_value_audit(prepared: Sequence[tuple[str, pd.DataFrame]], kind: str) -> None:
    if kind != "solution":
        return
    affected = []
    for name, frame in prepared:
        if name == "数据审计":
            continue
        missing = frame.isna()
        if name == "核心指标":
            # Per-row role, presence and omission reasons were checked together.
            missing = missing.drop(columns=["数值", "值类型", "是否必需", "缺失原因"], errors="ignore")
            if "单位" in missing and "值类型" in frame:
                missing.loc[frame["值类型"].isin(["逻辑", "文本"]), "单位"] = False
        if name == "不确定性区间":
            missing = missing.drop(columns=["下界单位", "上界单位", "下界统计口径", "上界统计口径"], errors="ignore")
        if name == "主结果质量门" and {"单位", "判定关系"}.issubset(frame.columns):
            logical_rows = frame["判定关系"].astype(str).str.strip().eq("bool_true")
            missing.loc[logical_rows, "单位"] = False  # A logical criterion has no unit.
        if missing.any().any():
            affected.append(name)
    if not affected:
        return
    audit = next((frame for name, frame in prepared if name == "数据审计"), None)
    if audit is None:
        raise ValueError(f"工作表 {affected} 包含缺失值，但缺少数据审计说明")
    text = " ".join(audit.astype(str).fillna("").to_numpy().ravel()).lower()
    if "缺失" not in text and "missing" not in text:
        raise ValueError(f"工作表 {affected} 包含缺失值，但数据审计未说明缺失处理")


def required_ordinary_sheets(section: Mapping[str, Any], analysis_methods: Sequence[str]) -> set[str]:
    """Resolve the selected method names and aliases to their ordinary evidence sheets."""
    mapping = section.get("ordinary_method_sheets", {})
    methods = {method.strip() for method in analysis_methods if isinstance(method, str)}
    return {mapping[method] for method in methods if method in mapping}


def _check_ordinary_sheets_present(names: set[str], required: set[str]) -> None:
    missing = sorted(required - names)
    if missing:
        raise ValueError(f"结果深化分析缺少已选择的普通证据表: {missing}")


def _check_ordinary_evidence(sheet: str, frame: pd.DataFrame, spec: Mapping[str, Any]) -> None:
    """Confirm that a selected method has at least one substantive observation."""
    columns = spec["required_columns"]
    complete = frame.loc[:, columns].dropna()
    for column in columns:
        if column == "是否可行":
            present = complete[column].map(lambda value: _as_bool(value) is not None)
        else:
            present = complete[column].map(
                lambda value: bool(str(value).strip())
                and (not isinstance(value, Real) or math.isfinite(value))
            )
        complete = complete.loc[present.astype(bool)]
    if complete.empty:
        raise ValueError(f"普通深化证据表“{sheet}”至少需要一条必需字段完整的实质记录")


_PLACEHOLDERS = {
    "", "-", "--", "—", "?", "n/a", "na", "nan", "none", "null", "tbd", "todo",
    "pending", "placeholder", "unknown", "待定", "待填", "待填写", "待运行", "待补",
    "待确认", "暂无", "占位", "占位符", "待验证", "未执行", "未运行", "未完成",
    "#n/a", "#div/0!", "#value!", "#ref!", "#name?", "#num!", "#null!",
}


def _substantive(value: Any) -> bool:
    if not pd.api.types.is_scalar(value) or pd.isna(value):
        return False
    if isinstance(value, str):
        text = value.strip()
        return not text.startswith("=") and text.lower() not in _PLACEHOLDERS
    return not isinstance(value, Real) or math.isfinite(value)


def ordinary_experiment_plan_issues(rows: Any, *, schema: Mapping[str, Any],
                                    analysis_methods: Sequence[str] = ()) -> list[str]:
    """Validate a static source declaration without inspecting returned workbook content."""
    section = schema["result_analysis_workbook"]
    if (section.get("ordinary_experiment_protocol") or {}).get("version") != "1.0.0":
        return ["工作簿schema未声明普通实验协议1.0.0"]
    if not isinstance(rows, list) or not rows:
        return ["ordinary_experiments必须为非空列表"]
    mapping = section["ordinary_method_sheets"]
    issues, ids, registered, required = [], set(), set(), set()
    for index, row in enumerate(rows, 1):
        if not isinstance(row, Mapping):
            issues.append(f"ordinary_experiments第{index}项必须为mapping")
            continue
        label = str(row.get("id") or f"第{index}项")
        if set(row) - {"id", "method", "target", "claim", "required"}:
            issues.append(f"{label}: 未知普通实验字段")
        for field in ("id", "method", "target", "claim"):
            value = row.get(field)
            if not isinstance(value, str) or value != value.strip() or not _substantive(value):
                issues.append(f"{label}: {field}须为实质文本")
        flag = row.get("required", True)
        if not isinstance(flag, bool):
            issues.append(f"{label}: required须为布尔值")
        if label in ids:
            issues.append(f"{label}: 重复检验ID")
        ids.add(label)
        method = row.get("method")
        if not isinstance(method, str) or method not in mapping:
            issues.append(f"{label}: 未登记的普通方法 {method}")
            continue
        registered.add(mapping[method])
        if flag is True:
            required.add(mapping[method])
    if not required:
        issues.append("ordinary_experiments缺少必需实验")
    if analysis_methods:
        selected = required_ordinary_sheets(section, analysis_methods)
        if selected - required:
            issues.append(f"已选择普通方法缺少必需实验: {sorted(selected - required)}")
        if registered - selected:
            issues.append(f"普通实验使用未选择方法: {sorted(registered - selected)}")
    return issues


def _experiment_rows(table: pd.DataFrame | None, identifier: str) -> list[dict[str, Any]]:
    if table is None or "检验ID" not in table:
        return []
    return table.loc[table["检验ID"].eq(identifier)].to_dict("records")


def _observation_present(row: Mapping[str, Any], columns: Sequence[str]) -> bool:
    return all(_substantive(row.get(column))
               and (column != "是否可行" or _as_bool(row[column]) is not None)
               for column in columns)


def _historical_experiment_issues(
    tables: Mapping[str, pd.DataFrame], section: Mapping[str, Any], ordinary_sheets: set[str],
) -> list[str]:
    """Only explicit registrations in active ordinary methods identify historical experiments."""
    design = tables.get("分析设计")
    if design is None or "检验ID" not in design or "方法" not in design:
        return []
    issues = []
    mapping = section.get("ordinary_method_sheets", {})
    for row in design.to_dict("records"):
        sheet = mapping.get(row["方法"])
        identifier = row["检验ID"]
        if sheet not in ordinary_sheets or not isinstance(identifier, str) or not identifier.strip():
            continue
        details = _experiment_rows(tables.get(sheet), identifier)
        columns = section["sheet_schemas"][sheet]["required_columns"]
        if not any(_observation_present(item, columns) for item in details):
            issues.append(f"{identifier}: 缺少{sheet}实质观测")
    return issues


def _unregistered_claim_issues(
    summary: pd.DataFrame | None, registered_ids: set[str], comparison_methods: Mapping[str, Any],
) -> list[str]:
    if summary is None or "主张处置" not in summary:
        return []
    issues = []
    for row in summary.to_dict("records"):
        identifier = row.get("检验ID")
        if (row.get("分析方法") not in comparison_methods and identifier not in registered_ids
                and _substantive(row.get("主张处置"))):
            issues.append(f"{identifier}: 未登记的普通实验不能处置主张 {row.get('核心结论')}")
    return issues


def _registered_claim_issues(
    claims: Sequence[Mapping[str, Any]], experiment: Mapping[str, Any], section: Mapping[str, Any], sheet: str,
) -> list[str]:
    if len(claims) != 1:
        return ["缺少唯一主张及处置"]
    claim = claims[0]
    mapping = section["ordinary_method_sheets"]
    issues = []
    if (claim.get("核心结论") != experiment["claim"] or mapping.get(claim.get("分析方法")) != sheet
            or claim.get("证据工作表") != sheet or not _substantive(claim.get("稳定范围"))):
        issues.append("主张、方法、证据工作表或稳定范围不匹配")
    disposition, retained = claim.get("主张处置"), _as_bool(claim.get("是否保持"))
    if disposition not in section["ordinary_experiment_protocol"]["dispositions"] or retained is None:
        issues.append("缺少有效主张处置或是否保持")
    elif (disposition == "support" and not retained) or (disposition == "reject" and retained):
        issues.append("主张处置与是否保持矛盾")
    return issues


def _registered_experiment_issues(
    tables: Mapping[str, pd.DataFrame], section: Mapping[str, Any], experiment: Mapping[str, Any],
) -> list[str]:
    identifier = experiment["id"]
    mapping = section["ordinary_method_sheets"]
    sheet = mapping[experiment["method"]]
    comparison_methods = section.get("comparison_method_sheets", {})
    designs = [row for row in _experiment_rows(tables.get("分析设计"), identifier)
               if row.get("方法") not in comparison_methods]
    claims = [row for row in _experiment_rows(tables.get("结论稳定性汇总"), identifier)
              if row.get("分析方法") not in comparison_methods]
    details = _experiment_rows(tables.get(sheet), identifier)
    statuses = section["ordinary_experiment_protocol"]["observation_statuses"]
    evidence_columns = section["sheet_schemas"][sheet]["required_columns"]
    issues = []
    if any(row.get("观测状态") not in statuses for row in details):
        issues.append("未知或缺少观测状态")
    observed = [_observation_present(row, evidence_columns) for row in details
                if row.get("观测状态") == "completed"]
    if not all(observed):
        issues.append("completed行缺少实质观测")
    # An optional failed/exploratory attempt carries no scientific verdict.
    if not experiment.get("required", True) and not any(_substantive(row.get("主张处置")) for row in claims):
        return issues
    design_columns = section["sheet_schemas"]["分析设计"]["required_columns"]
    if (len(designs) != 1 or mapping.get(designs[0].get("方法")) != sheet
            or designs[0].get("分析问题") != experiment["target"]
            or not all(_substantive(designs[0].get(column)) for column in design_columns)):
        issues.append("缺少与预登记方法和目标一致的唯一设计")
    if not any(observed):
        issues.append(f"缺少{sheet}的completed实质观测")
    issues.extend(_registered_claim_issues(claims, experiment, section, sheet))
    return issues


def _check_experiment_coverage(tables: Mapping[str, pd.DataFrame], section: Mapping[str, Any],
                               ordinary_sheets: set[str], experiments: Sequence[Mapping[str, Any]] | None) -> None:
    if experiments is None:
        issues = _historical_experiment_issues(tables, section, ordinary_sheets)
    else:
        issues = _unregistered_claim_issues(
            tables.get("结论稳定性汇总"), {row["id"] for row in experiments}, section.get("comparison_method_sheets", {}),
        )
        for experiment in experiments:
            prefix = f"{experiment['id']}（主张：{experiment['claim']}）"
            issues.extend(f"{prefix}: {issue}" for issue in _registered_experiment_issues(tables, section, experiment))
    if issues:
        raise ValueError("；".join(issues))


def _check_required_comparison_sheets(
    names: set[str], section: Mapping[str, Any], analysis_methods: Sequence[str],
    comparison_plan: Mapping[str, Any] | None,
) -> None:
    """Require each selected method and required check's own evidence table."""
    mapping = section.get("comparison_method_sheets", {})
    required = {mapping[method] for method in analysis_methods if method in mapping}
    for check in (comparison_plan or {}).get("checks", []):
        if check.get("requirement") == "required" and check.get("kind") in mapping:
            required.add(mapping[check["kind"]])
    missing = sorted(required - names)
    if missing:
        raise ValueError(f"结果深化分析缺少已选择的比较证据表: {missing}")


def _check_comparison_values(sheet: str, frame: pd.DataFrame, spec: Mapping[str, Any]) -> None:
    """Check complete comparison records and literal finite numerical values."""
    for column in spec["required_columns"]:
        if frame[column].isna().any() or frame[column].astype(str).str.strip().eq("").any():
            raise ValueError(f"比较表“{sheet}”必需字段“{column}”存在空值")
    numeric = ("主模型数值", "对照模型数值", "差异") if sheet == "多模型检验" else ("基准数值", "对照数值", "差异")
    for column in numeric:
        if not frame[column].map(lambda value: isinstance(value, Real) and not isinstance(value, bool) and math.isfinite(value)).all():
            raise ValueError(f"比较表“{sheet}”字段“{column}”必须为真实有限数值")


class _AnalysisOptions(NamedTuple):
    analysis_methods: Sequence[str] = ()
    comparison_plan: Mapping[str, Any] | None = None
    ordinary_experiments: Sequence[Mapping[str, Any]] | None = None
    require_ordinary_method_coverage: bool = True


def _check_solution_profiles(
    names: set[str], schema: Mapping[str, Any], problem_types: Sequence[str],
    capabilities: Mapping[str, bool] | None, objective: str | None, structures: Sequence[str],
) -> None:
    required = _conditional_required_sheets(schema, problem_types, capabilities)
    missing_conditional = sorted(required - names)
    if missing_conditional:
        active = sorted(name for name, enabled in (capabilities or {}).items() if enabled)
        note = f"；启用的capabilities: {active}" if active else ""
        raise ValueError(f"求解工作簿缺少必需工作表: {missing_conditional}{note}")
    for profile, required_any in _profile_requirements(schema, objective, structures, problem_types):
        if required_any and not names.intersection(required_any):
            raise ValueError(f"分类剖面“{profile}”至少需要一个专项工作表: {sorted(required_any)}")


def _check_analysis_sheet_names(
    names: set[str], section: Mapping[str, Any], sheet_schemas: Mapping[str, Any],
    ordinary_sheets: set[str], options: _AnalysisOptions,
) -> None:
    allowed_any = set(section.get("required_any_sheets", []))
    allowed_all = set(sheet_schemas)
    unknown_sheets = sorted(names - allowed_all)
    if unknown_sheets:
        raise ValueError(f"结果深化分析工作簿包含未登记工作表: {unknown_sheets}")
    if options.require_ordinary_method_coverage:
        _check_ordinary_sheets_present(names, ordinary_sheets)
    if not names.intersection(allowed_any):
        raise ValueError(f"结果深化分析工作簿至少需要一个实质分析表: {sorted(allowed_any)}")
    _check_required_comparison_sheets(names, section, options.analysis_methods, options.comparison_plan)


def validate_tables(
    tables: Mapping[str, Any],
    workbook_kind: str,
    *,
    schema: Mapping[str, Any],
    problem_types: Sequence[str] = (),
    capabilities: Mapping[str, bool] | None = None,
    objective: str | None = None,
    structures: Sequence[str] = (),
    name_normalizer: Callable[[str], str] | None = None,
    require_quality_passed: bool = True,
    **analysis_options: Any,
) -> list[tuple[str, pd.DataFrame]]:
    """Validate in-memory tables with the same analysis keywords as validate_workbook_file."""
    options = _AnalysisOptions(**analysis_options)
    kind = _normalize_kind(workbook_kind)
    if options.ordinary_experiments is not None:
        if kind != "result_analysis":
            raise ValueError("普通实验协议仅用于结果深化分析工作簿")
        issues = ordinary_experiment_plan_issues(
            options.ordinary_experiments, schema=schema,
            analysis_methods=options.analysis_methods if options.require_ordinary_method_coverage else (),
        )
        if issues:
            raise ValueError("；".join(issues))
    prepared = prepare_tables(tables, name_normalizer=name_normalizer, allow_empty=options.ordinary_experiments is not None)
    required_sheets, sheet_schemas = _required_sheet_schemas(schema, kind)
    names = {name for name, _ in prepared}
    ordinary_sheets: set[str] = set()
    if kind == "result_analysis" and (options.ordinary_experiments is not None or options.require_ordinary_method_coverage):
        section = schema["result_analysis_workbook"]
        ordinary_sheets = required_ordinary_sheets(section, options.analysis_methods)
        _check_experiment_coverage(dict(prepared), section, ordinary_sheets, options.ordinary_experiments)
    if any(frame.empty for _, frame in prepared):
        raise ValueError("禁止写入空工作表")
    missing = sorted(required_sheets - names)
    if missing:
        label = "求解" if kind == "solution" else "结果深化分析"
        raise ValueError(f"{label}工作簿缺少必需工作表: {missing}")
    if kind == "solution":
        _check_solution_profiles(names, schema, problem_types, capabilities, objective, structures)
    else:
        section = schema["result_analysis_workbook"]
        _check_analysis_sheet_names(names, section, sheet_schemas, ordinary_sheets, options)
    for name, frame in prepared:
        if name in sheet_schemas:
            _check_required_columns(name, frame, sheet_schemas[name])
        if kind == "solution" and name == "核心指标":
            _check_core_metrics(frame)
        if kind == "solution" and name == "不确定性区间":
            _check_uncertainty_intervals(frame)
        _check_record_keys(name, frame)
        _check_finite_numbers(name, frame)
        _check_residual_consistency(name, frame)
        if name in ordinary_sheets:
            _check_ordinary_evidence(name, frame, sheet_schemas[name])
        if kind == "result_analysis" and name in set(section.get("comparison_method_sheets", {}).values()):
            _check_comparison_values(name, frame, sheet_schemas[name])
    if kind == "solution" and require_quality_passed:
        _check_quality_gate(prepared)
    _check_missing_value_audit(prepared, kind)
    return prepared


def validate_ordinary_method_coverage(
    path: Path | bytes, *, schema: Mapping[str, Any], analysis_methods: Sequence[str],
) -> None:
    """Check selected evidence sheets without imposing new schemas on unrelated legacy sheets."""
    section = schema["result_analysis_workbook"]
    required = required_ordinary_sheets(section, analysis_methods)
    if not required:
        return
    tables = read_workbook_tables(path, only_sheets=required)
    _check_ordinary_sheets_present(set(tables), required)
    for sheet, frame in tables.items():
        spec = section["sheet_schemas"][sheet]
        _check_required_columns(sheet, frame, spec)
        _check_ordinary_evidence(sheet, frame, spec)


def validate_workbook_file(
    path: Path | bytes,
    workbook_kind: str,
    *,
    schema: Mapping[str, Any],
    problem_types: Sequence[str] = (),
    capabilities: Mapping[str, bool] | None = None,
    objective: str | None = None,
    structures: Sequence[str] = (),
    require_quality_passed: bool = True,
    analysis_methods: Sequence[str] = (),
    comparison_plan: Mapping[str, Any] | None = None,
    ordinary_experiments: Sequence[Mapping[str, Any]] | None = None,
    require_ordinary_method_coverage: bool = True,
) -> list[tuple[str, pd.DataFrame]]:
    if not isinstance(path, bytes):
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(path)
    return validate_tables(
        read_workbook_tables(path, allow_empty=ordinary_experiments is not None), workbook_kind, schema=schema,
        problem_types=problem_types, capabilities=capabilities,
        objective=objective, structures=structures,
        require_quality_passed=require_quality_passed,
        analysis_methods=analysis_methods, comparison_plan=comparison_plan,
        ordinary_experiments=ordinary_experiments,
        require_ordinary_method_coverage=require_ordinary_method_coverage,
    )


def validate_pair(
    solution_path: Path | None,
    result_analysis_path: Path | None,
    *,
    schema: Mapping[str, Any],
    require_solution: bool,
    require_result_analysis: bool = False,
    require_robustness: bool | None = None,
    problem_types: Sequence[str] = (),
    capabilities: Mapping[str, bool] | None = None,
    objective: str | None = None,
    structures: Sequence[str] = (),
    require_quality_passed: bool = True,
) -> list[str]:
    if require_robustness is not None:
        require_result_analysis = require_robustness
    issues: list[str] = []
    if require_solution and (solution_path is None or not Path(solution_path).is_file()):
        issues.append("缺少标准求解结果工作簿")
    if require_result_analysis and (
        result_analysis_path is None or not Path(result_analysis_path).is_file()
    ):
        issues.append("缺少标准结果深化分析工作簿")
    for path, kind in ((solution_path, "solution"), (result_analysis_path, "result_analysis")):
        if path is None or not Path(path).is_file():
            continue
        try:
            validate_workbook_file(
                Path(path), kind, schema=schema, problem_types=problem_types,
                capabilities=capabilities, objective=objective, structures=structures,
                require_quality_passed=require_quality_passed if kind == "solution" else True,
            )
        except Exception as exc:  # noqa: BLE001
            issues.append(f"{Path(path).name}: {exc}")
    return issues
