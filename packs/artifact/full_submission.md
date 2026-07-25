# Artifact Pack：完整提交包

提交包至少包含：项目根目录当前有效的 `模型论文框架.md`、论文源文件与 PDF、题目/附件说明和各问 Python 脚本、`结果数据表/问题X/` 下每问两类标准工作簿与同目录 `q{x}_plot.m`、`结果数据表/问题X/图表/` 中保留简洁 MATLAB 标题的正式结果图、核心可编辑机理图和运行说明。

`模型论文框架.md` 必须通过 `scripts/validate_model_paper_framework.py`，且与 `state/project_state.yaml`、两类标准工作簿、MATLAB 图标题/图注映射和最终论文一致。文件只保留当前有效口径，不能把旧模型、旧参数、旧约束或旧结果与新版并列打包。

不得为提交包额外复制出 `Python求解/`、`MATLAB绘图/` 或 `问题X结果数据/` 重复目录。复杂项目按需在对应问题目录生成 `run_info.json`、`result_manifest.yaml` 和 `matlab_figure_handoff.json`，不得将其机械写入论文正文。
