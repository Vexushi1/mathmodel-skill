---
name: mathmodel-skill
version: 7.16.0
summary: HSK mathematical-modeling workflow with Problem Contract freezing, semantic closure, independent Model Reviewer plus Devil's Advocate challenge, explicit Human Model Approval bound to the current semantic revision/hash, evidence-driven conditional preprocessing, full-fidelity user execution, capability-driven primary numerical validity with independent evidence recheck, evidence-ready Primary Evidence Capture, separate primary/result-analysis Python stages, fine-grained Analysis Evidence Capture, project-memory model-paper framework, Source-Derivation-Destination formula traces, explicit Model/Solver/Validator roles, optimization model expression closure, adaptive Algorithm Trace with stepwise/pseudocode presentation, tiered writing governance, Citation Evidence, Terminology Registry, scoring-aware high-precision Numeric Profile, Title Claim Gate, evidence-level claim calibration, question-subsection granularity review, support/modify/reject analysis evidence, local paper-fragment stale propagation, Paragraph Necessity, MATLAB Scientific Figure Synthesis with caption-owned formal titles, high-contrast composite visualization and evidence-driven Figure Enhancement, formal LaTeX audit/compile attestation, and validated submission-package provenance.
triggers: [数学建模, 数模, CUMCM, 国赛, MCM, ICM, 电工杯, 认证杯, 审题, 问题分析, 建模思路, 建模方案, 模型比较, 完整求解, 全流程, 建模论文, 模型论文框架, 模型锁定, 模型审查, 算法流程, 伪代码, 数据预处理, 数据清洗, 主结果质量, 数值有效性, 结果分析, 结果深化分析, Python求解, MATLAB绘图, LaTeX, DOCX, 终审, 提交包]
---

# HSK 数学建模模块化工作流 v7.16.0

<!-- HSK_RUNTIME_ENTRY_CONTRACT_START -->
## 运行时入口合同（非权威摘要）

无论从根目录 `SKILL.md` 还是插件目录 `skills/mathmodel-skill/SKILL.md` 进入，运行语义都只服从同一仓库根目录权威链：

1. 先读取 `core/bootstrap.yaml`；
2. 默认全局规则由 `core/workflow_router.yaml` 的 `default_load` 指向 `core/hsk_core_policy.md`；
3. 使用 `scripts/resolve_runtime.py` 按用户当前任务解析最小 `load_order`；
4. 只加载 resolver 命中的 route-specific contracts、modules、packs 与 templates；建模/写作推理仅在对应 route 加载 `core/writing_reasoning_contract.yaml`；模型锁定与人工批准按需加载 `core/model_approval_contract.yaml`；主求解设计、主求解与主工作簿验收按需加载 `core/numerical_verification_contract.yaml`，结果深化分析不把该合同扩张为稳健性规则；
5. 已有 current `模型论文框架.md` 时按 `project_memory_contract` 恢复项目语义，具体数值仍以已验收工作簿为准；
6. `legacy/` 与 V622 compatibility pointers 不进入默认执行链。

本节只声明入口委托关系，不作为模型、预处理、求解、绘图或写作规则的独立权威；详细规则以 `core/bootstrap.yaml` 指向的当前权威源为准。
<!-- HSK_RUNTIME_ENTRY_CONTRACT_END -->

### Declarative Runtime & Assurance

默认运行时入口为 `scripts/resolve_runtime.py`。它在不改变旧 plan 顶层字段的前提下增加 `runtime_plan` 与 `assurance`：可从 current `state/project_state.yaml` 按需恢复 competition、preprocessing decision、单问 classification 与已验证 artifact；所有推断都输出 intent provenance、confidence/ambiguity 诊断，文件型 artifact 只有 accepted 状态、路径和 SHA-256 同时闭合时才可由 project state 自动放行。选中 module/gate 后，再按 `core/runtime_assurance_contract.yaml` 声明补齐必需 contract；`scripts/resolve_workflow.py` 保留为无状态兼容入口。

## 默认执行

先读 `core/bootstrap.yaml`，再由 `scripts/resolve_runtime.py` 按任务加载最小模块集；只有显式 legacy 兼容调用才直接使用 `scripts/resolve_workflow.py`。Problem Contract 冻结后先完成非破坏性数据审计与模型路线/数据需求比较，随后锁定 `preprocessing_decision`，再完成题面—数学—代码—输出语义闭环和 Complexity Sanity Check；达到设计完整性后形成 `proposed_model_spec`，再执行独立 Model Reviewer 与 Devil's Advocate 两次 Model Challenge。Challenge 通过后生成 Model Approval Brief，并停在 `awaiting_model_approval`；只有用户明确批准当前 `semantic_revision/hash` 后才形成 current `locked_model_spec`。正式项目级预处理或主求解代码前还必须按 resolver 返回顺序通过 `scripts/validate_semantic_governance.py` 与 `scripts/validate_model_approval.py`。

### 项目工作记忆

`proposed_model_spec` 形成后即可建立或更新项目根目录 `模型论文框架.md`，用于保存当前模型口径、Challenge 与 Approval Brief；用户批准后当前模型才提升为 `locked_model_spec`。框架是助手跨阶段、跨聊天恢复当前项目语义的首选入口，只保存当前项目事实、选择、状态和证据位置，包括标准模型类型与正式模型名称、Model/Solver/Validator 角色、Formula Trace、Algorithm Trace、Model Challenge/Human Approval 当前状态、Primary Quality Specification、数值参数依据、命题、Citation Evidence、Terminology Registry、Numeric Profile、Title Claim、Paper Fragment Dependency Map、深化证据处置、Headline Claim Evidence Level/Scope、问题章节小节规划、结果摘要与图表映射；不复制通用写作手册。

具体数值必须回到已验收工作簿复核，semantic revision、hash、challenge/approval 和 stale 由 `state/project_state.yaml` 管理。模型、参数、约束、预处理或算法语义变化时旧 challenge、approval 与 locked model 同步 stale，并传播数值 stale；v0.9 框架再按真实依赖只传播到相关正文、摘要、图表、模型评价与 Title Claim，不无差别失效整篇论文。纯排版、措辞、caption、公式编号或不改变语义的 LaTeX 文件拆分不触发重新审批。

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

无论哪种预处理状态，都不能绕过 Model Challenge 与 Human Approval 直接生成正式任务代码。赛题数值代码由用户本地以 `full_fidelity` 执行；助手生成并静态检查，不运行题目专属预处理、求解或深化分析代码，不自动降采样、放宽容差或静默切换求解器。

v7.14 将主求解质量检查限定为**当前 locked model + 当前声明数值方法下，本次主计算是否具备 accepted 资格**。Module 02 在正式主求解代码前形成 Primary Quality Specification；`问题X求解.py` 只输出适用 capability 所要求的可行性、残差、离散、收敛、最低采样精度或其他内在数值有效性证据。`scripts/validate_numerical_evidence.py` 在返回工作簿验收时独立复核底层证据与 `主结果质量门` 的 Verification ID、实际值、阈值、判定关系和证据工作表，不能只相信工作簿自报“通过”。完整规则只由 `core/numerical_verification_contract.yaml` 定义。

v7.15 在不改变上述 PQS / Verification ID 语义的前提下，把主求解输出升级为 **evidence-ready**：除最终答案外，`问题X求解.py` 还应按模型 capability 保留本次主计算已经真实产生、且对解释模型、科研绘图、验证或避免昂贵重算有价值的状态、过程与结构数据。判界只看是否需要改变当前输入、参数、场景、seed、初值、算法、模型结构或验证窗口去重新运行新的计算世界；若需要，仍只能进入主工作簿 accepted 后的结果深化分析。

主质量门**不负责**参数敏感性、压力场景、替代算法/结构、多 seed 或多初值结论稳定性、异质性、误差分解和更广泛外样本稳定性；这些只在主工作簿 accepted 后进入独立结果深化分析。数值步长/网格是否足以支撑当前答案属于主质量，现实/模型参数变化是否改变结论属于深化分析。03B 产生的新分析证据也应保留参数/场景/算法/seed/阈值/对象等细粒度底表，而不是只留下“稳定”等摘要判断。

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

MATLAB 的唯一绘图决策 Authority 仍为 `modules/04_figure_evidence.md`。v7.15 在原有 Figure Layout / Enhancement 之上增加 **Scientific Figure Synthesis、Basic-form Challenge、Composite Encoding Preference、Scientific Rendering Profiles 与论文级 Figure Portfolio Scientific Quality Gate**：核心图优先把 accepted 工作簿中的时间、空间、状态、分布、约束、边界、不确定性、多目标和异质性结构直接编码成科研证据，而不是把丰富底层数据重新压成 plain bar / plain line / plain scatter。箱线+原始散点、小提琴+散点、折线+区间、scatter+fit/CI、heatmap+contour、Pareto+推荐点+Local Zoom、trajectory+field+boundary 等组合仅在真实证据支持且提高信息效率时采用；高级不等于复杂。

正式论文图继续不设置整体 `title` / `sgtitle`，DOCX/LaTeX caption 承担正式图号与图名；多面板按需只保留 panel label，坐标轴、单位、图例和必要直接标注继续服务证据读取。主证据恢复高对比亮蓝/鲜红等颜色，辅助对象、背景和区间仍用灰色/透明度降权；默认 `grid off`。`data_process.m` 和 `qX_plot.m` 只读取 Python 已输出的数据/工作簿，不重新执行核心计算；默认保留图窗供人工检查，不批量自动导出。

### 写作治理

LaTeX 是默认论文主链。写作阶段不在入口文件复制正文规则：

- `core/writing_reasoning_contract.yaml`：跨竞赛推理、Hard / Default / Recommendation、Model/Solver/Validator、优化模型表达、Formula Trace、Algorithm Trace 与算法呈现、solver justification、命题预算、Citation Evidence、Terminology、Numeric Style、Title Claim、Claim Strength Calibration、问题章节小节颗粒度、深化证据处置、Paragraph Necessity 与局部 stale；
- `core/model_approval_contract.yaml`：Model Reviewer、Devil's Advocate、Model Approval Brief、显式 Human Approval 与 revision/hash 绑定；
- `modules/05_writing/latex.md`：正文结构与表达唯一权威；
- `packs/artifact/algorithm_flow.md`：按需提供控制流伪代码与分阶段数学步骤的载体细则，不建立第二套算法规则；
- `modules/05_writing/ai_cleanup.md`：按 Integrity / Evidence / Style & Necessity / Machine diagnostics 分层清理，不维护穷举式第二套规则；
- `modules/05_writing/docx.md`：只在用户显式要求时加载，负责 Word 载体差异；
- `modules/06_review_delivery.md`：只检查和分级，不重新定义写作规则。

v7.16 进一步要求论文先恢复**数学模型本体**，再介绍 solver/validator：优化题默认按“标准模型类型与现实目标 → 决策变量/对象 → objective → objective 含义 → 约束 → 核心模型汇总 → solver/validator”组织；优化类摘要至少明确“优化什么”。题目专属模型名可以保留，但首次出现要能识别标准数学类型。solver 第一次使用说明本题结构理由，跨问复用/更换说明继承或结构增量；另用算法只有存在真实 artifact 时才写成 baseline/alternative/validator。问题章节内部二级小节默认保持紧凑连续，超过约 3--4 个只触发 review，不限制一级章节数量。摘要和正文的强 claim 按 `PROVEN / VERIFIED_NUMERIC / COMPARATIVE / OBSERVED / HEURISTIC` 校准，有限数值验证不得升级成全局最优证明。

核心模型收束按 `required / inline / not_applicable` 自适应；算法流程按 `not_needed / stepwise / pseudocode` 自适应；命题 0--4 是默认正文阅读预算而非 Hard 上限；优点与缺点没有强制数量关系。需要外部证据的核心 claim 通过 Citation Evidence 连接正文位置与 `references.bib`。

**核心答案展示精度优先服从题目、官方格式与评分精度。** 若后续小数位可能计分，摘要、正文直接答案、关键结果表和提交结果文件不得为了简洁或美观擅自降精度；无更具体口径时，高精度评分场景通常保留小数后 6--7 位。自然语言技术术语按 Terminology Registry 保持 canonical term 稳定；标题中的实质方法/贡献通过 Title Claim Gate 与摘要、关键词、正文主模型和结果证据闭环。

正式 LaTeX 成稿统一运行 `scripts/audit_latex_project.py` 并持久化 `latex_audit_report.yaml`；正式编译由 `scripts/render_paper.py` 生成绑定 source bundle、audit report、compile profile 与 PDF 哈希的 `compile_report.yaml`。模块化工程递归展开全部 active fragment，兼容单文件工程自然退化为单文件审计，底层 `audit_paper_prose.py` 继续执行 prose/BibTeX/framework 检查。最终提交包必须经过 `scripts/validate_submission_package.py`，official 与 reproducibility 两种 package 语义不得混用。

## 主链

```text
逐字审题 → Problem Contract冻结
→ 通用数据审计 → 两条模型路线与数据需求比较
→ preprocessing_decision
→ 变量/假设/公式/约束闭合 → 标准模型类型与Model/Solver/Validator身份 → 结构化简
→ Algorithm Trace/呈现模式按需确定
→ 题面—数学—代码—输出语义闭环 → Complexity Sanity Check
→ proposed_model_spec
→ Model Reviewer + Devil's Advocate → Model Challenge passed
→ Model Approval Brief → awaiting_model_approval
→ 用户明确批准 current semantic revision/hash → locked_model_spec
→ semantic governance + model approval gate
→ [仅project_level] 项目级预处理 → 预处理质量门
→ Primary Quality Specification → Python完整主求解 + Primary Evidence Capture → 用户完整运行
→ 主结果质量门 + 独立 numerical evidence recheck → accepted solution workbook
→ 独立Python结果深化分析 + Analysis Evidence Capture → support/modify/reject → 必要时回退
→ MATLAB Scientific Figure Synthesis / Composite / Enhancement → Portfolio Review
→ Terminology/Numeric/Title Claim/Claim Scope/局部Paper Fragment同步
→ 题型自适应LaTeX直写（含按需算法流程） → AI-cleanup
→ LaTeX project audit attestation → profile-bound compile attestation
→ 评委式终审 → 生成 official / reproducibility submission package
→ 按 resolver 返回顺序执行全部 pre_delivery_gates
→ validated_submission_package
```

目录、正式交付和同步门以 `core/output_contract.yaml` 为准；模型挑战与人工锁模以 `core/model_approval_contract.yaml` 为准；主求解数值有效性以 `core/numerical_verification_contract.yaml` 为准；代码工程质量以 `core/code_quality_contract.yaml` 为准；返回工作簿以 `scripts/validate_user_execution.py` 验收。legacy 项目保持只读兼容，重新进入当前模型设计/预处理/主求解时按当前 challenge/approval、语义、数据决策、v7.14 主数值证据、v7.15 Evidence Capture 与 v7.16 写作身份/claim-scope 规则迁移。
