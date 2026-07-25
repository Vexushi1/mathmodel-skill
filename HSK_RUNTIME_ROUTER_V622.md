# HSK Runtime Router v6.2.5

文件名保留 V622 作为稳定兼容路径；机器事实源仍为 `core/workflow_router.yaml`。

## 永久加载

- `core/hsk_core_policy.md`
- `core/workflow_router.yaml`
- `core/module_manifest.yaml`

## 当前项目入口

若 `locked_model_spec` 已形成，额外优先读取项目根目录 `模型论文框架.md`。它只保留当前有效模型、论文结构、逐问结果摘要和图表映射；发生变化时删除旧内容并完整替换。每次正式交付同步完整最新版。

## 机器可读契约

- 输出目录、框架同步与 MATLAB 标题：`core/output_contract.yaml`
- 工作簿结构与 capability 条件：`core/workbook_schema.yaml`
- 逐问项目状态、框架/结果摘要状态：`core/project_state.schema.yaml`
- 框架模板：`templates/model/model_paper_framework.md`
- LaTeX 模板入口与编译：`core/compile_profiles.yaml`

## 按需加载

| 用户任务 | 模块与补充 |
|---|---|
| 新赛题、审题、问题拆解 | `modules/01_problem_audit.md` |
| 模型路线、变量、公式、数据方案 | `modules/02_model_design.md` + 每问主/次题型 Pack + `templates/model/model_paper_framework.md` |
| 模型论文框架、结果摘要或模型/参数/约束变更同步 | `modules/02_model_design.md` + `templates/model/model_paper_framework.md` |
| W-DRO、MPEC、ALNS、GNN、DML、强化学习等高级方法 | `modules/02_model_design.md` + `packs/task/advanced_method_gate.md` + 对应题型 Pack |
| Python 代码、求解、检验、敏感性与鲁棒性 | `modules/03_solve_validate.md` + 对应题型 Pack；完成后同步结果摘要 |
| MATLAB 结果图、机理图、图表优化 | `modules/04_figure_evidence.md` + `templates/figure/chart_selection.md`；单图 `title`、多面板 `sgtitle`；视觉参考按需读取 `assets/figure_assets.yaml` |
| Word/DOCX 草稿 | `modules/05_writing/docx.md` + `templates/writing/docx_check.md`；先读取 current 框架 |
| LaTeX 终稿 | `modules/05_writing/latex.md` → `modules/05_writing/ai_cleanup.md` → `modules/05_latex_compile_quality.md`；先读取 current 框架 |
| 评分、终审、提交检查 | `modules/06_review_delivery.md` + `scripts/score_submission.py` + 框架/状态/产物校验器 |

分类器按小问输出一个主标签和最多两个必要次标签，并单独输出 capability 标志。项目题目、附件、`模型论文框架.md` 和 Python 脚本位于项目根目录；每问两类工作簿和 `q{x}_plot.m` 统一位于 `结果数据表/问题X/`，正式图位于同目录 `图表/`。禁止默认创建 `问题X结果数据/`，禁止默认加载 `legacy/`。
