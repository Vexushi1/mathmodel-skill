#!/usr/bin/env python3
"""Explicit-question scope only; implicit next-question selection is disabled.

Code Delivery and Model Approval own execution eligibility. This helper is
read-only and intentionally does not traverse or classify upstream blockers,
rank unfinished questions, or choose a wait/resume point.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
import re
from typing import Any

QUESTION = re.compile(r"Q[1-9][0-9]*\Z")
QUESTION_ROUTES = frozenset({
    "full_solution", "full_workflow", "code_and_solution", "model_selection",
    "new_problem_design", "advanced_method", "result_analysis", "validation",
})
FINAL_ROUTES = frozenset({
    "review", "full_submission", "latex", "docx", "project_sync",
    "problem_analysis", "data_preprocessing",
})


def select_question(
    state: Mapping[str, Any],
    *,
    explicit_question: str | None = None,
    selected_intents: Iterable[str] = (),
    request: str = "",
    verified_artifacts: Mapping[str, Iterable[str]] | None = None,
) -> dict[str, Any]:
    """Report an explicitly supplied target, never derive Qn from project state."""
    subproblems = state.get("subproblems", {}) or {}
    if not isinstance(subproblems, Mapping):
        raise ValueError("project subproblems must be a mapping")
    for name, entry in subproblems.items():
        if not isinstance(name, str) or QUESTION.fullmatch(name) is None:
            raise ValueError("registered question IDs must be Q1, Q2, ...")
        if not isinstance(entry, Mapping):
            raise ValueError(f"{name}: subproblem state must be a mapping")
        if "depends_on" in entry and not isinstance(entry["depends_on"], list):
            raise ValueError(f"{name}: depends_on must be a list")

    names = sorted(subproblems, key=lambda q: int(q[1:]))
    candidates = [{"question": name, "next_action": None, "blocked": None}
                  for name in names]
    intents = set(selected_intents)
    if explicit_question is None:
        reason = ("explicit_question_required"
                  if intents.intersection(QUESTION_ROUTES)
                  and not intents.intersection(FINAL_ROUTES)
                  else "project_level_route")
        return {
            "scope_kind": "project", "selected_question": None,
            "selection_reason": reason, "candidate_questions": candidates,
            "blocked_questions": {}, "prerequisite_closure": [],
            "waiting_action": None, "diagnostic_only": True,
        }
    if explicit_question not in subproblems:
        return {
            "scope_kind": "question", "selected_question": explicit_question,
            "selection_reason": "explicit_unregistered_question",
            "candidate_questions": candidates,
            "blocked_questions": {explicit_question: [{
                "question": explicit_question, "upstream": explicit_question,
                "kind": "registration", "reason": "question_not_registered",
            }]},
            "prerequisite_closure": [], "waiting_action": None,
            "diagnostic_only": True,
        }
    return {
        "scope_kind": "question", "selected_question": explicit_question,
        "selection_reason": "explicit_question",
        "candidate_questions": candidates, "blocked_questions": {},
        "prerequisite_closure": [], "waiting_action": None,
        "diagnostic_only": True,
    }
