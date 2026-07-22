%% q1_plot：问题一结果绘图入口，只读取工作簿，不重新计算结果
scriptDir = string(fileparts(mfilename("fullpath")));
addpath(scriptDir);
addpath(string(fileparts(scriptDir)));
projectRoot = hsk_find_project_root(scriptDir);
problemName = "问题一";
books = hsk_read_result_workbooks(projectRoot, problemName);

requiredSheet = "明细结果";
assert(any(books.solutionSheets == requiredSheet), "缺少工作表: %s", requiredSheet);
data = readtable(books.solution, "Sheet", requiredSheet, ...
    "VariableNamingRule", "preserve");

% 按实际字段替换下列字段；时间、类别、名次或坐标需显式排序。
% data = sortrows(data, "排序字段");

% 图窗默认可见并保留。可根据证据任务使用二维图、饼图、雷达图、
% 3D 柱状图、3D 曲面或其他高级图表，但需通过信息效率与误导风险检查。
fig = figure("Color", "w", "Position", [100, 100, 900, 620]);
ax = axes(fig);
% plot(ax, data.("横轴字段"), data.("纵轴字段"), "LineWidth", 2.2);
% bar3(ax, ...);       % 仅在双分类结构确有额外表达价值时使用
% surf(ax, ...);       % 需设置色条、单位、视角，必要时附等高线
xlabel(ax, "横轴名称（单位）");
ylabel(ax, "纵轴名称（单位）");

% 返回默认规则色板。palette 仅作为起点，可按变量语义和图型灵活调整。
palette = hsk_apply_scientific_style(fig); %#ok<NASGU>

% 仅在存在有效图元时添加图例，避免空图例警告。
% legend(ax, "Location", "best", "Box", "off");

% 人工调整尺寸、颜色、三维视角、图例和标签后再显式导出：
% hsk_export_figure(fig, fullfile(projectRoot, "figures", "q1_core_result"), ["pdf", "png"]);
