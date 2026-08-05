# HSK 项目调用说明

当前活动规则以 `core/bootstrap.yaml` 指向的权威文件为准。

1. 首先读取 `core/bootstrap.yaml`；
2. 使用 `scripts/resolve_workflow.py` 解析一个或多个意图；
3. 每问以 `classification.objective`、`classification.structures` 和顶层 `capabilities` 分类；
4. 模型锁定后维护项目根目录 `模型论文框架.md`；
5. 每问新建一个 `问题X求解/`，默认只保留 `问题X求解.py`、`问题X求解结果.xlsx`、`问题X结果深化分析.xlsx` 和 `qX_plot.m`；
6. Python 先完成完整主求解，不得因模块分离删除求解器状态、外样本精度、约束、残差、收敛或可复算检查；
7. 主结果质量报告写入同目录 `问题X求解结果.xlsx` 的 `主结果质量门` 工作表，全部通过后才能进入结果深化分析；
8. 结果深化方法根据题目、模型、数据、主结果表现和评委风险选择，可为敏感性、鲁棒性、多算法、结构稳健性、阈值、异质性、误差分解或外样本稳定性；
9. 主工作簿验收后覆盖更新同一个 `问题X求解.py`，深化分析写入同目录 `问题X结果深化分析.xlsx`，不得另建结果深化分析 Python 脚本；
10. 深化分析工作簿必须包含 `分析设计`、至少一个实质分析表和 `结论稳定性汇总`；
11. 深化分析发现主结论不可靠时，标记下游 stale，回退模型设计或主求解并重新计算；
12. MATLAB 使用同目录 `qX_plot.m` 精确读取两个真实工作簿，不重新计算核心结果，默认不创建图表子目录或自动导出图片；
13. 默认完整流程在结果和图表锁定后直接进入 LaTeX；
14. DOCX 仅在用户明确要求 Word 审阅、批注、协作或特定提交格式时加载独立路由，不是 LaTeX 前置；
15. 正式交付执行解析器返回的 `pre_delivery_gates`；
16. `project_sync` 使用 `python scripts/sync_project.py <project_root> --write --strict --delivery-scope <scope>`；
17. 同步器按 exact scope 检查必需产物、工作簿 Schema、MATLAB 图表链和分层哈希，只传播 stale，不生成模型语义、结果或 passed；
18. 旧 `结果数据表/问题X/`、独立结果深化脚本和 `问题X敏感性与鲁棒性结果.xlsx` 仅作历史项目只读兼容，新项目不再生成；
19. 命题详细 Pack 仅在明确需要证明或命题计划非零时加载；
20. 中文国赛终稿保留 `cumcmthesis`。

活动入口使用稳定文件名：`PROJECT_INSTRUCTIONS.md`、`RUNTIME_ROUTER.md`、`SKILL_FILE_INDEX.md` 和 `TEMPLATE_INDEX.md`。历史版本化文件名仅保留兼容指针。

## v6.6.0 用户执行完整版代码

默认不由助手运行赛题主求解或结果深化分析程序。助手交付题目专属完整版代码、嵌入式完整运行配置和聊天内运行说明，用户运行后返回标准工作簿；工作簿通过运行配置、代码/数据哈希和质量门验收后，工作流才继续。禁止自动降采样、粗网格、短时域、少重复、宽容差、静默求解器 fallback 或用轻量结果代替正式结果。
