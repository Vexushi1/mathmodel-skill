# Module 03A：主求解代码交付

本模块在 `问题X求解/` 中生成 `问题X求解.py`。助手只生成和静态检查，不运行赛题代码。

若项目根目录已有 current `模型论文框架.md`，正式生成本问代码前必须先读取“当前有效口径”、本问“当前模型口径/求解与验证方案”以及必要前问依赖，用它恢复当前模型语义；不得仅凭聊天记忆重建变量、参数、目标或约束。具体输入数值和已验收结果仍回到当前数据事实源/标准工作簿核验。

进入本模块前，当前小问必须先通过 `scripts/validate_semantic_governance.py`：

- `problem_contract_status=frozen`；
- `semantic_closure_status=passed`；
- `complexity_sanity_status=passed`；
- 当前 `semantic_revision` 已被语义治理门接受；
- `preprocessing_decision` 已锁定；
- 若已有历史结果且模型语义发生变化，本问及依赖后问已按 `depends_on` 正确标记 stale。

## 数据事实源分流

正式生成主求解代码前必须按 `preprocessing_decision` 选择唯一数据入口：

### `not_needed`

- 不生成、不要求 `数据预处理/`；
- `问题X求解.py` 允许直接读取题目原始附件；
- 仍必须保留字段、维度、单位、NaN/Inf、主键、索引等非破坏性检查；
- 不得为了形式完整而额外插值、滤波、平滑、标准化或删除异常候选。

### `question_local`

- 不生成全局 `数据预处理/`；
- 主求解允许读取原始附件；
- 仅允许执行本问数学层已经定义的局部变换，例如对数、标准化、滞后、滑动窗口或专属派生特征；
- 局部变换不得静默升级为其他小问必须复用的“统一清洗”。

### `project_level`

必须先完成项目级统一数据预处理：

- `数据预处理/数据预处理.py` 已生成并静态检查；
- 用户已本地 full-fidelity 运行；
- `数据预处理/数据预处理结果.xlsx` 的 `预处理质量门` 已通过；
- 本问数据依赖已统一指向该工作簿；
- 本问主求解脚本不得再次直接读取对应共享原始 CSV/XLSX/TXT 等数据源。

只有 `project_level` 状态下，上述统一工作簿是硬前置。`not_needed` 或 `question_local` 项目不得因缺少统一预处理工作簿而阻塞主求解。

任何一项真正适用的前置条件不满足，都不得生成正式主求解代码。尤其禁止出现“模型尚未闭环，先写 Python 看结果再决定题意”，也禁止在 `project_level` 已冻结后各问重新自行清洗。

```text
题意口径冻结
→ 题面—数学—代码语义闭环
→ 复杂度合理性复审
→ preprocessing_decision
   ├─ not_needed     → 原始数据
   ├─ question_local → 原始数据 + 本问局部变换
   └─ project_level  → Module 03P → 统一工作簿质量门
→ semantic governance gate
→ 生成问题X求解.py
→ validate_code_delivery.py：执行配置 + 代码工程质量门
→ 用户本地full_fidelity运行
→ 问题X求解结果.xlsx
→ validate_user_execution.py验收运行配置、哈希与主结果质量门
→ accepted后冻结问题X求解.py
```

脚本必须保留与当前数据事实源对应的读取与字段检查、模型与求解器、目标/约束或题型核心检查、停止条件、约束/残差/收敛或外样本证据、结果整理、中文工作簿输出和主入口。代码规模、函数规模、参数数量、复杂度与反模式以 `core/code_quality_contract.yaml` 为唯一事实源。

代码实现必须服从 Module 02 的三层语义闭环：核心 Python 变量、函数、目标项、约束、阈值、预处理和输出都必须能够回溯到当前数学层；不得在代码阶段静默新增模型语义。

- `project_level`：不得重复项目级去缺失、异常处理、单位换算、统一滤波、统一重采样或坐标修正；
- `question_local`：只允许当前小问有数学来源的局部变换；
- `not_needed`：默认保持原始数据，不为“规范化流程”虚构处理步骤。

若实现过程中发现必须新增核心变量、修改目标函数/约束、改变 `preprocessing_decision`、公共数据处理或算法语义，应停止代码交付，递增 `semantic_revision`，更新 `semantic_change_categories`，必要时回退 Module 03P 或 Module 02，重新闭环并运行语义治理门。

完整运行配置嵌入 `FULL_FIDELITY_CONFIG` 并写入主工作簿，不生成独立 YAML、运行说明或校验报告。主工作簿 accepted 后不得为了结果深化分析覆盖更新 `问题X求解.py`；深化分析进入 Module 03B，并生成独立 `问题X结果深化分析.py`。若后续发现主模型必须修改，应显式回退 Module 02/本模块，先传播 stale，再重新验收主结果。
