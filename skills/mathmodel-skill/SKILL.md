---
name: mathmodel-skill
version: 7.2.1
summary: HSK mathematical-modeling workflow with Problem Contract freezing, semantic closure, complexity sanity checks, evidence-driven conditional data preprocessing, dependency-aware stale propagation, full-fidelity solving, separate primary/result-analysis Python stages, MATLAB evidence figures and LaTeX-first writing.
triggers: [数学建模, 数模, CUMCM, 国赛, MCM, ICM, 电工杯, 认证杯, 数据预处理, Python求解, MATLAB绘图, LaTeX, DOCX]
---

# HSK 数学建模模块化工作流 v7.2.1

1. 从本目录定位仓库根目录 `../..`，读取 `../../core/bootstrap.yaml`；
2. 使用 `../../scripts/resolve_workflow.py` 获取任务执行计划；
3. 正式模型与代码前先完成 Problem Contract、非破坏性数据审计、`preprocessing_decision`、题面—数学—代码语义闭环和 Complexity Sanity Check，并运行 `../../scripts/validate_semantic_governance.py`；
4. `preprocessing_decision` 只有三种：`not_needed`、`question_local`、`project_level`。共享同一原始数据源本身不是 `project_level` 的充分条件；
5. 只有 `project_level` 才创建 `数据预处理/数据预处理.py` 与 `数据预处理结果.xlsx`；`not_needed` 直接使用原始数据，`question_local` 只在本问脚本内做有数学来源的局部变换；
6. 缺失填补、异常删除、插值、平滑、滤波、去趋势、归一化、标准化和重采样等操作必须有数据、机理或模型必要性证据；
7. 模型语义或数据处理判定变化时递增 semantic revision，并按 data / parameter / model / result 依赖递归传播 stale；
8. 每问最终维护两个题目专属 Python：`问题X求解.py` 和 `问题X结果深化分析.py`，并保留两个标准工作簿与一个 `qX_plot.m`；主求解脚本 accepted 后冻结，结果深化分析使用独立脚本；
9. 实际生成的 `preprocessing / primary / analysis` 代码阶段都必须通过 `../../core/code_quality_contract.yaml` 与 `../../scripts/validate_code_delivery.py`；
10. 用户完整运行后，由 `validate_user_execution.py` 按当前数据事实源验收工作簿、对应阶段代码/数据哈希和质量门；
11. 深化分析不稳定时按原因回退模型、条件式预处理或主求解并传播 stale；只改深化脚本不得污染已通过的主结果质量状态；
12. MATLAB只读真实结果数据绘图，LaTeX为默认论文主链，DOCX仅显式按需。

详细规则以 `../../core/` 下权威合同为准。v7.2.0 项目重新进入设计/求解时先补齐 `preprocessing_decision`；更早项目与 `legacy/` 按既有只读兼容规则处理。
