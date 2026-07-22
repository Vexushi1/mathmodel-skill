# Module 04：MATLAB 结果图证据与机理图精修

## 正确顺序

1. Python 完成求解、检验并锁定两类标准工作簿；
2. 先写每张图的 Core conclusion，再按 `templates/figure/chart_selection.md` 选择图型；
3. MATLAB 声明目标工作表和必需字段，调用 `hsk_read_result_workbooks.m` 校验后读取数据；
4. MATLAB 生成结果图；
5. 检查每个核心结论是否有图/表证据；
6. 回看早期机理图合同，只精修 S/A 级图；
7. 统一图号、图注、正文引用和结论映射。

## A 类：机理/推导图

优先表达公式来源、约束来源和临界状态，其次是对象关系和策略机制。图内只放对象、变量、方向、边界、距离、角度、流向和临界状态，完整推导留在正文。

几何图优先 GeoGebra/SVG，结构图优先 PPT/draw.io/SVG，可编译结构图可用 TikZ；数据驱动机理图可以由 MATLAB 读取结果工作簿绘制。禁止用通用“输入—模型—输出”流程图替代题目专属机理图。

## B 类：结果图

每张核心图建立：Core conclusion、Figure role、Panel map、Source workbook、Worksheet、Required columns、MATLAB script、Export files、Statistics/error、Reviewer risk、Paper location 和 Caption duty。

源数据只允许来自：

```text
结果数据表/问题X/问题X结果数据/问题X求解结果.xlsx
结果数据表/问题X/问题X结果数据/问题X敏感性与鲁棒性结果.xlsx
```

不得在 MATLAB 中重算核心指标，不得根据论文摘要数字伪造绘图序列。图型由结论任务和底层数据决定：趋势、分布、稳定性、排序、空间、网络、调度和 Pareto 权衡分别使用适配图型；禁止为装饰选择 3D、饼图、彩虹色或信息密度不足的多面板。

## MATLAB 数据校验

正式绘图脚本必须：

1. 以 `VariableNamingRule="preserve"` 读取中文字段；
2. 在 Figure Contract 中声明工作簿、工作表和必需字段；
3. 读取前检查工作表存在、字段齐全、至少一条真实记录；
4. 对显式 `记录键` 检查空值和重复；
5. 对数值字段检查 Inf 与非法值；
6. 时间、类别或坐标排序必须在脚本中显式完成，不依赖 Excel 原始顺序。

`templates/matlab/hsk_read_result_workbooks.m` 提供上述基础检查。未通过检查不得进入绘图阶段。

## MATLAB 绘图规范

- 默认创建可见图窗并保留，不自动关闭；
- 默认不批量调用 `exportgraphics` 或 `print`；人工调整后显式调用可选导出函数；
- 白底，`grid off`，坐标轴和边框清楚；
- 默认字号 18，图例约 16，面板字母 20--22；
- 主色采用深蓝、青绿、蓝紫、暗红，米色和浅灰仅作区间或背景；
- 图内不重复写总标题；多面板只保留 a、b、c、d 标记；
- 中文坐标轴和单位完整，标签不重叠，图例不遮挡。

正式图保存到 `figures/`，可编辑源文件保存到 `figures_editable/`；文件名使用英文或拼音。图题由 LaTeX 图注承担。

## 入文闭环

图后另起正文段，按 `templates/writing/caption_explanation.md` 组织趋势/差异、关键数值、机制和结论作用，不套用固定句式。无法绑定小问、公式、工作簿工作表或结论的图删除。
