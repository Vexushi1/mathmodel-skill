#!/usr/bin/env python3
"""Resolve an HSK workflow with declarative runtime context and assurance."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable

import yaml

from resolve_workflow import resolve_workflow
from runtime_assurance import (
    apply_contract_dependency_closure,
    authority_fingerprint,
    hydrate_project_context,
    reconcile_legacy_artifacts,
    resolve_intent_assurance,
)

ROOT = Path(__file__).resolve().parent.parent
BOOTSTRAP_PATH = ROOT / "core" / "bootstrap.yaml"
ROUTER_PATH = ROOT / "core" / "workflow_router.yaml"
MANIFEST_PATH = ROOT / "core" / "module_manifest.yaml"
ASSURANCE_PATH = ROOT / "core" / "runtime_assurance_contract.yaml"


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _unique(items: Iterable[str | None]) -> list[str]:
    return list(dict.fromkeys(str(item) for item in items if item and str(item).strip()))


def resolve_runtime(
    intents: str | Iterable[str] | None = None,
    *,
    request: str | None = None,
    objective: str | None = None,
    structures: Iterable[str] = (),
    capabilities: Iterable[str] = (),
    primary: str | None = None,
    secondary: Iterable[str] = (),
    competition: str | None = None,
    available_artifacts: Iterable[str] | None = None,
    preprocessing_decision: str | None = None,
    project_root: str | Path | None = None,
    question: str | None = None,
) -> dict[str, Any]:
    bootstrap = load_yaml(BOOTSTRAP_PATH)
    router = load_yaml(ROUTER_PATH)
    manifest = load_yaml(MANIFEST_PATH)
    assurance_contract = load_yaml(ASSURANCE_PATH)

    explicit_intents = [intents] if isinstance(intents, str) else list(intents or [])
    selected_intents, intent_diagnostics = resolve_intent_assurance(
        explicit_intents, request or "", router
    )
    if not selected_intents:
        raise ValueError("no workflow intent resolved; pass an intent or --request")

    hydration = (
        hydrate_project_context(project_root, question)
        if project_root
        else {
            "loaded": False,
            "project_root": None,
            "state_path": None,
            "question": question,
            "competition": None,
            "preprocessing_decision": None,
            "classification": {},
            "verified_artifacts": [],
            "artifact_evidence": [],
            "conflicts": [],
            "ambiguities": [],
        }
    )
    context_conflicts = list(hydration.get("conflicts", []) or [])
    field_provenance: dict[str, str] = {}

    if competition is None and hydration.get("competition"):
        competition = str(hydration["competition"])
        field_provenance["competition"] = "project_state"
    elif competition is not None:
        field_provenance["competition"] = "explicit"
        state_competition = hydration.get("competition")
        if state_competition and str(state_competition).lower() != str(competition).lower():
            context_conflicts.append(
                f"explicit competition {competition} differs from project state {state_competition}"
            )

    if preprocessing_decision is None and hydration.get("preprocessing_decision"):
        preprocessing_decision = str(hydration["preprocessing_decision"])
        field_provenance["preprocessing_decision"] = "project_state"
    elif preprocessing_decision is not None:
        field_provenance["preprocessing_decision"] = "explicit"
        state_decision = hydration.get("preprocessing_decision")
        if state_decision and state_decision != preprocessing_decision:
            context_conflicts.append(
                f"explicit preprocessing_decision {preprocessing_decision} differs from project state {state_decision}"
            )

    explicit_classification = bool(
        objective or list(structures) or list(capabilities) or primary or list(secondary)
    )
    hydrated_classification = hydration.get("classification", {}) or {}
    if not explicit_classification and hydrated_classification:
        objective = hydrated_classification.get("objective")
        structures = hydrated_classification.get("structures", []) or []
        capabilities = hydrated_classification.get("capabilities", []) or []
        field_provenance["classification"] = "project_state"
    elif explicit_classification:
        field_provenance["classification"] = "explicit"

    effective_artifacts, artifact_evidence, artifact_conflicts = reconcile_legacy_artifacts(
        available_artifacts or (), hydration
    )
    context_conflicts.extend(artifact_conflicts)
    dependency_state_supplied = available_artifacts is not None or bool(project_root)
    base_available: Iterable[str] | None = effective_artifacts if dependency_state_supplied else None

    plan = resolve_workflow(
        selected_intents,
        request=None,
        objective=objective,
        structures=structures,
        capabilities=capabilities,
        primary=primary,
        secondary=secondary,
        competition=competition,
        available_artifacts=base_available,
        preprocessing_decision=preprocessing_decision,
    )
    dependency = apply_contract_dependency_closure(plan, manifest, assurance_contract)

    fingerprint_sources = (
        assurance_contract.get("authority_fingerprint", {}) or {}
    ).get("ordered_sources", []) or []
    fingerprint = authority_fingerprint(ROOT, fingerprint_sources)
    ambiguities = _unique(
        [
            *(hydration.get("ambiguities", []) or []),
            *(
                ["intent resolution has tied top candidates"]
                if intent_diagnostics.get("ambiguity")
                else []
            ),
        ]
    )
    review_required = bool(context_conflicts or ambiguities)

    plan["version"] = bootstrap.get("skill_version", plan.get("version"))
    plan["runtime_plan"] = {
        "selected_intents": list(plan.get("intents", [])),
        "delivery_scope": plan.get("delivery_scope"),
        "pause_state": plan.get("pause_state"),
        "modules": list(plan.get("modules", [])),
        "pre_delivery_gate_names": [
            item.get("name") for item in plan.get("pre_delivery_gates", [])
        ],
        "terminal_outputs": list(plan.get("terminal_outputs", [])),
    }
    plan["assurance"] = {
        "schema_version": assurance_contract.get("version", "1.0.0"),
        "status": "review_required" if review_required else "pass",
        "context": {
            "project_state_loaded": bool(hydration.get("loaded")),
            "project_root": hydration.get("project_root"),
            "state_path": hydration.get("state_path"),
            "question": question,
            "field_provenance": field_provenance,
            "conflicts": context_conflicts,
            "ambiguities": ambiguities,
        },
        "intent_resolution": intent_diagnostics,
        "artifact_assurance": {
            "effective_artifacts": effective_artifacts,
            "evidence": artifact_evidence,
            "conflicts": artifact_conflicts,
        },
        "dependency_closure": dependency,
        "authority_fingerprint": fingerprint,
    }
    return plan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("intents", nargs="*")
    parser.add_argument("--request")
    parser.add_argument("--objective")
    parser.add_argument("--structures", nargs="*", default=[])
    parser.add_argument("--capabilities", nargs="*", default=[])
    parser.add_argument("--primary", help="legacy compatibility label")
    parser.add_argument("--secondary", nargs="*", default=[], help="legacy compatibility labels")
    parser.add_argument("--competition")
    parser.add_argument("--available-artifacts", nargs="*", default=None)
    parser.add_argument(
        "--preprocessing-decision",
        choices=["not_needed", "project_level", "question_local"],
    )
    parser.add_argument("--project-root")
    parser.add_argument("--question")
    args = parser.parse_args()
    try:
        plan = resolve_runtime(
            args.intents,
            request=args.request,
            objective=args.objective,
            structures=args.structures,
            capabilities=args.capabilities,
            primary=args.primary,
            secondary=args.secondary,
            competition=args.competition,
            available_artifacts=args.available_artifacts,
            preprocessing_decision=args.preprocessing_decision,
            project_root=args.project_root,
            question=args.question,
        )
    except (ValueError, FileNotFoundError) as exc:
        raise SystemExit(str(exc)) from exc
    print(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
