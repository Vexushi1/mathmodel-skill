# Module 03A：主求解代码交付

本模块在 `问题X求解/` 中生成 `问题X求解.py`。助手只生成和静态检查，不运行赛题代码。

若项目根目录已有 current `模型论文框架.md`，正式生成本问代码前必须先读取“当前有效口径”、本问“当前模型口径/求解与验证方案/模型挑战与人工锁模”以及必要前问依赖，用它恢复当前模型语义；不得仅凭聊天记忆重建变量、参数、目标或约束。具体输入数值和已验收结果仍回到当前数据事实源/标准工作簿核验。

进入本模块前，当前小问必须依次通过 `scripts/validate_semantic_governance.py` 与 `scripts/validate_model_approval.py`。前者负责当前题意/语义/复杂度与 stale 一致性，后者是 Challenge/Human Approval 的唯一字段级运行门；具体批准状态、revision/hash 绑定与失效条件只服从 `core/model_approval_contract.yaml`，本模块不复制第二套检查清单。

任一 gate 未通过都不得生成正式主求解代码；Model Approval 未通过时返回 Module 02，并停在 `awaiting_model_approval`。

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

- 当前模型已通过 Model Challenge 与 Human Approval；
- `数据预处理/数据预处理.py` 已生成并静态检查；
- 用户已本地 full-fidelity 运行；
- `数据预处理/数据预处理结果.xlsx` 的 `预处理质量门` 已通过；
- 本问数据依赖已统一指向该工作簿；
- 本问主求解脚本不得再次直接读取对应共享原始 CSV/XLSX/TXT 等数据源。

只有 `project_level` 状态下，上述统一工作簿是硬前置。`not_needed` 或 `question_local` 项目不得因缺少统一预处理工作簿而阻塞主求解。

任何一项真正适用的前置条件不满足，都不得生成正式主求解代码。尤其禁止出现“模型尚未闭环，先写 Python 看结果再决定题意”，也禁止在 `project_level` 已冻结后各问重新自行清洗。

## Primary Evidence Capture：主求解必须保留当前运行的高价值状态证据

主求解不能只输出最终答案或几个汇总指标。生成 `问题X求解.py` 前，必须结合当前 locked model、三轴分类、Formula/Algorithm Trace 与题面输出要求，先列出本次主计算**自然产生且对解释模型、科研绘图、数值验证、复现或避免昂贵重算有价值**的 Evidence Capture 项，再把这些项映射到现有工作簿表结构。

核心原则：

> **保存当前这一遍主计算已经真实产生的状态、过程和结构，不为绘图另造一个“替代世界”。**

### 允许并优先保留的 current-run evidence

按题型实际存在时优先保留：

- 决策变量、状态变量、控制量和目标函数分项；
- 逐对象、逐时刻、逐区域、逐节点、逐边、逐网格的状态；
- 路径、流量、覆盖、资源占用、作业起止和调度状态；
- 当前解的约束实际值、违反量、裕量、active/binding 状态和最坏位置；
- 当前算法运行过程中本来已经生成的候选可行解、Pareto candidate、当前最优解演化；
- 当前算法自然产生的 objective、gap、residual、feasibility、iteration/sample trace；
- 预测/分类任务中本次主计算已经生成的逐样本真实值、预测值/标签、概率、残差、合法区间、样本分组、时间/空间键；
- 机理/几何问题中本次主计算已经生成的轨迹、位置、距离、角度、临界事件和边界状态；
- 一旦丢失就需要重新运行昂贵主模型才能恢复的 current-run 中间状态，但不保存无论文/验证/复现价值的 debug 噪声。

### 工作簿映射原则

不建立“所有问题都必须有几十张 Sheet”的固定模板。优先复用 `core/workbook_schema.yaml` 已登记的 capability-driven 表，例如：

- `明细结果` / `状态明细`：逐对象、状态与通用细粒度结果；
- `逐时刻结果` / `仿真明细`：动态与仿真轨迹；
- `节点结果` / `边结果` / `路径或流结果`：空间、网络与流；
- `预测明细` / `预测或分类结果` / `误差指标`：逐样本预测与误差；
- `决策变量明细` / `方案对比` / `Pareto结果`：优化决策、候选方案与多目标结果；
- `约束违反检查` / `均衡残差` / `守恒残差`：约束与机制残差；
- `收敛诊断` / `离散精度`：当前主数值过程证据。

如果现有表结构不足以无歧义保存本题的真实状态，优先在题目专属输出中使用语义清楚的已登记通用明细表与真实字段，而不是把底层状态压缩成一个摘要数字；确需新增跨项目通用工作表时才修改工作簿 Authority，并必须保持旧工作簿兼容。

### 03A / 03B 硬边界

判定一份数据是否可在 03A 产生，不按计算耗时判断，而按下面的问题：

> **为了得到它，是否需要改变当前主计算的输入、参数、现实场景、seed、初值、算法、模型结构或验证窗口，然后重新执行新的计算世界？**

- **否**：属于 current-run capture，可在 03A 保存；
- **是**：属于 alternative-world analysis，必须留在 Module 03B。

因此，即使一次参数扫描只需数秒，也不能因为“便宜”塞入 03A；反之，主算法运行数小时自然产生的候选解池、状态轨迹和收敛 trace，如果保存不会改变算法语义，就应尽量在本次运行直接落盘。

主求解可以为后续 03B 保存可复现且不改变主结果语义的 warm-start 材料、候选解池或固定中间矩阵，但不得在 03A 中预先执行敏感性、压力场景、替代算法/结构、多 seed 结论稳定性或阈值搜索。

这一 Evidence Capture 只增加**结果保留粒度**，不改变 `core/numerical_verification_contract.yaml` 的 Primary Quality Specification，也不把绘图需求升级为主质量门的 blocking 条件。

## 主求解质量检查：只判断当前主计算是否可接受

主求解质量检查的唯一数值规则 Authority 为 `core/numerical_verification_contract.yaml`。它只回答：**在当前 locked model 与声明的 numerical method 下，本次主计算是否具有足够的内在数值有效性，可以成为 accepted solution workbook。**

因此 `问题X求解.py` 只实现 Module 02 已登记的 Primary Quality Specification（PQS）中真正适用的最低检查，例如当前解的约束违反、等式/均衡/守恒残差、必要的离散精度、必要的迭代/仿真收敛、当前求解器的 bound/gap/termination 证据，以及 capability 明确要求的主预测外样本、泄漏、校准、可识别性或最低不确定性精度。

**不得把参数敏感性、现实参数扰动、阈值/失效边界扩展搜索、场景压力测试、替代算法比较、替代结构/模型比较、多随机种子或多初值稳健性、异质性、误差分解、广义外样本稳定性等结果深化分析内容写入主求解质量门。** 这些内容只能在主工作簿 accepted 后进入 Module 03B。若某一主算法按数学定义本身需要多起点/多随机种子才能构成一次完整求解，这些运行可以作为主算法内部步骤，但不得据此在 03A 中生成“跨算法稳健性”或“结论稳定性”分析。

容易混淆的边界统一如下：

- 数值步长、网格、分辨率是否足以支撑**当前答案** → 主求解质量检查；物理/模型参数变化后结论是否改变 → Module 03B；
- Monte Carlo 样本量是否足以让**当前估计**达到声明精度 → 主求解质量检查；多 seed 下策略/排名是否稳定 → Module 03B；
- 当前精确/松弛求解器的 stop status、bound、gap → 主求解质量检查；MILP 与 ALNS/GA/greedy 等替代算法比较 → Module 03B；
- 预测主结果所必需的一次合法 OOS 验证 → 主求解质量检查；跨窗口、跨年份、跨地区或迁移场景稳定性 → Module 03B。

v7.14 新生成的严格主质量轨迹应在 `运行配置` 中写入 `primary_quality_protocol_version=1.0.0`，并在 `主结果质量门` 中使用 `Verification ID / 判定关系 / 阈值或容差 / 实际值 / 证据工作表 / 阈值来源` 追溯到底层证据。`离散精度` 与 `收敛诊断` 若由机器重算主判据，应使用 `用于主判定` 标记真正决定当前主结果是否可接受的证据行，避免把探索性粗网格或过程记录误当最终门槛。

返回工作簿时 `scripts/validate_user_execution.py` 先核验执行所有权、full-fidelity 配置和代码/数据哈希，再调用 `scripts/validate_numerical_evidence.py` 独立复核适用主数值证据；工作簿自行写出的“是否通过”不能替代机器可重算的证据一致性。v7.13 历史工作簿保持只读兼容；旧项目重新进入当前主求解时应按 v7.14 轨迹生成本问新工作簿。

```text
题意口径冻结
→ 非破坏性数据审计 + 模型路线/输入需求比较
→ preprocessing_decision
→ 题面—数学—代码语义闭环
→ Primary Quality Specification（只含当前主计算最低数值有效性）
→ 复杂度合理性复审
→ Independent Model Challenge
→ Human Model Approval（绑定 current semantic revision/hash）
→ semantic governance gate
→ model approval gate
→ 按 preprocessing_decision 分流
   ├─ not_needed     → 原始数据
   ├─ question_local → 原始数据 + 本问局部变换
   └─ project_level  → Module 03P → 统一工作簿质量门
→ 生成问题X求解.py前锁定 Primary Evidence Capture 项
→ 用户一次主运行同时保存最终答案 + 真实状态/过程/结构证据
→ validate_code_delivery.py：执行配置 + 代码工程质量门
→ 用户本地full_fidelity运行
→ 问题X求解结果.xlsx
→ validate_user_execution.py：运行配置/哈希 + 主结果质量门 + numerical evidence独立复核
→ accepted后冻结问题X求解.py
→ 才允许建立result_analysis_plan并进入Module 03B
```

脚本必须保留与当前数据事实源对应的读取与字段检查、模型与求解器、目标/约束或题型核心检查、停止条件、PQS 要求的约束/残差/离散/收敛/主预测有效性证据、**本次运行真实产生的高价值状态/过程证据**、结果整理、中文工作簿输出和主入口。代码规模、函数规模、参数数量、复杂度与反模式以 `core/code_quality_contract.yaml` 为唯一事实源。

代码实现必须服从 Module 02 的三层语义闭环：核心 Python 变量、函数、目标项、约束、阈值、预处理和输出都必须能够回溯到当前数学层；不得在代码阶段静默新增模型语义。

- `project_level`：不得重复项目级去缺失、异常处理、单位换算、统一滤波、统一重采样或坐标修正；
- `question_local`：只允许当前小问有数学来源的局部变换；
- `not_needed`：默认保持原始数据，不为“规范化流程”虚构处理步骤。

若实现过程中发现必须新增核心变量、修改目标函数/约束、改变 `preprocessing_decision`、公共数据处理或算法语义，应停止代码交付，递增 `semantic_revision`，更新 `semantic_change_categories`，把旧 `model_challenge_status`、`human_model_approval_status` 和 `locked_model_spec` 标记 stale，必要时回退 Module 03P 或 Module 02，重新闭环、重新 Challenge、重新取得用户 Approval，并再次运行两个治理门。

完整运行配置嵌入 `FULL_FIDELITY_CONFIG` 并写入主工作簿，不生成独立 YAML、运行说明或校验报告。主工作簿 accepted 后不得为了结果深化分析覆盖更新 `问题X求解.py`；深化分析进入 Module 03B，并生成独立 `问题X结果深化分析.py`。若后续发现主模型必须修改，应显式回退 Module 02/本模块，先传播 stale，再重新审查、批准并验收主结果。
