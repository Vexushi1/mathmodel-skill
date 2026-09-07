---
status: phase_i_i0_baseline
baseline_skill_version: 8.7.4
baseline_main_commit: 9530b0d47946ffe2ae85d814ba398527d65c1c5f
parent_plan: docs/semantic_state_runtime_refactor_plan.md
readiness_record: docs/phase_i_compatibility_removal_readiness.md
candidate_final_version: 9.0.0
runtime_authority: false
---

# Phase I I0 — Compatibility Surface Inventory

> 本文件是 Phase I 的实施审计记录，不是新的 Runtime Authority。字段结构、Model Approval、Runtime Assurance、stale propagation 等行为仍分别服从当前 `core/` Authority 与实现。真正实施任何删除前，必须重新读取当前 `main` 的 `docs/semantic_state_runtime_refactor_plan.md`。

## 1. 本阶段边界

I0 只做两件事：

1. 把 Phase I 候选兼容面按 **writer / runtime reader / Schema or Authority surface / docs-tests evidence** 分类；
2. 建立旧项目 migration acceptance matrix，固定破坏性删除前的真实兼容行为。

本阶段明确不做：

- 不删除任何旧字段、alias、reader、Schema property 或 fixture；
- 不停止任何现有 legacy write path；
- 不修改 `core/**`、`scripts/**`、`modules/**`、模板或 `legacy/`；
- 不修改 Python 主求解、结果深化分析、MATLAB 正式绘图职责；
- 不修改 workbook 数值事实原则；
- 不升级 Skill release carrier；
- 不把本轮“继续修改”解释为结束 v8 project write compatibility 的授权。

## 2. 原计划 Phase I 删除边界

`docs/semantic_state_runtime_refactor_plan.md` 当前只把以下内容列为候选删除/退役方向：

- `artifact_hashes.model` 新写支持；
- legacy `semantic_hash` 作为 approval identity 的含义；
- 经引用盘点确认无独立意义的 `model_hash / validated_model_hash`；
- 过期 stale alias。

因此 I0 不把所有名字中含 `legacy` 的 surface 自动归入删除集，也不对 `semantic_hash / validated_semantic_hash / approved_semantic_hash` 做机械整组删除。每个字段必须先按实际职责分类。

## 3. 精确兼容面清单

### 3.1 Implementation identity / stale layer

| Surface | 当前语义 | Active writer | Runtime reader / normalizer | Schema / Authority surface | I0 结论 |
|---|---|---|---|---|---|
| `artifact_hashes.model` | v8 primary Python implementation hash alias，不是数学模型身份 | **无**；Phase E 后新写使用 `primary_code` | `scripts/artifact_identity.py` 直接做 alias normalization；`runtime_assurance.py`、`sync_project.py`、`validate_project_state.py` 通过共享 normalizer/兼容入口消费 | `core/project_state.schema.yaml#$defs.artifact_hashes.model` 仍允许旧状态；`core/state_transition_contract.yaml` 保留 legacy model layer 读兼容 | writer gate 已满足；reader / Schema removal 尚未执行 |
| `model_hash` | legacy primary-code fallback | **无 active writer** | `artifact_identity.py`、`runtime_assurance.py`、`sync_project.py`、`validate_project_state.py` 作为 canonical hash 缺失时 fallback | `core/project_state.schema.yaml` 仍声明字段 | 具备 Phase I 退役资格，但必须与 migration fixture / historical-read policy 同步删除 |
| `validated_model_hash` | legacy validated primary-code fallback | **无 active writer** | 同上，用于 validated artifact fallback | `core/project_state.schema.yaml` 仍声明字段 | 同 `model_hash` |
| stale layer `model` | v8 implementation stale-layer alias，映射到 `primary_code` | **无新写支持** | shared State Transition compatibility path | `core/project_state.schema.yaml#$defs.artifact_layer` 仍含 `model`；`core/state_transition_contract.yaml` 明确 `legacy_model_artifact_layer_read_supported: true`、write=false | 这是原计划“过期 stale alias”的明确候选之一；I0 只记录，不删除 |

补充：`robustness_workbook` 等其他历史兼容名不属于本次 Phase I 计划已明确的 identity/stale 候选，禁止顺手清理。

### 3.2 Semantic identity / approval provenance

| Surface | 当前语义 | Active writer | Runtime reader | Schema / Authority surface | I0 结论 |
|---|---|---|---|---|---|
| `semantic_hash` | 无 SIB legacy 项目的 Markdown semantic-scope text hash；不能作为新主代码的 current structured identity | **仍有**：`validate_semantic_governance.py` 的 `legacy_text_hash` 分支保持 v8 write path | `validate_model_approval.py` legacy read-only mode；`runtime_assurance.py` legacy evidence；semantic governance 自身 | `core/project_state.schema.yaml` 仍声明；Model Approval / Runtime Assurance contracts 明确其为 historical/read-only approval provenance | Phase I gate 3 **尚未满足**；先停止 legacy write，再讨论 reader/field retirement |
| `validated_semantic_hash` | legacy text-hash validation baseline | **仍有**：legacy semantic governance write path | `validate_semantic_governance.py` | `core/project_state.schema.yaml` 仍声明；lint/tests 仍约束该 legacy path | 不是“approval identity”本身，但属于尚未停止的 legacy write surface；不得和 `model_hash` 同批机械删除 |
| `approved_semantic_hash` | legacy Human Approval provenance | **无新写/刷新**；Phase C 后 migration/validation 不得合成人工批准 | `validate_model_approval.py` 和 `runtime_assurance.py` 在 structured identity 完全不存在时只读 | `core/project_state.schema.yaml`、Model Approval / Runtime Assurance contracts | 原计划要求退役其 approval-authority 含义；是否保留窄历史 reader 由最终 v9 migration contract 决定 |
| `semantic_identity_hash` / validated / approved structured identity | 当前数学语义 identity | current write path | Model Approval、Runtime Assurance、semantic governance | current Authority | **不是删除对象** |

关键边界：structured identity 存在任一部分时禁止回退 legacy approval；partial structured state 必须 fail closed。旧 prose 不能被机器自动推断成已验证、已人工批准的 SIB。

## 4. 当前直接证据

I0 以当前主干行为为准，已有回归提供以下证据：

- `tests/test_v900_artifact_identity.py`：legacy `model` / `model_hash` 只读映射、冲突 blocking、canonical new writes；
- `tests/test_v900_semantic_governance.py::test_legacy_framework_keeps_v8_hash_write_path`：无 SIB 项目仍会写 `semantic_hash / validated_semantic_hash`；
- `tests/test_v900_semantic_identity_binding.py`：legacy approval 可做 read-only review，但 pre-code gate 要求 SIB migration；structured current identity 可 verified；
- `tests/test_v712_runtime_assurance.py`：legacy project 进入 `full_solution` 时 `locked_model_spec` 为 `legacy_review_required`，resolver 回到 Model Approval，而不是进入主求解。

本 PR 新增 `tests/test_v900_phase_i_migration_matrix.py`，把这些分散事实组合成 Phase I 的统一 migration acceptance baseline。

## 5. 旧项目 migration acceptance matrix

### L0 — Historical read-only legacy project

输入特征：

- 无 SIB；
- legacy semantic hash / approval provenance 完整；
- 仅需要历史读取/审计。

当前必须保持：

- legacy evidence 可以被读取；
- `locked_model_spec` **不得**提升为 `verified`；
- Runtime Assurance 返回 `legacy_review_required`；
- Model Approval validator 仅在显式 `allow_legacy_read_only` 场景允许历史审计。

### L1 — Legacy project re-entering model/code workflow

输入特征：同 L0，但请求重新进入 `model_design / data_preprocessing / solve_validate` 或生成新主代码。

当前必须保持：

- legacy approval 不能授权新代码；
- resolver 回到 `modules/02_model_design.md`；
- `pause_state = awaiting_model_approval`；
- 在 current SIB 建立、semantic governance 验证、Model Challenge 与显式 Human Approval 完成前，不进入 `modules/03_solve_validate.md`。

### L2 — Current structured project

输入特征：

- Framework 中有完整可解析 SIB；
- `semantic_identity_hash == validated_semantic_identity_hash == approved_semantic_identity_hash`；
- current revision / challenge / Human Approval 一致。

当前必须保持：

- Runtime Assurance 重新读取 Framework SIB 并得到 `verified`；
- `locked_model_spec` 可进入 verified artifacts；
- Model Approval validator 对 current structured identity 通过。

## 6. Phase I gate 状态（I0 基线）

| Gate | I0 状态 | 原因 |
|---|---|---|
| 至少一个稳定版本已写新字段 | **pending decision** | staged C–H 已进 main，但 release carrier 仍为 8.7.4；不能擅自把 unreleased staged main 等同于计划所说的 stable compatibility window |
| migration fixtures 全绿 | **building baseline** | I0 新增统一 matrix；后续 destructive PR 必须在此基础上继续绿 |
| 活动代码不再写旧字段 | **false** | artifact legacy writes 已停；legacy semantic no-SIB write path 仍存在 |
| code search 只剩 compatibility reader/docs | **partial** | artifact identity 接近该状态；semantic legacy 仍有 writer、Schema、lint 与 runtime reader |
| 用户确认结束 v8 project write compatibility | **pending** | 本轮只授权继续 I0，不视为 destructive-boundary approval |
| Changelog + migration doc 完整 | **false** | 最终 v8→v9 migration document 尚未形成 |

## 7. I0 退出条件

I0 可以合并的条件：

- compatibility inventory 与当前 `main` 实现一致；
- migration matrix fixture 能稳定表达 L0/L1/L2；
- I0 tests、全量 unit、lint、generated check 全绿；
- 不出现任何 Runtime Authority 或行为 diff；
- PR 仍保持 8.7.4 release carrier。

### Generated metadata branch contract

I0 以及后续 Phase I 实现分支必须使用仓库 `refresh-generated.yml` 已监听的分支前缀（例如 `refactor/**`、`fix/**`、`upgrade/**`），或者通过等价的受支持流程触发 generator。`SKILL_FILE_INDEX.md`、`TEMPLATE_INDEX.md`、`HSK_*INDEX*` 与 `MANIFEST.sha256` 只能由 `scripts/generate_indexes.py` / 仓库自动工作流维护，禁止为了让 CI 通过而手工修改哈希或索引内容。

I0 合并后仍**不允许**直接执行 destructive compatibility removal。下一步必须重新从最新 `main` 读取原计划，再决定 stable compatibility-window policy 与后续 I1/I2 的单主题边界。
