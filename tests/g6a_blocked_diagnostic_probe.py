#!/usr/bin/env python3
"""G6-A read-only diagnostic-scope admission: observe, never enable shortcut.

A current Resolver pause/evidence requirement can justify explaining the blocker,
but not authorize smaller rule consumption, a Gate result, a project write, or
model/figure modification. This test-only probe records that distinction.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
from resolve_runtime import resolve_runtime
from reading_plan_cases import build_project
from v10270_action_observation import validate_cases

MODEL_APPROVAL_AUTHORITY = "core/model_approval_contract.yaml"
FIGURE_AUTHORITY = "modules/04_figure_evidence.md"
ORACLE = "tests/fixtures/v10270_action_oracle.yaml"
PROJECT_CASES = (
    ("old_figure_approval_missing", "no_figure_approval", "只改配色和线宽。"),
    ("old_figure_current", "current", "只改配色和线宽。"),
    ("old_figure_source_drift", "figure_drift", "只改配色和线宽。"),
    ("figure_semantic_change", "current", "只改配色，同时对数据平滑。"),
    ("mixed_old_figure_and_new_design", "no_figure_approval",
     "只修改现有图的配色，另外补充一张新图，保持数据和坐标口径不变。"),
)


def git_head(root: Path) -> str:
    p = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                       capture_output=True, text=True, check=True)
    sha = p.stdout.strip()
    if len(sha) != 40 or any(char not in "0123456789abcdef" for char in sha):
        raise ValueError("unknown current Skill commit")
    return sha


def file_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*")) if path.is_file()
    }


def safe_origin_identity(root: Path, commit: str, rows: list[dict[str, Any]]
                         ) -> list[dict[str, Any]]:
    """Bind candidate *planned* source ranges to real immutable Skill bytes."""
    seen = set()
    identities = []
    for row in rows:
        path = row.get("path")
        if (row.get("origin", "skill") != "skill" or not isinstance(path, str)
                or not isinstance(row.get("sha256"), str)
                or not isinstance(row.get("ranges"), list)):
            raise ValueError("G6-A candidate lacks Skill source and range identity")
        key = (path, row["sha256"])
        if key in seen:
            raise ValueError("duplicated diagnostic source identity")
        seen.add(key)
        source = (root / path).resolve()
        if not source.is_relative_to(root) or not source.is_file():
            raise ValueError("invalid diagnostic source path")
        raw = source.read_bytes()
        if sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError("diagnostic source drift relative to plan")
        committed = subprocess.run(["git", "-C", str(root), "show", f"{commit}:{path}"],
                                   capture_output=True, check=False)
        if committed.returncode or committed.stdout != raw:
            raise ValueError("diagnostic source differs from selected Git commit")
        planned = row.get("planned_bytes")
        if type(planned) is not int or not 0 <= planned <= len(raw):
            raise ValueError("invalid diagnostic source planned byte budget")
        identities.append({
            "path": path, "source_sha256": row["sha256"], "source_commit": commit,
            "planned_bytes": planned, "original_ranges": row["ranges"],
            "source_bytes": len(raw), "resolution": row.get("resolution"),
            "fallback_reason": row.get("fallback_reason"),
        })
    return identities


def diagnostic_guard(case_id: str, plan: dict[str, Any]) -> tuple[bool, str, str | None]:
    """No heuristics may turn an unknown scope or a partial action into a block."""
    assurance = plan.get("assurance") or {}
    reading = plan.get("reading_plan") or {}
    if assurance.get("status") != "pass":
        return False, "assurance_not_passed", None
    if case_id == "model_approval_pending":
        if (list(plan.get("intents", [])) == ["full_solution"]
                and plan.get("pause_state") == "awaiting_model_approval"
                and plan.get("pause_for_model_approval")
                and not ((assurance.get("context") or {}).get("project_state_loaded"))):
            return True, "primary_code_delivery_paused_pending_model_approval", MODEL_APPROVAL_AUTHORITY
        return False, "model_approval_block_not_established", None
    if case_id == "old_figure_approval_missing":
        reasons = " | ".join(str(x).lower() for x in reading.get("reasons", []))
        if (list(plan.get("intents", [])) == ["figures"]
                and reading.get("status") == "evidence_required"
                and reading.get("profile") == "full"
                and ("approval" in reasons or "approved" in reasons)
                and (assurance.get("context") or {}).get("project_state_loaded")):
            return True, "old_figure_style_evidence_missing", FIGURE_AUTHORITY
        return False, "old_figure_approval_block_not_established", None
    return False, "negative_or_partially_executable_case", None


def observe(case_id: str, plan: dict[str, Any], root: Path,
            commit: str, before_project: dict[str, str] | None = None,
            project_root: Path | None = None) -> dict[str, Any]:
    eligible, reason, source = diagnostic_guard(case_id, plan)
    reading = plan.get("reading_plan") or {}
    current_rows = reading.get("read_now") or []
    if not isinstance(current_rows, list):
        raise ValueError("reading_plan.read_now must be a list")
    candidates = [row for row in current_rows if isinstance(row, dict)
                  and row.get("path") == source and row.get("origin", "skill") == "skill"] if eligible else []
    if len(candidates) != (1 if eligible else 0):
        # Do not search or manufacture an undeclared rule to justify narrowing.
        eligible = False
        reason = "diagnostic_authority_not_uniquely_in_current_read_now"
        candidates = []
    identities = safe_origin_identity(root, commit, candidates)
    if before_project is not None:
        if project_root is None or file_hashes(project_root) != before_project:
            raise RuntimeError("G6-A Resolver or evidence probe mutated synthetic project")
    declared_total = (reading.get("metrics") or {}).get("planned_skill_read_bytes")
    if type(declared_total) is not int or declared_total < 0:
        raise ValueError("invalid complete plan byte accounting")
    candidate_bytes = sum(item["planned_bytes"] for item in identities)
    if candidate_bytes > declared_total:
        raise ValueError("diagnostic candidate not bounded by full planned read")
    return {
        "case_id": case_id, "current_assurance": (plan.get("assurance") or {}).get("status"),
        "reading_profile": reading.get("profile"), "reading_status": reading.get("status"),
        "reading_reasons": list(reading.get("reasons") or []),
        "effective_pause": plan.get("pause_state"),
        "effective_intents": list(plan.get("intents", [])),
        "machine_gates": [x.get("name") for x in plan.get("pre_delivery_gates", [])],
        "diagnostic_scope_guard_observed": eligible,
        "guard_reason": reason,
        "candidate_source_identity": identities,
        "original_planned_skill_bytes": declared_total,
        "preview_candidate_bytes": candidate_bytes,
        "potential_display_byte_difference_not_actual_cost": declared_total - candidate_bytes if eligible else None,
        "complete_action_reading_preserved": True,
        "diagnostic_scope_admitted_to_production": False,
        "gate_execution": False, "stage_execution": False,
        "current_project_write": False,
    }


def collect(root: Path) -> dict[str, Any]:
    root = root.resolve(strict=True)
    if root != ROOT:
        raise ValueError("G6-A probe must run from candidate worktree")
    commit = git_head(root)
    oracle = validate_cases(root / ORACLE)
    entry = next((item for item in oracle if item["id"] == "unapproved_solver_gate"), None)
    if not entry or entry.get("explicit_intents") != ["full_solution"]:
        raise ValueError("independent model-approval oracle missing")
    cases: list[dict[str, Any]] = []
    model = resolve_runtime(
        "full_solution", request=entry["request"], competition=entry["competition"]
    )
    cases.append(observe("model_approval_pending", model, root, commit))
    for case_id, mode, request in PROJECT_CASES:
        with tempfile.TemporaryDirectory(prefix="hsk-g6a-synthetic-") as tmp:
            project = Path(tmp)
            build_project(root, project, mode)
            before = file_hashes(project)
            plan = resolve_runtime(
                "figures", request=request, competition="CUMCM",
                project_root=project, question="Q1",
            )
            cases.append(observe(case_id, plan, root, commit, before, project))
    if git_head(root) != commit:
        raise RuntimeError("G6-A checkout changed during measurement")
    if not any(c["diagnostic_scope_guard_observed"] for c in cases):
        raise AssertionError("G6-A has no reproducible blocked diagnostic candidate")
    if any(c["diagnostic_scope_admitted_to_production"] for c in cases):
        raise AssertionError("G6-A tests cannot authorize diagnostic-only runtime")
    return {
        "schema_version": 1, "source_commit": commit,
        "driver_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "oracle_sha256": sha256((root / ORACLE).read_bytes()).hexdigest(),
        "measurement_type": "synthetic_G6A_blocker_source_preview_not_actual_consumption",
        "cases": cases, "production_runtime_changed": False,
        "not_measured": [
            "real_ChatGPT_source_tokens", "project_user_approval",
            "actual_diagnostic_completeness", "human_model_challenge",
            "user_execution", "review_receipts", "real_user_latency",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo_root.resolve(strict=True)
    output = args.output.resolve()
    if root == output or root in output.parents:
        raise ValueError("G6-A report may not be written inside repository")
    report = collect(root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True,
                                     indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "read_only_admission_evidence_without_action_shortcut",
        "source_commit": report["source_commit"],
        "case_guards": {x["case_id"]: x["guard_reason"] for x in report["cases"]},
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
