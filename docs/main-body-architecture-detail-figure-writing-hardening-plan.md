# v7.19.0 Main-Body Writing Closure 详细修改计划

> 状态：**PLANNING ONLY / 待用户审查**  
> 当前正式基线：HSK Skill `v7.18.0`  
> 基线 `main`：`3209f884cc965791ae32b183bf5b37c7be38e075`  
> 计划分支：`upgrade/v7.19.0-main-body-writing-closure`  
> 暂定目标版本：`v7.19.0`（仅在正式实现、人工写作 smoke、完整 CI 全部通过后升级）  
> 修改主题：**符号说明之后的正文宏观编排、详略分配、图结果叙事闭环**

---

## 0. 修改简报

```text
修改主题：Main-Body Writing Closure
当前版本：7.18.0
目标版本：暂定 7.19.0
变更等级：minor（新增向后兼容的论文写作能力，不改变数值/模型/runtime 接口）
直接目标：
1. 让符号说明之后的正文顺序优先服从真实求解依赖与数学推进，而不是固定论文模板；
2. 建立“详写什么、略写什么”的技术信息分配规则，保证模型建立与求解详略得当；
3. 完善图结果叙事，使图的身份、关键特征、决定性数值、设问含义、形成原因和必要收束形成局部闭环；
4. 增加整篇 main body 的宏观闭环检查，确认每个章节都在推进问题答案。

明确不做：
- 不修改模型数学语义、模型设计 Gate、Human Model Approval、03A/03B；
- 不修改 Numerical Verification/PQS、Workbook Schema、Project State Schema、Task Taxonomy；
- 不改变 Python/MATLAB 职责；
- 不增加固定章节模板、固定标题数量、固定句式、连接词词库或图分析“六句话模板”；
- 不把任何单篇优秀论文的章节顺序或句子作为 runtime 模板；
- 不为“写得更顺”删除真实边界、异常、失效条件或必要数学步骤。

权威事实源：
- core/writing_reasoning_contract.yaml
- modules/05_writing/latex.md
- modules/05_writing/ai_cleanup.md

预计修改文件：
- core/writing_reasoning_contract.yaml
- modules/05_writing/latex.md
- modules/05_writing/ai_cleanup.md
- PROJECT_INSTRUCTIONS.md（仅入口摘要，必要时）
- tests/test_v719_main_body_writing_closure.py
- README.md / CHANGELOG.md / version carriers（仅正式发布阶段）
- generated indexes / MANIFEST（仅通过 generator 产生）

禁止触碰文件：
- core/model_approval_contract.yaml
- core/numerical_verification_contract.yaml
- core/workbook_schema.yaml
- core/project_state.schema.yaml
- core/task_taxonomy.yaml
- modules/02_model_design.md
- Python/MATLAB 求解与绘图语义文件

兼容性要求：
- 旧项目、旧模型论文框架、旧工作簿无需迁移；
- 新规则均为 Writing Default / Review guidance，不新增 runtime Gate；
- 旧论文若已有合理章节顺序，不因未显式登记新内部字段而 stale；
- 不引入新的必填 Schema 字段或 CLI 参数。

迁移要求：无 Schema/CLI/目录迁移。

验收测试：
- static contract lint；
- 全量 unittest；
- generated-file contract；
- v7.19 writing regression；
- 六类以上人工 prose smoke；
- 三套 LaTeX + Production LaTeX attestation；
- merge 后 main CI 全绿。

回滚方式：
- 若新写作规则造成模板化或误伤合理结构，回滚本次 writing authority/consumer/test 变更即可；
- 因无 Schema/CLI/模型语义变化，不需要项目数据迁移或兼容脚本。
```

---

# 1. 问题重新定义

v7.18.0 已经解决了“小问内部模型建立—模型求解—结果解释怎样连续写”的主要问题，当前已有：

- Continuous Mathematical Narrative；
- Formula Prose Rhythm；
- Functional Transition Governance；
- Professional Heading Semantics；
- Model-to-Solver Bridge；
- Result-adjacent Interpretation；
- Cross-question incremental writing；
- Paragraph Necessity 与 subsection granularity。

本轮不是推翻 v7.18，而是在其上补齐**整篇正文尺度的写作闭环**。

当前剩余问题主要有三类。

## 1.1 宏观正文顺序仍偏“章节骨架”，未充分服从真实求解依赖

当前论文骨架能告诉 Agent 常见章节有哪些，也能告诉后问只写增量，但还没有明确要求：

> **从“符号说明”之后开始，正文各章节、各问题、共享基础、模型建立、求解与结果的顺序，应优先映射真实的数学依赖与求解顺序。**

因此仍可能出现：

- 论文按“模板顺序”排，而实际求解先后不同；
- 某个后续章节真正依赖的结构在很后面才解释；
- 某个结果被提前使用，证据来源却晚于它出现；
- 多问之间存在真实输入输出依赖，但正文没有体现；
- 本应作为共享基础的内容重复散落在多个问题内；
- 正确的技术内容存在，但章节之间没有形成“前一节产出 → 后一节消费”的主线。

本轮拟把这一问题实质化为 **Post-Notation Main-Body Architecture**。

## 1.2 当前会“删冗余”，但还没有明确“哪里应该详、哪里应该略”

Paragraph Necessity 可以回答“该段是否必要”，subsection granularity 可以回答“是否拆得过碎”，但不能完全回答：

> **必要内容应该写到什么深度？**

当前可能出现两种相反风险：

- 核心推导过于压缩，评委无法恢复思路；
- 普通代数、标准算法、重复符号、继承关系写得过细，挤占真正关键的模型机制和结果解释。

本轮拟新增 **Detail Allocation Governance**，把“详略得当”从经验描述变成可执行的写作判断。

## 1.3 当前图表 profile 已有“趋势—数值—原因—结论”，但图的叙事入口与收束仍可更完整

v7.18 已要求关键结果邻接解释，但对于图像结果，仍可进一步明确：

- 图第一次出现时应让评委立即知道“这张图展示哪两个/哪几类量之间的关系”；
- 分析只抓决定结论的特征，而不是逐点读图；
- 特征必须回到当前问题，而不是停留在视觉描述；
- 原因解释应来自模型结构、约束、机制或数据规律；
- 若该图承担当前小问的关键证据，应有一句极简收束，把图证据返回到答案或后续求解步骤。

本轮拟把该逻辑固化为 **Figure Result Narrative**。

---

# 2. 总体设计原则

## 2.1 单一 Authority，不新增第二套写作系统

本轮所有新增跨题型写作规则仍放在：

`core/writing_reasoning_contract.yaml`

拟优先扩展现有：

`model_establishment_solution_narrative`

而不是新增：

- `main_body_writing_contract.yaml`；
- `figure_narrative_contract.yaml`；
- `detail_allocation_contract.yaml`；
- 新 Module；
- 新 runtime Gate。

`latex.md` 只负责正文落地，`ai_cleanup.md` 只负责表现层复查，不重复定义第二套规则。

## 2.2 逻辑功能优先，不做固定模板

所有新增规则必须表达“功能顺序”，不能变成：

- 固定章节数量；
- 固定章节名称；
- 固定六句图表分析；
- 固定“先模型准备，再问题一……”；
- 固定“本文首先、其次、最后”；
- 固定“XX 的 XX”标题语法。

## 2.3 求解事实优先于写作美观

正文顺序可以为了阅读做局部前置说明，但不得：

- 改变真实模型依赖；
- 把结果当成前提；
- 删除约束/边界；
- 为顺畅而跳过关键推导；
- 把验证结果提前包装成模型假设；
- 把图上的数值现象改写成理论证明。

## 2.4 不改变模型层与数值层

本轮只调整**已批准模型和已验收结果如何进入论文**。

不改变：

- 数学模型是什么；
- solver 如何运行；
- validator 如何判定；
- 工作簿怎样存结果；
- MATLAB 如何读取 Python 输出；
- Human Approval 与 03A/03B 责任边界。

---

# 3. 新增能力一：Post-Notation Main-Body Architecture

## 3.1 目标

让“符号说明”之后的正文顺序优先映射：

> **实际求解依赖 + 数学对象依赖 + 小问输入输出依赖 + 证据出现顺序。**

不是先选一个漂亮论文目录，再把技术内容塞进去。

## 3.2 拟新增 Authority 结构

拟在 `model_establishment_solution_narrative` 下增加：

```yaml
post_notation_main_body_architecture:
  governance_level: default
  principle: ...
  ordering_basis:
    - mathematical_dependency
    - actual_solution_sequence
    - shared_foundation_dependency
    - cross_question_input_output_dependency
    - evidence_before_claim
  preferred_progression:
    - recover_shared_or_local_prerequisite
    - establish_relation_needed_downstream
    - solve_current_mathematical_task
    - present_and_interpret_current_evidence
    - pass_only_needed_output_to_next_task
  architecture_checks:
    - prerequisite_before_use
    - result_not_used_before_evidence
    - shared_structure_not_repeated_without_need
    - later_question_consumes_declared_prior_output
    - independent_questions_not_forced_into_false_dependency
    - section_has_downstream_role_or_direct_answer_role
  hard_count_limit: false
```

名称最终可微调，但语义保持上述范围。

## 3.3 正文排序的优先级

拟明确以下优先级：

### A. 真实数学依赖优先

如果 B 的定义或求解依赖 A，则默认 A 在 B 之前出现。

例如：

```text
轨迹关系
→ 几何判据
→ 临界时刻
→ 有效时长
→ 优化目标
→ 参数搜索
```

不能为了章节对称把“优化模型”提前，再回头补判据来源。

### B. 共享基础优先于重复恢复

若多个小问共同依赖：

- 坐标系；
- 状态方程；
- 公共概率关系；
- 网络结构；
- 统一评价指标；

且单独列共享基础能够明显减少重复，则在第一个消费问题之前集中建立。

若共享内容很短，则不强制单列“模型准备”。

### C. 多问题目的真实输入输出依赖要在行文中可恢复

例如：

```text
问题一输出阈值 T*
→ 问题二以 T* 限定搜索域
→ 问题二输出资源配置
→ 问题三在该配置下做动态调整
```

正文必须让评委知道“前问的哪个输出被后问使用”，而不是只写“基于问题一结果”。

### D. 独立小问不得虚构递进

如果问题二与问题一实际上独立，就不为了“文章连贯”强行写成继承关系。

### E. Evidence Before Claim

任何定量结论、趋势、最优参数或稳定性主张，原则上在相应工作簿/图表/验证证据已经被引入后再正式提出。

## 3.4 符号说明之后的正文组织检查

在整篇正文初稿生成前，内部建立一个**轻量 Main-Body Dependency Map**，只记录：

```text
section_or_task
→ prerequisite
→ produces
→ consumed_by
→ evidence_anchor
```

注意：

- 这是内部写作辅助，不新增 Project State Schema；
- 不要求进入论文正文；
- 不要求旧项目持久化；
- 不作为 runtime Gate；
- 可以从当前 `模型论文框架.md` 的已有 dependency 信息推导，不新建重型 artifact。

## 3.5 宏观闭环检查

写完整篇正文后增加 Main-Body Narrative Closure Review：

逐个检查符号说明后的核心章节：

1. 为什么它在这里出现？
2. 它消费了什么已建立对象/结果？
3. 它产出了什么关系、参数、证据或结论？
4. 这个产出被后面哪里使用，或是否直接回答设问？
5. 若删除该章节，是否会破坏求解主线？
6. 是否存在“正确但不服务任何后续任务/答案”的孤立技术块？
7. 是否存在结果先出现、依据后补的逆序？

这套检查是 review/default，不通过关键词自动 block。

---

# 4. 新增能力二：Detail Allocation Governance

## 4.1 目标

把“详略得当”实质化为：

> **写作篇幅和推导深度应与该内容对最终模型、求解、证据和答案的重要性匹配。**

不是“越详细越好”，也不是“越短越高级”。

## 4.2 拟新增 Authority 结构

```yaml
detail_allocation_governance:
  governance_level: default
  principle: ...
  expand_when:
    - relation_changes_model_structure
    - criterion_or_boundary_is_decisive
    - derivation_reduces_dimension_or_feasible_region
    - parameter_or_constraint_source_is_nonobvious_and_decisive
    - solver_choice_depends_on_local_structure
    - result_is_headline_answer_or_changes_decision
    - exception_or_failure_boundary_changes_claim
  compress_when:
    - routine_algebra
    - already_defined_symbol_translation
    - standard_algorithm_history_or_generic_advantage
    - inherited_relation_without_change
    - intermediate_quantity_without_independent_role
    - repeated_table_or_curve_readout
    - implementation_detail_better_suited_for_appendix
  preserve_even_if_long_when:
    - omission_breaks_semantic_closure
    - omission_hides_decisive_constraint
    - omission_prevents_reproducible_solution_logic
    - omission_hides_exception_or_failure_boundary
  rule: ...
```

## 4.3 应详写的内容

### A. 决定模型成立的关键关系

例如：

- 精确几何判据；
- 状态转移方程；
- 关键概率结构；
- 目标函数从题意到数学量的转换；
- 关键资源/时序/边界约束来源。

### B. 使问题发生结构变化的推导

例如：

- 连续判定转化为临界边界搜索；
- 高维优化降维；
- 候选域缩减；
- 原始组合问题分解；
- 单调性/凸性/对称性带来的简化；
- 前问结论对后问搜索空间的限制。

### C. 直接决定 solver 选择的结构

不是详写算法历史，而是详写：

- 为什么可导/不可导；
- 为什么是混合离散—连续；
- 为什么存在多个局部区间；
- 为什么可做分解；
- 为什么需要全局搜索 + 局部精化；
- 为什么直接解析法已经足够。

### D. 直接决定答案的结果与边界

例如：

- 最优参数；
- 临界阈值；
- 决策转折点；
- 决定结论的敏感参数；
- 会使主结论失效的异常或边界。

## 4.4 应压缩的内容

### A. 普通代数

若只是从式（10）代入式（11）整理得到式（12），且没有新的结构信息，可压缩为一句或附录。

### B. 重复符号解释

符号首次定义后，不在每个公式后逐项翻译。

### C. 标准算法百科

算法未修改时，正文只保留本题：

- 编码/变量；
- 目标/适应度；
- 约束处理；
- 关键参数；
- 初值；
- 精度与终止；
- 输出映射。

### D. 后问完全继承的关系

只用短承接恢复，不重新推导。

### E. 没有独立作用的中间量

若某中间量只在一个式子里短暂出现，可就地定义，不单独建表或小节。

### F. 图表逐格/逐点复述

只抓决定结论的趋势、区间、极值、拐点和关键数值。

## 4.5 详略判断的四级证据权重

为了让 Agent 真正可执行，拟增加内部写作判断：

```text
Tier S：直接决定模型结构或最终答案 → 必须清楚展开
Tier A：决定 solver、关键参数、边界或验证结论 → 适度展开
Tier B：辅助解释、次要中间关系 → 压缩表达
Tier C：重复、百科、实现细节、无下游作用 → 删除/附录
```

注意：

- 这是写作信息预算，不是数学重要性评分 Schema；
- 不进入正文；
- 不要求 YAML 项目持久化；
- 不允许机器仅凭公式数量自动判层级；
- 由当前模型依赖和答案证据确定。

## 4.6 与 Paragraph Necessity 的关系

现有 Paragraph Necessity 解决：

> “这段要不要存在？”

新增 Detail Allocation 解决：

> “这段既然要存在，应写到多深？”

两者不得重复定义。

建议执行顺序：

```text
Need?（Paragraph Necessity）
→ Important how much?（Detail Allocation）
→ Place where?（Main-Body Architecture）
→ Write how?（Continuous Narrative / Formula Rhythm）
```

---

# 5. 新增能力三：Figure Result Narrative

## 5.1 目标

对承担正文证据作用的结果图，使文字分析形成：

> **图的身份 → 关键特征 → 决定性数值 → 当前设问含义 → 形成原因 → 必要收束**

但明确这是**信息功能顺序**，不是六句固定模板。

## 5.2 拟扩展现有 `result_adjacent_interpretation.curve_or_figure`

优先不新增平行 authority，而是在现有 profile 中补充：

```yaml
curve_or_figure:
  preferred_progression:
    - figure_identity_or_displayed_relation
    - key_trend_extremum_turning_point_or_interval
    - decisive_value_when_needed
    - implication_for_current_question
    - mechanism_or_model_reason_for_pattern
    - concise_closure_when_figure_is_decisive
```

并增加：

```yaml
figure_identity_rule: ...
feature_selection_rule: ...
question_link_rule: ...
mechanism_explanation_rule: ...
closure_rule: ...
anti_repetition_rule: ...
```

## 5.3 Figure Identity Sentence

图第一次进入正文时，邻近文字应让评委快速知道：

- 图展示什么对象；
- 哪些量之间的关系；
- 为什么这张图在当前步骤出现。

例如功能上类似：

> “图 8 给出了不同起爆延迟下有效遮蔽时长随投放时刻的变化关系。”

但规则不要求固定写“图 X 给出了……”。

避免两种问题：

- 只写“结果如图 8 所示”，看不出图为何出现；
- 把完整题注重新抄进正文。

## 5.4 数据特征只选择与当前答案有关的内容

不逐点、逐线、逐柱描述。

优先选择：

- 单调趋势；
- 极值；
- 拐点；
- 平台区；
- 阈值；
- 交叉点；
- 明显分组差异；
- 不确定区间变化；
- 异常/边界失效。

若图中有很多现象，只保留**真正推动当前问题答案**的 1–3 个特征。

## 5.5 特征必须回到当前设问

图分析不能停在：

> “曲线先上升后下降。”

而要说明这意味着：

- 搜索域如何缩小；
- 最优参数落在哪个区间；
- 哪个策略更优；
- 某阈值是否满足；
- 某变量是否敏感；
- 主结论是否稳定；
- 后续模型应该使用哪个参数/候选方案。

## 5.6 形成原因必须来自模型或数据结构

原因优先来自：

- 目标函数结构；
- 约束激活；
- 几何/物理机制；
- 状态转移；
- 概率/统计关系；
- 资源竞争；
- 边际收益递减；
- 数据分布；
- 模型已证明/已验证的结构。

禁止空泛原因：

- “说明模型合理”；
- “符合实际情况”；
- “算法具有较好性能”；
- “由于因素共同作用”。

## 5.7 必要时一句收束

当该图是当前阶段的关键证据时，分析末尾用一句极简结论将其返回：

- 当前问题直接答案；
- 下一步搜索域；
- 下一问输入；
- 当前 claim 的支持/修改/否决。

若前文已经自然完成该作用，不强制额外总结句。

## 5.8 图与数值排版的叙事位置

拟在 `latex.md` 明确：

```text
引出当前结果关系
→ 图/表（尽量靠近首次分析处）
→ 邻接分析
→ 必要关键数值/局部结果表
→ 下一求解步骤或小问答案
```

避免：

- 连续堆 4–5 张图后才分析；
- 先长篇分析后图隔两页出现；
- 图题承担全部解释，正文不引用；
- 同一关键数字在正文、表格、图注连续重复三遍。

这里不改变 LaTeX 浮动体技术规则，只规定正文证据的逻辑邻近性。

---

# 6. 三项能力如何组合成完整正文写作链

本轮最终希望形成一个统一但不模板化的写作判断链：

```text
符号说明结束
↓
先恢复真实求解依赖与跨问依赖
↓
确定正文主线与共享基础位置
↓
对每个技术块判断是否必要
↓
对必要内容判断详写/略写级别
↓
按当前数学任务连续建立模型
↓
由模型结构自然进入求解
↓
结果出现后就近解释
↓
图像证据按“关系—特征—数值—设问—原因—收束”组织
↓
当前小问直接回答
↓
仅把后问真正需要的输出传递下去
↓
全文 Main-Body Narrative Closure Review
```

这条链的核心不是“所有论文都长这样”，而是：

> **论文阅读顺序应尽可能恢复作者真实解决问题的思维顺序。**

---

# 7. `latex.md` 的拟修改范围

本轮预计只在现有结构中增加或强化以下位置，不重写整份文件。

## 7.1 在“终稿总体结构”后增加宏观正文排序说明

说明默认章节骨架只是可用结构，不凌驾于实际求解依赖。

明确：

> 符号说明之后的正文顺序应由共享基础、数学依赖、小问输入输出和证据链共同决定。

## 7.2 在模型推导/章节组织部分增加 Main-Body Architecture 落地

增加：

- 前置依赖必须先说明；
- 后续章节消费前问结果时应指出具体输出；
- 独立问题不伪造继承；
- 共享基础按复用强度决定是否独立。

## 7.3 在 Paragraph Necessity 后补 Detail Allocation

不另设庞大一级章节，避免模块膨胀。

重点写：

- 决定结构/答案的内容详写；
- 普通代数/百科/重复定义压缩；
- 详略来自下游作用而不是篇幅美感。

## 7.4 在“求解结果：局部证据闭环”中扩展 Figure Result Narrative

补充：

- 图身份句；
- 关键特征选择；
- 当前设问链接；
- 模型原因；
- 必要收束。

## 7.5 在终审前增加 Main-Body Narrative Closure

不新增独立正式论文章节，而是写作/终审动作。

---

# 8. `ai_cleanup.md` 的拟修改范围

AI Cleanup 只增加表现风险，不重新定义 Authority。

拟新增 review risks：

```text
solution_order_mismatch
prerequisite_after_use
orphan_technical_block
main_body_template_order_overrides_dependency
critical_derivation_overcompressed
routine_detail_overexpanded
figure_without_identity
figure_feature_without_question_link
figure_reason_without_model_basis
decisive_figure_without_local_closure
```

并明确机器限制：

- 不凭章节号判断顺序错误；
- 不凭段落长度判断详略错误；
- 不凭图后距离判断解释是否缺失；
- 不凭“因此/由图可知”等词判断叙事质量；
- 不自动重排章节；
- 不自动删除长推导；
- 不改变数学事实。

---

# 9. 测试设计

计划新增：

`tests/test_v719_main_body_writing_closure.py`

## 9.1 Authority 单一性

断言：

- 新规则仍位于 `writing_reasoning_contract.yaml`；
- 不出现新的平行 writing contract；
- latex / cleanup 只消费，不复制第二套 Authority。

## 9.2 Main-Body Architecture

断言：

- 存在 `post_notation_main_body_architecture`；
- ordering basis 包含 mathematical dependency / actual solution sequence / cross-question input-output / evidence-before-claim；
- 明确 independent questions 不虚构 dependency；
- 没有固定章节数量或固定章节名。

## 9.3 Detail Allocation

断言：

- expand_when 包含 structural change / decisive boundary / solver fit / headline result；
- compress_when 包含 routine algebra / repeated symbol / standard algorithm history / inherited unchanged relation；
- 规则与 Paragraph Necessity 明确分工；
- 不使用 paragraph length 作为机器硬判据。

## 9.4 Figure Narrative

断言：

`curve_or_figure` 至少包含：

- identity/relation；
- key feature；
- decisive value when needed；
- implication for current question；
- mechanism/model reason；
- concise closure when decisive。

并断言：

- 不固定六句话；
- 不要求每张图都完整重复同一流程。

## 9.5 No Architecture Creep

断言以下文件不出现新字段/新 Gate：

- task taxonomy；
- numerical verification；
- model approval；
- workbook schema；
- project state；
- workflow router；
- Module 02。

## 9.6 Anti-template

断言：

- 不新增固定连接词词库；
- 不强制“XX 的 XX”；
- 不强制“图 X 给出了”；
- 不强制固定章节“共享基础模型”；
- 不把任何单个算法、题型或参考论文作为默认顺序。

---

# 10. 人工 Prose Smoke 计划

机器测试只能确认规则存在与架构没有越界，无法证明文章真正“顺”。因此本轮必须做人工写作 smoke。

## Smoke A：机理/几何多问题

检查：

- 共享运动关系是否放在真正被消费的位置；
- 判据 → 边界 → 时长 → 优化是否顺序自然；
- 图是否从轨迹/判据特征自然导向答案。

## Smoke B：连续优化题

检查：

- 决策变量、目标、约束是否在同一建立链内；
- 关键降维详写，普通代数压缩；
- 目标函数形态 → solver 选择是否自然；
- 最优参数图是否就近解释。

## Smoke C：统计/回归题

检查：

- 数据处理、变量关系、模型估计、诊断与预测顺序是否与实际分析过程一致；
- 不把优化类顺序强套进统计题；
- 残差图/系数图是否围绕当前统计问题解释。

## Smoke D：时间序列/预测题

检查：

- 趋势/季节性识别是否在模型选择前；
- 训练/验证顺序与证据一致；
- 预测图说明“预测关系—误差—结论”，不只描述曲线。

## Smoke E：网络/调度或组合题

检查：

- 网络基础结构、组合约束、分解、候选域、求解顺序是否一致；
- 复杂 solver 之前是否先解释结构；
- 结果图是否返回资源/路径/调度决策。

## Smoke F：简单解析题

检查：

- Detail Allocation 不会把简单题强行写长；
- 不强制设置模型求解、算法流程或单独结果分析；
- 一两个关键公式即可完成闭环时允许 inline。

## Smoke G：多问递进题

检查：

- 问题一结果是否具体传递到问题二；
- 问题二新增内容详写、继承内容压缩；
- 问题三若依赖失效，是否明确指出而不是“同理”。

## Smoke H：图表密集题

检查：

- 图不会连续堆积后统一分析；
- 每张关键图有身份和问题角色；
- 只分析决定结论的特征；
- 图分析结尾能自然进入下一步或答案。

---

# 11. 验收标准

只有全部满足才进入版本发布。

## 11.1 内容验收

- [ ] 符号说明之后的正文顺序明确服从实际求解依赖，而不是只给固定骨架；
- [ ] 多问输入输出依赖可以被评委恢复；
- [ ] 独立小问不会被强行串联；
- [ ] “详略得当”已有明确 expand/compress 规则；
- [ ] 核心推导不会因追求简洁被过度压缩；
- [ ] 标准算法百科、普通代数和重复定义可被系统压缩；
- [ ] 图像结果有 identity / feature / value / question implication / reason / optional closure；
- [ ] 图分析不是固定句式；
- [ ] 全文存在 main-body closure review；
- [ ] 所有规则均保持 Default/Review 性质，不改变数学模型事实。

## 11.2 兼容验收

- [ ] Model Approval 无变化；
- [ ] 03A/03B 无变化；
- [ ] Numerical Verification/PQS 无变化；
- [ ] Workbook Schema 无变化；
- [ ] Project State Schema 无变化；
- [ ] Task Taxonomy 无变化；
- [ ] workflow runtime 无新 Gate；
- [ ] 旧项目无需迁移。

## 11.3 测试验收

- [ ] v7.19 regression 全绿；
- [ ] 全量 Python tests 全绿；
- [ ] Static contract lint 全绿；
- [ ] Generated file contract 全绿；
- [ ] 人工 prose smoke A–H 通过；
- [ ] LaTeX CUMCM 全绿；
- [ ] LaTeX MCM-ICM 全绿；
- [ ] LaTeX Diangong 全绿；
- [ ] Production LaTeX attestation 全绿；
- [ ] merge 后 main CI 再次全绿。

---

# 12. 实施阶段

## Phase 0 — 用户审查本计划

当前阶段只创建本计划，不修改正式 Skill 语义。

用户审查重点：

- 三个能力方向是否准确；
- Detail Allocation 是否符合“详略得当”的预期；
- Figure Result Narrative 是否过度模板化；
- Main-Body Architecture 是否真正体现求解顺序；
- 是否存在不希望加入 Skill 的要求。

未经批准，不进入 Phase 1。

## Phase 1 — Writing Authority

修改：

`core/writing_reasoning_contract.yaml`

预计：

- schema `1.4.0 -> 1.5.0`（仅 writing contract 自身语义版本）；
- 扩展 `model_establishment_solution_narrative`；
- 加入三项能力与 machine audit boundary；
- 不新增 runtime/schema gate。

## Phase 2 — LaTeX 正文落地

修改：

`modules/05_writing/latex.md`

将 Authority 转为自然语言执行规则，重点处理：

- 符号说明后的宏观排序；
- 详略判断；
- 图结果段；
- 全文 main-body closure review。

## Phase 3 — AI Cleanup 消费

修改：

`modules/05_writing/ai_cleanup.md`

只加入表现风险与复查方式，不重复 Authority。

## Phase 4 — Regression

新增：

`tests/test_v719_main_body_writing_closure.py`

并仅在旧测试与新合法语义冲突时进行最小兼容修正。

## Phase 5 — 人工 prose smoke

执行 A–H 八类写作样例。

若出现：

- 过度模板化；
- 简单题被强行写长；
- 图分析机械六句式；
- 章节顺序被过度强制；

则优先修改 Authority，不用测试例外掩盖。

## Phase 6 — 入口摘要

若规则足够稳定，再在 `PROJECT_INSTRUCTIONS.md` / `SKILL.md` 等入口文件做轻量摘要。

入口只写能力存在，不复制完整规则。

## Phase 7 — Release Candidate

若 Phase 1–6 全通过：

- 暂定升级 Skill `7.18.0 -> 7.19.0`；
- 更新 CHANGELOG / README / version carriers；
- 根 SKILL 与 packaged SKILL 保持一致；
- 归档本实施计划到 `legacy/architecture/`；
- generated metadata 仅由 generator 刷新。

## Phase 8 — Full CI / PR Acceptance

要求完整 HSK Skill CI 11 项全绿。

## Phase 9 — Squash Merge / Main Verification

- squash merge；
- 回读 main bootstrap 与 SKILL；
- 验证版本；
- 等待 merge 后 main CI 全绿；
- 确认 generated metadata 没有漂移。

---

# 13. 风险与防护

## 风险 A：把“按求解顺序写”误解为“代码执行日志顺序”

防护：正文服从**数学依赖与论证顺序**，不是 Python print 顺序、调参顺序或实验时间线。

## 风险 B：详略规则导致长文膨胀

防护：Detail Allocation 必须与 Paragraph Necessity 联用；只有决定结构/答案的内容才展开。

## 风险 C：图分析变成新的固定六句模板

防护：规则明确 functional checklist，不规定句数、不规定词语；功能可合并，可省略不适用项。

## 风险 D：为了“原因分析”强行编造机制

防护：原因必须能回到已批准模型、约束、数据规律或验证证据；无法支持时只陈述观察，不杜撰原因。

## 风险 E：Main-Body Architecture 过度约束不同题型

防护：仅规定 dependency-first，不规定具体章节名；统计、预测、网络、机理、优化各自保持题型自然顺序。

## 风险 F：新增规则侵入模型/数值 Authority

防护：回归锁定 protected files 不出现新 writing gate/field。

---

# 14. 预期修改后的写作效果

本轮完成后，符号说明之后的正文应更接近以下阅读体验：

```text
为什么先处理这一对象
→ 这一关系为后面解决什么问题
→ 当前关键推导展开到足够深度
→ 普通步骤适度压缩
→ 最终模型自然进入数值求解
→ 图/表一出现就知道它展示什么
→ 只分析真正决定答案的特征
→ 用模型结构解释趋势
→ 返回当前设问
→ 将必要输出交给下一问
```

评委阅读时应该能够清楚恢复：

1. 作者实际是怎样一步一步解决问题的；
2. 哪些步骤是关键数学贡献，哪些只是常规计算；
3. 每张核心图为什么出现、说明了什么；
4. 前后小问之间到底传递了什么；
5. 最终答案怎样由前述模型、求解与证据逐步推出。

---

# 15. 本轮明确不会做的“伪优化”

以下内容即使看起来能让规则更“完整”，本轮也不加入：

- “每个问题必须 4 个二级标题”；
- “每个图必须写 5 句分析”；
- “图后必须有综上所述”；
- “模型建立必须先变量再公式再算法”；
- “所有标题必须名词+动词”；
- “所有论文必须有共享基础模型”；
- “结果分析必须统一放每问最后”；
- “所有关键推导必须完整证明”；
- “所有标准算法必须介绍原理”；
- “为了论文连贯，所有小问都必须存在继承关系”。

---

# 16. 用户审查清单

在批准实施前，请重点审查以下 8 项：

1. **正文顺序**：是否同意“符号说明后优先服从真实数学依赖和实际求解顺序”？
2. **共享基础**：是否同意仅在多个问题真实共享且能减少重复时单列？
3. **详写范围**：是否同意关键机理、判据、降维、边界、solver 依据、决定性结果应详写？
4. **略写范围**：是否同意普通代数、重复符号、算法百科、继承未变化部分、逐点读图应压缩？
5. **图结果链**：是否同意“图身份/关系 → 关键特征 → 决定性数值 → 设问含义 → 原因 → 必要收束”？
6. **反模板**：是否同意上述仅是功能链，不固定句数和词语？
7. **宏观闭环**：是否同意终稿增加一次 main-body narrative closure review？
8. **版本策略**：若正式实现通过，是否同意作为向后兼容的新写作能力升级到 `v7.19.0`？

---

# 17. 后续聊天 / Agent 上下文恢复说明

若后续聊天上下文丢失，实施前必须重新读取：

1. 当前 `main` 的 `core/bootstrap.yaml`；
2. `SKILL_CHANGE_GOVERNANCE.md`；
3. 本计划文件；
4. 当前 `core/writing_reasoning_contract.yaml`；
5. 当前 `modules/05_writing/latex.md`；
6. 当前 `modules/05_writing/ai_cleanup.md`；
7. 当前分支/PR 与 main 差异。

恢复后必须牢记本轮核心目标：

> **这次不是修模型数学正确性，而是让符号说明之后的整篇正文更忠实地恢复真实求解顺序；让技术内容详略得当；让结果图从“图是什么”到“为什么这样、对问题意味着什么”形成精炼、专业、邻接的论证闭环。**

未经用户批准，不得从 PLANNING ONLY 进入正式 Skill 语义修改。
