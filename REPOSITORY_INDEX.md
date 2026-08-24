# Mathmodel Skill Repository Index

## 启动

1. `core/bootstrap.yaml`：最小启动契约；
2. `scripts/resolve_workflow.py`：一个或多个意图的确定性执行计划；
3. `core/hsk_core_policy.md`：全局硬规则；
4. `core/task_taxonomy.yaml`：objective、structures、capabilities；
5. `core/module_manifest.yaml`：模块与 utility gate 产物闭环；
6. 仅加载命中的模块、Pack 和模板；
7. 正式交付前执行解析结果中的 `pre_delivery_gates`。

## 活动入口

| 文件 | 作用 |
|---|---|
| `PROJECT_INSTRUCTIONS.md` | 项目调用说明 |
| `RUNTIME_ROUTER.md` | 运行时路由说明 |
| `SKILL_FILE_INDEX.md` | 活动 Skill 文件索引 |
| `TEMPLATE_INDEX.md` | 活动模板索引 |

旧 `V622` 文件只保留兼容指针，不再承载活动规则，也不计入 Active Skill Index、Active MANIFEST 或活动 REQUIRED 集合；默认 resolver 不加载这些文件。

## 默认写作策略

默认完整流程在求解、验证和图表锁定后直接进入 LaTeX。`modules/05_writing/docx.md` 与 `docx` delivery scope 保留，但仅在用户明确要求 Word 审阅、批注、协作或特定提交格式时加载；DOCX 不是 LaTeX 前置。

跨竞赛正文推理只认 `core/writing_reasoning_contract.yaml`，正文结构与表达只认 `modules/05_writing/latex.md`。Algorithm Trace 的 `not_needed / stepwise / pseudocode` 三态由前者治理；`packs/artifact/algorithm_flow.md` 仅在算法流程写作或终审需要时提供控制流伪代码和分阶段数学步骤的载体细则，不建立第二套算法规则。

## 仓库修改

任何聊天、Agent 或人工维护者准备修改活动文件时，必须先从 `main` 读取：

1. `core/bootstrap.yaml`；
2. `SKILL_CHANGE_GOVERNANCE.md`。

随后确认当前版本、最新提交、重叠 PR 和权威事实源，先形成修改简报，再创建独立分支与单主题 PR。禁止依赖旧聊天记忆、直接写 `main`、复制多份硬规则或手工伪造生成文件。

## 常用任务

| 任务 | 入口 |
|---|---|
| 新赛题与审题 | `modules/01_problem_audit.md` |
| 模型路线、变量、假设、公式、约束 | `modules/02_model_design.md` |
| 论文算法流程、Algorithm Trace、伪代码/Step 流程 | `core/writing_reasoning_contract.yaml` + `packs/artifact/algorithm_flow.md`，按需加载 |
| Python主求解与题目专属结果深化分析 | `modules/03_solve_validate.md`、`modules/03_result_analysis.md` |
| Python题型 starter | `templates/code/starter/` + `templates/code/hsk_pipeline/` |
| MATLAB结果图与机理图 | `modules/04_figure_evidence.md` |
| 默认 LaTeX 写作 | `modules/05_writing/latex.md` |
| 可选 DOCX 审阅 | `modules/05_writing/docx.md` |
| 终审与提交包 | `modules/06_review_delivery.md` |
| 命题证明 | `packs/artifact/proposition_proof.md`，仅按需加载 |
| 项目状态与产物同步 | `scripts/sync_project.py` |
| Skill 修改治理 | `SKILL_CHANGE_GOVERNANCE.md` |

## 机器契约

| 文件 | 作用 |
|---|---|
| `core/bootstrap.yaml` | 最小入口、权威源指针与仓库维护入口 |
| `core/task_taxonomy.yaml` | 正交分类与旧Pack映射 |
| `core/workflow_router.yaml` | 多意图路由、交付scope与显式同步门槛 |
| `core/module_manifest.yaml` | 模块输入输出、utility gate及terminal output闭环 |
| `core/output_contract.yaml` | 目录、写作策略、分层哈希、阶段产物与MATLAB证据链 |
| `core/writing_reasoning_contract.yaml` | Formula/Algorithm Trace、规则等级、命题、术语、数值、Title Claim、深化证据、Paragraph Necessity、局部 stale 与 Citation Evidence |
| `core/global_preprocessing_contract.yaml` | 三态预处理判定、处理证据和 `data_process.m` 边界 |
| `core/user_execution_contract.yaml` | 用户 full-fidelity 执行与返回工作簿验收 |
| `core/code_quality_contract.yaml` | 题目专属 Python 工程质量 |
| `core/workbook_schema.yaml` | objective/structure/capability工作簿条件与精确表头交接 |
| `core/project_state.schema.yaml` | 单一capability事实源、分层哈希、stale和框架状态 |

## 工具

- `scripts/resolve_workflow.py`：多意图合并、模块排序、前置缺口与 `pre_delivery_gates`；
- `scripts/validate_semantic_governance.py`：题意口径、语义闭环、复杂度复审、semantic revision 与跨问 stale 门；
- `scripts/validate_code_delivery.py`：分别静态校验每问主求解与结果深化分析两个 Python 脚本；
- `scripts/validate_user_execution.py`：验收两个标准工作簿及运行配置、哈希和质量门；
- `scripts/sync_project.py`：阶段产物发现、工作簿Schema、图表链、分层哈希和stale；
- `scripts/validate_project_state.py`：分类兼容、哈希与状态语义；
- `scripts/validate_model_paper_framework.py`：compact/full 模式、Algorithm Trace 与项目记忆确定性校验；
- `scripts/audit_latex_project.py`：正式 LaTeX 项目审计入口，递归覆盖模块化源码并委托 prose/BibTeX/framework 检查；
- `scripts/audit_paper_prose.py`：上述入口使用的底层成稿结构、引用、登记术语/Numeric Profile 保守审查实现；
- `scripts/latex_delivery.py`：维护 formal source/audit/profile/log/PDF attestation 的哈希与新鲜度验证；
- `scripts/render_paper.py`：按活动 compile profile 执行正式 audit → compile → compile-report 交付链；
- `scripts/hsk_pack_submission.py`：按 competition profile 生成 official 或 reproducibility submission package 与 manifest；
- `scripts/validate_submission_package.py`：验证 submission manifest、归档实际内容及其与当前项目/PDF 的绑定哈希；
- `scripts/lint_skill.py`：版本、路径、生产者—消费者、route load、gate和语义闭环；
- `scripts/score_submission.py`：评委式评分。

完整活动文件清单见 `SKILL_FILE_INDEX.md`；历史只通过 `legacy/README.md` 与 Git 历史追溯。
