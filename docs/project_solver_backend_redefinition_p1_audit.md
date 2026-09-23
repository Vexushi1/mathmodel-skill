# 项目级唯一求解后端：P1 整体复审与计划补全

> 日期：2026-09-22。
>
> 当前阶段：**用户已批准实施，前五批已提交，第六批退出数值模板的状态/框架第二写入链；保持 Draft，不合并。** 第 0—12 节及附录保留 P1 审查时的历史证据和当时状态；实施决议与分批进度见第 13—18 节。实施不包含自动发布或用户项目迁移。
>
> 当前运行版本仍为 **9.7.1**；用户提出的后续候选版本为 **10.0.0（major）**，不是已发布版本。
>
> 本文件与 [P0 原计划](project_solver_backend_redefinition_plan.md) 构成同一计划包。P0 的固定基线、B01—B27、T01—T30 和历史阅读记录原样保留；本文件补充当前审议状态、核实结果、具体设计及验收细目。它不是新的运行时 Authority，也不将已发现事项写成已修复。

## 0. 本轮文档修改简报

| 项目 | 当前内容 |
|---|---|
| 仓库 / 默认分支 | `Vexushi1/mathmodel-skill` / `main` |
| 当前实现基线 | `34deb02ff590d061fc7ca36f9bd2742a6653c797`，Skill 9.7.1 |
| 当前 main 文件树 | `9c8e9e02786c54f902b1eb6296801f3f1233ae9d` |
| 本轮读取的计划分支基点 | `d4f24fa073c07217d4a2d214b73b29e0e21e70f0` |
| 该基点文件树 | `f34c8e20ecc96ef76a82bd0f5d2e1613a0c8bdb2` |
| 工作分支 / PR | `docs/project-solver-backend-redefinition-plan` / #230 |
| 本轮变更等级 | docs，仅补全计划与当前 PR 描述，不改变执行规则 |
| 后续实现候选等级 | major / 10.0.0；独立 Schema、契约、回执版本不能复制此版本号 |
| 直接目标 | 补齐项目选择、历史迁移、事务恢复、读取快照、消费者和验收之间的缺口 |
| 权威来源 | 当前 `user_execution`、`project_state` Schema、`runtime_assurance`、`state_transition` 及其真实消费者 |
| 本轮源文件写入范围 | 本 P1 审查文档；派生索引/哈希仅由生成工作流另行提交 |
| 本轮禁止修改 | 实现代码、活动契约、Schema、模板、测试、CI、Skill 版本、用户项目、main、标签和 Release |
| 兼容与迁移 | 本轮不执行迁移；迁移方案见第 4—6 节 |
| 文档回滚 | 正常撤回本轮文档提交；不覆盖 P0 历史记录，不修改旧标签 |
| 验证边界 | 基线静态检查、57 项已完成专项测试及三个维护探针；完整测试尝试超时，不能宣称全量通过 |

开始审查和准备写入时均重新核对 main 与 #230；实现基线没有变化，唯一 open PR 仍为 #230。该 PR 基点相对 main 仅增加 P0 计划，以及生成器维护的 `SKILL_FILE_INDEX.md`、`MANIFEST.sha256`，没有提交 v10 实现。PR 历史描述中的“实施进行中”不能替代实际 diff；本轮按用户最新要求回到计划审议。

## 1. 阅读证据及其边界

### 1.1 源码身份

本地 GitHub DNS 通道不可用，本轮没有假称 clone 成功。通过 GitHub 连接器下载现有 Actions 源码归档，再在本地以文件内容和文件模式重建 Git tree。归档来自 run `35676051810`、artifact `10672294783`，归档 ZIP 的 SHA-256 为：

```text
e09d12207fb9801d24467373e9086ddc9900e76479d1e406ddd5f3a360b7c64c
```

候选源码重建的 tree 与上表 `f34c8e20...` 完全一致。另用 GitHub compare 确认其与 main 的差异仅为三个计划/派生文件，因此本次读取的实现代码等同于上述 main。树一致证明身份，不证明语义读完。

### 1.2 覆盖口径

| 层次 | 本轮实际覆盖 | 不能据此宣称的事项 |
|---|---|---|
| 计划分支完整 tracked 清单 | 550 文件 | 不是 550 文件全部审读 |
| UTF-8 文本身份与主题扫描 | 535 文件，103026 行 | 不把关键词未命中当作无影响证明 |
| 二进制/非 UTF-8 | 15 文件的身份记录 | 未做逐项内容或视觉审查 |
| 本轮本地逐段展开并全文复审 | 33 文件，见附录 A | 不重复累计 P0 已读 106 文件 |
| 本轮本地部分展开 | `validate_model_paper_framework.py` 539—587 | 不能称此文件本轮全文重读 |
| 上述本地去重展开行 | 12091 行 | 不等于全仓 103026 行全部理解 |
| 本轮另经连接器全文重读 | 当前 main 的 bootstrap 与修改治理规范 | 与本地统计分列，不虚增为全仓覆盖 |

P0 已记录 106 个全文文件和两个部分文件，但那是 P0 的历史阅读证据。本次补读重点为其未闭合的 lint、事务、状态、读取、支撑包测试，以及后端链路的实际调用者。跨问、图文、打包、入口清理仍按 P0 的影响矩阵处理，不声称本轮把所有历史计划、领域 Pack、写作推理和二进制重新全文审查。

**审查结论的范围是此次 v10 后端重定义的端到端影响面，不是全仓零缺陷证明。** 实施时每个实际改动文件及其删除/改名引用者仍须全文读取；本文件不能免除此要求。

### 1.3 证据分类

- **F**：已核对的当前源代码、契约或 PR 事实。
- **E**：本轮维护测试/受控探针实际观察到的行为，结论不超过用例。
- **D**：本次补全的待实施设计，不冒称接口已存在。
- **R**：仍需实现前或回归阶段进一步验证的风险。

后续问题条目同时写明分类和原计划对应项；“有意改变的旧能力”“当前确实存在的缺陷”“未来迁移需要新增的设计”不得混成一张已修复 bug 清单。

## 2. 原计划需要纠正或补足的结论

下列编号延续 P0 问题台账。源码行号均绑定 main `34deb02...`，不能用未来行号替换旧证据。

| ID / 证据 | 固定版本依据 | 补全后的处置 |
|---|---|---|
| B28 / F+D | P0 首页、第 12 节；PR #230 body 与 actual diff | 当前授权限于复审补计划；10.0.0 是候选 major；不再使用“正在实施”描述没有实现提交的本轮状态 |
| B29 / F+E+D | `project_transaction.py:229—332,385—489`；事务专项 12 项 | 事务不是所有失败都回滚。准备日志前失败保持 live 文件不变；日志 prepared 后通常向前恢复。修正 P0/PR 中过宽的回滚承诺 |
| B30 / F+E+D | `state_transition_contract.yaml:51—203`；四种依赖探针 | 普通 primary_code_changed 只传播 result，是既有设计；真正迁移需覆盖 data/parameter/result，不能直接当作普通代码更新 |
| B31 / F+D+R | `project_snapshot.py:144—223,399—546`；`sync_project.py:337—372` | 删除 stage selector 后，还必须明确旧路径、旧 bundle、历史文件的退役规则，避免目录发现重新建立 active 绑定 |
| B32 / F+D | `validate_model_approval.py:1—203`；事务 API | 模型批准校验器是只读 validator，不是首次选择 writer。必须落实唯一、显式、受事务保护的选择/迁移协调入口 |
| B33 / F+D | `project_state.schema.yaml:124—134,540—559` | 区分尚未选择、完整已选、字段残缺、历史状态和来源冲突；不得把用户 project.version 当作 Schema 时代判据 |
| B34 / F+D+R | `sync_project.py:713—789`；delivery/receipt CLI | failed 报告不必然表示没写入；strict 退出码也不是唯一资格判断。政策冲突需在写入前阻断，正常数值来源漂移仍应登记 stale |
| B35 / F+D+R | `validate_code_delivery.py:709—797`；`validate_user_execution.py:592—655` | 针对正式交付/验收请求检查覆盖集合，不能“零个所需文件被检查”却被下游当作通过；一般诊断扫描与正式交付区别处理 |
| B36 / F+D | `stage_code.py:104—166,481—566` 及调用者；P0 B07—B11 | 根策略必须传入共享源码绑定及全部消费者；保留 1.1 缺元数据不能降级的判断，不用删除 stage 字段来触发 legacy 分支 |
| B37 / F+D | `instantiate_model_paper_framework.py:1—306`；`test_p4_compact_framework.py` | compact/full 是同一框架投影；优先只改全局工程位置和选择器，投影自动适用则不机械改实例化算法 |
| B38 / F+D | `lint_skill_checks.py:387,426,440,455,1196—1201`；九个适用范围声明 | 补充 v10 applicability 与独立版本矩阵；处理硬编码旧版本/固定 Python 发现 token，不全仓替换 Python 或版本字符串 |
| B39 / F+D | `test_audit_a7_entry_consistency.py:181—243`；`test_python_reference_followup.py:26` | 现有 IO 隔离一致性不是 1.1 源码闭包可交付证明；mixed smoke 被其他回归导入，不能直接删文件丢失原保护 |
| B40 / F+D+R | `project_transaction.py` 的 companion text API；历史保留目标 | 明确原始二进制证据备份、空间/路径保护、失败后未引用归档的处理；不能把 YAML/hash 清单当作已保存全部原始工作簿 |

对原有两项的证据升级：

**B23 从静态源码对照升级为 E（限定范围的实际复现）。** 自包含现代 Python 入口在静态交付检查中无问题；原样复制 `result_io.py` 和 `workbook_validation.py`，正确声明 helper 摘要并以静态 import 引用后，真实交付检查返回“新源码闭包不支持动态Python代码加载”和“新源码闭包不支持执行命名空间的间接传递/反射”。本轮没有执行这份任务入口，也没有证明修复后回执链已经通过。

**B27 的读取快照部分升级为 E。** 在实际 resolver 与 reading_plan 之间注入一次受控状态变更，返回的后端仍为旧 Python，而 read_now 状态行已指向新 MATLAB 声明的文件摘要。本例使用合成 provenance fixture，没有真实数值工作簿，证明的是计划元数据混用，不是已发生的数值误验收或数据损坏。非法编码及其他并发交错仍需补充用例，不能一并写成已复现。

## 3. 一次项目选择：落实到写入动作

### 3.1 不变目标

新活动项目只在 `execution.solver_backend` 及 `execution.solver_backend_selection_reason` 保存一次选择。每问 primary 和真正激活的 analysis 均继承该值。保留每问独立算法、入口、源码 bundle、工作簿和验收状态。

RUN_CONFIG 与 RUN_RECEIPT 中的 backend 是实际执行事实，必须保留并与根策略一致。项目选择不是“全部依赖、工具箱、许可证、内存预算已经验证”的证明；未知条件仍须显式记录。

### 3.2 唯一协调入口的建议设计（D，尚不存在）

建议在现有 `stage_code.py` 或同等现有共享层集中纯策略解析与一致性检查，最多增加一个薄的项目协调脚本，例如 `scripts/project_solver_backend.py`，复用既有 Project Transaction 和 State Transition；不能给 resolver、sync、delivery、receipt 各造一个管理器。

该拟议入口应明确区分三种操作，而不是一个可以偷偷覆盖的 setter：

| 拟议操作 | 行为与写入边界 |
|---|---|
| inspect | 只读诊断根策略、历史候选和冲突，不恢复事务、不补值、不转换历史状态 |
| select | 显式传入 python/matlab、非空理由及预期状态代际；核对全题能力审视与既有批准衔接，首次写入 canonical 根选择 |
| migrate | 已存在历史阶段或需要更换当前选择时，输出影响预览并取得针对该迁移的明确确认，再按第 5—6 节提交 |

命令名称与文件路径是实现设计建议，不是当前仓库可调用的 CLI。实现前冻结其最小参数、结构化诊断及返回状态；新增入口必须进入当前脚本导航和专项测试。

首次选择不得由首份 RUN_CONFIG、目录中的首个 `.py`、Q1 的语言、多数阶段语言或机器上可启动的解释器倒推。auto 只能提出选择待办。缺少全题可预见数值能力、环境或选择理由时，停在候选状态，不交付已定语言的正式数值代码。

选择同一值的重复请求应幂等；仅修订工程理由不能使数值结果自动 stale 或改变数学 SIB。改变已锁值必须进入 migrate，不能允许普通 select 加 force 绕过迁移。纯语言变化不进入数学身份；同时改变算法语义、离散方案或保证时，仍回到已有模型审查和明确批准。

### 3.3 不增加独立审批系统

继续使用当前 Model Challenge/Human Approval。现有 `validate_model_approval.py` 只校验批准证据，不能通过给它一段字符串就伪称用户已批准后端。后端理由在既有 Model Approval Brief 的实现范围和框架全局工程记忆中说明；机器状态由唯一显式写入动作维护。不得新设平行 Backend Approval Gate、第二份策略 JSON 或自引用 trust token。

## 4. 新旧状态及操作资格矩阵

### 4.1 状态分类

| 状态类别 | 识别和处理 |
|---|---|
| 尚未选择 | 根 backend 与 reason 均不存在，且没有需迁移的数值阶段；允许早期审题/模型候选，不允许正式数值代码交付 |
| 完整 canonical | 根值为 python/matlab，理由去空白后非空；当前 stage 无 backend/reason 选择字段 |
| 残缺/非法 | 两个根字段只出现一个，空理由、auto、未知枚举、错误类型或当前根与旧 stage 选择混存；明确报错，不自动修补 |
| 一致历史 | 只有旧 per-stage 状态且可信证据同语言；只提出候选，仍需显式迁移/确认，不静默写根 |
| 混合历史 | 旧各问/主深化语言不同；保留只读历史诊断，暂停新数值交付，由用户选统一目标后分类迁移 |
| 来源冲突 | 声明、扩展名、代码配置、回执或摘要互相冲突；先列证据，不能填根字段压过冲突 |
| 事务待恢复 | 存在未完成 prepared 日志；正式读写先阻断或进入明确恢复动作，不混用多个阶段的 live 文件 |

新 Schema 的早期状态可以保留“未选择”，不需要新增 `not_applicable` 后端枚举。不把一般证明咨询、文字润色或只读历史浏览变成必须先选 Python/MATLAB 的操作；这也不等于新增一个未经定义的纯证明最终提交工作流。

旧项目的 `project.version` 是项目字段，不能擅自解释成 schema_version。Schema 自身版本、Skill 版本和回执版本分开。历史读取只能由明确边界解释，不能在所有当前消费者里散布“缺字段则当 v9 混合项目”的逃生分支。

### 4.2 操作矩阵（D）

| 操作 | 未选择/历史 | 合法已选 | 冲突/待恢复 |
|---|---|---|---|
| 一般方法咨询、文字整理 | 可进行与数值资格无关的工作；如引用结果仍按原证据门 | 正常读取相关事实 | 报告相关冲突，不编造当前结果，不隐式修复 |
| 项目需求审视与候选设计 | 形成一次全题候选，不冒称已锁策略 | 沿用当前选择，必要变更进入迁移 | 保留诊断，不能静默换语言 |
| 当前正式数值代码交付 | 阻断，进入选择或显式迁移 | 原模型门、来源门与项目策略均通过才可交付 | 写入前阻断，不制造新 delivered 身份 |
| 当前回执验收 | 历史诊断不等于新验收资格 | 四方后端一致并满足原质量/身份条件 | 不刷新 validated bundle，不撤换选择 |
| 正式 sync/write 与包资格 | 依所请求阶段明确阻断缺失资格；不是默认 Python | 正常观察/登记真实 stale，不替项目重选 | 区分政策冲突与正常来源漂移；前者不得偷偷写选择或误触发迁移 |
| 显式项目迁移 | 用户确认目标和影响后处理 | 更换当前值须明确确认 | 来源冲突先解决；中断事务先明确恢复，不覆盖未知第三方内容 |

全项目策略声明一致性必须在 question scope 过滤之前检查。Q1 请求不能遮蔽 Q2 的当前冲突，但没有必要因此重算或全文读取所有其他问题的工作簿。

## 5. 迁移与当前身份的退役

### 5.1 迁移前置检查

迁移先记录当前根/历史选择、状态代际与原始字节摘要、所有已声明数值阶段、当前代码/输入/回执/主工作簿身份，以及真实 typed 依赖。不要仅检查本次请求的问题，也不要仅按目录第一份入口判断。

预览至少分出：无需改变实现但仍须核验的同语言阶段、必须重新实现的阶段、已失效阶段、仅历史残留、来源冲突、受影响的参数/数据/结果下游和图文片段。尚未激活 analysis 的问题不能因为迁移而生成空分析源码或工作簿。

### 5.2 字段处置表

| 对象 | 同语言历史迁入 | 更换实现语言/证据不能继承 |
|---|---|---|
| 根选择和理由 | 用户确认后写一次 | 迁移确认后与失效状态共同提交 |
| stage backend/selection_reason | 从新 canonical 状态移除；原状态存历史证据 | 同左，不保留当前双写投影 |
| stage bundle/validated_bundle | 仅在完整来源与验收证据仍成立时保留 | 旧值保存在历史记录；当前 delivered/validated 绑定撤销或按已定义状态清除，不能指向退役代码 |
| code/result_analysis_code 与代码哈希 | 与实际当前入口逐项核验 | 不让旧另一语言路径继续充当当前入口；保留旧源文件原始字节，但区分历史观察与当前资格 |
| 工作簿/回执与其 backend、输入摘要 | 不改写文件；核验决定能否保留资格 | 文件及原回执保留为历史证据；当前结果按 typed stale 失效，不能重写 backend/摘要冒充新运行 |
| 数学 SIB、challenge、approval | 只迁工程组织时不伪造语义变化 | 单纯语言更换不直接修改数学身份；真正模型/算法/离散语义变化照原规则重审 |
| 参数/数据/结果依赖 | 根据实际来源和保留结论核验 | 需要重建的数值来源沿正确类型传播 |
| 图表与论文片段 | 未受影响证据不全局撤回 | 依赖失效数值的图文失效；无依赖的机理图不因语言字符串变化删除 |

不能只删除 `solver_execution.*.backend` 而留下与新策略冲突的 active 路径和 validated bundle。也不能删除整个 solver_execution；阶段源码集合和验收记录仍然必要。删除 validated_bundle 时须满足 Schema 的依赖约束及 existing stale profile，不能制造非法半状态。

### 5.3 避免发现旧文件时重新激活

snapshot 与 sync 会从实际目录发现代码和工作簿，并可能登记路径。迁移必须给出明确的“当前阶段资格与历史文件”的判定，不得仅靠删 YAML 路径期待旧物永远不会再被发现。

验收应包含：旧 Python/MATLAB 文件同时留在目录、旧 analysis 文件存在但当前 not_required、空 stage 元数据、仅有旧 validated 哈希、sync 两次以及重启恢复。观察可记录真实文件存在，但不能自动重新选择后端、恢复已退役 delivered/validated 绑定或重新设为 accepted。正式复现包也不能把历史入口当作当前必需入口。

### 5.4 类型化传播的最小扩展

本轮确认普通 `primary_code_changed` 只发出 result；data/parameter 下游不由该事件自动失效。这不是对旧设计的追责，但它不足以表达真实项目后端迁移的数值来源退役。

建议只为显式迁移增加一个最小事件（名称待实现时冻结，例如数值来源退役），发出 data/parameter/result，不发出 model，复用现有 profile 和同一传播引擎。普通代码变更和相反 CLI 请求的语义保持不变。

primary 与已激活 analysis 的代码失效应分别覆盖，不能因 primary_result profile 不包含 analysis_code 而漏掉分析入口。项目策略影响范围包含独立问题，不局限于 Q1 的依赖连通分量。

现有无类型 legacy 依赖按保守规则可能进一步触发模型层审查。因此“不发出 model”不等于保证所有含旧无类型边的项目审批都永远不受影响；须明确边类型或在迁移预览中报告保守处理，不能暗中削弱 legacy 防线。测试菱形依赖、链式依赖、重复调用和无依赖问题，保持确定性和幂等。

## 6. 事务、历史归档与中断恢复

### 6.1 当前真实事务语义（F/E）

`commit_project_state` 接收文本 companion 写入，在候选验证后写 prepared 日志，再逐文件替换。`_recover_project_transaction_locked` 明确按记录的新摘要向前恢复；`load_state_for_update` 会先调用恢复，因此不是纯读取函数。

| 中断位置 | 正确承诺和验收条件 |
|---|---|
| 准备日志前，包括候选验证失败 | 当前 live 状态/框架/伴随文本不变；清理该事务临时物 |
| prepared 日志后、部分文件已替换 | 不宣称全量回滚；保留恢复记录，按旧/新摘要核验后完成剩余新文件，或在来源不明时阻断 |
| 当前文件既不匹配旧摘要也不匹配新摘要 | 不猜测、不强覆盖第三方修改；显式报冲突 |
| 已完成迁移后的撤销 | 使用明确补偿动作和新的状态代际；不能把 generation 改回旧值或直接重新设 accepted |

读操作不得为了“拿一下状态”调用会恢复写盘的 load_state_for_update。遇到 prepared 日志，普通只读检查应报告 recovery_required 或等价诊断；恢复是独立、明确的状态操作。不要修改普通事务的既有恢复语义来使宣传中的“全部回滚”看似成立。

候选校验必须读取候选新状态，而非重新打开磁盘旧状态。根策略、当前身份退役、typed stale、框架工程记忆和必要伴随记录应在同一可恢复提交中协调。提交前重检状态代际及关键来源摘要；同 generation 的人工内容改写也不能忽略。

### 6.2 原始历史证据的最小保留方案（D）

现有 companion API 写的是 UTF-8 文本，不是任意二进制移动/归档事务。仅保存旧 YAML 和摘要列表，不能等同于保留将来可能被覆盖的原始 `.xlsx`、源码和回执。

优先采用不扩建第二套状态机的方案：先准备不可变历史归档，逐项流式复制并核对原始字节摘要；确认归档完整、路径合法、空间足够且源文件未变化后，再由现有项目事务提交当前根选择、退役/失效状态及小型归档引用。旧任务文件不在迁移过程中重写、删改或批量移动。

归档应处于明确历史位置，例如拟议的 `state/backend_history/<migration-id>/`，而非活动问题目录；它不是第二份当前后端选择或默认 runtime 输入，也不进入 official allowlist。路径仅为设计建议，须在 output/迁移说明中统一，不在多个文档各自定义。

该方案允许在当前状态提交前失败时留下未被引用的完整历史归档；应报告其位置和清理状态，不能声称所有文件都已回滚。只清理本次明确创建且尚未被引用的临时/孤立产物，不删除用户已有历史记录。若必须做到二进制归档与所有文件替换在一个更强的原子协议内，需要单独论证最小事务扩展，不能假装当前 API 已支持。

迁移预览、备份、确认、提交之间若来源或 generation 变化，原确认的影响集合不能继续复用；重新审视。未知来源冲突不能通过强制迁移“修正”。

### 6.3 必测故障点

准备前、归档完成后、prepared 后、框架替换后、state 替换后、报告替换后、恢复中断、历史归档摘要损坏、磁盘空间不足、第三方同代际改写、并发 writer、Windows 文件占用。区分能由本地合成故障验证的行为与必须原生 Windows 验证的生命周期，不把 Linux 模拟结果冒称原生平台通过。

## 7. 运行时读取与各消费者的闭合

### 7.1 修复混用快照，而非再加一份状态

runtime hydration、后端解析、analysis 前提和 reading_plan 应使用同一个已验证项目快照，或在读取计划生成前后比对状态 generation 与原始字节摘要。出现变化时重新解析整个相关计划或停止，不输出旧后端配新状态摘要。

只检查 generation 不足以识别手工改 YAML 而没有更新代际的情况。使用本次读取快照的内存身份即可，不需要把整个频繁变化的状态哈希嵌入用户入口造成自引用，也不新增永久 shadow state。

`reading_plan._current_project` 当前重新读盘；窄 `framework_result_sync` 路径仍须满足同一快照条件，不能只因为它不是求解请求就放过旧 assurance 与新状态混用。read_now 是读取计划，不证明助手已消费；实际未测得的 reading consumption 指标继续为空。

### 7.2 共享函数的直接消费者

| 共享能力 | 必须同步审查的实际消费者 |
|---|---|
| resolve_stage_code | project_snapshot、submission_requirements、validate_code_delivery |
| validate_stage_binding | analysis_prerequisites、project_snapshot、runtime_assurance、submission_requirements、validate_model_paper_framework、validate_project_state、validate_user_execution |
| requires_bundle_binding | project_snapshot、submission_requirements、validate_model_paper_framework、validate_project_state |
| primary_issues / analysis_issues | runtime_assurance、validate_code_delivery、validate_user_execution、validate_project_state |
| load_state_for_update / commit_project_state | sync_project、validate_code_delivery、validate_user_execution、validate_semantic_governance；迁移协调入口是拟增加的调用者 |

接口增加项目上下文时必须更新以上调用者和测试夹具。不能某些调用仍只传单问 entry，随后在底层缺值默认 Python。已有独立 input identity、主工作簿绑定、source bundle/validated bundle、防止现代协议降级等边界仍保留。

### 7.3 失败报告与写入效果分开

当前 sync 允许记录真实漂移导致的 stale，并输出失败报告；receipt 写链也可记录拒绝状态。因此“只要 status=failed 就必须任何字节都不变”并非所有既有操作的语义。

需要明确分流：普通相反后端请求及缺少当前政策资格，不得触发迁移、反向选择或刷新身份；真实源码/数据变化应继续通过既有写链登记失效。不能为前者的无副作用要求删除后者必要的 stale 持久化。

正式调用者联合检查操作资格、结构化 status、所请求问题/阶段的非空覆盖及退出状态。无 --strict 的退出码 0、检查到零入口、ZIP 创建成功、历史只读解析成功，都不单独构成正式交付或验收通过。

### 7.4 支撑包整改范围

将 result_io 的动态装载改为能被现有闭包识别的静态组织，或退出新项目默认复制链；不得对模板增加安全豁免。父包 `__init__.py`、实际 helper、相对导入和传递依赖仍属于真实来源闭包，不用同名外部模块代替未声明的项目文件。

原有 A7 复制 IO 包隔离测试验证的是 schema/fallback 的校验行为一致，不能替代现代交付用例。保留它，同时补“复制真实包—声明 helper—静态交付—维护微例执行—回执”的完整回归；本轮只复现到静态交付拒绝。

旧 combined run_pipeline 已有 legacy 说明，整改应让它退出新默认导出/示例路径，不应歪曲为此前模板已经支持新 1.1 正式交付。数值模板只写约定运行产物，不直接拥有整个项目状态；维护控制面内部的 importlib 与真正交付的数值闭包区别处理，不全仓禁止 importlib。

## 8. 入口、框架、图文与版本清理

### 8.1 不重新叠加政策

继续执行 P0 第 5 节的逐文件删除/重写矩阵：Authority 原位改写，root/packaged SKILL 保持一致，AGENTS/PROJECT/agents 提供短委托，模块保留自身职责，README 删除重复长史与错误固定目录树而保留真实能力导航。

全局工程口径只记一次项目 backend/reason，逐问仍写算法与源码/结果锚点。compact/full 共用模板投影，若全局块自然保留，实例化器只需回归而不必改算法。旧当前模型段落中的语言字段迁到全局时，不能把算法、离散和数学假设一起删除。

模型批准片段中出现的旧 text-hash 术语应核对其实际引用，再与当前 structured semantic identity 口径对齐；这是入口清理，不是授权重写审批机制。需要修改标题或 YAML key 时，同步 exact selector、链接、lint token 与读取回退；引用缺失/歧义不能返回空规则继续执行。

### 8.2 职责隔离与应保留的文字

保留项目级 Python 预处理、正式 MATLAB 绘图、draw.io/机理图渲染、LaTeX/bib 后端、可选 DOCX、外部数值库内部 C/Fortran 实现。统一 numerical backend 不代表禁止这些职责，也不等于一个大脚本或一种算法。

正式绘图仅消费合法已验收数据的约束不变。所有另一语言文件不能粗暴从复现 ZIP 中删除；应按角色、执行闭包和当前资格判断。历史命名、示例环境以及只读兼容中的 Python/MATLAB 文字可以存在，但不得继续授予新项目逐阶段选择权。

### 8.3 九处 applicability 与检查器

当前主题扫描定位到以下九个活动 `<10.0.0` 声明，实施时逐项给出保留、续期或重定义依据，而不是全仓替换成 `<11.0.0`：

| 活动文件 | 当前下界 | v10 审议动作 |
|---|---|---|
| SKILL_CHANGE_GOVERNANCE.md | >=6.3.0 | 对 v10 仍适用的治理续期；说明治理版本和入口指针影响，不新增多余审批 |
| assets/figure_assets.yaml | >=7.4.2 | 后端职责无变化，核对后续期；不重写配色/资产方法 |
| core/code_quality_contract.yaml | >=7.4.2 | 保留工程质量和真实来源门；核对新接口后续期 |
| core/global_preprocessing_contract.yaml | >=7.4.2 | 保留 Python 预处理及旧回执边界，核对后续期 |
| core/numerical_verification_contract.yaml | >=7.14.0 | 数值质量标准不降低；核对后续期 |
| core/runtime_assurance_contract.yaml | >=7.12.0 | 当前恢复语义发生破坏性变化；分别说明新行为与历史只读范围 |
| core/task_taxonomy.yaml | >=6.3.1 | 分类语义不变，核对后续期 |
| core/user_execution_contract.yaml | >=7.4.2 | 当前选择权改变，明确 v10 新语义和 v9 历史读取边界 |
| core/workbook_schema.yaml | >=6.3.2 | 不抹去真实 RUN_CONFIG/RECEIPT 字段；核对后续期 |

`lint_skill_checks.py:387,426,440,455` 的相关硬编码与这些声明一起审查。`1196—1201` 等固定 `.py` 能力发现断言应按实际新入口职责重定义，而不是删除测试让 CI 变绿。过往历史文档中的 `<10.0.0` 保留其历史含义。

### 8.4 独立版本矩阵

| 版本层 | 当前代表值 | 本次候选处理 |
|---|---|---|
| Skill release carriers | 9.7.1 | 后续实现验收时统一为候选 10.0.0；本轮不改 |
| Project State Schema | 7.11.0 | 删除当前 stage selector / 增加根策略属于自身接口变更，单独裁决版本与历史读法 |
| User Execution Contract | 2.6.0 | 新项目选择权重定义，单独记录破坏性变化 |
| Runtime Assurance Contract | 1.2.1 | 根策略恢复和快照边界变化，单独裁决 |
| State Transition Contract | 1.1.0 | 仅确需新增迁移事件时按自身规则升级，不重写普通事件 |
| 数值 RUN_CONFIG/RECEIPT | 1.1.0 | 不因项目选择移位而机械改为 10.0.0；真实运行字段继续保留 |
| 预处理回执 / PQS | 1.0.0 / 1.0.0 | 本次职责与质量标准不变，不随意改号 |
| bootstrap schema / 工作簿 schema | 1.1.0 / 2.3.1 | 按各自接口是否变化裁决，不机械同步 Skill 号 |
| 框架标记 | v0.8-project-memory | 工程记忆位置与兼容读取单独处理，不凭 Skill 主版本改数学身份 |

独立版本的精确目标号必须在 P2 第一个契约设计提交前写明理由；未冻结时明确标为待裁决，不能声称计划已经得到所有发布层的最终批准。Skill carriers 还需核对 bootstrap、router、manifest、output、plugin.json、root/packaged SKILL、README、CHANGELOG 及活动入口头部；不改历史标签和已发布制品。

## 9. 文件处置与实施顺序

### 9.1 改动组与禁止扩张

| 组 | 处置 |
|---|---|
| 四个政策/状态 Authority | 原位定义唯一根选择、当前资格、历史边界和必要的迁移事件；不增平行政策 |
| stage/runtime/delivery/receipt/state/snapshot/sync/package | 同一个接口的多消费者闭合；不能拆出互相矛盾的半套新语义合并 main |
| 选择/迁移协调入口 | 拟新增一个薄入口，复用现有纯解析、事务和类型化传播；不要新增另一套状态引擎 |
| 框架、入口、模块、Pack 和 README | 按 P0 矩阵删除旧选择许可和重复政策，保持导航和精确读取完整 |
| hsk_pipeline 与 starter | 移除新默认链的状态副作用和动态装载障碍；保留数学模式、IO 校验和明确历史 API |
| 测试与 CI | 同后端正例、混合负例、显式历史案例；保留 Python 矩阵、Windows、MATLAB、LaTeX 和来源漏洞回归 |
| stage_inputs / workbook_validation / 通用事务引擎 | 优先复用并回归；无已证实接口缺口不得为统一后端大改 |
| 图表方法、论文推理、领域 Pack、用户模型 | 本次不做无关重构；只检查实际受影响的读取与交接 |
| 生成文件 | 仅 generate_indexes.py；源提交与派生提交分开 |

`solver_backend_mixed_smoke.py` 的 helper 被 `test_python_reference_followup.py` 引用。应先审查全部 import 和 CI 调用，再重构为同项目语言正例与独立混合负例，不能简单删除。原来复现 3→6 别名/反射的负例必须在合法根策略下继续命中原来源错误，不能由新“缺策略”错误提前短路而伪装回归通过。

### 9.2 分阶段退出条件

P1 本轮只交付补全计划、真实证据和未决清单。P2 在用户明确同意实施后，先冻结独立版本、唯一 writer 参数、历史保留方案和故障语义；P3 接通全部共享消费者；P4 清理模板/入口/读取选择器；P5 按下节完整回归与原生验证；P6 在精确最终 head 运行生成和独立验收；P7 另行取得合并授权后方可合并，并单独核验 main。

P2—P4 可分源提交供审查，但不允许以“稍后补完”为理由合并能绕过策略的半成品。发现基线、open PR 或候选 tree 变化，先重核差异和交叉影响。不得将本次文档 CI 的绿色状态搬到未来实现提交。

## 10. T01—T30 的具体补测细目

保持原三十组编号，不新建三十个运行时 Gate。以下是原矩阵的可执行细化，全部是未来 v10 验收要求，不是本轮已经通过。

| 原组 | 必须补入的细目 |
|---|---|
| T01 选择 | 明确候选但未提交；全题需求不充分；auto；重复同值；理由修订；相反值只能迁移；选择不冒充环境验证 |
| T02 Schema | 根两字段成对；空白理由/错误类型/未知值；canonical 与旧 stage 选择混存；stage bundle 保留；不按 project.version 猜时代 |
| T03 同后端 | Python 与 MATLAB 分成两个独立完整项目，每个覆盖 Q1/Q2/required analysis，而非同工程混合正例 |
| T04 跨问 | 只请求 Q1 仍能发现 Q2 当前声明冲突；独立问题也继承根策略；不因此读取所有无关数值表 |
| T05 跨阶段 | 主/深化相反语言拒绝；相同语言不同算法合法；未激活 analysis 不产生入口 |
| T06 恢复 | Q3-only、auto、省略参数、跨聊天恢复；不能由旧扩展名/当前 scope 重选 |
| T07 请求冲突 | 根 Python 请求 MATLAB，状态/源码/工作簿不变；只读 inspect 不隐式 recover；不能把请求冲突变迁移 |
| T08 实际阶段 | 请求 analysis 但主结果 stale 时回到 primary，模板与根语言一致且是实际 resumed stage |
| T09 现代协议 | stage selector 删除仍识别 1.1；缺元数据不降级；无 state 的 literal config 解析不等于当前交付 |
| T10 写权 | delivery 不从配置创建根选择/理由；选择写入需 expected generation；候选校验不读旧磁盘政策 |
| T11 回执 | 项目/源码/配置/回执任一不一致拒绝；失败不刷新 validated；记录拒绝与篡改策略区别处理 |
| T12 来源 | 原始字节、helper、父包、相对 import、输入、主簿、SHA 大小写、路径别名/逃逸及不支持解析仍覆盖 |
| T13 原漏洞 | 在已选合法根策略下运行原 3→6 别名/反射维护案例，确认失败原因仍为原来源保护 |
| T14 同步 | 正常无变化不撤 accepted；真实来源漂移仍写 stale；政策冲突不迁移；旧文件存在不自动复活 delivered/validated |
| T15 迁移 | 全题影响；一致/混合/来源冲突历史；参数/数据/结果下游；无类型旧边的保守行为；未激活分析；归档完整性 |
| T16 事务 | prepared 前失败不写 live；prepared 后 roll-forward；候选新状态验证；同代际字节变化；中断恢复、并发及未知修改阻断 |
| T17 模板 | 数值入口无整份状态 writer；不写 approval；主求解不自动执行未批准分析；预处理/绘图角色不混淆 |
| T18 支撑包 | 真实复制后自包含控制正例；静态 import+已声明 helper 正例；动态/未声明负例；再跑维护微例和回执；保留 A7 IO 一致性 |
| T19 条件深化 | not_required 有理由且无当前分析资格；required 独立入口及 accepted 主簿；迁移旧分析残留不伪装当前 |
| T20 跨问输入 | 同后端 Q2 读取 Q1 当前 accepted 结果，声明与摘要齐全；迁移退役 Q1 后 Q2 按真实输入依赖失效 |
| T21 职责 | Python 全局预处理→MATLAB 数值求解、Python 数值求解→MATLAB 正式图，均保留合法闭环 |
| T22 包 | 当前必需入口/helper/input 非空且完整；历史文件不是资格来源；另一角色语言文件不误删；ZIP 成功不等于包验收 |
| T23 精确读取 | 所有改名标题/key 的选择器，缺文件、歧义、范围越界、非法编码和明确 fallback；不悄悄返回空政策 |
| T24 快照 | hydration 后 backend/generation/依赖变化；同 generation 改字节；prepared 日志；framework_result_sync 窄路由；实际阅读指标不伪造 |
| T25 图文隔离 | draw.io、bib backend、配色和图形角色保持不变；不以数值关键词替换其他职责 |
| T26 框架 | 全局工程选择能恢复；compact→full 保留原事实；纯语言不改 SIB；算法/离散真实变更仍触发原审批 |
| T27 文档 | 无当前 per-question/stage override、固定 Python 数值求解、无条件五文件许可；历史说明与合法职责词保留 |
| T28 原生平台 | Python 矩阵、Windows 8.3/文件生命周期、MATLAB fresh batch/原生数值回执等原场景不得因改例而减少 |
| T29 基线 | 固定 SHA 重表征；旧混合合法→新混合拒绝列为有意变化；不要求所有旧输出逐字相同，不称旧测试已验证新策略 |
| T30 放行 | 精确最终 tree 的 lint/全单测/索引/版本/链接/读取/专项/native；源与生成分提交，逐项登记失败、跳过、未运行 |

## 11. 本轮实际执行结果

### 11.1 已执行与未完成

以下均在修改本 P1 文档之前、上述固定基线读取副本上执行，属于仓库维护验证，不是用户赛题求解。

| 检查 | 实际结果 | 解释边界 |
|---|---|---|
| 重建源码 Git tree | 与 d4f 基点 tree 一致 | 仅源码身份 |
| `python scripts/lint_skill.py` | 通过 | 当前 9.7.1 基线，不证明 v10 完成 |
| `python scripts/generate_indexes.py --check` | 通过 | 当前基线派生文件一致 |
| `python -m unittest -v tests.test_v900_project_transaction` | 12 项通过，0.251 s | 已有事务语义的维护回归 |
| `python -m unittest -v tests.test_v900_state_transitions tests.test_schemas tests.test_reading_plan tests.test_p4_compact_framework` | 45 项通过，15.062 s | 已有状态/Schema/读取/框架维护回归 |
| 全量 `python -m unittest discover -s tests` | 尝试在 200 s 限时下超时，未得到完成汇总 | 不能宣称全量通过；日志只有阶段性进度，尚未确认超时原因 |
| 三个受控维护探针 | 已执行，见下一节 | 不执行用户任务数值入口，不等同于三十组未来验收 |
| 原生 MATLAB / Windows / LaTeX | 本轮未执行 | 不用历史 CI 代替本轮原生验证 |

**可确认完成并通过的现有专项单测合计为 57 项，不是“1354 项全部通过”。** 自动文档工作流若后续完成，应另记其精确 head、任务与结论，不能回填为本轮尚不存在的 v10 实现验收。

### 11.2 三个探针的输入与观察

1. **真实复制支撑包的静态交付。** 在临时项目中构造自包含现代 Python 配置和真实输入摘要，控制入口的检查 issues 为空。复制原文件并声明 helper 摘要后出现两条动态装载/命名空间问题。`result_io.py` 摘要为 `84b838529547779294d88cdb8fb36ad38bdbdb92504c8c8ac9ed68af2dfc1197`，`workbook_validation.py` 为 `4798454f7efbb91c1f541fe552189fca9d458b1dad56f9d8b0722fa36c3251b9`。未运行任务代码，未生成真实执行回执。
2. **普通事件的四种边。** Q1→Q2 分别设 data、parameter、model、result，触发现有 primary_code_changed。前三种 Q2 不 stale，result 时 Q2 stale。该结果验证旧行为，说明需要迁移专用最小事件，不是发现普通事件实现错误。
3. **混用读取快照。** 使用现有 reading_plan_cases 的合成 provenance fixture，在 hydration 与 reading_plan 之间把 generation 从 0 改 1，并把阶段声明从 Python 改 MATLAB。返回的 solver_backend.resolved 仍是 Python，而 read_now 状态摘要为新文件；reading_profile 为 framework_result_sync，assurance.status 为 pass。旧状态摘要 `507128d0717ed26e266142f6c699df0fe5e645066f9c7d2fa7a564af80485741`，新摘要 `72b6531503c21d0e669764cdc7e749401460b692806110110183037278dd8dc1`。没有真实数值工作簿，不推断真实数值验收已被绕过。

这些结果将随本轮审查交付保存日志、输入脚本及 JSON；仅扫描、失败的读取调用、未完成的测试不记作通过证据。修复后应再次以相同维护案例核验，不能直接把当前已复现的问题标记关闭。

## 12. 当前审议结论与实施停止条件

此次补全使原计划从方向性重定义进一步落实到：唯一写入者、状态资格、逐阶段身份退役、历史字节保留、类型化迁移、真实事务恢复、读取快照、消费者更新、入口/版本清理，以及原 T01—T30 的细化验收。

**尚未发生：v10 实现提交、状态迁移、全部未来测试通过、版本发布、PR 合并。** 原有 per-question/per-stage 行为仍是 9.7.1 的当前事实，不能因本文件出现而称已被撤销。

进入实现前，必须审议第 3 节唯一协调入口、第 4 节资格矩阵、第 5—6 节迁移/归档及恢复方案，并冻结独立版本与具体 CLI 设计。所有将实际修改的源文件和引用者须全文读取；本轮部分读取和历史范围必须如实保留。全量测试超时需在实现验收前定位或取得相应完整平台证据。

以下情况保持阻断：当前规则同时允许独立 stage 选择与根唯一选择；缺根策略仍默认 Python；现代协议降级；旧文件重新激活；选择和 stale 分次不可恢复提交；读取计划混合两代状态；prepared 后仍宣称所有失败都回滚；只备份摘要却声称保留原始工作簿；原负例被缺政策短路；未检查所需文件却声称通过；原生未运行却称通过；生成/候选 SHA 变化未复验；未取得本阶段授权便推进实现或合并。

本轮停在计划审议，不因工具能写入或文档 CI 通过而自动进入 P2。

## 附录 A. 本轮本地全文复审文件

下列 33 文件按去重范围核对；连接器另读的 bootstrap/治理文档不混入此表。部分复审的 `scripts/validate_model_paper_framework.py:539—587` 单列，不冒称全文。

```text
core/project_state.schema.yaml
core/runtime_assurance_contract.yaml
core/state_transition_contract.yaml
core/user_execution_contract.yaml
scripts/analysis_prerequisites.py
scripts/instantiate_model_paper_framework.py
scripts/lint_skill_checks.py
scripts/project_snapshot.py
scripts/project_transaction.py
scripts/python_source_checks.py
scripts/reading_plan.py
scripts/resolve_runtime.py
scripts/run_config_parser.py
scripts/runtime_assurance.py
scripts/stage_code.py
scripts/stage_inputs.py
scripts/submission_requirements.py
scripts/sync_project.py
scripts/validate_code_delivery.py
scripts/validate_model_approval.py
scripts/validate_project_state.py
scripts/validate_user_execution.py
templates/code/hsk_pipeline/__init__.py
templates/code/hsk_pipeline/result_io.py
templates/model/model_approval_section.md
tests/reading_plan_cases.py
tests/solver_backend_mixed_smoke.py
tests/test_audit_a7_entry_consistency.py
tests/test_p4_compact_framework.py
tests/test_reading_plan.py
tests/test_v900_project_transaction.py
tests/test_v900_state_transitions.py
tests/test_v900_transactional_writers.py
```

## 附录 B. 关键源码锚点

这些链接只是定位固定版本证据，不是引入外部政策。其他正文 `path:line` 同样绑定本次 main 基线。

- [事务向前恢复及 load_state_for_update](https://github.com/Vexushi1/mathmodel-skill/blob/34deb02ff590d061fc7ca36f9bd2742a6653c797/scripts/project_transaction.py#L229-L332)
- [候选验证、日志和逐文件替换](https://github.com/Vexushi1/mathmodel-skill/blob/34deb02ff590d061fc7ca36f9bd2742a6653c797/scripts/project_transaction.py#L385-L489)
- [当前类型化状态转换](https://github.com/Vexushi1/mathmodel-skill/blob/34deb02ff590d061fc7ca36f9bd2742a6653c797/core/state_transition_contract.yaml#L51-L203)
- [读取计划重新加载状态](https://github.com/Vexushi1/mathmodel-skill/blob/34deb02ff590d061fc7ca36f9bd2742a6653c797/scripts/reading_plan.py#L175-L216)
- [当前项目 hydration 与逐问后端恢复](https://github.com/Vexushi1/mathmodel-skill/blob/34deb02ff590d061fc7ca36f9bd2742a6653c797/scripts/runtime_assurance.py#L401-L540)
- [支撑包的动态加载](https://github.com/Vexushi1/mathmodel-skill/blob/34deb02ff590d061fc7ca36f9bd2742a6653c797/templates/code/hsk_pipeline/result_io.py#L13-L26)
- [交付时反向写入 stage 选择](https://github.com/Vexushi1/mathmodel-skill/blob/34deb02ff590d061fc7ca36f9bd2742a6653c797/scripts/validate_code_delivery.py#L631-L707)
- [sync 报告与事务写入](https://github.com/Vexushi1/mathmodel-skill/blob/34deb02ff590d061fc7ca36f9bd2742a6653c797/scripts/sync_project.py#L713-L789)
- [只读模型批准校验器](https://github.com/Vexushi1/mathmodel-skill/blob/34deb02ff590d061fc7ca36f9bd2742a6653c797/scripts/validate_model_approval.py)
- [包内当前入口与旧 Python 回退](https://github.com/Vexushi1/mathmodel-skill/blob/34deb02ff590d061fc7ca36f9bd2742a6653c797/scripts/submission_requirements.py#L164-L230)


## 13. 审批后的 P2/P3 基础实现续记

### 13.1 恢复基点与实施决议

用户已明确批准：有实质阻断则解决，否则开始修改。中断前 PR 描述已登记实施简报，但远程 head 仍为 `13fd939173d8a72ba9f0d5fce490a818c0be37ed`，没有实现提交。本轮恢复的源码按文件内容与模式重算，tree 精确为 `95c4ccf31e1e8466cd753e9f52b4a595d35107d1`；当前 main 仍为 `34deb02ff590d061fc7ca36f9bd2742a6653c797`。本运行环境没有保留上一请求工作目录，不声称恢复了不可见的未提交实现。

P1 剩余事项是已有方案的工程定稿，不再作为重复索要同范围审批的理由：唯一协调 CLI 定为 inspect / select / migrate；首次选择要求 backend、非空 reason、expected-generation；迁移需先预览，并绑定相同状态字节摘要、代际和影响集合的明确确认。不设 force 或独立 Backend Approval Gate。写侧未完成前只暴露 inspect。

最终独立版本目标冻结为 Project State Schema **8.0.0**、User Execution **3.0.0**、Runtime Assurance **2.0.0**、State Transition **1.2.0**。前两者移除已支持的阶段选择接口，Runtime Assurance 改项目级恢复，State Transition 最小增加迁移事件；数值 RUN_CONFIG/RECEIPT **1.1.0**、预处理回执/PQS **1.0.0**、bootstrap schema **1.1.0**、工作簿 schema **2.3.1**、框架标记 **v0.8-project-memory** 不机械随 Skill 改号。完整切换前，本批保持当前 release carrier 与现有契约版本，不提前宣称最终破坏性接口已生效。

历史保留采用第 6 节方案：先准备并逐字节核验独立归档，再以现有事务提交引用、选择与 typed stale；prepared 前失败不改 live，prepared 后沿用 roll-forward，未知第三方内容阻断。该写侧方案尚未实现，不能将下述只读测试当作迁移通过。

### 13.2 本批源修改及边界

| 文件 | 实际职责 |
|---|---|
| scripts/runtime_assurance.py | ProjectStateSnapshot 捕获原始 UTF-8 状态字节；payload 返回独立映射；检查代际类型、路径边界、未清理日志和读取边界的字节变化；hydration 接受同一内存快照 |
| scripts/resolve_runtime.py | 在 hydration 前捕获快照，传给读取计划，返回前再次核对；不增加旧 assurance 输出字段、不持久化 shadow state |
| scripts/reading_plan.py | 依赖核验复用同一快照；项目状态的行范围/摘要使用捕获字节；状态变化不退化成宽读成功；缺原始快照的独立投影不能取得窄读资格 |
| scripts/project_solver_backend.py | 纯声明分类及 inspect，只报告候选/冲突；历史同语言声明不是已验证来源；未知问题/阶段不按多数语言投票，不由扩展名选语言 |
| tests/test_project_state_read_snapshot.py | 读取中变更、同代际变更、日志、非法编码/结构、依赖、窄读/完整路由、路径与 CLI 的正反回归 |
| tests/test_project_solver_backend_inspect.py | 根字段成对、空理由/auto、旧阶段混存、历史一致/混合/未知、全题冲突、绘图隔离和只读 CLI 的正反回归 |
| core/runtime_assurance_contract.yaml；scripts/README.md | 读取一致性职责和维护导航；不在本批提前重定义 v10 当前后端选择权 |
| 本 P1 文档 | 保留历史记录，登记本批工程决议和完成边界 |

本批不执行 select/migrate、不删除旧 stage 字段、不切换正式交付或回执消费者、不改变数学/数值/图文门，也不修改用户赛题。inspector 的 `schema_validated`、`environment_verified`、`execution_authorized` 均为 false；CLI 零退出仅表示诊断完成且无声明错误，不是项目已批准。

状态一致性是对本次读取边界的乐观核验，不是覆盖所有项目文件的原子快照，也不能阻止返回后的外部修改。后续正式门仍须检查当前来源；实际阅读量指标继续为 null，不将计划哈希伪称已经阅读。

### 13.3 本轮已取得的验证与仍待完成项

在未修改副本上，本轮完整基线 unittest **1354 项执行完成，skipped=3，238.310 s，成功**；lint 和生成检查亦通过。本次给足执行时间后取得完整汇总，不能据此倒改 P1 先前 200 秒超时的历史记录，也不声称已证明所有超时原因。

本批首次新增专项 **35 项通过**，另运行现有读取/Runtime Assurance **28 项通过**。这些是开发时记录；最终源树的完整单测、lint、生成检查、基线行为对照和精确远程 HEAD 的 CI 需在提交后单独记录，不把开发期结果冒称最终放行。

B27 的已复现状态混用路径已有回归与实现；T01/T02 的声明诊断、T07 的只读/冲突基础和 T23/T24 的状态快照子项已推进。T01 首次选择写入、T02 canonical Schema、T07 新全项目运行时策略以及 T01—T30 的其余端到端条件尚未全部完成，不能把整组矩阵勾成通过。

后续沿同一 PR 继续：选择/迁移写侧与 canonical Schema → 运行时/交付/回执/同步/打包消费者统一 → 模板与活动说明清理 → 完整验收与版本统一。该进度不是新的并行计划；最终合并、发布与任何用户赛题迁移仍不在本批授权范围内。


## 14. 第二批：B23 支撑包静态闭包与真实维护回执

### 14.1 恢复及范围

本轮从远程 `2b3e043cb5bfc8ca189e57912cbbf8a6c3afdbda` 继续，已下载该提交的源码归档并重建 tree，精确等于 `33c6bfd2712131c444f02c9f120ddb80c07f2cb8`。这确认第 13 节第一批实现已提交，不把中断导致的无完成回复误认为仓库没有改变，也不重复创建提交或索要同范围审批。main 仍为 `34deb02ff590d061fc7ca36f9bd2742a6653c797`。

本批先实现可独立验证的 B23/T18，避免在所有消费者切换前向当前项目写入半套新后端状态。唯一选择/迁移接口和独立版本仍沿用第 13.1 节定稿，不另起审议或平行计划。本批不启用 select/migrate，不删除 stage selector，不改正式数值门、模型审批或 Skill 版本。

### 14.2 具体实现

- `templates/code/hsk_pipeline/result_io.py` 删除 `spec_from_file_location/module_from_spec/exec_module/sys.modules` 动态装载。包内以显式同级静态导入绑定 `workbook_validation`；历史平铺调用采用普通绝对导入，不捕获依赖内部的 ImportError 来切换同名模块。
- 所有工作簿验证函数、schema/fallback 投影和 `workbook_validation.py` 原始字节不变。维护测试与原生 smoke 读者改为真实包上下文加载 result_io，不修改它们的原数据断言。
- README 给出可选的最小 IO 包布局；不默认复制 legacy runner。使用原始完整初始化文件时，`main_pipeline.py` 也是传递依赖，必须声明。保留旧平铺运行验证，但不将其说成已取得现代闭包交付资格。
- 新增 `tests/test_copied_support_source_closure.py`。复制真实完整支撑包，声明全部 helper，并保留最小 IO 包正例。新微例仅使用既有合成 `a*x=b` 数据，在隔离目录中执行；不执行用户赛题。

测试装载适配涉及 `test_result_io`、`test_audit_blank_record_preservation`、`test_v631_contract_closure`、`test_audit_a7_entry_consistency`、`test_solver_backend_end_to_end` 和 `solver_backend_mixed_smoke`。这些维护读者不属于用户数值闭包，使用正常 import 不是对来源门的豁免。`stage_code.py`、`python_source_checks.py`、delivery/receipt 校验器未为本批放宽规则。

### 14.3 已复现与开发期验证

首次测试调用误用了工作目录，import tests 失败，已记录并更正；该调用不计为基线复现或通过。正确工作目录下，尚未修改 result_io 的完整复制正例实际返回动态加载及间接命名空间两项拒绝，与 B23 原风险一致。静态导入替换后，相同维护场景通过，不用缺失策略或哈希错误短路原问题。

本批新增 **11 项**专项，覆盖完整包/最小 IO 包正例、逐个未声明或错摘要 helper、文件缺失、重新引入旧动态装载、运行前 helper 变更、旧工作簿拒绝、重新交付新 bundle 后不能验收旧回执，以及历史平铺 IO 运行。

完整包正例执行了实际 CLI 静态交付 → 单独维护微例进程 → 1.1 工作簿回执验收，检查返回结果为 3、文本键 `0001` 保留、bundle 与原始源码一致。数值微例运行前后项目状态和原始输入字节不变；只有已有交付/回执控制面登记执行状态。重新交付或验收失败不能刷新 validated bundle，也不能改写历史工作簿。

开发时与既有 IO/blank-record/v631/A7/native-fixture 专项一起执行 **48 项，47 通过、1 条件跳过**（本地未提供真实 MATLAB 输出）；这里包含新增11项，不重复累计。最终完整单测、lint、生成检查及精确远程 HEAD 的 CI 另记在 PR 交付记录，不提前把开发期专项冒称完整放行。

### 14.4 完成边界

B23 的动态装载障碍已移除，T18 的真实包复制、声明、静态交付、维护执行与回执链已有回归。现代交付正例限于明确包上下文；历史平铺可运行不等于闭包认证。未修改 source gate 来忽略不可解析相对导入。

本批不证明 legacy pipeline 的状态 writer 已退出所有默认路径，不把完整包中的旧组合 API 升格为新正式数值入口；T17、B21/B22/B24 的后续清理以及全项目唯一策略仍需继续实现。跨后端请求、迁移、canonical Schema、全链消费者、活动版本和 T01—T30 完整放行均未因本批而宣称完成。保持 Draft，不合并、不发布、不迁移用户项目。


## 15. 第三批：迁移数值来源失效与字节绑定事务

### 15.1 固定起点和本批边界

本批从 `60c4328886fad20fe24a747777dcc3258338f3fe` 继续。已有 Actions 源码归档的 ZIP SHA-256 为 `7b2a963026870ec1421aa6406ffe706005de6a2b95bdf9c9f4a831c371f2f9df`，本地重新构建的完整 tree 为 `2704653b85c78244139e8a2bf2728e4ffe5f5ab8`，与远程基点一致。main 仍为 `34deb02ff590d061fc7ca36f9bd2742a6653c797`，唯一 open PR 为 #230。沿用第13节已审批的接口和独立版本决议，不新增审议循环。

本批将第5.4、6.1、6.3节中可独立检验的迁移基础落地；不开放 select/migrate 写命令，不写半套 canonical 项目状态。完整历史归档、当前绑定退役、首次选择及全部消费者接通仍在后续范围。本批库功能不构成用户项目迁移授权。

### 15.2 字节绑定的既有事务接口

`commit_project_state` 新增可选关键字参数 `expected_file_hashes`。映射必须包含 `state/project_state.yaml` 和每个伴随写入目标，可另列输入、源码、工作簿等只读关键来源；SHA-256 大小写等价，null 明确表示该路径必须不存在，不等于“忽略该文件”。路径须为无歧义的项目相对 POSIX 写法，拒绝越界、别名、事务内部文件及非法摘要。映射在进入检查后复制，验证器不能通过修改调用方原映射来重写已经捕获的期望。

该参数与 expected_generation 联合使用：锁内进入时及 prepared 日志之前均核对原始字节；候选验证仍针对下一代 staged state；同时核对 staged 新字节与 old-file 备份，防止验证过程改变未登记的候选或旧字节证据。prepared 后每个目标替换前核对其仍为预期旧文件及 staged 内容，未知第三方修改不得直接覆盖。

启用读集合时，任何未清理事务日志均要求明确恢复并重新捕获快照，不隐式恢复后复用旧确认。省略新参数的旧调用保留原自动恢复行为，这是阶段性兼容 API，不是最终新选择/迁移的默认逃生口。新协调写侧接通时必须传入完整关键读集合；接口本身不猜测哪些未声明来源影响模型。

不改变 JOURNAL_VERSION=1 或已有 prepared 后 roll-forward 协议。prepared 前失败不替换 live 状态与伴随目标，但可能创建协作锁文件／临时目录；prepared 后中断不声称全部回滚。未知内容阻断恢复。只读来源在提交决策点被核验，返回后仍可能变化，原正式门须继续核验当前来源。不能将协作式锁和边界检查宣传为针对任意不遵守锁的外部程序的全文件原子快照。

### 15.3 数值来源退役的类型化事件

`core/state_transition_contract.yaml` 按第13.1节既定目标升级为 **1.2.0**，只新增两个阶段对应事件：`primary_numerical_source_retired` 与 `analysis_numerical_source_retired`。二者发出 data/parameter/result，不直接发出 model，分别复用 primary_result 和 analysis_result profile。纯引擎 `state_transitions.py` 不增加私有传播规则或文件 I/O。

将早期“一个数值来源退役事件”的示例具体化为两个阶段事件，是为了让 analysis-only 迁移保留未受影响的本问主结果；否则借用 primary profile 会错误地撤回主数值资格，或需要为同一效果增加引擎分支。两者仍属同一 Authority，不创建第二状态机。普通 primary_code_changed / analysis_code_changed 的作用和既有 dependency_rules 全部保持不变。

来源退役事件只管理 freshness：不自行选择后端、不备份工作簿、不删除路径或 validated bundle、不授予执行资格。未来协调器须在应用 profile 前捕获受影响阶段，再统一处理当前绑定、历史归档与事务提交；不能因为 primary profile 重置了分析处置而漏掉原已激活 analysis。独立受影响问题需要明确列入，不能只从Q1传播。数据／参数／结果按现有类型规则传播，纯 model 边不由直接退役信号触发；legacy/未知边仍保守处理，可能间接使批准失效。

### 15.4 实际维护验证与完成边界

未修改基点的受控临时项目探针确认：只检查 generation 的旧写入会覆盖未增加代际的注释改写；这是本批字节保护要补上的能力，不将新 API 的缺失报错当作原漏洞复现。原事务／状态专项23项通过。

本批新增 **40项**测试：27项字节读集合事务、13项数值来源退役。初次与原事务／状态专项合并运行 **63项，全部通过**，包含同代际字节变化、二进制来源漂移、预期不存在、完整写集合、路径／摘要、候选和备份变更、并发写者、明确恢复、各替换边界向前恢复，以及类型边、analysis-only、链式／菱形／循环、幂等和独立问题。该数字为开发期记录，完整最终源码树、lint、生成与精确HEAD CI另列PR完成记录，不重复累加为总测试数。

本地符号链接正反例实际运行；Windows该项因创建链接可能需要权限而显式跳过，不能当作原生链接能力已验证。原有Windows事务生命周期仍由原专项与CI覆盖。所有新运行仅为临时目录中的仓库维护状态，不执行用户赛题、不伪造运行回执或 accepted 证据。

实际源修改为事务实现、State Transition Authority、scripts导航、本P1进度、两个新增专项，以及原状态专项中独立契约版本断言1.1.0→1.2.0；其余原断言、旧事件和profiles不弱化。本批推进B29/B30与T15/T16的基础子项，不将T15/T16整组、历史归档、canonical Schema、选择/迁移写侧或T01—T30全链勾为完成。Skill仍9.7.1，保持Draft，不合并、不发布。


## 16. 第四批：原始历史证据归档与可恢复引用

### 16.1 重新读取与固定身份

用户要求接着剩余工作，并明确不能依据不完整记忆猜测。本轮重新读取main的bootstrap和治理全文，核对main仍为`34deb02ff590d061fc7ca36f9bd2742a6653c797`、唯一open PR仍为#230，工作分支HEAD为`ddb2507aa40915a1e04bb654846e91070d123fc6`。重新提取该提交已有源码归档，ZIP SHA-256 `4b06196994c493f484aa25c68546834bdb56452d2c465d89e4d39bea4907e3fc`，本地完整Git tree精确等于`f30560a57a056144270d2e703b4965a64734ded3`。

P0全文与P1全文（含13—15节）已重读；当前准备不是新的平行计划。实际改动面为`project_transaction.py`、`output_contract.yaml`、scripts导航、本节与新增归档专项；前三者及P0/P1均已全文展开，未把整仓下载、扫描或测试等同于全仓全文审读。写源码前的修改简报已更新到当前PR。

### 16.2 原始字节保留的实际实现

落实第6.2节/B40：在已有事务模块增加`prepare_history_archive`与`verify_history_archive`，不新增管理器、后端政策或审批Gate。归档布局只在Output Contract的`backend_migration_history`定义；这是可选迁移历史，不是默认runtime输入，不改变official allowlist。

准备操作要求明确目标目录、expected_generation、原始expected_file_hashes；该集合必须含存在的原始state。逐项流式复制原始字节，保留中文路径、CRLF和二进制工作簿，不转换源码、回执或数据格式。null记录明确表示原路径不存在，不用空占位文件替代。复制前/后重检已声明来源；检查预计存储空间和余量，并在manifest形成后核验所有归档文件。摘要大小写规范化不改原始文件。

目标目录不能覆盖既有目录，不能与声明来源重叠，不能经过路径别名；不使用硬链接代替独立备份。归档manifest记录源路径、原始摘要、大小和基准代际，外部引用绑定manifest路径与SHA-256，不使用自报成功或自引用摘要证明完整性。复核拒绝遗漏、额外文件/目录、非法结构、重复JSON键、符号/硬链接及字节损坏。复核原始路径只作词法校验，不要求已退役的原始文件仍存在、仍为相同字节或仍可解析；否则迁移后正常重建会错误地使历史归档失效。

归档准备不写当前状态、后端、审批或运行资格。遇到I/O失败/复制中断，已创建的目录保留，异常明确携带archive_relative、cleanup_status=retained及state_commit_performed=false；尚未创建则报告not_created。不自动递归删除，避免误删既有或其他进程加入的历史材料。进程被直接终止也可能留下未完成目录，不能复用该目录或把其当作已核验备份。完整归档在后续候选状态失败时允许作为未引用历史保留；协调器仍负责最终引用与明确处置。

### 16.3 为什么需要归档依赖的journal v2

第三批的expected_file_hashes是在提交边界校验的读集合；v1日志不保存归档依赖，临时validator也不会在新进程恢复时自动重新运行。直接把归档摘要只交给v1调用方，会在prepared之后的进程中断中丢失历史完整性检查。因此本批按第6.2节允许的最小事务扩展，增加可选preserved_archives，并将其记录为有明确版本边界的journal v2。

无归档调用继续写/读v1；新增归档依赖必须同时使用字节绑定提交，所有归档的原始来源与本次确认读集合一致，基准代际一致，且任何事务目标不得写进归档。归档引用在进入时复制，不能通过validator修改调用方引用来重绑进行中的确认。

v2在prepared前、prepared后开始替换前、提交完成边界，以及恢复/committed清理入口复核归档；恢复核对日志的旧state摘要与已归档state一致；日志中的目标、暂存及备份清理路径均不得指向被保留的归档，避免清理动作删除其承诺保留的证据。归档损坏时保留日志并阻断，不通过恢复覆盖未知原始内容。原始输入之后发生正常变化不阻断归档字节复核；新进程只凭持久日志及外部绑定引用即可恢复，不依赖已经丢失的内存validator。

v2不接受缺失/空归档依赖、未知版本或保留归档字段却伪标v1。旧实现不认识v2，应保留明确不支持而不能假称向后恢复兼容；回滚代码之前须先用支持v2的实现处理未完成v2日志。旧v1日志不升级、不改写。journal v2与Skill10.0.0、State Schema8.0.0及回执1.1.0是独立协议，不机械同步改号。

这仍是同一可恢复事务、同一项目协作锁，不是第二状态机。prepared后沿用roll-forward；外部不遵守锁的写者仍可能在核验边界之间修改文件，不宣称文件系统级全局原子快照、硬件掉电绝对耐久或OS不可篡改。历史内容与manifest同时被改写再伪造所有受信引用的威胁不由该本地哈希协议解决。

### 16.4 开发验证与完成边界

在写源码前，固定基线完整unittest实际完成1440项，skipped=3，155.673秒，OK；lint与生成检查通过，不复用此前批次的计时作本轮证据。开发期首轮42项归档专项与原事务/字节绑定39项合跑81项全部通过；随后增加日志清理路径误指向归档的负例，实际暴露开发中v2清理路径缺口，修复后共43项新增专项；最终全量、精确源码树、生成与远程CI在PR完成记录分列，不把开发期专项替代最终验收。

维护用例创建真实XLSX，检查数值3与文本键0001、原始回执工作表、中文路径、CRLF及超过单个复制块的二进制数据，逐字节比较独立副本。测试包含旧源消失/变更后的只读归档复核、磁盘不足/复制故障、同代际修改、确认集合/引用修改、旧目录竞争、缺失/额外/损坏成员、所有替换边界、归档损坏阻断恢复、恢复后原始历史保留及真正新进程恢复。原始用户赛题与历史证据均未操作，维护state不是完整canonical Schema或数学验收证明。

Windows需要权限的两个新增符号链接用例有明确条件跳过；硬链接是否运行按系统实际能力记录，不冒称所有原生条件通过。本批没有改变原数值/审批/来源/状态传播规则或CI配置；只读inspect仍无新增写副作用。

本批完成B40/T15/T16中的归档与恢复依赖子项，但没有完成全题影响面识别、用户迁移确认、当前绑定退役、select/migrate CLI、canonical Schema和全链消费者切换。归档完整不等于数值来源合格，不凭归档重新授予accepted。剩余工作仍按既定计划实施，当前Skill仍9.7.1，保持Draft、不合并、不发布、不迁移用户项目。

## 17. 第五批：全题证据绑定的只读迁移预览

### 17.1 基点、阅读与范围

本批从远程 `9751295fac61d3eb5ce307452d9a728dc63d9516` 继续；558个tracked文件从第四批源码归档重建，tree精确等于 `e8fc1cece24fe6eafc50d15fd40839528d0928ba`。main仍为 `34deb02ff590d061fc7ca36f9bd2742a6653c797` / 9.7.1，唯一open PR为#230。重新读取main bootstrap/治理、P0/P1计划及第13—16节，再读现有inspect、阶段身份/输入/回执/分析前提、状态传播和直接测试。未把下载或关键词命中当作全仓全文审读。写源码前已将本批简报写入PR。

本批是B31/B32/B33/B36和T15/T16的证据/影响面预览子项，不新增平行计划或审批。按13.1节继续只开放inspect：canonical Schema及全部消费者未切换前，不提供能写出半套新状态的select/migrate命令。

### 17.2 已实现的读取与退役候选

`project_solver_backend.py inspect --project-root <root> --migration-target python|matlab --reason <reason>` 现在读取全题已登记的原始来源，区分显式迁移目标与普通requested-backend冲突；两类请求不能混用。没有迁移选项时，原声明诊断接口保持不变。

预览复用stage_code的静态配置、源码闭包/入口/交付与验收bundle，stage_inputs的实际输入摘要，以及既有回执、主数值复核与分析前提。只有同语言而没有有效证据，不产生accepted保留结论。源码/输入/回执冲突阻断；真实legacy读者证据只能提出重建，现代bundle不能靠改旧协议标记躲过检查。未来根策略声明的历史回执重检仅在私有内存副本中适配现有v9读者，不持久双写，也不宣称未来Schema或审批已通过。

逐一覆盖独立问题和主/分析阶段。目录中另一语言的孤立入口或未登记工作簿只观察，不投票、不重新授予资格；not_required的旧分析绑定可提出退出当前状态，但不重新激活分析。已登记跨问数值工作簿输入须有数值或保守legacy依赖，不能替用户补边；依赖源不存在、形状不合法或无法识别的问题编号均明确阻断，不静默漏查。

纯内存候选先捕获原分析激活条件，再复用数值来源退役事件做不动点传播；退役主来源同时处理适用分析，受影响的数值下游继续按真实类型传播。候选撤销对应入口、交付/验收bundle、工作簿及数据验收绑定，文件原字节不删除、不改写。analysis-only不撤销未受影响主结果；model-only边不因语言变化直接触发数值退役，旧无类型边保留既有保守模型审批失效。现有论文片段传播只标真实依赖，独立机理内容不被删除。

报告只输出字段差异与传播证据，不输出可直接冒充当前合法状态的整份YAML。`ready_for_review`不等于ready-to-migrate：仍显式标记schema_validated/environment_verified/execution_authorized/migration_authorized/write_supported为false，后续完整Schema与消费者、模型/语义复核、确认、归档、框架同步及事务提交均是独立未完成条件。

### 17.3 快照、摘要与故障边界

预览绑定原始state字节/代际、实际读入的源码/helper/输入/工作簿、适用框架及报告路径；标准潜在入口的预期不存在也保留。确认集合按项目相对路径输出，source/helper/receipt读取结束后再核对读集合和state；存在未恢复日志时不恢复、不写入。预览及直接共享实现/合同的摘要也参与payload并在读取末尾复核，防止本次核验期间合同切换。

摘要只是确定性审议标识，不是用户确认票据、密码签名、当前代码交付或数学验收。读取到一半失败时coverage_complete不伪装完整；任何错误清除字段差异及可用摘要，返回blocked。这里只约束声明与实际观测集合，不承诺任意外部非协作写者下的文件系统全局原子快照，也不证明未知动态legacy来源已全量保存。未来写侧必须重新形成完整归档/伴随目标集合并通过现有字节保护事务，不能直接把这份预览当作写入授权。

### 17.4 实际维护验证及剩余边界

修改前固定基点完整单测1483项，3条件跳过，158.908秒，OK；lint/生成检查通过。首批新增60项专项在开发候选执行通过；随后增加3项边界回归，实测发现已交付但无绑定被误记planned、已交付但缺文件被误记尚未生成、合法SHA大小写导致私有历史读者误判三类缺口。已补生命周期阻断，并只在历史重检内存副本规范化已验证为合法SHA的data/validated_data字符串；原state、原始字节和共享门不改。修复后新增专项总数为63项。开发探针曾因共享配置解析函数返回元组而未解包失败，已修正；首轮专项3处测试定位错误分别是错误消息用词、错误审批字段和按列号修改了错误表头，均改为实际接口/字段及精确表头断言后复验，没有修改旧Authority或削弱旧测试。原失败记录保留，最终全量与精确HEAD远程CI在PR完成记录分列。

Python主结果基准实际执行了已有a*x=b维护微例；部分新增分析/辅助源码回执是明确的合成读者夹具，不声称执行了对应用户模型。新增用例覆盖独立混合问题、主退役含分析、analysis-only、失效旧验收、typed/legacy/链式/循环/菱形、缺边、坏来源/输入/回执、协议降级、动态依赖闭包、同代际读时变化、真实数值底层复核、孤立旧文件、不适用分析、路径别名和无写副作用。

另下载前一提交的原生MATLAB证据artifact 10695574776，ZIP SHA-256 `59a75efddd03c236e69dbeb393f7a3e71a86b1c352051113a952613419ea0120`，仅作当前预览的只读开发输入。普通/摘要大小写/project-level预处理三组的两种目标共6个预览符合预期；两个旧跨语言夹具的两种目标共4个预览因缺少其真实工作簿输入的依赖边而阻断，没有反改旧fixture或宣称旧数值运行失败。此处是重检旧真实产物，不是本地重新运行MATLAB。

在原生end-to-end维护verify的analysis完成后追加同/异目标预览及全部项目文件不变断言；后续同一最终HEAD的MATLAB CI将真正执行这一集成。现有CI工作流不改、原数值断言不删。Windows符号链接新增用例按权限条件跳过；其他原生结果按实际记录，不能拿Linux断言冒称所有Windows条件通过。

本批没有启用select/migrate写侧，没有执行归档或项目迁移，没有修改当前Schema及运行时/交付/回执/同步/打包的活动策略。下一主体仍是明确确认、持久当前绑定退役、canonical Schema和全部消费者一致切换；随后旧模板writer退出、入口/版本范围、T01—T30最终验收与10.0.0发布载体。保持Draft，不合并、不发布，原P0及先前批次证据不倒改。

## 18. 第六批：数值模板的状态与框架写入权退出

### 18.1 固定基点与实施顺序

本批从实际分支ref `29af48a2010561bc20ce41b7f7e397780d100754` 继续。第五批源码归档ZIP的SHA-256为 `f5d955654f062098433429e864f47f1fd747f0a1ba73725e2db9478350018786`；本轮重新提取559个tracked文件，重建tree精确等于 `e36b1a072260326f9afe6aa5565dffd5033565ed`。main仍为 `34deb02ff590d061fc7ca36f9bd2742a6653c797` / Skill9.7.1，只有PR #230未合并。PR元数据仍显示第五批源提交b797及mergeable=false，与实际分支ref不一致；没有据此回退分支、强制更新或尝试合并。

已重新读取main bootstrap/治理、P0/P1及第13—17节，并全文审读本批实际修改的管线、包导出、五类starter、两份模板说明和受影响直接测试。相关执行/代码质量契约与静态闭包测试按影响面核查，不将下载、关键词扫描、AST比较或测试通过冒充全仓逐字审读。

本批落实既有B21/B22/B24、T17/T19的模板写权子项：先退出重复的任务侧状态writer和框架writer，再接通唯一select/migrate协调写侧。属于P0第7.5节、P1第7.4节既有清理项的前置实施，不是另建计划或审批Gate。写源码前已将范围、接口破坏性、验收和回滚写入同一PR。

### 18.2 已移除的第二写入链

`hsk_pipeline/main_pipeline.py` 删除 `_load_state`、`_write_state`、`_update_primary_state`、`_update_analysis_state` 及其私有辅助；主求解与历史分析数学骨架不再读取/重写整份project_state，不改变后端、代际、审批、交付/验收状态、stale或框架。项目控制状态由既有交付、回执和同步事务登记，未将事务引擎复制进数值支撑包。

主/分析runner的 `framework_sync_hook` 参数、类型别名、框架同步stub及自动sync命令建议退出；五类starter同步移除框架回调及无用导入。旧调用传该参数在任何数学钩子和输出执行前报错，不做静默忽略。调用者需要移除回调，改由控制面接收工作簿后记录；旧任务源码/工作簿不被自动改写。

`run_pipeline` 不再导出，直接模块中的旧名称只保留拒绝执行并说明迁入路径的退出提示；不会自动连跑主求解和分析。`run_result_analysis_pipeline` 也退出包级默认导出，仅保留显式直接模块的历史内存适配。这一适配不能证明主工作簿accepted或Analysis Necessity Gate=required，不能当作当前独立03B入口。当前正式分析仍须有独立配置/代码/回执并通过原前提。历史复现需要原版本环境，不把旧writer重新接入活动流程。

保留全部数值骨架、数据审计、能力标志、求解/约束/质量检查和Primary Evidence Capture内容；失败主质量仍先写工作簿再抛错，分析failed/redo仍保留证据并阻断。redo信息改为需要验收控制面登记回退与失效，不再声称已写stale。ResultAnalysisResult中的原因、方法和回退建议只是兼容内存数据，不表示真实项目状态已经变化。本地质量成功日志也明确仍需独立回执验收。

管线引用IO改为明确的包内相对静态导入；仅显式平铺模块使用正常同目录导入，不捕获内部ImportError后切换全局同名模块。默认推荐提取必要数学模式的自包含入口，确有需要才复制声明完整闭包的IO或支撑包。没有豁免模板、降低来源检查、自动生成1.1回执，或宣称这套数学骨架自身具备正式交付资格。

### 18.3 复现、回归与证据边界

修改前固定基点完整单测实际完成1546项，skipped=3，168.506秒，OK；lint与生成检查通过。独立临时维护探针复现旧主runner在generation=7不变时重写state、丢失注释并登记workbook_received；只证明模板自身旧写路径行为，不证明用户项目发生过损坏或误验收。

新增22项状态隔离回归，覆盖成功/失败工作簿、无state不创建、原始注释/CRLF/不透明状态字节、钩子期间外部更新不被覆盖、各计算钩子和IO异常、非法质量表、历史分析passed/failed/redo、旧参数和组合入口在计算前拒绝、默认导出、五个starter调用签名、同包依赖缺失不转全局fallback、显式平铺import无输出。对原始state和框架按字节比较，同时保留主结果值1.0、分析指标2.0和失败表的具体断言。

原有两个直接测试文件保留测试数量、数学/错误/证据断言；原先要求模板写状态的断言按本次明确破坏性职责调整，替换为更明确的状态/框架原始字节不变断言，而不是删除测试掩盖冲突。开发阶段22项新增、8项直接旧测试与11项真实复制包1.1交付/执行/回执测试合计41项通过（12.161秒），属于最终全量子集，不重复累加。完整候选、生成、精确远程源码和CI结果在PR完成记录分列。

所有运行均为临时维护微例或既有回归，不执行用户赛题。本批隔离测试不是数值验收/模型批准测试；故意不透明的状态用于确认数学骨架不持有writer权限，不能推断正式交付允许无效状态。任意Python自定义数学钩子仍有写文件能力，需服从既有静态来源/工程质量门；本库不是操作系统沙箱，也不证明非协作并发全局原子性。

### 18.4 兼容性、剩余工作与回滚

这是10.0.0候选中的明确接口破坏性清理，不伪装成旧模板完全兼容的小修。框架回调和组合runner不能继续使用；原历史分析适配只为显式维护保留，并已退出默认入口。结果表/工作簿格式、1.1回执、PQS、现有审批/数值/来源门及独立协议版本不变。

本批没有开放select/migrate、执行项目迁移或切换canonical Schema；也未修改预处理、MATLAB数值/正式绘图、LaTeX、CI工作流及release carrier。后续仍须完成确认与协调提交、当前绑定退役持久化、Schema与runtime/stage/delivery/receipt/snapshot/sync/package统一、活动入口/版本范围和T01—T30整体回归。模板writer退出不等于所有活动选择路径已统一。

保持同一Draft PR，不合并、不发布；正常revert本批源改动并重新生成索引/清单即可撤回本批代码。未执行用户状态写入，不回退用户generation或重写历史证据；此前journal v2未完成事务必须先由支持v2的实现恢复的降级限制保持不变。

## 19. 第七批：项目后端声明判断进入共享只读层

### 19.1 范围与权威边界

本批从第六批最终HEAD `43cb7cfde344224326aaec23334adecb044dd418` 继续，依据P0第6.2节与P1第3.2、9.2节，把已有的全题后端声明分类放到 `scripts/stage_code.py`，由 `scripts/project_solver_backend.py` 的既有公开函数薄转发。该函数只读取传入状态，报告根选择、历史候选、各问声明及请求冲突；不读取项目文件、不恢复事务、不写状态，也不授予数值执行资格。

本批保留原检查顺序、报告字段与错误语义，新增跨问冲突、非法根字段、历史一致/混合、反向请求和输入不变的专项回归。共享层为后续canonical Schema与消费者切换提供唯一纯判断入口，但当前活动Schema、运行/交付/回执/同步/打包行为仍为v9.7.1。不能把本批的只读分类说成v10正式策略已经启用。

### 19.2 后续闭合条件

下一主体仍须按P0/P1统一切换根状态Schema和全部正式消费者，再开放具有明确状态代际、原始字节读集合、影响确认、历史归档及可恢复事务的select/migrate写侧。现有迁移预览及其摘要本身不构成用户确认或写入授权；旧文件存在时的snapshot/sync重新发现风险必须在正式迁移前解决。保持同一Draft PR，不合并、不发布、不运行或迁移用户赛题。

### 19.3 本地验证与证据边界

新增5项共享策略专项，检查未选择不按环境推断、根字段必须成对且有效、跨问声明冲突、历史一致/混合及反向请求无写入。既有inspect/preview和下游身份专项继续通过。共享函数主体与原实现逐字相同，旧公开入口保持签名并只转发；本批没有修改正式消费者的调用关系。

当前工作树完整单测实际运行1573项，1565通过、8项条件跳过、无失败，153.350秒，OK；`scripts/lint_skill.py`、`scripts/generate_indexes.py --check`及`git diff --check`通过。这里的跳过数是本机此次运行结果，不改写第六批的历史计数；精确提交的远程CI须在本批提交后另行核对，不能借用上一HEAD的成功状态。

## 20. 第八批：canonical 项目策略与正式消费者闭合

### 20.1 基点和改动边界

本批从第七批最终HEAD `4b374698cad9c62de4ecc1ee588afb781510cda2` 继续；main仍为 `34deb02ff590d061fc7ca36f9bd2742a6653c797` / Skill 9.7.1，PR #230保持Draft。沿用第13.1节冻结的独立版本与唯一协调CLI设计。本批把项目级后端选择推进到当前状态及正式读者，但尚未开放select/migrate写侧；没有运行或迁移用户赛题、合并main或发布10.0.0。

### 20.2 本批实际接口

Project State Schema升至 **8.0.0**：当前状态只在根 `execution.solver_backend` 和 `execution.solver_backend_selection_reason` 记录一次选择，primary/analysis阶段只记录真实bundle与验收bundle。User Execution Contract升至 **3.0.0**，Runtime Assurance Contract升至 **2.0.0**，明确两阶段必须继承同一项目选择。State Transition维持既有 **1.2.0**；RUN_CONFIG/RECEIPT仍为 **1.1.0**，其中backend是运行事实而非第二选择权。

`stage_code`和项目状态验证器拒绝双策略、非法根值、当前数值身份缺根策略及阶段/RUN_CONFIG/源码冲突。runtime解析、代码交付、回执、分析前提都读取全题策略；交付在实际提交前重读当前状态并复核预处理决策和数据身份，不依赖先前静态检查时的旧状态。已验收分析若缺源码/bundle，或`not_required`仍登记当前analysis身份，不能提升validated_results。

snapshot/sync只让已登记、符合项目后端的入口和标准工作簿取得当前资格；目录旧文件作为历史观察，不因扫描而重新激活。正式同步在缺策略时拒绝写，并用`write_performed`区分请求写入与实际写入。正式复现包要求当前已验收阶段、对应源码bundle、工作簿哈希和真实输入闭包；旧文件或同后缀替身不能凑齐必需集合。框架消费者读取根策略。只读迁移预览对真实v9状态保留历史适配，对canonical状态不再注入阶段选择器。

旧跨问混合原生正例改为**两个独立项目**：Python项目内Q1/Q2和深化分析均为Python，MATLAB项目内已验收Q1与原生Q2均为MATLAB；相反后端交付及混合历史仍为负例。Python矩阵、Windows、MATLAB和LaTeX CI任务未删除。历史状态和工作簿的原始字节未批量改写。

### 20.3 验证和剩余工作

本地开发期完整unittest在最终补充残留哈希守卫之前运行 **1622项、8项条件跳过、无失败**；补齐守卫后改用逐项记录的`cmd`运行，**1623项、8项条件跳过、无失败，188.762秒**。此前两次PowerShell/.NET进程异常中断没有测试汇总，不计入通过。另在本机MATLAB R2025b实际运行合成Q1主求解/独立深化、原生Q2及对应交付/回执；同后端smoke通过，预览适配修复后对原生已验收结果的`verify-analysis`复核返回0。原生测试只使用仓库维护夹具，不是用户模型运行。生成检查和精确HEAD CI在提交后另行登记。

首次推送的`cc83b148`完整HSK Skill CI **13/13任务成功**（含Windows Python、MATLAB R2024b、Python矩阵、LaTeX、lint与生成）；本地同一HEAD完整unittest **1623项、8项条件跳过、无失败，191.086秒**。并行Optimization baseline的source_snapshot成功，characterize失败：旧P2读取夹具只有accepted标签/工作簿，没有v10根选择或源码bundle，正确的新门将其降为待复核；比较器还只认旧Assurance版本。没有把这次失败改写成绿色或删除工作流。

后续在同一第八批修复测试证据：`reading_plan_cases.py`为当前正例登记canonical Python根策略和1.1主/深化源码bundle；`test_reading_plan.py`保留独立旧accepted缺根负例，必须`review_required`且不得提升`validated_results`。`reading_plan_evidence.py`只登记精确的Assurance 1.2.0→2.0.0与根策略逐叶投影，不豁免结果资格、读取profile或整个assurance。用固定P1源码归档`0eecaf9`和当前工作树重新运行同一比较器，**19/19案例通过、未登记字段差异为0**；相关45项测试通过（1项条件跳过）。新精确HEAD远程CI仍须再次核验。

下一主体仍需按第13.1、5—6、8—9节实现绑定真实状态代际、原始字节集合、影响确认、历史归档和可恢复事务的select/migrate；再清理活动入口/精确读取/适用范围及Skill 10.0.0发布载体。当前候选的契约版本不等于10.0.0已经发布。第八批源与生成派生文件分提交；不能合并半套政策，保持Draft、不合并、不发布、不迁移用户项目。

## 21. 第九批：显式项目后端选择、确认迁移与持久历史

### 21.1 范围和写入入口

本批在第八批的 canonical Project State Schema 8.0.0 和正式消费者基础上，开放 `scripts/project_solver_backend.py` 的只读 `inspect`、首次 `select`、显式 `migrate` 三个入口。`select` 要求 `python` 或 `matlab`、非空选择理由和预期状态代际；检查全题已有模型/能力记录以及原状态、已登记框架的当前有效性。完全未选且没有历史数值阶段的项目走首次选择；同值同理由请求只读幂等，同值理由修订不误作数学模型变更，改换已锁后端或存在历史逐阶段策略的项目不能借 `select` 绕过迁移。根策略和框架中的全项目工作记忆受同一状态事务保护，候选校验读取 staged 框架字节。选择结果明确环境尚未验证、数值执行尚未获准，也不生成新的 Model Approval。

### 21.2 预览、确认和阶段影响

`inspect --migration-target ... --reason ...` 从项目实际状态、已登记来源、bundle、输入、工作簿及既有迁移历史生成只读预览，列出全题阶段影响、读集合、原始 state SHA-256、状态代际、`preview_sha256` 与 `effects_sha256`。`migrate` 必须分别提供目标与理由、`expected_generation`、`expected_state_sha256`、已审阅的两项摘要及 `--confirm-migration`；写前重新预览并重核项目、字节集合和影响。未确认、同代际 state 原始字节变化、目标或理由改变、已存在历史证据漂移均阻断。完全未选项目改用 `select`；同后端仅修订理由也改用 `select`。

同语言且重核通过的 accepted 来源、工作簿、bundle 和既有 Model Approval 关联可保留；跨语言的原当前绑定退役，受影响数值阶段和论文片段回到需重新交付、核验的状态。旧源码与工作簿仍保留为历史字节，不能因目录扫描而取得当前资格。迁移本身不代表新后端数值执行、回执或验收已经通过。

### 21.3 原始归档、报告和故障边界

协调器先用既有归档库复制并核验声明读集合的原始字节，归档位于 `state/backend_history/{migration_id}/`。经候选校验后，同一 journal 事务协调框架、state 和 `state/backend_migration_reports/{migration_id}.yaml` 的写入；Schema 的 `execution.backend_migration_history` 顺序追加 manifest、报告路径及各自原始字节 SHA-256 引用。先前引用必须原序保留并重核归档和报告；状态验证器也检查当前引用的路径、摘要与实际字节。候选校验针对 staged 框架、staged 报告和新 state，不以旧盘文本冒充新候选。

在 journal prepared 前失败时，当前 state、框架和报告保持原字节；已完成复制但未获引用的归档可留作检查，不能自动复用或删除。prepared 后的中断保留 journal，要求显式恢复并按既有事务语义向前完成；只读 `inspect` 不代替恢复。已提交 journal 的清理另核对目标字节、代际及归档，遇第三方改动则阻断清理并保留 journal，不能静默覆盖证据。

### 21.4 开发验证与未完成核验

本批开发期专项实测：迁移 **13/13通过**，首次选择 **11/11通过**，历史 Schema/框架 **6/6通过**；事务相关 **100项执行、3项条件跳过、无失败**，此前相关回归 **96项执行、1项条件跳过、无失败**。这些集合可能重叠，不相加成完整单测总数。新增测试覆盖首次选择及幂等/拒绝、独立预览确认、同/异语言 accepted 阶段、原始字节归档与报告引用、候选失败、prepared 中断与显式恢复，并保留既有 CLI 和事务回归。

首轮全量 `unittest` **执行1655项、8项条件跳过、1项失败**：`tests/test_v830_editable_mechanism_diagram.py` 的精确 Git blob 防漂移断言仍钉在第八批 Schema 字节。第九批授权增加严格 `backend_migration_history` 后，Schema 当前 blob 为 `11880dc6c8377245c4cec428f7b2a8f46d3d042f`；只将这一项保护哈希重钉到新字节，保留其他 Authority 的原断言。首轮失败照实保留，不改写为通过；后续复验分别登记。

保护哈希修复后、进一步边界复审前，完整 `unittest` 实测 **1655项、8项条件跳过、无失败，218.074秒**；另一次 Windows 进程以 `0xC000001D` 异常退出且没有汇总，不计为通过或测试失败。这两次都不是下述复审修复后的最终候选。生成器刷新后的 lint、索引检查与 `git diff --check` 在此前候选通过，修复后须重跑。

### 21.5 复审发现的恢复与保留边界

复审发现，同后端迁移曾允许历史 `awaiting_user_execution` 交付绑定在未复核 Model Approval 时成为当前；state 内自洽的批准 SHA 也不能替代框架真实 Semantic Identity Block。现在所有拟保留的数值绑定都复核现行 Model Approval、框架 Q 段结构化身份与文本身份；拟保留的分析阶段还核 Analysis Necessity Gate。维护夹具从真实框架 SIB 计算批准身份，并新增未批准交付、伪造 state 摘要和未裁决 03B 的负例。旧历史无法通过时阻断保留，不制造新的批准。

另一只读复审复现了历史 `paper_framework.sha256` 与当前框架文本漂移时，迁移预览仍可能给出可审阅状态，随后渲染新框架把旧漂移掩盖。预览现在按既有框架文本摘要算法复核已登记的旧摘要，不一致就阻断；只读历史缺此字段仍允许预览，但不能凭预览取得数值资格。新增框架末尾追加内容而 Q1 SIB 与节摘要不变的负例，预览须 blocked 且原 state/framework 字节不变；相关迁移预览/写侧定向 **85项执行、1项条件跳过、无失败**。最终完整复验仍待完成。

旧归档不仅在预览时核 manifest/成员，而且在 `select` 理由修订和 `migrate` 的写侧作为历史依赖绑定；v2 journal 在 prepared、显式恢复及 committed 清理时复核完整旧归档，并保存受保护读集合中所有非写入目标的原始 SHA/null，包括旧报告及已验收源码、工作簿和输入。旧 v2 日志缺此新增字段时维持原有兼容行为，不伪称旧日志已受新字段保护。事务日志的临时/备份清理路径须与事务 ID、目标和序号生成的精确文件名一致，且在任何 journal 恢复/清理前核对仍存在的 stage/backup 原始摘要；同名文件被第三方替换时保留文件和 journal，不删除未知字节。新增 v1/v2 清理负例，事务相关 **91项执行、3项条件跳过、无失败**。普通 writer 不再隐式恢复 v2 归档事务；同步和默认状态校验只读遇 pending journal 报 `recovery_required`。旧 v1 自动恢复语义保留，未知残留字节同样阻断清理。

同步写侧已对 state、框架和同步报告使用字节读集合；其观察期间读取的全部外部代码/数据/工作簿尚未形成完整的同步专用原始字节集合，非协作进程在观察与提交之间修改这些文件仍需单独处理。不能据本批声称项目级全局原子性。上述恢复/保留边界修复后、框架漂移修复前，完整 `unittest` 实测 **1668项、8项条件跳过、无失败，238.725秒**；lint、索引检查、`git diff --check` 同一候选通过。框架漂移修复后的最终完整单测与精确提交 HEAD 远程 CI 待核后登记；开发测试使用临时仓库维护夹具，没有迁移用户赛题。PR 保持 Draft，未合并 main 或发布 Skill 10.0.0。Skill 10.0.0 的 release carrier、适用范围声明、精确读取入口、lint 硬编码及生成派生文件仍按第8.3—8.4与9.2节分批核对；当前 Schema/契约版本不是已发布的 Skill 版本。

第九批最终源提交 `1c799e29f97ea0a0bf71fa996647bb131db84d5f`、派生索引提交 `e0a0105a111e79472fb549ad23e854eb06ca3b40` 后，本地完整 `unittest` 在精确 HEAD 实测 **1672项、8项条件跳过、无失败，233.591秒**；lint、生成索引 `--check` 与 `git diff --check` 通过。GitHub 上该精确 HEAD 的 HSK Skill CI **13/13任务成功**（包含 Windows Python、MATLAB R2024b、Python 3.10—3.14、LaTeX、lint 与生成文件），独立 Optimization baseline evidence 工作流也成功。上述结果只证明第九批精确提交；第十批及任何后续源码变化须重新验证，且 CI 成功不等于 PR 合并或 10.0.0 发布。

## 22. 第十批：10.0.0 候选入口、精确读取与活动文案

### 22.1 当前载体与独立版本

按第8.3—8.4节将 bootstrap、router、manifest、output、writing runtime、prose patterns、plugin 元数据、双 SKILL 入口、README 首行、CHANGELOG 当前候选与核心政策标题统一为 Skill `10.0.0`；这是 Draft PR 的候选源码，不是已发布 tag。bootstrap 只增加一个 `project_solver_backend.py` 协调入口。治理、图形资产、工程质量、全局预处理、数值核验、任务分类与工作簿七处活动适用范围在保留各自原下界的同时续期到 `<11.0.0`。Project State Schema `8.0.0`、User Execution `3.0.0`、Runtime Assurance `2.0.0`、State Transition `1.2.0`、RUN_CONFIG/RECEIPT `1.1.0`、工作簿 Schema `2.3.1`、框架标记 `v0.8-project-memory` 各守独立协议版本；未随 Skill 主版本机械改号。lint 原固定 Python 两阶段断言改为核对当前双语言入口映射，同时明确旧五文件表只是 Python 历史投影。

### 22.2 当前阅读与文案

`reading_policy` 和独立 `reading_plan` schema 升至 `1.1.0`；纯 `model_selection` / `advanced_method` 且 Assurance `pass` 时，`read_now` 对 User Execution 的 `solver_backends` 实际缩小行范围和计划字节，原 `load_order` 与机器依赖闭包不改。结果工作簿验收与项目同步读取此策略；缺失、歧义或非法选择器有显式全文回退，缺文件则报错，不返回空规则。`project_backend_navigation` 单列只读导航元数据，指向唯一 `inspect/select/migrate` CLI，`execute: false`；不混入需执行的 `tool_interfaces` 或 `pre_delivery_gates`，也不代表已得到某个真实项目的迁移确认。

活动文档、模块、Artifact Pack、代码附录说明和数值模板把“本问/本阶段另选后端”的许可改为项目根唯一选择；全局框架口径只登记一次项目后端及理由，各问保留独立数学 solver、实现锚点、证据与条件式深化。`agents/openai.yaml` 不再固定要求 Python 求解，MATLAB 的只读限制仅指正式绘图。项目级 Python 预处理、同项目后端的 question_local 变换、正式 MATLAB Figure Evidence 与独立论文工具职责保留。README 的长版本史及普通写作导航仍须依 P0 §5.2 在下一独立源批次审慎整理，不以本批仅改首行冒称 README 重组已完成。

### 22.3 同步观察竞态与验证边界

第21.5节记录的数值来源竞态已经用临时项目复现：观察完成后改动主源码，旧同步仍可提交基于旧 SHA 的 `passed` 报告。本批为同步写侧在观察前登记已声明源码、helper、输入、工作簿、图脚本/图证据的原始 SHA 或缺失事实，snapshot 后交叉核对观察摘要，提交前复核发现集合和同一 read set，再交既有字节绑定事务。并发改主源码、helper、输入或工作簿的负例均阻断，且 state、框架、报告不写入。此修复保护数值同步的观察—提交边界；非协作方在 journal prepared 后再修改非写入来源、formal LaTeX/ZIP 等间接读取和目录 ABA 不在本批全局原子性承诺内。

定向测试已覆盖载体版本、七处适用范围、阅读导航与精确范围、活动文案/模板以及同步并发负例；优化基线固定 P1 来源与候选工作树的 **19/19 案例通过、未登记 legacy 差异为 0**。首次完整 `unittest` 实测 **1685项、8项条件跳过、4项失败，243.770秒**；四项均为 `test_v830_editable_mechanism_diagram.py` 对两份已按计划续期的契约和两份已改项目后端文案的旧 Git blob 哈希。逐一复核精确 diff 后仅重钉四项，原防漂移测试 **26/26通过**；没有删除保护门或把首次失败写成通过。随后生成索引、完整 lint、索引 `--check`、`git diff --check` 通过；再次完整 `unittest` 实测 **1685项、8项条件跳过、无失败，240.777秒**。这些是本地候选源码树的证据，生成后的源/派生分提交及精确最终 HEAD 远程 CI 仍须另记；本地测试不替代原生平台任务。PR 保持 Draft，未迁移任何用户赛题、未合并 main、未发布 10.0.0。

第十批分为活动入口/读取源提交 `48f73621`、同步来源读集合修复提交 `1dd23d25` 和派生索引提交 `731413cc`，已推送同一 Draft PR #230，远端精确 HEAD 为 `731413ccb077950bf4658e3524465fbe27cc12e4`。该 HEAD 的 GitHub HSK Skill CI **13/13任务成功**（Windows Python、MATLAB R2024b、Python 3.10—3.14、LaTeX、lint、生成文件），Optimization baseline evidence 也成功。后续第十一批变更再次改变候选 tree，须单独验收最终 HEAD。

## 23. 第十一批：README 当前导航与残留许可清理

按照 P0 §5.2 将 README 从重复的逐版本长史改成当前简介、最短启动、项目数值职责、唯一 Authority 导航、最少检查命令和兼容/历史入口。版本演进交给 `CHANGELOG.md` 与 Git 历史；旧 v9 后端说明只作为历史资料链接，不再占据当前启动路径。旧 README 独有的七项专题资料入口逐一保留并验证目标；Algorithm Trace、普通正文/LaTeX 与复杂证据裁决分别委托现行 Pack、Paper Writing Protocol、LaTeX Adapter 和 Writing Reasoning Authority，不把旧首页长文当第二套政策。根与打包 SKILL 的历史指针和固定 Python 深化文件名发现断言同步换成 `core/output_contract.yaml#per_question.solver_scripts`，两入口保持字节一致。历史 Phase I 断言仍查 CHANGELOG 的真实记录，而不要求 README 再复制一份版本史。

活动文本复扫还在 `core/global_preprocessing_contract.yaml` 的 `question_local` 与下游入口、`core/workflow_router.yaml` 的 analysis 规则发现“本问/当前阶段所选后端”残留；现已原位改为项目根唯一后端继承。MATLAB 模板 README 的跨问/跨阶段混合 smoke 明确限定为 v9 历史兼容与 v10 拒绝回归，避免把负例当当前推荐路径。项目级 Python 预处理、各问数学 solver、正式 MATLAB 只读绘图和原输出契约仍保留。

README、双 SKILL 入口、版本矩阵及相关文档的定向测试 **71/71通过**；残留三文件相关 **65项通过、1项条件跳过**；README 本地 Markdown 链接/fragment 核对通过。第十一批候选树生成索引、完整 lint、索引 `--check` 与 `git diff --check` 通过；固定 P1 基线的运行时比较 **19/19通过、未登记差异为 0**；完整 `unittest` 实测 **1686项、8项条件跳过、无失败，399.316秒**。上述本地测试在审计文字最终补记前运行，源与派生提交后的精确 HEAD CI 与原生任务结果仍须另记，不沿用第十批 HEAD 的结论。
