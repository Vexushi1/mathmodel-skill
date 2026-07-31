# Changelog

## Current release: 6.4.0

### Quality-first primary solving

- `modules/03_solve_validate.md` now represents complete primary solving plus a mandatory result-quality gate.
- Solver termination, feasibility, optimality gap, residuals, convergence, leakage, base out-of-sample accuracy, uncertainty and identifiability remain in primary solving when applicable.
- The quality report is persisted in `问题X求解结果.xlsx` as `主结果质量门`; failed primary results cannot enter downstream analysis.

### Adaptive result analysis

- Added `modules/03_result_analysis.md` after primary solving and before figures.
- Result analysis methods are selected from the actual problem, model, data, primary-result behavior and reviewer risk.
- Supported evidence families include sensitivity, scenario robustness, multi-algorithm consistency, structural robustness, thresholds, heterogeneity, error decomposition and out-of-sample stability.
- Uniform ±5%/±10% perturbation is explicitly forbidden as a default template.
- Analysis failures can set `redo_required`, propagate stale and return the workflow to model design or primary solving.

### Workbook and state contracts

- New projects write `问题X求解结果.xlsx` and `问题X结果深化分析.xlsx`.
- Result-analysis workbooks require `分析设计`, at least one substantive analysis sheet and `结论稳定性汇总`.
- `result_quality_status` and `result_analysis_status` are tracked separately.
- Artifact hashes now distinguish `solution_workbook` and `result_analysis_workbook`.
- Legacy `问题X敏感性与鲁棒性结果.xlsx` remains read-only compatible but is not a new-project deliverable.

### Python, MATLAB and synchronization

- Added authoritative `run_primary_pipeline()` and `run_result_analysis_pipeline()` functions.
- Updated all starter templates to expose separate quality and result-analysis hooks.
- MATLAB handoff and readers now consume primary-solve and result-analysis workbooks.
- Project synchronization uses solved/analyzed state semantics and never promotes either quality or analysis status.

### LaTeX-first default workflow

- Default `full_workflow` proceeds from approved figures directly to LaTeX, AI cleanup, compilation and final review.
- DOCX route, module and delivery scope remain available only for explicit Word/DOCX requests.
- DOCX is not a LaTeX prerequisite.

### Stable active filenames

- Active instructions and indexes use `PROJECT_INSTRUCTIONS.md`, `RUNTIME_ROUTER.md`, `SKILL_FILE_INDEX.md` and `TEMPLATE_INDEX.md`.
- Old `V622` filenames remain compatibility pointers.
- `scripts/generate_indexes.py` manages active indexes, pointers and `MANIFEST.sha256`.
