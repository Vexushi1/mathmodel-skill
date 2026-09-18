# v9.3.1 Post-Release Health Remediation Plan

> 仓库：Vexushi1/mathmodel-skill  
> 审计基线：main@4018b3339ce7c1f223039d0c94020fc7378444b1  
> 计划创建时 Skill：9.3.0  
> 实际修复完成版本：9.3.1；release closeout 与 main post-merge verification 已通过  
> 本文件角色：维护计划与修改参考，不是 Runtime、Modeling、Approval、Schema 或 Writing Authority  
> 修改原则：先修真实语义缺口，再处理一致性与卫生；不新增后置 Gate，不削弱既有测试，不借修复扩大业务范围。

---

## 0. 修改简报

修改主题：v9.3.0 post-release semantic/read-path remediation

当前版本：9.3.0

目标版本：9.3.1，候选 patch；本 planning PR 本身不升版本。

直接目标：

1. 恢复 v9.3 重构中意外丢失的 Module 02 framework、mechanism contract 与 stage-gate 语义。
2. 修复 taxonomy 允许的合法多结构分类可能导致 Resolver task-pack budget ValueError。
3. 让活动模板、Manifest、Approval Brief 和项目记忆与“最小充分主模型 + 0..N comparator”保持一致。
4. 增加 capability-preservation、read-path、resolver regression，防止“新功能通过但旧能力被删”再次发生。
5. 区分 Runtime bug、active semantic drift、maintenance status drift 与纯仓库卫生债务。

明确不做：

- 不增加新的 workflow stage。
- 不增加新的 pre_delivery_gate。
- 不增加第三套 Model Review。
- 不改变用户 full-fidelity 执行所有权。
- 不改变 Workbook Schema。
- 不改变结果工作簿物理布局。
- 不改变 Python/MATLAB ownership。
- 不改变 LaTeX 主链。
- 不批量迁移旧项目。
- 不把历史 docs 全部删除。
- 不在核心 bugfix PR 中顺手删除大量旧 branch。
- 不直接写 main。
- 不通过删除、弱化测试让 CI 通过。

权威事实源：

- 启动：core/bootstrap.yaml
- 全局规则：core/hsk_core_policy.md
- 路由与读取：core/workflow_router.yaml
- 分类：core/task_taxonomy.yaml
- 模块产物：core/module_manifest.yaml
- 模型设计：modules/02_model_design.md
- 模型批准：core/model_approval_contract.yaml
- 项目记忆模板：templates/model/model_paper_framework.md
- Resolver：scripts/resolve_workflow.py 与 scripts/resolve_runtime.py
- 生成索引：scripts/generate_indexes.py
- 修改治理：SKILL_CHANGE_GOVERNANCE.md

兼容性要求：

- route IDs 不变。
- CLI 不变。
- required Schema root fields 不变。
- project_state、workbook、output 现有接口保持可读。
- root/package SKILL.md parity 保持。
- structured Semantic Identity v1 继续兼容。
- old projects read-compatible。
- Model Challenge、Human Approval、typed stale 不变。
- route_comparison、selected_models 等旧 artifact key 保留。

迁移要求：

- 无批量迁移。
- 旧 live project 不因模板升级自动 stale。
- 只有重新进入 model_design 且真实模型语义变化时，才按现有 semantic-governance 规则递增 revision。
- 新增 framework 记录槽位对旧项目采用“缺失可读、重新设计时渐进补齐”。

回滚方式：每个实现 PR 可独立 revert，不依赖不可逆 Schema migration。

---

# 1. 审计结论与严重度

| ID | 严重度 | 类型 | 已确认事实 | 影响 |
|---|---|---|---|---|
| A1 | HIGH | semantic loss / read insufficiency | modules/02_model_design.md 在第 10 节首段后结束；v9.2.1 中存在的 framework read/write rules、第 11 节机理图合同、阶段门槛已丢失 | Router 的轻量 framework read 仍读取第 10 节，但实际内容不足；Manifest 仍声明 mechanism_contracts |
| A2 | HIGH | resolver failure | taxonomy 允许 1 objective + 最多 3 structures；Resolver 映射 unique task packs 后硬编码大于 3 报错 | 合法分类可直接无法进入模型设计 |
| A3 | HIGH-MEDIUM | regression gap | v9.3 regression 主要验证新行为，没有验证 Module 02 尾部旧能力保存 | CI 全绿仍允许旧语义被删除 |
| B1 | HIGH-MEDIUM | active semantic residue | templates/problem/model_route_compare.md 仍固定经典稳健 + 高级创新/融合双路线 | 与 v9.3 主模型 + comparator 语义冲突 |
| B2 | HIGH-MEDIUM | project-memory gap | Framework 有 Reduction Provenance / Rationale，但缺少稳定 Condition→Consequence、minimal-sufficiency reason、comparator purpose 槽位 | 跨聊天可恢复最终模型，但不一定恢复关键生成逻辑 |
| B3 | MEDIUM | authority drift | Approval Contract 仍以 route_selection_fit、rejected_route_reason、simpler_baseline_may_be_sufficient 为主要旧术语 | Module 02 与 Approval Authority 口径不完全一致 |
| B4 | MEDIUM | manifest drift | route_comparison 和 selected_models 的描述仍是旧路线语义；Manifest 仍输出 mechanism_contracts | consumer 容易重新理解成传统路线选择；A1 造成 output 无业务合同 |
| C1 | LOW-MEDIUM | maintenance drift | docs/skill_optimization_status.md 未记录 v9.3.0 | 维护者可能误判当前优化进度 |
| C2 | LOW-MEDIUM | repository hygiene | 当前约 168 branches，v9.3 已合并 branch 仍保留 | 搜索与维护噪声，不影响 Runtime |
| C3 | LOW-MEDIUM | active-index hygiene | docs 中大量历史 plan/status/phase 文件仍出现在 Active Skill File Index | Agent/code-search 容易命中旧版本与旧路线语义 |
| C4 | LOW | discovery drift | plugin/agent 描述没有突出 condition-driven reduction / minimal-sufficient modeling | UI/discovery 语义落后，Runtime 可通过 bootstrap 恢复 |
| C5 | LOW | terminology debt | task packs 标题仍为“路线比较与初始化结构化简优先项” | 行为正确，标题仍带旧框架词汇 |

当前健康项：

- main 已是 v9.3.0 release merge。
- 当前无 open PR。
- Bootstrap、Router、Manifest、Output、Writing Runtime、Core Policy、root/package Skill、plugin、README、CHANGELOG 的活动版本均闭合到 9.3.0。
- root SKILL.md 与 packaged SKILL.md 当前一致。
- main 上 HSK Skill CI 成功。
- generated repository metadata workflow 成功。
- 正常 model-design route 仍会加载 Module 02 和 classified task packs。
- legacy 不进入默认执行链。

---

# 2. 总体修复策略

本轮禁止一次性改大量活动文件。按风险分层：

Layer 1：Critical semantic restoration  
A1 + A3

Layer 2：Resolver/read-path correctness  
A2

Layer 3：v9.3 semantic surface alignment  
B1 + B2 + B3 + B4 + C5

Layer 4：Maintenance/discovery/hygiene  
C1 + C4  
C2/C3 单独治理，不与 patch 核心实现混合。

优先级：

Runtime correctness  
> semantic consistency  
> maintenance clarity  
> repository cosmetic cleanup

---

# 3. PR A — Module 02 Capability Restoration

建议分支：fix/v9.3.1-model-design-capability-restoration

目标：只修 A1/A3。

预计修改文件：

- modules/02_model_design.md
- tests/test_v930_initial_modeling_core.py
- 新增 tests/test_v931_model_design_capability_preservation.py
- 如确有必要，最小修改 scripts/lint_skill_checks.py
- generated files 仅由自动流程更新

## 3.1 恢复 Framework 职责

以 v9.2.1 最后稳定版本为 provenance，不做盲目整段 copy。恢复并重新对齐：

- framework 是项目级长期工作记忆。
- compact / full 两种角色。
- 单问 continuation 使用 targeted read。
- full paper、cross-chat、final review 使用 full read。
- framework stale 时先修上游状态。
- concrete numbers 回 accepted workbook。
- framework 不替代 machine state 或 workbook。

## 3.2 恢复 Framework 写入规则

恢复：

- current-only。
- SIB 完整后再写。
- 不保存历史对话。
- design 时 result pending。
- Rationale、Algorithm Trace、PQS 只保存项目事实。
- baseline / alternative / validator 只有真实 artifact 时登记。
- 不复制通用规则。

并补充 v9.3：

- Condition→Consequence 只保存本题实际使用的高价值条目。
- minimal-sufficiency reason。
- comparator purpose，仅启用时。
- 不把结构原语大全复制进 framework。

## 3.3 恢复第 11 节机理图合同

使 Manifest 的 mechanism_contracts 有真实 Module 02 producer contract。

要求：

- 只定义解释对象、公式或约束锚点、必需变量、排除变量。
- S/A 级图绑定核心公式、约束或命题。
- 不画通用流程图替代题目机制。

## 3.4 恢复阶段门槛

恢复“设计完整性 + 审批完整性”双层闭合，并加入 v9.3：

- condition-driven reduction 已完成。
- minimal-sufficient reason 已明确。
- comparator 若启用，有明确 comparison question。
- solver selection 在 reduction 后。
- Formula Trace、Algorithm Trace、PQS、Approval 旧规则继续保留。

## 3.5 PR A 验收

必须证明：

- 第 10 节不再是单段截断。
- 第 11 节机理图合同存在。
- 阶段门槛存在。
- Manifest 的 mechanism_contracts 在 Module 02 有业务定义。
- Router framework_result_sync 读取第 10 节时能获得真正 read/write rules。
- v9.3 新语义没有被旧内容反向覆盖。

必须新增的 preservation regression 至少包括：

- framework read rules retained
- framework write rules retained
- mechanism contract semantics retained
- stage gate contract retained
- v9.3 generation order retained

不能只检查单个 token，至少检查 heading 顺序与关键语义组合。

---

# 4. PR B — Resolver Task-Pack Budget Closure

建议分支：fix/v9.3.1-task-pack-budget-closure

目标：修 A2，并消除 Router/Resolver budget 双重事实源。

当前冲突：

- taxonomy 允许一个 objective。
- taxonomy 允许最多三个 structures。
- 理论最大 unique Pack 可为 objective pack + 三个 structure packs = 四个。
- Resolver 当前硬编码超过三个 Pack 就 ValueError。
- Router 同时声明 task_pack_budget = 3。

## 4.1 首选修复方案

1. core/workflow_router.yaml 中 classification_contract.task_pack_budget 作为读取 budget Authority。
2. budget 从 3 调整为 4，使其至少能容纳当前 taxonomy 合法最大组合。
3. scripts/resolve_workflow.py 删除硬编码数字，读取 Router 声明。
4. 增加 consistency test，确保 Router budget 不小于 taxonomy 当前声明可能产生的合法 unique pack 数。
5. objective/structure 映射到同一 Pack 时继续 deduplicate。

## 4.2 明确不采用

- 不静默丢弃第三个 structure 对应 Pack。
- 不只加载所谓最重要两个 Pack 而没有确定性依据。
- 不把 structures_max_items 从 3 降为 2 迎合旧 budget。
- 不吞掉异常继续求解。
- 不让 Resolver 继续保留另一套 magic number。

## 4.3 代表性回归

必须加入合法四 Pack case：

objective = optimization

structures = spatial + network + stochastic

expected packs：

- optimization
- spatial
- graph_network
- simulation

并验证：

- resolve 成功。
- Module 02 仍加载。
- Pack 顺序确定。
- load_order 与 reading_plan 可构建。
- Model Approval pause semantics 不变。

同时测试：

- objective 与 structure 映射同一 Pack 时 dedupe。
- 超 taxonomy structures 数量仍 fail closed。
- Router budget 人为小于合法分类上限时测试失败。
- budget 改动只影响读取，不新增 lifecycle stage。

---

# 5. PR C — v9.3 Semantic Surface Alignment

建议分支：fix/v9.3.1-structural-reduction-surface-alignment

只在 PR A/B 合并后，基于最新 main 开始。

## 5.1 更新活动 Route Compare Template

当前 templates/problem/model_route_compare.md 仍固定：

- 经典稳健 + 本题改进
- 高级创新/融合

更新为主模型与 comparator 表达。保留文件路径，避免无必要路径兼容破坏。

建议字段：

| 小问 | 角色 | 模型/结构 | 题目条件与数学后果 | Reduction Provenance | comparison question / answer | 数据与计算支撑 | 关键局限 | 是否主模型 |
|---|---|---|---|---|---|---|---|---|
| Q1 | main |  |  |  | 完整回答本问 |  |  | yes |
| Q1 | comparator，可选 |  |  |  | 明确比较问题 |  |  | no |

规则：

- 每问一个 current minimal-sufficient main model。
- comparator 为 0..N。
- 高级不是固定角色。
- simple baseline 也可以是 comparator。
- template 不做 Approval Authority。

## 5.2 Framework 持久化 v9.3 初始化事实

在每问当前模型口径的既有 semantic scope 内增加轻量项目事实，不增加第二套手册。

建议新增：

Condition → Consequence / Reduction Summary

| ID | 题面条件或定义 | 数学后果 | reduction | 下游作用 |
|---|---|---|---|---|

Minimal Sufficiency

- 当前主模型
- 为什么已经充分
- 若继续简化首先损失
- 未进入主模型的机制及理由

Comparator Envelope，按需

| Comparator | role | comparison question | extra structure | evidence target | status |
|---|---|---|---|---|---|

规则：

- comparator=0 时允许明确 not_applicable。
- 不要求旧项目批量补齐。
- 不新增 SIB root required field。
- 如需 machine-stable binding，只使用现有 extensions，且必须单独论证必要性。
- template wording change 本身不得伪造 semantic revision。

## 5.3 Approval Contract 语义对齐

原则：不创建新 Gate，不改变 approval 状态机。

优先做解释层对齐：

- structure_before_algorithm 明确包含 Condition→Consequence。
- simpler_baseline_may_be_sufficient 明确属于 minimal-sufficiency challenge。
- structural_simplification 在 Approval Brief 中包含 minimal-sufficiency rationale。
- rejected_route_reason 保持兼容字段，但允许 not_applicable、被否决 alternative 理由、comparator 未升为主模型的理由。
- 不要求每问必须存在 rejected route。
- comparator 不自动触发 advanced-method 主模型准入。

只有现有字段确实无法表达时，才考虑 additive optional field；不能把 patch 变成 schema migration。

## 5.4 Manifest 描述对齐

保留 artifact key，但更新含义：

route_comparison：当前最小充分主模型与 0..N 信息型 comparator 的模型选择与比较记录。

selected_models：每问当前选定的最小充分主模型。

同时确认：

- mechanism_contracts producer 已由 PR A 恢复。
- model_design outputs 与 Module 02 真实业务合同逐项闭合。
- 不新增第二 artifact truth source。

## 5.5 Task Pack 标题债务

当前标题“路线比较与初始化结构化简优先项”是为兼容旧测试恢复的。

首选新标题：

“初始化结构化简优先项与 comparator 选择”

但只有在搜索确认不存在真实 heading consumer 后才修改。

必须先检查：

- Router heading selector
- Markdown cross-link
- tests
- docs anchor
- external consumer

若存在真实 consumer，先保留兼容锚点或延后，不能为术语清理制造读取失败。

---

# 6. PR D — Maintenance Status & Discovery Alignment

建议分支：docs/v9.3.1-maintenance-status-alignment

该 PR 只做 docs/metadata，不和核心 Runtime 修复混合。

## 6.1 更新 skill_optimization_status

追加 v9.3.0 章节：

- PR #178 core initialization modeling
- PR #179 domain reduction cues
- PR #180 release closeout
- v9.3.0 merge 4018b333...
- post-release audit 发现 v9.3.1 remediation
- 明确该文件仍是 implementation record，不是 Authority

不改写旧 P1–P9 历史事实。

## 6.2 Discovery 文案

按最小范围检查并更新：

- .codex-plugin/plugin.json description
- agents/openai.yaml short_description
- 必要时 default_prompt 增加一句结构优先提醒

只反映三个稳定概念：

- condition-driven structural reduction
- minimal-sufficient main model
- structure-matched solver

不得在 agent prompt 复制 Module 02 完整规则。

---

# 7. Repository Hygiene — 单独审批

C2/C3 不进入 v9.3.1 核心 patch。

## 7.1 Branch 清理

当前约 168 branches。

本计划不自动删除任何 branch。

先生成 inventory，至少包含：

- branch
- tip SHA
- merged into main
- associated PR
- PR state
- last commit time
- protected
- unique commits not in main
- recommended action

分类：

- SAFE_DELETE_CANDIDATE
- KEEP_PROVENANCE
- ACTIVE_UNKNOWN
- BLOCKED
- MANUAL_REVIEW

只有同时满足以下条件才可进入删除候选：

- merged into main
- no unique commits
- no open PR
- not protected
- not explicitly retained

v9.3 四个已合并 branch 可优先进入 inventory，但在用户单独批准前不得删除。

## 7.2 历史 docs / Active Index 分层

不按文件名直接删除。

先分：

- current_reference
- current_maintenance_status
- historical_provenance
- migration_contract
- obsolete_duplicate

目标不是减少文件数，而是降低 active-search 噪声。

优先方案：

1. 保留文件原位，但生成索引分为 Active Runtime/Reference 与 Historical Maintenance Provenance。
2. 若仍有明显检索污染，再考虑迁入 legacy/maintenance。
3. 删除只用于完全重复且无 provenance 价值的文件。

历史 plan 中旧版本号、旧阶段状态如果属于当时事实，不得全仓替换成 9.3.1。

---

# 8. 测试矩阵

所有实现 PR 至少执行：

    python scripts/lint_skill.py
    python -m unittest discover -s tests -p "test_*.py"
    python scripts/generate_indexes.py --check

PR A 重点：

- v9.3 initial modeling regression
- Module 02 preservation regression
- runtime health coherence
- content packs
- Manifest closure
- compact/full framework tests
- semantic identity / governance
- model approval tests

PR B 重点：

- router contract
- runtime assurance
- reading plan
- taxonomy/classifier
- resolver representative cases
- 新四 Pack 合法分类
- legacy single-intent compatibility

PR C 重点：

- content packs
- template/index generation
- model approval
- framework validator
- semantic identity
- v9.3 domain reduction cues
- v9.3 initial modeling core
- current Skill health
- repository reference health

Release closeout：

如果前三个实现 PR 构成真实 patch 行为修复，再单独 release PR：

- 9.3.0 → 9.3.1
- current carriers only
- CHANGELOG
- README
- release regression
- generated indexes / manifest
- full HSK Skill CI
- Optimization baseline evidence
- main post-merge CI

---

# 9. 版本策略

A1/A2 属于 v9.3.0 已发布行为 bug：

- A1：旧语义被意外删除。
- A2：合法分类可 Runtime fail。

计划保持 CLI、Schema、route IDs、artifact keys、directory、user execution、workbook/output 全部兼容，因此候选为 patch 9.3.1。

如果实施过程中发现必须：

- 新增 required Project State field
- 修改 SIB required root schema
- 修改 route ID
- 修改 CLI
- 修改目录
- 破坏旧 framework parser
- 强制旧项目迁移

立即停止，重新评估 minor/major，不得把破坏性修改塞入 9.3.1。

---

# 10. 单一事实源要求

修复后必须形成：

Taxonomy  
定义合法 classification。

Router  
定义 load policy 和 task pack budget。

Resolver  
解释 Router，不复制 budget magic number。

Module 02  
定义模型生成与 framework、mechanism、stage semantics。

Approval Contract  
定义 approval 字段级行为。

Framework Template  
保存当前项目事实，不复制 Module 02 教程。

Manifest  
描述 artifacts，不重新定义业务规则。

特别禁止：

- 在 Framework 重写完整结构原语。
- 在 Approval Contract 再实现一套 Module 02。
- 在 Resolver 硬编码 Router 数字。
- 在 template 固定高级创新第二路线。
- 在 agent default prompt 复制完整建模合同。

---

# 11. 验收行为场景

## Case 1：简单解析题

期望：

- Condition→Consequence
- exact reduction
- 一个 minimal-sufficient main model
- comparator = 0
- 不机械生成 advanced route
- Approval Brief 可记录 comparator not_applicable

## Case 2：PDE / 机理题

期望：

- mechanism pack loaded
- 守恒、参考系、对称先于 solver
- mechanism_contracts 可恢复
- high-fidelity model 可作为 comparator
- framework 可恢复 reduction logic

## Case 3：合法四 Pack 组合

optimization + spatial + network + stochastic

期望：

- Resolver 成功
- 四个 unique packs 全加载
- 不静默丢结构
- reading plan 可构建
- approval pause 正确

## Case 4：Comparator 暴露主模型不足

期望：

comparator 发现缺失必要结构  
→ 返回 model_design  
→ 只加回 minimum necessary structure  
→ 形成新的 minimal-sufficient main model

禁止自动把最复杂模型升级为主模型。

## Case 5：framework_result_sync 快捷读取

期望：

- Router 读 Module 02 第 8 节与第 10 节。
- 第 10 节包含真实 framework read/write semantics。
- 不需要加载整个 Module 02。
- 不丢 stale、numeric-source、current-only 边界。

---

# 12. 完成判据

Runtime：

- 合法 classification 不因 task-pack budget 人为失败。
- Router/Resolver budget 单一事实源。
- reading_plan 无新增失败。
- route、CLI、gates 不变。

Modeling：

- Condition→Consequence 仍是 model naming 前步骤。
- minimal-sufficient main model 仍是默认。
- comparator 仍是 0..N。
- solver 仍后置。
- advanced method 不恢复为默认 Route B。

Semantic persistence：

- framework 能恢复高价值 reduction logic。
- minimal-sufficiency rationale 可恢复。
- comparator purpose 可恢复。
- old projects 仍可读。

Capability preservation：

- Module 02 framework read/write rules 恢复。
- mechanism contract 恢复。
- stage gate 恢复。
- Manifest producer/output 闭合。

Repository health：

- active release carriers 一致。
- root/package Skill parity。
- generated indexes / manifest 正常。
- full CI + Optimization baseline 全绿。

---

# 13. 执行停止条件

任何阶段出现以下情况必须停止并报告，不自动扩大修复：

1. 需要改变 required Schema。
2. 需要改变 CLI。
3. 需要批量迁移旧项目。
4. 需要删除现有有效 Gate。
5. 需要弱化现有测试。
6. 发现另一个 open PR 修改同一 Authority。
7. main 在当前 PR 开发期间发生重叠语义变更。
8. generated metadata 出现非预期业务文件变化。
9. branch cleanup 发现未合并 unique commits。
10. docs hygiene 发现历史文档被 Runtime/Test 显式消费。

---

# 14. 实施记录模板

后续每个 PR 在本计划中只追加状态，不改写历史裁决：

PR:  
Branch:  
Base main SHA:  
Scope:  
Files:  
Tests:  
CI:  
Generated files:  
Review blockers:  
Merge SHA:  
Residual issues:  
Next stage:

状态枚举：

- NOT_STARTED
- IN_PROGRESS
- CI_PENDING
- BLOCKED
- MERGED
- DEFERRED

---

# 15. 当前实施状态

Plan PR: MERGED（PR #181，merge `b4fe9e3abc81a4481a322b5bd756913d2492e256`）  
PR A: MERGED（PR #182，merge `87a9d3b362562df7265ef2e790d0baf86f44973c`）  
PR B: MERGED（PR #183，merge `2de9f60f12e50612bc6ff4f451cab2dad855dac4`）  
PR C: MERGED（PR #185，merge `ed0f013fc024dc9d27c2ead6b370a21f7b6f88eb`）  
PR D: MERGED（PR #186，merge `48d05a98f6a7dd97770f8a1adc9c88e2cde29462`）  
Release 9.3.1: MERGED（PR #187，merge `8a9de52b85a93bb4e04bc03d4298da93b51de326`）  
Branch hygiene: DEFERRED_PENDING_EXPLICIT_APPROVAL  
Docs archive/index hygiene: DEFERRED_PENDING_INVENTORY

## 15.1 PR A 实施记录

PR: #182 — `fix: restore model-design capability closure after v9.3`  
Branch: `fix/v9.3.1-model-design-capability-restoration`  
Base main SHA: `b4fe9e3abc81a4481a322b5bd756913d2492e256`  
Scope: 恢复 Module 02 framework read/write、`mechanism_contracts` producer semantics 与阶段门槛，并增加 capability-preservation regression。  
Files: `modules/02_model_design.md`、`tests/test_v931_model_design_capability_preservation.py` 与 generated metadata。  
Tests: full HSK Skill CI passed。  
CI: success。  
Generated files: generator-produced metadata synchronized；中途 stale generated file failure 已按生成流程修正，未削弱 gate。  
Review blockers: none。  
Merge SHA: `87a9d3b362562df7265ef2e790d0baf86f44973c`。  
Residual issues: A2/B1–B4/C1–C5 继续按本计划后续阶段处理。  
Next stage: PR B。

## 15.2 PR B 实施记录

PR: #183 — `fix: close taxonomy-valid task-pack budget gap`  
Branch: `fix/v9.3.1-task-pack-budget-closure`  
Base main SHA: `87a9d3b362562df7265ef2e790d0baf86f44973c`。  
Scope: 修复 taxonomy 合法的 objective + 3 structures 可能解析为 4 个 unique task packs、却被旧 3-pack budget 拒绝的问题；把 budget 读取收口到 Router；同步 legacy compatibility alias，不改变 lifecycle。  
Files: `core/workflow_router.yaml`、`scripts/resolve_workflow.py`、`core/project_state.schema.yaml`、`modules/01_problem_audit.md`、`tests/test_v931_task_pack_budget_closure.py`、一处兼容 drift guard 与 generated metadata。  
Key closure:
- Router `task_pack_budget: 4` 可覆盖当前 taxonomy 最大合法 unique-pack 组合；
- Resolver 读取 Router budget，不再硬编码 3；
- `legacy_task_packs` 作为派生兼容 alias 不再在 Project State Schema 重复设置 `maxItems: 3`；
- Module 01 明确 compatibility packs 必须完整派生、去重，不得人为截断；
- 超过 taxonomy 的 3 structures 上限仍 fail closed。
Tests: 新增合法四 Pack、reading-plan、dedupe、schema compatibility、Router-authoritative budget 等回归。  
CI: PR head 的 HSK Skill CI 与 Optimization baseline evidence 均 success；merge 后 main 的 HSK Skill CI 与 generated metadata refresh 均 success。  
Review blockers: none。  
Merge SHA: `2de9f60f12e50612bc6ff4f451cab2dad855dac4`。  
Residual issues: B1/B2/B3/B4/C5 进入 PR C；C1/C4 进入 PR D；branch/docs hygiene 继续保持单独审批。  
Next stage: PR C — v9.3 Semantic Surface Alignment。

## 15.3 PR C 实施记录

PR: #185 — `fix: align v9.3 structural-reduction semantic surfaces`  
Branch: `fix/v9.3.1-structural-reduction-surface-alignment`  
Base main SHA: `10466507e23e701293bfff597e2c3bbdb4629836`。  
Scope: 对齐 active route-comparison template、Framework 的 Condition→Consequence / Minimal Sufficiency / Comparator Envelope 项目记忆、Model Approval compatibility field semantics、Manifest artifact descriptions 与十类 Task Pack section-2 heading；不新增 Gate、required Schema、CLI 或迁移。  
Tests: content-pack、Framework project-memory、Model Approval、v9.3 domain-reduction regressions 与完整 HSK Skill CI。  
CI: final PR head `3128dfd9c28841ebb09360ecd7bf7d8c3da6d8c1` HSK Skill CI success；Optimization baseline evidence 在与 final head tree 完全一致的直接父提交上 success；merge 后 main HSK Skill CI 与 generated metadata refresh 均 success。  
Review blockers: none。  
Merge SHA: `ed0f013fc024dc9d27c2ead6b370a21f7b6f88eb`。  
Residual issues: C1/C4 进入 PR D；branch/docs hygiene 继续保持单独审批。  
Next stage: PR D — Maintenance Status & Discovery Alignment。


## 15.4 PR D 实施记录

PR: #186 — `docs: align v9.3 maintenance status and discovery surfaces`  
Branch: `docs/v9.3.1-maintenance-status-alignment`  
Base main SHA: `ed0f013fc024dc9d27c2ead6b370a21f7b6f88eb`。  
Scope: 更新 `docs/skill_optimization_status.md` 的 v9.3 实施 provenance，并让 plugin/agent discovery surface 显式反映 condition-driven structural reduction、minimal-sufficient main model 与 structure-matched solver；不改变 Runtime 行为。  
Tests: current-skill health/discovery regression、release-carrier parity 与完整 HSK Skill CI。  
CI: PR head HSK Skill CI 与 Optimization baseline evidence 均 success；merge 后 main HSK Skill CI 与 generated metadata refresh 均 success。  
Review blockers: none。  
Merge SHA: `48d05a98f6a7dd97770f8a1adc9c88e2cde29462`。  
Residual issues: 核心 remediation A1/A2/A3/B1–B4/C1/C4/C5 已闭合；branch/docs hygiene 仍保持单独审批。  
Next stage: PR #187 — v9.3.1 Release Closeout。

## 15.5 v9.3.1 Release Closeout

PR: #187 — `release: close v9.3.1 post-release remediation`  
Branch: `release/v9.3.1-closeout`  
Base main SHA: `48d05a98f6a7dd97770f8a1adc9c88e2cde29462`。  
Scope: 只推进活动 release carriers、README/CHANGELOG、release regression 与 generated metadata 到 9.3.1；不新增模型、Runtime、Schema、CLI、Gate 或用户项目迁移。  
Final PR head: `3609f424f099ab857e13385d2663151c6fd03ef3`。  
CI: final PR head 的 HSK Skill CI 与 Optimization baseline evidence 均 success；Generated file contract、Static lint、Python 3.10--3.14、CUMCM/MCM-ICM/Diangong LaTeX 与 Production LaTeX attestation 全部 success。  
Merge SHA: `8a9de52b85a93bb4e04bc03d4298da93b51de326`。  
Post-merge verification: `main@8a9de52b...` 的 HSK Skill CI 与 Refresh generated repository metadata 均 success。  
Status: COMPLETED。  
Branch/docs hygiene: 继续 DEFERRED，未经单独审批不执行。


---

# 16. 核心结论

本轮修复的核心不是继续增加检查，而是修复 v9.3.0 发布后发现的三个闭环问题：

读得到，不等于读充分。

分类合法，不等于 Resolver 一定可加载。

新规则写进 Authority，不等于项目记忆、模板、Approval、Manifest 已经全部同步。

因此 v9.3.1 必须保持以下顺序：

恢复丢失语义  
→ 修 Resolver 合法读取  
→ 同步活动语义面  
→ 最后才做维护与卫生

本 Plan 的核心 remediation 与 v9.3.1 release closeout 已全部完成；branch cleanup 与历史 docs/index hygiene 仍是独立治理项，未经单独审批不执行删除或迁移。
