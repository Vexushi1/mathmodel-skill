# Module 03B：条件式独立结果深化分析代码

本模块只接受已验收的主工作簿，但**不是每个已验收主结果都必须进入本模块**。在生成任何 独立深化入口 之前，先执行 Analysis Necessity Gate：根据题目/用户显式要求、建模阶段遗留的 material risk、真实主结果边界性以及准备写入论文的 claim，判断当前小问是否确实需要改变参数、场景、seed、初值、算法、模型结构或验证窗口，建立一个新的计算世界来检验结论稳定性。

若 Gate 判定 `required`，再根据真实主结果选择参数敏感性、场景压力、多算法/多初值、结构稳健性、阈值、异质性、误差分解或外样本稳定性。若 current `模型论文框架.md` 已存在，制定分析计划前先读取本问当前模型、验证方案、主结果摘要、适用/失效边界和跨问依赖，再用已验收主工作簿复核具体数值；不得脱离框架按聊天印象选择分析对象。

若 Gate 判定 `not_required`，不得为了“流程完整”生成空洞的敏感性/鲁棒性代码、工作簿、图表或正文小节。必须在当前项目状态与 `模型论文框架.md` 中记录具体理由；`not_required` 只表示当前题目答案和计划中的正文主张不需要 alternative-world 证据，**绝不等价于“模型已通过稳健性检验”**。后续一旦新增“稳定、鲁棒、对参数不敏感、跨场景有效、替代算法一致”等超出主计算世界的 claim，必须重新打开本 Gate，并在需要时转为 `required`。

v7.14 起，`core/numerical_verification_contract.yaml` 只负责主工作簿 accepted 之前的**当前主计算内在数值有效性**。本模块继续独占主工作簿 accepted 后的参数敏感性、压力场景、替代算法/结构、多随机种子或多初值稳健性、阈值与失效边界、异质性、误差分解及广义外样本稳定性；这些内容**不得被主求解质量门提前吸收**，也不得为了让主工作簿“看起来验证充分”而预先塞回 主求解入口。

如果某个主算法按其数学定义本身需要多起点、多随机种子或内部重复才能完成一次主求解，这些运行可以留在 03A 的主算法内部；但一旦问题变成“不同 seed / 初值 / 替代算法下结论是否保持”，就属于本模块，并必须在 accepted 主工作簿之后先经过 Analysis Necessity Gate，再在 `required` 时形成 `result_analysis_plan`。

数据事实源必须继承当前 `preprocessing_decision`，不得在深化分析阶段重新决定数据清洗口径：

- `not_needed`：可读取必要原始数据 + 已验收主工作簿；
- `question_local`：可读取必要原始数据，并仅复现本问数学层已经定义的局部变换；
- `project_level`：读取 `数据预处理/数据预处理结果.xlsx` + 已验收主工作簿，禁止再次直接读取对应共享原始数据。

## 一、Analysis Necessity Gate

在 accepted 主工作簿之后、生成 03B 代码之前，对当前小问给出 `required / not_required` 二选一结论。以下任一 material 条件成立时，原则上应判定 `required`：

- 题目、竞赛要求或用户明确要求敏感性、鲁棒性、压力场景、替代算法/结构、阈值、异质性、外样本或稳定性检验；
- `validation_plan` 中存在 accepted 后才能检验、且会影响核心答案或论文主张的 residual risk；
- 正文准备声称结果“稳定、鲁棒、不敏感、跨场景有效、算法一致、结构选择不影响结论”等，而主工作簿只证明当前计算世界；
- 核心决策/排名/阈值紧贴约束、事件或切换边界，轻微合理扰动可能改变题目答案；
- 随机、非凸、多起点或启发式方法的**结论稳定性**本身是需要证明的对象，而不是主算法一次运行的内部组成；
- 真实主结果暴露出异常敏感、边界不清、替代结构可疑或需要外推的高风险信号。

只有在以下条件同时满足时，才可判定 `not_required`：主工作簿的内在数值有效性已通过；题目直接答案不依赖 alternative-world 证据；当前 `validation_plan` 没有未关闭的 material 03B 风险；计划中的正文 claim 不超出当前计算世界。判定时必须记录非空 `result_analysis_requirement_reason`，并同步当前 `模型论文框架.md` 的候选深化风险/待办；不能把“时间不够”“不想多算”或“主结果看起来正常”作为理由。

兼容语义：旧项目 `result_analysis_status=passed` 保持原义；`pending/failed/redo_required` 不变；新增 `not_required` 只表示 Gate 明确裁定无需 03B。它不生成伪 `result_analysis_workbook`，也不冒充 `accepted_result_analysis_workbook`。下游只在“accepted 主结果 + 有理由的 `not_required`”或“accepted 03B 工作簿 + `passed`”两种情况下获得 `validated_results`。

## 二、执行规则

Gate=`required` 后按 `core/user_execution_contract.yaml#solver_backends` 继承项目根唯一求解后端，不在 03B 另选语言。独立入口名称来自输出 Authority；03B 使用 1.1 配置/回执与独立源码 bundle。读取 accepted 主工作簿前由共享前提检查核对主代码与数据身份，不能通过调用主入口重新计算主结果。主阶段的执行状态不被深化阶段覆盖；`RUN_CONFIG` 与回执中的 backend 记录实际运行事实，须与项目策略一致。

`required` 分支：

```text
主工作簿accepted
→ 冻结主求解入口及其源码依赖
→ Analysis Necessity Gate = required
→ 继承preprocessing_decision与当前数据事实源
→ 基于真实主结果建立result_analysis_plan
→ 为每项计划声明target claim与判定准则
→ 按项目根后端新建本问独立深化入口
→ 读取当前数据事实源 + 已验收问题X求解结果.xlsx + 必要前问标准工作簿
→ validate_code_delivery.py静态验收analysis阶段代码
→ 用户本地full_fidelity运行
→ 同目录问题X结果深化分析.xlsx
→ validate_user_execution.py验收
→ 对每项证据给出support / modify / reject
→ analyzed或redo_required
```

`not_required` 分支：

```text
主工作簿accepted
→ 冻结主求解入口及其源码依赖
→ Analysis Necessity Gate = not_required
→ 记录result_analysis_requirement_reason并同步模型论文框架
→ 不生成03B代码/工作簿/分析图
→ 下游只使用accepted主工作簿支持当前计算世界内的claim
```

独立深化入口 是独立可复现程序，不复制主求解主链，不通过改写 主求解入口 实现深化分析。新生成脚本必须只定义一个按执行 Authority 可静态读取的 `RUN_CONFIG`，其中 `stage="analysis"` 并锁定当前数据事实源的 `data_sha256`；user/full-fidelity/no-degradation 政策由 `core/user_execution_contract.yaml` 继承，不在脚本中重复自报。工作簿中的 `code_sha256` 必须对应该深化分析脚本，并继续完整记录 solver/version、stop、platform、fallback 与 no-degradation 等实际运行事实。旧 `FULL_FIDELITY_CONFIG/FULL_RUN_CONFIG` 仅作只读兼容。

## 三、按需多模型检验与同模型多算法检验

两类新检验沿用本模块的 Analysis Necessity Gate、独立 analysis 入口、项目唯一 backend 和现有处置，不要求每问两个模型。

| 类型 | 保持与改变的对象 | 专项证据表 |
|---|---|---|
| `model_comparison` | 保持题目对象、合法数据事实源和共同评价问题；比较至少一个有实质数学差异的合理模型 | `多模型检验` |
| `algorithm_comparison` | 保持原始数学模型、现实参数、目标和硬约束；比较至少两个不同真实求解方法 | `同模型多算法检验` |

同算法换 seed、初值、容差或函数名不单独计为多算法；不同模型名字不证明模型不同。同一方程改变离散或积分算法通常属于求解方法变化，增加物理机制才可能属于模型变化。等价 reformulation 必须保留原模型映射与回算。两模型一致只提供指定范围内的交叉佐证；不同模型产生差异也不自动否决主模型。

Module 02 的 Comparator 按具体比较问题关联稳定检验 ID。数学／算法比较规范置于框架 `#### 结果摘要` 之后的独立 `HSK_ANALYSIS_COMPARISON_BEGIN/END Qn` marker，不能混入主 SIB 或主语义哈希区。规范、范围审查和批准服从 `core/model_approval_contract.yaml`；当前主身份仍须 current = validated = approved。比较范围变化只失效该范围及 analysis 链，主模型真正变化才按原语义治理使主批准和结果失效。

主工作簿 accepted 后，在现有 `analysis_comparison.checks` 中冻结本次具体检验、对象引用、共同评价、判据和预期证据选择器。`required` 项必须逐项执行并形成真实非空证据及 disposition；敏感性或另一张实质表不能替代它。`exploratory` 未完成不阻塞当前必要答案，但不得写成已验证。仍有 current required 项时不得整体 `not_required`；明确题目／用户要求和未关闭核心风险不能因计算失败撤销。

配置与回执扩展仅按 `core/user_execution_contract.yaml` 激活；计划摘要排除实际结果和运行后处置，主簿和源码身份继续使用现有绑定。机器能核对规范一致性、有限指标算术、覆盖和来源，不能从名称自动证明数学等价、算法独立性或模型正确性。

每次真实子运行保留模型／算法、实例或重复、指标、单位、实际设置、停止原因及必要可行性／残差／时间；表列与 MATLAB 交接只由 `core/workbook_schema.yaml` 定义。共同评价须声明输出映射、因果合法划分、单位、方向和判据；不同目标函数不能直接相减。性能主张还需要适用预算、硬件和重复记录。只写固定比较数字或“通过”不构成执行证据。

有效的负比较结果属于实验发现。技术失败、缺行、不可比数据或身份不符不能冒充 `reject` 或已完成。`modify` 或附加 claim 的 `reject` 可完成检验，但关联正文保持 stale，直到具体动作完成；核心答案／模型有效性 `reject` 按现有核心否证规则 `redo_required` 并回退。

## 四、Analysis Evidence Disposition

深化分析的每一项敏感性、鲁棒性、外样本、压力测试、多算法或多初值证据都必须说明它**作用于哪个具体主张**，并给出以下三种 disposition 之一：

- `support`：目标主张在该检验下保持，可作为正文增强证据，但不得自动扩大适用范围；
- `modify`：目标主张主体仍可使用，但区间、阈值、置信度、排序、边界或文字必须修改，并使依赖的 paper fragments 在完成同步前保持 stale；
- `reject`：目标主张不能继续原样使用。若否决的是核心答案、核心模型结构或关键可行性判断，必须 `redo_required` 并按原因回退；若只是否决一个附加的“稳定性很强”等非核心 claim，可以删除/重写该 claim，而不强迫整题重算。

显式采用 B2 `1.4.0/enforce_latex_text_and_figure_chain` 或 `1.5.0/enforce_selected_paper_claim_chain` 时，current 的 `modify/reject` 还必须记录 `impact_scope`，不得从 `target_claim` 或 `required_action` 自由文本猜测。`reject/core_answer` 精确声明 `return_stage=solve_validate`；`reject/model_validity` 精确声明 `return_stage=model_design`；`auxiliary_wording` 和 `modify` 不得携带 `return_stage`。若多个否证并存，`model_design` 优先。

每项证据至少记录：

```text
Evidence ID
→ method/source
→ target claim
→ disposition
→ impact scope（B2 1.4.0/1.5.0 current modify/reject）
→ return stage（仅核心 reject）
→ key finding
→ required action
→ paper/figure anchor
```

禁止只写“通过敏感性分析验证了模型稳定性”而不说明：分析了什么、支持/修改/否决了哪个主张、变化范围多大以及正文应怎样处理。

## 五、Analysis Evidence Capture：深化分析必须保留可复查的底层结果

03B 不得只输出“稳定”“变化不大”“算法一致”等摘要结论。只要本次深化分析已经真实产生逐参数、逐场景、逐 seed、逐算法、逐区域、逐阈值或逐样本结果，就应在分析工作簿中保留足以复核结论和直接供 MATLAB 绘图的细粒度证据。

典型底层结构包括：

- `参数值 × 结果指标 × 可行状态`，必要时附基准值、变化率、弹性或统计量；
- `场景ID × 变化条件 × 结果指标 × 是否可行/失败标记`；
- `算法 × 实例/重复编号 × 目标值 × 运行时间 × 可行性 × gap`；
- `seed/初值 × 结果 × 排名/策略 × 是否保持主结论`；
- `区域/对象 × 参数/场景 × 响应`；
- 阈值扫描中的当前值、临界前/后状态、策略切换、约束激活和失效标记；
- 外样本稳定性中的窗口/年份/地区/迁移场景、样本量、指标和相对变化；
- 误差分解中的误差来源、对象/时间/场景与对应数值，而不是只给总占比。

如果分析过程内部已经形成更细粒度记录，优先保留能够支撑正文、Figure、QA 或复现的那一层；不保存纯 debug 噪声，也不为“图更丰富”额外制造未执行的实验。

这条规则的目的，是让 Figure Evidence 阶段可以直接从 accepted 工作簿构造稳定区、阈值边界、ECDF、箱线/小提琴+散点、Small Multiples、Pareto/性能剖面等科研图，而不在 绘图阶段重新运行分析。

## 六、数据与模型边界

数据处理边界：

- `project_level` 项目不得重复公共去缺失、异常处理、单位换算、统一滤波、统一重采样或坐标修正；
- `question_local` 项目只能复现当前小问已有数学来源的局部变换，不得新增全局清洗；
- `not_needed` 项目不得为了深化分析方便而擅自补值、删异常、平滑或滤波。

若深化分析发现公共数据处理口径本身导致结论不稳定，且当前为 `project_level`，应回退 `data_preprocessing`；若发现 `not_needed/question_local` 的判定本身错误，则回退 `model_design` 修改 `preprocessing_decision`；若发现模型语义问题，则回退 `model_design`；若仅主求解数值质量不足，则回退 `solve_validate`。任何回退都必须按依赖传播下游 stale。

若核心结论未保持，必须回退相应阶段并标记真实依赖的下游 stale。默认不生成独立运行配置、运行说明或校验报告。


### 可选 A2 一致性绑定

仅当本问本阶段显式启用 A2 时，现有交付/回执与同步流程消费 `core/model_code_conformance_contract.yaml#activation.integration`。结构核验不代替模型批准、真实运行或数值质量；不支持或待审查的结构不得伪装通过，未启用的项目维持原流程。
