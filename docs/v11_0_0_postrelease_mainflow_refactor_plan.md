# v11.0.0 后主流程架构重构计划：项目级管理、逐问求解与全题交付

> **文档性质：** 仓库维护计划与架构提案，不是 Runtime Authority，不直接改变 Skill 运行行为，也不代表实现或测试已经通过。
>
> **日期：** 2026-11-22。
>
> **固定代码基线：** Skill v11.0.0，main@87ed5bbd173c02472a9e85cb09bdc4188d37a8bf。
>
> **计划 PR：** [PR #355](https://github.com/Vexushi1/mathmodel-skill/pull/355)，保持 Draft。
>
> **本次交付边界：** 只细化架构计划；不修改运行时代码、Schema、模板或正式业务规则，不合并 PR，不发布 Skill。
>
> **证据边界：** 本轮按 GitHub 固定提交读取源码、合同、测试与相关计划。没有运行 Resolver、仓库 checker、单元测试、MATLAB、用户赛题代码或本地生成器；不得将只读审查描述为运行验证。

---

## 0. 修改简报

| 项目 | 计划 |
|---|---|
| 修改主题 | v11.0.0 发布后的主流程架构重构 |
| 当前版本 / 基线 | v11.0.0 / main@87ed5bbd173c02472a9e85cb09bdc4188d37a8bf |
| 本 PR 变更等级 | docs-only，不升级 Skill 版本 |
| 后续实现版本 | 暂不预设；每个实现 PR 按真实接口、Schema 和兼容影响裁决 |
| 直接目标 | 明确项目级管理、逐问求解、全题终审三个运行层次；自动识别当前小问；检查只覆盖当前问和真实必要依赖；消除无关小问阻断；保留全局约束、下游 stale 传播和全题最终验收 |
| 用户收益 | 不反复提供已存在的项目状态；不为普通求解先证明本机平台/版本；不因 Q2 缺少无关产物而阻断 Q1；一次只交付当前小问的求解任务 |
| 明确不做 | 不重写数学建模方法论；不删除 Problem Contract、Model Challenge、Human Model Approval、SIB、数值验收、PQS、03B、Figure Evidence、论文写作、LaTeX/PDF 和最终交付门禁；不一次性生成全部小问求解代码；不增加第二套项目状态系统；不增加持久化 current_question 字段；不要求用户运行本地 checker |
| 权威事实源 | 当前 main 的 bootstrap、全局政策、Router、Module Manifest、Runtime Assurance、Project State Schema、State Transition、Output、Model Approval、User Execution、Workbook、Numerical Verification，以及实际消费者源码 |
| 本 PR 预计改动 | 更新本文件；保留 core/rule_corpus_sources.yaml 中 maintenance_and_history 登记；生成索引由 GitHub refresh-generated 管理 |
| 本 PR 禁止触碰 | 运行时脚本、业务合同、State Schema、工作簿 Schema、数值模板、MATLAB 模板和用户项目 |
| 兼容要求 | 现有项目状态、旧项目只读兼容、CLI、工作簿与回执版本、项目唯一后端、事务和 read-set 语义继续有效 |
| 验收方式 | 本 PR 验收计划文档、来源登记和 GitHub 生成工作流；后续每个代码 PR 单独做专项测试，最终冻结 head 后执行适用的完整 GitHub Actions |
| 回滚方式 | 本 PR 可独立 revert，不改变 main 运行行为，不迁移任何真实项目 |

### 0.1 本次工作的最终定义

这不是给旧流程增加三个补丁，而是重新明确 Skill 的运行组织方式：

**一个项目负责全局事实；一次问题级操作只推进一个小问；跨问关系决定等待条件；最终交付回到全项目范围。**

“逐问求解”不是强制 Q1、Q2、Q3 严格串行，也不是允许一次性生成全部小问代码。它表示：

1. 每次问题级求解动作只处理一个目标小问。
2. 目标小问只等待真实必要的上游依赖。
3. 前序小问被依赖的结果尚未满足时，其他独立小问仍可成为下一项任务。
4. 每个小问的模型审批、主求解、用户执行、工作簿验收和必要深化分析各自闭环。
5. 全题论文、综合结论、终审与提交仍检查所有必需小问。

---

## 1. 架构决策摘要

### 1.1 三个运行层次

**第一层：项目级管理（Project Runtime）**

- 赛题与附件整体审计。
- 全部小问 Problem Contract 和依赖关系登记。
- 项目级数据事实、preprocessing_decision 和共享预处理。
- 全项目唯一数值求解后端。
- 项目 State、框架、generation、事务与恢复。
- 项目级一致性和全局约束。

**第二层：逐问建模求解（Question Runtime）**

- 识别一个当前小问。
- 当前问模型设计、语义闭环、模型双审和人工批准。
- 当前问主求解代码交付、用户本地运行、工作簿与回执验收。
- 当前问 Analysis Necessity Gate 与必要的 03B。
- 当前问 Figure Evidence 和对应论文内容。

**第三层：全项目论文与最终交付（Submission Runtime）**

- 汇总所有必需小问的有效结果。
- 跨问综合、论文整体结构、摘要和结论。
- 全文图表引用、LaTeX 审计、编译和 PDF 检查。
- 最终审查、复现包或官方提交包验证。

### 1.2 三层之间的边界

| 工作 | 层次 | 说明 |
|---|---|---|
| 全题逐字审题、附件盘点、Problem Contract 列表 | 项目级 | 一次建立完整题目视图，不等于同时求解所有小问 |
| 项目级共享数据审计 | 项目级 | 根据真实数据与模型输入决定是否统一预处理 |
| 项目唯一求解后端 | 项目级 | 全部小问继承，不允许每问自行切换 |
| Qn 模型设计和批准 | 问题级 | 只审核当前问及其必要模型依赖 |
| Qn 主求解和结果验收 | 问题级 | 一次只处理当前问 |
| Qn 的 03B | 问题级 | 主工作簿 accepted 后按必要性决定 |
| Qn 图表 | 问题级 | 不因其他小问图表缺失而阻断 |
| 项目级预处理 | 项目级 | 仅 project_level 时执行一次，不能按每问重复 |
| 论文单问章节 | 论文层次中的问题级内容 | 按现有 writing runtime 和证据条件推进 |
| 摘要、跨问综合结论、终审、提交 | 全项目 | 必须检查所有必需小问 |

### 1.3 必须坚持的四条原则

1. **局部任务局部核验。** Q1 的代码交付不要求 Q2 的工作簿或图表已经存在。
2. **全局约束全局观察。** 单问模式不能隐藏 State 损坏、项目后端冲突、共享预处理变化或事务问题。
3. **变化沿真实依赖传播。** Q1 变化可以使依赖它的 Q2 stale，但不能无差别使独立 Q3 stale。
4. **最终交付全题验收。** 单问完成绝不等于全题完成。

---

## 2. 当前 v11.0.0 结构审计

### 2.1 现有架构与权威归属

| 层次 | 当前文件 | 当前职责 | 本次处理原则 |
|---|---|---|---|
| 启动 | core/bootstrap.yaml | 固定版本、权威源指针、启动事件和硬不变量 | 保持轻量，不复制业务流程 |
| 全局政策 | core/hsk_core_policy.md | 全局硬约束、阶段适用与工作边界 | 保留最小必要流程原则，让实现与之对齐 |
| 路由 | core/workflow_router.yaml | 意图、模块顺序、阶段边界、运行段和有序门禁 | 增加明确的逐问选择语义，不另造业务路由 |
| 模块与门禁 | core/module_manifest.yaml | 模块输入输出、utility gate、依赖合同 | 每个门禁保持唯一权威来源 |
| Runtime | core/runtime_assurance_contract.yaml | 项目上下文、意图来源、产物资格、依赖闭包、读取计划 | 明确项目范围与问题范围，不把诊断当执行授权 |
| 项目状态 | core/project_state.schema.yaml | 项目身份、每问状态、语义身份、执行状态和产物绑定 | 优先复用现有字段，不增加重复的当前问状态 |
| 状态转换 | core/state_transition_contract.yaml | typed stale、生命周期回退和跨问传播 | 保留全图传播，不因单问检查而裁剪 |
| 交付 | core/output_contract.yaml | 项目布局、每问产物、delivery scope 和正式交付要求 | 让 delivery_scope 与 question_scope 正交 |
| 模型批准 | core/model_approval_contract.yaml | Model Challenge、Human Approval、SIB 绑定 | 保留原审批门槛 |
| 数值执行 | core/user_execution_contract.yaml | 项目唯一后端、RUN_CONFIG、RUN_RECEIPT、full-fidelity | 仅调整环境元数据必填性，不放宽执行真实性 |
| 数值质量 | core/numerical_verification_contract.yaml | PQS 与主结果底层证据复核 | 不修改数值质量标准 |
| 执行入口 | scripts/resolve_runtime.py | 生成当前运行计划、项目保证、依赖诊断和门禁命令 | 补默认选问和问题范围传递 |
| 项目读取 | scripts/runtime_assurance.py | State 快照、问题范围、模型锁定和产物证据 | 保留整份 State 的一致性观察，细化语义范围 |
| 语义治理 | scripts/validate_semantic_governance.py | SIB、revision、依赖一致性和语义 stale | 当前无通用 --question，需要问题范围 |
| 项目同步 | scripts/sync_project.py | 发现产物、哈希、stale、正式交付检查和事务写入 | 当前按全部问题快照，需要问题范围 |
| 问题快照 | scripts/project_snapshot.py | 发现问题目录并读取每问产物 | 当前被同步器全量调用，需要目标/依赖快照 |
| 事务 | scripts/project_transaction.py | generation、read-set、并发保护、事务恢复和多文件提交 | 复用，不另建写入系统 |
| 框架生成 | scripts/instantiate_model_paper_framework.py | 从规范模板生成 compact/full 框架 | 复用其纯文本投影能力，由初始化编排器统一提交 |
| 执行验收 | scripts/validate_user_execution.py | 单工作簿回执、代码/数据身份和数值证据验收 | 保留单工作簿入口，移除新回执对非核心环境元数据的硬依赖 |

### 2.2 已经存在、必须复用的能力

| 现有能力 | 当前事实 | 结论 |
|---|---|---|
| 显式指定小问 | resolve_runtime 接受 question/--question | 不重新设计显式选问接口 |
| 问题级模型批准 | validate_model_approval.py 支持问题范围 | 复用现有批准验证器 |
| 单工作簿验收 | validate_user_execution.py 支持 --workbook | 返回 Qn 工作簿时不必验收全部小问 |
| 全项目结果闭合 | Runtime Assurance 已定义 validated_results；全流程最终交付检查所有注册小问 | 复用全题终审边界 |
| typed stale 传播 | State Transition Authority 支持 model/result/parameter/data 与 legacy untyped | 不重写依赖失效引擎 |
| State 快照一致性 | ProjectStateSnapshot 绑定原始 State 字节与 generation | 继续整份 State 快照和并发保护 |
| 原子多文件事务 | project_transaction.commit_project_state 支持 State 与伴随文件、read-set 和预期不存在路径 | 用于首次项目初始化 |
| 框架生成 | instantiate_model_paper_framework.instantiate() 返回经现有验证的文本 | 初始化器调用函数，不直接使用分开写文件的 CLI |

### 2.3 已确认的运行缺口

| 缺口 | 当前实现事实 | 用户可见影响 | 计划修复方向 |
|---|---|---|---|
| 缺少默认选问 | resolve_runtime 支持显式 Qn，但没有完整默认选择器 | 不指定题号时可能按全项目范围读取或产生多问分类歧义 | 增加只读问题选择器 |
| 无题号时聚合分类 | runtime_assurance._scope_questions 在无 question 时返回全部小问；_classification_for_scope 要求共享一套分类 | 不同题型小问可能被合并成歧义 | 问题级任务先选定 Qn，再读取该问分类 |
| 语义治理全量循环 | validate_semantic_governance.py 遍历全部 subproblems，CLI 当前没有 --question | 当前问可能被无关小问语义问题阻断 | 增加问题范围与必要依赖范围 |
| 同步器全量快照 | sync_project.synchronize() 没有通用 question 参数；通过 _question_names() 遍历所有小问 | Q1 的 code/results/figures 检查可能被 Q2 缺失产物阻断 | 增加 question scope，保留全局观察 |
| 同步器全量状态门 | _formal_state_issues() 遍历全部 subproblems；_scope_artifact_issues() 检查全部 snapshots | 单问 delivery scope 仍可能被其他问的质量状态或 stale 阻断 | 只对目标问和必要上游做局部交付检查；最终 scope 仍全题 |
| 依赖诊断不是执行授权 | _dependency_diagnostics() 只读观察 incoming result/legacy edges；合同明确它不改变 gate eligibility | 发现上游缺结果不等于实际代码交付门已阻断 | 把 typed dependency eligibility 接入既有 code_delivery 准入，不新增并行门禁 |
| 依赖诊断范围不完整 | 诊断主要处理 result 与 legacy untyped；model/data/parameter 语义分别在其他 Authority | 默认调度不能仅凭结果依赖表决定可执行性 | 复用各类型的现有语义，不把所有依赖都当成结果等待 |
| 项目初始化没有统一编排器 | 框架生成器只生成框架文本；State 事务能力存在，但没有入口将二者配套创建 | 项目记录创建与恢复缺少统一安全入口 | 新增轻量初始化编排器 |
| 新回执环境字段过严 | configuration_map() 将 solver_version、platform 列入通用必填项；新 RUN_CONFIG 已把 solver_version 作为可选兼容字段 | 新回执可能仅因缺少平台或版本信息被拒绝 | 区分执行真实性字段和可选环境元数据 |

### 2.4 必须保留的全局观察

单问范围不是“只读取一个文件夹”。以下检查仍然是项目级：

- 整份 state/project_state.yaml 必须可解析、符合 Schema，generation 合法。
- pending transaction journal 必须按原事务恢复规则处理；Resolver 不得隐式恢复或写入。
- 项目根唯一求解后端必须一致；不能因 Qn scope 忽略其他问的 backend 声明冲突。
- 项目级共享预处理的决策、输入来源和 accepted 工作簿必须保持当前。
- dependency graph 结构必须可解析；目标依赖闭包中的冲突、循环和不明确来源不能被忽略。
- 当前 State 的 generation/read-set/concurrency 保护必须覆盖所有写入。
- 发生变化的小问沿完整 typed dependency graph 向下游传播 stale；不得只传播到当前被检查的小问。

---

## 3. 目标运行范围模型

### 3.1 五个范围，不能混成一个 --question

| 范围 | 定义 | 典型内容 | 是否持久化 |
|---|---|---|---|
| Project Invariant Scope | 每次相关动作都必须观察的项目级约束 | State/schema/generation、唯一后端、共享预处理、依赖图结构、事务状态 | 现有 State/合同 |
| Target Question Scope | 当前动作直接处理的小问 | Qn 模型、代码、工作簿、分析、图表 | 现有 subproblem 状态和产物 |
| Upstream Prerequisite Closure | 当前问和当前阶段真正需要的上游问 | typed model/result/parameter/data 依赖 | 由现有 depends_on 推导 |
| Downstream Invalidation Closure | 某个源发生变化后，所有可能受影响的下游问 | typed stale 传播 | 由 State Transition Authority 推导 |
| Finalization Scope | 正式论文、终审与提交必须覆盖的全部注册小问 | 全部必需结果、分析、图表、章节和提交证据 | 现有项目状态与产物 |

**关键区别：** Target Question Scope 决定本次检查谁；Upstream Prerequisite Closure 决定本次依赖谁；Downstream Invalidation Closure 决定变化后使谁 stale；Finalization Scope 决定最终交付检查谁。

### 3.2 与现有 delivery_scope 的关系

当前 delivery_scope 表示 design/code/results/figures/docx/latex/submission 等交付阶段；它不等于小问范围。

目标接口是两个正交维度：

- delivery scope：本次检查哪一类交付。
- question scope：本次问题级交付属于哪个 Qn。

行为约定：

1. design/code/results/figures 支持单问范围。
2. 这些单问范围仍观察项目级不变量和必要上游依赖。
3. project-level preprocessing 是项目级动作，不伪装成每问重复执行。
4. docx/latex/submission 的最终资格仍覆盖所有必需小问。
5. 对论文单章的编辑可以有局部内容范围，但不得把最终交付门缩成单问。
6. mechanism scope 保留现有独立规则；选中某个 mechanism spec 时仍校验其 question ID。

### 3.3 单问同步的三段式数据流

每次 question-scoped sync 必须分开：

1. **全局观察：** 读取同一份 State snapshot，核对项目级不变量、generation、backend、共享预处理、dependency graph 结构和事务状态。
2. **局部快照：** 只读取目标问和当前阶段所需 upstream closure 的产物、源码、工作簿及身份。
3. **完整失效传播：** 若局部快照发现源变化，State Transition Authority 对完整 State 依赖图计算 downstream stale，不得因本次只检查 Q1 而裁掉 Q2。

对于无关小问：

- 不因其缺少代码、工作簿或图表而阻断当前问。
- 不把它的语义状态提升为 approved 或 accepted。
- 不删除它已有 stale。
- 不覆盖它未观察的产物哈希。
- 其变化在后续对应 scope 或全项目终审时仍可被发现。

---

## 4. 逐问选择与执行规则

### 4.1 默认选问优先级

选择器是 Resolver 的只读推导，不新增持久化 current_question。

1. **用户明确指定 Qn。** 优先处理该问；若该问依赖未满足，报告具体阻断，不自动跳去其他问。
2. **用户返回工作簿。** 通过标准路径、文件名和 RUN_RECEIPT 识别 question/stage；直接验收该工作簿，不再猜题号。
3. **用户明确要求继续/恢复。** 优先恢复唯一明确的等待点，例如当前问等待用户批准、用户本地执行或返回工作簿。
4. **项目级前置任务。** 若 project_level preprocessing 尚未 accepted，且它是当前可推进小问的共同必要条件，则先推进该项目级任务。
5. **选择第一道依赖满足的小问。** 按 Problem Contract 中的题目顺序，从尚未完成的注册小问中选择第一道当前阶段可推进的问。
6. **跳过被阻断但不相关的小问。** 若 Q2 因 Q1 结果尚未满足而等待，但 Q3 独立且可推进，则选择 Q3。
7. **没有可推进小问。** 报告具体上游缺口、循环或歧义；不随机选择。
8. **所有必需小问的 validated_results 已满足。** 转入项目级写作综合和最终交付，不再虚构一个当前求解问。

若 Problem Contract 未提供可核验顺序，按 Q 的自然数字顺序作确定性回退；不按字符串排序导致 Q10 排在 Q2 前面。

### 4.2 显式问号的阻断语义

- 用户明确说“继续 Q2”，即使 Q2 被阻断，也必须报告 Q2 的阻断原因。
- 不得静默改为 Q3，否则用户无法知道自己指定的 Q2 尚未满足条件。
- 用户明确改为 Q3 时，可以切换焦点；原 Q2 的等待状态必须保留，不能被覆盖或清除。
- 用户说“继续”但存在多个同等合理的等待点时，按 Problem Contract 顺序给出确定性选择；若状态冲突导致无法唯一判断，则只询问一个最关键的澄清问题。

### 4.3 一次只交付一个问题级求解任务

- 一次 code_delivery 只生成一个目标问的主求解入口及其必要辅助文件。
- 不因用户说“完成整道题”就一次生成 Q1-Qn 全部求解代码。
- 多问请求可以形成内部待办顺序，但当前只交付第一道可推进小问。
- 用户完成本问实际运行并返回工作簿后，再根据状态和依赖决定下一问。
- 若用户显式切换到另一独立问，原问的 awaiting_user_execution/approval 状态保留。
- 项目级预处理和最终论文交付不受“一次只做一个小问”限制，因为它们本来就是项目级动作。

### 4.4 Resolver 输出要求

Resolver 计划可增加只读选择诊断，但不得写回 State：

- selected_question
- selection_reason
- candidate_questions
- blocked_questions
- prerequisite_closure
- dependency_diagnostics
- scope_kind（question/project/finalization）
- 是否需要用户动作以及具体等待原因

这些是本次运行计划的解释，不是新的持久项目事实，不得当作批准、数值验收或 gate PASS。

### 4.5 full_solution 与 full_workflow 的逐问解释

现有 Router 中的 full_solution 和 full_workflow 表示用户的**项目级目标范围**，不表示一次性批量生成所有小问的求解代码，也不表示跳过用户批准、实际运行和结果验收。

- **full_solution：** 用户希望完成全部必需小问的数值求解。Resolver 每次仍只选择一个当前可推进的 Qn，交付该问的模型/代码/验收任务；在用户完成当前问的必要动作并再次继续后，按状态和依赖选择下一问。某问等待上游结果时，独立问可以先推进。
- **full_workflow：** 用户希望完成从审题到论文和最终提交的全项目流程。它包含 full_solution 的逐问循环，之后再进入跨问综合、论文、LaTeX/PDF 和最终提交。不得将它解释为一次调用中完成全部代码、所有数值运行或所有论文章节。
- **problem_analysis：** 仍是项目级整体审题和问题登记，可以一次性分析全部小问；它不等于一次性求解全部小问。
- **显式 Qn：** 对当前问题级动作优先指定目标问，但不会缩小全项目最终交付范围。
- **项目状态：** 不新增持久化 active_intent、current_question 或重复待办字段。已注册小问的状态、等待点、typed dependency 和已验收产物是后续选择依据；如果这些证据不足以判断用户是否希望继续全项目目标，则只执行当前明确动作，不擅自扩大交付。

因此，full_solution/full_workflow 可以在 Resolver 中保持项目级 intent 与完整路线，但其 question-level execution unit 必须始终是一个 Qn。每次遇到 Human Model Approval、用户本地执行、工作簿返回等既有等待点，均按原合同暂停；不能把“全流程”解释为取消这些等待点。

---

## 5. typed dependency 的执行资格

### 5.1 依赖类型与当前问的必要条件

| kind | 语义 | 下游执行前应核对什么 | 不应误判成什么 |
|---|---|---|---|
| model | 下游模型语义依赖上游模型 | 上游当前 SIB、semantic revision、Model Challenge 和 Human Approval 仍有效 | 不自动要求上游数值工作簿已完成 |
| result | 下游计算消费上游结果 | 上游 accepted primary、result quality passed；若上游 Analysis Necessity Gate=required，还须分析 accepted、必要处置完成；最终资格按 validated_results 语义判定 | 不仅凭文件存在或未验收工作簿放行 |
| parameter | 下游消费上游参数 | 参数值必须能追溯到当前 approved model/framework 或当前 accepted workbook；若来源是上游结果，按结果来源检查 | 不从聊天摘要、文件名或旧表格猜测参数 |
| data | 下游消费上游数据来源 | 原始数据身份当前；若 project_level，则统一预处理工作簿 accepted 且数据身份当前 | 不要求上游问先完成全部分析和图表 |
| legacy_untyped | 历史依赖没有明确类型 | 保留保守 stale 传播；若当前问资格依赖其具体含义，报告需要澄清 | 不自动解释为 result，也不当作无依赖 |

### 5.2 参数依赖的保守边界

当前 dependency_entry 只有 question、kind 和 note，没有通用参数 selector。计划第一阶段不凭自由文本猜测参数路径。

- 若当前框架或 SIB 已明确参数值及来源，按现有证据检查。
- 若参数来自上游 accepted workbook，沿结果来源检查。
- 若无法确定实际参数来源，阻断当前依赖该参数的小问并报告缺项。
- 不阻断不依赖该参数的其他小问。
- 若真实项目证明需要机器可核验的参数 selector，另行提出最小 Schema 变更、迁移和兼容测试；不得预先增加没有消费者的字段。

### 5.3 循环依赖与联合求解

- 目标问的上游 closure 存在真实循环时，不按普通 DAG 顺序自动排队。
- 报告循环涉及的 Q、各边类型和缺失证据。
- 退回 Problem Contract / Model Design，明确联合求解、初值、迭代更新、停止条件或其他实际数学结构。
- 不因 Q1-Q2 循环而阻断不在该循环闭包内的独立 Q3。
- State Transition Authority 继续检测并有限终止循环；本次不改变其纯状态转换职责。

### 5.4 Q1 / Q2 / Q3 标准场景

| 小问 | 依赖 | 当前条件 | 允许行为 |
|---|---|---|---|
| Q1 | 无 | 模型批准、项目级预处理（如适用）已满足 | 可独立求解 |
| Q2 | Q1 / result | Q1 的 validated_results 尚未满足 | Q2 等待，不生成正式依赖 Q1 结果的求解代码 |
| Q3 | 无 | 自身模型批准和数据条件满足 | 可在 Q2 等待期间独立推进 |
| Q2 | Q1 / model | Q1 模型身份已验证、批准有效，但 Q1 数值结果未完成 | Q2 可进入模型设计/求解准备；不人为等待 Q1 数值结果 |
| Q2 | Q1 / data | Q1 共享数据来源或 project_level 预处理发生变化 | 按数据身份与共享预处理当前性判断，不自动要求 Q1 的 03B 或 Figure Evidence |

Q1 的 Figure Evidence、论文段落或无关展示文件不应成为 Q2 的隐式前置条件。只有明确 typed dependency 或现有业务合同要求时才等待。

---

## 6. 项目级与逐问级工作流

### 6.1 新项目启动

| 步骤 | 范围 | 助手动作 | 停止/等待条件 |
|---|---|---|---|
| 1. 导入题目 | 项目级 | 读取题目、附件、评分与输出要求 | 材料缺失且会改变审题时报告缺口 |
| 2. 逐字审题 | 项目级 | 拆解背景、条件、约束、子问题、依赖和输出 | 不因无专属模板或无环境元数据而阻断 |
| 3. 数据审计 | 项目级 | 盘点字段、单位、粒度、主键、缺失、异常、时间/空间错位 | 只形成数据事实，不自动清洗 |
| 4. Problem Contract 注册 | 项目级 | 为全部 Q 建立问题目标、依赖类型和顺序 | 未确定的依赖保持未决，不猜测 |
| 5. 逐问模型设计 | 问题级 | 从第一道待设计问开始，形成 proposed_model_spec | 不同时输出全部小问求解代码 |
| 6. 首次项目记录创建 | 项目级 | 第一份 proposed_model_spec 成立后，原子创建 State 与框架 | 已有项目文件不得覆盖 |
| 7. 项目后端与预处理决策 | 项目级 | 根据全题可预见数值需求确定唯一后端；确定三态 preprocessing_decision | 不要求提前证明本机 platform/version；project_level 共享预处理按现有批准规则 |
| 8. 进入逐问循环 | 问题级 | 每次选择一个可推进小问 | 用户批准、用户运行和工作簿返回处正常暂停 |

### 6.2 单问生命周期

| 阶段 | 必须完成的事 | 不提前做的事 |
|---|---|---|
| Problem Contract | 目标、条件、输出、变量需求和依赖 | 不直接生成最终代码 |
| Model Design | 经典稳健路线、高级改进路线、公式闭环、假设与复杂度审查 | 不把算法名堆叠当创新 |
| Model Challenge | 正向审查与 Devil's Advocate 独立挑战 | 不用代码运行成功替代数学审查 |
| Human Model Approval | 用户明确批准当前语义身份 | 不把沉默当批准 |
| Preprocessing | 只执行当前决策要求的项目级或局部处理 | not_needed/question_local 不创建全局预处理目录 |
| Primary Code Delivery | 交付当前问主求解代码并做静态工程检查 | 不生成其他问的求解代码 |
| User Execution | 用户本地 full-fidelity 运行 | 助手不运行赛题专属数值入口 |
| Primary Acceptance | 核对工作簿、RUN_RECEIPT、代码/数据身份、PQS 和适用数值证据 | 不要求其他问工作簿同时返回 |
| Analysis Necessity | 对当前问判定 required/not_required | 不预先生成空 03B |
| Analysis Execution | required 时独立生成并验收当前问 03B | 不改写已冻结主求解入口 |
| Figure Evidence | 按当前问已验收数据和 Figure Authority 处理 | 不要求所有小问图表同时存在 |
| Question Result Closure | 形成当前问有效结果摘要与待办 | 不等于全题论文或提交完成 |

### 6.3 何时可以推进下一问

- 当前问的用户等待动作尚未返回时，默认恢复该等待点。
- 当前问 primary 未 accepted 时，不把它的结果作为下游 result dependency。
- 当前问 Analysis Necessity Gate=required 且分析未完成时，其 validated_results 尚未满足。
- 当前问 Gate=not_required 且有非空理由时，不生成 03B；这不是“稳健性已经通过”。
- 下游问只等待其 typed dependency 所需证据，不等待无关图表、写作或最终 PDF。
- 如果当前问结果被拒绝、语义变化或输入变化，按 State Transition Authority 使相关下游 stale。
- 当前问完成后，Resolver 再选第一道依赖满足的小问；不一次性生成剩余所有代码。

### 6.4 全项目收尾

只有全部必需小问满足现有 validated_results 语义，且相关 Figure Evidence、论文片段和提交证据 current 时，才允许进入相应全项目正式交付。

- Q1 solved 不等于 Q2/Q3 solved。
- 所有小问主工作簿 accepted 不一定等于所有 required 03B 已完成。
- 所有数值结果 validated 不等于图表已经人工审查。
- 图表通过不等于论文已完成。
- LaTeX 编译通过不等于 PDF 已逐页查看。
- ZIP 存在不等于提交包 validated。

---

## 7. 核验机制：按阶段、范围和身份触发

### 7.1 检查职责唯一归属

| 核验事实 | 唯一主要 Authority / 消费者 | 不应重复承担的职责 |
|---|---|---|
| Problem Contract 与语义闭环 | Problem Audit、Semantic Governance | Router 不裁决数学正确性 |
| SIB/revision/typed dependency 语义变化 | validate_semantic_governance.py 与 State Transition Authority | Sync 不另写一套语义 stale 规则 |
| Model Challenge / Human Approval | Model Approval Contract 与 validate_model_approval.py | 代码检查器不授予批准 |
| 代码静态质量与交付身份 | Code Quality / Code Delivery | 用户回执不替代静态代码检查 |
| 实际执行事实 | RUN_RECEIPT 与 validate_user_execution.py | RUN_CONFIG 不自报实际运行结果 |
| 主结果底层数值复核 | Numerical Verification Authority | 不把工作簿自报 Boolean 当独立复核 |
| 产物发现、哈希和 stale | sync_project.py + State Transition Authority | 不把同步器变成模型审批器 |
| 图表证据与视觉质量 | Figure Evidence Authority + 用户视觉检查 | 文件存在或图像哈希不等于视觉通过 |
| LaTeX/PDF | 现有 LaTeX audit/compile/PDF 页面检查 | 日志或文本提取不代替全页查看 |
| 全题最终交付 | Resolver 返回的正式门禁 + final review/submission contracts | 不以某个小问 PASS 推断全题 PASS |

### 7.2 触发矩阵

| 检查 | 触发时机 | 范围 | 复用原则 |
|---|---|---|---|
| State/schema/generation | 每次项目恢复或写入前 | 整份 State | 复用同一快照，不缓存 PASS |
| 项目 backend consistency | 进入数值设计/交付或后端迁移时 | 项目级 | 项目根唯一后端，不能每问重新选择 |
| preprocessing decision/currentness | 数据审计后、project_level 执行和下游数值交付时 | 项目级或实际数据依赖范围 | 共享预处理只验收一次；变化时重新处理 |
| Semantic Governance | 语义首次闭环、变化、代码交付和结果消费的必要边界 | 当前问及必要依赖；全题收尾为全项目 | 语义未变时只确认当前身份绑定，不重复人工双审 |
| Model Approval | 主模型形成后、数值代码交付前 | 当前问及必要 model dependency；project_level preprocessing 按共享消费者范围 | 纯措辞或实现变化不重新批准；语义变化必须重新挑战/批准 |
| Code Quality / Code Delivery | 首次交付或源码/bundle 变化 | 当前问 | 同一源码身份可复核绑定，不重复无变化的完整审查 |
| RUN_RECEIPT / Numerical Evidence | 用户返回对应工作簿后 | 当前问、当前阶段 | 一次绑定实际源码、数据和工作簿；不要求无关工作簿 |
| Analysis Necessity | 当前问 primary accepted 后 | 当前问 | Gate 决定是否激活 03B |
| Figure Evidence | 当前问正式图表请求/交付时 | 当前问及图实际依赖 | 不因其他问的图缺失而阻断 |
| Writing/LaTeX | 当前章节和对应来源满足时 | 当前章节；正式终稿按全项目 | 按 writing runtime 的阶段顺序和当前来源执行 |
| Final Review / Submission | 用户请求正式终审或提交时 | 全项目 | 必须检查所有必需问与最终证据 |

### 7.3 不重复检查的严格含义

“不重复检查”不是保存一个 PASS 布尔值后永远相信它。

允许复用的是：

- 当前已验收工作簿的原始字节与哈希。
- 已交付代码和 helper bundle 的原始字节身份。
- 已绑定的输入数据身份。
- 当前 SIB、semantic revision 和批准绑定。
- 现有事务与 State generation 证据。

每次使用时仍核对这些来源是否 current。不得只凭聊天记忆、文件名、Resolver assurance=pass 或旧回执声称当前资格；不得在源码/数据变化后沿用旧 accepted 身份。

### 7.4 写入与代次

project_transaction.commit_project_state() 每次提交都会推进 generation。因此后续实施应检查写模式 Validator 是否在状态完全未变时仍无必要提交。

- Semantic Governance：若候选 State 与当前 State 完全一致，优先返回只读结果，不提交无变化事务；若确有 semantic baseline/stale 变化，仍使用原事务和 read-set。
- Sync：先确认报告、框架同步头和 State 是否有实际变化；只有确有 State/框架变化时才提交相应事务。若只更新报告，必须用现有安全写入机制，不得绕过 read-set。
- 以上是需专项测试的实现优化，不得以减少 generation 为理由跳过 stale、并发或 source recheck。

---

## 8. 项目记录创建与恢复

### 8.1 初始化时机

当前 Output Contract 规定模型论文框架在 proposed_model_spec 后创建。本次保持这一业务边界：

1. Problem Audit 可先在当前对话中完成，不强制提前生成空 State。
2. Problem Contract 和全题依赖关系形成后，进入第一个小问模型设计。
3. 第一个 proposed_model_spec 已形成时，助手自动调用项目初始化编排器。
4. 初始化器一次性创建 State 与框架，并登记全部已知小问。
5. 后续问进入模型设计时更新各自已有条目，不重新初始化整个项目。

### 8.2 初始化器职责

拟新增 scripts/initialize_project.py，它是编排器，不是第二套 State Authority。

必须复用：

- scripts/instantiate_model_paper_framework.py::instantiate()：生成规范模板文本。
- core/output_contract.yaml：框架模式、目录与项目记录时机。
- core/project_state.schema.yaml：State 结构。
- scripts/validate_project_state.py 与 scripts/validate_model_paper_framework.py：现有验证。
- scripts/project_transaction.py：State 与框架的原子多文件提交。

禁止另建数据库/第二份项目状态；从聊天摘要填入批准、accepted 工作簿或数值；初始化时自动选择/批准模型；生成空 03B；覆盖已存在 State/框架。

### 8.3 全部小问注册

首次创建正式项目记录时，把 Problem Audit 中已确认的全部 Qn 登记到现有 subproblems map，而不是只登记第一个求解问。

pending 小问只记录：

- Qn 的 Problem Contract/分类与 capabilities。
- 已确认的 typed depends_on。
- status=audited 或等价的当前合法待设计状态。
- framework_section 锚点。
- result quality / analysis 的初始 pending 状态。
- 尚未选模型时 selected_model 为空，不伪造模型名。
- 不创建 semantic identity、validated hash、approved hash 或 accepted execution。

**前置测试：** 当前 Schema 的 selected_model 是 string 且没有 minLength，但仍必须通过 State Validator、Framework Validator 和 Semantic Governance 的真实测试，确认 pending stub 不会被当作已设计模型。如果任何消费者不接受空 selected_model，不得用“待定模型”伪装成真实模型；应在 PR-A 中给出最小兼容设计，必要时另行评估 Schema 变更。

模型论文框架需为每个注册小问提供真实章节锚点和 Problem Contract 槽位。规范模板仍是唯一模板来源；初始化器只做确定性扩展，不复制另一份论文规则。

### 8.4 初始化原子性

1. 捕获项目目录与预期不存在的 State/框架路径。
2. 捕获 Problem Contract、依赖图和 proposed_model_spec 来源身份。
3. 生成 State candidate 与框架 candidate。
4. 使用 commit_project_state() 的 expected_file_hashes、writes_before_state/writes_after_state 和 staged validators。
5. 同一事务提交 State 与框架，State generation 按现有事务规则推进。
6. 写后重新读取并校验两份文件及 generation。
7. 任何步骤失败时不留下“State 已有但框架没有”的半初始化项目。

### 8.5 恢复决策矩阵

| 现有情况 | 允许行为 | 禁止行为 |
|---|---|---|
| State 与框架均存在且一致 | 只读恢复当前上下文 | 重建或覆盖 |
| 两者均不存在，且确认是无历史产物的新项目 | 满足 proposed_model_spec 后初始化 | 早于现有 contract 创建空 State |
| 存在未完成事务 journal | 调用既有事务恢复流程，重新捕获快照后继续 | Resolver 自动恢复或初始化器覆盖 journal |
| State 缺失、框架存在 | 先找可信原始备份/版本历史；无备份时停止并报告恢复风险 | 从框架自动合成历史批准和 accepted 结果 |
| 框架缺失、State 存在 | 从可信原始备份恢复；无备份时停止模型语义依赖任务 | 从 semantic hash 反向生成模型公式和假设 |
| 两者都缺失但项目目录已有代码/工作簿 | 进入显式 recovery_required，检查可信来源并等待用户决定 | 当作全新项目重新初始化并覆盖历史 |
| State 与框架 SIB/hash/revision 不一致 | 报告冲突、保留原始字节、按现有语义治理处理 | 自动选择其中一个并清除 stale |
| 历史工作簿存在但 State 丢失 | 仅作为历史文件观察，不自动认定 accepted | 从文件存在或聊天摘要恢复 accepted |

若将来增加显式 degraded rebuild，必须要求用户确认；重建后的模型批准和数值接受默认回到待核验状态，历史工作簿只读保留。不得伪造原审批。

---

## 9. 环境元数据与执行真实性

### 9.1 先纠正问题定位

当前问题不是通用的“运行前本机身份检查”：

- 新 RUN_CONFIG 已将 solver_version 作为可选兼容字段。
- 当前 Model Approval Brief 已允许记录尚未验证的环境条件。
- 真正阻断点在 returned-workbook 的 configuration_map()：它把 solver_version 与 platform 列入通用必填项。
- MATLAB 模板中的 JVM 与 License 断言属于实际运行依赖，不是可删除的身份装饰。

因此，PR-E 的范围是：**新版本回执不再要求用户证明本机平台/版本元数据；保留真实执行来源、实际停止和 full-fidelity 证据。**

### 9.2 字段分层

| 字段/证据 | 新版本要求 | 说明 |
|---|---|---|
| semantic_identity_hash / validated_semantic_identity_hash / approved_semantic_identity_hash | 必须 | 数学模型身份和批准绑定 |
| semantic_revision / Model Challenge / Human Approval | 必须 | 不允许跳过或伪造 |
| code_sha256 | 必须 | 当前实际入口源码 |
| code_bundle_sha256 | 适用版本必须 | 入口与项目 helper 的源码闭包 |
| data_sha256 | 必须 | 实际输入数据身份 |
| solver_backend | 必须与项目唯一选择一致 | 不是机器身份，不允许静默切换 |
| solver | 必须 | 实际算法/求解器事实 |
| tolerance / iteration_or_time_limit / random_seed | 必须 | 计划与实际运行事实绑定 |
| actual_stop_reason | 必须 | 真实停止原因 |
| fallback_used | 必须为 false | 禁止静默回退 |
| execution_owner | 必须为 user | 助手不得代跑题目专属数值代码 |
| execution_profile | 必须为 full_fidelity | 不得缩减计算 |
| 六个 no-degradation 标志 | 必须保持 false | 不降低数值要求 |
| solver_version | 新版本可选 | 实际可得则记录，不作为通用阻断 |
| platform | 新版本可选 | 实际可得则记录，不作为通用阻断 |
| matlab_release | 可选 | 实际可得则记录；不新增必填要求 |

### 9.3 版本与兼容

- 显式声明当前受支持 RUN_RECEIPT 版本的新 writer：solver_version/platform/matlab_release 缺失不应单独导致验收失败。
- 若字段存在，按可选元数据进行格式检查；不应把缺失当作执行失败。
- 无版本握手的旧历史回执仍按现有 legacy read-only 兼容规则读取，不静默把新 writer 降级为 legacy。
- 旧 FULL_FIDELITY_CONFIG/FULL_RUN_CONFIG 的原字段规则不因本次修改而放宽。
- 不删除 MATLAB 模板在可得时记录 version/computer/release 的代码；只是这些字段不再决定新回执的核心资格。
- 不要求用户提供硬件序列号、CPU ID、操作系统指纹、许可证序列号、环境快照哈希或额外本机证明文件。

### 9.4 真实运行依赖仍保留

- MATLAB JVM、MATLAB License、所需 Toolbox 或 Python 包是实际运行条件。
- Model Approval Brief 可记录需要的依赖和未验证条件。
- 不在求解前要求用户提交一套机器环境证明。
- 用户运行时依赖缺失，按真实运行错误处理；不静默换后端、换求解器或降精度。
- 改变项目唯一 backend，必须走现有显式 backend migration/confirmation。

---

## 10. 具体文件与接口映射

| 实施主题 | 预计文件 | 具体责任 | 明确不做 |
|---|---|---|---|
| 项目初始化 | 新增 scripts/initialize_project.py | 创建全部问题登记、框架与 State 的统一编排 | 不新增 State Authority |
| 框架生成 | scripts/instantiate_model_paper_framework.py、templates/model/model_paper_framework.md | 复用规范模板并生成多问 skeleton | 不复制论文写作规则 |
| 问题选择 | scripts/resolve_runtime.py，必要时新增纯函数 scripts/question_scheduler.py | 显式问号、等待点、依赖就绪、题目顺序和下一项选择 | 不持久化 current_question |
| 选择与依赖合同 | core/workflow_router.yaml、core/runtime_assurance_contract.yaml | 规定一问一动作、typed dependency eligibility 和范围 | 不新增并行门禁 |
| 语义治理 | scripts/validate_semantic_governance.py | 增加问题范围；保留全项目默认模式和 downstream propagation | 不只检查目标目录而丢弃全图 |
| Model Approval | scripts/validate_model_approval.py、Resolver gate command | 复用现有 --question 能力；核对目标问和必要 model closure | 不改 Model Challenge 或人工批准规则 |
| Code Delivery | scripts/validate_code_delivery.py | 在现有交付门检查当前问和必要上游依赖资格 | 不重新实现 SIB 或数值验收 |
| 问题快照 | scripts/project_snapshot.py | 生成目标问与依赖 closure 的快照 | 不把未注册历史目录当成正式问题 |
| 单问同步 | scripts/sync_project.py | 增加 question scope；将目标快照和全局观察分开 | 不裁剪 State Transition 全图 |
| 同步合同 | core/output_contract.yaml | 明确 delivery_scope 与 question_scope 正交及 final scope 全题规则 | 不复制 workbook 规则 |
| stale 传播 | scripts/state_transitions.py、core/state_transition_contract.yaml | 继续负责完整 typed downstream invalidation | 不新增 private stale set |
| 环境元数据 | core/user_execution_contract.yaml、scripts/validate_user_execution.py | 新版本回执环境字段可选，核心执行事实严格 | 不删除执行真实性字段 |
| 入口说明 | AGENTS.md、SKILL.md、core/hsk_core_policy.md、相关 modules 与 scripts README | 让用户理解项目层/小问层/最终层流程 | 不在多个文件复制同一硬规则 |
| 回归 | 相关 tests 与新集成夹具 | 覆盖一问隔离、typed dependency、全题收尾、初始化、环境字段 | 不删除现有有效断言 |

---

## 11. 统一主流程实施分支与 PR 边界

### 11.1 统一实施的核心范围

本次运行时改造以一个核心主题实施：**Question-scoped Mainflow（逐问主流程）**。项目初始化、自动选问、typed dependency 执行准入、问题级语义治理、问题级同步和全题收尾必须形成同一条一致的执行链。

如果把这些部分拆成若干独立合并 PR，容易产生无法接受的中间状态：

- Resolver 已自动选择 Q1，但 semantic governance 仍全量检查所有小问，导致自动选问后仍被无关 Q2 阻断。
- sync 已按 Q1 过滤产物，却没有按完整 State 依赖图传播 stale，导致下游 Q2 的失效被隐藏。
- dependency gate 已要求 Q2 等待 Q1，但项目初始化没有登记全部 Problem Contract，导致选择器无法完整判断 Q3 是否独立。
- 局部同步已经放行，但最终 docx/latex/submission 仍沿用局部范围，导致全题终审被意外缩小。
- 初始化、Resolver、Sync 分别维护一套 current question 或 dependency 解释，导致同一项目出现多个事实来源。

因此，主流程相关运行时代码不应拆成多个先后合并、却各自不能独立保证核心不变量的 PR。它们在一个统一分支中分阶段提交、分阶段专项测试，最终以一个主题明确的 PR 一起审查和验收。

### 11.2 统一主流程实施分支

拟建立的分支：

- Branch：refactor/v11-question-scoped-mainflow
- Base：实施启动时最新 main，不得基于任何旧 PR 分支。
- PR 主题：refactor: implement question-scoped mainflow
- 交付范围：项目记录初始化、默认选问、一问一动作、typed dependency 执行准入、问题级语义治理、question-scoped sync、完整 stale 传播、全题 finalization，以及它们必需的合同、模块说明和集成测试。

该 PR 虽可能涉及超过 20 个活动文件，但所有文件共同实现一个不可拆散的运行时不变量：**一次问题级动作只检查当前问和真实必要依赖，同时保持全局不变量与完整下游失效传播，并将最终交付恢复为全题范围。**

PR 描述必须按治理规范解释超过 20 个文件的必要性，并提供每组文件的职责映射、旧接口兼容、迁移和回滚方式。若实施中发现某项改动可以独立合并且不会造成上述中间状态，则必须先重新评估 PR 边界，不为追求“统一”而强行扩大范围。

### 11.3 统一分支内的分阶段提交

| 阶段 | 代码主题 | 预计主要文件 | 阶段完成证据 |
|---|---|---|---|
| M0 | 固定基线与三问行为夹具 | tests/fixtures、tests/test_question_runtime_integration.py | 先用正式 Resolver/Sync 入口固定当前反例和正常对照，不以 mock 代替行为证据 |
| M1 | 项目初始化与安全恢复 | 新增 scripts/initialize_project.py；scripts/instantiate_model_paper_framework.py；scripts/project_transaction.py；State/Output 合同 | State 与框架原子创建；全部已知 Qn 登记；重复初始化不覆盖；恢复不伪造批准和数值 |
| M2 | 默认选问与一问一动作 | scripts/resolve_runtime.py；必要时新增纯函数 scripts/question_scheduler.py；workflow/runtime assurance 合同 | 显式 Qn 优先；唯一待续任务恢复；阻断问不静默跳过；独立问可被选择 |
| M3 | typed dependency 准入与问题级语义治理 | scripts/validate_semantic_governance.py；scripts/validate_code_delivery.py；scripts/validate_model_approval.py；Resolver gate commands | model/result/parameter/data 按真实语义准入；当前问只检查目标及必要闭包；全局 Schema/backend 检查仍有效 |
| M4 | 问题级同步与完整 stale 传播 | scripts/project_snapshot.py；scripts/sync_project.py；scripts/state_transitions.py；Output/State Transition 合同 | 目标产物快照与全局观察分离；全依赖图 stale 传播；最终 delivery scope 仍全题 |
| M5 | 入口、模块和集成收尾 | core/workflow_router.yaml；core/module_manifest.yaml；core/runtime_assurance_contract.yaml；core/output_contract.yaml；SKILL/AGENTS/相关 README；新增集成测试 | 用户入口、Resolver 计划、实际门禁命令、状态和恢复行为一致；核心能力非回归 |

每个阶段先添加可复现反例，再完成最小实现，再运行该阶段的 GitHub 专项测试。阶段中间提交不代表最终 PR 已通过；最终 PR head 必须执行适用的正式完整验收。

### 11.4 为什么主流程不拆成多个独立合并 PR

本次统一分支不是把无关功能堆进一个大 PR。以下项目均是 Question Runtime 的必要组成：

1. 初始化时登记全部问题，提供完整 Problem Contract 与依赖图。
2. Resolver 选出唯一目标问，避免无题号时全项目分类聚合。
3. Semantic Governance 与 Model Approval 只检查当前问及必要模型依赖。
4. Code Delivery 和 typed dependency eligibility 确保下游不会消费尚未 accepted 的上游结果。
5. Sync 只检查当前问与必要上游产物，但 State Transition 仍观察全图并传播 stale。
6. Submission Runtime 重新切换为全题范围。

这些组件的输入输出和安全边界彼此依赖。分开合并会让某一阶段短暂出现“局部放行但全局失效未传播”或“Resolver 选问成功但下游全量门禁仍阻断”的不一致状态。分阶段提交与专项测试可以保留开发可审查性，同时避免把不完整运行时暴露为正式 main。

### 11.5 环境元数据解耦作为独立 PR

环境元数据不是 Question Runtime 的依赖，不应混入主流程统一分支。

拟独立建立：

- Branch：fix/v11-run-receipt-environment-metadata
- PR 主题：fix: make nonessential execution environment metadata optional
- 范围：core/user_execution_contract.yaml、scripts/validate_user_execution.py、Python/MATLAB 回执模板及对应测试（仅在真实消费者要求时修改）。
- 资格：新版本 RUN_RECEIPT 缺少 solver_version/platform/matlab_release 不得单独失败；核心执行真实性字段继续严格；legacy reader 语义不变。
- 顺序：可在主流程 PR 之后实施，也可在独立维护轮次实施；不得为了“统一分支”把它合入 Question Runtime。
- 版本：按最终兼容影响与治理规范裁决，不在本计划中预设。

### 11.6 分支创建门槛

统一主流程分支只有在以下条件满足后才创建：

1. 本计划 PR #355 的文档、来源登记和生成文件状态已核对。
2. PR #355 的最终 head GitHub Actions 具备可核验的适用检查结果；action_required、等待审批、无 job 记录均不视为通过。
3. 用户审查并明确批准主流程计划。
4. 重新读取创建时最新 main、bootstrap、治理文件、相关权威合同及所有开放 PR/分支。
5. 比较当前 main 与本计划固定基线；若已变化，重做相关文件与重叠 PR 影响审查。
6. 从最新 main 创建唯一统一主流程分支，不 cherry-pick 已进入 main 的旧提交，不继承旧分支生成文件。
7. PR #355 仍是计划 PR；统一主流程实现 PR 不得复用 PR #355 的 docs-only 分支。

本计划不授权自动合并 PR #355、统一主流程 PR 或环境元数据 PR。
## 12. 必须建立的回归矩阵

### 12.1 三问核心集成夹具

固定一份三问项目：

- Q1：独立问题。
- Q2：typed result dependency 指向 Q1。
- Q3：独立问题。

另加变体：Q2 仅依赖 Q1/model、Q2 依赖 Q1/parameter、项目级共享预处理、循环依赖。

### 12.2 问题选择测试

| 场景 | 期望 |
|---|---|
| 显式指定 Q2，依赖满足 | 只选择 Q2 |
| 显式指定 Q2，result dependency 未满足 | 明确报告 Q2 等待，不自动改选 Q3 |
| 未指定问号，唯一等待点是 Q1 用户执行 | 恢复 Q1 |
| Q2 被 Q1/result 阻断，Q3 独立且可推进 | 选择 Q3 |
| Q1/model 已批准但结果未完成，Q2 只依赖 model | 不要求 Q1 数值结果 |
| Q1 primary accepted，但 03B required 尚未完成，Q2 依赖 Q1 validated result | Q2 等待 |
| 所有必需小问 validated_results 已满足 | 选择项目级论文/终审任务 |
| 多个等待点冲突且无法唯一判断 | 报告歧义，不随机选择 |

### 12.3 单问与全局范围测试

| 场景 | 期望 |
|---|---|
| Q1 code scope，Q2 缺少主代码 | Q1 不被 Q2 阻断 |
| Q1 results scope，Q2 缺少工作簿 | Q1 不被 Q2 阻断 |
| Q1 figures scope，Q2 stale 且无依赖 | Q1 不被 Q2 阻断 |
| Q1 有 Q2/result dependency | Q1 必须核对 Q2 的必要上游证据 |
| Q1 sync 时项目根 backend 冲突 | 阻断 Q1，因为这是全局不变量 |
| Q1 sync 时 State generation 并发变化 | 拒绝旧快照写入 |
| Q1 变化且 Q2 依赖 Q1 | Q2 正确 stale |
| Q1 变化且 Q3 独立 | Q3 保持 current |
| docx/latex/submission scope | 检查所有必需小问，不受单问过滤 |
| project_level preprocessing | 作为一次项目级共享动作，不按每问重复 |

### 12.4 语义治理测试

- Q1 语义变化：Q1 自身与必要下游按 typed impact stale。
- Q2 有不相关的待审模型：不阻断独立 Q1。
- Q2 与 Q1 的 dependency SIB/State 不一致且位于 Q1 相关闭包：阻断相关问。
- Q3 与 Q1 无关的语义问题：保留诊断，不污染 Q1 资格。
- 完整项目 finalization：全部注册小问的语义和审批按全项目条件核对。
- State Schema 本身损坏：仍全局拒绝，不允许用 question scope 绕过。
- Legacy untyped dependency：不被误判为无影响，不自动猜成 result。

### 12.5 项目初始化与恢复测试

- 全新项目、单问、三问、五问。
- 所有 Qn 已登记，但仅 Q1 有 proposed model。
- pending 小问不被误判为 approved/solved。
- selected_model 空值规则由 Schema、State Validator、Framework Validator、Semantic Governance 联合验证。
- 重复初始化同一输入：幂等，不覆盖。
- 初始化中断：事务可恢复，不能留下半成品。
- State 缺失、框架缺失、两者不一致、journal pending、历史数值文件存在等恢复矩阵全部覆盖。
- 没有可信原始来源时，不合成批准、哈希和 accepted 数值。

### 12.6 环境元数据测试

- 新版本 RUN_RECEIPT 缺少 solver_version/platform：可通过对应元数据检查。
- 新版本有合法元数据：保留并记录。
- 新版本有格式异常的可选元数据：给出非核心元数据诊断，不覆盖核心执行事实。
- 缺 code_sha256/code_bundle_sha256/data_sha256：失败。
- backend 与项目根选择不一致：失败。
- actual_stop_reason 缺失、fallback_used=true、full_fidelity 标志不符：失败。
- legacy unversioned receipt：维持原兼容规则。
- MATLAB JVM/License 不可用：实际 MATLAB 运行失败，不由助手提前伪造证明或自动切换。

### 12.7 核心能力非回归

必须继续覆盖：

- SIB 完整性和 semantic_revision。
- Model Challenge 两个独立 pass。
- Human Model Approval 明确绑定。
- project_level preprocessing 的真实输入与 accepted workbook。
- 项目唯一 Python/MATLAB backend。
- code SHA / bundle SHA / data SHA。
- RUN_CONFIG / RUN_RECEIPT 版本握手。
- full_fidelity/no-degradation。
- PQS 与数值证据独立复核。
- Analysis Necessity Gate。
- required 03B 的完整实验覆盖与主张处置。
- Figure Evidence 与人工视觉检查。
- LaTeX 审计、正式编译、PDF 全页查看。
- 最终提交包 allowlist 与内容校验。

---

## 13. 现有测试复用与新增测试

| 测试文件 | 本次用途 |
|---|---|
| tests/test_v712_runtime_assurance.py | 问题级 assurance、模型依赖和 SIB 传播 |
| tests/test_v900_semantic_governance.py | 语义闭环、依赖冲突、typed transition |
| tests/test_v900_state_transitions.py | stale、依赖类型、循环和幂等 |
| tests/test_sync_project.py | 当前同步范围和交付要求 |
| tests/test_sync_project_source_read_set.py | 同步过程源码/工作簿读集 |
| tests/test_project_state_read_snapshot.py | State snapshot、generation 和 scope read |
| tests/test_project_transaction_read_set.py | 多文件事务、并发、缺失路径与恢复 |
| tests/test_user_execution_contract.py | 单工作簿、回执、代码/数据身份和数值验收 |
| tests/test_v900_transactional_writers.py | State writer 事务保护 |
| tests/test_solver_backend_runtime_resume.py | 项目唯一 backend 与恢复行为 |
| tests/test_framework_project_memory_contract.py | 框架作为项目记忆的职责边界 |
| tests/test_v900_phase_h_sync_split.py | sync 兼容接口和拆分行为 |

拟新增专项测试：

- tests/test_project_initialization.py
- tests/test_question_scheduler.py
- tests/test_question_scoped_semantic_governance.py
- tests/test_question_scoped_sync.py
- tests/test_environment_metadata_optional.py
- tests/test_question_runtime_integration.py

新增测试必须围绕行为反例，不以函数名存在或 CLI 参数能解析作为验收。

---

## 14. 兼容、迁移与回滚

### 14.1 CLI 兼容

- 现有 Resolver 显式 --question Qn 保持。
- 新 selector 仅在 question-specific route 且用户未指定 Qn 时生效。
- 项目级 route 仍保持 project scope。
- sync_project.py 增加 --question；未传时保留旧 project-scope 行为。
- validate_semantic_governance.py 增加 --question；未传时保留旧全项目语义检查。
- validate_model_approval.py 已有问题范围能力，保持。
- validate_user_execution.py --workbook 保持单工作簿行为。
- 不改变旧项目 State 的读取含义；如需新增 Schema 字段，另行版本和迁移评估。

### 14.2 旧项目

- 已有 State 与框架的项目不重新初始化。
- 只有部分小问已登记的旧项目，不从目录名或历史文件擅自生成完整状态。
- 未注册的 Qn 被显式指定时，先要求完成 Problem Contract/项目登记。
- 旧项目缺少新 selector 需要的信息时，保持显式 Qn 路径；不假装自动选择成功。
- legacy untyped dependency 保持保守传播，不自动推断为 result。
- 历史回执、工作簿和旧 backend 记录继续按原只读兼容规则处理。

### 14.3 回滚原则

- 每个实现 PR 独立 revert。
- 回滚代码不自动恢复项目状态中的旧批准或 accepted 资格。
- 新状态字段若存在，必须有明确兼容读取和迁移策略。
- 已被真实上游变化判 stale 的下游产物不能因回滚代码自动变 current。
- 任何迁移、重建或恢复都必须有原始来源与字节身份；无法确认时停止并报告。

---

## 15. 相关计划、开放 PR 与分支整合策略

本次不是把所有旧分支直接合并，也不是按 PR 数量机械 cherry-pick。所有实现必须以当前 main 为唯一代码基线；旧分支只提供历史设计、反例和可复用测试思路。

| 相关材料 / PR | 当前核对结果 | 本次处理 |
|---|---|---|
| docs/runtime_router_and_gate_simplification_refactor_plan.md | 历史路由/门禁简化方案；必要质量控制和减少重复核验的原则已进入当前全局政策及部分实现 | 复用仍有效的原则，不重复实施已落地部分 |
| docs/stage_reading_execution_refactor_plan.md | 当前已有固定版本原文读取、来源身份和完整性机制 | 继续复用现有 Reading Authority，不在主流程 PR 重造全文读取系统 |
| docs/repository_audit_and_handoff_refactor_plan.md | 历史审计和交接记录 | 作为来源索引，按当前 main 复核，不把历史状态当现状 |
| PR #326 | 旧基线的工作流范围与数值验收计划；包含单问启动/全题收尾和循环依赖设计 | 只吸收仍适用的设计和反例；旧分支不作为代码基线 |
| PR #335 | 正式全文启动与阅读架构计划 | 当前 v11.0.0 已有 full_reading 相关实现；不复制阅读架构 |
| PR #336 | 基于 v10.35.3 的逐文件重构计划 | 与当前 main 分叉；只参考尚未被当前实现覆盖的设计，不 cherry-pick |
| PR #339–#347 | 已核对的分支 head 是当前 main 的祖先；PR 仍处于开放状态，但相关提交已进入固定 main | 不重复 cherry-pick；不把开放 PR 状态误认为其代码尚未进入 main |
| PR #349–#350 | 已核对的分支 head 是当前 main 的祖先 | 复用当前 main 中的结果，不重复合并 |
| PR #348 | 基于旧 P1 分支，含客户端试验题包、盲评和观测工具；与当前 main diverged | 保留为独立客户端试验工作，不纳入 Question Runtime；如后续需要其证据设计，按内容重审，不直接合并旧分支 |
| PR #355 | 当前 main 基线上的 docs-only 主流程计划 | 保持独立 Draft，完成计划审查和 GitHub 验收后，再作为统一主流程分支的设计依据 |

### 15.1 旧分支如何被“参考”

- 已进入 main 的代码只从 main 读取，不再从旧分支复制。
- 旧计划只提取当前仍缺少的设计决策、业务反例和兼容要求。
- 旧测试只有在能证明当前 main 尚未覆盖某个行为时才移植；移植时重写为当前接口与当前状态模型，不原样 cherry-pick 旧测试提交。
- 旧生成文件、Manifest、索引和哈希一律不移植。
- 对 PR #348 的客户端试验材料不作为运行时实现依赖；主流程集成验收仍由三问合成项目和 GitHub 正式测试负责。

### 15.2 冲突与串行处理

- 新分支一律从创建时最新 main 建立，不以 #326/#335/#336/#348 或 #339–#350 为 base。
- 若 PR #355 的计划文件尚未合并，统一主流程分支仍不得包含计划分支的旧生成文件；计划文档作为独立审查来源引用。
- 若主流程实施期间其他开放 PR 改动相同权威文件，按治理第 6.4 节停止、判断重叠、串行合并或重新基于最新 main 建立，不强行叠加。
- 环境元数据独立 PR 不与主流程分支共享同一未合并 head；若它先改动相同执行合同，主流程 PR 需在新 main 上重新审查执行合同影响。
- 不关闭、不合并其他开放 PR，除非其维护者/用户另行决定；本计划只决定本次改造如何安全吸收已有工作。

---


## 16. 验收标准与完成定义

只有同时满足以下条件，才能认为主流程架构重构完成：

1. 用户发起新题时，助手先完成项目级审题和问题登记，不要求先证明本机平台或版本。
2. 第一个 proposed_model_spec 形成后，项目框架与 State 能安全、原子地建立。
3. 用户只说“继续”时，Resolver 能根据当前状态和依赖选择一个小问；显式 Qn 优先。
4. 一次问题级求解操作只交付一个 Qn，不一次性生成全部小问求解代码。
5. Qn 的检查只覆盖当前问和真实必要上游，不被无关问的缺失产物阻断。
6. project backend、State/schema、共享预处理、generation、事务等全局约束仍严格有效。
7. typed result/model/parameter/data 依赖按真实含义决定等待；legacy untyped 不被静默解释。
8. Qn 变化沿完整 typed dependency graph 传播 stale；独立小问不被错误失效。
9. 新版本回执缺少 solver_version/platform/matlab_release 不会单独失败。
10. code/data/source bundle、solver backend、actual_stop_reason、fallback 和 full-fidelity 仍严格验收。
11. Model Challenge、Human Model Approval、SIB、PQS、03B、Figure Evidence、LaTeX/PDF 和最终交付全部保留。
12. 全题终审与提交仍要求所有必需小问满足现有 validated_results 和正式交付条件。
13. 不要求用户新增本地 checker、同步器或审计报告任务。
14. GitHub 最终 head 的适用正式 CI 通过，合并后 main 的 GitHub Actions 复核完成。

---

## 17. 本 PR 当前状态与下一步

**本 PR 只交付架构计划，不改变 Skill 运行时行为。**

### 17.1 六个计划部分的完成状态

| 部分 | 文档状态 | 说明 |
|---|---|---|
| 1. 现状架构审计 | 已形成 | 覆盖核心 Contract、Resolver、State、Sync、Snapshot、Transaction、执行验收与现有测试 |
| 2. 目标架构设计 | 已形成 | Project Runtime、Question Runtime、Submission Runtime 三层，以及五种正交范围 |
| 3. 完整流程设计 | 已形成 | 赛题导入、整体审题、问题登记、模型审批、逐问求解、分析、绘图、论文与最终提交 |
| 4. 核验机制重构 | 已形成 | 检查职责、触发时机、范围、必要依赖闭包、证据复用和全局不变量 |
| 5. 分批实施方案 | 已形成 | 一个统一主流程实施分支 M0–M5；环境元数据另一个独立 PR |
| 6. 完整验收方案 | 已形成 | 三问集成、异常/循环依赖、恢复、旧项目、Python/MATLAB 和最终交付非回归 |

“已形成”只表示计划文档已详细定义，不表示运行时代码已经实现或测试通过。

### 17.2 当前文档与 PR 状态

- 计划文档约 925 行，包含六个部分、统一分支策略、M0–M5 阶段、文件映射、兼容策略、回滚和测试矩阵。
- PR #355 基于 v11.0.0 main 87ed5bbd173c02472a9e85cb09bdc4188d37a8bf，保持 Draft，未合并。
- 计划修订已写入源文档；规则来源登记保持 maintenance/history，不进入规范性全文规则语料。
- GitHub refresh-generated run 44940120123 成功；生成的 MANIFEST、文件索引和 full-reading manifest 已进入当前 PR 文件列表。
- 最新已核对 PR head 为 82576dbebc413d30b22db4cd754cb9cd7cfc227c。

### 17.3 当前验证边界

- 最新已核对的 workflow_dispatch run 44940136874 针对 Draft PR 执行定向验证。
- 已通过：Static contract lint、Generated file contract、Python Figure rendering 3.10、Python Figure rendering 3.14。
- Windows Python targeted checks 在本次检查时仍在运行。
- 完整 Python 回归 shards、MATLAB R2024b native solver、Production LaTeX attestation 和 LaTeX matrix 在 Draft 定向模式下未执行，不能记为通过。
- 旧 head 的 action_required 和生成前 head 的 generated-file failure 不代表最新 head 的最终结果；应以最终 PR head 对应的最新运行记录为准。
- PR #355 当前没有 review submission、inline review thread 或评论记录。

### 17.4 尚未完成的工作

- 用户对计划的最终审查与明确批准。
- 将计划 PR 转为 Ready 后，对最终 head 执行适用的完整 GitHub Actions 验收。
- 从届时最新 main 创建统一主流程实施分支。
- 在统一分支中完成 M0–M5 运行时代码、阶段测试和最终集成验收。
- 创建并验收独立环境元数据 PR。
- 任何真实用户项目迁移或恢复。

### 17.5 下一步顺序

1. 用户审阅本计划的六个部分和统一分支边界。
2. 用户明确批准计划后，将 PR #355 转为 Ready，触发适用的完整验证；如有失败，先定位并修复计划/生成问题，不把定向检查当作全量通过。
3. 完整验证具备可核验证据后，重新读取创建时最新 main、bootstrap、治理规范、权威合同和所有开放 PR。
4. 从最新 main 创建唯一统一主流程分支 refactor/v11-question-scoped-mainflow，按 M0–M5 分阶段提交与专项测试，最终形成一个 Question Runtime 主流程 PR。
5. 环境元数据解耦另建分支和 PR，不混入主流程。
6. 各实现 PR 的最终 head 分别执行适用正式验收；不以计划通过代替代码通过。

**本 PR 不授权自动合并 PR #355、统一主流程实现 PR 或环境元数据 PR。**
