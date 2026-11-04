# Module 05C：AI 语言润色与模板感清除

本模块是 **draft_semantic_review 已闭合之后的普通自然语言润色消费者**，**不建立第二套正文写作规则**。它只消除模板化、空泛语句和机械重复，不修改已经整理好的数学、证据、版式结构或项目事实。普通正文和 Paragraph Necessity 由 `modules/05_writing/paper_writing_protocol.md` 管理；作者表达由 `paper_writing_protocol.md#7.3-作者视角与建模解释` 管理；Formula、Proposition、Algorithm、术语、数值与 Claim Strength 由 `core/writing_reasoning_contract.yaml` 及当前项目事实管理；载体由 `modules/05_writing/latex.md` 管理。**Skill 负责原则，脚本负责穷举**，而非让诊断脚本自动写论文。

启动前必须消费已解决的 draft review findings。局部修改默认只读当前目标 fragment 与直接依赖；只有跨问依赖、Title/Abstract、assembled seam、真实 Terminology/Numeric/Claim 冲突或 final review 有必要时才扩大读取范围；不能因为“顺便润色”重写无关章节。若未解决 blocking/review_required，回到 draft review，不靠润色宣称完成。

## A. Integrity / Hard boundary

**本阶段数学与事实只读；即使认为形式等价，也不得自行改动。**

- **公式与中文推导**：内联、行间与 LaTeX math 环境中的全部符号、上下标、运算方向、变量、关系、编号、标签、单位、精度和既定位置均逐字保留。公式间纯文字表达的前提→变换→结论、定义、关键近似、约束来源、初边值、误差、solver precondition、Reduction Provenance 与 Core Derivation Body Closure 也只读。**公式来源、推导、命题证明、伪代码及求解细节**一旦在正文定稿，Cleanup 不缩减、迁移、重排或删除；“代码能复现”不能替代数学论证。
- **已定稿的所有公式角色均只读**：`final_model_relation`、`key_bridge_relation`、`supporting_derivation`、`routine_algebra`。不能仅因“不是最终模型公式”删除；不能以旧 Formula Role 的 Keep / Compress / Re-locate / Delete 裁决对当前正文动手。删除机械代数或重写关键证明须回到前置 Protocol / Reasoning 阶段裁决。
- **证明与算法**：planned/current Proposition、Proof、stepwise/pseudocode Algorithm Trace、求解步骤、停机条件、条件句、限定词和推理次序只读。用户本轮没有再次提到这些能力，也不意味着可清除。若 `Core Derivation Body Closure Test` 或 Preflight 指出缺口，只报告给上游，不在 Cleanup 直接修补。
- **核心数值与全部数字**：包括非关键说明数字、目标值、阈值、比较基准、baseline、`accepted 数值`、单位、`绝对/相对误差`、百分比/百分点、`Numeric Profile` 和答题精度，均不舍入、不重写、不改变显示格式、计算或工作簿。此前已定的普通数字两位小数与关键精度 6--7 位规范仍由前置写作阶段决定；Cleanup 只读，不改 accepted 工作簿。
- **术语与主张**：`Terminology Registry`、canonical term、首次准确解释、`Citation Evidence`、BibTeX key、`Title Claim`、证据等级、当前结果和 stale 状态只读。数值实验不能成为数学证明；局部或启发式求解不能写成无依据的全局最优。发现 unsupported claim 或缺少来源，只提交原有 review finding，**不得**自行增删论断、引用或研究结论；不得为了“更简洁”删成裸术语/裸缩写。
- **源文件与图表实体**：章标题、小节名称及层级、目录顺序、文件边界、caption、表头、行列、图例、标签与交叉引用命令均只读。不限制也不重排一级章节；写作顺序优化也没有权限重排既定一级大章节。二三级小节的 Merge / Split、Heading Compression Test 与 Judge Readability Test 都属于上游写作/审查，不是 Cleanup 的主动编辑动作。

以上边界不取决于文本是否含公式：带“仅在、至少、局部、近似、必要、充分、不得”等限制的中文句子也是受保护推理。界限不清时保留原文并报告，禁止靠猜测数学正确性、参数最优性、术语语义等价或物理/统计准确性来替换内容。

## B. Evidence closure

**本节仅规定润色不得碰的既有信息，不再执行数学或论文结构裁决。** `model_establishment_solution_narrative`、Formula Roles、`Core Derivation Body Closure Test`、`Paper Writing Protocol §11` 的要求均已在写作与 draft review 阶段执行。Cleanup 的任务不是再次评价公式、模型、算法、模型求解结果或深化验证的充分性，更不能为了漂亮衔接新增未运行的 03B、伪造结果、删除 `support / modify / reject` 的反证。

碰到原文的数学、图表、引用、`Title Claim`、数值或逻辑缺口，**定位并返回相应 Authority / 原有 review finding**。例如模型建立开头重新完整复述题目、问题分析或模型假设，优化类模型先出现 DE、GA、PSO、ALNS、Dual Annealing，自定义模型名遮蔽标准类型，求解段一开始就是算法名或算法优点，核心结果远离所有解释，或摘要中用“先进、高效、精确、最优、显著、强鲁棒”包装无证据 claim：如果需要改变数学结构、标题、求解或结论，均交回上游，**不在 Cleanup 越权修复**。机器不能由“因为/因此”判定模型理由完整。

## C. Style & Necessity

### C1. 普通自然语言去模板化

仅编辑**不承担定义、证明、约束、数值、事实或证据功能**的句子：删除或压缩“为了更好地解决问题”、算法百科、重复预告、泛泛自夸、机械章间导航、没有信息增益的“本文/本问/该模型”。这是删套话，不是删除第一人称本身。对“本文不是……而是……”一类制造无必要冲突的表达，改为原文已支持的直接叙述；**不替作者编造理由**、团队讨论、失败试验、经验机制或故作犹豫。“首先、然后、因此”不是禁词，判断标准是逻辑功能，不是连接词词表。

**普通语言限定使用 Keep / Compress / Re-subject / Delete**：只操作与受保护内容可明确分离的过渡句、纯冗余句和语序。改动必须保持原研究对象、事实、语气、结论强度与上下文指向；不允许借“重设主语”改变已证明事实或实证主张。信息过载的长句仅在不含推理依赖时调整句式；不得以字数、句数、公式数或“像不像 AI”作删除规则。根据 `Paragraph Necessity、Model Rationale 与 Detail Allocation` 的上游结论保留有信息的理由，不在 Cleanup 再做数学价值删减。原文已经自然且准确时 Keep 即可。

### C2. 段落与结果附近的纯语言

可以消除已在邻近正文完整表达过的空泛衔接、逐格复述表格、逐点读图及仅重复 caption 的话术；但核心图表的结果、现象、范围、条件、为什么此时需要这张图和唯一一次必要解释一律保留。不要求每张图固定使用相同句数、句序和词语。空间/网络图、机理/几何图等证据作用按 Protocol / Figure Authority 判断；`图题/表题负责识别对象和范围`，Caption、轴、图例、表头、数据显示、表格拆分及表格 Cleanup 只改善显示层等旧操作**不属于本阶段权限**。

标题或章节有问题时，包括一个二级或三级小节只有一个公式、一张表或一幅普通图、程序执行步骤直接变成论文小节、专业缩写/方法名串联、泛化标题，应报告上游。Split 不能由字数触发，Merge 不能由标题数量触发；Cleanup 连按其他理由主动拆合标题也没有权限。

### C3. 不确定性与回退

遇到受保护内容和普通语言混在一句、无法证明可分离时，不作局部替换，记录位置及可疑点。发现公式缺口、引用范围不一致、数值漂移、证明错误或冲突，回到原写作/数学/数据/Review 阶段，必要时等待原有批准；不能自行修改事实、扩写证据或通过润色制造通过状态。

## D. Optional machine diagnostics

机器审计不得自动重写正文。现有 `scripts/audit_paper_prose.py` / `scripts/audit_v8_writing_surface.py` 等工具只能定位风险，不能由标题字符数、公式数量、篇幅、连接词、代词频率或算法名判断数学正确性、文章是否“像人”，明确不使用 `first_person_ratio`、`human_like_score`、`AI_like_score`。机器也不能只看 citation key 推断语义支持，不据表面自然度升级为 Hard 错误。

改动后在**现有** draft/final Review 流程和版本对照中检查：公式与中文推导、证明/伪代码、数字、术语/主张、标签与章节结构是否仍是原文；润色确实减少空话、未丢必要信息，关键依据与 Claim Strength 没有改变。仅有数学环境字符串不变，不代表中文推导无误改；有疑问则保留/回退。LaTeX 源码有真实文字变更时，仍按既有编译与 PDF currentness 要求更新，不复用旧证明。不新增项目状态、审批、逐句哈希台账或用户本地 checker。
