# P5b 版本化 RUN_RECEIPT 与运行事实绑定

> 维护实施证据，不建立第二套执行 Authority。正式执行边界继续由 `core/user_execution_contract.yaml`、`core/workbook_schema.yaml` 与返回工作簿校验器决定。

## 修改简报

- **修改主题：** P5b，把现有 `运行配置` 工作表中的实际运行事实显式定义为版本化 `RUN_RECEIPT`，并把其与已交付阶段脚本 `RUN_CONFIG` 做确定性绑定。
- **当前版本：** Skill v9.1.0。
- **目标版本：** 已批准候选 minor release 能力；本 PR 不修改 release carriers，统一发布留给 P9。
- **变更等级：** minor-compatible / execution-evidence protocol。
- **直接目标：** 新生成阶段脚本继续使用 P5a `RUN_CONFIG` 作为运行前任务参数；运行后工作簿继续使用既有 `运行配置(项目, 值)` 载体，但其逻辑对象明确命名为 `RUN_RECEIPT`，增加 `run_receipt_version=1.0.0`，并核对 solver/seed/tolerance/limit 等计划值与实际回执的对应关系。实际 solver_version、stop reason、运行规模、platform、fallback 与 no-degradation 事实仍只在回执中可信。
- **明确不做：** 不新增第二张回执工作表，不新增独立 YAML/JSON，不改项目 state Schema，不改变 workbook 文件名/目录，不改 Model Approval/SIB/stale、PQS 数值判据、03A/03B 分界，不移除 legacy receipt 读取。
- **权威事实源：** `core/user_execution_contract.yaml` 拥有运行政策与 RUN_CONFIG↔RUN_RECEIPT 绑定；`core/workbook_schema.yaml` 拥有工作簿载体与字段结构；`scripts/validate_user_execution.py` 执行 returned-workbook 事实验收。
- **预计修改文件：** User Execution Contract、Workbook Schema、returned-workbook validator、Solve/Analysis/Preprocessing/代码模板说明、P5b tests/status；generated index/MANIFEST 由既有 workflow 管理。
- **禁止触碰：** project_state/state_transition/model_approval/numerical_verification 的业务语义；正式赛题 MATLAB/LaTeX；release carriers。
- **兼容性要求：** P5a 之前和 P5a 过渡期脚本/工作簿继续只读兼容；旧 receipt 缺少版本字段时不得仅凭缺字段就拒绝。若已交付 RUN_CONFIG 显式绑定 `run_receipt_protocol_version`，则返回工作簿必须携带匹配的 `run_receipt_version`，且不允许降级为 legacy receipt。
- **迁移要求：** P5b 后新生成 RUN_CONFIG 应写 `run_receipt_protocol_version="1.0.0"`；运行后构造 RUN_RECEIPT 并写入既有 `运行配置` 工作表。P5a transitional RUN_CONFIG 无该字段仍可验收，兼容层至少保留到 P9 发布裁决。
- **验收测试：** version handshake、RUN_CONFIG↔RUN_RECEIPT echo、未知版本 fail closed、legacy/P5a transitional read compatibility、policy/fallback/hash 既有约束不弱化、primary PQS handshake 共存、完整 lint/unittest/generated/LaTeX CI 与 Optimization baseline。
- **回滚方式：** 恢复 P5b contract/schema/validator/docs/tests 并重新生成索引；由于未改 state/workbook 文件名和旧读取，回滚无需迁移用户项目。

## 设计原则

P5a 已把**运行前计划**与**全局执行政策**拆开。P5b 继续拆清第三类信息：**运行后实际事实**。

```text
RUN_CONFIG              User Execution Authority              RUN_RECEIPT
运行前任务参数          user/full_fidelity/no-degradation     运行后事实证据
-----------------       -------------------------------       -----------------------
stage                    execution_owner=user                 run_receipt_version
problem_name             execution_profile=full_fidelity      code_sha256 / data_sha256
data_paths               allow_*=false                        solver / solver_version
data_sha256                                                   tolerance / limit
solver                                                        actual_stop_reason
random_seed                                                   repetitions_or_scenarios
tolerance                                                     grid_or_time_range
iteration_or_time_limit                                      fallback_used / platform
expected_workbook                                             owner/profile/allow_* facts
protocol markers                                              protocol markers
```

`RUN_RECEIPT` 不是第二个项目文件。它是运行时构造的映射，仍序列化到现有工作簿 `运行配置` 表：两列固定为 `项目, 值`。因此 MATLAB/工作簿名/目录与历史读取路径保持不变。

## 协议版本与握手

P5b 定义：

- `run_receipt_protocol_version`：运行前 `RUN_CONFIG` 中的**协议期望版本**；P5b 后新生成脚本写 `1.0.0`。
- `run_receipt_version`：返回工作簿 RUN_RECEIPT 中的**实际回执版本**；当 delivered RUN_CONFIG 绑定上述协议时必须为 `1.0.0`。

迁移期规则：

1. delivered code 使用 `RUN_CONFIG` 且声明 `run_receipt_protocol_version=1.0.0` → 必须返回 `run_receipt_version=1.0.0`；缺失或不匹配均 fail closed。
2. delivered code 为 P5a transitional RUN_CONFIG，尚无 receipt protocol marker → 继续按旧 required receipt facts 验收；若工作簿主动携带 `run_receipt_version`，版本必须受支持。
3. delivered code 为 legacy `FULL_FIDELITY_CONFIG/FULL_RUN_CONFIG` → 继续旧 receipt 兼容；若主动携带版本字段，同样必须受支持。
4. 任何未来未知 `run_receipt_protocol_version/run_receipt_version` 均不得被解释为 1.0.0。

该设计避免仅根据当前 Skill 版本判断用户项目新旧，也避免把历史工作簿强制迁移。

## RUN_CONFIG 与 RUN_RECEIPT 的绑定

P5b 不把运行事实全部复制回 RUN_CONFIG。只对**计划值应与执行值一致**的字段做 echo 验证：

- `stage`
- `problem_name`
- `data_sha256`
- `solver`
- `random_seed`
- `tolerance`
- `iteration_or_time_limit`

其中 `code_sha256` 仍绑定实际已交付脚本哈希；`data_sha256` 同时继续绑定代码交付时冻结的数据版本。

以下字段仍是**实际运行事实**，不得用 RUN_CONFIG 自报替代：

- `solver_version`
- `actual_stop_reason`
- `repetitions_or_scenarios`
- `grid_or_time_range`
- `fallback_used`
- `platform`
- `execution_owner/execution_profile`
- 六个 `allow_*=false`

`fallback_used=false` 与 no-degradation flags 继续独立验收；即便 solver 名称与 RUN_CONFIG 相同，也不能据此跳过 fallback 检查。

## 与 Primary Quality Protocol 的关系

P5b 不替代 v7.14 `primary_quality_protocol_version`：

- receipt protocol 解决“这份运行事实按哪个 RUN_RECEIPT schema 解释”；
- primary quality protocol 解决“主结果数值证据按哪个严格质量协议复核”。

对新 primary 脚本，两者可同时存在于 RUN_CONFIG，并在返回工作簿中分别匹配。analysis/preprocessing 不因 P5b 被错误要求 primary quality marker。

## 兼容窗口

- legacy config readers 继续存在；
- P5a transitional RUN_CONFIG（无 receipt protocol marker）继续 read-compatible；
- 老工作簿不需要重写；
- P9 再根据真实兼容覆盖和发布证据决定是否收紧“新 RUN_CONFIG 必须携带 receipt protocol marker”的静态交付要求，P5b 不提前删除兼容窗口。

## 验收矩阵

| delivered code | workbook receipt | 结果 |
|---|---|---|
| RUN_CONFIG + protocol=1.0.0 | run_receipt_version=1.0.0 + echo 一致 | pass |
| RUN_CONFIG + protocol=1.0.0 | 缺 version | fail |
| RUN_CONFIG + protocol=1.0.0 | version 未知/不匹配 | fail |
| RUN_CONFIG + protocol=1.0.0 | solver/seed/tolerance/limit 任一不一致 | fail |
| P5a RUN_CONFIG 无 protocol | 无 version，但旧 required facts 完整 | pass compatibility |
| legacy FULL_* | 无 version，但旧 required facts 完整 | pass compatibility |
| 任意 delivered code | receipt 主动声明未知 version | fail |
| 任意 | hash、fallback、allow_* 违反既有规则 | fail |

## 回滚

P5b 不改变项目状态 Schema、工作簿文件名或目录。若需回滚，只撤销本阶段 Authority/Schema/validator/docs/tests 并重新生成 repository metadata；历史项目与 P5a 脚本无需迁移。