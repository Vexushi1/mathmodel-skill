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

本文先行提交 `1f168e88faac1a175f366f95c0e155dcdfba4cb3` 时，R1/R2均未修正。后续在同一PR内完成如下有限修复，并保留之前的失败事实：

- R1：在 `conformance_gate.observe_execution_sources` 的analysis分支补 `_observe_primary_dependencies`，以既有source limits、stage resolver、source fingerprint、输入观察及primary资格核验捕获上游source/helper/独立附件。全部进入既有transaction读集和Skill依据绑定。没有改事务引擎或要求未启用的primary提供A2声明。
- R2：两处合成声明构造器对model_ref作独立复制，避免YAML别名；不改变生产解析器安全规则。
- 新增 `tests/test_conformance_upstream_read_set.py` 五个测试函数，实际合成运行后注入落盘前变化。原恢复代码上出现13个预期失败子例、零执行错误；修复后5项全部通过。
- 新测试初版因合成脚本只计算入口SHA、未将新增helper加入回执bundle而失败；先修正生成的合成fixture，再执行上述有效红绿对照。这一fixture错误不是另一个生产缺陷，不隐藏为通过。
- 定向回归54项：全部通过，93.465秒。
- 本地完整回归：`python -m unittest discover -s tests -p 'test_*.py'`，**Ran 1810 tests in 411.098s / OK (skipped=3) / exit0**；新增5项不包含重复导入旧TestCase。
- `python scripts/lint_skill.py`、`python scripts/generate_indexes.py --check`、`git diff --check`均通过；生成物由原生成器生成。
- 曾有一次定向命令因调用超时中断，之后用保存日志的完整命令重新执行并得到上述54项结果。中断日志不能计为通过。

这组本地结果对应恢复源码加R1/R2五个源码/测试文件修正；本文台账、后续自动生成metadata不改变执行逻辑。上传时各新blob与已测本地 `git hash-object` 逐一核对，避免手工复制差异。最终head、原生MATLAB、完整CI、是否合并和main复验以 [PR #238最终验收记录](https://github.com/Vexushi1/mathmodel-skill/pull/238) 为准，未完成前不提前宣称成功。

无Release/tag/用户项目变更。只有A2通过最终验收后才能在独立分支启动原计划B1；这不代表B2/C/D或整份增强计划完成。
