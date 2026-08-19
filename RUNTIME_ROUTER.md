# HSK Runtime Router

机器路由以 `core/workflow_router.yaml` 为唯一事实源。本文件只解释运行时顺序，不复制完整路由表。

## 启动

```text
读取 core/bootstrap.yaml
→ 调用 scripts/resolve_workflow.py
→ 合并多个意图
→ 确定 objective / structures / 顶层 capabilities
→ 加载必要模块、Pack、模板
→ 到当前用户执行边界或所需模块产物停止
→ 执行解析结果中的 pre_delivery_gates
```

## 项目工作记忆

`模型论文框架.md` 不是只给用户查看的输出文件。模型锁定后，它是助手恢复当前项目上下文的首选入口：保存当前题意口径、数据与预处理决策、变量/参数/假设、模型与约束、小问依赖、Formula Trace、Algorithm Trace、数值参数证据、Terminology Registry、Numeric Profile、Title Claim、命题、Citation Evidence、Paper Fragment Dependency Map、深化证据处置、结果摘要、验证边界、图表映射和本项目论文组织选择。

- 普通单问继续：读取“当前有效口径”+对应 Q 区+必要依赖/结果摘要；
- 参数、约束、模型、预处理或算法口径修改：先读当前相关段落，再修改并同步受影响内容；
- 结果验收/深化分析/绘图完成：把 current 结果摘要与证据位置写回框架；
- 进入算法流程写作时：读取目标问的算法呈现状态和关联 Algorithm Trace；`stepwise/pseudocode` 再按需加载 `packs/artifact/algorithm_flow.md`；
- 新聊天接续、长上下文恢复、整篇论文写作和终审：读取完整 current 框架；
- 具体数值必须再核对标准工作簿；semantic revision、hash 和 stale 以 `state/project_state.yaml` 为准；
- 通用写作规则不写入框架，统一读取 writing Authority。

框架 stale 或与工作簿/状态冲突时，不得把聊天记忆当作仲裁依据，应回到对应上游阶段修正。

## 概念上的完整工作流

```text
problem_audit
→ model_design
   ├─ Formula Trace / 结构化简
   └─ Algorithm Trace：not_needed / stepwise / pseudocode
→ preprocessing_decision
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
→ prose/BibTeX/framework audit（scripts/audit_paper_prose.py + framework validator）
→ latex_compile_quality
→ review_delivery
```

`data_preprocessing` 是条件阶段，不因“多问共享数据”自动启用。`not_needed` 直接使用原始数据；`question_local` 仅允许相关小问 Python 执行当前数学层已经定义的局部变换；只有 `project_level` 才在主求解前暂停，等待统一预处理工作簿通过质量门。

`data_process.m` 虽属于 `数据预处理/`，但它在后续 Figure Evidence 阶段生成，只读取已验收 `数据预处理结果.xlsx` 的底层证据绘图，不是主求解前置。

`solve_validate` 表示主求解代码交付与主结果质量门；`result_analysis` 表示在已验收主工作簿上单独生成 `问题X结果深化分析.py` 并选择题目专属深化分析。二者不得倒序，也不得用覆盖修改 `问题X求解.py` 的方式合并。

解析器的 `full_solution` / `full_workflow` 初始计划不会跨越用户执行边界：它先交付当前应运行的 Python 与运行说明，在 `awaiting_user_preprocessing` 或 `awaiting_user_execution` 停止。用户返回对应工作簿并通过验收后，再继续后续模块。概念上的完整链与单次 resolver 输出不要混为一谈。

`result_analysis` 可以独立路由，但前提是当前主工作簿已经 accepted 且主结果质量门通过。若分析给出 `redo_required`，按原因回到 `model_design`、条件式 `data_preprocessing` 或 `solve_validate`，并传播下游 stale。

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
python scripts/resolve_workflow.py code_and_solution \
  --objective optimization \
  --structures stochastic \
  --competition CUMCM \
  --preprocessing-decision not_needed

python scripts/resolve_workflow.py code_and_solution \
  --objective optimization \
  --competition CUMCM \
  --preprocessing-decision project_level

python scripts/resolve_workflow.py result_analysis \
  --objective prediction \
  --structures temporal

python scripts/resolve_workflow.py algorithm_presentation \
  --objective optimization \
  --preprocessing-decision not_needed
```

解析结果返回 `module_terminal_outputs`、`pre_delivery_gates` 和 `terminal_outputs`。`semantic_governance` 在正式模型、代码、返回工作簿和下游交付前检查当前题意口径、语义闭环、复杂度复审和跨问 stale；`project_sync` 在正式产物交付时按 exact scope 检查产物、工作簿、图表链和哈希，不自动把质量门或分析状态提升为 passed。

赛题 Python 的执行权、full-fidelity 配置和禁止降采样/粗网格/短时域/少重复/宽容差/静默 solver fallback 等规则，以 `core/user_execution_contract.yaml` 为唯一事实源。
