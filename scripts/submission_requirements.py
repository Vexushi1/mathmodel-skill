"""Current package paths, derived from existing state/output contracts.

This is a collection/completeness check, not a replacement for execution, figure,
or compile attestation gates. Archive creation alone does not grant validation.
"""
from __future__ import annotations

from glob import has_magic
import hashlib
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml
import stage_code as STAGE_CODE

from project_snapshot import chinese_question_name, data_source_files, question_number

OUTPUT_CONTRACT = Path(__file__).resolve().parents[1] / "core/output_contract.yaml"


def project_path(root: Path, raw: Any) -> Path:
    """Canonicalize a registered path without allowing a project-boundary escape."""
    if not str(raw or "").strip():
        raise ValueError("项目必需文件路径为空")
    path = (root.resolve() / str(raw)).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"必需文件路径越出项目根目录: {raw}") from exc
    return path


def expand_required_allowlist(root: Path, patterns: Iterable[str]) -> list[Path]:
    """Exact entries are required; glob entries retain zero-match compatibility."""
    root = root.resolve()
    files: set[Path] = set()
    for raw in patterns:
        pattern = str(raw).strip()
        if not pattern:
            raise ValueError("submission_files allowlist含空路径")
        if Path(pattern).is_absolute():
            raise ValueError(f"submission_files必须是项目相对路径: {pattern}")
        if not has_magic(pattern):
            path = project_path(root, pattern)
            if not path.is_file():
                raise ValueError(f"submission_files必需精确文件不存在: {pattern}")
            files.add(path)
        else:
            for candidate in root.glob(pattern):
                if candidate.is_file():
                    files.add(project_path(root, candidate))
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def bound_compile_files(root: Path, state: Mapping[str, Any]) -> tuple[set[Path], list[str]]:
    """Retain only current v4 report-bound log/recorder auxiliaries, never all logs."""
    root = root.resolve()
    artifacts = state.get("artifacts") or {}
    issues: list[str] = []
    files: set[Path] = set()
    try:
        report_path = project_path(root, artifacts.get("compile_report") or "final_latex/compile_report.yaml")
        if not report_path.is_file():
            return files, issues
        report = yaml.safe_load(report_path.read_text(encoding="utf-8")) or {}
        if not isinstance(report, Mapping) or str(report.get("report_schema_version")) != "4.0.0":
            return files, issues  # Historical reports do not acquire a new recorder requirement.
        latex_root = report_path.parent
        main = project_path(latex_root, report.get("main"))
        if artifacts.get("latex_source") and main != project_path(root, artifacts["latex_source"]):
            raise ValueError("compile_report.main与当前latex_source不一致")
        recorder = project_path(latex_root, main.with_suffix(".fls"))
        if report.get("recorder") != recorder.name:
            raise ValueError("compile_report.recorder不是当前main绑定的.fls文件名")
        log = project_path(latex_root, report.get("log"))
        if log.suffix.lower() != ".log":
            raise ValueError("compile_report.log不是.log文件")
        for path, field in ((recorder, "recorder_sha256"), (log, "log_sha256")):
            relative = path.relative_to(root).as_posix()
            if not path.is_file():
                issues.append(f"当前编译报告绑定文件不存在: {relative}")
            elif hashlib.sha256(path.read_bytes()).hexdigest() != report.get(field):
                issues.append(f"当前编译报告绑定文件哈希不一致: {relative} ({field})")
            else:
                files.add(path)
    except (ValueError, OSError, yaml.YAMLError) as exc:
        issues.append(f"无法保留当前编译证明: {exc}")
    return files, issues


def reproducibility_requirements(root: Path, state: Mapping[str, Any]) -> tuple[set[str], list[str]]:
    """Derive the required set from current project state, independently of the ZIP."""
    root = root.resolve()
    contract = yaml.safe_load(OUTPUT_CONTRACT.read_text(encoding="utf-8"))
    required: set[str] = set()
    issues: list[str] = []

    def require(raw: Any) -> None:
        try:
            required.add(project_path(root, raw).relative_to(root).as_posix())
        except ValueError as exc:
            issues.append(str(exc))

    artifacts = state.get("artifacts") or {}
    require(contract["project_root"]["project_state"])
    require((state.get("paper_framework") or {}).get("path") or contract["model_paper_framework"]["path"])
    require(artifacts.get("compiled_pdf") or "final_latex/main.pdf")
    require(artifacts.get("latex_source") or "final_latex/main.tex")
    if (state.get("data") or {}).get("sources"):
        files, _, source_issues, _ = data_source_files(root, state)
        issues.extend(source_issues)
        for path in files:
            require(path)  # Recheck each expanded member's boundary, including symlinks.
    for path in artifacts.get("approved_figures") or []:
        require(path)
    raw_report = artifacts.get("compile_report") or "final_latex/compile_report.yaml"
    try:
        report_path = project_path(root, raw_report)
        if artifacts.get("compile_report") or report_path.is_file():
            require(raw_report)
        if report_path.is_file():
            report = yaml.safe_load(report_path.read_text(encoding="utf-8")) or {}
            if isinstance(report, Mapping):
                is_v4 = str(report.get("report_schema_version")) == "4.0.0"
                audit = report.get("latex_audit_report") or "latex_audit_report.yaml"
                if is_v4 or report.get("latex_audit_report") or (report_path.parent / audit).is_file():
                    require(project_path(report_path.parent, audit))
                if is_v4:
                    source_root = project_path(report_path.parent, report.get("main")).parent
                    for field in ("source_files", "actual_input_files"):
                        for record in report.get(field) or []:
                            if not isinstance(record, Mapping):
                                raise ValueError(f"compile_report.{field}含非法文件记录")
                            require(project_path(source_root, record.get("path")))
    except (ValueError, OSError, yaml.YAMLError) as exc:
        issues.append(f"无法解析当前编译证明必需文件: {exc}")
    bound, bound_issues = bound_compile_files(root, state)
    required.update(path.relative_to(root).as_posix() for path in bound)
    issues.extend(bound_issues)

    questions = state.get("subproblems") or {}
    if not isinstance(questions, Mapping) or not questions:
        issues.append("缺少当前subproblems，无法确认逐问复现完整性；历史包可读取，须登记当前问题及产物后重新打包验证")
        questions = {}
    per_question = contract["per_question"]
    for key, entry in questions.items():
        if not isinstance(entry, Mapping):
            issues.append(f"{key}: subproblem状态必须是映射")
            continue
        question = chinese_question_name(str(key))
        number = question_number(question)

        def question_path(field: str, pattern: str) -> None:
            declared = entry.get(field)
            if declared:
                require(declared)
            elif number is None:
                issues.append(f"{key}: 无法推导{field}，请登记当前精确路径")
            else:
                tokens = {"中文序号": question.removeprefix("问题"), "阿拉伯序号": number}
                require(per_question["question_directory"].format(**tokens) + pattern.format(**tokens))

        def require_stage(stage: str) -> None:
            field = "code" if stage == "primary" else "result_analysis_code"
            contract_stage = "primary" if stage == "primary" else "result_analysis"
            execution = entry.get("solver_execution", {})
            if not isinstance(execution, Mapping) or not isinstance(execution.get(stage, {}), Mapping):
                issues.append(f"{key}: {stage}后端状态必须是映射")
                return
            selection = execution.get(stage) or {}
            backend = selection.get("backend", "python")
            if not isinstance(backend, str):
                issues.append(f"{key}: {stage}后端必须为python或matlab")
                return
            patterns = (per_question.get("solver_scripts") or {}).get(backend)
            if patterns is None and backend == "python":
                patterns = per_question["python_scripts"]
            if patterns is None:
                issues.append(f"{key}: 未知求解后端 {backend}")
                return
            question_path(field, patterns[contract_stage])
            try:
                declared = str(entry.get(field) or "")
                if not selection and declared.endswith(".py"):
                    # Historical package collection accepted explicitly registered
                    # Python paths; do not impose new solver naming retrospectively.
                    legacy_path = project_path(root, declared)
                    if not legacy_path.is_file():
                        return
                    try:
                        _, legacy_config = STAGE_CODE.parse_stage_config(legacy_path, "python")
                    except (ValueError, SyntaxError):
                        return
                    if legacy_config.get("run_receipt_protocol_version") != "1.1.0":
                        return
                code = STAGE_CODE.resolve_stage_code(root, question, stage, entry=entry)
                if code and STAGE_CODE.requires_bundle_binding(root, {**entry, field: code.path.relative_to(root).as_posix()}, stage):
                    issues.extend(f"{key}: {item}" for item in STAGE_CODE.validate_stage_binding(
                        root, entry, stage, require_validated=True,
                    ))
                    _, config = STAGE_CODE.parse_stage_config(code.path, code.backend)
                    fingerprint = STAGE_CODE.stage_code_fingerprint(
                        root, code.path, config.get("code_dependencies", []),
                    )
                    for record in fingerprint["files"]:
                        require(record["path"])
            except (ValueError, TypeError, OSError) as exc:
                issues.append(f"{key}: {exc}")

        require_stage("primary")
        question_path("solution_workbook", per_question["mandatory_workbooks"]["solution"])
        question_path("matlab_script", per_question["matlab_script"])
        status = entry.get("result_analysis_status")
        reason = str(entry.get("result_analysis_requirement_reason") or "").strip()
        if status == "not_required":
            if not reason:
                issues.append(f"{key}: not_required缺少result_analysis_requirement_reason，不能确认03B豁免")
        elif status in {"passed", "failed", "redo_required"} or (reason and entry.get("analysis_methods")):
            # Existing activated chains remain readable; new acceptance still uses its own gate.
            require_stage("analysis")
            question_path("result_analysis_workbook", per_question["conditional_workbooks"]["result_analysis"]["path"])
        else:
            issues.append(f"{key}: Analysis Necessity Gate尚未明确，须登记required计划或带理由的not_required后重新验证")

    preprocessing = state.get("preprocessing") or {}
    if preprocessing.get("decision") == "project_level":
        layout = contract["global_preprocessing"]
        for field, filename in (("code", "python_script"), ("workbook", "workbook"), (None, "matlab_script")):
            require(preprocessing.get(field) or layout["directory"] + layout[filename])
    elif preprocessing.get("decision") not in {"not_needed", "question_local"}:
        issues.append("preprocessing.decision尚未明确，无法确认项目级预处理必需集合；请登记当前决策后重新验证")
    return required, issues
