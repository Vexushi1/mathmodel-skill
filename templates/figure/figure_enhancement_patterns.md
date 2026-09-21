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

规则：跨 panel 比较幅度时统一 `xlim` 与 `ylim`；只研究各自形态而允许自由 y 轴时 caption 必须明确说明；纵向 stacked strips 只在最底部保留完整 x 轴标题；每个 panel 只有一个主对象时优先 direct label；panel 间距紧凑；背景可按真实语义使用极浅 tint；主线与背景保持足够辨识度，颜色和线型沿用当前对象的语义映射。

### 2.2 Overview + detail

当既要比较对象之间整体关系，又要看每个对象自身结构时，使用“总览 overlay + 若干 small-multiple detail panels”。总览负责 between-series comparison；分面负责 within-series structure。两部分共享同一对象颜色映射。

### 2.3 Structured matrix

超过 4 个 panel 只有在 panel 本身构成参数 × 方法、场景 × 指标、时间 × 空间等规则矩阵时使用。要求共享视觉语法、稳定的行/列含义、尽量共享坐标范围，并避免 panel 增多时引入大量新颜色与图型。

## 3. Focus Highlighting

适用于对象很多但核心判断只依赖少量对象。

可通过颜色、线宽、线型、marker 或直接标注建立视觉层级；对当前判断不关键的上下文，可适当降低线宽或颜色强度。具体选择服从 Module 04 的逐图配色规则，不强制高饱和主色或全灰背景对象。

同等重要的比较对象保持可比的辨识度；关键区间用有真实依据的边界或轻量背景表达。不得为了突出目标方案而删除不利对象或隐藏失败样本。

## 4. Semantic Background

背景带可以表示稳定区间、风险等级、可行/不可行区、临界阈值带、时间阶段、政策阶段或题面定义状态。建议使用低透明度 patch。主曲线、误差线、marker 和关键注释必须拥有更高视觉权重。

禁止没有数学或业务语义的彩色背景、大面积高饱和填色、背景色与核心对象颜色竞争注意力。

## 5. Composite Diagnostic

Composite Diagnostic 仅在多个 axes 提供真实互补信息且组合更易读时，围绕同一个统计对象组织证据。一个 axes 已充分回答问题时保留单图；不要求规则 2×2、hero panel 或不对称布局。

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

这些模式是在**同一证据空间**内叠加互补编码的候选。仅选当前判断需要且已具备真实数据的组件，组合后还须更易读；模式名称中的加号不表示必须凑齐组件。相同 x/y 的线与点仍是一份证据；没有实际区间就不画带，没有真实配对就不画配对线。

### C1 Box + Raw Scatter

适用：组间分布、重复试验、鲁棒性、场景结果。

- box 表示 median/IQR/whisker；
- raw points 使用轻微 jitter，避免完全覆盖；
- 样本点颜色可统一为组色的浅化版本，box/median 使用更强主色；
- 小样本时 raw points 权重应高于密度估计；
- 若需要且已有真实均值/区间，用额外 marker/errorbar，不把 box 含义改成均值，也不为图型补估区间。

### C2 Violin + Scatter + Median/Quartile

适用：样本量足以支持密度估计，且分布形状本身有证据价值。

- violin 只表达 KDE/density；
- raw scatter 保留真实样本；
- median/quartile 用明确 marker/line；
- KDE 带宽不得为“更好看”而制造虚假双峰/平滑结构；样本不足时退回 box+scatter 或 ECDF。

### C3 Line + Uncertainty + Event/Threshold

适用：时间/连续参数响应。清楚的主线可独立支撑趋势结论；仅当真实区间、事件或阈值提供必要补充时组合。

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
- current/recommended point 使用可辨识的 marker 或直接标注，避免与色图背景混淆；
- 不把分类主色直接硬套为连续 colormap。

### C6 Pareto + Recommendation + Global/Detail

适用：多目标优化。

- 全部 accepted candidate / feasible candidate 保留上下文；
- Pareto front/set 清楚区分；
- 推荐点使用独立 marker 或直接标签；颜色沿用当前方案的语义映射；
- 膝点或局部前沿差异被压缩时增加 Local Zoom；
- 不用几个目标柱状图替代真实目标空间。

### C7 Trajectory + Field + Boundary

适用：空间路径、物理机理、运动/调度状态。

- field/背景编码空间状态；
- trajectory/path 为主对象；
- boundary/obstacle/feasible region 保留真实几何；
- critical state 用少量清楚可辨的 marker/annotation；
- 颜色与几何编码不能重复造成误读。

### C8 Bar + Error + Benchmark / Bar + Line

适用于离散类别比较。清楚的单独 bar 或 dot 可以承担核心结论；仅当真实误差、基准或第二种量提供必要补充时组合。

- bar + error + benchmark 适合“类别中心量 + 真实不确定性 + 外部/基准阈值”；
- bar + line 只有两种量具有清楚联合语义时允许；
- 双 Y 轴默认谨慎，必须在 Figure Contract 说明量纲与为什么单轴/分图更差；
- 不能用组合柱图掩盖本来存在的时间、分布、空间或多目标结构。

## 6A. Publication Rendering Pattern Library（C9--C16）

本节补充成熟论文图的**实现模式**，不改变 Module 04 的 Figure 决策权。所有 pattern 都必须先通过 Scientific Figure Synthesis、对应 Rendering Profile、Layout 与 Data Honesty Gate。

### C9 Multi-Metric Comparison Strip

适用：同一组方法/方案在 3 个及以上指标上比较，且指标单位或合理量程不同。

```text
Metric A │ Metric B │ Metric C │ Legend-only tile
```

实现要点：

- `tiledlayout(1, M + legendTile)`，每个 metric 独立 axes；
- 所有 panel 使用同一对象顺序、颜色、marker/hatch 语义；
- x/category label 若完全重复，可只在必要位置显示，不能靠缩小字号硬塞；
- 每个 y 轴保留真实单位，不使用多重 y-axis 把不同指标挤进一个 panel；
- shared/dedicated legend 只出现一次；
- 指标数量过多时优先拆 Figure 或 Evidence Matrix，不无限横向延伸。

### C10 Ordered Ablation Ladder

适用：模型/组件形成真实的有序嵌套序列，例如 baseline → +mechanism → +constraint → full model。

- 采用单 hue 的 lightness/saturation progression 表示递进关系；
- 误差/区间存在时必须保留 errorbar；
- 可以 horizontal bar / interval dot；
- 若候选方法并非嵌套，禁止用深浅暗示“完整度/等级”，改用普通 categorical palette。

### C11 Composition / Decomposition + Print-safe Encoding

适用：份额、概率、成本、能源、资源、流量来源等真实可加和构成。

- 绝对构成使用 stacked bar/area 时保留总量语义；百分比构成仅在分母明确时使用 100% stack；
- 颜色最多承担一级类别；hatch/edge/linestyle 仅在黑白打印或第二离散语义确有必要时加入；
- legend 应拆成“颜色语义”和“pattern 语义”两组或 dedicated tile，不做不可读的笛卡尔组合 legend；
- 分类过多时优先聚合有业务意义的尾部或使用 composition heatmap，不能随机分配十几种颜色。

### C12 Evidence Matrix + Marginal Context

适用：规则二维证据矩阵。

- `imagesc`/`heatmap` 负责连续或标准化主值；
- cell annotation 只在不会遮挡色块结构且精确值有阅读价值时显示；
- row/column 的 `n=`、total、baseline 只能来自工作簿真实字段；
- diverging 数据中心点必须有真实语义（0、基线差、目标差等）；
- 每列独立标准化时，在 caption/annotation 明确 `within-column normalized`，不能共享一个暗示跨列可比的 colorbar。

### C13 Milestone-aware Trend

适用：时序/连续参数中存在真实事件、阶段或关键里程碑。

推荐层级：

```text
context trajectory
+ primary line / interval
+ semantic phase band (optional)
+ event/milestone marker
+ 3--5 个关键 annotation
+ Local Zoom (only if needed)
```

事件线、箭头和阶段背景的时间/阈值必须绑定真实证据；普通采样点不得全部标注。

### C14 Normalized Multi-Criteria Radar

仅作为少量同向标准化指标的辅助综合画像，不是多指标比较默认图。

准入：

- 指标先统一“越大越好/越小越好”的方向；
- 半径使用清楚定义的 dimensionless normalized score；
- 通常 5--8 axes、比较对象不超过约 3 个；
- 原始指标值仍由表格、direct label 或正文提供；
- 不用多边形面积作为“综合性能更大”的定量证明；
- 轴多、对象多或精确比较优先 standardized dot / parallel coordinates / heatmap。

MATLAB 可用 `polaraxes` + 闭合曲线实现；若目标 MATLAB 版本/字体支持不足，必须可降级为 standardized dot/heatmap，而不是建立新硬依赖。

### C15 Density / Manifold / State-Space Evidence

适用：Monte Carlo、候选解云、嵌入、状态空间、粒子/轨迹分布。

- 原始/上下文样本以低视觉权重保留；
- 密度可由 `histcounts2` + `imagesc/pcolor/contour` 等可复现方法表达；
- 主轨迹/推荐路径/临界状态以可辨识的线型、marker 或显式颜色区分；
- density normalization 与 bandwidth/binning 不得改变结论；
- 点数不高时不要为了“高级”画 density，直接 raw scatter 更诚实。

### C16 Comparative Performance Matrix

适用：method × metric benchmark，同时需要展示原始值与相对 baseline 改善。

推荐：

- 主矩阵显示原始数值或统一可比较的 dimensionless score；
- best baseline / recommended method 用 edge/marker/annotation，而不是再叠一套高饱和颜色；
- improvement row/column 使用明确公式（如 relative improvement），并注明 higher/lower-is-better；
- 不同 metric 若独立归一化，颜色只表达列内排名/相对位置；原始数值文本负责精确比较。

## 6B. Publication Layout Patterns（L1--L3）

### L1 Dedicated Legend Tile

使用 `tiledlayout` 保留一个 `nexttile` 仅承载 legend，`axis off`。适用于共享 legend 很长、双重编码、或 legend 会显著压缩数据 axes 的场景。若 legend ≤3 项且 outside legend 已足够，不使用该模式。

### L2 Adaptive Canvas

画布尺寸由 panel 数、标签长度、legend 复杂度和目标宽高比决定。实现时可以在创建 `figure('Position',...)` 前根据这些离散结构参数选一个有限 profile（single / paired / metric-strip / matrix），不要根据数据值自动无限放大。

### L3 Open-axis Publication Frame

普通二维数据 axes 可从 `Box='off'`、`TickDir='out'`、frameless legend、`grid off` 起步。背景、网格与完整边框按当前读图需要选择；heatmap/3D/polar/边界图保留必要空间参照。使用基础样式后再设置当前图的局部网格、边框等属性，避免后续样式调用覆盖手调值。该模式只控制渲染，不更改 x/y limit 与数据范围。

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
- 只有连续函数、明确连续模型响应或 求解实现已输出连续预测网格时才允许平滑连续曲线；
- inset、small multiples、background band、KDE 和 3D 都必须来自 Figure Contract 登记的数据源；
- KDE/密度估计属于统计显示，样本量不足或带宽选择会误导时改用 ECDF、直方图或原始点。

## 10. Annotation Budget

关键标注只保留极值、交点、阈值、推荐点、拐点或临界状态等不可替代位置。单图关键数值标注通常不超过 3--5 个；不给所有数据点贴标签；标注不得压线；大量精确数字应进入表格而不是把图变成数据表。

## 11. MATLAB 实现提示

本节只提示实现工具，不改变 Gate。颜色、字号、数据线宽、轴线宽、网格与边框在脚本参数区集中设置，不建立所有图共用的固定外观。线条、散点和色块按其支持的 `Color`、`FaceColor`、`EdgeColor` 等属性显式给出当前图的 RGB；连续场显式选择 colormap。具体 SCI / Nature 论文的配色可作为参考，不对应仓库默认值或统一官方色板。

样式接口的调用顺序：

1. 按已验收数据创建图形对象、坐标标签、legend/colorbar，并显式赋予当前图选择的颜色与数据线宽；
2. 调用一次 `hsk_apply_scientific_style(fig, "", style)`，应用基础字体和框架；`style` 可集中设置 `fontName`、`axesFontSize`、`labelFontSize`、`legendFontSize`、`colorbarFontSize`、`axesLineWidth`、`colorbarLineWidth`，未提供字段使用 helper 的排版起点；
3. 再对需要区别处理的 axes、legend 或 colorbar 设置局部字号、网格、边框等；这些属性不放入未支持的 `style` 字段，也不在覆盖后再次套用基础样式。

无 profile 的 `hsk_publication_profile()` 返回空 palette；`hsk_apply_scientific_style(fig)` 只做基础排版且同样返回空 palette。两者都不替脚本选择数据颜色，样式 helper 也不设置 `ColorOrder`、colormap 或背景色。若确实选用既有候选，可显式调用 `spec = hsk_publication_profile("journal_balanced")`，再把 `spec.palette.series` 中选定的 RGB 赋给对应对象。`competition_high_contrast` 与 `monochrome_print` 也保留这种显式调用方式；它们是兼容候选，不是必选项。

其他实现工具：

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

正式 `q{x}_plot.m` 仍须遵守 Module 04 的真实表头唯一匹配、绘图代码不重算、默认保留图窗和不批量自动导出规则。

## 12. 按数据结构选择的绘图技巧

按当前结论只读需要的小节。这里补充“适用证据、可调参数、常见错误”和三个原创 MATLAB 片段，不另建 Figure Authority，不新增每问必交文件；图型选择仍服从 Module 04。

所有数值、对象键、单位、区间含义、顺序和可用来源均绑定 accepted 工作簿的精确唯一表头；03B 仅在当前图确实使用已验收分析证据时读取。代码前先完成既有 reader 的有限值、缺测和键检查，不用片段替代输入合同。这里只画已存在的结果，不计算置信区间、拟合或平滑，不补值、不重算 Pareto 前沿，也不为效果添加模拟样本。

配色没有默认。`seriesColors` 由当前脚本明确提供为 N×3 RGB：配对片段至少两行，趋势片段至少一行，矩阵片段至少两行连续色图；值须为有限实数且在 `[0,1]`。SCI/Nature 风格只能作为候选参考，不能替代顺序、发散或类别语义。`figureSizeCm` 为两个有限正数组成的行向量；`axesFontSize`、`labelFontSize`、`legendFontSize` 均为显式配置的有限正数。`fontName` 为用户本机可用、支持当前中文标签的非空字体名，统一传给坐标轴、轴标签、图例和 colorbar；不依赖 MATLAB 默认字体，也不在片段末尾调用 helper 覆盖用户设置。所有片段保留可见图窗，无整体 title/sgtitle，不自动导出或关闭。

### 12.1 排序比较与区间点图

**何时用：** 比较同口径对象的大小、排名或真实区间；长名称优先横向点图。只有中央估计时只画点，不因图型名称而补区间。

**可调参数：** 排序字段与方向、并列时的真实次序、点大小、区间线宽、对象间距、横轴范围、显示精度和长标签换行。排序只作用于展示索引，同一个索引同时作用于名称、键、点值和区间上下界；不能分别排序各列。指标“越大越好／越小越好”写在轴或 caption 中。

**常见误用：** 把条形截轴造成的视觉长度当数值差距；区间单位或置信水平不一致却直接比较；只留下前几名而隐去失败对象。条形通常保留零基线；点图可聚焦实际范围，但刻度、范围与 caption 应清楚，不靠夸大坐标制造优势。

### 12.2 真实键配对的前后变化

**何时用：** 同一对象在前后时点、两种真实条件或两次测量中的变化。哑铃两端必须绑定同一个 accepted 对象键；完全不同的方法列表用普通比较图。

**可调参数：** 两端颜色和 marker、连接线的颜色与宽度、点大小、对象显示顺序、轴范围、标签密度及图例位置。两端单位和指标定义相同；若方向含义没有真实依据，不自动把某端编码为“改善”。

**常见误用：** 根据 Excel 行号连线；两端各自排序后连线；静默取键交集，丢掉未配对对象。下面的简例明确要求完整一一配对；不满足时停止，单独说明未配对对象，不自动删记录。

前置字段：`beforeKey / afterKey` 为非空字符串列向量，每项已经首尾空白规范化且非空、无 missing；`beforeValue / afterValue` 为同单位有限实数列向量，分别与各自键等长。`displayNames` 是与 `beforeKey` 等长、同顺序的真实对象名；`phaseLabels` 是两个非空真实条件名，`valueAxisLabel` 含指标和单位。`connectorColor` 为一行合法 RGB，`connectorWidth / pointSize` 为显式有限正数，`pointSize` 是 scatter 的面积参数。若要改变显示次序，同一展示索引必须同步作用于名称、before 键值及按键匹配后的 after 值。

```matlab
assert(numel(unique(beforeKey)) == numel(beforeKey) && ...
    numel(unique(afterKey)) == numel(afterKey), "配对键必须唯一");
[matched, afterRow] = ismember(beforeKey, afterKey);
assert(all(matched) && numel(beforeKey) == numel(afterKey), ...
    "两端必须是同一对象集合，不能静默取交集");
afterMatched = afterValue(afterRow);
n = numel(beforeKey);
fig = figure("Visible", "on", "Color", "w", "Units", "centimeters", ...
    "Position", [2, 2, figureSizeCm]);
ax = axes(fig); hold(ax, "on");
for i = 1:n
    plot(ax, [beforeValue(i), afterMatched(i)], [i, i], ...
        "Color", connectorColor, "LineWidth", connectorWidth, ...
        "HandleVisibility", "off");
end
hBefore = scatter(ax, beforeValue, (1:n)', pointSize, seriesColors(1,:), "filled", "Marker", "o");
hAfter = scatter(ax, afterMatched, (1:n)', pointSize, seriesColors(2,:), "filled", "Marker", "s");
set(ax, "YTick", 1:n, "YTickLabel", displayNames, "YDir", "reverse", ...
    "FontName", fontName, "FontSize", axesFontSize);
ylim(ax, [0.5, n + 0.5]);
xlabel(ax, valueAxisLabel, "FontName", fontName, "FontSize", labelFontSize);
legend(ax, [hBefore, hAfter], phaseLabels, "Location", "best", ...
    "Box", "off", "FontName", fontName, "FontSize", legendFontSize);
```

两端用不同 marker 辅助颜色辨识；`pointSize` 调节标记面积，而不是直径。[MATLAB scatter](https://www.mathworks.com/help/matlab/ref/scatter.html)

### 12.3 趋势、稀疏 marker 与真实区间

**何时用：** 时间或连续参数的真实响应。先保证主线易读；区间只有确有来源、含义明确且帮助当前判断时才加。多条同等重要曲线保持相当的视觉权重，不能任意灰化对照。

**可调参数：** 线宽、marker 大小及间隔、真实区间透明度、轴范围、末端标签与图例位置。稀疏 marker 仅减少标记数量，主线仍使用全部原始行；阈值和事件只标注有题面或工作簿依据的位置。

**常见误用：** 先删除 NaN 再连线；把全部有限区间点拼成一个跨缺口的 polygon；平滑掉尖峰；拿同一 x/y 的线与点做两个图例对象。

前置字段：`x / y / lower / upper` 为非空、等长、同键同顺序的实数列向量，中心值和上下界使用相同单位；`x` 有限且严格递增，缺测行按合同保留，`y / lower / upper` 中允许的缺测为 NaN，Inf 已由 reader 拒绝。片段针对一个已确认的连续采样段；若真实时间中存在断档、不同轨迹或重启段，必须按 accepted 的时间／段标识先分段调用，不能仅凭邻接行推断连续。上下界成对存在，每个有效区间须有当前中心值；中心值存在而区间缺测时，保留主线并断开区间带。`markerEvery` 为有限正整数，`bandAlpha` 为 `[0,1]` 内的有限实数，`lineWidth / markerSize` 为有限正数；`xAxisLabel / yAxisLabel` 含真实指标和单位，`seriesLabel` 为真实对象名。caption 说明区间是 CI、PI、分位区间还是其他已验收范围及其水平。

```matlab
assert(all(isfinite(x)) && all(diff(x) > 0), "x 必须有限且严格递增");
assert(isequal(isfinite(lower), isfinite(upper)), "区间两端须成对有效");
bandOK = isfinite(lower) & isfinite(upper);
assert(all(lower(bandOK) <= upper(bandOK)) && all(isfinite(y(bandOK))), ...
    "有效区间须有正确上下界和中心值");
first = find(bandOK & [true; ~bandOK(1:end-1)]);
last = find(bandOK & [~bandOK(2:end); true]);
fig = figure("Visible", "on", "Color", "w", "Units", "centimeters", ...
    "Position", [2, 2, figureSizeCm]);
ax = axes(fig); hold(ax, "on");
for k = 1:numel(first)
    rows = first(k):last(k);
    if numel(rows) >= 2
        fill(ax, [x(rows); flipud(x(rows))], ...
            [lower(rows); flipud(upper(rows))], seriesColors(1,:), ...
            "FaceAlpha", bandAlpha, "EdgeColor", "none", "HandleVisibility", "off");
    else
        plot(ax, [x(rows), x(rows)], [lower(rows), upper(rows)], ...
            "Color", seriesColors(1,:), "HandleVisibility", "off");
    end
end
finiteMask = isfinite(y);
finiteRows = find(finiteMask);
assert(~isempty(finiteRows), "没有可展示的中心值");
isolatedRows = find(finiteMask & ~[false; finiteMask(1:end-1)] & ...
    ~[finiteMask(2:end); false]);
markerRows = unique([finiteRows(1:markerEvery:end); finiteRows(end); isolatedRows]);
hLine = plot(ax, x, y, "Color", seriesColors(1,:), "LineWidth", lineWidth, ...
    "Marker", "o", "MarkerSize", markerSize, "MarkerIndices", markerRows);
set(ax, "FontName", fontName, "FontSize", axesFontSize);
xlabel(ax, xAxisLabel, "FontName", fontName, "FontSize", labelFontSize);
ylabel(ax, yAxisLabel, "FontName", fontName, "FontSize", labelFontSize);
legend(ax, hLine, seriesLabel, "Box", "off", ...
    "FontName", fontName, "FontSize", legendFontSize);
```

这里 `bandOK` 只寻找原行序列中连续有效的区间段，不生成压缩后的跨缺口序列；孤立区间绘为竖线，不假造带宽。`plot` 保留 `y` 的 NaN 行产生断线，`MarkerIndices` 只改变 marker 位置；缺测之间或端部的孤立有限点强制进入 `markerRows`，避免没有线段且被稀疏标记隐藏。[MATLAB plot](https://www.mathworks.com/help/matlab/ref/plot.html)、[Line properties](https://www.mathworks.com/help/matlab/ref/matlab.graphics.chart.primitive.line-properties.html)、[fill](https://www.mathworks.com/help/matlab/ref/fill.html)

### 12.4 原始点与 ECDF 分布

**何时用：** 结论涉及样本异质性、尾部、分位数或失败比例。小样本直接展示原始点；需要累计比例时使用 accepted 的 ECDF 节点。箱线、密度或拟合分布不是每张分布图的必需组件。

**可调参数：** 点大小、透明度、类别轴上的轻微错位、类别间距、共同数值轴、累计比例刻度。错位只作用于类别轴，不移动真实数值轴；保持全部有效样本、真实样本量和失败／缺测说明。ECDF 节点由已验收来源提供时用阶梯表达，不在 MATLAB 追加区间估计或拟合。

**常见误用：** 把确定性方案当独立随机重复；为了云图均匀而删掉重合点或极端值；类别错位改变数值；缺少足够样本仍用平滑密度暗示精确形状。原始点或 ECDF 已清楚支持结论时就保留简单图。

### 12.5 多方案多指标矩阵

**何时用：** 同一对象集合有多项指标，需要同时判断各指标位置。不同单位的列可以共享行顺序，但不能共用一个未经解释的原始值色标。

**可调参数：** 行顺序、指标分组、单元格长宽、列间距、每列真实单位与色限、必要的数值标注及其精度。数值标注只改显示层；字色与底色需人工检查。已做归一化时必须说明基准、方向、范围和实际值来源，不把不同列同色解释成绝对值相等。

**常见误用：** 用不同单位的最大值统一映射颜色；每列独立拉伸后声称跨列差距可比较；常数列也制造强烈渐变；文字颜色与深色单元格混在一起。

下面以每指标一条窄矩阵、独立 colorbar 展示，数据仍为原始 accepted 数值。前置字段：`values` 为非空有限实数二维矩阵，所有列使用同一完整对象键和行序，不能按各表行号拼接或静默取键交集。`methodLabels` 与行数等长；`metricLabels / metricUnits` 与列数等长，均为无 missing 的真实文本标签；不含未说明的数值缺测。`metricLimits` 为指标数×2 的有限实数矩阵，每行严格递增且覆盖对应列全部展示值；同一指标跨图比较时沿用可比范围，不为每张图重新拉伸。本简例各列使用语义相容的同一顺序色图 `seriesColors`；需要不同的顺序／发散语义时应逐列显式选色或分图，不能机械共用色图。caption 写明颜色只在各指标自身尺度内解释；没有共同单位或规范化定义时不做跨列颜色大小判断。

```matlab
assert(~isempty(values) && isreal(values) && all(isfinite(values), "all"), ...
    "本简例需要非空有限原始值");
fig = figure("Visible", "on", "Color", "w", "Units", "centimeters", ...
    "Position", [2, 2, figureSizeCm]);
tiles = tiledlayout(fig, 1, size(values,2), "TileSpacing", "compact", "Padding", "compact");
for j = 1:size(values,2)
    limits = metricLimits(j,:);
    assert(all(isfinite(limits)) && limits(1) < limits(2), "需显式有效色限");
    assert(all(values(:,j) >= limits(1) & values(:,j) <= limits(2)), ...
        "色限不能静默截掉当前指标值");
    ax = nexttile(tiles);
    imagesc(ax, values(:,j));
    colormap(ax, seriesColors);
    caxis(ax, limits);
    set(ax, "XTick", [], "YTick", 1:size(values,1), ...
        "YTickLabel", methodLabels, "FontName", fontName, "FontSize", axesFontSize);
    xlabel(ax, metricLabels(j), "FontName", fontName, "FontSize", labelFontSize);
    cb = colorbar(ax);
    set(cb, "FontName", fontName, "FontSize", legendFontSize);
    set(cb.Label, "String", metricUnits(j), "FontName", fontName, "FontSize", labelFontSize);
end
```

片段使用 `caxis` 兼容所选 R2021a 语法基线；新版 MATLAB 将该接口名改为 `clim`，其含义都是设置颜色映射范围，不修改数值。[MATLAB colormap limits](https://www.mathworks.com/help/matlab/ref/clim.html)

### 12.6 空间场、Pareto 与真实基准消融

**何时用：** 结论确实涉及空间位置、边界、权衡或组件贡献。空间场必须有真实坐标和字段；Pareto 需要完整候选及已验收前沿／可行性标志；消融需要真实基准与已执行的变体。

**可调参数：** 空间纵横比例、共同色限、有物理含义的等值线、边界与路径线宽；候选点大小、前沿线宽、推荐点形状；消融的基准标识、差值方向、零参考线和显示精度。仅对同单位、同口径的空间图共享尺度；推荐点和前沿保留真实语义。

**常见误用：** 从摘要反推连续场；插值生成未经计算的“高分辨率”细节；只保留 Pareto 最优点而隐藏候选、不可行或失败状态；在绘图入口重新算前沿；把独立方法排序包装为逐级嵌套消融。消融差值直接读取已验收差值字段，并标明真实 baseline，不能以任意方法当暗含基准。

### 12.7 片段的使用边界

三个片段不自带示例数据，不能直接当作已经实例化的完整脚本。实际使用时先绑定相应字段、顺序和显式样式参数，再合入现有 `qX_plot.m`／`data_process.m` 的对应绘图段；无需额外正式文件。无某类证据就不用该片段，不补占位区间或无意义 panel。

这些片段仅供静态阅读与实例化参考；不生成效果图，不执行 MATLAB，不宣称可运行性或审美已经验收。最终字号、色彩观感、标签、图例位置和导出效果由用户在本机 MATLAB 调整。解析工具、语言版本与具体结果在交付记录中单独报告。
