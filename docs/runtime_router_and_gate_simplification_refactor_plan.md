# 运行时路由与门禁简化完整重构计划

> **文件性质：** 仓库维护计划，不是 Runtime Authority，不直接改变 Skill 的运行行为，也不代表任何测试已执行或通过。  
> **编制日期：** 2026-10-23（北京时间）。  
> **执行记录更新：** 2026-10-24（北京时间）。  
> **当前基线：** `Vexushi1/mathmodel-skill` 的 `main@75d772c84b75290f59f79b4d3e1eb2747e4eb3ec`，Skill v10.23.1。  
> **正式发布基线：** GitHub 最新 Release 仍为 v10.23.0，指向旧提交 `2c79599b80763a8840a4b0ee79f85271f9234c6a`；v10.23.1 尚未发布。  
> **前置事项：** PR #276 已合并至上述 main；其最终源 head `b049ca8cd9718d50a070ad0d9b33a2a3351cebed` 的完整 CI 与 Optimization baseline 均通过。合并后的 main CI `39999918643` 在本记录编写时仍在执行，必须确认后才能启动阶段 B 实现。

本计划只把用户已经明确提出的目标转化为可实施、可审查、可回滚的工作流程。实现期间不得自行扩展为新建一套数学建模流程、额外审批系统或另一套门禁系统。

---

## 0. 修改简报

| 项目 | 计划 |
|---|---|
| 修改主题 | 运行时路由、重复状态登记与交付门禁的简化重构 |
| 仓库 | `Vexushi1/mathmodel-skill` |
| 当前版本 / 基线 | v10.23.1 / `main@75d772c84b75290f59f79b4d3e1eb2747e4eb3ec` |
| 目标版本 | 暂不预设；根据实现 diff 与兼容性审查，按治理规范确定 |
| 变更等级 | 暂不预设；内部实现且兼容时按实际规则评估 patch/minor，只有确有破坏性接口或 Schema 变更时才评估 major |
| 直接目标 | 模板可选、通用建模可直接启动；移除没有独立质量价值的重复检查、重复状态登记和过早执行的正式交付门禁；保留真正保障模型、数值、代码、图表和论文正确性的必要检查 |
| 明确不做 | 不重写六个核心专业领域；不修改题目的数学模型或算法；不取消 Model Challenge、人工批准、公式与约束审查、真实数值执行和必要结果验收；不为显示“重构规模”而随意删除兼容接口 |
| 权威事实源 | `AGENTS.md`、`SKILL_CHANGE_GOVERNANCE.md`、`core/bootstrap.yaml`、`core/workflow_router.yaml`、`core/runtime_assurance_contract.yaml`、`core/module_manifest.yaml`、`core/project_state.schema.yaml`、`core/state_transition_contract.yaml`、`core/output_contract.yaml` 及其实际消费者 |
| 预计涉及范围 | 路由与运行时解析、门禁适用范围与执行时机、状态事实归属、绘图混合意图读取、相关测试和必要的入口说明 |
| 禁止触碰范围 | 任何与目标无关的业务模块、数学公式、求解算法、真实用户项目和结果文件；所有生成索引与 `MANIFEST.sha256` 均不得手工编辑 |
| 兼容要求 | 已有 CLI、旧项目读取、项目状态、工作簿、模型批准身份与交付证据尽量保持兼容；如需改变，必须先证明必要性并写出迁移方案 |
| 验收方式 | 遵循 GitHub-only 仓库维护流程；专项回归之后，必须对题目分析、模型建立、求解精度、求解规范、结果深化分析和论文写作六个方面重新进行完整回归审查 |
| 回滚方式 | 按单一主题分支和 PR 推进；各批次能单独 revert；回滚不得伪造旧 PASS、恢复过期批准或抹除用户真实项目事实 |

**写入前约束：** 本计划文件可以独立提交；任何运行时实现都必须在本计划冻结、前置 PR 状态明确、影响面查清后再启动。计划提交不等于实现授权。

## 1. 用户问题与重构目标

### 1.1 当前要解决的实际问题

用户希望 Skill 把精力用于理解赛题、建立合适的数学模型、求解、分析和论文交付，而不是先处理一长串与当前任务无关的分类、路由、状态登记或检查器流程。当前仓库有较多路由与运行时保证机制；其中部分机制有必要，但不能让可选资源、路由分类或中间产物状态变成正式建模的普遍前置条件。

本次目标不是“取消质量控制”，而是区分：

1. **数学与证据所必需的控制**：如果缺失会导致模型未获批准、约束不正确、数值结果未经真实验收或论文结论缺少依据，必须保留。
2. **仅用于选择工作路径的机制**：应帮助选择合适模块，不应因为缺少专属模板、竞赛 Pack 或完整分类而阻止通用分析。
3. **重复或时机错误的检查**：若同一事实已经由唯一 Authority 和当前证据负责，或当前任务尚未到该交付边界，不应重复登记、提前执行或阻断无关工作。
4. **仍未查清的机制**：先追踪真实消费者、阻断效果、输入与证据，不允许仅凭名称或复杂程度决定删除。

### 1.2 完成后必须达到的行为

- 有适用模板时，选择模板并遵循模板；没有适用模板时，依据题意和现有 Skill 专业规范直接开展分析与求解。
- 未知竞赛、缺失可选 Pack、没有显式分类或没有专属写作 profile，不得单独成为题目分析无法启动的理由。
- 路由只负责确定当前任务需要什么；不能将“分类已完成”“解析器已运行”“读取计划已返回”误当成模型正确或用户批准。
- 只在当前阶段确有必要时执行相应检查；正式交付门禁不能无故提前到模型讨论、框架建立或普通中间产物阶段。
- 同一事实只保留一个权威机器来源；面向人的框架可以显示摘要，但不能与项目状态、已验收工作簿争夺事实所有权。
- 真实数学风险、模型审批、数值质量、证据链和最终交付检查仍然严格。
- 对同一请求中同时出现的多个意图，取其**适用规则的并集**，不得由一个窄意图吞掉另一个意图。

## 2. 不得削弱的六个核心领域

本次重构完成后，不以路由测试通过作为整体完成。六个领域都必须重新核验。

| 核心领域 | 必须保留的能力 | 允许简化的部分 | 不可接受的结果 |
|---|---|---|---|
| 1. 题目分析 | 题意拆解、子问题与依赖关系、条件提取、数据需求、目标和输出定义、Problem Contract | 不强制先完成与当前问题无关的分类登记；缺少专属模板时使用通用分析 | 未识别关键条件便直接套模型；因没有模板或标签而无法开始 |
| 2. 模型分析与建立 | 变量、假设、目标函数、公式推导、约束条件、适用条件、模型复杂度复审、候选模型比较、独立 Model Reviewer 与 Devil’s Advocate、Model Approval Brief | 删除重复的状态确认、无关路由预检和相同内容的重复登记 | 取消用户对当前模型的明确批准；错误公式或遗漏约束仅因门禁减少而被放行 |
| 3. 模型求解精度 | 合适的求解器、容差、收敛性、数值稳定性、边界与可行性、Primary Quality Specification、真实结果的独立数值证据复核 | 不对尚未运行或不涉及数值求解的阶段执行数值交付检查 | 降低精度、缩减真实计算、把静态代码检查冒充数值验收 |
| 4. 模型求解规范 | 模块化代码、注释、代码与批准模型一致、后端选择、用户 full-fidelity 执行、返回工作簿核验、代码与结果身份绑定 | 不要求用户为每个日常动作额外运行 Skill checker、同步器或无关机器审计；不重复执行相同检查 | 助手代跑真实赛题代码；没有当前模型批准就交付任务代码；代码、工作簿和模型脱节 |
| 5. 求解结果深化分析 | 主结果 accepted 后的 Analysis Necessity Gate、必要时的敏感性/稳健性/边界/替代算法或多模型比较、证据与主张对应 | 不把所有分析强制套到每道题；`not_required` 有理由时不生成空产物 | 把未执行的稳健性写成已验证；因为删门禁而漏掉当前主张必需的深化分析 |
| 6. 论文写作 | 公式与结果一致、模型—算法—代码—结果证据闭环、图表读取与视觉审查、论文结构、引用与术语、LaTeX 正式审计与编译、PDF 实际页面检查、适用的终稿/提交包检查 | 不为普通修改提前执行提交包门；避免同一写作请求反复装载或重复运行无变化的审计 | 论文正文、图表或数值结论失去证据；用路由成功或机器 PASS 代替数学、语义和视觉审查 |

### 2.1 模型批准必须保留为真正的等待点

以下链条不得删除或降级为提示：

`proposed_model_spec` → 语义闭环与复杂度审查 → 两个独立 Model Challenge passes → Model Approval Brief → `awaiting_model_approval` → 用户明确批准当前 `semantic_revision` 与已验证的 `semantic_identity_hash` → `locked_model_spec`。

- “继续”“我看看”等模糊回复不构成批准。
- 有 blocking challenge item 时，不允许用用户批准绕过问题。
- 公式、目标函数、约束和变量定义必须经过实质性审核；不能把路由、Schema 或哈希一致性检查当作数学正确性证明。
- 语义修订或结构化身份变化必须按现有 Authority 使旧挑战、批准和锁模状态失效，并重新审查。
- 仅改变不改变数学语义的实现细节时，是否重新批准仍按现有模型批准合同裁决，不自行扩大或缩小范围。

## 3. 当前架构与现有工作的衔接

### 3.1 已核对的主要结构

| 文件或组件 | 当前职责 | 本次处理原则 |
|---|---|---|
| `core/bootstrap.yaml` | 最小启动入口、权威来源指针和硬性不变量 | 保持轻量，不把业务细则复制进 Bootstrap |
| `core/workflow_router.yaml` | 意图、模块顺序、任务分类约定、阶段边界、路由与门禁声明 | 核对哪些声明是唯一必要规则，哪些是重复清单或过度前置条件 |
| `core/runtime_assurance_contract.yaml` | 合同依赖闭包、Authority 指纹、读取计划和运行时保证协议 | 保留必要的来源身份与当前性检查；不让规划输出自动变成资格或 PASS |
| `core/module_manifest.yaml` | 模块输入输出、utility gate 与产物闭环 | 追踪真正消费者，避免与 Router/Output Contract 多处重复定义相同规则 |
| `scripts/resolve_runtime.py` | 当前默认的状态感知解析入口 | 重点审查是否把可选分类、可选资源或非当前阶段门禁变成阻断 |
| `scripts/resolve_workflow.py` | 旧的无状态兼容解析入口 | 保留明确的兼容边界；不为兼容接口继续叠加新的活动规则 |
| `scripts/runtime_assurance.py`、`scripts/reading_plan.py`、`scripts/read_stage.py` | 运行时保证、正文选段和阶段原文读取相关实现 | 复用既有职责，不另建第二套路由、读取计划或门禁顺序 |
| `core/project_state.schema.yaml`、`core/state_transition_contract.yaml` | 机器状态、身份、stale 与状态转换 | 只对真实重复事实做归并；不随意删除兼容字段或状态转换保护 |
| `core/output_contract.yaml` | 产物、交付范围、证据与交付资格 | 保留必要的最终交付约束；检查中间范围是否误继承最终交付门 |
| 模型批准、数值验证、用户执行、写作和图表 Authority | 专业质量和证据规则 | 作为本次回归的保护边界；不得由 Router 替代 |

### 3.2 与现有分阶段读取重构的关系

`docs/stage_reading_execution_refactor_plan.md` 已记录 P0—P3 完成、P4 实现及验收记录，并规定新阶段、新小问、新章和新图设计应重新取得适用正文。该计划解决的是**适用规则如何完整送达并在工作中落实**，不能被本次重构反向削弱。

本次不重建一套读取框架，也不把原文读取、来源哈希、阶段导航和读取完整性混为多份业务门禁。只针对路由与门禁简化后仍会出现的错误选择补齐行为测试。

### 3.3 与 PR #276 的关系

PR #276 已覆盖以下拟议范围的一部分：

1. 未知竞赛的专属 Pack/profile 变为可选适配资源，缺少时使用通用规则。
2. 新问题设计在缺少显式分类时可使用通用分类路径。
3. 非 LaTeX 路由不应提前解析写作 profile。
4. design/framework 等中间产物不应触发不适用的正式终稿/提交级同步门。

PR #276 已于 2026-10-23T18:01:38Z 合并，合并提交为 `75d772c84b75290f59f79b4d3e1eb2747e4eb3ec`；其源 head 为 `b049ca8cd9718d50a070ad0d9b33a2a3351cebed`。正式验收证据：完整 CI [#39991170816](https://github.com/Vexushi1/mathmodel-skill/actions/runs/39991170816) 通过，适用 Optimization baseline [#39991174320](https://github.com/Vexushi1/mathmodel-skill/actions/runs/39991174320) 通过；合并后 main CI [#39999918643](https://github.com/Vexushi1/mathmodel-skill/actions/runs/39999918643) 在本记录编写时仍在执行，生成元数据刷新 [#39999918645](https://github.com/Vexushi1/mathmodel-skill/actions/runs/39999918645) 已通过。

后续约束：

- PR #276 已进入 main；不要再次复制其未知竞赛通用回退、缺少分类时启动通用分析、非 LaTeX 路由延迟加载写作 profile，以及 design scope 不触发最终交付同步门等修复。
- 先完成合并后 main 的正式 CI 核验，再从该最新 main 创建独立的阶段 B 实现分支。
- PR #276 的局部修复不代表状态事实所有权、门禁生命周期和混合绘图意图问题已经全部解决。

### 3.4 既有全仓库审查问题的处理

`docs/repository_audit_and_handoff_refactor_plan.md` 记录了 AUD-01 至 AUD-18 共 18 项确认问题，以及额外观察和后续实施记录。该台账不得因新计划覆盖范围较窄而被删除、覆盖或悄悄改成“已解决”。

这些历史问题在本次重构中的处理方式是：

1. 以当前 main 中的实际实现、已有 PR/提交和相关测试重新确认状态。
2. 已修复的问题作为防回归基线，不重复实现、不把历史问题自动重新打开。
3. 若当前 main 上出现回归，记录具体反例、实际文件与证据，并按单主题 PR 修复。
4. 若问题仍未闭合，继续保留原台账状态；除非用户明确批准扩展本次范围，否则不把全部历史问题塞入同一重构 PR。
5. 原台账中四项观察以其第 8 节最终裁决为准，不把观察自动升级成已确认缺陷。

既有 AUD 项目的完整标题仍以原审计计划为准，避免在新计划中复制一份可能漂移的第二台账。

## 4. 目标运行流程

目标流程应当自然、短而可解释。它不是新的硬编码流程表，也不能取代现有业务 Authority。

1. **理解用户请求和题目材料。** 提取题意、目标、条件、子问题、数据与交付要求。仅当缺失信息会实质改变建模或执行时才询问澄清。
2. **选择适用模板。** 有匹配模板或竞赛规范时使用；没有时回退到通用 Skill 规则。模板是专业辅助，不是数学建模资格证。
3. **建立题目分析与候选模型。** 根据真实题意选择最小充分模型，完成变量、假设、公式、约束、算法候选及适用性说明。
4. **完成模型实质审查并等待批准。** 按现有双重 Model Challenge、公式与约束审核及 Human Model Approval 规则执行，不允许通用路由门禁替代。
5. **进入适用的数值工作。** 确认后端和真实执行边界，生成模块化代码；用户执行 full-fidelity 求解并返回产物，助手验收实际证据。
6. **根据真实主结果裁决是否需要深化分析。** 只在 Analysis Necessity Gate 判定 required 时生成独立深化分析；不得将未执行的分析描述成已验证。
7. **按当前请求处理图表和论文。** 对每项混合意图取适用规则并集；已批准图的单纯样式修改不重新审批模型，但新增图设计必须读取完整的设计规则与所需来源。
8. **在真正的交付边界执行适用门禁。** 按当前范围与 Authority 决定检查项；不把中间结果自动升级为正式交付，也不漏掉终稿/提交实际需要的检查。
9. **只更新发生变化的权威事实。** 同步现有项目框架、机器状态和产物记录；不为每次对话重复登记未改变的状态。
10. **报告真实完成度。** 清楚区分已分析、待用户批准、代码已交付、等待真实运行、结果已验收、图表/论文已审查和正式交付完成，不把解析器返回、文件存在或局部 PASS 泛化为全流程通过。

## 5. 具体实施工作包

### P0：基线冻结与权威/消费者盘点

**目标：** 先建立可复核的事实表，不先写实现。

步骤：

1. 再次读取实施时的 `main` 版 `core/bootstrap.yaml` 与 `SKILL_CHANGE_GOVERNANCE.md`。
2. 确认 Skill 版本、main HEAD、最新 Release、所有开放 PR/分支以及与本计划重叠的文件。
3. 读取 PR #276 的最终状态、文件列表、实际 head、CI 运行及其合并结果。
4. 逐项列出当前路由选择逻辑、分类必填条件、可选 Pack/profile 解析点、门禁产生者、门禁消费者和正式阻断点。
5. 对每个状态字段标明唯一事实源、写入者、读取者、失效条件和是否只是展示投影。
6. 对每个门禁标明：权威来源、触发条件、应执行的阶段、阻断对象、依赖输入、成功证据、输入变化时的失效方式、兼容路径。
7. 对照历史 AUD-01—AUD-18 台账和相关测试，区分当前已修复、未闭合、未复验与不在本次范围的项目。

**交付：** 作为实施 PR 描述与本计划的执行记录，给出文件—职责—消费者表、门禁适用性表、状态事实所有权表。不得新增运行时 Schema 来存储这三张维护表。

**停止条件：** 若发现与目标相同文件的开放 PR 尚未确定顺序，停止触碰重叠实现；若无法确认当前权威来源，先补齐读取，不以旧聊天内容推断。

### P1：路由简化与模板可选回退

**目标：** 让路由帮助工作，而不是让分类或模板成为启动门槛。

实施步骤：

1. 追踪 `core/workflow_router.yaml` 中路由声明、`classification_contract`、`execution_contract`、`runtime_segments` 与每个路由的加载和 gate 声明。
2. 追踪 `resolve_runtime.py`、`resolve_workflow.py` 与 `runtime_assurance.py` 的真实调用链，区分默认入口、旧兼容入口、内部辅助函数和实际阻断点。
3. 明确“意图识别/资源选择”与“数学工作能否继续”的边界。分类缺失时，若可由题目本身理解并使用通用流程，不应提前失败；仅当任务本身缺少不可替代的关键条件时，才澄清或等待。
4. 明确专属模板、竞赛 Pack、写作 profile 的可选性。缺少资源时回退到通用 Authority；不能假造模板内容，也不能因此跳过专业分析。
5. 保留显式 API/CLI intent 的既有优先级和多意图语义；不要让自然语言关键词评分覆盖用户明确指定的载体或任务。
6. 对非写作路由延迟写作 profile 解析；只有当前任务确实进入对应写作载体时才加载相应 profile。
7. 对混合请求采用意图并集与依赖去重：多个意图可以共享模块，但不能丢掉其中任何一个意图所必需的规则。
8. 检查 resolver 的兼容输出：模块、pause、terminal outputs、delivery scope、assurance、`pre_delivery_gates` 以及旧 CLI 的既有含义。
9. 删除或重构任何前置解析步骤之前，必须证明它没有唯一的安全、兼容或业务职责；不能只因它多一次函数调用就删除。

**本阶段不做：** 不改数学模型、求解算法、Model Approval 合同、数值验证阈值、图表标准或论文正文标准。

### P2：门禁分类、时机与重复执行治理

**目标：** 只在正确的业务边界执行必要门禁，删除无独立价值的重复阻断。

实施步骤：

1. 从当前 main 与 PR #276 的实际最终状态出发，枚举路由、模块清单、输出合同和运行时保证中所有门禁声明与消费点。
2. 为每项门禁建立审查行，至少包括：门禁名称、唯一 Authority、触发条件、适用交付范围、前置证据、阻断对象、实际消费者、现有测试与拟采取的动作。
3. 将门禁分成以下几类，但不另建运行时分类 Schema：
   - **必须保留的模型语义/批准门：** 模型语义闭环、复杂度与必要公式/约束审查、双重 Model Challenge、当前 Human Model Approval。
   - **必须保留的执行/数值门：** 当前代码交付条件、用户真实执行边界、主工作簿验收、适用的独立数值证据复核、必要的分析工作簿验收。
   - **条件触发的质量门：** 项目级预处理、结果深化分析、特定图表证据、LaTeX 编译、DOCX/LaTeX 对应交付和提交包验证，只在其 Authority 所规定的事实与范围满足时执行。
   - **可能冗余或时机错误的门：** 同一操作链内重复调用同一检查、design/framework 等中间范围错误继承最终提交门、仅因缺少可选分类/模板而阻断、已有权威检查后又由另一处重复定义相同阻断。
4. 每一项拟删除/合并/降级的门禁必须给出具体证据：当前由谁执行、重复发生在哪里、是否有独立输入/副作用、删掉后哪个真正的检查仍负责该风险。
5. 确定门禁顺序与适用范围的唯一维护位置。保留 resolver 根据当前范围产生的实际序列；不得再在 README、Router、Module Manifest、Output Contract 和脚本里各维护一份可独立漂移的固定 gate 清单。
6. 若某项门禁只是重复声明，不得简单从某一文件删除后留下其他文件继续执行；必须追踪从声明到消费者的完整链路。
7. 同一用户请求中若同一门禁因多个意图重复进入计划，去重的是**同一次动作中重复的调用**，不是不同输入或不同阶段本来就需要的独立验收。
8. 不保存可跨状态变更复用的 gate PASS 缓存。只有现有 Authority 明确允许且证据身份、作用范围和输入均保持当前时，才可以复用已接受产物或已有证据；状态或相关输入变化后必须按原契约重新验证。
9. 保留最终 LaTeX 正式 render 内部的 audit→compile 流程，避免把正常集成流程拆成日常重复手工 audit；但不因此省略正式审计本身。
10. 保留正式 PDF 的实际页面检查、视觉检查、必要语义检查和提交包内容验证；机器门通过不等于这些人工/证据职责已完成。

**必须形成的结果：** 一张审计过的门禁适用性表，明确每项门禁是保留、条件化、合并、移到正确阶段、降为诊断提示或删除，并附证据和测试。不得先列出“要删哪些门禁”再反向寻找理由。

### P3：重复状态登记与事实所有权归并

**目标：** 减少重复写入与重复登记，不削弱当前状态、证据身份和失效传播。

实施步骤：

1. 盘点 `state/project_state.yaml`、`模型论文框架.md`、运行回执、同步报告、工作簿与产物 Manifest 中重复表达的字段。
2. 对每类事实确定唯一权威来源，至少区分：
   - 当前模型语义与可供助手恢复的项目工作记忆；
   - 机器状态、semantic revision、structured identity、审批身份与 stale；
   - 数值事实与接受状态；
   - 源码、运行与证据文件身份；
   - 人工审查意见和当前审查范围。
3. 以当前契约为准：框架不是机器状态的替代品；项目状态不是数值真值来源；工作簿不能代替人工模型批准；来源 hash 不能证明数学正确。
4. 若框架需要显示状态，只将其作为可读摘要或同步投影，不让它成为第二个独立的机器审批事实来源。
5. 删除重复登记前，检查所有消费者、旧项目兼容、生成器、同步器、事务读集和 stale 传播。只要一个字段仍被有效消费者依赖，就不能直接删除。
6. 只在事实确实变化时更新其唯一所有者；框架同步和状态变更按既有事务/转换合同执行，避免一次动作由多处分别写入互相竞争的值。
7. 不为“减少状态”而取消语义修订历史、批准身份、输入哈希、运行证据、审查回执或必要 stale 信息。
8. 若必须更改 Schema，先评估兼容窗口、旧项目只读路径、状态迁移、恢复与回滚；Schema 破坏性变更不得伪装成 docs/patch。
9. 不在新项目状态里加入仅供本计划审计的额外字段；门禁清单、实施进度和审查说明应留在维护文档/PR 记录。

**退出条件：** 状态事实所有权清楚；不存在两份互相竞争的当前资格；旧项目可按明确兼容规则读取；输入改变不会因为“去重”而漏掉 stale 或批准失效。

### P4：混合意图的绘图规则读取修复

**目标：** 防止同一请求中一个样式意图覆盖新图设计所需的规则与原始材料。

**当前已确认的问题：** 同一请求既说“只修改现有图的配色”，又要求“补充一张新图”时，读取规划可能把整条请求归入样式修改路径，因而漏掉新图设计所需的原文和资源。现有证据支持这是**意图/读取规划错误**，不表示新图因此自动获批，也不表示已有图需要重新获得模型批准。

实施步骤：

1. 对照 `docs/stage_reading_execution_refactor_plan.md`、`core/runtime_assurance_contract.yaml#reading_plan.consumer_protocol`、`modules/04_figure_evidence.md` 和相关读取测试，定位当前意图选择、条件资源选择与正文读取范围。
2. 将“现有图样式修改”和“新增图设计”作为可同时成立的两个意图；计算当前请求所需的适用规则并集，而不是让一个标签排斥另一个。
3. 对现有图样式修改读取其真实当前绑定、已批准图身份、配色/可读性要求和相关视觉规范；只有在证据仍有效时才复用已有资格。
4. 对新增图读取完整 Figure Authority、图的论证功能与选型规则、当前问题所需原文/数据来源、图表与论文交接要求以及实际触发的条件资源。
5. 只补充本次新增图确实需要的来源，不因此无差别预加载整个仓库，也不把“读取更完整”作为额外审批或批准条件。
6. 不允许因为现有图已批准而自动批准新图；新图仍按原有设计、真实执行/导出、视觉审查与证据交接流程处理。
7. 同样核验其他混合请求：已有图调整 + 新图设计、现有论文局部改写 + 新增证明、结果解释 + 新增比较、明确写作载体 + 其他独立意图。只修复已确认的选择/并集缺陷，不借机重写全部读取系统。
8. 继续遵循既有“新阶段/新图设计需要重新取得适用正文”的规则；不新增“已读 PASS”状态或读取回执门禁。

**必要回归：**

| 请求场景 | 期望 |
|---|---|
| 只改变一张当前已确认图的配色 | 使用样式修改规则；不无故触发模型重新批准或全流程重算 |
| 只新增一张图 | 取得完整新图设计规则与相关来源；不能走 style-only 窄读 |
| 同一请求既调整旧图配色又新增图 | 两组适用规则均进入读取计划；新增图所需原文不能遗漏 |
| 新图依赖的关键原文/数据缺失 | 明确指出缺口并停止相应主张，不伪造来源 |
| 读取来源完整，但图尚未生成/导出/视觉审查 | 不标记为已批准或交付通过 |
| 现有图批准记录有效、新图未审查 | 旧图状态保持；新图仍待其自身的实际审查 |

### P5：六领域完整回归与历史缺陷防回归

**目标：** 证明简化没有把专业能力或已修复缺陷一起删掉。

步骤：

1. 使用第 2 节的六领域矩阵，逐项复查真实 Authority、当前实现、关键消费者和对应测试。
2. 对每个领域分别记录“行为未变的证据”“发现的回归”“尚未覆盖的边界”，不只报告 CI 总体绿灯。
3. 对模型批准、公式/约束、数值证据、代码执行、条件式深化分析、绘图视觉检查和论文最终交付执行跨模块集成回归。
4. 复跑或确认现有 AUD-01—AUD-18 的相关测试仍能覆盖原先缺陷；如果当前实现没有相应回归证据，记录为待核验，不假称已通过。
5. 将 P4 的混合绘图意图案例加入专项测试，并验证实际读取范围，而不只是断言某个字符串或路由名称。
6. 检查普通请求不会被无关的 A1/A2、B1/B2、C1/C2、D1/D2 或其他显式可选能力强制扩大流程；这些协议仍按各自 Authority 和既有显式激活条件工作。
7. 对每个被移除或合并的检查运行反例测试，证明真正的风险仍会被剩余的正确检查捕获。
8. 不因为一个单元测试通过就宣布某个数学模型、数值结果、图表视觉或论文语义已正确；各层仍需对应真实证据。

## 6. 实施文件范围与触碰纪律

以下是**检查范围，不是全部必须修改的文件清单**。只有前述事实盘点证明需要时才修改。

| 类别 | 优先检查的文件 | 允许的修改 |
|---|---|---|
| 启动/全局入口 | `core/bootstrap.yaml`、`SKILL.md`、`PROJECT_INSTRUCTIONS.md`、`RUNTIME_ROUTER.md`、`README.md` | 入口保持简洁、指向唯一 Authority；不得在入口文档复制详细门禁规则 |
| 路由与分类 | `core/workflow_router.yaml`、`core/task_taxonomy.yaml` | 只改已确认的启动阻断、资源回退、多意图合并或重复路由声明 |
| 运行时保证 | `core/runtime_assurance_contract.yaml`、`scripts/runtime_assurance.py`、`scripts/resolve_runtime.py`、`scripts/resolve_workflow.py`、`scripts/reading_plan.py` | 修复实际的路由/门禁/读取行为；保持输出契约和旧兼容路径，除非另有迁移批准 |
| 模块与产物 | `core/module_manifest.yaml`、`core/output_contract.yaml` | 清除重复或范围错误的声明；不降低真实交付所需产物与验证 |
| 项目状态 | `core/project_state.schema.yaml`、`core/state_transition_contract.yaml`、`scripts/validate_project_state.py`、`scripts/sync_project.py` 及实际消费者 | 仅在事实所有权分析证明重复时归并；保持 stale、身份和事务保护 |
| 模型批准/数值保护 | `core/model_approval_contract.yaml`、`core/numerical_verification_contract.yaml`、相关验证脚本 | 原则上不改业务语义；只修复因路由/门禁编排导致的调用时机问题，并以独立测试证明行为保全 |
| 绘图/论文读取 | `modules/04_figure_evidence.md`、`core/runtime_assurance_contract.yaml`、`scripts/reading_plan.py`、`tests/test_stage_reading_guide_lifecycle.py` 等现有测试 | 只修复混合意图读取与相关回归；不新建第二套 Figure Authority 或批准机制 |
| 测试 | `tests/test_router_contract.py`、`tests/test_v10_project_runtime_policy.py`、`tests/test_v712_runtime_assurance.py`、`tests/test_v632_delivery_gate_closure.py`、`tests/test_v633_gate_hardening.py`、`tests/test_stage_reading_lifecycle.py`、`tests/test_stage_reading_guide_lifecycle.py` 及经盘点确认的关联测试 | 优先扩展有实际行为覆盖价值的现有测试；必要时新增少量专项测试 |
| 版本/生成文件 | `CHANGELOG.md`、版本载体；生成的索引与 `MANIFEST.sha256` | 源文件按治理规范维护；索引和 Manifest 仅由 GitHub 生成流程更新 |

### 6.1 明确禁止的实现方式

- 不直接写 `main`。
- 不在多个 Authority 中同步复制同一套规则。
- 不为本次重构另建一个固定 gate list、第二个项目状态、第二个路由器或第二套读取计划。
- 不通过删除测试、减少覆盖、跳过旧兼容场景或伪造 fixture 来取得绿灯。
- 不把每项专业审查都变成新的前置表单、必填字段或用户签字步骤。
- 不以“无模板”为由编造模板；不以“有模板”为由机械套用与题意不符的模型。
- 不把读取计划生成、resolver 成功、来源 hash 一致、状态字段齐全或代码静态检查通过当成模型批准或数值正确。
- 不让新图因与旧图在同一请求中出现而继承旧图批准。
- 不手工编辑 `SKILL_FILE_INDEX.md`、`TEMPLATE_INDEX.md`、`HSK_SKILL_FILE_INDEX_V622.md`、`HSK_TEMPLATE_INDEX_V622.md`、`MANIFEST.sha256` 或其他由生成器管理的文件。
- 不执行真实赛题的 Python/MATLAB 求解来替代用户的 full-fidelity 执行；仓库 CI 的测试也不等于用户项目数值验收。
- 不在计划文件里预先承诺某个版本号、CI 结果或发布状态。

## 7. 专项验收矩阵

下列用例是计划要求的行为覆盖。实现时应尽量合并相邻案例，避免为每种措辞建立冗余测试，但不得遗漏独立失败模式。

| ID | 场景 | 通过标准 |
|---|---|---|
| R01 | 已登记竞赛且存在适用模板 | 选择正确模板，保持既有模板行为 |
| R02 | 未登记竞赛、无专属 Pack/profile | 通用流程可继续；不得因可选资源缺失抛异常 |
| R03 | 新赛题尚无显式 objective/structure 分类 | 仍可理解题意、分析问题并形成候选结构；不伪造已完成分类 |
| R04 | 显式 CLI/API intent | 保持既有明确选择的优先级 |
| R05 | 同一请求含多个意图 | 适用模块/规则取并集，公共依赖去重但不丢独立任务 |
| R06 | 非写作任务中包含可能被误识别的写作词 | 不提前加载不适用的写作 profile 或交付链 |
| G01 | 仅建立 Problem Contract/候选模型 | 不触发不适用的正式终稿或提交包门；仍执行本阶段真正必要的语义/模型工作 |
| G02 | 模型已提出但未完成双重挑战 | 不进入人工批准等待点或任务代码交付 |
| G03 | 模型挑战存在 blocking finding | 阻断锁模/代码，不可被用户批准绕过 |
| G04 | 用户仅说“继续”或“我看看” | 不误判为明确模型批准 |
| G05 | 当前 semantic revision/identity 变化 | 旧挑战、批准和锁模资格失效，按原合同重审 |
| G06 | 公式或约束审查发现数学问题 | 问题被指出并修复/解释；不能因门禁简化而通过 |
| G07 | 生成主求解代码 | 仍要求当前模型批准和适用代码交付条件 |
| G08 | 主代码已经交付但用户尚未运行 | 保持等待真实执行，不声称数值求解已完成 |
| G09 | 用户返回工作簿 | 仍按当前工作簿、运行身份、质量规范和适用数值证据验收 |
| G10 | 主结果 accepted，分析 Gate=not_required | 有理由、不造空分析产物、不声称稳健性已验证 |
| G11 | 主结果 accepted，分析 Gate=required | 独立分析入口、真实运行和分析工作簿验收仍完整 |
| G12 | 普通图表/写作只消费主结果证据 | 不因默认路径强制要求与当前主张无关的 03B 工作簿 |
| G13 | 单纯修改现有已确认图的配色 | 读取当前样式与证据要求，不无故触发模型重批或重算 |
| G14 | 单独新增一张图 | 读取完整新图设计规则和必要来源，不走 style-only 窄读 |
| G15 | 同一请求修改旧图配色并新增新图 | 两类读取要求均满足；不得漏掉新图设计原文；新图不自动获批 |
| G16 | 图已规划但尚未真实生成/导出/视觉审查 | 不把规划、登记或机器结构检查当作正式图通过 |
| G17 | 同一操作链的多个意图包含同一检查 | 当前操作内避免重复调用；独立阶段/不同输入仍各自验收 |
| G18 | 相关输入或语义身份改变 | 不复用旧 PASS 或过期证据，按原契约重验 |
| S01 | 框架显示模型批准摘要而 State 记录机器身份 | State 仍是机器事实源；框架不能独立授予批准 |
| S02 | 工作簿数值与框架摘要冲突 | 数值事实以当前 accepted 工作簿及原验收链为准，冲突明确处理 |
| S03 | 多个旧字段存在历史兼容值 | 不静默删字段或倒填当前批准；按兼容合同读取 |
| S04 | 状态更新跨多个文件 | 按原事务与 stale 传播合同处理，不出现部分写入冒充完成 |
| W01 | 默认论文草稿、没有专属写作模板 | 走通用写作 Authority 与适用默认载体，不因缺模板而失败 |
| W02 | 明确要求 Word/DOCX 或 LaTeX | 保持显式载体选择和对应交付规则 |
| W03 | LaTeX 正式 render | 仍完成正式 audit→compile 及当前源/报告/PDF 绑定，不重复强制用户独立运行相同审计 |
| W04 | 正式 PDF 生成后 | 仍进行助手实际页面检查和适用的终审，不以编译成功替代 |
| W05 | 用户要求提交包/复现包 | 当前 scope 下的 package/manifest/hash/竞赛规则检查仍执行 |
| C01 | 旧 CLI、旧项目和兼容命名 | 不因内部简化而无说明破坏旧调用；如确需破坏则先提供迁移方案 |
| C02 | AUD-01—AUD-18 的既有回归 | 原有修复不回退；任何未复验项目如实标记 |
| C03 | 任意失败/缺源/未执行/未知条件 | 状态明确为未完成或 review_required，不将未知转换成 PASS |

## 8. 六领域重新审查清单

本次实现完成后，以下内容必须全部重审。此处不是建立第二套日常门禁，而是本次重构的发布验收清单。

### 8.1 题目分析

- 对没有专属模板/竞赛 Pack 的赛题，能否直接形成问题分解、关键条件和数据需求。
- 显式分类缺失是否只在确实需要时才阻断。
- 是否保持多小问依赖、任务边界和 Problem Contract 的语义完整。
- 是否因默认回退而遗漏题目中的特殊要求。

### 8.2 模型分析与建立

- 候选模型是否由题意和数据决定，而不是由模板强制决定。
- 公式、变量、目标函数、约束与假设是否完整且一致。
- 两个独立 Model Challenge passes 是否真实执行。
- 人工批准是否绑定当前语义修订和结构化身份。
- 修改路由、门禁或状态后，是否仍正确处理 blocking finding 和 stale。

### 8.3 求解精度

- 求解器、容差、收敛条件和边界处理是否没有被改变。
- 是否保留 Primary Quality Specification 与独立数值证据复核。
- 用户真实执行的精度、数据规模和运行条件是否没有被替代或缩减。
- 代码通过、工作簿通过和数学结果有效是否仍清晰区分。

### 8.4 求解规范

- Python/MATLAB 后端选择与迁移规则是否保持。
- 代码是否与锁定模型和公式一致。
- 是否仍遵循模块化、注释、错误处理和输出契约。
- 用户执行与助手验收分工是否清晰，是否仍避免要求用户重复运行仓库 checker。
- 产物、运行配置、工作簿、源码和回执之间的身份与 stale 链是否完整。

### 8.5 结果深化分析

- Analysis Necessity Gate 是否只在主结果 accepted 后执行。
- `required` 与 `not_required` 是否都保持正确行为。
- 需要的敏感性、稳健性、阈值、替代方法、多模型或同模型多算法检验是否仍有真实可比证据。
- 未做的分析是否没有被状态、模板或论文文字伪装为已完成。

### 8.6 论文写作

- 论文是否仍使用当前有效的模型、公式、结果和验证证据。
- 模板存在时是否正确使用；模板缺失时是否能遵循通用写作规范。
- 新图、样式修改、图文衔接和视觉审查是否正确区分。
- 正文证明、算法、引用、术语、数值主张和章节交接是否完整。
- 正式 LaTeX 审计、编译、PDF 逐页检查和适用提交包验收是否仍保留。
- 任何“检查减少”是否只是减少重复调用，而不是降低实际审查覆盖。

**整体通过条件：** 六项均有对应的当前源码/Authority、专项回归与集成证据；只要其中一项未覆盖，不能以路由 CI 通过宣布本次重构完成。

## 9. 分批实施与 PR 顺序

为遵守“一次 PR 一个核心主题”和避免与现有未合并工作相互覆盖，建议按以下顺序推进。最终 PR 数量可以依据实际 diff 调整，但不得把不相关修复塞入同一 PR。

### 阶段 A：完成前置 PR #276

- [x] PR #276 最终源 head 与 PR diff 已复核；完整 CI 与适用 Optimization baseline 均通过。
- [x] 自动生成元数据刷新成功，合并后 main 为 `75d772c84b75290f59f79b4d3e1eb2747e4eb3ec`，Skill 版本为 v10.23.1。
- [x] PR #276 已合并；最新 Release 仍为 v10.23.0，未创建新 Release。
- [x] 合并后 main 的完整 CI `39999918643` 已完成并通过（完整 Python 3.10/3.14 汇总、MATLAB 原生契约、LaTeX 专项、静态与生成检查均成功）。
- [ ] 更新并合并本计划 PR #277；随后从经核验的最新 main 创建阶段 B 实现分支。

PR #276 合并后，阶段 A 的代码验收和合并动作已完成；在 main CI 与计划分支同步完成前，不把整个前置阶段标记为完全关闭。

### 阶段 B：路由与门禁生命周期重构

围绕一个核心主题：**当前任务如何选择必要工作、何时执行必要门禁**。

- 根据 P0 盘点结果调整 Router/resolver/runtime assurance 的最小必要部分。
- 对照门禁适用性表落实范围和时机。
- 不同时引入 Schema 迁移；如果发现状态字段问题，先以事实表确认其是否可在同一主题内安全处理。
- 以 G01—G18、R01—R06 和原路由回归测试为专项验收依据。

### 阶段 C：状态事实所有权归并（仅在盘点确认有必要时启动）

- 若只是展示摘要重复，优先修正说明和写入边界，不进行破坏性 Schema 修改。
- 若确有多处写入同一机器事实，则建立独立、单主题 PR，处理字段所有权、消费者、兼容和迁移。
- 在没有证明实际重复前，不预先承诺删除任何状态字段。
- 用 S01—S04、状态事务和 stale 回归验证。

### 阶段 D：混合绘图意图读取修复

- 若修复能与路由/读取选择在同一局部实现中保持单一主题，可与相应阶段集成；否则单独 PR。
- 覆盖 P4 的五类以上场景，至少有一项能证明新图设计原文确实进入可用读取范围。
- 不改变图表审批、导出、视觉审查或模型批准语义。
- 保留 `docs/stage_reading_execution_refactor_plan.md` 的既有完成记录，只在有必要时链接当前补充实施记录。

### 阶段 E：集成审查与版本收口

- 审查各 PR 之间的接口、兼容性和实际最终 main。
- 重新执行第 8 节六领域审查和第 7 节回归矩阵。
- 版本按实际兼容性定级；若未改变公共接口或 Schema，不因为“整体重构”自动升级 major。
- 在最终 PR 描述中明确记录删/并/移/保留的门禁清单，逐项引用证据；不能只写“简化流程”。
- 只有最终 head 的正式验收和 main 复核通过后，才进入发布步骤。

## 10. GitHub-only 验收流程

仓库维护遵循当前 `SKILL_CHANGE_GOVERNANCE.md`，本计划不另造 CI 标准。

1. **分支与 PR：** 每一实施主题使用独立分支；禁止直接写 main。
2. **开发阶段：** 推送源文件，由 GitHub Actions 执行适用专项与基础检查。Draft/开发分支结果仅用于发现问题，不宣称正式验收。
3. **生成元数据：** `refresh-generated` 在远端生成索引、MANIFEST 及其他受管产物。不得手工编辑；核对 bot 提交是否只包含预期生成差异。
4. **最终 head：** 记录 PR source head、实际 checkout commit、自动生成后 final head，三者不能混为一谈。
5. **专项覆盖：** 确认路由、运行时保证、状态转换、读取计划、图表混合意图和六领域关联测试均进入相应测试路径。
6. **正式完整验收：** PR ready 后按当前治理执行 Windows Python 3.10 和 3.14 的完整四分片与汇总、lint、生成文件检查、Windows MATLAB、Linux LaTeX，以及适用的 Optimization baseline。
7. **避免无意义重复：** 同一最终 head 已有可验证、等价且完整的正式运行时，按治理核对后可避免重复调度；只要源文件、生成物或 head 变化，必须对新的最终 head 重新验收。
8. **结果审计：** 核对失败、跳过、缺失或未完成的 job；不得把 targeted 成功、skipped 或旧 SHA 的绿灯当作完整通过。
9. **合并后：** 复核 main 上的 Actions、最终 commit 和生成文件。
10. **发布：** 只有达到正式发布条件后才创建/更新 Release；PR 合并、Skill 版本字段更新和 Release 发布是三个不同事实。

本仓库维护的 GitHub-only 流程不改变用户真实赛题代码的 full-fidelity 执行要求。用户项目的数值验收和仓库自身的 CI 必须分别记录。

## 11. 风险与回滚

| 风险 | 防护措施 | 回滚条件 |
|---|---|---|
| 删除的门禁其实承担独立质量责任 | 先做消费者/输入/失败模式追踪；为删除项添加反例测试 | 无法证明剩余检查覆盖相同风险时，不删除；若已合并则 revert 对应 PR |
| 通用回退导致漏掉特殊竞赛规则 | 专属模板优先，缺失时使用通用规则并明确未提供的专属约束；测试已登记和未知竞赛 | 发现合法专属规则被遗漏且不能安全回退时，恢复该路由或修正选择逻辑 |
| 过度归并状态破坏旧项目 | 明确事实所有者、兼容字段与迁移策略；不覆盖历史批准 | 旧项目恢复/只读兼容失败时回滚 Schema/状态改动 |
| 同一请求多意图只保留一个 | 多意图并集测试，尤其绘图“改色+新增图” | 任一意图的必需规则被吞掉时，不发布该实现 |
| 为减少重复调用而复用过期 PASS | 不保存可跨输入变化复用的 gate PASS；以当前身份和原契约决定重验 | 出现输入变化后仍放行，立即回滚并修复失效检测 |
| 路由简化改变六领域能力 | 六领域完整回归，不仅运行 router 单测 | 任一专业领域的保护条件回归则不得合并 |
| 多 PR 相互覆盖 | 前置 PR 先合并，后续分支基于最新 main，严格单主题 | 发现重叠未解决则停止写入并重建分支 |
| 计划与实际实施漂移 | 每个阶段更新实施记录、PR 与证据链接；未执行项明确标注 | 计划未更新前不得宣称与计划完全一致 |

## 12. 完成判据

只有以下条件全部成立，才可以称为“路由与门禁简化重构完成”：

- [ ] 模板有则使用，没有则能按通用 Skill 规范开展题目分析与求解。
- [ ] 缺少专属模板、Pack 或显式分类不再无故阻断普通建模任务。
- [ ] 复杂路由没有继续作为数学正确性、模型批准或数值有效性的替代证明。
- [ ] 所有被删除、合并、条件化或移动的门禁都有明确理由、唯一 Authority 和相应回归证据。
- [ ] 正式交付门禁只在适用的真实交付边界执行，且没有遗漏终稿/提交实际需要的门。
- [ ] Human Model Approval、模型双审、公式与约束审查、真实数值执行和结果验收完整保留。
- [ ] 重复状态登记已通过事实所有权表处理；没有破坏兼容、身份绑定、事务或 stale 传播。
- [ ] 绘图混合意图缺陷已修复；新增图设计所需原文读取完整，且不自动获得批准。
- [ ] 历史 AUD-01—AUD-18 的既有修复未回退；尚未闭合事项没有被移出原台账。
- [ ] 六个核心领域均已完成重构后的重新审查。
- [ ] 最终 head 的 GitHub 正式验收、生成元数据、适用 Optimization baseline 和 main 复核完成。
- [ ] 报告准确列出 PR、最终 head、合并 SHA、版本/Release 状态、已完成与未完成事项。

任何一项缺失，都只能报告为“部分完成”或“等待验收”，不能宣称整个重构完成。

## 13. 当前停止点与后续授权边界

当前只完成计划编写和计划文件的仓库提交流程。此计划不表示已修改 Router、resolver、门禁、状态 Schema 或任何运行时行为。

进入实现前，需要以当时最新的 main 和 PR 状态重新确认基线。若用户尚未授权开始代码实现，则停留在计划交付；不得因计划写得完整就自动扩大为实现、合并或发布。



---

## 11. 执行记录（2026-10-24）

### 11.1 基线冻结与开放工作

| 项目 | 核验结果 |
|---|---|
| 当前 main | `75d772c84b75290f59f79b4d3e1eb2747e4eb3ec` |
| 当前 Skill 版本 | `10.23.1`（`core/bootstrap.yaml`、Router、Manifest、Output Contract 版本字段一致） |
| 最新 Release | `v10.23.0`，仍指向 `2c79599b80763a8840a4b0ee79f85271f9234c6a`；v10.23.1 尚未发布 |
| 前置 PR #276 | 源 head `b049ca8cd9718d50a070ad0d9b33a2a3351cebed`；合并 SHA `75d772c84b75290f59f79b4d3e1eb2747e4eb3ec` |
| PR #276 源 head 验收 | [HSK Skill CI #39991170816](https://github.com/Vexushi1/mathmodel-skill/actions/runs/39991170816) 与 [Optimization baseline #39991174320](https://github.com/Vexushi1/mathmodel-skill/actions/runs/39991174320) 均通过 |
| 合并后验证（记录时） | [main CI #39999918643](https://github.com/Vexushi1/mathmodel-skill/actions/runs/39999918643) 当时仍在执行；[生成元数据刷新 #39999918645](https://github.com/Vexushi1/mathmodel-skill/actions/runs/39999918645) 已通过 |
| 开放 PR | 仅 PR #277（本计划文档），Draft，基于旧 main；其源文件为本计划，另含生成的 `MANIFEST.sha256` 与 `SKILL_FILE_INDEX.md` |
| 相关旧分支 | `fix/v10.20.5-stage-reading-consumption` 与 `refactor/v900-state-transition-engine` 有历史 diff，但均无开放 PR、相对 main 已明显落后；不自动合并、不作为新实现基线 |
| 重叠顺序 | 先同步并完成计划 PR #277，再创建阶段 B 代码分支；所有生成文件由 `refresh-generated` 维护，不手工编辑 |

### 11.2 文件—职责—消费者表

| 文件 / Authority | 唯一职责 | 主要消费者 / 边界 |
|---|---|---|
| `core/bootstrap.yaml` | 启动顺序、全局硬约束、权威入口索引；要求正式交付执行 resolver 返回的全部 gates | `AGENTS.md`、启动/入口说明与默认运行流程；不自行维护另一份 gate 顺序 |
| `core/workflow_router.yaml` | 唯一路由 Authority：intent、模块顺序、边界角色、runtime segments、delivery scope、route gate 声明与读取策略 | `scripts/resolve_runtime.py`、兼容解析器 `scripts/resolve_workflow.py`、`scripts/reading_plan.py` |
| `scripts/resolve_runtime.py` | 当前状态感知入口：显式/推断意图解析、项目上下文 hydration、artifact/backend 解析、契约闭包、assurance 与 reading-plan 组合 | CLI/Agent 默认运行；返回有效模块、暂停状态、outputs 和 gate 序列 |
| `scripts/resolve_workflow.py` | 旧无状态兼容入口：route inference、模块依赖/顺序、Model Approval / preprocessing / user-execution boundary、gate-plan 生成 | 兼容 CLI 和旧调用；行为变更需单独证明兼容性，不把它误当成当前状态事实 Authority |
| `scripts/runtime_assurance.py` + `core/runtime_assurance_contract.yaml` | intent 诊断、项目状态快照/读取一致性、artifact 资格、contract dependency closure 与 Authority fingerprint；不另造 gate 顺序 | `resolve_runtime.py` 与 `reading_plan.py`；reading plan 必须保留 effective plan 的所有 gates |
| `core/module_manifest.yaml` | 模块输入/输出、依赖与 utility gate 的可执行命令、inputs/outputs | `resolve_workflow.py` 与实际 gate 消费者；它是 gate catalog，不是路由顺序的第二 Authority |
| `core/output_contract.yaml` | 输出资格和 scope-specific `project_sync` 语义/实现指针 | `scripts/sync_project.py`、gate dependency closure；不维护独立的全局 gate 清单 |
| `core/project_state.schema.yaml` + `core/state_transition_contract.yaml` | 机器状态字段、revision/identity、批准与 stale 字段结构，以及变更时的确定性失效/跨问 stale 传播 | `runtime_assurance.py`、审批/同步/事务验证器；不由框架摘要或路由推断写入 |
| `core/workbook_schema.yaml` + `core/numerical_verification_contract.yaml` + `core/user_execution_contract.yaml` | accepted 工作簿、真实执行身份与数值证据的字段/资格/边界 | 主结果、分析结果、返回工作簿验收器；resolver 输出或框架摘要不能代替真实运行证据 |
| `AGENTS.md`、`RUNTIME_ROUTER.md` | 人类/Agent 操作说明与兼容边界 | 只说明并链接 Authority；不得与 Router、State、Workbook 或 gate catalog 争夺事实所有权 |
| 路由与 assurance 测试 | 锁定行为、兼容和失败边界 | `tests/test_router_contract.py`、`tests/test_v10182_paper_routing.py`、`tests/test_v712_runtime_assurance.py`、`tests/test_v900_phase_g_competition_runtime.py` 及其跨领域回归 |

### 11.3 门禁适用性与执行边界表

| Gate | Authority / 实现 | 适用触发与职责 | 不允许的简化 |
|---|---|---|---|
| `semantic_governance` | Router 决定何时进入序列；Manifest 指向 `scripts/validate_semantic_governance.py`；State Transition Authority 处理 stale | 当前模型语义/状态完整性；模型设计、代码交付、返回工作簿或实际正式交付中由有效计划要求时执行 | 不能因另一 gate 已执行或框架看似同步而跳过 |
| `model_approval` | `scripts/validate_model_approval.py` + `core/model_approval_contract.yaml` | 模型/预处理/主求解代码跨越相应边界前，验证当前 Model Challenge 与明确 Human Model Approval | 不得变成普通终稿门，也不能由旧 hash、读取计划或用户模糊的“继续”替代 |
| `code_delivery` | `scripts/validate_code_delivery.py` + `core/user_execution_contract.yaml` | 当前任务代码交付前验证代码/模型身份与适用工程条件，然后停在用户真实执行边界 | 代码存在、静态 CI 通过不等于用户已完成 full-fidelity 求解 |
| `user_execution_receipt` | `scripts/validate_user_execution.py` + Workbook / Numerical Verification Authority | 仅在用户返回执行产物后，核验真实执行回执、工作簿与数值资格 | 不得用代码生成、模拟回执或空工作簿替代真实执行 |
| `project_sync` | Router 的 formal-delivery scope 决定触发；Manifest 指向 `scripts/sync_project.py`；Output Contract 定义 scope-specific 语义 | design scope 不触发最终交付同步；其他正式 scope 按其适用产物、哈希和 stale 规则执行 | 不得对普通中间产物提前运行全量交付门，也不得把 sync PASS 当成模型/数值/视觉批准 |
| `submission_package_validation` | Router 的 submission route/segment；Manifest 指向 `scripts/validate_submission_package.py` | submission scope 最后核验 package、manifest、当前交付产物和适用竞赛规则 | 不得把 ZIP 存在、project_sync PASS 或旧 package PASS 当成当前正式提交资格 |
| 专项 gates（如 `claim_consumption`、`claim_evidence`、`model_code_conformance`） | 对应明确 audit route 与 Manifest utility-gate 声明 | 仅在相应显式核验意图或既有消费者条件成立时执行 | 不得把专项审计无条件追加到所有普通路由；也不得因门禁瘦身而丢失其独立风险覆盖 |

**顺序裁决：** Router 与经过边界处理的 resolver 输出拥有本次调用的有效 gate 顺序；`gate_plan` 按首次出现顺序去重。Manifest 只定义 gate 实现/输入/输出，Runtime Assurance Contract 只补充必要契约依赖，Output Contract 只定义交付语义。Reading Plan 明确保留 `pre_delivery_gates`，Bootstrap 要求按 resolver 顺序执行所有返回 gate。重复文本声明本身不证明存在重复执行；必须沿消费者链验证实际调用与副作用。

### 11.4 状态事实所有权表

| 事实类别 | 唯一机器事实源 | 写入 / 消费者 | 不可替代项 |
|---|---|---|---|
| 当前模型语义身份、revision、Challenge/Human Approval、机器 stale、状态 generation | `core/project_state.schema.yaml` 与 `core/state_transition_contract.yaml`；具体语义委托给 `core/model_approval_contract.yaml` | 既有 project transaction、语义/批准/同步验证器；resolver 只读取与诊断 | `模型论文框架.md`、路由返回值或旧语义 hash 不授予批准 |
| 助手可恢复的项目语义记忆与跨阶段摘要 | 项目内 `模型论文框架.md`，按 `core/output_contract.yaml#model_paper_framework` 和对应写作 Authority 维护 | 模型设计、分析、图表和论文阶段读取/同步 | 框架是语义记忆/摘要，不是数值真值、机器批准或 accepted 工作簿 |
| 主结果/分析结果数值、质量门、工作簿结构和真实运行身份 | 当前 accepted 工作簿及 `core/workbook_schema.yaml`、`core/numerical_verification_contract.yaml`、`core/user_execution_contract.yaml` 所规定的回执/验证链 | `validate_user_execution.py`、数值证据检查器、Analysis Necessity Gate 和下游证据消费者 | 不能从代码、计划、框架数字或静态测试推断数值正确 |
| 源码/运行产物身份、哈希、依赖和 stale 传播 | 各 Authority 规定的文件身份/哈希、当前项目 State 与 State Transition 合同 | 运行/回执/同步验证器及其消费者 | SHA-256 只证明字节身份，不证明数学正确或人工审查通过 |
| 人工模型/数学/视觉/论文审查 | 对应的 Model Challenge、Human Model Approval、作用范围明确的 review receipt 与人工审查记录 | 相关代码交付、图表和正式论文/提交边界 | 机器 schema、解析器、来源哈希和阅读计划不能替代人工语义或视觉判断 |
| Skill 仓库生成索引与 Manifest | 源文件为输入，`scripts/generate_indexes.py` 生成 | GitHub `refresh-generated` 工作流 | 生成文件不反向成为业务 Authority；禁止手工改哈希/索引 |

### 11.5 P0 结论与阶段 B 约束

1. P0 的基线、开放 PR、文件职责、gate 消费链与状态事实所有权盘点已完成；没有证据支持现在进行 State Schema 迁移，因此不启动阶段 C。
2. PR #276 已实现的通用竞赛回退、分类可选启动、非 LaTeX 写作 profile 延迟解析及 design scope 门禁边界已进入 main；阶段 B 不重复实现这些行为。
3. 默认 `resolve_runtime.py` 通过 `resolve_intent_assurance` 保持显式 intent 权威；旧 `resolve_workflow.py` 仍保留经测试的兼容性推断并集与 paper-carrier 例外。不能仅为统一代码风格而抹平二者的既有边界。
4. route/runtime-segment 存在部分相同的 gate 声明，但 resolver 按当前有效边界组合并去重；下一阶段只修复有可复现行为差异或真实重复副作用的路径，不根据文本重复直接删声明。
5. 本记录不是阶段 B 通过证明。阶段 B 仍须建立独立代码 PR，并以 G01—G18、R01—R06、原路由回归和六领域验收作为证据；所有未执行检查保持未完成状态。


### 11.6 合并后核验与阶段 B 的首个可复现缺陷

**合并后 main 核验已完成：** [HSK Skill CI #39999918643](https://github.com/Vexushi1/mathmodel-skill/actions/runs/39999918643) 最终结论为 `success`，实际 checkout 的 source head 与 main 合并 SHA 一致。完整 Python 3.10/3.14 shard 汇总、MATLAB R2024b native solver contracts、Production LaTeX attestation、LaTeX CUMCM/MCM-ICM/Diangong、Static contract lint 与 Generated file contract 均通过；没有失败 job。至此，PR #276 的合并后验收完成。

阶段 B 审计确认一个可复现的策略冲突，作为首个最小实现目标：

- `core/writing_runtime_contract.yaml#cross_file_chapter_handoff.activation.non_cumcm_or_missing_manifest` 明确声明 `full_reasoning_fallback`。
- 当前 `scripts/resolve_runtime.py::_apply_profile_writing_runtime` 在已识别的 Template-First profile 指向一个不存在的 manifest 时抛出 `ValueError`，使可选模板资源缺失阻断整个 LaTeX route；这与现有 Authority 不一致。
- 修复边界：manifest **字段未声明**或 runtime profile 不完整时仍按现有 fail-closed 规则处理；仅当 manifest 路径已声明但文件不存在时，保留通用 `core/writing_reasoning_contract.yaml`，不注册缺失 manifest、不进入 compact runtime，并按通用写作 Authority 继续。
- 新回归必须覆盖缺失文件场景，并保持现有 CUMCM manifest 存在时的 compact runtime、其他竞赛的 full reasoning fallback、非写作路由延迟加载行为不变。
- 门禁审计没有发现足以支持删除 gate 声明的重复副作用证据。当前 resolver 按首次出现顺序去重，reading plan 保留有效 gate 列表；阶段 B 将增加 G17 多正式意图场景的顺序/去重回归，不改变 gate 适用性或削弱检查。

阶段 B 的实现分支必须从通过合并后 CI 的 `main@75d772c84b75290f59f79b4d3e1eb2747e4eb3ec` 起建；本计划 PR 只维护文档，禁止在此分支叠加运行时代码。
