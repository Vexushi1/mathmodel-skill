# Agent instructions

1. Read `core/bootstrap.yaml` first.
2. Run `scripts/resolve_workflow.py` for one or more intents; do not preload the whole repository.
3. Classify each subproblem with one objective, up to three structures and independent capabilities using `core/task_taxonomy.yaml`.
4. Create or update project-root `模型论文框架.md` after the model is locked; keep only current semantics.
5. Before every formal artifact delivery, run `scripts/sync_project.py <project_root> --write --strict` and include `sync_report.yaml`.
6. The synchronizer never invents model semantics, results or passed validation; it only discovers artifacts, reads workbook structure, hashes files and propagates stale.
7. Python solves and writes workbooks. MATLAB reads exact unique headers from the same question directory and draws formal figures. DOCX is the draft carrier; LaTeX is the final paper.
8. Load `packs/artifact/proposition_proof.md` only for explicit proof requests or a nonzero proposition plan. Do not load `legacy/` by default.
