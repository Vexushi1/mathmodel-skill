#!/usr/bin/env python3
"""File-backed typed upstream prerequisites for a single numerical code delivery.

This is not a second Model Approval, data acceptance or State Transition
authority. Current artifact qualification comes only from Runtime Assurance;
this consumer enforces declared dependencies before delivering new code.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
import hashlib
import math
from pathlib import Path
from typing import Any

import conformance_gate as CONFORMANCE
import project_transaction as PROJECT_TX
import stage_code as STAGE_CODE
import stage_inputs as STAGE_INPUTS
import state_transitions as TRANSITIONS
from runtime_assurance import ProjectStateSnapshot, hydrate_project_context
from semantic_identity import framework_semantic_evidence

KINDS = frozenset({"model", "result", "parameter", "data"})


def _capture_path(root: Path, relative: str, observed: dict[str, str | None]) -> None:
    """Pin a necessary file before qualification, without overwriting its first identity."""
    if relative in observed:
        return
    try:
        path = PROJECT_TX._guarded_path(root, relative)
        if path.is_file():
            observed[relative] = STAGE_INPUTS.sha256_file(path)
        elif not path.exists():
            observed[relative] = None  # Pin nonexistence; a newly created source is a conflict.
        else:
            raise ValueError(f"dependency source is not a regular file: {relative}")
    except PROJECT_TX.ProjectTransactionError as exc:
        raise ValueError(f"invalid dependency source path {relative!r}: {exc}") from exc


def _capture_stage_inputs(
    root: Path, relative: str, observed: dict[str, str | None],
) -> None:
    """Bind declared helper and data files of an actually needed upstream result."""
    path = PROJECT_TX._guarded_path(root, relative)
    if not path.is_file():
        return  # Existing stage-binding qualification owns missing-code diagnostics.
    try:
        _, config = STAGE_CODE.parse_stage_config(path)
    except (OSError, ValueError, SyntaxError, TypeError):
        return  # A malformed legacy/current entry is adjudicated by Runtime Assurance.
    if not isinstance(config, Mapping):
        return
    # code_dependencies use structured {path, sha256} entries, unlike
    # data_paths and auxiliary_data_paths. Pin their original bytes before
    # Runtime Assurance qualifies the source bundle; never hash them late.
    helpers = config.get("code_dependencies") or []
    if not isinstance(helpers, list):
        raise ValueError("upstream code_dependencies must be a list of path/sha256 mappings")
    for item in helpers:
        if not isinstance(item, Mapping) or not isinstance(item.get("path"), str):
            raise ValueError("upstream code_dependencies item lacks a source path")
        _capture_path(root, item["path"], observed)
    for field in ("data_paths", "auxiliary_data_paths"):
        names = config.get(field)
        if isinstance(names, list):
            for name in names:
                if isinstance(name, str) and name.strip():
                    _capture_path(root, name, observed)


def _capture_edge_sources(
    root: Path, state: Mapping[str, Any], upstream: str, kind: str,
    config: Mapping[str, Any] | None, observed: dict[str, str | None],
) -> None:
    """Capture only inputs for this typed edge; never enumerate unrelated questions."""
    entry = (state.get("subproblems") or {}).get(upstream, {})
    if kind == "result" and isinstance(entry, Mapping):
        stages = [("code", "solution_workbook")]
        if entry.get("result_analysis_status") == "passed":
            stages.append(("result_analysis_code", "result_analysis_workbook"))
        for code_field, workbook_field in stages:
            code, workbook = entry.get(code_field), entry.get(workbook_field)
            if isinstance(code, str) and code.strip():
                _capture_path(root, code, observed)
                _capture_stage_inputs(root, code, observed)
            if isinstance(workbook, str) and workbook.strip():
                _capture_path(root, workbook, observed)
        prep = state.get("preprocessing") or {}
        if isinstance(prep, Mapping) and prep.get("decision") == "project_level":
            workbook = prep.get("workbook")
            if isinstance(workbook, str) and workbook.strip():
                _capture_path(root, workbook, observed)
    elif kind == "data":
        prep = state.get("preprocessing") or {}
        if isinstance(prep, Mapping) and prep.get("decision") == "project_level":
            workbook = prep.get("workbook")
            if isinstance(workbook, str) and workbook.strip():
                _capture_path(root, workbook, observed)
        elif isinstance(config, Mapping):
            for field in ("data_paths", "auxiliary_data_paths"):
                paths = config.get(field)
                if isinstance(paths, list):
                    for path in paths:
                        if isinstance(path, str) and path.strip():
                            _capture_path(root, path, observed)


def inspect(
    project_root: Path,
    question: str,
    *,
    config: Mapping[str, Any] | None = None,
    snapshot: ProjectStateSnapshot | None = None,
) -> dict[str, Any]:
    """Report only relevant typed dependencies; never run task-specific code."""
    root = Path(project_root).resolve()
    current = snapshot if snapshot is not None else ProjectStateSnapshot.capture(root)
    current.assert_current(root)
    state = current.payload()
    entries = state.get("subproblems") or {}
    if not isinstance(entries, Mapping) or question not in entries:
        return {"status": "failed", "question": question,
                "issues": [f"{question}: missing registered question"],
                "checked_edges": [], "observed_sources": {"project": {}}}
    edges = TRANSITIONS.dependency_edges(entries)
    incoming: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        incoming[edge["target"]].append(edge)
    inspected: set[str] = set()
    checked: list[dict[str, Any]] = []
    issues: list[str] = []
    lookup: dict[str, dict[str, Any]] = {}
    observed = {"project": {}, "skill": {}}
    # Read and hash one original framework byte image, rather than hashing a
    # potentially replaced version after qualification has already passed.
    framework_path = PROJECT_TX._guarded_path(root, "模型论文框架.md")
    framework_bytes = framework_path.read_bytes() if framework_path.is_file() else None
    observed["project"]["模型论文框架.md"] = (
        hashlib.sha256(framework_bytes).hexdigest() if framework_bytes is not None else None
    )
    framework = None

    def identity() -> dict[str, Any]:
        nonlocal framework
        if framework is None:
            if framework_bytes is None:
                framework, error = {}, "current model framework is missing"
            else:
                framework, error = framework_semantic_evidence(framework_bytes.decode("utf-8"))
            if error:
                issues.append(f"{question}: {error}")
        return framework or {}

    def source(name: str) -> dict[str, Any]:
        if name not in lookup:
            qualified = hydrate_project_context(
                root, name, state_snapshot=current, include_observed_sources=True,
            )
            lookup[name] = qualified
            # This pre-existing Runtime Assurance reader already captures the
            # actual source bytes of workbooks and comparison evidence.
            for row in qualified.get("artifact_evidence", ()):
                if not isinstance(row, Mapping) or row.get("scope") not in {name, "project"}:
                    continue
                if row.get("artifact") == "locked_model_spec" and row.get("scope") == name:
                    original = identity().get(name) or {}
                    mode = original.get("mode")
                    original_semantics = original.get(
                        "semantic_identity_hash" if mode == "semantic_identity_v1"
                        else "semantic_text_hash"
                    )
                    if row.get("status") == "verified" and original_semantics != row.get("actual_sha256"):
                        issues.append(f"{name}: 模型论文框架.md changed during qualification")
                elif row.get("artifact") in {
                    "accepted_solution_workbook", "accepted_result_analysis_workbook",
                    "preprocessing_workbook",
                }:
                    path = row.get("path")
                    if path in observed["project"] and observed["project"][path] != row.get("actual_sha256"):
                        issues.append(f"{name}: {path} changed during qualification")
            try:
                CONFORMANCE.merge_read_sets(
                    observed, qualified.get("observed_sources", {"project": {}, "skill": {}}),
                )
            except ValueError as exc:
                issues.append(f"{name}: upstream source changed during qualification: {exc}")
        return lookup[name]

    pending = [question]
    while pending:
        target = pending.pop()
        if target in inspected:
            continue
        inspected.add(target)
        scoped_edges = sorted(incoming.get(target, []), key=lambda e: (e["source"], e["kind"]))
        # Capture every necessary source *before* the first cached upstream
        # assurance call. A model+result pair must not observe late result bytes.
        for edge in scoped_edges:
            if edge["source"] in entries and edge["kind"] in KINDS:
                _capture_edge_sources(
                    root, state, edge["source"], edge["kind"], config, observed["project"],
                )
        for edge in scoped_edges:
            upstream = edge["source"]
            kind = edge["kind"]
            reason = None
            if upstream not in entries:
                reason = "unregistered upstream question"
            elif kind not in KINDS:
                reason = "legacy or unknown dependency kind requires explicit reconciliation"
            elif kind == "model":
                if "locked_model_spec" not in source(upstream)["verified_artifacts"]:
                    reason = "upstream current approved model is not file-backed verified"
            # A verified model lock is the semantic prerequisite; do not require its results.
            elif kind == "result":
                if "validated_results" not in source(upstream)["verified_artifacts"]:
                    reason = "upstream validated_results is not current (including required 03B)"
            elif kind == "parameter":
                if "locked_model_spec" not in source(upstream)["verified_artifacts"]:
                    reason = "upstream approved parameter model is not current"
                else:
                    target_inspection = identity().get(target) or {}
                    upstream_inspection = identity().get(upstream) or {}
                    declarations = [
                        d for d in (target_inspection.get("identity") or {}).get("dependencies", [])
                        if d.get("question") == upstream and d.get("kind") == "parameter"
                    ]
                    selectors = [d.get("selector") for d in declarations]
                    parameters = (upstream_inspection.get("identity") or {}).get("parameters", [])
                    invalid: list[str] = []
                    if not selectors or any(not isinstance(s, str) or not s.strip() for s in selectors):
                        invalid.append("<missing selector>")
                    declared_names = [s for s in selectors if isinstance(s, str) and s.strip()]
                    if len(declared_names) != len(set(declared_names)):
                        invalid.append("<duplicate selector>")
                    for selector in sorted(set(declared_names)):
                        matches = [p for p in parameters if isinstance(p, Mapping) and p.get("id") == selector]
                        if len(matches) != 1:
                            invalid.append(selector)
                        else:
                            param = matches[0]
                            value, provenance = param.get("value"), param.get("source")
                            try:
                                finite_value = (isinstance(value, (int, float))
                                                and not isinstance(value, bool) and math.isfinite(value))
                            except (TypeError, ValueError, OverflowError):
                                finite_value = False
                            if (not isinstance(provenance, str) or not provenance.strip()
                                    or not finite_value):
                                invalid.append(selector)
                    if invalid:
                        reason = (
                            "parameter selector/value/source has no exact approved SIB provenance: "
                            + ", ".join(dict.fromkeys(invalid))
                        )
            elif kind == "data":
                preprocessing = state.get("preprocessing") or {}
                if preprocessing.get("decision") == "project_level":
                    current_preprocessing = source(upstream)["verified_artifacts"]
                    if "preprocessing_workbook" not in current_preprocessing:
                        reason = "shared project preprocessing workbook is not accepted/current"
                    elif not isinstance(config, Mapping) or (
                        config.get("data_identity_mode") != "preprocessing_workbook"
                    ):
                        reason = "downstream must bind accepted project-level preprocessing workbook"
                    else:
                        configured = config.get("data_paths")
                        workbook = preprocessing.get("workbook") or "数据预处理/数据预处理结果.xlsx"
                        if not isinstance(configured, list) or configured != [workbook]:
                            reason = "downstream data_paths does not bind the accepted preprocessing workbook"
                else:
                    entry = entries[upstream]
                    declared = entry.get("data_hash") or entry.get("validated_data_hash")
                    configured = (config or {}).get("data_paths")
                    source_rows = (state.get("data") or {}).get("sources") or []
                    if (not isinstance(configured, list) or not isinstance(declared, str)
                            or declared.lower() != str((config or {}).get("data_sha256", "")).lower()):
                        reason = "raw upstream data identity is not bound to downstream input"
                    else:
                        raw = {str(row.get("path")): row for row in source_rows
                               if isinstance(row, Mapping) and row.get("sha256")}
                        if not configured or any(path not in raw for path in configured):
                            reason = "raw upstream data paths lack registered source provenance"
                        else:
                            for relative in configured:
                                source_path = (root / relative).resolve()
                                if (not source_path.is_relative_to(root) or not source_path.is_file()
                                        or STAGE_INPUTS.sha256_file(source_path) != raw[relative]["sha256"]):
                                    reason = "registered raw data source changed or is unavailable"
                                    break
            checked.append({"question": target, "upstream": upstream, "kind": kind,
                            "status": "blocked" if reason else "verified",
                            **({"reason": reason} if reason else {})})
            if reason:
                issues.append(f"{target}: {upstream}/{kind}: {reason}")
                # Follow only unresolved inputs. Once a source is verified,
                # unrelated prerequisites of that source are not reactivated.
                pending.append(upstream)

    necessary_graph: dict[str, dict[str, Any]] = {
        name: {"depends_on": [
            {"question": row["upstream"], "kind": row["kind"]}
            for row in checked if row["question"] == name and row["status"] == "blocked"
            and row["upstream"] in entries
        ]}
        for name in inspected
    }
    cycles = TRANSITIONS.dependency_cycles(necessary_graph)
    for cycle in cycles:
        issues.append(f"{question}: unresolved dependency cycle requires joint-model review: {cycle}")
    try:
        CONFORMANCE.assert_observed(root, observed)
    except (PROJECT_TX.ProjectTransactionError, ValueError, OSError) as exc:
        issues.append(f"{question}: upstream source changed during qualification: {exc}")
    current.assert_current(root)
    return {
        "status": "failed" if issues else "passed",
        "question": question,
        "issues": list(dict.fromkeys(issues)),
        "checked_edges": checked,
        "observed_sources": observed,
    }
