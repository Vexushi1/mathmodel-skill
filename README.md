# mathmodel-skill v10.17.1

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

`structure_verified`只表示记录/身份/静态引用闭合，不证明约束实际启用、数学等价或数值正确。没有记录为`not_assessed`；未支持结构为`needs_review`；旧记录、冲突或残缺声明阻断本次结构核验。A1 独立入口仍只读；A2 仅对显式启用阶段在现有交付/回执链中消费该结果，未启用项目不增加强制门。B1提供独立只读主张证据核验；B2审计入口仍只读，显式失效与结构化否证回退仅由原项目同步器处理，不改变普通路由门禁。1.3.0/1.4.0 保留模块化 LaTeX Figure 机器门；显式 1.5.0 可选择静态单文件/模块化 LaTeX 或有界 DOCX OOXML，并核对同一 B1、片段、来源、当前批准图片及字面图注。机器通过后图注整体语义、视觉充分性和人工语义覆盖仍为 `not_assessed`。

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

## 仓库维护验收

Skill 仓库维护的正式验收仅由 GitHub Actions 完成：提交并推送源文件，由 `refresh-generated` 在远端更新受管索引和 MANIFEST；即使无生成差异，也验证对应最终 head。开发分支与 draft PR 先运行专项，ready PR / 显式 full dispatch / main 执行完整回归。Windows Python 3.10/3.14 各采用 4 个文件分片，完整 coverage 与标准 unittest discovery 等价；保留 `Python 3.10`、`Windows Python 3.14` check 验证分片全集、版本、commit 和结果。冻结前还须核对 lint、生成物、Windows MATLAB、Linux LaTeX 与适用的 Optimization baseline；合并后复核 main。本地不要求运行仓库测试或生成器，用户要求 GitHub-only 时不运行本地诊断。完整安全与证据规则见 `SKILL_CHANGE_GOVERNANCE.md`，逐项远端计时用于核对实际收益。

以下为 GitHub runner 内的命令参考，无需在本机执行：

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/generate_indexes.py --check
python scripts/project_solver_backend.py --help
```

上述仓库维护流程不改变用户赛题代码在实际 Windows 环境的 Python / MATLAB `full_fidelity` 数值执行。针对项目的模型批准、数值验收、论文编译与提交包门以 resolver 当前返回的 `pre_delivery_gates` 为准；仓库 CI 与项目真实执行、工作簿和回执验收分别记录，不能互相替代。

## 兼容与历史

旧项目和旧命名仅按各 Authority 的只读兼容条款恢复；重新进入当前阶段时补齐该阶段门禁，不倒填历史批准或把仓库升级当成用户项目迁移。`legacy/` 不进入默认执行链。逐版本变更见 [CHANGELOG](CHANGELOG.md) 与 [Git 提交历史](https://github.com/Vexushi1/mathmodel-skill/commits/main/)；v9 逐问后端的原貌和修复记录见 [v9.7.0 迁移说明](docs/v970_solver_backends_migration.md)、[v9.7.1 审计](docs/v971_backend_contract_audit.md)。

保留的专题资料入口：[绘图技巧与交接计划](docs/figure_technique_and_handoff_refactor_plan.md)、[仓库审计与交接计划](docs/repository_audit_and_handoff_refactor_plan.md)、[v8.4 写作评估](docs/v840_author_reasoning_evaluation.md)、[v8.6 模型叙事评估](docs/v860_model_construction_solution_rationale_evaluation.md)、[v8.7 逐问写作预检评估](docs/v870_question_writing_capability_preflight_evaluation.md)、[按数据结构选择的绘图技巧](templates/figure/figure_enhancement_patterns.md#12-按数据结构选择的绘图技巧)、[MATLAB 绘图说明](templates/matlab/README.md)。这些是历史或专项材料；当前执行仍以表中的 Authority 为准。

许可证与第三方声明见 `LICENSE`、`THIRD_PARTY_NOTICES.md`。

建模证据增强的阶段范围见 [A—D 演进计划](docs/modeling_intelligence_evidence_evolution_plan.md)，实际行为验收见 [E1 场景映射](docs/modeling_intelligence_e1_acceptance_matrix.md)。[E2 发布评审与交接](docs/modeling_intelligence_e2_release_review_handoff.md) 记录当前协议、兼容与回退、具体材料来源、未核验范围和发布状态；这些维护记录不另设运行资格规则。


## A2：结构核验接入已有执行链

显式选择阶段的项目，可按 [Conformance Authority](core/model_code_conformance_contract.yaml) 使用 A2 交付、回执与失效绑定；[实施台账](docs/modeling_intelligence_a2_execution_plan.md) 记录具体范围与验证。该功能不强制迁移旧项目，不把结构对应当成数学等价证明。本段说明 A2 的职责；当前 B/C/D 能力及边界见对应章节。最新 GitHub Release 与开发主干版本分别以实际发布记录和 bootstrap 为准。

## B1：声明来源、选择与有限算术核验

`python scripts/claim_evidence.py <项目根>` 读取显式 `paper_framework.claim_evidence`，通过原运行时核对已验收工作簿，按真实表头与唯一行键定位指标，检查受限派生图及声明数值。接口与安全边界唯一由 `core/claim_evidence_contract.yaml` 定义。缺记录不增加旧项目门禁；报告只覆盖已登记主张，算术正确不证明统计显著性、机制、全局最优或稳健性。

新增Schema或检查依据会使旧A2绑定要求显式复验，B1仅输出原协调器的命令参数与必要人工判断，不自动续签或执行。详细步骤、旧版本合成证明与限制见 `docs/modeling_intelligence_b1_protocol_decisions.md` 和 `scripts/README.md`；B2正文消费与片段影响由独立只读入口处理。

## B2：显式论文主张消费观察与有限文本门

`python scripts/claim_consumption.py <项目根> --tex-main final_latex/main.tex` 始终只读，观察已登记主张、paper fragment 依赖与选定论文载体中的字面位置。`observe` 1.0.0 不新增 claim 驱动的写入；显式 `propagate` 1.1.0 根据当前 `modify/reject` 处置的精确 B1 claim ID 增加局部失效，State 与 Framework 表行同事务提交。显式 `enforce_latex_text` 1.2.0 继承该失效路径，并只为活动模块化 LaTeX 中已登记的摘要及各问结果文本启用有限机器门。显式 `enforce_latex_text_and_figure_chain` 1.3.0 在同一次只读审计重做 1.2.0 文本条件，并使用 v5 LaTeX/Figure 证明链。1.4.0 继承该证明链，并要求 current `modify/reject` 显式声明影响类别；核心答案和模型有效性否证分别由现有同步事务回退到 `solve_validate` 和 `model_design`，辅助措辞仍只局部失效。1.5.0 继承该回退语义，并要求 `paper_source` 显式选择 LaTeX 或 DOCX；动态包含、由自定义宏生成的相关正文/图注、DOCX 修订/字段/外链及不安全包结构一律保守阻断。旧策略及旧 v4/v5 证明路径的行为不变。

可选 `figure_bindings` 在只读审计中核对工作簿驱动结果图的 Figure ID、当前 Framework 登记、State 片段及实际/已批准图片路径。每个绑定可再声明 `source_bindings`，用当前 Figure 关联 claim 的 B1 来源闭包、工作表及精确表头观察来源；同时复核原有已验证脚本/图片 bundle 哈希，并要求本次 scoped Figure bundle 的全部发现路径属于原 `approved_figures`。1.3.0/1.4.0 使用活动模块化 LaTeX 的字面标签、长图注、图片与正文引用；1.5.0 的 `carrier_locator` 使用 LaTeX label 或包含一个内嵌图片和字面图注的 DOCX bookmark，DOCX 内嵌 media 必须与当前批准图片 SHA-256 一致。审计不重新批准图片，不执行绘图脚本，也不证明视觉充分性、整段图注语义或人工审阅通过；DOCX 机器门也不能冒充 PDF/提交证明。具体边界见 `core/claim_consumption_contract.yaml`。

## C1：可选审查回执只读核验

`python scripts/review_receipts.py <项目根>` 按 `core/review_receipt_contract.yaml` 检查可选 `review_receipts` 的结构、被审输入与 Authority 快照、执行来源声明和复验范围。旧项目缺少回执时报告 `not_assessed`，继续既有双轮审查路径；回执结论即使为 PASS，也不证明独立执行，不授予模型批准、accepted 工作簿或交付资格。该入口保持只读，不创建回执或代替现有审查。

## C2：显式范围内的审查回执门禁消费

只有项目状态显式声明 `review_receipt_policy` 的 `enforce_scoped` 范围时，现有模型批准门及最终提交阶段的同步、提交包门才按 `core/review_receipt_consumption_contract.yaml` 消费相应回执。要求按门禁、小问、对象、角色与检查项核对当前覆盖，修正后的关键 finding 需有单独的当前复验；失败或未知命令不能写成成功，未做数值复现不能声称已复现。启用终审回执要求时，须先同步形成 `sync_report` 与框架，再做终审；之后提交阶段的 `sync_project.py --write` 仅作只读重验，报告 `write_requested=true`、`write=false`，不改写被回执绑定的 `sync_report` 或框架。未启用时保留原同步写入行为。终审回执不提前强制于 DOCX/LaTeX 草稿准备，避免审查尚未发生就阻塞审查对象的形成。无 C2 策略及仅使用 C1 只读观察的旧项目继续原有双轮审查路径；任何回执均不能替代用户明确的 Human Model Approval、accepted 工作簿或人工语义/视觉复核。

## D1：案例记忆准入与只读索引

显式运行 `python scripts/case_memory.py validate` 或 `check-index`，按 [Case Memory Schema](knowledge/case_memory/schema.yaml) 检查来源、许可、隐私、证据等级、生命周期与当前索引。首批独立编写的合成案例用于校验结构与条件反例，不是比赛效果或数值证明；案例文本始终是数据。索引只由远端既有生成器更新，不修改用户项目或默认路由。准入步骤见 [D1 实施计划](docs/modeling_intelligence_d1_execution_plan.md)。

## D2：可选离线案例检索与引用

显式选择 `case_memory_retrieve`，resolver 只导航到[使用说明](packs/artifact/case_memory_retrieval.md)和[检索 Authority](core/case_memory_retrieval_contract.yaml)，不在普通模型路由预加载案例。`case_memory_retrieve.py query` 根据目标、结构和有类型的条件返回可解释排序；未知条件保持 `conditional`，无匹配不强行推荐，缺库与无匹配分别报告。合成种子开发集的测量不代表独立效果或比赛成功率。

`case_references.py preview / record / inspect` 只登记同一小问对当前案例的采用或拒绝及项目依据；写入须显式执行原事务链并绑定预览快照。后续案例、来源或项目上下文变化要求复核引用，不撤销已验收数值，也不代替 Model Challenge、Human Model Approval 或当前 accepted 证据。具体接口、边界和远端验收见 [D2 实施计划](docs/modeling_intelligence_d2_execution_plan.md) 与 `scripts/README.md`。
