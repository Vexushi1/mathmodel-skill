# Mathmodel Skill Repository Index v6.2.1

本文件是面向 AI、维护者和协作者的语义导航索引。它解决“应该先读什么、某类任务对应哪些文件”的问题；完整文件清单仍以 `HSK_SKILL_FILE_INDEX_V621.md` 为准。

## 1. 启动顺序

执行数学建模任务时，按以下顺序读取：

1. `core/hsk_core_policy.md`：全局硬规则与职责边界；
2. `core/workflow_router.yaml`：根据用户任务确定模块与 pack；
3. `core/module_manifest.yaml`：核对模块职责和依赖；
4. 仅加载命中的 `modules/`、`packs/` 与必要模板；
5. 不默认加载 `legacy/`。

根目录快捷入口：

- `AGENTS.md`：最短执行入口；
- `SKILL.md`：仓库级 Skill 说明；
- `skills/mathmodel-skill/SKILL.md`：插件安装入口；
- `HSK_RUNTIME_ROUTER_V621.md`：人类可读的路由摘要；
- `HSK_SKILL_FILE_INDEX_V621.md`：完整文件清单；
- `HSK_TEMPLATE_INDEX_V621.md`：模板索引；
- `PROJECT_INSTRUCTIONS_HSK_V621.md`：项目总指令；
- `CHANGELOG_V621.md`：版本变化。

## 2. 任务路由

| 用户任务 | 必读模块 | 常用补充 |
|---|---|---|
| 新赛题、完整建模、问题拆解 | `modules/01_problem_audit.md` | `packs/competition/auto.md`、`packs/task/classifier.md` |
| 模型路线、变量、假设、公式、约束 | `modules/02_model_design.md` | `packs/task/{classified_label}.md` |
| Python 求解、优化、仿真、统计检验 | `modules/03_solve_validate.md` | `packs/artifact/code.md`、题型 pack |
| 敏感性、鲁棒性、多算法验证 | `modules/03_solve_validate.md` | 题型 pack、`templates/review/robustness_check.md` |
| MATLAB 结果图、机理图、科研绘图 | `modules/04_figure_evidence.md` | `packs/artifact/figure.md`、`templates/figure/`、`templates/matlab/` |
| Word/DOCX 草稿 | `modules/05_writing/docx.md` | `packs/artifact/docx.md`、`templates/writing/` |
| LaTeX 终稿与编译 | `modules/05_writing/latex.md`、`modules/05_latex_compile_quality.md`、`modules/05_writing/ai_cleanup.md` | `packs/artifact/latex.md`、竞赛 pack、`templates/latex/` |
| 评分、终审、提交包 | `modules/06_review_delivery.md` | `packs/artifact/review.md` 或 `packs/artifact/full_submission.md` |

`{classified_label}` 只能替换为分类器返回的题型标签，不得一次加载全部题型 pack。

## 3. 题型 Pack

位于 `packs/task/`：

- `mechanism.md`：机理、几何、物理过程；
- `optimization.md`：规划、资源配置、路径与组合优化；
- `prediction.md`：时间序列、预测、趋势外推；
- `evaluation.md`：综合评价、排序、指标体系；
- `statistics_ml.md`：统计推断、回归、机器学习；
- `simulation.md`：蒙特卡罗、离散事件、系统仿真；
- `spatial.md`：空间计量、地理与空间关联；
- `graph_network.md`：图论、复杂网络、传播路径；
- `scheduling.md`：排程、调度、时空协同；
- `game_decision.md`：博弈、多主体决策；
- `classifier.md`：题型分类入口。

## 4. 竞赛 Pack

位于 `packs/competition/`：

- `auto.md`：按赛题与交付要求自动选择；
- `cumcm.md`：全国大学生数学建模竞赛；
- `mcm_icm.md`：MCM/ICM；
- `diangong.md`：电工杯；
- `certification_cup.md`：认证杯。

## 5. 交付物 Pack

位于 `packs/artifact/`：

- `code.md`：Python/MATLAB 代码交付；
- `figure.md`：结果图和机理图；
- `docx.md`：DOCX 草稿；
- `latex.md`：LaTeX 终稿；
- `review.md`：评分与审查；
- `full_submission.md`：完整复现与提交包。

## 6. 模板目录

- `templates/problem/`：题目要求覆盖、路线比较、数据审计；
- `templates/model/`：变量、假设、公式—代码闭环、约束违反检查；
- `templates/code/`：Python 起步脚本和 HSK 管线；
- `templates/matlab/`：读取结果工作簿、科研绘图和可选导出；
- `templates/figure/`：机理图与结果图合同、QA、论文闭环；
- `templates/writing/`：摘要、图后解释、DOCX、代码附录；
- `templates/latex/`：国赛、MCM/ICM、电工杯 LaTeX 模板；
- `templates/review/`：鲁棒性、代码精简、结果清单。

## 7. 核心输出契约

每个问题的标准结果目录为：

```text
结果数据表/
└─ 问题X/
   └─ 问题X结果数据/
      ├─ 问题X求解结果.xlsx
      └─ 问题X敏感性与鲁棒性结果.xlsx
```

Python 负责数据处理、模型求解、验证和工作簿输出；MATLAB 只读取工作簿绘制正式结果图，不重新计算核心结果。详细约束见 `core/output_contract.yaml` 和 `core/hsk_core_policy.md`。

## 8. 维护与读取规则

1. 新增、删除或移动文件后，同步更新 `HSK_SKILL_FILE_INDEX_V621.md`；
2. 路由关系变化时，优先修改 `core/workflow_router.yaml`，再同步本索引；
3. 全局规则只写入 `core/hsk_core_policy.md`，模块不得复制出冲突版本；
4. `legacy/` 仅用于历史追溯、差异核验或迁移，不参与默认执行；
5. GitHub 代码搜索索引未完成或延迟时，直接按本文件给出的路径调用 `fetch_file`；
6. 阅读顺序以最小必要加载为原则，避免全仓库扫描导致上下文污染。
