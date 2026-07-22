# Mathmodel Skill Repository Index v6.2.4

本文件是面向 AI、维护者和协作者的语义导航索引。完整活动文件清单以 `HSK_SKILL_FILE_INDEX_V622.md` 为准；该兼容文件名的标题显示当前版本。历史文件只通过 `legacy/README.md` 追溯。

## 1. 启动顺序

1. `core/hsk_core_policy.md`：全局硬规则与职责边界；
2. `core/workflow_router.yaml`：根据用户任务确定模块；
3. `core/module_manifest.yaml`：核对产物生产者、消费者与门槛；
4. `packs/task/classifier.md`：按小问输出主/次题型与 capability；
5. 仅加载命中的 `modules/`、`packs/` 与必要模板/视觉资产；
6. 不默认加载 `legacy/`。

根目录快捷入口：

- `AGENTS.md`：最短执行入口；
- `SKILL.md`：仓库级 Skill 说明；
- `skills/mathmodel-skill/SKILL.md`：插件安装入口；
- `HSK_RUNTIME_ROUTER_V622.md`：人类可读路由摘要；
- `HSK_SKILL_FILE_INDEX_V622.md`：活动文件清单；
- `HSK_TEMPLATE_INDEX_V622.md`：活动模板索引；
- `PROJECT_INSTRUCTIONS_HSK_V622.md`：项目调用说明；
- `CHANGELOG_V622.md`：版本变化。

## 2. 机器可读契约

| 契约 | 作用 |
|---|---|
| `core/module_manifest.yaml` | 模块产物目录、生产者—消费者闭环和终点产物 |
| `core/output_contract.yaml` | 项目目录、文件名、软件职责与元数据条件 |
| `core/workbook_schema.yaml` | 工作表、字段、单位、非空、capability 和 MATLAB 交接 |
| `core/project_state.schema.yaml` | 每问状态、题型、能力、哈希、证据与阶段门槛 |
| `core/compile_profiles.yaml` | 模板入口、项目入口及 LaTeX 编译链 |

## 3. 任务路由

| 用户任务 | 必读模块 | 常用补充 |
|---|---|---|
| 新赛题、完整建模、问题拆解 | `modules/01_problem_audit.md` | `packs/competition/auto.md`、`packs/task/classifier.md` |
| 模型路线、变量、假设、公式、约束 | `modules/02_model_design.md` | 每问分类器命中的主/次题型 Pack |
| 高级方法 | `modules/02_model_design.md` | `packs/task/advanced_method_gate.md` + 对应题型 Pack |
| Python 求解、优化、仿真、统计检验 | `modules/03_solve_validate.md` | `packs/artifact/code.md`、工作簿 Schema |
| 敏感性、鲁棒性、多算法验证 | `modules/03_solve_validate.md` | 题型 Pack、`templates/review/robustness_check.md` |
| MATLAB 结果图、机理图、科研绘图 | `modules/04_figure_evidence.md` | 图型选择、Figure Contract、按需 `assets/figure_assets.yaml` |
| Word/DOCX 草稿 | `modules/05_writing/docx.md` | `templates/writing/docx_check.md` |
| LaTeX 终稿与编译 | `modules/05_writing/latex.md` → `ai_cleanup.md` → `modules/05_latex_compile_quality.md` | `packs/artifact/latex.md`、竞赛 Pack |
| 评分、终审、提交包 | `modules/06_review_delivery.md` | `scripts/score_submission.py`、审查/提交 Pack |

确定性加载计划：

```bash
python scripts/resolve_workflow.py full_solution --primary mechanism --secondary optimization --competition CUMCM
```

## 4. 题型与能力

十类题型 Pack 位于 `packs/task/`：`mechanism`、`optimization`、`prediction`、`evaluation`、`statistics_ml`、`simulation`、`spatial`、`graph_network`、`scheduling`、`game_decision`。

题型决定变量、模型和专项结果；capability 单独决定：显式约束/可行性、均衡残差、守恒残差、离散精度和收敛诊断。两者按小问写入 `state/project_state.yaml`。

## 5. 竞赛与交付 Pack

竞赛 Pack：`auto.md`、`cumcm.md`、`mcm_icm.md`、`diangong.md`、`certification_cup.md`。

交付 Pack：`code.md`、`figure.md`、`docx.md`、`latex.md`、`review.md`、`full_submission.md`。

## 6. 模板与工具

- `templates/problem/`：要求覆盖、路线比较、数据审计；
- `templates/model/`：变量、假设、公式—代码闭环和适用检查；
- `templates/code/`：项目根目录 Python 起步管线与标准工作簿写入；
- `templates/matlab/`：同目录工作簿读取、单文件科研绘图和可选导出；
- `templates/figure/`：图型选择、机理图与结果图合同、QA、论文闭环；
- `templates/writing/`：摘要、图表解释、DOCX 检查、代码附录；
- `templates/latex/`：国赛、MCM/ICM、电工杯模板；
- `scripts/validate_project_state.py`：项目状态语义校验；
- `scripts/hsk_check_artifact.py`：根目录 Python、逐问工作簿、同目录 MATLAB、图像和状态检查；
- `scripts/score_submission.py`：六维评分与硬否决；
- `scripts/generate_indexes.py`：活动索引与 Manifest。

## 7. 核心输出契约

```text
项目根目录/
├─ 赛题与附件
├─ 问题一求解.py
└─ 结果数据表/
   └─ 问题一/
      ├─ 问题一求解结果.xlsx
      ├─ 问题一敏感性与鲁棒性结果.xlsx
      ├─ q1_plot.m
      └─ 图表/
```

Python 代码与赛题、附件同放项目根目录；每问两类工作簿和唯一 MATLAB 入口直接位于 `结果数据表/问题X/`；MATLAB 正式图写入同级 `图表/`。不再默认创建 `数据/`、`Python求解/`、`MATLAB绘图/` 或“问题X结果数据”重复层级。所有工作表必须非空；不适用分析写入 `适用性说明`。

## 8. 维护规则

1. 新增、删除或移动活动文件后运行 `scripts/generate_indexes.py`；
2. 路由关系变化时先修改 `core/workflow_router.yaml` 与 `core/module_manifest.yaml`；
3. 全局规则只写入 `core/hsk_core_policy.md`；
4. `legacy/` 不参与活动索引、Manifest 和默认执行；
5. GitHub 代码搜索延迟时按本文件路径直接读取；
6. 变更必须通过静态 lint、Python 3.10–3.14 单元测试、Schema、生成文件及三套 LaTeX 冒烟编译。
