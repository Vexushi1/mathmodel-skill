#!/usr/bin/env python3
"""Synchronize project artifacts without promoting solve or analysis decisions."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCHEMA_PATH = SKILL_ROOT / "core" / "workbook_schema.yaml"
DEFAULT_OUTPUT_CONTRACT_PATH = SKILL_ROOT / "core" / "output_contract.yaml"
QUESTION_RE = re.compile(r"问题([一二三四五六七八九十百]+)")
MATLAB_TITLE_RE = re.compile(r"\b(?:title|sgtitle)\s*\(", re.IGNORECASE)
EXPORT_RE = re.compile(
    r"(?:exportgraphics|print)\s*\([^\n]*?[\"']([^\"']+\.(?:png|pdf|svg|tif|tiff|jpg|jpeg))[\"']",
    re.IGNORECASE,
)
WORKBOOK_REF_RE = re.compile(r"[\"']([^\"']+\.xlsx)[\"']", re.IGNORECASE)
FIGURE_SUFFIXES = {".png", ".pdf", ".svg", ".tif", ".tiff", ".jpg", ".jpeg"}
DATA_SUFFIXES = {".csv", ".xlsx", ".xls", ".json", ".yaml", ".yml", ".txt"}
PHASE_SCOPE = {
    "problem_audit": "design", "model_design": "design",
    "solve_validate": "code", "result_analysis": "code",
    "figure_evidence": "figures", "writing_docx": "docx",
    "writing_latex": "latex", "ai_cleanup": "latex",
    "latex_compile_quality": "latex", "review_delivery": "submission",
    "completed": "submission",
}
HASH_KEYS = (
    "data", "model", "solution_workbook", "result_analysis_workbook",
    "matlab_script", "figure_bundle", "framework",
)
SOLVED_STATUSES = {"solved", "analyzed", "validated", "written", "completed"}
ANALYZED_STATUSES = {"analyzed", "validated", "written", "completed"}
PRIMARY_STALE_LAYERS = {
    "model", "solution_workbook", "result_analysis_workbook",
    "matlab_script", "figure_bundle", "framework",
}
ANALYSIS_STALE_LAYERS = {
    "result_analysis_workbook", "matlab_script", "figure_bundle", "framework",
}


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


WORKBOOK_VALIDATION = _load_module(
    "hsk_workbook_validation",
    SKILL_ROOT / "templates/code" / "hsk_pipeline" / "workbook_validation.py",
)
STATE_VALIDATION = _load_module(
    "hsk_project_state_validation", SKILL_ROOT / "scripts" / "validate_project_state.py"
)
FRAMEWORK_VALIDATION = _load_module(
    "hsk_framework_validation", SKILL_ROOT / "scripts" / "validate_model_paper_framework.py"
)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_json_or_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        if path.suffix.lower() == ".json":
            return json.loads(path.read_text(encoding="utf-8")) or {}
        return load_yaml(path)
    except Exception:  # noqa: BLE001
        return {}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def combined_hash(paths: Iterable[Path], root: Path) -> str | None:
    files = sorted(
        {Path(path).resolve() for path in paths if Path(path).is_file()},
        key=lambda item: item.as_posix(),
    )
    if not files:
        return None
    digest = hashlib.sha256()
    for path in files:
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            relative = path.as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()


def question_key(chinese_name: str) -> str:
    order = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    suffix = chinese_name.removeprefix("问题")
    return f"Q{order.index(suffix) + 1}" if suffix in order else chinese_name


def chinese_question_name(key: str) -> str:
    order = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    match = re.fullmatch(r"Q(\d+)", key)
    if match and 1 <= int(match.group(1)) <= len(order):
        return f"问题{order[int(match.group(1)) - 1]}"
    return key


def question_number(chinese_name: str) -> int | None:
    match = re.fullmatch(r"Q(\d+)", question_key(chinese_name))
    return int(match.group(1)) if match else None


def data_source_files(
    root: Path, state: Mapping[str, Any]
) -> tuple[list[Path], str, list[str], list[str]]:
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


def framework_section_text(path: Path, anchor: str) -> str | None:
    if not path.is_file() or not anchor.strip():
        return None
    lines = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n").splitlines()
    target = anchor.strip()
    start = next((index for index, line in enumerate(lines) if line.strip() == target), None)
    if start is None:
        start = next(
            (index for index, line in enumerate(lines) if line.lstrip().startswith("#") and target in line.strip()),
            None,
        )
    if start is None:
        return None
    heading = lines[start].lstrip()
    level = len(heading) - len(heading.lstrip("#"))
    end = len(lines)
    for index in range(start + 1, len(lines)):
        stripped = lines[index].lstrip()
        if stripped.startswith("#"):
            next_level = len(stripped) - len(stripped.lstrip("#"))
            if next_level <= level:
                end = index
                break
    return "\n".join(lines[start:end]).strip() + "\n"


def framework_section_hash(path: Path, anchor: str) -> str | None:
    text = framework_section_text(path, anchor)
    return sha256_text(text) if text else None


def stage_requirements(scope: str, output_contract: Mapping[str, Any]) -> list[str]:
    return list(
        ((output_contract.get("project_sync") or {}).get("stage_requirements") or {}).get(scope, [])
    )


def contract_preflight_issues(
    root: Path,
    scope: str,
    state_path: Path,
    framework_path: Path,
    output_contract: Mapping[str, Any],
) -> list[str]:
    issues: list[str] = []
    required = set(stage_requirements(scope, output_contract))
    if "project_state" in required and not state_path.is_file():
        issues.append("项目状态校验: 缺少 state/project_state.yaml")
    elif state_path.is_file():
        issues.extend(
            f"项目状态校验: {item}"
            for item in STATE_VALIDATION.validate_state_file(state_path, project_root=root)
        )
    if "model_paper_framework" in required and not framework_path.is_file():
        issues.append("模型论文框架校验: 缺少 模型论文框架.md")
    elif framework_path.is_file():
        issues.extend(
            f"模型论文框架校验: {item}"
            for item in FRAMEWORK_VALIDATION.validate_framework_file(
                framework_path,
                state_path=state_path if state_path.is_file() else None,
            )
        )
    return issues


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


def _parse_matlab(script: Path) -> tuple[bool, list[str], list[str]]:
    if not script.is_file():
        return False, [], []
    text = script.read_text(encoding="utf-8", errors="ignore")
    return bool(MATLAB_TITLE_RE.search(text)), WORKBOOK_REF_RE.findall(text), EXPORT_RE.findall(text)


def _snapshot_question(
    root: Path,
    chinese_name: str,
    entry: Mapping[str, Any],
    schema: Mapping[str, Any],
    data_hash: str | None,
    delivery_scope: str | None,
) -> dict[str, Any]:
    key = question_key(chinese_name)
    result_dir = _question_dir(root, chinese_name)
    solution = result_dir / f"{chinese_name}求解结果.xlsx"
    analysis_workbook, legacy_analysis_workbook = _analysis_path(result_dir, chinese_name)
    primary_code, analysis_code, legacy_single_code = _stage_code_paths(root, chinese_name)
    number = question_number(chinese_name)
    matlab = result_dir / f"q{number}_plot.m" if number else result_dir / "q_plot.m"
    figures = _figure_files(result_dir)
    status = str(entry.get("status", "pending"))
    require_solution = status in SOLVED_STATUSES
    require_analysis = status in ANALYZED_STATUSES
    require_analysis_code = status in ANALYZED_STATUSES and bool(entry.get("analysis_code_sha256"))
    if delivery_scope in {"results", "figures", "docx"}:
        require_solution = True
        require_analysis = True
        require_analysis_code = True

    issues: list[str] = []
    warnings: list[str] = []
    if delivery_scope == "code" and primary_code is None:
        issues.append("代码交付缺少标准主求解Python脚本")
    if require_solution and not solution.is_file():
        issues.append("缺少标准求解结果工作簿")
    if require_analysis and not analysis_workbook.is_file():
        issues.append("缺少标准结果深化分析工作簿")
    if require_analysis_code and analysis_code is None:
        if legacy_single_code and not entry.get("analysis_code_sha256"):
            warnings.append("检测到v6.6.x单脚本项目；只读兼容，重新深化分析时应迁移为独立结果深化分析脚本")
        else:
            issues.append("缺少标准结果深化分析Python脚本")
    if solution.is_file():
        issues.extend(_validate_workbook(solution, "solution", schema, entry))
    if analysis_workbook.is_file():
        issues.extend(_validate_workbook(analysis_workbook, "result_analysis", schema, entry))
        if legacy_analysis_workbook:
            warnings.append("使用旧敏感性与鲁棒性工作簿名；新交付应迁移为结果深化分析工作簿")

    quality_exists = _has_sheets(solution, {"主结果质量门"})
    analysis_report_exists = _has_sheets(analysis_workbook, {"分析设计", "结论稳定性汇总"})
    if require_solution and not quality_exists:
        issues.append("主求解工作簿缺少主结果质量门报告")
    if require_analysis and not analysis_report_exists:
        issues.append("结果深化分析工作簿缺少分析设计或结论稳定性汇总")

    matlab_has_title, workbook_refs, exports = _parse_matlab(matlab)
    if delivery_scope == "figures":
        if not matlab.is_file():
            issues.append("图表交付缺少MATLAB脚本")
        else:
            if not matlab_has_title:
                issues.append("MATLAB正式图缺少title或sgtitle")
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
        "model": sha256_file(primary_code) if primary_code else None,
        "solution_workbook": sha256_file(solution) if solution.is_file() else None,
        "result_analysis_workbook": sha256_file(analysis_workbook) if analysis_workbook.is_file() else None,
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
        "legacy_single_code": legacy_single_code,
        "solution_workbook": solution.relative_to(root).as_posix() if solution.is_file() else None,
        "result_analysis_workbook": analysis_workbook.relative_to(root).as_posix() if analysis_workbook.is_file() else None,
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


def _normalized_validated_hashes(entry: Mapping[str, Any]) -> dict[str, str]:
    validated = dict(entry.get("validated_artifact_hashes", {}) or {})
    if "result_analysis_workbook" not in validated and "robustness_workbook" in validated:
        validated["result_analysis_workbook"] = validated["robustness_workbook"]
    return {key: value for key, value in validated.items() if key in HASH_KEYS}


def _mismatched_layers(entry: Mapping[str, Any], current: Mapping[str, str]) -> set[str]:
    return {
        key for key, value in _normalized_validated_hashes(entry).items()
        if current.get(key) != value
    }


def _code_hash_mismatches(entry: Mapping[str, Any], snapshot: Mapping[str, Any]) -> tuple[bool, bool]:
    expected_primary = entry.get("primary_code_sha256")
    expected_analysis = entry.get("analysis_code_sha256")
    current_primary = snapshot.get("primary_code_sha256")
    current_analysis = snapshot.get("analysis_code_sha256")
    primary_changed = bool(expected_primary and current_primary != expected_primary)
    analysis_changed = bool(expected_analysis and current_analysis != expected_analysis)
    return primary_changed, analysis_changed


def _apply_snapshot_to_state(root: Path, state: dict[str, Any], snapshot: Mapping[str, Any]) -> set[str]:
    entry = state.setdefault("subproblems", {}).setdefault(str(snapshot["key"]), {})
    current = dict(snapshot.get("artifact_hashes", {}))
    mismatched = _mismatched_layers(entry, current)
    primary_changed, analysis_changed = _code_hash_mismatches(entry, snapshot)
    stale_layers = set(entry.get("stale_layers", []) or []) | mismatched

    if primary_changed:
        stale_layers |= PRIMARY_STALE_LAYERS
        entry["result_quality_status"] = "pending"
        entry["result_analysis_status"] = "pending"
        entry["analysis_execution_status"] = "pending"
        entry["result_summary_status"] = "stale"
    elif analysis_changed:
        stale_layers |= ANALYSIS_STALE_LAYERS
        entry["result_analysis_status"] = "pending"
        entry["analysis_execution_status"] = "pending"
        entry["result_summary_status"] = "stale"

    if mismatched.intersection({"data", "model", "solution_workbook"}):
        entry["result_quality_status"] = "pending"
        entry["result_analysis_status"] = "pending"
    elif "result_analysis_workbook" in mismatched:
        entry["result_analysis_status"] = "pending"

    entry["artifact_hashes"] = current
    if snapshot.get("primary_code"):
        entry["code"] = snapshot["primary_code"]
    if snapshot.get("result_analysis_code"):
        entry["result_analysis_code"] = snapshot["result_analysis_code"]
    for field in ("solution_workbook", "result_analysis_workbook", "matlab_script"):
        if snapshot.get(field):
            entry[field] = snapshot[field]

    if stale_layers:
        entry["artifacts_stale"] = True
        entry["stale_layers"] = sorted(stale_layers)
        entry["result_summary_status"] = "stale"
        entry["validation_status"] = "pending"
    evidence = _question_dir(root, str(snapshot["chinese_name"])) / "figure_evidence.yaml"
    if evidence.is_file():
        relative = evidence.relative_to(root).as_posix()
        values = list(entry.get("evidence", []) or [])
        if relative not in values:
            values.append(relative)
        entry["evidence"] = values
    return stale_layers


def _replace_or_prepend(lines: list[str], prefix: str, replacement: str) -> list[str]:
    for index, line in enumerate(lines):
        if line.startswith(prefix):
            lines[index] = replacement
            return lines
    return [replacement, *lines]


def _update_framework_header(path: Path, scope: str, stale: bool) -> None:
    if not path.is_file():
        return
    lines = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n").splitlines()
    timestamp = datetime.now(timezone.utc).isoformat()
    lines = _replace_or_prepend(lines, "- 最近同步：", f"- 最近同步：`{scope}`")
    lines = _replace_or_prepend(lines, "- 最近同步时间：", f"- 最近同步时间：`{timestamp}`")
    lines = _replace_or_prepend(lines, "- 当前状态：", f"- 当前状态：`{'stale' if stale else 'current'}`")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _approved_figure_issues(root: Path, state: Mapping[str, Any]) -> list[str]:
    approved = ((state.get("artifacts") or {}).get("approved_figures") or [])
    if not approved:
        return ["缺少已批准图表"]
    return [f"已批准图表不存在: {item}" for item in approved if not (root / str(item)).is_file()]


def _compile_artifact_issues(root: Path, state: Mapping[str, Any]) -> list[str]:
    artifacts = state.get("artifacts") or {}
    source = root / str(artifacts.get("latex_source") or "final_latex/main.tex")
    pdf = root / str(artifacts.get("compiled_pdf") or "final_latex/main.pdf")
    report_path = root / str(artifacts.get("compile_report") or "final_latex/compile_report.yaml")
    issues: list[str] = []
    if not source.is_file():
        issues.append("LaTeX交付缺少 final_latex/main.tex")
    if not pdf.is_file():
        issues.append("LaTeX交付缺少 final_latex/main.pdf")
    if not report_path.is_file():
        issues.append("LaTeX交付缺少 compile_report")
    else:
        report = load_json_or_yaml(report_path)
        if str(report.get("status", "")).lower() != "passed":
            issues.append("compile_report 未通过")
        if int(report.get("unresolved_references", 0) or 0) != 0:
            issues.append("compile_report 存在未解析引用")
    return issues


def _docx_issues(root: Path, state: Mapping[str, Any]) -> list[str]:
    declared = ((state.get("artifacts") or {}).get("docx") or [])
    files = [root / str(item) for item in declared] if declared else list((root / "draft_docx").glob("*.docx"))
    return [] if any(path.is_file() for path in files) else ["DOCX交付缺少真实.docx文件"]


def _submission_zip_issues(path: Path, require_matlab: bool = True) -> list[str]:
    if not path.is_file():
        return ["缺少提交ZIP"]
    try:
        with zipfile.ZipFile(path) as archive:
            names = [name.lower() for name in archive.namelist() if not name.endswith("/")]
    except Exception as exc:  # noqa: BLE001
        return [f"无法读取提交ZIP: {exc}"]
    issues: list[str] = []
    if not any(name.endswith(".pdf") for name in names):
        issues.append("提交ZIP缺少PDF")
    if not any(name.endswith(".py") for name in names):
        issues.append("提交ZIP缺少Python代码")
    if not any(name.endswith(".xlsx") for name in names):
        issues.append("提交ZIP缺少结果工作簿")
    if require_matlab and not any(name.endswith(".m") for name in names):
        issues.append("提交ZIP缺少MATLAB脚本")
    return issues


def _formal_state_issues(required: set[str], state: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    for name, entry in (state.get("subproblems") or {}).items():
        if not isinstance(entry, Mapping):
            continue
        if "result_quality_report" in required and entry.get("result_quality_status") != "passed":
            issues.append(f"{name}: 正式交付要求 result_quality_status=passed")
        if "result_analysis_report" in required and entry.get("result_analysis_status") != "passed":
            issues.append(f"{name}: 正式交付要求 result_analysis_status=passed")
        if required.intersection({"approved_figures", "docx_draft", "latex_source", "compiled_pdf", "validated_submission_package"}):
            if entry.get("artifacts_stale") is True:
                issues.append(f"{name}: 下游正式交付禁止使用 stale 结果")
    return issues


def _scope_artifact_issues(
    root: Path,
    scope: str,
    state: Mapping[str, Any],
    snapshots: Mapping[str, Mapping[str, Any]],
    output_contract: Mapping[str, Any],
) -> list[str]:
    required = set(stage_requirements(scope, output_contract))
    issues = _formal_state_issues(required, state)
    if "python_code" in required and not all(snapshot.get("primary_code") for snapshot in snapshots.values()):
        issues.append("正式交付缺少标准主求解Python脚本")
    if "result_analysis_code" in required:
        for key, snapshot in snapshots.items():
            if snapshot.get("result_analysis_code"):
                continue
            entry = (state.get("subproblems") or {}).get(key, {}) or {}
            if snapshot.get("legacy_single_code") and not entry.get("analysis_code_sha256"):
                continue
            issues.append(f"{key}: 正式结果交付缺少独立结果深化分析Python脚本")
    if "solution_workbook" in required and not all(snapshot.get("solution_workbook") for snapshot in snapshots.values()):
        issues.append("结果交付缺少标准求解结果工作簿")
    if "result_quality_report" in required and not all(snapshot.get("result_quality_report") for snapshot in snapshots.values()):
        issues.append("结果交付缺少主结果质量报告")
    if "result_analysis_workbook" in required and not all(snapshot.get("result_analysis_workbook") for snapshot in snapshots.values()):
        issues.append("结果交付缺少标准结果深化分析工作簿")
    if "result_analysis_report" in required and not all(snapshot.get("result_analysis_report") for snapshot in snapshots.values()):
        issues.append("结果交付缺少结果深化分析报告")
    if "approved_figures" in required:
        issues.extend(_approved_figure_issues(root, state))
    if "docx_draft" in required:
        issues.extend(_docx_issues(root, state))
    if required.intersection({"latex_source", "compiled_pdf", "compile_report"}):
        issues.extend(_compile_artifact_issues(root, state))
    if "validated_submission_package" in required:
        artifacts = state.get("artifacts") or {}
        package = root / str(artifacts.get("submission_package") or "submission/submission.zip")
        issues.extend(_submission_zip_issues(package, require_matlab=True))
    return issues


def synchronize(
    project_root: Path,
    *,
    write: bool = False,
    strict: bool = False,
    delivery_scope: str | None = None,
    schema_path: Path = DEFAULT_SCHEMA_PATH,
    output_contract_path: Path = DEFAULT_OUTPUT_CONTRACT_PATH,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    state_path = root / "state/project_state.yaml"
    framework_path = root / "模型论文框架.md"
    state = load_yaml(state_path)
    schema = load_yaml(Path(schema_path))
    output_contract = load_yaml(Path(output_contract_path))
    phase = str((state.get("project") or {}).get("current_phase", "model_design"))
    explicit_delivery_scope = delivery_scope is not None
    scope = delivery_scope or PHASE_SCOPE.get(phase, "design")
    if scope not in {"design", "code", "results", "figures", "docx", "latex", "submission"}:
        raise ValueError(f"未知delivery scope: {scope}")

    issues = contract_preflight_issues(root, scope, state_path, framework_path, output_contract)
    warnings: list[str] = []
    data_files, data_mode, data_issues, data_warnings = data_source_files(root, state)
    issues.extend(data_issues)
    warnings.extend(data_warnings)
    data_hash = combined_hash(data_files, root)
    snapshots: dict[str, dict[str, Any]] = {}
    subproblems = state.get("subproblems") or {}
    for chinese_name in _question_names(root, state):
        key = question_key(chinese_name)
        entry = subproblems.get(key) or subproblems.get(chinese_name) or {}
        snapshot = _snapshot_question(
            root, chinese_name, entry, schema, data_hash,
            scope if explicit_delivery_scope else None,
        )
        snapshots[key] = snapshot
        issues.extend(f"{key}: {item}" for item in snapshot["issues"])
        warnings.extend(f"{key}: {item}" for item in snapshot["warnings"])
    if explicit_delivery_scope and scope in {"results", "figures", "docx"} and not snapshots:
        issues.append("未发现任何小问结果目录或项目状态")
    if explicit_delivery_scope:
        issues.extend(_scope_artifact_issues(root, scope, state, snapshots, output_contract))

    stale_questions: list[str] = []
    if write and state_path.is_file():
        for snapshot in snapshots.values():
            stale = _apply_snapshot_to_state(root, state, snapshot)
            if stale:
                stale_questions.append(str(snapshot["key"]))
        any_stale = any(
            bool(entry.get("artifacts_stale"))
            for entry in (state.get("subproblems") or {}).values()
            if isinstance(entry, Mapping)
        )
        framework = state.setdefault("paper_framework", {})
        framework["sync_status"] = "stale" if any_stale else "current"
        framework["last_sync_scope"] = scope
        framework["last_synced_at"] = datetime.now(timezone.utc).isoformat()
        _update_framework_header(framework_path, scope, any_stale)
        if framework_path.is_file():
            framework["sha256"] = sha256_file(framework_path)
        state.setdefault("artifacts", {})["sync_report"] = "sync_report.yaml"
        state.setdefault("execution", {})["last_sync_report"] = "sync_report.yaml"
        state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
    else:
        for key, snapshot in snapshots.items():
            entry = subproblems.get(key) or subproblems.get(snapshot["chinese_name"]) or {}
            primary_changed, analysis_changed = _code_hash_mismatches(entry, snapshot)
            if (
                entry.get("artifacts_stale")
                or _mismatched_layers(entry, snapshot.get("artifact_hashes", {}))
                or primary_changed
                or analysis_changed
            ):
                stale_questions.append(key)

    report = {
        "status": "passed" if not issues else "failed",
        "delivery_scope": scope,
        "formal_delivery_scope": explicit_delivery_scope,
        "write": write,
        "strict": strict,
        "data_hash_mode": data_mode,
        "data_hash": data_hash,
        "framework_hash": sha256_file(framework_path) if framework_path.is_file() else None,
        "questions": snapshots,
        "stale_questions": sorted(set(stale_questions)),
        "issues": sorted(set(issues)),
        "warnings": sorted(set(warnings)),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    if write:
        report_path = root / "sync_report.yaml"
        report_path.write_text(yaml.safe_dump(report, allow_unicode=True, sort_keys=False), encoding="utf-8")
        if state_path.is_file() and framework_path.is_file():
            expected = ((load_yaml(state_path).get("paper_framework") or {}).get("sha256"))
            actual = sha256_file(framework_path)
            if expected != actual:
                report["issues"].append("写后哈希自检失败: paper_framework.sha256不一致")
                report["status"] = "failed"
                report_path.write_text(yaml.safe_dump(report, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", nargs="?", default=".")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument(
        "--delivery-scope",
        choices=["design", "code", "results", "figures", "docx", "latex", "submission"],
    )
    args = parser.parse_args()
    report = synchronize(
        Path(args.project_root), write=args.write, strict=args.strict,
        delivery_scope=args.delivery_scope,
    )
    for item in report["issues"]:
        print("-", item)
    for item in report["warnings"]:
        print("warning:", item)
    print(f"sync status: {report['status']}")
    return 1 if args.strict and report["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
