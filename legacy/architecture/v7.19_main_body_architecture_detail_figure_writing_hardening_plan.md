# v7.19.0 Intra-Question Writing Closure 详细修改计划

> 状态：**PLANNING ONLY / 待用户审查**  
> 当前正式基线：HSK Skill `v7.18.0`  
> 基线 `main`：`3209f884cc965791ae32b183bf5b37c7be38e075`  
> 计划分支：`upgrade/v7.19.0-main-body-writing-closure`  
> 暂定目标版本：`v7.19.0`（仅在用户批准、正式实现、人工 prose smoke、完整 CI 全部通过后升级）  
> 修改主题：**在既定论文大框架不变的前提下，规范各大章节内部的小节求解顺序、详略分配与图结果叙事**

---

# 0. 修改简报

```text
修改主题：Intra-Question Writing Closure
当前版本：7.18.0
目标版本：暂定 7.19.0
变更等级：minor（新增向后兼容的论文写作能力，不改变模型/数值/runtime 接口）

直接目标：
1. 冻结现有论文大章节骨架，不允许本轮规则重新排序、替换或破坏既定框架；
2. 只在“数据说明/必要数据预处理”“共享基础模型/模型准备”“问题X模型建立及求解”等大章节内部，
   依据真实局部求解依赖规范二级/三级小节的顺序与粒度；
3. 建立 Detail Allocation Governance，明确关键推导、求解依据、结果解释应详写，
   普通代数、重复定义、标准算法百科、未变化继承内容应压缩；
4. 完善 Figure Result Narrative，使图片结果形成“图的身份/关系—关键特征—必要数值—设问含义—原因—必要收束”的局部证据闭环；
5. 增加 Question-Section Narrative Closure Review，检查每个“问题X模型建立及求解”内部是否真正按求解过程推进并回答该问。

明确不做：
- 不改变现有大章节骨架；
- 不调整“符号说明 → 数据说明/必要数据预处理 → 共享基础模型/模型准备 → 问题一 → 问题二 → ……”的顺序；
- 不按求解依赖重排问题一、问题二、问题三等大章节；
- 不把后问提前到前问之前；
- 不把问题专属内容移动成新的一级大章节；
- 不修改模型数学语义、Human Model Approval、03A/03B；
- 不修改 Numerical Verification/PQS、Workbook Schema、Project State Schema、Task Taxonomy；
- 不改变 Python/MATLAB 职责；
- 不新增 runtime Gate、固定小节数量、固定句式、连接词词库或图分析“六句话模板”；
- 不把任何单篇优秀论文的章节顺序、句子或算法固化为 runtime 模板；
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
- tests/test_v719_intra_question_writing_closure.py
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
- 旧论文若已有合理的小节顺序，不因未显式登记新内部结构而 stale；
- 不引入新的必填 Schema 字段或 CLI 参数；
- 现有中文国赛大章节结构保持原样。

迁移要求：无 Schema/CLI/目录迁移。

验收测试：
- static contract lint；
- 全量 unittest；
- generated-file contract；
- v7.19 writing regression；
- 八类人工 prose smoke；
- 大框架不变 regression；
- 三套 LaTeX + Production LaTeX attestation；
- merge 后 main CI 全绿。

回滚方式：
- 若新写作规则造成小节模板化、正文膨胀或图表分析机械化，回滚本次 writing authority/consumer/test 变更即可；
- 因无 Schema/CLI/模型语义变化，不需要项目数据迁移或兼容脚本。
```

---

# 1. 本轮最重要的边界修正：冻结论文大章节骨架

本轮正式确认：**v7.19 不再讨论“符号说明之后的大章节宏观重排”。**

当前中文国赛论文的大框架已经在 v7.18 中确定，本轮不得以“求解依赖”“阅读顺序”或“宏观闭环”为理由破坏它。

符号说明之后的默认大章节顺序继续保持：

```text
符号说明
→ 数据说明 / 必要数据预处理（按既有 preprocessing_decision 决定是否启用）
→ 共享基础模型 / 模型准备（按既有 shared_foundation 规则决定是否启用）
→ 问题一模型建立及求解
→ 问题二模型建立及求解
→ 问题三模型建立及求解
→ ……
→ 模型的评价与推广
→ 参考文献
→ 附录
```

本轮新增规则必须满足以下四条硬边界：

1. **不重排大章节。** 问题一、问题二、问题三仍按题目顺序写；真实求解中即便做过交叉计算，也不能据此打乱论文大章节顺序。
2. **不改变可选章节的既有激活逻辑。** “数据说明/必要数据预处理”和“共享基础模型/模型准备”是否出现，仍由现有 Authority 决定；本轮只规范它们一旦出现后，内部小节怎样组织。
3. **不新造大章节。** 本轮新增的 Architecture、Detail Allocation、Figure Narrative 都是写作治理规则，不成为论文中的一级章节名称。
4. **不把局部求解顺序升级为全文排序权。** “符合求解顺序”只约束当前大章节内部的小节、段落、公式、算法和结果出现顺序。

因此，本计划原来的 **Post-Notation Main-Body Architecture** 不再作为正式能力名称。正式实现拟改为：

> **Within-Question Subsection Architecture / 问题章节内部小节架构**

它的作用域是：

- `数据说明/必要数据预处理` 大章节内部；
- `共享基础模型/模型准备` 大章节内部；
- 每个 `问题X模型建立及求解` 大章节内部；
- 必要的 `模型检验/敏感性/鲁棒性` 局部子节内部。

它**没有权限**改变这些大章节本身的相对顺序。

---

# 2. 问题重新定义

v7.18.0 已经解决“小问内部模型建立—模型求解—结果解释怎样连续写”的主要语言问题，当前已有：

- Continuous Mathematical Narrative；
- Formula Prose Rhythm；
- Functional Transition Governance；
- Professional Heading Semantics；
- Model-to-Solver Bridge；
- Result-adjacent Interpretation；
- Cross-question incremental writing；
- Paragraph Necessity；
- Subsection Granularity。

本轮不是推翻 v7.18，而是补齐三个**大章节内部**仍不够实质化的写作问题。

## 2.1 缺口一：问题章节内部的小节顺序仍缺少“局部求解依赖”规范

现有规则能够保证公式前后连续，也能保证模型自然进入 solver，但一个复杂问题内部仍可能出现：

- 先写优化模型，后补其依赖的判据；
- 先给结果图，后解释结果所依赖的计算量；
- 把“变量、目标函数、约束、算法、结果”按论文组件机械拆节，而不是按真正求解任务拆节；
- 同一问题的局部求解链被打散到多个互不承接的小节；
- 一个本应先完成的降维/边界定位被放到 solver 之后；
- 结果分析与当前模型步骤距离过远。

本轮要解决的是：

> **在“问题X模型建立及求解”这个大章节已经固定的前提下，其内部二级/三级小节怎样按真实数学任务和局部求解顺序组织。**

## 2.2 缺口二：已有“删冗余”，但缺“详写/略写”的明确分配标准

Paragraph Necessity 可以判断一段是否有必要，Subsection Granularity 可以判断是否过碎，但不能完整回答：

> **必要内容到底应该写到什么深度。**

当前仍可能出现两种相反问题：

- 决定模型结构的推导写得过短，评委无法恢复思路；
- 普通代数、重复符号、标准算法原理写得过长，真正重要的机制和结果反而被淹没。

本轮拟新增 **Detail Allocation Governance**。

## 2.3 缺口三：图结果已有趋势—原因—结论，但图的入口与收束仍可更专业

v7.18 已要求图表就近解释，但仍可进一步明确：

- 图第一次进入正文时，应用一句简洁语言说明它展示了什么关系，而不是只写“如图 X 所示”；
- 分析只抓决定结论的特征，不逐点读图；
- 特征要回到当前问题所求，而不是停留在视觉描述；
- 关键数值应放在最能支撑判断的位置；
- 原因解释只能来自模型结构、约束、机制或数据规律；
- 若该图是本问关键证据，应有一句简短收束，把图的证据返回到当前答案或下一步求解。

本轮拟把这一逻辑固化为 **Figure Result Narrative**。

---

# 3. 总体设计原则

## 3.1 大框架冻结，小节内部自适应

本轮的核心边界写成一句话：

> **大章节结构服从现有论文框架；大章节内部的小节顺序服从当前问题的真实数学任务与求解依赖。**

不得把这两层混淆。

## 3.2 单一 Authority，不新增第二套写作系统

所有新增跨题型规则仍放在：

`core/writing_reasoning_contract.yaml`

优先扩展现有：

`model_establishment_solution_narrative`

不新增：

- `main_body_writing_contract.yaml`；
- `figure_narrative_contract.yaml`；
- `detail_allocation_contract.yaml`；
- 新 Module；
- 新 runtime Gate。

`latex.md` 只把 Authority 落到论文正文；`ai_cleanup.md` 只检查表现层风险，不复制第二套规范。

## 3.3 逻辑功能优先，不建立固定模板

所有新增规则表达的是“信息功能与依赖”，不能变成：

- 每问固定 4 个小节；
- 每个模型固定先变量、再目标、再约束、再算法；
- 每张图固定 6 句话；
- 每个三级标题固定“XX 的 XX”；
- 每段固定出现“因此/进一步/由此”；
- 每个小问固定一张流程图。

## 3.4 求解事实优先于文字流畅

小节顺序优化不得：

- 改写已批准模型；
- 把结果倒灌成前提；
- 删除边界和异常；
- 隐去求解失败或限制；
- 把数值现象写成理论证明；
- 因追求短句而省略决定性推导。

---

# 4. 新增能力一：Within-Question Subsection Architecture

## 4.1 作用域

该能力只管理**固定大章节内部**的局部结构。

优先作用于：

```text
问题X模型建立及求解
├─ 模型建立相关小节
├─ 模型求解相关小节
├─ 结果分析相关小节
└─ 模型检验/敏感性/鲁棒性（确有需要时）
```

也可用于：

- 数据说明/必要数据预处理内部的小节顺序；
- 共享基础模型/模型准备内部的公共对象与关系顺序。

但它不管理这些大章节相互之间的顺序。

## 4.2 局部排序的第一原则：真实数学依赖

在同一大章节内，如果局部任务 B 依赖局部任务 A，则默认先写 A 再写 B。

例如机理/几何问题内部可能是：

```text
运动状态的确定
→ 几何判据的构造
→ 临界时刻的定位
→ 有效时长的计算
→ 优化目标的形成
→ 参数的数值求解
→ 最优方案的解释
```

这不是机理题固定模板，而只是说明：**局部小节顺序应能恢复真实数学依赖。**

统计问题可能是：

```text
变量关系的构造
→ 参数估计
→ 显著性/残差诊断
→ 结果解释
```

预测问题可能是：

```text
序列结构识别
→ 模型方程建立
→ 参数估计
→ 滚动预测
→ 误差分析
```

不同题型允许完全不同的小节顺序，只要顺序对应当前问题的真实求解过程。

## 4.3 局部排序的第二原则：模型先闭合，solver 后出现

在一个问题大章节内部：

- solver 不应早于其所消费的核心模型结构；
- 结果不应早于其计算依据；
- 验证不应早于被验证的主结果；
- 关键边界、判据或候选域若决定 solver，应在 solver 前交代。

继续消费 v7.18 的 `model_to_solver_bridge`，本轮不重复定义第二套算法顺序。

## 4.4 局部排序的第三原则：按数学任务分小节，不按合同字段分小节

优先标题：

```text
有效遮蔽判据的构造
临界边界时刻的求解
投放参数的联合优化
预测误差的滚动检验
资源配置结果的可行性验证
```

避免机械拆成：

```text
决策变量
目标函数
约束条件
算法设计
结果说明
```

如果“决策变量—目标—约束”共同完成同一个优化模型任务，应在同一小节连续展开。

## 4.5 二级/三级标题的层级判断

拟新增如下判断：

### 二级小节适合承载

- 一个独立模型任务；
- 一个独立求解阶段；
- 一个独立结果/验证证据组；
- 若不拆开会使较长论证难以恢复的数学阶段。

### 三级标题只在以下情况启用

- 一个二级小节内部存在两个以上真正独立的数学任务；
- 独立命题/关键算法/关键图需要清晰锚点；
- 不分三级标题会造成长推导难以定位。

### 不足以单独成标题的内容

- 单一公式；
- 一个参数值；
- 一张普通图；
- 一张普通表；
- 一个符号定义；
- 标准算法的一条参数设置；
- 一句“模型汇总”。

## 4.6 “符合求解顺序”不是“照抄 Python 执行日志”

必须明确：论文内部的求解顺序指**数学认知顺序**，不是程序运行顺序。

例如程序可能：

```text
读取数据 → 构造缓存 → 并行搜索 → 保存 Excel
```

论文不能据此设置：

```text
缓存构造
并行计算
文件保存
```

正确的论文顺序应恢复：

```text
数学对象 → 计算目标 → 可利用结构 → 求解方法 → 数值结果
```

## 4.7 多问递进只影响“承接内容”，不改变大章节顺序

问题二真实依赖问题一时，只在问题二开头用短句恢复：

- 继承的模型/参数/阈值；
- 本问新增条件；
- 本问新增数学任务。

不得因为问题二使用问题一结果，就把问题二的某些大段提前到问题一章节。

如果问题之间独立，不虚构递进。

## 4.8 数据说明/必要数据预处理章节内部

该大章节一旦由既有规则激活，本轮只规范其内部顺序：

```text
当前模型真正需要的数据对象/字段
→ 必要的数据质量处理
→ 必要变换或构造量
→ 对后续模型产生的直接输入
```

不写与后续模型无关的数据分析，不因“完整”而加入装饰性 EDA。

## 4.9 共享基础模型/模型准备章节内部

该大章节一旦由既有 `shared_foundation` 规则激活，内部优先：

```text
共享对象/坐标/索引
→ 共享定义
→ 共享核心关系
→ 后续各问实际消费的公共输出
```

不得塞入问题一专属最优值、问题二专属约束或后问 solver。

## 4.10 拟新增 Authority 结构

```yaml
within_question_subsection_architecture:
  governance_level: default
  scope_boundary:
    preserves_top_level_paper_skeleton: true
    may_reorder_top_level_sections: false
    may_reorder_question_sections: false
    applies_inside:
      - data_or_preprocessing_section_when_active
      - shared_foundation_section_when_active
      - question_model_establishment_solution_section
      - local_validation_section_when_active
  ordering_basis:
    - local_mathematical_dependency
    - local_solution_reasoning_sequence
    - model_before_solver
    - evidence_before_local_conclusion
  heading_basis:
    - independent_mathematical_task
    - independent_solution_stage
    - independent_result_or_validation_role
  rules:
    - do_not_follow_python_execution_log_as_paper_structure
    - do_not_split_by_contract_fields_when_one_argument_chain
    - do_not_move_question_specific_content_across_top_level_question_sections
    - cross_question_dependency_changes_inheritance_prose_not_top_level_order
```

名称和字段可在正式实现时微调，但语义边界不得改变。

---

# 5. 新增能力二：Detail Allocation Governance

## 5.1 目标

把“详略得当”从模糊要求转成一个可执行的判断：

> **篇幅优先分配给决定模型成立、决定求解方法、决定结果可信和决定最终答案的内容。**

不是平均分配篇幅，也不是所有公式都同等解释。

## 5.2 详写级别：Decisive / 关键决定性内容

满足下列任一条件时应优先展开：

- 决定核心模型结构；
- 决定关键判据是否成立；
- 决定可行域、边界或约束；
- 完成非显然降维、等价转化或分解；
- 解释为什么当前 solver 适配；
- 决定最终答案或关键策略；
- 决定结果为何可信；
- 存在容易被评委质疑的非显然步骤。

正文通常需要让评委恢复：

```text
为什么需要
→ 依据是什么
→ 怎么得到
→ 得到后改变什么
```

## 5.3 正常级别：Supporting / 必要支撑内容

包括：

- 主变量首次定义；
- 必要参数来源；
- 一般约束说明；
- 求解器本题化编码；
- 终止条件；
- 必要精度说明；
- 关键图表的基本解释。

要求信息完整，但不做无必要长推导。

## 5.4 压缩级别：Routine / 常规可压缩内容

默认压缩：

- 纯代数展开；
- 教科书级标准公式的重复证明；
- 已在符号说明定义过的符号逐项翻译；
- 未变化的前问共享关系；
- 标准算法历史与通用优点；
- 简单单位换算；
- 与当前答案无关的中间变量；
- 图表中非决定性的普通点值。

压缩不是删除。若这些内容是理解核心关系的必要桥梁，仍保留最短有效表述。

## 5.5 附录/省略级别：Implementation / 非正文信息

优先移附录或不进入正文：

- 完整 Python/MATLAB 代码；
- 文件路径；
- DataFrame 操作；
- 调试日志；
- 全部参数扫描记录；
- 全部候选解明细；
- 无独立证据作用的重复图；
- 软件安装或运行环境细节（除非影响复现/性能结论）。

## 5.6 公式详略规则

### 核心公式

必须保留必要来源、关键推导和下游作用。

### 中间公式

若仅用于代数传递，可合并或压缩。

### 最终模型

必须让评委恢复求解器真正消费的目标、关系、约束或状态方程。

### 已知标准关系

只说明本题为什么适用和怎样进入当前模型，不写教科书式长介绍。

## 5.7 Solver 详略规则

详写：

- 当前模型为何需要该 solver；
- 变量/状态怎样编码；
- 目标怎样评价；
- 约束怎样处理；
- 关键参数、初值、精度与停止条件；
- solver 输出怎样映射回模型变量。

略写：

- 算法历史；
- 通用优点；
- 与本题无关的标准更新公式；
- 没有修改过的标准算子细节。

## 5.8 结果详略规则

详写：

- 决定答案的数值；
- 决定策略的趋势/阈值/拐点；
- 关键约束的活跃状态；
- 结果形成的机制；
- 结果对设问的直接含义；
- 关键验证是否改变结论。

略写：

- 表格逐格复述；
- 曲线逐点复述；
- 与答案无关的辅助指标；
- 已经在图表中清楚展示且没有额外解释价值的数字。

## 5.9 “详写”不等于“写长”

本轮必须明确：

> 详写的标准是**信息链完整**，不是字数多。

一个关键推导可能只需要 3 句 + 1 个公式，也可能需要命题 + 证明。不能设置统一字数、句数或公式数。

## 5.10 简单问题防膨胀

如果一个问题只有一个直接解析关系或简单计算：

- 不强制设置多个小节；
- 不强制算法段；
- 不强制模型汇总；
- 不强制图表；
- 不因为 Detail Allocation 增加本来不存在的复杂性。

## 5.11 拟新增 Authority 结构

```yaml
detail_allocation_governance:
  governance_level: default
  principle: allocate_detail_by_decisiveness_not_uniformity
  expand_when_any:
    - determines_model_structure
    - determines_predicate_or_boundary
    - nontrivial_reduction_or_transformation
    - determines_solver_fit
    - determines_answer
    - determines_validation_claim
    - likely_reviewer_challenge
  compress_when_any:
    - routine_algebra
    - repeated_symbol_translation
    - unchanged_inherited_relation
    - generic_algorithm_background
    - nondecisive_intermediate_value
    - table_or_curve_repetition
  move_to_appendix_when_any:
    - implementation_detail
    - exhaustive_candidate_log
    - full_code
    - nonessential_parameter_sweep
  no_word_count_rule: true
  simple_problem_anti_bloat: true
```

---

# 6. 新增能力三：Figure Result Narrative

## 6.1 目标

使结果图的正文分析既完整又简洁，能够自然完成：

> **告诉评委这是什么关系 → 看出什么关键特征 → 关键数值是什么 → 这对当前问题意味着什么 → 为什么会这样 → 必要时一句收束。**

这是功能链，不是固定六句话。

## 6.2 Figure Identity / 图的身份说明

图第一次进入当前结果段时，邻近正文应让评委知道：

- 图展示哪些变量/对象之间的关系；
- 这张图为什么出现在当前问题这里。

例如功能上应达到：

> “图 X 展示参数 A 变化时指标 B 的响应关系，用于确定本问的可行参数区间。”

但不固定使用“图 X 展示……”这一句式。

不得只写：

> “结果如图 X 所示。”

也不重复完整图题。

## 6.3 Characterize / 关键特征识别

只提与当前答案有关的特征，例如：

- 单调趋势；
- 峰值/谷值；
- 拐点；
- 稳定区间；
- 临界区间；
- 分组差异；
- 收敛区间；
- 异常/反转。

不逐点读图，不把全部视觉变化都写进正文。

## 6.4 Quantify / 必要数值定位

只有决定判断的数值才进入正文：

- 阈值；
- 极值；
- 最优点；
- 关键区间；
- 误差；
- 相对变化量；
- 关键时间/坐标。

精度继续服从 Numeric Profile，不因正文简洁擅自降位。

## 6.5 Answer Link / 回到当前设问

图分析不能停在“曲线先升后降”。必须说明：

- 这一特征如何缩小参数范围；
- 如何选择策略；
- 如何判断是否满足要求；
- 如何支持当前小问的最终答案；
- 或如何为下一局部求解步骤提供依据。

这一步是图结果叙事的核心。

## 6.6 Cause / 简洁解释形成原因

原因优先来自：

- 当前模型方程；
- 约束变活跃/失活；
- 物理/几何机制；
- 统计结构；
- 资源竞争；
- 边界效应；
- 数据本身的已证实规律。

禁止为了“有分析”编造没有模型证据支持的原因。

如果无法从现有模型/证据解释原因，则只描述可确认现象和问题含义，不强行补机制。

## 6.7 Closure / 必要时简短收束

当该图承担当前局部任务的关键证据时，可以用一句很短的话收回：

- 当前结论；
- 最终参数区间；
- 当前问题答案；
- 下一步求解输入。

如果前一句已经完成 answer link，就不重复总结。

## 6.8 图、数值与正文的位置关系

拟明确：

```text
引出图及其作用
→ 图
→ 紧邻的关键特征/数值/设问含义/原因解释
→ 下一局部任务
```

或在版式需要时：

```text
短引出
→ 关键数值句
→ 图
→ 解释与收束
```

不允许：

```text
图1
图2
图3
表4
……
很后面才统一分析所有结果
```

## 6.9 多面板图

多面板图不要求每个 panel 各写一段。

正文应：

- 先说明整张图的共同问题；
- 再只分析各 panel 对结论有独立贡献的差异；
- 若多个 panel 只重复同一趋势，用一句综合解释即可。

## 6.10 不同图类型的自适应

### 参数响应/敏感性图

关注：趋势、阈值、稳定区间、结论是否改变。

### 优化收敛图

关注：目标变化、稳定位置、是否支持终止/精度，不用它证明全局最优。

### 预测/拟合图

关注：主趋势、关键偏差、异常区间，并与误差指标结合。

### 空间/网络图

关注：结构位置、聚集/连通/路径特征与决策含义，不机械谈“上升下降”。

### 机制/几何结果图

关注：临界状态、相对位置、边界关系和模型判据。

## 6.11 与现有 Result-adjacent Interpretation 的关系

本轮不另建第二套图表 Authority。

拟将 Figure Result Narrative 作为：

`model_establishment_solution_narrative.result_adjacent_interpretation.curve_or_figure`

的细化，或作为同一 Authority 下的 `figure_result_narrative` consumer 结构。

不得与现有 point optimum / algorithm accuracy / validation profile 冲突。

## 6.12 拟新增 Authority 结构

```yaml
figure_result_narrative:
  governance_level: default
  functional_sequence:
    - identify_relation_and_local_role
    - characterize_decisive_feature
    - quantify_decisive_value_when_needed
    - connect_feature_to_current_question
    - explain_supported_reason_when_available
    - close_to_answer_or_next_step_when_needed
  rules:
    - not_caption_repetition
    - not_point_by_point_reading
    - not_fixed_sentence_count
    - not_same_pattern_for_every_figure
    - reason_must_be_supported_by_model_or_evidence
    - interpretation_stays_adjacent_to_figure
  numeric_source: numeric_style_contract
  claim_source: claim_strength_calibration
```

---

# 7. Question-Section Narrative Closure Review

原计划中的 “Main-Body Narrative Closure Review” 范围过大，容易误导为重排全文大章节。

本轮改成：

> **Question-Section Narrative Closure Review / 问题章节内部闭环检查**

对每个 `问题X模型建立及求解` 大章节，在初稿完成后检查：

```text
1. 本问真正需要回答什么？
2. 第一个局部小节是否直接进入解决该问所需的数学对象/关系？
3. 各小节的先后是否符合局部数学依赖？
4. 是否出现“后定义的量被前面先用”的倒置？
5. 模型是否在 solver 之前达到可计算状态？
6. solver 是否由模型结构自然引出？
7. 关键结果是否在邻近位置解释？
8. 图表是否真正服务当前问题而非装饰？
9. 本问决定性推导是否写得足够，普通内容是否压缩？
10. 最终是否在本章节内直接回答该问？
11. 若后问需要本问输出，是否只明确传递必要量而不提前展开后问？
```

这不是新 Gate，而是 Writing Default 的 reviewer checklist。

整篇终审只额外确认一件事：

> **既定大章节骨架是否仍保持原顺序。**

它不重新决定全文章节排序。

---

# 8. `latex.md` 拟修改内容

正式实施时只在现有写作章节中增加/修订以下内容。

## 8.1 在总体结构处增加“冻结边界”说明

明确：

- v7.19 新增规则不改变 3.2 的中文国赛大章节骨架；
- 可选章节是否启用仍按既有规则；
- 新规则仅约束大章节内部小节。

## 8.2 在问题章节内部小节颗粒度处扩展

将当前 `subsection_granularity` 从“防止小节过碎”扩展为：

```text
防碎片化
+
局部求解依赖排序
+
数学任务型标题
+
大章节边界保护
```

## 8.3 在模型建立/模型求解处补 Detail Allocation

不新增独立论文章节，只在写作说明里明确：

- 关键推导详写；
- 普通过程压缩；
- 标准算法只写本题化部分；
- 决定性结果与解释保留足够篇幅。

## 8.4 在结果图表达处补 Figure Result Narrative

把图表结果写法明确为功能链，但不提供固定句式模板。

---

# 9. `ai_cleanup.md` 拟新增检查

AI Cleanup 只做表现层复查，不判断数学正确性。

拟新增 review risks：

- `subsection_order_breaks_local_dependency`
- `top_level_framework_reordered_by_writing_rule`
- `decisive_derivation_overcompressed`
- `routine_content_overexpanded`
- `figure_without_identity_or_local_role`
- `figure_feature_without_question_link`
- `unsupported_figure_cause`
- `detached_figure_summary`

其中：

`top_level_framework_reordered_by_writing_rule`

用于保护本轮最重要的边界：任何新增写作规则不得破坏既定大章节骨架。

机器审计仍不得：

- 从字数判断是否“详略得当”；
- 从公式数判断推导是否完整；
- 从标题语法判断标题是否专业；
- 从“图 X”关键词判断图分析是否合格；
- 从段落距离判断数学逻辑正确；
- 自动重排大章节。

---

# 10. 回归测试设计

拟新增：

`tests/test_v719_intra_question_writing_closure.py`

## 10.1 大框架冻结测试

至少断言：

- `within_question_subsection_architecture.scope_boundary.preserves_top_level_paper_skeleton == true`；
- `may_reorder_top_level_sections == false`；
- `may_reorder_question_sections == false`；
- `latex.md` 仍保留既定中文国赛骨架；
- v7.19 Authority 不出现“按求解依赖重排问题章节”的语义。

## 10.2 小节顺序测试

断言局部排序依据包含：

- local mathematical dependency；
- local solution reasoning sequence；
- model before solver；
- evidence before local conclusion。

## 10.3 详略分配测试

断言：

- 有 expand/compress/appendix 三类判断；
- 不存在固定字数；
- simple_problem_anti_bloat 为真；
- routine algebra 和 algorithm background 明确可压缩。

## 10.4 Figure Narrative 测试

断言功能链包含：

- identity/local role；
- decisive feature；
- key value when needed；
- question link；
- supported reason；
- optional closure。

同时断言：

- not fixed sentence count；
- not caption repetition；
- not point-by-point reading。

## 10.5 Authority 边界测试

继续断言：

- 不新增 runtime Gate；
- 不修改 Module 02；
- 不修改 Numerical Verification/PQS；
- 不修改 Workbook/Project State/Taxonomy；
- 不新增第二套 writing contract 文件。

---

# 11. 人工 prose smoke 设计

正式实现后至少做 8 类人工样例。

## A. 机理/几何题

检查：

- 局部小节是否按“关系依赖”排列；
- 判据/临界边界是否比普通代数写得更充分；
- 结果图是否围绕临界关系解释。

## B. 连续优化题

检查：

- 变量/目标/约束不机械拆成多个小节；
- solver 在模型闭合后出现；
- 最优参数图/曲线能直接回到决策答案。

## C. 统计回归题

检查：

- 不强套机理题小节结构；
- 参数估计、诊断、结果解释顺序自然；
- 诊断图不写成优化结果图。

## D. 时间序列题

检查：

- 序列结构、建模、预测、误差分析在问题章节内部顺序合理；
- 标准模型背景被压缩。

## E. 网络/调度题

检查：

- 网络对象/资源关系先于算法；
- 路径/调度结果图有明确问题含义。

## F. 简单解析题

检查：

- 不被 v7.19 强行拆成 3--4 个小节；
- 不因为“详写”产生无必要算法和图表。

## G. 多问递进题

检查：

- 问题一、二、三大章节顺序完全不变；
- 后问只短承接前问必要输出；
- 不把后问内容提前到前问。

## H. 图表密集题

检查：

- 图不连续裸堆；
- 每张关键图有身份、特征、问题链接；
- 不形成“六句话模板”；
- 多面板图能综合解释。

---

# 12. 正式实施阶段

## Phase 0：计划审查

当前阶段。

完成条件：用户明确批准本修订版计划。

## Phase 1：Authority 实现

修改：

`core/writing_reasoning_contract.yaml`

拟新增/扩展：

- `within_question_subsection_architecture`
- `detail_allocation_governance`
- `figure_result_narrative`
- `question_section_narrative_closure`

并明确 top-level skeleton preservation。

## Phase 2：LaTeX consumer 落地

修改：

`modules/05_writing/latex.md`

只把 Authority 转换成自然正文写作规则，不复制第二套完整合同。

## Phase 3：AI Cleanup

修改：

`modules/05_writing/ai_cleanup.md`

增加局部顺序、详略和图结果表现风险。

## Phase 4：Regression

新增：

`tests/test_v719_intra_question_writing_closure.py`

并检查旧 v7.18 回归继续通过。

## Phase 5：人工 prose smoke

执行第 11 节的 8 类样例。

如果出现下列任一问题，回到 Authority 修改：

- 大章节被重排；
- 简单题被写复杂；
- 图结果变成固定模板；
- 关键推导仍过短；
- 标准算法仍过长；
- 小节顺序与实际局部求解过程不一致。

## Phase 6：入口摘要

必要时轻量修改 `PROJECT_INSTRUCTIONS.md`，只加入一句：

> 既定论文大框架不变，各问题章节内部按真实数学任务与求解依赖组织小节，并按决定性分配详略、就近闭合图结果证据。

不得复制完整规则。

## Phase 7：版本与 Changelog

只有 Phase 1--6 全部通过后：

- Skill `7.18.0 → 7.19.0`；
- writing reasoning schema `1.4.0 → 1.5.0`（暂定）；
- 同步 version carriers；
- 更新 CHANGELOG；
- 更新 README 简短能力说明。

## Phase 8：Generated metadata

运行 generator，刷新：

- `SKILL_FILE_INDEX.md`
- `TEMPLATE_INDEX.md`
- `MANIFEST.sha256`

生成文件不得手工修改。

## Phase 9：完整 CI

必须通过：

- Static contract lint；
- Generated file contract；
- Python 3.10--3.14；
- LaTeX CUMCM；
- LaTeX MCM-ICM；
- LaTeX Diangong；
- Production LaTeX attestation。

## Phase 10：Release / Merge

只有全部通过后：

- PR Ready；
- squash merge；
- main 回读版本；
- main 合并后完整 CI；
- 将本计划归档到 `legacy/architecture/`。

---

# 13. 兼容性与明确非目标

## 13.1 向后兼容

本轮不新增：

- Project State 字段；
- Workbook 字段；
- CLI 参数；
- Runtime Gate；
- 模型审批状态；
- 题型 taxonomy 字段。

因此旧项目无需迁移。

## 13.2 不改变 v7.18 已有能力

继续保留：

- Continuous Mathematical Narrative；
- Formula Prose Rhythm；
- Model-to-Solver Bridge；
- Professional Heading Semantics；
- Result-adjacent Interpretation；
- Cross-question incremental writing。

v7.19 是在其上补充“局部小节架构 + 详略分配 + 图结果叙事”，不是替换。

## 13.3 不改变论文大框架

这是本计划的**最高优先级边界**。

正式实现和测试必须保证：

```text
符号说明
→ 数据说明/必要数据预处理
→ 共享基础模型/模型准备
→ 问题一模型建立及求解
→ 问题二模型建立及求解
→ ……
```

仍是既定顺序。

其中可选章节是否出现仍由现有规则决定，但一旦出现不得被本轮规则重新排序。

---

# 14. 最终验收标准

只有同时满足下列条件，v7.19 才可以发布：

1. 既定大章节框架未变化；
2. 每个问题大章节内部的小节顺序能恢复真实局部求解思路；
3. 小节按数学任务划分，不按合同字段机械拆分；
4. 关键推导、关键边界、solver 依据、决定性结果得到足够篇幅；
5. 普通代数、重复定义、标准算法背景明显压缩；
6. 简单题不被写复杂；
7. 结果图能够说明“是什么关系—有什么关键特征—对当前问题意味着什么—为什么—必要时如何收束”；
8. 图分析不逐点复述、不复制图题、不形成固定句式；
9. 每个问题大章节最终都直接回答本问；
10. 后问只承接必要输出，不改变问题章节顺序；
11. v7.18 全部旧回归继续通过；
12. 8 类 prose smoke 通过；
13. 完整 CI 通过；
14. merge 后 main CI 再次通过。

---

# 15. 后续聊天 / Agent 上下文恢复说明

如果后续聊天上下文丢失，重新读取本文件后必须恢复以下事实：

1. 当前正式基线是 `v7.18.0`，本计划只是 `v7.19.0` 候选实施合同；
2. 用户明确要求**不能破坏既定论文大框架**；
3. 本轮所谓“符合求解顺序”只针对**大章节内部的小节、段落、公式、算法和结果顺序**；
4. 大框架继续固定为：
   `符号说明 → 数据说明/必要数据预处理 → 共享基础模型/模型准备 → 问题一 → 问题二 → ……`；
5. 本轮三项正式目标是：
   - Within-Question Subsection Architecture；
   - Detail Allocation Governance；
   - Figure Result Narrative；
6. 结果图分析强调：图身份/关系 → 关键特征 → 必要数值 → 当前设问含义 → 支持的原因 → 必要收束；
7. 三项规则都只抽象逻辑功能，不固定句数、标题数量或连接词；
8. 不改变模型、solver、validator、数值验证、Python/MATLAB、Schema 和 runtime；
9. 用户批准前不得开始正式 Skill 实现；
10. 正式实现后必须做大框架冻结回归、8 类 prose smoke 和完整 CI。

---

# 16. 当前停点

当前仅完成计划修订：

- 已根据用户审查意见冻结大章节边界；
- 已将原 “Post-Notation Main-Body Architecture” 收缩为 “Within-Question Subsection Architecture”；
- 已把“全文宏观闭环”收缩为“Question-Section Narrative Closure”；
- 已保留 Detail Allocation 与 Figure Result Narrative 两项能力；
- 尚未修改 `core/writing_reasoning_contract.yaml`；
- 尚未修改 `latex.md` / `ai_cleanup.md`；
- 尚未升级 Skill 版本；
- 尚未进入正式实现。

下一步：等待用户审查本修订版计划。