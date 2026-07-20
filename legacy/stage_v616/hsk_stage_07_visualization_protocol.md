# HSK Stage 07：论文级可视化协议


## v6.1.6 调整

本阶段拆分为两部分：

- Stage 05：机理图合同与图位占坑，见 `references/hsk_stage_05_figure_contract_placeholder.md`。该阶段在建模早期执行，只规划和占位，不做最终精修。
- Stage 07：结果图与可复现可视化，继续执行本文件和 Nature/SCI 图表协议。结果图由代码和 `data_output/problemX/数据结果/` 驱动，默认输出到 `data_output/problemX/图表/`。

机理图最终精修延后到模型结果稳定之后，只处理 S 级核心图；普通辅助图保持简洁，重复图合并引用。


## 默认风格

图表分为两类：A 类为机理/推导图，负责说明题目对象、模型理由、公式来源和临界状态；B 类为结果/证据图，负责展示数值结果、对比、鲁棒性和决策结论。结果图默认 Nature/Science/SCI 风格，白底、细线条、中文标签、图例完整、标注不重叠。避免低级默认图和无信息柱状图。
## A 类：机理/推导图硬规则

本阶段必须先执行 `references/hsk_stage_09_mechanism_figure_protocol.md`，为每个核心小问规划本题专属推理图。该类图可以由 PPT、draw.io、Visio、TikZ、Python 或 MATLAB 绘制，不强制 Nature 风格，但必须清晰、符号一致、可导出公式或约束。

| 任务类型 | 推荐机理/推导图 |
|---|---|
| 几何建模 | 坐标系图、截面图、投影图、相切/相交关系图 |
| 物理机理 | 受力图、运动链路图、状态转移图、边界条件图 |
| 遮挡/碰撞 | 视线遮挡图、线段—圆/球相交图、临界接触图、局部放大图 |
| 路径优化 | 路径构型图、转弯/切换示意图、可行域边界图 |
| 调度/资源分配 | 任务分配图、资源流图、时间区间覆盖图、冲突图 |
| 多阶段决策 | 决策链路图、状态转移图、先后依赖图 |

每张图至少回答：为什么这样建模；为什么不能用更简单的模型；公式从哪个几何/物理关系来；约束对应题目哪个边界；临界值为什么合理。

模板见：`templates/shared/hsk_mechanism_figure_contract.md`、`templates/shared/hsk_mechanism_figure_qa_checklist.md`、`templates/shared/hsk_per_question_mechanism_plan_table.md`。


## 推荐图表

| 任务类型 | 推荐图表 |
|---|---|
| 预测 | 时序曲线、误差带、残差诊断、KDE/ECDF |
| 优化 | Pareto 前沿、收敛曲线、敏感性曲线、方案对比图 |
| 评价 | 权重热力图、排名稳定性图、贡献分解图 |
| 分类 | 混淆矩阵、ROC/PR、特征重要性、SHAP |
| 聚类 | 降维散点、轮廓系数、聚类热力图 |
| 时空 | 空间分布图、网络图、时空演化图 |
| 鲁棒性 | 扰动曲线、箱线图、置信区间、MC 分布图 |

## 图表规划表

| 问题 | 图编号 | 图名 | 类型 | Figure role | 支撑结论 | 对应公式/约束 | 论文位置 | 是否正文核心图 |
|---|---|---|---|---|---|---|---|---|

## 导出要求

每张核心图保存 PNG 和 PDF/SVG；文件名英文；论文内图题中文。核心结果优先做成单图，复杂机制可用多面板。机理/推导图可采用白底简洁线条、局部放大和关键符号标注，不要求炫技配色。


## 图表入文检查

所有核心图表必须通过 `templates/shared/hsk_figure_paper_check_table.md` 进行内部复核：

- 图表是否有明确数据来源；
- 是否能回溯到生成代码；
- 是否在正文中解释趋势、极值、差异或机制；
- 是否支撑某个具体结论；
- 图表文件是否适合 LaTeX 引用。


## Nature / SCI 图表增强

本阶段优先执行 `references/hsk_nature_figure_protocol.md` 中的图表契约、证据层级、配色、导出和 QA 规则。该增强只强化图表质量，不改变 HSK 主流程；默认以 Python / MATLAB 生成可复现图表，用户明确要求其他工具时再切换。

### 图表契约

每张正文核心图必须先明确：

- `Core conclusion`：该图支撑的一句话结论；
- `Figure role`：发现、机制、验证、比较、鲁棒性或决策；
- `Panel map`：每个面板分别承担哪一类证据；
- `Source data`：来自哪个 `data_output/` 文件；
- `Plot code`：由哪个脚本生成；
- `Reviewer risk`：评委可能质疑什么。

Nature/SCI 结果图模板见：`templates/shared/hsk_nature_figure_contract.md`；机理/推导图模板见：`templates/shared/hsk_mechanism_figure_contract.md`。

### 参考图谱

参考图表类型与示例图位于：

- `references/hsk_nature_chart_atlas.md`
- `assets/nature_figure/chart-atlas/`
- `assets/nature_figure/gallery/`

使用时只参考图表类型、布局和审美，不机械照搬生物医学语境。

### 配色与导出

高质量图表默认使用 `templates/shared/hsk_nature_style.py`，提供 Nature / SCI 低饱和配色、可编辑 SVG/PDF 字体设置、面板标签和统一导出函数。核心图建议导出：

```text
data_output/problemX/图表/xxx.pdf
data_output/problemX/图表/xxx.png
data_output/problemX/图表/xxx.svg
```

必要时额外导出 600 dpi TIFF。图像文件名仍建议英文或拼音，以保证 LaTeX 编译稳定。

### QA

核心图必须通过 `templates/shared/hsk_mechanism_figure_qa_checklist.md`、`templates/shared/hsk_nature_figure_qa_checklist.md` 与 `templates/shared/hsk_figure_paper_check_table.md` 检查：一方面检查期刊级图表质量，另一方面检查图表是否进入 HSK 论文闭环。