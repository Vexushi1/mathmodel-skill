# v8.7.0 Question Writing Capability Preflight 详细修改计划

> 状态：**审批前 / Plan Only**  
> 基线：`main@89a9fa64047d32a139ada1640aecf9001a79d5ec`（v8.6.1）  
> 建议目标版本：**v8.7.0**  
> 建议实施分支：`upgrade/v8.7.0-writing-capability-preflight`  
> 本文件角色：后续实现的 Scope Contract / 上下文参考，不是 runtime Authority。  
> 当前阶段禁止：修改现有 runtime 行为、修改版本 carrier、合并 PR、把本计划中的候选字段直接视为最终 schema。

---

## 0. Executive Summary

本轮不是继续增加新的论文写作“技巧”，而是修复一个已经逐渐暴露出来的架构问题：

> **Skill 已经拥有 Core Model Summary、Formula Trace、Proposition / Proof、Algorithm Trace / Pseudocode 等高级写作能力，但 CUMCM Compact Writing Runtime 主要保证这些能力“存在且可按需访问”，没有充分保证它们在每一问正式写作前被主动检查、按项目状态自动激活。**

用户实际体验是：

- 不主动提“模型/公式汇总”，writer 可能只按照普通 §7 模型建立继续写，未主动判断该问是否需要核心模型收束；
- 不主动提“命题/证明”，writer 可能不会读取 `packs/artifact/proposition_proof.md`；
- 不主动提“伪代码/算法流程”，writer 可能不会读取 `packs/artifact/algorithm_flow.md`；
- 但一旦用户明确提醒这些词，条件读取立刻被触发，说明能力本身并未缺失，而是 **discoverability / activation 不够主动**。

因此 v8.7.0 的核心不是“把所有 Pack 开篇全量 preload”，而是引入一个轻量、逐问、状态驱动的：

# **Per-Question Writing Capability Preflight（逐问写作能力预检）**

在写每个问题章节之前，先从当前项目事实中恢复并裁决：

```text
当前问 Qx
→ Formula roles
→ Core Model Summary mode
→ Proposition / Proof state
→ Algorithm presentation mode
→ Model Construction Rationale
→ Solver Preconditions
→ Result / Validation evidence
→ Figure Evidence
→ 当前真正需要加载哪些深层 Authority / Pack
→ 再进入该问正文写作
```

目标是把当前体系从：

```text
能力存在
→ writer 是否想起来
→ 想起来才加载
```

升级为：

```text
能力存在
→ 每问预检项目状态
→ 自动判定是否激活
→ 激活后按需读取
→ 再写正文
```

同时，针对“公式收束过狠”的问题，把现有近似的“核心公式 / 普通代数”二分进一步细化为四类公式角色：

1. **Final Model Relation**：最终模型 / solver / validator 直接消费的关系；
2. **Key Bridge Relation**：连接机理、变换、证明、判据与最终模型的不可替代桥接式；
3. **Supporting Derivation**：正文推导需要，但通常不进入最终汇总；
4. **Routine Algebra**：普通代数展开、重复代换、可压缩中间式。

这样论文中的“核心模型汇总”主要收束第 1 类，并在确有必要时带入少量第 2 类；正文推导保留 1 + 2 + 必要 3；第 4 类继续压缩。

---

# 1. 当前基线与已确认事实

## 1.1 当前版本

当前 `main`：

```text
89a9fa64047d32a139ada1640aecf9001a79d5ec
```

当前 Skill：

```text
v8.6.1
```

本轮建议使用 **minor capability release：v8.7.0**，而不是 v8.6.2 patch，原因是本轮将改变写作 runtime 的“逐问读取与激活机制”，虽然不改变数学 Authority，但属于新的 runtime capability orchestration。

## 1.2 当前已有能力并不缺失

v8.6.1 已经存在：

- `core/writing_reasoning_contract.yaml#adaptive_core_model_summary`
- `core/writing_reasoning_contract.yaml#proposition_governance`
- `core/writing_reasoning_contract.yaml#algorithm_presentation`
- `core/writing_reasoning_contract.yaml#model_construction_rationale`
- `core/writing_reasoning_contract.yaml#solver_justification`
- `modules/05_writing/paper_writing_protocol.md#7-模型建立`
- `packs/artifact/proposition_proof.md`
- `packs/artifact/algorithm_flow.md`
- `templates/model/model_paper_framework.md#核心公式-Trace`
- `templates/model/model_paper_framework.md#Algorithm-Trace`
- `templates/model/model_paper_framework.md#命题与证明规划`

因此本轮不得把问题误判成“缺少命题模块”“缺少伪代码模块”“缺少模型汇总规则”。

真正缺的是：

> **每问写作开始前的统一能力发现与 activation bridge。**

---

# 2. 已确认的具体问题

## 2.1 P1 — Core Model Summary 在 Compact Runtime 中可见性偏弱

当前 `paper_writing_protocol.md` 已有核心模型汇总语义，但 Compact Runtime 的 `ordinary_writing` capability 列表没有把 `adaptive_core_model_summary` 作为与 `formula_reasoning_chain / model_construction_rationale / solver_justification` 同等级的一等能力明确暴露。

结果是：

- 它存在；
- writer 读 §7 时可以看到；
- 但运行时没有明确告诉 writer：“在正式写 Qx 之前必须先判定这问的 summary mode”。

### 风险

复杂优化模型、多方程模型、长推导后接 solver 的题目，可能直接进入求解，而缺少对最终可计算模型的可恢复收束。

---

## 2.2 P2 — `output_contract` 对 Core Model Summary 的 current pointer 不够对称

当前命题与算法已有明确 Authority pointer：

```yaml
proposition_governance: ...#proposition_governance
algorithm_presentation_contract: ...#algorithm_presentation
```

而 Core Model Summary 仍保留较强的 v7 compatibility surface：

```yaml
core_model_summary_policy: adaptive_required_inline_not_applicable
core_model_summary_policy_status: deprecated_v7_read_compatibility
```

虽然另有 rendering authority，但缺少一个清晰 current pointer：

```yaml
core_model_summary_contract: core/writing_reasoning_contract.yaml#adaptive_core_model_summary
```

### 风险

current consumer 更容易“看到兼容字段”，却没有同等显式地看到 current semantic authority。

---

## 2.3 P3 — Proposition / Proof 采用“先意识到，后读取”的被动触发

当前 runtime 条件分支大意是：

```text
当当前问题需要创建/修改/审查命题、引理、推论、等价性/可行性/单调性证明或误差界
→ 读取完整 reasoning Authority
→ 读取 proposition_proof Pack
```

这里存在一个循环依赖：

```text
需要先判断“这里值得命题化”
→ 才读取最有助于判断如何命题化的 Pack
```

用户一旦主动说“这里要不要证明”，这个循环被人工打破；不提醒时则可能没有进入该分支。

---

## 2.4 P4 — Algorithm / Pseudocode 同样依赖已有 presentation_mode 被主动消费

当前规则是：

```text
Algorithm Trace presentation_mode = stepwise / pseudocode
→ 读取 algorithm_flow Pack
```

项目框架已经保存：

- `not_needed / stepwise / pseudocode`
- Algorithm Trace 的输入、状态、核心操作、循环/分支、Formula / Proposition / Constraint anchor、终止条件、输出、Python anchor

但逐问写作 stage 没有把“先读 Qx 的 Algorithm Trace 状态”定义为一个显式 preflight gate。

### 风险

即便上游项目框架已经决定 `pseudocode`，writer 也可能因为没有主动消费该状态而直接写 prose solver 说明。

---

## 2.5 P5 — `current_question_model_formula_algorithm_result_and_figure_evidence` 过于抽象

当前 question stage 的 `read_now` 中存在一个抽象资源名：

```text
current_question_model_formula_algorithm_result_and_figure_evidence
```

但其组成没有被显式结构化为：

```text
Qx model facts
+ Qx Formula Trace
+ Qx Core Model Summary state
+ Qx Proposition Plan
+ Qx Algorithm Trace
+ Qx Result / Validation evidence
+ Qx Figure Map
```

### 风险

该名称看起来覆盖面很强，但实际 consumer 很难知道每一类子能力是否必须主动检查。

---

## 2.6 P6 — 当前公式分类过于二分

项目框架当前原则：

> 只记录决定模型结构、约束、判定、参数或结论的核心关系；普通代数中间式不登记。

这个原则保护了简洁性，但只有：

```text
核心关系
vs
普通中间式
```

两档。

一些关键桥接公式可能：

- 不直接进入最终 solver；
- 却决定一个判据、降维、边界、变量变换或可行域；
- 如果删掉，读者无法理解最终模型从何而来。

这类关系容易在“不是最终核心公式”的压缩过程中损失。

---

## 2.7 P7 — 当前测试主要验证“分支存在”，没有验证“状态能够自动激活分支”

现有测试会检查：

- proposition conditional branch 存在；
- proposition pack 路径存在；
- algorithm pack 路径存在；
- `not_needed` 条件存在。

但缺少更关键的行为级 fixture：

```text
Q2 proposition_status = planned
→ Q2 writing preflight 必须激活 proposition_proof
```

```text
Q3 algorithm_presentation = pseudocode
→ Q3 writing preflight 必须激活 algorithm_flow
```

```text
Q1 core_model_summary = required
→ 模型建立阶段必须消费 Core Model Summary 语义
```

所以 CI 现在证明的是：

> “门没有被删。”

而不是：

> “该开门时一定会开。”

---

# 3. 本轮目标

v8.7.0 建议完成以下 8 个核心目标：

1. **Per-Question Writing Capability Preflight** 作为逐问正式写作前的 mandatory read-and-decide gate；
2. **Core Model Summary Activation** 从隐藏在 §7 的能力提升为 runtime 显式 capability；
3. **Formula Role Taxonomy** 将公式角色从二分升级为四层；
4. **Proposition / Proof Auto-Activation** 根据项目框架现有 proposition state 自动加载 Pack；
5. **Algorithm / Pseudocode Auto-Activation** 根据 Algorithm Trace / presentation mode 自动加载 Pack；
6. **Project Fact Bundle Clarification** 明确 `current_question_*_evidence` 的实际组成；
7. **Behavior-Level Tests** 测试“状态 → 激活”，不只测试“branch 存在”；
8. **保持 Compact Runtime**：不恢复开篇全量 preload，不把所有 Pack 每次都读一遍。

---

# 4. 明确非目标（Non-Goals）

本轮不得演变成以下改动：

- 不把所有论文都强制设置“核心模型汇总”小节；
- 不把所有问题都强制写命题；
- 不把所有 solver 都强制写伪代码；
- 不规定“至少 N 个命题”“至少 N 个公式”“至少 N 个算法”；
- 不把 Key Bridge Relation 全部复制进最终模型汇总；
- 不让 Machine Audit 通过正则判断某公式“数学上是否关键”；
- 不创建第二套 `writing_reasoning_contract`；
- 不改变 Model Approval；
- 不改变 03A / 03B；
- 不改变 Python 用户执行边界；
- 不改变 Workbook Schema；
- 不改变 Primary Quality Specification；
- 不改变 Result Analysis disposition；
- 不改变 Figure Evidence ownership；
- 不改变正式 LaTeX compile / attestation 责任；
- 不因为本轮写作能力增强而自动改变模型 semantic revision。

---

# 5. 总体架构设计

## 5.1 新增统一概念：Per-Question Writing Capability Preflight

建议在 `core/writing_runtime_contract.yaml` 中新增一个明确结构，例如：

```yaml
per_question_writing_capability_preflight:
  mode: mandatory_before_question_body
  role: >-
    在写当前问题正文前，从 current project facts 恢复本问需要的写作能力，
    只决定需要加载哪些 Authority / Pack，不重新定义数学语义。

  inspect:
    - formula_roles
    - core_model_summary_state
    - proposition_proof_state
    - algorithm_presentation_state
    - model_construction_rationale_state
    - solver_precondition_state
    - result_validation_state
    - figure_evidence_state

  activate:
    core_model_summary: ...
    proposition_proof: ...
    algorithm_flow: ...
    full_reasoning_authority: ...
```

注意：字段名只是候选设计，实施时必须与现有 schema 风格一致后再最终确定。

## 5.2 Preflight 不是新的数学 Authority

它只能回答：

```text
“当前问有哪些能力需要被读取？”
```

不能回答：

```text
“什么情况下数学上应该证明单调性？”
“这个模型是否真的全局最优？”
“这个算法为什么适合？”
```

这些仍由现有 Authority 决定。

因此建议明确：

```text
Preflight = capability dispatcher
Reasoning Contract = semantic authority
Protocol = prose organization authority
Packs = conditional deep guidance
Framework = project-specific state/evidence
```

---

# 6. 逐问预检的输入设计

## 6.1 必须优先复用现有项目事实

不建议新建一个与 `模型论文框架.md` 平行的巨大新状态文件。

Preflight 应优先消费现有：

- 当前问模型事实；
- 核心 Formula Trace；
- 核心模型收束状态；
- Algorithm Trace；
- 命题与证明规划；
- 数值参数依据；
- Result / Validation evidence；
- Figure Map；
- 当前写作选择；
- 当前状态 / stale information。

## 6.2 允许增加最小必要项目字段

如果现有框架不足以支持稳定 dispatch，可以在 `templates/model/model_paper_framework.md` 中增加一个紧凑的逐问预检表，而不是增加全新的大段手册。

建议候选结构：

```markdown
### 逐问写作能力预检

| 小问 | Formula Roles | Core Model Summary | Proposition / Proof | Algorithm | Full Reasoning Needed | 当前状态 |
|---|---|---|---|---|---|---|
| Q1 | F1 final; F2 bridge | required | planned | pseudocode | yes | current |
```

或者更结构化地记录：

```text
Q1
- formula_roles: ...
- core_model_summary: required
- proposition_proof: planned
- algorithm_presentation: pseudocode
- capability_activation: ...
```

但必须避免把通用规则抄进项目框架。

---

# 7. Formula Role Taxonomy 详细方案

## 7.1 新四层角色

建议在 `writing_reasoning_contract.yaml` 中为 Formula Trace 增加 role taxonomy：

### A. `final_model_relation`

定义：

- 最终模型的一部分；
- solver / validator / final decision rule 直接消费；
- 或用于最终答案直接计算。

典型对象：

- objective；
- 最终 constraints；
- 状态方程；
- 观测方程；
- 最终概率关系；
- 最终阈值判据；
- 初边值条件；
- 最终输出映射。

论文行为：

- 通常保留；
- `core_model_summary=required` 时优先进入 summary；
- 必须有 Source / Derivation / Destination。

### B. `key_bridge_relation`

定义：

- 不一定直接进入 solver；
- 但连接前提与最终模型；
- 删除后会造成推导跳跃、判据来源不明、降维理由丢失或结构不可恢复。

典型对象：

- 几何距离到遮挡判据的桥接关系；
- 原变量到降维变量的变换；
- 单调性推导中的关键导数关系；
- 从物理守恒到可计算状态方程的中间关系；
- 可行域边界表达式；
- 等价变换后的核心中间式；
- 决定候选区间的判别式。

论文行为：

- 正文应保留；
- 只有在 summary 本身需要恢复“为什么最终式成立”时，才带入少量关键 bridge；
- 不默认全部复制到 final summary。

### C. `supporting_derivation`

定义：

- 对严谨推导有帮助；
- 但删除/压缩后，只要保留必要说明，最终结构仍可恢复。

论文行为：

- 按 Detail Allocation 决定展开或压缩；
- 一般不进入 summary；
- 可以合并若干代数步骤。

### D. `routine_algebra`

定义：

- 机械展开；
- 重复代换；
- 直接整理；
- 与结论无独立结构贡献。

论文行为：

- 优先省略或压缩；
- 不登记为核心 Formula Trace；
- 不进入 summary。

---

## 7.2 Formula Trace 字段扩展

现有：

```text
Formula ID | 对应小问 | Source | Depends on | Derivation | Destination | 代码/证据锚点 | 状态
```

建议增加：

```text
Role
Summary Use
```

候选：

```text
Role = final_model_relation / key_bridge_relation / supporting_derivation
Summary Use = required / optional / no
```

`routine_algebra` 默认不进入核心 Trace，因此一般不需要单独登记。

也可以避免 `Summary Use` 与语义重复，改为由 role + summary mode 推导；实现前应评估是否会产生重复状态。

---

# 8. Core Model Summary 激活方案

## 8.1 Runtime 显式能力化

在 `semantic_capabilities.ordinary_writing` 中增加：

```yaml
- adaptive_core_model_summary
```

同时在 `chapter_content_from_protocol` 中考虑增加：

```yaml
- core_model_summary_activation_and_formula_role_preservation
```

具体命名应与现有 capability 风格一致。

## 8.2 Output Contract current pointer

建议新增：

```yaml
core_model_summary_contract:
  core/writing_reasoning_contract.yaml#adaptive_core_model_summary
```

保留 v7 compatibility alias，但明确：

```text
compatibility field ≠ current semantic pointer
```

## 8.3 Preflight 判定

写 Qx 前必须读取项目框架中的 summary state：

```text
required / inline / not_applicable
```

若状态缺失：

- 不允许默认为 `not_applicable`；
- 根据 Authority 进行一次语义判定；
- 将项目实际选择写回框架；
- 然后再生成模型建立正文。

## 8.4 Summary 内容选择

`required` 时：

```text
Final Model Relations
+ 必要 Key Bridge Relations
```

而不是：

```text
所有前文公式复制一次
```

### 优化模型

优先：

```text
决策变量域（必要时邻近说明）
objective
s.t. constraints
必要边界/逻辑条件
```

目标函数仍不得塞入约束大括号。

### 非优化模型

按真实结构：

- 状态方程；
- 观测关系；
- 概率模型；
- 初值 / 边界；
- 判据；
- 输出映射。

不强套 `s.t.`。

---

# 9. Proposition / Proof 自动激活方案

## 9.1 从“用户提醒触发”升级为“项目状态触发”

Preflight 优先读取：

```text
命题与证明规划
current proposition state
```

候选状态映射：

```text
not_assessed
candidate
planned
current
stale
removed
```

### 建议 activation

- `planned/current` → 必须读取 `proposition_proof.md`；
- `candidate` → 读取 lightweight proposition criteria，必要时再进入 full Pack；
- `stale` → 阻止直接写成 current proposition，先处理 stale；
- `removed/not_applicable` → 不加载 Pack；
- `not_assessed` 且当前问题存在以下高信号结构时，触发“是否需要命题化”的语义检查：
  - 等价变换；
  - 单调性；
  - 可行性；
  - 唯一性；
  - 降维；
  - 边界判定；
  - 误差界；
  - solver 前提依赖的数学性质。

注意：高信号结构只能触发**审查**，不能自动创建命题。

## 9.2 命题 Pack 的真正作用

Pack 应继续用于：

- 命题必要性；
- 前提、定义域、结论边界；
- 证明等级；
- 下游作用；
- 正文/附录分流。

不得变成：

- “为了显得高级，每问加命题”；
- “数值验证当证明”；
- “算法结果当唯一性证明”。

---

# 10. Algorithm / Pseudocode 自动激活方案

## 10.1 Preflight 必须先消费 presentation mode

当前问写作前读取：

```text
algorithm_presentation = not_needed / stepwise / pseudocode
```

### activation

- `not_needed` → 不读 algorithm_flow Pack；
- `stepwise` → 读 Pack，生成数学步骤结构；
- `pseudocode` → 读 Pack + LaTeX algorithm environment；
- 状态缺失但 Algorithm Trace 已存在 → 语义审查并补齐 mode；
- mode 为 stepwise/pseudocode 但 Algorithm Trace 缺失 → 先补 Trace，不允许直接凭 Python 源码即兴生成伪代码。

## 10.2 Algorithm Trace 与代码的边界

继续保持：

```text
Model / Formula / Proposition / Constraint
→ Algorithm Trace
→ 论文算法
→ Python implementation anchor
→ Workbook result / validation evidence
```

不能变成：

```text
Python 源码
→ 压缩几行
→ 假装论文算法
```

## 10.3 必须保留的算法信息

当 `stepwise/pseudocode`：

- 输入 / 初始状态；
- 核心数学对象；
- 分支 / 循环 / 阶段；
- 约束处理；
- 关键参数；
- 终止条件；
- 输出；
- 输出如何回到模型变量 / 结果。

通用算法历史、百科优点和未修改标准算子不进入主体。

---

# 11. Current Question Evidence Bundle 明确化

建议不要继续只使用一个模糊自然语言 token：

```text
current_question_model_formula_algorithm_result_and_figure_evidence
```

可以有两种实现方向。

## 方案 A：保留 token，但定义 composition authority

例如在 runtime 中增加：

```yaml
current_question_evidence_bundle:
  includes:
    - current_question_model_facts
    - current_question_formula_trace
    - current_question_core_model_summary_state
    - current_question_proposition_plan
    - current_question_algorithm_trace
    - current_question_numeric_result_evidence
    - current_question_validation_evidence
    - current_question_figure_map
```

优点：改动小。

## 方案 B：Question stage 显式列出资源

把 `read_now` 拆成上述多项。

优点：可读性更强；缺点：runtime 变长。

### 建议

优先采用 **方案 A**：保持 Compact Runtime 轻量，同时让抽象 bundle 有正式定义。

---

# 12. Writing Protocol 修改计划

`modules/05_writing/paper_writing_protocol.md` 不应复制 runtime dispatcher，但需要在正文语义上补足以下内容。

## 12.1 §1 写作输入

新增提醒：

写每一问前，当前项目事实应已经明确：

- 本问 Formula roles；
- Core Model Summary mode；
- Proposition / Proof state；
- Algorithm presentation mode；
- 结果/验证 evidence。

若缺失，先返回预检补齐，不直接写正文。

## 12.2 §7 模型建立

增加“公式角色与最终模型收束”的明确规则：

```text
Final Model Relation
Key Bridge Relation
Supporting Derivation
Routine Algebra
```

强调：

- Bridge equation 不是“中间式 = 可删”；
- Final summary 不是“全文公式复制”；
- 关键 bridge 只在确有恢复价值时进入 summary。

## 12.3 §7.1 优化模型

明确：

- summary 是最终可计算模型 recap；
- required 时必须真正呈现；
- inline 时自然收束；
- not_applicable 时不制造形式块。

## 12.4 §7.2 非优化模型

继续按真实结构收束；补充 bridge relation 例型，如：

- 状态更新前的关键闭合关系；
- 概率分解中的关键条件关系；
- 网络权重到传播规则的桥接式；
- 几何量到最终判定条件的桥接式。

## 12.5 §8 模型求解

在进入 solver 前增加 preflight consumption check：

- summary 是否已闭合；
- solver 所需命题/性质是否已建立；
- algorithm presentation mode 是否已确定。

这不是新增标题，只是写作顺序 gate。

---

# 13. Model Paper Framework 修改计划

`templates/model/model_paper_framework.md` 是本轮很关键的项目事实层。

建议修改：

## 13.1 核心公式 Trace

从：

```text
Formula ID | 对应小问 | Source | Depends on | Derivation | Destination | 代码/证据锚点 | 状态
```

升级候选：

```text
Formula ID | 对应小问 | Role | Source | Depends on | Derivation | Destination | Summary Use | 代码/证据锚点 | 状态
```

若最终决定不持久化 `Summary Use`，则至少增加 `Role`。

## 13.2 当前写作选择

强化以下现有条目，不重复通用规则：

- 各问核心模型收束状态；
- 各问算法流程呈现状态；
- 命题/证明位置。

新增：

```text
各问 Writing Capability Preflight 状态
```

## 13.3 命题与证明规划

保留现有字段，不扩张成复杂 schema；必要时增加一个简单 activation state。

## 13.4 Algorithm Trace

保持现有结构，确保 presentation mode 是可直接消费状态。

---

# 14. Writing Runtime Contract 修改计划

这是本轮主要 runtime 文件。

## 14.1 在 question stage 前加入 preflight 子阶段

建议有两种架构。

### 方案 1：独立 stage

```text
question_capability_preflight
question_model_solution_result_validation
```

优点：执行顺序最清楚。

缺点：当前 `repeat_for_each_question` 语义需要设计 Qx preflight 与 Qx write 的成对关系。

### 方案 2：question stage 内部 preflight block

```yaml
- id: question_model_solution_result_validation
  repeat_for_each_question_in_template_order: true
  before_write_preflight:
    ...
```

优点：更自然地表达：

```text
Q1 preflight → Q1 write → gate
Q2 preflight → Q2 write → gate
```

### 推荐

优先采用 **方案 2**。

避免形成：

```text
先把 Q1/Q2/Q3 全预检
再统一写 Q1/Q2/Q3
```

因为跨问状态可能在前问写作后发生调整。

## 14.2 新 preflight gate

建议：

```text
Qx cannot enter write_now until:
- formula role state adjudicated
- summary mode adjudicated
- proposition state adjudicated
- algorithm presentation adjudicated
- required conditional resources resolved
```

简单问题允许这些状态为 `not_applicable / not_needed`，但必须是**明确裁决**，不能因为没有读取而“默认消失”。

---

# 15. Resolver / Runtime Projection 修改计划

`scripts/resolve_runtime.py` 当前主要输出 writing runtime 的序列和 fallback triggers。

本轮应避免把它改成复杂的项目语义推理器。

## 15.1 Resolver 的职责

只需要保证：

- CUMCM compact writing plan 暴露 preflight execution contract；
- `writing_runtime.authoring_sequence` 中能看到 preflight；
- conditional resources / fallback triggers 能被 consumer 读取；
- 不需要 resolver 自己判断某个具体命题是否成立。

## 15.2 如果需要项目状态驱动 helper

若 `resolve_runtime.py` 无法消费 project framework 的逐问写作状态，可以考虑新增小型 helper，例如：

```text
scripts/resolve_writing_capabilities.py
```

但只有在真正需要 machine-resolved dispatch 时再创建。

优先级：

1. 先尝试 declarative runtime + framework state；
2. 只有测试证明 declarative mapping 不足时再加 helper。

防止继续增加脚本数量。

---

# 16. AI Cleanup 修改计划

`ai_cleanup.md` 需要加入一条新的保护边界：

> Cleanup 不得因为“中间公式重复”“标题简化”而删除已经标记为 `key_bridge_relation` 的必要桥接公式。

同时：

- `final_model_relation` 不得被清理掉；
- `key_bridge_relation` 可以压缩解释，但不能让最终关系失去来源；
- `supporting_derivation` 可按必要性压缩；
- `routine_algebra` 优先删除。

另外继续保留：

- 不删除真实命题；
- 不删除必要证明；
- 不删除已裁决 stepwise/pseudocode；
- 不按标题数量机械合并复杂结构。

---

# 17. Review Delivery 修改计划

终审需要增加一个 **Capability Activation Review**，检查的不是“是否有更多内容”，而是：

1. 本问 summary mode 是否有实际落实；
2. required summary 是否存在并闭合；
3. key bridge equation 是否被错误压没；
4. planned/current proposition 是否真正进入正文或明确分流附录；
5. `pseudocode` 状态是否真正生成算法块；
6. `not_needed/not_applicable` 是否来自显式裁决，而不是遗漏；
7. Formula / Proposition / Algorithm / Result 的锚点是否闭合。

## Severity

不得新增“缺少命题 = Blocking”这种错误规则。

建议：

- 项目状态明确 `pseudocode`，正文完全没有算法块 → `review_required`，若影响可复现性再结合既有证据规则升级；
- summary `required`，却完全未呈现最终模型 → `review_required`；
- key bridge relation 缺失导致最终模型无法恢复来源 → `review_required`，若导致数学语义错误则按既有 Hard Rule；
- planned proposition 未出现 → `review_required`；
- 证明错误 / 把数值验证当严格证明 → 走现有 Hard 证据边界。

---

# 18. Output Contract 修改计划

建议增加 current integration pointer：

```yaml
core_model_summary_contract:
  core/writing_reasoning_contract.yaml#adaptive_core_model_summary
```

并明确：

```text
core_model_summary_policy_status = deprecated_v7_read_compatibility
```

只用于旧项目读取，不能替代 current pointer。

如果新增 formula role authority，则再增加：

```yaml
formula_role_contract:
  core/writing_reasoning_contract.yaml#...
```

但如果 Formula Role 直接是现有 Formula Trace authority 的子节点，则不必增加过多 named pointer。

---

# 19. Template / LaTeX 修改边界

## 19.1 CUMCM Template

模板只需要：

- 保留 optional summary slot / 注释；
- 不新增固定“公式汇总”小节；
- 不新增固定“命题”小节；
- 不新增固定“伪代码”小节。

## 19.2 Algorithm / Proposition environment

继续由 LaTeX Adapter / Pack 提供环境。

Preflight 只决定是否读取和是否需要呈现，不复制载体实现。

---

# 20. 建议新增测试

建议新增：

```text
tests/test_v870_question_writing_capability_preflight.py
```

以及 fixture：

```text
tests/fixtures/writing_capability_preflight_cases.yaml
```

## 20.1 Case A — 复杂优化模型要求 summary

输入：

- multiple variables；
- objective；
- multiple constraints；
- solver follows。

预期：

```text
summary = required
activation includes adaptive_core_model_summary
```

## 20.2 Case B — 简单解析关系 inline

输入：

- one final analytic relation。

预期：

```text
summary = inline
no forced subsection
```

## 20.3 Case C — 直接计算 not applicable

预期：

```text
summary = not_applicable
no generated summary block
```

## 20.4 Case D — Bridge equation preservation

输入：

```text
F1 key_bridge_relation
F2 final_model_relation
```

预期：

- F1 retained in derivation；
- F2 in summary；
- F1 not necessarily duplicated in summary。

## 20.5 Case E — Proposition planned auto-activation

框架：

```text
proposition_status = planned
```

预期：

```text
proposition_proof pack activated
```

不需要用户 prompt 中出现“命题”二字。

## 20.6 Case F — Proposition not assessed + monotonicity signal

预期：

- trigger semantic proposition review；
- 不自动创建 proposition。

## 20.7 Case G — Pseudocode auto-activation

框架：

```text
algorithm_presentation = pseudocode
```

预期：

```text
algorithm_flow pack activated
latex algorithm environment available
```

即使用户只说“写问题二”。

## 20.8 Case H — Stepwise auto-activation

预期：

- algorithm pack activated；
- 不强制 algorithm environment if prose stepwise suffices。

## 20.9 Case I — not_needed 不加载算法 Pack

验证 Compact Runtime 不膨胀。

## 20.10 Case J — stale proposition

预期：

- 不允许作为 current 写入；
- preflight finding = stale / review_required。

## 20.11 Case K — Missing state 不静默默认

框架中 summary/proposition/algorithm state 缺失。

预期：

- preflight 标记 `needs_adjudication`；
- 不直接当 not_applicable/not_needed。

## 20.12 Case L — User explicitly asks for proof

确保旧行为仍兼容：

- 用户显式请求仍能触发；
- 新机制只是增加自动激活，不削弱显式触发。

## 20.13 Case M — Full authority is not eagerly preloaded

保证纯 CUMCM LaTeX 仍然 Compact：

```text
normal question without proposition/algorithm dispute
→ no full Authority preload
```

## 20.14 Case N — Cross-question inheritance

Q2 继承 Q1 模型，无新核心关系：

- summary 可为 not_applicable / inline；
- 不重复 Q1 全部模型；
- 若 Q2 新增关键 bridge relation，则保留增量关系。

---

# 21. 需要回归保护的既有测试

至少重新检查：

- `tests/test_v801_chapter_capability_preservation.py`
- `tests/test_v803_core_model_summary_vocabulary.py`
- `tests/test_v743_writing_structure_style.py`
- `tests/test_v760_writing_governance.py`
- `tests/test_v750_writing_reasoning_architecture.py`
- `tests/test_content_packs.py`
- `tests/test_schemas.py`
- v8.5 Author Reasoning Voice tests
- v8.6 Model Construction Rationale tests
- v8.6.1 Active Consistency tests

关键回归目标：

```text
新增自动激活
≠
恢复全量 preload
```

```text
增加 bridge formula preservation
≠
增加公式堆砌
```

```text
命题自动发现
≠
命题强制化
```

```text
Algorithm auto-activation
≠
所有 solver 都伪代码化
```

---

# 22. 机器审计边界

机器可以检查：

- preflight block 是否存在；
- project state / framework state 是否有合法枚举；
- `planned/current proposition → pack activation` 是否发生；
- `pseudocode → algorithm pack activation` 是否发生；
- `summary required → summary capability consumed` 是否发生；
- Formula Role enum 是否合法；
- root/package/version pointer 是否一致；
- generated metadata 是否 fresh。

机器不可以判断：

- 某公式数学上是不是关键 bridge；
- 某证明是否真正正确，仅靠关键词；
- 某题是否“应该”有命题；
- 某伪代码是否数学上最优；
- 某模型 summary 是否“写得好”仅靠公式数量。

这些继续是 semantic review / human review。

---

# 23. 性能与读取预算

本轮必须保持当前 Compact Runtime 的设计初衷。

### 禁止

```text
开篇 preload：
Reasoning Authority
+ Proposition Pack
+ Algorithm Pack
+ 所有 writing examples
```

### 推荐

```text
Template inspection
↓
当前 Qx Preflight 只读状态
↓
根据状态加载 0~N 个必要资源
↓
写 Qx
↓
gate
↓
下一问
```

理想结果：

- 简单题读取成本几乎不增加；
- 复杂题增加一小段状态读取，但不漏高级能力；
- proposition / pseudocode Pack 只在真实需要时加载。

---

# 24. 文件级修改矩阵（候选）

## 核心必须修改

1. `core/writing_runtime_contract.yaml`
   - 新增 per-question capability preflight；
   - 增加 Core Model Summary 显式 capability；
   - 明确 current question evidence bundle composition；
   - 条件激活规则。

2. `core/writing_reasoning_contract.yaml`
   - Formula Role Taxonomy；
   - Core Model Summary 对 bridge relation 的使用边界；
   - 如需，补充 preflight semantic delegation pointer。

3. `modules/05_writing/paper_writing_protocol.md`
   - 每问写前必须已有 capability adjudication；
   - Formula Roles；
   - summary / proposition / algorithm 的写作消费规则。

4. `templates/model/model_paper_framework.md`
   - Formula Role 字段；
   - 每问 preflight 状态；
   - 保持项目事实层，不复制手册。

5. `core/output_contract.yaml`
   - current Core Model Summary pointer；
   - 必要 integration pointer。

6. `modules/05_writing/ai_cleanup.md`
   - bridge formula preservation；
   - 不删除已激活 proposition / algorithm。

7. `modules/06_review_delivery.md`
   - Capability Activation Review。

## 可能修改

8. `scripts/resolve_runtime.py`
   - 仅暴露 preflight sequence / activation surface；
   - 不承担数学语义。

9. `templates/latex/cumcm/hsk/template_manifest.yaml`
   - 仅在需要增加 pointer 时修改；
   - 不改变固定一级骨架。

10. `modules/05_writing/latex.md`
    - 若需要补充 activated capability 与环境选择边界。

## 新增测试

11. `tests/test_v870_question_writing_capability_preflight.py`
12. `tests/fixtures/writing_capability_preflight_cases.yaml`

## 文档

13. `docs/v870_question_writing_capability_preflight_plan.md`
14. `docs/v870_question_writing_capability_preflight_evaluation.md`（实施后）

## 发布时才修改

- `core/bootstrap.yaml`
- root `SKILL.md`
- package `skills/mathmodel-skill/SKILL.md`
- `.codex-plugin/plugin.json`
- `README.md`
- `CHANGELOG.md`
- `core/hsk_core_policy.md`（仅若 header/version carrier 需要）
- 其他 release carriers
- generated `SKILL_FILE_INDEX.md`
- generated `MANIFEST.sha256`

---

# 25. 明确冻结的无关范围

除非测试证明存在直接依赖，本轮默认不改：

- 数据预处理语义；
- numerical verification contract；
- user execution contract；
- workbook schema；
- Python code quality；
- MATLAB plotting；
- draw.io mechanism diagrams；
- Figure Evidence contract；
- 03A/03B；
- Primary Quality Specification；
- result analysis；
- project_state core schema；
- Model Approval；
- official competition rule verification；
- submission package semantics。

---

# 26. 实施阶段

## Phase 0 — Baseline Freeze

- fresh read current `main`；
- 记录 baseline commit；
- 读取当前相关 tests；
- 确认 v8.6.1 全绿基线；
- 不先升级版本。

## Phase 1 — Runtime Preflight Contract

只实现：

- preflight structure；
- evidence bundle composition；
- activation semantics。

先不改 Formula Role。

目的：先验证“状态 → 激活”主链。

## Phase 2 — Formula Role Taxonomy

- reasoning contract；
- project framework；
- protocol；
- cleanup；
- review。

## Phase 3 — Core Model Summary Current Integration

- runtime capability；
- output contract pointer；
- summary behavior regression。

## Phase 4 — Proposition / Algorithm Auto-Activation

- planned/current proposition；
- stepwise/pseudocode algorithm；
- stale handling；
- explicit user request compatibility。

## Phase 5 — Behavior-Level Tests

优先固定：

- 不提“命题”也会根据 state 激活；
- 不提“伪代码”也会根据 mode 激活；
- 不提“模型汇总”也会根据 summary state 激活。

## Phase 6 — Fixed Writing Trials

至少做 6 类固定题型试写：

1. 简单解析题；
2. 复杂优化题；
3. 几何判据 + bridge equations；
4. 单调性 / 可行性证明题；
5. 黑箱优化 + pseudocode；
6. 跨问继承模型。

观察是否出现：

- 过度命题化；
- 过度伪代码化；
- 公式重复堆砌；
- summary 误触发；
- Pack preload 膨胀。

## Phase 7 — Regression Sweep

跑现有 Writing / Runtime / Schema / Template tests。

## Phase 8 — Evaluation

生成：

```text
docs/v870_question_writing_capability_preflight_evaluation.md
```

记录：

- fixed cases；
- activation coverage；
- preload budget；
- regressions；
- known limitations。

## Phase 9 — Release Sync

只有前述全部通过后：

- 8.6.1 → 8.7.0；
- carriers sync；
- generated metadata refresh；
- final full CI。

---

# 27. Acceptance Criteria

v8.7.0 只有同时满足以下条件才算完成。

## Runtime

- [ ] 每问写作前存在 mandatory capability preflight；
- [ ] preflight 与当前 Qx 成对执行；
- [ ] 不在所有问题前一次性全量 preload；
- [ ] Core Model Summary 作为 current runtime capability 可见；
- [ ] proposition / algorithm 能由项目状态自动激活。

## Formula

- [ ] Final Model Relation 与 Key Bridge Relation 明确区分；
- [ ] bridge equation 不因“不是最终模型”而自动删除；
- [ ] routine algebra 仍保持压缩；
- [ ] summary 不退化为公式大全。

## Core Model Summary

- [ ] required → 真正呈现；
- [ ] inline → 不机械单列标题；
- [ ] not_applicable → 不制造空块；
- [ ] summary 不替代变量/目标/约束/推导解释。

## Proposition / Proof

- [ ] planned/current → 自动读 Pack；
- [ ] candidate → 只触发审查，不自动创建命题；
- [ ] stale → 不写成 current；
- [ ] 数值实验不升级为数学证明。

## Algorithm

- [ ] pseudocode → 自动激活算法 Pack；
- [ ] stepwise → 自动激活；
- [ ] not_needed → 不加载；
- [ ] 论文算法与真实 Algorithm Trace / Python anchor 一致。

## Compatibility

- [ ] v8.5 Author Reasoning Voice 不回归；
- [ ] v8.6 Model Construction Rationale 不回归；
- [ ] v8.6.1 consistency fixes 不回归；
- [ ] CUMCM Template-First 不回归；
- [ ] Model Approval 不变；
- [ ] user execution 不变；
- [ ] workbook / numerical / figure / LaTeX delivery boundaries 不变。

---

# 28. Stop Conditions

实施过程中出现以下任意情况应立即停止并重新评估，而不是继续“为了通过测试”扩张范围：

1. 为自动激活而不得不全量 preload 所有 writing Pack；
2. 需要改变 Model Approval 才能实现 preflight；
3. 需要改变模型 semantic hash 才能记录纯写作 capability state；
4. Formula Role 导致大量旧项目无法读取；
5. proposition auto-activation 变成“检测到单调性关键词就自动写命题”；
6. pseudocode auto-activation 变成“任何 solver 都强制算法块”；
7. required summary 被错误理解为固定独立小节；
8. Machine Audit 开始判断数学证明真假或公式重要性；
9. 为本轮写作增强修改 numerical / workbook / user execution 等无关 Authority；
10. 现有 v8.6.1 主线测试出现行为性回归且无法在本 scope 内解释。

---

# 29. 风险与缓解

## R1. Preflight 变成新 Authority

缓解：

- 所有语义规则继续 delegate 到 Reasoning Contract；
- runtime 只做 dispatch。

## R2. 项目框架越来越胖

缓解：

- 只存项目状态；
- 不抄通用规则；
- Formula Role 只存枚举。

## R3. 过度触发命题

缓解：

- `candidate` 只触发 review；
- 不自动创建命题；
- 保留 0--4 阅读预算且不是 hard quota。

## R4. 过度触发伪代码

缓解：

- mode 必须由真实 Algorithm Trace / 项目选择驱动；
- `not_needed` 是合法且常见状态。

## R5. 公式越写越多

缓解：

- 四级 role 明确支持压缩；
- summary 只收 Final + 少量必要 Bridge。

## R6. Compact Runtime 失去意义

缓解：

- preflight 先读状态；
- Pack 只按 activation 加载；
- 增加测试确保 full Authority 不被普通问题 eager preload。

---

# 30. 建议的 release note

如果最终实施完成，v8.7.0 release note 可概括为：

> Added **Per-Question Writing Capability Preflight** so each question automatically checks and activates Core Model Summary, Formula roles, Proposition/Proof, and Algorithm Trace/Pseudocode from current project state before writing. Introduced Final / Bridge / Supporting formula roles to preserve mathematically necessary intermediate relations without turning summaries into formula dumps. Kept Compact Runtime conditional loading, simple-problem anti-bloat, Model Approval, numerical/workbook, figure, execution and LaTeX delivery boundaries unchanged.

---

# 31. 最终设计原则

本轮最重要的原则不是“写得更多”，而是：

```text
需要的能力必须主动出现；
不需要的能力必须保持关闭。
```

对每个问题，writer 应在动笔前能够回答：

1. 哪些公式是真正 Final Model Relations？
2. 哪些虽然不是最终式，但属于不可丢的 Key Bridge Relations？
3. 本问是否需要核心模型汇总？为什么？
4. 是否已有 proposition plan？是否需要读取证明 Pack？
5. Algorithm Trace 是 not_needed、stepwise 还是 pseudocode？
6. solver 所需的数学性质是否已经建立？
7. 结果和验证证据是否足以支撑当前 claim？
8. 需要哪些 Pack / Authority，现在应该加载什么，而不是“用户提醒后再想起来”？

只有这 8 个问题被预检闭合后，才进入当前问题正文。

这就是 v8.7.0 的核心目标：

> **从 capability preservation 升级到 capability discovery + state-driven activation，同时保留 Compact Runtime。**

---

# 32. 审批后第一步

如果本计划获批，实施时第一步不是立刻改 `writing_reasoning_contract.yaml`，而是：

1. fresh fetch 当前 `main`；
2. 对照本计划确认 scope 未漂移；
3. 先只实现 `writing_runtime_contract.yaml` 中的 preflight skeleton 与对应 tests；
4. 用三个最小 fixture 验证：
   - `summary=required`；
   - `proposition=planned`；
   - `algorithm=pseudocode`；
5. 确认“状态能自动激活”后，再进入 Formula Role 与 Protocol 层。

这样能避免一次性同时改 Authority、Runtime、Framework、Protocol 后难以判断真正的触发问题来自哪里。
