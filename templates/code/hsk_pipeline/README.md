# HSK Python 求解与结果深化管线 v6.4.0

本目录是所有 Python starter 的唯一执行底座。`main_pipeline.py` 提供两个权威阶段：

- `run_primary_pipeline()`：数据审计、完整主求解、主结果质量门、求解工作簿和主结果框架同步；
- `run_result_analysis_pipeline()`：读取已通过质量门的主结果，执行题目专属结果深化分析并同步分析结论。

`run_pipeline()` 仅按顺序编排上述两个阶段，不重新合并职责。

## 推荐复制结构

```text
项目根目录/
├─ hsk_pipeline/
│  ├─ __init__.py
│  ├─ main_pipeline.py
│  ├─ result_io.py
│  └─ workbook_validation.py
├─ 问题一求解.py
├─ 模型论文框架.md
└─ 赛题附件.xlsx
```

从 `templates/code/starter/` 选择最接近题型的脚本，复制到项目根目录并改为中文文件名。求解与结果深化分析可以由同一脚本顺序执行，也可以拆成两个中文脚本，但质量门和分析职责必须保持独立。

## 无导入副作用

导入 starter 或 `hsk_pipeline` 时不得：

- 创建 `结果数据表/`；
- 设置随机种子；
- 读取附件；
- 执行求解或分析；
- 写入 Excel 或框架。

所有副作用从 `main()` 调用执行函数后开始。

## 主求解阶段

```text
config.validate
→ set_random_seed
→ load_data
→ preprocess_data
→ build_features
→ solve_model
→ check_constraints
→ evaluate_primary_quality
→ assert_primary_quality
→ 写入问题X求解结果.xlsx
→ sync_primary_framework
```

`evaluate_primary_quality()` 返回非空 DataFrame，至少包含：

```text
检查项 | 是否通过 | 证据
```

报告写入 `主结果质量门` 工作表。任何检查未通过时，管线立即停止，不创建结果深化分析工作簿。

主结果质量门按题型覆盖：数据口径、求解器状态、停止条件、约束或残差、数值收敛、基础外样本精度、泄漏、校准、区间或可识别性。它不允许因模块分离而删除原来必要的精度检查。

## 结果深化分析阶段

```text
读取 PrimarySolveResult
→ 根据风险选择分析方法
→ analyze_results
→ 校验分析设计与实质分析表
→ 写入问题X结果深化分析.xlsx
→ sync_analysis_framework
```

`analyze_results()` 必须返回：

- `分析设计`；
- 至少一个实质分析表；
- `结论稳定性汇总`。

实质分析可以是参数敏感性、阈值与失效边界、场景压力测试、算法一致性、结构稳健性、异质性分析、误差分解或外样本稳定性。方法由本题风险决定，不统一做参数扰动。

若深化分析要求回退重算，应在项目状态中设置 `result_analysis_status: redo_required`、标记下游 stale，并停止绘图和写作。

## 固定输出

```text
结果数据表/问题一/
├─ 问题一求解结果.xlsx
└─ 问题一结果深化分析.xlsx
```

旧 `问题一敏感性与鲁棒性结果.xlsx` 只作历史读取兼容。

Python 不生成正式论文图。MATLAB 阶段将 `q1_plot.m` 放入同一问题目录，读取上述真实工作簿绘图。

正式结果交付前执行：

```bash
python scripts/sync_project.py <project_root> \
  --write --strict --delivery-scope results
```
