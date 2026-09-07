---
status: phase_i_i2_readiness_pre_destructive
baseline_skill_version: 8.9.0
baseline_main_commit: c2da692299e01463f3a2a657c25d9bc9c69dca90
parent_plan: docs/semantic_state_runtime_refactor_plan.md
migration_contract: docs/v900_migration_contract.md
inventory_fixture: tests/fixtures/v900_phase_i_writer_retirement_inventory.yaml
candidate_final_version: 9.0.0
runtime_authority: false
legacy_writer_retirement_authorized: false
---

# Phase I I2 — Legacy Writer Retirement Readiness

> 本文件只冻结 **未来 I2 应修改的精确 writer / reader / Schema 边界**。它不是 Runtime Authority，不停止任何 writer，不删除任何字段，也不代表用户已经确认结束 v8 project write compatibility。

## 1. 为什么 I2 必须先做 readiness

I1 已经固定了 v8.9.0 → v9.0.0 的迁移契约：implementation alias 可以在冲突可检测时机械归一化，但 legacy Markdown semantic hash 与 structured SIB identity 不是同一证据，不能自动互换；L0 historical project 需要窄的 read-only adapter，L1 重新进入建模/求解则必须形成 current SIB、重新通过 Model Challenge 并取得显式 Human Approval。

因此，Phase I Gate 3“活动代码不再写旧字段”不能通过全仓字符串替换或一次性删除 `semantic_hash*` 实现。当前必须先把三种不同职责分离：

1. **仍在主动写的 legacy semantic fields**；
2. **已经没有 writer、仅作 historical provenance/read fallback 的字段**；
3. **初始 v9 仍需保留的窄 historical reader**。

只有第一类是未来 I2 writer-retirement 的直接行为修改对象。

## 2. 当前唯一确认的 legacy semantic writer

当前 `scripts/validate_semantic_governance.py::validate_project()` 在 `write=True` 且当前 question 的 semantic identity mode 为 `legacy_text_hash` 时，仍执行：

```text
entry["semantic_hash"] = text_hash
entry["validated_semantic_hash"] = current_hash   # gate/revision/category 条件满足时
```

也就是说：

- `semantic_hash` 仍是 active write surface；
- `validated_semantic_hash` 仍是 active write surface；
- writer 只属于 **无 SIB / legacy_text_hash** 分支；
- structured SIB 分支写的是 `semantic_identity_hash / validated_semantic_identity_hash / semantic_text_hash`，不应被 I2 retirement 误伤。

未来真正执行 I2 时，目标不是把 legacy 分支“改写成 structured identity writer”，而是停止它继续刷新 legacy semantic approval evidence，并让重新进入 active workflow 的旧项目按 I1 迁移契约转向 structured identity。

## 3. 不属于 writer-retirement 的字段

### 3.1 `approved_semantic_hash`

当前职责是 legacy Human Approval provenance。Model Approval validator 已明确：

- legacy semantic approval 只有显式 `allow_legacy_read_only=True` 时才允许历史审计；
- 默认 task-code authorization 不接受 legacy approval；
- 旧项目要重新进入 task-code delivery，必须 current SIB + Model Challenge + explicit Human Approval。

当前没有 active refresh/write path 应在 I2 中“停止”。因此未来 I2 应保留其 historical read semantics，而不是和 `semantic_hash / validated_semantic_hash` 一起机械删除。

### 3.2 `model_hash / validated_model_hash`

这两个字段是 v8 primary-code implementation identity fallback。当前 Schema 已明确“活动代码无 writer”，共享 `artifact_identity.py` 只将它们作为 `artifact_hashes.primary_code / validated_artifact_hashes.primary_code` 的 fallback reader。

它们属于后续 artifact alias cleanup，而不是 semantic writer retirement。若把它们塞进 I2，同一个 PR 会同时改变数学语义身份与 implementation identity 两个边界，不符合单主题 PR 原则。

### 3.3 stale `model` layer

legacy stale `model` 只映射到 `primary_code`，属于 implementation layer 命名兼容。它不代表 mathematical semantic identity，也不应在 semantic writer retirement PR 中顺手删除。

## 4. 当前 Schema 必须同步但不能提前修改

`core/project_state.schema.yaml` 当前仍明确声明：

- `semantic_hash`：无 SIB 项目继续兼容读取/写入；
- `validated_semantic_hash`：无 SIB 项目继续兼容读取/写入；
- `approved_semantic_hash`：legacy approval 只读兼容；
- `model_hash / validated_model_hash`：活动代码无 writer，只读 fallback。

因此未来真正停止 semantic legacy write 时，必须在同一个行为 PR 中同步调整 Schema 描述/允许面，使 Authority 与实现一致。不能先在 docs-only PR 中把 Schema 宣称成 read-only，也不能只删 writer 而保留“继续读写”的 Authority 文本。

I2-readiness 本身明确禁止修改 Schema。

## 5. 初始 v9 必须保留的 historical readers

### 5.1 Model Approval historical reader

`scripts/validate_model_approval.py` 对 legacy approval 的默认行为已经是 fail closed；只有调用方显式设置 `allow_legacy_read_only=True` 才允许历史审计。

未来 I2 停止 legacy semantic write 后，这个 read-only adapter 仍应保留，以满足 L0 historical project 的审计需求。不得因为 code search 看到 `semantic_hash / approved_semantic_hash` 就把该 reader 当作“未清理干净”。

### 5.2 Runtime Assurance historical evidence

legacy no-SIB 项目应继续返回 historical / review-required evidence，而不能升级为 current `verified locked_model_spec`。I2 必须维持这一 fail-closed 边界。

### 5.3 Artifact identity readers

`artifact_identity.py` 的 legacy `model` / `model_hash` reader 与 semantic writer retirement 无关。它们保留到后续 artifact alias removal PR，并继续执行 conflict blocking。

## 6. 未来 I2 行为 PR 的最小修改顺序

只有在 **Phase I Gate 5 得到用户显式确认** 后，未来 I2 implementation PR 才可以开始。建议严格按以下顺序：

1. **Pre-change characterization**
   - 锁定无 SIB + `write=False` 的 historical validation 行为；
   - 锁定无 SIB + `write=True` 当前会写 `semantic_hash / validated_semantic_hash`；
   - 锁定 structured SIB writer 完全不依赖 legacy semantic fields；
   - 锁定 L0/L1/L2 migration matrix。
2. **停止 active legacy semantic write**
   - 无 SIB 分支不再刷新 `semantic_hash / validated_semantic_hash`；
   - 不自动创建 SIB；
   - 不自动复制 legacy hash 到 structured fields；
   - active reentry 必须转入 I1 的 structured migration / approval gate。
3. **同步 Authority / Schema**
   - 将 `semantic_hash / validated_semantic_hash` 从“无 SIB 兼容读写”收敛为 historical read-only，或按最终 v9 Schema 决策移出 active property surface；
   - `approved_semantic_hash` 保持 historical provenance，除非另一个独立删除决策明确覆盖。
4. **保留 historical reader**
   - L0 只读审计可继续；
   - L1 不得借 reader 绕过 structured migration；
   - partial structured identity 仍 fail closed。
5. **重新 code search**
   - 证明 active scripts 不再对 legacy semantic fields 赋值；
   - 剩余引用必须被分类为 historical reader、migration fixture/test 或 docs；
   - Gate 4 不能仅凭字符串数量判断，必须逐引用分类。
6. **完整测试与 migration notes**
   - Python 3.10–3.14；
   - Static / Generated；
   - L0/L1/L2；
   - semantic governance / model approval / runtime assurance；
   - LaTeX / Production attestation；
   - 更新最终 migration field table / Changelog。

## 7. 不能在未来 I2 中混入的工作

即使 Gate 5 已满足，writer-retirement PR 也不应同时执行：

- 删除 `model_hash / validated_model_hash`；
- 删除 `artifact_hashes.model`；
- 删除 stale `model` alias；
- 删除所有 historical semantic reader；
- 全仓替换 `<9.0.0`；
- 升级到 `9.0.0` release carrier；
- 重构 semantic parser / state transition / transaction engine；
- 修改 competition writing runtime。

这些都应在 writer retirement 验证稳定之后按独立主题处理。

## 8. 测试分类：哪些未来要改，哪些必须长期保留

### 8.1 Future I2 implementation 必须修改的 legacy-writer characterization

例如 `tests/test_v710_semantic_governance.py` 当前明确验证首次 `write=True` 会写 `validated_semantic_hash`。这是 **当前行为 characterization**，未来停止 writer 时必须有意更新为新的迁移/拒绝行为，不能简单删除测试。

### 8.2 必须保留的 historical-reader tests

- `validate_model_approval(..., allow_legacy_read_only=True)` 对合法历史 provenance 仍可通过；
- 默认 code authorization 对 legacy approval 仍失败；
- Runtime Assurance 对 legacy project 不得给 current verified model；
- L0/L1/L2 migration matrix 继续保护 read-only 与 active-reentry 的区别。

### 8.3 Structured identity tests 不应被 I2 改写

SIB canonicalization、structured semantic identity validation、Model Challenge / Human Approval binding、partial structured fail-closed 均是 v9 新主路径，不属于 legacy writer retirement 的待删除行为。

## 9. Gate 状态（I2 readiness）

| Gate | 状态 | 解释 |
|---|---|---|
| 1. stable version 写新字段 | **satisfied** | 8.9.0 stable checkpoint 已发布并经完整 CI |
| 2. migration fixtures green | **satisfied as current baseline** | I1 L0/L1/L2 + migration contract 已合并并通过完整 CI |
| 3. active code 不再写旧字段 | **false** | semantic governance 无-SIB `write=True` 分支仍写两个 legacy semantic fields |
| 4. old refs 只剩 reader/docs | **false / not yet** | writer 与 Schema read/write declaration 仍存在 |
| 5. 用户确认结束 v8 write compatibility | **false / not inferred** | 当前“继续修改”不等于 destructive-boundary approval |
| 6. Changelog + final migration docs complete | **false / partial** | I1/I2 readiness 已定义契约，但尚未发生实际字段退休与最终 release note |

I2-readiness 合并不会改变上述 Gate 3–6，也不会授权 future I2 implementation。

## 10. 回滚与风险控制

本 readiness PR 不改 runtime 或项目文件，因此回滚为整 PR revert，无项目数据副作用。

未来 writer-retirement implementation PR 必须：

- 以 8.9.0 project snapshot 作为回滚起点；
- 在写项目状态前保持 transaction semantics；
- 失败时不得留下“legacy fields 已停止更新、structured identity 又未建立”的半迁移 accepted state；
- 不以自动 SIB/approval 合成来填补迁移空档；
- 若出现无法解释的新旧字段冲突，blocking 而不是 silent normalization。

## 11. I2-readiness 退出条件

- 机器 inventory 与当前 `main` writer/reader/Schema 事实一致；
- 测试能够证明当前只有 `semantic_hash / validated_semantic_hash` 属于确认的 active legacy semantic write surface；
- 测试明确保护 Gate 5 仍为 false；
- PR 不包含 `scripts/**`、`core/**`、Schema、release carrier 或 compatibility range 修改；
- 全量 unit / lint / generated / standard CI 全绿；
- 合并后仍不能执行 destructive writer retirement，直到用户显式确认 Gate 5。
