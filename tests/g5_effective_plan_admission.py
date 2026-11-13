#!/usr/bin/env python3
"""G5 admission only: inspect effective-plan composability without narrowing reads.

A union of source rows is not proof of a composable execution plan. This
instrument is deliberately stateless and cannot certify approval, action
independence, actual source consumption, Gate execution, or user latency.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
import resolve_runtime as RESOLVER
import v10270_action_observation as ORACLE

IDS = ("independent_figure_and_latex", "independent_validation_and_latex")
SINGLE_REQUESTS = {
    "update_figure": "修改问题二图表",
    "revise_paper_explanation": "调整 LaTeX 论文中的文字说明",
    "model_validation": "进行模型检验",
    "write_latex": "编写 LaTeX 论文正文",
}
ORACLE_RELATIVE = "tests/fixtures/v10270_action_oracle.yaml"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def selected_cases(root: Path) -> list[dict[str, Any]]:
    corpus = ORACLE.validate_cases(root / ORACLE_RELATIVE)
    by_id = {item["id"]: item for item in corpus}
    if any(key not in by_id for key in IDS):
        raise ValueError("G5 requires both independently labeled G2 mixed cases")
    selected = [by_id[key] for key in IDS]
    for case in selected:
        actions = case["positive_actions"]
        if (case["category"] != "independent_actions" or len(actions) != 2
                or any(item["id"] not in SINGLE_REQUESTS for item in actions)):
            raise ValueError("G5 G2 case identity/actions changed: " + case["id"])
    return selected


def source_rows(plan: dict[str, Any], surface: str) -> list[dict[str, Any]]:
    reading = plan.get("reading_plan") or {}
    rows = reading.get(surface) or []
    if not isinstance(rows, list):
        raise ValueError("invalid reading surface: " + surface)
    for item in rows:
        if (not isinstance(item, dict) or not isinstance(item.get("path"), str)
                or not isinstance(item.get("sha256"), str)
                or not isinstance(item.get("ranges"), list)):
            raise ValueError("reading row has no checkable source identity and ranges")
    return rows


def normalize_ranges(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], list[tuple[int, int]]]:
    result: dict[tuple[str, str, str], list[tuple[int, int]]] = {}
    for row in rows:
        key = (str(row.get("origin") or "skill"), row["path"], row["sha256"])
        ranges = result.setdefault(key, [])
        for interval in row["ranges"]:
            if (not isinstance(interval, list) or len(interval) != 2
                    or not all(type(x) is int and x > 0 for x in interval)
                    or interval[1] < interval[0]):
                raise ValueError(f"malformed source interval: {row['path']}")
            ranges.append((interval[0], interval[1]))
    for key, intervals in result.items():
        merged: list[tuple[int, int]] = []
        for left, right in sorted(intervals):
            if merged and left <= merged[-1][1] + 1:
                merged[-1] = (merged[-1][0], max(merged[-1][1], right))
            else:
                merged.append((left, right))
        result[key] = merged
    return result


def missing_read_ranges(required: list[dict[str, Any]], proposed: list[dict[str, Any]]
                        ) -> list[dict[str, Any]]:
    """Compare only original 1-based source ranges; no reading or Gate attestation."""
    want, have = normalize_ranges(required), normalize_ranges(proposed)
    missing = []
    for key, intervals in want.items():
        supplied = have.get(key, [])
        for lo, hi in intervals:
            cursor = lo
            for a, b in supplied:
                if b < cursor or a > hi:
                    continue
                if a > cursor:
                    missing.append({"source": key, "range": [cursor, a - 1]})
                cursor = max(cursor, b + 1)
                if cursor > hi:
                    break
            if cursor <= hi:
                missing.append({"source": key, "range": [cursor, hi]})
    return missing


def gate_signature(gate: dict[str, Any]) -> str:
    """Include complete gate semantics instead of just its display name."""
    if not isinstance(gate, dict) or not isinstance(gate.get("name"), str):
        raise ValueError("invalid resolver gate")
    return json.dumps(gate, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def ordered_subsequence(items: list[str], sequence: list[str]) -> bool:
    it = iter(sequence)
    return all(any(candidate == item for candidate in it) for item in items)


def all_gate_orders_preserved(mixed: dict[str, Any],
                              singles: list[dict[str, Any]]) -> bool:
    combined = [gate_signature(g) for g in mixed.get("pre_delivery_gates", [])]
    return all(ordered_subsequence(
        [gate_signature(g) for g in single.get("pre_delivery_gates", [])], combined,
    ) for single in singles)


def safe_selected_row_identity(root: Path, commit: str, plans: list[dict[str, Any]]) -> dict[str, str]:
    """Check all unique skill-origin planned sources against current commit bytes."""
    observed: dict[str, str] = {}
    for plan in plans:
        for surface in ("read_now", "conditional"):
            for row in source_rows(plan, surface):
                if str(row.get("origin") or "skill") != "skill":
                    raise ValueError("stateless G5 probe cannot qualify project-origin sources")
                path = row["path"]
                if path in observed:
                    if observed[path] != row["sha256"]:
                        raise ValueError("inconsistent source SHA across effective plans: " + path)
                    continue
                source = (root / path).resolve()
                if not source.is_relative_to(root) or not source.is_file():
                    raise ValueError("missing or escaping source: " + path)
                raw = source.read_bytes()
                if digest(raw) != row["sha256"]:
                    raise ValueError("plan SHA differs from current bytes: " + path)
                committed = subprocess.run(
                    ["git", "-C", str(root), "show", f"{commit}:{path}"],
                    capture_output=True, check=False,
                )
                if committed.returncode != 0 or committed.stdout != raw:
                    raise ValueError("selected commit differs from source: " + path)
                observed[path] = digest(raw)
    return dict(sorted(observed.items()))


def summarize(plan: dict[str, Any]) -> dict[str, Any]:
    read = plan.get("reading_plan") or {}
    assurance = plan.get("assurance") or {}
    return {
        "intents": list(plan.get("intents", []) or []),
        "modules": list(plan.get("modules", []) or []),
        "pause_state": plan.get("pause_state"),
        "pause_for_model_approval": plan.get("pause_for_model_approval"),
        "pause_for_user_execution": plan.get("pause_for_user_execution"),
        "delivery_scope": plan.get("delivery_scope"),
        "assurance_status": assurance.get("status"),
        "missing_prerequisites": list(plan.get("missing_prerequisites", []) or []),
        "terminal_outputs": list(plan.get("terminal_outputs", []) or []),
        "gates": [g.get("name") for g in plan.get("pre_delivery_gates", [])],
        "reading_profile": read.get("profile"),
        "reading_status": read.get("status"),
        "read_now_sources": len(source_rows(plan, "read_now")),
        "conditional_sources": len(source_rows(plan, "conditional")),
    }


def probe_one(root: Path, case: dict[str, Any], commit: str) -> dict[str, Any]:
    """No project root: report negative evidence; do not assert real-world composability."""
    actions = case["positive_actions"]
    start = perf_counter()
    mixed = RESOLVER.resolve_runtime(
        request=case["request"], competition=case["competition"],
    )
    singles = [
        RESOLVER.resolve_runtime(
            action["intent"], request=SINGLE_REQUESTS[action["id"]],
            competition=case["competition"],
        ) for action in actions
    ]
    elapsed = round(perf_counter() - start, 6)
    expected = {action["intent"] for action in actions}
    selected = set(mixed.get("intents", []))
    missing_actions = sorted(expected - selected)
    forbidden = sorted(set(case.get("negative_intents", [])) & selected)
    gates_preserved = all_gate_orders_preserved(mixed, singles)
    full_read = source_rows(mixed, "read_now")
    union = [row for plan in singles for row in source_rows(plan, "read_now")]
    gaps = missing_read_ranges(full_read, union)
    # This is an observation of declared conditional resources, never their activation.
    cond_signatures = Counter(
        (str(row.get("origin") or "skill"), row["path"], row["sha256"], str(row.get("when")))
        for row in source_rows(mixed, "conditional")
    )
    source_hashes = safe_selected_row_identity(root, commit, [mixed, *singles])
    reasons: list[str] = []
    if missing_actions:
        reasons.append("mixed_effective_plan_omits_positive_actions")
    if forbidden:
        reasons.append("mixed_effective_plan_selects_forbidden_intent")
    if case.get("dependencies"):
        reasons.append("oracle_declares_cross_action_dependencies")
    if not gates_preserved:
        reasons.append("individual_gate_order_or_parameters_not_embedded_in_mixed_plan")
    if gaps:
        reasons.append("union_of_individual_read_ranges_does_not_cover_mixed_effective_plan")
    if any(plan.get("pause_state") and not mixed.get("pause_state") for plan in singles):
        reasons.append("mixed_plan_cannot_discard_an_individual_pause")
    reasons.append("stateless_cases_cannot_prove_current_project_approval_and_write_isolation")
    return {
        "case_id": case["id"],
        "positive_action_ids": [action["id"] for action in actions],
        "explicit_cross_action_dependencies": list(case.get("dependencies", [])),
        "mixed": summarize(mixed),
        "individual": [summarize(plan) for plan in singles],
        "missing_actions": missing_actions,
        "forbidden_intents": forbidden,
        "gate_order_and_parameters_preserved": gates_preserved,
        "source_union_missing_mixed_ranges": gaps,
        "conditional_trigger_count": sum(cond_signatures.values()),
        "conditional_conditions_not_executed": True,
        "source_sha256": source_hashes,
        "observation_wall_seconds": elapsed,
        "composability_admission": "NOT_ADMITTED",
        "reasons": reasons,
        "gate_execution": False,
        "read_consumption_executed": False,
    }


def git_head(root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    )
    commit = result.stdout.strip()
    if len(commit) != 40 or any(char not in "0123456789abcdef" for char in commit):
        raise ValueError("unknown source commit")
    return commit


def collect(root: Path) -> dict[str, Any]:
    if root.resolve(strict=True) != ROOT:
        raise ValueError("G5 probe requires candidate checked-out source tree")
    head = git_head(root)
    oracle_sha = digest((root / ORACLE_RELATIVE).read_bytes())
    rows = [probe_one(root, case, head) for case in selected_cases(root)]
    if git_head(root) != head or digest((root / ORACLE_RELATIVE).read_bytes()) != oracle_sha:
        raise ValueError("G5 source identity drift; report discarded")
    if any(row["missing_actions"] or row["forbidden_intents"] for row in rows):
        raise AssertionError("G2 independently marked actions have regressed")
    if any(row["composability_admission"] != "NOT_ADMITTED" for row in rows):
        raise AssertionError("stateless G5 probe may not qualify an effective plan")
    return {
        "schema_version": 1,
        "source_commit": head,
        "driver_sha256": digest(Path(__file__).read_bytes()),
        "oracle_sha256": oracle_sha,
        "measurement_type": "read_only_effective_plan_composability_precheck",
        "case_count": len(rows),
        "cases": rows,
        "production_narrow_read_enabled": False,
        "project_state_written": False,
        "not_measured": [
            "real_project_composition", "actual_tool_source_consumption",
            "actual_chatgpt_tokens", "project_generation_conflicts",
            "cross_action_writes", "human_approval", "gate_execution",
            "end_to_end_user_latency",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = args.repo_root.resolve(strict=True)
    output = args.output.resolve()
    if output == root or root in output.parents:
        raise ValueError("G5 report must stay outside repository")
    report = collect(root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": "measured_not_admitted",
        "source_commit": report["source_commit"],
        "cases": {x["case_id"]: x["reasons"] for x in report["cases"]},
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
