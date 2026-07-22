---
name: mathmodel-skill
description: Plugin discovery shim for the HSK v6.2.3 modular mathematical-modeling workflow.
---

Read `../../SKILL.md`, `../../core/hsk_core_policy.md`, `../../core/workflow_router.yaml`, and `../../core/module_manifest.yaml`. Classify each subproblem into one primary label, at most two necessary secondary labels, and validation capability flags; use `../../scripts/resolve_workflow.py` when a deterministic load plan is needed. Python owns solving and the two standard per-question Excel workbooks; the writer and artifact checker reuse the same `../../core/workbook_schema.yaml` validator. MATLAB owns formal result figures. LaTeX cleanup precedes final compilation. Resolve all paths relative to `../..`, load `../../assets/figure_assets.yaml` only when visual reference is useful, and never load `legacy/` by default.
