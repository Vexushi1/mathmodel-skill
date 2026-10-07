"""Current package paths, derived from existing state/output contracts.

This is a collection/completeness check, not a replacement for execution, figure,
or compile attestation gates. Archive creation alone does not grant validation.
"""
from __future__ import annotations

from glob import has_magic
import hashlib
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

import yaml
import run_config_parser
import safe_yaml
import stage_code as STAGE_CODE
from stage_inputs import input_files, observe_inputs

from project_snapshot import chinese_question_name, data_source_files, question_number

OUTPUT_CONTRACT = Path(__file__).resolve().parents[1] / "core/output_contract.yaml"
Observer = Callable[[Path, bytes], None]


def _read_bytes(path: Path, observe: Observer | None) -> bytes:
    payload = path.read_bytes()
    if observe is not None:
        observe(path, payload)
    return payload


def _read_yaml(path: Path, observe: Observer | None) -> Any:
    return safe_yaml.safe_load(_read_bytes(path, observe)) or {}


def selected_latex_entrypoint(state: Mapping[str, Any]) -> str | None:
    """Return the exact B2 1.5 LaTeX carrier selected by project state."""
    framework = state.get("paper_framework")
    policy = framework.get("claim_consumption_policy") if isinstance(framework, Mapping) else None
    source = policy.get("paper_source") if isinstance(policy, Mapping) else None
    if (
        isinstance(source, Mapping)
        and (policy.get("protocol_version"), policy.get("mode"))
        == ("1.5.0", "enforce_selected_paper_claim_chain")
        and source.get("format") == "latex"
        and isinstance(source.get("entrypoint"), str)
        and source["entrypoint"].strip()
    ):
        return source["entrypoint"]
    return None


def latex_artifact_defaults(state: Mapping[str, Any]) -> tuple[str, str, str]:
    """Resolve package proof defaults without overriding the selected B2 carrier."""
    artifacts = state.get("artifacts") or {}
    selected = selected_latex_entrypoint(state)
    source = selected or artifacts.get("latex_source") or "final_latex/main.tex"
    source_path = Path(str(source))
    pdf = (source_path.with_suffix(".pdf").as_posix() if selected
           else artifacts.get("compiled_pdf") or "final_latex/main.pdf")
    report = artifacts.get("compile_report") or (
        (source_path.parent / "compile_report.yaml").as_posix()
        if selected else "final_latex/compile_report.yaml"
    )
    return str(source), str(pdf), str(report)


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


def bound_compile_files(root: Path, state: Mapping[str, Any], *,
                        observe: Observer | None = None) -> tuple[set[Path], list[str]]:
    """Retain current v4/v5 report-bound log/recorder auxiliaries, never all logs."""
    root = root.resolve()
    artifacts = state.get("artifacts") or {}
    selected = selected_latex_entrypoint(state)
    source_raw, pdf_raw, report_raw = latex_artifact_defaults(state)
    issues: list[str] = []
    files: set[Path] = set()
    try:
        expected_source = project_path(root, source_raw)
        if selected and artifacts.get("latex_source"):
            declared_source = project_path(root, artifacts["latex_source"])
            if declared_source != expected_source:
                raise ValueError("artifacts.latex_source与选定B2 paper_source不一致")
        if selected and artifacts.get("compiled_pdf"):
            declared_pdf = project_path(root, artifacts["compiled_pdf"])
            if declared_pdf != project_path(root, pdf_raw):
                raise ValueError("artifacts.compiled_pdf与选定B2 paper_source输出不一致")
        report_path = project_path(root, report_raw)
        if not report_path.is_file():
            return files, issues
        report = _read_yaml(report_path, observe)
        if not isinstance(report, Mapping) or str(report.get("report_schema_version")) not in {"4.0.0", "5.0.0"}:
            return files, issues  # Historical reports do not acquire a new recorder requirement.
        latex_root = report_path.parent
        main = project_path(latex_root, report.get("main"))
        if main != expected_source:
            if selected:
                raise ValueError("compile_report.main与选定B2 paper_source不一致")
            if artifacts.get("latex_source"):
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
            elif hashlib.sha256(_read_bytes(path, observe)).hexdigest() != report.get(field):
                issues.append(f"当前编译报告绑定文件哈希不一致: {relative} ({field})")
            else:
                files.add(path)
    except (ValueError, OSError, yaml.YAMLError) as exc:
        issues.append(f"无法保留当前编译证明: {exc}")
    return files, issues


def reproducibility_requirements(root: Path, state: Mapping[str, Any], *,
                                 observe: Observer | None = None) -> tuple[set[str], list[str]]:
    """Derive the required set from current project state, independently of the ZIP."""
    root = root.resolve()
    contract = _read_yaml(OUTPUT_CONTRACT, observe)
    if not isinstance(contract, Mapping):
        raise ValueError("output contract必须是映射")
    required: set[str] = set()
    issues: list[str] = []

    def require(raw: Any) -> None:
        try:
            required.add(project_path(root, raw).relative_to(root).as_posix())
        except ValueError as exc:
            issues.append(str(exc))

    artifacts = state.get("artifacts") or {}
    source_raw, pdf_raw, report_raw = latex_artifact_defaults(state)
    require(contract["project_root"]["project_state"])
    require((state.get("paper_framework") or {}).get("path") or contract["model_paper_framework"]["path"])
    require(pdf_raw)
    require(source_raw)
    if (state.get("data") or {}).get("sources"):
        files, _, source_issues, _ = data_source_files(root, state)
        issues.extend(source_issues)
        for path in files:
            require(path)  # Recheck each expanded member's boundary, including symlinks.
    for path in artifacts.get("approved_figures") or []:
        require(path)
    raw_report = report_raw
    try:
        report_path = project_path(root, raw_report)
        if artifacts.get("compile_report") or report_path.is_file():
            require(raw_report)
        if report_path.is_file():
            report = _read_yaml(report_path, observe)
            if isinstance(report, Mapping):
                schema_version = str(report.get("report_schema_version"))
                is_v4 = schema_version == "4.0.0"
                is_v5 = schema_version == "5.0.0"
                audit = report.get("latex_audit_report") or "latex_audit_report.yaml"
                if is_v4 or is_v5 or report.get("latex_audit_report") or (report_path.parent / audit).is_file():
                    require(project_path(report_path.parent, audit))
                if is_v4 or is_v5:
                    source_root = project_path(report_path.parent, report.get("main")).parent if is_v4 else root
                    for field in ("source_files", "actual_input_files"):
                        for record in report.get(field) or []:
                            if not isinstance(record, Mapping):
                                raise ValueError(f"compile_report.{field}含非法文件记录")
                            require(project_path(source_root, record.get("path")))
    except (ValueError, OSError, yaml.YAMLError) as exc:
        issues.append(f"无法解析当前编译证明必需文件: {exc}")
    bound, bound_issues = bound_compile_files(root, state, observe=observe)
    required.update(path.relative_to(root).as_posix() for path in bound)
    issues.extend(bound_issues)

    questions = state.get("subproblems") or {}
    if not isinstance(questions, Mapping) or not questions:
        issues.append("缺少当前subproblems，无法确认逐问复现完整性；历史包可读取，须登记当前问题及产物后重新打包验证")
        questions = {}
    try:
        project_backend = STAGE_CODE.current_project_backend(state, required=bool(questions))
    except STAGE_CODE.StageCodeError as exc:
        project_backend = None
        issues.append(f"项目数值后端: {exc}")
    per_question = contract["per_question"]
    for key, entry in questions.items():
        if not isinstance(entry, Mapping):
            issues.append(f"{key}: subproblem状态必须是映射")
            continue
        question = chinese_question_name(str(key))
        number = question_number(question)

        def question_path(field: str, pattern: str, *, allow_default: bool = False) -> None:
            declared = entry.get(field)
            if declared:
                require(declared)
            elif not allow_default:
                issues.append(f"{key}: {field}缺少当前状态登记，目录旧文件不能取得正式包资格")
            elif number is None:
                issues.append(f"{key}: 无法推导{field}，请登记当前精确路径")
            else:
                tokens = {"中文序号": question.removeprefix("问题"), "阿拉伯序号": number}
                require(per_question["question_directory"].format(**tokens) + pattern.format(**tokens))

        def verified_workbook(field: str, pattern: str) -> None:
            question_path(field, pattern)
            declared = entry.get(field)
            if not declared or number is None:
                return
            tokens = {"中文序号": question.removeprefix("问题"), "阿拉伯序号": number}
            expected = per_question["question_directory"].format(**tokens) + pattern.format(**tokens)
            try:
                path = project_path(root, declared)
                if path != project_path(root, expected):
                    issues.append(f"{key}: {field}不是当前标准工作簿: {declared}")
                    return
                validated = (entry.get("validated_artifact_hashes") or {}).get(field)
                if not isinstance(validated, str) or len(validated) != 64:
                    issues.append(f"{key}: {field}缺少已验收SHA-256绑定")
                elif not path.is_file() or hashlib.sha256(_read_bytes(path, observe)).hexdigest() != validated.lower():
                    issues.append(f"{key}: {field}当前文件与已验收SHA-256绑定不一致")
            except (ValueError, OSError) as exc:
                issues.append(f"{key}: {field}: {exc}")

        def require_stage(stage: str) -> None:
            field = "code" if stage == "primary" else "result_analysis_code"
            contract_stage = "primary" if stage == "primary" else "result_analysis"
            execution = entry.get("solver_execution", {})
            if not isinstance(execution, Mapping) or not isinstance(execution.get(stage, {}), Mapping):
                issues.append(f"{key}: {stage}后端状态必须是映射")
                return
            if project_backend is None:
                issues.append(f"{key}: {stage}缺少当前项目数值后端")
                return
            patterns = (per_question.get("solver_scripts") or {}).get(project_backend)
            if patterns is None:
                issues.append(f"{key}: 未知求解后端 {project_backend}")
                return
            question_path(field, patterns[contract_stage])
            if not entry.get(field):
                return
            try:
                code = STAGE_CODE.resolve_stage_code(
                    root, question, stage, entry=entry, project_backend=project_backend,
                )
                if code is None:
                    issues.append(f"{key}: {stage}当前登记入口不存在")
                    return
                source = _read_bytes(code.path, observe)
                _, config = run_config_parser.parse_embedded_config(
                    source.decode("utf-8-sig"), messages=run_config_parser.DELIVERY_MESSAGES,
                    backend=code.backend,
                )
                dependency_paths = [STAGE_CODE._relative_path(root, record["path"])
                                    for record in config.get("code_dependencies", [])]
                data_paths = input_files(root, config.get("data_paths"))
                if config.get("auxiliary_data_paths"):
                    data_paths.extend(input_files(root, config["auxiliary_data_paths"]))
                if observe is not None:
                    for path in dependency_paths + data_paths:
                        _read_bytes(path, observe)
                issues.extend(f"{key}: {item}" for item in STAGE_CODE.validate_stage_binding(
                    root, entry, stage, require_validated=True, project_backend=project_backend,
                ))
                fingerprint = STAGE_CODE.stage_code_fingerprint(
                    root, code.path, config.get("code_dependencies", []),
                )
                for record in fingerprint["files"]:
                    require(record["path"])
                    if observe is not None:
                        path = project_path(root, record["path"])
                        if hashlib.sha256(_read_bytes(path, observe)).hexdigest() != record["sha256"]:
                            raise ValueError("源码在提交要求检查期间变化: " + record["path"])
                observation = observe_inputs(root, config, state)
                issues.extend(f"{key}: {stage}: {item}" for item in observation["issues"])
                for relative in observation["paths"]:
                    require(relative)
                    if observe is not None:
                        _read_bytes(project_path(root, relative), observe)
                if stage == "analysis" and str(config.get("data_sha256", "")).lower() != str(entry.get("data_hash", "")).lower():
                    issues.append(f"{key}: analysis data_sha256必须继承主结果data_hash，不得覆盖主数据身份")
            except (ValueError, TypeError, KeyError, SyntaxError, OSError) as exc:
                issues.append(f"{key}: {exc}")

        require_stage("primary")
        if entry.get("primary_execution_status") != "accepted":
            issues.append(f"{key}: 正式包要求已验收主求解执行状态")
        verified_workbook("solution_workbook", per_question["mandatory_workbooks"]["solution"])
        question_path("matlab_script", per_question["matlab_script"], allow_default=True)
        status = entry.get("result_analysis_status")
        reason = str(entry.get("result_analysis_requirement_reason") or "").strip()
        if status == "not_required":
            if not reason:
                issues.append(f"{key}: not_required缺少result_analysis_requirement_reason，不能确认03B豁免")
            analysis_record = (entry.get("solver_execution") or {}).get("analysis")
            if any(entry.get(field) for field in (
                "result_analysis_code", "analysis_code_sha256", "result_analysis_workbook",
            )) or analysis_record:
                issues.append(f"{key}: not_required阶段仍登记当前analysis数值身份")
        elif status in {"passed", "failed", "redo_required"} or (reason and entry.get("analysis_methods")):
            # Existing activated chains remain readable; new acceptance still uses its own gate.
            require_stage("analysis")
            if entry.get("analysis_execution_status") != "accepted":
                issues.append(f"{key}: 正式包要求已验收结果深化分析执行状态")
            verified_workbook("result_analysis_workbook", per_question["conditional_workbooks"]["result_analysis"]["path"])
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


def current_analysis_artifacts(root: Path, state: Mapping[str, Any], *,
                               required_files: Iterable[str] | None = None,
                               observe: Observer | None = None) -> tuple[set[str], list[str]]:
    """Exclude only contract-bound inactive analysis paths in a current project.

    Legacy backups without a current project-root backend retain broad collection,
    never modern delivery qualification. Current source/input dependencies are kept.
    """
    root = root.resolve()
    questions = state.get("subproblems")
    if not questions:
        return set(), []
    if not isinstance(questions, Mapping):
        return set(), ["subproblems必须是映射，无法选择当前分析产物"]
    execution = state.get("execution")
    if execution is None or (isinstance(execution, Mapping) and not any(
        field in execution for field in ("solver_backend", "solver_backend_selection_reason")
    )):
        return set(), []  # Dedicated legacy backup boundary; requirements still reject formal delivery.
    if not isinstance(execution, Mapping):
        return set(), ["execution必须是映射，不能按legacy备份豁免"]
    contract = _read_yaml(OUTPUT_CONTRACT, observe)
    per_question = contract["per_question"]
    try:
        backend = STAGE_CODE.current_project_backend(state)
    except STAGE_CODE.StageCodeError as exc:
        return set(), ["项目数值后端: " + str(exc)]
    excluded: set[str] = set()
    issues: list[str] = []
    for key, entry in questions.items():
        if not isinstance(entry, Mapping):
            issues.append(f"{key}: subproblem状态必须是映射")
            continue
        try:
            question = chinese_question_name(str(key))
            number = question_number(question)
            if number is None:
                raise ValueError("无法解析问题编号")
            tokens = {"中文序号": question.removeprefix("问题"), "阿拉伯序号": number}
            directory = per_question["question_directory"].format(**tokens)
            scripts = {name: directory + patterns["result_analysis"].format(**tokens)
                       for name, patterns in per_question["solver_scripts"].items()}
            workbook = directory + per_question["conditional_workbooks"]["result_analysis"]["path"].format(**tokens)
            legacy = per_question["legacy_compatibility"]
            old_workbook = legacy["sensitivity_robustness_filename"].format(**tokens)
            old_script = per_question["solver_scripts"]["python"]["result_analysis"].format(**tokens)
            candidates = {workbook, old_script, *scripts.values(), directory + old_workbook,
                          legacy["result_directory"].format(**tokens) + old_workbook}
            candidates.update(str(entry[field]) for field in (
                "result_analysis_code", "result_analysis_workbook", "robustness_workbook",
            ) if entry.get(field))
            current: set[str] = set()
            if entry.get("result_analysis_status") != "not_required":
                current.add(str(entry.get("result_analysis_workbook") or workbook))
                if entry.get("result_analysis_code"):
                    current.add(str(entry["result_analysis_code"]))
                else:
                    current.update([scripts[backend]] if backend else scripts.values())
            def normalize(raw: str) -> str:
                return STAGE_CODE._relative_path(root, raw).relative_to(root).as_posix()

            excluded.update({normalize(raw) for raw in candidates} - {normalize(raw) for raw in current})
        except (ValueError, TypeError, KeyError, OSError) as exc:
            issues.append(f"{key}: 无法选择当前分析产物: {exc}")
    if required_files is None:
        required_files, _ = reproducibility_requirements(root, state, observe=observe)
    required = {project_path(root, path).relative_to(root).as_posix() for path in required_files}
    protected: set[str] = set()
    if excluded & required:
        for key, entry in questions.items():
            if not isinstance(entry, Mapping):
                continue
            stages = ["primary"] if entry.get("result_analysis_status") == "not_required" else ["primary", "analysis"]
            for stage in stages:
                if not entry.get("code" if stage == "primary" else "result_analysis_code"):
                    continue
                try:
                    code = STAGE_CODE.resolve_stage_code(
                        root, chinese_question_name(str(key)), stage, entry=entry, project_backend=backend,
                    )
                    if code is None:
                        continue
                    _, config = run_config_parser.parse_embedded_config(
                        _read_bytes(code.path, observe).decode("utf-8-sig"),
                        messages=run_config_parser.DELIVERY_MESSAGES, backend=code.backend,
                    )
                    references = [code.path.relative_to(root).as_posix(),
                                  *(record["path"] for record in config.get("code_dependencies", []))]
                    protected.update(STAGE_CODE._relative_path(root, raw).relative_to(root).as_posix()
                                     for raw in references)
                    actual_inputs = input_files(root, config.get("data_paths"))
                    if config.get("auxiliary_data_paths"):
                        actual_inputs.extend(input_files(root, config["auxiliary_data_paths"]))
                    protected.update(path.relative_to(root).as_posix() for path in actual_inputs)
                except (ValueError, TypeError, KeyError, SyntaxError, OSError) as exc:
                    issues.append(f"{key}: 无法保留当前{stage}依赖: {exc}")
    protected.intersection_update(required)
    return excluded - protected, issues
