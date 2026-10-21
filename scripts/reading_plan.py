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


def validate_chunk_coverage(
    expected_ranges: list[list[int] | tuple[int, int]],
    chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    """Validate returned source chunks against a planned 1-based inclusive read set.

    This pure helper validates transport completeness only. It neither fetches text nor
    establishes semantic review, approval, artifact acceptance, or delivery-gate status.
    Each chunk must carry path, selected commit, an explicit SHA-256 value (or None when
    unavailable), a separately named blob ID, its inclusive line range, and returned text.
    """
    issues: list[str] = []
    expected_raw: list[tuple[int, int]] = []
    for index, interval in enumerate(expected_ranges):
        if (not isinstance(interval, (list, tuple)) or len(interval) != 2
                or any(not isinstance(value, int) or isinstance(value, bool) for value in interval)):
            issues.append(f"invalid expected range at index {index}")
            continue
        start, end = interval
        if start < 1 or end < start:
            issues.append(f"invalid expected range at index {index}: {start}-{end}")
            continue
        expected_raw.append((start, end))
    if not expected_raw:
        return {
            "complete": False,
            "missing_ranges": [],
            "issues": issues + ["no valid required ranges declared"],
        }

    expected = [
        (start + 1, end)
        for start, end in _merge_ranges([(start - 1, end) for start, end in expected_raw])
    ]
    normalized_chunks: list[tuple[int, int, int, dict[str, Any]]] = []
    identities: set[tuple[Any, ...]] = set()
    required_fields = {
        "path", "source_commit", "source_sha256", "source_blob_sha",
        "start_line", "end_line", "text",
    }
    for index, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            issues.append(f"chunk {index} is not a mapping")
            continue
        missing_fields = sorted(required_fields - set(chunk))
        if missing_fields:
            issues.append(f"chunk {index} missing fields: {', '.join(missing_fields)}")
            continue
        start, end = chunk["start_line"], chunk["end_line"]
        if (not isinstance(start, int) or isinstance(start, bool)
                or not isinstance(end, int) or isinstance(end, bool)
                or start < 1 or end < start):
            issues.append(f"chunk {index} has an invalid line range")
            continue
        if not isinstance(chunk["text"], str):
            issues.append(f"chunk {index} text is not a string")
            continue
        if not isinstance(chunk["path"], str) or not chunk["path"]:
            issues.append(f"chunk {index} has no source path")
        if not isinstance(chunk["source_commit"], str) or not chunk["source_commit"]:
            issues.append(f"chunk {index} has no selected commit")
        source_sha256 = chunk["source_sha256"]
        if source_sha256 is not None and (
            not isinstance(source_sha256, str) or re.fullmatch(r"[0-9a-fA-F]{64}", source_sha256) is None
        ):
            issues.append(f"chunk {index} has an invalid source SHA-256; blob IDs are not substitutes")
        if chunk["source_blob_sha"] is not None and not isinstance(chunk["source_blob_sha"], str):
            issues.append(f"chunk {index} has an invalid blob ID")
        actual_lines = len(chunk["text"].splitlines())
        expected_lines = end - start + 1
        if actual_lines != expected_lines:
            issues.append(
                f"chunk {index} line count mismatch for {start}-{end}: "
                f"expected {expected_lines}, received {actual_lines}"
            )
        identities.add((
            chunk["path"], chunk["source_commit"], source_sha256, chunk["source_blob_sha"],
        ))
        normalized_chunks.append((start, end, index, chunk))

    if len(identities) > 1:
        issues.append("source identity differs across chunks")
    for start, end, index, _ in normalized_chunks:
        if not any(left <= start and end <= right for left, right in expected):
            issues.append(f"chunk {index} range {start}-{end} is outside the required ranges")

    missing_ranges: list[list[int]] = []
    for required_start, required_end in expected:
        covered = sorted(
            (start, end, index)
            for start, end, index, _ in normalized_chunks
            if required_start <= start and end <= required_end
        )
        cursor = required_start
        for start, end, index in covered:
            if start < cursor:
                issues.append(f"overlapping chunk range at {start}-{end}")
                cursor = max(cursor, end + 1)
            elif start > cursor:
                missing_ranges.append([cursor, start - 1])
                cursor = end + 1
            else:
                cursor = end + 1
        if cursor <= required_end:
            missing_ranges.append([cursor, required_end])

    missing_ranges = [
        [start + 1, end]
        for start, end in _merge_ranges([(start - 1, end) for start, end in missing_ranges])
    ]
    return {
        "complete": bool(normalized_chunks) and not missing_ranges and not issues,
        "missing_ranges": missing_ranges,
        "issues": issues,
    }


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
        # The target was not pushed above. Discard its preceding siblings and
        # their descendants before retaining only true ancestor introductions.
        while stack and stack[-1][1] >= level:
            stack.pop()
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
        self._review_source_declaration: tuple[dict[str, Any] | None, dict[str, str] | None] | None = None

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


REVIEW_SOURCE_MANIFEST = "core/module_manifest.yaml"


def _review_declaration(
    reader: SourceReader, manifest: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, str] | None]:
    """Read the sole review-source declaration from captured repository bytes.

    Old isolated roots remain readable. Once bootstrap registers modular review
    sources, removing their declaration is a configuration error, not permission
    to read only the compatibility entry file.
    """
    if reader.origin != "skill":
        return None, None
    if reader._review_source_declaration is None:
        path = reader.root / REVIEW_SOURCE_MANIFEST
        payload: dict[str, Any] = {}
        binding = None
        if path.is_file():
            row = reader.describe({"path": REVIEW_SOURCE_MANIFEST})
            payload = yaml.safe_load(reader.cache[REVIEW_SOURCE_MANIFEST][0].decode("utf-8")) or {}
            if not isinstance(payload, dict):
                raise ValueError("review reading manifest must be a mapping")
            binding = {"path": REVIEW_SOURCE_MANIFEST, "sha256": row["sha256"]}
        modules = payload.get("modules") or {}
        if not isinstance(modules, dict):
            raise ValueError("review manifest modules must be a mapping")
        module = modules.get("review_delivery") or {}
        if not isinstance(module, dict):
            raise ValueError("review module declaration must be a mapping")
        declaration = module.get("reading_sources")
        if declaration is None:
            bootstrap = reader.root / "core/bootstrap.yaml"
            registered = {}
            if bootstrap.is_file():
                bootstrap_payload = yaml.safe_load(bootstrap.read_bytes().decode("utf-8")) or {}
                if not isinstance(bootstrap_payload, dict):
                    raise ValueError("bootstrap must be a mapping")
                registered = bootstrap_payload.get("authoritative_sources") or {}
                if not isinstance(registered, dict):
                    raise ValueError("bootstrap authoritative_sources must be a mapping")
            if registered.get("review_content") or registered.get("review_final"):
                raise ValueError("registered review sources have no reading_sources declaration")
            reader._review_source_declaration = None, None
        else:
            if not isinstance(declaration, dict):
                raise ValueError("review reading_sources must be a mapping")
            roles = {role: declaration.get(role) for role in ("entry", "content", "final")}
            if any(not isinstance(value, str) or not value for value in roles.values()):
                raise ValueError("review reading_sources must declare entry, content and final")
            if len(set(roles.values())) != len(roles):
                raise ValueError("review source roles must not alias or cycle")
            if module.get("path") != roles["entry"]:
                raise ValueError("review entry does not match its module path")
            resolved_sources = []
            for value in roles.values():
                if Path(value).suffix.lower() != ".md":
                    raise ValueError("review sources must be Markdown files")
                resolved_sources.append(_inside(reader.root, value))
            if len(set(resolved_sources)) != len(resolved_sources) or any(
                left.samefile(right)
                for index, left in enumerate(resolved_sources)
                for right in resolved_sources[index + 1:]
            ):
                raise ValueError("review source roles resolve to the same file or cycle")
            stages = declaration.get("stages")
            if not isinstance(stages, dict) or not stages:
                raise ValueError("review reading_sources must declare its consumer stages")
            for identifier, stage_roles in stages.items():
                if (not isinstance(identifier, str) or not identifier or not isinstance(stage_roles, list)
                        or not stage_roles or any(not isinstance(role, str) for role in stage_roles)
                        or stage_roles[0] != "entry"
                        or len(stage_roles) != len(set(stage_roles))
                        or any(role not in roles for role in stage_roles)):
                    raise ValueError("invalid review stage source roles")
            entry_headings = declaration.get("entry_headings")
            if (not isinstance(entry_headings, list) or not entry_headings
                    or any(not isinstance(heading, str) or not heading for heading in entry_headings)):
                raise ValueError("review entry boundaries must be explicitly declared")
            reader._review_source_declaration = deepcopy(declaration), binding
    declaration, binding = reader._review_source_declaration
    if manifest is not None:
        supplied = (((manifest.get("modules") or {}).get("review_delivery") or {}).get("reading_sources"))
        if supplied != declaration:
            raise ValueError("review source declaration differs from captured manifest bytes")
    return declaration, binding


def canonical_rolepaths(
    root: Path, *, manifest: dict[str, Any] | None = None,
) -> dict[str, str] | None:
    """Return declared source roles for diagnostics, never a second workflow."""
    declaration, _ = _review_declaration(SourceReader(root), manifest)
    if declaration is None:
        return None
    return {role: declaration[role] for role in ("entry", "content", "final")}


def validate_review_rows(root: Path, rows: list[dict[str, Any]]) -> dict[str, str] | None:
    """Reject an old/incomplete plan rather than inventing new leaf identities.

    The returned manifest identity must also be checked against the selected
    commit by a body-text consumer. This checks source-plan closure only.
    """
    bound = [row for row in rows
             if "reading_source_manifest" in row or "review_source_closure" in row]
    if any(row.get("origin", "skill") != "skill" for row in bound):
        raise ValueError("review source binding cannot be transferred to a project source")
    declaration, binding = _review_declaration(SourceReader(root))
    if declaration is None:
        if bound:
            raise ValueError("bound review reading plan lost its source declaration; rerun resolver")
        return None
    paths = {declaration[role] for role in ("entry", "content", "final")}
    skill_rows = [row for row in rows if row.get("origin", "skill") == "skill"]
    selected = {row.get("path") for row in skill_rows}
    relevant = [row for row in skill_rows
                if row.get("path") in paths or "reading_source_manifest" in row
                or "review_source_closure" in row]
    if not relevant:
        return None
    for row in relevant:
        closure = row.get("review_source_closure")
        if (row.get("reading_source_manifest") != binding or not isinstance(closure, list)
                or any(not isinstance(path, str) or path not in paths for path in closure)
                or len(closure) != len(set(closure))
                or not {declaration["entry"], declaration["content"]}.issubset(closure)
                or not set(closure).issubset(selected)
                or row["path"] not in closure
                or (row["path"] == declaration["final"] and declaration["final"] not in closure)):
            raise ValueError("review reading plan lacks its current canonical source closure; rerun resolver")
    return deepcopy(binding)


def describe_resources(
    reader: SourceReader, spec: dict[str, Any], *,
    manifest: dict[str, Any] | None = None, stage_id: str | None = None,
) -> list[dict[str, Any]]:
    """Expand the legacy review entry into actual canonical source ranges.

    ``describe`` remains the raw single-file API. Real consumption uses this
    additive projection so a compatibility heading or entry cannot replace its
    moved rules. Resource/stage definitions remain in the module manifest.
    """
    declaration, binding = _review_declaration(reader, manifest)
    path = str(spec["path"])
    if declaration is None or path not in {declaration[role] for role in ("entry", "content", "final")}:
        return [reader.describe(spec)]
    roles = {role: declaration[role] for role in ("entry", "content", "final")}
    known_stage = stage_id in declaration["stages"]
    stage_roles = declaration["stages"][stage_id] if known_stage else list(roles)
    entry_spec: dict[str, Any] = {"path": roles["entry"]}
    if known_stage:
        entry_spec["headings"] = list(declaration["entry_headings"])
    if spec.get("when") is not None:
        entry_spec["when"] = spec["when"]
    selected: list[dict[str, Any]] = [entry_spec]
    fallback = None
    if path != roles["entry"]:
        role = next(role for role, value in roles.items() if value == path)
        if known_stage and role not in stage_roles:
            raise ValueError(f"review source {role} is outside declared stage {stage_id}")
        # A final-specific source always retains the common review context.
        if role == "final":
            selected.append({"path": roles["content"], "when": spec.get("when")})
        selected.append(deepcopy(spec))
    elif not spec.get("headings") and not spec.get("yaml_paths"):
        selected.extend({"path": roles[role], "when": spec.get("when")}
                        for role in stage_roles if role != "entry")
    else:
        requested = spec.get("headings")
        if not isinstance(requested, list) or not requested or spec.get("yaml_paths"):
            fallback = "legacy review selector cannot be mapped uniquely"
        else:
            for heading in requested:
                found: list[tuple[str, str]] = []
                for role in ("content", "final"):
                    reader.describe({"path": roles[role]})
                    for _, _, actual in _headings(reader.cache[roles[role]][1]):
                        if actual == heading:
                            found.append((role, actual))
                if len(found) > 1:
                    raise ValueError(f"ambiguous canonical review heading: {heading}")
                if not found:
                    # This includes retained entry headings and unknown legacy
                    # aliases. Conservatively return the complete real closure.
                    fallback = f"legacy review heading requires complete source closure: {heading}"
                    break
                role, actual = found[0]
                if known_stage and role not in stage_roles:
                    raise ValueError(f"review heading is outside declared stage {stage_id}: {heading}")
                if role == "final":
                    selected.append({"path": roles["content"], "when": spec.get("when")})
                selected.append({"path": roles[role], "headings": [actual], "when": spec.get("when")})
        if fallback:
            selected = [{"path": roles[role], "when": spec.get("when")} for role in stage_roles]
    rows = reader.consolidate([reader.describe(item) for item in selected])
    # An invalid declared entry boundary must not degrade into a stub-only read.
    if known_stage and rows[0]["resolution"] != "exact":
        raise ValueError(f"review entry boundary is unavailable: {rows[0]['fallback_reason']}")
    closure = [row["path"] for row in rows]
    for row in rows:
        row["reading_source_manifest"] = deepcopy(binding)
        row["review_source_closure"] = list(closure)
        if fallback:
            row["resolution"] = "whole_file_fallback"
            row["fallback_reason"] = fallback
    return rows


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
    if intent in {"project_sync", "returned_workbook_validation", "case_memory_retrieve"}:
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


def _project_backend_navigation(
    plan: dict[str, Any], policy: dict[str, Any], reader: SourceReader,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Expose the policy anchor and project CLI without authorizing an operation."""
    backend = (plan.get("runtime_plan") or {}).get("solver_backend")
    navigation = policy.get("project_backend_navigation")
    if not isinstance(backend, dict):
        return None, None
    if not isinstance(navigation, dict) or not isinstance(navigation.get("authority_read"), dict):
        raise ValueError("project backend reading navigation is missing")
    decision_intents = navigation.get("decision_intents")
    if not isinstance(decision_intents, list) or not decision_intents or not all(
        isinstance(value, str) for value in decision_intents
    ):
        raise ValueError("project backend decision intents are missing")
    if not set(plan.get("intents", [])).intersection(decision_intents):
        return None, None
    authority = deepcopy(navigation["authority_read"])
    if backend.get("scope") != "project" or (backend.get("selection_complete") and not backend.get("conflicts")):
        return authority, None
    interface = deepcopy(navigation.get("interface"))
    if (not isinstance(interface, dict) or not isinstance(interface.get("path"), str)
            or interface.get("operations") != ["inspect", "select", "migrate"]):
        raise ValueError("project backend CLI navigation is missing")
    interface["source_sha256"] = reader.describe({"path": interface["path"]})["sha256"]
    interface["authority"] = reader.describe(authority)
    interface["condition"] = navigation.get("condition")
    interface["source"] = "reading_policy.project_backend_navigation"
    interface["execute"] = False
    interface["pre_delivery_gate"] = False
    interface["boundary"] = navigation.get("boundary")
    return authority, interface


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
    if policy and policy.get("schema_version") != "1.1.0":
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

    backend_authority, backend_interface = _project_backend_navigation(plan, policy, reader)
    if profile == "full":
        specs = [{"path": path} for path in plan["load_order"]]
        if (backend_authority is not None and plan["assurance"]["status"] == "pass"
                and plan.get("intents") in (["model_selection"], ["advanced_method"])):
            # These design-only routes need the project choice, while their legacy
            # load_order remains the complete compatibility resource inventory.
            specs = [deepcopy(backend_authority) if spec["path"] == backend_authority["path"]
                     else spec for spec in specs]
    elif profile == "progressive_writing":
        # Existing writing Authority owns stages/preflight; no parallel chapter planner.
        specs = [{"path": path} for path in plan["writing_runtime"]["initial_read_order"]]
    else:
        specs = list(config.get("read_now", []))
    specs = list(policy.get("common_reads", [])) + specs
    if backend_authority is not None:
        specs.append(backend_authority)
    # A2's consumer contract is relevant now only for explicitly scoped opt-in work.
    for path in (plan.get("conformance_integration") or {}).get("resources", []):
        specs.append({"path": path})
    read_now = reader.consolidate([
        row for spec in specs
        for row in describe_resources(reader, spec, manifest=manifest)
    ])
    deferred = []
    conditions = policy.get("deferred_conditions", {})
    for path in plan["load_order"]:
        current = next((row for row in read_now if row["path"] == path), None)
        if current and current["planned_bytes"] == current["source_bytes"]:
            continue
        when = conditions.get(path, "relevant_stage_or_scope_expansion_requires_this_resource")
        if path.startswith("scripts/"):
            when = "tool_failure_or_explicit_implementation_review_requires_source"
        deferred.extend(describe_resources(
            reader, {"path": path, "when": when}, manifest=manifest,
        ))
    deferred.extend(row for spec in config.get("conditional", [])
                    for row in describe_resources(reader, spec, manifest=manifest))
    if backend_interface is not None:
        deferred.append(reader.describe({
            "path": backend_interface["path"],
            "when": "project_backend_cli_failure_or_explicit_implementation_review",
        }))
    # Keep different conditional triggers for the same resource; never erase a trigger.
    deferred = list({(r["path"], str(r["selectors"]), r["when"]): r for r in deferred}.values())

    tools = deepcopy(plan["pre_delivery_gates"])
    route_tool = config.get("route_tool")
    if "case_memory_retrieve" in plan.get("intents", []):
        route_tool = "case_memory_retrieval"
    if route_tool and not any(tool["name"] == route_tool for tool in tools):
        tools.append({"name": route_tool, **deepcopy(manifest["utility_gates"][route_tool])})
    for tool in tools:
        tool["implementation_sha256"] = reader.describe({"path": tool["path"]})["sha256"]
        tool["interface_source"] = "resolved_pre_delivery_gates_or_existing_module_manifest"
        tool["success_policy"] = "inspect_real_exit_status_and_report_never_infer_execution_from_plan"
    legacy_inventory = reader.consolidate([reader.describe({"path": p}) for p in plan["load_order"]])
    inventory = reader.consolidate([
        row for path in plan["load_order"]
        for row in describe_resources(reader, {"path": path}, manifest=manifest)
    ])
    result = {
        "schema_version": policy.get("schema_version", "1.1.0"),
        "profile": profile, "status": status, "reasons": reasons,
        "read_now": read_now + project_rows, "conditional": deferred,
        "tool_interfaces": tools,
        "project_backend_navigation": backend_interface,
        "project_sources": deepcopy(plan["assurance"]["artifact_assurance"]["evidence"]),
        "machine_dependencies": deepcopy(plan["assurance"]["dependency_closure"]),
        "authority_fingerprint": deepcopy(plan["assurance"]["authority_fingerprint"]),
        "metrics": {
            "legacy_declared_resource_bytes": sum(row["source_bytes"] for row in legacy_inventory),
            "canonical_resource_bytes": sum(row["source_bytes"] for row in inventory),
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
