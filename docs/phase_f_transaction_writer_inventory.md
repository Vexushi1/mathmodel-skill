# Phase F Project-State Writer Inventory

Baseline: `main@0791432d9ab65c86b81d106274ed04731c510fd4`

This record scopes Phase F from `docs/semantic_state_runtime_refactor_plan.md`. It distinguishes repository control-plane writers from distributed task-code templates so transaction enforcement does not silently break the self-contained user-execution contract.

## Control-plane writers

| Writer | Current mutation surface before Phase F | Phase F action |
|---|---|---|
| `scripts/sync_project.py` | `模型论文框架.md` → `state/project_state.yaml` → `sync_report.yaml` direct sequential writes | One recoverable `framework → state → report` transaction; staged hash/self-check before commit |
| `scripts/validate_semantic_governance.py --write` | Direct `state/project_state.yaml` write | Shared generation-checked state transaction |
| `scripts/validate_code_delivery.py` | Direct state write for preprocessing/primary/analysis delivery | Shared generation-checked state transaction |
| `scripts/validate_user_execution.py --write` | Mutates all selected receipts in memory, then one direct state write | Keep one in-memory mutation batch, commit through shared transaction helper |

All four control-plane writers must recover an existing prepared journal before loading mutable state and must reject a stale writer if the live generation changes before commit.

## Distributed template writer

`templates/code/hsk_pipeline/main_pipeline.py` contains a local `_write_state()` used by generated/user-executed task code. It is not a repository control-plane CLI and is intentionally self-contained: the template explicitly supports running as an independent script and cannot assume that the skill repository's `scripts/project_transaction.py` is present inside the user's modeling project.

Phase F therefore does **not** make this distributed template import the repository transaction helper. The authoritative acceptance path remains `validate_user_execution.py`; control-plane writes are transaction-protected. A future template packaging change may carry a project-runtime transaction library explicitly, but that is not introduced implicitly in Phase F.

## Test-fixture writes

Direct `write_text(yaml.safe_dump(...))` calls under `tests/` are fixture construction and fault injection, not production state writers. They remain intentionally direct so tests can construct legacy generation-less projects and simulate concurrent/partial state.

## Generation compatibility

- Missing `project.state_generation` is read as generation `0` for v8 compatibility.
- New transactional writes persist `expected_generation + 1`.
- The Schema exposes `state_generation` additively and does not require it for legacy reads.
- A prepared journal may roll forward only when live generation is either the journal base generation or target generation; any third generation blocks recovery.

## Journal and recovery direction

Phase F uses deterministic roll-forward recovery. The journal records each target's old/new SHA-256, staged path, backup path, and base/target generation. On recovery, every live target must match either its recorded old hash or new hash. Unknown content is never overwritten or guessed.

For `sync_project --write`, replacement order is:

1. `模型论文框架.md`
2. `state/project_state.yaml`
3. `sync_report.yaml`

This order is recoverable because a crash after either the framework or state replacement leaves the prepared journal and remaining staged files for the next writer to finish safely.
