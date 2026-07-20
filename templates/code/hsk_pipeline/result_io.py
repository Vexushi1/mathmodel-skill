"""统一定位项目根目录并写入每问两类中文 Excel 结果工作簿。"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

INVALID_SHEET_CHARS = set('[]:*?/\\')
PROBLEM_PATTERN = re.compile(r"问题[一二三四五六七八九十百]+")


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
    safe = ''.join('_' if ch in INVALID_SHEET_CHARS else ch for ch in str(name)).strip()
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
    return frame


def write_workbook(path: Path, tables: Mapping[str, Any]) -> Path:
    if not tables:
        raise ValueError(f"没有可写入的结果表: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    used: set[str] = set()
    prepared: list[tuple[str, pd.DataFrame]] = []
    for raw_name, value in tables.items():
        name = _sheet_name(raw_name)
        if name in used:
            raise ValueError(f"工作表名称截断后重复: {name}")
        used.add(name)
        prepared.append((name, _to_frame(value)))
    with pd.ExcelWriter(path, engine="openpyxl", mode="w") as writer:
        for name, frame in prepared:
            frame.to_excel(writer, sheet_name=name, index=False)
    return path
