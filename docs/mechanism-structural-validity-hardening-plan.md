# v7.17 机理/几何结构有效性强化计划（MSV-01）

> 状态：**PLANNING ONLY / 仅作为实施导航，不是运行时权威规则**  
> 适用仓库：`Vexushi1/mathmodel-skill`  
> 基线 Skill：`7.16.0`  
> 基线 `main`：`afbbe58979f87be246896aa952b434c36f15b837`  
> 实施分支：`upgrade/v7.17-mechanism-structural-validity`  
> 目标版本：`7.17.0`  
> 计划代号：`MSV-01`（Mechanism Structural Validity）  
> 核心目标：在**不新增独立 Skill、不新增运行 Gate、不膨胀核心 Schema**的前提下，把机理/几何/连续事件/混合优化题中最容易出错的“物理判据—事件边界—结构降维—Solver 适配—多资源组合—原模型回算”链条补强到现有 Module 02 + Task Pack + Project Memory 体系中。

---

## 0. 上下文缩短后的恢复协议

本文件首先承担**实施记忆**作用。后续若聊天上下文缩短、Agent 切换、对本次修改细节记忆不足，**不得根据旧聊天印象继续写仓库**，必须按以下顺序恢复：

1. 从最新 `main` 重新读取 `core/bootstrap.yaml`；
2. 从最新 `main` 重新读取 `SKILL_CHANGE_GOVERNANCE.md`；
3. 读取本文件 `docs/mechanism-structural-validity-hardening-plan.md`；
4. 读取当前 PR 的 description、changed files、review comments、CI 状态；
5. 确认 `main` 是否前移，是否出现与本 PR 重叠的新 PR；
6. 重新读取本次真正要修改的当前权威文件，而不是相信本计划里记录的旧 SHA；
7. 从本文件最后的“实施进度记录”恢复已经完成和未完成的 Phase；
8. 若本文件与最新 `main` 权威规则冲突，以最新 `main` 权威规则为准，并先更新本计划的实施假设再继续。

**本文件不是第二套 runtime authority。** 最终生效规则必须写入各自的权威 Module / Pack / Contract / Template；本文件只记录为什么改、改什么、什么不能改、怎样验收和怎样继续。

---

## 1. 修改简报

```text
修改主题：v7.17 机理/几何结构有效性强化（Mechanism Structural Validity Hardening）
当前版本：7.16.0
目标版本：7.17.0
变更等级：minor（新增向后兼容的建模设计能力，不改变旧项目目录/Schema/CLI）
直接目标：
  1. 建立精确物理/几何成功判据闭合要求；
  2. 建立连续时间事件拓扑与临界边界求解协议；
  3. 区分 exact / proven_sufficient / heuristic 三类结构缩域来源；
  4. 增加 Solver Applicability / Objective Landscape 的条件式适配诊断；
  5. 显式记录多资源组合算子与量词顺序，防止错误相加/错误解耦；
  6. 要求 surrogate / decomposition 最终方案回到原始耦合模型复算；
  7. 消除 Task Pack 中“主求解验证”与“accepted 后深化分析”措辞歧义；
  8. 让上述语义能够保存在现有 模型论文框架.md，而不新建项目级报告。
明确不做：
  - 不新增 mechanism-structure-reducer Skill；
  - 不新增 G1.5 或其他新运行 Gate；
  - 第一轮不修改 core/task_taxonomy.yaml；
  - 第一轮不修改 core/numerical_verification_contract.yaml；
  - 不新增新的项目目录、工作簿、YAML 报告或运行日志；
  - 不把任何单一赛题的角度、速度、范围、常数或经验结论写成通用规则；
  - 不要求助手在审批前运行题目专属求解代码；
  - 不把参数敏感性、多算法稳定性、压力场景提前塞回 03A；
  - 不借本次 PR 重构路由、工作簿、LaTeX、绘图或提交包体系。
权威事实源：
  - core/bootstrap.yaml
  - SKILL_CHANGE_GOVERNANCE.md
  - modules/02_model_design.md
  - packs/task/mechanism.md
  - packs/task/optimization.md
  - core/model_approval_contract.yaml
  - core/numerical_verification_contract.yaml
  - modules/03_solve_validate.md
  - modules/03_result_analysis.md
  - packs/artifact/algorithm_flow.md
  - templates/model/model_paper_framework.md
  - tests/** 与现有版本/生成文件治理
预计修改文件：
  - modules/02_model_design.md
  - packs/task/mechanism.md
  - packs/task/optimization.md
  - templates/model/model_paper_framework.md
  - packs/artifact/algorithm_flow.md（仅在确实需要最小算法呈现补充时）
  - tests/test_v717_mechanism_structural_validity.py（建议新增）
  - CHANGELOG.md
  - 当前版本一致性要求涉及的版本载体（实施阶段按最新 main 再确认）
  - 由 scripts/generate_indexes.py 生成的索引/MANIFEST（只通过生成器更新）
禁止触碰文件：
  - legacy/**
  - core/task_taxonomy.yaml（第一轮冻结）
  - core/numerical_verification_contract.yaml（第一轮冻结）
  - core/workbook_schema.yaml
  - core/project_state.schema.yaml
  - core/workflow_router.yaml
  - core/module_manifest.yaml
  - Python/MATLAB/LaTeX 题目模板（除非实施中出现被现有测试证明的真实闭环缺口，并需单独评估是否拆 PR）
兼容性要求：
  - 旧项目继续可读、可运行；
  - 不改变问题目录五文件布局；
  - 不改变 full_fidelity 用户执行所有权；
  - 不改变 03A / 03B 生命周期；
  - 不改变 current Problem Contract / Model Challenge / Human Approval 语义；
  - 不改变现有 task taxonomy 字段；
  - 不要求历史项目回填新字段才能只读审查。
迁移要求：
  - 无 Schema 迁移；
  - 无 CLI 迁移；
  - 无工作簿迁移；
  - 新建项目或重新进入 model_design 的项目采用新规则；
  - 历史 locked model 在只读复核时不因 v7.17 自动 stale；若语义重新设计再按当前治理进入新规则。
验收测试：
  - python scripts/lint_skill.py
  - python -m unittest discover -s tests
  - python scripts/generate_indexes.py --check
  - 新增 v7.17 结构有效性语义回归测试
  - 代表性 mechanism / optimization runtime resolver smoke
  - 版本一致性测试
  - 检查 generated metadata 由生成器而非手改更新
回滚方式：
  - 回滚本 PR 的功能提交；
  - 由于不改 Schema/CLI/目录，回滚不需要项目迁移；
  - 若某条新规则被证明过度约束，只回退相应 Module/Pack/Template 语义，不保留半套字段。
```

---

## 2. 当前 v7.16.0 已经解决的问题

本次升级**不是重新设计整个 Skill**。v7.16.0 已经具备以下高质量基础，必须保留：

```text
Problem Contract
→ 数据/对象/约束语义冻结
→ 路线 A/B 比较
→ 结构化简优先于高级算法
→ 题面—数学—代码—输出语义闭环
→ Formula Trace
→ Complexity Sanity
→ Model Reviewer
→ Devil's Advocate
→ Human Model Approval（绑定 semantic revision/hash）
→ Primary Quality Specification
→ 03A 主求解与内在数值有效性
→ accepted workbook
→ 03B 深化分析
→ Figure / Writing / Review / Submission
```

其中已经存在并且本次不得破坏的关键思想：

- 模型和 Solver 分离；
- Validator / baseline / alternative 有独立角色；
- 高维问题先检查解析关系、单调性、凸性、对称性、消元、降维、分解；
- Complexity Sanity 已检查异常降维、错误解耦、动态静态化、多主体独立化、约束失活；
- Devil's Advocate 已检查 hidden coupling、invalid decoupling、local-to-global overclaim；
- 03A 只负责当前 locked model 下本次计算是否可接受；
- 03B 独占参数敏感性、压力场景、替代算法/结构、多 seed / 多初值结论稳定性；
- 机器检查锚点/字段/证据闭环，但不假装通过正则判断数学证明正确性。

因此 v7.17 的目标不是“再加一个大模块”，而是补足下列**中间结构层**：

```text
物理对象
→ 精确成功/失败判据
→ 连续事件结构
→ 可证明/启发式结构缩减
→ 目标函数/可行域的 Solver 适配特征
→ 主 Solver
→ 多资源组合与分解
→ 原始模型复核
```

---

## 3. 为什么需要本次升级

机理/几何/连续优化题最危险的错误往往不发生在“Solver 能不能跑”，而发生在 Solver 之前：

1. **判据对象错了**：把有限线段条件写成无限直线距离，把射线方向遗漏，把“覆盖整个对象”错写成“覆盖一个代表点”；
2. **量词顺序错了**：`对所有目标点存在一个资源` 与 `存在一个资源覆盖所有目标点` 不是同一问题；
3. **事件拓扑错了**：0→1→0 的事件状态被当成全区间单调，直接二分造成错误边界；
4. **缩域依据不清**：物理直觉给出的候选角度/区域被写成“最优解一定在此”，却没有证明或弃置域检查；
5. **Solver 家族不适配**：目标函数大面积为零、可行域极稀疏、非光滑或分段切换，却只因“连续变量”就使用局部梯度 NLP；
6. **多资源作用方式错了**：把区间并集写成时长相加，把联合覆盖写成独立覆盖，把合作关系错误解耦；
7. **分解模型替代原模型**：先构造 pairwise capability / surrogate 做分配后，直接把 surrogate 目标值当最终原问题目标值；
8. **验证阶段混淆**：Task Pack 中“参数敏感性”等措辞容易被误读成 03A 主质量门要求，与 v7.14 之后的 03A/03B Authority 产生阅读歧义。

这些问题都具有跨赛题复用价值，尤其适用于：

- 遮挡、可见性、覆盖、碰撞、追踪、投放、拦截；
- 轨迹—几何—时序联合优化；
- 多资源协同覆盖、时空调度；
- 连续时间事件定位；
- 几何判据嵌套在黑箱优化目标内部；
- 高维非凸但存在物理结构降维的 A 类机理题。

---

## 4. 总体架构原则

### 4.1 不新增独立 Skill

不新增 `mechanism-structure-reducer`、`geometry-validator` 等独立 Skill。原因：

- `modules/02_model_design.md` 已经是模型设计和结构化简 Authority；
- `packs/task/mechanism.md` 已经是机理/物理题专属准入与验证 Pack；
- 再增加独立模块会形成重复 Authority 和额外路由负担。

### 4.2 不新增新的运行 Gate

不新增 `G1.5`、`Mechanism Gate` 等。现有链条已经足够：

```text
Problem Contract frozen
→ semantic closure
→ Complexity Sanity
→ Independent Model Challenge
→ Human Model Approval
```

本次规则应作为上述阶段**通过条件的细化内容**，而不是新建生命周期状态。

### 4.3 第一轮不修改 taxonomy / numerical verification Schema

第一轮不新增：

```text
requires_equivalent_predicate_check
requires_event_topology_check
requires_objective_landscape_probe
```

等新 capability。

理由：这些规则目前更适合作为 mechanism/optimization 的条件式设计约束；先通过真实 A 题验证复用频率。如果后续 2--3 个项目证明这些能力需要被机器路由/工作簿协议单独识别，再单独提出 taxonomy minor upgrade。

### 4.4 不新增项目级报告

不生成：

- `MECHANISM_REVIEW.md`
- `PREDICATE_AUDIT.md`
- `SOLVER_LANDSCAPE_REPORT.md`
- `REDUCTION_AUDIT.yaml`

本题真实选择写入现有 `模型论文框架.md`；数值证据仍写入现有主/深化工作簿适用工作表。

### 4.5 机器不判断数学证明正确性

机器测试可以检查：

- 是否声明 exact / proven_sufficient / heuristic；
- 是否存在 bracket / tolerance / update rule 字段要求；
- 是否要求 original-model reevaluation；
- 是否明确 03A/03B ownership。

机器不得声称：

- 已证明某个圆周足够代表整个曲面；
- 已证明目标函数单调；
- 已证明某个缩域包含全局最优；
- 两个几何判据数学等价。

数学正确性仍由推导、命题、独立数值复核和人工审查承担。

---

## 5. v7.17 目标语义总链

实施后，机理/几何/混合优化小问在适用时应形成：

```text
Problem Contract
→ Object / reference frame closure
→ Mechanism Predicate Closure
→ Event Topology / Boundary Protocol（若存在连续事件）
→ Analytic / structural reduction
→ Reduction provenance: exact / proven_sufficient / heuristic
→ Solver Applicability Assessment（若优化目标有稀疏/平台/非光滑风险）
→ Multi-resource composition semantics（若多资源/多主体）
→ Model / Solver / Validator roles
→ Original-model reevaluation plan（若 surrogate / decomposition）
→ Complexity Sanity
→ Model Challenge
→ Human Approval
→ 03A primary computation
→ accepted
→ 03B claim-stability / sensitivity / stress analysis
```

注意：上述箭头表示**逻辑闭合顺序**，不意味着新增 runtime module 或新增项目文件。

---

# 6. P0-A：Mechanism Predicate Closure —— 精确物理/几何判据闭合

## 6.1 目标

在机理/几何题中，除状态方程和运动方程外，必须明确：

> **满足什么精确数学条件，才算题目中的事件/状态/成功条件成立？**

典型对象：

- 遮挡 / 可见；
- 碰撞 / 不碰撞；
- 覆盖 / 未覆盖；
- 进入 / 离开；
- 到达 / 未到达；
- 相交 / 相切 / 分离；
- 满足安全距离；
- 位于有效区域；
- 多资源联合满足约束。

## 6.2 条件式启用

仅当当前题目存在下列一种或多种结构时强制：

```text
几何可见性
点-线/射线/线段关系
点-曲线/曲面/实体关系
区域覆盖
碰撞/交叉
阈值进入/退出
多主体/多资源联合判定
```

纯 ODE 参数估计、普通守恒模型且没有离散事件判据时，不为了形式添加该块。

## 6.3 建议的内部字段

不新建 Schema；在 Module 02 当前模型语义和 `模型论文框架.md` 中按需记录：

```text
Predicate ID
Physical event / state
Object domain
Reference frame
Exact mathematical predicate
Quantifier order
Geometry semantics
Direction / segment / ray semantics
Boundary inclusivity
Exact / approximate status
Formula / Proposition anchor
Python predicate anchor（求解后）
Equivalent check / independent check（若适用）
Failure mode if mis-specified
Status: closed / gap / stale
```

## 6.4 必须区分的几何语义

### 无限直线、射线、有限线段不得混写

对点 `P` 到由 `A,B` 决定的几何对象，必须明确研究对象究竟是：

```text
line    : A + λ(B-A), λ ∈ R
ray     : A + λ(B-A), λ ≥ 0
segment : A + λ(B-A), λ ∈ [0,1]
```

仅有“到直线距离小于半径”不自动保证有限线段或射线方向条件成立。

### 点、边界、表面、实体不得混写

若题目要求整体对象被覆盖/可见/安全，必须说明计算域是：

```text
single representative point
boundary
visible / active boundary
surface
solid region
finite critical set after proof
```

只有存在结构证明时，才能把连续对象约化成边界或有限临界点集合。

## 6.5 量词顺序必须显式

多资源覆盖类问题必须明确：

```text
∀ point ∃ resource
∃ resource ∀ point
∀ resource ∀ point
∃ point ∃ resource
```

例如：

```math
\forall x\in\Omega,\ \exists i\in\mathcal I:\ C_i(x,t)=1
```

与：

```math
\exists i\in\mathcal I,\ \forall x\in\Omega:\ C_i(x,t)=1
```

语义完全不同。

## 6.6 等价/独立判据复核

当以下风险存在时，应**优先**准备第二种独立判据或等价数值检查：

- 方向性容易遗漏；
- 有限线段被无限直线替代；
- 投影参数/交点参数决定可行性；
- 复杂几何距离公式容易写错；
- 判据直接决定优化目标的大面积 0/1 跳变。

可选方式：

```text
distance formulation ↔ intersection parameter formulation
projection formulation ↔ angle/cone formulation
analytic predicate ↔ independent geometric construction
closed-form critical set ↔ dense local verification sample
```

此处的“independent check”不要求成为新的通用 capability；它作为本题 Validator / deterministic unit check / proposition numeric check 的一种实现。

## 6.7 通过标准

`Mechanism Predicate Closure` 通过至少需要：

- 研究对象定义域无歧义；
- 几何对象类型明确；
- 量词顺序明确；
- 方向/有限区间/边界包含关系明确；
- exact / approximate 状态明确；
- 若使用近似，近似误差和失效条件有说明；
- 关键判据有 Formula/Proposition 来源；
- 不能把“代码里这样算”作为数学来源。

若判据未闭合，`semantic_closure_status` 不应通过。

---

# 7. P0-B：Event Topology & Boundary Protocol —— 连续时间事件结构与临界边界协议

## 7.1 目标

连续时间题不应只说“求开始时间和结束时间”或“使用二分法”。必须先回答：

```text
事件在哪些时间段成立？
成立集合是一个区间还是多个区间？
边界是怎样定义的？
当前 root finder 在哪个局部区间满足使用条件？
```

## 7.2 事件函数与真假集合

建议定义：

```math
g(t)\le 0 \iff \text{event is active}
```

并记录：

```math
\mathcal T=\{t\in[t_0,t_1]:g(t)\le0\}.
```

不得默认：

```math
\mathcal T=[T_s,T_e]
```

若实际可能出现多次进入/退出，则应允许：

```math
\mathcal T=\bigcup_{k=1}^{K}[T_{s,k},T_{e,k}].
```

## 7.3 Event Topology 字段

```text
Event ID
Event function / predicate
Search horizon
Expected topology: monotone / 0→1→0 / multi-interval / unknown
Topology basis: proof / mechanism argument / coarse detection / assumption
Entry boundary definition
Exit boundary definition
Candidate brackets
Local monotonicity / sign-change basis
Left/right update rule
Tolerance
Stopping criterion
Multiple-root handling
Fallback when topology assumption fails
Formula / Algorithm anchor
```

## 7.4 二分法准入

“使用二分法”不能独立构成算法闭合。

进入 bisection 前至少必须知道：

```text
bracket
boundary function
which root is being searched
sign / monotonic structure on that bracket
left/right update rule
tolerance
stop rule
```

如果全局状态为：

```text
0 → 1 → 0
```

则必须先定位进入/退出的局部区间，再分别求边界；不能把整个时间域当作单调区间。

## 7.5 Newton / monotone search 同理

Newton、secant、monotone search、ternary search 等都必须记录各自所依赖的结构条件：

- 可导性；
- 初值域；
- 单峰/单调性；
- 分母/导数不退化；
- 越界处理；
- fallback。

不允许因为“算法常用”而省略本题条件。

## 7.6 论文呈现

若事件定位只是简单单次求根，可保持 `algorithm_presentation=not_needed`，在公式和短正文说明 bracket/tolerance 即可。

若包含：

- 粗定位 → 局部精修；
- 多区间扫描；
- 分支更新；
- 状态切换；
- fallback；

则可使用 `stepwise/pseudocode`，并让 Algorithm Trace 连接 Event ID / Formula / Proposition。

---

# 8. P0-C：Reduction Provenance —— 结构缩减来源分级

## 8.1 目标

当前 Skill 已要求“先结构化简，再选算法”。v7.17 进一步要求说明：

> 当前缩域/降维究竟是数学等价、充分性证明，还是启发式加速？

## 8.2 三种状态

### `exact`

严格等价变换、解析消元、变量替换、对称性等价、无损状态压缩等：

```math
\Omega_{red}\equiv\Omega_{full}
```

或完整模型与缩减模型之间存在可逆/等价关系。

### `proven_sufficient`

缩减空间并非逐点等价，但已证明最优解/可行关键点必落在缩减域：

```math
x^*\in\Omega_{red}\subseteq\Omega_{full}.
```

需要 Proposition / derivation anchor。

### `heuristic`

依据物理直觉、经验方向、已有结果、代表性区域或粗搜索判断缩小范围，但没有严格证明。

此时：

- Model 的原始定义域仍应保留 `\Omega_full`；
- reduced domain 属于 Solver strategy，不应偷换成数学模型本体；
- Claim Strength 不得自动升级为 PROVEN/global optimum；
- 应设计针对弃置域的 validator / coarse audit 或明确保留 residual warning。

## 8.3 每个缩减项建议记录

```text
Reduction ID
Original domain / dimension
Reduced domain / dimension
Transformation / reduction
Status: exact / proven_sufficient / heuristic
Basis
Formula / Proposition anchor
Discarded region
Validator for discarded region（heuristic 时）
Impact on claim strength
Failure / stale trigger
```

## 8.4 heuristic 缩域的弃置域检查

不规定固定方法，但可根据问题选用：

```text
coarse grid
Latin Hypercube
Sobol / low-discrepancy sample
random feasible sample
boundary scan
problem-specific extreme-point probe
```

检查目标不是“证明全局最优”，而是回答：

> 在声明的检查范围内，是否发现弃置域存在足以推翻当前主结论的候选？

输出措辞必须与证据一致：

```text
允许：在所检查的 full-domain coarse audit 中未发现更优候选
禁止：因此证明当前结果为全局最优
```

## 8.5 与 03A/03B 的边界

若 heuristic reduction 本身是**当前 Solver 的组成部分**，且弃置域 audit 使用同一输入、同一模型、同一场景，仅作为当前 Solver/Validator 的预定义检查，则可在 03A 同一次主计算中产生 evidence；它不是参数敏感性或 alternative-world analysis。

若检查需要：

- 改模型结构；
- 改现实参数/场景；
- 改主结论适用边界；
- 比较替代算法的稳定性；

则属于 03B。

本次升级不修改 `core/numerical_verification_contract.yaml`；是否成为 blocking PQS 仍由当前已有 capability / locked model 的数值有效性需求决定，不能借本规则偷偷新增 universal quality gate。

---

# 9. P0-D：Solver Applicability / Objective Landscape Assessment

## 9.1 目标

避免以下错误推理：

```text
连续变量 → NLP
非线性 → GA/DE
变量多 → 元启发式
有梯度 → 局部梯度法一定适合
```

Solver 选择应同时考虑：

- 数学类型；
- 可行域结构；
- 目标函数是否平滑；
- 正目标/有效区域是否稀疏；
- 是否存在大面积平台；
- 是否有跳变/事件切换；
- 单次评价成本；
- 维数；
- 是否有可用解析结构。

## 9.2 两层评估，避免破坏 Human Approval 边界

### Layer A：设计期结构评估（审批前）

不运行题目专属正式代码，仅从已建立数学模型判断：

```text
continuity
piecewise / discontinuous structure
differentiability
indicator / max / min / abs / event switching
known plateaus
feasible-region sparsity risk
multi-modality risk
single-evaluation cost expectation
```

该层必须在 Model Challenge 前完成，并用于 Solver family justification。

### Layer B：条件式 empirical probe（审批后、仅在必要时）

若主 Solver 选择高度依赖“有效域是否稀疏/平台是否严重”，可以把小预算、预定义的 landscape probe 作为当前 Solver 初始化/Validator 的一部分，由用户 full_fidelity 运行。

不得：

- 在审批前由助手偷偷运行正式题目代码；
- 根据 probe 结果 post-hoc 改阈值让某 Solver 看起来合理；
- 把小预算 probe 当成正式主结果。

## 9.3 可选诊断量

不设全局硬阈值，只提供可解释指标：

### 有限评价率

```math
\rho_{finite}=\frac{\#\{x:f(x)\in\mathbb R\}}{N}.
```

### 可行比例

```math
\rho_f=\frac{\#\{x:x\in\Omega_{feasible}\}}{N}.
```

### 非退化目标比例

```math
\rho_+=\frac{\#\{x:f(x)>f_{base}+\varepsilon\}}{N}.
```

### 平台质量

可用最常见目标邻域占比或目标唯一值/分位数结构描述，不规定唯一公式。

### 局部有限差分活跃率

```math
\rho_g=\frac{\#\{x:\|\nabla_h f(x)\|>\varepsilon_g\}}{N}.
```

### 其他

```text
objective quantiles
distinct-objective ratio
jump / nonsmooth evidence
active-constraint density
evaluation time per point
```

## 9.4 Solver 决策规则

不设置“`rho+ < 0.05` 就必须 DE”这种僵硬阈值。

只规定逻辑：

- 若有效域极稀疏、目标大面积平台、局部有限差分长期为零，则**梯度型局部 Solver 不应成为唯一求解依据**；
- 若目标光滑、可行域结构明确且局部法有理论支撑，则不应为了“高级”强制使用元启发式；
- 若结构化简能够显著降低维数/候选域，优先先做结构化简；
- Solver family 的选择必须连接实际 landscape evidence 或数学结构，而不是算法百科。

---

# 10. P1-A：Multi-resource Composition Semantics —— 多资源组合语义

## 10.1 目标

把“多个资源/多个主体如何共同作用”从隐含直觉提升为模型语义的一部分。

## 10.2 条件式启用

当存在：

- 多无人机/多车辆/多设施；
- 多覆盖体；
- 多区间；
- 多屏障/多传感器；
- 多资源联合满足目标；
- 多主体协同/竞争；

则必须声明组合关系。

## 10.3 组合算子建议字段

```text
Composition ID
Resources / agents
Target domain
Aggregation semantics:
  sum
  union
  intersection
  max
  min
  forall_exists
  exists_forall
  custom
Overlap semantics
Cooperation semantics
Conflict / shared-capacity semantics
Formula anchor
Decomposition validity
```

## 10.4 典型区别

### 数值求和

```math
F=\sum_i f_i
```

只有目标真实可加时成立。

### 时间/空间并集

```math
|\cup_i A_i|
```

不能用 `\sum_i |A_i|` 代替，除非证明没有重叠。

### 联合覆盖

```math
\forall x\in\Omega,\ \exists i:C_i(x)=1
```

可等价写成某些 max-min 结构，但需由当前判据推导。

### 共同满足

```math
\cap_i A_i
```

与并集完全不同。

## 10.5 Devil's Advocate 联动

如果多主体问题选择独立求解，必须回答：

- 为什么耦合可以删除；
- 是否存在 overlap / cooperation；
- 是否存在共享容量、同步、资源冲突；
- 独立结果怎样组合回全局目标。

若这些问题未闭合，应触发当前已有 `hidden_coupling / invalid_decoupling / multi_agent_to_independent` 风险，而不是新增新的 challenge state。

---

# 11. P1-B：Surrogate / Decomposition → Original Model Reevaluation

## 11.1 目标

当主问题通过 surrogate、pairwise capability、relaxation 或分解结构求解时，最终被选中的方案必须回到**原始模型**重新计算真实目标与耦合约束。

## 11.2 典型结构

例如先计算：

```math
T_{ij}=\text{resource }i\text{ 对 task }j\text{ 的局部能力}
```

再求：

```math
\max \sum_{ij}T_{ij}x_{ij}.
```

这里 `\sum T_{ij}x_{ij}` 可能只是 surrogate，而不等于原始协同目标。

## 11.3 必须记录

```text
Decomposition ID
Original model objective
Original coupling constraints
Surrogate / relaxed objective
Why decomposition is useful
What information is lost
Candidate solution recovery
Original-model reevaluation function
Original feasibility recheck
Objective discrepancy / approximation gap if computable
Claim scope
```

## 11.4 最终验收原则

对于最终推荐方案 `x*`：

```math
F_{original}(x^*)
```

必须在原始语义下重新计算；同时重新检查：

```math
g_k(x^*)\le0.
```

不得直接把 surrogate objective 当原问题 headline result。

若原模型复算后：

- 仍可行、结论一致：保留；
- 目标明显变化但方案主体可用：修改 claim/value；
- 出现耦合约束违反或核心答案改变：回到 model design / solve_validate。

---

# 12. P0-E：03A / 03B 责任边界澄清

## 12.1 当前歧义

Task Pack 中“参数敏感性”“多算法对比”等措辞如果不标阶段，可能被误读为主求解必须同步完成，从而与 v7.14 的 Numerical Verification Authority 产生冲突感。

本次不修改 v7.14 Contract，只把 Pack 写清楚。

## 12.2 mechanism Pack 建议改成两层

### 03A：当前主计算内在有效性

按适用项：

```text
量纲
符号方向
坐标/参考系转换
初值/边界
几何可行性
Predicate deterministic checks
极限/退化状态
守恒/残差
离散精度
事件边界容差
当前迭代/仿真收敛
当前 Solver 的约束/终止证据
```

### 03B：accepted 后结论深化

```text
现实参数敏感性
场景压力
失效阈值扩展搜索
替代模型/结构
替代算法比较
多 seed / 多初值 claim stability
广义外样本稳定性
```

## 12.3 optimization Pack 同理

03A：

- 当前解可行性；
- 当前 Solver status/gap/bound；
- 当前模型约束违反；
- 当前 Solver 自身要求的内部多启动/重复（若数学定义如此）；
- heuristic reduction 的当前 full-domain validator（若它就是当前 Solver validity 的组成部分）；
- surrogate candidate 的 original-model reevaluation。

03B：

- 替代算法横向比较；
- 参数扰动；
- 多 seed claim stability；
- 结构替代；
- 压力场景。

---

# 13. Project Memory：如何保存而不新增文件

本次应在 `templates/model/model_paper_framework.md` 的现有区域**增加少量可选字段**，不新增独立报告。

## 13.1 `结构化简与复杂度复审` 建议扩展

当前已有：

```text
未使用条件/字段及理由
可证明等价、降维、候选域或分解
高级算法前利用的结构
极端/边界/小规模复核
复审结论
```

建议扩展为可记录：

```text
核心 Predicate ID / 判据状态（适用时）
Event topology / boundary protocol（适用时）
Reduction ID + exact / proven_sufficient / heuristic
heuristic discarded-domain validator
Multi-resource composition semantics
Solver applicability summary
```

## 13.2 `求解与验证方案` 建议扩展

增加：

```text
Objective landscape / solver applicability assessment（适用时）
Original-model reevaluation（若 surrogate / decomposition）
Event boundary search bracket/tolerance（若算法依赖）
Predicate independent/equivalent check（若适用）
```

## 13.3 `结果摘要—验证与边界` 建议扩展

允许记录：

```text
heuristic reduction 实际 full-domain audit scope
surrogate 与 original objective 的差异
事件边界的实际数值精度
未发现更优候选的真实搜索范围
```

## 13.4 不升级 Framework Schema version

如果只是 Markdown 模板新增可选项目，且 `validate_model_paper_framework.py` 不要求历史项目必须出现这些字段，则继续使用现有 `v0.8-project-memory`，避免没有必要的项目迁移。

实施时必须先运行现有 framework validator 测试确认这一假设。若 validator 对模板结构有强制 schema 依赖，再单独评估最小兼容修改，不得直接宣布 schema migration。

---

# 14. 各权威文件的预计修改方案

| 文件 | 角色 | 计划修改 | 不应做的事 |
|---|---|---|---|
| `modules/02_model_design.md` | 模型设计 Authority | 定义 Predicate Closure、Event Protocol、Reduction Provenance、Solver Applicability、Composition、Original Reevaluation 的设计要求与通过逻辑 | 不复制 03A/03B 完整 contract；不新增 Gate |
| `packs/task/mechanism.md` | 机理题条件式 Pack | 给出适用场景、精确判据/事件/几何语义/阶段化验证要求 | 不独立定义新的全局生命周期 |
| `packs/task/optimization.md` | 优化题条件式 Pack | 强化 heuristic 缩域、landscape→solver、surrogate→original reevaluation | 不把算法名称变成模型类型 |
| `templates/model/model_paper_framework.md` | 项目语义记忆 | 增加少量可选结构有效性字段 | 不复制通用规则；不变成第二手册 |
| `packs/artifact/algorithm_flow.md` | 论文算法呈现 | 若必要，补“事件搜索/根定位需 bracket + update + tolerance”的呈现要求 | 不把简单求根强制变成 Algorithm 1 |
| `core/model_approval_contract.yaml` | Approval Authority | **默认不改**；现有 structural_simplification / hidden coupling / local-global checks 已足够承载 | 不复制新规则形成第二 authority |
| `core/numerical_verification_contract.yaml` | 03A 数值有效性 Authority | **第一轮不改** | 不把参数敏感性等 03B 内容拉回 03A |
| `core/task_taxonomy.yaml` | classification/capabilities | **第一轮不改** | 不为一次升级膨胀 capability |
| `modules/03_solve_validate.md` | 03A | 原则上不改；只有 Pack 无法消除 ownership 歧义时才做最小引用性补充 | 不新增第二套 PQS |
| `modules/03_result_analysis.md` | 03B | 原则上不改 | 不重复写 Pack 规则 |
| `tests/test_v717_mechanism_structural_validity.py` | regression | 检查关键治理语义存在且边界不漂移 | 不用测试“证明”数学正确性 |

---

# 15. Module 02 的建议落点

为避免文件碎片化，不新增大量二级标题。建议在现有“题面—数学—代码—输出语义闭环”和“复杂度合理性复审”之间建立一个紧凑的**结构有效性补充段**，仅在适用题型启用。

建议逻辑顺序：

```text
4 语义闭环
4.1 Formula Trace
4.2 Shared foundation
...
现有后续段

结构化简相关位置增加：
A. exact physical/geometric predicate
B. event topology if applicable
C. reduction provenance
D. multi-resource composition if applicable
E. solver applicability if needed
F. original-model reevaluation if decomposition/surrogate

→ Complexity Sanity
→ Model Challenge
```

注意：实际编号以实施时最新 `main` 为准，不为了本计划强行重排大文件。

---

# 16. mechanism Pack 的建议最终结构

仍保留现有五大节，避免 Pack 格式破坏：

```text
## 1. 进入条件
  + 对象 / 坐标 / 参考系 / 状态 / 边界
  + 条件式 Predicate Closure

## 2. 路线比较
  + 经典机理 vs 高保真
  + 解析/结构化简优先

## 3. 变量与公式闭环
  + state equations
  + exact predicate
  + line/ray/segment
  + quantifier order
  + event topology
  + reduction provenance

## 4. 必做验证与输出
  + 03A intrinsic
  + 03B post-acceptance（显式分层）

## 5. 否决或降级条件
  + predicate gap
  + invalid event search
  + heuristic reduction overclaim
  + geometry semantics mismatch
```

不要新增第 6、7、8 节把 Pack 写成小论文。

---

# 17. optimization Pack 的建议最终结构

仍保留现有五大节，在现有“solver 前结构检查”基础上增强：

```text
结构检查
→ reduction provenance
→ solver applicability
→ MODEL / SOLVER / VALIDATOR
→ decomposition/surrogate original reevaluation
→ 03A / 03B staged validation
```

重点新增否决条件：

- heuristic reduced domain 被写成 mathematically exact；
- sparse/plateau objective 仍只靠局部梯度 Solver 且无适配说明；
- surrogate objective 被当作 original objective；
- 多资源 union/cooperation 被直接相加；
- 原模型耦合约束未回算。

---

# 18. Algorithm Trace / 论文算法呈现的边界

本次不强制所有事件题都生成伪代码。

### `not_needed`

适用于：

- 单个解析根；
- 一次标准求根；
- bracket 和 tolerance 用几句正文即可恢复。

### `stepwise`

适用于：

```text
粗定位
→ 局部 bracket
→ entry boundary refine
→ exit boundary refine
→ interval union
```

### `pseudocode`

适用于：

- 多区间扫描；
- 条件分支更新；
- fallback；
- event-driven simulation；
- candidate repair。

如果修改 `packs/artifact/algorithm_flow.md`，只增加最小一句规则：

> 根定位/事件边界算法若依赖局部单调、符号变化或 bracket，Algorithm Trace 必须能恢复 bracket、更新判据、容差与 fallback；简单单次求根仍可 `not_needed`。

---

# 19. Solver Applicability 的实施细则

## 19.1 不设置 universal thresholds

禁止写成：

```text
rho_plus < 0.05 → DE
rho_g < 0.10 → GA
维数 > 20 → PSO
```

原因：不同问题尺度、目标值定义、采样设计不同，固定阈值没有跨项目数学依据。

## 19.2 记录 Evidence Level

Solver suitability 的经验 probe 只能支持：

```text
OBSERVED / VERIFIED_NUMERIC / HEURISTIC
```

不能把“随机采样没有发现更优点”包装成数学证明。

## 19.3 先数学结构、后经验 probe

推荐顺序：

```text
analytic structure
→ symmetry / monotonicity / convexity / elimination
→ qualitative landscape risk
→ only if needed: empirical probe
→ solver family
```

不能把 landscape sampling 变成另一种“先算再决定模型”的捷径。

---

# 20. 与 Claim Strength Calibration 的联动

不新建 claim 等级。沿用 v7.16 已有：

```text
PROVEN
VERIFIED_NUMERIC
COMPARATIVE
OBSERVED
HEURISTIC
```

建议映射原则：

- `exact` 且有严格推导/证明：可以支持 PROVEN 的结构性 claim；
- `proven_sufficient`：可支持“最优解必在缩减域”等被证明的局部结构 claim；
- `heuristic + coarse audit`：最多支持有限范围的 VERIFIED_NUMERIC / OBSERVED / HEURISTIC；
- surrogate decomposition 经 original reevaluation：headline result 应来自 original evaluation，而不是 surrogate score；
- “未发现更优”必须带真实搜索范围。

不修改 Claim Strength Authority，只让 Module 02 / framework 消费现有等级。

---

# 21. 测试计划

## 21.1 新增专门 regression

建议新增：

```text
tests/test_v717_mechanism_structural_validity.py
```

### 测试组 A：Mechanism Pack

至少检查存在以下语义：

```text
Predicate / 精确判据
line / ray / segment 或等价中文语义
量词顺序
事件拓扑 / bracket / tolerance
exact / proven_sufficient / heuristic
03A / 03B 分层
```

### 测试组 B：Model Design

检查：

```text
结构化简仍先于算法
Reduction provenance 三态
Solver applicability 是条件式而非 universal
不设固定 rho 阈值
不允许审批前运行正式任务代码
多资源 composition semantics
surrogate/decomposition original-model reevaluation
```

### 测试组 C：Optimization Pack

检查：

```text
heuristic reduction 不能冒充 exact
solver choice 需要结构依据
surrogate final candidate 必须 original-model reevaluate
03A / 03B ownership 清楚
```

### 测试组 D：Framework Template

检查可选字段存在：

```text
Predicate status
Event topology
Reduction status
Composition semantics
Solver applicability summary
Original-model reevaluation
```

同时验证历史 framework 不因缺这些新字段而读失败。

### 测试组 E：No architecture creep

建议加反向断言，防止未来误加：

```text
没有新 task pack 名 mechanism_structure_reducer
没有新 runtime gate 名 mechanism_structure_gate
core/task_taxonomy.yaml 未因本次第一轮新增 capability
core/numerical_verification_contract.yaml 未被本次语义错误扩展到参数敏感性
```

反向断言应谨慎，只针对本 PR 明确冻结的范围，不永久阻止未来单独设计的合法升级。

## 21.2 全仓测试

必须执行：

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests
python scripts/generate_indexes.py --check
```

## 21.3 路由 smoke

按当前 `resolve_runtime.py` 的正式 CLI 运行代表性任务，至少覆盖：

```text
mechanism/explanation + physical_mechanism
optimization + physical_mechanism
普通 optimization（确认未无条件加载机理细则）
普通 prediction/evaluation（确认无影响）
```

具体命令以实施时当前 router tests / CLI help 为准，不在本计划硬编码可能过时的参数格式。

## 21.4 Version consistency

目标发布为 `7.17.0` 时，按当前治理检查所有版本载体和回归测试；不得全仓盲替换 `7.16.0`。

---

# 22. 生成文件与索引

任何源文件修改后：

```text
source changes
→ scripts/generate_indexes.py
→ review generated diff
→ generated-file contract
```

不得手改：

- `MANIFEST.sha256`；
- generated Skill indexes；
- 其他由 generator 管理的文件。

本计划文件加入 `docs/` 后，如果生成器把它纳入索引，应由自动生成链更新。

---

# 23. 版本发布计划

## 23.1 版本等级

本次完整功能实现属于 `minor`：

```text
7.16.0 → 7.17.0
```

原因：增加新的条件式建模设计能力，但：

- 不破坏旧目录；
- 不破坏 CLI；
- 不破坏 Schema；
- 不改变旧项目读取；
- 不删除现有能力。

## 23.2 计划文件阶段

当前只创建计划文档时：

- 不提前把 runtime Skill 版本改成 7.17.0；
- 不在功能未实现时宣称 v7.17.0 已发布；
- PR 可保持 draft，后续实现完成再更新版本载体和 Changelog。

## 23.3 最终 Changelog 主题

预计记录：

```text
Mechanism Predicate Closure
Event Topology & Boundary Protocol
Reduction Provenance
Solver Applicability Assessment
Multi-resource Composition Semantics
Original-model Reevaluation
03A/03B Pack wording alignment
Backward-compatible project-memory persistence
```

---

# 24. 分阶段实施顺序

## Phase 0：基线与范围冻结

- [x] 读取 `core/bootstrap.yaml`
- [x] 读取 `SKILL_CHANGE_GOVERNANCE.md`
- [x] 确认 v7.16.0
- [x] 确认基线 main SHA
- [x] 检查 open PR：无重叠
- [x] 读取 Module 02 / mechanism / optimization / numerical verification / 03A / 03B / Algorithm Flow / Framework Template
- [x] 创建独立升级分支
- [x] 写入本计划

## Phase 1：只改模型设计语义

目标文件：

```text
modules/02_model_design.md
```

完成：

- Predicate Closure；
- Event Protocol；
- Reduction Provenance；
- Solver Applicability；
- Composition Semantics；
- Original Reevaluation；
- 与 Complexity Sanity / Model Challenge 的连接。

**先不动 Pack。** 完成后检查是否存在重复 Authority。

## Phase 2：Task Pack 消费 Authority

目标：

```text
packs/task/mechanism.md
packs/task/optimization.md
```

原则：Pack 只给题型进入条件、适用检查和否决条件，不复制 Module 02 全文。

同时完成 03A/03B wording alignment。

## Phase 3：Project Memory 持久化

目标：

```text
templates/model/model_paper_framework.md
```

只增加可选项目字段，不改 framework schema version，除非测试证明必须。

## Phase 4：Algorithm presentation 最小补充

评估：

```text
packs/artifact/algorithm_flow.md
```

只有 Event Protocol 无法通过现有 Algorithm Trace 表达时才修改；否则跳过。

## Phase 5：Tests

新增专用 regression，并更新必要现有测试。

先跑 focused tests，再全仓 tests。

## Phase 6：Version / Changelog / Generated Metadata

只有功能实现与测试通过后：

- bump `7.17.0`；
- 更新 Changelog；
- 运行 generator；
- 检查版本一致性。

## Phase 7：PR Review

- 更新 PR description 中的修改简报；
- 列出实际 changed files；
- 说明哪些“预计文件”最终无需修改及原因；
- 等待完整 CI；
- CI 未完成时不得宣称通过；
- 发现 review finding 时先更新本计划/实现一致性，再修复。

## Phase 8：Merge 与完成报告

仅 CI 全绿且无 blocking review 后合并。

完成报告必须包含：

```text
branch
PR
merge status
merge SHA
core changed files
semantic changes
compatibility
CI status
remaining uncertainties
```

---

# 25. 风险矩阵

| 风险 | 严重度 | 预防措施 | 验收 |
|---|---:|---|---|
| 把计划写成第二 Authority | 高 | 所有最终规则回到 Module/Pack；本文件标 PLANNING ONLY | PR review |
| 新增太多 Gate/Skill | 高 | 明确禁止新 Gate/Skill | changed-file review |
| 破坏 03A/03B 边界 | 高 | numerical contract 第一轮冻结；Pack 阶段化表述 | regression + full tests |
| heuristic 缩域被误写成证明 | 高 | 三态 provenance + claim-level linkage | content test + review |
| empirical probe 变成审批前跑代码 | 高 | Layer A/Layer B 分离；继续遵守 user execution | Module 02 review |
| 固定阈值过拟合单赛题 | 高 | 禁止 universal rho threshold | negative regression |
| 多资源 operator 规则过于具体 | 中 | 只定义语义类别和量词，不写赛题常数 | review |
| Framework 变成通用手册 | 中 | 只放本项目当前选择字段 | framework test |
| 新字段导致旧项目读失败 | 高 | 保持可选；跑 historical/validator tests | unit tests |
| 版本提前升级但功能未完成 | 中 | Phase 6 最后 bump | git history review |
| generated files 手改 | 高 | generator only | generated contract |
| PR 范围膨胀到 plotting/writing | 中 | forbidden scope list | PR changed files |

---

# 26. 兼容与迁移

## 26.1 旧项目

旧项目：

- 可以继续读取；
- 不要求补 `Predicate ID` 等新字段；
- 只读 review 不自动 stale；
- 重新进入 model_design 且模型语义发生变化时，按新规则完成结构有效性设计。

## 26.2 已批准模型

仅因为 Skill 从 7.16.0 升到 7.17.0，不自动使旧 `locked_model_spec` stale。

只有项目自身出现：

- predicate 语义修改；
- reduction domain 修改；
- solver strategy 实质修改；
- composition semantics 修改；
- decomposition 结构修改；

才按已有 semantic governance 触发 revision/stale。

## 26.3 工作簿

不新增 mandatory sheet，不改变 Workbook Schema。

如果实际项目需要保存：

- event brackets；
- full-domain audit candidates；
- original-model reevaluation；

优先使用现有通用明细、约束检查、状态明细、候选方案/验证 evidence 结构。只有未来多个项目证明现有工作簿无法无歧义承载，才单独提出 Workbook Schema 升级。

---

# 27. 明确禁止的 scope creep

本 PR 禁止顺手加入：

- 新 AI agent 编排；
- 新深度学习/强化学习算法；
- 新数据清洗规则；
- 新 MATLAB 配色；
- 新 Figure Enhancement；
- 新 LaTeX 格式；
- 新 Submission package 规则；
- Branch Protection 设置；
- unrelated CI 重构；
- legacy 文件清理；
- 全仓 terminology 重写；
- 新工作簿 Schema；
- 新 task taxonomy capability。

如发现这些问题，应记录为独立后续 Issue/Plan，不混入 MSV-01。

---

# 28. 完成判据（Definition of Done）

v7.17 只有同时满足以下条件才可认为本主题完成：

- [ ] 机理题在适用时必须明确 exact physical/geometric predicate；
- [ ] line / ray / segment、对象定义域和量词顺序不再只靠隐含理解；
- [ ] 连续事件算法必须能恢复 topology / bracket / update / tolerance；
- [ ] 缩域明确标记 `exact / proven_sufficient / heuristic`；
- [ ] heuristic 缩域不会自动产生 global-optimum claim；
- [ ] Solver 选择能够检查 sparse/plateau/nonsmooth 适配风险；
- [ ] 不存在固定的跨题 `rho` 阈值硬编码；
- [ ] 多资源作用显式记录 composition semantics；
- [ ] surrogate/decomposition 的最终方案回到 original model 复算；
- [ ] mechanism/optimization Pack 已明确 03A 与 03B 的职责边界；
- [ ] `模型论文框架.md` 能保存本题实际结构选择且未变成第二手册；
- [ ] 没有新增独立 Skill；
- [ ] 没有新增 runtime Gate；
- [ ] 第一轮没有修改 task taxonomy / numerical verification contract；
- [ ] 旧项目 read compatibility 保持；
- [ ] lint 通过；
- [ ] full unit tests 通过；
- [ ] generated index check 通过；
- [ ] representative runtime smoke 通过；
- [ ] 版本一致性通过；
- [ ] GitHub CI 全绿；
- [ ] PR review 无 blocking finding；
- [ ] Changelog 准确说明能力边界；
- [ ] 完成报告不夸大未验证内容。

---

# 29. 预期最终能力示例（仅用于验收理解，不作为题目模板）

对于一个“运动体 + 几何遮挡 + 多资源 + 时间优化”问题，v7.17 应能引导出：

```text
1. 运动方程：状态如何随时间变化
2. Predicate：什么条件才叫真正遮挡/覆盖
3. Geometry semantics：射线/线段/边界/实体/量词顺序
4. Critical-set reduction：为什么只检查某个边界或有限临界点
5. Event topology：遮挡成立时间集合可能是什么结构
6. Boundary protocol：怎样可靠求进入/退出时刻
7. Reduction provenance：缩小角度/时间/空间搜索域的依据等级
8. Solver applicability：目标是否平台、稀疏、跳变，什么 Solver 适配
9. Composition semantics：多个资源是并集、协同 max-min 还是其他
10. Decomposition：若先分配后局部优化，是否丢失耦合
11. Original reevaluation：最终方案回到原始模型重新算真实目标
12. Claim calibration：证明、数值验证、启发式结论分别怎么写
```

而不是：

```text
列几个运动方程
→ 直接密集离散
→ 上 DE/GA/PSO
→ 得到一个数字
→ 写“模型有效、结果最优”
```

---

# 30. 实施进度记录

> 本区用于上下文恢复。每完成一个 Phase，只更新状态和必要的事实摘要；不要在这里复制实际规则全文。最终 runtime truth 仍在权威文件中。

| Phase | 状态 | 当前事实 | 下一步 |
|---|---|---|---|
| 0 基线与计划 | `completed` | v7.16.0；main=`afbbe589...`；无 open overlapping PR；分支已创建；计划已写 | 创建 Draft PR，后续等待用户要求进入功能实现 |
| 1 Module 02 | `not_started` |  |  |
| 2 mechanism/optimization Packs | `not_started` |  |  |
| 3 Framework persistence | `not_started` |  |  |
| 4 Algorithm Flow | `not_started` |  |  |
| 5 Tests | `not_started` |  |  |
| 6 Version/Changelog/generated | `not_started` |  |  |
| 7 PR review/CI | `not_started` |  |  |
| 8 Merge/report | `not_started` |  |  |

---

## 31. 当前停点

当前阶段只完成：

```text
重新读取 current v7.16.0
→ 仓库事实核对
→ 修改范围冻结
→ 创建 upgrade/v7.17-mechanism-structural-validity
→ 写入本计划
```

**尚未修改任何 v7.16.0 runtime modeling semantics。**

下一次进入实施时，必须从本文件第 0 节恢复，并从 **Phase 1：`modules/02_model_design.md`** 开始；不得跳过最新 main / PR / authority 再确认，也不得因为本文件已经很详细就把它当成实际 Skill Authority。
