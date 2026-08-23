#!/usr/bin/env python3
"""Audit a modular LaTeX project by expanding project-local input/include files.

This wrapper preserves ``audit_paper_prose.py`` as the prose/structure/BibTeX/framework
authority. It adds deterministic project-graph checks, expands the active LaTeX source
tree in document order, then delegates the combined text to the existing audit logic.

It intentionally does not infer mathematical correctness or LaTeX search-path semantics
outside the project root.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict
from pathlib import Path

from audit_paper_prose import (
    Finding,
    audit_bibliography,
    audit_framework_consistency,
    audit_text,
    overall_status,
)

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
    """Return code-like LaTeX text for deterministic structural checks.

    Comments and verbatim-like environments are excluded because examples in comments,
    appendices, or listings must not be interpreted as executable document declarations.
    This is intentionally conservative; it is not a full TeX parser.
    """
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
    """Resolve an input/include target exactly from the main-file project root.

    The repository compiles LaTeX from ``main.tex``'s directory. Nested fragments must
    therefore keep project-root-relative paths such as ``sections/q3/model`` rather than
    relying on the including child file's directory. The audit must never accept a path
    that the formal compile can reject.
    """
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
            # LaTeX 允许同一文件被多次 input，但论文 fragment 默认不应重复展开。
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


def audit_project(
    main_file: Path,
    *,
    bib_path: Path | None = None,
    framework_path: Path | None = None,
) -> list[Finding]:
    combined, project_findings, _ = expand_project(main_file)
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
    findings.extend(audit_framework_consistency(combined, framework_text))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit a modular LaTeX project and delegate combined prose checks to audit_paper_prose.py."
    )
    parser.add_argument("tex", type=Path, help="LaTeX main file to audit")
    parser.add_argument("--bib", type=Path, help="Optional references.bib path; defaults to main directory/references.bib")
    parser.add_argument("--framework", type=Path, help="Optional 模型论文框架.md for Terminology/Numeric Profile checks")
    parser.add_argument("--strict", action="store_true", help="Return exit code 1 for blocking or review_required findings")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    if not args.tex.is_file():
        raise SystemExit(f"LaTeX main file not found: {args.tex}")

    findings = audit_project(args.tex, bib_path=args.bib, framework_path=args.framework)
    status = overall_status(findings)
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
