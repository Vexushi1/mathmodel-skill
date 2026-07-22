function figureRegistry = QX_plot()
% QX_plot 单问题全图绘制入口模板。
% 实例化时必须同时替换文件名、函数名、problemIndex 和 problemName：
%   问题一 -> Q1_plot.m / function Q1_plot()
%   问题二 -> Q2_plot.m / function Q2_plot()
%
% 一次运行生成该问题全部需要的结果图、诊断图、敏感性图和鲁棒性图。
% 支持 single / layered / multi-panel / hybrid 四级图形复杂度。
% 本文件只读取 Python 输出的两类标准工作簿，不重新计算核心结果。
% 所有辅助逻辑均为文件末尾本地函数，项目交付不得再生成其他辅助 .m 文件。

%% 1. 问题配置：实例化时必须修改
problemIndex = 1;
problemName = "问题一";
exportFigures = false;          % 默认保留可见图窗，人工确认后再改为 true
exportFormats = ["pdf", "png"];
buildEvidenceComposite = true;  % 数据充分时生成一张混合组合证据图

scriptDir = string(fileparts(mfilename("fullpath")));
projectRoot = find_project_root(scriptDir);
books = locate_result_workbooks(projectRoot, problemName);
palette = high_contrast_palette();
filePrefix = "q" + string(problemIndex);
figureRegistry = struct("id", {}, "handle", {}, "fileBase", {});

coreData = table();
sensitivityData = table();
robustnessData = table();

%% 2. 核心结果：折线/散点/区间带等按真实字段选择
if has_sheet(books.solution, "明细结果")
    coreData = read_required_table(books.solution, "明细结果", ...
        ["横轴字段", "纵轴字段"]);
    fig = plot_core_result(coreData, palette);
    figureRegistry(end + 1) = register_figure( ...
        "core_result", fig, filePrefix + "_core_result"); %#ok<AGROW>
end

%% 3. 多算法或方案比较：优先使用层叠组合图
if has_sheet(books.solution, "多算法对比")
    compareData = read_required_table(books.solution, "多算法对比", ...
        ["算法", "目标值", "可行性"]);
    if has_columns(compareData, "运行时间")
        fig = plot_bar_line_combo(string(compareData.("算法")), ...
            compareData.("目标值"), compareData.("运行时间"), ...
            "目标值（单位）", "运行时间（s）", palette, true);
    else
        fig = plot_bar_point_combo(string(compareData.("算法")), ...
            compareData.("目标值"), string(compareData.("可行性")), palette);
    end
    figureRegistry(end + 1) = register_figure( ...
        "algorithm_comparison", fig, filePrefix + "_algorithm_comparison"); %#ok<AGROW>
end

%% 4. 参数敏感性：多曲线或中心线+区间带
if has_sheet(books.robustness, "参数敏感性")
    sensitivityData = read_required_table(books.robustness, "参数敏感性", ...
        ["参数", "扰动值", "目标指标"]);
    fig = plot_sensitivity(sensitivityData, palette);
    figureRegistry(end + 1) = register_figure( ...
        "sensitivity", fig, filePrefix + "_sensitivity"); %#ok<AGROW>
end

%% 5. 鲁棒性：逐场景数据优先箱线/小提琴+散点，只有区间时使用区间点图
if has_sheet(books.robustness, "扰动明细")
    robustnessData = read_required_table(books.robustness, "扰动明细", ...
        ["场景", "指标值"]);
    group = string(robustnessData.("场景"));
    value = robustnessData.("指标值");
    if minimum_group_size(group) >= 8
        fig = plot_violin_scatter_combo(group, value, palette);
    else
        fig = plot_box_scatter_combo(group, value, palette);
    end
    figureRegistry(end + 1) = register_figure( ...
        "robustness_distribution", fig, filePrefix + "_robustness_distribution"); %#ok<AGROW>
elseif has_sheet(books.robustness, "鲁棒性区间")
    robustnessData = read_required_table(books.robustness, "鲁棒性区间", ...
        ["指标", "下界", "上界"]);
    fig = plot_robustness_interval(robustnessData, palette);
    figureRegistry(end + 1) = register_figure( ...
        "robustness_interval", fig, filePrefix + "_robustness_interval"); %#ok<AGROW>
end

%% 6. 混合组合证据图：主结果 + 敏感性 + 鲁棒性
if buildEvidenceComposite && ~isempty(coreData) && ~isempty(sensitivityData) && ~isempty(robustnessData)
    fig = plot_hybrid_evidence_combo(coreData, sensitivityData, robustnessData, palette);
    figureRegistry(end + 1) = register_figure( ...
        "evidence_composite", fig, filePrefix + "_evidence_composite"); %#ok<AGROW>
end

%% 7. 统一样式与可选导出
if isempty(figureRegistry)
    error("未生成任何图。请核对工作表、字段和本问题的绘图函数。");
end

for k = 1:numel(figureRegistry)
    apply_scientific_style(figureRegistry(k).handle, palette);
    if exportFigures
        outputBase = fullfile(projectRoot, "figures", figureRegistry(k).fileBase);
        export_figure(figureRegistry(k).handle, outputBase, exportFormats);
    end
end

fprintf("%s 共生成 %d 个图窗。\n", problemName, numel(figureRegistry));
if ~exportFigures
    fprintf("图窗已保留；人工调整完成后将 exportFigures 改为 true 再运行导出。\n");
end
end

%% ======================== 问题专属绘图函数 ========================
function fig = plot_core_result(data, palette)
% 若工作簿提供上下界，使用中心线+区间带；否则使用折线+原始点。
x = data.("横轴字段");
y = data.("纵轴字段");
fig = create_figure("核心结果", [80, 80, 1020, 680]);
ax = axes(fig);
if has_columns(data, ["下界", "上界"])
    draw_line_band(ax, x, y, data.("下界"), data.("上界"), palette.navy, palette);
else
    hold(ax, "on");
    plot(ax, x, y, "-", "Color", palette.navy, "LineWidth", 2.8);
    scatter(ax, x, y, 54, palette.navy, "filled", ...
        "MarkerFaceAlpha", 0.82, "MarkerEdgeColor", palette.ink, "LineWidth", 0.7);
    hold(ax, "off");
end
xlabel(ax, "横轴名称（单位）");
ylabel(ax, "纵轴名称（单位）");
end

function fig = plot_bar_line_combo(category, barValues, lineValues, barLabel, lineLabel, palette, useDualAxis)
% 柱状 + 折线组合。双轴仅在单位不同且具有明确机制关系时使用。
category = string(category(:));
barValues = barValues(:);
lineValues = lineValues(:);
assert(numel(category) == numel(barValues) && numel(category) == numel(lineValues), ...
    "柱线组合的类别、柱值和线值长度必须一致。");

fig = create_figure("柱线组合", [100, 90, 1040, 680]);
ax = axes(fig);
x = 1:numel(category);
hold(ax, "on");
if useDualAxis
    yyaxis(ax, "left");
end
b = bar(ax, x, barValues, 0.64, "FaceColor", palette.navy, ...
    "EdgeColor", palette.ink, "LineWidth", 0.9);
b.FaceAlpha = 0.90;
ylabel(ax, barLabel);

if useDualAxis
    yyaxis(ax, "right");
end
plot(ax, x, lineValues, "-o", "Color", palette.orange, ...
    "LineWidth", 2.7, "MarkerSize", 7.5, ...
    "MarkerFaceColor", palette.orange, "MarkerEdgeColor", palette.ink);
ylabel(ax, lineLabel);
xticks(ax, x);
xticklabels(ax, category);
xlim(ax, [0.35, numel(category) + 0.65]);
if useDualAxis
    ax.YAxis(1).Color = palette.navy;
    ax.YAxis(2).Color = palette.orange;
end
hold(ax, "off");
end

function fig = plot_bar_point_combo(category, value, feasible, palette)
% 柱体承担目标规模，顶层点和不可行标记承担结论。
category = string(category(:));
value = value(:);
feasible = string(feasible(:));
fig = create_figure("方案比较", [120, 110, 1000, 660]);
ax = axes(fig);
x = 1:numel(category);
hold(ax, "on");
b = bar(ax, x, value, 0.62, "FaceColor", palette.teal, ...
    "EdgeColor", palette.ink, "LineWidth", 0.9);
b.FaceAlpha = 0.90;
scatter(ax, x, value, 62, palette.orange, "filled", ...
    "MarkerEdgeColor", palette.ink, "LineWidth", 0.8);
for i = 1:numel(value)
    if ~is_feasible(feasible(i))
        scatter(ax, x(i), value(i), 92, "x", "MarkerEdgeColor", palette.red, "LineWidth", 2.2);
    end
end
xticks(ax, x);
xticklabels(ax, category);
xlim(ax, [0.35, numel(category) + 0.65]);
ylabel(ax, "目标值（单位）");
hold(ax, "off");
end

function fig = plot_scatter_fit_combo(x, y, modelX, modelY, lowerBound, upperBound, palette)
% 散点 + 模型线 + 区间带。模型线和区间必须来自 Python 工作簿。
fig = create_figure("散点与模型关系", [140, 120, 980, 660]);
ax = axes(fig);
hold(ax, "on");
if ~isempty(lowerBound) && ~isempty(upperBound)
    fill_band(ax, modelX, lowerBound, upperBound, palette.teal, 0.16);
end
scatter(ax, x, y, 46, palette.navy, "filled", ...
    "MarkerFaceAlpha", 0.58, "MarkerEdgeColor", palette.ink, "LineWidth", 0.55);
plot(ax, modelX, modelY, "-", "Color", palette.red, "LineWidth", 2.7);
hold(ax, "off");
xlabel(ax, "解释变量（单位）");
ylabel(ax, "响应变量（单位）");
end

function fig = plot_box_scatter_combo(group, value, palette)
% 箱线 + 确定性抖动散点，不依赖额外工具箱。
[groupLevels, groupIndex] = stable_group_index(group);
fig = create_figure("箱线与原始样本", [160, 130, 1000, 680]);
ax = axes(fig);
hold(ax, "on");
colors = role_colors(palette);
for i = 1:numel(groupLevels)
    values = value(groupIndex == i);
    color = colors(mod(i - 1, size(colors, 1)) + 1, :);
    draw_custom_box(ax, i, values, color, palette);
    jitter = deterministic_jitter(numel(values), 0.16);
    scatter(ax, i + jitter, values, 34, color, "filled", ...
        "MarkerFaceAlpha", 0.58, "MarkerEdgeColor", palette.ink, "LineWidth", 0.45);
end
xticks(ax, 1:numel(groupLevels));
xticklabels(ax, groupLevels);
xlim(ax, [0.45, numel(groupLevels) + 0.55]);
ylabel(ax, "指标值（单位）");
hold(ax, "off");
end

function fig = plot_violin_scatter_combo(group, value, palette)
% 小提琴 + 中位数/IQR + 原始散点；小样本应在主流程中降级为箱线+散点。
[groupLevels, groupIndex] = stable_group_index(group);
fig = create_figure("分布形状与原始样本", [180, 150, 1040, 700]);
ax = axes(fig);
hold(ax, "on");
colors = role_colors(palette);
for i = 1:numel(groupLevels)
    values = value(groupIndex == i);
    color = colors(mod(i - 1, size(colors, 1)) + 1, :);
    [gridValues, density] = gaussian_kde(values, 120);
    width = 0.34 * density / max(density);
    patch(ax, [i - width; flipud(i + width)], ...
        [gridValues; flipud(gridValues)], color, ...
        "FaceAlpha", 0.24, "EdgeColor", color, "LineWidth", 1.0);
    draw_custom_box(ax, i, values, color, palette, 0.13);
    jitter = deterministic_jitter(numel(values), 0.13);
    scatter(ax, i + jitter, values, 30, color, "filled", ...
        "MarkerFaceAlpha", 0.62, "MarkerEdgeColor", palette.ink, "LineWidth", 0.4);
end
xticks(ax, 1:numel(groupLevels));
xticklabels(ax, groupLevels);
xlim(ax, [0.45, numel(groupLevels) + 0.55]);
ylabel(ax, "指标值（单位）");
hold(ax, "off");
end

function fig = plot_hist_density_combo(value, palette)
% 直方图 + 固定带宽 KDE + 中位数参考线。
value = value(isfinite(value));
fig = create_figure("分布与密度", [200, 170, 980, 650]);
ax = axes(fig);
hold(ax, "on");
h = histogram(ax, value, "Normalization", "pdf", ...
    "FaceColor", palette.lightGray, "EdgeColor", palette.ink, "LineWidth", 0.8);
h.FaceAlpha = 0.82;
[gridValues, density] = gaussian_kde(value, 160);
plot(ax, gridValues, density, "-", "Color", palette.purple, "LineWidth", 2.7);
medianValue = percentile(value, 50);
xline(ax, medianValue, "--", "Color", palette.orange, "LineWidth", 1.7);
hold(ax, "off");
xlabel(ax, "指标值（单位）");
ylabel(ax, "概率密度");
end

function fig = plot_sensitivity(data, palette)
parameter = string(data.("参数"));
perturbation = data.("扰动值");
response = data.("目标指标");
parameterLevels = unique(parameter, "stable");
colors = role_colors(palette);
fig = create_figure("参数敏感性", [220, 190, 1040, 690]);
ax = axes(fig);
hold(ax, "on");
for i = 1:numel(parameterLevels)
    idx = parameter == parameterLevels(i);
    [x, order] = sort(perturbation(idx));
    y = response(idx);
    color = colors(mod(i - 1, size(colors, 1)) + 1, :);
    plot(ax, x, y(order), "-o", "LineWidth", 2.35, "MarkerSize", 6.2, ...
        "Color", color, "MarkerFaceColor", "w", "MarkerEdgeColor", color, ...
        "DisplayName", parameterLevels(i));
end
xline(ax, 0, ":", "Color", palette.gray, "LineWidth", 1.2, "HandleVisibility", "off");
hold(ax, "off");
xlabel(ax, "参数扰动值（单位）");
ylabel(ax, "目标指标（单位）");
legend(ax, "Location", "northoutside", "Orientation", "horizontal", "Box", "off");
end

function fig = plot_robustness_interval(data, palette)
metric = string(data.("指标"));
lowerBound = data.("下界");
upperBound = data.("上界");
center = (lowerBound + upperBound) / 2;
negativeError = center - lowerBound;
positiveError = upperBound - center;
fig = create_figure("鲁棒性区间", [240, 210, 1000, 670]);
ax = axes(fig);
x = 1:numel(metric);
hold(ax, "on");
errorbar(ax, x, center, negativeError, positiveError, "o", ...
    "Color", palette.red, "MarkerFaceColor", palette.orange, ...
    "MarkerEdgeColor", palette.ink, "MarkerSize", 8, ...
    "LineWidth", 2.0, "CapSize", 12);
scatter(ax, x, center, 74, palette.orange, "filled", ...
    "MarkerEdgeColor", palette.ink, "LineWidth", 0.8);
xticks(ax, x);
xticklabels(ax, metric);
xlim(ax, [0.5, numel(metric) + 0.5]);
ylabel(ax, "指标区间（单位）");
hold(ax, "off");
end

function fig = plot_hybrid_evidence_combo(coreData, sensitivityData, robustnessData, palette)
% 混合组合图：主面板使用折线/区间叠加，辅助面板使用敏感性和分布/区间叠加。
fig = create_figure("核心证据组合", [60, 50, 1280, 900]);
t = tiledlayout(fig, 2, 2, "TileSpacing", "compact", "Padding", "compact");

axA = nexttile(t, [1, 2]);
draw_core_on_axes(axA, coreData, palette);
add_panel_label(axA, "a", palette);

axB = nexttile(t);
draw_sensitivity_on_axes(axB, sensitivityData, palette);
add_panel_label(axB, "b", palette);

axC = nexttile(t);
if has_columns(robustnessData, ["场景", "指标值"])
    draw_box_scatter_on_axes(axC, string(robustnessData.("场景")), ...
        robustnessData.("指标值"), palette);
else
    draw_robustness_interval_on_axes(axC, robustnessData, palette);
end
add_panel_label(axC, "c", palette);
end

%% ======================== 可复用图层函数 ========================
function draw_line_band(ax, x, center, lowerBound, upperBound, color, palette)
hold(ax, "on");
fill_band(ax, x, lowerBound, upperBound, color, 0.18);
plot(ax, x, center, "-", "Color", color, "LineWidth", 2.8);
scatter(ax, x, center, 46, color, "filled", ...
    "MarkerFaceAlpha", 0.85, "MarkerEdgeColor", palette.ink, "LineWidth", 0.55);
hold(ax, "off");
end

function fill_band(ax, x, lowerBound, upperBound, color, alphaValue)
x = x(:);
lowerBound = lowerBound(:);
upperBound = upperBound(:);
patch(ax, [x; flipud(x)], [lowerBound; flipud(upperBound)], color, ...
    "FaceAlpha", alphaValue, "EdgeColor", "none", "HandleVisibility", "off");
end

function draw_core_on_axes(ax, data, palette)
x = data.("横轴字段");
y = data.("纵轴字段");
if has_columns(data, ["下界", "上界"])
    draw_line_band(ax, x, y, data.("下界"), data.("上界"), palette.navy, palette);
else
    hold(ax, "on");
    plot(ax, x, y, "-", "Color", palette.navy, "LineWidth", 2.8);
    scatter(ax, x, y, 46, palette.navy, "filled", ...
        "MarkerFaceAlpha", 0.78, "MarkerEdgeColor", palette.ink, "LineWidth", 0.5);
    hold(ax, "off");
end
xlabel(ax, "横轴名称（单位）");
ylabel(ax, "纵轴名称（单位）");
end

function draw_sensitivity_on_axes(ax, data, palette)
parameter = string(data.("参数"));
perturbation = data.("扰动值");
response = data.("目标指标");
levels = unique(parameter, "stable");
colors = role_colors(palette);
hold(ax, "on");
for i = 1:numel(levels)
    idx = parameter == levels(i);
    [x, order] = sort(perturbation(idx));
    y = response(idx);
    color = colors(mod(i - 1, size(colors, 1)) + 1, :);
    plot(ax, x, y(order), "-o", "Color", color, "LineWidth", 2.0, ...
        "MarkerSize", 4.8, "DisplayName", levels(i));
end
xline(ax, 0, ":", "Color", palette.gray, "LineWidth", 1.0, "HandleVisibility", "off");
hold(ax, "off");
xlabel(ax, "扰动值");
ylabel(ax, "目标指标");
legend(ax, "Location", "best", "Box", "off");
end

function draw_box_scatter_on_axes(ax, group, value, palette)
[levels, index] = stable_group_index(group);
colors = role_colors(palette);
hold(ax, "on");
for i = 1:numel(levels)
    values = value(index == i);
    color = colors(mod(i - 1, size(colors, 1)) + 1, :);
    draw_custom_box(ax, i, values, color, palette, 0.22);
    scatter(ax, i + deterministic_jitter(numel(values), 0.12), values, 24, color, ...
        "filled", "MarkerFaceAlpha", 0.55, "MarkerEdgeColor", palette.ink, "LineWidth", 0.35);
end
xticks(ax, 1:numel(levels));
xticklabels(ax, levels);
xlim(ax, [0.45, numel(levels) + 0.55]);
ylabel(ax, "指标值");
hold(ax, "off");
end

function draw_robustness_interval_on_axes(ax, data, palette)
metric = string(data.("指标"));
lowerBound = data.("下界");
upperBound = data.("上界");
center = (lowerBound + upperBound) / 2;
x = 1:numel(metric);
errorbar(ax, x, center, center - lowerBound, upperBound - center, "o", ...
    "Color", palette.red, "MarkerFaceColor", palette.orange, ...
    "MarkerEdgeColor", palette.ink, "LineWidth", 1.8, "CapSize", 9);
xticks(ax, x);
xticklabels(ax, metric);
xlim(ax, [0.5, numel(metric) + 0.5]);
ylabel(ax, "区间");
end

function draw_custom_box(ax, xPosition, values, color, palette, boxWidth)
if nargin < 6
    boxWidth = 0.24;
end
values = values(isfinite(values));
q1 = percentile(values, 25);
medianValue = percentile(values, 50);
q3 = percentile(values, 75);
iqrValue = q3 - q1;
lowerWhisker = max(min(values), q1 - 1.5 * iqrValue);
upperWhisker = min(max(values), q3 + 1.5 * iqrValue);
patch(ax, xPosition + [-boxWidth, boxWidth, boxWidth, -boxWidth], ...
    [q1, q1, q3, q3], color, "FaceAlpha", 0.20, ...
    "EdgeColor", color, "LineWidth", 1.3);
plot(ax, [xPosition - boxWidth, xPosition + boxWidth], ...
    [medianValue, medianValue], "-", "Color", palette.ink, "LineWidth", 2.0);
plot(ax, [xPosition, xPosition], [lowerWhisker, q1], "-", "Color", palette.ink, "LineWidth", 1.1);
plot(ax, [xPosition, xPosition], [q3, upperWhisker], "-", "Color", palette.ink, "LineWidth", 1.1);
plot(ax, xPosition + [-0.10, 0.10], [lowerWhisker, lowerWhisker], "-", "Color", palette.ink, "LineWidth", 1.1);
plot(ax, xPosition + [-0.10, 0.10], [upperWhisker, upperWhisker], "-", "Color", palette.ink, "LineWidth", 1.1);
end

function add_panel_label(ax, labelText, palette)
text(ax, -0.10, 1.04, string(labelText), "Units", "normalized", ...
    "FontSize", 21, "FontWeight", "bold", "Color", palette.ink, ...
    "HorizontalAlignment", "left", "VerticalAlignment", "bottom");
end

%% ======================== 本地数据、样式与数学辅助 ========================
function entry = register_figure(id, fig, fileBase)
entry = struct("id", string(id), "handle", fig, "fileBase", string(fileBase));
end

function fig = create_figure(name, position)
fig = figure("Color", "w", "Position", position, ...
    "Name", string(name), "NumberTitle", "off", "Visible", "on");
end

function books = locate_result_workbooks(projectRoot, problemName)
resultDir = fullfile(projectRoot, "结果数据表", problemName, problemName + "结果数据");
books.solution = fullfile(resultDir, problemName + "求解结果.xlsx");
books.robustness = fullfile(resultDir, problemName + "敏感性与鲁棒性结果.xlsx");
assert(isfile(books.solution), "缺少求解结果工作簿: %s", books.solution);
assert(isfile(books.robustness), "缺少敏感性与鲁棒性工作簿: %s", books.robustness);
end

function projectRoot = find_project_root(startDir)
current = string(startDir);
while true
    hasData = isfolder(fullfile(current, "结果数据表"));
    hasMatlab = isfolder(fullfile(current, "MATLAB绘图"));
    if hasData && hasMatlab
        projectRoot = current;
        return;
    end
    parent = string(fileparts(current));
    if parent == current || strlength(parent) == 0
        error("无法定位项目根目录；应同时包含“结果数据表”和“MATLAB绘图”目录。");
    end
    current = parent;
end
end

function tf = has_sheet(workbook, sheetName)
try
    tf = any(string(sheetnames(workbook)) == string(sheetName));
catch errorInfo
    error("无法读取工作簿工作表: %s\n%s", workbook, errorInfo.message);
end
end

function data = read_required_table(workbook, sheetName, requiredColumns)
data = readtable(workbook, "Sheet", sheetName, "VariableNamingRule", "preserve");
assert(height(data) > 0, "工作表为空: %s / %s", workbook, sheetName);
missing = setdiff(string(requiredColumns), string(data.Properties.VariableNames));
assert(isempty(missing), "工作表 %s 缺少字段: %s", sheetName, strjoin(missing, ", "));
end

function tf = has_columns(data, requiredColumns)
tf = all(ismember(string(requiredColumns), string(data.Properties.VariableNames)));
end

function tf = is_feasible(value)
tf = any(strcmpi(string(value), ["是", "true", "可行", "1"]));
end

function n = minimum_group_size(group)
[~, index] = stable_group_index(group);
counts = accumarray(index, 1);
n = min(counts);
end

function [levels, index] = stable_group_index(group)
levels = unique(string(group), "stable");
index = zeros(numel(group), 1);
for i = 1:numel(levels)
    index(string(group) == levels(i)) = i;
end
end

function offsets = deterministic_jitter(n, width)
if n <= 1
    offsets = zeros(n, 1);
    return;
end
idx = (1:n)';
raw = sin(idx * 12.9898) * 43758.5453;
raw = raw - floor(raw);
offsets = (raw - 0.5) * 2 * width;
end

function value = percentile(values, p)
values = sort(values(isfinite(values)));
assert(~isempty(values), "无法对空数据计算分位数。");
position = 1 + (numel(values) - 1) * p / 100;
lowerIndex = floor(position);
upperIndex = ceil(position);
if lowerIndex == upperIndex
    value = values(lowerIndex);
else
    weight = position - lowerIndex;
    value = values(lowerIndex) * (1 - weight) + values(upperIndex) * weight;
end
end

function [gridValues, density] = gaussian_kde(values, gridCount)
values = values(isfinite(values));
assert(numel(values) >= 2, "KDE 至少需要两个有效样本。");
rangeValue = max(values) - min(values);
scaleValue = std(values);
if scaleValue <= eps
    scaleValue = max(abs(mean(values)), 1) * 1e-3;
end
bandwidth = 1.06 * scaleValue * numel(values) ^ (-1 / 5);
bandwidth = max(bandwidth, scaleValue * 0.08);
padding = max(rangeValue * 0.12, bandwidth * 2);
gridValues = linspace(min(values) - padding, max(values) + padding, gridCount)';
z = (gridValues - values(:)') / bandwidth;
density = mean(exp(-0.5 * z .^ 2), 2) / (bandwidth * sqrt(2 * pi));
end

function colors = role_colors(palette)
colors = [palette.navy; palette.teal; palette.purple; palette.red; palette.orange; palette.gold];
end

function palette = high_contrast_palette()
palette.navy = [18, 59, 93] / 255;
palette.teal = [0, 158, 145] / 255;
palette.purple = [107, 79, 163] / 255;
palette.red = [198, 61, 61] / 255;
palette.orange = [224, 122, 36] / 255;
palette.gold = [211, 160, 0] / 255;
palette.ink = [24, 28, 34] / 255;
palette.gray = [139, 146, 154] / 255;
palette.lightGray = [229, 231, 233] / 255;
palette.beige = [232, 215, 191] / 255;
palette.sequential = [18, 59, 93; 0, 158, 145; 231, 210, 111; 224, 122, 36; 198, 61, 61] / 255;
end

function apply_scientific_style(fig, palette)
fontName = select_font();
set(fig, "Color", "w");
axesList = findall(fig, "Type", "axes");
for ax = reshape(axesList, 1, [])
    set(ax, "FontName", fontName, "FontSize", 17, ...
        "LineWidth", 1.35, "Box", "off", "Layer", "top", ...
        "TickDir", "out", "TickLength", [0.012, 0.012], ...
        "XColor", palette.ink);
    if numel(ax.YAxis) == 1
        ax.YColor = palette.ink;
    end
    ax.XLabel.FontSize = 18;
    ax.YLabel.FontSize = 18;
    grid(ax, "off");
end
legendList = findall(fig, "Type", "legend");
for lgd = reshape(legendList, 1, [])
    set(lgd, "FontName", fontName, "FontSize", 15.5, "Box", "off");
end
colorbarList = findall(fig, "Type", "colorbar");
for cb = reshape(colorbarList, 1, [])
    set(cb, "FontName", fontName, "FontSize", 15.5, "LineWidth", 1.1);
end
textList = findall(fig, "Type", "text");
for txt = reshape(textList, 1, [])
    if isprop(txt, "FontName")
        set(txt, "FontName", fontName);
    end
end
end

function fontName = select_font()
preferred = ["Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", ...
    "Source Han Sans SC", "SimHei", "Arial Unicode MS", "Helvetica", "Arial"];
available = string(listfonts);
fontName = "Helvetica";
for candidate = preferred
    if any(strcmpi(available, candidate))
        fontName = candidate;
        return;
    end
end
end

function export_figure(fig, outputBase, formats)
outDir = fileparts(outputBase);
if strlength(outDir) > 0 && ~isfolder(outDir)
    mkdir(outDir);
end
for fmt = formats
    switch lower(fmt)
        case "pdf"
            exportgraphics(fig, outputBase + ".pdf", "ContentType", "vector");
        case "png"
            exportgraphics(fig, outputBase + ".png", "Resolution", 600);
        case "svg"
            exportgraphics(fig, outputBase + ".svg", "ContentType", "vector");
        otherwise
            error("不支持的导出格式: %s", fmt);
    end
end
end
