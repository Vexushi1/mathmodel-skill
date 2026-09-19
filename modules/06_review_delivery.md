# Module 06：评委式终审与交付

本模块只负责**检查、分级、返修排序和交付判定**，**不重新定义正文写作规则**。普通正文写法只消费 `modules/05_writing/paper_writing_protocol.md`，作者声音检查直接消费 `paper_writing_protocol.md#7.3-作者视角与建模解释`，复杂数学/证据语义只消费 `core/writing_reasoning_contract.yaml`，固定 CUMCM 骨架只消费 Template Manifest；Review 不复制这些规则。

消费时机只有两类：

- `draft_semantic_review`：正文初稿完成、AI Cleanup 前，检查数学/证据/能力激活/结构/引用风险，不要求 compile report，也不做最终交付判定；
- `final_review_and_delivery`：Cleanup、装配、正式 audit/compile 后，覆盖全文 active scope、所有 assembled seam 与机器证据，给出最终 delivery decision。

## 一、评审分级

- **blocking**：已有 Hard 违规，修复前不得交付；
- **review_required**：Default 偏离或语义裁决未闭合，需要修复或可验证 justification；
- **warning**：Recommendation / 表面风险，不阻断交付。

每个 finding 至少记录 `scope / location / authority / evidence / severity / repair / status`。机器能够证明的只按确定性证据定级；不能由关键词、词频或句式推断数学正确性。

## 二、题意、框架与局部 stale 审查

核验题目要求、附件、输出格式、单位和精度；检查 current `模型论文框架.md`、`state/project_state.yaml` 与 accepted 标准工作簿的职责边界。模型/结果/图/命题/正文 fragment 的 stale 只沿真实依赖传播，不能“整篇保险起见”全部判旧。

框架应能恢复当前模型身份、Model/Solver/Validator、Formula/Algorithm Trace、Model Construction Rationale、Reduction Provenance、solver precondition、关键参数依据、Terminology/Numeric/Title/Claim 状态、结果和图表证据位置；具体数值回到 accepted workbook。五文件合同、目录和交付内容只核对 `core/output_contract.yaml`，Review 不再复制目录定义。

### Cross-File Assembled Seam Sweep

本检查**只消费** Protocol §5A、Template Manifest 与 current Chapter Handoff Map。draft review 与 final review 均执行 `assembled seam sweep`：按最终 active physical-file 顺序逐对检查实际邻接；inactive slot 不建立虚假 seam；摘要按最终阅读位置检查，不按最后写作位置连接评价章。

对每个 seam 检查对象、符号/术语、真实依赖、claim、重复与 bridge_need。`bridge_need=required` 需要真实语义桥，但不强制独立“过渡段”；独立小问不虚构跨问继承。机器可核文件/记录/stale 冲突，不能由物理邻接、连接词或 token 相似断言语义连续。

## 三、公式、模型角色、算法、命题与数值证据审查

核心公式按 reasoning Authority 的 Source → Derivation → Destination、Core Derivation Body Closure 与 Formula Role 检查；模型建立、求解和结果解释按 Protocol 检查当前 gap、结构选择、适用边界、solver 消费、结果意义和验证边界。数学错误回上游修复，不能由风格润色掩盖。

### Question Writing Capability Activation Review

本检查消费 `core/writing_runtime_contract.yaml#per_question_writing_capability_preflight` 与当前项目状态，验证**项目状态是否在该出现时真的激活了相应能力**：

1. Formula Roles：`final_model_relation / key_bridge_relation / supporting_derivation` 与下游作用一致，必要 bridge 与恢复非显然核心推导所需的 supporting derivation 未被 Cleanup 删除；
2. Core Model Summary：`required/inline/not_applicable` 来自显式裁决；
3. Proposition：`planned/current` 自动激活 reasoning + proposition pack，candidate 只审必要性，stale 不作为 current；同时核对核心证明是否按数学作用留在正文完整可恢复，不能仅因篇幅、难度、数量预算或版式把“完整证明”降成“关键链 + 见附录”；
4. Algorithm：`stepwise/pseudocode` 自动激活 current Algorithm Trace 与 algorithm-flow pack，即使用户没有再次说“伪代码”；`not_needed` 不造装饰算法框；current trace 还必须能闭合到**真实 Python 实现**及对应结果/验证证据；
5. Missing / Stale：关键状态 missing → `needs_adjudication`，stale/review_required 不得通过 Cleanup 降级；
6. **Compact Runtime Boundary**：完整 reasoning、proof pack、algorithm pack 仍条件加载，不恢复开篇全量 preload。

上述 activation 缺口通常为 review_required；若同时造成 Hard 数学/证据错误则 blocking。

### Author Reasoning Semantic Review

只消费 Protocol §7.3 与 reasoning Authority。检查 Reasoning Necessity、Problem-Specificity、Question Closure 与 Claim Strength；不做“人工感”评分，不用第一人称/连接词频率推断作者身份；明确禁止 `first_person_ratio`、`human_like_score`、`AI_like_score`。必要理由可以保留“我们”，客观事实可以重设为对象主语；不得由表面自然度牺牲公式来源、证明、Algorithm Trace 或证据边界。

### Formula-Rich Narrative Readability Review

消费 Authority / Protocol §7。

### Core Derivation Body Closure Review

消费 `formula_reasoning_chain.core_derivation_body_closure` 与 Protocol §7，不新建 Gate。只核对当前题实际存在的非显然链是否能在正文恢复：

- 条件/规律到关键关系、方程、目标、约束或指标；
- 关键假设、变换/化简及非平凡初边值、可行域；
- 影响主结果的离散/误差关系、事件判据或 solver 前提；
- 共享模型回指、后问增量及标准定理在本题中的适用条件与落点。

普通代数可省；若缺失使模型成立、化简合法性、关键边界/可行域、solver 适用性或主要结论来源无法恢复，则按既有严重度处理，必要时 blocking。机器不能根据公式数量、篇幅、连接词或 citation 存在自动判定推导完整/正确。

### Model Construction & Solution Rationale Review

只消费 Model Construction Rationale、Reduction Provenance、solver preconditions、Numerical Parameter Rationale 和 Protocol 对应段落：

- 重要模型能恢复 `current structure → gap → chosen structure → why → applicability → downstream role`；简单直接题允许 not_applicable；
- exact / proven_sufficient / heuristic 的缩减语言匹配证据，**启发式缩域**不得写成等价或严格充分；
- solver 理由与当前结构相关，必要前提可验证；不靠通用算法优点；
- 数值参数有来源/候选/指标/选择规则，但不强制把 03A 参数证据扩成 03B 稳健性；
- **默认不要求独立“模型适用性分析”小节**，适用边界优先就地写；
- 不得由“因为/因此”等连接词判断 rationale 是否完整，**不能仅因标题较长**判标题失败。

## 四、Terminology、Numeric Style 与 Claim Strength 审查

### Terminology

按 current Registry 检查 canonical term、discouraged alias 和 confusable terms；不为“词汇丰富”轮换同义词，也不由机器自判陌生词等价。对领域专有词、项目自定义指标和专业缩写，人工审阅其首次实质出现处是否有准确、简短、邻近的含义与本题作用说明；已经解释后不要求重复定义。普通解释不足属于写作可读性问题，若术语漂移造成不同量、单位、模型类型或算法角色混淆，则按既有事实/数学严重度处理。

### Numeric Style

按 Numeric Profile 和题面/评分要求核精度、单位、百分比/百分点、科学计数法、区间等。摘要、正文直接答案和表格的必要评分精度不能为简洁而降低；图轴可简化但关键证据不可丢位数。

### Claim Strength

结论强度不得超过 Evidence Level / Scope。数值验证、算法一致性、样本观察和启发式搜索不能自动升级为严格证明、全局最优、因果或普适规律；有严格证据时也不必机械弱化成“可能”。

## 五、Title Claim、正文结构与 Paragraph Necessity

Title Claim 中的主方法/机制必须在正文实质使用并有结果证据；标题—摘要—关键词—正文模型口径一致。正文段落按 Paragraph Necessity 判断信息作用，不按字数配额。

本规则只检查**问题章节内部二级/三级小节**，不改 Template Manifest 一级结构。一级至三级正常可用，正式章节禁止四级及以上；**这不是硬计数**，自定义层级不明时人工复核。独立公式组、证明/判据、结构化简、参数证据或 solver stage 可拆，同链可合并。

同时做评委可读性复核：默认评委懂数学建模但不预设其熟悉题目所属专业领域。标题若只有专业缩写、领域概念或多个方法名而无法恢复研究对象和当前任务，按现有 Default 语义进入 review_required；必要模型名/方法名用于区分真实任务时应保留。不能为了“更通俗”把标题改成“数据处理、模型处理、结果说明、影响因素”等无对象空标题。

以下**不再自动列为 Blocking**：问题章节内部二级/三级小节超过经验数量、标题较长、使用“基于/的”等语法、段落公式较多，或标题含必要专业术语。只有实际造成语义断裂、证据缺失、模板违规或 Hard 冲突时才 blocking。

### v7.20/v8.0.1 章节能力保全检查

作为历史能力兼容回归，继续覆盖装饰性引号、solver 入口、Document Length Profile、目标函数位于约束大括号外等既有风险；这些只按当前 Authority 分级，不复制旧规则。按当前 Protocol/Runtime 检查标题/关键词、摘要逐问闭合、问题重述/分析、假设符号、条件式数据/共享基础、逐问 MODEL→SOLVE→RESULT→VALIDATE、评价/结论/附录、Citation Evidence 与自然学术表达是否按项目事实激活。此清单只检查 coverage，不复制章节写法。

## 六、深化分析、图表与结果证据审查

图表和结果必须来自 current evidence source。验证/深化分析说明它具体支持、修改或否决哪个 claim；评价不能代替验证。核心图有正文解释，解释抓决定性趋势/阈值/结构并回答设问；不逐点读图，也不补造机制。Figure portfolio 与视觉质量继续委托 Figure Authority。

`figure_table_information_value` 继续作为既有终审 coverage family，不新增新的可读性检查族。人工/混合审阅至少核对：

- 图题/表题是否让评委知道对象、比较内容或范围，而不是“结果图/结果表/算法对比”一类空标题；
- 图的轴、图例、colorbar、panel label 与表的行名、列名、单位、表注是否足以读数；正文是否只解释决定性特征和题意，未与 caption/表注机械重复；
- 表格内部 run id、代码变量、文件名和裸符号是否已经转换或补充为可读显示名，且没有改变 canonical term、数据字段或模型含义；
- 指标方向、baseline、时间/场景、样本和统计口径在需要时是否明确；无量纲量未虚构单位；
- 可读性调整是否保持 accepted 数值、单位、绝对/相对误差、百分比/百分点、排序规则和 Numeric Profile 精度不变；
- 一张表是否服务明确的主要比较问题；过宽/过密是否通过真实结构拆分而非缩字、删单位或降精度处理。

这些缺口通常是 writing/layout 的 review_required 或 warning；若已造成数值、单位、指标定义、官方格式或答案语义错误，则按对应既有 Hard 规则处理，不能因为“图表可读性”统一降级。机器可以核显式字段/引用/注册单位冲突，但不得仅凭列数、标题长度、指标名称或字符串相似度判断图表语义质量。

## 七、Citation Evidence 与参考文献审查

外部经验参数、外部数据、领域事实、非显然标准定理、既有研究比较具有真实 Citation Evidence；citation key 可解析且实际支持所述范围。本文推导/工作簿结果不得靠外引替代内部证据；机器只校键和结构，不判断文献语义支持是否充分。

## 八、编译、复现与提交包

正式交付消费最新 LaTeX audit、compile report、PDF、project sync 和 submission package validation。目录、**五文件合同**、official/reproducibility package 边界以 Output Contract/Artifact Packs 为准；Review 不复制文件列表。任何 stale source bundle、未解析引用、编译错误、manifest/hash 不一致按既有 gate 处理。

## 九、Final Submission Compliance & Evidence Sweep

### 1. 恢复终审上下文

final review 读取 current framework、state、active assembly、题目要求、verified competition rules、accepted numeric/figure evidence、audit/compile/package reports。旧聊天记忆不作为事实源。

### 2. 动态检查族

终审必须覆盖题意/输出、模型语义、数值与精度、写作能力激活、术语/claim、图表、引用、编译和提交合规。可按 physical file / question / check family 分批读取以控制上下文，但必须维护 coverage ledger；每个 active file、current question、headline claim 与 required gate 都有明确 covered 状态，**不得抽样几个章节就宣称全文通过**。

稳定的机器检查族字段为：`edition_compliance`、`anonymity_and_metadata`、`ai_disclosure`、`citation_entity_integrity`、`rendered_page_surface`、`figure_table_information_value`、`reproducibility_and_package`、`cross_question_dynamic_coverage`。这些名称只服务 `templates/review/final_review_matrix.yaml` 的覆盖闭合，不复制正文规则。每项 finding 的证据来源应明确为 `machine / manual / hybrid`；赛事规则只有 `verification_status=verified` 才可形成官方 Hard，`unverified / expired` 只能进入复核。确认的官方硬违规统一记录为 `verified_official_rule_violation`。内部审查记录**不进入 Project State**，审查中间材料与内部元数据**不得自动加入 official package**。

### 3. 原子 finding 与评分关系

finding 定位到最小可修复对象，并记录 evidence/authority/severity/repair/status。评分只消费已完成 findings，不以总分掩盖 blocking。

### 4. 已核验规则与 Hard Fail

当届官方页数、匿名、提交文件或 AI 披露只在 competition profile 已 verified 且有来源/核验日期时作为官方 Hard；未核验时标 review_required，不凭历史记忆创造规则。

### 5. 机器与人工边界

机器检查文件、hash、引用、状态、Schema、coverage 与显式冲突；人工作数学合理性、因果/机制、claim 支持、正文连续性与视觉质量判断。机器不得把“检查脚本成功”当论文内容正确的证明。

## 十、返修优先级

按 `blocking → review_required → warning`，并优先修复会使大量下游 stale 的上游问题。数学/事实错误先回模型或数值阶段；写作语义缺口回对应 Authority；纯表达问题交 Cleanup；LaTeX/提交问题交载体或 package gate。修复后只重审真实受影响范围及必要跨文件 seam/全篇一致性，不机械全文重写。

## 十一、Blocking 条件

以下任一成立不得最终交付：题意/输出硬要求缺失；current claim 使用 stale/未验收事实；必要模型/公式/约束、非显然核心推导或证明逻辑断裂；关键数值/单位/精度错误；局部/启发式结果被宣称为严格全局结论；外部核心 claim 无必要来源；正式引用/编译/包级 gate 失败；verified official rule 明确违规；或 required delivery gate 尚未成功执行。

除此之外的标题数量、第一人称、连接词、普通风格偏好等不得自动升级为 blocking。
