"""可选生成 MATLAB 图表数据映射；真实数据仍以两类标准工作簿为准。"""
from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any


PLOT_SCRIPT_PATTERN = re.compile(r"^Q[1-9][0-9]*_plot\.m$")
ALLOWED_COMPOSITION_LEVELS = {"single", "layered", "multi-panel", "hybrid"}
REQUIRED_FIGURE_FIELDS = {
    "figure_id",
    "workbook",
    "worksheet",
    "matlab_script",
    "local_plot_function",
    "composition_level",
    "layer_map",
    "axis_contract",
    "panel_map",
    "shared_color_mapping",
    "rendering_transforms",
}


def write_matlab_handoff(project_root: Path, problem_name: str, figures: list[dict[str, Any]]) -> Path:
    result_dir = project_root / "结果数据表" / problem_name / f"{problem_name}结果数据"
    solve_book = result_dir / f"{problem_name}求解结果.xlsx"
    robust_book = result_dir / f"{problem_name}敏感性与鲁棒性结果.xlsx"
    for path in (solve_book, robust_book):
        if not path.exists():
            raise FileNotFoundError(path)
    if not figures:
        raise ValueError("图表映射不能为空")

    normalized: list[dict[str, Any]] = []
    script_names: set[str] = set()
    for spec in figures:
        missing = REQUIRED_FIGURE_FIELDS - set(spec)
        if missing:
            raise ValueError(f"图表映射缺少字段: {sorted(missing)}")

        composition_level = str(spec["composition_level"])
        if composition_level not in ALLOWED_COMPOSITION_LEVELS:
            raise ValueError(
                f"composition_level 必须为 {sorted(ALLOWED_COMPOSITION_LEVELS)} 之一: "
                f"{composition_level}"
            )

        for field in (
            "figure_id",
            "workbook",
            "worksheet",
            "matlab_script",
            "local_plot_function",
            "layer_map",
            "axis_contract",
            "panel_map",
            "shared_color_mapping",
            "rendering_transforms",
        ):
            if not str(spec[field]).strip():
                raise ValueError(f"图表映射字段不得为空: {field}")

        script_name = Path(str(spec["matlab_script"])).name
        if not PLOT_SCRIPT_PATTERN.fullmatch(script_name):
            raise ValueError(f"MATLAB 绘图文件必须命名为 QX_plot.m: {script_name}")
        script_names.add(script_name)
        normalized.append(dict(spec))

    if len(script_names) != 1:
        raise ValueError(f"同一问题只能映射到一个 MATLAB 绘图文件: {sorted(script_names)}")

    out_dir = project_root / "MATLAB绘图" / problem_name
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "matlab_figure_handoff.json"
    payload = {
        "version": "6.2.2",
        "problem": problem_name,
        "solution_workbook": solve_book.as_posix(),
        "sensitivity_robustness_workbook": robust_book.as_posix(),
        "matlab_plot_script": next(iter(script_names)),
        "allowed_composition_levels": sorted(ALLOWED_COMPOSITION_LEVELS),
        "figures": normalized,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
