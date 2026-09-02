# v8.0.1 Skill Health Remediation Status

> 这是 `docs/v801_skill_health_remediation_plan.md` 的当前实施状态摘要，不替代任何 Runtime Authority。  
> 当前 Skill：`8.0.3`  
> 当前实施基线：以 GitHub `main` 与 `core/bootstrap.yaml` 为当前事实源；本文件不作为 commit SHA、版本或 machine state Authority。  
> 最后状态更新：2026-09-02

## 执行决定

用户已批准完整 remediation plan，并在 2026-09-02 明确覆盖原计划的 Phase 1B blocking gate：由于当前 GitHub 账号没有完成 Branch Protection / Ruleset 设置所需权限，Branch Protection **延期处理，但不再阻塞 Phase 2–6**。

该例外只改变 remediation program 的实施顺序，不改变 Skill runtime 语义。不得通过修改 Skill 源码、CI 名称或伪造 repository settings 来模拟平台保护。

## 当前阶段

| Phase | 状态 | 说明 |
|---|---|---|
| Phase 0 | complete | 详细 remediation plan 已通过 PR #90 纳入 main |
| Phase 1A | complete | PR #91 已使 generated metadata 在 feature branch 闭环，main 只做 `--check` |
| Phase 1B | deferred | Branch Protection 因当前账号权限不足延期；Issue #92 保留为平台治理债务 |
| Phase 2 | complete | 旧 v7.16 Branch Protection 施工计划已归档，active path 只保留 current pointer |
| Phase 3 | complete | PR #94 已发布 `8.0.2`，入口已收缩为最小导航/硬边界/Authority pointers |
| Phase 4 | complete | PR #95 发布 `8.0.3`，明确 `semantic_summary_mode` / `rendering_mode` 两层并保留 v8.x 只读兼容 alias |
| Phase 5 | complete | PR #96 将官方 Actions runtime 升级到 Node-24-native v7 majors；CI job 名称与执行语义保持不变 |
| Phase 6 | complete | current-health 测试去版本化命名；完成 tag / GitHub Release provenance read-back 与治理决策 |

## 已验证事实

- `main` 的 generated metadata workflow 自 Phase 1A 起只运行 `verify-main`，`refresh-feature-branch` 在 `main` 上跳过；
- feature branch 继续负责生成 Index / Manifest，`main` 只执行 `python scripts/generate_indexes.py --check`；
- Phase 3 的 v8.0.2 entrypoint slimming 已由完整 HSK Skill CI 验证；
- Phase 4 的 v8.0.3 双词汇澄清保留旧字段只读兼容，并由完整 HSK Skill CI 验证；
- Phase 5 的官方 Actions v7 升级保持既有 11 个 CI job 名称与命令，完整 HSK Skill CI 验证通过；
- Branch Protection 当前仍未形成平台强制，因此不得宣称仓库平台治理已经闭环。

## Release provenance read-back

2026-09-02 对 GitHub repository 的直接 read-back：

- Git refs `tags/`：空；
- GitHub Releases：空。

本 remediation program **不把 tag / GitHub Release 建立为 Skill runtime 或交付 gate**，也不在没有独立发布策略的情况下自动制造历史标签。当前正式版本事实继续由 `core/bootstrap.yaml`、release carriers、CHANGELOG 与完整 CI 共同闭合。

如果未来需要不可变版本分发、外部安装或长期归档，再单独定义 release policy，包括：tag 命名、tag 指向、Release notes 来源、是否签名、发布前 required CI、回滚/撤回语义。该未来工作不得反向改变已 accepted 项目的模型或数值状态。

## 状态文档边界

本文件只记录 remediation program 的人工可读进度。以下事实不得从本文件单独推断：

- 当前 `main` SHA；
- 当前 Skill version；
- 当前 project state / semantic revision / accepted workbook；
- GitHub Branch Protection 实际 enforcement；
- CI 当前运行状态。

这些事实必须分别回到 GitHub read-back、`core/bootstrap.yaml`、`state/project_state.yaml`、accepted workbook 或对应机器事实源。

## 后续

Phase 0–6 除 Phase 1B 外均完成。Branch Protection 权限未来恢复后，再单独完成 Issue #92 的 read-back 验收；该债务不与数学建模 runtime 语义混合处理。
