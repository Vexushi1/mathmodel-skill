# A2 接续复核：恢复记录、阻断项与限定修正指南

日期：2026-09-25。本文是 `docs/modeling_intelligence_a2_execution_plan.md` 的复核补充，不是新的运行时 Authority。用户要求按原计划完成 A2、确认验收后再进入 B；此前仅有草稿 PR 不能作为完成依据。

## 1. 当前基线与真实恢复

- 主干仍为 A1：`718d129bf0121d95bac3e6323e48c11bf67dafba`，Skill10.2.0。
- 接管既有 PR #238 / `upgrade/v10.3.0-conformance-a2`，不创建重复功能分支。
- 原传输 run `36129180956` attempt2 成功应用52路径补丁并生成提交，但 Actions token 无权修改 `.github/workflows/ci.yml`，push被拒绝；不得把应用成功记为已发布。
- 保留下来的完整提交 `02fbc51ed976d89fcfaf02f73570a5316d6d8302` 是原分支 `be9cba8560c172b2e0938c041d2f638bc7cb28d5` 的正常快进，tree为 `bfad1be41a354e32a706c86d3e7e61b9b654afec`。经diff及原计划核对后，通过有权限的GitHub连接恢复分支；未强推main、未取得或暴露令牌。
- 恢复提交的Actions源码快照包含590个跟踪文件，ZIP SHA-256 `1a317dd44b1e7493dd77ba3807ebd53b4614f8665b877127f956976a3ca32f97`、内部归档和完整重建Git tree均核对一致。临时传输workflow已不在恢复后的树中。
- 恢复树的本地lint、生成物检查、完整unittest均exit0，完整测试用时380.141秒，3项条件跳过。已有绿色测试未覆盖下面新反例，不能据此关闭A2。

## 2. R1：analysis 上游资格依赖未进入事务读集（T17/T28）

真实合成primary和analysis运行后，在analysis回执CLI调用 `commit_project_state` 的前一刻修改primary源码。实测primary源码不在expected_file_hashes中，CLI退出0，状态被写成analysis accepted。这是已复现的阻断项，不是对任意时间竞争的泛泛推测。

修正限定：在现有A2共享观察器中，把analysis所依赖的primary入口、显式源码依赖及实际输入集合纳入同一读集，并在捕获前后沿用原主结果资格核验。应复用现有路径解析、配置解析、source bundle、input identity与transaction，不建立第二身份算法或事务系统。primary/analysis同时启用和只启用analysis均须覆盖；不得因此强制primary提供A1映射或新A2绑定。实际主结果资格仍由原检查器裁决。

需要新增的行为反例：analysis交付/回执提交前primary入口与helper变化；上游独有辅助输入变化；检查过程中上游来源改变；声明来源与当前已验收bundle不一致；正常路径只读且不改primary批准、工作簿或策略。修复后仍要承认读集复核不是任意外部写入下的文件系统原子快照。

## 3. R2：原生MATLAB合成映射产生YAML别名（T15）

恢复提交的完整CI `36133292474` 中，旧MATLAB数值/辅助输入步骤成功，新A2步骤在primary已实际运行并通过回执后、analysis交付时失败。真实错误是 `YAML aliases are outside the bounded declaration protocol`。

下载artifact `10862583894` 并核对ZIP摘要 `79c7a4b55a9d80576f7b8030d9d42b61d63bd8e573985cbd34a6d611032104a4`。state中的同一model_ref字典同时出现在mappings和reverse_review，序列化产生 `&id001/*id001`；由合成声明构造器复用对象引起。

修正限定：合成声明构造时复制model_ref，确保实际生成的测试记录符合既定无别名协议。增加有reverse candidates的MATLAB声明往返测试。不得放宽A1对YAML别名/重复键/超深结构的拒绝，不移除原生A2步骤，不将Python静态检查称为MATLAB执行。

## 4. 文件白名单与验收顺序

本补充允许修改：`scripts/conformance_gate.py` 的现有读集闭环；`core/model_code_conformance_contract.yaml` 的依赖范围澄清；`tests/conformance_a2_smoke.py` 和原A2测试辅助声明构造；新增 `tests/test_conformance_upstream_read_set.py` 及对应反例；本补充和原A2计划台账；由既有生成器生成的索引/MANIFEST。若必须触及额外消费者，先给出实际调用链和补充裁决，不顺手改其他模块。

顺序：冻结本记录→反例在恢复代码上失败→最小修复→专项与两后端静态正负例→完整回归/lint/index→精确提交CI及原生A2复验→完整diff审阅→满足后正常合并和main复验。期间PR保持draft。B1只能在A2不存在已知阻断项且完成验收后串行启动，B2/C/D不自动开始。不得宣称全仓或任意数学模型绝对无缺陷。

## 5. 执行台账

本文提交时：恢复完成，R1实测可复现，R2原生失败原因已定位；两项尚未修正。后续真实测试、提交、合并状态在本节和PR最终验收记录回填。无Release/tag/用户项目变更。
