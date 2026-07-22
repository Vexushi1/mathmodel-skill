function projectRoot = hsk_find_project_root(startPath)
% 兼容辅助函数。新项目的 q{x}_plot.m 默认不调用本函数，
% 而是直接以自身所在的“结果数据表/问题X/”为结果目录。
arguments
    startPath (1,1) string = string(pwd)
end

if isfile(startPath)
    current = string(fileparts(startPath));
else
    current = startPath;
end

for depth = 1:12
    if isfolder(fullfile(current, "结果数据表"))
        projectRoot = current;
        return;
    end

    [parentPath, folderName] = fileparts(char(current));
    if startsWith(string(folderName), "问题")
        [grandParent, parentName] = fileparts(parentPath);
        if string(parentName) == "结果数据表"
            projectRoot = string(grandParent);
            return;
        end
    end

    parent = string(fileparts(current));
    if strlength(parent) == 0 || parent == current
        break;
    end
    current = parent;
end

error(["未找到项目根目录。" newline ...
    "新项目应包含 结果数据表/，每问 q{x}_plot.m 与工作簿同放在结果数据表/问题X/。"]);
end
