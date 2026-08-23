#!/usr/bin/env python3
"""Audit a modular LaTeX project and persist formal source/framework attestation."""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import yaml

from audit_paper_prose import Finding, audit_bibliography, audit_framework_consistency, audit_text, overall_status
from latex_delivery import sha256_file, source_bundle_snapshot

INCLUDE_RE = re.compile(r"\\(?:input|include)\s*\{([^{}]+)\}")
FORBIDDEN_CHILD_RE = re.compile(r"\\documentclass|\\begin\s*\{document\}|\\end\s*\{document\}")
VERBATIM_ENV_RE = re.compile(
    r"\\begin\{(?:verbatim|Verbatim|lstlisting|minted)\}.*?\\end\{(?:verbatim|Verbatim|lstlisting|minted)\}",
    re.S,
)
PAPER_FRAGMENT_HEADING = "### Paper Fragment Dependency Map"


def strip_comments(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines(keepends=True):
        out: list[str] = []
        escaped = False
        for char in line:
            if char == "%" and not escaped:
                break
            out.append(char)
            if char == "\\":
                escaped = not escaped
            else:
                escaped = False
        lines.append("".join(out))
    return "".join(lines)


def executable_tex(text: str) -> str:
    return strip_comments(VERBATIM_ENV_RE.sub("\n", text))


def resolve_include(project_root: Path, target: str) -> Path | None:
    raw = Path(target.strip())
    if raw.suffix == "":
        raw = raw.with_suffix(".tex")
    if raw.is_absolute():
        return None
    candidate = (project_root / raw).resolve()
    try:
        candidate.relative_to(project_root)
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def discover_tex_graph(main_file: Path) -> tuple[list[Path], list[Finding]]:
    root = main_file.parent.resolve()
    visited: set[Path] = set()
    stack: list[Path] = []
    order: list[Path] = []
    findings: list[Finding] = []

    def walk(path: Path) -> None:
        resolved = path.resolve()
        if resolved in stack:
            cycle = " -> ".join(item.relative_to(root).as_posix() for item in [*stack, resolved])
            findings.append(Finding("blocking", "latex_include_cycle", f"检测到 LaTeX include 循环：{cycle}", cycle))
            return
        if resolved in visited:
            relative = resolved.relative_to(root).as_posix()
            findings.append(Finding(
                "review_required",
                "latex_fragment_reincluded",
                "同一 LaTeX fragment 被重复 input/include；请确认不是重复正文。",
                relative,
            ))
            return
        if not resolved.is_file():
            findings.append(Finding("blocking", "latex_source_missing", f"LaTeX 源文件不存在：{resolved}"))
            return
        visited.add(resolved)
        stack.append(resolved)
        order.append(resolved)
        text = resolved.read_text(encoding="utf-8-sig", errors="strict")
        code = executable_tex(text)
        if resolved != main_file.resolve() and FORBIDDEN_CHILD_RE.search(code):
            relative = resolved.relative_to(root).as_posix()
            findings.append(Finding(
                "blocking",
                "latex_child_declares_document",
                f"子文件 {relative} 不得声明 documentclass/document 环境。",
                relative,
            ))
        for target in INCLUDE_RE.findall(code):
            child = resolve_include(root, target)
            if child is None:
                relative = resolved.relative_to(root).as_posix()
                evidence = f"{relative} -> {target}"
                findings.append(Finding(
                    "blocking",
                    "latex_include_missing",
                    f"{relative} 引用了不存在或越出工程根目录的文件：{target}",
                    evidence,
                ))
                continue
            walk(child)
        stack.pop()

    walk(main_file.resolve())
    return order, findings


def flatten_tex(main_file: Path, files: list[Path]) -> str:
    root = main_file.parent.resolve()
    cache = {
        path.resolve(): path.read_text(encoding="utf-8-sig", errors="strict")
        for path in files
    }
    stack: list[Path] = []

    def expand(path: Path) -> str:
        resolved = path.resolve()
        if resolved in stack:
            return ""
        stack.append(resolved)
        text = cache.get(resolved, "")
        code = executable_tex(text)
        cursor = 0
        chunks: list[str] = []
        for match in INCLUDE_RE.finditer(code):
            chunks.append(code[cursor:match.start()])
            child = resolve_include(root, match.group(1))
            if child is not None and child.resolve() in cache:
                chunks.append("\n" + expand(child) + "\n")
            cursor = match.end()
        chunks.append(code[cursor:])
        stack.pop()
        return "".join(chunks)

    return expand(main_file.resolve())


def _framework_section(text: str, heading: str) -> str:
    start = text.find(heading)
    if start < 0:
        return ""
    tail = text[start + len(heading):]
    next_heading = re.search(r"\n#{1,4}\s+", tail)
    return tail[:next_heading.start()] if next_heading else tail


def _parse_markdown_table(section: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if not cells or all(re.fullmatch(r":?-{2,}:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows


def audit_paper_fragment_sources(
    *,
    framework_path: Path,
    project_root: Path,
    active_tex_files: list[Path],
) -> list[Finding]:
    findings: list[Finding] = []
    text = framework_path.read_text(encoding="utf-8-sig", errors="strict")
    section = _framework_section(text, PAPER_FRAGMENT_HEADING)
    rows = _parse_markdown_table(section)
    if len(rows) < 2:
        return findings
    header = rows[0]
    source_index = next((i for i, item in enumerate(header) if "LaTeX" in item and "源码" in item), None)
    status_index = next((i for i, item in enumerate(header) if item == "状态"), None)
    id_index = next((i for i, item in enumerate(header) if "Fragment ID" in item), 0)
    if source_index is None:
        return findings
    active = {path.resolve() for path in active_tex_files}
    for cells in rows[1:]:
        if source_index >= len(cells):
            continue
        fragment_id = cells[id_index] if id_index < len(cells) else "<unknown>"
        status = cells[status_index] if status_index is not None and status_index < len(cells) else ""
        raw = cells[source_index].strip()
        if not raw or raw in {"—", "-", "无", "none", "None"}:
            continue
        candidate = (project_root / raw).resolve()
        try:
            candidate.relative_to(project_root)
        except ValueError:
            findings.append(Finding("blocking", "paper_fragment_source_outside_project", f"{fragment_id} 的 source_file 越出项目根目录：{raw}", raw))
            continue
        if candidate.suffix.lower() != ".tex" or not raw.replace("\\", "/").startswith("final_latex/"):
            findings.append(Finding("blocking", "paper_fragment_source_invalid", f"{fragment_id} 的 source_file 必须位于 final_latex/ 且为 .tex：{raw}", raw))
            continue
        if status == "current":
            if not candidate.is_file():
                findings.append(Finding("blocking", "paper_fragment_source_missing", f"current fragment {fragment_id} 指向不存在的 LaTeX 文件：{raw}", raw))
            elif candidate not in active:
                findings.append(Finding("blocking", "paper_fragment_source_not_in_active_graph", f"current fragment {fragment_id} 的源码未进入当前 main.tex include graph：{raw}", raw))
    return findings


def audit_project(
    main_file: Path,
    *,
    bib_path: Path | None = None,
    framework_path: Path | None = None,
    require_framework: bool = False,
) -> list[Finding]:
    main_file = main_file.resolve()
    project_root = main_file.parent.resolve()
    files, findings = discover_tex_graph(main_file)
    if any(item.severity == "blocking" for item in findings):
        return findings

    flattened = flatten_tex(main_file, files)
    findings.extend(audit_text(flattened))

    effective_bib = bib_path
    if effective_bib is None and (project_root / "references.bib").is_file():
        effective_bib = project_root / "references.bib"
    bib_text = effective_bib.read_text(encoding="utf-8-sig", errors="strict") if effective_bib and effective_bib.is_file() else None
    findings.extend(audit_bibliography(flattened, bib_text))

    if require_framework and (framework_path is None or not framework_path.is_file()):
        findings.append(Finding("blocking", "latex_framework_missing", "正式 LaTeX 审计要求当前 模型论文框架.md，但未找到该文件。"))
    framework_text = None
    if framework_path is not None and framework_path.is_file():
        framework_text = framework_path.read_text(encoding="utf-8-sig", errors="strict")
        findings.extend(audit_paper_fragment_sources(
            framework_path=framework_path,
            project_root=project_root.parent if project_root.name == "final_latex" else project_root,
            active_tex_files=files,
        ))
    findings.extend(audit_framework_consistency(flattened, framework_text))

    all_tex = sorted(project_root.rglob("*.tex"))
    active = {path.resolve() for path in files}
    for path in all_tex:
        if path.resolve() in active:
            continue
        if any(part.startswith(".") for part in path.relative_to(project_root).parts):
            continue
        relative = path.relative_to(project_root).as_posix()
        findings.append(Finding("warning", "latex_orphan_fragment", f"LaTeX 工程中存在未被 main.tex 引用的 .tex 文件：{relative}", relative))
    return findings


def write_audit_report(
    *,
    main_file: Path,
    findings: list[Finding],
    framework_path: Path | None = None,
    bib_path: Path | None = None,
    report_path: Path | None = None,
    mode: str = "formal",
) -> dict[str, object]:
    """Persist an audit attestation, including a failed report for invalid source graphs."""
    main_file = main_file.resolve()
    project = main_file.parent.resolve()
    snapshot_error: str | None = None
    try:
        snapshot = source_bundle_snapshot(main_file, bib_path=bib_path)
    except Exception as exc:  # noqa: BLE001 - persistence must survive malformed source graphs
        snapshot_error = str(exc)
        snapshot = {
            "source_bundle_sha256": None,
            "source_files": [],
            "source_file_count": 0,
        }
    framework_hash = sha256_file(framework_path) if framework_path is not None and framework_path.is_file() else None
    highest_severity = overall_status(findings)
    rejected = (
        highest_severity == "blocking"
        or (mode == "formal" and highest_severity == "review_required")
        or snapshot_error is not None
    )
    report = {
        "audit_schema_version": "1.0.0",
        "status": "failed" if rejected else "passed",
        "highest_severity": highest_severity,
        "mode": mode,
        "main": main_file.relative_to(project).as_posix(),
        **snapshot,
        "source_snapshot_error": snapshot_error,
        "framework": str(framework_path) if framework_path is not None else None,
        "framework_sha256": framework_hash,
        "findings": [asdict(item) for item in findings],
        "audited_at": datetime.now(timezone.utc).isoformat(),
    }
    destination = (report_path or project / "latex_audit_report.yaml").resolve()
    destination.write_text(yaml.safe_dump(report, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit a modular LaTeX project and delegate combined prose checks to audit_paper_prose.py."
    )
    parser.add_argument("tex", type=Path, help="LaTeX main file to audit")
    parser.add_argument("--bib", type=Path, help="Optional references.bib path; defaults to main directory/references.bib")
    parser.add_argument("--framework", type=Path, help="Optional 模型论文框架.md for Terminology/Numeric Profile checks")
    parser.add_argument("--require-framework", action="store_true", help="Block when the framework file is missing")
    parser.add_argument("--report", type=Path, help="Write YAML audit attestation; defaults to final_latex/latex_audit_report.yaml when --write-report is used")
    parser.add_argument("--write-report", action="store_true", help="Persist latex_audit_report.yaml next to the main file")
    parser.add_argument("--mode", choices=["formal", "template_smoke"], default="formal")
    parser.add_argument("--strict", action="store_true", help="Return exit code 1 for blocking or review_required findings")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    if not args.tex.is_file():
        raise SystemExit(f"LaTeX main file not found: {args.tex}")

    findings = audit_project(
        args.tex,
        bib_path=args.bib,
        framework_path=args.framework,
        require_framework=args.require_framework,
    )
    status = overall_status(findings)
    if args.report is not None or args.write_report:
        write_audit_report(
            main_file=args.tex,
            findings=findings,
            framework_path=args.framework,
            bib_path=args.bib,
            report_path=args.report,
            mode=args.mode,
        )
    if args.json:
        print(json.dumps({"status": status, "findings": [asdict(item) for item in findings]}, ensure_ascii=False, indent=2))
    else:
        print(f"LaTeX project audit: {status}")
        for item in findings:
            suffix = f" | {item.evidence}" if item.evidence else ""
            print(f"- [{item.severity}] {item.code}: {item.message}{suffix}")

    return 1 if args.strict and status in {"blocking", "review_required"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
