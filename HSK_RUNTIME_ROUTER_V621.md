# HSK Runtime Router v6.2.1

## 永久加载

- `core/hsk_core_policy.md`
- `core/workflow_router.yaml`

## 按需加载

| 用户任务 | 模块 |
|---|---|
| 新赛题、审题、问题拆解 | `modules/01_problem_audit.md` |
| 模型路线、变量、公式、数据方案 | `modules/02_model_design.md` |
| Python 代码、求解、检验、敏感性与鲁棒性 | `modules/03_solve_validate.md` |
| MATLAB 结果图、机理图、图表优化 | `modules/04_figure_evidence.md` |
| Word/DOCX 草稿 | `modules/05_writing/docx.md` |
| LaTeX 终稿 | `modules/05_writing/latex.md` + `modules/05_latex_compile_quality.md` + `modules/05_writing/ai_cleanup.md` |
| 评分、终审、提交检查 | `modules/06_review_delivery.md` |

每问结果统一读取/写入 `结果数据表/问题X/问题X结果数据/`。再按题型、竞赛和交付物加载对应 pack。禁止默认加载 `legacy/`。
