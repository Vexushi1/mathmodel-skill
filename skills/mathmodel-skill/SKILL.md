---
name: mathmodel-skill
version: 7.0.0
summary: HSK mathematical-modeling workflow with full-fidelity solving, separate primary/result-analysis Python stages, code-quality enforcement, result gates, MATLAB evidence figures and LaTeX-first writing.
triggers: [数学建模, 数模, CUMCM, 国赛, MCM, ICM, 电工杯, 认证杯, Python求解, MATLAB绘图, LaTeX, DOCX]
---

# HSK 数学建模模块化工作流 v7.0.0

1. 从本目录定位仓库根目录 `../..`，读取 `../../core/bootstrap.yaml`；
2. 使用 `../../scripts/resolve_workflow.py` 获取任务执行计划；
3. 每问最终维护两个 Python、两个标准工作簿和一个 `qX_plot.m`：主求解脚本 accepted 后冻结，结果深化分析使用独立脚本；
4. 两个代码阶段都必须通过 `../../core/code_quality_contract.yaml` 与 `../../scripts/validate_code_delivery.py`；
5. 用户完整运行后，由 `validate_user_execution.py` 验收工作簿、对应阶段代码/数据哈希和质量门；
6. 深化分析不稳定时回退模型或主求解并传播 stale；只改深化脚本不得污染已通过的主结果质量状态；
7. MATLAB只读工作簿绘图，LaTeX为默认论文主链，DOCX仅显式按需。

详细规则以 `../../core/` 下权威合同为准，v6.6.x 单脚本项目和 `legacy/` 仅作只读兼容，不参与新项目默认生成。
