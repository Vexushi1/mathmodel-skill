#!/usr/bin/env python3
"""Validate the active HSK v6.3.4 graph, contracts, semantics and generated files."""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
PACKAGE_VERSION = "6.3.4"
REQUIRED = [
    "SKILL.md", "README.md", "REPOSITORY_INDEX.md", "SKILL_CHANGE_GOVERNANCE.md", "CHANGELOG_V634.md", "CHANGELOG_V633.md", "CHANGELOG_V632.md",
    "PROJECT_INSTRUCTIONS_HSK_V622.md", "HSK_RUNTIME_ROUTER_V622.md", "CHANGELOG_V630.md",
    "core/bootstrap.yaml", "core/hsk_core_policy.md", "core/task_taxonomy.yaml",
    "core/workflow_router.yaml", "core/module_manifest.yaml", "core/output_contract.yaml",
    "core/workbook_schema.yaml", "core/project_state.schema.yaml", "core/compile_profiles.yaml",
    "modules/01_problem_audit.md", "modules/02_model_design.md", "modules/03_solve_validate.md",
    "modules/04_figure_evidence.md", "modules/05_latex_compile_quality.md",
    "modules/05_writing/docx.md", "modules/05_writing/latex.md",
    "modules/05_writing/ai_cleanup.md", "modules/06_review_delivery.md",
    "packs/task/classifier.md", "packs/task/advanced_method_gate.md",
    "packs/artifact/proposition_proof.md", "templates/model/model_paper_framework.md",
    "templates/code/hsk_pipeline/result_io.py", "templates/code/hsk_pipeline/workbook_validation.py", "templates/matlab/q1_plot.m",
    "scripts/resolve_workflow.py", "scripts/sync_project.py",
    "scripts/validate_model_paper_framework.py", "scripts/validate_project_state.py",
    "scripts/score_submission.py", ".github/pull_request_template.md",
    ".github/workflows/ci.yml", ".github/workflows/refresh-generated.yml",
    "LICENSE", "THIRD_PARTY_NOTICES.md",
]
ACTIVE_DIRS = ["core", "modules", "packs", "templates", "scripts", "config", "state", "assets", "agents", "skills", ".codex-plugin", ".github"]
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".py", ".m", ".tex", ".bib"}
VERSION_DOCS = ["SKILL.md", "README.md", "REPOSITORY_INDEX.md", "PROJECT_INSTRUCTIONS_HSK_V622.md", "HSK_RUNTIME_ROUTER_V622.md", "CHANGELOG_V634.md"]
VERSION_CONTRACTS = ["core/bootstrap.yaml", "core/workflow_router.yaml", "core/module_manifest.yaml", "core/output_contract.yaml", "core/project_state.schema.yaml"]


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
    workbook = load_structured(ROOT / "core/workbook_schema.yaml") or {}
    if workbook.get("schema_version") != "2.2.0":
        errors.append("workbook schema version must be 2.2.0")
    if ">=6.3.2" not in str(workbook.get("skill_compatibility", "")):
        errors.append("workbook schema compatibility must start at 6.3.2")


def check_bootstrap_and_governance(errors: list[str]) -> None:
    data = load_structured(ROOT / "core/bootstrap.yaml") or {}
    for key, path in (data.get("authoritative_sources", {}) or {}).items():
        if not path or not (ROOT / path).is_file():
            errors.append(f"bootstrap authoritative source missing: {key} -> {path}")
    if data.get("entrypoints", {}).get("sync") != "python scripts/sync_project.py":
        errors.append("bootstrap must expose sync_project.py")
    maintenance = data.get("repository_maintenance", {})
    expected = {"governance": "SKILL_CHANGE_GOVERNANCE.md", "mandatory_before_write": True, "read_from_ref": "main", "direct_main_write_allowed": False}
    for key, value in expected.items():
        if maintenance.get(key) != value:
            errors.append(f"repository maintenance mismatch: {key}")
    governance = read_text(ROOT / "SKILL_CHANGE_GOVERNANCE.md")
    for token in ("每个新聊天的强制启动顺序", "修改简报", "单一事实源", "一次聊天一个分支", "一个 PR 一个主题", "禁止直接写 main", "生成文件规则", "测试与验收", "完成报告"):
        if token not in governance:
            errors.append(f"governance document lacks section: {token}")
    template = read_text(ROOT / ".github/pull_request_template.md")
    for token in ("修改简报", "治理确认", "SKILL_CHANGE_GOVERNANCE.md", "generate_indexes.py --check"):
        if token not in template:
            errors.append(f"pull request template lacks governance token: {token}")


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
    if len(data.get("legacy_mapping", {})) != 10:
        errors.append("task taxonomy must map all ten legacy packs")


def check_router(errors: list[str]) -> None:
    router = load_structured(ROOT / "core/workflow_router.yaml") or {}
    routes = router.get("routing", {})
    if router.get("bootstrap") != "core/bootstrap.yaml":
        errors.append("router must reference bootstrap")
    if "project_sync" not in routes:
        errors.append("router must define project_sync")
    if router.get("execution_contract", {}).get("formal_delivery_gates") != ["project_sync"]:
        errors.append("formal delivery must declare project_sync gate")
    for name, route in routes.items():
        if route.get("formal_delivery"):
            if not route.get("terminal_outputs"):
                errors.append(f"formal route lacks terminal outputs: {name}")
            if route.get("delivery_scope") not in {"design", "results", "figures", "docx", "latex", "submission"}:
                errors.append(f"formal route lacks valid delivery_scope: {name}")
    if not routes.get("proposition_proof", {}).get("load_proposition_pack"):
        errors.append("proposition route must lazily load proposition pack")
    resolver = read_text(ROOT / "scripts/resolve_workflow.py")
    for token in ("pre_delivery_gates", "available_after_modules", "available_after_plan", "gate_plan"):
        if token not in resolver:
            errors.append(f"resolver lacks gate-closure token: {token}")


def check_manifest(errors: list[str]) -> None:
    manifest = load_structured(ROOT / "core/module_manifest.yaml") or {}
    catalog = set(manifest.get("artifact_catalog", {}))
    external = set(manifest.get("external_artifacts", []))
    known = catalog | external
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
    for name, spec in modules.items():
        for artifact in spec.get("inputs", []):
            if artifact in external:
                continue
            upstream = [producer for producer in producers.get(artifact, []) if rank.get(producer, 999) < rank.get(name, 999)]
            if not upstream:
                errors.append(f"module input lacks upstream producer: {name}:{artifact}")
    gate = manifest.get("utility_gates", {}).get("project_sync", {})
    if gate.get("path") != "scripts/sync_project.py" or not (ROOT / str(gate.get("path", ""))).is_file():
        errors.append("project_sync gate must point to scripts/sync_project.py")
    if set(gate.get("outputs", [])) != {"project_state", "sync_report"}:
        errors.append("project_sync must produce project_state and sync_report")
    source = "core/output_contract.yaml#project_sync.stage_requirements"
    if gate.get("stage_requirements_source") != source:
        errors.append("module manifest project_sync must reference the output-contract stage requirements")
    if "stage_requirements" in gate:
        errors.append("module manifest must not duplicate project_sync.stage_requirements")
    for field in ("inputs", "outputs"):
        unknown = set(gate.get(field, [])) - known
        if unknown:
            errors.append(f"project_sync has uncatalogued {field}: {sorted(unknown)}")
    for profile_name, profile in manifest.get("workflow_profiles", {}).items():
        profile_modules = profile.get("modules", [])
        if profile_modules != sorted(profile_modules, key=lambda item: rank.get(item, 999)):
            errors.append(f"workflow profile module order invalid: {profile_name}")
        available = set(external)
        for module_name in profile_modules:
            spec = modules.get(module_name, {})
            missing = set(spec.get("inputs", [])) - available
            if missing:
                errors.append(f"workflow profile {profile_name} missing inputs before {module_name}: {sorted(missing)}")
            available.update(spec.get("outputs", []))
        for gate_name in profile.get("pre_delivery_gates", []):
            available.update(manifest.get("utility_gates", {}).get(gate_name, {}).get("outputs", []))
        unavailable = set(profile.get("terminal_outputs", [])) - available
        if unavailable:
            errors.append(f"workflow profile {profile_name} has unproducible terminal outputs: {sorted(unavailable)}")


def check_contracts(errors: list[str]) -> None:
    output = load_structured(ROOT / "core/output_contract.yaml") or {}
    modes = output.get("model_paper_framework", {}).get("modes", {})
    compact = set(modes.get("compact", {}).get("required_sections", []))
    full = set(modes.get("full", {}).get("required_sections", []))
    if set(modes) != {"compact", "full"} or not compact or not compact < full:
        errors.append("framework compact/full contract is invalid")
    sync = output.get("project_sync", {})
    if sync.get("role") != "formal_pre_delivery_gate":
        errors.append("project_sync must be a formal pre-delivery gate")
    expected_scopes = {"design", "results", "figures", "docx", "latex", "submission"}
    requirements = sync.get("stage_requirements", {}) or {}
    if set(requirements) != expected_scopes or any(not isinstance(value, list) or not value for value in requirements.values()):
        errors.append("output contract must define non-empty exact stage requirements for every delivery scope")
    if sync.get("stage_requirements_authority") != "core/output_contract.yaml#project_sync.stage_requirements":
        errors.append("output contract must declare itself as the stage-requirements authority")
    if sync.get("stage_requirements_semantics") != "exact_scope":
        errors.append("project_sync stage requirements must use exact_scope semantics")
    sync_text = read_text(ROOT / "scripts/sync_project.py")
    for token in ("stage_requirements(scope, output_contract)", "contract_preflight_issues", "clears_stale"):
        if token not in sync_text:
            errors.append(f"sync_project lacks gate-hardening token: {token}")
    expected_layers = {"data", "model", "solution_workbook", "robustness_workbook", "matlab_script", "figure_bundle", "framework"}
    if set(sync.get("artifact_hash_layers", [])) != expected_layers:
        errors.append("project_sync artifact hash layers are incomplete")
    if output.get("classification_contract", {}).get("authoritative_locations", {}).get("capabilities") != "subproblem.capabilities":
        errors.append("output contract capabilities source is invalid")
    workbook = load_structured(ROOT / "core/workbook_schema.yaml") or {}
    if workbook.get("global_rules", {}).get("empty_worksheet_allowed") is not False:
        errors.append("workbook schema must forbid empty worksheets")
    if not workbook.get("solution_workbook", {}).get("objective_profiles"):
        errors.append("workbook schema lacks objective_profiles")
    if not workbook.get("solution_workbook", {}).get("structure_profiles"):
        errors.append("workbook schema lacks structure_profiles")
    if workbook.get("classification_contract", {}).get("capabilities_source") != "subproblem.capabilities":
        errors.append("workbook capabilities source is invalid")
    if workbook.get("matlab_handoff", {}).get("field_resolution", {}).get("method") != "exact_header_unique_match":
        errors.append("workbook MATLAB handoff must use exact header matching")


def check_project_state_and_framework(errors: list[str]) -> None:
    schema = load_structured(ROOT / "core/project_state.schema.yaml")
    Draft202012Validator.check_schema(schema)
    example = load_structured(ROOT / "state/project_state.example.yaml")
    for violation in Draft202012Validator(schema).iter_errors(example):
        location = "/".join(map(str, violation.path)) or "<root>"
        errors.append(f"project state example violates schema at {location}: {violation.message}")
    classification_required = set(schema.get("$defs", {}).get("classification", {}).get("required", []))
    if "capabilities" in classification_required:
        errors.append("classification.capabilities must not remain required")
    subproblem_contract = schema.get("properties", {}).get("subproblems", {})
    sub_required = set(subproblem_contract.get("additionalProperties", {}).get("required", []))
    if "capabilities" not in sub_required:
        errors.append("subproblem top-level capabilities must be required")
    if subproblem_contract.get("minProperties") != 1:
        errors.append("project state must require at least one subproblem")
    state_validator = load_module("lint_state_validator", ROOT / "scripts/validate_project_state.py")
    for issue in state_validator.validate_state_payload(example, project_root=ROOT):
        errors.append(f"project state semantic violation: {issue}")
    framework_validator = load_module("lint_framework_validator", ROOT / "scripts/validate_model_paper_framework.py")
    compact = "# 模型论文框架\n只保留当前有效版本\n## 当前有效口径\n## 各问模型与结果\n## 图表证据链\n## 待办与缺口\n"
    full_text = compact + "## 论文整体框架\n### 命题与证明规划\n全文命题上限：4\n当前计划命题数：0\n## 综合检验与跨问结论\n## 同步检查\n"
    if framework_validator.validate_framework_text(compact, mode="compact"):
        errors.append("minimal compact framework must pass")
    if framework_validator.validate_framework_text(full_text, mode="full"):
        errors.append("minimal full framework must pass")
    if not framework_validator.validate_framework_text(compact, mode="full"):
        errors.append("compact framework must fail full mode")


def check_templates(errors: list[str]) -> None:
    plot = read_text(ROOT / "templates/matlab/q1_plot.m")
    for token in ("exact_header_column", "headers ==", "warn_position_drift", "title(ax, figureTitle"):
        if token not in plot:
            errors.append(f"q1_plot.m lacks required token: {token}")
    proposition = read_text(ROOT / "packs/artifact/proposition_proof.md")
    if "全文最多 4 个" not in proposition or "数值复核不能替代证明" not in proposition:
        errors.append("proposition proof pack is incomplete")


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
    result = subprocess.run([sys.executable, str(ROOT / "scripts/generate_indexes.py"), "--check"], cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        errors.append(f"generated indexes or MANIFEST are stale: {(result.stdout + result.stderr).strip()}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-generated", action="store_true")
    args = parser.parse_args()
    errors: list[str] = []
    checks = (check_required, check_versions, check_bootstrap_and_governance, check_taxonomy, check_router, check_manifest, check_contracts, check_project_state_and_framework, check_templates, check_syntax)
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
