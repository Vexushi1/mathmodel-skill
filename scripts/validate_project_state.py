#!/usr/bin/env python3
"""Validate split result-quality/result-analysis state and paper semantic freshness."""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path
from typing import Any, Mapping

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "core/project_state.schema.yaml"
TAXONOMY_PATH = ROOT / "core/task_taxonomy.yaml"
SOLVED_STATUSES = {"solved", "analyzed", "validated", "written", "completed"}
ANALYZED_STATUSES = {"analyzed", "validated", "written", "completed"}
VALIDATED_STATUSES = {"validated", "written", "completed"}
WRITTEN_STATUSES = {"written", "completed"}
FRAMEWORK_REQUIRED_PHASES = {
    "model_design", "solve_validate", "result_analysis", "figure_evidence",
    "writing_docx", "writing_latex", "ai_cleanup", "latex_compile_quality",
    "review_delivery", "completed",
}
PROPOSITION_DEFAULT_BUDGET = 4
PROPOSITION_ID_PATTERN = re.compile(r"^P[1-9][0-9]*$")
CURRENT_PROPOSITION_REQUIRED_FIELDS = (
    "assumptions_and_domain", "conclusion", "modeling_effect",
    "failure_boundary", "framework_anchor",
)
ARTIFACT_LAYERS = {
    "data", "model", "solution_workbook", "result_analysis_workbook",
    "robustness_workbook", "matlab_script", "figure_bundle", "framework",
}
HIGH_PRECISION_BASES = {"prompt", "official", "reviewer", "project_high_precision"}


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _artifact_exists(project_root: Path, value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and (project_root / value).exists()


def _sha256_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _validate_propositions(
    framework: Mapping[str, Any], *, framework_sync: Any,
) -> tuple[list[str], set[str], bool]:
    issues: list[str] = []
    count = framework.get("proposition_count")
    status = framework.get("proposition_status")
    entries = framework.get("propositions", []) or []

    if not isinstance(count, int) or count < 0:
        issues.append("paper_framework.proposition_count must be a non-negative integer")
    if isinstance(count, int) and count != len(entries):
        issues.append("paper_framework.proposition_count must equal len(paper_framework.propositions)")

    if isinstance(count, int) and count > PROPOSITION_DEFAULT_BUDGET:
        budget_status = framework.get("proposition_budget_status")
        reason = str(framework.get("proposition_budget_reason", "")).strip()
        if budget_status != "justified":
            issues.append(
                f"paper_framework has {count} propositions, above default budget {PROPOSITION_DEFAULT_BUDGET}; "
                "proposition_budget_status must be justified"
            )
        if not reason:
            issues.append("paper_framework.proposition_budget_reason is required above the default proposition budget")
    elif framework.get("proposition_budget_status") == "justification_required":
        issues.append("paper_framework.proposition_budget_status cannot remain justification_required within default budget")

    ids: list[str] = []
    has_stale = status == "stale"
    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping):
            issues.append(f"paper_framework.propositions[{index}] must be a mapping")
            continue
        proposition_id = str(entry.get("id", "")).strip()
        ids.append(proposition_id)
        if not PROPOSITION_ID_PATTERN.fullmatch(proposition_id):
            issues.append(f"invalid proposition id: {proposition_id or '<empty>'}; use P1, P2, ...")
        entry_status = str(entry.get("status", ""))
        if entry_status == "stale":
            has_stale = True
        if entry_status == "current":
            for field in CURRENT_PROPOSITION_REQUIRED_FIELDS:
                if not str(entry.get(field, "")).strip():
                    issues.append(f"{proposition_id}.{field} is required for a current proposition")
    if len(ids) != len(set(ids)):
        issues.append("paper_framework.propositions must use unique IDs")
    proposition_ids = {item for item in ids if item}
    if count == 0 and status in {"planned", "current"}:
        issues.append("paper_framework.proposition_status cannot be planned/current when proposition_count is 0")
    if isinstance(count, int) and count > 0 and status == "not_assessed":
        issues.append("paper_framework.proposition_status cannot be not_assessed when propositions exist")
    return issues, proposition_ids, has_stale


def _validate_terminology(framework: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    entries = framework.get("terminology_registry", []) or []
    ids: list[str] = []
    alias_owner: dict[str, str] = {}
    canonical_terms: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping):
            issues.append(f"paper_framework.terminology_registry[{index}] must be a mapping")
            continue
        term_id = str(entry.get("id", "")).strip()
        canonical = str(entry.get("canonical_term", "")).strip()
        ids.append(term_id)
        if canonical:
            if canonical in canonical_terms:
                issues.append(f"duplicate canonical terminology term: {canonical}")
            canonical_terms.add(canonical)
        aliases = [
            *(entry.get("allowed_aliases", []) or []),
            *(entry.get("discouraged_aliases", []) or []),
        ]
        for raw_alias in aliases:
            alias = str(raw_alias).strip()
            if not alias:
                continue
            prior = alias_owner.get(alias)
            if prior and prior != term_id:
                issues.append(f"terminology alias maps to multiple canonical terms: {alias} -> {prior}, {term_id}")
            alias_owner[alias] = term_id
    if len(ids) != len(set(ids)):
        issues.append("paper_framework.terminology_registry must use unique IDs")
    return issues


def _validate_numeric_profile(framework: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    entries = framework.get("numeric_profile", []) or []
    ids: list[str] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping):
            issues.append(f"paper_framework.numeric_profile[{index}] must be a mapping")
            continue
        metric_id = str(entry.get("id", "")).strip()
        ids.append(metric_id)
        basis = str(entry.get("precision_basis", "")).strip()
        if basis in HIGH_PRECISION_BASES:
            for field in ("abstract_decimals", "body_decimals", "table_decimals"):
                value = entry.get(field)
                if not isinstance(value, int):
                    issues.append(f"{metric_id}.{field} is required for a scored/high-precision metric")
            if basis in {"reviewer", "project_high_precision"}:
                decimals = entry.get("abstract_decimals")
                if isinstance(decimals, int) and decimals < 6:
                    issues.append(
                        f"{metric_id}.abstract_decimals={decimals} conflicts with the declared high-precision scoring profile; "
                        "use at least 6 decimals or change precision_basis with evidence"
                    )
    if len(ids) != len(set(ids)):
        issues.append("paper_framework.numeric_profile must use unique IDs")
    return issues


def _validate_title_claims(framework: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    entries = framework.get("title_claims", []) or []
    ids: list[str] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping):
            issues.append(f"paper_framework.title_claims[{index}] must be a mapping")
            continue
        claim_id = str(entry.get("id", "")).strip()
        ids.append(claim_id)
        if entry.get("status") == "current" and entry.get("claim_type") in {"main_method", "core_mechanism", "core_contribution"}:
            for field in ("related_questions", "body_anchor", "result_evidence", "abstract_anchor", "keyword_link"):
                value = entry.get(field)
                if value in (None, "", []):
                    issues.append(f"{claim_id}.{field} is required for a current substantive title claim")
    if len(ids) != len(set(ids)):
        issues.append("paper_framework.title_claims must use unique IDs")
    return issues


def _validate_paper_fragments(framework: Mapping[str, Any]) -> tuple[list[str], bool]:
    issues: list[str] = []
    entries = framework.get("paper_fragments", []) or []
    ids: list[str] = []
    by_id: dict[str, Mapping[str, Any]] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping):
            issues.append(f"paper_framework.paper_fragments[{index}] must be a mapping")
            continue
        fragment_id = str(entry.get("id", "")).strip()
        ids.append(fragment_id)
        by_id[fragment_id] = entry
    if len(ids) != len(set(ids)):
        issues.append("paper_framework.paper_fragments must use unique IDs")
    for fragment_id, entry in by_id.items():
        for dependency in entry.get("depends_on", []) or []:
            dep = str(dependency)
            if dep.startswith("paper.") and dep not in by_id:
                issues.append(f"{fragment_id}.depends_on references unknown paper fragment: {dep}")
            if dep == fragment_id:
                issues.append(f"{fragment_id} cannot depend on itself")
    has_stale = any(str(entry.get("status", "")) == "stale" for entry in by_id.values())
    return issues, has_stale


def _validate_analysis_dispositions(name: str, state: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    entries = state.get("analysis_evidence_dispositions", []) or []
    ids: list[str] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping):
            issues.append(f"{name}.analysis_evidence_dispositions[{index}] must be a mapping")
            continue
        evidence_id = str(entry.get("id", "")).strip()
        ids.append(evidence_id)
        disposition = entry.get("disposition")
        action = str(entry.get("required_action", "")).strip()
        if disposition in {"modify", "reject"} and not action:
            issues.append(f"{name}.{evidence_id}.required_action is required for {disposition}")
        if disposition == "reject" and state.get("result_analysis_status") == "passed" and "remove" not in action.lower() and "删除" not in action:
            issues.append(
                f"{name}.{evidence_id} rejects a claim while result_analysis_status=passed; "
                "record an explicit remove/rewrite action or set redo_required for a rejected core claim"
            )
    if len(ids) != len(set(ids)):
        issues.append(f"{name}.analysis_evidence_dispositions must use unique IDs")
    return issues


def _derived_legacy_packs(classification: Mapping[str, Any], taxonomy: Mapping[str, Any]) -> list[str]:
    packs: list[str] = []
    objective = classification.get("objective")
    if objective in taxonomy.get("objectives", {}):
        packs.append(taxonomy["objectives"][objective].get("legacy_pack"))
    for structure in classification.get("structures", []) or []:
        if structure in taxonomy.get("structures", {}):
            packs.append(taxonomy["structures"][structure].get("supplemental_pack"))
    return list(dict.fromkeys(item for item in packs if item))


def _validate_classification_aliases(
    name: str, state: Mapping[str, Any], taxonomy: Mapping[str, Any],
) -> list[str]:
    issues: list[str] = []
    classification = state.get("classification") or {}
    capabilities = state.get("capabilities") or {}
    deprecated_capabilities = classification.get("capabilities")
    if deprecated_capabilities is not None and deprecated_capabilities != capabilities:
        issues.append(f"{name}.classification.capabilities must equal top-level capabilities while deprecated alias exists")
    if classification:
        derived = _derived_legacy_packs(classification, taxonomy)
        declared = classification.get("legacy_task_packs")
        if declared is not None and list(declared) != derived:
            issues.append(f"{name}.classification.legacy_task_packs must be derived as {derived}")
        problem_types = state.get("problem_types")
        if problem_types:
            old = [problem_types.get("primary"), *(problem_types.get("secondary", []) or [])]
            old = list(dict.fromkeys(item for item in old if item))
            if old != derived[:3]:
                issues.append(f"{name}.problem_types must match derived compatibility packs {derived[:3]}")
    return issues


def _framework_section_hash(path: Path, anchor: str) -> str | None:
    if not path.is_file() or not anchor.strip():
        return None
    lines = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n").splitlines()
    target = anchor.strip()
    start = next((index for index, line in enumerate(lines) if line.strip() == target), None)
    if start is None:
        start = next(
            (index for index, line in enumerate(lines) if line.lstrip().startswith("#") and target in line.strip()),
            None,
        )
    if start is None:
        return None
    heading = lines[start].lstrip()
    level = len(heading) - len(heading.lstrip("#"))
    end = len(lines)
    for index in range(start + 1, len(lines)):
        stripped = lines[index].lstrip()
        if stripped.startswith("#"):
            next_level = len(stripped) - len(stripped.lstrip("#"))
            if next_level <= level:
                end = index
                break
    text = "\n".join(lines[start:end]).strip() + "\n"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalized_hashes(state: Mapping[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    current = dict(state.get("artifact_hashes", {}) or {})
    validated = dict(state.get("validated_artifact_hashes", {}) or {})
    if "result_analysis_workbook" not in current and "robustness_workbook" in current:
        current["result_analysis_workbook"] = current["robustness_workbook"]
    if "result_analysis_workbook" not in validated and "robustness_workbook" in validated:
        validated["result_analysis_workbook"] = validated["robustness_workbook"]
    if not current:
        if state.get("data_hash"):
            current["data"] = state["data_hash"]
        if state.get("model_hash"):
            current["model"] = state["model_hash"]
    if not validated:
        if state.get("validated_data_hash"):
            validated["data"] = state["validated_data_hash"]
        if state.get("validated_model_hash"):
            validated["model"] = state["validated_model_hash"]
    return current, validated


def _validate_hashes(name: str, state: Mapping[str, Any], status: str) -> list[str]:
    issues: list[str] = []
    current, validated = _normalized_hashes(state)
    stale_layers = set(state.get("stale_layers", []) or [])
    invalid_layers = stale_layers - ARTIFACT_LAYERS
    if invalid_layers:
        issues.append(f"{name}.stale_layers contains invalid layers: {sorted(invalid_layers)}")
    mismatched = {key for key, value in validated.items() if current.get(key) != value}
    stale_flag = state.get("artifacts_stale") is True
    semantic_stale = (
        state.get("result_quality_status") == "failed"
        or state.get("result_analysis_status") == "redo_required"
    )
    if mismatched and not stale_flag:
        issues.append(f"{name}.artifacts_stale must be true while validated hashes differ: {sorted(mismatched)}")
    if stale_flag:
        if semantic_stale:
            if not stale_layers:
                issues.append(f"{name}.stale_layers must be non-empty for semantic stale")
            if not mismatched.issubset(stale_layers):
                issues.append(f"{name}.stale_layers must include changed validated layers: {sorted(mismatched)}")
        elif mismatched != stale_layers:
            issues.append(f"{name}.stale_layers must equal changed validated layers: {sorted(mismatched)}")
    if not stale_flag and stale_layers:
        issues.append(f"{name}.stale_layers must be empty while artifacts_stale is false")
    if status in SOLVED_STATUSES:
        required = {"data", "model", "solution_workbook", "framework"}
        missing = sorted(key for key in required if key not in current or key not in validated)
        if missing:
            issues.append(f"{name} solved status requires current and validated hashes for: {missing}")
    if status in ANALYZED_STATUSES:
        required = {"result_analysis_workbook"}
        missing = sorted(key for key in required if key not in current or key not in validated)
        if missing:
            issues.append(f"{name} analyzed status requires current and validated hashes for: {missing}")
    if status in VALIDATED_STATUSES and mismatched:
        issues.append(f"{name} validated artifact hashes are stale: {sorted(mismatched)}")
    return issues


def validate_state_payload(
    payload: Mapping[str, Any], *, project_root: Path,
    schema_path: Path = SCHEMA_PATH, taxonomy_path: Path = TAXONOMY_PATH,
) -> list[str]:
    issues: list[str] = []
    schema = load_yaml(schema_path)
    taxonomy = load_yaml(taxonomy_path)
    validator = Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(payload), key=lambda item: list(item.path)):
        location = "/".join(str(part) for part in error.path) or "<root>"
        issues.append(f"schema {location}: {error.message}")

    requirements = payload.get("requirements", {})
    completed = set(requirements.get("completed", []))
    pending = set(requirements.get("pending", []))
    if completed.intersection(pending):
        issues.append("requirements.completed and requirements.pending must be disjoint")
    if requirements.get("total") != len(completed | pending):
        issues.append("requirements.total must equal the number of unique completed and pending items")

    project = payload.get("project", {}) or {}
    framework = payload.get("paper_framework", {}) or {}
    phase = str(project.get("current_phase", ""))
    framework_path = project_root / str(framework.get("path", "模型论文框架.md"))
    framework_sync = framework.get("sync_status")
    expected_framework_hash = framework.get("sha256")
    if framework_path.is_file() and expected_framework_hash:
        if _sha256_text(framework_path).lower() != str(expected_framework_hash).lower():
            issues.append("paper_framework.sha256 does not match the current framework file")

    proposition_issues, proposition_ids, _ = _validate_propositions(
        framework, framework_sync=framework_sync
    )
    issues.extend(proposition_issues)
    issues.extend(_validate_terminology(framework))
    issues.extend(_validate_numeric_profile(framework))
    issues.extend(_validate_title_claims(framework))
    fragment_issues, has_stale_fragments = _validate_paper_fragments(framework)
    issues.extend(fragment_issues)

    any_subproblem_stale = False
    for name, state in payload.get("subproblems", {}).items():
        if not isinstance(state, Mapping):
            continue
        status = str(state.get("status", ""))
        capabilities = state.get("capabilities", {}) or {}
        summary_status = state.get("result_summary_status")
        framework_section = str(state.get("framework_section", "")).strip()
        quality_status = state.get("result_quality_status")
        analysis_status = state.get("result_analysis_status")
        issues.extend(_validate_classification_aliases(name, state, taxonomy))
        issues.extend(_validate_hashes(name, state, status))
        issues.extend(_validate_analysis_dispositions(name, state))
        section_hash = (state.get("artifact_hashes", {}) or {}).get("framework")
        if section_hash and framework_path.is_file():
            actual_section_hash = _framework_section_hash(framework_path, framework_section)
            if actual_section_hash != section_hash:
                issues.append(f"{name}.artifact_hashes.framework does not match the current framework section")
        if not framework_section:
            issues.append(f"{name}.framework_section must identify the current framework section")
        proposition_refs = set(state.get("proposition_refs", []) or [])
        unknown_refs = sorted(proposition_refs - proposition_ids)
        if unknown_refs:
            issues.append(f"{name}.proposition_refs contain unknown IDs: {unknown_refs}")
        if status in SOLVED_STATUSES:
            if quality_status != "passed":
                issues.append(f"{name}.result_quality_status must be passed when status is {status}")
            if summary_status != "current":
                issues.append(f"{name}.result_summary_status must be current when status is {status}")
            if not str(state.get("result_summary_anchor", "")).strip():
                issues.append(f"{name}.result_summary_anchor is required when status is {status}")
            if not _artifact_exists(project_root, state.get("solution_workbook")):
                issues.append(f"{name}.solution_workbook must exist when status is {status}")
        if status in ANALYZED_STATUSES:
            if analysis_status != "passed":
                issues.append(f"{name}.result_analysis_status must be passed when status is {status}")
            analysis_path = state.get("result_analysis_workbook") or state.get("robustness_workbook")
            if not _artifact_exists(project_root, analysis_path):
                issues.append(f"{name}.result_analysis_workbook must exist when status is {status}")
            if not state.get("analysis_methods"):
                issues.append(f"{name}.analysis_methods must be non-empty when status is {status}")
        if analysis_status == "redo_required":
            if state.get("artifacts_stale") is not True:
                issues.append(f"{name}.artifacts_stale must be true when result_analysis_status is redo_required")
            if phase not in {"model_design", "solve_validate"}:
                issues.append(f"{name} redo_required must return project.current_phase to model_design or solve_validate")
        if state.get("artifacts_stale") is True:
            any_subproblem_stale = True
            if summary_status == "current":
                issues.append(f"{name}.result_summary_status cannot be current while artifacts_stale is true")
            if proposition_refs:
                issues.append(f"{name}.proposition_refs must be revalidated while artifacts_stale is true")
        if status in VALIDATED_STATUSES:
            if not state.get("evidence"):
                issues.append(f"{name}.evidence must be non-empty when status is {status}")
            if state.get("validation_status") not in {None, "passed"}:
                issues.append(f"{name}.validation_status must be passed when status is {status}")
            if state.get("artifacts_stale") is True:
                issues.append(f"{name} cannot be {status} while artifacts_stale is true")
            if capabilities.get("has_explicit_constraints"):
                value = state.get("max_constraint_violation")
                tolerance = state.get("tolerance")
                if value is None or tolerance is None:
                    issues.append(f"{name} requires tolerance and max_constraint_violation")
                elif float(value) > float(tolerance):
                    issues.append(f"{name} maximum constraint violation exceeds tolerance")
            if state.get("optimality_claim") in {"proven_optimal", "global"} and state.get("optimality_gap") is None:
                issues.append(f"{name} global/proven optimality claim requires optimality_gap")
        if status in WRITTEN_STATUSES:
            paper = state.get("paper_source")
            if paper and not _artifact_exists(project_root, paper):
                issues.append(f"{name}.paper_source does not exist")

    if phase in FRAMEWORK_REQUIRED_PHASES and framework_sync != "current":
        issues.append(f"paper_framework.sync_status must be current in phase {phase}; local stale belongs in paper_framework.paper_fragments")
    if phase in {"review_delivery", "completed"} and has_stale_fragments:
        issues.append(f"paper_framework.paper_fragments contains stale items in phase {phase}")
    if phase == "completed":
        if any_subproblem_stale:
            issues.append("completed project cannot retain stale subproblem artifacts")
        if pending:
            issues.append("completed project cannot retain pending requirements")
        if payload.get("next_gate", {}).get("module") != "completed":
            issues.append("completed project must set next_gate.module to completed")
    return issues


def validate_state_file(path: Path, *, project_root: Path | None = None) -> list[str]:
    root = (project_root or path.parent.parent).resolve()
    return validate_state_payload(load_yaml(path), project_root=root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("state", nargs="?", default="state/project_state.yaml")
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()
    state_path = Path(args.state).resolve()
    if not state_path.is_file():
        raise SystemExit(f"project state not found: {state_path}")
    issues = validate_state_file(state_path, project_root=Path(args.project_root).resolve())
    if issues:
        for issue in issues:
            print("-", issue)
        return 1
    print("project state validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
