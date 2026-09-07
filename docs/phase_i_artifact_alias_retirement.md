---
status: phase_i_i3a_active_artifact_alias_retirement
baseline_skill_version: 8.9.0
baseline_main_commit: 6b3a67f99607b34cf47da88c20c9f8d0cdcc7cc0
parent_plan: docs/semantic_state_runtime_refactor_plan.md
migration_contract: docs/v900_migration_contract.md
candidate_final_version: 9.0.0
runtime_authority: false
active_alias_write_retirement: true
schema_field_removal_in_scope: false
historical_read_adapter_removal_in_scope: false
release_carrier_bump_in_scope: false
---

# Phase I I3a — Active Artifact Alias Retirement

> 本文件记录 Phase I I3 的第一步实施边界，不替代 Project State、State Transition、Runtime Assurance 或 User Execution Authority。

## 1. 修改简报

**修改主题：** 停止 active project writers 对 legacy implementation artifact aliases 的静默 canonicalization。

**当前版本：** `8.9.0`。

**目标版本：** 本 PR release carrier 仍为 `8.9.0`；staged final target 为 `9.0.0`。

**变更等级：** major migration step / compatibility boundary change。

**直接目标：**

1. `artifact_hashes.model` 在 historical audit/migration read 中仍可安全映射到 `primary_code`，冲突继续 blocking；
2. `model_hash / validated_model_hash` 在 historical read 中仍可作为 primary implementation identity fallback；
3. stale layer `model` 在 historical migration diagnostics 中仍可映射到 `primary_code`；
4. 任何 active writer 在进入 project-state mutation 前，只要检测到上述 legacy surfaces，就 fail closed；
5. 已经 canonical 的 `primary_code / analysis_code` 项目保持现有写入行为；
6. active writer 不自动删旧字段、不自动选择冲突值、不自动把 legacy alias 提升为 current state。

**明确不做：**

- 本 PR 不删除 `core/project_state.schema.yaml` 中 legacy artifact properties；
- 不删除 `core/state_transition_contract.yaml` 的 legacy model-layer read compatibility；
- 不删除 L0 historical semantic readers；
- 不删除 `semantic_hash / validated_semantic_hash / approved_semantic_hash`；
- 不修改 Model Approval / Runtime Assurance 的 semantic identity 规则；
- 不批量修改 `<9.0.0` compatibility ranges；
- 不升级 Skill release carrier；
- 不执行真实用户项目的自动迁移。

**权威事实源：**

- `core/bootstrap.yaml`
- `SKILL_CHANGE_GOVERNANCE.md`
- `docs/v900_migration_contract.md`
- `core/project_state.schema.yaml`
- `core/state_transition_contract.yaml`
- `scripts/artifact_identity.py`

**预计修改文件：**

- `scripts/artifact_identity.py`
- `tests/test_v900_artifact_identity.py`
- 本实施记录及 generator-managed metadata。

**兼容性要求：** L0 read-only audit 仍可读取非冲突 legacy implementation identity；L1/L2 active writes 必须先完成 mechanical migration，使 state 只使用 canonical implementation names。

**验收测试：** full unit suite、lint、generated check、standard 11-job CI；额外覆盖 read-only mapping、conflict blocking、sync active-write rejection、code-delivery no-mutation rejection、canonical write regression。

**回滚：** 整 PR revert 到 `main@6b3a67f99607b34cf47da88c20c9f8d0cdcc7cc0`；本 PR 不批量改写任何真实项目文件。

## 2. I3 分解理由

I3 同时包含两个不同风险层级：

- **I3a：active runtime retirement** — 停止 active writers 静默迁移 alias；
- **I3b：obsolete state-field removal** — 从 Project State Schema / State Transition compatibility surface 物理删除 `artifact_hashes.model`、`model_hash / validated_model_hash`、stale `model`。

先合并 I3a 可以证明所有 active writers 已经不依赖旧名字，再执行 I3b 的 Schema 删除。这样避免在一个 PR 中同时改变 writer 行为与 state parse boundary，也提供清晰的回滚点。

## 3. 新行为

`normalize_artifact_hashes()` 与 `normalize_stale_layers()` 保持 read-only audit/migration helper：

```text
legacy non-conflicting alias -> canonical comparison value
legacy/canonical conflict   -> blocking
```

`canonicalize_entry_hashes()` 改为 active-write gate：

```text
artifact_hashes.model present        -> block
validated_artifact_hashes.model      -> block
model_hash present                   -> block
validated_model_hash present         -> block
stale_layers contains model          -> block
canonical-only state                 -> continue
```

该 gate 被现有 `sync_project.py`、`validate_code_delivery.py`、`validate_user_execution.py` 共享消费，因此不在三个脚本里复制同一兼容策略。

## 4. I3b 前置条件

只有 I3a final head 和 post-merge main 都通过完整 CI 后，才进入 I3b。I3b 才负责：

- 从 Project State Schema 删除 `artifact_hashes.model`；
- 删除 `model_hash / validated_model_hash` properties；
- 从 artifact-layer enum 删除 stale `model`；
- 收敛 State Transition compatibility metadata；
- 更新 migration matrix / release migration field inventory；
- 重新运行全部 migration acceptance tests 与 11-job CI。

I3a 完成不等于 `9.0.0` 已发布，也不授权删除 semantic historical readers。
