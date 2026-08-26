# Figure Enhancement Patterns

本文件只提供 `modules/04_figure_evidence.md` 中 Figure Enhancement Gate 的实现模式，不建立第二套绘图决策权威。是否启用 Enhancement、Evidence level、Primary question、布局、数据来源和视觉预算仍由 Module 04 决定。

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

适用：

- 最优方案的关键区间；
- 最差站点或高风险区域；
- 代表性样本；
- Pareto 推荐点附近；
- 约束即将激活的方案。

必须说明为什么选择该对象，不能只挑对结论有利的对象。

### Z4 ROI + semantic zoom

局部区域同时包含稳定区、风险区、可行区、阈值带或阶段边界时，在 zoom axes 中加入浅色 semantic band。

背景色只编码真实阈值/状态，不承担装饰作用。

## 2. Small Multiples

当多条曲线同轴叠加导致交叉、遮挡或 legend 搜索成本过高时，把对象拆成共享语义的小面板。

### 2.1 Stacked strips

推荐结构：

```text
对象 A ─────────────────
对象 B ─────────────────
对象 C ─────────────────
对象 D ─────────────────
                共享 x
```

规则：

- 跨 panel 比较幅度时统一 `xlim` 与 `ylim`；
- 只研究各自形态而允许自由 y 轴时，caption 必须明确说明；
- 纵向 stacked strips 只在最底部保留完整 x 轴标题；
- 每个 panel 只含一个主对象时优先 direct label，避免重复 legend；
- panel 间距要紧凑，使读者感知为一个 Figure；
- panel 背景可使用与主线同色系的极浅 tint，但主线必须保持更高对比。

### 2.2 Overview + detail

当既要比较对象之间的整体关系，又要看每个对象自身结构时，使用：

```text
总览 overlay
↓
若干 small-multiple detail panels
```

总览负责 between-series comparison；分面负责 within-series structure。两部分必须共享同一对象颜色映射。

### 2.3 Structured matrix

超过 4 个 panel 只有在 panel 本身构成参数 × 方法、场景 × 指标、时间 × 空间等规则矩阵时使用。

要求：

- 共享视觉语法；
- 同一行/列承担稳定含义；
- 尽量共享坐标范围；
- 不因 panel 数量增加而引入大量新的颜色与图型。

## 3. Focus Highlighting

适用于对象很多但核心判断只依赖少量对象。

推荐视觉层级：

```text
核心对象       中高饱和主色 + 主线宽
基准对象       深灰/次主色
上下文对象     浅灰/低透明度/细线
关键区间       轻量背景或边界
```

不得为了突出目标方案而删除不利对象或隐藏失败样本。

## 4. Semantic Background

背景带可以表示：

- 稳定区间；
- 风险等级；
- 可行/不可行区；
- 临界阈值带；
- 时间阶段；
- 政策阶段；
- 题面定义的健康/警戒状态。

建议使用低透明度 patch。主曲线、误差线、marker 和关键注释必须拥有更高视觉权重。

禁止：

- 没有数学或业务语义的彩色背景；
- 大面积高饱和填色；
- 背景色与核心对象颜色竞争注意力。

## 5. Composite Diagnostic

Composite Diagnostic 用多个 axes 围绕同一个统计对象组织证据，不要求规则 2×2。

### 5.1 回归/预测联合诊断

推荐结构：

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

可同时表达：

- 真实—预测关系；
- 训练/测试分层；
- 边际分布偏移；
- 残差结构；
- $R^2$、RMSE、MAE 等少量必要统计量。

训练集可降权为灰色，测试集或外部验证集作为重点色。统计量文字只保留直接支撑可信度判断的少量指标。

### 5.2 其他联合诊断

可按同一原则扩展：

- 分类：ROC / PR / calibration / confusion；
- 聚类：embedding / cluster size / silhouette / distance；
- 优化：Pareto / marginal objective distribution / constraint violation。

必须满足：多个 axes 共享一个 Primary question，而不是把互不相关的结果拼图。

## 6. Conditional 3D

3D 仅在第三维有真实含义时使用。

### 可考虑

- 两个真实因素 $x,y$ 与响应 $z=f(x,y)$；
- 三目标 Pareto 空间；
- 三维几何/空间场；
- 约束曲面与真实可行域；
- 双分类网格中柱高本身承担可验证响应。

### 优先降级

出现以下任一情况时优先 2D：

- 3D 只是把普通柱状图立体化；
- 透视导致远近误差或遮挡；
- 精确比较数值困难；
- 热力图/等高线/二维切片能更直接回答问题；
- 高度和颜色只是重复编码同一数值且没有额外结构收益。

必要时使用 3D 主图 + 2D 投影/切片作为补充。

## 7. Data Honesty

Figure Enhancement 不能改变结果语义。

- 离散实验点、独立场景点、离散参数扫描、迭代记录默认使用 marker + 直线段或真实离散表达；
- 不得仅为美观对离散点使用 spline、Bezier 等平滑并制造新峰谷或拐点；
- 只有连续函数、明确连续模型响应或 Python 已输出连续预测网格时才允许平滑连续曲线；
- inset、small multiples、background band、KDE 和 3D 都必须来自 Figure Contract 登记的数据源；
- KDE/密度估计属于统计显示，样本量不足或带宽选择会误导时改用 ECDF、直方图或原始点。

## 8. Annotation Budget

关键标注只保留极值、交点、阈值、推荐点、拐点或临界状态等不可替代位置。

默认建议：

- 单图关键数值标注通常不超过 3--5 个；
- 不给所有数据点贴标签；
- 标注与线条、marker、误差线不重叠；
- 需要大量精确数字时使用正文表格，而不是把图变成数据表。

## 9. MATLAB 实现提示

本节只提示实现工具，不改变 Gate：

- inset / detached axes：`axes('Position', ...)`；
- ROI：`rectangle` 或 `patch`；
- connector：`annotation('line', ...)` / `annotation('arrow', ...)`；
- semantic band：`patch` / `area` 并降低透明度；
- small multiples：`tiledlayout` + `nexttile`；
- direct label：在曲线末端附近使用 `text`；
- shared limits：显式统一 `xlim/ylim` 或 `linkaxes`；
- composite diagnostic：显式创建多个 axes，并按统计关系而非规则网格布置。

正式 `q{x}_plot.m` 仍须遵守 Module 04 的真实表头唯一匹配、MATLAB 不重算、默认保留图窗和不批量自动导出规则。
