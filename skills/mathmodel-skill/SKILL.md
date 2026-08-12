---
name: mathmodel-skill
version: 7.2.5
summary: HSK mathematical-modeling workflow with Problem Contract freezing, semantic closure, generalized evidence-driven conditional preprocessing, substantive preprocessing paper evidence, dedicated data_process MATLAB figures, dependency-aware stale propagation, full-fidelity solving, separate primary/result-analysis Python stages and LaTeX-first writing.
triggers: [数学建模, 数模, CUMCM, 国赛, MCM, ICM, 电工杯, 认证杯, 数据预处理, Python求解, MATLAB绘图, LaTeX, DOCX]
---

# HSK 数学建模模块化工作流 v7.2.5

1. 从本目录定位仓库根目录 `../..`，读取 `../../core/bootstrap.yaml`；
2. 使用 `../../scripts/resolve_workflow.py` 获取任务执行计划；
3. 正式模型与代码前先完成 Problem Contract、当前附件的非破坏性通用数据审计、`preprocessing_decision`、题面—数学—代码语义闭环和 Complexity Sanity Check，并运行 `../../scripts/validate_semantic_governance.py`；
4. `preprocessing_decision` 只有三种：`not_needed`、`question_local`、`project_level`。共享同一原始数据源、检测到缺失值或某类赛题过去常见处理本身都不是 `project_level` 的充分条件；
5. 只有 `project_level` 才创建 `数据预处理/`；最终标准文件为 `数据预处理.py`、`数据预处理结果.xlsx` 和 `data_process.m`。`not_needed` 直接使用原始数据，`question_local` 只在本问脚本内做有数学来源的局部变换；
6. 判定必须检查当前数据的完整性、一致性、有效性、重复身份、采样与覆盖、测量质量、模型输入要求以及时间因果/信息泄漏；缺失值不等于必须插值，插值、统计填补、模型填补和预测填补都必须按变量语义、缺失结构与可验证性选择；
7. 预测填补只可用于恢复后续模型确实需要的缺测输入，并须独立验证且禁止未来信息/标签泄漏；赛题本身要求预测的未来值、类别、需求、风险等属于核心模型，不得包装为数据预处理；
8. 只要实际预处理改变后续模型输入，论文必须给出数据问题、数学公式或映射、参数依据、方法验证、处理前后证据和后续模型接口；经验型处理不得编造形式证明；
9. `project_level` 的 `data_process.m` 是项目级预处理证据固定 MATLAB 脚本；文件归属 `数据预处理/`，但仅在 Figure Evidence 阶段、主求解与结果深化分析完成后生成。它只读取 `数据预处理结果.xlsx` 中 Python 已持久化的处理前后、诊断和验证数据绘图，不重新清洗、插值、滤波、重采样或估计参数；正式导出基名使用 `data_process` 或 `data_process_<evidence>`；
10. 模型语义或数据处理判定变化时递增 semantic revision，并按 data / parameter / model / result 依赖递归传播 stale；
11. 每问最终维护两个题目专属 Python：`问题X求解.py` 和 `问题X结果深化分析.py`，并保留两个标准工作簿与一个 `qX_plot.m`；主求解脚本 accepted 后冻结，结果深化分析使用独立脚本；
12. 实际生成的 `preprocessing / primary / analysis` 代码阶段都必须通过 `../../core/code_quality_contract.yaml` 与 `../../scripts/validate_code_delivery.py`；
13. 用户完整运行后，由 `validate_user_execution.py` 按当前数据事实源验收工作簿、对应阶段代码/数据哈希和质量门；project_level 工作簿同时必须保存论文方法、处理前后和绘图底层证据；
14. 深化分析不稳定时按原因回退模型、条件式预处理或主求解并传播 stale；只改深化脚本不得污染已通过的主结果质量状态；
15. MATLAB只读真实工作簿证据绘图，LaTeX为默认论文主链，DOCX仅显式按需。

详细规则以 `../../core/` 下权威合同为准。v7.2.0--v7.2.2 项目重新进入设计、预处理、绘图或写作时沿用三态 `preprocessing_decision` 并按当前通用审计与论文证据框架复核；历史只读交付不强制反向补 `data_process.m`，更早项目与 `legacy/` 按既有只读兼容规则处理。
