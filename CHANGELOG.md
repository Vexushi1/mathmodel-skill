# Changelog

## Current release: 6.6.0

- Restored one self-contained `问题X求解/` directory per subproblem.
- New projects keep exactly one evolving Python script, two standard workbooks and one `qX_plot.m` in that directory.
- Removed standalone run-config, execution-instruction and validation-report files from the default user-visible output.
- Fixed cross-question Python hash contamination in project synchronization.
- Kept legacy `结果数据表/问题X/` and separate analysis-code layouts as read-only compatibility inputs.
- Corrected the nested plugin entry path and removed the stale LaTeX module version title.
- Kept the existing DOCX + review multi-intent ordering unchanged in this release.
- Hotfix: removed the obsolete standalone run-config and execution-instruction templates, the superseded MATLAB handoff writer, and the redundant artifact checker.
- Hotfix: aligned the global policy, Starter guides, code appendix, Figure Contract, MATLAB reader, optional manifest, review pack and active tests with the exact four-file contract.
- Hotfix: default MATLAB delivery now keeps only the visible figure window; exports belong to project-level `figures/` only after paper-stage confirmation.

## Previous release: 6.5.1

- Removed the obsolete fixed sensitivity/robustness checklist and the unreferenced pre-user-execution pipeline config.
- New-project starters now stop after `run_primary_pipeline()`; `run_pipeline()` remains only as a user-local compatibility API.
- Local workbook generation records `workbook_received` and can no longer promote a subproblem to `solved` or `analyzed` before returned-workbook validation.
- Both standard workbooks now require the `运行配置` evidence sheet; workbook schema version is 2.2.1.

## Previous release: 6.5.0

- Default execution ownership is now user-managed full-fidelity: the assistant generates task-specific code but never runs solve or result-analysis programs.
- Added formal code-delivery and returned-workbook gates, execution states, full-run configuration, code/data hash checks, and the mandatory `运行配置` workbook evidence contract.
- Primary code delivery pauses at `awaiting_user_execution`; final result-analysis code is generated only after the returned primary workbook is accepted.
- Existing local pipelines remain runnable by the user; legacy projects without the new optional execution fields remain readable.

## Previous release: 6.4.1

- Active MATLAB and figure templates now use `问题X结果深化分析.xlsx` instead of generating the historical `问题X敏感性与鲁棒性结果.xlsx` name.
- `result_manifest.yaml` now records `result_analysis_workbook` as the current field.
- The code-appendix template now names the primary-solve and result-analysis scripts separately.
- `AGENTS.md` now matches the LaTeX-first workflow and treats DOCX as an explicit optional branch.
- Added regression coverage that prevents current-generation templates from reintroducing legacy workbook names and checks packaged/root Skill version alignment.

## Previous release: 6.4.0

### Quality-first primary solving

- Added an explicit primary-result quality gate before any sensitivity, robustness or multi-algorithm analysis.
- Split primary solving from result analysis in the module graph, state machine and workbook contract.
- Added adaptive result-analysis selection based on problem, model, data, result and reviewer risk instead of a fixed perturbation checklist.
- Added structured `passed` / `failed` / `redo_required` outcomes and stale propagation when result analysis invalidates the primary result.
- Switched the default full workflow to LaTeX-first authoring; DOCX is now an explicit independent review branch.
- Replaced versioned active entry filenames with stable names and moved historical release documents into `legacy/`.

## Previous release: 6.3.4

- Added the `result_analysis` module and separated it from primary solving.
- Added current-state `模型论文框架.md` synchronization for model, result, analysis and figure changes.
- Added adaptive analysis categories, redo-required feedback and figure-evidence updates.
- Updated the three competition profiles, score rubric and submission checks.

## Previous release: 6.3.3

- Hardened formal delivery gates with exact-scope artifact requirements.
- Added conservative stale propagation and write-after-hash checks.
- Added state and framework preflight validation before synchronization.

## Previous release: 6.3.2

- Added current-state project synchronization and per-question artifact hashes.
- Added objective-specific workbook evidence and data-source hashing isolation.
- Added document, LaTeX and submission artifact validation.

## Previous release: 6.3.1

- Added three-axis task classification: objective, structures and capabilities.
- Added deterministic workflow resolution and multi-intent support.
- Added proposition planning and proof integration.

## Previous release: 6.3.0

- Introduced the modular workflow graph and project-state contract.
- Added output, workbook, figure and compile contracts.

## Previous releases

See the versioned changelog files and `legacy/README.md` for v6.2.x and earlier history.
