"""Maintenance-only measurements around the real assured resolver; no task execution."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve()
DEFAULT_CASES = HERE.parent / "fixtures" / "skill_optimization_cases.yaml"
CALL_FIELDS = {
    "intents", "request", "objective", "structures", "capabilities", "primary",
    "secondary", "competition", "available_artifacts", "preprocessing_decision",
}
BEHAVIOR_FIELDS = (
    "intents", "modules", "delivery_scope", "pause_state", "formal_delivery",
    "terminal_outputs", "pre_delivery_gates", "missing_inputs",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_cases(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError("Unsupported optimization case schema")
    cases = value.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("At least one case is required")
    identifiers = [case.get("id") for case in cases if isinstance(case, dict)]
    if len(identifiers) != len(cases) or any(not isinstance(i, str) or not i for i in identifiers):
        raise ValueError("Every case needs a nonempty string id")
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Duplicate case id")
    for case in cases:
        unknown = set(case) - CALL_FIELDS - {"id", "project_fixture"}
        if unknown:
            raise ValueError(f"Unknown case fields: {sorted(unknown)}")
    return value


def read_resource(root: Path, relative: str) -> dict[str, Any]:
    """Count bytes once per source, not tokens or implied mandatory reading."""
    relative = relative.split("#", 1)[0]
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Resource escapes repository: {relative}")
    if not path.is_file():
        raise FileNotFoundError(f"Declared resource is missing: {relative}")
    data = path.read_bytes()
    text = data.decode("utf-8")
    kind = "other_text"
    for prefix, label in (
        ("core/", "contract"), ("scripts/", "executable_source"),
        ("templates/", "template"), ("modules/", "module"),
        ("packs/", "pack"), ("assets/", "asset_index"),
    ):
        if relative.startswith(prefix):
            kind = label
            break
    return {"path": relative, "bytes": len(data), "lines": len(text.splitlines()),
            "sha256": sha256(data), "kind_hint": kind}


def resource_rows(root: Path, paths: list[str]) -> list[dict[str, Any]]:
    unique = dict.fromkeys(path.split("#", 1)[0] for path in paths)
    return [read_resource(root, path) for path in unique]


def tree_identity(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): sha256(p.read_bytes())
            for p in sorted(root.rglob("*")) if p.is_file()}


def build_project(repo: Path, root: Path, mode: str) -> None:
    """Reuse an existing tested SIB fixture; never mint real user approvals."""
    helper_path = repo / "tests" / "test_v900_semantic_identity_binding.py"
    spec = importlib.util.spec_from_file_location("optimization_binding_fixture", helper_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load the existing identity fixture")
    helper = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = helper
    spec.loader.exec_module(helper)
    payload = helper.identity()
    payload["preprocessing_decision"] = "not_needed"
    question = helper.structured_question(payload)
    text = helper.framework(payload)
    if mode == "unapproved":
        question["human_model_approval_status"] = "pending"
    elif mode == "identity_drift":
        payload["objective"]["sense"] = "maximize"
        text = helper.framework(payload)
    elif mode == "wording_only":
        text = helper.framework(payload, prose="只调整 SIB 外的说明措辞。")
    elif mode == "legacy":
        text = helper.legacy_framework()
        section = helper.SEMANTIC.question_sections(text)["Q1"]
        digest = helper.SEMANTIC.inspect_question_semantics(section, "Q1")["semantic_text_hash"]
        question = {
            "model_challenge_status": "passed", "human_model_approval_status": "approved",
            "semantic_revision": 2, "approved_semantic_revision": 2,
            "semantic_hash": digest, "approved_semantic_hash": digest,
        }
    elif mode != "approved":
        raise ValueError(f"Unknown synthetic project fixture: {mode}")
    # Keep task classification fixed even when legacy mode replaces approval fields.
    question["classification"] = {
        "objective": "optimization", "structures": ["scheduling"],
    }
    question["capabilities"] = {"requires_feasibility_check": True}
    helper.write_project(root, state_question=question, framework_text=text)


def normalize(value: Any, repo: Path, project: Path | None) -> Any:
    if isinstance(value, dict):
        return {key: normalize(item, repo, project) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize(item, repo, project) for item in value]
    if isinstance(value, str):
        if project is not None:
            value = value.replace(str(project), "<PROJECT_ROOT>")
        return value.replace(str(repo), "<SKILL_ROOT>")
    return value


def measure_plan(repo: Path, case: dict[str, Any], project: Path | None) -> dict[str, Any]:
    # Each worker imports only one target checkout; baseline and candidate cannot share caches.
    sys.path.insert(0, str(repo / "scripts"))
    from resolve_runtime import resolve_runtime

    arguments = {key: value for key, value in case.items() if key in CALL_FIELDS}
    if project is not None:
        arguments.update(project_root=project, question="Q1")
    before = tree_identity(project) if project is not None else None
    plan = resolve_runtime(**arguments)
    if project is not None and tree_identity(project) != before:
        raise RuntimeError("Resolver mutated the synthetic project during read-only measurement")
    assurance = plan["assurance"]
    closure = assurance["dependency_closure"]
    declared = resource_rows(repo, plan["load_order"])
    machine = resource_rows(repo, closure["required_paths"])
    combined = resource_rows(repo, [row["path"] for row in declared + machine])
    router = yaml.safe_load((repo / "core/workflow_router.yaml").read_text(encoding="utf-8"))
    semantics = {
        intent: router["routing"][intent].get("load_semantics", "not_separately_declared")
        for intent in plan["intents"]
    }
    behavior = {key: plan.get(key) for key in BEHAVIOR_FIELDS}
    behavior["runtime_plan"] = plan["runtime_plan"]
    behavior["assurance_status"] = assurance["status"]
    behavior["context"] = assurance["context"]
    behavior["intent_resolution"] = assurance["intent_resolution"]
    behavior["artifact_assurance"] = assurance["artifact_assurance"]
    behavior["dependency_closure"] = closure
    return {
        "id": case["id"], "input": case,
        "behavior": normalize(behavior, repo, project),
        "measurement": {
            "declared_resource_bytes": sum(row["bytes"] for row in declared),
            "machine_contract_bytes": sum(row["bytes"] for row in machine),
            "declared_and_machine_union_bytes": sum(row["bytes"] for row in combined),
            "required_read_bytes": None, "actual_read_tokens": None,
            "repeat_read_bytes": None,
            "unmeasured_reason": "No assistant read trace; load_order is not actual context consumption.",
            "route_load_semantics": semantics,
            "resources": declared, "machine_contract_resources": machine,
        },
        "authority_fingerprint": assurance["authority_fingerprint"],
        "project_read_only": True,
        "project_read_only_applicable": project is not None,
    }


def worker(repo: Path, case: dict[str, Any]) -> dict[str, Any]:
    repo = repo.resolve()
    sys.path.insert(0, str(repo / "scripts"))
    if case.get("project_fixture"):
        with tempfile.TemporaryDirectory(prefix="hsk-opt-synthetic-") as tmp:
            project = Path(tmp)
            build_project(repo, project, case["project_fixture"])
            return measure_plan(repo, case, project)
    return measure_plan(repo, case, None)


def collect(repo: Path, case_file: Path) -> dict[str, Any]:
    payload = load_cases(case_file)
    results = []
    for case in payload["cases"]:
        command = [sys.executable, str(HERE), "--worker", str(repo), json.dumps(case, ensure_ascii=False)]
        completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=90)
        if completed.returncode:
            raise RuntimeError(f"Case {case['id']} failed:\n{completed.stderr}")
        results.append(json.loads(completed.stdout))
    revision = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=False,
    )
    return {
        "schema_version": 1, "measurement_type": "declared_resources_and_resolver_behavior",
        "source_commit": revision.stdout.strip() if revision.returncode == 0 else None,
        "skill_version": yaml.safe_load((repo / "core/bootstrap.yaml").read_text(encoding="utf-8"))["skill_version"],
        "expected_baseline_commit": payload["baseline_commit"],
        "cases_sha256": sha256(case_file.read_bytes()),
        "measurement_driver_sha256": sha256(HERE.read_bytes()),
        "environment": {"python": platform.python_version(), "platform": platform.platform(), "pyyaml": yaml.__version__},
        "cases": results,
    }


def compare(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    if before["cases_sha256"] != after["cases_sha256"]:
        raise ValueError("Cannot compare different case inputs")
    if before["measurement_driver_sha256"] != after["measurement_driver_sha256"]:
        raise ValueError("Cannot compare different measurement drivers")
    left = {row["id"]: row for row in before["cases"]}
    right = {row["id"]: row for row in after["cases"]}
    if left.keys() != right.keys():
        raise ValueError("Case sets differ")
    rows = []
    for identifier in left:
        a, b = left[identifier], right[identifier]
        rows.append({
            "id": identifier, "behavior_equal": a["behavior"] == b["behavior"],
            "authority_fingerprint_equal": a["authority_fingerprint"] == b["authority_fingerprint"],
            "baseline_declared_bytes": a["measurement"]["declared_resource_bytes"],
            "candidate_declared_bytes": b["measurement"]["declared_resource_bytes"],
            "declared_bytes_delta": b["measurement"]["declared_resource_bytes"] - a["measurement"]["declared_resource_bytes"],
        })
    return {
        "schema_version": 1, "baseline_commit": before["source_commit"],
        "candidate_commit": after["source_commit"], "cases": rows,
        "all_equal": all(row["behavior_equal"] and row["authority_fingerprint_equal"]
                         and row["declared_bytes_delta"] == 0 for row in rows),
        "note": "P1 characterizes unchanged behavior; zero delta is expected, not a claimed optimization.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=HERE.parents[1])
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", nargs=2, metavar=("REPO", "CASE_JSON"))
    parser.add_argument("--compare", nargs=2, type=Path, metavar=("BEFORE", "AFTER"))
    args = parser.parse_args()
    if args.worker:
        result = worker(Path(args.worker[0]), json.loads(args.worker[1]))
    elif args.compare:
        result = compare(*(json.loads(path.read_text(encoding="utf-8")) for path in args.compare))
    else:
        result = collect(args.repo_root.resolve(), args.cases.resolve())
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if not args.compare or result["all_equal"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
