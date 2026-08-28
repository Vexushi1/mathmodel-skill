# v7.16.0 论文写作规范回滚与 Skill 优化实施计划

> 状态：CANONICAL IMPLEMENTATION PLAN  
> 计划编号：RP-01  
> 当前基线：v7.15.0 / `main@6827cb781bf34ad4c15c6714e376d810a52a7b9a`  
> 工作分支：`upgrade/v7.16.0-paper-writing-spec`  
> 目标版本：v7.16.0（minor，向后兼容的写作能力增强）  
> 适用仓库：`Vexushi1/mathmodel-skill`

---

## 0. 文档地位与执行纪律

本文档是本轮论文写作规范回滚与优化的**实施基准**。后续修改写作、模型表达、AI Cleanup、终审和相关测试时，必须先核对本文档，不得依据旧聊天中的仓库结构猜测直接改文件。

执行纪律：

1. 不整体回滚旧版本，不把 `legacy/` 变成活动依赖；本轮只恢复历史上有价值且仍适用于当前架构的论文写作语义。
2. 不在多个文件复制同一规则。严格遵守 `SKILL_CHANGE_GOVERNANCE.md` 的单一事实源原则。
3. 当前 v7.15.0 已采用 `core/ + modules/ + packs/ + scripts/` 权威架构，**不再按旧计划新建一套 `.codex/skills/paper-section-writer/references/*` 规范树**。旧计划中这部分视为架构假设失效，禁止实施。
4. 保留当前正确机制：`模型论文框架.md` 作为语义记忆、已验收工作簿作为数值事实源、Human Model Approval、Model Challenge、result-analysis evidence disposition、Figure Contract、LaTeX audit、Hard/Default/Recommendation 分级。
5. 先修改权威合同，再修改 consumer；脚本只检查机器可靠判断的结构，不通过正则“证明”数学或写作质量。
6. 每批修改后运行对应回归测试；CI 未通过前不得宣称完成。

---

# 1. 修改简报

```text
修改主题：恢复并强化数学建模论文写作规格，重点修复摘要、优化模型表达、算法说明、小节颗粒度与中文过度声称
当前版本：7.15.0
目标版本：7.16.0
变更等级：minor
直接目标：
  1. 让写作阶段稳定读取并执行完整论文结构与章节写法；
  2. 对优化题强制呈现模型类型、决策变量、目标函数、约束与求解器角色；
  3. 区分 Model / Solver / Validator；
  4. 解释多算法为何使用、复用或更换；
  5. 控制问题章节内部二级小节过度碎片化；
  6. 强化中文摘要与正文的 claim calibration；
  7. 恢复有价值的旧版写作语义，但不恢复全自动和模板主义。
明确不做：
  - 不重构求解/绘图/工作簿架构；
  - 不增加第二套写作事实源；
  - 不强制固定一级章节数量；
  - 不强制每问固定同名小节；
  - 不新增算法百科或固定高级模型清单；
  - 不让脚本判断数学正确性或模型最优性。
权威事实源：
  - core/bootstrap.yaml
  - SKILL_CHANGE_GOVERNANCE.md
  - core/writing_reasoning_contract.yaml
  - modules/05_writing/latex.md
  - modules/05_writing/ai_cleanup.md
  - packs/task/optimization.md
  - modules/02_model_design.md
  - modules/06_review_delivery.md
  - scripts/audit_paper_prose.py
预计修改文件：见第 11 节
禁止触碰文件：legacy/；与本轮无关的数值求解、绘图和工作簿 schema
兼容性要求：旧项目可读；新增规则按 Hard/Default/Recommendation 分级，不用新规则倒逼旧结果重算
迁移要求：无目录破坏；必要时仅增加 framework 可选字段/检查提示，旧项目缺失时按需补齐
验收测试：见第 12 节 T01–T20
回滚方式：回滚本 PR；不影响 v7.15 已验收项目的数值事实与工作簿
```

---

# 2. 问题定性：不是“没有写作规则”，而是关键写作合同仍不够显式

v7.15.0 已经存在较强写作基础：

- `core/writing_reasoning_contract.yaml` 已覆盖公式 Source→Derivation→Destination、shared foundation、cross-question progression、structure-before-algorithm、algorithm presentation、numeric style 等；
- `modules/05_writing/latex.md` 已明确摘要、问题重述、问题分析、假设符号、共享基础、公式推导等正文规则；
- `modules/05_writing/ai_cleanup.md` 已有模板感、过度声称、算法百科、Paragraph Necessity、数字风格等清理规则；
- `packs/task/optimization.md` 已要求完整目标函数、约束集合、变量定义域、可行性与最优性证据。

因此本轮不能“再造一套 writer”。真正缺口集中在：

1. **优化模型的论文表达合同还不够显式**：模型设计阶段知道变量/目标/约束，但论文阶段仍可能先写算法，再把目标函数埋在后面。
2. **模型名称缺少标准数学类型约束**：题目专属名字可能很好听，但评委看不出它到底是优化、微分、统计还是图模型。
3. **Model / Solver / Validator 的角色分离不够显式**：计划库、DE、Dual Annealing、局部精修等容易在摘要或标题里抢占“模型”位置。
4. **摘要对优化题的信息闭合不足**：当前摘要优先“对象/模型结构→结果→判断”，但没有明确要求优化类问题至少交代目标函数。
5. **多算法使用理由缺少论文级合同**：已有 structure-before-algorithm，但需要进一步约束“为什么本问沿用/更换算法、替代算法是什么角色”。
6. **问题章节内部小节过多的风险没有直接治理**：教师反馈指向的是 subsection fragmentation，不是一级章节过多。
7. **中文 claim calibration 还可进一步具体化**：尤其摘要中的“显著、最优、证明、稳定性很好”等词，需要和实际证据等级绑定。

---

# 3. 教师反馈转化为跨项目规则

## 3.1 小节过多：只治理 subsection，不限制一级章节

教师反馈“不要分这么多章”在本次实例中指**每个问题章节内部二级小节过多**。

因此新增/强化 Default 规则：

- 一个问题章节优先形成 3–4 个主要二级小节；
- 超过 4 个不是自动错误，但必须检查是否存在可合并的同一论证链；
- “决策变量、目标函数、约束、核心模型汇总”优先在“模型建立”内连续展开，不机械各自升成二级标题；
- “活跃边界、消融、独立算法挑战、局部验证”若都服务于结果可信性，优先并入“结果分析/模型检验”；
- 禁止设置“一级章节最多 N 个”的错误规则。

机器审计只能给 `review_required` / warning，不能按标题数量自动判论文失败。

## 3.2 多算法：必须解释角色与必要性

算法第一次在正文作为主求解器出现时，需要说明其适配当前结构的理由：

```text
当前数学结构/困难
→ 为什么经典直接法不足或为什么该类算法适配
→ 算法在本问承担的具体角色
```

同一算法后续复用：只需说明为什么继承结构后仍适用，不重复算法百科。

不同问题更换算法：说明新增结构（组合性、非光滑、离散任务分配、规模、不确定性等）如何改变求解需求。

如果正文写“也采用了另一算法”，必须满足：实际运行、有 artifact、有可比指标，并明确它是 baseline / alternative / validator，而不是为了显得工作量大。

## 3.3 模型命名必须包含标准类型

自定义名称允许，但第一次正式出现时应能识别标准数学类型。

推荐形式：

```text
题目专属机制 + 标准数学模型类型
```

例如：

- “共享航迹三弹时域并集模型” → “共享航迹约束下的三弹联合遮蔽时长优化模型”；
- “三机单弹协同时域覆盖模型” → “多无人机时域互补的联合遮蔽时长优化模型”。

标准类型包括但不限于：连续优化、非线性优化、非光滑优化、混合整数优化、多目标优化、微分方程、回归、时间序列、图模型、仿真等。

题目专属机制是加分信息，不能替代标准类型。

## 3.4 优化模型写作顺序

优化类问题正式“模型建立”默认采用：

```text
模型类型与现实目标
→ 决策变量
→ 目标函数（单独展示）
→ 目标现实含义
→ 约束条件（按来源解释）
→ 最终核心模型汇总
→ 求解算法
```

核心模型汇总继续保留，但它是 recap，不替代变量、目标和约束的解释。

## 3.5 中文语言与摘要：证据强度决定措辞

论文不得把启发式/局部/有限搜索证据润色成严格证明。

建立证据等级：

- `PROVEN`：严格数学证明；
- `VERIFIED_NUMERIC`：多分辨率、独立算法、重复/边界等数值验证；
- `COMPARATIVE`：和实际测试 baseline/alternative 的比较；
- `OBSERVED`：当前方案/样本中的观察；
- `HEURISTIC`：启发式搜索得到的当前方案。

典型措辞：

- 无统计检验时，“显著提高”改为“提高 X% / X 单位”；
- “证明模型有效”改为与实际验证范围一致的表述；
- “全局最优”必须有相应证明/最优性证据；
- “鲁棒性很强”改为写明扰动范围和保持的 claim；
- “独立算法未发现更优”只能支持“在所检验范围内未发现更优”。

摘要执行最严格的 claim calibration。

---

# 4. 权威文件职责调整

## 4.1 `core/writing_reasoning_contract.yaml`：跨竞赛语义权威

本轮主要在这里新增/强化跨竞赛可复用的推理合同，避免把同一规则复制进多个模块。

计划新增/强化：

### A. `model_solver_validator_roles`

明确：

```text
MODEL = 数学上求什么
SOLVER = 如何求模型
VALIDATOR = 如何独立检查求解/结论
```

并规定题目专属求解架构不得冒充标准模型类型。

### B. `optimization_model_expression`

适用于 optimization / scheduling / routing / allocation / control 等目标驱动问题：

- 决策变量必须闭合；
- 目标函数必须显式；
- 目标函数现实含义必须解释；
- 约束按来源组织；
- 核心模型汇总 adaptive；
- solver 在模型语义闭合之后出现。

### C. `solver_justification`

与现有 `structure_before_algorithm` 连接：

- first-use justification；
- repeated-use inheritance explanation；
- changed-solver structural delta explanation；
- alternative algorithm role evidence requirement。

### D. `subsection_granularity`

只定义 Default 级别的逻辑颗粒度原则，不绑定固定章节名或硬数量。

### E. `claim_strength_calibration`

将 PROVEN / VERIFIED_NUMERIC / COMPARATIVE / OBSERVED / HEURISTIC 与允许表述建立语义映射；机器只能检查明确越界模式，不推断证据是否真的充分。

## 4.2 `modules/05_writing/latex.md`：正文结构与表达权威

这里把 reasoning contract 落到实际论文文字。

重点修改：

1. **摘要**：对优化类小问加入信息闭合要求：标准模型类型、核心决策变量、目标函数、必要约束、主求解器、关键结果、直接判断；根据篇幅压缩，但 `objective_function` 不能消失。
2. **模型命名**：第一次正式出现应包含或紧邻标准模型类型。
3. **优化模型建立**：新增“变量→目标→约束→模型汇总→算法”的正文默认顺序。
4. **算法说明**：区分主求解器、边界精修、替代算法、验证算法；算法原理只写与本题结构有关的部分。
5. **小节颗粒度**：问题章节内部默认 3–4 个主二级小节，强调“减少标题，不减少技术内容”。
6. **结果分析**：headline result 至少形成“数值→比较/边界→机制或现实意义→证据范围”的闭环；不机械要求每个辅助数字三维展开。
7. 保留现有“不强制独立结论一级章”的 CUMCM Default，不因本轮教师反馈改变一级章节策略。

## 4.3 `modules/05_writing/ai_cleanup.md`：表现层风险清理

新增/强化：

- 中文夸张措辞与证据等级不匹配；
- model/solver/validator 概念混用；
- 模型名只有题目花名、无标准数学类型；
- 一个问题章节二级标题过密、每节只承载一个公式/图表；
- “采用 A、B、C、D 算法”但没有角色或必要性；
- 结果分析只有“由图可知/结果较好”而没有量化证据与意义。

仍坚持：AI Cleanup 不建立第二套正文规则，只引用 authority。

## 4.4 `packs/task/optimization.md`：原则上小改或不改

当前 pack 已明确决策变量、目标函数、约束和最优性证据。本轮只在确有必要时增加**写作交接提示**：模型设计阶段应把标准模型类型、决策变量、目标函数、核心约束和理论性质写入 `模型论文框架.md`，供 Module 05 消费。

若 `modules/02_model_design.md` 已完整承载该 handoff，则不重复修改 optimization pack。

## 4.5 `modules/02_model_design.md` / `模型论文框架` 模板：检查上游信息是否足够

写作不能在最后阶段猜“这是什么模型、目标函数是什么”。因此检查当前 framework 是否稳定保存：

- standard model type；
- decision variables；
- objective function；
- core constraints；
- solver role；
- validator role；
- algorithm justification；
- claim scope。

若已有等价字段，只复用；若缺失，采用最小可选字段扩展，不做大规模 schema 重构。

---

# 5. 摘要合同（P0）

## 5.1 通用每问摘要

每问应尽可能包含：

```text
对象 / 问题目标
→ 标准模型类型 + 题目专属结构
→ 核心求解或估计方式
→ 高精度 headline result
→ 对设问的直接判断
```

## 5.2 优化类每问摘要

优化题额外要求至少可恢复：

```text
model_type
+ decision_variables
+ objective_function
+ key_constraints（只保留最关键者）
+ main_solver
+ headline_result
+ conclusion
+ claim_scope
```

摘要不要求展示完整公式，但必须用自然语言明确“最大化/最小化什么”。

如果一个优化段落只写“建立 XX 模型，采用 DE 求解，得到 XX”，而没有目标函数，应判为 `review_required`，正式交付前修复。

---

# 6. 优化模型正文合同（P0）

默认写作结构：

### X.1 模型建立

1. 一句话说明标准模型类型和现实目标；
2. 定义决策变量及单位/范围/连续离散类型；
3. 单列目标函数；
4. 解释目标函数为什么对应题意；
5. 分组说明约束来源；
6. 需要时给出核心模型汇总。

### X.2 模型求解

1. 先说明数学结构：线性/凸/非凸/非光滑/组合/分解等；
2. 说明为何采用当前 solver；
3. 若有多阶段求解，解释各阶段角色；
4. 不介绍通用算法百科。

### X.3 结果分析

1. headline result；
2. baseline / 场景 / 边界对比；
3. 机制或现实含义；
4. 验证证据和 claim scope。

### X.4 模型检验（确有独立证据时）

独立验证、消融、敏感性、鲁棒性等只有在内容足够独立时单列，否则并入结果分析。

---

# 7. 问题重述与问题分析：恢复后禁止再次退化

当前 `modules/05_writing/latex.md` 已经较完整，本轮主要做回归测试和必要加固，不重复再造规范。

必须保持：

- 问题重述回答“要解决什么”，不提前放模型名、算法、最终数值；
- 问题分析回答“难点在哪里、抓住什么、依赖什么、哪类模型适配”；
- 多问论文按问分析；
- 替换题目对象名后仍适用于任意赛题的通用段落应重写。

---

# 8. 结果讨论与“内容更丰富立体”的边界

教师提出可以增加其他算法结果、误差等，使内容更立体。Skill 应吸收为：

- **允许并鼓励有证据的对照**；
- 不鼓励算法数量本身；
- alternative/baseline/validator 必须有真实计算 artifact；
- 比较指标必须同口径；
- 说明比较的目的：选模、搜索充分性、误差验证、边界检查，而不是“为了显得做得多”。

headline result 讨论优先从以下维度选择 2–3 个真正有证据的维度：

- baseline comparison；
- sensitivity / robustness；
- numerical certification；
- physical/domain meaning；
- cross-question consistency；
- uncertainty / interval。

不再设置“每个数字必须机械三维讨论”的硬模板。

---

# 9. AI 模板感与吹牛控制

重点检查中文竞赛常见风险：

- “具有重要意义”“提供参考价值”“较好地解决”；
- 无统计检验的“显著”；
- 无严格证据的“证明”“全局最优”“保证”；
- “表现出很强的鲁棒性/稳定性”却不写扰动范围；
- “明显优于其他方法”却没有实际 baseline；
- 多段机械“首先、其次、最后”；
- “由图可知”之后没有关键数字、机制或判断；
- 用“耦合、驱动机制、多尺度、理论框架”等抽象词包装普通关系。

建议机器层仅对高风险词 + 邻近证据线索做保守 warning/review_required；最终是否合理仍由人工/语义审查判断。

---

# 10. QA 与静态审计

## 10.1 `scripts/audit_paper_prose.py`

只增加机器可靠检查：

- optimization question section 中明显存在 solver 名但缺乏 max/min/objective 线索时给 review_required（只做保守提示）；
- 问题章节二级标题密度异常时 warning；
- 高频绝对/夸张 claim 模式 warning/review_required；
- 标题/摘要中的算法名密度高而模型类型缺失时 warning；
- 不得自动修改正文；不得声称数学错误。

如果该类规则无法在低误报下可靠实现，则只放入 Module 06 人工 review checklist，不强行编码。

## 10.2 `modules/06_review_delivery.md`

新增 Paper Writing Specification Review：

```text
[ ] 摘要逐问闭合；优化题目标函数没有消失
[ ] 模型名能识别标准数学类型
[ ] Model / Solver / Validator 角色没有混淆
[ ] 优化模型按变量→目标→约束→求解展开
[ ] 多算法均有角色与必要性
[ ] 问题章节内部没有明显标题碎片化
[ ] headline result 有量化证据、意义和证据边界
[ ] claim strength 与证据等级匹配
[ ] 问题重述与问题分析职责清楚
```

---

# 11. 预计修改文件与阶段

## P0：核心写作语义

必须修改：

- `core/writing_reasoning_contract.yaml`
- `modules/05_writing/latex.md`
- `modules/05_writing/ai_cleanup.md`

检查后决定是否修改：

- `modules/02_model_design.md`
- `templates/model/model_paper_framework.md`
- `packs/task/optimization.md`

P0 目标：摘要、模型命名、优化模型表达、Model/Solver/Validator、多算法说明、小节颗粒度、claim calibration 全部在 authority 层闭合。

## P1：终审与机器检查

- `modules/06_review_delivery.md`
- `scripts/audit_paper_prose.py`
- 对应 tests

仅把可可靠静态检测的规则写入脚本。

## P2：路由/版本/生成文件

检查是否需要：

- `core/workflow_router.yaml`（通常无需新增 route，只确认 writing route 已加载 authorities）
- `core/bootstrap.yaml` 版本号
- plugin manifest / version carriers
- `CHANGELOG.md`
- 生成索引和 `MANIFEST.sha256`

不得手工改生成文件；统一走 `scripts/generate_indexes.py`。

## P3：文档与发布

- README/README-zh 只在用户可见能力发生变化且确有必要时更新；
- 完成 PR、CI、版本一致性检查；
- 合并后再宣称进入 main。

---

# 12. 回归测试 T01–T20

| ID | 场景 | 预期 |
|---|---|---|
| T01 | 写问题重述 | 不提前写模型名/算法/最终数值 |
| T02 | 写问题分析 | 包含难点、抓手、依赖、模型类别，不是算法目录 |
| T03 | 优化题摘要只写模型+DE+结果 | 检出缺 objective，要求补“最大化/最小化什么” |
| T04 | 自定义模型名无标准类型 | review_required / 写作规则要求补标准类型 |
| T05 | 正文先讲 DE 再定义变量目标 | 要求重排为模型闭合后再讲 solver |
| T06 | 同一算法跨问复用 | 要有继承适用理由，无需重复百科 |
| T07 | 不同问题更换算法 | 要说明新增数学结构导致的求解需求变化 |
| T08 | 写“也采用某算法”但无 artifact | 禁止生成对照数值/误差 |
| T09 | 一个问题有 6–7 个二级小节 | 触发 granularity review，不自动判失败 |
| T10 | 将一级章节数量设硬上限 | 测试应确保不存在此规则 |
| T11 | 核心模型汇总存在 | 保留，但不能替代变量/目标/约束解释 |
| T12 | “显著提高 20%”无统计检验 | 改为“提高 20%”或说明显著性依据 |
| T13 | 独立算法未发现更优 | 禁止升级为“证明全局最优” |
| T14 | 启发式搜索结果 | 允许“当前认证方案/所得方案”，控制 claim scope |
| T15 | headline 只有裸数字 | 要求至少补比较/意义/验证边界中的有效内容 |
| T16 | 摘要/正文同一核心数值 | 必须来自同一已验收工作簿并保持必要精度 |
| T17 | solver/validator 被写进模型名 | 提示角色混淆 |
| T18 | AI Cleanup 遇到算法百科 | 删除/压缩，保留本题适配理由 |
| T19 | 旧项目缺新增可选 framework 字段 | 仍可读；写作阶段按需补齐，不倒逼重算 |
| T20 | 机器审计无法判断数学正确性 | 只 warning/review，不产生虚假的 blocking 结论 |

基础测试仍必须执行：

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests
python scripts/generate_indexes.py --check
```

若修改路由、framework、prose audit 或版本 carrier，再追加对应专项测试。

---

# 13. 验收标准

完成后应达到：

1. 写作阶段不依赖聊天记忆猜章节规范；
2. 现有“问题重述/问题分析”规则不会再次因精简而丢失；
3. 优化类论文在评委进入正文很早的位置即可识别：**模型类型、决策变量、目标函数、核心约束**；
4. 模型、求解算法、验证算法角色清楚；
5. 摘要中的优化问题不会只报算法而漏掉目标函数；
6. 自定义模型名称不会掩盖标准数学类型；
7. 多算法出现是因为角色不同或结构需要，而不是堆工作量；
8. 问题章节内部减少无必要二级标题，但不减少技术内容；
9. 核心模型汇总继续保留为快速恢复模型的工具；
10. 中文摘要和正文的 claim 强度与证据边界一致；
11. 旧项目和 v7.15 的数值/工作簿/绘图语义不被破坏；
12. 单一事实源不被破坏，不新增一套平行 writer 规范。

最终标准：

> 任何一次正式论文写作，都应先恢复当前项目语义和写作 authority，再让评委清楚看到“这是什么模型、变量是什么、优化/估计什么、约束是什么、为什么这样求、证据能支持到什么程度”，而不是用算法名、复杂标题和强势措辞代替数学模型本体。

---

# 14. 实施日志模板

每批提交/PR 更新按以下格式记录：

```text
Plan: RP-01
Phase: P0 / P1 / P2 / P3
Plan sections implemented:
Files changed:
Authority changed:
Consumer changed:
Legacy semantics restored:
Teacher-feedback rules added:
Compatibility:
Tests run:
Known gaps:
Next step:
```

若实施发现计划与当前仓库事实冲突，应先更新本文档再继续修改。