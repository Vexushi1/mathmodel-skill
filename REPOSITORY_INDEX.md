# Mathmodel Skill Repository Index v6.2.2

本文件是面向 AI、维护者和协作者的语义导航索引。它解决“应该先读什么、某类任务对应哪些文件”的问题；完整文件清单以 `HSK_SKILL_FILE_INDEX_V622.md` 为准。

## 1. 启动顺序

执行数学建模任务时，按以下顺序读取：

1. `core/hsk_core_policy.md`：全局硬规则与职责边界；
2. `core/workflow_router.yaml`：根据用户任务确定模块与题型 Pack；
3. `core/module_manifest.yaml`：核对模块职责、依赖和机器可读契约；
4. 仅加载命中的 `modules/`、`packs/` 与必要模板；
5. 不默认加载 `legacy/`。

根目录快捷入口：

- `AGENTS.md`：最短执行入口；
- `SKILL.md`：仓库级 Skill 说明；
- `skills/mathmodel-skill/SKILL.md`：插件安装入口；
- `HSK_RUNTIME_ROUTER_V622.md`：人类可读的路由摘要；
- `HSK_SKILL_FILE_INDEX_V622.md`：完整文件清单；
- `HSK_TEMPLATE_INDEX_V622.md`：模板索引；
- `PROJECT_INSTRUCTIONS_HSK_V622.md`：项目总指令；
- `CHANGELOG_V622.md`：版本变化。

## 2. 机器可读契约

| 契约 | 作用 |
|---|---|
| `core/output_contract.yaml` | 项目目录、文件名、软件职责与元数据条件 |
| `core/workbook_schema.yaml` | 工作表、字段、单位、非空规则与 MATLAB 交接 |
| `core/project_state.schema.yaml` | 跨聊天项目状态及阶段门槛 |
| `core/compile_profiles.yaml` | CUMCM、MCM/ICM、电工杯的 LaTeX 编译链 |

## 3. 任务路由

| 用户任务 | 必读模块 | 常用补充 |
|---|---|---|
| 新赛题、完整建模、问题拆解 | `modules/01_problem_audit.md` | `packs/competition/auto.md`、`packs/task/classifier.md` |
| 模型路线、变量、假设、公式、约束 | `modules/02_model_design.md` | 分类器命中的主/次题型 Pack |
| Python 求解、优化、仿真、统计检验 | `modules/03_solve_validate.md` | `packs/artifact/code.md`、题型 Pack、工作簿 Schema |
| 敏感性、鲁棒性、多算法验证 | `modules/03_solve_validate.md` | 题型 Pack、`templates/review/robustness_check.md` |
| MATLAB 结果图、机理图、科研绘图 | `modules/04_figure_evidence.md` | `packs/artifact/figure.md`、`templates/figure/`、`templates/matlab/` |
| Word/DOCX 草稿 | `modules/05_writing/docx.md` | `packs/artifact/docx.md`、`templates/writing/` |
| LaTeX 终稿与编译 | `modules/05_writing/latex.md`、`modules/05_latex_compile_quality.md`、`modules/05_writing/ai_cleanup.md` | `packs/artifact/latex.md`、竞赛 Pack、`templates/latex/` |
| 评分、终审、提交包 | `modules/06_review_delivery.md` | `packs/artifact/review.md` 或 `packs/artifact/full_submission.md` |

分类器输出一个主标签和最多两个必要次标签。次标签只有在会改变变量、约束、验证方法或交付物时才加载；不得一次加载全部题型 Pack。

## 4. 题型 Pack

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

## 5. 竞赛与交付 Pack

竞赛 Pack 位于 `packs/competition/`：`auto.md`、`cumcm.md`、`mcm_icm.md`、`diangong.md`、`certification_cup.md`。

交付 Pack 位于 `packs/artifact/`：`code.md`、`figure.md`、`docx.md`、`latex.md`、`review.md`、`full_submission.md`。

## 6. 模板目录

- `templates/problem/`：题目要求覆盖、路线比较、数据审计；
- `templates/model/`：变量、假设、公式—代码闭环、约束违反检查；
- `templates/code/`：Python 起步脚本和 HSK 管线；
- `templates/matlab/`：项目根定位、工作簿读取、科研绘图和可选导出；
- `templates/figure/`：机理图与结果图合同、QA、论文闭环；
- `templates/writing/`：摘要、图后解释、DOCX、代码附录；
- `templates/latex/`：国赛、MCM/ICM、电工杯 LaTeX 模板；
- `templates/review/`：鲁棒性、代码精简、结果清单。

## 7. 核心输出契约

```text
结果数据表/
└─ 问题X/
   └─ 问题X结果数据/
      ├─ 问题X求解结果.xlsx
      └─ 问题X敏感性与鲁棒性结果.xlsx
```

Python 负责数据处理、模型求解、验证和工作簿输出；MATLAB 只读取工作簿绘制正式结果图，不重新计算核心结果。所有工作表必须非空；不适用分析写入 `适用性说明`。

## 8. 维护与读取规则

1. 新增、删除或移动文件后，由 `.github/workflows/refresh-generated.yml` 调用 `scripts/generate_indexes.py` 自动更新 V622 文件索引、模板索引和 `MANIFEST.sha256`；
2. 路由关系变化时先修改 `core/workflow_router.yaml`，再同步本语义索引；
3. 全局规则只写入 `core/hsk_core_policy.md`，模块不得复制出冲突版本；
4. `legacy/` 仅用于历史追溯、差异核验或迁移，不参与默认执行；
5. GitHub 代码搜索索引未完成或延迟时，直接按本文件给出的路径调用 `fetch_file`；
6. 阅读顺序以最小必要加载为原则，避免全仓库扫描导致上下文污染；
7. 变更必须通过 Python 3.10–3.14 CI、Schema 验证和生成文件一致性检查。
