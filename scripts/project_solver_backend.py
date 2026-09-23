#!/usr/bin/env python3
"""Explicit project-backend selection and evidence-bound migration coordination.

Inspect and migration preview are read-only diagnostics. Selection and migration
are explicit guarded transactions; neither grants numerical execution eligibility
or changes mathematical Model Approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from copy import deepcopy
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from runtime_assurance import ProjectStateReadError, ProjectStateSnapshot
from stage_code import BACKENDS, POLICY_FIELDS, inspect_project_backend_declarations


def _backend(value: Any) -> bool:
    return isinstance(value, str) and value in BACKENDS


def _reason(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def inspect_backend_declarations(
    state: Mapping[str, Any], *, requested_backend: str | None = None,
) -> dict[str, Any]:
    """Compatibility entry point for the shared read-only project classification."""
    return inspect_project_backend_declarations(state, requested_backend=requested_backend)


def inspect_project(project_root: str | Path, *, requested_backend: str | None = None) -> dict[str, Any]:
    """Inspect one consistent state snapshot; do not create files or recover journals."""
    snapshot = ProjectStateSnapshot.capture(project_root)
    report = inspect_backend_declarations(snapshot.payload(), requested_backend=requested_backend)
    report["state_snapshot"] = snapshot.describe()
    snapshot.assert_current()
    return report


class ProjectBackendSelectionError(ValueError):
    """An explicit first selection cannot be committed as a current project fact."""


def select_project_backend(
    project_root: str | Path, *, backend: str, reason: str, expected_generation: int,
) -> dict[str, Any]:
    """Commit one project backend and its framework memory in the existing transaction.

    Selection is an implementation policy, not Model Approval, environment proof,
    or a numerical source transition. Historical projects use migration instead.
    """
    import project_transaction as transaction
    import sync_project
    import validate_model_paper_framework as framework_validator
    import validate_project_state as state_validator

    if not _backend(backend) or not _reason(reason):
        raise ProjectBackendSelectionError("select requires python/matlab and a non-empty reason")
    if isinstance(expected_generation, bool) or not isinstance(expected_generation, int) or expected_generation < 0:
        raise ProjectBackendSelectionError("expected_generation must be a non-negative integer")
    reason = reason.strip()
    snapshot = ProjectStateSnapshot.capture(project_root)
    if snapshot.raw is None:
        raise ProjectBackendSelectionError("selection requires an existing project state")
    root, state = snapshot.root, snapshot.payload()
    generation = snapshot.describe()["state_generation"]
    if generation != expected_generation:
        raise transaction.GenerationConflictError(
            f"stale backend selection: expected generation {expected_generation}, live generation {generation}"
        )
    declaration = inspect_backend_declarations(state)
    if declaration["issues"]:
        raise ProjectBackendSelectionError("; ".join(declaration["issues"]))
    if declaration["kind"] == "canonical_declarations":
        if declaration["selected_backend"] != backend:
            raise ProjectBackendSelectionError("project backend is already selected; use explicit migration to change it")
    elif declaration["kind"] != "unselected":
        raise ProjectBackendSelectionError("historical numerical declarations require explicit project migration")

    # Existing design records are the review linkage. Neither a placeholder
    # environment fact nor an automatic Model Approval is manufactured here.
    questions = state.get("subproblems")
    if not isinstance(questions, Mapping) or not questions:
        raise ProjectBackendSelectionError("selection requires recorded whole-project question requirements")
    requirements = state.get("requirements", {})
    recorded_questions = set(questions)
    if isinstance(requirements, Mapping):
        if any(not isinstance(requirements.get(key, []), list) for key in ("completed", "pending")):
            raise ProjectBackendSelectionError("project requirement question lists are malformed")
        declared_questions = {item for key in ("completed", "pending")
                              for item in requirements.get(key, [])
                              if isinstance(item, str) and re.fullmatch(r"Q[1-9][0-9]*", item)}
        absent_questions = sorted(declared_questions - recorded_questions)
        if absent_questions:
            raise ProjectBackendSelectionError(
                f"whole-project capability review lacks question records: {absent_questions}"
            )
    for question, entry in questions.items():
        if (not isinstance(entry, Mapping) or not _reason(entry.get("selected_model"))
                or not isinstance(entry.get("capabilities"), Mapping)
                or not isinstance(entry.get("classification", entry.get("problem_types")), Mapping)
                or not _reason(entry.get("framework_section"))):
            raise ProjectBackendSelectionError(f"{question}: model structure and numerical capability review are incomplete")

    framework = state.get("paper_framework")
    if not isinstance(framework, Mapping) or not isinstance(framework.get("path"), str):
        raise ProjectBackendSelectionError("selection requires a registered current model framework")
    framework_relative = framework["path"]
    framework_path = transaction._guarded_path(root, framework_relative)
    if not framework_path.is_file():
        raise ProjectBackendSelectionError(f"registered model framework is missing: {framework_relative}")
    framework_raw = framework_path.read_bytes()
    try:
        framework_text = framework_raw.decode("utf-8")
    except UnicodeError as exc:
        raise ProjectBackendSelectionError("model framework must be UTF-8") from exc
    for question, entry in questions.items():
        if entry["framework_section"] not in framework_text:
            raise ProjectBackendSelectionError(f"{question}: current framework section is missing")
    baseline_issues = state_validator.validate_state_payload(state, project_root=root)
    baseline_issues.extend(framework_validator.validate_framework_text(
        framework_text, state=state, project_root=root,
    ))
    if baseline_issues:
        raise ProjectBackendSelectionError(
            "current project state/framework validation failed: " + "; ".join(baseline_issues)
        )
    history_refs = []
    history_hashes: dict[str, str] = {}
    for item in (state.get("execution") or {}).get("backend_migration_history", []):
        reference = {"manifest": item["manifest"], "sha256": item["sha256"]}
        try:
            archive = transaction.verify_history_archive(root, reference)
        except (OSError, ValueError, transaction.ProjectTransactionError) as exc:
            raise ProjectBackendSelectionError("previous migration archive is incomplete or changed") from exc
        history_refs.append(reference)
        for relative, digest in archive["archive_hashes"].items():
            if relative in history_hashes and history_hashes[relative] != digest:
                raise ProjectBackendSelectionError(f"previous history has conflicting file identities: {relative}")
            history_hashes[relative] = digest
        history_hashes[item["report"]] = item["report_sha256"].lower()

    candidate = deepcopy(state)
    candidate.setdefault("execution", {}).update(zip(POLICY_FIELDS, (backend, reason)))
    rendered = sync_project.render_project_backend_memory(framework_text, candidate)
    candidate["paper_framework"]["sha256"] = framework_validator.sha256_text(rendered)
    read_set = {
        transaction.STATE_RELATIVE_PATH: snapshot.describe()["sha256"],
        framework_relative: hashlib.sha256(framework_raw).hexdigest(),
        **history_hashes,
    }
    snapshot.assert_current()
    transaction._check_read_set(root, read_set)

    def validate_candidate(staged: Mapping[str, Path]) -> None:
        staged_framework = staged[framework_relative]
        staged_state = yaml.safe_load(staged[transaction.STATE_RELATIVE_PATH].read_text(encoding="utf-8"))
        issues = state_validator.validate_state_payload(
            staged_state, project_root=root, framework_path_override=staged_framework,
        )
        issues.extend(framework_validator.validate_framework_text(
            staged_framework.read_text(encoding="utf-8"), state=staged_state, project_root=root,
        ))
        if issues:
            raise ProjectBackendSelectionError("candidate project state/framework validation failed: " + "; ".join(issues))

    if candidate == state and rendered == framework_text:
        # A repeated identical request is read-only and does not advance generation.
        snapshot.assert_current()
        transaction._check_read_set(root, read_set)
        return {"status": "unchanged", "selected_backend": backend, "selection_reason": reason,
                "state_generation": generation, "schema_validated": True,
                "design_record_questions": sorted(recorded_questions),
                "environment_verified": False, "execution_authorized": False}

    transaction_result = transaction.commit_project_state(
        root, candidate, expected_generation=expected_generation, expected_file_hashes=read_set,
        historical_archives=history_refs,
        writes_before_state=[(framework_relative, rendered)], validators=[validate_candidate],
    )
    return {"status": transaction_result["status"], "selected_backend": backend,
            "selection_reason": reason, "state_generation": transaction_result["target_generation"],
            "framework_path": framework_relative, "schema_validated": True,
            "design_record_questions": sorted(recorded_questions),
            "environment_verified": False, "execution_authorized": False}


# The preview is a proposal, never an admission gate or a writable state format.
_STAGE_KEYS = {
    "primary": ("code", "primary_code_sha256", "solution_workbook"),
    "analysis": ("result_analysis_code", "analysis_code_sha256", "result_analysis_workbook"),
}
_PREVIEW_SOURCES = (
    "core/output_contract.yaml", "core/state_transition_contract.yaml",
    "core/user_execution_contract.yaml", "core/project_state.schema.yaml",
    "core/workbook_schema.yaml", "core/numerical_verification_contract.yaml",
    "scripts/project_solver_backend.py", "scripts/project_transaction.py",
    "scripts/stage_code.py", "scripts/stage_inputs.py", "scripts/run_config_parser.py",
    "scripts/artifact_fingerprint.py", "scripts/runtime_assurance.py",
    "scripts/validate_user_execution.py", "scripts/validate_numerical_evidence.py",
    "scripts/analysis_prerequisites.py", "scripts/artifact_identity.py",
    "scripts/validate_model_approval.py", "scripts/semantic_identity.py",
    "scripts/state_transitions.py", "scripts/sync_project.py",
    "scripts/project_snapshot.py", "scripts/submission_requirements.py",
    "scripts/validate_code_delivery.py", "scripts/validate_project_state.py",
    "scripts/validate_model_paper_framework.py", "scripts/resolve_runtime.py",
)


def _preview_shape_issues(state: Mapping[str, Any]) -> list[str]:
    """Check only structures consumed by this proposal, not a second State Schema."""
    issues = []
    for name in ("preprocessing", "paper_framework"):
        if not isinstance(state.get(name, {}), Mapping):
            issues.append(f"{name} must be a mapping")
    subproblems = state.get("subproblems", {})
    for question, entry in subproblems.items():
        for name in ("artifact_hashes", "validated_artifact_hashes"):
            values = entry.get(name, {})
            if not isinstance(values, Mapping):
                issues.append(f"{question}.{name} must be a mapping")
            elif any(not isinstance(key, str) or not _sha(value) for key, value in values.items()):
                issues.append(f"{question}.{name} must contain string layer keys and SHA-256 values")
        for name in ("stale_layers", "analysis_methods"):
            values = entry.get(name, [])
            if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
                issues.append(f"{question}.{name} must be a string list")
        dependencies = entry.get("depends_on", [])
        if not isinstance(dependencies, list):
            issues.append(f"{question}.depends_on must be a list")
            continue
        for item in dependencies:
            source = item if isinstance(item, str) else item.get("question") if isinstance(item, Mapping) else None
            if not isinstance(source, str) or source not in subproblems:
                issues.append(f"{question}.depends_on contains an absent or malformed source")
            if isinstance(item, Mapping) and not isinstance(item.get("kind", ""), str):
                issues.append(f"{question}.depends_on kind must be a string")
    framework = state.get("paper_framework", {})
    if isinstance(framework, Mapping):
        fragments = framework.get("paper_fragments", [])
        if not isinstance(fragments, list):
            issues.append("paper_framework.paper_fragments must be a list")
        else:
            ids = []
            for fragment in fragments:
                if not isinstance(fragment, Mapping) or not _reason(fragment.get("id")):
                    issues.append("paper fragment must be a mapping with a non-empty id")
                    continue
                ids.append(fragment["id"])
                deps = fragment.get("depends_on", [])
                if not isinstance(deps, list) or any(not isinstance(item, str) for item in deps):
                    issues.append("paper fragment depends_on must be a string list")
            if len(ids) != len(set(ids)):
                issues.append("paper fragment ids must be unique")
    return issues


def _sha(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdefABCDEF" for c in value)


def _has_stage_binding(entry: Mapping[str, Any], stage: str) -> bool:
    code, digest, workbook = _STAGE_KEYS[stage]
    record = entry.get("solver_execution", {}).get(stage, {})
    layers = ("primary_code", "solution_workbook") if stage == "primary" else (
        "analysis_code", "result_analysis_workbook", "robustness_workbook")
    return bool(any(entry.get(key) for key in (code, digest, workbook))
                or (stage == "analysis" and entry.get("robustness_workbook"))
                or any(record.get(key) for key in ("bundle_sha256", "validated_bundle_sha256"))
                or any(entry.get(name, {}).get(layer) for name in ("artifact_hashes", "validated_artifact_hashes")
                       for layer in layers))


def _analysis_active(entry: Mapping[str, Any]) -> bool:
    if entry.get("result_analysis_status") == "not_required":
        return False
    return bool((_reason(entry.get("result_analysis_requirement_reason")) and entry.get("analysis_methods"))
                or _has_stage_binding(entry, "analysis")
                or entry.get("analysis_execution_status") in (
                    "code_delivered", "awaiting_user_execution", "workbook_received", "accepted", "rejected", "redo_required"))


def _state_delta(before: Any, after: Any, path: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    if before == after:
        return []
    if isinstance(before, Mapping) and isinstance(after, Mapping):
        result = []
        for key in sorted(set(before) | set(after)):
            location = [*path, key]
            if key not in after:
                result.append({"path": location, "operation": "remove", "before": deepcopy(before[key])})
            elif key not in before:
                result.append({"path": location, "operation": "add", "after": deepcopy(after[key])})
            else:
                result.extend(_state_delta(before[key], after[key], (*path, key)))
        return result
    return [] if before == after else [{"path": list(path), "operation": "replace",
                                        "before": deepcopy(before), "after": deepcopy(after)}]


def _retirement_candidate(state: Mapping[str, Any], stages: list[dict[str, Any]], target: str,
                          reason: str, contract: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Pure proposal; not current Schema-valid and never passed to a state writer here."""
    import state_transitions as transitions
    from sync_project import _mark_paper_fragments_stale, _uses_fragment_stale

    candidate = deepcopy(dict(state))
    entries = candidate.setdefault("subproblems", {})
    original = state.get("subproblems", {})
    rows = {(row["question"], row["stage"]): row for row in stages}
    retired = {key for key, row in rows.items() if row["action"].startswith("rebuild")}
    inactive = {key for key, row in rows.items() if row["action"] == "historical_inactive"}
    applied: set[tuple[str, str]] = set()
    reports = []
    # Capture activation before a primary profile clears the old analysis reason.
    active_analysis = {q for q, entry in original.items() if _analysis_active(entry)}
    while retired - applied:
        question, stage = min(retired - applied)
        applied.add((question, stage))
        if stage == "primary" and question in active_analysis:
            retired.add((question, "analysis"))
        report = transitions.apply_transition(
            candidate, event=f"{stage}_numerical_source_retired", source_question=question, contract=contract)
        reports.append(report)
        for item in report["transitions"]:
            q, layers = item["question"], set(item["stale_layers"])
            if layers & {"data", "primary_code", "solution_workbook"} and _has_stage_binding(original[q], "primary"):
                retired.add((q, "primary"))
            if layers & {"analysis_code", "result_analysis_workbook"} and q in active_analysis:
                retired.add((q, "analysis"))
    merged = transitions.merge_transition_reports(reports)
    for question, stage in sorted(retired | inactive):
        entry = entries[question]
        code, digest, workbook = _STAGE_KEYS[stage]
        fields = [code, digest, workbook]
        layers = ["primary_code", "solution_workbook"] if stage == "primary" else [
            "analysis_code", "result_analysis_workbook", "robustness_workbook"]
        if stage == "primary":
            fields += ["data_hash", "validated_data_hash", "model_hash", "validated_model_hash", "result_quality_report"]
            entry.get("validated_artifact_hashes", {}).pop("data", None)
        else:
            fields += ["robustness_workbook", "result_analysis_report"]
        for field in fields:
            entry.pop(field, None)
        for name in ("artifact_hashes", "validated_artifact_hashes"):
            for layer in layers:
                entry.get(name, {}).pop(layer, None)
        record = entry.get("solver_execution", {}).get(stage, {})
        record.pop("bundle_sha256", None)
        record.pop("validated_bundle_sha256", None)
        entry[f"{stage}_execution_status"] = "pending"
        if (question, stage) in retired:
            entry["status"] = "designed" if (question, "primary") in retired else (
                "solved" if original[question].get("primary_execution_status") == "accepted" else "designed")
    for entry in entries.values():
        for record in entry.get("solver_execution", {}).values():
            record.pop("backend", None)
            record.pop("selection_reason", None)
    candidate.setdefault("execution", {}).update(zip(POLICY_FIELDS, (target, reason)))
    framework = candidate.get("paper_framework", {})
    fragments = _mark_paper_fragments_stale(framework, set(merged["affected_questions"]))
    # Never assert a synchronized framework: this command has not rewritten it.
    if merged["affected_questions"] and not _uses_fragment_stale(framework):
        framework["sync_status"] = "stale"
    return candidate, {**merged, "retired_stages": [{"question": q, "stage": s} for q, s in sorted(retired)],
                       "unbound_inactive_stages": [{"question": q, "stage": s} for q, s in sorted(inactive)],
                       "stale_paper_fragments": fragments}


def preview_migration(project_root: str | Path, *, target_backend: str, reason: str,
                      migration_id: str | None = None) -> dict[str, Any]:
    """Read actual evidence and propose a migration. No lock, archive, recovery or write."""
    import artifact_identity
    import project_transaction as transaction
    import stage_code
    import stage_inputs
    import state_transitions
    import sync_project
    import validate_user_execution as receipts
    import validate_project_state as state_validator
    from analysis_prerequisites import primary_issues

    if not _backend(target_backend) or not _reason(reason):
        raise ValueError("migration preview requires an explicit python/matlab target and non-empty reason")
    snapshot = ProjectStateSnapshot.capture(project_root)
    root, state = snapshot.root, snapshot.payload()
    if migration_id is None:
        migration_id = hashlib.sha256(json.dumps({
            "project_root": str(root), "state_sha256": snapshot.describe()["sha256"],
            "target_backend": target_backend, "reason": reason.strip(),
        }, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:32]
    elif not re.fullmatch(r"[0-9a-f]{32}", migration_id):
        raise ValueError("migration_id must be exactly 32 lowercase hexadecimal characters")
    report = inspect_backend_declarations(state)
    report.update(status="blocked", mode="migration_preview", target_backend=target_backend, reason=reason.strip(),
                  project_root=str(root), migration_id=migration_id,
                  state_snapshot=snapshot.describe(), stages=[], issues=list(report["issues"]),
                  preview_sha256=None, state_delta=[], effects={}, expected_file_hashes={}, coverage_complete=False,
                  effects_sha256=None, history_file_hashes={},
                  remaining_write_gates=["canonical_schema_and_consumer_cutover", "semantic_and_model_approval_review",
                                         "explicit_snapshot_bound_confirmation",
                                         "archive_inventory_and_raw_copy", "framework_candidate_sync", "guarded_transaction"],
                  schema_validated=False, migration_authorized=False, write_supported=False,
                  semantic_approval_rechecked=False, archive_prepared=False,
                  evidence_recheck_protocol="historical_numeric_1.1_not_new_canonical_admission")
    if snapshot.raw is None:
        report["issues"].append("migration preview requires an existing project state")
    if report["issues"]:
        return report
    report["issues"].extend(_preview_shape_issues(state))
    if report["issues"]:
        return report
    repository = Path(__file__).resolve().parents[1]
    implementation = {name: transaction.sha256_file(repository / name) for name in _PREVIEW_SOURCES}
    output = yaml.safe_load((repository / "core/output_contract.yaml").read_text(encoding="utf-8"))
    contract = yaml.safe_load((repository / "core/state_transition_contract.yaml").read_text(encoding="utf-8"))
    history = output["backend_migration_history"]["directory"].rstrip("/")
    report_path = output["backend_migration_history"]["report_path"].replace("{migration_id}", migration_id)
    archive_directory = f"{history}/{migration_id}"
    report.update(report_path=report_path, archive_directory=archive_directory)
    read_set = {transaction.STATE_RELATIVE_PATH: snapshot.describe()["sha256"]}
    history_hashes: dict[str, str] = {}
    observed_only: list[str] = []

    def capture(relative: str, *, required: bool = True) -> Path:
        path = stage_code._relative_path(root, relative)
        transaction._guarded_path(root, relative)
        if relative == history or relative.startswith(history + "/"):
            raise ValueError(f"historical archive cannot be a current source: {relative}")
        if path.exists() and (not path.is_file() or path.stat().st_nlink != 1):
            raise ValueError(f"source must be an independent regular file: {relative}")
        digest = transaction.sha256_file(path) if path.exists() else None
        if relative in read_set and read_set[relative] != digest:
            raise ValueError(f"source changed during preview: {relative}")
        read_set[relative] = digest
        if digest is None and required:
            raise ValueError(f"declared source is missing: {relative}")
        return path

    entries = state.get("subproblems", {})
    edges = state_transitions.dependency_edges(entries)
    numeric_edges = {(edge["source"], edge["target"]) for edge in edges if edge["kind"] != "model"}
    report["dependency_edges"] = edges
    workbooks: dict[str, tuple[str, str]] = {}
    standard_workbooks: dict[str, tuple[str, str]] = {}
    # A private historical adapter only; no root/stage dual selection is persisted.
    historical_state = deepcopy(state)
    for q, entry in entries.items():
        # SHA-256 hex case is not a different data identity. Keep this historical
        # adapter private; the raw caller state and its snapshot remain unchanged.
        for field in ("data_hash", "validated_data_hash"):
            if _sha(entry.get(field)):
                historical_state["subproblems"][q][field] = entry[field].lower()
        if report["selected_backend"] and report["kind"] != "canonical_declarations":
            for stage in ("primary", "analysis"):
                if _has_stage_binding(entry, stage):
                    historical_state["subproblems"][q].setdefault("solver_execution", {}).setdefault(stage, {}).update(
                        backend=report["selected_backend"], selection_reason="Read-only historical evidence adapter")
        if stage_code.question_number(q) is not None:
            problem_name = stage_code.question_name(q)
            for st, suffix in (("primary", "求解结果"), ("analysis", "结果深化分析")):
                standard_workbooks[f"{problem_name}求解/{problem_name}{suffix}.xlsx"] = (q, st)
        for stage, (_, _, wbkey) in _STAGE_KEYS.items():
            value = entry.get(wbkey) or (entry.get("robustness_workbook") if stage == "analysis" else None)
            if value:
                if not isinstance(value, str) or value in workbooks:
                    report["issues"].append(f"{q}.{stage}: workbook path is malformed or shared by stages")
                else:
                    workbooks[value] = (q, stage)
    try:
        if (root / archive_directory).exists() or (root / archive_directory).is_symlink():
            raise ValueError("migration archive destination already exists; choose a new migration_id and re-preview")
        if capture(report_path, required=False).exists():
            raise ValueError("migration report destination already exists; choose a new migration_id and re-preview")
        previous_history = (state.get("execution") or {}).get("backend_migration_history") or []
        if not isinstance(previous_history, list):
            raise ValueError("previous backend migration history must be a list")
        history_issues = sync_project.backend_history_append_issues(state, state)
        if history_issues:
            raise ValueError("previous backend migration history is malformed: " + "; ".join(history_issues))
        for reference in previous_history:
            if not isinstance(reference, Mapping):
                raise ValueError("previous backend migration reference is malformed")
            archive_report = transaction.verify_history_archive(
                root, {"manifest": reference.get("manifest"), "sha256": reference.get("sha256")},
            )
            for relative, digest in archive_report["archive_hashes"].items():
                if relative in history_hashes and history_hashes[relative] != digest:
                    raise ValueError(f"previous history file has conflicting identities: {relative}")
                history_hashes[relative] = digest
            relative = reference.get("report")
            digest = reference.get("report_sha256")
            if not isinstance(relative, str) or not _sha(digest):
                raise ValueError("previous migration report reference is malformed")
            path = transaction._guarded_path(root, relative)
            if transaction.sha256_file(path) != digest.lower():
                raise ValueError(f"previous migration report changed: {relative}")
            history_hashes[relative] = digest.lower()
        framework = state.get("paper_framework", {})
        framework_path = capture(framework.get("path") or "模型论文框架.md",
                                 required=bool(framework.get("path")))
        expected_framework_hash = framework.get("sha256")
        if expected_framework_hash and (
            state_validator._sha256_text(framework_path).lower()
            != str(expected_framework_hash).lower()
        ):
            raise ValueError("paper_framework.sha256 does not match the current framework file")
        preprocessing = state.get("preprocessing", {})
        if preprocessing.get("decision") == "project_level":
            capture(preprocessing.get("workbook"))
        for question in sorted(entries):
            entry = entries[question]
            for name in ("artifact_hashes", "validated_artifact_hashes"):
                artifact_identity.normalize_artifact_hashes(entry.get(name))  # reject conflicting aliases
            if artifact_identity.entry_alias_issues(entry):
                report["issues"].append(f"{question}: active artifact aliases require explicit historical reconciliation")
            for field in ("result_quality_report", "result_analysis_report"):
                if entry.get(field):
                    capture(entry[field])
            number = stage_code.question_number(question)
            if number is None:
                report["issues"].append(f"{question}: unsupported question identity, not silently skipped")
                continue
            problem = stage_code.question_name(question)
            for stage, (codekey, hashkey, wbkey) in _STAGE_KEYS.items():
                record = entry.get("solver_execution", {}).get(stage, {})
                code = entry.get(codekey)
                workbook = entry.get(wbkey) or (entry.get("robustness_workbook") if stage == "analysis" else None)
                bound = _has_stage_binding(entry, stage)
                active = stage == "primary" or _analysis_active(entry)
                row = dict(question=question, stage=stage, active=active, action="planned" if active else "not_activated",
                           backend=None, evidence_status="not_checked", inputs=[], issues=[])
                report["stages"].append(row)
                # Observe both standard names, but never promote an orphan to an active binding.
                for name in stage_code._names(problem, stage).values():
                    relative = f"{problem}求解/{name}"
                    path = capture(relative, required=False)
                    if path.exists() and relative != code:
                        observed_only.append(relative)
                expected_wb = f"{problem}求解/{problem}{'求解结果' if stage == 'primary' else '结果深化分析'}.xlsx"
                if capture(expected_wb, required=False).exists() and expected_wb != workbook:
                    observed_only.append(expected_wb)
                if not active:
                    if bound:
                        for relative in (code, workbook):
                            if relative:
                                capture(relative, required=False)
                        row.update(action="historical_inactive", evidence_status="historical_bytes_not_qualified")
                    continue
                if not bound:
                    status = entry.get(f"{stage}_execution_status")
                    if status == "accepted":
                        raise ValueError(f"{question}.{stage}: accepted stage has no source bindings")
                    if status not in (None, "pending"):
                        raise ValueError(f"{question}.{stage}: execution stage has no source bindings")
                    row["evidence_status"] = "no_current_numerical_binding"
                    continue
                # A planned missing source has no previously delivered/validated identity.
                if (code and not capture(code, required=False).exists() and not entry.get(hashkey) and not workbook
                        and not record.get("bundle_sha256") and entry.get(f"{stage}_execution_status") in (None, "pending")):
                    row["evidence_status"] = "planned_source_not_delivered"
                    continue
                path = capture(code)
                identity = stage_code.script_identity(path)
                if identity.stage != stage or identity.problem_name != problem:
                    raise ValueError(f"{question}.{stage}: registered source identity is inconsistent")
                _, config = stage_code.parse_stage_config(path, identity.backend)
                row["backend"] = identity.backend
                for field, expected in (("solver_backend", identity.backend), ("stage", stage), ("problem_name", problem)):
                    if field in config and config[field] != expected:
                        raise ValueError(f"{question}.{stage}: RUN_CONFIG.{field} conflicts with registered source identity")
                fingerprint = stage_code.stage_code_fingerprint(root, path, config.get("code_dependencies", []))
                for item in fingerprint["files"]:
                    capture(item["path"])
                    if read_set[item["path"]] != item["sha256"]:
                        raise ValueError(f"source changed during fingerprint: {item['path']}")
                # Historical evidence is never an escape from a modern source binding.
                if config.get("run_receipt_protocol_version") != "1.1.0":
                    if record.get("bundle_sha256") or record.get("validated_bundle_sha256"):
                        raise ValueError(f"{question}.{stage}: modern binding cannot downgrade to a legacy config")
                    if entry.get(hashkey) and read_set[code] != str(entry[hashkey]).lower():
                        raise ValueError(f"{question}.{stage}: historical entry digest conflicts")
                    closure_issues = stage_code.dependency_reference_issues(root, path, config)
                    if closure_issues:
                        raise ValueError(f"{question}.{stage}: legacy source inventory is unresolved: {closure_issues}")
                    for source in stage_inputs.input_files(root, config.get("data_paths")):
                        capture(source.relative_to(root).as_posix())
                    if workbook:
                        wbpath = capture(workbook)
                        rc, errors = receipts.configuration_map(wbpath)
                        errors.extend(receipts.validate_run_receipt_binding(rc, config))
                        if errors:
                            raise ValueError(f"{question}.{stage}: legacy receipt/config conflict: {errors}")
                        for name in ("artifact_hashes", "validated_artifact_hashes"):
                            saved = entry.get(name, {}).get(wbkey)
                            if saved and str(saved).lower() != read_set[workbook]:
                                raise ValueError(f"{question}.{stage}: legacy workbook digest conflicts")
                    row.update(action="rebuild_legacy", evidence_status="unqualified_legacy_requires_rebuild",
                               inputs=list(config["data_paths"]))
                    continue
                for relative in config.get("data_paths", []):
                    capture(relative)
                    source = workbooks.get(relative) or standard_workbooks.get(relative)
                    if source and relative not in workbooks:
                        row["issues"].append(f"input {relative} uses an unregistered numerical workbook")
                    if source and source[1] == "analysis" and not _analysis_active(entries[source[0]]):
                        row["issues"].append(f"input {relative} uses an inactive analysis source")
                    if source and source[0] != question:
                        if (source[0], question) not in numeric_edges:
                            row["issues"].append(f"input {relative} lacks an explicit numerical or conservative legacy dependency")
                row["inputs"] = list(config.get("data_paths", []))
                current = historical_state["subproblems"][question]
                accepted = entry.get(f"{stage}_execution_status") == "accepted"
                row["issues"].extend(stage_code.validate_stage_binding(
                    root, current, stage, require_validated=accepted,
                    project_backend=(report["selected_backend"] if report["kind"] == "canonical_declarations" else None),
                ))
                code_layer = "primary_code" if stage == "primary" else "analysis_code"
                for name in ("artifact_hashes", "validated_artifact_hashes"):
                    saved = entry.get(name, {}).get(code_layer)
                    if saved and str(saved).lower() != fingerprint["entry_sha256"]:
                        row["issues"].append(f"{name}.{code_layer} differs from source bytes")
                observed = stage_inputs.observe_inputs(root, config, historical_state)
                row["issues"].extend(observed["issues"])
                if str(config.get("data_sha256", "")).lower() != str(entry.get("data_hash", "")).lower():
                    row["issues"].append("RUN_CONFIG input identity disagrees with delivered project data_hash")
                layers = set(entry.get("stale_layers", []))
                relevant = {"data", "primary_code", "solution_workbook"} | (
                    {"analysis_code", "result_analysis_workbook"} if stage == "analysis" else set())
                stale = bool(layers & relevant or (entry.get("artifacts_stale") and not layers))
                if workbook:
                    wbpath = capture(workbook)
                    receipt, errors = receipts.configuration_map(wbpath)
                    row["issues"].extend(errors)
                    wb_problem, wb_stage, errors = receipts.workbook_identity(root, wbpath)
                    row["issues"].extend(errors)
                    if (wb_problem, wb_stage) != (problem, stage):
                        row["issues"].append("registered workbook identity differs from its stage")
                    row["issues"].extend(receipts.validate_run_receipt_binding(receipt, config))
                    row["issues"].extend(receipts.validate_execution_evidence(receipt, historical_state, current, stage))
                    if str(receipt.get("code_bundle_sha256", "")).lower() != fingerprint["bundle_sha256"]:
                        row["issues"].append("receipt bundle differs from current source fingerprint")
                    for name in ("artifact_hashes", "validated_artifact_hashes"):
                        saved = entry.get(name, {}).get(wbkey)
                        if saved and str(saved).lower() != read_set[workbook]:
                            row["issues"].append(f"{name}.{wbkey} differs from original workbook bytes")
                    if accepted and not stale:
                        if not entry.get("validated_artifact_hashes", {}).get(wbkey):
                            row["issues"].append("accepted workbook lacks its validated raw digest")
                        row["issues"].extend(receipts.validate_one(root, wbpath, deepcopy(historical_state), False))
                        if stage == "primary":
                            row["issues"].extend(primary_issues(root, historical_state, current))
                elif accepted:
                    row["issues"].append("accepted stage lacks a registered workbook")
                row["evidence_status"] = "accepted_rechecked" if accepted and not stale else "source_rechecked_not_accepted"
                row["action"] = "rebuild_backend" if identity.backend != target_backend else (
                    "rebuild_stale" if stale else "retain_candidate")
                if row["issues"]:
                    row.update(action="blocked", evidence_status="unverifiable")
                    report["issues"].extend(f"{question}.{stage}: {item}" for item in row["issues"])
        report["coverage_complete"] = True
        if not report["issues"]:
            candidate, effects = _retirement_candidate(state, report["stages"], target_backend, reason.strip(), contract)
            retired = {(item["question"], item["stage"]) for item in effects["retired_stages"]}
            for row in report["stages"]:
                if (row["question"], row["stage"]) in retired and not row["action"].startswith("rebuild"):
                    row["action"] = "rebuild_dependency"
            effects["dependency_cycles"] = state_transitions.dependency_cycles(entries)
            report["effects"], report["state_delta"] = effects, _state_delta(state, candidate)
        transaction._check_read_set(root, {**read_set, **history_hashes})
        snapshot.assert_current()
        if implementation != {name: transaction.sha256_file(repository / name) for name in _PREVIEW_SOURCES}:
            raise ValueError("preview implementation or contract changed while reading evidence")
    except Exception as exc:
        # File/library failures are blocking diagnostics, never successful absence or fallback.
        report["issues"].append(f"evidence_recheck_error:{type(exc).__name__}: {exc}")
    report["expected_file_hashes"] = dict(sorted(read_set.items()))
    report["history_file_hashes"] = dict(sorted(history_hashes.items()))
    report["observed_unbound_files"] = sorted(set(observed_only))
    report["implementation_hashes"] = implementation
    report["issues"] = sorted(set(report["issues"]))
    if report["issues"]:
        report["state_delta"], report["effects"] = [], {}
    else:
        report["status"] = "ready_for_review"
        try:
            report["effects_sha256"] = hashlib.sha256(json.dumps(
                report["effects"], ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                allow_nan=False).encode("utf-8")).hexdigest()
            report["preview_sha256"] = hashlib.sha256(json.dumps(
                report, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()
        except (TypeError, ValueError) as exc:
            report.update(status="blocked", state_delta=[], effects={}, issues=[f"unsupported proposal value: {exc}"])
    return report


class ProjectBackendMigrationError(ValueError):
    """A migration cannot use the proposed evidence or confirmed effects."""


def migrate_project_backend(
    project_root: str | Path, *, target_backend: str, reason: str,
    expected_generation: int, expected_state_sha256: str,
    confirmed_preview_sha256: str, confirmed_effects_sha256: str,
    confirm_migration: bool = False, migration_id: str | None = None,
    failure_hook=None,
) -> dict[str, Any]:
    """Archive original bytes, then atomically publish one confirmed project migration.

    Confirmation binds a fresh, project-specific preview and its full impact set.
    The archive is retained if a pre-commit failure occurs; a prepared transaction
    follows the existing journal's explicit roll-forward recovery semantics.
    """
    import project_transaction as transaction
    import state_transitions
    import sync_project
    import validate_model_approval as approval
    import semantic_identity
    from analysis_prerequisites import analysis_issues
    import validate_model_paper_framework as framework_validator
    import validate_project_state as state_validator

    if confirm_migration is not True:
        raise ProjectBackendMigrationError("migration needs explicit confirmation of the reviewed project and effects")
    if type(expected_generation) is not int or expected_generation < 0:
        raise ProjectBackendMigrationError("expected_generation must be a non-negative integer")
    for name, value in (("expected_state_sha256", expected_state_sha256),
                        ("confirmed_preview_sha256", confirmed_preview_sha256),
                        ("confirmed_effects_sha256", confirmed_effects_sha256)):
        if not _sha(value):
            raise ProjectBackendMigrationError(f"{name} must be a SHA-256 digest")
    report = preview_migration(project_root, target_backend=target_backend, reason=reason,
                               migration_id=migration_id)
    if report["status"] != "ready_for_review" or report["issues"] or not report["coverage_complete"]:
        raise ProjectBackendMigrationError("migration preview is blocked: " + "; ".join(report["issues"]))
    snapshot = report["state_snapshot"]
    if (snapshot["state_generation"] != expected_generation
            or snapshot["sha256"] != expected_state_sha256.lower()
            or report["preview_sha256"] != confirmed_preview_sha256.lower()
            or report["effects_sha256"] != confirmed_effects_sha256.lower()):
        raise ProjectBackendMigrationError("migration confirmation differs from current project bytes or effects; re-preview")
    if report["kind"] == "unselected":
        raise ProjectBackendMigrationError("a project without numerical history uses first-time select, not migration")
    if report["kind"] == "canonical_declarations" and report["selected_backend"] == target_backend:
        raise ProjectBackendMigrationError("same-backend reason revision belongs to select, not migration")

    root = Path(report["project_root"])
    state_snapshot = ProjectStateSnapshot.capture(root)
    state = state_snapshot.payload()
    if state_snapshot.describe() != snapshot:
        raise ProjectBackendMigrationError("project state changed after the confirmed preview")
    read_set = report["expected_file_hashes"]
    guarded_read_set = {**read_set, **report["history_file_hashes"]}
    transaction._check_read_set(root, guarded_read_set)
    repository = Path(__file__).resolve().parents[1]
    contract = yaml.safe_load((repository / "core/state_transition_contract.yaml").read_text(encoding="utf-8"))
    candidate, effects = _retirement_candidate(
        state, report["stages"], target_backend, reason.strip(), contract,
    )
    effects["dependency_cycles"] = state_transitions.dependency_cycles(state.get("subproblems", {}))
    if effects != report["effects"] or _state_delta(state, candidate) != report["state_delta"]:
        raise ProjectBackendMigrationError("migration candidate no longer equals confirmed effects")
    declaration = inspect_backend_declarations(candidate)
    if declaration["kind"] != "canonical_declarations" or declaration["issues"]:
        raise ProjectBackendMigrationError("candidate is not a single canonical project backend")

    framework = candidate.get("paper_framework")
    if not isinstance(framework, dict) or not isinstance(framework.get("path"), str):
        raise ProjectBackendMigrationError("migration requires a registered model framework")
    framework_relative = framework["path"]
    framework_path = transaction._guarded_path(root, framework_relative)
    if not framework_path.is_file() or framework_relative not in read_set:
        raise ProjectBackendMigrationError("confirmed read set lacks the registered framework")
    try:
        framework_text = framework_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ProjectBackendMigrationError("registered framework is unreadable UTF-8") from exc
    # Retention is a new current numerical binding, even when the old source is
    # delivered but has not yet produced an accepted workbook. Check approval,
    # necessity, and the actual structured semantic identity before archiving.
    retained_rows = [row for row in report["stages"] if row["action"] == "retain_candidate"]
    sections = semantic_identity.question_sections(framework_text)
    for question in sorted({row["question"] for row in retained_rows}):
        entry = candidate["subproblems"][question]
        issues = approval.validate_question(question, entry)
        if issues:
            raise ProjectBackendMigrationError("retained numerical stage lacks current Model Approval: " + "; ".join(issues))
        section = sections.get(question)
        if section is None:
            raise ProjectBackendMigrationError(f"{question}: retained numerical stage lacks its framework section")
        try:
            inspected = semantic_identity.inspect_question_semantics(section, question)
        except semantic_identity.SemanticIdentityError as exc:
            raise ProjectBackendMigrationError(f"{question}: current structured semantic identity is invalid: {exc}") from exc
        if inspected["mode"] != "semantic_identity_v1" or any(
            str(entry.get(field, "")).lower() != str(inspected[observed]).lower()
            for field, observed in (("semantic_identity_schema_version", "semantic_identity_schema_version"),
                                    ("semantic_identity_hash", "semantic_identity_hash"),
                                    ("validated_semantic_identity_hash", "semantic_identity_hash"),
                                    ("approved_semantic_identity_hash", "semantic_identity_hash"),
                                    ("semantic_text_hash", "semantic_text_hash"))
        ):
            raise ProjectBackendMigrationError(
                f"{question}: retained stage requires a current framework SIB matching validated and approved state identity"
            )
    for row in retained_rows:
        if row["stage"] != "analysis":
            continue
        entry = candidate["subproblems"][row["question"]]
        historical_workbook = (root / entry["result_analysis_workbook"]
                               if row["evidence_status"] == "accepted_rechecked" and entry.get("result_analysis_workbook")
                               else None)
        issues = analysis_issues(
            root, candidate, entry, historical_workbook=historical_workbook,
            require_project_policy=True,
        )
        if issues:
            raise ProjectBackendMigrationError(
                f"{row['question']}.analysis: retained stage lacks Analysis Necessity Gate: " + "; ".join(issues)
            )
    rendered = sync_project.render_project_backend_memory(framework_text, candidate)
    framework["sha256"] = framework_validator.sha256_text(rendered)
    archive_relative = report["archive_directory"]
    report_relative = report["report_path"]

    # The confirmed read set includes the previously absent report target. The
    # immutable archive copies all existing declared source bytes before any
    # current state or framework file can be replaced.
    archive_ref = transaction.prepare_history_archive(
        root, archive_relative, expected_generation=expected_generation,
        expected_file_hashes=read_set, failure_hook=failure_hook,
    )
    try:
        transaction.verify_history_archive(root, archive_ref)
    except Exception as exc:
        raise ProjectBackendMigrationError(
            f"migration archive verification stopped; retained archive is at {archive_relative}"
        ) from exc
    historical_refs = [
        {"manifest": item["manifest"], "sha256": item["sha256"]}
        for item in (state.get("execution") or {}).get("backend_migration_history", [])
    ]
    try:
        for reference in historical_refs:
            transaction.verify_history_archive(root, reference)
    except (OSError, ValueError, transaction.ProjectTransactionError) as exc:
        raise ProjectBackendMigrationError(
            f"previous migration archive changed; retained new archive is at {archive_relative}"
        ) from exc
    report_payload = {
        "version": "1.0.0", "status": "committed", "migration_id": report["migration_id"],
        "project_root": str(root), "base_generation": expected_generation,
        "target_generation": expected_generation + 1, "state_sha256_before": expected_state_sha256.lower(),
        "target_backend": target_backend, "selection_reason": reason.strip(),
        "confirmed_preview_sha256": confirmed_preview_sha256.lower(),
        "confirmed_effects_sha256": confirmed_effects_sha256.lower(),
        "effects": effects, "state_delta": report["state_delta"],
        "archive": archive_ref, "source_hashes_before": read_set,
        "previous_history_hashes": report["history_file_hashes"],
    }
    try:
        report_text = yaml.safe_dump(report_payload, allow_unicode=True, sort_keys=False)
    except Exception as exc:
        raise ProjectBackendMigrationError(
            f"migration report construction stopped; retained archive is at {archive_relative}"
        ) from exc
    history_ref = {
        **archive_ref, "report": report_relative,
        "report_sha256": hashlib.sha256(report_text.encode("utf-8")).hexdigest(),
    }
    previous_refs = candidate.setdefault("execution", {}).get("backend_migration_history", [])
    if not isinstance(previous_refs, list):
        raise ProjectBackendMigrationError(
            f"migration history is malformed; retained archive is at {archive_relative}"
        )
    candidate["execution"]["backend_migration_history"] = [*previous_refs, history_ref]
    history_issues = sync_project.backend_history_append_issues(state, candidate)
    if history_issues:
        raise ProjectBackendMigrationError(
            f"migration history cannot be published; retained archive is at {archive_relative}: "
            + "; ".join(history_issues)
        )

    def validate_candidate(staged: Mapping[str, Path]) -> None:
        staged_state = yaml.safe_load(staged[transaction.STATE_RELATIVE_PATH].read_text(encoding="utf-8"))
        staged_framework = staged[framework_relative]
        staged_report = staged[report_relative]
        issues = state_validator.validate_state_payload(
            staged_state, project_root=root, framework_path_override=staged_framework,
            report_path_overrides={report_relative: staged_report},
        )
        issues.extend(framework_validator.validate_framework_text(
            staged_framework.read_text(encoding="utf-8"), state=staged_state, project_root=root,
        ))
        issues.extend(sync_project.backend_history_append_issues(state, staged_state))
        if staged_state["execution"]["backend_migration_history"][-1] != history_ref:
            issues.append("staged migration history differs from the prepared archive/report reference")
        transaction.verify_history_archive(root, archive_ref)
        if issues:
            raise ProjectBackendMigrationError("candidate migration validation failed: " + "; ".join(issues))

    try:
        committed = transaction.commit_project_state(
            root, candidate, expected_generation=expected_generation,
            expected_file_hashes=guarded_read_set, preserved_archives=[archive_ref],
            historical_archives=historical_refs,
            writes_before_state=[(framework_relative, rendered)],
            writes_after_state=[(report_relative, report_text)],
            validators=[validate_candidate], failure_hook=failure_hook,
        )
    except Exception as exc:
        raise ProjectBackendMigrationError(
            f"migration commit stopped; preserved archive remains at {archive_relative}; "
            "inspect the transaction journal before retrying"
        ) from exc
    return {
        "status": committed["status"], "target_backend": target_backend,
        "state_generation": committed["target_generation"], "migration_id": report["migration_id"],
        "archive": archive_ref, "report": report_relative, "report_sha256": history_ref["report_sha256"],
        "affected_questions": effects["affected_questions"], "execution_authorized": False,
    }


def main() -> int:
    import project_transaction as transaction

    parser = argparse.ArgumentParser(description=__doc__)
    operations = parser.add_subparsers(dest="operation", required=True)
    inspect = operations.add_parser("inspect", help="read-only project diagnosis or migration preview")
    inspect.add_argument("--project-root", required=True)
    inspect.add_argument("--requested-backend", choices=["auto", "python", "matlab"])
    inspect.add_argument("--migration-target", choices=["python", "matlab"], help="read-only evidence/retirement proposal")
    inspect.add_argument("--reason", help="reason bound to an explicit migration preview")
    inspect.add_argument("--migration-id", help="32 lowercase hex; choose a new ID after an orphaned archive")
    select = operations.add_parser("select", help="commit a first project backend or revise its reason")
    select.add_argument("--project-root", required=True)
    select.add_argument("--backend", choices=["python", "matlab"], required=True)
    select.add_argument("--reason", required=True)
    select.add_argument("--expected-generation", type=int, required=True)
    migrate = operations.add_parser("migrate", help="commit a separately confirmed project migration")
    migrate.add_argument("--project-root", required=True)
    migrate.add_argument("--target-backend", choices=["python", "matlab"], required=True)
    migrate.add_argument("--reason", required=True)
    migrate.add_argument("--expected-generation", type=int, required=True)
    migrate.add_argument("--expected-state-sha256", required=True)
    migrate.add_argument("--confirmed-preview-sha256", required=True)
    migrate.add_argument("--confirmed-effects-sha256", required=True)
    migrate.add_argument("--confirm-migration", action="store_true", required=True)
    migrate.add_argument("--migration-id", help="ID shown in the confirmed preview")
    args = parser.parse_args()
    if args.operation == "inspect" and args.migration_target:
        if args.requested_backend is not None or not _reason(args.reason):
            parser.error("--migration-target requires --reason and cannot be combined with --requested-backend")
    elif args.operation == "inspect" and (args.reason is not None or args.migration_id is not None):
        parser.error("--reason/--migration-id require --migration-target")
    try:
        if args.operation == "inspect":
            report = (preview_migration(
                args.project_root, target_backend=args.migration_target, reason=args.reason,
                migration_id=args.migration_id,
            ) if args.migration_target else inspect_project(
                args.project_root, requested_backend=args.requested_backend,
            ))
        elif args.operation == "select":
            report = select_project_backend(
                args.project_root, backend=args.backend, reason=args.reason,
                expected_generation=args.expected_generation,
            )
        else:
            report = migrate_project_backend(
                args.project_root, target_backend=args.target_backend, reason=args.reason,
                expected_generation=args.expected_generation,
                expected_state_sha256=args.expected_state_sha256,
                confirmed_preview_sha256=args.confirmed_preview_sha256,
                confirmed_effects_sha256=args.confirmed_effects_sha256,
                confirm_migration=args.confirm_migration, migration_id=args.migration_id,
            )
    except (ProjectStateReadError, ProjectBackendSelectionError, ProjectBackendMigrationError,
            transaction.ProjectTransactionError, OSError) as exc:
        report = {"status": exc.code if isinstance(exc, ProjectStateReadError) else "blocked",
                  "issues": [str(exc)], "execution_authorized": False}
        if isinstance(exc, transaction.HistoryArchiveError):
            report.update(archive_relative=exc.archive_relative,
                          cleanup_status=exc.cleanup_status,
                          state_commit_performed=exc.state_commit_performed)
        print(yaml.safe_dump(report, allow_unicode=True, sort_keys=False))
        return 2
    print(yaml.safe_dump(report, allow_unicode=True, sort_keys=False))
    return 2 if report.get("issues") else 0


if __name__ == "__main__":
    raise SystemExit(main())
