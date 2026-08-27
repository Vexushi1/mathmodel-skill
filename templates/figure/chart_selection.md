# 结果图型选择索引

图型由“要证明的结论”、底层数据结构和信息展示效率共同决定，不按软件默认、图型新奇度或固定禁用清单选择。每张图先填写结果图 Figure Contract，确定 DOCX/LaTeX 正式图注及其证据职责，再查本表；正式论文图不设置冗余整体 `title` / `sgtitle`。

本索引的第一层不是 bar / line / scatter，而是 **Evidence Structure → Scientific Visual Structure**。如果 accepted 工作簿已经保存时间、空间、分布、约束、状态、不确定性、多目标或阈值等结构，不应先把它压成几个汇总数字再画基础图。

## 可选视觉参考

只有图型选择或多面板布局需要外部视觉对照时，才按 `assets/figure_assets.yaml` 加载对应资产。图集不提供数据、结论或固定配色，不能替代工作簿、Figure Contract、`模型论文框架.md` 和 `q{x}_plot.m`。

## Scientific Figure Synthesis 快速索引

| Evidence Structure | 优先科学视觉结构 | 常见基础退化 | 需要检查的底层数据 |
|---|---|---|---|
| 简单离散比较 | interval dot / sorted dot / bar+error+benchmark | plain bar | 对象、指标、误差/区间、基准 |
| 分布 | box+raw scatter、violin+scatter+median、ECDF+quantile | 均值柱状、plain box | 逐样本值、组别、样本量、分位数 |
| 时间演化 | line+interval+event、state trajectory、overview+detail | plain line | 时间、状态、区间、事件、阶段 |
| 空间结构 | spatial field+path+boundary、节点/流量高亮 | 区域均值柱状 | 坐标、节点/网格值、路径、边界 |
| 机制关系 | trajectory+critical state、phase/response relation | 指标柱状 | 机制变量、状态量、临界点/边界 |
| 约束/可行域 | feasible region+boundary+recommended point、violation structure | 可行/不可行数量柱状 | 约束值、容差、变量、可行状态 |
| 参数响应 | curve+stable/risk band、heatmap+contour+operating point | 多组柱状 | 参数网格、响应、阈值、可行状态 |
| 不确定性 | interval+raw points、ECDF、quantile band | 均值±单数字 | 重复/场景结果、分位数、失败标记 |
| 多目标权衡 | Pareto+feasible state+knee+zoom | 各目标分开柱状 | 全部候选方案、各目标、推荐点 |
| 稳定/失效区域 | response+semantic background+threshold | “变化不大”折线 | 扫描点、状态/策略、失效标记 |
| 网络/流 | network+weighted flow+focus highlighting | 节点分数柱状 | 节点、边、权重、流量、路径 |
| 调度/资源 | Gantt+resource utilization+conflict context | 完工时间柱状 | 作业、资源、起止、占用/冲突 |
| 预测/诊断 | observed-vs-predicted+CI+residual/marginal | 模型指标柱状 | 逐样本真实/预测/残差/区间 |
| 全局—局部 | global view + Local Zoom / detached detail | 单图截轴 | 全局序列、ROI、临界/局部状态 |

## Composite Encoding 快速索引

当多个编码共享同一证据空间并共同回答一个 Primary question 时，优先考虑组合，而不是拆成多个普通单图：

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

组合图的目标是同时保留真实样本、统计结构、阈值/边界或模型关系，不是增加装饰数量。

## Scientific Rendering Profile 快速索引

| Profile | 核心元素 | 典型用途 |
|---|---|---|
| Distribution | raw points + box/violin/ECDF + median/quantile | 分组、鲁棒性、重复试验 |
| Regression / Prediction | scatter + identity/fit + CI + residual/marginal | 预测、拟合、分类概率诊断 |
| Dynamic | trajectory + interval + event/threshold + zoom | 时序、状态演化、控制过程 |
| Parameter Surface | heatmap + contour + point + feasible boundary | 参数敏感性、双因素响应 |
| Spatial | field + path/flow + node + boundary + colorbar | 选址、路径、覆盖、空间残差 |
| Optimization / Pareto | candidates + Pareto + feasible state + knee/recommendation | 单/多目标优化、方案选择 |
| High-density Scatter | alpha scatter / binned density / 2D density contour | 大样本仿真、预测、候选解云 |

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

| 证据任务 | 常规科研候选 | 进阶候选 | 主要准入条件与风险控制 |
|---|---|---|---|
| 方案/类别数值比较 | interval dot、排序点图、bar+error+benchmark | dumbbell、slopegraph、少量类别比例图 | 只有真正一维比较才保留 plain bar；成对变化优先直接表达变化方向 |
| 时间趋势与预测 | line+interval、真实—预测、残差时序 | Small Multiples、Local Zoom、状态阶段背景 | 多线遮挡优先分面；不能用平滑掩盖误差 |
| 参数敏感性 | 参数—响应+基准/阈值、tornado、heatmap+contour | Local Zoom、Semantic Background、3D response surface | 参数敏感性必须展示稳定/风险/失效结构，而非只报变化率 |
| 鲁棒性与扰动 | box/violin+raw points、ECDF、quantile interval | raincloud、Small Multiples、threshold background | 必须展示尾部、失败场景或原始点，不能只展示均值 |
| 多算法比较 | performance profile、error-time scatter、interval dot | Small Multiples、Focus Highlighting、parallel coordinates | 算法柱状图不能成为默认；需保留实例/重复、时间、可行性 |
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

## 基础图退化检查

如果正文核心 Figure 出现连续多个 plain bar / plain line / plain scatter，不要机械换成另一种基础图。先回到 `问题X求解结果.xlsx` / `问题X结果深化分析.xlsx` 检查是否已经存在状态、时间、空间、分布、阈值、不确定性、多目标、候选解或逐样本证据；若存在，回到 Scientific Figure Synthesis，而不是“柱状图换点图”结束。

如果工作簿本身只剩汇总值，应检查 Python 是否遗漏了本次运行真实产生的 Evidence Capture；但不得让 MATLAB 自己重算或伪造底层序列。

## 权威边界

本文件只负责候选图型与视觉问题索引；在当前版本中同时给出 Evidence Structure 与 Scientific Rendering Profile 的候选映射，但不维护通用绘图政策。通用信息效率判定、Evidence level、Primary question、Scientific Figure Synthesis Gate、Basic-form Challenge、Composite Encoding Preference、Figure Layout Gate、Figure Enhancement Gate、视觉注意力预算、正式图内标题策略、论文 caption、配色、数据诚实、Portfolio Gate、删除规则和入文闭环统一服从 `modules/04_figure_evidence.md`；Enhancement 的 MATLAB 实现模式只参考 `templates/figure/figure_enhancement_patterns.md`。

表格中的准入条件只用于提示某类候选视觉结构的局部风险，不构成第二套通用规则。若本文件与 Module 04 存在任何不一致，以 Module 04 为准。
