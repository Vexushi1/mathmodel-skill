function books = hsk_read_result_workbooks(location, problemName, requirements)
% 读取同一问题目录中的主求解与结果深化分析工作簿。
% 新项目目录为“问题X求解/”；旧“结果数据表/问题X/”只读兼容。

arguments
    location (1,1) string
    problemName (1,1) string = ""
    requirements (1,1) struct = struct()
end

if strlength(problemName) == 0
    resultDir = location;
    folderName = string(get_last_folder(resultDir));
    assert(endsWith(folderName, "求解"), ...
        "直接传入结果目录时，目录名应为问题一求解、问题二求解等");
    problemName = extractBefore(folderName, strlength(folderName) - 1);
else
    resultDir = fullfile(location, problemName + "求解");
    if ~isfolder(resultDir)
        legacyDir = fullfile(location, "结果数据表", problemName);
        assert(isfolder(legacyDir), "缺少问题求解目录: %s", resultDir);
        resultDir = legacyDir;
        warning("使用旧结果数据表目录，仅作只读兼容");
    end
end

books.resultDir = resultDir;
books.solution = fullfile(resultDir, problemName + "求解结果.xlsx");
books.analysis = fullfile(resultDir, problemName + "结果深化分析.xlsx");
legacyAnalysis = fullfile(resultDir, problemName + "敏感性与鲁棒性结果.xlsx");
if ~isfile(books.analysis) && isfile(legacyAnalysis)
    books.analysis = legacyAnalysis;
    warning("使用旧工作簿名，仅作只读兼容");
end
books.matlabScript = fullfile(resultDir, "q" + question_number(problemName) + "_plot.m");

assert(isfile(books.solution), "缺少求解结果工作簿: %s", books.solution);
assert(isfile(books.analysis), "缺少结果深化分析工作簿: %s", books.analysis);

books.solutionSheets = string(sheetnames(books.solution));
books.analysisSheets = string(sheetnames(books.analysis));

if isfield(requirements, "solution")
    validate_exact_requirements(books.solution, requirements.solution);
end
if isfield(requirements, "analysis")
    validate_exact_requirements(books.analysis, requirements.analysis);
elseif isfield(requirements, "robustness")
    validate_exact_requirements(books.analysis, requirements.robustness);
end
end

function validate_exact_requirements(workbookPath, sheetRequirements)
assert(isstruct(sheetRequirements), "工作表校验要求必须为 struct");
availableSheets = string(sheetnames(workbookPath));
sheetNames = string(fieldnames(sheetRequirements));

for i = 1:numel(sheetNames)
    sheetName = sheetNames(i);
    assert(any(availableSheets == sheetName), "工作簿缺少工作表“%s”", sheetName);
    spec = sheetRequirements.(sheetName);
    assert(isstruct(spec) && isfield(spec, "headers") && isfield(spec, "columns"), ...
        "工作表“%s”必须提供 headers 和 columns", sheetName);

    expectedHeaders = string(spec.headers);
    fixedColumns = double(spec.columns);
    assert(numel(expectedHeaders) == numel(fixedColumns), "headers 与 columns 数量不一致");
    assert(all(isfinite(fixedColumns)) && all(fixedColumns >= 1) && ...
        all(fixedColumns == floor(fixedColumns)), "固定列号必须为正整数");

    raw = readcell(workbookPath, "Sheet", sheetName);
    assert(size(raw, 1) >= 2, "工作表“%s”没有真实数据", sheetName);
    assert(size(raw, 2) >= max(fixedColumns), "工作表“%s”的列数少于已锁定列位置", sheetName);

    for j = 1:numel(fixedColumns)
        columnIndex = fixedColumns(j);
        actualHeader = strtrim(string(raw{1, columnIndex}));
        assert(actualHeader == expectedHeaders(j), ...
            "工作表“%s”第%d列表头应为“%s”，实际为“%s”", ...
            sheetName, columnIndex, expectedHeaders(j), actualHeader);
    end

    if isfield(spec, "key_column")
        keyColumn = double(spec.key_column);
        assert(keyColumn >= 1 && keyColumn <= size(raw, 2), "key_column 越界");
        key = cell_to_string(raw(2:end, keyColumn));
        assert(all(strlength(strtrim(key)) > 0), "记录键存在空值");
        assert(numel(unique(key)) == numel(key), "记录键存在重复值");
    end

    if isfield(spec, "numeric_columns")
        for columnIndex = double(spec.numeric_columns)
            assert(columnIndex >= 1 && columnIndex <= size(raw, 2), "数值列号越界");
            values = cell_to_numeric(raw(2:end, columnIndex));
            assert(all(isfinite(values) | isnan(values)), "数值列包含 Inf 或非法值");
        end
    end
end
end

function values = cell_to_string(column)
values = strings(size(column, 1), 1);
for i = 1:size(column, 1)
    if isempty(column{i})
        values(i) = "";
    else
        values(i) = strtrim(string(column{i}));
    end
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
        if isfinite(parsed)
            values(i) = parsed;
        end
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
