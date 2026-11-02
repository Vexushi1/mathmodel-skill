# Python Figure Rendering Backend（新增；不替代 MATLAB）

此目录只提供 Figure Evidence 的 **Python 渲染执行后端**。原有 Authority：
[modules/04_figure_evidence.md](../../../modules/04_figure_evidence.md)；
Scientific Figure Synthesis、Basic-form Challenge、Panel/Enhancement、
Publication Rendering Grammar、来源绑定和人工审图全部沿用原规则。

- 每个赛题只在项目根选择一个绘图后端：Python 或 MATLAB；**不能逐问题混用**。
- Python 模板放进项目时，每问唯一入口为 `问题X求解/qN_plot.py`。
- 只有 `preprocessing_decision=project_level` 时才生成 `数据预处理/data_process.py`。
- 求解代码可以是 Python 或 MATLAB；绘图只读取当前合法数据源及已经验收的结果工作簿。03B 只有实际 required 且 accepted 才允许作结果深化图。
- `not_needed/question_local` 及未覆盖辅助附件的合法原始数据源，继续遵照原 Figure Contract，而非全部强制转为公共工作簿。
- 不运行模型、不执行再次插值/训练/清洗、不写回 accepted Excel。
- 在用户本地运行：`python -m pip install numpy openpyxl matplotlib`。SciPy、Seaborn 等并非基础入口强制依赖。
- 实例化时填入真实 sheet、列名、单位/标签、RGB，按当前证据决定图型及绘图顺序。模板的线/点仅演示真实读取和渲染链，**不能机械作为全部图的默认图型**。
- 默认打开图窗供用户人工检查，**不自动导出、不自动批准**。图正式入文时需注册实际图片、脚本、工作簿、Figure ID、caption，并走现有 Figure Source 和论文引用检查。
- 中国字体是否具备需依据用户机器实际字体确认，脚本不能假设 CI 的字体和本机一致。

`q1_plot.py`、`data_process.py` 为**各自可独立运行的单文件模板**，不要求用户为每个项目安装新内部工具包，且不会改变 MATLAB 下 `qN_plot.m` / `data_process.m` 的正常维护行为。
