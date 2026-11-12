#!/usr/bin/env python3
"""G3-A experiment: characterize *presentation* bytes of the current Resolver plan.

This is an observational, maintenance-only prototype. It does not change the
Resolver, its default CLI, selected routes, any reading obligation, or Gate.
A smaller serialization is NOT proof of reduced user/model tokens or source reads.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import platform
from pathlib import Path
import statistics
import subprocess
import sys
from typing import Any

import yaml

import v10270_runtime_measurement as G1A
import v10270_action_observation as G1B

PROJECTION_SCHEMA = 1
SOURCE_KEYS = ("path", "origin", "sha256", "ranges", "selectors", "when",
               "resolution", "fallback_reason", "source_bytes", "planned_bytes")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def encoded(value: Any) -> bytes:
    """Use the SAME compact JSON serializer for both compared representations."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), default=str).encode("utf-8")


def source_projection(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        raise ValueError("reading source rows must be a list")
    result = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("path"), str) or not row["path"]:
            raise ValueError("invalid source row")
        if not isinstance(row.get("ranges"), list):
            raise ValueError("source row missing its ranges")
        result.append({key: deepcopy(row.get(key)) for key in SOURCE_KEYS})
    return result


def preview_from_plan(plan: dict[str, Any], full_plan_sha256: str) -> dict[str, Any]:
    """Compute a candidate projection; never return it as current machine truth."""
    if not isinstance(plan, dict) or not isinstance(plan.get("reading_plan"), dict):
        raise ValueError("a real machine plan and reading_plan are required")
    reading = plan["reading_plan"]
    assurance = plan.get("assurance") or {}
    context = assurance.get("context") or {}
    intent = assurance.get("intent_resolution") or {}
    writing = plan.get("writing_runtime") or {}
    gates = deepcopy(plan.get("pre_delivery_gates") or [])
    tools = deepcopy(reading.get("tool_interfaces") or [])
    if not isinstance(gates, list) or not isinstance(tools, list):
        raise ValueError("Gate contract is malformed")
    return {
        "schema_version": PROJECTION_SCHEMA,
        "role": "experiment_only_not_executable_not_a_consumption_or_gate_certificate",
        "machine_plan_sha256": full_plan_sha256,
        "version": plan.get("version"),
        "selected_intents": deepcopy(plan.get("intents")),
        "intent_diagnostics": {
            "mode": intent.get("mode"), "ambiguity": intent.get("ambiguity"),
            "selection_reason": intent.get("selection_reason"),
        },
        "scope": plan.get("delivery_scope"),
        "modules": deepcopy(plan.get("modules")),
        "pause_state": plan.get("pause_state"),
        "missing_prerequisites": deepcopy(plan.get("missing_prerequisites")),
        "terminal_outputs": deepcopy(plan.get("terminal_outputs")),
        "assurance": {
            "status": assurance.get("status"),
            "conflicts": deepcopy(context.get("conflicts")),
            "ambiguities": deepcopy(context.get("ambiguities")),
            "question": context.get("question"),
            "field_provenance": deepcopy(context.get("field_provenance")),
            "artifact_evidence": deepcopy((assurance.get("artifact_assurance") or {}).get("evidence")),
        },
        "authority_fingerprint": deepcopy(
            (assurance.get("authority_fingerprint") or {}).get("sha256")
        ),
        "read": {
            "profile": reading.get("profile"), "status": reading.get("status"),
            "reasons": deepcopy(reading.get("reasons")),
            "read_now": source_projection(reading.get("read_now", [])),
            "conditional": source_projection(reading.get("conditional", [])),
            "project_snapshot": deepcopy(reading.get("project_snapshot")),
        },
        # Preserve the complete ordered Gate contracts in the experiment. No
        # actual execution evidence is generated here.
        "pre_delivery_gates": gates,
        "tool_interfaces": tools,
        "writing": {
            "mode": writing.get("mode"), "contract": writing.get("contract"),
            "stages": [x.get("id") for x in writing.get("authoring_sequence", [])
                       if isinstance(x, dict)],
            "requires_original_authoring_sequence": bool(writing),
        },
        "status_boundaries": {
            "source_text_returned": False,
            "full_rule_consumption_proved": False,
            "gate_executed_or_passed": False,
            "approved_or_accepted_artifact": False,
            "project_writes_performed": False,
            "not_a_replacement_for_machine_plan": True,
        },
    }


def prove_presentation_subset(plan: dict[str, Any], view: dict[str, Any]) -> None:
    """Verify every proposed displayed read row and Gate comes from the plan."""
    reading = plan["reading_plan"]
    for key in ("read_now", "conditional"):
        expected = source_projection(reading.get(key, []))
        observed = view["read"][key]
        if expected != observed:
            raise ValueError(f"unfaithful displayed source row: {key}")
    for key in ("intents", "modules", "pause_state", "delivery_scope",
                "missing_prerequisites", "terminal_outputs"):
        target = {"intents": "selected_intents", "delivery_scope": "scope"}.get(key, key)
        if plan.get(key) != view.get(target):
            raise ValueError(f"unfaithful displayed machine field: {key}")
    if plan.get("pre_delivery_gates", []) != view["pre_delivery_gates"]:
        raise ValueError("ordered Gate contracts must be preserved exactly")
    if (reading.get("tool_interfaces", []) != view["tool_interfaces"] or
            (plan.get("assurance") or {}).get("status") != view["assurance"]["status"]):
        raise ValueError("tool interface or assurance status changed")
    original = (plan.get("assurance") or {}).get("authority_fingerprint") or {}
    if original.get("sha256") != view["authority_fingerprint"]:
        raise ValueError("current Authority fingerprint was lost")
    boundary = view["status_boundaries"]
    if any(value is True for key, value in boundary.items()
           if key != "not_a_replacement_for_machine_plan"):
        raise ValueError("experimental view cannot grant source, Gate, or artifact status")


def cases_from_existing(root: Path) -> list[dict[str, Any]]:
    """Use only established synthetic requests; never fetch actual user tasks."""
    g1a = G1A.load_cases(root / "tests/fixtures/v10270_runtime_cases.yaml")
    g1b = G1B.validate_cases(root / "tests/fixtures/v10270_action_oracle.yaml")
    examples = []
    for tag, cases in (("g1a", g1a), ("g1b", g1b)):
        for row in cases:
            examples.append({
                "id": f"{tag}::{row['id']}",
                "request": row.get("request", ""),
                "competition": row.get("competition", "CUMCM"),
                "intents": row.get("intents", row.get("explicit_intents", [])),
            })
    ids = [row["id"] for row in examples]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate experimental case ID")
    return examples


def run_resolver(root: Path, row: dict[str, Any]) -> tuple[dict[str, Any], bytes]:
    command = [sys.executable, str(root / "scripts/resolve_runtime.py"),
               *row["intents"], "--competition", row["competition"]]
    if row["request"]:
        command.extend(["--request", row["request"]])
    p = subprocess.run(command, cwd=root, capture_output=True, text=True,
                       encoding="utf-8", timeout=120, check=False)
    if p.returncode:
        raise RuntimeError(f"case {row['id']}: {p.stderr[-600:]}")
    plan = yaml.safe_load(p.stdout)
    if not isinstance(plan, dict):
        raise ValueError("machine Resolver returned no plan")
    return plan, p.stdout.encode("utf-8")


def collect(root: Path) -> dict[str, Any]:
    root = root.resolve(strict=True)
    head = G1A.git_head(root)
    rows = []
    for row in cases_from_existing(root):
        plan, stdout = run_resolver(root, row)
        full_bytes = encoded(plan)
        slim = preview_from_plan(plan, digest(stdout))
        prove_presentation_subset(plan, slim)
        slim_bytes = encoded(slim)
        rows.append({
            "id": row["id"],
            "selected_intents": deepcopy(plan.get("intents")),
            "read_profile": (plan.get("reading_plan") or {}).get("profile"),
            "full_plan_json_bytes": len(full_bytes),
            "experimental_view_json_bytes": len(slim_bytes),
            "actual_original_yaml_stdout_bytes": len(stdout),
            "potential_presentation_byte_reduction": len(full_bytes)-len(slim_bytes),
            "potential_presentation_byte_ratio": round(
                1 - len(slim_bytes)/len(full_bytes), 5),
            "read_now_rows_preserved": len(slim["read"]["read_now"]),
            "conditional_rows_preserved": len(slim["read"]["conditional"]),
            "ordered_gate_count_preserved": len(slim["pre_delivery_gates"]),
            "candidate_is_read_only": True,
        })
    if G1A.git_head(root) != head:
        raise RuntimeError("Git checkout changed during measurement")
    ratios = [row["potential_presentation_byte_ratio"] for row in rows]
    return {
        "schema_version": PROJECTION_SCHEMA,
        "source_commit": head,
        "test_driver_sha256": digest(Path(__file__).read_bytes()),
        "cases": rows,
        "summary": {
            "case_count": len(rows),
            "total_full_json_bytes": sum(x["full_plan_json_bytes"] for x in rows),
            "total_candidate_json_bytes": sum(x["experimental_view_json_bytes"] for x in rows),
            "median_byte_ratio": round(statistics.median(ratios), 5),
            "cases_with_smaller_presentation": sum(x["potential_presentation_byte_reduction"]>0
                                                   for x in rows),
        },
        "scope": "projection_bytes_only_same_json_serializer; no production UI/CLI change",
        "not_measured": ["actual_chatgpt_token_consumption", "source_text_read_reduction",
                         "GitHub_only_user_latency", "G3B_batch_runtime"],
        "execution_status": "measurement_only_no_gate_or_project_writes",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    report = collect(args.repo_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True)+"\n",
                           encoding="utf-8")
    print(json.dumps({"output": str(args.output), "summary": report["summary"],
                      "measured": report["scope"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
