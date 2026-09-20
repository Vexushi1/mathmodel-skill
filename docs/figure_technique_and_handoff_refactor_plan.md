# 绘图衔接修复与绘图技巧改进详细计划

> 仓库：`Vexushi1/mathmodel-skill`  
> 计划日期：2026-09-20；计划版本：1.6
> 编制基线：`main@d6f24892dec61d01a6a75811d01e0c32e04da438`  
> 编制时 Skill：9.4.0；计划创建提交未升级版本。当前已合入 9.5.0，F3 实施目标：9.5.1 patch；补足现有绘图技巧参考。
> 状态：`implementing`；P0、F1 与 F2 已合并，F3 正在实施，具体验证与剩余阶段见第 12 节。
> 文件角色：本轮绘图改造的维护计划、实施顺序和进度依据，不是新的 Figure、Workbook、Runtime 或 Writing Authority。

## 0. 后续如何使用本计划

后续绘图维护从本文件接续：先读最新 `main` 的 `core/bootstrap.yaml`、`SKILL_CHANGE_GOVERNANCE.md`、本计划的进度表和当前阶段相关源文件，再核对实际分支、未合并 PR 与基线。每个实施 PR 关联本文件的任务编号，报告修改范围、验证结果、兼容处理和剩余工作。

**顺序固定为：先解决 P0 衔接问题，再调整绘图决策和样式接口，最后完善技巧样例与文档闭环。** P0 未完成时，不先批量替换颜色或重写图型模板。计划创建轮仅上传文档；用户已于 2026-09-20 明确同意开始推进，后续按本计划实施并更新进度。

本计划是这轮维护的执行依据，不要求普通赛题绘图任务预读整篇计划。实际绘图政策仍写在现有 Authority；模板提供实现方式，Pack 只摘要或引用。发现范围变化时，先在本计划记录证据、依赖和调整原因，再按更新后的范围实施；不能以“顺便优化”绕开计划，也不因本计划要求重复请求已经获得的授权。

## 1. 计划创建简报与实施边界

| 项目 | 本次计划提交 | 后续实施要求 |
|---|---|---|
| 修改主题 | 绘图衔接修复与按图设计的详细实施计划 | 数据交接一致、图表美观、代码便于用户在 MATLAB 调整 |
| 当前 / 目标版本 | 9.4.0 / 9.4.0 | 每个实现 PR 根据实际行为、API 与兼容性裁决，不预定版本号 |
| 变更等级 | docs / planning-only | 修错、能力新增、破坏兼容分别如实标级，不能把行为变化当 docs |
| 直接产物 | 本文件；原生成器产生的索引与 Manifest 差异 | 按阶段的最小规则、模板、检查和文档修改 |
| 明确不做 | 不改活动契约、代码、测试、CI、版本、用户项目 | 不重做模型、重跑求解或分析，不扩建通用绘图库或状态系统 |
| 事实源 | 本次用户要求、当前 main 的治理及绘图/工作簿/输出契约、已读取实现 | 实施前复核最新事实；外部 Skill 仅为技巧参考 |
| 预计修改文件 | 本文件、`SKILL_FILE_INDEX.md`、`MANIFEST.sha256`；生成结果以实际差异为准 | 第 4–9 节列出必查影响面，只修改真正受影响的位置 |
| 禁止触碰 | 除计划和自动生成差异外的活动文件、用户数据和成果 | 未涉及的模型、算法参数、结果数值、论文内容和项目状态接口 |
| 兼容 / 迁移 | 本次没有接口变化或项目迁移 | 旧工作簿与显式旧 profile 调用有清楚的兼容边界，不批量回写旧项目 |
| 验证 | 文档事实与链接、diff、lint、全量 Python 单元测试、生成文件检查 | MATLAB 仅静态检查；图形由用户本机运行、人工检查调整 |
| 回滚 | revert 计划 PR，按原生成器刷新索引 | 按阶段回滚，契约及消费者成组恢复，不回写用户工作簿 |

编制时已核对：默认分支为 `main`，最新 SHA 如页首，开放 PR 为 0；远端尚有历史分支，不把它们直接当作已合并实现或本次工作分支。实施时必须重新检查。

## 2. 用户要求与不可偏离的设计边界

### 2.1 配色没有默认答案

- **不设仓库默认配色。** 不把 `competition_high_contrast` 换成 `journal_balanced`、Nature、SCI 或其他新的隐式默认；也不通过隐藏分支退回 MATLAB 的默认颜色循环。
- SCI、Nature 风格可作为候选参考。这里指从科研图中借鉴色彩关系与排版方法，不宣称存在统一的“SCI 官方配色”或所有 Nature 图共同遵循的一套色值。
- 先按数据语义、对象数量、图幅、重点和跨图一致性选择颜色，再在当前脚本显式配置。类别色用于类别；顺序色用于有序大小；发散色用于具有真实中心或基准的正负偏离。不能将连续量随意涂成类别色。
- 同一论文中同一对象尽量保持颜色一致；不同图型可以采用不同合适方案。没有证据支持的重点不靠亮色制造；平等比较对象保持相近视觉权重。
- 美观包括适当对比、留白、线点比例、清楚的标签与图例，不等于所有图降饱和、全部灰色背景加一个亮点或强制某个期刊模板。

### 2.2 静态检查与人工调图分工

Agent 检查 MATLAB 代码结构、文件与函数接口、字段引用、尺寸/索引使用及数据边界；可运行仓库自身的 Python lint 和单元测试。**不运行用户项目的求解、分析或 MATLAB 绘图，不安装 MATLAB，不用其他语言重画来声称 MATLAB 已验证。**

图窗显示、标签拥挤、最终字号、图例位置、颜色观感和导出效果由用户在本机 MATLAB 中查看、调整。无需 Agent 截图、读图打分、AI 视觉评审或“渲染—检查—反复修图”流程，也不要求用户上传截图才交付代码。

静态检查只能报告“已检查范围内未发现问题”，不能保证 MATLAB 运行绝对无错；最终报告分别列出静态检查结果、未运行事项和用户人工验收状态。代码静态交付不冒充 `approved_for_paper`，也不自动回填图形已通过人工验收。

### 2.3 美观必须服务真实证据

1. 不改变 accepted workbook 数值、指标方向、样本集合、比较条件或模型参数来让图更好看。
2. 不为绘图重做敏感性、回归、PCA、误差估计或模型求解；新增证据需求回到已有工作流判断，本轮模板不得自行补算。
3. 没有实际区间就不画置信带，没有真实配对就不画配对连线，没有可靠样本支持就不画看似精确的密度。
4. 清楚的折线、点图、条形图可以承担核心论证；不因“基础图”身份降低质量判断，不为多样性配额制造复杂图或重复面板。
5. 保留每张图对应结论、数据来源、caption 和正文用途的证据链。正式图沿用无整体 `title/sgtitle` 的当前政策，图名由论文 caption 承担；必要的面板编号、局部标签、阈值和单位照常保留。

## 3. 三个外部 Skill：吸收什么，如何落地

本节记录已通读资料的借鉴方向，不执行它们的自动化步骤，也不整体复制代码、默认规则或许可证约束不同的素材。引用固定到本次读取的提交，未来升级参考版本须重新核验。

| 来源 | 值得学习的内容 | 本仓库落地位置 | 明确不直接照搬 |
|---|---|---|---|
| [SciPilot Figure](https://github.com/Haojae/scipilot-figure-skill/tree/43098ddb9e6a6d142218540c114f9ed38922fc42) | 图型与统计语义匹配；分布显示真实点；按最终图幅安排字号、线宽和图例；参数集中可调 | F1 决策指引、F3 技巧样例、MATLAB 参数区 | 自动视觉 QA、机械样本阈值、为所有确定性结果添加误差线、按比例容忍静默丢数据 |
| [Scientific Figure Making / figures4papers](https://github.com/ChenLiu-1996/figures4papers/tree/3c181f85e82c6f24948fcaaf3be6696102b41d8d) | 主次层级；基准和改变量表达；矩阵分组与数值标注；局部尺度和图例排版 | F2 样式接口、F3 对比/矩阵/消融模式 | 整库移植、把项目专用硬编码当通用 API、用透明度或归一化掩盖比较差异 |
| [Academic Figure Skill](https://github.com/TingxiYu/academic-figure-skill/tree/1df9940dd01ac939f072b12fe28d6353b79b90f9) | 按任务和数学语义选择表示；每个面板贡献独立证据；保留明确的好/坏案例与修复原因 | F1 证据决策、F3 案例说明、F4 人工调整指引 | 自动图像评分、固定 hero 面板或强制不对称、按效果强弱门槛过滤真实结果、把栅格拼接 PDF 当作全矢量 |

实现采用独立的 MATLAB 写法，借鉴“为什么这样画”，不复制外部 Python 工程。本次读取的仓库许可分别为 MIT、CC BY-NC 4.0、Apache-2.0；如后续确需复制代码或资产，先核对具体文件归属、许可和署名要求，不把不同来源的相同示例当作独立验证。

现有仓库已吸收过部分科研绘图理念，F1/F2 应修正冲突与缺口，不再叠加一套平行的 Scientific Figure Authority。

## 4. P0：已确认的衔接问题与修复顺序

### P0-1：标题契约与当前正式图政策冲突

**基线事实：** `core/workbook_schema.yaml` 的 `matlab_handoff.required_mapping_fields` 仍要求 `matlab_title`，`title_contract` 仍要求单图 `title`、多图 `sgtitle` 并保留导出。当前 `modules/04_figure_evidence.md`、`core/output_contract.yaml` 与 MATLAB 正式模板执行无整体标题政策。

当前 `scripts/lint_skill_checks.py` 内有旧的正向标题 token，但 `scripts/lint_skill.py` 会精确过滤该旧诊断，并检查可执行代码中的 `title/sgtitle`。因此问题是 schema 漂移，**不能误报为当前 lint 要求添加标题**。本次检索未发现独立的 `build_matlab_handoff.py` 或 `validate_matlab_handoff.py`，不能为不存在的消费端安排修复或新增无必要文件。

**修改内容：**

1. 对齐现有 workbook schema 与正式输出政策，新映射不再要求图内标题；caption 保持承载图名与必要说明。
2. 旧项目中已有的 `matlab_title` 可作为只读历史描述，不用于生成 `title/sgtitle`，不因此自动迁移、拒绝或重写旧工作簿。
3. 复核实际 `scripts/project_snapshot.py`、`scripts/sync_project.py` 与标题检查，必要时修正同一语义的消费行为；不因 schema 改动重构同步器。
4. 清理真正失效的旧检查来源及对应 facade 特判时，必须同 PR 保留当前可执行标题禁止规则，不能只删报错。

**验收：** schema 不再要求新映射带图内标题；无标题代码合规；实际整体标题调用被识别；注释中的示例不误报；旧字段仅有历史来源时可兼容。重点检查 `tests/test_schemas.py`、`tests/test_sync_project.py`、`tests/test_tooling.py`。

### P0-2：可选 03B 与工作簿 reader 的强制依赖冲突

**基线事实：** `templates/matlab/hsk_read_result_workbooks.m` 无条件要求分析工作簿存在并枚举其工作表；这与 `Analysis Necessity Gate=not_required` 时合法没有 03B 产物的规则冲突。具体工作表只有在 requirements 声明时才检查，声明项同时要求 headers 和 columns 并按固定列校验，并非空 requirements 也强制某一套分析表。当前 `q1_plot.m` 自行读取选定工作簿，并未调用该 reader；这是备用 helper 风险，不能说所有现有绘图已因此失败。

**修改内容：**

1. reader 按调用方明确声明的当前图所需工作簿、工作表和字段读取，不先枚举并强制所有可能产物存在。
2. 普通主结果图只依赖其真实使用的数据。`not_required` 且有理由时缺少分析工作簿是合法状态。
3. 明确引用 03B 的图必须验证对应分析已执行、验收且文件存在；缺失时清楚报错，不自动回退主工作簿或临时文件。
4. 是否保留 reader 的旧调用签名，先列调用点；优先新增明确可选参数或局部适配，保留独立 `q{x}_plot.m` 的运行方式，不增加每问必须携带的新 helper 文件。
5. 保持目前的主结果/条件分析文件命名与同题目录约定，不以绘图修改重写 Analysis Necessity Gate。

**验收：** 主结果图在没有 03B 时合法；声明需要 03B 却缺失时失败；没有用到的分析表不被强制读取；不把 `not_required` 解释成已经通过稳定性检验。检查 MATLAB README、reader、相关模板与 `tests/test_p7_conditional_analysis_appendix.py`、`tests/test_sync_project.py`、`tests/test_tooling.py`。

### P0-3：固定列位置与精确唯一表头规则未闭环

**基线事实：** reader 仍有 `fixedColumns` 位置约定；`templates/figure/figure_plan.md`、`figure_paper_closure.md` 等表头仍登记“固定列”。`scripts/lint_skill_checks.py` 和 `tests/test_tooling.py` 仍有活跃的 `fixedColumns` token 断言。当前 schema 和 `q1_plot.m` 已采用精确唯一表头，期望列号仅辅助提示。

**修改内容：** reader 及活动交接表统一为工作簿 → 工作表 → 精确表头唯一匹配。键列、数值列也必须通过表头定位，不能留下整数列号旁路。允许已有规则规定的空白规范化；缺失或重复匹配立即报错，不猜别名、相近列或默认列号。期望列号只做可选漂移警告。同步 `templates/model/model_paper_framework.md`、`templates/writing/caption_explanation.md`、`templates/writing/docx_check.md` 中仍与该语义有关的字段说明；不要重排整个框架或扩展 DOCX 写作重构。

**验收：** 字段移动仍读取正确数据；重复表头、缺少表头、相似但不相同字段被拒绝；前后空白按既有规范处理；可选期望位置不影响合法读取。检查和测试从“必须出现 fixedColumns 字样”转为有正反例的实际契约约束。

### P0-4：非法值、缺测与排序不能静默改变证据

**基线事实：** `q1_plot.m` 与 `data_process.m` 把不能解析的单元格转为 NaN，再用 `isfinite` 掩码静默删行，并无条件按 x 排序。reader 的数值检查允许 NaN，非法文本也可能先变成 NaN，不能据此声称它已严格拒绝坏数据。

**修改内容：**

1. 区分导入空值、合同允许的缺测、失败状态记录、非空非法文本、Inf/NaN，保留读入行号与记录键。显示转换不承担重新清洗或插补职责。`readcell` 已按读取范围导入；导入后的 missing/NaN 不能证明原单元格是物理空白，默认不追加推测性的尾行裁剪。确需限制尾部时，使用已验收证据明确给出的范围，不从缺测模式猜测。
2. 非空非法数据给出工作簿、工作表、表头和行号定位；合同未允许的缺测不得悄悄删除。合法缺测应按其语义留下间断或显式说明，不跨越缺口画出连续关系。
3. 所有配对数组沿同一记录键处理，保持 x/y/区间/组别关联，不能分别过滤后拼接。
4. 只有合同明确存在时间或连续自变量的排序语义时排序，并同步其他字段；轨迹、路径、类别或配对记录保留真实顺序，不一律 `sort(x)`。
5. 避免一概拒绝所有 NaN，导致合法缺测无法展示；也不设“丢弃不足某百分比便可接受”的阈值。

**验收：** 导入范围、非法文本、Inf、允许/不允许的缺测、配对键、重复时间及路径顺序都有明确预期；不能把读入的缺测行自动视为空尾删掉，错误不会静默变成一个更好看的子样本。源代码检查和纯语法解析不冒充 MATLAB 运行行为测试，也不以 Python 影子 reader 证明 MATLAB 正确；模型数值与真实图形仍由用户本机验收。

### P0-5：先落实不自动运行 MATLAB 和图像检查

**基线事实：** `.github/workflows/optimization-baseline.yml` 的 `real_matlab_preview` 会在两个样式 helper 等文件变化时安装 MATLAB、执行 `tests/matlab/p6b_publication_preview.m`、导出并通过 `imread` 等检查图像/图形对象。这是自动渲染与机器检查，不是 AI 审美评分，但仍超出用户本轮希望的静态验证范围。

**修改内容：** 在后续触碰样式 helper 之前，把真实 MATLAB preview 保留为**只有显式手动触发且明确选择时才运行的可选能力**，从普通 PR 自动执行范围移出。为 `workflow_dispatch` 增加缺省为 false 的布尔选择，job 级同时限制事件类型和该选择；手动明确选 true 后不再依赖旧的 changed-path 判断，避免用户要求预览却因本次未改 helper 而静默跳过。同步触发条件、相关说明与 `tests/test_p6b_matlab_preview_contract.py`；保留无关的 `source_snapshot`、`characterize`、普通 CI、静态 lint 和数据契约回归。不删除历史预览证据，不修改已完成历史运行的事实。

**验收：** 普通 PR（含 workflow 自身或 helper 改动）不会安装/运行 MATLAB 或执行图像检查；手动触发的开关缺省不启用；保留能力是否可用只能如实报告静态配置检查，本轮不调用验证；任何跳过都不能写成真实渲染通过。P0-5 应先独立合并，再进行 F2，以免新 helper PR 被旧触发逻辑自动运行。

## 5. F1：从“强制丰富图型”改为按证据选择表达

### 5.1 修改位置与原则

以 `modules/04_figure_evidence.md` 为绘图决策 Authority；审查 `templates/figure/chart_selection.md`、`result_figure_contract.md`、`result_figure_qa.md`、`figure_enhancement_patterns.md`、MATLAB README 和 `packs/artifact/figure.md` 的对应说明。

保留 Evidence Structure、Figure Contract、Basic-form Challenge、Composite Encoding、Rendering Profile、动态布局的已有能力，调整其中容易被理解成“基础图必须升级成复杂图”的措辞。检查内容改为：这张图是否让读者正确理解必要关系，是否缺失关键证据，附加编码是否提供新信息。

决策过程收敛为：

1. 写明图要支持的具体结论和可用真实字段。
2. 判断变量类型、比较/排序/配对关系、空间结构和不确定性是否真实存在。
3. 选择能清楚回答问题的最简单表达；只有缺少必要证据时才增加编码或面板。
4. 再安排视觉权重、颜色、尺寸、标注和图例。
5. 当前 accepted 数据不支持某种图时，换合适表达或记录证据缺口，不补造数据。

### 5.2 兼容与验收

- 先核对 F1/F2/F3 层级标签的现有消费端，不因为字面上像“档次”就删除 schema 枚举；在现有结构内澄清质量不由图型复杂度决定。
- `core/workflow_router.yaml` 存在按章节标题读取的配置。优先保留现有锚点；确需改标题时，同 PR 同步读取列表和相关测试，防止规则改好了却读不到。
- 不新增独立审美 Gate、必填“去 AI 分数”、最少图数、图型多样性配额或机器视觉复核。当前图形审批的人工责任保持。
- 验收反例包括：清楚的单折线可以是核心图；相同数据的线和点不构成两份证据；没有真实区间不画带；存在互补证据时允许复合图；单面板合理时不强加 hero 面板。
- 重点回归 `tests/test_v715_scientific_figure_elevation.py`、`tests/test_v713_figure_enhancement.py`、`tests/test_v742_dynamic_figure_layout.py`、`tests/test_read_path_semantic_closure.py` 与相应 lint。

## 6. F2：无默认配色、样式可调、单文件可运行

### 6.1 调整样式接口

检查并成组修改：

- `templates/matlab/hsk_publication_profile.m`：不再通过省略参数隐式选择某套色板；参考色板仅在显式选择时返回。
- `templates/matlab/hsk_apply_scientific_style.m`：将字体、线框等基础排版与配色选择分开；没有颜色参数时不偷偷改变颜色。图中颜色由实例脚本明确配置。
- `templates/matlab/q1_plot.m`、`data_process.m`：移除固定 high-contrast 调用和仅支持该 profile 的本地 fallback 限制；集中当前图的可调参数，保持无共享 helper 时的独立执行能力。
- `scripts/lint_skill.py`：当前硬编码要求 `apply_publication_style(fig, "competition_high_contrast")` 和特定 palette 字段的检查必须同步改为新接口约束，不保留强制默认色板的旧 token。
- `tests/test_v910_publication_rendering.py`、`test_p6a_figure_reference_profile.py`、`test_read_path_semantic_closure.py`、`test_tooling.py` 及实际相关调用点：更新假设，保留可调性和真实证据约束。

同步检查 Module 04、Figure Pack、根 `README.md`、MATLAB README、`result_figure_qa.md` 和 enhancement patterns 中的“默认高对比、蓝红优先”表述，以及 `tests/test_content_packs.py`、`test_v715_scientific_figure_elevation.py`、`test_v742_dynamic_figure_layout.py` 等对旧措辞的约束。政策与代码在 F2 同一 PR 闭环，不能只换 helper 让上游仍按旧默认生成调用，也不能把必需的政策更新留到 F4。

F2 还须同步 `core/output_contract.yaml` 中当前为 true 的 `matlab_figure_contract.high_contrast_primary_palette_required` 与 `tests/test_current_skill_health.py` 的对应断言；不能遗漏上游产物合同的强制配色要求。global policy 已将 Figure 细则委托 Module 04，无需另加一份配色政策。

明确选择旧 profile 的调用可以保留兼容；**旧 API 省略参数时隐式选色的行为不能以兼容为由继续作为新默认。** 优先采用“省略颜色只应用基础排版，原色不变”的兼容方式；必须返回 palette 的旧无参调用若无法兼容，应给出清楚的迁移提示并在 PR 如实说明接口影响，不使用隐藏默认掩盖变化。参考色板可继续保留原名，但全部是显式候选。

### 6.2 每张图的人工调整入口

在脚本开头集中当前图实际需要的参数：颜色/colormap、字体和字号、主辅线宽、点大小与展示间隔、图幅、图例位置、轴范围和必要注释。提供合理排版起点，但数值不能成为所有图的硬性要求；不为了配置增加多层抽象、独立配置仓库或必交附属文件。

统一 helper 与本地 fallback 的必要排版语义，修正当前 fallback 字号与轴标签/colorbar 覆盖不一致的问题。普通 Cartesian、heatmap、三维或 polar 对象按各自支持的属性处理，不对全部对象盲设同一轴属性。明确调用顺序：基础样式先应用，当前图的局部覆盖最后生效；禁止在脚本结尾再调用统一 helper 把用户调好的字号、线宽或图例位置重置。

继续保留可见 figure 窗口；默认不自动关闭或批量导出。用户需要时再显式导出，优先支持能保留对象编辑能力的输出选项；不把 `.fig`、PDF、PNG 全套文件设为每问强制产物。不把保存 `.fig` 等同于正式论文已经验收。

### 6.3 修复最明显的模板化表达

当前 `q1_plot.m` 的蓝色线与红色点共用同一组 x/y，却用“主结果”“真实点”两个图例，容易让人误以为是两组独立结果。改为同一对象使用统一颜色与一个图例项；若 marker 没有帮助可省略，密集趋势可稀疏显示 marker，但保留全部线数据。只有真实区分观测、拟合、预测或方案时才分别编码。

不统一要求所有图隐藏网格或只使用一种边框。按读数需要设置细网格，避免强网格、粗边框、过多刻度与反复标注。注释只强调有证据的关键阈值、边界、极值或决策点，不给每个点加大段说明。

**验收：** 更改脚本头部参数能沿代码路径生效；显式配色和旧显式 profile 都有清楚行为；未选择配色不会被 helper 重涂；新模板不得隐式使用某套色序；有/无共享 helper 的接口与配置覆盖规则一致；类别数据不被无条件连线。

## 7. F3：建立少量高价值绘图技巧样例

优先在既有 `templates/figure/figure_enhancement_patterns.md`、`chart_selection.md` 和 MATLAB README 补足“适用证据 → 表达方法 → 参数 → 常见错误”。仅当可读性确有需要时新增少量 MATLAB 示例文件，不建立覆盖所有图型的大框架，也不让普通任务预读完整样例库。

| 模式 | 可学习的绘制技巧 | 数据和误用边界 |
|---|---|---|
| 排序比较 / 区间点图 | 横向布局容纳长名称；点位显示大小；有真实区间时附区间；突出实际研究重点 | 标明排序依据和指标方向；条形通常保留零基线；点图区间缩放明确标示，不伪装差距 |
| 配对前后 / 哑铃或斜率图 | 同一对象两端连接；少量标签直接标注；真实增减使用一致语义色 | 必须具有真实配对键；非同一对象不连线；方法列表顺序不冒充嵌套消融过程 |
| 时间 / 参数趋势 | 清晰主线、适当背景线、稀疏 marker、末端标签；有真实区间时用轻带 | 保留全部数据和真实转折；不跨缺测连接；多条同等重要曲线不能任意灰化；无区间不造带 |
| 分布 | 原始散点与箱线配合，或 ECDF；点密集时透明度和抖动仅服务可见性 | 原始点不删，抖动不改变数值轴；密度需足够样本及合适方法；不把确定性方案结果当随机样本 |
| 矩阵 / 多方案多指标 | 有依据的行列分组；适度数值标注；读数文字与底色协调；色条表达清楚 | 列内归一化与全图共同尺度明确区分；保留真实值和单位；不同单位不能暗示绝对值可直接比较 |
| 空间 / 多目标 / 消融 | 空间场配必要边界或等值线；Pareto 展示候选与前沿及推荐点；消融对真实基准展示差值 | 不从摘要反推场；不同空间图若比较大小应共用可比尺度；不隐藏非最优候选；差值有实际基准 |

样例应说明为何选择、哪些参数适合手动改、何时不适用。展示数据若为 synthetic，放在隔离示例中明确标识；不得写进 accepted 工作簿、论文数值或正式图表登记。无 MATLAB 环境时交付静态样例和明确限制，不输出未经实际运行的“前后效果图”或虚构审美改善证据。

## 8. F4：绘图与论文、框架、用户操作的收口

1. 将图表计划和论文闭环表中的“固定列”更新为实际字段合同，补充/复用记录键、单位、caption、支撑结论和当前数据来源，避免重复维护独立交接文件。
2. 标明主工作簿与条件 03B 来源，不在默认示例中暗示每问都必须存在分析工作簿。按 P0-2/P0-3 的结果同步 `templates/model/model_paper_framework.md`；不触碰无关的模型、证明和写作结构。
3. 图名由 caption 承担；正文解释写清“看到什么、支持什么判断、有什么适用条件”，不在图中堆论文句子。本文只调整绘图相关接口说明，不重写普通正文 Writing Authority。
4. MATLAB README 提供简短操作路径：替换真实来源与字段 → 按图显式选择颜色及必要参数 → 静态检查 → 用户在 MATLAB 打开图窗 → 手动调整与需要时导出。用户无需提交截图或完成额外审美表单。
5. `templates/figure/result_figure_qa.md` 等已有检查资料保留科学正确性和人工参考内容；Agent 的确定性代码检查、人工观感判断和实际运行验证分别标注，不把人工事项包装成自动执行的 Gate。
6. 基于实际改动更新入口摘要、受影响的按标题读取映射和生成索引。历史计划、已完成 release 与原始验收证据不批量改写成新事实；必要时补充简短的现行政策指针。

## 9. 文件职责与最小影响面

下表是实施时的必查范围，不是要求全部修改。每个 PR 应说明真正修改了哪些位置、哪些已一致而无需改动。

| 主题 | 主要承载文件 | 关联检查 |
|---|---|---|
| 绘图选型及证据政策 | `modules/04_figure_evidence.md` | Figure Pack、chart selection、result figure contract/QA、按章节读取路由 |
| 工作簿与标题交接 | `core/workbook_schema.yaml`、`core/output_contract.yaml` | 实际 snapshot/sync 消费端、schema/tooling/sync 测试；不新增假定的 handoff 工具 |
| 读取与合法数据记录 | reader、`q1_plot.m`、`data_process.m` | `templates/code/hsk_pipeline/result_io.py` 作为生产端必查；无写出问题则不修改它 |
| 无默认颜色及样式覆盖 | 两个 style/profile helper、两个 MATLAB 入口及本地 fallback | MATLAB README、lint facade/helper、profile/rendering/tooling/read-path 测试 |
| 不自动运行预览 | `.github/workflows/optimization-baseline.yml` | `tests/test_p6b_matlab_preview_contract.py`、现有 preview 说明和 harness 的接口；不删除历史证据 |
| 论文与框架衔接 | `figure_plan.md`、`figure_paper_closure.md`、`templates/model/model_paper_framework.md` | 保留框架结构、caption 和 current accepted 来源，不扩大写作重构 |
| 导航与版本 | 受影响入口、`core/workflow_router.yaml`、现有版本载体 | 仅在实际需要时改源；所有索引和 Manifest 由 `scripts/generate_indexes.py` 生成 |

## 10. 实施阶段、提交顺序与完成条件

| 阶段 | 内容 / 依赖 | 合并前的完成条件 |
|---|---|---|
| P0-A | P0-1 标题 schema 与现行标题链对齐 | 标题政策、活动检查与旧字段兼容闭环；不引入新标题要求 |
| P0-B | P0-2 可选 03B、P0-3 表头规范/reader/交接表/检查全链、P0-4 数据记录与排序；依赖 P0-A | 合法缺少分析簿不阻塞；字段移动可读而缺失/重复失败；非法数据/顺序不静默改变；不留下固定列半迁移 |
| P0-C | P0-5 将 MATLAB preview 改为显式手动选择；在任何样式 helper PR 前完成 | 自动 PR 不运行 MATLAB/图像检查，静态和无关 CI 保留 |
| F1 | 证据导向决策与简单图合法性；依赖全部 P0 | 不强制复杂图，不损失互补证据能力，读取路径与测试一致 |
| F2 | 无默认配色、显式候选、参数和 fallback、重复线点/图例修复；依赖 F1/P0-C | 没有隐式配色，用户局部设置可保留，共享/单文件使用方式清楚 |
| F3 | 高频技巧样例；依赖 F1/F2 | 每个样例有适用证据和误用边界，代码静态可审查，未声称实机运行 |
| F4 | 文档、框架、图文衔接与最终核对；依赖前述全部 | 活动接口一致，生成索引有效，状态报告真实，用户人工调图路径简明 |

每阶段一个主题 PR；同一任务只维护一个当前活动分支，不同时铺开修改共享 Authority。一个阶段体量过大时可按独立接口拆分，但必须先更新本表的依赖和验收，不能形成消费者先于契约或 helper 先于 P0-C 的顺序。前一 PR 合并后才以最新 main 建立下一阶段分支；合并仍以用户授权为准。

本次计划 PR 不是上述任何实施阶段的完成记录。计划合并也不代表具体实现已经完成或所有后续合并已获授权。

## 11. 验证策略：检查真实风险，不以静态替代运行

### 11.1 仓库基本检查

按现有治理执行：

```text
python scripts/lint_skill.py
python -m unittest discover -s tests
python scripts/generate_indexes.py --check
```

源文件改动后先运行 `python scripts/generate_indexes.py`，检查生成差异，再执行 `--check`。生成产物单独提交；不手工写哈希，不往源树放测试日志或用户工作簿。

Python 单元测试在这里验证仓库实现/合同，不代表运行了用户 MATLAB 或数值模型。受影响测试可以在开发中先跑，但不能以小范围测试替代治理规定的全套回归。若环境相关失败出现，保留日志，区分基线问题与本次回归；不得为绿色结果删除或弱化无关测试。

### 11.2 关键正反例

| 风险 | 正例 | 反例 / 必须识别的情况 |
|---|---|---|
| 标题 | caption 承载图名、无整体标题 | 实际执行 `title/sgtitle`；注释不能被当作调用 |
| 条件分析 | 主结果图、03B 合法缺省 | 图声明需要分析证据却缺失；偷偷换来源 |
| 字段 | 精确唯一表头，列顺序改变 | 同名重复、缺失、相似字段替代、固定位置误读 |
| 数据记录 | 合同允许缺测、配对键及路径顺序保全 | 非空坏字符串变 NaN 后删行、分别过滤数组、随意排序 |
| 配色 | 当前图显式配置；未指定颜色的基础样式不改原色 | 无参隐式高对比/Nature/SCI/色序回退 |
| 可调性 | 局部字号/图例覆盖保留；standalone fallback 可审查 | 末尾 helper 再次覆盖；为换色强制多交文件 |
| 图型 | 简单图充分表达；复合图有真实补充证据 | 重复数据两图例、虚构区间、强制多面板或多样性配额 |
| 自动化 | 普通 PR 只执行既定非 MATLAB 检查 | 路径命中后安装/运行 MATLAB、读图评分、跳过当通过 |

这些是有实际风险的验收边界，不要求给每个字体常数或 Markdown 句子新增单元测试，也不以“某 token 出现”代替 MATLAB 行为验证。可用现有分析器检查源代码时说明工具；若没有 MATLAB Code Analyzer，只能说明人工静态阅读和仓库合同检查覆盖，不能写成已通过 `checkcode/mlint`。P0-A 的标题扫描回归覆盖普通行注释与直接 `title/sgtitle` 调用；现有扫描不是完整 MATLAB lexer，字符串与块注释等复杂语法不据此宣称已完整验证，本阶段不顺带重写词法解析器。

### 11.3 用户人工验收

用户按需要在 MATLAB 检查实际图形是否美观、坐标/单位是否清楚、线点和颜色是否合适、图例与标签是否遮挡，再自行调整脚本参数。此项是用户的实际使用过程，不是要求 Agent 追加图像审查的交付步骤。用户未反馈之前记录“未进行本机运行/人工验收”，静态交付可以完成；正式论文图的最终验收不伪造为已完成。

## 12. 进度记录与后续交付格式

每次实施更新本节，状态与实际 commit/PR/检查对应。只完成静态修改时，不勾选图形实机验收，也不以 PR CI 代替合并后 main CI。

| 编号 | 状态 | 实现 PR / commit | 验证与剩余事项 |
|---|---|---|---|
| P0-A | 已合并并完成验证 | [PR #211](https://github.com/Vexushi1/mathmodel-skill/pull/211)，合并 `e00f31dfc5ab4fcf67877e8b0effdff61d6970e2` | [PR CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35491575546)、[优化基线](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35491575524)、[main CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35491780957) 和 main 生成检查通过；本地 1076 项仍有同样的 40 个 Windows 基线问题；未运行 MATLAB |
| P0-B | 已合并并完成验证 | [PR #212](https://github.com/Vexushi1/mathmodel-skill/pull/212)，合并 `208d8ddda42150371d59b6553ec171853e5cd509` | [PR CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35492571378)、[优化基线](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35492571439)、[main CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35492791788)及 main 生成检查通过；3 个 MATLAB 文件纯语法解析通过，36 项读取/保护专项、46 项发布/交接专项通过；全量 1076 项与初始基线相同的 40 个 Windows 问题，无新增失败（一次进程异常退出单独留日志，复跑完成）；MATLAB 实机验收独立进行 |
| P0-C | 已合并并完成验证 | [PR #213](https://github.com/Vexushi1/mathmodel-skill/pull/213)，合并 `deca8d60973635057cf55969c0b0e81bc892c241` | [PR CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35493084211)和[优化基线](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35493084249)通过，[main CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35493337986) 和 main 生成检查通过；真实 MATLAB job 为 skipped；8 项专项通过，全量 1079 项仅原有 40 个 Windows 问题；未 dispatch |
| F1 | 已合并并完成验证 | [PR #214](https://github.com/Vexushi1/mathmodel-skill/pull/214)，合并 `5d0829b11d3522862697bb638581ddb68fd761e8` | [PR CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35493617169)、[优化基线](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35493617190)、[main CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35493787196)及 main 生成检查通过；28 个 Module 04 selector 唯一命中；MATLAB 非注释行不变，2 文件纯语法解析通过；27 项专项通过；全量 1080 项仅原有 40 个 Windows 问题 |
| F2 | 已合并并完成验证 | [PR #215](https://github.com/Vexushi1/mathmodel-skill/pull/215)，合并 `9ae97530c0d9e2a574be001b4039e56c67b17eda` | [PR CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35494610086)、[优化基线](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35494610072)和生成检查通过；Python 3.10–3.14 全矩阵通过；真实 MATLAB job skipped；[main CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35494773894) 通过，main 生成检查通过；本地全量 1088 项仅原有 40 个 Windows 问题；5 文件纯语法解析通过 |
| F3 | 实现与本地静态验证完成，待 PR CI | `fix/figure-f3-techniques`，基线 `9ae9753` | 六类技巧和三个原创 MATLAB 片段集成到现有文档；片段需真实输入与显式参数，无模拟数据，不新增必交文件；3 片段 MISS_HIT 0.9.44 / R2021a 解析通过；35 项保护/读取闭环检查通过；全量 1088 项仅原有 40 个 Windows 问题；lint/生成检查通过，PR CI 待完成 |
| F4 | 未开始 | — | 文档与跨文件最终闭环待核对 |
| 用户 MATLAB 运行与人工调图 | 用户自行进行 | 不适用 | 不由静态检查或 CI 自动宣告通过 |

实施 PR 的简短交付应包含：任务编号；改了什么及为何；基线与 head SHA；实际验证及未运行事项；兼容/迁移；PR、合并状态与下一未完成阶段。若发生阶段调整，在下表记录，不用多份“最终计划”替代本文件。

| 日期 | 计划修订 | 原因与影响 |
|---|---|---|
| 2026-09-20 | 1.0 初稿 | 固化用户要求；P0 优先；配色不设默认；仅静态 MATLAB 检查，人工调图；未实施代码 |
| 2026-09-20 | 1.1 开始 P0-A | 计划 PR [#210](https://github.com/Vexushi1/mathmodel-skill/pull/210) 已合并，基线 `32587cf8463937611c3458429bc57f0d5cfce591`；用户授权开始实施；目标 Skill 9.4.1、Workbook Schema 声明 2.3.1，不改变实际 Excel 字段或用户项目 |
| 2026-09-20 | 1.2 完成 P0-A，进入 P0-B | P0-A 的 PR/main 检查通过；P0-B 保守处理不可由导入值反推的物理空白，不自动猜测裁尾；使用 MISS_HIT core 0.9.44 做第三方纯语法解析，不执行 MATLAB；补记 F2 的 Output Contract 配色约束影响面 |
| 2026-09-20 | 1.3 完成 P0-B，实施 P0-C | P0-B 的 PR/main 检查通过；P0-C 将真实 MATLAB preview 从普通 PR 移至缺省关闭的手动选项，保留普通静态 CI 和历史证据 |
| 2026-09-20 | 1.4 完成 P0-C，进入 F1 | P0-C PR CI 通过且 MATLAB job 跳过；F1 保留能力与标签，修正基础图强制升级、候选凑数和 Portfolio 图型比例倾向，同步标题 selector |

| 2026-09-20 | 1.5 完成 F1，进入 F2 | F1 的 PR/main 检查通过；F2 新增可选排版参数并取消隐式配色。旧的显式 profile 名称及别名保留；无参调用不再返回带颜色字段的 palette，依赖 `palette.primary` 等的旧调用须显式传入原 profile，或自行设置 RGB。已复制到旧项目的脚本不自动迁移；新模板须实例化颜色后使用，不把留空参数模板当作开箱即跑的完成代码 |

| 2026-09-20 | 1.6 完成 F2，进入 F3 | F2 PR 检查通过并合并；补充六类按需参考技巧，三个片段保留真实配对集合、缺测断线/区间分段和各指标真实尺度；静态片段不充当完整已实例化脚本或运行证明 |

## 13. 回滚与完成判定

每阶段尽量形成可独立回滚的契约/消费者/测试闭环；回滚时一起恢复，随后用生成器刷新索引。P0-C 与 F2 有明确先后关系：不能单独恢复旧的自动 preview 触发规则却仍声称后续维护只静态检查。旧项目不批量迁移，回滚不触碰用户结果与原始数据。

全部实施完成的判据是 P0-A 至 F4 均有真实实现和相应验证记录，活动规则、模板、检查与文档相互一致，新生成脚本能够按图显式选色且便于用户调整。没有 MATLAB 实际运行证据时，完成状态应写“仓库修改与静态验证完成；用户本机图形验收独立进行”，不能写“所有图已运行无错并达到美观要求”。
