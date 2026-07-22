function figureRegistry = QX_plot()
% QX_plot 单问题全图绘制入口模板。
% 实例化时必须同时替换文件名、函数名、problemIndex 和 problemName：
%   问题一 -> Q1_plot.m / function Q1_plot()
%   问题二 -> Q2_plot.m / function Q2_plot()
%
% 一次运行生成该问题全部需要的结果图、诊断图、敏感性图和鲁棒性图。
% 本文件只读取 Python 输出的两类标准工作簿，不重新计算核心结果。
% 所有辅助逻辑均为文件末尾本地函数，项目交付不得再生成其他辅助 .m 文件。

%% 1. 问题配置：实例化时必须修改
problemIndex = 1;
problemName = "问题一";
exportFigures = false;          % 默认只保留可见图窗，人工确认后再改为 true
exportFormats = ["pdf", "png"];

scriptDir = string(fileparts(mfilename("fullpath")));
projectRoot = find_project_root(scriptDir);
books = locate_result_workbooks(projectRoot, problemName);

palette = scientific_palette();
figureRegistry = struct("id", {}, "handle", {}, "fileBase", {});

%% 2. 核心结果图：按实际工作表和字段替换
if has_sheet(books.solution, "明细结果")
    data = read_required_table(books.solution, "明细结果", ...
        ["横轴字段", "纵轴字段"]);
    fig = plot_core_result(data, palette);
    figureRegistry(end + 1) = register_figure( ...
        "core_result", fig, "q" + problemIndex + "_core_result"); %#ok<AGROW>
end

%% 3. 多算法或方案比较图：不适用时删除本节
if has_sheet(books.solution, "多算法对比")
    data = read_required_table(books.solution, "多算法对比", ...
        ["算法", "目标值", "可行性"]);
    fig = plot_algorithm_comparison(data, palette);
    figureRegistry(end + 1) = register_figure( ...
        "algorithm_comparison", fig, "q" + problemIndex + "_algorithm_comparison"); %#ok<AGROW>
end

%% 4. 参数敏感性图：不适用时由工作簿“适用性说明”证明
if has_sheet(books.robustness, "参数敏感性")
    data = read_required_table(books.robustness, "参数敏感性", ...
        ["参数", "扰动值", "目标指标"]);
    fig = plot_sensitivity(data, palette);
    figureRegistry(end + 1) = register_figure( ...
        "sensitivity", fig, "q" + problemIndex + "_sensitivity"); %#ok<AGROW>
end

%% 5. 鲁棒性区间图：按实际指标筛选或拆分
if has_sheet(books.robustness, "鲁棒性区间")
    data = read_required_table(books.robustness, "鲁棒性区间", ...
        ["指标", "下界", "上界"]);
    fig = plot_robustness_interval(data, palette);
    figureRegistry(end + 1) = register_figure( ...
        "robustness", fig, "q" + problemIndex + "_robustness"); %#ok<AGROW>
end

%% 6. 统一样式与可选导出
if isempty(figureRegistry)
    error("未生成任何图。请核对工作表、字段和本问题的绘图函数。");
end

for k = 1:numel(figureRegistry)
    apply_scientific_style(figureRegistry(k).handle);
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
% 将占位字段替换为该问题工作簿中的真实列名。
x = data.("横轴字段");
y = data.("纵轴字段");
fig = figure("Color", "w", "Position", [100, 100, 920, 620], ...
    "Name", "核心结果", "NumberTitle", "off");
ax = axes(fig);
plot(ax, x, y, "-o", "Color", palette.deepBlue, ...
    "LineWidth", 2.2, "MarkerSize", 6, ...
    "MarkerFaceColor", "w", "MarkerEdgeColor", palette.deepBlue);
xlabel(ax, "横轴名称（单位）");
ylabel(ax, "纵轴名称（单位）");
end

function fig = plot_algorithm_comparison(data, palette)
algorithm = categorical(string(data.("算法")));
value = data.("目标值");
feasible = string(data.("可行性"));
fig = figure("Color", "w", "Position", [130, 120, 920, 620], ...
    "Name", "多算法对比", "NumberTitle", "off");
ax = axes(fig);
barHandle = bar(ax, algorithm, value, 0.62, ...
    "FaceColor", palette.teal, "EdgeColor", palette.darkGray, "LineWidth", 1.0);
barHandle.FaceAlpha = 0.92;
ylabel(ax, "目标值（单位）");
for i = 1:numel(value)
    if ~any(strcmpi(feasible(i), ["是", "true", "可行", "1"]))
        text(ax, i, value(i), "不可行", "HorizontalAlignment", "center", ...
            "VerticalAlignment", "bottom", "FontWeight", "bold", ...
            "Color", palette.darkRed);
    end
end
end

function fig = plot_sensitivity(data, palette)
parameter = string(data.("参数"));
perturbation = data.("扰动值");
response = data.("目标指标");
parameterLevels = unique(parameter, "stable");
colors = [palette.deepBlue; palette.teal; palette.purple; palette.darkRed];
fig = figure("Color", "w", "Position", [160, 140, 960, 640], ...
    "Name", "参数敏感性", "NumberTitle", "off");
ax = axes(fig);
hold(ax, "on");
for i = 1:numel(parameterLevels)
    idx = parameter == parameterLevels(i);
    [x, order] = sort(perturbation(idx));
    y = response(idx);
    color = colors(mod(i - 1, size(colors, 1)) + 1, :);
    plot(ax, x, y(order), "-o", "LineWidth", 2.1, "MarkerSize", 5.5, ...
        "Color", color, "DisplayName", parameterLevels(i));
end
hold(ax, "off");
xlabel(ax, "参数扰动值（单位）");
ylabel(ax, "目标指标（单位）");
legend(ax, "Location", "best", "Box", "off");
end

function fig = plot_robustness_interval(data, palette)
metric = categorical(string(data.("指标")));
lowerBound = data.("下界");
upperBound = data.("上界");
center = (lowerBound + upperBound) / 2;
negativeError = center - lowerBound;
positiveError = upperBound - center;
fig = figure("Color", "w", "Position", [190, 160, 960, 640], ...
    "Name", "鲁棒性区间", "NumberTitle", "off");
ax = axes(fig);
errorbar(ax, metric, center, negativeError, positiveError, "o", ...
    "Color", palette.darkRed, "MarkerFaceColor", "w", ...
    "MarkerSize", 7, "LineWidth", 1.8, "CapSize", 10);
ylabel(ax, "指标区间（单位）");
end

%% ======================== 本地数据与样式函数 ========================
function entry = register_figure(id, fig, fileBase)
entry = struct("id", string(id), "handle", fig, "fileBase", string(fileBase));
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

function palette = scientific_palette()
palette.deepBlue = [23, 59, 94] / 255;
palette.midBlue = [55, 92, 135] / 255;
palette.teal = [30, 117, 107] / 255;
palette.darkRed = [154, 56, 56] / 255;
palette.purple = [93, 75, 134] / 255;
palette.beige = [169, 143, 112] / 255;
palette.darkGray = [32, 38, 46] / 255;
palette.lightGray = [217, 218, 215] / 255;
end

function apply_scientific_style(fig)
fontName = select_font();
set(fig, "Color", "w");
axesList = findall(fig, "Type", "axes");
for ax = reshape(axesList, 1, [])
    set(ax, "FontName", fontName, "FontSize", 18, ...
        "LineWidth", 1.4, "Box", "on", "Layer", "top");
    grid(ax, "off");
end
legendList = findall(fig, "Type", "legend");
for lgd = reshape(legendList, 1, [])
    set(lgd, "FontName", fontName, "FontSize", 16, "Box", "off");
end
colorbarList = findall(fig, "Type", "colorbar");
for cb = reshape(colorbarList, 1, [])
    set(cb, "FontName", fontName, "FontSize", 16, "LineWidth", 1.2);
end
textList = findall(fig, "Type", "text");
for txt = reshape(textList, 1, [])
    if isprop(txt, "FontName")
        set(txt, "FontName", fontName);
    end
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
