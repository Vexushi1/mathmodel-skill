# HSK Runtime Router

机器路由以 `core/workflow_router.yaml` 为唯一事实源。

## 启动

```text
读取 core/bootstrap.yaml
→ 调用 scripts/resolve_workflow.py
→ 合并多个意图
→ 确定 objective / structures / 顶层 capabilities
→ 加载必要模块、Pack、模板
→ 到用户要求的模块产物停止
→ 执行 pre_delivery_gates
→ gate 成功后暴露 project_state / sync_report
```

默认完整流程严格按以下顺序：

```text
problem_audit
→ model_design
→ solve_validate
→ result_analysis
→ figure_evidence
→ writing_latex
→ ai_cleanup
→ latex_compile_quality
→ review_delivery
```

`solve_validate` 表示完整主求解和主结果质量门；`result_analysis` 表示在已通过质量门的结果上选择题目专属深化分析。二者不得倒序，也不得由统一扰动实验替代。

`result_analysis` 可以独立路由，但前提是当前 `solution_workbook` 和 `result_quality_report` 已有效。若分析给出 `redo_required`，路由返回 `model_design` 或 `solve_validate`，并将后续图表和写作产物标记 stale。

默认完整流程在 `figure_evidence` 后直接进入 LaTeX。`writing_docx` 不在默认顺序中，仅由显式 DOCX/Word 请求加载，且不是 LaTeX 前置。

Python starter 使用：

```text
run_primary_pipeline
→ 主结果质量门
→ run_result_analysis_pipeline
```

`run_pipeline()` 仅作为顺序编排器存在，不重新合并两个阶段的职责。

## 示例

```bash
python scripts/resolve_workflow.py code_and_solution figures \
  --objective optimization \
  --structures stochastic \
  --competition CUMCM

python scripts/resolve_workflow.py result_analysis \
  --objective prediction \
  --structures temporal
```

解析结果返回 `module_terminal_outputs`、`pre_delivery_gates` 和 `terminal_outputs`。`project_sync` 是 utility gate，不属于主求解或结果深化分析模块；它按 exact scope 检查产物、工作簿、图表链和哈希，不得自动把质量门或分析状态提升为 passed。
## v6.5.0 用户执行完整版代码

默认不由助手运行赛题主求解或结果深化分析程序。助手交付题目专属完整版代码、完整运行配置和本地说明，用户运行后返回标准工作簿；工作簿通过运行配置、代码/数据哈希和质量门验收后，工作流才继续。禁止自动降采样、粗网格、短时域、少重复、宽容差、静默求解器 fallback 或用轻量结果代替正式结果。
