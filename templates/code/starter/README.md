# 题型 Starter 使用说明

本目录包含五个薄入口：

- `classification.py`：分类、判别和监督学习；
- `evaluation.py`：综合评价、评分和排序；
- `optimization.py`：显式目标与约束优化；
- `prediction.py`：时间序列或滚动预测；
- `simulation.py`：随机、状态转移或离散事件仿真。

Starter 不再自行定位输出文件、设置随机种子或直接写 Excel。所有公共行为由 `hsk_pipeline.run_pipeline()` 统一执行。

## 使用步骤

1. 将整个 `templates/code/hsk_pipeline/` 复制为项目根目录下的 `hsk_pipeline/`；
2. 选择一个 starter，复制到项目根目录并改名为 `问题一求解.py` 等中文名；
3. 替换 `INPUT_FILE`、`FRAMEWORK_SECTION` 和 `PROBLEM_NAME`；
4. 根据当前 `模型论文框架.md` 修改 objective、structures 和 capabilities；
5. 实现预处理、特征/参数构造、求解、验证和框架同步钩子；
6. 运行脚本并检查两类标准工作簿；
7. 正式交付前执行 results scope 的 `project_sync`。

禁止把多个 starter 拼接到同一脚本，也禁止保留未使用的题型钩子。题型变化时应替换当前脚本内容，而不是并列保存旧实现。
