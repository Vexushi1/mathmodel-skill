#!/usr/bin/env python3
"""One-shot v8.7.1 release-carrier synchronization.

Temporary implementation helper. It only updates explicit current-release carriers and
current-health assertions after the v8.7.1 implementation tree has passed the full
pre-release CI matrix. Historical docs and subordinate schema versions are intentionally
left unchanged. Remove this helper before final candidate validation.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_exact(relative: str, old: str, new: str, *, expected: int = 1) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    found = text.count(old)
    if found != expected:
        raise RuntimeError(f"{relative}: expected {expected} occurrence(s) of {old!r}, found {found}")
    path.write_text(text.replace(old, new), encoding="utf-8")


# Active release carriers.
replace_exact(".codex-plugin/plugin.json", '"version": "8.7.0"', '"version": "8.7.1"')
replace_exact("core/bootstrap.yaml", "skill_version: 8.7.0", "skill_version: 8.7.1")
replace_exact("core/hsk_core_policy.md", "# HSK Core Policy v8.7.0", "# HSK Core Policy v8.7.1")
replace_exact("core/module_manifest.yaml", "version: 8.7.0", "version: 8.7.1")
replace_exact("core/output_contract.yaml", "version: 8.7.0", "version: 8.7.1")
replace_exact("core/workflow_router.yaml", "version: 8.7.0", "version: 8.7.1")
replace_exact("core/writing_runtime_contract.yaml", "version: 8.7.0", "version: 8.7.1")
replace_exact("config/prose_audit_patterns.yaml", "version: 8.7.0", "version: 8.7.1")
replace_exact(
    "modules/05_writing/paper_writing_protocol.md",
    "# Module 05A：Paper Writing Protocol（v8.7.0）",
    "# Module 05A：Paper Writing Protocol（v8.7.1）",
)

for relative in ("SKILL.md", "skills/mathmodel-skill/SKILL.md"):
    replace_exact(relative, "version: 8.7.0", "version: 8.7.1")
    replace_exact(
        relative,
        "# HSK 数学建模模块化工作流 v8.7.0",
        "# HSK 数学建模模块化工作流 v8.7.1",
    )

# README keeps the repository overview before release sections and preserves v8.7.0 history.
replace_exact("README.md", "# mathmodel-skill v8.7.0", "# mathmodel-skill v8.7.1")
readme_patch = """## v8.7.1：Read-Path & Semantic-State Consistency Hardening

本补丁不新增模型、solver、数值或论文写作能力，而是收口 v8.7.0 已发布能力的读取路径与状态一致性：终审模板版本改为从 current Bootstrap hydration；Module 02 Formula Trace 显式生产 `对应小问 + Role`；Proposition / Proof 增加 question-scoped 确定性状态派生；逐问 Writing Capability Preflight 获得行为级 framework validator 强制。

同时，critical active Authority pointer lint 已从“只检查文件存在”升级为 fragment-level health，兼容 Markdown heading、YAML dotted/dynamic path、JSON Pointer 与现有 composite semantic pointer；LaTeX Adapter/模板中的旧 release 号改为明确 provenance；Writing Reasoning `schema_version: 1.8.0` 被正式定义为 parser/migration compatibility family，纯 additive semantic nodes 不机械 bump。本补丁不修改 Project State Schema、Model Approval、03A/03B、Workbook、Figure、MATLAB、目录或公共 CLI 语义。

"""
old_readme_heading = "## v8.7.0：Per-Question Writing Capability Preflight\n\n"
replace_exact("README.md", old_readme_heading, readme_patch + old_readme_heading)

# CHANGELOG preserves the full v8.7.0 release body as historical evidence.
changelog_patch = """## Current release: 8.7.1

- Removed historical Skill-version pinning from the active final-review template; completed matrices hydrate the current version from Bootstrap while unhydrated templates still fail closed in the scorer.
- Closed the Module 02 Formula Trace producer/consumer gap by carrying explicit question and Formula Role fields into the current framework without duplicating the role taxonomy.
- Defined deterministic question-scoped Proposition / Proof derivation across global plan, proposition items and framework preflight, preserving missing/stale/review-required semantics without changing Project State Schema.
- Added behavior-level framework validation for mandatory Per-Question Writing Capability Preflight, including Formula Role/Trace consistency and current Algorithm Trace requirements.
- Added fragment-level health validation for critical active Authority pointers, covering Markdown headings, YAML dotted/dynamic paths, JSON Pointer and existing composite semantic pointers.
- Clarified active old-release labels as architecture provenance rather than current-version carriers and preserved protected Adapter/template semantics through normalization-based regression tests.
- Kept `writing_reasoning_contract.yaml` at schema family `1.8.0` and documented that additive semantic nodes do not bump parser/migration compatibility versions.

## Previous release: 8.7.0

"""
replace_exact("CHANGELOG.md", "## Current release: 8.7.0\n\n", changelog_patch)

# Current release-health assertions only; historical versioned evaluations remain untouched.
replace_exact("tests/test_current_skill_health.py", "8.7.0", "8.7.1", expected=5)
replace_exact(
    "tests/test_v840_author_reasoning_writing.py",
    'self.assertEqual(runtime["version"], "8.7.0")',
    'self.assertEqual(runtime["version"], "8.7.1")',
)

# Close the approved Scope Contract without rewriting its historical baseline/current-at-planning facts.
replace_exact(
    "docs/v871_readpath_semantic_state_consistency_hardening_plan.md",
    "> 状态：**审批前 / Plan Only / Implementation Not Started**  ",
    "> 状态：**APPROVED / Implementation Complete / Release Candidate Validation**  ",
)
replace_exact(
    "docs/v871_readpath_semantic_state_consistency_hardening_plan.md",
    "> 当前阶段禁止：修改实际 runtime 语义、升级 release carriers、修改 generated hashes、合并 PR。",
    "> 当前阶段边界：runtime implementation 已完成并通过 pre-release 11-job CI；release carriers 可按本 Scope Contract 同步；generated hashes 仍只由 generator 管理；PR 合并仍需用户单独明确批准。",
)

root_skill = (ROOT / "SKILL.md").read_bytes()
packaged_skill = (ROOT / "skills/mathmodel-skill/SKILL.md").read_bytes()
if root_skill != packaged_skill:
    raise RuntimeError("root/package SKILL parity broke during v8.7.1 release sync")

reasoning = (ROOT / "core/writing_reasoning_contract.yaml").read_text(encoding="utf-8")
if not reasoning.startswith("schema_version: 1.8.0\n"):
    raise RuntimeError("writing reasoning schema family must remain 1.8.0 for v8.7.1")

print("v8.7.1 release carriers synchronized; generated metadata still pending generator refresh")
