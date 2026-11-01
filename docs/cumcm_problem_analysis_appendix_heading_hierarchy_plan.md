# CUMCM 问题分析与附录标题层级统一实施计划

> **文档状态：** \`plan_only / not_implemented\`。本文是后续仓库实现的实施蓝图，不是已经生效的运行时规范。  
> **本次 PR 边界：** 只新增本计划文件；不修改 Skill Authority、模板、脚本、测试、CI 或版本文件。  
> **后续实施原则：** 必须在实施时重新读取最新 \`main\` 的 \`core/bootstrap.yaml\`、\`SKILL_CHANGE_GOVERNANCE.md\` 和本计划，重新核对版本、PR、权威文件与测试，不得把本文基线当作未来的实时仓库状态。

---

## 0. 修改简报

| 治理字段 | 本计划确定内容 |
|---|---|
| 仓库 | \`Vexushi1/mathmodel-skill\` |
| 本计划编制基线 | Skill \`10.23.2\`；\`main\` commit \`9e029966a691e8858fdea740ca821cdf5e77dce5\` |
| 编制日期 | 2026-11-01 |
| 编制时未合并 PR | 无 |
| 本计划文件 | \`docs/cumcm_problem_analysis_appendix_heading_hierarchy_plan.md\` |
| 本计划分支 | \`docs/cumcm-problem-analysis-appendix-heading-plan\` |
| 本计划变更等级 | \`docs\`；仅增加实施计划，不改变运行行为，不升级 Skill 版本 |
| 后续实现主题 | CUMCM 问题分析标题与附录标题层级统一 |
| 后续目标版本候选 | \`10.23.3\` |
| 后续实现等级候选 | \`patch\`；实施前按当时治理规则复核 |
| 后续实现分支候选 | \`fix/v10.23.3-cumcm-frontmatter-appendix-heading-hierarchy\` |
| 后续实现 PR 标题候选 | \`fix: standardize CUMCM problem-analysis and appendix heading hierarchy\` |
| 唯一结构 Authority | \`templates/latex/cumcm/hsk/template_manifest.yaml\` |
| 写作执行说明 | \`modules/05_writing/paper_writing_protocol.md\` |
| 阶段读取 Authority | \`core/writing_runtime_contract.yaml\` |
| 模板静态校验 | \`scripts/validate_template_manifest.py\` |
| 实际论文结构审计 | \`scripts/audit_paper_prose.py\`，由 \`scripts/audit_latex_project.py\` 对模块化 LaTeX 源码展开后调用 |
| 生成文件 | 仅由现有 GitHub \`refresh-generated\` 流程更新 |

**直接目标：**

1. 将 CUMCM 论文“问题分析”章节的二级标题正式固定为“问题一的分析”“问题二的分析”，按实际小问数量依次扩展。
2. 将附录正式固定为一个一级总标题“附录”，其下以“附录A”“附录B”……作为二级标题。
3. 将上述规则写入唯一结构 Authority，并同步模板、写作协议、阶段读取、模板校验和实际论文审计。
4. 核查本次涉及的语义漂移、版本同步、阶段读取失效、审计边界和编译覆盖问题，不把局部修复扩张成全仓库重构。

**明确不做：**

- 不固定“问题一模型建立及求解”内部的二级/三级标题；该部分继续遵循现有自适应规则。
- 不修改数学模型、求解算法、数据处理、工作簿、数值结果、Figure Contract 或用户执行流程。
- 不修改 Model Approval、Project State、03A 主求解、03B 深化分析、Figure Evidence、Output Contract 的业务语义。
- 不新增独立写作模块、项目状态字段、审批节点、重复 gate 或第二套标题规则。
- 不批量重写历史论文，不自动迁移用户已有 LaTeX 项目。
- 不把附录设为必选章节，不为“结构完整”生成空附录。
- 不修改 MCM/ICM、电工杯或其他竞赛模板。
- 不修改 \`legacy/\`，不修改参考论文文件及其 SHA256 来源记录。
- 不手工修改 \`MANIFEST.sha256\`、\`SKILL_FILE_INDEX.md\`、\`TEMPLATE_INDEX.md\` 或生成的阶段读取导航。

**核心兼容要求：** 新规则只作用于 CUMCM HSK 模板的前置“问题分析”结构和条件式“附录”结构；各问题模型章节仍保留真实任务驱动的标题自适应。旧项目不自动重排，既有模型批准、数值验收和证据资格不因本次标题规范变化而失效。

---

## 1. 背景与已核实的现状

### 1.1 问题分析章节：示例已存在，正式规则缺失

当前模板文件：

\`templates/latex/cumcm/hsk/sections/02_problem_analysis.tex\`

已经包含：

- \`\\section{问题分析}\`
- \`\\subsection{问题一的分析}\`
- \`\\subsection{问题二的分析}\`
- 问题三及以后按实际小问数量扩展的注释示例。

因此，本次不是重新设计问题分析的写作内容，而是把现有示例提升为可执行、可检查的正式标题规则。

目前缺口：

1. \`template_manifest.yaml\` 的 \`paper_skeleton.ordered_slots.problem_analysis\` 只声明 \`default_internal_roles: per_question_analysis\`，没有正式规定二级标题的精确模式、数量、顺序和编号方式。
2. Manifest 的 \`authority_boundary.forbidden_template_authority\` 仍有宽泛的 \`force_internal_subsection_names\`，没有区分“问题分析的固定标题”与“各问题模型章节的自适应标题”。
3. \`templates/latex/cumcm/hsk/README.md\` 已经展示“问题一的分析”“问题二的分析”，但其 Template/Writing 职责边界没有把这一固定结构例外表达清楚。
4. \`modules/05_writing/paper_writing_protocol.md\` 的 §6.2 已要求多问论文按问分小节，但没有把标题字面形式固定下来。
5. \`core/writing_runtime_contract.yaml\` 的 \`problem_analysis\` 阶段目前读取 Protocol §6.2、Problem Contract 和跨问依赖，没有显式读取 Manifest 中的标题结构依据。

### 1.2 附录：当前是多个一级节，不符合目标层级

当前模板文件：

\`templates/latex/cumcm/hsk/appendices/appendices.tex\`

目前采用：

- 一个 \`appendices\` 环境；
- 环境内多个 \`\\section{核心代码与复现说明}\`、\`\\section{补充推导与图表}\`。

这会把每个附录材料作为一级 section，而不是“附录”总标题下的二级标题。

当前主文件：

\`templates/latex/cumcm/hsk/hsk_main.tex\`

已经将附录设置为条件槽位，默认注释关闭；这一行为必须保留。

当前 Manifest 的 appendix slot 也已明确：

- \`required: false\`
- \`default_active: false\`
- 仅在官方规则要求或确有必要的支持材料时启用。

因此，本次只调整附录内部层级，不改变附录的条件启用逻辑。

### 1.3 LaTeX appendix 宏包行为需要按真实输出验证

当前 CUMCM 类文件：

\`templates/latex/cumcm/cumcmthesis/cumcmthesis.cls\`

加载：

\`\\RequirePackage[titletoc,title]{appendix}\`

没有启用 \`page\` 选项。

根据 appendix 宏包文档：

- \`title\` 用于在每个附录标题前增加附录名称；
- \`page\` 才会在 appendices 环境开始处生成独立的附录总标题；
- \`appendices\` 环境可以替代单独的 \`\\appendix\` 命令。

参考：<https://tug.org/docs/latex/appendix/appendix.pdf>。

这解释了当前模板为什么只有 A、B 等独立附录节，而没有统一的“附录”总标题。

**实施时不得仅凭宏包选项推断 PDF 最终外观。** 必须对“附录总标题 + 二级附录标题”方案进行真实 LaTeX 编译，检查是否出现重复“附录”、错误编号、标题级别错位或目录异常。默认优先复用现有 class、宏包和 \`appendices\` 环境，不轻易修改官方 class 或全局宏包。

### 1.4 论文审计存在附录边界识别不一致

当前：

\`scripts/audit_paper_prose.py\`

函数 \`_main_text_before_appendix\` 只通过 \`\\appendix\` 字符串截断正文。

但当前模板实际使用的是：

\`\\begin{appendices} ... \\end{appendices}\`

两者并不相同。于是模块化 LaTeX 被展开后，审计器仍可能把 appendices 环境中的内容留在正文文本范围内。

另外，当前审计器的 \`SECTION_RE\`、\`SUBSECTION_RE\` 主要匹配未带星号的标题命令；如果新模板采用 \`\\section*{附录}\` 与 \`\\subsection*{附录A}\`，就需要为附录结构检查提供对星号标题的明确解析能力。

\`scripts/audit_latex_project.py\` 已负责展开模块化 \`\\input\`/\`\\include\`，并将展开文本交给 \`audit_paper_prose.audit_text\`。实施时应沿用这条真实审计链，不另建一套只检查主文件的审计器。

### 1.5 模板校验器尚未覆盖这两项结构

当前：

\`scripts/validate_template_manifest.py\`

已检查：

- Manifest 声明的模板文件是否存在；
- 主文件固定一级结构和条件槽位；
- Q1/Q2/Q3 维护示例；
- 问题章节标题及优化公式展示示例；
- 模板来源文件 SHA256。

但尚未检查：

- 问题分析二级标题是否按小问编号排列；
- 附录是否只有一个总标题；
- 附录 A/B 是否作为二级标题；
- 附录是否仍然保持条件启用。

需要在现有校验器上补齐这些确定性检查，不另建大型校验系统。

### 1.6 阶段读取能力已经存在，不需要重写读取器

当前：

- \`core/writing_runtime_contract.yaml\` 是 CUMCM 写作阶段读取顺序的 Authority；
- \`core/stage_reading_guide.md\` 是由 \`scripts/generate_indexes.py\` 生成的导航文件；
- \`scripts/read_stage.py\` 支持字符串形式的 YAML selector，例如 \`templates/.../template_manifest.yaml#paper_skeleton\`；
- \`read_stage.py\` 对非字符串阶段条目会记为 unresolved，因此本次新增读取项必须继续使用现有字符串路径/selector，不引入字典式自定义读取条目。

因此，阶段读取问题通过补齐 Runtime 的 source mapping 解决；不得手工编辑 \`stage_reading_guide.md\`，也不得新增另一套读取流程。

### 1.7 现有计划与本次范围的关系

以下计划已存在：

- \`docs/cumcm_question_writing_refinement_plan.md\`
- \`docs/v10183_cumcm_heading_hierarchy_readability_completion_plan.md\`

它们主要讨论各问题模型章节内部的 MODEL / SOLVE / RESULT / VALIDATE 功能标题、三级标题可读性、论证详略和图表落位。

**本计划不重复修改这些既有主题。** 本次仅处理：

1. 问题分析这个前置一级章节中的逐问二级标题；
2. 附录的总标题与 A/B/C 二级标题；
3. 上述结构规则的 Authority、读取、模板、审计和编译闭环。

不得把既有问题模型章节的自适应标题重新锁死。

### 1.8 本次基线健康检查结论

截至编制基线：

| 检查项 | 结果 | 说明 |
|---|---|---|
| 当前 Skill 版本 | 通过 | 当前为 10.23.2 |
| 当前 main commit | 已确认 | 9e029966a691e8858fdea740ca821cdf5e77dce5 |
| 未合并 PR | 无 | 编制时未发现 open PR |
| 版本矩阵 | 通过 | 当前活动版本载体均为 10.23.2 |
| 最新 main 完整 CI | 通过 | 编制前已核对完整工作流记录 |
| 问题分析结构 Authority | 有缺口 | 模板有示例，Manifest 未定义固定标题模式 |
| 附录层级 | 不符合目标 | 当前多个一级 section，没有独立总标题 |
| 阶段读取 | 局部缺口 | 问题分析与附录阶段没有显式读取对应 Manifest 结构 |
| 正文/附录边界 | 有缺口 | 审计器只识别 \`\\appendix\`，未识别当前 \`appendices\` 环境 |
| 附录编译覆盖 | 不充分 | 现有 CUMCM smoke 默认关闭附录，未单独证明激活后的结构可编译 |

健康检查结论仅覆盖本次相关入口和关联链路，不代表对所有 Skill 模块重新完成了全仓库审计。现有 Bootstrap、Router、模型批准、数值执行、结果深化、图表证据和交付主流程没有发现需要随本次修改重构的依据。

---

## 2. 目标结构与必须保持的语义

### 2.1 问题分析：一个实际小问对应一个二级标题

正式结构：

\`\`\`text
二、问题分析
    2.1 问题一的分析
    2.2 问题二的分析
    2.3 问题三的分析
    ...
\`\`\`

LaTeX 结构：

\`\`\`latex
\\section{问题分析}

\\subsection{问题一的分析}
% 问题一的分析正文

\\subsection{问题二的分析}
% 问题二的分析正文
\`\`\`

规则：

1. 标题统一使用“问题X的分析”，X 使用中文题号。
2. 每个实际小问对应且仅对应一个二级标题。
3. 标题顺序严格跟随当前 Problem Contract 的小问顺序。
4. 不得缺少实际小问，不得增加题目不存在的小问，不得重复编号。
5. 不因实际题目只有两问而预留“问题三的分析”等空标题。
6. 不把标题改写成“问题一的数学分析”“问题一求解思路”等其他名称。
7. 二级标题下面仍使用连续自然段完成“对象与条件—真实困难—数学抓手—建模转化—准备建立的结构—跨问关系”的分析链。
8. 不因为标题固定而增加三级标题，不把问题分析写成软件执行流水线。
9. 本规则只约束 CUMCM HSK 模板的“问题分析”章节，不扩展为其他竞赛的全局标题规则。

### 2.2 附录：一个一级总标题，多个二级附录标题

正式结构：

\`\`\`text
附录
    附录A
    附录B
    附录C
    ...
\`\`\`

建议的 LaTeX 目标层级：

\`\`\`latex
\\begin{appendices}

\\section*{附录}

\\subsection*{附录A}
% 附录A的实际材料

\\subsection*{附录B}
% 附录B的实际材料

\\end{appendices}
\`\`\`

规则：

1. “附录”是唯一的一级总标题。
2. “附录A”“附录B”“附录C”依次作为二级标题。
3. 默认标题使用上述精确字面形式，不再将“核心代码与复现说明”“补充推导与图表”分别设置成一级标题。
4. 若确有必要标明附录内容类别，应在对应附录正文开头说明，不另造一个一级附录节；如后续确需在标题中增加描述性后缀，必须先更新 Manifest 规则和对应测试，不允许写作时自由漂移。
5. 附录字母按实际材料数量连续生成，不预留空白附录。
6. 附录仍为条件槽位；没有真实支持材料且官方规则未要求时，保持关闭。
7. 代码、复现说明、补充推导、辅助图表等按真实材料分配，不固定 A/B 必须对应某种材料。
8. 核心模型关系、关键推导、核心证明、重要约束来源、影响主结论的必要论证继续留在正文；不得借新附录结构把核心论证整体外移。

### 2.3 LaTeX 标题命令的选择边界

目标语义层级是：

- 一级：\`section\`；
- 二级：\`subsection\`。

附录的“附录”总标题和“附录A/B”条目建议使用星号形式，避免继承正文 section 编号后产生“9.1 附录A”等不符合要求的编号。

但实施时必须先用当前 CUMCM class 与 appendix 宏包进行编译验证：

- 检查 \`appendices\` 环境与星号标题是否兼容；
- 检查 \`title\` 选项是否给星号标题重复添加“附录”前缀；
- 检查 PDF 中总标题与 A/B 标题的视觉层级；
- 检查引用、书签和目录（若当前项目启用目录）；
- 检查环境结束后正文 section 状态是否恢复。

若当前环境无法无冲突地实现目标层级，先在实施 PR 中比较 \`appendices\` 环境与显式 \`\\appendix\` 的最小实现；不得直接修改 \`cumcmthesis.cls\` 或移除宏包选项来绕过问题。

---

## 3. 单一事实源与职责边界

### 3.1 唯一结构 Authority：Template Manifest

正式结构规则只在：

\`templates/latex/cumcm/hsk/template_manifest.yaml\`

定义。

建议在 \`paper_skeleton.ordered_slots\` 对应的 \`problem_analysis\` 和 \`appendix\` slot 中分别增加结构字段，字段名最终以现有 YAML 风格和校验器实现为准。

问题分析结构至少表达：

- 标题层级为 subsection；
- 标题模式为“问题{中文序号}的分析”；
- 数量来源为当前实际小问；
- 顺序来源为 Problem Contract；
- 每个实际小问一个标题；
- 不允许空标题、缺失标题和额外标题。

附录结构至少表达：

- slot 仍然是 optional / conditionally active；
- 一级总标题为“附录”；
- 二级标题模式为“附录{大写拉丁字母}”；
- 字母按顺序递增；
- 仅为实际存在的附录材料生成标题；
- 附录内容的学术归属仍由 Paper Writing Protocol 控制。

### 3.2 收窄 Template/Writing 职责边界

Manifest 当前 \`forbidden_template_authority\` 中的 \`force_internal_subsection_names\` 过于宽泛，与本次固定问题分析标题的目标冲突。

实施时应明确：

**Template Authority 可以拥有：**

- 固定一级论文骨架；
- 问题分析章节逐问二级标题模式；
- 附录一级总标题和 A/B/C 二级标题层级；
- LaTeX 模板文件编排与确定性渲染。

**Writing Skill 继续拥有：**

- 问题分析正文的数学叙事和段落逻辑；
- 各问题模型建立及求解章节内部的专业标题；
- 模型、求解、结果、验证的自适应标题决策；
- 公式、推导、结果解释、验证边界；
- 附录材料是否具备外置资格及其正文/附录内容分配。

因此，应把原来宽泛的“禁止模板强制指定内部标题”收窄为“禁止模板强制指定各问题模型建立与求解章节内部标题”等精确边界，并把问题分析和附录的固定结构作为显式例外。

**禁止：** 为了实现问题分析固定标题，顺手把各问题模型章节内部标题也变成固定模板。

### 3.3 其他文件只引用，不重复定义

| 文件 | 职责 | 允许的内容 |
|---|---|---|
| Template Manifest | 唯一结构 Authority | 精确标题模式、层级、数量和条件 |
| Paper Writing Protocol | 写作行为说明 | 告知写作者遵循 Manifest；保留分析内容和附录内容规则 |
| LaTeX Template | 结构的实际呈现 | 真实的 section/subsection 命令和示例正文位置 |
| Template README | 使用说明 | 展示结构并解释 Template/Writing 边界，引用 Manifest |
| Writing Runtime | 阶段读取与执行顺序 | 声明问题分析和附录阶段读取 Manifest |
| Stage Reading Guide | 生成导航 | 由 Runtime 自动生成，不拥有规则 |
| Template Validator | 模板结构确定性校验 | 检查 Manifest 与模板文件一致 |
| Paper Prose Audit | 实际论文结构审计 | 检查真实论文是否遵循标题层级 |
| Model Paper Framework | 项目级事实与实际选择 | 仅记录当前项目真实章节选择，不复制通用规则 |

不修改 \`core/writing_reasoning_contract.yaml\` 的模型章节标题 Authority；它继续管理各问题模型章节的专业标题、自适应拆分和三级标题可读性。本次不新增第二份标题语义合同。

---

## 4. 逐文件修改计划

### 4.1 \`templates/latex/cumcm/hsk/template_manifest.yaml\`

**必须修改。**

1. 为 \`problem_analysis\` slot 增加固定逐问二级标题规则。
2. 为 \`appendix\` slot 增加一级/二级标题层级规则。
3. 更新 \`authority_boundary.template_owns\`，显式包含问题分析逐问标题和附录层级。
4. 收窄 \`forbidden_template_authority\` 中过宽的内部标题禁止项，保留问题模型章节内部标题自适应。
5. 保留 \`appendix.required: false\`、\`default_active: false\` 和原 activation 条件。
6. 保留 \`cumcm_question_section.internal_structure: adaptive\`。
7. 保留 \`cumcm_question_section.default_complex_question_headings_role: maintained_example_profile_only\`；该字段仍只管理问题模型章节示例，不应被本次前置标题规则混淆。
8. 不修改外部参考文件路径、来源哈希和 reference provenance。

版本处理：

- \`template_id: hsk_cumcm_v8\` 保持不变。
- 当前 \`schema_version: 1.0.0\` 默认保持不变，因为本次是现有 slot 的向后兼容结构元数据补充；现有校验器明确要求该版本。
- 只有当实施发现 Manifest schema 本身必须新增强制解析语义时，才另行说明 schema 版本升级理由，并同步 validator 与测试；不得为了新增几个可选字段机械升级。

### 4.2 \`templates/latex/cumcm/hsk/sections/02_problem_analysis.tex\`

**必须核查，按需做最小修改。**

当前 Q1/Q2 标题已经正确，不应为制造 diff 而重写。

实施要求：

1. 保留 \`\\section{问题分析}\`。
2. 保留 Q1/Q2 的准确二级标题。
3. 将注释改为清晰的动态扩展说明：实际有几问就生成几个标题，按 Problem Contract 顺序，不预留空标题。
4. Q3+ 只保留注释示例或按实际问题生成，不把示例数量固定成五问。
5. 不在模板中预填任何题目专属正文、模型名称、公式或结果。
6. 不添加无必要的三级标题。

### 4.3 \`templates/latex/cumcm/hsk/appendices/appendices.tex\`

**必须修改。**

将当前多个一级 \`\\section\` 调整为：

- 一个“附录”一级标题；
- “附录A”“附录B”作为二级标题；
- 实际需要几个附录就生成几个，不预留空白项。

默认优先保留现有 \`appendices\` 环境和官方 class，不修改 \`cumcmthesis.cls\` 与全局宏包。建议先试验 §2.3 中的星号标题形式，再根据实际编译结果确定最小可行写法。

现有“核心代码与复现说明”“补充推导与图表”只作为材料内容示例，不再作为多个一级附录节。附录 A/B 的具体内容分配必须由实际材料决定。

### 4.4 \`templates/latex/cumcm/hsk/README.md\`

**必须做小范围同步。**

1. §1 的整体框架保留“问题一的分析”“问题二的分析”示例，并明确这是固定的逐问二级标题。
2. §3 的 Template/Writing 边界明确列出两个例外：
   - 问题分析逐问二级标题由 Template Manifest 固定；
   - 附录总标题和 A/B/C 层级由 Template Manifest 固定。
3. 明确各问题模型建立与求解内部标题仍由 Writing Skill 自适应决定。
4. 明确附录仍是条件章节，默认关闭。
5. 不复制 Manifest 的完整 YAML 字段，不在 README 再定义一套标题模式。

### 4.5 \`modules/05_writing/paper_writing_protocol.md\`

**必须做局部同步。**

§6.2“问题分析”：

- 增加一句明确规则：逐问二级标题遵循 CUMCM Template Manifest 的“问题X的分析”模式；
- 标题数量和顺序按当前实际小问；
- 正文内容仍服从现有分析链，不因固定标题而变成模板化段落。

§15“模型评价、逐问结论与附录”：

- 保留现有核心论证不得移入附录的内容规则；
- 增加附录标题层级服从 Template Manifest 的简短引用；
- 继续强调附录条件启用，不得为了完整性生成空附录。

不得将完整标题规则再抄一遍到 Protocol；不得修改各问题模型章节的标题自适应规则。

### 4.6 \`core/writing_runtime_contract.yaml\`

**必须做局部同步。**

在当前 \`problem_analysis\` 阶段的 \`read_now\` 中增加：

\`templates/latex/cumcm/hsk/template_manifest.yaml#paper_skeleton\`

在当前 \`evaluation_references_conclusion_appendix\` 阶段的 \`read_now\` 中增加同一结构来源，确保附录启用与标题组织时能够读取当前结构 Authority。

约束：

- 使用现有字符串路径/selector；
- 不新增 dict 形式的阶段读取项；
- 不改变阶段顺序、gate、pause、写作产物或条件激活逻辑；
- 不新增 Project State 字段；
- 不将模板结构读取变成新的审批或交付门禁。

### 4.7 \`core/stage_reading_guide.md\`

**禁止手工修改。**

该文件由 \`scripts/generate_indexes.py\` 从 Runtime 派生。实施后应检查生成结果是否在：

- \`problem_analysis\`
- \`evaluation_references_conclusion_appendix\`

两个阶段显示新增的 Manifest selector。

如果生成结果没有更新，检查 generator 的既有读取逻辑和生成契约；不得直接编辑生成文件伪造读取完成。

### 4.8 \`scripts/validate_template_manifest.py\`

**必须扩展现有校验器。**

增加确定性检查：

**问题分析模板检查：**

- Manifest 存在问题分析标题策略；
- 标题层级为 subsection；
- 标题模式为“问题{中文序号}的分析”；
- 当前模板示例至少包含 Q1/Q2 两个正确标题；
- 标题顺序正确；
- 不存在重复的活动标题；
- 模板注释中的扩展示例不能被误判为活动标题。

**附录模板检查：**

- Manifest 中 appendix 仍为 conditional；
- \`required\` 和 \`default_active\` 仍为 false；
- 附录模板存在唯一一级总标题“附录”；
- 附录 A/B 为二级标题；
- A/B 顺序连续；
- 不再出现将附录 A/B 分别作为一级标题的旧结构；
- \`hsk_main.tex\` 中附录输入仍默认关闭。

校验器只检查模板文件和 Manifest 的确定性一致性，不负责判断某个真实项目是否应该启用附录。

### 4.9 \`scripts/audit_paper_prose.py\`

**必须扩展现有论文审计逻辑。**

#### A. 附录边界识别

将 \`_main_text_before_appendix\` 的边界识别扩展为兼容：

- \`\\appendix\`
- \`\\begin{appendices}\`

取正文中最先出现的有效附录起点。识别前应排除注释，不能因为注释示例中的命令提前截断正文。

#### B. 问题分析标题审计

复用现有 \`QUESTION_SECTION_RE\` 识别当前论文的问题章节，不新增独立题号解析体系。

检查：

- 问题分析标题与实际问题章节一一对应；
- 标题按问题顺序排列；
- 标题使用“问题X的分析”；
- 不缺失、不重复、不多出无对应小问的标题。

实际问题数必须从当前论文已有的问题章节结构恢复；模板静态校验不负责猜测用户题目有几问。

#### C. 附录层级审计

仅当论文实际启用附录时检查：

- 是否有且仅有一个一级“附录”总标题；
- “附录A”“附录B”是否为二级标题；
- 字母是否连续、顺序正确；
- 是否存在把 A/B 错放为多个一级 section 的情况；
- 是否存在空附录或只有标题没有材料的情况。

附录标题解析必须能处理星号形式的 section/subsection 命令；尽量采用附录专用解析，不要为了本次功能无差别改变所有现有标题解析行为。

#### D. Finding 严重度

- canonical template 与 Manifest 不一致：由模板 validator 报错。
- 实际论文偏离默认标题结构：沿用现有 \`Finding\` 和 \`review_required\` 体系，不新增独立严重度。
- 不因为某个附录未启用而报错。
- 不把结构偏离自动判成数学模型错误，不修改论文正文，不自动重命名标题。

### 4.10 \`scripts/audit_latex_project.py\`

**默认只核查，不预设修改。**

该脚本已展开模块化 LaTeX include graph，再调用 \`audit_paper_prose.audit_text\`。实施时应通过集成测试确认新结构审计确实作用于展开后的问题分析和附录文件。

只有测试证明当前调用链遗漏新 finding 时，才做最小必要修改；不得另建平行 LaTeX 审计入口。

### 4.11 测试文件

建议新增：

\`tests/test_v10233_cumcm_problem_analysis_appendix_headings.py\`

并按实际影响扩展现有测试：

- \`tests/test_v800_template_authority.py\`
- \`tests/test_v800_writing_runtime.py\`
- \`tests/test_read_stage.py\`
- \`tests/test_stage_reading_guide_lifecycle.py\`
- \`tests/test_p7_conditional_analysis_appendix.py\`
- \`tests/test_v745_prose_audit.py\`
- \`tests/test_v872_template_assembly_consistency.py\`
- \`tests/test_v1000_release_version_matrix.py\`

测试只覆盖实际变化，不重复创建现有测试已经证明的行为。

### 4.12 \`.github/workflows/ci.yml\`

**需要评估并扩展现有 CUMCM LaTeX smoke。**

当前 \`latex-smoke\` 的 CUMCM 模板编译默认附录关闭，因此不能证明激活附录后的层级能够正常编译。

建议在现有 \`latex-smoke\` 工作流中增加一个 CUMCM appendix-active smoke：

1. 在临时副本或临时主文件中启用附录输入；
2. 编译包含“附录”“附录A”“附录B”的结构；
3. 检查编译日志中的错误、未定义引用和重复标题问题；
4. 确认临时文件不会污染仓库 checkout；
5. 不新增独立 CI workflow。

如果现有 LaTeX smoke 已能通过更小的 fixture 覆盖同一行为，可以复用，不重复建立第二条编译链。

---

## 5. 版本与生成文件同步

### 5.1 后续实现版本

当前基线为 10.23.2。若实施时仍以 10.23.2 为当前 main 版本，候选发布版本为：

\`10.23.3\`（patch）。

理由：

- 修改实际写作行为；
- 修改模板结构；
- 补充确定性校验与论文审计；
- 保持已有项目目录、CLI、Project State 和数值接口兼容；
- 不新增跨模块能力或新的工作流。

本计划文件自身属于 docs，不升级 Skill 版本。

### 5.2 版本同步载体

后续若按 10.23.3 发布，至少核对并按版本矩阵同步：

- \`core/bootstrap.yaml\`
- \`.codex-plugin/plugin.json\`
- \`core/workflow_router.yaml\`
- \`core/module_manifest.yaml\`
- \`core/output_contract.yaml\`
- \`core/writing_runtime_contract.yaml\`
- \`config/prose_audit_patterns.yaml\`
- \`core/hsk_core_policy.md\`
- 根目录 \`SKILL.md\`
- \`skills/mathmodel-skill/SKILL.md\`
- \`README.md\`
- \`CHANGELOG.md\`
- \`tests/test_v1000_release_version_matrix.py\`

以上是当前版本矩阵中已声明的 Skill 版本载体。实施时必须重新读取测试，不能照抄本文而漏掉届时新增的载体。

### 5.3 独立 Schema 版本

不因 Skill patch 而盲目升级：

- Template Manifest 的 \`schema_version\`
- Writing Reasoning 的 \`schema_version\`
- Writing Runtime 之外的项目状态、工作簿、执行回执等独立协议版本。

只有对应 schema 本身发生不兼容或有明确版本治理要求时才升级，并提供迁移说明。

### 5.4 生成文件

以下文件由 GitHub \`refresh-generated\` 更新，不得人工提交伪造版本：

- \`MANIFEST.sha256\`
- \`SKILL_FILE_INDEX.md\`
- \`TEMPLATE_INDEX.md\`
- \`core/stage_reading_guide.md\`
- 其他由 \`scripts/generate_indexes.py\` 管理的受管文件。

---

## 6. 分阶段实施顺序

### Phase 0：实施前基线复核

实施开始前必须重新：

1. 读取最新 main 的 \`core/bootstrap.yaml\`；
2. 读取最新 main 的 \`SKILL_CHANGE_GOVERNANCE.md\`；
3. 确认当前 Skill 版本、main commit、open PR 和相关分支；
4. 检查本计划涉及的 Authority 与文件是否已经被其他 PR 修改；
5. 重新确认 Manifest、模板、Runtime、审计器和 CI 的现状；
6. 形成符合治理规范的修改简报；
7. 创建独立实现分支，不复用本计划 docs 分支。

若有 PR 同时修改 Template Manifest、Writing Runtime、模板文件或审计器，先判断串行顺序；不能同时向同一权威文件强行叠加修改。

**完成条件：** 当前基线和修改范围明确，没有未处理的源文件冲突。

### Phase 1：先确立结构 Authority，再修改模板

顺序：

1. 修改 Template Manifest 中问题分析和 appendix slot 的结构策略；
2. 修正 Template/Writing authority boundary；
3. 修改 \`02_problem_analysis.tex\` 的注释/动态扩展说明；
4. 重构 \`appendices.tex\` 的标题层级；
5. 同步模板 README。

**完成条件：**

- Manifest 是唯一规则来源；
- 问题分析标题固定；
- 附录总标题和 A/B 二级标题明确；
- 模型章节内部标题继续自适应；
- 附录仍然默认关闭。

### Phase 2：同步写作协议与阶段读取

顺序：

1. 修改 Protocol §6.2；
2. 修改 Protocol §15；
3. 在 Writing Runtime 的问题分析阶段加入 Manifest selector；
4. 在评价/引用/附录阶段加入 Manifest selector；
5. 通过现有 \`read_stage.py\` 验证两个阶段能读取完整的 \`paper_skeleton\`；
6. 运行现有生成逻辑，核对 \`stage_reading_guide.md\` 自动反映变化。

**完成条件：**

- 问题分析阶段能够取得固定标题 Authority；
- 附录阶段能够取得条件启用与标题层级 Authority；
- selector 解析成功，无 unresolved stage entry；
- 未新增读取器、阶段或 gate。

### Phase 3：补齐模板校验和真实论文审计

顺序：

1. 扩展 \`validate_template_manifest.py\` 的问题分析模板检查；
2. 扩展该校验器的附录层级和条件性检查；
3. 修复 \`audit_paper_prose.py\` 的附录边界识别；
4. 增加实际论文的问题分析标题一一对应检查；
5. 增加实际论文的附录总标题与 A/B 层级检查；
6. 通过 \`audit_latex_project.py\` 对模块化 LaTeX 进行集成验证；
7. 检查现有 Finding 级别与历史项目兼容性。

**完成条件：** 模板自身错误能够被确定性发现，实际论文偏离结构能够被现有审计流程发现，附录正文不会再被错误混入正文范围。

### Phase 4：补充回归与附录激活编译

执行 §7 的测试矩阵。

特别注意：

- 默认附录关闭的 CUMCM 主模板仍然正常编译；
- 附录激活后也必须正常编译；
- 不出现重复“附录”前缀；
- PDF 标题视觉层级与要求一致；
- 其他竞赛模板没有被本次修改影响。

**完成条件：** Python 专项测试、阶段读取测试、模板检查和 CUMCM 附录激活编译均通过。

### Phase 5：版本、生成和正式 PR 验收

1. 根据实施时最新版本矩阵同步 Skill 版本；
2. 更新 Changelog；
3. 只提交源文件；
4. 推送实现分支；
5. 等待 GitHub \`refresh-generated\`；
6. 审查 bot 生成提交和最终 PR head；
7. Draft 阶段先运行受影响专项检查；
8. PR 冻结为 ready 后，在最终 head 运行正式完整验证；
9. 所有适用门通过后才允许合并；
10. 合并后复核 main CI。

**完成条件：** 最终 PR head、实际 checkout commit、生成提交、GitHub Actions 结果和合并后 main 状态均有真实记录。

---

## 7. 验收测试矩阵

### 7.1 问题分析标题

| ID | 输入场景 | 预期结果 |
|---|---|---|
| PA-01 | 一道小问 | 只有“问题一的分析” |
| PA-02 | 两道小问 | 依次出现“问题一的分析”“问题二的分析” |
| PA-03 | 三道小问 | 依次出现一、二、三 |
| PA-04 | 五道小问 | 依次出现一至五 |
| PA-05 | 缺少问题二标题 | 审计能够发现 |
| PA-06 | 问题二、问题一顺序颠倒 | 审计能够发现 |
| PA-07 | 多出题目不存在的问题四标题 | 审计能够发现 |
| PA-08 | 问题二标题重复 | 审计能够发现 |
| PA-09 | 标题被改成“问题一求解思路” | 审计能够发现 |
| PA-10 | 问题分析正文含有普通自然段 | 不误报 |
| PA-11 | 各问题模型章节采用专业自适应标题 | 不受本次固定标题规则影响 |
| PA-12 | 注释中出现 Q3/Q4 模板示例 | 不把注释当作活动标题 |

### 7.2 附录结构

| ID | 输入场景 | 预期结果 |
|---|---|---|
| AP-01 | 附录未启用 | 不产生空标题，也不报缺少附录 |
| AP-02 | 一个附录 | “附录”一级标题 + “附录A”二级标题 |
| AP-03 | 两个附录 | “附录”一级标题 + A/B 两个二级标题 |
| AP-04 | 三个附录 | A/B/C 连续递增 |
| AP-05 | 缺少总标题 | 审计能够发现 |
| AP-06 | A/B 分别作为一级 section | 审计能够发现 |
| AP-07 | 附录A/B 作为三级标题 | 审计能够发现 |
| AP-08 | 附录字母跳号或倒序 | 审计能够发现 |
| AP-09 | 存在空附录标题 | 审计能够发现 |
| AP-10 | 只有附录材料，没有核心证明外移 | 通过结构检查 |
| AP-11 | 通过 \`appendices\` 环境启用 | 正确识别正文/附录边界 |
| AP-12 | 旧式 \`\\appendix\` 项目 | 边界识别保持兼容；结构偏离按现有 Finding 规则提示 |

### 7.3 阶段读取与语义一致性

| ID | 测试 | 预期结果 |
|---|---|---|
| RD-01 | \`problem_analysis\` 读取 | Manifest 的 \`paper_skeleton\` 被选中 |
| RD-02 | \`evaluation_references_conclusion_appendix\` 读取 | Manifest 的 \`paper_skeleton\` 被选中 |
| RD-03 | YAML selector | 正确解析，无 unresolved |
| RD-04 | Stage Reading Guide 生成 | 两阶段均出现新来源 |
| RD-05 | README / Protocol / Manifest | 无互相冲突的标题规定 |
| RD-06 | Template/Writing boundary | 固定问题分析标题不再与禁止项冲突 |
| RD-07 | 各问题模型章节 | 仍然保留自适应标题规则 |
| RD-08 | 附录条件槽 | required/default_active 仍为 false |

### 7.4 编译与工程兼容

| ID | 测试 | 预期结果 |
|---|---|---|
| TX-01 | 默认 CUMCM 模板 | 附录关闭时正常编译 |
| TX-02 | CUMCM 附录激活 smoke | A/B 层级正常编译 |
| TX-03 | PDF 标题显示 | 不重复“附录”前缀 |
| TX-04 | 附录环境结束 | 后续结构/编号不受污染 |
| TX-05 | MCM/ICM 模板 | 无变化、编译通过 |
| TX-06 | 电工杯模板 | 无变化、编译通过 |
| TX-07 | Manifest validator | 对正确模板通过，对错误层级失败 |
| TX-08 | 模块化 LaTeX audit | 能从 include graph 取得问题分析和附录内容 |

### 7.5 机器检查与人工检查边界

**机器适合检查：**

- 标题命令层级；
- 标题文本模式；
- 问题编号是否连续；
- 标题数量、顺序、重复和缺失；
- 附录总标题是否唯一；
- A/B/C 是否为二级标题；
- 条件槽是否关闭；
- Manifest 与模板文件是否同步；
- LaTeX 是否能够编译；
- 正文/附录边界是否正确识别。

**人工仍需检查：**

- 问题分析正文是否真正对应题意；
- 每问之间是否存在真实继承关系；
- 附录内容是否确实适合外置；
- 核心证明、关键推导和主要约束是否留在正文；
- 附录内容是否有正文引用及实际复现价值。

禁止用标题检查器替代数学语义审查。

---

## 8. 本次附带的 Skill 健康检查清单

本次不重构全流程，只把已发现的风险纳入后续实现验收。

### 8.1 语义漂移

- [ ] Manifest 中问题分析标题与实际 TeX 示例一致。
- [ ] Manifest 中附录层级与实际 TeX 示例一致。
- [ ] README 不再把问题分析固定标题与模型章节自适应标题混为一谈。
- [ ] Protocol 只说明执行要求，不复制第二份标题 Authority。
- [ ] Writing Runtime 指向当前 Manifest。
- [ ] Stage Reading Guide 由 Runtime 自动生成且无失效 selector。
- [ ] 原有问题模型章节标题规则不受影响。

### 8.2 版本同步

- [ ] 按最新版本矩阵同步 Skill 版本载体。
- [ ] 不全仓库盲目替换独立 Schema 版本。
- [ ] Template Manifest schema_version 按实际兼容性决定，不机械升级。
- [ ] Changelog 描述真实行为变化。
- [ ] 版本矩阵测试通过。
- [ ] MANIFEST 与索引由生成工作流更新。

### 8.3 读取失效/失败

- [ ] 问题分析阶段可以读取 Manifest 的 \`paper_skeleton\`。
- [ ] 附录阶段可以读取 Manifest 的 \`paper_skeleton\`。
- [ ] 所有新增 read_now 条目均为现有读取器支持的字符串路径/selector。
- [ ] 不新增 dict 型 read_now 条目。
- [ ] 不手工修改生成的 Stage Reading Guide。
- [ ] 通过 \`read_stage.py\` 的实际选择结果验证来源，不仅检查文本中存在路径。

### 8.4 模板、审计和编译

- [ ] 模板校验器能够识别错误结构。
- [ ] 正文审计器能够识别 \`appendices\` 环境。
- [ ] 附录内容不再错误进入正文范围检查。
- [ ] 星号标题能够被附录结构审计解析。
- [ ] CUMCM 附录激活后实际编译。
- [ ] 其他竞赛模板不受影响。

### 8.5 整体流程的范围判断

当前检查没有发现需要因本次标题调整而改动以下流程的依据：

- Bootstrap 和 Workflow Router 的总体路由；
- Problem Contract、模型挑战与人工批准；
- 预处理、主求解、结果深化与用户本地 full-fidelity 执行；
- Figure Contract、图表证据和图表生成；
- Project State、stale 传播、结果验收和正式交付 gate。

如果实施时出现这些模块的真实缺陷，应先记录为独立问题并停止扩围；不得把无关重构混入本次单主题 PR。

---

## 9. 兼容、迁移与回滚

### 9.1 兼容范围

| 对象 | 处理 |
|---|---|
| 新建 CUMCM HSK 论文 | 按新标题结构生成 |
| 正在写作的 CUMCM 论文 | 用户继续编辑或进入相应写作阶段时按新规范处理；不自动覆盖 |
| 历史 LaTeX 论文 | 不批量重排，不自动重命名 |
| 附录未启用的论文 | 不受影响 |
| MCM/ICM、电工杯论文 | 不受影响 |
| 问题模型章节内部标题 | 保持自适应 |
| 已验收数值结果/模型批准 | 不失效、不重跑 |

### 9.2 历史项目处理

旧论文可能采用多个一级附录节。实施后，实际论文审计可以按现有 \`review_required\` 体系提示其偏离当前默认结构，但不得自动改写旧文件。

用户明确要求继续维护或重新提交旧论文时，再根据当届官方模板和当前项目需要决定是否调整。不得把新规则追溯性地改成所有历史项目的自动迁移任务。

### 9.3 回滚

如果新模板或审计逻辑产生误判：

1. 通过单主题 revert PR 回滚相关源文件；
2. 由 GitHub \`refresh-generated\` 恢复受管文件；
3. 在最新 PR head 重新执行适用的 GitHub Actions；
4. 合并后复核 main；
5. 不回滚或修改用户项目的工作簿、模型批准、数值结果和项目状态。

如果仅 LaTeX 附录激活 smoke 失败，先修正模板实现或测试 fixture；不得删除有效测试来获得绿色 CI。

---

## 10. PR 与发布纪律

### 10.1 本计划 PR

本次只新增：

\`docs/cumcm_problem_analysis_appendix_heading_hierarchy_plan.md\`

允许 GitHub 自动生成受管索引/MANIFEST 变化；不修改任何活动 Authority 或执行文件。

本计划 PR 合并只表示实施蓝图被保存，不代表标题规范已经生效。

### 10.2 后续实现 PR

后续实施必须使用新的实现分支和单主题 PR，不应把本计划 docs 分支继续扩展为行为修改分支。

实施 PR 描述至少包括：

- 修改背景和直接目标；
- 当前版本、目标版本和变更等级；
- 唯一结构 Authority；
- 逐文件修改及未修改关联文件的原因；
- 模板与历史项目兼容；
- 测试矩阵；
- 生成文件状态；
- 回滚方式；
- 最终 PR head SHA；
- 实际 checkout commit；
- GitHub Actions workflow run 与结果；
- 合并后 main 状态。

### 10.3 GitHub 验收

严格遵循当前 \`SKILL_CHANGE_GOVERNANCE.md\`：

- Draft 阶段优先受影响专项测试和基础检查；
- ready PR 冻结后执行正式完整验证；
- Windows Python 3.10 与 Python 3.14 完整回归；
- Static contract lint；
- Generated file contract；
- MATLAB native contract；
- LaTeX templates；
- Production LaTeX attestation；
- 适用的 Optimization baseline（若不适用，应说明本次未改变优化执行语义的原因）；
- 任何源码或 bot 生成提交导致 head 变化，都必须针对新最终 head 重新核验；
- 只有正式验证通过后才允许合并；
- 合并后复核 main Actions。

仓库维护验收以 GitHub 证据为准，不以本地测试、手工生成索引或聊天中的“应该通过”代替。

---

## 11. 停止条件

出现以下任一情况时，实施者应暂停并先报告，不得擅自扩大范围：

1. 最新 main 已改变 Manifest 的结构 Authority，导致本计划字段位置不再适用。
2. 存在其他未合并 PR 同时修改 Manifest、Writing Runtime、CUMCM 模板或论文审计器。
3. 当前 \`appendices\` 环境与目标星号标题层级无法兼容，且最小替代实现需要修改官方 class 或全局宏包。
4. 实际论文题号无法从现有 Problem Contract/问题章节结构可靠恢复。
5. 新的标题审计会误伤非 CUMCM 模板或无附录项目。
6. 需要新增 Project State、审批流程、模型语义字段或数值验收规则才能实现本次需求。
7. 需要修改 03A/03B、工作簿、Figure Contract 或其他数值事实源。
8. 现有正式 CI 失败且原因尚未定位。

停止后先提供最小复现、受影响 Authority 和可选修正路径；用户未确认前不将扩围内容并入本次 PR。

---

## 12. 后续实施指令

后续新聊天或 Codex 接手时，按以下指令执行：

> 目标仓库：\`Vexushi1/mathmodel-skill\`。  
> 先从最新 \`main\` 读取 \`core/bootstrap.yaml\`、\`SKILL_CHANGE_GOVERNANCE.md\)，确认版本、main SHA、未合并 PR 和本计划文件。随后完整读取 \`docs/cumcm_problem_analysis_appendix_heading_hierarchy_plan.md\`，按 Phase 0—5 实施。
>
> 本次行为目标仅为：  
> 1. CUMCM “问题分析”一级章节下，每个实际小问对应一个固定二级标题“问题X的分析”；  
> 2. 附录只有一个一级总标题“附录”，其下为“附录A”“附录B”……二级标题；  
> 3. 附录继续条件启用，默认关闭；  
> 4. 各问题模型建立与求解章节内部标题继续自适应。
>
> Template Manifest 是唯一结构 Authority。Protocol 只说明写作行为；Runtime 声明阶段读取；LaTeX 文件落实结构；模板 validator 检查模板；paper audit 检查实际论文；Stage Reading Guide 由生成器更新。不得重复定义规则，不得手改生成文件。
>
> 必须修复 \`audit_paper_prose.py\` 对 \`\\begin{appendices}\` 的正文边界识别，并测试星号标题；必须确认模块化 LaTeX audit 经过 include 展开后能看到问题分析和附录。必须在现有 CUMCM LaTeX smoke 中覆盖附录激活编译。
>
> 不修改数值求解、模型批准、工作簿、Project State、Figure Evidence、03A/03B 或其他竞赛模板。不得批量重写历史论文。任何超出本计划范围的发现先报告，不擅自扩大。
>
> 开发阶段优先 GitHub targeted checks；冻结最终 PR head 后按仓库治理完成正式 GitHub Actions 全量验收，合并后复核 main。没有真实远端证据时不得声称完成。

---

## 13. 完成定义

本计划对应的后续实现只有同时满足以下条件，才能称为完成：

- [ ] 问题分析标题正式进入 Manifest，并与模板、Protocol 和 README 一致。
- [ ] 任意实际小问数量均能正确生成对应二级标题。
- [ ] 附录只有一个总标题，A/B/C 等为二级标题。
- [ ] 附录仍然条件启用，默认关闭。
- [ ] 各问题模型章节内部标题仍然自适应。
- [ ] 问题分析阶段和附录阶段能读取 Manifest。
- [ ] Stage Reading Guide 由生成流程正确更新。
- [ ] 模板 validator 能识别结构漂移。
- [ ] Paper audit 能正确识别正文/附录边界及标题层级。
- [ ] 模块化 LaTeX 审计覆盖展开后的源文件。
- [ ] 默认 CUMCM 模板和附录激活模板均编译通过。
- [ ] 版本矩阵和生成文件合同通过。
- [ ] 正式 PR head 的 GitHub Actions 全部适用检查通过。
- [ ] 合并后 main CI 通过。
- [ ] 没有引入无关的模型、数值、状态或工作流变更。

**当前状态：仅完成计划文件。** 本文不表示 Manifest、模板、Protocol、Runtime、validator、audit 或 CI 已经修改，也不表示 10.23.3 已发布。

---

## 14. 本次核查的主要仓库来源

- \`AGENTS.md\`
- \`PROJECT_INSTRUCTIONS.md\`
- \`SKILL_CHANGE_GOVERNANCE.md\`
- \`core/bootstrap.yaml\`
- \`templates/latex/cumcm/hsk/template_manifest.yaml\`
- \`templates/latex/cumcm/hsk/hsk_main.tex\`
- \`templates/latex/cumcm/hsk/sections/02_problem_analysis.tex\`
- \`templates/latex/cumcm/hsk/appendices/appendices.tex\`
- \`templates/latex/cumcm/hsk/README.md\`
- \`templates/latex/cumcm/hsk/config/preamble.tex\`
- \`templates/latex/cumcm/cumcmthesis/cumcmthesis.cls\`
- \`modules/05_writing/paper_writing_protocol.md\`
- \`core/writing_runtime_contract.yaml\`
- \`core/stage_reading_guide.md\`（生成文件，只读核对）
- \`scripts/read_stage.py\`
- \`scripts/generate_indexes.py\`
- \`scripts/validate_template_manifest.py\`
- \`scripts/audit_paper_prose.py\`
- \`scripts/audit_latex_project.py\`
- \`tests/test_v10183_cumcm_writing_structure.py\`
- \`tests/test_p7_conditional_analysis_appendix.py\`
- \`tests/test_v800_writing_runtime.py\`
- \`tests/test_v1000_release_version_matrix.py\`
- \`.github/workflows/ci.yml\`
- \`docs/cumcm_question_writing_refinement_plan.md\`
- \`docs/v10183_cumcm_heading_hierarchy_readability_completion_plan.md\`

外部宏包行为参考：

- Appendix package manual: <https://tug.org/docs/latex/appendix/appendix.pdf>
- CTAN Appendix package: <https://ctan.org/pkg/appendix>

---

**文档用途：** 本文件是后续实施计划，不是运行时合同。只有未来实现 PR 中通过仓库治理、正式测试并合并到 main 的 Authority 修改，才会使新标题规范正式生效。
