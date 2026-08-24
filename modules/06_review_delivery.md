# Module 06：评委式终审与交付

本模块只负责**检查、分级、返修排序和交付判定**。它不重新定义正文写作规则。

权威来源：

- `core/writing_reasoning_contract.yaml`：推理、证据、规则等级、Formula Trace、Algorithm Trace 与算法呈现、命题预算、引用证据、术语、数字、标题主张、深化证据处置、Paragraph Necessity 与局部 stale；
- `modules/05_writing/latex.md`：正文结构与表达；
- 各 Artifact Pack：载体、编译和交付特有要求。

若本模块与 Authority 文案不同，以 Authority 为准。

## 一、评审分级

所有问题按三层治理映射：

- **blocking**：对应 Hard 违规，修复前不得交付；
- **review_required**：对应 Default 偏离，需要题型/模板/用户要求/真实结构的明确理由；
- **warning**：对应 Recommendation 或风格风险，不阻断交付。

终审报告仍可按“致命问题、重要问题、一般问题”向用户呈现，但内部必须保留上述治理来源，避免把经验建议误判为硬错误。

## 二、题意、框架与局部 stale 审查

逐项核验题目要求、附件使用、输出格式和数值精度。建立内部覆盖矩阵，正文不机械展示。

检查 `模型论文框架.md`：

- 文件存在且 `paper_framework.sync_status=current`；
- 只保留当前有效模型、参数、约束、命题、算法呈现、结果和图表映射；
- 已求解小问有 current 结果摘要；
- `stepwise/pseudocode` 小问存在 current Algorithm Trace，`not_needed` 不残留装饰性算法框；
- 具体数值回到已验收工作簿复核；
- semantic revision、hash 与 stale 状态和 `state/project_state.yaml` 一致；
- Terminology Registry、Numeric Profile、Title Claim Gate 和 Paper Fragment Dependency Map 与当前项目一致；
- 框架保存项目事实和当前选择，没有重新复制通用写作手册。

`paper_framework.sync_status=current` 只表示框架已同步记录当前项目状态，**不代表所有正文片段都 current**。正式交付前检查交付范围内 `paper_fragments` 无 stale。若 Q3 变化，只应使真实依赖 Q3 的正文、图表、摘要 Q3 段、相关模型评价和 Title Claim stale；Q1/Q2/无关背景不得因“整篇保险起见”被机械判 stale。

模型设计层检查题型匹配、变量闭合、公式来源、假设、约束、高级模型必要性、内生性/共线性/过拟合/计算爆炸及解释边界。

## 三、公式、算法、命题与数值证据审查

对核心公式按 reasoning contract 检查 `Source → Derivation → Destination` 是否闭合。机器只能检查锚点和结构，人工作语义判断；不得把关键词匹配当数学正确性证明。

对 Algorithm Trace 按 `writing_reasoning_contract.algorithm_presentation` 检查：

- `not_needed / stepwise / pseudocode` 是否与真实求解复杂度一致，而不是为了版式整齐统一设置算法框；
- `stepwise/pseudocode` 是否存在 current Algorithm ID，算法作用、输入/状态、核心操作、终止条件、输出和呈现模式是否完整；
- Formula / Proposition / Constraint 锚点是否确实改变对应算法步骤，不能只在表中挂名；
- 论文算法步骤能否追溯到真实 Python 实现，且输入、状态、分支/阶段、停止条件和输出没有被论文改写成另一套算法；
- 已求解小问的算法输出能否继续落到标准工作簿结果或验证证据；
- 伪代码没有混入 DataFrame、文件路径、日志、异常捕获、并行池等纯工程细节；
- 算法语义变化后旧 Algorithm Trace、正文算法块和依赖 paper fragments 已 stale 或同步重写。

机器可以检查 declared mode、ID、必填字段和确定性锚点存在性，但不得仅凭伪代码文字推断算法正确性、收敛性或与 Python 的数学等价性。

对命题检查：前提、定义域、参数范围和结论完整；没有循环论证、隐藏条件、变量/定义域偷换；没有用有限实验、求解器状态或模型准确率代替数学证明；没有把局部性质写成全局性质；证明后说明对降维、约束、候选域、可行性、阈值、边界或模型必要性的实际作用；模型、参数、约束变化后旧命题已重新核验或 stale。

**命题 0--4 是默认正文阅读预算，不是自动否决线。** 超过预算时检查是否已先合并同质命题、把技术引理移附录，并说明额外命题的不可替代作用。只有命题本身无建模作用、证明错误或与当前模型冲突时才按对应 Hard 问题处理。

证明的“3--8 行”“2--6 步”等只属于 Recommendation，不作为否决条件。重点是推理完整、阅读连续和技术细节位置合理。

数值参数检查候选范围、收敛/验证依据、最终取值和必要的主结果稳定性，不能只接受“综合考虑精度与效率，取……”。

## 四、Terminology 与 Numeric Style 审查

### Terminology

读取 Terminology Registry，检查：

- 同一技术量是否坚持 canonical term；
- discouraged alias 是否仍在终稿高频出现；
- confusable terms 是否定义、量纲、符号和适用范围分离；
- “样本/场景/仿真样本/realization”“有效时长/总时长/累计时长”等是否存在跨量混用；
- 标准术语是否因 AI 润色被机械换成近义词。

机器只做已登记别名和局部共现提示，不能自动判断陌生术语是否同义。

### Numeric Style

核心原则是：**结果展示精度服从题目与评分精度，不以版面美观为由擅自降精度。**

检查：

- 若题目、官方、评委或项目 Numeric Profile 指明后续小数位会影响结果分，摘要、正文直接答案、关键表格和提交结果文件是否保留相应高精度；在无更具体要求时，高精度评分场景通常保留小数后 6--7 位；
- 同一指标的比例、百分比和百分点是否正确区分；
- 单位、科学计数法、均值 ± 标准差、置信区间、坐标/时间/优化变量精度是否统一；
- 表格与正文是否同源，不能一个写 `0.9132478`、一个无依据写 `0.91`；
- 图轴可以简化，但作为答案证据的关键标注不能丢掉评分所需位数。

机器不能由“很多小数位”自动判断统计、物理或数学准确性。

## 五、Title Claim、正文结构与 Paragraph Necessity

Title Claim Gate 检查选定标题中的研究对象、主方法、核心机制或贡献：

- 是否至少服务一个核心问题；
- 是否在正文有实质模型/算法使用；
- 是否有对应结果证据；
- 摘要是否真实反映，而非继续放大；
- 关键词是否与选定标题和正文实际主模型一致。

如果标题写“基于鲁棒优化”，但正文核心链实际上是 Monte Carlo + 贪心、鲁棒优化只在末尾做一次扰动，则应修改标题，不允许通过摘要包装来掩盖。

按 `modules/05_writing/latex.md` 检查正文结构：问题重述能否恢复对象与要求；问题提出与问题分析分工；假设与符号清楚；共享基础真实共享；核心模型收束按 `required / inline / not_applicable` 自适应；算法流程按 `not_needed / stepwise / pseudocode` 自适应；求解段从模型结构解释算法；主结果形成图表/数值—比较—机制—回答闭环；独立结论等 Default 偏离有真实理由。

对主要段落执行 Paragraph Necessity Test：删去后若不丢失题意、机制、数学关系、求解依据、结果证据或必要边界，则优先删、并或移附录。重点删除算法百科、重复背景、重复模型优点、重复小问总结、装饰流程和无用途公式。机器只给 warning，不能自动删文。

## 六、深化分析、图表与结果证据审查

每项深化证据必须能回答：**它具体 support / modify / reject 哪个 claim？**

- `support`：只能增强原主张，不能自动扩大适用范围；
- `modify`：边界、阈值、排序、置信度或正文必须同步修改，相关 paper fragments 在修订前保持 stale；
- `reject`：若核心答案/模型被否决则必须 redo；若只否决附加评价句，可以删除/重写该 claim，不强迫整题重算。

检查每张正文核心图和核心表：有邻近显式编号引用；能读出主要趋势/高精度关键数值及模型或题目含义；工作簿、工作表、MATLAB 脚本、导出文件、图注、正文判断映射一致；MATLAB `title/sgtitle` 与正式 caption 分工明确；三线表、图题/表题位置、公式编号、命题编号、交叉引用正确；图表没有用摘要数字反推底层数据。

真实存在的算法分歧、敏感边界、异常样本和约束失效不得被终稿静默删除。

## 七、Citation Evidence 与参考文献审查

按 `writing_reasoning_contract.citation_evidence` 检查：外部经验参数、外部数据、领域事实、非显然标准定理和既有研究比较有真实 citation key；`\cite{}` key 存在于 `references.bib`；重复 key、明显孤儿条目和 `\nocite{*}` 风险已处理；标准定理已核验本题条件；外部参数说明了怎样适配当前问题；本文自己的推导、工作簿结果和数值验证没有被外部引用替代。

机器可以检查 key、重复和未使用条目，但不能仅凭 citation 存在判断文献是否真的支持该 claim，也不能按域名自动判断文献质量。

## 八、编译、复现与提交包

检查输入数据、项目根目录 `模型论文框架.md`、Python 求解代码、环境说明、随机种子、每问标准工作簿、MATLAB 绘图脚本、正式图、可编辑机理图、DOCX（如需）、LaTeX 源码和 PDF。

正式 LaTeX 交付要求：编译引擎和模板 profile 正确；`latex_audit_report.yaml` 与 v3 `compile_report.yaml` 均为 current；无 Error、未定义引用、缺失文献、缺图、字体错误和不可接受的 Overfull；目录、页码、摘要、图表、命题和附录编号正确；PDF 逐页检查。

提交包按 `packs/artifact/full_submission.md` 分流：

- **official**：只包含当届已核验 `edition_rules.submission_files` 允许/要求的文件。若赛事只要求 PDF，就只提交该 PDF；不得为了“复现完整”擅自塞入框架、代码、工作簿或内部元数据；
- **reproducibility**：仅在用户明确要求全套成果/内部归档时包含框架、源码、代码、工作簿、MATLAB 等复现材料；
- 两类 ZIP 都必须先形成 `submission_manifest.yaml`，再通过 `submission_package_validation`；ZIP 存在不等于 `validated_submission_package`。

终审不得再使用“提交包必须包含完整框架，不只交 PDF”这类跨赛事固定规则。

## 九、返修优先级

返修按影响顺序：

```text
会改变答案/数学语义/事实来源的问题
→ 核心答案评分精度或工作簿一致性问题
→ subproblem / paper fragment stale 冲突
→ 模型、Algorithm Trace、命题、代码、工作簿不一致
→ 深化证据 unresolved modify/reject
→ Title Claim / Terminology / Citation Evidence 断链
→ 正文 Default 偏离
→ 风格、排版和美观 warning
```

不要先修漂亮再修会改变答案的问题。

## 十、Blocking 条件

以下属于典型 Hard 违规，必须修复后才能正式交付：

- 漏答核心题目要求；
- 关键变量、目标或约束缺失；
- 数据处理改变结论但没有依据/验证；
- 结果不可复现或与已验收工作簿冲突；
- 评分敏感的核心答案被无依据截断/舍入，导致与题目、官方、评委或已声明 Numeric Profile 不一致；
- stale 模型、结果、Algorithm Trace、命题、图表或交付范围 paper fragment 被当作 current 使用；
- `stepwise/pseudocode` 的论文算法与真实 Python 实现、当前约束/停止条件或工作簿结果存在会改变可复现性的实质冲突；
- 关键证明循环论证、缺少必要前提或与当前模型不一致；
- 有限实验/求解器状态冒充严格证明；
- 把局部/启发式结果无依据写成全局最优；
- 无检验却把稳定性、泛化或显著优越写成确定事实；
- 核心深化证据 `reject` 仍未处理却继续交付原主张；
- 核心图表与正文结论冲突或关键引用不存在；
- 必需 citation key 不存在、外部核心数据/参数完全无来源；
- 正式 LaTeX 审计/编译证明失效，或提交包缺少**当前已核验赛事规则/所选复现模式真正要求的文件**，或 package provenance 验证失败。

以下**不再自动列为 Blocking**：命题超过默认正文预算、优缺点条目数量关系、简单问题没有独立“核心模型汇总”小节、`not_needed` 小问没有正式算法框、短证明超过经验行数预算、仅由机器字符串相似度产生的术语提示、普通未引用公式的 warning。它们按 Authority 对应 Default/Recommendation 处理。
