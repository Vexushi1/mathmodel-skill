# Final Acceptance：50 场景追溯矩阵与专业边界（维护证据）

> **性质：** docs-only 仓库维护审计，不是 Runtime Authority，不定义新 gate 或 State Schema，也不授予任何真实赛题的数学/数值/视觉 PASS。原始场景定义以 [重构计划第 7 节](runtime_router_and_gate_simplification_refactor_plan.md) 及 P6 的 K01–K14 为准；AUD-01–AUD-18 的逐项日志以 [阶段 E 审计第 7 节](phase_e_six_domain_regression_audit.md) 为准。
>
> **审计基线（2026-10-31）：** Skill `10.23.2`，`main@eefca0175d06fe62445943eec20092925a373555`；PR #279/#280/#281/#282 均已合并，开放 PR 数量 0。PR #282 最终源 head `a0d062d2800082413e9611565f4663612ab1fa7f`；merge `eefca017...`。当前 Release `v10.23.0`，并非 Skill `10.23.2` 的发布证明。

## 1. 证据层级与 SHA 绑定

1. **单方法原始日志 L：** [main HSK CI #41187493893](https://github.com/Vexushi1/mathmodel-skill/actions/runs/41187493893)，checkout `6b20a216f365f9458e554b00f7215c2f77e786bf`，Python 3.10/3.14 各四分片，原 `unittest.log` 中各 2,753 条 `... ok`、无 FAIL/ERROR；AUD 逐项分片/Job/Artifact 见阶段 E 审计 §7.2–7.3。该运行的单方法日志为**历史同代码证据**，不能直接冒充 `eefca017` 的日志。
2. **当前 HEAD 正式远端证据 M：** [main HSK CI #41205006994](https://github.com/Vexushi1/mathmodel-skill/actions/runs/41205006994)，`head_sha=eefca0175d06fe62445943eec20092925a373555`，正式 Windows Python 3.10/3.14 各四分片与汇总、Static lint、Generated contract、Regression mode、MATLAB R2024b native、LaTeX 三模板及 Production attestation 均 `success`；Windows targeted checks 条件 `skipped`，不计 PASS。两版本汇总作业分别为 Job `124553436240` 与 `124551324219`。该汇总按治理核对当前 checkout、完整 discovery IDs 与结果；本审计**没有重新逐行下载 M 的八份 unittest.log**，因此不能声称已在 M 重新逐项定位每条日志。
3. **测试代码等同性 E：** [compare `6b20a216...eefca017`](https://github.com/Vexushi1/mathmodel-skill/compare/6b20a216f365f9458e554b00f7215c2f77e786bf...eefca0175d06fe62445943eec20092925a373555) 仅变更 `docs/phase_e_six_domain_regression_audit.md` 与由 GitHub 生成的 `MANIFEST.sha256`，没有生产源码/测试改动。L 的方法级执行与 M 的最终 HEAD 全发现集汇总可组合用于**相同代码的机器合同追溯**，但不得替代真实赛题人工复演。
4. **生成元数据：** [main Refresh #41205007022](https://github.com/Vexushi1/mathmodel-skill/actions/runs/41205007022) `success`；main 事件的 feature-branch refresh 条件跳过不计 PASS。docs-only 的 Optimization baseline 为 NOT APPLICABLE（没有运行时性能代码变更），不伪造运行记录。

| Python | Shard 0：Job / Artifact | Shard 1：Job / Artifact | Shard 2：Job / Artifact | Shard 3：Job / Artifact |
|---|---|---|---|---|
| 3.10 | 124548240430 / 13043588380 | 124548240536 / 13044254761 | 124548240474 / 13043704156 | 124548240453 / 13044354937 |
| 3.14 | 124548240576 / 13044258789 | 124548240580 / 13044448259 | 124548240530 / 13044032980 | 124548240546 / 13044214350 |

上表是 **M 的 Job/Artifact ID**；原始逐方法日志 L 的 Job/Artifact 不同，详见阶段 E 审计 §7.2。全部 50 行的 `M+E+L` 表示“当前 HEAD 汇总 + 未变测试源码 + 前一 HEAD 方法日志”，**不等于**在 M 单独完成逐方法日志重读。

## 2. 索引约定

Authority 缩写：`RT` = `core/workflow_router.yaml`；`CR` = `config/competition_profiles.yaml`；`AS` = `core/runtime_assurance_contract.yaml`；`MA` = `core/model_approval_contract.yaml`；`UE` = `core/user_execution_contract.yaml`；`WB` = `core/workbook_schema.yaml`；`NV` = `core/numerical_verification_contract.yaml`；`ST` = `core/state_transition_contract.yaml`；`STATE` = `core/project_state.schema.yaml`；`OUT` = `core/output_contract.yaml`；`MOD` = `core/module_manifest.yaml`；`FE` = `modules/04_figure_evidence.md`；`WR` = `core/writing_runtime_contract.yaml`；`REV` = `modules/06_review_delivery.md`；`PK` = `core/output_contract.yaml#delivery_attestation`。这里的缩写只是本审计引用，不是第二套 Authority。表内消费者为已核对的主要路径，完整输入/副作用以原 Authority 为准。

测试文件缩写（所有方法均位于当前 `main` 测试源码）：`RT` = `tests/test_router_contract.py`；`CR` = `tests/test_v900_phase_g_competition_runtime.py`；`PR` = `tests/test_v10182_paper_routing.py`；`RP` = `tests/test_reading_plan.py`；`MA` = `tests/test_v711_model_approval_gate.py`；`RR` = `tests/test_review_receipts.py`；`SG` = `tests/test_v900_semantic_governance.py`；`SI` = `tests/test_v900_semantic_identity.py`；`SB` = `tests/test_v900_semantic_identity_binding.py`；`AS` = `tests/test_v712_runtime_assurance.py`；`UE` = `tests/test_user_execution_contract.py`；`AB` = `tests/test_audit_analysis_boundaries.py`；`NV` = `tests/test_v714_numerical_verification.py`；`EP` = `tests/test_execution_provenance.py`；`ST` = `tests/test_v900_state_transitions.py`；`TX` = `tests/test_v900_project_transaction.py`；`SY` = `tests/test_sync_project.py`；`AR` = `tests/test_audit_current_artifacts.py`；`AC` = `tests/test_audit_closure_regressions.py`；`FM` = `tests/test_framework_project_memory_contract.py`；`PA` = `tests/test_v900_phase_i_migration_matrix.py`；`AI` = `tests/test_v900_artifact_identity.py`；`RL` = `tests/test_result_io.py`；`LA` = `tests/test_v7100_delivery_attestation.py`；`LC` = `tests/test_v7100_final_closure.py`；`FC` = `tests/test_v820_final_review_compliance.py`；`PK` = `tests/test_audit_package_completeness.py`；`SC` = `tests/test_submission_current_artifacts.py`；`PS` = `tests/test_project_state_read_snapshot.py`；`MC` = `tests/test_matlab_code_checks.py`；`PY` = `tests/test_python_execution_reference_closure.py`；`CC` = `tests/test_model_code_conformance.py`；`CQ` = `tests/test_code_quality_contract.py`；`TW` = `tests/test_v900_transactional_writers.py`；`WL` = `tests/test_v7100_delivery_compatibility.py`。行内 `别名.test_...` 表示该文件中的实际方法，`;` 分隔的多个方法分别用于正向/反向或边界断言；**不能因测试名称本身推断所有场景均已覆盖**。

状态含义：`PASS_MACHINE` 仅表示列明的机器合同与合成反例已有相同源码的正式回归证据；`PARTIAL` 表示仅覆盖部分断言/风险；`PENDING_MANUAL` 表示目标本身必须依赖真实题目或人工审查，不能由 CI 判 PASS。每行都保留其未覆盖边界。当前没有证据支持新代码修复或阶段 C Schema 迁移。

## 3. 原计划第 7 节与 P6：50 项逐项矩阵

| ID | Authority → 生产消费者 | 已定位代表性正/反断言（测试文件缩写） | 机器审计状态 | 未覆盖边界 |
|---|---|---|---|---|
| R01 | CR/WR → resolve_runtime; writing template loader | `CR.test_cumcm_routes_match_pre_migration_golden`；`CR.test_declared_but_missing_template_manifest_uses_full_reasoning_fallback` | PARTIAL | CUMCM golden 与模板回退已证；任意已登记竞赛的模板选择尚无全称证明 |
| R02 | RT/CR → resolve_workflow; resolve_runtime | `RT.test_unknown_competition_and_unclassified_problem_use_generic_fallback`；`CR.test_unknown_competition_uses_generic_writing_authority` | PASS_MACHINE | 不代表真实未知赛题已完成题意分析 |
| R03 | RT/AS → resolve_workflow; model design route | `RT.test_unknown_competition_and_unclassified_problem_use_generic_fallback`；`RT.test_design_scope_does_not_run_final_delivery_gates` | PARTIAL | 通用路由可启动；真实题意理解与候选模型质量需人工 |
| R04 | RT/AS → resolve_runtime; intent assurance | `AS.test_explicit_intent_is_authoritative_over_request_keywords`；`PR.test_explicit_api_paper_intent_overrides_opposite_carrier_keywords` | PASS_MACHINE | 未覆盖所有自然语言冲突句式 |
| R05 | RT/AS → resolve_workflow; reading_plan | `RT.test_g17_multi_formal_intents_deduplicate_only_identical_gate_names`；`PR.test_legacy_explicit_paper_override_preserves_other_inferred_intents` | PASS_MACHINE | 不同阶段实际 gate 执行不由路由单测证明 |
| R06 | RT/CR → resolve_runtime; writing profile loader | `CR.test_nonwriting_route_does_not_require_competition_writing_profile`；`PR.test_carrier_disambiguation_does_not_override_unrelated_routes` | PASS_MACHINE | 未穷举全部模糊关键词 |
| G01 | RT/OUT → resolver; sync_project | `RT.test_design_scope_does_not_run_final_delivery_gates`；`SY.test_designed_project_does_not_require_workbooks` | PASS_MACHINE | 真实设计仍需语义/模型审查 |
| G02 | MA/MOD → model design; validate_model_approval | `MA.test_contract_defines_two_independent_passes_and_explicit_approval`；`MA.test_pending_approval_fails` | PARTIAL | 两次独立挑战的真实质量与未完成挑战的全部组合需人工核对 |
| G03 | MA/STATE → review_receipts; validate_model_approval | `RR.test_c06_corrected_blocker_without_recheck_is_not_closed`；`RR.test_c06_other_gate_cannot_reverify_model_finding`；`RR.test_model_pass_with_no_checks_cannot_be_current` | PASS_MACHINE | 真实 blocking finding 是否被充分修复须专业审查 |
| G04 | MA/STATE → assistant approval interpretation; validator | `MA.test_contract_defines_two_independent_passes_and_explicit_approval`；`MA.test_pending_approval_fails` | PARTIAL | “继续”“我看看”具体话语识别没有独立分类断言；助手行为待核 |
| G05 | MA/ST → semantic governance; approval validator | `MA.test_structured_semantic_change_marks_challenge_and_human_approval_stale`；`SG.test_identity_change_without_revision_bump_fails_and_with_bump_stales` | PASS_MACHINE | 实际模型语义变更识别仍须专业审查 |
| G06 | MA/NV → Model Challenge; formula trace; human reviewer | `RR.test_c06_corrected_blocker_without_recheck_is_not_closed`；`MA.test_contract_defines_two_independent_passes_and_explicit_approval` | PENDING_MANUAL | 合成状态机测试无法判断公式/约束数学正确性；需要真实题目、公式与双审记录 |
| G07 | MA/UE → validate_model_approval; validate_code_delivery | `RT.test_code_plus_figures_without_lock_stops_at_model_approval`；`MA.test_pending_approval_fails` | PASS_MACHINE | 真实生成代码与已批准模型一致性需项目实例 |
| G08 | UE/STATE → validate_code_delivery; user execution boundary | `UE.test_code_delivery_does_not_mark_solved`；`UE.test_reduced_flag_is_rejected` | PASS_MACHINE | 真实用户尚未运行的项目不得声称已求解 |
| G09 | UE/WB/NV → validate_user_execution; workbook checker | `UE.test_primary_workbook_acceptance_marks_solved`；`UE.test_data_hash_mismatch_is_rejected`；`NV.test_residual_actual_is_recomputed_from_bottom_level_evidence` | PASS_MACHINE | 合成 fixture 非真实 full-fidelity 求解、收敛或精度证明 |
| G10 | UE/OUT → analysis necessity; sync_project | `AB.test_not_required_allows_later_states_without_analysis_artifacts`；`AB.test_not_required_is_not_analyzed_and_needs_accepted_primary_and_reason` | PASS_MACHINE | 具体赛题是否应做稳健性/敏感性分析需人工 |
| G11 | UE/WB → analysis code/receipt; workbook checker | `AB.test_required_chain_and_figure_only_stale_remain_usable`；`UE.test_analysis_requires_accepted_primary` | PASS_MACHINE | 独立真实 03B 数值执行与结论待项目证据 |
| G12 | OUT/WB → sync_project; downstream figures/writing | `SY.test_solved_project_does_not_require_analysis_before_formal_results_delivery`；`SC.test_not_required_excludes_exact_residuals_and_preserves_ordinary_inputs` | PASS_MACHINE | 主张若依赖 03B 仍须相应证据 |
| G13 | AS/FE → reading_plan; figure consumer | `RP.test_verified_facts_and_style_are_narrow`；`RP.test_unscoped_ambiguous_changed_and_stale_never_take_shortcut` | PARTIAL | 实际旧图批准、图像视觉与配色修改未人工复演 |
| G14 | AS/FE → reading_plan; figure design | `RP.test_new_figure_keeps_selection_and_enhancement_available`；`RP.test_mixed_style_and_new_figure_reads_both_actual_authorities` | PASS_MACHINE | 新图设计合理性与真实导出待人工 |
| G15 | AS/FE → reading_plan; figure design and style | `RP.test_mixed_style_and_new_figure_reads_both_actual_authorities`；`RP.test_mixed_figure_unapproved_old_figure_keeps_new_design_readable` | PASS_MACHINE | 规则读取并集不代表新图已获批准 |
| G16 | FE/OUT → figure export audit; human visual review | `AR.test_newly_discovered_approved_bundle_requires_existing_manual_binding`；`AR.test_declared_export_deletion_and_escape_are_diagnosed` | PARTIAL | 机器拒绝缺失绑定/导出；实际图像视觉审查 PENDING_MANUAL |
| G17 | RT/AS → resolve_runtime; reading_plan | `RT.test_g17_multi_formal_intents_deduplicate_only_identical_gate_names`；`RP.test_g17_multi_formal_intents_preserve_gate_sequence_and_distinct_inputs`；`RP.test_distinct_conditional_triggers_for_same_source_are_preserved` | PASS_MACHINE | 不同操作/输入不可跨次缓存 PASS |
| G18 | ST/AS → sync_project; semantic governance; currentness | `AR.test_first_source_change_fails_same_formal_check_in_read_and_write_modes`；`SG.test_identity_change_without_revision_bump_fails_and_with_bump_stales` | PASS_MACHINE | 项目真实变更需重新取得当前执行证据 |
| S01 | STATE/ST → project transaction; framework reader | `FM.test_framework_is_memory_not_numeric_database`；`SB.test_legacy_approval_is_readable_but_pre_code_gate_requires_migration` | PASS_MACHINE | 人工审批不得由框架摘要替代 |
| S02 | WB/STATE → validate_user_execution; framework consumer | `FM.test_framework_is_memory_not_numeric_database`；`UE.test_workbook_changed_after_capture_cannot_acquire_qualification` | PARTIAL | 真实框架与工作簿数字冲突的端到端纠正需实例 |
| S03 | STATE/ST → historical project read adapters | `PA.test_semantic_identity_and_human_approval_are_never_synthesized`；`AI.test_conflicting_old_and_new_alias_blocks_even_read_only_migration` | PASS_MACHINE | 仅代表已覆盖的旧格式与 alias |
| S04 | ST/STATE → project transaction; sync_project | `TX.test_partial_staging_failures_cleanup_unjournaled_files`；`TX.test_recovery_after_framework_replace_before_state_replace`；`TW.test_repeated_sync_is_transition_idempotent_and_generation_monotonic` | PASS_MACHINE | 不等于任意外部并发环境无故障 |
| W01 | WR/RT → resolve_runtime; LaTeX writing | `PR.test_generic_paper_drafts_reach_latex_with_existing_outputs_and_gates`；`CR.test_declared_but_missing_template_manifest_uses_full_reasoning_fallback` | PASS_MACHINE | 真实论文写作质量需专业审查 |
| W02 | WR/RT → paper carrier resolver | `PR.test_explicit_word_docx_survive_accumulated_generic_paper_keywords`；`PR.test_explicit_api_paper_intent_overrides_opposite_carrier_keywords` | PASS_MACHINE | 具体载体排版与视觉审查未完成 |
| W03 | OUT/PK → render_paper; audit_latex_project; package validator | `LC.test_normal_render_runs_one_formal_audit_and_persists_before_compiling`；`LA.test_compile_report_without_log_cannot_pass` | PASS_MACHINE | 正式项目 PDF 来源需按真实文件绑定 |
| W04 | REV/OUT → final review; PDF human page inspection | `FC.test_final_matrix_requires_current_source_and_pdf_hashes`；`FC.test_open_review_required_is_visible_but_not_a_hard_fail` | PENDING_MANUAL | CI 不具备逐页阅读真实 PDF 的人工审查证明 |
| W05 | OUT/PK → validate_submission_package; official rules check | `LA.test_official_packaging_refuses_unverified_rules`；`PK.test_two_question_required_analysis_package_rejects_omitted_question_and_stage` | PARTIAL | 当前赛事官方赛规/精确 allowlist/真实 ZIP 需单独核验 |
| C01 | RT/STATE → legacy resolver; historical project readers | `AC.test_legacy_resolver_projection_is_retained`；`PA.test_legacy_artifact_names_are_pre_schema_read_only_aliases` | PASS_MACHINE | 未穷尽所有历史用户项目 |
| C02 | ST/OUT → historical AUD consumers | `AR.test_first_source_change_fails_same_formal_check_in_read_and_write_modes`；`PK.test_official_missing_exact_file_is_rejected_by_generator_and_independent_validator` | PASS_MACHINE | AUD-01–18 逐项日志见 phase_e_six_domain_regression_audit.md §7；真实项目复演未覆盖 |
| C03 | REV/AS → final review; resolver; state snapshot | `FC.test_open_review_required_is_visible_but_not_a_hard_fail`；`FC.test_open_blocking_finding_forces_rejection`；`PS.test_invalid_encoding_yaml_shape_and_generation_fail_before_assurance` | PASS_MACHINE | 具体未知输入仍需 fail-closed/人工核实 |
| K01 | UE/ST → execution_provenance; project_snapshot; figures | `EP.test_source_only_hash_drift_is_not_numerical_result_staleness`；`EP.test_read_only_cleanup_suppresses_only_code_transition` | PASS_MACHINE | 旧回执仍绑定原执行源码，非新代码运行证明 |
| K02 | UE/ST → execution_provenance; sync_project | `EP.test_real_input_drift_is_not_suppressed_by_source_cleanup`；`SI.test_objective_change_changes_identity_hash` | PASS_MACHINE | 任意动态依赖/算法变更的实际影响需专业识别 |
| K03 | UE/MA → source checks; code/model conformance; MATLAB parser | `PY.test_harmless_sys_static_imports_and_path_text_remain_supported`；`PY.test_static_imports_numerical_aliases_and_text_are_preserved`；`CC.test_comment_edit_invalidates_binding_not_model_approval`；`MC.test_comments_and_transpose_are_distinct` | PARTIAL | 静态解析不能证明任意 Python/MATLAB 计算等价；历史结果只读消费独立 |
| K04 | UE/OUT → code delivery; MATLAB entry checker; historical figures | `MC.test_wrong_main_function_is_blocking`；`EP.test_accepted_workbook_is_bound_to_old_bundle_not_current_source` | PARTIAL | 任意移动/改名后的依赖闭包与正式运行需实际验证 |
| K05 | FE/OUT → figure mapping; reading_plan; export audit | `RP.test_verified_facts_and_style_are_narrow`；`AR.test_root_figure_mapping_is_hashed_and_changes_invalidate_without_reapproval` | PARTIAL | caption/图名/样式改动的真实视觉与论文引用待人工 |
| K06 | UE/FE → project_snapshot; qX_plot.m; figure consumer | `EP.test_read_only_consumption_requires_fully_verified_semantics`；`EP.test_accepted_workbook_is_bound_to_old_bundle_not_current_source`；`SY.test_figure_scope_checks_declared_export` | PASS_MACHINE | 真实 MATLAB 绘图执行及图像视觉仍待项目材料 |
| K07 | ST/UE → sync_project; 03B receipt | `SY.test_analysis_code_change_only_invalidates_analysis_chain`；`UE.test_analysis_change_does_not_invalidate_primary_quality` | PASS_MACHINE | 依赖 03B 的具体图仍需逐项确认 |
| K08 | WB/UE → workbook reader; execution_provenance | `EP.test_changed_accepted_workbook_bytes_block_consumption`；`RL.test_required_columns_are_enforced` | PASS_MACHINE | 真实数据变化的数值意义不能由哈希判断 |
| K09 | UE/WB → validate_user_execution; receipt binding | `UE.test_data_hash_mismatch_is_rejected`；`UE.test_workbook_changed_after_capture_cannot_acquire_qualification` | PASS_MACHINE | 需要真实新运行回执才能接受新结果 |
| K10 | STATE/MA → legacy read adapter; model approval validator | `PA.test_l0_historical_legacy_is_readable_but_never_verified`；`MA.test_old_project_without_approval_fields_is_not_backfilled` | PASS_MACHINE | 旧项目只读不等于可迁移/重新批准 |
| K11 | UE/MA → code delivery; semantic governance; read-only figure consumer | `EP.test_read_only_cleanup_suppresses_only_code_transition`；`EP.test_accepted_workbook_is_bound_to_old_bundle_not_current_source`；`SG.test_wording_only_change_updates_text_hash_without_semantic_stale` | PARTIAL | 正式整理代码静态质量/顺序与新提交复现资格须按真实项目裁决 |
| K12 | AS/FE → reading_plan; figure export; human visual review | `RP.test_verified_facts_and_style_are_narrow`；`AR.test_declared_export_deletion_and_escape_are_diagnosed` | PARTIAL | 图像实际配色/版式的视觉批准 PENDING_MANUAL |
| K13 | ST/UE → state transitions; validate_user_execution | `EP.test_real_input_drift_is_not_suppressed_by_source_cleanup`；`ST.test_model_dependency_invalidates_approval_but_result_dependency_preserves_it` | PASS_MACHINE | 新计算的 full-fidelity 回执与数值精度仍待真实项目 |
| K14 | OUT/PK → submission validator; official package verifier | `LA.test_reproducibility_manifest_detects_stale_packaged_pdf`；`LA.test_official_packaging_refuses_unverified_rules` | PARTIAL | 赛规是否要求源码复现、提交源码与运行源码是否一致需核验 |

**统计：** 50 个 ID 全部建立来源/消费者/方法映射；`PASS_MACHINE=34`，`PARTIAL=14`，`PENDING_MANUAL=2`。这里的机器 PASS **不表示该行完整业务目标（尤其人工边界）通过**；未发现可复现新运行时缺陷，未创建代码补丁。K03/G03 的具体反例与 G04/G06 的边界见阶段 E 审计及原计划。

## 4. 六领域的独立验收边界

| 领域 | 业务 Authority / 消费者 | 当前机器保护证据 | 保留的真实项目审查 |
|---|---|---|---|
| 题目分析 | `core/task_taxonomy.yaml`、`core/workflow_router.yaml`、`modules/01_problem_analysis.md` → resolver、Problem Contract | R02/R03/G01，路由通用回退与 design scope 反例 | **PENDING_MANUAL**：真实题目条件、依赖、数据、目标与候选结构是否正确 |
| 模型分析与建立 | `core/model_approval_contract.yaml`、`core/project_state.schema.yaml`、`modules/02_model_design.md` → semantic governance / model approval | G02–G07，双挑战声明、blocking finding、revision/identity stale | **PENDING_MANUAL**：公式/约束/候选模型优劣、两个独立 Challenge 的实际内容、用户明确批准 |
| 求解精度 | `core/numerical_verification_contract.yaml`、`core/workbook_schema.yaml` → `validate_user_execution.py` | G09/G18、`NV.test_residual_actual_is_recomputed_from_bottom_level_evidence`、MATLAB native 合成作业 | **PENDING_MANUAL**：真实数据、容差/收敛、数值稳定性、边界可行性与可信精度 |
| 求解规范 | `core/user_execution_contract.yaml`、`core/code_quality_contract.yaml`、`core/model_code_conformance_contract.yaml` → code delivery / receipt | G07–G09、K01–K14 的身份与阶段合同、Python/MATLAB CI | **PENDING_MANUAL**：用户 full-fidelity 执行、真实源码/依赖/数据/RUN_CONFIG/RUN_RECEIPT 与工作簿绑定 |
| 结果深化分析 | `core/user_execution_contract.yaml#analysis_necessity_state_mapping`、`core/output_contract.yaml` → analysis gate / 03B consumer | G10–G12、03B accepted/required/not_required 反例 | **PENDING_MANUAL**：是否真正需要稳健性/敏感性/替代方法，结论是否由真实结果支持 |
| 论文写作 | `core/writing_runtime_contract.yaml`、`modules/04_figure_evidence.md`、`modules/06_review_delivery.md` → reading plan / render / final review | G13–G16、W01–W05，三模板编译与 Production attestation | **PENDING_MANUAL**：新图语义/视觉批准、PDF 逐页人工审查、真实论文论证/引用与适用赛规 |

人工闭环材料应为**明确选定的一份真实项目**：赛题及附件/官方赛规版本、当前 `模型论文框架.md`、State/审批与双挑战记录、实际执行源码/依赖/数据指纹、完整 RUN_CONFIG/RUN_RECEIPT、accepted 主/必要 03B 工作簿、正式图及导出记录、论文源文件与 PDF、逐页审查和提交包/allowlist 记录。没有这套材料时，专业实例审查保持 PENDING，不制造演示项目或把 fixture 当作真实结果。

## 5. Gate 触发、输入、副作用与唯一事实源终审

| Gate / 处理 | Authority → 生产消费者 | 触发意图/阶段/scope 与输入 | 副作用 / 独立风险 | 跳过条件与测试 |
|---|---|---|---|---|
| `semantic_governance` | `core/model_approval_contract.yaml` + Router/Manifest → `validate_semantic_governance.py` | 当前模型语义进入设计/代码/正式交付适用边界；输入为 framework、revision/identity、State、read-set | 写模式可更新语义/失效状态；防止旧批准/旧身份被当成当前 | 仅按 resolver 当前计划；`SG.test_identity_change_without_revision_bump_fails_and_with_bump_stales` |
| `model_approval` | `core/model_approval_contract.yaml` + Manifest → `validate_model_approval.py` | 当前模型跨越代码交付边界；双重 Challenge、明确人工批准、当前 semantic identity | 阻断未批准/过期/有 blocker 的锁模与代码；不授予数学正确 | 不属于当前代码交付时不提前执行；`MA.test_pending_approval_fails`、`RR.test_c06_corrected_blocker_without_recheck_is_not_closed` |
| `code_delivery` | `core/user_execution_contract.yaml` + Manifest → `validate_code_delivery.py` | 新源码作为正式求解/分析代码交付；模型、源码/依赖、代码质量、阶段/scope | 可登记当前交付源码身份；**不得**重签旧 accepted 执行身份；保护静态可交付性 | 纯只读消费不作新代码验收；`UE.test_code_delivery_does_not_mark_solved`、`EP.test_accepted_workbook_is_bound_to_old_bundle_not_current_source` |
| `user_execution_receipt` | `core/user_execution_contract.yaml`、`core/workbook_schema.yaml`、`core/numerical_verification_contract.yaml` → `validate_user_execution.py` | 用户实际返回新工作簿/回执的 solve_validate；输入含运行源码/依赖/数据哈希、RUN_CONFIG/RUN_RECEIPT、数值证据 | 合格时 accepted 当前结果；拒绝不一致/降采样/数值质量失败；不可预先 PASS | 未执行、无工作簿、仅设计/只读图时跳过；`UE.test_data_hash_mismatch_is_rejected`、`UE.test_primary_workbook_acceptance_marks_solved` |
| `project_sync` | Router + `core/output_contract.yaml#project_sync` + Manifest → `sync_project.py` | 仅正式适用 delivery scope（results/figures/docx/latex/submission 等）；输入项目 State、framework、产物、哈希、依赖 | 可写 sync_report/传播 stale；防止错 scope、缺产物、过期数据；不代替批准 | design 不提前触发终稿门；`RT.test_design_scope_does_not_run_final_delivery_gates`、`SY.test_solved_project_does_not_require_analysis_before_formal_results_delivery` |
| `submission_package_validation` | Router + `core/output_contract.yaml#delivery_attestation` → `validate_submission_package.py` | 仅 submission；输入当前 PDF、ZIP、manifest、来源/哈希、已核验赛规 allowlist | 阻断漏项、错版、过期或非法包；不以 ZIP 存在判通过 | 非 submission 不执行；`LA.test_official_packaging_refuses_unverified_rules`、`PK.test_two_question_required_analysis_package_rejects_omitted_question_and_stage` |
| `claim_consumption` / `claim_evidence` / `model_code_conformance` | Manifest utility gates 与各自 `core/claim_consumption_contract.yaml`、`core/model_code_conformance_contract.yaml` → 专项脚本 | 显式/opt-in 的声明、主张/证据或模型-代码一致性核验；输入各自当前作用域证据 | 独立专项报告/阻断风险，不是通用路由的重复 PASS | 未激活时不强制运行；参见 `tests/test_claim_consumption.py`、`tests/test_model_code_conformance.py` |
| 多意图 gate 合并 | `core/workflow_router.yaml` → `resolve_runtime.py` / `reading_plan.py` | 同一调用、相同 gate 名/当前 scope 与输入；保留第一次出现顺序 | 减少重复调度，**不**跨阶段复用结果、不合并不同输入 | `RT.test_g17_multi_formal_intents_deduplicate_only_identical_gate_names`、`RP.test_distinct_conditional_triggers_for_same_source_are_preserved` |

本轮没有从调用链/日志/反例发现新的竞争双写或可安全删除的独立 gate。**阶段 C 不立项，State Schema 不迁移。** 文本声明重合与真实重复执行不同；不以名称相似为由删除。机器 State/semantic identity/stale、框架语义记忆、accepted 工作簿数值、执行回执来源、人工审查记录分别由既有 Authority 负责。

## 6. 兼容性、风险、回滚与收口条件

- **兼容：** R02/R03（未知竞赛/无分类通用回退）、R04/R06（显式 intent 与 legacy 推断边界）、R05/G17（多意图顺序与同次去重）、G01（design 非终稿）、K01/K06/K09/K11/K13（旧 accepted 只读与新运行身份分离）、G15（混合样式+新图规则并集）、S03/C01（旧项目/历史 workbook 只读适配）。每项均对应上表当前测试；部分真实实例/自然语言覆盖仍为 PARTIAL。
- **保留：** 双重 Model Challenge、Human Model Approval、Formula Trace/约束审查、数值质量、用户真实执行、Analysis Necessity、图表视觉、PDF 逐页、正式 package/赛规检查。删除或放松这些机制没有证据基础。
- **风险：** 测试是合成 fixture；G04 的具体话语识别、G06 的数学公式问题、W04 的实际 PDF 页面、K14 的赛规/源码复现要求等仍不具备真实项目证据。R01 的所有已登记竞赛模板选择未穷尽；K03 静态解析不能证明一般程序等价。
- **回滚：** PR #276/#278/#279/#280 等运行时变更按原单主题 PR 独立 revert，须保留既有用户项目的真实执行 provenance；本次文档 PR 可独立 revert，不更改机器状态或结果。任何新回归需先给出最小可复现反例，再单独代码 PR 与正式远端验收。
- **当前结论：** `main@eefca017` 的仓库正式 CI/Refresh 已 PASS，50 行机器证据追溯已形成但部分仍是 PARTIAL 或 PENDING_MANUAL；**此文档 PR 未完成自身最终 HEAD 的远端正式验收、合并后 main 复核前，不宣布最终仓库关闭**。真实项目人工审查单独 PENDING，不与仓库 CI 混淆。
