#!/usr/bin/env python3
"""Module-aware entrypoint for the HSK repository lint suite.

The large cross-contract checks live in ``lint_skill_checks.py``.  This entrypoint adds
current-source adapters that require repository-wide context, most notably the modular
CUMCM LaTeX template whose semantic tokens now live in child ``.tex`` files instead of
being duplicated in ``hsk_main.tex`` comments.
"""
from __future__ import annotations

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


def _module_aware_read_text(path: Path) -> str:
    """Present the active CUMCM template as one virtual document to legacy checks.

    The returned text is assembled from actual source modules.  No semantic marker is
    injected and no comment-only compatibility token is accepted as evidence.
    """
    resolved = Path(path).resolve()
    if resolved == _CUMCM_MAIN:
        return "\n".join(_ORIGINAL_READ_TEXT(item) for item in _CUMCM_LINT_PARTS)
    return _ORIGINAL_READ_TEXT(path)


checks.read_text = _module_aware_read_text

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


def _check_templates(errors: list[str]) -> None:
    main_text = _ORIGINAL_READ_TEXT(_CUMCM_ROOT / "hsk_main.tex")
    if "兼容旧版静态合同检查" in main_text:
        errors.append("CUMCM main must not carry comment-only compatibility markers for lint")
    if "\\subsection{问题提出}" in main_text or "\\subsection{求解结果}" in main_text:
        errors.append("CUMCM main must remain orchestration-only; semantic section tokens belong in child modules")
    _original_check_templates(errors)


checks.check_templates = _check_templates


if __name__ == "__main__":
    raise SystemExit(checks.main())
