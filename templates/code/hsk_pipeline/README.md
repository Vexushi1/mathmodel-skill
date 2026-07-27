# HSK Python 求解模板 v6.3.1

具体项目中，赛题文件、附件数据表、项目根目录 `模型论文框架.md` 和各问 Python 脚本直接放在同一项目根目录。将模板改为中文名，如 `问题一求解.py`；不要复制到 `Python求解/` 子目录。

模板导入时不创建目录、不设置随机种子、不执行求解；所有运行副作用只发生在 `main()`。

## 路径规则

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULT_DIR = ROOT / "结果数据表" / "问题一"
FRAMEWORK = ROOT / "模型论文框架.md"
```

- 题目与附件从 `ROOT` 读取；
- 当前模型、参数、约束和验证计划从 `FRAMEWORK` 核对；
- 两类工作簿写入 `RESULT_DIR`；
- 不依赖当前工作目录和绝对路径；
- 不创建 `问题一结果数据/` 重复层级。

## 运行前必须填写

在 `build_config()` 中逐问填写：

- `problem_name`；
- 一个 `objective`；
- 0--3 个真正改变模型、验证或交付的 `structures`；
- 完整的顶层 `capabilities`；
- 随机种子；
- 当前框架章节与结果摘要状态。

`objective` 为空、结构标签超限或 capability 缺失会直接报错。显式约束或可行性能力为 true 时，必须实现约束违反检查；外样本、不确定性、泄漏、校准或可识别性能力为 true 时，必须输出对应工作表。

旧 `problem_types` 只用于兼容历史项目，不作为新模板配置项。

## 工作簿写入

```python
write_workbook(
    solution_path,
    solution_tables,
    workbook_kind="solution",
    objective=config.objective,
    structures=config.structures,
    capabilities=config.capabilities,
)
```

工作簿校验顺序为：通用必需表 → objective 专项 → structure 专项 → capability 强制表 → 字段、主键、非有限值和判定一致性。

## 固定输出

```text
项目根目录/
├─ 模型论文框架.md
└─ 结果数据表/
   └─ 问题一/
      ├─ 问题一求解结果.xlsx
      ├─ 问题一敏感性与鲁棒性结果.xlsx
      ├─ q1_plot.m
      └─ 图表/
```

Python 只写入前两份工作簿；`q1_plot.m` 由绘图阶段放入同一问题目录。求解工作簿承载核心指标、三轴专项结果和 capability 对应检查；敏感性与鲁棒性工作簿保留逐参数、逐扰动或逐重复数据。两类工作簿由 `result_io.py` 校验后写入。

工作簿通过校验后，必须完整替换 `模型论文框架.md` 中该问的当前模型口径和结果摘要，不并列旧版与新版。

## 正式结果交付

工作簿和框架同步完成后执行：

```bash
python scripts/sync_project.py <project_root> \
  --write --strict --delivery-scope results
```

同步器校验两类工作簿，计算 data、model 和 workbook 哈希，更新框架最终哈希并生成 `sync_report.yaml`。它不会自动把验证状态提升为 passed。

Python 不生成正式论文图。完整链路为：项目根目录 Python 求解 → 两类工作簿 → 框架结果摘要 → `project_sync` results gate → 同目录 `q{x}_plot.m` 读取真实表头 → 正式图 → `project_sync` figures gate。
