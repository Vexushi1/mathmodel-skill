# Python 科研 Figure Evidence：继承 MATLAB 绘图 Skill

**这是相同的科研绘图能力在 Python 中的实现，不是一套降级版规则。**

唯一科学判断 Authority 是 [Module 04](../../../modules/04_figure_evidence.md)，模式与增强手法参阅 [Figure Enhancement Patterns](../../figure/figure_enhancement_patterns.md)；原 [MATLAB 科研绘图模板说明](../../matlab/README.md) 的所有科学判断同样适用。`q1_plot.py` 的 line/point 只是工作簿读取与绘图调用的示例，**不得当成全题默认图型**。

## MATLAB → Python 的能力对应（必须全部继承其判断规则）

| 原 MATLAB Skill 要点 | Python 执行路径 / 准入条件 |
|---|---|
| Scientific Figure Synthesis Gate | 先明确 Core conclusion、Evidence structure、Primary question、实际可用细粒度证据；再选图型 |
| Basic-form Challenge | 先判断普通 line/bar/scatter/box/histogram 是否足够；不能为了高级图而复合 |
| Figure Level / Composite Encoding | F1/F2/F3 不是质量排名；C1–C16 按真实互补信息使用，不重复编码同一证据 |
| Scientific Rendering Profiles | Distribution、Regression/Prediction、Dynamic、Parameter Surface、Spatial、Optimization/Pareto、High-density Scatter 不改变原判定规则 |
| Figure Layout Gate | 动态判断单图、1×2、2×1、1×3、2×2 或拆分，不凑无效 panel；按语义决定 shared axes |
| Figure Enhancement Gate | Local Zoom、Small Multiples、Focus Highlighting、Semantic Background、Composite Diagnostic、Conditional 3D 只有在提供必要信息增益时启用 |
| Publication Rendering Grammar | 显式 RGB/colormap、open axes、局部覆盖字体字号、adaptive canvas、legend/colorbar、有限注意力、诚实坐标轴范围及矢量优先导出 |
| 证据保真 | 真实工作簿名/工作表/原始表头唯一匹配；缺测保留 NaN 断线；明确理由才能排序；不要在绘图阶段补算模型 |
| 统计与不确定性 | 只能展示 accepted 工作簿内已有的区间、残差、阈值、PQS/03B 证据，不伪造拟合线或 CI |
| Caption/Portfolio/人工验收 | 正式图内无整体标题、caption 归 LaTeX/DOCX；Figure ID、图源、工作簿、图片哈希、approved figures 与结果主张形成闭环 |

### Python 实现示例：不是新 Authority

`figure_patterns.py` 提供常用科研视觉模式的 **可选实现参考**。选图由上面的 Module 04 决定，绝不由这个文件或绘图库 API 决定：

- C1 分布：`box_with_raw_points`，箱线+真实样本散点，jitter 只改变横向显示位置。
- C3 动态/区间：`line_with_recorded_interval`，线+**真实记录的**上下界，缺测保持断开。
- C5 参数场：`heatmap_with_real_boundary`，已验收真实网格+真实边界阈值，禁止在图形函数中插值。
- C6 多目标：`pareto_with_choice`，只显示已确认的 Pareto 候选和推荐点，不在绘图层计算支配关系。
- Z1 关键细节：`inset_with_grounded_limits`，只用用户根据数据选择的 ROI；局部放大不能制造新证据。
- L3 论文框架：`apply_publication_frame`，数据图层全部建立之后一次应用、随后允许各 panel 局部覆盖；不使用默认颜色循环。
- 正式导出：`export_after_visual_review`，选 PDF/SVG/PNG，检查裁切、字体、图例与实际输出，不能把导出当图审通过。

C2、C4、C7–C16、L1/L2、空间、网络、3D、高密度分布等**并未取消**：按原 Figure Enhancement Patterns 的适用条件使用 Matplotlib 自带的 `GridSpec`、`scatter`、`hexbin`、`pcolormesh`、`contour`、`Axes3D` 等模块实现，不强制一个公共函数对应一种图。

`figure_patterns.py` 是供选择性复制或显式依赖的参考代码，**不是逐问代码必须额外安装的新运行时包**。正式实例化时可把实际使用的函数放入单文件 `qN_plot.py`，或如实登记依赖，遵守项目的单文件源码交付及 hash/read-set 规则。

## 项目级唯一后端及数据边界

- `plotting.backend` 为整个项目的 Python/MATLAB **唯一绘图后端**，独立于 `execution.solver_backend`。问题一 Python/问题二 MATLAB 的当前混用不得发生。
- Python 每问独立脚本位于 `问题X求解/qN_plot.py`；历史 MATLAB 项目不需要迁移且仍可写入原 `qN_plot.m`。
- `preprocessing_decision=project_level` 才有 `数据预处理/data_process.py`，它只读取 accepted `数据预处理结果.xlsx`；不能重新插值/平滑/标准化/拟合/估计。
- 主结果图读取当前 accepted 03A 工作簿；03B 仅当 Analysis Necessity Gate 为 required 且 03B 实际通过时才被引用，缺失时不能回退主结果并伪造稳健性结论。
- 合法的 `not_needed/question_local` 原始数据与问题局部数据入口继续由原数据事实源合同决定。

## 数据、样式和出版

选定真实结构后，脚本集中填写系列颜色、字体、尺幅、坐标单位、marker 密度和 legend/cbar 位置。中文字体需要在用户机器实际核查，不能以 CI 存在相似字体为依据。只选择 Matplotlib 默认 palette、无差异美化或自行改数值，不满足 Module 04。

用户手动运行并看图，默认 `plt.show()` 不导出；确认后可按证据使用 vector-first SVG/PDF 或 PNG（通常 300 DPI，根据密度可增至 600 DPI）。不要擅自画 3D、假误差带、虚构阈值或无来源背景。正式图内不使用 `ax.set_title` / `fig.suptitle`；多 panel 可以保留 a/b/c/d 标签。

基础运行依赖单独存于 `requirements-plot-python.txt`，没有必要让全部数值求解路径安装 Matplotlib。Windows Python 3.10/3.14 的 CI 测试只证明真实 Excel→绘图运行可用，不替代人工审核视觉和语义。

**完整流程**：锁定 Figure Contract → 读取真实 accepted 证据 → 选择科学模式和必要布局 → Python/MATLAB 渲染 → 用户审图/调整 → 按需导出 → Figure Source/Portfolio 检查 → 图片哈希与论文 caption/claim 对应。模型、数值、人工批准各自保持原身份。
