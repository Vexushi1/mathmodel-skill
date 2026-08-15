# Scripts v7.4.2

- `lint_skill.py`：检查活动版本、路由、语义治理、通用判定式条件数据预处理、产物闭环、五文件合同、代码质量合同、Schema、兼容层隔离、仓库引用路径、本地 Markdown 链接、全路由 resolver smoke、旧结构残留、Python 语法和生成文件；
- `resolve_workflow.py`：解析意图、`objective`、`structures`、`capabilities`、`preprocessing_decision` 与竞赛类型，返回确定性执行计划；只有 `project_level` 才插入项目级预处理阶段；
- `validate_semantic_governance.py`：检查 Problem Contract、题面—数学—代码语义闭环、Complexity Sanity Check、semantic revision 和 typed dependency stale 传播，不运行赛题代码；
- `validate_code_delivery.py`：按 `preprocessing / primary / analysis` 阶段静态校验实际生成 Python 的完整运行配置与工程质量，不运行赛题代码；
- `validate_user_execution.py`：按当前 `preprocessing_decision` 验收适用的预处理、主求解与深化分析工作簿，以及对应代码/数据哈希和质量门；
- `sync_project.py`：按 active data source 发现条件式预处理产物与每问两个阶段脚本、两个结果工作簿和 `qX_plot.m`，隔离各层哈希并传播产物 stale；
- `validate_project_state.py`、`validate_model_paper_framework.py`：校验机器状态与当前模型论文框架；
- `generate_indexes.py`：重建活动索引与 `MANIFEST.sha256`；
- `score_submission.py`、`hsk_pack_submission.py`、`render_paper.py`：评分、打包和 LaTeX 编译。

v7.4.2 的 Figure Evidence 规则由 `modules/04_figure_evidence.md` 负责：绘图代码生成前动态判断单图、1×2、2×1、1×3、2×2或拆图，不在脚本层写死某一种布局；主比较允许中高饱和、高对比配色，辅助元素降权。

数据主链为：Problem Contract冻结 → 当前附件的非破坏性通用数据审计 → `preprocessing_decision` → 语义闭环 → Complexity Sanity Check → semantic governance。审计至少覆盖完整性、一致性、有效性、重复身份、采样/覆盖、测量质量、模型输入要求和时间因果/信息泄漏。`not_needed` 直接使用原始数据，`question_local` 仅在本问脚本内执行有数学来源的局部变换，`project_level` 才执行 `数据预处理.py` 并验收 `数据预处理结果.xlsx`。共享数据、检测到缺失或过去赛题习惯本身都不是清洗、插值、预测填补或滤波的充分条件。

缺失处理必须先判断缺失模式、变量语义和模型需求，再在保持缺失、删除、插值、统计填补、模型填补或预测填补之间选择。预测填补只用于恢复缺测输入；赛题本身要求的预测输出仍属于核心建模。

每问 Python 主链为：当前数据事实源 → `问题X求解.py` → 主代码工程质量门 → 用户运行 → 主工作簿验收并冻结主脚本 → 独立 `问题X结果深化分析.py` → 深化代码质量门 → 用户运行 → 深化工作簿验收。运行配置分别嵌入对应阶段 Python 和工作簿，不产生独立配置、说明或校验报告。

仓库维护至少执行：

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/generate_indexes.py --check
```
