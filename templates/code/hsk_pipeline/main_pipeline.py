from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from result_io import find_project_root, not_applicable_table, workbook_paths, write_workbook

RANDOM_SEED = 2026
np.random.seed(RANDOM_SEED)

PROJECT_ROOT = find_project_root(Path(__file__))
DATA_DIR = PROJECT_ROOT / "数据"
PROBLEM_NAME = "问题一"
# 按题意填写，可包含一个主标签和必要次标签。
PROBLEM_TYPES: tuple[str, ...] = ()
SOLUTION_WORKBOOK, ROBUSTNESS_WORKBOOK = workbook_paths(PROJECT_ROOT, PROBLEM_NAME)
AUDIT_ROWS: list[dict[str, str]] = []


@dataclass(frozen=True)
class ModelContext:
    raw_data: dict[str, pd.DataFrame]
    clean_data: dict[str, pd.DataFrame]
    features: dict[str, Any]
    solution: dict[str, Any]
    random_seed: int = RANDOM_SEED


def setup_logger() -> logging.Logger:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    return logging.getLogger("hsk_mathmodel")


def record_audit(level: str, item: str, message: str, action: str = "") -> None:
    AUDIT_ROWS.append({"等级": level, "检查项": item, "信息": message, "处理方式": action})


def check_required_columns(df: pd.DataFrame, required: list[str], table_name: str) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        record_audit("Error", table_name, f"缺少字段: {missing}", "修正输入后重跑")
        raise ValueError(f"{table_name} 缺少字段: {missing}")


def check_missing_values(df: pd.DataFrame, table_name: str) -> pd.Series:
    missing = df.isna().sum()
    missing = missing[missing > 0]
    if not missing.empty:
        record_audit("Warning", table_name, f"缺失值: {missing.to_dict()}", "按题目口径处理并说明")
    return missing


def check_dimensions(df: pd.DataFrame, table_name: str, min_rows: int = 1, min_cols: int = 1) -> None:
    if df.shape[0] < min_rows or df.shape[1] < min_cols:
        record_audit("Error", table_name, f"维度异常: {df.shape}", "检查读取或筛选逻辑")
        raise ValueError(f"{table_name} 维度异常: {df.shape}")


def load_data() -> dict[str, pd.DataFrame]:
    raise NotImplementedError("请根据赛题附件实现数据读取")


def preprocess_data(raw_data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    raise NotImplementedError("请根据题意实现清洗、单位统一和时间/空间对齐")


def build_features(clean_data: dict[str, pd.DataFrame]) -> dict[str, Any]:
    raise NotImplementedError("请根据模型构造参数、状态或特征")


def solve_model(features: dict[str, Any]) -> dict[str, Any]:
    """至少返回符合 Schema 的“核心指标”；其他工作表按题型返回。"""
    raise NotImplementedError("请实现目标函数、约束与求解算法")


def check_constraints(solution: dict[str, Any]) -> pd.DataFrame | None:
    """约束型题返回约束检查表；无约束题返回 None。"""
    return None


def run_validation(
    context: ModelContext,
) -> tuple[pd.DataFrame | None, dict[str, pd.DataFrame]]:
    """返回可选多算法对比，以及敏感性与鲁棒性工作簿的非空工作表映射。"""
    raise NotImplementedError(
        "validation_tables 应包含参数敏感性、鲁棒性区间、扰动明细、算法稳定性中的适用项；"
        "全部不适用时返回 {'适用性说明': not_applicable_table(...)}"
    )


def build_solution_tables(
    solution: dict[str, Any],
    constraints: pd.DataFrame | None,
    algorithm_comparison: pd.DataFrame | None,
) -> dict[str, Any]:
    """只写入真实适用的工作表；条件必需项由 Schema 校验器把关。"""
    if "核心指标" not in solution:
        raise KeyError("solution 必须包含“核心指标”")
    tables: dict[str, Any] = {
        "核心指标": solution["核心指标"],
        "数据审计": AUDIT_ROWS
        or [{"等级": "Info", "检查项": "数据审计", "信息": "未发现需记录问题", "处理方式": "无"}],
    }
    for optional_sheet in (
        "推荐方案",
        "明细结果",
        "预测明细",
        "误差指标",
        "残差诊断",
        "综合评分",
        "排序结果",
        "指标权重",
        "模型指标",
        "预测或分类结果",
        "交叉验证",
        "校准结果",
        "空间诊断",
        "参数估计",
        "空间效应分解",
        "节点结果",
        "边结果",
        "路径或流结果",
    ):
        if optional_sheet in solution:
            tables[optional_sheet] = solution[optional_sheet]
    if constraints is not None:
        tables["约束违反检查"] = constraints
    if algorithm_comparison is not None:
        tables["多算法对比"] = algorithm_comparison
    return tables


def save_outputs(
    solution: dict[str, Any],
    constraints: pd.DataFrame | None,
    algorithm_comparison: pd.DataFrame | None,
    validation_tables: dict[str, pd.DataFrame],
) -> tuple[Path, Path]:
    if not validation_tables:
        validation_tables = {
            "适用性说明": not_applicable_table(
                "该题没有可独立扰动的外生参数或随机输入",
                alternative_test="边界、极限状态与数值一致性检查",
            )
        }

    solution_tables = build_solution_tables(solution, constraints, algorithm_comparison)
    write_workbook(
        SOLUTION_WORKBOOK,
        solution_tables,
        workbook_kind="solution",
        problem_types=PROBLEM_TYPES,
    )
    write_workbook(
        ROBUSTNESS_WORKBOOK,
        validation_tables,
        workbook_kind="robustness",
        problem_types=PROBLEM_TYPES,
    )
    return SOLUTION_WORKBOOK, ROBUSTNESS_WORKBOOK


def main() -> None:
    logger = setup_logger()
    raw = load_data()
    clean = preprocess_data(raw)
    features = build_features(clean)
    solution = solve_model(features)
    context = ModelContext(raw_data=raw, clean_data=clean, features=features, solution=solution)
    constraints = check_constraints(solution)
    comparison, validation_tables = run_validation(context)
    paths = save_outputs(solution, constraints, comparison, validation_tables)
    logger.info("结果已写入: %s", [path.as_posix() for path in paths])
    logger.info("正式论文图由 MATLAB 读取上述工作簿绘制。")


if __name__ == "__main__":
    main()
