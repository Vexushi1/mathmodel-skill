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

## 概念上的完整工作流

```text
problem_audit
→ model_design
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
→ writing_latex
→ ai_cleanup
→ latex_compile_quality
→ review_delivery
```

`data_preprocessing` 是条件阶段，不因“多问共享数据”自动启用。`not_needed` 直接使用原始数据；`question_local` 仅允许相关小问 Python 执行当前数学层已经定义的局部变换；只有 `project_level` 才在主求解前暂停，等待统一预处理工作簿通过质量门。

`data_process.m` 虽属于 `数据预处理/`，但它在后续 Figure Evidence 阶段生成，只读取已验收 `数据预处理结果.xlsx` 的底层证据绘图，不是主求解前置。

`solve_validate` 表示主求解代码交付与主结果质量门；`result_analysis` 表示在已验收主工作簿上单独生成 `问题X结果深化分析.py` 并选择题目专属深化分析。二者不得倒序，也不得用覆盖修改 `问题X求解.py` 的方式合并。

解析器的 `full_solution` / `full_workflow` 初始计划不会跨越用户执行边界：它先交付当前应运行的 Python 与运行说明，在 `awaiting_user_preprocessing` 或 `awaiting_user_execution` 停止。用户返回对应工作簿并通过验收后，再继续后续模块。概念上的完整链与单次 resolver 输出不要混为一谈。

`result_analysis` 可以独立路由，但前提是当前主工作簿已经 accepted 且主结果质量门通过。若分析给出 `redo_required`，按原因回到 `model_design`、条件式 `data_preprocessing` 或 `solve_validate`，并传播下游 stale。

默认写作链在 `figure_evidence` 后进入 LaTeX。`writing_docx` 只由显式 DOCX/Word 请求加载，不是 LaTeX 前置。

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
```

解析结果返回 `module_terminal_outputs`、`pre_delivery_gates` 和 `terminal_outputs`。`semantic_governance` 在正式模型、代码、返回工作簿和下游交付前检查当前题意口径、语义闭环、复杂度复审和跨问 stale；`project_sync` 在正式产物交付时按 exact scope 检查产物、工作簿、图表链和哈希，不自动把质量门或分析状态提升为 passed。

赛题 Python 的执行权、full-fidelity 配置和禁止降采样/粗网格/短时域/少重复/宽容差/静默 solver fallback 等规则，以 `core/user_execution_contract.yaml` 为唯一事实源。
