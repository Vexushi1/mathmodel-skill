---
status: phase_i_i3b_artifact_state_surface_removal
baseline_skill_version: 8.9.0
baseline_main_commit: e7a5f45fe5bbd96db03b49c6e993b26af10f55ae
parent_plan: docs/semantic_state_runtime_refactor_plan.md
migration_contract: docs/v900_migration_contract.md
i2_record: docs/phase_i_legacy_writer_retirement.md
i3a_record: docs/phase_i_artifact_alias_retirement.md
candidate_final_version: 9.0.0
runtime_authority: false
artifact_active_state_alias_removal_authorized: true
semantic_historical_reader_removal_in_scope: false
release_carrier_update_in_scope: false
---

# Phase I I3b — Obsolete Implementation Artifact State Surface Removal

> 本文件记录 I3b 的实施边界与验收证据，不替代 Runtime Authority。当前 Project State 合法字段由 `core/project_state.schema.yaml` 定义；stale/transition 行为由 `core/state_transition_contract.yaml` 定义；historical implementation alias 的机械识别由 `scripts/artifact_identity.py` 提供。

## 1. 前置条件与授权

I3b 只在以下前置条件成立后执行：

1. v8.9.0 stable compatibility checkpoint 已建立；
2. I2 已停止 `semantic_hash / validated_semantic_hash` active writer，并记录用户对结束 v8 project write compatibility 的显式授权；
3. I3a 已使 active project writers 对 implementation artifact legacy aliases fail closed；
4. I3a final PR head 与 post-merge `main@e7a5f45f...` 均通过标准 11-job CI；
5. 用户在进入 I3b 前再次明确同意“进入下一步”。

因此 I3b 可以删除已经没有 active-write 责任的 implementation artifact state aliases，而不需要恢复 silent migration 或扩大到 semantic historical reader 删除。

## 2. 修改简报

**修改主题：** Phase I I3b — remove obsolete implementation artifact aliases from active Project State / State Transition surfaces.

**当前版本：** `8.9.0`

**目标版本：** release carrier 仍为 `8.9.0`；staged final target 为 `9.0.0`。

**变更等级：** major migration step / active state parse-boundary change。

**直接目标：**

1. 从 `core/project_state.schema.yaml#$defs.artifact_hashes.properties` 删除 `model`；
2. 从 subproblem properties 删除 `model_hash / validated_model_hash`；
3. 从 stale artifact-layer enum 删除 implementation alias `model`；
4. 从 State Transition Authority 删除旧 `legacy_model_artifact_layer_*` compatibility surface；
5. active Project State 对上述旧字段 fail closed；
6. `scripts/artifact_identity.py` 继续提供 pre-schema historical audit/migration normalization；
7. legacy/canonical identity conflict 继续 blocking；
8. typed dependency kind `model` 保留，因为它表示数学模型语义依赖，不是 implementation artifact alias。

**明确不做：**

- 不删除 `semantic_hash / validated_semantic_hash / approved_semantic_hash` historical properties/readers；
- 不删除 Model Approval / Runtime Assurance 的 L0 historical semantic evidence path；
- 不删除 `legacy_untyped` dependency compatibility；
- 不修改 typed dependency propagation；
- 不删除 `robustness_workbook` 等其他独立 legacy compatibility surface；
- 不修改 `<9.0.0` compatibility ranges；
- 不升级 Skill release carrier；
- 不执行真实用户项目的批量迁移；
- 不新增自动迁移 CLI。

**权威事实源：**

- `core/bootstrap.yaml`
- `SKILL_CHANGE_GOVERNANCE.md`
- `core/project_state.schema.yaml`
- `core/state_transition_contract.yaml`
- `scripts/artifact_identity.py`
- `docs/v900_migration_contract.md`
- `docs/phase_i_legacy_writer_retirement.md`
- `docs/phase_i_artifact_alias_retirement.md`

**回滚：** 整个 I3b PR revert 到 `main@e7a5f45fe5bbd96db03b49c6e993b26af10f55ae`。本 PR 不批量改写任何真实 project state。

## 3. Active state surface before / after

| Surface | I3a 后 | I3b 后 |
|---|---|---|
| `artifact_hashes.model` | writer fail closed；Schema 仍允许 | **Schema 删除** |
| `validated_artifact_hashes.model` | writer fail closed；Schema 仍允许 | **Schema 删除** |
| `model_hash` | historical fallback reader；Schema 仍允许 | **Schema 删除** |
| `validated_model_hash` | historical fallback reader；Schema 仍允许 | **Schema 删除** |
| `stale_layers: model` | historical normalization；Schema/Transition metadata 仍允许读取说明 | **active Schema/Transition surface 删除** |
| `artifact_hashes.primary_code` | canonical | canonical |
| `artifact_hashes.analysis_code` | canonical | canonical |
| dependency kind `model` | typed semantic dependency | **保留** |

I3b 的核心原则是：**active state shape 不再承担 historical file parsing 责任**。旧项目若需要继续进入 active workflow，必须先在 Schema 之外通过窄的 migration adapter 完成机械 implementation alias 归一化，再进入 current state validation。

## 4. Historical adapter boundary

`scripts/artifact_identity.py` 中的：

- `normalize_artifact_hashes()`；
- `normalize_stale_layers()`；

继续允许读取历史 v8 implementation aliases，用于：

- L0 historical audit；
- migration diagnostics；
- 显式 pre-schema migration tooling/流程。

它们不表示 legacy aliases 仍是 current Project State 的合法字段。

冲突策略保持不变：legacy 与 canonical identity 同时存在且值不同必须 blocking；不得静默选择任何一边。

## 5. `model` dependency kind 与 retired `model` artifact alias 的区分

I3b **必须保留**：

```text
dependency_kind: model
```

因为该值表达的是“下游数学模型语义依赖上游模型语义”。它参与 typed dependency propagation，属于 State Transition 的语义依赖图。

I3b **删除**的是：

```text
artifact_hashes.model
stale_layers: model
model_hash
validated_model_hash
```

这些值只表示旧 primary implementation identity 命名。二者名字相同但职责完全不同，禁止机械全局替换或一起删除。

## 6. Migration matrix 更新

`tests/fixtures/v900_phase_i_migration_matrix.yaml` 在 I3b 后记录：

- stable compatibility window closed = true；
- all targeted legacy writers stopped = true；
- user-approved end of v8 write compatibility = true；
- active Schema accepts implementation aliases = false；
- historical adapter remains supported = true；
- automatic implementation alias migration scope = `pre_schema_historical_adapter_only`；
- final migration/release document complete = false。

I1 `docs/v900_migration_contract.md` 仍保留为 **I1 当时的 pre-destructive historical baseline**。其中“本阶段不删除字段”的文字描述 I1 本身，不覆盖 I2/I3a/I3b 后的 current Runtime Authority。

## 7. 验收

最低验收：

```text
python scripts/lint_skill.py
python -m unittest discover -s tests
python scripts/generate_indexes.py --check
```

I3b 额外验收：

- current example state 继续通过 Project State Schema；
- `artifact_hashes.model` 被 active Schema 拒绝；
- `validated_artifact_hashes.model` 被 active Schema 拒绝；
- `model_hash / validated_model_hash` 被 active Schema 拒绝；
- stale layer `model` 被 active Schema 拒绝；
- `dependency_kind.model` 仍存在；
- historical `artifact_identity` normalization 继续通过；
- alias conflict 继续 blocking；
- State Transition profiles 不产生 retired `model` artifact layer；
- standard 11-job HSK Skill CI 全绿。

只有 final PR head 与合并后的 main 都通过上述 gate，I3b 才算闭环。I4 才处理 v9 compatibility metadata / governance / release carriers。
