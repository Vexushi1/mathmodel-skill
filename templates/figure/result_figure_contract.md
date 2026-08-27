# 结果图 Figure Contract

| 字段 | 内容 |
|---|---|
| Figure ID | 图 X |
| Core conclusion | 一句话核心结论 |
| Evidence level | L1 / L2 / L3 / L4 |
| Primary question | 该 Figure 唯一一级阅读任务 |
| Figure role | 趋势 / 分布 / 诊断 / 敏感性 / 鲁棒性 / Pareto / 空间 / 网络 / 构成 / 多维画像 |
| Available evidence dimensions | 当前 accepted 工作簿实际具备的时间、空间、样本、状态、约束、不确定性、多目标等维度 |
| Evidence structure | 简单比较 / 分布 / 时间演化 / 空间 / 机制 / 边界 / 参数响应 / 不确定性 / 多目标 / 稳定区 / 网络 / 调度 / 诊断 / 全局—局部 |
| Figure level | F1 / F2 / F3；F1 核心图需通过 Basic-form Challenge |
| Candidate visual structures | 至少两个合理候选；不要求为了多样性凑图型 |
| Selected visual structure | 最终采用的科学视觉结构 |
| Basic-form challenge | 若最终为 plain bar/line/scatter/box/histogram，说明为何更丰富结构不存在或无信息增益；否则写通过升级 |
| Composite encoding | none 或 box+scatter / violin+scatter / line+interval / scatter+fit+CI / heatmap+contour / trajectory+boundary 等 |
| Scientific Rendering Profile | Distribution / Regression-Prediction / Dynamic / Parameter Surface / Spatial / Optimization-Pareto / High-density Scatter / custom |
| Scientific value rationale | 相较替代方案如何增加可验证信息、揭示模型结构或降低评委搜索成本 |
| DOCX/LaTeX caption | 正式图号与图名；必要时补充样本、统计口径、时间范围和误差 |
| In-figure title | 正式论文图固定为 `none`；不设置整体 `title` / `sgtitle`，多面板按需只保留 a/b/c/d 等 panel label |
| Enhancement | 可选：none / Local Zoom / Small Multiples / Focus Highlighting / Semantic Background / Composite Diagnostic / Conditional 3D；可合理组合 |
| Enhancement rationale | 为什么基础布局不足，以及增强后增加了什么可验证信息或降低了什么视觉搜索成本 |
| Global/detail strategy | none / inset / detached zoom / overview+detail / split figures；说明全局—局部关系 |
| Rejected alternatives | 记录 1--2 个关键备选及否决原因，避免因为模板默认而选图 |
| Source workbook | `问题X求解/问题X求解结果.xlsx` 或 `问题X求解/问题X结果深化分析.xlsx` |
| Worksheet | 中文工作表名 |
| Required columns | 绘图必需真实字段、记录键、单位和排序字段 |
| Expected positions | 可选列号，仅作结构漂移警告 |
| MATLAB script | `问题X求解/qX_plot.m` |
| Panel map | a/b/c/d 或其他 axes 的证据职责；无多面板时写单图职责 |
| Statistics/error | 误差线、区间、样本量和统计口径 |
| Export files | 求解阶段留空；论文阶段人工确认后可登记项目级 `figures/qx_*.pdf`、`.png` 或 `.svg` |
| Framework registry | `模型论文框架.md` 中的对应图表登记 |
| Paper location | 正文章节 |
| Reviewer risk | 可能质疑点与处理 |

Figure Contract 默认登记在 `模型论文框架.md`，不生成独立 `figure_evidence` 文件。`Candidate visual structures / Basic-form challenge / Scientific value rationale` 只记录科研表达决策，不变成样式参数表；Enhancement 只记录决策与理由，**不记录 inset 坐标、透明度等 MATLAB 实现参数**。

合同的核心问题是：这张图为什么比一个普通柱状/折线/散点更能解释当前模型；若基础图已经是最直接答案，则说明其信息结构为何确实简单，而不是为了“高级”强行复杂化。
