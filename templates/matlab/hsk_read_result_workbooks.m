function books = hsk_read_result_workbooks(projectRoot, problemName)
% 返回每问两类标准结果工作簿及其工作表名称。
arguments
    projectRoot (1,1) string
    problemName (1,1) string
end
resultDir = fullfile(projectRoot, "结果数据表", problemName, problemName + "结果数据");
books.solution = fullfile(resultDir, problemName + "求解结果.xlsx");
books.robustness = fullfile(resultDir, problemName + "敏感性与鲁棒性结果.xlsx");
assert(isfile(books.solution), "缺少求解结果工作簿: %s", books.solution);
assert(isfile(books.robustness), "缺少敏感性与鲁棒性工作簿: %s", books.robustness);
books.solutionSheets = string(sheetnames(books.solution));
books.robustnessSheets = string(sheetnames(books.robustness));
end
