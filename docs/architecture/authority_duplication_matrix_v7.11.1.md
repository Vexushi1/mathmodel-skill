# Authority Duplication Matrix v7.11.1

## Scope

Phase 1 focuses on authority convergence. This document records the pre-migration duplication points, their target authority, and the acceptance criteria used to verify the post-migration state. Generated repository metadata is intentionally refreshed only after the final source state is committed, so temporary migration helpers must never remain in the active index or manifest.

| Field / Concept | Current Location | Duplication Risk | Target Authority | Migration Strategy |
|---|---|---|---|---|
| Workflow routing rules | core/workflow_router.yaml | Low | core/workflow_router.yaml | Keep as router authority |
| Workflow order | workflow_router execution_contract + module_manifest workflow_order | Medium | core/workflow_router.yaml | Manifest becomes derived reference |
| Module graph | module_manifest modules section | Low | core/module_manifest.yaml | Keep module ownership here; resolver must not redefine |
| workflow_profiles | core/module_manifest.yaml | Medium | core/workflow_router.yaml | Remove semantic profile copies; retain only a lightweight non-runtime alias map |
| PRIMARY_CODE_GATES | scripts/resolve_workflow.py | High | core/workflow_router.yaml | Move declaration into YAML |
| ANALYSIS_CODE_GATES | scripts/resolve_workflow.py | High | core/workflow_router.yaml | Move declaration into YAML |
| SEMANTIC_SYNC_GATES | scripts/resolve_workflow.py | High | core/workflow_router.yaml | Move declaration into YAML |
| SUBMISSION_GATES | scripts/resolve_workflow.py | High | core/workflow_router.yaml | Move declaration into YAML |
| MODEL_APPROVAL_OUTPUTS | scripts/resolve_workflow.py | High | Router/manifest contract layer | Resolver reads declaration |
| PREPROCESSING_OUTPUTS | scripts/resolve_workflow.py | High | Router/manifest contract layer | Resolver reads declaration |
| FINAL_WORKFLOW_OUTPUTS | scripts/resolve_workflow.py | High | Router/manifest contract layer | Resolver reads declaration |
| MODEL_APPROVAL_REQUIRED_INTENTS | scripts/resolve_workflow.py | High | core/workflow_router.yaml | Convert to declarative intent policy |
| Resolver execution algorithm | scripts/resolve_workflow.py | Low | scripts/resolve_workflow.py | Keep implementation only |

## Boundary Rules

The resolver may:

- load YAML authority;
- transform declarations into execution plans;
- validate consistency.

The resolver may not:

- define workflow policy constants;
- define gate sets;
- define output ownership;
- define module graph semantics.

## Phase 1 Acceptance Criteria

- Router contains policy declarations.
- Manifest workflow_profiles are explicitly compatibility-only.
- Resolver contains no embedded *_GATES, *_OUTPUTS, *_REQUIRED_INTENTS policy constants.
- Invariant tests prevent future authority duplication.
