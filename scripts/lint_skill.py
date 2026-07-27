#!/usr/bin/env python3
"""Validate the active HSK v6.3 skill graph, schemas, router and templates."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
PACKAGE_VERSION = "6.3.0"
REQUIRED = [
    "SKILL.md", "README.md", "REPOSITORY_INDEX.md", "SKILL_CHANGE_GOVERNANCE.md",
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
    "templates/code/hsk_pipeline/result_io.py", "templates/matlab/q1_plot.m",
    "scripts/resolve_workflow.py", "scripts/sync_project.py",
    "scripts/validate_model_paper_framework.py", "scripts/validate_project_state.py",
    "scripts/score_submission.py", ".github/pull_request_template.md",
    ".github/workflows/ci.yml", ".github/workflows/refresh-generated.yml",
    "LICENSE", "THIRD_PARTY_NOTICES.md",
]
ACTIVE_DIRS = ["core", "modules", "packs", "templates", "scripts", "config", "state", "assets", "agents", "skills", ".codex-plugin", ".github"]
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".py", ".m", ".tex", ".bib"}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="strict")


def load_structured(path: Path) -> Any:
    return json.loads(read_text(path)) if path.suffix == ".json" else yaml.safe_load(read_text(path))


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
    for relative in ["SKILL.md", "README.md", "REPOSITORY_INDEX.md", "PROJECT_INSTRUCTIONS_HSK_V622.md", "HSK_RUNTIME_ROUTER_V622.md", "CHANGELOG_V630.md"]:
        if PACKAGE_VERSION not in read_text(ROOT / relative):
            errors.append(f"version marker missing: {relative}")
    for relative in ["core/bootstrap.yaml", "core/workflow_router.yaml", "core/module_manifest.yaml", "core/output_contract.yaml", "core/project_state.schema.yaml"]:
        payload = load_structured(ROOT / relative) or {}
        value = payload.get("skill_version", payload.get("version"))
        if str(value) != PACKAGE_VERSION:
            errors.append(f"version mismatch: {relative} -> {value}")
    plugin = load_structured(ROOT / ".codex-plugin/plugin.json") or {}
    if plugin.get("version") != PACKAGE_VERSION:
        errors.append("plugin version mismatch")
    workbook = load_structured(ROOT / "core/workbook_schema.yaml") or {}
    if not workbook.get("schema_version") or not workbook.get("skill_compatibility"):
        errors.append("workbook schema must use independent schema_version and skill_compatibility")


def check_bootstrap(errors: list[str]) -> None:
    data = load_structured(ROOT / "core/bootstrap.yaml") or {}
    sources = data.get("authoritative_sources", {})
    for key in ("global_policy", "routing", "artifact_graph", "task_taxonomy", "project_state", "workbook", "output"):
        path = sources.get(key)
        if not path or not (ROOT / path).is_file():
            errors.append(f"bootstrap authoritative source missing: {key} -> {path}")
    if data.get("entrypoints", {}).get("sync") != "python scripts/sync_project.py":
        errors.append("bootstrap must expose sync_project.py")
    maintenance = data.get("repository_maintenance", {})
    if maintenance.get("governance") != "SKILL_CHANGE_GOVERNANCE.md":
        errors.append("bootstrap must reference SKILL_CHANGE_GOVERNANCE.md")
    if maintenance.get("mandatory_before_write") is not True:
        errors.append("repository governance must be mandatory before write")
    if maintenance.get("read_from_ref") != "main":
        errors.append("repository governance must be read from main")
    if maintenance.get("direct_main_write_allowed") is not False:
        errors.append("bootstrap must forbid direct main writes")


def check_governance(errors: list[str]) -> None:
    governance = read_text(ROOT / "SKILL_CHANGE_GOVERNANCE.md")
    for token in (
        "每个新聊天的强制启动顺序",
        "修改简报",
        "单一事实源",
        "一次聊天一个分支",
        "一个 PR 一个主题",
        "禁止直接写 main",
        "生成文件规则",
        "测试与验收",
        "完成报告",
    ):
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
    for capability in ("requires_out_of_sample_validation", "requires_uncertainty_quantification", "requires_leakage_check", "requires_calibration_check"):
        if capability not in data.get("capabilities", {}):
            errors.append(f"task taxonomy lacks capability: {capability}")
    if len(data.get("legacy_mapping", {})) != 10:
        errors.append("task taxonomy must map all ten legacy packs")


def check_router(errors: list[str]) -> None:
    router = load_structured(ROOT / "core/workflow_router.yaml") or {}
    if router.get("bootstrap") != "core/bootstrap.yaml":
        errors.append("router must reference bootstrap")
    routes = router.get("routing", {})
    if "project_sync" not in routes:
        errors.append("router must define project_sync")
    for name, route in routes.items():
        if route.get("formal_delivery") and not route.get("terminal_outputs"):
            errors.append(f"formal route lacks terminal outputs: {name}")
    if not routes.get("proposition_proof", {}).get("load_proposition_pack"):
        errors.append("proposition route must lazily load proposition pack")


def check_manifest(errors: list[str]) -> None:
    manifest = load_structured(ROOT / "core/module_manifest.yaml") or {}
    catalog = set(manifest.get("artifact_catalog", {}))
    external = set(manifest.get("external_artifacts", []))
    known = catalog | external
    if "sync_report" not in catalog:
        errors.append("manifest must catalogue sync_report")
    if "project_sync" not in manifest.get("utility_gates", {}):
        errors.append("manifest must define project_sync utility gate")
    for name, spec in manifest.get("modules", {}).items():
        for field in ("inputs", "outputs"):
            unknown = set(spec.get(field, [])) - known
            if unknown:
                errors.append(f"module {name} has uncatalogued {field}: {sorted(unknown)}")
        path = spec.get("path")
        if path and not (ROOT / path).is_file():
            errors.append(f"module path missing: {name} -> {path}")


def check_contracts(errors: list[str]) -> None:
    output = load_structured(ROOT / "core/output_contract.yaml") or {}
    if output.get("project_root", {}).get("sync_report") != "sync_report.yaml":
        errors.append("output contract must place sync_report.yaml in project root")
    if set(output.get("model_paper_framework", {}).get("modes", {})) != {"compact", "full"}:
        errors.append("framework contract must define compact and full modes")
    if output.get("project_sync", {}).get("script") != "scripts/sync_project.py":
        errors.append("output contract must reference sync_project.py")
    if output.get("matlab_figure_contract", {}).get("field_resolution") != "exact_header_unique_match":
        errors.append("MATLAB field resolution must use exact unique headers")
    workbook = load_structured(ROOT / "core/workbook_schema.yaml") or {}
    if workbook.get("global_rules", {}).get("empty_worksheet_allowed") is not False:
        errors.append("workbook schema must forbid empty worksheets")
    allowed = set(workbook.get("capability_contract", {}).get("allowed", []))
    for capability in ("requires_out_of_sample_validation", "requires_uncertainty_quantification", "requires_leakage_check", "requires_calibration_check", "requires_identifiability_check"):
        if capability not in allowed:
            errors.append(f"workbook schema lacks capability: {capability}")
    if workbook.get("matlab_handoff", {}).get("field_resolution", {}).get("method") != "exact_header_unique_match":
        errors.append("workbook MATLAB handoff must use exact header matching")


def check_project_state(errors: list[str]) -> None:
    schema = load_structured(ROOT / "core/project_state.schema.yaml")
    Draft202012Validator.check_schema(schema)
    example = load_structured(ROOT / "state/project_state.example.yaml")
    for violation in Draft202012Validator(schema).iter_errors(example):
        location = "/".join(map(str, violation.path)) or "<root>"
        errors.append(f"project state example violates schema at {location}: {violation.message}")
    defs = schema.get("$defs", {})
    if "classification" not in defs or "objective" not in defs or "structure" not in defs:
        errors.append("project state schema lacks v6.3 classification definitions")


def check_templates(errors: list[str]) -> None:
    plot = read_text(ROOT / "templates/matlab/q1_plot.m")
    for token in ("exact_header_column", "headers ==", "warn_position_drift", "title(ax, figureTitle"):
        if token not in plot:
            errors.append(f"q1_plot.m lacks v6.3 token: {token}")
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
    for check in (
        check_required,
        check_versions,
        check_bootstrap,
        check_governance,
        check_taxonomy,
        check_router,
        check_manifest,
        check_contracts,
        check_project_state,
        check_templates,
        check_syntax,
    ):
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