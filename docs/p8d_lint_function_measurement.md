# P8d 大型静态检查器函数分布测量

> 本文件是维护证据，不是新的业务 Authority。`scripts/lint_skill_checks.py` 的检查语义、错误文本和完整门禁仍由现有实现与测试共同约束。

## 目的

P8a 已确认 `scripts/lint_skill_checks.py` 是当前 `scripts/` 中显著最大的维护热点，但“文件大”本身不足以证明应该拆分。P8d 在任何结构拆分前，先把顶层函数数量、`check_*` 顶层检查函数数量以及最长顶层函数的真实行跨度加入 `scripts/measure_infrastructure.py` 的可复算输出。

该测量只回答结构事实：哪些职责是独立顶层函数、哪些函数占据较大连续实现面、是否存在可以在不改变调用顺序和检查集合的前提下按职责分组的候选。它不定义“超过多少行必须拆分”的政策阈值。

## 本批修改边界

- `measure_infrastructure.py` schema 从 `1.0.0` 增量到 `1.1.0`；
- 每个 `scripts/*.py` 行新增 `top_level_function_count`、`top_level_check_function_count` 与最多 10 个 `largest_top_level_functions`；
- 每个函数记录 `name / start_line / end_line / span_lines`，按跨度降序；
- 原有 bytes、nonblank lines、全部函数数量、YAML/workbook 解析调用点与 generated-metadata 测量保持不变；
- 不修改 `lint_skill_checks.py`，不移动任何检查，不更改 CLI、错误文本、检查顺序或 gate；
- 不修改业务 contract、Schema、MATLAB/LaTeX、用户项目或 release carrier。

## 后续结构整理的准入条件

只有下一轮从最新 main 重新运行 `python scripts/measure_infrastructure.py --json` 后，才允许讨论 `lint_skill_checks.py` 的结构拆分。候选拆分必须同时满足：

1. 由真实顶层函数边界形成可识别职责组，而不是按行数机械切片；
2. `scripts/lint_skill.py` 的公开入口、检查调用顺序、错误文本和失败集合保持等价；
3. 不删除或弱化任何历史 drift guard、static contract check、generated check 或完整 CI；
4. 拆分后的专项测试必须证明检查集合没有减少，并继续通过全量 unittest、HSK Skill CI 与 Optimization baseline；
5. 若函数分布不能支持低风险职责拆分，则 P8 在大型 validator 项上应选择“不拆”，而不是为了完成计划强行重构。

因此本批只建立证据，不提前宣称大型 validator 一定需要拆分。
