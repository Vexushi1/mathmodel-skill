# Architecture Provenance Archive

本目录保存已经完成使命的一次性架构迁移矩阵、版本实施计划和维护施工计划。它们用于 Git 历史之外的人工 provenance 与迁移追溯，**不是 Runtime Authority，也不属于当前默认运行链路**。

使用边界：

- 当前行为始终以 `core/bootstrap.yaml` 指向的活动 Authority、modules、packs 和 scripts 为准；
- 本目录文件不得进入默认 Router load、Active Skill Index、Active MANIFEST 或正式交付依赖；`scripts/generate_indexes.py` 只保留 `legacy/README.md` 作为历史导航入口，不索引本目录正文；
- 若历史计划与当前实现不一致，以当前 Authority 和当前测试为准；
- 只有在追溯某次架构迁移、解释历史设计取舍或维护旧项目时才人工读取。

当前归档：

- `authority_duplication_matrix_v7.11.1.md`：v7.11.1 单一事实源收口前的 authority duplication matrix；
- `v7.14_primary_numerical_validity_plan.md`：v7.14.0 Primary Numerical Validity & Quality Gate 的实施计划；
- `v7.14.1_skill_health_hygiene_plan.md`：v7.14.1 Skill health / semantic hygiene 维护计划；
- `v7.15_scientific_figure_elevation_plan.md`：v7.15.0 Scientific Evidence Capture & Figure Synthesis 的实施计划；
- `v7.16_paper_writing_skill_rollback_and_optimization_plan.md`：v7.16.0 Paper Writing Specification & Model Expression Closure 的实施计划；
- `v7.17_mechanism_structural_validity_hardening_plan.md`：v7.17.0 Mechanism Structural Validity Hardening 的实施计划；
- `v7.18_model_establishment_solution_writing_style_hardening_plan.md`：v7.18.0 Model Establishment & Solution Writing Style Hardening 的实施计划；
- `v7.19_main_body_architecture_detail_figure_writing_hardening_plan.md`：v7.19.0 Intra-Question Writing Closure 的实施计划。
