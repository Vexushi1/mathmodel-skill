---
name: mathmodel-skill
description: Plugin discovery shim for the HSK modular mathematical-modeling workflow.
---

Read `../../SKILL.md`, `../../core/hsk_core_policy.md`, and `../../core/workflow_router.yaml`. Load only the selected modules and packs. Python owns solving and the two standard per-question Excel workbooks; MATLAB owns formal result figures through one self-contained `QX_plot.m` per question. For plotting requests, also load `../../modules/04_figure_evidence.md`, `../../templates/figure/chart_selection.md`, and `../../templates/figure/scientific_composite_system.md` so formal figures use the high-contrast single/layered/multi-panel/hybrid system. Resolve all paths relative to `../..` and never load `legacy/` by default.
