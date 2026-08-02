from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from hsk_pipeline import (
    AuditLog,
    ModelContext,
    PipelineConfig,
    PrimarySolveResult,
    REQUIRED_CAPABILITIES,
    run_primary_pipeline,
)
from hsk_pipeline.result_io import find_project_root

INPUT_FILE = "__INPUT_FILE__"
FRAMEWORK_SECTION = "### Q1：__QUESTION_NAME__"
PROBLEM_NAME = "问题一"


def capabilities(**enabled: bool) -> dict[str, bool]:
    unknown = sorted(set(enabled) - REQUIRED_CAPABILITIES)
    if unknown:
        raise ValueError(f"未知 capability: {unknown}")
    values = {name: False for name in REQUIRED_CAPABILITIES}
    values.update(enabled)
    return values


def build_config(script_path: Path) -> PipelineConfig:
    project_root = find_project_root(script_path)
    return PipelineConfig(
        project_root=project_root,
        framework_path=project_root / "模型论文框架.md",
        framework_section=FRAMEWORK_SECTION,
        problem_name=PROBLEM_NAME,
        objective="evaluation",
        structures=("static_tabular",),
        capabilities=capabilities(),
        random_seed=2026,
    )


def load_data(config: PipelineConfig, audit: AuditLog) -> dict[str, pd.DataFrame]:
    raise NotImplementedError("请读取评价对象、指标和单位并检查正负向与缺失值")


def preprocess_data(
    raw_data: dict[str, pd.DataFrame],
    config: PipelineConfig,
    audit: AuditLog,
) -> dict[str, pd.DataFrame]:
    raise NotImplementedError("请依据指标含义完成无量纲化、正向化和异常处理")


def build_features(clean_data: dict[str, pd.DataFrame], config: PipelineConfig) -> dict[str, Any]:
    raise NotImplementedError("请构造评价矩阵、权重输入和等级或排序口径")


def solve_model(features: dict[str, Any], config: PipelineConfig) -> dict[str, Any]:
    raise NotImplementedError("请计算主评价结果并输出综合评分、排序结果和必要权重明细")


def check_constraints(solution: dict[str, Any], config: PipelineConfig) -> pd.DataFrame | None:
    return None


def evaluate_primary_quality(
    context: ModelContext,
    constraints: pd.DataFrame | None,
) -> pd.DataFrame:
    raise NotImplementedError(
        "请检查指标方向、标准化、权重和评分计算闭环、排名并列规则和可复算性，"
        "返回检查项/是否通过/证据"
    )


def sync_primary_framework(primary: PrimarySolveResult) -> None:
    raise NotImplementedError("回写主评价模型、评分与排名、质量门结论和证据")


def main() -> None:
    config = build_config(Path(__file__))
    run_primary_pipeline(
        config,
        load_data_hook=load_data,
        preprocess_hook=preprocess_data,
        build_features_hook=build_features,
        solve_hook=solve_model,
        constraint_hook=check_constraints,
        quality_hook=evaluate_primary_quality,
        framework_sync_hook=sync_primary_framework,
    )


if __name__ == "__main__":
    main()
