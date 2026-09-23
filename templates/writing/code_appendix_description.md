# 附录代码说明模板

以下模板按 `core/output_contract.yaml` 的 current conditional layout 填写。03B 项只在 Analysis Necessity Gate=`required` 时列入；Gate=`not_required` 时不为凑结构虚构深化代码、工作簿或稳健性结论。

| 项目 | 内容 |
|---|---|
| 程序名称 | 按项目根后端及 `core/output_contract.yaml#per_question.solver_scripts` 填对应主入口（如 `问题X求解/问题X求解.py` 或 `问题X求解/qX_solver.m`）和 `问题X求解/qX_plot.m`；Gate=`required` 时追加同语言独立深化入口（如 `问题X求解/问题X结果深化分析.py` 或 `问题X求解/qX_analysis.m`），并列明已声明的必要辅助源码 |
| 输入 | 主求解读取当前合法数据事实源和已锁定参数；Gate=`required` 时，深化分析读取已验收主结果工作簿及必要当前数据事实源 |
| 功能 | 主求解代码完成模型求解与主结果质量检查；主工作簿 accepted 后冻结该脚本并执行 Analysis Necessity Gate；仅 Gate=`required` 时由独立深化代码完成题目专属敏感性、鲁棒性、多算法、阈值或结构分析；MATLAB 主结果图读取主工作簿，只有实际使用 03B evidence 的图才读取条件存在的深化工作簿 |
| 主要输出 | 必有：`问题X求解/问题X求解结果.xlsx`；Gate=`required` 且 03B 执行后追加：`问题X求解/问题X结果深化分析.xlsx` |
| 复现顺序 | 按项目根后端运行当前主入口 → 验收主工作簿并冻结主脚本 → Analysis Necessity Gate → `required`：按同一项目后端运行独立深化入口并验收 `问题X结果深化分析.xlsx`；`not_required`：记录非空理由并跳过 03B → 运行 `qX_plot.m` → LaTeX 编译 |

按项目根唯一后端列明主/条件式深化入口、必要源码依赖与本地运行顺序；`RUN_CONFIG` 与回执中的 backend 记录实际运行事实并须与根策略一致，协议版本按执行 Authority 的阶段映射，项目级预处理仍为 Python。

完整运行配置分别写在实际激活阶段的代码 和对应工作簿的 `运行配置` 表中。求解目录默认不包含独立配置、说明、校验报告、图表目录或自动导出的图片。Gate=`not_required` 只表示当前计划正文 claim 不需要 alternative-world 证据，不等价于“稳健性已通过”。
