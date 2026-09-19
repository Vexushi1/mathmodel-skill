# Module 05C：AI 模板感清除

本模块只负责**清除模板化、空泛化、机械重复与表现层风险**，不建立第二套正文写作规则。普通正文如何组织由 `modules/05_writing/paper_writing_protocol.md` 决定；作者声音与建模解释直接消费 `paper_writing_protocol.md#7.3-作者视角与建模解释`；复杂数学语义、Formula / Algorithm / Proposition、Model/Solver/Validator、Claim Strength、Citation Evidence 与数值口径只服从 `core/writing_reasoning_contract.yaml`；LaTeX 载体只服从 `modules/05_writing/latex.md`。若本文与 Authority 冲突，以 Authority 为准。**Skill 负责原则，脚本负责穷举。**

Cleanup 只在 `draft_semantic_review` 的 blocking / review_required finding 已处理后执行。它可以改表达，不能改模型事实、数值、证据范围、一级章节顺序或问题顺序；**写作顺序优化也没有权限重排既定一级大章节**。局部修改默认只读当前目标 fragment、其真实依赖和已登记 Terminology/Numeric/Claim 锚点；只有跨问依赖、Title/Abstract、assembled seam、全篇术语/数值冲突或 final review 明确需要时才扩大范围，不能因为“顺便润色”重写无关章节。

## A. Integrity / Hard boundary

Cleanup 前后都必须保持以下不变量：

- 核心数值、单位、精度、引用键、公式/图表锚点与 current 事实源一致；stale 不得润色成 current；
- 数值实验、solver 状态或经验现象不得改写成严格证明；局部/启发式结果不得润色成无依据的全局最优；
- `Reduction Provenance`、solver precondition、约束方向、边界、变量含义和 claim scope 不得被改写；
- 非显然核心推导必须保持正文可恢复：题目条件/基本规律怎样形成关系或方程、关键假设/变换/化简怎样进入模型、初边值/关键约束/可行域怎样得到、关键离散/误差关系或 solver 前提怎样支撑主结果，不能为了简洁变成“直接可得”或只剩最终公式；
- 当前 Preflight 已激活的 Core Model Summary、planned/current Proposition、stepwise/pseudocode Algorithm Trace 不得因篇幅或模板感被删除；
- 需要外部来源的 claim 不得为了行文流畅移除 Citation Evidence；内部推导和工作簿结果也不得用外引替代；
- 未解决的深化证据 `reject`、语义争议或验证边界不能靠删除异常描述继续交付。

Cleanup 不重新判断数学正确性、参数最优性、术语语义等价、物理/统计准确性，也不因 citation 存在就声称文献对 claim 形成语义支持。它不替作者编造理由，不从模型名、算法名、标题、连接词或图形外观猜测机制。**公式来源、推导、命题证明、伪代码及求解细节**若是当前证据链所需内容，必须保留其可恢复性。

## B. Evidence closure

### B1. 公式、模型、算法、结果与深化证据

先消费本问 Formula Roles 与 Writing Capability Preflight，再决定 Keep / Compress / Re-locate / Delete：

- `final_model_relation`：Keep；清理后 solver / validator / 决策规则仍可恢复。
- `key_bridge_relation`：若承担机理、判据、关键变换/化简、初边值/约束来源、证明、边界、降维、候选域或 solver precondition，Keep 或只压缩解释；**不能仅因“不是最终模型公式”删除**。
- `supporting_derivation`：按实际数学作用压缩；若其中步骤是恢复非显然核心推导、关键变换/化简、初边值/约束来源、solver 前提或核心证明不可缺少的逻辑环节，必须留在正文可恢复。Cleanup 不得仅因篇幅、难度、角色名或版面需要把它移入附录。
- `routine_algebra`：优先压缩或删除，不因角色 taxonomy 增加正文公式。
- Preflight 为 `required / planned / current / stepwise / pseudocode` 时，即使**用户本轮没有再次提到这些能力**也照常保留；`missing/stale/review_required` 必须回到裁决，不能靠润色伪装通过。
- Proposition / Proof 为 planned/current 且承担正文核心论证时，Cleanup 只能改善分段、衔接和排版，不能把完整证明降成“关键链 + 见附录”。

执行 **Core Derivation Body Closure Test** 后才能 Compress / Re-locate：

1. 正文还能否看出条件、基本规律或定义从哪里进入模型；
2. 关键假设、坐标/变量/参考系变换、对称化简、降维或分解是否仍能恢复；
3. 非平凡初边值、目标/约束/指标、可行域或 solver 前提的来源是否仍清楚；
4. 关键关系怎样进入最终模型、计算、验证或答案是否仍清楚；
5. 后问新增/改变部分是否真的展开，而不是只剩“同理”。

任一项因删减而断裂，就不是可安全压缩的“支持性细节”。“代码能复现”“附录有完整式子”“最终公式还在”都不能替代正文的数学论证链。共享模型前文已完整推导时允许准确回指，只保留本问新增推导。

模型建立—求解—结果连续性只消费 `model_establishment_solution_narrative`、Model Construction Rationale 与相关 reasoning Authority。Cleanup 只处理表现风险，例如：

- 模型建立开头重新完整复述题目、问题分析或模型假设，而没有新增数学作用；
- **优化类模型先出现 DE、GA、PSO、ALNS、Dual Annealing** 等 solver，决策变量、目标、约束与可计算结构尚未出现；
- 求解段一开始就是算法名或算法优点，未说明当前结构、剩余困难和适配条件；
- solver / validator / 软件被误写成模型本体，或**自定义模型名**掩盖标准数学模型类型；
- 关键参数给出数值却没有题面来源、候选范围、收敛/误差/可行性或选择依据；
- 核心结果远离所有解释，或图表只剩“如图所示”而不回答当前设问；
- 独立算法未发现更优被润色成“证明全局最优”；
- `support / modify / reject` 的真实深化证据没有映射到具体 claim。

判断标准是语义与证据功能。**不得仅凭连接词、标题语法、算法名、段落距离、小节数量、标题字数、正文长度、公式数、图引用关键词或表面顺序判断叙事/详略质量**；机器不能由“因为/因此”判定模型理由完整。

### B2. Terminology

只根据当前 Terminology Registry 做一致性修正：canonical term 保持稳定，discouraged alias 改回登记词，confusable terms 不因“避免重复”而交替使用。Cleanup 同时保护首次解释：领域术语、项目自定义指标或专业缩写第一次实质出现时若已有准确的邻近解释，不得为了“更简洁”删成裸术语/裸缩写；若原稿缺少解释，可以在不改变定义、量纲、符号、模型类型和算法角色的前提下补一个简短解释。

已经解释清楚的术语后文不反复定义，也不为“更自然”轮换同义词。陌生词是否同义、某词对评委是否陌生、括号里出现全称是否已经解释充分，都不得由机器自判。

### B3. Numeric Style

只根据 current Numeric Profile 和题面/评分精度要求统一格式：默认高精度连续评分结果在没有更具体口径时保留 6--7 位，不得为了摘要简洁擅自降精度；不得为了简洁把高精度答案擅自压成两三位；比例、百分比、百分点、科学计数法、区间、均值±标准差和单位不能混用。图轴刻度可简化，但关键答案标注不能因此丢失必要位数。

### B4. Citation Evidence、Title Claim 与 Claim Strength

外部经验参数、外部数据、领域事实、非显然标准定理与既有研究比较保留真实 citation；本文推导与工作簿结果保留内部证据链。Title Claim 必须对应正文实质使用的方法/机制及结果证据。`HEURISTIC / OBSERVED / COMPARATIVE / VERIFIED_NUMERIC` 不得润色升级为 `PROVEN` 或无依据的全局/因果主张。

重点复查**摘要中用“先进、高效、精确、最优、显著、强鲁棒”**等包装词时是否有相应证据；没有证据则改成可验证的具体事实，而不是换一个更夸张的形容词。

## C. Style & Necessity

### C1. 模板段、吹牛腔与元话语

删除或压缩跨题通用的管理句、空泛价值判断、重复章节预告、算法百科与“为了更好地解决问题”等元话语；“本文/本问/该模型”只在承担真实指代时保留。保留真实对象、gap、选择依据、数学作用、结果含义和限制。第一人称不是错误：需要删除的是没有信息增益的宣布动作，**不是删除第一人称本身**。

“本文不是……而是……”等连续否定若只制造无必要冲突则改为直接说明当前对象和选择；不建立推荐连接词库；“首先/然后/因此/同理”可以自然使用，判断标准是逻辑功能，不是连接词词表。不得为了“更像人”刻意加入犹豫、口语、故事或团队经历。

### C2. Paragraph Necessity、Model Rationale 与 Detail Allocation

段落只在删除后仍不损失题意、机制、模型关系、选择依据、solver 条件、结果证据或边界时才删。决定性推导不能压成一句“可得”；routine algebra、重复定义、算法历史、算法百科和通用优点可以缩减。**不得以字数、句数、公式数**或小节长度直接判断详略得当。

公式密集段落遵循 Authority / Protocol：保留对象/缺口→推导→作用。信息过载的长句按推理单元拆分，不按字符/句数硬切，也不把无直接依赖内容硬塞一句。

局部模型适用性通常就地说明，不为展示完整性机械新增“模型适用性分析”；简单直接问题执行 anti-bloat，不强造 solver、命题、图表或验证。

### C3. 结果与图表表达

删除逐格复述表格、逐点读图和只重复 caption 的报表式句子；核心图表必须在邻近正文承担明确证据作用；保留“关键结果/特征 → 证据支持的解释 → 对设问的含义”。图第一次进入正文时必须说明它展示的变量/对象关系以及**为什么此时需要这张图**。参数响应、收敛、预测拟合、**空间/网络图**、**机理/几何图**分别按证据角色解释，不强套同一曲线模板。

图表改写先检查职责：图题/表题负责识别对象和范围，轴/图例/表头/行名/表注负责读数条件，正文负责关键特征、解释和答案。Cleanup 可以压缩三处重复，但不能删掉唯一一次必要定义、单位、比较基准或指标方向，也不能把长篇分析塞回 caption。

表格 Cleanup 只改善显示层：把内部 run id、代码变量名或裸符号替换/补充为可读显示名时，必须能回到 current Terminology/Numeric/工作簿事实；不得猜测含义，也不得改变 accepted 数值。单位、无量纲、百分比/百分点、绝对/相对误差、指标优劣方向、baseline 和排序口径不得为了“表头更短”改变。过宽表优先拆分真实比较维度或删冗余列，不缩小到难读，也不以删除单位和精度换宽度。

多面板图只解释对结论有独立贡献的差异；原因必须能回到模型/约束/机制/统计结构或已证实数据规律。Figure Result Narrative 是信息功能链，**不要求每张图固定使用相同句数、句序和词语**。核心结果远离所有解释属于风险，但机器不按“图后几行”硬判。

### C4. 问题章节内部小节架构、标题最小化与大框架保护

只调整问题章节内部二级/三级标题，**一级至三级正常可用，正式章节禁止四级及以上**。按独立数学任务执行 Keep / Compress / Merge / Split：同一论证链可合并；独立公式组、证明/判据、结构化简、参数证据或 solver stage 可拆分。

执行 **Heading Compression Test**：删除父标题已提供的上下文和无信息包装后，当前任务若仍完整则优先短标题；若会混淆对象、方法或边界则保留限定。再执行 **Judge Readability Test**：把标题单独交给“懂数学建模但不熟悉本题专业领域”的评委，若只看到专业缩写、领域名词或方法堆叠而无法判断对象与任务，应补回必要对象/目的，或把非必要方法名移到节首正文。必要标准模型名、方法名和区分性限定可以保留，不能为了通俗化改成错误或空泛名称。

**Split 不能由字数触发，Merge 不能由标题数量触发**，也没有标题字符数硬阈值。

风险包括：依赖关系倒置；一个二级或三级小节只有一个公式、一张表或一幅普通图却没有独立任务；复杂模型反而过度合并；只由专业缩写/方法名串联而遮蔽对象与任务；“模型处理/参数处理/结果说明/影响因素”等**泛化标题**；把读取数据、缓存、并行或保存等**程序执行步骤直接变成论文小节**。

### C5. 科研初学者式自然重写

保留真实推理痕迹，动作只有 Keep / Compress / Re-subject / Delete：

- Keep：保留当前 gap、选择依据、简化原因、数学作用、验证动机或结论边界；
- Compress：删除聊天式填充与重复，但保留对象、依据和下一步；
- Re-subject：已经证明的数学/数据事实可让对象或结果作主语；
- Delete：纯管理动作且删除后不损失任何技术信息。

每次实质改写后做 Reasoning Necessity 与 Problem-Specificity 检查。自然发问必须进入相邻推导、真实验证、后续任务或明确未决边界；不能提出问题后无证据直接给肯定答案。第一人称、本文和对象主语都可合法存在，不设置频率目标，也不推断作者身份。

## D. Optional machine diagnostics

正式 LaTeX 工程的确定性审计入口仍为 `scripts/audit_latex_project.py`；Cleanup 本身不替代该审计。机器诊断只定位可复核风险，机器审计不得自动重写正文。允许报告模板化元话语、重复章节预告、solver-first、标题碎片化/过度合并、图表裸堆、术语/数值格式漂移、强 claim 表面风险等；这些通常是 warning / review_required，只有同时违反既有 Hard 事实、证据、引用或 stale 边界时才 blocking。

机器不得根据代词比例、连接词、标题字符数、公式数量、正文长度、算法名或图引用距离评价“像不像人”、数学正确性或模型理由质量；明确禁止 `first_person_ratio`、`human_like_score`、`AI_like_score` 一类作者身份/自然度评分。BibTeX 只检查 key 与结构完整性，不由 Cleanup 推断引用是否语义支持 claim。所有自动修复必须在改后重新检查 Formula/Proof/Algorithm、数值精度、Citation Evidence、Claim Strength、局部依赖和 LaTeX 引用完整性。
