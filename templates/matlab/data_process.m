%% data_process：项目级数据预处理证据绘图入口
% 仅 preprocessing_decision=project_level 时实例化并放入“数据预处理/”。
% 只读取“数据预处理结果.xlsx”中 Python 已输出的处理前/后与验证底层数据。
% 禁止在 MATLAB 中重新清洗、插值、滤波、重采样、训练填补模型或重新选择参数。
% 版式同样服从 modules/04_figure_evidence.md 的 Figure Layout Gate，不默认多面板。

clearvars;
clc;

%% 1. 路径
scriptPath = string(mfilename("fullpath"));
assert(strlength(scriptPath) > 0, "请从已保存的data_process.m运行脚本");
processDir = string(fileparts(scriptPath));
processBook = fullfile(processDir, "数据预处理结果.xlsx");
assert(isfile(processBook), "缺少工作簿: %s", processBook);

%% 2. 图证据合同——实例化时必须替换真实字段
sourceSheet = "__ACTUAL_SOURCE_SHEET__";
xHeader = "__ACTUAL_X_HEADER__";
beforeHeader = "__ACTUAL_BEFORE_HEADER__";
afterHeader = "__ACTUAL_AFTER_HEADER__";
figureTitle = "__ACTUAL_PREPROCESSING_FIGURE_TITLE__";
xLabelText = "__ACTUAL_X_LABEL_WITH_UNIT__";
yLabelText = "__ACTUAL_Y_LABEL_WITH_UNIT__";
expectedXColumn = NaN;
expectedBeforeColumn = NaN;
expectedAfterColumn = NaN;

placeholders = [sourceSheet, xHeader, beforeHeader, afterHeader, figureTitle, xLabelText, yLabelText];
assert(~any(startsWith(placeholders, "__ACTUAL_")), "data_process模板尚未实例化");
assert(strlength(strtrim(figureTitle)) <= 30, "图标题过长");

availableSheets = string(sheetnames(processBook));
assert(any(availableSheets == sourceSheet), "缺少工作表: %s", sourceSheet);
raw = readcell(processBook, "Sheet", sourceSheet);
assert(size(raw, 1) >= 2, "预处理绘图工作表没有真实数据");
headers = strtrim(string(raw(1, :)));

xColumn = exact_header_column(headers, xHeader);
beforeColumn = exact_header_column(headers, beforeHeader);
afterColumn = exact_header_column(headers, afterHeader);
warn_position_drift(xHeader, expectedXColumn, xColumn);
warn_position_drift(beforeHeader, expectedBeforeColumn, beforeColumn);
warn_position_drift(afterHeader, expectedAfterColumn, afterColumn);

x = cell_to_numeric(raw(2:end, xColumn));
before = cell_to_numeric(raw(2:end, beforeColumn));
after = cell_to_numeric(raw(2:end, afterColumn));
valid = isfinite(x) & (isfinite(before) | isfinite(after));
x = x(valid);
before = before(valid);
after = after(valid);
assert(~isempty(x), "没有可绘制的预处理底层数据");
[x, order] = sort(x);
before = before(order);
after = after(order);

%% 3. 处理前后证据图
% “处理前”作为参考对象降权，“处理后”作为主比较对象使用高对比主色。
fig = figure("Color", "w", "Position", [100, 100, 960, 620]);
ax = axes(fig);
hold(ax, "on");
plot(ax, x, before, "LineWidth", 1.8, "Color", [37, 43, 55] / 255, "DisplayName", "处理前");
plot(ax, x, after, "LineWidth", 2.2, "Color", [240, 68, 68] / 255, "DisplayName", "处理后"); % #F04444
xlabel(ax, xLabelText);
ylabel(ax, yLabelText);
title(ax, figureTitle, "FontWeight", "normal");
legend(ax, "Location", "best");
grid(ax, "off");
box(ax, "on");
apply_scientific_style(fig);

%% 4. 可选：按“绘图数据索引”继续实例化掩蔽恢复、误差分布、频谱或覆盖证据
% 每个面板必须直接对应一个预处理必要性/有效性判断。
% 所有数值必须来自数据预处理结果.xlsx；不得从摘要数字反推序列。
% 若两个或更多证据并不回答同一个 Primary question，应拆为多张 Figure。

%% 5. 图窗保留供人工检查；默认不自动导出
% 正式导出时文件基名使用 data_process 或 data_process_<evidence>。

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
