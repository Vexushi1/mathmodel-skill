# Main 分支保护硬化计划（历史指针）

> 当前状态：**DEFERRED / 当前工具缺少设置写入通道，2026-10-07 已复核**  
> 历史 Skill：`8.0.1`  
> 历史治理上下文：`docs/v801_skill_health_remediation_plan.md` 与 `docs/v801_skill_health_remediation_status.md`  
> 跟踪 Issue：`#92`

原 `v7.16.0` 分支保护施工计划已经发生事实漂移，不再作为 current operational fact。原文按原始字节归档至：

`legacy/architecture/v7.16_main_branch_protection_hardening_plan.md`

当前已完成的代码侧治理是：feature branch 自动闭合 generated metadata，`main` 仅执行 generated metadata check，不再依赖 merge 后 bot 补救性写入。

2026-10-07 实时复核：`main.protected=false`，rulesets 为空。repository metadata 返回 `permissions.admin=true`；历史“当前账号权限不足”的解释不再作为当前事实。当前 GitHub 插件提供保护设置的只读访问，没有设置写入工具，因此本次未启用 Branch Protection / Ruleset。仓库权限和当前工具能力应分别记录。

该平台设置不得通过修改 Skill 代码模拟；获得实际设置写入通道后按 Issue #92 的入口纪律及当前 CI 名称配置，并通过 API read-back 验收。Issue 中旧 Python 3.11/3.12/3.13 等检查名不能照搬；当前正式汇总为 `Python 3.10`、`Windows Python 3.14`，并保留 lint、生成、MATLAB 与 LaTeX 等必要检查。当前施工步骤见 [v10.18.2 修改计划](v10182_routing_submission_closure_plan.md#7-平台事项主分支保护)。

本文件仅作为兼容导航指针，不是 Runtime Authority。
