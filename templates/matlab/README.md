# HSK MATLAB 科研绘图模板 v7.0.0

MATLAB 只读取 Python 两阶段输出的两个标准工作簿，不重新求解。每问唯一入口通用记为 `q{x}_plot.m`，问题一实例为 `q1_plot.m`，与主求解/深化分析脚本及工作簿同处 `问题X求解/`。禁止 `q1_polt.m` 等拼写变体。

## 路径

```matlab
scriptPath = string(mfilename("fullpath"));
resultDir = string(fileparts(scriptPath));
solutionBook = fullfile(resultDir, "问题一求解结果.xlsx");
resultAnalysisBook = fullfile(resultDir, "问题一结果深化分析.xlsx");
```

主结果图读取 `solutionBook`；稳定性、阈值、算法或结构图读取 `resultAnalysisBook`。不得跨问题读取临时 Excel、根据摘要数字反推数据或在 MATLAB 中重算核心结果。

## 实表读取

字段定位采用精确表头唯一匹配。允许登记期望列号作为结构漂移警告，禁止模糊匹配、别名猜测、相似字段回退和自动改变语义映射。

## 图标题与风格

- 单图使用简洁 `title`，多面板使用一个整体 `sgtitle`；
- 图注补充统计口径、时间范围和误差，不与标题逐字重复；
- 白底、细轴、低饱和深色、中文坐标轴和单位，默认字号 18；
- 默认保留可见图窗，不自动关闭，不创建图表子目录，不批量导出；
- 论文阶段人工确认后，按需导出到项目级 `figures/`。

每张图的源工作簿、工作表、真实表头、脚本、图注和正文位置同步登记到 `模型论文框架.md`；默认不生成独立 `figure_evidence` 文件。

图表交付前执行 `python scripts/sync_project.py <project_root> --write --strict --delivery-scope figures`。同步器检查两个工作簿、`qX_plot.m` 的真实引用、标题和证据链；默认不要求导出图片已经存在。
