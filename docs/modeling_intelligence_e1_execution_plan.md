# E1：跨模块综合验收实施与证据计划

## 基线与修改简报

- 基线：`main@b9f20400e7e58a0717eaa2b88ebcce116c7d0613` / Skill 10.17.0 / State 8.15.0。D2 [PR #258](https://github.com/Vexushi1/mathmodel-skill/pull/258) 已 squash 合并；[main CI 36729741410](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36729741410) 的九项正式门和八个 Python worker 成功；[生成物 36729741450](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36729741450) verify-main 成功。没有开放 PR。
- 授权：用户要求按总计划完成 E1 综合验收、E2 发布评审与交接；E1 与 E2 串行。仓库验收只在 GitHub；不执行用户真实赛题。
- 等级及目标：patch / Skill 10.17.1，用于补充行为验收缺口；State、SIB、A/B/C/D 协议、Governance 1.0.6 和 Runtime Assurance 2.4.0 均保留。
- 直接目标：映射总计划 52 场景及第 14.4 节十条混合链；补真实交叉行为负例；记录扩展关闭与显式检索开启的有限资源测量；复核原 Windows MATLAB、Linux LaTeX 与包证据链。
- Authority：既有 conformance、claim/fragment、review receipt、case admission/retrieval、State/transaction 和 resolver。测试与本计划不新增资格 Authority。
- 白名单：新 E1 行为测试、维护度量脚本及其测试、验收映射/计划、总计划当前台账、CHANGELOG、当前 Skill 版本载体/精确版本断言与历史优化比较的严格补丁载体登记、现有 CI 专项/证据上传。生成物由 GitHub bot 唯一生成。
- 禁止修改：数学模型和求解器、用户项目、State Schema 与协议业务规则、批准/accepted/stale 权限、完整测试的平台/数量约束和 check 名称、既有历史 hash/实际平台验收记录。
- 兼容与迁移：无项目迁移；无新增正式 gate；旧无扩展项目按现有语义读取，声明残缺/未知版本仍失败关闭。案例库不进入普通任务默认加载。
- 回退：撤回本主题 PR 或恢复已测源码；保留用户既有记录，不删除新字段伪装兼容。

载体、版本断言和严格比较必须同提交闭合，因此预计超过 20 个活动路径；按新增验收/度量、文档、版本载体/精确断言、CI、受管生成物分组审查。独立协议不随 Skill patch 升级。

## 行为与证据范围

1. helper 变化的真实合成链：A 当前源绑定拒绝、原 accepted 资格拒绝、B 来源影响定位、C 对实际绑定 helper/workbook 的旧快照拒绝。不能用 mock gate PASS 代替真实消费者；未绑定某输入的回执不宣称会因该输入自行过期。
2. 标题措辞变化：数学口径与 primary 资格不应自动撤销；与变更文本实际绑定的回执不能继续 current。文本语义和人工独立审查未发生，不填 PASS。
3. 已批准近似/严格等价、外部引文/本题结果分别验证实际有限协议边界，不能把有限静态通过解释为普遍数学证明。
4. 复用已有 B12 辅助/核心/模型否证、多处消费、read-set、C 修复复验、D 来源撤回/关闭及事务故障恢复测试；矩阵记录具体方法和共享继承，不重复复制全部测试。
5. 独立建模效果、人工视觉/整体语义、可信原生/人类审查身份仍明确 `not_assessed` / unsupported；真实授权试点另行开展。

## 资源测量

维护工具在 Windows GitHub runner 内记录固定普通路由与显式检索模式的耗时、Python 跟踪分配峰值及实际返回上下文字节；记录 head、输入和相关当前文件身份。Python 跟踪分配峰值不是总进程 RSS；声明加载字节不是助手实际读取 token。重复调用每次仍观察当前文件，不保存 gate PASS。

A0 冻结的文件/节点/对象预算及 D2 上下文预算继续执行。A0 没有冻结秒数/RSS 阈值，本次只输出测量，不能事后发明时间门槛、抬高预算或据此声称真实求解/建模质量提升。关闭/开启路径用途不同，耗时不是同任务算法优劣比较。

## GitHub 验收顺序

1. 源码冻结前独立静态复审；只提交源文件并推送。
2. refresh-generated 自动形成 bot final head；draft 专项验证新增交叉行为、度量、历史精确载体与全部相关既有模块。
3. 专项、静态、生成物均成功后 ready；最终 head 的 Windows 3.10/3.14 各四片完整覆盖、其余七正式门和适用 Optimization baseline 全成功。
4. 保存日志、退出结果、测试计数、覆盖/源码 identities、资源报告和实际 MATLAB/LaTeX 证据。失败仅从该 head 远端日志窄修，不重跑旧 head。
5. squash merge 时核对已测 head 与 main Git tree 相同，复核 main 九项正式门和 verify-main；随后 E2 文档主题基于新 main 接续。

本稿是验收前的范围冻结。最终 head、PR、测试计数和合并后证据保存在 PR 的关闭台账；不存在的运行不能预登记。E2 可以诚实标记限制，实际创建 tag/Release 须符合总计划的明确发布授权。

## 首轮专项发现与窄修

首轮 bot head `6a5a58ee03601d5e9acadc759a91630b7f888404` 的 [GitHub 专项 36740672801](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36740672801) 实际运行 702 项，2219.463 秒；两项新增跨模块测试在准备阶段失败，3 项条件 skip。原因是测试选择 B2 1.5 论文证据链却没有其 Schema 必需的 Figure 绑定；现有 validator 正确拒绝了残缺策略。本次只补齐真实合成 Figure 夹具和断言诊断，不放宽生产门禁。原失败运行保留，不作为新 head 的通过证据。

逐文件计时显示，未改动的 `test_b2b5_continuous_acceptance`、`test_b2b6_rejection_return`、`test_b2c_total_acceptance` 与 `test_b2c_runtime_integration` 合计 1641.171 秒，约占该专项 74%。这四个文件继续由 Windows 3.10/3.14 冻结完整回归覆盖；从开发专项的新增列表移出，保留本次新增链、度量、conformance/currentness/transaction、严格载体及既有专项。测试、断言、完整 discovery 和正式 CI 门均保留；该调整只减少开发阶段与冻结阶段的重复执行。
