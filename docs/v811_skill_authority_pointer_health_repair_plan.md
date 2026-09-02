# v8.1.1 Skill Authority Pointer Health Repair Plan

## 1. Purpose

This plan is the implementation context for a single patch release that repairs the active Skill entrypoint after the v8.1.0 health audit.

The audit proved that v8.1.0 Cross-File Chapter Handoff, protected model/numerical semantics, version carriers, generated metadata and the validated content tree are healthy. It also found one pre-existing active-entry defect:

```text
项目工作记忆
→ core/project_memory_contract.yaml
→ 404 / file does not exist
```

The current project-memory template and consumer chain already use:

```text
templates/model/model_paper_framework.md
```

This patch must repair that stale pointer and prevent the same class of active Authority navigation defect from passing CI again. It must not redesign project memory, Cross-File Chapter Handoff, model state or any mathematical workflow.

## 2. Frozen baseline

- Repository: `Vexushi1/mathmodel-skill`
- Baseline branch: `main`
- Baseline commit: `cf46c02a0ac6424d3be34e66952741214551a19e`
- Current Skill version: `8.1.0`
- Target Skill version: `8.1.1`
- Change level: `patch`
- Compatibility: backward compatible
- Open pull requests at freeze: none

## 3. Confirmed defect

Both active Skill entrypoints are byte-identical and both contain the same stale Authority row:

- `SKILL.md`
- `skills/mathmodel-skill/SKILL.md`

Current invalid row:

```markdown
| 项目工作记忆 | `core/project_memory_contract.yaml` |
```

The target file is absent from the repository, active indexes and generated manifest. Direct GitHub content lookup returns 404.

The correct current project-memory source is already declared consistently by:

- `core/module_manifest.yaml#framework_template`
- `core/output_contract.yaml#model_paper_framework.template`
- `core/workflow_router.yaml`
- `core/writing_runtime_contract.yaml#cross_file_chapter_handoff.project_memory`
- `modules/02_model_design.md`
- `README.md`

Correct target:

```text
templates/model/model_paper_framework.md
```

## 4. Root cause

The stale pointer predates v8.1.0. Root/package Skill parity checks only compare the two Skill files with each other. Because both files contain the same invalid path, parity remains green.

The active health suite checks required discovery tokens and release versions but does not validate that repository-relative Authority targets in the Skill navigation table exist. Generated indexes correctly omit the nonexistent file, but no current test treats that disagreement as a failure.

## 5. Authorized repair

### 5.1 Skill entrypoints

Replace the stale project-memory row in both byte-identical Skill entrypoints:

```text
core/project_memory_contract.yaml
→ templates/model/model_paper_framework.md
```

Do not alter the role of project memory, its schema, lifecycle, semantic hash boundary or current Framework contents.

### 5.2 Regression guard

Add a deterministic current-health regression that:

1. extracts repository-relative Markdown-code paths from the active `Authority 导航` table;
2. verifies every target exists in the repository;
3. verifies the root and packaged Skill remain byte-identical;
4. asserts the project-memory row points to `templates/model/model_paper_framework.md`;
5. rejects `core/project_memory_contract.yaml`.

Prefer a small helper in `tests/test_current_skill_health.py`. If the current lint architecture has a clean, low-risk hook, add the same invariant to `scripts/lint_skill_checks.py`; otherwise the unit-matrix regression is the mandatory guard and no large lint refactor is allowed.

### 5.3 Patch release carriers

Publish `8.1.1` as a repair-only patch. Update only current release carriers already governed by the existing health tests:

- `.codex-plugin/plugin.json`
- `CHANGELOG.md`
- `README.md`
- `SKILL.md`
- `skills/mathmodel-skill/SKILL.md`
- `core/bootstrap.yaml`
- `core/hsk_core_policy.md`
- `core/module_manifest.yaml`
- `core/output_contract.yaml`
- `core/workflow_router.yaml`
- `core/writing_runtime_contract.yaml` — version field only
- `config/prose_audit_patterns.yaml`
- current version assertions in affected tests

No blind repository-wide version replacement is allowed. Historical release text must remain historical.

### 5.4 Generated metadata

After all hand-edited files are final, regenerate through the existing generator/workflow only:

- `SKILL_FILE_INDEX.md`
- `TEMPLATE_INDEX.md`
- `HSK_SKILL_FILE_INDEX_V622.md` only if generator output changes it
- `HSK_TEMPLATE_INDEX_V622.md` only if generator output changes it
- `MANIFEST.sha256`

Do not hand-edit generated hashes.

## 6. Explicit non-goals

This patch must not:

- add a new project-memory contract;
- change `v0.8-project-memory`;
- change Framework fields or Chapter Handoff Map;
- change Paper Writing Protocol prose semantics;
- change final-assembly ordering or Template Manifest;
- change Writing Reasoning Authority;
- change semantic revision/hash behavior;
- change Model Approval or Model Challenge;
- change preprocessing, Python/MATLAB ownership or numerical validation;
- change Workbook Schema or Project State Schema;
- change 03A, 03B or Figure Evidence;
- add a new capability, route, artifact type, CLI option or directory;
- treat the missing post-merge push run as a Skill semantic failure;
- bundle CI TeX retry hardening into this pointer repair.

The Production TeX installation flake is recorded as a separate operational improvement and is deliberately excluded to keep this patch single-purpose.

## 7. Protected semantic freeze

The following Git blob SHAs must remain unchanged:

| Protected source | Frozen blob SHA |
|---|---|
| `core/model_approval_contract.yaml` | `7d97255dde9cf780755bab896964e905066bf4b8` |
| `core/numerical_verification_contract.yaml` | `b901923edf38112cbc922f51d1157265fe1931bd` |
| `core/workbook_schema.yaml` | `2422bbfa8cb3fad3b5b04c12de21c954ec8b3723` |
| `core/project_state.schema.yaml` | `fa12de39d7bbdc2e014b2912a186834b941b28d4` |
| `modules/03_solve_validate.md` | `f49480d96e6a491255010868e409b2d64d620f5e` |
| `modules/03_result_analysis.md` | `f43d21dc99d71e6b19baeec7af66cbf334da13a7` |
| `modules/04_figure_evidence.md` | `3a34af07c7c8f58769e28dc22ab3b712481107f7` |
| `templates/latex/cumcm/hsk/template_manifest.yaml` | `32402842ea88c2a4ce3df052f6c01534b357549f` |
| `core/writing_reasoning_contract.yaml` | `adb962b3b764c08f78fdb002b97401adde693856` |

The following v8.1.0 business semantics must remain unchanged, except that `core/writing_runtime_contract.yaml` may receive the release version-field update only:

| v8.1 semantic source | Frozen blob SHA |
|---|---|
| `core/writing_runtime_contract.yaml` | `15542ef7e610283fc9575d42cad4e0a6364dd008` |
| `modules/05_writing/paper_writing_protocol.md` | `5404b1dc891227249644b040c40482bd6065b81a` |
| `modules/06_review_delivery.md` | `7c703a27301634bac6b71fa183b88e8f8048258e` |
| `templates/model/model_paper_framework.md` | `9e4474f58d5e7fc1e0f4171ba528291e41de0155` |

For the Runtime file, compare a version-normalized body or inspect the diff to prove that only `version: 8.1.0 → 8.1.1` changed.

## 8. Expected hand-edited files

Expected active hand edits are limited to:

1. this plan;
2. root/package Skill;
3. current health regression and only the minimum version assertions;
4. existing release carriers;
5. optionally `scripts/lint_skill_checks.py` only for a small path-existence guard.

If active hand-edited scope approaches the 20-file governance threshold, stop and reassess before adding unrelated changes.

## 9. Implementation order

1. Freeze current `main`, open PR state, governance and protected SHAs.
2. Create `fix/v811-skill-authority-pointer-health`.
3. Commit this plan before implementation.
4. Add the failing regression for the stale/nonexistent Authority path.
5. Repair both Skill files and re-establish byte parity.
6. Update explicit 8.1.1 release carriers.
7. Run static and unit validation.
8. Obtain generated metadata from the existing generator/workflow and apply it without manual hash edits.
9. Run full HSK Skill CI.
10. Compare protected files and v8.1 semantic sources against the freeze.
11. Merge only when every required check is green.
12. Perform a post-merge health audit.

## 10. Required tests

Minimum focused regression:

- root/package Skill equality;
- correct project-memory target;
- invalid legacy target absent;
- every active Skill Authority target exists;
- version carriers resolve to 8.1.1;
- Framework schema remains `v0.8-project-memory`;
- Chapter Handoff remains writing-only and outside model semantic hash;
- protected files remain unchanged.

Full repository acceptance:

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/generate_indexes.py --check
```

Required CI jobs:

- Static contract lint
- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13
- Python 3.14
- Generated file contract
- LaTeX CUMCM
- LaTeX MCM-ICM
- LaTeX Diangong
- Production LaTeX attestation

## 11. Acceptance criteria

The patch is complete only when:

1. both Skill files read successfully and are byte-identical;
2. no active file references `core/project_memory_contract.yaml`;
3. project-memory Authority points to the existing Framework template;
4. automated regression fails for any future nonexistent Authority-table target;
5. all current version carriers equal 8.1.1;
6. generated files are current;
7. all required CI jobs pass;
8. all protected blob SHAs match;
9. v8.1 Cross-File business semantics are unchanged;
10. the PR contains no unrelated CI, model, numerical, template-order or writing-rule changes.

## 12. Rollback

If the regression or release update creates unexpected behavior, revert the single repair PR. No project state, workbook, solve result, approval record or LaTeX project migration is required.

## 13. Post-merge EOF newline hygiene remediation

The post-merge audit of PR #102 found a formatting-only regression in the files updated through the GitHub contents API: thirteen pre-existing text files lost their final LF byte and their commits report `No newline at end of file`.

This does not change Skill behavior or any protected semantics, but it violates the no-new-regression acceptance intent. Remediation is therefore part of closing this plan:

1. create `fix/v811-eof-newline-hygiene` from merge commit `76bf73a3dca54d1df2d2908accf4b65d09a7fe82`;
2. restore exactly one terminal LF to the thirteen affected files, with no content change;
3. let the existing generator refresh `MANIFEST.sha256`;
4. rerun all eleven CI jobs;
5. reconfirm the protected semantic blob SHAs and merge through a separate PR.

This hygiene follow-up must not bump the Skill version or alter the v8.1.1 release text.

