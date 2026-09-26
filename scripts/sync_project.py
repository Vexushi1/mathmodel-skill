#!/usr/bin/env python3
"""Synchronize project artifacts without promoting preprocessing, solve, or analysis decisions."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml
from jsonschema import Draft202012Validator

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = str(SKILL_ROOT / "scripts")
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
import artifact_identity as ARTIFACT_IDENTITY  # noqa: E402
import project_transaction as PROJECT_TX  # noqa: E402
import runtime_assurance as RUNTIME_ASSURANCE  # noqa: E402
import artifact_fingerprint as ARTIFACT_FINGERPRINT  # noqa: E402
import project_snapshot as PROJECT_SNAPSHOT  # noqa: E402
import stage_code as STAGE_CODE  # noqa: E402
import conformance_gate as CONFORMANCE  # noqa: E402
from execution_protocol import declared_input_paths
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


def _claim_policy_issues(framework: Mapping[str, Any], schema: Mapping[str, Any]) -> list[str]:
    """Validate an explicit claim policy before any project writer can run."""
    if "claim_consumption_policy" not in framework:
        return []
    validator = Draft202012Validator({
        "$ref": "#/$defs/claim_consumption_policy", "$defs": schema.get("$defs", {}),
    })
    errors = sorted(validator.iter_errors(framework["claim_consumption_policy"]),
                    key=lambda error: (list(map(str, error.absolute_path)), error.message))
    if errors:
        return [f"claim consumption policy: {error.message}" for error in errors]
    issues: list[str] = []
    record_validator = Draft202012Validator({
        "$ref": "#/$defs/claim_evidence", "$defs": schema.get("$defs", {}),
    })
    for error in record_validator.iter_errors(framework.get("claim_evidence")):
        issues.append(f"B1 claim record: {error.message}")
    fragment_validator = Draft202012Validator({
        "$ref": "#/$defs/paper_fragment_entry", "$defs": schema.get("$defs", {}),
    })
    fragments = framework.get("paper_fragments")
    if not isinstance(fragments, list):
        issues.append("paper_fragments must be a list")
    else:
        for index, fragment in enumerate(fragments):
            for error in fragment_validator.iter_errors(fragment):
                issues.append(f"paper fragment {index}: {error.message}")
    if issues:
        return issues
    issues.extend(STATE_VALIDATION._validate_claim_consumption_policy(framework))
    fragment_issues, _ = STATE_VALIDATION._validate_paper_fragments(framework)
    issues.extend(fragment_issues)
    return issues


def _current_rejected_claim_ids(state: Mapping[str, Any], schema: Mapping[str, Any]) -> list[str]:
    """Return exact B1 IDs for current modifying/rejecting dispositions only."""
    framework = state.get("paper_framework", {}) or {}
    claims = ((framework.get("claim_evidence") or {}).get("claims") or [])
    by_id = {row["id"]: row for row in claims
             if isinstance(row, Mapping) and isinstance(row.get("id"), str)}
    validator = Draft202012Validator({
        "$ref": "#/$defs/analysis_evidence_entry", "$defs": schema.get("$defs", {}),
    })
    selected: set[str] = set()
    for question, entry in sorted((state.get("subproblems") or {}).items()):
        if not isinstance(entry, Mapping):
            raise ValueError(f"{question}: subproblem must be a mapping")
        dispositions = entry.get("analysis_evidence_dispositions", []) or []
        if not isinstance(dispositions, list):
            raise ValueError(f"{question}: analysis dispositions must be a list")
        seen_dispositions: set[str] = set()
        for disposition in dispositions:
            if not isinstance(disposition, Mapping):
                raise ValueError(f"{question}: analysis disposition must be a mapping")
            error = next(validator.iter_errors(disposition), None)
            if error:
                raise ValueError(f"{question}: malformed analysis disposition: {error.message}")
            disposition_id = disposition["id"]
            if disposition_id in seen_dispositions:
                raise ValueError(f"{question}: duplicate analysis disposition ID {disposition_id}")
            seen_dispositions.add(disposition_id)
            if (disposition.get("status", "current") != "current"
                    or disposition.get("disposition") not in {"modify", "reject"}):
                continue
            target = disposition.get("target_claim")
            if not isinstance(target, str) or target not in by_id:
                raise ValueError(f"{question}/{disposition.get('id')}: target_claim must be an exact B1 claim ID")
            if by_id[target].get("scope") != question:
                raise ValueError(f"{question}/{disposition.get('id')}: target_claim {target} scope does not match {question}")
            selected.add(target)
    return sorted(selected)


def _read_framework_exact(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def _framework_header_preserving_layout(text: str, scope: str, stale: bool) -> str:
    """Apply the usual sync header fields while retaining all other line endings."""
    lines = text.splitlines(keepends=True)
    newline = "\r\n" if "\r\n" in text else "\n"
    replacements = (
        ("- 最近同步：", f"- 最近同步：`{scope}`"),
        ("- 最近同步时间：", f"- 最近同步时间：`{datetime.now(timezone.utc).isoformat()}`"),
        ("- 当前状态：", f"- 当前状态：`{'stale' if stale else 'current'}`"),
    )
    for prefix, replacement in replacements:
        match = next((index for index, line in enumerate(lines) if line.startswith(prefix)), None)
        if match is None:
            lines.insert(0, replacement + newline)
        else:
            line = lines[match]
            ending = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
            lines[match] = replacement + ending
    return "".join(lines)


def _framework_fragment_status_text(text: str, stale_ids: set[str]) -> str:
    """Patch only existing seven-column status cells for selected fragment IDs."""
    if not stale_ids:
        return text
    lines = text.splitlines(keepends=True)
    heading = "### Paper Fragment Dependency Map"
    starts = [index for index, line in enumerate(lines) if line.rstrip("\r\n") == heading]
    if len(starts) != 1:
        raise ValueError("Framework requires exactly one Paper Fragment Dependency Map")
    seen: set[str] = set()
    for index in range(starts[0] + 1, len(lines)):
        line = lines[index]
        body = line.rstrip("\r\n")
        if re.match(r"^#{1,4}\s+", body):
            break
        if not body.startswith("|"):
            continue
        cells = body.split("|")
        if len(cells) != 9 or cells[0] or cells[-1].strip():
            raise ValueError("Framework fragment row must have seven columns")
        fragment_id = cells[1].strip()
        if fragment_id not in stale_ids:
            continue
        if fragment_id in seen:
            raise ValueError(f"Framework repeats fragment ID {fragment_id}")
        seen.add(fragment_id)
        status = re.fullmatch(r"([ \t]*)(current|stale|not_applicable)([ \t]*)", cells[7])
        if status is None:
            raise ValueError(f"Framework fragment {fragment_id} has malformed status cell")
        cells[7] = status.group(1) + "stale" + status.group(3)
        lines[index] = "|".join(cells) + line[len(body):]
    missing = sorted(stale_ids - seen)
    if missing:
        raise ValueError(f"Framework missing stale fragment rows: {missing}")
    return "".join(lines)



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
    *,
    candidate_state: Mapping[str, Any] | None = None,
    candidate_framework_text: str | None = None,
) -> list[str]:
    issues: list[str] = []
    required = set(stage_requirements(scope, output_contract))
    if "project_state" in required and not state_path.is_file():
        issues.append("项目状态校验: 缺少 state/project_state.yaml")
    elif state_path.is_file():
        issues.extend(
            f"项目状态校验: {item}"
            for item in (
                STATE_VALIDATION.validate_state_payload(
                    candidate_state, project_root=root,
                    framework_text_override=candidate_framework_text,
                )
                if candidate_state is not None
                else STATE_VALIDATION.validate_state_file(state_path, project_root=root)
            )
        )
    if "model_paper_framework" in required and not framework_path.is_file():
        issues.append("模型论文框架校验: 缺少 模型论文框架.md")
    elif framework_path.is_file():
        issues.extend(
            f"模型论文框架校验: {item}"
            for item in FRAMEWORK_VALIDATION.validate_framework_text(
                candidate_framework_text if candidate_framework_text is not None
                else framework_path.read_text(encoding="utf-8"),
                state=candidate_state if candidate_state is not None else load_yaml(state_path),
                project_root=root,
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
    observed = snapshot.get("solver_execution_observed") or {}
    changes = {"primary": primary_changed, "analysis": analysis_changed}
    selections = entry.get("solver_execution", {})
    if not isinstance(selections, Mapping):
        return True, True
    for stage, path_field in (("primary", "code"), ("analysis", "result_analysis_code")):
        delivered = selections.get(stage, {})
        current = observed.get(stage) or {}
        if not isinstance(delivered, Mapping):
            changes[stage] = True
            continue
        if delivered.get("bundle_sha256"):
            changes[stage] |= bool(
                current.get("bundle_sha256") != str(delivered["bundle_sha256"]).lower()
                or current.get("backend") != snapshot.get("project_backend")
                or current.get("entrypoint") != entry.get(path_field)
                or current.get("binding_issues")
            )
        elif current.get("binding_issues") and entry.get(path_field):
            changes[stage] = True
    return changes["primary"], changes["analysis"]


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
    observed_inputs = snapshot.get("solver_execution_observed") or {}
    for stage, event in (("primary", "data_changed"), ("analysis", "analysis_inputs_changed")):
        if ((observed_inputs.get(stage) or {}).get("inputs") or {}).get("issues"):
            events.append(event)
    if primary_changed:
        events.append("primary_code_changed")
    if analysis_changed:
        events.append("analysis_code_changed")
    for stage, observation in (snapshot.get("conformance_observed") or {}).items():
        field = "code" if stage == "primary" else "result_analysis_code"
        if observation.get("issues") and entry.get(field):
            events.append(f"{stage}_conformance_changed")
    for layer in sorted(_mismatched_layers(entry, current)):
        event = LAYER_TRANSITION_EVENTS.get(layer)
        if event and event not in events:
            events.append(event)
    return events


def _apply_snapshot_to_state(
    root: Path, state: dict[str, Any], snapshot: Mapping[str, Any]
) -> tuple[set[str], list[dict[str, Any]]]:
    key = str(snapshot["key"])
    subproblems = state.get("subproblems") or {}
    if key not in subproblems:
        return set(), []  # Files in an unregistered question directory are historical observations.
    entry = subproblems[key]
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


_LEGACY_BACKEND_LINE = re.compile(r"^(\s*)- 已选求解后端 / 选择理由 / 依赖核验([：:])(.*)$")
_QUESTION_FRAMEWORK_HEADING = re.compile(r"^### Q[1-9][0-9]*(?:$|[：: ])")
_HISTORY_MANIFEST = re.compile(r"^state/backend_history/([0-9a-f]{32})/manifest\.json$")
_HISTORY_REPORT = re.compile(r"^state/backend_migration_reports/([0-9a-f]{32})\.yaml$")


def backend_history_append_issues(
    previous_state: Mapping[str, Any], candidate_state: Mapping[str, Any],
) -> list[str]:
    """Check that a new state retains every previously published migration reference."""
    previous = (previous_state.get("execution") or {}).get("backend_migration_history") or []
    candidate = (candidate_state.get("execution") or {}).get("backend_migration_history") or []
    if not isinstance(previous, list) or not isinstance(candidate, list):
        return ["backend_migration_history must be an array"]
    issues = []
    if candidate[:len(previous)] != previous:
        issues.append("backend_migration_history must retain the previous references in order")
    seen: set[str] = set()
    for index, item in enumerate(candidate):
        if not isinstance(item, Mapping):
            issues.append(f"backend_migration_history[{index}] must be a reference")
            continue
        manifest = _HISTORY_MANIFEST.fullmatch(str(item.get("manifest", "")))
        report = _HISTORY_REPORT.fullmatch(str(item.get("report", "")))
        if manifest is None or report is None or manifest.group(1) != report.group(1):
            issues.append(f"backend_migration_history[{index}] manifest/report id mismatch")
            continue
        migration_id = manifest.group(1)
        if migration_id in seen:
            issues.append(f"backend_migration_history[{index}] repeats migration id")
        seen.add(migration_id)
    return issues


def render_project_backend_memory(text: str, candidate_state: Mapping[str, Any]) -> str:
    """Patch only project backend memory and exact legacy template fields in framework text."""
    backend = STAGE_CODE.current_project_backend(candidate_state, required=True)
    reason = (candidate_state.get("execution") or {}).get("solver_backend_selection_reason")
    if (not isinstance(reason, str) or not reason.strip() or len(reason.splitlines()) != 1
            or any(ord(char) < 32 for char in reason)):
        raise ValueError("project backend reason must be one non-empty text line")
    reason = reason.strip()
    without_crlf = text.replace("\r\n", "")
    if "\r" in without_crlf or ("\r\n" in text and "\n" in without_crlf):
        raise ValueError("framework has unsupported mixed line endings")
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(newline)
    current = [i for i, line in enumerate(lines) if line == "## 当前有效口径"]
    if len(current) != 1:
        raise ValueError("framework requires one exact current-state heading")

    # Leave the known per-question template line byte-for-byte intact so an
    # accepted question section keeps its existing framework identity. Its
    # historical meaning is stated once in the new global project section.
    section = ""
    question = ""
    converted: set[str] = set()
    for line in lines:
        if line.startswith("## "):
            section, question = line, ""
        elif line.startswith("### "):
            question = (line.split("：", 1)[0].split(":", 1)[0].split(" ", 2)[1]
                        if _QUESTION_FRAMEWORK_HEADING.match(line) else "")
        if "已选求解后端" not in line:
            continue
        match = _LEGACY_BACKEND_LINE.fullmatch(line)
        if match is None or section != "## 各问模型与结果" or not question or question in converted:
            raise ValueError("ambiguous legacy per-question backend field in framework")
        converted.add(question)

    start = current[0]
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    headings = [i for i, line in enumerate(lines) if line == "### 全项目数值实现"]
    if any(line.startswith("### 全项目数值实现") and line != "### 全项目数值实现" for line in lines):
        raise ValueError("ambiguous project backend section in framework")
    if len(headings) > 1 or (headings and not start < headings[0] < end):
        raise ValueError("ambiguous project backend section in framework")
    backend_line = f"- 项目求解后端：`{backend}`"
    reason_line = f"- 项目后端选择理由：{reason}"
    history_note = "- 逐问旧已选后端/理由为迁移前历史记录，当前取项目根。"
    if not headings:
        if any("项目求解后端" in line or "项目后端选择理由" in line for line in lines):
            raise ValueError("project backend field appears outside its section")
        insert = ["", "### 全项目数值实现", "", backend_line, reason_line]
        if converted:
            insert.append(history_note)
        insert.append("")
        if start + 1 < len(lines) and lines[start + 1] == "":
            del lines[start + 1]
        lines[start + 1:start + 1] = insert
    else:
        heading = headings[0]
        block_end = next(
            (i for i in range(heading + 1, end) if lines[i].startswith(("### ", "## "))), end,
        )
        if any(
            ("项目求解后端" in line or "项目后端选择理由" in line)
            for index, line in enumerate(lines) if not heading < index < block_end
        ):
            raise ValueError("project backend field appears outside its section")
        body = lines[heading + 1:block_end]
        retained = []
        found = {"backend": 0, "reason": 0, "history": 0}
        for line in body:
            if line.startswith("- 项目求解后端："):
                found["backend"] += 1
            elif line.startswith("- 项目后端选择理由："):
                found["reason"] += 1
            elif line == history_note:
                found["history"] += 1
            elif "项目求解后端" in line or "项目后端选择理由" in line:
                raise ValueError("ambiguous project backend field in framework")
            else:
                retained.append(line)
        if max(found.values()) > 1:
            raise ValueError("duplicate project backend field in framework")
        if retained and retained[0] == "":
            retained.pop(0)
        if retained and retained[0] != "":
            retained.insert(0, "")
        lines[heading + 1:block_end] = [
            "", backend_line, reason_line, *([history_note] if converted else []), *retained,
        ]
    return newline.join(lines)


def _approved_figure_issues(
    root: Path, state: Mapping[str, Any], snapshots: Mapping[str, Mapping[str, Any]],
) -> tuple[list[str], list[str]]:
    approved = ((state.get("artifacts") or {}).get("approved_figures") or [])
    if not approved:
        return ["缺少已批准图表"], []
    issues: list[str] = []
    warnings: list[str] = []
    approved_paths = {(root / str(item)).resolve() for item in approved}
    discovered = {(root / name).resolve() for snapshot in snapshots.values() for name in snapshot.get("figures", [])}
    for item in approved:
        path = (root / str(item)).resolve()
        if not path.is_relative_to(root):
            issues.append(f"已批准图表路径越出项目根目录: {item}")
        elif not path.is_file():
            issues.append(f"已批准图表不存在: {item}")
        elif path not in discovered:
            # An independent project-level diagram need not belong to any question.
            # Report the uncovered scope without inventing a per-question binding.
            warnings.append(f"已批准图表未映射到本问图哈希: {item}；独立全局图不强分小问，需按现有框架另行核对来源")
    for key, snapshot in snapshots.items():
        if not {(root / path).resolve() for path in snapshot.get("figures", [])}.intersection(approved_paths):
            continue
        entry = (state.get("subproblems") or {}).get(key) or {}
        if not (entry.get("validated_artifact_hashes") or {}).get("figure_bundle"):
            issues.append(f"{key}: 当前图表映射缺少已验证figure_bundle哈希，需人工复核绑定；同步不自动批准")
    return issues, warnings


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


def _submission_zip_issues(
    path: Path, require_matlab: bool = True, *, required_paths: Iterable[str] | None = None,
) -> list[str]:
    if not path.is_file():
        return ["缺少提交ZIP"]
    try:
        with zipfile.ZipFile(path) as archive:
            actual_names = [name for name in archive.namelist() if not name.endswith("/")]
            names = [name.lower() for name in actual_names]
    except Exception as exc:  # noqa: BLE001
        return [f"无法读取提交ZIP: {exc}"]
    issues: list[str] = []
    if not any(name.endswith(".pdf") for name in names):
        issues.append("提交ZIP缺少PDF")
    if required_paths is not None:
        for required in sorted(set(required_paths)):
            if required not in actual_names:
                issues.append(f"提交ZIP缺少当前必需文件: {required}")
    elif not any(name.endswith(".py") for name in names):
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
        if "result_analysis_report" in required:
            analysis_status = entry.get("result_analysis_status")
            if analysis_status not in {"passed", "not_required"}:
                issues.append(f"{name}: 正式交付要求 result_analysis_status=passed 或 not_required")
            elif analysis_status == "not_required" and not str(
                entry.get("result_analysis_requirement_reason") or ""
            ).strip():
                issues.append(
                    f"{name}: result_analysis_status=not_required必须提供非空result_analysis_requirement_reason"
                )
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
    *,
    warnings: list[str] | None = None,
) -> list[str]:
    required = set(stage_requirements(scope, output_contract, state))
    issues = _formal_state_issues(required, state)
    issues.extend(_preprocessing_artifact_issues(root, required, state))
    if required.intersection({"python_code", "primary_code"}) and not all(snapshot.get("primary_code") for snapshot in snapshots.values()):
        issues.append("正式交付缺少标准主求解脚本")
    if "result_analysis_code" in required:
        for key, snapshot in snapshots.items():
            if not snapshot.get("result_analysis_code"):
                issues.append(f"{key}: 正式结果交付缺少独立结果深化分析脚本")
    if "solution_workbook" in required and not all(snapshot.get("solution_workbook") for snapshot in snapshots.values()):
        issues.append("结果交付缺少标准求解结果工作簿")
    if "result_quality_report" in required and not all(snapshot.get("result_quality_report") for snapshot in snapshots.values()):
        issues.append("结果交付缺少主结果质量报告")
    if "result_analysis_workbook" in required and not all(snapshot.get("result_analysis_workbook") for snapshot in snapshots.values()):
        issues.append("结果交付缺少标准结果深化分析工作簿")
    if "result_analysis_report" in required and not all(snapshot.get("result_analysis_report") for snapshot in snapshots.values()):
        issues.append("结果交付缺少结果深化分析报告或明确的not_required判定")
    if "approved_figures" in required:
        figure_issues, figure_warnings = _approved_figure_issues(root, state, snapshots)
        issues.extend(figure_issues)
        if warnings is not None:
            warnings.extend(figure_warnings)
    if "docx_draft" in required:
        issues.extend(_docx_issues(root, state))
    if required.intersection({"latex_source", "compiled_pdf", "compile_report"}):
        issues.extend(_compile_artifact_issues(root, state))
    if "validated_submission_package" in required:
        from submission_requirements import reproducibility_requirements

        artifacts = state.get("artifacts") or {}
        package = root / str(artifacts.get("submission_package") or "submission/submission.zip")
        package_paths, package_issues = reproducibility_requirements(root, state)
        issues.extend(package_issues)
        issues.extend(_submission_zip_issues(package, require_matlab=True, required_paths=package_paths))
    return issues


def _capture_sync_source(root: Path, read_set: dict[str, str | None], path: Path) -> None:
    """Bind a source before sync reads it; None also guards an expected absence."""
    relative = path.relative_to(root).as_posix()
    guarded = PROJECT_TX._guarded_path(root, relative)
    if os.path.lexists(guarded) and not guarded.is_file():
        raise PROJECT_TX.ReadSetConflictError(f"sync source is not a regular file: {relative}")
    digest = PROJECT_TX.sha256_file(guarded) if guarded.is_file() else None
    if relative in read_set and read_set[relative] != digest:
        raise PROJECT_TX.ReadSetConflictError(f"sync source changed during observation: {relative}")
    read_set[relative] = digest


def _capture_sync_question_sources(
    root: Path, name: str, entry: Mapping[str, Any], read_set: dict[str, str | None],
) -> set[str]:
    """Capture registered numerical sources and standard observation candidates."""
    result_dir = _question_dir(root, name)
    number = question_number(name)
    for stage, field in (("primary", "code"), ("analysis", "result_analysis_code")):
        if number is not None:
            for filename in STAGE_CODE._names(name, stage).values():
                _capture_sync_source(root, read_set, root / f"{name}求解" / filename)
        relative = entry.get(field)
        if not isinstance(relative, str) or not relative:
            continue
        try:
            code = STAGE_CODE._relative_path(root, relative)
        except STAGE_CODE.StageCodeError:
            continue  # The normal snapshot reports invalid registered paths.
        _capture_sync_source(root, read_set, code)
        if not code.is_file():
            continue
        try:
            _, config = STAGE_CODE.parse_stage_config(code)
        except (OSError, ValueError, SyntaxError, TypeError):
            continue  # The normal snapshot reports invalid RUN_CONFIG.
        for item in config.get("code_dependencies", []) or []:
            if isinstance(item, Mapping) and isinstance(item.get("path"), str):
                try:
                    _capture_sync_source(root, read_set, STAGE_CODE._relative_path(root, item["path"]))
                except STAGE_CODE.StageCodeError:
                    pass
        try:
            declared_inputs = declared_input_paths(config)
        except ValueError:
            declared_inputs = []  # Snapshot observation reports the invalid shape; no current qualification.
        for relative_input in declared_inputs:
            if isinstance(relative_input, str):
                try:
                    _capture_sync_source(root, read_set, STAGE_CODE._relative_path(root, relative_input))
                except STAGE_CODE.StageCodeError:
                    pass
    for suffix in ("求解结果.xlsx", "结果深化分析.xlsx", "敏感性与鲁棒性结果.xlsx"):
        _capture_sync_source(root, read_set, result_dir / f"{name}{suffix}")
    for field in ("solution_workbook", "result_analysis_workbook"):
        relative = entry.get(field)
        if isinstance(relative, str) and relative:
            try:
                _capture_sync_source(root, read_set, STAGE_CODE._relative_path(root, relative))
            except STAGE_CODE.StageCodeError:
                pass
    plot = result_dir / (f"q{number}_plot.m" if number else "q_plot.m")
    _capture_sync_source(root, read_set, plot)
    _capture_sync_source(root, read_set, result_dir / "figure_evidence.yaml")
    figures, _ = PROJECT_SNAPSHOT.scoped_figure_files(root, plot, entry)
    for figure in figures:
        _capture_sync_source(root, read_set, figure)
    return {figure.relative_to(root).as_posix() for figure in figures}


def _verify_sync_question_sources(
    snapshot: Mapping[str, Any], read_set: Mapping[str, str | None], figures: set[str],
) -> None:
    """Do not pair observations with an uncaptured or different source version."""
    if set(snapshot.get("figures", [])) != figures:
        raise PROJECT_TX.ReadSetConflictError("sync figure discovery changed during observation")
    observed: dict[str, str] = {}
    for stage in ("primary", "analysis"):
        row = (snapshot.get("solver_execution_observed") or {}).get(stage) or {}
        for source in row.get("files", []) or []:
            observed[source["path"]] = source["sha256"]
        for relative in ((row.get("inputs") or {}).get("paths") or []):
            if relative not in read_set:
                raise PROJECT_TX.ReadSetConflictError(f"sync input was not captured: {relative}")
    for field, digest_field in (
        ("primary_code", "primary_code_sha256"),
        ("result_analysis_code", "analysis_code_sha256"),
    ):
        if snapshot.get(field) and snapshot.get(digest_field):
            observed[snapshot[field]] = snapshot[digest_field]
    for field in ("solution_workbook", "result_analysis_workbook", "matlab_script"):
        relative = snapshot.get(field)
        if relative and (digest := (snapshot.get("artifact_hashes") or {}).get(field)):
            observed[relative] = digest
    observed.update(snapshot.get("individual_figure_hashes") or {})
    for relative, digest in observed.items():
        if relative not in read_set or read_set[relative] != digest:
            raise PROJECT_TX.ReadSetConflictError(f"sync observation differs from captured source: {relative}")


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
    state_snapshot = RUNTIME_ASSURANCE.ProjectStateSnapshot.capture(root)
    state = state_snapshot.payload()
    state_present = state_snapshot.raw is not None
    base_generation = state_snapshot.describe()["state_generation"]
    sync_read_set = None
    if write and state_present:
        sync_read_set = {PROJECT_TX.STATE_RELATIVE_PATH: state_snapshot.describe()["sha256"]}
        for relative in ("模型论文框架.md", "sync_report.yaml"):
            path = PROJECT_TX._guarded_path(root, relative)
            sync_read_set[relative] = PROJECT_TX.sha256_file(path) if path.is_file() else None
        history = (state.get("execution") or {}).get("backend_migration_history") or []
        if isinstance(history, list):
            for item in history:
                if not isinstance(item, Mapping):
                    continue
                for field, pattern in (("manifest", _HISTORY_MANIFEST), ("report", _HISTORY_REPORT)):
                    relative = item.get(field)
                    if isinstance(relative, str) and pattern.fullmatch(relative):
                        _capture_sync_source(root, sync_read_set, root / relative)
    schema = load_yaml(Path(schema_path))
    output_contract = load_yaml(Path(output_contract_path))
    phase = str((state.get("project") or {}).get("current_phase", "model_design"))
    explicit_delivery_scope = delivery_scope is not None
    scope = delivery_scope or PHASE_SCOPE.get(phase, "design")
    if scope not in {"design", "code", "results", "figures", "docx", "latex", "submission"}:
        raise ValueError(f"未知delivery scope: {scope}")

    issues: list[str] = []
    warnings: list[str] = []
    policy_error = False
    claim_projection_write = False
    claim_propagate = False
    claim_ids: list[str] = []
    claim_stale_fragments: list[str] = []
    claim_framework_text: str | None = None
    initial_framework = state.get("paper_framework") or {}
    claim_policy_present = (write and state_present and isinstance(initial_framework, Mapping)
                            and "claim_consumption_policy" in initial_framework)
    if claim_policy_present:
        # `schema_path` above is the workbook schema; this policy uses the State schema.
        claim_schema = load_yaml(SKILL_ROOT / "core/project_state.schema.yaml")
        policy_issues = _claim_policy_issues(initial_framework, claim_schema)
        if policy_issues:
            policy_error = True
            issues.extend(policy_issues)
        else:
            policy = initial_framework["claim_consumption_policy"]
            claim_projection_write = True
            claim_propagate = (policy["protocol_version"], policy["mode"]) == ("1.1.0", "propagate")
            try:
                if not framework_path.is_file():
                    raise ValueError("claim policy requires 模型论文框架.md")
                claim_framework_text = _read_framework_exact(framework_path)
                if claim_framework_text.startswith("\ufeff"):
                    raise ValueError("UTF-8 BOM in Framework is unsupported for claim policy writes")
                recorded_hash = initial_framework.get("sha256")
                if recorded_hash and (not isinstance(recorded_hash, str)
                                      or recorded_hash.lower() != sha256_text(claim_framework_text)):
                    raise ValueError("paper_framework.sha256 does not match 模型论文框架.md")
                import claim_consumption as CLAIM_CONSUMPTION
                CLAIM_CONSUMPTION._check_projection(initial_framework, claim_framework_text)
                if claim_propagate:
                    claim_ids = _current_rejected_claim_ids(state, claim_schema)
            except (ValueError, KeyError, TypeError, UnicodeError) as exc:
                policy_error = True
                issues.append(f"claim policy projection: {exc}")
    try:
        project_backend = STAGE_CODE.current_project_backend(
            state, required=(explicit_delivery_scope or write) and scope in {
                "code", "results", "figures", "docx", "latex", "submission",
            } and phase != "data_preprocessing",
        )
    except STAGE_CODE.StageCodeError as exc:
        project_backend = None
        policy_error = True
        issues.append(f"项目数值后端: {exc}")
    raw_files, raw_mode, data_issues, data_warnings = data_source_files(root, state)
    issues.extend(data_issues)
    warnings.extend(data_warnings)
    if sync_read_set is not None:
        for source in raw_files:
            _capture_sync_source(root, sync_read_set, source)
        preprocessing = state.get("preprocessing") or {}
        if preprocessing.get("decision") == "project_level":
            relative = preprocessing.get("workbook") or "数据预处理/数据预处理结果.xlsx"
            try:
                _capture_sync_source(root, sync_read_set, STAGE_CODE._relative_path(root, relative))
            except STAGE_CODE.StageCodeError:
                pass  # The normal preflight reports an invalid workbook path.
    data_hash, data_mode, active_warnings = active_data_hash(root, state, raw_files, raw_mode)
    warnings.extend(active_warnings)

    decision = preprocessing_decision(state)
    if state.get("data") and decision is None:
        warnings.append("项目含数据但尚未锁定preprocessing.decision；重新进入模型设计/求解前必须补齐")

    conformance_read_set: dict[str, Any] = {"project": {}, "skill": {}}
    snapshots: dict[str, dict[str, Any]] = {}
    subproblems = state.get("subproblems") or {}
    question_names = _question_names(root, state)
    for chinese_name in question_names:
        key = question_key(chinese_name)
        entry = subproblems.get(key) or subproblems.get(chinese_name) or {}
        captured_figures = (
            _capture_sync_question_sources(root, chinese_name, entry, sync_read_set)
            if sync_read_set is not None else set()
        )
        snapshot = _snapshot_question(
            root, chinese_name, entry, schema, data_hash,
            scope if explicit_delivery_scope else None,
            state=state, project_backend=project_backend,
        )
        if CONFORMANCE.present(entry):
            snapshot["conformance_observed"] = {}
            for stage in CONFORMANCE.STAGES:
                slot = (entry.get("solver_execution") or {}).get(stage, {})
                boundary = ("current" if entry.get(f"{stage}_execution_status") == "accepted"
                            else "receipt" if slot.get(CONFORMANCE.DELIVERY) or slot.get("bundle_sha256") else "delivery")
                check = CONFORMANCE.inspect_gate(root, state, key, stage, boundary=boundary)
                if check["enabled"]:
                    snapshot["conformance_observed"][stage] = {
                        "status": check["status"], "issues": check["issues"],
                        "structure_status": check.get("structure_status", "not_assessed")}
                    snapshot["issues"].extend(check["issues"])
                    CONFORMANCE.merge_read_sets(conformance_read_set, check["observed_sources"])
            if sync_read_set is not None:
                for relative, digest in conformance_read_set["project"].items():
                    if relative in sync_read_set and sync_read_set[relative] != digest:
                        raise PROJECT_TX.ReadSetConflictError("conformance sync read-set conflict: " + relative)
                    sync_read_set[relative] = digest
        if sync_read_set is not None:
            _verify_sync_question_sources(snapshot, sync_read_set, captured_figures)
        snapshots[key] = snapshot
        issues.extend(f"{key}: {item}" for item in snapshot["issues"])
        warnings.extend(f"{key}: {item}" for item in snapshot["warnings"])
    if explicit_delivery_scope and scope in {"results", "figures", "docx"} and not snapshots:
        issues.append("未发现任何小问结果目录或项目状态")
    stale_questions: list[str] = []
    stale_fragments: list[str] = []
    transition_reports: list[dict[str, Any]] = []
    transition_state = state if write else deepcopy(state)
    if state_present and not policy_error:
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
    if state_present:
        any_stale = any(
            bool(entry.get("artifacts_stale"))
            for entry in (transition_state.get("subproblems") or {}).values()
            if isinstance(entry, Mapping)
        )
        framework = transition_state.setdefault("paper_framework", {})
        if claim_policy_present and policy_error:
            header_stale = False  # An invalid opt-in policy cannot enter either stale writer.
        elif _uses_fragment_stale(framework):
            stale_fragments = _mark_paper_fragments_stale(framework, set(stale_questions))
            if claim_propagate and not policy_error:
                try:
                    claim_closure = set(STATE_TRANSITIONS.claim_fragment_stale_closure(
                        framework.get("paper_fragments", []), claim_ids,
                    ))
                    for fragment in framework["paper_fragments"]:
                        if fragment["id"] in claim_closure and fragment["status"] == "current":
                            fragment["status"] = "stale"
                            claim_stale_fragments.append(fragment["id"])
                    claim_stale_fragments.sort()
                except ValueError as exc:
                    policy_error = True
                    issues.append(f"claim stale propagation: {exc}")
            if claim_projection_write and not policy_error:
                stale_fragments = _stale_paper_fragment_ids(framework)
            framework["sync_status"] = "current"
            header_stale = False
        else:
            framework["sync_status"] = "stale" if any_stale else "current"
            header_stale = any_stale
    if not claim_projection_write and not (claim_policy_present and policy_error):
        issues.extend(contract_preflight_issues(
            root, scope, state_path, framework_path, output_contract, candidate_state=transition_state,
        ))
    if explicit_delivery_scope and not (claim_policy_present and policy_error):
        issues.extend(_scope_artifact_issues(root, scope, transition_state, snapshots, output_contract, warnings=warnings))

    if write and state_present:
        framework["last_sync_scope"] = scope
        framework["last_synced_at"] = datetime.now(timezone.utc).isoformat()
        if claim_policy_present and policy_error:
            framework_text_for_write = None
        elif claim_projection_write and not policy_error:
            try:
                framework_text_for_write = _framework_fragment_status_text(
                    _framework_header_preserving_layout(claim_framework_text or "", scope, header_stale),
                    set(_stale_paper_fragment_ids(framework)),
                )
            except ValueError as exc:
                policy_error = True
                issues.append(f"claim stale propagation: {exc}")
        else:
            framework_text_for_write = _framework_header_text(framework_path, scope, header_stale)
        if framework_text_for_write is not None:
            framework["sha256"] = (
                sha256_text(framework_text_for_write) if claim_projection_write
                else hashlib.sha256(framework_text_for_write.encode("utf-8")).hexdigest()
            )
        state.setdefault("artifacts", {})["sync_report"] = "sync_report.yaml"
        state.setdefault("execution", {})["last_sync_report"] = "sync_report.yaml"
    else:
        for key, entry in (transition_state.get("subproblems", {}) or {}).items():
            if isinstance(entry, Mapping) and entry.get("artifacts_stale"):
                stale_questions.append(str(key))
        framework = transition_state.get("paper_framework") or {}
        if _uses_fragment_stale(framework):
            stale_fragments = _stale_paper_fragment_ids(framework)

    if claim_projection_write and not policy_error:
        issues.extend(contract_preflight_issues(
            root, scope, state_path, framework_path, output_contract,
            candidate_state=transition_state, candidate_framework_text=framework_text_for_write,
        ))

    report = {
        "status": "passed" if not issues else "failed",
        "delivery_scope": scope,
        "formal_delivery_scope": explicit_delivery_scope,
        "write": write,
        "write_performed": write and not policy_error,
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
    if claim_propagate:
        report["invalidated_claim_ids"] = claim_ids
        report["claim_stale_fragments"] = claim_stale_fragments
    CONFORMANCE.assert_observed(root, conformance_read_set)
    if write and not policy_error:
        if sync_read_set is not None:
            current_raw_files, current_raw_mode, _, _ = data_source_files(root, state)
            if (current_raw_mode != raw_mode or
                    {path.relative_to(root).as_posix() for path in current_raw_files}
                    != {path.relative_to(root).as_posix() for path in raw_files} or
                    _question_names(root, state) != question_names):
                raise PROJECT_TX.ReadSetConflictError("sync source discovery changed during observation")
            PROJECT_TX._check_read_set(root, sync_read_set)
        state_snapshot.assert_current()
        report_text = yaml.safe_dump(report, allow_unicode=True, sort_keys=False)
        if state_present:
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
                    actual = (
                        sha256_text(_read_framework_exact(staged_framework))
                        if claim_projection_write else sha256_file(staged_framework)
                    )
                    if expected != actual:
                        raise ValueError("staged paper_framework.sha256 self-check failed")
                    if claim_projection_write:
                        import claim_consumption as CLAIM_CONSUMPTION
                        CLAIM_CONSUMPTION._check_projection(
                            staged_state["paper_framework"], _read_framework_exact(staged_framework),
                        )
                staged_report = load_yaml(staged["sync_report.yaml"])
                if staged_report.get("framework_hash") != report.get("framework_hash"):
                    raise ValueError("staged sync report framework hash self-check failed")
                if claim_projection_write and sha256_file(staged["模型论文框架.md"]) != report["framework_hash"]:
                    raise ValueError("staged sync report framework bytes self-check failed")

            PROJECT_TX.commit_project_state(
                root,
                state,
                expected_generation=base_generation,
                expected_file_hashes=sync_read_set,
                writes_before_state=before_state,
                writes_after_state=[("sync_report.yaml", report_text)],
                validators=[_validate_staged_sync, CONFORMANCE.skill_validator(conformance_read_set)],
            )
        else:
            PROJECT_TX.atomic_write_text(root / "sync_report.yaml", report_text)
    elif not write:
        state_snapshot.assert_current()
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
    try:
        report = synchronize(
            Path(args.project_root), write=args.write, strict=args.strict,
            delivery_scope=args.delivery_scope,
        )
    except (RUNTIME_ASSURANCE.ProjectStateReadError, PROJECT_TX.TransactionRecoveryError) as exc:
        print(f"- {exc}")
        return 2
    for item in report["issues"]:
        print("-", item)
    for item in report["warnings"]:
        print("warning:", item)
    print(f"sync status: {report['status']}")
    return 1 if args.strict and report["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
