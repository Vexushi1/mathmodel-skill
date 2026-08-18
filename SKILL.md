---
name: mathmodel-skill
version: 7.6.0
summary: HSK mathematical-modeling workflow with Problem Contract freezing, semantic closure, evidence-driven conditional preprocessing, full-fidelity user execution, separate primary/result-analysis Python stages, project-memory model-paper framework, Source-Derivation-Destination formula traces, tiered writing governance, Citation Evidence, adaptive proposition/core-model-summary policies, MATLAB evidence figures, prose/BibTeX audit, and LaTeX-first delivery.
triggers: [数学建模, 数模, CUMCM, 国赛, MCM, ICM, 电工杯, 认证杯, 建模论文, 模型论文框架, 数据预处理, 数据清洗, 主结果质量, 结果深化分析, Python求解, MATLAB绘图, LaTeX, DOCX]
---

# HSK 数学建模模块化工作流 v7.6.0

<!-- HSK_RUNTIME_ENTRY_CONTRACT_START -->
## 运行时入口合同（非权威摘要）

无论从根目录 `SKILL.md` 还是插件目录 `skills/mathmodel-skill/SKILL.md` 进入，运行语义都只服从同一仓库根目录权威链：

1. 先读取 `core/bootstrap.yaml`；
2. 默认全局规则由 `core/workflow_router.yaml` 的 `default_load` 指向 `core/hsk_core_policy.md`；
3. 使用 `scripts/resolve_workflow.py` 按用户当前任务解析最小 `load_order`；
4. 只加载 resolver 命中的 route-specific contracts、modules、packs 与 templates；建模/写作推理仅在对应 route 加载 `core/writing_reasoning_contract.yaml`；
5. 已有 current `模型论文框架.md` 时按 `project_memory_contract` 恢复项目语义，具体数值仍以已验收工作簿为准；
6. `legacy/` 与 V622 compatibility pointers 不进入默认执行链。

本节只声明入口委托关系，不作为模型、预处理、求解、绘图或写作规则的独立权威；详细规则以 `core/bootstrap.yaml` 指向的当前权威源为准。
<!-- HSK_RUNTIME_ENTRY_CONTRACT_END -->

## 默认执行

先读 `core/bootstrap.yaml`，再由 `scripts/resolve_workflow.py` 按任务加载最小模块集。正式模型或代码前必须完成 Problem Contract、数据审计与 `preprocessing_decision`、题面—数学—代码—输出语义闭环和 Complexity Sanity Check，并通过 `scripts/validate_semantic_governance.py`。

### 项目工作记忆

`locked_model_spec` 形成后，项目根目录 `模型论文框架.md` 是助手跨阶段、跨聊天恢复当前项目语义的首选入口。它只保存当前项目事实、选择、状态和证据位置，包括 Formula Trace、数值参数依据、命题、Citation Evidence、结果摘要与图表映射；不复制通用写作手册。

具体数值必须回到已验收工作簿复核，semantic revision、hash 和 stale 由 `state/project_state.yaml` 管理。模型、参数、约束、预处理或算法语义变化时先传播 stale，再同步受影响框架内容。

### 数据与求解

所有数据题都先审计，但不是所有数据题都要清洗：

```text
preprocessing_decision
├─ not_needed     → 不创建数据预处理/，直接读取原始数据
├─ question_local → 不创建全局预处理目录，本问脚本内做有数学来源的局部变换
└─ project_level  → 数据预处理.py → 数据预处理结果.xlsx → 依赖小问统一读取
```

共享数据本身不能推出必须项目级预处理；任何会改变模型输入的处理都要有数据、机理或模型必要性、参数依据和验证证据。`project_level` 时使用：

```text
数据预处理/
├─ 数据预处理.py
├─ 数据预处理结果.xlsx
└─ data_process.m
```

赛题数值代码由用户本地以 `full_fidelity` 执行；助手生成并静态检查，不运行题目专属预处理、求解或深化分析代码，不自动降采样、放宽容差或静默切换求解器。

每问默认唯一数值目录：

```text
问题X求解/
├─ 问题X求解.py
├─ 问题X求解结果.xlsx
├─ 问题X结果深化分析.py
├─ 问题X结果深化分析.xlsx
└─ qX_plot.m
```

主工作簿 accepted 后冻结 `问题X求解.py`，再独立生成 `问题X结果深化分析.py`；不得为深化分析覆盖改写主求解脚本。

### Figure Evidence

MATLAB 图形布局、证据等级、配色和数据追溯统一由 `modules/04_figure_evidence.md` 管理。`data_process.m` 和 `qX_plot.m` 只读取 Python 已输出的数据/工作簿，不重新执行核心计算；默认保留图窗供人工检查，不批量自动导出。

### 写作治理

LaTeX 是默认论文主链。写作阶段不在入口文件复制正文规则：

- `core/writing_reasoning_contract.yaml`：跨竞赛推理、Hard / Default / Recommendation、命题预算、Citation Evidence；
- `modules/05_writing/latex.md`：正文结构与表达唯一权威；
- `modules/05_writing/ai_cleanup.md`：只做模板化与空泛表达清理；
- `modules/05_writing/docx.md`：只在用户显式要求时加载，负责 Word 载体差异；
- `modules/06_review_delivery.md`：只检查和分级，不重新定义写作规则。

核心模型收束按 `required / inline / not_applicable` 自适应；命题 0--4 是默认正文阅读预算而非 Hard 上限；优点与缺点没有强制数量关系。需要外部证据的核心 claim 通过 Citation Evidence 连接正文位置与 `references.bib`。成稿运行 `scripts/audit_paper_prose.py`，确定性 Hard 错误为 blocking，Default 偏离为 review_required，Recommendation/风格风险为 warning；机器不得从正则推断数学正确性或 citation 的语义支持关系。

## 主链

```text
逐字审题 → Problem Contract冻结
→ 通用数据审计 → preprocessing_decision
→ 两条模型路线 → 变量/假设/公式/约束闭合
→ 题面—数学—代码—输出语义闭环 → Complexity Sanity Check
→ semantic governance gate
→ [仅project_level] 项目级预处理 → 预处理质量门
→ Python完整主求解 → 用户完整运行 → 主结果质量门
→ 独立Python结果深化分析 → 用户完整运行 → 稳定性验收/必要时回退
→ MATLAB证据图
→ 题型自适应LaTeX直写 → AI-cleanup → prose/BibTeX audit
→ 编译与评委式终审
```

目录、正式交付和同步门以 `core/output_contract.yaml` 为准；代码工程质量以 `core/code_quality_contract.yaml` 为准；返回工作簿以 `scripts/validate_user_execution.py` 验收。legacy 项目保持只读兼容，重新进入当前流程时按当前语义与数据决策规则迁移。
