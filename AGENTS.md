# Agent instructions

For repository navigation, read `REPOSITORY_INDEX.md`. For the complete path inventory, use `HSK_SKILL_FILE_INDEX_V621.md`.

For task execution, read `core/hsk_core_policy.md` and `core/workflow_router.yaml` first, then load only the relevant modules, packs, and templates. Python solves and writes the two standard per-question Excel workbooks under `结果数据表/问题X/问题X结果数据/`; MATLAB reads them to produce formal result figures. Do not load `legacy/` by default.

If GitHub code search is unavailable or stale, resolve files directly from the paths in `REPOSITORY_INDEX.md` and call `fetch_file` instead of treating the repository as empty.
