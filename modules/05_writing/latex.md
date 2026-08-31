# Module 05B：LaTeX Adapter（v8.0.0 Draft）

v8.0.0 起，本模块不再是正文结构与表达的主 Authority。正式论文采用 **Template-First** 架构：

- `templates/latex/cumcm/hsk/template_manifest.yaml` 决定固定论文骨架、问题一级标题和 LaTeX 结构；
- `modules/05_writing/paper_writing_protocol.md` 决定普通正文怎样组织数学叙事、solver、结果和验证；
- `core/writing_reasoning_contract.yaml` 保留完整跨题型语义 Authority，在命题、复杂 Algorithm Trace、Model / Solver / Validator 角色争议、优化语义、跨问依赖、Title Claim、Claim Strength 或终审时按需加载；
- `core/writing_runtime_contract.yaml` 负责普通写作最小加载策略；
- 本文件只把已经确定的内容放进当前 LaTeX 模板，不建立第二套写作规范。

论文从首个正式版本开始直接使用 LaTeX。中文国赛默认基于 `templates/latex/cumcm/hsk/` 模块化工程；DOCX 不是进入本模块的前置条件，也不得成为模型或数值事实源。

## 1. Template Adapter 边界

### Template 负责

- `documentclass`、宏包、字体、字号、页边距；
- 摘要/关键词环境；
- 一级章节顺序与固定标题；
- 公式、图、表、命题、算法、参考文献和附录环境；
- `main.tex` 与子文件组织；
- 图题在图下、表题在表上等载体约束；
- CUMCM 问题一级标题 `问题X模型建立及求解`。

### Writing Skill 负责

- 为什么此时需要一个公式；
- 公式如何从当前对象、定义、机制或前式得到；
- 出现后下一步怎样变化；
- solver 为什么适配当前模型；
- 结果如何解释；
- 验证针对什么风险；
- 二级/三级标题怎样反映独立数学任务。

因此本模块**没有权限重排上述一级大章节**，也**不改变问题章节顺序**。局部数学依赖与求解认知顺序只影响一个问题章节内部的段落、公式、solver、结果与验证。

## 2. 模板实例化

正式项目推荐复制整个：

```text
templates/latex/cumcm/hsk/
```

到：

```text
final_latex/
```

并将 `hsk_main.tex` 重命名为 `main.tex`。不要只复制单个主文件。

当前固定骨架不在本文件重复列举，以 `template_manifest.yaml` 和实际 `hsk_main.tex` 为准。数据章、共享基础章等可选结构是否启用，仍由当前项目事实和模板 profile 决定。

## 3. 问题章节内部写作接口

复杂问题通常消费四个功能槽：

```text
MODEL → SOLVE → RESULT → VALIDATE
```

它们是认知功能，不是强制标题。标题应对应**独立数学任务**，不强制所有标题使用“XX 的 XX”。简单解析或直接计算问题执行 anti-bloat，不为了结构对称增加算法、核心模型汇总、结果图或验证。

进入模型建立后，默认不重新写一遍问题分析、模型假设和题目要求，只承接当前对象或上一关系，说明为什么此时出现新的量、关系或约束，以及出现后下一步怎样变化。

这部分完整规则消费 `model_establishment_solution_narrative` 与 v8 `paper_writing_protocol.md`。

## 4. 公式写入

公式的数学来源、推导与去向服从 `formula_reasoning_chain`，即 **Source → Derivation → Destination**。本模块只负责 LaTeX 环境和引用。

```latex
\begin{equation}
    F(x,\theta)=0,
    \label{eq:q-core}
\end{equation}
```

正文用 `式~\eqref{eq:q-core}` 引用。符号已经定义后，公式后优先说明它如何改变判据、可行域、目标、候选域或计算结构，而不是逐个重复符号定义。

### 4.1 核心模型收束

**核心模型汇总：自适应而非机械必设。** v7.x 的 `required` / `inline` / `not_applicable` 语义在 v8 中由 Template/Protocol 解释为 `displayed / inline / omitted` rendering。核心模型汇总仍然是重要能力，但默认不是固定二级标题。

复杂优化模型应先显示目标函数：

```latex
\begin{equation}
    \min_{\mathbf{x}} f(\mathbf{x}).
\end{equation}
```

再显示约束：

```latex
\begin{equation}
\text{s.t.}\quad
\left\{
\begin{aligned}
    g_i(\mathbf{x}) &\le 0,\\
    h_j(\mathbf{x}) &= 0,\\
    \mathbf{x} &\in \Omega.
\end{aligned}
\right.
\end{equation}
```

目标函数不得为了大括号整齐而塞进约束系统。题目专属名称可以保留，但首次出现仍需让读者识别标准模型类型与现实优化目标。

## 5. 优化类写作接口

优化类正文应能恢复：

```text
标准模型类型与现实优化目标
→ 决策变量
→ 目标函数
→ 目标含义
→ 约束来源
→ 核心模型汇总
→ solver / validator
```

优化类摘要如果只列决策变量和算法，却没有说明目标函数含义，模型信息仍不闭合。

第一次作为主求解器出现时，必须先说明当前模型结构或困难；后问沿用同一算法时只写继承结构和新增变化；更换算法时说明新增离散性、非光滑、规模或其他结构变化；另用方法时明确 `baseline / alternative / validator` 角色。

不用“下面进行模型求解”作为唯一过渡。求解段一开始先恢复结构分析后的结果、最终可计算结构、搜索对象、目标评价或约束处理，再介绍 solver。**高级算法前**应先检查解析关系、单调性/凸性、降维、候选域、界或分解结构；不能仅因变量多就跳到启发式算法。

## 6. Algorithm / Stepwise / Pseudocode

算法呈现模式保持 **not_needed / stepwise / pseudocode** 自适应。详细规则按需读取 `packs/artifact/algorithm_flow.md`。

只有真实多阶段数学传递、循环、分支、筛选、修复、接受/拒绝或终止逻辑需要展示时，才设置 stepwise 或 pseudocode。**伪代码写数学对象与控制逻辑**，不把 DataFrame、文件路径、日志、异常处理或其他纯 Python 工程细节搬进正文。

算法块前说明为什么需要它、输入是什么；算法块后说明输出怎样映射回模型变量、结果表或下一阶段。标准算法未修改时不展开算法历史和无关通用更新式。

## 7. 结果与图表写入

关键结果出现后，在邻近位置完成**局部证据闭环**：

```text
高精度关键数值/图表
→ 决定性趋势、阈值、区间或结构
→ 当前问题含义
→ 有证据支持时解释原因
→ 直接回答或下一步
```

Figure Result Narrative 是信息功能链，不是固定六句话。多面板图先说明整张图共同回答的问题，再只展开真正改变结论的 panel 差异。

正文核心图/表必须有**显式编号引用** `\ref`，不要只写“结果如图所示”。最后一个结果段已经直接回答本问时，**不机械追加“小问结论”**。

## 8. 结果与验证接口

结果段先闭合主结果。若后续确有参数、边界、seed/初值、残差、替代算法、替代模型、Bootstrap、外样本等风险，再进入 VALIDATE。

结果到验证之间要说明当前已经回答什么、仍可能受什么影响、下一步检验什么。验证不是为了增加工作量，而是限定主张可以成立到什么范围。

验证同时关注数值一致性和**结构结论**。若多方法数值接近而结构判断冲突，不能仅凭目标值接近宣称模型稳定，应回到判据、边界、约束活跃性或解结构继续检查。

`support / modify / reject` 只属于内部证据状态；正式正文写真实数学动作和结论变化，不显示内部状态词。

## 9. 问题章节颗粒度

问题章节内部默认优先形成少量主要数学单元，但**不限制全文一级章节数量**。变量、目标、约束和最终模型若属于同一条模型建立链，不机械拆为多个标题。

一个公式、一张表、一幅普通图或一个参数设置本身不自动构成独立标题。标题根据真实数学任务命名；“模型处理”“参数处理”“结果说明”等泛化标题需要复查。

## 10. 数据章与共享基础章

数据说明/必要预处理章一旦由当前模板与项目事实启用，内部推荐按：模型需要的数据对象 → 必要质量处理 → 必要变换 → 直接进入下游模型的量。这是数据预处理大章节**内部**的组织顺序，不是重排全文一级章节的权限。

共享基础章一旦启用，内部按：共享对象/坐标或索引 → 共享定义 → 共享核心关系 → 后问真实消费的共同输出。这只是章节内部的依赖顺序。

共同轨迹、共同概率关系或共同网络结构不从头复制；后问只写真实新增部分。“同理”只能用于确实没有结构变化的推导。

## 11. Detail Allocation 与模型评价

详写的标准是信息链完整，不是字数更多。决定模型结构、判据/边界、可行域、solver 适配、核心答案和验证主张的步骤应完整；普通代数、重复符号、算法百科、重复图表读数应压缩。

Detail Allocation 在 solver 段同样适用：展开本题 solver fit、problem-specific encoding、objective evaluation、constraint handling、关键参数/精度/终止条件和 output mapping；压缩算法历史、通用优点和无关标准更新式。

0--4 是**默认正文阅读预算**，不是绝对数学上限；它只用于命题规划的阅读负担。模型评价中**优点和缺点的数量按模型实际决定**，本 Adapter **不检查“优点必须多于缺点”**。

## 12. 自然叙事

优先正向叙述，保持规范、朴素、略带**科研训练初期**的真实推理痕迹，不追求成熟期刊式概念包装。

不建立推荐连接词词库。过渡句是否保留只看它是否承担 inherit / gap / transform / solve_entry / result_entry / interpret 等真实逻辑功能。

普通概念不要加装饰性中文引号；不要堆叠 A-B-C-D / A—B—C—D 式概念链。工作流内部词不得进入正式正文。

## 13. 摘要、Citation Evidence 与精度

摘要按问写“模型/关键结构 → 求解方法 → 核心结果 → 直接结论”。优化类必须让读者知道“优化什么”。外部经验参数、外部数据事实和非显然标准理论按 **Citation Evidence** 规则提供真实引用；内部推导与工作簿结果不靠文献替代自身证据链。

**核心答案的精度不得为了摘要简洁而擅自降低。** 若题目或评分可能核对后续小数位，摘要、正文直接答案和核心表格保持同一事实源和足够精度；高精度评分场景常见为 6--7 位，但以题目、物理分辨率和 **Numeric Style Contract** / Numeric Profile 为准。

独立算法未发现更优不自动等于全局最优；Claim Strength 继续服从完整 reasoning Authority。

## 14. LaTeX 工程规则

- 子文件不得重复 `\documentclass`、`\begin{document}`、`\end{document}` 或全局宏包；
- label 在整个工程唯一；
- `\input` / `\include` 路径相对 `main.tex` 工程根目录；
- 图片名和正式工程路径使用 ASCII；
- 图题在图下，表题在表上；
- 参考文献使用当前模板提供的 biblatex/Biber 接口；
- 正式项目统一从 `scripts/audit_latex_project.py` 执行 LaTeX 项目审计，再进入 compile profile；
- 完整编译与正式审计仍由 `modules/05_latex_compile_quality.md`、`core/compile_profiles.yaml` 和相应脚本治理。

## 15. Runtime 与完整 Authority

普通 LaTeX 写作默认加载：

```text
core/writing_runtime_contract.yaml
+ templates/latex/cumcm/hsk/template_manifest.yaml
+ modules/05_writing/paper_writing_protocol.md
+ 本 LaTeX Adapter
```

不需要每次预载完整 `core/writing_reasoning_contract.yaml`。出现复杂语义裁决时再按需补读完整 Authority。

本 Adapter 不允许通过改写模板来掩盖数学错误，也不允许为了叙事流畅改变模型、参数、结果或证据。

## 16. v7.x 兼容语义索引（非 Authority）

为避免 v8 重构期间历史回归测试把“文件换位”误判成“语义删除”，本节仅保留旧 consumer 可识别的术语索引；它不恢复旧职责。

- v7.x 曾把本文件称为“**正文结构与表达权威**”；v8 的正文写作主入口已经迁移到 `paper_writing_protocol.md`，固定结构迁移到 Template Authority。
- 历史 Hard / Default / Recommendation 分级仍由 `core/writing_reasoning_contract.yaml#rule_governance` 定义。
- “问题重述”“问题分析”“求解结果”等结构名称由当前模板与 Protocol 消费，本文件不再单独定义其章节逻辑。
- 历史关键词仅用于兼容检查，不构成第二套写作手册。