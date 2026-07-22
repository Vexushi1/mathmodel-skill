# Agent instructions

For repository navigation, read `REPOSITORY_INDEX.md`. For the complete active path inventory, use `HSK_SKILL_FILE_INDEX_V622.md`; archived history is reached only through `legacy/README.md`.

For task execution, read `core/hsk_core_policy.md`, `core/workflow_router.yaml`, and `core/module_manifest.yaml` first. Classify every subproblem separately into one primary task label, at most two necessary secondary labels, and validation capability flags. Load only the relevant modules, packs, templates, and optional figure assets.

Python solves and writes the two validated per-question Excel workbooks under `结果数据表/问题X/问题X结果数据/`; MATLAB reads them to produce formal result figures. The writer and artifact checker reuse the same workbook validator. LaTeX draft cleanup precedes final compilation.

Use `scripts/resolve_workflow.py` for deterministic load plans, `scripts/validate_project_state.py` for real project-state semantics, and `scripts/score_submission.py` for weighted review. If GitHub code search is unavailable or stale, resolve files directly from `REPOSITORY_INDEX.md` and call `fetch_file` instead of treating the repository as empty.
