#!/usr/bin/env python3
"""G1A: same-driver v10.27.0 vs candidate characterization; never a project gate."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from time import perf_counter
from typing import Any

import yaml

BASELINE = "5b7828ec0ae41dc97c095cd62d43f889596bd646"
SCHEMA = 1
CASE_KEYS = {"id", "request", "intents", "competition", "objective", "solver_backend"}
BEHAVIOR_KEYS = (
    "intents", "modules", "load_order", "delivery_scope", "pause_state",
    "formal_delivery", "terminal_outputs", "pre_delivery_gates",
    "missing_inputs", "missing_prerequisites", "task_code_execution_allowed",
    "pause_for_model_approval", "pause_for_user_execution",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_cases(path: Path) -> list[dict[str, Any]]:
    value = yaml.safe_load(path.read_bytes())
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA:
        raise ValueError("unsupported G1A case schema")
    if set(value) != {"schema_version", "cases"}:
        raise ValueError("unexpected G1A case corpus fields")
    cases = value["cases"]
    if not isinstance(cases, list) or not cases:
        raise ValueError("G1A case corpus must be nonempty")
    ids = []
    for row in cases:
        if not isinstance(row, dict) or not set(row) <= CASE_KEYS:
            raise ValueError("invalid G1A case fields")
        if not isinstance(row.get("id"), str) or not row["id"]:
            raise ValueError("G1A case ID must be a nonempty string")
        ids.append(row["id"])
        intents = row.get("intents", [])
        if not isinstance(intents, list) or any(not isinstance(x, str) or not x for x in intents):
            raise ValueError("G1A intents must be a list of names")
        if not intents and not row.get("request"):
            raise ValueError("G1A case must provide a request or explicit intent")
        for key in ("request", "competition", "objective", "solver_backend"):
            if key in row and not isinstance(row[key], str):
                raise ValueError("G1A case optional values must be text")
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate G1A case IDs")
    return cases


def git_head(root: Path) -> str:
    p = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                       capture_output=True, text=True, check=True)
    return p.stdout.strip()


def source_rows(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    return [
        {key: row.get(key) for key in ("path", "ranges", "selectors", "when", "resolution", "origin")}
        for row in rows if isinstance(row, dict)
    ]


def projection(plan: dict[str, Any]) -> dict[str, Any]:
    assurance = plan.get("assurance") or {}
    reading = plan.get("reading_plan") or {}
    intent = assurance.get("intent_resolution") or {}
    runtime = plan.get("runtime_plan") or {}
    writing = runtime.get("writing_runtime") or {}
    return {
        **{key: plan.get(key) for key in BEHAVIOR_KEYS},
        "assurance_status": assurance.get("status"),
        "selected_intents": intent.get("selected_intents"),
        "intent_ambiguity": intent.get("ambiguity"),
        "intent_mode": intent.get("mode"),
        "reading_profile": reading.get("profile"),
        "reading_status": reading.get("status"),
        "reading_reasons": reading.get("reasons"),
        "read_now": source_rows(reading.get("read_now")),
        "conditional": source_rows(reading.get("conditional")),
        "tool_interfaces": [
            {key: item.get(key) for key in ("name", "path", "command", "delivery_scope", "read_only")}
            for item in reading.get("tool_interfaces", []) if isinstance(item, dict)
        ],
        "writing_mode": writing.get("mode"),
        "writing_stage_ids": [
            item.get("id") for item in writing.get("authoring_sequence", []) if isinstance(item, dict)
        ],
        "solver_selection": runtime.get("solver_backend"),
    }


def measure_one(root: Path, case: dict[str, Any]) -> dict[str, Any]:
    command = [sys.executable, str(root / "scripts" / "resolve_runtime.py"), *case.get("intents", [])]
    for key, option in (("request", "--request"), ("competition", "--competition"),
                        ("objective", "--objective"), ("solver_backend", "--solver-backend")):
        if key in case:
            command.extend((option, case[key]))
    started = perf_counter()
    p = subprocess.run(command, cwd=root, capture_output=True, text=True,
                       encoding="utf-8", timeout=120)
    elapsed = perf_counter() - started
    if p.returncode:
        raise RuntimeError(f"G1A case {case['id']} failed ({p.returncode}): {p.stderr[-1500:]}")
    plan = yaml.safe_load(p.stdout)
    if not isinstance(plan, dict):
        raise ValueError("resolver did not return a plan")
    evidence = (plan.get("assurance") or {}).get("authority_fingerprint") or {}
    metrics = (plan.get("reading_plan") or {}).get("metrics") or {}
    return {
        "id": case["id"],
        "behavior": projection(plan),
        "source_identity": {
            "authority_sha256": evidence.get("sha256"),
            "sources": evidence.get("sources"),
            "skill_version": plan.get("version"),
        },
        "measurement": {
            "resolver_wall_seconds": elapsed,
            "resolver_stdout_bytes": len(p.stdout.encode("utf-8")),
            "planned_skill_read_bytes": metrics.get("planned_skill_read_bytes"),
            "planned_project_read_bytes": metrics.get("planned_project_read_bytes"),
            "actual_returned_read_bytes": None,
            "actual_read_tokens": None,
            "interpretation": "subprocess plan characterization, not source consumption or task latency",
        },
    }


def collect(root: Path, corpus: Path, driver: Path | None = None) -> dict[str, Any]:
    root = root.resolve(strict=True)
    corpus = corpus.resolve(strict=True)
    driver = (driver or Path(__file__)).resolve(strict=True)
    cases = load_cases(corpus)
    before = git_head(root)
    rows = [measure_one(root, row) for row in cases]
    if git_head(root) != before:
        raise RuntimeError("repository commit changed during G1A measurement")
    return {
        "schema_version": SCHEMA, "method": "same_driver_nonregression_characterization",
        "source_commit": before, "driver_sha256": digest(driver.read_bytes()),
        "cases_sha256": digest(corpus.read_bytes()),
        "python_version": platform.python_version(), "platform": platform.platform(),
        "cases": rows,
    }


def differences(a: Any, b: Any, prefix: str = "") -> list[dict[str, Any]]:
    if isinstance(a, dict) and isinstance(b, dict):
        result: list[dict[str, Any]] = []
        for key in sorted(set(a) | set(b)):
            result.extend(differences(a.get(key), b.get(key), f"{prefix}.{key}" if prefix else key))
        return result
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        result = []
        for index, (left, right) in enumerate(zip(a, b)):
            result.extend(differences(left, right, f"{prefix}[{index}]"))
        return result
    return [] if a == b else [{"path": prefix, "before": a, "after": b}]


def approved_changes(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA:
        raise ValueError("unsupported approval manifest")
    rows = data.get("approved_behavior_deltas")
    if not isinstance(rows, list):
        raise ValueError("approved_behavior_deltas must be an array")
    seen = set()
    for row in rows:
        required = {"case_id", "path", "before", "after", "reason", "authorization", "test_id"}
        if not isinstance(row, dict) or set(row) != required:
            raise ValueError("approval must specify exact delta and provenance")
        key = (row["case_id"], row["path"])
        if key in seen or not all(isinstance(row[x], str) and row[x].strip()
                                  for x in ("case_id", "path", "reason", "authorization", "test_id")):
            raise ValueError("duplicate or incomplete approval")
        if "*" in row["path"] or row["path"].startswith("source_identity"):
            raise ValueError("wildcard/source identity approval is not a behavior delta")
        seen.add(key)
    return rows


def approved_source_span_migrations(path: Path | None) -> dict[str, Any] | None:
    """Accept only a complete, version-pinned source-span migration declaration."""
    if path is None:
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(data, dict) or set(data) != {
        "schema_version", "scope", "version", "authorizing_reason",
        "required_case_ids", "migrations",
    } or data["schema_version"] != SCHEMA
        or data["scope"] != "v10.28.0_p1_source_only_read_ranges"
        or data["version"] != "10.28.0"
        or not isinstance(data["authorizing_reason"], str)
        or not data["authorizing_reason"]
        or not isinstance(data["required_case_ids"], list)
        or not isinstance(data["migrations"], list)
        or len(data["migrations"]) != 1):
        raise ValueError("unsupported source span migration manifest")
    expected_paths = {"core/workflow_router.yaml"}
    paths = [item.get("path") for item in data["migrations"] if isinstance(item, dict)]
    if set(paths) != expected_paths or len(paths) != 1:
        raise ValueError("source span migration must bind exactly the current router authority")
    for item in data["migrations"]:
        if set(item) != {
            "path", "baseline_sha256", "candidate_sha256",
            "old_ranges", "new_ranges",
        } or any(not isinstance(item[key], str) or len(item[key]) != 64
                 for key in ("baseline_sha256", "candidate_sha256")):
            raise ValueError("source span migration identity is incomplete")
        if item["old_ranges"] == item["new_ranges"]:
            raise ValueError("source span migration is not a change")
        actual = digest((Path(__file__).resolve().parents[1] / item["path"]).read_bytes())
        if actual != item["candidate_sha256"]:
            raise ValueError("source span migration candidate bytes changed")
    return data


def project_exact_approved_source_spans(
    old_case: dict[str, Any], new_case: dict[str, Any],
    manifest: dict[str, Any] | None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Rebase only exact, hash-pinned physical spans; leave all real source evidence intact."""
    if manifest is None:
        return new_case["behavior"], []
    if new_case["source_identity"].get("skill_version") != manifest["version"]:
        raise ValueError("source span migration release identity drift")
    before_rows = old_case["behavior"].get("read_now")
    after_rows = new_case["behavior"].get("read_now")
    if not isinstance(before_rows, list) or not isinstance(after_rows, list):
        raise ValueError("source span migration requires readable actual read_now")
    expected = deepcopy(new_case["behavior"])
    replacements = []
    for item in manifest["migrations"]:
        path = item["path"]
        for source, wanted in (
            (old_case, item["baseline_sha256"]),
            (new_case, item["candidate_sha256"]),
        ):
            rows = source["source_identity"].get("sources", [])
            sha = [row["sha256"] for row in rows if row.get("path") == path]
            if sha != [wanted]:
                raise ValueError("source span migration source identity drift: " + path)
        prior = [row for row in before_rows if row.get("path") == path]
        next_rows = [row for row in expected["read_now"] if row.get("path") == path]
        if len(prior) != 1 or len(next_rows) != 1:
            raise ValueError("source span migration source occurrence drift: " + path)
        before_row, after_row = prior[0], next_rows[0]
        if (before_row.get("ranges") != item["old_ranges"]
                or after_row.get("ranges") != item["new_ranges"]):
            raise ValueError("source span migration physical span drift: " + path)
        other_before = {key: value for key, value in before_row.items() if key != "ranges"}
        other_after = {key: value for key, value in after_row.items() if key != "ranges"}
        if other_before != other_after:
            raise ValueError("source span migration changed reading semantics: " + path)
        after_row["ranges"] = deepcopy(before_row["ranges"])
        replacements.append({
            "path": path, "actual_ranges": deepcopy(item["new_ranges"]),
            "historical_ranges": deepcopy(item["old_ranges"]),
            "source_sha256": item["candidate_sha256"],
        })
    return expected, replacements


def compare(before: dict[str, Any], after: dict[str, Any],
            approvals: list[dict[str, Any]] | None = None,
            span_migrations: dict[str, Any] | None = None) -> dict[str, Any]:
    for field in ("schema_version", "driver_sha256", "cases_sha256"):
        if before.get(field) != after.get(field):
            raise ValueError(f"non-comparable G1A reports: {field}")
    if before.get("source_commit") != BASELINE:
        raise ValueError("G1A baseline is not the frozen v10.27.0 source commit")
    left, right = before.get("cases"), after.get("cases")
    if not isinstance(left, list) or not isinstance(right, list) or (
        [row["id"] for row in left] != [row["id"] for row in right]
    ):
        raise ValueError("G1A case order/identity differs")
    if span_migrations is not None and [row["id"] for row in left] != span_migrations["required_case_ids"]:
        raise ValueError("source span migration case identities differ from pinned corpus")
    allowed = {(row["case_id"], row["path"]): row for row in (approvals or [])}
    matched: set[tuple[str, str]] = set()
    results = []
    for a, b in zip(left, right):
        compared_behavior, approved_spans = project_exact_approved_source_spans(
            a, b, span_migrations,
        )
        diffs = differences(a["behavior"], compared_behavior)
        unapproved = []
        for diff in diffs:
            token = (a["id"], diff["path"])
            approval = allowed.get(token)
            if approval and approval["before"] == diff["before"] and approval["after"] == diff["after"]:
                matched.add(token)
            else:
                unapproved.append(diff)
        results.append({
            "id": a["id"], "behavior_deltas": diffs, "unapproved_behavior_deltas": unapproved,
            "exact_source_span_migrations": approved_spans,
            "source_identity_changed": a["source_identity"] != b["source_identity"],
            "source_identity_before": a["source_identity"],
            "source_identity_after": b["source_identity"],
            "baseline_measurement": a["measurement"], "candidate_measurement": b["measurement"],
        })
    unused = sorted(set(allowed) - matched)
    if unused:
        raise ValueError(f"unused or mismatched approved deltas: {unused}")
    failures = sum(len(row["unapproved_behavior_deltas"]) for row in results)
    return {
        "schema_version": SCHEMA, "status": "pass" if failures == 0 else "blocked",
        "baseline_commit": before["source_commit"], "candidate_commit": after["source_commit"],
        "driver_sha256": before["driver_sha256"], "cases_sha256": before["cases_sha256"],
        "approved_delta_count": len(matched), "unapproved_delta_count": failures,
        "cases": results,
        "boundary": "source SHA changes are observed, never auto-approved or treated as gate success",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    capture = sub.add_parser("capture")
    capture.add_argument("--root", type=Path, required=True)
    capture.add_argument("--cases", type=Path, required=True)
    capture.add_argument("--output", type=Path, required=True)
    comp = sub.add_parser("compare")
    comp.add_argument("--baseline-report", type=Path, required=True)
    comp.add_argument("--candidate-report", type=Path, required=True)
    comp.add_argument("--approvals", type=Path)
    comp.add_argument("--source-span-migrations", type=Path)
    comp.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.action == "capture":
        result = collect(args.root, args.cases)
    else:
        before = json.loads(args.baseline_report.read_text(encoding="utf-8"))
        after = json.loads(args.candidate_report.read_text(encoding="utf-8"))
        result = compare(
            before, after, approved_changes(args.approvals),
            approved_source_span_migrations(args.source_span_migrations),
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({"action": args.action, "output": str(args.output),
                      "status": result.get("status", "captured"), "cases": len(result["cases"])}))
    return 1 if args.action == "compare" and result["status"] != "pass" else 0


if __name__ == "__main__":
    raise SystemExit(main())
