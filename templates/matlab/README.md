# HSK MATLAB 科研绘图模板（当前活动模板）

MATLAB 只读取 Python 两阶段输出的 accepted 工作簿与当前合法数据事实源，不重新求解、重新清洗、重新做敏感性或重新估计模型。每问唯一入口通用记为 `q{x}_plot.m`，问题一实例为 `q1_plot.m`，与主求解/深化分析脚本及工作簿同处 `问题X求解/`；活动模板与文档只使用这一标准命名。

MATLAB 的职责不是“把 Excel 画出来”，而是：

> **基于 Python 已验收的细粒度证据，完成 Scientific Evidence Visualization：科学视觉编码、组合表达、结构表达、全局—局部组织、统计/不确定性表达与论文证据强化。**

## 路径

```matlab
scriptPath = string(mfilename("fullpath"));
resultDir = string(fileparts(scriptPath));
solutionBook = fullfile(resultDir, "问题一求解结果.xlsx");
resultAnalysisBook = fullfile(resultDir, "问题一结果深化分析.xlsx");
```

主结果、状态、轨迹、约束、逐样本预测等读取 `solutionBook`；敏感性、稳定性、阈值、算法、结构、异质性等读取 `resultAnalysisBook`。不得跨问题读取临时 Excel、根据摘要数字反推数据或在 MATLAB 中重算核心结果。

## 实表读取

字段定位采用精确表头唯一匹配。允许登记期望列号作为结构漂移警告，禁止模糊匹配、别名猜测、相似字段回退和自动改变语义映射。

## Scientific Figure Synthesis Gate

正式绘图前先读取 Figure Contract 与 accepted 工作簿，识别 Evidence Structure：简单比较、分布、时间演化、空间结构、机制关系、约束/可行域、参数响应、不确定性、多目标、稳定/失效区域、网络流、调度、诊断、全局—局部。

不要先问“用 bar 还是 line”。先问：

```text
这条 Core conclusion 依赖什么结构？
当前工作簿实际保留了哪些状态/过程/样本/边界？
哪种视觉结构能把模型本身暴露出来？
```

正文核心图若最终只是 plain bar / plain line / plain scatter / plain box / plain histogram，必须经过 Basic-form Challenge。只有数据结构本身确实是一维简单比较时，才直接保留基础图。

## Composite Encoding Preference

若多个编码共享同一证据空间并共同回答一个 Primary question，优先组合：

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

组合图不是为了装饰，而是让原始样本、统计结构、模型关系、阈值/边界或不确定性同屏可验证。

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
- 主结果恢复高对比、中高饱和科研主色：亮蓝 `#1478FF`、鲜红 `#F04444`、亮绿 `#16B364`、亮橙 `#F79009`、亮紫 `#7A5AF8`；强比较优先亮蓝 vs 鲜红；
- 辅助对象、置信区间、背景带和参考元素使用深灰 `#252B37`、浅灰 `#E9EAEB` 或透明度降权；高对比不等于全图所有元素都鲜艳；
- 同一对象/语义在全文保持颜色一致；红绿不能承担唯一语义，需要 marker/linestyle/shape；
- 禁止 rainbow/jet 和无序彩虹；热图按连续变量语义选择 sequential/diverging colormap，并保留 colorbar 与单位；
- 默认 `grid off`；确需网格时保持浅、稀且位于数据后方；
- 默认保留可见图窗，不自动关闭，不创建图表子目录，不批量导出；
- 论文阶段人工确认后，按需导出到项目级 `figures/`。

## Portfolio Gate

所有单图完成后，再看整篇核心 Figure 集合。如果大量都是 plain bar / line / scatter，即使每张单独无错，也要检查：Python 是否只留摘要、Evidence Structure 是否被压扁、是否跳过 Synthesis/Rendering、是否可以组合编码/Local Zoom/合理拆图，以及机制/空间/动态/阈值/不确定性是否缺直接视觉证据。

不得设置“必须有 N 种图型”的机械多样性指标。

每张图的源工作簿、工作表、真实表头、脚本、论文 caption、Evidence level、Primary question、Evidence structure、Figure level、Selected visual structure、Composite encoding、Scientific Rendering Profile、Layout decision、Split decision、Enhancement / Enhancement rationale 和正文位置同步登记到 `模型论文框架.md`；默认不生成独立 `figure_evidence` 文件。

图表交付前执行 `python scripts/sync_project.py <project_root> --write --strict --delivery-scope figures`。同步器检查两个工作簿、`qX_plot.m` 的真实引用、正式图内无整体 `title/sgtitle` 和证据链；默认不要求导出图片已经存在。
