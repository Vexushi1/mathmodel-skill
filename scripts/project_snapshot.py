#!/usr/bin/env python3
"""Project artifact discovery and per-question snapshots extracted mechanically from sync_project."""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

import artifact_fingerprint as ARTIFACT_FINGERPRINT
import stage_code as STAGE_CODE
from stage_inputs import observe_inputs

SKILL_ROOT = Path(__file__).resolve().parent.parent

def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

WORKBOOK_VALIDATION = _load_module(
    "hsk_project_snapshot_workbook_validation",
    SKILL_ROOT / "templates/code" / "hsk_pipeline" / "workbook_validation.py",
)

sha256_file = ARTIFACT_FINGERPRINT.sha256_file
combined_hash = ARTIFACT_FINGERPRINT.combined_hash
framework_section_hash = ARTIFACT_FINGERPRINT.framework_section_hash

QUESTION_RE = re.compile(r"问题([一二三四五六七八九十百]+)")

MATLAB_TITLE_RE = re.compile(r"\b(?:title|sgtitle)\s*\(", re.IGNORECASE)

EXPORT_RE = re.compile(
    r"(?:exportgraphics|print)\s*\([^\n]*?[\"']([^\"']+\.(?:png|pdf|svg|tif|tiff|jpg|jpeg))[\"']",
    re.IGNORECASE,
)

WORKBOOK_REF_RE = re.compile(r"[\"']([^\"']+\.xlsx)[\"']", re.IGNORECASE)

FIGURE_SUFFIXES = {".png", ".pdf", ".svg", ".tif", ".tiff", ".jpg", ".jpeg"}

DATA_SUFFIXES = {".csv", ".xlsx", ".xls", ".json", ".yaml", ".yml", ".txt"}

SOLVED_STATUSES = {"solved", "analyzed", "validated", "written", "completed"}

ANALYZED_STATUSES = {"analyzed", "validated", "written", "completed"}

VALID_PREPROCESSING_DECISIONS = {"not_needed", "question_local", "project_level"}


def question_key(chinese_name: str) -> str:
    number = STAGE_CODE.question_number(chinese_name)
    return f"Q{number}" if number else chinese_name

def chinese_question_name(key: str) -> str:
    return STAGE_CODE.question_name(key)

def question_number(chinese_name: str) -> int | None:
    return STAGE_CODE.question_number(chinese_name)

def preprocessing_decision(state: Mapping[str, Any]) -> str | None:
    value = str(((state.get("preprocessing") or {}).get("decision", ""))).strip()
    return value if value in VALID_PREPROCESSING_DECISIONS else None

def data_source_files(
    root: Path, state: Mapping[str, Any]
) -> tuple[list[Path], str, list[str], list[str]]:
    root = root.resolve()
    issues: list[str] = []
    warnings: list[str] = []
    entries = ((state.get("data") or {}).get("sources") or []) if state else []
    files: list[Path] = []
    if entries:
        for entry in entries:
            relative = str((entry or {}).get("path", "")).strip()
            if not relative:
                issues.append("data.sources 存在空路径")
                continue
            path = (root / relative).resolve()
            try:
                path.relative_to(root)
            except ValueError:
                issues.append(f"data.sources 路径越出项目根目录: {relative}")
                continue
            if path.is_file():
                files.append(path)
            elif path.is_dir():
                files.extend(item for item in path.rglob("*") if item.is_file())
            else:
                issues.append(f"data.sources 文件不存在: {relative}")
        return files, "declared_sources", issues, warnings
    for path in root.iterdir() if root.is_dir() else []:
        if path.is_file() and not path.name.startswith("."):
            if path.name not in {"模型论文框架.md", "sync_report.yaml"} and path.suffix.lower() in DATA_SUFFIXES:
                files.append(path)
    warnings.append("项目状态未声明data.sources；data hash使用受限根目录数据文件回退扫描")
    return files, "fallback_scan", issues, warnings

def active_data_hash(
    root: Path,
    state: Mapping[str, Any],
    raw_files: Iterable[Path],
    raw_mode: str,
) -> tuple[str | None, str, list[str]]:
    """Select raw or accepted unified workbook as the downstream data hash fact source."""
    decision = preprocessing_decision(state)
    warnings: list[str] = []
    raw_hash = combined_hash(raw_files, root)
    if decision != "project_level":
        return raw_hash, raw_mode, warnings
    preprocessing = state.get("preprocessing") or {}
    workbook_rel = str(preprocessing.get("workbook") or "数据预处理/数据预处理结果.xlsx")
    workbook = (root / workbook_rel).resolve()
    if (
        preprocessing.get("status") == "accepted"
        and preprocessing.get("quality_status") == "passed"
        and workbook.is_file()
    ):
        return sha256_file(workbook), "preprocessing_workbook", warnings
    warnings.append("preprocessing_decision=project_level但统一预处理工作簿尚未accepted；当前data hash仍使用原始数据，仅可用于预处理阶段")
    return raw_hash, "raw_project_level_pending", warnings

def _classification(entry: Mapping[str, Any]):
    classification = entry.get("classification") or {}
    objective = classification.get("objective")
    structures = tuple(classification.get("structures", []) or [])
    old = entry.get("problem_types") or {}
    labels = [old.get("primary"), *(old.get("secondary", []) or [])]
    problem_types = tuple(dict.fromkeys(str(item) for item in labels if item))
    capabilities = entry.get("capabilities")
    return objective, structures, problem_types, capabilities if isinstance(capabilities, Mapping) else None

def _question_dir(root: Path, chinese_name: str) -> Path:
    current = root / f"{chinese_name}求解"
    if current.is_dir():
        return current
    return root / "结果数据表" / chinese_name

def _question_names(root: Path, state: Mapping[str, Any]) -> list[str]:
    names = {chinese_question_name(str(key)) for key in (state.get("subproblems") or {})}
    names.update(
        path.name.removesuffix("求解")
        for path in root.glob("问题*求解")
        if path.is_dir() and QUESTION_RE.fullmatch(path.name.removesuffix("求解"))
    )
    result_root = root / "结果数据表"
    if result_root.is_dir():
        names.update(
            path.name for path in result_root.iterdir()
            if path.is_dir() and QUESTION_RE.fullmatch(path.name)
        )
    return sorted(names, key=lambda value: question_number(value) or 999)

def _stage_code_paths(root: Path, chinese_name: str) -> tuple[Path | None, Path | None, bool]:
    current_dir = root / f"{chinese_name}求解"
    primary = current_dir / f"{chinese_name}求解.py"
    analysis = current_dir / f"{chinese_name}结果深化分析.py"
    if primary.is_file() or analysis.is_file():
        legacy_single = primary.is_file() and not analysis.is_file()
        return primary if primary.is_file() else None, analysis if analysis.is_file() else None, legacy_single
    legacy_primary = root / f"{chinese_name}求解.py"
    legacy_analysis = root / f"{chinese_name}结果深化分析.py"
    return (
        legacy_primary if legacy_primary.is_file() else None,
        legacy_analysis if legacy_analysis.is_file() else None,
        legacy_primary.is_file() and not legacy_analysis.is_file(),
    )

def _python_files(root: Path, chinese_name: str) -> list[Path]:
    primary, analysis, _ = _stage_code_paths(root, chinese_name)
    return [path for path in (primary, analysis) if path is not None]


def _solver_observations(
    root: Path, question: str, entry: Mapping[str, Any],
    *, project_backend: str | None = None, current_state: bool = False,
) -> tuple[dict[str, Any], dict[str, Path | None], list[str]]:
    """Observe current implementation bytes without updating delivered identities."""
    root = root.resolve()
    observed: dict[str, Any] = {}
    paths: dict[str, Path | None] = {"primary": None, "analysis": None}
    issues: list[str] = []
    selections = entry.get("solver_execution", {})
    if not isinstance(selections, Mapping):
        return observed, paths, ["solver_execution必须为映射"]
    for stage in paths:
        field = "code" if stage == "primary" else "result_analysis_code"
        hash_field = f"{stage}_code_sha256"
        selection = selections.get(stage, {})
        if not isinstance(selection, Mapping):
            observed[stage] = {"binding_issues": ["后端选择必须为映射"]}
            issues.append(f"{stage}: 后端选择必须为映射")
            continue
        registered = bool(entry.get(field) or entry.get(hash_field)
                          or selection.get("bundle_sha256") or selection.get("validated_bundle_sha256")
                          or entry.get(f"{stage}_execution_status") in {
                              "code_delivered", "awaiting_user_execution", "workbook_received", "accepted",
                          })
        if current_state and not registered:
            directory = root / f"{STAGE_CODE.question_name(question)}求解"
            names = (STAGE_CODE._names(STAGE_CODE.question_name(question), stage).values()
                     if STAGE_CODE.question_number(question) is not None else ())
            historical = [path.relative_to(root).as_posix() for name in names
                          if (path := directory / name).is_file()]
            if historical:
                observed[stage] = {"historical_entrypoints": historical}
            continue
        if current_state and (project_backend is None or not all((
            entry.get(field), entry.get(hash_field), selection.get("bundle_sha256"),
        ))):
            issue = f"{stage}当前交付需要项目后端及完整登记的入口、SHA-256和bundle"
            observed[stage] = {"binding_issues": [issue]}
            issues.append(issue)
            continue
        try:
            code = STAGE_CODE.resolve_stage_code(
                root, question, stage, entry=entry, project_backend=project_backend,
            )
            if code is None:
                continue
            paths[stage] = code.path
            record = {"backend": code.backend, "entrypoint": code.path.relative_to(root).as_posix()}
            bound_entry = {**entry, field: record["entrypoint"]}
            if STAGE_CODE.requires_bundle_binding(root, bound_entry, stage, project_backend=project_backend):
                _, config = STAGE_CODE.parse_stage_config(code.path, code.backend)
                record.update(STAGE_CODE.stage_code_fingerprint(
                    root, code.path, config.get("code_dependencies", []), check_declared_hashes=False,
                ))
                if registered:
                    binding_issues = STAGE_CODE.validate_stage_binding(
                        root, entry, stage,
                        require_validated=entry.get(f"{stage}_execution_status") == "accepted",
                        project_backend=project_backend,
                    )
                    record["binding_issues"] = binding_issues
                    issues.extend(f"{stage}: {issue}" for issue in binding_issues)
            observed[stage] = record
        except STAGE_CODE.StageCodeMissingError as exc:
            if registered:
                observed[stage] = {"binding_issues": [str(exc)]}
                issues.append(f"{stage}: {exc}")
        except (ValueError, OSError, TypeError) as exc:
            observed[stage] = {"binding_issues": [str(exc)]}
            issues.append(f"{stage}: {exc}")
    return observed, paths, issues

def _analysis_path(result_dir: Path, chinese_name: str) -> tuple[Path, bool]:
    current = result_dir / f"{chinese_name}结果深化分析.xlsx"
    if current.is_file():
        return current, False
    legacy = result_dir / f"{chinese_name}敏感性与鲁棒性结果.xlsx"
    return (legacy, True) if legacy.is_file() else (current, False)

def _figure_files(result_dir: Path) -> list[Path]:
    directories = [result_dir, result_dir / "图表"]
    return sorted(
        {path for directory in directories if directory.is_dir() for path in directory.iterdir()
         if path.is_file() and path.suffix.lower() in FIGURE_SUFFIXES},
        key=lambda item: item.as_posix(),
    )


def _figure_table_rows(text: str) -> list[dict[str, str]]:
    """Read explicit Markdown table cells, excluding fenced examples."""
    rows: list[dict[str, str]] = []
    headers: list[str] = []
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
            headers = []
        if fenced:
            continue
        if not line.strip().startswith("|"):
            headers = []
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            continue
        if not headers:
            headers = cells
        elif len(cells) == len(headers):
            rows.append(dict(zip(headers, cells)))
    return rows


def _declared_paths(cell: str) -> list[str]:
    paths: list[str] = []
    for item in re.split(r"<br\s*/?>|[;；]", cell, flags=re.IGNORECASE):
        item = item.strip().strip("`")
        link = re.fullmatch(r"\[[^\]]*\]\((.*?)\)", item)
        if link:
            item = link.group(1).strip().strip("<>")
        if item and item not in {"-", "—"}:
            paths.append(item)
    return paths


def scoped_figure_files(
    root: Path, script: Path, entry: Mapping[str, Any] | None = None,
) -> tuple[list[Path], list[str]]:
    """Combine legacy local figures with exact current framework/export bindings.

    Framework paths are project-relative; literal MATLAB exports are script-relative.
    Figure IDs in the question's existing map can bind non-MATLAB/shared figures too.
    This discovers evidence; it does not grant approval or update validated hashes.
    """
    root, script = root.resolve(), script.resolve()
    issues: list[str] = []
    figures: set[Path] = set()

    def inside(raw: str, base: Path) -> Path:
        path = (base / raw).resolve()
        if not path.is_relative_to(root):
            raise ValueError(f"图表映射路径越出项目根目录: {raw}")
        return path

    def add(raw: str, base: Path) -> None:
        try:
            path = inside(raw, base)
            if path.suffix.lower() not in FIGURE_SUFFIXES:
                issues.append(f"图表映射不是受支持的图片载体: {raw}")
            elif not path.is_file():
                issues.append(f"图表映射声明的文件不存在: {raw}")
            else:
                figures.add(path)
        except ValueError as exc:
            issues.append(str(exc))

    if not script.is_relative_to(root):
        return [], ["图表映射脚本越出项目根目录"]
    for path in _figure_files(script.parent):
        add(str(path), root)
    for raw in _parse_matlab(script)[2]:
        add(raw, script.parent)
    framework = root / "模型论文框架.md"
    text = ARTIFACT_FINGERPRINT.framework_section_text(framework, "## 图表证据链") or ""
    question_text = ARTIFACT_FINGERPRINT.framework_section_text(
        framework, str((entry or {}).get("framework_section", ""))
    ) or ""
    identifiers = {row["Figure ID"] for row in _figure_table_rows(question_text) if row.get("Figure ID")}
    for row in _figure_table_rows(text):
        outputs = _declared_paths(row.get("导出文件", ""))
        if not outputs:
            continue
        programs = {(root / raw).resolve() for raw in _declared_paths(row.get("绘图程序", ""))}
        identifier = row.get("图号") or row.get("Figure ID")
        if script not in programs and identifier not in identifiers:
            continue
        if any(not program.is_relative_to(root) for program in programs):
            issues.append(f"图表映射脚本越出项目根目录: {row.get('绘图程序')}")
            continue
        for raw in outputs:
            add(raw, root)
    return sorted(figures, key=lambda path: path.as_posix()), sorted(set(issues))


def _validate_workbook(path: Path, kind: str, schema: Mapping[str, Any], entry: Mapping[str, Any]) -> list[str]:
    objective, structures, problem_types, capabilities = _classification(entry)
    try:
        WORKBOOK_VALIDATION.validate_workbook_file(
            path, kind, schema=schema, problem_types=problem_types,
            capabilities=capabilities, objective=objective, structures=structures,
            require_quality_passed=True,
        )
    except Exception as exc:  # noqa: BLE001
        return [f"{path.name}: {exc}"]
    return []

def _has_sheets(path: Path, names: set[str]) -> bool:
    if not path.is_file():
        return False
    try:
        return names.issubset(WORKBOOK_VALIDATION.read_workbook_tables(path))
    except Exception:  # noqa: BLE001
        return False

def _matlab_executable_text(text: str) -> str:
    """Remove MATLAB comments while preserving percent signs inside quoted strings."""
    cleaned: list[str] = []
    for source in text.splitlines():
        line = source
        in_single = False
        in_double = False
        index = 0
        while index < len(line):
            char = line[index]
            if char == '"' and not in_single:
                if in_double and index + 1 < len(line) and line[index + 1] == '"':
                    index += 2
                    continue
                in_double = not in_double
            elif char == "'" and not in_double:
                if in_single:
                    if index + 1 < len(line) and line[index + 1] == "'":
                        index += 2
                        continue
                    in_single = False
                else:
                    previous = line[index - 1] if index else ""
                    if not previous or not (previous.isalnum() or previous in "_)]}."):
                        in_single = True
            elif char == "%" and not in_single and not in_double:
                line = line[:index]
                break
            index += 1
        cleaned.append(line)
    return "\n".join(cleaned)

def _parse_matlab(script: Path) -> tuple[bool, list[str], list[str]]:
    if not script.is_file():
        return False, [], []
    text = script.read_text(encoding="utf-8", errors="ignore")
    code_text = _matlab_executable_text(text)
    return (
        bool(MATLAB_TITLE_RE.search(code_text)),
        WORKBOOK_REF_RE.findall(code_text),
        EXPORT_RE.findall(code_text),
    )

def _snapshot_question(
    root: Path,
    chinese_name: str,
    entry: Mapping[str, Any],
    schema: Mapping[str, Any],
    data_hash: str | None,
    delivery_scope: str | None,
    *,
    state: Mapping[str, Any] | None = None,
    project_backend: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    key = question_key(chinese_name)
    result_dir = _question_dir(root, chinese_name)
    expected_solution = result_dir / f"{chinese_name}求解结果.xlsx"
    expected_analysis = result_dir / f"{chinese_name}结果深化分析.xlsx"
    current_state = state is not None
    workbook_issues: list[str] = []
    if current_state:
        def registered_workbook(field: str, expected: Path) -> Path | None:
            relative = entry.get(field)
            if not relative:
                return None
            try:
                path = STAGE_CODE._relative_path(root, relative)
            except STAGE_CODE.StageCodeError as exc:
                workbook_issues.append(f"{field}: {exc}")
                return None
            if path != expected:
                workbook_issues.append(f"{field}不是当前阶段标准工作簿: {relative}")
                return None
            return path

        solution = registered_workbook("solution_workbook", expected_solution)
        analysis_workbook = registered_workbook("result_analysis_workbook", expected_analysis)
        legacy_analysis_workbook = False
    else:
        solution = expected_solution
        analysis_workbook, legacy_analysis_workbook = _analysis_path(result_dir, chinese_name)
    implementations, code_paths, code_issues = _solver_observations(
        root, chinese_name, entry, project_backend=project_backend, current_state=current_state,
    )
    primary_code, analysis_code = code_paths["primary"], code_paths["analysis"]
    legacy_single_code = bool(primary_code and primary_code.suffix == ".py" and not analysis_code)
    number = question_number(chinese_name)
    matlab = result_dir / f"q{number}_plot.m" if number else result_dir / "q_plot.m"
    figures, figure_issues = scoped_figure_files(root, matlab, entry)
    status = str(entry.get("status", "pending"))
    analysis_not_required = (
        entry.get("result_analysis_status") == "not_required"
        and bool(str(entry.get("result_analysis_requirement_reason") or "").strip())
    )
    selections = entry.get("solver_execution")
    if current_state and analysis_not_required and (
        entry.get("result_analysis_code") or entry.get("analysis_code_sha256")
        or entry.get("result_analysis_workbook")
        or (isinstance(selections, Mapping) and selections.get("analysis"))
    ):
        workbook_issues.append("not_required阶段仍登记当前analysis数值身份")
    input_issues: list[str] = []
    for stage, code in code_paths.items():
        if code is None or (stage == "analysis" and analysis_not_required):
            continue
        if not STAGE_CODE.requires_bundle_binding(root, entry, stage, project_backend=project_backend):
            continue  # Historical 1.0 observations retain the global data policy.
        if stage == "primary":
            data_hash = None  # Invalid modern inputs must not fall back to raw scans.
        try:
            _, config = STAGE_CODE.parse_stage_config(code)
            observation = observe_inputs(root, config, state or {})
            implementations.setdefault(stage, {})["inputs"] = observation
            input_issues.extend(f"{stage}: {issue}" for issue in observation["issues"])
            if stage == "primary":
                data_hash = observation["data_sha256"]
            elif str(config.get("data_sha256", "")).lower() != str(entry.get("data_hash", "")).lower():
                input_issues.append("analysis data_sha256必须继承主结果data_hash，不得覆盖主数据身份")
        except (ValueError, OSError, TypeError) as exc:
            input_issues.append(f"{stage}输入身份: {exc}")
    require_solution = status in SOLVED_STATUSES
    require_analysis = status in ANALYZED_STATUSES and not analysis_not_required
    require_analysis_code = (
        status in ANALYZED_STATUSES
        and not analysis_not_required
        and bool(entry.get("analysis_code_sha256"))
    )
    if delivery_scope in {"results", "figures", "docx"}:
        require_solution = True
        require_analysis = not analysis_not_required
        require_analysis_code = not analysis_not_required

    formal_figures = delivery_scope in {"figures", "docx", "latex", "submission"}
    issues: list[str] = [*workbook_issues, *code_issues, *input_issues, *(figure_issues if formal_figures else [])]
    warnings: list[str] = [] if formal_figures else list(figure_issues)
    if entry.get("result_analysis_status") == "not_required" and not analysis_not_required:
        issues.append("result_analysis_status=not_required必须提供非空result_analysis_requirement_reason")
    if delivery_scope == "code" and primary_code is None:
        issues.append("代码交付缺少标准主求解脚本")
    if require_solution and not (solution and solution.is_file()):
        issues.append("缺少标准求解结果工作簿")
    if require_analysis and not (analysis_workbook and analysis_workbook.is_file()):
        issues.append("缺少标准结果深化分析工作簿")
    if require_analysis_code and analysis_code is None:
        if delivery_scope is None and legacy_single_code and not entry.get("analysis_code_sha256"):
            warnings.append("检测到v6.6.x单脚本项目；只读兼容，重新深化分析时应迁移为独立结果深化分析脚本")
        else:
            issues.append("缺少标准结果深化分析脚本")
    if solution and solution.is_file():
        issues.extend(_validate_workbook(solution, "solution", schema, entry))
    if analysis_workbook and analysis_workbook.is_file():
        issues.extend(_validate_workbook(analysis_workbook, "result_analysis", schema, entry))
        if legacy_analysis_workbook:
            warnings.append("使用旧敏感性与鲁棒性工作簿名；新交付应迁移为结果深化分析工作簿")

    quality_exists = bool(solution and _has_sheets(solution, {"主结果质量门"}))
    analysis_report_exists = analysis_not_required or bool(analysis_workbook and _has_sheets(
        analysis_workbook, {"分析设计", "结论稳定性汇总"}
    ))
    if require_solution and not quality_exists:
        issues.append("主求解工作簿缺少主结果质量门报告")
    if require_analysis and not analysis_report_exists:
        issues.append("结果深化分析工作簿缺少分析设计或结论稳定性汇总")

    matlab_has_title, workbook_refs, exports = _parse_matlab(matlab)
    if delivery_scope == "figures":
        if not matlab.is_file():
            issues.append("图表交付缺少MATLAB脚本")
        else:
            if matlab_has_title:
                issues.append("MATLAB正式论文图不得设置整体title或sgtitle；正式图名由LaTeX/DOCX caption承担")
            standard = {
                f"{chinese_name}求解结果.xlsx",
                f"{chinese_name}结果深化分析.xlsx",
                f"{chinese_name}敏感性与鲁棒性结果.xlsx",
            }
            if not {Path(item).name for item in workbook_refs}.intersection(standard):
                issues.append("MATLAB脚本未发现标准工作簿引用")
            for item in exports:
                export_path = (matlab.parent / item).resolve()
                if not export_path.is_file():
                    shown = export_path.relative_to(root).as_posix() if export_path.is_relative_to(root) else export_path.as_posix()
                    issues.append(f"MATLAB声明导出的图不存在: {shown}")

    framework = root / "模型论文框架.md"
    hashes = {
        "data": data_hash,
        "primary_code": sha256_file(primary_code) if primary_code else None,
        "analysis_code": sha256_file(analysis_code) if analysis_code else None,
        "solution_workbook": sha256_file(solution) if solution and solution.is_file() else None,
        "result_analysis_workbook": sha256_file(analysis_workbook) if analysis_workbook and analysis_workbook.is_file() else None,
        "matlab_script": sha256_file(matlab) if matlab.is_file() else None,
        "figure_bundle": combined_hash(figures, root),
        "framework": framework_section_hash(framework, str(entry.get("framework_section", ""))),
    }
    hashes = {name: value for name, value in hashes.items() if value}
    return {
        "key": key,
        "chinese_name": chinese_name,
        "status": status,
        "primary_code": primary_code.relative_to(root).as_posix() if primary_code else None,
        "result_analysis_code": analysis_code.relative_to(root).as_posix() if analysis_code else None,
        "primary_code_sha256": sha256_file(primary_code) if primary_code else None,
        "analysis_code_sha256": sha256_file(analysis_code) if analysis_code else None,
        "solver_execution_observed": implementations,
        "project_backend": project_backend,
        "historical_workbooks": [path.relative_to(root).as_posix() for path in (
            expected_solution, expected_analysis, result_dir / f"{chinese_name}敏感性与鲁棒性结果.xlsx"
        ) if path.is_file() and path not in (solution, analysis_workbook)],
        "legacy_single_code": legacy_single_code,
        "solution_workbook": solution.relative_to(root).as_posix() if solution and solution.is_file() else None,
        "result_analysis_workbook": analysis_workbook.relative_to(root).as_posix() if analysis_workbook and analysis_workbook.is_file() else None,
        "legacy_analysis_workbook": legacy_analysis_workbook,
        "result_quality_report": quality_exists,
        "result_analysis_report": analysis_report_exists,
        "matlab_script": matlab.relative_to(root).as_posix() if matlab.is_file() else None,
        "matlab_has_title": matlab_has_title,
        "workbook_references": workbook_refs,
        "declared_exports": exports,
        "figures": [path.relative_to(root).as_posix() for path in figures],
        "individual_figure_hashes": {
            path.relative_to(root).as_posix(): sha256_file(path) for path in figures
        },
        "artifact_hashes": hashes,
        "issues": issues,
        "warnings": warnings,
    }
