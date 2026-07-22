# 结果图 Figure Contract

| 字段 | 内容 |
|---|---|
| Figure ID | 图 X |
| Core conclusion | 一句话核心结论 |
| Figure role | 趋势 / 分布 / 诊断 / 敏感性 / 鲁棒性 / Pareto / 空间 / 网络 / 构成 / 多维画像 |
| Chart type | 条形图 / 折线图 / 热图 / 饼图 / 雷达图 / 3D 柱状图 / 3D 曲面 / 桑基图 / 其他 |
| Efficiency rationale | 该图型相较常规替代图如何提高信息展示效率 |
| Source workbook | `结果数据表/问题X/问题X求解结果.xlsx` 或 `问题X敏感性与鲁棒性结果.xlsx` |
| Worksheet | 中文工作表名 |
| Required columns | 绘图必需字段、记录键、单位和排序字段 |
| MATLAB script | `结果数据表/问题X/q{x}_plot.m`，例如问题一为 `结果数据表/问题一/q1_plot.m` |
| Panel map | a/b/c/d 各自证据职责 |
| Statistics/error | 误差线、区间、样本量和统计口径 |
| Color plan | 默认规则色板或按变量语义定制的配色及其含义 |
| Advanced chart safeguards | 视角、遮挡、比例、标准化、色条、二维投影或数值标签等控制措施 |
| Export files | `结果数据表/问题X/图表/qx_*.pdf`、`.png`，可选 `.svg` |
| Paper location | 正文章节 |
| Reviewer risk | 可能质疑点与处理 |
