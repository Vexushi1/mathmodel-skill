# Module 03B：结果深化分析与证据增强

本模块只在主结果质量门通过后执行。输入必须是在当前模型口径下已经算准并锁定的主结果；结果深化分析不得补救未收敛、不可行或基础精度不足的主求解。

## 1. 分析目标

回答结果形成机制、主导因素、稳定范围、阈值与失效边界、算法偶然性、结构依赖、群体差异及最值得进入正文的证据。敏感性、鲁棒性和多算法只是候选方法，不是固定三件套。

## 2. 风险驱动的方法选择

先建立 `result_analysis_plan`，每项至少记录：风险来源、具体分析问题、方法、输入、指标、通过标准和论文作用。根据题目、模型、数据、主结果表现和评委质疑点按需选择：

- 参数与机制敏感性；
- 场景压力和不确定性传播；
- 多算法、多初值及数值一致性；
- 结构稳健性；
- 异质性和误差分解；
- 阈值、边界和极端情景；
- 外样本与迁移稳定性。

禁止统一 ±5%、±10% 扰动、把随机重复直接称为鲁棒性、重复包装主求解器状态、生成空表或装饰图。

## 3. 结构化运行结果

Python 分析钩子应返回：

```python
ResultAnalysisResult(
    tables=...,
    status="passed | failed | redo_required",
    methods=(...),
    reason="...",
    stale_layers=(...),
    restart_phase="model_design | solve_validate",
)
```

语义如下：

- `passed`：核心结论在声明范围内保持，可以进入绘图和写作；
- `failed`：本轮分析证据不充分或未达到通过标准，保存工作簿但阻断下游；
- `redo_required`：合理变化下核心结论失效，保存工作簿后自动标记下游 stale，并回退模型设计或主求解。

旧项目暂可返回工作表字典，运行器会兼容归一化为 `passed`；新项目不得依赖该兼容路径。

## 4. 自动反馈回路

`redo_required` 必须触发：

```text
写入问题X结果深化分析.xlsx
→ result_analysis_status = redo_required
→ artifacts_stale = true
→ stale: result_analysis_workbook / matlab_script / figure_bundle / framework
→ result_summary_status = stale
→ project.current_phase 回退到 model_design 或 solve_validate
→ 抛出阻断异常
```

模型、参数、约束或数据口径修改后，重新完整求解、通过质量门并重新分析。不得保留旧结果继续绘图或写论文。

## 5. 工作簿

固定输出：

```text
结果数据表/问题X/问题X结果深化分析.xlsx
```

必需表为：

- `分析设计`；
- 至少一个实质分析表；
- `结论稳定性汇总`。

实质分析表按需从参数敏感性、阈值与失效边界、场景压力测试、算法一致性、结构稳健性、异质性分析、误差分解和外样本稳定性中选择。必须保留逐参数、逐场景、逐算法、逐分组或逐重复底层数据。

## 6. 输出

- `result_analysis_plan`；
- `result_analysis_workbook`；
- `result_analysis_report`；
- 通过时的 `validated_results`；
- 更新后的 `evidence_map` 和 `model_paper_framework`。

正文只写实际采用的方法、关键数值、稳定范围、失效边界和证据位置，不机械设置统一章节名。
