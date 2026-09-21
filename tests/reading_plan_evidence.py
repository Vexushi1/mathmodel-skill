"""Compare legacy plans across isolated checkouts; report exact approved changes separately and reject every unregistered Runtime field difference."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path

from reading_plan_cases import CASES, build_project

HERE = Path(__file__).resolve()
ALLOWED_CHANGED_AUTHORITIES = {
    "core/bootstrap.yaml",
    "core/workflow_router.yaml",
    "core/runtime_assurance_contract.yaml",
    "core/module_manifest.yaml",
    "core/writing_runtime_contract.yaml",
    "core/writing_reasoning_contract.yaml",
    "modules/05_writing/paper_writing_protocol.md",
    "templates/latex/cumcm/hsk/template_manifest.yaml",
}
P7_OPTIONAL_ANALYSIS_PREREQUISITE = "figure_evidence:result_analysis_workbook"
P9_RELEASE_VERSIONS = {"9.1.0", "9.2.0", "9.2.1", "9.3.0", "9.3.1", "9.4.0", "9.4.1", "9.4.2", "9.4.3", "9.4.4", "9.5.0", "9.5.1", "9.5.2", "9.5.3", "9.5.4", "9.5.5", "9.5.6", "9.5.7", "9.6.0", "9.6.1", "9.7.0"}
A7_HYDRATED_PROVENANCE_CASES = {
    "facts_current", "facts_model_change", "facts_ambiguous", "facts_stale_framework",
    "facts_hash_drift", "facts_identity_drift", "facts_stale_dependency", "style_current",
    "style_data_change", "style_figure_drift", "style_no_approval", "mixed",
}


def normalize(value, repo, project):
    if isinstance(value, dict):
        return {key: normalize(item, repo, project) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize(item, repo, project) for item in value]
    if isinstance(value, str):
        return value.replace(str(project), "<PROJECT_ROOT>").replace(str(repo), "<SKILL_ROOT>")
    return value


def legacy_projection(plan):
    value = deepcopy(plan)
    value.pop("reading_plan", None)
    if value.get("version") in P9_RELEASE_VERSIONS:
        value["version"] = "<EXPECTED_P9_RELEASE_CARRIER_CHANGE>"
    fingerprint = value["assurance"]["authority_fingerprint"]
    fingerprint["sha256"] = "<EXPECTED_APPROVED_AUTHORITY_CHANGE>"
    for source in fingerprint["sources"]:
        if source["path"] in ALLOWED_CHANGED_AUTHORITIES:
            source["sha256"] = "<EXPECTED_APPROVED_AUTHORITY_CHANGE>"
    prerequisites = value.get("missing_prerequisites")
    if isinstance(prerequisites, list):
        value["missing_prerequisites"] = [
            item for item in prerequisites if item != P7_OPTIONAL_ANALYSIS_PREREQUISITE
        ]
    return value


def approved_a3_changes(identifier, old, new):
    """Register exact A3 transitions; never normalize an entire assurance subtree."""
    projected = deepcopy(new)
    changes = []

    def register(path, baseline, candidate, approval):
        left, right, target = old, new, projected
        try:
            for key in path[:-1]:
                left, right, target = left[key], right[key], target[key]
            key = path[-1]
            if left[key] != baseline or right[key] != candidate:
                return
        except (KeyError, IndexError, TypeError):
            return
        target[key] = deepcopy(baseline)
        changes.append({"path": ".".join(map(str, path)), "baseline": baseline,
                        "candidate": candidate, "approval": approval})

    register(("assurance", "schema_version"), "1.2.0", "1.2.1",
             "A3 approved runtime assurance contract version")
    if identifier == "facts_hash_drift":
        approval = "A3 AUD-03: changed primary workbook cannot qualify analysis or validated_results"
        evidence = ("assurance", "artifact_assurance", "evidence", 2)
        try:
            analysis_rows = [plan["assurance"]["artifact_assurance"]["evidence"][2] for plan in (old, new)]
        except (KeyError, IndexError, TypeError):
            analysis_rows = []
        if len(analysis_rows) == 2 and all(
            isinstance(row, dict) and row.get("artifact") == "accepted_result_analysis_workbook"
            and row.get("scope") == "Q1" for row in analysis_rows
        ):
            register((*evidence, "status"), "verified", "not_accepted", approval)
            register((*evidence, "reason"), "result-analysis execution and stability status are accepted",
                     "result-analysis execution or stability status is not accepted", approval)
        revoked = {"accepted_result_analysis_workbook", "result_analysis_workbook", "validated_results"}
        for path in (("assurance", "artifact_assurance", "effective_artifacts"),
                     ("available_after_modules",), ("available_after_plan",)):
            values = old
            try:
                for key in path:
                    values = values[key]
            except (KeyError, TypeError):
                continue
            if isinstance(values, list) and all(values.count(item) == 1 for item in revoked):
                register(path, values, [item for item in values if item not in revoked], approval)
    return projected, changes


def approved_a7_changes(identifier, old, new):
    """Only the measured absent-to-project_state provenance leaves are approved."""
    projected = deepcopy(new)
    changes = []
    if identifier not in A7_HYDRATED_PROVENANCE_CASES:
        return projected, changes
    try:
        left, right, target = [plan["assurance"]["context"]["field_provenance"]
                               for plan in (old, new, projected)]
    except (KeyError, TypeError):
        return projected, changes
    if not all(isinstance(item, dict) and item.get("classification") == "project_state"
               for item in (left, right)):
        return projected, changes
    for axis in ("objective", "structures", "capabilities"):
        key = f"classification.{axis}"
        if key not in left and right.get(key) == "project_state":
            del target[key]
            changes.append({
                "path": f"assurance.context.field_provenance.{key}",
                "baseline_present": False, "baseline": None, "candidate": "project_state",
                "approval": "A7 AUD-17: expose hydrated classification provenance per axis",
            })
    return projected, changes


def worker(repo, index):
    sys.path.insert(0, str(repo / "scripts"))
    from resolve_runtime import resolve_runtime
    identifier, intent, request, fixture = CASES[index]
    with tempfile.TemporaryDirectory(prefix="p2-reading-case-") as tmp:
        project = Path(tmp)
        kwargs = {"competition": "CUMCM", "request": request}
        if fixture:
            build_project(repo, project, fixture)
            kwargs.update(project_root=project, question="Q1")
        plan = resolve_runtime(intent, **kwargs)
        value = normalize(plan, repo, project)
        declared = sum(len((repo / path).read_bytes()) for path in dict.fromkeys(plan["load_order"]))
        return {"id": identifier, "plan": value, "legacy_declared_bytes": declared}


def collect(repo):
    rows = []
    for index, _ in enumerate(CASES):
        proc = subprocess.run([sys.executable, str(HERE), "--worker", str(repo), str(index)],
                              capture_output=True, text=True, encoding="utf-8", timeout=90)
        if proc.returncode:
            raise RuntimeError(proc.stderr)
        rows.append(json.loads(proc.stdout))
    return rows


def approved_solver_changes(old, new):
    """Allow only the v9.7 execution-Authority additions, retaining every old field."""
    projected = deepcopy(new)
    changes = []
    additions = {
        ("contracts",): "core/user_execution_contract.yaml",
        ("load_order",): "core/user_execution_contract.yaml",
        ("assurance", "dependency_closure", "added_paths"): "core/user_execution_contract.yaml",
        ("assurance", "dependency_closure", "required_paths"): "core/user_execution_contract.yaml",
        ("assurance", "dependency_closure", "required_aliases"): "user_execution",
    }
    source_path = ("assurance", "authority_fingerprint", "sources")
    for path in (*additions, source_path):
        left, right = old, projected
        try:
            for key in path[:-1]:
                left, right = left[key], right[key]
            previous, current = left[path[-1]], right[path[-1]]
        except (KeyError, TypeError):
            continue
        if not isinstance(previous, list) or not isinstance(current, list) or previous == current:
            continue
        if path == source_path:
            expected = {"core/user_execution_contract.yaml", "core/code_quality_contract.yaml", "core/output_contract.yaml"}
            added = [row for row in current if row.get("path") in expected]
            filtered = [row for row in current if row.get("path") not in expected]
            exact = {row.get("path") for row in added} == expected and len(added) == 3
        else:
            token = additions[path]
            filtered = [value for value in current if value != token]
            exact = token not in previous and current.count(token) == 1
        if exact and filtered == previous:
            changes.append({"path": ".".join(path), "baseline": previous, "candidate": current,
                            "approval": "v9.7 approved solver backend Authority dependency/fingerprint closure"})
            right[path[-1]] = deepcopy(previous)
    return projected, changes


def compare(before, after):
    if [r["id"] for r in before] != [r["id"] for r in after]:
        raise ValueError("Case order or identity differs")
    rows = []
    for a, b in zip(before, after):
        reading = b["plan"].get("reading_plan")
        if not reading:
            raise ValueError(f"P2 reading plan missing: {b['id']}")
        old = legacy_projection(a["plan"])
        new = legacy_projection(b["plan"])
        projected, expected = approved_a3_changes(a["id"], old, new)
        projected, a7_changes = approved_a7_changes(a["id"], old, projected)
        expected.extend(a7_changes)
        projected, solver_changes = approved_solver_changes(old, projected)
        expected.extend(solver_changes)
        changed_keys = sorted(k for k in set(old) | set(projected) if old.get(k) != projected.get(k))
        rows.append({
            "id": a["id"], "legacy_behavior_equal": old == new,
            "legacy_behavior_equal_except_approved_changes": old == projected,
            "expected_legacy_changes": expected,
            "unexpected_legacy_changes": changed_keys,
            "baseline_declared_bytes": a["legacy_declared_bytes"],
            "candidate_declared_bytes": b["legacy_declared_bytes"],
            "planned_skill_read_bytes": reading["metrics"]["planned_skill_read_bytes"],
            "planned_project_read_bytes": reading["metrics"]["planned_project_read_bytes"],
            "reading_profile": reading["profile"], "reading_status": reading["status"],
            "actual_read_tokens": None,
        })
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", nargs=2)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--baseline-ref", default="0eecaf929c83f19555402564ea0b14743d9bcf7d")
    parser.add_argument("--candidate-ref", default="working-tree")
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(Path(args.worker[0]).resolve(), int(args.worker[1])), ensure_ascii=False))
        return 0
    if not args.baseline or not args.candidate or not args.output:
        parser.error("baseline, candidate and output are required")
    before, after = collect(args.baseline.resolve()), collect(args.candidate.resolve())
    rows = compare(before, after)
    report = {
        "schema_version": 1, "baseline_ref": args.baseline_ref, "candidate_ref": args.candidate_ref,
        "driver_sha256": hashlib.sha256(HERE.read_bytes()).hexdigest(),
        "cases_sha256": hashlib.sha256(HERE.with_name("reading_plan_cases.py").read_bytes()).hexdigest(),
        "comparison_scope": "all_legacy_fields_with_declared_authority_hash_p7_prerequisite_p9_carrier_exceptions_and_explicit_a3_a7_v970_field_transitions",
        "expected_authority_changes": sorted(ALLOWED_CHANGED_AUTHORITIES),
        "all_legacy_behavior_equal": all(r["legacy_behavior_equal"] for r in rows),
        "all_legacy_behavior_equal_except_approved_changes": all(r["legacy_behavior_equal_except_approved_changes"] for r in rows),
        "interpretation": "Initial planned ranges, not actual reads/tokens or total task cost. Existing Authority hash, P7 prerequisite and registered release-carrier exceptions remain. legacy_behavior_equal is measured before the exact A3/A7/v9.7 exceptions; each approved version, qualification, per-axis provenance or solver Authority addition is visible in expected_legacy_changes. No classification value or existing list-order normalization is applied. Passing requires no unregistered field differences, not an assertion that the original behavior is unchanged.",
        "cases": rows,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in (("p2-baseline-plans.json", before), ("p2-candidate-plans.json", after), ("p2-comparison.json", report)):
        (args.output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["all_legacy_behavior_equal_except_approved_changes"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
