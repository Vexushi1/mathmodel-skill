"""可选生成 MATLAB 图表映射；数值事实来自主求解与结果深化分析工作簿。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = {
    "figure_id",
    "matlab_title",
    "paper_caption",
    "workbook",
    "worksheet",
    "required_headers",
    "matlab_script",
    "framework_registry",
}
OPTIONAL_FIELDS = {"expected_column_positions", "units", "schema_hash"}


def write_matlab_handoff(
    project_root: Path,
    problem_name: str,
    figures: list[dict[str, Any]],
) -> Path:
    result_dir = Path(project_root) / "结果数据表" / problem_name
    solve_book = result_dir / f"{problem_name}求解结果.xlsx"
    analysis_book = result_dir / f"{problem_name}结果深化分析.xlsx"
    for path in (solve_book, analysis_book):
        if not path.exists():
            raise FileNotFoundError(path)
    allowed_books = {solve_book.name, analysis_book.name}
    normalized = []
    for spec in figures:
        missing = REQUIRED_FIELDS - set(spec)
        if missing:
            raise ValueError(f"图表映射缺少字段: {sorted(missing)}")
        unknown = set(spec) - REQUIRED_FIELDS - OPTIONAL_FIELDS
        if unknown:
            raise ValueError(f"图表映射包含未知字段: {sorted(unknown)}")
        title = str(spec["matlab_title"]).strip()
        caption = str(spec["paper_caption"]).strip()
        workbook = Path(str(spec["workbook"])).name
        if workbook not in allowed_books:
            raise ValueError(f"workbook 必须是本问主求解或结果深化分析工作簿: {workbook}")
        if not title:
            raise ValueError("matlab_title 不能为空")
        if len(title) > 30:
            raise ValueError("matlab_title 过长，应只保留研究对象、指标关系和必要方法信息")
        if not caption:
            raise ValueError("paper_caption 不能为空")
        if title == caption:
            raise ValueError("paper_caption 不得与 matlab_title 逐字重复")
        headers = [str(item).strip() for item in spec["required_headers"]]
        if not headers or any(not item for item in headers) or len(headers) != len(set(headers)):
            raise ValueError("required_headers 必须为非空且唯一的真实表头")
        normalized.append({**dict(spec), "workbook": workbook, "required_headers": headers})
    result_dir.mkdir(parents=True, exist_ok=True)
    path = result_dir / "matlab_figure_handoff.json"
    payload = {
        "version": "6.4.1",
        "problem": problem_name,
        "result_directory": result_dir.as_posix(),
        "solution_workbook": solve_book.as_posix(),
        "result_analysis_workbook": analysis_book.as_posix(),
        "model_paper_framework": (Path(project_root) / "模型论文框架.md").as_posix(),
        "matlab_script_location": f"{result_dir.as_posix()}/q{{x}}_plot.m",
        "figure_directory": f"{result_dir.as_posix()}/图表",
        "field_resolution": "exact_header_unique_match",
        "expected_column_position_role": "optional_drift_warning",
        "title_policy": {
            "single_panel": "title",
            "multi_panel": "sgtitle",
            "keep_in_export": True,
            "caption_must_supplement_not_duplicate": True,
        },
        "figures": normalized,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
