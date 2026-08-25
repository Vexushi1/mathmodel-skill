from __future__ import annotations

import hashlib
import logging
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal, Mapping

import numpy as np
import pandas as pd
import yaml

try:
    from .result_io import find_project_root, workbook_paths, write_workbook
except ImportError:  # 允许将本文件作为独立脚本运行
    from result_io import find_project_root, workbook_paths, write_workbook

VALID_OBJECTIVES = {"explanation", "inference", "prediction", "evaluation", "optimization", "simulation"}
VALID_STRUCTURES = {"physical_mechanism", "temporal", "spatial", "network", "scheduling", "game", "stochastic", "static_tabular"}
REQUIRED_CAPABILITIES = {
    "has_explicit_constraints", "requires_feasibility_check",
    "requires_equilibrium_residual", "requires_conservation_residual",
    "requires_discretization_check", "requires_convergence_diagnostic",
    "requires_out_of_sample_validation", "requires_uncertainty_quantification",
    "requires_leakage_check", "requires_calibration_check",
    "requires_identifiability_check",
}
ANALYSIS_STATUSES = {"passed", "failed", "redo_required"}
REDO_STALE_LAYERS = (
    "result_analysis_workbook", "matlab_script", "figure_bundle", "framework",
)


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
    execution_owner: Literal["user"] = "user"
    execution_profile: Literal["full_fidelity"] = "full_fidelity"
    allow_reduced_data: bool = False
    allow_coarser_grid: bool = False
    allow_shorter_horizon: bool = False
    allow_fewer_repetitions: bool = False
    allow_relaxed_tolerance: bool = False
    allow_silent_solver_fallback: bool = False

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
        if self.execution_owner != "user" or self.execution_profile != "full_fidelity":
            raise ValueError("正式代码必须由用户以full_fidelity模式执行")
        forbidden_flags = {
            "allow_reduced_data": self.allow_reduced_data,
            "allow_coarser_grid": self.allow_coarser_grid,
            "allow_shorter_horizon": self.allow_shorter_horizon,
            "allow_fewer_repetitions": self.allow_fewer_repetitions,
            "allow_relaxed_tolerance": self.allow_relaxed_tolerance,
            "allow_silent_solver_fallback": self.allow_silent_solver_fallback,
        }
        enabled = sorted(name for name, value in forbidden_flags.items() if value)
        if enabled:
            raise ValueError(f"完整版运行禁止启用降级标志: {enabled}")
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


@dataclass(frozen=True)
class ResultAnalysisResult:
    tables: dict[str, pd.DataFrame]
    status: Literal["passed", "failed", "redo_required"] = "passed"
    methods: tuple[str, ...] = ()
    reason: str = ""
    stale_layers: tuple[str, ...] = REDO_STALE_LAYERS
    restart_phase: Literal["model_design", "solve_validate"] = "solve_validate"

    def validate(self) -> None:
        if self.status not in ANALYSIS_STATUSES:
            raise ValueError(f"未知结果深化分析状态: {self.status}")
        required = {"运行配置", "分析设计", "结论稳定性汇总"}
        missing = sorted(required - set(self.tables))
        if missing:
            raise ValueError(f"结果深化分析缺少必需工作表: {missing}")
        if not self.methods:
            raise ValueError("结果深化分析必须登记实际采用的方法")
        if self.status in {"failed", "redo_required"} and not self.reason.strip():
            raise ValueError(f"结果深化分析状态为 {self.status} 时必须说明原因")
        if self.status == "redo_required":
            if self.restart_phase not in {"model_design", "solve_validate"}:
                raise ValueError("redo_required 的 restart_phase 必须为 model_design 或 solve_validate")
            if not self.stale_layers:
                raise ValueError("redo_required 必须声明至少一个 stale layer")


LoadDataHook = Callable[[PipelineConfig, AuditLog], dict[str, pd.DataFrame]]
PreprocessHook = Callable[[dict[str, pd.DataFrame], PipelineConfig, AuditLog], dict[str, pd.DataFrame]]
BuildFeaturesHook = Callable[[dict[str, pd.DataFrame], PipelineConfig], dict[str, Any]]
SolveHook = Callable[[dict[str, Any], PipelineConfig], dict[str, Any]]
ConstraintHook = Callable[[dict[str, Any], PipelineConfig], pd.DataFrame | None]
QualityHook = Callable[[ModelContext, pd.DataFrame | None], pd.DataFrame]
ResultAnalysisHook = Callable[[PrimarySolveResult], ResultAnalysisResult | dict[str, pd.DataFrame]]
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


def analyze_results(primary: PrimarySolveResult) -> ResultAnalysisResult:
    raise NotImplementedError(
        "根据题目、模型、数据、主结果表现和评委风险选择真实分析，并返回含状态、方法、"
        "原因、回退阶段和工作表的 ResultAnalysisResult"
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


def _quality_failures(quality_report: pd.DataFrame) -> list[str]:
    required = {"检查项", "是否通过", "证据"}
    missing = sorted(required - set(quality_report.columns))
    if missing:
        raise ValueError(f"主结果质量报告缺少字段: {missing}")
    if quality_report.empty:
        raise ValueError("主结果质量报告不能为空")
    return [
        str(row["检查项"])
        for _, row in quality_report.iterrows()
        if _as_bool(row["是否通过"]) is not True
    ]


def assert_primary_quality(quality_report: pd.DataFrame) -> None:
    failed = _quality_failures(quality_report)
    if failed:
        raise RuntimeError(f"主结果质量门未通过，禁止进入结果深化分析: {failed}")


def build_solution_tables(
    solution: dict[str, Any],
    constraints: pd.DataFrame | None,
    quality_report: pd.DataFrame,
    audit: AuditLog,
) -> dict[str, Any]:
    for required_sheet in ("运行配置", "核心指标"):
        if required_sheet not in solution:
            raise KeyError(f"solution 必须包含“{required_sheet}”")
    tables: dict[str, Any] = {
        "运行配置": solution["运行配置"],
        "核心指标": solution["核心指标"],
        "数据审计": audit.table(),
        "主结果质量门": quality_report,
    }
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


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _question_key(problem_name: str) -> str:
    order = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    suffix = problem_name.removeprefix("问题")
    return f"Q{order.index(suffix) + 1}" if suffix in order else problem_name


def _load_state(config: PipelineConfig) -> tuple[Path, dict[str, Any]] | None:
    path = config.project_root / "state" / "project_state.yaml"
    if not path.is_file():
        return None
    return path, yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _write_state(path: Path, state: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _update_primary_state(primary: PrimarySolveResult, passed: bool) -> None:
    loaded = _load_state(primary.context.config)
    if loaded is None:
        return
    path, state = loaded
    entry = state.setdefault("subproblems", {}).setdefault(
        _question_key(primary.context.config.problem_name), {}
    )
    relative = primary.solution_path.relative_to(primary.context.config.project_root).as_posix()
    entry["solution_workbook"] = relative
    entry["result_quality_report"] = f"{relative}#主结果质量门"
    entry["primary_execution_status"] = "workbook_received" if passed else "rejected"
    entry["result_quality_status"] = "pending" if passed else "failed"
    entry["result_analysis_status"] = "pending"
    entry["execution_note"] = (
        "主工作簿已由用户本地运行生成，等待validate_user_execution.py验收"
        if passed else "主结果质量门未通过，需修正后重跑"
    )
    hashes = entry.setdefault("artifact_hashes", {})
    hashes["solution_workbook"] = _file_hash(primary.solution_path)
    entry.setdefault("validated_artifact_hashes", {}).pop("solution_workbook", None)
    entry["status"] = "designed"
    entry["result_summary_status"] = "stale" if not passed else "pending"
    entry["validation_status"] = "pending"
    entry["artifacts_stale"] = True
    entry["stale_layers"] = sorted(set(entry.get("stale_layers", [])) | {
        "solution_workbook", "result_analysis_workbook", "matlab_script", "figure_bundle", "framework",
    })
    entry["proposition_refs"] = []
    state.setdefault("paper_framework", {})["sync_status"] = "stale"
    state.setdefault("project", {})["current_phase"] = "solve_validate"
    _write_state(path, state)


def _normalize_analysis_result(
    value: ResultAnalysisResult | dict[str, pd.DataFrame],
) -> ResultAnalysisResult:
    if isinstance(value, ResultAnalysisResult):
        result = value
    elif isinstance(value, dict):
        methods: tuple[str, ...] = ()
        design = value.get("分析设计")
        if isinstance(design, pd.DataFrame) and "方法" in design.columns:
            methods = tuple(dict.fromkeys(str(item) for item in design["方法"] if str(item).strip()))
        result = ResultAnalysisResult(tables=value, status="passed", methods=methods)
    else:
        raise TypeError("analysis_hook 必须返回 ResultAnalysisResult 或工作表字典")
    result.validate()
    return result


def _update_analysis_state(
    primary: PrimarySolveResult,
    analysis_path: Path,
    result: ResultAnalysisResult,
) -> None:
    config = primary.context.config
    loaded = _load_state(config)
    if loaded is None:
        return
    path, state = loaded
    entry = state.setdefault("subproblems", {}).setdefault(_question_key(config.problem_name), {})
    relative = analysis_path.relative_to(config.project_root).as_posix()
    entry["result_analysis_workbook"] = relative
    entry["result_analysis_report"] = f"{relative}#结论稳定性汇总"
    entry["analysis_methods"] = list(result.methods)
    hashes = entry.setdefault("artifact_hashes", {})
    hashes["result_analysis_workbook"] = _file_hash(analysis_path)
    entry.setdefault("validated_artifact_hashes", {}).pop("result_analysis_workbook", None)
    if result.status == "passed":
        entry["analysis_execution_status"] = "workbook_received"
        entry["result_analysis_status"] = "pending"
        entry["execution_note"] = "深化工作簿已由用户本地运行生成，等待validate_user_execution.py验收"
        entry["status"] = "solved"
        entry["artifacts_stale"] = True
        entry["stale_layers"] = sorted(set(entry.get("stale_layers", [])) | {
            "result_analysis_workbook", "matlab_script", "figure_bundle", "framework",
        })
        state.setdefault("project", {})["current_phase"] = "result_analysis"
    elif result.status == "failed":
        entry["analysis_execution_status"] = "rejected"
        entry["result_analysis_status"] = "failed"
        entry["validation_status"] = "pending"
        state.setdefault("project", {})["current_phase"] = "result_analysis"
    else:
        entry["analysis_execution_status"] = "redo_required"
        entry["result_analysis_status"] = "redo_required"
        entry["status"] = "designed"
        entry["validation_status"] = "pending"
        entry["result_summary_status"] = "stale"
        entry["artifacts_stale"] = True
        entry["stale_layers"] = sorted(set(entry.get("stale_layers", [])) | set(result.stale_layers))
        entry["proposition_refs"] = []
        state.setdefault("project", {})["current_phase"] = result.restart_phase
        state.setdefault("paper_framework", {})["sync_status"] = "stale"
    _write_state(path, state)


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
    """完整主求解；失败证据先落盘，再阻断结果深化分析。"""
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
    failures = _quality_failures(quality_report)
    solution_path, _ = workbook_paths(config.project_root, config.problem_name)
    write_workbook(
        solution_path,
        build_solution_tables(solution, constraints, quality_report, audit),
        workbook_kind="solution",
        objective=config.objective,
        structures=config.structures,
        capabilities=config.capabilities,
        require_quality_passed=False,
    )
    primary = PrimarySolveResult(context, solution_path, quality_report, constraints)
    framework_sync_hook(primary)
    _update_primary_state(primary, passed=not failures)
    if failures:
        raise RuntimeError(
            f"主结果质量门未通过；失败证据已写入 {solution_path.as_posix()}，禁止进入结果深化分析: {failures}"
        )
    logger.info("主求解结果已通过质量门并写入: %s", solution_path.as_posix())
    return primary


def run_result_analysis_pipeline(
    primary: PrimarySolveResult,
    *,
    analysis_hook: ResultAnalysisHook,
    framework_sync_hook: AnalysisFrameworkSyncHook,
) -> Path:
    """写入题目专属分析；failed/redo_required 均阻断绘图和写作。"""
    assert_primary_quality(primary.quality_report)
    result = _normalize_analysis_result(analysis_hook(primary))
    _, analysis_path = workbook_paths(
        primary.context.config.project_root,
        primary.context.config.problem_name,
    )
    config = primary.context.config
    write_workbook(
        analysis_path,
        result.tables,
        workbook_kind="result_analysis",
        objective=config.objective,
        structures=config.structures,
        capabilities=config.capabilities,
    )
    framework_sync_hook(primary, analysis_path, result.tables)
    _update_analysis_state(primary, analysis_path, result)
    if result.status == "failed":
        raise RuntimeError(f"结果深化分析未通过；证据已写入 {analysis_path.as_posix()}: {result.reason}")
    if result.status == "redo_required":
        raise RuntimeError(
            f"结果深化分析要求回退到 {result.restart_phase}；下游产物已标记 stale: {result.reason}"
        )
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
    """一键编排器；内部保持主求解和结果深化分析两道独立门。"""
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
