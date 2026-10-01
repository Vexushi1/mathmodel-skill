#!/usr/bin/env python3
"""Runtime context hydration and assurance helpers for the HSK resolver."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
from typing import Any, Iterable

import yaml
import safe_yaml
from jsonschema import Draft202012Validator

from semantic_identity import (
    SEMANTIC_IDENTITY_SCHEMA_VERSION,
    SemanticIdentityError,
    semantic_revision_issues,
    inspect_question_semantics,
    question_sections,
)
import artifact_identity as ARTIFACT_IDENTITY
import analysis_prerequisites as ANALYSIS_PREREQUISITES
import analysis_comparison_gate as COMPARISON
import conformance_gate as CONFORMANCE
import stage_code as STAGE_CODE
import state_transitions as STATE_TRANSITIONS
from project_transaction import JOURNAL_RELATIVE_PATH, STATE_RELATIVE_PATH, ProjectTransactionError, state_generation

FRAMEWORK_RELATIVE_PATH = "模型论文框架.md"
QUALIFIED_ARTIFACT_ALIASES = {
    "locked_model_spec": "locked_model_spec",
    "preprocessing_workbook": "preprocessing_workbook",
    "accepted_preprocessing_workbook": "preprocessing_workbook",
    "accepted_solution_workbook": "accepted_solution_workbook",
    "solution_workbook": "accepted_solution_workbook",
    "solved_results": "accepted_solution_workbook",
    "result_quality_report": "accepted_solution_workbook",
    "accepted_result_analysis_workbook": "accepted_result_analysis_workbook",
    "result_analysis_workbook": "accepted_result_analysis_workbook",
    "validated_results": "validated_results",
}
STRUCTURED_IDENTITY_FIELDS = {
    "semantic_identity_schema_version",
    "semantic_identity_hash",
    "validated_semantic_identity_hash",
    "approved_semantic_identity_hash",
    "semantic_text_hash",
}
STRUCTURED_REJECTION_POLICY = ("1.4.0", "enforce_latex_text_and_figure_chain")
SELECTED_PAPER_CLAIM_POLICY = ("1.5.0", "enforce_selected_paper_claim_chain")
STRUCTURED_REJECTION_POLICIES = {
    STRUCTURED_REJECTION_POLICY,
    SELECTED_PAPER_CLAIM_POLICY,
}
LEGACY_CLAIM_CONSUMPTION_POLICIES = {
    ("1.0.0", "observe"),
    ("1.1.0", "propagate"),
    ("1.2.0", "enforce_latex_text"),
    ("1.3.0", "enforce_latex_text_and_figure_chain"),
}
STRUCTURED_DISPOSITION_FIELDS = {
    "id", "method_or_source", "target_claim", "disposition", "impact_scope",
    "return_stage", "key_finding", "required_action", "paper_or_figure_anchor", "status",
}


def _unique(items: Iterable[str | None]) -> list[str]:
    return list(dict.fromkeys(str(item) for item in items if item and str(item).strip()))


def _structured_disposition_issue(row: dict[str, Any]) -> str | None:
    """Validate the runtime-relevant exact-1.4 shape for current modify/reject rows."""
    required = {
        "id", "method_or_source", "target_claim", "disposition",
        "impact_scope", "key_finding", "required_action",
    }
    missing = sorted(required - set(row))
    unknown = sorted(repr(key) for key in set(row) - STRUCTURED_DISPOSITION_FIELDS)
    if missing:
        return f"missing required fields {missing}"
    if unknown:
        return f"unknown fields {unknown}"
    identifier = row.get("id")
    if not isinstance(identifier, str) or re.fullmatch(r"E[1-9][0-9]*", identifier) is None:
        return "id must match E1, E2, ..."
    for field in ("method_or_source", "target_claim", "key_finding", "required_action"):
        value = row.get(field)
        if not isinstance(value, str) or not value.strip():
            return f"{field} must be a non-empty string"
    anchor = row.get("paper_or_figure_anchor")
    if "paper_or_figure_anchor" in row and not isinstance(anchor, str):
        return "paper_or_figure_anchor must be a string"
    scope = row.get("impact_scope")
    if (not isinstance(scope, str)
            or scope not in {"auxiliary_wording", "core_answer", "model_validity"}):
        return "impact_scope is invalid"
    disposition = row.get("disposition")
    if disposition == "modify":
        return "modify must not declare return_stage" if "return_stage" in row else None
    expected = {
        "auxiliary_wording": None,
        "core_answer": "solve_validate",
        "model_validity": "model_design",
    }[scope]
    if expected is None:
        return "auxiliary_wording reject must omit return_stage" if "return_stage" in row else None
    if row.get("return_stage") != expected:
        return f"{scope} reject requires return_stage={expected}"
    return None


def _exact_structured_policy_issues(policy: dict[str, Any]) -> list[str]:
    schema_path = Path(__file__).resolve().parent.parent / "core" / "project_state.schema.yaml"
    try:
        schema = safe_yaml.safe_load(schema_path.read_text(encoding="utf-8")) or {}
        validator = Draft202012Validator({
            "$ref": "#/$defs/claim_consumption_policy", "$defs": schema["$defs"],
        })
    except (OSError, yaml.YAMLError, KeyError, TypeError) as exc:
        return [f"claim-consumption policy schema is unavailable: {exc}"]
    issues: list[str] = []
    for error in sorted(
        validator.iter_errors(policy),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    ):
        location = ".".join(str(item) for item in error.absolute_path) or "<root>"
        issues.append(f"{location}: {error.message}")
    return issues


def _dependency_shape_issue(subproblems: Any) -> str | None:
    """Reject dependency shapes the compatibility parser would otherwise skip."""
    if not isinstance(subproblems, dict):
        return "subproblems must be a mapping"
    for question, entry in subproblems.items():
        if not isinstance(entry, dict) or "depends_on" not in entry:
            continue
        dependencies = entry.get("depends_on")
        if not isinstance(dependencies, list):
            return f"{question}.depends_on must be a list"
        for index, dependency in enumerate(dependencies):
            if isinstance(dependency, str):
                if re.fullmatch(r"Q[1-9][0-9]*", dependency) is None:
                    return f"{question}.depends_on[{index}] must name Q1, Q2, ..."
                continue
            if not isinstance(dependency, dict):
                return f"{question}.depends_on[{index}] must be a string or mapping"
            unknown = sorted(repr(key) for key in set(dependency) - {"question", "kind", "note"})
            if unknown:
                return f"{question}.depends_on[{index}] has unknown fields {unknown}"
            source = dependency.get("question")
            if (not isinstance(source, str)
                    or re.fullmatch(r"Q[1-9][0-9]*", source) is None):
                return f"{question}.depends_on[{index}].question must match Q1, Q2, ..."
            if "kind" in dependency and not isinstance(dependency.get("kind"), str):
                return f"{question}.depends_on[{index}].kind must be a string"
            if "note" in dependency and not isinstance(dependency.get("note"), str):
                return f"{question}.depends_on[{index}].note must be a string"
    return None


def _current_structured_rejections(
    state: dict[str, Any], questions: Iterable[str],
) -> dict[str, dict[str, Any]]:
    """Return fail-closed runtime effects for current structured B2 policies."""
    framework = state.get("paper_framework")
    policy_present = isinstance(framework, dict) and "claim_consumption_policy" in framework
    policy = framework.get("claim_consumption_policy") if policy_present else None
    pair = (
        (policy.get("protocol_version"), policy.get("mode"))
        if isinstance(policy, dict) else None
    )
    active = pair in STRUCTURED_REJECTION_POLICIES
    policy_error = None
    if "paper_framework" in state and not isinstance(framework, dict):
        policy_error = "paper_framework is malformed"
    elif policy_present and not isinstance(policy, dict):
        policy_error = "paper_framework.claim_consumption_policy is malformed"
    elif policy_present and pair not in (LEGACY_CLAIM_CONSUMPTION_POLICIES
                                         | STRUCTURED_REJECTION_POLICIES):
        policy_error = f"claim-consumption policy pair is unsupported or incomplete: {pair!r}"
    elif active:
        policy_issues = _exact_structured_policy_issues(policy)
        if policy_issues:
            label = "1.4" if pair == STRUCTURED_REJECTION_POLICY else "1.5"
            policy_error = f"exact B2 {label} claim-consumption policy is malformed: " + "; ".join(policy_issues)
    requested = [str(question) for question in questions]
    results: dict[str, dict[str, Any]] = {}
    subproblems = state.get("subproblems", {})
    contract_path = Path(__file__).resolve().parent.parent / "core" / "state_transition_contract.yaml"
    contract = safe_yaml.safe_load(contract_path.read_text(encoding="utf-8")) or {}
    events = contract.get("transition_events", {}) or {}
    rules = contract.get("dependency_rules", {}) or {}
    profiles = contract.get("profiles", {}) or {}
    known_questions = set(requested)
    if isinstance(subproblems, dict):
        known_questions.update(str(question) for question in subproblems)

    def result_for(question: str) -> dict[str, Any]:
        return results.setdefault(question, {
            "blocks_primary": False,
            "blocks_model": False,
            "primary_reasons": [],
            "model_reasons": [],
            "conflicts": [],
        })

    for question in sorted(known_questions):
        result_for(question)

    signals: list[tuple[str, str]] = []

    def emit_event(question: str, event: str) -> None:
        spec = events.get(event, {}) if isinstance(events, dict) else {}
        emitted = {str(item) for item in spec.get("emitted_impacts", []) or []}
        signals.extend((question, signal) for signal in sorted({"*", *emitted}))

    def block_invalid(question: str, reason: str) -> None:
        result = result_for(question)
        result["blocks_primary"] = True
        result["blocks_model"] = True
        result["primary_reasons"].append(reason)
        result["model_reasons"].append(reason)
        result["conflicts"].append(reason)
        signals.extend((question, signal) for signal in ("*", "data", "model", "parameter", "result"))

    if policy_error:
        for question in sorted(known_questions):
            block_invalid(question, f"{policy_error}; runtime qualification is blocked")
        return results
    comparison_questions = {str(q) for q, entry in subproblems.items()
                            if isinstance(entry, dict) and COMPARISON.present(entry)} if isinstance(subproblems, dict) else set()
    if not active and not comparison_questions:
        return results
    b2_label = ("1.4" if pair == STRUCTURED_REJECTION_POLICY else "1.5") if active else "analysis-comparison 1.0"

    for question in sorted(known_questions):
        result = result_for(question)
        item = subproblems.get(question, {}) if isinstance(subproblems, dict) else {}
        if not active and question not in comparison_questions:
            continue
        comparison = item.get("analysis_comparison", {}) if isinstance(item, dict) else {}
        checks = comparison.get("checks", []) if isinstance(comparison, dict) else []
        if not isinstance(checks, list):
            block_invalid(question, f"{question}.analysis_comparison.checks is malformed")
            continue
        references = {row["disposition_ref"] for row in checks if isinstance(row, dict)
                      and isinstance(row.get("disposition_ref"), str)}
        if not isinstance(item, dict):
            block_invalid(question, f"{question} is malformed under B2 {b2_label}")
            continue
        rows = item.get("analysis_evidence_dispositions", []) if isinstance(item, dict) else []
        if not isinstance(rows, list):
            block_invalid(
                question, f"{question}.analysis_evidence_dispositions is malformed under B2 {b2_label}",
            )
            continue
        current_ids = [
            row.get("id") for row in rows
            if isinstance(row, dict) and row.get("status", "current") == "current"
            and isinstance(row.get("disposition"), str)
            and row.get("disposition") in {"modify", "reject"}
            and isinstance(row.get("id"), str)
        ]
        duplicate_ids = sorted({identifier for identifier in current_ids if current_ids.count(identifier) > 1})
        if duplicate_ids:
            block_invalid(
                question,
                f"{question}.analysis_evidence_dispositions has duplicate current B2 {b2_label} IDs: {duplicate_ids}",
            )
            continue
        for index, row in enumerate(rows):
            if not active and (not isinstance(row, dict) or row.get("id") not in references):
                continue
            if not isinstance(row, dict):
                block_invalid(
                    question,
                    f"{question}.analysis_evidence_dispositions[{index}] is malformed under B2 {b2_label}",
                )
                continue
            status = row.get("status", "current")
            if not isinstance(status, str) or status not in {"current", "resolved", "stale"}:
                block_invalid(
                    question,
                    f"{question}.analysis_evidence_dispositions[{index}].status is malformed under B2 {b2_label}",
                )
                continue
            if (status == "resolved" and row.get("id") in references and row.get("disposition") == "reject"
                    and row.get("impact_scope") in {"core_answer", "model_validity"}):
                status = "current"  # Resolving wording cannot restore rejected numerical/model validity.
            if status != "current":
                continue
            disposition = row.get("disposition")
            if not isinstance(disposition, str) or disposition not in {"support", "modify", "reject"}:
                block_invalid(
                    question,
                    f"{question}.analysis_evidence_dispositions[{index}].disposition is malformed under B2 {b2_label}",
                )
                continue
            if disposition not in {"modify", "reject"}:
                continue
            shape_issue = _structured_disposition_issue(row)
            evidence_id = str(row.get("id") or f"index {index}")
            if shape_issue:
                block_invalid(
                    question,
                    f"{question}.{evidence_id} is a malformed current B2 {b2_label} {disposition}: {shape_issue}",
                )
                continue
            if disposition == "modify":
                continue
            scope = row.get("impact_scope")
            if scope == "core_answer":
                result["blocks_primary"] = True
                result["primary_reasons"].append(
                    f"{question}.{evidence_id} is a current B2 {b2_label} core-answer rejection"
                )
                emit_event(question, "core_answer_rejected")
            elif scope == "model_validity":
                reason = f"{question}.{evidence_id} is a current B2 {b2_label} model-validity rejection"
                result["blocks_primary"] = True
                result["blocks_model"] = True
                result["primary_reasons"].append(reason)
                result["model_reasons"].append(reason)
                emit_event(question, "model_validity_rejected")
    by_source: dict[str, list[dict[str, Any]]] = {}
    dependency_issue = _dependency_shape_issue(subproblems)
    if dependency_issue:
        reason = f"project dependency declarations are malformed under B2 {b2_label}: {dependency_issue}"
        for question in sorted(known_questions):
            block_invalid(question, reason)
        return results
    try:
        dependency_rows = STATE_TRANSITIONS.dependency_edges(subproblems)
    except (TypeError, ValueError) as exc:
        reason = f"project dependency declarations are malformed under B2 {b2_label}: {exc}"
        for question in sorted(known_questions):
            block_invalid(question, reason)
        return results
    for edge in dependency_rows:
        by_source.setdefault(str(edge["source"]), []).append(edge)
    visited: set[tuple[str, str]] = set()
    applied_edges: set[tuple[str, str, str]] = set()
    cursor = 0
    while cursor < len(signals):
        source, signal = signals[cursor]
        cursor += 1
        if (source, signal) in visited:
            continue
        visited.add((source, signal))
        for edge in by_source.get(source, []):
            kind = str(edge["kind"])
            rule = rules.get(kind, {}) if isinstance(rules, dict) else {}
            triggers = set(rule.get("trigger_impacts", []) or []) if isinstance(rule, dict) else set()
            if not (signal == "*" if "*" in triggers else signal in triggers):
                continue
            edge_key = (source, str(edge["target"]), kind)
            if edge_key in applied_edges:
                continue
            applied_edges.add(edge_key)
            target = str(edge["target"])
            profile_name = str(rule.get("target_profile", ""))
            profile = profiles.get(profile_name, {}) if isinstance(profiles, dict) else {}
            target_result = result_for(target)
            stale_layers = set(profile.get("stale_layers", []) or []) if isinstance(profile, dict) else set()
            updates = {
                **(profile.get("set", {}) or {}),
                **(profile.get("set_if_present", {}) or {}),
            } if isinstance(profile, dict) else {}
            reason = f"{target} depends on rejected {source} through {kind}"
            if ("solution_workbook" in stale_layers
                    or updates.get("result_quality_status") not in {None, "passed"}
                    or "primary_execution_status" in updates):
                target_result["blocks_primary"] = True
                if reason not in target_result["primary_reasons"]:
                    target_result["primary_reasons"].append(reason)
            if any(field in updates for field in (
                "human_model_approval_status", "model_challenge_status", "semantic_closure_status",
            )):
                target_result["blocks_model"] = True
                if reason not in target_result["model_reasons"]:
                    target_result["model_reasons"].append(reason)
            emitted = {str(item) for item in rule.get("emitted_impacts", []) or []}
            signals.extend((target, next_signal) for next_signal in sorted({"*", *emitted}))
    return results


class ProjectStateReadError(ValueError):
    """A read-only plan cannot safely use the current project-state bytes."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        super().__init__(f"{code}: {detail}")


def _read_state_bytes(root: Path) -> bytes | None:
    """Observe state without opening a writer lock or recovering a transaction."""
    paths = {}
    for relative in (STATE_RELATIVE_PATH, JOURNAL_RELATIVE_PATH):
        path = root / relative
        if not path.resolve().is_relative_to(root):
            raise ProjectStateReadError("state_path_outside_project_root", relative)
        paths[relative] = path
    journal = paths[JOURNAL_RELATIVE_PATH]
    if journal.exists() or journal.is_symlink():
        raise ProjectStateReadError("recovery_required", "project transaction journal requires explicit recovery")
    path = paths[STATE_RELATIVE_PATH]
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        if path.is_symlink():
            raise ProjectStateReadError("invalid_project_state", "project state link target is missing")
        raw = None
    except OSError as exc:
        raise ProjectStateReadError("unreadable_project_state", str(exc)) from exc
    if journal.exists() or journal.is_symlink():
        raise ProjectStateReadError("recovery_required", "project transaction started during the state read")
    return raw


@dataclass(frozen=True)
class ProjectStateSnapshot:
    """One immutable byte snapshot; payload() returns a fresh mapping to each caller.

    Boundary rechecks detect observed changes; this is not an atomic snapshot of all
    project artifacts and does not claim to prevent changes after a plan is returned.
    """

    root: Path
    raw: bytes | None

    @classmethod
    def capture(cls, project_root: str | Path) -> "ProjectStateSnapshot":
        root = Path(project_root).expanduser().resolve()
        snapshot = cls(root, _read_state_bytes(root))
        snapshot.payload()  # Reject malformed/undecodable state before any assurance work.
        snapshot.assert_current()
        return snapshot

    def payload(self) -> dict[str, Any]:
        if self.raw is None:
            return {}
        try:
            state = safe_yaml.safe_load(self.raw.decode("utf-8"))
        except (UnicodeError, yaml.YAMLError) as exc:
            raise ProjectStateReadError("invalid_project_state", "state must be valid UTF-8 YAML") from exc
        state = {} if state is None else state
        if not isinstance(state, dict):
            raise ProjectStateReadError("invalid_project_state", "state must be a mapping")
        for key in ("project", "subproblems", "preprocessing"):
            value = state.get(key)
            if value is not None and not isinstance(value, dict):
                raise ProjectStateReadError("invalid_project_state", f"{key} must be a mapping")
        for question, entry in (state.get("subproblems") or {}).items():
            scope = f"subproblems.{question}"
            if not isinstance(entry, dict):
                raise ProjectStateReadError("invalid_project_state", f"{scope} must be a mapping")
            if entry.get("stale_layers") is not None and not isinstance(entry["stale_layers"], list):
                raise ProjectStateReadError("invalid_project_state", f"{scope}.stale_layers must be a list")
            try:
                ARTIFACT_IDENTITY.validate_identity_container_shapes(entry, scope=scope)
            except ARTIFACT_IDENTITY.ArtifactIdentityError as exc:
                raise ProjectStateReadError("invalid_project_state", str(exc)) from exc
        try:
            state_generation(state)
        except ProjectTransactionError as exc:
            raise ProjectStateReadError("invalid_project_state", str(exc)) from exc
        return state

    def assert_current(self, project_root: str | Path | None = None) -> None:
        if project_root is not None and Path(project_root).expanduser().resolve() != self.root:
            raise ProjectStateReadError("snapshot_project_mismatch", "snapshot belongs to another project")
        if _read_state_bytes(self.root) != self.raw:
            raise ProjectStateReadError(
                "project_state_changed", "state bytes changed during planning; rerun the complete resolver"
            )

    def describe(self) -> dict[str, Any]:
        return {
            "path": STATE_RELATIVE_PATH,
            "sha256": hashlib.sha256(self.raw).hexdigest() if self.raw is not None else None,
            "state_generation": state_generation(self.payload()),
            "present": self.raw is not None,
        }


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_intent_assurance(
    explicit_intents: Iterable[str],
    request: str,
    router: dict[str, Any],
) -> tuple[list[str], dict[str, Any]]:
    explicit = _unique(explicit_intents)
    text = request.strip().lower()
    candidates: list[dict[str, Any]] = []
    if text:
        for name, route in (router.get("routing", {}) or {}).items():
            keywords = route.get("infer_keywords", route.get("triggers", []))
            matched = _unique(
                str(word) for word in keywords if str(word).lower() in text
            )
            if matched:
                candidates.append(
                    {
                        "intent": str(name),
                        "score": sum(max(1, len(word.strip())) for word in matched),
                        "matched_keyword_count": len(matched),
                        "matched_keywords": matched,
                    }
                )
    candidates.sort(key=lambda item: (-int(item["score"]), str(item["intent"])))
    top_score = int(candidates[0]["score"]) if candidates else 0
    top = [item for item in candidates if int(item["score"]) == top_score]
    inferred = [str(item["intent"]) for item in top]
    if "full_workflow" in inferred:
        inferred = ["full_workflow"]

    selected = explicit if explicit else inferred
    ambiguity = bool(not explicit and len(inferred) > 1)

    if explicit:
        confidence_band = "high"
        confidence_score = 1.0
        mode = "mixed" if candidates else "explicit"
        reason = "explicit intent is authoritative; keyword matches are provenance only"
    elif not candidates:
        confidence_band = "low"
        confidence_score = 0.0
        mode = "unresolved"
        reason = "no explicit intent and no configured keyword matched"
    elif ambiguity:
        confidence_band = "low"
        confidence_score = 0.35
        mode = "inferred"
        reason = "multiple inferred intents share the top deterministic specificity score"
    elif int(top[0].get("matched_keyword_count", 0)) >= 2:
        confidence_band = "high"
        confidence_score = 0.8
        mode = "inferred"
        reason = "the selected route has multiple deterministic keyword matches"
    else:
        confidence_band = "medium"
        confidence_score = 0.6
        mode = "inferred"
        reason = "the selected route has the highest deterministic keyword-specificity score"

    return selected, {
        "mode": mode,
        "explicit_intents": explicit,
        "inferred_candidates": candidates,
        "selected_intents": selected,
        "confidence_band": confidence_band,
        "confidence_score": confidence_score,
        "ambiguity": ambiguity,
        "selection_reason": reason,
    }


def _scope_questions(state: dict[str, Any], question: str | None) -> tuple[list[str], list[str]]:
    subproblems = state.get("subproblems", {})
    if not isinstance(subproblems, dict):
        return [], ["project state subproblems must be a mapping"]
    if question:
        if question not in subproblems:
            return [], [f"question {question} is not present in project state"]
        return [question], []
    return sorted(str(name) for name in subproblems), []


def _classification_for_scope(
    state: dict[str, Any], questions: list[str]
) -> tuple[dict[str, Any], list[str]]:
    if not questions:
        return {}, []
    subproblems = state.get("subproblems", {})
    if not isinstance(subproblems, dict):
        return {}, ["project state subproblems must be a mapping"]
    rows: list[tuple[str | None, tuple[str, ...], tuple[str, ...]]] = []
    ambiguities: list[str] = []
    for question in questions:
        item = subproblems.get(question, {})
        if not isinstance(item, dict):
            ambiguities.append(f"subproblem {question} must be a mapping")
            continue
        classification = item.get("classification", {}) or {}
        if not isinstance(classification, dict):
            ambiguities.append(f"subproblem {question} classification must be a mapping")
            continue
        objective = classification.get("objective")
        raw_structures = classification.get("structures", []) or []
        if (not isinstance(raw_structures, list)
                or not all(isinstance(structure, str) for structure in raw_structures)):
            ambiguities.append(
                f"subproblem {question} classification.structures must be a string list"
            )
            continue
        structures = tuple(sorted(set(raw_structures)))
        capabilities = item.get("capabilities", {}) or classification.get("capabilities", {}) or {}
        if not isinstance(capabilities, dict):
            ambiguities.append(f"subproblem {question} capabilities must be a mapping")
            continue
        enabled = tuple(sorted(str(name) for name, value in capabilities.items() if value is True))
        if objective or structures or enabled:
            rows.append((str(objective) if objective else None, structures, enabled))
    if not rows:
        return {}, ambiguities
    if len(set(rows)) != 1:
        ambiguities.append(
            "scoped subproblems do not share one objective/structures/capabilities classification"
        )
        return {}, ambiguities
    objective, structures, capabilities = rows[0]
    return {
        "objective": objective,
        "structures": list(structures),
        "capabilities": list(capabilities),
    }, ambiguities


def _framework_semantic_evidence(
    framework_path: Path,
) -> tuple[dict[str, dict[str, Any]], str | None]:
    """Parse current per-question semantic evidence using the shared canonical implementation."""
    if not framework_path.is_file():
        return {}, "current model framework is missing"
    text = framework_path.read_text(encoding="utf-8")
    rows: dict[str, dict[str, Any]] = {}
    try:
        sections = question_sections(text)
    except SemanticIdentityError as exc:
        return {}, f"current model framework is malformed: {exc}"
    for question, section in sections.items():
        try:
            rows[question] = inspect_question_semantics(section, question)
        except SemanticIdentityError as exc:
            rows[question] = {
                "mode": "malformed",
                "error": str(exc),
                "semantic_text_hash": None,
                "semantic_identity_hash": None,
                "semantic_identity_schema_version": None,
            }
    return rows, None


def _uses_structured_identity(item: dict[str, Any]) -> bool:
    return any(name in item for name in STRUCTURED_IDENTITY_FIELDS)


def _is_sha256(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(character in "0123456789abcdefABCDEF" for character in value)


def _semantic_lock_evidence(
    question: str,
    item: dict[str, Any],
    *,
    current_semantics: dict[str, Any] | None,
    framework_error: str | None,
) -> dict[str, Any]:
    revision = item.get("semantic_revision")
    approved_revision = item.get("approved_semantic_revision")
    approval_current = (
        item.get("model_challenge_status") == "passed"
        and item.get("human_model_approval_status") == "approved"
        and not semantic_revision_issues(
            item, required=("semantic_revision", "approved_semantic_revision"))
        and approved_revision == revision
    )
    structured_state = _uses_structured_identity(item)

    if structured_state:
        identity_mode = "semantic_identity_v1"
        schema_version = item.get("semantic_identity_schema_version")
        current_hash = item.get("semantic_identity_hash")
        validated_hash = item.get("validated_semantic_identity_hash")
        approved_hash = item.get("approved_semantic_identity_hash")
        structured_state_complete = (
            schema_version == SEMANTIC_IDENTITY_SCHEMA_VERSION
            and _is_sha256(current_hash)
            and _is_sha256(validated_hash)
            and _is_sha256(approved_hash)
        )
        state_identity_current = (
            structured_state_complete
            and validated_hash == current_hash
            and approved_hash == current_hash
        )
        expected_hash = approved_hash if _is_sha256(approved_hash) else None
    else:
        identity_mode = "legacy_text_hash"
        schema_version = None
        current_hash = item.get("semantic_hash")
        approved_hash = item.get("approved_semantic_hash")
        structured_state_complete = False
        state_identity_current = _is_sha256(current_hash) and _is_sha256(approved_hash) and approved_hash == current_hash
        expected_hash = approved_hash if _is_sha256(approved_hash) else None

    actual_hash: str | None = None
    framework_mode: str | None = None
    framework_schema_version: str | None = None
    if current_semantics:
        framework_mode = str(current_semantics.get("mode") or "")
        if framework_mode == "semantic_identity_v1":
            value = current_semantics.get("semantic_identity_hash")
            framework_schema_version = current_semantics.get("semantic_identity_schema_version")
        elif framework_mode == "legacy_text_hash":
            value = current_semantics.get("semantic_text_hash")
        else:
            value = None
        actual_hash = value if isinstance(value, str) else None

    if framework_error:
        status = "missing" if framework_error == "current model framework is missing" else "malformed"
        reason = framework_error
    elif current_semantics is None:
        status = "malformed"
        reason = f"current framework has no semantic scope for {question}"
    elif framework_mode == "malformed":
        status = "malformed"
        reason = str(current_semantics.get("error") or "current semantic evidence is malformed")
    elif structured_state:
        if not approval_current:
            status = "unapproved"
            reason = "Model Challenge/Human Approval or semantic revision binding is not current"
        elif not structured_state_complete:
            status = "malformed"
            reason = "structured semantic identity state is partial, invalid, or uses an unsupported schema version"
        elif not state_identity_current:
            status = "stale"
            reason = "current, validated and approved semantic identity hashes are not identical"
        elif framework_mode != "semantic_identity_v1":
            status = "malformed"
            reason = "project state uses structured semantic identity but current framework has no valid SIB"
        elif framework_schema_version != schema_version:
            status = "malformed"
            reason = "current framework SIB schema version does not match project-state identity schema version"
        elif actual_hash != current_hash:
            status = "stale"
            reason = "current framework semantic identity does not match project-state semantic identity"
        else:
            status = "verified"
            reason = "current framework SIB, current state, validated state and explicit approval share one semantic identity"
    else:
        if framework_mode == "semantic_identity_v1":
            status = "legacy_review_required"
            reason = "current framework has a SIB but project state has not established structured validation and approval binding"
            schema_version = framework_schema_version
        elif not approval_current:
            status = "unapproved"
            reason = "legacy approval provenance is missing or not current; a current SIB must be established before new task-code delivery"
        elif not state_identity_current:
            status = "stale"
            reason = "legacy semantic_hash approval provenance is internally stale or malformed"
        elif actual_hash != current_hash:
            status = "stale"
            reason = "current framework legacy semantic hash does not match project-state provenance"
        else:
            status = "legacy_review_required"
            reason = "legacy semantic_hash provenance matches the current framework but is read-only compatibility; migrate to a validated and explicitly approved SIB before new task-code delivery"

    return {
        "artifact": "locked_model_spec",
        "source": "framework+project_state",
        "scope": question,
        "status": status,
        "reason": reason,
        "path": FRAMEWORK_RELATIVE_PATH,
        "expected_sha256": expected_hash,
        "actual_sha256": actual_hash,
        "identity_mode": identity_mode,
        "identity_schema_version": schema_version,
    }


def _project_artifact_path(
    project_root: Path, relative_path: str | None
) -> tuple[Path | None, str | None]:
    if not relative_path:
        return None, None
    root = project_root.resolve()
    raw = Path(relative_path).expanduser()
    candidate = raw.resolve() if raw.is_absolute() else (root / raw).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None, "artifact path resolves outside project root"
    return candidate, None


def _file_evidence(
    project_root: Path,
    *,
    artifact: str,
    scope: str,
    relative_path: str | None,
    expected_sha256: str | None,
    accepted: bool,
    accepted_reason: str,
) -> dict[str, Any]:
    path, path_error = _project_artifact_path(project_root, relative_path)
    actual = sha256_file(path) if path else None
    if not accepted:
        status = "not_accepted"
        reason = accepted_reason
    elif not relative_path:
        status = "missing"
        reason = "accepted state has no artifact path"
    elif path_error:
        status = "outside_project_root"
        reason = path_error
    elif not path or not path.is_file():
        status = "missing"
        reason = "artifact path does not exist"
    elif not expected_sha256:
        status = "unverified"
        reason = "accepted state has no expected sha256"
    elif actual != expected_sha256:
        status = "hash_mismatch"
        reason = "actual sha256 does not match current project-state evidence"
    else:
        status = "verified"
        reason = accepted_reason
    return {
        "artifact": artifact,
        "source": "project_state",
        "scope": scope,
        "status": status,
        "reason": reason,
        "path": relative_path,
        "expected_sha256": expected_sha256,
        "actual_sha256": actual,
    }


def _expected_hash(item: dict[str, Any], layer: str) -> str | None:
    try:
        validated = ARTIFACT_IDENTITY.normalize_artifact_hashes(
            item.get("validated_artifact_hashes"),
            legacy_primary_fallback=item.get("validated_model_hash"),
        )
        current = ARTIFACT_IDENTITY.normalize_artifact_hashes(
            item.get("artifact_hashes"), legacy_primary_fallback=item.get("model_hash")
        )
    except ARTIFACT_IDENTITY.ArtifactIdentityError:
        return None
    return validated.get(layer) or current.get(layer)


def hydrate_project_context(
    project_root: str | Path, question: str | None = None, *,
    state_snapshot: ProjectStateSnapshot | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    state_path = root / STATE_RELATIVE_PATH
    snapshot = state_snapshot if state_snapshot is not None else ProjectStateSnapshot.capture(root)
    snapshot.assert_current(root)
    state = snapshot.payload()
    if not state:
        snapshot.assert_current()
        return {
            "loaded": False,
            "project_root": str(root),
            "state_path": str(state_path),
            "question": question,
            "competition": None,
            "preprocessing_decision": None,
            "classification": {},
            "backend_policy": None,
            "verified_artifacts": [],
            "artifact_evidence": [],
            "conflicts": [],
            "ambiguities": ["project state is unavailable"],
        }

    # The backend is a project declaration: inspect every registered question
    # before narrowing numerical and semantic evidence to this request's scope.
    backend_policy = STAGE_CODE.inspect_project_backend_declarations(state)
    try:
        project_backend = STAGE_CODE.current_project_backend(state)
    except STAGE_CODE.StageCodeError:
        project_backend = None  # The diagnostic report below retains the conflict.
    questions, ambiguities = _scope_questions(state, question)
    classification, classification_ambiguities = _classification_for_scope(state, questions)
    ambiguities.extend(classification_ambiguities)
    structured_rejections = _current_structured_rejections(state, questions)
    project = state.get("project", {}) or {}
    preprocessing = state.get("preprocessing", {}) or {}
    evidence: list[dict[str, Any]] = []
    verified: set[str] = set()
    conflicts: list[str] = list(backend_policy["issues"])
    comparison_read_set = {"project": {}, "skill": {}}
    conflicts.extend(
        issue
        for scoped in structured_rejections.values()
        for issue in scoped.get("conflicts", [])
    )

    framework_path = root / FRAMEWORK_RELATIVE_PATH
    semantic_evidence, framework_error = _framework_semantic_evidence(framework_path)
    subproblems = state.get("subproblems", {})
    scoped_items = {
        q: (
            subproblems.get(q, {})
            if isinstance(subproblems, dict) and isinstance(subproblems.get(q, {}), dict)
            else {}
        )
        for q in questions
    }
    semantic_rows = [
        _semantic_lock_evidence(
            q,
            scoped_items[q],
            current_semantics=semantic_evidence.get(q),
            framework_error=framework_error,
        )
        for q in questions
    ]
    for question, row in zip(questions, semantic_rows):
        rejection = structured_rejections.get(str(question), {})
        if rejection.get("blocks_model"):
            prior_reason = str(row.get("reason") or "").strip()
            rejection_reason = "; ".join(rejection.get("model_reasons", []) or [])
            row["status"] = "not_accepted"
            row["reason"] = "; ".join(item for item in (prior_reason, rejection_reason) if item)
    evidence.extend(semantic_rows)
    if semantic_rows and all(item["status"] == "verified" for item in semantic_rows):
        verified.add("locked_model_spec")

    preprocessing_status = preprocessing.get("status") == "accepted"
    pre = _file_evidence(
        root,
        artifact="preprocessing_workbook",
        scope="project",
        relative_path=preprocessing.get("workbook"),
        expected_sha256=preprocessing.get("workbook_sha256"),
        accepted=preprocessing_status,
        accepted_reason=(
            "project-level preprocessing workbook is accepted"
            if preprocessing_status
            else "project-level preprocessing workbook is not accepted"
        ),
    )
    if preprocessing.get("decision") == "project_level" or preprocessing.get("workbook"):
        evidence.append(pre)
        if pre["status"] == "verified":
            verified.update({"preprocessing_workbook", "accepted_preprocessing_workbook"})

    primary_rows: list[dict[str, Any]] = []
    analysis_rows: list[dict[str, Any]] = []
    analysis_skip_rows: list[dict[str, Any]] = []
    analysis_complete: list[bool] = []
    for q in questions:
        item = scoped_items[q]
        selections = item.get("solver_execution", {})
        if not isinstance(selections, dict):
            selections = {}
        conflicts.extend(ARTIFACT_IDENTITY.entry_alias_issues(item, scope=q))
        stale = set(ARTIFACT_IDENTITY.normalize_stale_layers(item.get("stale_layers")))
        primary_issues = ANALYSIS_PREREQUISITES.primary_issues(
            root, state, item, require_project_policy=True,
        )
        rejection = structured_rejections.get(str(q), {})
        primary_issues.extend(rejection.get("primary_reasons", []) or [])
        primary_ok = (
            item.get("primary_execution_status") == "accepted"
            and item.get("result_quality_status") == "passed"
            and not rejection.get("blocks_primary")
        )
        primary_row = _file_evidence(
            root,
            artifact="accepted_solution_workbook",
            scope=q,
            relative_path=item.get("solution_workbook"),
            expected_sha256=_expected_hash(item, "solution_workbook"),
            accepted=primary_ok,
            accepted_reason=(
                "primary execution and result quality are accepted"
                if primary_ok
                else "; ".join(primary_issues)
            ),
        )
        if primary_row["status"] == "verified" and primary_issues:
            primary_row.update(status="not_accepted", reason="; ".join(primary_issues))
        primary_rows.append(primary_row)

        analysis_ok = (
            primary_row["status"] == "verified"
            and item.get("analysis_execution_status") == "accepted"
            and item.get("result_analysis_status") == "passed"
            and not stale.intersection({"analysis_code", "result_analysis_workbook"})
        )
        analysis_row = _file_evidence(
            root,
            artifact="accepted_result_analysis_workbook",
            scope=q,
            relative_path=item.get("result_analysis_workbook"),
            expected_sha256=_expected_hash(item, "result_analysis_workbook"),
            accepted=analysis_ok,
            accepted_reason=(
                "result-analysis execution and stability status are accepted"
                if analysis_ok
                else "result-analysis execution or stability status is not accepted"
            ),
        )
        if analysis_row["status"] == "verified" and (
            project_backend is not None or item.get("result_analysis_code") or selections.get("analysis")
        ):
            binding_issues = STAGE_CODE.validate_stage_binding(
                root, item, "analysis", require_validated=True, project_backend=project_backend,
            )
            binding_issues.extend(ANALYSIS_PREREQUISITES.stage_input_issues(root, state, item, "analysis"))
            from conformance_gate import read_issues
            binding_issues.extend(read_issues(root, state, item, "analysis"))
            if binding_issues:
                analysis_row.update(status="not_accepted", reason="; ".join(binding_issues))
        if analysis_row["status"] == "verified":
            comparison = COMPARISON.inspect_gate(root, state, q, boundary="current")
            CONFORMANCE.merge_read_sets(comparison_read_set, comparison["observed_sources"])
            if comparison["issues"]:
                analysis_row.update(status="not_accepted", reason="; ".join(comparison["issues"]))
        analysis_rows.append(analysis_row)

        requirement_reason = str(item.get("result_analysis_requirement_reason") or "").strip()
        not_required = item.get("result_analysis_status") == "not_required"
        analysis_hash_layers = ("analysis_code", "result_analysis_workbook", "robustness_workbook")
        analysis_identity = (
            any(item.get(field) for field in (
                "result_analysis_code", "analysis_code_sha256", "result_analysis_workbook", "robustness_workbook",
            ))
            or bool(selections.get("analysis"))
            or item.get("analysis_execution_status") not in (None, "pending")
            or any(hashes.get(layer)
                   for hashes in (item.get("artifact_hashes"), item.get("validated_artifact_hashes"))
                   if isinstance(hashes, dict)
                   for layer in analysis_hash_layers)
        )
        skip_issues = []
        if not_required:
            comparison = COMPARISON.inspect_gate(root, state, q, boundary="plan")
            CONFORMANCE.merge_read_sets(comparison_read_set, comparison["observed_sources"])
            skip_issues = comparison["issues"]
        skip_verified = (not_required and bool(requirement_reason) and not COMPARISON.required_ids(item) and not skip_issues
                         and primary_row["status"] == "verified" and not analysis_identity)
        if not_required:
            analysis_skip_rows.append(
                {
                    "artifact": "result_analysis_not_required",
                    "source": "project_state",
                    "scope": q,
                    "status": "verified" if skip_verified else "not_accepted",
                    "reason": (
                        requirement_reason
                        if skip_verified
                        else ("; ".join(skip_issues) if skip_issues else
                              "not_required cannot retire a current required comparison"
                              if COMPARISON.required_ids(item) else
                              "not_required still records current analysis numerical identity"
                              if analysis_identity else
                              "result_analysis_status=not_required requires a non-empty reason and a verified accepted primary result")
                    ),
                    "path": None,
                    "expected_sha256": None,
                    "actual_sha256": None,
                }
            )
        analysis_complete.append(
            primary_row["status"] == "verified"
            and (analysis_row["status"] == "verified" or skip_verified)
        )

    evidence.extend(primary_rows)
    evidence.extend(analysis_rows)
    evidence.extend(analysis_skip_rows)
    if primary_rows and all(item["status"] == "verified" for item in primary_rows):
        verified.update({"accepted_solution_workbook", "solution_workbook", "result_quality_report"})
    if analysis_rows and all(item["status"] == "verified" for item in analysis_rows):
        verified.update({"accepted_result_analysis_workbook", "result_analysis_workbook"})
    if analysis_complete and all(analysis_complete):
        verified.add("validated_results")

    CONFORMANCE.assert_observed(root, comparison_read_set)
    snapshot.assert_current()
    return {
        "loaded": True,
        "project_root": str(root),
        "state_path": str(state_path),
        "question": question,
        "project": {
            "competition": project.get("competition"),
            "problem": project.get("problem"),
            "version": project.get("version"),
            "current_phase": project.get("current_phase"),
        },
        "competition": project.get("competition"),
        "preprocessing_decision": preprocessing.get("decision"),
        "classification": classification,
        "backend_policy": backend_policy,
        "verified_artifacts": sorted(verified),
        "artifact_evidence": evidence,
        "conflicts": conflicts,
        "ambiguities": ambiguities,
    }


def reconcile_legacy_artifacts(
    declared: Iterable[str], hydration: dict[str, Any]
) -> tuple[list[str], list[dict[str, Any]], list[str]]:
    declared_set = set(_unique(declared))
    verified = set(hydration.get("verified_artifacts", []) or [])
    evidence = list(hydration.get("artifact_evidence", []) or [])
    conflicts: list[str] = []
    known_invalid = {
        str(item.get("artifact"))
        for item in evidence
        if item.get("status") not in {"verified"}
    }
    effective = set(verified)
    for artifact in sorted(declared_set):
        canonical = QUALIFIED_ARTIFACT_ALIASES.get(artifact)
        if hydration.get("loaded") and (
            (canonical is not None and canonical not in verified)
            or artifact in known_invalid
        ):
            conflicts.append(
                f"legacy artifact declaration {artifact} conflicts with current project-state assurance"
            )
            continue
        effective.add(artifact)
        evidence.append(
            {
                "artifact": artifact,
                "source": "legacy_available_artifacts",
                "scope": hydration.get("question") or "unspecified",
                "status": "declared_unverified",
                "reason": "legacy name-only compatibility input",
                "path": None,
                "expected_sha256": None,
                "actual_sha256": None,
            }
        )
    return sorted(effective), evidence, conflicts


def apply_contract_dependency_closure(
    plan: dict[str, Any],
    manifest: dict[str, Any],
    assurance_contract: dict[str, Any],
) -> dict[str, Any]:
    dependency_spec = (
        assurance_contract.get("contract_dependency_closure", {}) or {}
    ).get("contract_dependencies", {}) or {}
    aliases = manifest.get("contracts", {}) or {}
    required_aliases: list[str] = []
    for module in plan.get("modules", []) or []:
        required_aliases.extend(dependency_spec.get(str(module), []) or [])
    for gate in plan.get("pre_delivery_gates", []) or []:
        required_aliases.extend(
            dependency_spec.get(f"gate:{gate.get('name')}", []) or []
        )
    required_aliases = _unique(required_aliases)
    missing_aliases = [alias for alias in required_aliases if alias not in aliases]
    if missing_aliases:
        raise ValueError(f"runtime contract dependency aliases are undefined: {missing_aliases}")
    required_paths = _unique(aliases.get(alias) for alias in required_aliases)
    load_order = list(plan.get("load_order", []) or [])
    additions = [path for path in required_paths if path not in load_order]
    if additions:
        first_module = next(
            (index for index, item in enumerate(load_order) if str(item).startswith("modules/")),
            len(load_order),
        )
        load_order[first_module:first_module] = additions
    plan["load_order"] = load_order
    plan["contracts"] = _unique(
        [*(plan.get("contracts", []) or []), *required_paths]
    )
    return {
        "required_aliases": required_aliases,
        "required_paths": required_paths,
        "added_paths": additions,
        "missing_aliases": [],
    }


def authority_fingerprint(root: Path, sources: Iterable[str]) -> dict[str, Any]:
    rows: list[dict[str, str | None]] = []
    aggregate = hashlib.sha256()
    for relative in sources:
        path = root / relative
        digest = sha256_file(path)
        rows.append({"path": relative, "sha256": digest})
        aggregate.update(relative.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update((digest or "missing").encode("ascii"))
        aggregate.update(b"\n")
    return {"algorithm": "sha256", "sources": rows, "sha256": aggregate.hexdigest()}
