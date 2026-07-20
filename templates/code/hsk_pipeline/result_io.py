"""统一写入每问两类中文 Excel 结果工作簿。"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Mapping
import pandas as pd

INVALID_SHEET_CHARS = set('[]:*?/\\')


def result_data_dir(project_root: Path, problem_name: str) -> Path:
    if not problem_name.startswith("问题"):
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


def _sheet_name(name: str) -> str:
    safe = ''.join('_' if ch in INVALID_SHEET_CHARS else ch for ch in str(name)).strip()
    if not safe:
        raise ValueError("工作表名称不能为空")
    return safe[:31]


def _to_frame(value: Any) -> pd.DataFrame:
    if isinstance(value, pd.DataFrame):
        return value
    if isinstance(value, Mapping):
        return pd.DataFrame([dict(value)])
    if isinstance(value, (list, tuple)):
        return pd.DataFrame(value)
    return pd.DataFrame({"数值": [value]})


def write_workbook(path: Path, tables: Mapping[str, Any]) -> Path:
    if not tables:
        raise ValueError(f"没有可写入的结果表: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    used: set[str] = set()
    with pd.ExcelWriter(path, engine="openpyxl", mode="w") as writer:
        for raw_name, value in tables.items():
            name = _sheet_name(raw_name)
            if name in used:
                raise ValueError(f"工作表名称截断后重复: {name}")
            used.add(name)
            _to_frame(value).to_excel(writer, sheet_name=name, index=False)
    return path
