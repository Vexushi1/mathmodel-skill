# HSK MATLAB 科研绘图模板 v6.3.4

MATLAB 只读取 Python 输出的两类标准工作簿，不重新求解。每问唯一入口 `q{x}_plot.m` 与工作簿同目录，正式图导出到同级 `图表/`。

活动模板只保留新项目直接需要的绘图入口、科研样式、题目专属机理图骨架和仍有兼容价值的精确工作簿读取器。旧的项目根目录搜索与独立导出辅助函数已迁入 `legacy/matlab_compat/`，不得继续作为新项目默认依赖。

## 路径

```matlab
scriptPath = string(mfilename("fullpath"));
resultDir = string(fileparts(scriptPath));
solutionBook = fullfile(resultDir, "问题一求解结果.xlsx");
robustnessBook = fullfile(resultDir, "问题一敏感性与鲁棒性结果.xlsx");
```

MATLAB 只能引用本问两类标准工作簿，不得跨问题目录读取摘要数字或临时 Excel。

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
- 需要导出时在 `q{x}_plot.m` 的显式 `EXPORT_FIGURES` 分支中完成；
- 3D、饼图、雷达图等只有在提高信息效率且不制造误读时使用。

## 图表证据链门槛

每张正式图的标题、图注、源工作簿、工作表、真实表头、脚本和支撑结论必须同步到项目根目录 `模型论文框架.md`。正式图必须真实存在，且修改时间不得早于对应工作簿或 MATLAB 脚本。

图表交付前执行：

```bash
python scripts/sync_project.py <project_root> \
  --write --strict --delivery-scope figures
```

同步器检查工作簿引用、`title`/`sgtitle`、声明导出文件、正式图存在性和源文件新旧关系，并计算 `matlab_script` 与 `figure_bundle` 分层哈希。

命名固定为 `q1_plot.m`、`q2_plot.m`；禁止 `q1_polt.m` 等拼写变体。
