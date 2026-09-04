# v8.6.1 Post-Merge Delivery Verification Record

> Document role: post-merge factual verification record; **not** runtime Authority.  
> Verified release: **v8.6.1**  
> Merged release PR: **#111**  
> PR #111 merge commit / verification target: `f757d823135ce8f97c404b60bd5965e2a071bb82`  
> Verification date: 2026-09-04

## 1. Why this record exists

`docs/v861_active_consistency_semantic_drift_hardening_plan.md` is retained as the implementation Scope Contract and therefore contains pre-merge wording such as “尚未合并 `main`” and “PR-head CI 必须全绿后才可 Ready/merge”. Those statements describe the implementation/release-decision stage at the time the plan was finalized; they are **historical workflow state, not live repository state**.

Live repository state is determined by the repository’s current `main`, release carriers and the CI attached to the relevant current commit. This record closes the historical/current distinction for the v8.6.1 release without treating any fixed SHA in this document as a permanently current `main` pointer. Subsequent docs-only closure commits may advance `main`; that does not change the release/runtime semantics recorded here and must be verified by their own CI.

## 2. Release-merge closure

PR #111, `fix: harden v8.6.1 active consistency and semantic drift`, was merged successfully.

```text
release_pr = #111
release_pr_head = b1207ce37ed2e12451cc8c7999af508f6671bb2e
release_merge_commit = f757d823135ce8f97c404b60bd5965e2a071bb82
main_head_immediately_after_release_merge = f757d823135ce8f97c404b60bd5965e2a071bb82
```

A commit comparison from the final release PR head to the release merge commit reports no changed files, so the merge commit preserves the verified PR-head tree exactly; the only additional commit is the merge commit itself.

## 3. Release-carrier parity at the verified release state

The v8.6.1 release carriers were synchronized as follows:

- `core/bootstrap.yaml`: `skill_version: 8.6.1`
- `.codex-plugin/plugin.json`: `"version": "8.6.1"`
- `README.md`: `# mathmodel-skill v8.6.1`
- `SKILL.md`: frontmatter `version: 8.6.1` and heading `v8.6.1`
- `skills/mathmodel-skill/SKILL.md`: same content/blob as root `SKILL.md`
- `CHANGELOG.md`: `## Current release: 8.6.1`

This verification record does not introduce a version bump. Any later docs-only closure commit must preserve these release carriers unless a separately governed release changes them.

## 4. Release post-merge CI closure

The push workflow on the release merge commit completed successfully:

```text
HSK Skill CI #2433
verified_head = f757d823135ce8f97c404b60bd5965e2a071bb82
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

The separate `Refresh generated repository metadata` push workflow on the release merge commit also completed successfully, confirming generated metadata was current at that verified state.

## 5. Runtime and scope integrity

This verification record changes no model, solver, validator, runtime, schema, CLI, Model Approval, preprocessing, user-execution, workbook, project-state, figure or LaTeX behavior. It records the v8.6.1 release closure and disambiguates the historical Scope Contract from live repository state.

The v8.6.1 release conclusion is therefore:

```text
release = 8.6.1
release_pr_merged = true
release_merge_verified = true
release_carriers_synchronized = true
root_package_skill_parity = true
generated_metadata_fresh_at_release_merge = true
release_post_merge_ci = success
runtime_behavior_changed_by_verification = false
delivery_status = released_and_verified
```

For any later repository state, do not infer the current `main` SHA from this historical record; read live `main` and its CI directly.