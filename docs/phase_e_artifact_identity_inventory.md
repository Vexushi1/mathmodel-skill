# Phase E Artifact Identity Reference Inventory

Baseline: `main@5ec9974bfcf87075d509da9fcced69541013877d`
Scope: Phase E additive naming migration only. No Phase F transactional writes, Phase G resolver policy, Phase H mechanical split, or Phase I compatibility deletion.

| Field | Active readers before E | Active writers before E | Proven semantic meaning | Phase E action |
|---|---|---|---|---|
| `artifact_hashes.model` | `validate_project_state.py`, `sync_project.py` stale comparison/fixtures | `sync_project.py::_snapshot_question()` | SHA-256 of the primary Python implementation, not mathematical model semantics | Read as legacy alias only when `primary_code` is absent; block conflicting dual presence; stop all new writes |
| `artifact_hashes.primary_code` | none before E | none before E | Canonical primary implementation identity | Add to Schema; canonical write/read key in sync and delivery flows |
| `artifact_hashes.analysis_code` | none before E | none before E | Canonical result-analysis implementation identity | Add to Schema; canonical write/read key in sync and analysis delivery flows |
| `primary_code_sha256` | `validate_user_execution.py`, `sync_project.py`, delivery/runtime tests | `validate_code_delivery.py` | Exact delivered primary Python hash used by workbook receipt binding | Keep; it is already unambiguous stage-specific delivery provenance and must equal canonical `artifact_hashes.primary_code` on new writes |
| `analysis_code_sha256` | `validate_user_execution.py`, `sync_project.py`, delivery/runtime tests | `validate_code_delivery.py` | Exact delivered analysis Python hash used by workbook receipt binding | Keep; bind new writes to canonical `artifact_hashes.analysis_code` |
| `model_hash` | `validate_project_state.py` only | no active writer found | Legacy fallback for primary implementation hash | Keep read-only compatibility; map to `primary_code` only when canonical artifact hash is absent; deletion deferred to Phase I |
| `validated_model_hash` | `validate_project_state.py` only | no active writer found | Legacy validated fallback for primary implementation hash | Keep read-only compatibility; map to validated `primary_code`; deletion deferred to Phase I |
| `semantic_identity_hash` | semantic governance, Model Approval, Runtime Assurance | semantic governance | Mathematical semantic identity from the Framework SIB | Unchanged; explicitly separate from implementation identity |
| `semantic_hash` | legacy semantic compatibility readers | legacy migration path only | Legacy Markdown semantic-scope provenance | Unchanged by E; Phase C/Phase I compatibility policy continues to govern it |

## Migration invariants

1. `artifact_hashes.model -> artifact_hashes.primary_code` is mechanical compatibility mapping only.
2. `model` and `primary_code` may be read together only when their values are equal; disagreement is blocking.
3. New writes never persist `artifact_hashes.model` or the legacy stale layer `model`.
4. Primary-code freshness never substitutes for `semantic_identity_hash` and never invalidates Human Model Approval by itself.
5. Analysis-code changes do not invalidate the accepted primary result.
6. `model_hash / validated_model_hash` are not deleted in Phase E because the repository audit proves they still participate in legacy reads.
