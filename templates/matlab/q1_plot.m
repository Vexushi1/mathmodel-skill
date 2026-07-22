%% q1_plot：问题一结果绘图入口
% 本文件应放在“结果数据表/问题一/”中，与两份问题一工作簿同目录。
% MATLAB 只读取工作簿绘图，不重新计算核心结果。

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

%% 2. Figure Contract 对应的数据读取
% 按实际图表合同替换工作表和字段。中文字段必须保留原名。
requiredSheet = "明细结果";
requiredColumns = ["记录键", "横轴字段", "纵轴字段"];
data = read_and_check(solutionBook, requiredSheet, requiredColumns);

% 时间、类别、名次或坐标必须显式排序，不依赖 Excel 原始顺序。
% data = sortrows(data, "横轴字段");

%% 3. 正式结果图
% 图型依据 Core conclusion、底层数据和信息效率选择；高级图表不得制造遮挡或比例失真。
fig = figure("Color", "w", "Position", [100, 100, 900, 620]);
ax = axes(fig);
hold(ax, "on");

% 示例：替换为本题真实字段后启用。
% plot(ax, data.("横轴字段"), data.("纵轴字段"), ...
%     "LineWidth", 2.2, "Color", [23, 59, 94] / 255);

xlabel(ax, "横轴名称（单位）");
ylabel(ax, "纵轴名称（单位）");
grid(ax, "off");
box(ax, "on");
hold(ax, "off");

apply_scientific_style(fig);

%% 4. 人工调整后可选导出
% 默认不自动导出、不关闭图窗。确认尺寸、图例、标签和视角后再设为 true。
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
function T = read_and_check(workbookPath, sheetName, requiredColumns)
availableSheets = string(sheetnames(workbookPath));
assert(any(availableSheets == sheetName), ...
    "工作簿“%s”缺少工作表“%s”", workbookPath, sheetName);

opts = detectImportOptions(workbookPath, "Sheet", sheetName, ...
    "VariableNamingRule", "preserve");
T = readtable(workbookPath, opts, "Sheet", sheetName, ...
    "VariableNamingRule", "preserve");

assert(height(T) >= 1, "工作表“%s”没有真实数据", sheetName);
actualColumns = string(T.Properties.VariableNames);
missingColumns = requiredColumns(~ismember(requiredColumns, actualColumns));
assert(isempty(missingColumns), "工作表“%s”缺少字段: %s", ...
    sheetName, strjoin(missingColumns, "、"));

if any(actualColumns == "记录键")
    key = string(T.("记录键"));
    assert(all(strlength(strtrim(key)) > 0), "记录键存在空值");
    assert(numel(unique(key)) == numel(key), "记录键存在重复值");
end

numericMask = varfun(@isnumeric, T, "OutputFormat", "uniform");
numericNames = actualColumns(numericMask);
for i = 1:numel(numericNames)
    values = T.(numericNames(i));
    assert(all(isfinite(values) | ismissing(values)), ...
        "数值字段“%s”包含 Inf 或非法值", numericNames(i));
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
