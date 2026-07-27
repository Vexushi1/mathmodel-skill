# HSK MATLAB 科研绘图模板 v6.3.0

MATLAB 只读取 Python 输出的两类标准工作簿，不重新求解。每问唯一入口 `q{x}_plot.m` 与工作簿同目录，正式图导出到同级 `图表/`。

## 路径

```matlab
scriptPath = string(mfilename("fullpath"));
resultDir = string(fileparts(scriptPath));
solutionBook = fullfile(resultDir, "问题一求解结果.xlsx");
robustnessBook = fullfile(resultDir, "问题一敏感性与鲁棒性结果.xlsx");
```

## 实表读取

生成正式代码前必须读取本次工作簿。字段定位采用精确表头唯一匹配：

```matlab
raw = readcell(sourceBook, "Sheet", sourceSheet);
headers = strtrim(string(raw(1, :)));
matches = find(headers == expectedHeader);
assert(numel(matches) == 1, "字段缺失或重复: %s", expectedHeader);
column = matches(1);
```

允许记录期望列号作为结构漂移警告，但禁止模糊匹配、别名猜测、相似字段回退和自动改变语义映射。列顺序的无害变化不应迫使重写整段脚本。

## 图标题与风格

- 单图使用简洁 `title`，多面板使用一个整体 `sgtitle`；
- 标题默认保留在图窗和导出文件；
- 图注补充统计口径、时间范围、误差和解释，不与标题逐字重复；
- 白底、细轴、低饱和深色、中文坐标轴和单位，默认字号 18；
- 默认保留可见图窗，不自动关闭或批量导出；
- 3D、饼图、雷达图等只有在提高信息效率且不制造误读时使用。

每张正式图的标题、图注、源工作簿、工作表、真实表头、脚本和支撑结论必须同步到项目根目录 `模型论文框架.md`。正式交付后运行项目同步器，登记 MATLAB 脚本、标题与导出图。

命名固定为 `q1_plot.m`、`q2_plot.m`；禁止 `q1_polt.m` 等拼写变体。
