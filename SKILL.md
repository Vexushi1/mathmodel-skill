---
name: mathmodel-skill
version: 7.0.0
summary: HSK mathematical-modeling workflow with full-fidelity user execution, separate primary/result-analysis Python stages, explicit numerical quality gates, code-quality enforcement, MATLAB evidence figures and LaTeX-first writing.
triggers: [数学建模, 数模, CUMCM, 国赛, MCM, ICM, 电工杯, 认证杯, 建模论文, 模型论文框架, 主结果质量, 结果深化分析, Python求解, MATLAB绘图, LaTeX, DOCX]
---

# HSK 数学建模模块化工作流 v7.0.0

## 默认执行

先读 `core/bootstrap.yaml`，再由 `scripts/resolve_workflow.py` 按任务加载模块。赛题数值代码由用户本地以 `full_fidelity` 运行；助手生成并静态检查代码，不运行赛题代码、不自动降采样、不静默切换求解器。

每问完成数值阶段后默认恰好包含：

```text
问题X求解/
├─ 问题X求解.py
├─ 问题X求解结果.xlsx
├─ 问题X结果深化分析.py
├─ 问题X结果深化分析.xlsx
└─ qX_plot.m
```

完整运行配置分别嵌入对应阶段 Python 并写入对应工作簿；运行步骤和校验结果只在聊天或标准输出中返回。主工作簿验收后冻结 `问题X求解.py`，随后独立生成 `问题X结果深化分析.py`，不得为深化分析覆盖改写主求解脚本。

## 主链

```text
逐字审题 → 两条模型路线 → 变量/假设/公式/约束闭合
→ Python完整主求解 → 主代码质量门 → 用户完整运行
→ 主结果质量门 → 独立Python结果深化分析 → 深化代码质量门 → 用户完整运行
→ 稳定性验收/必要时回退重算
→ MATLAB读取两个真实工作簿绘图 → LaTeX直写 → 编译与终审
```

代码工程质量由 `core/code_quality_contract.yaml` 唯一定义并由 `scripts/validate_code_delivery.py` 分别检查两个 Python；主结果和工作簿质量分别由 `core/workbook_schema.yaml` 与 `scripts/validate_user_execution.py` 验收。目录与正式交付以 `core/output_contract.yaml` 为准。

MATLAB 默认只保留图窗，不在求解目录创建 `图表/` 或自动导出。DOCX 仅在用户显式要求时加载，不是 LaTeX 前置。v6.6.x 单脚本项目与 `legacy/` 只作历史和只读兼容，不参与新项目默认生成。
