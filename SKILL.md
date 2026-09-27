---
name: mathmodel-skill
description: Guide mathematical-modeling competition work from problem analysis and model design through user-run computation, accepted-workbook figures, paper writing and delivery review. Use for CUMCM, MCM/ICM and related modeling projects, including targeted work on an existing modeling project.
metadata:
  version: 10.9.0
  summary: HSK mathematical-modeling workflow with bootstrap-first task routing, Problem Contract freezing, condition-driven structural reduction and minimal-sufficient main-model generation before solver selection, independent Model Challenge, explicit Human Model Approval bound to the current semantic revision and validated structured identity, one project-wide Python/MATLAB numerical backend choice and user-owned full-fidelity numerical execution, evidence-checked workbooks, MATLAB evidence visualization, editable draw.io mechanism diagrams with deterministic structural checks and required rendered review, model-construction rationale with solver-precondition evidence, Template-First paper authoring with state-driven per-question writing capability preflight and final-order Cross-File Chapter Handoff, formal LaTeX attestation, evidence-traceable final review compliance, and validated delivery provenance.
  triggers: [数学建模, 数模, CUMCM, 国赛, MCM, ICM, 电工杯, 认证杯, 审题, 问题分析, 建模思路, 建模方案, 模型比较, 完整求解, 全流程, 建模论文, 模型论文框架, 模型锁定, 模型审查, 算法流程, 伪代码, 数据预处理, 数据清洗, 主结果质量, 数值有效性, 结果分析, 结果深化分析, Python求解, MATLAB求解, MATLAB绘图, 可编辑机理图, draw.io, drawio, LaTeX, DOCX, 终审, 提交包]
---

# HSK 数学建模模块化工作流 v10.9.0

<!-- HSK_RUNTIME_ENTRY_CONTRACT_START -->
## 运行时入口合同（非权威摘要）

下文资源路径均相对于包含 `core/bootstrap.yaml` 和 `.codex-plugin/plugin.json` 的仓库/插件根目录。根入口以自身目录为根；`skills/mathmodel-skill/SKILL.md` 以自身目录上两级为根。先确认这两个根标记存在，再解析资源路径；不以用户项目的工作目录代替插件根。

本文件只负责发现、启动和 Authority 委托，不复制数学建模业务合同。无论从根目录 `SKILL.md` 还是 `skills/mathmodel-skill/SKILL.md` 进入，都按同一链路执行：

1. 首先读取 `core/bootstrap.yaml`；
2. 由 `core/workflow_router.yaml` 的 `default_load` 加载 `core/hsk_core_policy.md`；
3. 使用 `scripts/resolve_runtime.py` 根据当前意图、竞赛和项目状态解析最小 `load_order`、运行时 assurance 与 `pre_delivery_gates`；模型批准、条件式预处理与主数值验证分别委托 `core/model_approval_contract.yaml`、`core/global_preprocessing_contract.yaml`、`core/numerical_verification_contract.yaml`；
4. 只加载 resolver 命中的 contracts、modules、packs 和 templates，不预载整个仓库；
5. 需要项目语义时读取 current `模型论文框架.md`，生命周期 revision/structured identity/text provenance/stale 服从 `state/project_state.yaml`，具体数值回到 accepted workbook；
6. 普通写作由 Template Manifest、Paper Writing Protocol 和 compact writing runtime 渐进加载，并按最终 active assembly 执行 Cross-File Chapter Handoff；复杂数学/证据裁决按 resolver 补读 `core/writing_reasoning_contract.yaml`，终审再读取 `modules/06_review_delivery.md` 与 `templates/review/final_review_matrix.yaml`；
7. `legacy/` 不进入默认执行链，旧 `scripts/resolve_workflow.py` 只保留无状态/兼容入口。

本节只声明入口委托关系，**不作为模型、预处理、求解、绘图或写作规则的独立权威**；任何冲突都以 `core/bootstrap.yaml` 指向的 current Authority 与 resolver 输出为准。
<!-- HSK_RUNTIME_ENTRY_CONTRACT_END -->

## 默认执行

用户明确指定 Python 或 MATLAB 求解时，将请求传为 `--solver-backend python` 或 `--solver-backend matlab`，与当前项目根 `execution.solver_backend` 核对；未指定时，新 assured 数值/模型设计入口按 `--solver-backend auto` 解释，已有项目选择由状态恢复；仅旧 `resolve_workflow.py` 保留省略参数时的 Python 兼容投影。`auto` 和无状态兼容默认均不写入项目选择，当前项目缺少根选择时不得正式交付数值代码。完全未选且无历史数值阶段的项目，审视全题需求并衔接既有 Model Approval 后用 `scripts/project_solver_backend.py select` 登记；即使只读迁移预览为 `ready_for_review`，也不能以 `migrate` 替代首次选择。有历史数值阶段或更换已锁后端时，先用该脚本 `inspect --migration-target ... --reason ...` 预览全题影响，再针对该项目目标、原始状态、代际和影响摘要明确确认，才可执行 `migrate --confirm-migration`；仓库代码修改的批准不等于具体项目迁移的确认。迁移同事务登记原始字节归档和报告引用，完成后仍须重新满足当前数值交付门。`RUN_CONFIG` / `RUN_RECEIPT` 的后端是实际运行事实，不能替项目选值。具体规则服从 `core/user_execution_contract.yaml` 与 `core/runtime_assurance_contract.yaml`。默认入口始终是 `scripts/resolve_runtime.py`；`scripts/resolve_workflow.py` 只作为 legacy / 无状态兼容 resolver，不参与默认 assured read path。

### 项目工作记忆

项目语义继续由 `模型论文框架.md`、`state/project_state.yaml` 与 accepted workbook 分层恢复；本节只保留稳定导航标题，不复制 Project Memory 合同字段。

## 主链

为兼容活动导航与健康检查，只列出主链语义节点，不在入口重新定义其业务规则：

`通用数据审计` → `条件数学化与结构化简` → `最小充分主模型 + 按需 comparator` → `preprocessing_decision` → `proposed_model_spec` → `Model Reviewer + Devil's Advocate` → `awaiting_model_approval` → explicit Human Model Approval → `locked_model_spec` → resolver-selected preprocessing / solve / analysis stages。

## 目录、正式交付

目录与 artifact 数量只服从 `core/output_contract.yaml`。LaTeX 公共审计入口是 `scripts/audit_latex_project.py`；提交包在 resolver 返回的全部 gate 完成后才可成为 `validated_submission_package`。

## 稳定硬边界

- Problem Contract 冻结不等于模型已批准。形成 `proposed_model_spec` 后，必须完成独立 Model Reviewer 与 Devil's Advocate challenge；正式项目级预处理或主求解代码只有在用户明确批准 current `semantic_revision` 与 validated `semantic_identity_hash`、并由 Model Approval gate 确认 current = validated = approved identity 后才允许进入对应 gate；legacy hash 只读兼容不能授权新代码。
- 题目专属预处理、Python/MATLAB主求解与结果深化代码由用户本地按 `full_fidelity` 执行；助手负责生成、静态检查和验收返回 artifact，不得静默降采样、放宽容差、缩短时域或切换求解器。
- `模型论文框架.md` 保存当前项目语义与证据位置；`state/project_state.yaml` 管 revision/structured identity/text provenance/stale；accepted workbook 是具体数值事实源。三者职责不得互相替代。
- 主求解数值有效性与 accepted 资格服从 `core/numerical_verification_contract.yaml`；accepted 后的替代世界/敏感性/稳健性分析服从 resolver 命中的结果分析模块，不反向扩张主质量门。
- MATLAB 绘图入口只消费已验收求解实现的数据/工作簿进行 Figure Evidence，不重新预处理或求解；正式图名由 LaTeX/DOCX caption 承担。
- 可编辑 draw.io 只服务后端选择门确认的非数据驱动题目专属机理图；确定性结构检查不替代渲染预览、箭头语义或数学正确性人工复核。
- LaTeX 是默认论文主链；CUMCM 结构先由 Template Manifest 确定，再逐章读取当前写作规则。DOCX 只在用户明确要求 Word 载体时加载。
- 最终交付只执行 resolver 当前返回且按顺序排列的 `pre_delivery_gates`；入口文件不维护第二套 gate 清单。
- 仓库修改遵守 `SKILL_CHANGE_GOVERNANCE.md`。Branch Protection 若因平台权限不可用，只记录为平台治理债务，不得用 Skill 代码伪造。

求解语言参数按上文“默认执行”传入；后端决策与旧调用兼容只服从 `core/user_execution_contract.yaml` 和 runtime assurance，不把 MATLAB 一词自动路由为绘图。

## Authority 导航

| 主题 | Current Authority / consumer |
|---|---|
| 启动、最小加载 | `core/bootstrap.yaml` |
| 全局硬规则 | `core/hsk_core_policy.md` |
| 路由、阶段、gate | `core/workflow_router.yaml` |
| 题型与 capability | `core/task_taxonomy.yaml` |
| 模块输入输出 | `core/module_manifest.yaml` |
| 目录与正式交付 | `core/output_contract.yaml` |
| 项目状态与 stale | `core/project_state.schema.yaml` |
| 显式主张证据核验 | `core/claim_evidence_contract.yaml`，只读消费原已验收来源 |
| 显式论文主张消费与局部失效 | `core/claim_consumption_contract.yaml`；独立审计仍只读，`propagate` 仅经现有项目同步事务写相关片段 stale，不更改普通路由门禁 |
| 项目工作记忆 | `templates/model/model_paper_framework.md` |
| 模型 Challenge / Human Approval | `core/model_approval_contract.yaml` |
| 数据审计与条件式预处理 | `core/global_preprocessing_contract.yaml` |
| 用户执行所有权 | `core/user_execution_contract.yaml` |
| 主求解数值有效性 | `core/numerical_verification_contract.yaml` |
| Python/MATLAB 工程质量 | `core/code_quality_contract.yaml` |
| runtime assurance | `core/runtime_assurance_contract.yaml` |
| 主求解 / Primary Evidence | `modules/03_solve_validate.md` |
| accepted 后结果深化 | `modules/03_result_analysis.md` |
| 科研图证据 | `modules/04_figure_evidence.md` |
| 可编辑机理图实现 | `templates/figure/mechanism_drawio_spec.yaml`, `templates/figure/mechanism_drawio_patterns.md`, `scripts/generate_mechanism_drawio.py`, `scripts/validate_drawio_figure.py` |
| CUMCM 固定结构 | `templates/latex/cumcm/hsk/template_manifest.yaml` |
| 写作读取状态机 | `core/writing_runtime_contract.yaml` |
| 普通正文 | `modules/05_writing/paper_writing_protocol.md` |
| 复杂写作语义与证据 | `core/writing_reasoning_contract.yaml` |
| LaTeX Adapter | `modules/05_writing/latex.md` |
| 表达清理 | `modules/05_writing/ai_cleanup.md` |
| 终审语义 / 报告结构 | `modules/06_review_delivery.md`, `templates/review/final_review_matrix.yaml` |

## 能力发现标签

以下名称仅用于能力发现与回归，不在本入口重复定义规则：**Condition-Driven Reduction、Minimal Sufficient Main Model、Comparison Envelope、Structure-Matched Solver、Template Manifest、Paper Writing Protocol、Cross-File Chapter Handoff、Primary Evidence Capture、Scientific Figure Synthesis、Editable Mechanism Diagram、Model/Solver/Validator、Model Construction Rationale、Solver Preconditions、Claim Strength Calibration、Final Review Compliance & Evidence Sweep、within-question local dependency architecture、decisiveness-based detail allocation、adaptive subsection separation、adaptive figure-result narrative**。具体定义只读取上表 Authority。

能力发现只保留名称与委托：`preprocessing_decision`、**Algorithm Trace**；当前主求解与独立深化入口按 `core/output_contract.yaml#per_question.solver_scripts` 和项目根后端解析，不以旧 Python 文件名推定交付。入口不重新定义预处理、结果分析或算法呈现规则。

## 兼容与版本信息

- 历史 v7 项目继续保持只读兼容，不自动重排或覆盖既有论文正文；迁移说明见 `docs/v8_writing_migration.md`。
- 历史版本能力与实施记录见 `CHANGELOG.md`、Git 历史和 `legacy/README.md`；`README.md` 只提供当前启动、职责与资料导航。
- 活动文件导航使用 `PROJECT_INSTRUCTIONS.md`、`RUNTIME_ROUTER.md`、`SKILL_FILE_INDEX.md`、`TEMPLATE_INDEX.md`。
