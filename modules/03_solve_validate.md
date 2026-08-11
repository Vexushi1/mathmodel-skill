# Module 03A：主求解代码交付

本模块在 `问题X求解/` 中生成 `问题X求解.py`。助手只生成和静态检查，不运行赛题代码。

进入本模块前，当前小问必须先通过 `scripts/validate_semantic_governance.py`：

- `problem_contract_status=frozen`；
- `semantic_closure_status=passed`；
- `complexity_sanity_status=passed`；
- 当前 `semantic_revision` 已被语义治理门接受；
- 若已有历史结果且模型语义发生变化，本问及依赖后问已按 `depends_on` 正确标记 stale。

任何一项不满足，都不得生成正式主求解代码。尤其禁止出现“模型尚未闭环，先写 Python 看结果再决定题意”的反向流程。

```text
题意口径冻结
→ 题面—数学—代码语义闭环
→ 复杂度合理性复审
→ semantic governance gate
→ 锁定模型
→ 生成问题X求解.py
→ validate_code_delivery.py：执行配置 + 代码工程质量门
→ 用户本地full_fidelity运行
→ 问题X求解结果.xlsx
→ validate_user_execution.py验收运行配置、哈希与主结果质量门
→ accepted后冻结问题X求解.py
```

脚本必须保留数据读取与审计、随机种子、模型与求解器、目标/约束或题型核心检查、停止条件、约束/残差/收敛或外样本证据、结果整理、中文工作簿输出和主入口。代码规模、函数规模、参数数量、复杂度与反模式以 `core/code_quality_contract.yaml` 为唯一事实源。

代码实现必须服从 Module 02 的三层语义闭环：核心 Python 变量、函数、目标项、约束、阈值、预处理和输出都必须能够回溯到当前数学层；不得在代码阶段静默新增模型语义。若实现过程中发现必须新增核心变量、修改目标函数/约束、改变数据处理或算法语义，应停止代码交付，递增 `semantic_revision`，更新 `semantic_change_categories`，回到 Module 02 重新闭环并运行语义治理门。

完整运行配置嵌入 `FULL_FIDELITY_CONFIG` 并写入主工作簿，不生成独立 YAML、运行说明或校验报告。主工作簿 accepted 后不得为了结果深化分析覆盖更新 `问题X求解.py`；深化分析进入 Module 03B，并生成独立 `问题X结果深化分析.py`。若后续发现主模型必须修改，应显式回退 Module 02/本模块，先传播 stale，再重新验收主结果。
