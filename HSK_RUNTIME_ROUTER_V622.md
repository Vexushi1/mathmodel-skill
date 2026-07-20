# HSK Runtime Router v6.2.2

## 永久加载

- `core/hsk_core_policy.md`
- `core/workflow_router.yaml`

## 机器可读契约

- 输出目录与职责：`core/output_contract.yaml`
- 工作簿结构：`core/workbook_schema.yaml`
- 项目状态：`core/project_state.schema.yaml`
- LaTeX 编译：`core/compile_profiles.yaml`

## 按需加载

| 用户任务 | 模块与补充 |
|---|---|
| 新赛题、审题、问题拆解 | `modules/01_problem_audit.md` |
| 模型路线、变量、公式、数据方案 | `modules/02_model_design.md` + 主/次题型 Pack |
| W-DRO、MPEC、ALNS、GNN、DML、强化学习等高级方法 | `modules/02_model_design.md` + `packs/task/advanced_method_gate.md` + 对应题型 Pack |
| Python 代码、求解、检验、敏感性与鲁棒性 | `modules/03_solve_validate.md` + 对应题型 Pack |
| MATLAB 结果图、机理图、图表优化 | `modules/04_figure_evidence.md` + `templates/figure/chart_selection.md` |
| Word/DOCX 草稿 | `modules/05_writing/docx.md` + `templates/writing/docx_check.md` |
| LaTeX 终稿 | `modules/05_writing/latex.md` + `modules/05_latex_compile_quality.md` + `modules/05_writing/ai_cleanup.md` |
| 评分、终审、提交检查 | `modules/06_review_delivery.md` |

题型分类输出一个主标签和最多两个必要次标签，只加载会改变变量、约束、验证或交付物的题型 Pack。高级方法不是题型标签，仅在用户明确提出或路线 B 准备作为主模型时加载准入 Pack。多意图任务按“审题 → 设计 → 求解验证 → 图表 → 写作 → 终审”合并模块并去重。

每问结果统一读取/写入 `结果数据表/问题X/问题X结果数据/`。禁止默认加载 `legacy/`。