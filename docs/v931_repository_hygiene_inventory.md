# v9.3.1 Repository Hygiene Inventory

> 仓库：`Vexushi1/mathmodel-skill`  
> 审计基线：`main@f028b2dc320f5ad8dd731d60903126fc2d193fae`  
> 当前 Skill：`9.3.1`  
> 状态：`H0_INVENTORY_MERGED / H1_INDEX_SEGMENTATION_IN_PROGRESS`  
> 角色：维护清单与治理证据，不是 Runtime / Modeling / Approval Authority。

## 1. Hygiene 边界

本阶段只做 repository hygiene，不改变数学建模业务语义。

明确保持不变：

- Runtime / Router / Resolver 的业务语义；
- Model Challenge / Human Approval；
- Semantic Identity / typed stale；
- Workbook / Output / User Execution；
- Python / MATLAB ownership；
- LaTeX 正式交付链；
- 当前 release `9.3.1`。

本阶段顺序：

```text
H0  inventory + risk classification
H1  Active Index 分层（保留原文件路径，优先非破坏性）
H2  merged branch cleanup（仅 SAFE_DELETE_CANDIDATE）
H3  docs archive/move/delete（只有 H1 仍无法降低噪声时再评估）
```

任何 branch 删除、历史 docs 迁移或删除都不得先于 inventory。

---

# 2. 仓库总体概况

本次重新枚举得到：

- Branches：**177**
- 当前 open PR：**0**
- 当前 release：**9.3.1**
- v9.3 / v9.3.1 相关残留 branch：**13**
- 当前所有枚举 branch 的 `protected=false`；这不替代仓库规则集/branch-protection 的独立治理判断。
- `docs/` 当前文件：**41**

主要 branch prefix 数量（本轮枚举）：

| prefix | count |
|---|---:|
| `docs/` | 27 |
| `fix/` | 49 |
| `refactor/` | 35 |
| `release/` | 4 |
| other | 62 |

> 说明：branch 数量相比 v9.3.0 post-release audit 的约 168 已增长到 177，主要来自本轮 remediation / release / verification 分支；因此 branch hygiene 已成为实际维护成本，而非纯视觉问题。

---

# 3. Branch 判定语义

## 3.1 为什么不能只看 `ahead_by`

本仓库大量 PR 使用 **squash merge**。因此：

- feature branch 的原始 commits 可能永远不会成为 `main` 的祖先；
- `compare main...branch` 可显示 `ahead_by > 0` / `diverged`；
- 这不自动表示 branch 仍有未合并业务内容。

因此本 inventory 同时记录：

1. branch 当前 tip SHA；
2. 对应 PR 是否 merged；
3. 当前 branch tip 是否等于该 PR 的 final head SHA；
4. commit-level `ahead_by / behind_by`；
5. 是否存在“post-merge branch advance”证据。

### SAFE_DELETE_CANDIDATE

对于 squash-merged branch，以下证据足以说明“无 post-merge branch advance”：

- associated PR 已 merged；
- current branch tip == merged PR final head SHA；
- 无 open PR；
- branch 非 protected；
- 未被明确要求长期保留。

这类 branch 的 `ahead_by>0` 仅表示 squash 后 commit identity 没进入 main，不等同于未合并内容。

### MANUAL_REVIEW

以下任一情形进入人工复核：

- 无 associated PR；
- branch tip 与 PR final head 不同；
- branch 有 open PR；
- branch protected；
- branch 被指定为长期 provenance 分支；
- 不能证明当前 tip 内容已经被 main/release 包含。

---

# 4. v9.3 / v9.3.1 Branch Inventory

| branch | tip SHA | last commit (UTC) | PR | merged | tip=PR head | compare main...branch | protected | recommendation |
|---|---|---|---:|---|---|---|---|---|
| `docs/v9.3.1-maintenance-status-alignment` | `3e9acad1` | 2026-09-18 15:28:44 | #186 | yes | yes | ahead 7 / behind 3 | no | **SAFE_DELETE_CANDIDATE** |
| `docs/v9.3.1-postrelease-health-remediation-plan` | `4766b608` | 2026-09-18 12:19:12 | #181 | yes | yes | ahead 2 / behind 8 | no | **SAFE_DELETE_CANDIDATE** |
| `docs/v9.3.1-postrelease-verification-closeout` | `09b2cacf` | 2026-09-18 15:58:46 | #188 | yes | yes | ahead 2 / behind 1 | no | **SAFE_DELETE_CANDIDATE** |
| `docs/v9.3.1-prb-status-closure` | `13985060` | 2026-09-18 15:00:00 | #184 | yes | yes | ahead 2 / behind 5 | no | **SAFE_DELETE_CANDIDATE** |
| `fix/v9.3.1-model-design-capability-restoration` | `02d4893c` | 2026-09-18 13:04:24 | #182 | yes | yes | ahead 6 / behind 7 | no | **SAFE_DELETE_CANDIDATE** |
| `fix/v9.3.1-structural-reduction-surface-alignment` | `3128dfd9` | 2026-09-18 15:15:44 | #185 | yes | yes | ahead 11 / behind 4 | no | **SAFE_DELETE_CANDIDATE** |
| `fix/v9.3.1-task-pack-budget-closure` | `f0e2f08a` | 2026-09-18 13:18:46 | #183 | yes | yes | ahead 17 / behind 6 | no | **SAFE_DELETE_CANDIDATE** |
| `refactor/v9.3.0-domain-reduction-cues` | `3bb66e2a` | 2026-09-18 00:25:12 | #179 | yes | yes | ahead 38 / behind 10 | no | **SAFE_DELETE_CANDIDATE** |
| `refactor/v9.3.0-initial-modeling-core` | `fc4e31a9` | 2026-09-17 09:36:00 | #178 | yes | yes | ahead 18 / behind 11 | no | **SAFE_DELETE_CANDIDATE** |
| `refactor/v9.3.0-release-metadata-refresh` | `3767804c` | 2026-09-18 02:19:39 | — | — | — | ahead 21 / behind 9 | no | **MANUAL_REVIEW** |
| `refactor/v9.3.1-release-metadata-refresh` | `bb5d51a7` | 2026-09-18 15:40:07 | helper in PR #187 commit list | release merged | n/a | ahead 3 / behind 2 | no | **SAFE_DELETE_CANDIDATE** after release provenance check |
| `release/v9.3.0-closeout` | `b956c4c6` | 2026-09-18 02:20:09 | #180 | yes | yes | ahead 19 / behind 9 | no | **SAFE_DELETE_CANDIDATE** |
| `release/v9.3.1-closeout` | `3609f424` | 2026-09-18 15:48:27 | #187 | yes | yes | ahead 9 / behind 2 | no | **SAFE_DELETE_CANDIDATE** |

## 4.1 H0 结论

当前 v9.3 / v9.3.1 残留中：

- **SAFE_DELETE_CANDIDATE：12**
- **MANUAL_REVIEW：1**
- **BLOCKED：0**
- **ACTIVE_UNKNOWN：0**

`refactor/v9.3.0-release-metadata-refresh` 暂不删除：它没有直接 PR 绑定，且其 tip SHA 不在 PR #180 commit list 中；后续应通过 tree/content provenance 再确认。

---

# 5. Docs / Active Index Inventory

当前 `scripts/generate_indexes.py` 的 `is_active_path()` 逻辑是：

- 排除 `legacy/`（只保留 `legacy/README.md`）；
- 但 **所有 `docs/` 文件默认都被视为 active path**；
- 因此 41 个 docs 全部进入 `SKILL_FILE_INDEX.md` 的平铺列表。

这会把维护记录、旧 migration provenance、旧 release plan 与真实 Runtime/Reference 文件放在同一 Active Index 表面。

## 5.1 分类

### A. current_reference

这些文件仍有活动 test / compatibility consumer 或提供当前仍需保留的稳定解释：

- `docs/v871_writing_reasoning_schema_version_policy.md`
  - 被 `tests/test_v871_writing_reasoning_schema_policy.py` 直接读取；
- `docs/v900_migration_contract.md`
  - 被 v9 compatibility / release closure tests 与 migration fixtures 直接读取。

### B. current_maintenance_status

- `docs/skill_optimization_status.md`
  - 当前优化/发布实施记录；
  - 被 optimization-baseline workflow 的 path surface 覆盖；
- `docs/v931_postrelease_health_remediation_plan.md`
  - 当前已完成的 v9.3.1 remediation / hygiene 母计划；
  - 仍作为本 Repository Hygiene 的父级治理记录。

### C. migration_contract / compatibility provenance

建议继续保留原路径，暂不迁移：

- `docs/phase_e_artifact_identity_inventory.md`
- `docs/phase_f_transaction_writer_inventory.md`
- `docs/phase_i_artifact_alias_retirement.md`
- `docs/phase_i_artifact_state_surface_removal.md`
- `docs/phase_i_compatibility_inventory.md`
- `docs/phase_i_compatibility_removal_readiness.md`
- `docs/phase_i_legacy_writer_retirement.md`
- `docs/phase_i_legacy_writer_retirement_readiness.md`
- `docs/phase_i_v9_applicability_renewal.md`
- `docs/phase_i_v9_release_carrier_transition.md`
- `docs/phase_i_v9_release_closure.md`

原因：其中若干文件被 v9 migration tests / fixtures 显式引用。H0 不移动它们。

### D. historical_provenance

建议在 H1 从“Active Runtime/Reference”索引表面移到 **Historical Maintenance Provenance** 分区，但文件先保持原路径：

- `docs/main-branch-protection-hardening-plan.md`
- `docs/matlab_publication_rendering_v91_plan.md`
- `docs/p3a_global_policy_source_map.md`
- `docs/p3b_writing_role_source_map.md`
- `docs/p4_compact_framework_progression.md`
- `docs/p5a_run_config_migration.md`
- `docs/p5b_run_receipt_versioning.md`
- `docs/p6a_figure_reference_profile_split.md`
- `docs/p6b_matlab_rendering_preview.md`
- `docs/p7_conditional_analysis_appendix.md`
- `docs/p8_infrastructure_measurement.md`
- `docs/p8d_lint_function_measurement.md`
- `docs/p8e_validator_split_decision.md`
- `docs/p9_release_closeout.md`
- `docs/semantic_state_runtime_refactor_plan.md`
- `docs/v801_chapter_capability_preservation_audit.md`
- `docs/v801_skill_health_remediation_plan.md`
- `docs/v801_skill_health_remediation_status.md`
- `docs/v840_author_reasoning_evaluation.md`
- `docs/v850_author_reasoning_voice_evaluation.md`
- `docs/v860_model_construction_solution_rationale_evaluation.md`
- `docs/v870_question_writing_capability_preflight_evaluation.md`
- `docs/v8_writing_capability_inventory.md`
- `docs/v8_writing_migration.md`
- `docs/v921_p7_conditional_analysis_semantic_hygiene_plan.md`
- `docs/v9_3_initial_modeling_structural_reduction_refactor_plan.md`

### E. obsolete_duplicate

**H0 暂无任何文件被证明为可安全删除的 obsolete duplicate。**

原则：没有 byte-identical / superseded-with-no-consumer / no-provenance 证据前，不用文件名判断“无用”。

---

# 6. H1 建议：非破坏性 Active Index 分层

首选不移动任何 docs，只调整生成索引的**展示层**：

```text
HSK Active Skill File Index

1. Active Runtime & Reference
2. Current Maintenance / Migration Records
3. Historical Maintenance Provenance
4. Legacy pointer
```

关键约束：

- `MANIFEST.sha256` 仍覆盖这些文件；
- 文件物理路径不变；
- test/fixture references 不变；
- Runtime resolver 不读取该分类来授权业务行为；
- 不把 historical docs 从仓库删除；
- 不把 migration contracts 移入 `legacy/`，除非后续独立测试证明可以迁移；
- `TEMPLATE_INDEX.md` 逻辑不因 docs 分层改变。

这样先解决“Active Index 看起来所有历史文档都是当前 Authority”的噪声，而不制造路径迁移风险。

---

# 7. H2 Branch Cleanup Gate

真正删除 branch 前，对每一个候选必须再次检查：

1. 当前 branch tip 未发生变化；
2. associated PR 仍为 merged；
3. 无 open PR；
4. branch 非 protected；
5. branch tip == merged PR final head，或有等价 release/helper provenance；
6. 没有新的用户保留要求。

v9.3 / v9.3.1 的 12 个候选满足 H0 删除候选标准；删除动作应在 H1 inventory 合并后单独执行并记录。

---

# 8. Stop Conditions

发现以下任一情况即停止自动清理：

- branch tip 在 inventory 后发生变化；
- branch 出现新的 open PR；
- no-PR branch 无法证明内容已被 main/release 吸收；
- docs 文件被 Runtime / test / fixture 明确按路径读取，而计划准备移动它；
- Index 分层需要改变 Manifest 覆盖范围；
- 清理需要修改 Runtime Authority 才能成立；
- 发现历史文件仍承担 active compatibility contract。

---

# 9. 当前状态

```text
H0 branch/docs inventory: MERGED（PR #189）
H1 Active Index segmentation: IN_PROGRESS
H2 safe branch deletion: NOT_STARTED
H3 docs move/delete: DEFERRED
```

本文件完成并通过 review 后，优先进入 H1；branch 删除不与 Index generator 修改混在同一 PR。
