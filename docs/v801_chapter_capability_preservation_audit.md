# v8.0.1 章节详细写法能力保全审计

## 1. 审计目的与基线

本文件是迁移审计记录，不是新的写作 Authority。它回答：v8 拆分 `latex.md` 后，v7.19 已有章节写法和用户提供的 v7.20 R1 优化计划是否仍有唯一归属、普通运行入口和可执行检查。

对照基线：

- v7.19 `modules/05_writing/latex.md`：重构前正文结构与表达能力清单；
- v7.19/v8 `core/writing_reasoning_contract.yaml`：跨题型复杂语义 Authority；
- 用户提供的《数学建模 Skill 写作模块优化计划 v7.20 草案 R1》：章节内部结构、语言防火墙、审计和回归要求；
- v8.0.0 `main`：Template-First 重构后的实际运行表面。

判定标准不是“旧句子是否原样复制”，而是每项能力同时满足：

1. 存在一个明确的唯一 Authority；
2. 普通 CUMCM 写作路由能读取完成任务所需的规则；
3. 复杂语义有明确的 full-authority 回退；
4. 模板或审计行为能被测试验证；
5. 精简只删除重复，不删除决定模型、求解、结果或证据闭环的信息。

## 2. v7.19 章节能力迁移矩阵

| v7.19 能力 | v8.0.1 唯一归属 | 普通运行是否可读 | 保全要点 |
|---|---|---:|---|
| 写作输入与事实源 | Paper Writing Protocol §1 | 是 | current 框架、数值事实源、图表与文献；不从聊天恢复旧事实 |
| 规则等级 | reasoning contract + review | 按需 | Hard/Default/Recommendation 不由 Adapter 重定义 |
| 标题与关键词 | Protocol §2；复杂 Title Claim 回退 reasoning contract | 是 | 标题方法真实服务核心问题并有结果证据；关键词与标题/摘要/正文同口径 |
| 摘要 | Protocol §14 | 是 | 逐问任务—模型—目标/条件—方法—结果—真实检验—结论；禁止虚构敏感性 |
| 中文国赛一级骨架 | Template Manifest | 是 | “问题X模型建立及求解”锁定；正文规则无权重排 |
| 段落必要性 | Protocol §4--5 + reasoning contract | 是 | Local Narrative Chain、Paragraph Handoff、删除测试 |
| 问题重述 | Protocol §6.1 | 是 | 不照抄、不逐句同义替换；准确保留对象、条件、量词、单位、边界和输出 |
| 问题分析 | Protocol §6.2 | 是 | 连续写出对象/条件—困难—数学抓手—建模转化—准备结构—跨问关系 |
| 假设与符号 | Protocol §6.3 | 是 | 假设来源、影响和失效边界；符号跨公式、代码和结果一致 |
| 数据说明/预处理 | Protocol §6.4 + Template Manifest 条件槽 | 是 | not_needed/question_local/project_level 分流；参数依据、验证、信息损失和下游接口 |
| 共享基础/模型准备 | Protocol §6.5 + Template Manifest 条件槽 | 是 | 只放两问以上真实共享关系；不提前放单问 solver、结果或验证 |
| 模型推导 | Protocol §7 + reasoning contract | 是 | Source → Derivation → Destination；关键边界、降维、判据和约束来源不得过度压缩 |
| 优化模型建立 | Protocol §7.1 | 是 | 标准类型、决策对象/定义域/单位、目标现实含义、约束来源、最终可计算模型 |
| 非优化模型建立 | Protocol §7.2 | 是 | 状态/观测/概率关系、初边值、判据和输出映射；不强套 `s.t.` |
| 命题与证明 | Protocol §7.2；复杂证明回退 reasoning contract/Pack | 是 | 只保留有下游作用的命题；数值实验不能替代证明 |
| 核心模型汇总 | Protocol §7 + Template Manifest rendering | 是 | displayed/inline/omitted 自适应；recap 不替代变量、目标、约束和推导说明 |
| 模型求解 | Protocol §8 | 是 | 计算结构/困难—可利用性质—solver 适配—编码/约束—参数/停止—输出映射 |
| 算法呈现 | Protocol §8；复杂流程回退 Algorithm Trace/Pack | 是 | not_needed/stepwise/pseudocode；算法块前后闭合，代码工程细节不入正文 |
| 数值展示 | Protocol §9.1 + Numeric Profile | 是 | 评分精度优先；摘要、正文、表格、提交结果同源同口径 |
| 术语与模型命名 | Protocol §9.2；语义争议回退 reasoning contract | 是 | canonical term；标准模型类型与题目专属名称并存；model/solver/validator 分离 |
| 求解结果 | Protocol §9 | 是 | 主结果—图表/数值—决定性特征—机制—直接回答；核心证据邻近解释 |
| 结果验证 | Protocol §10--11 | 是 | 风险—扰动—不变量—指标—变化范围—结论/边界；存在 Result → Validation Bridge |
| 跨问递进 | Protocol §12 | 是 | 真实继承与新增结构；不复制、不虚构依赖、不重排一级章节 |
| 图结果叙事 | Protocol §13 | 是 | 按单点、曲线、算法/验证、空间/网络/机理等证据角色解释；禁止裸堆与无证据因果 |
| 模型评价与推广 | Protocol §15 | 是 | 优缺点绑定证据/影响；评价不代替验证；推广说明可迁移与需重标定边界 |
| 逐问结论与附录 | Protocol §15 | 是 | 每问直接回答；集中结论不新增主张；正文保留理解模型和结论所需主体 |
| Citation Evidence | Protocol §16；语义争议回退 reasoning contract | 是 | 外部主张有真实引用和本题映射；内部推导/结果不靠外引代替 |
| 自然学术表达 | Protocol §16--17 + AI Cleanup | 是 | 少管理话语、少标签包装、术语稳定、内部治理词不进入正文 |
| 篇幅与工作量 | Protocol §18 + runtime Document Length Profile | 是 | 页数只诊断覆盖度；只补真实技术链，不灌水 |
| LaTeX 环境、审计和输出 | LaTeX Adapter | 是 | Adapter 只负责载体，不重新拥有章节语义 |

## 3. v7.20 R1 实施矩阵

| v7.20 要求 | v8.0.1 落点 | 验收方式 |
|---|---|---|
| 一级标题保持“问题X模型建立及求解” | Template Manifest + Q1/Q2/Q3 | manifest/title-lock 测试 |
| 复杂题 MODEL → SOLVE → RESULT → VALIDATE | Manifest + Protocol §3 | 功能槽与模板测试 |
| 简单题不机械四小节 | Protocol §3 + manifest anti-bloat | 简单题场景测试 |
| 模型建立/求解/结果/验证职责分离 | Protocol §7--11 | 章节能力矩阵测试 |
| Local Narrative Chain | Protocol §4 | runtime/protocol 测试 |
| Paragraph Handoff Test | Protocol §5 | runtime/protocol 测试 |
| Result → Validation Bridge | Protocol §11 + surface audit | 行为测试 |
| 目标函数在约束大括号外 | Manifest + Adapter + Q1/Q2 | 模板 validator/编译测试 |
| 非优化多方程与简单解析模型自适应 | Protocol §7.2 + rendering modes | 矩阵测试 |
| Stepwise/Pseudocode 前后闭合 | Protocol §8 | 算法呈现回归 |
| Document Length Profile | runtime contract + Protocol §18 | runtime/review 测试 |
| 装饰性引号与概念连接符 | surface pattern/audit | 行为测试 |
| 内部工作流术语防火墙 | runtime + surface audit | 行为测试 |
| 明确功能标题次序倒置 | surface audit | `question_stage_order_risk` 行为测试 |
| solver 直接以算法开场 | surface audit | `solver_first_narrative` 行为测试 |
| 连续核心图缺少邻近解释 | surface audit | `consecutive_figures_without_local_interpretation` 行为测试 |
| 专业标题不按文字机械失败 | surface audit boundary + 人工终审 | 负例测试 |
| 终审逐问闭环、表面风险和篇幅 | Review Delivery 专项清单 | 文件契约测试 |
| Q1/Q2/Q3 均有可维护示例 | Template Manifest + 三个 section 文件 | 文件与标题测试 |
| Case A/B/C 回归思想 | v7.20 execution-closure tests | 复杂题、简单题、专业标题负例 |

## 4. v8.0.0 发现的缺口与 v8.0.1 处置

1. `paper_writing_protocol.md` 已保留主要章节链，但普通 compact runtime 缺少若干旧版细节。v8.0.1 补回数据/共享基础、决策变量定义域与单位、目标现实含义、约束来源、算法输出映射、数值风格、术语、引用、图证据分型和评价边界。
2. v8.0.0 surface audit 只实现四类风险。v8.0.1 增加明确功能标题倒序、solver-first 和连续图裸堆三类保守诊断。
3. v8.0.0 终审依赖上游规则但没有显式消费 v7.20 的表面风险与篇幅检查。v8.0.1 增加专项消费清单，不复制 Authority。
4. v8.0.0 只维护 Q1/Q2 文件，Q3 仅在注释中出现。v8.0.1 增加 Q3 后问继承与扩展示例，并由 manifest 声明三个维护示例。
5. `ai_cleanup.md` 曾列出尚未自动实现的语义风险码，容易被误解为脚本已经覆盖。v8.0.1 明确区分已实现机器 finding 与人工/语义审查类别。
6. v8.0.0 的 `load_order` 能保证模板早于 Protocol，但未把逐章读取/写入时机锁成执行状态机，命题证明和伪代码也主要依赖宽泛 preload。v8.0.1 新增 mandatory `template_first_progressive_authoring`：模板检查阶段不写正文，随后每阶段执行 `read_now → write_now → gate`；命题/证明与 `stepwise/pseudocode` 分别条件读取完整 reasoning Authority 和对应 artifact pack；draft review 明确早于 AI Cleanup、编译与 final review。

## 5. 后续重构门禁

未来再拆分或精简写作模块时，必须同时满足：

- 本矩阵中的每项能力仍有唯一 Authority 和可达运行路径；
- 默认新论文仍先读 active 模板且不写正文，之后逐章读取当前规则、写当前章节并通过 gate；不得退回一次性预读全部写作/清理/编译模块；
- 命题/证明与 `stepwise/pseudocode` 的条件分支必须继续可达，并在 AI Cleanup 前完成语义审查；
- `model_establishment_solution_narrative`、Numeric/Terminology/Citation、数据预处理和图结果叙事不能只剩名称而没有可执行规则；
- 删除文字前说明替代 Authority，不能以行数下降作为能力保留证明；
- 行为可确定的部分使用行为测试，复杂数学/语义判断保留人工 review boundary，不用正则伪装能力；
- 已填写 v8 项目不自动重排、重命名或覆盖正文。
