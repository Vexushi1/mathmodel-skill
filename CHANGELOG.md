# Changelog

## Current release: 7.16.0

- Restored and strengthened the paper-writing specification without reviving the legacy full-auto architecture. Existing single-authority governance remains centered on `core/writing_reasoning_contract.yaml`, `modules/05_writing/latex.md`, project memory and accepted workbooks.
- Added explicit **Model / Solver / Validator** role separation so mathematical model identity cannot be replaced by solver names, validation algorithms, software or implementation architecture.
- Added **Model Naming** governance: project-specific model names remain allowed, but first formal use must expose the standard mathematical model type and the load-bearing problem structure.
- Added **Optimization Model Expression** closure for optimization/scheduling/routing/allocation/control problems: standard model type and real objective → decision variables/objects → objective function and interpretation → constraints by source → adaptive core-model summary → solver/validation.
- Upgraded optimization abstracts so they must communicate what is being optimized; listing decision variables and an algorithm without objective semantics is no longer considered model-information closure.
- Added **Solver Justification** for first use, cross-question reuse, solver changes and alternative-method evidence. Alternative algorithms enter the paper only when actually run and traceable as baseline, alternative or validator with comparable evidence.
- Added **Subsection Granularity** governance focused only on second-level subsections inside question chapters. About 3–4 major units is a default reading structure, not a hard count; top-level chapter count is not restricted, and count alone cannot decide section quality.
- Added five-level **Claim Strength Calibration** (`PROVEN`, `VERIFIED_NUMERIC`, `COMPARATIVE`, `OBSERVED`, `HEURISTIC`) to stop numerical/heuristic evidence from being polished into unsupported proof, global-optimality, universal-comparison or strong-robustness claims. Abstract wording receives the strictest scope review.
- Upgraded `模型论文框架.md` to `v0.9-project-memory` with standard model type, formal model name, Model/Solver/Validator roles, optimization-objective abstract closure, solver evidence roles, subsection planning, and headline claim Evidence Level/Scope.
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