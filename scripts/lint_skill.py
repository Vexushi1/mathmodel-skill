#!/usr/bin/env python3
"""Module-aware entrypoint for the HSK repository lint suite.

The large cross-contract checks live in ``lint_skill_checks.py``. This entrypoint adds
current-source adapters that require repository-wide context, most notably the modular
CUMCM LaTeX template, critical Authority-fragment health, active Markdown-link fragment
health, and current formal MATLAB figure semantics.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import unquote

import lint_skill_checks as checks

ROOT = checks.ROOT
_BOOTSTRAP = checks.load_structured(ROOT / "core/bootstrap.yaml") or {}
checks.PACKAGE_VERSION = str(_BOOTSTRAP.get("skill_version", checks.PACKAGE_VERSION))
_ORIGINAL_READ_TEXT = checks.read_text
_CUMCM_ROOT = ROOT / "templates/latex/cumcm/hsk"
_CUMCM_MAIN = (_CUMCM_ROOT / "hsk_main.tex").resolve()
_CUMCM_LINT_PARTS = (
    _CUMCM_ROOT / "hsk_main.tex",
    _CUMCM_ROOT / "config/preamble.tex",
    _CUMCM_ROOT / "sections/01_problem_statement.tex",
    _CUMCM_ROOT / "sections/06_question1.tex",
)
_CRITICAL_POINTER_REGISTRIES = (
    ROOT / "core/bootstrap.yaml",
    ROOT / "core/output_contract.yaml",
    ROOT / "core/writing_runtime_contract.yaml",
    ROOT / "templates/latex/cumcm/hsk/template_manifest.yaml",
    ROOT / "templates/review/final_review_matrix.yaml",
)
_ROOT_ACTIVE_MARKDOWN = (
    ROOT / "SKILL.md",
    ROOT / "README.md",
    ROOT / "REPOSITORY_INDEX.md",
    ROOT / "PROJECT_INSTRUCTIONS.md",
    ROOT / "RUNTIME_ROUTER.md",
    ROOT / "SKILL_CHANGE_GOVERNANCE.md",
)
_REPO_POINTER_RE = re.compile(
    r"^(?:core|modules|templates|config|packs|scripts)/[^#\s]+#[^\s]+$"
)


def _module_aware_read_text(path: Path) -> str:
    """Present the active CUMCM template as one virtual document to legacy checks.

    The returned text is assembled from actual source modules. No semantic marker is
    injected and no comment-only compatibility token is accepted as evidence.
    """
    resolved = Path(path).resolve()
    if resolved == _CUMCM_MAIN:
        return "\n".join(_ORIGINAL_READ_TEXT(item) for item in _CUMCM_LINT_PARTS)
    return _ORIGINAL_READ_TEXT(path)


checks.read_text = _module_aware_read_text


def _normalize_heading_fragment(value: str) -> str:
    value = re.sub(r"`([^`]*)`", r"\1", value.strip().lower())
    return "".join(char for char in value if char.isalnum() or "\u4e00" <= char <= "\u9fff")


def _markdown_fragment_exists(path: Path, fragment: str) -> bool:
    text = _ORIGINAL_READ_TEXT(path)
    raw_fragment = unquote(fragment.strip())
    if not raw_fragment:
        return False
    escaped = re.escape(raw_fragment)
    if re.search(rf"<(?:a|span)\b[^>]*(?:id|name)=[\"']{escaped}[\"'][^>]*>", text, flags=re.IGNORECASE):
        return True
    if re.search(rf"\{{#{escaped}\}}", text):
        return True
    target = _normalize_heading_fragment(raw_fragment)
    if not target:
        return False
    for match in re.finditer(r"(?m)^#{1,6}\s+(.+?)\s*#*\s*$", text):
        heading = _normalize_heading_fragment(match.group(1))
        if heading == target or heading.endswith(target):
            return True
    return False


def _active_markdown_surfaces() -> list[Path]:
    paths = {path.resolve() for path in _ROOT_ACTIVE_MARKDOWN if path.is_file()}
    paths.update(path.resolve() for path in checks.active_files() if path.suffix.lower() == ".md")
    return sorted(paths)


def _markdown_link_target(origin: Path, target: str) -> tuple[Path, str] | None:
    token = target.strip()
    if token.startswith("<") and token.endswith(">"):
        token = token[1:-1].strip()
    if not token or token.startswith(("http://", "https://", "mailto:", "plugin://")):
        return None
    if " " in token and not token.startswith("#"):
        token = token.split(" ", 1)[0].strip()
    if "#" not in token:
        return None
    path_token, fragment = token.split("#", 1)
    fragment = unquote(fragment.strip())
    if not fragment:
        return None
    if not path_token:
        candidate = origin
    else:
        path_token = unquote(path_token.strip())
        if path_token.startswith("/"):
            candidate = ROOT / path_token.lstrip("/")
        elif path_token.startswith(checks.REPO_PATH_PREFIXES):
            candidate = ROOT / path_token
        else:
            candidate = origin.parent / path_token
    candidate = candidate.resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        return None
    return candidate, fragment


def _check_active_markdown_link_fragments(errors: list[str]) -> None:
    """Validate fragments in real Markdown links on active runtime surfaces.

    Critical machine registries retain their stricter pointer scan. This layer only
    promotes actual Markdown link syntax to fragment validation; inline-code examples
    and free prose containing ``#`` are intentionally ignored.
    """
    for origin in _active_markdown_surfaces():
        text = _ORIGINAL_READ_TEXT(origin)
        for match in checks.MARKDOWN_LINK_RE.finditer(text):
            resolved = _markdown_link_target(origin, match.group(1))
            if resolved is None:
                continue
            target_path, fragment = resolved
            relative_origin = origin.relative_to(ROOT)
            if not target_path.is_file():
                errors.append(
                    f"markdown link target missing: {relative_origin} -> {match.group(1)}"
                )
                continue
            suffix = target_path.suffix.lower()
            if suffix == ".md":
                exists = _markdown_fragment_exists(target_path, fragment)
            elif suffix in {".yaml", ".yml"}:
                exists = _yaml_fragment_exists(target_path, fragment)
            else:
                continue
            if not exists:
                errors.append(
                    f"markdown link fragment missing: {relative_origin} -> {match.group(1)}"
                )


def _resolve_yaml_dotted_nodes(node: object, expression: str) -> list[object]:
    """Resolve a dotted YAML path, expanding ``<placeholder>`` over mapping values."""
    parts = [part for part in expression.split(".") if part]
    if not parts:
        return []
    nodes: list[object] = [node]
    for part in parts:
        next_nodes: list[object] = []
        for current in nodes:
            if part.startswith("<") and part.endswith(">"):
                if isinstance(current, Mapping):
                    next_nodes.extend(current.values())
                continue
            if isinstance(current, Mapping) and part in current:
                next_nodes.append(current[part])
        nodes = next_nodes
        if not nodes:
            return []
    return nodes


def _yaml_json_pointer_exists(node: object, fragment: str) -> bool:
    """Resolve the JSON-Pointer form already used by JSON-schema-style YAML contracts."""
    if not fragment.startswith("/"):
        return False
    current = node
    for raw_part in fragment[1:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, Mapping):
            if part not in current:
                return False
            current = current[part]
            continue
        if isinstance(current, list) and part.isdigit():
            index = int(part)
            if index >= len(current):
                return False
            current = current[index]
            continue
        return False
    return True


def _yaml_descendant_expression_exists(node: object, expression: str) -> bool:
    """Find a dotted expression at or below a previously resolved YAML subtree."""
    if _resolve_yaml_dotted_nodes(node, expression):
        return True
    if isinstance(node, Mapping):
        return any(_yaml_descendant_expression_exists(value, expression) for value in node.values())
    if isinstance(node, list):
        return any(_yaml_descendant_expression_exists(value, expression) for value in node)
    return False


def _yaml_fragment_exists(path: Path, fragment: str) -> bool:
    """Validate active YAML fragments without inventing a second pointer language.

    Supported forms mirror syntax already present in active contracts:

    - ``#top.child`` for an exact dotted path;
    - ``#profiles.<name>.edition_rules`` for a declared dynamic mapping branch;
    - ``#/$defs/dependency_kind`` for JSON Pointer used by schema references;
    - ``#paper_skeleton.ordered_slots+activation`` for a composite semantic pointer,
      meaning that the base subtree exists and the named field is present somewhere
      within that subtree.
    """
    data = checks.load_structured(path)
    raw_fragment = fragment.strip()
    if not raw_fragment:
        return False
    if raw_fragment.startswith("/"):
        return _yaml_json_pointer_exists(data, raw_fragment)

    expressions = [item.strip() for item in raw_fragment.split("+")]
    if not expressions or not expressions[0]:
        return False
    base_nodes = _resolve_yaml_dotted_nodes(data, expressions[0])
    if not base_nodes:
        return False
    for required_descendant in expressions[1:]:
        if not required_descendant:
            return False
        if not any(
            _yaml_descendant_expression_exists(base_node, required_descendant)
            for base_node in base_nodes
        ):
            return False
    return True


def _critical_fragment_exists(reference: str) -> bool:
    token = reference.strip().strip("`<>")
    if "#" not in token:
        return False
    path_token, fragment = token.split("#", 1)
    path = ROOT / path_token
    if not path.is_file() or not fragment:
        return False
    if path.suffix.lower() == ".md":
        return _markdown_fragment_exists(path, fragment)
    if path.suffix.lower() in {".yaml", ".yml"}:
        return _yaml_fragment_exists(path, fragment)
    return False


def _iter_critical_pointer_strings(value: object):
    if isinstance(value, Mapping):
        for child in value.values():
            yield from _iter_critical_pointer_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_critical_pointer_strings(child)
    elif isinstance(value, str):
        token = value.strip().strip("`<>")
        if _REPO_POINTER_RE.fullmatch(token):
            yield token


def _check_critical_pointer_fragments(errors: list[str]) -> None:
    """Validate fragments only on active machine-like pointer registries.

    This intentionally does not scan legacy/history prose. Dynamic YAML placeholders such as
    ``profiles.<name>.edition_rules`` still validate the static prefix and at least one matching
    dynamic branch instead of bypassing fragment checks altogether.
    """
    for registry in _CRITICAL_POINTER_REGISTRIES:
        data = checks.load_structured(registry) or {}
        for reference in _iter_critical_pointer_strings(data):
            path_token, fragment = reference.split("#", 1)
            path = ROOT / path_token
            origin = registry.relative_to(ROOT)
            if not path.is_file():
                errors.append(f"critical repository reference missing: {origin} -> {path_token}")
                continue
            if path.suffix.lower() not in {".md", ".yaml", ".yml"}:
                continue
            if not _critical_fragment_exists(reference):
                errors.append(f"critical repository fragment missing: {origin} -> {reference}")


_original_check_contracts = checks.check_contracts


def _p7_conditional_analysis_contract_errors(output: Mapping[str, object]) -> list[str]:
    """Validate the approved P7 conditional three/five-file lifecycle directly."""
    current: list[str] = []
    per_question = output.get("per_question", {}) or {}
    solver_scripts = per_question.get("solver_scripts") or {}
    python_scripts = solver_scripts.get("python") or {}
    solution = (per_question.get("mandatory_workbooks") or {}).get("solution")
    analysis_workbook = ((per_question.get("conditional_workbooks") or {}).get("result_analysis") or {}).get("path")
    base_expected = [python_scripts.get("primary"), solution, per_question.get("matlab_script")]
    analysis_expected = [python_scripts.get("result_analysis"), analysis_workbook]
    if set(solver_scripts) != {"python", "matlab"}:
        current.append("per-question solver mapping must cover Python and MATLAB")
    for backend, stages in solver_scripts.items():
        if not isinstance(stages, Mapping) or set(stages) != {"primary", "result_analysis"}:
            current.append(f"{backend} solver mapping must define primary and result_analysis")
            continue
        names = [stages["primary"], solution, per_question.get("matlab_script"), stages["result_analysis"], analysis_workbook]
        if any(not isinstance(name, str) or not name for name in names) or len(set(names)) != 5:
            current.append(f"{backend} conditional layout must have disjoint primary/analysis/figure roles")
    if per_question.get("python_scripts") != python_scripts:
        current.append("legacy python_scripts projection must match the Python backend mapping")
    if per_question.get("two_python_stage_policy") != per_question.get("stage_policy"):
        current.append("legacy two_python_stage_policy projection must match stage_policy")
    base = per_question.get("base_default_files") or []
    analysis = per_question.get("analysis_required_additional_files") or []
    if base != base_expected:
        current.append("P7 per-question base layout must be the exact three-file primary/plot set")
    if analysis != analysis_expected:
        current.append("P7 required-analysis extension must be the exact independent 03B code/workbook pair")
    if set(base) & set(analysis) or len(set(base + analysis)) != 5:
        current.append("P7 conditional layout must remain disjoint three-plus-two and total five when analysis is required")

    sync = output.get("project_sync", {}) or {}
    requirements = sync.get("stage_requirements", {}) or {}
    results = requirements.get("results", []) or []
    if "result_analysis_code" in results:
        current.append("P7 results base scope must not unconditionally require result-analysis code")
    if "result_analysis_report" not in results:
        current.append("P7 results scope must retain the auditable result-analysis gate/report state")
    formal = sync.get("formal_state_requirements", {}) or {}
    if formal.get("result_analysis_status") != ["passed", "not_required"]:
        current.append("P7 formal delivery must accept only passed or reasoned not_required analysis status")

    mechanism = output.get("mechanism_drawio_contract", {}) or {}
    if mechanism.get("per_question_five_file_layout_unchanged") is not False:
        current.append("P7 draw.io contract must acknowledge conditional rather than fixed five-file layout")

    manifest = checks.load_structured(ROOT / "core/module_manifest.yaml") or {}
    result_analysis = ((manifest.get("modules") or {}).get("result_analysis") or {})
    if result_analysis.get("conditional") is not True:
        current.append("P7 result-analysis module must remain explicitly conditional")
    return current


def _check_contracts(errors: list[str]) -> None:
    _original_check_contracts(errors)
    output = checks.load_structured(ROOT / "core/output_contract.yaml") or {}
    errors.extend(_p7_conditional_analysis_contract_errors(output))
    policy = output.get("writing_policy", {}) or {}
    expected = {
        "latex_source_layout_default": "modular",
        "latex_project_audit_script": "scripts/audit_latex_project.py",
        "legacy_single_file_latex_supported": True,
    }
    for key, value in expected.items():
        if policy.get(key) != value:
            errors.append(f"writing policy modular-LaTeX contract mismatch: {key} -> {policy.get(key)!r}")
    _check_critical_pointer_fragments(errors)
    _check_active_markdown_link_fragments(errors)


checks.check_contracts = _check_contracts

_original_check_project_state_and_framework = checks.check_project_state_and_framework


def _check_project_state_and_framework(errors: list[str]) -> None:
    _original_check_project_state_and_framework(errors)
    schema = checks.load_structured(ROOT / "core/project_state.schema.yaml") or {}
    fragment = ((schema.get("$defs") or {}).get("paper_fragment_entry") or {})
    source_file = (fragment.get("properties") or {}).get("source_file") or {}
    if source_file.get("type") != "string":
        errors.append("paper fragment schema must expose optional source_file string mapping")
    framework = _ORIGINAL_READ_TEXT(ROOT / "templates/model/model_paper_framework.md")
    if "LaTeX 源码文件（可选）" not in framework:
        errors.append("model-paper framework must expose optional physical LaTeX source mapping")


checks.check_project_state_and_framework = _check_project_state_and_framework

_original_check_templates = checks.check_templates


def _matlab_executable_code(text: str) -> str:
    """Strip ordinary MATLAB comments before checking executable title calls."""
    return "\n".join(line.split("%", 1)[0] for line in text.splitlines())


def _latex_executable_code(text: str) -> str:
    """Strip ordinary LaTeX comments for current active-template safety checks."""
    return "\n".join(line.split("%", 1)[0] for line in text.splitlines())


def _check_templates(errors: list[str]) -> None:
    main_text = _ORIGINAL_READ_TEXT(_CUMCM_ROOT / "hsk_main.tex")
    if "兼容旧版静态合同检查" in main_text:
        errors.append("CUMCM main must not carry comment-only compatibility markers for lint")
    if "\\subsection{问题提出}" in main_text or "\\subsection{求解结果}" in main_text:
        errors.append("CUMCM main must remain orchestration-only; semantic section tokens belong in child modules")

    _original_check_templates(errors)

    plotting = _ORIGINAL_READ_TEXT(ROOT / "templates/matlab/q1_plot.m")
    code = _matlab_executable_code(plotting)
    if re.search(r"\b(?:title|sgtitle)\s*\(", code, flags=re.IGNORECASE):
        errors.append("q1_plot.m formal template must not contain executable overall title/sgtitle")
    for token in (
        "LaTeX/DOCX caption",
        "Scientific Figure Synthesis Gate",
        "Publication Rendering Grammar",
        'seriesColors = zeros(0, 3)',
        'apply_publication_style(fig, style)',
        'grid(ax, gridMode)',
    ):
        if token not in plotting:
            errors.append(f"q1_plot.m lacks current scientific Figure semantic token: {token}")

    data_process = _ORIGINAL_READ_TEXT(ROOT / "templates/matlab/data_process.m")
    process_code = _matlab_executable_code(data_process)
    if re.search(r"\b(?:title|sgtitle)\s*\(", process_code, flags=re.IGNORECASE):
        errors.append("data_process.m formal template must not contain executable overall title/sgtitle")
    for token in (
        "LaTeX/DOCX caption",
        "Scientific Figure Synthesis Gate",
        "Publication Rendering Grammar",
        'seriesColors = zeros(0, 3)',
        'apply_publication_style(fig, style)',
        'grid(ax, gridMode)',
    ):
        if token not in data_process:
            errors.append(f"data_process.m lacks current scientific Figure semantic token: {token}")

    style = _ORIGINAL_READ_TEXT(ROOT / "templates/matlab/hsk_apply_scientific_style.m")
    profile = _ORIGINAL_READ_TEXT(ROOT / "templates/matlab/hsk_publication_profile.m")
    for relative, text in (("style", style), ("profile", profile)):
        if 'profile (1,1) string = ""' not in text:
            errors.append(f"{relative} helper must not select an implicit palette")
    for token in (
        "spec = hsk_publication_profile(profile)",
        "palette = spec.palette",
        "listfonts",
        "Noto Sans CJK SC",
    ):
        if token not in style:
            errors.append(f"scientific style helper lacks profile-application token: {token}")
    if 'case "journal_balanced"' in style or 'case "monochrome_print"' in style:
        errors.append("scientific style helper must not duplicate publication profile registry cases")
    for token in (
        "palette.brightBlue = [20, 120, 255] / 255",
        "palette.vividRed = [240, 68, 68] / 255",
        "palette.brightGreen = [22, 179, 100] / 255",
        'case "competition_high_contrast"',
        'case "journal_balanced"',
        'case "monochrome_print"',
        "palette.primary",
        "palette.series",
        "高对比、中高饱和",
    ):
        if token not in profile:
            errors.append(f"publication profile registry lacks explicit compatibility token: {token}")

    for name, relative in (
        ("Diangong", "templates/latex/diangong/main.tex"),
        ("MCM/ICM", "templates/latex/mcm/main.tex"),
    ):
        text = _ORIGINAL_READ_TEXT(ROOT / relative)
        first_line = text.splitlines()[0] if text.splitlines() else ""
        if re.search(r"\bv\d+\.\d+(?:\.\d+)?\b", first_line, flags=re.IGNORECASE):
            errors.append(f"active {name} template header ambiguously carries an old release label")
        if "current Skill release" not in text or "core/bootstrap.yaml" not in text:
            errors.append(f"active {name} template must distinguish template lineage from current Skill release")

    diangong = _ORIGINAL_READ_TEXT(ROOT / "templates/latex/diangong/main.tex")
    active_diangong = _latex_executable_code(diangong)
    if r"\section*{AI工具使用声明}" in active_diangong:
        errors.append("Diangong generic template must not emit an unconditional AI-use disclosure")
    if "本参赛队在论文撰写、程序开发与结果整理过程中合理使用了 AI" in active_diangong:
        errors.append("Diangong generic template must not fabricate project AI-use facts")

    ai_scaffold = _ORIGINAL_READ_TEXT(_CUMCM_ROOT / "sections/10_ai_tool_statement.tex")
    if "本参赛队在论文撰写、程序开发与结果整理过程中合理使用了 AI" in ai_scaffold:
        errors.append("CUMCM AI-disclosure scaffold must not fabricate project AI-use facts")
    if r"\input{sections/10_ai_tool_statement}" in _latex_executable_code(main_text):
        errors.append("CUMCM generic main must keep the AI-disclosure slot inactive by default")


checks.check_templates = _check_templates


if __name__ == "__main__":
    raise SystemExit(checks.main())
