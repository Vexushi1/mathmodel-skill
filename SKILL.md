---
name: mathmodel-skill
version: 7.2.5
summary: HSK mathematical-modeling workflow with Problem Contract freezing, semantic closure, generalized evidence-driven conditional preprocessing, preprocessing paper/mathematical evidence, dedicated data_process MATLAB figures, dependency-aware stale propagation, full-fidelity user execution, separate primary/result-analysis Python stages and LaTeX-first writing.
triggers: [数学建模, 数模, CUMCM, 国赛, MCM, ICM, 电工杯, 认证杯, 建模论文, 模型论文框架, 数据预处理, 数据清洗, 主结果质量, 结果深化分析, Python求解, MATLAB绘图, LaTeX, DOCX]
---

# HSK 数学建模模块化工作流 v7.2.5

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

### 预处理一旦启用，论文与图表必须形成证据链

只要实际数据变换参与后续模型，就不能在论文中只写“完成清洗”“进行了插值/标准化”。必须闭合：

```text
数据问题与必要性
→ 方法选择与替代方案
→ 数学公式/变换关系/目标函数
→ 参数与阈值来源
→ 理论、统计或物理合理性验证
→ 处理前后底层数据证据
→ MATLAB证据图
→ 后续模型输入接口
```

确定性单位/坐标/主键处理给出映射和一致性检查；标准化/变换给出公式和参数估计范围；插值/填补给出公式或目标函数、边界条件和人工掩蔽/留出恢复误差；滤波/平滑/重采样给出核函数、频率响应或离散映射及参数依据；异常处理给出判定指标、阈值来源及保留/处理对照。

“合理的方法证明”不等于所有清洗都写形式定理。只有存在等价性、守恒性、单调性、误差界或可行性保持等可证明命题时才写形式证明；经验型处理使用统计检验、物理约束、人工掩蔽、留出验证、残差、频谱、分布和处理前后对照等可复验证据。

`project_level` 的最终预处理目录固定为：

```text
数据预处理/
├─ 数据预处理.py
├─ 数据预处理结果.xlsx
└─ data_process.m
```

`data_process.m` 是项目级预处理证据的固定 MATLAB 绘图脚本名；文件归属 `数据预处理/`，但仅在 Figure Evidence 阶段、主求解与结果深化分析完成后生成。它只读取 `数据预处理结果.xlsx` 中 Python 已保存的处理前后、诊断和验证底层数据，绘制处理前后、缺失/填补、分布、频谱、掩蔽恢复、采样覆盖或异常阈值等证据图；禁止在 MATLAB 中重新清洗、插值、滤波、重采样、训练填补模型或重新选择参数。正式导出图片基名使用 `data_process` 或 `data_process_<evidence>`，默认仍只保留图窗人工检查。

`question_local` 的实质变换在对应小问正文写公式、参数依据和验证；若需要图证据，由该问 `qX_plot.m` 读取 Python 已输出的底层数据绘制。

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
→ [project_level] data_process预处理证据图
→ MATLAB各问结果图 → LaTeX直写 → 编译与终审
```

题意解释、数据范围、变量、参数、假设、目标、约束、`preprocessing_decision`、实际预处理、算法语义或小问依赖变化时必须递增 `semantic_revision`；已验证语义变化先使受影响结果 stale，再按 `data / parameter / model / result` 依赖递归传播。接受新语义不恢复旧数值，仍须重新执行适用的数据处理、求解与验收。

代码工程质量由 `core/code_quality_contract.yaml` 唯一定义并由 `scripts/validate_code_delivery.py` 检查实际生成的 `preprocessing / primary / analysis` Python；工作簿由 `scripts/validate_user_execution.py` 按当前数据决策验收。目录与正式交付以 `core/output_contract.yaml` 为准。

MATLAB 默认只保留图窗，不在求解目录创建 `图表/` 或自动导出。DOCX 仅在用户显式要求时加载，不是 LaTeX 前置。v7.2.0--7.2.2 项目重新进入设计、预处理、绘图或写作时继续沿用三态 `preprocessing_decision`，并按当前通用审计与论文证据规则复核；历史只读交付不强制反向补文件。
