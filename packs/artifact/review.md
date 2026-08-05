# 审查交付适配器

审查报告按致命、重要、一般问题排序，并给出可执行修改位置、原因和修复方案。评分必须说明证据与扣分来源，不能只给总分。

审查前执行：

```bash
python scripts/validate_model_paper_framework.py 模型论文框架.md --state state/project_state.yaml
python scripts/validate_project_state.py state/project_state.yaml --project-root .
python scripts/sync_project.py . --write --strict --delivery-scope submission
```

重点核对：当前模型口径、命题与证明、主结果质量门、深化分析、代码—工作簿—MATLAB—正文证据链、LaTeX 编译和提交包内容。每问数值目录必须符合四文件合同；旧目录只能作为只读兼容输入。

评分权重以 `config/review_weights.json` 为唯一机器配置。出现硬否决时不得用加权总分掩盖，先按 `reject_or_major_rework` 处理。
