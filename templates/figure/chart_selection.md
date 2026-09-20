# 结果图型选择索引

图型由“要证明的结论”、底层数据结构和信息展示效率共同决定，不按软件默认、图型新奇度或固定禁用清单选择。每张图先填写结果图 Figure Contract，确定 DOCX/LaTeX 正式图注及其证据职责，再查本表；正式论文图不设置冗余整体 `title` / `sgtitle`。

本索引按 **Evidence Structure → Scientific Visual Structure** 查找候选。先判断当前结论需要哪些关系，再选择直接、清楚的表达；不因工作簿还有更多维度便强制增加编码，也不把必要的时间、空间、分布、约束或多目标关系压成汇总数。基础图可以承担核心证据。

## 可选视觉参考

只有图型选择或多面板布局需要外部视觉对照时，才按 `assets/figure_assets.yaml` 加载对应资产。图集不提供数据、结论或固定配色，不能替代工作簿、Figure Contract、`模型论文框架.md` 和 `q{x}_plot.m`。

需要具体绘制方法时，按需查 [绘图技巧第 12 节](figure_enhancement_patterns.md#12-按数据结构选择的绘图技巧)：12.1 排序与区间点图、12.2 真实键配对、12.3 趋势与真实区间、12.4 原始点与 ECDF、12.5 多指标矩阵、12.6 空间/Pareto/真实基准消融。每节同时说明适用证据、可调参数和误用边界；不要求每张图组合这些技巧。

## Scientific Figure Synthesis 快速索引

| Evidence Structure | 可选科学视觉结构 | 须避免的信息遗漏 | 需要检查的底层数据 |
|---|---|---|---|
| 简单离散比较 | dot / sorted dot / bar；有真实区间或基准时按需补充 | 未说明比较对象、口径或必要基准 | 对象、指标；区间/基准仅在真实存在时使用 |
| 分布 | raw scatter、box、ECDF；必要时组合分位数或密度 | 结论涉及分布尾部或异质性却只展示均值 | 逐样本值、组别、样本量、分位数 |
| 时间演化 | line / state trajectory；必要时补真实区间、事件或 detail | 关键时间关系、状态切换或局部差异不可辨 | 时间、状态；区间/事件/阶段按结论需要检查 |
| 空间结构 | spatial field+path+boundary、节点/流量高亮 | 位置、路径或边界关系被区域均值遮蔽 | 坐标、节点/网格值、路径、边界 |
| 机制关系 | trajectory+critical state、phase/response relation | 结论所需状态关系或临界条件缺失 | 机制变量、状态量、临界点/边界 |
| 约束/可行域 | feasible region+boundary+recommended point、violation structure | 可行边界或违反位置被数量汇总遮蔽 | 约束值、容差、变量、可行状态 |
| 参数响应 | curve / heatmap；按需补真实阈值、contour 或 operating point | 结论所需响应关系或失效边界缺失 | 参数网格、响应、阈值、可行状态 |
| 不确定性 | interval、raw points、ECDF、quantile band；按需组合 | 区间含义、失败样本或尾部风险未说明 | 重复/场景结果、分位数、失败标记 |
| 多目标权衡 | candidates + Pareto；推荐点、可行状态或 zoom 按需补充 | 各目标关系和权衡不能直接判断 | 全部候选方案、各目标、推荐点 |
| 稳定/失效区域 | response；有真实边界时补 threshold / semantic background | 缺失“稳定”的判据、范围或失效条件 | 扫描点、状态/策略、失效标记 |
| 网络/流 | network+weighted flow+focus highlighting | 结论所需连通关系或流向缺失 | 节点、边、权重、流量、路径 |
| 调度/资源 | Gantt；占用或冲突结构按需补充 | 任务时间、资源关系或冲突被总量遮蔽 | 作业、资源、起止、占用/冲突 |
| 预测/诊断 | observed-vs-predicted / residual；CI 或 marginal 按需组合 | 结论所需误差结构或验证条件未显示 | 逐样本真实/预测/残差/区间 |
| 全局—局部 | global view + Local Zoom / detached detail | 局部判别缺少全局尺度和位置上下文 | 全局序列、ROI、临界/局部状态 |

## Composite Encoding 快速索引

多个编码共享同一证据空间并共同回答一个 Primary question，且有真实互补信息和可读性增益时，才考虑组合。以下模式按需选用，不是必须凑齐的组件：

- `box + raw scatter`；
- `violin + raw scatter + median/quartile`；
- `line + CI / prediction interval`；
- `scatter + fit/identity + CI`；
- `scatter + marginal histogram/KDE`；
- `bar + errorbar + benchmark`；
- `bar + line`（仅在联合语义明确且双轴不会误导时）；
- `heatmap + annotation / contour / feasible boundary`；
- `Pareto + recommendation + Local Zoom`；
- `trajectory + field + boundary`；
- `3D surface + 2D contour projection`（仅第三维真实且 2D 损失结构时）。

组合图应保留当前结论需要的真实样本、统计结构、阈值/边界或模型关系。相同 x/y 的线与点仍是一份证据；没有实际区间不画带，没有真实配对不画配对线。

## Scientific Rendering Profile 快速索引

| Profile | 按证据选用的元素 | 典型用途 |
|---|---|---|
| Distribution | raw points + box/violin/ECDF + median/quantile | 分组、鲁棒性、重复试验 |
| Regression / Prediction | scatter + identity/fit + CI + residual/marginal | 预测、拟合、分类概率诊断 |
| Dynamic | trajectory + interval + event/threshold + zoom | 时序、状态演化、控制过程 |
| Parameter Surface | heatmap + contour + point + feasible boundary | 参数敏感性、双因素响应 |
| Spatial | field + path/flow + node + boundary + colorbar | 选址、路径、覆盖、空间残差 |
| Optimization / Pareto | candidates + Pareto + feasible state + knee/recommendation | 单/多目标优化、方案选择 |
| High-density Scatter | alpha scatter / binned density / 2D density contour | 大样本仿真、预测、候选解云 |

## Publication Rendering 候选补充

在 `Evidence Structure → Scientific Visual Structure` 已确定后，可按下列结构进入 publication rendering pattern；这些是候选索引，不建立新 Authority。

| 证据结构 | 新候选结构 | 关键准入条件 |
|---|---|---|
| 同对象多指标 benchmark | Multi-Metric Comparison Strip + shared/dedicated legend | 指标量纲/量程不同但对象集合一致；跨 panel 保持对象语义 |
| 有序组件增量 | Ordered Ablation Ladder | 必须是真实嵌套/递进，不得给独立方法制造等级感 |
| 可加和构成 | Composition / Decomposition + print-safe encoding | 总量/分母定义清楚，颜色与 hatch 不过载 |
| 规则二维矩阵 | Evidence Matrix + marginal context | cell/marginal 值来自真实证据；normalization 可解释 |
| 带真实事件的动态过程 | Milestone-aware Trend | event/phase/milestone 有题面或工作簿事实来源 |
| 少量标准化多指标画像 | Normalized Multi-Criteria Radar | 方向统一、归一化明确、通常 5--8 轴且对象很少 |
| 状态空间/候选解云 | Density / Manifold / State-Space | density 只辅助，不隐藏原始样本/关键状态 |
| method × metric performance | Comparative Performance Matrix | 原始值与相对改善语义分离，列独立 normalization 不伪装跨列可比 |

`Palette profile / open-axis / adaptive canvas / legend strategy` 属于渲染实现层；图型选择仍以 Module 04 的 Core conclusion 与 Evidence Structure 为先。

## Figure Enhancement 快速索引

基础科学视觉结构和布局确定后，按 `modules/04_figure_evidence.md` 的 Figure Enhancement Gate 判断是否需要增强；具体实现模式见 `templates/figure/figure_enhancement_patterns.md`。

| 当前视觉问题 | 优先增强 | 典型用途 |
|---|---|---|
| 全局尺度压缩关键差异、交点或阈值 | Local Zoom | 临界点、Pareto 膝点、局部误差、关键时间窗 |
| 多条曲线大量交叉、遮挡、图例搜索成本高 | Small Multiples | 多算法、多区域、多对象时序、参数组曲线 |
| 对象很多但核心判断只依赖少量对象 | Focus Highlighting | 推荐方案 vs 基准、关键站点、代表性样本 |
| 存在稳定区、风险区、可行区、阶段区间 | Semantic Background | 参数敏感性、鲁棒性、阈值、状态分类 |
| 中心关系、边际分布和残差共同回答可信度 | Composite Diagnostic | 回归、预测、分类、聚类、优化诊断 |
| 第三维具有真实结构且二维会损失信息 | Conditional 3D | 双因素响应、三目标 Pareto、空间场、约束曲面 |

Enhancement 默认是 `none`。若增强后不能增加可验证信息、降低视觉搜索成本或强化关键证据，则不使用。

## 题型候选索引

| 证据任务 | 常用候选 | 有额外信息收益时的候选 | 主要准入条件与风险控制 |
|---|---|---|---|
| 方案/类别数值比较 | dot、排序点图、bar；真实区间/基准按需补充 | dumbbell、slopegraph、少量类别比例图 | 清楚的基础图可承担核心结论；配对变化须有真实配对关系 |
| 时间趋势与预测 | line、真实—预测、残差时序；真实 interval 按需加入 | Small Multiples、Local Zoom、状态阶段背景 | 多线遮挡优先分面；不能用平滑掩盖误差 |
| 参数敏感性 | 参数—响应+基准/阈值、tornado、heatmap+contour | Local Zoom、Semantic Background、3D response surface | 论证稳定范围或失效边界时须展示相应真实证据；单纯响应趋势可以用清楚曲线 |
| 鲁棒性与扰动 | box/violin+raw points、ECDF、quantile interval | raincloud、Small Multiples、threshold background | 结论涉及尾部、失败场景或分布差异时须保留相应证据，不能只展示均值 |
| 多算法比较 | performance profile、error-time scatter、interval dot | Small Multiples、Focus Highlighting、parallel coordinates | 按当前比较判断选图；实例/重复、时间和可行性中有必要的信息不得遗漏 |
| 排名稳定性 | rank heatmap、slopegraph、Top-k overlap | Focus Highlighting、ranking flow | 不把名次变化压成平均名次柱状 |
| 分布差异 | ECDF、box/violin+raw points | Composite Diagnostic、ridge/raincloud | 高级分布图必须保留样本量与可核对统计量 |
| 相关性与变量结构 | correlation matrix、scatter matrix、loadings | Composite Diagnostic、network | 不得由相关直接宣称因果 |
| 空间分布 | spatial field、local statistic、spatial residual | Focus Highlighting、3D surface/flow field | 投影、坐标、单位和 colorbar 正确 |
| 路径与网络 | path highlight、weighted flow、adjacency heatmap | Focus Highlighting、Sankey/3D network | 控制节点和边数量，避免毛线团 |
| 调度与资源占用 | Gantt+resource step、conflict matrix | Semantic Background、resource flow | 高级图不能替代可行性检查 |
| 多目标权衡 | Pareto+recommendation、parallel coordinates | Local Zoom、3D Pareto | 推荐点/膝点可局部放大；三目标才考虑 3D |
| 约束与可行域 | feasible region、critical boundary、violation points | Local Zoom、Semantic Background、3D feasible surface | 必须标明边界和可行侧，不替代约束检查表 |
| 模型拟合与诊断 | observed-vs-fit+identity、residual、calibration | Composite Diagnostic、Local Zoom | 高级图必须提升异质性/局部结构识别，不只报 $R^2$ |
| 构成比例与层级 | sorted/stacked bar、treemap | sunburst、Sankey | 饼图仅少量类别且整体口径明确 |
| 多指标画像 | parallel coordinates、standardized dot、heatmap | Focus Highlighting、radar | 雷达图仅少量同向标准化指标 |

## 核心证据覆盖检查

按核心结论检查必要关系和适用边界是否有图或表证据，并检查重复图和重复 panel。连续多张 plain bar / plain line / plain scatter 本身不构成问题；已有证据充分时保留。发现必要信息缺口时，回到 current 合法工作簿集合检查真实状态、时间、空间、分布、阈值、不确定性或逐样本记录，再判断是否需要改变表达。

只有必要证据被汇总而无法支持当前结论时，才检查 Python 是否遗漏本次运行真实产生的 Evidence Capture；MATLAB 不自行重算或伪造底层序列。

## 权威边界

本文件只负责候选图型与视觉问题索引；在当前版本中同时给出 Evidence Structure 与 Scientific Rendering Profile 的候选映射，但不维护通用绘图政策。通用信息效率判定、Evidence level、Primary question、Scientific Figure Synthesis Gate、Basic-form Challenge、Composite Encoding Preference、Figure Layout Gate、Figure Enhancement Gate、视觉注意力预算、正式图内标题策略、论文 caption、配色、数据诚实、Portfolio Gate、删除规则和入文闭环统一服从 `modules/04_figure_evidence.md`；Enhancement 的 MATLAB 实现模式只参考 `templates/figure/figure_enhancement_patterns.md`。

表格中的准入条件只用于提示某类候选视觉结构的局部风险，不构成第二套通用规则。若本文件与 Module 04 存在任何不一致，以 Module 04 为准。
