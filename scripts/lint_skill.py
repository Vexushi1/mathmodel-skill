#!/usr/bin/env python3
"""Validate the active HSK skill graph, schemas, templates and generated indexes."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
EXPECTED_VERSION = "6.2.2"
REQUIRED = [
    "SKILL.md",
    "README.md",
    "REPOSITORY_INDEX.md",
    "PROJECT_INSTRUCTIONS_HSK_V622.md",
    "HSK_RUNTIME_ROUTER_V622.md",
    "CHANGELOG_V622.md",
    "core/hsk_core_policy.md",
    "core/workflow_router.yaml",
    "core/module_manifest.yaml",
    "core/output_contract.yaml",
    "core/workbook_schema.yaml",
    "core/project_state.schema.yaml",
    "core/compile_profiles.yaml",
    "modules/01_problem_audit.md",
    "modules/02_model_design.md",
    "modules/03_solve_validate.md",
    "modules/04_figure_evidence.md",
    "modules/05_latex_compile_quality.md",
    "modules/05_writing/docx.md",
    "modules/05_writing/latex.md",
    "modules/05_writing/ai_cleanup.md",
    "modules/06_review_delivery.md",
    "templates/code/hsk_pipeline/result_io.py",
    "templates/matlab/hsk_find_project_root.m",
    "templates/matlab/hsk_read_result_workbooks.m",
    "templates/matlab/plot_from_workbook.m",
    "templates/latex/cumcm/cumcmthesis/cumcmthesis.cls",
    ".github/workflows/ci.yml",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
]
ACTIVE_DIRS = ["core", "modules", "packs", "templates", "scripts", "config", "state", ".github"]
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".py", ".m", ".tex", ".bib"}
BAD_PATTERNS = {
    r"references/hsk_stage_": "active file depends on obsolete Stage reference",
    r"feedback_layer[1-4]": "active file depends on obsolete feedback layer",
    r"data_output/problem": "obsolete result path",
    r"data_output/": "obsolete result root",
    r"plot_results\(": "obsolete Python plotting entry point",
    r"SEED v0\.1": "obsolete SEED template marker",
    r"Filled by stage 8 output": "obsolete Stage template comment",
}
PATH_PATTERN = re.compile(
    r"(?P<path>(?:core|modules|packs|templates|scripts|state)/[A-Za-z0-9_./{}-]+\.(?:md|yaml|yml|json|py|m|tex|bib))"
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
        "core/workflow_router.yaml",
        "core/module_manifest.yaml",
        "core/output_contract.yaml",
        "core/workbook_schema.yaml",
        "core/project_state.schema.yaml",
        "core/compile_profiles.yaml",
        "config/review_weights.json",
        ".codex-plugin/plugin.json",
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
        suffix = path.suffix.lower()
        try:
            if suffix in {".yaml", ".yml"}:
                load_yaml(path)
            elif suffix == ".json":
                json.loads(read_text(path))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"cannot parse {path.relative_to(ROOT)}: {exc}")


def check_declared_paths(errors: list[str]) -> None:
    for relative in ("core/workflow_router.yaml", "core/module_manifest.yaml"):
        path = ROOT / relative
        data = load_yaml(path)
        for value in iter_strings(data):
            for match in PATH_PATTERN.finditer(value):
                declared = match.group("path").replace("{classified_label}", "classifier")
                if not (ROOT / declared).exists():
                    errors.append(f"declared path does not exist: {relative} -> {declared}")


def check_project_state_schema(errors: list[str]) -> None:
    schema_path = ROOT / "core/project_state.schema.yaml"
    example_path = ROOT / "state/project_state.example.yaml"
    schema = load_yaml(schema_path)
    example = load_yaml(example_path)
    try:
        validator = Draft202012Validator(schema)
        validator.check_schema(schema)
        violations = sorted(validator.iter_errors(example), key=lambda error: list(error.path))
        for violation in violations:
            location = "/".join(str(item) for item in violation.path) or "<root>"
            errors.append(f"project state example violates schema at {location}: {violation.message}")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"invalid project state schema: {exc}")


def check_workbook_schema(errors: list[str]) -> None:
    schema = load_yaml(ROOT / "core/workbook_schema.yaml")
    required_top = {"version", "global_rules", "solution_workbook", "sensitivity_robustness_workbook", "matlab_handoff"}
    missing = required_top - set(schema or {})
    if missing:
        errors.append(f"workbook schema missing keys: {sorted(missing)}")
    if schema.get("global_rules", {}).get("empty_worksheet_allowed") is not False:
        errors.append("workbook schema must forbid empty worksheets")


def check_tex_templates(errors: list[str]) -> None:
    for path in (ROOT / "templates/latex").rglob("*.tex"):
        text = read_text(path)
        if "\\begin{document}" not in text or "\\end{document}" not in text:
            errors.append(f"LaTeX template lacks document boundary: {path.relative_to(ROOT)}")
        if "内部题目要求覆盖检查说明" in text:
            errors.append(f"internal QA leaked into final template: {path.relative_to(ROOT)}")


def check_python_syntax(errors: list[str]) -> None:
    for path in (ROOT / "templates/code").rglob("*.py"):
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
    check_project_state_schema(errors)
    check_workbook_schema(errors)
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
