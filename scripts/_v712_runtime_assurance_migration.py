#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_required(text: str, old: str, new: str, path: str) -> str:
    if old not in text:
        if new in text:
            return text
        raise RuntimeError(f"missing replacement anchor in {path}: {old!r}")
    return text.replace(old, new, 1)


def patch_bootstrap() -> None:
    path = "core/bootstrap.yaml"
    text = read(path)
    text = replace_required(text, "skill_version: 7.11.2", "skill_version: 7.12.0", path)
    text = replace_required(
        text,
        "use scripts/resolve_workflow.py for the task-specific plan.",
        "use scripts/resolve_runtime.py for the assured task-specific plan.",
        path,
    )
    text = replace_required(
        text,
        "  semantic_governance: scripts/validate_semantic_governance.py\n",
        "  semantic_governance: scripts/validate_semantic_governance.py\n  runtime_assurance: core/runtime_assurance_contract.yaml\n",
        path,
    )
    text = replace_required(
        text,
        "  resolver: scripts/resolve_workflow.py",
        "  resolver: scripts/resolve_runtime.py",
        path,
    )
    text = replace_required(
        text,
        "    - Route-specific contracts are loaded only when the resolved task needs them.\n",
        "    - Route-specific contracts are loaded only when the resolved task needs them.\n    - Runtime context hydration, intent provenance, artifact assurance and declarative contract dependency closure are governed by core/runtime_assurance_contract.yaml.\n",
        path,
    )
    text = replace_required(
        text,
        "  resolve: python scripts/resolve_workflow.py\n",
        "  resolve: python scripts/resolve_runtime.py\n  resolve_legacy: python scripts/resolve_workflow.py\n",
        path,
    )
    write(path, text)


def patch_version_carriers() -> None:
    replacements = {
        "core/workflow_router.yaml": ("version: 7.11.2", "version: 7.12.0"),
        "core/module_manifest.yaml": ("version: 7.11.2", "version: 7.12.0"),
        "core/output_contract.yaml": ("version: 7.11.2", "version: 7.12.0"),
        "core/hsk_core_policy.md": ("# HSK Core Policy v7.11.2", "# HSK Core Policy v7.12.0"),
    }
    for path, (old, new) in replacements.items():
        text = read(path)
        write(path, replace_required(text, old, new, path))


def patch_skill() -> None:
    path = "SKILL.md"
    text = read(path)
    text = replace_required(text, "version: 7.11.2", "version: 7.12.0", path)
    text = replace_required(
        text,
        "# HSK 数学建模模块化工作流 v7.11.2",
        "# HSK 数学建模模块化工作流 v7.12.0",
        path,
    )
    text = text.replace("scripts/resolve_workflow.py", "scripts/resolve_runtime.py", 1)
    anchor = "<!-- HSK_RUNTIME_ENTRY_CONTRACT_END -->\n\n"
    addition = (
        "### Declarative Runtime & Assurance\n\n"
        "默认运行时入口升级为 `scripts/resolve_runtime.py`。它在不改变旧 plan 顶层字段的前提下增加 `runtime_plan` 与 `assurance`：可从 current `state/project_state.yaml` 按需恢复 competition、preprocessing decision、单问 classification 与已验证 artifact；所有推断都输出 intent provenance、confidence/ambiguity 诊断，文件型 artifact 只有 accepted 状态、路径和 SHA-256 同时闭合时才可由 project state 自动放行。选中 module/gate 后，再按 `core/runtime_assurance_contract.yaml` 声明补齐必需 contract；`scripts/resolve_workflow.py` 保留为无状态兼容入口。\n\n"
    )
    if addition not in text:
        text = replace_required(text, anchor, anchor + addition, path)
    write(path, text)
    write("skills/mathmodel-skill/SKILL.md", text)


def patch_readme() -> None:
    path = "README.md"
    text = read(path)
    text = replace_required(text, "# mathmodel-skill v7.11.2", "# mathmodel-skill v7.12.0", path)
    section = """## v7.12.0：Declarative Runtime & Assurance\n\n本版本把 v7.11.2 体检中确认的运行时设计债务收口为一个可解释、可验证且向后兼容的 assurance layer；不改变数学模型、Project State Schema、Workbook Schema、每问五文件、Python/MATLAB 职责或 LaTeX/submission provenance。\n\n- 新增默认入口 `scripts/resolve_runtime.py`，旧 `scripts/resolve_workflow.py` 保留为兼容 resolver；Bootstrap 只指向新的 assured runtime。\n- 可选 `--project-root` / `--question` 从 current `state/project_state.yaml` 恢复 competition、preprocessing decision、单问 classification 与 verified artifact availability，显式 CLI/API 参数优先且冲突进入 assurance diagnostics。\n- intent 推断现在记录 matched keywords、deterministic score、confidence band、ambiguity 与 selection reason，不再只返回不可解释的 route 名称。\n- project-state artifact assurance 对 locked model 使用 challenge/approval 与 semantic revision/hash 绑定，对工作簿使用 accepted status + 路径 + SHA-256 闭环；已知 stale/hash mismatch 不能被 legacy name-only artifact 声明静默覆盖。\n- 新增 `core/runtime_assurance_contract.yaml`，声明 selected modules/gates 所需 contract dependencies；runtime 自动补齐缺失 contract，Router 的显式 core loads 只作为兼容提示而不是正确性前提。\n- resolver 输出保留全部旧顶层字段，并增量增加 `runtime_plan` 与 `assurance`，其中 authority fingerprint 绑定 Bootstrap、Router、Manifest 与 Runtime Assurance Contract。\n\n"""
    marker = "## v7.11.2：Runtime Health & Semantic Coherence\n"
    if section not in text:
        text = replace_required(text, marker, section + marker, path)
    write(path, text)


def patch_changelog() -> None:
    path = "CHANGELOG.md"
    text = read(path)
    marker = "## Current release: 7.11.2\n"
    section = """## Current release: 7.12.0\n\n- Added `core/runtime_assurance_contract.yaml` as the single authority for runtime context precedence, intent provenance, artifact assurance, declarative contract dependency closure and authority fingerprinting.\n- Added default state-aware resolver `scripts/resolve_runtime.py`; preserved `scripts/resolve_workflow.py` as the legacy stateless compatibility entrypoint.\n- Added optional project-state hydration for competition, preprocessing decision, scoped classification and verified artifacts without changing Project State Schema or legacy CLI arguments.\n- Added deterministic intent diagnostics with matched keywords, score, confidence band, ambiguity and selection reason.\n- Added file-backed artifact assurance requiring accepted state, existing path and matching SHA-256; stale/hash-mismatched current-state evidence blocks legacy name-only promotion.\n- Added additive `runtime_plan` and `assurance` envelopes while preserving the existing resolver plan fields and task-code execution boundary.\n- Added declarative module/gate contract dependency closure and authority fingerprinting across Bootstrap, Router, Manifest and Runtime Assurance Contract.\n\n## Previous release: 7.11.2\n"""
    if "## Current release: 7.12.0" not in text:
        text = replace_required(text, marker, section, path)
    write(path, text)


def patch_runtime_docs() -> None:
    path = "RUNTIME_ROUTER.md"
    text = read(path)
    text = replace_required(
        text,
        "→ 调用 scripts/resolve_workflow.py\n→ 合并多个意图\n→ 确定 objective / structures / 顶层 capabilities\n→ 加载必要模块、Pack、模板\n",
        "→ 调用 scripts/resolve_runtime.py\n→ [可选] 从 current project state 恢复缺失上下文与 verified artifacts\n→ 合并显式/推断意图并记录 route provenance / confidence / ambiguity\n→ 确定 objective / structures / 顶层 capabilities\n→ 按 selected module/gate 声明补齐必要 contracts，再加载模块、Pack、模板\n",
        path,
    )
    anchor = "## 项目工作记忆\n"
    addition = """## Runtime Assurance\n\n`core/runtime_assurance_contract.yaml` 只管理运行时证明层，不重新定义 Router、Manifest、Model Approval、Workbook 或 User Execution 的业务语义。默认 resolver 保留旧 plan 字段，同时输出 `runtime_plan` 与 `assurance`：context 说明字段来自 explicit input 还是 project state；intent resolution 给出关键词证据与歧义；artifact assurance 记录 scope、accepted/stale 状态、路径和 SHA-256；dependency closure 记录由选中 module/gate 自动补入的 contracts；authority fingerprint 绑定本次计划所依据的四个 Authority 文件。旧 `scripts/resolve_workflow.py` 继续用于无状态兼容调用。\n\n"""
    if addition not in text:
        text = replace_required(text, anchor, addition + anchor, path)
    write(path, text)

    path = "scripts/README.md"
    text = read(path)
    old = "- `resolve_workflow.py`：解析一个或多个用户意图、`objective`、`structures`、`capabilities`、`preprocessing_decision` 与竞赛类型，返回最小确定性 `load_order`、模块计划、Model Approval/用户执行暂停边界与 `pre_delivery_gates`；只有 `project_level` 才插入项目级数据预处理阶段。\n"
    new = "- `resolve_runtime.py`：默认 assured runtime 入口。在兼容旧 plan 字段的基础上，可选读取 `--project-root` / `--question` 恢复 current project state，验证 artifact hash，输出 intent provenance、ambiguity、declarative contract closure、authority fingerprint 与 `runtime_plan/assurance`。\n- `resolve_workflow.py`：保留的无状态兼容 resolver；仍可直接解析显式 intent/classification/artifact-name 输入，但不负责 project-state hydration 或 artifact hash assurance。\n"
    text = replace_required(text, old, new, path)
    write(path, text)


def patch_agent_entrypoints() -> None:
    path = "AGENTS.md"
    text = read(path)
    text = replace_required(
        text,
        "2. Run `scripts/resolve_workflow.py` for one or more intents; do not preload the whole repository.",
        "2. Run `scripts/resolve_runtime.py` for one or more intents; when a current project root is available, pass it so context/artifact assurance can hydrate from project state. `scripts/resolve_workflow.py` is legacy stateless compatibility only; do not preload the whole repository.",
        path,
    )
    write(path, text)

    path = "PROJECT_INSTRUCTIONS.md"
    text = read(path)
    text = replace_required(
        text,
        "2. 使用 `scripts/resolve_workflow.py` 解析一个或多个意图，只加载命中的模块、Pack 和模板；",
        "2. 使用 `scripts/resolve_runtime.py` 解析一个或多个意图；已有项目优先传入 project root，使 runtime 从 current project state 恢复缺失上下文、验证 artifact 并输出 assurance；旧 `scripts/resolve_workflow.py` 仅作无状态兼容入口；只加载命中的合同、模块、Pack 和模板；",
        path,
    )
    write(path, text)

    path = "agents/openai.yaml"
    text = read(path)
    text = text.replace("Use scripts/resolve_workflow.py to resolve one or more intents", "Use scripts/resolve_runtime.py to resolve one or more intents; pass the current project root when available so state/artifact assurance can hydrate context", 1)
    write(path, text)


def patch_plugin() -> None:
    path = ROOT / ".codex-plugin" / "plugin.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = "7.12.0"
    description = str(data.get("description", ""))
    if "state-aware runtime assurance" not in description:
        description = description.replace(
            "HSK lightweight-bootstrap mathematical-modeling workflow with ",
            "HSK lightweight-bootstrap mathematical-modeling workflow with state-aware runtime assurance, ",
            1,
        )
    data["description"] = description
    keywords = list(data.get("keywords", []))
    for keyword in ("runtime-assurance", "state-aware-routing", "artifact-assurance"):
        if keyword not in keywords:
            keywords.append(keyword)
    data["keywords"] = keywords
    if isinstance(data.get("interface"), dict):
        data["interface"]["shortDescription"] = "状态感知路由、独立模型挑战、人工锁模、双阶段Python与交付证明链"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    patch_bootstrap()
    patch_version_carriers()
    patch_skill()
    patch_readme()
    patch_changelog()
    patch_runtime_docs()
    patch_agent_entrypoints()
    patch_plugin()


if __name__ == "__main__":
    main()
