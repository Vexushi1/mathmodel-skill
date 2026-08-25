#!/usr/bin/env python3
"""One-shot migration for v7.11.2 runtime-health semantic coherence."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    (ROOT / rel).write_text(text, encoding="utf-8", newline="\n")


def replace_once(rel: str, old: str, new: str) -> None:
    text = read(rel)
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected one replacement in {rel}, found {count}: {old[:80]!r}")
    write(rel, text.replace(old, new, 1))


# Release carriers.
replace_once("core/bootstrap.yaml", "skill_version: 7.11.1", "skill_version: 7.11.2")
replace_once("core/workflow_router.yaml", "version: 7.11.1", "version: 7.11.2")
replace_once("core/module_manifest.yaml", "version: 7.11.1", "version: 7.11.2")
replace_once("core/output_contract.yaml", "version: 7.11.1", "version: 7.11.2")
replace_once("core/hsk_core_policy.md", "# HSK Core Policy v7.11.1", "# HSK Core Policy v7.11.2")

plugin_path = ROOT / ".codex-plugin/plugin.json"
plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
if plugin.get("version") != "7.11.1":
    raise RuntimeError(f"unexpected plugin version: {plugin.get('version')}")
plugin["version"] = "7.11.2"
keywords = list(plugin.get("keywords", []))
for item in ("problem-audit", "model-design", "workflow-routing"):
    if item not in keywords:
        keywords.append(item)
plugin["keywords"] = keywords
plugin_path.write_text(json.dumps(plugin, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Entrypoint discoverability and lifecycle summary. Root is edited, packaged copy is regenerated from it.
replace_once("SKILL.md", "version: 7.11.1", "version: 7.11.2")
replace_once("SKILL.md", "# HSK 数学建模模块化工作流 v7.11.1", "# HSK 数学建模模块化工作流 v7.11.2")
old_triggers = "triggers: [数学建模, 数模, CUMCM, 国赛, MCM, ICM, 电工杯, 认证杯, 建模论文, 模型论文框架, 模型锁定, 模型审查, 算法流程, 伪代码, 数据预处理, 数据清洗, 主结果质量, 结果深化分析, Python求解, MATLAB绘图, LaTeX, DOCX]"
new_triggers = "triggers: [数学建模, 数模, CUMCM, 国赛, MCM, ICM, 电工杯, 认证杯, 审题, 问题分析, 建模思路, 建模方案, 模型比较, 完整求解, 全流程, 建模论文, 模型论文框架, 模型锁定, 模型审查, 算法流程, 伪代码, 数据预处理, 数据清洗, 主结果质量, 结果分析, 结果深化分析, Python求解, MATLAB绘图, LaTeX, DOCX, 终审, 提交包]"
replace_once("SKILL.md", old_triggers, new_triggers)
old_default = "先读 `core/bootstrap.yaml`，再由 `scripts/resolve_workflow.py` 按任务加载最小模块集。Problem Contract 冻结后先完成数据审计与 `preprocessing_decision`、题面—数学—代码—输出语义闭环和 Complexity Sanity Check，再执行独立 Model Reviewer 与 Devil's Advocate 两次 Model Challenge。Challenge 通过后生成 Model Approval Brief，并停在 `awaiting_model_approval`；只有用户明确批准当前 `semantic_revision/hash` 后才形成 current `locked_model_spec`。正式项目级预处理或主求解代码前还必须通过 `scripts/validate_semantic_governance.py` 与 `scripts/validate_model_approval.py`。"
new_default = "先读 `core/bootstrap.yaml`，再由 `scripts/resolve_workflow.py` 按任务加载最小模块集。Problem Contract 冻结后先完成非破坏性数据审计与模型路线/数据需求比较，随后锁定 `preprocessing_decision`，再完成题面—数学—代码—输出语义闭环和 Complexity Sanity Check；达到设计完整性后形成 `proposed_model_spec`，再执行独立 Model Reviewer 与 Devil's Advocate 两次 Model Challenge。Challenge 通过后生成 Model Approval Brief，并停在 `awaiting_model_approval`；只有用户明确批准当前 `semantic_revision/hash` 后才形成 current `locked_model_spec`。正式项目级预处理或主求解代码前还必须按 resolver 返回顺序通过 `scripts/validate_semantic_governance.py` 与 `scripts/validate_model_approval.py`。"
replace_once("SKILL.md", old_default, new_default)
old_chain = """逐字审题 → Problem Contract冻结
→ 通用数据审计 → preprocessing_decision
→ 两条模型路线 → 变量/假设/公式/约束闭合
→ 结构化简 → Algorithm Trace/呈现模式按需确定
→ 题面—数学—代码—输出语义闭环 → Complexity Sanity Check
→ Model Reviewer + Devil's Advocate → Model Challenge passed
→ Model Approval Brief → awaiting_model_approval
→ 用户明确批准 current semantic revision/hash → locked_model_spec"""
new_chain = """逐字审题 → Problem Contract冻结
→ 通用数据审计 → 两条模型路线与数据需求比较
→ preprocessing_decision
→ 变量/假设/公式/约束闭合 → 结构化简
→ Algorithm Trace/呈现模式按需确定
→ 题面—数学—代码—输出语义闭环 → Complexity Sanity Check
→ proposed_model_spec
→ Model Reviewer + Devil's Advocate → Model Challenge passed
→ Model Approval Brief → awaiting_model_approval
→ 用户明确批准 current semantic revision/hash → locked_model_spec"""
replace_once("SKILL.md", old_chain, new_chain)
write("skills/mathmodel-skill/SKILL.md", read("SKILL.md"))

# Runtime human-readable lifecycle: decision is a model-design semantic input, not a post-approval step.
old_runtime = """problem_audit
→ model_design
   ├─ Formula Trace / 结构化简
   ├─ Algorithm Trace：not_needed / stepwise / pseudocode
   ├─ Complexity Sanity
   └─ proposed_model_spec
→ Model Reviewer
→ Devil's Advocate
→ Model Challenge passed
→ Model Approval Brief
→ awaiting_model_approval
→ 用户明确批准当前 semantic revision/hash
→ locked_model_spec
→ preprocessing_decision
   ├─ not_needed     ───────────────────────────────┐
   ├─ question_local ───────────────────────────────┤
   └─ project_level → data_preprocessing            │"""
new_runtime = """problem_audit
→ model_design
   ├─ 非破坏性数据审计 + 两条模型路线/数据需求比较
   ├─ preprocessing_decision
   ├─ Formula Trace / 结构化简
   ├─ Algorithm Trace：not_needed / stepwise / pseudocode
   ├─ Semantic Closure / Complexity Sanity
   └─ proposed_model_spec
→ Model Reviewer
→ Devil's Advocate
→ Model Challenge passed
→ Model Approval Brief
→ awaiting_model_approval
→ 用户明确批准当前 semantic revision/hash
→ locked_model_spec
→ 按 preprocessing_decision 分流
   ├─ not_needed     ───────────────────────────────┐
   ├─ question_local ───────────────────────────────┤
   └─ project_level → data_preprocessing            │"""
replace_once("RUNTIME_ROUTER.md", old_runtime, new_runtime)

# Preprocessing contract: distinguish contract introduction from current Skill release and make lifecycle explicit.
replace_once(
    "core/global_preprocessing_contract.yaml",
    "version: 1.3.0\nskill_version: 7.4.2",
    "version: 1.3.0\nintroduced_in_skill_version: 7.4.2\nskill_compatibility: '>=7.4.2,<8.0.0'",
)
old_position = """workflow_position:
  decision_after: model_design
  project_level_stage_after: preprocessing_decision
  before: solve_validate
  rationale: 模型设计先锁定数据需求并形成preprocessing_decision；只有decision=project_level才执行数据预处理模块，否则直接进入主求解。"""
new_position = """workflow_position:
  decision_stage: model_design
  decision_after: data_audit_and_model_route_selection
  decision_before: proposed_model_spec_and_model_challenge
  project_level_stage_after: human_model_approval
  before: solve_validate
  rationale: 模型设计先审计数据并比较模型路线/输入需求，再锁定preprocessing_decision；该判定进入当前模型语义并先于proposed_model_spec与Model Challenge。只有decision=project_level且当前模型已通过Human Model Approval后才执行数据预处理模块，否则进入主求解前的数据源分流。"""
replace_once("core/global_preprocessing_contract.yaml", old_position, new_position)

for rel, contract_version in (
    ("core/user_execution_contract.yaml", "2.2.0"),
    ("core/code_quality_contract.yaml", "1.3.0"),
):
    replace_once(
        rel,
        f"version: {contract_version}\nskill_version: 7.4.2",
        f"version: {contract_version}\nintroduced_in_skill_version: 7.4.2\nskill_compatibility: '>=7.4.2,<8.0.0'",
    )

# Primary-code module: align lifecycle and gate order with Router authority.
old_solve_flow = """题意口径冻结
→ 题面—数学—代码语义闭环
→ 复杂度合理性复审
→ Independent Model Challenge
→ Human Model Approval（绑定 current semantic revision/hash）
→ model approval gate
→ preprocessing_decision
   ├─ not_needed     → 原始数据
   ├─ question_local → 原始数据 + 本问局部变换
   └─ project_level  → Module 03P → 统一工作簿质量门
→ semantic governance gate
→ 生成问题X求解.py
→ validate_code_delivery.py：执行配置 + 代码工程质量门"""
new_solve_flow = """题意口径冻结
→ 非破坏性数据审计 + 模型路线/输入需求比较
→ preprocessing_decision
→ 题面—数学—代码语义闭环
→ 复杂度合理性复审
→ Independent Model Challenge
→ Human Model Approval（绑定 current semantic revision/hash）
→ semantic governance gate
→ model approval gate
→ 按 preprocessing_decision 分流
   ├─ not_needed     → 原始数据
   ├─ question_local → 原始数据 + 本问局部变换
   └─ project_level  → Module 03P → 统一工作簿质量门
→ 生成问题X求解.py
→ validate_code_delivery.py：执行配置 + 代码工程质量门"""
replace_once("modules/03_solve_validate.md", old_solve_flow, new_solve_flow)

# README release carrier + health-audit synopsis.
replace_once("README.md", "# mathmodel-skill v7.11.1", "# mathmodel-skill v7.11.2")
old_readme_intro = "HSK 数学建模工作流：**审题与 Problem Contract 冻结 → 数据审计与 `preprocessing_decision` → 语义闭环与复杂度复审 → 结构化简与 Algorithm Trace → `proposed_model_spec` → Model Reviewer + Devil's Advocate → Model Approval Brief → `awaiting_model_approval` → 用户明确批准当前 `semantic_revision/hash` → `locked_model_spec` → 条件式预处理 → 用户本地 full-fidelity Python 主求解 → 独立结果深化分析 → MATLAB 证据图 → LaTeX 终稿 → AI cleanup → LaTeX project audit attestation → profile-bound compile attestation → 评委式终审 → submission package generation → resolver-returned `pre_delivery_gates` → validated submission package**。"
new_readme_intro = "HSK 数学建模工作流：**审题与 Problem Contract 冻结 → 非破坏性数据审计 + 模型路线/数据需求比较 → `preprocessing_decision` → 语义闭环与复杂度复审 → 结构化简与 Algorithm Trace → `proposed_model_spec` → Model Reviewer + Devil's Advocate → Model Approval Brief → `awaiting_model_approval` → 用户明确批准当前 `semantic_revision/hash` → `locked_model_spec` → 条件式预处理 → 用户本地 full-fidelity Python 主求解 → 独立结果深化分析 → MATLAB 证据图 → LaTeX 终稿 → AI cleanup → LaTeX project audit attestation → profile-bound compile attestation → 评委式终审 → submission package generation → resolver-returned `pre_delivery_gates` → validated submission package**。"
replace_once("README.md", old_readme_intro, new_readme_intro)
health_section = """## v7.11.2：Runtime Health & Semantic Coherence

本补丁在进入 v7.12.0 Declarative Runtime & Assurance 规划前做一次运行时体检，不新增业务模型或数值接口。重点修复 Skill 调取面与生命周期摘要中的语义漂移，并把当前可运行基线进一步收紧。

- 扩展 root/packaged Skill 的高频触发词，覆盖审题、建模思路/方案、完整求解、结果分析、终审和提交包等常见自然语言入口；插件关键词补充 problem-audit、model-design 与 workflow-routing。
- 统一 `preprocessing_decision` 生命周期：先做非破坏性数据审计并比较模型路线/输入需求，在 Module 02 内锁定判定，再完成 current proposed model、Model Challenge 与 Human Approval；不再在 Runtime Router 中把该判定误写成锁模后的步骤。
- 修复 Module 03A 的示意链，使正式主求解代码前的 gate 顺序与 Router 一致：`semantic_governance → model_approval → code_delivery`，并保持 project-level 预处理位于人工锁模之后、主求解之前。
- 将三个 v7.4.2 引入的长期合同中的旧 `skill_version` 元数据改为 `introduced_in_skill_version + skill_compatibility`，避免把合同引入版本误读为当前 Skill 版本；合同自身 version、Schema、CLI 与执行语义不变。
- 增加 runtime-health 回归，锁定 root/packaged Skill 全文件一致、常用触发面、预处理生命周期与主求解 gate 顺序，防止后续声明式运行时重构再次产生入口/语义漂移。

本补丁明确不实现 state-aware resolver hydration、artifact project/hash binding、intent confidence/ambiguity diagnostics 或新的 runtime assurance schema；这些进入 v7.12.0 规划。

"""
marker = "## v7.11.1：Single-Authority Stabilization\n"
if read("README.md").count(marker) != 1:
    raise RuntimeError("README v7.11.1 marker missing or duplicated")
write("README.md", read("README.md").replace(marker, health_section + marker, 1))

# Changelog release entry.
change_entry = """## Current release: 7.11.2

- Ran a runtime-health audit before v7.12 planning and kept the repair scope to invocation/read-path/lifecycle coherence rather than new modeling capabilities.
- Expanded high-frequency Skill discovery triggers for problem audit, model design, full solving, result analysis, final review and submission-package requests while keeping root and packaged Skill entrypoints identical.
- Aligned `preprocessing_decision` lifecycle across the preprocessing authority, Skill summary, Runtime Router and primary-solve module: audit + model-route/data-requirement comparison → decision → proposed model/challenge → explicit approval → conditional project-level preprocessing.
- Corrected the Module 03A pre-code sequence to the Router-authoritative `semantic_governance → model_approval → code_delivery` order.
- Reclassified legacy `skill_version: 7.4.2` metadata in preprocessing/user-execution/code-quality contracts as introduction/compatibility metadata, without changing their contract versions or runtime semantics.
- Added runtime-health regression coverage for full root/packaged Skill parity, discovery triggers, lifecycle ordering and subordinate-contract version-carrier hygiene.
- Preserved CLI, Project State Schema, Workbook Schema, per-question five-file interface, Python/MATLAB ownership, full-fidelity user execution, LaTeX attestation v3 and submission provenance.

## Previous release: 7.11.1
"""
replace_once("CHANGELOG.md", "## Current release: 7.11.1\n", change_entry)

# Lint now guards full entrypoint parity and subordinate-contract release-carrier hygiene.
lint_rel = "scripts/lint_skill_checks.py"
old_lint_parity = """    if root_block is not None and packaged_block is not None and root_block != packaged_block:
        errors.append(\"root and packaged SKILL runtime-entry contracts drifted\")

    plugin = load_structured(plugin_path) or {}"""
new_lint_parity = """    if root_block is not None and packaged_block is not None and root_block != packaged_block:
        errors.append(\"root and packaged SKILL runtime-entry contracts drifted\")
    if texts[\"SKILL.md\"] != texts[\"skills/mathmodel-skill/SKILL.md\"]:
        errors.append(\"root and packaged SKILL files drifted\")

    plugin = load_structured(plugin_path) or {}"""
replace_once(lint_rel, old_lint_parity, new_lint_parity)
old_lint_governance = """    if \"<8.0.0\" not in governance:
        errors.append(\"governance applicability must include v7\")


def check_taxonomy(errors: list[str]) -> None:"""
new_lint_governance = """    if \"<8.0.0\" not in governance:
        errors.append(\"governance applicability must include v7\")
    for relative in (
        \"core/global_preprocessing_contract.yaml\",
        \"core/user_execution_contract.yaml\",
        \"core/code_quality_contract.yaml\",
    ):
        contract = load_structured(ROOT / relative) or {}
        if \"skill_version\" in contract:
            errors.append(f\"subordinate contract must not declare current-release skill_version: {relative}\")
        if not contract.get(\"introduced_in_skill_version\"):
            errors.append(f\"subordinate contract introduction version missing: {relative}\")
        compatibility = str(contract.get(\"skill_compatibility\", \"\"))
        if \"<8.0.0\" not in compatibility:
            errors.append(f\"subordinate contract compatibility must cover active v7 line: {relative}\")


def check_taxonomy(errors: list[str]) -> None:"""
replace_once(lint_rel, old_lint_governance, new_lint_governance)

# Focused regression suite for the health findings.
test_text = r'''from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
ROOT_SKILL = ROOT / "SKILL.md"
PACKAGED_SKILL = ROOT / "skills/mathmodel-skill/SKILL.md"


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def skill_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise AssertionError(f"missing frontmatter: {path}")
    return yaml.safe_load(text.split("---\n", 2)[1]) or {}


def assert_order(test: unittest.TestCase, text: str, tokens: list[str]) -> None:
    positions = []
    for token in tokens:
        pos = text.find(token)
        test.assertGreaterEqual(pos, 0, token)
        positions.append(pos)
    test.assertEqual(positions, sorted(positions), tokens)


class RuntimeHealthCoherenceTests(unittest.TestCase):
    def test_root_and_packaged_skill_are_fully_identical(self):
        self.assertEqual(ROOT_SKILL.read_text(encoding="utf-8"), PACKAGED_SKILL.read_text(encoding="utf-8"))

    def test_skill_discovery_covers_high_frequency_intents(self):
        triggers = set(skill_frontmatter(ROOT_SKILL).get("triggers", []))
        required = {"审题", "建模思路", "建模方案", "完整求解", "结果分析", "终审", "提交包"}
        self.assertFalse(required - triggers, sorted(required - triggers))

    def test_subordinate_contract_versions_are_introduction_metadata(self):
        for relative in (
            "core/global_preprocessing_contract.yaml",
            "core/user_execution_contract.yaml",
            "core/code_quality_contract.yaml",
        ):
            data = yaml.safe_load(read(relative)) or {}
            self.assertNotIn("skill_version", data, relative)
            self.assertEqual(str(data.get("introduced_in_skill_version")), "7.4.2", relative)
            self.assertEqual(str(data.get("skill_compatibility")), ">=7.4.2,<8.0.0", relative)

    def test_preprocessing_lifecycle_authority_is_explicit(self):
        data = yaml.safe_load(read("core/global_preprocessing_contract.yaml")) or {}
        position = data.get("workflow_position", {})
        self.assertEqual(position.get("decision_stage"), "model_design")
        self.assertEqual(position.get("decision_after"), "data_audit_and_model_route_selection")
        self.assertEqual(position.get("decision_before"), "proposed_model_spec_and_model_challenge")
        self.assertEqual(position.get("project_level_stage_after"), "human_model_approval")
        self.assertEqual(position.get("before"), "solve_validate")

    def test_skill_main_chain_preserves_preprocessing_lifecycle(self):
        text = ROOT_SKILL.read_text(encoding="utf-8")
        block = text.split("## 主链", 1)[1].split("目录、正式交付", 1)[0]
        assert_order(self, block, [
            "通用数据审计",
            "两条模型路线与数据需求比较",
            "preprocessing_decision",
            "proposed_model_spec",
            "Model Reviewer + Devil's Advocate",
            "locked_model_spec",
        ])

    def test_runtime_router_preserves_preprocessing_lifecycle(self):
        text = read("RUNTIME_ROUTER.md")
        block = text.split("## 概念上的完整工作流", 1)[1].split("## Algorithm Trace 路由边界", 1)[0]
        assert_order(self, block, [
            "两条模型路线/数据需求比较",
            "preprocessing_decision",
            "proposed_model_spec",
            "Model Reviewer",
            "locked_model_spec",
            "按 preprocessing_decision 分流",
        ])

    def test_primary_solve_flow_preserves_gate_order(self):
        text = read("modules/03_solve_validate.md")
        block = text.split("```text\n题意口径冻结", 1)[1].split("```", 1)[0]
        assert_order(self, block, [
            "模型路线/输入需求比较",
            "preprocessing_decision",
            "Independent Model Challenge",
            "Human Model Approval",
            "semantic governance gate",
            "model approval gate",
            "生成问题X求解.py",
            "validate_code_delivery.py",
        ])


if __name__ == "__main__":
    unittest.main()
'''
write("tests/test_runtime_health_coherence.py", test_text)
