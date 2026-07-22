---
name: mathmodel-skill
description: Plugin discovery shim for the HSK modular mathematical-modeling workflow.
---

Read `../../SKILL.md`, `../../core/hsk_core_policy.md`, `../../core/workflow_router.yaml`, and `../../core/module_manifest.yaml`. Use the router to distinguish design-only, full-solution, and full-workflow requests, then load only the selected modules and packs. Python owns solving and the two standard per-question Excel workbooks; both the writer and artifact checker enforce `../../core/workbook_schema.yaml`. MATLAB owns formal result figures. Resolve all paths relative to `../..` and never load `legacy/` by default.
