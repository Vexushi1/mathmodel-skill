# HSK Nature / SCI 图表增强协议

本文件由 `nature-figure` 工作流选择性吸收而来，用于增强 HSK Stage 07 可视化协议。它不是独立主工作流；数学建模任务仍以 HSK DOCX 草稿 + LaTeX 终稿、`data_output/problemX/数据结果/`、`data_output/problemX/图表/`、LaTeX 终稿阶段的 `final_latex/figures/` 复制链路和可复现代码链路为准。

## 1. 吸收边界

吸收：

- 图表结论契约（figure contract）；
- 证据层级与 hero panel 思维；
- Nature / Science / SCI 风格设计原则；
- 参考图表类型图谱；
- 统一配色体系；
- Python Matplotlib 论文级样式模板；
- PDF / SVG / PNG / 可选 TIFF 导出规范；
- 图表 QA 与审稿风险检查。

执行边界：

- 本协议只强化图表证据、版式、配色、导出和 QA；
- 默认以 Python / MATLAB 生成可复现图表，用户明确要求其他工具时再切换；
- 不为美观牺牲题意、结果复核或 LaTeX 编译稳定性。

## 2. Figure contract：画图前必须先定论证功能

每张核心图，尤其正文主图，必须先写清：

```text
Core conclusion: 这张图要支撑的一句话结论
Figure role: discovery / mechanism / validation / comparison / robustness / decision
Figure archetype: quantitative grid / schematic-led composite / image plate + quant / asymmetric mixed-modality figure
Panel map:
  a: 主证据或核心结果
  b: 对比、验证或机制补充
  c: 鲁棒性、误差、敏感性或统计检验
Evidence hierarchy:
  hero evidence: 最能支撑结论的证据
  validation evidence: 验证或多算法对照
  controls/robustness: 参数扰动、误差、约束或消融检查
Source data: data_output/...
Plot code: code/...
Export files: data_output/problemX/图表/...
Reviewer risk: 可能被质疑的点及预防说明
```

硬规则：如果一个面板不能支撑独立证据，应删除或并入附录；不能为了“图多”堆面板。

## 3. HSK 数模图表角色

| 图表角色 | 适用位置 | 典型问题 | 推荐图表 |
|---|---|---|---|
| discovery | 题目分析 / 数据预处理 | 数据分布、异常、空间格局 | 分布图、箱线图、热力图、散点图 |
| mechanism | 建模与机理说明 | 变量关系、物理过程、路径机制 | 流程图、状态曲线、相图、网络图 |
| comparison | 求解结果比较 | 多模型、多方案、多算法 | 分组柱状图、折线对比、雷达图 |
| validation | 模型检验 | 预测误差、拟合质量、分类性能 | 残差图、误差带、ROC、混淆矩阵 |
| robustness | 敏感性与鲁棒性 | 参数扰动、噪声扰动、约束可行性 | 箱线图、森林图、误差带、敏感性曲线 |
| decision | 结论与策略 | 推荐方案、优先级、权衡关系 | Pareto 前沿、排序条形图、决策矩阵 |

## 4. 参考图表图谱

参考图谱位于：

```text
assets/nature_figure/chart-atlas/
├── atlas-01-bar-charts.png
├── atlas-02-line-trends.png
├── atlas-03-heatmaps.png
├── atlas-04-scatter-bubble.png
├── atlas-05-radar-polar.png
├── atlas-06-distributions.png
├── atlas-07-forest-interval.png
├── atlas-08-area-stacked.png
├── atlas-09-image-plates.png
└── atlas-10-network-matrix.png
```

使用规则：参考图谱用于选择图表类型和版式，不得机械照抄无关语境。数模论文优先使用：趋势图、对比图、热力图、分布图、森林/区间图、网络/矩阵图、Pareto 图和多面板验证图。

## 5. 论文级配色原则

总体原则：一张图像应像一个统一的证据页面，而不是多张默认图拼贴。

- 同一方法或同一方案在全文保持同色；
- 基准模型、对照方案使用中性灰或冷色；
- 本文方法、推荐方案使用主强调色；
- 绿色/红色主要用于上升、下降、收益、风险等方向性信息；
- 不使用彩虹色、3D 渐变和高饱和装饰色；
- 不再强制色盲友好作为第一约束，但必须保证黑白打印可辨识、投影清晰。

推荐配色见 `templates/shared/hsk_nature_style.py`。

## 6. 多面板布局规则

- 优先设置一个 hero panel；
- 支撑面板围绕 hero panel 组织，不强制所有面板等大；
- 面板编号使用小写粗体 `a/b/c/d`；
- 面板标号位于左上角；
- 字体、线宽、坐标风格统一；
- 图注必须逐一解释每个面板；
- 不要用边框硬包围所有面板，优先用留白和对齐形成结构。

数模常用结构：

```text
a  核心结果 / 推荐方案 / 主趋势
b  多算法或多方案对比
c  误差、残差、约束违反或可行性检查
d  参数敏感性、鲁棒性或消融验证
```

## 7. 导出规范

默认导出：

```text
data_output/problem1/图表/q1_core_result.pdf   # LaTeX 正文优先
data_output/problem1/图表/q1_core_result.png   # 预览与答辩
data_output/problem1/图表/q1_core_result.svg   # 可编辑矢量图，可选但推荐
```

投稿级或需要极高清栅格图时，可额外导出：

```text
data_output/problem1/图表/q1_core_result.tiff  # 600 dpi，可选
```

Matplotlib 关键设置：

```python
mpl.rcParams.update({
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "axes.spines.right": False,
    "axes.spines.top": False,
    "legend.frameon": False,
})
```

## 8. 图表 QA 检查

每张正文核心图必须回答：

1. 是否有一句明确结论；
2. 是否有唯一的数据来源；
3. 是否能回溯到绘图代码；
4. 坐标轴是否有名称和单位；
5. 颜色是否有语义且全文一致；
6. 图例是否必要，是否遮挡数据；
7. 面板是否都承担独立证据；
8. 统计量、误差线、样本量或容差是否说明；
9. 是否导出 PDF/PNG，必要时 SVG；
10. LaTeX 正文是否引用并解释；
11. 是否支撑某个小问结论；
12. 是否存在评委可能质疑的图表风险。

## 9. 与 HSK 闭环绑定

所有核心图表必须形成：

```text
题目要求 → 数据文件 → 绘图代码 → data_output/problemX/图表/图像文件 → LaTeX 正文引用 → 图注解释 → 结论支撑
```

若该链条断裂，图表不得进入正文主图。