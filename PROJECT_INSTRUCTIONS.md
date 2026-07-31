# HSK 项目调用说明

当前活动规则以 `core/bootstrap.yaml` 指向的权威文件为准。

1. 首先读取 `core/bootstrap.yaml`；
2. 使用 `scripts/resolve_workflow.py` 解析一个或多个意图；
3. 每问以 `classification.objective`、`classification.structures` 和顶层 `capabilities` 分类；
4. 模型锁定后维护项目根目录 `模型论文框架.md`，日常使用 compact，跨聊天、完整写作和终审使用 full；
5. Python 负责求解、验证和两类标准工作簿，MATLAB 精确读取真实表头绘制正式结果图；
6. Python starter 统一通过 `hsk_pipeline.run_pipeline()` 执行，不得在导入阶段创建目录、设置随机种子或写工作簿；
7. 默认完整流程在结果、验证和图表锁定后直接进入 LaTeX，并在源码中持续修改；
8. DOCX 仅在用户明确要求 Word 审阅、批注、协作或特定提交格式时加载独立路由，不是 LaTeX 前置；
9. 正式交付执行解析器返回的 `pre_delivery_gates`；
10. `project_sync` 使用 `python scripts/sync_project.py <project_root> --write --strict --delivery-scope <scope>`；
11. 同步器按 exact scope 检查必需产物、工作簿 Schema、MATLAB 图表链和分层哈希，只传播 stale，不生成模型语义、结果或 passed；
12. `sync_report.yaml` 只有在 gate 成功后才视为可用产物；
13. 命题详细 Pack 仅在明确需要证明或命题计划非零时加载；
14. 中文国赛终稿保留 `cumcmthesis`。

活动入口使用稳定文件名：`PROJECT_INSTRUCTIONS.md`、`RUNTIME_ROUTER.md`、`SKILL_FILE_INDEX.md` 和 `TEMPLATE_INDEX.md`。历史版本化文件名仅保留兼容指针。
