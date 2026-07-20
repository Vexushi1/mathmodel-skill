# Agent instructions

For repository navigation, read `REPOSITORY_INDEX.md`. For the complete path inventory, use `HSK_SKILL_FILE_INDEX_V622.md`.

For task execution, read `core/hsk_core_policy.md` and `core/workflow_router.yaml` first, then load only the relevant modules, packs, and templates. Follow `core/output_contract.yaml`, `core/workbook_schema.yaml`, `core/project_state.schema.yaml`, and `core/compile_profiles.yaml` when the task reaches those artifacts.

Python solves and writes the two validated per-question Excel workbooks under `结果数据表/问题X/问题X结果数据/`; MATLAB reads them to produce formal result figures. Do not load `legacy/` by default.

If GitHub code search is unavailable or stale, resolve files directly from the paths in `REPOSITORY_INDEX.md` and call `fetch_file` instead of treating the repository as empty.
