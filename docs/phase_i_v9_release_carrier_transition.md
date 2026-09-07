---
status: implemented
phase: I4b
baseline_skill_version: 8.9.0
target_skill_version: 9.0.0
baseline_main_commit: 92b494154ed49f134d5d18eb9b6c4eebade2aec0
parent_plan: docs/semantic_state_runtime_refactor_plan.md
i4a_record: docs/phase_i_v9_applicability_renewal.md
runtime_authority: false
github_release_or_tag_created: false
---

# Phase I I4b — v9 Release Carrier Transition

本记录说明 Phase I I4b 将活动 Skill release carrier 从 `8.9.0` 切换到 `9.0.0`。它是 release metadata / entrypoint 一致性变更，不建立新的 Runtime Authority，也不改变数学、状态、求解、写作或执行语义。

## 活动 release carriers

以下活动 surface 必须一致声明 `9.0.0`：

- `core/bootstrap.yaml#skill_version`；
- `.codex-plugin/plugin.json#version`；
- 根目录与 packaged `SKILL.md` frontmatter / 标题；
- `README.md` current heading；
- `core/hsk_core_policy.md` 标题；
- `CHANGELOG.md#Current release`；
- `core/workflow_router.yaml#version`；
- `core/module_manifest.yaml#version`；
- `core/output_contract.yaml#version`；
- `core/writing_runtime_contract.yaml#version`；
- `config/prose_audit_patterns.yaml#version`。

## 历史 provenance 不重写

I0/I1/I2/I3/I4a 的 `baseline_skill_version: 8.9.0`、migration fixtures 与当时的“release carrier 仍为 8.9.0”陈述是历史事实，继续保留。I4b 只改变 current active release carrier，不通过全仓字符串替换篡改阶段证据。

## 行为不变量

- 不恢复 I2 已停止的 legacy semantic writers；
- 不恢复 I3 已移除的 active artifact aliases / obsolete state fields；
- 不删除 initial-v9 L0 historical readers；
- 不修改 Project State Schema、State Transition、Resolver、transaction、numerical verification、writing runtime 或 Model Approval 行为；
- I4a 的 active applicability 继续为 `<10.0.0`；
- 不创建 GitHub tag 或 GitHub Release。

## 后续

Phase I I5 负责最终 migration/release documentation closure、最终 release validation，以及在确认全部 release gate 后处理外部 release/tag（如项目流程要求）。
