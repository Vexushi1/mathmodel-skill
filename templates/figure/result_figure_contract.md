# 结果图 Figure Contract

| 字段 | 内容 |
|---|---|
| Figure ID | 图 X |
| Core conclusion | 一句话核心结论 |
| Figure role | 趋势 / 分布 / 诊断 / 敏感性 / 鲁棒性 / Pareto / 空间 / 网络 |
| Source workbook | `结果数据表/问题X/问题X结果数据/问题X求解结果.xlsx` 或 `问题X敏感性与鲁棒性结果.xlsx` |
| Worksheet | 中文工作表名 |
| MATLAB script | `MATLAB绘图/问题X/QX_plot.m`；同一问题全部结果图必须指向同一个脚本 |
| Local plot function | `QX_plot.m` 内对应本地图函数名，如 `plot_core_result`、`plot_sensitivity` |
| Panel map | a/b/c/d 各自证据职责；单图时填“不适用” |
| Statistics/error | 误差线、区间、样本量和统计口径 |
| Export files | `figures/qx_*.pdf`、`.png`，可选 `.svg` |
| Paper location | 正文章节 |
| Reviewer risk | 可能质疑点与处理 |

同一问题不得在合同中出现第二个正式 MATLAB 绘图文件。需要新增图时，在原 `QX_plot.m` 中增加本地绘图函数和图表注册项。