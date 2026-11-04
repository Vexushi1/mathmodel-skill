# AI Cleanup 单一语言润色职责与数学内容只读保护：详细改造计划（Plan Only）

> **状态：规划已起草，功能未实施。** 本文件只记录未来修改方案，不是新的运行时 Authority，不代表源代码已经改造或通过验收。  
> **仓库：** Vexushi1/mathmodel-skill  
> **编制日期：** 2026-11-04  
> **实查基线：** main@269186ce76d7d9912c6b2d17687835407f300a17，Skill v10.25.0。  
> **待继承的并行改动：** [PR #292（B1–B4、开发 v10.26.0）](https://github.com/Vexushi1/mathmodel-skill/pull/292)，实查 head f521865eabd0b0a4c1a5ffc0b24a75670d6172d7，检查时尚未合并。  
> **本计划优先级：** 必须在 #292 最终合并并通过 main 验收之后，基于新的 main 对齐；若 #292 被取消，则以实际 main 重新裁决。不能把本计划直接应用到历史 main，也不能在 #292 开放时并行写入重叠写作 Authority。  
> **用户授权边界：** 用户同意“Cleanup 只润色语句、降低 AI 模板感、删除空话套话，已经整理好的数学公式与推导不动”，并要求本轮仅拟订额外计划。**未授权本轮执行功能改造、合并或发布。**

## 0. 修改简报（SKILL_CHANGE_GOVERNANCE.md §3）

| 字段 | 约定 |
|---|---|
| 修改主题 | AI Cleanup 从“表达清理 + 部分数学/结构裁决”收束成“自然语言润色；数学、推导、结构及事实内容默认只读” |
| 当前 Skill 版本 | main v10.25.0；#292 仍为开发 v10.26.0 |
| 本计划变更等级/版本 | docs / 不升级；未来功能 PR 依据**实施时**最新 main 和是否向后兼容决定 patch/minor，不能预占版本号 |
| 直接目标 | 把“能改语言、不能改数学”的可操作边界写清；不复制其他 Authority；保留证据、数学、引用和公式保护；消费者与测试一起同步 |
| 明确不做 | 不改模型、证明、方程、求解算法、Numerical Profile、accepted workbook、Preflight 状态、Figure Evidence、Chapter Handoff 语义、目录/Schema、模型批准、用户执行边界和真实论文数据；不做用户论文全篇自动改写 |
| 权威事实源 | core/bootstrap.yaml；SKILL_CHANGE_GOVERNANCE.md；core/writing_runtime_contract.yaml；modules/05_writing/paper_writing_protocol.md；core/writing_reasoning_contract.yaml；modules/05_writing/ai_cleanup.md |
| 结构和消费者 | core/workflow_router.yaml；core/module_manifest.yaml；modules/06_review_delivery.md 与 modules/06_review/content_review.md；modules/05_writing/latex.md；scripts/lint_skill_checks.py；相关 writing/review/reading/test |
| 计划改造文件 | Cleanup 主文；Runtime 的现有 ai_cleanup stage 描述（必要）；直接依赖旧语句的 lint/test/fixture；极少量 Review 引用（确有缺口才改） |
| 禁止触碰 | 既有 accepted 事实、数值/绘图生产者、用户项目、历史发布 Tag、机器 gate 数量和源码签名；MANIFEST.sha256 与受管索引不手工编辑 |
| 兼容与迁移 | 保持原写作阶段名称、read_now/write_now 输出、CUMCM/MCM/ICM/DOCX 路由与历史项目可读；旧论文不批量重写 |
| 验收 | 单一职责/完整性与负例测试、旧测试等价保护迁移、阅读路由投影、正式双 Windows Python 回归、静态/生成检查和适用的 MATLAB/Figure/LaTeX/Optimization 远端验证 |
| 回滚 | 独立功能 PR 原子 revert；保持当前成果、模型批准、accepted 数值和后续可读取性不变 |

## 1. 已核实的仓库现状与问题根源

### 1.1 现有写作链与职责

实际 Runtime（core/writing_runtime_contract.yaml#template_first_progressive_authoring.stages）已有以下顺序：

~~~text
当前项目事实/论文框架 + Template/Protocol/Reasoning
  → 按小问写好数学内容和正文
  → draft_semantic_review：数学、证据、段落与结构先审
  → ai_cleanup：当前目标文件和 resolved findings 的表达清理
  → latex_assembly_audit_and_compile：装配/审计/编译
  → final_review_and_delivery：最终检查及交付
~~~

- **Reasoning Authority**（core/writing_reasoning_contract.yaml）已有 Formula Role、核心推导、证明、Algorithm Trace、Claim Strength、数值精度、引用语义。
- **Prose Authority**（modules/05_writing/paper_writing_protocol.md）已有模型建立、求解、RESULT→VALIDATE、图表结果、章节标题/段落逻辑。
- **Runtime Authority**（core/writing_runtime_contract.yaml）已有 read_now→write_now→gate、按状态补读、Preflight、draft-before-cleanup 和 cleanup-before-compile。
- **Cleanup consumer**（modules/05_writing/ai_cleanup.md）本应只修语言，却仍自行定义公式 Keep/Compress/Re-locate/Delete、Core Derivation Body Closure Test、标题 Merge/Split、表格内容和数值格式。
- **Review consumer**（modules/06_review_delivery.md 与子模块）已有审查分级、范围和 formal delivery；不应为 Cleanup 新建审稿状态、门禁或检查族。
- **LaTeX Adapter**（modules/05_writing/latex.md）只管理载体；数学内容不能因为 Cleanup 变为第二套 LaTeX 生成任务。

### 1.2 具体的权限冲突

1. Cleanup §B1 允许依公式角色压缩或迁移部分支持性推导；用户当前的明确目标是**已经定稿的数学内容在 Cleanup 全程只读**。是否缩减推导应在 Cleanup 之前的写作/数学审查阶段完成。
2. Cleanup §C4 提供标题压缩与 Merge/Split 规则；用户要的是语句润色而非重构标题/章节。结构判定属于 Protocol/Runtime 的早期写作阶段。
3. Cleanup §B3 允许统一 Numeric Style；这应由已经确定的项目 Numeric Profile/数值 Authority 管理。Cleanup 不应自主执行任何数值格式重写，即使表面精度看起来满足默认。
4. Cleanup §C3 包含表头、caption、Figure role 和表格拆分判断；这属于上游图表/写作，不应作为自然语言润色权限。
5. 当前文件重复罗列大量数学合法性、算法适用性和诊断边界，导致消费者变大且随着写作 Authority 漂移。
6. 不能只删旧文：大量 tests/lint 仍按 Cleanup 中的历史固定短语断言，简单删段落会引发回归，同时可能掩盖真实的保护能力损失。

### 1.3 与 #292 的先后关系

#292 在 Cleanup §B3 增补了“普通非关键说明性数值可建议两位小数”的消费者规则，并在 §C3 补充了深化分析的回收引用；同时修改 Protocol/Reasoning 和一批测试。本计划**不否定 #292 的正式数值与结果深化规定**，而是将这些规定继续保留在各自 Authority，Cleanup 在下游只读和引用，不再实施格式改写。#292 中 tests/test_v10260_cumcm_writing_narrative_b.py 的 Cleanup 固定短语断言也必须在未来实施时同步迁移。

## 2. 目标行为契约：只改自然语言，不编辑数学内容

### 2.1 默认可编辑内容（且必须语义保持）

- 与公式、证明、约束或主张无直接推理作用的普通衔接句、重复预告、空泛管理句、套话、算法百科式铺垫。
- 不携带条件/因果/数量口径的冗长表达，允许调整语序、分句、措辞和中文标点，使其自然、准确、学术化。
- 表达已经被原文真实支持、且不改变主张强度的结果说明；删去“如表所示”式重复叙述时，保留唯一的实际结论、引用和必要限定。
- 不要求引入“我们认为”“值得注意的是”等假自然句，不靠第一人称、连接词频率、固定短句模式或所谓 AI 分数判断成功。

### 2.2 默认严格只读的保护对象

**不能只锁定公式环境而放开推导文字。** 下列内容在 Cleanup 视为同等受保护：

1. **数学源码与显示：** 所有内联/行间公式、LaTeX math 环境、符号、上下标、集合、条件、目标、约束、边界、定义、单位、数值和精度；不得变换等价形式、重编号、移动、合并、拆分或删除。
2. **文字推导：** 承担“前提→转换→结论”、证明步骤、可行性/凸性/等价性、近似或误差界、solver 前提、Reduction Provenance 的句子和段落；即使只有中文、没有公式也只读。
3. **证明与算法：** 命题、引理、证明、伪代码、关键算法步骤、流程判据、初始化/停止条件、Algorithm/Formula Trace 的实质表述；不能因“写得太长”自行改写。
4. **证据和主张：** 数值结果、表格值、已有术语定义、条件与结论强度、有效范围、误差/统计含义、引文支持范围，不得擅自推高或减弱。
5. **源文件结构：** 章节标题及层级、正文顺序、表格和图、caption/表头/图例、标签与引用命令及其 key、交叉引用锚点、文献键、LaTeX 控制结构和源码文件边界；默认不做修改。
6. **项目事实：** current/accepted 事实与状态、Human Model Approval、既有论文图表和证据身份；Cleanup 绝不改这些事实源。

其中数学内容包含混在自然语言里的关键限制词（如“仅在”“至少”“必要”“充分”“局部”“近似”“不大于”）。普通润色不得把这些词改掉以制造顺畅语句。

### 2.3 界限不清、发现错误和另行授权

- **无法确认一段是否承担推导/主张功能：保留原文，并指出可疑位置。** 不以 AI 的等价性判断作直接替换依据。
- 发现数学笔误、变量冲突、证明缺口、错误单位或不一致数值时，只在既有 review finding/对话中报告，并交回对应写作或数学审查阶段；不能在 Cleanup 中顺手纠正。
- 用户将来明确要求“修改公式/推导/标题”时，先按该请求重新路由到相应 Authority，不把这种任务伪装为一次更宽松的 Cleanup。
- 不要求为每个句子创建新 ID、hash、审计台账或人工批准点；复用已有版本控制、当前片段和 Draft/Final Review。

### 2.4 精简后建议的 05C 主文骨架（非本轮实际改写）

~~~text
# Module 05C：AI 语言润色与模板感清除
0. 定位、输入与权限：只改普通自然语言；前置 draft review 已闭合
A. 数学/结构/证据只读边界：简短硬规则 + 相关 Authority 引用
B. 自然语言清理：空话套话、机械重复、句式与衔接、图表附近的非关键表达
C. 遇到争议/错误：不自行改，交回原写作/审查阶段
D. 改写后对照：数学/引用/结构未变，语言更清楚，结果主张未越界
~~~

不再在 Cleanup 复述完整公式四分类、五项核心推导检查、Heading Compression Test、图/表显示职责矩阵、两位/六位小数规则或机器审查算法。必要名称可以作为**引用**出现，定义仍归原 Authority。原文中真正独特的“反模板”“语句必要性”“不根据词频判断像人”保留。

## 3. 单一 Authority 与消费者同步矩阵

| 文件/组件 | 应做的动作 | 为什么 |
|---|---|---|
| **modules/05_writing/ai_cleanup.md** | **必须改**：重写为语言-only 权限、只读边界、争议回退与改后检查；保留具体删套话能力 | 唯一直接目标；不做数学决策 |
| **core/writing_runtime_contract.yaml** | **优先审查并预计最小改**：ai_cleanup stage 的 gate 明确“公式/推导/标题/结构保持不变”，保留原 read_now、write_now、stage ID、前后顺序 | 当前 stage 虽要求不删推导，仍可能让“无损压缩数学内容”进入 Cleanup |
| **modules/05_writing/paper_writing_protocol.md** | **先核查，原则不改**；若缺少“推导压缩只在前置写作审查完成”的约束，限定在其已有 Formula Roles/段落必要性处增一条准确说明 | 防止把数学规则再复制回 Cleanup |
| **core/writing_reasoning_contract.yaml** | **先核查，原则不改**：保留 Formula Role、numeric/claim、证明和算法现行语义 | 这些定义已经存在，变更它反而扩大范围 |
| **modules/06_review_delivery.md / modules/06_review/content_review.md** | **按缺口条件改**：在现有 draft/final 检查中核对语言-only 改动是否越界；不新建 finding 家族、状态或人工批准 | 检查责任要有消费者，不允许只在 05C 中自我宣告 |
| **modules/05_writing/latex.md、DOCX adapter、Template Manifest** | **检查但默认不改**：载体和定稿骨架不因 Cleanup 而变；LaTeX 语言修改不触碰数学环境 | 保留不同载体及历史模板兼容 |
| **core/module_manifest.yaml / core/workflow_router.yaml / scripts/resolve_runtime.py / scripts/reading_plan.py** | **核查、预期无业务改动**：cleaned_paper_text 输出、ai_cleanup route、load timing、read-set、fallback 和 gates 保留 | 防止语义修订意外成为架构重构 |
| **scripts/audit_paper_prose.py / scripts/audit_v8_writing_surface.py** | **核查，默认不修改**：继续定位风险；不能因为 Cleanup 更严格而变成自动数学裁判 | 当前脚本不是公式变化的语义证明器 |
| **scripts/lint_skill_checks.py** | **必须检查并预计同步旧 token 断言**：用新的权责不变量替换已过时的 Cleanup 四章标题和字面短语检查 | 防止 CI 绑定旧重复表述 |
| **tests/fixtures/p3b_writing_role_source_map.yaml、tests/test_p3b_writing_roles.py** | **需要同步**：保留 consumer <15000 UTF-8 字节上限、Preflight/Review/routing；将旧 Formula Role 文本存在性改成“受保护内容只读 + Authority 保持 + 显式回退” | 不能为过关提高 cap 或删除防护 |
| **tests/test_v830_editable_mechanism_diagram.py** | **必要时精确重基线**：仅对实际修改的 05C blob（及真正改过的 Authority）更新保护哈希；保留其历史逆投影和全部无关 PROTECTED hashes | 防止重复出现 #292 的冻结 hash 失败；不取消防漂移 |
| **tests/test_v10260_cumcm_writing_narrative_b.py**（#292 引入） | **必须继承后检查**：当前 B2/B4 在 Protocol/Reasoning 的验证不变；Cleanup 的固定短语要求迁为“不得自行执行数值/深化分析修改”的行为边界 | 保持 B1–B4 的已授权新增能力 |

### 3.1 必须逐项检索旧文字锚点的回归集

主检查列表（实施时按实际最新 HEAD 再复核）：

- tests/test_v716_paper_writing_spec.py：solver-first、标题风险、AI 包装词；应改成上游审查负责、Cleanup 不动结构。
- tests/test_v718_model_solution_writing_style.py：连续叙事、Heading Compression Test、Judge Readability Test、solver 叙事；迁至 Protocol/Reasoning，05C 只留语言风险边界。
- tests/test_v719_intra_question_writing_closure.py：Core Derivation Body Closure Test、Split/Merge、表格、图；数学/结构责任回到 Authority。
- tests/test_v730_writing_expression_protocol.py：旧 A/B/C/D 章节标题和 protected markers；替换为新权限与引用合同。
- tests/test_v740_writing_evidence_architecture.py：完整性、图表和表格 token；保护不降级，规则位置从 05C 迁到现有 Authority。
- tests/test_v743_writing_structure_style.py、tests/test_v744_natural_paper_flow.py：Consumer 和自然措辞约束；核查无空泛分数器。
- tests/test_v750_writing_reasoning_architecture.py：核心推导原文不得被 Cleanup 压缩的更强保护。
- tests/test_v760_writing_governance.py、tests/test_v770_paper_semantic_governance.py：文稿权限、数字和术语 Authority；B4 结果不回退。
- tests/test_v831_author_reasoning_voice.py、tests/test_v850_author_reasoning_speech_acts.py：保留真实作者语气，不靠第一人称频率判断。
- tests/test_v860_model_construction_solution_rationale.py、tests/test_v870_question_writing_capability_preflight.py：不能让 Cleanup 代替数学、模型、标题/Preflight 裁决。
- tests/test_v801_chapter_capability_preservation.py、tests/test_v800_writing_runtime.py、tests/test_router_contract.py、tests/test_reading_plan_evidence.py：阶段顺序、原 read-set 与 fallback 保持。
- tests/test_v830_editable_mechanism_diagram.py：全源防漂移精确哈希/逆投影。
- #292 新增测试及当时新增/改动的其他测试必须纳入最终核查；不可只看上面历史清单。

仅在测试确实依赖旧文案而不能继续代表正确目标时改断言。**删除过时字面断言必须有同等或更强的新负例；不允许删掉数学保护测试或把所有变化加入宽松例外。**

## 4. 计划实施顺序（未来单独功能 PR）

### P0｜等待前置 PR 并重新取证

1. 待 #292 完成、合并且 main CI 真实验收，读取新的 main SHA/version、bootstrap、治理规范及本计划涉及的完整 Authority；如被取消，则按实际 main 重建计划的 diff。
2. 检查是否已有重叠 PR；有冲突先排队，不在不同聊天并行更改 05C/Runtime/Reasoning 等文件。
3. 对比 main 与现有草案：逐条标注“已满足 / 仍冲突 / 需要兼容 / 不适用”；本计划不替代源码事实。
4. 确认未来 PR 的修改简报、变更等级、版本同步和原子回滚；**本轮 docs PR 不执行 P0 之后的功能变更**。

### P1｜冻结保护对象与代表性文本

1. 选用小范围维护 fixture（可复用已有 tests）覆盖：纯中文衔接、内联及行间 LaTeX 数学、公式间的中文推导、证明、伪代码、引用、图表、优化决策值、英文算法名、跨问与多载体。
2. 将每个片段区分为“允许语言润色 / 已整理好且不可变 / 应报告给上游”的操作范围；不落用户项目文件，不新增项目状态字段。
3. 确认现实执行并无专门的可追溯公式前后差异自动证明器：不要把现有 lint/关键词测试声称为数学等价证明。以后如要引入自动结构比较，必须另行评估正确性、成本与单一消费者，本计划默认**不新增检查器**。

### P2｜重写 05C 单一职责

1. 清除 §B1 内公式 Keep/Compress/Re-locate/Delete 的**执行权**；角色名可以作为只读指针，完整判断留在上游。
2. 清除 §C4 标题拆分/合并执行权；标题保持定稿结构，发现过长/无对象标题只给写作审查建议。
3. 清除 §B3 数值舍入和自动格式统一的执行权；保留“数值/单位/精度不动，遵循当前 Numeric Profile”的短边界。#292 的两位小数仍可在原写作阶段按 Authority 进行。
4. 移除 §C3 表格裁剪/重排、修改 caption 与显示名的执行权；图表附近纯叙述性语言可以润色。
5. 用简洁的禁止变更、争议报告、改后逐项核对，替代反复罗列算法/模型/公式详细规范；保留 C1/C2/C5 真正的去模板化能力。
6. 不新增独立“ai_cleanup_rules.yaml”、文件校验状态或另一套 Model/Formula Trace。文件体积以职责清楚为先，保留既有 <15000 字节消费者上限，不能把缩小字节数当成唯一 PASS。

### P3｜运行时与审查消费者最小同步

1. 在 core/writing_runtime_contract.yaml 当前 ai_cleanup stage 的 gate 中闭合“只允许自然语言；公式/推导/结构等只读”；不改 stages 排序、Preflight、原有读集身份、gate 数目或 cleaned_paper_text 输出。
2. 明确已完成的 draft 审查不是允许 Cleanup 再改数学的授权；需要数学修订时回到原阶段。按真实作用范围消费 resolved findings。
3. Draft/Final Review 如缺少非授权修改对照提示，则仅加在现有复核环节，不新增第九 coverage family、额外 reviewer、逐句人工批准或项目 State。
4. 保留 LaTeX 载体与项目语义身份。仅修改普通语言不构成模型 semantic_revision 变化；但如纸面源码发生改动，已有 LaTeX source bundle、compile/PDF currentness 仍须按原要求更新，不复用过期编译证明。

### P4｜更新引用、测试与负例

按 §3 全部消费点完成小范围修订，重点采用**原文未变、越界被识别**的例子，而不是单纯在文档里查到“不得修改公式”四个字。

| ID | 场景 | 正确结果／错误结果 |
|---|---|---|
| AC-01 | 纯空话与机械过渡 | 允许删“为了更好地解决这一问题”等无信息句；不删题目特定理由 |
| AC-02 | 行内数学、上下标、反向不等号 | 数学源码及含义不动；不得换变量、方向或条件 |
| AC-03 | 连续 equation/align/定理环境 | 数学/标签/编号/顺序不动；不得合并或删除 |
| AC-04 | 五步证明夹杂中文逻辑 | 整段证明和关键自然语言推理只读；不能为了短把五步改一句“易得” |
| AC-05 | supporting_derivation 或 routine_algebra 已在正文定稿 | Cleanup 无权按角色自行删减/移附录；需上游另行授权 |
| AC-06 | “局部最优”“数值近似”“在假设 A 下”等限制 | 不能改为全局、精确、无条件等更强说法 |
| AC-07 | 高精度答案及普通解释数字混排 | 05C 两类都不改数值；B4 展示口径仍由 Numeric Profile/上游写作处理 |
| AC-08 | 章节标题/小节层级和物理文件 | 保持不变；可报告标题问题，但不在 Cleanup 改结构 |
| AC-09 | 图题/表题、表头、数值、引用标签 | 不动图表实体与 key；仅可润色不承载事实的相邻正文 |
| AC-10 | 已运行结果与尚未运行的 03B | 不新增试验、对照数据、收敛证明或“已验证”主张 |
| AC-11 | 引文键与外部事实 claim | 不删除 key、不改引文范围、不把 cited claim 扩大 |
| AC-12 | 标准算法名与首次术语定义 | 不因“像 AI”换术语；已准确解释的定义不删 |
| AC-13 | 用户要求改数学错误 | 不作为 Cleanup 执行；返回原写作/数学审核阶段 |
| AC-14 | CUMCM 与 MCM/ICM/DOCX、历史无独立 Manifest | 权限边界共用，载体 fallback/路由规则不回退 |
| AC-15 | 用户仅让修改一段普通语句 | 不触碰其余章节，不触发模型重新审批或数值重算 |
| AC-16 | 对原稿进行了真实文字修改 | 改后检查语义、受保护块和引用；LaTeX 源码变动不能继续复用旧 compile/PDF attestation |
| AC-17 | 用户要求压缩正文关键推导或长证明 | Cleanup 仅报告范围冲突，Math/Prose Authority 先裁决；不能擅作删除 |

验收方式可组合**受控 fixture 的数学/标签原文对照**与现有人工语义审查；任何自动检查只能宣称其实际覆盖的字符串/结构性质，不能冒充真正的数学等价性判断。可在现有 tests 中增补或建立一个专门的回归测试文件，**测试文件不是用户运行的 checker，也不是新 delivery gate**。

### P5｜正式 GitHub 验收、收尾与回滚

1. 功能修改创建独立单主题分支和 PR，从 P0 核对后的 main 出发；更新实际 release carriers/Changelog 只按最新治理规则决定，不抢发 GitHub Release。
2. 先 GitHub draft/branch 专项验证 lint、旧文字断言迁移、新负例、P3b consumer cap、Formula/Proof/Algorithm 保护、Review/Runtime/read-set 兼容。
3. 源码提交后由 GitHub refresh-generated 自动更新受管索引；对最终 source head 核对生成 diff，不手工改 MANIFEST 或索引。
4. ready 后以**最终 PR head**完成正式 Windows Python 3.10/3.14 四分片及汇总、Static lint、Generated contract、CUMCM/MCM/Diangong LaTeX、Production attestation、MATLAB native、两版本 Python Figure 和适用 Optimization baseline；严格按真实 Actions 状态报告，不用历史 PASS 顶替。
5. 发生源/生成文件新 commit 后重新验收最终 head；失败时按具体日志最小修复，**不能**删掉有效的数学保护测试或调高体积上限“绿灯”。
6. 功能 PR 获许可合并后复核 main CI；按用户“后续统一发布版本”的安排处理 Release，不因为计划完成就独立发布。
7. 回滚必须同时撤回消费者、测试与 Authority 的对应修改，保留旧项目、accepted Workbook 和已批准模型身份；生成文件依原工作流恢复。

## 5. 完成定义与风险控制

**必须同时达到：**

- [ ] Cleanup 的主动编辑权限仅针对普通自然语言，公式与中文推导、证明、伪代码、数值、图表实体和结构保持只读；没有残留的数学 Keep/Compress/Re-locate/Delete 许可。
- [ ] 不出现第二套数学/图表/数值 Authority；精简后的 05C 能准确引用现有来源，不需要从头加载无关合同。
- [ ] 反模板化仍有效：自然、准确、不空泛、不逐点读表、不为“像人”注入故事、错位第一人称或伪犹豫。
- [ ] 遇到数学疑问只能报告和回退原阶段；不以“形式等价”自行替换符号/推导。
- [ ] 所有直接消费 05C 原文短语的 lint/test/fixture 经真实扫描并更新，保留等价或更强保护；全源防漂移只精准批准实际变更部分。
- [ ] Preflight、runtime 阶段名、read-set、输出、复核覆盖、existing gates、模型和 accepted 数值链均未回退。
- [ ] GitHub 证据覆盖最终 head，测试/编译/生成成功才可称功能完成；Plan Only 不声明已经实现。

**主要风险及处理：**

| 风险 | 对策 |
|---|---|
| 过度冻结导致可用语言完全不能动 | 区分数学逻辑句与非逻辑叙述句；无争议叙述可优化，疑难句保留并报告 |
| 只保护 TeX 公式而误删中文证明 | 把文字推导、成立条件、算法前提纳入同级受保护范围；以混合段落负例验收 |
| AI 为“改得更自然”改动结论、精度或模型类别 | 主张、数字、术语和 citation key 只读；对照后修复/回退 |
| 精简删除历史固定 token 触发大批 CI 失败 | 预先盘点测试锚点；同步迁至正确 Authority，再用更强的 05C 只读断言替代 |
| 新增 checker、审批和重复状态增加成本 | 不新增用户工具、流程状态或 gate；复用现有 Draft/Final Review 与版本对照 |
| #292 及未来 Phase C 发生交集 | 必须先合并或裁决 #292，按新 main 重读原文与实际变更；与 Phase C 不打包 |
| 仅凭自动匹配宣称所有数学语义保持一致 | 机器只做其可证明的结构/原文核对，语义风险由已有 Review 检查；不伪称数学 PASS |
| 清理正文后复用旧 LaTeX/PDF 验收 | 数学不变不代表文件未变，paper source changed 仍由原 compile/read-set currentness 处理 |

## 6. 计划与后续动作状态

- **本计划：** 只新增此 docs 文档，允许作为独立 Plan-Only PR 保存，不合并在 #292 前，也不修改活动 Skill。
- **尚未进行：** P0–P5 的功能实施、改写/执行真实用户论文、运行新负例、正式 CI 成功验收、合并功能 PR 和发布 Release。
- **实施触发：** #292 当前开发改造先闭合；用户未来明确要求执行本计划时，重新读取适用完整 Authority 与源码后启动独立功能 PR。
- **无附加等待任务：** 不要求用户本地 checker、人工逐章已读确认、逐句批准或预先批准图表位置。

**总原则：** AI Cleanup 只决定“自然语言怎样更简洁、准确、少模板感”；公式、推导、模型、证据、数值和章节结构已经在上游确定，Cleanup 对这些内容只有只读与问题上报权限。
