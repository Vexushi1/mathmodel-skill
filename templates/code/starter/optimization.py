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


def read_tabular_input(config: PipelineConfig, audit: AuditLog) -> pd.DataFrame:
    if INPUT_FILE.startswith("__"):
        raise ValueError("请将 INPUT_FILE 替换为项目根目录中的真实附件文件名")
    path = config.project_root / INPUT_FILE
    if not path.is_file():
        raise FileNotFoundError(f"缺少输入文件: {path}")
    suffix = path.suffix.lower()
    if suffix == ".csv":
        data = pd.read_csv(path)
    elif suffix in {".xlsx", ".xls"}:
        data = pd.read_excel(path)
    else:
        raise ValueError(f"暂不支持的输入格式: {suffix}")
    if data.empty:
        raise ValueError("输入数据为空")
    audit.record("Info", "输入文件", path.name, f"读取 {data.shape[0]} 行、{data.shape[1]} 列")
    return data


def build_config(script_path: Path) -> PipelineConfig:
    project_root = find_project_root(script_path)
    return PipelineConfig(
        project_root=project_root,
        framework_path=project_root / "模型论文框架.md",
        framework_section=FRAMEWORK_SECTION,
        problem_name=PROBLEM_NAME,
        objective="optimization",
        structures=(),
        capabilities=capabilities(
            has_explicit_constraints=True,
            requires_feasibility_check=True,
        ),
        random_seed=2026,
    )


def load_data(config: PipelineConfig, audit: AuditLog) -> dict[str, pd.DataFrame]:
    data = read_tabular_input(config, audit)
    return {"原始数据": data}


def preprocess_data(
    raw_data: dict[str, pd.DataFrame],
    config: PipelineConfig,
    audit: AuditLog,
) -> dict[str, pd.DataFrame]:
    raise NotImplementedError("请依据题意实现清洗、单位统一和关联键检查")


def build_features(clean_data: dict[str, pd.DataFrame], config: PipelineConfig) -> dict[str, Any]:
    raise NotImplementedError("请构造决策变量索引、目标系数和约束参数")


def solve_model(features: dict[str, Any], config: PipelineConfig) -> dict[str, Any]:
    raise NotImplementedError(
        "请完整求解主模型，输出核心指标、推荐方案、决策变量明细，并按完整运行配置与实际终止信息生成运行配置表"
    )


def check_constraints(solution: dict[str, Any], config: PipelineConfig) -> pd.DataFrame | None:
    raise NotImplementedError("请按约束编号输出违反量、容差和是否满足")


def evaluate_primary_quality(
    context: ModelContext,
    constraints: pd.DataFrame | None,
) -> pd.DataFrame:
    raise NotImplementedError(
        "请检查求解器终止、可行性、最优间隙或停止条件、数值收敛和可复算性，"
        "返回检查项/是否通过/证据"
    )


def sync_primary_framework(primary: PrimarySolveResult) -> None:
    raise NotImplementedError("回写当前主模型、核心结果、质量门结论和求解工作簿证据")


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
