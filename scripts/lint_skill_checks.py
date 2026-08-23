#!/usr/bin/env python3
"""Validate active HSK graph, preprocessing governance, semantic governance, result contracts, code quality and generated files."""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
PACKAGE_VERSION = "7.8.1"
REQUIRED = [
    "SKILL.md", "README.md", "REPOSITORY_INDEX.md", "SKILL_CHANGE_GOVERNANCE.md", "CHANGELOG.md",
    "PROJECT_INSTRUCTIONS.md", "RUNTIME_ROUTER.md", "SKILL_FILE_INDEX.md", "TEMPLATE_INDEX.md",
    "core/bootstrap.yaml", "core/hsk_core_policy.md", "core/task_taxonomy.yaml",
    "core/workflow_router.yaml", "core/module_manifest.yaml", "core/output_contract.yaml",
    "core/global_preprocessing_contract.yaml", "core/workbook_schema.yaml",
    "core/project_state.schema.yaml", "core/compile_profiles.yaml",
    "core/user_execution_contract.yaml", "core/code_quality_contract.yaml", "core/writing_reasoning_contract.yaml",
    "modules/01_problem_audit.md", "modules/02_model_design.md", "modules/03_data_preprocessing.md",
    "modules/03_solve_validate.md", "modules/03_result_analysis.md", "modules/04_figure_evidence.md",
    "modules/05_latex_compile_quality.md", "modules/05_writing/docx.md", "modules/05_writing/latex.md",
    "modules/05_writing/ai_cleanup.md", "modules/06_review_delivery.md",
    "packs/task/classifier.md", "packs/task/advanced_method_gate.md",
    "packs/artifact/proposition_proof.md", "packs/artifact/algorithm_flow.md", "templates/model/model_paper_framework.md",
    "templates/code/hsk_pipeline/result_io.py", "templates/code/hsk_pipeline/workbook_validation.py",
    "templates/code/hsk_pipeline/main_pipeline.py", "templates/matlab/q1_plot.m",
    "templates/matlab/data_process.m", "templates/latex/cumcm/hsk/hsk_main.tex",
    "templates/latex/diangong/main.tex", "templates/writing/caption_explanation.md",
    "scripts/resolve_workflow.py", "scripts/validate_semantic_governance.py", "scripts/sync_project.py",
    "scripts/validate_code_delivery.py", "scripts/validate_user_execution.py", "scripts/audit_paper_prose.py",
    "scripts/validate_model_paper_framework.py", "scripts/validate_project_state.py",
    "scripts/score_submission.py", ".github/pull_request_template.md",
    ".github/workflows/ci.yml", ".github/workflows/refresh-generated.yml",
    "LICENSE", "THIRD_PARTY_NOTICES.md",
]
ACTIVE_DIRS = ["core", "modules", "packs", "templates", "scripts", "config", "state", "assets", "agents", "skills", ".codex-plugin", ".github"]
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".py", ".m", ".tex", ".bib"}
COMPATIBILITY_POINTERS = {
    "PROJECT_INSTRUCTIONS_HSK_V622.md": "PROJECT_INSTRUCTIONS.md",
    "HSK_RUNTIME_ROUTER_V622.md": "RUNTIME_ROUTER.md",
    "HSK_SKILL_FILE_INDEX_V622.md": "SKILL_FILE_INDEX.md",
    "HSK_TEMPLATE_INDEX_V622.md": "TEMPLATE_INDEX.md",
}
REPO_PATH_PREFIXES = ("core/", "modules/", "packs/", "templates/", "scripts/", "config/", "state/", "assets/", "agents/", "skills/", ".github/", ".codex-plugin/")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
VERSION_DOCS = ["SKILL.md", "README.md", "CHANGELOG.md", "core/hsk_core_policy.md"]
VERSION_CONTRACTS = [
    "core/bootstrap.yaml", "core/workflow_router.yaml", "core/module_manifest.yaml",
    "core/output_contract.yaml",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="strict")


def load_structured(path: Path) -> Any:
    return json.loads(read_text(path)) if path.suffix == ".json" else yaml.safe_load(read_text(path))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def active_files() -> Iterable[Path]:
    for top in ACTIVE_DIRS:
        base = ROOT / top
        if base.exists():
            yield from (path for path in base.rglob("*") if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES)


def check_required(errors: list[str]) -> None:
    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required: {relative}")


def check_compatibility_pointers(errors: list[str]) -> None:
    bootstrap = load_structured(ROOT / "core/bootstrap.yaml") or {}
    if bootstrap.get("compatibility", {}).get("legacy_document_pointers_supported") is not True:
        errors.append("bootstrap must explicitly declare legacy document-pointer compatibility")
    for legacy, active in COMPATIBILITY_POINTERS.items():
        legacy_path = ROOT / legacy
        active_path = ROOT / active
        if not active_path.is_file():
            errors.append(f"compatibility pointer target missing: {legacy} -> {active}")
            continue
        if not legacy_path.is_file():
            errors.append(f"compatibility pointer missing: {legacy}")
            continue
        text = read_text(legacy_path)
        if "Compatibility Pointer" not in text or active not in text:
            errors.append(f"invalid compatibility pointer: {legacy} -> {active}")
    active_index = read_text(ROOT / "SKILL_FILE_INDEX.md") if (ROOT / "SKILL_FILE_INDEX.md").is_file() else ""
    manifest = read_text(ROOT / "MANIFEST.sha256") if (ROOT / "MANIFEST.sha256").is_file() else ""
    for legacy in COMPATIBILITY_POINTERS:
        if f"`{legacy}`" in active_index:
            errors.append(f"compatibility pointer leaked into active index: {legacy}")
        if any(line.endswith(f"  {legacy}") for line in manifest.splitlines()):
            errors.append(f"compatibility pointer leaked into active manifest: {legacy}")


def _check_repo_reference(errors: list[str], value: object, origin: str, *, base: Path | None = None) -> None:
    if not isinstance(value, str):
        return
    token = value.strip().strip("`<>")
    if not token or token.startswith(("http://", "https://", "mailto:", "#", "plugin://")):
        return
    token = token.split("#", 1)[0].strip()
    if not token or any(marker in token for marker in ("{", "}", "<", ">", "*")):
        return
    candidate = (base / token).resolve() if base is not None and not token.startswith(REPO_PATH_PREFIXES) else (ROOT / token)
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        return
    if not candidate.exists():
        errors.append(f"repository reference missing: {origin} -> {token}")


def check_skill_entrypoint_parity(errors: list[str]) -> None:
    """Keep repository and packaged Skill entrypoints on one runtime authority chain."""
    root_skill_path = ROOT / "SKILL.md"
    packaged_skill_path = ROOT / "skills/mathmodel-skill/SKILL.md"
    plugin_path = ROOT / ".codex-plugin/plugin.json"
    bootstrap = load_structured(ROOT / "core/bootstrap.yaml") or {}
    current = str(bootstrap.get("skill_version", ""))
    start = "<!-- HSK_RUNTIME_ENTRY_CONTRACT_START -->"
    end = "<!-- HSK_RUNTIME_ENTRY_CONTRACT_END -->"

    def frontmatter_version(text: str, origin: str) -> str | None:
        match = re.search(r"^version:\s*([^\s]+)", text, flags=re.MULTILINE)
        if not match:
            errors.append(f"skill entrypoint version missing: {origin}")
            return None
        return match.group(1)

    def contract_block(text: str, origin: str) -> str | None:
        if text.count(start) != 1 or text.count(end) != 1:
            errors.append(f"skill entrypoint runtime contract markers invalid: {origin}")
            return None
        return text.split(start, 1)[1].split(end, 1)[0].strip()

    texts = {
        "SKILL.md": read_text(root_skill_path),
        "skills/mathmodel-skill/SKILL.md": read_text(packaged_skill_path),
    }
    blocks: dict[str, str | None] = {}
    required_tokens = (
        "core/bootstrap.yaml", "core/workflow_router.yaml", "core/hsk_core_policy.md",
        "scripts/resolve_workflow.py", "core/writing_reasoning_contract.yaml",
        "模型论文框架.md", "legacy/",
    )
    forbidden_tokens = (
        "HSK_RUNTIME_ROUTER_V622.md", "HSK_SKILL_FILE_INDEX_V622.md",
        "HSK_TEMPLATE_INDEX_V622.md", "PROJECT_INSTRUCTIONS_HSK_V622.md",
    )
    for origin, text_value in texts.items():
        version = frontmatter_version(text_value, origin)
        if version is not None and version != current:
            errors.append(f"skill entrypoint version mismatch: {origin} -> {version}, bootstrap -> {current}")
        block = contract_block(text_value, origin)
        blocks[origin] = block
        if block is None:
            continue
        for token in required_tokens:
            if token not in block:
                errors.append(f"skill entrypoint authority token missing: {origin} -> {token}")
        for token in forbidden_tokens:
            if token in block:
                errors.append(f"skill entrypoint must not depend on compatibility pointer: {origin} -> {token}")

    root_block = blocks.get("SKILL.md")
    packaged_block = blocks.get("skills/mathmodel-skill/SKILL.md")
    if root_block is not None and packaged_block is not None and root_block != packaged_block:
        errors.append("root and packaged SKILL runtime-entry contracts drifted")

    plugin = load_structured(plugin_path) or {}
    if plugin.get("version") != current:
        errors.append(f"plugin/bootstrap version mismatch: plugin -> {plugin.get('version')}, bootstrap -> {current}")
    if plugin.get("skills") != "./skills/":
        errors.append("plugin skill discovery path must remain ./skills/")


def check_repository_references(errors: list[str]) -> None:
    bootstrap = load_structured(ROOT / "core/bootstrap.yaml") or {}
    for key, value in (bootstrap.get("authoritative_sources") or {}).items():
        _check_repo_reference(errors, value, f"bootstrap.authoritative_sources.{key}")
    for key, command in (bootstrap.get("entrypoints") or {}).items():
        if isinstance(command, str):
            parts = command.split()
            if len(parts) >= 2 and parts[0].lower().startswith("python"):
                _check_repo_reference(errors, parts[1], f"bootstrap.entrypoints.{key}")
    maintenance = bootstrap.get("repository_maintenance") or {}
    _check_repo_reference(errors, maintenance.get("governance"), "bootstrap.repository_maintenance.governance")

    router = load_structured(ROOT / "core/workflow_router.yaml") or {}
    _check_repo_reference(errors, router.get("bootstrap"), "router.bootstrap")
    for index, value in enumerate(router.get("default_load", [])):
        _check_repo_reference(errors, value, f"router.default_load[{index}]")
    for route_name, route in (router.get("routing") or {}).items():
        for field in ("load", "then"):
            for index, value in enumerate(route.get(field, [])):
                _check_repo_reference(errors, value, f"router.{route_name}.{field}[{index}]")
        conditional = route.get("conditional_stage") or {}
        _check_repo_reference(errors, conditional.get("module"), f"router.{route_name}.conditional_stage.module")

    manifest = load_structured(ROOT / "core/module_manifest.yaml") or {}
    for key, value in (manifest.get("contracts") or {}).items():
        _check_repo_reference(errors, value, f"manifest.contracts.{key}")
    for name, spec in (manifest.get("modules") or {}).items():
        _check_repo_reference(errors, spec.get("path"), f"manifest.modules.{name}.path")
    for name, spec in (manifest.get("utility_gates") or {}).items():
        _check_repo_reference(errors, spec.get("path"), f"manifest.utility_gates.{name}.path")

    taxonomy = load_structured(ROOT / "core/task_taxonomy.yaml") or {}
    for objective, spec in (taxonomy.get("objectives") or {}).items():
        pack = spec.get("legacy_pack")
        if pack:
            _check_repo_reference(errors, f"packs/task/{pack}.md", f"taxonomy.objectives.{objective}.legacy_pack")
    for structure, spec in (taxonomy.get("structures") or {}).items():
        pack = spec.get("supplemental_pack")
        if pack:
            _check_repo_reference(errors, f"packs/task/{pack}.md", f"taxonomy.structures.{structure}.supplemental_pack")

    competitions = load_structured(ROOT / "config/competition_profiles.yaml") or {}
    compile_profiles = load_structured(ROOT / "core/compile_profiles.yaml") or {}
    known_compile_profiles = set((compile_profiles.get("profiles") or {}).keys())
    for name, spec in (competitions.get("profiles") or {}).items():
        stable = spec.get("stable") or {}
        _check_repo_reference(errors, stable.get("competition_pack"), f"competition.{name}.competition_pack")
        _check_repo_reference(errors, stable.get("latex_template"), f"competition.{name}.latex_template")
        profile = stable.get("compile_profile")
        if profile is not None and profile not in known_compile_profiles:
            errors.append(f"competition compile profile missing: {name} -> {profile}")
    for name, spec in (compile_profiles.get("profiles") or {}).items():
        directory = spec.get("template_directory")
        _check_repo_reference(errors, directory, f"compile_profiles.{name}.template_directory")
        if directory and spec.get("template_main"):
            _check_repo_reference(errors, f"{str(directory).rstrip('/')}/{spec['template_main']}", f"compile_profiles.{name}.template_main")

    root_docs = [
        ROOT / "SKILL.md", ROOT / "README.md", ROOT / "PROJECT_INSTRUCTIONS.md",
        ROOT / "RUNTIME_ROUTER.md", ROOT / "REPOSITORY_INDEX.md", ROOT / "SKILL_CHANGE_GOVERNANCE.md",
    ]
    markdown_files = set(path for path in active_files() if path.suffix.lower() == ".md") | set(root_docs)
    for path in sorted(markdown_files):
        if not path.is_file():
            continue
        for match in MARKDOWN_LINK_RE.finditer(read_text(path)):
            target = match.group(1).strip()
            if target.startswith(("http://", "https://", "mailto:", "#", "plugin://")):
                continue
            target = target.split()[0].strip("<>")
            _check_repo_reference(errors, target, f"markdown:{path.relative_to(ROOT)}", base=path.parent)


def check_resolver_smoke(errors: list[str]) -> None:
    resolver = load_module("lint_resolver_smoke", ROOT / "scripts/resolve_workflow.py")
    router = load_structured(ROOT / "core/workflow_router.yaml") or {}
    manifest = load_structured(ROOT / "core/module_manifest.yaml") or {}
    available = set(manifest.get("external_artifacts", [])) | set(manifest.get("artifact_catalog", {}))
    for gate in (manifest.get("utility_gates") or {}).values():
        available.update(gate.get("outputs", []))

    def validate_plan(label: str, plan: dict[str, Any]) -> None:
        for field in ("modules", "packs", "templates", "contracts", "load_order"):
            for value in plan.get(field, []):
                if isinstance(value, str) and value.startswith(REPO_PATH_PREFIXES):
                    _check_repo_reference(errors, value, f"resolver:{label}:{field}")
        for gate in plan.get("pre_delivery_gates", []):
            _check_repo_reference(errors, gate.get("path"), f"resolver:{label}:gate:{gate.get('name')}")
        if plan.get("missing_prerequisites"):
            errors.append(f"resolver smoke has missing prerequisites for {label}: {plan['missing_prerequisites']}")

    for route_name in (router.get("routing") or {}):
        decision = "project_level" if route_name == "data_preprocessing" else "not_needed"
        try:
            plan = resolver.resolve_workflow(
                route_name,
                objective="optimization",
                structures=["stochastic"],
                available_artifacts=sorted(available),
                preprocessing_decision=decision,
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"resolver route failed: {route_name}: {exc}")
            continue
        validate_plan(route_name, plan)

    competitions = load_structured(ROOT / "config/competition_profiles.yaml") or {}
    for name in (competitions.get("profiles") or {}):
        try:
            plan = resolver.resolve_workflow(
                "model_selection",
                objective="optimization",
                competition=name,
                available_artifacts=sorted(available),
                preprocessing_decision="not_needed",
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"resolver competition failed: {name}: {exc}")
            continue
        validate_plan(f"competition:{name}", plan)


def check_root_release_note_hygiene(errors: list[str]) -> None:
    stale = sorted(path.name for path in ROOT.glob("CHANGELOG_V*.md") if path.is_file())
    if stale:
        errors.append(
            "versioned root changelogs are forbidden; keep active release history in CHANGELOG.md "
            f"and use Git history/legacy for archival material: {', '.join(stale)}"
        )


def check_versions(errors: list[str]) -> None:
    for relative in VERSION_DOCS:
        if PACKAGE_VERSION not in read_text(ROOT / relative):
            errors.append(f"version marker missing: {relative}")
    for relative in VERSION_CONTRACTS:
        payload = load_structured(ROOT / relative) or {}
        value = payload.get("skill_version", payload.get("version"))
        if str(value) != PACKAGE_VERSION:
            errors.append(f"version mismatch: {relative} -> {value}")
    plugin = load_structured(ROOT / ".codex-plugin/plugin.json") or {}
    if plugin.get("version") != PACKAGE_VERSION:
        errors.append("plugin version mismatch")
    if read_text(ROOT / "core/hsk_core_policy.md").splitlines()[0].strip() != f"# HSK Core Policy v{PACKAGE_VERSION}":
        errors.append("core policy current-version header mismatch")
    packaged = read_text(ROOT / "skills/mathmodel-skill/SKILL.md")
    if f"version: {PACKAGE_VERSION}" not in packaged:
        errors.append("packaged skill version mismatch")
    workbook = load_structured(ROOT / "core/workbook_schema.yaml") or {}
    if workbook.get("schema_version") != "2.2.1":
        errors.append("workbook schema version must be 2.2.1")
    compatibility = str(workbook.get("skill_compatibility", ""))
    if ">=6.3.2" not in compatibility or "<8.0.0" not in compatibility:
        errors.append("workbook schema compatibility must cover 6.3.2 through v7")


def check_bootstrap_and_governance(errors: list[str]) -> None:
    data = load_structured(ROOT / "core/bootstrap.yaml") or {}
    for key, path in (data.get("authoritative_sources", {}) or {}).items():
        if not path or not (ROOT / path).is_file():
            errors.append(f"bootstrap authoritative source missing: {key} -> {path}")
    if data.get("authoritative_sources", {}).get("code_quality") != "core/code_quality_contract.yaml":
        errors.append("bootstrap must declare code-quality authority")
    if data.get("authoritative_sources", {}).get("preprocessing") != "core/global_preprocessing_contract.yaml":
        errors.append("bootstrap must declare conditional preprocessing authority")
    if data.get("authoritative_sources", {}).get("semantic_governance") != "scripts/validate_semantic_governance.py":
        errors.append("bootstrap must declare semantic-governance authority")
    if data.get("entrypoints", {}).get("semantic_governance") != "python scripts/validate_semantic_governance.py":
        errors.append("bootstrap must expose validate_semantic_governance.py")
    if data.get("entrypoints", {}).get("sync") != "python scripts/sync_project.py":
        errors.append("bootstrap must expose sync_project.py")
    if data.get("entrypoints", {}).get("audit_paper_prose") != "python scripts/audit_paper_prose.py":
        errors.append("bootstrap must expose audit_paper_prose.py")
    maintenance = data.get("repository_maintenance", {})
    expected = {
        "governance": "SKILL_CHANGE_GOVERNANCE.md",
        "mandatory_before_write": True,
        "read_from_ref": "main",
        "direct_main_write_allowed": False,
    }
    for key, value in expected.items():
        if maintenance.get(key) != value:
            errors.append(f"repository maintenance mismatch: {key}")
    governance = read_text(ROOT / "SKILL_CHANGE_GOVERNANCE.md")
    for token in ("每个新聊天的强制启动顺序", "修改简报", "单一事实源", "一次聊天一个分支", "一个 PR 一个主题", "禁止直接写 main", "生成文件规则", "测试与验收", "完成报告"):
        if token not in governance:
            errors.append(f"governance document lacks section: {token}")
    if "<8.0.0" not in governance:
        errors.append("governance applicability must include v7")


def check_taxonomy(errors: list[str]) -> None:
    data = load_structured(ROOT / "core/task_taxonomy.yaml") or {}
    required_objectives = {"explanation", "inference", "prediction", "evaluation", "optimization", "simulation"}
    if required_objectives - set(data.get("objectives", {})):
        errors.append("task taxonomy lacks required objectives")
    required_capabilities = {"requires_out_of_sample_validation", "requires_uncertainty_quantification", "requires_leakage_check", "requires_calibration_check", "requires_identifiability_check"}
    if required_capabilities - set(data.get("capabilities", {})):
        errors.append("task taxonomy lacks required validation capabilities")
    if data.get("classification_contract", {}).get("authoritative_locations", {}).get("capabilities") != "subproblem.capabilities":
        errors.append("taxonomy must declare top-level capabilities as authoritative")
    compatibility = str(data.get("skill_compatibility", ""))
    if ">=6.3.1" not in compatibility or "<8.0.0" not in compatibility:
        errors.append("task taxonomy compatibility must cover the active v7 line")


def check_router(errors: list[str]) -> None:
    router = load_structured(ROOT / "core/workflow_router.yaml") or {}
    routes = router.get("routing", {})
    execution = router.get("execution_contract", {})
    order = execution.get("workflow_order", [])
    for name in ("data_preprocessing", "solve_validate", "result_analysis", "figure_evidence"):
        if name not in order:
            errors.append(f"workflow order lacks: {name}")
    if all(name in order for name in ("solve_validate", "result_analysis", "figure_evidence")):
        if not order.index("solve_validate") < order.index("result_analysis") < order.index("figure_evidence"):
            errors.append("workflow must place result_analysis between solve and figures")
    if "data_preprocessing" not in execution.get("conditional_modules", []):
        errors.append("data_preprocessing must be declared conditional")
    if execution.get("formal_delivery_gates") != ["semantic_governance", "project_sync"]:
        errors.append("formal delivery must declare semantic_governance then project_sync")
    if execution.get("code_stage_gates") != ["semantic_governance", "code_delivery"]:
        errors.append("code stages must declare semantic_governance before code_delivery")
    if execution.get("task_code_execution_allowed") is not False:
        errors.append("router must forbid assistant task-code execution")
    full = routes.get("full_workflow", {})
    loaded = list(full.get("load", [])) + list(full.get("then", []))
    if full.get("pause_for_user_execution") is not True:
        errors.append("full_workflow must pause at the user execution gate")
    if full.get("delivery_scope") != "code" or full.get("pre_delivery_gates") != ["semantic_governance", "code_delivery"]:
        errors.append("full_workflow initial segment must use semantic and code-delivery gates")
    if "modules/03_solve_validate.md" not in loaded:
        errors.append("full_workflow initial segment must load primary solve code generation")
    if "modules/03_data_preprocessing.md" in loaded:
        errors.append("full_workflow must not unconditionally load project-level preprocessing")
    conditional = full.get("conditional_stage", {})
    if conditional.get("when") != "preprocessing_decision == project_level":
        errors.append("full_workflow must condition preprocessing on project_level decision")
    if any(item in loaded for item in ("modules/03_result_analysis.md", "modules/04_figure_evidence.md", "modules/05_writing/latex.md")):
        errors.append("full_workflow must not cross a user execution gate in its initial segment")
    if "modules/05_writing/docx.md" in loaded:
        errors.append("default full_workflow must not load DOCX")
    analysis_route = routes.get("result_analysis", {})
    if "modules/03_result_analysis.md" not in analysis_route.get("load", []):
        errors.append("result_analysis route must load the dedicated module")
    if "result_analysis_code" not in analysis_route.get("terminal_outputs", []):
        errors.append("result_analysis route must deliver independent result_analysis_code")
    if analysis_route.get("pre_delivery_gates") != ["semantic_governance", "code_delivery"]:
        errors.append("result_analysis must pass semantic governance before code delivery")
    returned = routes.get("returned_workbook_validation", {})
    if returned.get("pre_delivery_gates") != ["semantic_governance", "user_execution_receipt"]:
        errors.append("returned workbook validation must run semantic governance first")
    validation_route = routes.get("validation", {})
    if "modules/03_result_analysis.md" not in validation_route.get("load", []):
        errors.append("validation route must use result-analysis module")
    algorithm_route = routes.get("algorithm_presentation", {})
    if "packs/artifact/algorithm_flow.md" not in algorithm_route.get("load", []):
        errors.append("algorithm_presentation route must load the dedicated algorithm-flow pack")
    if "算法" in algorithm_route.get("infer_keywords", []):
        errors.append("algorithm_presentation inference must use precise paper-algorithm triggers, not plain 算法")
    if not {"算法流程", "伪代码", "论文算法"}.issubset(set(algorithm_route.get("infer_keywords", []))):
        errors.append("algorithm_presentation route lacks precise pseudocode/algorithm-flow triggers")
    for route_name in ("full_workflow", "docx", "latex", "review", "full_submission"):
        if "packs/artifact/algorithm_flow.md" not in (routes.get(route_name, {}) or {}).get("load", []):
            errors.append(f"{route_name} route must make algorithm-flow presentation rules directly available")
    for route_name in ("review", "full_submission"):
        if "core/writing_reasoning_contract.yaml" not in (routes.get(route_name, {}) or {}).get("load", []):
            errors.append(f"{route_name} route must directly load writing-reasoning authority")
    explicit_docx = routes.get("docx", {})
    if explicit_docx.get("delivery_scope") != "docx" or "modules/05_writing/docx.md" not in explicit_docx.get("load", []):
        errors.append("explicit DOCX route must remain available")
    resolver = read_text(ROOT / "scripts/resolve_workflow.py")
    for token in ("pre_delivery_gates", "available_after_modules", "available_after_plan", "gate_plan", "SEMANTIC_CODE_GATES", "SEMANTIC_SYNC_GATES", "apply_preprocessing_boundary", "preprocessing_decision"):
        if token not in resolver:
            errors.append(f"resolver lacks gate-closure token: {token}")
    if "ordered HSK execution plan" not in resolver:
        errors.append("resolver must expose the versionless execution-plan docstring")
    if re.search(r"HSK v\d+\.\d+\.\d+ execution plan", resolver):
        errors.append("resolver execution-plan docstring must remain versionless")


def check_manifest(errors: list[str]) -> None:
    manifest = load_structured(ROOT / "core/module_manifest.yaml") or {}
    catalog = set(manifest.get("artifact_catalog", {}))
    external = set(manifest.get("external_artifacts", []))
    known = catalog | external
    if manifest.get("contracts", {}).get("code_quality") != "core/code_quality_contract.yaml":
        errors.append("manifest must register code-quality contract")
    if manifest.get("contracts", {}).get("preprocessing") != "core/global_preprocessing_contract.yaml":
        errors.append("manifest must register preprocessing contract")
    for token in ("problem_contract", "preprocessing_decision", "semantic_closure", "complexity_sanity_check", "semantic_governance_report"):
        if token not in catalog:
            errors.append(f"manifest lacks semantic artifact: {token}")
    modules = manifest.get("modules", {})
    order = manifest.get("workflow_order", [])
    rank = {name: index for index, name in enumerate(order)}
    producers: dict[str, list[str]] = {}
    for name, spec in modules.items():
        path = spec.get("path")
        if not path or not (ROOT / path).is_file():
            errors.append(f"module path missing: {name} -> {path}")
        for field in ("inputs", "outputs"):
            unknown = set(spec.get(field, [])) - known
            if unknown:
                errors.append(f"module {name} has uncatalogued {field}: {sorted(unknown)}")
        for output in spec.get("outputs", []):
            producers.setdefault(output, []).append(name)
    for gate_name, gate in (manifest.get("utility_gates") or {}).items():
        for output in gate.get("outputs", []):
            producers.setdefault(output, []).append(f"gate:{gate_name}")
    for name, spec in modules.items():
        for artifact in spec.get("inputs", []):
            if artifact in external:
                continue
            upstream = [
                producer for producer in producers.get(artifact, [])
                if producer.startswith("gate:") or rank.get(producer, 999) < rank.get(name, 999)
            ]
            if not upstream:
                errors.append(f"module input lacks upstream producer: {name}:{artifact}")
    preprocessing = modules.get("data_preprocessing", {})
    if preprocessing.get("conditional") is not True or preprocessing.get("activation") != "preprocessing_decision == project_level":
        errors.append("manifest data_preprocessing must be conditional on project_level")
    if "result_analysis" not in modules:
        errors.append("manifest lacks dedicated result_analysis module")
    else:
        inputs = set(modules["result_analysis"].get("inputs", []))
        outputs = set(modules["result_analysis"].get("outputs", []))
        if not {"accepted_solution_workbook", "result_quality_report", "code_quality_contract"}.issubset(inputs):
            errors.append("result_analysis must depend on accepted primary evidence and code-quality contract")
        if "result_analysis_code" not in outputs:
            errors.append("result_analysis must produce independent result_analysis_code")
    solve_inputs = set(modules.get("solve_validate", {}).get("inputs", []))
    if not {"code_quality_contract", "semantic_closure", "complexity_sanity_check", "preprocessing_decision"}.issubset(solve_inputs):
        errors.append("solve_validate must consume code quality, semantic governance and preprocessing decision outputs")
    if "preprocessing_workbook" in solve_inputs:
        errors.append("solve_validate must not unconditionally require preprocessing_workbook")
    solve_conditional = modules.get("solve_validate", {}).get("conditional_inputs", {}) or {}
    if (solve_conditional.get("preprocessing_workbook") or {}).get("when") != "preprocessing_decision == project_level":
        errors.append("solve_validate must condition preprocessing_workbook on project_level")
    if "problem_contract" not in set(modules.get("model_design", {}).get("inputs", [])):
        errors.append("model_design must require frozen problem_contract")
    if "preprocessing_decision" not in set(modules.get("model_design", {}).get("outputs", [])):
        errors.append("model_design must produce preprocessing_decision")
    if "Algorithm Trace" not in str(manifest.get("artifact_catalog", {}).get("model_paper_framework", "")):
        errors.append("model-paper framework artifact description must expose Algorithm Trace project memory")
    profile_spec = manifest.get("workflow_profiles", {}).get("full_workflow", {})
    profile = profile_spec.get("modules", [])
    if profile != ["problem_audit", "model_design", "solve_validate"]:
        errors.append("full_workflow initial manifest profile must stop at solve_validate")
    if (profile_spec.get("conditional_modules") or {}).get("data_preprocessing", {}).get("when") != "preprocessing_decision == project_level":
        errors.append("full_workflow manifest profile must condition data_preprocessing")
    if profile_spec.get("pre_delivery_gates") != ["semantic_governance", "code_delivery"]:
        errors.append("full_workflow initial manifest profile must use semantic and code delivery")
    semantic_gate = manifest.get("utility_gates", {}).get("semantic_governance", {})
    if semantic_gate.get("path") != "scripts/validate_semantic_governance.py":
        errors.append("manifest must register semantic governance gate")
    gate = manifest.get("utility_gates", {}).get("project_sync", {})
    if gate.get("stage_requirements_source") != "core/output_contract.yaml#project_sync.stage_requirements":
        errors.append("project_sync must reference output-contract stage requirements")
    code_gate = manifest.get("utility_gates", {}).get("code_delivery", {})
    if "code_quality_contract" not in code_gate.get("inputs", []):
        errors.append("code-delivery gate must consume code-quality contract")


def check_contracts(errors: list[str]) -> None:
    output = load_structured(ROOT / "core/output_contract.yaml") or {}
    quality = load_structured(ROOT / "core/code_quality_contract.yaml") or {}
    user_execution = load_structured(ROOT / "core/user_execution_contract.yaml") or {}
    preprocessing = load_structured(ROOT / "core/global_preprocessing_contract.yaml") or {}
    decision_values = ((preprocessing.get("decision_gate") or {}).get("decision_values") or [])
    if decision_values != ["not_needed", "question_local", "project_level"]:
        errors.append("preprocessing contract must expose the three-state decision")
    insufficient = (preprocessing.get("activation") or {}).get("never_sufficient_alone", []) or []
    if not any("共享同一原始数据源" in str(item) for item in insufficient):
        errors.append("shared raw data must be explicitly insufficient to require project-level preprocessing")
    audit_dimensions = ((preprocessing.get("judgment_framework") or {}).get("audit_dimensions") or {})
    required_audits = {
        "completeness", "consistency", "validity", "identity_and_duplicates",
        "sampling_and_coverage", "measurement_quality", "model_readiness",
        "temporal_causality_and_leakage", "target_and_label_integrity",
    }
    if required_audits - set(audit_dimensions):
        errors.append("generic preprocessing judgment lacks required cross-competition audit dimensions")
    missing_policy = preprocessing.get("missing_data_policy") or {}
    if "有缺失就插值" not in str(missing_policy.get("principle", "")):
        errors.append("missing-data policy must explicitly reject missing=>interpolation defaults")
    prediction_boundary = preprocessing.get("prediction_boundary") or {}
    if "核心建模" not in str(prediction_boundary.get("principle", "")):
        errors.append("prediction boundary must separate predictive imputation from task prediction")
    if not any("赛题直接要求预测未来值" in str(item) for item in prediction_boundary.get("not_preprocessing_when", [])):
        errors.append("task-requested forecasting must be explicitly excluded from preprocessing")
    paper = preprocessing.get("paper_evidence_contract") or {}
    paper_text = "\n".join(str(item) for item in paper.get("required_paper_elements", []))
    for token in ("数学公式", "参数", "合理性验证", "预处理图"):
        if token not in paper_text:
            errors.append(f"preprocessing paper evidence contract lacks: {token}")
    if "不得编造数学证明" not in str(paper.get("formal_proof_boundary", "")):
        errors.append("preprocessing paper evidence must reject fabricated formal proofs")
    figure_contract = preprocessing.get("preprocessing_figure_contract") or {}
    if figure_contract.get("project_level_script") != "数据预处理/data_process.m":
        errors.append("project-level preprocessing MATLAB script must be 数据预处理/data_process.m")
    if figure_contract.get("export_stem") != "data_process":
        errors.append("preprocessing figure export stem must be data_process")
    pre_files = ((preprocessing.get("project_directory") or {}).get("exact_default_files") or [])
    if pre_files != ["数据预处理.py", "数据预处理结果.xlsx", "data_process.m"]:
        errors.append("project-level preprocessing directory must be the exact three-file data_process layout")
    pre_sheets = set(((preprocessing.get("workbook") or {}).get("common_required_sheets") or {}))
    if not {"预处理方法证据", "处理前后对比", "绘图数据索引"}.issubset(pre_sheets):
        errors.append("preprocessing workbook lacks paper/figure evidence sheets")
    data_process = read_text(ROOT / "templates/matlab/data_process.m")
    for token in ("数据预处理结果.xlsx", "处理前", "处理后"):
        if token not in data_process:
            errors.append(f"data_process MATLAB template lacks: {token}")
    if "exportgraphics(" in data_process:
        errors.append("data_process MATLAB template must not auto-export")
    sync_runtime = read_text(ROOT / "scripts/sync_project.py")
    for token in (
        "MATLAB_PREPROCESSING_FORBIDDEN_FUNCTIONS", "interp2", "normalize", "detrend",
        "filter", "movmean", "movmedian", "predict",
    ):
        if token not in sync_runtime:
            errors.append(f"sync_project preprocessing MATLAB runtime gate lacks: {token}")
    line_policy = quality.get("line_count", {})
    if (line_policy.get("target_max"), line_policy.get("hard_max"), line_policy.get("exemption_max")) != (500, 700, 900):
        errors.append("code-quality line thresholds must be 500/700/900")
    if quality.get("function_size", {}).get("hard_max") != 120:
        errors.append("code-quality function hard limit must be 120")
    if quality.get("parameter_count", {}).get("hard_max") != 12:
        errors.append("code-quality parameter hard limit must be 12")
    scopes = quality.get("scope", [])
    if not isinstance(scopes, list) or "问题X求解/问题X结果深化分析.py" not in scopes:
        errors.append("code-quality contract must cover independent analysis script")
    if "数据预处理/数据预处理.py" not in scopes:
        errors.append("code-quality contract must cover conditional preprocessing script")
    if output.get("code_quality_contract") != "core/code_quality_contract.yaml":
        errors.append("output contract must reference code-quality contract")
    if output.get("preprocessing_contract") != "core/global_preprocessing_contract.yaml":
        errors.append("output contract must reference preprocessing contract")
    if output.get("writing_reasoning_contract") != "core/writing_reasoning_contract.yaml":
        errors.append("output contract must reference writing-reasoning contract")
    semantic = output.get("semantic_governance", {})
    if semantic.get("script") != "scripts/validate_semantic_governance.py":
        errors.append("output contract must declare semantic governance script")
    if semantic.get("dependency_kinds") != ["data", "parameter", "model", "result"]:
        errors.append("semantic governance must define typed dependency kinds")
    execution = output.get("execution_policy", {})
    if execution.get("semantic_governance_gate") != "scripts/validate_semantic_governance.py":
        errors.append("execution policy must require semantic governance")
    if execution.get("preprocessing_required_before_solve_when_decision") != "project_level":
        errors.append("execution policy must require preprocessing only for project_level")
    if execution.get("shared_data_alone_does_not_require_preprocessing") is not True:
        errors.append("execution policy must not promote shared data to preprocessing automatically")

    policy = output.get("writing_policy", {})
    expected_pointers = {
        "reasoning_contract": "core/writing_reasoning_contract.yaml",
        "expression_authority": "modules/05_writing/latex.md",
        "rule_governance": "core/writing_reasoning_contract.yaml#rule_governance",
        "terminology_contract": "core/writing_reasoning_contract.yaml#terminology_governance",
        "numeric_style_contract": "core/writing_reasoning_contract.yaml#numeric_style_contract",
        "title_claim_contract": "core/writing_reasoning_contract.yaml#title_claim_gate",
        "analysis_evidence_disposition_contract": "core/writing_reasoning_contract.yaml#analysis_evidence_disposition",
        "paragraph_necessity_contract": "core/writing_reasoning_contract.yaml#paragraph_necessity",
        "paper_fragment_stale_contract": "core/writing_reasoning_contract.yaml#paper_fragment_stale_governance",
        "citation_evidence_contract": "core/writing_reasoning_contract.yaml#citation_evidence",
        "proposition_governance": "core/writing_reasoning_contract.yaml#proposition_governance",
        "algorithm_presentation_contract": "core/writing_reasoning_contract.yaml#algorithm_presentation",
        "core_model_summary_policy": "adaptive_required_inline_not_applicable",
        "prose_audit_script": "scripts/audit_paper_prose.py",
    }
    for key, expected in expected_pointers.items():
        if policy.get(key) != expected:
            errors.append(f"writing policy authority mismatch: {key} -> {policy.get(key)!r}")
    if policy.get("default_mode") != "latex_first":
        errors.append("default writing mode must be latex_first")
    if policy.get("docx_mode") != "explicit_only_independent" or policy.get("docx_is_latex_prerequisite") is not False:
        errors.append("DOCX must remain explicit-only and not be a LaTeX prerequisite")
    if policy.get("prose_audit_strict_blocks_on") != ["blocking", "review_required"]:
        errors.append("prose audit strict mode must block deterministic Hard failures and unresolved Default review")
    if "Authority" not in str(policy.get("consumer_rule", "")):
        errors.append("writing policy must declare Authority/consumer single-source boundary")

    proposition = output.get("proposition_contract", {})
    if proposition.get("authority") != "core/writing_reasoning_contract.yaml#proposition_governance":
        errors.append("proposition contract must delegate governance to writing reasoning authority")
    if proposition.get("default_budget") != [0, 4]:
        errors.append("proposition default reading budget must be [0, 4]")
    if proposition.get("automatic_rejection_over_budget") is not False:
        errors.append("proposition count above default budget must not be automatic rejection")
    if proposition.get("over_budget_action") != "justification_required":
        errors.append("proposition over-budget action must require justification")
    if proposition.get("display_numbering") != "arabic_section_dot_arabic_proposition":
        errors.append("proposition contract must use Arabic section.proposition numbering")
    if "maximum_per_paper" in proposition:
        errors.append("proposition contract must not retain a hard maximum_per_paper")
    algorithm = output.get("algorithm_presentation_contract", {})
    if algorithm.get("authority") != "core/writing_reasoning_contract.yaml#algorithm_presentation":
        errors.append("algorithm presentation must delegate governance to writing reasoning authority")
    if algorithm.get("modes") != ["not_needed", "stepwise", "pseudocode"]:
        errors.append("algorithm presentation must expose adaptive not_needed/stepwise/pseudocode modes")
    if algorithm.get("detail_pack") != "packs/artifact/algorithm_flow.md":
        errors.append("algorithm presentation must use the on-demand algorithm-flow pack")
    if algorithm.get("no_new_project_state_field_required") is not True:
        errors.append("v7.8 algorithm presentation must not add a mandatory project-state field")

    result_policy = output.get("result_policy", {})
    if result_policy.get("primary_quality_gate_required") is not True:
        errors.append("primary result quality gate must be required")
    if result_policy.get("fixed_perturbation_forbidden") is not True:
        errors.append("fixed perturbation must be forbidden")
    if result_policy.get("result_analysis_dispositions") != ["support", "modify", "reject"]:
        errors.append("result-analysis paper evidence must expose support/modify/reject")
    if result_policy.get("result_analysis_disposition_authority") != "core/writing_reasoning_contract.yaml#analysis_evidence_disposition":
        errors.append("result-analysis dispositions must delegate to writing-reasoning authority")
    per_question = output.get("per_question", {}) or {}
    expected_files = [
        "问题{中文序号}求解.py", "问题{中文序号}求解结果.xlsx",
        "问题{中文序号}结果深化分析.py", "问题{中文序号}结果深化分析.xlsx",
        "q{阿拉伯序号}_plot.m",
    ]
    if per_question.get("exact_default_files") != expected_files:
        errors.append("per-question default must be exact five-file two-script layout")
    if "single_python_update_policy" in per_question:
        errors.append("output contract must not restore single-script overwrite policy")
    delivery = user_execution.get("code_delivery") or {}
    stages = delivery.get("stage_scripts") or {}
    expected_stage_scripts = {
        "primary": "问题X求解/问题X求解.py",
        "analysis": "问题X求解/问题X结果深化分析.py",
    }
    if stages != expected_stage_scripts:
        errors.append("user execution stage_scripts must preserve the per-question primary/analysis two-script interface")
    if delivery.get("preprocessing_script") != "数据预处理/数据预处理.py":
        errors.append("user execution contract must expose conditional preprocessing_script separately")
    if delivery.get("semantic_governance_required") is not True:
        errors.append("user execution code delivery must require semantic governance")
    forbidden = set(delivery.get("standalone_files_forbidden_by_default") or [])
    if "问题X结果深化分析.py" in forbidden:
        errors.append("analysis script must not be forbidden")
    acceptance_rules = "\n".join((user_execution.get("returned_workbook") or {}).get("acceptance_rules", []))
    for token in ("实际路径", "标准文件名", "problem_name", "stage"):
        if token not in acceptance_rules:
            errors.append(f"returned-workbook contract lacks identity binding token: {token}")
    sync = output.get("project_sync", {})
    expected_scopes = {"design", "code", "results", "figures", "docx", "latex", "submission"}
    requirements = sync.get("stage_requirements", {}) or {}
    if set(requirements) != expected_scopes or any(not isinstance(value, list) or not value for value in requirements.values()):
        errors.append("output contract must define every exact delivery scope")
    if "result_analysis_code" not in requirements.get("results", []):
        errors.append("results scope must require independent result-analysis code")
    if "preprocessing_workbook" in requirements.get("results", []):
        errors.append("base results scope must not unconditionally require preprocessing_workbook")
    conditional = (sync.get("conditional_stage_requirements") or {}).get("preprocessing_decision_project_level", {})
    if "preprocessing_workbook" not in conditional.get("results", []):
        errors.append("project_level results scope must conditionally require preprocessing_workbook")
    if sync.get("stage_requirements_semantics") != "exact_scope":
        errors.append("project_sync must preserve the existing exact_scope stage requirements interface")
    if sync.get("conditional_stage_requirements_semantics") != "additive_when_condition_true_without_changing_base_exact_scope":
        errors.append("project_sync must define additive conditional preprocessing semantics separately")
    expected_layers = {
        "raw_data", "preprocessing_decision", "preprocessing_code", "preprocessing_workbook",
        "preprocessing_matlab_script", "model", "solution_workbook", "result_analysis_workbook", "matlab_script", "figure_bundle", "framework",
    }
    if set(sync.get("artifact_hash_layers", [])) != expected_layers:
        errors.append("project_sync artifact hash layers are incomplete")
    sync_text = read_text(ROOT / "scripts/sync_project.py")
    for token in ("stage_requirements(", "contract_preflight_issues", "_code_hash_mismatches", "analysis_code_sha256", "result_analysis_code", "active_data_hash", "preprocessing_decision", "_mark_paper_fragments_stale"):
        if token not in sync_text:
            errors.append(f"sync_project lacks conditional/two-stage/paper-fragment gate token: {token}")
    workbook = load_structured(ROOT / "core/workbook_schema.yaml") or {}
    runtime = workbook.get("runtime_enforcement", {}) or {}
    if "artifact_checker" in runtime:
        errors.append("workbook schema still references removed artifact_checker")
    for key in ("code_delivery_checker", "returned_workbook_checker", "project_sync", "shared_validator"):
        value = runtime.get(key)
        if not value or not (ROOT / value).is_file():
            errors.append(f"workbook runtime checker missing: {key} -> {value}")
    handoff = workbook.get("matlab_handoff", {}).get("evidence_chain", {}) or {}
    if handoff.get("declared_export_must_exist") is not False:
        errors.append("workbook MATLAB handoff must not require exported figures by default")
    if handoff.get("independent_evidence_file_default") is not False:
        errors.append("workbook MATLAB handoff must not default to an independent evidence file")
    if "figure_evidence.yaml" in str(handoff.get("provenance_record", "")):
        errors.append("workbook MATLAB handoff must not default to figure_evidence.yaml")
    if workbook.get("global_rules", {}).get("empty_worksheet_allowed") is not False:
        errors.append("workbook schema must forbid empty worksheets")
    if "主结果质量门" not in workbook.get("solution_workbook", {}).get("common_required_sheets", {}):
        errors.append("solution workbook must persist the quality gate")
    analysis = workbook.get("result_analysis_workbook", {})
    if not {"分析设计", "结论稳定性汇总"}.issubset(analysis.get("common_required_sheets", {})):
        errors.append("result-analysis workbook lacks required plan/report sheets")
    if "适用性说明" in analysis.get("sheet_schemas", {}):
        errors.append("result-analysis workbook must not use applicability placeholders")


def check_project_state_and_framework(errors: list[str]) -> None:
    schema = load_structured(ROOT / "core/project_state.schema.yaml")
    Draft202012Validator.check_schema(schema)
    example = load_structured(ROOT / "state/project_state.example.yaml")
    for violation in Draft202012Validator(schema).iter_errors(example):
        location = "/".join(map(str, violation.path)) or "<root>"
        errors.append(f"project state example violates schema at {location}: {violation.message}")
    if example.get("semantic_governance_version") != "1.0.0":
        errors.append("project state example must enable semantic governance v1.0.0")
    subproblem = schema["properties"]["subproblems"]["additionalProperties"]
    required = set(subproblem.get("required", []))
    if not {"capabilities", "result_quality_status", "result_analysis_status"}.issubset(required):
        errors.append("project state must require split quality/analysis statuses")
    fields = subproblem.get("properties", {})
    semantic_fields = {
        "depends_on", "problem_contract_status", "semantic_closure_status", "complexity_sanity_status",
        "semantic_revision", "semantic_change_categories", "semantic_hash", "validated_semantic_hash",
    }
    if semantic_fields - set(fields):
        errors.append(f"project state lacks semantic fields: {sorted(semantic_fields - set(fields))}")
    if not {"code", "result_analysis_code", "primary_code_sha256", "analysis_code_sha256", "analysis_evidence_dispositions"}.issubset(fields):
        errors.append("project state must expose both stage-specific code paths/hashes and analysis_evidence_dispositions")
    phases = set(schema["properties"]["project"]["properties"]["current_phase"]["enum"])
    if "result_analysis" not in phases or "data_preprocessing" not in phases:
        errors.append("project state phases must include data_preprocessing and result_analysis")
    if "preprocessing" not in schema["properties"]:
        errors.append("project state must expose preprocessing decision/execution state")
    decision_enum = set(schema["$defs"]["preprocessing_decision"]["enum"])
    if decision_enum != {"not_needed", "question_local", "project_level"}:
        errors.append("project state preprocessing decision enum mismatch")
    if "algorithm" not in set(schema["$defs"]["semantic_change_category"]["enum"]):
        errors.append("project state must preserve algorithm as an existing semantic-change category")
    proposition_id = schema["$defs"]["proposition_entry"]["properties"]["id"].get("pattern")
    if proposition_id != "^P[1-9][0-9]*$":
        errors.append("project state proposition IDs must support justified P5+ entries")
    proposition_count = schema["properties"]["paper_framework"]["properties"]["proposition_count"]
    if "maximum" in proposition_count:
        errors.append("project state proposition_count must not retain a hard maximum")
    framework_props = schema["properties"]["paper_framework"]["properties"]
    if "proposition_budget_status" not in framework_props:
        errors.append("project state must expose proposition budget justification state")
    for field in ("terminology_registry", "numeric_profile", "title_claims", "paper_fragments"):
        if field not in framework_props:
            errors.append(f"project state must expose optional v0.8 paper-framework field: {field}")
    if "algorithm_trace" in framework_props:
        errors.append("v7.8 Algorithm Trace must stay in project memory without introducing a mandatory project-state schema field")
    if "analysis_evidence_entry" not in schema.get("$defs", {}):
        errors.append("project state must define support/modify/reject analysis evidence")

    state_validator = load_module("lint_state_validator", ROOT / "scripts/validate_project_state.py")
    for issue in state_validator.validate_state_payload(example, project_root=ROOT):
        errors.append(f"project state semantic violation: {issue}")
    framework_validator = load_module("lint_framework_validator", ROOT / "scripts/validate_model_paper_framework.py")
    compact = "# 模型论文框架\n只保留当前有效版本\n## 当前有效口径\n## 各问模型与结果\n## 图表证据链\n## 待办与缺口\n"
    full_text = compact + (
        "## 论文整体框架\n"
        "### 命题与证明规划\n"
        "当前计划命题数：0\n"
        "## 综合检验与跨问判断\n"
        "## 同步检查\n"
    )
    if framework_validator.validate_framework_text(compact, mode="compact"):
        errors.append("minimal compact framework must pass")
    if framework_validator.validate_framework_text(full_text, mode="full"):
        errors.append("minimal legacy-compatible full framework must pass")


def check_templates(errors: list[str]) -> None:
    pipeline = read_text(ROOT / "templates/code/hsk_pipeline/main_pipeline.py")
    for token in ("def run_primary_pipeline(", "def run_result_analysis_pipeline(", "assert_primary_quality", "主结果质量门", "分析设计", "结论稳定性汇总"):
        if token not in pipeline:
            errors.append(f"main pipeline lacks token: {token}")
    reader = read_text(ROOT / "templates/matlab/hsk_read_result_workbooks.m")
    for token in ("结果深化分析.xlsx", "books.analysis", "fixedColumns", "expectedHeaders"):
        if token not in reader:
            errors.append(f"MATLAB reader lacks token: {token}")
    plot = read_text(ROOT / "templates/matlab/q1_plot.m")
    for token in ("exact_header_column", "headers ==", "warn_position_drift", "title(ax, figureTitle"):
        if token not in plot:
            errors.append(f"q1_plot.m lacks required token: {token}")
    semantic = read_text(ROOT / "scripts/validate_semantic_governance.py")
    for token in ("problem_contract_status", "semantic_closure_status", "complexity_sanity_status", "semantic_revision", "depends_on", "_dependent_closure", "_mark_paper_fragments_stale"):
        if token not in semantic:
            errors.append(f"semantic governance validator lacks token: {token}")
    validator = read_text(ROOT / "scripts/validate_code_delivery.py")
    for token in ("QUALITY_CONTRACT", "code_quality_findings", "nonblank_lines", "forbidden_import_roots", "结果深化分析.py", "result_analysis_code", "unchanged_accepted", "preprocessing", "数据预处理.py"):
        if token not in validator:
            errors.append(f"code delivery validator lacks quality/conditional-stage token: {token}")
    receipt = read_text(ROOT / "scripts/validate_user_execution.py")
    for token in ("workbook_identity", "工作簿文件名对应", "problem_name与工作簿目录/文件名不一致", "预处理质量门", "project_level"):
        if token not in receipt:
            errors.append(f"returned-workbook validator lacks conditional identity-binding token: {token}")
    audit = read_text(ROOT / "modules/01_problem_audit.md")
    design = read_text(ROOT / "modules/02_model_design.md")
    preprocessing = read_text(ROOT / "modules/03_data_preprocessing.md")
    solve = read_text(ROOT / "modules/03_solve_validate.md")
    analysis = read_text(ROOT / "modules/03_result_analysis.md")
    for token in ("Problem Contract", "禁止假设", "data", "parameter", "model", "result"):
        if token not in audit:
            errors.append(f"problem audit lacks semantic freeze token: {token}")
    for token in ("题面—数学—代码—输出语义闭环", "复杂度合理性复审", "semantic_revision", "review_required", "preprocessing_decision", "Citation Evidence", "Algorithm Trace"):
        if token not in design:
            errors.append(f"model design lacks semantic/writing governance token: {token}")
    if "3--5 个关键假设" in design or "3—5 个关键假设" in design:
        errors.append("model design must not restore a fixed assumption quota")
    for token in ("按必要性而非数量保留", "共享假设", "局部假设"):
        if token not in design:
            errors.append(f"model design lacks scoped assumption token: {token}")
    for token in ("not_needed", "question_local", "project_level", "共享", "五问", "预测填补"):
        if token not in preprocessing:
            errors.append(f"preprocessing module lacks generic decision/necessity token: {token}")
    if "validate_semantic_governance.py" not in solve:
        errors.append("solve module must require semantic governance")
    if "冻结问题X求解.py" not in solve or "问题X结果深化分析.py" not in analysis:
        errors.append("solve/result-analysis modules must enforce frozen primary and separate analysis script")
    for token in ("support", "modify", "reject", "target claim"):
        if token not in analysis:
            errors.append(f"result-analysis module lacks evidence-disposition token: {token}")
    framework = read_text(ROOT / "templates/model/model_paper_framework.md")
    for token in (
        "题意口径（Problem Contract）", "核心公式 Trace", "Algorithm Trace", "Citation Evidence", "Terminology Registry",
        "Numeric Profile", "Title Claim Gate", "Paper Fragment Dependency Map", "深化证据处置",
        "核心模型收束", "算法流程呈现", "semantic revision", "正文引用位置",
    ):
        if token not in framework:
            errors.append(f"model framework lacks current project-memory token: {token}")

    reasoning = load_structured(ROOT / "core/writing_reasoning_contract.yaml") or {}
    if set((reasoning.get("rule_governance") or {}).get("levels", {})) != {"hard", "default", "recommendation"}:
        errors.append("writing reasoning contract must expose Hard/Default/Recommendation levels")
    if (reasoning.get("proposition_governance") or {}).get("automatic_rejection_over_budget") is not False:
        errors.append("writing reasoning contract must not hard-reject proposition count above default budget")
    for key in (
        "citation_evidence", "terminology_governance", "numeric_style_contract", "title_claim_gate",
        "analysis_evidence_disposition", "paragraph_necessity", "paper_fragment_stale_governance", "algorithm_presentation",
    ):
        if key not in reasoning:
            errors.append(f"writing reasoning contract lacks current governance authority: {key}")
    algorithm_reasoning = reasoning.get("algorithm_presentation") or {}
    if algorithm_reasoning.get("modes") != ["not_needed", "stepwise", "pseudocode"]:
        errors.append("writing reasoning contract must expose adaptive algorithm-presentation modes")
    if algorithm_reasoning.get("governance_level") != "default":
        errors.append("algorithm presentation must remain Default, not a universal Hard requirement")
    closure = algorithm_reasoning.get("closure_chain") or []
    if closure != ["model_structure", "algorithm_trace", "paper_algorithm_presentation", "python_implementation", "workbook_result_or_validation"]:
        errors.append("Algorithm Trace closure must connect model, paper algorithm, Python and workbook evidence")
    digits = (((reasoning.get("numeric_style_contract") or {}).get("high_precision_default") or {}).get("preferred_decimal_places_when_not_otherwise_specified"))
    if digits != [6, 7]:
        errors.append("numeric style contract must default scoring-sensitive continuous results to 6--7 decimals when no more specific rule exists")
    if (reasoning.get("model_evaluation") or {}).get("count_relation_required") is not False:
        errors.append("writing reasoning contract must not require strengths to outnumber weaknesses")

    latex_authority = read_text(ROOT / "modules/05_writing/latex.md")
    cleanup = read_text(ROOT / "modules/05_writing/ai_cleanup.md")
    proposition_pack = read_text(ROOT / "packs/artifact/proposition_proof.md")
    algorithm_pack = read_text(ROOT / "packs/artifact/algorithm_flow.md")
    review_module = read_text(ROOT / "modules/06_review_delivery.md")
    review_pack = read_text(ROOT / "packs/artifact/review.md")
    full_submission = read_text(ROOT / "packs/artifact/full_submission.md")
    caption_contract = read_text(ROOT / "templates/writing/caption_explanation.md")
    cumcm = read_text(ROOT / "templates/latex/cumcm/hsk/hsk_main.tex")
    diangong = read_text(ROOT / "templates/latex/diangong/main.tex")
    prose_audit = read_text(ROOT / "scripts/audit_paper_prose.py")
    for token in ("核心模型汇总：自适应而非机械必设", "Citation Evidence", "不检查“优点必须多于缺点”", "Source → Derivation → Destination", "not_needed / stepwise / pseudocode", "packs/artifact/algorithm_flow.md"):
        if token not in latex_authority:
            errors.append(f"LaTeX writing authority lacks current governance token: {token}")
    for token in ("not_needed", "stepwise", "pseudocode", "控制流伪代码版", "分阶段数学步骤版", "不把 Python 源码改写成缩进版论文", "Algorithm Trace 不替代 Formula Trace"):
        if token not in algorithm_pack:
            errors.append(f"algorithm-flow pack lacks adaptive presentation token: {token}")
    for text_name, text in (("review module", review_module), ("review pack", review_pack)):
        for token in ("Algorithm Trace", "stepwise", "pseudocode"):
            if token not in text:
                errors.append(f"{text_name} lacks v7.8.1 Algorithm Trace review token: {token}")
    if "命题数量允许为 0 且最多 4 个" in full_submission:
        errors.append("full submission must not restore a hard four-proposition maximum")
    if "0--4 仅是默认正文阅读预算" not in full_submission or "P5+" not in full_submission:
        errors.append("full submission must preserve proposition default-budget/justification semantics")
    for token in ("Integrity / Hard boundary", "Evidence closure", "Style & Necessity", "Optional machine diagnostics", "Skill 负责原则，脚本负责穷举"):
        if token not in cleanup:
            errors.append(f"AI cleanup lacks v7.7 layered-governance token: {token}")
    if "分段优先，分点按需" not in proposition_pack:
        errors.append("proposition pack must be paragraph-first and number steps only when needed")
    if "显式编号引用" not in caption_contract:
        errors.append("caption contract must require explicit numbered body references")
    for token in (
        "blocking", "review_required", "missing_bib_key", "unused_bib_entries", "standalone_conclusion",
        "missing_ref_label", "discouraged_terminology_alias", "numeric_precision_drift",
    ):
        if token not in prose_audit:
            errors.append(f"paper prose audit lacks v7.7 structural/semantic token: {token}")
    for name, text in (("CUMCM HSK", cumcm), ("Diangong", diangong)):
        if "\n\\section{结论}\n" in text:
            errors.append(f"{name} active template must not contain a default standalone conclusion section")
        if "\\subsection{问题要求}" in text:
            errors.append(f"{name} active template must use 问题提出 instead of 问题要求")
        if "\\subsection{问题提出}" not in text:
            errors.append(f"{name} active template lacks 问题提出")
        if "\\subsection{求解结果}" not in text:
            errors.append(f"{name} active template lacks 求解结果")
    if "\\renewcommand{\\theproposition}{\\arabic{section}.\\arabic{proposition}}" not in cumcm:
        errors.append("CUMCM HSK template must force Arabic proposition numbering")
    if "模板 v6.2.2" in diangong or "\\section{模型假设与符号说明}" in diangong:
        errors.append("active Diangong template still contains stale v6 writing structure")

    for relative in ("SKILL.md", "README.md", "skills/mathmodel-skill/SKILL.md"):
        text = read_text(ROOT / relative)
        if "└─ 图表/" in text or "输出完整版代码、运行配置和说明" in text:
            errors.append(f"active entry still contains obsolete output wording: {relative}")
        if "问题X结果深化分析.py" not in text:
            errors.append(f"active entry lacks independent analysis script: {relative}")
        if "semantic" not in text.lower() and "语义" not in text:
            errors.append(f"active entry lacks semantic governance summary: {relative}")
        if "preprocessing_decision" not in text:
            errors.append(f"active entry lacks conditional preprocessing summary: {relative}")
        if "Algorithm Trace" not in text:
            errors.append(f"active entry lacks v7.8 Algorithm Trace summary: {relative}")
    removed_checker = "hsk_check_" + "artifact.py"
    lint_path = ROOT / "scripts/lint_skill.py"
    for path in active_files():
        if path == lint_path:
            continue
        if removed_checker in read_text(path):
            errors.append(f"active file references removed artifact checker: {path.relative_to(ROOT)}")


def check_syntax(errors: list[str]) -> None:
    for path in active_files():
        try:
            if path.suffix.lower() in {".yaml", ".yml", ".json"}:
                load_structured(path)
            elif path.suffix.lower() == ".py":
                compile(read_text(path), str(path), "exec")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"cannot parse {path.relative_to(ROOT)}: {exc}")


def check_generated(errors: list[str]) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/generate_indexes.py"), "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode:
        errors.append(f"generated indexes or MANIFEST are stale: {(result.stdout + result.stderr).strip()}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-generated", action="store_true")
    args = parser.parse_args()
    errors: list[str] = []
    checks = (
        check_required, check_compatibility_pointers, check_skill_entrypoint_parity, check_root_release_note_hygiene, check_versions, check_bootstrap_and_governance,
        check_taxonomy, check_repository_references, check_router, check_manifest, check_resolver_smoke,
        check_contracts, check_project_state_and_framework, check_templates, check_syntax,
    )
    for check in checks:
        try:
            check(errors)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{check.__name__} failed: {exc}")
    if not args.skip_generated:
        check_generated(errors)
    if errors:
        print("HSK skill lint failed:")
        for item in sorted(set(errors)):
            print("-", item)
        return 1
    print("HSK skill lint passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
