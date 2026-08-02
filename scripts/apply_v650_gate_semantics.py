#!/usr/bin/env python3
"""Apply v6.5.0 staged user-execution semantics to router lint and manifest."""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"missing anchor in {path}: {old[:100]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


def patch_manifest() -> None:
    path = ROOT / "core/module_manifest.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    external = data["external_artifacts"]
    for item in ("accepted_solution_workbook", "accepted_result_analysis_workbook"):
        if item in external:
            external.remove(item)
    catalog = data["artifact_catalog"]
    catalog["accepted_solution_workbook"] = "通过运行配置、哈希和主结果质量门验收的主工作簿"
    catalog["accepted_result_analysis_workbook"] = "通过运行配置和结论稳定性验收的结果深化工作簿"
    figure_inputs = data["modules"]["figure_evidence"]["inputs"]
    data["modules"]["figure_evidence"]["inputs"] = [item for item in figure_inputs if item != "evidence_map"]
    data["utility_gates"]["user_execution_receipt"]["outputs"] = [
        "user_execution_validation_report", "project_state",
        "solution_workbook", "accepted_solution_workbook", "result_quality_report", "solved_results",
        "result_analysis_workbook", "accepted_result_analysis_workbook", "validated_results",
    ]
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")


def patch_resolver() -> None:
    path = ROOT / "scripts/resolve_workflow.py"
    marker = '''def resolve_workflow(
'''
    helper = '''PRIMARY_CODE_OUTPUTS = [
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


'''
    replace(path, marker, helper + marker)
    replace(
        path,
        '''    paths: list[str] = ["core/bootstrap.yaml"]
''',
        '''    available_set = set(available_artifacts or ())
    paths: list[str] = ["core/bootstrap.yaml"]
''',
    )
    replace(
        path,
        '''    if any(router["routing"][name].get("load_proposition_pack") for name in resolved_intents):
        paths.append("packs/artifact/proposition_proof.md")

    module_paths = ordered_modules(paths, manifest)
    dependency_closure_applied = available_artifacts is not None
    available_set = set(available_artifacts or ())
''',
        '''    if any(router["routing"][name].get("load_proposition_pack") for name in resolved_intents):
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
''',
    )


def patch_lint() -> None:
    path = ROOT / "scripts/lint_skill.py"
    replace(
        path,
        '''    "core/workbook_schema.yaml", "core/project_state.schema.yaml", "core/compile_profiles.yaml",
''',
        '''    "core/workbook_schema.yaml", "core/project_state.schema.yaml", "core/compile_profiles.yaml",
    "core/user_execution_contract.yaml",
''',
    )
    replace(
        path,
        '''    "scripts/resolve_workflow.py", "scripts/sync_project.py",
''',
        '''    "scripts/resolve_workflow.py", "scripts/sync_project.py",
    "scripts/validate_code_delivery.py", "scripts/validate_user_execution.py",
''',
    )
    replace(
        path,
        '''VERSION_CONTRACTS = ["core/bootstrap.yaml", "core/workflow_router.yaml", "core/module_manifest.yaml", "core/output_contract.yaml", "core/project_state.schema.yaml"]
''',
        '''VERSION_CONTRACTS = ["core/bootstrap.yaml", "core/workflow_router.yaml", "core/module_manifest.yaml", "core/output_contract.yaml", "core/project_state.schema.yaml", "core/user_execution_contract.yaml"]
''',
    )
    old_router = '''    full = routes.get("full_workflow", {})
    loaded = list(full.get("load", [])) + list(full.get("then", []))
    if "modules/03_solve_validate.md" not in loaded or "modules/03_result_analysis.md" not in loaded:
        errors.append("full_workflow must load primary solve and result analysis")
    if loaded.index("modules/03_solve_validate.md") > loaded.index("modules/03_result_analysis.md"):
        errors.append("full_workflow result-analysis order invalid")
    if "modules/05_writing/docx.md" in loaded:
        errors.append("default full_workflow must not load DOCX")
    if "modules/05_writing/latex.md" not in loaded:
        errors.append("default full_workflow must load LaTeX")
'''
    new_router = '''    full = routes.get("full_workflow", {})
    loaded = list(full.get("load", [])) + list(full.get("then", []))
    if full.get("pause_for_user_execution") is not True:
        errors.append("full_workflow must pause at the user execution gate")
    if full.get("delivery_scope") != "code" or full.get("pre_delivery_gates") != ["code_delivery"]:
        errors.append("full_workflow initial segment must use the code-delivery gate")
    if "modules/03_solve_validate.md" not in loaded:
        errors.append("full_workflow initial segment must load primary solve code generation")
    if any(item in loaded for item in ("modules/03_result_analysis.md", "modules/04_figure_evidence.md", "modules/05_writing/latex.md")):
        errors.append("full_workflow must not cross a user execution gate in its initial segment")
    if "modules/05_writing/docx.md" in loaded:
        errors.append("default full_workflow must not load DOCX")
    if router.get("execution_contract", {}).get("task_code_execution_allowed") is not False:
        errors.append("router must forbid assistant task-code execution")
'''
    replace(path, old_router, new_router)
    replace(
        path,
        '''    for name, spec in modules.items():
        for artifact in spec.get("inputs", []):
''',
        '''    for gate_name, gate in (manifest.get("utility_gates", {}) or {}).items():
        for output in gate.get("outputs", []):
            producers.setdefault(output, []).append(f"gate:{gate_name}")
    for name, spec in modules.items():
        for artifact in spec.get("inputs", []):
''',
    )
    replace(
        path,
        '''            upstream = [producer for producer in producers.get(artifact, []) if rank.get(producer, 999) < rank.get(name, 999)]
''',
        '''            upstream = [
                producer for producer in producers.get(artifact, [])
                if producer.startswith("gate:") or rank.get(producer, 999) < rank.get(name, 999)
            ]
''',
    )
    replace(
        path,
        '''        if not {"solved_results", "result_quality_report", "solution_workbook"}.issubset(inputs):
            errors.append("result_analysis must depend on solved results and quality report")
    profile = manifest.get("workflow_profiles", {}).get("full_workflow", {}).get("modules", [])
    if "result_analysis" not in profile or "writing_docx" in profile or "writing_latex" not in profile:
        errors.append("full_workflow manifest profile is incomplete")
''',
        '''        if not {"accepted_solution_workbook", "result_quality_report"}.issubset(inputs):
            errors.append("result_analysis must depend on an accepted primary workbook and quality report")
    profile_spec = manifest.get("workflow_profiles", {}).get("full_workflow", {})
    profile = profile_spec.get("modules", [])
    if profile != ["problem_audit", "model_design", "solve_validate"]:
        errors.append("full_workflow initial manifest profile must stop at solve_validate")
    if profile_spec.get("pre_delivery_gates") != ["code_delivery"]:
        errors.append("full_workflow initial manifest profile must use code_delivery")
''',
    )
    replace(
        path,
        '''    expected_scopes = {"design", "results", "figures", "docx", "latex", "submission"}
''',
        '''    expected_scopes = {"design", "code", "results", "figures", "docx", "latex", "submission"}
''',
    )


def patch_legacy_pointer() -> None:
    path = ROOT / "legacy/README.md"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("v6.4.1 默认运行链路", "v6.5.0 默认运行链路"), encoding="utf-8")


def main() -> int:
    patch_manifest()
    patch_resolver()
    patch_lint()
    patch_legacy_pointer()
    print("v6.5.0 staged gate semantics applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
