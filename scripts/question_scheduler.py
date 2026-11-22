#!/usr/bin/env python3
"""Read-only target-question selection for an existing project runtime plan.

This module selects *where to continue*, not whether code or numerical evidence
is authorized. Qualification facts are supplied by the existing file-backed
Runtime Assurance reader; no State field, local-machine check, gate or write
is introduced here.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
import re
from typing import Any

from state_transitions import dependency_cycles, dependency_edges

QUESTION = re.compile(r"Q[1-9][0-9]*\Z")
QUESTION_ROUTES = frozenset({
    "full_solution", "full_workflow", "code_and_solution", "model_selection",
    "new_problem_design", "advanced_method", "result_analysis", "validation",
})
FINAL_ROUTES = frozenset({
    "review", "full_submission", "latex", "docx", "project_sync",
    "problem_analysis", "data_preprocessing",
})


def _ordered(subproblems: Mapping[str, Any]) -> list[str]:
    names = list(subproblems)
    if any(not isinstance(q, str) or not QUESTION.fullmatch(q) for q in names):
        raise ValueError("registered question IDs must be Q1, Q2, ...")
    return sorted(names, key=lambda q: int(q[1:]))


def _next_action(entry: Mapping[str, Any], verified: set[str]) -> str:
    if "validated_results" in verified:
        return "validated_results"
    if entry.get("problem_contract_status") not in (None, "frozen"):
        return "problem_audit"
    if entry.get("status") in {"pending", "audited"}:
        return "model_design"
    if entry.get("model_challenge_status") != "passed":
        return "model_challenge"
    if entry.get("human_model_approval_status") != "approved":
        return "human_model_approval"
    primary = entry.get("primary_execution_status")
    if primary == "workbook_received":
        return "primary_workbook_acceptance"
    if primary in {"code_delivered", "awaiting_user_execution"}:
        return "user_execution"
    if primary != "accepted":
        return "primary_code_delivery"
    if entry.get("result_analysis_status") == "not_required":
        return "primary_result_requalification"
    if entry.get("result_analysis_status") == "pending":
        return "analysis_necessity"
    if entry.get("analysis_execution_status") in {"code_delivered", "awaiting_user_execution"}:
        return "user_execution"
    if entry.get("analysis_execution_status") == "workbook_received":
        return "analysis_workbook_acceptance"
    return "result_requalification"


def select_question(
    state: Mapping[str, Any],
    *,
    explicit_question: str | None = None,
    selected_intents: Iterable[str] = (),
    request: str = "",
    verified_artifacts: Mapping[str, Iterable[str]] | None = None,
) -> dict[str, Any]:
    """Select a single Qn or report why none is eligible, without authorizing work.

    verified_artifacts MUST be produced by current Runtime Assurance for a
    project-backed resolver. Without it, completed/approved results are treated
    as unverified, not inferred from filenames or State's self-report.
    """
    subproblems = state.get("subproblems", {}) or {}
    if not isinstance(subproblems, Mapping):
        raise ValueError("project subproblems must be a mapping")
    order = _ordered(subproblems)
    for name, entry in subproblems.items():
        if not isinstance(entry, Mapping):
            raise ValueError(f"{name}: subproblem state must be a mapping")
        if "depends_on" in entry and not isinstance(entry["depends_on"], list):
            raise ValueError(f"{name}: depends_on must be a list")
    intents = set(selected_intents)
    qualifications = {
        question: set(verified_artifacts.get(question, ()) or ())
        if verified_artifacts is not None else set()
        for question in order
    }

    if not order:
        return {
            "scope_kind": "project", "selected_question": None,
            "selection_reason": "no_registered_questions", "candidate_questions": [],
            "blocked_questions": {}, "prerequisite_closure": [],
            "waiting_action": None, "diagnostic_only": True,
        }

    edges = dependency_edges(subproblems)
    incoming: dict[str, list[dict[str, Any]]] = {name: [] for name in order}
    for edge in edges:
        incoming[edge["target"]].append(edge)
    cycles = dependency_cycles(subproblems)
    preprocessing = state.get("preprocessing") or {}
    required_preprocessing = (
        isinstance(preprocessing, Mapping)
        and preprocessing.get("decision") == "project_level"
    )
    project_preprocessed = any(
        "accepted_preprocessing_workbook" in qualifications[name]
        or "preprocessing_workbook" in qualifications[name]
        for name in order
    )

    def closure_for(question: str) -> list[dict[str, Any]]:
        seen: set[str] = set()
        rows: dict[tuple[str, str, str], dict[str, Any]] = {}
        def visit(target: str) -> None:
            if target in seen:
                return
            seen.add(target)
            for edge in incoming.get(target, ()):
                source = str(edge["source"])
                key = (target, source, str(edge["kind"]))
                rows[key] = {
                    "question": target, "upstream": source, "kind": edge["kind"],
                }
                if source in subproblems:
                    visit(source)
        visit(question)
        return [rows[key] for key in sorted(rows)]

    def blockers_for(question: str) -> list[dict[str, str]]:
        issues: list[dict[str, str]] = []
        closure = closure_for(question)
        involved = {question, *(item["upstream"] for item in closure)}
        for cycle in cycles:
            if any(node in involved for node in cycle.split(" -> ")):
                issues.append({"question": question, "upstream": question,
                               "kind": "cycle", "reason": cycle})
        for edge in closure:
            source, kind = edge["upstream"], edge["kind"]
            label = {"question": question, "upstream": source, "kind": kind}
            if source not in subproblems:
                issues.append({**label, "reason": "unregistered_upstream"})
            elif kind == "model" and "locked_model_spec" not in qualifications[source]:
                issues.append({**label, "reason": "current_approved_model_unverified"})
            elif kind == "result" and "validated_results" not in qualifications[source]:
                issues.append({**label, "reason": "upstream_validated_results_unverified"})
            elif kind == "parameter":
                issues.append({**label, "reason": "parameter_source_requires_review"})
            elif kind == "data":
                if required_preprocessing and not project_preprocessed:
                    issues.append({**label, "reason": "project_preprocessing_unverified"})
                else:
                    issues.append({**label, "reason": "data_source_requires_review"})
            elif kind == "legacy_untyped":
                issues.append({**label, "reason": "legacy_dependency_kind_unresolved"})
        return issues

    blocked = {name: issues for name in order if (issues := blockers_for(name))}
    actions = {name: _next_action(subproblems[name], qualifications[name]) for name in order}
    candidates = [
        {"question": name, "next_action": actions[name],
         "blocked": name in blocked}
        for name in order
    ]

    if explicit_question is not None:
        if explicit_question not in subproblems:
            return {
                "scope_kind": "question", "selected_question": explicit_question,
                "selection_reason": "explicit_unregistered_question",
                "candidate_questions": candidates,
                "blocked_questions": {**blocked, explicit_question: [
                    {"question": explicit_question, "upstream": explicit_question,
                     "kind": "registration", "reason": "question_not_registered"}]},
                "prerequisite_closure": [], "waiting_action": None,
                "diagnostic_only": True,
            }
        selected = explicit_question
        reason = "explicit_question"
    elif not intents.intersection(QUESTION_ROUTES) or intents.intersection(FINAL_ROUTES):
        return {
            "scope_kind": "project", "selected_question": None,
            "selection_reason": "project_level_route",
            "candidate_questions": candidates, "blocked_questions": blocked,
            "prerequisite_closure": [], "waiting_action": None,
            "diagnostic_only": True,
        }
    elif all(actions[name] == "validated_results" for name in order):
        return {
            "scope_kind": "finalization", "selected_question": None,
            "selection_reason": "all_required_results_verified",
            "candidate_questions": candidates, "blocked_questions": blocked,
            "prerequisite_closure": [], "waiting_action": None,
            "diagnostic_only": True,
        }
    else:
        unfinished = [
            name for name in order
            if actions[name] != "validated_results" and name not in blocked
        ]
        waits = [
            name for name in unfinished
            if actions[name] in {"human_model_approval", "user_execution",
                                 "primary_workbook_acceptance", "analysis_workbook_acceptance"}
        ]
        is_resume = bool(re.search(r"继续|恢复|接着|resume|continue", request, flags=re.I))
        if is_resume and len(waits) == 1:
            selected, reason = waits[0], "resume_unique_wait"
        else:
            actionable = [name for name in unfinished if name not in waits]
            if actionable:
                selected, reason = actionable[0], "first_unblocked_actionable"
            elif waits:
                selected, reason = waits[0], "waiting_for_user_action"
            else:
                return {
                    "scope_kind": "project", "selected_question": None,
                    "selection_reason": "all_unfinished_questions_blocked",
                    "candidate_questions": candidates,
                    "blocked_questions": blocked,
                    "prerequisite_closure": [], "waiting_action": None,
                    "diagnostic_only": True,
                }
    return {
        "scope_kind": "question", "selected_question": selected,
        "selection_reason": reason, "candidate_questions": candidates,
        "blocked_questions": blocked,
        "prerequisite_closure": closure_for(selected),
        "waiting_action": (
            actions[selected] if actions[selected] in {
                "human_model_approval", "user_execution",
                "primary_workbook_acceptance", "analysis_workbook_acceptance",
            } else None
        ),
        "diagnostic_only": True,
    }
