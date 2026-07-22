function books = hsk_read_result_workbooks(projectRoot, problemName, requirements)
% 返回每问两类标准结果工作簿及工作表名称，并按需校验工作表字段。
arguments
    projectRoot (1,1) string
    problemName (1,1) string
    requirements (1,1) struct = struct()
end

resultDir = fullfile(projectRoot, "结果数据表", problemName, problemName + "结果数据");
books.solution = fullfile(resultDir, problemName + "求解结果.xlsx");
books.robustness = fullfile(resultDir, problemName + "敏感性与鲁棒性结果.xlsx");

assert(isfile(books.solution), "缺少求解结果工作簿: %s", books.solution);
assert(isfile(books.robustness), "缺少敏感性与鲁棒性工作簿: %s", books.robustness);

books.solutionSheets = string(sheetnames(books.solution));
books.robustnessSheets = string(sheetnames(books.robustness));

if isfield(requirements, "solution")
    hsk_validate_requirements(books.solution, requirements.solution);
end
if isfield(requirements, "robustness")
    hsk_validate_requirements(books.robustness, requirements.robustness);
end
end

function hsk_validate_requirements(workbookPath, sheetRequirements)
% sheetRequirements 示例：
% requirements.solution.核心指标 = ["指标", "数值"];
% requirements.solution.明细结果 = ["记录键", "数值"];
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
        "工作表“%s”缺少字段: %s", sheetName, strjoin(missingColumns, ", "));

    if any(actualColumns == "记录键")
        key = string(T.("记录键"));
        assert(all(strlength(strtrim(key)) > 0), ...
            "工作表“%s”的记录键存在空值", sheetName);
        assert(numel(unique(key)) == numel(key), ...
            "工作表“%s”的记录键存在重复值", sheetName);
    end

    numericMask = varfun(@isnumeric, T, "OutputFormat", "uniform");
    numericNames = actualColumns(numericMask);
    for j = 1:numel(numericNames)
        values = T.(numericNames(j));
        assert(all(isfinite(values) | ismissing(values)), ...
            "工作表“%s”的数值字段“%s”包含 Inf 或非法值", ...
            sheetName, numericNames(j));
    end
end
end
