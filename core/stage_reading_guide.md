# Stage Reading Guide (generated navigation)

Generated from `core/workflow_router.yaml#reading_policy` and
`core/writing_runtime_contract.yaml#template_first_progressive_authoring.stages`.
This is a source and conditional pointer inventory, not source text,
a duplicate phase registry, proof of reading, an approval, or a gate result.
Resolve current project facts and use the selected commit of the original Authority.

## Common source selectors

- read_now: `core/bootstrap.yaml`
- read_now: `core/hsk_core_policy.md`
- read_now: `core/workflow_router.yaml`; selector=['reading_policy.boundaries']

## Routing profiles (selection belongs to the resolver)

### case_memory_retrieve

- read_now: `packs/artifact/case_memory_retrieval.md`
- read_now: `core/case_memory_retrieval_contract.yaml`

### framework_result_sync

- read_now: `modules/02_model_design.md`; selector=['## 8. 模型语义修订、审批失效与跨问传播', '## 10. `模型论文框架.md`']
- read_now: `core/writing_reasoning_contract.yaml`; selector=['schema_version', 'role', 'scope', 'rule_governance', 'analysis_evidence_disposition', 'paper_fragment_stale_governance', 'numeric_style_contract']

### figure_style

- read_now: `modules/04_figure_evidence.md`; selector=['## 正确顺序', '### 视觉修改与语义修改分流', '## C 类：各问结果图合同', '## Publication Rendering Grammar：成熟论文图实现层', '## 实表读取规则', '## 图题、配色与风格', '## 入文闭环']
- read_now: `templates/figure/result_figure_qa.md`

### figure_design

- read_now: `modules/04_figure_evidence.md`; selector=['## 正确顺序', '## C 类：各问结果图合同', '## Figure Evidence 层级', '## Scientific Figure Synthesis Gate：从证据结构设计 Figure', '## Basic-form Challenge：检查当前表达是否遗漏必要证据', '## Composite Encoding Preference：按真实信息增益选择互补编码', '## Scientific Rendering Profiles：选定视觉结构后的专属科研表达', '## Figure Layout Gate：单图 / 1×2 / 2×2 动态判断', '## Figure Enhancement Gate：焦点—上下文信息增强', '## Publication Rendering Grammar：成熟论文图实现层', '## 视觉注意力预算', '## 实表读取规则', '## 图题、配色与风格', '## Figure Portfolio Scientific Quality Gate', '## Missing Scientific Evidence Check', '## 分析图准入', '## 入文闭环']
- read_now: `templates/figure/result_figure_contract.md`
- read_now: `templates/figure/result_figure_qa.md`
- conditional: `templates/figure/chart_selection.md`; when=candidate_visual_structure_is_being_selected
- conditional: `templates/figure/figure_enhancement_patterns.md`; when=selected_enhancement_requires_an_implementation_pattern
- conditional: `modules/04_figure_evidence.md`; selector=['## B 类：项目级预处理证据图']; when=project_level_preprocessing_figure_is_in_scope

### mechanism

- read_now: `modules/04_figure_evidence.md`; selector=['## 正确顺序', '## A 类：机理与推导图', '## 入文闭环']
- read_now: `templates/figure/mechanism_contract.md`
- read_now: `templates/figure/mechanism_qa.md`
- conditional: `templates/figure/mechanism_drawio_spec.yaml`; when=drawio_backend_selected
- conditional: `templates/figure/mechanism_drawio_patterns.md`; when=drawio_source_is_being_generated_or_repaired

### project_sync

- read_now: `scripts/README.md`; selector=['## 运行时入口与治理']
- read_now: `core/output_contract.yaml`; selector=['scope_boundary', 'project_sync']
- read_now: `core/user_execution_contract.yaml`; selector=['solver_backends']

### returned_workbook_validation

- read_now: `scripts/README.md`; selector=['## 代码与用户执行']
- read_now: `core/user_execution_contract.yaml`; selector=['solver_backends', 'assistant_policy', 'returned_workbook']
- read_now: `core/numerical_verification_contract.yaml`

## CUMCM writing stages (order belongs to writing runtime)

### template_inspection

- read_now: `templates/latex/cumcm/hsk/template_manifest.yaml`
- read_now: `templates/latex/cumcm/hsk/hsk_main.tex`
- read_now: `current_model_paper_framework#当前写作选择`
- read_now: `current_model_paper_framework#Chapter-Handoff-Map when available`

### problem_restatement

- read_now: `modules/05_writing/paper_writing_protocol.md#6.1-问题重述`
- read_now: `current_problem_contract`
- read_now: `original_problem_text`

### problem_analysis

- read_now: `modules/05_writing/paper_writing_protocol.md#6.2-问题分析`
- read_now: `current_problem_contract`
- read_now: `current_classification_and_cross_question_dependencies`

### assumptions_symbols_and_preparation

- read_now: `modules/05_writing/paper_writing_protocol.md#6.3-模型假设与符号说明`
- read_now: `modules/05_writing/paper_writing_protocol.md#6.4-数据说明与必要预处理`
- read_now: `modules/05_writing/paper_writing_protocol.md#6.5-共享基础与模型准备`
- read_now: `current_model_paper_framework#预处理判定与共享关系`

### question_model_solution_result_validation

- preflight: `current_question_evidence_bundle`
- preflight: `current_model_paper_framework#逐问写作能力预检`
- preflight: `modules/05_writing/paper_writing_protocol.md#13.0-CUMCM-图表的正文落点先论证职责后图型`
- read_now: `modules/05_writing/paper_writing_protocol.md#1-写作输入`
- read_now: `modules/05_writing/paper_writing_protocol.md#3-每问的四个功能槽`
- read_now: `modules/05_writing/paper_writing_protocol.md#4-Local-Narrative-Chain`
- read_now: `modules/05_writing/paper_writing_protocol.md#5-Paragraph-Handoff-Test`
- read_now: `modules/05_writing/paper_writing_protocol.md#7-模型建立`
- read_now: `modules/05_writing/paper_writing_protocol.md#7.3-作者视角与建模解释`
- read_now: `modules/05_writing/paper_writing_protocol.md#8-模型求解`
- read_now: `modules/05_writing/paper_writing_protocol.md#9-求解结果数值与术语`
- read_now: `modules/05_writing/paper_writing_protocol.md#10-结果与验证的分层`
- read_now: `modules/05_writing/paper_writing_protocol.md#11-Result-Validation-Bridge`
- read_now: `modules/05_writing/paper_writing_protocol.md#12-跨问递进`
- read_now: `modules/05_writing/paper_writing_protocol.md#13-图结果叙事`
- read_now: `current_question_model_formula_algorithm_result_and_figure_evidence`
- conditional branch: `proposition_or_proof`; when=当前问 preflight 的 derived proposition_proof state 为 planned/current，或 candidate/stale/missing/review_required 需要语义裁决， 或用户明确要求创建/修改/审查命题、引理、推论、等价性/可行性/单调性证明或误差界；显式请求不得覆盖 stale/missing 冲突。
- conditional source: `core/writing_reasoning_contract.yaml`
- conditional source: `packs/artifact/proposition_proof.md`
- conditional branch: `stepwise_or_pseudocode`; when=当前问 preflight 已裁决 Algorithm Trace presentation_mode 为 stepwise 或 pseudocode，而不是 not_needed； mode 来自项目状态即可触发，不要求用户 prompt 再出现“伪代码/算法流程”。
- conditional source: `core/writing_reasoning_contract.yaml`
- conditional source: `packs/artifact/algorithm_flow.md`
- conditional source: `modules/05_writing/latex.md#5-图表命题和算法环境`
- conditional branch: `complex_semantic_dispute`; when=Model/Solver/Validator、优化语义、跨问依赖、术语数值、Model Construction Rationale、Reduction Provenance、solver precondition、Preflight 缺失状态或 Claim Strength 存在争议。
- conditional source: `core/writing_reasoning_contract.yaml`
- conditional branch: `reasoning_example`; when=当前段落需要改写示范，或难以区分有效建模解释与空泛铺垫；只读取相关案例，不作为开篇预读。
- conditional source: `modules/05_writing/references/model_solution_reasoning_examples.md`
- conditional branch: `model_construction_solution_example`; when=当前段落难以说明为什么建立该模型、为什么结构化简成立、solver 前提/适用性、关键数值参数依据，或小节标题拆分/压缩存在争议；只读取相关案例。
- conditional source: `modules/05_writing/references/model_construction_solution_rationale_examples.md`

### evaluation_references_conclusion_appendix

- read_now: `modules/05_writing/paper_writing_protocol.md#15-模型评价逐问结论与附录`
- read_now: `modules/05_writing/paper_writing_protocol.md#16-引用与正文语言`
- read_now: `current_citation_evidence_and_final_question_answers`

### abstract_title_and_keywords

- read_now: `modules/05_writing/paper_writing_protocol.md#2-模板与写作职责`
- read_now: `modules/05_writing/paper_writing_protocol.md#14-摘要`
- read_now: `current_final_question_answers_and_validation_boundaries`

### draft_semantic_review

- read_now: `core/writing_reasoning_contract.yaml`
- read_now: `modules/05_writing/paper_writing_protocol.md#5-Paragraph-Handoff-Test`
- read_now: `modules/05_writing/paper_writing_protocol.md#7.3-作者视角与建模解释`
- read_now: `modules/06_review_delivery.md#三-公式模型角色算法命题与数值证据审查`
- read_now: `modules/05_writing/paper_writing_protocol.md#5A-Cross-File-Chapter-Handoff`
- read_now: `current_model_paper_framework#Chapter-Handoff-Map`
- read_now: `modules/06_review_delivery.md#Cross-File-Assembled-Seam-Sweep`
- read_now: `modules/06_review_delivery.md#五-Title-Claim-正文结构与-Paragraph-Necessity`
- read_now: `modules/06_review_delivery.md#v7.20-v8.0.1-章节能力保全检查`

### ai_cleanup

- read_now: `modules/05_writing/ai_cleanup.md`
- read_now: `modules/05_writing/paper_writing_protocol.md#5-Paragraph-Handoff-Test`
- read_now: `modules/05_writing/paper_writing_protocol.md#7.3-作者视角与建模解释`
- read_now: `resolved_draft_review_findings`

### latex_assembly_audit_and_compile

- read_now: `modules/05_writing/latex.md`
- read_now: `modules/05_latex_compile_quality.md`
- read_now: `packs/artifact/latex.md`

### final_review_and_delivery

- read_now: `core/writing_reasoning_contract.yaml`
- read_now: `modules/06_review_delivery.md`
- read_now: `templates/review/final_review_matrix.yaml`
- read_now: `current_latex_audit_and_compile_reports`
