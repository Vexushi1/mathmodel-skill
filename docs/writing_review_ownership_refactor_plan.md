# 论文写作与后期审查职责收束：详细实施计划（Plan Only）

> 状态：**Plan Only；待审阅，未实施任何运行时/业务规则修改**  
> 仓库：Vexushi1/mathmodel-skill  
> 计划基线：2026-11-04，main@87c7cbef3ca59fd3e6c5771e7fa8952f04bef0da，Skill v10.26.2  
> 维护依据：main 的 core/bootstrap.yaml、SKILL_CHANGE_GOVERNANCE.md、AGENTS.md 和现行 Authority  
> 文档分支：docs/writing-review-ownership-refactor-plan  
> 当前变更等级：docs，无版本升级；后续功能 PR 在实施时按最新 main 重新裁决版本等级  
> 既有相关开放 PR：#293（旧 AI Cleanup prose-only 的 Plan Only 草稿，主要改其计划文档及受管索引）。与本计划存在主题关联，但无活动 Authority 的文件级冲突；不接管、不覆盖其分支。实施前必须再次检查最新开放 PR。  
> **本文件只是实现蓝图，不是新的写作 Authority、审查门禁、模型授权或 GitHub CI 通过记录。**

## 0. 变更简报（治理规范 §3）

| 项目 | 计划 |
|---|---|
| 修改主题 | 模块 05A/05B/05C/05D 与 Module 06 的职责清晰化、重叠规则收束、去防御性学术表达的安全融合 |
| 当前版本 | v10.26.2；上述固定 main 提交作为计划审计基线 |
| 目标版本 / 等级 | 本次 docs/no bump；未来实施预期为兼容性重构，可能属于 patch 或 minor，按实际规则行为变更决定，不预占版本号 |
| 直接目标 | 一项规则只定义一次；写作、语言修改、载体、工程验证、语义审查、交付判定各有明确负责人；质量前移但不新增重复门禁 |
| 明确不做 | 不重设计数学模型、Formula Role、Proof、Algorithm Trace、Claim Strength、数值验证、图表 Authority、Human Model Approval、求解后端、用户项目正文或正式模板骨架 |
| Authority | core/writing_reasoning_contract.yaml；modules/05_writing/paper_writing_protocol.md；core/writing_runtime_contract.yaml；templates/latex/cumcm/hsk/template_manifest.yaml；modules/06_review_delivery.md 及其两个真实叶文件 |
| 预计功能改动文件 | modules/05_writing/paper_writing_protocol.md、modules/05_writing/ai_cleanup.md、modules/06_review_delivery.md、modules/06_review/content_review.md、modules/06_review/final_delivery.md |
| 仅按实际需要微调 | modules/05_writing/latex.md、modules/05_latex_compile_quality.md、config/prose_audit_patterns.yaml、core/writing_runtime_contract.yaml、core/module_manifest.yaml、templates/review/final_review_matrix.yaml、相关脚本/消费端测试/导航文档；无实际缺口则不改 |
| 禁止触碰 | 已有用户项目与 accepted workbooks、模型批准与状态数据、legacy 默认链、官方模板一级结构、无关 Python/MATLAB 求解/绘图实现、生成索引/MANIFEST 的人工内容 |
| 兼容性 | 逐章读取与逐问闭环、现有 stage ID/read_now/write_now/gate、CUMCM/其他竞赛回退、DOCX 可选路由、Review 入口兼容锚点、最终完整 coverage 与 C1/C2 回执机制全部保留 |
| 迁移要求 | 原则上无用户项目数据迁移；现有 runtime 阅读路径若有引用调整须同步源映射和测试。Review 历史快照/旧锚点仅按现行兼容协议处理，不随意改写冻结基线 |
| 验收 | 功能用例 + 读取路径回归 + Review 完整覆盖和回执来源绑定 + Cleanup 只读保护 + GitHub 最终 head 正式 CI；具体见 §8 |
| 回滚 | 各实施 PR 原子 revert，并重验读集与索引；不回滚已发布数值/模型成果或改写用户论文 |

**明确授权范围：** 当前用户批准“准备重构、先写修改计划”；此时只允许新增本计划和 Plan Only PR。正式业务源修改应在计划审阅后另开实施分支与单主题 PR，不把计划当作已经实施的授权。

## 1. 当前结构与需要修复的真实问题

### 1.1 现有运行链（保持不变）

~~~text
core/bootstrap.yaml
  ├── Template Manifest：固定一级骨架/条件槽
  ├── core/writing_runtime_contract.yaml：按阶段、按当前章节渐进取读
  ├── core/writing_reasoning_contract.yaml：复杂数学/证据 Authority（按需）
  └── modules/05_writing/paper_writing_protocol.md：普通正文写作 Authority

template_inspection
→ problem_restatement
→ problem_analysis
→ assumptions_symbols_and_preparation
→ question_model_solution_result_validation（逐问）
→ evaluation_references_conclusion_appendix
→ abstract_title_and_keywords
→ draft_semantic_review
→ ai_cleanup
→ latex_assembly_audit_and_compile
→ final_review_and_delivery
~~~

现状在“阶段顺序”层面已经合理，不增加额外写作或审查节点。最终论文阅读顺序不等于作者写作顺序；摘要仍在各问事实稳定后写，终审仍按最终 active assembly 检查相邻章节。

### 1.2 已核对的职责交叉（不是全部都需要删除）

| 交叉点 | 实际位置 | 结论与拟定动作 |
|---|---|---|
| 普通学术表达与润色 | Protocol §7.3、§16；Cleanup §C；Content Review 的 Author Reasoning | **规范—执行—验收分开**：Protocol 定义写作质量，Cleanup 只编辑可改语言，Review 只审查是否符合规范 |
| 数学/证据边界 | Reasoning Contract；Protocol §7–§11；Cleanup §A–§B；Content Review §三–§四 | Reasoning 保持唯一复杂语义 Authority；Protocol 保留必要写作应用；Cleanup 保留只读边界，不重新证明；Review 消费既有 Authority |
| 工作流治理词泄漏 | Protocol §17；core/writing_runtime_contract.yaml#runtime_vocabulary_firewall；config/prose_audit_patterns.yaml；scripts/audit_v8_writing_surface.py | 保留写作原则与机器定位的分工；词项统一由现有配置维护，避免多地逐字手抄后漂移；现有 warning 不升为默认 Hard |
| 段落/章节衔接 | Protocol §4、§5、§5A；Runtime seam 时机；Content Review 的 assembled seam sweep | Protocol 定义合格叙事，Runtime 只决定何时读取/检查，Review 只执行审查；不增加 Handoff 必填表 |
| 图表叙事与信息价值 | Protocol §13；Figure Authority；Content Review §六；Final Matrix figure_table_information_value | 写作位置与解释归 Protocol；图的制作/视觉证据归 Figure Authority；Review 验证论文内证据作用，不新造图形质量规则 |
| LaTeX 审计及 PDF | 05B §7、05D；scripts/render_paper.py → audit_latex_project.py；Final Delivery 与 Matrix | 05B 只装配，05D 负责实际工程审计/编译/逐页检查，06 消费当前 PDF 的有效检查证据并作交付决定 |
| 初稿与终稿的共用检查 | Module 06 入口 + content_review.md + final_delivery.md | 保留 **同一个共用内容审查文件**，区分首次核查与最终当前性/变化影响复核；不因此新建独立 Review 模块 |
| 历史兼容导航 | 06_review_delivery.md 旧二至九节锚点指向两个叶文件 | 保留旧路径、兼容展开与真正的 leaf 正文；不能把指针当作已读取规范，也不能直接删除历史映射 |

### 1.3 已有优化，不重复再做

- v10.26.2 的 Cleanup 已经收缩为普通语言编辑，**不得恢复**对公式、中文推导、证明、伪代码、数值或章节结构的直接改写权。
- Module 06 已拆为入口 / 共用内容 / 终稿交付三文件：本轮优化的是职责与消费语义，不重新进行一次大拆分。
- 正式 LaTeX 编译入口 scripts/render_paper.py 已内部执行正式项目审计；默认流程不再额外机械运行完全相同的项目审计。
- 既有 final_review_matrix.yaml 已有八类 coverage，不新增“防御性写作评分”或额外 quality gate。

## 2. 拟定的唯一职责（重构后）

| 所有者 | 唯一主要责任 | 允许即时检查 | 无权改动/重定义 |
|---|---|---|---|
| Template Manifest | 一级骨架、active 槽位、模板固定结构 | 模板结构正确性 | 当前模型/算法/论证和语言 |
| Writing Runtime | 何时读哪个规则/事实、条件激活、阶段次序及原有 gate | 当前来源/状态能否进入阶段 | 论文内容与数学语义定义 |
| Reasoning Contract | 数学语义、公式角色、证明/Algorithm Trace、主张与证据等级 | 推理/证据规则的适用性 | 普通语言润色 |
| **05A Paper Writing Protocol** | 如何按当前题目、事实和证据组织正文；模型理由、推导说明、结果叙事、章节承接与学术表达原则 | 逐章/逐问局部内容质量自检，不生成完整 Review 报告 | 改动已锁模型事实、数值；最终独立验收 |
| **05C AI Cleanup** | 对已经通过初稿语义审查的普通语言做 Keep/Compress/Re-subject/Delete 等有界修改；去空话、模板感、无依据的自我削弱及工程管理话语 | 编辑范围/保护内容与相邻语境的必要对照 | 公式、中文推导、证明、伪代码、数字、正式术语、条件、claim、caption、标题及结构 |
| **05B LaTeX Adapter** | 正文源码装配、环境、label/ref、模板载体映射 | 环境/引用技术边界 | 论文写法与模型选择 |
| **05D Compile Quality** | 当前 LaTeX 正式审计、编译证明及当前 PDF 逐页检查 | 工程、页面、可见排版缺陷 | 数学与证据语义重新裁决 |
| **06 Review Entry** | 审查分级、阶段选择、finding 定位、返修路由、blocking 和交付裁决 | 真实问题严重度判断 | 正文写作规范的第二套定义 |
| **06 Content Review** | 按现有 Authority 独立检查题意、数学/证据、结构、术语、主张、语言、图表叙事、引用 | 逐章及最终完整语义 coverage | 直接当作者改写论文或改模型 |
| **06 Final Delivery** | 当前全部活动范围覆盖、官方赛事合规、来源/报告/PDF/包的有效性与最终决定 | 对变化范围复核、对旧检查证据作有效性裁决 | 重复执行 05D 同一版 PDF 的无条件逐页检查 |
| DOCX（可选） | Word 专属载体、批注与迁移 | Word 特有排版 | 默认替代 LaTeX 主链 |

**关键原则：允许多个模块发现同一类问题，不允许多个模块各自制定同一条规则。** 05A 的即时自检不等于 06 的独立审查；06 发现实质性错误应返给具有内容或数学权限的上游，而不是让 05C 借润色修复。

## 3. 防御性写作 Skill：安全融合方案

参考外部 Adkid-Zephyr/anti-defensive-writing-Skill 的中文 Skill（MIT 项目，需在实施时复核来源及许可）。只吸收适合数学建模竞赛、与真实题意和证据一致的原则，不直接复制整套指令。

| 类型 | 典型问题 | 拟定权威及处理 |
|---|---|---|
| 叙事组织 | 工作汇报、试错流水账、无关算法背景、结果没有回应题目 | 05A §7.3/§9/§16，写作时预防；结构确需重排则走原 05A/06 修复 |
| 成果表达 | 已成立优势被空泛否定，未说明适用条件与贡献 | 05A 描述真实比较对象/条件/指标，不编造优势或改变题目评价目标 |
| 普通措辞 | “遗憾的是”“仅取得一定效果”等无信息价值的自我削弱套话 | 05C 在不改变结论、数量、范围和限制条件时改为客观陈述 |
| 工程口吻 | “质量门”“已验收工作簿”“03B”“stale”等项目管理词进入论文 | 05A 避免写入；既有 config/prose_audit_patterns.yaml + audit_v8_writing_surface.py 定位；05C 在普通文字中安全清理 |
| 真实负面结果 | 必须披露的性能下降、失败实验、适用边界、精度缺口 | **必须保留**，按证据写得准确、克制；不可因去防御性表述而删除 |
| 涉及重新选指标、删必要比较、改变研究任务/主张 | 外部 Skill 中“打不过的维度不设为比赛”“不说输”“重定义故事”等强策略 | **不直接采用为自动改写规则**；题目规定的指标与必要反证必须如实呈现，任何实质性主张/设计变更走上游审查与必要审批 |

### 3.1 规则落点：不新增独立工作流 Skill

- 05A §7.3：真实作者判断、论证必要性、积极但证据有界的表述；预防实验流水账。
- 05A §16：普通学术表达、非防御性且准确的客观叙述；§17 只保留工作流词汇原则及统一配置引用。
- 05C §C1/§C2：安全语言改写的允许动作、禁改边界与必要最小回退；不将“仅”“可能”“不显著”“存在局限”等词定义为通用禁词。
- 06 Content Review：消费相同规范判断实质叙事问题和表达风险；不复制外部 Skill 全文；现有终审 coverage 包含该检查，不新增独立 family。
- 当前计划**不新增 academic_expression_policy.md**。未来只有在 05A/05C 事实上形成需要跨载体共享的大段可执行规范、且重复已经影响维护时，才另行评估拆出短文件，并同步读取路径。

### 3.2 应预先设计的正反例

- 可修改：“遗憾的是，该方法仅取得一定效果。”→ 在已有证据允许时，写具体指标及效果；若没有数据支撑具体化，只删无信息套话，不填造数字。
- 不可自动弱化：“算法在测试集 B 上的误差比基线高 12%。”属于真实发现；保留比较条件、差异方向和数值。
- 不可删除：“仅在 x>0 时成立”“局部最优”“未通过显著性检验”“存在 3% 偏差”等承载数学/证据边界的表达。
- 允许更准确而非更积极：区分“数值上未观察到差异”和“证明不存在差异”；不以语言风格推动结论升级。
- 对必需负面结果和题目要求的完整比较，Review 不允许因“发布会原则”将其移除。

## 4. 功能改造时各文件的具体操作

| 文件 / 部位 | 保留 | 计划操作 | 不做 |
|---|---|---|---|
| modules/05_writing/paper_writing_protocol.md §0–§6、§8–§15、§18–§19 | 逐章节写作、Preflight、局部闭环、题目与结果叙事 | 只审计职责重叠；无缺口不删 | 不把本文件压缩成只有原则的短文 |
| 05A §7.3、§16 | 作者判断、事实依据、朴素学术表达 | 定位防御性叙事预防与具体语言例子；避免同一表达原则多地复制 | 不建立新的实验或指标选择权 |
| 05A §17 | 内部词汇不得进入正文 | 引用统一诊断配置；减少多位置同词项静态复制 | 不删合法技术术语 |
| modules/05_writing/ai_cleanup.md §A–§D | Prose-Only、数学/事实/结构只读、局部修改、受保护内容复核 | 减少多余的业务定义解释；在 §C 加入去防御性语言执行规则和例外 | 不恢复数学压缩、标题改写、表格/图注编辑权限 |
| modules/06_review_delivery.md | 两种消费时机、severity、finding、返修排序、blocking | 保留入口/历史锚点，清晰化“只负责调度与裁决” | 不把两个真实叶文件合并回入口 |
| modules/06_review/content_review.md | 六类共用内容审查与组装缝隙 sweep | 把 language/prose 判据改成明确消费 05A/05C 的规则；区分初稿实质性审查与终审当前性复核 | 不复制润色词表、不降低数学完整性要求 |
| modules/06_review/final_delivery.md | 八类 coverage、赛事规则/提交证据、人工/机器分工 | 明确对 05D 逐页结果按 PDF SHA 消费、失效和补审条件；完整覆盖可批次/复用 | 不把旧 report 存在等于当前通过 |
| modules/05_writing/latex.md | LaTeX Adapter | 若确有重复解释，改为引用 05D 工程权威 | 不改变正式模板骨架 |
| modules/05_latex_compile_quality.md | render_paper.py 正式入口、实际页面检查 | 仅必要时澄清检查执行者和当前 PDF 证据责任 | 不删 PDF 实际逐页审查 |
| config/prose_audit_patterns.yaml、scripts/audit_v8_writing_surface.py | 内部词风险/引号/概念链等保守诊断 | 优先不改；如确认词表漂移，集中统一配置和测试 | 不增加防御性语言关键词一票否决或 AI 检测评分 |
| core/writing_runtime_contract.yaml、core/module_manifest.yaml | stage ID、read/write/gate、条件激活、Review 读取闭包 | 本轮默认不改；只在已有消费者无法正确取读时做窄范围路径修复 | 不改阶段顺序、不新增状态或全量预读 |
| templates/review/final_review_matrix.yaml | 已有八类终审 family | 原则上不改；现有 language/content finding 在原有 scope 记录 | 不新增第九类防御性写作专项 coverage |
| core/writing_reasoning_contract.yaml | 数学与证据的完整唯一 Authority | 此次原则上只读核对 | 不变更 Formula/Proof/Algorithm/Claim 数学语义 |
| templates/latex/cumcm/hsk/template_manifest.yaml | 固定一级结构 | 只读核对 | 不改活动标题/条件槽 |
| 05E docx.md | 用户显式请求才激活的 Word Adapter | 仅验引用没漂移 | 不使 DOCX 成为默认流程 |

变更尽量是局部 diff；避免全文件自动格式化造成无关噪音。执行时对每一项实际移动的规则建立“原位置→唯一新权威→消费位置→对应测试”映射，不能只为了缩短文件而删有效规则。

## 5. 两次 Review 与 05D 的执行边界

### 5.1 初稿语义审查（仍发生在 05C 之前）

消费 06_review_delivery.md + 06_review/content_review.md，检查每个 active 问题的数学与证据、必要能力是否激活、标题/结构/段落和已知表达风险；重大/需裁决问题返上游修复。此阶段不要求最终 compile report，不执行最终提交包审查。不能因为“还会终审”就放过会使 Cleanup 无从安全编辑的数学缺口。

### 5.2 AI Cleanup

只编辑通过前置审查的目标普通语言；若风险触及公式/条件/Claim/引用/证明、算法、标题/图表/数值，定位并返回现有 finding/上游，不在 Cleanup 修复。编辑结束时仅对照原文和受保护内容、直接依赖进行必要校验，不新增独立审批节点或逐句哈希台账。

### 5.3 正式 LaTeX 与 PDF

05B 负责装配；05D 的正式路径由 scripts/render_paper.py 在编译之前调用 audit_latex_project.py，得到与实际 source bundle 绑定的审计证明，之后编译并逐页查看当前 PDF。独立诊断脚本只在有明确问题时运行，不默认额外再走一遍相同审计。

### 5.4 最终终审

消费 06 入口 + 共用内容审查 + final_delivery.md 以及既有 final_review_matrix.yaml。完成**所有 active files、questions、headline claims、required gates 的完整 coverage**。对未发生变化、来源仍 current、人工语义覆盖仍可证明的结果可复用；重点重审 Cleanup 改写片段、相邻推理/章节缝隙、变化依赖、最终源码与 PDF、当届赛事交付条件。任一来源变化导致原回执、PDF 哈希、读集或相关证据失效时，按既有规则补审，不能凭“之前审过”跳过。并非所有未改段落都能仅凭 hash 自动被视为数学正确；人工审查范围必须有可核证依据。

05D **执行**当前 PDF 逐页检查；06 **核验/消费** coverage 和 currentness。相同 PDF 且有效证据齐全时不无条件重做；PDF 变更后按 05D 既有逐页规则重新覆盖，不能只抽查差异页就宣称全篇页面通过。

### 5.5 精确返修路由

| 发现 | 修复责任 | 验收重点 |
|---|---|---|
| 题目遗漏、模型/公式/推导/命题/算法错误 | 05A 或更上游模型、证据 Authority（必要时原有人工批准） | 正确性和 affected scope |
| 模型事实未变但写作结构/推理表达不闭合 | 05A | 语义完整性、跨章节依赖 |
| 纯空话/防御性套话/工程词泄漏 | 05C | 保真修改与语气准确 |
| LaTeX/引用环境/编译/PDF 缺陷 | 05B 或 05D | 当前工程/页面证据 |
| 竞赛规则/匿名/AI 披露/提交包 | 对应模板/提交 Authority，由 06 判定 | 已核验当届规则与交付状态 |

## 6. 渐进读取与跨竞赛兼容：必须不变

- 保持原 authoring_sequence 的所有 stage ID、stage order、当前 read_now/write_now/gate 语义及阶段输出名称。逐章采用“读本章 → 写本章 → 原有适用检查 → 下一章”，不能提前全读整个 05A/05C/06。
- 不提前读取初稿 Review、Final Review、05D 的全部正文来决定某章句子风格；05A 的防御性叙事原则按 §7.3、§16 和本章实际读集局部读取。
- Proposition/Proof、Algorithm Trace stepwise/pseudocode、Formula Role、跨问真实依赖、当前图表候选的条件激活完全保留；必要时 full Reasoning fallback，不能因压缩 rule 文案漏读。
- MCM/ICM、DOCX 及缺少可验证 CUMCM narrow-read 支持的路径保持现有回退；不能硬套 CUMCM 二级标题/模板。
- Cross-File Assembled Seam Sweep 保留初稿和终稿的最终活动文件顺序，摘要按最终读序；普通邻接不强制建立新的持久 Handoff 表。
- Review 来源仍按 core/module_manifest.yaml 的 entry/content/final 闭包：draft=[entry,content]，final=[entry,content,final]。旧路径和锚点必须取回叶文件真实正文，而非仅返回指针。
- Model Approval、用户 full-fidelity 运行、accepted workbook、项目 State/typed stale、C1/C2 回执资格与全部 resolver-gates 保持不变。规范文件来源变化对回执有效性造成的真实影响必须如实处理，不“刷新 hash”绕过。

## 7. 分批实施计划（每批可独立回滚）

**Plan PR（本次）：** 只新增本 docs 计划；不修改 active Authority、运行时、脚本、测试、版本、模板或用户文件。计划 PR 保持 Draft，仅报告实际远端检查结果。

**实施批次 A — 写作/语言职责：**
- 先形成精确的 §4 规则迁移表，固定 05A/05C 编辑权限，再在 05A 中吸收安全防御性叙事原则、在 05C 中实现有界去防御性措辞。
- 同一 PR 内同步更新必要的读集断言/脚本配置和专项测试；不提交只更新文档却破坏依赖的中间状态。
- 专项关注公式/中文推导/证明/伪代码/数字/Caption/结构只读，当前结果说明的限定与 Claim Strength 不漂移。

**实施批次 B — Review 职责与检查复用：**
- 调整入口与两个叶文件的职责描述，区分 draft 实质审查和 final 当前性/增量复核；保留八类 coverage 和 full active scope。
- 同一 PR 处理与 Module 06 历史文字重组、来源快照、阅读计划、Review receipts、Final Matrix 关联的测试；不得通过改冻结 fixture 或放松检查消除失败。
- 05D/Final 的 PDF 证据消费接口确有缺口才做最小文字/消费者修正，避免引入并行 report。

**实施批次 C — 集成收尾（有必要才执行）：**
- 若前两批发现真实调用漂移，窄范围修复 core/writing_runtime_contract.yaml、core/module_manifest.yaml 或阅读消费者，同时保留所有 stage ID/gate 和来源闭包。
- 同步长期导航说明与兼容锚点（只在必要时）；不重复修改无关流程或新建总控。
- 用户认可并满足所有正式验证后再决定版本发布；不与 Plan PR 混在一起。

每个功能批次在**新的维护会话**确认最新 main 和重叠 PR 后建立独立分支/单主题 PR；每个 PR 自带必要测试修复。不能先改源码、把消费者测试留待最后一个大 PR 才修。

## 8. 验收矩阵：必须能发现哪些回归

| ID | 场景/断言 | 关联测试和检查 |
|---|---|---|
| WR-01 | CUMCM 普通逐章只读当前 Protocol sections，章节次序、read/write/gate 不变 | tests/test_v800_writing_runtime.py、test_reading_plan.py、test_reading_plan_evidence.py、test_p3b_writing_roles.py |
| WR-02 | 命题 planned/current、Algorithm stepwise/pseudocode 条件资源照常激活；missing 不静默 not_needed | test_v870_question_writing_capability_preflight.py、test_p3b_writing_roles.py |
| WR-03 | 局部润色不预载/修改无关章节，跨问真实依赖才扩围 | test_v10262_ai_cleanup_prose_only.py、test_p3b_writing_roles.py |
| WR-04 | Cleanup 不能改公式、中文推导、证明、伪代码、限制条件、数字/单位、术语、引用、caption、结构 | test_v10262_ai_cleanup_prose_only.py + 代表性正反例审阅 |
| WR-05 | 防御性写作清理不得删除真实负面结果、题目规定比较或模型适用条件；不做关键词硬禁 | 新增窄范围表达用例，结合当前项目片段人工语义对照；不能宣称静态单测证明 LLM 语义保真 |
| WR-06 | 工程词泄漏沿用 warning/保守诊断，排除合法文件名/代码/引用；不制造语言分数 | test_v800_surface_audit.py、相关 prose/latex audit 测试 |
| WR-07 | Draft 读取 entry+content；Final 读取 entry+content+final；旧锚点、缺源/截断/兼容闭包完整 | test_reading_module06.py、test_reading_plan_evidence.py、test_p3b_writing_roles.py |
| WR-08 | Review 原业务检查无遗漏，不靠复制/删除冻结历史规则骗过断言 | tests/module06_sources.py、tests/fixtures/module06_v10210_source.md、相关历史兼容测试 |
| WR-09 | C1 review receipt 的来源文件、read-set、currentness 与变化失效正确；C2 消费不绕过 | test_review_receipts.py、test_review_receipt_consumption.py、test_review_receipt_schema.py |
| WR-10 | 终审八类 coverage、每个 active question/claim/file、逐页 PDF 当前 SHA 全覆盖；旧检查未当前不得 passed | test_v820_final_review_compliance.py、LaTeX/Review 的原有用例 + 必要负例 |
| WR-11 | 正式编译只经现有 render_paper.py 调用 audit，review 只消费 05D 的有效页面证据；不新增重复 gate | 现有 LaTeX audit、render/attestation、production tests |
| WR-12 | MCM/ICM、DOCX、CUMCM 现有模板/fallback 和 output requirements 不发生旁路变化 | 既有跨竞赛/模板/路由专项 |
| WR-13 | 最终 main 来源与版本、当前文档/规则、生成文件和真实 PR head 对齐 | GitHub refresh-generated + 最终 CI + post-merge main |

本计划的目标是**缩减职责冗余与无效执行**，不以文件字节减少、扫描告警数量减少或手工重置冻结哈希作为成功条件。若需要重写已有断言，应证明旧断言实际绑定的是已撤销职责，保留等价的正反向能力测试；Review 的历史冻结快照不得为适配新文案而盲改。

## 9. 仓库维护、远端验收、风险及回滚

### 9.1 GitHub 纪律

- 每批先重新读 main bootstrap/governance，确认版本、HEAD、开放 PR、计划基线与最新 Authority；发现修改同一 active 文件的重叠 PR 先停止并串行合并/重建。
- 单会话一个专用分支，一主题 PR；禁止直接写 main。Plan PR 与后续功能 PR 不共享未合并分支。
- 仅提交源文档/代码/测试。SKILL_FILE_INDEX.md、TEMPLATE_INDEX.md、MANIFEST.sha256 及其他受管文件由 GitHub refresh-generated 更新，检查 bot diff 和最终 head，不手工编辑。
- 开发/Draft PR 优先远端 targeted 验证，Ready PR 和 main push 做正式完整验收：Windows Python 3.10/3.14 各四个 shard 及汇总、Static/Generated、Windows MATLAB R2024b、LaTeX 模板/Production attestation 以及适用 Optimization baseline。
- 所有 required checks 以最后 PR head 与实际 checkout SHA 为准。出现新提交必须重验；合并后复核 main。不得把计划中的测试当作已经运行/通过。

### 9.2 风险与控制

1. **规则裁剪丢数学能力**：先对照 Reasoning/Protocol 实际内容和测试定位唯一 Authority，修订前后做语义差分；Formula/Proof/Algorithm 激活与完整性不能弱化。
2. **Cleanup 借去防御性擅改事实**：正例/反例同时验，Protected Content 只读；语义冲突回原上游流程，绝不“优化掉”负面证据。
3. **Review 改动触发历史快照断言**：优先小 diff 与保留旧锚点；现有历史冻结/逆投影不是普通可随意更新的测试数据。必要业务更改需明确新的、独立的兼容策略，不能静默删除保护。
4. **过度增加规则加载**：防御性写作原则内聚到现有章节，不新增 default preload、强制 checkpoint 或每段 QA 表。
5. **以增量复核冒充完整终审**：全 active scope coverage 仍必须闭合；无 provenance/currentness 的旧检查不能复用。
6. **外部 Skill 与国赛题意冲突**：只采纳学术真实叙述，不允许挑选有利指标代替题目指定目标、隐藏必要反证或重定义已批准模型。
7. **范围膨胀**：05B、05D、Runtime、Reasoning、模板和审计脚本原则上仅检查，证明有真实职责缺口才纳入当前单主题 PR；不可顺手清理其他模块。

### 9.3 回滚与成功条件

- Plan Only：删除/关闭本文件及 Draft PR 即可，不影响 main 业务；无用户项目迁移。
- 未来实施：按各主题 PR 原子 revert，恢复兼容来源/旧读取路径，远端重新生成索引及验证；不改已验收模型/数值/图表或历史论文。
- 成功须同时满足：职责明确、同一规则唯一来源、原逐章读取行为完整、Cleanup 数学/证据只读、初稿与终审覆盖不降级、PDF 当前证据可审、无新增重复 gate、最终 GitHub 正式验证通过。

## 10. 计划实施状态

- [x] 核对 v10.26.2 的 main HEAD、bootstrap 和维护规范。
- [x] 查开放 PR #293 并确认与本计划无活动 Authority 文件级冲突。
- [x] 核对 05A/05B/05C/05D/06、Runtime、Manifest、矩阵、机器表面审计、Review 来源测试的相关现状。
- [x] 审读外部 anti-defensive-writing 中文 Skill，归纳可采纳与不采纳原则。
- [ ] 实施批次 A：尚未授权修改业务源；未启动。
- [ ] 实施批次 B：尚未授权修改业务源；未启动。
- [ ] 实施批次 C：视真实漂移而定；未启动。
- [ ] 最终功能回归、版本发布与 main 合并后复核：尚未进行。

**审阅口径：** 认可此计划仅表示认可分工方向；具体功能改动应先在实施 PR 展示真实 diff、测试证据及影响范围。