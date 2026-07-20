# HSK 数学建模项目指令 v6.2.1

本项目默认执行 HSK 模块化数学建模工作流。最高原则和硬规则只定义于 `core/hsk_core_policy.md`；本文件仅声明项目级调用方式。

1. 新任务先用 `core/workflow_router.yaml` 判定模块，禁止全包无差别读取。
2. Python 只承担数据处理、模型求解、检验、敏感性、鲁棒性和 Excel 结果输出。
3. 每问固定输出到 `结果数据表/问题X/问题X结果数据/`，标准文件为 `问题X求解结果.xlsx` 与 `问题X敏感性与鲁棒性结果.xlsx`。
4. MATLAB 读取上述工作簿绘制正式结果图，不重新计算核心结果；图窗默认保留，导出显式触发。
5. DOCX 用于前期迭代，LaTeX 用于最终提交；中文国赛保留 `cumcmthesis`。
6. 题型知识、竞赛格式和交付规范分别按需加载 `packs/task/`、`packs/competition/`、`packs/artifact/`。
7. 旧 Stage、反馈层、句式语料和旧 Python 绘图模板只保存在 `legacy/`，不得默认调用。
