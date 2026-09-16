# Artifact Pack：每问自包含求解代码

每问代码交付服从 `core/output_contract.yaml` 与 `core/user_execution_contract.yaml`，本 Pack 不复制一套固定目录合同：

- `问题X求解/问题X求解.py`：主求解程序，按 applicable approval/data gates 交付；
- `问题X求解/问题X结果深化分析.py`：仅在主工作簿 accepted 且 Analysis Necessity Gate=`required` 时交付的独立深化分析程序。

基础布局是主求解 Python、`问题X求解结果.xlsx` 与 `qX_plot.m`；Gate=`required` 时再追加结果深化分析 Python 与 `问题X结果深化分析.xlsx`。主工作簿 accepted 后冻结主求解脚本，不用深化分析代码覆盖它。Gate=`not_required` 时记录非空理由，不生成 03B 代码/工作簿，也不得把缺少 03B 解释为稳健性或稳定性已验证。

本 Pack 只描述代码交付边界，不重新定义数据事实源。数据读取必须继承 current `preprocessing_decision`，以 `core/global_preprocessing_contract.yaml` 与对应阶段模块为准：

- `not_needed`：主求解以及被激活的深化分析可读取必要原始数据并执行非破坏性审计；
- `question_local`：可读取必要原始数据，并只复现本问数学层已定义的局部变换；
- `project_level`：依赖公共口径的主求解/被激活的深化分析读取 `数据预处理/数据预处理结果.xlsx`，禁止再次直接读取对应共享原始数据。

完整运行配置分别嵌入实际激活阶段的 Python 并写入对应工作簿，**不生成独立 YAML**、运行说明或校验报告。

实际交付的 Python 都必须通过两类互补质量门：

- **工程质量门**：`core/code_quality_contract.yaml` + `scripts/validate_code_delivery.py`，检查规模、函数、参数、复杂度、禁用绘图库、裸 `except`、调试断点、通配 import、未使用 import 和 `print`；
- **数值结果质量门**：用户运行后由工作簿 Schema 与 `validate_user_execution.py` 检查运行配置、对应阶段代码哈希、可行性、残差、收敛、外样本或题型专项证据。

代码精简不得删除随机种子、目标函数、约束、质量检查、结果输出或复现信息。Gate=`required` 时，深化分析脚本应读取已验收主工作簿和当前允许的数据事实源，不复制完整主求解流程。Python 不生成论文结果图；MATLAB 主结果图默认只需同目录主工作簿，只有 Figure Evidence 明确消费真实 03B 证据时才读取条件存在的深化工作簿；必须精确匹配表头，不得重新求解。旧 v6.6.x 单脚本四文件项目与旧 `结果数据表/问题X/` 仅作**只读兼容**。
