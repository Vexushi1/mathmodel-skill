# Changelog

## Current release: 7.11.0

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
