%% q1_plot：问题一结果绘图入口
% 本文件应放在“结果数据表/问题一/”中，与两份问题一工作簿同目录。
% MATLAB 只读取工作簿绘图，不重新计算核心结果。
%
% 重要：本文件是实例化模板，不得直接作为正式脚本交付。
% 生成具体问题脚本前，必须先读取实际工作簿，并将全部 __ACTUAL_*__
% 替换为真实工作表名、真实表头、固定列位置、坐标轴名称和图标题。
% 正式脚本不得保留占位符，不得动态寻找替代表头。
% 单图必须保留简洁 title；多面板脚本应改用一个整体 sgtitle。

clearvars;
clc;

%% 1. 当前问题结果目录
scriptPath = string(mfilename("fullpath"));
if strlength(scriptPath) == 0
    resultDir = string(pwd);
else
    resultDir = string(fileparts(scriptPath));
end

solutionBook = fullfile(resultDir, "问题一求解结果.xlsx");
robustnessBook = fullfile(resultDir, "问题一敏感性与鲁棒性结果.xlsx");
figureDir = fullfile(resultDir, "图表");
EXPORT_FIGURES = false;

assert(isfile(solutionBook), "缺少求解结果工作簿: %s", solutionBook);
assert(isfile(robustnessBook), "缺少敏感性与鲁棒性工作簿: %s", robustnessBook);

%% 2. 实际工作簿结构与图标题锁定
% 以下内容必须由生成器在读取实际工作簿后写成真实值。
sourceBook = solutionBook;
sourceSheet = "__ACTUAL_SHEET_NAME__";
xHeader = "__ACTUAL_X_HEADER__";
yHeader = "__ACTUAL_Y_HEADER__";
xColumn = NaN;
yColumn = NaN;
figureTitle = "__ACTUAL_FIGURE_TITLE__";

assert(~startsWith(sourceSheet, "__ACTUAL_"), ...
    "MATLAB 模板尚未按实际工作簿实例化：工作表名未替换");
assert(~startsWith(xHeader, "__ACTUAL_"), ...
    "MATLAB 模板尚未按实际工作簿实例化：横轴表头未替换");
assert(~startsWith(yHeader, "__ACTUAL_"), ...
    "MATLAB 模板尚未按实际工作簿实例化：纵轴表头未替换");
assert(~startsWith(figureTitle, "__ACTUAL_") && strlength(strtrim(figureTitle)) > 0, ...
    "MATLAB 模板尚未按实际问题实例化：图标题未替换");
assert(strlength(figureTitle) <= 30, ...
    "图标题过长：请只保留研究对象、指标关系和必要方法信息");
assert(isfinite(xColumn) && xColumn >= 1 && xColumn == floor(xColumn), ...
    "MATLAB 模板尚未按实际工作簿实例化：横轴固定列号未填写");
assert(isfinite(yColumn) && yColumn >= 1 && yColumn == floor(yColumn), ...
    "MATLAB 模板尚未按实际工作簿实例化：纵轴固定列号未填写");

availableSheets = string(sheetnames(sourceBook));
assert(any(availableSheets == sourceSheet), ...
    "工作簿“%s”缺少已锁定工作表“%s”", sourceBook, sourceSheet);

raw = readcell(sourceBook, "Sheet", sourceSheet);
assert(size(raw, 1) >= 2, "工作表“%s”没有真实数据", sourceSheet);
assert(size(raw, 2) >= max(xColumn, yColumn), ...
    "工作表“%s”的列数少于已锁定列位置", sourceSheet);

actualXHeader = strtrim(string(raw{1, xColumn}));
actualYHeader = strtrim(string(raw{1, yColumn}));
assert(actualXHeader == xHeader, ...
    "工作表“%s”第%d列表头应为“%s”，实际为“%s”", ...
    sourceSheet, xColumn, xHeader, actualXHeader);
assert(actualYHeader == yHeader, ...
    "工作表“%s”第%d列表头应为“%s”，实际为“%s”", ...
    sourceSheet, yColumn, yHeader, actualYHeader);

x = cell_to_numeric(raw(2:end, xColumn));
y = cell_to_numeric(raw(2:end, yColumn));
valid = isfinite(x) & isfinite(y);
x = x(valid);
y = y(valid);
assert(~isempty(x), "工作表“%s”没有可绘制的真实数据", sourceSheet);

% 时间、类别、名次或坐标必须显式排序，不依赖 Excel 原始顺序。
[x, order] = sort(x);
y = y(order);

%% 3. 正式结果图
% 图型依据 Core conclusion、底层数据和信息效率选择；高级图表不得制造遮挡或比例失真。
fig = figure("Color", "w", "Position", [100, 100, 900, 620]);
ax = axes(fig);
hold(ax, "on");

plot(ax, x, y, ...
    "LineWidth", 2.2, ...
    "Color", [23, 59, 94] / 255);

xlabel(ax, "__ACTUAL_X_LABEL_WITH_UNIT__");
ylabel(ax, "__ACTUAL_Y_LABEL_WITH_UNIT__");
title(ax, figureTitle, "FontWeight", "normal");
grid(ax, "off");
box(ax, "on");
hold(ax, "off");

assert(~contains(string(ax.XLabel.String), "__ACTUAL_"), ...
    "横轴名称尚未按实际字段替换");
assert(~contains(string(ax.YLabel.String), "__ACTUAL_"), ...
    "纵轴名称尚未按实际字段替换");
assert(strlength(strtrim(string(ax.Title.String))) > 0, ...
    "正式结果图必须保留简洁图标题");

apply_scientific_style(fig);

%% 4. 人工调整后可选导出
% 默认不自动导出、不关闭图窗。确认尺寸、图例、标题、标签和视角后再设为 true。
if EXPORT_FIGURES
    if ~isfolder(figureDir)
        mkdir(figureDir);
    end
    exportgraphics(fig, fullfile(figureDir, "q1_core_result.pdf"), ...
        "ContentType", "vector");
    exportgraphics(fig, fullfile(figureDir, "q1_core_result.png"), ...
        "Resolution", 600);
end

%% 局部函数
function values = cell_to_numeric(column)
values = nan(size(column, 1), 1);
for i = 1:size(column, 1)
    item = column{i};
    if isnumeric(item) && isscalar(item)
        values(i) = double(item);
    elseif islogical(item) && isscalar(item)
        values(i) = double(item);
    elseif ischar(item) || isstring(item)
        parsed = str2double(string(item));
        if isfinite(parsed)
            values(i) = parsed;
        end
    end
end
end

function apply_scientific_style(fig)
fontName = select_font();
set(fig, "Color", "w");
axesList = findall(fig, "Type", "axes");
for ax = reshape(axesList, 1, [])
    set(ax, "FontName", fontName, "FontSize", 18, ...
        "LineWidth", 1.4, "Box", "on", "Layer", "top");
    grid(ax, "off");
    if isprop(ax, "Title") && isgraphics(ax.Title)
        set(ax.Title, "FontName", fontName, "FontSize", 18, ...
            "FontWeight", "normal");
    end
end
legendList = findall(fig, "Type", "legend");
for lgd = reshape(legendList, 1, [])
    set(lgd, "FontName", fontName, "FontSize", 16, "Box", "off");
end
end

function fontName = select_font()
preferred = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", ...
    "Arial Unicode MS", "Helvetica", "Arial"];
available = string(listfonts);
fontName = "Helvetica";
for candidate = preferred
    if any(strcmpi(available, candidate))
        fontName = candidate;
        return;
    end
end
end
