# P7 条件式结果分析与附录

## 范围

P7 只处理两个结构性问题：03B 结果深化分析是否需要执行，以及 LaTeX 附录是否需要启用。它不改变 Model Approval、主求解 PQS、主数值证据复核、full-fidelity/no-degradation 政策，也不升级 Skill 版本。

## Analysis Necessity Gate

主工作簿 accepted 后先执行 Gate。只有题目/用户明确要求、存在未关闭的 material post-primary risk、正文准备提出超出当前计算世界的稳定性/鲁棒性主张、核心结果靠近边界，或真实主结果暴露结构/外推风险等条件成立时，03B 才进入 `required` 分支。

`not_required` 只在主结果数值有效性已通过、题目直接答案不依赖 alternative-world 证据、没有未关闭的 material 03B 风险且计划正文 claim 不超出当前计算世界时成立。该状态必须带非空 `result_analysis_requirement_reason`，并且不能被解释为“鲁棒性已通过”。

下游统一消费 `validated_results`：每个作用域小问均需要 accepted 主结果，并满足以下二者之一：

1. 真实 03B 工作簿 accepted 且 `result_analysis_status=passed`；
2. `result_analysis_status=not_required` 且存在非空 requirement reason。

第二种情况不会伪造 `accepted_result_analysis_workbook` 或 `result_analysis_workbook`。

## 附录 Gate

CUMCM 模板中的 appendix 槽位保留，但改为 `required=false`、`default_active=false`。仅在官方规则要求，或存在确实应放在正文之外但需要保留的长代码、长证明/推导、扩展表格、复现材料时启用。没有真实材料时禁止生成空附录。

## 兼容性

旧项目中的 `pending/passed/failed/redo_required` 语义保持不变；新增 `not_required` 是加法式状态。旧的真实 03B 工作簿路径、哈希层、stale 传播与 accepted-workbook 语义保持不变。

## 验证

P7 新增回归覆盖：

- 有理由的 `not_required` 可产生 `validated_results`，但不会产生伪 analysis-workbook artifact；
- 缺少 requirement reason 时 fail closed；
- workflow router 将 result_analysis 标记为条件模块；
- figure_evidence 只在 `result_analysis_status=passed` 时要求 03B 工作簿；
- appendix 默认关闭且主模板中没有活动的 appendix input。
