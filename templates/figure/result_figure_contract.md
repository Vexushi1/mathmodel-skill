# 结果图 Figure Contract

| 字段 | 内容 |
|---|---|
| Figure ID | 图 X |
| Core conclusion | 一句话核心结论 |
| Figure role | 趋势 / 分布 / 诊断 / 敏感性 / 鲁棒性 / Pareto / 空间 / 网络 |
| Composition level | `single` / `layered` / `multi-panel` / `hybrid` |
| Layer map | 背景区间、结构图形、原始数据、模型线、结论标记分别承担什么职责；非层叠图填“不适用” |
| Axis contract | 单轴/双轴、各轴单位、范围、零线/基准线/容差线；双轴需说明准入理由 |
| Panel map | a/b/c/d 各自证据职责；单图或纯层叠图填“不适用” |
| Shared color mapping | 主模型、对照、风险、关键点等跨图层/面板的固定颜色角色 |
| Source workbook | `结果数据表/问题X/问题X结果数据/问题X求解结果.xlsx` 或 `问题X敏感性与鲁棒性结果.xlsx` |
| Worksheet by layer/panel | 每个图层或面板对应的中文工作表名和字段 |
| MATLAB script | `MATLAB绘图/问题X/QX_plot.m`；同一问题全部结果图必须指向同一个脚本 |
| Local plot function | `QX_plot.m` 内对应本地图函数名，如 `plot_bar_line_combo`、`plot_violin_scatter_combo`、`plot_evidence_panel_combo` |
| Statistics/error | 误差线、区间、样本量和统计口径 |
| Rendering transforms | 抖动、固定带宽 KDE、分箱、透明度、图例和面板布局等仅绘图参数 |
| Export files | `figures/qx_*.pdf`、`.png`，可选 `.svg` |
| Paper location | 正文章节 |
| Reviewer risk | 可能质疑点与处理 |

同一问题不得在合同中出现第二个正式 MATLAB 绘图文件。需要新增图时，在原 `QX_plot.m` 中增加本地绘图函数和图表注册项。

层叠组合图必须逐层说明证据作用。两层表达相同信息时删除弱层；双纵轴没有明确机制关系时拆图；小提琴样本不足时降级为箱线 + 散点。多面板或混合组合图缩放到论文实际尺寸后不可读时拆分。
