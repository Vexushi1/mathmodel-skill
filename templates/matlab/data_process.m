%% data_process：项目级数据预处理证据绘图入口
% 仅 preprocessing_decision=project_level 时实例化并放入“数据预处理/”。
% 只读取“数据预处理结果.xlsx”中 Python 已输出的处理前/后与验证底层数据。
% 禁止在 MATLAB 中重新清洗、插值、滤波、重采样、训练填补模型或重新选择参数。
% 先执行 modules/04_figure_evidence.md 的 Scientific Figure Synthesis Gate 与 Basic-form Challenge；清楚的前后折线或点图可直接承担核心证据。
% Composite Encoding 仅在真实互补信息和可读性增益同时存在时使用；没有实际区间就不画带，不因额外维度存在而强制组合。
% 选定视觉结构后进入对应 Scientific Rendering Profile，再通过 Figure Layout Gate 与 Figure Enhancement Gate。
% 视觉结构确定后再进入 Publication Rendering Grammar：palette profile / open-axis / adaptive canvas / legend strategy；样式不得改变预处理证据语义。
% Enhancement 的实现模式参考 templates/figure/figure_enhancement_patterns.md，不得在本模板建立第二套绘图决策规则。
% 正式论文图不设置整体 title/sgtitle；正式图题由 LaTeX/DOCX caption 承担，多面板按需只保留 a/b/c/d 等 panel label。

clearvars;
clc;

%% 0. 本图视觉参数——实例化时按证据与版面填写
seriesColors = zeros(0, 3);  % 必填 N×3 RGB，范围 [0,1]；无默认色板，不自动循环补色
style = struct("fontName", "", "axesFontSize", 12, "labelFontSize", 13, ...
    "legendFontSize", 11, "colorbarFontSize", 11, ...
    "axesLineWidth", 0.8, "colorbarLineWidth", 0.8);  % 排版起点，可按实际图幅调整
figurePosition = [100, 100, 900, 560];
lineWidth = 1.6;
markerSize = 5;
markerEvery = 1;  % 有连续线时可稀疏标点，线仍保留全部数据；无连接线时显示全部点
connectPoints = false;  % 仅有真实连续/顺序语义时改为 true；数值编码的类别不自动连线
legendLocation = "best";
gridMode = "off";  % 需要辅助读数时可改为 on；局部覆盖在基础样式之后生效
axesBox = "off";
xLimits = [];  % 空表示 MATLAB 自动范围；比较图须按证据决定是否共用范围
yLimits = [];
seriesLabels = ["处理前", "处理后"];
markerSymbols = ["o", "s"];
seriesLineStyles = ["-", "--"];

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
xLabelText = "__ACTUAL_X_LABEL_WITH_UNIT__";
yLabelText = "__ACTUAL_Y_LABEL_WITH_UNIT__";
expectedXColumn = NaN;
expectedBeforeColumn = NaN;
expectedAfterColumn = NaN;
keyHeader = "";
allowMissingHeaders = strings(0, 1);  % 仅列出合同允许缺测的 before/after 字段
missingTokens = strings(0, 1);  % 仅填写真实的非数值缺测标记
sortByX = false;
sortReason = "";  % 路径/轨迹保留源顺序；时间排序需有明确理由

placeholders = [sourceSheet, xHeader, beforeHeader, afterHeader, xLabelText, yLabelText];
assert(~any(startsWith(placeholders, "__ACTUAL_")), "data_process模板尚未实例化");
xHeader = strtrim(string(xHeader));
beforeHeader = strtrim(string(beforeHeader));
afterHeader = strtrim(string(afterHeader));

availableSheets = string(sheetnames(processBook));
assert(any(availableSheets == sourceSheet), "缺少工作表: %s", sourceSheet);
raw = readcell(processBook, "Sheet", sourceSheet);
assert(size(raw, 1) >= 2, "预处理绘图工作表没有真实数据");
headers = strtrim(string(raw(1, :)));

xColumn = exact_header_column(headers, xHeader, processBook, sourceSheet);
beforeColumn = exact_header_column(headers, beforeHeader, processBook, sourceSheet);
afterColumn = exact_header_column(headers, afterHeader, processBook, sourceSheet);
warn_position_drift(xHeader, expectedXColumn, xColumn);
warn_position_drift(beforeHeader, expectedBeforeColumn, beforeColumn);
warn_position_drift(afterHeader, expectedAfterColumn, afterColumn);

% 保留全部导入记录；允许的缺测保留 NaN 断线，不裁掉一方缺测而另一方仍有值的行。
sourceRows = (2:size(raw, 1))';
recordKeys = read_record_keys(raw, headers, keyHeader, processBook, sourceSheet, sourceRows);
[allowMissingHeaders, missingTokens] = check_numeric_contract([xHeader, beforeHeader, afterHeader], xHeader, allowMissingHeaders, missingTokens);
x = cell_to_numeric(raw(2:end, xColumn), xHeader, false, missingTokens, processBook, sourceSheet, sourceRows, recordKeys);
before = cell_to_numeric(raw(2:end, beforeColumn), beforeHeader, any(allowMissingHeaders == beforeHeader), missingTokens, processBook, sourceSheet, sourceRows, recordKeys);
after = cell_to_numeric(raw(2:end, afterColumn), afterHeader, any(allowMissingHeaders == afterHeader), missingTokens, processBook, sourceSheet, sourceRows, recordKeys);
assert(any(isfinite(before) | isfinite(after)), "工作簿%s/工作表%s没有可绘制的有限前后值", processBook, sourceSheet);
assert(islogical(sortByX) && isscalar(sortByX), "sortByX 必须为 true 或 false");
if sortByX
    assert(isscalar(sortReason) && ~ismissing(sortReason) && strlength(strtrim(sortReason)) > 0, "排序必须声明真实的时间/连续变量语义");
    assert(numel(unique(x)) == numel(x), "工作簿%s/工作表%s的排序自变量重复；请按真实组别或记录键明确顺序，不能自动聚合", processBook, sourceSheet);
    [x, order] = sort(x);
    before = before(order);
    after = after(order);
    recordKeys = recordKeys(order);
    sourceRows = sourceRows(order);
end

%% 3. 处理前后结构读取示例——正式实例化时按 Evidence Structure 选择
% 若 x 具有时间/空间顺序，清楚的前后曲线可独立表达趋势；原始点/事件/误差仅按真实证据需要加入。
% 结论涉及分布时可用 box、raw scatter 或 ECDF；涉及二维参数/空间时可用 heatmap/field，contour/boundary 按需加入。
assert(isnumeric(seriesColors) && ismatrix(seriesColors) && size(seriesColors, 2) == 3 && ...
    size(seriesColors, 1) >= 2 && isreal(seriesColors) && ...
    all(isfinite(seriesColors(:))) && all(seriesColors(:) >= 0 & seriesColors(:) <= 1), ...
    "请在 seriesColors 按图填写足够的 [0,1] RGB 行；本模板不提供默认配色");
validateattributes(lineWidth, {'numeric'}, {'scalar', 'real', 'finite', 'positive'});
validateattributes(markerSize, {'numeric'}, {'scalar', 'real', 'finite', 'positive'});
validateattributes(markerEvery, {'numeric'}, {'scalar', 'real', 'finite', 'integer', 'positive'});
assert(islogical(connectPoints) && isscalar(connectPoints), "connectPoints 必须为 true 或 false");
assert(connectPoints || all(markerSymbols ~= "none"), "离散点图需要可见 marker");
fig = figure("Visible", "on", "Color", "w", "Position", figurePosition);
ax = axes(fig);
hold(ax, "on");
values = [before, after];  % 同一 x/记录键下配对；不分别过滤两列
for j = 1:2
    lineStyle = "none";
    if connectPoints, lineStyle = seriesLineStyles(j); end
    markerIndices = visible_marker_indices(values(:, j), markerEvery, lineStyle, markerSymbols(j));
    plot(ax, x, values(:, j), "LineStyle", lineStyle, "LineWidth", lineWidth, ...
        "Color", seriesColors(j, :), "Marker", markerSymbols(j), ...
        "MarkerIndices", markerIndices, "MarkerSize", markerSize, "DisplayName", seriesLabels(j));
end
xlabel(ax, xLabelText);
ylabel(ax, yLabelText);
legend(ax, "Location", legendLocation);
apply_publication_style(fig, style);  % 对象创建完成后只应用一次

% 当前图的局部覆盖最后生效；不要在这些设置后再次调用统一样式。
grid(ax, gridMode);
if gridMode == "on"
    ax.Layer = "bottom";  % 辅助网格放在数据后方
end
ax.Box = axesBox;
if ~isempty(xLimits), xlim(ax, xLimits); end
if ~isempty(yLimits), ylim(ax, yLimits); end

%% 4. 可选：按 Figure Contract 继续实例化真正需要的科研证据
% 推荐优先级：
% - before/after + raw points + error/threshold；
% - missing/recovery + true-vs-recovered + residual distribution；
% - frequency/spectrum before vs after；
% - resampling coverage / grid alignment；
% - heatmap/field + contour/boundary；
% - Local Zoom / overview+detail（仅关键差异被全局尺度压缩时）。
% 每个面板必须直接对应一个预处理必要性/有效性判断。
% 所有数值必须来自数据预处理结果.xlsx；不得从摘要数字反推序列。
% 若两个或更多证据并不回答同一个 Primary question，应拆为多张 Figure。

%% 5. 图窗保留供人工检查；默认不自动导出
% 正式导出时文件基名使用 data_process 或 data_process_<evidence>。

function indices = visible_marker_indices(values, every, lineStyle, marker)
% 无连线时显示全部点；连续线稀疏标点仍保留缺测间孤立的有效点。
indices = 1:numel(values);
if lineStyle == "none"
    assert(marker ~= "none", "无连线的系列必须使用可见 marker");
    return;
end
finite = isfinite(values);
isolated = finite & ~[false; finite(1:end-1)] & ~[finite(2:end); false];
assert(marker ~= "none" || ~any(isolated), "缺测间存在孤立有效点，请使用可见 marker 保留该证据");
indices = unique([1:every:numel(values), find(isolated)']);
end

function column = exact_header_column(headers, expected, workbook, sheet)
expected = strtrim(string(expected));
assert(isscalar(expected) && ~ismissing(expected) && strlength(expected) > 0, "工作簿%s/工作表%s要求非空标量表头", workbook, sheet);
matches = find(headers == expected);
assert(numel(matches) == 1, "工作簿%s/工作表%s字段缺失或重复: %s", workbook, sheet, expected);
column = matches(1);
end

function warn_position_drift(header, expected, actual)
assert(isnumeric(expected) && isscalar(expected) && isreal(expected) && ...
    (isnan(expected) || (isfinite(expected) && expected >= 1 && expected == floor(expected))), ...
    "字段%s的期望位置必须为正整数或 NaN", header);
if isfinite(expected) && actual ~= expected
    warning("字段%s由第%d列移动到第%d列；已按精确表头读取", header, expected, actual);
end
end

function [allowMissingHeaders, missingTokens] = check_numeric_contract(numericHeaders, xHeader, allowMissingHeaders, missingTokens)
assert(isstring(allowMissingHeaders) && (isvector(allowMissingHeaders) || isempty(allowMissingHeaders)) && ...
    ~any(ismissing(allowMissingHeaders(:))), "允许缺测字段必须为 string 向量");
allowMissingHeaders = strtrim(allowMissingHeaders(:));
assert(all(ismember(allowMissingHeaders, numericHeaders)) && ~any(allowMissingHeaders == xHeader), ...
    "允许缺测字段须为当前 y/前后指标；该数值曲线示例的 x 必须有限");
assert(isstring(missingTokens) && (isvector(missingTokens) || isempty(missingTokens)) && ...
    ~any(ismissing(missingTokens(:))), "缺测标记须为非空 string 向量");
missingTokens = strtrim(missingTokens(:));
assert(all(strlength(missingTokens) > 0), "缺测标记不能是空白文本");
parsedTokens = str2double(missingTokens);
assert(isreal(parsedTokens) && all(isnan(parsedTokens)), "缺测标记不能伪装有限数值、Inf 或复数");
end

function keys = read_record_keys(raw, headers, keyHeader, workbook, sheet, sourceRows)
keyHeader = strtrim(string(keyHeader));
assert(isscalar(keyHeader) && ~ismissing(keyHeader), "记录键表头必须为标量文本");
keys = strings(numel(sourceRows), 1);
if strlength(keyHeader) == 0, return; end
column = exact_header_column(headers, keyHeader, workbook, sheet);
for i = 1:numel(sourceRows)
    item = raw{sourceRows(i), column};
    validNumber = (isnumeric(item) || islogical(item)) && isscalar(item) && isreal(item) && isfinite(item);
    validText = (ischar(item) && isrow(item)) || (isstring(item) && isscalar(item) && ~ismissing(item));
    assert(validNumber || validText, "工作簿%s/工作表%s键字段%s读入行%d无有效标量键", workbook, sheet, keyHeader, sourceRows(i));
    if validNumber && ~isinteger(item)
        if item == 0
            keys(i) = "0";
        else
            keys(i) = string(sprintf("%.17g", double(item)));
        end
    else
        keys(i) = strtrim(string(item));
    end
    assert(strlength(keys(i)) > 0, "工作簿%s/工作表%s键字段%s读入行%d为空", workbook, sheet, keyHeader, sourceRows(i));
end
assert(numel(unique(keys)) == numel(keys), "工作簿%s/工作表%s键字段%s存在重复；请使用真实唯一键", workbook, sheet, keyHeader);
end

function values = cell_to_numeric(column, header, allowMissing, missingTokens, workbook, sheet, sourceRows, keys)
values = nan(size(column, 1), 1);
for i = 1:size(column, 1)
    item = column{i};
    isMissingValue = isempty(item) || isa(item, "missing");
    value = NaN;
    if ~isMissingValue && (isnumeric(item) || islogical(item))
        assert(isscalar(item) && isreal(item), "工作簿%s/工作表%s字段%s读入行%d键%s必须为实数标量", workbook, sheet, header, sourceRows(i), keys(i));
        value = double(item);
        isMissingValue = isnan(value);
    elseif ~isMissingValue && ((ischar(item) && isrow(item)) || (isstring(item) && isscalar(item)))
        text = strtrim(string(item));
        isMissingValue = ismissing(text) || strlength(text) == 0 || any(text == missingTokens);
        if ~isMissingValue
            value = str2double(text);
            assert(isreal(value) && isfinite(value), "工作簿%s/工作表%s字段%s读入行%d键%s包含非法数值文本", workbook, sheet, header, sourceRows(i), keys(i));
        end
    elseif ~isMissingValue
        error("工作簿%s/工作表%s字段%s读入行%d键%s包含不支持的单元格类型", workbook, sheet, header, sourceRows(i), keys(i));
    end
    if isMissingValue
        assert(allowMissing, "工作簿%s/工作表%s字段%s读入行%d键%s缺测但合同未允许；不会自动删行", workbook, sheet, header, sourceRows(i), keys(i));
    else
        assert(isfinite(value), "工作簿%s/工作表%s字段%s读入行%d键%s包含 Inf 或非法值", workbook, sheet, header, sourceRows(i), keys(i));
        values(i) = value;
    end
end
end

function apply_publication_style(fig, style)
% 独立入口只请求基础排版；图的 RGB 由脚本头部显式配置，不复制候选色板。
arguments
    fig (1,1) matlab.ui.Figure
    style (1,1) struct = struct()
end

assert(isgraphics(fig, "figure"), "fig 必须为有效 figure");
if exist("hsk_apply_scientific_style", "file") == 2
    hsk_apply_scientific_style(fig, "", style);
    return;
end
defaults = struct("fontName", "", "axesFontSize", 16, "labelFontSize", 18, ...
    "legendFontSize", 14, "colorbarFontSize", 14, ...
    "axesLineWidth", 1.15, "colorbarLineWidth", 1.0);
frame = struct("box", "off", "tick_dir", "out", "grid", "off");
apply_base_style(fig, style, defaults, frame);
end

function fontName = apply_base_style(fig, overrides, defaults, frame)
% 与独立入口 fallback 保持相同实现；先完整验证，再修改任何图形属性。
style = checked_style(overrides, defaults);
assert(isstring(frame.box) && isscalar(frame.box) && any(frame.box == ["on", "off"]), ...
    "基础 frame.box 必须为 on 或 off");
assert(isstring(frame.tick_dir) && isscalar(frame.tick_dir) && ...
    any(frame.tick_dir == ["in", "out", "both"]), "基础 frame.tick_dir 无效");
assert(isstring(frame.grid) && isscalar(frame.grid) && any(frame.grid == ["on", "off"]), ...
    "基础 frame.grid 必须为 on 或 off");
fontName = style.fontName;
if strlength(fontName) == 0
    fontName = select_style_font();
end

% findobj 不穿透隐藏图表内部；只处理公开的普通 axes。
for ax = reshape(findobj(fig, "Type", "axes"), 1, [])
    set(ax, "FontName", fontName, "FontUnits", "points", ...
        "FontSize", style.axesFontSize, "LineWidth", style.axesLineWidth);
    if isequal(ax.View, [0, 90])
        set(ax, "Box", frame.box, "Layer", "top", "TickDir", frame.tick_dir);
        grid(ax, frame.grid);
    end
    % yyaxis 的 YAxis 可有两个 ruler；逐个访问 Label，不切换活动侧。
    for axisName = ["XAxis", "YAxis", "ZAxis"]
        for ruler = reshape(ax.(axisName), 1, [])
            if isprop(ruler, "Label") && isgraphics(ruler.Label, "text")
                set(ruler.Label, "FontName", fontName, "FontUnits", "points", ...
                    "FontSize", style.labelFontSize);
            end
        end
    end
end

% 极坐标不套用 Cartesian 的 open-axis/grid 规则。
for ax = reshape(findobj(fig, "Type", "polaraxes"), 1, [])
    set(ax, "FontName", fontName, "FontUnits", "points", ...
        "FontSize", style.axesFontSize, "LineWidth", style.axesLineWidth);
end
% HeatmapChart 只有公共统一字号，不访问隐藏 axes 或把文字标签当 Text。
for chart = reshape(findobj(fig), 1, [])
    if isa(chart, "matlab.graphics.chart.HeatmapChart")
        set(chart, "FontName", fontName, "FontSize", style.axesFontSize);
    end
end
for txt = reshape(findobj(fig, "Type", "text"), 1, [])
    set(txt, "FontName", fontName);
end

% axes 字号可能影响关联对象，因此 legend/colorbar 最后设置。
for lgd = reshape(findobj(fig, "Type", "legend"), 1, [])
    set(lgd, "FontName", fontName, "FontUnits", "points", ...
        "FontSize", style.legendFontSize, "Box", "off");
end
for cb = reshape(findobj(fig, "Type", "colorbar"), 1, [])
    set(cb, "FontName", fontName, ...
        "FontSize", style.colorbarFontSize, "LineWidth", style.colorbarLineWidth);
    set(cb.Label, "FontName", fontName, "FontUnits", "points", ...
        "FontSize", style.colorbarFontSize);
end
end

function style = checked_style(overrides, defaults)
assert(isstruct(overrides) && isscalar(overrides), "style 必须为标量 struct");
style = defaults;
names = fieldnames(overrides);
unknown = setdiff(names, fieldnames(style));
assert(isempty(unknown), "未知 style 字段: %s", strjoin(string(unknown), ", "));
for i = 1:numel(names)
    style.(names{i}) = overrides.(names{i});
end
names = fieldnames(style);
for i = 1:numel(names)
    name = names{i};
    value = style.(name);
    if strcmp(name, "fontName")
        isText = (ischar(value) && (isrow(value) || isequal(size(value), [0, 0]))) || ...
            (isstring(value) && isscalar(value) && ~ismissing(value));
        assert(isText, "style.fontName 必须为非缺测标量文本；空文本表示本机字体候选");
        style.fontName = strtrim(string(value));
    else
        assert(isnumeric(value) && isscalar(value) && isreal(value) && ...
            isfinite(value) && value > 0, "style.%s 必须为有限正实标量", name);
        style.(name) = double(value);
    end
end
end

function fontName = select_style_font()
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
