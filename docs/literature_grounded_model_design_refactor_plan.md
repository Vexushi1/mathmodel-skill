# Literature-Grounded Model Design：文献证据增强型模型设计改造计划

> 状态：**PLAN ONLY / 未实施 / 不作为现行运行时 Authority**
>
> 仓库：Vexushi1/mathmodel-skill
>
> 审计基线：v10.27.1，main commit 78bc7b5ae3fbcf3385ae3013d8f2e87575673f15
>
> 文档性质：修改治理下的设计和分阶段实施计划；不是已激活的模块、Schema、门禁或用户项目契约。
>
> 适用范围：当前审题—模型设计—Model Challenge—Human Model Approval 前端；不得借此重构求解、工作簿、可视化或论文交付主链。

## 0. 修改简报（本次文档 PR 与后续功能 PR 严格分开）

| 项目 | 本次文档 PR |
|---|---|
| 修改主题 | 审题后真实学术文献检索、方法迁移性判断、自主模型设计及人工锁模前证据审查的详细计划 |
| 当前版本 | v10.27.1 |
| 目标版本 | **不升级版本**；仅新增文档 |
| 变更等级 | **docs**（本文不改变现行行为） |
| 直接目标 | 建立可执行的架构决策、文件级影响矩阵、逐 PR 实施顺序、反例与验收门槛 |
| 明确不做 | 不修改 Router/Module/Authority/Schema/代码/模板/CI；不启动文献检索功能；不迁移旧项目；不自动创建任何赛题产物 |
| 权威事实源 | core/bootstrap.yaml、SKILL_CHANGE_GOVERNANCE.md 及下文第 2 节列出的现行 Authority |
| 预计手工新增 | docs/literature_grounded_model_design_refactor_plan.md |
| 禁止触碰 | 本次所有现有活动源文件、legacy/、生成索引和 MANIFEST |
| 兼容性要求 | 既有调用、暂停、锁模、任务代码与正式交付行为完全不变 |
| 迁移要求 | 本次无迁移 |
| 验收测试 | docs diff 审查、GitHub 生成文件流程、最终 head 的适用 GitHub Actions；若工作流改变了文件则重新检查 |
| 回滚方式 | 关闭/撤回本 docs PR 或以单独 PR 撤销该文档；不涉及项目状态或数值成果 |

后续功能实现预期属于向后兼容的 minor 能力；是否需要调整协议版本、Skill 版本、状态 Schema 或兼容窗口，必须在对应 PR 的最新 main 上重新裁决，不能预先视为已批准。

## 1. 目标、成功标准与非目标

### 1.1 用户的真实目标

每次新赛题先逐字审题并冻结当前小问 Problem Contract；在正式构建数学模型之前，围绕**研究对象、问题背景、数学机制、决策目标、约束和可用数据**定向查找近期发表且高度相关的真实学术研究。理解已有研究的模型、假设、方程、求解和验证，评价其在本题的迁移性，再结合独立数学推理构建针对性模型；通过既有 Model Reviewer + Devil's Advocate 质询、用户明确批准后锁模。

文献是外部知识和候选方法，不是模型选择权威；最近发表不是数学适配的充分条件；检索未找到文献也不能凭空制造文献或阻断完全可由题面和理论自洽解决的问题。

### 1.2 必须交付的能力

1. 问题导向的 Research Brief：从已冻结题意提炼检索疑问，而非按题名堆关键词。
2. 动态检索：优先近期、直接相关的原始论文，必要时追溯经典理论与反例。
3. 来源身份核验：书目、DOI/其他稳定 ID、版本、发表状态和实际访问范围。
4. 方法核验：明确哪些公式、参数、假设是**原文可定位内容**，哪些只是作者摘要/系统推断。
5. 迁移性决策：依据本题对象、目标、约束、数据、时空与信息边界给出采用/改进/对照/拒绝理由。
6. 自主建模：依旧由 Condition → Consequence、结构化简与 Minimal Sufficient Main Model 确定主模型。
7. 既有质询与批准：文献研究不创建第三套 Model Approval，不授予代码、数值结果或论文资格。
8. 可恢复且不夸大的证据链：记录实际检索状态、未核实范围、来源位置与当前问题绑定。
9. 受控开销：在竞赛时间内使用轻量/定向/深度策略，不设固定阅读篇数。
10. 测试可证：重点检查虚构文献、未经核实的方程、模型锚定、无关 stale、未经批准代码和旧项目兼容。

### 1.3 明确非目标

不做自动系统综述、批量下载受版权限制的 PDF、第三方文献库永久同步、自动论文复现、自动宣称学术首创、按引用量选主模型、固定双路线/三路线配额、重新设计数值模型审批、不改变用户自有 full_fidelity 任务代码执行边界、不为文献检索重写论文引用或机器审查体系。

图表 QA、最终 PDF 排版 QA 和视觉案例库另立主题及 PR，不混入本项目。

## 2. 当前仓库权威图与发现

### 2.1 Bootstrap、Router 与运行时

- SKILL.md 是入口摘要，core/bootstrap.yaml 声明 Authority 指针；全局规则由 core/hsk_core_policy.md 管理。
- core/workflow_router.yaml 维护 default_load、routing、execution_contract、runtime_segments、reading_policy。
- core/module_manifest.yaml 负责模块输入/输出、Artifact Catalog 和 Gate 生产消费闭环。
- scripts/resolve_runtime.py 是默认解析入口；scripts/resolve_workflow.py 仍承担路由、模块依赖与暂停计算；scripts/reading_plan.py 与 scripts/read_stage.py 指导/验证按需读取。
- core/runtime_assurance_contract.yaml 与 scripts/runtime_assurance.py 负责意图证据、项目 hydration、当前语义身份、Contract Dependency Closure、读集和 Authority Fingerprint。
- **Reading Plan 是读取指令，不证明资料已经读取；工具导航不是工具实际执行；检索协议加载不等于真实论文检索完成。**

### 2.2 当前建模主链（保持不变）

problem_audit → model_design → data_preprocessing（条件）→ solve_validate → result_analysis（条件）→ figure_evidence → writing_latex / writing_docx（按载体）→ ai_cleanup / latex_compile_quality（按需）→ review_delivery。

模型设计中的关键既有规范：

- modules/01_problem_audit.md：Problem Contract、数据角色、题型轴、typed 小问依赖及题意冻结。
- modules/02_model_design.md：题目数学本体、Condition → Consequence、exact/proven_sufficient/heuristic 化简、最小充分主模型、0..N 信息型 Comparator Envelope、后置 Solver、Formula Trace、PQS、Construction Rationale、独立 Model Challenge、Human Approval。
- core/model_approval_contract.yaml：显式用户批准、Model Challenge、current semantic_revision 与 validated structured semantic_identity_hash 绑定。
- scripts/semantic_identity.py、scripts/validate_semantic_governance.py 与 scripts/validate_model_approval.py 是当前数学语义身份/审批执行与校验链；不得由文献证据写入批准。

### 2.3 其他已有证据系统的明确边界

| 现有能力 | 现有权威/实现 | 新功能应如何相处 |
|---|---|---|
| D1/D2 Case Memory | knowledge/case_memory/schema.yaml、core/case_memory_retrieval_contract.yaml、scripts/case_memory_retrieve.py、scripts/case_references.py | **合成案例、有界离线检索**。可学习其来源哈希、可迁移条件和 read-only/record 分离的工程模式，不把真实论文当成已准入合成案例 |
| Citation Evidence | core/writing_reasoning_contract.yaml#citation_evidence、模型论文框架相应小节 | 继续作为**已采用外部主张进入论文的引用链**；不承担搜索、全文核验或模型适配 |
| B1 Claim Evidence | core/claim_evidence_contract.yaml、scripts/claim_evidence.py | 现有声明数值来源及有限算术检查，**不是** DOI 或学术文献真实性检查 |
| B2 Claim Consumption | core/claim_consumption_contract.yaml、相应 scripts | 保留现有论文主张消费与证据边界；新研究不替代它 |
| Project State / stale | core/project_state.schema.yaml、core/state_transition_contract.yaml、scripts/state_transitions.py | 不以文献检索状态自动覆盖数学语义失效；尽量不改基础 Schema |
| 项目框架 | core/output_contract.yaml、templates/model/model_paper_framework.md、scripts/instantiate_model_paper_framework.py | 继续保存当前项目语义摘要，不保存整套文献全文；遵守既有创建时机、compact/full 投影与校验 |

### 2.4 需要在 P0 裁决的既有文档张力

- modules/01_problem_audit.md 描述审题时将 Problem Contract 写入模型论文框架对应小问。
- core/output_contract.yaml 当前声明 model_paper_framework.create_after = proposed_model_spec。

不能在未核对现有实例化器、用户项目实际行为与测试前，直接把这一表述差异判定为已发生的运行错误，也不能通过新研究模块擅自把框架提前创建。

**P0 必须解决**：在 proposed_model_spec 形成前，审题结果和 Research Brief 如何暂存、跨聊天如何恢复；若使用独立研究报告，何时创建/确认它，怎样在正式框架形成时无损投影，是否涉及原有 Schema 和目录 Authority。先做行为追踪和测试，再作单点兼容修复；不得在文献功能 PR 中偷偷修改框架生命周期。

## 3. 拟定端到端流程和明确权限

### 3.1 研究应插入的逻辑位置

1. **Module 01** 逐字审题与附件审计，冻结每问 Problem Contract；只识别未来可能需要查证的领域机制，不在此选择论文中的主模型。
2. **Module 02 初步独立结构判断**：按当前本体初始化区分定义、题设硬条件、守恒、本构、假设、近似、决策以及时间/空间/信息边界；形成尚未锁定的数学疑问。
3. **Research Brief**：根据当前题意生成研究对象、目标、机制、数据限制、研究疑问、双语检索词、时间窗口、禁止假设和预计证据用途。
4. **定向真实检索**：检索高度相关近期研究、必要基础理论、方法比较和反例；按可用合法 Provider 执行。
5. **身份及内容核验**：候选识别、去重/版本关联、原文可见程度、可定位方法证据。
6. **迁移性与反证评价**：逐问映射原文目标/变量/约束/假设/参数/尺度/验证范围到本题，形成 adopt/adapt/comparator/reject 决策。
7. **自主模型构建**：将文献建议与题面结构推导并列评价；保留数学上必要的复杂度，明确更简单模型失去什么；选择唯一当前最小充分主模型及按需 Comparator Envelope。
8. **原 Model Design 闭环**：Formula Trace、模型/算法/Validator 分离、PQS、参数证据、预处理决策、Complexity Sanity、具体 Solver preconditions。
9. **原独立质询**：Model Reviewer 与 Devil's Advocate 检验文献适用、引用边界、遗漏反例、虚构新颖性及可计算性。
10. **原 Human Approval**：形成 Brief，停在 awaiting_model_approval；用户显式批准当前经验证的数学语义身份，才允许 locked_model_spec。
11. **后续 03A/03B/Figure/Writing**：只消费其本来需要的已采纳来源与证据，不额外自动重做全文检索。

### 3.2 权限边界

- 文献不能修改冻结的题目对象或约束。若新证据提示原审题错误，必须回到 Module 01 按现有规则重新审题。
- 文献可启发候选主模型/基线，却不能直接生成 locked_model_spec 或数值 accepted 状态。
- 不以文献作者报告的实验结论替代本题模拟、观测、验证或用户执行回执。
- Model Reviewer/Devil's Advocate 仍是原有两次独立审查；研究者不能以来源权威绕过审查。
- 不强制每问有两套路线。现有 Module 02 已明确主模型 1 个、comparator 为 0..N，只有明确检验价值才建立。
- 不凭新论文存在就宣布原模型无效，也不凭检索不足而宣布学术首创。

## 4. 研究触发、检索深度、停止和恢复

### 4.1 任务矩阵

| 请求 | 研究处理 |
|---|---|
| 单纯逐字审题 | 生成可能的研究需求，不越界执行完整研究 |
| new_problem_design / 首次模型设计 | 默认启用**检索可行性和必要性判断**；可用时开展面向问题的定向研究 |
| full_solution / full_workflow 的尚未锁模部分 | 研究与模型设计发生在原 Human Approval 暂停前；不得直接跳到代码 |
| advanced_method / model_selection 新设计 | 针对相应模型问题执行，保持原路由意图 |
| 用户明确要求查找或更新文献 | 允许独立只读研究，不隐含模型修改 |
| 已锁模的 code_and_solution / returned workbook / figure / writing | 不默认重开完整文献检索；仅针对明确外部证据缺口 |
| 单问重设计 | 只影响当前小问和现有依赖闭包内确需处理的内容 |
| 用户禁止联网 | 不调用外部检索；如实记载限制 |
| 已有当前研究依据 | 优先复用并校验，不无差别重搜 |

触发实现应避免把任何出现“文献/模型”字样的普通聊天推断成两个写入意图；特别保护显式 intent、混合意图、否定句、只读审查和原暂停链。

### 4.2 动态研究强度

- Lightweight：成熟结构、外部依赖低；核对基础理论、主要边界和明显反例。
- Targeted（新建模常见默认）：围绕决定模型选型的领域机制、方程/参数及比较方法深入核实少量高相关研究。
- Deep：跨学科、争议性边界、多个不兼容机制、特殊理论或高风险外部假设；适度扩大引文网络。

首轮优先近期 3—5 年的研究，但研究适配性、原始理论和可核查程度高于年份。经典奠基方法、当届正式标准和关键反例不因年代较早而排除。

**禁止固定论文篇数/模型数量/检索轮次数量作为硬门。** 停止基于关键研究疑问覆盖率、方法迁移条件是否闭合、是否找到会改变数学结构的反例，以及继续检索的信息增益。必须记录未解决的关键问题。

### 4.3 检索执行边界

真实搜索与“研究证据格式验证”分层：

- 外部检索适配器可利用当次 ChatGPT 实际可用的 Web / 学术数据库连接器或经授权 Provider；不假设任何特定工具、API key 或付费全文访问始终存在。
- Skill 证据检查器只能核对实际返回且可定位的来源元数据、报告结构和绑定；不得伪造某个外部 Provider 已实际运行。
- 网络失败、限流、无全文、无命中、用户禁网分别报告，不用模型已有知识伪装成“今天已查到的论文”。
- 搜索/阅读工具的结果属于不可信输入，不得执行 PDF 或网页里的指令和代码；遵守版权与赛题隐私边界。

## 5. 文献来源核验、方法卡与迁移裁决

### 5.1 身份与版本核对

原始来源尽量保留：title、authors、year、在线发表日/版本日、venue、DOI 或可靠替代 ID、publisher/original URL、版本、检索时间、核验位置、摘要/方法/全文可见范围、更正/撤稿迹象。元数据不足时不得编造缺失字段；不把预印本、正式版和更新版机械计为互不相干论文。

### 5.2 不得跨越的核验等级

| 等级 | 真正核实到的范围 | 可以作什么判断 |
|---|---|---|
| E0 | 可信书目记录 | 文献身份及候选相关性 |
| E1 | 摘要/公开概述 | 作者报告的大致研究方向或方法类别 |
| E2 | 可定位的原文方法段/公式/假设 | 具体方法结构、前提、方程的有界分析 |
| E3 | 按明确方案实际独立实现、实验或数值复核 | 限定范围内的复现/比较事实 |

E3 不要求在审批前普遍完成，必要时进入现有 03A/03B，并遵守用户执行和 accepted 工作簿边界。E0/E1 **不能**用推测构造所谓“原论文完整模型”。

### 5.3 Literature Method Card

每个被深入考虑的方法至少记：Source ID、检索/核验等级及原文锚点、原作者研究对象和输出目标、变量/单位/数学结构、假设/初边界/信息边界、数据和参数要求、原文 Solver 与验证范围、限制条件、当前题目的条件映射、可采用部分、不可迁移部分、备选基线/对照用途、使用或拒绝理由、仍未闭合的证据缺口。

**方法卡是论文方法的有限核验记录，不是证明其在本题有效的证书。**

### 5.4 决策分流

- adopt_as_basis：原始模型在本题关键适用条件成立；
- adapt_to_problem：存在确切缺口，允许明确数学改造；
- use_as_comparator：只为某项信息增益提供基线/替代机制；
- use_for_validation：提供可实施的独立检验或误差诊断；
- reference_only：背景、理论或参数来源；
- reject：明确条件冲突；
- insufficient_evidence：原文或关键证据不足。

必须保留被否决的关键方案理由，而不是只列采用论文。采用文献理论时仍独立推出当前题目的方程/目标/约束；不能把旧模型改名或简单叠加算法当创新。

### 5.5 Novelty Claim 边界

可以说“相对本次核验的文献候选，本题增加了 X 机制”，前提是能够定位差异；不能仅凭有限检索声称“首次提出”“全球首创”。将**原文已有**、**当前题目独立推导**、**本题定制改进**、**待计算验证的猜想**分别标注。

## 6. 模型设计、审批和论文的既有 Authority 衔接

### 6.1 Module 02 内容修改方案

在“问题本体初始化/关键条件结构初判”与“正式主模型生成”之间增加文献 Evidence Intake 的调用规则。Module 02 只保留项目级选择和推理链的执行顺序，来源验证等级/检索规则由单一新的 Authority 定义。

保持：
- 先结构，后 Solver；
- 不能由文献模型名决定题目结构；
- exact/proven_sufficient/heuristic 的原有等级；
- 当前主模型最小充分性；
- 0..N Comparator Envelope；
- accepted 后才确定正式 03B 深化方案；
- 现有 Algorithm Trace、Formula Trace、PQS、Preprocessing Decision 和论文身份字段。

### 6.2 Model Challenge 最小增强

Model Reviewer 增补：文献条件是否真正适用；外部经验参数、非平凡理论是否被核实；是否遗漏重要反例；更简单结构是否足以回答题目；是否把未核实方法冒充完整研究。

Devil's Advocate 增补：文献来源可信度偏差、时间新颖性偏差、原文与题目尺度不符、缺失关键数据、作者验证范围外推、所谓创新已为已知结构/同类方法的可能性。

所有 blocking/review_required/warning 仍按当前 core/model_approval_contract.yaml 处分；不新增第三个审批 Agent，不允许外部证据通过机器生成 approved_semantic_identity_hash。

### 6.3 Model Approval Brief

在**现有 Brief** 中摘要显示：少量最关键的来源、被采用的具体数学结构、本题与来源的不同、方法迁移条件、真正的创新假说/已验证边界、主要被拒方法、未核实风险，以及为何仍是最小充分主模型。完整搜索结果不塞入 Brief。

### 6.4 Citation Evidence / Writing 接口

新研究产物记录检索、阅读、评估和采用判断；core/writing_reasoning_contract.yaml#citation_evidence 继续负责外部主张和论文 citation_key。没有最终论文使用价值的检索候选不需都成为 BibTeX 条目；已有自身推导与数值证据不能被引用替代。

模型论文框架只保存**项目当前有效的研究决策摘要**及必要的来源映射，不保存全文和历史检索日志，避免与当前 framework/current-only 语义冲突。

## 7. 研究证据产物、绑定与语义身份

### 7.1 首版最小产物

建议在正式实现时由 core/output_contract.yaml 裁决是否引入**一个**项目级可选研究报告，如：

- 候选路径：文献研究/literature_evidence.json；
- 覆盖多个小问，分别存 Research Brief、来源条目、Method Card、adopt/reject、证据缺口；
- 默认不将报告或下载的论文全文加入赛事 official submission ZIP；
- 路径、大小预算、敏感信息清理、编码、版本、规范化哈希和文本长度必须在新 Authority 明确；
- 目前只是**候选接口**，不是当前有效产物或目录规则。

在提出模型前尚无正式框架的阶段，如果用户请求持久恢复，必须首先解决第 2.4 节的 P0 生命周期问题；临时聊天文字不是可校验的磁盘证据，也不能提前自称已建立 current framework。

### 7.2 研究报告双层状态

**检索是否真实执行**与**研究证据是否充分**必须分开。

候选执行状态：completed / no_suitable_source / unavailable / skipped / failed。
候选证据状态：sufficient / partial / insufficient / not_required。

两者只是独立研究报告的候选字段；不得直接加入当前 Project State。若网络不可用但本题可通过纯数学推理闭合，可带风险继续设计；若关键经验参数或理论不可证，则不得虚报已满足模型前提。

### 7.3 Problem Contract 与研究报告的当前性

只要声称“研究基于当前 Problem Contract”，就必须有可复核的**当前来源锚点或具体范围内容身份**；只记录 Research Brief 的自有 hash 无法单独证明整份 Problem Contract 当前有效。

建议研究记录包含：当前 Qn、审题有效范围标识、实际源 anchor/hash（若可取得）、Research Brief hash、检索范围/时间、Provider 身份、研究规则版本、实际核验文献及其可定位位置。任何不具备的锚点报告为 unverified，不允许把 string equality 当数学适配证据。

### 7.4 不扩展 SIB 以容纳引用元数据

保留 scripts/semantic_identity.py 当前 schema/canonicalization。DOI、发表年份、来源页面、检索时间和论文引用位置**不属于数学 SIB**；单纯文献元数据变化不触发重新锁模。

若文献研究导致**当前模型的变量、数学参数、假设、目标、约束或算法语义**改变，则按原现有 semantic_revision、Model Challenge 与 Human Approval、typed stale 机制处理。新研究检查器不得直接调用自造的 stale 事件。

### 7.5 不直接加入 Project State Schema

第一版计划先只读证据检查和现有框架中的简洁研究摘要。若后续确需自动记录 currentness/跨聊天恢复，单独论证 project_state.schema.yaml 的新可选字段、项目事务、legacy 兼容、读集和 stale 规则，并在额外 PR 实施。绝不在本轮 P1 用 add-anything 的方式扩张封闭 Schema。

## 8. 故障/更新/回退决策表

| 事件 | 研究来源层 | 数学/项目状态层 |
|---|---|---|
| 没有检索工具、禁网或 Provider 失败 | 明确 unavailable/skipped/failed；不伪造完成 | 不自动撤销模型；关键外部前提未核实可产生 blocking |
| 检索实际完成但没有适用论文 | 标记 no_suitable_source 及已搜索范围 | 允许本题独立推导 |
| 仅访问摘要 | E1，具体原文公式标未核实 | 不允许把原公式当已验证前提 |
| DOI 修复或引用链接更正 | 研究/引用 provenance 更新 | 不改变 SIB |
| 新论文出现但不改变模型 | 必要时 review source/创新表述 | 不触发原审批 stale |
| 原始来源撤稿或被更正 | 对使用该来源的主张标风险和替代证据 | 根据受影响的假设/参数/方法做实质审查，不机械全链撤销 |
| 文献表明原模型关键假设不适用 | needs_model_review | 真实数学变更后走原 semantic_identity_changed |
| Problem Contract 发生有效变更 | 研究关联范围需要重查/重评 | 原 Module 01 与跨问 typed dependency 规则处理 |
| 用户要求仅更新学术引用 | 只读检索、Citation Evidence 修正 | 不自动修改已批准模型 |
| 已批准项目继续数值/图表/写作 | 复用已知当前来源 | 不以缺失新研究产物阻断旧项目 |

注意：**来源的新鲜度不等于模型数学身份的新鲜度**。每次新增搜索结果也不意味着过去的所有研究决定自动失效；“当前性”评价由真实被消费的来源范围和具体数学影响决定。

## 9. 文件级改造地图：检查、候选修改、不改范围

### 9.1 本文档 PR（当前允许的全部手工 diff）

**只新增 docs/literature_grounded_model_design_refactor_plan.md。** 不修改任何已有文件；不升级 v10.27.1；不更改 Router、Schema、模板和 Python 实现。生成索引/MANIFEST 若受影响，仅由既有 GitHub refresh-generated 管理，不手工写入。

### 9.2 后续 P1 / P2：研究规则与最小协议

| 路径 | 拟定职责 | 约束 |
|---|---|---|
| core/literature_research_contract.yaml（候选新增） | 来源核验、研究等级、迁移性、失败和资源边界唯一 Authority | 避免与 Citation Evidence / Case Memory / model approval 复制规则 |
| packs/artifact/literature_research.md（候选新增） | 实际执行指南、Method Card 和决策输入/输出 | 仅引用新 Authority 的通用规则 |
| modules/01_problem_audit.md | 输出检索疑问/Research Brief 输入 | 不把检索结果反向冻结为题意 |
| modules/02_model_design.md | 将真实研究与独立数学推理连接到主模型/质询 | 仍是唯一当前主模型设计入口 |
| scripts/literature_evidence.py（如确有需要） | 只读报告结构、身份、来源锚点检查 | 不联网、不模拟检索、不授予状态与批准 |
| tests/test_literature_research.py（候选新增） | 证据强度、来源冲突、无搜索与恶意文本负例 | 用独立/合成的测试元数据；不要求 CI 联网 |

### 9.3 后续 P3：路由、加载与依赖闭包

| 路径 | 检查/修改目的 |
|---|---|
| core/workflow_router.yaml | 原 new_problem_design/model_selection/full_solution/full_workflow 的研究必要性接入；可选独立只读研究意图；既有 pause/gates 严格不变 |
| core/module_manifest.yaml | 只有在真实研究产物进入路由时登记 Artifact Catalog、必要输入/输出与消费者；不虚报可用 |
| core/bootstrap.yaml | 如需新增 Authority 发现指针，保持 bootstrap 极简 |
| core/runtime_assurance_contract.yaml | 按真实模块消费需求纳入 dependency closure，不能仅因加载新 Pack 破坏精简读取 |
| scripts/resolve_runtime.py | 只有现有数据流不能表达新路由/研究导航时才做最小修改 |
| scripts/resolve_workflow.py | 保护 explicit intent、模块顺序、pre_delivery_gates、pause boundary；不是默认重写目标 |
| scripts/reading_plan.py / scripts/read_stage.py | 必要时新增条件式读取配置；研究工具声明≠调用成功；不得降低 read-set/selector/authority currentness |
| tests/test_case_memory_routing.py、tests/test_reading_plan.py、tests/test_v712_runtime_assurance.py 等 | 回归检索与独立研究共存、旧路由和项目恢复 |

### 9.4 后续 P4：框架、模型质询与来源消费

| 路径 | 条件及目的 |
|---|---|
| core/output_contract.yaml | 需要新增持久产物时裁决唯一目录/路径/保留规则 |
| templates/model/model_paper_framework.md | 只添加当前项目研究决策摘要，确保 compact/full 兼容 |
| scripts/instantiate_model_paper_framework.py / scripts/validate_model_paper_framework.py | 只有新增章节真的影响投影/校验才改；旧 compact 实例不得失效 |
| core/model_approval_contract.yaml | 在原 Model Reviewer / Devil's Advocate 增加文献条件及 provenance 审查；**不新增 Approval State** |
| core/writing_reasoning_contract.yaml | 只有现有 citation_evidence 缺少明确交接语义时才增补单点引用 |
| modules/06_review_delivery.md | 如有必要，在当前证据终审中检查实际使用的外部方法出处，不重复正文引用规范 |
| tests/test_v711_model_approval_gate.py、tests/test_framework_project_memory_contract.py 等 | 验证无额外审批、无误锁模、框架读写兼容 |

### 9.5 默认禁止碰触或必须另立重大设计审查的接口

- scripts/semantic_identity.py（数学语义身份）
- core/project_state.schema.yaml（机器状态）
- core/state_transition_contract.yaml、scripts/state_transitions.py（typed stale）
- scripts/sync_project.py、scripts/project_transaction.py（项目同步与事务）
- core/user_execution_contract.yaml、core/numerical_verification_contract.yaml、core/workbook_schema.yaml（03A/03B 数值证据）
- core/case_memory_retrieval_contract.yaml、knowledge/case_memory/（D1/D2 合成案例边界）
- core/claim_evidence_contract.yaml（B1 自有数值来源边界）
- 跨载体论文模板、MATLAB/Python 求解模板、图表、PDF 编译及官方提交规则

这些文件**仍需审查影响**，但不能默认作为“实现文献研究”的编辑目标。任何无法避免的修改必须说明必要性、拆出独立兼容 PR、测试迁移及回滚。

## 10. 分阶段实施与 PR 切分

| 阶段 | 核心交付 | 通过后允许的下一步 |
|---|---|---|
| P0 — 行为基线与前置裁决 | 当前 main/PR/Authority/真实路由/框架创建时机、已有研究能力与可访问检索工具审计；可核对黄金行为样例 | 无开放的生命周期冲突再设计接口 |
| P1 — Literature Authority + 只读数据合同 | 有限 Schema、检索状态、来源等级、研究卡、适配决策、负例测试 | 不实际接入模型写入 |
| P2 — Module 01/02 研究融合 | Research Brief、结构初判、证据评价→数学模型设计及两轮审查增量 | 不提前锁模或生成代码 |
| P3 — 真实 Runtime/Reading/Provider 适配 | 任务触发、可用检索执行适配、来源核验报告、恢复和失败降级 | 测试验证路由不改旧 pause/gates |
| P4 — Optional artifact / Framework / Citation handoff | 如有必要引入唯一项目研究报告、项目摘要和引用交接；当前性绑定 | 未验证来源/已锁数学身份不能自动变更 |
| P5 — 有限门禁（仅在证明必要时） | 可选适用的新项目研究证据入场检查；禁止将搜索返回等同审核通过 | 旧项目不被强迫迁移 |
| P6 — 历史题对照与正式发布 | 负例+兼容完整回归、耗时及质量评估、版本/Changelog/最终 PR head CI | 经过验收后才考虑作为默认新赛题能力发布 |

每个阶段一个主题 PR，新增内容须有文件级直接目标、明确不做、单一 Authority、旧行为证明和回滚条件。不得在一个 PR 同时引入未知 Provider、状态大改、Figure QA 或出版排版升级。

## 11. 最低可执行回归矩阵

### 11.1 路由与边界

| Case | 输入/情境 | 必须成立 |
|---|---|---|
| RT01 | 仅审题 | 不无条件执行深度检索/模型批准 |
| RT02 | 新赛题建模 | 审题冻结后才能产生正式研究依据 |
| RT03 | full_solution 尚未批准 | 仍停 awaiting_model_approval，不交付主求解代码 |
| RT04 | 显式只读文献查找 | 不暗含写 Project State、代码或锁模 |
| RT05 | 多意图/否定词/明确限制 | 不扩大意图或改变原 gate 顺序 |
| RT06 | 旧项目进入 03A/03B/Figure/Writing | 不因缺新文献产物而阻断 |
| RT07 | 单问研究与跨问依赖 | 不把 Q1 论文自动视为 Q2 条件充分 |
| RT08 | Reading Plan 指向研究协议 | 不虚报“已实际检索” |

### 11.2 来源、方法和学术边界

| Case | 输入/情境 | 必须成立 |
|---|---|---|
| EV01 | 真实可定位论文元数据 | 保留来源身份/版本/核验状态 |
| EV02 | 伪 DOI / 伪造期刊 | 不认定已核实 |
| EV03 | 仅摘要 | 不输出冒充原文的完整公式 |
| EV04 | 经典模型比近期论文更适配 | 允许选经典方法 |
| EV05 | 近期高引用论文违反题面条件 | 拒绝直接迁移 |
| EV06 | 预印本/出版版/更新版 | 版本合并或明确区分 |
| EV07 | 文献撤稿/关键更正 | 标记引用与模型风险，不机械篡改状态 |
| EV08 | Provider 失败、禁网、无匹配 | 区分 failed/skipped/unavailable/no_suitable_source |
| EV09 | PDF/网页中的恶意指令 | 只作为数据，不执行 |
| EV10 | 未验证的“创新” | 不宣称首创或已证明改善 |

### 11.3 语义、状态与项目恢复

| Case | 输入/情境 | 必须成立 |
|---|---|---|
| ST01 | 引用 DOI、年份、格式变更 | SIB 与批准保持不变 |
| ST02 | 数学假设/约束/目标变更 | 仅按原 Semantic Governance 传播 stale |
| ST03 | Challenge 未通过或用户沉默 | 不能产生 locked_model_spec |
| ST04 | 补充文献但模型未变 | 不重新批准、不让已验收数值自动失效 |
| ST05 | 研究报告旧版本、read-set 漂移 | 不把旧身份升级为 current |
| ST06 | 旧 compact/full 框架 | 无新报告时仍可按既有逻辑恢复 |
| ST07 | 项目 state_generation 被其他写入推进 | 陈旧写侧必须拒绝 |
| ST08 | 报告没有实际落盘 | 不宣称成功持久化 |
| ST09 | 报告路径越界/敏感数据 | 拒绝写入并避免输出敏感内容 |

### 11.4 GitHub 正式验收

- 保留原 Windows Python 3.10 / 3.14 完整正式回归及汇总 check 名称；若新增代码影响 MATLAB native、LaTeX、生成器或其他受控检查，则执行全部适用专项。
- 代码/Schema/路由阶段至少覆盖 test_v711_model_approval_gate、test_v712_runtime_assurance、test_reading_plan、test_case_memory_routing、test_case_references、test_framework_project_memory_contract、test_sync_project、test_v900_state_transitions、test_runtime_consistency_repairs 以及相关 intent / state / source read-set 测试。
- 只依赖测试名称不够：应增加真实失败用例与拒绝条件，尤其是“文献检索未执行却报告 completed”“元数据改变导致误 stale”“未经批准代码”“检索工具声明冒充已调用”。
- 正式证据为最终 PR head 的 GitHub Actions checkout commit、分片完整覆盖、生成文件状态和工作流结果。不能以本地静态检查、某一次专项通过或旧 head 结果代替正式验收。
- 此 docs PR 只按 docs/生成文件治理执行，不能将文档提交等同于功能测试通过；如果 refresh-generated 产生新 commit，重新核验最终 head。

## 12. 历史题效果评价及发布准则

使用不同题型的真实历史赛题构造非污染对照，基线为**原有独立模型设计**，候选为**文献增强设计**。比较同等题目/附件/时间或资源预算下：

1. 关键题设覆盖率与错误假设数量；
2. 主模型数学充分性、可迁移前提和最小复杂度；
3. 对经典基线/独立算法验证的设计质量；
4. 来源真实、公式核验、引用有效和过度创新声明；
5. 可实施计算要求、推导与数值检验闭环；
6. 研究成本：外部搜索次数、阅读成本、重复检索及端到端设计耗时；
7. 独立审查的实质性阻断问题数量和修复成本。

不以检索到论文更多、使用了较新模型、引用量更多或问答篇幅更长作为“能力提升”。不预设提升百分比。若研究成本显著上升却没有质量增益，则必须改用更窄的 Targeted/Lightweight 条件，而不是强制全题深搜。

## 13. 实施前必须回答的开放裁决

1. **审题与框架时机**：Module 01 的 Problem Contract 写入描述和 output_contract.create_after 的真实用户项目行为如何兼容？哪些历史测试证明当前路径？
2. **检索 Provider 能力**：实际使用哪些授权工具、支持哪些字段、如何证明检索执行、怎样处理无联网或无法获取全文？
3. **最小研究产物**：首版是只读对话报告还是一个有界文件？是否确需跨聊天持久化？如果需要，何时创建、怎样按 P0 规则存放？
4. **现有 Citation Evidence 是否足够**：哪些字段真正缺失？是否只需 Method Card 到 citation_key 的映射，不需修改 Citation Authority？
5. **Reviewer 改动位置**：哪个 Authority 定义审查，Module 02 如何只引用？避免相同审查规则复制两份。
6. **路由实现边界**：现有 Router 与 resolver 能否无需代码修改支持新显式 research intent 和模型设计默认研究？不得未经实测声称兼容。
7. **Project State 是否真的需要变化**：首版优先完全不动；需证明现有恢复场景不可满足才能开启独立字段/事务 PR。
8. **不同竞赛资料与 AI 规则**：由当前当届核验的 competition_profiles / packs 处置，研究模块不得覆盖官方规则。
9. **文献方案创新判断**：如何保证 Reviewer 检查迁移条件而不是只检查“是否引用了近期论文”？
10. **文档与功能 PR 分隔**：docs-only 无版本升级；未来功能 PR 根据当时最新 main、重叠 PR 和实际影响重新提出修改简报。

## 14. 兼容、回滚和 Definition of Done

### 14.1 硬不变量

- 原 Problem Contract、User Execution、PQS、03A/03B、工作簿、Figure、Writing 规则不变；
- 原现行 Model Approval 明确用户批准，validated SIB 与 approved identity 精确绑定；
- 旧项目缺少新文献报告时仍能继续合法的原任务；
- 研究搜索或报告失败不生成成功信号；
- 外部文献/网页是不可执行数据；
- 原 pre_delivery_gates 有序执行，且 Gate 不由读计划代替；
- 数值结果仍只来自用户真实运行并验收的工作簿；
- 研究的参考文献变更与数学语义变更分离。

### 14.2 发布完成的判据

实际新赛题能够在审题后完成受控且可核查的真实学术检索（或如实降级），说明模型迁移与自主选择理由，顺利进入原 Model Challenge/Human Approval，未获批准不输出正式求解代码；旧路径保持兼容，历史赛题对照有实证支持，最终 PR head 的正式 CI 全部通过。

### 14.3 回滚

功能必须通过条件路由关闭，不改变旧项目语义、审批和 accepted 数值；研究产物可作为只读资料保留。出现结构冲突时，优先撤销新增研究自动路由，保留原 Module 02 执行路径；任何 Project State 迁移须有单独恢复策略。

---

## 15. GitHub 实施纪律

执行 SKILL_CHANGE_GOVERNANCE.md：每轮从当时最新 main 读取 bootstrap 和治理，核对未合并 PR，先形成具体修改简报；一次聊天一个明确分支、一个 PR 一个主题，禁止直接写 main。仅提交源文件，受管索引/阶段阅读指南/MANIFEST 按 refresh-generated 自动生成并逐项核验。冻结最终 head 后执行规定的远端验收；未通过不合并。本文是计划，不代表任何阶段已实施或已通过测试。

**最终立场**：题目驱动检索、文献提供外部研究方法、独立数学推理决定最小充分主模型、真实证据支撑结论、独立质询识别迁移风险、用户明确批准完成锁模。