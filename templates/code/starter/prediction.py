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
        objective="prediction",
        structures=("temporal",),
        capabilities=capabilities(
            requires_out_of_sample_validation=True,
            requires_leakage_check=True,
        ),
        random_seed=2026,
    )


def load_data(config: PipelineConfig, audit: AuditLog) -> dict[str, pd.DataFrame]:
    raise NotImplementedError("请读取真实预测数据并记录时间范围、粒度和目标变量")


def preprocess_data(
    raw_data: dict[str, pd.DataFrame],
    config: PipelineConfig,
    audit: AuditLog,
) -> dict[str, pd.DataFrame]:
    raise NotImplementedError("请按时间顺序完成缺失、异常、滞后和数据泄漏检查")


def build_features(clean_data: dict[str, pd.DataFrame], config: PipelineConfig) -> dict[str, Any]:
    raise NotImplementedError("请构造只使用预测时点可获得信息的特征和滚动划分")


def solve_model(features: dict[str, Any], config: PipelineConfig) -> dict[str, Any]:
    raise NotImplementedError("请训练主预测模型并输出预测明细、误差指标、外样本验证和泄漏检查")


def check_constraints(solution: dict[str, Any], config: PipelineConfig) -> pd.DataFrame | None:
    return None


def evaluate_primary_quality(
    context: ModelContext,
    constraints: pd.DataFrame | None,
) -> pd.DataFrame:
    raise NotImplementedError(
        "请检查时间切分、泄漏、测试集误差、基准模型、校准或区间覆盖和可复算性，"
        "返回检查项/是否通过/证据"
    )


def sync_primary_framework(primary: PrimarySolveResult) -> None:
    raise NotImplementedError("回写主预测结果、基础外样本精度、质量门结论和证据")


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
