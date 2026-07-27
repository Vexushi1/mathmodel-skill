# Mathmodel Skill Repository Index v6.3.2

## 启动

1. `core/bootstrap.yaml`：最小启动契约；
2. `scripts/resolve_workflow.py`：一个或多个意图的确定性执行计划；
3. `core/hsk_core_policy.md`：全局硬规则；
4. `core/task_taxonomy.yaml`：objective、structures、capabilities；
5. `core/module_manifest.yaml`：模块与 utility gate 产物闭环；
6. 仅加载命中的模块、Pack 和模板；
7. 正式交付前执行解析结果中的 `pre_delivery_gates`。

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
| Python求解、验证、敏感性与鲁棒性 | `modules/03_solve_validate.md` |
| MATLAB结果图与机理图 | `modules/04_figure_evidence.md` |
| DOCX / LaTeX | `modules/05_writing/` |
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
| `core/output_contract.yaml` | 目录、框架模式、分层哈希、阶段产物与MATLAB证据链 |
| `core/workbook_schema.yaml` | objective/structure/capability工作簿条件与精确表头交接 |
| `core/project_state.schema.yaml` | 单一capability事实源、分层哈希、stale和框架状态 |

## 工具

- `scripts/resolve_workflow.py`：多意图合并、模块排序、前置缺口与 `pre_delivery_gates`；
- `scripts/sync_project.py`：阶段产物发现、工作簿Schema、图表链、分层哈希和stale；
- `scripts/validate_project_state.py`：分类兼容、哈希与状态语义；
- `scripts/validate_model_paper_framework.py`：compact/full模式感知校验；
- `scripts/hsk_check_artifact.py`：交付物检查；
- `scripts/lint_skill.py`：版本、路径、生产者—消费者、gate和语义闭环；
- `scripts/score_submission.py`：评委式评分。

完整活动文件清单仍使用兼容文件名 `HSK_SKILL_FILE_INDEX_V622.md`；历史只通过 `legacy/README.md` 追溯。
