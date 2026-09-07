---
status: implemented
phase: I4a
baseline_skill_version: 8.9.0
candidate_final_version: 9.0.0
baseline_main_commit: 12483b97186d7570cd54f3a549b18248732f7079
parent_plan: docs/semantic_state_runtime_refactor_plan.md
runtime_authority: false
---

# Phase I I4a — v9 Applicability Metadata Renewal

本记录说明 Phase I I4a 对活动 governance / subordinate contract compatibility metadata 的续期。它不是新的 Runtime Authority，不改变模型、状态传播、数值验证、写作或执行语义。

## 修改边界

当前 Skill release carrier 仍为 `8.9.0`。本阶段只为仍将在 v9 继续生效的活动规则续期 applicability：

- `SKILL_CHANGE_GOVERNANCE.md`: `>=6.3.0,<10.0.0`；
- `core/task_taxonomy.yaml`: `>=6.3.1,<10.0.0`；
- `core/workbook_schema.yaml`: `>=6.3.2,<10.0.0`；
- `core/global_preprocessing_contract.yaml`: `>=7.4.2,<10.0.0`；
- `core/user_execution_contract.yaml`: `>=7.4.2,<10.0.0`；
- `core/code_quality_contract.yaml`: `>=7.4.2,<10.0.0`；
- `assets/figure_assets.yaml`: `>=7.4.2,<10.0.0`；
- `core/runtime_assurance_contract.yaml`: `>=7.12.0,<10.0.0`；
- `core/numerical_verification_contract.yaml`: `>=7.14.0,<10.0.0`。

这些 metadata 表示对应 Authority / asset contract 的规则仍适用于 Skill v9；它们不是 current Skill release carrier，也不把 repository 当前版本从 `8.9.0` 提前提升为 `9.0.0`。

## 明确不修改的 `<9.0.0`

历史计划和阶段审计中的 `<9.0.0` 是当时事实，必须保留，例如：

- `docs/v801_skill_health_remediation_plan.md`；
- `docs/phase_i_compatibility_removal_readiness.md`；
- `docs/v900_migration_contract.md` 的 I1 历史非破坏性边界；
- I2/I3 implementation records 中当时明确排除的范围。

因此本阶段禁止全仓 search/replace。

## 行为不变量

- `core/bootstrap.yaml#skill_version` 继续为 `8.9.0`；
- 不恢复任何 I2/I3 已退休 legacy writer/active alias；
- 不删除 L0 historical semantic readers；
- 不修改 Project State Schema、State Transition、Resolver 或 transaction 行为；
- 不改变 subordinate contract 自身 `version/schema_version/contract_version`；
- 不创建 v9 GitHub release/tag。

## 后续

I4b 才处理 current release carriers 从 `8.9.0` 到 `9.0.0`。I5 负责最终 migration/release documentation closure 与 release validation。
