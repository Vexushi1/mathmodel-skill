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

## 插件目录解析

本文件位于 `skills/mathmodel-skill/`；执行时先定位仓库根目录 `../..`，再读取 `../../core/bootstrap.yaml` 并调用 `../../scripts/resolve_workflow.py`。后续合同、模块、模板和脚本路径均以仓库根目录为基准，不在插件目录维护第二份规则。

## 当前运行摘要

正式模型/代码前完成 Problem Contract、当前附件数据审计、`preprocessing_decision`、题面—数学—代码—输出语义闭环和 Complexity Sanity Check，并通过 `../../scripts/validate_semantic_governance.py`。

`模型论文框架.md` 是当前项目事实与语义索引，只保存当前项目选择、Formula Trace、参数证据、命题、Citation Evidence、结果摘要和图表映射。数值事实来自已验收工作簿，semantic revision/hash/stale 来自 `state/project_state.yaml`。

数据决策只有：

```text
not_needed
question_local
project_level
```

共享数据或发现缺失值本身不能自动推出 `project_level`。只有 `project_level` 创建 `数据预处理/数据预处理.py`、`数据预处理结果.xlsx` 和 `data_process.m`；局部变换留在对应小问。

每问默认唯一数值目录：

```text
问题X求解/
├─ 问题X求解.py
├─ 问题X求解结果.xlsx
├─ 问题X结果深化分析.py
├─ 问题X结果深化分析.xlsx
└─ qX_plot.m
```

题目专属 Python 由用户本地 full-fidelity 执行。主工作簿 accepted 后冻结主脚本，再独立生成结果深化分析脚本。

写作规则按单一 Authority 链加载：`core/writing_reasoning_contract.yaml` 管理 Hard / Default / Recommendation、命题预算和 Citation Evidence；`modules/05_writing/latex.md` 管正文结构与表达；AI-cleanup、DOCX、review 和 Artifact Packs 只消费这些 Authority。核心模型收束按 `required / inline / not_applicable` 自适应；命题 0--4 是默认阅读预算而非 Hard 上限；优缺点没有强制数量关系。

正式 LaTeX 在 AI cleanup 后运行 prose/BibTeX audit，再进入编译和终审。目录、交付和同步门以 `core/output_contract.yaml` 为准。
