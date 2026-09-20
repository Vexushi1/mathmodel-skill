function books = hsk_read_result_workbooks(location, problemName, requirements)
% 只检查当前图声明使用的工作簿；空 requirements 仅检查主工作簿。
% 验收状态由上游工作流核对，本 helper 不因文件存在而宣称结果已验收。
% 新项目目录为“问题X求解/”；旧目录、robustness 与列号声明只读兼容。

arguments
    location (1,1) string
    problemName (1,1) string = ""
    requirements (1,1) struct = struct()
end

requestedBooks = string(fieldnames(requirements));
assert(all(ismember(requestedBooks, ["solution", "analysis", "robustness"])), ...
    "requirements 只允许 solution、analysis 或历史 robustness");
assert(~(isfield(requirements, "analysis") && isfield(requirements, "robustness")), ...
    "analysis 与 robustness 不能同时声明，请明确唯一分析来源");
if isempty(requestedBooks), requirements.solution = struct(); end

if strlength(problemName) == 0
    resultDir = location;
    [~, folderName] = fileparts(char(resultDir));
    folderName = string(folderName);
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
books.matlabScript = fullfile(resultDir, "q" + question_number(problemName) + "_plot.m");
books.solutionSheets = strings(0, 1);
books.analysisSheets = strings(0, 1);

if isfield(requirements, "solution")
    books.solutionSheets = validate_exact_requirements(books.solution, requirements.solution);
end
if isfield(requirements, "analysis") || isfield(requirements, "robustness")
    legacyAnalysis = fullfile(resultDir, problemName + "敏感性与鲁棒性结果.xlsx");
    if ~isfile(books.analysis) && isfile(legacyAnalysis)
        books.analysis = legacyAnalysis;
        warning("使用旧工作簿名，仅作只读兼容: %s", books.analysis);
    end
    if isfield(requirements, "analysis")
        analysisRequirements = requirements.analysis;
    else
        analysisRequirements = requirements.robustness;
        warning("requirements.robustness 仅作只读兼容；新声明使用 analysis");
    end
    books.analysisSheets = validate_exact_requirements(books.analysis, analysisRequirements);
end
end

function availableSheets = validate_exact_requirements(workbookPath, sheetRequirements)
assert(isstruct(sheetRequirements) && isscalar(sheetRequirements), ...
    "工作簿%s的工作表要求必须为标量 struct", workbookPath);
assert(isfile(workbookPath), "当前图声明的工作簿不存在: %s", workbookPath);
availableSheets = string(sheetnames(workbookPath));
for sheetName = reshape(string(fieldnames(sheetRequirements)), 1, [])
    context = sprintf("工作簿%s，工作表%s", workbookPath, sheetName);
    assert(any(availableSheets == sheetName), "%s：缺少工作表", context);
    spec = normalize_spec(sheetRequirements.(sheetName), context);
    raw = readcell(workbookPath, "Sheet", sheetName);
    assert(size(raw, 1) >= 2, "%s：没有读入数据行", context);
    % 不裁尾、不删行；missing/NaN 无法证明原 Excel 单元格是物理空白。
    actualHeaders = strtrim(string(raw(1, :)));
    actualColumns = zeros(size(spec.headers));
    for j = 1:numel(spec.headers)
        actualColumns(j) = exact_header_column(actualHeaders, spec.headers(j), context);
        expected = spec.expected_columns(j);
        if isfinite(expected) && expected ~= actualColumns(j)
            warning("%s，字段%s：期望第%d列，实际第%d列；已按精确表头读取", ...
                context, spec.headers(j), expected, actualColumns(j));
        end
    end
    if strlength(spec.key_header) > 0
        column = exact_header_column(actualHeaders, spec.key_header, context);
        validate_keys(raw(2:end, column), spec.key_header, context);
    end
    for header = reshape(spec.numeric_headers, 1, [])
        column = exact_header_column(actualHeaders, header, context);
        allowMissing = any(spec.allow_missing_headers == header);
        for row = 2:size(raw, 1)
            validate_numeric(raw{row, column}, allowMissing, spec.missing_tokens, ...
                sprintf("%s，字段%s，读入行%d", context, header, row));
        end
    end
end
end

function spec = normalize_spec(input, context)
allowed = ["headers", "expected_columns", "key_header", "numeric_headers", ...
    "allow_missing_headers", "missing_tokens", "columns", "key_column", "numeric_columns"];
assert(isstruct(input) && isscalar(input) && isfield(input, "headers"), ...
    "%s：每个工作表必须提供带 headers 的标量 struct", context);
assert(all(ismember(string(fieldnames(input)), allowed)), "%s：存在未知工作表配置字段", context);
spec.headers = text_list(input.headers, "headers", context);
assert(~isempty(spec.headers), "%s：headers 不能为空", context);
spec.expected_columns = nan(size(spec.headers));
if isfield(input, "expected_columns")
    spec.expected_columns = position_list(input.expected_columns, true, "expected_columns", context);
    assert(numel(spec.expected_columns) == numel(spec.headers), ...
        "%s：expected_columns 与 headers 数量不一致", context);
end
legacyColumns = [];
if isfield(input, "columns")
    legacyColumns = position_list(input.columns, false, "columns", context);
    assert(numel(legacyColumns) == numel(spec.headers), "%s：columns 与 headers 数量不一致", context);
    if isfield(input, "expected_columns")
        assert(isequaln(spec.expected_columns, legacyColumns), ...
            "%s：columns 与 expected_columns 声明不一致", context);
    end
    spec.expected_columns = legacyColumns;
end
spec.key_header = "";
spec.numeric_headers = strings(0, 1);
for name = ["key_header", "numeric_headers", "allow_missing_headers", "missing_tokens"]
    if isfield(input, name)
        spec.(name) = text_list(input.(name), name, context);
    elseif name ~= "key_header"
        spec.(name) = strings(0, 1);
    end
end
parsedTokens = str2double(spec.missing_tokens);
assert(isreal(parsedTokens) && all(isnan(parsedTokens)), ...
    "%s：missing_tokens 不能把有限数、Inf 或复数声明为缺测", context);
aliases = ["key_column", "key_header"; "numeric_columns", "numeric_headers"];
for k = 1:size(aliases, 1)
    oldName = aliases(k, 1); newName = aliases(k, 2);
    if ~isfield(input, oldName), continue; end
    indices = position_list(input.(oldName), false, oldName, context);
    mapped = strings(size(indices));
    for j = 1:numel(indices)
        match = find(legacyColumns == indices(j));
        assert(numel(match) == 1, ...
            "%s：旧%s中的第%d列没有唯一 columns→headers 映射，请改用%s", ...
            context, oldName, indices(j), newName);
        mapped(j) = spec.headers(match);
    end
    if isfield(input, newName)
        assert(isequal(sort(spec.(newName)), sort(mapped)), ...
            "%s：%s 与 %s 声明不一致", context, oldName, newName);
    end
    spec.(newName) = mapped;
end
assert(isscalar(spec.key_header), "%s：key_header 必须是一个精确表头；不使用时省略或设为空字符串", context);
assert(strlength(spec.key_header) == 0 || any(spec.headers == spec.key_header), ...
    "%s：key_header 必须属于 headers", context);
assert(all(ismember(spec.numeric_headers, spec.headers)), "%s：numeric_headers 必须是 headers 子集", context);
assert(all(ismember(spec.allow_missing_headers, spec.numeric_headers)), ...
    "%s：allow_missing_headers 必须是 numeric_headers 子集", context);
assert(~any(spec.allow_missing_headers == spec.key_header), "%s：记录键不能声明为允许缺测", context);
end

function values = text_list(input, name, context)
assert(isstring(input) || ischar(input) || iscellstr(input), ...
    "%s：%s 必须为文本或文本向量", context, name);
values = string(input);
assert(isvector(values) || isempty(values), "%s：%s 必须为向量", context, name);
values = strtrim(values(:));
assert(all(~ismissing(values) & (strlength(values) > 0 | name == "key_header")), ...
    "%s：%s 不能包含空白或缺测文本", context, name);
assert(numel(unique(values)) == numel(values), "%s：%s 包含重复值", context, name);
end

function values = position_list(input, allowNaN, name, context)
assert(isnumeric(input) && isreal(input) && (isvector(input) || isempty(input)), ...
    "%s：%s 必须为数值向量", context, name);
values = double(input(:));
valid = isfinite(values) & values >= 1 & values == floor(values);
assert(all(valid | (allowNaN & isnan(values))), ...
    "%s：%s 只允许正整数；仅 expected_columns 可用 NaN 跳过位置检查", context, name);
finiteValues = values(isfinite(values));
assert(numel(unique(finiteValues)) == numel(finiteValues), "%s：%s 包含重复列号", context, name);
end

function column = exact_header_column(headers, expected, context)
matches = find(headers == expected);
assert(numel(matches) == 1, "%s：字段%s缺失或重复", context, expected);
column = matches(1);
end

function validate_keys(column, header, context)
keys = strings(size(column));
for j = 1:numel(column)
    item = column{j};
    location = sprintf("%s，字段%s，读入行%d", context, header, j + 1);
    assert(~is_import_missing(item), "%s：记录键为空或缺测", location);
    if (isnumeric(item) || islogical(item)) && isscalar(item) && isreal(item) && isfinite(item)
        if isinteger(item)
            keys(j) = string(item);
        elseif item == 0
            keys(j) = "0";
        else
            keys(j) = string(sprintf("%.17g", double(item)));
        end
    elseif (ischar(item) && isrow(item)) || (isstring(item) && isscalar(item))
        keys(j) = strtrim(string(item));
    else
        error("%s：记录键必须为有限实数标量或文本", location);
    end
    assert(strlength(keys(j)) > 0, "%s：记录键为空白", location);
end
[~, first] = unique(keys, "stable");
duplicate = find(~ismember((1:numel(keys))', first), 1);
assert(isempty(duplicate), "%s，字段%s：读入行%s的记录键重复", ...
    context, header, mat2str(duplicate + 1));
end

function validate_numeric(item, allowMissing, missingTokens, context)
missingValue = is_import_missing(item);
if (ischar(item) && (isrow(item) || isempty(item))) || (isstring(item) && isscalar(item))
    text = strtrim(string(item));
    if ~ismissing(text)
        missingValue = strlength(text) == 0 || any(text == missingTokens);
        if ~missingValue
            value = str2double(text);
            assert(isreal(value) && isfinite(value), "%s：非空文本不是有限实数", context);
        end
    end
elseif ~missingValue
    assert((isnumeric(item) || islogical(item)) && isscalar(item) && isreal(item) && isfinite(item), ...
        "%s：数值必须是有限实数，不能为 Inf、复数或非标量", context);
end
assert(~missingValue || allowMissing, "%s：合同未允许该字段缺测", context);
end

function result = is_import_missing(item)
% 只识别导入表示，不声称其原始 Excel 单元格物理为空，不据此删行。
result = isempty(item) || (isa(item, "missing") && isscalar(item)) || ...
    (isstring(item) && isscalar(item) && ismissing(item)) || ...
    (isnumeric(item) && isscalar(item) && isreal(item) && isnan(item));
end

function number = question_number(problemName)
mapping = containers.Map( ...
    ["问题一", "问题二", "问题三", "问题四", "问题五", ...
     "问题六", "问题七", "问题八", "问题九", "问题十"], ...
    ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]);
assert(isKey(mapping, problemName), "无法识别问题编号: %s", problemName);
number = mapping(problemName);
end
