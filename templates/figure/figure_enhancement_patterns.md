# Figure Enhancement Patterns

本文件只提供 `modules/04_figure_evidence.md` 中 Figure Enhancement Gate、Composite Encoding Preference 与 Scientific Rendering Profile 的实现模式，**不建立第二套绘图决策权威**。是否启用 Enhancement、Evidence level、Primary question、Evidence structure、布局、数据来源和视觉预算仍由 Module 04 决定。

## 1. Local Zoom

### Z1 Embedded inset

适用于局部证据简单、内嵌 axes 不遮挡主图核心信息的情况。

要求：

- 主图保留完整尺度与全局趋势；
- 主图用矩形、半透明 patch 或两条边界线标明 ROI；
- inset 使用与主图完全一致的颜色、线型、marker 和单位；
- inset 的 `xlim/ylim` 必须由真实 ROI 决定，不得任意截轴夸大差异；
- inset 通常只占主 axes 约 20%--35% 的视觉面积；
- 单个主图默认不超过 1 个 inset，确有两个独立关键局部时才例外。

### Z2 Detached zoom

当局部信息密集、需要完整坐标轴或 inset 会遮挡主图时，把放大区放在主图旁边作为独立 detail axes。

要求：

- ROI 与 detail axes 之间使用 connector 建立几何对应；
- detail axes 不承担新的一级结论，只放大同一 Primary question；
- 若主图和放大图的 y 轴范围不同，必须通过坐标刻度和 caption 清楚表达。

### Z3 Selective detail

总览包含多个对象，但局部只放大一个代表对象、最优对象、风险对象或临界对象。

适用：最优方案的关键区间、最差站点或高风险区域、代表性样本、Pareto 推荐点附近、约束即将激活的方案。

必须说明为什么选择该对象，不能只挑对结论有利的对象。

### Z4 ROI + semantic zoom

局部区域同时包含稳定区、风险区、可行区、阈值带或阶段边界时，在 zoom axes 中加入浅色 semantic band。背景色只编码真实阈值/状态，不承担装饰作用。

## 2. Small Multiples

当多条曲线同轴叠加导致交叉、遮挡或 legend 搜索成本过高时，把对象拆成共享语义的小面板。

### 2.1 Stacked strips

```text
对象 A ─────────────────
对象 B ─────────────────
对象 C ─────────────────
对象 D ─────────────────
                共享 x
```

规则：跨 panel 比较幅度时统一 `xlim` 与 `ylim`；只研究各自形态而允许自由 y 轴时 caption 必须明确说明；纵向 stacked strips 只在最底部保留完整 x 轴标题；每个 panel 只有一个主对象时优先 direct label；panel 间距紧凑；背景可用极浅 tint，但主线保持高对比。

### 2.2 Overview + detail

当既要比较对象之间整体关系，又要看每个对象自身结构时，使用“总览 overlay + 若干 small-multiple detail panels”。总览负责 between-series comparison；分面负责 within-series structure。两部分共享同一对象颜色映射。

### 2.3 Structured matrix

超过 4 个 panel 只有在 panel 本身构成参数 × 方法、场景 × 指标、时间 × 空间等规则矩阵时使用。要求共享视觉语法、稳定的行/列含义、尽量共享坐标范围，并避免 panel 增多时引入大量新颜色与图型。

## 3. Focus Highlighting

适用于对象很多但核心判断只依赖少量对象。

推荐视觉层级：

```text
核心对象       高对比、中高饱和主色 + 主线宽
基准对象       深灰/次主色
上下文对象     浅灰/低透明度/细线
关键区间       轻量背景或边界
```

不得为了突出目标方案而删除不利对象或隐藏失败样本。

## 4. Semantic Background

背景带可以表示稳定区间、风险等级、可行/不可行区、临界阈值带、时间阶段、政策阶段或题面定义状态。建议使用低透明度 patch。主曲线、误差线、marker 和关键注释必须拥有更高视觉权重。

禁止没有数学或业务语义的彩色背景、大面积高饱和填色、背景色与核心对象颜色竞争注意力。

## 5. Composite Diagnostic

Composite Diagnostic 用多个 axes 围绕同一个统计对象组织证据，不要求规则 2×2。

### 5.1 回归/预测联合诊断

```text
             边际分布 p(y)
       ┌──────────────────┐
       │ Histogram + KDE  │
       └──────────────────┘

       ┌──────────────────┐ ┌─────────┐
       │ observed vs pred │ │ p(pred) │
       │ + identity line  │ │         │
       └──────────────────┘ └─────────┘

       ┌──────────────────┐
       │ residuals        │
       └──────────────────┘
```

可同时表达真实—预测关系、训练/测试分层、边际分布偏移、残差结构以及少量必要统计量。训练集可降权为灰色，测试集/外部验证集作为重点色。

### 5.2 其他联合诊断

可扩展：分类的 ROC/PR/calibration/confusion；聚类的 embedding/cluster size/silhouette/distance；优化的 Pareto/marginal objective/constraint violation。多个 axes 必须共享一个 Primary question。

## 6. Composite Encoding Library

这些模式是在**同一证据空间**内叠加互补编码，优先用于把 raw data、统计摘要、边界和模型关系放在同一视图中。

### C1 Box + Raw Scatter

适用：组间分布、重复试验、鲁棒性、场景结果。

- box 表示 median/IQR/whisker；
- raw points 使用轻微 jitter，避免完全覆盖；
- 样本点颜色可统一为组色的浅化版本，box/median 使用更强主色；
- 小样本时 raw points 权重应高于密度估计；
- 若需要精确均值/区间，用额外 marker/errorbar，不把 box 含义改成均值。

### C2 Violin + Scatter + Median/Quartile

适用：样本量足以支持密度估计，且分布形状本身有证据价值。

- violin 只表达 KDE/density；
- raw scatter 保留真实样本；
- median/quartile 用明确 marker/line；
- KDE 带宽不得为“更好看”而制造虚假双峰/平滑结构；样本不足时退回 box+scatter 或 ECDF。

### C3 Line + Uncertainty + Event/Threshold

适用：时间/连续参数响应。

- 主线承担中心趋势；
- band 只表示真实 CI/PI/quantile/stability interval；
- threshold/event 使用清楚但较轻的线型；
- 关键点只标必要事件；
- band 透明度必须低于主线，不形成主视觉色块。

### C4 Scatter + Fit/Identity + CI

适用：预测、拟合、相关/响应关系。

- 原始散点必须可见；
- identity line 与 fitted line 语义不得混淆；
- CI/PI 必须来自合法统计计算；
- 若数据密度过高，优先 alpha scatter 或 density contour；
- 异常点只标少量真正改变结论的对象。

### C5 Heatmap + Contour + Boundary + Point

适用：双参数响应、稳定区/风险区、二维可行域。

- heatmap/colorbar 表示连续响应；
- contour 提供等值结构；
- feasible/failure boundary 使用独立线型；
- current/recommended point 使用高对比 marker；
- 不把分类主色直接硬套为连续 colormap。

### C6 Pareto + Recommendation + Global/Detail

适用：多目标优化。

- 全部 accepted candidate / feasible candidate 保留上下文；
- Pareto front/set 清楚区分；
- 推荐点使用高对比主色与独立 marker；
- 膝点或局部前沿差异被压缩时增加 Local Zoom；
- 不用几个目标柱状图替代真实目标空间。

### C7 Trajectory + Field + Boundary

适用：空间路径、物理机理、运动/调度状态。

- field/背景编码空间状态；
- trajectory/path 为主对象；
- boundary/obstacle/feasible region 保留真实几何；
- critical state 用少量高对比 marker/annotation；
- 颜色与几何编码不能重复造成误读。

### C8 Bar + Error + Benchmark / Bar + Line

仅在离散类别本身就是核心结构时使用。

- bar + error + benchmark 适合“类别中心量 + 真实不确定性 + 外部/基准阈值”；
- bar + line 只有两种量具有清楚联合语义时允许；
- 双 Y 轴默认谨慎，必须在 Figure Contract 说明量纲与为什么单轴/分图更差；
- 不能用组合柱图掩盖本来存在的时间、分布、空间或多目标结构。

## 7. Conditional 3D

3D 仅在第三维有真实含义时使用。

### 可考虑

- 两个真实因素 $x,y$ 与响应 $z=f(x,y)$；
- 三目标 Pareto 空间；
- 三维几何/空间场；
- 约束曲面与真实可行域。

### 优先降级

出现以下任一情况时优先 2D：3D 只是把普通柱状图立体化；透视导致远近误差或遮挡；精确比较困难；heatmap/contour/2D slices 能更直接回答问题；高度和颜色只是重复编码同一数值且没有额外结构收益。

必要时使用 3D 主图 + 2D contour projection / slice 作为补充。

## 8. High-density Scatter Patterns

点数量大且严重重叠时，不继续机械增加 marker size 或不透明度。

可选顺序：

1. alpha scatter；
2. binned/hexbin-like density；
3. 2D histogram；
4. density contour；
5. focus subset + gray context。

MATLAB 没有直接等价于所有 matplotlib 高阶接口时，可以用 `histcounts2` + `imagesc` / `pcolor` / `contourf` 构造可复现的密度证据，但不得改变原始样本和统计口径。

## 9. Data Honesty

Figure Enhancement 不能改变结果语义。

- 离散实验点、独立场景点、离散参数扫描、迭代记录默认使用 marker + 直线段或真实离散表达；
- 不得仅为美观对离散点使用 spline、Bezier 等平滑并制造新峰谷或拐点；
- 只有连续函数、明确连续模型响应或 Python 已输出连续预测网格时才允许平滑连续曲线；
- inset、small multiples、background band、KDE 和 3D 都必须来自 Figure Contract 登记的数据源；
- KDE/密度估计属于统计显示，样本量不足或带宽选择会误导时改用 ECDF、直方图或原始点。

## 10. Annotation Budget

关键标注只保留极值、交点、阈值、推荐点、拐点或临界状态等不可替代位置。单图关键数值标注通常不超过 3--5 个；不给所有数据点贴标签；标注不得压线；大量精确数字应进入表格而不是把图变成数据表。

## 11. MATLAB 实现提示

本节只提示实现工具，不改变 Gate：

- inset / detached axes：`axes('Position', ...)`；
- ROI：`rectangle` 或 `patch`；
- connector：`annotation('line', ...)` / `annotation('arrow', ...)`；
- semantic band：`patch` / `area` 并降低透明度；
- small multiples：`tiledlayout` + `nexttile`；
- direct label：曲线末端 `text`；
- shared limits：`xlim/ylim` 或 `linkaxes`；
- box + raw scatter：`boxchart` + `scatter`；
- violin：若使用自定义 kernel density 绘制，KDE 带宽与样本量必须在 Figure Contract/代码注释说明；
- heatmap + contour：`imagesc`/`pcolor` + `contour`；
- surface + projection：`surf` + `contour3`/底面 `contour`；
- uncertainty band：`patch` / `fill`；
- high-density 2D：`histcounts2` + `imagesc`/`contourf`；
- composite diagnostic：显式创建多个 axes，并按统计关系而非规则网格布置。

正式 `q{x}_plot.m` 仍须遵守 Module 04 的真实表头唯一匹配、MATLAB 不重算、默认保留图窗和不批量自动导出规则。
