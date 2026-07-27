#!/usr/bin/env python3
"""Validate the active HSK v6.2.6 skill graph, framework, schemas and templates."""
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
PACKAGE_VERSION = "6.2.6"
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
    "packs/task/advanced_method_gate.md",
    "templates/model/model_paper_framework.md",
    "templates/figure/chart_selection.md",
    "templates/writing/docx_check.md",
    "templates/writing/caption_explanation.md",
    "templates/code/hsk_pipeline/result_io.py",
    "templates/code/hsk_pipeline/matlab_handoff.py",
    "templates/matlab/q1_plot.m",
    "templates/latex/cumcm/cumcmthesis/cumcmthesis.cls",
    "templates/latex/cumcm/hsk/hsk_main.tex",
    "scripts/resolve_workflow.py",
    "scripts/validate_model_paper_framework.py",
    "scripts/validate_project_state.py",
    "scripts/score_submission.py",
    "assets/figure_assets.yaml",
    "assets/nature_figure/README.md",
    ".github/workflows/ci.yml",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
]
TASK_PACKS = [
    "mechanism",
    "optimization",
    "prediction",
    "evaluation",
    "statistics_ml",
    "simulation",
    "spatial",
    "graph_network",
    "scheduling",
    "game_decision",
]
TASK_HEADINGS = [
    "## 1. 进入条件",
    "## 2. 路线比较",
    "## 3. 变量与公式闭环",
    "## 4. 必做验证与输出",
    "## 5. 否决或降级条件",
]
ACTIVE_DIRS = [
    "core",
    "modules",
    "packs",
    "templates",
    "scripts",
    "config",
    "state",
    "assets",
    "agents",
    "skills",
    ".codex-plugin",
    ".github",
]
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
STALE_TITLE_PATTERNS = {
    "图内不重复总标题": "old no-title rule remains",
    "图内不重复放总标题": "old no-title rule remains",
    "图题由 LaTeX 图注承担": "old LaTeX-only title rule remains",
    "图内是否没有重复总标题": "old no-title QA remains",
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
    package_structured = ["core/output_contract.yaml", ".codex-plugin/plugin.json"]
    for relative in package_structured:
        path = ROOT / relative
        data = json.loads(read_text(path)) if path.suffix == ".json" else load_yaml(path)
        version = str((data or {}).get("version", ""))
        if version != PACKAGE_VERSION:
            errors.append(
                f"package version mismatch: {relative} -> {version or '<missing>'}, expected {PACKAGE_VERSION}"
            )

    textual = [
        "SKILL.md",
        "README.md",
        "PROJECT_INSTRUCTIONS_HSK_V622.md",
        "HSK_RUNTIME_ROUTER_V622.md",
        "CHANGELOG_V622.md",
        "REPOSITORY_INDEX.md",
        "scripts/README.md",
    ]
    for relative in textual:
        if PACKAGE_VERSION not in read_text(ROOT / relative):
            errors.append(f"version marker missing: {relative} -> {PACKAGE_VERSION}")

    for relative in [
        "core/workflow_router.yaml",
        "core/module_manifest.yaml",
        "core/workbook_schema.yaml",
        "core/project_state.schema.yaml",
        "core/compile_profiles.yaml",
        "config/review_weights.json",
        "assets/figure_assets.yaml",
    ]:
        path = ROOT / relative
        data = json.loads(read_text(path)) if path.suffix == ".json" else load_yaml(path)
        if not str((data or {}).get("version", "")).strip():
            errors.append(f"schema revision missing: {relative}")


def check_output_contract(errors: list[str]) -> None:
    contract = load_yaml(ROOT / "core/output_contract.yaml") or {}
    question = contract.get("per_question", {})
    if question.get("question_directory") != "结果数据表/问题{中文序号}/":
        errors.append("output contract must use flat 结果数据表/问题X/ directory")
    if question.get("matlab_script") != "q{阿拉伯序号}_plot.m":
        errors.append("output contract must co-locate q{x}_plot.m with workbooks")
    if question.get("figure_directory") != "图表/":
        errors.append("output contract must export to local 图表/")

    framework = contract.get("model_paper_framework", {})
    if contract.get("project_root", {}).get("model_paper_framework") != "模型论文框架.md":
        errors.append("output contract must place 模型论文框架.md in project root")
    if framework.get("template") != "templates/model/model_paper_framework.md":
        errors.append("output contract must reference the active framework template")
    if framework.get("formal_delivery_sync") is not True:
        errors.append("every formal delivery must synchronize 模型论文框架.md")
    required_sections = set(framework.get("required_sections", []))
    if "命题与证明规划" not in required_sections:
        errors.append("model paper framework contract must require 命题与证明规划")

    proposition = contract.get("proposition_contract", {})
    if proposition.get("optional") is not True:
        errors.append("proposition use must be optional")
    if proposition.get("minimum_per_paper") != 0:
        errors.append("minimum proposition count must be 0")
    if proposition.get("maximum_per_paper") != 4:
        errors.append("maximum proposition count must be 4")
    required_fields = set(proposition.get("required_fields", []))
    for field in (
        "proposition_id",
        "assumptions_and_domain",
        "conclusion",
        "proof_level",
        "modeling_effect",
        "failure_boundary",
        "status",
    ):
        if field not in required_fields:
            errors.append(f"proposition contract must require {field}")

    figure = contract.get("matlab_figure_contract", {})
    if figure.get("title_required") is not True:
        errors.append("MATLAB figure title must be required")
    if figure.get("single_panel_title") != "title":
        errors.append("single-panel MATLAB figure must use title")
    if figure.get("multi_panel_title") != "sgtitle":
        errors.append("multi-panel MATLAB figure must use sgtitle")
    if figure.get("keep_title_in_export_by_default") is not True:
        errors.append("MATLAB title must be retained in exports by default")


def check_flat_path_and_matlab_template(errors: list[str]) -> None:
    active_targets = [
        ROOT / "SKILL.md",
        ROOT / "core/hsk_core_policy.md",
        ROOT / "modules/03_solve_validate.md",
        ROOT / "modules/04_figure_evidence.md",
        ROOT / "packs/artifact/code.md",
        ROOT / "packs/artifact/figure.md",
    ]
    stale_paths = [
        "结果数据表/问题X/问题X结果数据/",
        "MATLAB绘图/问题X/q{x}_plot.m",
        "MATLAB绘图/问题一/q1_plot.m",
    ]
    for path in active_targets:
        text = read_text(path)
        for pattern in stale_paths:
            if pattern in text:
                errors.append(f"stale project path remains: {path.relative_to(ROOT)} -> {pattern}")

    plot = read_text(ROOT / "templates/matlab/q1_plot.m")
    for required in [
        'fileparts(scriptPath)',
        'fullfile(resultDir, "问题一求解结果.xlsx")',
        'fullfile(resultDir, "问题一敏感性与鲁棒性结果.xlsx")',
        'fullfile(resultDir, "图表")',
        'figureTitle = "__ACTUAL_FIGURE_TITLE__"',
        "title(ax, figureTitle",
    ]:
        if required not in plot:
            errors.append(f"q1_plot.m lacks required contract: {required}")
    if "hsk_find_project_root" in plot or "hsk_read_result_workbooks" in plot:
        errors.append("q1_plot.m must be self-contained by default")


def check_obsolete_patterns(errors: list[str]) -> None:
    for path in active_files():
        if path.resolve() == Path(__file__).resolve():
            continue
        text = read_text(path)
        for pattern, message in BAD_PATTERNS.items():
            if re.search(pattern, text, flags=re.IGNORECASE):
                errors.append(f"{message}: {path.relative_to(ROOT)} -> {pattern}")
        for phrase, message in STALE_TITLE_PATTERNS.items():
            if phrase in text:
                errors.append(f"{message}: {path.relative_to(ROOT)} -> {phrase}")


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
    for relative in (
        "core/workflow_router.yaml",
        "core/module_manifest.yaml",
        "core/output_contract.yaml",
        "assets/figure_assets.yaml",
    ):
        for value in iter_strings(load_yaml(ROOT / relative)):
            for match in PATH_PATTERN.finditer(value):
                declared = match.group("path")
                if "{" not in declared and not (ROOT / declared).exists():
                    errors.append(f"declared path does not exist: {relative} -> {declared}")


def check_module_artifact_closure(errors: list[str]) -> None:
    manifest = load_yaml(ROOT / "core/module_manifest.yaml") or {}
    modules = manifest.get("modules", {})
    known = set(manifest.get("artifact_catalog", {})) | set(manifest.get("external_artifacts", []))
    for name, module in modules.items():
        for field in ("inputs", "outputs"):
            unknown = sorted(set(module.get(field, [])) - known)
            if unknown:
                errors.append(f"module {name} has uncatalogued {field}: {unknown}")

    profile = manifest.get("workflow_profiles", {}).get("full_workflow", {})
    available = set(manifest.get("external_artifacts", []))
    for name in profile.get("modules", []):
        module = modules.get(name)
        if not module:
            errors.append(f"full_workflow references undefined module: {name}")
            continue
        missing = sorted(set(module.get("inputs", [])) - available)
        if missing:
            errors.append(f"module {name} has no upstream producer for inputs: {missing}")
        available.update(module.get("outputs", []))
    missing_terminal = set(profile.get("terminal_outputs", [])) - available
    if missing_terminal:
        errors.append(f"full_workflow terminal outputs are not produced: {sorted(missing_terminal)}")

    if "model_paper_framework" not in manifest.get("artifact_catalog", {}):
        errors.append("module manifest must catalogue model_paper_framework")
    if "proposition_plan" not in manifest.get("artifact_catalog", {}):
        errors.append("module manifest must catalogue proposition_plan")
    if "proposition_plan" not in modules.get("model_design", {}).get("outputs", []):
        errors.append("model_design must output proposition_plan")
    for name in ("model_design", "solve_validate", "figure_evidence"):
        if "model_paper_framework" not in modules.get(name, {}).get("outputs", []):
            errors.append(f"{name} must output synchronized model_paper_framework")


def check_project_state_schema(errors: list[str]) -> None:
    schema = load_yaml(ROOT / "core/project_state.schema.yaml")
    example = load_yaml(ROOT / "state/project_state.example.yaml")
    try:
        validator = Draft202012Validator(schema)
        validator.check_schema(schema)
        for violation in validator.iter_errors(example):
            location = "/".join(str(item) for item in violation.path) or "<root>"
            errors.append(f"project state example violates schema at {location}: {violation.message}")
        module = load_module("validate_project_state", ROOT / "scripts/validate_project_state.py")
        for issue in module.validate_state_payload(example, project_root=ROOT):
            errors.append(f"project state example violates semantics: {issue}")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"invalid project state schema: {exc}")

    properties = (schema or {}).get("properties", {})
    framework = properties.get("paper_framework", {})
    if not framework:
        errors.append("project state schema must define paper_framework")
    for field in (
        "proposition_limit",
        "proposition_count",
        "proposition_status",
        "propositions",
    ):
        if field not in framework.get("required", []):
            errors.append(f"project state paper_framework must require {field}")
    subproblem = properties.get("subproblems", {}).get("additionalProperties", {})
    subprops = subproblem.get("properties", {})
    for field in (
        "framework_section",
        "result_summary_status",
        "result_summary_anchor",
        "proposition_refs",
    ):
        if field not in subprops:
            errors.append(f"project state subproblem must define {field}")


def check_framework_template(errors: list[str]) -> None:
    path = ROOT / "templates/model/model_paper_framework.md"
    module = load_module(
        "validate_model_paper_framework", ROOT / "scripts/validate_model_paper_framework.py"
    )
    for issue in module.validate_framework_file(path):
        errors.append(f"framework template violation: {issue}")
    text = read_text(path)
    for token in (
        "结果摘要状态",
        "MATLAB 图标题",
        "图表证据链",
        "只保留当前有效",
        "### 命题与证明规划",
        "全文命题上限：4",
        "当前计划命题数：0",
        "证明等级",
        "失效边界",
    ):
        if token not in text:
            errors.append(f"framework template lacks token: {token}")


def check_workbook_schema(errors: list[str]) -> None:
    schema = load_yaml(ROOT / "core/workbook_schema.yaml") or {}
    required_top = {
        "version",
        "global_rules",
        "capability_contract",
        "solution_workbook",
        "sensitivity_robustness_workbook",
        "matlab_handoff",
    }
    if required_top - set(schema):
        errors.append(f"workbook schema missing keys: {sorted(required_top - set(schema))}")
    if schema.get("global_rules", {}).get("empty_worksheet_allowed") is not False:
        errors.append("workbook schema must forbid empty worksheets")
    handoff = schema.get("matlab_handoff", {})
    required_fields = set(handoff.get("required_mapping_fields", []))
    for field in ("matlab_title", "paper_caption", "framework_registry"):
        if field not in required_fields:
            errors.append(f"workbook MATLAB handoff must require {field}")


def check_task_packs(errors: list[str]) -> None:
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


def check_supporting_assets(errors: list[str]) -> None:
    weights = json.loads(read_text(ROOT / "config/review_weights.json"))
    total = sum(float(item["weight"]) for item in weights.get("dimensions", {}).values())
    if abs(total - 1.0) > 1e-9:
        errors.append("review weights must sum to 1")

    registry = load_yaml(ROOT / "assets/figure_assets.yaml") or {}
    for value in iter_strings(registry.get("assets", {})):
        if value.startswith("assets/") and not (ROOT / value).is_file():
            errors.append(f"figure asset registry path missing: {value}")

    profiles = (load_yaml(ROOT / "core/compile_profiles.yaml") or {}).get("profiles", {})
    for name, profile in profiles.items():
        entry = ROOT / str(profile.get("template_directory", "")) / str(
            profile.get("template_main", "")
        )
        if not entry.is_file():
            errors.append(f"compile profile {name} template entry does not exist: {entry}")
        if not str(profile.get("project_main", "")).strip():
            errors.append(f"compile profile {name} lacks project_main")


def check_templates_and_syntax(errors: list[str]) -> None:
    caption = read_text(ROOT / "templates/writing/caption_explanation.md")
    for fixed in ("由图X可知，……。这一结果说明", "由表X可知，……。该结果与"):
        if fixed in caption:
            errors.append(f"fixed AI-like caption sentence remains: {fixed}")

    for path in (ROOT / "templates/latex").rglob("*.tex"):
        text = read_text(path)
        if "\\begin{document}" not in text or "\\end{document}" not in text:
            errors.append(f"LaTeX template lacks document boundary: {path.relative_to(ROOT)}")

    hsk_main = read_text(ROOT / "templates/latex/cumcm/hsk/hsk_main.tex")
    for token in (
        "\\newtheorem{proposition}{命题}[section]",
        "\\newenvironment{hskproof}",
        "证明：",
        "全文命题总数不得超过 4",
    ):
        if token not in hsk_main:
            errors.append(f"CUMCM HSK template lacks proposition contract: {token}")

    for base in (ROOT / "templates/code", ROOT / "scripts"):
        for path in base.rglob("*.py"):
            try:
                compile(read_text(path), str(path), "exec")
            except SyntaxError as exc:
                errors.append(f"Python syntax error: {path.relative_to(ROOT)}:{exc.lineno}: {exc.msg}")


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
    check_required(errors)
    check_versions(errors)
    check_output_contract(errors)
    check_flat_path_and_matlab_template(errors)
    check_obsolete_patterns(errors)
    check_structured_files(errors)
    check_declared_paths(errors)
    check_module_artifact_closure(errors)
    check_project_state_schema(errors)
    check_framework_template(errors)
    check_workbook_schema(errors)
    check_task_packs(errors)
    check_supporting_assets(errors)
    check_templates_and_syntax(errors)
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
