#!/usr/bin/env python3
"""G3-B measurement-only grouped source reading, not a runtime API/Gate."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys
from time import perf_counter
from typing import Any
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import read_stage as ACTIVE
import resolve_runtime as RESOLVER
from reading_plan import validate_chunk_coverage, validate_review_rows

CHUNK_LINES = 60
CHUNKS_PER_FILE = 4
MAX_SOURCE_BYTES = 65536
SOURCES = ("modules/04_figure_evidence.md",
           "templates/figure/result_figure_contract.md")


def git_head(root: Path) -> str:
    result = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                            capture_output=True, text=True, check=True)
    commit = result.stdout.strip()
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("unknown checkout identity")
    return commit


def chosen_rows(plan: dict, root: Path, paths: tuple[str, ...] = SOURCES) -> list[dict]:
    rows, unresolved = ACTIVE.select_sources(plan, root, "read_now")
    if unresolved or validate_review_rows(root, rows) is not None:
        raise ValueError("pilot excludes conditional/project/review sources")
    chosen = []
    for path in paths:
        matching = [row for row in rows if row.get("path") == path
                    and row.get("origin", "skill") == "skill"]
        if len(matching) != 1:
            raise ValueError(f"source not uniquely selected: {path}")
        chosen.append(matching[0])
    return chosen


def count_git_and_time(fn: Any) -> tuple[Any, dict]:
    old = subprocess.run
    calls = []

    def traced(*args: Any, **kwargs: Any) -> Any:
        argv = args[0] if args else kwargs.get("args")
        if (isinstance(argv, (list, tuple)) and argv
                and Path(str(argv[0])).name.lower() in {"git", "git.exe"}):
            calls.append(argv)
        return old(*args, **kwargs)

    start = perf_counter()
    with mock.patch.object(subprocess, "run", side_effect=traced):
        result = fn()
    return result, {"seconds": round(perf_counter() - start, 6),
                    "git_subprocesses": len(calls)}


def sequential(plan: dict, root: Path, commit: str, rows: list[dict]) -> list[dict]:
    result = []
    for row in rows:
        for index in range(CHUNKS_PER_FILE):
            if index and index >= count:
                break
            data = ACTIVE.extract(plan, root, commit, "read_now", row["path"],
                                  chunk_lines=CHUNK_LINES, chunk_index=index)
            count = data["chunk_count"]
            if data["gate_status"] != "not_executed_by_reader":
                raise RuntimeError("original Reader erroneously claimed Gate execution")
            result.append(data["returned_chunk"])
    return result


def grouped_probe(plan: dict, root: Path, commit: str,
                  paths: tuple[str, ...] = SOURCES) -> dict:
    """Validate once per request, and again on exit; no durable identity cache."""
    ACTIVE.verify_checkout(root, commit)
    ACTIVE.verify_plan_context(root, plan, commit)
    rows = chosen_rows(plan, root, paths)
    chunks = []
    bytes_returned = 0
    coverage = {}
    for row in rows:
        ACTIVE.verify_writing_source_commit(root, row, commit)
        all_chunks = ACTIVE.source_chunks(root, row, commit, CHUNK_LINES)
        selected = all_chunks[:CHUNKS_PER_FILE]
        if not selected:
            raise ValueError("empty source")
        nbytes = sum(len(chunk["text"].encode("utf-8")) for chunk in selected)
        if nbytes <= 0 or bytes_returned + nbytes > MAX_SOURCE_BYTES:
            raise ValueError("bounded reply budget exceeded; report no partial success")
        bytes_returned += nbytes
        check = validate_chunk_coverage(row["ranges"], selected)
        if check["issues"]:
            raise ValueError("invalid selected chunk coverage")
        coverage[row["path"]] = {
            "planned_ranges": deepcopy(row["ranges"]),
            "first_chunks": len(selected),
            "available_chunks": len(all_chunks),
            "complete": check["complete"],
            "missing_ranges": check["missing_ranges"],
            "issues": check["issues"],
        }
        chunks.extend(selected)
    # Source and selected branch must still be current after *all* output was built.
    ACTIVE.verify_checkout(root, commit)
    ACTIVE.verify_plan_context(root, plan, commit)
    for row in rows:
        ACTIVE.verify_writing_source_commit(root, row, commit)
    identities = {(x["path"], x["source_commit"], x["source_sha256"]) for x in chunks}
    if len(identities) != len(rows):
        raise ValueError("duplicate or mismatched source identity")
    return {
        "status": "probe_text_returned_not_a_read_qualification",
        "gate_status": "not_executed_by_reader",
        "chunks": chunks, "coverage": coverage,
        "source_text_bytes": bytes_returned,
    }


def identical(a: list[dict], b: dict, rows: list[dict]) -> None:
    if a != b["chunks"]:
        raise AssertionError("batch source text/ranges/provenance differs from serial")
    if b["gate_status"] != "not_executed_by_reader":
        raise AssertionError("batch claimed Gate execution")
    for row in rows:
        relevant = [x for x in b["chunks"] if x["path"] == row["path"]]
        check = validate_chunk_coverage(row["ranges"], relevant)
        stated = b["coverage"][row["path"]]
        if (check["complete"] != stated["complete"] or
                check["missing_ranges"] != stated["missing_ranges"] or
                check["issues"] != stated["issues"]):
            raise AssertionError("coverage is not established by the returned chunks")


def collect(root: Path, repeat: int = 3) -> dict:
    if repeat < 1 or repeat > 4:
        raise ValueError("repeat must be between 1 and 4")
    root = root.resolve(strict=True)
    commit = git_head(root)
    # Stateless synthetic G1B case, no accepted results and no real user project.
    plan = RESOLVER.resolve_runtime(
        "figures", request="为时空含水率数据设计新的结果图", competition="CUMCM")
    rows = chosen_rows(plan, root)
    runs = []
    for _ in range(repeat):
        old, prior = count_git_and_time(lambda: sequential(plan, root, commit, rows))
        new, grouped = count_git_and_time(lambda: grouped_probe(plan, root, commit))
        identical(old, new, rows)
        runs.append({"serial_seconds": prior["seconds"],
                     "grouped_seconds": grouped["seconds"],
                     "serial_git_subprocesses": prior["git_subprocesses"],
                     "grouped_git_subprocesses": grouped["git_subprocesses"],
                     "source_text_bytes": new["source_text_bytes"],
                     "returned_chunks": len(new["chunks"])})
    if git_head(root) != commit:
        raise RuntimeError("checkout changed during G3B measurement")
    return {
        "schema_version": 1,
        "source_commit": commit,
        "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "profile": plan["reading_plan"]["profile"],
        "case": "G1B figure_design_only",
        "measurement_type": "one_process_pilot_not_production_batch_api",
        "sources": list(SOURCES),
        "chunk_lines": CHUNK_LINES,
        "chunks_per_file": CHUNKS_PER_FILE,
        "max_source_reply_bytes": MAX_SOURCE_BYTES,
        "runs": runs,
        "summary": {
            "serial_median_seconds": statistics.median(x["serial_seconds"] for x in runs),
            "grouped_median_seconds": statistics.median(x["grouped_seconds"] for x in runs),
            "serial_median_git_subprocesses": statistics.median(x["serial_git_subprocesses"] for x in runs),
            "grouped_median_git_subprocesses": statistics.median(x["grouped_git_subprocesses"] for x in runs),
            "source_text_identical": True,
            "gate_execution": False,
        },
        "not_measured": ["real_model_token_usage", "GitHub_only_tool_latency",
                         "project_origin_sources", "writing_stage", "conditional",
                         "complete_multi_page_consumer_delivery"],
        "changes_live_reader": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeat", type=int, default=3)
    args = parser.parse_args()
    data = collect(args.repo_root, args.repeat)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2,
                                      sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "measured", "commit": data["source_commit"],
                      "summary": data["summary"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
