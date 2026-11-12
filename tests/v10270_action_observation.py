#!/usr/bin/env python3
"""G1B read-only synthetic action oracle and bounded observed runtime/reader costs.

This is a measurement instrument, not a Router, approval, project writer or Gate.
It reports current known action gaps without silently changing production behavior.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import tempfile
from time import perf_counter
from typing import Any

import yaml

SCHEMA_VERSION = 1
CATEGORIES = {"single_action", "independent_actions", "read_only", "explicit_scope",
              "historically_protected_carriers", "lifecycle"}
CASE_KEYS = {
    "id", "request", "competition", "explicit_intents", "category",
    "positive_actions", "negative_intents", "informational_mentions",
    "targets", "dependencies", "protected_assured_intents",
    "expected_pause_state", "forbid_execution_modules", "forbid_write_gates",
    "read_sample_path",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_cases(path: Path) -> list[dict[str, Any]]:
    value = yaml.safe_load(path.read_bytes())
    if not isinstance(value, dict) or set(value) != {"schema_version", "authored_basis", "cases"}:
        raise ValueError("G1B oracle requires the exact corpus envelope")
    if value["schema_version"] != SCHEMA_VERSION or value["authored_basis"] != "human_independent_semantic_labels":
        raise ValueError("G1B oracle must be independently authored")
    rows = value["cases"]
    if not isinstance(rows, list) or not rows:
        raise ValueError("G1B oracle requires cases")
    ids = []
    for case in rows:
        if not isinstance(case, dict) or set(case) - CASE_KEYS:
            raise ValueError("invalid G1B case fields")
        if not all(isinstance(case.get(key), str) and case[key].strip()
                   for key in ("id", "request", "competition", "category")):
            raise ValueError("missing G1B case identity/request/scope")
        if case["category"] not in CATEGORIES:
            raise ValueError("unknown G1B category")
        ids.append(case["id"])
        actions = case.get("positive_actions")
        if not isinstance(actions, list) or not actions:
            raise ValueError("each G1B case requires positive actions")
        for action in actions:
            if (not isinstance(action, dict) or set(action) != {"id", "intent"}
                    or not all(isinstance(action[key], str) and action[key]
                               for key in ("id", "intent"))):
                raise ValueError("positive action requires manually marked id and intent")
        action_ids = [action["id"] for action in actions]
        if len(set(action_ids)) != len(action_ids):
            raise ValueError("duplicate positive action IDs")
        for key in ("negative_intents", "informational_mentions", "targets", "dependencies",
                    "explicit_intents", "protected_assured_intents", "forbid_execution_modules"):
            values = case.get(key, [])
            if (not isinstance(values, list)
                    or any(not isinstance(item, str) or not item.strip() for item in values)
                    or len(set(values)) != len(values)):
                raise ValueError(f"G1B {key} must be unique nonblank strings")
        if set(case.get("negative_intents", [])) & {action["intent"] for action in actions}:
            raise ValueError("same G1B action cannot be positive and forbidden")
        if "expected_pause_state" in case and not isinstance(case["expected_pause_state"], str):
            raise ValueError("expected pause state must be text")
        if "forbid_write_gates" in case and not isinstance(case["forbid_write_gates"], bool):
            raise ValueError("forbid_write_gates must be boolean")
        if "read_sample_path" in case:
            p = case["read_sample_path"]
            if not isinstance(p, str) or not p or p.startswith("/") or ".." in Path(p).parts:
                raise ValueError("read sample path must be a safe repository-relative source")
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate G1B case IDs")
    return rows


def run_cmd(cmd: list[str], root: Path) -> tuple[subprocess.CompletedProcess[str], float]:
    env = dict(os.environ, PYTHONUTF8="1")
    start = perf_counter()
    result = subprocess.run(cmd, cwd=root, capture_output=True, text=True,
                            encoding="utf-8", timeout=120, env=env, check=False)
    return result, perf_counter() - start


def githash(root: Path) -> str:
    proc, _ = run_cmd(["git", "-C", str(root), "rev-parse", "HEAD"], root)
    if proc.returncode != 0 or len(proc.stdout.strip()) != 40:
        raise RuntimeError("cannot identify G1B source checkout")
    return proc.stdout.strip()


def invoke(root: Path, case: dict[str, Any]) -> tuple[dict[str, Any], str, float]:
    cmd = [sys.executable, str(root / "scripts/resolve_runtime.py"),
           *case.get("explicit_intents", []), "--request", case["request"],
           "--competition", case["competition"]]
    proc, elapsed = run_cmd(cmd, root)
    if proc.returncode:
        raise RuntimeError(f"{case['id']}: resolver error ({proc.returncode}): {proc.stderr[-1000:]}")
    plan = yaml.safe_load(proc.stdout)
    if not isinstance(plan, dict) or not isinstance(plan.get("reading_plan"), dict):
        raise RuntimeError(f"{case['id']}: incomplete resolver plan")
    return plan, proc.stdout, elapsed


def observed_actions(case: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    selected = plan.get("intents", []) or []
    pause = plan.get("pause_state")
    actions = []
    for action in case["positive_actions"]:
        if action["intent"] in selected:
            disposition = "explicitly_deferred_or_blocked" if pause else "dispatched"
            reason = f"effective plan pause: {pause}" if pause else "selected intent (not execution)"
        else:
            disposition = "missing_unjustified"
            reason = "declared independent action is absent from selected intents"
        actions.append({"id": action["id"], "intent": action["intent"],
                        "disposition": disposition, "reason": reason})
    forbidden = sorted(set(selected) & set(case.get("negative_intents", [])))
    conflicts = []
    if forbidden:
        conflicts.append({"type": "forbidden_intent", "intents": forbidden})
    protected = case.get("protected_assured_intents")
    if protected is not None and list(selected) != protected:
        conflicts.append({"type": "protected_carrier_selection_changed",
                          "expected": protected, "observed": selected})
    expected_pause = case.get("expected_pause_state")
    if expected_pause is not None and pause != expected_pause:
        conflicts.append({"type": "unexpected_pause", "expected": expected_pause, "observed": pause})
    modules = plan.get("modules", []) or []
    unexpected = sorted(set(modules) & set(case.get("forbid_execution_modules", [])))
    if unexpected:
        conflicts.append({"type": "execution_boundary_crossed", "modules": unexpected})
    gates = plan.get("pre_delivery_gates", []) or []
    if case.get("forbid_write_gates") and any("--write" in str(gate.get("command", "")) for gate in gates):
        conflicts.append({"type": "write_capable_gate_in_read_only_plan"})
    resolution = (plan.get("assurance") or {}).get("intent_resolution") or {}
    reading = plan.get("reading_plan") or {}
    return {
        "actions": actions,
        "missing_action_count": sum(x["disposition"] == "missing_unjustified" for x in actions),
        "safety_conflicts": conflicts,
        "selected_intents": list(selected),
        "pause_state": pause,
        "delivery_scope": plan.get("delivery_scope"),
        "module_names": list(modules),
        "ordered_gate_names": [g.get("name") for g in gates],
        "terminal_outputs": list(plan.get("terminal_outputs", [])),
        "missing_prerequisites": list(plan.get("missing_prerequisites", [])),
        "assurance_status": (plan.get("assurance") or {}).get("status"),
        "candidate_keywords": [
            {"intent": row.get("intent"), "score": row.get("score"),
             "keywords": row.get("matched_keywords")}
            for row in resolution.get("inferred_candidates", [])
        ],
        "reading_profile": reading.get("profile"),
        "reading_status": reading.get("status"),
    }


def timed_summary(samples: list[float]) -> dict[str, Any]:
    if not samples:
        raise ValueError("elapsed samples cannot be empty")
    ordered = sorted(samples)
    return {"count": len(ordered), "median_seconds": statistics.median(ordered),
            "nearest_rank_p95_seconds": ordered[max(0, math.ceil(.95 * len(ordered)) - 1)],
            "note": "cold subprocess samples, exploratory small-N; not task or user latency"}


def read_first_chunk(root: Path, commit: str, plan_yaml: str,
                     plan: dict[str, Any], path: str) -> dict[str, Any]:
    rows = [x for x in plan["reading_plan"].get("read_now", [])
            if isinstance(x, dict) and x.get("path") == path and x.get("origin", "skill") == "skill"]
    if len(rows) != 1:
        raise ValueError(f"G1B source sample not uniquely selected in read_now: {path}")
    with tempfile.TemporaryDirectory(prefix="hsk-g1b-readonly-") as temp:
        planfile = Path(temp) / "plan.yaml"
        planfile.write_text(plan_yaml, encoding="utf-8")
        cmd = [sys.executable, str(root / "scripts/read_stage.py"),
               "--plan", str(planfile), "--root", str(root),
               "--source-commit", commit, "--surface", "read_now",
               "--path", path, "--chunk-index", "0", "--chunk-lines", "120"]
        proc, elapsed = run_cmd(cmd, root)
        if proc.returncode:
            raise RuntimeError(f"G1B Stage Reader sample failed: {proc.stderr[-1200:]}")
        result = json.loads(proc.stdout)
    if (result.get("status") != "source_text_returned_not_stage_or_gate_passed"
            or result.get("gate_status") != "not_executed_by_reader"
            or result.get("source_identity", {}).get("selected_commit") != commit
            or result.get("source_identity", {}).get("sha256") != rows[0].get("sha256")):
        raise RuntimeError("source sample returned a mismatched provenance or Gate status")
    chunk = result["returned_chunk"]
    return {
        "path": path, "source_sha256": result["source_identity"]["sha256"],
        "selected_commit": commit, "status": "first_chunk_only_no_gate_executed",
        "stdout_transport_bytes": len(proc.stdout.encode("utf-8")),
        "actual_returned_source_text_bytes": len(chunk["text"].encode("utf-8")),
        "chunk_count_in_source": result["chunk_count"],
        "required_ranges": result["required_ranges"],
        "returned_range": [chunk["start_line"], chunk["end_line"]],
        "coverage_complete_with_this_chunk": bool(result["all_required_ranges_returned_in_this_response"]),
        "wall_seconds": elapsed, "not_measured": ["host_consumption", "real_token_count", "other_chunks",
                                                 "conditional_reads", "writing_stage_reads"],
    }


def collect(root: Path, corpus: Path, repeats: int = 3) -> dict[str, Any]:
    if not 1 <= repeats <= 5:
        raise ValueError("G1B cold subprocess repeats must be 1..5")
    root = root.resolve(strict=True)
    cases = validate_cases(corpus.resolve(strict=True))
    sha = githash(root)
    output = []
    for case in cases:
        plan, yaml_text, first = invoke(root, case)
        durations = [first]
        for _ in range(repeats - 1):
            repeated, _, elapsed = invoke(root, case)
            # Cross-run identity is part of measurement validity.
            if (repeated.get("intents") != plan.get("intents")
                    or repeated.get("pause_state") != plan.get("pause_state")
                    or repeated.get("pre_delivery_gates") != plan.get("pre_delivery_gates")):
                raise RuntimeError(f"G1B nondeterministic plan: {case['id']}")
            durations.append(elapsed)
        observed = observed_actions(case, plan)
        sample = (read_first_chunk(root, sha, yaml_text, plan, case["read_sample_path"])
                  if case.get("read_sample_path") else None)
        metrics = (plan["reading_plan"] or {}).get("metrics") or {}
        output.append({
            "id": case["id"], "category": case["category"], "request": case["request"],
            "oracle": {
                "positive_actions": case["positive_actions"],
                "negative_intents": case.get("negative_intents", []),
                "informational_mentions": case.get("informational_mentions", []),
                "targets": case.get("targets", []),
                "dependencies": case.get("dependencies", []),
            },
            "observed": observed,
            "measured": {
                "resolver_cold_subprocess": timed_summary(durations),
                "resolver_stdout_bytes": len(yaml_text.encode("utf-8")),
                "planned_initial_skill_read_bytes": metrics.get("planned_skill_read_bytes"),
                "planned_initial_project_read_bytes": metrics.get("planned_project_read_bytes"),
                "bounded_reader_sample": sample,
                "actual_read_tokens": None,
                "full_task_consumed_bytes": None,
            },
        })
    if githash(root) != sha:
        raise RuntimeError("G1B repository checkout changed during measurement")
    findings = [row["id"] for row in output if row["observed"]["missing_action_count"]]
    unsafe = [row["id"] for row in output if row["observed"]["safety_conflicts"]]
    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": "diagnostic_only_no_runtime_authority",
        "source_commit": sha,
        "driver_sha256": sha256(Path(__file__).read_bytes()),
        "oracle_sha256": sha256(corpus.read_bytes()),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "case_count": len(output),
        "diagnostic_missing_action_cases": findings,
        "safety_conflict_cases": unsafe,
        "status": "blocked_safety_conflict" if unsafe else
                  "diagnostic_action_gaps" if findings else "no_gap_observed_in_synthetic_scope",
        "not_measured": ["model_tokens", "GitHub_only_UI_tool_calls", "complete_task_latency",
                         "actual_full_policy_consumption", "real_project_model_correctness"],
        "executed_model_or_user_project": False,
        "gate_pass_granted": False,
        "cases": output,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--oracle", type=Path, default=Path(__file__).parent / "fixtures/v10270_action_oracle.yaml")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = collect(args.repo_root, args.oracle, args.repeats)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({
        "status": result["status"], "source_commit": result["source_commit"],
        "case_count": result["case_count"],
        "missing_action_cases": result["diagnostic_missing_action_cases"],
        "safety_conflict_cases": result["safety_conflict_cases"],
        "note": "G1B observational only: current gaps do not self-authorize a Router patch",
    }, ensure_ascii=False))
    # Missing actions are characterized findings for G2, not test-baseline failures.
    return 1 if result["safety_conflict_cases"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
