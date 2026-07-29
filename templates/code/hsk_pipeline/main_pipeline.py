from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np
import pandas as pd

try:
    from .result_io import find_project_root, not_applicable_table, workbook_paths, write_workbook
except ImportError:  # 允许将本文件作为独立脚本运行
    from result_io import find_project_root, not_applicable_table, workbook_paths, write_workbook

VALID_OBJECTIVES = {"explanation", "inference", "prediction", "evaluation", "optimization", "simulation"}
VALID_STRUCTURES = {"physical_mechanism", "temporal", "spatial", "network", "scheduling", "game", "stochastic", "static_tabular"}
REQUIRED_CAPABILITIES = {
    "has_explicit_constraints",
    "requires_feasibility_check",
    "requires_equilibrium_residual",
    "requires_conservation_residual",
    "requires_discretization_check",
    "requires_convergence_diagnostic",
    "requires_out_of_sample_validation",
    "requires_uncertainty_quantification",
    "requires_leakage_check",
    "requires_calibration_check",
    "requires_identifiability_check",
}


@dataclass(frozen=True)
class PipelineConfig:
    project_root: Path
    framework_path: Path
    framework_section: str
    problem_name: str
    objective: str
    structures: tuple[str, ...]
    capabilities: Mapping[str, bool]
    random_seed: int = 2026

    def validate(self) -> None:
        if self.objective not in VALID_OBJECTIVES:
            raise ValueError(f"objective 必须为 {sorted(VALID_OBJECTIVES)} 之一")
        if len(self.structures) > 3 or len(self.structures) != len(set(self.structures)):
            raise ValueError("structures 必须唯一且最多三项")
        unknown_structures = sorted(set(self.structures) - VALID_STRUCTURES)
        if unknown_structures:
            raise ValueError(f"未知 structures: {unknown_structures}")
        missing = sorted(REQUIRED_CAPABILITIES - set(self.capabilities))
        unknown = sorted(set(self.capabilities) - REQUIRED_CAPABILITIES)
        if missing:
            raise ValueError(f"缺少验证能力标志: {missing}")
        if unknown:
            raise ValueError(f"未知验证能力标志: {unknown}")
        if not all(isinstance(value, bool) for value in self.capabilities.values()):
            raise TypeError("capabilities 的所有值必须为 bool")
        if not self.framework_path.is_file():
            raise FileNotFoundError(f"模型锁定后必须先创建项目根目录模型论文框架: {self.framework_path}")
        if not self.framework_section.strip():
            raise ValueError("必须填写该问在模型论文框架.md中的当前章节标题")
        framework_text = self.framework_path.read_text(encoding="utf-8")
        if self.framework_section not in framework_text:
            raise ValueError(f"模型论文框架中缺少该问当前章节: {self.framework_section}")
        if "只保留当前有效" not in framework_text and "当前有效版本" not in framework_text:
            raise ValueError("模型论文框架必须声明只保留当前有效版本")


@dataclass
class AuditLog:
    rows: list[dict[str, str]] = field(default_factory=list)

    def record(self, level: str, item: str, message: str, action: str = "") -> None:
        self.rows.append({"等级": level, "检查项": item, "信息": message, "处理方式": action})

    def table(self) -> list[dict[str, str]]:
        return self.rows or [{"等级": "Info", "检查项": "数据审计", "信息": "未发现需记录问题", "处理方式": "无"}]


@dataclass(frozen=True)
class ModelContext:
    config: PipelineConfig
    raw_data: dict[str, pd.DataFrame]
    clean_data: dict[str, pd.DataFrame]
    features: dict[str, Any]
    solution: dict[str, Any]


LoadDataHook = Callable[[PipelineConfig, AuditLog], dict[str, pd.DataFrame]]
PreprocessHook = Callable[[dict[str, pd.DataFrame], PipelineConfig, AuditLog], dict[str, pd.DataFrame]]
BuildFeaturesHook = Callable[[dict[str, pd.DataFrame], PipelineConfig], dict[str, Any]]
SolveHook = Callable[[dict[str, Any], PipelineConfig], dict[str, Any]]
ConstraintHook = Callable[[dict[str, Any], PipelineConfig], pd.DataFrame | None]
ValidationHook = Callable[[ModelContext], tuple[pd.DataFrame | None, dict[str, pd.DataFrame]]]
FrameworkSyncHook = Callable[
    [ModelContext, tuple[Path, Path], pd.DataFrame | None, pd.DataFrame | None, dict[str, pd.DataFrame]],
    None,
]


def build_config(script_path: Path) -> PipelineConfig:
    """通用入口示例；实际项目优先使用 starter 中的题型专属 build_config。"""
    project_root = find_project_root(script_path)
    return PipelineConfig(
        project_root=project_root,
        framework_path=project_root / "模型论文框架.md",
        framework_section="### Q1：__QUESTION_NAME__",
        problem_name="问题一",
        objective="optimization",
        structures=(),
        capabilities={name: False for name in REQUIRED_CAPABILITIES},
        random_seed=2026,
    )


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
    raise NotImplementedError("请根据当前模型论文框架构造参数、状态或特征")


def solve_model(features: dict[str, Any], config: PipelineConfig) -> dict[str, Any]:
    """至少返回符合 Schema 的“核心指标”；专项表由三轴分类决定。"""
    raise NotImplementedError("请实现当前框架中的目标函数、约束与求解算法")


def check_constraints(solution: dict[str, Any], config: PipelineConfig) -> pd.DataFrame | None:
    """显式约束/可行性能力为 true 时必须返回约束检查表。"""
    if config.capabilities.get("has_explicit_constraints") or config.capabilities.get("requires_feasibility_check"):
        raise NotImplementedError("该问题声明需要可行性检查，请实现约束违反检查表")
    return None


def run_validation(context: ModelContext) -> tuple[pd.DataFrame | None, dict[str, pd.DataFrame]]:
    """返回多算法对比和敏感性/鲁棒性工作簿的非空表映射。"""
    raise NotImplementedError(
        "validation_tables 应包含适用的参数敏感性、鲁棒性区间、扰动明细或算法稳定性；"
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
        "推荐方案", "明细结果", "预测明细", "误差指标", "外样本验证", "不确定性区间",
        "综合评分", "排序结果", "模型指标", "预测或分类结果", "泄漏检查", "校准结果",
        "可识别性检查", "空间诊断", "参数估计", "节点结果", "边结果", "路径或流结果",
        "均衡残差", "守恒残差", "离散精度", "收敛诊断",
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
    solution_path, robustness_path = workbook_paths(context.config.project_root, context.config.problem_name)
    solution_tables = build_solution_tables(context.solution, constraints, algorithm_comparison, audit)
    common = {
        "objective": context.config.objective,
        "structures": context.config.structures,
        "capabilities": context.config.capabilities,
    }
    write_workbook(solution_path, solution_tables, workbook_kind="solution", **common)
    write_workbook(robustness_path, validation_tables, workbook_kind="robustness", **common)
    return solution_path, robustness_path


def sync_model_paper_framework(
    context: ModelContext,
    output_paths: tuple[Path, Path],
    constraints: pd.DataFrame | None,
    algorithm_comparison: pd.DataFrame | None,
    validation_tables: dict[str, pd.DataFrame],
) -> None:
    """完整替换该问当前模型口径和结果摘要，不叠加旧版本。"""
    raise NotImplementedError(
        "工作簿通过校验后，删除该问旧模型/旧摘要，写入当前模型与算法、核心数值、"
        "验证/可行性、敏感性/鲁棒性、最终结论和证据位置，并将结果摘要状态设为 current"
    )


def project_sync_command(config: PipelineConfig) -> str:
    return (
        f'python scripts/sync_project.py "{config.project_root.as_posix()}" '
        "--write --strict --delivery-scope results"
    )


def run_pipeline(
    config: PipelineConfig,
    *,
    load_data_hook: LoadDataHook,
    preprocess_hook: PreprocessHook,
    build_features_hook: BuildFeaturesHook,
    solve_hook: SolveHook,
    constraint_hook: ConstraintHook,
    validation_hook: ValidationHook,
    framework_sync_hook: FrameworkSyncHook,
) -> tuple[Path, Path]:
    """执行统一求解主链；所有目录创建、随机种子和文件写入均从这里开始。"""
    config.validate()
    logger = setup_logger()
    set_random_seed(config.random_seed)
    audit = AuditLog()
    raw = load_data_hook(config, audit)
    clean = preprocess_hook(raw, config, audit)
    features = build_features_hook(clean, config)
    solution = solve_hook(features, config)
    context = ModelContext(config=config, raw_data=raw, clean_data=clean, features=features, solution=solution)
    constraints = constraint_hook(solution, config)
    comparison, validation_tables = validation_hook(context)
    paths = save_outputs(context, constraints, comparison, validation_tables, audit)
    framework_sync_hook(context, paths, constraints, comparison, validation_tables)
    logger.info("结果已写入: %s", [path.as_posix() for path in paths])
    logger.info("模型论文框架已同步: %s", config.framework_path.as_posix())
    logger.info("正式交付前执行: %s", project_sync_command(config))
    logger.info("正式论文图由 MATLAB 读取上述工作簿绘制，并保留简洁 title/sgtitle。")
    return paths


def main() -> None:
    config = build_config(Path(__file__))
    run_pipeline(
        config,
        load_data_hook=load_data,
        preprocess_hook=preprocess_data,
        build_features_hook=build_features,
        solve_hook=solve_model,
        constraint_hook=check_constraints,
        validation_hook=run_validation,
        framework_sync_hook=sync_model_paper_framework,
    )


if __name__ == "__main__":
    main()
