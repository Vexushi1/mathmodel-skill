# Scripts

- `lint_skill.py`：检查活动版本、路由、语义治理、通用判定式条件数据预处理、产物闭环、五文件合同、代码质量合同、写作策略合同、Schema、兼容层隔离、仓库引用路径、本地 Markdown 链接、全路由 resolver smoke、活动写作模板旧结构残留、Python 语法和生成文件；
- `resolve_workflow.py`：解析意图、`objective`、`structures`、`capabilities`、`preprocessing_decision` 与竞赛类型，返回确定性执行计划；只有 `project_level` 才插入项目级预处理阶段；
- `validate_semantic_governance.py`：检查 Problem Contract、题面—数学—代码语义闭环、Complexity Sanity Check、semantic revision 和 typed dependency stale 传播，不运行赛题代码；
- `validate_code_delivery.py`：按 `preprocessing / primary / analysis` 阶段静态校验实际生成 Python 的完整运行配置与工程质量，不运行赛题代码；
- `validate_user_execution.py`：按当前 `preprocessing_decision` 验收适用的预处理、主求解与深化分析工作簿，以及对应代码/数据哈希和质量门；
- `audit_paper_prose.py`：对最终 LaTeX 主文件执行非破坏性成稿审计；默认只报告 `pass / warning / review_required`，`--strict` 只阻断结构性 `review_required`，不自动改写正文；
- `sync_project.py`：按 active data source 发现条件式预处理产物与每问两个阶段脚本、两个结果工作簿和 `qX_plot.m`，隔离各层哈希并传播产物 stale；
- `validate_project_state.py`、`validate_model_paper_framework.py`：校验机器状态与当前模型论文框架；
- `generate_indexes.py`：重建活动索引与 `MANIFEST.sha256`；
- `score_submission.py`、`hsk_pack_submission.py`、`render_paper.py`：评分、打包和 LaTeX 编译。

v7.5.2 新增根 `SKILL.md` 与 packaged `skills/mathmodel-skill/SKILL.md` 的运行时入口合同一致性检查；两入口都只委托 bootstrap/resolver/route authority，不各自建立第二套运行规则。版本一致性检查同时避免稳定工具说明、legacy 归档说明和 resolver docstring 成为无意义的 release carrier。

v7.5.1 将 bootstrap 收回为最小启动索引，并把 taxonomy/reasoning 改为 route-specific lazy load；v7.5.0 建立跨比赛 Source→Derivation→Destination、共享基础、跨问增量、结构化简优先和数值参数证据。

v7.4.5 保留 v7.4.4 的自然论文流，并清理证明机器契约歧义：默认 `paragraph_first`，要求逻辑单元清晰，只有明显多阶段证明才使用 2--6 个编号步骤。prose audit 检查高密度否定/转折、重复段首主语、重复固定图表句式及独立结论章、H1/A1、缺“问题提出”/“核心模型汇总”等结构回退；普通单次使用“但/然而”不判错。

正文写作仍由 `modules/05_writing/latex.md` 唯一负责，`modules/05_writing/ai_cleanup.md` 执行模板化和自然度检查。`模型的评价与推广 / 模型的改进、评价与推广` 两级策略保持不变。v7.4.3 建立的假设/符号分章、自然假设编号、短上标优先、表上图下、三线表短内容居中和模型评价规范继续保持；v7.4.2 引入的 Figure Evidence 动态布局和高对比配色也继续保持。

数据主链为：Problem Contract冻结 → 当前附件的非破坏性通用数据审计 → `preprocessing_decision` → 语义闭环 → Complexity Sanity Check → semantic governance。审计至少覆盖完整性、一致性、有效性、重复身份、采样/覆盖、测量质量、模型输入要求和时间因果/信息泄漏。`not_needed` 直接使用原始数据，`question_local` 仅在本问脚本内执行有数学来源的局部变换，`project_level` 才执行 `数据预处理.py` 并验收 `数据预处理结果.xlsx`。共享数据、检测到缺失或过去赛题习惯本身都不是清洗、插值、预测填补或滤波的充分条件。

缺失处理必须先判断缺失模式、变量语义和模型需求，再在保持缺失、删除、插值、统计填补、模型填补或预测填补之间选择。预测填补只用于恢复缺测输入；赛题本身要求的预测输出仍属于核心建模。

每问 Python 主链为：当前数据事实源 → `问题X求解.py` → 主代码工程质量门 → 用户运行 → 主工作簿验收并冻结主脚本 → 独立 `问题X结果深化分析.py` → 深化代码质量门 → 用户运行 → 深化工作簿验收。运行配置分别嵌入对应阶段 Python 和工作簿，不产生独立配置、说明或校验报告。

仓库维护至少执行：

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/generate_indexes.py --check
```
