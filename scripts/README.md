# Scripts v7.0.0

- `lint_skill.py`：检查活动版本、路由、产物闭环、五文件合同、代码质量合同、Schema、旧结构残留、Python 语法和生成文件；
- `resolve_workflow.py`：解析意图、`objective`、`structures`、`capabilities` 与竞赛类型，返回确定性执行计划；
- `validate_code_delivery.py`：按阶段静态校验主求解或结果深化分析 Python 的完整运行配置与工程质量，不运行赛题代码；
- `validate_user_execution.py`：验收用户返回的两个工作簿及运行配置、对应阶段代码/数据哈希和数值质量门；
- `sync_project.py`：发现每问两个阶段脚本、两个工作簿和 `qX_plot.m`，隔离两阶段哈希并校验、传播 stale；
- `validate_project_state.py`、`validate_model_paper_framework.py`：校验机器状态与当前模型论文框架；
- `generate_indexes.py`：重建活动索引与 `MANIFEST.sha256`；
- `score_submission.py`、`hsk_pack_submission.py`、`render_paper.py`：评分、打包和 LaTeX 编译。

每问 Python 主链为：`问题X求解.py` → 主代码工程质量门 → 用户运行 → 主工作簿验收并冻结主脚本 → 独立 `问题X结果深化分析.py` → 深化代码质量门 → 用户运行 → 深化工作簿验收。运行配置分别嵌入对应阶段 Python 和工作簿，不产生独立配置、说明或校验报告。

仓库维护至少执行：

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/generate_indexes.py --check
```
