# Changelog

## Current release: 7.4.5

- Removed the ambiguous active proof-contract fields `proposition_proof_segmented_steps`, `segmented_steps_required` and `main_text_key_steps_*`. Proposition proof governance now has one machine-readable meaning: `paragraph_first` by default, distinguishable logical units required, and 2--6 numbered steps only when the proof genuinely has multiple independent stages.
- Added `scripts/audit_paper_prose.py`, a non-destructive final-LaTeX prose/structure audit. It reports `pass`, `warning` or `review_required` and never rewrites paper text.
- Prose warnings cover repeated/high-density negation or contrast, repeated `本文/本问/该模型` paragraph starts, repeated `本文不是……而是……` / `不能……只能……` structures, and overused stock phrases such as `由图可知` or `见表`. A single legitimate `但/然而/不是` is not an error.
- Structural `review_required` checks cover default standalone `结论` sections, visible H1/A1 assumption IDs, merged assumptions/symbols, missing `问题提出`, formulas inside `问题分析`, and missing per-question `核心模型汇总`; unreferenced main-text figure/table labels are warnings for evidence review rather than automatic hard failures.
- The audit is report-only by default. Before final compilation, `python scripts/audit_paper_prose.py final_latex/main.tex --strict` blocks only unresolved `review_required` findings; warnings remain for human judgment.
- Preserved the v7.4.4 paper structure and the two-level model-evaluation strategy: default `模型的评价与推广`, or `模型的改进、评价与推广` when substantive improvement content exists.
- Numerical models, preprocessing, workbook schema, user-execution ownership, MATLAB Figure Evidence and per-question five-file interfaces are unchanged.

## Previous release: 7.4.4

- Reworked Chinese competition problem restatement into the default `问题背景 + 问题提出` structure. `问题提出` now restates each subproblem as `问题一：… / 问题二：…`, using the authors' own understanding of research object, key conditions and required output while excluding formal models, equations, algorithms and final results.
- Added an affirmative-flow writing rule. Prose should directly state the object, mathematical treatment and result; high densities of `但/然而/不是/不能/只能/而不是` now trigger a real-conflict review instead of being treated as signs of rigor. The novice-academic style remains plain and earnest but must not become repetitive self-negation, self-defense or disclaimer-heavy writing.
- Changed proposition proof presentation from uniformly segmented numbered chains to **paragraph-first, numbered-when-needed**. Continuous 3--8 line proofs use natural paragraphs and equations; 2--6 numbered steps are reserved for genuinely multi-stage arguments such as case analysis, existence/uniqueness or mapping-feasibility-objective proofs.
- Standardized proposition display numbering to Arabic section/proposition form such as `命题 4.1` and `命题 6.2`; mixed forms such as `命题 六.1` are rejected.
- Strengthened figure/table evidence closure: every core body figure and table requires an explicit nearby numbered reference plus interpretation of trend/key value and model/question meaning. Caption-only evidence is no longer sufficient, while the wording of figure/table references must still vary naturally rather than forming a new `由图可知/见表可知` phrase template.
- Made `求解结果` the default per-question result subsection. Question-specific deep evidence follows under task-specific headings, and the final result/deep-analysis paragraph answers the current subproblem naturally. Fixed `小问结论` subsections are no longer part of the default skeleton.
- Removed the standalone Chinese CUMCM `结论` chapter from the default paper skeleton. A separate conclusion is now added only when the current competition template, user or paper type explicitly requires it; this does not affect the internal project-memory heading used for cross-question synthesis.
- Updated the CUMCM HSK template, DOCX rules/checklist, LaTeX artifact pack, final-review module, caption contract and model-paper framework memory so they implement the same authority rather than reintroducing older structures later in the workflow.
- Audited active read paths and found the current Diangong template still carried a v6.2.2-era skeleton (`问题要求`, merged assumptions/symbols, fixed validation/sensitivity chapters and standalone conclusion). That active template was modernized to v7.4.4. Legacy archives and V622 compatibility pointers remain intentionally read-only and are not deleted merely because they contain historical wording.
- Hardened lint/regression coverage so active CUMCM/Diangong templates cannot silently restore `问题要求`, merged assumption/symbol chapters, default standalone conclusions, stale v6 template markers, non-Arabic proposition numbering, or the old proof-listification behavior. Numerical, preprocessing, workbook, user-execution, MATLAB Figure Evidence and per-question five-file interfaces remain unchanged.

## Previous release: 7.4.3

- Reworked the CUMCM writing authority around actual reviewer reading order: problem background is normally one paragraph, problem analysis is organized question-by-question and excludes formal equations/final results, model assumptions and symbol definitions are separate top-level sections, and each question enters through “问题X模型建立及求解”.
- Added a mandatory `核心模型汇总` between detailed derivation and numerical solving so the final variables, objective/equations, constraints and boundaries can be recovered without rereading the full derivation.
- Strengthened notation readability: visible assumptions use natural numbering instead of H1/A1 contract labels; high-frequency symbols avoid long text/multi-level subscripts and use short superscripts for model/scenario/stage information where appropriate.
- Reworked proposition presentation: B-level proofs use 2--6 segmented/numbered logical steps; standard proposition boxes are non-breaking, and overlong technical proofs move to the appendix instead of shrinking fonts or splitting across pages.
- Replaced the default “模型评价与适用范围” pattern with “模型的评价与推广” or, when real improvement content exists, “模型的改进、评价与推广”. Strengths must outnumber weaknesses, strengths are capped at four, and improvement/promotion sections are evidence-driven optional content rather than fixed quotas.
- Enforced strict “表上图下”: table captions are above, figure captions below, tables/figures are centered, and three-line table numeric/short-text cells are centered by default.
- Extended AI cleanup from phrase deletion to sentence-structure de-templating: repeated “本文……因此……”, “不是……而是……”, repeated paragraph-start subjects, abstract-jargon stacking and identical result-paragraph rhythms are now explicit rewrite triggers.
- Added a final “科研初学者式学术表达” pass: prose stays formal and technically stable but intentionally a little plainer and less over-polished, preserving visible reasoning steps without manufacturing grammatical errors, colloquialism or mechanical synonym replacement.
- Updated the CUMCM HSK LaTeX template and DOCX/check templates to implement these rules instead of leaving them only in documentation; removed fixed top-level model-validation/sensitivity placeholders from the default paper skeleton.
- Added v7.4.3 regression coverage for question-analysis structure, separate assumptions/symbols, core-model summaries, segmented/non-breaking propositions, caption positions and anti-template language. Numerical, preprocessing, workbook, MATLAB, user-execution and five-file interfaces remain unchanged.

## Previous release: 7.4.2

- Added a Figure Evidence hierarchy (`L1` main result, `L2` mechanism/heterogeneity, `L3` robustness, `L4` numerical-validity evidence) so unlike evidence layers are not automatically packed into one dense multi-panel figure.
- Added a dynamic Figure Layout Gate. MATLAB planning now asks whether a single panel already closes the primary question, then considers paired `1×2/2×1`, inseparable `1×3`, and only conditionally retains `2×2`; otherwise evidence is split by Primary question / Evidence level.
- Defined explicit `2×2` retention criteria: one core conclusion, clear paired/cross structure, limited visual encodings, real same-screen comparison value, indispensable panels and a single coherent caption duty. `2×2` is neither the default nor mechanically forbidden.
- Added a visual-attention budget: one first-level conclusion per Figure by default, usually no more than 2--3 primary comparison objects, no more than two main visual encodings, and clear de-emphasis of auxiliary evidence.
- Replaced the old low-saturation-dark default with a competition-oriented high-contrast policy. Primary objects may use medium/high saturation colors such as bright blue `#1478FF`, vivid red `#F04444`, bright green `#16B364`, orange `#F79009` and purple `#7A5AF8`; confidence bands, backgrounds and secondary references remain muted or transparent.
- Kept color semantics stable across the paper and prohibited rainbow/unordered color cycling and color-only red/green encoding. Continuous fields still use physically meaningful continuous/diverging colormaps rather than categorical bright colors.
- Updated Figure Contract fields with Evidence level, Primary question, Layout decision, Split decision and Panel necessity; aligned project-level preprocessing figures with the same authority instead of retaining a conflicting low-saturation style.
- Added v7.4.2 regression coverage to prevent future reintroduction of a fixed panel layout or the old low-saturation default. No Problem Contract, preprocessing-decision API, numerical model, workbook schema, user-execution boundary, five-file layout or LaTeX writing interface changed.

## Previous release: 7.4.1

- Audited every active Module 01--06 stage plus bootstrap, router, manifest, contracts, templates and compatibility boundaries for read/load closure.
- Fixed the active `core/hsk_core_policy.md` header that still advertised v7.2.6, and extended release-marker linting so current authoritative Markdown cannot silently lag the Skill version again.
- Fixed `core/task_taxonomy.yaml` declaring `<7.0.0` compatibility even though the active Skill is v7; the taxonomy now explicitly supports the v7 line.
- Removed the stale fixed `3--5` assumption quota from Module 02 and aligned model design with the writing authority: assumptions are impact-based, checkable and localized by cross-question or question-local scope.
- Kept the four V622 filenames as backward-compatible pointers but removed them from the active Skill index, active MANIFEST and active-required-file set, so historical pointer names cannot be mistaken for current runtime modules.
- Made the CUMCM HSK template add-on README versionless so a stable active template entry does not carry an obsolete Skill-era version label.
- Hardened `lint_skill.py` with compatibility-pointer isolation, taxonomy compatibility checks, repository-relative path validation, Markdown local-link checks and all-route resolver smoke checks.
- Added v7.4.1 regression coverage for active/compatibility separation and resolver path existence. No Problem Contract, preprocessing, numerical, workbook, MATLAB, five-file or writing-evidence interface changed.

## Previous release: 7.4.0

- Reviewed all 16 user-supplied 2024 CUMCM showcase papers (A016, A053, A163, A178, A242, B159, B195, B196, C038, C063, C094, C234, D033, E010, E061, E218; 807 pages) and extracted cross-paper evidence-architecture rules rather than copying phrases or treating every showcase-paper convention as exemplary.
- Added title/abstract discipline: implementation software, script names, workbooks and parameter dumps cannot substitute for research object, modeling mechanism, decisive values and direct conclusions.
- Added task-specific object-restoration figures to the front-matter contract when complex geometry, topology, spatial relations or production structure cannot be recovered efficiently from prose; decorative/general workflow figures remain rejected.
- Localized assumptions by scope: only cross-question assumptions belong in the global assumption section, question-local assumptions stay near first use, and a standalone assumption chapter is optional when no substantive shared assumptions exist.
- Added placement criteria for problem analysis: shared mechanisms go to a global analysis, local difficulties stay inside the question, and hybrid problems use a short global map plus local additions.
- Added local evidence closure so derivation, solution, key result and its matching error/validation evidence are kept close when possible; only cross-question synthesis is deferred to a global analysis section.
- Separated model validation from model evaluation. Quantitative credibility evidence (error, residual, feasibility, optimality gap, external validation, calibration, sensitivity, confidence interval, convergence or physical checks as appropriate) cannot be replaced by generic strengths/weaknesses. A standalone evaluation chapter remains optional.
- Added a minimal algorithm-explanation budget: generic algorithm background is compressed to citation-level context while problem-specific encoding/state, objective, constraints, parameters, stopping and validation remain explicit.
- Allowed local short properties/proofs to remain embedded in derivations without being forced into formal proposition boxes; formal proposition admission remains governed by the proposition-proof authority.
- Updated `模型论文框架.md` to remember title/abstract strategy, object-restoration figures, assumption scope, local evidence closure, validation placement and algorithm explanation budget; removed the old fixed three-assumption placeholder.
- Preserved all v7.3.0 numerical, preprocessing, workbook, MATLAB, LaTeX-first and five-file interfaces; no new required user-visible artifacts were introduced.

## Previous release: 7.3.0

- Added a shared evidence-driven **paper expression and section-organization protocol** for DOCX, LaTeX and AI cleanup, derived from cross-paper review of 2025 mathematical-modeling showcase papers rather than fixed phrase imitation.
- Reframed problem restatement as a compact recovery of research object, modeling-relevant conditions and per-question inputs/outputs; direct prompt copying, premature model naming and premature result reporting are rejected.
- Reframed problem analysis around the actual modeling difficulty, object/mechanism, cross-question dependency and model-selection rationale instead of generic “preprocess -> model -> solve -> plot” workflow prose.
- Made model assumptions impact-based rather than quota-based: facts and conventions are separated from assumptions, and retained assumptions must affect model structure, approximation, distribution or validity boundaries and be defensible/checkable.
- Added anti-textbook derivation rules: start from problem-specific objects and mechanisms, connect every core equation to its modeling role, and avoid generic model history or algorithm encyclopedias unless needed for the current derivation.
- Added a result-writing evidence chain: key value/phenomenon -> comparison or threshold -> mechanism -> direct answer -> validity/failure boundary; result paragraphs must distinguish description, explanation and question answering and must preserve inconvenient anomalies or local instability.
- Replaced generic “three strengths, two weaknesses, one promotion” evaluation with model-specific mechanism closure, validation evidence, computational structure, interpretability, explicit limitation consequences and concrete extension conditions.
- Added adaptive sectioning patterns for physical/mechanistic, statistical/regression, machine-learning, optimization/network, dynamic/simulation and mixed multi-question problems; shared foundations are defined once and downstream questions emphasize only new variables, objectives, constraints and evidence.
- Strengthened AI cleanup with prompt-copy, pipeline-listing, universal-assumption, textbook-derivation, software-as-algorithm, result-reporting and generic-evaluation checks plus a cross-topic replacement test for detecting reusable template paragraphs.
- Preserved the v7.2.x three-state preprocessing API, full-fidelity execution ownership, two-Python/five-file per-question interface, MATLAB ownership and LaTeX-first workflow; this is a backward-compatible writing-capability release with no new required user-visible artifacts.
- Added v7.3.0 regression coverage locking the shared writing authority and version consistency.

## Previous release: 7.2.6

- Repositioned project-root `模型论文框架.md` as assistant-readable project memory in addition to a user-visible modeling/paper artifact, so current semantics can be recovered across long contexts and new chats without reconstructing the model from conversation history.
- Added a router-level `project_memory_contract` with targeted reads for ordinary single-question continuation and full reads for cross-chat recovery, full-paper writing, cross-question synthesis and final review.
- Added explicit read-before-use rules to project-level preprocessing, primary solving, result analysis, Figure Evidence and LaTeX writing; downstream stages must consult the current framework before acting when it exists.
- Kept source-of-truth boundaries strict: accepted workbooks remain the numerical fact source and project state remains the semantic-revision/hash/stale source; framework summaries are context, navigation and writing memory rather than a replacement database.
- Added write-after-change synchronization requirements for semantic changes, accepted primary/results-analysis outputs and locked figure evidence, while continuing to keep only the current framework version and using Git for history.
- Removed the remaining active legacy `结果数据表/问题一/q1_plot.m` path from the framework template and renamed its generic sensitivity/robustness evidence row to the current result-analysis workbook terminology.
- Added regression coverage for the framework project-memory contract without changing the existing three-state preprocessing API or per-question five-file interface.

## Previous release: 7.2.5

- Normalized `accepted_preprocessing_workbook` to the canonical `preprocessing_workbook` artifact before resolver dependency reporting, eliminating false missing-prerequisite warnings after an accepted project-level preprocessing workbook.
- Added `state.preprocessing.covered_raw_sources` so project-level preprocessing explicitly records only the raw sources replaced by the unified workbook; independent auxiliary attachments remain readable when they are not covered.
- Hardened `validate_code_delivery.py` so project-level primary/analysis code must retain the accepted preprocessing data hash, primary code must declare the unified workbook in `data_paths`, and covered raw sources cannot be reintroduced through `data_paths` or literal data-reader calls.
- Hardened `data_process.m` runtime checks by stripping inline MATLAB comments and blocking dynamic dispatch (`eval`, `evalin`, `feval`, `str2func`, `builtin`) plus forbidden preprocessing function handles.
- Clarified across Skill/module contracts that `data_process.m` belongs to the project-level preprocessing evidence directory but is generated only in the later Figure Evidence stage after primary solve and result analysis.

## Previous release: 7.2.4

- Hardened `data_process.m` delivery with a contract-backed runtime forbidden-call set covering interpolation, missing/outlier repair, smoothing, resampling/alignment, detrending/normalization, filtering/filter design, fitting and prediction calls.
- `scripts/sync_project.py` now scans executable MATLAB lines at figures-and-later delivery scopes and reports the exact forbidden functions detected; full-line comments are ignored to avoid documentation false positives.
- Aligned `modules/04_figure_evidence.md` with the authoritative router: project-level preprocessing workbook acceptance precedes solving, while `data_process.m` is created only after primary solving and result analysis when Figure Evidence begins.
- Added regression/static-lint coverage that locks the contract/runtime forbidden-function set and the Figure Evidence stage order without changing the three-state preprocessing decision or per-question five-file interface.

## Previous release: 7.2.3

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
