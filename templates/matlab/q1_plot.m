%% q1_plot：问题一结果绘图入口（当前活动模板）
% 放在“问题一求解/”，与主求解Python、深化分析Python和两个标准工作簿同目录。
% 字段使用精确表头唯一匹配；期望列号仅用于结构漂移警告。
% 版式不预设，必须先按 modules/04_figure_evidence.md 的 Figure Layout Gate 动态判断。

clearvars;
clc;

%% 1. 路径
scriptPath = string(mfilename("fullpath"));
assert(strlength(scriptPath) > 0, "请从已保存的q1_plot.m运行脚本");
resultDir = string(fileparts(scriptPath));
solutionBook = fullfile(resultDir, "问题一求解结果.xlsx");
resultAnalysisBook = fullfile(resultDir, "问题一结果深化分析.xlsx");
assert(isfile(solutionBook), "缺少工作簿: %s", solutionBook);
assert(isfile(resultAnalysisBook), "缺少工作簿: %s", resultAnalysisBook);

%% 2. 实际结构锁定
% 图型选择以 Core conclusion / Evidence level / Primary question 和信息效率为准。
% 兼容检查标记：xColumn = NaN；actualXHeader == xHeader。
% 主结果图优先使用solutionBook；稳定性、阈值、算法或结构图优先使用resultAnalysisBook。
% 若图确实需要底层事实源，必须继承当前 preprocessing_decision；MATLAB 不重建模型变换。
sourceBook = solutionBook;
sourceSheet = "__ACTUAL_SHEET_NAME__";
xHeader = "__ACTUAL_X_HEADER__";
yHeader = "__ACTUAL_Y_HEADER__";
expectedXColumn = NaN;  % 可选，仅作结构漂移警告
expectedYColumn = NaN;
figureTitle = "__ACTUAL_FIGURE_TITLE__";
xLabelText = "__ACTUAL_X_LABEL_WITH_UNIT__";
yLabelText = "__ACTUAL_Y_LABEL_WITH_UNIT__";

placeholders = [sourceSheet, xHeader, yHeader, figureTitle, xLabelText, yLabelText];
assert(~any(startsWith(placeholders, "__ACTUAL_")), "模板尚未实例化");
assert(strlength(strtrim(figureTitle)) <= 30, "图标题过长");

availableSheets = string(sheetnames(sourceBook));
assert(any(availableSheets == sourceSheet), "缺少工作表: %s", sourceSheet);
raw = readcell(sourceBook, "Sheet", sourceSheet);
assert(size(raw, 1) >= 2, "工作表没有真实数据");
headers = strtrim(string(raw(1, :)));

xColumn = exact_header_column(headers, xHeader);
yColumn = exact_header_column(headers, yHeader);
warn_position_drift(xHeader, expectedXColumn, xColumn);
warn_position_drift(yHeader, expectedYColumn, yColumn);

x = cell_to_numeric(raw(2:end, xColumn));
y = cell_to_numeric(raw(2:end, yColumn));
valid = isfinite(x) & isfinite(y);
x = x(valid);
y = y(valid);
assert(~isempty(x), "没有可绘制的真实数据");
[x, order] = sort(x);
y = y(order);

%% 3. 正式结果图
% 这里只给单图骨架；若 Figure Layout Gate 判定为多面板，应实例化 tiledlayout，而不是机械沿用本段。
fig = figure("Color", "w", "Position", [100, 100, 900, 620]);
ax = axes(fig);
plot(ax, x, y, "LineWidth", 2.2, "Color", [20, 120, 255] / 255);  % #1478FF 亮蓝
xlabel(ax, xLabelText);
ylabel(ax, yLabelText);
title(ax, figureTitle, "FontWeight", "normal");
grid(ax, "off");
box(ax, "on");
apply_scientific_style(fig);

%% 4. 图窗保留供人工检查；本脚本默认不自动导出文件

function column = exact_header_column(headers, expected)
matches = find(headers == strtrim(string(expected)));
assert(numel(matches) == 1, "字段缺失或重复: %s", expected);
column = matches(1);
end

function warn_position_drift(header, expected, actual)
if isfinite(expected) && expected >= 1 && actual ~= expected
    warning("字段%s由第%d列移动到第%d列；已按精确表头读取", header, expected, actual);
end
end

function values = cell_to_numeric(column)
values = nan(size(column, 1), 1);
for i = 1:size(column, 1)
    item = column{i};
    if (isnumeric(item) || islogical(item)) && isscalar(item)
        values(i) = double(item);
    elseif ischar(item) || isstring(item)
        parsed = str2double(string(item));
        if isfinite(parsed), values(i) = parsed; end
    end
end
end

function apply_scientific_style(fig)
fontName = select_font();
set(fig, "Color", "w");
for ax = reshape(findall(fig, "Type", "axes"), 1, [])
    set(ax, "FontName", fontName, "FontSize", 18, "LineWidth", 1.4, "Box", "on", "Layer", "top");
    grid(ax, "off");
end
for lgd = reshape(findall(fig, "Type", "legend"), 1, [])
    set(lgd, "FontName", fontName, "FontSize", 16, "Box", "off");
end
end

function fontName = select_font()
preferred = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Arial Unicode MS", "Helvetica", "Arial"];
available = string(listfonts);
fontName = "Helvetica";
for candidate = preferred
    if any(strcmpi(available, candidate)), fontName = candidate; return; end
end
end
