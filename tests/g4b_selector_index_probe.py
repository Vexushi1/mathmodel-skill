#!/usr/bin/env python3
"""G4-B test-only Markdown selector index admission; never a runtime cache."""
from __future__ import annotations

import argparse
from collections import Counter
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
import reading_plan as READING
import resolve_runtime as RUNTIME

MODES = ("existing", "test_only_index")
CASES = (
    ("figure_design_only", "figures", "为时空含水率数据设计新的结果图"),
    ("review_word_no_writes", "review", "审稿 Word 论文，只给修改建议，不修改文件"),
)
SOURCES = (
    "core/bootstrap.yaml",
    "core/workflow_router.yaml",
    "core/module_manifest.yaml",
    "modules/04_figure_evidence.md",
    "modules/06_review_delivery.md",
)
MAX_ENTRY_BYTES = 512 * 1024
MAX_CACHE_BYTES = 4 * 1024 * 1024
MAX_CACHE_ENTRIES = 32


def git_head(root: Path) -> str:
    run = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    )
    head = run.stdout.strip()
    if len(head) != 40 or any(c not in "0123456789abcdef" for c in head):
        raise ValueError("invalid Git source identity")
    return head


def pinned_sources(root: Path, commit: str) -> dict[str, str]:
    digests: dict[str, str] = {}
    for path in SOURCES:
        raw = (root / path).read_bytes()
        run = subprocess.run(
            ["git", "-C", str(root), "show", f"{commit}:{path}"],
            capture_output=True, check=False,
        )
        if run.returncode or run.stdout != raw:
            raise ValueError(f"source changed against pinned commit: {path}")
        digests[path] = hashlib.sha256(raw).hexdigest()
    return digests


class HeadingIndex:
    """Experiment scoped to each SourceReader instance, not shared project state."""

    def __init__(self, mode: str):
        if mode not in MODES:
            raise ValueError("unknown G4-B measurement mode")
        self.mode = mode
        self.original = READING._headings
        self.original_describe = READING.SourceReader.describe
        self.reader_stack: list[Any] = []
        self.cache: dict[tuple[Any, bytes], tuple[tuple[int, int, str], ...]] = {}
        self.cache_bytes = 0
        self.heading_requests = 0
        self.heading_builds = 0
        self.index_hits = 0
        self.yaml_scan_calls = 0
        self.yaml_compose_calls = 0
        self.describe_counts: Counter[str] = Counter()

    def describe(self, reader: Any, spec: dict[str, Any]) -> dict[str, Any]:
        self.describe_counts[str(spec["path"])] += 1
        self.reader_stack.append(reader)
        try:
            return self.original_describe(reader, spec)
        finally:
            self.reader_stack.pop()

    def headings(self, lines: list[str]) -> list[tuple[int, int, str]]:
        self.heading_requests += 1
        raw = "".join(lines).encode("utf-8")
        owner = self.reader_stack[-1] if self.reader_stack else None
        key = (owner, raw)  # Exact bytes plus reader identity, not a digest-only hit.
        if self.mode == "test_only_index" and key in self.cache:
            self.index_hits += 1
            return list(self.cache[key])  # Never share the mutable list with a caller.
        self.heading_builds += 1
        result = self.original(lines)
        if (self.mode == "test_only_index" and key not in self.cache
                and len(raw) <= MAX_ENTRY_BYTES
                and len(self.cache) < MAX_CACHE_ENTRIES
                and self.cache_bytes + len(raw) <= MAX_CACHE_BYTES):
            self.cache[key] = tuple(result)
            self.cache_bytes += len(raw)
        return result

    def counts(self) -> dict[str, Any]:
        return {
            "markdown_heading_requests": self.heading_requests,
            "markdown_actual_heading_builds": self.heading_builds,
            "markdown_index_hits": self.index_hits,
            "yaml_selector_scan_calls": self.yaml_scan_calls,
            "yaml_selector_compose_calls": self.yaml_compose_calls,
            "source_describes": dict(sorted(self.describe_counts.items())),
            "duplicate_source_describes": sum(
                max(0, n - 1) for n in self.describe_counts.values()
            ),
            "index_entries": len(self.cache),
            "index_source_bytes": self.cache_bytes,
        }


def capture(intent: str, request: str, mode: str) -> tuple[dict[str, Any], dict[str, Any]]:
    index = HeadingIndex(mode)
    original_scan = yaml.scan
    original_compose = yaml.compose

    def tracked_scan(*args: Any, **kwargs: Any) -> Any:
        index.yaml_scan_calls += 1
        return original_scan(*args, **kwargs)

    def tracked_compose(*args: Any, **kwargs: Any) -> Any:
        index.yaml_compose_calls += 1
        return original_compose(*args, **kwargs)

    with mock.patch.object(READING, "_headings", side_effect=index.headings), \
         mock.patch.object(READING.SourceReader, "describe", autospec=True,
                           side_effect=index.describe), \
         mock.patch.object(yaml, "scan", side_effect=tracked_scan), \
         mock.patch.object(yaml, "compose", side_effect=tracked_compose):
        started = perf_counter()
        plan = RUNTIME.resolve_runtime(intent, request=request, competition="CUMCM")
        wall_seconds = perf_counter() - started
    signature = hashlib.sha256(
        yaml.safe_dump(plan, allow_unicode=True, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return plan, {
        "mode": mode,
        "wall_seconds": round(wall_seconds, 6),
        "full_plan_sha256": signature,
        **index.counts(),
    }


def collect(root: Path, repeats: int = 3) -> dict[str, Any]:
    if not 1 <= repeats <= 5:
        raise ValueError("repeats must be 1..5")
    if root.resolve(strict=True) != ROOT:
        raise ValueError("G4-B probe requires its checked-out source tree")
    commit = git_head(root)
    hashes = pinned_sources(root, commit)
    cases = []
    for case_id, intent, request in CASES:
        runs = []
        reference: dict[str, Any] | None = None
        for _ in range(repeats):
            actual, current = capture(intent, request, "existing")
            projected, indexed = capture(intent, request, "test_only_index")
            if actual != projected or (reference is not None and actual != reference):
                raise AssertionError(f"selector indexing changed full Resolver plan: {case_id}")
            reference = actual
            runs.append({"existing": current, "test_only_index": indexed})
        cases.append({
            "id": case_id, "full_plan_equal": True, "runs": runs,
            "summary": {
                mode: {
                    metric: statistics.median(run[mode][metric] for run in runs)
                    for metric in (
                        "wall_seconds", "markdown_heading_requests",
                        "markdown_actual_heading_builds", "markdown_index_hits",
                        "yaml_selector_scan_calls", "yaml_selector_compose_calls",
                        "duplicate_source_describes",
                    )
                } for mode in MODES
            },
        })
    if git_head(root) != commit or pinned_sources(root, commit) != hashes:
        raise RuntimeError("source identity drift in G4-B probe")
    return {
        "schema_version": 1, "source_commit": commit,
        "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "measurement": "one_process_real_resolver_and_test_only_markdown_index",
        "repeats": repeats, "source_sha256": hashes, "cases": cases,
        "no_production_changes": True,
        "not_measured": [
            "YAML_AST_index_reuse", "project_origin_and_mutable_generation",
            "production_cache_memory_lifecycle", "real_ChatGPT_tokens",
            "GitHub_only_end_to_end_latency", "user_numerical_execution",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    root = args.repo_root.resolve(strict=True)
    output = args.output.resolve()
    if output == root or root in output.parents:
        raise ValueError("reports must be outside the repository")
    report = collect(root, repeats=args.repeats)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": "measured_no_production_change",
        "source_commit": report["source_commit"],
        "summaries": {c["id"]: c["summary"] for c in report["cases"]},
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
