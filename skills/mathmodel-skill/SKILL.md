---
name: mathmodel-skill
version: 7.2.3
summary: HSK mathematical-modeling workflow with Problem Contract freezing, semantic closure, complexity sanity checks, generalized evidence-driven conditional data preprocessing, preprocessing MATLAB evidence via data_process.m, dependency-aware stale propagation, full-fidelity solving, separate primary/result-analysis Python stages, MATLAB evidence figures and LaTeX-first writing.
triggers: [数学建模, 数模, CUMCM, 国赛, MCM, ICM, 电工杯, 认证杯, 数据预处理, Python求解, MATLAB绘图, LaTeX, DOCX]
---

# HSK 数学建模模块化工作流 v7.2.3

1. 从本目录定位仓库根目录 `../..`，读取 `../../core/bootstrap.yaml`；
2. 使用 `../../scripts/resolve_workflow.py` 获取任务执行计划；
3. 正式模型与代码前先完成 Problem Contract、当前附件的非破坏性通用数据审计、`preprocessing_decision`、题面—数学—代码语义闭环和 Complexity Sanity Check，并运行 `../../scripts/validate_semantic_governance.py`；
4. `preprocessing_decision` 只有三种：`not_needed`、`question_local`、`project_level`。共享同一原始数据源、检测到缺失值或某类赛题过去常见处理本身都不是 `project_level` 的充分条件；
5. 只有 `project_level` 才创建项目级数据预处理：Python阶段生成 `数据预处理/数据预处理.py` 与 `数据预处理结果.xlsx`，Figure Evidence阶段固定补充 `数据预处理/data_process.m`；`not_needed` 直接使用原始数据，`question_local` 只在本问脚本内做有数学来源的局部变换；
6. 判定必须检查当前数据的完整性、一致性、有效性、重复身份、采样与覆盖、测量质量、模型输入要求以及时间因果/信息泄漏；缺失值不等于必须插值，插值、统计填补、模型填补和预测填补都必须按变量语义、缺失结构与可验证性选择；
7. 预测填补只可用于恢复后续模型确实需要的缺测输入，并须独立验证且禁止未来信息/标签泄漏；赛题本身要求预测的未来值、类别、需求、风险等属于核心模型，不得包装为数据预处理；
8. `数据预处理.py` 必须把 `data_process.m` 所需的处理前后、修复验证、采样覆盖或结构对齐真实底层数据写入统一工作簿；`data_process.m` 只读该工作簿绘图，不重新插值、填补、滤波、平滑、预测、异常修复或重采样；
9. 模型语义或数据处理判定变化时递增 semantic revision，并按 data / parameter / model / result 依赖递归传播 stale；
10. 每问最终维护两个题目专属 Python：`问题X求解.py` 和 `问题X结果深化分析.py`，并保留两个标准工作簿与一个 `qX_plot.m`；主求解脚本 accepted 后冻结，结果深化分析使用独立脚本；
11. 实际生成的 `preprocessing / primary / analysis` 代码阶段都必须通过 `../../core/code_quality_contract.yaml` 与 `../../scripts/validate_code_delivery.py`；
12. 用户完整运行后，由 `validate_user_execution.py` 按当前数据事实源验收工作簿、对应阶段代码/数据哈希和质量门；
13. 深化分析不稳定时按原因回退模型、条件式预处理或主求解并传播 stale；只改深化脚本不得污染已通过的主结果质量状态；
14. MATLAB只读真实工作簿绘图：project_level预处理统一用 `data_process.m`，每问用 `qX_plot.m`；LaTeX为默认论文主链，DOCX仅显式按需。

详细规则以 `../../core/` 下权威合同为准。v7.2.0--v7.2.2 项目重新进入设计/求解时沿用三态 `preprocessing_decision` 并按当前通用审计框架复核处理必要性；project_level旧项目重新进入 Figure Evidence 时补充 `data_process.m`；更早项目与 `legacy/` 按既有只读兼容规则处理。
