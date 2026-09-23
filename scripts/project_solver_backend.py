#!/usr/bin/env python3
"""Read-only project-backend preflight for explicit v10 selection or migration.

This inspector classifies declarations, not complete Schema/receipt validity. It
neither selects a backend nor grants execution eligibility. A preview does not
modify the current project or authorize use of historical numerical artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
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
    from sync_project import _mark_paper_fragments_stale

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
    if merged["affected_questions"] and not framework.get("paper_fragments"):
        framework["sync_status"] = "stale"
    return candidate, {**merged, "retired_stages": [{"question": q, "stage": s} for q, s in sorted(retired)],
                       "unbound_inactive_stages": [{"question": q, "stage": s} for q, s in sorted(inactive)],
                       "stale_paper_fragments": fragments}


def preview_migration(project_root: str | Path, *, target_backend: str, reason: str) -> dict[str, Any]:
    """Read actual evidence and propose a migration. No lock, archive, recovery or write."""
    import artifact_identity
    import project_transaction as transaction
    import stage_code
    import stage_inputs
    import state_transitions
    import validate_user_execution as receipts
    from analysis_prerequisites import primary_issues

    if not _backend(target_backend) or not _reason(reason):
        raise ValueError("migration preview requires an explicit python/matlab target and non-empty reason")
    snapshot = ProjectStateSnapshot.capture(project_root)
    root, state = snapshot.root, snapshot.payload()
    report = inspect_backend_declarations(state)
    report.update(status="blocked", mode="migration_preview", target_backend=target_backend, reason=reason.strip(),
                  state_snapshot=snapshot.describe(), stages=[], issues=list(report["issues"]),
                  preview_sha256=None, state_delta=[], effects={}, expected_file_hashes={}, coverage_complete=False,
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
    read_set = {transaction.STATE_RELATIVE_PATH: snapshot.describe()["sha256"]}
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
        framework = state.get("paper_framework", {})
        capture(framework.get("path") or "模型论文框架.md", required=bool(framework.get("path")))
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
        transaction._check_read_set(root, read_set)
        snapshot.assert_current()
        if implementation != {name: transaction.sha256_file(repository / name) for name in _PREVIEW_SOURCES}:
            raise ValueError("preview implementation or contract changed while reading evidence")
    except Exception as exc:
        # File/library failures are blocking diagnostics, never successful absence or fallback.
        report["issues"].append(f"evidence_recheck_error:{type(exc).__name__}: {exc}")
    report["expected_file_hashes"] = dict(sorted(read_set.items()))
    report["observed_unbound_files"] = sorted(set(observed_only))
    report["implementation_hashes"] = implementation
    report["issues"] = sorted(set(report["issues"]))
    if report["issues"]:
        report["state_delta"], report["effects"] = [], {}
    else:
        report["status"] = "ready_for_review"
        try:
            report["preview_sha256"] = hashlib.sha256(json.dumps(
                report, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()
        except (TypeError, ValueError) as exc:
            report.update(status="blocked", state_delta=[], effects={}, issues=[f"unsupported proposal value: {exc}"])
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    operations = parser.add_subparsers(dest="operation", required=True)
    inspect = operations.add_parser("inspect", help="read-only diagnostic; not selection or migration")
    inspect.add_argument("--project-root", required=True)
    inspect.add_argument("--requested-backend", choices=["auto", "python", "matlab"])
    inspect.add_argument("--migration-target", choices=["python", "matlab"], help="read-only evidence/retirement proposal")
    inspect.add_argument("--reason", help="reason bound to an explicit migration preview")
    args = parser.parse_args()
    if args.migration_target:
        if args.requested_backend is not None or not _reason(args.reason):
            parser.error("--migration-target requires --reason and cannot be combined with --requested-backend")
    elif args.reason is not None:
        parser.error("--reason requires --migration-target")
    try:
        report = (preview_migration(args.project_root, target_backend=args.migration_target, reason=args.reason)
                  if args.migration_target else inspect_project(args.project_root, requested_backend=args.requested_backend))
    except ProjectStateReadError as exc:
        report = {"diagnostic_only": True, "status": exc.code, "issues": [str(exc)],
                  "execution_authorized": False}
        print(yaml.safe_dump(report, allow_unicode=True, sort_keys=False))
        return 2
    print(yaml.safe_dump(report, allow_unicode=True, sort_keys=False))
    return 2 if report["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
