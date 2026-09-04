from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = "8.6.0"
NEW = "8.6.1"


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def write(relative: str, text: str) -> None:
    (ROOT / relative).write_text(text, encoding="utf-8")


def replace_once(relative: str, old: str, new: str) -> None:
    text = read(relative)
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{relative}: expected one match, got {count}: {old!r}")
    write(relative, text.replace(old, new, 1))


def replace_all_checked(relative: str, old: str, new: str, expected: int) -> None:
    text = read(relative)
    count = text.count(old)
    if count != expected:
        raise RuntimeError(f"{relative}: expected {expected} matches, got {count}: {old!r}")
    write(relative, text.replace(old, new))


# Canonical release carriers.
replace_once("core/bootstrap.yaml", "skill_version: 8.6.0", "skill_version: 8.6.1")
for relative in (
    "core/workflow_router.yaml",
    "core/module_manifest.yaml",
    "core/output_contract.yaml",
    "core/writing_runtime_contract.yaml",
    "config/prose_audit_patterns.yaml",
):
    replace_once(relative, "version: 8.6.0", "version: 8.6.1")
replace_once(
    ".codex-plugin/plugin.json",
    '"version": "8.6.0"',
    '"version": "8.6.1"',
)
replace_once("core/hsk_core_policy.md", "# HSK Core Policy v8.6.0", "# HSK Core Policy v8.6.1")
replace_once(
    "modules/05_writing/paper_writing_protocol.md",
    "# Module 05A：Paper Writing Protocol（v8.6.0）",
    "# Module 05A：Paper Writing Protocol（v8.6.1）",
)

# Root/package entrypoints must remain byte-identical.
for relative in ("SKILL.md", "skills/mathmodel-skill/SKILL.md"):
    replace_once(relative, "version: 8.6.0", "version: 8.6.1")
    replace_once(
        relative,
        "# HSK 数学建模模块化工作流 v8.6.0",
        "# HSK 数学建模模块化工作流 v8.6.1",
    )
if read("SKILL.md") != read("skills/mathmodel-skill/SKILL.md"):
    raise RuntimeError("root/package SKILL parity broken")

# README: current header + patch note; preserve the v8.6.0 historical section intact.
replace_once("README.md", "# mathmodel-skill v8.6.0", "# mathmodel-skill v8.6.1")
readme_marker = "## v8.6.0：Model Construction & Solution Rationale"
readme_section = """## v8.6.1：Active Consistency & Semantic Drift Hardening

本补丁不新增模型、solver、数值或论文写作能力，而是收口 v8.6.0 合并后通读发现的 current-state 与语义漂移风险：v8.6 evaluation 现在同时保留候选阶段失败记录与最终 merged/released/post-merge-CI 状态，v8.4/v8.5 evaluation 明确标记为历史非 Authority 快照；CHANGELOG release heading 统一为可机读格式。

CUMCM canonical example 中的四个常见问题内标题现在明确只是 maintained LaTeX smoke/profile，不是 runtime 固定标题或固定小节数量；A196 继续保留 provenance 与 chapter-topology 参考，但显式隔离于当前写作语义、模型/solver 选择和问题内标题 Authority。`core/output_contract.yaml` 补齐 v8.6 reasoning capability 的命名指针，`RUNTIME_ROUTER.md` 明确 raw declarative candidate surface 与 resolver effective plan 的区别。Model Approval、03A/03B、Workbook、Project State、用户执行、Figure Evidence、LaTeX 编译职责和 v8.6 建模写作语义均保持不变。

"""
text = read("README.md")
if text.count(readme_marker) != 1:
    raise RuntimeError("README v8.6 marker not unique")
write("README.md", text.replace(readme_marker, readme_section + readme_marker, 1))

# Changelog: patch becomes current; existing v8.6 bullets remain under Previous release.
changelog_marker = "## Current release: 8.6.0"
changelog_section = """## Current release: 8.6.1

- Closed v8.6 release-state drift by separating final merged/post-merge-CI facts from preserved candidate-stage evaluation history; older v8.4/v8.5 evaluation documents are explicitly historical non-Authority records.
- Clarified that CUMCM fixed four-heading checks are maintained example/compile smoke only; runtime subsection structure remains adaptive and has no fixed heading count or title-length rule.
- Isolated A196/reference provenance from runtime writing semantics, internal subsection decisions and model/solver selection while retaining chapter-topology provenance.
- Added named `output_contract` pointers for Model Construction Rationale and Numerical Parameter Evidence without duplicating their reasoning rules.
- Clarified raw declarative route/module output surfaces versus resolver-returned effective plans, preserving all existing Model Approval, preprocessing and user-execution boundaries.
- Normalized historical release headings and added regression coverage; no model mathematics, 03A/03B, workbook/project-state schema, figure ownership, CLI or public runtime field was changed.

## Previous release: 8.6.0"""
replace_once("CHANGELOG.md", changelog_marker, changelog_section)

# Current-release tests and one release-carrier assertion.
replace_all_checked("tests/test_current_skill_health.py", "8.6.0", "8.6.1", 6)
replace_once(
    "tests/test_v840_author_reasoning_writing.py",
    'self.assertEqual(runtime["version"], "8.6.0")',
    'self.assertEqual(runtime["version"], "8.6.1")',
)

# Scope-contract status: implementation complete, final release CI still required.
plan = "docs/v861_active_consistency_semantic_drift_hardening_plan.md"
replace_once(
    plan,
    "> 状态：用户已批准实施 / implementation in progress  ",
    "> 状态：实现与版本同步完成 / final release CI pending  ",
)
text = read(plan)
anchor = "implementation_started = true\n"
if text.count(anchor) != 1:
    raise RuntimeError("plan implementation_started anchor missing")
text = text.replace(
    anchor,
    anchor + "semantic_patch_ci = HSK Skill CI #2411 success\nrelease_sync = complete\nfinal_release_ci = pending\n",
    1,
)
write(plan, text)

# Sanity: active current carriers must not retain OLD in their current-version positions.
checks = {
    "core/bootstrap.yaml": "skill_version: 8.6.1",
    "core/workflow_router.yaml": "version: 8.6.1",
    "core/module_manifest.yaml": "version: 8.6.1",
    "core/output_contract.yaml": "version: 8.6.1",
    "core/writing_runtime_contract.yaml": "version: 8.6.1",
    "config/prose_audit_patterns.yaml": "version: 8.6.1",
    ".codex-plugin/plugin.json": '"version": "8.6.1"',
    "core/hsk_core_policy.md": "# HSK Core Policy v8.6.1",
    "modules/05_writing/paper_writing_protocol.md": "Paper Writing Protocol（v8.6.1）",
    "README.md": "# mathmodel-skill v8.6.1",
    "CHANGELOG.md": "## Current release: 8.6.1",
}
for relative, token in checks.items():
    if token not in read(relative):
        raise RuntimeError(f"release sync failed: {relative}: {token}")

print("v8.6.1 release carriers synchronized")
