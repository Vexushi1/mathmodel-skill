# 题型 Starter 使用说明 v6.5.1

本目录包含五个**主求解代码入口**：

- `classification.py`：分类、判别和监督学习；
- `evaluation.py`：综合评价、评分和排序；
- `optimization.py`：显式目标与约束优化；
- `prediction.py`：时间序列或滚动预测；
- `simulation.py`：随机、状态转移或离散事件仿真。

Starter 只调用 `run_primary_pipeline()`，不得在同一脚本中继续执行结果深化分析。公共写表、质量门和状态记录由 `hsk_pipeline` 提供；赛题代码由用户本地完整运行，助手不得执行。

## 使用步骤

1. 将整个 `templates/code/hsk_pipeline/` 复制为项目根目录下的 `hsk_pipeline/`；
2. 选择一个 starter，复制到项目根目录并改名为 `问题一求解.py` 等中文名；
3. 替换 `INPUT_FILE`、`FRAMEWORK_SECTION` 和 `PROBLEM_NAME`；
4. 根据当前 `模型论文框架.md` 修改 objective、structures 和 capabilities；
5. 实现数据处理、模型求解、主结果质量门、`运行配置` 工作表和主结果框架同步；
6. 生成 `问题X完整运行配置.yaml` 与 `问题X本地运行说明.md`，执行 `validate_code_delivery.py`；
7. 用户本地运行 `问题X求解.py`，返回 `问题X求解结果.xlsx`；
8. `validate_user_execution.py` 验收通过后，另行生成 `问题X结果深化分析.py`；
9. 用户运行深化脚本并返回深化工作簿；两类工作簿均 accepted 后才进入 results、MATLAB 和 LaTeX。

正式主代码交付使用 `--delivery-scope code`。禁止把多个 starter 拼接到同一脚本，也禁止在主求解 starter 中保留未使用的结果深化钩子。
