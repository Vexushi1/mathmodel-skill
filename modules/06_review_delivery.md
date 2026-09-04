# Module 06：评委式终审与交付

本模块只负责**检查、分级、返修排序和交付判定**。它不重新定义正文写作规则。

本模块有两个明确消费时机：

- `draft_semantic_review`：正文各章节初稿完成后、AI Cleanup 之前执行，读取第二至七部分，先修复章节缺失、数学/证据越界、命题证明、伪代码、数值、引用和结构问题；此时不要求尚未生成的 compile report，也不作最终交付判定。
- `final_review_and_delivery`：AI Cleanup、LaTeX 装配、正式审计与编译之后执行，消费全文以及 audit/compile reports，覆盖本模块全部检查并给出最终交付判定。

AI Cleanup 不能替代前一种语义审查，文本变得更流畅也不能让 blocking 或 `review_required` 问题自动消失。

权威来源：

- `config/competition_profiles.yaml` 与当前 competition Pack：当届页数、匿名、提交文件和 AI 披露规则；只有 `edition_rules.verification_status=verified` 且具有来源与核验日期时，才可作为当届官方 Hard 判定依据；
- `templates/latex/cumcm/hsk/template_manifest.yaml`：CUMCM 固定骨架、一级顺序和问题一级标题；
- `modules/05_writing/paper_writing_protocol.md`：普通正文组织、局部叙事、跨文件章节承接、结果解释与验证承接；
- `core/writing_reasoning_contract.yaml`：推理、证据、规则等级、Model/Solver/Validator、优化模型表达、Formula Trace、Algorithm Trace 与算法呈现、命题预算、引用证据、术语、数字、标题主张、claim strength、深化证据处置、Paragraph Necessity 与局部 stale；
- `modules/05_writing/latex.md`：LaTeX 载体、环境、引用、审计与编译接口；
- `templates/review/final_review_matrix.yaml`：正式终审报告 v1 的机器可读字段与稳定枚举；
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
- 每问能够恢复标准模型类型、正式模型名称以及 Model / Solver / Validator 角色；
- 优化类小问能够恢复主决策变量/对象、objective 现实含义、核心约束与摘要 objective 口径；
- solver 首次使用、后问沿用/更换以及 alternative/validator 的角色和 evidence anchor 已按实际情况记录；
- 问题章节内部小节规划已检查颗粒度，必要扩展有独立论证理由；
- headline claim 的 Evidence Level / Scope 与当前结果和深化证据一致；
- `stepwise/pseudocode` 小问存在 current Algorithm Trace，`not_needed` 不残留装饰性算法框；
- 具体数值回到已验收工作簿复核；
- semantic revision、hash 与 stale 状态和 `state/project_state.yaml` 一致；
- Terminology Registry、Numeric Profile、Title Claim Gate 和 Paper Fragment Dependency Map 与当前项目一致；
- 框架保存项目事实和当前选择，没有重新复制通用写作手册。

`paper_framework.sync_status=current` 只表示框架已同步记录当前项目状态，**不代表所有正文片段都 current**。正式交付前检查交付范围内 `paper_fragments` 无 stale。若 Q3 变化，只应使真实依赖 Q3 的正文、图表、摘要 Q3 段、相关模型评价和 Title Claim stale；Q1/Q2/无关背景不得因“整篇保险起见”被机械判 stale。

### Cross-File Assembled Seam Sweep

本检查只消费 `paper_writing_protocol.md#5A-Cross-File-Chapter-Handoff`、Template Manifest、当前 Chapter Handoff Map 与已有 Terminology/Numeric/Claim/Paper Fragment 锚点，不复制另一套 handoff Authority。

在 `draft_semantic_review` 与最终装配后各执行一次 **assembled seam sweep**：

- 按 Manifest 的 `paper_skeleton.ordered_slots + activation` 展开最终 active physical files，逐对核对 actual adjacency；inactive data/model-preparation/question file 不得残留在 current map；
- 摘要只检查 `abstract.tex → 01_problem_statement.tex` 的 final-reading consistency，不检查评价章→摘要的写作顺序；
- 对每个 relevant seam 读取 profile、source closure、carry forward、entry reason、anchors、bridge need 与 status，再按 Protocol 审查对象、符号/术语、依赖、claim、重复和桥接必要性；
- `cross_question_increment` 只在真实前问依赖存在时成立；独立小问不得为了连贯虚构继承；
- `bridge_need=required` 时确认真实语义桥存在，但不要求独立过渡段；`not_needed` seam 出现“下面给出参考文献”等管理型句子时列为 cleanup/review risk；
- 旧 framework 缺少 Map 时，在当前多文件写作路由中增量初始化，不要求重做模型或自动改写旧正文；
- 纯 handoff wording、术语统一、重复删除和 status 更新不触发模型 semantic revision、Model Approval 或 03A；上游真实变化只使引用相关锚点的 seam stale。

机器可检查文件存在、active adjacency、record/status 和确定性 stale 冲突；seam 是否真正连续、是否需要桥接仍由语义 review 判断。物理相邻、连接词出现或表面 token 相似均不能证明数学连续。

模型设计层检查题型匹配、变量闭合、公式来源、假设、约束、高级模型必要性、内生性/共线性/过拟合/计算爆炸及解释边界。

## 三、公式、模型角色、算法、命题与数值证据审查

对核心公式按 reasoning contract 检查 `Source → Derivation → Destination` 是否闭合。机器只能检查锚点和结构，人工作语义判断；不得把关键词匹配当数学正确性证明。

对模型建立、求解及紧邻结果解释，按 `paper_writing_protocol.md#7.3-作者视角与建模解释` 检查关键选择的理由、具体处理和结果用途是否可恢复。不能只剩“建立模型—进行求解”，也不能为增加思考痕迹编造依据、共识或试错；有信息的适度第一人称不作为风格缺陷删除。该检查不按口语或代词频率评分，不判断作者身份，不减免公式来源、证明、Algorithm Trace、数值证据和真实 AI 使用披露。

先检查 Model / Solver / Validator 是否被正文和摘要正确区分：

- 模型名称首次出现时能否识别标准数学类型；
- solver、validator、软件或求解架构是否被误写成模型本体；
- 优化类模型是否按变量/决策对象、目标函数、目标现实含义、约束和最终核心模型闭合；
- 摘要是否至少让读者知道“优化什么”，而不是只看到决策变量和算法名；
- 复杂模型汇总是否用于 recap，而不是替代变量、目标和约束解释。

对 solver 与 Algorithm Trace 按 `writing_reasoning_contract.solver_justification` 和 `algorithm_presentation` 检查：

- 主 solver 第一次使用时是否有本题结构理由，而不是“先进、快速、应用广泛”；
- 后问沿用同一 solver 时是否说明继承结构和新增变化；
- 更换 solver 时是否说明新增离散性、非光滑、规模、不确定性或分解结构如何改变求解需求；
- 另用算法是否有实际 artifact，并明确 baseline / alternative / validator 角色及可比指标；
- `not_needed / stepwise / pseudocode` 是否与真实求解复杂度一致，而不是为了版式整齐统一设置算法框；
- `stepwise/pseudocode` 是否存在 current Algorithm ID，算法作用、输入/状态、核心操作、终止条件、输出和呈现模式是否完整；
- Formula / Proposition / Constraint 锚点是否确实改变对应算法步骤，不能只在表中挂名；
- 论文算法步骤能否追溯到真实 Python 实现，且输入、状态、分支/阶段、停止条件和输出没有被论文改写成另一套算法；
- 已求解小问的算法输出能否继续落到标准工作簿结果或验证证据；
- 伪代码没有混入 DataFrame、文件路径、日志、异常捕获、并行池等纯工程细节；
- 算法语义变化后旧 Algorithm Trace、正文算法块和依赖 paper fragments 已 stale 或同步重写。

机器可以检查 declared mode、ID、必填字段和确定性锚点存在性，但不得仅凭伪代码文字推断算法正确性、收敛性、标准模型类型或与 Python 的数学等价性。

对命题检查：前提、定义域、参数范围和结论完整；没有循环论证、隐藏条件、变量/定义域偷换；没有用有限实验、求解器状态或模型准确率代替数学证明；没有把局部性质写成全局性质；证明后说明对降维、约束、候选域、可行性、阈值、边界或模型必要性的实际作用；模型、参数、约束变化后旧命题已重新核验或 stale。

**命题 0--4 是默认正文阅读预算，不是自动否决线。** 超过预算时检查是否已先合并同质命题、把技术引理移附录，并说明额外命题的不可替代作用。只有命题本身无建模作用、证明错误或与当前模型冲突时才按对应 Hard 问题处理。

证明的“3--8 行”“2--6 步”等只属于 Recommendation，不作为否决条件。重点是推理完整、阅读连续和技术细节位置合理。

数值参数检查候选范围、收敛/验证依据、最终取值和必要的主结果稳定性，不能只接受“综合考虑精度与效率，取……”。

## 四、Terminology、Numeric Style 与 Claim Strength 审查

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

### Claim Strength

按 `writing_reasoning_contract.claim_strength_calibration` 检查摘要、结果末段、模型评价和标题：

- `PROVEN` 才允许严格“证明/必然/全局性质”等证明级主张；
- `VERIFIED_NUMERIC` 只能覆盖实际数值检查范围；“独立算法未发现更优”不能自动升级成“全局最优”；
- `COMPARATIVE` 只能比较实际运行的 baseline / alternative 和对应指标；
- `OBSERVED` 只描述当前样本/场景观察；
- `HEURISTIC` 应写“当前找到的最好方案/当前认证方案”等与实际证据一致的措辞。

重点检查“显著提高、证明模型有效、全局最优、鲁棒性很强、稳定性很好、优于所有方法”等语言是否有对应统计检验、证明、范围或比较证据。摘要执行最严格校准。

## 五、Title Claim、正文结构与 Paragraph Necessity

Title Claim Gate 检查选定标题中的研究对象、主方法、核心机制或贡献：

- 是否至少服务一个核心问题；
- 是否在正文有实质模型/算法使用；
- 是否有对应结果证据；
- 摘要是否真实反映，而非继续放大；
- 关键词是否与选定标题和正文实际主模型一致。

如果标题写“基于鲁棒优化”，但正文核心链实际上是 Monte Carlo + 贪心、鲁棒优化只在末尾做一次扰动，则应修改标题，不允许通过摘要包装来掩盖。

按 Template Manifest 检查固定一级骨架，按 `paper_writing_protocol.md` 检查正文内容：摘要逐问覆盖“任务—模型—目标/关键条件或约束—算法/方法—结果—真实检验证据（若有）—结论”，且没有虚构敏感性或鲁棒性；问题重述能否在不照抄原题的前提下准确恢复对象、条件、范围、量词和输出；问题分析是否以连续自然段形成“对象/条件—困难—数学抓手—建模转化—准备建立的结构—跨问关系”，而非散乱清单或软件流水线；假设是否说明来源/必要性与失效影响，符号是否跨公式/代码/结果一致；共享基础真实共享；核心模型收束按当前 rendering mode 自适应；算法流程按 `not_needed / stepwise / pseudocode` 自适应；求解段从模型结构解释算法；主结果形成图表/数值—比较—机制—回答闭环；模型评价、逐问结论与附录均不新增未经证明的主张。

对每个问题章节执行 `subsection_granularity`：本规则只检查**问题章节内部二级小节**，不限制一级章节数量。默认优先形成“模型建立—模型求解—结果分析—必要检验”约 3--4 个主要单元；超过该颗粒度不自动失败，但需要确认是否存在一个公式/一张表一个小节、变量/目标/约束/汇总机械拆分，或多个同类验证各自单开标题等碎片化。减少标题数量不等于删除技术内容。

对主要段落执行 Paragraph Necessity Test：删去后若不丢失题意、机制、数学关系、求解依据、结果证据或必要边界，则优先删、并或移附录。重点删除算法百科、重复背景、重复模型优点、重复小问总结、装饰流程和无用途公式。机器只给 warning，不能自动删文。

### v7.20/v8.0.1 章节能力保全检查

本检查只消费 Template Manifest、Paper Writing Protocol、reasoning Authority 和正式审计报告，不复制第二套写作规则：

- 中文国赛问题一级标题仍为“问题X模型建立及求解”；专业化二级标题允许，但评委必须能恢复 MODEL → SOLVE → RESULT → 按需 VALIDATE 的真实依赖链；
- 模型建立应保留决策变量/对象、定义域与现实含义、目标函数含义、关键约束来源、核心推导和最终可计算模型，不得因减少标题而删除技术内容；
- 模型求解应从计算结构/困难进入 solver，说明本题化编码、约束处理、初值/参数/精度/终止条件和输出映射；算法名或通用优点不能代替这些信息；
- 求解结果应给出 current 高精度答案、邻近图表解释和直接回答；独立验证前存在 Result → Validation Bridge，且验证写出风险、扰动、指标、变化范围与结论边界；
- 优化模型渲染复核目标函数位于约束大括号外；非优化多方程模型和简单解析模型使用各自适合的汇总方式；
- 读取 prose/surface audit 的装饰性引号、概念连接符链、内部工作流词汇、功能次序、solver 入口和连续图裸堆 finding；warning 不自动阻断，但终审必须记录人工处置；
- 读取项目 Document Length Profile。篇幅偏短时只定位缺失的推导、约束来源、solver 适配、参数依据、结果解释、验证、适用边界或复现说明，不按页数扩写背景、算法百科或伪检验。

## 六、深化分析、图表与结果证据审查

每项深化证据必须能回答：**它具体 support / modify / reject 哪个 claim？**

- `support`：只能增强原主张，不能自动扩大适用范围；
- `modify`：边界、阈值、排序、置信度或正文必须同步修改，相关 paper fragments 在修订前保持 stale；
- `reject`：若核心答案/模型被否决则必须 redo；若只否决附加评价句，可以删除/重写该 claim，不强迫整题重算。

检查每张正文核心图和核心表：有邻近显式编号引用；能读出主要趋势/高精度关键数值及模型或题目含义；工作簿、工作表、MATLAB 脚本、导出文件、图注、正文判断映射一致；正式论文图不嵌入重复的整体 MATLAB `title/sgtitle`，正式图名由 caption 承担；三线表、图题/表题位置、公式编号、命题编号、交叉引用正确；图表没有用摘要数字反推底层数据。

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

## 九、Final Submission Compliance & Evidence Sweep

本节是最终提交合规与证据扫描的唯一语义 Authority。它只在 `final_review_and_delivery` 中、AI Cleanup 与当前 LaTeX audit/compile attestation 完成后执行；`draft_semantic_review` 不要求尚未生成的 PDF、compile report 或提交包证据。

### 1. 恢复终审上下文

开始扫描前必须恢复并在 `review_context` 记录：当前 Skill 版本、competition profile、edition、`edition_rules.verification_status / verified_at / source`、delivery mode、当前 source bundle SHA-256 与 compiled PDF SHA-256。缺少的信息保持可见，不能靠赛事名称、往届经验、自查表或模型猜测补成已核验事实。

规则来源优先级为：当届已核验官方规则或题面 → 当前 competition Pack 的稳定模板约束 → Template Manifest → Writing / Reasoning Authority → 本模块默认审查规则 → 经验建议。低层规则不得覆盖高层规则，经验建议不得伪装成官方要求。

### 2. 动态检查族

按当前论文、实际问题数量、模型数量、交付模式和适用规则动态覆盖以下八族，不展开固定问题数或固定行数清单：

1. `edition_compliance`：消费当前 profile 中页数、匿名、提交文件和 AI 披露等当届规则；
2. `anonymity_and_metadata`：检查最终 PDF 可见内容与作者/公司/标题等元数据，以及图片、代码截图、路径、账户、批注或修订记录中的身份泄露；
3. `ai_disclosure`：核对当届规则、论文声明、独立支撑材料与用户确认的真实使用事实是否一致；
4. `citation_entity_integrity`：在既有 citation key 闭环之外，核对作者、题名、年份、期刊、DOI/URL/访问日期及来源对对应 claim 的真实支持；
5. `rendered_page_surface`：逐页检查孤行、标题悬空、对象裁切、横向溢出、跨页表头、无意义大空白和打印可辨识性；
6. `figure_table_information_value`：检查图与表是否重复承担同一信息任务，以及保留对象是否对结论具有独立信息价值；
7. `reproducibility_and_package`：核对 audit/compile 证明链、manifest、交付模式与当前 package validation；
8. `cross_question_dynamic_coverage`：按实际问题、模型和跨问依赖检查题意—方法—结果—验证—交付覆盖，不预置五问、固定模型数或固定图表数。

每族在 `coverage` 中记录 `check_family / applicability / verification_mode / status / rule_source / evidence`。`applicability` 只能为 `applicable / not_applicable`；`verification_mode` 只能为 `machine / manual / hybrid`；`status` 只能为 `passed / findings_present / unverifiable / not_applicable`。`not_applicable` 必须写明理由，`unverifiable` 必须写明缺失的证据或输入，二者都不能伪装为 `passed`。

### 3. 原子 finding 与评分关系

每个问题使用唯一 `check_id`，并记录 `check_family / dimension / severity / status / hard_fail_code / rule_source / verification_mode / location / evidence / action`。严重级只允许 `blocking / review_required / warning`，处置状态只允许 `open / resolved / accepted_exception`；非 `resolved` finding 必须有具体位置、证据和可执行动作。

`scores` 继续由六维评委式判断形成，且每个维度必须能指向报告 evidence。不得按 finding 数量固定扣 1 分或 2 分，也不得以字符串命中推断数学正确性、身份泄露、AI 使用事实、文献真实性或图表语义重复。

### 4. 已核验规则与 Hard Fail

- `verification_status=verified` 且 `verified_at + source` 完整时，当前适用且强制的官方规则可作为 Hard 判定；
- `unverified / expired` 时，不得声称页数、匿名、AI 披露或提交文件已经满足当届官方要求；official package 是否阻断继续服从现有 package validator；
- 未解决的已核验官方规则违规使用 `verified_official_rule_violation`，前提是没有更具体的现有 Hard Fail code；
- `blocking + open` 必须映射允许的 Hard Fail code，并独立于加权总分触发 `reject_or_major_rework`；
- `accepted_exception` 不得绕过已核验且适用的强制官方规则。

### 5. 机器与人工边界

机器继续负责已有的 label/citation key/结构审计、edition verification 字段读取、source/PDF hash、compile attestation 和 package allowlist；PDF 可见身份、真实 AI 使用、文献实体与 claim 支持、图表信息冗余及页面视觉缺陷由人工或当前可用工具核对并记录验证方式。无法证明时标记 `unverifiable`，不得引入隐藏联网依赖或以字符串规则制造确定结论。

正式 v1 报告以 `templates/review/final_review_matrix.yaml` 为结构载体，并由 `scripts/score_submission.py` 校验。Matrix 是 Review artifact，不是赛事规则 Authority，不进入 Project State、模型 semantic hash、Model Approval、03A/03B 或 Figure Evidence stale 传播，也不得自动加入 official package。

## 十、返修优先级

返修按影响顺序：

```text
会改变答案/数学语义/事实来源的问题
→ 已核验官方规则或匿名性违规
→ 核心答案评分精度或工作簿一致性问题
→ subproblem / paper fragment stale 冲突
→ 模型类型、Model/Solver/Validator、目标函数或约束断链
→ 模型、Algorithm Trace、命题、代码、工作簿不一致
→ 深化证据 unresolved modify/reject 或 claim strength 越界
→ Title Claim / Terminology / Citation Evidence 断链
→ 正文 Default 偏离（含小节过度碎片化）
→ 风格、排版和美观 warning
```

不要先修漂亮再修会改变答案的问题。

## 十一、Blocking 条件

以下属于典型 Hard 违规，必须修复后才能正式交付：

- 漏答核心题目要求；
- 关键变量、目标或约束缺失；
- 数据处理改变结论但没有依据/验证；
- 结果不可复现或与已验收工作簿冲突；
- 评分敏感的核心答案被无依据截断/舍入，导致与题目、官方、评委或已声明 Numeric Profile 不一致；
- stale 模型、结果、Algorithm Trace、命题、图表、Chapter Handoff seam 或交付范围 paper fragment 被当作 current 使用；
- 最终装配 seam 出现会改变研究对象、符号/单位、真实依赖或 claim 边界的实质冲突，仍未修复却继续交付；
- `stepwise/pseudocode` 的论文算法与真实 Python 实现、当前约束/停止条件或工作簿结果存在会改变可复现性的实质冲突；
- 关键证明循环论证、缺少必要前提或与当前模型不一致；
- 有限实验/求解器状态冒充严格证明；
- 把局部/启发式结果无依据写成全局最优；
- 无检验却把稳定性、泛化或显著优越写成确定事实；
- 核心深化证据 `reject` 仍未处理却继续交付原主张；
- 核心图表与正文结论冲突或关键引用不存在；
- 必需 citation key 不存在、外部核心数据/参数完全无来源；
- 正式 LaTeX 审计/编译证明失效，或提交包缺少**当前已核验赛事规则/所选复现模式真正要求的文件**，或 package provenance 验证失败。
- 当前适用、强制且已核验的官方页数、匿名、AI 披露或提交文件规则存在明确未解决违规。

以下**不再自动列为 Blocking**：问题章节内部二级小节超过默认 3--4 个、命题超过默认正文预算、优缺点条目数量关系、简单问题没有独立“核心模型汇总”小节、`not_needed` 小问没有正式算法框、短证明超过经验行数预算、仅由机器字符串相似度产生的术语提示、普通未引用公式的 warning。它们按 Authority 对应 Default/Recommendation 处理。
