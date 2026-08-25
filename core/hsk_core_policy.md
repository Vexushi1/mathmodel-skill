# HSK Core Policy v7.11.0

本文件只保存全局硬规则。题意口径、语义闭环和语义变更状态以 `模型论文框架.md`、`core/project_state.schema.yaml` 与 `scripts/validate_semantic_governance.py` 为准；模型挑战与人工锁模以 `core/model_approval_contract.yaml` 与 `scripts/validate_model_approval.py` 为准；目录与交付文件以 `core/output_contract.yaml` 为准；数据审计、`preprocessing_decision`、条件式统一数据预处理、预处理论文数学证据与 `data_process.m` 图证据以 `core/global_preprocessing_contract.yaml` 为准；用户本地执行与工作簿验收以 `core/user_execution_contract.yaml` 为准；题目专属 Python 工程质量以 `core/code_quality_contract.yaml` 为准；跨竞赛写作推理、Algorithm Trace、术语、数值展示、标题主张与证据治理以 `core/writing_reasoning_contract.yaml` 为准，正文结构与表达以 `modules/05_writing/latex.md` 为准。本文件不复制这些合同的完整字段。

## 1. 总目标与优先级

数学建模任务必须形成题意正确、机制闭合、数据可信、数值可复现和结果可审查的成果链。优先级为：

$$
\text{题意正确}>\text{语义与机制闭合}>\text{数据可信}>\text{完整版数值求解}>\text{结果证据}>\text{图表}>\text{论文表达}>\text{形式创新}.
$$

不能落地、不能解释、不能检验或不能复现的模型必须否决、降级或重构。运行成功、结果合理、多个算法一致都不能替代题意和模型语义正确性。

## 2. 四项前置语义治理硬规则

### 2.1 Problem Contract：题意口径冻结

进入模型设计前，每问必须冻结研究对象、原始/派生对象、已知/可计算量、决策/状态/输出量、显式/隐含约束、禁止假设、数据角色与小问依赖。不得根据附件呈现方式、已有程序、求解方便性或结果表象反推题意。关键歧义未解决时不得锁模。

### 2.2 题面—数学—代码三层闭环

每个核心对象、条件、变量、目标、约束和输出必须形成：

$$
\text{题面对象与要求}
\rightarrow
\text{数学变量/关系/目标/约束}
\rightarrow
\text{Python变量/函数}
\rightarrow
\text{工作簿输出或验证证据}.
$$

出现“题目要求有、代码没有”“代码有、数学层无来源”“数学关系无题意/机制依据”或单位、粒度、索引含义断裂时，正式代码交付必须停止。

### 2.3 模型语义修改治理

题意解释、数据范围、变量、参数、假设、目标函数、约束、`preprocessing_decision`、实际预处理、算法语义或小问依赖发生变化时，必须递增当前小问 `semantic_revision` 并记录变更类别。`模型论文框架.md` 只保留当前有效版本，历史由 Git 保存。

已验证语义发生变化时，先将受影响结果及下游标记 stale，再按 `depends_on` 的 `data / parameter / model / result` 依赖递归传播。不得因为项目存在共享数据，就无差别失效所有小问。进入论文层后，正文片段只按显式 `source_questions/depends_on` 局部传播 stale，不得把无依赖背景和独立小问机械标旧。

### 2.4 Complexity Sanity Check

复杂赛题异常退化为低维直接计算、弱耦合独立求解、动态转静态、多主体转单主体，或题目专门条件/附件字段大量闲置、关键约束长期不生效、后问近乎复制前问时，必须触发复审。无法证明简化合理时，`complexity_sanity_status=review_required`，禁止进入主求解。

上述语义治理由 `scripts/validate_semantic_governance.py` 在正式模型、代码、返回工作簿和下游交付前执行。该门不运行赛题代码、不生成数值结果，也不清除数值 stale。

### 2.5 Model Challenge 与 Human Model Approval

Problem Contract 冻结只回答“题目是什么意思”，Semantic Closure 与 Complexity Sanity 只回答“当前数学语义是否闭合、简化是否合理”，三者都不能替代正式锁模。进入项目级预处理或主求解代码前，必须按 `core/model_approval_contract.yaml` 完成相互独立的 Model Reviewer 与 Devil's Advocate 两次挑战审查；blocking 必须先修复，`review_required` 必须修复或给出具体、可验证的 justification。

Challenge passed 后必须向用户提供 Model Approval Brief，并停在 `awaiting_model_approval`。只有用户明确批准当前 `semantic_revision` 与 `semantic_hash` 后，`locked_model_spec` 才成为 current；用户沉默、模糊继续或未反对不得推断为批准。语义 revision/hash 改变时旧 challenge、approval 与 locked model 同时 stale；纯排版、措辞、caption、公式编号或不改变语义的 LaTeX 文件拆分不触发重新审批。

### 2.6 项目工作记忆与上下文恢复

`模型论文框架.md` 是当前项目的**助手可读工作记忆**，只保存当前题意口径、数据角色、`preprocessing_decision`、变量/参数/假设、核心 Formula Trace、Algorithm Trace、数值参数证据、Terminology Registry、Numeric Profile、小问依赖、当前算法语义、命题、Title Claim、Citation Evidence、paper-fragment 状态、结果摘要、验证边界、图表证据位置和本项目论文组织选择。它不得重新复制跨项目写作、证明或排版手册。

执行现有项目时采用 **read-before-use / write-after-change**：

1. 框架存在且 `current` 时，继续预处理、主求解、结果深化、绘图或单问修改前，优先读取“当前有效口径”、目标小问的当前模型/结果区和必要跨问依赖，不得仅凭聊天记忆恢复模型；
2. 新聊天接续、长上下文恢复、整篇 DOCX/LaTeX 写作、跨问综合和终审时读取完整 current 框架；日常单问工作允许定向读取相关段落；
3. 题意、数据口径、参数、假设、目标、约束、预处理、算法语义或依赖变化后，先按 semantic governance 处理 stale，再重写受影响当前内容；主结果、深化结果或图表验收后同步结果摘要和证据位置；
4. 框架只保留当前有效版本，历史由 Git 保存；
5. 具体数值必须回到已验收标准工作簿复核；`state/project_state.yaml` 负责 semantic revision、hash、依赖和 stale。

因此，框架是“当前项目事实与语义索引”，工作簿是数值事实源，project state 是机器状态源，写作规则由 writing Authority 管理；四者不得互相替代。

## 3. 数据审计、条件式预处理与论文证据

**所有数据题先审计，但不是所有数据题都要清洗或建立统一预处理工作簿。**

模型设计阶段必须形成：

```text
not_needed
question_local
project_level
```

硬规则：

1. 字段、维度、单位、主键、NaN/Inf、重复、时间/空间粒度、采样覆盖、测量质量、模型输入条件和信息泄漏风险等非破坏性审计默认执行；
2. 多问共享同一原始数据源不能单独推出需要项目级预处理；
3. 原数据满足模型要求时使用 `not_needed`，不创建 `数据预处理/`；
4. 仅某一问需要对数、标准化、滞后、窗口、专属派生特征或局部缺失处理时使用 `question_local`；
5. 只有多个小问共同依赖同一公共单位、坐标、时间、主键、采样、缺失、异常、填补、滤波或其他有依据的变换时，才使用 `project_level`；
6. 缺失填补、异常删除、插值、平滑、滤波、去噪、标准化、归一化、重采样等操作必须逐项有数据、机理或模型必要性证据；统计极端值不得直接等价为错误数据；
7. `project_level` 统一工作簿验收后，依赖该公共口径的下游脚本不得重新读取共享原始数据；
8. 任何实际改变模型输入的预处理都必须形成论文证据链：**问题证据 → 数学公式/定义 → 参数依据 → 合理性验证 → 处理前后证据 → 对后续模型的接口说明**；
9. 形式证明只用于确实可证明的等价性、守恒性、单调性、误差界或可行性保持；经验型清洗使用统计/物理/留出/人工掩蔽等可复验方法，不编造数学证明；
10. `project_level` 必须使用独立 MATLAB 脚本 `数据预处理/data_process.m` 读取 `数据预处理结果.xlsx` 中 Python 已保存的处理前后、诊断和验证数据，形成至少一张能证明预处理必要性或有效性的图；MATLAB 不重新做预处理；
11. `question_local` 若需要处理前后图证据，由对应 `qX_plot.m` 读取 Python 已输出的底层数据绘制；
12. 地震、时序、空间、传感器等题的去趋势、滤波、插值、坏道修复、taper 等均为条件操作，不得写成默认模板步骤。

`project_level` 的默认目录为：

```text
数据预处理/
├─ 数据预处理.py
├─ 数据预处理结果.xlsx
└─ data_process.m
```

完整判定、方法数学化写作深度、工作簿证据、`data_process` 图规则和 stale 规则以 `core/global_preprocessing_contract.yaml` 为唯一事实源。

## 4. 每问唯一数值交付目录

新项目每个小问只建立一个 `问题X求解/`，最终默认恰好包含：

```text
问题X求解/
├─ 问题X求解.py
├─ 问题X求解结果.xlsx
├─ 问题X结果深化分析.py
├─ 问题X结果深化分析.xlsx
└─ qX_plot.m
```

两个 Python 文件职责分离。`问题X求解.py` 只负责主求解；主工作簿 accepted 后冻结。随后单独生成 `问题X结果深化分析.py`，继承当前 `preprocessing_decision` 与数据事实源，完成题目专属深化分析。不得为了深化分析覆盖改写主求解脚本，也不得在该目录增加独立配置、运行说明、校验报告、图表目录或元数据文件。

`data_process.m` 属于项目级预处理目录，不计入每问五文件合同。

## 5. 用户执行与质量门

实际生成的 `数据预处理.py`、`问题X求解.py` 与 `问题X结果深化分析.py` 均由助手生成和静态检查、由用户本地 full-fidelity 执行。正式项目级预处理或主求解代码前，当前模型必须同时通过 semantic governance 与 model approval gate；旧审批不得覆盖新的 semantic revision/hash。

- `project_level`：预处理工作簿 accepted 且 `预处理质量门` passed 后才能进入依赖主求解；工作簿还必须持久化论文方法证据、处理前后对比和 `data_process.m` 绘图底层数据；
- `not_needed/question_local`：没有统一预处理工作簿门槛；
- 主工作簿通过当前语义、运行配置、代码/数据哈希与 `主结果质量门` 后才进入 `solved`；
- 深化工作簿通过运行配置、代码/数据哈希、`分析设计` 与 `结论稳定性汇总` 后才进入 `analyzed`。

助手不得运行、导入或间接执行题目专属预处理、主求解或深化分析脚本，不得自动缩减数据、网格、时域、场景、重复次数、迭代次数或放宽容差，也不得静默切换求解器或轻量近似。

## 6. 软件职责与写作硬边界

- Python 条件式项目级预处理：仅 `project_level` 时读取共享原始数据，执行已批准公共处理，输出 `数据预处理结果.xlsx`，同时保存论文公式参数、方法验证和 MATLAB 绘图底层证据；
- MATLAB `data_process.m`：仅 `project_level` 时读取 `数据预处理结果.xlsx` 绘制预处理证据图，不重新处理数据；
- Python 主求解：按 `preprocessing_decision` 读取原始数据或统一工作簿，完成模型求解、质量门和主工作簿；
- Python 深化分析：继承同一数据事实源，读取已验收主结果与必要前问结果，完成题目专属深化分析；
- MATLAB `qX_plot.m`：读取本问标准结果工作簿及必要数据事实源绘制各问结果图，不重新求解；完整图形规则以 `modules/04_figure_evidence.md` 为准；
- LaTeX：默认论文主链；正文结构与表达唯一权威为 `modules/05_writing/latex.md`；
- DOCX：仅用户明确要求时加载，不是 LaTeX 前置。

写作阶段这里只保留 Hard 边界，Default 与 Recommendation 不在全局政策重复定义：

1. 核心数值必须与当前已验收工作簿一致，stale 结果不得写成 current；
2. **已核验的题面、官方规则、官方评讲或评分口径要求的结果精度不得在摘要、正文或答案表中降低。** 对没有更具体评分口径的连续评分型结果，6--7 位小数属于 writing Authority 的默认高精度策略而非本全局 Hard；
3. 核心公式、命题、图表和结论必须能回到当前模型或证据链，不能以润色掩盖语义 gap；
4. 有限数值实验、交叉验证、算法一致性或求解器状态不能替代数学证明，也不能无依据把局部/启发式结果写成全局最优；
5. 外部经验参数、外部数据、领域事实、非显然标准定理和既有研究比较等需要外部来源的核心 claim，必须按 `writing_reasoning_contract.citation_evidence` 形成 Citation Evidence；本文自己的推导和工作簿结果不得用外部引用替代；
6. 正式 LaTeX 中 citation key、label/ref、图表与文献引用必须可解析，结构性缺失在交付前修复；机器不得仅凭关键词或 citation 存在推断数学正确性、定理适用性或文献是否真正支持 claim；
7. 命题 0--4 仅为默认正文阅读预算，不是 Hard 上限；优点与缺点无强制数量关系；核心模型收束按 `required / inline / not_applicable` 自适应，不能把这些经验规则升级为自动否决条件；
8. AI cleanup 只清除模板化、空泛、重复和呈现风险，不建立第二套正文规则；成稿机器审计按 `blocking / review_required / warning` 分级，warning 不阻断交付。

MATLAB 默认只保留图窗，不自动创建图表目录或批量导出正式图片。

## 7. 元数据与兼容边界

`run_info.json`、`result_manifest.yaml` 和 `matlab_figure_handoff.json` 只在用户明确要求完整复现包时生成，并放入项目级内部元数据目录，不得放入 `问题X求解/` 或 `数据预处理/`。

v7.7 及更早项目继续只读兼容；Algorithm Trace 与算法流程呈现是可选写作能力，不要求历史交付反向补写。v7.6 的 `v0.7-project-memory` 和 semantic-governance 1.0.0 仍保持只读兼容；项目重新进入当前 writing/review 流程时再按 current 框架补充需要的 Terminology/Numeric/Title/Paper Fragment/Algorithm Trace 信息。v7.2.0--7.2.2 项目重新进入模型设计、预处理、绘图或写作时，应按当前规则补齐适用的论文证据与 `data_process.m` 图证据；更早项目继续只读兼容，重新进入当前流程时先审计数据并形成判定。

## 8. 正式交付同步

- 语义治理：`scripts/validate_semantic_governance.py`；
- 条件式项目级数据预处理：`modules/03_data_preprocessing.md` + `core/global_preprocessing_contract.yaml`；
- 代码交付：`scripts/validate_code_delivery.py`；
- 用户返回工作簿：`scripts/validate_user_execution.py`；
- 图表、论文和提交包：`scripts/sync_project.py`。

同步器必须根据 `preprocessing_decision` 判断数据事实源和条件产物：`project_level` 才要求预处理脚本/工作簿/`data_process.m`；`not_needed/question_local` 不得因不存在预处理目录而失败。同步器只做发现、校验、哈希与 stale 传播，不自动生成模型语义、数据处理决策、数值结果或 passed 状态。
