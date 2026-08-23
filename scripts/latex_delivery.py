#!/usr/bin/env python3
"""Deterministic LaTeX source, audit, and compile-attestation utilities.

The source bundle contains the active project-root-relative TeX include graph plus
project-local bibliography, document class/style files and graphics referenced by
that graph. Compile reports bind the PDF to that source bundle, the formal LaTeX
audit attestation, and the selected compile-profile definition.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

INCLUDE_RE = re.compile(r"\\(?:input|include)\s*\{([^{}]+)\}")
DOCUMENTCLASS_RE = re.compile(r"\\documentclass(?:\[[^\]]*\])?\{([^{}]+)\}")
USEPACKAGE_RE = re.compile(r"\\usepackage(?:\[[^\]]*\])?\{([^{}]+)\}")
ADDBIB_RE = re.compile(r"\\addbibresource(?:\[[^\]]*\])?\{([^{}]+)\}")
BIBLIOGRAPHY_RE = re.compile(r"\\bibliography\{([^{}]+)\}")
GRAPHICS_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^{}]+)\}")
GRAPHICSPATH_RE = re.compile(r"\\graphicspath\s*\{((?:\{[^{}]*\}\s*)+)\}")
GRAPHIC_DIR_RE = re.compile(r"\{([^{}]*)\}")
VERBATIM_ENV_RE = re.compile(
    r"\\begin\{(?:verbatim|Verbatim|lstlisting|minted)\}.*?\\end\{(?:verbatim|Verbatim|lstlisting|minted)\}",
    re.S,
)
TEXT_SUFFIXES = {".tex", ".bib", ".cls", ".sty", ".cfg", ".def"}
GRAPHIC_SUFFIXES = (".pdf", ".png", ".jpg", ".jpeg", ".eps", ".svg", ".tif", ".tiff")
SKILL_ROOT = Path(__file__).resolve().parent.parent
COMPILE_PROFILES_PATH = SKILL_ROOT / "core" / "compile_profiles.yaml"


def _split_code_comment(line: str) -> str:
    backslashes = 0
    for index, char in enumerate(line):
        if char == "\\":
            backslashes += 1
            continue
        if char == "%" and backslashes % 2 == 0:
            return line[:index]
        backslashes = 0
    return line


def executable_tex(text: str) -> str:
    text = VERBATIM_ENV_RE.sub("\n", text)
    return "".join(_split_code_comment(line) for line in text.splitlines(keepends=True))


def _safe_project_path(root: Path, token: str, suffix: str | None = None) -> Path | None:
    raw = Path(token.strip())
    if suffix and raw.suffix == "":
        raw = raw.with_suffix(suffix)
    if raw.is_absolute():
        return None
    candidate = (root / raw).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def _discover_tex_graph(main: Path) -> tuple[set[Path], str]:
    root = main.parent.resolve()
    visited: set[Path] = set()
    stack: list[Path] = []
    texts: list[str] = []

    def walk(path: Path) -> None:
        resolved = path.resolve()
        if resolved in stack:
            cycle = " -> ".join(item.relative_to(root).as_posix() for item in [*stack, resolved])
            raise ValueError(f"LaTeX include cycle: {cycle}")
        if resolved in visited:
            return
        if not resolved.is_file():
            raise ValueError(f"LaTeX source missing: {resolved}")
        visited.add(resolved)
        stack.append(resolved)
        text = resolved.read_text(encoding="utf-8-sig", errors="strict")
        code = executable_tex(text)
        texts.append(code)
        for target in INCLUDE_RE.findall(code):
            child = _safe_project_path(root, target, ".tex")
            if child is None or not child.is_file():
                relative = resolved.relative_to(root).as_posix()
                raise ValueError(f"LaTeX include missing or outside project: {relative} -> {target}")
            walk(child)
        stack.pop()

    walk(main)
    return visited, "\n".join(texts)


def _graphic_dirs(root: Path, combined: str) -> list[Path]:
    directories = [root]
    for block in GRAPHICSPATH_RE.findall(combined):
        for token in GRAPHIC_DIR_RE.findall(block):
            candidate = _safe_project_path(root, token)
            if candidate is not None and candidate.is_dir() and candidate not in directories:
                directories.append(candidate)
    return directories


def _resolve_graphic(root: Path, token: str, directories: Iterable[Path]) -> Path | None:
    raw = Path(token.strip())
    search: list[Path] = []
    for directory in directories:
        if raw.suffix:
            search.append((directory / raw).resolve())
        else:
            search.extend((directory / raw).with_suffix(suffix).resolve() for suffix in GRAPHIC_SUFFIXES)
    for candidate in search:
        try:
            candidate.relative_to(root)
        except ValueError:
            continue
        if candidate.is_file():
            return candidate
    return None


def source_bundle_files(main: Path, bib_path: Path | None = None) -> list[Path]:
    main = main.resolve()
    root = main.parent.resolve()
    visited, combined = _discover_tex_graph(main)
    files = set(visited)

    for raw_name in DOCUMENTCLASS_RE.findall(combined):
        for name in raw_name.split(","):
            candidate = _safe_project_path(root, name.strip(), ".cls")
            if candidate is not None and candidate.is_file():
                files.add(candidate)
    for raw_names in USEPACKAGE_RE.findall(combined):
        for name in raw_names.split(","):
            candidate = _safe_project_path(root, name.strip(), ".sty")
            if candidate is not None and candidate.is_file():
                files.add(candidate)

    bib_candidates: list[Path] = []
    if bib_path is not None:
        bib_candidates.append(bib_path.resolve())
    for token in ADDBIB_RE.findall(combined):
        candidate = _safe_project_path(root, token, ".bib")
        if candidate is not None:
            bib_candidates.append(candidate)
    for block in BIBLIOGRAPHY_RE.findall(combined):
        for token in block.split(","):
            candidate = _safe_project_path(root, token.strip(), ".bib")
            if candidate is not None:
                bib_candidates.append(candidate)
    default_bib = root / "references.bib"
    if default_bib.is_file():
        bib_candidates.append(default_bib)
    for candidate in bib_candidates:
        try:
            candidate.relative_to(root)
        except ValueError:
            continue
        if candidate.is_file():
            files.add(candidate)

    directories = _graphic_dirs(root, combined)
    for token in GRAPHICS_RE.findall(combined):
        graphic = _resolve_graphic(root, token, directories)
        if graphic is not None:
            files.add(graphic)

    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def sha256_file(path: Path) -> str:
    path = path.resolve()
    if path.suffix.lower() in TEXT_SUFFIXES:
        text = path.read_text(encoding="utf-8-sig", errors="strict").replace("\r\n", "\n").replace("\r", "\n")
        payload = text.encode("utf-8")
    else:
        payload = path.read_bytes()
    return hashlib.sha256(payload).hexdigest()


def source_bundle_snapshot(main: Path, bib_path: Path | None = None) -> dict[str, Any]:
    main = main.resolve()
    root = main.parent.resolve()
    files = source_bundle_files(main, bib_path=bib_path)
    digest = hashlib.sha256()
    records: list[dict[str, str]] = []
    for path in files:
        relative = path.relative_to(root).as_posix()
        file_hash = sha256_file(path)
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(file_hash))
        records.append({"path": relative, "sha256": file_hash})
    return {
        "source_bundle_sha256": digest.hexdigest(),
        "source_files": records,
        "source_file_count": len(records),
    }


def profile_fingerprint(profile_config: Mapping[str, Any]) -> str:
    """Hash the machine-readable profile definition without depending on YAML layout."""
    payload = json.dumps(profile_config, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def current_profile_config(profile_name: str) -> Mapping[str, Any] | None:
    if not COMPILE_PROFILES_PATH.is_file():
        return None
    payload = yaml.safe_load(COMPILE_PROFILES_PATH.read_text(encoding="utf-8")) or {}
    profile = (payload.get("profiles") or {}).get(profile_name)
    return profile if isinstance(profile, Mapping) else None


def uses_profile_override(
    profile_config: Mapping[str, Any] | None,
    *,
    engine: str,
    bibliography: str,
    sequence: Iterable[str],
) -> bool:
    if not profile_config:
        return False
    canonical_engine = str(profile_config.get("engine", ""))
    canonical_bib = str(profile_config.get("bibliography", ""))
    canonical_sequence = [str(item) for item in profile_config.get("sequence", [])]
    return (
        engine != canonical_engine
        or bibliography != canonical_bib
        or list(sequence) != canonical_sequence
    )


def inspect_log(log_path: Path) -> dict[str, Any]:
    if not log_path.is_file():
        return {
            "log_present": False,
            "fatal_errors": 1,
            "unresolved_references": 0,
            "unresolved_citations": 0,
            "overfull_boxes": 0,
        }
    text = log_path.read_text(encoding="utf-8", errors="ignore")
    ref_count = len(re.findall(r"LaTeX Warning: Reference .*? undefined", text))
    cite_count = len(re.findall(r"LaTeX Warning: Citation .*? undefined", text))
    if ref_count == 0 and "There were undefined references." in text:
        ref_count = 1
    if cite_count == 0 and "There were undefined citations." in text:
        cite_count = 1
    fatal = len(re.findall(r"(?:LaTeX Error|Undefined control sequence|Fatal error occurred)", text))
    overfull = len(re.findall(r"Overfull \\[hv]box", text))
    return {
        "log_present": True,
        "fatal_errors": fatal,
        "unresolved_references": ref_count,
        "unresolved_citations": cite_count,
        "overfull_boxes": overfull,
    }


def verify_audit_report(
    *,
    project: Path,
    main: Path,
    report: Mapping[str, Any],
    framework_path: Path | None = None,
    require_formal: bool = True,
) -> list[str]:
    """Verify that an audit attestation still describes the current source/framework."""
    issues: list[str] = []
    if str(report.get("audit_schema_version", "")) != "1.0.0":
        return ["latex_audit_report缺少v1审计证明Schema；请重新运行当前项目审计"]
    if str(report.get("status", "")).lower() != "passed":
        issues.append("latex_audit_report未通过")
    if require_formal and str(report.get("mode", "")) != "formal":
        issues.append("正式交付不得使用template_smoke审计证明")
    try:
        current_source = source_bundle_snapshot(main)["source_bundle_sha256"]
    except Exception as exc:  # noqa: BLE001
        return [f"LaTeX source bundle无法重建: {exc}"]
    if str(report.get("source_bundle_sha256", "")) != current_source:
        issues.append("LaTeX源码在审计后发生变化；latex_audit_report stale")
    if require_formal:
        framework = framework_path or project.parent / "模型论文框架.md"
        if not framework.is_file():
            issues.append("正式LaTeX证明缺少模型论文框架.md")
        else:
            recorded = str(report.get("framework_sha256", ""))
            if not recorded or recorded != sha256_file(framework):
                issues.append("模型论文框架在审计后发生变化；latex_audit_report stale")
    return issues


def write_compile_report(
    *,
    project: Path,
    main: Path,
    profile: str,
    engine: str,
    bibliography: str,
    sequence: Iterable[str],
    profile_config: Mapping[str, Any] | None = None,
    audit_report_path: Path | None = None,
    attestation_mode: str = "formal",
    bib_path: Path | None = None,
) -> dict[str, Any]:
    project = project.resolve()
    main = main.resolve()
    pdf = project / f"{main.stem}.pdf"
    if not pdf.is_file():
        raise FileNotFoundError(pdf)
    snapshot = source_bundle_snapshot(main, bib_path=bib_path)
    log_status = inspect_log(project / f"{main.stem}.log")

    audit_path = (audit_report_path or project / "latex_audit_report.yaml").resolve()
    audit_report: dict[str, Any] = {}
    audit_issues: list[str] = []
    if audit_path.is_file():
        audit_report = yaml.safe_load(audit_path.read_text(encoding="utf-8")) or {}
        audit_issues = verify_audit_report(
            project=project,
            main=main,
            report=audit_report,
            require_formal=attestation_mode == "formal",
        )
    elif attestation_mode == "formal":
        audit_issues.append("正式编译缺少latex_audit_report.yaml")

    status = "passed"
    if (
        not log_status["log_present"]
        or log_status["fatal_errors"]
        or log_status["unresolved_references"]
        or log_status["unresolved_citations"]
        or audit_issues
    ):
        status = "failed"

    profile_config = profile_config or current_profile_config(profile)
    profile_hash = profile_fingerprint(profile_config) if profile_config is not None else None
    effective_sequence = list(sequence)
    override_used = uses_profile_override(
        profile_config,
        engine=engine,
        bibliography=bibliography,
        sequence=effective_sequence,
    )
    report = {
        "report_schema_version": "3.0.0",
        "status": status,
        "attestation_mode": attestation_mode,
        "profile": profile,
        "compile_profile_sha256": profile_hash,
        "engine": engine,
        "bibliography": bibliography,
        "sequence": effective_sequence,
        "profile_override_used": override_used,
        "main": main.relative_to(project).as_posix(),
        **snapshot,
        "compiled_from_source_sha256": snapshot["source_bundle_sha256"],
        "latex_audit_report": audit_path.relative_to(project).as_posix() if audit_path.is_relative_to(project) else str(audit_path),
        "latex_audit_report_sha256": sha256_file(audit_path) if audit_path.is_file() else None,
        "audit_status": str(audit_report.get("status", "missing")),
        "audit_issues": audit_issues,
        "pdf": pdf.relative_to(project).as_posix(),
        "pdf_sha256": sha256_file(pdf),
        **log_status,
        "compiled_at": datetime.now(timezone.utc).isoformat(),
    }
    (project / "compile_report.yaml").write_text(
        yaml.safe_dump(report, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    return report


def verify_compile_report(
    *,
    project: Path,
    main: Path,
    pdf: Path,
    report: Mapping[str, Any],
) -> list[str]:
    issues: list[str] = []
    if str(report.get("report_schema_version", "")) != "3.0.0":
        issues.append("compile_report缺少v3交付证明Schema；请用当前render_paper.py重新编译")
        return issues
    if str(report.get("status", "")).lower() != "passed":
        issues.append("compile_report未通过")
    if str(report.get("attestation_mode", "")) != "formal":
        issues.append("正式交付不得使用template_smoke编译证明")
    try:
        snapshot = source_bundle_snapshot(main)
    except Exception as exc:  # noqa: BLE001
        return [f"LaTeX source bundle无法重建: {exc}"]
    current_source = snapshot["source_bundle_sha256"]
    recorded_source = str(report.get("source_bundle_sha256", ""))
    compiled_source = str(report.get("compiled_from_source_sha256", ""))
    if not recorded_source or not compiled_source:
        issues.append("compile_report缺少source_bundle_sha256/compiled_from_source_sha256")
    elif current_source != recorded_source or current_source != compiled_source:
        issues.append("LaTeX source bundle已在编译后变化；当前PDF stale，必须重新编译")

    profile_name = str(report.get("profile", ""))
    current_profile = current_profile_config(profile_name)
    recorded_profile = str(report.get("compile_profile_sha256", ""))
    if current_profile is None:
        issues.append(f"compile_report引用未知编译profile: {profile_name}")
    elif not recorded_profile or recorded_profile != profile_fingerprint(current_profile):
        issues.append("编译profile定义已变化；当前PDF需要重新按当前profile编译")
    else:
        recorded_sequence = [str(item) for item in (report.get("sequence") or [])]
        expected_override = uses_profile_override(
            current_profile,
            engine=str(report.get("engine", "")),
            bibliography=str(report.get("bibliography", "")),
            sequence=recorded_sequence,
        )
        if bool(report.get("profile_override_used")) != expected_override:
            issues.append("compile_report的profile_override_used与实际engine/bibliography/sequence不一致")

    latex_project = main.parent.resolve()
    raw_audit = Path(str(report.get("latex_audit_report") or "latex_audit_report.yaml"))
    audit_path = raw_audit.resolve() if raw_audit.is_absolute() else (latex_project / raw_audit).resolve()
    try:
        audit_path.relative_to(latex_project)
    except ValueError:
        issues.append("compile_report绑定的latex_audit_report越出当前LaTeX工程")
    else:
        if not audit_path.is_file():
            issues.append("compile_report绑定的latex_audit_report不存在")
        else:
            current_audit_hash = sha256_file(audit_path)
            if current_audit_hash != str(report.get("latex_audit_report_sha256", "")):
                issues.append("latex_audit_report与compile_report绑定哈希不一致")
            audit_report = yaml.safe_load(audit_path.read_text(encoding="utf-8")) or {}
            issues.extend(
                verify_audit_report(
                    project=latex_project,
                    main=main,
                    report=audit_report,
                    require_formal=True,
                )
            )

    if not bool(report.get("log_present")) or int(report.get("fatal_errors", 0) or 0) != 0:
        issues.append("compile_report没有有效的正式编译日志证明")
    if int(report.get("unresolved_references", 0) or 0) != 0:
        issues.append("compile_report存在未解析引用")
    if int(report.get("unresolved_citations", 0) or 0) != 0:
        issues.append("compile_report存在未解析文献引用")

    if not pdf.is_file():
        issues.append(f"编译PDF不存在: {pdf}")
    else:
        current_pdf = sha256_file(pdf)
        recorded_pdf = str(report.get("pdf_sha256", ""))
        if not recorded_pdf:
            issues.append("compile_report缺少pdf_sha256")
        elif current_pdf != recorded_pdf:
            issues.append("当前PDF哈希与compile_report不一致")
    return issues
