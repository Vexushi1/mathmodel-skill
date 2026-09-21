#!/usr/bin/env python3
"""Resolve an HSK workflow with declarative runtime context and assurance."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable

import yaml

from resolve_workflow import TAXONOMY_PATH, add_solver_resources, code_artifact_projection, legacy_to_axes, resolve_workflow
from reading_plan import build_reading_plan
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
WRITING_RUNTIME_PATH = ROOT / "core" / "writing_runtime_contract.yaml"
COMPETITION_PROFILES_PATH = ROOT / "config" / "competition_profiles.yaml"


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _unique(items: Iterable[str | None]) -> list[str]:
    return list(dict.fromkeys(str(item) for item in items if item and str(item).strip()))


def _resolve_competition_profile(
    token: str, profiles: dict[str, Any]
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    normalized = token.strip().lower()
    for name, config in (profiles.get("profiles", {}) or {}).items():
        aliases = [name, *(config.get("aliases", []) or [])]
        if normalized not in {str(item).strip().lower() for item in aliases}:
            continue
        stable = config.get("stable", {}) or {}
        runtime_profile = stable.get("writing_runtime")
        if not isinstance(runtime_profile, dict):
            raise ValueError(
                f"competition profile {name} lacks stable.writing_runtime; "
                "declare template_first_progressive or full_reasoning_fallback"
            )
        return str(name), config, runtime_profile
    raise ValueError(f"unknown competition profile for writing runtime: {token}")


def _apply_profile_writing_runtime(
    plan: dict[str, Any], *, profiles: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Apply competition writing-runtime policy without competition-specific Python branches.

    Competition profiles select whether a route uses Template-First progressive writing or
    retains the full reasoning authority. The writing runtime contract still owns the common
    writing capabilities and fallback semantics; this function only assembles the resources
    declared by the active competition profile.
    """
    intents = set(str(item) for item in plan.get("intents", []))
    competition = str(plan.get("competition") or "").strip()
    if not intents or not competition:
        return plan

    profile_payload = profiles if profiles is not None else load_yaml(COMPETITION_PROFILES_PATH)
    profile_name, _profile, runtime_profile = _resolve_competition_profile(
        competition, profile_payload
    )
    mode = str(runtime_profile.get("mode") or "").strip()
    if mode == "full_reasoning_fallback":
        return plan
    if mode != "template_first_progressive":
        raise ValueError(
            f"competition profile {profile_name} has unsupported writing_runtime.mode: {mode!r}"
        )

    supported = {str(item) for item in runtime_profile.get("supported_intents", [])}
    compact_intents = {str(item) for item in runtime_profile.get("compact_intents", [])}
    if not supported:
        raise ValueError(f"competition profile {profile_name} has no supported writing intents")
    if not compact_intents.issubset(supported):
        raise ValueError(
            f"competition profile {profile_name} compact_intents must be a subset of supported_intents"
        )
    if not intents.intersection(supported):
        return plan

    runtime = load_yaml(WRITING_RUNTIME_PATH)
    writing_module = runtime.get("writing_module", {}) or {}
    adapter = str(writing_module.get("latex_adapter") or "")
    load_order = list(plan.get("load_order", []))
    if not adapter or adapter not in load_order:
        return plan

    template_manifest = str(runtime_profile.get("template_manifest") or "").strip()
    if not template_manifest:
        raise ValueError(
            f"competition profile {profile_name} template_first_progressive mode requires template_manifest"
        )
    if not (ROOT / template_manifest).is_file():
        raise ValueError(
            f"competition profile {profile_name} template manifest does not exist: {template_manifest}"
        )

    old_authority = str(
        (runtime.get("full_authority_fallback", {}) or {}).get(
            "authority", "core/writing_reasoning_contract.yaml"
        )
    )
    runtime_order = _unique(runtime.get("ordinary_writing_resource_order", []))
    default_policy = "core/hsk_core_policy.md"
    if default_policy in runtime_order:
        runtime_order.remove(default_policy)

    canonical_manifest = str(
        (runtime.get("canonical_template", {}) or {}).get("manifest") or ""
    )
    if canonical_manifest and canonical_manifest in runtime_order:
        runtime_order = [
            template_manifest if item == canonical_manifest else item for item in runtime_order
        ]
    elif template_manifest not in runtime_order:
        runtime_order.append(template_manifest)
    runtime_order = _unique(runtime_order)

    compact = intents.issubset(compact_intents)
    managed = set(runtime_order)
    if compact:
        managed.add(old_authority)
    load_order = [item for item in load_order if item not in managed]
    insertion_point = load_order.index(default_policy) + 1 if default_policy in load_order else 0
    load_order[insertion_point:insertion_point] = runtime_order
    load_order = _unique(load_order)

    plan["load_order"] = load_order
    plan["contracts"] = [item for item in load_order if item.startswith("core/")]
    plan["templates"] = [item for item in load_order if item.startswith("templates/")]
    plan["writing_runtime"] = {
        "mode": "compact" if compact else "full_authority",
        "execution_mode": "template_first_progressive_authoring",
        "competition": str(runtime_profile.get("competition_label") or profile_name),
        "contract": "core/writing_runtime_contract.yaml",
        "protocol": str(writing_module.get("protocol") or "modules/05_writing/paper_writing_protocol.md"),
        "template_manifest": template_manifest,
        "resource_order_semantics": runtime.get("template_first_progressive_authoring", {}).get(
            "resource_order_semantics"
        ),
        "initial_read_order": list(
            runtime.get("template_first_progressive_authoring", {}).get("initial_read_order", [])
        ),
        "authoring_sequence": list(
            runtime.get("template_first_progressive_authoring", {}).get("stages", [])
        ),
        "full_reasoning_authority_preloaded": old_authority in load_order,
        "full_reasoning_authority_fallback": old_authority,
        "fallback_triggers": list(
            runtime.get("semantic_capabilities", {}).get(
                "load_full_reasoning_authority_when_any", []
            )
        ),
    }
    return plan

def _solver_context(
    requested: str | None, hydration: dict[str, Any], intents: list[str],
) -> tuple[str | None, dict[str, Any] | None, list[str]]:
    """Resolve a scoped preference without overwriting a previously delivered choice."""
    if requested is not None and requested not in {"auto", "python", "matlab"}:
        raise ValueError(f"unknown solver backend: {requested}")
    by_question = hydration.get("solver_backends") or {}
    stage = "analysis" if set(intents).intersection({"result_analysis", "validation"}) else "primary"
    resolved: dict[str, Any] = {}
    conflicts: list[str] = []
    modern = False
    for question, stages in by_question.items():
        selected = stages.get(stage) or {}
        if not selected and stage == "analysis" and requested not in {"python", "matlab"}:
            selected = stages.get("primary") or {}
        backend = selected.get("backend")
        modern |= selected.get("source") == "project_state"
        if backend and requested not in {None, "auto", backend}:
            conflicts.append(f"{question}.{stage} requested backend {requested} conflicts with current {backend}")
        resolved[question] = {
            "backend": backend or (requested if requested != "auto" else None),
            "source": selected.get("source") or ("explicit" if requested else "unresolved"),
        }
    if requested is None and not modern:
        return None, None, conflicts  # Exact legacy return projection remains available.
    choices = {row["backend"] for row in resolved.values() if row["backend"]}
    complete = bool(resolved) and all(row["backend"] for row in resolved.values())
    effective = next(iter(choices)) if complete and len(choices) == 1 else requested or "auto"
    if complete and len(choices) > 1:
        effective = "auto"
    context = {
        "request": requested, "stage": stage, "by_question": resolved,
        "resolved": effective if effective != "auto" else None,
        "selection_complete": complete or (not resolved and effective in {"python", "matlab"}),
        "source": "project_state" if modern else "explicit", "environment_verified": False,
        "decision_contract": "core/user_execution_contract.yaml#solver_backends",
    }
    return effective, context, conflicts


def resolve_runtime(
    intents: str | Iterable[str] | None = None,
    *,
    request: str | None = None,
    objective: str | None = None,
    structures: Iterable[str] | None = None,
    capabilities: Iterable[str] | None = None,
    primary: str | None = None,
    secondary: Iterable[str] = (),
    competition: str | None = None,
    available_artifacts: Iterable[str] | None = None,
    preprocessing_decision: str | None = None,
    solver_backend: str | None = None,
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
    effective_backend, solver_context, solver_conflicts = _solver_context(solver_backend, hydration, selected_intents)
    field_provenance: dict[str, str] = {}

    if competition is None and hydration.get("competition"):
        competition = str(hydration["competition"])
        field_provenance["competition"] = "project_state"
    elif competition is not None:
        field_provenance["competition"] = "explicit"
        state_competition = hydration.get("competition")
        profiles = load_yaml(COMPETITION_PROFILES_PATH)
        if state_competition and _resolve_competition_profile(str(state_competition), profiles)[0] != _resolve_competition_profile(competition, profiles)[0]:
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

    secondary = list(secondary)
    legacy_requested = bool(primary or secondary)
    legacy_objective, legacy_structures, _ = (
        legacy_to_axes(primary, secondary, load_yaml(TAXONOMY_PATH))
        if legacy_requested else (None, [], [])
    )
    explicit_fields = {
        "objective": objective is not None or legacy_objective is not None,
        "structures": structures is not None or legacy_requested,
        "capabilities": capabilities is not None,
    }
    hydrated_classification = hydration.get("classification", {}) or {}
    objective = objective if objective is not None else legacy_objective or hydrated_classification.get("objective")
    structures = list(structures) if structures is not None else (
        legacy_structures if legacy_requested else hydrated_classification.get("structures", []) or []
    )
    capabilities = list(capabilities) if capabilities is not None else hydrated_classification.get("capabilities", []) or []
    if any(explicit_fields.values()) or hydrated_classification:
        field_provenance["classification"] = "explicit" if any(explicit_fields.values()) else "project_state"
        for field, explicit in explicit_fields.items():
            if explicit or field in hydrated_classification:
                field_provenance[f"classification.{field}"] = "explicit" if explicit else "project_state"

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
        # Backend projection follows the actual resumed stage, not the request intent.
        solver_backend=None,
    )
    if "modules/03_solve_validate.md" in plan["modules"]:
        effective_backend, solver_context, solver_conflicts = _solver_context(solver_backend, hydration, ["code_and_solution"])
    elif "modules/03_result_analysis.md" in plan["modules"]:
        effective_backend, solver_context, solver_conflicts = _solver_context(solver_backend, hydration, ["result_analysis"])
    context_conflicts.extend(solver_conflicts)
    if solver_context is not None:
        aliases = load_yaml(ROOT / "core/output_contract.yaml").get("solver_artifact_aliases", {})
        plan = code_artifact_projection(plan, aliases)
        plan["solver_backend"] = solver_context
        field_provenance["solver_backend"] = solver_context["source"]
        if solver_context["selection_complete"]:
            plan["missing_prerequisites"] = [value for value in plan["missing_prerequisites"] if value != "solver_backend_selection"]
            backends = [row["backend"] for row in solver_context["by_question"].values() if row["backend"]]
            add_solver_resources(plan, backends or [effective_backend])
        elif any(module in plan["modules"] for module in ("modules/03_solve_validate.md", "modules/03_result_analysis.md")):
            plan["missing_prerequisites"] = _unique([*plan["missing_prerequisites"], "solver_backend_selection"])
    for field, explicit in explicit_fields.items():
        if not explicit or field not in hydrated_classification:
            continue
        current = plan["classification"][field]
        previous = hydrated_classification[field]
        differs = current != previous if field == "objective" else set(current) != set(previous)
        if differs:
            context_conflicts.append(
                f"explicit classification.{field} {current} differs from current project scope {previous}"
            )
    dependency = apply_contract_dependency_closure(plan, manifest, assurance_contract)
    # Assurance closure may legitimately add the full writing reasoning contract because
    # old module dependencies still know the v7 authority graph. Apply the v8 compact
    # projection afterwards so pure prose-generation routes do not preload that file.
    plan = _apply_profile_writing_runtime(plan)

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
        "writing_runtime": plan.get("writing_runtime"),
    }
    if solver_context is not None:
        plan["runtime_plan"]["solver_backend"] = solver_context
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
            **({"solver_backends": hydration.get("solver_backends", {})} if solver_context is not None else {}),
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
    # P2 adds consumption guidance only; old plan fields and machine closure stay intact.
    plan["reading_plan"] = build_reading_plan(ROOT, plan, router, manifest, request or "")
    return plan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("intents", nargs="*")
    parser.add_argument("--request")
    parser.add_argument("--objective")
    parser.add_argument("--structures", nargs="*")
    parser.add_argument("--capabilities", nargs="*")
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
    parser.add_argument("--solver-backend", choices=["auto", "python", "matlab"])
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
            solver_backend=args.solver_backend,
        )
    except (ValueError, FileNotFoundError) as exc:
        raise SystemExit(str(exc)) from exc
    print(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
