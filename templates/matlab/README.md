# HSK MATLAB 科研绘图模板 v6.2.1

MATLAB 只读取 Python 输出的两类标准工作簿，不重新求解。

```text
结果数据表/问题X/问题X结果数据/
├─ 问题X求解结果.xlsx
└─ 问题X敏感性与鲁棒性结果.xlsx
```

使用顺序：

1. `books = hsk_read_result_workbooks(projectRoot, "问题一")`；
2. 用 `readtable(books.solution, "Sheet", "明细结果")` 读取工作表；
3. 运行问题专属绘图脚本；
4. 保留可见图窗，人工调整尺寸、图例和标签；
5. 需要导出时显式调用 `hsk_export_figure(fig, outputBase)`。

禁止默认隐藏图窗、批量自动导出、关闭图窗或在 MATLAB 中重新计算核心结果。
