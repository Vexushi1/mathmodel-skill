#!/usr/bin/env python3
"""Deterministic LaTeX source-bundle and compile-report utilities.

The source bundle contains the active project-root-relative TeX include graph plus
project-local bibliography, document class/style files and graphics referenced by
that graph. It deliberately ignores system TeX packages and unrelated orphan files.
"""
from __future__ import annotations

import hashlib
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
TEXT_SUFFIXES = {".tex", ".bib", ".cls", ".sty", ".cfg", ".def"}
GRAPHIC_SUFFIXES = (".pdf", ".png", ".jpg", ".jpeg", ".eps", ".svg", ".tif", ".tiff")


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


def inspect_log(log_path: Path) -> dict[str, int]:
    if not log_path.is_file():
        return {"unresolved_references": 0, "unresolved_citations": 0, "overfull_boxes": 0}
    text = log_path.read_text(encoding="utf-8", errors="ignore")
    ref_count = len(re.findall(r"LaTeX Warning: Reference .*? undefined", text))
    cite_count = len(re.findall(r"LaTeX Warning: Citation .*? undefined", text))
    if ref_count == 0 and "There were undefined references." in text:
        ref_count = 1
    if cite_count == 0 and "There were undefined citations." in text:
        cite_count = 1
    overfull = len(re.findall(r"Overfull \\[hv]box", text))
    return {
        "unresolved_references": ref_count,
        "unresolved_citations": cite_count,
        "overfull_boxes": overfull,
    }


def write_compile_report(
    *,
    project: Path,
    main: Path,
    profile: str,
    engine: str,
    bibliography: str,
    sequence: Iterable[str],
    bib_path: Path | None = None,
) -> dict[str, Any]:
    project = project.resolve()
    main = main.resolve()
    pdf = project / f"{main.stem}.pdf"
    if not pdf.is_file():
        raise FileNotFoundError(pdf)
    snapshot = source_bundle_snapshot(main, bib_path=bib_path)
    log_status = inspect_log(project / f"{main.stem}.log")
    status = "passed" if not (log_status["unresolved_references"] or log_status["unresolved_citations"]) else "failed"
    report = {
        "report_schema_version": "2.0.0",
        "status": status,
        "profile": profile,
        "engine": engine,
        "bibliography": bibliography,
        "sequence": list(sequence),
        "main": main.relative_to(project).as_posix(),
        **snapshot,
        "compiled_from_source_sha256": snapshot["source_bundle_sha256"],
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
    if str(report.get("report_schema_version", "")) != "2.0.0":
        issues.append("compile_report缺少v2源码新鲜度Schema；请用当前render_paper.py重新编译")
        return issues
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
