#!/usr/bin/env python3
"""Resolve one or more user intents into an ordered HSK v7.0.1 execution plan."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Iterable

import yaml

ROOT = Path(__file__).resolve().parent.parent
BOOTSTRAP_PATH = ROOT / "core" / "bootstrap.yaml"
ROUTER_PATH = ROOT / "core" / "workflow_router.yaml"
MANIFEST_PATH = ROOT / "core" / "module_manifest.yaml"
TAXONOMY_PATH = ROOT / "core" / "task_taxonomy.yaml"
COMPETITION_PATH = ROOT / "config" / "competition_profiles.yaml"
SCOPE_RANK = {"design": 0, "code": 1, "results": 2, "figures": 3, "docx": 4, "latex": 5, "submission": 6}


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def unique(items: Iterable[str | None]) -> list[str]:
    return list(dict.fromkeys(str(item) for item in items if item and str(item).strip()))


def resolve_competition_pack(token: str | None, profiles: dict[str, Any]) -> str | None:
    if not token:
        return None
    normalized = token.strip().lower()
    for name, config in profiles.get("profiles", {}).items():
        aliases = [name, *config.get("aliases", [])]
        if normalized in {str(item).lower() for item in aliases}:
            return config.get("stable", {}).get("competition_pack")
    raise ValueError(f"unknown competition: {token}")


def infer_intents(request: str, router: dict[str, Any]) -> list[str]:
    text = request.strip().lower()
    if not text:
        return []
    matches: list[tuple[int, str]] = []
    for name, route in router.get("routing", {}).items():
        keywords = route.get("infer_keywords", route.get("triggers", []))
        score = sum(1 for word in keywords if str(word).lower() in text)
        if score:
            matches.append((score, name))
    if not matches:
        return []
    selected = [name for _, name in sorted(matches, key=lambda item: (-item[0], item[1]))]
    if "full_workflow" in selected:
        return ["full_workflow"]
    return unique(selected)


def legacy_to_axes(
    primary: str | None,
    secondary: Iterable[str],
    taxonomy: dict[str, Any],
) -> tuple[str | None, list[str], list[str]]:
    labels = unique(([primary] if primary else []) + list(secondary))
    mapping = taxonomy.get("legacy_mapping", {})
    objective: str | None = None
    structures: list[str] = []
    packs: list[str] = []
    for label in labels:
        if label not in mapping:
            raise ValueError(f"unknown legacy task label: {label}")
        item = mapping[label]
        objective = objective or item.get("objective")
        structures.extend(item.get("structures", []))
        packs.append(label)
    return objective, unique(structures), unique(packs)


def axes_to_packs(
    objective: str | None,
    structures: Iterable[str],
    taxonomy: dict[str, Any],
) -> list[str]:
    packs: list[str] = []
    if objective:
        objective_spec = taxonomy.get("objectives", {}).get(objective)
        if not objective_spec:
            raise ValueError(f"unknown objective: {objective}")
        packs.append(objective_spec.get("legacy_pack"))
    for structure in structures:
        structure_spec = taxonomy.get("structures", {}).get(structure)
        if not structure_spec:
            raise ValueError(f"unknown structure: {structure}")
        packs.append(structure_spec.get("supplemental_pack"))
    return unique(packs)


def ordered_modules(paths: Iterable[str], manifest: dict[str, Any]) -> list[str]:
    order = manifest.get("workflow_order") or manifest.get("workflow_profiles", {}).get("full_workflow", {}).get("modules", [])
    rank = {name: index for index, name in enumerate(order)}
    module_to_path = {
        name: spec.get("path") for name, spec in manifest.get("modules", {}).items() if isinstance(spec, dict)
    }
    path_rank = {path: rank.get(name, 10_000) for name, path in module_to_path.items()}
    modules = unique(path for path in paths if path.startswith("modules/"))
    return sorted(modules, key=lambda path: (path_rank.get(path, 10_000), modules.index(path)))


def close_module_dependencies(
    modules: Iterable[str],
    available_artifacts: set[str],
    manifest: dict[str, Any],
) -> list[str]:
    """Add unique upstream producers when the caller supplied current artifact state."""
    module_specs = manifest.get("modules", {})
    path_to_name = {
        spec.get("path"): name for name, spec in module_specs.items() if isinstance(spec, dict)
    }
    producers: dict[str, list[str]] = {}
    for name, spec in module_specs.items():
        if not isinstance(spec, dict):
            continue
        for artifact in spec.get("outputs", []):
            producers.setdefault(str(artifact), []).append(name)
    selected = set(modules)
    external = set(manifest.get("external_artifacts", []))
    while True:
        produced = set(available_artifacts)
        changed = False
        for path in ordered_modules(selected, manifest):
            name = path_to_name.get(path)
            if not name:
                continue
            spec = module_specs[name]
            for artifact in spec.get("inputs", []):
                if artifact in produced or artifact in external:
                    continue
                candidates = producers.get(str(artifact), [])
                if len(candidates) != 1:
                    continue
                producer_path = module_specs[candidates[0]].get("path")
                if producer_path and producer_path not in selected:
                    selected.add(producer_path)
                    changed = True
            produced.update(spec.get("outputs", []))
        if not changed:
            return ordered_modules(selected, manifest)


def prerequisite_report(
    modules: Iterable[str],
    available_artifacts: set[str],
    manifest: dict[str, Any],
) -> tuple[list[str], list[str]]:
    missing: list[str] = []
    produced = set(available_artifacts)
    path_to_module = {
        spec.get("path"): name for name, spec in manifest.get("modules", {}).items() if isinstance(spec, dict)
    }
    for path in modules:
        name = path_to_module.get(path)
        if not name:
            continue
        spec = manifest["modules"][name]
        for artifact in spec.get("inputs", []):
            if artifact not in produced and artifact not in manifest.get("external_artifacts", []):
                missing.append(f"{name}:{artifact}")
        produced.update(spec.get("outputs", []))
    return unique(missing), sorted(produced)


def highest_scope(scopes: Iterable[str]) -> str | None:
    valid = [scope for scope in scopes if scope in SCOPE_RANK]
    return max(valid, key=SCOPE_RANK.get) if valid else None


def gate_plan(
    gate_names: Iterable[str],
    manifest: dict[str, Any],
    delivery_scope: str | None,
) -> list[dict[str, Any]]:
    plans: list[dict[str, Any]] = []
    for name in unique(gate_names):
        spec = manifest.get("utility_gates", {}).get(name)
        if not isinstance(spec, dict):
            raise ValueError(f"unknown utility gate: {name}")
        command = str(spec.get("command", ""))
        if delivery_scope:
            command = command.replace("<delivery_scope>", delivery_scope)
        plans.append({
            "name": name,
            "path": spec.get("path"),
            "command": command,
            "delivery_scope": delivery_scope,
            "inputs": list(spec.get("inputs", [])),
            "outputs": list(spec.get("outputs", [])),
        })
    return plans


PRIMARY_CODE_OUTPUTS = [
    "python_code", "full_run_config", "execution_instructions", "code_delivery_report",
    "awaiting_user_execution", "model_paper_framework",
]
ANALYSIS_CODE_OUTPUTS = [
    "result_analysis_plan", "result_analysis_code", "full_run_config",
    "execution_instructions", "code_delivery_report", "awaiting_user_execution",
    "model_paper_framework",
]
FINAL_WORKFLOW_OUTPUTS = [
    "approved_figures", "latex_source", "compiled_pdf", "compile_report",
    "review_report", "model_paper_framework",
]
DOWNSTREAM_MODULES = {
    "modules/03_result_analysis.md", "modules/04_figure_evidence.md",
    "modules/05_writing/docx.md", "modules/05_writing/latex.md",
    "modules/05_writing/ai_cleanup.md", "modules/05_latex_compile_quality.md",
    "modules/06_review_delivery.md",
}


def apply_user_execution_boundary(
    intents: list[str],
    paths: list[str],
    outputs: list[str],
    scopes: list[str],
    gates: list[str],
    formal_delivery: bool,
    pause: bool,
    available: set[str],
) -> tuple[list[str], list[str], list[str], list[str], bool, bool]:
    """Select the next executable segment without crossing a user execution gate."""
    primary_accepted = (
        "accepted_solution_workbook" in available
        or {"solution_workbook", "result_quality_report"}.issubset(available)
        or {"solved_results", "result_quality_report"}.issubset(available)
    )
    analysis_accepted = (
        "accepted_result_analysis_workbook" in available
        or {"result_analysis_workbook", "validated_results"}.issubset(available)
    )
    intent_set = set(intents)
    analysis_requested = bool(intent_set & {"result_analysis", "validation"})
    code_requested = bool(intent_set & {"full_solution", "code_and_solution"})

    def keep_before_analysis(items: list[str]) -> list[str]:
        return [item for item in items if item not in DOWNSTREAM_MODULES]

    if "full_workflow" in intent_set:
        if not primary_accepted:
            paths = keep_before_analysis(paths)
            if "modules/03_solve_validate.md" not in paths:
                paths.append("modules/03_solve_validate.md")
            return paths, PRIMARY_CODE_OUTPUTS.copy(), ["code"], ["code_delivery"], False, True
        if not analysis_accepted:
            paths = [item for item in paths if item != "modules/03_solve_validate.md" and item not in DOWNSTREAM_MODULES]
            paths.append("modules/03_result_analysis.md")
            return paths, ANALYSIS_CODE_OUTPUTS.copy(), ["code"], ["code_delivery"], False, True
        paths = [item for item in paths if item not in {"modules/03_solve_validate.md", "modules/03_result_analysis.md"}]
        paths.extend([
            "modules/04_figure_evidence.md", "modules/05_writing/latex.md",
            "modules/05_writing/ai_cleanup.md", "modules/05_latex_compile_quality.md",
            "modules/06_review_delivery.md",
        ])
        return paths, FINAL_WORKFLOW_OUTPUTS.copy(), ["submission"], ["project_sync"], True, False

    if analysis_requested and not primary_accepted:
        paths = keep_before_analysis(paths)
        if "modules/03_solve_validate.md" not in paths:
            paths.append("modules/03_solve_validate.md")
        return paths, PRIMARY_CODE_OUTPUTS.copy(), ["code"], ["code_delivery"], False, True
    if analysis_requested and primary_accepted and not analysis_accepted:
        paths = [item for item in paths if item != "modules/03_solve_validate.md" and item not in DOWNSTREAM_MODULES]
        paths.append("modules/03_result_analysis.md")
        return paths, ANALYSIS_CODE_OUTPUTS.copy(), ["code"], ["code_delivery"], False, True
    if code_requested and not primary_accepted:
        paths = keep_before_analysis(paths)
        return paths, PRIMARY_CODE_OUTPUTS.copy(), ["code"], ["code_delivery"], False, True
    return paths, outputs, scopes, gates, formal_delivery, pause


def resolve_workflow(
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
    router_path: Path = ROUTER_PATH,
    manifest_path: Path = MANIFEST_PATH,
    taxonomy_path: Path = TAXONOMY_PATH,
    competition_path: Path = COMPETITION_PATH,
) -> dict[str, Any]:
    bootstrap = load_yaml(BOOTSTRAP_PATH)
    router = load_yaml(router_path)
    manifest = load_yaml(manifest_path)
    taxonomy = load_yaml(taxonomy_path)

    explicit_intents = [intents] if isinstance(intents, str) else list(intents or [])
    resolved_intents = unique(explicit_intents + infer_intents(request or "", router))
    if not resolved_intents:
        raise ValueError("no workflow intent resolved; pass an intent or --request")
    unknown_intents = [name for name in resolved_intents if name not in router.get("routing", {})]
    if unknown_intents:
        valid = ", ".join(sorted(router.get("routing", {})))
        raise ValueError(f"unknown intents {unknown_intents}; choose from {valid}")

    legacy_objective, legacy_structures, legacy_packs = legacy_to_axes(primary, secondary, taxonomy)
    objective = objective or legacy_objective
    structures = unique([*legacy_structures, *structures])
    max_structures = int(taxonomy.get("classification_contract", {}).get("structures_max_items", 3))
    if len(structures) > max_structures:
        raise ValueError(f"at most {max_structures} structures are allowed")
    allowed_capabilities = set(taxonomy.get("capabilities", {}))
    capability_list = unique(capabilities)
    unknown_capabilities = sorted(set(capability_list) - allowed_capabilities)
    if unknown_capabilities:
        raise ValueError(f"unknown capabilities: {unknown_capabilities}")
    task_packs = unique([*legacy_packs, *axes_to_packs(objective, structures, taxonomy)])
    if len(task_packs) > 3:
        raise ValueError("resolved task packs exceed the one-primary/two-secondary loading budget")

    available_set = set(available_artifacts or ())
    paths: list[str] = ["core/bootstrap.yaml"]
    module_terminal_outputs: list[str] = []
    formal_delivery = False
    route_scopes: list[str] = []
    explicit_gates: list[str] = []
    pause_for_user_execution = False
    for intent in resolved_intents:
        route = router["routing"][intent]
        paths.extend(router.get("default_load", []))
        paths.extend(route.get("load", []))
        paths.extend(route.get("then", []))
        module_terminal_outputs.extend(route.get("terminal_outputs", []))
        formal_delivery = formal_delivery or bool(route.get("formal_delivery"))
        if route.get("delivery_scope"):
            route_scopes.append(route["delivery_scope"])
        explicit_gates.extend(route.get("pre_delivery_gates", []))
        pause_for_user_execution = pause_for_user_execution or bool(route.get("pause_for_user_execution"))
        if route.get("load_competition_pack"):
            pack = resolve_competition_pack(competition, load_yaml(competition_path))
            paths.append(pack or "packs/competition/auto.md")
        if route.get("load_classified_task_packs"):
            if not task_packs:
                raise ValueError(f"intent {intent} requires objective/structures or legacy primary label")
            paths.extend(f"packs/task/{label}.md" for label in task_packs)
    if any(router["routing"][name].get("load_proposition_pack") for name in resolved_intents):
        paths.append("packs/artifact/proposition_proof.md")

    paths, module_terminal_outputs, route_scopes, explicit_gates, formal_delivery, pause_for_user_execution = apply_user_execution_boundary(
        resolved_intents,
        paths,
        module_terminal_outputs,
        route_scopes,
        explicit_gates,
        formal_delivery,
        pause_for_user_execution,
        available_set,
    )
    module_paths = ordered_modules(paths, manifest)
    dependency_closure_applied = available_artifacts is not None
    if dependency_closure_applied:
        module_paths = close_module_dependencies(module_paths, available_set, manifest)
        paths.extend(module_paths)
    non_modules = [path for path in unique(paths) if not path.startswith("modules/")]
    ordered = unique([*non_modules, *module_paths])
    if formal_delivery:
        module_terminal_outputs.append("model_paper_framework")
        explicit_gates.extend(router.get("execution_contract", {}).get("formal_delivery_gates", []))
    delivery_scope = highest_scope(route_scopes)
    gates = gate_plan(explicit_gates, manifest, delivery_scope)

    missing, produced_after_modules = prerequisite_report(module_paths, available_set, manifest)
    available_after_plan = set(produced_after_modules)
    terminal_outputs = unique(module_terminal_outputs)
    for gate in gates:
        for artifact in gate["inputs"]:
            if artifact not in available_after_plan and artifact not in manifest.get("external_artifacts", []):
                missing.append(f"gate:{gate['name']}:{artifact}")
        available_after_plan.update(gate["outputs"])
        terminal_outputs.extend(gate["outputs"])

    return {
        "version": router.get("version", bootstrap.get("skill_version")),
        "intents": resolved_intents,
        "classification": {
            "objective": objective,
            "structures": structures,
            "legacy_task_packs": task_packs,
            "capabilities": capability_list,
        },
        "competition": competition,
        "delivery_scope": delivery_scope,
        "dependency_closure_applied": dependency_closure_applied,
        "modules": module_paths,
        "packs": [item for item in ordered if item.startswith("packs/")],
        "templates": [item for item in ordered if item.startswith("templates/")],
        "contracts": [item for item in ordered if item.startswith("core/")],
        "load_order": ordered,
        "module_terminal_outputs": unique(module_terminal_outputs),
        "pre_delivery_gates": gates,
        "terminal_outputs": unique(terminal_outputs),
        "missing_prerequisites": unique(missing),
        "available_after_modules": produced_after_modules,
        "available_after_plan": sorted(available_after_plan),
        "sync_required_before_delivery": any(gate["name"] == "project_sync" for gate in gates),
        "pause_for_user_execution": pause_for_user_execution,
        "task_code_execution_allowed": False,
    }


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
    args = parser.parse_args()
    try:
        plan = resolve_workflow(
            args.intents,
            request=args.request,
            objective=args.objective,
            structures=args.structures,
            capabilities=args.capabilities,
            primary=args.primary,
            secondary=args.secondary,
            competition=args.competition,
            available_artifacts=args.available_artifacts,
        )
    except (ValueError, FileNotFoundError) as exc:
        raise SystemExit(str(exc)) from exc
    print(yaml.safe_dump(plan, allow_unicode=True, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())