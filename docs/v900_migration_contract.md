---
status: phase_i_i1_draft_pre_destructive
baseline_skill_version: 8.9.0
baseline_main_commit: c8687dd89d3b90fd288d9d375c0341e2750cf510
parent_plan: docs/semantic_state_runtime_refactor_plan.md
inventory: docs/phase_i_compatibility_inventory.md
candidate_final_version: 9.0.0
runtime_authority: false
destructive_compatibility_removal_authorized: false
---

# Phase I I1 — v8.9.0 → v9.0.0 Migration Contract

> 本文件是 v9 迁移契约草案与验收基线，不是 Runtime Authority。它不能覆盖 `core/project_state.schema.yaml`、`core/model_approval_contract.yaml`、`core/runtime_assurance_contract.yaml`、`core/state_transition_contract.yaml` 或当前脚本行为。真正停止 legacy write、删除 Schema 字段或删除 compatibility reader 时，仍必须在独立 PR 中修改对应 Authority/实现并重新通过完整测试。

## 1. 目的与当前边界

`8.9.0` 已作为稳定 v8.x compatibility checkpoint 合并到 `main`，因此原计划 Phase I Gate 1“至少一个稳定版本已写新字段”已经满足。

I1 的目标不是执行迁移，而是固定 **迁移允许做什么、禁止做什么、何时必须重新 Human Approval、发生冲突时如何 fail closed**。本阶段只更新 docs / fixtures / acceptance tests。

I1 明确不做：

- 不停止无 SIB legacy 项目的 `semantic_hash / validated_semantic_hash` write path；
- 不删除 `artifact_hashes.model`、`model_hash / validated_model_hash`、legacy stale `model` layer 或任何 Schema property；
- 不把 legacy `semantic_hash` 复制为 `semantic_identity_hash`；
- 不把 legacy `approved_semantic_hash` 复制为 `approved_semantic_identity_hash`；
- 不自动生成、自动验证或自动批准 Semantic Identity Block（SIB）；
- 不改变 Model Challenge / Human Model Approval 状态；
- 不修改任何 `<9.0.0` compatibility boundary；
- 不执行项目文件写入，也不新增自动迁移 CLI；
- 不把本轮“继续修改”解释为用户已经授权结束 v8 project write compatibility。

## 2. 迁移对象分类

### L0 — Historical read-only legacy project

特征：

- Framework 无 SIB；
- legacy semantic hash / approval provenance 存在；
- 项目只用于查看历史结果、复核或审计。

v9 初始版本目标行为：

- 保留窄的 historical read adapter；
- legacy approval 仅作为 historical provenance 读取；
- `locked_model_spec` 不得被提升为 current `verified`；
- 不要求为了只读审计而强制构造 SIB；
- 一旦重新进入模型设计、预处理、主求解或新代码生成，立即转为 L1。

### L1 — Legacy project re-entering active modeling / code workflow

特征：

- 起点与 L0 相同；
- 用户要求重新进入 `model_design / data_preprocessing / solve_validate`，或需要生成新的主代码。

迁移顺序必须为：

1. 在最后稳定 v8.x（`8.9.0`）状态下保留项目快照/备份；
2. 由模型设计流程形成 **candidate SIB**，不得从旧 prose 静默推断成“已验证身份”；
3. semantic governance 对 current Framework 中的 SIB 做 canonical validation，并得到 current `semantic_identity_hash`；
4. Model Challenge 对当前 structured semantics 通过；
5. 用户对当前 semantic revision 与 current validated structured identity 做 **显式 Human Approval**；
6. 只有上述条件全部满足后，才允许进入新的主代码生成 / solve workflow。

legacy `semantic_hash / approved_semantic_hash` 可以作为历史证据保留，但不能授权第 6 步。

### L2 — Current structured project

特征：

- Framework 中存在完整可解析的 SIB；
- current / validated / approved structured identity 一致；
- current revision、Model Challenge 与 Human Approval 一致。

迁移原则：

- 不因为“升级版本号”本身使 current structured Human Approval stale；
- Runtime Assurance 仍必须重新从当前 Framework 计算 structured identity，而不是相信 state 自证；
- 若 current / validated / approved identity 不一致，按现有 Authority fail closed；
- implementation artifact 的 legacy alias 仅允许按 §3 做机械归一化。

## 3. 允许的机械迁移

只有 **身份含义完全确定且冲突可检测** 的 implementation/stale alias 可以机械归一化。

### 3.1 Artifact implementation identity

当前共享 helper `scripts/artifact_identity.py` 已定义安全映射：

```text
artifact_hashes.model
  -> artifact_hashes.primary_code

validated_artifact_hashes.model
  -> validated_artifact_hashes.primary_code
```

当 canonical key 缺失时，还允许将：

```text
model_hash
  -> artifact_hashes.primary_code fallback

validated_model_hash
  -> validated_artifact_hashes.primary_code fallback
```

但这些 fallback 只用于保留已知的 **primary implementation identity**，不能解释为数学模型语义身份。

### 3.2 Stale layer alias

```text
stale_layers: model
  -> stale_layers: primary_code
```

这个映射只表示 v8 implementation layer 命名迁移，不触发 mathematical semantic approval stale。

### 3.3 冲突规则

若 legacy 与 canonical 值同时存在且不一致：

```text
blocking inconsistency
```

禁止：

- 任选一个值继续；
- 以“新字段优先”为理由静默覆盖；
- 以“旧字段兼容”为理由静默回退；
- 在不知道来源的情况下重新计算一个值并覆盖两者。

必须先人工/确定性地解释冲突来源，再继续迁移。

## 4. 禁止的自动语义迁移

以下转换在 v9 migration 中 **明确禁止自动执行**：

```text
semantic_hash
  -X-> semantic_identity_hash

validated_semantic_hash
  -X-> validated_semantic_identity_hash

approved_semantic_hash
  -X-> approved_semantic_identity_hash
```

原因：legacy semantic hash 是 Markdown semantic-scope text hash；structured identity 是 canonical SIB 的数学语义身份。二者不是同一种证据，不能通过字段复制、重命名或 hash 重用建立等价关系。

同样禁止：

- 从 legacy prose 自动生成 SIB 后直接标记 validated；
- 从 legacy approval 推导 current structured Human Approval；
- 自动把 `model_challenge_status` 改为 `passed`；
- 自动把 `human_model_approval_status` 改为 `approved`；
- structured identity 只存在一部分时回退 legacy approval 继续求解。

partial structured state 必须 fail closed，而不是混用两套 identity。

## 5. 数值事实与论文内容不参与身份偷换

迁移不得改变仓库现有三类事实边界：

- `模型论文框架.md`：当前模型语义与论文结构记忆；
- `state/project_state.yaml`：机器生命周期/状态；
- accepted workbooks：数值事实源。

因此：

- 不能从 workbook 数值结果反推出“模型已被批准”；
- 不能从 Markdown result summary 代替 accepted workbook；
- 不能因为旧 workbook 仍可复现，就自动继承旧 semantic approval 到新的 structured identity。

## 6. v8.7.x / v8.9.0 项目升级路径

### 6.1 只读历史项目

```text
v8.x project
-> classify as L0
-> keep historical read adapter
-> no forced SIB write
-> no new solve/code authorization
```

### 6.2 重新进入建模/求解的旧项目

```text
v8.x project
-> classify as L1
-> snapshot under v8.9.0 compatibility checkpoint
-> build candidate SIB through model-design flow
-> semantic validation
-> Model Challenge
-> explicit Human Approval
-> current structured identity becomes authoritative for new code
```

### 6.3 已采用 structured identity 的项目

```text
current structured project
-> classify as L2
-> re-verify current Framework identity
-> preserve current approval only when all structured evidence remains current
-> mechanically normalize implementation aliases when safe
```

## 7. 自动迁移与人工确认矩阵

| Surface / 状态 | 自动迁移 | 人工确认 | 冲突处理 |
|---|---|---|---|
| `artifact_hashes.model` → `primary_code` | 允许 | 通常不需要 | 新旧不同则 blocking |
| `validated_artifact_hashes.model` → `primary_code` | 允许 | 通常不需要 | 新旧不同则 blocking |
| `model_hash` / `validated_model_hash` fallback | 允许作为 implementation fallback | 冲突时需要 | 不得解释为 semantic identity |
| stale `model` → `primary_code` | 允许 | 不需要 | 未知 layer 继续按 Authority 处理 |
| `semantic_hash` → structured identity | **禁止** | 必须重新建立 SIB | 不可复制 hash |
| legacy approval → structured approval | **禁止** | **必须显式 Human Approval** | 不可自动继承 |
| partial structured identity | 禁止 legacy fallback | 需要修复/重新验证 | fail closed |
| L0 只读历史项目 | 不强制迁移 | 无新求解时不需要 | 只读 adapter |
| L1 重新求解 | 不自动批准 | 必须 | 未批准不得进主求解 |
| L2 current structured | 不做无意义重建 | 仅证据变化时重新审批 | mismatch fail closed |

## 8. 回滚契约

I1 本身不执行项目写入，因此没有项目数据层面的不可逆副作用。

未来 destructive migration PR 必须满足：

1. 迁移前保留可恢复的 project-state / framework 快照；
2. migration 失败时不得留下“部分 canonical、部分 legacy”的已接受状态；
3. 若需要回滚代码，最后稳定 v8.x 基线为 `8.9.0`；
4. 若项目文件已经由未来 migration writer 修改，必须使用该 PR 明确提供的 rollback path / backup，而不能只降级 Skill 代码后假定旧 state 自动兼容。

## 9. Compatibility reader 的退出策略

原计划要求 major 前停止旧写，并由 code search 证明旧字段只剩 compatibility reader / docs。由此可见，**初始 v9.0.0 不要求为了“清理彻底”而删除所有 historical reader**。

v9.0.0 的目标是：

- 停止被批准删除对象的 legacy write；
- 删除无必要的 active Schema/write aliases；
- 对 L0 保留明确、窄、read-only 的 historical adapter；
- L1 不允许借 historical adapter 绕过 structured migration/approval。

historical reader 的彻底删除应作为 v9.0.0 之后的独立兼容性决策，至少需要真实迁移采用证据、无 active dependency 的 code search 以及独立 release/migration 说明，不能塞进 Phase I 的最后清理中顺手删除。

## 10. 当前 Phase I Gate 快照（I1）

| Gate | I1 状态 | 证据 / 说明 |
|---|---|---|
| 1. 至少一个稳定版本已写新字段 | **satisfied** | `8.9.0` stable compatibility checkpoint 已合并到 `main@c8687dd8...`，PR head 与 post-merge main 均执行完整 CI |
| 2. migration fixtures 全绿 | **satisfied as current baseline** | I0 L0/L1/L2 matrix 已在 8.9.0 release CI 中通过；任何后续 destructive PR 必须再次全绿 |
| 3. 活动代码不再写旧字段 | **false** | no-SIB legacy semantic governance 仍写 `semantic_hash / validated_semantic_hash` |
| 4. code search 只剩 compatibility reader/docs | **partial** | artifact identity 接近目标；semantic legacy 仍有 writer/Schema/reader |
| 5. 用户确认结束 v8 project write compatibility | **false / not inferred** | “继续修改”不等同于 destructive-boundary approval |
| 6. Changelog + migration doc 完整 | **partial** | 本文件固定迁移契约，但真正停止旧写/删除字段后的最终字段清单与 release migration notes 尚未完成 |

因此 I1 合并后仍不得直接执行 destructive compatibility removal。

## 11. I1 退出条件

- migration contract 与当前 8.9.0 行为一致；
- migration matrix 把 stable compatibility window 记录为 closed；
- acceptance tests 明确保护：mechanical alias migration 可做、semantic identity / approval 不得自动合成、冲突必须 blocking；
- 全量 unit、lint、generated check 与标准 CI 继续全绿；
- PR diff 不包含任何 Runtime Authority、Schema 或 runtime implementation 修改；
- Skill release carrier 继续为 `8.9.0`。
