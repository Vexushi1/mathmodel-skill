# 审查交付适配器

审查报告按致命、重要、一般问题排序，并给出可执行修改位置、原因和修复方案。评分必须说明证据与扣分来源，不能只给总分。

审查前执行：

```bash
python scripts/validate_model_paper_framework.py 模型论文框架.md --state state/project_state.yaml
python scripts/validate_project_state.py state/project_state.yaml --project-root .
python scripts/sync_project.py . --write --strict --delivery-scope submission
```

重点核对：当前模型口径、命题与证明、条件式预处理、主结果质量门、独立结果深化分析、代码—工作簿—MATLAB—正文证据链、LaTeX 编译和提交包内容。

新项目每问数值目录必须符合当前五文件合同：

```text
问题X求解/
├─ 问题X求解.py
├─ 问题X求解结果.xlsx
├─ 问题X结果深化分析.py
├─ 问题X结果深化分析.xlsx
└─ qX_plot.m
```

主工作簿 accepted 后必须冻结主求解脚本，深化分析使用独立 Python；旧单脚本四文件目录、旧 `结果数据表/问题X/` 和旧敏感性与鲁棒性工作簿只能作为历史项目只读兼容输入。

若 `preprocessing_decision=project_level`，同时检查 `数据预处理/数据预处理.py`、已验收 `数据预处理结果.xlsx` 和 Figure Evidence 阶段的 `data_process.m`；若为 `not_needed/question_local`，不得因不存在全局预处理目录而扣分。

评分权重以 `config/review_weights.json` 为唯一机器配置。出现硬否决时不得用加权总分掩盖，先按 `reject_or_major_rework` 处理。
