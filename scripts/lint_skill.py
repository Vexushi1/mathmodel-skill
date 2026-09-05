#!/usr/bin/env python3
"""Module-aware entrypoint for the HSK repository lint suite.

The large cross-contract checks live in ``lint_skill_checks.py``. This entrypoint adds
current-source adapters that require repository-wide context, most notably the modular
CUMCM LaTeX template, critical Authority-fragment health, and current formal MATLAB figure semantics.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path

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
    raw_fragment = fragment.strip()
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


def _yaml_fragment_exists(path: Path, fragment: str) -> bool:
    data = checks.load_structured(path)
    parts = [part for part in fragment.split(".") if part]
    if not parts:
        return False

    def descend(node: object, index: int) -> bool:
        if index >= len(parts):
            return True
        part = parts[index]
        if part.startswith("<") and part.endswith(">"):
            if not isinstance(node, Mapping) or not node:
                return False
            return any(descend(value, index + 1) for value in node.values())
        if not isinstance(node, Mapping) or part not in node:
            return False
        return descend(node[part], index + 1)

    return descend(data, 0)


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


def _check_contracts(errors: list[str]) -> None:
    _original_check_contracts(errors)
    output = checks.load_structured(ROOT / "core/output_contract.yaml") or {}
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


def _check_templates(errors: list[str]) -> None:
    main_text = _ORIGINAL_READ_TEXT(_CUMCM_ROOT / "hsk_main.tex")
    if "兼容旧版静态合同检查" in main_text:
        errors.append("CUMCM main must not carry comment-only compatibility markers for lint")
    if "\\subsection{问题提出}" in main_text or "\\subsection{求解结果}" in main_text:
        errors.append("CUMCM main must remain orchestration-only; semantic section tokens belong in child modules")

    _original_check_templates(errors)

    # lint_skill_checks.py keeps a historical v7.4-era positive-title token for
    # compatibility. Current formal Figure semantics intentionally replace that
    # requirement with a stronger executable-code prohibition.
    obsolete = "q1_plot.m lacks required token: title(ax, figureTitle"
    errors[:] = [item for item in errors if item != obsolete]

    plotting = _ORIGINAL_READ_TEXT(ROOT / "templates/matlab/q1_plot.m")
    code = _matlab_executable_code(plotting)
    if re.search(r"\b(?:title|sgtitle)\s*\(", code, flags=re.IGNORECASE):
        errors.append("q1_plot.m formal template must not contain executable overall title/sgtitle")
    for token in (
        "LaTeX/DOCX caption",
        "Scientific Figure Synthesis Gate",
        "[20, 120, 255] / 255",
        "[240, 68, 68] / 255",
        'grid(ax, "off")',
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
        "[20, 120, 255] / 255",
        "[240, 68, 68] / 255",
        'grid(ax, "off")',
    ):
        if token not in data_process:
            errors.append(f"data_process.m lacks current scientific Figure semantic token: {token}")

    style = _ORIGINAL_READ_TEXT(ROOT / "templates/matlab/hsk_apply_scientific_style.m")
    for token in (
        "palette.brightBlue = [20, 120, 255] / 255",
        "palette.vividRed = [240, 68, 68] / 255",
        "palette.brightGreen = [22, 179, 100] / 255",
        "高对比、中高饱和",
    ):
        if token not in style:
            errors.append(f"scientific style helper lacks current high-contrast token: {token}")


checks.check_templates = _check_templates


if __name__ == "__main__":
    raise SystemExit(checks.main())
