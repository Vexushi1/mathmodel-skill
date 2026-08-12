---
name: mathmodel-skill
version: 7.2.3
summary: HSK mathematical-modeling workflow with Problem Contract freezing, semantic closure, complexity sanity checks, generalized evidence-driven conditional data preprocessing, preprocessing MATLAB evidence via data_process.m, dependency-aware stale propagation, full-fidelity user execution, separate primary/result-analysis Python stages, MATLAB evidence figures and LaTeX-first writing.
triggers: [数学建模, 数模, CUMCM, 国赛, MCM, ICM, 电工杯, 认证杯, 建模论文, 模型论文框架, 数据预处理, 数据清洗, 主结果质量, 结果深化分析, Python求解, MATLAB绘图, LaTeX, DOCX]
---

# HSK 数学建模模块化工作流 v7.2.3

## 默认执行

先读 `core/bootstrap.yaml`，再由 `scripts/resolve_workflow.py` 按任务加载模块。进入正式模型或代码前，必须完成 Problem Contract 题意口径冻结、数据质量审计与 `preprocessing_decision`、题面—数学—代码—输出语义闭环、Complexity Sanity Check，并由 `scripts/validate_semantic_governance.py` 检查当前 semantic revision 和跨小问依赖 stale。

### 数据阶段硬规则

所有数据题都先审计，但不是所有数据题都要清洗：

```text
preprocessing_decision
├─ not_needed     → 不创建数据预处理/，直接读取原始数据
├─ question_local → 不创建全局预处理目录，本问脚本内做有数学来源的局部变换
└─ project_level  → 数据预处理.py → 数据预处理结果.xlsx → 依赖小问统一读取
```

是否进入预处理阶段必须根据**当前题目和当前附件本身**判断，不按某一种赛题或过去经验套模板。至少审计：缺失/NaN/Inf、缺失分布与连续缺口、单位/类型/主键/时间/坐标一致性、重复记录、物理或逻辑无效值、时间/空间采样与覆盖、测量噪声或漂移、模型对规则网格/完整矩阵/尺度/编码等输入要求，以及预测任务中的时间因果和信息泄漏。

两个及以上小问共享同一原始数据源只触发统一口径审计，不能单独推出需要清洗、插值、滤波、标准化或统一工作簿。存在缺失值也不能直接推出“必须插值”：应先判断变量类型、缺失位置、缺口长度、连续机制、模型是否原生支持缺失，以及删除、保持缺失、插值、统计填补、模型填补或预测填补哪一种假设最弱且可验证。

预测填补仅可用于恢复后续模型确实需要的缺测输入，并必须有独立验证且不得使用未来信息或目标标签；若赛题本身要求预测未来值、未知类别、需求、价格、风险或其他最终结果，该预测属于核心建模，不得提前包装成数据预处理。

若最终判定为 `project_level`，Python 预处理脚本还必须把处理前后、缺失修复验证、采样覆盖、结构对齐或其他实际需要的底层证据写入 `数据预处理结果.xlsx`。到 MATLAB Figure Evidence 阶段统一生成固定命名 **`数据预处理/data_process.m`**，该脚本只读统一工作簿绘图，不重新插值、填补、滤波、平滑、预测、异常修复或重采样。

赛题数值代码由用户本地以 `full_fidelity` 运行；助手生成并静态检查代码，不运行赛题代码、不自动降采样、不静默切换求解器。

每问完成数值阶段后默认恰好包含：

```text
问题X求解/
├─ 问题X求解.py
├─ 问题X求解结果.xlsx
├─ 问题X结果深化分析.py
├─ 问题X结果深化分析.xlsx
└─ qX_plot.m
```

只有 `preprocessing_decision=project_level` 时额外创建，Python阶段先形成前两项，统一 MATLAB 绘图阶段补齐第三项：

```text
数据预处理/
├─ 数据预处理.py
├─ 数据预处理结果.xlsx
└─ data_process.m
```

完整运行配置分别嵌入实际生成的阶段 Python 并写入对应工作簿；运行步骤和校验结果只在聊天或标准输出中返回。主工作簿验收后冻结 `问题X求解.py`，随后独立生成 `问题X结果深化分析.py`，不得为深化分析覆盖改写主求解脚本。

## 主链

```text
逐字审题 → Problem Contract冻结
→ 通用数据审计 → preprocessing_decision
→ 两条模型路线 → 变量/假设/公式/约束闭合
→ 题面—数学—代码语义闭环 → Complexity Sanity Check
→ semantic governance gate
→ [仅project_level] 项目级预处理 → 预处理质量门
→ Python完整主求解 → 主代码质量门 → 用户完整运行
→ 主结果质量门 → 独立Python结果深化分析 → 深化代码质量门 → 用户完整运行
→ 稳定性验收/必要时回退重算
→ MATLAB Figure Evidence：[project_level] data_process.m + 各问qX_plot.m
→ LaTeX直写 → 编译与终审
```

题意解释、数据范围、变量、参数、假设、目标、约束、`preprocessing_decision`、实际预处理、算法语义或小问依赖变化时必须递增 `semantic_revision`；已验证语义变化先使受影响结果 stale，再按 `data / parameter / model / result` 依赖递归传播。接受新语义不恢复旧数值，仍须重新执行适用的数据处理、求解与验收。

代码工程质量由 `core/code_quality_contract.yaml` 唯一定义并由 `scripts/validate_code_delivery.py` 检查实际生成的 `preprocessing / primary / analysis` Python；工作簿由 `scripts/validate_user_execution.py` 按当前数据决策验收。目录与正式交付以 `core/output_contract.yaml` 为准。

MATLAB 默认只保留图窗，不在求解目录创建 `图表/` 或自动导出。DOCX 仅在用户显式要求时加载，不是 LaTeX 前置。v7.2.0--7.2.2 项目重新进入设计/求解时继续沿用三态 `preprocessing_decision`，并按当前通用审计规则复核处理必要性；project_level旧项目重新进入 Figure Evidence 时补充 `data_process.m`。更早版本按既有只读兼容规则处理。
