# mathmodel-skill v10.3.0

HSK 数学建模工作流覆盖审题与 Problem Contract、条件驱动结构化简、最小充分的 `proposed_model_spec`、独立 Model Reviewer / Devil's Advocate、`awaiting_model_approval` 到用户明确批准后的 `locked_model_spec`，以及数值求解、证据绘图、论文和终稿交付。每问保留自己的数学模型、算法、源码与结果；数值语言由项目根策略统一选择。仓库改造不代表任何具体项目已完成后端选择、迁移或数值验收。

## 最短启动

1. 从根目录 `SKILL.md` 或打包入口 `skills/mathmodel-skill/SKILL.md` 进入，先读 `core/bootstrap.yaml`，再按 `core/workflow_router.yaml` 加载全局政策。
2. 运行 `scripts/resolve_runtime.py`，按任务和当前项目恢复最小 `reading_plan`、Authority 与 `pre_delivery_gates`。已有项目传入 `--project-root`，需要定位小问时传入 `--question`；只读取 resolver 当前返回的资源。
3. 模型设计先完成语义闭环、Model Challenge 和当前 `semantic_revision` / validated `semantic_identity_hash` 的 Human Model Approval。数据项目先审计，再按证据确定 `preprocessing_decision`；锁模不等于代码交付资格。
4. 生成、核验和交付时执行 resolver 返回的完整且有序的 `pre_delivery_gates`。当前 `模型论文框架.md` 是语义工作记忆，`state/project_state.yaml` 是机器状态，accepted workbook 是具体数值事实；三者不能互相代替。

## 项目数值职责

项目根 `execution.solver_backend` 和非空理由记录一次 Python 或 MATLAB 选择。首次选择先审视全题可预见数值需求并衔接 Model Approval：`scripts/project_solver_backend.py inspect` 只读，完全未选且无数值历史用 `select`；有历史数值阶段或更换已锁后端时，先预览全题影响，再经针对该项目原状态与影响摘要的明确确认执行 `migrate`。`auto`、旧阶段声明及 `RUN_CONFIG` / `RUN_RECEIPT` 中的运行事实都不会自动选值。操作边界只服从 `core/user_execution_contract.yaml`。

每问在已选项目后端下交付独立主求解入口，按 Primary Quality Specification (PQS) 保存本次运行的 Primary Evidence Capture；返回主工作簿通过独立数值复核后才可成为 accepted。Analysis Necessity Gate 判定 `required` 时，独立结果深化入口继承同一后端，产生 Analysis Evidence Capture；`not_required` 记录理由，不生成深化结果，也不声称已验证稳健性。精确入口名、工作簿和条件式产物只看 `core/output_contract.yaml#per_question.solver_scripts`；不按固定 Python 文件清单或统一五文件数推断当前资格。赛题数值代码由用户本地 `full_fidelity` 执行，助手生成、静态检查并验收返回证据。

项目级预处理仍是独立的 Python 职责。正式 MATLAB 结果绘图只消费当前 accepted 工作簿与已验收证据，不重求解、不制造序列；非数据驱动的题目专属机理图可按 Figure Authority 选择可编辑 draw.io。图内正式标题由论文 caption 承担，实际渲染和语义检查不能由静态检查替代。

## 可选 Code ↔ Model 结构核验（A1）

`python scripts/model_code_conformance.py <项目根> --question Q1 --stage primary` 只读核对当前批准SIB、阶段源码bundle和`implementation_conformance`覆盖声明。`--inventory`只列当前可定位对象与源码锚点，不自动生成已验证映射。范围、状态与限制见`core/model_code_conformance_contract.yaml`；使用说明见`templates/model/formula_code_closure.md`。

`structure_verified`只表示记录/身份/静态引用闭合，不证明约束实际启用、数学等价或数值正确。没有记录为`not_assessed`；未支持结构为`needs_review`；旧记录、冲突或残缺声明阻断本次结构核验。A1 独立入口仍只读；A2 仅对显式启用阶段在现有交付/回执链中消费该结果，未启用项目不增加强制门。B/C/D 增强尚未完成。

## 唯一 Authority 导航

| 职责 | 当前规则 |
|---|---|
| 启动、路由和项目恢复 | `core/bootstrap.yaml`、`core/workflow_router.yaml`、`core/runtime_assurance_contract.yaml`、`core/project_state.schema.yaml` |
| Problem Contract、模型设计与批准 | `modules/01_problem_audit.md`、`modules/02_model_design.md`、`core/model_approval_contract.yaml` |
| 数据审计与条件式预处理 | `core/global_preprocessing_contract.yaml` |
| 项目后端、用户执行和精确交付入口 | `core/user_execution_contract.yaml`、`core/output_contract.yaml`、`core/workbook_schema.yaml` |
| 主结果内在数值有效性 | `core/numerical_verification_contract.yaml` |
| 结果深化、MATLAB 证据图和机理图 | `modules/03_result_analysis.md`、`modules/04_figure_evidence.md` |
| 普通正文结构与表达 | `modules/05_writing/paper_writing_protocol.md`：普通正文结构与表达 |
| LaTeX 载体 | `modules/05_writing/latex.md`：LaTeX Adapter 与载体接口 |
| 复杂数学与证据裁决 | `core/writing_reasoning_contract.yaml`；Algorithm Trace 的 `not_needed / stepwise / pseudocode` 呈现按需读取 `packs/artifact/algorithm_flow.md` |
| 最终审查与交付 | `modules/06_review_delivery.md`、`core/output_contract.yaml` 和 resolver 返回的门 |

这些路径负责当前规范。README 只提供入口和职责导航，不替它们设第二套规则。

## 最少检查命令

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests
python scripts/generate_indexes.py --check
python scripts/project_solver_backend.py --help
```

针对项目的模型批准、数值验收、论文编译与提交包门以 resolver 当前返回的 `pre_delivery_gates` 为准；静态测试、真实 MATLAB 执行、渲染验收和远程 CI 分别记录，不能互相替代。

## 兼容与历史

旧项目和旧命名仅按各 Authority 的只读兼容条款恢复；重新进入当前阶段时补齐该阶段门禁，不倒填历史批准或把仓库升级当成用户项目迁移。`legacy/` 不进入默认执行链。逐版本变更见 [CHANGELOG](CHANGELOG.md) 与 [Git 提交历史](https://github.com/Vexushi1/mathmodel-skill/commits/main/)；v9 逐问后端的原貌和修复记录见 [v9.7.0 迁移说明](docs/v970_solver_backends_migration.md)、[v9.7.1 审计](docs/v971_backend_contract_audit.md)。

保留的专题资料入口：[绘图技巧与交接计划](docs/figure_technique_and_handoff_refactor_plan.md)、[仓库审计与交接计划](docs/repository_audit_and_handoff_refactor_plan.md)、[v8.4 写作评估](docs/v840_author_reasoning_evaluation.md)、[v8.6 模型叙事评估](docs/v860_model_construction_solution_rationale_evaluation.md)、[v8.7 逐问写作预检评估](docs/v870_question_writing_capability_preflight_evaluation.md)、[按数据结构选择的绘图技巧](templates/figure/figure_enhancement_patterns.md#12-按数据结构选择的绘图技巧)、[MATLAB 绘图说明](templates/matlab/README.md)。这些是历史或专项材料；当前执行仍以表中的 Authority 为准。

许可证与第三方声明见 `LICENSE`、`THIRD_PARTY_NOTICES.md`。


## A2：结构核验接入已有执行链

显式选择阶段的项目，可按 [Conformance Authority](core/model_code_conformance_contract.yaml) 使用 A2 交付、回执与失效绑定；[实施台账](docs/modeling_intelligence_a2_execution_plan.md) 记录具体范围与验证。该功能不强制迁移旧项目，不把结构对应当成数学等价证明，不包含 B/C/D 后续模块。最新 GitHub Release 与开发主干版本分别以实际发布记录和 bootstrap 为准。
