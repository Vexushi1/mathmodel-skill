# HSK MATLAB 科研绘图模板 v6.2.5

MATLAB 只读取 Python 输出的两类标准工作簿，不重新求解。每问绘图脚本与工作簿同目录：

```text
结果数据表/问题X/
├─ 问题X求解结果.xlsx
├─ 问题X敏感性与鲁棒性结果.xlsx
├─ q{x}_plot.m
└─ 图表/
```

## 问题绘图脚本命名

每个问题只设置一个主绘图入口：

```text
结果数据表/问题一/q1_plot.m
结果数据表/问题二/q2_plot.m
结果数据表/问题三/q3_plot.m
...
```

规则为 `q{x}_plot.m`，其中 `x` 是阿拉伯数字问题编号。不要使用 `问题一结果绘图.m`、`plot_q1.m`、`q1_polt.m` 等其他命名。

## 默认单文件结构

`q{x}_plot.m` 默认自包含以下职责：

1. 用 `fileparts(mfilename("fullpath"))` 获取自身所在问题结果目录；
2. 直接定位同目录两类固定工作簿；
3. 检查文件、工作表、字段、空表和非法数值；
4. 显式排序时间、类别、名次或坐标；
5. 生成并保留可见图窗；
6. 单图设置简洁 `title`，多面板设置一个整体 `sgtitle`；
7. 人工调整后按需导出到同级 `图表/`；
8. 将图标题、图注、数据源、脚本和结论同步到项目根目录 `模型论文框架.md`。

简单项目不得强制额外生成 `hsk_find_project_root.m`、`hsk_read_result_workbooks.m`、样式函数或导出函数。多个问题确有共享需求时才抽取辅助函数，并仍以各问 `q{x}_plot.m` 为唯一入口。

## 推荐路径代码

```matlab
scriptPath = mfilename("fullpath");
if strlength(scriptPath) == 0
    resultDir = string(pwd);
else
    resultDir = string(fileparts(scriptPath));
end

solutionBook = fullfile(resultDir, "问题一求解结果.xlsx");
robustnessBook = fullfile(resultDir, "问题一敏感性与鲁棒性结果.xlsx");
figureDir = fullfile(resultDir, "图表");
```

## 图标题

- 单图使用 `title(ax, figureTitle, "FontWeight", "normal")`；
- 多面板使用 `sgtitle(layout, figureTitle, "FontWeight", "normal")`；
- 标题只写“研究对象 + 指标或关系 + 必要方法信息”，不写完整结论；
- 多面板只有在面板对象确有差异时再设置短子标题；
- 图标题默认保留在图窗和导出文件中；
- DOCX/LaTeX 图注补充统计口径、时间范围、误差和解释，不与图内标题逐字重复。

## 图型与配色

- 常规图表、饼图、环形图、雷达图、3D 柱状图、3D 曲面及其他高级图表均可使用；
- 选型依据是结论匹配、信息展示效率、比较效率、失真风险和可复现性；
- 默认色板为深蓝、青绿、蓝紫、暗红、米色、深灰和浅灰，可根据变量语义调整；
- 3D 图需要处理视角、遮挡、色条、投影和单位；必要时同时给出二维投影或等高线；
- 饼图和雷达图需控制类别或对象数量，并保留可核对的比例、标准化方法或数值信息。

禁止默认隐藏图窗、批量自动导出、关闭图窗、搜索多层项目目录、在 MATLAB 中重新计算核心结果或省略正式图标题。
