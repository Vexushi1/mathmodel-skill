#!/usr/bin/env python3
"""Audit a modular LaTeX project and persist a deterministic attestation.

The wrapper expands project-local input/include files, performs deterministic project-
graph checks, delegates prose/structure/BibTeX/framework checks to
``audit_paper_prose.py``, and can write a machine-readable audit report bound to the
active LaTeX source bundle and model-paper framework.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import yaml

from audit_paper_prose import (
    Finding,
    audit_bibliography,
    audit_framework_consistency,
    audit_text,
    overall_status,
)
from latex_delivery import sha256_file, source_bundle_snapshot

INCLUDE_RE = re.compile(r"\\(?:input|include)\s*\{([^{}]+)\}")
FORBIDDEN_CHILD_RE = re.compile(
    r"\\documentclass(?:\[[^\]]*\])?\{|\\begin\{document\}|\\end\{document\}"
)
CONTENT_DIRS = ("frontmatter", "sections", "appendices")
VERBATIM_LIKE_ENVS = ("verbatim", "lstlisting", "minted")


def _split_code_comment(line: str) -> tuple[str, str]:
    """Split a LaTeX line at the first unescaped percent sign."""
    backslashes = 0
    for index, char in enumerate(line):
        if char == "\\":
            backslashes += 1
            continue
        if char == "%" and backslashes % 2 == 0:
            return line[:index], line[index:]
        backslashes = 0
    return line, ""


def _executable_tex(text: str) -> str:
    """Return code-like LaTeX text for deterministic structural checks."""
    uncommented = "".join(
        _split_code_comment(line)[0]
        for line in text.splitlines(keepends=True)
    )
    executable = uncommented
    for env in VERBATIM_LIKE_ENVS:
        executable = re.sub(
            rf"\\begin\{{{re.escape(env)}\}}.*?\\end\{{{re.escape(env)}\}}",
            "\n",
            executable,
            flags=re.S,
        )
    return executable


def _resolve_include(target: str, *, project_root: Path) -> Path | None:
    """Resolve an input/include target exactly from the main-file project root."""
    raw = Path(target.strip())
    if raw.suffix == "":
        raw = raw.with_suffix(".tex")
    if raw.is_absolute():
        return None

    resolved = (project_root / raw).resolve()
    try:
        resolved.relative_to(project_root)
    except ValueError:
        return None
    return resolved if resolved.is_file() else None


def expand_project(main_file: Path) -> tuple[str, list[Finding], set[Path]]:
    project_root = main_file.parent.resolve()
    visited: set[Path] = set()
    stack: list[Path] = []
    findings: list[Finding] = []

    def expand(path: Path, *, is_main: bool) -> str:
        resolved = path.resolve()
        if resolved in stack:
            cycle = " -> ".join(item.relative_to(project_root).as_posix() for item in [*stack, resolved])
            findings.append(Finding("blocking", "latex_include_cycle", "LaTeX 模块存在递归 input/include 环。", cycle))
            return ""
        if resolved in visited:
            findings.append(
                Finding(
                    "review_required",
                    "latex_fragment_reincluded",
                    "同一项目内 .tex fragment 被重复 input/include；请确认不是重复正文。",
                    resolved.relative_to(project_root).as_posix(),
                )
            )

        visited.add(resolved)
        stack.append(resolved)
        text = resolved.read_text(encoding="utf-8-sig", errors="strict")
        if not is_main:
            forbidden = FORBIDDEN_CHILD_RE.search(_executable_tex(text))
            if forbidden:
                findings.append(
                    Finding(
                        "blocking",
                        "latex_child_declares_document",
                        "正文子文件不得声明 documentclass 或 document 环境。",
                        f"{resolved.relative_to(project_root).as_posix()}: {forbidden.group(0)}",
                    )
                )

        expanded_lines: list[str] = []
        for line in text.splitlines(keepends=True):
            code, comment = _split_code_comment(line)

            def replace(match: re.Match[str]) -> str:
                target = match.group(1).strip()
                child = _resolve_include(target, project_root=project_root)
                if child is None:
                    findings.append(
                        Finding(
                            "blocking",
                            "latex_include_missing",
                            "LaTeX input/include 必须使用 main.tex 所在工程根目录的相对路径，且目标文件必须存在于项目根目录内。",
                            f"{resolved.relative_to(project_root).as_posix()} -> {target}",
                        )
                    )
                    return ""
                return "\n" + expand(child, is_main=False) + "\n"

            expanded_lines.append(INCLUDE_RE.sub(replace, code) + comment)
        stack.pop()
        return "".join(expanded_lines)

    combined = expand(main_file, is_main=True)

    for directory_name in CONTENT_DIRS:
        directory = project_root / directory_name
        if not directory.is_dir():
            continue
        for candidate in sorted(directory.rglob("*.tex")):
            resolved = candidate.resolve()
            if resolved not in visited:
                findings.append(
                    Finding(
                        "warning",
                        "latex_orphan_fragment",
                        "检测到未被 main.tex 当前 input/include 链引用的正文 fragment；请确认是待删除文件、可选草稿还是遗漏入口。",
                        candidate.relative_to(project_root).as_posix(),
                    )
                )
    return combined, findings, visited


def audit_fragment_source_files(
    main_file: Path,
    framework_path: Path,
    visited: set[Path],
) -> list[Finding]:
    """Validate declared current Paper Fragment -> physical LaTeX source mappings."""
    text = framework_path.read_text(encoding="utf-8-sig", errors="strict")
    heading = "### Paper Fragment Dependency Map"
    start = text.find(heading)
    if start < 0:
        return []
    tail = text[start + len(heading):]
    next_heading = re.search(r"\n#{1,3}\s+", tail)
    section = tail[:next_heading.start()] if next_heading else tail
    project_root = framework_path.parent.resolve()
    final_root = main_file.parent.resolve()
    findings: list[Finding] = []

    for raw_line in section.splitlines():
        line = raw_line.strip()
        if not line.startswith("| paper."):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 7:
            continue
        fragment_id, source_file, status = cells[0], cells[5].strip("` "), cells[6].strip("` ")
        if not source_file or status != "current":
            continue
        candidate = (project_root / source_file).resolve()
        try:
            candidate.relative_to(project_root)
            candidate.relative_to(final_root)
        except ValueError:
            findings.append(
                Finding(
                    "blocking",
                    "paper_fragment_source_outside_latex",
                    "current Paper Fragment 的 source_file 必须位于当前 final_latex 工程内。",
                    f"{fragment_id}: {source_file}",
                )
            )
            continue
        if not candidate.is_file():
            findings.append(
                Finding(
                    "blocking",
                    "paper_fragment_source_missing",
                    "current Paper Fragment 声明的 LaTeX source_file 不存在。",
                    f"{fragment_id}: {source_file}",
                )
            )
            continue
        if candidate not in visited:
            findings.append(
                Finding(
                    "blocking",
                    "paper_fragment_source_not_in_active_graph",
                    "current Paper Fragment 的 source_file 未进入 main.tex 当前 input/include 图。",
                    f"{fragment_id}: {source_file}",
                )
            )
    return findings


def audit_project(
    main_file: Path,
    *,
    bib_path: Path | None = None,
    framework_path: Path | None = None,
    require_framework: bool = False,
) -> list[Finding]:
    combined, project_findings, visited = expand_project(main_file)
    findings = list(project_findings)
    findings.extend(audit_text(combined))

    if bib_path is None:
        default_bib = main_file.parent / "references.bib"
        bib_path = default_bib if default_bib.is_file() else None
    bib_text = None
    if bib_path is not None and bib_path.is_file():
        bib_text = bib_path.read_text(encoding="utf-8-sig", errors="strict")
    findings.extend(audit_bibliography(combined, bib_text))

    framework_text = None
    if framework_path is not None and framework_path.is_file():
        framework_text = framework_path.read_text(encoding="utf-8-sig", errors="strict")
        findings.extend(audit_fragment_source_files(main_file, framework_path, visited))
    elif require_framework or framework_path is not None:
        findings.append(
            Finding(
                "blocking",
                "latex_framework_missing",
                "正式 LaTeX 审计要求存在当前 模型论文框架.md。",
                str(framework_path or "模型论文框架.md"),
            )
        )
    findings.extend(audit_framework_consistency(combined, framework_text))
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
    """Persist an audit attestation bound to the current source bundle/framework."""
    main_file = main_file.resolve()
    project = main_file.parent.resolve()
    snapshot = source_bundle_snapshot(main_file, bib_path=bib_path)
    framework_hash = sha256_file(framework_path) if framework_path is not None and framework_path.is_file() else None
    report = {
        "audit_schema_version": "1.0.0",
        "status": overall_status(findings),
        "mode": mode,
        "main": main_file.relative_to(project).as_posix(),
        **snapshot,
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
