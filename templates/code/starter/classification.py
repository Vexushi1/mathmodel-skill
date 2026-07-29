from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from hsk_pipeline import AuditLog, ModelContext, PipelineConfig, REQUIRED_CAPABILITIES, run_pipeline
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
        objective="inference",
        structures=("static_tabular",),
        capabilities=capabilities(requires_out_of_sample_validation=True, requires_leakage_check=True),
        random_seed=2026,
    )


def load_data(config: PipelineConfig, audit: AuditLog) -> dict[str, pd.DataFrame]:
    """读取分类样本并检查标签、主键、缺失、重复和类别分布。"""
    data = read_tabular_input(config, audit)
    return {"原始数据": data}


def preprocess_data(
    raw_data: dict[str, pd.DataFrame],
    config: PipelineConfig,
    audit: AuditLog,
) -> dict[str, pd.DataFrame]:
    """按题意完成字段选择、缺失处理、单位统一和异常处理。"""
    raise NotImplementedError("请依据模型论文框架实现预处理，并记录处理前后样本量")


def build_features(clean_data: dict[str, pd.DataFrame], config: PipelineConfig) -> dict[str, Any]:
    """构造训练特征、标签和不泄漏的训练/验证/测试划分。"""
    raise NotImplementedError("请将当前模型的变量和参数映射为可计算对象")


def solve_model(features: dict[str, Any], config: PipelineConfig) -> dict[str, Any]:
    """训练基准与候选分类器，输出核心指标、预测或分类结果和模型指标。"""
    raise NotImplementedError("solution 至少包含符合工作簿 Schema 的‘核心指标’")


def check_constraints(solution: dict[str, Any], config: PipelineConfig) -> pd.DataFrame | None:
    return None


def validate_model(context: ModelContext) -> tuple[pd.DataFrame | None, dict[str, pd.DataFrame]]:
    """输出多算法对比，以及阈值、Bootstrap、校准或外样本稳定性表。"""
    raise NotImplementedError("敏感性与鲁棒性工作簿必须非空；不适用时写明原因和替代检验")


def sync_framework(
    context: ModelContext,
    output_paths: tuple[Path, Path],
    constraints: pd.DataFrame | None,
    algorithm_comparison: pd.DataFrame | None,
    validation_tables: dict[str, pd.DataFrame],
) -> None:
    """完整替换该问当前模型口径和结果摘要，不保留并列旧版本。"""
    raise NotImplementedError("请回写模型、算法、核心数值、验证结论和工作簿证据位置")


def main() -> None:
    config = build_config(Path(__file__))
    run_pipeline(
        config,
        load_data_hook=load_data,
        preprocess_hook=preprocess_data,
        build_features_hook=build_features,
        solve_hook=solve_model,
        constraint_hook=check_constraints,
        validation_hook=validate_model,
        framework_sync_hook=sync_framework,
    )


if __name__ == "__main__":
    main()
