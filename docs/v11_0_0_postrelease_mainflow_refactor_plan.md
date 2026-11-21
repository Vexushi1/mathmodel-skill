# v11.0.0 发布后主流程改造计划：项目记录接管、执行环境解耦与逐问调度

> **文档性质：** 仓库结构盘点与后续改造计划，不是 Runtime Authority，不直接改变 Skill 行为。
>
> **状态：** 待用户审查；未获明确批准前，不启动三批业务代码实施。
>
> **编制日期：** 2026-11-21。
>
> **固定基线：** Skill v11.0.0，main / Release 对应提交为 `87ed5bbd173c02472a9e85cb09bdc4188d37a8bf`。
>
> **本次交付边界：** 只新增本计划文档；不修改活动规则、Schema、脚本、模板、测试或真实建模项目。

---

## 0. 修改简报

| 项目 | 本计划 |
|---|---|
| 修改主题 | v11.0.0 发布后的主流程改造：助手接管项目记录、移出用户环境核验、默认逐问推进 |
| 当前版本 / 固定提交 | v11.0.0 / `87ed5bbd173c02472a9e85cb09bdc4188d37a8bf` |
| 目标版本 | 暂不预设；三个实现 PR 的真实差异、兼容性和协议变化确定后再按治理规范裁决 |
| 本计划 PR 变更等级 | docs；只增加计划文档，不改变运行行为 |
| 后续实现等级 | 分别按实际 Schema、CLI、模板、状态与兼容影响评估 patch / minor / major，不提前承诺版本号 |
| 直接目标 | 以当前仓库真实分层为基础，把三个方向拆成可独立实施、可验收、可回滚的单主题 PR |
| 明确不做 | 不重建 v11 全文读取架构；不改项目级唯一 Python/MATLAB 后端政策；不取消 Model Challenge、Human Model Approval、用户 full-fidelity 执行、数值验收、03B 必要性判断或正式交付门；不把 Issue #352 的 embedded_parameters 混入本计划 |
| 权威事实源 | 当前 main 的 AGENTS.md、SKILL_CHANGE_GOVERNANCE.md、core/bootstrap.yaml，以及各方向对应的 Router、Output、State、Runtime、Approval、Execution、Workbook Authority 和实际消费者 |
| 本次预计修改文件 | 仅新增本文件；MANIFEST.sha256、SKILL_FILE_INDEX.md 等受管文件由 GitHub refresh-generated 处理，不手工编辑 |
| 禁止触碰 | main 上的活动业务规则、Schema、脚本、模板、测试、版本载体、真实用户项目文件及历史已验收工作簿 |
| 兼容要求 | 现有 v11.0.0 项目、历史 State、历史工作簿、RUN_RECEIPT、后端选择和 stale 规则保持可读；任何新写入规则不得追溯性要求旧项目重跑 |
| 本次验收 | 核对本计划内容、GitHub 生成结果和最终 PR head；不宣称三项运行时改造已实现或通过测试 |
| 回滚方式 | 本计划是独立 docs-only PR，可单独关闭或 revert；后续三个代码 PR 各自回滚，不以回滚代码伪造旧项目批准或数值资格 |

本计划遵循仓库治理：先盘点结构和现有能力，再确定改动归属；一个 PR 只处理一个核心主题。计划文档获用户审查通过，只代表允许进入后续实施简报，不代表三个代码 PR 自动获批、合并或发布。

---

## 1. 当前仓库结构盘点

### 1.1 顶层结构

当前 main 的根目录由入口与治理文件、规则 Authority、业务模块、运行脚本、模板、测试、历史计划、赛事资源和 GitHub 工作流组成。以下数量是 GitHub 当前目录直接子项数量，不等同于源文件数或测试用例数。

| 目录 / 文件组 | 当前规模 | 实际职责 | 与本次三个方向的关系 |
|---|---:|---|---|
| 根入口与治理 | 多个活动入口文件 | SKILL 启动、网页/App 项目指令、Agent 规则、仓库治理、索引与导航 | 三批实现都要保持入口只引用 Authority，不复制业务规则 |
| core/ | 28 项 | Bootstrap、Router、Module Manifest、State Schema、Output、Runtime、Approval、Execution、Workbook、Numerical Verification 等唯一规则来源 | 三个方向的主要规则修改层 |
| modules/ | 10 项 | 01 审题、02 模型设计、03P 预处理、03A 主求解、03B 深化分析、04 绘图、05 写作、06 终审 | 业务流程的规则说明；本次以复用现有模块为主 |
| scripts/ | 81 项 | Resolver、State/Artifact assurance、事务、快照、同步、代码交付、回执验收、后端选择、绘图后端和论文审计 | 三批主要实现层 |
| templates/ | 9 个直接子项 | Python/MATLAB 代码、工作簿 IO、模型框架、图表、LaTeX、DOCX/Review 等模板 | 第二批需要核对回执生成；第一批复用模型框架模板 |
| tests/ | 297 项 | 单元、集成、平台/后端、读取、数值回执、State、同步、绘图和发布回归；包含 fixture 与 smoke 脚本 | 三批都必须在现有测试体系中增加针对性反例 |
| docs/ | 96 项 | 历史审计、迁移记录、重构计划、实施台账和验收矩阵 | 本次新增唯一总计划；历史计划作为上下文，不作为当前运行 Authority |
| packs/ | 3 个直接子项 | artifact、competition、task 专项资源 | 不是本次新建第二套业务流程的地方 |
| config/ | 3 项 | 竞赛配置、文字审计模式和评审权重 | 仅在确有竞赛差异时使用，不因本次改造扩张 |
| assets/ | 2 项 | Figure 资产与图形资源 | 本次不改 |
| knowledge/ | 1 个直接子项 | Case Memory | 本次不改 |
| state/ | 1 项 | 仓库内项目状态示例 | 示例只作结构参考，不是新项目可直接复制的真实 State |
| legacy/ | 15 项 | 历史版本、旧工具与兼容材料 | 不进入默认执行链，不作为新初始化或调度依赖 |
| .github/workflows/ | 3 项 | CI、Optimization baseline、refresh-generated | 仓库文档和代码 PR 的远端生成与验收入口 |

### 1.2 活动规则与运行代码的分层

| 层次 | 关键文件 | 当前职责 | 本次边界 |
|---|---|---|---|
| 启动与固定来源 | SKILL.md、PROJECT_INSTRUCTIONS.md、AGENTS.md、core/bootstrap.yaml | 固定来源、启动范围、全局硬边界、网页/App 操作入口 | 只更新稳定导航和动作说明，不复制完整业务规则 |
| 路由与模块依赖 | core/workflow_router.yaml、core/module_manifest.yaml | 意图、模块顺序、runtime segment、gate 声明、模块输入输出 | 第三批在现有 Router 上补默认选问，不新建第二套路由 |
| 产物与阶段资格 | core/output_contract.yaml、core/workbook_schema.yaml | 框架、State、工作簿、脚本、Figure 和正式交付范围 | 第一批明确项目记录创建时点；第三批明确单问与全题 scope |
| 项目状态与恢复 | core/project_state.schema.yaml、core/state_transition_contract.yaml、scripts/runtime_assurance.py | revision、structured identity、批准、依赖、stale、generation、只读 State snapshot | 第一批复用现有 State 和 snapshot 语义，不另建并行状态机 |
| 运行时解析与读取 | scripts/resolve_runtime.py、scripts/resolve_workflow.py、scripts/reading_plan.py、scripts/read_stage.py | 当前动作解析、兼容规划、阶段读取计划和原文读取 | 默认入口继续使用 resolve_runtime；resolve_workflow 保持 legacy/stateless 兼容边界 |
| 项目写入与同步 | scripts/project_transaction.py、scripts/sync_project.py、scripts/project_snapshot.py | generation/read-set 事务、Artifact 发现、快照、Schema/Hash 与 stale 传播 | 第一批新增初始化编排；第三批增加通用 question scope |
| 数值代码与验收 | scripts/stage_code.py、scripts/stage_inputs.py、scripts/validate_code_delivery.py、scripts/validate_user_execution.py | 后端、源码 bundle、输入身份、代码交付、RUN_RECEIPT 和返回工作簿验收 | 第二批调整环境元数据必填性，保留数值证据资格 |
| 模型批准与后端 | core/model_approval_contract.yaml、core/user_execution_contract.yaml、scripts/validate_model_approval.py、scripts/project_solver_backend.py | 双重 Model Challenge、明确人工批准、项目级唯一后端和迁移 | 第二批只解耦环境信息；不重做后端选择 |
| Figure 与论文 | modules/04_figure_evidence.md、scripts/plot_backend.py、modules/05_writing、modules/06_review | 已验收数据绘图、论文写作、审查与终稿交付 | 第三批让单问 Figure 独立检查；不降低视觉/论文终审要求 |
| 模板与实例 | templates/model、templates/code/starter、templates/code/matlab、templates/code/hsk_pipeline | 规范框架生成、Python/MATLAB 入口、工作簿写入与验证 | 第一批复用框架生成器；第二批同步检查回执生产端 |
| 测试与维护 | tests/、.github/workflows/、scripts/generate_indexes.py | 行为回归、原生 MATLAB/LaTeX 和生成文件维护 | 仅新增对应反例，不手工维护生成索引 |

### 1.3 当前实际主流程

当前正式活动链可概括为：

**固定 Skill 来源与启动合同 → Router / Module Manifest → resolve_runtime → 项目 State 与 Artifact assurance → 读取当前阶段原文 → 对应业务 Module → resolver 返回的有序 gate → 代码交付 / 用户本地执行 / 返回工作簿验收 → 项目事务与同步 → Figure Evidence → 写作与终审。**

其中，读取计划、resolver 输出、文件存在和哈希一致都不自动等于模型正确、用户批准、数值 accepted 或图表视觉通过。正式交付仍只执行 resolver 当前返回的有序 pre_delivery_gates。

### 1.4 项目事实的当前所有权

| 事实 | 当前权威事实源 | 不可替代边界 |
|---|---|---|
| 当前模型语义、公式、变量、跨问依赖、论文结构与图表映射 | 项目根 模型论文框架.md | 作为项目工作记忆，不替代机器批准和数值真值 |
| revision、structured identity、Model Challenge/Human Approval 状态、artifact identity、stale、依赖和机器阶段状态 | state/project_state.yaml | 聊天摘要和框架文字不能自行授予批准或恢复 stale 资格 |
| 具体数值、质量门和实际运行事实 | 当前 accepted 主/深化工作簿及其 RUN_RECEIPT | 不能从代码、State 摘要或模型框架反推具体数值 |
| 跨项目方法、审批、执行、图表、写作和交付规则 | 固定提交的活动 Authority | 项目框架不能复制成另一份全局规则 |
| 仓库版本、源文件索引和 Manifest | Git commit、生成器及 GitHub refresh-generated | 不手工修改生成哈希或索引 |

---

## 2. 已有能力与本次改造的边界

### 2.1 第一方向：已有事务和框架生成，但缺少统一初始化编排

已核实：

1. AGENTS.md 和 core/output_contract.yaml 已规定 proposed_model_spec 形成后建立或更新项目根 模型论文框架.md。
2. scripts/instantiate_model_paper_framework.py 已能从 canonical 模板生成 compact/full 框架文本；它不负责生成 project_state.yaml。
3. core/project_state.schema.yaml 已定义 State 根结构和小问字段，subproblems 至少需要一个真实小问记录。
4. scripts/runtime_assurance.py 的 ProjectStateSnapshot 是只读快照；State 缺失会被表示为 unavailable，不会自动创建。
5. scripts/project_transaction.py 已支持 State 与伴随文件的可恢复事务、generation、expected_file_hashes、staged validators；tests/test_project_transaction_read_set.py 已覆盖“目标 State 原本不存在时，通过显式 absence read-set 初始化”。
6. 现有项目状态更新写入者包括 sync_project、semantic governance、code delivery、user execution、project backend、plot backend 和 case references 等；这些属于已有更新/选择动作，不等于一个统一的新项目初始化入口。

**判断：** 不能重造事务系统，也不能把初始化写进只读 resolver。缺少的是在 proposed_model_spec 之后，依据真实题目与已形成模型记录，协调框架和 State 的首次创建、部分缺失修复及安全恢复。

### 2.2 第二方向：项目后端和真实执行边界已存在，环境元数据被过度设为验收必填

已核实：

1. core/user_execution_contract.yaml 已规定一赛题一个项目级 Python/MATLAB 后端，主求解和 required 的分析入口继承同一后端。
2. Model Approval Brief 已承载具体求解器、依赖和未验证环境条件；没有必要新增一个环境审批 Gate。
3. Model Challenge 的检查项包含 selected_backend_capabilities_and_environment；后端选择依据包含可用环境和必要数值能力，但合同同时允许明确记录未验证条件。
4. canonical RUN_CONFIG 的必需字段不包含 solver_version 或 platform；solver_version 在历史兼容字段中另有定义。
5. scripts/validate_user_execution.py 的 configuration_map() 却把 solver_version 与 platform 放入通用工作簿必填集合，形成合同与消费者不一致。
6. Python/MATLAB 模板会把 solver_version、platform 等写入运行后 RUN_RECEIPT；这些值是实际执行事实，不是运行前的模型审批或代码交付授权。
7. MATLAB 数值模板除 usejava('jvm') / license('test','MATLAB') 检查外，还在路径规范化和 SHA-256 计算中实际使用 Java；仅删除前两条 assert 并不会消除 JVM 依赖。

**判断：** 应移出“用户必须提前证明本机环境”的阻断作用，但不能删除求解器数学能力审查、项目唯一后端、真实运行错误诊断、源码/数据身份和 full-fidelity 数值验收。

### 2.3 第三方向：已有显式小问作用域和 03B Gate，但默认选问与同步器仍偏全题

已核实：

1. scripts/resolve_runtime.py 已接受可选 question 参数和 CLI --question；runtime assurance 能按小问核对语义与工作簿证据。
2. core/workflow_router.yaml 已分开 primary_execution、analysis_execution 和 full_workflow_resume。
3. modules/03_result_analysis.md 已有 Analysis Necessity Gate；required 才生成独立 03B 入口，not_required 必须记录理由。不得重复建立第二个 03B Gate。
4. scripts/sync_project.py 的 synchronize() 目前只有 mechanism_question 这种专项参数，没有通用 question 参数。
5. scripts/project_snapshot.py 的 _question_names() 会合并 State 中登记的小问、问题目录和历史结果目录；sync_project 随后遍历这些小问建立快照。
6. sync_project 的 _formal_state_issues() 遍历全部 subproblems；_scope_artifact_issues() 对传入的全部快照检查脚本、工作簿和图表。
7. 因此，即使目标是 Q1 的 Figure，其他小问的缺失产物仍可能进入同一次正式同步检查。
8. runtime_assurance_contract 已规定 --question 的单问证据范围，以及 full_workflow 最终交付前必须检查全部已登记小问。

**判断：** 第三批重点是“默认选哪一问”和“单问同步实际检查哪些快照”，不是重新设计模型审批、03B 或全题终审。

### 2.4 已有历史计划和独立议题

| 当前仓库已有资料 | 本计划的处理 |
|---|---|
| docs/semantic_state_runtime_refactor_plan.md、docs/phase_f_transaction_writer_inventory.md | 作为现有事务机制的历史来源；本次复用，不重建 transaction engine |
| docs/project_solver_backend_redefinition_plan.md、docs/project_solver_backend_redefinition_p1_audit.md | 项目级唯一后端已形成独立政策；本次不重新设计后端选择/迁移 |
| docs/runtime_router_and_gate_simplification_refactor_plan.md | 作为历史路由/门禁审计参考；本次只处理默认选问和 question-scoped sync 的具体缺口 |
| docs/v10180_analysis_comparison_plan.md 与当前 modules/03_result_analysis.md | 多模型/多算法分析与现有 03B 必要性判断已有专门规则；本次不重复建设 |
| docs/v11_0_0_migration.md、docs/v11_rule_preservation_map.md | 保留 v11 固定来源、读取和迁移边界 |
| PR #326、#335、#336 | 当前仍为开放的旧基线文档 PR；其分支与当前 main 已分叉。本计划使用新文件路径，不覆盖它们，也不把旧分支视为当前源码 |
| PR #348 | 独立客户端试验资料，不与本次三个运行时方向混合 |
| Issue #352 | parameter-only / embedded_parameters 输入身份问题，作为独立技术议题，不塞入本次三批主流程改造 |

---

## 3. 第一批：助手接管项目记录的创建、更新与恢复

### 3.1 目标行为

新项目的项目记录创建时点沿用现有合同：proposed_model_spec 已形成后，助手建立当前项目框架和 State。纯审题阶段只维护 Problem Contract，不为满足 Schema 而提前生成空 State 或虚构小问模型。

推荐链路：

**题面与附件 → Module 01 冻结 Problem Contract → Module 02 形成 proposed_model_spec → 助手建立真实项目框架与 State → Model Challenge → Model Approval Brief → 等待用户明确批准。**

若创建时 Model Challenge 尚未完成，State 如实记录 pending；若双重 Challenge 已真实通过，才记录 passed；用户尚未明确批准当前 semantic_revision 和 validated semantic_identity_hash 时，human_model_approval_status 仍为 pending。创建文件不能代替批准。

### 3.2 计划修改的文件与职责

| 文件 | 当前职责 | 计划修改摘要 | 处理方式 |
|---|---|---|---|
| core/output_contract.yaml | 定义项目框架、State 路径和产物创建时点 | 明确框架与 State 的配套创建时点、项目记录所有权、首次创建与部分修复的边界 | 修改唯一 Authority，不在入口重复字段清单 |
| core/runtime_assurance_contract.yaml | 只读 State snapshot、Hydration、Artifact assurance、读取计划 | 明确 State 不存在、State 损坏、事务待恢复、框架缺失和部分记录缺失的不同处理；resolver 继续只读 | 修改规则，不让 resolver 自动写文件 |
| scripts/initialize_project.py（拟新增） | 当前未发现统一的项目初始化编排入口 | 协调真实题目信息、Problem Contract、框架生成、State 构造、Schema/框架验证和事务提交；可提供首次初始化与可证明的部分修复动作 | 新增单一编排器，不新增第二个事务引擎 |
| scripts/instantiate_model_paper_framework.py | 从 canonical 模板生成框架文本 | 优先复用现有 instantiate() 返回文本的接口；若保留直接输出项目文件的 CLI，补充防止意外覆盖的保护 | 原则上不重写模板生成逻辑 |
| scripts/project_transaction.py | generation/read-set/事务日志/恢复 | 初始化器复用 commit_project_state() 和现有 expected_file_hashes；只有测试发现缺少必要原子性时才改事务实现 | 优先不改 |
| scripts/validate_project_state.py、scripts/validate_model_paper_framework.py | 分别验证 State 与框架 | 为初始化器提供 staged validators，确保提交前结构和身份检查 | 复用现有验证器 |
| AGENTS.md、PROJECT_INSTRUCTIONS.md、scripts/README.md | Agent/网页/App/脚本入口说明 | 只增加“何时创建、缺失时如何恢复、无写权限时如何说明”的导航 | 最后更新，引用 Authority |
| tests/ | 现有 State snapshot、事务、框架和 writer 测试 | 新增初始化/恢复集成测试，扩展已有事务和缺失 State 测试 | 新增 tests/test_project_initialization.py（拟） |

### 3.3 初始化与恢复规则

1. **首次创建：** 只在 proposed_model_spec 已形成且真实题号、问题映射、分类、模型候选和依赖可用时创建；不得从 state/project_state.example.yaml 复制示例竞赛、示例模型或 placeholder。
2. **真实初始状态：** 按当前事实填写 project、requirements、decisions、subproblems、variables、paper_framework、artifacts、risks 和 next_gate；未发生的审批、执行、accepted 和图表通过状态保持 pending / not_applicable。
3. **配套提交：** 先生成完整框架文本与 State 候选，再使用一个 guarded transaction 同时提交；读取集合明确声明 State、框架原先不存在，防止覆盖已存在文件。
4. **现有项目续做：** 优先读取 current 框架、State 和 accepted 工作簿；只更新发生变化的事实，不重建或清空整个项目。
5. **部分缺失：** 只有当其他当前权威来源足以无歧义恢复缺失记录时才修复；无法恢复批准、语义身份或历史执行证据时，保留待核状态并说明缺口，不从聊天摘要推断通过。
6. **事务中断：** 遵守现有 prepared journal 的显式恢复规则；先恢复并重新取得快照，不沿用旧 read-set，也不让 resolver 偷偷恢复。
7. **没有可写工作区：** 助手可维护会话内的临时记录并继续已授权分析，但必须明确它不是持久化 State；不要求用户额外运行本地 checker。
8. **不新增当前问字段：** 当前问仍由已有 State、阶段状态、Artifact 和依赖证据推导；除非后续反例证明无法可靠推导，否则不增加人工维护的 current_question。

### 3.4 第一批验收

| 场景 | 通过标准 |
|---|---|
| 只有题面和附件，尚在审题 | 不创建空白 State 或伪造框架；Problem Contract 可继续 |
| proposed_model_spec 已形成 | 一次性建立真实框架和 State，Schema 有效，初始批准/执行状态准确 |
| 已有框架、State 不存在 | 不直接覆盖；检查项目是否属于新项目或历史项目缺失 |
| State 存在、框架缺失 | 仅在当前语义身份与批准证据可验证时恢复框架 |
| 框架存在、State 部分缺失 | 只补可证实字段；无法证明的批准和数值资格保持未确认 |
| 已存在事务 journal | 明确恢复后重新读快照，不隐式覆盖 |
| 重复执行初始化 | 幂等；不重复生成、不覆盖用户当前记录、不改变 accepted 身份 |
| 写入中断或并发修改 | 使用现有事务恢复/冲突机制；不能留下只写一半的框架/State 组合 |

---

## 4. 第二批：从模型审批与数值验收中移出用户环境证明

### 4.1 目标行为

把“模型/算法是否具有数学适用性”与“用户当前机器是否已经安装某个软件包或取得某个 License”分开。

- Model Challenge 继续检查求解器能力、数学保证、计算规模、全精度可实现性和必要依赖。
- 用户本地包、Toolbox、软件版本或 License 尚未验证，可以作为明确的未验证条件记录，不单独阻断候选模型讨论或代码准备。
- 代码交付前不要求用户提供环境截图、版本清单或本地预检证明。
- 用户仍负责真实 full-fidelity 执行；实际缺包、License 不可用、运行错误或数值失败发生时，按真实错误排查，不能把未知状态写成已验证。
- 项目根唯一求解后端、solver、代码/数据身份、停止条件、数值质量、no-degradation 标志和用户执行所有权全部保留。

### 4.2 计划修改的文件与职责

| 文件 | 当前职责 | 计划修改摘要 | 处理方式 |
|---|---|---|---|
| core/model_approval_contract.yaml | 两个独立 Model Challenge pass 与 Approval Brief | 将“环境能力”明确拆成求解器数学能力/全精度可计算性与本机安装状态；未验证安装事实可记录，不作为模型正确性自动否决 | 修改语义边界，不删 Challenge |
| core/user_execution_contract.yaml | 项目唯一后端、RUN_CONFIG/RUN_RECEIPT、用户 full-fidelity 执行 | 明确环境信息是可选运行事实/未验证条件；保持 solver_backend、solver、数据身份和执行政策 | 修改唯一执行 Authority |
| core/workbook_schema.yaml | 工作簿结构与运行配置表 | 核对 RUN_RECEIPT 字段是否被 Schema 额外声明为必填；若没有字段级要求，不为此机械升级 Schema | 仅在真实字段合同需要时修改 |
| scripts/validate_user_execution.py | 返回工作簿配置与 RUN_RECEIPT 验收 | 将 platform、solver_version 从通用必填集合移为可选事实；缺失不阻断，其余核心字段与绑定仍严格校验 | 主要实现点 |
| templates/code/starter/ | Python 主求解、分析与对照示例 | 保留可获得时的 solver_version/platform 输出；缺失时不制造占位值，不将其作为运行前配置要求 | 同步 writer |
| templates/code/matlab/ | MATLAB 主求解、分析与对照示例 | 保留可获得的 MATLAB 版本/平台信息；运行前不要求用户先证明环境 | 同步 writer |
| templates/code/hsk_pipeline/ | Python 工作簿写入与公共验证 | 检查通用 writer 是否对可选回执字段施加隐含必填约束；只修改真实消费者 | 按影响面核验 |
| scripts/validate_code_delivery.py | 代码静态检查、配置和源码 bundle 交付 | 审查是否仍存在与本机环境证明绑定的阻断；若无，不为形式统一而改写 | 以审计为主 |
| AGENTS.md、PROJECT_INSTRUCTIONS.md、scripts/README.md | 操作边界与用户执行说明 | 删除要求用户提前证明平台/版本的说明，保留真实运行依赖和错误报告 | 最后同步导航 |
| tests/ | 执行回执、后端、模板、MATLAB 静态检查 | 新增缺失 platform/solver_version 的有效回执对照，同时保留错误哈希、错误 backend、降级标志和数值失败的阻断测试 | 扩展现有测试 |

### 4.3 必须保留与不能混淆的字段

| 类别 | 字段/行为 | 目标 |
|---|---|---|
| 项目策略 | execution.solver_backend、selection_reason | 仍是全项目唯一 Python/MATLAB 选择；缺失不默认 Python |
| 实际求解 | solver、tolerance、iteration_or_time_limit、random_seed | 继续按现行阶段和算法要求验收 |
| 身份证据 | code_sha256、code_bundle_sha256、data_sha256、适用的 auxiliary input 和 primary_workbook_sha256 | 必须保持当前来源绑定 |
| 执行事实 | actual_stop_reason、repetitions_or_scenarios、grid_or_time_range、fallback_used | 继续记录和核验；不能以代码计划值替代实际执行 |
| 执行所有权 | execution_owner=user、execution_profile=full_fidelity、所有 allow_* 降级标志为 false | 继续严格要求 |
| 可选环境元数据 | solver_version、platform、matlab_release 等 | 有则保留；没有不单独阻断；不得写虚假占位 |
| 运行时失败 | 缺少真实依赖、License、文件权限或运行失败 | 仍如实报告；不能用“环境未核验”伪装成功 |

历史 RUN_CONFIG 的兼容必填字段与返回工作簿中的运行后元数据是两个不同对象。本批首先调整的是工作簿 RUN_RECEIPT 的通用验收必填性；不应顺手删除历史配置协议的兼容读取要求。

### 4.4 MATLAB JVM / License 的专门边界

当前 MATLAB 模板在入口处检查 JVM 和 MATLAB License；同时，路径规范化与 SHA-256 helper 实际使用 Java 类。

因此有两种不同修改，不能混为一谈：

- **最低范围：** 不要求用户在模型审批或代码交付前提供 JVM/License 证明；真实 MATLAB 执行时仍可能因运行条件不足而明确失败。模板若保留实际 Java 调用，就必须如实说明它仍依赖 JVM。
- **扩大范围：** 若目标是彻底取消 JVM 依赖，必须替换路径规范化、文件身份与 SHA-256 实现，并用同一组文件对 Python/MATLAB 摘要进行字节级一致性测试。仅删除 usejava('jvm') 检查不算完成。

MATLAB License 是实际运行前提，不应被描述成可有可无；本次只移出提前证明要求，不承诺无 License 仍能运行。

### 4.5 第二批验收

1. 新回执缺少 platform、solver_version，但其他必需字段和身份/数值证据完整时，可以通过相应字段检查。
2. 新回执提供 platform、solver_version 时，保留实际值；非法类型或重复键仍按对应规则处理。
3. code_sha256、bundle、data_sha256、backend、primary workbook 绑定错误仍必须失败。
4. actual_stop_reason、执行规模、fallback 和 no-degradation 证据缺失或不一致仍必须失败。
5. 历史工作簿继续可读，不要求批量重跑或重写历史回执。
6. Python 与 MATLAB 两端输出字段保持兼容；MATLAB JVM/License 的真实依赖不被虚构为已验证。
7. 用户仍是数值代码执行者，助手不得代跑或自动降级。

---

## 5. 第三批：默认逐问调度与单问 Figure 独立验收

### 5.1 目标行为

用户只说“进入 03A”或“继续”时，助手能够根据当前项目记录和真实证据选择当前小问，而不是要求用户每次重复提供题号，也不是把所有小问的缺失产物一起检查。

**建议的选问优先级：**

1. 用户明确指定的 Qn 优先；显式指定不能绕过该问的上游依赖。
2. 未指定题号时，如果 State/Artifact 中只有一个明确等待用户执行、返回验收、03B 或当前 Figure 动作的小问，继续该问。
3. 没有唯一待续动作时，按 Problem Contract 的题目顺序，选择依赖已满足且当前阶段具备资格的第一道小问。
4. 若多个小问同时处于无法区分的等待状态，或依赖关系形成未解决冲突，返回明确歧义/等待原因，不随机选问。
5. 不增加人工维护的 current_question State 字段；当前问由现有阶段状态、执行回执、工作簿、Figure 证据和 typed dependency 推导。

### 5.2 单问执行链

**Q1 进入 03A → Q1 主代码交付 → 用户运行并返回主工作簿 → Q1 主结果验收 → 现有 Analysis Necessity Gate → required 时独立 03B 代码/工作簿验收，not_required 时记录理由 → Q1 Figure Evidence → Q1 当前问完成 → 选择下一道依赖满足的小问。**

需要区分三个状态：

- 只交付绘图脚本：进度只到脚本交付，不标记 Figure Evidence 已完成。
- 结果图已经本地渲染：仍需核对当前 accepted 来源、实际图像与图表证据链。
- 当前问所需图表证据及视觉/语义审查完成：才可把当前问推进到下一问。

本批不改变 modules/04_figure_evidence.md 的科研图设计、真实数据来源、渲染、视觉审查和论文引用要求。

### 5.3 单问与全题的边界

| 检查对象 | 单问 code/results/figures | 全题论文/终审/提交 |
|---|---|---|
| 当前问 State 与模型身份 | 检查目标 Qn | 检查所有相关小问 |
| 上游依赖 | 检查目标问实际需要的 typed dependency closure | 检查整题依赖与综合结论 |
| 无关小问的工作簿/绘图文件 | 不得阻断当前 Qn | 按全题最终要求检查 |
| 项目级唯一 backend | 仍是全项目不变量 | 仍是全项目不变量 |
| 项目级共享预处理 | 按当前 preprocessing_decision 检查共享数据事实 | 仍需检查全部下游使用范围 |
| 03B 必要性 | 只执行当前问已有 Analysis Necessity Gate | 每道需要的问都必须有 accepted 03B 或有理由的 not_required |
| 最终论文、PDF、提交包 | 不因单问 Figure 资格自动通过 | 仍按全部登记小问、论文与提交证据检查 |

### 5.4 计划修改的文件与职责

| 文件 | 当前职责 | 计划修改摘要 | 处理方式 |
|---|---|---|---|
| core/workflow_router.yaml | 任务意图、runtime segment、阶段边界与 gate 顺序 | 定义默认选问优先级、继续当前等待点和完成当前问后的推进语义 | 作为调度规则 Authority |
| core/runtime_assurance_contract.yaml | 项目 State 快照、question scope、依赖诊断与最终全题资格 | 明确单问检查范围、必要上游闭包、全题 finalization 边界 | 作为证据范围 Authority |
| core/output_contract.yaml | code/results/figures/docx/latex/submission 产物资格 | 明确哪些 scope 支持单问检查，哪些 scope 必须全题 | 不改变各阶段真实产物要求 |
| scripts/resolve_runtime.py | 当前默认状态感知 Resolver，已有可选 --question | 未显式题号时按 State 与证据选择当前问，并把所选问传入已有阶段/门禁规划 | 主要调度实现点 |
| scripts/sync_project.py | 项目同步 CLI 与正式交付编排 | 增加通用 question 参数/作用域；保留现有 mechanism_question 兼容入口；单问检查不遍历无关小问 | 主要阻塞修复点 |
| scripts/project_snapshot.py | 按小问发现源码、工作簿、绘图与 Figure 快照 | 支持只捕获目标问及必要上游依赖；项目级共享输入仍按真实范围核验 | 配合同步器 |
| scripts/resolve_workflow.py | 旧无状态兼容解析器 | 原则上不承载新默认调度；只有兼容测试要求时作窄幅适配 | 保持 legacy/stateless |
| modules/03_result_analysis.md | 现有 03B 必要性与执行规则 | 原则上不重写；仅在阶段交接文字缺失时做引用性澄清，不新增第二个 Gate | 保留现有 Authority |
| modules/04_figure_evidence.md | 每问结果图、Figure Evidence、渲染和审查 | 保持原规则；同步单问调度如何提供目标问的合法证据 | 不降低图表审查 |
| PROJECT_INSTRUCTIONS.md、AGENTS.md、RUNTIME_ROUTER.md | 用户与 Agent 操作入口 | 说明“进入 03A / 继续”如何选问、显式 Qn 如何覆盖、单问与全题边界 | 只引用 Router/Runtime Authority |
| tests/ | Router、runtime resume、sync、snapshot、Figure routing 回归 | 新增三问依赖夹具与 question-scoped sync 反例 | 扩展现有测试，不新建独立验收体系 |

### 5.5 第三批验收

采用三问项目夹具：

- Q1：已锁模，可执行 03A。
- Q2：依赖 Q1 的 accepted result。
- Q3：不依赖 Q1/Q2 的独立小问。

必测：

1. 三问均已锁模，只说“进入 03A”，首轮只交付 Q1 主代码。
2. Q1 主工作簿 accepted 后，required 与 not_required 两条 03B 分支均正确。
3. Q1 的 Figure 检查不因 Q2 缺少工作簿或绘图脚本而失败。
4. Q2 在 Q1 结果尚未 accepted 时等待；Q1 accepted 后才允许进入 Q2。
5. Q3 的独立性按真实依赖处理，不把 Q2 的无关结果错误传播给 Q3。
6. 显式指定 Q2 时仍检查 Q2 的真实上游依赖，不能以题号覆盖依赖门。
7. 多个问题同时等待时返回歧义，不随机选一个。
8. 当前问只交付 Figure 脚本时，不把脚本交付写成 Figure Evidence 完成。
9. 当前问 Figure Evidence 完成后，才允许默认推进下一问。
10. 全题 LaTeX、终审与 submission 仍要求所有登记小问满足 validated_results 和相应最终证据。
11. 既有 State snapshot、read-set、stale 传播和并发写入保护不因 question filter 被绕过。

---

## 6. 三批统一实施顺序与 PR 切分

### 6.1 当前交付：唯一总计划文档

本 PR 只新增本文件。目标是让用户先审查结构、文件范围、现有能力、兼容边界和测试矩阵。该 PR 不修改运行行为，不合并任何实现。

### 6.2 后续三个单主题 PR

| 顺序 | 主题 | 主要文件面 | 先决条件 | 退出条件 |
|---|---|---|---|---|
| PR-A | 项目记录初始化与恢复 | Output/Runtime Authority、初始化编排器、框架/State validators、事务复用、初始化测试 | 用户审查并批准本计划；刷新最新 main 与重叠 PR | 新建、续做、部分修复、事务恢复和重复初始化全部通过 |
| PR-B | 执行环境信息解耦 | Model Approval、User Execution、Workbook、回执验收、Python/MATLAB writer 与测试 | PR-A 完成并核对主干；环境元数据与实际运行事实边界冻结 | 缺少 platform/solver_version 不再单独阻断；其余身份/数值/执行边界不回归 |
| PR-C | 默认逐问调度与单问同步 | Router、Runtime Assurance、Output、resolve_runtime、sync_project、project_snapshot 与集成测试 | PR-A 完成；PR-B 完成或其影响面已冻结；三问测试夹具固定 | Q1 可独立完成当前问 Figure；依赖问正确等待；全题 finalization 仍严格 |

每批从最新 main 创建独立分支；写入前重新检查开放 PR、相同 Authority 的实际差异和生成工作流。若后续 PR 修改相同权威文件，按治理要求串行重基，不让不同分支并行改写同一合同。

### 6.3 版本与迁移

- 本计划 PR 只增加 docs，不升级 Skill 版本。
- 实现 PR 是否需要修改 Project State Schema、Workbook Schema、RUN_RECEIPT 协议或 CLI，必须由实际差异决定。
- 仅增加可选 question 参数且保持旧默认兼容，和改变既有默认选问/阻断范围，不应未经分析就按同一版本等级处理。
- 历史 State、工作簿和批准不能因为新默认调度而批量作废。
- 若出现破坏性 Schema/CLI/目录变化，必须另有迁移说明和兼容窗口；不得为完成三批而顺手升级无关协议。

---

## 7. 跨批次非回归底线

以下约束贯穿三个 PR，不得由“体验简化”削弱：

1. 固定 Skill commit、全文读取、阶段换问换章重新取得适用原文的规则继续有效。
2. Problem Contract、两个独立 Model Challenge、用户明确批准当前语义身份和 Model Approval gate 保留。
3. 项目根仍只允许一个 Python/MATLAB 数值后端；所有小问主求解和 required 分析入口继承它。
4. 真实赛题数值代码仍由用户本地 full-fidelity 执行；助手不得导入、运行或间接执行题目专属求解代码。
5. 不允许静默降采样、粗网格、缩短时域、减少场景/重复、放宽容差或替换求解器。
6. 代码、数据、辅助输入、RUN_RECEIPT、accepted workbook 和模型身份的绑定继续严格。
7. 03A 只负责当前主计算及其内在数值有效性；accepted 后的 03B 仍由现有 Analysis Necessity Gate 条件激活。
8. not_required 需要非空理由，且不等于稳健性/稳定性已通过。
9. Figure Evidence 只消费当前合法的已验收来源；脚本存在不等于图已渲染或人工审查通过。
10. 单问 scope 不得削弱项目级唯一后端、共享预处理和 typed upstream dependencies。
11. 整题论文、终审和提交仍检查全部必需小问及跨问结论。
12. resolver、reading plan、sync PASS、文件存在或 hash 一致均不得自动提升为数学正确、人工批准或数值 accepted。

---

## 8. 综合验收矩阵

| 维度 | 必测正例 | 必测反例 |
|---|---|---|
| 项目初始化 | proposed_model_spec 后创建框架+State，事务完整提交 | 纯审题阶段创建空 State；复制示例值；覆盖现有项目 |
| 项目恢复 | 单个缺失文件能从当前权威证据安全恢复 | 从聊天摘要恢复批准、从框架数字恢复 accepted 数值 |
| 事务 | read-set、generation、staged validator、journal recovery 正常 | 并发修改、文件缺失/替换、事务中断后旧快照继续提交 |
| Model Approval | 未批准时状态保持 awaiting_model_approval | 以环境未知、文件存在或模糊“继续”伪造批准 |
| 环境元数据 | 缺少 platform/solver_version 但其余证据完整可验收 | 缺 code/data hash、错误 backend、降级标志为 true 却被放行 |
| MATLAB | 保留真实可用的运行事实，错误能定位 | 删除 JVM assert 后仍声称无 JVM 依赖 |
| 逐问选择 | 明确 Qn、唯一待续问、首个可执行问均可正确选择 | 多个 pending 时随机选择、显式 Qn 绕过上游依赖 |
| 单问同步 | Q1 figures 只检查 Q1 和必要依赖 | Q2 缺工作簿导致 Q1 figures 阻塞 |
| 03B | required 和 not_required 两条现有分支正确 | 新建第二套 03B Gate，或把 not_required 写成鲁棒性通过 |
| Figure | 脚本交付、实际渲染、视觉审查状态分开记录 | 仅有 qX_plot 文件就标记 Figure Evidence accepted |
| 全题收尾 | 所有必需小问证据齐备后进入终审 | 单问 Q1 通过就跳过 Q2/Q3 的全题最终检查 |
| 兼容性 | 历史 State/Workbook/RUN_RECEIPT 可读 | 为删字段要求历史项目批量重跑 |

---

## 9. 当前不纳入本计划的事项

### 9.1 Issue #352：parameter-only / embedded_parameters

该问题涉及 RUN_CONFIG 输入身份、空 data_paths、参数规范化摘要、Python/MATLAB 跨后端一致性、回执和所有输入文件消费者。它是独立的数据身份协议改造，不属于“项目记录初始化、环境元数据、逐问调度”的直接必要范围。

后续若使用没有外部数据文件的 D-Q1 做 03A 正式测试，应先按 Issue #352 单独实施和验收；本计划的三问调度测试先使用有真实输入文件的测试项目，不用 placeholder 文件绕过输入身份。

### 9.2 本次不重构的现有能力

- v11_full_read 与 fixed-commit 全文读取；
- Model Challenge / Human Model Approval；
- 项目级唯一求解后端与历史 backend migration；
- Analysis Necessity Gate 与多模型/多算法 03B 比较；
- 项目级预处理与 question_local 数据处理；
- Figure Evidence 的视觉/语义审查；
- LaTeX 模板、PDF 逐页审查和 submission package；
- Case Memory、Review Receipt、Claim Consumption 与其他独立专项 Gate。

---

## 10. 用户审查项与实施前停止点

请重点审查以下设计决定：

1. **项目记录创建时点：** 是否确认在 proposed_model_spec 形成后，由助手一次性创建框架和 State；纯审题阶段不创建正式 State。
2. **恢复边界：** 是否确认缺失文件只在当前证据可恢复时修复；批准、数值 accepted 和历史执行身份绝不从聊天摘要推断。
3. **环境元数据：** 是否确认 platform、solver_version 缺失不再单独阻断返回工作簿验收，但代码/数据身份、实际停止原因、full-fidelity 与数值质量仍严格。
4. **JVM 处理：** 是否只移出提前环境证明，暂时保留 MATLAB 模板的真实 Java 运行依赖；还是要求第二批同时彻底取消 JVM，并承担 SHA-256/路径实现替换与跨后端一致性测试。
5. **默认选问优先级：** 是否确认“显式 Qn > 唯一待续小问 > 依赖已满足的题目顺序首问”；多个 pending 无法唯一判断时不随机选问。
6. **单问同步范围：** 是否确认当前问 + 必要上游依赖 + 项目级共享事实，而不是所有已登记小问；docx/LaTeX/终审/submission 仍按全题范围。
7. **当前问完成条件：** 是否确认只交付绘图脚本不算 Figure Evidence 完成；应区分脚本交付、实际渲染和必要视觉/语义审查。
8. **独立问题：** 是否确认 Issue #352 不并入本次三批 PR。

**停止条件：** 用户审查前不修改三个方向的活动规则或业务代码。用户批准计划后，仍须从当时最新 main 重新核对 Bootstrap、治理规范、开放 PR、权威源与实际差异，再形成各批单独的修改简报和实现 PR。

---

## 11. 本次结构核查范围与证据状态

本计划基于固定提交的目录清单、活动入口、相关 Authority、业务 Module、实现脚本、模板、测试名称与既有历史计划进行结构盘点。已核对的重点源码包括：

- 项目记录：AGENTS.md、core/output_contract.yaml、core/project_state.schema.yaml、scripts/runtime_assurance.py、scripts/instantiate_model_paper_framework.py、scripts/project_transaction.py、scripts/validate_project_state.py。
- 环境与回执：core/model_approval_contract.yaml、core/user_execution_contract.yaml、core/workbook_schema.yaml、scripts/validate_user_execution.py、scripts/validate_code_delivery.py、Python starter 与 MATLAB 数值模板。
- 逐问调度：core/workflow_router.yaml、core/runtime_assurance_contract.yaml、scripts/resolve_runtime.py、scripts/resolve_workflow.py、scripts/project_snapshot.py、scripts/sync_project.py、modules/03_result_analysis.md、modules/04_figure_evidence.md。
- 现有回归：State snapshot、transaction read-set、transactional writers、router、runtime resume、user execution、sync project、solver backend end-to-end 和 Figure routing 测试。
- 既有计划：semantic/state runtime、transaction writer inventory、runtime router/gate simplification、project backend redefinition、03B comparison、v11 migration。

本次没有运行 resolver、checker、unittest、MATLAB、真实赛题代码或网页/App 端到端试验。目录/源码读取可以支持结构判断，但不等于三个改造已经实现、数学正确或通过正式 CI。后续正式验收只认最终 PR head 的 GitHub Actions 与实际产物。

