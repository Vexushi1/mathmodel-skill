---
name: mathmodel-skill
description: Plugin discovery shim for the HSK v6.2.5 current-model-framework mathematical-modeling workflow.
---

Read `../../SKILL.md`, `../../core/hsk_core_policy.md`, `../../core/workflow_router.yaml`, and `../../core/module_manifest.yaml`. Classify each subproblem into one primary label, at most two necessary secondary labels, and validation capability flags; use `../../scripts/resolve_workflow.py` when a deterministic load plan is needed.

After `locked_model_spec` exists, create project-root `模型论文框架.md` from `../../templates/model/model_paper_framework.md`. Keep only the current effective model semantics, paper structure, per-question result summaries and figure mappings. When models, parameters, constraints, data processing, algorithms, results or figures change, remove affected old content and replace it with the current version; Git history stores prior versions. Every formal artifact delivery must include the complete synchronized framework and may be checked by `../../scripts/validate_model_paper_framework.py`.

Contest files, attachments, the framework and Python scripts live in the project root. Python writes the two standard per-question Excel workbooks directly under `结果数据表/问题X/`; the writer and artifact checker reuse the same `../../core/workbook_schema.yaml` validator. The unique MATLAB entry `q{x}_plot.m` lives beside those workbooks and exports formal figures to the local `图表/` subdirectory. Single figures retain a concise `title`; multi-panel figures retain one `sgtitle`; DOCX/LaTeX captions supplement rather than duplicate them. Do not create `Python求解/`, `MATLAB绘图/` or `问题X结果数据/` by default. LaTeX cleanup precedes final compilation. Resolve repository paths relative to `../..`, load `../../assets/figure_assets.yaml` only when visual reference is useful, and never load `legacy/` by default.
