# v8.7.0 Per-Question Writing Capability Preflight — Evaluation

> Status: **pre-release implementation evaluation**.  This file records fixed behavioral trials and regression evidence for the approved v8.7.0 scope.  It is not a new writing Authority and must not override `core/writing_reasoning_contract.yaml`, `core/writing_runtime_contract.yaml`, `modules/05_writing/paper_writing_protocol.md`, or the current project framework.

## 1. Evaluation target

v8.7.0 is accepted only if a question writer can discover and activate the capabilities already required by current project state **before** writing the question body, while keeping the compact runtime closed for capabilities that are not needed.

The evaluation therefore checks four coupled behaviors:

1. `project state -> capability activation` works without repeated user keywords;
2. Formula Roles preserve necessary bridge equations without creating formula dumps;
3. Core Model Summary / Proposition / Algorithm remain adaptive rather than mandatory;
4. the existing v8.5/v8.6/v8.6.1 writing and evidence boundaries remain intact.

## 2. Implemented surface under test

Current implementation adds or integrates:

- `core/writing_runtime_contract.yaml#per_question_writing_capability_preflight`;
- explicit `current_question_evidence_bundle` composition;
- `adaptive_core_model_summary` as an ordinary compact writing capability;
- state-driven Proposition / Proof activation;
- state-driven `not_needed / stepwise / pseudocode` Algorithm activation;
- Formula Role Taxonomy: `final_model_relation / key_bridge_relation / supporting_derivation / routine_algebra`;
- current Output Contract pointers for Formula Roles, Core Model Summary, and question preflight;
- `模型论文框架.md` project-memory fields for per-question preflight and Formula Roles;
- AI Cleanup protection for final/bridge relations and activated proposition/algorithm content;
- Review Delivery capability-activation checks;
- behavioral fixtures and resolver-level tests.

## 3. Fixed writing trials

These are fixed **paper-surface behavior trials**, not numerical model benchmarks.  The question state is fixed first; then the expected writing behavior is checked against Runtime + Reasoning + Protocol + Cleanup + Review.  The purpose is to detect over-activation, silent omission, or formula over-compression.

### Trial A — simple analytic question

State:

```text
Formula Roles: one final_model_relation
Core Model Summary: inline
Proposition / Proof: not_assessed
Algorithm: not_needed
```

Expected paper surface:

- keep the final analytic relation in adjacent prose;
- no forced “核心模型汇总” subsection;
- no proposition block;
- no algorithm steps or pseudocode;
- full reasoning Authority and Algorithm/Proposition Packs are not eagerly preloaded.

Result: **PASS by contract + fixture**.  `summary_inline_simple_analytic` activates only adaptive summary semantics and keeps the optional deep Packs closed.

### Trial B — complex optimization model

State:

```text
Formula Roles: final_model_relation + key_bridge_relation
Core Model Summary: required
Proposition / Proof: not_assessed
Algorithm: not_needed
```

Expected paper surface:

- final objective / constraints remain recoverable in the model recap;
- a bridge relation is retained when deleting it would break source, boundary, reduction, or solver-precondition recovery;
- supporting derivation and routine algebra are not copied into the recap by default;
- no algorithm block is manufactured merely because the model is complex.

Result: **PASS by contract + fixture**.  `summary_required_complex_optimization` and `bridge_relation_preserved_without_formula_dump` cover the activation and formula-role split.

### Trial C — geometric / mechanism predicate with bridge equations

State:

```text
F_bridge: key_bridge_relation
F_final: final_model_relation
F_support: supporting_derivation
summary: required or inline according to final recoverability
```

Expected paper surface:

- the geometry-to-predicate bridge remains near the derivation;
- the final decision predicate remains visible to the solver / result chain;
- `F_support` may be compressed;
- the summary includes the bridge only if otherwise the final predicate loses recoverable origin;
- Cleanup cannot delete `F_bridge` merely because it is not the final solver equation.

Result: **PASS by Authority/Protocol/Cleanup assertions**.

### Trial D — monotonicity / feasibility property used by solving

State A:

```text
proposition = candidate
```

Expected behavior: trigger semantic necessity review only; do **not** auto-create a proposition or preload the full proposition Pack.

State B:

```text
proposition = planned/current
```

Expected behavior: activate full reasoning Authority + `packs/artifact/proposition_proof.md`, then preserve the property’s downstream effect on candidate region, reduction, boundary, or solver precondition.

Result: **PASS by fixture + Runtime assertions**.  Candidate and planned/current paths are explicitly different.

### Trial E — black-box optimization with real pseudocode need

State:

```text
Algorithm Trace: current
presentation_mode: pseudocode
```

Expected paper surface:

- activate full reasoning Authority;
- activate `packs/artifact/algorithm_flow.md`;
- activate the LaTeX algorithm-environment adapter;
- write mathematical state / objective / constraint handling / branching / termination / output mapping rather than compressed Python source;
- `stepwise` uses the algorithm Pack but does not itself require the LaTeX algorithm environment;
- `not_needed` leaves both closed.

Result: **PASS by fixture + mode-separation assertions**.

### Trial F — cross-question inheritance

State:

```text
Q2 inherits Q1 model
Q2 adds only an incremental bridge/final relation
summary = inline
algorithm = not_needed
```

Expected paper surface:

- do not copy the complete Q1 model into Q2;
- preserve the new Q2 bridge/final relation and explain the increment;
- do not add proposition or algorithm content without state evidence;
- if a later question fully inherits the prior model and adds no new core relation, `adaptive_core_model_summary.not_applicable_when` permits the recap to stay off.

Result: **PASS by fixture + cross-question progression assertions**.

## 4. Negative / fail-closed trials

### Missing state

`summary / proposition / algorithm = missing` and no Formula Roles must yield `needs_adjudication`; it cannot silently become `not_applicable / not_needed`.

Status: **PASS**.

### Stale proposition

A stale proposition cannot surface as current prose.  It activates review and the proposition resources needed to resolve the stale state.

Status: **PASS**.

### Explicit user request compatibility

State-driven activation is additive.  An explicit request to create/review a proof still enters the proposition/proof conditional branch even when the current project state was previously `not_assessed`.

Status: **PASS**.

## 5. Resolver / compact-runtime projection

The resolver test executes:

```text
python scripts/resolve_runtime.py latex --competition CUMCM
```

and verifies that:

- `writing_runtime.execution_mode = template_first_progressive_authoring`;
- the projected `question_model_solution_result_validation` stage contains `before_write_preflight`;
- the preflight pointer is `core/writing_runtime_contract.yaml#per_question_writing_capability_preflight`;
- `full_reasoning_authority_preloaded = false` for the ordinary CUMCM LaTeX compact route.

Result: **PASS in current unit-test runs**.

## 6. Regression boundaries

The implementation intentionally changes writing runtime / reasoning / protocol / cleanup / review and the project-memory template.  It does **not** change the semantics of:

- Model Approval;
- Primary Numerical Verification / PQS;
- 03A / 03B separation;
- user execution;
- workbook schema;
- project-state core schema;
- result-analysis ownership;
- figure ownership / draw.io mechanism semantics;
- formal LaTeX compilation and production attestation.

Protected drift tests continue pinning those unrelated Authorities.  The four v8.7 writing Authorities have updated protected snapshots so the protection test describes intentional release scope rather than treating approved writing changes as unrelated drift.

## 7. Compatibility checks

Current assertions explicitly preserve:

- v8.5 Author Reasoning Voice: no authorship scoring, no pronoun quota, no fabricated team history;
- v8.6 Model Construction & Solution Rationale: model gap, local applicability, reduction provenance, solver preconditions, parameter evidence, adaptive subsection separation;
- v8.6.1 active consistency / Template-First progressive authoring;
- simple-problem anti-bloat;
- Model / Solver / Validator separation;
- claim-strength and proof/evidence boundaries.

## 8. CI evidence before release sync

During implementation, an earlier v8.7 candidate reached green Python test jobs and green static / LaTeX / production-attestation jobs; the only transient failure on a user commit was the generated-file freshness gate while the normal metadata workflow was creating its follow-up metadata commit.  The branch then moved to the generated-metadata commit, as designed.

After expanded activation fixtures and resolver tests, current Python jobs are again passing on the user commit while generated metadata is refreshed by the normal workflow.  **This section is intentionally not the final release attestation.**  A stable-head full matrix must still be run after release-carrier sync.

## 9. Known limitations / deliberate boundaries

1. Preflight dispatch does not decide mathematical truth.  It cannot prove that a bridge relation is genuinely necessary, that a proposition is correct, or that a solver precondition is satisfied.
2. Candidate proposition signals trigger semantic review, not automatic proposition creation.
3. `required` summary means semantic recoverability, not a mandatory same-named subsection.
4. Formula Role classification is project/model reasoning work; machine checks may validate declared enums and anchors but cannot infer roles from regex or equation position.
5. Other competitions without the dedicated CUMCM Template Manifest continue using the full-Authority fallback; v8.7 does not silently project the CUMCM compact runtime onto them.

## 10. Pre-release verdict

Current implementation satisfies the intended **capability discovery + state-driven activation** architecture and the fixed behavior trials above.  Remaining release work is procedural rather than a change of semantic design:

- synchronize version carriers from 8.6.1 to 8.7.0;
- refresh generated metadata;
- run one stable-head full CI matrix;
- record the final candidate SHA and CI run in this evaluation;
- update the PR from implementation status to review-ready status.

Until those steps are complete, PR #114 remains Draft and `main` remains unchanged.
