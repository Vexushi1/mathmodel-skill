# Artifact Pack：每问自包含求解代码

每问默认维护两个阶段明确的 Python 文件：

- `问题X求解/问题X求解.py`：主求解程序；
- `问题X求解/问题X结果深化分析.py`：主工作簿验收后的独立深化分析程序。

最终它们与 `问题X求解结果.xlsx`、`问题X结果深化分析.xlsx` 和 `qX_plot.m` 同目录。主工作簿 accepted 后冻结主求解脚本，不用深化分析代码覆盖它。

本 Pack 只描述代码交付边界，不重新定义数据事实源。数据读取必须继承 current `preprocessing_decision`，以 `core/global_preprocessing_contract.yaml` 与对应阶段模块为准：

- `not_needed`：主求解/深化分析可读取必要原始数据并执行非破坏性审计；
- `question_local`：可读取必要原始数据，并只复现本问数学层已定义的局部变换；
- `project_level`：依赖公共口径的主求解/深化分析读取 `数据预处理/数据预处理结果.xlsx`，禁止再次直接读取对应共享原始数据。

完整运行配置分别嵌入对应阶段 Python 并写入对应工作簿，**不生成独立 YAML**、运行说明或校验报告。

两个 Python 都必须通过两类互补质量门：

- **工程质量门**：`core/code_quality_contract.yaml` + `scripts/validate_code_delivery.py`，检查规模、函数、参数、复杂度、禁用绘图库、裸 `except`、调试断点、通配 import、未使用 import 和 `print`；
- **数值结果质量门**：用户运行后由工作簿 Schema 与 `validate_user_execution.py` 检查运行配置、对应阶段代码哈希、可行性、残差、收敛、外样本或题型专项证据。

代码精简不得删除随机种子、目标函数、约束、质量检查、结果输出或复现信息。深化分析脚本应读取已验收主工作簿和当前允许的数据事实源，不复制完整主求解流程。Python 不生成论文结果图；MATLAB 只读已验收的真实工作簿及 `modules/04_figure_evidence.md` 明确允许的必要事实源，必须精确匹配表头，不得重新求解。旧 v6.6.x 单脚本四文件项目与旧 `结果数据表/问题X/` 仅作**只读兼容**。
