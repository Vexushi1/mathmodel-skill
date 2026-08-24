---
name: mathmodel-skill
version: 7.10.0
summary: HSK mathematical-modeling workflow with Problem Contract freezing, semantic closure, evidence-driven conditional preprocessing, full-fidelity user execution, separate primary/result-analysis Python stages, project-memory model-paper framework, Source-Derivation-Destination formula traces, adaptive Algorithm Trace with stepwise/pseudocode presentation, tiered writing governance, Citation Evidence, Terminology Registry, scoring-aware high-precision Numeric Profile, Title Claim Gate, support/modify/reject analysis evidence, local paper-fragment stale propagation, Paragraph Necessity, MATLAB evidence figures, formal LaTeX audit/compile attestation, and validated submission-package provenance.
triggers: [数学建模, 数模, CUMCM, 国赛, MCM, ICM, 电工杯, 认证杯, 建模论文, 模型论文框架, 算法流程, 伪代码, 数据预处理, 数据清洗, 主结果质量, 结果深化分析, Python求解, MATLAB绘图, LaTeX, DOCX]
---

# HSK 数学建模模块化工作流 v7.10.0

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

`locked_model_spec` 形成后，项目根目录 `模型论文框架.md` 是助手跨阶段、跨聊天恢复当前项目语义的首选入口。它只保存当前项目事实、选择、状态和证据位置，包括 Formula Trace、Algorithm Trace、数值参数依据、命题、Citation Evidence、Terminology Registry、Numeric Profile、Title Claim、Paper Fragment Dependency Map、深化证据处置、结果摘要与图表映射；不复制通用写作手册。

具体数值必须回到已验收工作簿复核，semantic revision、hash 和 stale 由 `state/project_state.yaml` 管理。模型、参数、约束、预处理或算法语义变化时先传播数值 stale；v0.8 框架再按真实依赖只传播到相关正文、摘要、图表、模型评价与 Title Claim，不无差别失效整篇论文。

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

主工作簿 accepted 后冻结 `问题X求解.py`，再独立生成 `问题X结果深化分析.py`；不得为深化分析覆盖改写主求解脚本。每项深化分析证据必须指向具体 target claim，并记录 `support / modify / reject` 与 required action；reject 核心答案才触发回退，reject 非核心评价可删除或重写。

### Algorithm Trace 与论文算法流程

算法流程不是独立求解阶段，也不是每问必设。模型设计后按真实求解结构选择：

```text
not_needed → 公式与短正文已经足以恢复计算逻辑
stepwise   → 多阶段数学求解，用 Step 1...n 表达阶段传递
pseudocode → 循环、分支、筛选、修复、接受/拒绝或终止逻辑本身需要展示
```

只有 `stepwise/pseudocode` 才建立 current Algorithm Trace，并闭合：

```text
模型结构/命题/约束
→ Algorithm Trace
→ 论文算法流程
→ Python真实实现
→ 工作簿结果或验证证据
```

详细呈现按需加载 `packs/artifact/algorithm_flow.md`。伪代码写数学对象和控制逻辑，不把 `range(len(...))`、DataFrame、文件路径、日志或异常处理等 Python 实现细节搬进正文；简单问题不得为了形式生成装饰性 Algorithm 1。

### Figure Evidence

MATLAB 图形布局、证据等级、配色和数据追溯统一由 `modules/04_figure_evidence.md` 管理。`data_process.m` 和 `qX_plot.m` 只读取 Python 已输出的数据/工作簿，不重新执行核心计算；默认保留图窗供人工检查，不批量自动导出。

### 写作治理

LaTeX 是默认论文主链。写作阶段不在入口文件复制正文规则：

- `core/writing_reasoning_contract.yaml`：跨竞赛推理、Hard / Default / Recommendation、Formula Trace、Algorithm Trace 与算法呈现、命题预算、Citation Evidence、Terminology、Numeric Style、Title Claim、深化证据处置、Paragraph Necessity 与局部 stale；
- `modules/05_writing/latex.md`：正文结构与表达唯一权威；
- `packs/artifact/algorithm_flow.md`：按需提供控制流伪代码与分阶段数学步骤的载体细则，不建立第二套算法规则；
- `modules/05_writing/ai_cleanup.md`：按 Integrity / Evidence / Style & Necessity / Machine diagnostics 分层清理，不维护穷举式第二套规则；
- `modules/05_writing/docx.md`：只在用户显式要求时加载，负责 Word 载体差异；
- `modules/06_review_delivery.md`：只检查和分级，不重新定义写作规则。

核心模型收束按 `required / inline / not_applicable` 自适应；算法流程按 `not_needed / stepwise / pseudocode` 自适应；命题 0--4 是默认正文阅读预算而非 Hard 上限；优点与缺点没有强制数量关系。需要外部证据的核心 claim 通过 Citation Evidence 连接正文位置与 `references.bib`。

**核心答案展示精度优先服从题目、官方格式与评分精度。** 若后续小数位可能计分，摘要、正文直接答案、关键结果表和提交结果文件不得为了简洁或美观擅自降精度；无更具体口径时，高精度评分场景通常保留小数后 6--7 位。自然语言技术术语按 Terminology Registry 保持 canonical term 稳定；标题中的实质方法/贡献通过 Title Claim Gate 与摘要、关键词、正文主模型和结果证据闭环。

正式 LaTeX 成稿统一运行 `scripts/audit_latex_project.py` 并持久化 `latex_audit_report.yaml`；正式编译由 `scripts/render_paper.py` 生成绑定 source bundle、audit report、compile profile 与 PDF 哈希的 `compile_report.yaml`。模块化工程递归展开全部 active fragment，兼容单文件工程自然退化为单文件审计，底层 `audit_paper_prose.py` 继续执行 prose/BibTeX/framework 检查。最终提交包必须经过 `scripts/validate_submission_package.py`，official 与 reproducibility 两种 package 语义不得混用。

## 主链

```text
逐字审题 → Problem Contract冻结
→ 通用数据审计 → preprocessing_decision
→ 两条模型路线 → 变量/假设/公式/约束闭合
→ 结构化简 → Algorithm Trace/呈现模式按需确定
→ 题面—数学—代码—输出语义闭环 → Complexity Sanity Check
→ semantic governance gate
→ [仅project_level] 项目级预处理 → 预处理质量门
→ Python完整主求解 → 用户完整运行 → 主结果质量门
→ 独立Python结果深化分析 → support/modify/reject → 必要时回退
→ MATLAB证据图
→ Terminology/Numeric/Title Claim/局部Paper Fragment同步
→ 题型自适应LaTeX直写（含按需算法流程） → AI-cleanup
→ LaTeX project audit attestation → profile-bound compile attestation
→ submission package validation → 编译与评委式终审
```

目录、正式交付和同步门以 `core/output_contract.yaml` 为准；代码工程质量以 `core/code_quality_contract.yaml` 为准；返回工作簿以 `scripts/validate_user_execution.py` 验收。legacy 项目保持只读兼容，重新进入当前流程时按当前语义与数据决策规则迁移。
