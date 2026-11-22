#!/usr/bin/env python3
"""Resolve an HSK workflow with declarative runtime context and assurance."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable

import yaml
import safe_yaml
import stage_code as STAGE_CODE
import question_scheduler as QUESTION_SCHEDULER

from resolve_workflow import TAXONOMY_PATH, add_solver_resources, code_artifact_projection, legacy_to_axes, resolve_workflow, review_only_request, route_boundary_roles
from reading_plan import build_reading_plan
from state_transitions import dependency_cycles, dependency_edges
from runtime_assurance import (
    ProjectStateSnapshot,
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
    return safe_yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _unique(items: Iterable[str | None]) -> list[str]:
    return list(dict.fromkeys(str(item) for item in items if item and str(item).strip()))


def _resolve_competition_profile(
    token: str, profiles: dict[str, Any]
) -> tuple[str, dict[str, Any], dict[str, Any]] | None:
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
    # An unknown competition uses the generic writing authority already declared by
    # the route. Competition-specific template-first behavior is an optional adapter.
    return None


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

    # Template-first runtime is specific to the LaTeX adapter. Do not even load
    # writing-runtime configuration for non-LaTeX routes.
    load_order = list(plan.get("load_order", []))
    if "modules/05_writing/latex.md" not in load_order:
        return plan
    runtime = load_yaml(WRITING_RUNTIME_PATH)
    writing_module = runtime.get("writing_module", {}) or {}
    adapter = str(writing_module.get("latex_adapter") or "")
    if not adapter or adapter not in load_order:
        return plan

    profile_payload = profiles if profiles is not None else load_yaml(COMPETITION_PROFILES_PATH)
    profile_result = _resolve_competition_profile(competition, profile_payload)
    if profile_result is None:
        # The generic route already loads full writing reasoning authority. Leave that
        # route intact rather than failing because no competition-specific profile exists.
        return plan
    profile_name, _profile, runtime_profile = profile_result
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

    template_manifest = str(runtime_profile.get("template_manifest") or "").strip()
    if not template_manifest:
        raise ValueError(
            f"competition profile {profile_name} template_first_progressive mode requires template_manifest"
        )

    old_authority = str(
        (runtime.get("full_authority_fallback", {}) or {}).get(
            "authority", "core/writing_reasoning_contract.yaml"
        )
    )
    if not (ROOT / template_manifest).is_file():
        writing_sequence = runtime.get("template_first_progressive_authoring", {}) or {}
        chapter_handoff = writing_sequence.get("cross_file_chapter_handoff", {}) or {}
        activation = chapter_handoff.get("activation", {}) or {}
        missing_manifest_policy = activation.get("non_cumcm_or_missing_manifest")
        if missing_manifest_policy != "full_reasoning_fallback":
            raise ValueError(
                f"competition profile {profile_name} template manifest does not exist and "
                f"fallback is not authorized by core/writing_runtime_contract.yaml: "
                f"{template_manifest}"
            )

        canonical_template = runtime.get("canonical_template", {}) or {}
        unavailable_template_resources = {
            template_manifest,
            str(canonical_template.get("manifest") or "").strip(),
            str(canonical_template.get("executable_entry") or "").strip(),
        }
        unavailable_template_resources.discard("")
        load_order = [
            item for item in load_order if item not in unavailable_template_resources
        ]
        default_policy = "core/hsk_core_policy.md"
        if old_authority not in load_order:
            insertion_point = (
                load_order.index(default_policy) + 1 if default_policy in load_order else 0
            )
            load_order.insert(insertion_point, old_authority)

        plan["load_order"] = _unique(load_order)
        plan["contracts"] = [
            item for item in plan["load_order"] if item.startswith("core/")
        ]
        plan["templates"] = [
            item for item in plan["load_order"] if item.startswith("templates/")
        ]
        plan.pop("writing_runtime", None)
        return plan

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
    requested: str | None, hydration: dict[str, Any], state: dict[str, Any] | None,
    stage: str | None, *, project_root_supplied: bool,
) -> tuple[str | None, dict[str, Any] | None, list[str]]:
    """Project policy is the only current selection; requests are never state writes."""
    if requested is not None and requested not in {"auto", "python", "matlab"}:
        raise ValueError(f"unknown solver backend: {requested}")
    candidate = requested if requested in {"python", "matlab"} else None
    if not project_root_supplied and requested is None:
        return None, None, []  # Stateless legacy planning keeps its old projection.
    if not project_root_supplied or not hydration.get("loaded"):
        scope = "stateless" if not project_root_supplied else "project"
        source = "explicit_candidate" if candidate else "unresolved"
        context = {
            "scope": scope, "request": requested, "stage": stage,
            "resolved": candidate if scope == "stateless" else None,
            "candidate_backend": candidate, "selection_complete": False,
            "source": source, "conflicts": [], "environment_verified": False,
            "decision_contract": "core/user_execution_contract.yaml#solver_backends",
        }
        return candidate if scope == "stateless" else None, context, []

    assert state is not None
    report = STAGE_CODE.inspect_project_backend_declarations(state, requested_backend=requested)
    conflicts = list(report["issues"])
    try:
        backend = STAGE_CODE.current_project_backend(state, requested_backend=requested)
    except STAGE_CODE.StageCodeError as exc:
        if report["kind"] == "canonical_declarations" and report["request_conflict"]:
            backend = STAGE_CODE.current_project_backend(state)
        else:
            backend = None
            if not conflicts:
                conflicts.append(str(exc))
    complete = backend is not None and report["kind"] == "canonical_declarations"
    source = ("project_state" if complete else "historical_read_only" if report["kind"].startswith("legacy_")
              else "explicit_candidate" if report["kind"] == "unselected" and candidate else "unresolved")
    context = {
        "scope": "project", "request": requested, "stage": stage,
        "resolved": backend, "candidate_backend": report["candidate_backend"] or candidate,
        "selection_complete": complete, "source": source, "conflicts": conflicts,
        "environment_verified": False,
        "decision_contract": "core/user_execution_contract.yaml#solver_backends",
    }
    return backend, context, conflicts


def _project_result_prerequisites(
    snapshot: ProjectStateSnapshot, hydration: dict[str, Any], question: str | None,
    context_conflicts: list[str],
) -> tuple[str, ...]:
    """Requalify all project results before a question-scoped workflow can finalize."""
    if not hydration["loaded"]:
        return ("full_workflow_resume:project_state",)
    if question is None or "validated_results" not in hydration["verified_artifacts"]:
        return ()

    project = hydrate_project_context(snapshot.root, state_snapshot=snapshot)
    context_conflicts.extend(project["conflicts"])
    if project["conflicts"]:
        return ("full_workflow_resume:project_state",)
    if "validated_results" in project["verified_artifacts"]:
        return ()

    evidence = project["artifact_evidence"]
    verified = {(row["scope"], row["artifact"]) for row in evidence if row["status"] == "verified"}
    missing = []
    for row in evidence:
        if row["artifact"] != "accepted_solution_workbook":
            continue
        scoped_question = row["scope"]
        if row["status"] != "verified":
            missing.append(f"full_workflow_resume:{scoped_question}:accepted_solution_workbook")
        elif not any((scoped_question, artifact) in verified for artifact in (
            "accepted_result_analysis_workbook", "result_analysis_not_required",
        )):
            missing.append(f"full_workflow_resume:{scoped_question}:validated_results")
    return tuple(missing) or ("full_workflow_resume:validated_results",)


def _question_receipt_target(
    root: Path, question: str, entry: dict[str, Any]
) -> tuple[str | None, list[str]]:
    numeral = STAGE_CODE.question_name(question).removeprefix("问题")
    output = load_yaml(ROOT / "core/output_contract.yaml")["per_question"]
    folder = output["question_directory"].replace("{中文序号}", numeral)
    patterns = {
        "primary": output["mandatory_workbooks"]["solution"],
        "analysis": output["conditional_workbooks"]["result_analysis"]["path"],
    }
    paths = {
        stage: f"{folder.rstrip('/')}/{pattern.replace('{中文序号}', numeral)}"
        for stage, pattern in patterns.items()
    }
    pending = {
        stage: path for stage, path in paths.items()
        if entry.get(f"{stage}_execution_status") == "awaiting_user_execution"
    }
    candidates = [
        path for path in (pending or paths).values()
        if STAGE_CODE._relative_path(root, path).is_file()
    ]
    return (candidates[0] if len(candidates) == 1 else None,
            candidates or list((pending or paths).values()))


def _scope_gate_commands(
    plan: dict[str, Any], root: Path, state: dict[str, Any], question: str,
    backend: str | None,
) -> list[str]:
    """Bind gate commands while retaining the router's ordered gate list."""
    outputs = set(plan["module_terminal_outputs"])
    stage_choices = [
        stage for stage, artifact in (
            ("preprocessing", "preprocessing_code"), ("primary", "primary_code"),
            ("analysis", "result_analysis_code"),
        ) if artifact in outputs
    ]
    stage = stage_choices[0] if len(stage_choices) == 1 else None
    entry = (state.get("subproblems") or {}).get(question)
    known = isinstance(entry, dict) and STAGE_CODE.question_number(question) is not None
    issues: list[str] = []
    for gate in plan["pre_delivery_gates"]:
        name = gate["name"]
        if not known and name in {"semantic_governance", "model_approval", "code_delivery", "user_execution_receipt"}:
            issues.append(f"{question}: gate requires a supported registered question")
        if (name == "semantic_governance"
                and plan.get("delivery_scope") in {"design", "code", "results", "figures"}
                and stage != "preprocessing"):
            target = question if known else "<registered_question>"
            gate["command"] += f' --question "{target}"'
        elif name == "model_approval" and stage != "preprocessing":
            target = question if known else "<registered_question>"
            gate["command"] += f' --question "{target}"'
        elif name == "code_delivery":
            target = "<stage_script>"
            if stage == "preprocessing" or (stage and backend and known):
                try:
                    registration = (state.get("preprocessing") or {}) if stage == "preprocessing" else entry
                    script = STAGE_CODE.planned_stage_code_path(
                        root, question, stage, backend, entry=registration,
                    )
                    target = script.relative_to(root).as_posix()
                except (OSError, ValueError) as exc:
                    issues.append(f"{question}: cannot bind {stage} code delivery: {exc}")
            elif stage is None:
                issues.append(f"{question}: select one code delivery stage")
            gate["command"] += f' --script "{target}" --stage "{stage or "<stage>"}"'
        elif name == "user_execution_receipt":
            target = "<returned_workbook>"
            if known:
                try:
                    path, candidates = _question_receipt_target(root, question, entry)
                    if path:
                        target = path
                    else:
                        issues.append(f"{question}: select one returned workbook: {', '.join(candidates)}")
                except (OSError, ValueError) as exc:
                    issues.append(f"{question}: cannot bind returned workbook: {exc}")
            gate["command"] += f' --workbook "{target}"'
    return issues


def _dependency_diagnostics(
    snapshot: ProjectStateSnapshot, question: str | None, stage: str,
    artifact_evidence: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Observe scoped result dependencies without inferring execution requirements."""
    subproblems = snapshot.payload().get("subproblems") or {}
    incoming: dict[str, set[tuple[str, str]]] = {}
    for edge in dependency_edges(subproblems):
        if edge["kind"] in {"result", "legacy_untyped"}:
            incoming.setdefault(edge["target"], set()).add((edge["source"], edge["kind"]))

    results = {
        row["scope"]: row for row in artifact_evidence
        if row["artifact"] == "accepted_solution_workbook"
    }
    pending = [question] if question is not None else sorted(subproblems, reverse=True)
    visited: set[str] = set()
    observations = []
    legacy = []
    unresolved: dict[str, Any] = {}
    while pending:
        target = pending.pop()
        if target in visited:
            continue
        visited.add(target)
        for upstream, kind in sorted(incoming.get(target, ())):
            edge = {"question": target, "upstream": upstream}
            if kind == "legacy_untyped":
                legacy.append(edge)
                continue
            if upstream not in subproblems:
                observations.append({**edge, "status": "unregistered",
                                     "reason": "upstream question is not registered in project state"})
                continue
            if upstream not in results:
                context = hydrate_project_context(snapshot.root, upstream, state_snapshot=snapshot)
                results[upstream] = next((
                    row for row in context["artifact_evidence"]
                    if row["artifact"] == "accepted_solution_workbook" and row["scope"] == upstream
                ), {"status": "unavailable", "reason": "no current accepted primary workbook evidence"})
            row = results[upstream]
            observations.append({**edge, "status": row["status"], "reason": row["reason"]})
            if row["status"] != "verified":
                unresolved.setdefault(target, {"depends_on": []})["depends_on"].append(
                    {"question": upstream, "kind": "result"}
                )
                pending.append(upstream)

    if not observations and not legacy:
        return {}
    return {
        "stage": stage,
        "result_dependencies": observations,
        "unresolved_result_cycles": dependency_cycles(unresolved),
        "legacy_dependencies": legacy,
    }


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
    candidate_startup_event: str | None = None,
    source_commit: str | None = None,
) -> dict[str, Any]:
    bootstrap = load_yaml(BOOTSTRAP_PATH)
    router = load_yaml(ROUTER_PATH)
    manifest = load_yaml(MANIFEST_PATH)
    assurance_contract = load_yaml(ASSURANCE_PATH)

    if (candidate_startup_event is None) != (source_commit is None):
        raise ValueError("candidate startup requires both an explicit event and its pinned source commit")
    startup_reading = None
    if candidate_startup_event is not None and source_commit is not None:
        from read_stage import verify_checkout

        commit = verify_checkout(ROOT, source_commit)

        startup = bootstrap["startup_contract"]
        profile = startup["candidate_events"].get(candidate_startup_event)
        if profile is None:
            raise ValueError(f"unknown candidate startup event: {candidate_startup_event}")
        reading = startup["profiles"][profile]["reading"]
        startup_reading = {
            "selector": startup["activation"]["candidate_selector"],
            "event": candidate_startup_event,
            "profile": profile,
            "reading": reading,
            "source_commit": commit,
            "status": "selection_only",
        }
        if reading != "current_action_text":
            delivery = assurance_contract["reading_plan"]["formal_rule_delivery"]
            startup_reading.update(manifest=delivery["manifest"], reader=delivery["reader"])

    explicit_intents = [intents] if isinstance(intents, str) else list(intents or [])
    selected_intents, intent_diagnostics = resolve_intent_assurance(
        explicit_intents, request or "", router
    )
    if not selected_intents:
        raise ValueError("no workflow intent resolved; pass an intent or --request")
    if review_only_request(request or "", router) and set(explicit_intents) - {"review"}:
        raise ValueError("explicit intent conflicts with review-only request; resolve review without write actions")

    requested_question = question
    state_snapshot = ProjectStateSnapshot.capture(project_root) if project_root else None
    question_selection = None
    if state_snapshot is not None and state_snapshot.raw is not None:
        requested = set(selected_intents)
        # M2 adds a default only when the caller did not name a Qn.
        # Explicit --question retains the pre-M2 resolver envelope and gates.
        if (question is None and requested.intersection(QUESTION_SCHEDULER.QUESTION_ROUTES)
                and not requested.intersection(QUESTION_SCHEDULER.FINAL_ROUTES)):
            state_for_selection = state_snapshot.payload()
            registered = state_for_selection.get("subproblems") or {}
            if not isinstance(registered, dict):
                raise ValueError("project subproblems must be a mapping")
            # Explicit Qn observes one target and its necessary incoming graph
            # closure. Unrelated sibling artifacts must not be opened just to
            # decide the requested target; the complete State snapshot is shared.
            inspected = set(registered) if question is None else set()
            if question is not None:
                incoming = {}
                for edge in dependency_edges(registered):
                    incoming.setdefault(edge["target"], set()).add(edge["source"])
                pending = [question]
                while pending:
                    target = pending.pop()
                    if target in inspected or target not in registered:
                        continue
                    inspected.add(target)
                    pending.extend(incoming.get(target, ()))
            verified_by_question = {
                name: hydrate_project_context(
                    project_root, name, state_snapshot=state_snapshot,
                ).get("verified_artifacts", [])
                for name in sorted(inspected)
            }
            question_selection = QUESTION_SCHEDULER.select_question(
                state_for_selection,
                explicit_question=question,
                selected_intents=selected_intents,
                request=request or "",
                verified_artifacts=verified_by_question,
            )
            if question is None and question_selection["scope_kind"] == "question":
                question = question_selection["selected_question"]
            state_snapshot.assert_current()
    hydration = (
        hydrate_project_context(project_root, question, state_snapshot=state_snapshot)
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
        profiles = load_yaml(COMPETITION_PROFILES_PATH)
        if state_competition:
            state_profile = _resolve_competition_profile(str(state_competition), profiles)
            explicit_profile = _resolve_competition_profile(competition, profiles)
            state_name = state_profile[0] if state_profile else str(state_competition).strip().lower()
            explicit_name = explicit_profile[0] if explicit_profile else competition.strip().lower()
            if state_name != explicit_name:
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
    project_result_prerequisites = ()
    if state_snapshot is not None and "full_workflow_resume" in route_boundary_roles(selected_intents, router):
        project_result_prerequisites = _project_result_prerequisites(
            state_snapshot, hydration, question, context_conflicts,
        )

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
        project_result_prerequisites=project_result_prerequisites,
        figure_request=request,
    )
    if "figure_composition" in plan:
        intent_diagnostics["selected_intents"] = list(plan["intents"])
        if intent_diagnostics["ambiguity"] and set(selected_intents) == {"editable_mechanism_diagram", "figures"}:
            intent_diagnostics.update(ambiguity=False, confidence_band="medium", confidence_score=0.6,
                                      selection_reason="the requested physical figures resolve the tied figure routes")
    actual_stage = ("primary" if "modules/03_solve_validate.md" in plan["modules"] else
                    "analysis" if "modules/03_result_analysis.md" in plan["modules"] else None)
    numerical_context = actual_stage is not None or any(module in plan["modules"] for module in (
        "modules/02_model_design.md", "modules/03_data_preprocessing.md"))
    requested_backend = "auto" if solver_backend is None and numerical_context else solver_backend
    effective_backend, solver_context, solver_conflicts = _solver_context(
        requested_backend, hydration, state_snapshot.payload() if state_snapshot is not None else None,
        actual_stage, project_root_supplied=project_root is not None,
    )
    context_conflicts = _unique([*context_conflicts, *solver_conflicts])
    if solver_context is not None:
        aliases = load_yaml(ROOT / "core/output_contract.yaml").get("solver_artifact_aliases", {})
        plan = code_artifact_projection(plan, aliases)
        plan["solver_backend"] = solver_context
        field_provenance["solver_backend"] = solver_context["source"]
        if solver_context["selection_complete"]:
            plan["missing_prerequisites"] = [value for value in plan["missing_prerequisites"] if value != "solver_backend_selection"]
            add_solver_resources(plan, [effective_backend])
        elif solver_context["scope"] == "stateless" and effective_backend in {"python", "matlab"}:
            # Explicit generic planning may show a template without claiming a project selection.
            add_solver_resources(plan, [effective_backend])
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
    if state_snapshot is not None:
        from conformance_gate import add_runtime_resources
        state_payload = state_snapshot.payload()
        add_runtime_resources(plan, state_payload, question)
        paper_framework = state_payload.get("paper_framework")
        policy = paper_framework.get("claim_consumption_policy") if isinstance(paper_framework, dict) else None
        claim_pair = (policy.get("protocol_version"), policy.get("mode")) if isinstance(policy, dict) else None
        selected_pair = ("1.5.0", "enforce_selected_paper_claim_chain")
        paper_source = policy.get("paper_source") if isinstance(policy, dict) else None
        carrier_format = (paper_source.get("format")
                          if claim_pair == selected_pair and isinstance(paper_source, dict)
                          else None)
        legacy_enabled = (
            claim_pair in {("1.2.0", "enforce_latex_text"),
                           ("1.3.0", "enforce_latex_text_and_figure_chain"),
                           ("1.4.0", "enforce_latex_text_and_figure_chain")}
            and plan.get("delivery_scope") in {"latex", "submission"}
        )
        selected_enabled = (
            claim_pair == selected_pair
            and ((carrier_format == "latex" and plan.get("delivery_scope") in {"latex", "submission"})
                 or (carrier_format == "docx" and plan.get("delivery_scope") in {"docx", "submission"}))
        )
        if ((legacy_enabled or selected_enabled)
                and any(gate.get("name") == "project_sync" for gate in plan.get("pre_delivery_gates", []))):
            resources = ["core/claim_consumption_contract.yaml", "core/claim_evidence_contract.yaml",
                         "scripts/claim_consumption.py"]
            figure_policy = claim_pair[0] in {"1.3.0", "1.4.0", "1.5.0"}
            if figure_policy:
                resources.extend(["modules/04_figure_evidence.md", "scripts/claim_figure.py"])
            if carrier_format == "docx":
                resources.append("scripts/claim_docx.py")
            elif figure_policy:
                resources.append("scripts/latex_delivery.py")
            for path in resources:
                if path not in plan["load_order"]:
                    plan["load_order"].append(path)
                if path.startswith("core/") and path not in plan["contracts"]:
                    plan["contracts"].append(path)
            plan["claim_consumption_integration"] = {
                "mode": claim_pair[1], "protocol_version": claim_pair[0],
                "scope": (
                    "declared_bounded_docx_text_and_figure_chain"
                    if carrier_format == "docx"
                    else "declared_static_selected_latex_text_and_figure_chain"
                    if claim_pair[0] == "1.5.0"
                    else "declared_static_modular_latex_text_and_figure_chain"
                    if figure_policy
                    else "declared_static_modular_latex_text_only"
                ),
                "consumer_gates": ["project_sync"], "resources": resources,
                "human_semantic_coverage": "not_assessed",
            }
            if claim_pair == selected_pair:
                plan["claim_consumption_integration"].update({
                    "carrier_format": carrier_format,
                    "entrypoint": paper_source.get("entrypoint"),
                })
    dependency = apply_contract_dependency_closure(plan, manifest, assurance_contract)
    # Assurance closure may legitimately add the full writing reasoning contract because
    # old module dependencies still know the v7 authority graph. Apply the v8 compact
    # projection afterwards so pure prose-generation routes do not preload that file.
    plan = _apply_profile_writing_runtime(plan)
    if state_snapshot is not None:
        import plot_backend
        plot = plot_backend.inspect_plotting(state_snapshot.payload())
        context_conflicts.extend(plot["issues"])
        output = load_yaml(ROOT / "core/output_contract.yaml")
        for field in ("module_terminal_outputs", "terminal_outputs", "available_after_modules", "available_after_plan"):
            plan[field] = plot_backend.project_figure_roles(
                plan[field], output, plot["backend"], preprocessing_decision,
            )

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
    if question and state_snapshot is not None:
        selected_backend = effective_backend if solver_context and solver_context["selection_complete"] else None
        context_conflicts = _unique([*context_conflicts, *_scope_gate_commands(
            plan, state_snapshot.root, state_snapshot.payload(), question, selected_backend,
        )])
    dependency_diagnostics = {}
    if (state_snapshot is not None and actual_stage and hydration.get("loaded")
            and any(gate["name"] == "code_delivery" for gate in plan["pre_delivery_gates"])):
        dependency_diagnostics = _dependency_diagnostics(
            state_snapshot, requested_question, actual_stage, hydration["artifact_evidence"],
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
    if question_selection is not None:
        plan["runtime_plan"]["selected_question"] = question_selection["selected_question"]
        plan["runtime_plan"]["scope_kind"] = question_selection["scope_kind"]
        plan["runtime_plan"]["selection_reason"] = question_selection["selection_reason"]
        plan["runtime_plan"]["waiting_action"] = question_selection["waiting_action"]
        # Question selection never changes gate eligibility or qualifies numerical artifacts.
        plan["question_selection"] = question_selection
    plan["assurance"] = {
        "schema_version": assurance_contract.get("version", "1.0.0"),
        "status": "review_required" if review_required else "pass",
        "context": {
            "project_state_loaded": bool(hydration.get("loaded")),
            "project_root": hydration.get("project_root"),
            "state_path": hydration.get("state_path"),
            "question": question,
            **({"question_selection": question_selection} if question_selection is not None else {}),
            "field_provenance": field_provenance,
            "conflicts": context_conflicts,
            "ambiguities": ambiguities,
            **({"dependency_diagnostics": dependency_diagnostics} if dependency_diagnostics else {}),
            **({"backend_policy": hydration.get("backend_policy")} if solver_context is not None else {}),
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
    if "figure_composition" in plan:
        scoped_hydration = {question: hydration}
        registered = list((state_snapshot.payload().get("subproblems") or {})) if state_snapshot else []
        for delivery in plan["figure_composition"]["deliveries"]:
            target = delivery["question"] or question or (registered[0] if len(registered) == 1 else None)
            delivery["question"] = target
            if delivery["delivery_scope"] == "mechanism" and STAGE_CODE.question_number(target) is not None:
                owner = f"Q{STAGE_CODE.question_number(target)}"
                for gate in [*delivery["pre_delivery_gates"], *plan["pre_delivery_gates"]]:
                    if gate["name"] == "project_sync" and gate.get("delivery_scope") == "mechanism":
                        gate["command"] = gate["command"].replace(
                            '--mechanism-question "<registered_question>"', f'--mechanism-question "{owner}"',
                        )
            if state_snapshot is None:
                continue
            if not target or target == "unresolved":
                delivery["evidence_status"] = "question_scope_unresolved"
                continue
            if target not in scoped_hydration:
                scoped_hydration[target] = hydrate_project_context(project_root, target, state_snapshot=state_snapshot)
            current = scoped_hydration[target]
            verified = set(current.get("verified_artifacts", []))
            missing = [item for item in delivery["required_verified_artifacts"] if item not in verified]
            delivery["missing_verified_artifacts"] = missing
            if current.get("loaded"):
                delivery["evidence_status"] = "missing_current_inputs" if missing else "base_inputs_verified"
    if startup_reading is not None:
        plan["startup_reading"] = startup_reading
        if plan.get("writing_runtime") and startup_reading["profile"] in {"formal", "recovery"}:
            plan["writing_runtime"]["resource_order_semantics"] = load_yaml(WRITING_RUNTIME_PATH)["candidate_formal_reading"]["stage_reading"]
    plan["reading_plan"] = build_reading_plan(
        ROOT, plan, router, manifest, request or "", state_snapshot=state_snapshot
    )
    if state_snapshot is not None:
        state_snapshot.assert_current()
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
    parser.add_argument("--candidate-startup-event", help="explicitly selected event from bootstrap.startup_contract.candidate_events")
    parser.add_argument("--source-commit", help="full selected commit for the candidate startup event")
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
            candidate_startup_event=args.candidate_startup_event,
            source_commit=args.source_commit,
        )
    except (ValueError, FileNotFoundError) as exc:
        raise SystemExit(str(exc)) from exc
    print(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
