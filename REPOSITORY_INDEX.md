# Mathmodel Skill Repository Index v6.3.0

## 启动

1. `core/bootstrap.yaml`：最小启动契约；
2. `scripts/resolve_workflow.py`：一个或多个意图的确定性加载计划；
3. `core/hsk_core_policy.md`：全局硬规则；
4. `core/task_taxonomy.yaml`：objective、structures、capabilities；
5. `core/module_manifest.yaml`：产物闭环；
6. 仅加载命中的模块、Pack 和模板；
7. 正式交付前运行 `scripts/sync_project.py`。

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

## 机器契约

| 文件 | 作用 |
|---|---|
| `core/bootstrap.yaml` | 最小入口与权威源指针 |
| `core/task_taxonomy.yaml` | 正交分类与旧Pack映射 |
| `core/workflow_router.yaml` | 多意图路由、自然语言关键词与正式交付标志 |
| `core/module_manifest.yaml` | 模块输入输出、sync_report和同步门槛 |
| `core/output_contract.yaml` | 目录、框架compact/full、同步器和MATLAB读取规则 |
| `core/workbook_schema.yaml` | 工作表、字段、capability条件和精确表头交接 |
| `core/project_state.schema.yaml` | classification、哈希、stale、框架和产物状态 |

## 工具

- `scripts/resolve_workflow.py`：多意图合并、Pack去重、模块排序和前置缺口；
- `scripts/sync_project.py`：产物发现、工作簿结构、哈希、stale和同步报告；
- `scripts/validate_project_state.py`：状态语义；
- `scripts/validate_model_paper_framework.py`：框架结构；
- `scripts/hsk_check_artifact.py`：交付物检查；
- `scripts/score_submission.py`：评委式评分。

完整活动文件清单仍使用兼容文件名 `HSK_SKILL_FILE_INDEX_V622.md`；历史只通过 `legacy/README.md` 追溯。
