#!/usr/bin/env python3
"""One-shot v8.7.0 release-carrier synchronizer for PR #114.

This helper is intentionally narrow and idempotent. It updates only active release
carriers/current-version assertions plus the v8.7 README/CHANGELOG release note.
Historical v8.6.1 records are deliberately untouched. Remove this helper before the
PR becomes review-ready.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = "8.6.1"
NEW = "8.7.0"


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def write(relative: str, text: str) -> None:
    (ROOT / relative).write_text(text, encoding="utf-8")


def replace_once(relative: str, old: str, new: str) -> None:
    text = read(relative)
    if new in text and old not in text:
        return
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{relative}: expected exactly one marker {old!r}, found {count}")
    write(relative, text.replace(old, new, 1))


def replace_all_exact(relative: str, old: str, new: str, *, minimum: int = 1) -> None:
    text = read(relative)
    if old not in text:
        if new in text:
            return
        raise RuntimeError(f"{relative}: marker {old!r} not found")
    count = text.count(old)
    if count < minimum:
        raise RuntimeError(f"{relative}: expected >= {minimum} markers, found {count}")
    write(relative, text.replace(old, new))


def git_blob_sha(relative: str) -> str:
    data = (ROOT / relative).read_bytes()
    payload = b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    return hashlib.sha1(payload).hexdigest()


def update_skill_entrypoints() -> None:
    root = read("SKILL.md")
    if "version: 8.7.0" not in root:
        root = root.replace("version: 8.6.1", "version: 8.7.0", 1)
    root = root.replace(
        "# HSK 数学建模模块化工作流 v8.6.1",
        "# HSK 数学建模模块化工作流 v8.7.0",
        1,
    )
    root = root.replace(
        "Template-First paper authoring with final-order Cross-File Chapter Handoff",
        "Template-First paper authoring with state-driven per-question writing capability preflight and final-order Cross-File Chapter Handoff",
        1,
    )
    if "version: 8.7.0" not in root or "v8.7.0" not in root:
        raise RuntimeError("SKILL.md v8.7 markers were not applied")
    write("SKILL.md", root)
    write("skills/mathmodel-skill/SKILL.md", root)


def update_readme() -> None:
    path = "README.md"
    text = read(path)
    text = text.replace("# mathmodel-skill v8.6.1", "# mathmodel-skill v8.7.0", 1)
    text = text.replace(
        "Template-First 逐章读取/写入 → final-order Cross-File Chapter Handoff",
        "Template-First 逐章读取/写入 + 每问 Writing Capability Preflight → final-order Cross-File Chapter Handoff",
        1,
    )
    heading = "## v8.7.0：Per-Question Writing Capability Preflight\n"
    if heading not in text:
        anchor = "## v8.6.1：Active Consistency & Semantic Drift Hardening\n"
        if anchor not in text:
            raise RuntimeError("README v8.6.1 section anchor missing")
        section = (
            "## v8.7.0：Per-Question Writing Capability Preflight\n\n"
            "本版本把逐问写作从“能力存在但需要用户再次提醒”推进到 **capability discovery + state-driven activation**。"
            "每写 Qx 前，CUMCM Compact Runtime 先读取当前项目事实并裁决 Formula Roles、Core Model Summary、"
            "Proposition / Proof 与 Algorithm Presentation；`required / planned / current / stepwise / pseudocode` 即使未在本轮 prompt 再次出现，也必须按状态激活对应能力。"
            "`missing` 不得静默降级为 `not_applicable / not_needed`，`stale` 不得直接写成 current。\n\n"
            "Formula Trace 新增 `final_model_relation / key_bridge_relation / supporting_derivation / routine_algebra` 四级角色。"
            "最终模型汇总以 Final Relations 为主体，只在恢复最终关系、关键边界、降维或 solver precondition 确有需要时纳入少量 Key Bridge Relations；"
            "因此既防止把必要中间式压没，也不把 summary 退化成公式大全。planned/current 命题自动读取证明 Pack，candidate 只触发必要性审查；"
            "stepwise/pseudocode 自动读取 Algorithm Pack，而 `not_needed` 保持关闭。完整 reasoning Authority 与深层 Packs 仍不在普通 CUMCM 写作开篇 eager preload。\n\n"
            "本次升级不强制每问设置“核心模型汇总”小节、不强制命题或伪代码，也不改变 Model Approval、03A/03B、用户执行、Workbook、"
            "Primary Numerical Verification、Figure Evidence 或正式 LaTeX delivery 边界。实现与固定行为试验见 "
            "[v8.7 评估记录](docs/v870_question_writing_capability_preflight_evaluation.md)。\n\n"
        )
        text = text.replace(anchor, section + anchor, 1)
    write(path, text)


def update_changelog() -> None:
    path = "CHANGELOG.md"
    text = read(path)
    current = "## Current release: 8.6.1\n"
    new_heading = "## Current release: 8.7.0\n"
    if new_heading not in text:
        if current not in text:
            raise RuntimeError("CHANGELOG current 8.6.1 heading missing")
        release = (
            "## Current release: 8.7.0\n\n"
            "- Added mandatory **Per-Question Writing Capability Preflight** for CUMCM Template-First writing so current Formula Roles, Core Model Summary, Proposition/Proof and Algorithm Presentation states are consumed before each question body without relying on repeated user keywords.\n"
            "- Added `final_model_relation / key_bridge_relation / supporting_derivation / routine_algebra` Formula Roles; necessary bridge relations survive derivation/cleanup while summaries remain Final-first and avoid formula dumps.\n"
            "- Added state-driven Proposition and Algorithm activation: planned/current proof work and stepwise/pseudocode load their conditional resources; candidate proposition signals review only, `not_needed` stays compact, and missing/stale states fail closed.\n"
            "- Exposed current Formula Role, Core Model Summary and per-question preflight pointers through Output Contract and persisted only compact project-specific activation state in `模型论文框架.md`.\n"
            "- Expanded behavior fixtures, resolver projection coverage and six fixed writing-surface trials while preserving v8.5 Author Reasoning Voice, v8.6 Model Construction Rationale, simple-problem anti-bloat and Compact Runtime conditional loading.\n"
            "- Preserved Model Approval, 03A/03B, user execution, Workbook/Project State, numerical verification, Figure Evidence and formal LaTeX delivery semantics.\n\n"
            "## Previous release: 8.6.1\n"
        )
        text = text.replace(current, release, 1)
    write(path, text)


def update_core_policy() -> None:
    path = "core/hsk_core_policy.md"
    text = read(path)
    text = text.replace("# HSK Core Policy v8.6.1", "# HSK Core Policy v8.7.0", 1)
    text = text.replace(
        "逐章读取/写入时机以 `core/writing_runtime_contract.yaml#template_first_progressive_authoring` 为准",
        "逐章读取/写入时机及逐问 Writing Capability Preflight 以 `core/writing_runtime_contract.yaml` 为准",
        1,
    )
    write(path, text)


def update_protocol_and_snapshot() -> None:
    protocol = "modules/05_writing/paper_writing_protocol.md"
    text = read(protocol)
    text = text.replace(
        "# Module 05A：Paper Writing Protocol（v8.6.1）",
        "# Module 05A：Paper Writing Protocol（v8.7.0）",
        1,
    )
    write(protocol, text)
    digest = git_blob_sha(protocol)

    test_path = "tests/test_v830_editable_mechanism_diagram.py"
    test = read(test_path)
    pattern = re.compile(
        r'(\"modules/05_writing/paper_writing_protocol\.md\": \" )[0-9a-f]{40}(\",)'
    )
    # The actual source has no space inside the quoted digest; use a simpler exact capture.
    pattern = re.compile(
        r'(\"modules/05_writing/paper_writing_protocol\.md\": \"?)([0-9a-f]{40})(\"?,)'
    )
    match = pattern.search(test)
    if not match:
        raise RuntimeError("protected protocol snapshot entry missing")
    test = test[: match.start(2)] + digest + test[match.end(2) :]
    write(test_path, test)


def update_version_tests() -> None:
    replace_all_exact(
        "tests/test_current_skill_health.py",
        "8.6.1",
        "8.7.0",
        minimum=4,
    )
    path = "tests/test_v840_author_reasoning_writing.py"
    text = read(path)
    old = 'self.assertEqual(runtime["version"], "8.6.1")'
    new = 'self.assertEqual(runtime["version"], "8.7.0")'
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise RuntimeError("v840 runtime-version assertion missing")
    write(path, text)


def main() -> int:
    # Machine-readable/current release carriers.
    replace_once("core/bootstrap.yaml", "skill_version: 8.6.1", "skill_version: 8.7.0")
    replace_once("core/workflow_router.yaml", "version: 8.6.1", "version: 8.7.0")
    replace_once("core/module_manifest.yaml", "version: 8.6.1", "version: 8.7.0")
    replace_once("core/output_contract.yaml", "version: 8.6.1", "version: 8.7.0")
    replace_once("core/writing_runtime_contract.yaml", "version: 8.6.1", "version: 8.7.0")
    replace_once("config/prose_audit_patterns.yaml", "version: 8.6.1", "version: 8.7.0")

    plugin_path = ".codex-plugin/plugin.json"
    plugin = json.loads(read(plugin_path))
    plugin["version"] = NEW
    write(plugin_path, json.dumps(plugin, ensure_ascii=False, indent=2) + "\n")

    update_skill_entrypoints()
    update_readme()
    update_changelog()
    update_core_policy()
    update_protocol_and_snapshot()
    update_version_tests()

    # Release-scope sanity checks. Historical v8.6.1 docs are intentionally excluded.
    required_new = [
        "core/bootstrap.yaml",
        "core/workflow_router.yaml",
        "core/module_manifest.yaml",
        "core/output_contract.yaml",
        "core/writing_runtime_contract.yaml",
        "config/prose_audit_patterns.yaml",
        ".codex-plugin/plugin.json",
        "SKILL.md",
        "skills/mathmodel-skill/SKILL.md",
        "README.md",
        "CHANGELOG.md",
        "core/hsk_core_policy.md",
        "modules/05_writing/paper_writing_protocol.md",
        "tests/test_current_skill_health.py",
        "tests/test_v840_author_reasoning_writing.py",
    ]
    for relative in required_new:
        if NEW not in read(relative):
            raise RuntimeError(f"{relative}: v8.7.0 marker missing after sync")
    if read("SKILL.md") != read("skills/mathmodel-skill/SKILL.md"):
        raise RuntimeError("root/package SKILL parity lost")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
