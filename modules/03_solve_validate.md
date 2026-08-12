# Module 03A：主求解代码交付

本模块在 `问题X求解/` 中生成 `问题X求解.py`。助手只生成和静态检查，不运行赛题代码。

进入本模块前，当前小问必须先通过 `scripts/validate_semantic_governance.py`：

- `problem_contract_status=frozen`；
- `semantic_closure_status=passed`；
- `complexity_sanity_status=passed`；
- 当前 `semantic_revision` 已被语义治理门接受；
- 若已有历史结果且模型语义发生变化，本问及依赖后问已按 `depends_on` 正确标记 stale。

若项目满足 `core/global_preprocessing_contract.yaml` 的启用条件，还必须先完成项目级统一数据预处理：

- `数据预处理/数据预处理.py` 已生成并静态检查；
- 用户已本地 full-fidelity 运行；
- `数据预处理/数据预处理结果.xlsx` 的 `预处理质量门` 已通过；
- 本问数据依赖已统一指向该工作簿；
- 本问主求解脚本不得再次直接读取共享原始 CSV/XLSX/TXT 等数据源。

任何一项不满足，都不得生成正式主求解代码。尤其禁止出现“模型尚未闭环，先写 Python 看结果再决定题意”，也禁止“统一预处理未验收，各问先各自读取原始数据并自行清洗”的反向流程。

```text
题意口径冻结
→ 题面—数学—代码语义闭环
→ 复杂度合理性复审
→ semantic governance gate
→ 锁定模型
→ 项目级统一数据预处理（共享数据项目）
→ 预处理质量门
→ 生成问题X求解.py
→ validate_code_delivery.py：执行配置 + 代码工程质量门
→ 用户本地full_fidelity运行
→ 问题X求解结果.xlsx
→ validate_user_execution.py验收运行配置、哈希与主结果质量门
→ accepted后冻结问题X求解.py
```

脚本必须保留统一预处理工作簿读取与字段检查、模型与求解器、目标/约束或题型核心检查、停止条件、约束/残差/收敛或外样本证据、结果整理、中文工作簿输出和主入口。若未启用全局预处理，才允许按当前题意直接读取原始数据。代码规模、函数规模、参数数量、复杂度与反模式以 `core/code_quality_contract.yaml` 为唯一事实源。

代码实现必须服从 Module 02 的三层语义闭环：核心 Python 变量、函数、目标项、约束、阈值、预处理和输出都必须能够回溯到当前数学层；不得在代码阶段静默新增模型语义。统一预处理已经完成的项目级去缺失、异常处理、单位换算、统一滤波、统一重采样或坐标修正不得在小问脚本内重复执行。小问专属派生特征允许从统一工作簿计算，但必须在数学层有来源。

若实现过程中发现必须新增核心变量、修改目标函数/约束、改变统一数据处理或算法语义，应停止代码交付，递增 `semantic_revision`，更新 `semantic_change_categories`，必要时回退 Module 03P 或 Module 02，重新闭环并运行语义治理门。

完整运行配置嵌入 `FULL_FIDELITY_CONFIG` 并写入主工作簿，不生成独立 YAML、运行说明或校验报告。主工作簿 accepted 后不得为了结果深化分析覆盖更新 `问题X求解.py`；深化分析进入 Module 03B，并生成独立 `问题X结果深化分析.py`。若后续发现主模型必须修改，应显式回退 Module 02/本模块，先传播 stale，再重新验收主结果。
