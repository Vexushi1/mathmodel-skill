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

import stage_inputs as STAGE_INPUTS
import state_transitions as TRANSITIONS
from runtime_assurance import ProjectStateSnapshot, hydrate_project_context
from semantic_identity import read_framework_semantic_evidence

KINDS = frozenset({"model", "result", "parameter", "data"})


def _observed(root: Path, state: Mapping[str, Any], names: set[str]) -> dict[str, str]:
    """Pin current dependency files and the SIB source for the delivery transaction."""
    candidates = {"模型论文框架.md"}
    prep = state.get("preprocessing") or {}
    if isinstance(prep, Mapping) and prep.get("workbook"):
        candidates.add(str(prep["workbook"]))
    for name in names:
        entry = (state.get("subproblems") or {}).get(name, {})
        if isinstance(entry, Mapping):
            for field in ("code", "result_analysis_code", "solution_workbook",
                          "result_analysis_workbook"):
                value = entry.get(field)
                if isinstance(value, str) and value.strip():
                    candidates.add(value)
    observed: dict[str, str] = {}
    for relative in sorted(candidates):
        candidate = (root / relative).resolve()
        if not candidate.is_relative_to(root):
            raise ValueError(f"upstream evidence escapes project root: {relative}")
        if candidate.is_file():
            observed[candidate.relative_to(root).as_posix()] = STAGE_INPUTS.sha256_file(candidate)
    return observed


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
    tracked: set[str] = {question}
    checked: list[dict[str, Any]] = []
    issues: list[str] = []
    lookup: dict[str, dict[str, Any]] = {}
    framework = None

    def source(name: str) -> dict[str, Any]:
        if name not in lookup:
            lookup[name] = hydrate_project_context(root, name, state_snapshot=current)
        return lookup[name]

    def identity() -> dict[str, Any]:
        nonlocal framework
        if framework is None:
            framework, error = read_framework_semantic_evidence(root / "模型论文框架.md")
            if error:
                issues.append(f"{question}: {error}")
        return framework or {}

    pending = [question]
    while pending:
        target = pending.pop()
        if target in inspected:
            continue
        inspected.add(target)
        for edge in sorted(incoming.get(target, []), key=lambda e: (e["source"], e["kind"])):
            upstream = edge["source"]
            kind = edge["kind"]
            tracked.add(upstream)
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
                    selectors = {d.get("selector") for d in declarations if d.get("selector")}
                    param_items = [
                        p for p in (upstream_inspection.get("identity") or {}).get("parameters", [])
                        if isinstance(p, Mapping) and p.get("id") in selectors
                        and isinstance(p.get("source"), str) and p["source"].strip()
                        and isinstance(p.get("value"), (int, float))
                        and not isinstance(p.get("value"), bool)
                        and math.isfinite(p["value"])
                    ]
                    if len(selectors) != 1 or len(param_items) != 1:
                        reason = "parameter selector/value/source has no exact approved SIB provenance"
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
    observed = _observed(root, state, tracked)
    current.assert_current(root)
    return {
        "status": "failed" if issues else "passed",
        "question": question,
        "issues": list(dict.fromkeys(issues)),
        "checked_edges": checked,
        "observed_sources": {"project": observed},
    }
