# Scripts v6.6.0

- `lint_skill.py`：检查活动版本、路由、产物闭环、四文件合同、旧结构残留、Schema、Python 语法和生成文件；
- `resolve_workflow.py`：解析意图、`objective`、`structures`、`capabilities` 与竞赛类型，返回确定性执行计划；
- `validate_code_delivery.py`：静态校验每问唯一 Python 脚本，不运行赛题代码；
- `validate_user_execution.py`：验收用户返回的两个工作簿及运行配置、哈希和质量门；
- `sync_project.py`：发现每问唯一脚本、两个工作簿和 `qX_plot.m`，校验并传播 stale；
- `validate_project_state.py`、`validate_model_paper_framework.py`：校验机器状态与当前模型论文框架；
- `generate_indexes.py`：重建活动索引与 `MANIFEST.sha256`；
- `score_submission.py`、`hsk_pack_submission.py`、`render_paper.py`：评分、打包和 LaTeX 编译。

每问 Python 主链为：主求解版本 → 用户运行 → 主工作簿验收 → 覆盖更新同一脚本 → 分析阶段 → 深化工作簿验收。运行配置嵌入 Python 和工作簿，不产生独立配置、说明或校验报告。

仓库维护至少执行：

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/generate_indexes.py --check
```
