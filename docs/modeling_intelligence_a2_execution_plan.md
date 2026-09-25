# A2 实施指南：模型—代码结构核验接入交付、回执与失效链

日期：2026-09-25。用户明确授权按原计划推进到 A2；本文件是本阶段修改指南和执行台账，不是新的运行时 Authority。

## 1. 固定基线与范围

基线为 `main@718d129bf0121d95bac3e6323e48c11bf67dafba`，Git tree `3b520f5ff4be64475b60595bdcb3ad00ef40f311`，Skill 10.2.0 / State Schema 8.1.0。A1 的合并后 CI `36119863180` 已逐项核实 13/13 jobs 成功；本轮开始时无开放 PR。

依据原计划第6、10—14、17—20节及 `docs/modeling_intelligence_a0_decisions.md` 的 DEC01/02/06/10。只完成 A2：已有只读结构核验的按需消费、交付/验收身份绑定、恢复/同步的失效识别、事务读集及回归。不得进入 B 主张图、C 独立审查回执、D 案例记忆或改变真实用户项目。

## 2. 修改简报

- 等级：minor；目标 Skill 10.3.0，新增显式可选能力，不改变未启用项目的资格和默认门禁。
- State Schema 8.2.0 增加可选阶段策略及交付/验收绑定；一致性声明仍1.0.0，绑定协议单独1.0.0。
- Conformance Authority 1.1.0、User Execution 3.2.0、Runtime Assurance 2.2.0、State Transition 1.4.0各自维护版本；SIB、source bundle、RUN_RECEIPT 1.0/1.1/1.2、PQS不改。
- 不发布10.3.0 Release，不移动任何已有tag，不改变Python/MATLAB统一项目后端、用户执行权、预处理/绘图分工。
- 无项目迁移、无新数据库、无自动生成模型批准、无新通用事务系统。

## 3. A2字段裁决与唯一权威

字段形状只定义在 `core/project_state.schema.yaml`；行为只在现有Conformance Authority与State Transition Authority各自职责中定义。

1. 小问可选 `implementation_conformance_policy`：`protocol_version: 1.0.0` 与非空、去重 `required_stages: [primary, analysis]` 的适用子集。只有显式声明才启用；不是看到A1映射就自动强制。
2. 原 `implementation_conformance.primary|analysis` 继续保存作者提供的1.0结构对应声明，不变成审稿结论。
3. `solver_execution.<stage>.conformance_delivery` 保存本次交付观察：协议、问题/阶段、后端、语义revision/identity、入口、source bundle、声明摘要、检查依据摘要及当前/过期适用性。没有“数学等价已证明”或“独立审查通过”字段。
4. 同级 `conformance_acceptance` 只绑定已检查的交付身份及本次真正通过原回执/数值门的工作簿摘要。它不是另一个数值事实源，也不能覆盖旧数值门失败。
5. 交付绑定仅由现有 `validate_code_delivery.update_state` 协调写入；验收绑定仅由 `validate_user_execution` 在原验收成功后写入；失效由原状态转换/同步协调器处理。只读inspect不写项目。
6. 有A2残缺字段、未知协议、孤立绑定或取消策略却保留绑定时，明确拒绝；没有A2策略/绑定的历史项目和A1观察声明按原行为处理。不得通过删字段伪装兼容。

## 4. 消费规则与防循环

交付前不要求工作簿存在。针对启用阶段调用A1并核对当前实际源码与模型身份；只有 `structure_verified` 可以完成本项结构门，`needs_review/not_assessed/blocked` 均不是完整结构通过。未支持结构或合法变换需要按现有审查规则补足说明，不自动修改SIB、不擅自裁定变换错误、不捏造新的独立审查证据。

结构门只解决结构资格，原模型批准、Code Analyzer、实际输入、full-fidelity运行和PQS仍独立生效。A2不会自动解决A1未支持的语义区域；不能以切换required策略掩盖已启用阶段的失败。

回执验收必须同时满足：当前结构观察与已交付绑定一致，returned receipt的原source bundle与该交付源一致，原回执与数值验收通过。声明改变后旧交付绑定不再适用。仅登记新映射不能刷新旧accepted；需经过明确重新交付和原回执验收。源码字节和已有回执均未变时，可以重新复核同一已有工作簿，不能谎称发生了新运行。

恢复与下游资格消费同一公共检查，不创建替代accepted资格。analysis只读检查不能反向要求自己先accepted；分析交付仅依赖当前主结果与本阶段交付前观察。只启用analysis不迫使primary添加A2记录。每个阶段和问题严格隔离。

## 5. 源快照与事务

复用A1的state/framework/source/Skill读取证据和既有 `commit_project_state(expected_file_hashes=...)`。本次检查对应的主文件、helper、框架、状态以及返回工作簿必须与落盘时核对的字节一致。候选状态内的已验收字段与磁盘原始快照分开，不把两次无关读取拼成一个PASS。

不改transaction实现。启用A2的writer看到pending journal必须显式恢复后重取快照，不能自动恢复再沿用旧检查。Skill依据在提交前及staged validator再次核对；这是协作写入与读前后检测，不承诺任意外部进程下的文件系统原子快照。prepared后的恢复沿用原roll-forward合同，不承诺所有失败自动回滚。

## 6. 失效裁决

- 模型语义变化：相关主/深化交付与验收绑定过期；数学批准仍由原语义profile处理。
- primary源码/helper变化：主及相关深化绑定过期，沿既有typed result依赖传播；普通代码变化不撤销数学批准。
- analysis源码变化：只影响analysis绑定及其原有下游。
- 数据、主工作簿变化：至少相应验收绑定过期；依赖主结果的analysis绑定按原链失效。
- 声明或检查依据改变：同步观察本阶段旧结构绑定不再匹配，使用明确conformance变更事件落入现有数值/证据失效范围；不新增模型批准根或隐藏stale列表。
- 纯论文/图样式变化：不使不相关的结构绑定或数学批准过期。
- 过期绑定保留来源信息并标为stale；声明保留，不自动重签。重复同步应幂等。

## 7. 影响面与白名单

主体：Conformance Authority、State Schema、原A1内核的必要只读证据输出、一个小型集成helper；代码交付、回执、公共前置资格、runtime、sync、状态引擎、状态验证器。路由/reading plan只按显式启用范围加载新增依据；无A2策略时不增加新强制产物或门。

必要说明：User Execution/Runtime/State Transition合同、求解/深化模块、既有闭环模板、脚本导航、原计划台账及本指南；Skill版本载体、受影响当前版本测试及生成索引。

测试新增A2正负例，保留A1、旧Schema投影、未知版本拒绝、输入/回执、事务、后端和历史baseline检查。禁止修改求解器数值公式、MATLAB/Python求解模板、绘图/论文表达规则、旧有效断言、治理文件或无关工作流。

预计跨20个文件，因为同一资格链必须覆盖producer、consumer、validator、stale与双后端测试，加上原有版本载体；不能只插一个if。最终逐路径解释，删除无关改动。临时传输若需Actions，只允许固定分支、固定新旧摘要、明确路径白名单，执行后删除，不进入主干。

## 8. 必测场景

T01旧无A2项目差分不变；T02只有A1声明仍观察；T03显式空/null/未知策略拒绝；T04孤立绑定拒绝；T05初次交付无工作簿可通过结构门；T06缺模型条目/错锚点拒绝交付；T07needs_review不冒充通过；T08主/深化及跨问错绑拒绝；T09helper改动旧绑定失效；T10声明变动后旧回执拒绝；T11原PQS失败不生成验收绑定；T12数值工作簿身份与绑定不一致拒绝；T13原运行回执协议不改；T14Python真实合成交付→运行→验收→恢复；T15MATLAB静态/原生证据分别记录；T16只启用analysis保留primary资格；T17数据/source/框架在检查后改变不落盘；T18pending journal拒绝并保留；T19事务prepared失败遵循原恢复；T20重复同步幂等；T21代码变动不撤销数学批准；T22数学变动仍走旧批准失效；T23论文样式变动不影响结构绑定；T24启用范围的读取计划包含Authority、关闭时不加载；T25验收成功后再变源码，runtime和下游不误判accepted；T26直接调用现有writer也不能跳过A2；T27未知/非法字段不给宽松降级；T28真实依赖集合与原始输入检查仍生效。

基础命令：`python scripts/lint_skill.py`；`python -m unittest discover -s tests -p 'test_*.py'`；`python scripts/generate_indexes.py --check`。专项先失败再修复；最终精确head的多平台CI、优化基线与生成文件分别核对。MATLAB无本地环境时不称本地原生通过，原生结论只认真实远程步骤。

## 9. 当前执行台账与接管

此文件首次提交时仅完成主干/治理/原计划/A0与关键调用链读取、基线源码快照摘要及Git tree核对，baseline lint/index通过，完整基线测试正在执行。所有A2功能及专项测试尚未完成；不可把本段当成实现证明。

后续顺序：固定本计划→补A2反例→实现最小消费与writer绑定→专项→完整回归→索引→精确上传→PR最终head CI及差异复核→正常合并→main复验。每次追加记录真实失败、修正、命令/退出码、SHA、CI及未完成事项。

本轮到A2结束，不启动B/C/D，不发布10.3.0。未合并可撤回PR；合并后revert不删除用户已有记录。旧工具遇新策略/绑定必须报告不支持，不能靠删除记录让历史结果重新合格。
