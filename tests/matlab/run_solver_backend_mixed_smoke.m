function report = run_solver_backend_mixed_smoke(projectRoot)
% Both primary and analysis run natively after Python's accepted primary.
arguments
    projectRoot (1,1) string
end
marker = jsondecode(fileread(fullfile(projectRoot,"synthetic_fixture.json")));
assert(strcmp(marker.fixture,'mixed_solver_native_v1') && strcmp(marker.purpose,'repository_test'));
root = fullfile(projectRoot,"python-to-matlab");
previousPath = path;
cleanup = onCleanup(@() path(previousPath));
addpath(fullfile(root,"问题一求解"),fullfile(root,"问题二求解"));
primary = fullfile(root,"问题一求解","问题一求解结果.xlsx");
before = bytes(primary);
downstream = q2_solver();
analysis = q1_analysis();
assert(isequal(before,bytes(primary)), 'Mixed stages changed the accepted Python primary.');
report = struct('status','passed','actual_matlab_execution',true,'matlab_release',version('-release'), ...
    'downstream_workbook',downstream,'analysis_workbook',analysis,'upstream_primary_unchanged',true);
fid = fopen(fullfile(projectRoot,"mixed_matlab_report.json"),'w','n','UTF-8');
assert(fid >= 0);
reportCleanup = onCleanup(@() fclose(fid));
fwrite(fid,jsonencode(report),'char');
end

function value = bytes(filename)
fid = fopen(filename,'rb');
assert(fid >= 0);
cleanup = onCleanup(@() fclose(fid));
value = fread(fid,Inf,'*uint8');
end
