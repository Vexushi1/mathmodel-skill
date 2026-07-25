# 审查交付适配器

审查报告按致命/重要/一般问题排序，并给可执行修改位置、原因和修复方案。评分必须说明证据与扣分来源，不能只给总分。

审查前先执行：

```bash
python scripts/validate_model_paper_framework.py 模型论文框架.md --state state/project_state.yaml
python scripts/validate_project_state.py state/project_state.yaml --project-root .
python scripts/hsk_check_artifact.py . --mode full
```

重点核对：框架是否只保留当前有效口径；已求解小问是否有 current 结果摘要；工作簿数值、MATLAB 图标题/图注、正文和附录是否一致；单图是否有 `title`、多面板是否有 `sgtitle`；每次正式交付是否包含完整最新版框架。

## 评分执行

评分权重以 `config/review_weights.json` 为唯一机器配置。准备一份 YAML/JSON 评分输入：

```yaml
scores:
  problem_and_mechanism: 90
  mathematical_closure: 88
  data_and_validation: 84
  results_and_figures: 86
  writing_and_layout: 82
  reproduction_and_delivery: 85
hard_fail: []
evidence:
  problem_and_mechanism: 模型论文框架、问题审计表与机理图合同
```

执行：

```bash
python scripts/score_submission.py review_input.yaml --output review_score.yaml
```

权重总和、维度完整性、分值范围和硬否决代码由脚本校验。出现硬否决时不得用加权总分掩盖，先按 `reject_or_major_rework` 处理。
