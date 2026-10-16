# CUMCM 问题章节写作结构、详略分配与图表落位规范化实施计划

> **文档状态：待评审的实施蓝图（plan_only / not_implemented）**  
> **目的：** 为后续聊天 / Codex 修改 Skill 时提供可追溯、可复核、可回滚的统一执行上下文。本文**不直接改变运行时规范**。  
> **编制基线：** `Vexushi1/mathmodel-skill` / `main` / Skill `10.18.2` / commit `1060c9bf6c68daa77e369104253e59fc70886de9`。  
> **后续执行前提：** 必须重新读取届时最新 `main` 的 `core/bootstrap.yaml` 和 `SKILL_CHANGE_GOVERNANCE.md`，确认版本、PR 重叠及权威源；不能将本文历史基线当作最新仓库事实。  
> **与其他 PR 的关系：** 编制时 PR #265（本地环境按需排障）仍未合并，修改 `README.md`、`scripts/README.md` 和自动生成的 `MANIFEST.sha256`；与本主题没有活动源文件交叉。本计划不得接管或修改该 PR。

## 0. 修改简报（供未来实现 PR 直接继承，并在执行前复核）

| 治理字段 | 本计划的决策 |
| --- | --- |
| 修改主题 | CUMCM 问题章节二级标题默认结构、三级标题颗粒度、论证详略和图表正文落位 |
| 当前版本 | 编制时 10.18.2；实施前以实际 main 为准 |
| 目标版本 | **计划文档本身：不升级**。后续行为规则实施初判为向后兼容 patch；若基线仍是 10.18.2，候选版本 10.18.3，最终由当时版本和治理决定 |
| 变更等级 | 本 PR 仅增加说明性计划文件：`docs`；**后续实施 PR 预计 `patch`**（会改变写作决策，不能伪装为纯 docs） |
| 直接目标 | 复杂问题优先采用 MODEL→SOLVE→RESULT→VALIDATE 的二级章节架构，条件式命名检验/对照；依据独立任务设置三级标题，并让关键数学依据、主结果及图表证据就地闭合 |
| 明确不做 | 不重排 CUMCM 一级章节，不锁死四小节，不添加标题/图表数量配额，不新增图表自动语义检查器、State/Schema 或本地人工预检，不改变模型/求解/数值事实和交付门禁 |
| 权威事实源 | `core/writing_reasoning_contract.yaml` 的 `model_establishment_solution_narrative`、`within_question_subsection_architecture`、`detail_allocation_governance`、`figure_result_narrative`、`subsection_granularity`；模板边界由 `templates/latex/cumcm/hsk/template_manifest.yaml` 定义 |
| 预计修改文件（未来实现） | 优先仅 `core/writing_reasoning_contract.yaml` 和 `modules/05_writing/paper_writing_protocol.md`；版本/Changelog/测试按正式 patch 治理补充 |
| 当前实际修改 | 本计划 `docs/cumcm_question_writing_refinement_plan.md`，不含上述 Authority 的任何行为修改 |
| 禁止触碰的模块（默认） | 数值求解、`core/user_execution_contract.yaml`、`core/workbook_schema.yaml`、`scripts/validate_user_execution.py`、`modules/03_result_analysis.md`、`legacy/`、LaTeX class 和 MATLAB 模板；禁止手工编辑生成索引/MANIFEST |
| 兼容性 | 旧项目章节、旧 `模型论文框架.md`、现有模板 smoke 样例和既有证据链继续可读可交付；仅新写作任务改变默认推荐行为 |
| 迁移要求 | 无强制迁移或批量改写历史论文；已批准结果、主模型与图表不自动 stale；如实际修改 active 正文/图片仍按现有局部 stale/审计规则执行 |
| 验收测试 | 章节结构与标题决策正反例、图表角色落位样例、现有 Authority/Framework/LaTeX smoke 和相应 GitHub Actions；最终 head 正式验收 |
| 回滚方式 | 本计划 PR：revert 新增文档；未来 patch PR：revert 对应 Authority/说明/版本及生成产物，重新远端验证 |

## 1. 背景、已有基础及真实缺口

### 1.1 已有能力，不重复造轮子

1. **固定一级结构已存在。** CUMCM Template Manifest 锁定 `问题{N}模型建立及求解`，`internal_structure: adaptive`；`model / solve / result / validate` 已列为四功能槽。其 `default_complex_question_headings` 是 maintained example / smoke profile，`must_not_infer` 明确不可把该样例当作固定运行时二级标题。
2. **二、三级标题允许自适应。** `core/writing_reasoning_contract.yaml#model_establishment_solution_narrative.within_question_subsection_architecture` 和 `subsection_granularity` 已有最大三级、独立任务判据、模型依赖顺序及反机械拆分要求。
3. **详略规则已存在。** `detail_allocation_governance` 允许按模型成立、关键推导、solver 前提和证据作用决定篇幅；不能靠字数配额判断。
4. **图表事实链已存在。** `modules/04_figure_evidence.md` 中 Figure Contract 已有 `Figure role`、`Core conclusion`、`Paper location` 和 `Caption duty`；`templates/model/model_paper_framework.md` 已有二/三级标题规划以及“论文与图表映射”“图表证据链”。
5. **写作前的 capability preflight 已存在。** `core/writing_runtime_contract.yaml#per_question_writing_capability_preflight` 负责消费当前事实/证据并激活相关写作能力，不应另造第二道预检或登记表。

### 1.2 真正缺口

现有规则强调“可以自适应”，但尚未让写作模型**先做二级功能归属，再决定三级拆分、篇幅轻重与图表位置**。结果可能出现：二级标题泛化或重叠；普通变量/算法简介被拆成多节；核心机理推导被压缩；结果与验证混写；图表生成后再临时找位置。

### 1.3 预期改善（不是保证结果）

- 评委快速定位“为什么建模—如何求解—直接答案—怎样质疑/验证”。
- 关键推导、决定性约束、题目专属算法适配和结果解释得到足够篇幅。
- 每张核心图/表有明确证据角色、就地解释和单一主要落点。
- 简单题与后问继承题保留压缩空间，避免模板化灌水。
- 不改变真实数值证据、模型批准、图表导出和正式交付管线。

## 2. 适用范围与优先级

### 2.1 适用范围

- **直接适用：** 使用现行 HSK CUMCM 模板、一级标题为 `问题X模型建立及求解` 的逐问正文。
- **可能借鉴但不自动推广：** 其他竞赛或 DOCX 论文的相同数学叙事原则。此次不得擅自修改跨竞赛固定模板。
- **仅针对逐问主体：** 不重排问题重述、问题分析、假设、符号、数据准备、共享模型、模型评价、参考文献及附录等一级槽位。

### 2.2 优先级（冲突裁决）

1. 官方赛题要求、经核验的当届竞赛提交约束；
2. Template Authority 对一级骨架、LaTeX 环境、示例 smoke 的固定边界；
3. 当前已批准模型/算法语义、有效工作簿和真实图表证据；
4. Writing Reasoning Authority 关于数学依赖、公式、证明、证据和标题的约束；
5. **本计划拟引入的默认二级标题语义与图表落位偏好**；
6. 语言可读性、排版喜好。

低优先级不得覆盖高优先级。默认标题不是保留一个错误结构的理由；标题调整也不得用来“顺便修正”已冻结模型或已验收数值。

## 3. 二级标题决策：先定功能，再定文字

### 3.1 复杂问题的首选框架

```text
问题X模型建立及求解                  ← 既有一级标题，保持不动
  X.1 XX模型的建立                  ← WHY / WHAT：依据、数学结构与闭合
  X.2 模型求解                      ← HOW：算法适配、编码与计算
  X.3 模型求解结果与分析            ← ANSWER：直接答案、决定性证据与解释
  X.4 模型检验 / 模型检验与对照      ← TRUST：条件式独立验证或对照
```

**四项是复杂问题的默认功能路径，不是强制出现四个子节、四个固定名字或固定标题计数。** 标题可以在必要时保留题目专属对象限定，但不能失去其功能归属。尤其第 3 项的首选文字明确使用**“模型求解结果与分析”**，不回退到“模型结果”“求解结果”。

### 3.2 各章入口 / 出口职责

| 二级功能 | 必须优先解释 | 应保留的典型核心内容 | 不应混入或过度展开 |
| --- | --- | --- | --- |
| MODEL / XX模型的建立 | 题意或机制提供什么、数学上还缺什么、为什么引入当前结构 | 对象与变量、关键关系、目标/约束、初边值、结构化简合法性、Final Model + 不可删除的 Key Bridge | 已在问题分析完整说过的背景、教科书式公式简介、求解器参数、未经验证的结果 |
| SOLVE / 模型求解 | 当前最终模型有哪些计算困难、何种 solver 真正适配 | 解析/降维/离散/算法选择理由、问题专属编码与可行性处理、关键精度/终止依据、输出映射 | 通用算法历史、代码工程日志、把 solver 名称当数学模型 |
| RESULT / 模型求解结果与分析 | 问题的直接答案是什么、哪项证据决定答案、含义是什么 | 主工作簿关键值、图表与趋势、最优方案、约束状态、证据支持的解释 | 重讲完整建模和求解、没有主结果就裸堆多图、把稳健性判定硬写成事实 |
| VALIDATE / 模型检验（与对照） | 针对什么具体风险/替代假设、改变和固定什么、关键结论是否改变 | 实际检验方法、有效范围、替代算法/模型比较、独立证据与负结果 | 把单纯设想当运行过的实验、以数值相近代替结构一致性、虚构 03B |

### 3.3 第四节的条件式命名：明确判据

用**当前已执行且已验收的独立论证任务**判定，不以计划中的模型、运行名称或图片样式判定：

| 真实情况 | 正式二级标题 | 边界 |
| --- | --- | --- |
| 无值得独立展开的检验，也无实质对照 | 不设置独立 X.4；必要的主计算质量说明留在求解附近 | “未设置”不等于声称模型已经通过稳健性检验 |
| 存在实际可入文的验证，但没有实质模型/算法对照 | **模型检验** | 参数扰动、鲁棒性、残差/外样本等按证据角色组织 |
| 存在实际执行、可比较的替代模型或同模型替代算法对照 | **模型检验与对照** | 必须明确 comparator 的模型/算法角色与共同比较口径；即使独立内容以对照为主也适用 |

**不要混淆：** 同一模型的多算法求解 ≠ 不同数学模型对照；同一算法的多种参数设置、场景或敏感性曲线通常仍属检验，不自动升级为“与对照”。若“另一算法”只被提议但未实际运行/验收，不能据此更名。未完成/失败的比较可以如实说明其状态，不得将其当作完成的有效对照。

### 3.4 特殊与精简情形

- 直接解析、无需独立 solver 论述：可以使用 MODEL + RESULT，甚至在连续短小节中完成，不捏造算法段。
- 求解与模型天然一体、拆分会割裂推导：允许有记录理由的局部合并或更合适的专业标题。
- 后问沿用前问模型：仅交代继承与真实新增的变量/约束/判据，不重复完整建立过程；如 MODEL 工作量非常少可紧凑写。
- 多个独立模型在同一问并列使用：先确定统一回答当前问题的数学任务及相互依赖，再决定是否用三级标题区分；不能把一问简单复制成多套四节。
- 共享机理：仍服从上游 `模型准备` 条件式章节职责，逐问只引用和增量推导。
- 题目专属二级标题优于本表时可以替换，但必须能映射回功能槽；替换不构成新增第五类功能槽。

## 4. 三级标题准入与详略治理

### 4.1 写作决策次序

```text
识别本问独立数学任务、结果和检验风险
→ 对每项任务归属二级功能
→ 标出决定模型成立 / solver 适配 / 答案 / 可信度的关键任务
→ 选择是否设置三级标题
→ 分配必要公式、解释、图表和证据
→ 自查过度拆分、关键论证被压缩及非必要赘述
```

三级标题**不以字数、图数、公式数或“小节对称”触发**。即使一节只有一个独立命题或关键边界证明，也可有三级导航；即使公式很多但属于一条连续短逻辑链，也不必机械逐式分节。

### 4.2 各功能槽可拆分的具体条件

- **MODEL：** 独立机理/几何关系、控制方程推导、关键边界/约束来源、结构化简/充分性、不同模型对象及不可替代证明等。
- **SOLVE：** 非平凡 solver family 选择或条件、独立分解/迭代阶段、关键编码与可行域处理、影响答案的数值参数证据及精度终止要求等。
- **RESULT：** 两项以上真正不同、具有单独阅读与回指必要的最终结果任务，例如“关键参数与最优解”“空间分布与路径结构”“多策略结果与代价分析”；这是**允许**而非禁止三级标题，不为一张普通图/表单设章节。
- **VALIDATE：** 不同风险类型（模型结构、参数、随机性、外样本）或独立 comparator（baseline/alternative solver/alternative model）承担不同结论时拆分；若只有一项检验，连续正文即可。

### 4.3 关键内容详写与非关键内容压缩

详写触发（基于作用，而非篇幅）：关键模型选择为何适配、非显然推导、初边值与核心约束、等价/充分/启发式简化依据、solver 正确性前提及当前范围、关键数值参数、决定答案的结果及其解释、影响主结论的检验差异和失效边界。

压缩对象：符号反复翻译、机械代数、普通同型约束、标准算法的通用百科、重复工作簿字段、逐点读图、不改变判断的中间计算、已经建立且未变化的跨问关系。

**刚性边界：** 不因为想简洁就删核心 Key Bridge Relation、非显然 supporting derivation 或真实核心证明；不因为想详细就虚构模型选择依据、数据、实验、假设或最优性证书。保持最大三级（`section / subsection / subsubsection`），不允许用粗体独立行、无编号小标题或 `paragraph` 伪造第四级。

### 4.4 反面例与推荐决策

| 场景 | 不推荐 | 推荐 |
| --- | --- | --- |
| 变量只有两行定义 | 独立 `X.1.1 决策变量` + 极短内容 | 并入 `XX模型的建立` 的相关公式段 |
| 非平凡活动边界决定解 | “由于边界约束可得最终模型”一笔带过 | 说明边界来源、必要/充分性、求解消费方式；需要时三级展开 |
| 标准算法照常使用 | 几页介绍遗传算法的一般历史 | 说明本题编码、约束处理、参数证据、终止规则 |
| 结果包含轨迹与资源调度两项独立答案 | 所有图表连续堆积，末尾一段总述 | 结果章节按实际任务拆三级标题并就地解释 |
| 一个实际敏感性检验，无替代方法 | 仍写“模型检验与对照” | 写“模型检验” |
| 没有实际检验数据 | 创建空“模型检验”段称稳定性良好 | 省略独立章节，保留必要的结论限制 |

## 5. 图表落位：语义职责优先、就地证据闭合

### 5.1 唯一主规则

**图表出现在它首次承担决定性数学判断的位置；图型名称、脚本文件名、工作簿名称及 Figure Level 不自动决定章节。** 同一张参数曲线用于主计算的网格精度选择可归 SOLVE，用于现实参数扰动后的答案稳定性可归 VALIDATE；需以当前 Figure Contract 的 `Core conclusion / Primary question / Figure role / Paper location` 实际判断。

### 5.2 默认映射（可有证据支持的例外）

| 主要证明职责 | 默认二级章 | 常见图/表 | 必须解释 |
| --- | --- | --- | --- |
| 模型对象、机制、几何与约束的成立/来源 | MODEL | 机理图、空间关系、网络结构、临界几何示意 | 图怎样支持哪个关系、公式、判据或边界 |
| 数值方法如何执行、精度和可行性是否满足 | SOLVE | 真正有用的算法流程、离散收敛、残差/可行性曲线 | 方法条件、容差/精度、实际求解有效范围；收敛不代表全局最优 |
| 本问直接结果、方案与决定性现象 | RESULT | 最优参数表、策略表、状态轨迹、预测、分布、Pareto 或空间结果 | 主值、决定性特征、题目含义及可靠的机制解释 |
| 独立挑战主结论或比较替代方法 | VALIDATE | 敏感性、鲁棒性、外样本误差、算法/模型对照表 | 比较口径、变化范围、结论是否变、证据支持的边界 |

跨功能的表图仅在**确有直接比较/证明收益**时可在最能承载主论点的位置放一份，并用另一节的编号交叉引用；不因为功能跨度默认复制图片，也不把所有 L4 数值合法性图机械放第四节。

### 5.3 图、表及正文的职责边界

1. 正文先说明当前要验证/展示的关系及图表为何必要，随后展示图/表，紧邻指出决定性趋势/阈值/差异/答案。
2. 图题/表题识别对象、范围、指标及必要口径；坐标轴、图例、表头、表注提供可读条件；正文解释问题含义。三者不重复长文。
3. 关键单点精确答案优先直接文字或结构清楚的表格；连续趋势、空间状态、分布或复杂比较选择合适图型，不为“图表比例”强制绘图。
4. 多面板图必须有共同主结论；没有必要的对比不混绘不同量纲、不依赖颜色暗示未证实关联。
5. 论文代码中保持唯一 `label`、正文明确编号引用；物理浮动位置由 LaTeX Adapter 管理，原则上与首次有效引用接近；不规定每幅图必须 `[H]` 或改变模板渲染器。
6. 核心图表必须有 current 数值/数学来源、实物图片、图注和邻近证据解释，不能用“如图所示”代替分析。

### 5.4 证据链和绝对边界

- 复用既有 `模型论文框架.md` 的标题规划、`论文与图表映射`、`图表证据链` 与 Figure ID，不新增强制表单、不复制统计口径为第二份 Authority。
- 主问题结果源：accepted `问题X求解结果.xlsx`；独立敏感性、异质性及比较需 `Analysis Necessity Gate=required` 并有已执行、已验收的 `问题X结果深化分析.xlsx`（03B）。`not_required` 不得补造 03B 或检验图。
- 建模阶段的题目专属机理图遵守 `modules/04_figure_evidence.md` 和 Mechanism Contract；数据驱动图不允许绘图入口重求解。
- 图表**仅重新定位或改正文引用**时，原则上不使已批准模型语义 stale、不触发 03A/03B 数值重跑；但 active `.tex`/图片/`caption`/框架位置发生变化后，受影响的 Figure、Paper Fragment、source bundle、LaTeX audit/compile/PDF 证明需要按既有依赖规则刷新。若图揭示模型/事实冲突，应回上游处理，不能在绘图或文案中偷偷改模型。
- 机器只可检查可解析引用、真实文件、source/hash 和固定渲染规则；**是否落在最合理的章节属于语义审阅**，不新增“看标题词猜图表位置”的阻断式程序检查。

## 6. 写作前的轻量规划：融入既有逐问能力预检

正式撰写每一问前，从**当前** Model/Formula/Algorithm Trace、accepted results、Figure Contracts 和 `模型论文框架.md` 中完成一次轻量内部判定：

1. 本问是否复杂到适用四功能默认框架；哪项功能不需要独立成节？
2. 已有何种 Model/Solver/Validator 角色及主结果；有无实际独立对照证据？
3. 哪些数学任务关键、需证明或详写；哪些可紧凑？
4. MODEL / SOLVE / RESULT / VALIDATE 的二级落位分别是什么？
5. 哪些独立任务需要三级标题，尤其结果是否有多项独立任务？
6. 每张已批准核心图表的主论点、默认落点、正文首引位置和解释职责是什么？
7. 标题与图表规划是否冲突已批准模型、当前 Figure ID、证据来源或旧项目状态？
8. 通过条件项后再按 `template_first_progressive_authoring` 正文逐节写作；不把全部 Authority 预加载成一次大提示词。

**不创建新 `preflight` gate、项目状态字段或重复的规划表。** 仅利用 `templates/model/model_paper_framework.md` 的 `论文整体框架` 第 9/10 项、本问 `问题章节二级/三级小节计划` 与 `论文与图表映射`。若已有足够记录无需再重复填写。

## 7. 内容归属边界：数值质量、主结果与结果深化

- **主模型计算内的必要质量证据**：求解器真实停止条件、残差、约束可行性、离散精度等；根据论证功能就地进入 SOLVE 或 RESULT。这些不自动等同于敏感性、鲁棒性或替代模型验证。
- **RESULT：** 先回答本问，然后邻近图表解释关键含义，不将实际结果解释全部推迟到第四节。
- **VALIDATE：** 针对已经给出的主结论提出具体风险，声明改变与固定的条件、指标与比较基准，报告真实变化及适用范围，返回“主结论是否仍成立”。
- **同模型多算法 vs 不同模型对照：** 选择术语和算法角色应与上游分析合同一致；仅仅“两个数值相近”无法证明同模型、模型有效或结论稳定。
- **负结果同样如实写**：比较不一致、受扰动后失稳、没有外样本证据，都应保留；不得以“章节有了就要给出好结果”为由篡改。
- 若检验没有真正执行，不得用空第四节或泛化“模型精度高、鲁棒性好”冒充证据。

## 8. 权威文件修改映射（未来实现 PR 执行清单）

### 8.1 必改：`core/writing_reasoning_contract.yaml`

以现有结构局部增补，禁止再造并列 `cumcm_heading_policy` 全量 Authority：

| 现有节点 | 计划增补 | 不应改变 |
| --- | --- | --- |
| `model_establishment_solution_narrative.within_question_subsection_architecture` | CUMCM 四功能默认结构、二级标题语义、第四节条件式命名、简题例外、局部功能依赖顺序 | 一级骨架、现有最大三级规则 |
| `model_establishment_solution_narrative.detail_allocation_governance` | 与二级功能/三级标题决定相联系的“关键论证优先展开”判断 | 既有公式角色、证明与反硬字数配额 |
| `model_establishment_solution_narrative.figure_result_narrative` | 图表按证据职责分配默认槽位、就地引用与解释规则 | Figure Contract 的制作、数据归属、图片真实审批 |
| `subsection_granularity` | 对“模型求解结果与分析”允许按独立任务拆三级的明确条款，避免四节/结果节僵化 | `hard_count_limit: false` 及精简题边界 |

**重要：** 写作规范的运行时 Authority 只能在这里定义；其他描述文件用引用/操作说明，不重复存放完整 YAML 规则。具体字段命名应沿既有节点组织，不应因本计划引入大规模 schema 迁移。

### 8.2 必改：`modules/05_writing/paper_writing_protocol.md`

在现有章节中就地完成“实践版”调整：``2--3`（标题职责、四功能默认结构），``7--8`（MODEL/SOLVE 的主次信息）、`9`（“模型求解结果与分析”的结果+解释闭环与可拆三级）、``10--11`（检验/对照命名条件）、`13`（图表角色→论文落点、证据邻近解释）。尽量提供精炼的不同题型正反例，而非重复 Authority 整篇规则。

### 8.3 关联影响面：优先只读，默认不改

| 文件 | 为什么要检查 | 默认处理 |
| --- | --- | --- |
| `templates/latex/cumcm/hsk/template_manifest.yaml` | 确认一级标题、四功能槽、`maintained_example_profile_only` 与 smoke 例子不冲突 | **保留**既有文字样例与模板固定检查；运行时命名由 Writing Authority 拥有 |
| `templates/latex/cumcm/hsk/README.md` | 检查 A196 示例、固定文字与 Runtime Authority 的边界 | 原则上不动；如旧示例真的被读作运行时规则才做最小引用修复 |
| `modules/04_figure_evidence.md` | 已有 Figure `Paper location` / Evidence level / `Caption duty` | 不建第二套章节分类；如需要只增指向 Writing Authority 的单条引用 |
| `templates/model/model_paper_framework.md` | 现成小节计划、图表映射与 Figure ID | 不新增栏位或强制表单 |
| `core/writing_runtime_contract.yaml` | 现有逐问 preflight 和渐进读取 | 不改路由、Preflight/gate；优先通过原有输入实现 |
| `modules/05_writing/latex.md` | `figure` / `table` / `label` / `caption` / 三级对应载体 | 保持排版 Adapter 责任，不新增图表位置硬校验 |
| `core/output_contract.yaml`、`modules/06_review_delivery.md` | 结果证据、正式载体和 review 的既有边界 | 检查但不因标题改动扩张 |
| `templates/latex/cumcm/hsk/sections/*.tex` | 维护示例的 literal smoke 会固定读取“模型建立/求解/求解结果/结果的分析与验证” | **不为本次 Runtime 命名偏好强迫改写 smoke 样例** |

只有真实冲突与测试失败能证明必须修改这些文件时，才提出最小影响调整及理由；不得顺手重写模板。

### 8.4 版本/日志/索引的条件维护

本次计划文件不升级版本。**后续修改真实 Authority 行为**时遵守届时 `SKILL_CHANGE_GOVERNANCE.md`：若按 patch 发布，统一更新当前 Skill 版本及治理要求的 `core/bootstrap.yaml`、`core/writing_runtime_contract.yaml`、`.codex-plugin/plugin.json`、`core/output_contract.yaml`、`CHANGELOG.md`、相关入口/版本测试；具体实际修改列表以当时的版本一致性检查为准。**所有生成的 `MANIFEST.sha256`、File/Template indexes 仅交由 GitHub `refresh-generated` 更新，不手改。**

## 9. 分阶段实施、完成条件与冻结边界

| Phase | 工作 | 主要产出 | 完成 / 止损标准 |
| --- | --- | --- | --- |
| P0 基线与冲突核对 | 重读最新 bootstrap/治理、PR、Authority、原有 tests，冻结小范围修改简报 | 修改影响面与基线 SHA、明确不做 | 存在重叠 PR 时暂停并串行；不依旧上下文强写 |
| P1 Authority 局部增补 | 二级功能、条件命名、三级拆分/详略、图表语义落位 | 最小 YAML diff，唯一规则位置 | 保留已有 schema/角色与 anti-template；无互相冲突条款 |
| P2 执行说明 | 在 Paper Writing Protocol 的相应章节给出可执行写法、正反例和少量引用 | 最小 MD diff | 不复制 Authority 为第二套标准，不强制统一句式 |
| P3 行为级案例与回归 | 针对有无对照、简单/复杂题、图表职责及结果拆分编写/更新精准 tests | 测试和示例的可复核断言 | 强制守不变量、避免用文本数量推断语义 |
| P4 版本/生成/专项 CI | 按治理同步版本、Changelog；独立分支 push，自动生成产物；draft PR 跑受影响检查 | 源码 commit、bot 生成 commit、targeted 结果 | 仅预期 diff、无生成文件手改，错误不通过重跑全流程掩盖 |
| P5 正式验收及发布 | ready PR 冻结最终 head，在 GitHub 运行完整正式 CI；成功才合并并核 main | PR 与 CI run、最终/合并 SHA、Release 判断 | 未完成所有适用门前不得宣称合并/发布成功 |

**停止条件：** 如果实现过程中发现需要修改数值工作簿 Schema、执行/收据合同、Figure Contract 主结构或模板一级章，则先停下并提交范围扩大评审；不得把超范围问题塞进本 PR。

## 10. 验收用例矩阵（应基于项目事实，不伪造赛题结论）

| ID | 代表场景与输入证据 | 期望写作行为 | 反面失败表现 |
| --- | --- | --- | --- |
| A1 | 复杂约束优化，独立模型推导、solver、方案、敏感性 | 以四功能组织，MODEL 的关键约束详细解释，检验独立成章 | 约束一行带过、算法百科占主篇幅 |
| A2 | 无独立验证或替代模型的简单解析计算 | 精简为 MODEL+RESULT 或短连续结构 | 硬凑 X.2 算法、X.4 稳健性 |
| A3 | 主结果+参数敏感性，**无实际 comparator** | X.4 写 **模型检验** | 写“模型检验与对照”但无对照 |
| A4 | 主模型与真实运行的同模型第二 solver，比得出结果 | X.4 写 **模型检验与对照**，注明“同模型多算法” | 错称“两个不同数学模型” |
| A5 | 仅设想第二模型，未运行、未验收 | 不用“与对照”，不制造比较图 | 将 planned alternative 写成 accepted |
| A6 | 结果有独立的最优参数组合和空间/轨迹两个任务 | 在 `模型求解结果与分析` 内按需拆三级，并各自解释 | 仅因 RESULT 名称而禁止三级、连续裸堆图 |
| A7 | 变量定义极短，关键初边值/活动约束推导很长 | 合并变量定义、保留关键推导与证明 | 变量定一级三级占据版面，核心推导压缩 |
| A8 | 标准算法无改进，但本题有非平凡编码/约束修复 | 介绍编码、数学影响、可行性与终止；压缩标准百科 | 反向扩写通用算法介绍 |
| F1 | 相同形式曲线 A 用于时间步长精度选择，B 用于现实参数扰动 | A→SOLVE，B→VALIDATE，依据 Figure role/论点而非折线图型 | 只根据“折线图”统一放结果节 |
| F2 | 题目专属几何/机理图支撑边界关系 | MODEL 处首次使用，近邻明确对应公式和判据 | 图被塞到 RESULT 且不解释关系 |
| F3 | 当前 accepted 主结果有高精度参数和结果曲线 | 精确值直接文字/表格、趋势适合图，编号引用+局部答案 | 结果只摆表图，正文无解释 |
| F4 | `Analysis Necessity Gate=not_required` 且无 03B | 不生成敏感性、鲁棒性、多算法 comparison 图 | 为第四节补齐而伪造 03B |
| F5 | 图表位置改变但数值与模型未变 | 更新 Figure/Paper 证据和 LaTeX 审计/编译，**不重跑 03A/03B** | 无谓触发数值重算或沿用 stale 编译证明 |
| T1 | 维护示例 smoke 仍写旧标题 | 继续按 `maintained_example_profile_only` 运作；不将旧示例强制当运行时语义 | 因新规则要求而删除有效 smoke 或模板 |
| T2 | 任一问题出现真正第四级标题 | 既有正式层级检查应阻止；证明分情况不误判 | 使用 `paragraph` 绕过四级禁令 |
| T3 | 跨问共享机理，后问只新增一个边界条件 | 引用共享基础，只推导真实增量 | 对每一问重复完整模型造成冗长 |
| T4 | 检验结果与主结果冲突或负结果 | 如实记录差异和主结论限定；不能无证据称鲁棒 | 为配合“模型检验”标题强行写正面结论 |

### 10.1 自动与人工审查的合理界限

- **确定性自动检查可做：** YAML 语法/schema 基本兼容、Authority 链接存在、模板/章节一级骨架、LaTeX 可解析层级、唯一 label/引用、源文件与生成哈希、案例中已明确的功能槽/状态声明。
- **必须人工语义审阅：** 数学独立任务是否值得三级、核心推导是否完整、某图的证明职责、详略分配是否准确、比较是否实质可比。
- **禁止建立的伪规则：** “三级标题超过 n 个即失败”“标题必须含某词”“每章必须至少一张图”“RESULT 段字数下限”“看到敏感性曲线即证明稳健”。

### 10.2 远端 CI 检查点

结合实际测试影响面优先复核 `tests/test_v743_writing_structure_style.py`、`tests/test_v750_writing_reasoning_architecture.py`、`tests/test_v800_template_authority.py`、`tests/test_v800_writing_runtime.py`、`tests/test_v870_question_writing_capability_preflight.py`、`tests/test_framework_project_memory_contract.py`、`tests/test_v931_writing_readability_w4_acceptance.py`、`tests/test_authority_single_source.py`，以及现行 LaTeX/source audit 相关测试。**这些只是待核对的既有回归入口，不宣称已经运行或与目标完全一一对应**；最终决定依据测试文件的真实断言与最新 `main`。

正式验收必须遵守最终 PR head：GitHub Windows Python 3.10 / 3.14 分片与聚合、Static contract lint、Generated file contract、MATLAB native contract、LaTeX templates、Production LaTeX attestation 及适用的 Optimization baseline；开发阶段优先专项测试，冻结时完整回归。不能本地跑一次或仅以专项绿灯代替正式验收。

## 11. 风险清单与控制措施

| 风险 | 典型症状 | 缓解 |
| --- | --- | --- |
| 模板语义与 Runtime Authority 冲突 | smoke 示例标题被当硬模板 | 保留 `maintained_example_profile_only`，只改正文写作 Authority |
| 默认结构僵化 | 简单题硬凑四节 | 明写 `default` 非 `hard`；用 A2 检验 |
| 标题美化压倒模型事实 | 更名导致公式、算法或结果口径漂移 | 以 current Framework/accepted workbook/Model Approval 为边界 |
| 三级泛滥或过度合并 | 每个公式设一节，或整章不可导航 | 独立任务/可恢复性判据 + 正反例，不设数量配额 |
| 图表放置过于机械 | 图型决定章节、相同数据多次入文 | 以论点和 Figure role 决策，就地首引 |
| 证据冒充 | 03B 不存在却宣称敏感性/对照 | 按 Analysis Necessity Gate / accepted evidence fail closed |
| 重复定义规则 | YAML、模块文档和模板各有一套互冲突标准 | Authority 一处定义，消费者简述并引用 |
| 过度工程 | 新增额外中间文件、审计器或执行前动作 | 复用既有 Framework、Figure、Writing capability preflight |
| 回归时间与反复重跑 | 每次微调触发所有 30 分钟全量测试 | 开发阶段先用远端 targeted 检查；冻结 head 后跑完整 CI，不降低最终门 |
| 历史版本漂移 | 下一聊天以本计划中的 SHA 直接写 main | P0 必须重读 main 与 PR；版本/测试因最新仓库而调整 |

## 12. 兼容、迁移及回滚细节

1. **旧项目可运行：** 本次计划无运行影响；未来 patch 仅调整新写作默认决策，不改变历史项目执行、结果工作簿与模型批准效力。
2. **旧字段/CLI/目录：** 不删除、不更名；因此无淘汰期限与兼容层需要。
3. **旧论文内容：** 不批量改写已存在的正式 LaTeX 章节；用户要求重写某一问时才按新默认结构判断是否更名/拆节。
4. **生成/证据刷新：** 实际改正文 LaTeX/图片仍需刷新 source bundle、Figure ID、正式审计与编译报告；仅改计划/Authority 不得凭空宣布赛题数值 stale。
5. **计划 PR 回滚：** revert `docs/cumcm_question_writing_refinement_plan.md` 即可；GitHub 生成的 MANIFEST 由 workflow 统一恢复。
6. **未来实现 PR 回滚：** 整体 revert 单主题 source commits（包含与其一致的版本/日志），允许生成工作流重新刷新受管文件，远端重验；不通过修改 accepted 工作簿来回滚写作规则。

## 13. PR 与发布流程（必须遵守治理）

- 本计划为**独立 docs PR**，只新增本文件；经 GitHub 自动生成受管文件后以最终 head 核对文档差异。计划 PR 可以等待用户确认，未合并前不代表主仓库已接受未来行为修改。
- 后续实际实施须在**新的聊天 / 新分支 / 新 PR** 中依据本计划启动 P0，不能把当前计划分支混改为行为实现分支（除非用户另行明确要求且治理允许）。
- 未来实现 PR 的描述至少包含：背景、目标/不做、等级与目标版本、权威源、逐文件修改、兼容迁移、受影响测试、生成物、风险回滚、最终 PR head/checkout、合并后 main 状态。
- 发现与其他 PR 修改同一 Authority 时必须停写、串行；不能同时强行向同一权威文件合并两套规则。
- 不手工修 `MANIFEST.sha256`、索引或伪造 CI；完成前准确表述“尚未完成验证/尚未合并”。

## 14. 下一聊天 / Codex 的执行指令（可直接引用）

> 目标仓库 `Vexushi1/mathmodel-skill`。先**从最新 main** 读取 `core/bootstrap.yaml` 和 `SKILL_CHANGE_GOVERNANCE.md`，核验版本、head、未合并 PR、Authority 和测试，不要把计划中 10.18.2 的历史信息当作最新事实。随后读取本计划 `docs/cumcm_question_writing_refinement_plan.md`，依第 0 节复核修改简报，第 8 节冻结文件范围，第 9 节按 P0→P5 实施。只在 `core/writing_reasoning_contract.yaml` 定义正式写作语义，在 `modules/05_writing/paper_writing_protocol.md` 添加执行指导；不直接改 `templates/latex/cumcm/hsk/template_manifest.yaml` 的 smoke 字面标题。复杂问题默认四功能，第四节严格按“模型检验 / 模型检验与对照”根据已验收比较证据命名，第三级依独立数学任务拆分，结果节也允许自适应三级；图表按主要论证位置就地落位。保持用户数值执行、accepted evidence、Figure Contract 和正式交付不变量。先补行为级正反例，开发阶段 GitHub targeted，冻结最终 PR head 后完整 GitHub Actions 通过才合并并核验 main。**没有用户另行授权前，本计划只用于审阅，不自动触发实现。**

## 15. 后续修订与签收

- **计划范围确认：** 用户已认可“模型求解结果与分析”、第四节自适应命名、结果节必要时使用三级、图表按论证职责定位，并要求先写详细计划作为后续上下文；本文件依此整理。
- **尚未发生：** 没有运行时 Authority 修改、没有样例赛题数值计算、没有新行为测试结果，也未获得本计划之外自动推进实现的授权。
- **后续若有变更：** 在新 PR 或本计划审阅阶段记录“变更原因—受影响规则—验收用例调整—是否超出原始范围”，而不是无说明地扩大到整个论文生产链。

---
**本文件是实施规范的计划，不是已生效的 Skill 合同。实际合同只能由通过仓库治理、测试并合并到 main 的 Authority 改动形成。**
