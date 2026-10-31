# 阶段 E：六领域跨模块回归与门禁证据审计（进行中）

> 记录日期：2026-10-31；证据基线：`main@3901a9343945328fc2fc17b8d4a8cd9fa11ca850`，Skill `10.23.2`。本文件是维护审计记录，不是运行时 Authority、用户项目的数学证明或额外 gate。
>
> 依据：`docs/runtime_router_and_gate_simplification_refactor_plan.md` 第 2、5、7、8、10、12、14 节及 `SKILL_CHANGE_GOVERNANCE.md`。阶段 B2/P6（PR #279）和阶段 D/P4（PR #280）已合并，不重复修改。阶段 C 只有发现多个消费者竞争写入同一机器事实时才独立立项。

## 1. 合并后 main 的远端证据

- PR #280 的最终源 head 为 `e1546d836f5e0d169358e93c0ac6da8befc490d3`；合并提交为 `3901a9343945328fc2fc17b8d4a8cd9fa11ca850`。PR head 的正式 HSK CI [#41165226134](https://github.com/Vexushi1/mathmodel-skill/actions/runs/41165226134) 和适用 Optimization baseline [#41165226091](https://github.com/Vexushi1/mathmodel-skill/actions/runs/41165226091) 已成功；这些是 **PR head** 证据，不替代合并后的 main。
- 合并后 [HSK Skill CI #41170163057](https://github.com/Vexushi1/mathmodel-skill/actions/runs/41170163057)：Static contract lint、Generated file contract、Regression mode、Windows Python 3.10/3.14 各四分片及各自汇总、MATLAB R2024b native、LaTeX CUMCM/MCM-ICM/Diangong、Production LaTeX attestation 均为 `success`。抽查 Python 汇总、MATLAB、Generated contract、Production attestation 的原始 job 日志，checkout/source SHA 为上述合并提交。Windows targeted job 为条件 `skipped`，**不计 PASS**。
- 合并后 [Refresh generated #41170163022](https://github.com/Vexushi1/mathmodel-skill/actions/runs/41170163022)：`verify-main=success`；`refresh-feature-branch=skipped`（main 事件下不适用），**不计 PASS**。
- 以上证明仓库自动化覆盖的正式检查通过，**不证明任一真实赛题的模型正确、用户 full-fidelity 执行、人工模型/图表批准或 PDF 逐页视觉检查已完成**。

## 2. 六领域审查矩阵

| 领域 | Authority / 当前消费者 | 已核对的现有回归证据 | 结论及剩余边界 |
|---|---|---|---|
| 题目分析 | `core/workflow_router.yaml`、`core/task_taxonomy.yaml`、`scripts/resolve_runtime.py`、`scripts/resolve_workflow.py` | `tests/test_router_contract.py` 的 unknown/unclassified generic fallback、design scope、legacy labels；`tests/test_v900_phase_g_competition_runtime.py` 的 unknown competition、missing manifest fallback；`tests/test_v10182_paper_routing.py` 的显式 intent 及载体优先级 | 路由/可选资源边界有当前自动化回归；真实赛题的题目条件、依赖、特殊要求是否完整提取需在项目实例中核查，不能仅凭路由测试宣布通过 |
| 模型分析与建立 | `core/model_approval_contract.yaml`、`core/project_state.schema.yaml`、`core/state_transition_contract.yaml`、`scripts/validate_model_approval.py` | `tests/test_v711_model_approval_gate.py` 的独立双挑战、明确批准、blocking/stale/旧字段；`tests/test_v900_state_transitions.py` 的事件与依赖传播；`tests/test_v930_initial_modeling_core.py`、`tests/test_v931_model_design_capability_preservation.py` 的结构与能力保全 | 批准、修订、stale 的机器边界有回归；具体公式、目标函数、约束、候选模型优劣与两位独立审查者的实际专业判断不由仓库 CI 证明 |
| 求解精度 | `core/numerical_verification_contract.yaml`、`core/workbook_schema.yaml`、`scripts/validate_numerical_evidence.py`、`scripts/validate_user_execution.py` | `tests/test_v714_numerical_verification.py` 的残差重算、容差、收敛、布尔证据、缺失证据 fail-closed；`tests/test_result_io.py` 的质量门与工作簿结构；`tests/test_user_execution_contract.py` 的 receipt 与 accepted 边界；main MATLAB native job | 合同与合成数值链已远端验证；不等于实际赛题精度、规模、收敛和模型有效性已实测 |
| 求解规范 | `core/user_execution_contract.yaml`、`core/code_quality_contract.yaml`、`core/model_code_conformance_contract.yaml`、`scripts/validate_code_delivery.py`、`scripts/sync_project.py` | `tests/test_model_code_conformance.py` 的源码/模型绑定、动态代码 needs_review、变更身份、CLI fail-closed；`tests/test_user_execution_contract.py` 的代码交付不等于已求解；`tests/test_sync_project.py` 的 scope、主/分析失效；`tests/test_audit_closure_regressions.py` 的数据身份与旧入口 | 当前机器身份、执行分工与 scope 回归通过；不能用静态代码合格或合成 MATLAB 作业替代用户实际运行、运行环境与代码-数值对应证明 |
| 结果深化分析 | `core/output_contract.yaml`、`core/workbook_schema.yaml`、`scripts/validate_user_execution.py` 与 analysis 相关合同 | `tests/test_audit_analysis_boundaries.py` 的 required/not_required、accepted primary、依赖失效；`tests/test_analysis_comparison_integration.py` 的比较证据、篡改阻断、独立 analysis 资格；`tests/test_result_io.py` 的分析工作簿结构 | 条件式分析和比较证据的机器边界有回归；具体问题是否需要敏感性、稳健性、阈值或替代算法，以及分析结论是否充分，仍需按题意评审 |
| 论文写作 | `modules/04_figure_evidence.md`、`modules/05_writing/paper_writing_protocol.md`、`modules/06_review_delivery.md`、`core/output_contract.yaml` | `tests/test_reading_plan.py` 的 mixed style/new figure 原文读取、未批准/真实语义变化、gate 保留；`tests/test_b2b4_formal_figure_gate.py` 的图文证据链；`tests/test_v7100_delivery_attestation.py` 的 source/PDF/manifest 绑定；`tests/test_v820_final_review_compliance.py` 的终审证据；main 三模板与 Production attestation | 新图与样式、来源及机器交付检查有回归；正式 PDF 逐页人工视觉审查、数学文字质量、图像可读性和语义批准不能由编译/结构检查代替 |

审计结论：**六领域的既有自动化保护链均有可定位证据，尚未发现足以启动代码修复的新回归；阶段 E 的专业/人工实例审查仍是未完成边界。** 不把此表的机器证据提升为全部六领域人工验收 PASS。

## 3. 第 7 节专项矩阵与历史回归

- **R01–R06 / G01–G06：** `test_router_contract.py`、`test_v900_phase_g_competition_runtime.py`、`test_v10182_paper_routing.py`、`test_v711_model_approval_gate.py` 为可定位的回归入口；对显式意图、可选模板、未分类题、审批边界分别保留现有正反例。
- **G07–G09 / G10–G12：** `test_user_execution_contract.py`、`test_v714_numerical_verification.py`、`test_audit_analysis_boundaries.py` 及 `test_result_io.py` 对代码交付、用户执行、accepted、分析必要性与条件依赖提供回归。
- **G13–G16 / K01–K14：** `test_reading_plan.py` 与图表相关测试保护混合读取和新图未自动获批；PR #279 的旧 accepted provenance/新执行边界另由原有源码身份、同步及工作簿回归保护。未在本审计中逐项重演 K01–K14 的真实用户项目操作，不将历史专项成功等同于重新实测。
- **G17–G18 / S01–S04：** `test_router_contract.py`、`test_reading_plan.py` 的同次调用 gate 去重、顺序、不同输入；`test_v900_state_transitions.py`、`test_audit_closure_regressions.py` 的 stale 与机器事实身份。未发现需要双写 State Schema 的新证据。
- **W01–W05 / C01–C03：** `test_v10182_paper_routing.py`、`test_v7100_delivery_attestation.py`、`test_submission_current_artifacts.py`、`test_v820_final_review_compliance.py`、历史兼容相关测试为入口。人工 PDF 逐页审查与官方赛规核验仍需真实交付时执行。
- **AUD-01–AUD-18：** `docs/repository_audit_and_handoff_refactor_plan.md` 的 A1–A7 历史记录分别列出原缺陷和已验证结果；当前 main 包含 `tests/test_audit_*.py`、`tests/test_v714_numerical_verification.py`、`tests/test_v7100_delivery_attestation.py` 等对应测试族，并完成本次全量回归。**本轮尚未逐个 AUD ID 重新追踪到唯一测试断言及日志行**，因此仅确认回归族运行，不宣称 18 项均已单项人工复核。

## 4. 门禁删 / 并 / 移 / 保留清单（不创建新运行时 Schema）

| Gate 或机制 | 当前 Authority / 消费者 | 本次裁决 | 证据及不可突破边界 |
|---|---|---|---|
| `semantic_governance` | Router 有效顺序、Manifest→`validate_semantic_governance.py` | **保留** | 当前语义与 stale，不可因其他 gate 执行而跳过 |
| `model_approval` | Manifest→`validate_model_approval.py` | **保留** | 双重 Model Challenge 与当前 Human Model Approval 不可用模糊继续、旧 hash 或 CI 代替 |
| `code_delivery` | Manifest→`validate_code_delivery.py` | **保留，按阶段触发** | 真实交付前静态/身份要求；不等于 full-fidelity 用户执行 |
| `user_execution_receipt` | Manifest→`validate_user_execution.py` | **保留，返回工作簿时触发** | 必须绑定真实源码/数据/回执与数值质量，不能预先 PASS |
| `project_sync` | Router + `core/output_contract.yaml#project_sync`→`sync_project.py` | **移至适用正式 scope，保留独立风险覆盖** | design 不触发不适用的终稿门；results/figures/docx/latex/submission 按实际依赖，旧 accepted 只读路径不受无关源码整理误阻断 |
| `submission_package_validation` | Router submission→`validate_submission_package.py` | **保留，仅提交范围** | manifest、PDF、ZIP、官方 allowlist 与实际来源仍须核对 |
| `claim_consumption`、`claim_evidence`、`model_code_conformance` | Manifest 对应 utility gate 与各自独立 Authority | **保留，显式/opt-in 消费** | 不无条件追加普通路由，不用专项观察结果代替审批或 accepted |
| 同一调用中重复出现的 gate 名称 | Router/Resolver 的有效 `pre_delivery_gates` | **合并同次相同检查的重复调度** | `test_router_contract.py`、`test_reading_plan.py` 保留有序去重；不同输入、阶段和风险不能误合并 |
| 可选模板/分类缺失导致的过早阻断 | `resolve_runtime.py` 与写作 profile Authority | **改为适用回退或诊断，保持非法配置 fail-closed** | 缺已声明文件可通用回退；字段缺失、无效配置仍阻断 |
| 其他 gate 删除 | 各既有 Authority | **本轮不删除** | 未获得重复真实执行、副作用及唯一风险被替代的证据，不因文本声明重合而删除 |

## 5. 状态事实所有权与阶段 C 决策

机器 revision/approval/stale 以 `core/project_state.schema.yaml`、`core/state_transition_contract.yaml` 为权威；`模型论文框架.md` 为语义记忆/摘要，accepted 工作簿与运行回执为数值及执行证据，人工审查记录不能由机器 PASS 代替。当前审计未发现两处同时竞争写入同一机器状态事实的可复现用例。**阶段 C 不立项，不迁移 Schema。**

## 6. 下一步与验收限制

1. 本文件仅记录已完成的远端检查和代码/测试静态证据；对 R/G/S/W/C、K01–K14、AUD-01–AUD-18 建立逐项测试方法与原始日志的交叉索引后，再判断历史回归审查是否闭合。
2. 需要真实项目实例才能验证的数学审查、用户数值执行、视觉审查、PDF 页面检查和赛规，不得由 CI 自动标记通过；如发现具体可复现的跨模块缺陷，按单主题独立修复 PR、自动生成元数据、专项、Ready、最终 head 正式 full、合并后 main 复核。
3. 本次 docs-only 审计 PR 不改变 Authority、gate、Schema、CLI、版本、生成索引或测试；应由 GitHub 自动刷新生成文件并按治理完成适用远端检查。正式通过前本文件只是待复核记录。
