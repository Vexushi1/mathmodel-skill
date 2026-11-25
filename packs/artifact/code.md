# Artifact Pack：每问自包含求解代码

按需 `model_comparison / algorithm_comparison` 复用独立 analysis 入口与项目 backend，详见 Module 03B。模型／算法 helper 纳入实际源码闭包；配置与回执绑定冻结比较计划，每个 required 项真实输出专项底层数据，不能只添表或固定数字。可实例化模式见 Python starter 与 MATLAB comparison example；它们不授权用户模型。

每问代码保留在同一个 `问题X求解/` 目录；交付服从 `core/output_contract.yaml` 与 `core/user_execution_contract.yaml`，本 Pack 不复制一套固定目录合同：

- `per_question.solver_scripts` 中项目根后端对应的主入口：按 `core/model_approval_contract.yaml#human_approval` 恢复批准模型，并读取本问所需数据后交付；
- 同一项目后端对应的独立深化入口：按 `core/user_execution_contract.yaml#result_handoff` 核对主结果，且 Analysis Necessity Gate=`required` 时交付。

基础布局是主求解代码、`问题X求解结果.xlsx` 与已选绘图后端的 `qX_plot.py` 或 `qX_plot.m`；Gate=`required` 时再追加结果深化分析代码与 `问题X结果深化分析.xlsx`。因此只有 Gate=`required` 路径才具有两个阶段明确的代码入口；Gate=`not_required` 时仅保留主求解代码。Gate=`required` 的兼容五文件路径中会形成同目录两个真实工作簿（主工作簿 + 03B 工作簿）；该表述仅描述被 Gate 激活的路径，不适用于 Gate=`not_required`。主工作簿核对后冻结主求解脚本，不用深化分析代码覆盖它。Gate=`not_required` 时记录非空理由，不生成 03B 代码/工作簿，也不得把缺少 03B 解释为稳健性或稳定性已验证。

本 Pack 只描述代码交付边界，不重新定义数据事实源。数据读取必须继承 current `preprocessing_decision`，以 `core/global_preprocessing_contract.yaml` 与对应阶段模块为准：

- `not_needed`：主求解以及被激活的深化分析可读取必要原始数据并执行非破坏性审计；
- `question_local`：可读取必要原始数据，并只复现本问数学层已定义的局部变换；
- `project_level`：依赖公共口径的主求解/被激活的深化分析读取 `数据预处理/数据预处理结果.xlsx`，禁止再次直接读取对应共享原始数据。

唯一数值后端取自项目根 `execution.solver_backend`；各阶段 `RUN_CONFIG`、回执、协议与源码 bundle 遵循执行 Authority，记录实际运行事实并与项目策略一致。代码默认自包含，必要 helper 显式纳入依赖绑定。

完整运行配置分别嵌入实际激活阶段的代码并写入对应工作簿，**不生成独立 YAML**、运行说明或校验报告。

代码与结果分别检查：

- **工程质量**：按 `core/code_quality_contract.yaml` 检查代码规模、复杂度及对应语言的工程问题；
- **数值结果**：用户运行后按 `result_handoff` 读取实际工作簿，核对运行配置、可行性、残差、收敛、外样本或题型专项证据。

代码精简不得删除随机种子、目标函数、约束、质量检查、结果输出或复现信息。Gate=`required` 时，深化分析脚本应读取已核对主工作簿和当前允许的数据事实源，不复制完整主求解流程。主求解/深化入口不生成论文结果图；项目选定的 Python/MATLAB 主结果图默认只需同目录主工作簿，只有 Figure Evidence 明确消费真实 03B 证据时才读取条件存在的深化工作簿；必须精确匹配表头，不得重新求解。旧 v6.6.x 单脚本四文件项目与旧 `结果数据表/问题X/` 仅作**只读兼容**。
