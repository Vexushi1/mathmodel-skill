function workbook = analysis_comparison_example()
RUN_CONFIG = jsondecode('{"stage":"analysis","problem_name":"问题一","solver_backend":"matlab","data_paths":["input.json"],"data_sha256":"__DATA_SHA256__","solver":"explicit_qr_svd_comparison","random_seed":2026,"tolerance":1e-10,"iteration_or_time_limit":"direct","expected_workbook":"问题一求解/问题一结果深化分析.xlsx","run_receipt_protocol_version":"1.1.0","code_dependencies":[],"primary_workbook":"问题一求解/问题一求解结果.xlsx","primary_workbook_sha256":"__ACCEPTED_PRIMARY_SHA256__","analysis_comparison_protocol_version":"1.0.0","analysis_comparison_plan_sha256":"__FROZEN_PLAN_SHA256__"}');
% Instantiate the approved scope and plan; this source does not grant approval.
% Repository fixtures also instantiate its primary QR branch in q1_solver.m.
entrypoint = string(mfilename('fullpath')) + ".m";
root = string(fileparts(fileparts(entrypoint)));
assert(usejava('jvm'), 'HSK:Environment', 'SHA-256 requires the MATLAB JVM.');
identity = verify_inputs(root, entrypoint, RUN_CONFIG);
assert(strcmp(RUN_CONFIG.iteration_or_time_limit,'direct'), 'HSK:Policy', 'Use the complete direct-decomposition policy.');
rng(RUN_CONFIG.random_seed,'twister');
started = tic;
payload = read_model_input(root,RUN_CONFIG);
assert(numel(payload.scenarios) == numel(payload.evaluation_t) && ~isempty(payload.scenarios) && ...
    numel(unique(string(payload.scenarios))) == numel(payload.scenarios), ...
    'HSK:Scenarios', 'Every declared evaluation point needs one unique scenario.');
if strcmp(RUN_CONFIG.stage,'primary')
    assert(strcmp(RUN_CONFIG.solver,'explicit_qr'), 'HSK:Solver', 'Wrong primary decomposition policy.');
    [sheets,passed] = primary_tables(RUN_CONFIG,payload);
    receipt = make_receipt(RUN_CONFIG,identity,toc(started),'all_declared_decompositions_completed',1);
    receipt.primary_quality_protocol_version = RUN_CONFIG.primary_quality_protocol_version;
else
    assert(strcmp(RUN_CONFIG.stage,'analysis') && strcmp(RUN_CONFIG.solver,'explicit_qr_svd_comparison'), ...
        'HSK:Solver', 'Wrong analysis decomposition policy.');
    primary = project_path(root,RUN_CONFIG.primary_workbook);
    assert(strcmpi(file_digest(primary),RUN_CONFIG.primary_workbook_sha256), 'HSK:Primary', 'Accepted primary workbook changed.');
    identity.primary_workbook_sha256 = file_digest(primary);
    sheets = analysis_tables(root,RUN_CONFIG,payload);
    passed = true; % Analysis conclusion is reviewed separately; source failure still throws.
    receipt = make_receipt(RUN_CONFIG,identity,toc(started),'all_declared_decompositions_completed',2);
    receipt.primary_workbook_sha256 = identity.primary_workbook_sha256;
    receipt.analysis_comparison_protocol_version = RUN_CONFIG.analysis_comparison_protocol_version;
    receipt.analysis_comparison_plan_sha256 = RUN_CONFIG.analysis_comparison_plan_sha256;
end
sheets(end+1,:) = {'运行配置',receipt_cells(receipt)};
current = verify_inputs(root,entrypoint,RUN_CONFIG);
if strcmp(RUN_CONFIG.stage,'analysis')
    current.primary_workbook_sha256 = file_digest(project_path(root,RUN_CONFIG.primary_workbook));
end
assert(isequal(identity,current), 'HSK:IdentityChanged', 'Source, input or primary changed during execution.');
workbook = project_path(root,RUN_CONFIG.expected_workbook);
write_workbook(workbook,sheets);
assert(passed, 'HSK:Quality', 'The workbook records a failed primary numerical check.');
end

function [sheets,passed] = primary_tables(config,payload)
[coefficients,predictions,residual] = hsk_comparison_fit(payload.train_t,payload.train_y,2,"QR",payload.evaluation_t);
rows = cell(numel(predictions)+numel(coefficients),6);
for k = 1:numel(predictions)
    rows(k,:) = {sprintf('prediction-%d',k-1),'prediction',predictions(k),'dimensionless',payload.scenarios{k},'prediction'};
end
for k = 1:numel(coefficients)
    rows(numel(predictions)+k,:) = {sprintf('coefficient-%d',k-1),'coefficient',coefficients(k),'dimensionless',sprintf('coefficient-%d',k-1),'coefficient'};
end
passed = residual <= config.tolerance;
sheets = {'核心指标',{'指标','数值';'留出预测',predictions(end);'正规方程残差',residual}; ...
    '数据审计',{'等级','检查项','信息','处理方式';'info','有限成对样本','完整原始训练和评价点','只读检查'}; ...
    '主结果质量门',{'Verification ID','检查项','是否通过','证据','判定关系','阈值或容差','实际值','证据工作表','阈值来源'; ...
      'PQ-Q1-01','最小二乘正规方程残差',passed,'从完整设计矩阵重算','abs<=',config.tolerance,residual,'均衡残差','solver_tolerance'}; ...
    '均衡残差',{'主体或均衡','残差','容差','是否满足';'X.T*(X*c-y)=0',residual,config.tolerance,passed}; ...
    '状态明细',[{'记录键','状态','数值','单位','实例或场景','指标'};rows]};
end

function sheets = analysis_tables(root,config,payload)
raw = readcell(project_path(root,config.primary_workbook),'Sheet','状态明细');
headers = string(raw(1,:));
keyColumn = find(headers == "记录键");
valueColumn = find(headers == "数值");
assert(isscalar(keyColumn) && isscalar(valueColumn), 'HSK:Headers', 'Primary headers are missing or duplicated.');
keys = string(raw(2:end,keyColumn));
count = numel(payload.evaluation_t);
baseline = zeros(count,1);
for k = 1:count
    selected = find(keys == sprintf('prediction-%d',k-1));
    assert(isscalar(selected), 'HSK:Primary', 'Primary prediction key is missing or duplicated.');
    baseline(k) = raw{selected+1,valueColumn};
end
[~,linear,linearResidual] = hsk_comparison_fit(payload.train_t,payload.train_y,1,"QR",payload.evaluation_t);
[~,svdPrediction,svdResidual] = hsk_comparison_fit(payload.train_t,payload.train_y,2,"SVD",payload.evaluation_t);
models = cell(count,17);
algorithms = cell(count,19);
for k = 1:count
    modelDifference = linear(k)-baseline(k);
    algorithmDifference = svdPrediction(k)-baseline(k);
    models(k,:) = {'CMP-Q1-01',sprintf('model-%d',k-1),'MODEL-Q1-01','MODEL-Q1-02','EVAL-Q1-01',payload.scenarios{k}, ...
        'prediction','dimensionless',baseline(k),linear(k),'difference',modelDifference,'CRIT-CMP-Q1-01', ...
        abs(modelDifference)>=payload.model_difference_threshold,linearResidual,char("QR/MATLAB " + string(version)),'decomposition_completed'};
    algorithms(k,:) = {'CMP-Q1-02',sprintf('algorithm-%d',k-1),'MODEL-Q1-01','ALGO-Q1-01','ALGO-Q1-02','EVAL-Q1-02',payload.scenarios{k}, ...
        1,'prediction','dimensionless',baseline(k),svdPrediction(k),'difference',algorithmDifference,'CRIT-CMP-Q1-02', ...
        abs(algorithmDifference)<=config.tolerance,svdResidual,char("SVD/MATLAB " + string(version)),'decomposition_completed'};
end
sheets = {'分析设计',{'风险来源','分析问题','方法','指标','通过标准','检验ID','判据ID'; ...
    '模型结构','二次项是否影响共同留出预测','多模型检验','prediction','预设留出差异下界','CMP-Q1-01','CRIT-CMP-Q1-01'; ...
    '求解方法','同一二次模型QR与SVD是否一致','同模型多算法检验','prediction','预设数值容差','CMP-Q1-02','CRIT-CMP-Q1-02'}; ...
    '多模型检验',[{'检验ID','记录键','主模型ID','对照模型ID','评价协议ID','实例或场景','指标','单位','主模型数值','对照模型数值','差异类型','差异','判据ID','判定','残差','求解器及版本','停止原因'};models]; ...
    '同模型多算法检验',[{'检验ID','记录键','模型ID','基准算法ID','对照算法ID','评价协议ID','实例或场景','重复编号','指标','单位','基准数值','对照数值','差异类型','差异','判据ID','判定','残差','求解器版本','停止原因'};algorithms]; ...
    '结论稳定性汇总',{'核心结论','分析方法','稳定范围','是否保持','检验ID','证据工作表'; ...
      '此案例二次项影响留出预测','多模型检验','声明的共同留出点',models{end,14},'CMP-Q1-01','多模型检验'; ...
      '同模型预测对QR/SVD一致','同模型多算法检验','全部声明评价点',all(cell2mat(algorithms(:,16))),'CMP-Q1-02','同模型多算法检验'}};
end

function identity = verify_inputs(root, entrypoint, config)
assert(strcmp(config.solver_backend, 'matlab'), 'HSK:Backend', 'Wrong execution backend.');
validateattributes(config.random_seed, {'numeric'}, {'scalar','integer','nonnegative','<=',2^32-1});
validateattributes(config.tolerance, {'numeric'}, {'scalar','real','finite','positive'});
inputs = string(config.data_paths(:));
assert(~isempty(inputs), 'HSK:Input', 'Declare at least one actual input.');
identity.data_sha256 = input_digest(root, inputs, config);
assert(strcmpi(identity.data_sha256, config.data_sha256), 'HSK:InputHash', 'Input hash does not match RUN_CONFIG.');
auxiliaryHash = auxiliary_input_digest(root, inputs, config);
if auxiliaryHash ~= "", identity.auxiliary_data_sha256 = auxiliaryHash; end
entryRelative = replace(extractAfter(entrypoint, strlength(root) + 1), '\', '/');
sources = strings(numel(config.code_dependencies) + 1, 1);
sources(1) = entryRelative;
if ~isempty(config.code_dependencies)
    assert(isstruct(config.code_dependencies), 'HSK:Dependencies', 'Dependencies must be path/hash records.');
    for k = 1:numel(config.code_dependencies)
        dep = config.code_dependencies(k);
        path = project_path(root, dep.path);
        assert(strcmpi(file_digest(path), dep.sha256), 'HSK:Dependencies', 'Dependency hash mismatch.');
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

function hash = auxiliary_input_digest(root, inputs, config)
protocol = string(config.run_receipt_protocol_version);
assert(isscalar(protocol) && any(protocol == ["1.1.0","1.2.0"]), ...
    'HSK:Protocol', 'Unsupported numerical receipt protocol.');
fields = isfield(config, {'auxiliary_data_paths','auxiliary_data_sha256'});
hash = "";
if protocol == "1.1.0"
    assert(~any(fields), 'HSK:Protocol', 'Auxiliary inputs require receipt 1.2.0.');
    return
end
assert(all(fields) && data_identity_mode(config) == "preprocessing_workbook", ...
    'HSK:Protocol', 'Receipt 1.2.0 requires preprocessing and complete auxiliary inputs.');
assert(iscell(config.auxiliary_data_paths), 'HSK:Input', 'Auxiliary paths must be an array.');
paths = string(config.auxiliary_data_paths(:));
assert(~isempty(paths) && all(strlength(paths) > 0), 'HSK:Input', 'Auxiliary inputs cannot be empty.');
assert_distinct_files(root, [inputs; paths]);
hash = files_digest(root, paths);
assert(strcmpi(hash, config.auxiliary_data_sha256), 'HSK:InputHash', 'Auxiliary input hash mismatch.');
end

function assert_distinct_files(root, paths)
paths = string(paths(:));
assert(numel(unique(lower(paths))) == numel(paths), 'HSK:Path', 'Duplicate or case-aliased inputs.');
for k = 1:numel(paths)
    current = java.io.File(char(project_path(root, paths(k))));
    for j = 1:k-1
        previous = java.io.File(char(project_path(root, paths(j))));
        assert(~java.nio.file.Files.isSameFile(current.toPath(), previous.toPath()), ...
            'HSK:Path', 'Different declared inputs alias the same file.');
    end
end
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
receipt = struct('run_receipt_version',config.run_receipt_protocol_version,'execution_owner','user', ...
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
if strcmp(config.run_receipt_protocol_version, '1.2.0')
    receipt.data_identity_mode = 'preprocessing_workbook';
    receipt.auxiliary_data_paths = jsonencode(config.auxiliary_data_paths(:).');
    receipt.auxiliary_data_sha256 = identity.auxiliary_data_sha256;
end
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
