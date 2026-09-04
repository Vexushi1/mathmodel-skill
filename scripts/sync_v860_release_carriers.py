#!/usr/bin/env python3
"""One-shot v8.6.0 release-carrier synchronizer for PR #110.

Temporary maintenance helper: it only updates existing release/version surfaces and
release notes. It does not change modeling, numerical, figure, template or runtime
semantics. Remove this file after the carrier-sync commit is materialized.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = "8.6.0"
PREVIOUS = "8.5.0"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    text = read(path)
    if new in text and old not in text:
        return
    if old not in text:
        raise RuntimeError(f"expected marker missing in {path}: {old!r}")
    write(path, text.replace(old, new, 1))


def set_yaml_top_version(path: str) -> None:
    text = read(path)
    updated, count = re.subn(
        rf"(?m)^version:\s*(?:{re.escape(PREVIOUS)}|{re.escape(TARGET)})\s*$",
        f"version: {TARGET}",
        text,
        count=1,
    )
    if count != 1:
        raise RuntimeError(f"top-level version marker missing in {path}")
    write(path, updated)


def sync_plugin() -> None:
    path = ROOT / ".codex-plugin/plugin.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = TARGET
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sync_skill(path: str) -> None:
    text = read(path)
    text, n1 = re.subn(r"(?m)^version:\s*[^\s]+$", f"version: {TARGET}", text, count=1)
    text, n2 = re.subn(r"(?m)^# HSK 数学建模模块化工作流 v[^\s]+$", f"# HSK 数学建模模块化工作流 v{TARGET}", text, count=1)
    if n1 != 1 or n2 != 1:
        raise RuntimeError(f"Skill version markers missing in {path}")
    write(path, text)


def sync_readme() -> None:
    path = "README.md"
    text = read(path)
    text, count = re.subn(r"^# mathmodel-skill v[^\n]+", f"# mathmodel-skill v{TARGET}", text, count=1)
    if count != 1:
        raise RuntimeError("README heading marker missing")
    heading = "## v8.6.0：Model Construction & Solution Rationale\n"
    if heading not in text:
        anchor = "## v8.5.0：Author Reasoning Voice 细化\n"
        if anchor not in text:
            raise RuntimeError("README v8.5 anchor missing")
        section = (
            heading
            + "\n本次升级在 v8.5 Author Reasoning Voice 基础上，继续强化“为什么这样建模、为什么这样简化、当前结构何时成立、为什么该 solver 在这里适用、关键数值参数为什么这样选”。新增 Model Construction Rationale、Local Applicability、Solver Preconditions、Reduction Provenance-aware prose、Numerical Parameter Rationale、Section Title Minimality 与 Adaptive Subsection Separation。\n\n"
            + "复杂模型允许保留真正有导航价值的短二级/三级标题，简单模型则继续执行 anti-bloat；不设置标题字符数/数量 Hard Rule，不固定“模型适用性分析”小节，不把 A196 的算法、标题或句式变成模板。v8.5 的 Question Closure、Reasoning Necessity、Problem-Specificity、Claim Strength、无代词配额和不推断作者身份边界保持不变。实现与回归记录见 [v8.6 评估记录](docs/v860_model_construction_solution_rationale_evaluation.md)。\n\n"
        )
        text = text.replace(anchor, section + anchor, 1)
    write(path, text)


def sync_changelog() -> None:
    path = "CHANGELOG.md"
    text = read(path)
    marker = f"## Current release: {TARGET}\n"
    if marker not in text:
        old = f"## Current release: {PREVIOUS}\n"
        if old not in text:
            raise RuntimeError("CHANGELOG current-release marker missing")
        text = text.replace(old, marker, 1)
    v860_block = (
        "\n- Added **Model Construction Rationale** so non-trivial model choices recover current structure, modeling gap, chosen mathematical structure, why it closes the gap, applicability conditions and downstream role.\n"
        "- Added local applicability and explicit solver-precondition evidence without fixed applicability sections, algorithm-name inference or generic algorithm praise.\n"
        "- Strengthened `exact / proven_sufficient / heuristic` reduction provenance and evidence-bound language; heuristic scope cannot be promoted to strict equivalence or global optimality.\n"
        "- Added Numerical Parameter Rationale for grid/discretization/step/tolerance choices while preserving the 03A/PQS versus accepted-after-03B boundary.\n"
        "- Added Section Title Minimality and Adaptive Subsection Separation so complex independent tasks may keep short navigation headings while simple argument chains remain compact; no title-count or character Hard Rule was introduced.\n"
        "- Preserved v8.5 Author Reasoning Voice, Claim Strength, Model Approval, numerical/workbook, Figure Evidence and LaTeX/template boundaries; added 12 fixed semantic cases and v8.6 regression coverage.\n"
    )
    if "**Model Construction Rationale**" not in text.split("## 8.5.0", 1)[0]:
        current = marker
        if current not in text:
            raise RuntimeError("CHANGELOG v8.6 current marker missing")
        text = text.replace(current, current + v860_block + "\n## 8.5.0\n", 1)
    write(path, text)


def main() -> None:
    bootstrap_text = read("core/bootstrap.yaml")
    if re.search(rf"(?m)^skill_version:\s*{re.escape(TARGET)}\s*$", bootstrap_text) is None:
        raise RuntimeError(f"bootstrap must already be {TARGET}")

    sync_plugin()
    sync_skill("SKILL.md")
    sync_skill("skills/mathmodel-skill/SKILL.md")
    sync_readme()
    sync_changelog()
    replace_once("core/hsk_core_policy.md", f"# HSK Core Policy v{PREVIOUS}", f"# HSK Core Policy v{TARGET}")
    for path in (
        "core/workflow_router.yaml",
        "core/module_manifest.yaml",
        "core/output_contract.yaml",
        "core/writing_runtime_contract.yaml",
        "config/prose_audit_patterns.yaml",
    ):
        set_yaml_top_version(path)

    if read("SKILL.md") != read("skills/mathmodel-skill/SKILL.md"):
        raise RuntimeError("root/package Skill parity drift after sync")
    print(f"release carriers synchronized to {TARGET}")


if __name__ == "__main__":
    main()
