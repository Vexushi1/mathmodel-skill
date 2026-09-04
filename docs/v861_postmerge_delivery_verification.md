# v8.6.1 Post-Merge Delivery Verification Record

> Document role: post-merge factual verification record; **not** runtime Authority.  
> Verified release: **v8.6.1**  
> Merged PR: **#111**  
> Merge commit / current verified `main`: `f757d823135ce8f97c404b60bd5965e2a071bb82`  
> Verification date: 2026-09-04

## 1. Why this record exists

`docs/v861_active_consistency_semantic_drift_hardening_plan.md` is retained as the implementation Scope Contract and therefore contains pre-merge wording such as “尚未合并 `main`” and “PR-head CI 必须全绿后才可 Ready/merge”. Those statements describe the implementation/release-decision stage at the time the plan was finalized; they are **historical workflow state, not current repository state**.

Current repository state is determined by current `main`, release carriers and post-merge CI. This record closes that distinction explicitly so the historical plan cannot be misread as the live release status.

## 2. Merge closure

PR #111, `fix: harden v8.6.1 active consistency and semantic drift`, was merged successfully.

```text
pr = #111
pr_head = b1207ce37ed2e12451cc8c7999af508f6671bb2e
merge_commit = f757d823135ce8f97c404b60bd5965e2a071bb82
main_head_after_merge = f757d823135ce8f97c404b60bd5965e2a071bb82
```

A commit comparison from the final PR head to the merge commit reports no changed files, so the merge commit preserves the verified PR-head tree exactly; the only additional commit is the merge commit itself.

## 3. Release-carrier parity after merge

The following current-main carriers are synchronized to `8.6.1`:

- `core/bootstrap.yaml`: `skill_version: 8.6.1`
- `.codex-plugin/plugin.json`: `"version": "8.6.1"`
- `README.md`: `# mathmodel-skill v8.6.1`
- `SKILL.md`: frontmatter `version: 8.6.1` and heading `v8.6.1`
- `skills/mathmodel-skill/SKILL.md`: same content/blob as root `SKILL.md`
- `CHANGELOG.md`: `## Current release: 8.6.1`

No follow-up version bump is introduced by this verification record.

## 4. Post-merge CI closure

The push workflow on the merge commit completed successfully:

```text
HSK Skill CI #2433
head = f757d823135ce8f97c404b60bd5965e2a071bb82
status = completed
conclusion = success
```

Successful jobs include:

- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13
- Python 3.14
- Static contract lint
- Generated file contract
- LaTeX CUMCM
- LaTeX MCM-ICM
- LaTeX Diangong
- Production LaTeX attestation

The separate `Refresh generated repository metadata` push workflow on `main` also completed successfully, confirming generated metadata was already current after merge.

## 5. Runtime and scope integrity

This post-merge verification introduces no model, solver, validator, runtime, schema, CLI, Model Approval, preprocessing, user-execution, workbook, project-state, figure or LaTeX behavior change. It only records the final release state after PR #111 and disambiguates the historical Scope Contract from current repository state.

The v8.6.1 delivery conclusion is therefore:

```text
release = 8.6.1
merged = true
main_verified = true
release_carriers_synchronized = true
root_package_skill_parity = true
generated_metadata_fresh = true
post_merge_ci = success
runtime_behavior_changed_by_verification = false
delivery_status = released_and_verified
```
