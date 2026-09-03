# 审查交付适配器

本 Pack 只适配 `modules/06_review_delivery.md` 的终审语义，不复制检查规则。审查报告先按致命、重要、一般问题排序，再给六维评分；每个 finding 必须给出规则来源、验证方式、位置、证据、原因和可执行修复动作，不能只给总分。

审查前执行：

```bash
python scripts/validate_model_paper_framework.py 模型论文框架.md --state state/project_state.yaml
python scripts/validate_project_state.py state/project_state.yaml --project-root .
python scripts/sync_project.py . --write --strict --delivery-scope submission
```

重点核对：当前模型口径、Formula Trace、Algorithm Trace 与 `not_needed / stepwise / pseudocode` 呈现选择、命题与证明、条件式预处理、主结果质量门、独立结果深化分析、代码—工作簿—MATLAB—正文证据链、LaTeX 编译和提交包内容。

执行 `final_review_and_delivery` 时读取当前 competition profile、competition Pack、edition rule verification、最终 PDF、`latex_audit_report.yaml` 与 `compile_report.yaml`，并按 `modules/06_review_delivery.md#Final-Submission-Compliance-Evidence-Sweep` 完成八类动态 coverage。新生成的正式终审报告使用 `templates/review/final_review_matrix.yaml`；旧 `scores + hard_fail + evidence` 报告仍可作为兼容输入。

Matrix 中 `unverifiable` 不得改写成 `passed`；未解决 `blocking` 必须有允许的 Hard Fail code；`review_required` 和 warning 均保留证据与处置状态。评分继续使用显式六维分数，不按 finding 数量自动扣分。

对 `stepwise/pseudocode` 小问，核对 current Algorithm ID、核心输入/状态、操作、停止条件和输出，并人工确认论文算法与真实 Python 实现、约束/命题锚点及工作簿结果一致；`not_needed` 小问不因缺少算法框扣分，也不应残留装饰性 Algorithm 1。机器只核确定性字段和锚点存在性，不从伪代码文字推断算法正确性或收敛性。

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

`review_report` 和 `final_review_matrix.yaml` 都是内部终审产物，不自动进入 official package。正式提交内容只服从当前已核验 `edition_rules.submission_files` 与现有 submission package validator。
