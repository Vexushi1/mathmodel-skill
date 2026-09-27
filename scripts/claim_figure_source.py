"""Read-only B2 Figure source and original approval-freshness observation.

This module reuses the live B1 accepted-workbook result and the original
per-question Figure discovery/fingerprint. It neither runs MATLAB nor approves
an image, caption, or scientific interpretation.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
from typing import Any, Mapping

import artifact_fingerprint
from claim_workbook import Workbook
from claim_values import EvidenceError
import model_code_conformance as bounded
import project_snapshot
import stage_code


MAX_BINDINGS = 8
MAX_HEADERS_PER_BINDING = 64
MAX_SCOPED_IMAGES = 128
MAX_UNIQUE_IMAGES = 512
MAX_IMAGE_BYTES = 64 * 1024 * 1024
MAX_TOTAL_IMAGE_BYTES = 256 * 1024 * 1024
MAX_UNIQUE_WORKBOOKS = 8
MAX_UNIQUE_SCRIPTS = 16
MAX_SCRIPT_BYTES = 2 * 1024 * 1024
MAX_TOTAL_SCRIPT_BYTES = 16 * 1024 * 1024
_CELL_SEPARATOR = re.compile(r"<br\s*/?>|[;；]", re.I)


def _items(cell: str) -> list[str]:
    if not isinstance(cell, str):
        raise ValueError("Figure registry cell must be text")
    items = [item.strip().strip("`").strip() for item in _CELL_SEPARATOR.split(cell)]
    if not items or any(not item for item in items):
        raise ValueError("Figure registry has an empty source item")
    if len(items) != len(set(items)):
        raise ValueError("Figure registry has duplicate source items")
    return items


def _project_path(root: Path, relative: str) -> Path:
    path = stage_code._relative_path(root, relative)
    current = root
    for part in relative.split("/"):
        current /= part
        if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
            raise ValueError("Figure source path has a link alias: " + relative)
    return path


def _required_claim_sources(state: Mapping[str, Any], fragment_id: str) -> set[str]:
    framework = state["paper_framework"]
    fragment = next(row for row in framework["paper_fragments"] if row["id"] == fragment_id)
    claims = {row["id"]: row for row in framework["claim_evidence"]["claims"]}
    derivations = {row["id"]: row for row in framework["claim_evidence"]["derivations"]}
    found: set[str] = set()
    visited: set[str] = set()

    def visit(ref: str) -> None:
        if ref.startswith("source:"):
            found.add(ref.removeprefix("source:"))
        elif ref.startswith("derivation:") and ref not in visited:
            visited.add(ref)
            node = derivations[ref.removeprefix("derivation:")]
            inputs = node["inputs"]
            children = [child for value in inputs.values()
                        for child in (value if isinstance(value, list) else [value])]
            for child in children:
                visit(child)

    for dep in fragment["depends_on"]:
        if dep.startswith("claim:"):
            claim = claims[dep.removeprefix("claim:")]
            for edge in claim["evidence"]:
                if edge["relation"] in {"supports", "qualifies"}:
                    visit(edge["ref"])
    return found


def _header_issues(book: Workbook, source: Mapping[str, Any], sheet: str,
                   required_headers: list[str]) -> list[str]:
    selector = source["selector"]
    header_row = selector["header_row"]
    if selector["sheet"] != sheet or type(header_row) is not int:
        return ["Figure source sheet differs from its B1 selector"]
    rows = book.rows(sheet)
    headers = rows.get(header_row, {})
    issues: list[str] = []
    for name in required_headers:
        columns = [col for col, cell in headers.items()
                   if cell.kind == "text" and cell.value == name]
        if len(columns) != 1:
            issues.append(f"Figure source header is absent or not unique: {sheet}/{name}")
        elif any(c1 <= columns[0] <= c2 and r1 <= header_row <= r2
                 for c1, r1, c2, r2 in book._merges[sheet]):
            issues.append(f"Figure source header is merged: {sheet}/{name}")
    return issues


def _stale_issues(entry: Mapping[str, Any], stages: set[str]) -> list[str]:
    stale = set(entry.get("stale_layers") or [])
    relevant = {"data", "primary_code", "solution_workbook", "matlab_script",
                "figure_bundle", "framework"}
    if "analysis" in stages:
        relevant.update({"analysis_code", "result_analysis_workbook", "robustness_workbook"})
    affected = sorted(stale & relevant)
    issues = ["Figure source has relevant stale layers: " + ", ".join(affected)] if affected else []
    if entry.get("artifacts_stale"):
        issues.append("Figure source has artifact stale status")
    return issues


def _audit_cache(root: Path, cache: dict | None) -> dict:
    """A caller may share this one-audit cache across declared Figures only."""
    cache = {} if cache is None else cache
    expected = str(root)
    if "root" in cache and cache["root"] != expected:
        raise ValueError("Figure source cache belongs to a different project root")
    cache.setdefault("root", expected)
    for key in ("workbooks", "scripts", "images", "discovery"):
        cache.setdefault(key, {})
    for key in ("workbook_bytes", "script_bytes", "image_bytes"):
        cache.setdefault(key, 0)
    return cache


def _cached_workbook(root: Path, relative: str, expected_sha: str,
                     observed: dict, claim_contract: dict, cache: dict) -> Workbook:
    existing = cache["workbooks"].get(relative)
    if existing is not None:
        if existing["sha256"] != expected_sha or observed["project"].get(relative) != expected_sha:
            raise EvidenceError("Figure workbook cache differs from live B1/read-set identity")
        return existing["reader"]
    limit = claim_contract["limits"]["workbook_bytes"]
    total_limit = claim_contract["limits"]["total_workbook_bytes"]
    if len(cache["workbooks"]) >= MAX_UNIQUE_WORKBOOKS:
        raise EvidenceError("Figure unique-workbook budget exceeded")
    if cache["workbook_bytes"] + _project_path(root, relative).stat().st_size > total_limit:
        raise EvidenceError("Figure aggregate workbook byte budget exceeded")
    raw = bounded._read(root, relative, limit, observed["project"])
    if cache["workbook_bytes"] + len(raw) > total_limit:
        raise EvidenceError("Figure aggregate workbook byte budget exceeded")
    actual_sha = hashlib.sha256(raw).hexdigest()
    if actual_sha != expected_sha:
        raise EvidenceError("Figure workbook bytes differ from live B1 qualification")
    reader = Workbook(raw, claim_contract)
    cache["workbooks"][relative] = {"sha256": actual_sha, "reader": reader}
    cache["workbook_bytes"] += len(raw)
    return reader


def _cached_script(root: Path, relative: str, observed: dict, cache: dict) -> str:
    existing = cache["scripts"].get(relative)
    if existing is not None:
        if observed["project"].get(relative) != existing:
            raise EvidenceError("Figure script cache differs from the audit read set")
        return existing
    if len(cache["scripts"]) >= MAX_UNIQUE_SCRIPTS:
        raise EvidenceError("Figure unique-script budget exceeded")
    if cache["script_bytes"] + _project_path(root, relative).stat().st_size > MAX_TOTAL_SCRIPT_BYTES:
        raise EvidenceError("Figure aggregate script byte budget exceeded")
    raw = bounded._read(root, relative, MAX_SCRIPT_BYTES, observed["project"])
    if cache["script_bytes"] + len(raw) > MAX_TOTAL_SCRIPT_BYTES:
        raise EvidenceError("Figure aggregate script byte budget exceeded")
    digest = hashlib.sha256(raw).hexdigest()
    cache["scripts"][relative] = digest
    cache["script_bytes"] += len(raw)
    return digest


def _cached_image(root: Path, relative: str, observed: dict, cache: dict) -> str:
    existing = cache["images"].get(relative)
    if existing is not None:
        if observed["project"].get(relative) != existing:
            raise EvidenceError("Figure image cache differs from the audit read set")
        return existing
    if len(cache["images"]) >= MAX_UNIQUE_IMAGES:
        raise EvidenceError("Figure unique-image budget exceeded")
    if cache["image_bytes"] + _project_path(root, relative).stat().st_size > MAX_TOTAL_IMAGE_BYTES:
        raise EvidenceError("Figure aggregate image byte budget exceeded")
    raw = bounded._read(root, relative, MAX_IMAGE_BYTES, observed["project"])
    if cache["image_bytes"] + len(raw) > MAX_TOTAL_IMAGE_BYTES:
        raise EvidenceError("Figure aggregate image byte budget exceeded")
    digest = hashlib.sha256(raw).hexdigest()
    cache["images"][relative] = digest
    cache["image_bytes"] += len(raw)
    return digest


def _cached_discovery(root: Path, question: str, script: Path, script_hash: str,
                      entry: dict, cache: dict) -> tuple[list[Path], list[str]]:
    key = (question, script.relative_to(root).as_posix(), script_hash)
    existing = cache["discovery"].get(key)
    if existing is None:
        paths, issues = project_snapshot.scoped_figure_files(root, script, entry)
        relative = [path.relative_to(root).as_posix() for path in paths]
        existing = (relative, list(issues))
        cache["discovery"][key] = existing
    return [root / relative for relative in existing[0]], list(existing[1])


def inspect_source_binding(root: Path, state: dict, binding: dict,
                           registry_row: dict, b1_report: dict,
                           observed: dict, claim_contract: dict, *, cache: dict | None = None) -> dict:
    """Check declared Figure inputs against live B1 and original Figure hashes.

    ``observed`` is the parent B2 project's existing project/skill read-set.
    A caller must run ``recheck_source_discovery`` and the normal byte read-set
    recheck before returning an audit or using its result in a formal gate.
    """
    root = Path(root).resolve()
    figure_id = binding.get("figure_id")
    result = {"figure_id": figure_id, "status": "needs_review",
              "source_status": "needs_review", "approval_freshness": "not_assessed",
              "visual_and_caption_semantics": "not_assessed", "issues": [],
              "source_bindings": [], "discovery": None}
    issues: list[str] = result["issues"]
    rows = binding.get("source_bindings")
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_BINDINGS:
        issues.append("Figure source bindings are missing or exceed the bounded scope")
        result["status"] = "not_assessed" if not rows else "needs_review"
        return result
    try:
        cache = _audit_cache(root, cache)
        sources = {row["id"]: row for row in state["paper_framework"]["claim_evidence"]["sources"]}
        b1_sources = {row["id"]: row for row in b1_report["sources"]}
        allowed = _required_claim_sources(state, binding["fragment_id"])
        if b1_report.get("status") != "evidence_checked":
            issues.append("Live B1 evidence check is not current")
        expected_workbooks: set[str] = set()
        expected_headers: set[tuple[str, str]] = set()
        stages: set[str] = set()
        questions: set[str] = set()
        for row in rows:
            source_id = row["source_id"]
            sheet = row["sheet"]
            headers = row["required_headers"]
            if (not isinstance(headers, list) or not 1 <= len(headers) <= MAX_HEADERS_PER_BINDING
                    or any(not isinstance(header, str) or not header for header in headers)
                    or len(headers) != len(set(headers))):
                issues.append("Figure required headers are missing, duplicated or over budget")
                continue
            if source_id not in sources or source_id not in b1_sources:
                issues.append("Figure source ID is absent from the live B1 record/report")
                continue
            if source_id not in allowed:
                issues.append("Figure source is not linked to the bound fragment claim")
            source, checked = sources[source_id], b1_sources[source_id]
            questions.add(source["question"])
            stages.add(source["stage"])
            expected = state["subproblems"][source["question"]].get(source["artifact_role"])
            if (checked.get("source_qualification") != "verified"
                    or checked.get("selection_status") != "selected"
                    or checked.get("path") != expected
                    or checked.get("sha256") != (observed.get("project") or {}).get(expected)):
                issues.append("Figure B1 source qualification/path/hash is not current")
                continue
            if source["selector"]["sheet"] != sheet:
                issues.append("Figure source sheet differs from its B1 selector")
            reader = _cached_workbook(root, expected, checked["sha256"],
                                      observed, claim_contract, cache)
            issues.extend(_header_issues(reader, source, sheet, headers))
            expected_workbooks.add(expected)
            expected_headers.update((sheet, header) for header in headers)
            result["source_bindings"].append({"source_id": source_id, "question": source["question"],
                                              "stage": source["stage"], "workbook_path": expected,
                                              "workbook_sha256": checked["sha256"], "sheet": sheet,
                                              "required_headers": list(headers)})
        if len(questions) != 1:
            issues.append("A bounded result Figure must use one question scope")
        if not expected_workbooks:
            issues.append("Figure has no live accepted workbook source")
        if set(_items(registry_row["workbook"])) != expected_workbooks:
            issues.append("Framework source-workbook paths differ from live accepted paths")
        registry_headers: set[tuple[str, str]] = set()
        for item in _items(registry_row["worksheet_headers"]):
            sheet, slash, header = item.partition("/")
            if not slash or not sheet or not header or (sheet, header) in registry_headers:
                issues.append("Framework sheet/header entry is malformed or duplicated")
            else:
                registry_headers.add((sheet, header))
        if registry_headers != expected_headers:
            issues.append("Framework sheet/header entries differ from typed Figure sources")
        if len(questions) != 1:
            return result
        question = next(iter(questions))
        entry = state["subproblems"][question]
        freshness_ok = True
        stale_issues = _stale_issues(entry, stages)
        if stale_issues:
            freshness_ok = False
            issues.extend(stale_issues)
        script_relative = entry.get("matlab_script")
        if not isinstance(script_relative, str) or not script_relative:
            issues.append("State has no current Figure plotting script")
            return result
        if _items(registry_row["plotting_program"]) != [script_relative]:
            issues.append("Framework plotting program differs from State MATLAB script")
        script = _project_path(root, script_relative)
        if script.suffix.lower() != ".m":
            issues.append("Figure plotting program is not a MATLAB source")
            return result
        script_hash = _cached_script(root, script_relative, observed, cache)
        validated = entry.get("validated_artifact_hashes") or {}
        current = entry.get("artifact_hashes") or {}
        if validated.get("matlab_script") != script_hash:
            freshness_ok = False
            issues.append("Current MATLAB script differs from its existing validated hash")
        if current.get("matlab_script") and current["matlab_script"] != script_hash:
            freshness_ok = False
            issues.append("State MATLAB script observation differs from current bytes")
        figures, discovery_issues = _cached_discovery(
            root, question, script, script_hash, entry, cache)
        if discovery_issues:
            freshness_ok = False
        issues.extend("Figure discovery: " + item for item in discovery_issues)
        if not figures or len(figures) > MAX_SCOPED_IMAGES:
            issues.append("Figure discovery is empty or over the image-count budget")
            return result
        figure_paths: list[str] = []
        figure_entries: list[tuple[str, str]] = []
        for path in sorted(set(figures), key=lambda item: item.resolve().as_posix()):
            relative = path.relative_to(root).as_posix()
            _project_path(root, relative)
            image_sha = _cached_image(root, relative, observed, cache)
            figure_paths.append(relative)
            figure_entries.append((relative, image_sha))
        bundle_hash = artifact_fingerprint.combined_hash_from_entries(figure_entries)
        if bundle_hash != validated.get("figure_bundle"):
            freshness_ok = False
            issues.append("Current Figure bundle differs from its existing validated hash")
        if current.get("figure_bundle") and current["figure_bundle"] != bundle_hash:
            freshness_ok = False
            issues.append("State Figure bundle observation differs from current bytes")
        approved = set((state.get("artifacts") or {}).get("approved_figures") or [])
        if not set(figure_paths).issubset(approved):
            freshness_ok = False
            issues.append("Discovered Figure bundle is not fully covered by original approvals")
        if binding["image_path"] not in figure_paths:
            freshness_ok = False
            issues.append("Bound paper image is absent from current scoped Figure bundle")
        result["discovery"] = {"question": question, "script_path": script_relative,
                               "script_sha256": script_hash, "figure_paths": figure_paths,
                               "figure_bundle_sha256": bundle_hash}
        result["approval_freshness"] = "current" if freshness_ok else "not_assessed"
    except (OSError, ValueError, TypeError, KeyError, AttributeError, EvidenceError) as exc:
        issues.append("Figure source could not be assessed: " + str(exc)[:256])
    result["issues"] = sorted(set(issues))
    result["source_status"] = "current" if not result["issues"] else "needs_review"
    result["status"] = result["source_status"]
    return result


def recheck_source_discovery(root: Path, state: dict, checks: list[dict]) -> list[str]:
    """Detect additions/removals in the original scoped Figure discovery set."""
    root = Path(root).resolve()
    issues: list[str] = []
    seen: dict[tuple[str, str], tuple[list[str], list[str]]] = {}
    for check in checks:
        discovery = check.get("discovery")
        if not discovery:
            continue
        try:
            question = discovery["question"]
            script = _project_path(root, discovery["script_path"])
            key = (question, discovery["script_path"])
            if key not in seen:
                current, trouble = project_snapshot.scoped_figure_files(
                    root, script, state["subproblems"][question])
                seen[key] = ([path.relative_to(root).as_posix() for path in current], trouble)
            paths, trouble = seen[key]
            if trouble or paths != discovery["figure_paths"]:
                issues.append("Figure discovery changed during B2 audit: " + str(check.get("figure_id")))
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
            issues.append("Figure discovery recheck failed: " + str(exc)[:256])
    return issues
