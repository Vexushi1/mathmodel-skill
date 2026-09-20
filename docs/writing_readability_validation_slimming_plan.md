# 写作可读性与检查减重详细修改计划

> 仓库：`Vexushi1/mathmodel-skill`  
> 计划日期：2026-09-19  
> 计划版本：1.0  
> 编制基线：`main@a8cba4d5086eceaf06b98e9bac5332b811a05dc1`  
> 当前 Skill：9.3.1；本次计划提交不升级 Skill。  
> 授权状态：用户已认可 A–G 摘要并授权编写、上传详细计划；该句记录计划创建时状态。  
> 最终实施状态：**COMPLETED**；P0、W0–W5 与 Part C–G 已全部闭环，活动 release 已进入 v9.4.0。  
> 文件角色：维护计划与后续实施依据，不是新的 Runtime、Writing、Modeling 或 Approval Authority。

## 0. 使用方法与授权边界

本计划用于后续聊天或维护者接续实施，不要求每次赛题写作预读全文。实际写作继续由现有 Authority、路由和项目事实驱动。

本轮只提交本文件及既有生成器产生的索引、Manifest 变化；不修改写作合同、运行时、检查脚本、模板、测试、CI 或用户论文。计划进入 main 不等于其中的实现已经完成，也不等于已批准具体检查项降级、删除或改变验收语义。

后续开始实现前，重新读取最新 main 的 `core/bootstrap.yaml`、`SKILL_CHANGE_GOVERNANCE.md`、本计划和相关 Authority，核对未合并 PR 与实际基线。用户确认进入实施后，按第 10 节串行推进；出现超出本计划的风险或接口变化时暂停并报告。

本计划的正文推导、三级标题等要求来自本次用户明确批准的写作要求。本文不据此声称已经核验某届赛事的官方评分细则。真实官方格式冲突仍按仓库既有赛事规则核验机制处理，不凭经验扩大或撤销用户要求。

## 1. 修改简报

| 项目 | 本轮计划提交 | 后续业务实现 |
|---|---|---|
| 主题 | 固化写作可读性与检查减重实施计划 | 完整推导、评委可读表达、有限且有证据的检查减重 |
| 版本 | 9.3.1 保持不变 | 根据实际行为与兼容性评估，发布阶段再确定，不预定大版本 |
| 变更等级 | docs / planning-only | 按各 PR 实际变化裁决，不能把行为变化伪装成 docs |
| 直接产物 | 本计划及生成索引、Manifest | 已批准的最小 Authority/consumer/测试修改与验收证据 |
| 不做 | 不实施正文规则或检查逻辑变化 | 不重做模型设计、不扩建状态系统、不批量删除检查器 |
| 事实源 | 本次用户要求、当前 main 的相关合同/模块/代码 | 同左，并要求实施时重新取证 |
| 回滚 | revert 计划 PR | 按阶段独立 revert，保留必要兼容与证据 |

总体目标：**严格模型、完整推导、必要验证、清晰表达。**

“减重”主要针对重复读取、重复规则定义、同一输入上的重复计算、重复 finding 和过度风格复核，不针对数学论证、数值质量或提交真实性。正文是否可读与计算是否正确分别评价，任何一项改善都不能代替另一项。

## 2. 已批准要求与交付对应

| 编号 | 已批准部分 | 必须落实的核心变化 | 后续验收产物 |
|---|---|---|---|
| A | 检查体系减重 | 先实测再去重；保留 Hard，风格问题不反复阻塞；不新增平行检查体系 | 调用/规则清单、逐项裁决、正反例和成本对比 |
| B | 面向评委的表达 | 默认读者具备数学建模基础，但不预设其具有题目领域知识；标题可导航，术语首次解释 | 标题、术语和节首段的跨题型改写样例 |
| C | 核心推导在正文 | 本题模型与结论所需的非显然推导完整保留正文，不因长、难或不是最终公式而移附录 | 同一论证改写前后推导链与边界保全对照 |
| D | 表格与图表可读性 | 表题、表头、行名、单位、指标方向、比较条件和图表说明能独立理解 | 数值不变的表格/图表说明对照及渲染检查 |
| E | 正文叙事 | 现实问题、建模理由、推导、公式作用、结果含义相互承接；不机械套句式 | 局部段落与完整小问的可读性审查 |
| F | 章节层级 | **一级、二级、三级标题都可正常使用；禁止四级及以上** | 三级正例、四级反例、跨载体映射与误报测试 |
| G | 轻量可读性审查 | 接入现有 draft review / Cleanup / final review，不新增独立 Readability Gate | 原有 findings/coverage 内的审查记录，无新增必填状态 |

对 F 的解释必须严格保持：三级不是“只有必要时才允许”的例外，也不是必须每章写满三层的配额。论证按真实需要使用一级至三级；不限制三级标题数量，不因标题较多自动否决。

## 3. 当前仓库取证与问题定位

### 3.1 已读取的关键依据

下表记录本计划实际使用的基线文件及相关范围。基于这些范围可以提出影响面计划，但不代表已完成全仓函数级去重审计。

| 文件 | 已核对的内容 | 对计划的意义 |
|---|---|---|
| `core/bootstrap.yaml` | Authority 指针、最小读取、逐问事实与正式 Gate 不变量 | 不扩大全局预载，不削弱正式交付 |
| `SKILL_CHANGE_GOVERNANCE.md` | 修改简报、分支/PR、生成文件、测试、版本和回滚 | 限定本轮 planning-only 与后续串行实现 |
| `core/writing_reasoning_contract.yaml` | rule_governance、formula_reasoning_chain、Formula Roles；命题预算相关检索 | 复用既有 Hard/Default/Recommendation，不建立第二套写作 Authority |
| `core/writing_runtime_contract.yaml` | evidence bundle、逐问 preflight、渐进写作 stages、draft/cleanup/assembly/final 阶段 | 区分必要阶段复验和可能重复调用 |
| `modules/05_writing/paper_writing_protocol.md` | 标题最小化、二/三级组织、公式角色、模型/求解/结果、附录边界 | 保留已有写作能力，只补本次缺口与冲突 |
| `modules/05_writing/ai_cleanup.md` | Hard boundary、公式角色、术语数字、标题、机器诊断 | 防止压缩时删推导或改变数值与结论 |
| `modules/05_writing/latex.md` | 职责边界、图表环境、工程规则、正式审计入口 | 写法与载体分离，避免复制政策 |
| `modules/06_review_delivery.md` | 三档分级、两类消费时机、coverage、返修范围 | 可读性接入既有 review，不扩建流程 |
| `packs/artifact/proposition_proof.md` | 命题预算、证明等级、半页建议、同页命题框、附录迁移 | 存在需要按 C 修正的明确表述 |
| `templates/latex/cumcm/hsk/template_manifest.yaml` | 权威边界、章节槽、内部标题建议、appendix activation | 模板不得用篇幅反向决定核心推导位置 |
| `templates/review/final_review_matrix.yaml` | 既有八类 coverage、findings、source/PDF 绑定 | 直接复用，不增 required schema |
| `scripts/audit_latex_project.py` | prose audit 委托、正式报告、strict 与 review_required 行为 | 独立文件数不等于重复执行数 |
| `scripts/audit_paper_prose.py` | v8 audit 导入/调用、Finding、文本预处理与结构规则 | 找重复预处理和 finding 时必须检查真实嵌套调用 |
| `scripts/audit_v8_writing_surface.py` | 表面规则、段落预处理、风险提示 | 机器不能把表面提示当作语义证明 |
| `config/prose_audit_patterns.yaml` | 当前 warning/review_required 配置与机器边界 | 逐规则裁决，禁止一刀切全部降级 |
| `docs/p8e_validator_split_decision.md` | 既有大型 validator 不拆裁决与 host-adapter 风险 | 不重新盲拆 `lint_skill_checks.py` |

补充检索已定位 `tests/test_content_packs.py` 中现有命题环境/非 breakable 断言，以及 `templates/latex/cumcm/hsk/config/preamble.tex` 的命题环境定义。完整测试上下文与长证明渲染仍须在对应实施阶段读取，不能仅据检索片段直接改测试。

### 3.2 已确认的现状，不应误判为缺失

1. 仓库已经要求核心公式具备 Source → Derivation → Destination，并保护 Key Bridge Relation；不是“没有推导规范”。
2. Protocol 已有标题最小化、二/三级自适应小节、模型/求解器/验证器区分、数值精度保护和局部返修边界。
3. Review 已存在 blocking / review_required / warning，Cleanup 也明确不能替代数学审查；不是需要从零新增 Soft Audit 架构。
4. `audit_latex_project.py` 委托 `audit_paper_prose.py`，后者内部又消费 v8 surface audit。该嵌套是现有实现关系，不应仅因存在三个脚本就删除其中两个。
5. draft review 与最终装配后 review 面对的正文可能不同；正式 source/PDF/工作簿绑定承担不同风险，不能视为天然重复。

### 3.3 本次明确需要修正的表述与风险

| 编号 | 基线证据 | 问题判定 | 处理方向 |
|---|---|---|---|
| R1 | Proposition Pack 建议超过半页技术证明移附录，命题框超高时正文仅留关键链 | 与“核心非显然推导完整在正文”存在冲突风险 | 先判核心性，再选正文排版；不以长度/框高决定移附录 |
| R2 | Template Manifest 的附录说明包含长推导/证明 | 容易把篇幅当作核心性判据 | 模板仅引用正文边界，明确长不等于可迁移 |
| R3 | Cleanup 对 supporting_derivation 允许压缩或移位，Protocol 按篇幅/难度分配 | 角色标签可能被当作删减授权 | 非显然且本题论证必需者仍在正文；只压缩平凡重复步骤 |
| R4 | Protocol/Template 存在 professional object/problem-specific headings 表述 | 专业准确与读者可理解之间缺少本次明确优先级 | 对象/问题含义优先，必要术语保留并解释，不把标题泛化 |
| R5 | 现有规则重视 caption、数值和证据，但表格完整语义接口分散 | 需强化读表可理解性；不据此宣称所有表格都不可读 | 集中说明表题、行列、单位、条件、方向、注释及论证用途 |
| R6 | 目前读取范围中二/三级可用，但未见本次要求的统一“最大三级”合同闭合 | 需要建立明确的用户要求及 consumer 映射 | 允许三级正常使用；禁止四级及以上，包括伪装层级 |
| R7 | 部分表面风险为 review_required；formal audit 会拒绝未闭合 review_required | 可能使写作修辞问题放大为流程负担，不等于已经证明误报 | W0 建立误报/漏报例，再逐条决定保留或降级 |
| R8 | Runtime 多阶段检查，脚本有相似文本预处理，文档有多处规则摘要 | 存在减重候选，但尚无重复成本实测 | 先测量输入、时机、调用次数和语义，再决定复用或去重 |

“未在已读范围看到”不能作为全仓不存在的证明；R5–R8 的完整覆盖、成本和函数级归属仍属于 W0，不允许先写“已经去重完成”。

## 4. 权威位置与影响面分工

| 内容 | 唯一定义或主要承载位置 | 其他位置的职责 |
|---|---|---|
| 跨载体的正文核心推导边界、标题政策与证据分级 | 现有 `core/writing_reasoning_contract.yaml` 对应章节 | Protocol 给执行投影；Pack/Review 引用，不平行立法 |
| 普通正文标题、术语解释、表格叙事、段落写法 | `modules/05_writing/paper_writing_protocol.md` | Cleanup 只修表达；Review 只检查；示例不当项目事实 |
| 何时读取、检查和复验 | `core/writing_runtime_contract.yaml` | 不复制推导、表头、术语的完整正文规则 |
| 论文一级骨架与载体映射 | 现有 Template Manifest、LaTeX/DOCX 适配层 | 不把 CUMCM 一级骨架强加给 MCM/ICM、DOCX |
| 现有机器表面诊断 | 原 audit 脚本与 `config/prose_audit_patterns.yaml` | 明确风险提示与确定性违规的区别，不自动重写正文 |
| 终审结论和覆盖 | `modules/06_review_delivery.md` 与现有 review matrix | 不新增可读性必填项目表或独立状态机 |
| 数值、模型、状态事实 | accepted workbook、现有模型记录、project state | 本计划和写作润色均无权改写 |

实施中应优先修改原章节并替换冗余表述，不通过另加一整套 Readability Contract 来叠加政策。Schema 的 required 字段、既有 artifact key、route ID、CLI 与结果文件合同默认全部保持。

## 5. Part A：有证据的检查减重

### 5.1 把四类“重”分开

- 读取重：同一普通写作任务反复全量读取合同，或提前读取不相关章节。
- 定义重：同一规则在 Authority、Runtime、Cleanup、Review、模板中被重新定义。
- 执行重：相同输入和政策下，确定性检查重复解析或重复运行。
- 反馈重：同一问题产生多条等价 finding，或主观风格反复升级为阻塞。

不以脚本数量、文件长度或测试数量直接代表负担，也不预设所有重复都是无用。

### 5.2 W0 必须建立的裁决表

每个候选在维护证据中记录：检查对象、入口/调用者、Authority、输入及版本/指纹、阶段、风险、现有 severity、调用次数/耗时、已覆盖测试、建议、接受/拒绝理由。

建议只有五类：保留、同阶段共享计算、合并同义 finding、降低表面风险级别、在原接口下收敛重复实现。没有证据则保持原状，不为了完成“减重”数量指标强删。

同阶段计算复用必须同时满足：被检查内容、依赖集合、Policy/工具版本、检查范围和模式相同，没有中途写入。任何一项变化都需要按影响范围复验。初期优先函数内或单次任务内复用；不新增跨运行持久缓存、信任令牌或“已检查所以永久通过”状态。

### 5.3 必须保留的正确性与交付边界

题面条件和输出要求、数据/单位/精度、模型审批与 semantic identity、stale、数值主结果质量、accepted workbook 一致性、约束可行性、引用完整性、源文件/编译/PDF 绑定、正式提交包和已核验官方规则均不得弱化。

必要模型推导缺失、术语改变变量含义、表头单位错误、结果断言超过证据，不能以“可读性属于 Soft”降级。仓库 CI、多 Python 版本、真实编译与发布验收不属于本计划的裁剪对象。

不默认重跑已经有有效证据的数值求解；需要的是核对结果来源与适用范围。纯改标题、表述、表头显示名称不得让 locked model stale、重触发审批或生成数值新结论。

### 5.4 风格审查的减负方式

写作时按简短规则直接生成合适表达，不要求每段新增自评表。draft review 集中定位理解障碍；Cleanup 处理已定位的表达问题；final review 消费修复结果并复查修改影响，仍完成既有全篇 active coverage。

已证明相同且同源的 finding 可以合并，但不得合并掉不同位置、不同单位/模型含义或不同修复动作。未解决的高严重度项必须保留。表面关键词只能提示人工查看，不能自动裁决逻辑正确性。

R7 所涉及的 review_required → warning 只能逐条通过正反例决定；formal strict 对真正未闭合语义问题的拦截保持。不得一次性把所有 review_required 改成 warning。

### 5.5 验收

同一基线样例上，硬错误检出集合不得减少；每个降级项有误报与真实缺陷对照；原 CLI、报告消费和正式交付链兼容；成本改善提供相同环境/相同输入的证据。若拆分反而引入 context/adapter 协议或复杂缓存，拒绝该候选。

## 6. Part B：评委可理解的标题与术语

### 6.1 默认读者与标题任务

默认读者具有数学和建模阅读能力，但不预设其了解题目所属行业、专业物理概念或算法缩写。小标题应让读者先知道处理什么对象、回答什么问题，再在正文进入准确的技术名称。

研究对象和当前问题优先，不等于所有标题只能套“对象 + 问题”句型。短标题、标准术语、必要方法名都可以使用；关键是脱离作者内部上下文后仍可理解且不会混淆。

示例只展示表达方向，不作为固定标题库：

| 过度依赖技术名词的表达 | 更易定位的表达 | 不可丢失的信息 |
|---|---|---|
| 非线性变物性热质耦合场构建 | 药材内部温度与水分变化模型 | 正文解释参数变化、方程联系和假设 |
| FV–BDF–Radau 一致性 | 不同数值方法的结果比较 | 说明比较的是求解算法，不是三套物理模型 |
| Sobol 全局敏感性分解 | 各参数对预测误差的影响 | 正文给出实际方法、指标和扰动范围 |
| Pareto 解集演化 | 成本与服务水平的权衡 | 保留两项目标及非支配解含义 |
| 熵权–TOPSIS 评价结果 | 各地区收入质量的综合评价 | 方法确实使用时在正文准确说明 |

不能把标题改成“数据处理”“结果说明”“影响因素”等无对象的空标题；两个不同任务若因此重名，保留必要对象、方法或范围限定。一级官方/模板锁定标题不擅自改名。

### 6.2 术语使用

首次实质出现的领域术语，应在邻近位置说明准确名称、简明含义及本题中的作用。缩写首次给出全称或中文名称；已经清晰解释后不反复重新定义。表格/图中单独出现的缩写也必须在邻近说明中可恢复。

解释可以是同一句、括号、前后短句或已有定义的明确引用，不要求每个术语增加三句固定模板。基础数学常识不写成词典；专业术语不改成错误的口语同义词。

沿用已有 canonical term 和 Terminology Registry。简明显示名称与正式术语/符号需对应一致，不新增另一套术语注册表；显示层变更不改数据字段、关联键、工作簿合同和模型含义。

### 6.3 验收

仅阅读标题和节首段，可以复述本节对象、任务及其与前文关系；遇到必要专业词可就地找到解释。删掉术语包装后，不改变模型类型、方法角色、单位或结论边界。

## 7. Part C：完整核心推导留在正文

### 7.1 总原则

本题模型建立和结论所需的非显然推导，是正文论证链，不是篇幅富余时才出现的附件。可读性通过解释、分段、公式编排和一级至三级标题实现，而不是减少论证责任。

正文须能独立恢复：现实条件与基本规律如何形成变量关系，关键假设如何进入或化简模型，约束/目标/指标如何构造，推导在何种条件下成立，最终关系怎样进入计算并支撑结论。

### 7.2 必须保留的内容

- 本题条件到数学对象、控制方程、目标函数或评价指标的非显然建构；
- 决定模型成立的关键代换、坐标/变量变换、参考系处理、对称化简、降维和分解；
- 非平凡约束、初始/边界条件、可行性及必要性/充分性来源；
- 连接前式和最终模型的关键桥接，以及理解这些桥接所必需的 supporting derivation；
- 支撑主要结论或求解前提的命题与证明，不能只有结论或“证明见附录”；
- 影响主结果有效性的关键离散思想、误差关系或求解前提；
- 后问相对前问新增或变化部分的实际推导，而非未经说明的“同理”。

复用共享模型时，正文前部已有完整推导且后问准确引用即可，不要求每问复制同一推导。标准定理可引用来源并核验本题条件，但不能用引用替代本题自己的关键推导。

### 7.3 允许压缩或外置的边界

显然移项、重复代入、基础恒等变换和不改变理解的机械展开可以省略。完整程序、运行配置明细、批量重复系数、完整网格表或非主线补充实验可以放附录/复现材料。

外置前同时回答：移走后正文是否仍具备完整关键推导？该内容是否不承担当前模型成立、结论证明、化简合法性或主要算法前提？只要任一答案为否，就保留正文。

“公式不是最终输出”“Supporting Derivation”“篇幅长”“超过半页”“命题框放不下”均不能单独作为删除或移附录的理由。必须依据实际论证作用，不按角色名自动处理。

### 7.4 现有规则的具体修正方向

1. 在 `formula_reasoning_chain`、详略分配和命题治理位置明确正文完整推导原则；角色枚举和既有 Trace 接口不变。
2. Protocol 的 Formula Roles、模型建立、附录和篇幅章节同步引用这一边界；Final Summary 仍是收束，不代替前面的完整推导。
3. Cleanup 的 Compress / Re-locate 只作用于平凡步骤、重复表达或非核心补充，不能授权关键跳步。
4. Proposition Pack 中“超过半页通常移附录”“框高不足则仅留关键链”的建议改为先保证正文论证完整，再处理版式。
5. Template Manifest 的 appendix activation 不再把长度当作核心材料外置依据；模板不能反向裁决数学核心性。
6. 长证明先采用可分页的正文组织、框外完整正文证明或其他既有兼容形式；只有现有环境确实无法承载时，才单独评估最小渲染修改。

不能直接删除命题环境或放开所有样式。先读取 `config/preamble.tex` 和 `tests/test_content_packs.py` 完整上下文；短命题原样保留，长证明的解决方式必须有真实 LaTeX 渲染和引用/编号测试。不得为了让测试过而删掉原断言，需要以新的等价或更强能力保全用例替代已过时的具体样式限制。

### 7.5 验收

对同一模型制作“原始完整论证—改写正文”对照，逐一核对前提、定义域、量词、符号、方向、假设、关键桥接与结论。人工能只读正文跟随非显然推导；代码仍可复现；主张强度不因改写提升。

反例至少包含：把长关键证明移附录、用“可得”跨关键步骤、因 supporting 标签删掉必要推导、用数值对照代替严格证明。这些不能以文字变短或版面更好作为通过依据。

## 8. Parts D–F：图表、叙事与三级章节

### 8.1 D：表格是一份可独立理解的结果说明

表题说明对象、比较内容或关系；必要时说明时间、地区或场景范围。行名说明模型/方案/样本，而非直接输出内部运行代号。列名优先使用现实含义，保留必要符号；单位、比例/百分点、指标方向和比较基准在表头或紧邻表注明确。

不能默认所有指标越大越好。误差类、风险类、拟合类、约束余量等依实际定义解释；指标名称相同但计算口径不同必须区分。无量纲量标明无量纲或给出清楚定义，不虚构单位。

例如 `t_c / Cmax / eps` 不能无定义直接作为结果表头。可以使用“烘干时间/h”“最高含水率/(kg/kg)”“相对误差/%”，但必须先核对 eps 真实定义；不能为了让表头好懂就把绝对误差改成相对误差。

一张表通常服务一个主要比较问题，允许共同支撑该问题的多个指标。过宽时优先拆分比较维度、使用分组表头或精简冗余列，不把字体缩小到难以阅读。长表重复表头，注释紧邻对应表；不把同一数据复制成多张无独立信息的表。

题目指定的表格格式优先遵守，必要解释放邻近正文或表注；不得为改善阅读擅改官方工作簿结构。摘要、正文、结果表与提交文件的必要精度保持一致，不再使用“为简洁把高精度答案统一改成两位”之类做法。

### 8.2 D：图表说明与正文分工

图/表标题负责识别对象与范围；轴/图例/表头负责读数；正文负责关键特征、解释和答案。避免重复三次讲同一件事。图表关键解释应邻近出现，不要求每张图固定写几句话，也不把 caption 写成内部检查报告。

排版继续服从适配层已有规则：表题在表上，图题在图下。复杂图仅增加必要的变量/面板/方法解释；不改变原始数值、图中结论和证据级别。本计划不更改 MATLAB 调色、算法或数据读取合同。

### 8.3 E：公式多也能形成清晰叙事

每个非显然推导段让读者知道当前已有什么、还缺什么关系、为什么引入本式、怎样推出以及得到后有什么作用。这是信息关系，不是逐段固定句序。

公式前交代当前对象与依据；公式后解释现实/数学作用及下游用途。变量已在前文清楚定义后不重复逐字解释；连续公式间补足真正的理由，不用连接词填空。关键条件、近似范围和失效边界尽量邻近相关公式。

一段可以完成多个有依赖的推理，但不把互不相关的模型选择、求解器介绍、指标定义和结果解释塞进一个长句。分段按推理单元而非固定字符阈值。精简的是重复、包装、软件流水账，不是数学信息。

结果段解释“这对题目意味着什么”，而非逐格读表；模型不支持机制或因果解释时，保留现象和可支持的决策含义，不编造原因。

### 8.4 F：正式章节最大三级

规则：**一级、二级、三级标题均为正常可用层级；禁止四级及以上。**

示例：

```text
5 问题一模型建立及求解
5.1 温度与水分变化模型
5.1.1 热量传递方程
5.1.2 水分扩散方程
5.1.3 初始状态与表面条件
5.2 数值求解与精度检查
```

示例只说明层级，不强制所有题目采用该对象或小节数量。不得生成 `5.1.1.1`，也不得以小字号、加粗独立行、无编号子标题或列表包装新的第四层章节。

LaTeX 正文章节使用 `section / subsection / subsubsection` 对应一至三级。作为正式下级标题使用的 `paragraph / subparagraph`、自定义更深标题和星号版本都不能通过“未编号”绕过上限。宏定义、注释、代码示例和未激活模板中的字符串不等于已生成论文标题。

Markdown 与 DOCX 按最终论文语义层级映射：论文总标题、封面元信息不算正文一级；DOCX 显式 Heading 1–3 可用；自定义样式需核实际大纲层级。正式附录的章节标题同样不出现四级及以上，但证明步骤、算法步骤、公式编号和表内分组不是章节标题。

仓库维护 MD 本身、代码注释层级和 API/Schema 嵌套不受论文标题规则约束。不全仓替换 `####`，不修改与论文输出无关的文档层级。

三级以下仍有复杂推理时，使用连续自然段、公式组、证明中的分情况或说明句组织，不增设第四层。不得以三级上限为由删除应留正文的推导，也不得把所有三级小节强行并回二级。

## 9. Part G：复用现有审查，不增建 Gate

### 9.1 接入位置

draft review 集中发现标题、术语、表格和推导的理解障碍；Cleanup 只完成表达修正；final review 核对变更后内容与原有全篇 coverage。不新增 `readability_status`、项目 required 字段、新 JSON/YAML 注册表、独立 Readability Gate 或额外正常写作必交文件。

既有 `figure_table_information_value`、`rendered_page_surface`、正文结构及公式/能力审查承载本次需求；保持 review schema 和八类 coverage 的现有接口，不机械新增第九个检查族。

### 9.2 检查内容与严重度

| 问题 | 默认处理 | 升级条件 |
|---|---|---|
| 标题偏专业、长句、重复说明 | warning 或人工修辞建议 | 确实掩盖对象、造成语义缺口时按现有规则裁决 |
| 术语或表头难懂 | 就地解释、统一名称、补定义 | 改变变量/指标/单位/结果含义时为事实或数学错误 |
| 核心推导缺失、关键证明移附录 | 回正文论证修复 | 必要逻辑断裂按现有 Hard 处理 |
| 机器确定正式章节超过三级 | 对已采用本计划规则的新稿阻止正式交付 | 依据明确用户要求，不冒称官方规则 |
| 机器无法判断宏或自定义样式层级 | 人工复核该位置 | 不把解析未知直接当作四级，也不静默放行 |
| 数值、精度、引用、stale 或包级错误 | 保持原有 Hard/Default 语义 | 不因本轮“减重”统一降级 |

局部可读性变化不自动触发全篇重写。纯文字变化虽然不改变模型身份，但影响正文源文件，后续正式 audit/compile/source bundle 仍须与最终稿一致。

### 9.3 机器和人工各做什么

机器适合定位可解析的标题层级、缺失明确标注、重复编号/引用、字段与数值冲突以及既有表面风险。是否解释充分、表题准确、推导完整、技术名词能否理解仍需要语义审阅。

不得新增术语密度阈值、标题字符数上限、公式数量配额、可读性打分或 AI/人工身份分数作为通过标准。不能通过关键词黑名单把所有专业名词替换掉，也不能根据“因此”“可得”是否出现推断推导正确。

## 10. 实施顺序与 PR 划分

实施阶段必须串行。每个阶段的文件集合是影响面候选，不是要求全部修改；若现有能力已满足，用测试证明后保持原样。

| 阶段 | 任务 | 前提 | 主要交付 | 完成条件 |
|---|---|---|---|---|
| P0 | 详细计划入库 | 本次用户授权 | 本计划、规划 PR、真实 CI | 仅规划文件与生成产物进入 main；不宣称实现完成 |
| W0 | 读取/检查基线与影响面裁决 | 用户确认进入实施 | 调用图、候选裁决表、样例快照、数据范围 | 每个待改检查有风险与测试；不确定项保留 |
| W1 | 写作核心政策闭合 | W0 范围已确定 | A–G 对应 Authority/Protocol 最小调整 | C/F 无歧义；保留原有公式/证明/算法/数字能力 |
| W2 | Consumer、模板与样例对齐 | W1 语义稳定 | Cleanup/Review/Pack/Template/例文对齐 | 长证明、三级标题、可读表格能实际输出；不只改政策 |
| W3 | 已证明冗余检查的最小减重 | W0 正反例与 W1 分级已确定 | 逐候选复用/去重/分级补丁 | 硬错误不漏报；无真实收益的重构取消 |
| W4 | 既有 review 内的可读性验收 | W1–W3 集成 | 正例/反例、跨文件与载体检查、人工审阅记录 | 无新 Gate/required 状态；检查与输出符合 C/F |
| W5 | 综合回归、版本与收尾 | 前述阶段全绿 | 完整 CI、渲染/兼容证据、发布裁决与状态更新 | 实际新行为有 release 说明；范围闭合，不混入其他清理 |

W1–W4 不允许长期积累互相矛盾的主分支合同：每个 PR 自身必须包含使该次变化一致所需的最小 consumer 和测试。若 W1 的单条规则必须同时改一个 Pack 或模板才能自洽，应合并进该原子 PR，W2 再处理剩余样例；不能为阶段编号把破坏一致性的半成品合入 main。

W3 可按实际情况取消某个拆分候选；“未找到安全减重收益并有证据说明”是该候选的合法结论，不允许为完成计划而强行改造。任何更改正式 Gate 列表、报告 schema、规则严重度公共约定或信任复用范围的方案，必须回报具体差异后再批准。

## 11. 文件级修改边界

### 11.1 主要候选

| 文件或范围 | 预期动作 | 不可越界 |
|---|---|---|
| `core/writing_reasoning_contract.yaml` | 统一核心正文推导与三级层级政策；收紧篇幅外置语义 | 不改模型/证明真实性、公式角色枚举和主张证据关系 |
| `modules/05_writing/paper_writing_protocol.md` | 标题读者视角、术语解释、完整推导、表格、叙事与层级的执行写法 | 不复制完整硬合同、不固定所有题型小标题 |
| `modules/05_writing/ai_cleanup.md` | 改写权限与不可删推导边界；精简重复规则 | 不重新裁决数学、不改数值与术语含义 |
| `modules/06_review_delivery.md` | 复用现有分级和覆盖，明确可读性审查与复验范围 | 不取消全篇 active coverage，不凭机器通过代替语义审阅 |
| `core/writing_runtime_contract.yaml` | 仅在 W0 证明需要时精简重复读取/检查指令，更新实际 selector | 不新增生命周期、不降低 missing/stale 处理、不扩大默认预载 |
| `packs/artifact/proposition_proof.md` | 收紧长核心证明外置、预算与框高建议 | 命题作用、证明完整性、编号和主张级别不降级 |
| `templates/latex/cumcm/hsk/template_manifest.yaml` | 对齐 appendix/标题政策指针与载体边界 | 一级骨架、官方适配、条件槽机制不变 |
| `templates/latex/cumcm/hsk/sections/06_question1.tex`、`07_question2.tex`、`08_question3.tex` | 对齐实际小节、表头及示例推导提示 | 样例不得成为固定标题/方法要求 |
| `templates/latex/cumcm/hsk/config/preamble.tex` | 仅确有长证明正文渲染障碍时作最小兼容调整 | 不把所有环境重设计，不因框高删证明 |
| `modules/05_writing/latex.md` | 必要的标题映射与长证明载体说明 | 不拥有第二套正文政策 |
| `scripts/audit_paper_prose.py`、`scripts/audit_v8_writing_surface.py`、`scripts/audit_latex_project.py`、`config/prose_audit_patterns.yaml` | 仅实现 W0 已批准候选和明确层级检查 | 不扩建万能 LaTeX 解析器，不静默修改输出接口/错误含义 |
| `templates/review/final_review_matrix.yaml` | 优先只复用；确有需要时改说明或 evidence 填写指引 | 不新增 required 字段或检查族 |

`modules/05_writing/references/model_solution_reasoning_examples.md` 与 `model_construction_solution_rationale_examples.md` 在修改示例前完整读取相关案例；优先改已有实例，不新建泛化话术库。图形内容 Authority、DOCX 和其他比赛模板先核对现有接口，仅在发现本计划适用范围内的实际冲突时纳入最小修正。

### 11.2 仅审查或原则上不动

`core/workflow_router.yaml`、`scripts/resolve_runtime.py`、`core/runtime_assurance_contract.yaml`：仅核对阅读 selector、条件加载和保留的 Gate；不以写作减重名义重构路由或可信根。

`core/project_state.schema.yaml`、`core/state_transition_contract.yaml`、模型审批、数值验证、User Execution、Workbook/Output 合同、主求解与图表数据链：默认不修改；发生需要改变其语义的情况立即升级范围。

`scripts/lint_skill.py` / `scripts/lint_skill_checks.py`：不重新强拆。已有 P8e 对 host-adapter 耦合的裁决仍有效；只在受本次明确规则变更影响时更新相应兼容断言，不删除漂移保护。

`.github/workflows/`：本计划不裁剪 CI，也不更改权限、绕过检查或修改分支保护。`legacy/`、历史计划、80 个 MANUAL_REVIEW 分支和用户项目文件不纳入清理。

### 11.3 测试与版本载体

已定位可复用测试包括 `tests/test_v745_prose_audit.py`、`tests/test_content_packs.py`；其余 writing/runtime/reading-plan/LaTeX/review/模板测试须在 W0 通过目录与调用关系确认，不能假定文件名存在。

优先扩展原有测试。只有现有位置不能清楚承担新增反例时才新增一个聚焦测试文件，不建立新的测试框架。发布载体、CHANGELOG、README、优化状态等仅在 W5 按实际 release 决策更新；计划阶段不写实现完成记录。

## 12. 行为验收矩阵

下面是必须覆盖的行为场景，不要求一行对应一个新测试器。合适的场景复用同一 fixture；人工案例结果与机器断言分别记录。

| ID | 场景 | 必须通过的结果 | 禁止的伪通过 |
|---|---|---|---|
| T01 | 简单解析题，少量显然代数 | 清楚直接回答，不强造算法/验证/第三层配额 | 为展示完整性堆检查和公式 |
| T02 | 非显然机理模型推导 | 依据、化简、方程、初边值、适用范围在正文完整 | 只列最终 PDE，关键推导放附录 |
| T03 | 复杂优化模型 | 变量、目标、非平凡约束来源与最终模型完整；三级正常导航 | 只保留优化模型总括号 |
| T04 | 核心证明超过半页 | 正文完整证明可连续阅读并正确分页 | 因框高只留结论或关键摘要 |
| T05 | 长而平凡的重复系数/代码 | 允许压缩或外置，不丢核心思想 | 把所有长内容都硬塞正文 |
| T06 | supporting 标签实际承载必要推导 | 根据真实作用保留，必要时修正角色判断 | 仅按标签压缩导致跳步 |
| T07 | 同一方法跨问复用 | 正文准确引用已有完整推导，只展开新增部分 | 每问重复整套推导或虚构继承 |
| T08 | 多个三级标题 | 正常通过，不因数量或“非必要”拒绝 | 强制压回二级 |
| T09 | 四级标题及星号/伪装版本 | 在本计划适用的新稿中识别并改到三级以内 | 去编号但保留第四层语义 |
| T10 | 注释、代码块、宏定义含深层标题文本 | 不因非活动文本误报论文层级 | 全仓搜索 `paragraph`/`####` 后判错 |
| T11 | 专业术语首次出现 | 准确解释且后续 canonical term 不漂移 | 换成不准确口语词或持续重复定义 |
| T12 | 多模型/算法比较表 | 行名、单位、指标方向、比较口径清楚，数值完全不变 | 把算法比较改称模型比较 |
| T13 | 题面指定表与高精度结果 | 保留规定格式与位数，用邻近说明改善阅读 | 擅自舍入、改单位/百分比口径 |
| T14 | 局部标题/说明改写 | 不动数值、不触发模型审批；正式源文件审计随最终稿更新 | 复用过期 source/PDF 报告 |
| T15 | 相同输入的重复诊断 | 只合并已证明等价的调用/finding，硬缺陷全部保留 | 删检查而无行为对照 |
| T16 | 改写后符号、约束方向或证据变化 | 相关审查失效并重新执行，阻止错误交付 | 以“已经审过”绕过复验 |
| T17 | MCM/ICM、DOCX、非 CUMCM | 写作语义与最大三级适用，载体骨架保持各自合同 | 强行套 CUMCM 一级章名 |
| T18 | 真实术语/证明/数字错误 | 仍被相应 Hard/Default 流程发现并处理 | 所有可读性问题一律 warning |

T17 不要求为其他载体新增独立 manifest 或全面重构；至少明确适用边界、读取回退和实际支持程度。没有该载体运行环境时区分静态检查与真实渲染，不能声称已经编译/渲染通过。

## 13. 如何证明变轻且不变弱

### 13.1 基线记录

W0 选定普通单问写作、局部标题/表格编辑、含证明或算法的复杂写作、全篇终审等代表请求。固定相同源码/项目证据、检查模式和环境；记录实际读取文件/范围、去重后的 UTF-8 字节、重复读取、检查调用次数、重复 findings、耗时及输入绑定。

读取字节不是模型真实 token，耗时不是算法复杂度，检查数量下降不是正确性提高。没有实测数据时留待测，不承诺“减少 30%/50%”或其他任意收益。

### 13.2 双重验收

机器侧：同一硬错误集合不减少；旧有效用例兼容；新三级正例和四级反例成立；重复 finding 处理不丢位置/证据；正式报告与最终源文件/PDF 相符。

人工侧：同一模型、公式、条件、数值和结论边界保持；只读正文能跟随推导；标题可定位任务；不查代码或反复翻符号表也能理解关键结果表。若需要用户或独立审阅者评价，应记录真实反馈，不编造“评委已验证”。

减重候选至少展示一种可验证收益：少读无关规则、减少同输入重复执行、减少等价重复 finding，或降低已证明的风格误报；同时说明新增成本。若收益不足以抵消复杂度，撤销候选。正文完整性优先于字数、页数和公式数下降。

### 13.3 正式验证

所有合并遵守现有仓库治理，至少保持：

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests
python scripts/generate_indexes.py --check
```

再按影响面执行 writing/prose/runtime/template/reading-plan/proposition/review 等已存在回归，以及受影响载体的真实编译或渲染。最终仍要求完整 HSK Skill CI、Optimization baseline evidence 与生成文件合同；不得为本计划减少原测试矩阵。

只对最终被验收的实际 SHA 作通过结论；若生成器追加提交，应重新绑定最终 head。测试超时、跳过、环境缺失、模板 smoke 与正式验证必须分别报告。

## 14. 兼容、风险、停止与回滚

### 14.1 兼容策略

新写作及用户明确要求结构重写的正文采用新要求。旧论文和旧审查报告仍可读取，不批量改文、不覆盖历史数值、不伪造当时采用了新标准。

旧稿进入新的正式交付审查时，对超深标题或正文推导缺口给出定位和修正建议；不能因新增写作政策让既有模型结果失效或触发重算。题目条件、真实参数或模型关系发生变化时仍按现有模型治理处理。

尽量保持原公开函数、CLI、报告键、Formula/Algorithm/Proposition Trace、项目目录和 Schema。新行为需要实际 release 说明；若不得不破坏兼容，停止并提出独立迁移计划，不悄悄套 patch。

### 14.2 主要风险及应对

| 风险 | 识别信号 | 应对 |
|---|---|---|
| 减重导致漏检 | 既有 Hard 负例变成通过 | 立即撤销对应补丁，不放宽断言 |
| 推导保护变成无差别冗长 | 重复基础代数、共享模型反复复制 | 保留关键非显然链，压缩机械重复 |
| 标题去术语化造成含义模糊 | 两个不同任务变成同一泛化标题 | 加回必要对象/范围/方法限定 |
| 三级限制被误用于仓库 MD | 维护文档或代码示例被判论文错误 | 限定 active paper scope，按载体语义解析 |
| 长证明改善破坏短命题版式 | 命题编号、引用、短框渲染改变 | 优先兼容替代组织；渲染后逐项核对 |
| 复用结果过期 | 输入、框架、policy 或最终装配已变化 | 按真实影响重新检查，不做跨运行盲缓存 |
| 扩大到全仓基础设施重构 | 需要新 context/adapter/状态协议 | 停止，回到独立方案与用户审批 |
| 计划本身污染运行上下文 | 被加入默认 load 或当作 Authority | 维护文档只供实施检索，不加入写作默认读取 |

### 14.3 停止条件

出现任一情况暂停该项，不自动扩大范围：需要新增必填项目字段或生命周期 Gate；需要降低数值/审批/引用/交付标准；无法证明去重前后 Hard 行为一致；需要改写当前已批准模型；需要靠关键词判断数学正确；出现重叠 PR；官方已核验规则与用户约定发生真实冲突；需要修改无关模板/工作流/权限；生成元数据包含意外业务变化；无法完成必要兼容或真实渲染验收。

### 14.4 回滚

每阶段保留基线、修改范围、测试和实际 merge SHA。规则、consumer 与对应测试作为同一可回滚单元；回滚后重新生成索引与 Manifest 并执行受影响检查。不得只回滚 Authority 而留 consumer 的相反语义。

不为回滚恢复已清理远端分支，不修改历史 H2 清单。本计划不包含远端 branch 删除任务；实施产生的 PR 分支按照正常合并后管理处理，不能为删除一次分支再创建一轮收尾分支。

## 15. 实施状态与更新格式

| 范围 | 当前状态 |
|---|---|
| A–G 摘要方向及 C 修正 | 用户已认可 |
| F：三级正常可用，四级及以上禁止 | 用户已明确批准 |
| P0：详细计划 | MERGED（PR #193，merge `d11961f34ee8f9f6cfa6e80eafd67d37745eb4f5`） |
| W0 完整基线/检查去重裁决 | COMPLETED：PR #202；调用图、同环境耗时、输入指纹、正反例与逐候选裁决已闭环，final head 与 main 后验均通过 |
| W1 核心政策实施 | COMPLETED：W1-P1 / W1-P2 与 Part C/D/E/F/G 已闭环；检查减重继续走 W0→W3 独立阶段 |
| Part C：完整核心推导留正文 | COMPLETED：PR #194 完成核心证明正文保全，PR #197 完成非证明型核心推导正文闭环；final head 与合并后 main 验收均通过 |
| Part D：表格与图表可读性 | COMPLETED（PR #196，merge `b1b92eb31d444058a33a5e72a8ea8796dc1b28ec`） |
| Part E：公式多时保持清晰叙事 | COMPLETED：PR #199，final head 与合并后 main 验收均通过 |
| Part F：正式章节最大三级 | COMPLETED：PR #200，final head 与合并后 main 验收均通过 |
| Part G：复用现有审查，不增建 Gate | COMPLETED：PR #201 以既有 Review/Runtime/coverage 回归证明闭环，未新增 Gate/required 状态/coverage family |
| W2 Consumer/模板/样例实施 | COMPLETED：PR #205 完成 Consumer/Pack/Template/例文对齐，PR #206 完成长核心证明真实 LaTeX 分页与引用/编号验收；final head 与 main 后验均通过 |
| W3 检查减重实施 | COMPLETED：PR #203 仅移除 W0 批准的 count-only `question_subsection_granularity` finding；final head 与 main 后验均通过 |
| W4 行为验收集成 | COMPLETED：PR #207 完成 T01–T18 机器/语义双重验收与跨文件/跨载体证据；final head 与 main 后验均通过 |
| W5 发布与综合收尾 | COMPLETED：v9.4.0 PR #208 完成 release carriers、综合回归与发布说明；final head 与合并后 main 验收均通过 |

### W1-P1：核心证明正文保全

阶段 / PR：W1 原子修改 / PR #194 — `fix: preserve core proofs in the paper body`  
Base main SHA：`d11961f34ee8f9f6cfa6e80eafd67d37745eb4f5`；Final head：`3959fee68e9a588e1a3aae9dd9b1fe359b57f8ca`；Merge SHA：`1640680af529f71d08b40973626a85cd13d0b4c2`。  
本次获批范围与 Authority：用户明确要求证明不因长度被强制放附录；核心证明若决定模型成立、关键变换、核心结论或下游计算，应留正文。Authority 为 `core/writing_reasoning_contract.yaml#proposition_governance`，Pack 为 `packs/artifact/proposition_proof.md`。  
实际修改范围：Authority、Proposition Pack、Module 02 命题规划、Writing Protocol、AI Cleanup、LaTeX/DOCX adapter、DOCX checklist、CUMCM Template Manifest、Review 与既有测试。未修改 preamble、Output Contract、Project State、Runtime、Schema、CLI、Gate、数值链。  
核心裁决：删除“超过半页通常移附录”“整框过高则完整证明移附录”等长度优先口径；保留非核心技术引理/重复展开/扩展证明进入附录的空间；较长核心证明允许“命题陈述框 + 正文 `hskproof`”自然分页。  
检查减重候选：本 PR 不处理；未降低任何 Hard/Default 检查。  
核心推导、数值与三级层级保全：只改证明位置语义；不改变数值、模型、标题层级政策。  
静态测试 / 真实执行 / 生成文件：final head HSK Skill CI #3663 与 Optimization baseline #279 均 success；合并后 main HSK Skill CI #3665 与 metadata #2431 均 success。  
兼容性：0--4 命题预算、命题编号、现有环境名、Project State 字段和 Trace 接口保持不变。  
遗留问题 / 下一阶段：证明正文保全原子闭环已完成；继续 W1-P2 评委可读标题与术语首次说明；W0 检查减重完整基线仍单独执行。

### W1-P2：评委可读标题与专业术语首次说明

阶段 / PR：W1 原子修改 / PR #195 — `fix: make headings and terminology judge-readable`  
Base main SHA：`1640680af529f71d08b40973626a85cd13d0b4c2`；Final head：`8922dd2d26415e3a5dbdc1efadab5267f35118f4`；Merge SHA：`bf9c7d1a3cb6270f24db99c28ed1104c1d0b781b`。  
本次获批范围与 Authority：依据 Part B，默认读者为具有数学建模基础但不预设熟悉题目专业领域的评委。标题应优先恢复研究对象与当前任务，专业模型/方法名按真实区分需要保留；领域术语、项目自定义指标和专业缩写首次实质出现时给出准确、简短、邻近的含义与本题作用说明。Authority 为 `core/writing_reasoning_contract.yaml#model_establishment_solution_narrative.professional_heading_semantics` 与 `#terminology_governance`。  
实际修改范围：Writing Reasoning Authority、Paper Writing Protocol、AI Cleanup、Review 与既有 heading/terminology/drift regression。未修改 Template Manifest、标题层级规则、表格规则、Runtime、Schema、CLI、Gate、数值链、模型审批、MATLAB。  
核心裁决：不把“去专业化”理解为删除专业术语；必要模型名/方法名可保留。只在标题由专业缩写/方法堆叠遮蔽对象和任务时补回对象/目的或把非必要方法名移入节首正文；禁止退化为“数据处理/模型处理/结果说明/影响因素”等无对象空标题。术语首次解释不采用固定三句模板，也不靠机器词频或括号存在判断充分性。  
检查减重候选：本 PR 不处理；不新增 Readability Gate，不改变现有 severity 公共接口。  
核心推导、数值与三级层级保全：PR #194 的正文证明规则保持；数值、模型和“一级至三级正常可用/四级及以上禁止”的后续任务均不在本 PR 改动。  
静态测试 / 真实执行 / 生成文件：final head HSK Skill CI #3673 与 Optimization baseline #284 均 success；合并后 main HSK Skill CI #3675 与 metadata #2441 均 success。  
兼容性：Terminology Registry 结构、Project State、Title Claim、公开 CLI 和报告接口不变；旧稿不批量迁移。  
遗留问题 / 下一阶段：W1-P2 已闭合；当前进入 Part D。Part C 除核心证明外仍 PARTIAL，Part D 完成后必须先回补 Part C 非证明型核心推导，再决定 E/F；W0/W3 检查减重仍单独实施。

### D-P1：表格与图表可读性

阶段 / PR：Part D 原子修改 / PR #196 — `fix: make tables and figures easier for judges to read`  
Base main SHA：`bf9c7d1a3cb6270f24db99c28ed1104c1d0b781b`；Final head：`5269a506ad84d6182c97088963b97829e0c2a51f`；Merge SHA：`b1b92eb31d444058a33a5e72a8ea8796dc1b28ec`。  
本次获批范围与 Authority：依据 Part D，表题、表头、行名、单位、指标方向、比较条件及图题/轴/图例/正文解释要让评委独立读懂；可读性不得改变 accepted 数值和口径。Authority 复用 `core/writing_reasoning_contract.yaml#model_establishment_solution_narrative`，在既有 `figure_result_narrative` 下补职责分工，并新增同层 `table_result_readability`，不另建新合同。  
实际修改范围：Writing Reasoning Authority、Paper Writing Protocol、AI Cleanup、Review、caption/table 执行模板、DOCX checklist 与既有 writing/review/drift regression。Module 04 Figure Evidence、MATLAB、Workbook/Output、Runtime、Schema、CLI、Gate、模型审批不改。  
核心裁决：表题说明对象/比较内容/范围；行列使用可读名称并保留必要符号/追踪 ID；单位、无量纲、baseline、样本/时间/场景、指标方向按需说明；图题—轴/图例—正文和表题—表头/行名/表注—正文职责分离；一张表通常服务一个主要比较问题。  
数值保全：显示层调整不得改变 accepted 数值、单位、百分比/百分点、绝对/相对误差、排序规则、Numeric Profile 精度或题面指定工作簿/提交格式。  
Review：继续复用 `figure_table_information_value`，不新增 Readability Gate 或第九个 coverage family；机器不得仅凭列数、标题长度、指标名或字符串相似度判断语义质量。  
Part C 依赖：本 PR 不宣称 Part C 完成；Part C 非证明型核心推导仍列为必须回补项，PR #196 完成后优先执行。  
静态测试 / 真实执行 / 生成文件：final head HSK Skill CI workflow_dispatch #3693 与 Optimization baseline #297 均 success；合并后 main HSK Skill CI #3695 与 metadata #2455 均 success。PR-triggered #3694 的 failure 不作为通过证据，最终验收绑定上述 successful exact-head run 与合并后 main。  
兼容性：Project State、Terminology Registry、Numeric Profile、Title Claim、公开 CLI/报告接口不变；旧论文不批量迁移。  
遗留问题 / 下一阶段：Part D 已闭合；当前按既定顺序返回 Part C，PR #197 回补非证明型核心推导正文闭环；不得直接跳 E/F。

### C-P2：非证明型核心推导正文闭环

阶段 / PR：Part C 原子修改 / PR #197 — `fix: keep nontrivial core derivations recoverable in the body`  
Base main SHA：`b1b92eb31d444058a33a5e72a8ea8796dc1b28ec`；Final head：`81e058c294a2d12dda79c73278c7fd1b121fdd42`；Merge SHA：`a3ceba47f633b25562d53d24b4e0c4b5438e5a4a`。  
本次获批范围与 Authority：补齐 Part C 除 PR #194 核心证明之外的正文推导责任。Authority 为 `core/writing_reasoning_contract.yaml#formula_reasoning_chain.core_derivation_body_closure`；Formula Role 枚举与 Core Formula Trace 接口保持不变。  
正文必须可恢复：题目条件/基本规律→变量关系、控制方程、目标/约束/指标；关键假设/变换/参考系/对称化简/降维/分解；非平凡初边值/可行域/必要充分条件；影响主结果的关键离散/误差关系、事件判据、搜索区间与 solver 前提；后问新增/改变推导。  
压缩边界：机械代数、重复代入、批量同型展开、完整代码/日志、重复系数、非主线补充实验与不承担主论证闭环的扩展推导仍可压缩或外置；但“篇幅长/不是最终公式/supporting_derivation/代码可复现”不能单独作为外置理由。  
共享与标准定理：前文已完整推导的共享模型可准确回指，后问只展开新增部分；标准定理可引用但必须核验本题条件并说明如何进入模型/边界/solver。  
Consumer：Paper Writing Protocol、AI Cleanup、Review、DOCX checklist；不新增 Runtime Gate、Project State required 字段或新的 Trace/Review schema。  
检查减重候选：本 PR 不处理。  
Part C 完成条件：PR #194 + PR #197 共同覆盖证明与非证明型核心推导；PR #197 final head CI、Optimization baseline 及合并后 main CI 均成功后才将 Part C 标为 COMPLETED。  
静态测试 / 真实执行 / 生成文件：final head HSK Skill CI workflow_dispatch #3716 与 Optimization baseline #310 均 success；合并后 main HSK Skill CI #3718 与 metadata #2469 均 success。PR-triggered #3717 没有产生可用 job，不作为验收依据。  
兼容性：模型、数值、工作簿、Runtime/Router/Resolver、Schema、CLI/Gate、MATLAB、Part D 图表规则及 Part F 标题层级均不变。  
完成结论：PR #194 + PR #197 已覆盖 Part C 的证明与非证明型核心推导；当前 `main@a3ceba47f633b25562d53d24b4e0c4b5438e5a4a` 可将 Part C 标记为 COMPLETED。  
遗留问题 / 下一阶段：按计划进入 Part E“公式多时仍保持清晰叙事”；Part F/G 与 W0/W3/W4/W5 仍未完成，不能把整份计划标为 completed。

### E-P1：公式多时保持清晰叙事

阶段 / PR：Part E 原子修改 / PR #199 — `fix: keep formula-rich mathematical narrative readable`  
Base main SHA：`ff1996ca46017e24baa0169bf88c7bfb2df73fe8`；Final head：`4697e689c305d871d8f6b868c2008e76ec9bd0d7`；Merge SHA：`23befe4d6580435646ee6b60388e3bb08d4ba7eb`。  
本次获批范围与 Authority：依据 Part E，公式密集正文应让评委恢复当前对象、数学缺口、引式依据/推导、结构作用与下一用途；关键成立条件/近似范围/定义域/局部性/失效边界贴近对应公式。Authority 复用 `model_establishment_solution_narrative.continuous_mathematical_narrative` 与 `formula_prose_rhythm`，不新建写作合同。  
实际修改范围：Writing Reasoning Authority、Paper Writing Protocol、AI Cleanup、Review 与既有 writing/drift regression。未修改 Runtime、Project State、Schema、CLI/Gate、模型/数值、Workbook、MATLAB、Part D 图表与 Part F 标题层级。  
核心裁决：一个自然段可承载直接依赖的多个推理动作；互不相关的模型选择、solver 介绍、指标定义、结果解释不压成信息过载长句；分段按对象/数学依赖/证据角色/下游任务，不按字符数、句数、公式数或版面长度硬切。  
Part C 保全：Part E 只优化阅读组织，不得删除 Part C 要求保留的非显然核心推导、关键条件、桥接或证明。  
机器边界：仅提示 `formula_condition_or_applicability_detached_from_use` / `paragraph_mixes_unrelated_reasoning_units` 等风险；不得从字数、句数、公式数、连接词推断可读性或数学完整性。  
静态测试 / 真实执行 / 生成文件：final head HSK Skill CI workflow_dispatch #3785 与 Optimization baseline #337 均 success；PR-triggered HSK Skill CI #3786 为 `action_required`，按仓库既有触发机制不作为通过证据；合并后 main HSK Skill CI #3787 与 metadata refresh #2501 均 success。  
兼容性：无新 Gate、无新 Project State 字段、无 readability score、无固定句式或段落长度阈值。  
完成结论：Part E 已在 final head 与合并后 main 双重验收下闭环，且 Part C/D 保全未受影响。  
遗留问题 / 下一阶段：进入 Part F“正式章节最大三级”；Part G 与 W0/W3/W4/W5 仍后续实施。

### F-P1：正式章节最大三级

阶段 / PR：Part F 原子修改 / PR #200 — `fix: cap formal paper headings at semantic level three`。  
Base main SHA：`8fb72f6e73a245f101690d01e9db82064206d48b`；Final head：`1b1da84e2788bd4894273b9e310b743e6441c26a`；Merge SHA：`0d8b44c0c26ad7694638da468d457df76ded08ce`。  
本次获批范围与 Authority：依据 Part F，一级、二级、三级标题均为正常可用层级；三级不是例外权限或数量配额，正式章节禁止四级及以上。Authority 进入 `model_establishment_solution_narrative.within_question_subsection_architecture.formal_heading_depth_policy`，不新建独立写作合同。  
实际修改范围：Writing Reasoning Authority、Paper Writing Protocol、AI Cleanup、Review、LaTeX/DOCX adapter、正式 LaTeX 审计与既有 writing/LaTeX regression。现有 CUMCM/MCM/ICM/电工杯活动模板本身已停在三级，不为完成计划机械改模板正文。  
核心裁决：LaTeX `section/subsection/subsubsection` 映射一至三级；活动正文 `paragraph/subparagraph`（含星号形式）若承担正式章节即阻止交付。Markdown/DOCX 按最终论文语义/outline level 映射；不全仓搜索 `####`，不把维护文档、注释、代码示例、宏定义、证明分情况、算法步骤或表内分组误判为第四层。  
三级保全：三级标题数量不设硬上限；不能因多个三级标题自动压回二级。三级以下复杂推理改用自然段、公式组、证明分情况或算法步骤，不通过加粗独立行、列表或无编号子标题伪装第四层，也不得借三级上限删除 Part C 核心推导。  
机器边界：明确可解析的活动正式 LaTeX 四级及以上为 deterministic blocking；自定义宏/样式真实层级无法判断时进入 review_required，不从宏名或字体外观猜测。  
静态测试 / 真实执行 / 生成文件：final head HSK Skill CI workflow_dispatch #3805 与 Optimization baseline #343 均 success；PR-triggered HSK Skill CI #3806 为 `action_required`，不作为通过证据；合并后 main HSK Skill CI #3807 与 metadata refresh #2509 均 success。  
兼容性：不新增 Gate、Project State required 字段、报告 schema 或标题数量指标；一级骨架仍由 Template Manifest 管理。  
完成结论：Part F 已在 final head 与合并后 main 双重验收下闭环，三级正常可用、四级及以上禁止的跨载体与正式 LaTeX 检查链已稳定。  
遗留问题 / 下一阶段：按计划进入 Part G；Part G 完成后必须先补齐 W0 检查调用/成本/正反例基线，再进入 W3，不能直接删检查器。

### G-P1：复用现有审查，不增建 Gate

阶段 / PR：Part G 原子修改 / PR #201 — `test: prove readability reuses the existing review pipeline`。  
Base main SHA：`0d8b44c0c26ad7694638da468d457df76ded08ce`；Final head：`692e970a32adfbb95ea1380fa72fe65fdef510b9`；Merge SHA：`f489934efd633b1c5c5dc0930858aa4c49f6ca3a`。  
本次获批范围与 Authority：严格按 Part G §9 与实施规则 §10；draft review 发现理解障碍，Cleanup 只修表达，final review 在既有全篇 coverage 内复验；不得新增 `readability_status`、Project State required 字段、新注册表、独立 Readability Gate 或第九个 coverage family。  
现状裁决：读取 current Review、Writing Runtime、Cleanup、review matrix、score/lint 与 Project State 后，现有 active interface 已满足 Part G：`draft_semantic_review → ai_cleanup → final_review_and_delivery` 顺序已存在；终审稳定 coverage 仍为八类，`rendered_page_surface` 与 `figure_table_information_value` 已承载相关可读性证据；finding 已区分 `machine / manual / hybrid`；内部审查记录明确不进入 Project State。  
实际修改文件及未修改原因：按 §10“若现有能力已满足，用测试证明后保持原样”，不修改 Review、Runtime、Cleanup、review matrix、score schema、Project State 或 Gate；仅扩展既有 `tests/test_v820_final_review_compliance.py` 固化上述不新增接口边界，并更新本计划状态/证据。  
检查减重候选的逐项裁决：Part G 不执行 W3 减重，不降低任何 Hard/Default severity；R7/R8 仍留给 W0 完整基线与 W3 逐候选裁决。  
核心推导、数值与三级层级保全结果：Part C–F 规则保持；本阶段不改模型、数值、工作簿、标题层级或 LaTeX 审计语义。  
静态测试 / 真实执行 / 生成文件：final head HSK Skill CI workflow_dispatch #3811 与 Optimization baseline #345 均 success；PR-triggered HSK 为 `action_required` 不作为通过证据；合并后 main HSK Skill CI #3813 与 metadata refresh #2512 均 success。  
兼容性与实际成本变化：零运行接口变化、零 schema/gate/family 增量；本阶段未宣称性能收益。  
完成结论：Part G 已闭环，现有 draft review / Cleanup / final review 管线继续作为唯一可读性审查载体。  
遗留问题 / 下一阶段：按计划进入 W0 完整基线；必须先完成检查对象/调用者/输入指纹/阶段/severity/调用次数耗时/测试覆盖/正反例裁决表，再进入 W3。

### W0-P1：检查调用、成本与正反例基线

阶段 / PR：W0 完整基线 / PR #202 — `test: establish writing-validation W0 baseline`。  
Base main SHA：`f489934efd633b1c5c5dc0930858aa4c49f6ca3a`；Final head：`1604edba0d02afb15202cd0a0da748aba64a17ed`；Merge SHA：`cef433c513b3ab384702c1057adf5502788b99b9`。  
本次范围：严格执行 §5.2 与 §10 的 W0 前置要求，只建立调用图、输入阶段/指纹、severity、调用次数/耗时、测试与正反例证据，不删除脚本、不降级检查、不改 Gate/Schema/Runtime 语义。  
测量入口：新增 maintenance-only `scripts/measure_writing_validation.py`；计时仅作证据，不设阈值、不成为 Gate。配对样例复用/扩展现有 prose audit 测试，覆盖 R7 的 count-only 小节复核、Result→Validation bridge、solver-first 和功能次序。  
R8 调用图结论：draft 阶段直接运行 `audit_v8_writing_surface.py`；Cleanup 与 LaTeX assembly 后，formal route 由 `audit_latex_project.py → audit_paper_prose.py → audit_v8_writing_surface.py` 再审。两次 surface 输入阶段不同，禁止跨阶段缓存复用；formal 内部只嵌套一次 surface audit。  
实际测量：Optimization baseline #347，head `8c543f9c6a0966d84f7a357a7fc3c12069c8f5bb`，Python 3.12.14 / Linux Azure，30 次计时 + 5 次 warmup；small/medium/large 三档 fixture 分别为 761 / 3659 / 12344 bytes。完整结果见 `docs/writing_validation_w0_baseline.md`。  
裁决：跨阶段 surface 复验保留；formal→surface 嵌套保留；surface 内部重复预处理虽实测为 4/6/9 次，但 12.3 KB 大样例 direct surface median 仅 9.7019 ms，当前拒绝为此引入共享 context/cache。R7 仅 `question_subsection_granularity` 的“二级小节 >4 即 review_required”被证实为 W3 候选：独立数学任务正例仍被误报，而机械拆分已有更具体 `possible_mechanical_model_subsection_split` 证据。其余三项 surface review_required 均由成对正反例证明有区分度，保留。  
静态测试 / 真实执行 / 生成文件：final head HSK Skill CI #3816 与 Optimization baseline #348 均 success；W0 实测 artifact 来自同分支 intermediate head 的 Optimization baseline #347；合并后 main HSK Skill CI #3818 与 metadata refresh #2516 均 success。  
完成结论：W0 维护证据已闭环，只批准 `question_subsection_granularity` 的 count-only review finding 进入 W3。  
遗留问题 / 下一阶段：W3 只能处理该单一候选；不得扩大到未取证 severity、Runtime、Gate、Schema、缓存或其它 review_required。

### W3-P1：移除 count-only 小节数量复核

阶段 / PR：W3 最小减重 / PR #203 — `fix: remove count-only subsection review finding`。  
Base main SHA：`cef433c513b3ab384702c1057adf5502788b99b9`；Final head：`a74079882158bff693cd083f3abc2c1e8abada1e`；Merge SHA：`491fac0af1f77eb91e64f32e21ae21abcc442b4e`。  
本次获批范围：严格消费 `docs/writing_validation_w0_baseline.md#6-W3-唯一已批准候选`，只移除 `len(subsection_titles) > 4` 触发的 `question_subsection_granularity` review_required。  
实际修改范围：`scripts/audit_paper_prose.py` 删除 count-only finding；更新既有 v7.16/v7.45 回归和 maintenance measurement 当前期待；不修改 `config/prose_audit_patterns.yaml`、surface audit、Runtime、Review、Gate、Schema、Project State 或报告结构。  
保留检查：`possible_mechanical_model_subsection_split` warning 继续识别变量/目标/约束/汇总机械拆分；`framework_subsection_granularity_pending` review_required 继续拦截框架中显式未闭合的小节颗粒度状态；其它 W0 保留项 severity 全部不变。  
Hard 保全：duplicate label、missing reference/BibTeX、claim-scope 冲突等既有 blocking 路径不改；formal audit 入口与 strict 对 remaining review_required 的处理不变。  
兼容性：public CLI、Finding 数据结构、报告键、Runtime/Gate/Project State 不变；仅不再产生一个已证明 count-only 误报的 finding code。  
静态测试 / 真实执行 / 生成文件：final head HSK Skill CI workflow_dispatch #3822 与 Optimization baseline #350 均 success；PR-triggered #3823 为 `action_required`，不作为失败证据；合并后 main HSK Skill CI #3824 与 metadata refresh #2519 均 success。  
完成结论：W3 已闭环，只删除已证明 count-only 误报；其它 review_required、formal audit 与 Hard 路径保持。  
遗留问题 / 下一阶段：按总实施顺序先正式闭合仍标 IN_PROGRESS 的 W2，再进入 W4；不得借 W2/W4 扩大检查减重范围。

### W2-P1：Consumer、模板与样例闭环验收

阶段 / PR：W2 closure / PR #205 — `test: close writing consumer and template alignment`。  
Base main SHA：`491fac0af1f77eb91e64f32e21ae21abcc442b4e`；Final head：`e990bb8afa0d703245f33b87721f824229dc6200`；Merge SHA：`0242bb8d4d6b94dab7b14773940e92e8c692e99d`。  
本次范围：严格按 §10 W2 完成条件检查 Cleanup/Review/Pack/Template/例文的实际承载，不再改写已经稳定的 C–F Authority。按“现有能力已满足则用测试证明后保持原样”执行。  
完整读取与裁决：长核心证明由 `packs/artifact/proposition_proof.md` 明确允许命题框后接 standalone `hskproof` 并正常分页，活动 preamble 已提供独立 `hskproof`；CUMCM Q2 模板已有多个正常 `subsubsection` 示例且明确不设固定名称/数量；模型建立与求解论证例文同时保留紧凑型与导航型 Profile；表格可读性由 caption template 与 DOCX checklist 落到 run id、指标方向、accepted 数值和过宽表处理。  
实际修改：不修改上述业务文件；仅扩展既有 writing evidence regression，把 Pack→preamble→Q2 template→rationale examples→caption/DOCX checklist 的具体输出载体锁成一个集成断言，并更新本计划状态。  
兼容性：不新增模板骨架、示例库、Gate、Schema 或 Runtime 读取；不把 CUMCM 一级骨架扩散到其他载体。  
静态测试 / 真实执行 / 生成文件：final head HSK Skill CI #3826 与 Optimization baseline #351 均 success，CUMCM/MCM-ICM/电工杯 LaTeX smoke、Production LaTeX attestation 与 generated-file contract 均 success；合并后 main HSK Skill CI #3828 与 metadata refresh #2521 均 success。  
完成结论：W2-P1 已证明 Consumer/Pack/Template/例文静态与常规模板执行对齐，但计划 §7.4 还要求长核心证明方案具备真实 LaTeX 渲染与引用/编号证据，因此 W2 暂不标 COMPLETED。  
遗留问题 / 下一阶段：先完成 W2-P2 长核心证明真实分页验收，再进入 W4 T01–T18；不得以静态 token 检查替代该渲染要求。

### W2-P2：长核心证明真实 LaTeX 分页与引用验收

阶段 / PR：W2 real-render closure / PR #206 — `test: render long core proof across pages`。  
Base main SHA：`0242bb8d4d6b94dab7b14773940e92e8c692e99d`；Final head：`7bf2e2c3e31319544d93512ab23ceaffb05e6620`；Merge SHA：`f3946972f246cc145796558a8c115062d435ecb3`。  
计划依据：严格执行 §7.4“长证明的解决方式必须有真实 LaTeX 渲染和引用/编号测试”，以及 T04“核心证明超过半页时正文完整证明可连续阅读并正确分页”。  
实际修改：不改 Proposition Pack、Writing Authority 或活动 preamble 业务语义；仅在现有 Production LaTeX attestation 中增加临时 CUMCM 长核心证明 fixture，直接复制 current `config/preamble.tex`，把命题陈述留在 `hskproposition`，完整证明置于框外 standalone `hskproof`。真实编译后从 AUX 核对命题/最终公式 label 均存在且最终公式页码大于命题页码，并拒绝 unresolved reference/citation；失败时保留 proof-specific audit/compile/log/aux diagnostics。  
测试保护：扩展既有 `tests/test_content_packs.py`，确保真实渲染步骤、命题/公式 label 和跨页页码断言不会被后续维护静默删除。  
兼容性：不新增 Runtime Gate、Project State、报告 schema、模板正式章节、用户必交文件或跨运行缓存；只加强现有 CI 验收，不裁剪任何现有 job。  
静态测试 / 真实执行 / 生成文件：final head HSK Skill CI workflow_dispatch #3832 与 Optimization baseline #353 均 success；Production LaTeX attestation 中 `Render long core proof pagination and numbering fixture` success；PR-triggered #3833 为 `action_required` 不作为失败证据；合并后 main HSK Skill CI #3834 与 metadata refresh #2524 均 success。  
完成结论：W2-P1 + W2-P2 已共同满足 §10 的 Consumer/模板/样例实际输出条件与 §7.4 长证明真实渲染要求，W2 可标 COMPLETED。  
遗留问题 / 下一阶段：进入 W4 T01–T18 集成验收；W4 只补行为证据和语义审阅记录，不重复修改已闭环 C–F 业务政策。

### W4-P1：T01–T18 集成行为验收

阶段 / PR：W4 integrated acceptance / PR #207 — `test: integrate writing readability W4 acceptance`。  
Base main SHA：`f3946972f246cc145796558a8c115062d435ecb3`；Final head：`06ace7b99bd7977b74c34fc9f7e554b16f576318`；Merge SHA：`e8fd923e6273b9fe644d506ecc8c3b3372d7e4a6`。  
本次范围：严格按 §10 W4 与 §12/T01–T18，把现有 Authority/Consumer/audit/CI 的正例、反例、跨文件与跨载体证据汇总为一个集成验收；不新增 Gate、required 状态、coverage family 或新的业务规则。  
实际修改：新增维护证据 `docs/writing_readability_w4_acceptance.md` 与一个聚焦集成回归 `tests/test_v931_writing_readability_w4_acceptance.py`。测试复用现有 audit / Runtime / DOCX / Review 接口，覆盖三级正例、四级反例、非活动文本排除、W3 count-only 边界、Terminology/Numeric drift、wording/semantic stale 分界、跨载体 fallback 与 Hard blocking 保全。  
语义审阅边界：维护记录中的语义判断不是独立评委、用户或第三方反馈；未编造“评委已验证”。机器不能判定的推导完整性、术语解释充分性、表格语义继续按 Review 的 manual/hybrid 边界记录。  
兼容性：不改模型/数值/工作簿、Runtime stage、Review schema、Project State、formal Gate、CLI 或 report shape。  
静态测试 / 真实执行 / 生成文件：final head HSK Skill CI workflow_dispatch #3838 与 Optimization baseline #355 均 success；Python 3.10–3.14、Static lint、Generated file contract、CUMCM/MCM-ICM/电工杯 LaTeX 与 Production LaTeX attestation 全部 success；PR-triggered #3839 failure 不作为 final-head 通过证据；合并后 main HSK Skill CI #3840 与 metadata refresh #2527 均 success。  
完成结论：T01–T18 已有机器/语义/hybrid 正反边界和跨载体证据，Hard 集合与既有 review 八类 coverage 保全，W4 可标 COMPLETED。  
遗留问题 / 下一阶段：进入 W5 综合回归、版本/release 裁决与计划收尾。

### W5-P1：v9.4.0 Release Closeout

阶段 / PR：W5 release closeout / PR #208 — `release: publish v9.4.0 writing readability closeout`。  
Base main SHA：`e8fd923e6273b9fe644d506ecc8c3b3372d7e4a6`；Final head：`81492db887439a6afffa4f9e36702f4b686c5f67`；Merge SHA：`551054e695a11a8f49399619b833635577b7215e`。  
发布裁决：依据 `SKILL_CHANGE_GOVERNANCE.md`，本轮已新增向后兼容的写作/审查能力而非仅修复单一缺陷，因此从 9.3.1 升为 **9.4.0 minor**；未改变目录、Schema、CLI、required state、Model Approval、数值/工作簿或用户执行接口，不构成 major。  
实际修改：只统一活动 release carriers、README/CHANGELOG/维护状态、release regression 与本计划状态；不重写 W1–W4 已合并业务实现。新增 `docs/writing_readability_w5_release_closeout.md` 记录版本依据、兼容边界和最终验收要求。  
兼容性：旧项目继续读取；无批量迁移；W3 只移除已证明 count-only 误报，其余 review/Hard 路径保持；MCM/ICM、电工杯、DOCX 不强套 CUMCM 骨架。  
正式验收：final generated head `81492db887439a6afffa4f9e36702f4b686c5f67` 的 HSK Skill CI workflow_dispatch #3843 与 Optimization baseline #356 均 success；Python 3.10–3.14、Static lint、Generated contract、CUMCM/MCM-ICM/电工杯 LaTeX、Production attestation（含长核心证明真实分页）全部 success。PR #208 合并为 `551054e695a11a8f49399619b833635577b7215e` 后，main HSK Skill CI #3845 与 metadata refresh #2529 均 success。  
完成结论：v9.4.0 release carriers、发布说明、综合回归与 main 后验全部闭合，W5 与整份计划均标记 COMPLETED；无后续计划阶段，任何新需求应按新的独立修改简报/PR 进入。

后续每个实施 PR 在本节追加记录，不重写历史裁决：

```text
阶段 / PR：
Base main SHA / Final head SHA / Merge SHA：
本次获批范围与 Authority：
实际修改文件及未修改原因：
检查减重候选的逐项裁决：
核心推导、数值与三级层级保全结果：
静态测试 / 真实执行 / 跳过或缺失环境：
生成文件状态：
兼容性与实际成本变化：
遗留问题 / 停止原因 / 下一阶段：
```

该记录只用于仓库维护，不新增用户赛题必交材料。计划完成状态以实际实现和验收为准；不能仅因全部段落写齐或规划 PR CI 通过就将 W1–W5 标为完成。

## 16. 后续接续指令

> 先读取最新 main 的 bootstrap、修改治理、本计划和相关 Authority，核对开放 PR、基线漂移与用户实施授权。先做 W0，输出检查候选裁决和测试依据；不要直接删检查器。落实 C 时必须保护正文完整非显然推导，不能因篇幅/框高将核心证明移附录。落实 F 时一级至三级正常可用，四级及以上禁止；不要把三级重新写成例外，也不要限制标题数量。复用现有 Writing/Review/Runtime 结构，不新增 Readability Gate、required 项目字段或全量预读。每个 PR 自身保持 Authority—consumer—测试一致，全部真实验收通过后再合并；本计划是实施依据，不是新的业务权威。
