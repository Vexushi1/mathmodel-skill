# HSK MATLAB 科研绘图模板（当前活动模板）

MATLAB 只读取 Python 已验收的 current 合法工作簿与数据事实源，不重新求解、重新清洗、重新做敏感性或重新估计模型。每问唯一入口通用记为 `q{x}_plot.m`，问题一实例为 `q1_plot.m`，与主求解脚本、主工作簿以及条件存在的 03B 脚本/工作簿同处 `问题X求解/`；活动模板与文档只使用这一标准命名。

MATLAB 的职责不是“把 Excel 画出来”，而是：

> **基于 Python 已验收的细粒度证据，完成 Scientific Evidence Visualization：科学视觉编码、组合表达、结构表达、全局—局部组织、统计/不确定性表达与论文证据强化。**

## 路径

```matlab
scriptPath = string(mfilename("fullpath"));
resultDir = string(fileparts(scriptPath));
solutionBook = fullfile(resultDir, "问题一求解结果.xlsx");
resultAnalysisBook = fullfile(resultDir, "问题一结果深化分析.xlsx");
```

`solutionBook` 是主结果图的必需事实源。`resultAnalysisBook` 只是条件路径：Analysis Necessity Gate=`required` 且 03B 已实际执行、验收时才存在；只有敏感性、稳定性、阈值、算法、结构、异质性等 Figure Contract 明确引用 03B evidence 时才读取。Gate=`not_required` 且理由非空时，没有分析工作簿是合法状态；不得因此阻断普通主结果图，也不得从主工作簿伪造 03B 图。若实例脚本明确选择 `resultAnalysisBook` 为 source，则文件不存在必须 fail closed。

不得跨问题读取临时 Excel、根据摘要数字反推数据或在 MATLAB 中重算核心结果。

## 实表读取

字段定位采用精确表头唯一匹配。允许登记期望列号作为结构漂移警告，禁止模糊匹配、别名猜测、相似字段回退和自动改变语义映射。

### 可选 reader 的调用与兼容

`hsk_read_result_workbooks(location, problemName, requirements)` 是可选 helper，不是每问必须携带的新增文件；`q{x}_plot.m` 与 `data_process.m` 继续独立读取各自的实际工作簿。`location` 可为项目根目录，此时指定 `problemName`；也可为 `问题X求解/`，此时传入空 `problemName`。

空 `requirements` 只检查主工作簿存在并枚举其工作表；显式声明后只检查所用的 `solution` / `analysis`。未使用的 `books.solutionSheets` / `books.analysisSheets` 返回空 string 数组，路径字段仍保留，不代表文件已存在或已经验收。声明 `analysis` 后文件缺失必须报错，不回退主结果。历史 `robustness` 仍映射分析来源，但与 `analysis` 同时出现时报歧义；历史分析文件名只在明确使用分析且标准文件缺失时只读兼容并告警。本轮保留这些旧接口，不迁移用户工作簿；未来删除兼容路径须单独说明迁移。

每个工作表的要求是标量 struct，只有 `headers` 必填：

| 字段 | 作用 |
|---|---|
| `headers` | 非空、无重复的精确表头文本；只规范化首尾空白 |
| `expected_columns` | 可选、与 headers 等长；正整数仅用于位置告警，NaN 表示不检查位置 |
| `key_header` | 可选、属于 headers 的单个表头；检查记录键非空且唯一；省略或空字符串表示不声明键 |
| `numeric_headers` | headers 的子集；逐行检查有限实数或该字段允许的缺测 |
| `allow_missing_headers` | numeric_headers 的子集；仅这些数值字段允许缺测 |
| `missing_tokens` | 可选的精确文本缺测标记；用于数值字段，首尾空白规范化，不猜测 NA/NaN 等含义；不能把有限数、Inf 或复数声明为缺测 |

新写法示例，表名和字段名必须替换成 accepted 工作簿的实际名称：

```matlab
requirements.solution.("逐时结果") = struct( ...
    "headers", ["记录键", "时刻", "数值"], ...
    "key_header", "记录键", "numeric_headers", ["时刻", "数值"], ...
    "allow_missing_headers", "数值");  % 仅当该字段的证据合同确实允许缺测
books = hsk_read_result_workbooks(projectRoot, "问题一", requirements);
```

旧写法仍可读，但整数必须能通过 `columns` 和 `headers` 声明映射：

```matlab
requirements.solution.("逐时结果") = struct( ...
    "headers", ["记录键", "时刻", "数值"], "columns", [1, 3, 5], ...
    "key_column", 1, "numeric_columns", [3, 5]);
```

这里的第 3、5 列先映射为“时刻”“数值”，再按真实唯一表头读取；移动列不改变绑定。`columns` 不再锁定实际列位置。旧整数缺少声明映射、存在歧义、新旧位置/角色声明不一致或未知配置字段均报错；不能直接用旧列号读取，也不静默忽略冲突。`key_header` 可单独使用；把它同时列为 numeric_headers 时还会接受数值检查。该 helper 只验证要求，不排序或返回重组后的数值数组。

### 缺测、读入行与证据保全

数值 NaN、导入 missing、字符串缺测和空值只能说明当前导入表示，不能证明原 Excel 单元格物理为空。`readcell` 的默认 used range 已处理无数据首尾区域；reader 和独立绘图入口不再根据“转换后全 NaN”自动裁尾或删行，纯空白文本也不据此整行丢弃。难以判定的尾行保留并按字段合同处理；需要精确范围时使用已验收数据明确给出的范围，不猜测数据边界。[readcell](https://www.mathworks.com/help/matlab/ref/readcell.html)、[missing](https://www.mathworks.com/help/matlab/ref/missing.html)

允许的数值缺测保留位置；绘图时保留 NaN 间断，不删除缺测点后跨缺口连线。文本先规范化首尾空白，空文本按缺测处理；其他文本只有在明确 missing_tokens 中才作缺测，否则必须能解析为有限实数；Inf、复数和非标量报错。记录键不能缺测或重复，数值键不能用有限显示精度舍入后判重。报错包括工作簿、工作表、字段和**读入行号（含表头）**，不把默认导入偏移猜作 Excel 绝对行号。该检查不替代 accepted 状态验证，也不重新清洗、补算或改写工作簿。

两个独立入口默认保留源记录顺序。只有当前证据确有连续自变量/时间排序语义时，才显式设置 `sortByX=true` 并填写 `sortReason`；同一排序同时作用于数值、键和读入行。重复 x 不自动聚合或猜测组别。此数值曲线示例要求有限 x；datetime、类别横轴和多组轨迹应按真实字段另外实例化。

## Scientific Figure Synthesis Gate

正式绘图前先读取 Figure Contract 与当前合法 accepted workbook，识别 Evidence Structure：简单比较、分布、时间演化、空间结构、机制关系、约束/可行域、参数响应、不确定性、多目标、稳定/失效区域、网络流、调度、诊断、全局—局部。

不要先问“用 bar 还是 line”。先问：

```text
这条 Core conclusion 依赖什么结构？
当前工作簿实际保留了哪些状态/过程/样本/边界？
哪种视觉结构能把模型本身暴露出来？
```

所有候选核心图按 Module 04 执行 Basic-form Challenge，检查当前结论所需关系是否充分表达。清楚的 plain bar / plain line / plain scatter / plain box / plain histogram 可以直接承担核心论证；复合图同样需要检查证据覆盖。F1/F2/F3 标签描述表达结构，不作质量排序；只有一种合适结构时记录理由，不凑第二候选。

## Composite Encoding Preference

只有多个编码共享同一证据空间、共同回答一个 Primary question，并同时提供真实互补信息和可读性增益时才组合；否则保留单一表达或分图。下列模式是候选，不是必须凑齐的组件：

```text
box + raw scatter
violin + raw scatter + median/quartile
line + CI / prediction interval
scatter + fit/identity + CI
scatter + marginal histogram/KDE
bar + errorbar + benchmark
bar + line（联合语义清楚时）
heatmap + contour / boundary
Pareto + recommendation + Local Zoom
trajectory + field + boundary
surface + contour projection（第三维真实时）
```

组合图只补充当前结论需要的真实样本、统计结构、模型关系、阈值/边界或不确定性。同一 x/y 的线与点仍是一份证据，不作为两个比较对象；没有实际区间就不画带，没有真实配对就不画配对线。

## Scientific Rendering Profile

选择视觉结构后再进入对应 Profile：

- Distribution：raw points + box/violin/ECDF + median/quantile；
- Regression / Prediction：scatter + identity/fit + CI + residual/marginal；
- Dynamic：trajectory + interval + event/threshold + zoom；
- Parameter Surface：heatmap + contour + point + feasible boundary；
- Spatial：field + path/flow + critical nodes + boundary + colorbar；
- Optimization / Pareto：candidates + Pareto + feasible state + knee/recommendation；
- High-density Scatter：alpha scatter / binned density / 2D density contour。

具体实现参考 `templates/figure/figure_enhancement_patterns.md`；该模板不拥有独立决策权。

## Publication Rendering Grammar 快速参考

`modules/04_figure_evidence.md` 决定“是否应该使用某种结构”；本目录只实现渲染。P6a 将“profile 数据”和“对 figure 应用样式”拆成两个职责：

```matlab
spec = hsk_publication_profile("journal_balanced");
% spec 只返回 deterministic palette / typography / frame，不修改 figure。

palette = hsk_apply_scientific_style(fig);  % 默认 competition_high_contrast
palette = hsk_apply_scientific_style(fig, "journal_balanced");
palette = hsk_apply_scientific_style(fig, "monochrome_print");
```

`hsk_publication_profile.m` 是共享 template implementation registry，不是 Figure Authority：它不读取工作簿、不创建 figure、不选择图型、legend/layout、坐标范围或导出策略。`hsk_apply_scientific_style.m` 消费该 registry，选择本机字体并把已选 profile 应用到当前 figure。

新脚本优先使用 semantic roles：`palette.primary / comparison / positive / accent / secondary / focus / context / neutral`；旧 `brightBlue / vividRed / ...` 字段继续兼容，但不应作为新图的唯一设计接口。

选择建议：

- `competition_high_contrast`：1--3 个主要对象、强比较、竞赛快速阅读；
- `journal_balanced`：4--8 个对象、多 panel、多指标、长 legend；
- `monochrome_print`：黑白打印或颜色不能承担唯一语义。

共享 style kernel 只做 white background、font fallback、open-axis ordinary Cartesian frame、frameless legend、colorbar typography 与 palette；**不自动决定图型、ylim、x ticks、legend tile、数据字段或导出**。heatmap、3D、polar 等若需要完整 frame，可在 helper 之后按 Figure Contract 明确覆盖。

高价值 publication patterns：Multi-Metric Comparison Strip、Dedicated Legend Tile、Ordered Ablation Ladder、Composition/Decomposition、Evidence Matrix、Milestone-aware Trend、Normalized Radar（严格准入）、Density/State-Space、Comparative Performance Matrix。实现边界见 `templates/figure/figure_enhancement_patterns.md`。

### 论文 Figure 视觉参考索引

当图型选择或布局确实需要视觉对照时，使用 `assets/figure_assets.yaml#reference_index` 先按 Evidence Structure、publication pattern 或 layout need 取得少量 asset key，再加载这些 key 对应的 `path/paths`。不得预加载整个图集，也不得把示例图的颜色、legend、面板数量或统计图型当成规则。最终视觉结构仍由 Figure Contract 与 Module 04 决定。

### Standalone project compatibility

项目正式接口保持 `core/output_contract.yaml` 的 conditional per-question layout：基础三文件；Gate=`required` 时追加 03B 两文件。Gate=`required` 的 total=5 兼容路径仍对应历史“每问五文件”接口；该术语不得解释为 Gate=`not_required` 的无条件默认。共享 style helper/profile helper 仍不是必须复制到每问目录的额外产物；换言之，本 patch 不新增“必须复制一个 style helper/profile helper”的第六文件。仓库模板在 HSK Skill/MATLAB template 路径可见时优先调用共享 `hsk_apply_scientific_style.m` + `hsk_publication_profile.m`；若用户只把单个 `qX_plot.m` / `data_process.m` 带到独立项目目录，入口脚本保留最小 local fallback，仅保证默认高对比 palette 与基础 frame，不复制 profile registry、profile 决策或图型 Authority。

## Figure Layout Gate

正式绘图前按 `modules/04_figure_evidence.md` 的 Figure Layout Gate 动态决定单图、1×2、2×1、1×3、2×2 或拆图，禁止把某一种版式写成所有赛题的默认模板。

判定顺序为：

```text
单图能闭合核心结论 → 单图
否则两个证据强配对/互补 → 1×2 或 2×1
否则三个证据构成不可拆序列 → 1×3
否则四个 panel 同时满足 2×2 保留条件 → 2×2
否则 → 按 Primary question / Evidence level 拆图
```

一张 Figure 原则上只有一个一级 Core conclusion。2×2 仅在四个 panel 具有清楚的对称/交叉结构、视觉编码不过载且拆分会明显损失直接比较效率时保留，不因为“结果多”就自动采用 2×2。

## Figure Enhancement Gate

Scientific Figure Synthesis、Rendering Profile 和基础布局确定后，继续按 `modules/04_figure_evidence.md` 的 Figure Enhancement Gate 判断是否需要信息增强；默认 `Enhancement=none`。只有局部差异被压缩、多曲线遮挡、焦点对象需要降噪、存在真实阈值/阶段、多个统计视角共同回答同一诊断问题，或第三维确有数学/物理意义时，才启用 Local Zoom、Small Multiples、Focus Highlighting、Semantic Background、Composite Diagnostic 或 Conditional 3D。

Figure Contract 记录 `Enhancement / Enhancement rationale`，不把 inset 坐标、透明度等实现参数写进项目语义合同。

## 图题与风格

- 正式论文图不设置整体 `title` 或 `sgtitle`；LaTeX/DOCX `caption` 承担正式图号和图名，多面板按需只保留 a/b/c/d 等 panel label；
- 本地探索阶段若临时使用调试标题，进入正式 `figures` 交付前必须移除；
- 白底、清晰细轴、中文坐标轴和单位，默认字号 18；
- 数据驱动主结果图恢复高对比、中高饱和科研主色：亮蓝 `#1478FF`、鲜红 `#F04444`、亮绿 `#16B364`、亮橙 `#F79009`、亮紫 `#7A5AF8`；强比较优先亮蓝 vs 鲜红；正式机理/推导图不继承该调色板，统一服从 Module 04 的 monochrome-first 黑白灰线稿规则；
- 辅助对象、置信区间、背景带和参考元素使用深灰 `#252B37`、浅灰 `#E9EAEB` 或透明度降权；高对比不等于全图所有元素都鲜艳；
- 同一对象/语义在全文保持颜色一致；红绿不能承担唯一语义，需要 marker/linestyle/shape；
- 禁止 rainbow/jet 和无序彩虹；热图按连续变量语义选择 sequential/diverging colormap，并保留 colorbar 与单位；
- 默认 `grid off`；确需网格时保持浅、稀且位于数据后方；
- 默认保留可见图窗，不自动关闭，不创建图表子目录，不批量导出；
- 论文阶段人工确认后，按需导出到项目级 `figures/`。

## Portfolio Gate

所有单图完成后，按核心结论检查图或表证据覆盖、必要关系缺口、跨图一致性以及重复图和 panel，不按 plain 图数量或占比触发返工。只有必要关系缺失时，才回查主求解与已激活 03B 的真实 Evidence Capture 和 Synthesis/Rendering 选择；数据中存在更多维度本身不是加图理由。

不得设置“必须有 N 种图型”的机械多样性指标，也不设复杂度或 F2/F3 占比配额。多张清楚的简单图可完整承担核心论证；单面板合理时不强制 hero panel 或不对称布局。

每张图的源工作簿、工作表、真实表头、脚本、论文 caption、Evidence level、Primary question、Evidence structure、Figure level、Selected visual structure、Composite encoding、Scientific Rendering Profile、Layout decision、Split decision、Enhancement / Enhancement rationale 和正文位置同步登记到 `模型论文框架.md`；默认不生成独立 `figure_evidence` 文件。

图表交付前执行 `python scripts/sync_project.py <project_root> --write --strict --delivery-scope figures`。同步器检查 current required workbook set、`qX_plot.m` 的真实引用、正式图内无整体 `title/sgtitle` 和证据链；Gate=`not_required` 时不因合法缺少 03B workbook 失败，Gate=`required` 且 Figure 使用 03B 时则必须保持 fail closed。默认不要求导出图片已经存在。
