#!/usr/bin/env python3
"""Pure deterministic project-state transition engine.

The engine deliberately performs no project-file I/O. Callers load the authoritative
`core/state_transition_contract.yaml`, pass the parsed mapping here, and persist the
returned/mutated project state themselves.
"""
from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Mapping, MutableMapping
from typing import Any

VALID_DEPENDENCY_KINDS = {"data", "parameter", "model", "result"}
LEGACY_DEPENDENCY_KIND = "legacy_untyped"
_EVENT_SIGNAL = "*"


def _subproblems(state: Mapping[str, Any]) -> Mapping[str, Any]:
    value = state.get("subproblems", {}) or {}
    return value if isinstance(value, Mapping) else {}


def dependency_edges(subproblems: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return deterministic source->target dependency edges, preserving legacy evidence."""
    rows: list[dict[str, Any]] = []
    for target in sorted(str(key) for key in subproblems):
        entry = subproblems.get(target, {})
        if not isinstance(entry, Mapping):
            continue
        for raw in entry.get("depends_on", []) or []:
            if isinstance(raw, str):
                source = raw.strip()
                if source:
                    rows.append(
                        {
                            "source": source,
                            "target": target,
                            "kind": LEGACY_DEPENDENCY_KIND,
                            "declared_kind": None,
                            "legacy": True,
                        }
                    )
                continue
            if not isinstance(raw, Mapping):
                continue
            source = str(raw.get("question", "")).strip()
            if not source:
                continue
            declared = str(raw.get("kind", "")).strip()
            kind = declared if declared in VALID_DEPENDENCY_KINDS else LEGACY_DEPENDENCY_KIND
            rows.append(
                {
                    "source": source,
                    "target": target,
                    "kind": kind,
                    "declared_kind": declared or None,
                    "legacy": kind == LEGACY_DEPENDENCY_KIND,
                }
            )
    return sorted(
        rows,
        key=lambda row: (
            str(row["source"]),
            str(row["target"]),
            str(row["kind"]),
            str(row.get("declared_kind") or ""),
        ),
    )


def _canonical_cycle(nodes: list[str]) -> tuple[str, ...]:
    """Canonicalize a directed closed cycle by rotation only."""
    body = nodes[:-1]
    if not body:
        return tuple(nodes)
    rotations = [tuple(body[index:] + body[:index]) for index in range(len(body))]
    best = min(rotations)
    return (*best, best[0])


def dependency_cycles(subproblems: Mapping[str, Any]) -> list[str]:
    """Report dependency cycles deterministically without rejecting or looping."""
    adjacency: dict[str, list[str]] = defaultdict(list)
    known = {str(key) for key in subproblems}
    for edge in dependency_edges(subproblems):
        source = str(edge["source"])
        target = str(edge["target"])
        if source in known and target in known and target not in adjacency[source]:
            adjacency[source].append(target)
    for source in adjacency:
        adjacency[source].sort()

    visited: set[str] = set()
    active: list[str] = []
    active_set: set[str] = set()
    found: set[tuple[str, ...]] = set()

    def visit(node: str) -> None:
        visited.add(node)
        active.append(node)
        active_set.add(node)
        for target in adjacency.get(node, []):
            if target not in visited:
                visit(target)
            elif target in active_set:
                start = active.index(target)
                found.add(_canonical_cycle([*active[start:], target]))
        active.pop()
        active_set.remove(node)

    for node in sorted(known):
        if node not in visited:
            visit(node)
    return [" -> ".join(cycle) for cycle in sorted(found)]


def _profile(contract: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    profiles = contract.get("profiles", {}) or {}
    value = profiles.get(name, {}) if isinstance(profiles, Mapping) else {}
    if not isinstance(value, Mapping):
        raise ValueError(f"state transition profile {name!r} is not a mapping")
    return value


def _event_spec(contract: Mapping[str, Any], event: str) -> Mapping[str, Any]:
    events = contract.get("transition_events", {}) or {}
    value = events.get(event) if isinstance(events, Mapping) else None
    if not isinstance(value, Mapping):
        raise ValueError(f"unknown state transition event: {event}")
    return value


def _dependency_rule(contract: Mapping[str, Any], kind: str) -> Mapping[str, Any]:
    rules = contract.get("dependency_rules", {}) or {}
    value = rules.get(kind) if isinstance(rules, Mapping) else None
    if not isinstance(value, Mapping):
        raise ValueError(f"missing dependency transition rule for {kind!r}")
    return value


def _apply_profile(
    entry: MutableMapping[str, Any],
    *,
    profile_name: str,
    contract: Mapping[str, Any],
) -> tuple[list[str], dict[str, Any]]:
    profile = _profile(contract, profile_name)
    stale_layers = sorted({str(item) for item in profile.get("stale_layers", []) or []})
    if stale_layers:
        previous = set(entry.get("stale_layers", []) or [])
        entry["stale_layers"] = sorted(previous | set(stale_layers))
        entry["artifacts_stale"] = True

    updates: dict[str, Any] = {}
    for field, value in (profile.get("set", {}) or {}).items():
        if entry.get(str(field)) != value:
            entry[str(field)] = value
        updates[str(field)] = value
    for field, value in (profile.get("set_if_present", {}) or {}).items():
        field = str(field)
        if field in entry:
            if entry.get(field) != value:
                entry[field] = value
            updates[field] = value
    return stale_layers, updates


def apply_local_event(
    entry: MutableMapping[str, Any],
    event: str,
    contract: Mapping[str, Any],
    *,
    context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply only an event's own-question profile to one subproblem entry."""
    spec = _event_spec(contract, event)
    profile_name = str(spec.get("own_profile", "")).strip()
    if not profile_name:
        raise ValueError(f"event {event!r} has no own_profile")
    stale_layers, updates = _apply_profile(entry, profile_name=profile_name, contract=contract)
    emitted = _event_impacts(spec, context or {})
    return {
        "profile": profile_name,
        "stale_layers": stale_layers,
        "status_updates": updates,
        "emitted_impacts": sorted(emitted),
    }


def _event_impacts(spec: Mapping[str, Any], context: Mapping[str, Any]) -> set[str]:
    impacts = {str(item) for item in spec.get("emitted_impacts", []) or []}
    categories = {str(item) for item in context.get("semantic_change_categories", []) or []}
    category_impacts = spec.get("category_impacts", {}) or {}
    if isinstance(category_impacts, Mapping):
        for category in sorted(categories):
            impacts.update(str(item) for item in category_impacts.get(category, []) or [])
    return impacts


def apply_transition(
    state: MutableMapping[str, Any],
    *,
    event: str,
    source_question: str,
    contract: Mapping[str, Any],
    context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply one event plus typed downstream propagation in place and return evidence."""
    subproblems = state.get("subproblems", {}) or {}
    if not isinstance(subproblems, MutableMapping):
        raise ValueError("project state subproblems must be a mutable mapping")
    source_question = str(source_question)
    source_entry = subproblems.get(source_question)
    if not isinstance(source_entry, MutableMapping):
        raise ValueError(f"source question {source_question!r} is not present as a mutable mapping")

    spec = _event_spec(contract, event)
    local = apply_local_event(source_entry, event, contract, context=context)
    transitions: list[dict[str, Any]] = [
        {
            "question": source_question,
            "scope": "own",
            "source": source_question,
            "dependency_kind": None,
            "profile": local["profile"],
            "stale_layers": local["stale_layers"],
            "status_updates": local["status_updates"],
            "emitted_impacts": local["emitted_impacts"],
            "reason": f"direct event {event}",
        }
    ]
    affected = {source_question}

    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in dependency_edges(subproblems):
        by_source[str(edge["source"])].append(edge)

    queue: deque[tuple[str, str]] = deque()
    initial_impacts = set(local["emitted_impacts"])
    for signal in sorted({*initial_impacts, _EVENT_SIGNAL}):
        queue.append((source_question, signal))
    visited_signals: set[tuple[str, str]] = set()
    applied_edges: set[tuple[str, str, str]] = set()

    while queue:
        current_question, signal = queue.popleft()
        signal_key = (current_question, signal)
        if signal_key in visited_signals:
            continue
        visited_signals.add(signal_key)
        for edge in by_source.get(current_question, []):
            kind = str(edge["kind"])
            rule = _dependency_rule(contract, kind)
            trigger_impacts = {str(item) for item in rule.get("trigger_impacts", []) or []}
            triggers = signal == _EVENT_SIGNAL if _EVENT_SIGNAL in trigger_impacts else signal in trigger_impacts
            if not triggers:
                continue
            edge_key = (str(edge["source"]), str(edge["target"]), kind)
            if edge_key in applied_edges:
                continue
            applied_edges.add(edge_key)
            target = str(edge["target"])
            target_entry = subproblems.get(target)
            if not isinstance(target_entry, MutableMapping):
                continue
            profile_name = str(rule.get("target_profile", "")).strip()
            stale_layers, updates = _apply_profile(
                target_entry, profile_name=profile_name, contract=contract
            )
            emitted = sorted({str(item) for item in rule.get("emitted_impacts", []) or []})
            reason = str(rule.get("reason", "typed dependency invalidation"))
            if edge.get("legacy") and edge.get("declared_kind"):
                reason += f"; unsupported declared kind={edge['declared_kind']!r} treated conservatively"
            transitions.append(
                {
                    "question": target,
                    "scope": "downstream",
                    "source": current_question,
                    "dependency_kind": kind,
                    "profile": profile_name,
                    "stale_layers": stale_layers,
                    "status_updates": updates,
                    "emitted_impacts": emitted,
                    "reason": reason,
                }
            )
            affected.add(target)
            for next_signal in sorted({*emitted, _EVENT_SIGNAL}):
                queue.append((target, next_signal))

    return {
        "event": event,
        "source": source_question,
        "affected_questions": sorted(affected),
        "transitions": transitions,
        "dependency_cycles": dependency_cycles(subproblems),
    }


def merge_transition_reports(reports: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Combine multiple source-event reports without losing per-edge provenance."""
    affected: set[str] = set()
    cycles: set[str] = set()
    transitions: list[dict[str, Any]] = []
    for report in reports:
        affected.update(str(item) for item in report.get("affected_questions", []) or [])
        cycles.update(str(item) for item in report.get("dependency_cycles", []) or [])
        transitions.extend(dict(item) for item in report.get("transitions", []) or [])
    return {
        "affected_questions": sorted(affected),
        "dependency_cycles": sorted(cycles),
        "transitions": transitions,
    }
