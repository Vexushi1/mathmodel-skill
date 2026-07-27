# HSK 项目调用说明 v6.3.0

文件名保留 V622 作为兼容路径。

1. 首先读取 `core/bootstrap.yaml`；
2. 使用 `scripts/resolve_workflow.py` 解析一个或多个意图；
3. 每问按 objective、structures、capabilities 分类；
4. 模型锁定后维护项目根目录 `模型论文框架.md`；
5. Python 负责求解并输出两类工作簿，MATLAB 读取真实表头绘图；
6. 每次正式交付前运行 `python scripts/sync_project.py <project_root> --write --strict`；
7. 同步器只做发现、哈希和 stale 传播，不生成模型语义、结果或 passed；
8. 命题详细 Pack 仅在明确需要时加载；
9. 最终论文默认 LaTeX，中文国赛保留 `cumcmthesis`。
