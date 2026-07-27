---
name: mathmodel-skill
description: Plugin discovery shim for the HSK v6.3 lightweight-bootstrap, multi-intent routing and project synchronization workflow.
---

Read `../../core/bootstrap.yaml` first. Resolve the request with `../../scripts/resolve_workflow.py`, then load only the returned contracts, modules, packs and templates. Classify every subproblem by one objective, up to three structures and independent validation capabilities; legacy task labels are only compatibility mappings.

After `locked_model_spec` exists, maintain project-root `模型论文框架.md` as the current effective model and paper source. Before every formal model, code, workbook, MATLAB figure, DOCX, LaTeX or submission delivery, run `../../scripts/sync_project.py <project_root> --write --strict` and include `sync_report.yaml`. The synchronizer may discover artifacts, read workbook structure, hash files and propagate stale state, but must never invent model semantics, numerical results or validation success.

Python writes the two standard workbooks to `结果数据表/问题X/`; the unique `q{x}_plot.m` in that directory reads exact unique headers and exports formal figures to `图表/`. Do not load `legacy/` by default. Load `../../packs/artifact/proposition_proof.md` only for explicit proof requests or a nonzero proposition plan.
