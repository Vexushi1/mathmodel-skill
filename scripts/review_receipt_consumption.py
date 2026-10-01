#!/usr/bin/env python3
"""Read-only, explicitly scoped C2 consumption of current C1 review receipts.

A passed result means only that the declared receipt scope is eligible for an
existing gate to consume. It cannot approve a model, reproduce a computation,
accept a workbook, or authorize final delivery.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml
import safe_yaml
from jsonschema import Draft202012Validator

import project_transaction as PROJECT_TX
import review_receipts as REVIEW
import runtime_assurance as RUNTIME

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "core/project_state.schema.yaml"
CONTRACT = "core/review_receipt_consumption_contract.yaml"
MODEL_CONTRACT = "core/model_approval_contract.yaml"
FINAL_MATRIX = "templates/review/final_review_matrix.yaml"
POLICY_VERSION = "1.0.0"
MODEL_ROLES = {
    "positive_fitness_review": "reviewer_pass",
    "adversarial_model_challenge": "devils_advocate_pass",
}
GATES = {"model_challenge", "draft_semantic_review", "final_review_and_delivery"}


def _report(gate: str, questions: Sequence[str] | None) -> dict[str, Any]:
    return {
        "status": "failed",
        "gate": gate,
        "questions": list(questions or []),
        "qualification": "not_granted",
        "coverage_boundary": "declared_scope_only",
        "human_model_approval": "not_granted",
        "numerical_reproduction": "not_granted",
        "accepted_workbook": "not_granted",
        "final_delivery": "not_granted",
        "receipt_ids": [],
        "selected_snapshots": [],
        "issues": [],
        "observed_sources": {"project": {}, "skill": {}},
    }


def _observe_skill(relative: str, observed: dict[str, str | None]) -> Mapping[str, Any]:
    path = ROOT / relative
    raw = path.read_bytes()
    observed[relative] = hashlib.sha256(raw).hexdigest()
    value = safe_yaml.safe_load(raw.decode("utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError(f"{relative} is not a mapping")
    return value


def _policy_issues(
    policy: Mapping[str, Any], model: Mapping[str, Any], final_matrix: Mapping[str, Any],
) -> list[str]:
    issues: list[str] = []
    seen: set[tuple[str, str]] = set()
    challenge = model.get("model_challenge") or {}
    final_families = {
        item.get("check_family") for item in final_matrix.get("coverage", [])
        if isinstance(item, Mapping) and isinstance(item.get("check_family"), str)
    }
    if not final_families:
        issues.append("final review matrix has no check families")
    for requirement in policy["requirements"]:
        gate = requirement["gate"]
        roles = {item["role"]: item for item in requirement["roles"]}
        if len(roles) != len(requirement["roles"]):
            issues.append(f"{gate}: duplicate review role in policy")
        if gate == "model_challenge":
            if set(roles) != set(MODEL_ROLES):
                issues.append("model_challenge requires the two existing Model Challenge roles")
            for role, pass_name in MODEL_ROLES.items():
                required = set((challenge.get(pass_name) or {}).get("must_check") or [])
                declared = set(roles.get(role, {}).get("check_ids", []))
                if not required or not required.issubset(declared):
                    issues.append(f"model_challenge {role} policy omits current must_check IDs")
            for question in requirement["questions"]:
                if f"{question}:model" not in requirement["object_ids"]:
                    issues.append(f"model_challenge/{question}: model object is absent from policy")
        elif len(roles) < 2:
            issues.append(f"{gate}: paper review needs two distinct roles")
        if gate == "final_review_and_delivery":
            for role, role_spec in roles.items():
                if not final_families.issubset(role_spec["check_ids"]):
                    issues.append(f"{gate}/{role}: policy omits final review matrix check families")
        for question in requirement["questions"]:
            key = (gate, question)
            if key in seen:
                issues.append(f"duplicate policy requirement for {gate}/{question}")
            seen.add(key)
    return issues


def _selected_paper_source(state: Mapping[str, Any]) -> tuple[str, str] | None:
    framework = state.get("paper_framework")
    policy = framework.get("claim_consumption_policy") if isinstance(framework, Mapping) else None
    if not isinstance(policy, Mapping) or (
        policy.get("protocol_version"), policy.get("mode")
    ) != ("1.5.0", "enforce_selected_paper_claim_chain"):
        return None
    source = policy.get("paper_source")
    if not isinstance(source, Mapping):
        return None
    fmt, entrypoint = source.get("format"), source.get("entrypoint")
    if fmt == "latex" and isinstance(entrypoint, str) and re.fullmatch(r"final_latex/[^/]+\.tex", entrypoint):
        return fmt, entrypoint
    if fmt == "docx" and isinstance(entrypoint, str) and re.fullmatch(r"draft_docx/[^/]+\.docx", entrypoint):
        return fmt, entrypoint
    return None


def _active_paper_objects(
    root: Path, state: Mapping[str, Any], gate: str,
    project_read_set: dict[str, str | None],
) -> tuple[tuple[str, str], set[str]]:
    selected = _selected_paper_source(state)
    if selected is None:
        raise ValueError("selected paper source is not current")
    fmt, entrypoint = selected
    objects = {f"paper_source:{entrypoint}"}
    if fmt == "latex":
        main = PROJECT_TX._guarded_path(root, entrypoint)
        scan = REVIEW.claim_tex.scan_static_latex(root, main, selected_carrier=True)
        if scan.get("status") != "scanned":
            raise ValueError("active LaTeX source graph is not statically closed")
        for path, item in scan.get("files", {}).items():
            digest = item.get("sha256") if isinstance(item, Mapping) else None
            if not isinstance(digest, str):
                raise ValueError(f"active LaTeX source has no observed hash: {path}")
            project_read_set[path] = digest
            objects.add(f"source:{path}")
        figures = REVIEW.claim_figure.inspect_static_figures(scan)
        if figures.get("status") != "scanned":
            raise ValueError("active LaTeX Figure source is not statically closed")
        for figure in figures.get("figures", []):
            token = figure.get("image")
            if not isinstance(token, str) or not token:
                raise ValueError("active Figure has no literal image path")
            resolved = (main.parent / token).resolve()
            if not resolved.is_relative_to(root):
                raise ValueError("active Figure image escapes the project")
            relative = resolved.relative_to(root).as_posix()
            image = PROJECT_TX._guarded_path(root, relative)
            digest = PROJECT_TX.sha256_file(image)
            if relative in project_read_set and project_read_set[relative] != digest:
                raise PROJECT_TX.ReadSetConflictError(
                    f"C2 observed different project input: {relative}"
                )
            project_read_set[relative] = digest
            objects.add(f"figure:{relative}")
    else:
        objects.add(f"source:{entrypoint}")
    if gate == "final_review_and_delivery":
        artifacts = state.get("artifacts")
        pdf = artifacts.get("compiled_pdf") if isinstance(artifacts, Mapping) else None
        if not isinstance(pdf, str) or not pdf.endswith(".pdf"):
            raise ValueError("final review has no registered compiled PDF")
        objects.add(f"rendered:{pdf}")
    return selected, objects


def _shared_inputs(record: Mapping[str, Any]) -> bytes:
    """Compare reviewer passes on the same inputs without their role labels."""
    snapshot = record["snapshot"]
    return REVIEW._canonical({
        "gate": record["gate"],
        "criteria_version": record["criteria_version"],
        "scope": {
            "questions": sorted(record["scope"]["questions"]),
            "object_ids": sorted(record["scope"]["object_ids"]),
        },
        "state_fields": REVIEW._sorted_rows(snapshot["state_fields"], "pointer"),
        "project_files": REVIEW._sorted_rows(snapshot["project_files"], "path"),
        "authorities": REVIEW._sorted_rows(snapshot["authorities"], "path"),
    })


def _record_issues(
    record: Mapping[str, Any], row: Mapping[str, Any], requirement: Mapping[str, Any],
    role_spec: Mapping[str, Any], paper_source: tuple[str, str] | None,
    active_paper_objects: set[str],
    host_observation: Any = None,
) -> list[str]:
    issues: list[str] = []
    review_id = record["review_id"]
    required_objects = set(requirement["object_ids"])
    if row["applicability"] != "current" or row["verdict"] != "pass" or row["issues"]:
        issues.append(f"{review_id}: no current complete PASS")
    if row["independence"] != "separated_passes":
        issues.append(f"{review_id}: execution method is not a traceable separated pass")
    if not required_objects.issubset(record["scope"]["object_ids"]):
        issues.append(f"{review_id}: required review objects are not in the declared scope")
    fields = {item["pointer"] for item in record["snapshot"]["state_fields"]}
    if "/review_receipt_policy" not in fields:
        issues.append(f"{review_id}: C2 policy is absent from the reviewed input snapshot")
    authorities = {item["path"] for item in record["snapshot"]["authorities"]}
    if CONTRACT not in authorities:
        issues.append(f"{review_id}: C2 consumption Authority is absent from the review snapshot")
    if paper_source is not None:
        _, entrypoint = paper_source
        paths = {item["path"] for item in record["snapshot"]["project_files"]}
        if "/paper_framework/claim_consumption_policy/paper_source" not in fields or entrypoint not in paths:
            issues.append(f"{review_id}: current selected paper source is outside the review snapshot")
        for object_id in sorted(active_paper_objects):
            kind, _, path = object_id.partition(":")
            if kind in {"paper_source", "source", "figure", "rendered"} and path not in paths:
                issues.append(f"{review_id}: active paper object file is absent from the review snapshot: {object_id}")
    checks = {item["id"]: item for item in record["checks"]}
    required_checks = set(role_spec["check_ids"])
    if not required_checks.issubset(checks):
        issues.append(f"{review_id}: required role checks are absent")
    else:
        covered: set[str] = set()
        for check_id in required_checks:
            check = checks[check_id]
            touched = required_objects.intersection(check["object_ids"])
            if check["result"] != "pass" or not touched:
                issues.append(f"{review_id}: required check {check_id} did not pass its declared object scope")
            covered.update(touched)
        if required_objects - covered:
            issues.append(f"{review_id}: required objects lack passed role checks")
    execution = record["execution"]
    if "command" in execution and execution.get("exit_code") != 0:
        issues.append(f"{review_id}: failed or unknown command exit cannot support a PASS")
    if host_observation is not None:
        if not isinstance(host_observation, Mapping):
            issues.append(f"{review_id}: execution observation is malformed")
        else:
            for key in ("command", "exit_code"):
                if key in host_observation and host_observation[key] != execution.get(key):
                    issues.append(f"{review_id}: observed {key} contradicts the receipt")
            if "exit_code" in host_observation and host_observation["exit_code"] != 0:
                issues.append(f"{review_id}: observed command did not succeed")
    return issues


def _comparison_scope_issues(record: Mapping[str, Any], question: str,
                             framework_path: str) -> list[str]:
    """A primary-model receipt cannot silently authorize a new comparison scope."""
    review_id = record["review_id"]
    fields = {item["pointer"] for item in record["snapshot"]["state_fields"]}
    paths = {item["path"] for item in record["snapshot"]["project_files"]}
    issues = []
    pointer = f"/subproblems/{question}/analysis_comparison/scope_sha256"
    if pointer not in fields:
        issues.append(f"{review_id}: comparison scope identity is outside the review snapshot")
    if framework_path not in paths:
        issues.append(f"{review_id}: comparison specifications are outside the review snapshot")
    return issues


def evaluate_gate(
    project_root: str | Path, gate: str, questions: Sequence[str] | None = None,
    state: Mapping[str, Any] | None = None,
    host_evidence: Mapping[str, Any] | None = None,
    *, comparison_scope: bool = False,
) -> dict[str, Any]:
    """Evaluate only current, policy-declared receipt coverage for an existing gate."""
    requested = ([questions] if isinstance(questions, str) else list(questions)
                 if questions is not None else None)
    report = _report(gate, requested)
    observed = report["observed_sources"]
    root = Path(project_root).expanduser().resolve()
    snapshot: RUNTIME.ProjectStateSnapshot | None = None
    try:
        if gate not in GATES:
            raise ValueError(f"unknown review gate: {gate}")
        if requested is not None and (
            not requested or len(requested) != len(set(requested))
            or any(not isinstance(item, str) or not re.fullmatch(r"Q[1-9][0-9]*", item)
                   for item in requested)
        ):
            raise ValueError("question scope must contain unique Qn identifiers")
        snapshot = RUNTIME.ProjectStateSnapshot.capture(root)
        payload = snapshot.payload()
        observed["project"][PROJECT_TX.STATE_RELATIVE_PATH] = snapshot.describe()["sha256"]
        if state is not None and dict(state) != payload:
            raise ValueError("candidate State differs from the reviewed on-disk State")
        policy = payload.get("review_receipt_policy")
        if policy is None and "review_receipt_policy" not in payload:
            report["status"] = "not_assessed"
            return report
        observed["skill"][safe_yaml.SOURCE_RELATIVE_PATH] = PROJECT_TX.sha256_file(
            ROOT / safe_yaml.SOURCE_RELATIVE_PATH)
        schema = _observe_skill(SCHEMA, observed["skill"])
        contract = _observe_skill(CONTRACT, observed["skill"])
        model = _observe_skill(MODEL_CONTRACT, observed["skill"])
        final_matrix = _observe_skill(FINAL_MATRIX, observed["skill"])
        if schema.get("version") not in {"8.14.0", "8.15.0", "8.16.0"} or contract.get("version") != POLICY_VERSION:
            raise ValueError("unsupported C2 Schema or Authority version")
        policy_shape = (schema.get("$defs") or {}).get("review_receipt_policy")
        if not isinstance(policy_shape, Mapping):
            raise ValueError("C2 policy has no State Schema definition")
        errors = sorted(Draft202012Validator(policy_shape).iter_errors(policy),
                        key=lambda item: tuple(map(str, item.path)))
        if errors:
            raise ValueError("invalid review_receipt_policy: " + "; ".join(
                "/".join(map(str, error.path)) + ": " + error.message for error in errors[:8]
            ))
        if policy["protocol_version"] != POLICY_VERSION or policy["mode"] != "enforce_scoped":
            raise ValueError("unsupported C2 activation policy")
        policy_issues = _policy_issues(policy, model, final_matrix)
        if policy_issues:
            raise ValueError("; ".join(policy_issues))
        subproblems = payload.get("subproblems")
        if not isinstance(subproblems, Mapping):
            raise ValueError("C2 policy requires current State subproblems")
        policy_questions = {
            question for requirement in policy["requirements"]
            for question in requirement["questions"]
        }
        unknown_questions = policy_questions - set(subproblems)
        if unknown_questions:
            raise ValueError(
                "C2 policy names questions absent from current State: "
                + ", ".join(sorted(unknown_questions))
            )
        gate_reqs = [item for item in policy["requirements"] if item["gate"] == gate]
        declared = {question for item in gate_reqs for question in item["questions"]}
        if requested is None:
            requested = sorted(declared)
        report["questions"] = requested
        if not declared or not set(requested).intersection(declared):
            report["status"] = "not_assessed"
            return report
        if not set(requested).issubset(declared):
            raise ValueError("requested review scope mixes declared and undeclared questions")
        if "review_receipts" not in payload:
            raise ValueError("C2 policy is active but review receipts are absent")
        paper_source = None
        active_paper_objects: set[str] = set()
        if gate != "model_challenge":
            paper_source, active_paper_objects = _active_paper_objects(
                root, payload, gate, observed["project"],
            )
        inspection = REVIEW.inspect_project(root, host_evidence=host_evidence)
        for domain in ("project", "skill"):
            for path, digest in inspection["observed_sources"][domain].items():
                if path in observed[domain] and observed[domain][path] != digest:
                    raise PROJECT_TX.ReadSetConflictError(
                        f"C2 and C1 observed different {domain} input: {path}"
                    )
                observed[domain][path] = digest
        if inspection["status"] == "blocked" or inspection["issues"]:
            raise ValueError("C1 receipt inspection is blocked: " + "; ".join(inspection["issues"][:8]))
        rows = {item["review_id"]: item for item in inspection["receipts"]}
        records = payload["review_receipts"]["records"]
        selected: list[Mapping[str, Any]] = []
        for question in requested:
            requirement = next(item for item in gate_reqs if question in item["questions"])
            required_objects = set(requirement["object_ids"])
            if comparison_scope:
                if gate != "model_challenge":
                    raise ValueError("comparison scope applies only to the existing Model Challenge gate")
                comparison = subproblems[question].get("analysis_comparison")
                if (not isinstance(comparison, Mapping)
                        or comparison.get("protocol_version") != "1.0.0"
                        or not isinstance(comparison.get("scope_sha256"), str)
                        or not re.fullmatch(r"[0-9a-f]{64}", comparison["scope_sha256"])):
                    raise ValueError(f"{question}: no current supported comparison scope identity")
                if f"{question}:analysis_comparison" not in required_objects:
                    report["issues"].append(
                        f"{gate}/{question}: comparison scope is absent from the explicit review policy")
            if active_paper_objects - required_objects:
                report["issues"].append(
                    f"{gate}/{question}: policy omits active paper source objects: "
                    + ", ".join(sorted(active_paper_objects - required_objects))
                )
            relevant = [
                item for item in records
                if item["gate"] == gate and question in item["scope"]["questions"]
                and required_objects.intersection(item["scope"]["object_ids"])
            ]
            if not relevant:
                report["issues"].append(f"{gate}/{question}: no receipt covers required objects")
                continue
            for item in relevant:
                row = rows[item["review_id"]]
                if row["applicability"] != "superseded" and (
                    row["applicability"] != "current" or row["verdict"] != "pass" or row["issues"]
                ):
                    report["issues"].append(
                        f"{gate}/{question}: unresolved or inapplicable receipt {item['review_id']}"
                    )
            chosen: list[Mapping[str, Any]] = []
            for role_spec in requirement["roles"]:
                candidates = [
                    item for item in relevant
                    if item["role"] == role_spec["role"]
                    and rows[item["review_id"]]["applicability"] == "current"
                    and required_objects.issubset(item["scope"]["object_ids"])
                ]
                if len(candidates) != 1:
                    report["issues"].append(
                        f"{gate}/{question}/{role_spec['role']}: expected one current full-scope receipt, got {len(candidates)}"
                    )
                    continue
                item = candidates[0]
                report["issues"].extend(_record_issues(
                    item, rows[item["review_id"]], requirement, role_spec, paper_source,
                    active_paper_objects,
                    host_evidence.get(item["review_id"]) if host_evidence is not None else None,
                ))
                if comparison_scope:
                    framework = payload.get("paper_framework") or {}
                    framework_path = framework.get("path", "模型论文框架.md")
                    report["issues"].extend(_comparison_scope_issues(item, question, framework_path))
                chosen.append(item)
            if len(chosen) != len(requirement["roles"]):
                continue
            if len({_shared_inputs(item) for item in chosen}) != 1:
                report["issues"].append(f"{gate}/{question}: reviewer passes do not share one input snapshot")
            pass_ids = [item["execution"].get("pass_id") for item in chosen]
            if any(not pass_id for pass_id in pass_ids) or len(set(pass_ids)) != len(pass_ids):
                report["issues"].append(f"{gate}/{question}: reviewer passes are not distinct")
            if len({REVIEW._review_payload(item) for item in chosen}) != len(chosen):
                report["issues"].append(f"{gate}/{question}: copied substantive review cannot count twice")
            selected.extend(chosen)
        if not report["issues"]:
            unique = {item["review_id"]: item for item in selected}
            report["receipt_ids"] = sorted(unique)
            report["selected_snapshots"] = [
                {
                    "review_id": review_id,
                    "state_fields": item["snapshot"]["state_fields"],
                    "project_files": item["snapshot"]["project_files"],
                    "authorities": item["snapshot"]["authorities"],
                }
                for review_id, item in sorted(unique.items())
            ]
            report["status"] = "passed"
            report["qualification"] = "scoped_receipt_eligible"
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RuntimeError,
            yaml.YAMLError) as exc:
        report["issues"].append(str(exc).replace(str(root), "<project>"))
        report["status"] = "failed"
    finally:
        try:
            if snapshot is not None:
                snapshot.assert_current()
            PROJECT_TX._check_read_set(root, observed["project"])
            PROJECT_TX._check_read_set(ROOT, observed["skill"])
        except (OSError, ValueError, RuntimeError) as exc:
            report["issues"].append(
                "C2 read snapshot changed: " + str(exc).replace(str(root), "<project>")
            )
            report["status"] = "failed"
        if report["status"] != "passed":
            report["qualification"] = "not_granted"
            report["receipt_ids"] = []
            report["selected_snapshots"] = []
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect explicitly scoped C2 receipt eligibility")
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--gate", required=True, choices=sorted(GATES))
    parser.add_argument("--question", action="append", dest="questions")
    args = parser.parse_args()
    report = evaluate_gate(args.project_root, args.gate, questions=args.questions)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if report["status"] == "passed" else 2 if report["status"] == "not_assessed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
