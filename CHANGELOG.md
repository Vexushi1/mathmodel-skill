# Changelog

## 10.9.0

- Add optional Figure `source_bindings` (State Schema 8.8.0, B2 contract 1.4.0) for read-only source and current approved-bundle observation. An explicitly bound workbook-driven result Figure can report exact B1 source ID, sheet and literal header agreement, plus whether the existing validated script/figure bundle matches current bytes and every discovered path in this scoped bundle belongs to the original `approved_figures` list.
- Preserve the three existing B2 policy pairs and B2b3a-only Figure rows: missing source bindings remain `not_assessed`. The audit does not rerun a model or plotting script, renew approval, certify image/caption semantics, or add a formal Figure gate. B2 remains in progress.
- Bound one audit by unique accepted-workbook bytes (B1's 64 MiB total), image bytes (256 MiB) and script bytes (16 MiB). Repeated Figure sources may reuse captured hashes, workbook readers and scoped discovery; final project/Skill read-set and discovery checks still run.

## Previous release: 10.8.0

- Add optional B2 Figure identity bindings (State Schema 8.7.0, B2 contract 1.3.0) for workbook-driven result figures. The read-only audit checks the current Figure ID across the Framework registry, claim fragment, approved image path and literal active modular LaTeX label, caption, image and body reference.
- Keep the existing `observe`, `propagate` and `enforce_latex_text` policy pairs unchanged. Figure identity observations do not qualify workbook or plotting-script content, establish visual/caption semantics, change project state or enter a formal LaTeX/submission gate. B2 remains in progress.

## Previous release: 10.7.0

- Add an explicit B2 `enforce_latex_text` policy (protocol 1.2.0) for machine-checkable claim consumption in active modular LaTeX text at formal audit, compile, project sync, and package validation boundaries. The gate checks live B1 qualification and current declared fragments; human semantic review remains separate.
- Retain claim-local stale propagation when an opted-in project advances from `propagate` to `enforce_latex_text`. Existing projects and the `observe`/`propagate` modes keep their prior gate behavior.
- Figure/caption evidence chains, DOCX, single-file or dynamic TeX, and full-paper semantic coverage remain outside this slice. B2 stays in progress.

## Previous release: 10.6.0

- Add an explicit B2 `propagate` policy (protocol 1.1.0) for claim-ID-based local paper-fragment stale propagation through the existing project sync transaction. The original `observe` 1.0.0 audit stays read-only; projects without the policy keep their prior behavior.
- Keep State and the Framework fragment table synchronized when the opt-in writer marks fragments stale. Preserve the existing artifact-level stale rules, accepted-workbook qualification, human model approval, and project generation/read-set checks.
- This slice does not introduce a formal writing, figure or submission gate and does not establish semantic support. B2 remains in progress pending cross-format and figure-chain integration.

## Previous release: 10.5.0

- Add an explicit read-only B2 `claim_consumption_audit` route for declared claim-to-fragment and active LaTeX observations. The route keeps original B1 source qualification and does not grant semantic support, write project state, or alter ordinary delivery gates.
- Extend optional Project State Schema to 8.4.0 for the B2 observe policy while retaining `paper_fragments[].depends_on` as the consumption edge. B1 Claim Evidence 1.0.0, A2 binding, numerical acceptance and approval protocols remain distinct; projects without the policy retain their routes.

## Previous release: 10.4.0

- Add opt-in B1 `claim_evidence_audit`: original accepted-workbook qualification, bounded OOXML selectors, finite Decimal derivations and declared assertion checks, with independent source/selection/arithmetic/semantic-support statuses.
- Keep `paper_framework.claim_evidence` optional in State Schema8.3.0; no new mandatory gate or user-project writer. Unknown/partial records, ambiguous coordinates, formula caches, cross-scope comparisons, duplicate origins, invalid units and resource overruns are not silently accepted.
- Preserve A2 full checker fingerprints. Read-only guidance requires explicit original delivery/receipt revalidation and re-adjudication of the analysis necessity gate when invalidated; never re-sign old evidence or claim a new numerical run.
- Use genuine synthetic old-A2 workbooks for cross-version regression; preserve original approval, numerical/PQS/receipt, transaction and Python/MATLAB policies. B2/C/D and new Release/tag creation remain outside this change.

## Previous release: 10.3.0

- A2 adds an explicit per-question/stage opt-in policy for consuming A1 structural conformance at existing code-delivery, receipt, runtime and sync boundaries. A1-only declarations and projects without A2 policy/bindings keep their previous workflow.
- Existing coordinators record structural delivery and successful-original-receipt acceptance bindings; declaration, model, helper, source or checker-Authority drift cannot silently re-sign old evidence. Current model approval and numerical/PQS checks remain separate and mandatory.
- Guarded writes include the captured state/framework/source/input/auxiliary/primary-workbook read set and a staged Skill-source recheck. Pending journals require explicit existing recovery; no replacement transaction engine or universal atomic-snapshot claim.
- State Schema 8.2.0 adds optional policy/binding fields. Conformance 1.1.0, User Execution 3.2.0, Runtime Assurance 2.2.0 and State Transition 1.4.0 maintain separate protocol versions. SIB, source bundle and RUN_RECEIPT 1.0/1.1/1.2 remain unchanged.
- Retain stale bindings through existing typed invalidation without revoking mathematical approval for ordinary code changes. Unknown/partial/orphan A2 records fail closed; structure verification never proves mathematical equivalence or independent review.
- Scope ends at A2. Claim-Evidence Graph, independent reviewer receipts and Case Memory are not implemented by this change; no user project is migrated and no release/tag is automatically created.

## Previous release: 10.2.0

- Adds opt-in A1 model/code structural conformance: current approved SIB selectors, selected primary/analysis source bundles, bounded symbol anchors, lexical reverse candidates and optional syntax-only expression checks. No task execution or mathematical-equivalence claim.
- Adds optional Project State Schema 8.1.0 declaration records and a dedicated read-only audit route; existing runtime gates, source receipts, numerical acceptance and ordinary workflow behavior are unchanged when the extension is not requested.
- Keeps A2 integration and Claim-Evidence/Reviewer Receipt/Case Memory stages separate. Implementation and verification scope are recorded in `docs/modeling_intelligence_a0_decisions.md`; this heading alone does not mean a GitHub Release was published.

## Previous release: 10.1.0

- Rechecks actual stage inputs at current-result qualification and receipt boundaries without requiring a prior sync; matching stale state hashes cannot prove unchanged raw files.
- Adds optional receipt 1.2 for project-level preprocessing plus explicit independent auxiliary attachments. Base preprocessing identity remains unchanged; auxiliary paths and digest are bound by code, runtime receipts, synchronization and reproducibility inventory. Unextended 1.1 and preprocessing 1.0 retain their contracts; older readers reject 1.2 rather than ignoring new evidence.
- Rejects boolean, floating-point and string semantic revisions consistently in approval, semantic governance and runtime recovery.
- Makes omitted backend arguments neutral/auto in the assured numerical entry while keeping the explicit legacy resolver's old projection. One project-wide Python/MATLAB selection remains required; preprocessing and plotting roles are unchanged.
- Corrects prose-authority delegation in script navigation. Independent protocol versions remain distinct from the Skill release.
- Verification and remaining limitations are recorded in `docs/v1010_audit_closure_remediation_plan.md` and this PR; a version heading does not assert completed CI or publication.

## Previous release: 10.0.1

- Fixes real MATLAB publication preview on R2024b: ColorBar font size is already measured in points and does not expose `FontUnits`. The shared styling helper and both standalone plot/preprocessing fallbacks now set only supported ColorBar properties; ColorBar label typography remains unchanged.
- Retains the v10.0.0 project-wide solver backend, read-only legacy compatibility, and all independent state, workbook, and receipt protocol versions.

## Previous release: 10.0.0

- Makes one project-root Python or MATLAB numerical backend choice authoritative for all questions and activated numerical analysis. Per-question algorithms, source bundles, workbooks, and accepted evidence remain separate; project-level Python preprocessing and formal MATLAB plotting keep their independent roles.
- Adds read-only backend inspection, a guarded first-choice `select`, and explicitly confirmed `migrate` with whole-project impact review, original-byte archival, and recoverable transaction. Historical stage declarations remain diagnostic evidence, and migration does not confer numerical delivery or acceptance.
- Aligns current Project State, runtime, synchronization, delivery, and package checks with the root choice. Skill carriers are 10.0.0 while state schemas, contracts, workbooks, and run receipts retain their independent protocol versions.

## Previous release: 9.7.1

- Resolves solver backend and legacy artifact projection from the actual resumed stage, including analysis requests that must return to primary solving.
- Closes discoverable Python relative-import and MATLAB helper-reference gaps, and rejects direct incremental mutation of version 1.1 RUN_CONFIG. Unverifiable project function resolution cannot qualify as a proved source bundle.
- Aligns per-question input observation with delivered 1.1 inputs, collects declared inputs in reproducibility packages, and wires project-aware implementation-anchor validation into synchronization.
- Accepts equivalent SHA-256 casing in native MATLAB templates and normalizes returned-workbook path identity, including Windows 8.3 aliases, while rejecting out-of-project paths.
- Corrects active Python-only summaries, retired implementation-hash guidance and missing versioned analysis-primary binding declarations. Retains legacy Python/FULL/P5a/1.0 compatibility, existing model approval and numerical evidence gates. See [audit scope, repairs and verification](docs/v971_backend_contract_audit.md).

## Previous release: 9.7.0

- Adds per-question Python/MATLAB selection for primary solving and conditional analysis, with scoped runtime recovery, backend-specific templates, and neutral artifact roles. Existing model approval and numerical acceptance remain authoritative; project-level preprocessing remains Python.
- Adds shared stage resolution, literal MATLAB RUN_CONFIG parsing, native Code Analyzer delivery checks, and receipt 1.1 binding backend, original entry SHA and declared source bundle. Observed source drift cannot refresh delivered or validated identities and invalidates dependent results through the existing state engine.
- Adds self-contained MATLAB numerical fixtures, native Excel writing, input/source stability checks, and exact backend-aware reproducibility package requirements. Existing Python receipt 1.0, legacy filenames and omitted CLI argument behavior remain compatible. Figure, writing and delivery consumers use the same accepted evidence interface.
- Adds backend unit/integration regressions and a distinct native MATLAB solver CI job, including real mixed-language handoffs. MATLAB execution evidence is separate from Python/static tests and the existing optional figure-preview job. See [migration, scope and verification](docs/v970_solver_backends_migration.md).

## Previous release: 9.6.1

- A7 aligns copied Python workbook support with canonical required run-configuration and conditional/profile sheets, with isolated real XLSX I/O parity checks.
- Both skill entries now carry a concise discovery description and preserve legacy version/summary/triggers under metadata. Repository readers accept current metadata and historical top-level fields; root and packaged entries retain identical content and explicit resource-root resolution.
- Runtime reports explicit classification conflicts per supplied axis while preserving unspecified current axes. Registered competition aliases and equivalent structure sets do not create false conflicts. Two prose references now delegate to the existing Paper Writing Protocol; palette discovery copy follows per-figure choice.

## Previous release: 9.6.0

- A6 adds compile-report v4 actual-input evidence: literal conditional support files join the audited bundle, engines produce a recorder, and formal verification binds the recorder and observed project inputs. Partial or unexplained chapter assembly cannot claim a full current PDF.
- Historical v3 reports remain readable but require re-audit and recompile for new formal delivery. Installed TeX/font assets remain an explicit environment boundary; current bound log/recorder files are retained for verification and reproducibility packaging.
- Reference checks use the full assembled body including appendices. Headline claim checks compare declared evidence and claims within each question, preserving clear negative statements and using review for ambiguous wording.

## Previous release: 9.5.7

- A5 verifies reproducibility packages against independently derived current per-question, conditional-analysis and project-preprocessing file sets. Declared data directories expand to actual bounded members; a self-consistent manifest cannot hide a missing question or stage.
- Exact official allowlist paths are required by both collection and validation; optional wildcard zero matches retain compatibility. Official PDF-only rules stay separate from reproducibility requirements.
- Current v4 compile-report-bound log/recorder files can be retained, with exact hashes and source members checked; older reports do not gain a fictitious recorder. ZIP creation alone remains distinct from validated delivery.

## Previous release: 9.5.6

- A4 applies current snapshot transitions and local paper-fragment invalidation before formal delivery checks. Read-only and write modes assess the same candidate state, so a first detected change cannot reuse an earlier passed gate.
- Snapshot and reading-plan figure binding share exact framework/script/export discovery, including explicitly mapped project-root figures. Missing or ambiguous scoped evidence is diagnosed; discovery never writes validated hashes or approval. Independent unmapped global diagrams remain a documented coverage warning.

## Previous release: 9.5.5

- A3 uses one current-primary prerequisite check for runtime qualification, analysis code delivery and analysis receipts. New analysis requires an explicit reason and method plan after primary acceptance; not_required remains a valid final-state branch without an analysis workbook.
- Name-only aliases cannot override current invalid evidence. Primary/data changes reopen the Analysis Necessity Gate and invalidate dependent results; successful receipts close only their verified numerical stale layers and preserve downstream figure/framework invalidation.
- Analysis delivery cannot overwrite the primary data identity. Historical accepted analysis remains readable; new receipt acceptance follows current gate requirements. No user code, MATLAB or image QA is executed.

## Previous release: 9.5.4

- A2 closes strict boolean evidence acceptance: the declared quality relation must match the existing numerical contract, and a false primary boolean recheck cannot become accepted through a numerical comparison.
- Synthetic receipt tests cover read-only rejection, failed write state, unchanged workbook bytes, true positive evidence and non-primary historical failures. Numeric relations and legacy read-only behavior remain available; no user models are executed.

## Previous release: 9.5.3

- A0/A1 repairs native Windows state transactions: backup synchronization uses a writable descriptor and partial pre-journal staging cleans only its own temporary files. Generation checks, locks, journal recovery and companion-file order remain unchanged.
- Workbook receipt readers close their owned read-only workbook on success, early return and exception. Native Windows unit CI now covers file lifecycle; only the symbolic-link fixture may skip on the exact missing-privilege condition, while ordinary path escape checks always run.
- This patch implements AUD-01/AUD-14 of the repository audit plan. No model, numerical acceptance rule, project schema, MATLAB execution or visual QA changes.
- The new Windows runner exposed equivalent short/long temporary-root spellings. File discovery, package paths and combined fingerprints now canonicalize roots before comparison; test measurement normalizes both spellings without disabling path-escape checks.

## Previous release: 9.5.2

- F4 closes the accepted source / exact header / Figure ID / caption / paper-reference / framework handoff in existing figure documents. Planned export names no longer stand in for real exported or approved files.
- Static code checks, actual MATLAB execution, human appearance review and paper approval are recorded separately using existing fields and pending work. Python execution facts and existing stale/approval rules remain intact; no new schema, review form or image QA is introduced.
- MATLAB guidance now gives the short manual workflow from real fields and explicit styles to user-run adjustment and optional export. Existing headings, table structures and F3 technique navigation are preserved.

## Previous release: 9.5.1

- F3 adds six focused technique references within the existing Figure patterns, with original MATLAB snippets for exact-key pairing, gap-preserving real intervals and per-metric color limits. Each describes input evidence, adjustable parameters and misleading uses.
- Chart selection and MATLAB guidance link to the relevant sections on demand. No new mandatory files, default palette, synthetic evidence, automatic visual QA or MATLAB execution are introduced; existing template interfaces remain unchanged.

## Previous release: 9.5.0

- F2 separates basic typography/frame from per-figure color selection. Empty or omitted profile now returns an empty palette and never selects a candidate; existing explicitly named profiles and color aliases remain available. Callers that formerly read palette.primary from a no-profile call must choose a profile explicitly or provide RGB.
- Plotting entry parameters now collect RGB, typography, line/marker size, canvas, legend, grid/frame and limits. A single object uses one color and one legend item; point-only plots retain every point, while sparse markers on continuous lines preserve isolated finite observations across missing-value gaps.
- Shared and standalone style paths use the same rendering implementation and explicit overrides. Ordinary axes, yyaxis labels, polar axes and heatmap public properties are handled separately; style runs once before local overrides and does not repaint data or colormaps.
- Updated Figure Authority, output contract, consumers, checks and migration guidance together. The optional historical preview harness now requests its own white background; it remains skipped on PRs and was not executed. MATLAB validation is static only.

## Previous release: 9.4.4

- F1 makes figure selection evidence-first: a clear line, dot, bar or single panel can directly support a core conclusion. Existing F1/F2/F3 labels describe structure, not quality or mandatory escalation.
- Composite encodings require real complementary information and improved readability; repeated line/point data are one evidence source, and absent intervals or pairings must not be invented.
- Aligned Module 04, Figure Pack, chart/contract/QA guides, MATLAB entry comments, output summaries and exact-heading routing. Portfolio review checks coverage and repetition rather than quotas of chart types or complexity. MATLAB executable lines and palette policy remain unchanged in this stage.

## Previous release: 9.4.3

- P0-C makes real MATLAB preview an explicit manual option: workflow_dispatch must select run_matlab_preview=true; the default is false and ordinary pull requests skip the entire MATLAB job.
- Removed the preview-only changed-path gate so an explicit manual request is not silently skipped when the latest commit does not touch a style helper. Source snapshots, characterization, native static CI and historical preview evidence remain available.
- This patch validates configuration and source contracts only; no MATLAB dispatch, rendering, image check or user-project approval was performed.

## Previous release: 9.4.2

- Fixed P0-B MATLAB workbook handoff: analysis workbooks are required only when the current figure explicitly needs accepted 03B evidence; missing requested workbooks, sheets or fields remain errors, while solution-only figures do not require an unrelated analysis workbook.
- Aligned readers and figure/writing handoff templates with exact unique headers after whitespace normalization. Expected column positions are optional drift warnings rather than field identities; duplicate or missing requested headers remain errors.
- Removed silent invalid-value filtering and implicit x sorting from plotting entry templates so malformed values are distinguished from declared missing observations and row correspondence/order remain explicit.
- Kept Workbook Schema 2.3.1, actual Excel fields, accepted numerical data, model solving, palette selection and CI unchanged. Verification for this patch is static for MATLAB; it does not claim MATLAB execution, image review or completion of later figure-plan stages.

## Previous release: 9.4.1

- Fixed the P0-A MATLAB title handoff mismatch: new mappings no longer require `matlab_title`, while existing values are declared read-only historical metadata and do not authorize rendered figure titles.
- Updated the workbook Schema declaration to 2.3.1 and replaced its conflicting title instructions with a reference to the existing formal-figure output Authority; actual Excel worksheet names, headers and accepted numerical data remain unchanged.
- Removed the obsolete positive `title` lint expectation and its facade diagnostic suppression, preserving the active prohibition on executable overall `title/sgtitle` in formal MATLAB templates.
- Preserved model solving, optional-analysis lifecycle, workbook readers, chart and palette selection, user-owned MATLAB execution and existing preview infrastructure. This patch does not complete the remaining figure-technique/handoff plan stages or claim MATLAB runtime, image-review or CI acceptance.

## Previous release: 9.4.0

- Published the completed writing/readability program as a backward-compatible minor release: nontrivial core derivations and proofs remain recoverable in the paper body by mathematical role, while routine algebra, repeated coefficients, code/log detail and non-core supplements may still be compressed or externalized.
- Added judge-readable writing behavior for professional headings and first-use terminology, readable result tables with invariant accepted values/units/precision, formula-rich narrative organized by reasoning units, and normal use of semantic heading levels 1–3 with deterministic blocking of active LaTeX level 4+ headings.
- Preserved carrier boundaries across CUMCM, MCM/ICM, Diangong and DOCX; non-CUMCM/DOCX writing continues to use the full reasoning fallback and does not inherit the CUMCM top-level skeleton.
- Closed the long-core-proof delivery path with real CUMCM LaTeX pagination and proposition/equation reference-numbering evidence in Production LaTeX attestation.
- Slimmed validation only where W0 paired evidence proved a false positive: the count-only `question_subsection_granularity` review finding was removed, while specific mechanical-split, framework-pending, surface-review and all existing Hard paths remain.
- Completed T01–T18 integrated machine/semantic/hybrid acceptance without adding a Readability Gate, required Project State field, ninth review coverage family, readability score, cross-stage cache or persistent trust token.
- Preserved Model Approval, Semantic Identity, typed stale, numerical/workbook contracts, 03A/03B, user-owned full-fidelity execution, public CLI/report shapes and project layout; existing projects require no bulk migration for v9.4.0.
- Release acceptance remains the complete HSK Skill CI plus Optimization baseline evidence on the final generated head, followed by merge-to-main HSK CI and generated-metadata verification.

## Previous release: 9.3.1

- Restored the Module 02 framework read/write, `mechanism_contracts` producer and design/approval stage-boundary semantics that were accidentally truncated during the v9.3.0 structure-first refactor, with capability-preservation regression coverage.
- Closed the taxonomy-valid task-pack loading gap: Router now authoritatively allows the four unique packs that can arise from one objective plus three structures, Resolver consumes that budget instead of hard-coding three, and the legacy compatibility alias no longer duplicates the obsolete three-pack limit.
- Aligned active modeling surfaces with the v9.3 contract while preserving compatibility identifiers: the route-comparison template now records one minimal-sufficient main model plus `0..N` purpose-driven comparators, project memory persists high-value Condition→Consequence / minimal-sufficiency / comparator facts, and Model Approval compatibility fields no longer imply mandatory classic-versus-advanced routes.
- Updated task-pack headings, maintenance status, plugin discovery and the OpenAI agent discovery summary so active surfaces consistently expose condition-driven structural reduction, minimal-sufficient main-model generation and structure-matched solver selection.
- Preserved route IDs, CLI, required Semantic Identity/Project State roots, Model Challenge/Human Approval lifecycle, workbook/output contracts and user-owned full-fidelity execution; existing projects remain read-compatible and require no bulk migration solely for this patch.
- Release acceptance requires the complete HSK Skill CI and Optimization baseline evidence on the final generated head; valid tests and gates are not deleted, weakened or bypassed.

## Previous release: 9.3.0

- Moved condition-driven structural reduction ahead of model naming and solver selection: current Problem Contract facts are converted into mathematical consequences before the minimal-sufficient main model is proposed.
- Replaced the former mandatory classic-versus-advanced two-route framing with one minimal-sufficient main model plus `0..N` information-bearing comparators; advanced methods remain available when they add a necessary mechanism or answer an explicit comparison question.
- Reused existing `exact / proven_sufficient / heuristic` Reduction Provenance and preserved the existing Model Reviewer, Devil's Advocate, explicit Human Model Approval, Semantic Identity, typed-stale and runtime-gate lifecycle instead of creating a new structural-reduction gate.
- Added domain-specific structure discovery cues for mechanism, optimization, prediction, evaluation, statistics/ML, graph/network, scheduling, game/decision, simulation and spatial tasks; task classification remains a structure-discovery input rather than a direct model-name/algorithm mapping.
- Separated advanced-method roles into `main_model`, `quantitative_comparator` and `exploratory_only`; complexity or novelty alone is not sufficient admission evidence.
- Preserved route IDs, CLI, required schemas, project-state/workbook/output interfaces and user-owned full-fidelity execution. Existing projects remain read-compatible and require no bulk migration solely for this release.
- Release acceptance requires the complete HSK Skill CI and Optimization baseline evidence on the final generated head; valid tests and gates are not deleted, weakened or bypassed.

## Previous release: 9.2.1

- Closed the post-v9.2.0 P7 Analysis Necessity Gate semantic-hygiene gap without adding a new Schema, CLI, project directory, numerical stage or Figure business rule.
- PR A aligned User Execution activation with `accepted_primary_workbook and analysis_necessity_gate == required` and fixed `q1_plot.m` so a valid `result_analysis_status=not_required` project does not require a nonexistent 03B workbook while explicit 03B evidence remains fail-closed.
- PR B aligned active consumers, Artifact Packs and guidance to the published `base3 + conditional2` lifecycle and applied the user-approved minimal Module-04 Authority closure for Figure entry conditions, workbook selection and per-question artifact descriptions.
- PR C replaced obsolete fixed-five textual assumptions with executable conditional-layout invariants in repository hygiene/lint, removed the obsolete fixed-five suppression bridge, and preserved or strengthened validation instead of deleting tests or weakening gates.
- The per-question contract is therefore exact base 3 (`问题X求解.py`, `问题X求解结果.xlsx`, `qX_plot.m`) plus the exact 03B Python/workbook pair only when the Gate is `required`; `not_required` requires a non-empty reason and does not prove robustness/stability.
- Legacy five-file projects and the existing `FULL_FIDELITY_CONFIG / FULL_RUN_CONFIG` plus P5a versionless-receipt readers remain read-only compatible under their existing major-migration exit condition; no user-project migration is forced by this patch.
- Release acceptance remains the complete HSK Skill CI plus Optimization baseline evidence on the final generated head; generated metadata is refreshed rather than hand-forged.

## Previous release: 9.2.0

- Consolidated the approved P1–P8 optimization program into a single minor release without introducing breaking directory, Schema, CLI, numerical, Model Approval, MATLAB or LaTeX semantics.
- Added task-scoped `reading_plan`, global-policy/writing-role deduplication, compact model-paper framework instantiation, canonical `RUN_CONFIG` and versioned `RUN_RECEIPT`, publication-profile MATLAB rendering with a real preview gate, and conditional result-analysis/appendix lifecycle support.
- Retained legacy `FULL_FIDELITY_CONFIG / FULL_RUN_CONFIG` and P5a versionless receipt paths as read-only compatibility in 9.2.0; new writers remain canonical and unknown explicit receipt versions fail closed.
- Recorded an explicit compatibility exit condition: reader removal is deferred to a future major migration (earliest v10) with migration/detection evidence, compatibility-matrix update and dedicated regression.
- Closed P8 infrastructure work using measured evidence: generated-metadata final-head validation is preserved, duplicated RUN_CONFIG parsing is shared, and the large validator is not forcibly split where host-adapter coupling makes a mechanical move unsafe.
- Release acceptance remains the complete HSK Skill CI plus Optimization baseline evidence on the final generated head; tests/gates are not deleted or weakened for this release.

## Previous release: 9.1.0

- Added a Module-04-owned Publication Rendering Grammar for palette profile selection, open-axis publication frames, adaptive canvas/panel geometry, legend strategy, axis/baseline honesty and explicit export policy without creating a second Figure Authority.
- Extended `hsk_apply_scientific_style.m` with `competition_high_contrast`, `journal_balanced` and `monochrome_print` profiles, semantic palette fields, typography hierarchy and backward-compatible legacy palette aliases.
- Added C9--C16 publication patterns: Multi-Metric Comparison Strip, Ordered Ablation Ladder, Composition/Decomposition, Evidence Matrix, Milestone-aware Trend, normalized multi-criteria radar, Density/State-Space Evidence and Comparative Performance Matrix, plus Dedicated Legend Tile / Adaptive Canvas / Open-axis implementation references.
- Consolidated `q1_plot.m` and `data_process.m` around the shared style kernel while retaining a minimal standalone fallback so the existing per-question five-file interface does not gain a hidden sixth-file requirement.
- Preserved Model Approval, Semantic Governance, Runtime Assurance, Project State/Transaction, Workbook Schema, Numerical Verification, Python 03A/03B boundaries and accepted-workbook numerical truth; pure rendering changes do not create a project migration or automatically stale existing Figures.
- Passed the complete Phase A--F regression gate before this carrier transition: Generated-file contract, Static contract lint, Python 3.10--3.14, CUMCM/MCM-ICM/Diangong LaTeX smoke and production LaTeX attestation. MATLAB visual smoke remains an explicit manual rendering check when MATLAB is absent from CI.
- No GitHub Release/tag object is required by current repository governance; release evidence remains the active carriers, Changelog, PR history and validated CI.

## Previous release: 9.0.0

- Advanced the formal active release carriers from `8.9.0` to `9.0.0` after the Phase I I2/I3 compatibility-removal work and I4a v9 applicability renewal were merged and validated on `main`.
- Preserved the intentionally narrow initial-v9 historical readers for L0/read-only projects; retired legacy fields and aliases are not restored as active write or authorization surfaces.
- Kept Project State, State Transition, Resolver, transaction, numerical verification, writing runtime and Model Approval behavior unchanged in this carrier-only transition.
- Kept historical Phase-I baselines, migration fixtures and implementation records pinned to the v8.9 compatibility window instead of rewriting their provenance.
- Phase I I5 closes the final migration/release documentation and release-validation record; all six Phase I gates now have explicit satisfied dispositions for repository release `9.0.0`.
- No GitHub Release/tag object is created by I5 because current repository governance does not require one; active release carriers, Changelog, migration contract and validated `main` history remain the release evidence.

## Previous release: 8.9.0

- Published the Phase C–H staged refactor as the final stable v8.x compatibility checkpoint before Phase I destructive removal; release carriers now identify `8.9.0` while the final program target remains `9.0.0`.
- Preserved the existing v8 compatibility window: no-SIB projects still retain the current legacy semantic-hash write path, artifact/stale aliases remain readable, and no Phase I field/reader removal is performed by this release.
- Retained the Phase I I0 compatibility inventory and L0/L1/L2 migration acceptance matrix as executable evidence for the later v9 removal gates.
- Preserved Python primary solve, accepted-after-primary result analysis, MATLAB workbook-driven figure ownership, and accepted workbooks as the numerical source of truth.

### v9 staged refactor compatibility window — Phase C

- Bound the current per-question Semantic Identity Block (SIB) to Model Approval and Runtime Assurance while keeping `模型论文框架.md` the model-semantics source and reusing the shared `scripts/semantic_identity.py` parser/canonicalizer.
- Human Model Approval binds the current `semantic_revision` and structured `semantic_identity_hash`; partial structured state fails closed and legacy semantic hashes cannot authorize new project-level preprocessing or primary solve code.
- Runtime Assurance recomputes the current framework SIB and promotes `locked_model_spec=verified` only when current, validated and approved identity hashes plus challenge/approval/revision evidence agree.
- Old projects without a SIB remain readable; re-entry into model design, project-level preprocessing, primary solve or regenerated primary code requires current structured identity validation and renewed explicit Human Approval.

### v9 staged refactor compatibility window — Phase D

- Added `core/state_transition_contract.yaml` as the single Authority for stale transitions, lifecycle invalidation, typed cross-question propagation, conservative legacy fallback and deterministic cycle reporting.
- Routed semantic governance, project sync and code delivery through the shared pure `scripts/state_transitions.py` engine; `depends_on.kind` now controls model/result/parameter/data propagation without conflating implementation freshness with mathematical approval.

### v9 staged refactor compatibility window — Phase E

- Migrated implementation artifact identity to canonical `artifact_hashes.primary_code` and `artifact_hashes.analysis_code`; legacy `artifact_hashes.model` remains read-compatible only and conflicting old/new identities stay blocking.
- Confirmed `model_hash / validated_model_hash` have no active writer and only serve legacy primary-code fallback reads; they remain present until the Phase I removal gate.

### v9 staged refactor compatibility window — Phase F

- Added transactional project writes with `project.state_generation`, staged validation, transaction journal/recovery, optimistic generation checks and shared writer integration.
- Project-state persistence remains file-based and preserves existing semantic, workbook and stale Authorities rather than introducing a database or second state truth.

### v9 staged refactor compatibility window — Phase G

- Moved competition writing-runtime selection into `config/competition_profiles.yaml#profiles.*.stable.writing_runtime`; the Resolver is a generic consumer instead of accumulating CUMCM-specific Python constants.
- Preserved CUMCM Template-First progressive behavior and explicit full-reasoning fallback for MCM/ICM, Diangong and Certification Cup.

### v9 staged refactor compatibility window — Phase H

- Mechanically extracted project snapshot and artifact fingerprint helpers from `scripts/sync_project.py` while keeping orchestration, CLI, stale semantics, hashes, transaction behavior and Resolver behavior unchanged.
- Phase H parity was validated by the full HSK Skill CI matrix before merge.

### Phase I preparation — I0 baseline

- Added an exact compatibility-surface inventory plus L0/L1/L2 migration acceptance fixtures/tests.
- I0 intentionally does not stop legacy writes, remove fields/aliases/readers, widen `<9.0.0` compatibility ranges or publish `9.0.0`; the original Phase I six-gate entry contract remains authoritative.

## Previous release: 8.7.4

- Repaired active writing Authority/read-path drift: ordinary body structure and expression consistently point to `modules/05_writing/paper_writing_protocol.md`, while `modules/05_writing/latex.md` remains a carrier-only LaTeX Adapter.
- Removed stale release branding from the active Paper Writing Protocol title and separated the optional DOCX branch display label from the ordinary-writing Module 05A label.
- Clarified MATLAB figure guidance so the high-contrast scientific palette applies to data-driven result figures only; formal mechanism/derivation figures continue to use the Module 04 monochrome-first visual grammar.
- Added focused active-authority hygiene regression coverage while preserving model mathematics, Model Approval, 03A/03B, Workbook/Project State schemas, CLI, project layout, legacy/V622 read compatibility, and the v8.7.3 mechanism rendering behavior.

## Previous release: 8.7.3

- Restored formal mechanism/derivation diagrams to a **monochrome-first** visual grammar: white background, black/dark-gray outlines and text, grayscale de-emphasis, and structure conveyed primarily through geometry, line style, line weight, boundary and spacing rather than semantic blue/green/red fills.
- Extended the existing Mechanism Spec v1 shape vocabulary compatibly with `circle`, `sphere`, `triangle`, `quadrilateral`, and `cylinder` while preserving `rounded_rect`, `rect`, `ellipse`, `diamond`, and `hexagon`; sphere/cylinder semantics remain simple 2D outline/projection primitives rather than decorative 3D rendering.
- Removed default red constraint/switch edges from the draw.io generator and kept color as an exceptional secondary cue only when monochrome encoding is insufficient; black-and-white print distinguishability remains mandatory.
- Kept MATLAB workbook-driven scientific result figures on the existing high-contrast research palette; the rollback applies only to formal mechanism/derivation diagrams and does not change Mechanism Spec fields, CLI, artifact lifecycle, Model Approval, 03A/03B, numerical fact sources, or per-question layout.
- Added focused v8.7.3 regression coverage for monochrome generator output, regular-geometry mappings, Authority/QA wording, and backward-compatible shape support.

## Previous release: 8.7.2

- Closed CUMCM Template Manifest ↔ canonical LaTeX assembly drift by declaring the AI-disclosure slot in the manifest, keeping it conditional by default, and validating canonical body composition against manifest-declared active/default slots.
- Replaced reusable-template AI-use assertions with truth-bound disclosure scaffolding: generic CUMCM and Diangong templates no longer invent team AI usage, while final disclosure remains governed by verified current-edition rules plus project-confirmed actual-use facts.
- Synchronized Cross-File Chapter Handoff terminal seams with the actual final assembly for both AI-disclosure-active and inactive cases, without adding a second prose or compliance Authority.
- Restored the CUMCM reference exemplar to provenance-only semantics and kept its source/adaptation checksum boundary independent from active-template policy changes.
- Hardened active-template release-label hygiene for CUMCM, MCM/ICM and Diangong while preserving `version: 6.2.3` profile/config lineage as a subordinate compatibility version rather than a Skill release carrier.
- Extended repository-reference health conservatively so real active Markdown links validate local/cross-file heading fragments without promoting free prose or legacy examples into runtime pointers.
- Preserved model mathematics, Problem Contract/Model Approval, 03A/03B user execution, Workbook and Project State schemas, Figure/MATLAB ownership, public CLI and per-question project layout.

## Previous release: 8.7.1

- Removed historical Skill-version pinning from the active final-review template; completed matrices hydrate the current version from Bootstrap while unhydrated templates still fail closed in the scorer.
- Closed the Module 02 Formula Trace producer/consumer gap by carrying explicit question and Formula Role fields into the current framework without duplicating the role taxonomy.
- Defined deterministic question-scoped Proposition / Proof derivation across global plan, proposition items and framework preflight, preserving missing/stale/review-required semantics without changing Project State Schema.
- Added behavior-level framework validation for mandatory Per-Question Writing Capability Preflight, including Formula Role/Trace consistency and current Algorithm Trace requirements.
- Added fragment-level health validation for critical active Authority pointers, covering Markdown heading, YAML dotted/dynamic paths, JSON Pointer and existing composite semantic pointers.
- Clarified active old-release labels as architecture provenance rather than current-version carriers and preserved protected Adapter/template semantics through normalization-based regression tests.
- Kept `writing_reasoning_contract.yaml` at schema family `1.8.0` and documented that additive semantic nodes do not bump parser/migration compatibility versions.

## Previous release: 8.7.0

- Added mandatory **Per-Question Writing Capability Preflight** for CUMCM Template-First writing so current Formula Roles, Core Model Summary, Proposition/Proof and Algorithm Presentation states are consumed before each question body without relying on repeated user keywords.
- Added `final_model_relation / key_bridge_relation / supporting_derivation / routine_algebra` Formula Roles; necessary bridge relations survive derivation/cleanup while summaries remain Final-first and avoid formula dumps.
- Added state-driven Proposition and Algorithm activation: planned/current proof work and stepwise/pseudocode load their conditional resources; candidate proposition signals review only, `not_needed` stays compact, and missing/stale states fail closed.
- Exposed current Formula Role, Core Model Summary and per-question preflight pointers through Output Contract and persisted only compact project-specific activation state in `模型论文框架.md`.
- Expanded behavior fixtures, resolver projection coverage and six fixed writing-surface trials while preserving v8.5 Author Reasoning Voice, v8.6 Model Construction Rationale, simple-problem anti-bloat and Compact Runtime conditional loading.
- Preserved Model Approval, 03A/03B, user execution, Workbook/Project State, numerical verification, Figure Evidence and formal LaTeX delivery semantics.

## Previous release: 8.6.1

- Closed v8.6 release-state drift by separating final merged/post-merge-CI facts from preserved candidate-stage evaluation history; older v8.4/v8.5 evaluation documents are explicitly historical non-Authority records.
- Clarified that CUMCM fixed four-heading checks are maintained example/compile smoke only; runtime subsection structure remains adaptive and has no fixed heading count or title-length rule.
- Isolated A196/reference provenance from runtime writing semantics, internal subsection decisions and model/solver selection while retaining chapter-topology provenance.
- Added named `output_contract` pointers for Model Construction Rationale and Numerical Parameter Evidence without duplicating their reasoning rules.
- Clarified raw declarative route/module output surfaces versus resolver-returned effective plans, preserving all existing Model Approval, preprocessing and user-execution boundaries.
- Normalized historical release headings and added regression coverage; no model mathematics, 03A/03B, workbook/project-state schema, figure ownership, CLI or public runtime field was changed.

## Previous release: 8.6.0

- Added **Model Construction Rationale** so non-trivial model choices recover current structure, modeling gap, chosen mathematical structure, why it closes the gap, applicability conditions and downstream role.
- Added local applicability and explicit solver-precondition evidence without fixed applicability sections, algorithm-name inference or generic algorithm praise.
- Strengthened `exact / proven_sufficient / heuristic` reduction provenance and evidence-bound language; heuristic scope cannot be promoted to strict equivalence or global optimality.
- Added Numerical Parameter Rationale for grid/discretization/step/tolerance choices while preserving the 03A/PQS versus accepted-after-03B boundary.
- Added Section Title Minimality and Adaptive Subsection Separation so complex independent tasks may keep short navigation headings while simple argument chains remain compact; no title-count or character Hard Rule was introduced.
- Preserved v8.5 Author Reasoning Voice, Claim Strength, Model Approval, numerical/workbook, Figure Evidence and LaTeX/template boundaries; added 12 fixed semantic cases and v8.6 regression coverage.

## Previous release: 8.5.0

- Deepened **Model/Solution Author Reasoning Voice** into 11 evidence-bound reasoning acts rather than a pronoun or style-frequency rule.
- Added Question Closure, Claim Strength Alignment, Reasoning Necessity and Problem-Specificity so natural questions, judgments, simplifications and interpretations must have real mathematical destinations and evidence boundaries.
- Clarified the semantic roles of “我们”, “本文” and mathematical/object subjects without quotas, bulk replacement, authorship inference or fabricated team history.
- Expanded the optional reasoning examples, AI Cleanup and final semantic review while keeping examples conditional and preserving the single Paper Writing Protocol authority.
- Added v8.5 fixed voice cases and regression coverage; existing Formula/Proof/Algorithm/Citation/Numerical/Global-Optimum gates remain authoritative, and simple direct problems retain an explicit no-bloat/no-change path.

## Previous release: 8.4.0

- Incorporated the unreleased v8.3.1 work from PR #108 into a compatible **Model/Solution Reasoning and Author Voice** enhancement, not a separate historical release.
- Strengthened the actual model, solver and result instructions in Paper Writing Protocol §7–9: task-to-objective rationale, non-obvious variables, constraint consequences, approximation boundaries, structure-led computation, implementation choices, proof-to-algorithm consequences and evidence-backed interpretation.
- Made informative author judgments and natural questions normal prose choices under §7.3, without pronoun quotas, fixed narrative sentences, invented consensus/experiments, authorship inference or changes to real AI-use disclosure.
- Clarified Paragraph Necessity and AI Cleanup so irreplaceable choice reasons, mathematical roles and conditions survive cleanup even without new formulas or data; empty announcements, repetition, excessive colloquialism and unsupported claims still require revision.
- Kept a single prose authority, routed the relevant existing writing/review/cleanup stages to it, and added one conditional examples page without new default preload, project fields, runtime stages or gates.
- Added four fixed synthetic writing inputs, scope-preservation regressions and an explicitly non-blind complete-section writing/cleanup review; retained audit behavior tests without claiming that token checks establish prose quality.
- Preserved v7.20/v8 chapter detail, template order, proof/pseudocode forms, cross-file handoff and numerical/model/workbook contracts; existing projects require no migration or automatic prose rewrite.

## Previous release: 8.3.0

- Added **Editable Mechanism Diagram Production & Visual QA** under the existing Figure Evidence Authority for problem-specific, non-data-driven draw.io mechanism figures.
- Added an optional v1 Mechanism Diagram Spec, deterministic uncompressed `.drawio` generation, and structure/geometry/safety validation with human-readable and JSON output.
- Added precise routing for draw.io/editable mechanism requests while keeping ordinary result-figure routes free of draw.io implementation resources.
- Required a current rendered preview and manual semantic/visual review before `approved_for_paper`; machine validation explicitly does not judge arrow semantics, mathematics, missing mechanisms, aesthetics, or claim support.
- Preserved MATLAB ownership for workbook-driven figures, the per-question five-file layout, Project State and Model Approval schemas, numerical/writing/review Authorities, and official package allowlists.
- Added v8.3 regression coverage for deterministic output, invalid specs, geometry/security failures, approval-state boundaries, version parity, and protected semantic-file drift.

## Previous release: 8.2.0

- Added **Final Review Compliance & Evidence Sweep** as the single final-submission review authority for verified edition rules, anonymity/metadata, AI disclosure consistency, citation entity integrity, rendered-page defects, figure/table information value, package evidence and dynamic cross-question coverage.
- Added `templates/review/final_review_matrix.yaml` with eight stable coverage families and atomic findings carrying source, verification mode, location, evidence, severity, status and corrective action.
- Extended `scripts/score_submission.py` with optional v1 matrix validation while preserving the exact legacy report output path; explicit scores remain authoritative and finding counts never create fixed deductions.
- Added `verified_official_rule_violation`, usable only with a current verified rule source/date and an unresolved blocking finding; Hard Fail remains independent of the weighted score.
- Kept the matrix outside Project State, model semantic hashes, Model Approval, 03A/03B, Figure Evidence and official package allowlists; added no PDF parser, network dependency, report-schema migration or pre-delivery gate.
- Added dedicated regression and static-contract coverage for enum/schema failures, evidence completeness, official-rule provenance, version parity, Authority isolation and protected-file drift.

## Previous release: 8.1.1

- Repaired the active `SKILL.md` Authority navigation so project memory points to the existing `templates/model/model_paper_framework.md` instead of the nonexistent `core/project_memory_contract.yaml`.
- Kept root and packaged Skill entrypoints byte-identical and synchronized all explicit current-release carriers to v8.1.1.
- Added a deterministic health regression that extracts repository-relative paths from the active Authority navigation, rejects the obsolete pointer and verifies that every target is readable.
- Preserved all protected model, numerical, workbook, project-state, 03A/03B, figure, Template Manifest, Writing Reasoning, Paper Writing Protocol and Cross-File Chapter Handoff semantics.

## Previous release: 8.1.0

- Added **Cross-File Chapter Handoff** as a final-assembly continuity capability for modular CUMCM LaTeX papers, so actual adjacent active physical files preserve objects, symbols/terms, dependencies, claims, non-duplication and only necessary semantic bridges.
- Kept ordinary prose semantics in `modules/05_writing/paper_writing_protocol.md`; `core/writing_runtime_contract.yaml` only resolves final-order adjacency and read/write/gate timing, `模型论文框架.md#Chapter Handoff Map` stores optional writing-only project facts, and final review consumes the Authority through an assembled seam sweep.
- Reused `template_manifest.yaml#paper_skeleton.ordered_slots + activation` instead of adding a second assembly-order schema; inactive data/model-preparation/question files cannot create false current seams.
- Preserved `cross_question_progression.activate_when=actual_dependency_exists`, existing Terminology/Numeric/Claim/Paper Fragment capabilities, and the no-forced-transition boundary.
- Kept Chapter Handoff outside the model semantic hash: pure handoff wording/status changes do not bump `semantic_revision`, stale `locked_model_spec`, trigger Model Approval or rerun 03A.
- Preserved old-framework readability, single-file `not_applicable` behavior, full-authority fallback for non-CUMCM/missing-manifest routes, and all protected model/numerical/workbook/project-state/03A/03B/figure semantics.
- Added v8.1.0 regression coverage for Authority separation, minimal/conditional assembly order, Q1→Q2→Q3 adjacency, abstract final-reading order, optional project memory, semantic-state isolation and connector-frequency false positives.

## Previous release: 8.0.3

- Clarified Core Model Summary as two explicit concepts: `semantic_summary_mode` (`required / inline / not_applicable`) for mathematical narrative need, and CUMCM `rendering_mode` (`displayed / inline / omitted`) for presentation.
- Kept the former `modes` and `old_to_new_modes` fields as deprecated read-only aliases through v8.x, with a single canonical semantic-to-rendering mapping in `core/writing_reasoning_contract.yaml`.
- Preserved CUMCM rendering, simple-problem anti-bloat, historical-paper ordering, Template-First authoring, Model Approval, numerical verification, user execution and all project schemas unchanged.
- Added regression coverage for the two-layer vocabulary and compatibility aliases.

## Previous release: 8.0.2

- Slimmed `SKILL.md` and packaged `skills/mathmodel-skill/SKILL.md` to discovery, startup delegation, stable hard boundaries and Authority pointers instead of duplicating detailed domain contracts and release-history rulebooks.
- Slimmed `PROJECT_INSTRUCTIONS.md` to project startup/recovery, execution ownership, writing/delivery delegation and repository-maintenance procedure; detailed preprocessing, 03A/03B, figure, algorithm and writing semantics remain in their single Authorities.
- Preserved exact root/package Skill parity, bootstrap-first `resolve_runtime.py` routing, Human Model Approval, user-owned full-fidelity execution, accepted-workbook numeric facts, MATLAB non-recomputation, Template-First writing, legacy isolation and resolver-returned pre-delivery gates.
- Added regression coverage that prevents versioned business rulebooks from regrowing inside the entrypoints while keeping the v8.0.1 chapter-capability audit explicitly historical.

## Previous release: 8.0.1

- Completed a three-way chapter-capability audit against the v7.19 writing authority, the user-approved v7.20 R1 plan and the v8.0.0 compact runtime; added `docs/v801_chapter_capability_preservation_audit.md` as a non-authoritative migration/evidence matrix.
- Restored ordinary-route detail for title/keywords, data/preprocessing, shared foundations, optimization variables/domains/units, objective meaning, constraint sources, non-optimization summaries, proposition boundaries, solver encoding/parameters/termination/output mapping, numerical style, terminology, citations, role-specific figure interpretation and evaluation boundaries.
- Preserved the full `model_establishment_solution_narrative` reasoning Authority unchanged while keeping `latex.md` a carrier-only Adapter; complex Terminology/Numeric/Citation disputes now explicitly trigger the full-authority fallback.
- Added a maintained Q3 later-question inheritance/extension template so Q1, Q2 and Q3 all carry the adaptive MODEL → SOLVE → RESULT → VALIDATE writing contract without forcing simple questions into four literal headings.
- Extended the conservative surface audit with explicit-stage order reversal, solver-first narrative and consecutive-figure adjacency findings, including negative tests for professional headings and structure-led solver introductions.
- Added an explicit v7.20/v8.0.1 final-review consumer checklist for detailed model establishment/solution content, objective/constraint rendering, result-validation bridging, surface findings and Document Length Profile handling.
- Clarified which AI Cleanup risks are implemented machine findings and which remain human/semantic review categories; the audit no longer implies that undeveloped regex checks already exist.
- Added v8.0.1 chapter-preservation and v7.20 execution-closure regression coverage while retaining v8.0.0 project read compatibility and the no-automatic-body-rewrite migration boundary.
- Replaced eager ordinary-writing consumption with an explicit Template-First progressive authoring sequence: inspect the manifest without drafting, then read/write/gate problem restatement, problem analysis, assumptions/symbols/preparation, each question's model/solve/result/validate chain, evaluation/references/appendix and finally the evidence-backed abstract; draft semantic review now precedes AI Cleanup, compile and final review.
- Made proposition/proof and stepwise/pseudocode reachable conditional branches inside each question-writing stage, loading the full reasoning Authority plus `proposition_proof.md` or `algorithm_flow.md` before the relevant passage instead of relying on implicit recall.

## Previous release: 8.0.0

- Replaced the former LaTeX-centered writing authority with a five-layer Template-First architecture: CUMCM Template Manifest, Paper Writing Protocol, full semantic reasoning Authority, LaTeX Adapter, and project-facts/audit consumers.
- Added `templates/latex/cumcm/hsk/template_manifest.yaml` as the machine-readable CUMCM structure authority. The canonical topology follows the user-provided A196 paper only at chapter level; no paper body, formulas, figures, data, algorithms or results are copied.
- Adapted the user-provided `example_mm_r1.tex` as a provenance-checked layout reference while retaining official `cumcmthesis` compliance. Compatible table, code-listing and appendix infrastructure is exposed without overriding official page or title rules.
- Made project-level data and shared model preparation conditional, inactive-by-default slots. Each enabled question remains an independent `问题X模型建立及求解` top-level section with adaptive `MODEL → SOLVE → RESULT → VALIDATE` functionality inside it.
- Added `core/writing_runtime_contract.yaml` and declarative runtime dependencies. Ordinary CUMCM LaTeX writing uses the compact manifest/protocol/adapter package; DOCX and competitions without their own Template Manifest retain the complete reasoning fallback, and final review always loads the full Authority.
- Slimmed `modules/05_writing/latex.md` to a carrier Adapter. Ordinary mathematical narrative now lives in `paper_writing_protocol.md`; complex cross-task semantics remain in `writing_reasoning_contract.yaml`; consumers and review modules point to those authorities instead of copying them.
- Integrated the v8 surface audit into the formal `audit_paper_prose.py` / `audit_latex_project.py` chain for workflow-vocabulary leakage, decorative quote density, concept-label chains and Result-to-Validation bridge risk. These checks remain conservative and do not infer mathematical correctness.
- Added explicit v7 read-only compatibility and a manual dry-run migration guide. Existing filled LaTeX bodies are never automatically renamed, split, reordered or overwritten; compatibility mappings remain available throughout v8.x and are not removed before v9.0.0.
- Extended active subordinate-contract compatibility metadata through v8.x, recorded user-requested template overrides with official-format impact, and kept the MCM/ICM empty-skeleton bibliography compile smoke deterministic via an explicit removable example-reference marker.
- Restored explicit chapter-content guidance inside the Paper Writing Protocol: problem restatement must reconstruct rather than copy the prompt; problem analysis must form a continuous object-to-model argument rather than a scattered software checklist; abstracts must cover each question's task, model, objective/conditions/constraints, method, result, evidence-backed validation and conclusion without inventing sensitivity claims; assumptions, symbols, evaluation, conclusion and appendix boundaries remain available after the LaTeX split.
- Preserved model mathematics, Human Model Approval, Primary Numerical Verification/PQS, Workbook Schema, Project State Schema, Task Taxonomy, Python/MATLAB ownership, result-analysis semantics and the user-execution boundary.

## Previous release: 7.19.0

- Added **Within-Question Subsection Architecture** under the existing `model_establishment_solution_narrative` authority so second/third-level subsections, formulas, solver discussion, results and local validation follow real local mathematical dependency and solution reasoning while the established top-level paper skeleton and Question 1/2/3 order remain frozen.
- Added explicit top-level guards: `preserves_top_level_paper_skeleton=true`, `may_reorder_top_level_sections=false`, and `may_reorder_question_sections=false`. Data/preprocessing and shared-foundation rules may organize only their own internal content and cannot gain authority to reorder question chapters.
- Added **Detail Allocation Governance** based on decisiveness rather than uniform section length. Derivations that determine model structure, predicates/boundaries, feasible regions, solver fit, headline answers or validation claims are expanded to a complete information chain; routine algebra, repeated symbol translation, unchanged inherited relations, generic algorithm background and point-by-point table/curve repetition are compressed.
- Added problem-specific solver detail rules: explain solver fit, encoding, objective evaluation, constraint handling, key parameters/accuracy/termination and output mapping, while algorithm history, generic advantages and unchanged standard operators remain compact.
- Added `simple_problem_anti_bloat=true`, preventing direct analytic/simple-calculation questions from being forced into extra subsections, algorithm blocks, core-model summaries, figures or validation solely for structural symmetry.
- Added adaptive **Figure Result Narrative** with functional roles for relation/local purpose, decisive feature, necessary key value, current-question link, evidence-supported reason and optional closure. The rule explicitly forbids fixed sentence counts, caption repetition, point-by-point reading and unsupported causal explanation.
- Added adaptive profiles for parameter/sensitivity, optimization convergence, prediction/fit, spatial/network and mechanism/geometry figures, plus multi-panel guidance that explains the common question first and only expands panel differences that independently affect the conclusion.
- Added **Question-Section Narrative Closure** so each `问题X模型建立及求解` chapter locally closes `task → model semantics → solver consumption → result interpretation → direct answer` without adding a new runtime gate or a mandatory “小问结论” sentence.
- Extended `modules/05_writing/latex.md`, `modules/05_writing/ai_cleanup.md`, `PROJECT_INSTRUCTIONS.md` and regression coverage as consumers of the single writing authority. AI Cleanup may review local-order/detail/figure risks but cannot infer mathematical correctness, causal validity or detail quality from word counts, formula counts, heading syntax or figure-reference keywords.
- Upgraded `core/writing_reasoning_contract.yaml` schema from 1.4.0 to 1.5.0 while preserving model mathematics, Human Model Approval, Numerical Verification/PQS, 03A/03B, Workbook Schema, Project State Schema, Task Taxonomy, Python/MATLAB ownership, CLI and runtime-gate semantics.
- Added eight-family human prose smoke coverage for mechanism/geometry, continuous optimization, statistics/regression, time series, network/scheduling, simple analytic, multi-question progression and figure-dense/multi-panel writing.
- Archived the completed v7.19 implementation plan under `legacy/architecture/v7.19_main_body_architecture_detail_figure_writing_hardening_plan.md`; active runtime and generated indexes depend only on current authorities, consumers and tests.

## Previous release: 7.18.0

- Added a single `model_establishment_solution_narrative` writing authority for continuous model-establishment, solution and result-interpretation prose without changing modeling, solver, validator or numerical semantics.
- Added **Continuous Mathematical Narrative** and **Formula Prose Rhythm** so core relations are introduced from the current mathematical need, connected to their basis, and followed by the structural or downstream consequence instead of being presented as disconnected formula blocks.
- Added **Transition Function Governance** based on logical roles (`inherit / gap / introduce / transform / solve_entry / result_entry / interpret / increment`) rather than a connector-word phrase bank.
- Added **Professional Heading Semantics** so question subsections are organized by independent mathematical tasks; generic headings are review risks, while no hard “XX 的 XX” or heading-grammar template is introduced.
- Added **Model-to-Solver Bridge** rules requiring solver choice to emerge from actual model structure, computational difficulty or completed simplification, with problem-specific encoding, constraints, accuracy and termination stated before generic algorithm exposition.
- Added adaptive **Result-adjacent Interpretation** profiles for point optima/parameter sets, curves/figures and algorithm/accuracy/validation evidence; key results should be interpreted near the evidence rather than detached into a final generic paragraph.
- Clarified that model-establishment sections do not repeat full problem analysis, model-assumption lists or prompt restatement, and that later questions write inherited structure plus genuine mathematical/solver increments only.
- Extended AI Cleanup to review report-like model listing, formula-without-purpose, solver-first narrative, generic-heading density, management-only transitions and detached result interpretation while explicitly forbidding keyword-only judgments of mathematical correctness or narrative quality.
- Added v7.18 regression coverage and six-family human prose smoke for mechanism/geometry, continuous optimization, statistics/regression, simple analytic, multi-question progression and result-dense writing.
- Preserved Model Challenge/Human Approval, Numerical Verification/PQS, 03A/03B, Workbook Schema, Project State, runtime routing, user-owned full-fidelity execution and all existing numerical/figure/LaTeX provenance semantics.

## Previous release: 7.17.0

- Added conditional **Mechanism / Geometry Structural Validity** closure inside Module 02 without introducing a new lifecycle gate, project-state field or task-taxonomy capability.
- Added **Predicate Closure** for object domain, active/visible subset, reference frame, exact predicate, quantifier order and line/ray/segment/surface/volume semantics; independent equivalent predicates may cross-check implementations but do not replace proof.
- Added **Event Topology / Boundary** requirements for multi-interval events, valid local brackets, endpoint update rules, tolerances and fallback logic; global bisection is rejected when event state can follow `0→1→0` or otherwise switch non-monotonically.
- Added **Reduction Provenance** with `exact / proven_sufficient / heuristic`. Heuristic reductions must retain discarded-domain audit evidence and calibrated claim scope instead of being presented as full-domain proof.
- Added **Solver Applicability / Objective Landscape** reasoning and approval-bound conditional probes. Solver families must be justified from actual mathematical/landscape structure; cross-problem fixed numeric switch thresholds and post-hoc criteria are forbidden.
- Added explicit **Multi-resource Composition** semantics, including `forall-exists` versus `exists-forall`, to prevent invalid simple summation, overlap handling and hidden-coupling removal.
- Added **Surrogate / Decomposition → Original Model Reevaluation** so final candidates return to the original objective and all original hard constraints before headline results are accepted.
- Clarified the mechanism/optimization 03A/03B boundary: current locked-model intrinsic validity remains in 03A, while parameter sensitivity, stress scenarios, alternative models/algorithms, multi-seed or multi-initial-value claim stability and broader failure-boundary exploration remain post-acceptance 03B.
- Extended the existing `v0.8-project-memory` framework with optional structural-validity facts and evidence anchors only; no framework schema migration, new project report, workbook migration or CLI migration was introduced.
- Added v7.17 regression coverage for structural validity and authority boundaries while preserving the existing Problem Contract, Model Challenge/Human Approval, Numerical Verification/PQS authority, Project State, Workbook Schema, per-question five-file layout and user-owned full-fidelity execution.

## Previous release: 7.16.0

- Restored and strengthened the paper-writing specification without reviving the legacy full-auto architecture. Existing single-authority governance remains centered on `core/writing_reasoning_contract.yaml`, `modules/05_writing/latex.md`, project memory and accepted workbooks.
- Added explicit **Model / Solver / Validator** role separation so mathematical model identity cannot be replaced by solver names, validation algorithms, software or implementation architecture.
- Added **Model Naming** governance: project-specific model names remain allowed, but first formal use must expose the standard mathematical model type and the load-bearing problem structure.
- Added **Optimization Model Expression** closure for optimization/scheduling/routing/allocation/control problems: standard model type and real objective → decision variables/objects → objective function and interpretation → constraints by source → adaptive core-model summary → solver/validation.
- Upgraded optimization abstracts so they must communicate what is being optimized; listing decision variables and an algorithm without objective semantics is no longer considered model-information closure.
- Added **Solver Justification** for first use, cross-question reuse, solver changes and alternative-method evidence. Alternative algorithms enter the paper only when actually run and traceable as baseline, alternative or validator with comparable evidence.
- Added **Subsection Granularity** governance focused only on second-level subsections inside question chapters. About 3--4 major units is a default reading structure, not a hard count; top-level chapter count is not restricted, and count alone cannot decide section quality.
- Added five-level **Claim Strength Calibration** (`PROVEN`, `VERIFIED_NUMERIC`, `COMPARATIVE`, `OBSERVED`, `HEURISTIC`) to stop numerical/heuristic evidence from being polished into unsupported proof, global-optimality, universal-comparison or strong-robustness claims. Abstract wording receives the strictest scope review.
- Extended the existing `v0.8-project-memory` model-paper framework with standard model type, formal model name, Model/Solver/Validator roles, optimization-objective abstract closure, solver evidence roles, subsection planning, and headline claim Evidence Level/Scope, without a framework schema-version migration.
- Extended model design and final review so paper-ready model identity and algorithm rationale are captured upstream rather than reconstructed during writing from chat memory.
- Extended `scripts/audit_paper_prose.py` conservatively: question-subsection fragmentation and unresolved framework objective/granularity states produce review findings; explicit `HEURISTIC + global optimum` framework conflicts block delivery; raw strong wording remains a warning unless registered semantics establish a deterministic contradiction.
- Removed the obsolete expectation that every complex question must have a standalone `核心模型汇总` subsection. Core-model summary remains adaptive (`required / inline / not_applicable`) and may close the model-construction subsection directly.
- Added v7.16 regression coverage for model identity, optimization abstract/objective closure, model-before-solver order, algorithm justification, subsection scope, claim calibration, framework storage and prose-audit behavior.
- Preserved v7.15 Primary/Analysis Evidence Capture, Scientific Figure Synthesis, v7.14 PQS/Verification-ID semantics, Workbook and Project State schemas, the per-question five-file layout, user-owned full-fidelity execution, caption-owned formal figure titles, LaTeX attestation/submission provenance and legacy read compatibility. Historical accepted numerical results are not forced to rerun solely for the writing upgrade.

## Previous release: 7.15.0

- Added capability-driven **Primary Evidence Capture** to the primary-solve stage: current-run decision/state/process/structure evidence that is already produced by the locked computation may be retained in the accepted-candidate workbook instead of being collapsed to final-answer-only summaries.
- Preserved the v7.14 primary/result-analysis semantic boundary: any evidence that requires changing parameters, scenarios, seeds, initial values, algorithms, model structure or validation windows and re-running an alternative world remains exclusively in post-acceptance result analysis.
- Added **Analysis Evidence Capture** so sensitivity, robustness, threshold, scenario, algorithm, seed and heterogeneity studies retain fine-grained evidence tables rather than only summary judgments.
- Upgraded Module 04 with **Scientific Figure Synthesis**, **Basic-form Challenge**, **Composite Encoding Preference**, **Scientific Rendering Profiles**, Missing Scientific Evidence review and a paper-level **Figure Portfolio Scientific Quality Gate**. Core figures are now selected from evidence structure and model-specific scientific content rather than from a basic chart-type default.
- Restored a high-contrast scientific palette for primary evidence (`#1478FF`, `#F04444`, `#16B364`, `#F79009`, `#7A5AF8`) while keeping auxiliary elements visually deweighted, white backgrounds, `grid off` by default and semantic consistency across figures.
- Updated MATLAB templates, figure contracts/QA, chart-selection guidance and starter Python templates so rich accepted evidence can support distributions, uncertainty bands, feasible boundaries, Pareto structure, spatial fields, trajectories, local zoom and other evidence-driven composite expressions without MATLAB recomputation.
- Preserved caption-owned formal titles: formal MATLAB figures still omit overall `title`/`sgtitle`; DOCX/LaTeX captions own the formal figure number/name, and panel labels/axes/units/legends/direct annotations remain evidence-driven.
- Preserved Workbook Schema 2.3.0, Project State Schema, v7.14 numerical-verification/PQS/Verification-ID semantics, the per-question five-file layout, user-owned full-fidelity execution, LaTeX attestation/submission provenance, V622 read-only compatibility pointers and `assets/nature_figure/**`.
- Archived the completed implementation plan under `legacy/architecture/v7.15_scientific_figure_elevation_plan.md` so the active runtime depends only on the current authorities, contracts, modules, templates and tests.

## Previous release: 7.14.1

- Aligned formal Figure Evidence semantics across Module 04, MATLAB templates, writing/review consumers and `core/output_contract.yaml`: formal paper figures no longer embed a redundant overall `title`/`sgtitle`; DOCX/LaTeX captions own the formal figure number/name while panel labels, axes, units, legends and necessary direct annotations remain available.
- Reversed strict figure synchronization accordingly: `scripts/sync_project.py --delivery-scope figures` now rejects executable overall MATLAB titles instead of requiring them, while preserving the existing `matlab_has_title` report field for backward report compatibility and ignoring comment-only title text.
- Restored the restrained scientific plotting defaults used by the current paper workflow: white background, solid dark/low-saturation primary colors and `grid off` by default; preprocessing figure guidance delegates style to `modules/04_figure_evidence.md` instead of maintaining a second high-saturation rule.
- Repaired active navigation lag so `PROJECT_INSTRUCTIONS.md` describes primary solve as primary computation plus only the intrinsic numerical-validity evidence needed for acceptance, and `REPOSITORY_INDEX.md` explicitly lists `core/numerical_verification_contract.yaml` and `scripts/validate_numerical_evidence.py`.
- Moved completed one-shot architecture/implementation notes from active `docs/architecture/` into `legacy/architecture/`, preserving provenance while removing them from the active Skill surface and generated metadata.
- Added/updated regressions for root/package Skill parity, formal MATLAB no-title semantics, strict figure-sync behavior, archive hygiene and the unchanged v7.14 primary-quality/result-analysis boundary.
- Preserved Workbook Schema, Project State Schema, numerical-verification protocol semantics, per-question five-file layout, user-owned full-fidelity execution, LaTeX attestation/submission provenance and V622 read-only compatibility pointers.

## Previous release: 7.14.0

- Added `core/numerical_verification_contract.yaml` as the single field-level authority for intrinsic primary numerical validity before a solution workbook may be accepted.
- Added a Primary Quality Specification (PQS) design step so active capabilities determine only the minimum feasibility/residual/discretization/convergence/primary-OOS/uncertainty/leakage/calibration/identifiability evidence required for the current primary computation.
- Added `scripts/validate_numerical_evidence.py` and integrated it into returned-workbook validation so v7.14 quality-gate rows are independently rechecked through `Verification ID → actual value → threshold → relation → evidence sheet → threshold source`; self-declared Boolean pass values are no longer sufficient for new primary runs.
- Strengthened row-level consistency checks for constraint violations and equilibrium/conservation residuals and added strict trace support for marked discretization/convergence evidence without forcing a universal convergence-order formula.
- Preserved the two-stage Python boundary: parameter sensitivity, stress scenarios, alternative algorithms/structures, multi-seed or multi-start claim stability, heterogeneity, error decomposition and broader out-of-sample stability remain exclusively post-acceptance result analysis.
- Added `primary_quality_protocol_version=1.0.0` to newly delivered primary full-fidelity configurations so current primary runs cannot silently fall back to legacy Boolean-only quality semantics; preprocessing and analysis stages do not carry that field.
- Preserved read compatibility for v7.13 and older historical workbooks without Verification IDs; migration is per-question only when an old project re-enters current primary solving.
- Preserved project layout, Project State Schema, user-owned full-fidelity execution, MATLAB plotting ownership, Figure/LaTeX/submission behavior and legacy read paths.

## Previous release: 7.13.0

- Added an evidence-driven Figure Enhancement Gate after Figure Layout Gate, with default `none` and conditional Local Zoom, Small Multiples, Focus Highlighting, Semantic Background, Composite Diagnostic, and Conditional 3D.
- Added `templates/figure/figure_enhancement_patterns.md` for reusable enhancement implementations while keeping `modules/04_figure_evidence.md` the sole plotting decision authority.
- Added explicit data-honesty rules: local zoom must retain global context and traceable ROI; small multiples must use comparable scales or disclose scale differences; semantic backgrounds require real thresholds/states/stages; discrete evidence may not be spline-smoothed merely for appearance.
- Extended Figure Contract, QA and chart selection with Enhancement/rationale, embedded/detached zoom, overview + detail, structured small multiples, joint prediction diagnostics and conditional 3D admission.
- Updated the `figures` route and full-workflow resume load so enhancement patterns are available at the actual Figure Evidence stage.
- Preserved Workbook Schema, Project State Schema, Python/MATLAB ownership, per-question five-file layout, user full-fidelity execution, LaTeX attestation and legacy read compatibility.

## Previous release: 7.12.0

- Added `core/runtime_assurance_contract.yaml` as the single authority for runtime context precedence, intent provenance, artifact assurance, declarative contract dependency closure and authority fingerprinting.
- Added default state-aware resolver `scripts/resolve_runtime.py`; preserved `scripts/resolve_workflow.py` as the legacy stateless compatibility entrypoint.
- Added optional project-state hydration for competition, preprocessing decision, scoped classification and verified artifacts without changing Project State Schema or legacy CLI arguments.
- Added deterministic intent diagnostics with matched keywords, score, confidence band, ambiguity and selection reason.
- Added file-backed artifact assurance requiring accepted state, existing path and matching SHA-256; stale/hash-mismatched current-state evidence blocks legacy name-only promotion.
- Added additive `runtime_plan` and `assurance` envelopes while preserving the existing resolver plan fields and task-code execution boundary.
- Added declarative module/gate contract dependency closure and authority fingerprinting across Bootstrap, Router, Manifest and Runtime Assurance Contract.

## Previous release: 7.11.2

- Ran a runtime-health audit before v7.12 planning and kept the repair scope to invocation/read-path/lifecycle coherence rather than new modeling capabilities.
- Expanded high-frequency Skill discovery triggers for problem audit, model design, full solving, result analysis, final review and submission-package requests while keeping root and packaged Skill entrypoints identical.
- Aligned `preprocessing_decision` lifecycle across the preprocessing authority, Skill summary, Runtime Router and primary-solve module: audit + model-route/data-requirement comparison → decision → proposed model/challenge → explicit approval → conditional project-level preprocessing.
- Corrected the Module 03A pre-code sequence to the Router-authoritative `semantic_governance → model_approval → code_delivery` order.
- Reclassified legacy `skill_version: 7.4.2` metadata in preprocessing/user-execution/code-quality contracts as introduction/compatibility metadata, without changing their contract versions or runtime semantics.
- Added runtime-health regression coverage for full root/packaged Skill parity, discovery triggers, lifecycle ordering and subordinate-contract version-carrier hygiene.
- Preserved CLI, Project State Schema, Workbook Schema, per-question five-file interface, Python/MATLAB ownership, full-fidelity user execution, LaTeX attestation v3 and submission provenance.

## Previous release: 7.11.1

- Consolidated workflow authority so `core/workflow_router.yaml` owns route ordering and runtime boundary declarations, while `core/module_manifest.yaml` is limited to module/artifact/gate graph semantics.
- Removed resolver-embedded `*_GATES`, `*_OUTPUTS`, `DOWNSTREAM_MODULES`, and `MODEL_APPROVAL_REQUIRED_INTENTS` policy constants; `scripts/resolve_workflow.py` now executes declarative router segments and derives module ordering from the router authority.
- Reduced Model Approval duplication in Modules 02/03: field-level challenge/approval binding remains defined only by `core/model_approval_contract.yaml` and enforced by `scripts/validate_model_approval.py`.
- Narrowed `core/output_contract.yaml` semantic/execution/result sections to authority pointers plus delivery-integration switches instead of parallel policy copies.
- Repaired stale release/proposition fixtures and added invariant-focused tests for single authority, boundary dispatch, manifest scope, and resolver policy hygiene.
- Preserved CLI, project-state schema, Workbook Schema, per-question five-file interface, Python/MATLAB ownership, full-fidelity user execution, LaTeX attestation v3, and submission provenance.

## Previous release: 7.11.0

- Added independent Model Reviewer and Devil's Advocate challenge passes after semantic closure and Complexity Sanity, before the model can be locked.
- Added explicit Human Model Approval bound to the current semantic revision/hash; silence or vague continuation is not approval, and blocking challenge findings cannot be waived.
- Added `proposed_model_spec`, `awaiting_model_approval`, approval state fields and `scripts/validate_model_approval.py` so project-level preprocessing and primary solve code cannot bypass the current approved model.
- Semantic revision/hash drift now invalidates the previous challenge, approval and locked model while preserving read-only compatibility for historical projects.
- Kept Python/MATLAB ownership, Workbook Schema, full-fidelity user execution, modular LaTeX, compile attestation v3, submission provenance and the per-question five-file interface unchanged.

## Previous release: 7.10.1

- Made resolver-returned `pre_delivery_gates` the complete ordered execution list for Agent/Bootstrap/entry consumers; removed the stale four-gate consumer enumeration that could omit `submission_package_validation`.
- Aligned the human-readable terminal chain to review → package generation → resolver gates → `validated_submission_package`, without changing the existing router or validator semantics.
- Added missing repository/script navigation for `render_paper.py`, `latex_delivery.py`, `hsk_pack_submission.py` and `validate_submission_package.py`.
- Standardized reproducibility metadata guidance on project-level `internal_metadata/` and removed the active `metadata/` path residue.
- Derived the lint backend release version directly from `core/bootstrap.yaml` so direct backend execution cannot silently retain an older hard-coded release.
- Added v7.10.1 read-path regression coverage; numerical models, preprocessing, user execution, workbook interfaces, LaTeX attestation v3 and submission validation behavior remain unchanged.

## Previous release: 7.10.0

- Added a persistent formal LaTeX audit attestation (`latex_audit_report.yaml`) bound to the active source bundle and current `模型论文框架.md`; formal compile delivery can no longer rely on prose-only audit invocation without a machine-readable proof artifact.
- Upgraded compile evidence to v3: `compile_report.yaml` now binds source bundle hash, audit-report hash, compile-profile fingerprint, actual engine/bibliography/sequence, PDF hash and a real compilation log. Missing logs no longer default to `passed`.
- Made `scripts/render_paper.py` the formal production path for audit → profile-bound compile → compile attestation, while keeping template smoke builds explicitly separate from formal delivery evidence.
- Added CUMCM class materialization to the controlled compile path so production compilation does not depend on an undocumented manual copy step.
- Closed `full_workflow` submission loading with `packs/artifact/full_submission.md` plus a `submission_package_validation` gate; `validated_submission_package` is now a gate result rather than a synonym for “ZIP exists”.
- Split package generation into explicit `official` and `reproducibility` semantics. Official packages require current verified competition `edition_rules.submission_files`; unverified edition rules block automatic official packaging instead of falling back to historical guesses.
- Added deterministic `submission_manifest.yaml` provenance with per-file SHA-256 and `scripts/validate_submission_package.py` checks against the archive, current project files and current compiled PDF. Stale PDFs/code/workbooks cannot pass merely because filenames match.
- Preserved legacy no-`--mode` packaging as reproducibility behavior and legacy v2 compile reports as read-compatible only; current formal delivery requires regenerated v3 attestations.
- Numerical models, preprocessing semantics, Workbook Schema, Python/MATLAB responsibilities, full-fidelity user execution, semantic-governance 1.0.0, framework `v0.8-project-memory` and the per-question five-file interface remain unchanged.

## Previous release: 7.9.0

- Closed modular-LaTeX runtime dispatch: `audit_latex_project.py` is the public LaTeX audit entrypoint for modular and compatible single-file projects, delegating prose/BibTeX/framework checks to `audit_paper_prose.py`.
- Closed `full_workflow` post-execution Pack loading so Figure, LaTeX and Review Artifact Packs are available after accepted primary/result-analysis workbooks, and added `validated_submission_package` to final workflow outputs.
- Unified the current CUMCM project-template authority on `templates/latex/cumcm/hsk/`; the `cumcmthesis/` directory remains an upstream class/base-template resource rather than the active project template.
- Added source-bundle/PDF freshness verification through deterministic compile reports. `render_paper.py` now writes `compile_report.yaml`; `sync_project.py` recomputes the current active source bundle before LaTeX/submission delivery.
- Added deterministic Paper Fragment `source_file` checks against actual files and the active `main.tex` include graph.
- Added regression coverage for the integration gaps above. Numerical modeling, preprocessing, Workbook Schema, Python/MATLAB ownership, user full-fidelity execution, framework `v0.8-project-memory`, semantic-governance 1.0.0 and the per-question five-file interface are unchanged.

## Previous release: 7.8.1

- Closed the v7.8 Algorithm Trace delivery loop: final review and submission now explicitly consume the writing-reasoning Authority and the algorithm-flow Pack, and review checks the declared `not_needed / stepwise / pseudocode` mode against the current model, Python implementation and workbook evidence.
- Added deterministic runtime validation for current Algorithm Trace records in `scripts/validate_model_paper_framework.py`. `stepwise/pseudocode` questions must link a current Algorithm ID with complete structural fields and matching mode; `not_needed` questions must not retain stale decorative links. Solved-or-later current traces require a Python code anchor.
- Corrected an active submission residue that had accidentally restored a hard “at most four propositions” rule. `0--4` remains only the default body-reading budget; P5+ is allowed after necessity review and recorded justification.
- Closed route-loading omissions so full-paper, LaTeX, DOCX, review and submission paths have the algorithm-flow presentation Pack available when Algorithm Trace must be rendered or audited. Review/submission routes now explicitly load `core/writing_reasoning_contract.yaml` instead of relying on a second-hop textual reference.
- Fixed framework validation so the `analyzed` subproblem status is treated as a solved-or-later state for current result-summary checks.
- Numerical modeling, preprocessing, Workbook Schema, semantic-governance 1.0.0, Python/MATLAB ownership, user full-fidelity execution, framework `v0.8-project-memory`, project-state schema and the per-question five-file interface remain unchanged.

## Previous release: 7.8.0

- Added adaptive `Algorithm Trace` governance to close the chain from current model structure / formulas / propositions / constraints through paper algorithm presentation to the real Python implementation and accepted workbook result or validation evidence.
- Added three algorithm-presentation modes: `not_needed / stepwise / pseudocode`. Direct or one-shot problems no longer receive decorative algorithm boxes; multi-stage mathematical pipelines use stepwise presentation, while material loops, branches, screening, repair, search and termination logic can use structured pseudocode.
- Added the on-demand `packs/artifact/algorithm_flow.md` Pack with two paper styles: control-flow pseudocode and staged mathematical solution steps. The Pack explicitly forbids treating Python source code, DataFrame operations, file paths, logging, exception handling or parallel plumbing as paper pseudocode.
- Connected proposition/formula/constraint anchors to Algorithm Trace so a proved dimension reduction, candidate restriction, feasibility property, threshold or stopping condition can be shown at the exact algorithm step it changes instead of remaining detached from computation.
- Extended `模型论文框架.md` without a framework-version migration: `v0.8-project-memory` now stores only lightweight per-question algorithm-presentation choices and current Algorithm Trace records; no new mandatory `project_state` field or workflow stage was introduced.
- Added a precise paper-algorithm route (`算法流程 / 伪代码 / 论文算法 / 算法步骤 / Algorithm 1 / 求解流程表`) without overloading the existing generic code/solver route for plain “算法”.
- Reused the existing `semantic_change_categories=algorithm` stale mechanism for substantive algorithm changes; pure layout changes such as line numbers, indentation or wrapping do not trigger numerical recomputation.
- Numerical modeling, conditional preprocessing, Workbook Schema, Python/MATLAB ownership, full-fidelity user execution, semantic-governance 1.0.0 and the per-question five-file interface remain unchanged.

## Previous release: 7.7.0

- Added `Terminology Registry` governance for natural-language technical terms. Current projects can register a canonical term, allowed/discouraged aliases, confusable terms, units/dimensions, linked symbols and scope; machines only check declared collisions/drift and never infer unseen synonymy from string similarity.
- Added a scoring-aware `Numeric Style Contract` and per-project `Numeric Profile` for units, percentages versus percentage points, scientific notation, mean ± standard deviation, confidence intervals, coordinates, optimization variables and precision consistency.
- Corrected the result-display policy so **core answer precision follows prompt/official/judging requirements rather than cosmetic brevity**. When late decimal digits can affect scoring and no more specific rule exists, high-precision result presentation normally retains 6--7 decimal places in the abstract, direct body answers and key result tables; the Skill no longer treats “3--4 decimals in the abstract” as a generic quality target.
- Added `Title Claim Gate` closure from selected title to core questions, substantive model/algorithm use, result evidence, abstract contribution and keywords, reducing title over-packaging.
- Refactored AI Cleanup into `Integrity / Evidence / Style & Necessity / Optional machine diagnostics`, formalizing “Skill defines principles; scripts enumerate reliable checks” instead of growing a numbered checklist indefinitely.
- Extended `scripts/audit_paper_prose.py` conservatively with unresolved-reference blocking, unused-label/equation warnings, figure/table first-reference distance, caption position/length, abstract figure/table/display-math checks, keyword count and optional `--framework` checks for declared terminology/numeric-profile drift. The audit still does not infer mathematical correctness, theorem applicability, terminology equivalence, physical/statistical accuracy or citation semantics.
- Upgraded `模型论文框架.md` to `v0.8-project-memory` with Terminology Registry, Numeric Profile, Title Claim Gate, analysis-evidence disposition and Paper Fragment Dependency Map while keeping it project memory rather than a second writing manual.
- Added `support / modify / reject` result-analysis evidence disposition. Every sensitivity, robustness, out-of-sample, stress or multi-method result can be tied to a target claim and required action; rejecting a core answer triggers redo/redesign, while rejecting an auxiliary evaluation claim may be handled by explicit removal/rewrite.
- Added local paper-fragment stale propagation for v0.8 projects. A Q3 semantic/result change only invalidates paper fragments that actually depend on Q3 (for example Q3 prose, figures, abstract claim, evaluation sentence or Title Claim); unrelated background/Q1/Q2 remain current. v0.7 and earlier whole-framework stale semantics remain read-compatible.
- Added `Paragraph Necessity Test`: if deleting a paragraph loses no problem requirement, mechanism, mathematical relation, solver basis, result evidence or necessary boundary, it should be removed, merged or moved to an appendix. Machine heuristics may warn but cannot automatically delete prose.
- Numerical modeling, conditional preprocessing semantics, workbook Schema, Python/MATLAB ownership, full-fidelity user execution and the per-question five-file interface remain unchanged.

## Previous release: 7.6.0

- Consolidated writing governance around two authorities: `core/writing_reasoning_contract.yaml` for cross-competition reasoning/evidence policy and `modules/05_writing/latex.md` for prose/section structure. `ai_cleanup.md`, DOCX/review modules, Artifact Packs and checklists now consume these authorities instead of maintaining parallel rule sets.
- Added `Hard / Default / Recommendation` governance. Deterministic fact/math/reproducibility failures block delivery; default competition structures require review only when deviated from; experience-based style advice is warning-only.
- Reclassified the previous hard proposition cap into a default `0--4` body-reading budget. P5+ is allowed when the extra propositions cannot reasonably be merged or moved to an appendix and the project records a justification. Internal proposition IDs now support `P1, P2, ...` rather than only P1--P4.
- Removed the mechanical “strengths must outnumber weaknesses” rule. Model evaluation now checks evidence, affected result/boundary and actual model-specific limitations rather than a count inequality.
- Replaced the mandatory named `核心模型汇总` subsection with adaptive `required / inline / not_applicable` states. Complex multi-equation/constraint models still require a dedicated recoverable final model, while simple analytic/direct-readout questions may close inline.
- Slimmed `templates/model/model_paper_framework.md` into project memory rather than a second writing manual. It keeps current problem/data/model facts, writing choices, Formula Trace, numerical-parameter evidence, proposition plan, Citation Evidence, result summaries and code/workbook/MATLAB/paper mappings.
- Added structured Formula Trace fields to the framework while preserving the semantic boundary: tools can verify IDs/sources/dependencies/destinations/anchors exist, but they do not infer mathematical correctness from regex.
- Added Citation Evidence governance for external empirical parameters, external data/domain facts, nontrivial theorems, material method origins and prior-research comparisons. Own derivations and workbook results remain grounded in the current model/evidence chain rather than external citations.
- Extended `scripts/audit_paper_prose.py` to `blocking / review_required / warning`, with deterministic BibTeX checks for missing/duplicate keys and warning-only checks for unused entries and `\nocite{*}`. The audit explicitly does not infer citation semantic support, theorem applicability, source quality or mathematical correctness.
- Updated `core/project_state.schema.yaml`, project-state/framework validators, output contract and regression tests so proposition budget exceptions and adaptive writing states are machine-checkable without restoring old hard limits.
- Numerical modeling, conditional preprocessing semantics, workbook Schema, Python/MATLAB ownership, user full-fidelity execution and the per-question five-file interface are intentionally unchanged.

## Previous release: 7.5.2

- Added identical non-authoritative runtime-entry contract blocks to root and packaged Skill entrypoints so both delegate to `core/bootstrap.yaml` → global policy → resolver → route-specific authorities.
- Added parity lint/regression coverage for entrypoint semantics, plugin discovery, authority pointers and legacy/V622 isolation.
- Removed unnecessary current-version coupling from stable utility/archive documents. Numerical and writing-reasoning behavior remained that of v7.5.0/v7.5.1.

## Previous release: 7.5.1

- Slimmed `core/bootstrap.yaml` to a true startup index containing authority pointers and invariants rather than duplicated domain rules.
- Made resolver taxonomy loading lazy and route-specific while preserving all v7.5.0 reasoning capability.
- Added anti-regression coverage for startup/read-budget and route isolation.

## Previous release: 7.5.0

- Added cross-competition `Source → Derivation → Destination` formula reasoning.
- Added adaptive shared foundations and authentic cross-question progression.
- Added structure-before-algorithm checks, numerical-parameter evidence and numerical + structural multi-method validation.
- Added evidence-driven undergraduate academic prose and proposition downstream-consequence requirements.
- Extended prose audit with conservative formula-density, derivation-connector, meta-navigation and numerical-parameter warnings.

## Previous release: 7.4.5

- Consolidated proposition proof presentation around paragraph-first reasoning and numbered steps only for genuinely multi-stage proofs.
- Added the non-destructive final-LaTeX prose/structure audit.
- Added warnings for repetitive contrast, repeated paper-subject paragraph starts and stock phrases, with structural review for major writing-architecture regressions.

## Previous release: 7.4.4

- Reworked Chinese competition restatement to `问题背景 + 问题提出` and strengthened positive-flow prose.
- Moved question answers into local result/evidence closure, removed default fixed small-question conclusions and removed the default standalone Chinese CUMCM conclusion chapter.
- Strengthened explicit figure/table references and natural evidence interpretation.

## Previous release: 7.4.3

- Reworked question-by-question problem analysis, separate assumptions/symbols, readable notation and model-evaluation structure.
- Introduced the dedicated core-model-summary pattern for complex questions and strengthened proposition/table/figure presentation.
- Added a plainer evidence-driven undergraduate rewrite pass.

## Previous release: 7.4.2

- Added dynamic Figure Evidence hierarchy/layout selection and a high-contrast scientific palette policy while preserving white-background, clear-axis and stable-semantic requirements.

## Previous release: 7.4.1

- Hardened active/compatibility-path separation, repository-reference linting and route smoke tests.
- Removed stale fixed assumption quotas and repaired v7 taxonomy/template version drift.

## Previous release: 7.4.0

- Distilled cross-paper evidence architecture from the user-supplied 2024 CUMCM showcase set: title/abstract discipline, object-restoration figures, local assumption/evidence placement, validation/evaluation separation and minimal algorithm exposition.

## Earlier releases

Earlier 7.3.x, 7.2.x, 7.1.x, 7.0.x and 6.x release details remain available in Git history and `legacy/` where applicable. Active execution never depends on archived release notes.
