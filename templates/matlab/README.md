# HSK MATLAB 科研绘图模板（当前活动模板）

MATLAB 只读取 Python 两阶段输出的两个标准工作簿，不重新求解。每问唯一入口通用记为 `q{x}_plot.m`，问题一实例为 `q1_plot.m`，与主求解/深化分析脚本及工作簿同处 `问题X求解/`；活动模板与文档只使用这一标准命名。

## 路径

```matlab
scriptPath = string(mfilename("fullpath"));
resultDir = string(fileparts(scriptPath));
solutionBook = fullfile(resultDir, "问题一求解结果.xlsx");
resultAnalysisBook = fullfile(resultDir, "问题一结果深化分析.xlsx");
```

主结果图读取 `solutionBook`；稳定性、阈值、算法或结构图读取 `resultAnalysisBook`。不得跨问题读取临时 Excel、根据摘要数字反推数据或在 MATLAB 中重算核心结果。

## 实表读取

字段定位采用精确表头唯一匹配。允许登记期望列号作为结构漂移警告，禁止模糊匹配、别名猜测、相似字段回退和自动改变语义映射。

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

基础图型和布局确定后，继续按 `modules/04_figure_evidence.md` 的 Figure Enhancement Gate 判断是否需要信息增强；默认 `Enhancement=none`。只有局部差异被压缩、多曲线遮挡、焦点对象需要降噪、存在真实阈值/阶段、多个统计视角共同回答同一诊断问题，或第三维确有数学/物理意义时，才启用 Local Zoom、Small Multiples、Focus Highlighting、Semantic Background、Composite Diagnostic 或 Conditional 3D。

具体 MATLAB 实现只参考 `templates/figure/figure_enhancement_patterns.md`，该模板不拥有独立决策权。Figure Contract 只登记 `Enhancement / Enhancement rationale`，不把 inset 坐标、透明度等实现参数写进项目语义合同。

## 图题与风格

- 正式论文图不设置整体 `title` 或 `sgtitle`；LaTeX/DOCX `caption` 承担正式图号和图名，多面板按需只保留 a/b/c/d 等 panel label；
- 本地探索阶段若临时使用调试标题，进入正式 `figures` 交付前必须移除，避免与论文 caption 重复；
- 白底、清晰细轴、中文坐标轴和单位，默认字号 18；
- 主色默认采用实体、低饱和、可区分的科研配色，例如深蓝 `#173B5E`、中蓝 `#375C87`、青绿 `#1E756B`、砖红 `#9A3838`、紫色 `#5D4B86`、棕灰 `#A98F70`；
- 辅助对象、置信区间、背景带和参考元素使用浅灰 `#D9DAD7`、深灰 `#20262E` 或透明度降权，不能让辅助元素压过主证据；
- 同一对象/语义在全文保持颜色一致；禁止彩虹色和无序多色轮换，热图按连续变量语义选择连续或发散色图；
- 默认 `grid off`；确需网格时保持浅、稀且位于数据后方；
- 默认保留可见图窗，不自动关闭，不创建图表子目录，不批量导出；
- 论文阶段人工确认后，按需导出到项目级 `figures/`。

每张图的源工作簿、工作表、真实表头、脚本、论文 caption、Evidence level、Primary question、Layout decision、Split decision、Enhancement / Enhancement rationale 和正文位置同步登记到 `模型论文框架.md`；默认不生成独立 `figure_evidence` 文件。

图表交付前执行 `python scripts/sync_project.py <project_root> --write --strict --delivery-scope figures`。同步器检查两个工作簿、`qX_plot.m` 的真实引用、正式图内无整体 `title/sgtitle` 和证据链；默认不要求导出图片已经存在。