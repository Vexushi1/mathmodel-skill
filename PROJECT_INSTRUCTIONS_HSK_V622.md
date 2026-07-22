# HSK 数学建模项目指令 v6.2.4

本项目默认执行 HSK 模块化数学建模工作流。最高原则和硬规则只定义于 `core/hsk_core_policy.md`；本文件仅声明项目级调用方式。文件名保留 V622 作为稳定兼容路径。

1. 新任务先用 `core/workflow_router.yaml` 判定模块，并按每个小问输出主/次题型与 capability 标志；禁止全包无差别读取。
2. 可用 `scripts/resolve_workflow.py` 将意图、题型和竞赛转换为确定性的模块/Pack 加载计划。
3. 赛题、附件数据表和各问 Python 脚本直接放在项目根目录；Python 只承担数据处理、模型求解、检验、敏感性、鲁棒性和 Excel 结果输出。
4. 每问固定输出到 `结果数据表/问题X/`，标准文件为 `问题X求解结果.xlsx` 与 `问题X敏感性与鲁棒性结果.xlsx`；不得再创建 `问题X结果数据/`。
5. 每问唯一 MATLAB 入口为同目录 `q{x}_plot.m`，脚本直接读取同目录工作簿，正式图显式导出到同级 `图表/`。
6. 不再默认创建 `数据/`、`Python求解/` 或 `MATLAB绘图/` 中间层；路径分别由 Python 的 `__file__` 和 MATLAB 的 `mfilename("fullpath")` 定位。
7. 工作表、字段、单位和非空规则执行 `core/workbook_schema.yaml`；约束、均衡、守恒、离散和收敛工作表由 capability 决定。
8. 写入器和 `scripts/hsk_check_artifact.py` 复用 `result_io.py` 的同一校验实现；不适用分析使用 `适用性说明`。
9. MATLAB 不重新计算核心结果；图窗默认保留，导出显式触发。简单问题的 `q{x}_plot.m` 默认自包含读取、校验和样式，不强制拆分辅助函数。
10. DOCX 用于前期迭代；LaTeX 草稿先执行 AI 模板感清除，再按 `core/compile_profiles.yaml` 编译最终 PDF。
11. 跨聊天或复杂项目状态按 `core/project_state.schema.yaml` 维护，并由 `scripts/validate_project_state.py` 检查阶段、证据、哈希和失效状态。
12. 题型知识、竞赛格式和交付规范分别按需加载 `packs/task/`、`packs/competition/`、`packs/artifact/`。
13. Nature 图集只通过 `assets/figure_assets.yaml` 按需引用，不作为数据或固定绘图模板。
14. 旧 Stage、反馈层、句式语料和旧 Python 绘图模板只保存在 `legacy/`，不进入活动索引与默认运行。
