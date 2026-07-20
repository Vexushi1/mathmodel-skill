%% 问题一敏感性与鲁棒性绘图模板
projectRoot = string(fileparts(fileparts(mfilename("fullpath"))));
problemName = "问题一";
books = hsk_read_result_workbooks(projectRoot, problemName);

sheet = "参数敏感性";
assert(any(books.robustnessSheets == sheet), "缺少工作表: %s", sheet);
data = readtable(books.robustness, "Sheet", sheet, "VariableNamingRule", "preserve");

fig = figure("Color", "w", "Position", [100, 100, 900, 620]);
ax = axes(fig);
% plot(ax, data.("参数取值"), data.("目标值"), "LineWidth", 2.2);
xlabel(ax, "参数取值");
ylabel(ax, "目标指标");
hsk_apply_scientific_style(fig);
% hsk_export_figure(fig, fullfile(projectRoot, "figures", "q1_sensitivity"), ["pdf", "png"]);
