# HSK Core Policy v9.7.1

本文件只定义**跨阶段硬不变量**。任何阶段的目录、字段、工作表、图型、论文小节、算法展示、兼容迁移或工具参数，均以 `core/bootstrap.yaml` 指向的 current Authority 为准；本文件不复制这些阶段合同的完整实现。

主要 Authority：题意与语义治理 `modules/01_problem_audit.md`、`modules/02_model_design.md`、`scripts/validate_semantic_governance.py`；模型挑战与人工锁模 `core/model_approval_contract.yaml`；项目状态与 typed stale `core/project_state.schema.yaml`、`core/state_transition_contract.yaml`；数据与预处理 `core/global_preprocessing_contract.yaml`；目录与交付 `core/output_contract.yaml`；用户执行 `core/user_execution_contract.yaml`；主数值有效性 `core/numerical_verification_contract.yaml`；结果深化 `modules/03_result_analysis.md`；科研图 `modules/04_figure_evidence.md`；复杂写作语义 `core/writing_reasoning_contract.yaml`；普通正文 `modules/05_writing/paper_writing_protocol.md`；写作运行时 `core/writing_runtime_contract.yaml`；最终审查 `modules/06_review_delivery.md`。

## 1. 总目标与优先级

数学建模成果必须同时做到题意正确、机制闭合、数据可信、数值可复现、证据可审查。优先级为：

$$
\text{题意正确}>\text{语义与机制闭合}>\text{数据可信}>\text{完整版数值求解}>\text{结果证据}>\text{图表}>\text{论文表达}>\text{形式创新}.
$$

不能落地、不能解释、不能检验或不能复现的模型必须否决、降级或重构。运行成功、结果看似合理、多个算法给出相近答案，都不能替代题意与模型语义正确性。

## 2. 题意、模型与批准

1. **先冻结题意，再从条件生成结构。** 每问先形成 current Problem Contract，明确研究对象、已知/可计算量、状态/决策/输出、约束、禁止假设、数据角色和跨问依赖。关键歧义会改变对象、变量、约束或结论时不得锁模。Problem Contract 冻结后，在提出模型名称和 solver 之前，必须优先把题面条件、定义、守恒/不变量、几何/时间/网络/随机结构转成数学后果，判断可消元、降维、分解、排序、边界化、充分状态或等价变换；不得把题面条件只当作附加约束后直接进入通用算法。
2. **主模型以最小充分为目标，不以复杂为目标。** 在完整回答题意、保留关键机制、满足约束/精度/输出要求的前提下，优先选择不能再合理降低变量、自由度、机制或计算复杂度而不损失必要信息的当前主模型。高级模型可以作为主模型或 comparator，但必须说明它增加了哪一个必要机制或比较信息；“更高级”“更复杂”本身不是准入理由。
3. **精确化简和已证明充分的缩减优先于算法升级。** 可逆等价、定义/守恒消元、严格对称降维、已证明保留所需最优/临界/可行对象的缩减，应先于元启发式、深度学习或大规模通用 solver。启发式缩域、surrogate 或近似必须保留适用范围、被舍弃信息和 claim boundary。具体 Reduction Provenance 语言与证据边界服从 current writing reasoning Authority。
4. **Solver 服从结构，而不是反向塑造模型。** 先完成问题本体、条件后果、结构化简和当前主模型，再选择解析/结构算法/稀疏或低维数值法/通用 solver。不得因为熟悉某算法而保留本可消掉的变量、把可排序问题写成组合暴搜，或把凸/树/DAG/带状等结构丢给不必要的黑箱算法。
5. **题面—数学—代码—输出必须闭环。** 核心对象、公式、约束和结论必须有可追溯来源；“题目要求有而代码没有”“代码对象无数学来源”“单位/粒度/索引断裂”等 hard gap 未关闭时不得正式交付代码。
6. **复杂度异常退化必须复审。** 复杂题被无依据降成低维直接计算、弱耦合、静态或单主体问题，或者题目专门条件长期闲置时，必须触发 Complexity Sanity Check；无法证明简化合理时不得进入主求解。该检查是安全网，不替代前述条件驱动的生成式结构发现。
7. **Problem Contract、Semantic Closure 与 Complexity Sanity 都不能替代 Model Approval。** 进入项目级预处理或当前主求解代码前，必须完成独立 Model Reviewer、Devil's Advocate 和显式 Human Model Approval。
8. **批准只绑定 current structured identity。** 只有用户明确批准当前 `semantic_revision` 与已验证 `semantic_identity_hash`，且 current = validated = approved identity 后，`locked_model_spec` 才成为 current。legacy semantic hash 只保留只读 provenance，不能授权新的项目级预处理或主求解。
9. **语义变化必须失效真实依赖。** 题意、数据口径、参数、假设、目标、约束、预处理、算法语义或跨问依赖改变时，按 current state/transition Authority 更新 revision 并传播 typed stale；不因“保险起见”无差别失效独立问题，也不以纯排版/SIB 外措辞变化冒充模型变化。

上述字段、状态和验证细节只服从对应 Authority；`scripts/validate_semantic_governance.py` 与 `scripts/validate_model_approval.py` 是 current 机器门，不由本文件维护第二套检查清单。

## 3. 项目事实源与上下文

项目中必须区分四类事实：

- `模型论文框架.md`：current 项目语义与助手可读工作记忆；
- accepted 标准工作簿：具体数值事实；
- `state/project_state.yaml`：revision、structured identity、artifact hash、依赖、stale 与机器状态；
- 活动 Authority：跨项目方法、写作、绘图、执行和交付规则。

四者不得互相替代。继续现有项目时必须 **read-before-use / write-after-change**：使用 current 框架恢复目标小问和必要依赖，具体数值回到 accepted workbook，状态判断回到 project state；语义、结果或图表验收发生真实变化后，只同步受影响 current 内容。聊天记忆不能覆盖 current 项目事实。

P2 `reading_plan` 可以缩小本轮初始阅读范围，但不能缩小机器依赖、审批、质量门或真实失效范围；证据不足、语义不清或来源漂移时应扩大读取而不是猜测。

## 4. 数据、执行与数值证据

1. **所有数据题先审计，但不是所有数据题都清洗。** `preprocessing_decision` 只允许 `not_needed / question_local / project_level`，具体判定、操作证据与公共数据源边界由 `core/global_preprocessing_contract.yaml` 唯一定义。共享数据、缺失值或历史经验本身都不能自动推出项目级预处理。
2. **任何改变模型输入的数据处理都必须有必要性与验证证据。** 不得为了曲线更平滑、结果更好看或流程更完整而补值、删异常、滤波、平滑、标准化、重采样或改变时间因果。
3. **题目专属计算代码由用户本地 full-fidelity 执行。** 助手可以生成、静态检查和验收返回 artifact，但不得导入、运行或间接执行赛题预处理、主求解或结果深化脚本；不得自动缩减数据、网格、时域、场景、重复次数、迭代次数、放宽容差或静默切换 solver/近似。
4. **主求解只回答当前计算能否 accepted。** Primary Quality Specification、Verification ID、残差、可行性、离散/收敛和其它主数值证据只用于判断当前 locked model 与声明数值方法下的本次计算是否有效；参数敏感性、压力场景、替代算法/结构、多 seed/初值结论稳定性、异质性和广义 claim stability 属于 accepted 之后的独立结果深化分析。
5. **Primary Evidence Capture 只保存当前运行真实产生的高价值状态。** 不能为了图或分析改变参数、场景、seed、初值、算法、结构或验证窗口去制造另一个计算世界。
6. **预期身份与实际执行证据都要保留。** 代码/数据指纹、实际停止原因、真实运行范围与质量证据按 user-execution / numerical-verification Authority 核验；工作簿自行写出的 `passed` 不能替代机器可复算证据。
7. **绘图入口只做证据可视化。** `data_process.m` 与 `qX_plot.m` 不重新预处理、求解或生成未执行的敏感性/稳健性结论；具体 Figure Evidence 规则只读 `modules/04_figure_evidence.md`。

具体目录、工作簿字段、每问文件集合与 stage requirements 只由 `core/output_contract.yaml`、`core/workbook_schema.yaml` 和相应 Module 定义，不在全局政策重复维护。

## 5. 论文、图表与结论边界

1. 正式论文只能使用 current 模型、accepted 数值和已确认图表。stale 结果不得写成 current，不能用润色或版式掩盖语义/证据 gap。
2. 已核验题面、官方规则、官方评讲或评分口径要求的结果精度不得降低；没有更具体要求时的默认数字样式只服从 writing Authority。
3. 核心公式、命题、算法、图表和结论必须可回到当前模型或证据链。有限数值实验、交叉验证、算法一致性或 solver 状态不能替代数学证明，也不能无依据把局部/启发式结果升级为全局结论。
4. 外部经验参数、外部数据、领域事实、非显然标准定理和既有研究比较等需要外部来源的核心 claim，必须形成 Citation Evidence；本文自己的推导和 accepted workbook 结果不得用外部引用代替。
5. 图表只组织已有证据，不制造新数据、新统计量或新结论；正式批准仍需要真实渲染/语义审查，静态代码检查不能替代视觉验收。
6. CUMCM 固定结构、普通段落组织、Formula/Algorithm Trace、命题、solver justification、Claim Strength、逐问 Preflight、AI cleanup 和 LaTeX Adapter 分别服从 current 写作 Authority；consumer 不得复制出第二套正文规则。DOCX 仅在用户明确要求相应载体时加载。

## 6. 交付、同步与兼容

1. `scripts/resolve_runtime.py` 返回的 `pre_delivery_gates` 是本次正式交付的完整有序机器门；必须按顺序真实执行并检查报告。读取更少、文件存在或 ZIP 生成都不等于 gate 已通过。
2. `scripts/sync_project.py` 只做发现、Schema/哈希核验与 stale 传播，不自动生成模型语义、数据处理决策、数值结果或 `passed` 状态。
3. 最终审查、LaTeX audit/compile attestation 与 submission package 只服从 `modules/06_review_delivery.md`、`core/output_contract.yaml` 及 resolver 当前返回的 gate；未核验赛事规则不得伪装成官方 Hard 要求。
4. 旧项目、旧字段和 legacy artifact 的兼容只按各 Authority 的显式 compatibility 条款读取；历史 accepted 记录不要求批量迁移，但重新进入 current 模型设计、预处理、主求解、写作或终审时，按该阶段 current contract 补足需要的信息。`legacy/` 不能成为活动执行依赖。

## 7. Authority 导航

| 主题 | 唯一/主 Authority |
|---|---|
| 审题与 Problem Contract | `modules/01_problem_audit.md` |
| 模型、语义闭环、复杂度复审 | `modules/02_model_design.md` + `scripts/validate_semantic_governance.py` |
| Model Challenge / Human Approval | `core/model_approval_contract.yaml` |
| 状态、依赖与 typed stale | `core/project_state.schema.yaml` + `core/state_transition_contract.yaml` |
| 数据审计与预处理 | `core/global_preprocessing_contract.yaml` |
| 目录与正式产物 | `core/output_contract.yaml` |
| 工作簿结构 | `core/workbook_schema.yaml` |
| 用户本地执行 | `core/user_execution_contract.yaml` |
| 主数值有效性 | `core/numerical_verification_contract.yaml` |
| 主求解 / 当前运行证据 | `modules/03_solve_validate.md` |
| accepted 后结果深化 | `modules/03_result_analysis.md` |
| 科研图与机理图 | `modules/04_figure_evidence.md` |
| 跨竞赛复杂写作语义 | `core/writing_reasoning_contract.yaml` |
| 普通正文组织 | `modules/05_writing/paper_writing_protocol.md` |
| 写作运行时与 Preflight | `core/writing_runtime_contract.yaml` |
| 最终审查与交付判定 | `modules/06_review_delivery.md` |

出现冲突时，先按 `core/bootstrap.yaml` 确认 current Authority，再修复事实源或调用链；不得通过在本文件继续复制阶段细节来“保持一致”。
