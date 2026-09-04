# v8.7.0 Per-Question Writing Capability Preflight — Evaluation

> Status: **release-candidate semantic evaluation complete; pre-merge**. This file records fixed behavioral trials, regression evidence and the first stable-head release-candidate CI for the approved v8.7.0 scope. It is not a new writing Authority and must not override `core/writing_reasoning_contract.yaml`, `core/writing_runtime_contract.yaml`, `modules/05_writing/paper_writing_protocol.md`, or the current project framework.

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

These are fixed **paper-surface behavior trials**, not numerical model benchmarks. The question state is fixed first; then the expected writing behavior is checked against Runtime + Reasoning + Protocol + Cleanup + Review. The purpose is to detect over-activation, silent omission, or formula over-compression.

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

Result: **PASS by contract + fixture**. `summary_inline_simple_analytic` activates only adaptive summary semantics and keeps the optional deep Packs closed.

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

Result: **PASS by contract + fixture**. `summary_required_complex_optimization` and `bridge_relation_preserved_without_formula_dump` cover the activation and formula-role split.

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

Result: **PASS by fixture + Runtime assertions**. Candidate and planned/current paths are explicitly different.

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

A stale proposition cannot surface as current prose. It activates review and the proposition resources needed to resolve the stale state.

Status: **PASS**.

### Explicit user request compatibility

State-driven activation is additive. An explicit request to create/review a proof still enters the proposition/proof conditional branch even when the current project state was previously `not_assessed`.

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

The implementation intentionally changes writing runtime / reasoning / protocol / cleanup / review and the project-memory template. It does **not** change the semantics of:

- Model Approval;
- Primary Numerical Verification / PQS;
- 03A / 03B separation;
- user execution;
- workbook schema;
- project-state core schema;
- result-analysis ownership;
- figure ownership / draw.io mechanism semantics;
- formal LaTeX compilation and production attestation.

Protected drift tests continue pinning those unrelated Authorities. The v8.7 writing Authorities have updated protected snapshots only where the approved writing scope changed; unrelated numerical, model-approval, workbook, project-state, plotting and delivery snapshots remain pinned.

## 7. Compatibility checks

Current assertions explicitly preserve:

- v8.5 Author Reasoning Voice: no authorship scoring, no pronoun quota, no fabricated team history;
- v8.6 Model Construction & Solution Rationale: model gap, local applicability, reduction provenance, solver preconditions, parameter evidence, adaptive subsection separation;
- v8.6.1 active consistency / Template-First progressive authoring;
- simple-problem anti-bloat;
- Model / Solver / Validator separation;
- claim-strength and proof/evidence boundaries.

## 8. Release-carrier sync and stable-head CI evidence

Release carriers were synchronized from `8.6.1` to `8.7.0` only after the semantic implementation and expanded behavior fixtures were already passing. The sync covers the active bootstrap/plugin/Skill/README/CHANGELOG/core-version carriers, compact writing runtime and current health assertions; root and packaged `SKILL.md` remain byte-identical. Historical v8.6.1 release records were not mass-rewritten.

The temporary one-shot release-sync helper and temporary workflow hook were removed before candidate validation. The normal generated-metadata workflow then refreshed the active indexes/manifest, producing metadata head:

```text
metadata_head = 60cdb10c9de24cbe38472bf81f7a253d8f62b50b
```

An empty user-authored commit with the **same tree** was then created specifically to validate a stable tree whose generated metadata was already current:

```text
release_candidate_validation_head = a47dd7c553b9becd1bcfd5e3d5ccbb687d0a8761
HSK Skill CI run = #2495
run_id = 33895569951
result = success
```

All 11 jobs passed on that stable candidate tree:

- Generated file contract ✅
- Static contract lint ✅
- Python 3.10 ✅
- Python 3.11 ✅
- Python 3.12 ✅
- Python 3.13 ✅
- Python 3.14 ✅
- LaTeX CUMCM ✅
- LaTeX MCM-ICM ✅
- LaTeX Diangong ✅
- Production LaTeX attestation ✅

This is **pre-merge release-candidate evidence**, not a post-merge release attestation. The evaluation-document closure in this commit is documentation-only; after its normal generated-metadata refresh, one final stable-head matrix should be used as the PR-ready check. Exact final PR head/run can be recorded in the PR body without turning this evaluation file into a moving live-state pointer.

## 9. Known limitations / deliberate boundaries

1. Preflight dispatch does not decide mathematical truth. It cannot prove that a bridge relation is genuinely necessary, that a proposition is correct, or that a solver precondition is satisfied.
2. Candidate proposition signals trigger semantic review, not automatic proposition creation.
3. `required` summary means semantic recoverability, not a mandatory same-named subsection.
4. Formula Role classification is project/model reasoning work; machine checks may validate declared enums and anchors but cannot infer roles from regex or equation position.
5. Other competitions without the dedicated CUMCM Template Manifest continue using the full-Authority fallback; v8.7 does not silently project the CUMCM compact runtime onto them.

## 10. Release-candidate verdict

The semantic implementation satisfies the intended **capability discovery + state-driven activation** architecture, the six fixed writing-surface trials and the fail-closed cases. Release carriers are synchronized to `8.7.0`, temporary implementation helpers are removed, generated metadata has been refreshed, and a stable candidate tree has passed the complete 11-job CI matrix.

Remaining pre-merge work is limited to repository-state closure:

- refresh generated metadata for this evaluation-document update;
- run one final stable-head full CI matrix on the resulting tree;
- update PR #114 with the final candidate head/run and mark it review-ready.

`main` remains unchanged. This evaluation does not authorize merge; merge remains a separate explicit user decision.
