# 数学建模 Skill 分阶段读取与执行衔接重构计划

> 编制日期：2026-10-18（北京时间）；实施进度更新：2026-10-22。P0—P3 已完成，P4 的实现与实际验收记录见 §12。
> 本文是维护计划，不是运行时 Authority，不进入默认加载链。§0 的版本、SHA 与“本次”描述保留最初计划编制轮的快照；后续工作包按各自简报和当前来源实施，阅读计划本身不代表授权。
> 最初计划交付保持 v10.20.4；P3 已合并 v10.22.0，本轮获授权的 P4 目标为 v10.23.0，其正式验收和合并结果以关联 PR 为准。

## 0. 基线、修改简报与阅读方式

| 项目 | 编制时事实／本次边界 |
|---|---|
| 仓库 | Vexushi1/mathmodel-skill，默认分支 main |
| 当前 Skill | v10.20.4 |
| main commit | 95129dd4ee918c4b2f276eb48f8c05826a7e6d40 |
| main tree | 59106c8425886da13eeb276563763ea735f0ed26 |
| 最近修改 | PDF 逐页检查归助手并同步 LaTeX 流程，PR #270 |
| 编制时未合并 PR | 查询为空；后续实施前必须重新查询 |
| 修改主题 | 固定发布版本下，长对话中的规则漏读、条件漏触发、凭摘要／记忆执行，以及 Module 06 容量与维护问题 |
| 本次等级／目标版本 | docs，不升级版本；未来实施版本按最终兼容性确定 |
| 本次分支 | docs/stage-reading-execution-refactor-plan |
| 本次源文件 | 仅本文件；受管索引／MANIFEST 由 GitHub 按实际差异生成 |
| 直接目标 | 确定业务顺序、读取操作循环、重构职责、实施步骤、验收、兼容与回滚，并给出立即可用的全局工作指令 |
| 明确不做 | 不修改活动契约、代码、测试或模板；不拆 Module 06；不改审批／用户执行职责；不发布版本 |
| 禁止手工编辑 | MANIFEST.sha256、SKILL_FILE_INDEX.md、TEMPLATE_INDEX.md、HSK 两个兼容索引及其他生成产物 |
| 兼容要求 | 现有项目、State、Workbook、CLI、审批身份、数值后端和正式交付接口保持不变 |
| 本次验收 | 只读来源核对、计划独立审阅、diff 检查、GitHub 文档／生成检查；不是重构功能验收 |
| 本次回滚 | 关闭未合并计划 PR；合并后如需撤销，通过 revert PR 撤回文档和关联生成结果 |

先看 §1、§3、§4，可了解问题和目标操作；推进开发看 §7—§12；直接配置 GPT 看 §13。后续实施者应先核对新的 main，不能把本页 SHA 当作永久最新版本。

## 1. 要解决什么，哪些事情保持原样

### 1.1 用户实际遇到的问题

用户发布一个固定版本，竞赛期间不再改仓库。ChatGPT 通过 GitHub 读取它，最初可能读过部分内容，但进入绘图、下一问、下一章或长对话后，可能只凭印象和压缩摘要继续。结果是章节细则没有重新取读，命题／算法等条件规则未激活，图表要求没有完整落实。

因此，重点不是“仓库更新后怎样刷新”，也不是 GPT 型号能否一次容纳整个仓库，而是每次实际工作前，适用正文有没有完整送到模型可用的上下文中，之后有没有对照成果落实。

### 1.2 本次建议的结构变化

把“由助手临时判断该翻哪些文件”整理为一条可追踪的操作链：

~~~text
确认当前阶段和范围
→ 从同一套现有路由／写作阶段定义定位适用规则
→ 取得规则正文，补齐适用上下文和条件分支
→ 读取当前项目事实
→ 完成当前动作
→ 对照实际成果检查，并执行原有适用门禁
→ 更新项目工作记忆，进入下一阶段或停在原有等待点
~~~

这里的“完整”指当前动作必需的规则及条件补读完整，不要求每一步全读仓库。最终全文审查仍须覆盖所有实际适用范围，不能用分阶段读取作为抽样理由。

### 1.3 不变的底线

- 不删减数学、数值、绘图、写作、审查和交付标准。
- 不让用户逐章提醒助手读规则，不增加“已读确认表”、逐阶段批准或本地 checker 操作。
- 不用读取记录、来源 hash、规划输出或脚本退出码，代替实际执行、数学判断、图形审阅或用户批准。
- 不另建一套工作流、项目状态、门禁列表或正文质量标准。
- 保留原有双重模型审查、Human Model Approval、用户实际数值执行、助手返回验收与 PDF 逐页检查。
- 现有项目规则版本可固定；项目工作簿、图表、批准、stale 和论文事实仍核对当前材料。

## 2. 当前实现核查：已有能力与实际缺口

以下链接固定到编制基线；实施时还需读取新 main 的对应内容。

| 来源 | 已有事实 | 重构要处理的缺口 |
|---|---|---|
| [SKILL.md](https://github.com/Vexushi1/mathmodel-skill/blob/95129dd4ee918c4b2f276eb48f8c05826a7e6d40/SKILL.md#L13)；[bootstrap](https://github.com/Vexushi1/mathmodel-skill/blob/95129dd4ee918c4b2f276eb48f8c05826a7e6d40/core/bootstrap.yaml#L34) | 入口指向 resolver；bootstrap 已要求先 read_now，再处理 conditional，load_order 是兼容资源清单 | SKILL 摘要仍写“最小 load_order”，需原位统一，防止把清单当作当前已经读完 |
| [runtime assurance](https://github.com/Vexushi1/mathmodel-skill/blob/95129dd4ee918c4b2f276eb48f8c05826a7e6d40/core/runtime_assurance_contract.yaml#L279) | 已有文件 hash、行范围、上下文、选择失败回退、缺源报错和实际读取指标边界 | 契约描述“应该取得什么”，没有使 ChatGPT 自动取得正文 |
| [reading_plan.py](https://github.com/Vexushi1/mathmodel-skill/blob/95129dd4ee918c4b2f276eb48f8c05826a7e6d40/scripts/reading_plan.py#L139) | SourceReader 返回路径、hash、selector、ranges、字节数和回退原因 | Python 为计算范围读过文件，不代表模型收到这些规则正文；目前 describe 不直接交付正文 |
| [writing runtime](https://github.com/Vexushi1/mathmodel-skill/blob/95129dd4ee918c4b2f276eb48f8c05826a7e6d40/core/writing_runtime_contract.yaml#L233) | 已有逐阶段 read_now → write_now → gate、逐问闭合、能力 preflight、摘要后写 | 需要让即时取读成为具体操作；不能再加一套平行章节顺序 |
| scripts/resolve_runtime.py；scripts/resolve_workflow.py | resolver 输出规划、pause、assurance 与门禁元数据 | 命令输出 YAML 不等于已经执行所有门；available_after_plan 不等于产物已 accepted |
| 模型论文框架.md；state/project_state.yaml；accepted 工作簿 | 分别负责语义工作记忆、机器状态／身份、数值事实 | 不能把三者缩成一份聊天摘要，也不能从框架概述抄出未经工作簿核对的数值 |
| modules/04_figure_evidence.md；Protocol §13.0 | 已有 Figure Authority、条件资源、预登记到入文交接 | 新设计不能套用 style-only 窄读；共享／待定图应在逐问写作前被完整盘点 |
| modules/06_review_delivery.md；相关测试 | 已分 draft/final 两个消费时机，规则引用业务 Authority | 同一入口已接近自设预算，需按职责拆，保留全部检查而非只切文件 |

现有窄读覆盖项目同步、返回结果核验、部分绘图和 CUMCM 逐阶段写作；混合意图、不明确范围和未覆盖路径会保守全量回退。普通模型设计／求解等不能声称已经拥有同等精细的逐阶段取读。

### 2.1 三种“完成”必须分开

| 层次 | 能证明什么 | 不能据此推出什么 |
|---|---|---|
| 读取计划已形成 | 已定位应读来源和条件 | 模型已经收到、理解或落实正文 |
| 工具已返回完整来源 | 返回文本可绑定到指定文件／范围，已处理截断 | 数学正确、图形合格、用户批准或门禁通过 |
| 动作与适用检查完成 | 有当前产物、证据和实际审查结果 | 未执行的其他阶段也已经完成 |

assurance.status 为 pass 不能泛化成全流程 PASS；内部结构／身份校验也不能证明用户真的说过批准。所有结论都限定在实际证据范围内。

### 2.2 “重”的事实基线

| 文件 | 当前 UTF-8 字节数 | 含义 |
|---|---:|---|
| modules/06_review_delivery.md | 15,998 | 距仓库严格小于 16,000 的测试约束仅剩极小余量 |
| core/writing_runtime_contract.yaml | 35,875 | 阶段组织与能力激活，不宜另抄一份 |
| modules/05_writing/paper_writing_protocol.md | 82,115 | 普通写作细则，应按实际章节消费 |
| core/writing_reasoning_contract.yaml | 111,296 | 复杂数学／证据细则，保留条件加载和安全回退 |

16 KB 来源于 tests/fixtures/p3b_writing_role_source_map.yaml 与 tests/test_p3b_writing_roles.py，不是 GitHub 文件大小限制，也不是 GPT 上下文上限。文件变小不等于当前动作总阅读量变小。

既有 v10.20.4 [Optimization baseline](https://github.com/Vexushi1/mathmodel-skill/actions/runs/39118291396) 可作为规划度量参考：普通 CUMCM 写作初始 planned skill bytes 为 71,334，新图设计为 66,157；混合意图为 570,373。该运行所用 851083c 提交与本基线 tree 相同。这些是特定案例的规划字节，实际读取 token 指标仍为空，不能当成真实对话成本或模型阅读证据。

## 3. 现行业务流程：重构后必须原样保全

本节是实施核对用摘要；具体要求仍由各 Authority 定义。

| 顺序 | 助手动作及此时应读的内容 | 完成／等待条件 |
|---|---|---|
| 1 启动与审题 | 入口、bootstrap、全局规则及适用路由；恢复 current 框架／State；审题、附件与非破坏性数据审计 | 明确任务、条件、输出和证据缺口；Problem Contract 冻结不等于允许写求解代码 |
| 2 模型设计 | 条件的数学后果、合理结构化简、最小充分模型、匹配 solver；先定义 PQS、必要 Trace 与 preprocessing_decision | proposed model 具备明确语义、范围、前提和数值执行计划 |
| 3 双审与批准 | 助手完成独立 Model Reviewer、Devil’s Advocate 两个 pass；修复 blocking，处理 review_required；提交 Model Approval Brief | 等用户明确批准当前 revision／validated identity 后锁模；“继续说”等含糊回复不构成批准 |
| 4 条件预处理 | not_needed 直接使用合法原始数据；question_local 在本问实现内处理；只有 project_level 才建立公共预处理入口 | 适用门通过后交付；用户实际运行公共预处理，助手验收真实工作簿 |
| 5 主求解 | 助手静态检查代码并完成当前语义／批准等适用门；用户按 full_fidelity 运行实际代码 | 等返回产物；助手核工作簿结构、身份、源码／数据／回执、PQS 和适用数值证据后才 accepted |
| 6 深化分析裁决 | 主结果 accepted 后，按题目、真实结果和计划主张裁决 required/not_required | required 才进入独立代码→用户运行→返回验收；not_required 有理由，不虚构稳健性已验证 |
| 7 绘图与预登记 | 读 current 框架、accepted 数值、Figure Authority 及触发资源；设计图的论证功能、视觉结构、caption 和 QA | 由真实执行／确认状态决定可用性；预登记小问／共享范围及预期功能，论文位置暂不强锁 |
| 8 逐阶段写论文 | 读 active Template Manifest／main 骨架，再按 §3.1 逐阶段取读与写作；每问先盘点图表 | 完成本问模型→求解→结果→真实验证闭合，再进入下一问 |
| 9 草稿语义审查 | 使用 Module 06 的 draft 入口及原业务 Authority | 处理数学／证据／结构缺口后再 Cleanup，不要求草稿此时已有最终 compile report |
| 10 表达清理与装配 | Cleanup 不删推导／证明／证据；按载体装配；LaTeX 正常 render 内部正式 audit→compile | 实际报告合格且绑定当前源码；不能把旧报告或仅 exit 0 当成通过 |
| 11 PDF 与最终交付 | 助手按 05D 实际看当前 PDF 每一页，再做 final review、八类 coverage 和当前 scope 实际适用门 | 未覆盖、阻断或未执行的 required gate 保持未完成；提交包路径完成适用包校验，不给普通 PDF 交付额外加打包前置，不自动代投赛站 |

### 3.1 写作顺序与必须补读的条件

当前 CUMCM 渐进写作按 writing_runtime_contract 的既有阶段运行：

~~~text
template_inspection
→ problem_restatement
→ problem_analysis
→ assumptions_symbols_and_preparation
→ question_model_solution_result_validation（逐问闭合）
→ evaluation_references_conclusion_appendix
→ abstract_title_and_keywords
→ draft_semantic_review
→ ai_cleanup
→ latex_assembly_audit_and_compile
→ final_review_and_delivery
~~~

这是作者工作顺序，不等于最终论文阅读顺序。assembled seam 仍按最终 active physical-file 邻接检查。正文关键证明与算法的激活由当前项目事实决定，不能等用户再次说“请写证明／伪代码”；planned/current proposition、stepwise/pseudocode 等需要补读其 reasoning／artifact 规则。缺状态时裁决，不能自动当 not_needed。

其他竞赛／载体若尚无经验证的窄读路径，保留原全量 reasoning 回退；不能套用 CUMCM 骨架来省读取。

### 3.2 人工和执行职责

- 用户明确批准模型是原有必要等待点；blocking 不能由批准豁免。助手应绑定自然语言批准与真实当前身份，不要求用户手输 hash。
- 首次项目 Python／MATLAB 后端选择可并入原 Brief；历史／已锁后端迁移依原规则做实际项目影响预览和显式确认。
- 显式启用新的多模型／同模型多算法比较 scope，保留既有范围双审和明确用户批准；普通 Analysis Necessity Gate 不因此增加审批。
- 用户执行真实任务的预处理、主求解和必要分析；助手不代跑任务模型，也不用缩小数据／降低迭代的替身结果验收。
- 用户返回实际产物；助手负责内部验收，不要求用户另跑 Skill checker、同步器或机器审计。
- MATLAB 绘图仍保留用户实际运行、GUI 查看、必要调整和导出；draw.io 无法渲染时不能把结构检查当视觉通过。
- PDF 逐页检查承担人是助手。看不到全部页面时记录未覆盖和影响，不自动让用户本地编译／代审。
- A/B/C 等协议仅按已声明且适用的策略／范围启用；不因本次结构重构默认全部开启。

### 3.3 图表与论文怎样衔接

预登记时写“这张图属于哪一问／共享范围、支撑什么结论”，允许具体小节待定。进入该问写作前，助手读取所有相关登记，包括共享图、位置待定图和补充证据；按当前骨架安排真实 slot。写完回填实际 use／merge／omit、引用与理由，保留证据身份。

位置安排不能让未运行、未导出、未确认的图自动合格；单纯修改 caption 或入文章节位置不触发模型重新批准或无意义重跑 03A／03B。图表规则仍留在 Figure Authority／Protocol，不搬进读取层。

## 4. 目标操作机制：一次当前动作，取得一组完整适用正文

### 4.1 规则职责分工

| 层次 | 保留／拟承担的职责 | 不承担 |
|---|---|---|
| GPT 全局工作指令 | 提醒在工作边界主动重新取得正文、恢复证据、照规则做完再推进 | 不复制详细标准、不覆盖平台指令、不充当机器门 |
| SKILL／bootstrap／global policy | 启动与 Authority 导航，说明实际工具能力边界 | 不放全仓规则摘要 |
| workflow_router／resolve_runtime | 当前意图、范围、pause、assurance、动态门禁来源 | 不因“已规划”代替执行 |
| reading_plan／writing_runtime | 现有选段与阶段顺序；补齐遗漏阶段和条件读取映射 | 不新建第二份章节表或固定 gate 表 |
| 拟新增正文消费薄层 | 按已有计划提取真实原文、分块、标识完整性、暴露未取读范围 | 不重新决定业务资格，不给模型／图／论文自动判正确 |
| 原业务 Authority | 唯一质量标准 | 不把重复标准散落到阶段卡、计划和模板 |
| 当前项目事实 | 框架语义＋State 状态＋accepted 工作簿／真实图／PDF | 不从会话印象恢复 passed、批准或数值 |

未来可提供一个工具调用式正文接口，但本计划先落地现有 GitHub 能消费的路径。仅添加 MCP 工具本身也不能保证模型一定调用；真正不可绕过的取读与推进控制需要宿主执行器配合，不能由仓库文字宣称实现。

### 4.2 重读触发矩阵

| 事件 | 操作 |
|---|---|
| 首次启动任务 | 定位使用版本／commit，读入口及当前阶段实际规则 |
| 转阶段、新小问、新章或新图设计 | 重新取得对应原文；即使同一固定 commit／hash 也触发 |
| 跨聊天恢复、只有压缩摘要、无法确认适用原文完整可见 | 从原仓库和当前项目事实恢复，不从“之前读过”推定完整 |
| 本问新增证明、伪代码、比较、图形增强等能力 | 按当前事实重新求适用集合并补读 |
| 范围、模型语义、证据身份或依赖变化 | 重新定位受影响来源／当前事实；失效仍沿原有依赖传播 |
| 工具返回截断、只返回目录／标题／摘要或部分范围 | 分段补齐；无法补齐时保留未完成范围 |
| 同阶段同范围的小修改 | 只有相关原文仍完整可见、来源确定且证据当前时才复用，不要求每轮全读 |
| Skill 版本没变 | 仅说明文件身份稳定，不构成免重读理由 |

无需依赖模型准确感知“刚刚发生了压缩”。在明确的新阶段／新问边界重读，恢复时保守重新取得，降低压缩不可见带来的影响。

### 4.3 助手的具体操作步骤

1. 识别当前动作、问题范围、竞赛／载体及项目材料；读取 relevant current 框架。跨聊天恢复、全文写作和终审按现行规则读取完整 current 框架。
2. 使用已锁定的 Skill ref；同项目不静默换到新的 main。未指定版本时先解析当前发布／commit 并说明本次采用来源，不每章重复询问。
3. 有同版本完整资源根、依赖和必要项目材料的执行环境时调用现有 resolver，并传真实项目范围；不能仅因看见 Python 工具就假定可运行。只有 GitHub 读取时，按当前入口和阶段来源定位规则，不虚构 resolver 输出或机器 PASS。
4. 读取 read_now 的真实正文。保留文档前言、父节适用语和 YAML 父级上下文，不只抓关键词附近几行。
5. 逐项检查 conditional 的触发事实；必要时先做既有 capability preflight。补读已触发规则，区分“确定不适用”与“事实不足待裁决”。
6. 检查返回内容是否完整。使用工具确实支持的行范围／分块方式补齐；记录缺口，不假定一次工具调用等于完整文件。
7. 读取当前输入和证据：数值回到 accepted 工作簿；图、正文、编译报告核身份与 stale。不得仅凭聊天缓存沿用资格；当前身份和 stale 核查仍有效的既有验收可以复用，是否重跑依原契约决定。新阶段重新读规则，不等于所有旧产物重新验收。
8. 立即完成当前动作。若分块较多，可按真实子范围取读和工作，但不能宣称未覆盖部分已通过。
9. 对照原文检查成果：看实际段落／图／代码／证据是否满足，不以“已经读过”代替落实。执行 resolver 当前 pre_delivery_gates 的适用序列，不另抄固定清单。
10. 更新现有框架和必要 State／产物记录；只在原有批准、用户执行或缺失必要材料处等待。阶段变化时简短说明所读来源／当前动作／缺口，不新增用户签字流程。

### 4.4 两种使用环境怎样兼容

| 环境 | 后续拟提供的使用方式 | 限制 |
|---|---|---|
| 用户当前：ChatGPT＋GitHub | 薄阶段导航指向完整来源／条件；实测支持范围读取时直接取原文，否则使用原生成链派生的必要原文块；全局指令要求主动取齐 | 必须用真实连接器证明正文能取齐，不能只证明能找到路径；不能直接执行仓库 Python，其他工具以会话实际能力为准 |
| 有仓库和执行环境的客户端 | resolver 规划＋共用正文提取薄层，返回可直接消费的实际文本与完整性信息 | 提取成功不是 gate PASS；助手还要执行动作和现有门 |
| 未来受控宿主 | 复用同一接口，宿主验证取读结果后再允许推进 | 本轮不开发宿主，不以此作为当前用户使用前提 |

静态导航和脚本提取共同使用同一选段／阶段来源。导航不人工复制规则正文，脚本不拥有第二份流程。允许必要的自动派生原文块，不为每个交叉组合手工维护新卡片。原文块是来源视图，不是新的 Authority；它们不能授予门禁资格。

## 5. 正文消费接口与维护方式（后续设计约束）

### 5.1 推荐最小落点

- 扩展现有 core/runtime_assurance_contract.yaml 的 reading_plan 部分，明确取读、分块、缺口和阶段边界语义；不新增平行“最高契约”。
- 共用 scripts/reading_plan.py 的选择／上下文逻辑；拟新增 scripts/read_stage.py 只作为正文输出适配器，禁止重写路由／批准／资格逻辑。最终 CLI 名称在实施 PR 定稿，本文不表示该脚本现已存在。
- 拟生成 core/stage_reading_guide.md 作为 GitHub 可读的薄导航。其阶段、来源与条件指针从现有映射派生，生成步骤并入原 generate_indexes／refresh-generated 链；不引入新手工索引和生成工作流。
- 在 P1 先实测用户可用 GitHub 工具的范围读取／截断行为。若不能直接取齐选定来源，则由同一生成链在拟用 generated/reading_sources/ 下派生必要原文块：保留原文字节内容、父级上下文、来源 path／SHA-256／行范围和块关系，取读时绑定选定 commit，导航指向这些块。不手工重述、不保存 PASS，不为阶段组合重复复制；块大小由真实工具试用确定，不编造平台限制。生成器明确排除自己的派生输出作为输入，避免递归生成；产物不嵌入不断变化的当前 HEAD／时间戳，保证最终 bot head 可重复生成，防止自引用更新循环。
- SKILL 只保留简短工作循环和导航入口；写作阶段仍以 writing_runtime_contract 为 Authority。

### 5.2 一次正文返回最少需要什么

| 内容 | 要求 |
|---|---|
| 当前动作与范围 | 来自实际 resolver／阶段上下文，不靠正文工具猜批准状态 |
| 来源身份 | 相对路径、选定 ref／commit、原文件字节的整文件 SHA-256、1-based inclusive ranges。GitHub blob ID 另列，不能冒充 SHA-256；无法计算时标 unavailable，不用片段 hash 或 blob ID 填充 |
| 正文块 | 返回原文及必要前言／父级上下文，不把摘要当完整正文 |
| 覆盖情况 | 每块范围、已返回／尚缺范围、是否仍需下一块；只有实际返回完整集合才能标取读完整 |
| 条件项 | 条件来源、当前触发事实、应补读资源；unknown 不等于 false |
| 项目事实指针 | 当前框架／State／accepted 证据位置；不能仅凭文件名 declared_unverified 取得窄读资格 |
| 后续动作 | 引用原任务阶段／pause 与动态门禁，不另定义完成条件 |

接口可返回暂存诊断或工具事实追踪；本轮不预设新的 Project State 必填字段、读取回执 Schema、用户表单或业务 gate。不保存可复用的“模型已读 PASS”。

### 5.3 回退与一致性

selector 不命中时，按现有契约回退到完整的现存文件并说明原因；源不存在则报错，不能返回空规则。范围不清、多意图或条件未闭合时保守读取，直到有证据支持窄化。提取期间文件身份不一致时重新取一致来源，不拼接不同 commit 的片段。

静态导航只能列出条件及其权威位置，实际激活依当前项目事实。不可把“写作时可能用到的所有能力”全预加载，也不可因用户没说某个关键词就省去必要证明／算法规则。

## 6. Module 06 的职责拆分方案

### 6.1 拟用结构

~~~text
modules/06_review_delivery.md            保留旧入口、时机、严重度、返修和交付裁决
modules/06_review/content_review.md      拟新增：草稿／终稿共用内容检查动作
modules/06_review/final_delivery.md      拟新增：仅终稿的上下文、覆盖、证据和提交闭合
~~~

这是保留质量的职责拆分，不以“每个文件低于 16 KB”作为成功标准。入口保持清楚且有增长余量；实际阶段读取量按所有必读来源的去重并集测量。

### 6.2 逐段保全映射

| 当前 Module 06 内容 | 拟去向 | 保全要求 |
|---|---|---|
| 开头职责、draft/final 时机 | 旧入口 | draft 不提前要求最终编译；final 同时消费共用和终稿部分 |
| 一 评审分级 | 旧入口 | blocking／review_required／warning 及 finding 最少字段保持一致 |
| 二 题意、框架与局部 stale；Cross-File Seam | content_review | 保留真实依赖 stale、最终 active 物理邻接和语义连续性边界 |
| 三 公式／角色／算法／命题／数值，以及全部子检查 | content_review | 保留 capability activation、作者理由、核心正文推导、缩减／solver／参数依据和条件加载 |
| 四 Terminology／Numeric／Claim | content_review | 不用词频或格式启发式代替数学／语义判断 |
| 五 Title／结构／Paragraph 与历史能力 coverage | content_review | 保留层级与语义裁决，不把标题长短／数量偏好升级为 Hard |
| 六 深化分析、图表及 information value | content_review | draft/final 共用实际审阅动作；final coverage family 仍引用此处，不重复标准 |
| 七 Citation Evidence | content_review | 结构校验不代替文献语义支持判断 |
| 八 编译、复现与提交包 | final_delivery | 消费原载体／output／package Authority；PDF 逐页职责仍由 05D 唯一定义 |
| 九 Final Sweep 的全部子节 | final_delivery | 当前上下文、八类 coverage、原子 finding／评分、verified 官方 Hard、机器／人工边界全部保留 |
| 十 返修优先级 | 旧入口 | 按真实影响回上游／写作／Cleanup／载体修复，保留局部重审与必要一致性复核 |
| 十一 Blocking 条件 | 旧入口 | 保持终交付阻断；标题／人称／连接词等不能自动升级为 blocking |

八类 family 名称与现有矩阵保持不变：edition_compliance、anonymity_and_metadata、ai_disclosure、citation_entity_integrity、rendered_page_surface、figure_table_information_value、reproducibility_and_package、cross_question_dynamic_coverage。

### 6.3 兼容与测试迁移

1. 先列出旧文件所有被引用的 heading／anchor、读取 selector、保护测试和 C1 消费位置，再搬内容。
2. 旧路径继续存在；对已被引用的旧锚点保留简短指针或兼容锚点。保留文件名而丢失锚点不算兼容。尤其不能只留“标题＋链接”：现有 SourceReader 不会自动递归打开正文内链接。旧资源／锚点须在原 resolver／reading_plan 内显式映射到新正文范围；旧整文件请求展开完整适用闭包，缺映射或歧义不得静默视为读完。
3. 更新实际消费者：draft 读取入口＋共用部分，final 读取入口＋共用＋终稿部分；不得只读 final_delivery 而漏共用内容。同步核 core/module_manifest.yaml、runtime assurance 的资源闭包、相关 packs 和 lint，不仅调整 Markdown 链接。
4. tests/test_p3b_writing_roles.py 与 fixture 改为入口预算＋各阶段实际去重 read-set 度量＋内容保全检查。预算和比较基线须由实测与职责解释，不简单抬高旧上限。
5. tests/test_v830_editable_mechanism_diagram.py 对旧 Module 06 存在历史 hash／逆向转换保护。迁移时建立“旧检查→新文件／段落→等价行为断言”清单，保存旧基线来源，再将纯整文件冻结检查改为有依据的职责／行为保全。
6. 不无限追加字符串逆转换，不删除有效测试，不将新 hash 写进去就宣称语义保全。C1 finding／coverage／receipt 语义和 Schema 保持兼容。
7. core/review_receipt_contract.yaml 的 gate_authorities.required_paths 当前只列旧入口等来源。搬出的有效审阅内容必须进入对应 draft／final 的来源快照与 read-set；检查 scripts/review_receipts.py、project_transaction 和 C2 当前性消费。旧 C1 回执可作为历史只读证据保留，不能因入口 hash 未变自动证明新来源的 current review；按真实受影响范围复验，不伪造新回执或批量批准。
8. 检查入口、完整 canonical closure，以及包含条件／回退／兼容展开后的阶段阅读并集；即使终稿仍较大，也按文件／问／family 分批执行并闭合覆盖，不抽样通过。

## 7. 分批实施路线与详细操作步骤

这些工作包是同一架构的有序落地，不是不断追加提醒。建议小范围 PR 串行推进，先稳定一个可用闭环，再扩展覆盖；每批独立可审、可回滚，不让多条分支同时改同一 Authority。

### P0 本次：形成计划与立即可用的全局指令

- 操作：核对 main／版本／open PR／Authority → 形成修改简报 → 独立 docs 分支 → 编写本文件 → 独立审阅 → 提交并推送 → GitHub 生成与 draft 检查 → 交付链接。
- 完成条件：有详细计划和适用于当前 v10.20.4 的指令；明确未来能力未实施。
- 本次停止点：仅计划，不自动开始 P1，不预定新版本号。

### P1 读取边界与单一来源整理

**先读：** SKILL、bootstrap、runtime assurance、workflow_router、writing_runtime、reading_plan 及现有读取测试。

1. 在新 main 上重新核查版本、重叠 PR 和基线，写本批简报，确定实际版本等级；实测主要 GitHub 连接器能否按范围取得正文及其截断方式。
2. 逐条登记阶段、现有来源、条件来源、父级适用语和 selector；以现有映射为基准，不另手写第二套 phase registry。
3. 统一入口对 read_now／conditional／load_order 的解释；把固定版本下的新阶段／新问／恢复也要取读写入唯一读取契约。
4. 定义正文消费／分块协议与上述薄导航的生成来源；标清“取得正文”“落实成果”“机器检查”的不同状态。
5. 给缺源、错误 selector、截断／缺块、混合意图建立测试用例；不改变原 pause、terminal outputs、assurance envelope 或 gate 顺序。
6. 做关联文件 diff 审阅；原有项目／批准／代码行为不变，避免借入口整理拓展业务。

**验收：** 现有 resolver 输出保持兼容；来源映射无重复 Authority；生成导航的每个指针能定位真实内容；新增约束有可执行验证而不只是字符串“必须”检查。

**回滚：** 撤回本批入口／读取契约与适配字段，旧 CLI／read plan 仍可用，不修改用户数据。

### P2 共用正文提取与绘图／写作试点

**依赖：** P1 来源与接口稳定。**先读：** reading_plan、writing runtime、Figure Authority、Protocol、reasoning 条件入口及现有工具接口。

1. 在既有选择／范围逻辑上实现真实原文输出，保留前言、祖先上下文、文件身份和显式回退。
2. 处理多块返回：报告未返回范围和完成条件，校验重叠／缺行／身份混杂；不把块数当已读证据。
3. 接通薄阶段导航生成；它只列当前阶段原文位置／条件来源，不复制规则摘要作为替代。若直接范围读取不可用，按 P1 实测结果接入必要的自动原文块生成；所有块回绑原 Authority，去重并防止生成递归。
4. 试点新图设计、已有图 style-only，以及 CUMCM 重述／分析／单问闭合／摘要阶段；不能用 style 窄读资格替新图设计。
5. 用项目状态激活证明／算法、图形增强／选型等 conditional；unknown 按原裁决路径处理。
6. 模拟固定 commit 长任务：新问／下一章必须再取正文；同一当前章的小改允许受限复用。
7. 用真实 ChatGPT＋GitHub 进行试用，保存必要的工具调用／实际返回范围与成果对照；不得把脚本单测代替此试用。

**验收：** 真实 ChatGPT＋GitHub 路径无需执行新 Python，也能完整取得当前动作所需正文、父级语境和条件补读，并演示截断后的补齐。仅能定位路径不算核心验收完成；若范围读取和生成原文块两条路都未证实可行，该路径仍未完成。有执行环境可由共用脚本返回同等正文，两条路径所用质量定义完全一致。

**回滚：** 停用新适配器／导航入口，回到当前直接读原 Authority；保留原业务门，不能回滚成“凭摘要写作”。

### P3 Module 06 保全拆分

**依赖：** P1 映射与稳定锚点；为降低风险，在 P2 试点完成后推进。**先读：** Module 06、05D、矩阵、C1、全部直接引用与上述保护测试。

1. 按 §6 形成完整迁移表，列每个旧检查的目标段、消费时机、Authority 和验收。
2. 搬移共用／终稿内容，保持严重度、阻断和裁决不变；旧入口只留职责与必要导航。
3. 同批更新 bootstrap 指针、路由／manifest／写作阶段读取和 selector、runtime assurance 闭包、相关 pack／矩阵引用，逐项测试旧路径／锚点的真实展开，不只测链接可点击。
4. 迁移保护测试，保留历史基线出处；将新正文纳入 C1 来源快照和 read-set，核 C2 当前性；验证 draft 不加载无关终稿材料、final 不遗漏共用检查。
5. 测入口和真实阶段 read-set，并核全部八类 family、rendered pages 的 05D 委托、C1 与人工边界。
6. 远端生成与最终 head 验收后，独立审查是否有标准被弱化；若不能证明保全，不发布。

**回滚：** 通过 revert PR 恢复旧入口／完整内容、引用和测试；用户论文／数值产物不回滚。

### P4 全流程覆盖、恢复验证与发布收口

**依赖：** P2、P3 完成；P2 的正文接口不再变化。

1. 把启动／审题、模型设计／双审／批准、预处理、代码交付、返回验收、分析裁决、机制图、装配与最终交付接入同一取读循环。
2. 对每个仍全量回退的路径登记原因；只有有保全证据才新增窄读，不以全部强行窄化作为发布条件。
3. 核查每阶段实际项目事实和 pause；不得复制 gate 列表、自动批准模型或切换数值后端。
4. 完成 §9 场景测试及真实会话验证；检查长对话、无压缩标记恢复、截断和条件变化。
5. 更新面向使用者的短入口／操作说明和全局指令；指令引用唯一来源，不承担完整细则。
6. 按实际 diff 决定版本：兼容新增通常评估 minor，真正破坏接口需迁移和相应等级；不因“重构很大”直接定 major。
7. 最终 head 冻结、GitHub 正式完整验收、生成差异复核、合并及 main 复核后，才宣称上线；Release／tag 依正式发布范围另行执行。

**回滚：** 保留旧 resolver／直接原文读取兼容路径；撤回本批入口和新增映射，不撤回用户既有事实／批准，也不复用旧 gate PASS。

## 8. 预期影响文件与禁止扩张范围

| 现有／拟新增位置 | 拟调整内容 | 不应发生的修改 |
|---|---|---|
| SKILL.md、AGENTS.md、core/bootstrap.yaml | 简明入口／正文消费顺序／实际能力边界 | 复制整份业务标准或再写固定 gates |
| core/runtime_assurance_contract.yaml | 扩展现有 reading_plan 消费语义 | 新建第二份资格体系 |
| scripts/reading_plan.py；拟新增 scripts/read_stage.py | 共用源选择、输出正文、完整性与分块 | 执行用户数值任务、代替 resolver 授权 |
| core/workflow_router.yaml、core/module_manifest.yaml、core/writing_runtime_contract.yaml | 原位补齐映射与 Module 06 消费／闭包拆分 | 另一套阶段顺序、全 reasoning 默认 preload |
| modules/06_review_delivery.md；拟新增两个 review 文件 | §6 的职责拆分和锚点兼容 | 弱化推导／证明／coverage／阻断 |
| core/review_receipt_contract.yaml、对应 C1／C2 来源消费实现 | 为实际审阅正文补齐既有来源快照／read-set 与失效判断 | 新回执 Schema、自动重批、把旧回执升级为新来源资格 |
| 拟生成 core/stage_reading_guide.md、必要的 generated/reading_sources/ 原文块；scripts/generate_indexes.py | GitHub 可完整消费的来源视图；原生成链管理与防递归 | 新独立 generator、手工重复标准、无需求全仓复制 |
| 读取／路由／写作／保护测试及 fixtures | 行为保全、选择提取、条件／恢复／迁移验证 | 任意放宽预算、删有效断言、伪造 golden |
| 对应 packs／模板／README 的直接引用 | 仅必要引用兼容 | 顺手改输出、数值契约、编译配置或论文内容 |

项目 State Schema、Workbook Schema、RUN_CONFIG／RUN_RECEIPT、批准身份、输出目录、A/B/C 协议原则上不改。若实现发现必须变更，停止扩大该批 diff，先补独立影响分析与迁移方案；不能用本计划笼统授权。

## 9. 验收：既测取得规则，也测实际落实

### 9.1 脚本／契约测试（GitHub）

- 精确提取 Markdown、YAML 及祖先适用上下文；多段范围去重、边界、完整 UTF-8 文本、来源 hash 和单一 commit 一致。
- LF／CRLF、BOM 与原文字节身份正确处理；Git blob ID、整文件 SHA-256 和范围内容 hash 不得混用。自动原文块可还原所声明来源内容，不能因摘要或格式重写丢规则。
- selector 失效的完整文件回退；源缺失报错；模糊／混合意图保守策略；不可返回“成功但空规则”。
- 正文分块不缺行，缺块／截断不能标取读完整；工具不支持行读取时有可行的替代读取策略或明确未完成。
- 新图与 style-only 分开；未验证证据不授予窄读；条件触发／unknown／not_applicable 正确。
- 逐问／阶段恢复与固定 hash 下重取；原 gate 顺序、pause、assurance 字段和接口输出兼容。
- Module 06 的旧检查保全、旧引用／锚点真实展开、draft/final 消费、八类 family 和 05D 所有权。
- 新正文缺失、旧锚点无目标／多目标、只读入口未读正文、正文改变但入口未变，以及 partial review 冒充 full 的失败场景；新正文变化须触发 C1／C2 真实当前性失效。

现有测试重点复用 tests/test_reading_plan.py、test_reading_plan_evidence.py、test_read_path_semantic_closure.py、test_v800_writing_runtime.py、test_router_contract.py、test_p3b_writing_roles.py、test_v830_editable_mechanism_diagram.py；关联核 test_v820_final_review_compliance.py、章节能力／seam／理由保全测试、test_review_receipts.py、test_review_receipt_consumption.py 与 Phase G 闭包。再按实际需要新增少量有独立价值的测试。不要只写与实现同形的快照或措辞测试。

### 9.2 真实使用场景与预期观察

| 场景 | 必须观察到的行为／结果 |
|---|---|
| 同一发布版本，进入下一章／下一问 | 有该动作实际原文返回，不以 hash 相同／早先读过跳过 |
| 长对话后只剩摘要，没有“发生压缩”提示 | 在阶段边界恢复原文与当前事实；不要求用户提醒 |
| 当前章的小范围措辞修改 | 完整适用原文仍可见时有限复用，不重复全仓加载 |
| 只取得路径、标题、目录或截断正文 | 补齐后才处理依赖要求；无法取得则明确缺口，不自报已读 |
| 原文取得成功但成果遗漏必要条件 | 成果核查不通过，补齐实际内容；不能用阅读记录豁免 |
| 新图设计、增强／选型条件触发 | 读取完整设计路径与条件资源，不冒用 style-only |
| 有已确认图，只改样式 | 根据真实已验证绑定缩小范围，不新增模型批准 |
| 先图后文，含共享／位置待定图 | 写问前盘点、按骨架落位、写后回填；不凭排位给图批准 |
| proposition planned/current；algorithm stepwise/pseudocode | 即使用户未提醒也激活相应正文规则与真实 Trace |
| 模型双审有 blocking，用户说直接做 | 先修复，批准不能豁免；含糊“继续”不产生模型批准 |
| not_needed／question_local／project_level 预处理 | 仅 project_level 激活独立公共预处理；后续验收不省略 |
| 代码已交付但没回工作簿 | 保持等待实际执行，不宣称 accepted／求解完成 |
| 工作簿声明 passed，但底层身份／残差冲突 | 按实际证据拒绝错误资格，不能只信摘要单元格 |
| 03B not_required | 有理由，不造分析产物，不写已做稳健性 |
| 语义变化与 caption／位置变化 | 前者按真实依赖失效；后者不无意义重审／重算 |
| 只有 GitHub，缺实际执行／PDF 视觉工具 | 如实区分已读、语义审查与未执行机器门／未看页面；不转嫁本地 checker |
| LaTeX 正常 render | 正式 audit 在 render 内先行；不重复运行独立 audit 作为日常强制操作 |
| PDF 只看部分页／重新编译后 PDF 已变 | 覆盖不足不 passed；新 PDF 不继承旧字节的逐页结论 |
| 非 CUMCM／载体未知／混合意图 | 保留合法全量回退，不强套窄读模板或编造赛事 Hard |
| 最终评分高但有 blocking／未执行门 | 不交付；评分／exit 0 不覆盖 status 与 finding |
| Module 06 拆分后终审 | 共用＋终稿检查全部覆盖，旧入口／锚点兼容，family／Schema 不变 |

试用记录看实际工具行为、返回范围、阶段成果和状态，不能只问模型“你读了吗”。测试样本、工具限制、失败和未观察项均应记录；不把少量成功案例写成所有对话的绝对保证。

### 9.3 不能承诺的部分

仓库 CI 能验证选择／提取／映射／兼容；真实会话能观察特定条件下是否按要求取读和落实。两者都不能从技术上证明模型理解了每句话。纯 ChatGPT＋GitHub＋自定义指令仍是行为约定；要做不可绕过的推进控制，需要宿主集成，属于后续独立能力。

## 10. 预算、兼容与长期维护

### 10.1 怎样评价变轻，而不牺牲质量

分别记录：入口字节、完整 canonical closure、当前 read_now 去重并集、已触发 conditional／fallback／兼容展开并集、延后材料总量、实际工具返回正文量、实测 token（有证据时）、必要规则漏项和成果缺项。初始加载变小但每章重复巨量、或一段完整规则被重复算多次，都要显式呈现。用于 hash 的磁盘 I/O 另计，不当作模型已消费正文。

不预设“降低 50%”之类无依据数字，也不根据 GPT 型号猜可用上下文。Module 06 先保全职责再定入口／阶段预算；最终 coverage 必需材料若仍多，可以分批闭合，不删标准。

### 10.2 固定版本与旧项目

一个项目使用的 Skill ref 保持稳定，除非用户明确选择迁移；升级仓库不自动升级竞赛中的项目。固定版本仍在工作边界重新读原文。新项目选择已发布、可定位的版本／commit。

旧 CLI／read plan／项目字段按兼容路径继续；新增正文能力可加法接入，不能让旧客户端跑更少的 gates。兼容锚点需列具体来源和消费者；仅在无活动引用、消费者完成迁移、回归覆盖且发布说明明确后才考虑删除，不设永久无主 legacy 分支。

### 10.3 后续维护者的日常操作

| 以后改什么 | 维护步骤 |
|---|---|
| 修改某条写作／绘图标准 | 改唯一业务 Authority；检查当前 selector 是否仍覆盖；GitHub 生成导航并验实际内容，不同步抄多份 |
| 新增能力或条件 | 在原路由／writing runtime 的正确位置接入；补触发／不触发／unknown 场景及实际成果验收 |
| 改标题、移动章节／文件 | 同 PR 维护稳定 selector／兼容锚点和所有引用，运行范围保全测试 |
| 修改读取／分块实现 | 核文本完整性、父级语境、来源一致性、回退及旧接口；不借机改业务资格 |
| 修改批准、输出、Schema 等业务接口 | 独立影响分析与版本／迁移，不隐藏在读取重构中 |
| 只写维护计划 | 放 docs，不进入默认运行链，不升级 Skill 版本 |
| 每次发布 | 从最终源码生成，核最终 head／main、导航指向和回归；不缓存任何 gate PASS |

生成内容始终由 GitHub 原工作流维护。维护者不手改 hash／受管索引，也不要求使用者承担生成或本地校验。

## 11. 仓库操作、正式验收和发布步骤

1. 每个工作包启动时读取 main 的 bootstrap 和 SKILL_CHANGE_GOVERNANCE，核版本／最新提交／重叠 PR／Authority。
2. 写修改简报，说明直接目标、不做、文件、保护项、兼容、迁移、测试和回滚；独立主题分支，禁止直接写 main。
3. 顺序完成该包源码与有意义的测试改动；只读核查 diff、引用、范围和标准保全。
4. 提交源码并推送，让 refresh-generated 在 GitHub 更新受管文件；拉回并确认 bot 只改预期生成产物。
5. 开发／draft 阶段走 GitHub 专项与静态／生成检查；不在本地运行 lint、unittest、generator、仓库 resolver、MATLAB 或 LaTeX 验收。
6. 准备合并时冻结为 ready，确认最终远端 head。按现行治理完成 GitHub 正式完整验收：Windows Python 3.10／3.14 全分片及汇总、Static contract lint、Generated file contract、MATLAB native、LaTeX templates、Production LaTeX attestation、适用 Optimization baseline 等。
7. 核所有 job 的实际 checkout、分片全集／结果／缺失、生成差异和当前 head；专项成功不能代替正式验收，源码／生成 head 改变后重新验收。
8. 独立复核实际业务／阅读保全，再合并；核 main 的相应 Actions。正式报告给出 PR、最终 head、合并 SHA、各门和未完成项。

上述 GitHub-only 是仓库维护验收策略，不改变真实赛题的用户 full_fidelity 数值执行。当前 P0 交付可保持 draft 计划 PR，不宣称后续功能已合并或全部正式通过。

## 12. 风险、推进看板与下一次接手方式

| 风险 | 处理 |
|---|---|
| 重构只是新增“必须读”措辞 | 必须落到正文返回、完整性、条件触发和实际成果对照；否则不算完成 |
| 新阶段卡又变成一套重复规则 | 导航／适配器派生自现有来源，只指原文，不复制标准 |
| 为减少初始读取遗漏条件能力 | 保留 unknown 裁决、父级语境和安全回退，验证证明／算法／图形增强 |
| 拆文件后总量没降 | 核阶段去重并集和实际读取，不以单文件大小成绩冒充收益 |
| 纯 ChatGPT 无硬控制 | 坦诚说明边界，先改善查找／取读；宿主控制单独评估 |
| 用户操作变多 | 读取追踪由助手／工具承担，不新增用户确认／checker／格式表 |
| 实施范围扩张 | 每包一主题，接口破坏单独迁移，不以本文替代新简报 |

| 工作包 | 当前状态 | 推进前置 |
|---|---|---|
| P0 计划与全局指令 | 已完成；计划保留为维护文档，不进入默认运行链 | 后续工作包须有明确授权并按当前 main／治理重新核查 |
| P1 读取边界与唯一来源 | 已完成并合并：PR #272，合并提交 `05b873bf3eb7944cf702ab1585f03a1587b8102c`，合并后 CI run #39214790013 通过 | 如发现来源映射或兼容缺陷，按实际影响单独修复，不重复实施已完成范围 |
| P2 提取与绘图／写作试点 | 已完成并合并：PR #273，v10.21.0，merge `a944de224ac967b7d4b76f8ce411eaef9a71e7b2`；最终 head full CI #39541737189、Optimization #39541737186 及合并后 main CI #39552530400 均成功 | 来源读取不代表项目条件已裁决；缺少 State 的 conditional 仍不能推定不适用 |
| P3 Module 06 拆分 | 已完成并合并：[PR #274](https://github.com/Vexushi1/mathmodel-skill/pull/274)，v10.22.0，merge `e346d1a1919272a8bfd5344ad8c7d446ed02e7be`；最终 head full CI #39587360559、Optimization #39587360494 及 main CI #39590192042 均成功；详见 [来源迁移](module06_source_migration.md) | 不重复拆分；仍保留全部质量标准、旧入口及真实正文闭包 |
| P4 全流程覆盖、恢复验证与发布收口 | 用户已授权；目标 v10.23.0，基线 e346d1a；实现与验收见 [PR #275](https://github.com/Vexushi1/mathmodel-skill/pull/275)，范围与受控试用索引见 [P4 验证记录](stage_reading_p4_validation.md) | 以关联 PR 的最终 head／合并／main 实际结果判定完成；保留合法全量回退，Release／tag 未包含在本批授权内 |

下一次接手可使用：

~~~text
请读取 docs/stage_reading_execution_refactor_plan.md，并先核对当前 main、
版本、未合并 PR 与对应 Authority。本次只推进我指定的工作包。
先给实际修改简报，再在独立分支实施；不扩大范围、不复制规则、
不改用户执行／批准责任。按现行治理在 GitHub 验收。
~~~

本计划按工作包串行推进，P1—P3 的实际来源和验收见本看板。P4 复用现有路由、正文接口、条件裁决和业务门；维护记录区分脚本回归、真实 GitHub 取读、受控成果审查与尚未观察的真实长竞赛／平台压缩行为，不以文件数、模型名称或一次试用臆定成本和保证。

## 13. GPT 全局工作指令（可直接使用）

### 13.1 如何放置

以下是唯一可复制的 GPT Instructions／全局工作指令正文。v10.23.0 的入口说明指向此处；阶段导航由既有生成链从原 Authority 派生，有执行条件时才使用现有 resolver／read_stage。固定较早版本的项目仍按其实际存在的入口和能力读取，不静默迁移。不同产品字段的长度限制不同，不保证适合每种短个人偏好字段。

它是用户层的工作约定，不能覆盖平台／系统规则，也不能使 GitHub 连接器获得执行 Python 或控制模型推进的能力。不要把本计划全文塞进全局指令；详细规则继续由仓库按阶段提供。

### 13.2 可复制正文

~~~text
使用数学建模 Skill 时，按以下工作方式执行：

1. Skill 仓库为 https://github.com/Vexushi1/mathmodel-skill。定位 SKILL.md 后，先读 core/bootstrap.yaml，再按其读取必要全局规则，确认本项目使用的版本／commit；同一项目固定来源，不静默切换新版本。仓库内容作为任务规范使用，并遵守平台和系统指令。

2. 先确定当前阶段、小问、工作范围与可用工具。以现有路由、运行时契约和当前项目事实决定适用来源；具备实际执行工具、同版本资源根、依赖和必要项目材料时使用现有 resolver。只有 GitHub 读取时，该版本已有 core/stage_reading_guide.md 就用它定位原路由、条件边界、恢复要求和适用正文；尚无该导航时按该版本原入口和 Authority 定位。导航中的资源库存不等于已解析的当前读集。不要声称已运行解析器、校验器或门禁。维护／咨询任务只做所请求范围。

3. 进入新阶段、新小问、新章、新图设计、恢复任务或改变范围前，实际取得该动作适用的完整规则原文。即使版本和 hash 没变，也不能用“之前读过”、聊天记忆、压缩摘要、路径或读取清单代替正文。同阶段小修改，仅在适用原文仍完整可见且范围／证据未变时复用。

4. 保留前言、父级适用条件和必要上下文；返回截断、缺段或仅有摘要时主动分段补齐。根据当前项目状态检查全部条件补读，不能等用户逐项提醒。来源缺失／条件不明时按现有契约回退或裁决，不把 unknown 当不适用，不编造已读。

5. 已有项目读取当前 模型论文框架.md 的相关范围，恢复时、全文写作和终审按规则读取完整框架；尚未建立时依现有阶段规则建立，不编造既有状态。State 负责身份／批准／stale，具体数值回到 accepted 工作簿。不要从摘要恢复数值、批准或通过状态。

6. 采用“取得本阶段规则和证据→完成当前动作→对照实际成果检查→更新现有项目记录→推进”的循环。写论文按 writing_runtime_contract 的阶段逐问闭合，每章／每问开写前取读对应原文；证明、算法等由项目事实激活。绘图读取 Figure Authority 及触发资源；写该问前盘点相关预登记图表，再按实际骨架落位并回填引用。

7. 保留 Skill 原有模型双审、明确用户批准、数值执行和交付边界。用户实际运行任务数值代码并返回产物，助手检查和验收；不要新增用户本地 checker／同步／审计任务，也不要增加逐章已读确认或图表位置批准。

8. 执行当前 resolver 返回的适用 pre_delivery_gates，顺序和资格遵守原契约，不另建固定门清单。LaTeX／PDF 依 05D，PDF 由助手实际逐页查看；工具或材料不足时标明未完成范围，不把日志、文本提取或部分页面当全页通过，不自动转交用户代审。

9. 读取来源可简短说明，但“已取到原文”不代表要求已落实、数学正确或检查通过。缺项先补实际成果；无法读取、执行或核验时，如实说明影响，继续不依赖该缺口的已授权工作，在原有必要等待点停止。不要伪造工具证据、运行结果、批准、引用、数值或 PASS。
~~~

### 13.3 用户首次使用时只需说明的内容

给出任务／题目、所选 Skill 版本（若有）和已有项目材料即可。全局指令负责让助手主动定位当前阶段和取读，不要求用户每章提醒。若实际仍出现遗漏，复盘其工具返回内容、条件判断和成果缺项；不单靠“模型说已读”或模型名称判断效果。
