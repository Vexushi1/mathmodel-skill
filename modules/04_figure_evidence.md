# Module 04：MATLAB 结果图、预处理图证据与机理图精修

## 正确顺序

1. 继承已经锁定的 `preprocessing_decision`；若为 `project_level`，确认 `数据预处理结果.xlsx` 已 accepted 且预处理质量门通过，但此时不要求先生成 `data_process.m`；
2. Python 完成完整主求解并通过主结果质量门；
3. Python 基于题目风险完成实际需要的结果深化分析，并验收 `问题X求解/` 中两个标准工作簿；
4. 只有上述数值阶段完成后才进入 Figure Evidence；先明确每张图读取原始数据、统一预处理工作簿或结果工作簿中的哪一种事实源；
5. 若为 `project_level`，此时生成并人工检查 `数据预处理/data_process.m`，只把已验收预处理工作簿中的底层证据转成图；
6. 为各问结果图先写 Core conclusion，再按信息效率选择图型；
7. 生成 MATLAB 代码前实际读取工作簿，锁定工作簿名、工作表名、真实表头、单位和数据类型；
8. 设置简洁 `title` 或一个整体 `sgtitle`，拟定不逐字重复的论文图注；
9. 将各问 `q{x}_plot.m` 与两类 Python 脚本、两类结果工作簿放在同一 `问题X求解/`；项目级预处理图脚本固定为 `数据预处理/data_process.m`；
10. 检查核心结论是否有图或表证据，并同步 `模型论文框架.md`；
11. 默认只保留图窗供人工检查，不自动创建图表子目录或批量导出图片。

## A 类：机理与推导图

优先表达公式来源、约束来源、临界状态和策略机制。图内只放对象、变量、方向、边界、距离、角度、流向和临界状态，完整推导留在正文。禁止用通用“输入—模型—输出”流程图替代题目专属机理图。

## B 类：项目级预处理证据图

当 `preprocessing_decision=project_level` 时，必须生成独立 MATLAB 脚本：

```text
数据预处理/data_process.m
```

它只读取：

```text
数据预处理/数据预处理结果.xlsx
```

其职责是把 Python 已经保存的处理前/后、诊断和验证底层数据转成论文证据图。MATLAB 不允许重新清洗、插值、滤波、重采样、预测填补、训练模型或重新确定参数。

至少有一张图直接回答下列问题之一：

- 为什么原始数据需要处理；
- 当前处理是否解决了已审计问题；
- 插值/填补恢复误差是否可接受；
- 滤波/平滑是否保留所需信息；
- 重采样/时间对齐/空间对齐是否满足模型输入要求；
- 异常处理是否有清晰边界并避免误删真实结构。

优先图型包括：

- 处理前后时序、轨迹、空间场或剖面对比；
- 缺失位置/覆盖与填补结果图；
- 分布、箱线、QQ、残差、尺度变化图；
- 频谱/功率谱/频率响应处理前后对比；
- 人工掩蔽或留出样本的真实值—恢复值图及误差分布；
- 重采样前后的网格/采样间隔/覆盖图；
- 异常阈值边界与保留/处理样本图。

`data_process.m` 的 Figure Contract 必须记录：Core conclusion、Figure role、MATLAB title、论文 caption、Source workbook=`数据预处理结果.xlsx`、Worksheet、Required headers、Panel map、Statistics/error、Paper location。

若需要正式导出，文件基名固定为：

```text
data_process
或
data_process_<evidence>
```

默认仍不自动导出，先保留图窗人工调整。

## C 类：各问结果图合同

每张结果图记录：Core conclusion、Figure role、MATLAB title、论文 caption、Panel map、Source workbook、Worksheet、Required headers、Expected positions（可选）、MATLAB script、Export files、Statistics/error、Reviewer risk、Paper location 和 Caption duty。

结果证据优先来自本问主求解工作簿或结果深化分析工作簿：

- 主结果、决策变量、预测明细、基础误差和质量门证据来自 `问题X求解结果.xlsx`；
- 参数、场景、算法、结构、阈值、异质性和稳定范围证据来自 `问题X结果深化分析.xlsx`。

只有图本身确实需要底层数据时，才按 `preprocessing_decision` 追加数据事实源：

- `not_needed`：允许读取必要原始数据；
- `question_local`：允许读取必要原始数据，但不得在 MATLAB 中重新构造模型变换；若该局部处理需要论文图证据，应由 Python 将处理前后底层数据写入本问工作簿，再由 `qX_plot.m` 绘制；
- `project_level`：各问需要底层公共数据时读取 `数据预处理结果.xlsx`，不得绕回共享原始附件；公共预处理本身的前后对比优先集中在 `data_process.m`。

不得为了统一脚本结构而强制所有 `qX_plot.m` 读取 `数据预处理结果.xlsx`。若图只依赖标准结果工作簿，则不额外加载任何原始或预处理数据。

不得在 MATLAB 中重新求解，不得从摘要数字反推绘图序列。图型必须提高信息展示或比较效率，否则降级为更直接的二维图。

## 实表读取规则

正式脚本必须：

1. 使用已核对的真实工作簿名、工作表名和表头；
2. 读取第一行原始表头并做空白归一化；
3. 对每个要求字段执行精确相等匹配，并断言只出现一次；
4. 可登记期望列号，当实际位置变化时给出结构漂移警告；
5. 禁止模糊匹配、别名词典、相似字段猜测和自动回退；
6. 工作簿变化后重新读取并更新 Figure Contract；
7. 检查文件、工作表、非空、主键、非法值和排序。

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

## 分析图准入

结果深化分析不是每种方法都要画图。只有满足以下条件时才入图：

- 分析方法与风险来源匹配；
- 图能展示稳定范围、阈值、算法一致性、结构稳健性、结构差异或异质性；
- 图的底层数据已完整写入分析工作簿；
- 图能直接支撑正文中的一个核心判断。

统一扰动曲线、无解释的算法柱状图和只展示“结果变化不大”的装饰图删除。

## 入文闭环

预处理图后正文必须解释原始问题、处理机制、关键参数、验证误差或信息保留情况，以及处理后数据为何可以进入后续模型；结果图后解释趋势、关键数值、机制、稳定范围或失效边界。正式图片进入 LaTeX 时按需人工导出。
