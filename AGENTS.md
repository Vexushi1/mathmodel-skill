# Agent instructions

## Runtime tasks

1. Read `core/bootstrap.yaml` first.
2. Run `scripts/resolve_workflow.py` for one or more intents; do not preload the whole repository.
3. Classify each subproblem with one objective, up to three structures and independent capabilities using `core/task_taxonomy.yaml`.
4. Create or update project-root `模型论文框架.md` after the model is locked; keep only current semantics.
5. Before every formal artifact delivery, run `scripts/sync_project.py <project_root> --write --strict` and include `sync_report.yaml`.
6. The synchronizer never invents model semantics, results or passed validation; it only discovers artifacts, reads workbook structure, hashes files and propagates stale.
7. Python solves and writes workbooks. MATLAB reads exact unique headers from the same question directory and draws formal figures. DOCX is the draft carrier; LaTeX is the final paper.
8. Load `packs/artifact/proposition_proof.md` only for explicit proof requests or a nonzero proposition plan. Do not load `legacy/` by default.

## Repository modification tasks

1. Before changing any active repository file, read the current `main` versions of `core/bootstrap.yaml` and `SKILL_CHANGE_GOVERNANCE.md`.
2. Confirm the current Skill version, latest `main` commit, overlapping open PRs and authoritative source files.
3. Produce the required change brief before writing files.
4. Use one dedicated branch and one single-theme PR; never write directly to `main`.
5. Do not rely on previous-chat memory, duplicate authoritative rules, hand-edit generated indexes or falsify test status.
6. Run the governance-mandated lint, full tests, generated-file checks and affected specialist checks before merge.
7. Report branch, PR, merge status, commit SHA, compatibility and unfinished validation accurately.