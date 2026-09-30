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

import yaml

from reading_plan_cases import CASES, build_project

HERE = Path(__file__).resolve()
ALLOWED_CHANGED_AUTHORITIES = {
    "core/bootstrap.yaml",
    "core/workflow_router.yaml",
    "core/runtime_assurance_contract.yaml",
    "core/state_transition_contract.yaml",
    "core/project_state.schema.yaml",
    "core/module_manifest.yaml",
    "core/writing_runtime_contract.yaml",
    "core/writing_reasoning_contract.yaml",
    "modules/05_writing/paper_writing_protocol.md",
    "templates/latex/cumcm/hsk/template_manifest.yaml",
}
P7_OPTIONAL_ANALYSIS_PREREQUISITE = "figure_evidence:result_analysis_workbook"
APPROVED_RELEASE_CARRIERS = {"9.1.0", "9.2.0", "9.2.1", "9.3.0", "9.3.1", "9.4.0", "9.4.1", "9.4.2", "9.4.3", "9.4.4", "9.5.0", "9.5.1", "9.5.2", "9.5.3", "9.5.4", "9.5.5", "9.5.6", "9.5.7", "9.6.0", "9.6.1", "9.7.0", "9.7.1", "10.0.0", "10.0.1"}
A7_HYDRATED_PROVENANCE_CASES = {
    "facts_current", "facts_model_change", "facts_ambiguous", "facts_stale_framework",
    "facts_hash_drift", "facts_identity_drift", "facts_stale_dependency", "style_current",
    "style_data_change", "style_figure_drift", "style_no_approval", "mixed",
}
B2B6_AUTHORITY_VERSIONS = {
    "skill": "10.12.0",
    "project_state": "8.11.0",
    "claim_consumption": "1.7.0",
    "state_transition": "1.5.0",
    "writing_reasoning": "1.9.0",
    "runtime_assurance": "2.3.0",
}
B2C_AUTHORITY_VERSIONS = {
    "skill": "10.13.0",
    "project_state": "8.12.0",
    "claim_consumption": "1.8.0",
    "state_transition": "1.6.0",
    "writing_reasoning": "1.10.0",
    "runtime_assurance": "2.4.0",
}
C1_AUTHORITY_VERSIONS = {
    **B2C_AUTHORITY_VERSIONS,
    "skill": "10.14.0",
    "project_state": "8.13.0",
}
WINDOWS_PYTHON_CI_AUTHORITY_VERSIONS = {
    **C1_AUTHORITY_VERSIONS,
    "skill": "10.14.1",
}
WINDOWS_MATLAB_CI_AUTHORITY_VERSIONS = {
    **WINDOWS_PYTHON_CI_AUTHORITY_VERSIONS,
    "skill": "10.14.2",
}
C2_AUTHORITY_VERSIONS = {
    **WINDOWS_MATLAB_CI_AUTHORITY_VERSIONS,
    "skill": "10.15.0",
    "project_state": "8.14.0",
    "review_receipt_consumption": "1.0.0",
}
PYTHON_CI_PERFORMANCE_AUTHORITY_VERSIONS = {
    **C2_AUTHORITY_VERSIONS,
    "skill": "10.15.1",
}


def authority_versions(repo):
    """Read exact release carriers without making missing historical files fatal."""
    carriers = {
        "skill": ("core/bootstrap.yaml", "skill_version"),
        "project_state": ("core/project_state.schema.yaml", "version"),
        "claim_consumption": ("core/claim_consumption_contract.yaml", "version"),
        "state_transition": ("core/state_transition_contract.yaml", "version"),
        "writing_reasoning": ("core/writing_reasoning_contract.yaml", "schema_version"),
        "runtime_assurance": ("core/runtime_assurance_contract.yaml", "version"),
        "review_receipt_consumption": ("core/review_receipt_consumption_contract.yaml", "version"),
    }
    versions = {}
    for name, (relative, key) in carriers.items():
        try:
            payload = yaml.safe_load((repo / relative).read_text(encoding="utf-8"))
            versions[name] = str(payload.get(key)) if isinstance(payload, dict) and key in payload else None
        except (OSError, UnicodeError, yaml.YAMLError):
            versions[name] = None
    return versions


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
    if value.get("version") in APPROVED_RELEASE_CARRIERS:
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
        return {"id": identifier, "plan": value, "legacy_declared_bytes": declared,
                "authority_versions": authority_versions(repo)}


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


def approved_v10_project_backend_changes(identifier, old, new):
    """Register only the measured v10 Authority version and canonical root projection."""
    projected = deepcopy(new)
    changes = []

    def register(path, candidate, approval):
        left, right, target = old, new, projected
        try:
            for key in path[:-1]:
                left, right, target = left[key], right[key], target[key]
            key = path[-1]
            if key in left or right.get(key) != candidate:
                return
        except (KeyError, TypeError):
            return
        target.pop(key)
        changes.append({"path": ".".join(path), "baseline_present": False,
                        "candidate": candidate, "approval": approval})

    if (old.get("assurance", {}).get("schema_version") == "1.2.0"
            and new.get("assurance", {}).get("schema_version") == "2.0.0"):
        projected["assurance"]["schema_version"] = "1.2.0"
        changes.append({"path": "assurance.schema_version", "baseline": "1.2.0",
                        "candidate": "2.0.0", "approval": "v10 approved Runtime Assurance Authority version"})

    if identifier not in A7_HYDRATED_PROVENANCE_CASES:
        return projected, changes
    approval = "v10 approved canonical project solver backend projection"
    solver = {
        "scope": "project", "request": None, "stage": None, "resolved": "python",
        "candidate_backend": None, "selection_complete": True, "source": "project_state",
        "conflicts": [], "environment_verified": False,
        "decision_contract": "core/user_execution_contract.yaml#solver_backends",
    }
    declarations = [
        {"question": "Q1", "stage": stage, "declared_backend": None,
         "code": f"问题一求解/{filename}", "artifact_identity_verified": False}
        for stage, filename in (("primary", "问题一求解.py"),
                                ("analysis", "问题一结果深化分析.py"))
    ]
    policy = {
        "scope": "project", "kind": "canonical_declarations", "diagnostic_only": True,
        "selected_backend": "python", "candidate_backend": None,
        "candidate_evidence": "declarations_only_not_artifact_validation",
        "requested_backend": None, "request_conflict": False,
        "declarations": declarations, "issues": [], "schema_validated": False,
        "environment_verified": False, "execution_authorized": False,
    }
    register(("assurance", "context", "backend_policy"), policy, approval)
    register(("assurance", "context", "field_provenance", "solver_backend"), "project_state", approval)
    register(("runtime_plan", "solver_backend"), solver, approval)
    register(("solver_backend",), solver, approval)
    return projected, changes


def approved_v1010_audit_changes(identifier, old, new):
    """Expose only AUD-04's exact auto projection and this release's version pair."""
    projected = deepcopy(new)
    changes = []
    if (identifier not in {case[0] for case in CASES}
            or old.get("version") != "<EXPECTED_P9_RELEASE_CARRIER_CHANGE>"
            or new.get("version") != "10.1.0"):
        return projected, changes

    def register(path, expected, *, absent=False, previous=None):
        left, right, target = old, new, projected
        try:
            for key in path[:-1]:
                left, right, target = left[key], right[key], target[key]
            key = path[-1]
            if not isinstance(left, dict) or not isinstance(right, dict) or key not in right:
                return
            if (json.dumps(right[key], sort_keys=True) != json.dumps(expected, sort_keys=True)
                    or (key in left if absent else left.get(key) != previous)):
                return
        except (KeyError, TypeError):
            return
        if absent:
            target.pop(key)
        else:
            target[key] = deepcopy(previous)
        changes.append({"path": ".".join(path), "baseline_present": not absent,
                        "baseline": previous, "candidate": deepcopy(expected),
                        "approval": "v10.1 AUD-04 exact neutral-backend projection and protocol carriers"})

    register(("version",), "10.1.0", previous="<EXPECTED_P9_RELEASE_CARRIER_CHANGE>")
    register(("assurance", "schema_version"), "2.1.0", previous="1.2.0")
    solver = {
        "scope": "project", "request": "auto", "stage": None, "resolved": "python",
        "candidate_backend": None, "selection_complete": True, "source": "project_state",
        "conflicts": [], "environment_verified": False,
        "decision_contract": "core/user_execution_contract.yaml#solver_backends",
    }
    if identifier in A7_HYDRATED_PROVENANCE_CASES:
        register(("solver_backend",), solver, absent=True)
        register(("runtime_plan", "solver_backend"), solver, absent=True)
    elif identifier == "facts_unscoped":
        solver.update(scope="stateless", resolved=None, selection_complete=False, source="unresolved")
        register(("solver_backend",), solver, absent=True)
        register(("runtime_plan", "solver_backend"), solver, absent=True)
        register(("assurance", "context", "backend_policy"), None, absent=True)
        register(("assurance", "context", "field_provenance", "solver_backend"),
                 "unresolved", absent=True)
    return projected, changes



def approved_a1_carrier_change(identifier, old, new):
    """Reuse the exact predecessor transitions; A1 changes no legacy task behavior."""
    if (identifier not in {case[0] for case in CASES}
            or old.get("version") != "<EXPECTED_P9_RELEASE_CARRIER_CHANGE>"
            or new.get("version") != "10.2.0"):
        return deepcopy(new), []
    predecessor = deepcopy(new)
    predecessor["version"] = "10.1.0"
    projected, changes = approved_v1010_audit_changes(identifier, old, predecessor)
    for change in changes:
        if change["path"] == "version":
            change["candidate"] = "10.2.0"
            change["approval"] = "A1 opt-in 10.2.0 carrier only; predecessor field transitions remain exact"
    return projected, changes


def approved_a2_carrier_change(identifier, old, new):
    """A2-disabled controls may change exact version carriers, not runtime behavior."""
    if (identifier not in {case[0] for case in CASES}
            or old.get("version") != "<EXPECTED_P9_RELEASE_CARRIER_CHANGE>"
            or new.get("version") != "10.3.0"):
        return deepcopy(new), []
    predecessor=deepcopy(new)
    predecessor["version"]="10.2.0"
    known=(predecessor.get("assurance") or {}).get("schema_version")=="2.2.0"
    if known:
        predecessor["assurance"]["schema_version"]="2.1.0"
    projected,changes=approved_a1_carrier_change(identifier,old,predecessor)
    for change in changes:
        if change["path"]=="version":
            change["candidate"]="10.3.0"
            change["approval"]="A2 opt-in 10.3.0 version carrier only on fixed disabled controls"
        elif known and change["path"]=="assurance.schema_version":
            change["candidate"]="2.2.0"
            change["approval"]="A2 Runtime Assurance 2.2.0 protocol carrier; no qualification changes waived"
    return projected,changes


def approved_b1_carrier_change(identifier, old, new):
    """Only the exact B1 version carrier on pre-existing disabled controls."""
    if (identifier not in {case[0] for case in CASES}
            or old.get("version") != "<EXPECTED_P9_RELEASE_CARRIER_CHANGE>"
            or new.get("version") != "10.4.0"):
        return deepcopy(new), []
    predecessor=deepcopy(new)
    predecessor["version"]="10.3.0"
    projected,changes=approved_a2_carrier_change(identifier,old,predecessor)
    for change in changes:
        if change["path"]=="version":
            change["candidate"]="10.4.0"
            change["approval"]="B1 opt-in 10.4.0 carrier only; all old qualification differences remain checked"
    return projected,changes


def approved_b2_carrier_change(identifier, old, new):
    """Only the exact B2 version carrier on pre-existing disabled controls."""
    if (identifier not in {case[0] for case in CASES}
            or old.get("version") != "<EXPECTED_P9_RELEASE_CARRIER_CHANGE>"
            or new.get("version") != "10.5.0"
            or not isinstance(new.get("assurance"), dict)
            or new["assurance"].get("schema_version") != "2.2.0"):
        return deepcopy(new), []
    predecessor = deepcopy(new)
    predecessor["version"] = "10.4.0"
    projected, changes = approved_b1_carrier_change(identifier, old, predecessor)
    for change in changes:
        if change["path"] == "version":
            change["candidate"] = "10.5.0"
            change["approval"] = "B2 opt-in 10.5.0 carrier only; all old qualification differences remain checked"
    return projected, changes


def approved_b2b1_carrier_change(identifier, old, new):
    """Only the exact B2b1 version carrier on pre-existing disabled controls."""
    if (identifier not in {case[0] for case in CASES}
            or old.get("version") != "<EXPECTED_P9_RELEASE_CARRIER_CHANGE>"
            or new.get("version") != "10.6.0"
            or not isinstance(new.get("assurance"), dict)
            or new["assurance"].get("schema_version") != "2.2.0"):
        return deepcopy(new), []
    predecessor = deepcopy(new)
    predecessor["version"] = "10.5.0"
    projected, changes = approved_b2_carrier_change(identifier, old, predecessor)
    for change in changes:
        if change["path"] == "version":
            change["candidate"] = "10.6.0"
            change["approval"] = "B2b1 opt-in 10.6.0 carrier only; old qualification remains checked"
    return projected, changes


def approved_b2b2_carrier_change(identifier, old, new):
    """Only the exact B2b2 version carrier on pre-existing disabled controls."""
    if (identifier not in {case[0] for case in CASES}
            or old.get("version") != "<EXPECTED_P9_RELEASE_CARRIER_CHANGE>"
            or new.get("version") != "10.7.0"
            or not isinstance(new.get("assurance"), dict)
            or new["assurance"].get("schema_version") != "2.2.0"):
        return deepcopy(new), []
    predecessor = deepcopy(new)
    predecessor["version"] = "10.6.0"
    projected, changes = approved_b2b1_carrier_change(identifier, old, predecessor)
    for change in changes:
        if change["path"] == "version":
            change["candidate"] = "10.7.0"
            change["approval"] = "B2b2 opt-in 10.7.0 carrier only; old qualification remains checked"
    return projected, changes


def approved_b2b3a_carrier_change(identifier, old, new):
    """Only the exact B2b3a version carrier on pre-existing disabled controls."""
    if (identifier not in {case[0] for case in CASES}
            or old.get("version") != "<EXPECTED_P9_RELEASE_CARRIER_CHANGE>"
            or new.get("version") != "10.8.0"
            or not isinstance(new.get("assurance"), dict)
            or new["assurance"].get("schema_version") != "2.2.0"):
        return deepcopy(new), []
    predecessor = deepcopy(new)
    predecessor["version"] = "10.7.0"
    projected, changes = approved_b2b2_carrier_change(identifier, old, predecessor)
    for change in changes:
        if change["path"] == "version":
            change["candidate"] = "10.8.0"
            change["approval"] = "B2b3a opt-in 10.8.0 carrier only; old qualification remains checked"
    return projected, changes


def approved_b2b3b_carrier_change(identifier, old, new):
    """Only the exact B2b3b version carrier on pre-existing disabled controls."""
    if (identifier not in {case[0] for case in CASES}
            or old.get("version") != "<EXPECTED_P9_RELEASE_CARRIER_CHANGE>"
            or new.get("version") != "10.9.0"
            or not isinstance(new.get("assurance"), dict)
            or new["assurance"].get("schema_version") != "2.2.0"):
        return deepcopy(new), []
    predecessor = deepcopy(new)
    predecessor["version"] = "10.8.0"
    projected, changes = approved_b2b3a_carrier_change(identifier, old, predecessor)
    for change in changes:
        if change["path"] == "version":
            change["candidate"] = "10.9.0"
            change["approval"] = "B2b3b opt-in 10.9.0 carrier only; old qualification remains checked"
    return projected, changes


def approved_b2b3c_carrier_change(identifier, old, new):
    """Only the exact B2b3c version carrier on pre-existing disabled controls."""
    if (identifier not in {case[0] for case in CASES}
            or old.get("version") != "<EXPECTED_P9_RELEASE_CARRIER_CHANGE>"
            or new.get("version") != "10.10.0"
            or not isinstance(new.get("assurance"), dict)
            or new["assurance"].get("schema_version") != "2.2.0"):
        return deepcopy(new), []
    predecessor = deepcopy(new)
    predecessor["version"] = "10.9.0"
    projected, changes = approved_b2b3b_carrier_change(identifier, old, predecessor)
    for change in changes:
        if change["path"] == "version":
            change["candidate"] = "10.10.0"
            change["approval"] = "B2b3c opt-in 10.10.0 carrier only; old qualification remains checked"
    return projected, changes


def approved_b2_patch_carrier_change(identifier, old, new):
    """Only the exact 10.10.1 patch carrier on pre-existing disabled controls."""
    if (identifier not in {case[0] for case in CASES}
            or old.get("version") != "<EXPECTED_P9_RELEASE_CARRIER_CHANGE>"
            or new.get("version") != "10.10.1"
            or not isinstance(new.get("assurance"), dict)
            or new["assurance"].get("schema_version") != "2.2.0"):
        return deepcopy(new), []
    predecessor = deepcopy(new)
    predecessor["version"] = "10.10.0"
    projected, changes = approved_b2b3c_carrier_change(identifier, old, predecessor)
    for change in changes:
        if change["path"] == "version":
            change["candidate"] = "10.10.1"
            change["approval"] = "B2 wording patch 10.10.1 carrier only; old qualification remains checked"
    return projected, changes


def approved_b2b4_carrier_change(identifier, old, new):
    """Only the exact B2b4 10.11.0 carrier on pre-existing disabled controls."""
    if (identifier not in {case[0] for case in CASES}
            or old.get("version") != "<EXPECTED_P9_RELEASE_CARRIER_CHANGE>"
            or new.get("version") != "10.11.0"
            or not isinstance(new.get("assurance"), dict)
            or new["assurance"].get("schema_version") != "2.2.0"):
        return deepcopy(new), []
    predecessor = deepcopy(new)
    predecessor["version"] = "10.10.1"
    projected, changes = approved_b2_patch_carrier_change(identifier, old, predecessor)
    for change in changes:
        if change["path"] == "version":
            change["candidate"] = "10.11.0"
            change["approval"] = "B2b4 opt-in Figure-chain 10.11.0 carrier only; old qualification remains checked"
    return projected, changes


def approved_b2b5_carrier_change(identifier, old, new):
    """Only the exact B12 acceptance 10.11.1 carrier; no qualification waiver."""
    if (identifier not in {case[0] for case in CASES}
            or old.get("version") != "<EXPECTED_P9_RELEASE_CARRIER_CHANGE>"
            or new.get("version") != "10.11.1"
            or not isinstance(new.get("assurance"), dict)
            or new["assurance"].get("schema_version") != "2.2.0"):
        return deepcopy(new), []
    predecessor = deepcopy(new)
    predecessor["version"] = "10.11.0"
    projected, changes = approved_b2b4_carrier_change(identifier, old, predecessor)
    for change in changes:
        if change["path"] == "version":
            change["candidate"] = "10.11.1"
            change["approval"] = "B12 acceptance 10.11.1 carrier only; old qualification remains checked"
    return projected, changes


def approved_b2b6_carrier_change(identifier, old, new, candidate_authority_versions):
    """Approve B2b6 only when all six release and Authority carriers are exact."""
    old_sources = (((old.get("assurance") or {}).get("authority_fingerprint") or {}).get("sources") or [])
    new_sources = (((new.get("assurance") or {}).get("authority_fingerprint") or {}).get("sources") or [])
    fingerprint_additions = [
        "core/project_state.schema.yaml", "core/state_transition_contract.yaml",
    ]
    added_authorities = [
        row for row in new_sources
        if isinstance(row, dict) and row.get("path") in fingerprint_additions
    ]
    filtered_sources = [
        row for row in new_sources
        if not (isinstance(row, dict) and row.get("path") in fingerprint_additions)
    ]
    exact_fingerprint_extension = (
        [row.get("path") for row in added_authorities] == fingerprint_additions
        and all(set(row) == {"path", "sha256"} for row in added_authorities)
    )
    if (identifier not in {case[0] for case in CASES}
            or old.get("version") != "<EXPECTED_P9_RELEASE_CARRIER_CHANGE>"
            or new.get("version") != B2B6_AUTHORITY_VERSIONS["skill"]
            or candidate_authority_versions != B2B6_AUTHORITY_VERSIONS
            or not isinstance(new.get("assurance"), dict)
            or new["assurance"].get("schema_version") != B2B6_AUTHORITY_VERSIONS["runtime_assurance"]
            or not exact_fingerprint_extension):
        return deepcopy(new), []
    predecessor = deepcopy(new)
    predecessor["version"] = "10.11.1"
    predecessor["assurance"]["schema_version"] = "2.2.0"
    predecessor["assurance"]["authority_fingerprint"]["sources"] = deepcopy(filtered_sources)
    predecessor, solver_changes = approved_solver_changes(old, predecessor)
    projected_sources = (
        ((predecessor.get("assurance") or {}).get("authority_fingerprint") or {})
        .get("sources") or []
    )
    if projected_sources != old_sources:
        return deepcopy(new), []
    projected, changes = approved_b2b5_carrier_change(identifier, old, predecessor)
    changes = solver_changes + changes
    for change in changes:
        if change["path"] == "version":
            change["candidate"] = B2B6_AUTHORITY_VERSIONS["skill"]
            change["authority_versions"] = deepcopy(B2B6_AUTHORITY_VERSIONS)
            change["approval"] = (
                "B2b6 structured rejection return exact carrier set only; "
                "old qualification remains checked"
            )
    changes.extend([
        {
            "path": "assurance.schema_version", "baseline": "2.2.0",
            "candidate": B2B6_AUTHORITY_VERSIONS["runtime_assurance"],
            "approval": "B2b6 fail-closed runtime rejection qualification protocol",
        },
        {
            "path": "assurance.authority_fingerprint.sources",
            "baseline": filtered_sources, "candidate": new_sources,
            "approval": "B2b6 binds Project State Schema and State Transition Authority into the runtime fingerprint",
        },
    ])
    return projected, changes


def approved_b2c_carrier_change(identifier, old, new, candidate_authority_versions):
    """Approve B2c only after replaying the exact historical B2b6 projection."""
    if (identifier not in {case[0] for case in CASES}
            or old.get("version") != "<EXPECTED_P9_RELEASE_CARRIER_CHANGE>"
            or new.get("version") != B2C_AUTHORITY_VERSIONS["skill"]
            or candidate_authority_versions != B2C_AUTHORITY_VERSIONS
            or not isinstance(new.get("assurance"), dict)
            or new["assurance"].get("schema_version") != B2C_AUTHORITY_VERSIONS["runtime_assurance"]):
        return deepcopy(new), []
    predecessor = deepcopy(new)
    predecessor["version"] = B2B6_AUTHORITY_VERSIONS["skill"]
    predecessor["assurance"]["schema_version"] = B2B6_AUTHORITY_VERSIONS["runtime_assurance"]
    projected, changes = approved_b2b6_carrier_change(
        identifier, old, predecessor, deepcopy(B2B6_AUTHORITY_VERSIONS)
    )
    if projected != old:
        return deepcopy(new), []
    for change in changes:
        if change["path"] == "version":
            change["candidate"] = B2C_AUTHORITY_VERSIONS["skill"]
            change["authority_versions"] = deepcopy(B2C_AUTHORITY_VERSIONS)
            change["approval"] = (
                "B2c selected paper-carrier exact Authority set only; "
                "old qualification remains checked"
            )
        elif change["path"] == "assurance.schema_version":
            change["candidate"] = B2C_AUTHORITY_VERSIONS["runtime_assurance"]
            change["approval"] = "B2c selected paper-carrier runtime qualification protocol"
    return projected, changes


def approved_c1_carrier_change(identifier, old, new, candidate_authority_versions):
    """C1 adds an opt-in read-only reviewer receipt; legacy runtime qualification is unchanged."""
    if (identifier not in {case[0] for case in CASES}
            or old.get("version") != "<EXPECTED_P9_RELEASE_CARRIER_CHANGE>"
            or new.get("version") != C1_AUTHORITY_VERSIONS["skill"]
            or candidate_authority_versions != C1_AUTHORITY_VERSIONS
            or not isinstance(new.get("assurance"), dict)
            or new["assurance"].get("schema_version") != C1_AUTHORITY_VERSIONS["runtime_assurance"]):
        return deepcopy(new), []
    predecessor = deepcopy(new)
    predecessor["version"] = B2C_AUTHORITY_VERSIONS["skill"]
    projected, changes = approved_b2c_carrier_change(
        identifier, old, predecessor, deepcopy(B2C_AUTHORITY_VERSIONS)
    )
    if projected != old:
        return deepcopy(new), []
    for change in changes:
        if change["path"] == "version":
            change["candidate"] = C1_AUTHORITY_VERSIONS["skill"]
            change["authority_versions"] = deepcopy(C1_AUTHORITY_VERSIONS)
            change["approval"] = "C1 opt-in reviewer receipt carrier; legacy runtime qualification remains checked"
    return projected, changes


def approved_windows_python_ci_carrier_change(identifier, old, new, candidate_authority_versions):
    """Allow only the 10.14.1 CI policy release carrier, without runtime behavior changes."""
    if (identifier not in {case[0] for case in CASES}
            or old.get("version") != "<EXPECTED_P9_RELEASE_CARRIER_CHANGE>"
            or new.get("version") != WINDOWS_PYTHON_CI_AUTHORITY_VERSIONS["skill"]
            or candidate_authority_versions != WINDOWS_PYTHON_CI_AUTHORITY_VERSIONS
            or not isinstance(new.get("assurance"), dict)
            or new["assurance"].get("schema_version") != C1_AUTHORITY_VERSIONS["runtime_assurance"]):
        return deepcopy(new), []
    predecessor = deepcopy(new)
    predecessor["version"] = C1_AUTHORITY_VERSIONS["skill"]
    projected, changes = approved_c1_carrier_change(
        identifier, old, predecessor, deepcopy(C1_AUTHORITY_VERSIONS)
    )
    if projected != old:
        return deepcopy(new), []
    for change in changes:
        if change["path"] == "version":
            change["candidate"] = WINDOWS_PYTHON_CI_AUTHORITY_VERSIONS["skill"]
            change["authority_versions"] = deepcopy(WINDOWS_PYTHON_CI_AUTHORITY_VERSIONS)
            change["approval"] = "Windows Python CI policy patch carrier only; legacy runtime qualification remains checked"
    return projected, changes


def approved_windows_matlab_ci_carrier_change(identifier, old, new, candidate_authority_versions):
    """Allow only the 10.14.2 MATLAB CI release carrier, not runtime behavior changes."""
    if (identifier not in {case[0] for case in CASES}
            or old.get("version") != "<EXPECTED_P9_RELEASE_CARRIER_CHANGE>"
            or new.get("version") != WINDOWS_MATLAB_CI_AUTHORITY_VERSIONS["skill"]
            or candidate_authority_versions != WINDOWS_MATLAB_CI_AUTHORITY_VERSIONS
            or not isinstance(new.get("assurance"), dict)
            or new["assurance"].get("schema_version") != C1_AUTHORITY_VERSIONS["runtime_assurance"]):
        return deepcopy(new), []
    predecessor = deepcopy(new)
    predecessor["version"] = WINDOWS_PYTHON_CI_AUTHORITY_VERSIONS["skill"]
    projected, changes = approved_windows_python_ci_carrier_change(
        identifier, old, predecessor, deepcopy(WINDOWS_PYTHON_CI_AUTHORITY_VERSIONS)
    )
    if projected != old:
        return deepcopy(new), []
    for change in changes:
        if change["path"] == "version":
            change["candidate"] = WINDOWS_MATLAB_CI_AUTHORITY_VERSIONS["skill"]
            change["authority_versions"] = deepcopy(WINDOWS_MATLAB_CI_AUTHORITY_VERSIONS)
            change["approval"] = "Windows MATLAB CI policy patch carrier only; legacy runtime qualification remains checked"
    return projected, changes


def approved_c2_carrier_change(identifier, old, new, candidate_authority_versions):
    """Allow only exact opt-in C2 carriers; compare all ordinary runtime fields."""
    if (identifier not in {case[0] for case in CASES}
            or old.get("version") != "<EXPECTED_P9_RELEASE_CARRIER_CHANGE>"
            or new.get("version") != C2_AUTHORITY_VERSIONS["skill"]
            or candidate_authority_versions != C2_AUTHORITY_VERSIONS
            or not isinstance(new.get("assurance"), dict)
            or new["assurance"].get("schema_version") != C2_AUTHORITY_VERSIONS["runtime_assurance"]):
        return deepcopy(new), []
    predecessor = deepcopy(new)
    predecessor["version"] = WINDOWS_MATLAB_CI_AUTHORITY_VERSIONS["skill"]
    projected, changes = approved_windows_matlab_ci_carrier_change(
        identifier, old, predecessor, deepcopy(WINDOWS_MATLAB_CI_AUTHORITY_VERSIONS)
    )
    if projected != old:
        return deepcopy(new), []
    for change in changes:
        if change["path"] == "version":
            change["candidate"] = C2_AUTHORITY_VERSIONS["skill"]
            change["authority_versions"] = deepcopy(C2_AUTHORITY_VERSIONS)
            change["approval"] = (
                "C2 explicit scoped review-receipt policy and Authority carriers only; "
                "ordinary legacy runtime qualification remains checked"
            )
    return projected, changes


def approved_python_ci_performance_carrier_change(identifier, old, new, candidate_authority_versions):
    """Allow only the exact 10.15.1 patch carrier with all C2 semantics checked."""
    if (identifier not in {case[0] for case in CASES}
            or old.get("version") != "<EXPECTED_P9_RELEASE_CARRIER_CHANGE>"
            or new.get("version") != PYTHON_CI_PERFORMANCE_AUTHORITY_VERSIONS["skill"]
            or candidate_authority_versions != PYTHON_CI_PERFORMANCE_AUTHORITY_VERSIONS
            or not isinstance(new.get("assurance"), dict)
            or new["assurance"].get("schema_version") != C2_AUTHORITY_VERSIONS["runtime_assurance"]):
        return deepcopy(new), []
    predecessor = deepcopy(new)
    predecessor["version"] = C2_AUTHORITY_VERSIONS["skill"]
    projected, changes = approved_c2_carrier_change(
        identifier, old, predecessor, deepcopy(C2_AUTHORITY_VERSIONS)
    )
    if projected != old:
        return deepcopy(new), []
    for change in changes:
        if change["path"] == "version":
            change["candidate"] = PYTHON_CI_PERFORMANCE_AUTHORITY_VERSIONS["skill"]
            change["authority_versions"] = deepcopy(PYTHON_CI_PERFORMANCE_AUTHORITY_VERSIONS)
            change["approval"] = (
                "Windows Python CI performance patch carrier only; "
                "all C2 and ordinary runtime qualifications remain checked"
            )
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
        projected, v10_changes = approved_v10_project_backend_changes(a["id"], old, projected)
        expected.extend(v10_changes)
        projected, audit_changes = approved_v1010_audit_changes(a["id"], old, projected)
        expected.extend(audit_changes)
        projected, a1_changes = approved_a1_carrier_change(a["id"], old, projected)
        expected.extend(a1_changes)
        projected, a2_changes = approved_a2_carrier_change(a["id"], old, projected)
        expected.extend(a2_changes)
        projected, b1_changes = approved_b1_carrier_change(a["id"], old, projected)
        expected.extend(b1_changes)
        projected, b2_changes = approved_b2_carrier_change(a["id"], old, projected)
        expected.extend(b2_changes)
        projected, b2b1_changes = approved_b2b1_carrier_change(a["id"], old, projected)
        expected.extend(b2b1_changes)
        projected, b2b2_changes = approved_b2b2_carrier_change(a["id"], old, projected)
        expected.extend(b2b2_changes)
        projected, b2b3a_changes = approved_b2b3a_carrier_change(a["id"], old, projected)
        expected.extend(b2b3a_changes)
        projected, b2b3b_changes = approved_b2b3b_carrier_change(a["id"], old, projected)
        expected.extend(b2b3b_changes)
        projected, b2b3c_changes = approved_b2b3c_carrier_change(a["id"], old, projected)
        expected.extend(b2b3c_changes)
        projected, b2_patch_changes = approved_b2_patch_carrier_change(a["id"], old, projected)
        expected.extend(b2_patch_changes)
        projected, b2b4_changes = approved_b2b4_carrier_change(a["id"], old, projected)
        expected.extend(b2b4_changes)
        projected, b2b5_changes = approved_b2b5_carrier_change(a["id"], old, projected)
        expected.extend(b2b5_changes)
        projected, b2b6_changes = approved_b2b6_carrier_change(
            a["id"], old, projected, b.get("authority_versions")
        )
        expected.extend(b2b6_changes)
        projected, b2c_changes = approved_b2c_carrier_change(
            a["id"], old, projected, b.get("authority_versions")
        )
        expected.extend(b2c_changes)
        projected, c1_changes = approved_c1_carrier_change(
            a["id"], old, projected, b.get("authority_versions")
        )
        expected.extend(c1_changes)
        projected, windows_ci_changes = approved_windows_python_ci_carrier_change(
            a["id"], old, projected, b.get("authority_versions")
        )
        expected.extend(windows_ci_changes)
        projected, windows_matlab_ci_changes = approved_windows_matlab_ci_carrier_change(
            a["id"], old, projected, b.get("authority_versions")
        )
        expected.extend(windows_matlab_ci_changes)
        projected, c2_changes = approved_c2_carrier_change(
            a["id"], old, projected, b.get("authority_versions")
        )
        expected.extend(c2_changes)
        projected, python_ci_performance_changes = approved_python_ci_performance_carrier_change(
            a["id"], old, projected, b.get("authority_versions")
        )
        expected.extend(python_ci_performance_changes)
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
            "candidate_authority_versions": b.get("authority_versions"),
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
        "comparison_scope": "all_legacy_fields_with_declared_authority_hash_p7_prerequisite_p9_carrier_exceptions_and_exact_a3_a7_v970_v10_v1010_a1_a2_b1_b2_b2b1_b2b2_b2b3a_b2b3b_b2b3c_b2_patch_b2b4_b2b5_b2b6_b2c_c1_windows_python_ci_windows_matlab_ci_c2_python_ci_performance_exact_authority_carrier_transitions",
        "expected_authority_changes": sorted(ALLOWED_CHANGED_AUTHORITIES),
        "approved_b2b6_authority_versions": B2B6_AUTHORITY_VERSIONS,
        "approved_b2c_authority_versions": B2C_AUTHORITY_VERSIONS,
        "approved_c1_authority_versions": C1_AUTHORITY_VERSIONS,
        "approved_windows_python_ci_authority_versions": WINDOWS_PYTHON_CI_AUTHORITY_VERSIONS,
        "approved_windows_matlab_ci_authority_versions": WINDOWS_MATLAB_CI_AUTHORITY_VERSIONS,
        "approved_c2_authority_versions": C2_AUTHORITY_VERSIONS,
        "approved_python_ci_performance_authority_versions": PYTHON_CI_PERFORMANCE_AUTHORITY_VERSIONS,
        "all_legacy_behavior_equal": all(r["legacy_behavior_equal"] for r in rows),
        "all_legacy_behavior_equal_except_approved_changes": all(r["legacy_behavior_equal_except_approved_changes"] for r in rows),
        "interpretation": "Initial planned ranges, not actual reads/tokens or total task cost. Existing Authority hash, P7 prerequisite and registered release-carrier exceptions remain. legacy_behavior_equal is measured before exact A3/A7/v9.7/v10/v10.1/A1/A2/B1/B2/B2b1/B2b2/B2b3a/B2b3b/B2b3c/B2 patch/B2b4/B2b5/B2b6/B2c/C1/Windows Python CI/Windows MATLAB CI/C2/Python CI performance carrier exceptions; B2b6, B2c, C1, both earlier CI patches, C2 and the performance patch require their exact Authority version sets. Each approved version, provenance or canonical solver projection is visible in expected_legacy_changes. No result qualification, classification value or existing list-order normalization is waived. Passing requires no unregistered field differences.",
        "cases": rows,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in (("p2-baseline-plans.json", before), ("p2-candidate-plans.json", after), ("p2-comparison.json", report)):
        (args.output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["all_legacy_behavior_equal_except_approved_changes"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
