# P5a RUN_CONFIG 命名与配置职责迁移

> 维护实施证据，不建立第二套执行 Authority。正式执行边界继续由 `core/user_execution_contract.yaml` 与代码/回执校验器决定。

## 基线

- P5a 基线：main `a15b0a15e45fd561a87264eae4af5b1a710d23f6`，Skill v9.1.0。
- P1--P4 已依次合并；当前没有开放重叠 PR。
- P5a 只处理**新生成阶段脚本的配置名称、配置职责与旧配置兼容读取**；P5b 再处理版本化 `RUN_RECEIPT` 与工作簿运行事实 schema。

## 当前问题

现有 `core/user_execution_contract.yaml` 同时把两类不同性质的信息放入每个阶段脚本的 `FULL_FIDELITY_CONFIG`：

1. **任务会变化的运行输入**：stage、problem、data path/hash、solver、seed、tolerance、limit、expected workbook、primary protocol；
2. **全局不允许变化的执行政策**：`execution_owner=user`、`execution_profile=full_fidelity` 与六个 `allow_* = false`。

第二类字段在每个脚本中重复声明，容易形成“只要把 false 写上就等于真正没有降级”的错觉，也增加生成/校对负担。`solver_version` 更适合记录为实际运行事实，而不是作者在运行前手填的任务参数。

仓库校验器已经能识别 `RUN_CONFIG`，但错误文案、required fields 和模板说明仍以 `FULL_FIDELITY_CONFIG` 为主。因此 P5a 不发明全新机制，而是把已有兼容入口提升为新写入规范。

## 单一事实源与职责

| 事项 | P5a 后唯一责任位置 |
|---|---|
| 用户执行、full-fidelity、禁止降级/静默 fallback | `core/user_execution_contract.yaml` 全局执行政策 |
| 新阶段脚本任务参数 | 顶层字典常量 `RUN_CONFIG` |
| 旧脚本兼容 | validator 静态读取 `FULL_FIDELITY_CONFIG` / `FULL_RUN_CONFIG`，只读兼容 |
| 数据版本预绑定 | `RUN_CONFIG.data_sha256`，继续必须是运行前锁定的 SHA-256 |
| 主质量协议 | `RUN_CONFIG.primary_quality_protocol_version`（primary only） |
| 实际 solver/version/platform/stop/fallback/运行规模 | 工作簿 `运行配置` 事实；P5b 再版本化为 `RUN_RECEIPT` |
| 主代码冻结和 state 绑定 | 现有 `validate_code_delivery.py` / project state 逻辑，不变 |

## P5a canonical RUN_CONFIG

新生成脚本只写一个顶层字典常量：

```python
RUN_CONFIG = {
    "stage": "primary",
    "problem_name": "问题一",
    "data_paths": ["附件1.xlsx"],
    "data_sha256": "<运行前锁定的64位SHA-256>",
    "solver": "...",
    "random_seed": 2026,
    "tolerance": "...",
    "iteration_or_time_limit": "...",
    "expected_workbook": "问题一求解/问题一求解结果.xlsx",
    "primary_quality_protocol_version": "1.0.0",
}
```

其中 `primary_quality_protocol_version` 只在 primary 阶段需要。

**不再要求新 RUN_CONFIG 重复：**

- `execution_owner`
- `execution_profile`
- `allow_reduced_data`
- `allow_coarser_grid`
- `allow_shorter_horizon`
- `allow_fewer_repetitions`
- `allow_relaxed_tolerance`
- `allow_silent_solver_fallback`
- `solver_version`

这些字段的约束没有删除：owner/profile/no-degradation 继续是全局 Hard；solver version 与实际 fallback 等继续在用户返回工作簿中验证。P5b 将对运行事实做显式版本化，不在 P5a 混改回执 schema。

## 兼容策略

### 新写入

- 新生成脚本：必须使用 `RUN_CONFIG`。
- validator 对 `RUN_CONFIG` 使用新的 task-variable field set；若新 RUN_CONFIG 主动携带 policy-invariant 字段，则必须与全局 policy 一致，但不要求重复填写。
- `solver_version` 若出现在新 RUN_CONFIG 可暂时接受为冗余兼容信息，但不视为可信运行事实。

### 旧读取

- `FULL_FIDELITY_CONFIG`、`FULL_RUN_CONFIG` 继续可静态读取。
- legacy config 保持旧 required fields 和 false flags 要求，避免旧代码在迁移时被悄悄放宽。
- 旧字段只读兼容窗口至少维持到 P9 发布裁决；本轮不删除。
- 若同一脚本同时定义多个支持的 config 名称，fail closed，避免 validator 选择顺序不确定。

### 回执

P5a **不改**工作簿当前 `运行配置` required items，也不改 `validate_user_execution.py` 对 owner/profile/no-degradation/fallback/solver_version/platform/stop reason 等运行事实的验收。因此代码交付变轻，不等于执行证据变弱。

## 安全边界

- 绝不把 `data_sha256` 从 pre-run config 移除。返回工作簿实际 `data_sha256` 仍必须与代码交付时锁定值一致。
- 绝不因为 RUN_CONFIG 没有六个 false 字段就允许降采样/粗网格/缩时域/少重复/放宽容差/静默 fallback。
- 代码校验器的新模式验证“任务参数完整 + 若出现 invariant override 必须合法”；工作簿回执继续验证实际运行事实。
- P5a 不执行赛题脚本，不修改用户 state 或工作簿。
- 旧 accepted 主脚本继续按 hash 冻结；不能借命名迁移绕过 freeze。

## 预计修改面

- `core/user_execution_contract.yaml`：声明 canonical config name、new/legacy schemas、policy-inherited fields；回执部分保持原 schema。
- `scripts/validate_code_delivery.py`：返回 config name，按 RUN_CONFIG vs legacy 分别校验；多 config fail closed；错误文案去除旧名称硬编码。
- `scripts/validate_user_execution.py`：只改静态读取 config 的歧义/错误文案和 legacy/new name provenance，不改工作簿 required receipt fields。
- `templates/code/hsk_pipeline/main_pipeline.py`：移除 `PipelineConfig` 中重复的 execution owner/profile/六 false policy 字段；验证逻辑不再依赖自报 policy flag。
- starter/hsk_pipeline README、Solve/Analysis 模块：新写入术语改为 RUN_CONFIG，明确 receipt 仍保留运行事实。
- tests：新增 new-vs-legacy schema、multiple config fail closed、pre-run hash binding、不降级边界和 PipelineConfig 去重测试；历史旧 config fixture 继续跑。

## 明确不做

- 不改工作簿 `运行配置` required receipt schema；
- 不引入 `RUN_RECEIPT` 版本字段（P5b）；
- 不改 state Schema、工作簿 Schema、PQS、03A/03B、模型审批、SIB/stale；
- 不把配置藏入 Skill 外部依赖，最终赛题脚本仍可独立运行；
- 不移除旧 config reader。

## 验收

P5a 至少验证：

1. canonical RUN_CONFIG 缺 task-variable 字段时失败；完整时通过；
2. RUN_CONFIG 无 owner/profile/六 allow/solver_version 仍能通过代码交付静态检查；
3. RUN_CONFIG 若显式把任何 invariant 改为非法值仍失败；
4. legacy FULL_FIDELITY_CONFIG/FULL_RUN_CONFIG 仍必须满足旧完整字段和 false flags；
5. 同文件多个 config 名称失败；
6. `data_sha256` 仍强制 64 位 SHA-256，并继续写入 state 作为该阶段锁定数据版本；
7. 返回 workbook 仍要求 owner/profile、六 false flags、fallback=false、solver_version、actual stop/platform 等当前事实；
8. accepted 主代码 freeze、preprocessing decision 与 project-level raw-source isolation 不变；
9. 完整 `lint_skill.py`、全 unittest、generated check、GitHub Python 3.10--3.14、Static lint、三类 LaTeX、Production attestation 与 Optimization baseline 全绿。

## 回滚

撤销 P5a contract/validator/template/docs/tests 并重新生成索引即可。旧 config 一直保留 read compatibility，因此回滚不需要修改用户项目、工作簿或 state。