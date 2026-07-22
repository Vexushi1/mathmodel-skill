"""可选生成 MATLAB 图表数据映射；真实数据仍以两类标准工作簿为准。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_matlab_handoff(
    project_root: Path,
    problem_name: str,
    figures: list[dict[str, Any]],
) -> Path:
    result_dir = Path(project_root) / "结果数据表" / problem_name
    solve_book = result_dir / f"{problem_name}求解结果.xlsx"
    robust_book = result_dir / f"{problem_name}敏感性与鲁棒性结果.xlsx"

    for path in (solve_book, robust_book):
        if not path.exists():
            raise FileNotFoundError(path)

    normalized = []
    for spec in figures:
        required = {"figure_id", "workbook", "worksheet", "matlab_script"}
        missing = required - set(spec)
        if missing:
            raise ValueError(f"图表映射缺少字段: {sorted(missing)}")
        normalized.append(dict(spec))

    result_dir.mkdir(parents=True, exist_ok=True)
    path = result_dir / "matlab_figure_handoff.json"
    payload = {
        "version": "6.2.4",
        "problem": problem_name,
        "result_directory": result_dir.as_posix(),
        "solution_workbook": solve_book.as_posix(),
        "sensitivity_robustness_workbook": robust_book.as_posix(),
        "matlab_script_location": f"{result_dir.as_posix()}/q{{x}}_plot.m",
        "figure_directory": f"{result_dir.as_posix()}/图表",
        "figures": normalized,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
