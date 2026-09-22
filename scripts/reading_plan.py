"""Additive, read-only content projection for the assured runtime.

This module never changes the legacy plan, executes gates, or writes project state.
Selections name exact source ranges; they are not a record of completed reading.
"""
from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml
from yaml.nodes import MappingNode
from yaml.tokens import AliasToken

from artifact_fingerprint import combined_hash, sha256_file
from runtime_assurance import ProjectStateReadError, ProjectStateSnapshot
from project_transaction import STATE_RELATIVE_PATH


def _inside(root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute():
        raise ValueError(f"Reading resources must be relative: {relative}")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f"Reading resource escapes its root: {relative}")
    if not resolved.is_file():
        raise FileNotFoundError(resolved)
    return resolved


def _merge_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for start, end in sorted(ranges):
        if start >= end:
            continue
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return merged


def _headings(lines: list[str]) -> list[tuple[int, int, str]]:
    result = []
    fence: str | None = None
    for number, line in enumerate(lines):
        token = line.strip()
        match = re.match(r"^(`{3,}|~{3,})", token)
        if match:
            mark = match.group(1)
            if fence is None:
                fence = mark
            elif mark[0] == fence[0] and len(mark) >= len(fence) and not token[len(mark):].strip():
                fence = None
            continue
        if fence is not None:
            continue
        match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line.rstrip())
        if match:
            result.append((number, len(match.group(1)), token))
    return result


def _markdown_ranges(lines: list[str], selectors: list[str]) -> list[tuple[int, int]]:
    headings = _headings(lines)
    if not headings:
        raise LookupError("Markdown headings unavailable")
    intro_end = next((i for i, level, _ in headings if level > 1), len(lines))
    ranges = [(0, intro_end)]
    for selector in selectors:
        matches = [item for item in headings if item[2] == selector]
        if len(matches) != 1:
            raise LookupError(f"Heading not unique: {selector}")
        start, level, _ = matches[0]
        end = next((i for i, lev, _ in headings if i > start and lev <= level), len(lines))
        ranges.append((start, end))
        # Include ancestor introductory prose (applicability), not unrelated siblings.
        stack: list[tuple[int, int, str]] = []
        for item in headings:
            if item[0] >= start:
                break
            while stack and stack[-1][1] >= item[1]:
                stack.pop()
            stack.append(item)
        for ancestor, _, _ in stack:
            next_heading = next((i for i, _, _ in headings if i > ancestor), len(lines))
            ranges.append((ancestor, next_heading))
    return ranges


def _yaml_ranges(text: str, selectors: list[str]) -> list[tuple[int, int]]:
    if any(isinstance(token, AliasToken) for token in yaml.scan(text)):
        raise LookupError("YAML aliases require whole-file applicability context")
    root = yaml.compose(text, Loader=yaml.SafeLoader)
    ranges: list[tuple[int, int]] = []
    for selector in selectors:
        current = root
        for part in selector.split("."):
            if not isinstance(current, MappingNode):
                raise LookupError(f"Not a mapping: {selector}")
            keys = [key.value for key, _ in current.value]
            if len(keys) != len(set(keys)):
                raise LookupError(f"Duplicate YAML mapping keys: {selector}")
            candidates = [(key, value) for key, value in current.value if key.value == part]
            if len(candidates) != 1:
                raise LookupError(f"YAML path not unique: {selector}")
            key, current = candidates[0]
            ranges.append((key.start_mark.line, key.start_mark.line + 1))
        end_line, end_column = current.end_mark.line, current.end_mark.column
        source_lines = text.splitlines(keepends=True)
        prefix = source_lines[end_line][:end_column] if end_line < len(source_lines) else ""
        stop = end_line + (1 if prefix.strip() else 0)
        ranges.append((key.start_mark.line, max(key.start_mark.line + 1, stop)))
    return ranges


class SourceReader:
    """Cache one immutable source read per build and count UTF-8 bytes of range unions."""

    def __init__(self, root: Path, origin: str = "skill") -> None:
        self.root = root.resolve()
        self.origin = origin
        self.cache: dict[str, tuple[bytes, list[str]]] = {}

    def seed(self, path: str, raw: bytes) -> None:
        """Use already captured bytes, retaining the normal relative-path boundary."""
        _inside(self.root, path)
        value = raw, raw.decode("utf-8").splitlines(keepends=True)
        if path in self.cache and self.cache[path] != value:
            raise ValueError(f"Conflicting captured reading source: {path}")
        self.cache[path] = value

    def describe(self, spec: dict[str, Any]) -> dict[str, Any]:
        path = str(spec["path"])
        if path not in self.cache:
            raw = _inside(self.root, path).read_bytes()
            self.cache[path] = raw, raw.decode("utf-8").splitlines(keepends=True)
        raw, lines = self.cache[path]
        selectors = {key: list(spec[key]) for key in ("headings", "yaml_paths") if key in spec}
        fallback = None
        try:
            if len(selectors) > 1 or any(not values for values in selectors.values()):
                raise LookupError("Ambiguous/empty selector declaration")
            if "headings" in selectors:
                ranges = _markdown_ranges(lines, selectors["headings"])
            elif "yaml_paths" in selectors:
                ranges = _yaml_ranges("".join(lines), selectors["yaml_paths"])
            else:
                ranges = [(0, len(lines))]
        except (LookupError, yaml.YAMLError) as exc:
            ranges, fallback = [(0, len(lines))], str(exc)
        ranges = _merge_ranges(ranges)
        return {
            "path": path, "origin": self.origin, "sha256": hashlib.sha256(raw).hexdigest(),
            "selectors": selectors, "ranges": [[a + 1, b] for a, b in ranges],
            "source_bytes": len(raw),
            "planned_bytes": sum(len("".join(lines[a:b]).encode("utf-8")) for a, b in ranges),
            "resolution": "whole_file_fallback" if fallback else "exact",
            "fallback_reason": fallback, "when": spec.get("when"),
        }

    def consolidate(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, dict[str, Any]] = {}
        for row in rows:
            path = row["path"]
            if path not in grouped:
                grouped[path] = deepcopy(row)
                continue
            item = grouped[path]
            ranges = _merge_ranges([(a - 1, b) for a, b in item["ranges"] + row["ranges"]])
            item["ranges"] = [[a + 1, b] for a, b in ranges]
            lines = self.cache[path][1]
            item["planned_bytes"] = sum(len("".join(lines[a:b]).encode("utf-8")) for a, b in ranges)
            for key, values in row["selectors"].items():
                item["selectors"][key] = list(dict.fromkeys(item["selectors"].get(key, []) + values))
            if row["fallback_reason"]:
                item["resolution"], item["fallback_reason"] = "whole_file_fallback", row["fallback_reason"]
        return list(grouped.values())


def _current_project(
    plan: dict[str, Any], state_snapshot: ProjectStateSnapshot | None,
) -> tuple[Path | None, dict[str, Any], list[str]]:
    assurance = plan["assurance"]
    context = assurance["context"]
    if not context.get("project_state_loaded") or not context.get("question"):
        return None, {}, ["current scoped project evidence required"]
    root = Path(context["project_root"]).resolve()
    if state_snapshot is None:
        return root, {}, ["hydration snapshot unavailable; rerun resolve_runtime for a current narrow read"]
    state_snapshot.assert_current(root)
    try:
        state = state_snapshot.payload()
        framework = _inside(root, "模型论文框架.md")
        record = state.get("paper_framework") or {}
        if record.get("sync_status") != "current" or record.get("sha256") != sha256_file(framework):
            return root, state, ["framework current status/hash is missing or changed"]
        question = state["subproblems"][context["question"]]
        if question.get("artifacts_stale") or question.get("stale_layers"):
            return root, state, ["scoped project has stale artifacts"]
        # A narrow read needs an explicit, current dependency scope; uncertainty widens it.
        from runtime_assurance import hydrate_project_context

        pending, visited = [context["question"]], {context["question"]}
        while pending:
            current = state["subproblems"][pending.pop()]
            for dependency in current.get("depends_on", []):
                target = dependency.get("question")
                if dependency.get("kind") not in {"data", "parameter", "model", "result"}:
                    return root, state, ["dependency kind is missing or unsupported"]
                if target not in state["subproblems"]:
                    return root, state, ["dependency question is missing"]
                item = state["subproblems"][target]
                if item.get("artifacts_stale") or item.get("stale_layers"):
                    return root, state, ["a dependency has stale artifacts"]
                hydrated = hydrate_project_context(root, target, state_snapshot=state_snapshot)
                verified = set(hydrated.get("verified_artifacts", []))
                if "locked_model_spec" not in verified:
                    return root, state, ["dependency semantics lack current verified identity"]
                if dependency["kind"] in {"data", "parameter", "result"} and "accepted_solution_workbook" not in verified:
                    return root, state, ["dependency result/source binding needs full review"]
                if target not in visited:
                    visited.add(target)
                    pending.append(target)
        return root, state, []
    except ProjectStateReadError:
        raise  # State drift is a resolver failure, not a wider-reading success.
    except (FileNotFoundError, ValueError, KeyError, TypeError, AttributeError, yaml.YAMLError) as exc:
        return root, {}, [f"project evidence cannot be used for a narrow read: {exc}"]


def _figure_binding(root: Path, state: dict[str, Any], question: str) -> list[str]:
    """Reuse the existing fingerprint algorithm and discovery scope; never mint approval."""
    from project_snapshot import scoped_figure_files

    item = state["subproblems"][question]
    hashes = item.get("validated_artifact_hashes") or {}
    try:
        root = root.resolve()
        script = _inside(root, item.get("matlab_script", ""))
        if script.suffix.lower() != ".m":
            return ["validated figure script is not a MATLAB source"]
        if hashes.get("matlab_script") != sha256_file(script):
            return ["current MATLAB script is not bound to its validated hash"]
        approved = {_inside(root, p) for p in state.get("artifacts", {}).get("approved_figures", [])}
        figures, discovery_issues = scoped_figure_files(root, script, item)
        if discovery_issues:
            return discovery_issues
        if not figures or not set(figures).issubset(approved):
            return ["scoped figure bundle is not fully present in the existing approval registry"]
        for figure in figures:
            _inside(root, str(figure.relative_to(root)))
        if hashes.get("figure_bundle") != combined_hash(figures, root):
            return ["current figure bundle is not bound to its validated hash"]
    except (FileNotFoundError, ValueError, TypeError, KeyError, AttributeError) as exc:
        return [f"approved figure binding unavailable: {exc}"]
    return []


def _scope(plan: dict[str, Any], request: str, policy: dict[str, Any]) -> tuple[str, str, list[str]]:
    intents = plan.get("intents", [])
    if len(intents) != 1 or plan["assurance"]["status"] != "pass":
        return "full", "conservative_fallback", ["mixed intents or unresolved assurance diagnostics"]
    intent = intents[0]
    if intent in {"project_sync", "returned_workbook_validation"}:
        return intent, "planned", []
    if intent == "latex" and (plan.get("writing_runtime") or {}).get("mode") == "compact":
        return "progressive_writing", "delegated", []
    signals = policy["scope_signals"]
    clean = request
    for pattern in signals["immutable_clauses"]:
        clean = re.sub(pattern, "", clean)
    semantic_risk = bool(re.search(signals["semantic_risk"], clean))
    if intent == "framework_sync":
        if semantic_risk:
            return "full", "semantic_change_or_adjudication", ["request may change mathematical semantics"]
        if re.search(signals["result_only"], request):
            return "framework_result_sync", "candidate", []
        return "full", "needs_adjudication", ["framework update scope is not explicitly limited"]
    if intent == "editable_mechanism_diagram" or (intent == "figures" and re.search(signals["mechanism"], request)):
        return "mechanism", "planned", []
    if intent == "figures":
        if re.search(signals["style_only"], request):
            if semantic_risk:
                return "full", "semantic_change_or_adjudication", ["style request also changes data/coordinate/claim semantics"]
            return "figure_style", "candidate", []
        return "figure_design", "planned", []
    return "full", "conservative_fallback", ["no narrower reading profile is defined for this operation"]


def _project_reads(
    root: Path, state: dict[str, Any], question: str, *, style: bool,
    state_snapshot: ProjectStateSnapshot,
) -> list[dict[str, Any]]:
    state_snapshot.assert_current(root)
    if state_snapshot.raw is None:
        raise ProjectStateReadError("invalid_project_state", "a narrow read requires captured state bytes")
    reader = SourceReader(root, "project")
    reader.seed(STATE_RELATIVE_PATH, state_snapshot.raw)
    text = _inside(root, "模型论文框架.md").read_text(encoding="utf-8")
    scoped = {question}
    pending = [question]
    valid_dependencies = True
    while pending:
        current = pending.pop()
        for dependency in state.get("subproblems", {}).get(current, {}).get("depends_on", []):
            target = dependency.get("question") if isinstance(dependency, dict) else None
            if not target or target not in state.get("subproblems", {}):
                valid_dependencies = False
                continue
            if target not in scoped:
                scoped.add(target)
                pending.append(target)
    headings = ["## 当前有效口径", "## 图表证据链", "## 待办与缺口"]
    known = _headings(text.splitlines(keepends=True))
    for target in sorted(scoped):
        matches = [s for _, _, s in known if re.match(r"^###\s+" + re.escape(target) + r"[：:]", s)]
        headings.append(matches[0] if len(matches) == 1 else f"missing-unique-question-{target}")
    spec: dict[str, Any] = {"path": "模型论文框架.md"}
    if valid_dependencies:
        spec["headings"] = headings
    rows = [reader.describe(spec), reader.describe({"path": "state/project_state.yaml"})]
    if style:
        rows.append(reader.describe({"path": state["subproblems"][question]["matlab_script"]}))
    return reader.consolidate(rows)


def build_reading_plan(root: Path, plan: dict[str, Any], router: dict[str, Any],
                       manifest: dict[str, Any], request: str = "", *,
                       state_snapshot: ProjectStateSnapshot | None = None) -> dict[str, Any]:
    """Return only a new sibling; never mutate fields or promote artifact evidence."""
    if state_snapshot is not None:
        state_snapshot.assert_current(plan["assurance"]["context"]["project_root"])
    policy = router.get("reading_policy") or {}
    reader = SourceReader(root)
    profile, status, reasons = (_scope(plan, request, policy) if policy else
                                ("full", "conservative_fallback", ["no reading policy declared"]))
    config = policy.get("profiles", {}).get(profile, {})
    if policy and policy.get("schema_version") != "1.0.0":
        raise ValueError("Unsupported reading_policy schema")
    if profile not in {"full", "progressive_writing"} and not config.get("read_now"):
        profile, status = "full", "conservative_fallback"
        reasons.append("reading profile is absent or has no required reads")
        config = {}
    context = plan["assurance"]["context"]
    project_root, state, project_rows = None, {}, []
    if config.get("needs_current_project"):
        project_root, state, issues = _current_project(plan, state_snapshot)
        evidence = plan["assurance"]["artifact_assurance"]["evidence"]
        for artifact in config.get("required_verified_artifacts", []):
            if artifact == "validated_results":
                primary = [
                    row for row in evidence
                    if row.get("artifact") == "accepted_solution_workbook"
                    and row.get("scope") == context.get("question")
                ]
                analysis = [
                    row for row in evidence
                    if row.get("artifact") in {"accepted_result_analysis_workbook", "result_analysis_not_required"}
                    and row.get("scope") == context.get("question")
                ]
                if (
                    not primary
                    or any(row.get("status") != "verified" for row in primary)
                    or not any(row.get("status") == "verified" for row in analysis)
                ):
                    issues.append("verified scoped artifact required: validated_results")
                continue
            scoped = [row for row in evidence if row.get("artifact") == artifact
                      and row.get("scope") == context.get("question")]
            if not scoped or any(row.get("status") != "verified" for row in scoped):
                issues.append(f"verified scoped artifact required: {artifact}")
            elif artifact != "locked_model_spec" and project_root:
                for row in scoped:
                    try:
                        if sha256_file(_inside(project_root, row["path"])) != row["actual_sha256"]:
                            issues.append(f"artifact changed after assurance: {artifact}")
                    except (FileNotFoundError, ValueError, TypeError, KeyError):
                        issues.append(f"artifact path no longer valid: {artifact}")
        if not issues and config.get("needs_approved_figure_binding"):
            issues.extend(_figure_binding(project_root, state, context["question"]))
        if issues:
            profile, status, config = "full", "evidence_required", {}
            reasons.extend(issues)
        else:
            status = "planned"
            project_rows = _project_reads(
                project_root, state, context["question"], style=profile == "figure_style",
                state_snapshot=state_snapshot,
            )

    if profile == "full":
        specs = [{"path": path} for path in plan["load_order"]]
    elif profile == "progressive_writing":
        # Existing writing Authority owns stages/preflight; no parallel chapter planner.
        specs = [{"path": path} for path in plan["writing_runtime"]["initial_read_order"]]
    else:
        specs = list(config.get("read_now", []))
    specs = list(policy.get("common_reads", [])) + specs
    read_now = reader.consolidate([reader.describe(spec) for spec in specs])
    deferred = []
    conditions = policy.get("deferred_conditions", {})
    for path in plan["load_order"]:
        current = next((row for row in read_now if row["path"] == path), None)
        if current and current["planned_bytes"] == current["source_bytes"]:
            continue
        when = conditions.get(path, "relevant_stage_or_scope_expansion_requires_this_resource")
        if path.startswith("scripts/"):
            when = "tool_failure_or_explicit_implementation_review_requires_source"
        deferred.append(reader.describe({"path": path, "when": when}))
    deferred.extend(reader.describe(spec) for spec in config.get("conditional", []))
    # Keep different conditional triggers for the same resource; never erase a trigger.
    deferred = list({(r["path"], str(r["selectors"]), r["when"]): r for r in deferred}.values())

    tools = deepcopy(plan["pre_delivery_gates"])
    route_tool = config.get("route_tool")
    if route_tool and not any(tool["name"] == route_tool for tool in tools):
        tools.append({"name": route_tool, **deepcopy(manifest["utility_gates"][route_tool])})
    for tool in tools:
        tool["implementation_sha256"] = reader.describe({"path": tool["path"]})["sha256"]
        tool["interface_source"] = "resolved_pre_delivery_gates_or_existing_module_manifest"
        tool["success_policy"] = "inspect_real_exit_status_and_report_never_infer_execution_from_plan"
    inventory = reader.consolidate([reader.describe({"path": p}) for p in plan["load_order"]])
    result = {
        "schema_version": policy.get("schema_version", "1.0.0"),
        "profile": profile, "status": status, "reasons": reasons,
        "read_now": read_now + project_rows, "conditional": deferred,
        "tool_interfaces": tools,
        "project_sources": deepcopy(plan["assurance"]["artifact_assurance"]["evidence"]),
        "machine_dependencies": deepcopy(plan["assurance"]["dependency_closure"]),
        "authority_fingerprint": deepcopy(plan["assurance"]["authority_fingerprint"]),
        "metrics": {
            "legacy_declared_resource_bytes": sum(row["source_bytes"] for row in inventory),
            "planned_skill_read_bytes": sum(row["planned_bytes"] for row in read_now),
            "planned_project_read_bytes": sum(row["planned_bytes"] for row in project_rows),
            "actual_read_tokens": None, "actual_read_bytes": None,
            "meaning": "planned_initial_read_only_not_full_task_cost_or_observed_token_savings",
        },
    }
    if profile == "progressive_writing":
        result["delegated_writing_sequence"] = deepcopy(plan["writing_runtime"])
    if state_snapshot is not None:
        state_snapshot.assert_current()
    return result
