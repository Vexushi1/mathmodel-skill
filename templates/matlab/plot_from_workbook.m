%% 问题一结果绘图模板：读取工作簿，不重新计算结果
scriptDir = string(fileparts(mfilename("fullpath")));
addpath(scriptDir);
addpath(string(fileparts(scriptDir)));
projectRoot = hsk_find_project_root(scriptDir);
problemName = "问题一";
books = hsk_read_result_workbooks(projectRoot, problemName);

requiredSheet = "明细结果";
assert(any(books.solutionSheets == requiredSheet), "缺少工作表: %s", requiredSheet);
data = readtable(books.solution, "Sheet", requiredSheet, "VariableNamingRule", "preserve");

% 按实际字段替换下列两列；图窗默认可见并保留。
fig = figure("Color", "w", "Position", [100, 100, 900, 620]);
ax = axes(fig);
% plot(ax, data.("横轴字段"), data.("纵轴字段"), "LineWidth", 2.2);
xlabel(ax, "横轴名称（单位）");
ylabel(ax, "纵轴名称（单位）");
% 仅在存在有效图元时添加图例，避免空图例警告。
% legend(ax, "Location", "best", "Box", "off");
hsk_apply_scientific_style(fig);

% 人工调整完成后再显式导出：
% hsk_export_figure(fig, fullfile(projectRoot, "figures", "q1_core_result"), ["pdf", "png"]);
