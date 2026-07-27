# Module 04：MATLAB 结果图证据、标题与机理图精修

## 正确顺序

1. Python 完成求解、检验并锁定两类标准工作簿；
2. 为每张图先写 Core conclusion，再按信息效率和图型选择模板选图；
3. 生成 MATLAB 代码前实际读取工作簿，锁定工作簿名、工作表名、真实表头、单位和数据类型；
4. 字段定位采用精确表头唯一匹配；期望列号只作结构漂移警告，不作为唯一读取机制；
5. 设置简洁 `title` 或一个整体 `sgtitle`，并拟定不逐字重复的论文图注；
6. 将 `q{x}_plot.m` 与两类工作簿放在同一问题目录；
7. 检查每个核心结论是否有图或表证据，并同步框架；
8. 只精修 S/A 级机理图；
9. 正式交付前运行项目同步器。

## A 类：机理与推导图

优先表达公式来源、约束来源和临界状态，其次是对象关系和策略机制。图内只放对象、变量、方向、边界、距离、角度、流向和临界状态，完整推导留在正文。禁止用通用“输入—模型—输出”流程图替代题目专属机理图。

## B 类：结果图合同

每张图记录：Core conclusion、Figure role、MATLAB title、论文 caption、Panel map、Source workbook、Worksheet、Required headers、Expected positions（可选）、MATLAB script、Export files、Statistics/error、Reviewer risk、Paper location 和 Caption duty。

数据源仅允许来自每问两类标准工作簿。不得在 MATLAB 中重算核心指标，不得从摘要数字反推绘图序列。图型必须提高信息展示或比较效率，否则降级为更直接的二维图。

## 实表读取规则

正式脚本必须：

1. 使用已核对的真实工作簿名、工作表名和表头；
2. 读取第一行原始表头并做空白归一化；
3. 对每个要求字段执行精确相等匹配，并断言只出现一次；
4. 可登记期望列号，当实际位置变化时给出清晰结构漂移警告；
5. 禁止模糊匹配、别名词典、相似字段猜测、自动回退和运行时改变语义映射；
6. 工作簿或表头变化后重新读取并更新 Figure Contract；
7. 检查文件、工作表、非空、主键、非法值和排序。

示例：

```matlab
headers = strtrim(string(raw(1, :)));
xMatches = find(headers == xHeader);
assert(numel(xMatches) == 1, "字段缺失或重复: %s", xHeader);
xColumn = xMatches(1);
if isfinite(expectedXColumn) && xColumn ~= expectedXColumn
    warning("字段%s由第%d列移动到第%d列", xHeader, expectedXColumn, xColumn);
end
```

## 图标题与风格

单图使用 `title`，多面板使用一个 `sgtitle`。标题只说明研究对象、指标关系和必要方法，不写结论长句。默认白底、细轴、低饱和深色、中文坐标轴和单位、字号 18，网格关闭或极浅。颜色不是固定约束，但同一对象和同一语义应保持一致。图窗默认可见，不批量自动导出。

## 入文闭环

图后另起正文段解释趋势、关键数值、机制和结论作用。无法绑定小问、公式、工作簿、工作表、真实表头、MATLAB 脚本、框架映射或正文结论的图删除。
