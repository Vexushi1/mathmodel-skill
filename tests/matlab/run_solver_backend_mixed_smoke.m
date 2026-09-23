function report = run_solver_backend_mixed_smoke(projectRoot)
% Q2 runs natively from the same MATLAB project's accepted Q1 primary.
arguments
    projectRoot (1,1) string
end
marker = jsondecode(fileread(fullfile(projectRoot,"synthetic_fixture.json")));
assert(strcmp(marker.fixture,'same_backend_solver_native_v1') && strcmp(marker.purpose,'repository_test'));
root = fullfile(projectRoot,"matlab-project");
previousPath = path;
cleanup = onCleanup(@() path(previousPath));
addpath(fullfile(root,"问题一求解"),fullfile(root,"问题二求解"));
primary = fullfile(root,"问题一求解","问题一求解结果.xlsx");
before = bytes(primary);
downstream = q2_solver();
assert(isequal(before,bytes(primary)), 'Q2 changed the accepted MATLAB Q1 primary.');
report = struct('status','passed','actual_matlab_execution',true,'matlab_release',version('-release'), ...
    'downstream_workbook',downstream,'upstream_primary_unchanged',true);
fid = fopen(fullfile(projectRoot,"same_backend_matlab_report.json"),'w','n','UTF-8');
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
