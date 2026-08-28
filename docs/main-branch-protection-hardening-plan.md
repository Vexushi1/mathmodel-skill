# Main 分支保护硬化计划（P0-BP-01）

> 状态：PLANNING ONLY / 尚未修改仓库保护设置  
> 适用仓库：`Vexushi1/mathmodel-skill`  
> 基线 Skill：`7.16.0`  
> 基线 `main`：`9df2107f2076a3c2396691c46cbadf808f54a1e2`  
> 目标：只修复 `main` 未启用 GitHub Branch Protection 这一项 P0 风险，不修改其他 Skill 语义、工作流、模型、代码、绘图、写作或交付规则。

---

## 1. 修改简报

```text
修改主题：main 分支保护硬化
当前版本：7.16.0
目标版本：7.16.0（不升级 Skill 版本）
变更等级：repository governance / settings-only；本计划文件本身属于 docs
直接目标：把 main 从 unprotected 改为 protected，并强制 PR + 现有 CI 通过后才能合并
明确不做：不处理任何其他 P0/P1/P2；不修改 Skill 运行逻辑；不改 CI 内容；不新增算法、模型、验证或写作规则
权威事实源：core/bootstrap.yaml、SKILL_CHANGE_GOVERNANCE.md、.github/workflows/ci.yml、.github/workflows/refresh-generated.yml、GitHub main branch 当前保护状态
预计修改文件：仅本计划文档；实际保护通过 GitHub Repository Settings 完成，不写 Skill 源文件
禁止触碰文件：core/**、modules/**、packs/**、templates/**、scripts/**、config/**、state/**、SKILL.md、README.md、PROJECT_INSTRUCTIONS.md、现有工作流
兼容性要求：v7.16.0 所有 route、CI、LaTeX、Python 3.10--3.14、generated metadata 与现有 PR 工作方式保持不变
迁移要求：无项目迁移、无 Schema 迁移、无 CLI 迁移
验收测试：保护设置 read-back + 现有完整 HSK Skill CI + PR 合并路径验证
回滚方式：仅撤销/放宽 main 保护规则；不回滚 Skill 源码，因为本次不改 Skill 源码
```

---

## 2. 当前事实基线

实施前已确认：

1. `main` 当前提交为 `9df2107f2076a3c2396691c46cbadf808f54a1e2`；
2. `main` 当前 `protected=false`，required status checks enforcement 为 `off`；
3. 当前 Skill 版本为 `7.16.0`；
4. 仓库修改治理已经明确要求 `branch_required=true`、`pull_request_required=true`、`direct_main_write_allowed=false`；
5. 当前没有 open PR 与本修改范围重叠；
6. 当前仓库为 private，当前账号对仓库具有 admin 权限；
7. Repository Rulesets API 当前返回 403，并提示 private repository 需要升级 GitHub Pro 或改为 public 才能使用该功能；因此本计划优先采用 classic branch protection，并在实施前再次确认该仓库套餐是否支持；
8. 当前连接的 GitHub 工具支持 branch-protection/ruleset **读取**，但没有 branch-protection **写入**动作。实际设置应通过 GitHub Repository Settings，或另一个具备 Branch Protection 写权限的官方 API/CLI 完成；修改后再由当前工具 read-back 验证。

若 classic branch protection 同样因套餐限制不可用，则本 P0 修复应暂停。**不得通过修改 Skill 代码、伪造 CI、改变仓库可见性或绕过 GitHub 权限模型来“模拟”分支保护。**

---

## 3. 核心原则：保护仓库，不改变 Skill

本次修复必须满足：

```text
Skill semantic hash / behavior        不变
workflow_router                       不变
model / solver / validator contracts 不变
Python / MATLAB / LaTeX              不变
CI workflow definitions              不变
generated metadata mechanism         不变
GitHub main admission policy         变强
```

Branch Protection 属于仓库治理层，不属于数学建模语义层。因此：

- 不升级 `7.16.0`；
- 不改 `core/bootstrap.yaml` 的 Skill 版本；
- 不改 `.codex-plugin/plugin.json`；
- 不改 `CHANGELOG.md` 的 Skill 功能版本；
- 不重新生成 active indexes / manifest，除非未来决定把本 docs 文件纳入生成索引且生成器本身要求；本次不得手工修改生成文件；
- 不为保护设置新增一套 Skill runtime gate。

---

## 4. 推荐的 main Branch Protection 配置

### 4.1 必须开启

针对 branch pattern：`main`

#### A. Require a pull request before merging

开启。

目的：把仓库治理文件中“禁止直接写 main”的软约束变成 GitHub 平台硬约束。

**Required approvals：0。**

原因：当前仓库是个人维护场景。若要求 1 个 approval，作者不能批准自己的 PR，可能导致单维护者永久锁死合并路径。此次 P0 修复的目标是“必须经过 PR + CI”，不是引入第二维护者依赖。

不要求：

- Code Owner approval；
- stale approval dismissal；
- last-push approval；
- reviewer 数量门槛。

这些都不属于本次 P0 范围。

#### B. Require status checks to pass before merging

开启，并启用 `Require branches to be up to date before merging`（若当前 classic protection UI 提供该选项）。

Required checks 只绑定当前 `.github/workflows/ci.yml` 已存在、已通过 main 的正式检查，不新增检查：

```text
Static contract lint
Python 3.10
Python 3.11
Python 3.12
Python 3.13
Python 3.14
LaTeX CUMCM
LaTeX MCM-ICM
LaTeX Diangong
Production LaTeX attestation
Generated file contract
```

原则：**保护规则消费现有 CI，不修改 CI 来迎合保护规则。**

不把 `Refresh generated repository metadata` 设为 required check。该 workflow 的职责是生成元数据并在 feature branch 上提交变化，而正式 current/stale 判定已经由 `Generated file contract` 覆盖。

#### C. Allow force pushes

关闭。

#### D. Allow deletions

关闭。

#### E. Do not allow bypassing the above settings

原则上开启，使 admin 也走 PR + CI，真正消除“规则只靠自觉”的 P0 风险。

实施前必须执行第 6 节的 `refresh-generated` 兼容检查；只有确认现有自动生成链不会依赖向受保护 `main` 直接写入新内容，才开启 admin no-bypass。

---

## 5. 明确不启用的保护项

为保证 Skill 与现有仓库工作方式继续可行，本次不启用：

- Require signed commits；
- Require linear history；
- Merge queue；
- Required deployments；
- Code Owners；
- 固定 reviewer 数量；
- Restrict pushes to named actors；
- Lock branch；
- 其他 ruleset 条件规则。

原因：这些不是修复 `main unprotected` 所必需，并可能与当前 merge commit、自动化、个人维护或紧急修复路径发生无关冲突。

---

## 6. `refresh-generated.yml` 可行性保护

当前 `refresh-generated.yml` 对多类 feature branch 和 `main` 触发，使用 `contents: write`，当生成索引/manifest 有变化时执行 `git push`。

Branch Protection 上线后必须保持以下机制成立：

```text
feature branch push
→ refresh-generated 在 feature branch 更新生成文件
→ PR synchronize
→ HSK Skill CI
→ Generated file contract = success
→ merge main
→ main 上 refresh-generated 再运行时应无生成差异
```

因此保护前验证：

1. 当前正常 PR 已经在 feature branch 阶段带入最新 generated metadata；
2. `Generated file contract` 在 PR 上是 required check；
3. merge 后 main 的 tree 不应因为 merge commit 本身产生新的 generated metadata 差异；
4. 若 main 上 refresh-generated 偶发尝试 push，受保护 main 应拒绝该写入，而不是绕过规则；此时应修复 feature-branch generated metadata 闭环，而不是放开 main。

这保证 Branch Protection 不会改变 Skill 内容，只会把“generated metadata 必须在 PR 合并前变 current”执行得更严格。

---

## 7. 实施顺序

### Phase 0：冻结基线

- 记录 `main` SHA；
- 记录当前 Branch Protection 状态；
- 记录当前完整 CI 成功状态；
- 确认没有 overlapping open PR；
- 不修改任何 Skill 源文件。

### Phase 1：确认 GitHub 功能可用性

优先检查 classic branch protection 对当前 private repository 是否可用。

- 可用：进入 Phase 2；
- 不可用且 GitHub 提示需要 Pro：停止实施，保留本计划；
- 不得默认把 private repository 改 public；
- 不得为绕过套餐限制改代码或自制伪保护脚本。

### Phase 2：设置最小 Branch Protection

严格按第 4、5 节配置 `main`。

只改 Repository Settings，不改 Git tree。

### Phase 3：平台 read-back

修改后必须确认：

```text
main.protected == true
pull-request requirement == enabled
required status checks == 当前正式 CI 检查集合
force pushes == disabled
deletions == disabled
admin bypass == disabled（若平台能力允许并经兼容检查）
```

read-back 不满足则不宣布完成。

### Phase 4：Skill 可行性回归

Branch Protection 不改变代码，因此不重新设计模型/路由。只做“保护前后功能等价”验证：

1. 当前 `main` 文件树与设置前相同；
2. 当前 Skill version 仍为 `7.16.0`；
3. 在 PR 分支触发完整 HSK Skill CI；
4. 所有 required checks 均可成功；
5. generated metadata 能在 PR 分支闭环；
6. PR 合并路径仍可用；
7. main read-back 仍为 protected。

只有以上全部成立，才可称“P0 修复完成且 Skill 仍然可行”。

---

## 8. 验收标准

### Blocking acceptance criteria

必须全部满足：

- [ ] `main` 显示 `protected=true`；
- [ ] 直接 main 写入不再是正常维护路径；
- [ ] PR 是正常合并入口；
- [ ] 当前正式 CI required checks 全部可运行；
- [ ] 无 required check 名称错误造成永久 pending；
- [ ] force push disabled；
- [ ] branch deletion disabled；
- [ ] `refresh-generated` 的 feature-branch 生成链不被破坏；
- [ ] `main` 的 Skill 文件 tree 未因保护设置发生变化；
- [ ] Skill version 仍为 `7.16.0`；
- [ ] 当前 runtime / modeling / solving / figure / writing / LaTeX contract 无任何语义修改。

任一项不满足都不宣布完成。

---

## 9. 风险与回滚

### 风险 R1：private repo 套餐不支持 Branch Protection

处理：停止，不改 Skill。由仓库所有者决定是否升级 GitHub plan；**不默认公开仓库**。

### 风险 R2：required check 名称选错

表现：PR 永久等待一个不存在的 check。

处理：只修正 protection setting 中的 check 名称，不改 CI job 名来迁就设置。

### 风险 R3：单维护者被 review requirement 锁死

预防：required approvals 保持 0，不启用 Code Owners / reviewer 数量门槛。

### 风险 R4：generated metadata bot 不能向 main push

原则：这是预期的保护效果。生成文件必须在 feature branch + PR 阶段闭环。若 main 仍需要 bot 产生新差异，说明上游 PR generated metadata 未闭环，应修复其流程，不通过放开 main 绕过。

### 回滚

若 Branch Protection 导致 GitHub 平台级合并死锁且无法通过正确 PR/CI 路径解除：

1. 由 admin 暂时移除/放宽 `main` protection；
2. 不修改 Skill 源码；
3. 查明具体 protection setting 冲突；
4. 重新按最小配置启用；
5. 再做 read-back 与 PR smoke。

由于本次是 settings-only，回滚不会产生模型、数值、工作簿、MATLAB、LaTeX 或论文 stale。

---

## 10. 本计划的边界

P0-BP-01 完成后，只能得出：

> `main` 已从依赖维护者自觉的软治理，升级为 GitHub 平台执行的 PR + CI 保护入口，同时保持 v7.16.0 Skill 语义和产物链不变。

本计划**不授权**顺手处理以下事项：

- fast mode；
- competition profiles；
- dependency pinning；
- environment snapshot；
- legacy cleanup；
- Node warnings；
- CI 重构；
- optimization 03A/03B 文案；
- 任何模型、代码、图表或写作优化。

这些全部保持原状。

---

## 11. 实施记录（后续填写）

```text
实施日期：pending
实施者：pending
保护方式：classic branch protection / pending
实施前 main SHA：9df2107f2076a3c2396691c46cbadf808f54a1e2
实施后 main SHA：应保持相同，除非计划文档另经 PR 合并
main protected read-back：pending
required checks read-back：pending
PR smoke：pending
CI：pending
Skill version：7.16.0 / pending confirm
结论：pending
```
