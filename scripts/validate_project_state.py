#!/usr/bin/env python3
"""Validate split result-quality/result-analysis state and paper semantic freshness."""
from __future__ import annotations

import argparse
import hashlib
import re
from collections import deque
from pathlib import Path
from typing import Any, Mapping

import yaml
from jsonschema import Draft202012Validator

import artifact_identity as ARTIFACT_IDENTITY
import analysis_prerequisites as ANALYSIS_PREREQUISITES
import runtime_assurance as RUNTIME_ASSURANCE
import stage_code as STAGE_CODE

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
    "data", "model", "primary_code", "analysis_code", "solution_workbook",
    "result_analysis_workbook", "robustness_workbook", "matlab_script",
    "figure_bundle", "framework",
}
HIGH_PRECISION_BASES = {"prompt", "official", "reviewer", "project_high_precision"}
AUXILIARY_REJECT_ACTION_MARKERS = ("remove", "rewrite", "drop", "delete", "删除", "重写", "撤回")
BACKEND_HISTORY_MANIFEST = re.compile(r"^state/backend_history/([0-9a-f]{32})/manifest\.json$")
BACKEND_HISTORY_REPORT = re.compile(r"^state/backend_migration_reports/([0-9a-f]{32})\.yaml$")


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _artifact_exists(project_root: Path, value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and (project_root / value).exists()


def _sha256_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _validate_backend_history(
    payload: Mapping[str, Any], project_root: Path,
    report_path_overrides: Mapping[str, Path] | None,
) -> list[str]:
    """Check durable migration references without re-reading archived user workbooks."""
    execution = payload.get("execution", {}) or {}
    history = execution.get("backend_migration_history", []) if isinstance(execution, Mapping) else []
    if not isinstance(history, list):
        return []  # The JSON Schema reports this shape error.
    issues, seen = [], set()
    root = project_root.resolve()
    for index, item in enumerate(history):
        if not isinstance(item, Mapping):
            continue
        manifest, report = item.get("manifest"), item.get("report")
        manifest_match = BACKEND_HISTORY_MANIFEST.fullmatch(manifest) if isinstance(manifest, str) else None
        report_match = BACKEND_HISTORY_REPORT.fullmatch(report) if isinstance(report, str) else None
        if manifest_match and report_match:
            migration_id = manifest_match.group(1)
            if migration_id != report_match.group(1):
                issues.append(f"execution.backend_migration_history[{index}]: archive and report IDs differ")
            if migration_id in seen:
                issues.append(f"execution.backend_migration_history[{index}]: duplicate migration ID")
            seen.add(migration_id)
        for field, relative in (("manifest", manifest), ("report", report)):
            if not isinstance(relative, str) or not (
                BACKEND_HISTORY_MANIFEST.fullmatch(relative) if field == "manifest"
                else BACKEND_HISTORY_REPORT.fullmatch(relative)
            ):
                continue  # The JSON Schema reports malformed paths.
            path = (report_path_overrides or {}).get(relative) if field == "report" else None
            path = Path(path) if path is not None else root / relative
            try:
                if not path.resolve().is_relative_to(root) or not path.is_file() or path.is_symlink():
                    raise OSError("missing, linked, or outside project root")
                actual = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError:
                issues.append(f"execution.backend_migration_history[{index}].{field}: referenced file is unavailable")
                continue
            expected = item.get("sha256" if field == "manifest" else "report_sha256")
            if isinstance(expected, str) and actual != expected.lower():
                issues.append(f"execution.backend_migration_history[{index}].{field}: raw SHA-256 differs")
    return issues


def _uses_fragment_stale(framework: Mapping[str, Any]) -> bool:
    version = str(framework.get("version", "")).strip()
    return version.startswith("v0.8") or "paper_fragments" in framework


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


def _validate_figure_bindings(
    policy: Mapping[str, Any], fragments: list[Any], claim_ids: set[str], obligations: list[Any],
) -> list[str]:
    """Check declared Figure identities and direct claim edges; no artifact approval occurs here."""
    if "figure_bindings" not in policy:
        return []
    bindings = policy["figure_bindings"]
    if not isinstance(bindings, list):
        return ["paper_framework.claim_consumption_policy.figure_bindings must be an array"]
    issues: list[str] = []
    if len(bindings) > 128:
        issues.append("paper_framework.claim_consumption_policy.figure_bindings budget exceeded (128)")
    fragments_by_id = {row["id"]: row for row in fragments
                       if isinstance(row, Mapping) and isinstance(row.get("id"), str)}
    required_kinds = {row["claim_id"]: {kind for kind in row.get("fragment_kinds", [])
                                        if isinstance(kind, str)}
                      for row in obligations if isinstance(row, Mapping)
                      and isinstance(row.get("claim_id"), str)
                      and isinstance(row.get("fragment_kinds"), list)}
    seen: dict[str, set[str]] = {key: set() for key in
                                 ("figure_id", "fragment_id", "latex_label", "image_path")}
    for index, binding in enumerate(bindings):
        prefix = f"paper_framework.claim_consumption_policy.figure_bindings[{index}]"
        if not isinstance(binding, Mapping):
            issues.append(f"{prefix} must be a mapping")
            continue
        for key, used in seen.items():
            value = binding.get(key)
            if not isinstance(value, str) or not value:
                issues.append(f"{prefix}.{key} must be a nonempty string")
            elif value in used:
                issues.append(f"{prefix}.{key} duplicates a Figure binding: {value}")
            else:
                used.add(value)
        image_path = binding.get("image_path")
        if isinstance(image_path, str):
            parts = image_path.split("/")
            if (any(not part or part in (".", "..") or part != part.strip() or
                        any(ord(char) < 32 or 127 <= ord(char) <= 159 or char in "\\:"
                            for char in part)
                        for part in parts) or
                    not image_path.endswith((".pdf", ".png", ".svg"))):
                issues.append(f"{prefix}.image_path must be a normalized project-relative pdf/png/svg path")
        fragment_id = binding.get("fragment_id")
        if not isinstance(fragment_id, str):
            continue
        fragment = fragments_by_id.get(fragment_id)
        if fragment is None:
            issues.append(f"{prefix}.fragment_id references unknown paper fragment: {fragment_id}")
        elif fragment.get("kind") != "figure_or_table_claim":
            issues.append(f"{prefix}.fragment_id requires a figure_or_table_claim fragment: {fragment_id}")
        elif fragment.get("status") != "current":
            issues.append(f"{prefix}.fragment_id requires a current fragment: {fragment_id}")
        else:
            refs = fragment.get("depends_on")
            linked = {ref[6:] for ref in refs if isinstance(ref, str) and ref.startswith("claim:")} \
                     if isinstance(refs, list) else set()
            if not any(claim_id in claim_ids and "figure_or_table_claim" in required_kinds.get(claim_id, set())
                       for claim_id in linked):
                issues.append(f"{prefix}.fragment_id requires a declared current claim: Figure obligation edge")
    return issues


def _validate_claim_consumption_policy(framework: Mapping[str, Any]) -> list[str]:
    """Check opt-in B2 references without changing legacy fragment semantics."""
    if "claim_consumption_policy" not in framework:
        return []
    policy = framework["claim_consumption_policy"]
    if not isinstance(policy, Mapping):
        return ["paper_framework.claim_consumption_policy must be a mapping"]
    supported_policies = (("1.0.0", "observe"), ("1.1.0", "propagate"),
                          ("1.2.0", "enforce_latex_text"))
    if (policy.get("protocol_version"), policy.get("mode")) not in supported_policies:
        return ["paper_framework.claim_consumption_policy requires a supported protocol_version/mode pair"]
    record = framework.get("claim_evidence")
    if not isinstance(record, Mapping):
        return ["paper_framework.claim_consumption_policy requires a B1 claim_evidence record"]
    claims = record.get("claims")
    obligations = policy.get("required_consumptions")
    fragments = framework.get("paper_fragments")
    if not isinstance(claims, list) or not isinstance(obligations, list) or not isinstance(fragments, list):
        return ["paper_framework.claim_consumption_policy requires claim and paper fragment arrays"]
    issues: list[str] = []
    if len(fragments) > 512:
        return ["paper_framework.claim_consumption_policy fragment budget exceeded (512)"]
    claim_scope: dict[str, str] = {}
    for claim in claims:
        if not isinstance(claim, Mapping):
            continue
        claim_id, scope = claim.get("id"), claim.get("scope")
        if not isinstance(claim_id, str):
            continue
        if claim_id in claim_scope:
            issues.append(f"paper_framework.claim_evidence has duplicate claim IDs: {claim_id}")
        claim_scope[claim_id] = scope if isinstance(scope, str) else ""
    required_ids: set[str] = set()
    for row in obligations:
        if not isinstance(row, Mapping) or not isinstance(row.get("claim_id"), str):
            continue
        claim_id = row["claim_id"]
        if claim_id in required_ids:
            issues.append(f"paper_framework.claim_consumption_policy has duplicate claim obligations: {claim_id}")
        required_ids.add(claim_id)
        if claim_id not in claim_scope:
            issues.append(f"paper_framework.claim_consumption_policy references unknown claim: {claim_id}")
    issues.extend(_validate_figure_bindings(policy, fragments, set(claim_scope), obligations))
    fragment_ids = {row.get("id") for row in fragments if isinstance(row, Mapping) and isinstance(row.get("id"), str)}
    dependencies: dict[str, list[str]] = {}
    edge_count = 0
    for fragment in fragments:
        if not isinstance(fragment, Mapping) or not isinstance(fragment.get("id"), str):
            continue
        fragment_id = fragment["id"]
        raw_dependencies = fragment.get("depends_on")
        if not isinstance(raw_dependencies, list):
            continue
        edge_count += len(raw_dependencies)
        dependencies[fragment_id] = []
        for ref in raw_dependencies:
            if not isinstance(ref, str):
                continue
            if ref.startswith("claim:"):
                claim_id = ref[6:]
                if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", claim_id):
                    issues.append(f"{fragment_id}.depends_on has malformed claim reference: {ref}")
                elif claim_id not in claim_scope:
                    issues.append(f"{fragment_id}.depends_on references unknown claim: {claim_id}")
                else:
                    claim_question, fragment_scope = claim_scope[claim_id], fragment.get("scope")
                    if (re.fullmatch(r"Q[1-9][0-9]*", claim_question)
                            and isinstance(fragment_scope, str)
                            and re.fullmatch(r"Q[1-9][0-9]*", fragment_scope)
                            and fragment_scope != claim_question):
                        issues.append(f"{fragment_id} scope {fragment_scope} conflicts with claim {claim_id} scope {claim_question}")
            elif ref.startswith("paper.") and ref in fragment_ids:
                dependencies[fragment_id].append(ref)
    if edge_count > 2048:
        issues.append("paper_framework.claim_consumption_policy fragment dependency edge budget exceeded (2048)")
        return issues
    remaining = {fragment_id: len(set(refs)) for fragment_id, refs in dependencies.items()}
    dependents: dict[str, set[str]] = {fragment_id: set() for fragment_id in dependencies}
    for fragment_id, refs in dependencies.items():
        for ref in refs:
            dependents[ref].add(fragment_id)
    ready = deque(sorted(fragment_id for fragment_id, count in remaining.items() if count == 0))
    visited = 0
    while ready:
        fragment_id = ready.popleft()
        visited += 1
        for dependent in sorted(dependents[fragment_id]):
            remaining[dependent] -= 1
            if remaining[dependent] == 0:
                ready.append(dependent)
    if visited != len(dependencies):
        issues.append("paper_framework.paper_fragments contains a dependency cycle under claim consumption policy")
    return issues


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
        if disposition == "reject" and state.get("result_analysis_status") == "passed":
            lowered = action.lower()
            if not any(marker in lowered or marker in action for marker in AUXILIARY_REJECT_ACTION_MARKERS):
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


def _normalized_hashes(state: Mapping[str, Any]) -> tuple[dict[str, str], dict[str, str], list[str]]:
    issues = ARTIFACT_IDENTITY.entry_alias_issues(state)
    try:
        current = ARTIFACT_IDENTITY.normalize_artifact_hashes(
            state.get("artifact_hashes"), legacy_primary_fallback=state.get("model_hash")
        )
        validated = ARTIFACT_IDENTITY.normalize_artifact_hashes(
            state.get("validated_artifact_hashes"),
            legacy_primary_fallback=state.get("validated_model_hash"),
        )
    except ARTIFACT_IDENTITY.ArtifactIdentityError:
        # The detailed issue is already recorded. Keep deterministic partial maps so the
        # caller can report other state problems without silently selecting a winner.
        current = {key: value for key, value in dict(state.get("artifact_hashes", {}) or {}).items() if key != "model"}
        validated = {key: value for key, value in dict(state.get("validated_artifact_hashes", {}) or {}).items() if key != "model"}
    if "result_analysis_workbook" not in current and "robustness_workbook" in current:
        current["result_analysis_workbook"] = current["robustness_workbook"]
    if "result_analysis_workbook" not in validated and "robustness_workbook" in validated:
        validated["result_analysis_workbook"] = validated["robustness_workbook"]
    if "data" not in current and state.get("data_hash"):
        current["data"] = state["data_hash"]
    if "data" not in validated and state.get("validated_data_hash"):
        validated["data"] = state["validated_data_hash"]
    return current, validated, issues


def _contract_stale_coverage(state: Mapping[str, Any], stale_layers: set[str]) -> set[str]:
    contract = load_yaml(ROOT / "core/state_transition_contract.yaml")
    current, validated, _ = _normalized_hashes(state)
    closed: set[str] = set()
    accepted_updates: dict[str, str] = {}
    for execution, quality, layers in (
        ("primary_execution_status", "result_quality_status", {"data", "primary_code", "solution_workbook"}),
        ("analysis_execution_status", "result_analysis_status", {"analysis_code", "result_analysis_workbook"}),
    ):
        if (state.get(execution) == "accepted" and state.get(quality) == "passed"
                and all(current.get(layer) and current.get(layer) == validated.get(layer) for layer in layers)):
            closed.update(layers)
            accepted_updates.update({execution: "accepted", quality: "passed"})
    for execution, code_layer, code_hash in (
        ("primary_execution_status", "primary_code", "primary_code_sha256"),
        ("analysis_execution_status", "analysis_code", "analysis_code_sha256"),
    ):
        if (state.get(execution) in {"code_delivered", "awaiting_user_execution", "workbook_received"}
                and current.get(code_layer) and current[code_layer] == state.get(code_hash)):
            accepted_updates[execution] = state[execution]
    covered: set[str] = set()
    for profile in (contract.get("profiles") or {}).values():
        layers = set(profile.get("stale_layers", []) or []) - closed
        updates = {**(profile.get("set") or {}), **{
            key: value for key, value in (profile.get("set_if_present") or {}).items() if key in state
        }}
        if layers.issubset(stale_layers) and all(
            state.get(key) == value or (key in accepted_updates and state.get(key) == accepted_updates[key])
            for key, value in updates.items()
        ):
            covered.update(layers)
    return covered


def _validate_hashes(name: str, state: Mapping[str, Any], status: str) -> list[str]:
    issues: list[str] = []
    current, validated, alias_issues = _normalized_hashes(state)
    issues.extend(f"{name}.{item}" for item in alias_issues)
    raw_stale_layers = set(state.get("stale_layers", []) or [])
    invalid_layers = raw_stale_layers - ARTIFACT_LAYERS
    stale_layers = set(ARTIFACT_IDENTITY.normalize_stale_layers(raw_stale_layers))
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
            covered = _contract_stale_coverage(state, stale_layers)
            if not mismatched.issubset(stale_layers) or not stale_layers.issubset(mismatched | covered):
                issues.append(f"{name}.stale_layers must equal changed validated layers or complete applicable transition profiles: {sorted(mismatched)}")
    if not stale_flag and stale_layers:
        issues.append(f"{name}.stale_layers must be empty while artifacts_stale is false")
    if status in SOLVED_STATUSES:
        required = {"data", "primary_code", "solution_workbook", "framework"}
        missing = sorted(key for key in required if key not in current or key not in validated)
        if missing:
            issues.append(f"{name} solved status requires current and validated hashes for: {missing}")
    if status in ANALYZED_STATUSES and state.get("result_analysis_status") != "not_required":
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
    framework_path_override: Path | None = None,
    framework_text_override: str | None = None,
    report_path_overrides: Mapping[str, Path] | None = None,
) -> list[str]:
    if not isinstance(payload, Mapping):
        return ["schema <root>: project state must be a mapping"]
    issues: list[str] = []
    schema = load_yaml(schema_path)
    taxonomy = load_yaml(taxonomy_path)
    validator = Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(payload), key=lambda item: list(item.path)):
        location = "/".join(str(part) for part in error.path) or "<root>"
        issues.append(f"schema {location}: {error.message}")

    issues.extend(_validate_backend_history(payload, project_root, report_path_overrides))

    backend_report = STAGE_CODE.inspect_project_backend_declarations(payload)
    if backend_report["kind"] not in {"unselected", "canonical_declarations"}:
        issues.append(f"current project backend state is {backend_report['kind']}; explicit selection or migration is required")
    issues.extend(f"project backend: {item}" for item in backend_report["issues"])
    project_backend = (backend_report["selected_backend"]
                       if backend_report["kind"] == "canonical_declarations" and not backend_report["issues"] else None)
    if backend_report["kind"] == "unselected":
        numerical_layers = {"primary_code", "analysis_code", "solution_workbook", "result_analysis_workbook",
                            "robustness_workbook"}
        subproblems = payload.get("subproblems") or {}
        if isinstance(subproblems, Mapping):
            for name, entry in subproblems.items():
                if not isinstance(entry, Mapping):
                    continue
                hashes = (entry.get("artifact_hashes"), entry.get("validated_artifact_hashes"))
                has_numeric_hash = any(
                    isinstance(values, Mapping) and bool(numerical_layers & set(values)) for values in hashes
                )
                if (entry.get("primary_code_sha256") or entry.get("analysis_code_sha256") or has_numeric_hash):
                    issues.append(f"{name}: numerical delivery identity requires explicit project backend selection")

    requirements = payload.get("requirements", {})
    completed = set(requirements.get("completed", []))
    pending = set(requirements.get("pending", []))
    if completed.intersection(pending):
        issues.append("requirements.completed and requirements.pending must be disjoint")
    if requirements.get("total") != len(completed | pending):
        issues.append("requirements.total must equal the number of unique completed and pending items")

    project = payload.get("project", {}) or {}
    framework = payload.get("paper_framework", {}) or {}
    fragment_mode = _uses_fragment_stale(framework)
    phase = str(project.get("current_phase", ""))
    # A transaction validator must inspect the staged companion framework that
    # belongs to this candidate, not the previous live framework bytes.
    framework_path = (framework_path_override if framework_path_override is not None
                      else project_root / str(framework.get("path", "模型论文框架.md")))
    framework_sync = framework.get("sync_status")
    expected_framework_hash = framework.get("sha256")
    if expected_framework_hash and (framework_text_override is not None or framework_path.is_file()):
        actual_framework_hash = (
            hashlib.sha256(framework_text_override.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")).hexdigest()
            if framework_text_override is not None else _sha256_text(framework_path)
        )
        if actual_framework_hash.lower() != str(expected_framework_hash).lower():
            issues.append("paper_framework.sha256 does not match the current framework file")

    proposition_issues, proposition_ids, proposition_stale = _validate_propositions(
        framework, framework_sync=framework_sync
    )
    issues.extend(proposition_issues)
    issues.extend(_validate_terminology(framework))
    issues.extend(_validate_numeric_profile(framework))
    issues.extend(_validate_title_claims(framework))
    fragment_issues, has_stale_fragments = _validate_paper_fragments(framework)
    issues.extend(fragment_issues)
    issues.extend(_validate_claim_consumption_policy(framework))

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
        from conformance_gate import stored_issues
        issues.extend(stored_issues(state, str(name)))
        solver_execution = state.get("solver_execution") or {}
        if isinstance(solver_execution, Mapping):
            for stage, field in (("primary", "code"), ("analysis", "result_analysis_code")):
                execution_status = state.get(f"{stage}_execution_status")
                new_code = STAGE_CODE.requires_bundle_binding(
                    project_root, state, stage, project_backend=project_backend)
                delivered = state.get(field) or execution_status in {
                    "code_delivered", "awaiting_user_execution", "workbook_received", "accepted",
                }
                if new_code and delivered and project_backend is not None:
                    issues.extend(f"{name}: {issue}" for issue in STAGE_CODE.validate_stage_binding(
                        project_root, state, stage, require_validated=execution_status == "accepted",
                        project_backend=project_backend,
                    ))
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
        if analysis_status == "not_required":
            if not str(state.get("result_analysis_requirement_reason") or "").strip():
                issues.append(f"{name}.result_analysis_requirement_reason is required for not_required")
            issues.extend(f"{name}: {item}" for item in ANALYSIS_PREREQUISITES.primary_issues(project_root, payload, state))
            if status == "analyzed":
                issues.append(f"{name}.status=analyzed requires actual passed analysis, not not_required")
            if state.get("analysis_execution_status") == "accepted":
                issues.append(f"{name}.not_required must not claim accepted analysis execution")
        elif status in ANALYZED_STATUSES:
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

    if fragment_mode:
        if phase in FRAMEWORK_REQUIRED_PHASES and framework_sync != "current":
            issues.append(f"paper_framework.sync_status must be current in phase {phase}; local stale belongs in paper_framework.paper_fragments")
        if phase in {"review_delivery", "completed"} and has_stale_fragments:
            issues.append(f"paper_framework.paper_fragments contains stale items in phase {phase}")
    else:
        legacy_any_stale = any_subproblem_stale or proposition_stale
        if phase in FRAMEWORK_REQUIRED_PHASES and framework_sync != "current" and not legacy_any_stale:
            issues.append(f"paper_framework.sync_status must be current in phase {phase}")
        if legacy_any_stale and framework_sync == "current":
            issues.append("paper_framework.sync_status cannot remain current while a legacy subproblem or proposition is stale")

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
    if path.resolve() == (root / "state/project_state.yaml").resolve():
        try:
            snapshot = RUNTIME_ASSURANCE.ProjectStateSnapshot.capture(root)
            issues = validate_state_payload(snapshot.payload(), project_root=root)
            snapshot.assert_current()
            return issues
        except RUNTIME_ASSURANCE.ProjectStateReadError as exc:
            return [str(exc)]
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
