---
name: mathmodel-skill
description: Plugin discovery shim for the HSK v6.2.4 modular mathematical-modeling workflow.
---

Read `../../SKILL.md`, `../../core/hsk_core_policy.md`, `../../core/workflow_router.yaml`, and `../../core/module_manifest.yaml`. Classify each subproblem into one primary label, at most two necessary secondary labels, and validation capability flags; use `../../scripts/resolve_workflow.py` when a deterministic load plan is needed. Contest files, attachments and Python scripts live in the project root. Python writes the two standard per-question Excel workbooks directly under `结果数据表/问题X/`; the writer and artifact checker reuse the same `../../core/workbook_schema.yaml` validator. The unique MATLAB entry `q{x}_plot.m` lives beside those workbooks and exports formal figures to the local `图表/` subdirectory. Do not create `Python求解/`, `MATLAB绘图/` or `问题X结果数据/` by default. LaTeX cleanup precedes final compilation. Resolve repository paths relative to `../..`, load `../../assets/figure_assets.yaml` only when visual reference is useful, and never load `legacy/` by default.
