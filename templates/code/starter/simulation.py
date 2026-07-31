from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from hsk_pipeline import (
    AuditLog,
    ModelContext,
    PipelineConfig,
    PrimarySolveResult,
    ResultAnalysisResult,
    REQUIRED_CAPABILITIES,
    run_pipeline,
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
        objective="simulation",
        structures=("stochastic",),
        capabilities=capabilities(
            requires_convergence_diagnostic=True,
            requires_uncertainty_quantification=True,
        ),
        random_seed=2026,
    )


def load_data(config: PipelineConfig, audit: AuditLog) -> dict[str, pd.DataFrame]:
    raise NotImplementedError("请读取仿真参数、初始状态和外部场景并检查单位与边界")


def preprocess_data(
    raw_data: dict[str, pd.DataFrame],
    config: PipelineConfig,
    audit: AuditLog,
) -> dict[str, pd.DataFrame]:
    raise NotImplementedError("请完成参数校准、场景整理和随机变量分布检查")


def build_features(clean_data: dict[str, pd.DataFrame], config: PipelineConfig) -> dict[str, Any]:
    raise NotImplementedError("请构造状态转移、事件机制、随机输入和停止条件")


def solve_model(features: dict[str, Any], config: PipelineConfig) -> dict[str, Any]:
    raise NotImplementedError("请完成主仿真并输出底层明细、重复试验、收敛诊断和不确定性区间")


def check_constraints(solution: dict[str, Any], config: PipelineConfig) -> pd.DataFrame | None:
    return None


def evaluate_primary_quality(
    context: ModelContext,
    constraints: pd.DataFrame | None,
) -> pd.DataFrame:
    raise NotImplementedError(
        "请检查随机种子、重复次数、收敛、守恒或状态边界、置信区间和可复算性，"
        "返回检查项/是否通过/证据"
    )


def analyze_results(primary: PrimarySolveResult) -> ResultAnalysisResult:
    raise NotImplementedError(
        "根据随机输入、极端场景和样本量风险，选择场景压力、阈值、参数敏感性、误差分解、"
        "结构稳健性或异质性分析，并返回 ResultAnalysisResult；失效时使用 redo_required"
    )


def sync_primary_framework(primary: PrimarySolveResult) -> None:
    raise NotImplementedError("回写主仿真结果、收敛与区间证据和质量门结论")


def sync_analysis_framework(
    primary: PrimarySolveResult,
    analysis_path: Path,
    tables: dict[str, pd.DataFrame],
) -> None:
    raise NotImplementedError("回写极端场景、稳定范围、失效边界、回退结论和分析工作簿证据")


def main() -> None:
    config = build_config(Path(__file__))
    run_pipeline(
        config,
        load_data_hook=load_data,
        preprocess_hook=preprocess_data,
        build_features_hook=build_features,
        solve_hook=solve_model,
        constraint_hook=check_constraints,
        quality_hook=evaluate_primary_quality,
        result_analysis_hook=analyze_results,
        primary_framework_sync_hook=sync_primary_framework,
        analysis_framework_sync_hook=sync_analysis_framework,
    )


if __name__ == "__main__":
    main()
