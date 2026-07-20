function projectRoot = hsk_find_project_root(startPath)
% 从脚本目录向上查找数学建模项目根目录。
arguments
    startPath (1,1) string = string(pwd)
end
if isfile(startPath)
    current = string(fileparts(startPath));
else
    current = startPath;
end
for depth = 1:12
    hasResults = isfolder(fullfile(current, "结果数据表"));
    hasMatlab = isfolder(fullfile(current, "MATLAB绘图"));
    hasPython = isfolder(fullfile(current, "Python求解"));
    if hasResults && (hasMatlab || hasPython)
        projectRoot = current;
        return;
    end
    parent = string(fileparts(current));
    if strlength(parent) == 0 || parent == current
        break;
    end
    current = parent;
end
error("未找到项目根目录。应至少包含结果数据表/，并包含 MATLAB绘图/ 或 Python求解/。");
end
