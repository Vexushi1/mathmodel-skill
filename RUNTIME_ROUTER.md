# HSK Runtime Router

机器路由以 `core/workflow_router.yaml` 为唯一事实源。本文件只解释运行时顺序，不复制完整路由表。

## 启动

```text
读取 core/bootstrap.yaml
→ 调用 scripts/resolve_runtime.py
→ [可选] 从 current project state 恢复缺失上下文与 verified artifacts
→ 合并显式/推断意图并记录 route provenance / confidence / ambiguity
→ 确定 objective / structures / 顶层 capabilities
→ 按 selected module/gate 声明补齐必要 contracts，再加载模块、Pack、模板
→ 到当前用户执行边界或所需模块产物停止
→ 执行解析结果中的 pre_delivery_gates
```

## Runtime Assurance

`core/runtime_assurance_contract.yaml` 只管理运行时证明层，不重新定义 Router、Manifest、Model Approval、Workbook 或 User Execution 的业务语义。默认 resolver 保留旧 plan 字段，同时输出 `runtime_plan` 与 `assurance`：context 说明字段来自 explicit input 还是 project state；intent resolution 给出关键词证据与歧义；artifact assurance 记录 scope、accepted/stale 状态、路径和 SHA-256；dependency closure 记录由选中 module/gate 自动补入的 contracts；authority fingerprint 绑定本次计划所依据的四个 Authority 文件。旧 `scripts/resolve_workflow.py` 继续用于无状态兼容调用。

## 项目工作记忆

`模型论文框架.md` 不是只给用户查看的输出文件。`proposed_model_spec` 形成后即可建立并维护，它是助手恢复当前项目上下文的首选入口：保存当前题意口径、数据与预处理决策、变量/参数/假设、模型与约束、小问依赖、Formula Trace、Algorithm Trace、Model Challenge/Human Approval 当前状态、数值参数证据、Terminology Registry、Numeric Profile、Title Claim、命题、Citation Evidence、Paper Fragment Dependency Map、深化证据处置、结果摘要、验证边界、图表映射和本项目论文组织选择。

- 普通单问继续：读取“当前有效口径”+对应 Q 区+必要依赖/结果摘要；
- 参数、约束、模型、预处理或算法口径修改：先读当前相关段落，再修改并同步受影响内容；
- Model Challenge/Human Approval 阶段：读取 current proposed model、semantic revision/hash、challenge 结论与 Approval Brief；用户只批准与当前 revision/hash 完全一致的模型语义；
- 结果验收/深化分析/绘图完成：把 current 结果摘要与证据位置写回框架；
- 进入算法流程写作时：读取目标问的算法呈现状态和关联 Algorithm Trace；`stepwise/pseudocode` 再按需加载 `packs/artifact/algorithm_flow.md`；
- 新聊天接续、长上下文恢复、整篇论文写作和终审：读取完整 current 框架；
- 具体数值必须再核对标准工作簿；semantic revision、hash、challenge/approval 和 stale 以 `state/project_state.yaml` 为准；
- 通用写作规则不写入框架，统一读取 writing Authority。

框架 stale 或与工作簿/状态冲突时，不得把聊天记忆当作仲裁依据，应回到对应上游阶段修正。

## 概念上的完整工作流

```text
problem_audit
→ model_design
   ├─ 非破坏性数据审计 + 两条模型路线/数据需求比较
   ├─ preprocessing_decision
   ├─ Formula Trace / 结构化简
   ├─ Algorithm Trace：not_needed / stepwise / pseudocode
   ├─ Semantic Closure / Complexity Sanity
   └─ proposed_model_spec
→ Model Reviewer
→ Devil's Advocate
→ Model Challenge passed
→ Model Approval Brief
→ awaiting_model_approval
→ 用户明确批准当前 semantic revision/hash
→ locked_model_spec
→ 按 preprocessing_decision 分流
   ├─ not_needed     ───────────────────────────────┐
   ├─ question_local ───────────────────────────────┤
   └─ project_level → data_preprocessing            │
                     → 用户本地运行预处理 Python     │
                     → 预处理工作簿 accepted ────────┘
→ solve_validate
→ 用户本地运行主求解 Python
→ 主工作簿 accepted
→ result_analysis
→ 用户本地运行深化分析 Python
→ 深化工作簿 accepted
→ figure_evidence
   ├─ [project_level] data_process.m
   └─ qX_plot.m / 机理图
→ writing_latex（按需消费 Algorithm Trace / algorithm_flow Pack）
→ ai_cleanup
→ LaTeX project/prose/BibTeX/framework audit（scripts/audit_latex_project.py + framework validator）
→ latex_compile_quality
→ review_delivery
→ 生成 official / reproducibility submission package（按当前请求与竞赛规则）
→ 按 resolver 返回顺序执行全部 pre_delivery_gates
→ validated_submission_package
```

Problem Contract 冻结、Semantic Closure 通过和 Complexity Sanity 通过都不能单独授权项目级预处理或主求解代码。只有 Model Challenge passed 且 Human Model Approval 绑定当前 `semantic_revision/hash` 后，`locked_model_spec` 才成为 current；语义 revision/hash 漂移会使旧 challenge、approval 与 locked model stale，并在重新进入主求解前要求重新 challenge + approval。

`data_preprocessing` 是条件阶段，不因“多问共享数据”自动启用。`not_needed` 直接使用原始数据；`question_local` 仅允许相关小问 Python 执行当前数学层已经定义的局部变换；只有 `project_level` 才在主求解前暂停，等待统一预处理工作簿通过质量门。

`data_process.m` 虽属于 `数据预处理/`，但它在后续 Figure Evidence 阶段生成，只读取已验收 `数据预处理结果.xlsx` 的底层证据绘图，不是主求解前置。

`solve_validate` 表示主求解代码交付与主结果质量门；`result_analysis` 表示在已验收主工作簿上单独生成 `问题X结果深化分析.py` 并选择题目专属深化分析。二者不得倒序，也不得用覆盖修改 `问题X求解.py` 的方式合并。已有 accepted 主工作簿的历史项目进入独立 `result_analysis` 时，不要求为了分析阶段追溯补做当时不存在的 Human Model Approval；只有重新进入当前模型设计、项目级预处理、主求解或语义变化后的重算才迁入该门。

解析器的 `full_solution` / `full_workflow` 初始计划不会跨越用户执行边界：未完成人工锁模时先停在 `awaiting_model_approval`；已锁模后若 `project_level` 则停在 `awaiting_user_preprocessing`，否则交付当前主求解 Python 并停在 `awaiting_user_execution`。用户返回对应工作簿并通过验收后，再继续后续模块。概念上的完整链与单次 resolver 输出不要混为一谈。

`result_analysis` 可以独立路由，但前提是当前主工作簿已经 accepted 且主结果质量门通过。若分析给出 `redo_required`，按原因回到 `model_design`、条件式 `data_preprocessing` 或 `solve_validate`，并传播下游 stale；若回到模型设计或需要重算主结果，则再次遵守 current Model Challenge/Human Approval 边界。

## Algorithm Trace 路由边界

普通“算法/算法实现/求解”仍属于数值求解路由；只有“算法流程、伪代码、论文算法、算法步骤、Algorithm 1、求解流程表”等明确论文呈现意图进入 `algorithm_presentation` route，避免把求解需求误识别成排版需求。

三种呈现状态：

```text
not_needed → 相邻公式与短正文足以恢复真实求解逻辑
stepwise   → 数学阶段传递是主要信息
pseudocode → 循环、分支、筛选、修复、接受/拒绝或终止逻辑本身是方法信息
```

只有 `stepwise/pseudocode` 建立 current Algorithm Trace，并闭合“模型/公式/命题/约束 → 论文算法 → 真实 Python → 工作簿结果或验证证据”。`not_needed` 不创建装饰性 Algorithm 1。Algorithm Flow Pack 是按需载体，不是新的 workflow stage，也不改变 Python 求解职责。

## 写作运行边界

默认写作链在 `figure_evidence` 后进入 LaTeX。`writing_docx` 只由显式 DOCX/Word 请求加载，不是 LaTeX 前置。

写作只加载当前 route 需要的 Authority：`core/writing_reasoning_contract.yaml` 管理 Formula Trace、Algorithm Trace、自适应算法呈现、Hard / Default / Recommendation、命题预算、Terminology、Numeric Style、Title Claim、深化证据处置、Paragraph Necessity、Paper Fragment stale 和 Citation Evidence；`modules/05_writing/latex.md` 管正文结构与表达。`packs/artifact/algorithm_flow.md` 与命题 Pack 仅承担按需呈现细则；AI cleanup、DOCX、review 与其他 Artifact Packs 是 consumer，不重新定义规则。

`prose/BibTeX/framework audit` 是 AI cleanup 后、最终编译前的非破坏性检查步骤：

- `blocking`：确定性 Hard 结构错误；
- `review_required`：Default 偏离，需要理由或修正；
- `warning`：Recommendation/风格风险。

默认只报告；`--strict` 阻断 `blocking` 和未处理的 `review_required`，warning 仍交给人工判断。机器不得从正则推断数学正确性、算法正确性、参数最优性、术语等价性或 citation 是否真正语义支持某个 claim。

## 示例

```bash
python scripts/resolve_runtime.py code_and_solution \
  --objective optimization \
  --structures stochastic \
  --competition CUMCM \
  --preprocessing-decision not_needed

python scripts/resolve_runtime.py code_and_solution \
  --objective optimization \
  --competition CUMCM \
  --preprocessing-decision project_level

python scripts/resolve_runtime.py result_analysis \
  --objective prediction \
  --structures temporal

python scripts/resolve_runtime.py algorithm_presentation \
  --objective optimization \
  --preprocessing-decision not_needed
```

解析结果返回 `module_terminal_outputs`、`pre_delivery_gates` 和 `terminal_outputs`。正式交付必须把 resolver 返回的 `pre_delivery_gates` 视为完整且有序的执行序列，不在入口文档维护第二套固定列表。`semantic_governance` 负责当前题意口径、语义闭环、复杂度复审和跨问 stale；`model_approval` 在当前代码阶段被返回时验证 Challenge/Human Approval 与 current semantic revision/hash；`project_sync` 按 exact scope 检查产物、工作簿、图表链和哈希且不自动提升质量状态；`submission_package_validation` 在返回时负责最终 submission manifest、归档内容与绑定哈希验证。

赛题 Python 的执行权、full-fidelity 配置和禁止降采样/粗网格/短时域/少重复/宽容差/静默 solver fallback 等规则，以 `core/user_execution_contract.yaml` 为唯一事实源。
