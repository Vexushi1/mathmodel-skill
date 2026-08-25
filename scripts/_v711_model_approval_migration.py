#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: str, old: str, new: str) -> None:
    file = ROOT / path
    text = file.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"missing migration anchor in {path}: {old[:120]!r}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8")


def replace_all(path: str, old: str, new: str, minimum: int = 1) -> None:
    file = ROOT / path
    text = file.read_text(encoding="utf-8")
    count = text.count(old)
    if count < minimum:
        raise SystemExit(f"expected >= {minimum} anchors in {path}, found {count}: {old!r}")
    file.write_text(text.replace(old, new), encoding="utf-8")


# Release carriers.
replace_once("README.md", "# mathmodel-skill v7.10.1", "# mathmodel-skill v7.11.0")
replace_once(
    "README.md",
    "## v7.10.1：Read-Path & Gate Dispatch Closure",
    """## v7.11.0：Model Challenge & Human Approval Closure

本版本在 Problem Contract、Semantic Closure 与 Complexity Sanity 之后增加两层正式锁模治理，不改变数值模型接口、Workbook Schema、Python/MATLAB 职责、用户 full-fidelity 执行、LaTeX attestation v3、submission provenance 或每问五文件合同。

- Module 02 在 `locked_model_spec` 前新增 `proposed_model_spec`，并执行相互独立的 Model Reviewer 与 Devil's Advocate 两次挑战审查；blocking 不能由用户批准绕过。
- Challenge passed 后生成 Model Approval Brief，并停在 `awaiting_model_approval`；只有用户明确批准当前 `semantic_revision/hash` 后，`locked_model_spec` 才成为 current。
- 新增 `core/model_approval_contract.yaml` 与 `scripts/validate_model_approval.py`；项目级预处理和主求解代码交付前必须验证 challenge/approval 与当前 revision/hash 完全一致。
- 语义 revision/hash 变化会使旧 challenge、approval 与 locked model stale；纯排版、措辞、caption、公式编号或不改变语义的 LaTeX 文件拆分不触发重新审批。
- 旧项目保持只读兼容；只有重新进入模型设计、项目级预处理、主求解或语义变化后的重算时才迁入新 approval gate。
- 不迁移旧 V2 的 `HUMAN_MODEL_REVIEW.md`、`MODEL_REVIEW_AI.md`、`AGENT_RUNS.md` 等 reports 文件体系，也不绑定特定 multi-agent runtime。

## v7.10.1：Read-Path & Gate Dispatch Closure""",
)
replace_once(
    "CHANGELOG.md",
    "## Current release: 7.10.1\n\n",
    """## Current release: 7.11.0

- Added independent Model Reviewer and Devil's Advocate challenge passes after semantic closure and Complexity Sanity, before the model can be locked.
- Added explicit Human Model Approval bound to the current semantic revision/hash; silence or vague continuation is not approval, and blocking challenge findings cannot be waived.
- Added `proposed_model_spec`, `awaiting_model_approval`, approval state fields and `scripts/validate_model_approval.py` so project-level preprocessing and primary solve code cannot bypass the current approved model.
- Semantic revision/hash drift now invalidates the previous challenge, approval and locked model while preserving read-only compatibility for historical projects.
- Kept Python/MATLAB ownership, Workbook Schema, full-fidelity user execution, modular LaTeX, compile attestation v3, submission provenance and the per-question five-file interface unchanged.

## Previous release: 7.10.1

""",
)

# Core policy.
replace_once("core/hsk_core_policy.md", "# HSK Core Policy v7.10.1", "# HSK Core Policy v7.11.0")
replace_once(
    "core/hsk_core_policy.md",
    "题意口径、语义闭环和语义变更状态以 `模型论文框架.md`、`core/project_state.schema.yaml` 与 `scripts/validate_semantic_governance.py` 为准；",
    "题意口径、语义闭环和语义变更状态以 `模型论文框架.md`、`core/project_state.schema.yaml` 与 `scripts/validate_semantic_governance.py` 为准；模型挑战与人工锁模以 `core/model_approval_contract.yaml` 与 `scripts/validate_model_approval.py` 为准；",
)
replace_once(
    "core/hsk_core_policy.md",
    "### 2.5 项目工作记忆与上下文恢复",
    """### 2.5 Model Challenge 与 Human Model Approval

Problem Contract 冻结只回答“题目是什么意思”，Semantic Closure 与 Complexity Sanity 只回答“当前数学语义是否闭合、简化是否合理”，三者都不能替代正式锁模。进入项目级预处理或主求解代码前，必须按 `core/model_approval_contract.yaml` 完成相互独立的 Model Reviewer 与 Devil's Advocate 两次挑战审查；blocking 必须先修复，`review_required` 必须修复或给出具体、可验证的 justification。

Challenge passed 后必须向用户提供 Model Approval Brief，并停在 `awaiting_model_approval`。只有用户明确批准当前 `semantic_revision` 与 `semantic_hash` 后，`locked_model_spec` 才成为 current；用户沉默、模糊继续或未反对不得推断为批准。语义 revision/hash 改变时旧 challenge、approval 与 locked model 同时 stale；纯排版、措辞、caption、公式编号或不改变语义的 LaTeX 文件拆分不触发重新审批。

### 2.6 项目工作记忆与上下文恢复""",
)
replace_once(
    "core/hsk_core_policy.md",
    "实际生成的 `数据预处理.py`、`问题X求解.py` 与 `问题X结果深化分析.py` 均由助手生成和静态检查、由用户本地 full-fidelity 执行。",
    "实际生成的 `数据预处理.py`、`问题X求解.py` 与 `问题X结果深化分析.py` 均由助手生成和静态检查、由用户本地 full-fidelity 执行。正式项目级预处理或主求解代码前，当前模型必须同时通过 semantic governance 与 model approval gate；旧审批不得覆盖新的 semantic revision/hash。",
)

# Router authority and code gate order.
replace_once("core/workflow_router.yaml", "version: 7.10.1", "version: 7.11.0")
replace_once(
    "core/workflow_router.yaml",
    "  - Load global_preprocessing_contract only when the route decides, executes or inherits preprocessing semantics.\n",
    "  - Load global_preprocessing_contract only when the route decides, executes or inherits preprocessing semantics.\n  - Load model_approval_contract for model-design routes that can propose/lock a model and for task-code routes that must verify current Human Model Approval.\n",
)
replace_once(
    "core/workflow_router.yaml",
    "  activation: locked_model_spec exists and current framework is available",
    "  activation: proposed_model_spec exists or locked_model_spec exists and current framework is available",
)
replace_once(
    "core/workflow_router.yaml",
    "  targeted_read_sections: [当前有效口径, relevant_subproblem, required_dependencies, relevant_result_summary, Algorithm Trace, Terminology Registry, Numeric Profile, 待办与缺口]",
    "  targeted_read_sections: [当前有效口径, relevant_subproblem, required_dependencies, Model Challenge, Human Model Approval, relevant_result_summary, Algorithm Trace, Terminology Registry, Numeric Profile, 待办与缺口]",
)
replace_once(
    "core/workflow_router.yaml",
    "  code_stage_gates: [semantic_governance, code_delivery]",
    "  code_stage_gates: [semantic_governance, model_approval, code_delivery]",
)
replace_once(
    "core/workflow_router.yaml",
    "  - Problem Contract, semantic closure and complexity sanity must pass before any formal model or code delivery.",
    "  - Problem Contract, semantic closure and complexity sanity must pass before Model Challenge; project-level preprocessing or primary solve code additionally requires challenge passed plus explicit Human Model Approval bound to the current semantic revision/hash.",
)
replace_all(
    "core/workflow_router.yaml",
    "pre_delivery_gates: [semantic_governance, code_delivery]",
    "pre_delivery_gates: [semantic_governance, model_approval, code_delivery]",
    minimum=4,
)
for anchor in (
    "load: [core/task_taxonomy.yaml, core/global_preprocessing_contract.yaml, core/writing_reasoning_contract.yaml, modules/01_problem_audit.md, packs/task/classifier.md]",
    "load: [core/task_taxonomy.yaml, core/global_preprocessing_contract.yaml, core/user_execution_contract.yaml, core/code_quality_contract.yaml, core/writing_reasoning_contract.yaml, modules/01_problem_audit.md, packs/task/classifier.md]",
    "load: [core/task_taxonomy.yaml, core/global_preprocessing_contract.yaml, core/writing_reasoning_contract.yaml, modules/02_model_design.md, packs/task/classifier.md]",
    "load: [core/task_taxonomy.yaml, core/global_preprocessing_contract.yaml, core/writing_reasoning_contract.yaml, modules/02_model_design.md, packs/task/advanced_method_gate.md, packs/task/classifier.md]",
    "load: [core/task_taxonomy.yaml, core/global_preprocessing_contract.yaml, core/user_execution_contract.yaml, core/code_quality_contract.yaml, modules/03_solve_validate.md, packs/artifact/code.md, packs/task/classifier.md]",
):
    if anchor in (ROOT / "core/workflow_router.yaml").read_text(encoding="utf-8"):
        replace_all("core/workflow_router.yaml", anchor, anchor.replace("core/global_preprocessing_contract.yaml, ", "core/global_preprocessing_contract.yaml, core/model_approval_contract.yaml, "))
replace_once(
    "core/workflow_router.yaml",
    "load: [core/global_preprocessing_contract.yaml, core/user_execution_contract.yaml, core/code_quality_contract.yaml, modules/03_data_preprocessing.md, packs/artifact/code.md]",
    "load: [core/global_preprocessing_contract.yaml, core/model_approval_contract.yaml, core/user_execution_contract.yaml, core/code_quality_contract.yaml, modules/03_data_preprocessing.md, packs/artifact/code.md]",
)

# Output contract.
replace_once("core/output_contract.yaml", "version: 7.10.1", "version: 7.11.0")
replace_once(
    "core/output_contract.yaml",
    "preprocessing_contract: core/global_preprocessing_contract.yaml\n",
    "preprocessing_contract: core/global_preprocessing_contract.yaml\nmodel_approval_contract: core/model_approval_contract.yaml\n",
)
replace_once(
    "core/output_contract.yaml",
    "  semantic_governance_gate: scripts/validate_semantic_governance.py\n",
    "  semantic_governance_gate: scripts/validate_semantic_governance.py\n  model_approval_gate: scripts/validate_model_approval.py\n",
)
replace_once(
    "core/output_contract.yaml",
    "  pause_states:\n  - awaiting_user_preprocessing\n",
    "  pause_states:\n  - awaiting_model_approval\n  - awaiting_user_preprocessing\n",
)
replace_once(
    "core/output_contract.yaml",
    "  preprocessing_decision_required_before_solve: true\n",
    "  model_approval_required_before_project_preprocessing_or_primary_solve: true\n  preprocessing_decision_required_before_solve: true\n",
)
replace_all(
    "core/output_contract.yaml",
    "create_after: locked_model_spec",
    "create_after: proposed_model_spec",
    minimum=1,
)

# Resolver: approval must appear in code-stage gates and old accepted results remain read-compatible.
replace_once(
    "scripts/resolve_workflow.py",
    'SEMANTIC_CODE_GATES = ["semantic_governance", "code_delivery"]',
    'SEMANTIC_CODE_GATES = ["semantic_governance", "model_approval", "code_delivery"]',
)
replace_once(
    "scripts/resolve_workflow.py",
    '    "full_workflow", "code_and_solution", "data_preprocessing",\n}',
    '    "full_workflow", "code_and_solution", "data_preprocessing", "result_analysis", "validation",\n}',
)
replace_once(
    "scripts/resolve_workflow.py",
    '    if "locked_model_spec" in available:\n        return paths, outputs, scopes, gates, formal_delivery, pause, False\n',
    '    primary_accepted = bool(\n        "accepted_solution_workbook" in available\n        or {"solution_workbook", "result_quality_report"}.issubset(available)\n        or {"solved_results", "result_quality_report"}.issubset(available)\n    )\n    if "locked_model_spec" in available or primary_accepted:\n        return paths, outputs, scopes, gates, formal_delivery, pause, False\n',
)

# Lint expectations: code-stage closure is now semantic -> approval -> code delivery.
replace_all(
    "scripts/lint_skill_checks.py",
    '["semantic_governance", "code_delivery"]',
    '["semantic_governance", "model_approval", "code_delivery"]',
    minimum=1,
)
replace_once(
    "scripts/lint_skill_checks.py",
    '"core/user_execution_contract.yaml", "core/code_quality_contract.yaml", "core/writing_reasoning_contract.yaml",',
    '"core/model_approval_contract.yaml", "core/user_execution_contract.yaml", "core/code_quality_contract.yaml", "core/writing_reasoning_contract.yaml",',
)
replace_once(
    "scripts/lint_skill_checks.py",
    '"scripts/resolve_workflow.py", "scripts/validate_semantic_governance.py", "scripts/sync_project.py",',
    '"scripts/resolve_workflow.py", "scripts/validate_semantic_governance.py", "scripts/validate_model_approval.py", "scripts/sync_project.py",',
)

# Canonical framework template: approval status is part of current per-question semantics.
replace_once(
    "templates/model/model_paper_framework.md",
    "- 复杂度复审：`pending / passed / review_required`\n- semantic revision：`1`",
    "- 复杂度复审：`pending / passed / review_required`\n- Model Challenge：`pending / passed / revision_required / stale`\n- Human Model Approval：`pending / approved / revision_required / stale`\n- Approved semantic revision：\n- Approved semantic hash：\n- semantic revision：`1`",
)
replace_once(
    "templates/model/model_paper_framework.md",
    "**数值参数证据**\n",
    """**模型挑战与人工锁模**

- Model Reviewer verdict 与 required actions：
- Devil's Advocate verdict、核心反例/风险与 required actions：
- Residual warnings：
- Model Approval Brief：研究对象、selected model、核心变量、objective、关键约束、preprocessing_decision、结构化简、求解方式、algorithm presentation、被否决路线理由、下一阶段实现范围。
- 当前模型状态：`proposed_model_spec / locked_model_spec / stale`

**数值参数证据**
""",
)

# Fix packaged entry typo introduced during branch editing.
replace_once(
    "skills/mathmodel-skill/SKILL.md",
    "问题X结果深化分析结果.xlsx",
    "问题X结果深化分析.xlsx",
)

print("v7.11 model-approval migration applied")
