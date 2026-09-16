# P9 综合回归、兼容窗口与 v9.2.0 发布收尾

> 本文件是 P9 实施/验收记录，不建立新的建模、数值、写作或 Figure Authority。运行语义仍由 Bootstrap 指向的现有 Authority 拥有。

## 修改简报

- **修改主题：** P9——对 P1–P8 已合并优化做综合回归，裁决 P5a/P5b 兼容窗口，并统一活动 release carriers / CHANGELOG 发布收尾。
- **当前版本：** 9.1.0；起点 `main@9d2d7d10800aabcecbdcffda597575c5bbb42930`（P8e #170 已合并）。
- **目标版本：** 9.2.0。
- **变更等级：** minor。P1–P8 的新增能力均以向后兼容方式分阶段合并，P9 不引入破坏性目录、Schema、CLI 或职责迁移；按 `SKILL_CHANGE_GOVERNANCE.md` 的 minor 规则，9.1.0 的下一兼容能力发布为 9.2.0。
- **直接目标：** 统一活动版本载体；把 P5a/P5b 临时兼容窗口转成有退出条件的只读兼容决议；补充 P9 release regression；刷新 CHANGELOG / README / 优化状态；在最终 head 运行完整 HSK Skill CI 与 Optimization baseline。
- **明确不做：** 不重写 P1–P8 已合并业务实现；不删除有效测试/gate；不把 legacy FULL_* 恢复为新 writer；不创建破坏性 v10 迁移；不改 Workbook Schema 2.3.0、Project State、Model Approval、数值判据、MATLAB/LaTeX 业务语义。
- **权威事实源：** `core/bootstrap.yaml`、`SKILL_CHANGE_GOVERNANCE.md`、`core/user_execution_contract.yaml`；其余 release carriers 只同步当前版本身份。
- **预计修改文件：** 活动 release carriers、`core/user_execution_contract.yaml`、CHANGELOG/README、P9 测试与状态记录、generated metadata。
- **禁止触碰：** 历史 release/phase/evaluation 文档中的 provenance 版本号；legacy 历史基线；已批准数学/数值业务合同语义。
- **兼容性要求：** 9.2.0 仍能读取旧 `FULL_FIDELITY_CONFIG / FULL_RUN_CONFIG`；P5a 过渡期无 receipt marker 的 `RUN_CONFIG` / receipt 仍只读兼容；所有新 writer 继续必须输出 canonical `RUN_CONFIG` + `run_receipt_protocol_version=1.0.0`，未知协议 fail closed。
- **迁移要求：** 无强制用户迁移。兼容 reader 的退出不得在 9.2.0 minor release 内静默发生。
- **验收测试：** release-carrier consistency、P5a/P5b new/legacy/transitional compatibility、P1–P8 optimization baseline、完整 unittest、Static contract lint、Generated file contract、Python 3.10–3.14、三类 LaTeX 与 production attestation；MATLAB preview 按现有 change detector 执行。
- **回滚方式：** 整体回滚 P9 carrier/compatibility-record/test/doc 更新即可，P1–P8 已合并能力仍留在 9.1.0 carrier 下运行。

## 兼容窗口裁决

### 1. `FULL_FIDELITY_CONFIG / FULL_RUN_CONFIG`

P5a 已把新 writer 迁移到 canonical `RUN_CONFIG`，旧 FULL_* 名称当前只参与静态读取兼容。P9 **保留该只读 reader**：在 minor release 中删除它会使仍可读取的旧项目变为不可读取，属于治理意义上的 breaking change，不应伪装为 9.2.0 minor 清理。

退出条件：只有未来明确的 major migration（最早 v10）在提供旧项目迁移/检测证据、更新兼容矩阵并完成专门回归后，才可删除该 reader。新 writer 不得继续生成 FULL_*。

### 2. P5a 过渡 `RUN_CONFIG` / versionless receipt

P5b 起新 writer 必须写 `run_receipt_protocol_version=1.0.0`，返回工作簿必须在既有 `运行配置` 载体内写 `run_receipt_version=1.0.0`。P9 同样 **保留 P5a 过渡期缺 marker/version 的只读兼容**，因为现有 9.x 项目可能是在 P5a 合并后、P5b 合并前生成。

退出条件与 FULL_* reader 相同：不得在 9.2.0 minor release 中删除；未来 major migration 必须先证明活动新 writer 已完全版本化，并为历史工作簿/代码提供明确识别与迁移路径。未知显式协议版本继续 fail closed。

### 3. 新 writer 规则不放宽

保留旧 reader 不等于允许旧 writer。9.2.0 的生成侧仍只允许 canonical `RUN_CONFIG`，并要求 receipt protocol marker；legacy / transitional 路径仅用于读取历史项目，不得成为新项目的默认或 fallback 写路径。

## 活动 release carrier 范围

依据现有 release-carrier 回归，P9 应统一更新以下活动身份，不机械改写历史 provenance：

- `core/bootstrap.yaml#skill_version`；
- `.codex-plugin/plugin.json#version`；
- 根与 packaged `SKILL.md`；
- `README.md` 当前标题与新增 v9.2.0 release 摘要；
- `core/hsk_core_policy.md` 当前版本标题；
- `core/workflow_router.yaml#version`；
- `core/module_manifest.yaml#version`；
- `core/output_contract.yaml#version`；
- `core/writing_runtime_contract.yaml#version`；
- `config/prose_audit_patterns.yaml#version`；
- `CHANGELOG.md` 当前 release；
- generator 管理的 index/MANIFEST。

`core/workbook_schema.yaml#schema_version=2.3.0`、各 subordinate contract 自身 schema/version、competition profile lineage 以及历史计划/迁移记录不是 Skill release carrier，不随 9.2.0 机械改写。

## 发布验收状态

待本 PR 完成实现并在最终 generated head 通过完整 CI 后填写。