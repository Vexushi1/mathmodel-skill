# Module 02：模型设计、语义闭环、复杂度复审、算法规划、命题规划与论文框架锁定

本模块负责把审题结果转成可求解、可验证、可写作的当前模型语义。跨竞赛的公式推理、Algorithm Trace、规则等级、命题预算和 Citation Evidence 由 `core/writing_reasoning_contract.yaml` 唯一定义；本模块只记录本题实际选择，不复制第二套写作规范。

## 0. 前置条件

只接受 `problem_contract_status=frozen` 的小问。若题意对象、数据角色、约束来源或小问依赖仍存在会改变答案的歧义，退回 Module 01；不得通过代码试错替代审题。

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

### 4.4 Citation Evidence 计划

只登记需要外部来源的核心 claim，例如外部经验参数、数据、领域事实、非显然标准定理、方法来源和既有研究比较。本文自己的推导和数值结果不需要外部文献代替证据。

| Claim ID | 主张/来源对象 | 类型 | Citation Key | 预期正文位置 | 状态 |
|---|---|---|---|---|---|
| C1 |  | method / theorem / parameter / data / domain_fact / prior_comparison |  |  | pending / current / stale |

设计阶段可以先标 pending；进入写作前需要外部来源的核心 claim 应闭合。

### 4.5 Algorithm Trace 与呈现模式

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

## 5. 复杂度合理性复审

模型路线锁定后、进入 Python 前检查题目复杂度是否被异常压扁。触发复审的典型 flag：

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

无法解释则 `complexity_sanity_status=review_required`，禁止进入求解。

## 6. 模型语义修订与跨问失效传播

`模型论文框架.md` 只保存当前有效模型，不作为第二份变更日志。Git 保存历史；`state/project_state.yaml` 记录当前语义修订号、变更类别、依赖、哈希和 stale。

题意解释、数据范围、变量、参数、假设、目标、约束、预处理、算法语义或小问依赖变化时递增 `semantic_revision`。

若已验收语义哈希变化，`scripts/validate_semantic_governance.py` 先将本问及依赖后问相关产物标记 stale。重新完成 Problem Contract、语义闭环和复杂度复审后才能接受新语义哈希；旧结果在重新求解和验收前保持 stale。

## 7. 命题与证明规划

命题是全文级决策，不按小问机械分配。命题准入、证明作用和数量治理服从 `writing_reasoning_contract.proposition_governance`。

**0--4 是默认正文阅读预算，不是绝对上限。** 先收集真正需要证明的对象，再筛选：

- 预算内：正常规划；
- 超过 4 个：先合并同质命题、把技术引理移附录；
- 仍需超过预算：记录 `proposition_budget_status=justified` 与 `proposition_budget_reason`，说明额外命题的不可替代建模作用。

命题 ID 使用 `P1, P2, ...` 作为内部稳定追踪编号，不限制为 P1--P4。正式论文仍按章节显示“命题 4.1、命题 6.2”等。

每个保留命题记录前提/定义域、结论、证明等级、建模作用、下游计算作用、数值复核、失效边界和状态。数值复核不能替代证明。详细准入与排版只在需要时加载 `packs/artifact/proposition_proof.md`。

模型、参数、约束或定义域变化时逐个复核相关命题，不再成立则 stale。

## 8. `模型论文框架.md`

`locked_model_spec` 形成后，以 `templates/model/model_paper_framework.md` 为骨架在项目根目录创建 `模型论文框架.md`。

它只承担**项目级长期工作记忆**：当前题意口径、数据、变量、模型、Formula Trace、Algorithm Trace、参数证据、跨问依赖、写作选择、命题、Citation Evidence、逐问结果摘要和图表映射。通用写作规则不得复制进去。

框架支持：

- `compact`：日常单问迭代，只保留当前有效口径、各问模型/结果、必要证据链和待办；
- `full`：跨聊天交接、整篇 DOCX/LaTeX、终审和提交，增加论文整体结构、共享基础、命题、Citation Evidence 和跨问综合。

读取规则：

1. 继续某一问前优先读取当前有效口径、该问当前模型/结果摘要和必要依赖；
2. 普通单问迭代不强制加载整份大框架；
3. 新聊天恢复、跨问综合、整篇写作和终审读取完整 current 框架；
4. 框架 stale 时先依据 project state 与已验收产物修正；
5. 具体数值回到标准工作簿核验，框架摘要不替代数值事实源。

写入规则：

- 只保留当前有效口径和项目选择；
- 口径变化时替换受影响内容，不堆“旧方案—新方案”历史；
- 设计阶段结果摘要为 pending，不填未求解数字；
- Algorithm Trace 只记录真实求解结构与锚点，不复制 Python 源码或通用算法定义；
- 通用命题、证明、语言、排版规则不写入框架；
- 正式交付前通过语义治理和框架验证。

事实源边界：模型语义与论文组织以框架为准；修订、依赖、哈希、stale 以项目状态为准；数值以标准工作簿为准。

## 9. 机理图合同

早期只建立合同和占位。合同说明解释对象、支撑公式/约束、必需变量、排除变量、评委需要从图中确认什么，以及无图时哪段机制难以恢复。S 级图必须绑定核心公式、约束或命题。

## 阶段门槛

进入求解前必须满足：

1. `problem_contract_status=frozen`；
2. 数据口径、objective、structures、capabilities、变量、目标、约束、求解器候选、评价指标和验证方案已锁定；
3. `preprocessing_decision` 已锁定；
4. 题面—数学—代码—输出无关键 gap，`semantic_closure_status=passed`；
5. 核心 Formula Trace closed，影响结论的数值参数已有证据计划；
6. 需要正式算法流程的问已确定 `stepwise/pseudocode` 并建立可追溯 Algorithm Trace；简单问题允许 `not_needed`；
7. `complexity_sanity_status=passed`；
8. `semantic_revision` 与当前框架一致；
9. 已完成命题必要性初审；若超过默认 0--4 预算，已记录 justification 状态和理由；
10. 需要外部来源的核心 Citation Claim 已登记，进入写作前必须闭合。

若 `preprocessing_decision=project_level`，下一阶段进入 Module 03P；若为 `not_needed` 或 `question_local`，跳过 Module 03P 直接进入主求解。

形成 `locked_model_spec`、`preprocessing_decision`、`semantic_closure`、`formula_reasoning_chain`、`complexity_sanity_check`、`proposition_plan`、`citation_evidence_plan`、`validation_plan` 与包含当前 Algorithm Trace 的 current 框架；未闭环不得以代码试错代替建模。
