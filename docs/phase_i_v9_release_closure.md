---
status: phase_i_i5_release_closure
phase: I5
skill_version: 9.0.0
baseline_main_commit: f6b506212cf466add0e55f175527651a18ae9fe2
parent_plan: docs/semantic_state_runtime_refactor_plan.md
migration_contract: docs/v900_migration_contract.md
runtime_authority: false
phase_i_complete: true
github_release_or_tag_created: false
---

# Phase I I5 — v9.0.0 Release Closure

本记录闭合 `8.7.4 → 9.0.0` staged refactor 的 Phase I。它只记录最终 migration/release documentation 与 release-validation gate，不建立新的 Runtime Authority，也不改变 Project State、State Transition、Resolver、transaction、Model Approval、Runtime Assurance、数值验证或写作运行时语义。

## 六个 Phase I gate 的最终 disposition

| Gate | I5 disposition | Evidence |
|---|---|---|
| stable v8.x compatibility window | satisfied | `8.9.0` stable checkpoint |
| migration fixtures green | satisfied | I0/I1 L0/L1/L2 matrix + full staged CI |
| active code stops targeted old writes | satisfied | I2 legacy semantic writer retirement |
| targeted old fields only historical reader/docs | satisfied | I3a/I3b active alias retirement + current Schema/Transition boundary |
| explicit user authorization to end v8 writes | satisfied | I2 implementation record |
| Changelog + migration documentation complete | satisfied by I5 | final migration contract, current Changelog, this closure record |

## 最终兼容边界

- L0 historical project：保留窄的 read-only semantic provenance reader；不能授权新代码。
- L1 legacy re-entry：必须建立 current SIB、通过 semantic validation / Model Challenge，并获得 current structured identity 的 explicit Human Approval。
- L2 structured current：证据仍 current 时不因版本号本身自动 stale；Runtime Assurance 继续现场重算 identity。
- historical implementation aliases：只允许 `scripts/artifact_identity.py` 在 pre-schema audit/migration 中机械识别；active Project State 已不接受这些字段。
- semantic historical reader 的进一步删除：明确延后到 v9.0.0 之后的独立兼容性决策。

## I4b 合并与 main 验证证据

I4b PR `#147` final head `f042d1c6fc1c119b3ea2251281fbc283bd692082` 在合并前通过标准 11-job HSK Skill CI，并以 expected-head squash merge 到 `main@f6b506212cf466add0e55f175527651a18ae9fe2`。

合并后：

- HSK Skill CI run `34100869380`：11/11 success；
- Refresh generated repository metadata run `34100869385`：success；
- 活动 release carriers 为 `9.0.0`。

## I5 自身 release validation gate

I5 PR merge 前仍必须满足 lint、完整 unit suite、generated check、standard 11-job HSK Skill CI、无 unresolved review threads，并保证 exact PR head 未移动。I5 merge 后还必须检查 `main` HSK Skill CI 与 generated verification；两者成功后 Phase I 才最终闭环。

## GitHub Release / tag

当前仓库治理未规定必须创建 GitHub Release 或 tag；仓库当前也没有 GitHub Releases 对象。因此 I5 不创建 GitHub tag / GitHub Release，不把外部 release object 当作隐含 gate。

## 回滚

- I5 本身是 docs/tests closure，可整 PR revert；
- 代码级 v9 rollback 按对应 I2/I3/I4 PR 边界 revert，不做盲目全仓版本替换；
- 最后稳定 v8.x checkpoint 为 `8.9.0`；
- 若真实 project state 已在 v9 下显式迁移，必须使用迁移前 snapshot/backup，不能只降级 Skill 代码后假设旧 state 自动恢复兼容。

## Phase I 之后

v9.0.0 已完成本计划内的 compatibility-removal 与 release closure。后续若删除 L0 historical readers、扩大 Schema 破坏边界或修改 migration adapter，必须作为新的独立治理变更处理，不得追溯性改写本次 Phase I 证据。
