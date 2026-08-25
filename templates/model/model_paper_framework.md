# 模型论文框架

> 本文件只保留**当前有效项目事实、选择、状态与证据位置**。历史由 Git 保存。
> 通用写作规则不在这里重复：推理与证据治理见 `core/writing_reasoning_contract.yaml`，正文结构与表达见 `modules/05_writing/latex.md`。
> 具体数值必须回到已验收标准工作簿复核；semantic revision、hash 与 stale 以 `state/project_state.yaml` 为准。

- 项目：`__PROJECT__`
- 竞赛与题号：`__COMPETITION_AND_PROBLEM__`
- 框架版本：`v0.8-project-memory`
- 框架模式: full
- 当前阶段：`审题 / 模型设计 / 求解 / 验证 / 绘图 / 写作 / 终审`
- 最近同步：`__LAST_SYNC_SCOPE__`
- 最近同步时间：`__ISO_DATETIME__`
- 当前状态：`current / stale`

## 当前有效口径

### 题目对象与核心关系

- 研究对象：
- 核心问题：
- 显式约束：
- 隐含约束：
- 禁止假设：
- 统一单位与精度：
- 核心答案是否属于高精度评分项：`yes / no / unknown`
- 若 yes，题目/评委/竞赛要求的小数位或有效位数：

### 全局数据协议

| 数据源 | 文件/工作表 | 字段与单位 | 时间/空间粒度 | 关联键 | 数据角色 | 当前处理口径 |
|---|---|---|---|---|---|---|
|  |  |  |  |  | 输入/标定/验证/边界/结果观测 |  |

### 全局符号、参数与共享假设

| 符号/参数 | 类型 | 含义 | 单位 | 当前值/范围 | 来源与有效边界 |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

### Terminology Registry

> 只登记本项目真正会反复使用、容易混淆或与符号强绑定的技术术语；不建立通用词典。

| Term ID | 标准术语 | 定义 | 量纲/单位 | 允许简称 | 不建议别名 | 易混术语 | 对应符号 | 适用范围 | 状态 |
|---|---|---|---|---|---|---|---|---|---|
| T1 |  |  |  |  |  |  |  |  | current / stale |

### Numeric Profile

> 核心答案默认优先保留可评分的高精度。若小数后 6--7 位可能影响结果分，摘要、正文直接答案和关键结果表均保留相应精度，不因“摘要简洁”擅自降精度。

| Metric ID | 标准指标 | 符号 | 单位 | 展示形式 | 摘要精度 | 正文精度 | 表格精度 | 提交/决策精度 | 评分精度依据 |
|---|---|---|---|---|---|---|---|---|---|
| N1 |  |  |  | decimal / percent / scientific / interval |  |  |  |  | prompt / official / reviewer / model_resolution |

- 单位间距约定：
- 百分比与百分点口径：
- 科学计数法约定：
- 均值 ± 标准差格式：
- 置信区间格式：
- 坐标/时间/优化变量高精度要求：

### 各问依赖关系

| 小问 | 直接目标 | 隐含目标 | 依赖前问 | 依赖类型 | 输出交付 | 当前状态 |
|---|---|---|---|---|---|---|
| Q1 |  |  |  | data / parameter / model / result / independent |  |  |

## 论文整体框架

### 论文题目候选

1. 
2. 

- 选定题目：

#### Title Claim Gate

| Claim ID | 标题核心主张 | 类型 | 对应小问 | 正文锚点 | 结果证据 | 摘要位置 | 关键词链接 | 状态 |
|---|---|---|---|---|---|---|---|---|
| TC1 |  | research_object / main_method / core_mechanism / core_contribution |  |  |  |  |  | pending / current / stale |

### 摘要组织

- 总述：研究对象、统一建模路线：
- Q1：模型/关键结构—高精度决定性数值—直接判断：
- Q2：
- 其他小问：
- 综合检验：
- 每问摘要保留的决定性数值/区间/阈值：
- 摘要核心答案是否按 Numeric Profile 保留评分所需精度：
- 标题核心主张是否在摘要中得到真实反映：
- 关键词是否与选定标题及正文主模型一致：

### 当前写作选择

> 这里只记录**本项目的实际选择**，不抄写通用规则。

1. 正文总体结构：
2. 共享基础与跨问递进：
3. 假设、数据说明与预处理位置：
4. 公式推导重点与普通代数压缩范围：
5. 各问核心模型收束状态：`required / inline / not_applicable`：
6. 各问算法流程呈现状态：`not_needed / stepwise / pseudocode`：
7. 求解、结果、局部验证和深化证据布局：
8. 命题/证明、Citation Evidence、Terminology 与 Numeric Profile 的使用位置：
9. 特殊结构例外（独立结论、对象图、问题关系图等）及依据：

### 共享基础与跨问增量

- 共享基础状态：`不需要 / 首次使用处定义 / 独立章节`
- 涉及小问：
- 真正共享的对象/状态/方程/概率或网络结构：
- 最终章节名与位置（若单列）：

| 小问 | 继承结构 | 新增对象/条件 | 新增数学结构 | 困难变化 | 求解变化 |
|---|---|---|---|---|---|
| Q1 | independent / shared foundation |  |  |  |  |

### 核心公式 Trace

> 只记录决定模型结构、约束、判定、参数或结论的核心关系；普通代数中间式不登记。

| Formula ID | 对应小问 | Source | Depends on | Derivation | Destination | 代码/证据锚点 | 状态 |
|---|---|---|---|---|---|---|---|
| F1 |  |  |  |  |  |  | closed / gap / stale |

### Algorithm Trace

> 仅当某问 `algorithm_presentation=stepwise/pseudocode` 时登记。Trace 保存真实求解结构与锚点，不复制 Python 源码或通用算法知识。

| Algorithm ID | 小问 | 作用 | 输入/状态 | 核心操作 | 循环/分支/阶段 | Formula/Proposition/Constraint 锚点 | 终止条件 | 输出 | Python 锚点 | 呈现模式 | 状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A1 |  |  |  |  |  |  |  |  |  | stepwise / pseudocode | current / stale |

### 数值参数依据

| 参数 | 对应小问 | 数学作用 | 候选范围 | 选择证据 | 最终取值 | 主结果稳定性 |
|---|---|---|---|---|---|---|
|  |  |  |  |  | pending | pending |

### Citation Evidence

> 只登记需要外部来源的核心 claim；本文自己的推导和工作簿结果不靠外部引用替代证据。

| Claim ID | 主张/来源对象 | 类型 | Citation Key | 正文位置 | 状态 |
|---|---|---|---|---|---|
| C1 |  | method / theorem / parameter / data / domain_fact / prior_comparison |  |  | pending / current / stale / not_required |

### 命题与证明规划

- 当前计划命题数：0
- 默认正文预算：0--4
- 超预算状态：`not_applicable / justification_required / justified`
- 超预算说明（若适用）：
- 当前命题状态：`not_assessed / planned / current / stale`

| 命题ID | 对应小问 | 名称与类型 | 前提/定义域 | 核心结论 | 证明等级 | 下游模型/计算作用 | 失效边界 | 状态 |
|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  | A / B / C |  |  | candidate / current / stale / removed |

### 正文章节与交付映射

| 题目要求 | 论文位置 | 核心模型/公式 | Algorithm | 命题 | Python | 工作簿/工作表 | MATLAB 图表 | Citation | 本问答案 |
|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |  |

### Paper Fragment Dependency Map

> 用于局部 stale 传播。`paper_framework.sync_status=current` 只表示本框架已同步记录当前状态，不代表下面所有 fragment 都 current。进入模块化 LaTeX 写作后，可为 fragment 记录对应物理源码文件；旧单文件项目或尚未进入 LaTeX 阶段时允许留空。

| Fragment ID | 类型 | 范围 | 依赖对象 | 正文/摘要锚点 | LaTeX 源码文件（可选） | 状态 |
|---|---|---|---|---|---|---|
| paper.abstract.q1 | abstract_claim | Q1 | Q1.result_summary |  | `final_latex/frontmatter/abstract.tex` | current / stale / not_applicable |

## 各问模型与结果

> 每个小问复制一份以下结构。`#### 当前模型口径` 到 `#### 结果摘要` 之间属于语义哈希区；题意、变量、参数、假设、目标、约束、预处理、算法语义或依赖变化时递增 `semantic_revision`。

### Q1：__QUESTION_NAME__

- 主/次题型：
- capability：
- 当前状态：`audited / designed / solved / analyzed / validated / written / completed`
- 结果摘要状态：`pending / current / stale`
- Problem Contract：`pending / frozen / stale`
- 语义闭环：`pending / passed / stale`
- 公式推理链：`pending / passed / stale`
- 复杂度复审：`pending / passed / review_required`
- Model Challenge：`pending / passed / revision_required / stale`
- Human Model Approval：`pending / approved / revision_required / stale`
- Approved semantic revision：
- Approved semantic hash：
- semantic revision：`1`
- semantic change categories：`initial_design / problem_definition / data_scope / variable / parameter / assumption / objective / constraint / preprocessing / algorithm / dependency`
- 核心模型收束：`required / inline / not_applicable`
- 算法流程呈现：`not_needed / stepwise / pseudocode`
- 关联 Algorithm ID：
- 关联命题：
- 关联 Citation Claim：
- 关联术语 Term ID：
- 关联 Numeric Metric ID：
- 关联 Paper Fragment：

#### 当前模型口径

**题意口径（Problem Contract）**

| 项目 | 当前冻结口径 | 来源/推导依据 |
|---|---|---|
| 研究对象 |  |  |
| 输入与给定条件 |  |  |
| 待求输出 |  |  |
| 显式约束 |  |  |
| 隐含约束 |  |  |
| 不允许的简化 |  |  |

**数据与局部处理**

- 输入数据：
- 使用字段/单位/粒度：
- `preprocessing_decision` 对本问的作用：
- 本问专属变换及参数（如有）：

**变量、假设与模型**

| 符号 | 类型 | 含义 | 单位/范围 | Python 变量 |
|---|---|---|---|---|
|  |  |  |  |  |

- 本问共享假设继承：
- 本问局部假设：
- 当前目标/评价指标：
- 当前约束与边界：

$$
\text{在此写入当前有效模型。}
$$

| Formula ID | Source | Depends on | Derivation | Destination | 状态 |
|---|---|---|---|---|---|
|  |  |  |  |  | closed / gap |

**题面—数学—代码—输出闭环**

| 题面对象/要求 | 数学变量、关系、目标或约束 | Python 变量/函数 | 工作簿输出/验证 | 状态 |
|---|---|---|---|---|
|  |  |  |  | closed / gap |

**结构化简与复杂度复审**

- 未使用条件/字段及理由：
- 可证明等价、降维、候选域或分解：
- 高级算法前利用的结构：
- 极端/边界/小规模复核：
- 复审结论：`passed / review_required`

**模型挑战与人工锁模**

- Model Reviewer verdict 与 required actions：
- Devil's Advocate verdict、核心反例/风险与 required actions：
- Residual warnings：
- Model Approval Brief：研究对象、selected model、核心变量、objective、关键约束、preprocessing_decision、结构化简、求解方式、algorithm presentation、被否决路线理由、下一阶段实现范围。
- 当前模型状态：`proposed_model_spec / locked_model_spec / stale`

**数值参数证据**

| 参数 | 数学作用 | 候选范围 | 证据方法 | 最终值 | 主结果稳定性 |
|---|---|---|---|---|---|
|  |  |  |  | pending | pending |

**求解与验证方案**

- 主求解算法及模型适配理由：
- 算法流程呈现：`not_needed / stepwise / pseudocode`
- Algorithm ID（若适用）：
- 输入、状态/决策变量与输出：
- 核心操作及阶段传递：
- 真实循环/分支/候选筛选/修复（若有）：
- Formula / Proposition / Constraint 锚点：
- Python 实现锚点：
- 初始化/随机种子：
- 容差与终止条件：
- 必做检验：
- 多方法数值一致性指标：
- 多方法结构一致性指标：

**本问理论与引用证据**

- 命题及下游作用：
- Citation Claim 与 key：
- 外部参数/定理如何映射到本问：

#### 结果摘要

**模型与算法**

- 当前有效模型/关键结构：
- 主算法/求解方式：
- 算法流程在正文的呈现方式与 Algorithm ID：

**核心结果**

- 目标值/误差/概率/预测结果：
- 关键决策变量或主要分类结果：
- 关键区间、拐点、排序或推荐方案：
- 单位与数值精度：
- 核心答案评分精度：`not_applicable / prompt_defined / official_defined / reviewer_defined / project_high_precision`
- 摘要与正文直接答案应保留的小数位：

**深化证据处置**

| Evidence ID | 方法/来源 | 目标主张 | Disposition | 关键结论 | 后续动作 | 正文/图表锚点 |
|---|---|---|---|---|---|---|
| E1 |  |  | support / modify / reject |  |  |  |

**验证与边界**

- 最大约束违反量/残差/误差：
- 最优性间隙或理论界：
- 多算法/多初值数值一致性：
- 结构结论一致性：
- 数值参数稳定性：
- 敏感区间/失效阈值：

**可入文答案表述**

用两至四句记录可直接进入摘要和本问结果末段的当前答案，包含高精度决定性数值、判断和必要边界。若评分可能核对小数后 6--7 位，应直接保留相应位数。

**证据位置**

| 证据类型 | 文件 | 工作表/函数/命题/图号/citation key | 关键字段或指标 |
|---|---|---|---|
| Python |  |  |  |
| 求解工作簿 |  |  |  |
| 深化分析工作簿 |  |  |  |
| Algorithm |  |  |  |
| 命题 |  |  |  |
| MATLAB 图 |  |  |  |
| Citation |  |  |  |

#### 论文与图表映射

| MATLAB 图标题 | DOCX/LaTeX 图注 | 源工作簿 | 工作表/固定列 | MATLAB 脚本 | 支撑判断 | 论文位置 | 正文引用位置 |
|---|---|---|---|---|---|---|---|
|  |  |  |  | `问题一求解/q1_plot.m` |  |  |  |

## 综合检验与跨问判断

### 多方法一致性

- 数值一致性：
- 结构结论一致性：
- 若冲突，当前处理：

### 敏感性与鲁棒性总览

- 

### 深化证据处置总览

| Evidence ID | 小问 | 目标主张 | Disposition | required_action | 下游 stale/更新范围 | 当前状态 |
|---|---|---|---|---|---|---|
|  |  |  | support / modify / reject |  |  | current / stale / resolved |

### 公式、算法、参数、引用、术语与数字复核

- Formula Trace 是否仍有 `gap/stale`：
- `stepwise/pseudocode` 的 Algorithm Trace 是否 current 且锚点闭合：
- 是否有其实应为 `not_needed` 的装饰性算法流程：
- 是否存在无依据数值参数：
- Citation Evidence 是否存在 pending/stale 的核心 claim：
- Terminology Registry 是否存在 alias collision 或未处理易混术语：
- Numeric Profile 是否覆盖核心答案及提交结果：
- 摘要/正文/表格中的核心答案是否保留评分所需高精度：
- 共享基础是否只定义一次：
- 后问是否只写真实增量：
- 结构化简是否先于高级算法：

### 标题—摘要—关键词一致性

- 选定标题的 Title Claim 是否全部 current：
- 标题主方法是否至少服务一个核心问题：
- 标题主方法是否有正文实质使用与结果证据：
- 摘要是否真实反映标题主张：
- 关键词是否与选定标题和正文实际主模型一致：

### 命题与理论边界复核

- 当前命题数量：
- 是否超过默认预算：
- 若超过，必要性说明：
- 命题条件是否覆盖实际计算参数：
- 数值结果是否落在理论界内：
- 是否存在 stale 命题：

### 模型适用边界与主要误差来源

- 

## 图表证据链

| 图号 | MATLAB 图标题 | 图型/作用 | 源工作簿 | 工作表/固定列 | 绘图程序 | 导出文件 | 正文支撑判断 | 正文引用位置 |
|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |

## 待办与缺口

| 优先级 | 待办项 | 影响范围 | 前置条件/数据 | 完成判据 | 状态 |
|---|---|---|---|---|---|
| P0 |  |  |  |  |  |

## 同步检查

- [ ] 每个已进入模型设计的小问均已冻结 Problem Contract；
- [ ] 题面—数学—代码—输出不存在关键 gap；
- [ ] 核心 Formula Trace 均为 closed，或 gap 已阻断下游；
- [ ] 需要正式算法流程的小问已选择 `stepwise/pseudocode` 并建立 current Algorithm Trace；简单问题明确 `not_needed`，未机械生成伪代码；
- [ ] Algorithm Trace 中公式/命题/约束、Python 与输出锚点和当前求解链一致；
- [ ] 影响结论的数值参数有来源、收敛或验证依据；
- [ ] 复杂度异常信号已经解释；
- [ ] semantic revision 与 stale 传播正确；
- [ ] Paper Fragment Dependency Map 只传播真实依赖，未把无关章节机械 stale；模块化 LaTeX 项目中的 current/stale fragment 已记录可追踪的源码文件；
- [ ] 已求解小问均有 current 结果摘要，具体数值已回工作簿复核；
- [ ] 核心答案按 Numeric Profile 保留评分所需高精度，摘要未因简洁而无依据降精度；
- [ ] 多方法验证同时检查适用的数值与结构结论；
- [ ] 每项深化分析已标记 support / modify / reject，并完成对应后续动作；
- [ ] 核心图表映射到工作簿、MATLAB、正文引用和支撑判断；
- [ ] 需要外部来源的核心 Citation Claim 均有 current citation key 与正文位置；
- [ ] Terminology Registry 中标准术语、易混术语与符号含义一致；
- [ ] Title Claim 与摘要、关键词、正文主模型及结果证据闭合；
- [ ] 命题超过默认预算时已有必要性说明，不按数量自动否决；
- [ ] Paragraph Necessity Test 已用于删除/合并无用途背景、算法百科、重复数字和重复总结；
- [ ] 本文件只保存项目事实和当前选择，没有复制通用写作/排版规则；
- [ ] 本次正式交付同时附带完整最新版 `模型论文框架.md`。
