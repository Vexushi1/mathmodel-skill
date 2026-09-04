# v8.7.0 Post-Merge Verification Record

> Status: **released / post-merge verification complete**. This file is a time-stable release verification record, not a live pointer to whatever commit `main` may advance to in the future and not a writing Authority.

## 1. Release target

The v8.7.0 release was merged through PR #114.

```text
release_pr = #114
release_merge_commit = 4a10e889e97b84715729ed70ccf248ec2a9ca3a9
release_version = 8.7.0
```

The semantic scope is the approved Per-Question Writing Capability Preflight release: state-driven capability activation, Formula Role Taxonomy, adaptive Core Model Summary activation, Proposition/Proof activation, Algorithm stepwise/pseudocode activation, behavior fixtures/tests, and release-carrier synchronization.

## 2. Post-merge main CI

The release merge commit was validated on `main` by HSK Skill CI run #2502 (run ID `33897510479`).

Result: **completed / success**.

All 11 jobs passed:

- Generated file contract
- Static contract lint
- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13
- Python 3.14
- LaTeX CUMCM
- LaTeX MCM-ICM
- LaTeX Diangong
- Production LaTeX attestation

This is post-merge evidence on the release merge commit, not a pre-merge PR-only substitute.

## 3. Generated metadata verification

The normal `Refresh generated repository metadata` workflow run #1896 (run ID `33897510563`) completed with **success** on the same release merge commit.

The release merge also passed the independent `Generated file contract` job inside HSK Skill CI #2502. No metadata refresh commit was required after the merge; `refs/heads/main` remained on the release merge commit during this verification.

## 4. Version-carrier confirmation

At verification time:

- `core/bootstrap.yaml` reports `skill_version: 8.7.0`;
- root `SKILL.md` reports `version: 8.7.0`;
- packaged `skills/mathmodel-skill/SKILL.md` reports `version: 8.7.0`;
- root and packaged `SKILL.md` have the same Git blob SHA `6c8746710941ed71c42c8ffb50acb8203f30878a`;
- `.codex-plugin/plugin.json` reports `version: 8.7.0`;
- `SKILL_FILE_INDEX.md` and `TEMPLATE_INDEX.md` both report current Skill version `8.7.0`.

Therefore the release-carrier and generated-index surfaces were synchronized for v8.7.0 at this verification point.

## 5. Boundary of this record

This record does not claim that a fixed SHA is permanently the live `main`. Future documentation-only, metadata, maintenance, or feature commits may legitimately advance `main` while v8.7.0 remains the current release until a later version is published.

For future live-state questions, read `refs/heads/main` and the workflows associated with that then-current commit instead of inferring current state from this historical verification record.

No additional model, solver, validator, numerical, Workbook/Project State, Figure, LaTeX runtime, public schema, CLI, Model Approval, or 03A/03B semantics are introduced by this file.
