# Module 02：模型设计、语义闭环、复杂度复审、独立挑战、人工锁模与论文框架

本模块负责把审题结果转成可求解、可验证、可写作的当前模型语义。跨竞赛的公式推理、Model/Solver/Validator 角色、优化模型表达、Algorithm Trace、规则等级、命题预算和 Citation Evidence 由 `core/writing_reasoning_contract.yaml` 唯一定义；Model Challenge 与 Human Model Approval 的唯一行为合同为 `core/model_approval_contract.yaml`；主求解内在数值有效性的字段级规则由 `core/numerical_verification_contract.yaml` 唯一定义。本模块只记录本题实际选择，不复制第二套写作、审批或数值验证规范。

## 0. 前置条件

只接受 `problem_contract_status=frozen` 的小问。若题意对象、数据角色、约束来源或小问依赖仍存在会改变答案的歧义，退回 Module 01；不得通过代码试错替代审题。

Problem Contract 冻结只回答“题目是什么意思”，不等于模型已获准进入代码阶段。正式任务代码前还必须依次完成当前模型语义闭环、Complexity Sanity、独立 Model Challenge 和用户 Human Model Approval。

## 1. 模型路线比较

每问至少构造两条实质路线：

- 路线 A：经典稳健模型 + 本题修正；
- 路线 B：高级创新或跨领域融合。

比较核心原理、数学表达、适配性、创新点、精度优势、局限、误差来源、求解难度和推荐等级，并说明为何否决看似高级但不适合的路线。

高级模型执行必要性、变量闭环、数据支撑、计算可行、解释性、验证性和复现性七项准入。准备使用 W-DRO、CVaR、MPEC、Stackelberg、ALNS、GNN、空间杜宾、DML、强化学习、深度学习等时，按需加载 `packs/task/advanced_method_gate.md`。

**结构化简优先于算法升级。** 高维、非线性或组合问题在决定 GA、PSO、DE、ALNS、深度学习等方法前，依次检查：解析/近似解析关系、单调性/凸性/对称性、变量消元或降维、候选区域/上下界、分解/分层结构、离散与连续决策能否分开，以及前问结果能否限制搜索域。最终路线应形成：

```text
题目结构 → 数学化简/分解 → 有效搜索空间 → 算法
```

而不是“问题复杂 → 直接上高级算法”。

## 2. 数据协议与预处理必要性判定

在 Module 01 的数据结构基础上锁定字段—含义—单位—粒度—范围—关联键，并先完成**非破坏性数据审计**：缺失、NaN/Inf、异常候选、重复、单位冲突、时间错位、空间坐标、主键和采样结构。检查本身不等于需要修改数据。

标准化、归一化、对数、Box-Cox、滞后、窗口、空间权重、插值、滤波、重采样、异常替换和编码等操作必须有对象和依据。无真实数据时可模拟，但必须记录生成机制、参数来源和随机种子。

完成审计和模型路线选择后，锁定项目级 `preprocessing_decision`：

| 字段 | 取值/要求 |
|---|---|
| `decision` | `not_needed / question_local / project_level` |
| `level` | `none / structural / transformative` |
| `evidence` | 原始数据可直接使用或必须处理的理由 |
| `operations` | 实际允许的数据变换；可为空 |
| `forbidden_operations` | 会破坏题意、物理意义或解释的操作 |
| `downstream_data_source` | `raw / preprocessed` |

判定：

1. 多问共享同一数据不等于需要项目级预处理；数据已满足模型要求时判 `not_needed`；
2. 只有某问需要对数、标准化、滞后、窗口或模型专属编码时判 `question_local`；
3. 多问共同需要单位换算、坐标统一、时间对齐、表关联、公共重采样、缺失/异常处理或滤波时判 `project_level`；
4. 用户明确要求统一数据总表时可判 `project_level`；仅整理/对齐而不改观测值时标记 `structural`，不包装成“清洗”；
5. 审计证明不存在的问题，对应处理不得继续保留；
6. 统计极端值不自动等于错误数据，先判断尖峰、边界、结构突变、稀有事件等真实对象语义。

任何会改变数据的操作必须回答：问题是否真实存在；不处理影响哪个模型环节；为何选择当前方法和参数；是否可能破坏真实信息。无法闭合则删除该处理。

`preprocessing_decision` 属于模型语义。数据角色、判定状态或处理口径变化时同步更新 `semantic_revision` 与 `semantic_change_categories`。

## 3. 变量、假设与三轴分类

区分决策变量、状态变量、中间变量、参数、目标、约束和评价指标。变量记录符号、名称、类型、单位、范围、现实含义和代码变量。

假设按必要性而非数量保留。只有实质改变变量、约束、目标、分布、状态转移、近似误差或适用边界的条件才作为假设；题面事实、数据事实、确定性定义和单位约定不伪装成假设。共享假设与局部假设按实际作用分层。

逐问锁定：

1. `classification.objective`：最终直接交付目标，只保留一个；
2. `classification.structures`：真正改变变量、约束、验证或交付结构的特征，最多三个；
3. 顶层 `capabilities`：必须执行的可行性、残差、外样本、不确定性、泄漏、校准或可识别性检查。

同时为写作与评审登记当前**标准模型类型**与**正式模型名称**：标准类型用于回答“这是什么数学模型”，正式名称可加入题目专属机制。不得用 solver、软件或验证算法名称替代标准模型类型。优化类小问还要明确主决策变量/决策对象和 objective 的现实含义，使后续摘要能直接恢复“优化什么”。

`capabilities` 的唯一权威位置是小问顶层。兼容别名存在时必须与顶层一致；旧 `problem_types/legacy_task_packs` 只能由三轴分类派生。

## 4. 题面—数学—代码—输出语义闭环

每个核心对象、条件、变量、约束和输出至少建立：

```text
题面对象/要求
→ 数学变量、关系、目标或约束
→ Python 变量/函数
→ 工作簿输出或验证证据
```

| 题面来源 | 数学层 | 计算层 | 输出证据 | 状态 |
|---|---|---|---|---|
|  |  |  |  | closed / gap |

Hard gap 包括：

- 题目要求有、代码没有；
- 核心代码对象有、数学来源没有；
- 论文隐含约束/变换无法由题意、数据或机制支持；
- 同名不同义；
- 单位、时间/空间粒度或索引断裂。

关键项全部 closed 后，`semantic_closure_status=passed`。

### 4.1 核心 Formula Trace

`Source–Derivation–Destination` 的语义由 reasoning contract 唯一定义。本阶段只登记当前模型的核心关系：

| Formula ID | Source | Depends on | Derivation | Destination | 代码/证据锚点 | 状态 |
|---|---|---|---|---|---|---|
| F1 |  |  |  |  |  | closed / gap / stale |

机器只核验来源、依赖、去向和锚点是否存在，不从正则判断数学正确性。存在 gap 时不得用代码实现或论文润色补洞。

### 4.2 共享基础与跨问增量

是否启用共享基础、允许内容和关系图准入服从 `writing_reasoning_contract.shared_foundation` 与 `cross_question_progression`。本阶段只记录本题实际选择；独立小问明确 `independent`。

| 小问 | 继承结构 | 新增对象/条件 | 新增数学结构 | 困难变化 | 求解变化 |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

### 4.3 数值参数证据计划

对会影响结论的数值参数登记候选范围、证据方法和最终值状态；题面固定参数注明来源即可。

| 参数 | 数学作用 | 候选范围 | 证据方法 | 通过标准 | 最终值状态 |
|---|---|---|---|---|---|
|  |  |  |  |  | pending |

### 4.4 Primary Quality Specification（PQS）

模型设计阶段必须把“当前主计算本身是否有资格被接受”与“结果 accepted 后结论是否稳健”分开。前者依据当前小问顶层 `capabilities` 和 `core/numerical_verification_contract.yaml`，在现有 `validation_plan` / 当前模型论文框架中登记 **Primary Quality Specification**；后者只记录为 downstream risk hints，不能在本阶段提前生成 `result_analysis_plan`。

PQS 只允许描述当前 locked model 与声明数值方法的最低内在有效性要求，例如：当前解的可行性/约束违反、等式/均衡/守恒残差、必要的网格或时间步精度、必要的迭代/仿真收敛、当前求解器 bound/gap/termination 的可解释等级，以及 capability 明确要求且失败会使主结果无效的一次主 OOS、泄漏、校准、可识别性或最低不确定性精度。

每项至少记录：

```text
PQS ID
→ capability
→ protocol
→ target
→ metric
→ criterion / threshold
→ threshold source
→ evidence worksheet
→ blocking
```

阈值必须在主求解代码生成前有来源，可来自题目/官方精度、数学定义、locked model tolerance、solver tolerance、数值方法精度目标或明确论证的项目标准。禁止先看结果再挑一个刚好能“通过”的阈值。

PQS **不得包含**参数敏感性、现实参数扰动、场景压力、替代算法/结构、多 seed / 多初值结论稳定性、异质性、误差分解、广义外样本稳定性或消融。这些只作为候选风险记录，必须等 `accepted_solution_workbook` 后由 Module 03B 根据真实主结果决定是否进入正式 `result_analysis_plan`。

因此设计阶段的验证规划分成两个不同层次：

```text
Primary Quality Specification
→ 决定本次主计算能否 accepted

Downstream risk hints
→ 仅提示 accepted 后可能需要哪些深化分析
→ 不提前执行、不提前写入问题X求解.py
```

### 4.5 Citation Evidence 计划

只登记需要外部来源的核心 claim，例如外部经验参数、数据、领域事实、非显然标准定理、方法来源和既有研究比较。本文自己的推导和数值结果不需要外部文献代替证据。

| Claim ID | 主张/来源对象 | 类型 | Citation Key | 预期正文位置 | 状态 |
|---|---|---|---|---|---|
| C1 |  | method / theorem / parameter / data / domain_fact / prior_comparison |  |  | pending / current / stale |

设计阶段可以先标 pending；进入写作前需要外部来源的核心 claim 应闭合。

### 4.6 Algorithm Trace 与呈现模式

算法选择完成后按 `writing_reasoning_contract.algorithm_presentation` 判断论文是否需要正式算法流程：

```text
not_needed → 相邻公式 + 简短求解说明即可
stepwise   → 多阶段数学求解流程，控制流不是主要信息
pseudocode → 循环/分支/候选筛选/修复/停止规则本身是方法信息
```

只有 `stepwise` 或 `pseudocode` 才建立 current Algorithm Trace；`not_needed` 不创建装饰性算法框。Trace 至少记录算法作用、输入、核心操作、终止条件、输出、呈现模式与状态，并按需要连接状态/决策变量、循环/分支、Formula、Proposition、Constraint、Python 代码和工作簿证据。

内部闭环：

```text
模型结构/已证明性质
→ Algorithm Trace
→ 论文算法步骤
→ Python真实实现
→ 工作簿结果或验证证据
```

若命题证明了候选域缩减、可行保持、阈值或停止条件，应把命题锚点连接到真正受影响的算法步骤，而不是让命题与求解段彼此独立。详细的控制流伪代码与分阶段数学步骤只在需要时加载 `packs/artifact/algorithm_flow.md`。

### 4.7 Model / Solver / Validator 与论文身份字段

按 `writing_reasoning_contract.model_solver_validator_roles`、`model_naming`、`optimization_model_expression` 和 `solver_justification` 登记当前小问的论文身份信息。这里只记录本题事实，不复制通用规则。

每问至少能恢复：

```text
标准模型类型
正式模型名称
Model：数学上求什么
Solver：主求解器/分解求解结构及本题适配理由
Validator / baseline / alternative：独立验证角色及 evidence anchor
```

对优化/调度/路径/分配/控制类小问额外登记：

```text
主要决策变量或决策对象
→ objective 的现实含义
→ 核心约束来源
→ 核心模型收束状态
```

如果 solver 后问沿用，记录继承结构与新增变化；如果更换 solver，记录改变求解需求的结构增量。若正文计划写“另用某算法”，必须在这里给出 `baseline / alternative / validator` 角色和实际 evidence anchor，否则写作阶段不得凭空补出对照结果。

同时给每问记录论文二级小节规划与 `subsection_granularity` 状态。这个字段只用于避免“决策变量/目标/约束/汇总/算法/验证”被机械拆成过多标题，不限制全文一级章节数量。

### 4.8 机理/几何结构有效性（按需）

本节不是新的生命周期 Gate，也不新增 task taxonomy 字段。只有当当前小问确实包含几何判定、连续事件、机理约束嵌套优化、多资源协同、候选域缩减或 surrogate / decomposition 时，才把相应要求纳入现有 `semantic_closure`、Complexity Sanity、Model Challenge 和 Human Approval。

#### 4.8.1 Predicate Closure：先闭合“成功/失败到底是什么”

碰撞、遮挡、覆盖、可见、进入/退出、接触、包含、到达等布尔事件必须从自然语言闭合到可计算判据。当前模型至少能恢复：

```text
physical event
→ object domain / active or visible subset
→ reference frame
→ exact mathematical predicate
→ quantifier order
→ line / ray / segment / surface / volume semantics
→ exact or approximate status
→ Python predicate / evidence anchor
```

不得把无限直线、射线和有限线段默认等价；不得把点、边界、表面和实体默认等价；不得把“对所有对象存在一个资源”与“存在一个资源满足所有对象”默认等价。若模型通过对称性、凸性、可见性、极值原理或临界点把连续对象缩减到活动边界/有限临界集，必须同时登记该缩减的依据。

若存在两个数学上独立、代价合理的等价判据，可规划一个作主判据、另一个作实现交叉复核。**数值一致不能替代等价性证明**；机器只检查声明与 evidence anchor，不从代码或正则自动推断数学等价。

#### 4.8.2 Event Topology / Boundary：先确定事件区间结构，再定位临界时刻

连续时间事件先定义 `I(t)`、`g(t)` 或等价状态关系，再说明事件集合可能是单区间还是多区间。若不能证明只存在一个区间，不得先验把事件写成单个 `[T_s,T_e]`；应允许表示为若干进入/退出区间的并集。

二分、牛顿、单调搜索或其他根定位方法使用前必须给出适用的局部结构：搜索域与 bracket、符号变化/单调性/单峰或相位依据、左右端点更新规则、容差、停止条件以及多次切换时的粗定位/分段策略。全局状态呈 `0→1→0` 或更复杂切换时，“函数连续”本身不足以证明可以在全区间直接二分。

若 event boundary 的 bracket、相位和更新规则是算法的实质信息，应连接 Algorithm Trace；若只是单次直接求根且相邻公式已足够恢复，则保持 `algorithm_presentation=not_needed`，不为形式额外生成伪代码。

#### 4.8.3 Reduction Provenance：缩域必须区分证明与启发式

所有会改变候选域、搜索空间、活动边界或分解范围的结构化简，按真实依据区分：

```text
exact             = 与原问题严格等价
proven_sufficient = 已证明保留至少一个原问题最优解或全部所需临界/可行解
heuristic         = 由物理直觉、经验、粗数据或计算预算提出，没有充分性证明
```

- `exact` 说明等价/可逆关系；
- `proven_sufficient` 连接命题、证明或其他充分性依据；
- `heuristic` 必须保留被排除区域的语义，设计弃置域反例检查或有限覆盖证据，并在 claim scope 中承认验证范围。可用 coarse grid、Latin Hypercube、Sobol、随机可行采样、边界扫描等，但具体方法由题型和维度决定；
- heuristic 缩域不得仅因主 solver 在缩域内停止就升级为“全局最优”。其最终 claim strength 继续服从现有 Claim Strength Calibration。

上述弃置域检查若需要题目专属计算，仍受 Human Approval 和 `core/user_execution_contract.yaml` 约束；助手不得为了在审批前“证明 solver 适用”而私自运行赛题代码。

#### 4.8.4 Solver Applicability：由目标/可行域结构决定算法族

solver 选择先使用可证明结构：连续/可微、凸性、单调性、可行域连通性、离散性、事件跳变、单次评价代价和问题规模。对几何判据嵌套、可行域极稀疏、目标大面积零/平台、强非光滑或分段切换的问题，不能只因为决策变量连续就默认局部梯度 NLP 适用。

若解析结构不足以判断，可在 proposed model 中设计一个**条件式 solver applicability probe**，例如记录：

```text
finite evaluation rate
feasible ratio
non-degenerate objective ratio
plateau / zero-mass ratio
local finite-difference activity
jump / nonsmooth evidence
dimension
single-evaluation cost
```

该 probe 是 solver 适配诊断，不是主结果，也不是 03B 的参数敏感性。审批前只能定义 protocol、阈值来源、solver 分支与 fallback，不能由助手执行题目专属数值试跑。若用户批准的是“probe 判据 → solver A/B 分支”的完整条件式策略，则用户本地 full-fidelity 执行可按该已批准策略选择分支；若实际 probe 触发了未在批准语义内的新算法、搜索域或模型修改，则现有 semantic governance 使旧 approval stale，并回到本模块重新审查。

当有效目标区域和局部变化区域极稀疏、有限差分长期近零或事件判据造成明显跳变时，局部梯度法不得作为唯一主 solver；应优先考虑进一步结构缩域、候选生成、全局/无导数搜索、分解或“全局粗搜 + 局部精修”。

#### 4.8.5 Multi-resource Composition：先声明组合算子和量词

多个资源共同作用时，必须明确真实组合语义，例如：

```text
sum / union / intersection / max / min / forall-exists / custom
```

并写出相应数学关系、重叠/互补/同步/共享约束和量词顺序。时长相加不自动等于区间并集；单资源独立最优不自动等于联合最优；存在合作覆盖时不得把多资源问题静默解耦为多个独立单体。

#### 4.8.6 Surrogate / Decomposition：最终回到原始耦合模型

使用 pairwise capability、松弛、代理目标、分层分解、先分配后连续优化或其他 surrogate / decomposition 时，至少区分：

```text
original model/objective
surrogate or subproblem objective
mapping to full decision
final original-model reevaluation
```

surrogate 可以承担筛选、分配、产生初值或缩域角色，但最终推荐方案原则上必须回到原始目标和全部原始硬约束复算。若规模使完整回算不可行，必须显式保留剩余近似、遗漏耦合和实际 claim scope，不能把 surrogate objective 直接冒充原问题最终目标值。

#### 4.8.7 与 03A / 03B 的边界

本节只强化**当前模型语义和当前主算法适配性**，不改变 `core/numerical_verification_contract.yaml`：

- 当前精确判据、事件定位精度、当前缩域/solver 策略内部成立所必需的证据，以及当前推荐方案的 original-model 回算，可进入 03A；
- 参数敏感性、现实扰动、压力场景、替代算法/结构、多 seed / 多初值结论稳定性、广义失效边界仍只属于 accepted 后的 03B；
- 不新增工作簿 Schema、Project State 字段或独立结构审查报告。适用信息只写入当前 `模型论文框架.md`、Formula/Algorithm Trace、现有 challenge/approval 和后续真实 evidence anchor。

## 5. 复杂度合理性复审

模型路线形成后、进入 Model Challenge 前检查题目复杂度是否被异常压扁。触发复审的典型 flag：

- `unused_problem_conditions`；
- `unused_attachment_fields`；
- `unexpected_dimension_collapse`；
- `unexpected_decoupling`；
- `dynamic_to_static_collapse`；
- `multi_agent_to_independent`；
- `inactive_key_constraints`；
- `downstream_copy`；
- `implausibly_easy_computation`。

出现 flag 不等于模型必错，但必须说明：简化是否来自严格等价/可证明降维/主导机制；删除的耦合、状态、边界和约束依据；未使用字段为何冗余；极端/边界/小规模复核是否支持；是否先利用可解释结构再选择算法。

对适用 4.8 的机理/几何/混合优化问题，还要检查：判据是否把 line/ray/segment 或量词顺序混淆；事件是否被无依据地假定全局单调/单区间；heuristic 缩域是否被伪装成严格充分；多资源组合是否错误求和/解耦；surrogate 结果是否计划回到 original model 复算；solver 是否与目标/可行域的实际结构相符。这些 finding 复用现有 `review_required/blocking/warning` 治理，不建立新的 machine-state gate。

无法解释则 `complexity_sanity_status=review_required`，不得进入 Model Challenge，更不得进入求解。

## 6. Independent Model Challenge

当 Problem Contract、语义闭环、Formula Trace、`preprocessing_decision` 与 Complexity Sanity 已达到当前设计要求后，形成 `proposed_model_spec`，然后按 `core/model_approval_contract.yaml` 执行两次独立审查。两次审查不创建 `MODEL_REVIEW_AI.md`、`HUMAN_MODEL_REVIEW.md` 或 `AGENT_RUNS.md`，当前结论写入 `模型论文框架.md`，机器状态只写入 `state/project_state.yaml`。

### 6.1 Model Reviewer

Model Reviewer 是正向适配审查，至少检查：

- 当前路线是否真正回答冻结后的 Problem Contract；
- selected model 是否比被否决路线更适配当前数据、约束和交付；
- 变量、目标函数、约束、Formula Trace 与 `preprocessing_decision` 是否闭合；
- 标准模型类型和正式模型名称是否与真实数学结构一致，题目专属名称是否没有掩盖模型类型；
- Model / Solver / Validator 角色是否分离，算法没有替代模型本体；
- 优化类模型是否能直接恢复决策变量/对象、objective、核心约束和最终可计算模型；
- solver 第一次使用、后问沿用或更换时是否有本题结构依据；
- 是否先利用结构化简，再选择求解器/算法；
- 适用时精确物理/几何判据、事件 bracket/拓扑、缩域 evidence level、多资源组合语义、solver applicability 与 surrogate→original reevaluation 是否闭合；
- full-fidelity 计算是否可实施；
- PQS 是否足以判断主计算的内在数值有效性，且没有把结果深化分析伪装成主质量门；
- accepted 后的候选深化风险是否与核心结论有关，而不是为了形式完整机械堆敏感性/鲁棒性图；
- 模型是否能够自然、准确地进入论文，而不是靠术语包装；
- 当前问题章节计划是否把同一论证链机械切成过多二级小节。

### 6.2 Devil's Advocate

Devil's Advocate 是反方挑战，至少检查：

- 是否存在另一种会改变答案的合理题意解释；
- 是否为了求解方便引入题目不允许的假设；
- 是否闲置关键题面条件或附件字段；
- 预处理是否改变真实对象语义或造成泄漏；
- 是否错误解耦、错误静态化或把多主体问题压成独立单体；
- 核心约束是否长期不生效；
- 是否把局部性质写成全局性质；
- 是否把无限直线/射线/线段、代表点/整个对象、可见/不可见区域或 `forall/exists` 量词顺序混为一谈；
- 是否对 `0→1→0`、多区间或非单调事件直接使用没有局部 bracket 依据的根搜索；
- 是否把 heuristic 缩域、局部验证或 surrogate objective 写成严格全局性质；
- 多资源是否存在被忽略的重叠、协同、同步或共享约束；
- 分解/代理路线是否跳过原始耦合模型回算；
- solver 是否可能因零平台、稀疏可行域、非光滑或跳变而失去有效搜索信息；
- 是否存在明显更简单的 baseline 已足以回答题目，使当前高级模型缺乏必要性；
- 是否反向出现“题目本来复杂但模型异常容易”的过度简化；
- 是否用 post-hoc 阈值让主质量门看起来通过，或把参数敏感性/替代算法等 03B 工作提前塞进 03A 掩盖主计算本身的质量问题；
- 是否出现“模型名很高级但实际只是 solver/求解架构”的角色包装；
- 是否已经预设“显著、全局最优、强鲁棒”等超出计划证据等级的论文 claim。

两次审查必须独立形成结论。若运行环境支持独立子 Agent，可并行；不支持时执行两个分离 review pass，第二次不得以第一次 verdict 为起点。

### 6.3 Challenge Gate

严重度复用现有治理：

- `blocking`：必须回到当前 Module 02 修复，用户不能用“直接批准”绕过；
- `review_required`：必须修复或给出具体、可验证的 justification 后才能继续；
- `warning`：允许保留，但必须进入 Model Approval Brief 的 residual warnings。

只有无 blocking 且所有 `review_required` 已处理后，`model_challenge_status=passed`。否则为 `revision_required`；当当前模型语义变化时旧 challenge 变 `stale`。

## 7. Human Model Approval 与正式锁模

`model_challenge_status=passed` 后，不直接进入 Python。先向用户提供简洁但完整的 Model Approval Brief，至少包含：研究对象、selected model、标准模型类型、核心变量、目标、关键约束、`preprocessing_decision`、结构化简、Solver/Validator 角色与算法适配理由、Algorithm presentation、主求解 PQS 的关键门槛、主要被否决路线理由、residual warnings 与下一阶段实际实现范围。若 4.8 适用，Brief 还应简要暴露真正会改变求解语义的精确判据、事件边界策略、缩域 evidence level、组合算子、条件式 solver probe/分支以及 surrogate→original 回算要求；不适用项不机械列空字段。

用户必须明确批准当前模型。自然语言如“OK，就按这个模型求解”“这个框架可以，进入主求解”“Q1-Q3 全部冻结”可视为批准；“我看看”“继续说”“还有别的方案吗”“这个模型怎么样”以及用户沉默不得推断为批准。

批准时在 machine state 中绑定：

```text
human_model_approval_status = approved
approved_semantic_revision = current semantic_revision
approved_semantic_hash = current semantic_hash
```

语义关系严格区分：

```text
selected_models
→ proposed_model_spec
→ Model Challenge passed
→ awaiting_model_approval
→ explicit Human Model Approval
→ locked_model_spec
```

因此 `locked_model_spec` 只能在 challenge passed 且用户明确批准当前 `semantic_revision/hash` 后成为 current。未批准时，本模块必须停在 `awaiting_model_approval`，不得交付正式预处理代码或主求解代码。

## 8. 模型语义修订、审批失效与跨问传播

`模型论文框架.md` 只保存当前有效模型，不作为第二份变更日志。Git 保存历史；`state/project_state.yaml` 记录当前语义修订号、变更类别、依赖、哈希、challenge/approval 状态和 stale。

题意解释、数据范围、变量、参数、假设、目标、约束、预处理、算法语义或小问依赖变化时递增 `semantic_revision`。对 4.8 适用的问题，精确判据、事件拓扑、候选域/缩域依据、组合算子、solver 条件分支或 original-model 回算语义发生实质变化时，应归入现有最贴近的 `constraint / assumption / algorithm / dependency / objective` 等变更类别，而不是为 v7.17 新造 Project State 枚举。

当前 `semantic_revision` 或 `semantic_hash` 改变时，旧 `model_challenge_status`、`human_model_approval_status` 与 `locked_model_spec` 同时变 stale；必须重新完成必要的语义闭环、Complexity Sanity、Model Challenge 和 Human Approval。Markdown 排版、纯措辞、图注、公式编号或不改变语义的 LaTeX 文件拆分不触发重新审批。

若已验收语义哈希变化，`scripts/validate_semantic_governance.py` 先将本问及依赖后问相关产物标记 stale。旧结果在重新求解和验收前保持 stale。代码前再由 `scripts/validate_model_approval.py` 核验 challenge/approval 与当前 revision/hash 的绑定关系。

## 9. 命题与证明规划

命题是全文级决策，不按小问机械分配。命题准入、证明作用和数量治理服从 `writing_reasoning_contract.proposition_governance`。

**0--4 是默认正文阅读预算，不是绝对上限。** 先收集真正需要证明的对象，再筛选：

- 预算内：正常规划；
- 超过 4 个：先合并同质命题、把技术引理移附录；
- 仍需超过预算：记录 `proposition_budget_status=justified` 与 `proposition_budget_reason`，说明额外命题的不可替代建模作用。

命题 ID 使用 `P1, P2, ...` 作为内部稳定追踪编号，不限制为 P1--P4。正式论文仍按章节显示“命题 4.1、命题 6.2”等。

每个保留命题记录前提/定义域、结论、证明等级、建模作用、下游计算作用、数值复核、失效边界和状态。数值复核不能替代证明。详细准入与排版只在需要时加载 `packs/artifact/proposition_proof.md`。

模型、参数、约束或定义域变化时逐个复核相关命题，不再成立则 stale。

## 10. `模型论文框架.md`

`proposed_model_spec` 形成后即可按 `templates/model/model_paper_framework.md` 建立或更新项目根目录 `模型论文框架.md`，用于承载当前模型口径、Model Challenge 和 Approval Brief；用户批准后再把当前模型状态提升为 `locked_model_spec`。框架不是批准本身，批准事实以 machine state 中绑定的当前 revision/hash 为准。

它只承担**项目级长期工作记忆**：当前题意口径、数据、变量、标准模型类型与正式模型名称、Model/Solver/Validator 角色、Formula Trace、Algorithm Trace、参数证据、Primary Quality Specification、accepted 后候选深化风险、跨问依赖、Model Challenge、Human Approval 当前状态、写作选择、小节颗粒度、命题、Citation Evidence、逐问结果摘要与 claim evidence level/scope、图表映射；对适用问题额外保存当前精确判据/事件结构、缩域 evidence level、组合语义、solver applicability 结论和 surrogate→original 回算口径。通用写作规则不得复制进去。

框架支持：

- `compact`：日常单问迭代，只保留当前有效口径、各问模型/结果、必要证据链和待办；
- `full`：跨聊天交接、整篇 DOCX/LaTeX、终审和提交，增加论文整体结构、共享基础、命题、Citation Evidence 和跨问综合。

读取规则：

1. 继续某一问前优先读取当前有效口径、该问当前模型/结果摘要、Challenge/Approval 状态和必要依赖；
2. 普通单问迭代不强制加载整份大框架；
3. 新聊天恢复、跨问综合、整篇写作和终审读取完整 current 框架；
4. 框架 stale 时先依据 project state 与已验收产物修正；
5. 具体数值回到标准工作簿核验，框架摘要不替代数值事实源。

写入规则：

- 只保留当前有效口径和项目选择；
- 口径变化时替换受影响内容，不堆“旧方案—新方案”历史；
- Model Reviewer/Devil's Advocate 只保存当前 verdict、required actions 与 residual warnings，不保存长篇历史对话；
- 设计阶段结果摘要为 pending，不填未求解数字；
- Algorithm Trace 只记录真实求解结构、角色与锚点，不复制 Python 源码或通用算法定义；
- 优化题保存 objective 现实含义与主决策对象，使摘要和正文无需从聊天记忆重建“优化什么”；
- 对 4.8 适用的问题，只保存本题实际采用的判据、事件/缩域/组合/solver 适配/原模型回算语义及证据锚点，不复制本模块的通用检查清单；
- baseline / alternative / validator 只有存在真实 artifact 时才进入框架；
- PQS 只保存本题选择的主数值有效性规格和阈值来源，不复制 `core/numerical_verification_contract.yaml` 的通用规则；
- accepted 后候选深化风险只作导航，不在主求解前生成具体分析结果；
- 通用命题、证明、语言、排版规则不写入框架；
- 正式交付前通过语义治理、Model Approval 验证和框架验证。

事实源边界：模型语义与论文组织以框架为准；修订、依赖、哈希、Challenge/Approval 状态与 stale 以项目状态为准；数值以标准工作簿为准。

## 11. 机理图合同

早期只建立合同和占位。合同说明解释对象、支撑公式/约束、必需变量、排除变量、评委需要从图中确认什么，以及无图时哪段机制难以恢复。S 级图必须绑定核心公式、约束或命题。若 4.8 的 line/ray/segment、活动边界、临界状态、量词作用域或多资源协同仅靠文字难以恢复，应优先把该关系纳入 S/A 级机理图合同，而不是另画通用流程图。

## 阶段门槛

进入项目级预处理或主求解前分两层闭合：

1. **设计完整性**：Problem Contract 已冻结；数据口径、三轴分类、标准模型类型与正式模型名称、变量/目标/约束、Model/Solver/Validator 角色、`preprocessing_decision`、语义闭环、核心 Formula Trace、必要 Algorithm Trace、Primary Quality Specification、Complexity Sanity、当前 semantic revision、命题必要性与 Citation Evidence 计划均达到本模块要求；对适用问题，4.8 的精确判据、事件结构、缩域 evidence level、组合语义、solver applicability 与 original-model reevaluation 也已进入现有闭环或明确 `not_applicable`；
2. **审批完整性**：调用 `scripts/validate_model_approval.py` 检查 current Challenge/Approval。审批状态、用户显式批准、revision/hash 绑定、blocking/review_required 处置及 stale 规则只由 `core/model_approval_contract.yaml` 定义，本模块不再复制字段级判定表。

若设计完整性已经满足但 Model Approval gate 尚未通过，形成 `proposed_model_spec`、Model Approval Brief、`awaiting_model_approval` 与 current 框架后停止；不得把“用户未反对”解释为 approval。Gate 通过后才形成 current `locked_model_spec`。若 `preprocessing_decision=project_level`，下一阶段进入 Module 03P；否则直接进入主求解。

最终 current 设计链至少形成 `proposed_model_spec`、`model_challenge`、`human_model_approval`、`locked_model_spec`、`preprocessing_decision`、`semantic_closure`、`formula_reasoning_chain`、`complexity_sanity_check`、`proposition_plan`、`citation_evidence_plan`、含 PQS 与 downstream risk hints 的 `validation_plan`，以及包含标准模型类型、Model/Solver/Validator、当前 Algorithm Trace/Challenge/Approval 状态的 current 框架；未闭环不得以代码试错代替建模。