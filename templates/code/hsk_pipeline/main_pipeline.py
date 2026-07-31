from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np
import pandas as pd

try:
    from .result_io import find_project_root, workbook_paths, write_workbook
except ImportError:  # 允许将本文件作为独立脚本运行
    from result_io import find_project_root, workbook_paths, write_workbook

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


@dataclass(frozen=True)
class PrimarySolveResult:
    context: ModelContext
    solution_path: Path
    quality_report: pd.DataFrame
    constraints: pd.DataFrame | None


LoadDataHook = Callable[[PipelineConfig, AuditLog], dict[str, pd.DataFrame]]
PreprocessHook = Callable[[dict[str, pd.DataFrame], PipelineConfig, AuditLog], dict[str, pd.DataFrame]]
BuildFeaturesHook = Callable[[dict[str, pd.DataFrame], PipelineConfig], dict[str, Any]]
SolveHook = Callable[[dict[str, Any], PipelineConfig], dict[str, Any]]
ConstraintHook = Callable[[dict[str, Any], PipelineConfig], pd.DataFrame | None]
QualityHook = Callable[[ModelContext, pd.DataFrame | None], pd.DataFrame]
ResultAnalysisHook = Callable[[PrimarySolveResult], dict[str, pd.DataFrame]]
PrimaryFrameworkSyncHook = Callable[[PrimarySolveResult], None]
AnalysisFrameworkSyncHook = Callable[[PrimarySolveResult, Path, dict[str, pd.DataFrame]], None]


def build_config(script_path: Path) -> PipelineConfig:
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
    raise NotImplementedError("请实现当前框架中的目标函数、约束与求解算法")


def check_constraints(solution: dict[str, Any], config: PipelineConfig) -> pd.DataFrame | None:
    if config.capabilities.get("has_explicit_constraints") or config.capabilities.get("requires_feasibility_check"):
        raise NotImplementedError("该问题声明需要可行性检查，请实现约束违反检查表")
    return None


def evaluate_primary_quality(context: ModelContext, constraints: pd.DataFrame | None) -> pd.DataFrame:
    raise NotImplementedError(
        "请按检查项输出是否通过和证据；至少覆盖数据口径、收敛/终止、可行性或残差、"
        "基础精度和可复算性"
    )


def analyze_results(primary: PrimarySolveResult) -> dict[str, pd.DataFrame]:
    raise NotImplementedError(
        "根据题目、模型、数据、主结果表现和评委风险选择敏感性、鲁棒性、多算法、结构、"
        "阈值、异质性、误差分解或外样本稳定性等真实分析"
    )


def _as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "是", "通过", "满足"}:
        return True
    if text in {"false", "0", "no", "否", "未通过", "不满足"}:
        return False
    return None


def assert_primary_quality(quality_report: pd.DataFrame) -> None:
    required = {"检查项", "是否通过", "证据"}
    missing = sorted(required - set(quality_report.columns))
    if missing:
        raise ValueError(f"主结果质量报告缺少字段: {missing}")
    if quality_report.empty:
        raise ValueError("主结果质量报告不能为空")
    failed = []
    for _, row in quality_report.iterrows():
        if _as_bool(row["是否通过"]) is not True:
            failed.append(str(row["检查项"]))
    if failed:
        raise RuntimeError(f"主结果质量门未通过，禁止进入结果深化分析: {failed}")


def build_solution_tables(
    solution: dict[str, Any],
    constraints: pd.DataFrame | None,
    audit: AuditLog,
) -> dict[str, Any]:
    if "核心指标" not in solution:
        raise KeyError("solution 必须包含“核心指标”")
    tables: dict[str, Any] = {"核心指标": solution["核心指标"], "数据审计": audit.table()}
    optional_sheets = (
        "推荐方案", "明细结果", "预测明细", "误差指标", "外样本验证", "不确定性区间",
        "综合评分", "排序结果", "模型指标", "预测或分类结果", "泄漏检查", "校准结果",
        "可识别性检查", "空间诊断", "参数估计", "节点结果", "边结果", "路径或流结果",
        "机理分析", "状态明细", "边界检验", "量纲检查", "决策变量明细", "方案对比",
        "Pareto结果", "仿真明细", "逐时刻结果", "逐场景结果", "重复试验结果",
        "均衡残差", "守恒残差", "离散精度", "收敛诊断",
    )
    for sheet in optional_sheets:
        if sheet in solution:
            tables[sheet] = solution[sheet]
    if constraints is not None:
        tables["约束违反检查"] = constraints
    return tables


def project_sync_command(config: PipelineConfig) -> str:
    return (
        f'python scripts/sync_project.py "{config.project_root.as_posix()}" '
        "--write --strict --delivery-scope results"
    )


def run_primary_pipeline(
    config: PipelineConfig,
    *,
    load_data_hook: LoadDataHook,
    preprocess_hook: PreprocessHook,
    build_features_hook: BuildFeaturesHook,
    solve_hook: SolveHook,
    constraint_hook: ConstraintHook,
    quality_hook: QualityHook,
    framework_sync_hook: PrimaryFrameworkSyncHook,
) -> PrimarySolveResult:
    """完整主求解；结果未通过质量门时停止，不执行后续分析。"""
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
    quality_report = quality_hook(context, constraints)
    assert_primary_quality(quality_report)
    solution_path, _ = workbook_paths(config.project_root, config.problem_name)
    write_workbook(
        solution_path,
        build_solution_tables(solution, constraints, audit),
        workbook_kind="solution",
        objective=config.objective,
        structures=config.structures,
        capabilities=config.capabilities,
    )
    primary = PrimarySolveResult(context, solution_path, quality_report, constraints)
    framework_sync_hook(primary)
    logger.info("主求解结果已通过质量门并写入: %s", solution_path.as_posix())
    return primary


def run_result_analysis_pipeline(
    primary: PrimarySolveResult,
    *,
    analysis_hook: ResultAnalysisHook,
    framework_sync_hook: AnalysisFrameworkSyncHook,
) -> Path:
    """在已通过质量门的主结果上执行题目专属结果深化分析。"""
    assert_primary_quality(primary.quality_report)
    tables = analysis_hook(primary)
    if not tables:
        raise ValueError("结果深化分析不能为空；应选择至少一项真正服务结论的分析")
    _, analysis_path = workbook_paths(
        primary.context.config.project_root,
        primary.context.config.problem_name,
    )
    config = primary.context.config
    write_workbook(
        analysis_path,
        tables,
        workbook_kind="result_analysis",
        objective=config.objective,
        structures=config.structures,
        capabilities=config.capabilities,
    )
    framework_sync_hook(primary, analysis_path, tables)
    return analysis_path


def run_pipeline(
    config: PipelineConfig,
    *,
    load_data_hook: LoadDataHook,
    preprocess_hook: PreprocessHook,
    build_features_hook: BuildFeaturesHook,
    solve_hook: SolveHook,
    constraint_hook: ConstraintHook,
    quality_hook: QualityHook,
    result_analysis_hook: ResultAnalysisHook,
    primary_framework_sync_hook: PrimaryFrameworkSyncHook,
    analysis_framework_sync_hook: AnalysisFrameworkSyncHook,
) -> tuple[Path, Path]:
    """兼容的一键编排器；内部仍严格经过独立主求解质量门和结果深化阶段。"""
    primary = run_primary_pipeline(
        config,
        load_data_hook=load_data_hook,
        preprocess_hook=preprocess_hook,
        build_features_hook=build_features_hook,
        solve_hook=solve_hook,
        constraint_hook=constraint_hook,
        quality_hook=quality_hook,
        framework_sync_hook=primary_framework_sync_hook,
    )
    analysis_path = run_result_analysis_pipeline(
        primary,
        analysis_hook=result_analysis_hook,
        framework_sync_hook=analysis_framework_sync_hook,
    )
    logger = setup_logger()
    logger.info("结果深化分析已写入: %s", analysis_path.as_posix())
    logger.info("正式交付前执行: %s", project_sync_command(config))
    return primary.solution_path, analysis_path


def sync_primary_framework(primary: PrimarySolveResult) -> None:
    raise NotImplementedError("完整替换该问主模型、主结果、质量门结论和证据位置")


def sync_analysis_framework(
    primary: PrimarySolveResult,
    analysis_path: Path,
    tables: dict[str, pd.DataFrame],
) -> None:
    raise NotImplementedError("写入实际分析方法、稳定范围、失效边界、回退记录和工作簿证据")


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
