function report = run_solver_backend_smoke(projectRoot, stage)
% Run only explicitly prepared synthetic fixtures, never a user competition model.
arguments
    projectRoot (1,1) string
    stage (1,1) string {mustBeMember(stage,["primary","analysis"])}
end
preprocessed = isfile(fullfile(projectRoot,"preprocessing_native_fixture.json"));
if preprocessed
    preprocessingBook = fullfile(projectRoot,"数据预处理","数据预处理结果.xlsx");
    preprocessingBytes = fileread_bytes(preprocessingBook);
else
    assert(isfile(fullfile(projectRoot,"input.json")), 'Synthetic input is missing.');
end
marker = jsondecode(fileread(fullfile(projectRoot,"synthetic_fixture.json")));
assert(strcmp(marker.fixture,'solver_backend_native_v1') && strcmp(marker.purpose,'repository_test'), ...
    'This harness only runs explicitly prepared repository fixtures.');
repo = string(fileparts(fileparts(fileparts(mfilename('fullpath')))));
folder = fullfile(projectRoot,"问题一求解");
previousPath = path;
cleanup = onCleanup(@() path(previousPath));
addpath(folder,projectRoot,fullfile(repo,"templates","matlab"));
primary = fullfile(folder,"问题一求解结果.xlsx");
if stage == "primary"
    diagnostics = checkcode(fullfile(folder,"q1_solver.m"),'-id','-cyc');
    workbook = q1_solver();
    negative = strings(0, 1);
    typeProbe = "not_run_for_preprocessing";
    if ~preprocessed
        negative = run_negative_cases(projectRoot, primary);
        typeProbe = run_type_probe(projectRoot);
        native_hash_probe(projectRoot);
    end
else
    diagnostics = checkcode(fullfile(folder,"q1_analysis.m"),'-id','-cyc');
    before = fileread_bytes(primary);
    workbook = q1_analysis();
    assert(isequal(before,fileread_bytes(primary)), 'Analysis changed the primary workbook.');
    negative = strings(0, 1);
    typeProbe = "not_run_for_analysis";
end
books = hsk_read_result_workbooks(folder);
assert(books.solution == primary, 'The original reader selected another primary workbook.');
raw = readcell(primary,'Sheet','核心指标');
assert(isequal(string(raw(1,:)),["指标","数值"]), 'Native headers changed.');
report = struct('stage',stage,'matlab_release',version('-release'),'matlab_version',version, ...
    'workbook',workbook,'actual_matlab_execution',true,'code_analyzer',diagnostics, ...
    'negative_cases',negative,'type_probe',typeProbe,'status','passed');
if preprocessed
    assert(isequal(preprocessingBytes,fileread_bytes(preprocessingBook)), 'Solver changed the preprocessing workbook.');
    report.preprocessing_workbook_unchanged = true;
end
fid = fopen(fullfile(projectRoot,stage + "_matlab_report.json"),'w','n','UTF-8');
assert(fid >= 0, 'Cannot write smoke report.');
reportCleanup = onCleanup(@() fclose(fid));
fwrite(fid,jsonencode(report),'char');
end

function bytes = fileread_bytes(filename)
fid = fopen(filename,'rb');
assert(fid >= 0, 'Cannot read the primary workbook.');
cleanup = onCleanup(@() fclose(fid));
bytes = fread(fid,Inf,'*uint8');
end

function completed = run_negative_cases(projectRoot, primary)
cases = ["input_hash","missing_input","nonfinite_result"];
identifiers = ["HSK:InputHash","HSK:Read","HSK:Cell"];
completed = strings(0, 1);
originalPath = path;
cleanup = onCleanup(@() path(originalPath));
for index = 1:numel(cases)
    folder = fullfile(projectRoot,"negative",cases(index),"问题一求解");
    target = fullfile(folder,"问题一求解结果.xlsx");
    copyfile(primary,target);
    before = fileread_bytes(target);
    addpath(folder);
    clear q1_solver
    caught = false;
    try
        q1_solver();
    catch failure
        caught = true;
        assert(string(failure.identifier) == identifiers(index), 'Unexpected negative-case failure: %s',failure.message);
    end
    assert(caught, 'Invalid synthetic input was accepted.');
    assert(isequal(before,fileread_bytes(target)), 'A failed run replaced the valid old workbook.');
    assert(numel(dir(fullfile(folder,"*.xlsx"))) == 1, 'A temporary workbook leaked into output.');
    rmpath(folder);
    completed(end + 1, 1) = cases(index); %#ok<AGROW>
end
clear q1_solver
end

function result = run_type_probe(projectRoot)
folder = fullfile(projectRoot,"type-probe","问题一求解");
if ~isfolder(folder), mkdir(folder); end
filename = fullfile(folder,"问题一求解结果.xlsx");
native_writer_probe(filename,"valid");
spec = struct('headers',["记录键","数值","标记"], ...
    'key_header',"记录键",'numeric_headers',["数值","标记"],'allow_missing_headers',"数值");
requirements.solution = {'类型往返',spec};
hsk_read_result_workbooks(folder,"",requirements);
check_reader_requirements(folder,requirements,spec);
before = fileread_bytes(filename);
modes = ["duplicate_header","duplicate_key","infinite","duplicate_sheet","empty_sheet"];
identifiers = ["HSK:Sheet","HSK:Key","HSK:Cell","HSK:Sheet","HSK:Sheet"];
for k = 1:numel(modes)
    caught = false;
    try
        native_writer_probe(filename,modes(k));
    catch failure
        caught = true;
        assert(string(failure.identifier) == identifiers(k), 'Unexpected writer rejection: %s',failure.message);
    end
    assert(caught && isequal(before,fileread_bytes(filename)), 'Invalid write was accepted or changed the old workbook.');
end
result = "text_keys_logicals_missing_rows_and_rejections_passed";
end

function check_reader_requirements(folder,requirements,spec)
bad = {{'类型往返',spec;'类型往返',spec}, {'',spec}};
for k = 1:numel(bad)
    invalid.solution = bad{k};
    caught = false;
    try
        hsk_read_result_workbooks(folder,"",invalid);
    catch failure
        caught = true;
        assert(string(failure.identifier) == "HSK:SheetRequirements");
    end
    assert(caught, 'Invalid exact sheet declarations were accepted.');
end
filename = fullfile(folder,"问题一求解结果.xlsx");
writecell({'记录键','数值','标记';'0001',1.5,true},filename,'Sheet','LegacyASCII','UseExcel',false);
legacy.solution.LegacyASCII = spec;
hsk_read_result_workbooks(folder,"",legacy);
hsk_read_result_workbooks(folder,"",requirements);
end
