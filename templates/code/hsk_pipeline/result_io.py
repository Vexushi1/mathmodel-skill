"""统一定位项目根目录、校验工作簿契约并写入每问两类中文 Excel 结果工作簿。"""
from __future__ import annotations

import math
import os
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd
import yaml

INVALID_SHEET_CHARS = set('[]:*?/\\')
PROBLEM_PATTERN = re.compile(r"问题[一二三四五六七八九十百]+")
VALID_WORKBOOK_KINDS = {"solution", "robustness"}

_FALLBACK_SCHEMA: dict[str, Any] = {
    "global_rules": {"empty_worksheet_allowed": False},
    "solution_workbook": {
        "common_required_sheets": {
            "核心指标": {"required_columns": ["指标", "数值"]},
            "数据审计": {"required_columns": ["等级", "检查项", "信息", "处理方式"]},
        },
        "common_recommended_sheets": {
            "推荐方案": {"required_columns": ["方案"]},
            "明细结果": {"required_columns": ["记录键"]},
            "多算法对比": {"required_columns": ["算法", "目标值", "可行性"]},
            "约束违反检查": {
                "required_columns": ["约束编号", "约束含义", "违反量", "容差", "是否满足"]
            },
        },
        "conditional_requirements": {
            "constraint_based_problem_types": {
                "problem_types": [
                    "mechanism",
                    "optimization",
                    "simulation",
                    "graph_network",
                    "scheduling",
                    "game_decision",
                ],
                "required_sheets": ["约束违反检查"],
            }
        },
        "task_profiles": {},
    },
    "sensitivity_robustness_workbook": {
        "required_any_sheets": ["参数敏感性", "鲁棒性区间", "扰动明细", "算法稳定性", "适用性说明"],
        "sheet_schemas": {
            "参数敏感性": {"required_columns": ["参数", "基准值", "扰动值", "目标指标"]},
            "鲁棒性区间": {"required_columns": ["指标", "下界", "上界"]},
            "扰动明细": {"required_columns": ["扰动编号", "扰动对象", "扰动值", "结果指标"]},
            "算法稳定性": {"required_columns": ["算法", "重复编号", "目标值", "是否可行"]},
            "适用性说明": {"required_columns": ["分析类型", "不适用原因", "替代检验"]},
        },
    },
}


def find_project_root(start: Path) -> Path:
    """从脚本位置向上查找项目根目录，兼容脚本位于 Python求解/ 或其子目录。"""
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for _ in range(12):
        if current.name == "Python求解":
            return current.parent
        markers = (
            (current / "Python求解").is_dir(),
            (current / "数据").is_dir(),
            (current / "结果数据表").is_dir(),
            (current / "MATLAB绘图").is_dir(),
        )
        if sum(markers) >= 2:
            return current
        if current.parent == current:
            break
        current = current.parent
    raise FileNotFoundError("未找到项目根目录；应包含 Python求解/、数据/、结果数据表/ 或 MATLAB绘图/ 中至少两个目录")


def result_data_dir(project_root: Path, problem_name: str) -> Path:
    if not PROBLEM_PATTERN.fullmatch(problem_name):
        raise ValueError("problem_name 应为问题一、问题二等中文名称")
    path = project_root / "结果数据表" / problem_name / f"{problem_name}结果数据"
    path.mkdir(parents=True, exist_ok=True)
    return path


def workbook_paths(project_root: Path, problem_name: str) -> tuple[Path, Path]:
    base = result_data_dir(project_root, problem_name)
    return (
        base / f"{problem_name}求解结果.xlsx",
        base / f"{problem_name}敏感性与鲁棒性结果.xlsx",
    )


def not_applicable_table(
    reason: str,
    analysis_type: str = "敏感性与鲁棒性分析",
    alternative_test: str = "边界条件、有效性或一致性检查",
    evidence_location: str = "",
) -> pd.DataFrame:
    """生成符合 workbook_schema 的非空“适用性说明”记录。"""
    reason_text = str(reason).strip()
    analysis_text = str(analysis_type).strip()
    alternative_text = str(alternative_test).strip()
    if not reason_text or not analysis_text or not alternative_text:
        raise ValueError("分析类型、不适用原因和替代检验均不能为空")
    data = {
        "分析类型": [analysis_text],
        "不适用原因": [reason_text],
        "替代检验": [alternative_text],
    }
    location = str(evidence_location).strip()
    if location:
        data["证据位置"] = [location]
    return pd.DataFrame(data)


def _sheet_name(name: str) -> str:
    safe = "".join("_" if ch in INVALID_SHEET_CHARS else ch for ch in str(name)).strip()
    if not safe:
        raise ValueError("工作表名称不能为空")
    return safe[:31]


def _to_frame(value: Any) -> pd.DataFrame:
    if isinstance(value, pd.DataFrame):
        frame = value.copy()
    elif isinstance(value, Mapping):
        frame = pd.DataFrame([dict(value)])
    elif isinstance(value, (list, tuple)):
        frame = pd.DataFrame(value)
    else:
        frame = pd.DataFrame({"数值": [value]})
    if frame.empty:
        raise ValueError("禁止写入空工作表；不适用时请使用 not_applicable_table() 说明原因")
    if len(frame.columns) == 0:
        raise ValueError("工作表至少需要一个字段")
    if frame.columns.duplicated().any():
        duplicate = frame.columns[frame.columns.duplicated()].tolist()
        raise ValueError(f"工作表包含重复字段: {duplicate}")
    return frame


def _schema_candidates(explicit: Path | None) -> list[Path]:
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(explicit)
    env_path = os.getenv("HSK_WORKBOOK_SCHEMA")
    if env_path:
        candidates.append(Path(env_path))
    for parent in Path(__file__).resolve().parents:
        candidates.append(parent / "core" / "workbook_schema.yaml")
    return candidates


def load_workbook_schema(schema_path: Path | None = None) -> dict[str, Any]:
    """优先读取仓库机器契约；独立复制模板时退回最小兼容契约。"""
    for candidate in _schema_candidates(schema_path):
        if candidate.is_file():
            payload = yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
            if "solution_workbook" in payload and "sensitivity_robustness_workbook" in payload:
                return payload
    return _FALLBACK_SCHEMA


def _required_sheet_schemas(schema: Mapping[str, Any], kind: str) -> tuple[set[str], dict[str, Mapping[str, Any]]]:
    if kind == "solution":
        section = schema["solution_workbook"]
        required_map = dict(section.get("common_required_sheets", {}))
        all_schemas = {**required_map, **dict(section.get("common_recommended_sheets", {}))}
        return set(required_map), all_schemas
    section = schema["sensitivity_robustness_workbook"]
    return set(), dict(section.get("sheet_schemas", {}))


def _conditional_required_sheets(
    schema: Mapping[str, Any], problem_types: Sequence[str]
) -> set[str]:
    required: set[str] = set()
    section = schema.get("solution_workbook", {})
    selected = set(problem_types)
    for config in section.get("conditional_requirements", {}).values():
        if selected.intersection(config.get("problem_types", [])):
            required.update(config.get("required_sheets", []))
    return required


def _check_required_columns(sheet: str, frame: pd.DataFrame, spec: Mapping[str, Any]) -> None:
    required = [str(column) for column in spec.get("required_columns", [])]
    missing = [column for column in required if column not in frame.columns]
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


def validate_workbook_tables(
    tables: Mapping[str, Any],
    workbook_kind: str,
    problem_types: Sequence[str] = (),
    schema_path: Path | None = None,
) -> list[tuple[str, pd.DataFrame]]:
    """按 workbook_schema 校验工作表、字段、主键和数值有效性。"""
    if workbook_kind not in VALID_WORKBOOK_KINDS:
        raise ValueError(f"workbook_kind 必须为 {sorted(VALID_WORKBOOK_KINDS)}")
    if not tables:
        raise ValueError("没有可写入的结果表")

    prepared: list[tuple[str, pd.DataFrame]] = []
    used: set[str] = set()
    for raw_name, value in tables.items():
        name = _sheet_name(raw_name)
        if name in used:
            raise ValueError(f"工作表名称截断后重复: {name}")
        used.add(name)
        prepared.append((name, _to_frame(value)))

    schema = load_workbook_schema(schema_path)
    required_sheets, sheet_schemas = _required_sheet_schemas(schema, workbook_kind)
    names = {name for name, _ in prepared}

    if workbook_kind == "solution":
        required_sheets.update(_conditional_required_sheets(schema, problem_types))
        missing = sorted(required_sheets - names)
        if missing:
            raise ValueError(f"求解工作簿缺少必需工作表: {missing}")
        profiles = schema.get("solution_workbook", {}).get("task_profiles", {})
        for problem_type in problem_types:
            required_any = set(profiles.get(problem_type, {}).get("required_any", []))
            if required_any and not names.intersection(required_any):
                raise ValueError(
                    f"题型“{problem_type}”至少需要一个专项工作表: {sorted(required_any)}"
                )
    else:
        allowed_any = set(schema["sensitivity_robustness_workbook"].get("required_any_sheets", []))
        if not names.intersection(allowed_any):
            raise ValueError(f"敏感性与鲁棒性工作簿至少需要一个工作表: {sorted(allowed_any)}")

    for name, frame in prepared:
        spec = sheet_schemas.get(name)
        if spec:
            _check_required_columns(name, frame, spec)
        _check_record_keys(name, frame)
        _check_finite_numbers(name, frame)
    return prepared


def _infer_workbook_kind(path: Path) -> str | None:
    if "敏感性与鲁棒性" in path.name:
        return "robustness"
    if "求解结果" in path.name:
        return "solution"
    return None


def write_workbook(
    path: Path,
    tables: Mapping[str, Any],
    *,
    workbook_kind: str | None = None,
    problem_types: Sequence[str] = (),
    schema_path: Path | None = None,
) -> Path:
    """写入前执行统一契约校验；标准文件名可自动识别工作簿类型。"""
    kind = workbook_kind or _infer_workbook_kind(path)
    if kind is None:
        prepared = []
        used: set[str] = set()
        for raw_name, value in tables.items():
            name = _sheet_name(raw_name)
            if name in used:
                raise ValueError(f"工作表名称截断后重复: {name}")
            used.add(name)
            frame = _to_frame(value)
            _check_record_keys(name, frame)
            _check_finite_numbers(name, frame)
            prepared.append((name, frame))
    else:
        prepared = validate_workbook_tables(
            tables,
            workbook_kind=kind,
            problem_types=problem_types,
            schema_path=schema_path,
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl", mode="w") as writer:
        for name, frame in prepared:
            frame.to_excel(writer, sheet_name=name, index=False)
    return path
