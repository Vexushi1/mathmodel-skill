#!/usr/bin/env python3
"""Return actual stage-reading source text without making any workflow decision.

The resolver and writing runtime remain the only selectors of stages, resources,
project eligibility and gates. This read-only adapter does not execute those gates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

from reading_plan import (
    SourceReader, canonical_rolepaths, describe_resources,
    validate_chunk_coverage, validate_review_rows,
)

ROOT = Path(__file__).resolve().parents[1]


def verify_checkout(root: Path, selected_commit: str) -> str:
    if not re.fullmatch(r"[0-9a-fA-F]{40}", selected_commit):
        raise ValueError("a full 40-character selected source commit is required")
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise ValueError("source checkout identity could not be verified")
    current = result.stdout.strip()
    if current.lower() != selected_commit.lower():
        raise ValueError(f"source checkout changed: selected {selected_commit}, current {current}")
    return current


def _stage(plan: dict[str, Any], stage_id: str) -> dict[str, Any]:
    writing = (plan.get("reading_plan") or {}).get("delegated_writing_sequence")
    if not isinstance(writing, dict):
        writing = plan.get("writing_runtime")
    stages = (writing or {}).get("authoring_sequence") or []
    matches = [row for row in stages if row.get("id") == stage_id]
    if len(matches) != 1:
        raise ValueError(f"stage is unavailable or ambiguous: {stage_id}")
    return matches[0]


def _selector_spec(root: Path, resource: str) -> dict[str, Any] | None:
    """Resolve an existing writing-stage source anchor, not a project-fact alias."""
    path, sep, anchor = resource.partition("#")
    path = path.strip()
    if not (path.startswith(("core/", "modules/", "templates/", "packs/", "config/"))
            and Path(path).suffix.lower() in {".md", ".yaml", ".yml", ".tex"}):
        return None
    spec: dict[str, Any] = {"path": path}
    if not sep:
        return spec
    if Path(path).suffix.lower() in {".yaml", ".yml"}:
        spec["yaml_paths"] = [anchor.replace("/", ".")]
        return spec
    if Path(path).suffix.lower() != ".md":
        return None
    # Writing-stage references include Chinese-numbered, English, v7.x and
    # decimal-numbered headings. Match the *complete* declared anchor to a
    # unique real heading, rather than assuming an ASCII numeric prefix.
    # Punctuation and whitespace are presentation-only (e.g. 三、 versus 三-;
    # v7.20/v8.0.1 versus v7.20-v8.0.1). A collision is never guessed.
    def anchor_key(value: str) -> str:
        return "".join(char.casefold() for char in value if char.isalnum())

    key = anchor_key(anchor)
    if not key:
        raise ValueError(f"empty Markdown heading anchor: {resource}")
    candidate = (root / path).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise ValueError(f"reading source escapes root: {path}")
    if not candidate.is_file():
        raise FileNotFoundError(candidate)
    lines = candidate.read_text(encoding="utf-8").splitlines()
    headings = []
    for line in lines:
        match = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if match and anchor_key(match.group(2)) == key:
            headings.append(line)
    if len(headings) != 1:
        # Fail safely into existing SourceReader whole-file fallback,
        # not into an unverified substring selection.
        spec["headings"] = [f"missing-unique-anchor-{anchor}"]
    else:
        spec["headings"] = headings
    return spec


def select_sources(
    plan: dict[str, Any], root: Path, surface: str, *,
    stage_id: str | None = None, condition: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    reading = plan.get("reading_plan") or {}
    symbolic: list[dict[str, str]] = []
    if surface in {"read_now", "conditional"}:
        if stage_id:
            raise ValueError("stage_id is only valid with the writing_stage surface")
        if surface == "conditional" and not condition:
            # A conditional resource cannot be activated by its mere presence.
            return [], [{"source": "reading_plan.conditional", "status": "unresolved_condition"}]
        rows = reading.get(surface) or []
        selected = [row for row in rows if surface != "conditional" or row.get("when") == condition]
        validate_review_rows(root, selected)
        return selected, symbolic

    if surface != "writing_stage" or not stage_id:
        raise ValueError("writing_stage requires the current stage_id")
    stage = _stage(plan, stage_id)
    entries = list(stage.get("read_now", []))
    if stage_id == "question_model_solution_result_validation":
        entries = list((stage.get("before_write_preflight") or {}).get("read_now", [])) + entries
    branches = stage.get("conditional_reads_before_relevant_passage") or {}
    if condition:
        if condition not in branches:
            raise ValueError(f"unknown writing-stage conditional branch: {condition}")
        entries += list(branches[condition].get("read", []))
        symbolic.append({
            "source": f"writing_runtime.{stage_id}.{condition}",
            "status": "requires_current_project_fact_adjudication",
            "when": str(branches[condition].get("when") or ""),
        })
    elif branches:
        for name, branch in branches.items():
            symbolic.append({
                "source": f"writing_runtime.{stage_id}.{name}",
                "status": "unresolved_condition",
                "when": str(branch.get("when") or ""),
            })
    reader = SourceReader(root)
    candidates: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, str):
            symbolic.append({"source": str(entry), "status": "unresolved_stage_entry"})
            continue
        spec = _selector_spec(root, entry)
        if spec is None:
            symbolic.append({"source": entry, "status": "project_fact_or_conditional_input"})
        else:
            candidates.extend(describe_resources(reader, spec, stage_id=stage_id))
    selected = reader.consolidate(candidates)
    validate_review_rows(root, selected)
    return selected, symbolic


def verify_writing_source_commit(
    root: Path, row: dict[str, Any], selected_commit: str,
) -> None:
    """Bind dynamically selected writing-stage bytes to the pinned Git commit.

    Writing stages list symbolic paths/anchors rather than a resolver-produced
    source digest. A digest captured from the current working tree would only
    compare that tree to itself, allowing dirty files to impersonate HEAD.
    """
    actual = SourceReader(root).describe({"path": row["path"]})
    if actual["sha256"] != row["sha256"]:
        raise ValueError(f"writing-stage source SHA-256 differs from reading plan: {row['path']}")
    result = subprocess.run(
        ["git", "-C", str(root), "show", f"{selected_commit}:{row['path']}"],
        capture_output=True, check=False,
    )
    if result.returncode != 0:
        raise ValueError(f"selected commit source could not be verified: {row['path']}")
    if hashlib.sha256(result.stdout).hexdigest() != row["sha256"]:
        raise ValueError(f"writing-stage source SHA-256 differs from selected commit: {row['path']}")


def source_chunks(
    root: Path, row: dict[str, Any], selected_commit: str, chunk_lines: int
) -> list[dict[str, Any]]:
    if chunk_lines < 1:
        raise ValueError("chunk_lines must be positive")
    source = SourceReader(root, str(row.get("origin") or "skill"))
    fresh = source.describe({"path": row["path"]})
    if row.get("sha256") != fresh["sha256"]:
        raise ValueError(f"source SHA-256 differs from reading plan: {row['path']}")
    lines = source.cache[row["path"]][1]
    chunks: list[dict[str, Any]] = []
    for left, right in row["ranges"]:
        if (not isinstance(left, int) or not isinstance(right, int) or left < 1
                or right < left or right > len(lines)):
            raise ValueError("invalid source range in reading plan")
        for start in range(left, right + 1, chunk_lines):
            end = min(start + chunk_lines - 1, right)
            chunks.append({
                "path": row["path"],
                "source_commit": selected_commit,
                "source_sha256": fresh["sha256"],
                "source_blob_sha": None,
                "start_line": start,
                "end_line": end,
                "text": "".join(lines[start - 1:end]),
            })
    if not chunks:
        raise ValueError("empty source is not a completed reading")
    return chunks


def extract(
    plan: dict[str, Any], root: Path, selected_commit: str, surface: str, path: str,
    *, stage_id: str | None = None, condition: str | None = None,
    chunk_lines: int = 120, chunk_index: int = 0,
) -> dict[str, Any]:
    verify_checkout(root, selected_commit)
    rows, symbolic = select_sources(
        plan, root, surface, stage_id=stage_id, condition=condition
    )
    candidates = [row for row in rows if row["path"] == path]
    if len(candidates) != 1:
        raise ValueError(f"required source was not uniquely selected: {path}")
    row = candidates[0]
    if row.get("origin") == "project":
        raise ValueError("project source requires its separate verified project root")
    if surface == "writing_stage":
        verify_writing_source_commit(root, row, selected_commit)
    review_binding = validate_review_rows(root, rows)
    if review_binding is not None:
        # Legacy-plan rows cannot invent leaf hashes at extraction time. New
        # plans carry them, and every declared review source plus its sole map
        # must still match the fixed commit, including dirty working trees.
        verify_writing_source_commit(root, review_binding, selected_commit)
        rolepaths = set((canonical_rolepaths(root) or {}).values())
        for current in rows:
            if current["path"] in rolepaths and not (surface == "writing_stage" and current is row):
                verify_writing_source_commit(root, current, selected_commit)
    chunks = source_chunks(root, row, selected_commit, chunk_lines)
    if chunk_index < 0 or chunk_index >= len(chunks):
        raise ValueError("chunk_index out of range")
    emitted = chunks[chunk_index]
    coverage = validate_chunk_coverage(row["ranges"], [emitted])
    return {
        "status": "source_text_returned_not_stage_or_gate_passed",
        "surface": surface,
        "stage_id": stage_id,
        "condition": condition,
        "source_identity": {
            "path": row["path"], "selected_commit": selected_commit,
            "sha256": row["sha256"], "blob_id": None,
        },
        "resolution": row.get("resolution"),
        "fallback_reason": row.get("fallback_reason"),
        "required_ranges": row["ranges"],
        "chunk_index": chunk_index,
        "chunk_count": len(chunks),
        "returned_chunk": emitted,
        "remaining_ranges": coverage["missing_ranges"],
        "all_required_ranges_returned_in_this_response": coverage["complete"],
        "coverage_issues": coverage["issues"],
        "unresolved_inputs_or_conditions": symbolic,
        "gate_status": "not_executed_by_reader",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path, help="existing resolve_runtime YAML output")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--surface", choices=["read_now", "conditional", "writing_stage"], required=True)
    parser.add_argument("--stage-id")
    parser.add_argument("--condition", help="explicitly adjudicated conditional trigger")
    parser.add_argument("--path", required=True, help="one selected source per tool call")
    parser.add_argument("--chunk-lines", type=int, default=120)
    parser.add_argument("--chunk-index", type=int, default=0)
    args = parser.parse_args()
    try:
        plan = yaml.safe_load(args.plan.read_text(encoding="utf-8"))
        if not isinstance(plan, dict) or not isinstance(plan.get("reading_plan"), dict):
            raise ValueError("a complete resolver reading_plan is required")
        result = extract(
            plan, args.root.resolve(), args.source_commit, args.surface, args.path,
            stage_id=args.stage_id, condition=args.condition,
            chunk_lines=args.chunk_lines, chunk_index=args.chunk_index,
        )
    except (ValueError, FileNotFoundError, UnicodeError, yaml.YAMLError) as exc:
        parser.exit(2, f"reading incomplete: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
