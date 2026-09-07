#!/usr/bin/env python3
"""Synchronize project artifacts without promoting preprocessing, solve, or analysis decisions."""
from __future__ import annotations

import argparse
from copy import deepcopy
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
SCRIPT_DIR = str(SKILL_ROOT / "scripts")
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
import artifact_identity as ARTIFACT_IDENTITY  # noqa: E402
import project_transaction as PROJECT_TX  # noqa: E402
import artifact_fingerprint as ARTIFACT_FINGERPRINT  # noqa: E402
import project_snapshot as PROJECT_SNAPSHOT  # noqa: E402
DEFAULT_SCHEMA_PATH = SKILL_ROOT / "core" / "workbook_schema.yaml"
DEFAULT_OUTPUT_CONTRACT_PATH = SKILL_ROOT / "core" / "output_contract.yaml"
PHASE_SCOPE = {
    "problem_audit": "design", "model_design": "design",
    "data_preprocessing": "code", "solve_validate": "code", "result_analysis": "code",
    "figure_evidence": "figures", "writing_docx": "docx",
    "writing_latex": "latex", "ai_cleanup": "latex",
    "latex_compile_quality": "latex", "review_delivery": "submission",
    "completed": "submission",
}
HASH_KEYS = (
    "data", "primary_code", "analysis_code", "solution_workbook", "result_analysis_workbook",
    "matlab_script", "figure_bundle", "framework",
)
MATLAB_PREPROCESSING_FORBIDDEN_FUNCTIONS = (
    "interp1", "interp2", "interp3", "interpn", "griddedInterpolant", "scatteredInterpolant",
    "fillmissing", "rmmissing", "standardizeMissing",
    "filloutliers", "rmoutliers", "isoutlier",
    "smooth", "smoothdata", "movmean", "movmedian",
    "resample", "interpft", "decimate", "downsample", "upsample", "retime", "synchronize",
    "detrend", "normalize", "rescale", "zscore",
    "filter", "filtfilt", "designfilt", "lowpass", "highpass", "bandpass", "bandstop",
    "butter", "cheby1", "cheby2", "ellip", "fir1", "fir2",
    "fit", "fitlm", "fitrlinear", "fitrgp", "fitrensemble", "fitrtree",
    "predict", "trainNetwork", "trainnet",
)
MATLAB_PREPROCESSING_FORBIDDEN_RE = re.compile(
    r"(?<![\w])("
    + "|".join(re.escape(name) for name in MATLAB_PREPROCESSING_FORBIDDEN_FUNCTIONS)
    + r")\s*\(",
    re.IGNORECASE,
)
MATLAB_PREPROCESSING_FORBIDDEN_DISPATCH_FUNCTIONS = ("eval", "evalin", "feval", "str2func", "builtin")
MATLAB_PREPROCESSING_FORBIDDEN_DISPATCH_RE = re.compile(
    r"(?<![\w])("
    + "|".join(re.escape(name) for name in MATLAB_PREPROCESSING_FORBIDDEN_DISPATCH_FUNCTIONS)
    + r")\s*\(",
    re.IGNORECASE,
)
MATLAB_PREPROCESSING_FORBIDDEN_HANDLE_RE = re.compile(
    r"@(" + "|".join(re.escape(name) for name in MATLAB_PREPROCESSING_FORBIDDEN_FUNCTIONS) + r")\b",
    re.IGNORECASE,
)


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
LATEX_DELIVERY = _load_module(
    "hsk_latex_delivery", SKILL_ROOT / "scripts" / "latex_delivery.py"
)
STATE_TRANSITIONS = _load_module(
    "hsk_state_transitions", SKILL_ROOT / "scripts" / "state_transitions.py"
)
STATE_TRANSITION_CONTRACT = yaml.safe_load(
    (SKILL_ROOT / "core" / "state_transition_contract.yaml").read_text(encoding="utf-8")
) or {}

# Phase H compatibility aliases: existing callers/tests keep the sync_project surface.
sha256_file = ARTIFACT_FINGERPRINT.sha256_file
sha256_text = ARTIFACT_FINGERPRINT.sha256_text
combined_hash = ARTIFACT_FINGERPRINT.combined_hash
framework_section_text = ARTIFACT_FINGERPRINT.framework_section_text
framework_section_hash = ARTIFACT_FINGERPRINT.framework_section_hash
QUESTION_RE = PROJECT_SNAPSHOT.QUESTION_RE
MATLAB_TITLE_RE = PROJECT_SNAPSHOT.MATLAB_TITLE_RE
EXPORT_RE = PROJECT_SNAPSHOT.EXPORT_RE
WORKBOOK_REF_RE = PROJECT_SNAPSHOT.WORKBOOK_REF_RE
FIGURE_SUFFIXES = PROJECT_SNAPSHOT.FIGURE_SUFFIXES
DATA_SUFFIXES = PROJECT_SNAPSHOT.DATA_SUFFIXES
SOLVED_STATUSES = PROJECT_SNAPSHOT.SOLVED_STATUSES
ANALYZED_STATUSES = PROJECT_SNAPSHOT.ANALYZED_STATUSES
VALID_PREPROCESSING_DECISIONS = PROJECT_SNAPSHOT.VALID_PREPROCESSING_DECISIONS
question_key = PROJECT_SNAPSHOT.question_key
chinese_question_name = PROJECT_SNAPSHOT.chinese_question_name
question_number = PROJECT_SNAPSHOT.question_number
preprocessing_decision = PROJECT_SNAPSHOT.preprocessing_decision
data_source_files = PROJECT_SNAPSHOT.data_source_files
active_data_hash = PROJECT_SNAPSHOT.active_data_hash
_classification = PROJECT_SNAPSHOT._classification
_question_dir = PROJECT_SNAPSHOT._question_dir
_question_names = PROJECT_SNAPSHOT._question_names
_stage_code_paths = PROJECT_SNAPSHOT._stage_code_paths
_python_files = PROJECT_SNAPSHOT._python_files
_analysis_path = PROJECT_SNAPSHOT._analysis_path
_figure_files = PROJECT_SNAPSHOT._figure_files
_validate_workbook = PROJECT_SNAPSHOT._validate_workbook
_has_sheets = PROJECT_SNAPSHOT._has_sheets
_matlab_executable_text = PROJECT_SNAPSHOT._matlab_executable_text
_parse_matlab = PROJECT_SNAPSHOT._parse_matlab
_snapshot_question = PROJECT_SNAPSHOT._snapshot_question


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def unique(items: Iterable[Any]) -> list[str]:
    return list(dict.fromkeys(str(item) for item in items if item and str(item).strip()))


def load_json_or_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        if path.suffix.lower() == ".json":
            return json.loads(path.read_text(encoding="utf-8")) or {}
        return load_yaml(path)
    except Exception:  # noqa: BLE001
        return {}



def _uses_fragment_stale(framework: Mapping[str, Any]) -> bool:
    version = str(framework.get("version", "")).strip()
    return version.startswith("v0.8") or "paper_fragments" in framework


def _dependency_hits_question(dependency: str, question: str) -> bool:
    return dependency == question or dependency.startswith(f"{question}.") or dependency.startswith(f"{question}:")


def _mark_paper_fragments_stale(framework: dict[str, Any], stale_questions: set[str]) -> list[str]:
    fragments = framework.get("paper_fragments", []) or []
    by_id = {
        str(item.get("id")): item
        for item in fragments
        if isinstance(item, dict) and str(item.get("id", "")).strip()
    }
    stale_ids: set[str] = set()
    for fragment_id, fragment in by_id.items():
        scope = str(fragment.get("scope", ""))
        dependencies = [str(item) for item in fragment.get("depends_on", []) or []]
        if scope in stale_questions or any(
            _dependency_hits_question(dep, question)
            for dep in dependencies
            for question in stale_questions
        ):
            stale_ids.add(fragment_id)

    changed = True
    while changed:
        changed = False
        for fragment_id, fragment in by_id.items():
            if fragment_id in stale_ids:
                continue
            dependencies = {str(item) for item in fragment.get("depends_on", []) or []}
            if dependencies & stale_ids:
                stale_ids.add(fragment_id)
                changed = True

    for fragment_id in stale_ids:
        by_id[fragment_id]["status"] = "stale"
    return sorted(stale_ids)


def _stale_paper_fragment_ids(framework: Mapping[str, Any]) -> list[str]:
    return sorted(
        str(item.get("id"))
        for item in framework.get("paper_fragments", []) or []
        if isinstance(item, Mapping) and item.get("status") == "stale" and item.get("id")
    )



def stage_requirements(
    scope: str,
    output_contract: Mapping[str, Any],
    state: Mapping[str, Any] | None = None,
) -> list[str]:
    sync = output_contract.get("project_sync") or {}
    required = list((sync.get("stage_requirements") or {}).get(scope, []))
    if state is not None and preprocessing_decision(state) == "project_level":
        conditional = (
            (sync.get("conditional_stage_requirements") or {})
            .get("preprocessing_decision_project_level", {})
        )
        required.extend((conditional or {}).get(scope, []) or [])
    return unique(required)


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



def _normalized_validated_hashes(entry: Mapping[str, Any]) -> dict[str, str]:
    validated = ARTIFACT_IDENTITY.normalize_artifact_hashes(
        entry.get("validated_artifact_hashes"),
        legacy_primary_fallback=entry.get("validated_model_hash"),
    )
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


LAYER_TRANSITION_EVENTS = {
    "data": "data_changed",
    "primary_code": "primary_code_changed",
    "analysis_code": "analysis_code_changed",
    "solution_workbook": "solution_workbook_changed",
    "result_analysis_workbook": "analysis_workbook_changed",
    "matlab_script": "matlab_script_changed",
    "figure_bundle": "figure_bundle_changed",
    "framework": "paper_fragment_changed",
}


def _snapshot_transition_events(entry: Mapping[str, Any], snapshot: Mapping[str, Any]) -> list[str]:
    current = dict(snapshot.get("artifact_hashes", {}))
    primary_changed, analysis_changed = _code_hash_mismatches(entry, snapshot)
    events: list[str] = []
    if primary_changed:
        events.append("primary_code_changed")
    if analysis_changed:
        events.append("analysis_code_changed")
    for layer in sorted(_mismatched_layers(entry, current)):
        event = LAYER_TRANSITION_EVENTS.get(layer)
        if event and event not in events:
            events.append(event)
    return events


def _apply_snapshot_to_state(
    root: Path, state: dict[str, Any], snapshot: Mapping[str, Any]
) -> tuple[set[str], list[dict[str, Any]]]:
    key = str(snapshot["key"])
    entry = state.setdefault("subproblems", {}).setdefault(key, {})
    ARTIFACT_IDENTITY.canonicalize_entry_hashes(entry)
    current = dict(snapshot.get("artifact_hashes", {}))
    transition_reports: list[dict[str, Any]] = []
    for event in _snapshot_transition_events(entry, snapshot):
        transition_reports.append(
            STATE_TRANSITIONS.apply_transition(
                state,
                event=event,
                source_question=key,
                contract=STATE_TRANSITION_CONTRACT,
            )
        )
    entry = state.setdefault("subproblems", {}).setdefault(key, {})
    entry["artifact_hashes"] = current
    if snapshot.get("primary_code"):
        entry["code"] = snapshot["primary_code"]
    if snapshot.get("result_analysis_code"):
        entry["result_analysis_code"] = snapshot["result_analysis_code"]
    for field in ("solution_workbook", "result_analysis_workbook", "matlab_script"):
        if snapshot.get(field):
            entry[field] = snapshot[field]

    stale_layers = set(entry.get("stale_layers", []) or [])
    evidence = _question_dir(root, str(snapshot["chinese_name"])) / "figure_evidence.yaml"
    if evidence.is_file():
        relative = evidence.relative_to(root).as_posix()
        values = list(entry.get("evidence", []) or [])
        if relative not in values:
            values.append(relative)
        entry["evidence"] = values
    return stale_layers, transition_reports


def _replace_or_prepend(lines: list[str], prefix: str, replacement: str) -> list[str]:
    for index, line in enumerate(lines):
        if line.startswith(prefix):
            lines[index] = replacement
            return lines
    return [replacement, *lines]


def _framework_header_text(path: Path, scope: str, stale: bool) -> str | None:
    """Return the next framework text without mutating the live project."""
    if not path.is_file():
        return None
    lines = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n").splitlines()
    timestamp = datetime.now(timezone.utc).isoformat()
    lines = _replace_or_prepend(lines, "- 最近同步：", f"- 最近同步：`{scope}`")
    lines = _replace_or_prepend(lines, "- 最近同步时间：", f"- 最近同步时间：`{timestamp}`")
    lines = _replace_or_prepend(lines, "- 当前状态：", f"- 当前状态：`{'stale' if stale else 'current'}`")
    return "\n".join(lines).rstrip() + "\n"


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
        if int(report.get("unresolved_citations", 0) or 0) != 0:
            issues.append("compile_report 存在未解析文献引用")
        issues.extend(
            LATEX_DELIVERY.verify_compile_report(
                project=root, main=source, pdf=pdf, report=report
            )
        )
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
    if required.intersection({"docx_draft", "latex_source", "compiled_pdf", "validated_submission_package"}):
        framework = state.get("paper_framework") or {}
        if _uses_fragment_stale(framework):
            stale = _stale_paper_fragment_ids(framework)
            if stale:
                issues.append(f"正式论文交付禁止使用 stale paper fragments: {stale}")
    return issues


def _preprocessing_artifact_issues(
    root: Path,
    required: set[str],
    state: Mapping[str, Any],
) -> list[str]:
    if preprocessing_decision(state) != "project_level":
        return []
    issues: list[str] = []
    preprocessing = state.get("preprocessing") or {}
    code = root / str(preprocessing.get("code") or "数据预处理/数据预处理.py")
    workbook = root / str(preprocessing.get("workbook") or "数据预处理/数据预处理结果.xlsx")
    matlab = root / "数据预处理/data_process.m"
    if "preprocessing_code" in required and not code.is_file():
        issues.append("project_level正式交付缺少数据预处理/数据预处理.py")
    if "preprocessing_workbook" in required:
        if not workbook.is_file():
            issues.append("project_level正式交付缺少数据预处理/数据预处理结果.xlsx")
        if preprocessing.get("status") != "accepted" or preprocessing.get("quality_status") != "passed":
            issues.append("project_level正式交付要求预处理工作簿accepted且预处理质量门passed")
    if "preprocessing_matlab_script" in required:
        if not matlab.is_file():
            issues.append("project_level图表及论文交付缺少数据预处理/data_process.m")
        else:
            has_title, workbook_refs, exports = _parse_matlab(matlab)
            if has_title:
                issues.append("data_process.m正式论文图不得设置整体title或sgtitle；正式图名由LaTeX/DOCX caption承担")
            if "数据预处理结果.xlsx" not in {Path(item).name for item in workbook_refs}:
                issues.append("data_process.m必须读取数据预处理结果.xlsx")
            text = matlab.read_text(encoding="utf-8", errors="ignore")
            code_text = _matlab_executable_text(text)
            forbidden_matches = sorted({
                match.group(1).lower()
                for match in MATLAB_PREPROCESSING_FORBIDDEN_RE.finditer(code_text)
            })
            dispatch_matches = sorted({
                match.group(1).lower()
                for match in MATLAB_PREPROCESSING_FORBIDDEN_DISPATCH_RE.finditer(code_text)
            })
            handle_matches = sorted({
                match.group(1).lower()
                for match in MATLAB_PREPROCESSING_FORBIDDEN_HANDLE_RE.finditer(code_text)
            })
            if forbidden_matches:
                issues.append(
                    "data_process.m不得重新执行预处理、拟合或预测；检测到MATLAB调用: "
                    + ", ".join(forbidden_matches)
                )
            if dispatch_matches:
                issues.append(
                    "data_process.m不得使用可绕过绘图职责边界的动态调用: "
                    + ", ".join(dispatch_matches)
                )
            if handle_matches:
                issues.append(
                    "data_process.m不得持有被禁止预处理函数句柄: "
                    + ", ".join(handle_matches)
                )
            for item in exports:
                export_path = (matlab.parent / item).resolve()
                if not export_path.is_file():
                    shown = export_path.relative_to(root).as_posix() if export_path.is_relative_to(root) else export_path.as_posix()
                    issues.append(f"data_process.m声明导出的图不存在: {shown}")
    return issues


def _scope_artifact_issues(
    root: Path,
    scope: str,
    state: Mapping[str, Any],
    snapshots: Mapping[str, Mapping[str, Any]],
    output_contract: Mapping[str, Any],
) -> list[str]:
    required = set(stage_requirements(scope, output_contract, state))
    issues = _formal_state_issues(required, state)
    issues.extend(_preprocessing_artifact_issues(root, required, state))
    if "python_code" in required and not all(snapshot.get("primary_code") for snapshot in snapshots.values()):
        issues.append("正式交付缺少标准主求解Python脚本")
    if "result_analysis_code" in required:
        for key, snapshot in snapshots.items():
            if not snapshot.get("result_analysis_code"):
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
    if write and state_path.is_file():
        _, state, base_generation = PROJECT_TX.load_state_for_update(root)
    else:
        state = load_yaml(state_path)
        base_generation = PROJECT_TX.state_generation(state)
    schema = load_yaml(Path(schema_path))
    output_contract = load_yaml(Path(output_contract_path))
    phase = str((state.get("project") or {}).get("current_phase", "model_design"))
    explicit_delivery_scope = delivery_scope is not None
    scope = delivery_scope or PHASE_SCOPE.get(phase, "design")
    if scope not in {"design", "code", "results", "figures", "docx", "latex", "submission"}:
        raise ValueError(f"未知delivery scope: {scope}")

    issues = contract_preflight_issues(root, scope, state_path, framework_path, output_contract)
    warnings: list[str] = []
    raw_files, raw_mode, data_issues, data_warnings = data_source_files(root, state)
    issues.extend(data_issues)
    warnings.extend(data_warnings)
    data_hash, data_mode, active_warnings = active_data_hash(root, state, raw_files, raw_mode)
    warnings.extend(active_warnings)

    decision = preprocessing_decision(state)
    if state.get("data") and decision is None:
        warnings.append("项目含数据但尚未锁定preprocessing.decision；重新进入模型设计/求解前必须补齐")

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
    stale_fragments: list[str] = []
    transition_reports: list[dict[str, Any]] = []
    transition_state = state if write else deepcopy(state)
    if state_path.is_file():
        for snapshot in snapshots.values():
            stale, reports = _apply_snapshot_to_state(root, transition_state, snapshot)
            transition_reports.extend(reports)
            if stale:
                stale_questions.append(str(snapshot["key"]))
        merged_transitions = STATE_TRANSITIONS.merge_transition_reports(transition_reports)
        stale_questions.extend(merged_transitions["affected_questions"])
        dependency_cycles = (
            merged_transitions["dependency_cycles"]
            or STATE_TRANSITIONS.dependency_cycles(transition_state.get("subproblems", {}) or {})
        )
        if dependency_cycles:
            warnings.append("检测到跨问依赖环: " + "; ".join(dependency_cycles))
    else:
        dependency_cycles = []

    framework_text_for_write: str | None = None
    if write and state_path.is_file():
        any_stale = any(
            bool(entry.get("artifacts_stale"))
            for entry in (state.get("subproblems") or {}).values()
            if isinstance(entry, Mapping)
        )
        framework = state.setdefault("paper_framework", {})
        if _uses_fragment_stale(framework):
            stale_fragments = _mark_paper_fragments_stale(framework, set(stale_questions))
            framework["sync_status"] = "current"
            header_stale = False
        else:
            framework["sync_status"] = "stale" if any_stale else "current"
            header_stale = any_stale
        framework["last_sync_scope"] = scope
        framework["last_synced_at"] = datetime.now(timezone.utc).isoformat()
        framework_text_for_write = _framework_header_text(framework_path, scope, header_stale)
        if framework_text_for_write is not None:
            framework["sha256"] = hashlib.sha256(framework_text_for_write.encode("utf-8")).hexdigest()
        state.setdefault("artifacts", {})["sync_report"] = "sync_report.yaml"
        state.setdefault("execution", {})["last_sync_report"] = "sync_report.yaml"
    else:
        for key, entry in (transition_state.get("subproblems", {}) or {}).items():
            if isinstance(entry, Mapping) and entry.get("artifacts_stale"):
                stale_questions.append(str(key))
        framework = state.get("paper_framework") or {}
        if _uses_fragment_stale(framework):
            stale_fragments = _stale_paper_fragment_ids(framework)

    report = {
        "status": "passed" if not issues else "failed",
        "delivery_scope": scope,
        "formal_delivery_scope": explicit_delivery_scope,
        "write": write,
        "strict": strict,
        "preprocessing_decision": decision,
        "data_hash_mode": data_mode,
        "data_hash": data_hash,
        "framework_hash": (
            hashlib.sha256(framework_text_for_write.encode("utf-8")).hexdigest()
            if framework_text_for_write is not None
            else sha256_file(framework_path) if framework_path.is_file() else None
        ),
        "questions": snapshots,
        "stale_questions": sorted(set(stale_questions)),
        "stale_paper_fragments": stale_fragments,
        "state_transitions": transition_reports,
        "dependency_cycles": dependency_cycles,
        "issues": sorted(set(issues)),
        "warnings": sorted(set(warnings)),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    if write:
        report_text = yaml.safe_dump(report, allow_unicode=True, sort_keys=False)
        if state_path.is_file():
            before_state = (
                [("模型论文框架.md", framework_text_for_write)]
                if framework_text_for_write is not None
                else []
            )

            def _validate_staged_sync(staged: Mapping[str, Path]) -> None:
                staged_state = load_yaml(staged[PROJECT_TX.STATE_RELATIVE_PATH])
                if framework_text_for_write is not None:
                    staged_framework = staged["模型论文框架.md"]
                    expected = ((staged_state.get("paper_framework") or {}).get("sha256"))
                    actual = sha256_file(staged_framework)
                    if expected != actual:
                        raise ValueError("staged paper_framework.sha256 self-check failed")
                staged_report = load_yaml(staged["sync_report.yaml"])
                if staged_report.get("framework_hash") != report.get("framework_hash"):
                    raise ValueError("staged sync report framework hash self-check failed")

            PROJECT_TX.commit_project_state(
                root,
                state,
                expected_generation=base_generation,
                writes_before_state=before_state,
                writes_after_state=[("sync_report.yaml", report_text)],
                validators=[_validate_staged_sync],
            )
        else:
            PROJECT_TX.atomic_write_text(root / "sync_report.yaml", report_text)
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
