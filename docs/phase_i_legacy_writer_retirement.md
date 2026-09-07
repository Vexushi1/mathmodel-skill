---
status: phase_i_i2_writer_retirement_implementation
baseline_skill_version: 8.9.0
baseline_main_commit: f4b5bff59f77c45d53b1199e3b5d8f9b4d5620ce
parent_plan: docs/semantic_state_runtime_refactor_plan.md
migration_contract: docs/v900_migration_contract.md
readiness_audit: docs/phase_i_legacy_writer_retirement_readiness.md
inventory_fixture: tests/fixtures/v900_phase_i_writer_retirement_inventory.yaml
candidate_final_version: 9.0.0
runtime_authority: false
gate5_explicit_user_approval_recorded: true
legacy_writer_retirement_authorized: true
artifact_alias_removal_in_scope: false
legacy_field_deletion_in_scope: false
---

# Phase I I2 — Legacy Semantic Writer Retirement

> 本文件记录 I2 行为变更的实施边界与验收证据，不替代 Runtime Authority。实际写入规则由 `scripts/validate_semantic_governance.py` 与 `core/project_state.schema.yaml` 共同约束；Model Approval、Runtime Assurance 与 State Transition 继续由各自现有 Authority 管理。

## 1. Gate 5 授权记录

I2 readiness 明确要求：在停止 v8 project write compatibility 前，必须获得用户对 destructive boundary 的显式确认，不能从一般“继续”指令推断。

在本次 I2 implementation 分支创建前，用户在当前对话中明确批准：

- 可以结束 v8 project write compatibility；
- 可以进入 I2 writer retirement；
- 若需要额外 GitHub UI 操作再提醒。

该确认满足 Phase I Gate 5 对 **结束 v8 semantic project write compatibility** 的人工授权要求。仓库治理与 parent plan 没有要求用户必须额外在 GitHub UI 点击审批，因此无需第二次外部操作。

本授权在本 PR 中只用于 `semantic_hash / validated_semantic_hash` active writer retirement。它不自动授权扩大本 PR 到 I3 artifact alias cleanup、legacy field 物理删除、`<9.0.0` compatibility range 批量修改或 `9.0.0` release carrier 更新。

## 2. 修改简报

**修改主题：** Phase I I2 — stop remaining legacy semantic writes while preserving narrow historical readers.

**当前版本：** `8.9.0`

**目标版本：** release carrier 仍为 `8.9.0`；最终 staged target 为 `9.0.0`。

**变更等级：** major migration step / runtime compatibility boundary change。

**直接目标：**

1. 停止 semantic governance 对 `semantic_hash / validated_semantic_hash` 的 active write；
2. 无 SIB 项目在 `write=True` 时 fail closed，并要求先建立 current valid SIB；
3. legacy/no-SIB `write=False` 继续提供 historical read/diagnostic；
4. mixed structured + legacy 项目只要包含 legacy write blocker，整个 semantic-governance transaction 不提交，避免半迁移；
5. structured SIB writer、semantic stale propagation 与 transaction semantics保持 current；
6. Schema 将两个 legacy semantic fields 收敛为 historical read-only compatibility；
7. 保留 `approved_semantic_hash`、Model Approval historical reader、Runtime Assurance historical evidence。

**明确不做：**

- 不删除 `semantic_hash / validated_semantic_hash / approved_semantic_hash` Schema property；
- 不删除 `model_hash / validated_model_hash`；
- 不删除 `artifact_hashes.model`；
- 不删除 stale `model` alias；
- 不删除 historical semantic readers；
- 不自动生成 SIB；
- 不把 legacy hash 复制到 structured identity；
- 不自动继承或合成 Human Approval；
- 不修改 State Transition Authority；
- 不修改 competition writing runtime；
- 不批量修改 `<9.0.0` compatibility metadata；
- 不升级 Skill release carrier。

**权威事实源：**

- `core/bootstrap.yaml`
- `SKILL_CHANGE_GOVERNANCE.md`
- `core/project_state.schema.yaml`
- `core/model_approval_contract.yaml`
- `core/runtime_assurance_contract.yaml`
- `core/state_transition_contract.yaml`
- `docs/v900_migration_contract.md`
- `docs/phase_i_legacy_writer_retirement_readiness.md`

**回滚：** 整 PR revert 到 `main@f4b5bff59f77c45d53b1199e3b5d8f9b4d5620ce`。本 PR 不执行真实项目迁移，也不批量改写用户项目文件；已经由 v8.9.0 建立的 legacy state 仍可被 historical readers 读取。

## 3. 新的 semantic-governance 写入边界

### 3.1 Historical read remains available

Framework 无 SIB 时，`validate_project(..., write=False, ...)` 仍：

- 识别 `identity_mode=legacy_text_hash`；
- 从当前 Framework 计算 legacy text hash 用于 historical comparison；
- 检测 `validated_semantic_hash` drift；
- 运行 revision/category diagnostics；
- 在 state copy 上计算 stale/dependency propagation report；
- 不把 legacy provenance 提升为 current structured approval。

这保证 L0 historical project 仍可审计。

### 3.2 Active legacy write is retired

Framework 无 SIB 且调用 `write=True` 时：

- 报告该 question 为 `legacy_write_blocked_sources`；
- 同时列入 `migration_sources`；
- 返回明确 issue：legacy semantic hashes 已转为历史只读，active write 需要有效 current SIB；
- 不写 `semantic_hash`；
- 不写 `validated_semantic_hash`；
- 不自动创建 SIB；
- 不自动迁移 approval。

因此 L1 active reentry 必须按 I1 migration contract 建立 structured identity，然后再经过 Model Challenge / explicit Human Approval 才能进入新的 task-code delivery。

### 3.3 Transaction-level fail closed

若一次 semantic-governance `write=True` 涉及多个 questions，只要其中任一 question 为 legacy/no-SIB：

```text
entire semantic-governance state commit = blocked
```

transition diagnostics 可在 deep copy 上计算并返回，但不会把 structured question 的局部更新提交到磁盘。这样不会产生“部分 structured 已更新、legacy 仍旧”的半迁移 accepted state。

### 3.4 Structured writer remains current

有效 SIB question 继续写：

- `semantic_identity_schema_version`
- `semantic_identity_hash`
- `validated_semantic_identity_hash`
- `semantic_text_hash`
- `validated_semantic_revision`

现有 revision/category/stale propagation 与 transactional project-state write 行为保持不变。

## 4. Schema 与 historical readers

`core/project_state.schema.yaml` 继续允许旧字段存在，以便 v8.9.0 historical state 可以被解析；但描述收敛为：

- `semantic_hash`：historical read-only compatibility；active code must not write；
- `validated_semantic_hash`：historical read-only compatibility；active code must not write；
- `approved_semantic_hash`：继续 historical approval provenance read-only；
- `model_hash / validated_model_hash`：继续 I3 之前的 implementation fallback reader。

I2 不删除这些 properties，因为 initial v9 的 L0 read adapter 仍依赖它们。

Model Approval 保持现有边界：legacy approval 只有显式 `allow_legacy_read_only=True` 时可用于历史审计，默认 task-code authorization fail closed。

Runtime Assurance 保持现有边界：legacy evidence 不得升级为 current verified `locked_model_spec`，仍返回 historical/review-required 状态。

## 5. Characterization / regression 转换

原先专门验证 v8 legacy writer 的测试不会删除，而是转换为 I2 regression：

- first legacy `write=True` 不再 backfill hashes；
- legacy state `write=False` 仍可 historical validate；
- legacy semantic drift 仍可报告 `changed_sources / affected_questions`；
- legacy `write=True` 不提交 stale mutation；
- structured SIB initial validation仍可写并推进 `state_generation`；
- structured identity change 仍会使 Model Challenge / Human Approval stale；
- AST inventory 证明 active scripts 不再直接赋值 legacy semantic fields。

## 6. I2 后 Gate 快照

| Gate | I2 目标状态 | 说明 |
|---|---|---|
| 1. stable compatibility window | **satisfied** | v8.9.0 stable checkpoint 已建立 |
| 2. migration fixture baseline | **satisfied** | I0/I1 L0/L1/L2 baseline 已存在；本 PR 再跑全量回归 |
| 3. active code no longer writes targeted old fields | **satisfied after this PR passes** | `semantic_hash / validated_semantic_hash` direct writer 被移除 |
| 4. old refs only intended historical reader / validator / tests / docs | **must be proven by post-change code search** | 不以字符串数量代替分类 |
| 5. explicit user approval | **satisfied** | 本次分支创建前用户明确批准结束 v8 project write compatibility |
| 6. final changelog + migration docs | **partial** | I2 implementation record 完成；最终 v9 release notes 仍属于后续 I4/I5 |

I2 完成不代表 Phase I 全部完成，也不代表 `9.0.0` 已发布。

## 7. 验收

最低验收：

```text
python scripts/lint_skill.py
python -m unittest discover -s tests
python scripts/generate_indexes.py --check
```

额外要求：

- legacy `write=False` historical read regression；
- legacy `write=True` fail-closed/no-mutation regression；
- mixed transaction no-half-migration regression；
- structured semantic-governance writer regression；
- Model Approval historical reader regression；
- Runtime Assurance legacy review-required regression；
- AST code-search characterization proving no active legacy semantic direct assignment；
- standard 11-job HSK Skill CI。

只有 PR final head 全绿且 changed-file scope 无 I3/I4 越界时才可合并。
