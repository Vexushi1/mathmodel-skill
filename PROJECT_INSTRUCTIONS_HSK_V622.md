# HSK 项目调用说明 v6.3.4

文件名保留 V622 作为兼容路径。

1. 首先读取 `core/bootstrap.yaml`；
2. 使用 `scripts/resolve_workflow.py` 解析一个或多个意图；
3. 每问以 `classification.objective`、`classification.structures` 和顶层 `capabilities` 分类；
4. 模型锁定后维护项目根目录 `模型论文框架.md`，日常 compact，写作与终审 full；
5. Python 负责求解并输出两类工作簿，MATLAB 读取真实表头绘图；
6. Python starter 必须通过 `hsk_pipeline.run_pipeline()` 执行，不得在导入阶段创建目录、设置随机种子或写工作簿；
7. 正式交付执行解析器返回的 `pre_delivery_gates`；
8. `project_sync` 使用 `python scripts/sync_project.py <project_root> --write --strict --delivery-scope <scope>`；
9. 同步器按阶段检查必需产物、工作簿 Schema、MATLAB 图表链和分层哈希，只传播 stale，不生成模型语义、结果或 passed；
10. `sync_report.yaml` 只有在 gate 成功后才视为可用产物；
11. 命题详细 Pack 仅在明确需要时加载；
12. 最终论文默认 LaTeX，中文国赛保留 `cumcmthesis`。
