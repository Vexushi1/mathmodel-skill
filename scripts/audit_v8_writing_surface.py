#!/usr/bin/env python3
"""Conservative v8 surface audit for paper prose.

This complements, rather than replaces, audit_paper_prose.py. It only locates v8-specific
surface risks introduced by the Template-First writing refactor and never infers mathematical
correctness, model validity, solver optimality, causal validity, or evidence sufficiency.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import yaml

ROOT = Path(__file__).resolve().parents[1]
PATTERN_PATH = ROOT / "config" / "prose_audit_patterns.yaml"


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    evidence: str = ""


def load_policy(path: Path = PATTERN_PATH) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def strip_comments_and_blocks(text: str) -> str:
    lines = []
    for line in text.splitlines():
        out = []
        escaped = False
        for char in line:
            if char == "%" and not escaped:
                break
            out.append(char)
            escaped = char == "\\" and not escaped
            if char != "\\":
                escaped = False
        lines.append("".join(out))
    prose = "\n".join(lines)
    for env in ("verbatim", "lstlisting", "minted", "equation", "equation*", "align", "align*", "gather", "gather*"):
        prose = re.sub(
            rf"\\begin\{{{re.escape(env)}\}}.*?\\end\{{{re.escape(env)}\}}",
            " ", prose, flags=re.S,
        )
    prose = re.sub(r"\\\[.*?\\\]|\$\$.*?\$\$|\$[^$]*\$", " ", prose, flags=re.S)
    return prose


def plain_paragraphs(text: str) -> list[str]:
    prose = strip_comments_and_blocks(text)
    prose = re.sub(r"\\(?:section|subsection|subsubsection|paragraph)\*?\{[^{}]*\}", "\n\n", prose)
    prose = re.sub(r"\\(?:label|ref|eqref|cite|citep|citet|parencite|textcite)\*?(?:\[[^\]]*\])?\{[^{}]*\}", " ", prose)
    prose = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?", " ", prose)
    return [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", prose) if p.strip()]


def audit_workflow_vocabulary(text: str, policy: dict) -> list[Finding]:
    settings = policy.get("workflow_vocabulary", {}) or {}
    prose = strip_comments_and_blocks(text)
    findings = []
    for term in settings.get("terms", []):
        if term and term in prose:
            findings.append(Finding(
                settings.get("severity", "warning"),
                "workflow_vocabulary_leak",
                settings.get("message", "正文出现内部项目治理词。"),
                term,
            ))
    return findings


def audit_decorative_quotes(text: str, policy: dict) -> list[Finding]:
    settings = policy.get("decorative_chinese_quotes", {}) or {}
    threshold = int(settings.get("min_occurrences", 3))
    findings = []
    for paragraph in plain_paragraphs(text):
        count = len(re.findall(r"“[^”\n]{1,24}”", paragraph))
        if count >= threshold:
            findings.append(Finding(
                settings.get("severity", "warning"),
                "decorative_quote_density",
                "同一段普通概念使用中文引号较密；请人工确认是否属于必要引语、正式名称或题面原文。",
                paragraph[:180],
            ))
    return findings


def audit_concept_chains(text: str, policy: dict) -> list[Finding]:
    settings = policy.get("concept_chain", {}) or {}
    min_links = int(settings.get("min_links", 3))
    findings = []
    # Require short Chinese/Latin concept tokens on both sides. Numeric ranges and equations are excluded.
    token = r"[A-Za-z\u4e00-\u9fff][A-Za-z0-9\u4e00-\u9fff]{0,12}"
    chain = re.compile(rf"{token}(?:\s*[-–—]\s*{token}){{{min_links},}}")
    for paragraph in plain_paragraphs(text):
        match = chain.search(paragraph)
        if match:
            findings.append(Finding(
                settings.get("severity", "warning"),
                "concept_chain_density",
                "检测到较长概念连接符链；请确认它是否只是标签化包装，必要时改成自然句子关系。",
                match.group(0)[:180],
            ))
    return findings


def audit_result_validation_bridge(text: str, policy: dict) -> list[Finding]:
    settings = policy.get("narrative_jump", {}) or {}
    findings = []
    result_match = re.search(r"\\subsection\{[^{}]*(?:求解结果|结果分析|主要结果)[^{}]*\}", text)
    validation_match = re.search(r"\\subsection\{[^{}]*(?:敏感性|鲁棒性|稳定性|验证|检验)[^{}]*\}", text)
    if not result_match or not validation_match or validation_match.start() <= result_match.end():
        return findings
    gap = text[result_match.end():validation_match.start()]
    bridge_hints = re.compile(r"仍|影响|扰动|风险|稳定|可靠|边界|敏感|验证|检验|一致性|误差|不确定")
    if len(re.sub(r"\\[^\n]+", "", gap).strip()) < 40 or not bridge_hints.search(gap):
        findings.append(Finding(
            settings.get("severity", "review_required"),
            "result_validation_bridge_risk",
            "主结果后进入独立验证段，但邻近文本未明显说明待检验风险；请人工确认 Result → Validation bridge 是否闭合。",
            re.sub(r"\s+", " ", gap)[:180],
        ))
    return findings


def audit_text(text: str, policy: dict | None = None) -> list[Finding]:
    policy = policy or load_policy()
    findings = []
    findings.extend(audit_workflow_vocabulary(text, policy))
    findings.extend(audit_decorative_quotes(text, policy))
    findings.extend(audit_concept_chains(text, policy))
    findings.extend(audit_result_validation_bridge(text, policy))
    return findings


def overall_status(findings: Iterable[Finding]) -> str:
    order = {"pass": 0, "warning": 1, "review_required": 2, "blocking": 3}
    level = max((order.get(item.severity, 1) for item in findings), default=0)
    return {value: key for key, value in order.items()}[level]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tex", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    text = args.tex.read_text(encoding="utf-8")
    findings = audit_text(text)
    payload = {
        "status": overall_status(findings),
        "findings": [asdict(item) for item in findings],
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload["status"])
        for item in findings:
            print(f"[{item.severity}] {item.code}: {item.message} :: {item.evidence}")
    return 1 if payload["status"] in {"review_required", "blocking"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
