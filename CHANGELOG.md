# Changelog

## Current release: 7.2.3

- Elevated substantive preprocessing into a paper evidence chain: data problem/necessity -> mathematical formula or deterministic mapping -> parameter basis -> method-matched validation -> before/after evidence -> MATLAB figure -> downstream model interface.
- Added writing-depth rules for deterministic structural fixes, statistical transforms, interpolation/imputation, filtering/resampling and outlier/deletion operations.
- Clarified that formal proofs are used only for genuine equivalence, conservation, monotonicity, error-bound or feasibility-preservation claims; empirical cleaning uses reproducible statistical/physical/masking/holdout validation instead of fabricated theorems.
- Expanded the project-level preprocessing workbook with `预处理方法证据`, `处理前后对比` and `绘图数据索引`, plus bottom-level before/after or validation data.
- Added `数据预处理/data_process.m`; it reads only `数据预处理结果.xlsx`, plots preprocessing necessity/effectiveness evidence, and may not redo cleaning, interpolation, filtering, resampling or learned imputation.
- Standardized preprocessing figure export stems as `data_process` or `data_process_<evidence>` while preserving the visible-window/no-auto-export default.
- Project-level preprocessing now has an exact three-file final layout (`数据预处理.py`, `数据预处理结果.xlsx`, `data_process.m`); the per-question exact five-file/two-Python layout is unchanged.
- Added returned-workbook and formal figure-delivery gates plus regression/static-lint coverage for the new preprocessing paper/figure evidence chain.

## Previous release: 7.2.2

- Generalized preprocessing judgment from the v7.2.1 evidence gate into a cross-competition framework driven by the **current problem statement, current attachments and current model requirements**, rather than seismic-specific practice or any fixed competition template.
- Added mandatory audit dimensions for completeness, consistency, validity, duplicate identity, sampling and coverage, measurement quality, model readiness, temporal causality/information leakage, and target/label integrity before deciding whether data can be used directly.
- Added a dedicated missing-data policy. Missing values no longer imply interpolation: the workflow must distinguish isolated/continuous/boundary/group missingness, variable semantics and model-native missing-data support before choosing to keep missing values, delete rows, interpolate, use statistical imputation, model-based imputation or predictive imputation.
- Restricted interpolation to continuous variables with a defensible local-continuity mechanism and appropriate gap length/sampling structure; categorical variables, IDs, labels and event states cannot be mechanically interpolated.
- Added a predictive-imputation boundary: prediction may be used during preprocessing only to restore a genuinely missing model input, with independent masking/holdout validation and no future/target leakage. Forecasting or classification explicitly requested by the competition remains a core modeling task and cannot be hidden inside preprocessing.
- Added method-selection rules that prefer keeping raw data or model-native handling, then deterministic structural fixes, then simple mechanism-supported treatment, and only then validated statistical/model/predictive repair when simpler approaches are insufficient.
- Expanded the preprocessing operation gate to require independent validation evidence for data-changing operations and to route materially method-sensitive preprocessing choices into sensitivity/robustness analysis.
- Reframed seismic preprocessing as a domain-specific example only. Its DC removal, detrending, band-pass filtering, bad-trace repair, taper and interpolation rules must not be copied as defaults into unrelated competitions.
- Preserved the v7.2.1 three-state interface and output layout: `not_needed`, `question_local`, `project_level`; no new default user-visible files or directories were introduced.
- Added regression and static-lint coverage preventing future regressions to `shared data => forced preprocessing`, `missing => interpolation`, or `task prediction => preprocessing` behavior.

## Previous release: 7.2.1

- Replaced the v7.2.0 shared-data trigger with an explicit evidence-driven `preprocessing_decision`: `not_needed`, `question_local`, or `project_level`.
- Data quality audit is now mandatory for data projects, while data modification is conditional. Sharing the same raw attachment across questions is no longer sufficient to require cleaning, interpolation, filtering, standardization, or a unified preprocessing workbook.
- Added a strict operation-necessity gate for imputation, anomaly removal, interpolation, smoothing, filtering, detrending, normalization, standardization, resampling, bad-trace repair and related transformations. Operations must be supported by observed data issues or model requirements and must assess information-destruction risk.
- Made `data_preprocessing` a conditional workflow stage. `not_needed` and `question_local` projects skip the project-level preprocessing directory; only `project_level` creates `数据预处理/数据预处理.py` and `数据预处理/数据预处理结果.xlsx`.
- Added `preprocessing_decision`, preprocessing level, active data-source mode and conditional preprocessing execution state to the project-state contract; `data_preprocessing` is now a valid project phase.
- Updated solve, result-analysis and MATLAB evidence rules to inherit the active data source instead of always requiring `数据预处理结果.xlsx`.
- Extended code-delivery and returned-workbook validators to recognize the project-level preprocessing stage while refusing preprocessing artifacts when the decision is not `project_level`.
- Extended `resolve_workflow.py` with `--preprocessing-decision`; a `project_level` plan pauses at preprocessing until the unified workbook is accepted, while `not_needed` and `question_local` proceed directly to solve.
- Reworked seismic preprocessing guidance to audit first: DC removal, detrending, band-pass filtering, bad-trace repair, taper and interpolation are conditional operations rather than defaults. Default velocity smoothing, AGC, per-trace strong normalization, default band-pass filtering and default bad-trace interpolation are prohibited.
- Preserved read compatibility for v7.2.0 and earlier projects. Re-entering design/solve first establishes the new decision; legacy shared-data projects are not automatically migrated to `project_level`.

## Previous release: 7.2.0

- Added a project-level global preprocessing contract, `modules/03_data_preprocessing.md`, a unified `数据预处理/` directory, and a single `数据预处理结果.xlsx` handoff for shared-data projects.
- Added preprocessing artifacts to routing, manifest, output, code-quality and downstream data-source contracts.
- Added preprocessing-aware stale propagation and a user-execution pause before primary solving.
- This release treated shared raw data as a sufficient activation signal in several runtime contracts; v7.2.1 replaces that behavior with an explicit necessity decision.

## Previous release: 7.1.0

- Added a mandatory per-question Problem Contract that freezes original/derived objects, known/computable quantities, decision/state/output variables, explicit/implicit constraints, forbidden assumptions, data roles and typed cross-question dependencies before model design.
- Upgraded formula closure to a four-link semantic chain: problem statement and objects -> mathematical variables/formulas/objective/constraints -> Python variables/functions -> workbook outputs or validation evidence.
- Added `scripts/validate_semantic_governance.py` as a non-executing gate for Problem Contract status, semantic closure, Complexity Sanity Check, semantic revisions and current semantic hashes.
- Added `semantic_revision`, explicit semantic change categories and dependency-aware recursive stale propagation. Changes to problem interpretation, data scope, variables, parameters, assumptions, objectives, constraints, preprocessing, algorithm semantics or dependencies now invalidate the affected question and recursively dependent questions before new semantics are accepted.
- Added Complexity Sanity Check signals for unused conditions/attachments, unexplained dimensional collapse or decoupling, dynamic-to-static or multi-agent-to-independent collapse, inactive key constraints, downstream-copy behavior and implausibly easy computation. `review_required` blocks model/code delivery.
- Kept the v7.0 five-file per-question layout unchanged and added no new user-visible project report file; semantic governance results remain in chat/stdout, current semantics remain in `模型论文框架.md`, and machine revision/freshness state remains in `state/project_state.yaml`.
- Preserved read compatibility for v7.0.x projects without semantic-governance fields; projects migrate when they re-enter problem audit/model design.

### Repository maintenance

- Consolidated active release history into this `CHANGELOG.md`; root-level versioned release-note files are no longer part of the active Skill surface.
- Removed the superseded `CHANGELOG_V630.md`, `CHANGELOG_V632.md`, `CHANGELOG_V633.md` and `CHANGELOG_V634.md` root artifacts after their release history had already been summarized here and remained available through Git history.
- Repository lint and structure tests now reject any future root-level `CHANGELOG_V*.md`, preventing historical release notes from becoming accidental runtime or CI dependencies again.
- Kept the four V622 compatibility pointer documents because `core/bootstrap.yaml` still explicitly promises legacy document-pointer compatibility.

## Previous release: 7.0.1

- Preserved `primary_execution_status=accepted` when an accepted primary script is revalidated without a hash change, so the standard unscoped code-delivery gate can safely inspect both stage scripts.
- Bound returned-workbook acceptance to the actual path, exact standard filename, derived problem and derived stage before runtime evidence can mutate project state.
- Added regression coverage for unscoped two-script code delivery, workbook stage/problem/path spoofing rejection, and legacy result-directory read compatibility.
- Removed the stale `v6.6.0` release marker from `scripts/resolve_workflow.py`.

## Previous release: 7.0.0

- Restored two independent task-specific Python programs per question: `问题X求解.py` for primary solving and `问题X结果深化分析.py` for post-acceptance result analysis.
- The default question folder now contains exactly two Python scripts, two standard Excel workbooks and one `qX_plot.m`.
- Primary solve code freezes after the primary workbook is accepted; result analysis no longer overwrites or enlarges the primary script.
- Code delivery now enforces filename-to-stage consistency and records separate `primary_code_sha256` / `analysis_code_sha256` hashes and paths.
- Project synchronization hashes the primary script as the model layer and isolates analysis-code staleness, so changing only analysis code cannot invalidate an accepted primary result-quality status.
- Both Python scripts independently use the existing code-quality thresholds; the 500/700/900 line policy and function/parameter limits are unchanged.
- v6.6.x single-evolving-script projects remain readable as legacy compatibility inputs; new projects and new result-analysis work use the five-file layout.
- Removed the obsolete single-script overwrite rule and the dead sync logic for standalone run-config/instruction/report artifacts.

## Previous release: 6.6.1

- Added `core/code_quality_contract.yaml` as the single active authority for task-specific Python engineering quality.
- `validate_code_delivery.py` checks script/function/parameter size, static complexity and key anti-patterns without executing task code.
- Restored the 500-line target with a controlled complex-problem exemption up to 900 lines; functions target 80 lines and 8 parameters with hard limits at 120 lines and 12 parameters.
- Removed stale top-level `图表/` and standalone-config wording from active Skill entry documents.
- Replaced the deleted `hsk_check_artifact.py` workbook runtime reference with the current code-delivery and returned-workbook validators.
- Aligned the workbook MATLAB handoff with the current window-only default: exported figures and independent evidence files are not required by default.
- Slimmed active entry documents so detailed rules live in authoritative contracts instead of being duplicated.

## Previous release: 6.6.0

- Restored one self-contained `问题X求解/` directory per subproblem.
- New projects used one evolving Python script, two standard workbooks and one `qX_plot.m` in that directory; v7.0.0 supersedes this single-script rule.
- Removed standalone run-config, execution-instruction and validation-report files from the default user-visible output.
- Fixed cross-question Python hash contamination in project synchronization.
- Kept legacy `结果数据表/问题X/` layouts as read-only compatibility inputs.
- Corrected the nested plugin entry path and removed the stale LaTeX module version title.
- Kept the existing DOCX + review multi-intent ordering unchanged in this release.
- Hotfix: removed the obsolete standalone run-config and execution-instruction templates, the superseded MATLAB handoff writer, and the redundant artifact checker.
- Hotfix: aligned the global policy, Starter guides, code appendix, Figure Contract, MATLAB reader, optional manifest, review pack and active tests with the then-current four-file contract.
- Hotfix: default MATLAB delivery keeps only the visible figure window; exports belong to project-level `figures/` only after paper-stage confirmation.

## Previous release: 6.5.1

- Removed the obsolete fixed sensitivity/robustness checklist and the unreferenced pre-user-execution pipeline config.
- New-project starters stop after `run_primary_pipeline()`; `run_pipeline()` remains only as a user-local compatibility API.
- Local workbook generation records `workbook_received` and can no longer promote a subproblem to `solved` or `analyzed` before returned-workbook validation.
- Both standard workbooks require the `运行配置` evidence sheet; workbook schema version is 2.2.1.

## Previous release: 6.5.0

- Default execution ownership is user-managed full-fidelity: the assistant generates task-specific code but never runs solve or result-analysis programs.
- Added formal code-delivery and returned-workbook gates, execution states, full-run configuration, code/data hash checks, and the mandatory `运行配置` workbook evidence contract.
- Primary code delivery pauses at `awaiting_user_execution`; final result-analysis code is generated only after the returned primary workbook is accepted.
- Existing local pipelines remain runnable by the user; legacy projects without the new optional execution fields remain readable.

## Previous release: 6.4.1

- Active MATLAB and figure templates use `问题X结果深化分析.xlsx` instead of generating the historical `问题X敏感性与鲁棒性结果.xlsx` name.
- `result_manifest.yaml` records `result_analysis_workbook` as the current field.
- The code-appendix template names the primary-solve and result-analysis scripts separately.
- `AGENTS.md` matches the LaTeX-first workflow and treats DOCX as an explicit optional branch.
- Added regression coverage that prevents current-generation templates from reintroducing legacy workbook names and checks packaged/root Skill version alignment.

## Previous release: 6.4.0

### Quality-first primary solving

- Added an explicit primary-result quality gate before any sensitivity, robustness or multi-algorithm analysis.
- Split primary solving from result analysis in the module graph, state machine and workbook contract.
- Added adaptive result-analysis selection based on problem, model, data, result and reviewer risk instead of a fixed perturbation checklist.
- Added structured `passed` / `failed` / `redo_required` outcomes and stale propagation when result analysis invalidates the primary result.
- Switched the default full workflow to LaTeX-first authoring; DOCX is an explicit independent review branch.
- Replaced versioned active entry filenames with stable names and moved historical release documents into `legacy/`.

## Previous release: 6.3.4

- Added the `result_analysis` module and separated it from primary solving.
- Added current-state `模型论文框架.md` synchronization for model, result, analysis and figure changes.
- Added adaptive analysis categories, redo-required feedback and figure-evidence updates.
- Updated the three competition profiles, score rubric and submission checks.

## Previous release: 6.3.3

- Hardened formal delivery gates with exact-scope artifact requirements.
- Added conservative stale propagation and write-after-hash checks.
- Added state and framework preflight validation before synchronization.

## Previous release: 6.3.2

- Added current-state project synchronization and per-question artifact hashes.
- Added objective-specific workbook evidence and data-source hashing isolation.
- Added document, LaTeX and submission artifact validation.

## Previous release: 6.3.1

- Added three-axis task classification: objective, structures and capabilities.
- Added deterministic workflow resolution and multi-intent support.
- Added proposition planning and proof integration.

## Previous release: 6.3.0

- Introduced the modular workflow graph and project-state contract.
- Added output, workbook, figure and compile contracts.

## Previous releases

Use this file and Git history for release chronology; `legacy/README.md` documents compatibility-era material that is intentionally outside the active runtime.
