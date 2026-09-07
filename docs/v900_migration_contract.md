---
status: final_v900_release_contract
baseline_skill_version: 8.9.0
baseline_main_commit: c8687dd89d3b90fd288d9d375c0341e2750cf510
current_skill_version: 9.0.0
release_main_commit: f6b506212cf466add0e55f175527651a18ae9fe2
parent_plan: docs/semantic_state_runtime_refactor_plan.md
inventory: docs/phase_i_compatibility_inventory.md
i2_record: docs/phase_i_legacy_writer_retirement.md
i3a_record: docs/phase_i_artifact_alias_retirement.md
i3b_record: docs/phase_i_artifact_state_surface_removal.md
i4a_record: docs/phase_i_v9_applicability_renewal.md
i4b_record: docs/phase_i_v9_release_carrier_transition.md
i5_record: docs/phase_i_v9_release_closure.md
runtime_authority: false
destructive_compatibility_removal_authorized: true
phase_i_release_documentation_complete: true
---

# v8.9.0 → v9.0.0 Migration Contract — Final Release Contract

> 本文件是 v9.0.0 的最终迁移与兼容边界说明，不是 Runtime Authority。实际 Project State、Model Approval、Runtime Assurance、State Transition 与脚本行为继续以 `core/` Authority 和活动实现为准。

## 1. 最终发布状态

`8.9.0` 是最后一个稳定 v8.x compatibility checkpoint；活动 Skill release carrier 已在 I4b 切换为 `9.0.0`。Phase I I2/I3 已完成被批准的 legacy writer / active implementation alias retirement，I4a 已续期 v9 applicability；I5 只闭合 migration/release documentation 与 release validation，不再扩大 Runtime 行为范围。

Phase I 六个 gate 在 I5 均有明确 disposition：

1. stable v8.x compatibility window：**satisfied** — `8.9.0` 已作为稳定 checkpoint；
2. migration fixtures：**satisfied** — L0/L1/L2 acceptance matrix 保留并持续回归；
3. active code no longer writes targeted old fields：**satisfied** — I2 已停止 legacy semantic writes，I3a 已停止 active implementation alias canonicalization；
4. targeted old fields only remain in intended historical reader/docs：**satisfied** — I3b 已删除 active Schema/Transition implementation aliases，L0 historical reader 明确保留；
5. explicit user authorization：**satisfied** — I2 implementation record 已保存结束 v8 project write compatibility 的显式授权；
6. Changelog + migration documentation：**satisfied by I5** — 本合同、I5 closure record、migration matrix 与 current Changelog 共同闭环。

## 2. 项目分类与 v9 行为

### L0 — Historical read-only legacy project

Framework 无 SIB、仍带 legacy semantic/approval provenance 且只用于历史查看、复核或审计时：

- 保留窄的 historical read-only adapter；
- legacy approval 只能作为 historical provenance；
- `locked_model_spec` 不得因此提升为 current `verified`；
- 只读审计不强制构造 SIB；
- 一旦重新进入模型设计、预处理、主求解或新代码生成，立即按 L1 处理。

### L1 — Legacy project re-entering active modeling / code workflow

必须按以下顺序迁移：

1. 以最后稳定 v8.x（`8.9.0`）状态保留可恢复快照；
2. 通过模型设计流程形成 candidate SIB，禁止从旧 prose 静默推断成 verified identity；
3. semantic governance 对 current Framework SIB 做 canonical validation，得到 current `semantic_identity_hash`；
4. Model Challenge 对 current structured semantics 通过；
5. 用户对 current `semantic_revision` 与 validated structured identity **必须显式 Human Approval**；
6. 仅在上述证据全部 current 后，才允许新的 task-code / solve workflow。

legacy `semantic_hash / approved_semantic_hash` 可作为历史证据，但不能授权第 6 步。

### L2 — Current structured project

- 版本升级本身不自动使 current structured approval stale；
- Runtime Assurance 仍必须从当前 Framework 重新计算 structured identity；
- current / validated / approved identity 或 revision/challenge/approval 不一致时继续 fail closed；
- implementation identity 只接受 current active Schema 的 canonical names。

## 3. Implementation alias 的最终边界

v9 active Project State 已不再接受：

```text
artifact_hashes.model
validated_artifact_hashes.model
model_hash
validated_model_hash
stale_layers: model
```

`scripts/artifact_identity.py` 仍可在 **Schema 之外**对历史 v8 文件做只读审计或显式 pre-schema migration normalization：

```text
artifact_hashes.model -> artifact_hashes.primary_code
validated_artifact_hashes.model -> validated_artifact_hashes.primary_code
model_hash -> primary_code fallback
validated_model_hash -> validated primary_code fallback
stale model layer -> primary_code
```

这些映射只表示 primary implementation identity。若 legacy 与 canonical 值同时存在且不一致，必须返回 `blocking inconsistency`。禁止任选一边继续，禁止以“新字段优先”静默覆盖，也禁止以“兼容”为理由静默回退。

`dependency_kind: model` 继续保留，因为它表示数学模型语义依赖，不是已退休的 implementation artifact alias。

## 4. 禁止自动迁移的 semantic identity / approval

以下转换明确禁止：

```text
semantic_hash -X-> semantic_identity_hash
validated_semantic_hash -X-> validated_semantic_identity_hash
approved_semantic_hash -X-> approved_semantic_identity_hash
```

legacy text hash 与 structured SIB identity 不是同一种证据。禁止从 legacy prose 自动生成 SIB 后直接标记 validated，禁止从 legacy approval 自动继承 current structured approval，也禁止自动把 challenge/approval 状态改成 passed/approved。

**partial structured state 必须 fail closed**，不得回退 legacy approval 继续求解。

## 5. 三类事实源继续分离

- `模型论文框架.md`：当前模型语义与论文结构记忆；
- `state/project_state.yaml`：机器生命周期与状态；
- accepted workbooks：具体数值事实源。

workbook 数值、Markdown result summary 或可复现实验均不能替代 structured semantic approval。

## 6. v8.7.x / v8.9.0 → v9.0.0 升级路径

只读历史项目：

```text
v8.x project -> L0 -> historical read-only adapter
-> no forced SIB write -> no new solve/code authorization
```

重新进入建模/求解：

```text
v8.x project -> snapshot under v8.9.0 -> L1
-> candidate SIB -> semantic validation -> Model Challenge
-> explicit Human Approval -> current structured identity authorizes new code
```

已采用 structured identity：

```text
current structured project -> L2 -> re-verify current Framework identity
-> preserve approval only while all structured evidence remains current
```

## 7. 自动迁移 / 人工确认矩阵

| Surface / 状态 | 自动迁移 | 人工确认 | 冲突处理 |
|---|---|---|---|
| historical `artifact_hashes.model` → `primary_code` | 仅 pre-schema adapter 可机械归一化 | 通常不需要 | 新旧不同则 blocking |
| historical validated `model` → `primary_code` | 仅 pre-schema adapter 可机械归一化 | 通常不需要 | 新旧不同则 blocking |
| `model_hash / validated_model_hash` fallback | 仅 historical implementation fallback | 冲突时需要 | 不得解释为 semantic identity |
| stale `model` → `primary_code` | 仅 historical pre-schema adapter | 不需要 | unknown layer 按 Authority 处理 |
| `semantic_hash` → structured identity | **禁止** | 必须建立/验证 SIB | 不可复制 hash |
| legacy approval → structured approval | **禁止** | **必须显式 Human Approval** | 不可自动继承 |
| partial structured identity | 禁止 legacy fallback | 修复并重新验证 | fail closed |
| L0 只读历史项目 | 不强制迁移 | 无新求解时不需要 | read-only adapter |
| L1 重新求解 | 不自动批准 | 必须 | 未批准不得进主求解 |
| L2 current structured | 不做无意义重建 | 仅证据变化时重新审批 | mismatch fail closed |

## 8. 回滚契约

最后稳定 v8.x 基线是 `8.9.0`。代码级回滚应 revert 对应 v9 PR 或恢复到明确记录的 v8.9.0 checkpoint；不得用盲目版本字符串替换回滚。

若真实 project state 已在 v9 下被显式迁移/修改：

1. 必须使用迁移前 snapshot/backup；
2. 不能只降级 Skill 代码后假设 current state 自动重新兼容 v8；
3. 不得留下“部分 canonical、部分 legacy”的 accepted state；
4. 冲突状态必须先解释来源再继续。

I5 本身不执行真实用户项目的批量迁移，也不新增自动迁移 CLI。

## 9. Compatibility reader 退出策略

**初始 v9.0.0 不要求**为了“清理彻底”而删除所有 historical reader。当前保留：

- L0 明确、窄、read-only historical semantic adapter；
- historical implementation aliases 的 pre-schema audit/migration helper。

L1 不得借 historical adapter 绕过 SIB / challenge / Human Approval。

**historical reader 的彻底删除**必须作为 v9.0.0 之后的独立兼容性决策，需要真实迁移采用证据、无 active dependency 的 code search、单独 release/migration 说明与完整 CI；不得在 I5 顺手删除。

## 10. v9.0.0 最终 release contract

当前 release carrier：`9.0.0`。

当前 Phase I 状态：**closed for v9.0.0 repository release**。

已退休的 active 面：legacy semantic new writes、implementation artifact legacy aliases/fields/stale layer。

保留的兼容面：L0 semantic historical read-only path、pre-schema implementation audit/migration helper，以及与本次 Phase-I target 无关的独立 compatibility。

`9.0.0` 之后若继续删除 historical readers，必须开启新的独立治理变更。
