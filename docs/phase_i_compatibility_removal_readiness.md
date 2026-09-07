---
status: readiness_audit
baseline_skill_version: 8.7.4
baseline_main_commit: f602b66dab952b20ef2c417ba36241959d2b2867
parent_plan: docs/semantic_state_runtime_refactor_plan.md
candidate_final_version: 9.0.0
change_class: docs_only_pre_phase_i
---

# Phase I — v9.0.0 Compatibility Removal Readiness Audit

> 本文件是 `docs/semantic_state_runtime_refactor_plan.md` 的实施状态与 Phase I 入口审计记录，不是新的 Runtime Authority。任何行为规则仍以 `core/bootstrap.yaml` 指向的 current Authority 为准。

## 1. 修改简报

**修改主题：** 在进入 Phase I 破坏性兼容删除前，重新核实当前 `main` 的阶段完成状态、删除门槛与剩余兼容路径。

**当前版本：** `8.7.4`

**最终目标版本：** `9.0.0`

**变更等级：** docs only / pre-major readiness audit

**直接目标：**

1. 将实施事实从旧聊天/旧阶段描述重新对齐到当前 `main@f602b66`；
2. 确认 Phase G、Phase H 已合并并完成 CI 闭环；
3. 对照原计划 Phase I 的六项进入条件，记录当前满足项、阻塞项与需要再次决策的兼容边界；
4. 为后续真正的 Phase I PR 提供单一、可审计的起点。

**明确不做：**

- 不删除任何 v8 compatibility field、alias、reader 或 fixture；
- 不修改 Project State Schema、Model Approval、Runtime Assurance、State Transition、Workbook 或 Output Contract；
- 不修改 `resolve_runtime.py`、`sync_project.py`、Python 主求解、结果深化分析或 MATLAB 正式绘图职责；
- 不修改 release carrier，不把当前仓库标记为正式 `9.0.0`；
- 不修改 `legacy/`；
- 不处理 Issue #92 Branch Protection 权限债务；
- 不手工编辑 generated metadata。

**权威事实源：**

- `core/bootstrap.yaml`
- `SKILL_CHANGE_GOVERNANCE.md`
- `core/project_state.schema.yaml`
- `core/model_approval_contract.yaml`
- `core/runtime_assurance_contract.yaml`
- `core/state_transition_contract.yaml`
- `config/competition_profiles.yaml`
- `docs/semantic_state_runtime_refactor_plan.md`（实施蓝图，非 Runtime Authority）

**验收：**

- 文档内容必须与当前 `main`、已合并 PR 与当前 active compatibility reader 一致；
- generated metadata 由 `scripts/generate_indexes.py`/仓库自动工作流刷新；
- PR 仍需标准 lint、unit、generated check 与 HSK Skill CI。

**回滚：** 本文件和对应 generated metadata 可整 PR revert，不产生项目状态迁移。

---

## 2. 当前阶段事实

当前 `main` 已经超过此前“Phase G 进行中 / Phase H 未开始”的旧进度描述。

| 阶段 | 目标 | 当前事实 |
|---|---|---|
| Phase A | Characterization / Regression Baseline | complete |
| Phase B | Runtime Assurance current-framework evidence | complete |
| Phase C | Semantic Identity + Approval / Runtime binding | complete |
| Phase D | State Transition Authority + typed stale propagation | complete |
| Phase E | Artifact Identity Naming Migration | complete |
| Phase F | Transactional Project Writes | complete |
| Phase G | Competition Writing Runtime De-Hardcode | complete |
| Phase H | `sync_project.py` mechanical split | complete |
| Phase I | v8 compatibility removal + v9 release | not started |
| v9.0.0 release | release carriers / migration / compatibility removal | not released |

### Phase G merge evidence

- PR #135: `refactor: configure competition writing runtime profiles`
- merged main commit: `b3ffe3954b26542177aa17984749b4806b3b3cb6`
- `config/competition_profiles.yaml#profiles.*.stable.writing_runtime` now owns competition writing-runtime selection;
- CUMCM remains Template-First progressive; MCM/ICM、Diangong、Certification Cup keep explicit full-reasoning fallback.

### Phase H merge evidence

- PR #136: `refactor: mechanically split sync project helpers`
- merged main commit: `f602b66dab952b20ef2c417ba36241959d2b2867`
- `scripts/artifact_fingerprint.py` and `scripts/project_snapshot.py` were mechanically extracted;
- `scripts/sync_project.py` remains orchestration and preserves compatibility aliases;
- no stale matrix, Schema, hash semantics, transaction semantics or Resolver behavior was changed by Phase H.

Phase H PR head completed the standard 11-job HSK Skill CI successfully, and the post-merge `main` HSK Skill CI plus generated-metadata verification also completed successfully.

---

## 3. Original Phase I entry gates

The parent plan requires all of the following before compatibility removal:

1. at least one stable version has written the new fields;
2. migration fixtures are green;
3. active repository code no longer writes the old fields targeted for deletion;
4. code search proves the old fields remain only in compatibility readers / tests / docs as intended;
5. the user explicitly confirms that v8 project write compatibility may end;
6. changelog and migration documentation are complete.

Phase I must not begin destructive deletion until every gate has an explicit disposition.

---

## 4. Readiness assessment on `main@f602b66`

| Gate | Status | Current evidence / blocker |
|---|---|---|
| 1. Stable compatibility-window release | **BLOCKED / decision required** | The staged Phase C–H work is merged into `main`, but the public Skill release carrier intentionally remains `8.7.4`. The original plan expected at least one stable version to write the new fields before major deletion. No post-migration v8.x release carrier has yet established that compatibility window. |
| 2. Migration fixtures green | **PARTIAL** | Phase C–H contain substantial migration/compatibility regression coverage, but there is not yet one Phase-I migration acceptance matrix proving all old-project classes against the exact deletion set. |
| 3. No active writers for old fields | **NOT YET TRUE for all candidates** | `artifact_hashes.model`, `model_hash`, `validated_model_hash` are already read-only compatibility paths, but legacy semantic projects still intentionally use `semantic_hash / validated_semantic_hash` read/write compatibility when no SIB exists. |
| 4. Old fields only in intended compatibility surfaces | **PARTIAL** | Artifact identity aliases are concentrated in compatibility helpers/readers; semantic legacy fields are still part of active no-SIB compatibility behavior and schema/lint/tests. A Phase-I exact reference inventory is still required before deletion. |
| 5. Explicit user approval to end v8 write compatibility | **PENDING** | No Phase-I deletion PR should interpret general continuation instructions as approval to end the compatibility window. This must be explicit at the destructive boundary. |
| 6. Changelog + migration docs complete | **NOT YET** | Staged Phase C–H changelog exists, but a final v8→v9 migration document covering project classes, automatic mappings, required renewed Human Approval, rollback, and compatibility-reader retirement is not yet complete. |

**Conclusion:** Phase I compatibility deletion is **not ready to execute** on the current baseline. The repository is ready for a Phase-I preparation step, not for immediate removal.

---

## 5. Current compatibility surfaces that must be classified before deletion

### 5.1 Artifact implementation identity

Candidates:

- `artifact_hashes.model`
- `model_hash`
- `validated_model_hash`

Current intent:

- canonical current implementation identity is `artifact_hashes.primary_code` / `artifact_hashes.analysis_code`;
- `artifact_hashes.model` is a legacy alias to primary code only;
- `model_hash / validated_model_hash` are legacy primary-code fallbacks;
- conflicting old/new values remain blocking until the legacy path is removed.

Before deletion, inventory every active reader and every fixture that intentionally characterizes old-project behavior.

### 5.2 Legacy semantic text-hash identity

Candidates:

- `semantic_hash`
- `validated_semantic_hash`
- `approved_semantic_hash`

Current intent:

- current model locking uses structured SIB identity (`semantic_identity_hash`, validated and approved structured identity hashes);
- legacy text hashes are historical/read-compatibility evidence and cannot authorize new primary code after SIB migration applies;
- however, no-SIB legacy projects still have active semantic-governance compatibility behavior, including legacy hash persistence.

Therefore these fields cannot be mechanically deleted together with the artifact aliases without first defining the old-project migration boundary.

### 5.3 Compatibility metadata ending at `<9.0.0`

Multiple active contracts intentionally declare `skill_compatibility: ...<9.0.0` or equivalent version boundaries. They are not all release carriers and must not be globally search/replaced.

For each occurrence classify it as one of:

1. schema/parser compatibility boundary that must be extended or intentionally broken;
2. historical introduction/compatibility metadata that remains accurate as history;
3. active governance applicability boundary that must be renewed for v9;
4. test assertion that should change only with its owning contract.

`SKILL_CHANGE_GOVERNANCE.md` itself currently applies to `<9.0.0`, so the governance contract requires an explicit v9 transition rather than silent reuse beyond its declared range.

---

## 6. Required pre-Phase-I decisions

Before the destructive Phase I implementation PR, resolve these decisions explicitly:

### D1. Compatibility-window interpretation

The original plan requires at least one stable version that writes the new fields. Current staged implementation kept the release carrier at `8.7.4` throughout C–H.

Choose one audited policy before deletion:

- **Option A — publish a final v8.x compatibility checkpoint** before Phase I, preserving the original gate literally; or
- **Option B — formally amend the parent plan** with an equivalent compatibility-window justification based on merged main + migration fixtures + explicit user acceptance.

Do not silently treat staged unreleased `main` as satisfying a gate that explicitly says “stable version”.

### D2. Legacy project classes after v9

Define exact v9 behavior for:

- L0 historical read-only project;
- L1 old project that only resumes paper writing;
- L2 old project re-entering model design / preprocessing / primary solve.

The existing parent plan already distinguishes these classes; Phase I must convert that distinction into deterministic migration acceptance tests.

### D3. Semantic legacy write retirement

Decide whether v9:

- rejects no-SIB state at write-time and requires SIB migration before any state mutation; or
- keeps a narrow read-only legacy adapter while prohibiting all legacy semantic hash writes.

Migration code must never synthesize Human Approval.

---

## 7. Recommended next PR sequence

Do not combine all Phase I changes into one giant deletion PR. Recommended sequence:

```text
I0  readiness / exact reference inventory / migration acceptance matrix
    ↓
I1  v9 migration contract + migration CLI/dry-run if proven necessary
    ↓
I2  stop remaining legacy semantic writes; keep read adapter
    ↓
I3  remove artifact legacy aliases and obsolete state fields
    ↓
I4  renew v9 compatibility metadata / governance / release carriers
    ↓
I5  final v9.0.0 release validation + migration documentation
```

This is a proposed implementation decomposition only. If the parent plan is amended, keep one Authority per rule and preserve one-PR-one-theme governance.

---

## 8. Phase-I I0 acceptance checklist

Before any compatibility deletion PR:

- [ ] fresh `main` SHA recorded;
- [ ] no overlapping open PR;
- [ ] exact active reader/writer inventory for every deletion candidate;
- [ ] old-project L0/L1/L2 fixtures identified;
- [ ] migration acceptance matrix added;
- [ ] governance applicability for v9 explicitly decided;
- [ ] stable compatibility-window policy decided;
- [ ] explicit user approval to end v8 write compatibility recorded;
- [ ] rollback to last v8-compatible tree documented;
- [ ] no runtime Authority altered by the readiness-only PR.

---

## 9. Readiness verdict

Current implementation status is:

```text
Phase A–H: complete and merged
Phase I: not started
v9.0.0: not released
```

The next safe engineering action is **Phase I I0 — exact compatibility inventory + migration acceptance baseline**. Destructive compatibility removal must wait until the blockers in §4 and decisions in §6 are closed.
