# HSK Python 求解管线 v6.3.4

本目录是所有 Python starter 的唯一执行底座。`main_pipeline.py` 负责随机种子、数据审计、求解主链、三轴工作簿校验、结果保存和框架同步；`templates/code/starter/` 只填写题型配置与题目专属函数。

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

从 `templates/code/starter/` 选择最接近题型的脚本，复制到项目根目录并改为中文文件名。不要把 starter 和 `hsk_pipeline/` 拆散，也不要再复制旧版 `result_io.py` 到项目根目录。

## 无导入副作用

导入 starter 或 `hsk_pipeline` 时不得：

- 创建 `结果数据表/`；
- 设置随机种子；
- 读取附件；
- 执行求解；
- 写入 Excel 或框架。

所有副作用统一从 starter 的 `main()` 调用 `run_pipeline()` 后开始。

## 运行前必须填写

1. `INPUT_FILE`、`FRAMEWORK_SECTION`、`PROBLEM_NAME`；
2. 一个 `objective`；
3. 0--3 个真正改变模型、验证或交付的 `structures`；
4. 完整顶层 `capabilities`；
5. 数据预处理、特征/参数构造、求解、验证和框架同步函数。

显式约束或可行性 capability 为 true 时，必须返回“约束违反检查”；外样本、不确定性、泄漏、校准或可识别性 capability 为 true 时，必须输出对应工作表。

## 统一执行链

```text
build_config
→ config.validate
→ set_random_seed
→ load_data
→ preprocess_data
→ build_features
→ solve_model
→ check_constraints
→ validate_model
→ save_outputs
→ sync_framework
```

`save_outputs()` 始终把 `objective`、`structures`、`capabilities` 传给 `write_workbook()`，禁止绕过 `core/workbook_schema.yaml`。

## 固定输出

```text
项目根目录/
├─ 模型论文框架.md
└─ 结果数据表/问题一/
   ├─ 问题一求解结果.xlsx
   └─ 问题一敏感性与鲁棒性结果.xlsx
```

Python 不生成正式论文图。MATLAB 阶段再将 `q1_plot.m` 放入同一问题目录，并读取上述真实工作簿绘图。

正式结果交付前执行：

```bash
python scripts/sync_project.py <project_root> \
  --write --strict --delivery-scope results
```
