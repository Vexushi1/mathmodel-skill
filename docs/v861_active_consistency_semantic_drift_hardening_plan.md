# v8.6.1 Active Consistency & Semantic Drift Hardening Plan

> 状态：实现与版本同步完成 / final release CI pending  
> 基线：`main@41373e1a0ce3472df2c5afc15a3f4c0b9db379fa`（v8.6.0）  
> 计划分支：`fix/v8.6.1-active-consistency-semantic-drift`  
> 当前文件只作为后续实施上下文与 Scope Contract；除本计划文档外，本轮尚未修改任何 active runtime / Authority / template / test。  
> 目标版本：若用户批准实施，预计发布为 **v8.6.1 patch**；在正式实施前仍保持仓库 release carriers 为 v8.6.0。

---

## 1. 背景与本轮目标

v8.6.0 已完成 Model Construction & Solution Rationale、Local Applicability、Solver Preconditions、Reduction Provenance、Numerical Parameter Rationale、Section Title Minimality 与 Adaptive Subsection Separation，并已合并进入 `main`。本轮不是继续增加建模或写作能力，而是针对 v8.6.0 合并后通读发现的**活动文档状态漂移、模板示例锚定、集成指针不对称、发布历史格式不统一与 declarative surface 可误读性**做一次收口。

本轮核心原则：

```text
不新增模型能力
不重写 v8.6 数学/写作语义
不扩大 Authority 数量
不改变用户执行边界
不改变 Workbook / Project State / Numerical Verification
不改目录与五文件合同
不把历史记录“洗白”为从未失败
只修 current 表述与 current 运行链之间的事实一致性、接口可读性和防漂移保护
```

目标是让后续维护者或模型在读取当前仓库时得到统一结论：

```text
current release state
= current main / current CI / current release carriers

current writing semantics
= Authority 中的 adaptive rules
≠ canonical example 的表面形状

raw declarative route
≠ unresolved final plan
resolved runtime plan
= 实际执行边界事实源
```

---

## 2. 修改简报（按 SKILL_CHANGE_GOVERNANCE）

```text
修改主题：v8.6.1 Active Consistency & Semantic Drift Hardening
当前版本：8.6.0
目标版本：8.6.1（批准实施后）
变更等级：patch

直接目标：
1. 修复 v8.6 evaluation 与当前 merged/released/CI-green 状态不一致；
2. 明确旧 evaluation 文档是历史验收快照，避免被误读为 current release state；
3. 降低 CUMCM canonical example / fixed smoke 对 Adaptive Subsection 的错误锚定；
4. 补齐 v8.6 writing capabilities 在 integration pointer 层的可追溯性；
5. 统一 CHANGELOG release heading 的可机读格式；
6. 增加 A196 provenance 与 current semantic policy 的隔离保护；
7. 明确 raw route declaration 与 resolver-resolved terminal outputs 的边界，并增加回归测试。

明确不做：
- 不新增或替换数学模型、solver、validator；
- 不改变 Model Approval / Human Approval 行为；
- 不改变 preprocessing_decision 三态；
- 不改变 03A / 03B、Primary Quality Specification 或数值阈值；
- 不改变 Workbook Schema、Project State Schema、目录、五文件合同；
- 不修改 MATLAB 读取职责、Figure Evidence 或 draw.io 机制图语义；
- 不重写 Paper Writing Protocol 的主体能力；
- 不建立新的 prose Authority；
- 不删除 A196/reference provenance；
- 不在 patch 中重命名 router 的公共字段、CLI 或大规模 schema；
- 不通过 Skill 代码模拟 GitHub branch protection。

权威事实源：
- core/bootstrap.yaml
- SKILL_CHANGE_GOVERNANCE.md
- core/workflow_router.yaml
- scripts/resolve_runtime.py / scripts/resolve_workflow.py
- core/output_contract.yaml
- core/writing_reasoning_contract.yaml
- core/writing_runtime_contract.yaml
- modules/05_writing/paper_writing_protocol.md
- modules/05_writing/ai_cleanup.md
- modules/06_review_delivery.md
- templates/latex/cumcm/hsk/template_manifest.yaml
- README.md / CHANGELOG.md / current evaluation docs

预计修改文件：
- docs/v860_model_construction_solution_rationale_evaluation.md
- docs/v850_author_reasoning_voice_evaluation.md（仅历史状态标识/闭环说明，保留原证据）
- docs/v840_author_reasoning_evaluation.md（若需要，同样只补历史状态语义）
- templates/latex/cumcm/hsk/template_manifest.yaml
- templates/latex/cumcm/hsk/README.md
- core/output_contract.yaml
- RUNTIME_ROUTER.md（仅解释 raw declaration / resolved plan 边界）
- CHANGELOG.md
- tests/test_v861_active_consistency_semantic_drift.py（新增）
- 必要时小幅扩展现有 health / v8.6 tests
- release carriers（仅在实施完成并准备发布时同步到 8.6.1）
- generated indexes / MANIFEST（只能由生成流程更新）

禁止触碰文件：
- core/model_approval_contract.yaml
- core/numerical_verification_contract.yaml
- core/workbook_schema.yaml
- core/project_state.schema.yaml
- core/user_execution_contract.yaml
- core/global_preprocessing_contract.yaml
- modules/03_solve_validate.md
- modules/03_result_analysis.md
- modules/04_figure_evidence.md
- MATLAB templates / mechanism generator logic
- legacy/ 中历史材料

兼容性要求：
- v8.6.0 项目、route、CLI、模板工程继续可读；
- 不移除现有 manifest 字段；
- 不改变现有 resolver 的有效行为；
- 仅增加解释性元信息或回归保护时必须保持旧 consumer 可忽略；
- 若发现必须改公共字段名，停止本 patch，另立 minor/major 方案。

迁移要求：
- 预计无项目迁移；
- 旧论文、旧 framework、旧 project_state 不重写；
- 旧 evaluation 保留原始历史数据，只补 current/historical status 说明。

验收测试：
- python scripts/lint_skill.py
- python -m unittest discover -s tests
- python scripts/generate_indexes.py --check
- 代表性 resolver approval-boundary 回归
- v8.6 writing semantics 回归
- CUMCM / MCM-ICM / Diangong LaTeX CI
- Production LaTeX attestation
- Generated File Contract

回滚方式：
- 本轮为单一 patch PR；若新增测试证明某项“整理”改变了 runtime 行为，则撤回该项而不是放宽测试；
- 若 template / router 需要接口级重命名，回退到文档澄清 + 回归保护，并把接口重构拆到后续版本。
```

---

## 3. 风险清单与处理优先级

| ID | 风险 | 当前判断 | 本轮策略 |
|---|---|---|---|
| F1 | v8.6 evaluation 仍写 PR Draft / release pending / CI 未全绿 | 明确 current-state drift | 必修 |
| F2 | v8.4/v8.5 evaluation 仍呈现发布前状态但位于 active docs | 历史状态语义不清 | 必修，但只加历史状态说明，不改旧事实 |
| F3 | Template fixed example 仍呈现四标题，可能锚定 Adaptive Subsection | 非运行时 bug，但有 future drift 风险 | 必修防误读，不强改示例形状 |
| F4 | output_contract 对 v8.6 新 reasoning capability 的 named pointer 不完全对称 | 可维护性风险 | 必修轻量 pointer 收口 |
| F5 | CHANGELOG 8.6/8.5/8.4 release heading 格式不一致 | 可机读历史不整齐 | 必修 |
| F6 | `a196_inspired*` 仍出现在 active template provenance/profile | 当前合法 provenance，但有长期锚定风险 | 本轮只做隔离与测试，不做破坏性重命名 |
| F7 | raw route / module output 声明可能被误读为已经产生 locked model | declarative surface ambiguity | 本轮只澄清与测试，不改 resolver 行为/公共字段 |
| G1 | main branch protection 未在平台强制 | repository governance debt | 明确排除，不用 Skill 代码模拟 |

优先级：

```text
P0: F1
P1: F3 + F4 + F7
P2: F2 + F5 + F6
Out of scope: G1 platform enforcement
```

---

## 4. Phase A：关闭 v8.6 release-state 漂移（F1）

### 4.1 问题

`docs/v860_model_construction_solution_rationale_evaluation.md` 当前保存的是候选分支阶段观察，其中包括：

- 发布基线仍写 v8.5.0；
- PR #110 标记为 Draft；
- CI 观察停留在 release-carrier synchronization 尚未完成；
- `release_status = pending`；
- `merge_status = forbidden_until_final_green_ci`。

这些内容作为“当时发生过什么”的历史证据是有效的，但该文档又被 README 作为 v8.6 当前评估记录直接链接，导致 current reader 容易把 pre-merge 状态当作 current release state。

### 4.2 修改原则

**不删除失败历史，不重写成“从一开始就通过”。**

计划把文档分成两个层次：

```text
A. Final Release Status（current factual closure）
B. Candidate-stage Evaluation History（保留原始观察）
```

Final Release Status 至少记录：

- release version = 8.6.0；
- merged PR = #110；
- merge commit = `41373e1a0ce3472df2c5afc15a3f4c0b9db379fa`；
- final release carriers = synchronized；
- final required CI = green（引用最终验证 run/commit，而不是旧候选 run）；
- current verdict = released / merged；
- candidate-stage failures remain historical observations。

原“当前未完成项”改为明确的 historical checklist，保留其在候选 head 上曾经成立的事实，但不得继续使用“当前”“尚不能发布”等没有时间限定的措辞。

### 4.3 验收

新增确定性测试：

- current release evaluation 不得同时出现 current `release_status=pending`；
- current release evaluation 必须包含 current bootstrap version；
- 若 README 将某 evaluation 标为 current version evaluation，则该文档必须有 final-release-status block；
- historical CI 失败可保留，但必须明确标记 candidate/historical scope。

禁止测试通过方式：

- 不简单删除所有 `pending` 单词；
- 不删旧 CI 记录；
- 不把旧 failed job 改写成 passed。

---

## 5. Phase B：统一 evaluation 文档的“历史快照 / 当前状态”语义（F2）

### 5.1 目标

让 active `docs/v840_*evaluation.md`、`docs/v850_*evaluation.md`、`docs/v860_*evaluation.md` 在角色上可区分：

```text
implementation evaluation snapshot
release closure status
current authority? -> no
```

所有 evaluation 必须继续声明：

- 它们不是运行时 Authority；
- 它们不能覆盖 current contract；
- 历史 checklist/失败状态只描述当时 head。

### 5.2 建议结构

对 v8.4 / v8.5 不做大段重写，只在文件开头增加简短 metadata/status 区：

```text
Document role: historical implementation/evaluation record
Evaluated release: v8.x.x
Snapshot status at time of writing: ...
Current repository status: superseded by later release / released
Runtime authority: none
```

v8.5 原有未勾选 checklist 保留，但明确：

> checklist 是当时的 release-decision checklist，不代表当前 main 仍未发布 v8.5。

### 5.3 是否迁入 legacy

本 patch **不迁移**这些 docs 到 `legacy/`，原因：

- README / active release history 仍需引用；
- 文件对当前 capability provenance 有审计价值；
- 迁移路径会制造链接和 MANIFEST 噪声。

若未来要统一 archive policy，应单独开 docs/refactor PR。

---

## 6. Phase C：降低 canonical template 对四标题结构的错误锚定（F3）

### 6.1 当前矛盾不是运行时冲突，而是“示例形状 → 默认语义”的潜在误读

当前 Authority 已明确：

```text
MODEL / SOLVE / RESULT / VALIDATE = functional roles
不是 mandatory literal headings
```

同时：

- 简单解析题可合并；
- 复杂题可按真实独立数学任务拆分；
- 标题数量和长度都不是质量指标。

但 canonical Q1 与 `fixed_template_checks.required_question_tokens` 仍固定出现：

```text
模型建立
模型求解
求解结果
结果的分析与验证
```

本轮不把这些示例删掉，因为它们仍可作为“复杂题示例”和 LaTeX smoke fixture。要修的是其**语义地位**。

### 6.2 计划修改

在 `template_manifest.yaml` 中增加或强化以下边界（优先使用兼容新增字段，不重命名已有公共字段）：

```text
fixed_template_checks.role = maintained_example_smoke_only
fixed_template_checks.runtime_semantic_authority = false
fixed_template_checks.literal_subsection_tokens_apply_to = maintained_example_file_only
fixed_template_checks.must_not_infer = runtime_required_headings
```

若现有 schema/consumer 不适合新增结构字段，则改为同等明确的注释/说明字段，但必须配测试。

`default_complex_question_headings` 本轮不直接重命名，避免 patch 级接口变更；可增加 sibling 语义说明：

```text
these headings describe maintained example profile only;
runtime internal structure remains adaptive.
```

同时更新 template README：

- canonical example 是能力展示，不是正文标题模板；
- runtime subsection decisions 服从 Writing Reasoning + Paper Writing Protocol；
- 简单题保留 merged profile；
- 复杂题若出现独立证明、结构化简、参数证据、solver stage，可拆成更多或不同标题。

### 6.3 新增回归

至少固定以下两个负/正案例：

1. **Simple analytic case**：没有 solver、没有验证必要性时，不应因为 template example 存在四标题而强制生成四标题。
2. **Complex multi-stage case**：真实有独立 reduction / parameter evidence / solver stage 时，可以出现多于四个或完全不同的短标题，不得被 fixed example 判失败。

机器测试只检查 contract 边界和声明，不用标题数量判断 prose 质量。

---

## 7. Phase D：补齐 output_contract 的 v8.6 integration pointers（F4）

### 7.1 原则

`core/writing_reasoning_contract.yaml` 继续是唯一 reasoning Authority。`core/output_contract.yaml` 只做 integration pointer，不复制规则正文。

本轮补 pointer 的目的：让维护者从 writing_policy 一眼追踪 v8.6 capability，而不是误以为只有旧 named pointers 是正式能力。

### 7.2 确定可以增加的 pointer

实施前以 current Authority key 实际存在为准，优先加入：

```yaml
model_construction_rationale_contract: core/writing_reasoning_contract.yaml#model_construction_rationale
numerical_parameter_evidence_contract: core/writing_reasoning_contract.yaml#numerical_parameter_evidence
```

对 Section Title Minimality / Adaptive Subsection Separation，不先假定新的 root key；先检查它们在 current contract 中的实际 owner：

- 若仍属于 `model_establishment_solution_narrative` 内部结构，则 pointer 指向实际 nested owner 或保留现有 narrative/subsection pointer；
- 不为了“看起来对称”复制一份新 Authority key。

### 7.3 保护测试

- output_contract pointer 必须指向真实 active Authority；
- consumer 不得复制同一规则正文；
- pointer 缺失只作为 architecture consistency test，不升级成论文 runtime Hard gate。

---

## 8. Phase E：统一 CHANGELOG release heading（F5）

### 8.1 问题

当前存在：

```text
## Current release: 8.6.0
## 8.5.0
## 8.4.0
## Previous release: 8.3.0
```

而现有版本测试只匹配 `Current|Previous release:`，因此 8.5 / 8.4 会被 release-history parser 跳过。

### 8.2 计划

统一成：

```text
## Current release: 8.6.1   # 实施完成后
## Previous release: 8.6.0
## Previous release: 8.5.0
## Previous release: 8.4.0
...
```

注意：

- 只有真正发布 8.6.1 时才移动 current heading；
- 计划阶段不改版本；
- 历史 release 内容不重写。

### 8.3 测试

升级现有 release-carrier test：

- 所有正式 release section 都必须满足统一 heading pattern；
- 第一项必须等于 bootstrap current version；
- 后续版本不得等于 current；
- 版本序列无重复；
- 不要求通过字符串排序推断语义版本顺序，可显式解析 semver。

---

## 9. Phase F：A196 provenance 去锚定保护（F6）

### 9.1 当前判断

`a196_framework_notes.md`、`framework_profile: a196_inspired_question_local_closure`、`architecture_reference: a196_inspired` 当前仍属于合法 provenance：只用于章节拓扑与来源追溯，并没有把 A196 的算法、公式、标题或句式作为 runtime Authority。

因此本 patch **不删除、不重命名这些 provenance 文件和已有字段**。

### 9.2 本轮真正要做的事

增加明确隔离：

```text
A196 = provenance/reference evidence
A196 != writing semantic authority
A196 != runtime subsection requirement
A196 != solver/model recommendation source
```

检查范围：

- `template_manifest.yaml`
- template README
- current writing Authority / Runtime / Cleanup / Review
- tests / indexes

新增测试：

- `A196` / `a196_inspired` 可以存在于 template provenance/reference/docs；
- 不允许新出现在 `core/writing_reasoning_contract.yaml` 的算法/标题硬规则中；
- 不允许 router 因 A196 profile 选择 solver、验证方法或固定 subsection；
- fixed example 可引用 provenance，但 runtime decision 必须继续由 Authority 决定。

### 9.3 后续可选重构（不属于 v8.6.1）

若未来确实要把 profile 名从 `a196_inspired_*` 中性化，应另开 refactor/minor PR，保留旧 alias 和迁移窗口；本 patch 不做字段重命名。

---

## 10. Phase G：raw route declaration 与 resolved runtime plan 的边界澄清（F7）

### 10.1 当前事实

raw `workflow_router.yaml` / `module_manifest.yaml` 可以声明某 route/module 的潜在 outputs，其中包括 `locked_model_spec`；但实际 resolver 在 Model Approval 未满足时会通过 boundary segment 截断，并返回 `awaiting_model_approval`。

机器行为目前是正确的，风险在于维护者只读 raw YAML 时可能误解为“model_design 一运行就已经锁模”。

### 10.2 本轮策略

不改 resolver 行为，不重命名公共字段。

在 `RUNTIME_ROUTER.md` 增加一个短而明确的“declarative candidate vs effective resolved plan”说明：

```text
routing.<route>.terminal_outputs / module outputs
= route capability / candidate surface before boundary resolution

scripts/resolve_runtime.py returned terminal_outputs
= effective outputs for this invocation after approval/preprocessing/user-execution boundaries
```

并明确：

- 未审批时 resolved output 不得把 `locked_model_spec` 作为 current terminal artifact；
- raw manifest 不授权执行；
- formal consumers 必须使用 resolver 返回的有效计划。

### 10.3 回归测试

新增至少三组确定性案例：

1. 无 Human Approval 的 `full_solution`：必须停 `awaiting_model_approval`，不得暴露 current locked-model execution path。
2. locked model + `project_level` preprocessing 未 accepted：必须停 `awaiting_user_preprocessing`。
3. locked model + preprocessing satisfied、primary workbook 未 accepted：交付主求解代码并停 `awaiting_user_execution`。

这些测试只验证现有行为，若失败说明是真 runtime regression；不得为配合文档去修改 expected behavior。

---

## 11. G1：Branch Protection 作为平台治理债务处理

当前 `main` 的平台保护状态不属于 Skill runtime 语义。

本轮明确：

- 不修改 Core Policy、router 或 CI 去“模拟” GitHub Settings；
- 不新增伪 protection gate；
- `SKILL_CHANGE_GOVERNANCE.md` 中 direct-main-write 禁令继续保留；
- 若需要真正强制 branch protection，应在 GitHub repository settings / ruleset 层单独处理。

本计划只记录该债务，不在 v8.6.1 代码 PR 中混入平台权限治理。

---

## 12. 预计文件级修改矩阵

| 文件 | 计划动作 | 是否改变 runtime 行为 |
|---|---|---:|
| `docs/v860_model_construction_solution_rationale_evaluation.md` | 增加 final release closure，历史候选观察降格为 snapshot | 否 |
| `docs/v850_author_reasoning_voice_evaluation.md` | 增加 historical status metadata | 否 |
| `docs/v840_author_reasoning_evaluation.md` | 必要时同上 | 否 |
| `templates/latex/cumcm/hsk/template_manifest.yaml` | 明确 fixed example/smoke 非 runtime subsection authority | 原则上否 |
| `templates/latex/cumcm/hsk/README.md` | 解释 adaptive subsection 与 example 的关系 | 否 |
| `core/output_contract.yaml` | 补 v8.6 reasoning integration pointers | 否 |
| `RUNTIME_ROUTER.md` | 澄清 raw declaration / effective plan | 否 |
| `CHANGELOG.md` | 统一 release heading；实施完成后记录 8.6.1 | 否 |
| `tests/test_v861_active_consistency_semantic_drift.py` | 新增防漂移回归 | 否 |
| existing health / v8.6 tests | 仅在必要时增加一致性断言 | 否 |
| `core/bootstrap.yaml` 等 release carriers | 仅 release 阶段统一到 8.6.1 | 版本元数据 |
| generated indexes / MANIFEST | 生成器更新 | 否 |

若实施时发现必须修改 `core/workflow_router.yaml`、resolver 逻辑或写作 Authority 主体，先停止并重新评估 scope；不能把实际行为改动藏在“consistency cleanup”中。

---

## 13. 测试与验收设计

### 13.1 新增 v8.6.1 专项测试

建议新增：

`tests/test_v861_active_consistency_semantic_drift.py`

覆盖：

1. current evaluation release state closure；
2. historical evaluation snapshot labeling；
3. CHANGELOG heading completeness；
4. template fixed-example non-authority declaration；
5. adaptive subsection semantics still present；
6. output pointer resolves to current reasoning Authority key；
7. A196 provenance 不扩散到 runtime solver/subsection hard rules；
8. resolver Model Approval / preprocessing / user-execution boundary cases；
9. current release carriers parity。

### 13.2 保全回归

必须继续通过：

- `tests/test_v860_model_construction_solution_rationale.py`
- `tests/test_v840_author_reasoning_writing.py`
- `tests/test_v801_chapter_capability_preservation.py`
- `tests/test_v752_entrypoint_parity.py`
- `tests/test_current_skill_health.py`
- `tests/test_active_consistency_cleanup.py`
- 既有 router / approval / template / LaTeX tests

### 13.3 全量验收

本地/CI 最低要求：

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests
python scripts/generate_indexes.py --check
```

若 CI 工作流仍维持当前矩阵，正式 release 前要求：

- Python 3.10 / 3.11 / 3.12 / 3.13 / 3.14 green；
- Static contract lint green；
- Generated File Contract green；
- CUMCM LaTeX green；
- MCM/ICM LaTeX green；
- Diangong LaTeX green；
- Production LaTeX attestation green。

### 13.4 Generated Files

禁止手工改：

- `SKILL_FILE_INDEX.md`
- `TEMPLATE_INDEX.md`
- `MANIFEST.sha256`
- 其他由 generator 管理的索引/哈希。

流程必须是：

```text
source changes
→ scripts/generate_indexes.py
→ inspect generated diff
→ generated-only commit / bot refresh
→ re-run checks
```

---

## 14. 版本发布策略

### 14.1 为什么目标是 8.6.1 patch

本轮若按计划实施，不新增 workflow capability，不改 Schema/CLI/目录，不改变论文数学规则，而是修复：

- current docs state drift；
- integration pointer completeness；
- example/runtime semantic isolation；
- release-history parser completeness；
- existing resolver boundary 可读性与回归保护。

因此属于兼容性 patch。

### 14.2 何时才改 release carriers

计划文件阶段：

```text
bootstrap = 8.6.0
plugin = 8.6.0
README current = 8.6.0
```

实施完成、专项测试和全量回归通过后，才统一切换：

```text
8.6.0 → 8.6.1
```

需要同步的 carriers 以现有 parity test 为准，不通过全仓库盲替换完成。

---

## 15. 实施顺序

批准后按以下顺序执行，避免同时碰多个语义面：

### Step 0 — Reconfirm current main

- 重新读取 `core/bootstrap.yaml` 与治理文件；
- 检查 `main` 是否仍为本计划基线或已有新 commit；
- 检查新出现的重叠 PR；
- 若 main 已前进，先 compare/rebase/recreate branch，再实施。

### Step 1 — Documentation state closure

先修 F1/F2/F5：

- v8.6 final release state；
- v8.4/v8.5 historical snapshot semantics；
- CHANGELOG heading consistency；
- 先加对应 tests。

这一阶段不得碰 runtime semantics。

### Step 2 — Template semantic isolation

处理 F3/F6：

- template manifest example/smoke role；
- template README；
- A196 provenance isolation tests；
- simple/complex subsection regression。

若出现消费者依赖 `default_complex_question_headings` 作为 runtime requirement，停止并报告，不直接改字段。

### Step 3 — Integration pointer & router readability

处理 F4/F7：

- output contract named pointers；
- RUNTIME_ROUTER resolved-plan explanation；
- approval/preprocessing/execution boundary tests。

原则：文档/指针必须追随 resolver 当前行为，不反向改变 resolver 以符合说明。

### Step 4 — Targeted regression

先运行 v8.6.1 专项、v8.6、health、entrypoint、template/router tests。

### Step 5 — Full suite

运行全量 tests/lint/generator check。

### Step 6 — Release sync

所有语义与行为测试通过后再：

- bump 8.6.1 carriers；
- 更新 README / CHANGELOG current release；
- 重新生成 indexes / manifest；
- 完整 CI。

### Step 7 — PR finalization

PR 描述必须包含：

- 每个 F1–F7 的处理 disposition；
- 哪些只文档澄清，哪些新增 regression；
- 哪些风险明确 deferred；
- generated diff；
- final CI head；
- compatibility / rollback。

---

## 16. 完成判据（Definition of Done）

只有全部满足才可宣称 v8.6.1 本轮完成：

```text
[ ] v8.6 evaluation 不再把 merged release 描述为 current draft/pending
[ ] v8.4/v8.5 evaluation 的历史快照语义明确
[ ] README -> v8.6 evaluation 链不会产生 current-state 误读
[ ] CHANGELOG 所有 release heading 可被同一 parser 识别
[ ] canonical example 明确为 smoke/example，不是 adaptive subsection Authority
[ ] simple analytic 与 complex multi-stage 两类 subsection case 均有回归保护
[ ] A196 只停留在 provenance/reference boundary
[ ] output_contract 可追踪 v8.6 rationale / parameter evidence owner
[ ] RUNTIME_ROUTER 明确 raw route 与 resolved plan 差异
[ ] 未审批 full_solution 仍停 awaiting_model_approval
[ ] project_level 预处理边界未改变
[ ] user execution boundary 未改变
[ ] v8.6 Author Reasoning Voice / Model Construction Rationale tests 全保全
[ ] root/package Skill parity 保持
[ ] all release carriers = 8.6.1（仅 release 阶段）
[ ] generated metadata 由 generator 产生且 fresh
[ ] full CI green
[ ] PR review 无 unresolved blocking
```

---

## 17. 失败/停止条件

以下任一发生时，停止扩大修改并回报：

1. 为处理 F3 必须删除/重命名被 runtime consumer 使用的 template 字段；
2. 为处理 F7 需要改变 resolver 公共输出 schema 或 CLI；
3. 新测试暴露实际 Model Approval boundary bug，而不是文档误读；
4. A196 profile 已被某 active runtime 分支直接用于模型/solver 选择；
5. release-heading 修复会破坏外部工具依赖的既有格式；
6. 同期出现新 PR 修改相同 Authority；
7. main 在实施期间发生相关语义更新。

遇到以上情况应拆分新方案，不允许把 patch 偷偷扩大为 refactor/minor。

---

## 18. 预期最终结果

完成后，仓库应形成更明确的三层关系：

```text
历史评估材料
→ 保存当时发生过什么
→ 不冒充 current runtime 状态

Current Authority / Runtime
→ 决定当前语义和执行边界
→ 示例、provenance、历史计划不能反向覆盖

Regression / CI
→ 防止 release 状态、示例形状、raw route 声明再次被误读为 Authority
```

本轮成功标准不是“文件更整齐”，而是减少后续聊天、维护者和模型在以下位置发生错误推断的概率：

```text
旧 candidate 状态 → 被当作 current release
canonical example → 被当作 mandatory paper template
A196 provenance → 被当作 current writing rule
raw route outputs → 被当作 effective approved outputs
named pointer 缺失 → 被误判为 capability 未正式集成
```

---

## 19. 当前计划结论

截至本计划写入时：

```text
baseline_skill = 8.6.0
implementation_started = true
semantic_patch_ci = HSK Skill CI #2411 success
release_sync = complete
final_release_ci = pending
runtime_behavior_changed = false
target_patch = 8.6.1
scope = active consistency + semantic drift hardening
main_direct_write = forbidden
branch = fix/v8.6.1-active-consistency-semantic-drift
```

用户已明确批准实施；后续仍严格按本计划的 patch scope、停止条件与分阶段 release sync 执行。