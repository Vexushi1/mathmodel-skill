from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from result_io import find_project_root, not_applicable_table, workbook_paths, write_workbook


@dataclass(frozen=True)
class PipelineConfig:
    project_root: Path
    problem_name: str
    problem_types: tuple[str, ...]
    capabilities: Mapping[str, bool]
    random_seed: int = 2026

    def validate(self) -> None:
        if not self.problem_types:
            raise ValueError("必须填写每问主/次题型，禁止以空标签绕过专项工作簿校验")
        required = {
            "has_explicit_constraints",
            "requires_feasibility_check",
            "requires_equilibrium_residual",
            "requires_conservation_residual",
            "requires_discretization_check",
            "requires_convergence_diagnostic",
        }
        missing = sorted(required - set(self.capabilities))
        if missing:
            raise ValueError(f"缺少验证能力标志: {missing}")


@dataclass
class AuditLog:
    rows: list[dict[str, str]] = field(default_factory=list)

    def record(self, level: str, item: str, message: str, action: str = "") -> None:
        self.rows.append({"等级": level, "检查项": item, "信息": message, "处理方式": action})

    def table(self) -> list[dict[str, str]]:
        return self.rows or [
            {"等级": "Info", "检查项": "数据审计", "信息": "未发现需记录问题", "处理方式": "无"}
        ]


@dataclass(frozen=True)
class ModelContext:
    config: PipelineConfig
    raw_data: dict[str, pd.DataFrame]
    clean_data: dict[str, pd.DataFrame]
    features: dict[str, Any]
    solution: dict[str, Any]


def build_config(script_path: Path) -> PipelineConfig:
    """按题目填写后再运行；目录定位和创建只在 main() 内发生。"""
    project_root = find_project_root(script_path)
    config = PipelineConfig(
        project_root=project_root,
        problem_name="问题一",
        problem_types=(),  # 例如 ("mechanism", "optimization")
        capabilities={
            "has_explicit_constraints": False,
            "requires_feasibility_check": False,
            "requires_equilibrium_residual": False,
            "requires_conservation_residual": False,
            "requires_discretization_check": False,
            "requires_convergence_diagnostic": False,
        },
        random_seed=2026,
    )
    config.validate()
    return config


def set_random_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def setup_logger() -> logging.Logger:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    return logging.getLogger("hsk_mathmodel")


def check_required_columns(df: pd.DataFrame, required: list[str], table_name: str, audit: AuditLog) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        audit.record("Error", table_name, f"缺少字段: {missing}", "修正输入后重跑")
        raise ValueError(f"{table_name} 缺少字段: {missing}")


def check_missing_values(df: pd.DataFrame, table_name: str, audit: AuditLog) -> pd.Series:
    missing = df.isna().sum()
    missing = missing[missing > 0]
    if not missing.empty:
        audit.record("Warning", table_name, f"缺失值: {missing.to_dict()}", "按题目口径处理并说明")
    return missing


def check_dimensions(
    df: pd.DataFrame,
    table_name: str,
    audit: AuditLog,
    min_rows: int = 1,
    min_cols: int = 1,
) -> None:
    if df.shape[0] < min_rows or df.shape[1] < min_cols:
        audit.record("Error", table_name, f"维度异常: {df.shape}", "检查读取或筛选逻辑")
        raise ValueError(f"{table_name} 维度异常: {df.shape}")


def load_data(config: PipelineConfig, audit: AuditLog) -> dict[str, pd.DataFrame]:
    raise NotImplementedError("请根据赛题附件实现数据读取")


def preprocess_data(
    raw_data: dict[str, pd.DataFrame],
    config: PipelineConfig,
    audit: AuditLog,
) -> dict[str, pd.DataFrame]:
    raise NotImplementedError("请根据题意实现清洗、单位统一和时间/空间对齐")


def build_features(clean_data: dict[str, pd.DataFrame], config: PipelineConfig) -> dict[str, Any]:
    raise NotImplementedError("请根据模型构造参数、状态或特征")


def solve_model(features: dict[str, Any], config: PipelineConfig) -> dict[str, Any]:
    """至少返回符合 Schema 的“核心指标”；其他工作表按题型返回。"""
    raise NotImplementedError("请实现目标函数、约束与求解算法")


def check_constraints(solution: dict[str, Any], config: PipelineConfig) -> pd.DataFrame | None:
    """显式约束/可行性能力为 true 时必须返回约束检查表。"""
    if config.capabilities.get("has_explicit_constraints") or config.capabilities.get("requires_feasibility_check"):
        raise NotImplementedError("该问题声明需要可行性检查，请实现约束违反检查表")
    return None


def run_validation(context: ModelContext) -> tuple[pd.DataFrame | None, dict[str, pd.DataFrame]]:
    """返回可选多算法对比，以及敏感性与鲁棒性工作簿的非空工作表映射。"""
    raise NotImplementedError(
        "validation_tables 应包含参数敏感性、鲁棒性区间、扰动明细、算法稳定性中的适用项；"
        "全部不适用时返回 {'适用性说明': not_applicable_table(...)}"
    )


def build_solution_tables(
    solution: dict[str, Any],
    constraints: pd.DataFrame | None,
    algorithm_comparison: pd.DataFrame | None,
    audit: AuditLog,
) -> dict[str, Any]:
    if "核心指标" not in solution:
        raise KeyError("solution 必须包含“核心指标”")
    tables: dict[str, Any] = {"核心指标": solution["核心指标"], "数据审计": audit.table()}
    optional_sheets = (
        "推荐方案", "明细结果", "预测明细", "误差指标", "残差诊断", "综合评分", "排序结果",
        "指标权重", "模型指标", "预测或分类结果", "交叉验证", "校准结果", "空间诊断",
        "参数估计", "空间效应分解", "节点结果", "边结果", "路径或流结果", "均衡残差",
        "守恒残差", "离散精度", "收敛诊断",
    )
    for sheet in optional_sheets:
        if sheet in solution:
            tables[sheet] = solution[sheet]
    if constraints is not None:
        tables["约束违反检查"] = constraints
    if algorithm_comparison is not None:
        tables["多算法对比"] = algorithm_comparison
    return tables


def save_outputs(
    context: ModelContext,
    constraints: pd.DataFrame | None,
    algorithm_comparison: pd.DataFrame | None,
    validation_tables: dict[str, pd.DataFrame],
    audit: AuditLog,
) -> tuple[Path, Path]:
    if not validation_tables:
        validation_tables = {
            "适用性说明": not_applicable_table(
                "该题没有可独立扰动的外生参数或随机输入",
                alternative_test="边界、极限状态与数值一致性检查",
            )
        }
    solution_path, robustness_path = workbook_paths(
        context.config.project_root,
        context.config.problem_name,
    )
    solution_tables = build_solution_tables(
        context.solution,
        constraints,
        algorithm_comparison,
        audit,
    )
    common = {
        "problem_types": context.config.problem_types,
        "capabilities": context.config.capabilities,
    }
    write_workbook(solution_path, solution_tables, workbook_kind="solution", **common)
    write_workbook(robustness_path, validation_tables, workbook_kind="robustness", **common)
    return solution_path, robustness_path


def main() -> None:
    logger = setup_logger()
    config = build_config(Path(__file__))
    set_random_seed(config.random_seed)
    audit = AuditLog()
    raw = load_data(config, audit)
    clean = preprocess_data(raw, config, audit)
    features = build_features(clean, config)
    solution = solve_model(features, config)
    context = ModelContext(config=config, raw_data=raw, clean_data=clean, features=features, solution=solution)
    constraints = check_constraints(solution, config)
    comparison, validation_tables = run_validation(context)
    paths = save_outputs(context, constraints, comparison, validation_tables, audit)
    logger.info("结果已写入: %s", [path.as_posix() for path in paths])
    logger.info("正式论文图由 MATLAB 读取上述工作簿绘制。")


if __name__ == "__main__":
    main()
