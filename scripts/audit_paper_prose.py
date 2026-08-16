#!/usr/bin/env python3
"""Lightweight prose/structure audit for HSK LaTeX papers.

The audit is intentionally conservative: it reports repeated/template-like prose and
structural writing-contract violations, but never rewrites paper text. Ordinary uses
of contrast words such as “但/然而” are not errors; only repeated/high-density patterns
are flagged for review.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

SEVERITY_ORDER = {"pass": 0, "warning": 1, "review_required": 2}
CONTRAST_RE = re.compile(r"但(?:是)?|然而|不过|并非|不是|不能|只能|而不是|却")
PARAGRAPH_START_RE = re.compile(r"^(?:本文|本问|该模型)(?:认为|采用|建立|使用|通过|将|对|在|根据|从|以|中|所)?")
QUESTION_SECTION_RE = re.compile(r"\\section\{问题[一二三四五六七八九十百0-9]+模型建立及求解\}")
SECTION_RE = re.compile(r"\\section\{([^{}]+)\}")
LABEL_RE = re.compile(r"\\label\{((?:fig|tab):[^{}]+)\}")
REF_TEMPLATE = r"\\(?:ref|autoref|cref|Cref)\{{{label}\}}"


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    evidence: str = ""


def _strip_comments(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
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
    return "\n".join(lines)


def _document_body(text: str) -> str:
    text = _strip_comments(text)
    match = re.search(r"\\begin\{document\}(.*?)\\end\{document\}", text, flags=re.S)
    return match.group(1) if match else text


def _remove_non_prose_blocks(text: str) -> str:
    result = text
    for env in ("verbatim", "lstlisting", "minted", "equation", "equation*", "align", "align*", "gather", "gather*", "table", "table*", "figure", "figure*"):
        result = re.sub(
            rf"\\begin\{{{re.escape(env)}\}}.*?\\end\{{{re.escape(env)}\}}",
            "\n",
            result,
            flags=re.S,
        )
    result = re.sub(r"\\\[.*?\\\]", " ", result, flags=re.S)
    result = re.sub(r"\$\$.*?\$\$", " ", result, flags=re.S)
    result = re.sub(r"\$[^$]*\$", " ", result)
    return result


def _plain_paragraphs(body: str) -> list[str]:
    text = _remove_non_prose_blocks(body)
    text = re.sub(r"\\(?:section|subsection|subsubsection|paragraph)\*?\{[^{}]*\}", "\n\n", text)
    text = re.sub(r"\\(?:begin|end)\{[^{}]+\}", "\n", text)
    text = re.sub(r"\\(?:label|ref|autoref|cref|Cref|cite|citep|citet)\{[^{}]*\}", " ", text)
    text = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?", " ", text)
    text = text.replace("{", " ").replace("}", " ")
    paragraphs = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", text)]
    return [p for p in paragraphs if len(p) >= 20]


def _main_text_before_appendix(body: str) -> str:
    return body.split("\\appendix", 1)[0]


def _section_content(body: str, title: str) -> str | None:
    marker = re.search(rf"\\section\{{{re.escape(title)}\}}", body)
    if not marker:
        return None
    tail = body[marker.end():]
    next_section = SECTION_RE.search(tail)
    return tail[: next_section.start()] if next_section else tail


def _question_sections(body: str) -> Iterable[tuple[str, str]]:
    matches = list(QUESTION_SECTION_RE.finditer(body))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        next_generic = SECTION_RE.search(body, match.end(), end)
        if next_generic:
            end = next_generic.start()
        yield match.group(0), body[match.end():end]


def audit_text(text: str) -> list[Finding]:
    body = _document_body(text)
    main = _main_text_before_appendix(body)
    findings: list[Finding] = []

    # Structural contract checks.
    if re.search(r"\\section\{结论\}", main):
        findings.append(Finding("review_required", "standalone_conclusion", "中文国赛默认不设置全文独立“结论”一级章。"))
    if re.search(r"\\section\{模型假设与符号说明\}", main):
        findings.append(Finding("review_required", "merged_assumption_symbol_section", "“模型假设”和“符号说明”必须拆成两个独立一级章节。"))
    if re.search(r"(?:^|[\s；;。])(?:H|A)\d+[\.、：:]", _remove_non_prose_blocks(main), flags=re.M):
        findings.append(Finding("review_required", "visible_assumption_contract_id", "正文出现 H1/A1 等内部假设合同编号，应改用 1.、2.、3. 自然编号。"))

    restatement = _section_content(main, "问题重述")
    if restatement is not None:
        if "\\subsection{问题背景}" not in restatement:
            findings.append(Finding("review_required", "missing_problem_background", "“问题重述”缺少“问题背景”小节。"))
        if "\\subsection{问题提出}" not in restatement:
            findings.append(Finding("review_required", "missing_problem_statement", "“问题重述”缺少“问题提出”小节。"))
        if "\\subsection{问题要求}" in restatement:
            findings.append(Finding("review_required", "legacy_problem_requirement", "中文国赛默认使用“问题提出”，不使用“问题要求”作为第二小节。"))

    analysis = _section_content(main, "问题分析")
    if analysis is not None:
        if re.search(r"\\begin\{(?:equation|align|gather)\*?\}|\\\[|\$[^$]+\$", analysis):
            findings.append(Finding("review_required", "formula_in_problem_analysis", "“问题分析”中检测到正式数学公式，应移入模型建立章节。"))

    question_count = 0
    for heading, content in _question_sections(main):
        question_count += 1
        if not re.search(r"\\subsection\{核心模型汇总\}", content):
            findings.append(Finding("review_required", "missing_core_model_summary", f"{heading} 缺少“核心模型汇总”小节。", heading))
        if not re.search(r"\\subsection\{求解结果\}", content):
            findings.append(Finding("warning", "missing_solution_result_section", f"{heading} 未检测到默认“求解结果”小节，请确认是否有题型特定理由。", heading))
    if QUESTION_SECTION_RE.search(main) and question_count == 0:
        findings.append(Finding("warning", "question_section_parse", "检测到问题模型章节但未能完成逐问结构解析。"))

    # Main-text figure/table references: all labelled main-text figures/tables should normally be cited nearby.
    labels = LABEL_RE.findall(main)
    for label in labels:
        occurrences = len(re.findall(re.escape(f"\\label{{{label}}}"), main))
        refs = len(re.findall(REF_TEMPLATE.format(label=re.escape(label)), main))
        if occurrences and refs == 0:
            kind = "图" if label.startswith("fig:") else "表"
            findings.append(Finding("warning", "unreferenced_figure_table", f"正文{kind}标签 {label} 没有显式交叉引用；核心图表应在邻近正文中被解释。", label))

    # Prose-density checks: warnings only, never hard word bans.
    paragraphs = _plain_paragraphs(main)
    contrast_flags = [bool(CONTRAST_RE.search(p)) for p in paragraphs]
    for i in range(max(0, len(contrast_flags) - 2)):
        if all(contrast_flags[i:i + 3]):
            excerpt = " | ".join(p[:45] for p in paragraphs[i:i + 3])
            findings.append(Finding("warning", "consecutive_contrast_paragraphs", "连续 3 个自然段均使用明显否定/转折结构，请确认是否存在真实逻辑冲突；无冲突时改为正向连续叙述。", excerpt))
            break
    for paragraph in paragraphs:
        tokens = CONTRAST_RE.findall(paragraph)
        if len(tokens) >= 3:
            findings.append(Finding("warning", "dense_contrast_paragraph", "单个自然段中否定/转折词较密，请复查是否存在不必要的“先否定再肯定”句法。", paragraph[:120]))
            break

    start_flags = [bool(PARAGRAPH_START_RE.search(p)) for p in paragraphs]
    if len(paragraphs) >= 6 and sum(start_flags) / len(paragraphs) >= 0.35:
        findings.append(Finding("warning", "repeated_paper_subject_start", "“本文/本问/该模型”作为段首主语的比例偏高，建议更多从本题对象、公式或结果事实起句。", f"{sum(start_flags)}/{len(paragraphs)} paragraphs"))
    for i in range(max(0, len(start_flags) - 2)):
        if all(start_flags[i:i + 3]):
            findings.append(Finding("warning", "consecutive_paper_subject_start", "连续 3 段以“本文/本问/该模型”起句，句法同构风险较高。"))
            break

    template_patterns = {
        "本文不是…而是…": re.compile(r"本文不是.{0,60}?而是"),
        "由于…因此本文不能…": re.compile(r"由于.{0,80}?因此本文不能"),
        "不能…只能…": re.compile(r"不能.{0,60}?只能"),
    }
    prose = "\n".join(paragraphs)
    for name, pattern in template_patterns.items():
        count = len(pattern.findall(prose))
        if count >= 2:
            findings.append(Finding("warning", "repeated_negation_template", f"“{name}”结构重复出现 {count} 次，建议改为事实/条件→数学处理→结论边界的正向叙述。", name))

    phrase_limits = {
        "由图可知": 2,
        "由表可知": 2,
        "见表": 4,
        "首先": 3,
        "其次": 3,
        "最后": 3,
    }
    for phrase, limit in phrase_limits.items():
        count = prose.count(phrase)
        if count > limit:
            findings.append(Finding("warning", "repeated_stock_phrase", f"固定短语“{phrase}”出现 {count} 次，超过建议复查阈值 {limit}；请确认是否存在机械句式复用。", phrase))

    return findings


def audit_file(path: Path) -> list[Finding]:
    return audit_text(path.read_text(encoding="utf-8-sig", errors="strict"))


def overall_status(findings: Iterable[Finding]) -> str:
    status = "pass"
    for finding in findings:
        if SEVERITY_ORDER[finding.severity] > SEVERITY_ORDER[status]:
            status = finding.severity
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit final LaTeX prose for HSK writing-contract regressions.")
    parser.add_argument("tex", type=Path, help="LaTeX main file to audit")
    parser.add_argument("--strict", action="store_true", help="Return exit code 1 when review_required findings exist")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    if not args.tex.is_file():
        raise SystemExit(f"LaTeX file not found: {args.tex}")
    findings = audit_file(args.tex)
    status = overall_status(findings)

    if args.json:
        print(json.dumps({"status": status, "findings": [asdict(item) for item in findings]}, ensure_ascii=False, indent=2))
    else:
        print(f"Paper prose audit: {status}")
        for item in findings:
            suffix = f" | {item.evidence}" if item.evidence else ""
            print(f"- [{item.severity}] {item.code}: {item.message}{suffix}")

    return 1 if args.strict and status == "review_required" else 0


if __name__ == "__main__":
    raise SystemExit(main())
