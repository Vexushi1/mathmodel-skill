function workbook = q1_solver()
RUN_CONFIG = jsondecode('{"stage":"primary","problem_name":"问题一","solver_backend":"matlab","data_paths":["input.json"],"data_sha256":"__DATA_SHA256__","solver":"mldivide","random_seed":2026,"tolerance":1e-10,"iteration_or_time_limit":"direct","expected_workbook":"问题一求解/问题一求解结果.xlsx","run_receipt_protocol_version":"1.1.0","primary_quality_protocol_version":"1.0.0","code_dependencies":[]}');
% Instantiation example: solve a*x=b. Replace the model and its PQS together.
% This template does not authorize a project model or mark results accepted.
entrypoint = string(mfilename('fullpath')) + ".m";
root = string(fileparts(fileparts(entrypoint)));
assert(usejava('jvm'), 'HSK:Environment', 'SHA-256 requires the MATLAB JVM.');
assert(license('test', 'MATLAB'), 'HSK:Environment', 'MATLAB license is unavailable.');
identity = verify_inputs(root, entrypoint, RUN_CONFIG);
rng(RUN_CONFIG.random_seed, 'twister');
started = tic;
input = read_model_input(root, RUN_CONFIG);
validateattributes(input.coefficient, {'numeric'}, {'real','finite','scalar','nonzero'});
validateattributes(input.right_hand_side, {'numeric'}, {'real','finite','scalar'});
assert(strcmp(RUN_CONFIG.solver, 'mldivide') && strcmp(RUN_CONFIG.iteration_or_time_limit, 'direct'), ...
    'HSK:Solver', 'This instantiated direct solver does not support another solver or limit.');
solution = input.coefficient \ input.right_hand_side;
residual = abs(input.coefficient * solution - input.right_hand_side);
passed = isfinite(solution) && residual <= RUN_CONFIG.tolerance;
receipt = make_receipt(RUN_CONFIG, identity, toc(started), 'direct_solve_completed', 1);
receipt.primary_quality_protocol_version = RUN_CONFIG.primary_quality_protocol_version;
sheets = cell(0, 2);
sheets(end + 1, :) = {'运行配置',receipt_cells(receipt)};
sheets(end + 1, :) = {'核心指标',{'指标','数值'; '解',solution; '绝对方程残差',residual}};
sheets(end + 1, :) = {'数据审计',{'等级','检查项','信息','处理方式'; ...
    'info','有限输入与非零系数','全部已验证；未改变原始输入','只读检查'}};
sheets(end + 1, :) = {'主结果质量门',{'Verification ID','检查项','是否通过','证据','判定关系', ...
    '阈值或容差','实际值','证据工作表','阈值来源'; ...
    'PQ-Q1-01','方程残差',passed,'由原始系数与求解值重算','abs<=', ...
    RUN_CONFIG.tolerance,residual,'均衡残差','solver_tolerance'}};
sheets(end + 1, :) = {'均衡残差',{'主体或均衡','残差','容差','是否满足'; ...
    'a*x=b',residual,RUN_CONFIG.tolerance,passed}};
sheets(end + 1, :) = {'状态明细',{'记录键','状态','数值','单位'; '0001','解',solution,'无量纲'}};
current = verify_inputs(root, entrypoint, RUN_CONFIG);
assert(isequal(identity, current), 'HSK:IdentityChanged', 'Source or input changed during execution.');
workbook = project_path(root, RUN_CONFIG.expected_workbook);
write_workbook(workbook, sheets);
assert(passed, 'HSK:NumericalQuality', 'The written workbook records a failed numerical quality check.');
end

function identity = verify_inputs(root, entrypoint, config)
assert(strcmp(config.solver_backend, 'matlab'), 'HSK:Backend', 'Wrong execution backend.');
validateattributes(config.random_seed, {'numeric'}, {'scalar','integer','nonnegative','<=',2^32-1});
validateattributes(config.tolerance, {'numeric'}, {'scalar','real','finite','positive'});
inputs = string(config.data_paths(:));
assert(~isempty(inputs), 'HSK:Input', 'Declare at least one actual input.');
identity.data_sha256 = input_digest(root, inputs, config);
assert(strcmp(identity.data_sha256, config.data_sha256), 'HSK:InputHash', 'Input hash does not match RUN_CONFIG.');
entryRelative = replace(extractAfter(entrypoint, strlength(root) + 1), '\', '/');
sources = strings(numel(config.code_dependencies) + 1, 1);
sources(1) = entryRelative;
if ~isempty(config.code_dependencies)
    assert(isstruct(config.code_dependencies), 'HSK:Dependencies', 'Dependencies must be path/hash records.');
    for k = 1:numel(config.code_dependencies)
        dep = config.code_dependencies(k);
        path = project_path(root, dep.path);
        assert(strcmp(file_digest(path), dep.sha256), 'HSK:Dependencies', 'Dependency hash mismatch.');
        [~, name, extension] = fileparts(path);
        if extension == ".m"
            actual = string(which(name));
            assert(actual ~= "" && string(java.io.File(char(actual)).getCanonicalPath()) == path, ...
                'HSK:DependencyShadow', 'A MATLAB dependency resolves to an undeclared file.');
        end
        sources(k + 1) = string(dep.path);
    end
end
identity.code_sha256 = file_digest(entrypoint);
identity.code_bundle_sha256 = files_digest(root, sources);
end

function mode = data_identity_mode(config)
mode = "combined";
if isfield(config, 'data_identity_mode'), mode = string(config.data_identity_mode); end
assert(isscalar(mode) && any(mode == ["combined","preprocessing_workbook"]), ...
    'HSK:InputMode', 'Unsupported data identity mode.');
end

function hash = input_digest(root, inputs, config)
if data_identity_mode(config) == "preprocessing_workbook"
    assert(numel(inputs) == 1 && endsWith(lower(inputs(1)), '.xlsx'), ...
        'HSK:InputMode', 'Preprocessing identity requires exactly one accepted XLSX.');
    hash = file_digest(project_path(root, inputs(1)));
else
    hash = files_digest(root, inputs);
end
end

function input = read_model_input(root, config)
filename = project_path(root, config.data_paths{1});
if data_identity_mode(config) == "combined"
    input = jsondecode(fileread(filename));
    return
end
% Micro-example input contract; instantiate actual model fields explicitly.
raw = readcell(filename, 'Sheet', '模型输入');
assert(size(raw, 1) == 2, 'HSK:Input', 'The example requires one model-input record.');
headers = string(raw(1, :));
for field = ["coefficient","right_hand_side","sensitivity_coefficients"]
    column = find(headers == field);
    assert(isscalar(column), 'HSK:Headers', 'Model input header is missing or duplicated.');
    input.(field) = raw{2, column};
end
input.sensitivity_coefficients = jsondecode(char(string(input.sensitivity_coefficients)));
end

function path = project_path(root, relative)
relative = string(relative);
assert(isscalar(relative) && strlength(relative) > 0 && ~contains(relative, '\'), ...
    'HSK:Path', 'Use a nonempty project-relative POSIX path.');
parts = split(relative, '/');
assert(~any(parts == "" | parts == "." | parts == "..") && ...
    isempty(regexp(char(relative), '^[A-Za-z]:', 'once')), 'HSK:Path', 'Invalid relative path.');
root = string(java.io.File(char(root)).getCanonicalPath());
file = java.io.File(char(fullfile(root, relative)));
path = string(file.getCanonicalPath());
literal = string(file.getAbsolutePath());
assert(path == literal || (ispc && strcmpi(path,literal)), 'HSK:Path', 'Filesystem path aliases are not supported.');
assert(startsWith(path, root + filesep, 'IgnoreCase', ispc), 'HSK:Path', 'Path escapes the project.');
end

function result = file_digest(path)
[fid, message] = fopen(path, 'rb');
assert(fid >= 0, 'HSK:Read', 'Cannot read %s: %s', path, message);
cleanup = onCleanup(@() fclose(fid));
engine = java.security.MessageDigest.getInstance('SHA-256');
while ~feof(fid)
    engine.update(fread(fid, 1048576, '*uint8'));
end
result = digest_hex(engine);
end

function result = files_digest(root, paths)
paths = string(paths(:));
assert(numel(unique(lower(paths))) == numel(paths), 'HSK:Path', 'Duplicate or case-aliased paths.');
sortKeys = strings(size(paths));
for k = 1:numel(paths)
    sortKeys(k) = string(reshape(dec2hex(unicode2native(char(paths(k)), 'UTF-8'), 2).', 1, []));
end
[~, order] = sort(sortKeys); % Fixed-width UTF-8 hex gives byte order, including non-BMP names.
paths = paths(order);
engine = java.security.MessageDigest.getInstance('SHA-256');
for k = 1:numel(paths)
    path = project_path(root, paths(k));
    hash = file_digest(path);
    engine.update([unicode2native(char(paths(k)), 'UTF-8'), uint8(0)]);
    engine.update(uint8(sscanf(hash, '%2x').'));
end
result = digest_hex(engine);
end

function result = digest_hex(engine)
bytes = typecast(engine.digest(), 'uint8');
result = lower(reshape(dec2hex(bytes, 2).', 1, []));
end

function receipt = make_receipt(config, identity, elapsed, reason, count)
receipt = struct('run_receipt_version','1.1.0','execution_owner','user', ...
    'execution_profile','full_fidelity','stage',config.stage,'problem_name',config.problem_name, ...
    'solver_backend','matlab','code_sha256',identity.code_sha256, ...
    'code_bundle_sha256',identity.code_bundle_sha256,'data_sha256',identity.data_sha256, ...
    'solver',config.solver,'solver_version',version,'tolerance',config.tolerance, ...
    'iteration_or_time_limit',config.iteration_or_time_limit,'actual_stop_reason',reason, ...
    'random_seed',config.random_seed,'repetitions_or_scenarios',count, ...
    'grid_or_time_range','all declared inputs','fallback_used',false,'platform',computer, ...
    'allow_reduced_data',false,'allow_coarser_grid',false,'allow_shorter_horizon',false, ...
    'allow_fewer_repetitions',false,'allow_relaxed_tolerance',false, ...
    'allow_silent_solver_fallback',false,'matlab_release',version('-release'), ...
    'elapsed_seconds',elapsed);
end

function cells = receipt_cells(receipt)
names = fieldnames(receipt);
cells = [{'项目','值'}; names,struct2cell(receipt)];
end

function write_workbook(path, sheets)
names = string(sheets(:, 1));
assert(all(strlength(strtrim(names)) > 0) && numel(unique(lower(strtrim(names)))) == numel(names), ...
    'HSK:Sheet', 'Empty or duplicate worksheet names.');
for index = 1:numel(names)
    validate_sheet(names(index), sheets{index, 2});
end
temporary = string(tempname(fileparts(path))) + ".xlsx";
cleanup = onCleanup(@() remove_temporary(temporary));
for index = 1:numel(names)
    writecell(sheets{index, 2}, temporary, 'Sheet', char(names(index)), 'UseExcel', false);
end
[success, message] = movefile(temporary, path, 'f');
assert(success, 'HSK:Write', 'Workbook replacement failed: %s', message);
end

function validate_sheet(name, cells)
assert(strlength(name) <= 31 && isempty(regexp(char(name), '[:\\/?*\[\]]', 'once')), ...
    'HSK:Sheet', 'Invalid worksheet name.');
headers = string(cells(1, :));
assert(size(cells, 1) > 1 && all(strlength(strtrim(headers)) > 0) && ...
    numel(unique(strtrim(headers))) == numel(headers), 'HSK:Sheet', 'Empty sheet or duplicate headers.');
key = find(headers == "记录键");
if ~isempty(key), validate_keys(cells(2:end, key)); end
for k = 1:numel(cells)
    item = cells{k};
    text = (ischar(item) && isrow(item)) || (isstring(item) && isscalar(item) && ~ismissing(item));
    numeric = (isnumeric(item) || islogical(item)) && isscalar(item) && isreal(item) && isfinite(item);
    assert(text || numeric, 'HSK:Cell', 'Only finite real scalars, logicals, or explicit text are supported.');
end
end

function validate_keys(cells)
for k = 1:numel(cells)
    value = cells{k};
    if isnumeric(value)
        assert(isscalar(value) && isfinite(value) && abs(value) <= flintmax, ...
            'HSK:Key', 'Large identifiers must be explicit text.');
    end
end
keys = strtrim(string(cells));
assert(all(~ismissing(keys) & strlength(keys) > 0) && numel(unique(keys)) == numel(keys), ...
    'HSK:Key', 'Record keys must be nonempty and unique.');
end

function remove_temporary(path)
if isfile(path), delete(path); end
end
