#!/usr/bin/env python3
"""Validate the active HSK skill graph, schemas, templates and generated indexes."""
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
EXPECTED_VERSION = "6.2.3"
REQUIRED = [
    "SKILL.md", "README.md", "REPOSITORY_INDEX.md", "PROJECT_INSTRUCTIONS_HSK_V622.md",
    "HSK_RUNTIME_ROUTER_V622.md", "CHANGELOG_V622.md", "core/hsk_core_policy.md",
    "core/workflow_router.yaml", "core/module_manifest.yaml", "core/output_contract.yaml",
    "core/workbook_schema.yaml", "core/project_state.schema.yaml", "core/compile_profiles.yaml",
    "modules/01_problem_audit.md", "modules/02_model_design.md", "modules/03_solve_validate.md",
    "modules/04_figure_evidence.md", "modules/05_latex_compile_quality.md",
    "modules/05_writing/docx.md", "modules/05_writing/latex.md",
    "modules/05_writing/ai_cleanup.md", "modules/06_review_delivery.md",
    "packs/task/advanced_method_gate.md", "templates/figure/chart_selection.md",
    "templates/writing/docx_check.md", "templates/writing/caption_explanation.md",
    "templates/code/hsk_pipeline/result_io.py", "templates/matlab/hsk_find_project_root.m",
    "templates/matlab/hsk_read_result_workbooks.m", "templates/matlab/q1_plot.m",
    "templates/latex/cumcm/cumcmthesis/cumcmthesis.cls", "scripts/resolve_workflow.py",
    "scripts/validate_project_state.py", "scripts/score_submission.py",
    "assets/figure_assets.yaml", "assets/nature_figure/README.md",
    ".github/workflows/ci.yml", "LICENSE", "THIRD_PARTY_NOTICES.md",
]
TASK_PACKS = [
    "mechanism", "optimization", "prediction", "evaluation", "statistics_ml",
    "simulation", "spatial", "graph_network", "scheduling", "game_decision",
]
TASK_HEADINGS = [
    "## 1. 进入条件", "## 2. 路线比较", "## 3. 变量与公式闭环",
    "## 4. 必做验证与输出", "## 5. 否决或降级条件",
]
ACTIVE_DIRS = ["core", "modules", "packs", "templates", "scripts", "config", "state", "assets", ".github"]
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".py", ".m", ".tex", ".bib"}
BAD_PATTERNS = {
    r"references/hsk_stage_": "active file depends on obsolete Stage reference",
    r"feedback_layer[1-4]": "active file depends on obsolete feedback layer",
    r"data_output/problem": "obsolete result path",
    r"data_output/": "obsolete result root",
    r"plot_results\(": "obsolete Python plotting entry point",
    r"SEED v0\.1": "obsolete SEED template marker",
    r"Filled by stage 8 output": "obsolete Stage template comment",
    r"templates/writing/docx_(?:draft|layout)_check\.md": "obsolete duplicate DOCX checklist reference",
}
PATH_PATTERN = re.compile(
    r"(?P<path>(?:assets|core|modules|packs|templates|scripts|state)/[A-Za-z0-9_./{}-]+\.(?:md|yaml|yml|json|py|m|tex|bib|png))"
)


def active_files() -> Iterable[Path]:
    for top in ACTIVE_DIRS:
        base = ROOT / top
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
                yield path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="strict")


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(read_text(path))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from iter_strings(key)
            yield from iter_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item)


def check_required(errors: list[str]) -> None:
    for relative in REQUIRED:
        if not (ROOT / relative).exists():
            errors.append(f"missing required: {relative}")


def check_versions(errors: list[str]) -> None:
    structured = [
        "core/workflow_router.yaml", "core/module_manifest.yaml", "core/output_contract.yaml",
        "core/workbook_schema.yaml", "core/project_state.schema.yaml", "core/compile_profiles.yaml",
        "config/review_weights.json", "assets/figure_assets.yaml", ".codex-plugin/plugin.json",
    ]
    for relative in structured:
        path = ROOT / relative
        if not path.is_file():
            continue
        data = json.loads(read_text(path)) if path.suffix == ".json" else load_yaml(path)
        version = str((data or {}).get("version", ""))
        if version != EXPECTED_VERSION:
            errors.append(f"version mismatch: {relative} -> {version or '<missing>'}, expected {EXPECTED_VERSION}")

    textual = ["SKILL.md", "README.md", "PROJECT_INSTRUCTIONS_HSK_V622.md", "HSK_RUNTIME_ROUTER_V622.md", "CHANGELOG_V622.md"]
    for relative in textual:
        path = ROOT / relative
        if path.is_file() and EXPECTED_VERSION not in read_text(path):
            errors.append(f"version marker missing: {relative} -> {EXPECTED_VERSION}")


def check_obsolete_patterns(errors: list[str]) -> None:
    for path in active_files():
        if path.resolve() == Path(__file__).resolve():
            continue
        text = read_text(path)
        for pattern, message in BAD_PATTERNS.items():
            if re.search(pattern, text, flags=re.IGNORECASE):
                errors.append(f"{message}: {path.relative_to(ROOT)} -> {pattern}")


def check_structured_files(errors: list[str]) -> None:
    for path in active_files():
        try:
            if path.suffix.lower() in {".yaml", ".yml"}:
                load_yaml(path)
            elif path.suffix.lower() == ".json":
                json.loads(read_text(path))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"cannot parse {path.relative_to(ROOT)}: {exc}")


def check_declared_paths(errors: list[str]) -> None:
    for relative in ("core/workflow_router.yaml", "core/module_manifest.yaml", "assets/figure_assets.yaml"):
        data = load_yaml(ROOT / relative)
        for value in iter_strings(data):
            for match in PATH_PATTERN.finditer(value):
                declared = match.group("path")
                if "{" in declared:
                    continue
                if not (ROOT / declared).exists():
                    errors.append(f"declared path does not exist: {relative} -> {declared}")


def check_module_artifact_closure(errors: list[str]) -> None:
    manifest = load_yaml(ROOT / "core/module_manifest.yaml") or {}
    modules = manifest.get("modules", {})
    catalog = set(manifest.get("artifact_catalog", {}))
    external = set(manifest.get("external_artifacts", []))
    known = catalog | external
    for name, module in modules.items():
        for field in ("inputs", "outputs"):
            unknown = sorted(set(module.get(field, [])) - known)
            if unknown:
                errors.append(f"module {name} has uncatalogued {field}: {unknown}")

    profile = manifest.get("workflow_profiles", {}).get("full_workflow", {})
    available = set(external)
    for name in profile.get("modules", []):
        module = modules.get(name)
        if not module:
            errors.append(f"full_workflow references undefined module: {name}")
            continue
        missing = sorted(set(module.get("inputs", [])) - available)
        if missing:
            errors.append(f"module {name} has no upstream producer for inputs: {missing}")
        available.update(module.get("outputs", []))
    terminal = set(profile.get("terminal_outputs", []))
    if not terminal.issubset(available):
        errors.append(f"full_workflow terminal outputs are not produced: {sorted(terminal - available)}")


def check_project_state_schema(errors: list[str]) -> None:
    schema_path = ROOT / "core/project_state.schema.yaml"
    example_path = ROOT / "state/project_state.example.yaml"
    schema = load_yaml(schema_path)
    example = load_yaml(example_path)
    try:
        validator = Draft202012Validator(schema)
        validator.check_schema(schema)
        for violation in sorted(validator.iter_errors(example), key=lambda error: list(error.path)):
            location = "/".join(str(item) for item in violation.path) or "<root>"
            errors.append(f"project state example violates schema at {location}: {violation.message}")
        state_module = load_module("validate_project_state", ROOT / "scripts/validate_project_state.py")
        for issue in state_module.validate_state_payload(example, project_root=ROOT):
            errors.append(f"project state example violates semantics: {issue}")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"invalid project state schema: {exc}")


def check_workbook_schema(errors: list[str]) -> None:
    schema = load_yaml(ROOT / "core/workbook_schema.yaml") or {}
    required_top = {
        "version", "global_rules", "capability_contract", "solution_workbook",
        "sensitivity_robustness_workbook", "matlab_handoff",
    }
    missing = required_top - set(schema)
    if missing:
        errors.append(f"workbook schema missing keys: {sorted(missing)}")
    if schema.get("global_rules", {}).get("empty_worksheet_allowed") is not False:
        errors.append("workbook schema must forbid empty worksheets")
    sheet_names = set(schema.get("solution_workbook", {}).get("common_recommended_sheets", {}))
    for capability, required in schema.get("capability_contract", {}).get("required_sheets", {}).items():
        missing_sheets = sorted(set(required) - sheet_names)
        if missing_sheets:
            errors.append(f"capability {capability} requires undefined sheets: {missing_sheets}")


def check_task_pack_contract(errors: list[str]) -> None:
    for name in TASK_PACKS:
        path = ROOT / "packs" / "task" / f"{name}.md"
        if not path.is_file():
            errors.append(f"missing task pack: {path.relative_to(ROOT)}")
            continue
        text = read_text(path)
        for heading in TASK_HEADINGS:
            if heading not in text:
                errors.append(f"task pack missing heading: {path.relative_to(ROOT)} -> {heading}")
        if len(text.splitlines()) < 20:
            errors.append(f"task pack is too thin for execution: {path.relative_to(ROOT)}")


def check_review_weights(errors: list[str]) -> None:
    config = json.loads(read_text(ROOT / "config/review_weights.json"))
    weights = [float(item["weight"]) for item in config.get("dimensions", {}).values()]
    if abs(sum(weights) - 1.0) > 1e-9:
        errors.append("review weights must sum to 1")
    if config.get("status") == "active" and not (ROOT / "scripts/score_submission.py").is_file():
        errors.append("active review weights have no executable scorer")


def check_figure_assets(errors: list[str]) -> None:
    registry = load_yaml(ROOT / "assets/figure_assets.yaml") or {}
    for value in iter_strings(registry.get("assets", {})):
        if value.startswith("assets/") and not (ROOT / value).is_file():
            errors.append(f"figure asset registry path missing: {value}")
    chart = read_text(ROOT / "templates/figure/chart_selection.md")
    if "assets/figure_assets.yaml" not in chart:
        errors.append("figure asset registry is not connected to chart selection")


def check_compile_profiles(errors: list[str]) -> None:
    profiles = (load_yaml(ROOT / "core/compile_profiles.yaml") or {}).get("profiles", {})
    for name, profile in profiles.items():
        directory = ROOT / str(profile.get("template_directory", ""))
        template_main = directory / str(profile.get("template_main", ""))
        if not directory.is_dir() or not template_main.is_file():
            errors.append(f"compile profile {name} template entry does not exist: {template_main.relative_to(ROOT)}")
        if not profile.get("project_main"):
            errors.append(f"compile profile {name} lacks project_main")


def check_writing_templates(errors: list[str]) -> None:
    for obsolete in ("docx_draft_check.md", "docx_layout_check.md"):
        path = ROOT / "templates" / "writing" / obsolete
        if path.exists():
            errors.append(f"superseded DOCX checklist still exists: {path.relative_to(ROOT)}")
    caption = read_text(ROOT / "templates/writing/caption_explanation.md")
    for fixed in ("由图X可知，……。这一结果说明", "由表X可知，……。该结果与"):
        if fixed in caption:
            errors.append(f"fixed AI-like caption sentence remains: {fixed}")


def check_tex_templates(errors: list[str]) -> None:
    for path in (ROOT / "templates/latex").rglob("*.tex"):
        text = read_text(path)
        if "\\begin{document}" not in text or "\\end{document}" not in text:
            errors.append(f"LaTeX template lacks document boundary: {path.relative_to(ROOT)}")
        if "内部题目要求覆盖检查说明" in text:
            errors.append(f"internal QA leaked into final template: {path.relative_to(ROOT)}")


def check_python_syntax(errors: list[str]) -> None:
    for base in (ROOT / "templates/code", ROOT / "scripts"):
        for path in base.rglob("*.py"):
            try:
                compile(read_text(path), str(path), "exec")
            except SyntaxError as exc:
                errors.append(f"Python syntax error: {path.relative_to(ROOT)}:{exc.lineno}: {exc.msg}")


def check_generated_indexes(errors: list[str]) -> None:
    script = ROOT / "scripts/generate_indexes.py"
    result = subprocess.run([sys.executable, str(script), "--check"], cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        detail = (result.stdout + result.stderr).strip()
        errors.append(f"generated indexes or MANIFEST are stale: {detail}")
    index = ROOT / "HSK_SKILL_FILE_INDEX_V622.md"
    if index.is_file():
        legacy_entries = [line for line in read_text(index).splitlines() if "`legacy/" in line and "legacy/README.md" not in line]
        if legacy_entries:
            errors.append("active skill index contains archived legacy entries")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-generated", action="store_true", help="skip generated index and MANIFEST consistency check")
    args = parser.parse_args()
    errors: list[str] = []
    check_required(errors)
    check_versions(errors)
    check_obsolete_patterns(errors)
    check_structured_files(errors)
    check_declared_paths(errors)
    check_module_artifact_closure(errors)
    check_project_state_schema(errors)
    check_workbook_schema(errors)
    check_task_pack_contract(errors)
    check_review_weights(errors)
    check_figure_assets(errors)
    check_compile_profiles(errors)
    check_writing_templates(errors)
    check_tex_templates(errors)
    check_python_syntax(errors)
    if not args.skip_generated:
        check_generated_indexes(errors)
    if errors:
        print("HSK skill lint failed:")
        for item in sorted(set(errors)):
            print("-", item)
        return 1
    print("HSK skill lint passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
