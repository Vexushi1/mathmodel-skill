# HSK Nature Chart Atlas Index

本文件索引 `assets/nature_figure/chart-atlas/` 与 `assets/nature_figure/gallery/` 中的参考图表。它们仅用于版式、图表类型和审美参考，不替代题意分析。

## 1. Chart atlas

| 文件 | 图表类型 | 数模适用场景 |
|---|---|---|
| `assets/nature_figure/chart-atlas/atlas-01-bar-charts.png` | 柱状图 / 分组柱状图 | 模型性能、方案指标、权重和排名对比 |
| `assets/nature_figure/chart-atlas/atlas-02-line-trends.png` | 折线趋势图 | 时间序列、迭代收敛、参数变化、预测对比 |
| `assets/nature_figure/chart-atlas/atlas-03-heatmaps.png` | 热力图 | 相关矩阵、敏感性矩阵、空间格局、混淆矩阵 |
| `assets/nature_figure/chart-atlas/atlas-04-scatter-bubble.png` | 散点 / 气泡图 | 变量关系、聚类分布、拟合关系、异常识别 |
| `assets/nature_figure/chart-atlas/atlas-05-radar-polar.png` | 雷达 / 极坐标 | 多指标综合评价、方案画像、指标均衡性 |
| `assets/nature_figure/chart-atlas/atlas-06-distributions.png` | 分布图 | 箱线图、小提琴图、误差分布、MC 结果 |
| `assets/nature_figure/chart-atlas/atlas-07-forest-interval.png` | 森林图 / 区间图 | 置信区间、效应量、鲁棒性区间、灵敏度区间 |
| `assets/nature_figure/chart-atlas/atlas-08-area-stacked.png` | 面积 / 堆叠图 | 组成结构变化、累计贡献、类别占比 |
| `assets/nature_figure/chart-atlas/atlas-09-image-plates.png` | 图像板 | 图像处理、医学影像、遥感图、分割结果 |
| `assets/nature_figure/chart-atlas/atlas-10-network-matrix.png` | 网络 / 矩阵 | 图论、路径规划、邻接矩阵、空间网络 |

## 2. Gallery

| 文件 | 参考价值 |
|---|---|
| `assets/nature_figure/gallery/fig1-material-mechanism-rich.png` | 机制说明 + 定量验证的复合布局 |
| `assets/nature_figure/gallery/fig2-spatial-imaging-rich.png` | 空间图像 + 定量图的组合方式 |
| `assets/nature_figure/gallery/fig3-in-vivo-efficacy-rich.png` | 结果主图 + 统计验证 + 分组对比 |
| `assets/nature_figure/gallery/fig4-single-cell-systems-rich.png` | 多模态 / 系统图 / 热力图组合 |
| `assets/nature_figure/gallery/fig5-validation-perturbation-rich.png` | 验证实验 + 扰动分析 + 鲁棒性证据 |

## 3. 数模使用规则

1. 先确定小问结论，再选图表类型；
2. 优先选择能直接支持结论的图，不为美观堆图；
3. 预测题优先趋势图 + 误差图；
4. 优化题优先收敛曲线 + 约束检查 + 方案对比；
5. 评价题优先权重图 + 排名稳定性图 + 热力图；
6. 鲁棒性分析优先箱线图、误差带、森林图；
7. 图像文件名使用英文或拼音，正文图注使用中文；
8. 每张图必须绑定 `data_output/` 数据文件和绘图代码。