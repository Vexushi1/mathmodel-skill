# E1：52 场景与跨模块行为证据映射

本记录是维护验收索引，不是运行时 Authority，也不代表具体用户项目已完成数学、独立身份或视觉审查。A12+B16+C12+D12=52 个计划场景；一场景可以有多个已有行为测试，不为数量重复创建测试。以下映射由当前源码审阅形成，真正通过须以 E1 最终 head 的 GitHub 执行和 main 复验为准。

## 十条跨模块链

| 总计划14.4场景 | 实际行为证据与范围 |
|---|---|
| 源码偏离而数字合理 | 新E1 helper串联测试 + A2/B1来源资格；C仅在fixture实际绑定helper/workbook时过期，不要求所有回执隐式绑定 |
| helper→旧workbook→旧正文→旧PASS | tests/test_e1_cross_module_acceptance.py::CrossModuleAcceptanceTests.test_helper_drift_rejects_a_b_and_explicitly_bound_old_c_pass；真实Python两阶段seed、原A/B/C消费者及sync只读影响闭包 |
| 仅标题措辞 | 同类 test_title_wording_drift_preserves_accepted_numbers_but_stales_text_review；文本字节变更、数值/批准保持、旧C快照stale，不声称标题语义已人工核验 |
| analysis否定辅助措辞 | tests/test_b2b5_continuous_acceptance.py；实际accepted来源、局部stale、原数值/批准保护和修后新证明 |
| analysis否定直接答案/模型 | tests/test_b2b6_rejection_return.py + tests/test_b2c_runtime_integration.py；core_answer/model_validity分支按既有Authority回退 |
| 高分案例却缺条件 | tests/test_case_memory_retrieval.py 的 unknown/missing/conflict负例 + tests/test_case_references.py adopt-current-evidence与批准保护 |
| 审查读取时对象变化 | tests/test_review_receipts.py::test_c09_object_change_during_inspection_cannot_return_current + 原State/TX read-set反例；工具不实际产生可信审查 |
| 同一claim多消费 | tests/test_claim_consumption.py + tests/test_b2b5_continuous_acceptance.py 的摘要/结果/Figure义务与影响清单 |
| 旧项目不开扩展 | A/B缺policy短路、C optional、D无引用旧State、route disabled反例 + immutable Optimization baseline差分 |
| 部分新字段冒充完整协议 | A/B/C/D未知/残缺版本负例，不能legacy fallback；纯当前State缺字段无法证明过去没有被删，历史需要单独审阅 |

## A/B 映射与来源链

# E1 A/B scenario mapping and cross-module audit

Read-only source audit baseline: `main@b9f20400e7e58a0717eaa2b88ebcce116c7d0613`, Skill 10.17.0. No local lint, unittest, generator, MATLAB or LaTeX was run. A mapped method is source evidence of behavior assertions, not a new executed PASS. Prior main full-regression evidence covers 2438 cases per Windows Python version; the new E1 tests remain unexecuted until remote CI.

## Authority, producer, consumer and invalidator

- A Authority: `core/model_code_conformance_contract.yaml`, canonical opt-in State fields in `core/project_state.schema.yaml`, and original approval in `core/model_approval_contract.yaml`.
- A producer: `model_code_conformance.inspect_project` captures current SIB/source/read set; `validate_code_delivery.update_state` writes delivery bindings; `validate_user_execution.validate_one` plus the existing project transaction writes accepted run/workbook bindings. Source mappings do not prove mathematics or accept numbers.
- A consumer: `conformance_gate.inspect_gate`; current numerical eligibility belongs to `runtime_assurance.hydrate_project_context`.
- A invalidators: whole source bundle (including declared helpers), inputs, mapping/Authority, stage/question/backend mismatch, and the optimistic read set. `sync_project.synchronize` and `state_transitions.apply_transition` propagate source changes while preserving unrelated mathematical approval.
- B Authority: `core/claim_evidence_contract.yaml`, `core/claim_consumption_contract.yaml`, existing `core/writing_reasoning_contract.yaml` (Claim Strength / analysis disposition), Numeric Profile and Title Claim records in canonical State.
- B producer: explicit typed claim/evidence and fragment dependency records; actual numerical values are selected read-only from originally qualified workbook bytes by `claim_sources.Sources.qualify` and `claim_workbook.Workbook.select`.
- B consumers: `claim_evidence.inspect_project`, `claim_consumption.inspect_project`, selected text/Figure gates, original LaTeX audit/compile/submission coordinators. Own-result evidence cannot be substituted by a citation source.
- B invalidators: original source/input/workbook eligibility remains upstream; current modify/reject dispositions generate `stale_reason_paths`, and `sync_project` writes exact claim/fragment closure. Question-level source invalidation produces `stale_questions` and `stale_paper_fragments` rather than certifying stale matching numbers.
- C chain Authority: `core/review_receipt_contract.yaml` plus `core/review_receipt_consumption_contract.yaml`. C producer records actual declared review scope; read-only `review_receipts.inspect_project` checks captured files/State/Authority and C2 `review_receipt_consumption.evaluate_gate` accepts only scoped current full review pairs. A paper receipt must bind its active paper sources, but no new rule requires every receipt to bind every helper. The new E1 helper fixture explicitly adds helper/workbook bindings to its scope.

## A01-A12

| ID | Exact behavior methods | Coverage boundary / remaining E1 need |
|---|---|---|
| A01 | `tests.test_model_code_conformance.ConformanceTests.test_constraints_are_enumerated_from_current_sib_not_author_list`; `.test_phantom_anchor_and_duplicate_symbol_do_not_pass`; `tests.test_conformance_execution.A2BaselineGaps.test_required_missing_mapping_does_not_pass_delivery`; `.test_direct_writer_cannot_bypass_missing_mapping` | Current selectors and genuine source symbols; writer cannot bypass mapping. |
| A02 | `tests.test_model_code_conformance.ConformanceTests.test_reverse_clip_is_observation_and_requires_explicit_adjudication` | Unregistered clipping creates review requirement; explicit lexical adjudication is not proof of activation. |
| A03 | `tests.test_model_code_conformance.ConformanceTests.test_main_unchanged_helper_changes_invalidate_whole_record`; `tests.test_conformance_execution.A2ProtocolTests.test_raw_input_drift_and_helper_drift_are_not_laundered` | Existing A bundle checks; new E1 test joins A/B/C plus old workbook/claim/receipt in one executed seed. |
| A04 | `tests.test_model_code_conformance.ConformanceTests.test_robin_to_value_boundary_changes_fail_direct_syntactic_reference` | Controlled Python and MATLAB flat-source syntactic mismatch; not a symbolic equivalence engine. |
| A05 | `tests.test_model_code_conformance.ConformanceTests.test_equivalent_transform_is_review_not_false_failure`; `tests.test_claim_values.ClaimValuesTests.test_time_conversion`; `.test_percent_ratio_conversion_is_explicit` | Legal equivalent transform yields accurate needs_review, not false proof/failure; explicit supported unit conversions pass. |
| A06 | New `tests.test_e1_cross_module_acceptance.ExplicitScenarioAcceptanceTests.test_a06_approved_approximation_is_never_reported_as_strict_equivalence` | Previously no explicit `approved_approximation` behavior test despite shared implementation branch. New negative scenario explicitly keeps mathematical_equivalence not_established. |
| A07 | `tests.test_model_code_conformance.ConformanceTests.test_penalty_name_does_not_imply_model_error`; original numerical-quality checks below | The algorithm name alone cannot reject. Original constraint verification retains numerical ownership. |
| A08 | `tests.test_conformance_execution.A2ActualExecutionTests.test_pqs_failure_cannot_create_conformance_acceptance`; `tests.test_v714_numerical_verification.V714NumericalVerificationTests.test_feasibility_contradiction_is_rejected`; `.test_residual_actual_is_recomputed_from_bottom_level_evidence`; `.test_consistent_failed_residual_row_cannot_be_hidden_by_lax_summary_threshold` | Failed original quality evidence cannot gain A acceptance. These fixtures verify quality separately rather than solving a complete penalty optimizer. |
| A09 | `tests.test_model_code_conformance.ConformanceTests.test_dynamic_code_is_needs_review_not_silently_executed`; `tests.test_conformance_integration.OptInTests.test_matlab_nested_functions_are_not_silently_treated_as_flat` | Unsupported structures never silently pass or execute. |
| A10 | `tests.test_model_code_conformance.ConformanceTests.test_analysis_record_cannot_be_replayed_for_primary`; `tests.test_conformance_execution.A2ProtocolTests.test_primary_and_analysis_policies_are_separate`; `tests.test_conformance_upstream_read_set.UpstreamReadSetTests.test_analysis_inventory_captures_upstream_without_forcing_primary_policy` | Primary/analysis binding ownership remains separate; analysis upstream still observed. |
| A11 | `tests.test_model_code_conformance.ConformanceTests.test_comment_edit_invalidates_binding_not_model_approval`; `tests.test_conformance_execution.A2RoutingAndReplayTests.test_redelivery_mapping_change_requires_reacceptance_and_preserves_model_approval` | Source identity requires redelivery; unrelated model approval remains. |
| A12 | `tests.test_model_code_conformance.ConformanceTests.test_state_framework_and_source_midread_changes_fail_without_writes`; `tests.test_conformance_execution.A2TransactionTests.test_delivery_commit_rejects_late_source_input_framework_and_state_edits`; `tests.test_conformance_upstream_read_set.UpstreamReadSetTests.test_analysis_delivery_rejects_late_upstream_entry_helper_or_auxiliary` | Real read-set conflict, no stale successful commit. |

## B01-B16

| ID | Exact behavior methods | Coverage boundary |
|---|---|---|
| B01 | `tests.test_claim_consumption.ClaimConsumptionIntegrationTests.test_b01_second_location_110_conflicts_with_same_live_100`; `.test_b01_live_original_100_matches_two_location_profiles_and_is_readonly`; `tests.test_b2c_total_acceptance.B2cSelectedLatexAcceptanceTests.test_b01_b09_b10_b11_b12_b16_acceptance_matrix` | Genuine accepted value selected, actual summary/body locations compared. |
| B02 | `tests.test_claim_values.ClaimValuesTests.test_improvement_has_explicit_direction`; `.test_zero_negative_base_not_called_improvement` | Comparison direction and denominator semantics checked. |
| B03 | `tests.test_claim_values.ClaimValuesTests.test_percent_and_points_are_distinct`; `.test_percent_to_points_conversion_not_silent` | Percent and percentage-point types cannot be merged. |
| B04 | `tests.test_claim_values.ClaimValuesTests.test_mismatched_samples_rejected`; `.test_duplicate_observation_not_aggregate_replication`; `tests.test_claim_workbook.ClaimWorkbookTests.test_row_order_does_not_select_wrong_scenario` | Scenario/sample identity and duplicates handled without guessing. |
| B05 | `tests.test_claim_workbook.ClaimWorkbookTests.test_duplicate_headers_and_duplicate_keys_rejected`; `.test_no_match_and_missing_sheet_rejected`; `.test_two_sheet_names_cannot_disguise_one_physical_sheet` | No ambiguous selector auto-choice. |
| B06 | `tests.test_claim_values.ClaimValuesTests.test_zero_negative_base_not_called_improvement`; `.test_finite_numbers_and_boolean_rejected`; `.test_unsupported_unit_not_guessed`; `tests.test_claim_workbook.ClaimWorkbookTests.test_profile_cannot_override_actual_units` | Invalid units/numbers/denominator reject. |
| B07 | `tests.test_claim_graph.ClaimGraphTests.test_direct_and_indirect_cycles`; `.test_duplicate_id_and_unknown_reference`; `.test_depth_budget` | Cycle/missing dependency and resource limits fail closed. |
| B08 | New `tests.test_e1_cross_module_acceptance.ExplicitScenarioAcceptanceTests.test_b08_external_citation_cannot_substitute_an_own_result_source` | Existing own-workbook Schema rejects citation source; explicit B08 negative fixture was absent before E1. |
| B09 | `tests.test_b2b2_text_gate.B2b2TextGateTests.test_b09_b10_b16_unregistered_strong_wording_fails_with_source_location`; `tests.test_claim_graph.ClaimGraphTests.test_strong_claim_not_proved_by_correct_arithmetic`; selected-carrier matrix above | Arithmetic does not establish global optimality or full semantics. |
| B10 | Same strong-wording tests plus `tests.test_p7_conditional_analysis_appendix.TestP7ConditionalAnalysisAppendix.test_not_required_without_reason_fails_closed` | Analysis not_required is not an analyzed robustness claim. |
| B11 | `tests.test_b2b5_continuous_acceptance.B2b5ContinuousAcceptanceTests.test_b11_same_selected_value_drift_preserves_original_artifact_invalidation`; `tests.test_b2b3b_figure_source.FigureSourceTests.test_workbook_replaced_with_same_selected_value_is_not_accepted`; `tests.test_claim_evidence.ClaimEvidenceIntegrationTests.test_source_status_alone_cannot_qualify_changed_workbook` | Unchanged selected scalar cannot waive whole artifact qualification. |
| B12 | `tests.test_b2b5_continuous_acceptance.B2b5ContinuousAcceptanceTests.test_b12_reject_auxiliary_continuous_repair_retains_accepted_primary`; `.test_b12_modify_auxiliary_stales_only_dependents_and_retains_accepted_primary`; `tests.test_b2b6_rejection_return.B2b6RejectionReturnTests.test_core_answer_reject_returns_to_solve_and_removes_result_qualification`; `tests.test_b2c_runtime_integration.SelectedPolicyStructuredSyncTests.test_auxiliary_rejection_keeps_primary_state_under_1_5`; `.test_core_rejection_returns_to_solve_validate_under_1_5` | Auxiliary wording preserves numbers; direct-answer contradiction returns to existing solver gates. |
| B13 | `tests.test_claim_profiles.ClaimProfileTests.test_declared_scientific_precision_control`; `.test_percent_profile_requires_actual_percent_quantity`; `tests.test_claim_consumption.ClaimConsumptionIntegrationTests.test_b01_equal_number_with_wrong_body_precision_needs_review` | Numeric Profile is authoritative; not raw string matching. |
| B14 | `tests.test_claim_workbook.ClaimWorkbookTests.test_formula_never_uses_cached_value` | Formula text/cache cannot become confirmed numeric source. |
| B15 | `tests.test_claim_graph.ClaimGraphTests.test_dangerous_assertion_is_not_evaluated`; `tests.test_model_code_conformance.ConformanceTests.test_expression_payload_cannot_execute_python` | Executable expression payload is not run. |
| B16 | `tests.test_b2b2_text_gate.B2b2TextGateTests.test_b16_incomplete_figure_inventory_fails_without_caption_candidates`; `tests.test_b2c_total_acceptance.B2cSelectedLatexAcceptanceTests.test_single_file_latex_omitted_required_body_claim_fails_closed`; `tests.test_b2c_total_acceptance.B2cSelectedDocxAcceptanceTests.test_docx_omitted_required_body_claim_fails_closed` | Registered omissions and unregistered strong/numeric candidates are machine checks; human semantic/visual coverage remains not_assessed. |

## Section 14.4 combined gaps and additions

1. Helper -> unchanged old workbook -> unchanged paper claims -> old review PASS: new combined test, A/B reject original source eligibility, explicitly bound C receipts become stale, old source/workbooks preserved, existing sync reports Q1 and registered fragment impact closure. No gate PASS mocked.
2. Title wording only: new combined test changes actual active main.tex title metadata; A/B numeric checks and accepted primary persist, bound C1/C2 text reviews become stale. This observes identity/freshness only; the machine does not approve title semantics.
3. Auxiliary vs direct answer: existing B2b5/B2b6/B2c full continuous fixtures already cover numerical preservation vs stage return, including multiple registered consumer fragments. Reuse their tests rather than duplicate a large seed.
4. One claim in multiple consumption places: existing B2b5 `test_core_claim_disposition_stales_its_figure_and_all_registered_consumptions`, B2b stale-writer tests and claim fragment closure tests assert exact sets and fan-out/cycles.
5. Receipt race: existing A2 delivery/receipt transaction tests and C1 `ReviewReceiptTests.test_c09_object_change_during_inspection_cannot_return_current` exercise read-set. C1 is read-only; no new receipt writer is invented.
6. Legacy/partial protocol: existing `ClaimConsumptionIntegrationTests.test_missing_policy_does_not_call_b1_or_scan_tex`, `A2ProtocolTests.test_legacy_off_does_not_call_a1_or_parse_user_source`, C2 optional-policy tests and malformed policy fail-closed cases cover off behavior; CD agent supplies unified E1 mapping.

The exact 52-scenario matrix should distinguish full integrated fixtures, constituent behavior tests, and intentionally bounded/not_assessed semantics; it must not turn source inspection into executed acceptance.


## C/D、兼容与安全映射

# E1 C/D、兼容与安全只读审计

基线：`main@b9f20400e7e58a0717eaa2b88ebcce116c7d0613` / Skill 10.17.0 / State 8.15.0。审计读取 `work/mathmodel-skill-d2-case-retrieval` 的已冻结源码。没有执行本地 lint、测试、生成器、MATLAB、LaTeX 或 GitHub workflow；以下是行为测试源码映射，不把读取源码写成新的测试通过证据。最终执行证据由 E1 精确 head 的 GitHub CI 补齐。

## 1. C01—C12 行为映射

下表简写：`RR=tests/test_review_receipts.py`，`RC=tests/test_review_receipt_consumption.py`。

| 场景 | 现有行为测试方法 | 核读到的实际断言 |
|---|---|---|
| C01 虚构独立性 | RR `test_c01_self_assertion_and_fake_run_id_do_not_prove_independence`；RC `test_c10_failed_or_unknown_command_and_untrusted_native_claim_fail` | 自填 independent 字段不能提升；hand-typed host run 和传入 fake_host 仍 unverified；native 自声明在 C2 failed |
| C02 旧输入 PASS | RR `test_c02_old_pass_is_stale_after_bound_input_changes`；RC `test_policy_or_input_change_and_partial_policy_fail_closed` | 框架/语义身份变化使旧记录 stale 或门失败，不靠旧 PASS 放行 |
| C03 Authority 变化 | RR `test_c03_applicable_authority_changes_only_affected_receipt`、`test_c03_common_review_authorities_are_required_and_fingerprinted`、`test_paper_review_tracks_delegated_module06_authority` | 规范实际字节与 criteria version 必须绑定；正文审查跟踪被委托写作 Authority |
| C04 复制两轮 | RR `test_c04_copied_pass_cannot_establish_two_separate_reviews` | copied verdict + 相同 pass_id 不能得到 current；C2 `_shared_inputs`、distinct pass 和 substantive payload 再校验 |
| C05 可用分开审查 | RR `test_c05_distinct_separated_passes_remain_available`、`test_c05_separated_passes_need_traceable_source_and_pass_ids` | 正例 current 且方式准确保持 separated_passes；缺 traceability 降 unverified |
| C06 corrected 不等于复验 | RR `test_c06_corrected_blocker_without_recheck_is_not_closed`、`test_c06_other_gate_cannot_reverify_model_finding`、`test_c06_local_finding_recheck_keeps_full_review_scope_explicit`、`test_c06_full_new_pass_can_recheck_only_affected_finding`、`test_c06_reverified_finding_stays_closed_through_full_replacement_chain` | corrected blocker 不能 current；wrong gate recheck 拒绝；稳定 finding ID、affected checks/objects 与 current successor 核验 |
| C07 局部扩大范围 | RR `test_c07_partial_recheck_cannot_claim_full_scope`、`test_c07_current_full_review_can_supersede_stale_predecessor`、`test_c07_supersedes_cycle_cannot_make_all_reviews_current`、`test_c07_full_replacement_chain_is_independent_of_record_order`、`test_c07_different_criteria_cannot_supersede_prior_review`、`test_c07_finding_scope_must_match_original_check_objects`、`test_c07_pass_requires_union_coverage_of_declared_objects`；RC `test_local_recheck_cannot_replace_full_review` | 局部不能替代全量；真正 current 全量替代合法；环与 criteria 错配拒绝；对象/check 联合集合必须覆盖 |
| C08 回执自失效 | RR `test_c08_receipt_write_and_unrelated_generation_do_not_self_invalidate`、`test_c08_raw_state_file_cannot_be_a_review_input` | 写回回执/无关 generation 不过期；真正 semantic identity 改变 stale；禁止整个 State raw hash 自引用 |
| C09 中途变化 | RR `test_c09_object_change_during_inspection_cannot_return_current` | 通过 interleave 在 inspection 中更改框架，返回 blocked，已有 receipt 不能 current；C1/C2 finally 再查 State/所有观测字节 |
| C10 命令造假 | RR `test_c10_pass_command_requires_known_zero_exit`、`test_c10_host_observation_can_refute_but_not_attest_a_pass`；RC `test_c10_failed_or_unknown_command_and_untrusted_native_claim_fail` | 未知/nonzero exit 拒绝；host observation 冲突可否定，自声明 zero 不提升 trusted attestation |
| C11 未数值复现 | RC `test_model_pair_passes_only_scoped_receipt_eligibility` | passed 仅 scoped_receipt_eligible；numerical_reproduction、accepted_workbook、human_model_approval、final_delivery 均 not_granted |
| C12 人工批准不被替代 | RC `test_model_pair_passes_only_scoped_receipt_eligibility`；`tests/test_v711_model_approval_gate.py::test_c12_receipt_pass_cannot_replace_pending_human_approval`、`test_c12_active_receipt_failure_blocks_otherwise_approved_model`、`test_c12_explicit_state_cannot_mix_canonical_review_policy`、`test_c12_explicit_policy_state_must_be_canonical`、`test_c12_no_policy_preserves_existing_approval_gate` | C2 单内核正例仍 pending；原批准门与 C2 失败组合。后者 model glue 测试 mock `_evaluate_model_receipts`，不能当完整链行为证据 |

### C 正文和 Figure 证据范围

RR `test_paper_review_binds_selected_main_not_a_decoy`、`test_paper_review_binds_active_child_tex`、`test_paper_review_binds_approved_active_figure_image`：真正 selected carrier 闭包改变影响当前审查，未选 decoy 变化不影响。RC `test_final_review_requires_active_source_and_all_matrix_families`、`test_active_approved_figure_requires_both_role_object_coverage`：所有当前 paper-source/source/figure/rendered 对象、current matrix check families 必须在双方 scope/check 中。它们核验身份、覆盖和声明一致性，不能证明人类语义与视觉审阅发生。

## 2. D01—D12 行为映射

下表简写：`CM=tests/test_case_memory.py`，`DR=tests/test_case_memory_retrieval.py`，`CR=tests/test_case_references.py`。

| 场景 | 现有行为测试方法 | 核读到的实际断言 |
|---|---|---|
| D01 不兼容条件 | DR `test_cross_sectional_prediction_is_not_a_temporal_match`、`test_spatial_gradient_is_not_a_lumped_balance`、`test_parameter_inference_does_not_borrow_prediction_or_simulation`、`test_unknown_typed_trait_and_missing_conditions_are_conditional`、`test_known_variable_domain_conflict_excludes_the_case`、`test_violated_condition_is_excluded_in_both_ranking_modes`、`test_future_information_conflict_is_excluded` | 冲突排除/no_match；unknown 和缺条件明确 conditional，不包装为已满足 |
| D02 跨题名相似 | DR `test_seven_cross_title_development_queries_find_their_structural_case` | 7个合成结构目标 top-1 命中，带 missing_conditions、synthetic evidence、rationale/origins。仅开发检查，不是独立效果验证 |
| D03 无实测却宣称 observed | CM `test_d03_unperformed_validation_cannot_be_declared_observed`、`test_d03_completed_checks_and_source_reported_outcomes_need_real_evidence` | 伪 observed、无来源锚点、伪 performed checks 等无法通过准入 |
| D04 来源/权利 | CM `test_d04_unknown_license_and_missing_public_use_are_rejected_in_every_status`、`test_d04_real_sources_do_not_self_certify_public_authorization` | 每种生命周期都检查许可；用户/真实来源自填公开授权不能进入正式 reviewed |
| D05 提示注入 | CM `test_d05_instruction_text_remains_inert_data`；DR `test_prompt_text_is_data_and_cannot_execute_or_fetch` | patch executable sinks eval/shell/process/network 使任何调用必错；实际字符串照数据保留，不写入文件、不执行 |
| D06 同源多数 | CM `test_d06_forks_in_one_origin_group_form_one_indexed_group`、`test_d06_same_core_under_different_origins_does_not_create_a_majority`、`test_d06_text_case_and_whitespace_do_not_create_an_independent_core`、`test_unresolved_near_duplicates_cannot_enter_reviewed_recommendations`；DR `test_all_member_origins_survive_forks_and_transitive_group_bridges`、`test_excluded_nonrepresentative_origin_excludes_the_entire_bridge` | 同源/同核心合为一个连通 group，所有成员 origins 保留；非代表 origin 的 exclusion 也排除整组 |
| D07 无匹配 | DR 上述3个不兼容真实 query 方法 | 合法 no_match，不伪造 cases |
| D08 变更/撤回 | CM `test_current_index_becomes_stale_when_a_case_changes_or_is_withdrawn`、`test_index_checks_current_source_bytes_even_with_unchanged_stat`；DR `test_withdrawal_is_seen_by_a_fresh_query_without_old_cache`、`test_rebound_source_change_produces_a_new_binding_without_old_cache`；CR `test_withdrawn_case_requires_review_and_does_not_revoke_numerical_acceptance`、`test_context_or_current_evidence_drift_requires_review_without_model_changes` | fresh bytes 改变 index/bindings；原 snapshot 断言失败；持久引用 needs_review，仍不撤销批准或数值 accepted |
| D09 检索不能批准 | DR `test_match_is_not_execution_approval_or_numerical_evidence`；CR `test_adoption_needs_current_question_evidence_while_reference_can_be_unassessed`、`test_synthetic_approval_declarations_are_preserved_by_reference_write`、`test_unqualified_synthetic_acceptance_declaration_cannot_be_repaired_by_reference`、`test_authority_stale_profile_is_preserved_by_reference_write` | match 不授权执行、不提供批准/observed；writer 候选 delta 仅 references/generation，adopt 有当前题依据，不能修复旧 qualification |
| D10 隐私泄露 | CM `test_d10_private_paths_accounts_and_credentials_are_rejected_without_echo`、`test_d10_ids_schema_paths_and_custom_index_errors_never_echo_credentials`；CR `test_absolute_escape_and_private_path_diagnostics_do_not_echo_inputs` | 准入/引用路径和error不回显绝对路径、账号或密钥；仍不是完整人工隐私审查 |
| D11 污染评测 | DR `test_seed_derived_queries_are_explicitly_contaminated_and_origin_filtered`、`test_development_evaluation_never_reports_independent_performance`、`test_development_positive_cannot_hide_its_origin_as_an_independent_query`、`test_development_fake_or_wrong_group_origins_are_rejected`、`test_development_expected_cases_must_exist_and_remain_reviewed`、`test_development_originless_negative_is_still_not_independent_performance` | expected案例origin exclusion整个组；seed-derived含originless negative都不允许标独立评估；真实独立效果 not_assessed |
| D12 关闭/缺失 | DR `test_off_does_not_read_even_a_missing_corpus`、`test_missing_index_is_unavailable_and_never_regenerated`、`test_stale_index_is_unavailable_and_never_repaired`、`test_cli_disabled_ignores_missing_query_and_corpus`；CR `test_missing_or_stale_retrieval_never_writes_a_reference`；`tests/test_case_memory_routing.py` 四个方法 | disabled不读取corpus；missing/stale unavailable且不自动修复；路由不会读取库或新增qualification gate；既有 modules/gates/assurance 保持 |

## 3. 兼容、只读、故障恢复和边界

| 必测面 | 实际方法与边界 |
|---|---|
| 未激活旧项目 | RR `test_inspection_is_read_only_and_missing_or_unknown_protocol_is_explicit`；RC `test_optional_policy_is_closed_and_legacy_state_is_unchanged`；CR `test_old_state_without_optional_references_is_still_valid`；`tests/test_conformance_execution.py::test_legacy_off_does_not_call_a1_or_parse_user_source`；`tests/test_claim_evidence.py::test_missing_record_does_not_load_new_contract_or_workbook`；`tests/test_claim_consumption.py::test_missing_policy_does_not_call_b1_or_scan_tex`。缺字段只读/保留现有流程，不能用来追认已验证资格。 |
| 部分/未知新协议 | `tests/test_review_receipt_schema.py::test_partial_unknown_and_self_referential_records_rejected`；RC `test_policy_or_input_change_and_partial_policy_fail_closed`；CR `test_unknown_reference_protocol_and_closed_record_fields_block_consumption`；DR `test_unknown_protocol_fields_and_taxonomy_values_block`；CM `test_unknown_fields_and_document_versions_fail_closed`；`tests/test_claim_consumption.py::test_partial_unknown_or_mismatched_policy_blocks_before_b1`。均为明确 failed/blocked，不能静默 legacy fallback。 |
| 通用 State 单快照 | `tests/test_project_state_read_snapshot.py::test_same_generation_byte_change_is_rejected`、`test_dependency_hydration_reuses_the_same_snapshot`、`test_existing_journal_is_not_implicitly_recovered_or_removed`、`test_journal_appearing_during_planning_is_rejected_without_recovery`、`test_all_project_routes_not_only_narrow_ones_reject_state_changes`。 |
| D1/D2 源时点混合 | CM `test_current_bytes_are_rechecked_for_each_corpus_input`；DR `test_mid_read_change_returns_unavailable_instead_of_mixed_snapshot`、`test_corpus_read_set_checks_raw_same_size_same_timestamp_changes`、`test_skill_read_set_checks_authority_taxonomy_and_implementation_changes`。 |
| writer 并发冲突 | CR `test_raw_state_drift_with_same_generation_size_and_timestamp_blocks`、`test_stale_generation_state_and_retrieval_hashes_block_write`、`test_precommit_project_scope_and_evidence_changes_block_without_journal`、`test_precommit_corpus_source_schema_and_features_changes_block`、`test_precommit_external_authority_change_is_checked_on_its_actual_path`、`test_changed_writer_bytes_cannot_be_bound_to_an_old_loaded_module`、`test_precommit_state_schema_change_cannot_commit_an_old_validation`。 |
| prepared 故障与显式恢复 | CR `test_prepared_fault_requires_explicit_rollforward_and_keeps_generation_bound`：after_journal_prepared fault保留journal和旧State，preview拒绝；原 `recover_project_transaction` roll-forward，再写完全相同引用 unchanged。不承诺所有失败回滚。 |
| 通用事务更多故障点 | `tests/test_project_transaction_read_set.py::test_guarded_interruption_recovers_forward_at_each_replace_boundary`、`test_third_party_write_after_prepare_is_not_overwritten`、`test_prepared_staged_tamper_is_not_written`、`test_two_guarded_writers_do_not_rebase_stale_snapshot`、`test_guarded_commit_does_not_implicitly_recover_prepared_journal`、`test_guarded_commit_does_not_silently_clean_other_journal_states`；`tests/test_v900_project_transaction.py::test_validation_failure_leaves_all_live_files_untouched`、`test_recovery_after_framework_replace_before_state_replace`、`test_recovery_after_state_replace_before_report_replace`、`test_recovery_rejects_unknown_third_party_generation`。 |
| 路径/解析/资源 | CM `test_parser_file_string_depth_and_node_budgets_fail_closed`、`test_authority_total_byte_budget_is_enforced_and_cannot_be_relaxed`、`test_invalid_utf8_nonfinite_json_and_unsafe_yaml_are_rejected`、`test_schema_remote_and_nonlocal_refs_are_rejected_without_network_calls`、`test_corpus_file_symlinks_cannot_escape_the_read_root`；DR `test_query_and_projection_budgets_fail_closed`、`test_nested_projection_hits_depth_budget_before_consumption`、`test_lowered_report_budget_rejects_oversized_retrieval_context`、`test_remote_authority_reference_is_rejected_without_network_access`；CR `test_input_budget_blocks_without_echoing_large_text`。 |
| 生成物唯一性 | `tests/test_case_memory_generated.py::test_missing_case_index_is_generated_in_skill_index_and_manifest_without_writing`、`test_source_revision_changes_generated_case_identity_and_manifest`、`test_case_retirement_changes_generated_index_and_manifest`、`test_blocked_corpus_cannot_be_published_as_generated_metadata`、`test_old_root_without_case_pointer_keeps_original_five_outputs`。 |

## 4. Authority / producer / writer / consumer / invalidation 图

| 对象 | 唯一事实源/Authority | producer 与 writer | validator/consumer | 失效规则 |
|---|---|---|---|---|
| C1 optional `review_receipts` | shape=`core/project_state.schema.yaml` `$defs/review_receipts`；语义=`core/review_receipt_contract.yaml`；已有模型/写作规则仍各自 Authority | producer 是实际审查的有限范围声明。C1 validator 不产生审查、不执行命令、不持久化；contract `project_writer:none_in_C1`、stdout only。不要虚构新自动 writer 或可信宿主 attestor。 | `scripts/review_receipts.py::inspect_project` | 每次重查被审 State selected pointers、project file raw hashes、Authority fingerprints；输入变化 stale；未核执行 unverified；replacement 需 current PASS/完整范围；generation与整个State hash不是语义快照依赖。 |
| C2 `review_receipt_policy` | shape=State `$defs/review_receipt_policy`；消费=`core/review_receipt_consumption_contract.yaml`；current check families取原 model approval / final matrix | producer 为明确按 gate/Qn 激活的项目记录；C2 没有 writer，不能自动建立缺失回执。 | `review_receipt_consumption.evaluate_gate`→`validate_model_approval.py`（model_challenge）/`sync_project.py`（submission）/`validate_submission_package.py`（final）；draft是手动审查步骤，未变写作 runtime自动run_now | C1与C2 read-set合并必须一致；policy+Authority入快照；每个role共享同输入、独立pass ID、实际scope/check覆盖；failed blocked现有消费，not_assessed保留未声明gate路径。没有trusted host adapter。 |
| D1 `knowledge/case_memory` corpus | `knowledge/case_memory/schema.yaml` + limited pinned admission implementation；每条来源锚点、许可、隐私和lifecycle | 来源/卡片由显式仓库变更产生；无跨项目自动采集。 | `scripts/case_memory.py::inspect_corpus/build_index/check_index`，供D2 consume | raw字节read-set、安全解析/资源预算、实际source hash和锚点、同源连通分组；withdrawal排除reviewed索引。 |
| D1 canonical `index.json` | 当前corpus确定性派生；无第二种业务事实源 | 唯一canonical落盘 writer=`scripts/generate_indexes.py`（GitHub `refresh-generated` bot）；`build_index`本身只返回payload | existing generated contract / manifest / D2 current-index核验 | 每次比较当前bytes派生payload；变化/撤回/旧hash不接受；missing索引不能隐式重建为当前。 |
| D2 transient retrieval report | `core/case_memory_retrieval_contract.yaml`1.0.0＋current taxonomy；manual synthetic `retrieval_features.json`非observed事实 | `case_memory_retrieve.query_cases/capture_query`只读产生报告，不落用户State | route工具导航；显式Case Reference preview/writer | 读同一D1 corpus+index+features+Authority+实现read-set，缺条件conditional、冲突排除、samegroup只一hit；无跨调用旧PASS缓存。 |
| D2 persistent `decisions.Qn.case_references` | State `$defs/case_references/case_reference_record`；当前case/source/context/固定规则哈希 | 唯一业务writer=`case_references.record_reference(write=True)`，通过既有`commit_project_state`；默认preview；只有reference和generation允许delta | `case_references.inspect_references`读取并派生current/needs_review；原资格gate仍独立 | current项目scope/evidence与case/source/rules逐次校验；撤回/变化needs_review；query/filterhash历史provenance，不重建未保存query、不声称重算排名；不撤销numeric/model资格。 |
| 所有项目State持久化 | State Schema / state transition semantics | 既有`project_transaction.commit_project_state`协调；staged validator+expectedgeneration+read-set；C/D不开第二事务层 | snapshot captures / existing explicit recovery | prepared阶段按原恢复roll-forward；pendingjournal拒绝新读写；project/corpus跨根仅optimistic边界复核，未承诺跨根原子性。 |

### 已知且诚实的边界

- C 可核对声明/范围/输入与反例，不能凭 author/host字符串证明原生独立或人类审查。trusted host adapter当前 unavailable，不能在 E1 文档改成 verified。
- 当前State不能区分真正legacy缺policy与人为删除过往policy；已启用后删除需显式治理迁移，若有持久Git/audit history应比较。没有历史时必须保留该检测限制，不能声称机器已证明不存在降级。
- D 真实素材准入/独立效果仍未授权、不做；当前7例synthetic/10查询development不能证明比赛精度、获奖或统计稳定收益。
- Case Reference保留query/filter hash但不保留原query；inspect诚实报告 `ranking_not_recomputed` 和 `original_query_not_available`，只核对当前source/context/fixedrules。此已设计边界不是 E1 要擅自扩协议补功能。
- 数学等价、任意正文整体语义、人工图形版式QA仍有 `not_assessed`/需要人工核验范围。

## 5. E1 应补的最小行为缺口

1. 真实混合 A/B/C helper链：现有 C2 submission/model glue tests多数mock gate；E1应复用 accepted claim fixture 构造真实 C2 pair，不mockqualificationgate，改变helper后旧workbook/正文/PASS不得互相掩盖失败。C final PASS可仍current（paper未变），但B资格必须failed并阻断提交，不强求错误的“所有C一律stale”。
2. 真实title-only差分：active正文变化应旧paper receipt stale；相关主张/文本待审，而原数值/workbook/model approval保持。禁止测试为了通过重签旧hash或人工批准。
3. 开关/缺库差分的量化证据：现有 route/disabled行为断言已经防读库，E1远端测量应记录实际wall time/读入量/context，以及各现有硬预算；不把CI整仓耗时当solver性能，不为测量在本机运行。
4. 兼容和Fault已有充分单模块行为fixture，E1可把其纳入专项并记录方法映射；不为“52项”再造52份镜像实现的测试。

未发现需要修改生产 C/D 协议的阻断缺陷；最终结论仍依赖 E1 精确 head 的专项/完整 GitHub 执行、静态独立复审与 main复验。
