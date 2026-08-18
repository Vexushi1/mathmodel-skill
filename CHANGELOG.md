# Changelog

## Current release: 7.7.0

- Added project-level `Terminology Registry` governance for canonical terms, allowed aliases, discouraged aliases and confusable terms. Natural-language terminology is now treated as model semantics rather than free synonym variation; machine checks remain conservative and do not infer synonymy from word similarity.
- Added a high-precision `Numeric Profile`. Verified prompt/official/scoring precision takes precedence; when no more specific requirement exists, scoring-critical continuous results such as optimum values, times, coordinates, probabilities, errors and thresholds default to 6--7 decimal places in the abstract and body. Abstract brevity may reduce the number of secondary values, but not the necessary precision of retained decisive answers.
- Added `Title Claim Gate` so research objects, main methods, mechanisms and contribution claims in the selected title must connect to core questions, substantive model/algorithm use, result evidence, abstract text and keywords.
- Added optional local paper-fragment dependency state. Q-level semantic changes can mark only explicitly dependent model/result/figure, abstract, evaluation and title fragments stale instead of invalidating unrelated background or independent questions. `paper_framework.sync_status` now means the framework mirrors machine state; it is no longer an alias for every paper fragment being current.
- Added result-analysis `support / modify / reject` dispositions with explicit target claims and required actions. Rejecting a peripheral claim does not force a whole-question rerun; rejecting a core answer, feasibility result, main optimum or model structure does require `redo_required` and dependency-aware rollback.
- Added `Paragraph Necessity Test` as a writing recommendation: paragraphs without a problem, mechanism, mathematical, solver, evidence, boundary or closure role should be deleted, merged or moved to an appendix. Machine audit may only warn; it never auto-deletes prose.
- Refactored `modules/05_writing/ai_cleanup.md` into Integrity, Evidence, Style & Necessity and Optional Machine Diagnostics layers. The Skill keeps principles while `scripts/audit_paper_prose.py` carries deterministic and heuristic enumeration.
- Extended prose/structure audit with missing `\ref` targets, unused labels/equation numbers, figure/table reference distance, figure/table caption placement, long captions, abstract float/display-formula checks, keyword-count checks, registered terminology drift and project-declared numeric-precision checks. It still does not infer mathematical correctness, unregistered synonymy, physical-unit semantics or citation support from regex.
- Updated project-memory template to `v0.8-project-memory` and semantic-governance write version to `1.1.0`; v0.7/1.0.0 projects remain read-compatible and migrate when they re-enter current writing/review work.
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
- Extended `scripts/audit_paper_prose.py` to `blocking / review_required / warning`, with deterministic BibTeX checks for missing/duplicate keys and warning-only checks for unused entries and `\\nocite{*}`. The audit explicitly does not infer citation semantic support, theorem applicability, source quality or mathematical correctness.
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