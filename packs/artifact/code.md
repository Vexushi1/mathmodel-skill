# Artifact Pack：每问自包含求解代码

每问默认只有一个持续更新的 `问题X求解/问题X求解.py`，它是本问的**唯一Python文件**，并最终与 `问题X求解结果.xlsx`、`问题X结果深化分析.xlsx` 和 `qX_plot.m` 同目录。主工作簿验收后**覆盖更新同一文件**加入结果深化分析，不创建第二个 Python 文件。

完整运行配置嵌入 Python 并写入工作簿，**不生成独立 YAML**、运行说明或校验报告。

代码必须通过两类互补质量门：

- **工程质量门**：`core/code_quality_contract.yaml` + `scripts/validate_code_delivery.py`，检查规模、函数、参数、复杂度、禁用绘图库、裸 `except`、调试断点、通配 import、未使用 import 和 `print`；
- **数值结果质量门**：用户运行后由工作簿 Schema 与 `validate_user_execution.py` 检查运行配置、哈希、可行性、残差、收敛、外样本或题型专项证据。

代码精简不得删除随机种子、目标函数、约束、质量检查、结果输出或复现信息。Python不生成论文结果图；MATLAB只读**同目录两个真实工作簿**，必须**精确匹配表头**，不得重新求解。旧 `结果数据表/问题X/` 与旧工作簿名仅作**只读兼容**。
