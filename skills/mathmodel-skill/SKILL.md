---
name: mathmodel-skill
description: Plugin discovery shim for the HSK v6.3.2 lightweight-bootstrap, multi-intent routing and contract-closed project synchronization workflow.
---

Read `../../core/bootstrap.yaml` first. Resolve the request with `../../scripts/resolve_workflow.py`, then load only the returned contracts, modules, packs and templates. Classify every subproblem by one `classification.objective`, up to three `classification.structures`, and one authoritative top-level `capabilities` mapping; legacy task labels and `classification.capabilities` are compatibility aliases only.

After `locked_model_spec` exists, maintain project-root `模型论文框架.md` as the current effective model and paper source. Before every formal model, code, workbook, MATLAB figure, DOCX, LaTeX or submission delivery, execute the resolver's `pre_delivery_gates`. Run `../../scripts/sync_project.py <project_root> --write --strict --delivery-scope <scope>` for `project_sync`; only a successful gate makes `sync_report.yaml` available.

The synchronizer validates stage-required artifacts, workbook schemas and the MATLAB-to-figure chain; computes layered data, model, workbook, MATLAB, figure and framework hashes; and propagates stale state. It must never invent model semantics, numerical results or validation success. Python writes the two standard workbooks to `结果数据表/问题X/`; the unique `q{x}_plot.m` reads exact unique headers and exports formal figures to `图表/`. Do not load `legacy/` by default. Load `../../packs/artifact/proposition_proof.md` only for explicit proof requests or a nonzero proposition plan.
