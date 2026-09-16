"""Compare complete legacy plans across isolated checkouts; report P2 planned reads separately."""
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
    "templates/latex/cumcm/hsk/template_manifest.yaml",
}
P7_OPTIONAL_ANALYSIS_PREREQUISITE = "figure_evidence:result_analysis_workbook"
P9_RELEASE_VERSIONS = {"9.1.0", "9.2.0", "9.2.1"}


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
        changed_keys = sorted(k for k in set(old) | set(new) if old.get(k) != new.get(k))
        rows.append({
            "id": a["id"], "legacy_behavior_equal": old == new,
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
        "comparison_scope": "all_legacy_fields_except_declared_approved_authority_hashes_p7_optional_analysis_prerequisite_and_p9_release_carrier",
        "expected_authority_changes": sorted(ALLOWED_CHANGED_AUTHORITIES),
        "all_legacy_behavior_equal": all(r["legacy_behavior_equal"] for r in rows),
        "interpretation": "Initial planned ranges, not actual reads/tokens or total task cost; approved authority hashes, the P7 conditional-analysis prerequisite removal, and the explicit 9.1.0-to-9.2.x release carriers are normalized while every other legacy field remains exact.",
        "cases": rows,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in (("p2-baseline-plans.json", before), ("p2-candidate-plans.json", after), ("p2-comparison.json", report)):
        (args.output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["all_legacy_behavior_equal"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
