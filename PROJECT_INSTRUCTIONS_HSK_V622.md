# HSK 数学建模项目指令 v6.2.2

本项目默认执行 HSK 模块化数学建模工作流。最高原则和硬规则只定义于 `core/hsk_core_policy.md`；本文件仅声明项目级调用方式。

1. 新任务先用 `core/workflow_router.yaml` 判定模块和题型标签，禁止全包无差别读取。
2. Python 只承担数据处理、模型求解、检验、敏感性、鲁棒性和 Excel 结果输出。
3. 每问固定输出到 `结果数据表/问题X/问题X结果数据/`，标准文件为 `问题X求解结果.xlsx` 与 `问题X敏感性与鲁棒性结果.xlsx`。
4. 工作表、字段、单位和非空规则执行 `core/workbook_schema.yaml`；不适用分析使用 `适用性说明`，不得输出空表。
5. MATLAB 每问只交付一个自包含文件 `MATLAB绘图/问题X/QX_plot.m`，一次运行生成该问题全部结果、诊断、敏感性和鲁棒性图；不得重新计算核心结果或额外交付辅助 `.m` 文件。
6. 正式图按 `single`、`layered`、`multi-panel`、`hybrid` 四级选择；重点支持柱状+折线、散点+模型线+区间带、箱线+散点、小提琴+箱线/中位数+散点等同轴层叠组合图，并允许多面板中的面板继续使用层叠图。
7. 正式图执行 `templates/figure/scientific_composite_system.md`：采用高对比固定颜色角色、背景到结论的图层顺序、双轴准入和缩放可读性检查。
8. `QX_plot.m` 默认保留全部可见图窗，导出由同一文件内的显式开关在人工调整后触发。
9. DOCX 用于前期迭代，LaTeX 用于最终提交；中文国赛保留 `cumcmthesis`。
10. LaTeX 编译按 `core/compile_profiles.yaml` 执行，中文国赛默认 XeLaTeX → Biber → XeLaTeX → XeLaTeX。
11. 跨聊天或复杂项目状态按 `core/project_state.schema.yaml` 维护。
12. 题型知识、竞赛格式和交付规范分别按需加载 `packs/task/`、`packs/competition/`、`packs/artifact/`。
13. 旧 Stage、反馈层、句式语料和旧 Python/MATLAB 分散绘图模板只保存在 `legacy/`，不得默认调用。
