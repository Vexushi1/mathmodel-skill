#!/usr/bin/env python3
"""G4-A measurement-only Resolver YAML read/parse/copy probe; not a runtime API."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
from time import perf_counter
from typing import Any
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import resolve_runtime as ASSURED
import resolve_workflow as LEGACY
import safe_yaml

CONTRACTS = (
    "core/bootstrap.yaml",
    "core/workflow_router.yaml",
    "core/module_manifest.yaml",
)
CASES = (
    ("figure_design_only", "figures", "为时空含水率数据设计新的结果图"),
    ("review_word_no_writes", "review", "审稿 Word 论文，只给修改建议，不修改文件"),
)
MODES = ("cache_disabled", "cache_cold", "cache_warm")


def git_head(root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True, text=True, capture_output=True,
    )
    commit = result.stdout.strip()
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("cannot establish source commit identity")
    return commit


def source_digest(root: Path) -> dict[str, str]:
    return {
        path: hashlib.sha256((root / path).read_bytes()).hexdigest()
        for path in CONTRACTS
    }


def count_contract_reads(loads: list[tuple[str, str]]) -> dict[str, Any]:
    counts = Counter(path for _, path in loads)
    per_role = {role: {path: sum(1 for r, p in loads if r == role and p == path)
                       for path in CONTRACTS}
                for role in ("assured", "legacy")}
    return {
        "per_role": per_role,
        "per_contract": {path: counts[path] for path in CONTRACTS},
        "duplicate_contract_reads": sum(max(0, counts[path] - 1) for path in CONTRACTS),
        "total_tracked_yaml_file_reads": len(loads),
        "distinct_tracked_yaml_paths": len(counts),
    }


def capture(intent: str, request: str, mode: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if mode not in MODES:
        raise ValueError("unknown measurement mode")
    loads: list[tuple[str, str]] = []
    parser_calls = 0
    deep_copies = 0
    original_parse = yaml.load
    original_copy = safe_yaml.deepcopy

    def tracked_load(role: str, original: Any) -> Any:
        def apply(path: Path) -> dict[str, Any]:
            relative = Path(path).relative_to(ROOT).as_posix()
            loads.append((role, relative))
            return original(path)
        return apply

    def tracked_parse(stream: Any, Loader: Any) -> Any:
        nonlocal parser_calls
        parser_calls += 1
        return original_parse(stream, Loader=Loader)

    def tracked_copy(value: Any) -> Any:
        nonlocal deep_copies
        deep_copies += 1
        return original_copy(value)

    with mock.patch.dict(os.environ, {
        "HSK_YAML_DISABLE_CACHE": "1" if mode == "cache_disabled" else "0",
        "HSK_YAML_PURE_PYTHON": "0",
    }):
        with mock.patch.object(ASSURED, "load_yaml",
                               side_effect=tracked_load("assured", ASSURED.load_yaml)), \
             mock.patch.object(LEGACY, "load_yaml",
                               side_effect=tracked_load("legacy", LEGACY.load_yaml)), \
             mock.patch.object(yaml, "load", side_effect=tracked_parse), \
             mock.patch.object(safe_yaml, "deepcopy", side_effect=tracked_copy):
            started = perf_counter()
            plan = ASSURED.resolve_runtime(intent, request=request, competition="CUMCM")
            elapsed = perf_counter() - started
        cache_state = safe_yaml.cache_info()
    signature = hashlib.sha256(
        yaml.safe_dump(plan, allow_unicode=True, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return plan, {
        "mode": mode,
        "wall_seconds": round(elapsed, 6),
        "parser_calls": parser_calls,
        "safe_yaml_deep_copies": deep_copies,
        "cache_entry_count_after": cache_state["entries"],
        "plan_sha256": signature,
        "loads": count_contract_reads(loads),
    }


def collect(root: Path, repeats: int = 3) -> dict[str, Any]:
    if not 1 <= repeats <= 5:
        raise ValueError("repeats must be between 1 and 5")
    if root.resolve(strict=True) != ROOT:
        raise ValueError("G4-A probe can only measure its checked-out source tree")
    commit = git_head(root)
    hashes = source_digest(root)
    cases: list[dict[str, Any]] = []
    try:
        for case_id, intent, request in CASES:
            trials: list[dict[str, Any]] = []
            reference_plan: dict[str, Any] | None = None
            for _ in range(repeats):
                safe_yaml.clear_cache()
                plain_plan, plain = capture(intent, request, "cache_disabled")
                safe_yaml.clear_cache()
                cold_plan, cold = capture(intent, request, "cache_cold")
                warm_plan, warm = capture(intent, request, "cache_warm")
                if plain_plan != cold_plan or plain_plan != warm_plan:
                    raise AssertionError(f"cache changed Resolver behavior for {case_id}")
                if reference_plan is not None and plain_plan != reference_plan:
                    raise AssertionError(f"Resolver plan changed between repeats for {case_id}")
                reference_plan = plain_plan
                trials.append({"cache_disabled": plain, "cache_cold": cold,
                               "cache_warm": warm})
            cases.append({
                "id": case_id,
                "runs": trials,
                "summary": {
                    mode: {
                        "median_wall_seconds": statistics.median(
                            trial[mode]["wall_seconds"] for trial in trials
                        ),
                        "median_parser_calls": statistics.median(
                            trial[mode]["parser_calls"] for trial in trials
                        ),
                        "median_safe_yaml_deep_copies": statistics.median(
                            trial[mode]["safe_yaml_deep_copies"] for trial in trials
                        ),
                        "median_duplicate_contract_reads": statistics.median(
                            trial[mode]["loads"]["duplicate_contract_reads"]
                            for trial in trials
                        ),
                    } for mode in MODES
                },
                "behavior_equal": True,
            })
        if git_head(root) != commit or source_digest(root) != hashes:
            raise RuntimeError("source identity changed during G4-A measurement")
    finally:
        safe_yaml.clear_cache()
    return {
        "schema_version": 1,
        "source_commit": commit,
        "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python": platform.python_version(),
        "pyyaml": yaml.__version__,
        "loader": safe_yaml.loader_name(use_c=True),
        "measurement_type": "one_process_synthetic_resolver_admission_only",
        "not_a_production_api": True,
        "repeats": repeats,
        "contract_sha256": hashes,
        "cases": cases,
        "not_measured": [
            "real_chatgpt_tokens", "GitHub_only_end_to_end_latency",
            "project_mutable_state", "production_preparsed_argument_roi",
            "cross_process_cache_sharing", "user_numerical_execution",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    root = args.repo_root.resolve(strict=True)
    target = args.output.resolve()
    if target == root or root in target.parents:
        raise ValueError("measurement evidence must not be written inside repository")
    report = collect(root, args.repeats)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True,
                                     indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "measured_without_runtime_changes",
        "source_commit": report["source_commit"],
        "cases": {case["id"]: case["summary"] for case in report["cases"]},
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
