# Changelog

## Current release: 8.1.1

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
- Added **Subsection Granularity** governance focused only on second-level subsections inside question chapters. About 3–4 major units is a default reading structure, not a hard count; top-level chapter count is not restricted, and count alone cannot decide section quality.
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

## Earlier release: 7.9.0

- Closed modular-LaTeX runtime dispatch: `audit_latex_project.py` is now the public LaTeX audit entrypoint for modular and compatible single-file projects, delegating prose/BibTeX/framework checks to `audit_paper_prose.py`.
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
- Numerical modeling, conditional preprocessing, workbook Schema, Python/MATLAB ownership, full-fidelity user execution and the per-question five-file interface remain unchanged.

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