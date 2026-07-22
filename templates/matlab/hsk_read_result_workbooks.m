function books = hsk_read_result_workbooks(location, problemName, requirements)
% 兼容辅助函数。新项目优先直接传入“结果数据表/问题X/”目录。
% 简单绘图默认在 q{x}_plot.m 中自包含读取与校验，不强制依赖本函数。
arguments
    location (1,1) string
    problemName (1,1) string = ""
    requirements (1,1) struct = struct()
end

if strlength(problemName) == 0
    resultDir = location;
else
    flatDir = fullfile(location, "结果数据表", problemName);
    legacyDir = fullfile(flatDir, problemName + "结果数据");
    if isfolder(flatDir)
        resultDir = flatDir;
    elseif isfolder(legacyDir)
        resultDir = legacyDir;
    else
        resultDir = flatDir;
    end
end

if strlength(problemName) == 0
    folderName = string(get_last_folder(resultDir));
    assert(startsWith(folderName, "问题"), ...
        "直接传入结果目录时，目录名应为问题一、问题二等中文名称");
    problemName = folderName;
end

books.resultDir = resultDir;
books.solution = fullfile(resultDir, problemName + "求解结果.xlsx");
books.robustness = fullfile(resultDir, problemName + "敏感性与鲁棒性结果.xlsx");
books.matlabScript = fullfile(resultDir, "q" + question_number(problemName) + "_plot.m");
books.figureDir = fullfile(resultDir, "图表");

assert(isfile(books.solution), "缺少求解结果工作簿: %s", books.solution);
assert(isfile(books.robustness), "缺少敏感性与鲁棒性工作簿: %s", books.robustness);

books.solutionSheets = string(sheetnames(books.solution));
books.robustnessSheets = string(sheetnames(books.robustness));

if isfield(requirements, "solution")
    validate_requirements(books.solution, requirements.solution);
end
if isfield(requirements, "robustness")
    validate_requirements(books.robustness, requirements.robustness);
end
end

function validate_requirements(workbookPath, sheetRequirements)
assert(isstruct(sheetRequirements), "工作表校验要求必须为 struct");
availableSheets = string(sheetnames(workbookPath));
sheetNames = string(fieldnames(sheetRequirements));
for i = 1:numel(sheetNames)
    sheetName = sheetNames(i);
    assert(any(availableSheets == sheetName), ...
        "工作簿缺少工作表“%s”: %s", sheetName, workbookPath);

    requiredColumns = string(sheetRequirements.(sheetName));
    opts = detectImportOptions(workbookPath, "Sheet", sheetName, ...
        "VariableNamingRule", "preserve");
    T = readtable(workbookPath, opts, "Sheet", sheetName, ...
        "VariableNamingRule", "preserve");

    assert(height(T) >= 1, "工作表“%s”没有真实数据记录: %s", sheetName, workbookPath);
    actualColumns = string(T.Properties.VariableNames);
    missingColumns = requiredColumns(~ismember(requiredColumns, actualColumns));
    assert(isempty(missingColumns), ...
        "工作表“%s”缺少字段: %s", sheetName, strjoin(missingColumns, "、"));

    if any(actualColumns == "记录键")
        key = string(T.("记录键"));
        assert(all(strlength(strtrim(key)) > 0), "工作表“%s”的记录键存在空值", sheetName);
        assert(numel(unique(key)) == numel(key), "工作表“%s”的记录键存在重复值", sheetName);
    end

    numericMask = varfun(@isnumeric, T, "OutputFormat", "uniform");
    numericNames = actualColumns(numericMask);
    for j = 1:numel(numericNames)
        values = T.(numericNames(j));
        assert(all(isfinite(values) | ismissing(values)), ...
            "工作表“%s”的数值字段“%s”包含 Inf 或非法值", sheetName, numericNames(j));
    end
end
end

function name = get_last_folder(pathValue)
[~, name] = fileparts(char(pathValue));
end

function number = question_number(problemName)
mapping = containers.Map( ...
    ["问题一", "问题二", "问题三", "问题四", "问题五", ...
     "问题六", "问题七", "问题八", "问题九", "问题十"], ...
    ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]);
assert(isKey(mapping, problemName), "无法识别问题编号: %s", problemName);
number = mapping(problemName);
end
