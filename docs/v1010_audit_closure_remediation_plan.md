# v10.1.0 仓库审计闭环修复计划与执行台账

> 本计划只处理 2026-09-25 只读审计确认的 AUD-01—AUD-05。用户已授权“先写详细计划，再依据计划修正”。计划先提交，修复后回填实际证据；未核验事项不得标为通过。
>
> **当前进度：S0—S5 的实现、差异审阅和功能验收已完成。** 功能提交 `1ca2aea15f76d09664a66b9e019f3bc000a29342` 已通过本地完整1730项测试（3项条件跳过）、远程主CI的13个jobs及优化基线比较，详情见第16节。本文回填之后的最终分支head与实际合并状态，仍须由PR #236的最后验收记录绑定；不以旧head的绿色结果替代新head验证。不创建Release，不移动tag，不修改任何真实用户项目。

## 0. 基线、授权和修改简报

| 项目 | 记录 |
|---|---|
| 仓库 | `Vexushi1/mathmodel-skill` |
| 初始基线 | `main@0fc52fa47abf457ef4e180ac7a291583cd9be68f` |
| 基线 Skill | `10.0.1` |
| 本轮分支 | `upgrade/v10.1.0-audit-closure` |
| PR | [#236](https://github.com/Vexushi1/mathmodel-skill/pull/236) |
| 目标 Skill | `10.1.0`；辅助输入为可选协议扩展，按 minor 评审 |
| 计划先行提交 | `ed77fd5f930f0ff9e60855e2fa7e1743952c5e12` |
| 协议裁决先行提交 | `88f63856da4734e7045490116d01203b8459ddb4` |
| 授权范围 | 编写本计划、复现和修复五项问题、回归测试、完整 CI 核对 |
| 不重叠 PR | #235 仅新增功能计划，不接管、不修改、不合并 |

**直接目标：** 补齐“真实输入 → 当前执行资格 → 项目后端 → 模型批准 → 下游消费”的既有可信链，修正文档职责错指，不推翻项目统一后端设计。

**明确不做：** Case Memory、Claim-Evidence Graph、Independent Reviewer Receipt、通用 Code↔Model 新系统；不改用户赛题、数据、数学模型、数值结果；不自动迁移项目或批准模型；不变更 GitHub Settings；不混入无关模板重构。

**权威来源：** bootstrap、Skill 修改治理、User Execution、Global Preprocessing、Runtime Assurance、Project State、Model Approval、Output、State Transition 各自负责已有职责；普通正文由 `modules/05_writing/paper_writing_protocol.md` 管理。新 helper 不成为第二 Authority。

**版本纪律：** Skill 载体为 10.1.0；User Execution 3.1.0、Runtime Assurance 2.1.0、State Transition 1.3.0 按各自变更维护。Project State Schema 8.0.0、源码 bundle 1.1、项目级预处理回执 1.0 均不变。主/深化默认回执 1.1，只有显式辅助输入路径使用 1.2。

**兼容策略：** 旧 `resolve_workflow.py` 无状态接口及旧 1.0/P5a/FULL 读取按原规则保留；无辅助输入的合法 1.1 实例保持可用；不倒填历史字段。当前 `resolve_runtime.py` 的数值任务省略后端参数时等价待选择，不再隐含 Python 规划。

**回滚：** 未合并可撤回 PR；合并后 revert 回经过验证的基线。没有真实用户项目迁移。1.2 新实例不得删除辅助字段后伪装成 1.1；旧 reader 应明确拒绝未知协议，回退必须保留该边界。

## 1. 审计问题、证据与完成定义

| ID | 问题 | 基线证据 | 修复完成定义 |
|---|---|---|---|
| AUD-01 | 原始输入修改/删除后，未 sync 的公共主结果前提仍可能通过 | 组件复现；现有输入观察器可单独检出 | 公共前提、runtime、分析交付/receipt 均检查实际来源，不洗白状态 |
| AUD-02 | 预处理允许独立附件，但执行身份只能唯一预处理 XLSX | 合同冲突及真实函数拒绝两文件 | 主来源与辅助集合分开绑定，配置/回执/双后端/sync/package/迁移闭合 |
| AUD-03 | bool revision 被视作整数1 | 原审批 CLI `--strict` 错误 PASS | current/approved/validated revision 统一拒绝 bool/float/string/null 等 |
| AUD-04 | 新 assured 入口省略参数仍有旧 Python 投影 | 入口和源码对照 | 数值任务默认中立，当前项目继承，旧接口明确保留 |
| AUD-05 | 脚本导航把普通正文职责交给 LaTeX Adapter | 当前 Authority 对照 | 委托指向现有 Paper Writing Protocol，不复制规则 |

基线组件漏洞不等价于整条正式交付已被绕过；历史 CI 全绿也不替代新增反例。必须保留正常控制组和失败证据。

## 2. 必须保持的不变量

1. 后端依据全题模型、求解器能力、依赖/许可证、规模与复现成本判断，不按题型机械选语言，不因绘图为 MATLAB 就偏选 MATLAB。
2. 项目根 `execution.solver_backend` 是唯一选择；主求解和条件式深化继承；`auto` 是待判断而非自动环境验证。
3. 项目级预处理仍为 Python、正式数据图仍为 MATLAB；本问数学变换随已选后端，这不是逐問混合求解。
4. 模型批准不能由代码、工作簿或迁移制造；实现/输入新鲜度与数学语义改变分开。
5. 两个旧状态哈希相等不证明当前磁盘输入未变。
6. 检查默认只读；不能刷新已交付/已验收哈希使旧运行重新有效；写入仍走现有状态转移和事务。
7. 数值验收、来源身份、视觉渲染、论文语义互不替代。
8. 同类解析、输入观察、哈希与前置资格应共享，不新增各自宽松的 consumer 副本。
9. 新字段必须完整，未知版本/模式、半字段、路径逃逸、别名、覆盖原始源均不得被静默忽略。
10. 不降低数据量、网格、时域、重复次数或容差来通过测试；合成 fixture 不代表用户正式计算。

## 3. 分阶段实施和退出条件

| 阶段 | 目标 | 退出条件 | 当前记录 |
|---|---|---|---|
| S0 | 固定基线、取得可信完整源码 | main/PR 核对、逐文件身份核验 | 完成：固定 Git archive，571 个 blob 核验一致 |
| S1 | 先冻结真实失败、审阅调用链 | 正常/负例控制，协议最终裁决 | 完成：13 个基线测试中20个失败子例，零执行错误；决定可选1.2 |
| S2 | AUD-01/AUD-03 资格漏检 | 实际输入与严格类型，未制造批准/验收 | 完成：当前功能提交的1730项本地测试与远程矩阵通过 |
| S3 | AUD-02 辅助输入身份闭环 | 合同、解析、实例、receipt、sync、package、迁移 | 完成：Python合成运行与MATLAB R2024b原生1.2步骤均通过 |
| S4 | AUD-04/AUD-05 入口和职责 | 新中立、旧兼容、委托唯一 | 完成：差分、文档及精确变更登记的正负例通过 |
| S5 | 版本/生成物/最终远程验证 | lint、完整测试、精确最终head CI、无临时流程 | 功能验收完成：第16节；文档回填后的最终head及合并以PR最后记录为准 |

实现按上述顺序完成，本地冻结后以原文件与新文件 SHA-256 校验的精确增量提交，不用逐文件手工复制未测版本。PR 属于同一“资格证明链闭环”主题。任何远程失败仍按对应阶段回退，不以此表替代实际CI。

## 4. 环境与源码真实性

直接 `git clone` 仍因 DNS 失败。通过仅本分支触发、contents:read、固定基线、`persist-credentials: false` 的临时 Actions 快照导出公开 Git 跟踪文件；不包含 `.git`、凭证、环境变量或用户项目。下载后逐一核验571个Git blob，零差异，再建立本地完整工作副本。

快照 run：`36098787727`；artifact：`10848460988`。原始ZIP SHA-256：`4aba961908edb60591cdc7b94ec17fb7a88aa620d85d16eab6a5440399d11d5a`。

本地环境为 Python 3.13.5、PyYAML6.0.3、pandas2.2.3、openpyxl3.1.5。没有本地 MATLAB 原生运行证据，不将静态检查当原生验证。

精确补丁传输使用一次性分支限定维护桥接：固定58个源码/测试/载体路径，核对基线和新 SHA 后才写入，生成文件仍由现有生成器处理；CI工作流的2行原生测试通过Connector独立写入。两份临时工作流已经删除，不成为正式功能或常驻写权限入口。没有强推 main。

## 5. AUD-01：实际输入新鲜度

### 5.1 实施落点

`analysis_prerequisites.stage_input_issues` 复用 `stage_inputs.observe_inputs`；主结果公共前提及适用分析路径检查真实输入，runtime 不再仅靠保存的旧数据哈希提升 accepted 资格。代码交付、回执验收、同步和打包消费相同来源规则。

适用新1.1/1.2时，实际路径、源码bundle、配置、数据及工作簿必须一致；旧协议按既有只读兼容处理。source/data在验收计算期间变化，也必须在接受前重新核验。

### 5.2 禁止行为

不能把观察到的新摘要写入 `data_hash`、`validated_data_hash`、`bundle_sha256` 或 `validated_bundle_sha256` 来通过检查；不能读取失败后退回全局数据集合；不能为了检查而导入/执行用户求解脚本。

### 5.3 回归要求

A01 未变通过；A02 原文件变动未sync失败；A03 删除未sync失败；A04 helper变动失败；A05 工作簿变动失败；A06 显式stale失败；A07 runtime不再提升旧结果；A08 分析不能消费旧主结果；A09 两后端配置覆盖；A10 只读检查文件不变；A11 旧协议控制；A12 不回退未声明全局输入。

## 6. AUD-02：预处理主来源与辅助输入分离

### 6.1 已冻结的协议裁决

初稿曾提出在1.1上增加可选字段；在实现前复核旧reader后否决，因为旧reader可能忽略新字段。先提交 `docs/v1010_input_identity_protocol_decision.md`，再实现可选 RUN_RECEIPT **1.2.0**。

- 无辅助附件继续使用原合法1.1；项目级预处理仍1.0。
- 只有 project_level 主/深化计算需要独立附件时使用1.2。
- 主 `data_paths` 仍恰含当前accepted预处理XLSX，主 `data_sha256` 仍其普通文件SHA。
- `auxiliary_data_paths` 和 `auxiliary_data_sha256` 必须成对完整；前者严格非空相对路径列表，后者沿用现有 combined_hash。
- 配置和回执版本必须匹配；旧1.0/1.1携带辅助字段拒绝，1.2缺字段/错模式拒绝。
- 回执路径列表使用JSON文本适配XLSX配置表；严格解析并与交付配置比较，不将字符串相似视作一致。
- 源码bundle仍用既有1.1算法，不新增State Schema数值事实副本。

### 6.2 路径、运行与范围

辅助路径须真实存在、唯一、项目内、无符号链接/大小写或硬链接别名；不能与主输入相同，不能重读 `covered_raw_sources` 已覆盖原始源。不能以code_dependencies伪装数据。

运行前绑定、成功写出前复核源码/主数据/辅助输入。分析仍绑定accepted主工作簿，不能借辅助通道自动修改数学口径。相同预处理XLSX下辅助约束改变仍是不同计算输入；既有审批是否失效由真实语义变化决定，不由输入观察函数直接裁决。

旧固定基线的stage binding和receipt检查对1.2拒绝已实际验证；不声称旧reader能完整支持1.2，也不把新实例降级伪装为1.1。

### 6.3 调用链落点

| 层 | 当前实现 |
|---|---|
| 字段/行为Authority | `core/user_execution_contract.yaml`；preprocessing/output仅委托 |
| 共享协议形状与回执比较 | `scripts/execution_protocol.py`，不拥有业务Authority |
| 实际输入观察 | `scripts/stage_inputs.py`，返回主及辅助真实路径和身份 |
| 交付/验收 | `validate_code_delivery.py`、`validate_user_execution.py`，配置、回执、前后来源核对 |
| 当前资格 | analysis_prerequisites + runtime_assurance，不能依赖先sync |
| 同步 | project_snapshot记录观察问题；现有状态引擎传播相应主/分析失效 |
| 打包 | 现有submission requirements消费完整输入路径，遗漏辅助文件拒绝 |
| 迁移预览 | 完整收集辅助来源并核验，不静默遗漏归档输入 |
| Python/MATLAB | 合成原生实例/模板前后核对，回执记录实际输入 |

### 6.4 回归要求

B01 原单XLSX通过；B02 合法独立约束通过；B03 多辅助排序可复算；B04 修改失败；B05 删除失败；B06 半字段失败；B07 空列表失败；B08 重复主输入失败；B09 已覆盖源失败；B10 越界/符号链接/大小写/硬链接别名失败；B11 回执摘要伪造失败；B12 analysis仍绑定primary；B13 打包遗漏失败；B14 Python真实运行；B15 MATLAB原生CI；B16 旧1.0/1.1控制；B17 不制造/撤销数学批准；B18 sync不得洗白；B19 验收质量计算期间源变动拒绝；B20 旧reader拒绝1.2。

## 7. AUD-03：严格的语义修订号

在现有 `semantic_identity.py` 中共享正整数类型检查和已声明revision检查；`validate_model_approval.py`、`validate_semantic_governance.py`、`runtime_assurance.py` 消费同一规则。Schema正确约束保留不变。

current、approved、validated revision 必须真正正整数；bool/float/string/zero/negative/null不能通过。相等比较前先验证两端类型。可选历史字段未声明与“已声明非法值”严格区分，不自动填值。

C01 1/1通过；C02 true/true失败；C03 1/true失败；C04 true/1失败；C05 1/1.0失败；C06字符串失败；C07零/负数失败；C08不等失败；C09hash不等失败；C10validated非法类型失败；C11实际strict CLI非零；C12runtime不提升错误lock；C13不写文件；C14合法structured/legacy控制。

## 8. AUD-04：新入口中立，兼容入口显式保留

当前 `resolve_runtime.py` 根据实际恢复后的模块判定是否数值/模型设计上下文，省略后端时使用auto语义。已有根选择继承，冲突报告，不写状态。尚未选择的项目不会因为先展示Python产物而被暗示固定语言。

与数值无关的纯写作/绘图任务不因此强加模板。分析请求若实际恢复至主求解，以真实stage选择资源。`resolve_workflow.py` 保留历史无状态投影；两个入口文档明确区分。`selection_complete`、`assurance.status`、`missing_prerequisites`不是同义字段，不把无冲突规划称作执行授权。

D01新省略参数中立；D02auto同等；D03Python候选；D04MATLAB候选；D05项目继承；D06反向请求冲突；D07全项目混用拒绝；D08实际恢复stage；D09legacy不变；D10纯写作/图样式不增数值模板；D11两入口说明一致；D12不自动select/migrate。

## 9. AUD-05：写作职责委托

修正 `scripts/README.md` 陈旧描述：普通正文结构和表达由 `paper_writing_protocol.md` 管理；LaTeX Adapter只负责载体；复杂推理和证据由reasoning Authority；固定骨架由Template Manifest。不复制任何正文规则，不重写历史说明。

E01正确Authority存在；E02陈旧委托消失；E03两份Skill入口一致；E04引用可达；E05Skill与独立协议版本不混用。

## 10. 影响面与大于20文件的原因

这是一个资格链修复主题，但完整闭环不能只改一个检查器。实现包含输入观察、共享前提、receipt、sync、迁移、打包、双后端模板、回归夹具和版本载体；某些既有测试也断言当前版本或依赖没有真实数据的fixture，必须同步而不能假装不受影响。

主实现/协议复用现有模块，仅增加一个小型共享协议helper；数值事实仍在accepted工作簿，状态仍在原Project State。没有新数据库、全局状态系统、通用Agent或新增论文工作流。

测试修订分三类：补上原fixture缺失的真实输入和正确摘要；把当前版本断言更新为实际10.1.0；经审阅后重新固定确实被授权修改的保护文件摘要。原有历史版本控制组、拒绝路径及有效断言保留，不能以删除检查降低验收要求。

新增测试/夹具：`tests/test_audit_closure_regressions.py`、`tests/test_auxiliary_input_protocol.py`、`tests/audit_auxiliary_smoke.py`、`tests/fixtures/solver_backends/python_auxiliary.py`。正式CI只在既有MATLAB job增加辅助输入原生烟测步骤，其他完整jobs保留。

## 11. 实际测试记录

| 轮次 | 实际结果 | 含义 |
|---|---|---|
| 固定基线完整测试 | 1686项，3条件跳过，无失败 | 旧回归集通过不代表新反例已覆盖 |
| 新增基线反例 | 13测试，20失败子例，零执行错误 | 证明确有预期缺口，不把fixture错误当bug |
| 定向修复回归 | 64项通过，1条件跳过 | 首轮输入/后端/类型路径 |
| 第一次完整修复回归 | 1720项，24失败、1错误、3跳过 | 如实保留；主要为旧fixture/版本断言和诊断衔接，逐项修复 |
| 第二次完整修复回归 | 1723项，3跳过，无失败 | 新旧路径完整通过 |
| 实现冻结本地完整回归 | 1724项，3跳过，无失败，309.251s | 加入直接writer非法辅助协议拒绝后再次全量；后续新增测量回归见下一行 |
| 接续功能提交复验 | 1730项，3跳过，无失败，311.047s | 对`1ca2aea`完整原始源码执行，包含6项精确基线差异登记回归 |
| 本地lint/索引 | 均exit0 | 生成文件由生成器产生，未手改hash；接续复验再次通过 |
| Python辅助协议原生 | primary/analysis真实运行及验收通过 | 辅助约束使答案3变4，非只回显元数据；分析保留主工作簿 |
| 旧reader拒绝新协议 | primary/analysis均拒绝1.2 | 无静默忽略辅助附件的兼容降级 |
| MATLAB本地 | 静态检查，未原生执行 | 原生结果只认远程CI |
| 功能提交远程CI | `36104012555`的13个jobs成功 | 精确head为`1ca2aea`；含原生MATLAB R2024b的1.2主/深化验证 |
| 功能提交优化基线 | `36104014476`的2个jobs成功、1个条件跳过 | characterize与源码快照成功；独立出版图预览未执行，不计为通过 |

本地命令：

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests -p 'test_*.py'
python scripts/generate_indexes.py --check
python tests/audit_auxiliary_smoke.py --project /tmp/audit-auxiliary-python --backend python
```

最后一条只能用于仓库合成fixture，不执行用户真实赛题。日志写在checkout外，不污染索引。远程最终head的静态lint、Python3.10—3.14、Windows、MATLAB R2024b、LaTeX和生成文件检查均应单独核对；未完成或失败保持PR draft。

## 12. 安全与失败处置

源文件检查不导入求解脚本；路径检查先于读取；非法字段、版本、非有限值或hash冲突给出可定位错误。来源观察异常不能覆盖其他有价值的门禁诊断，也不能吞异常后PASS。

当前输入变动后不得刷新accepted；存在material模型问题时，仓库修复授权不等于具体模型批准。远程原生失败应修复并重跑对应专项及完整CI，不能移除失败步骤。临时桥接只传输已测精确补丁，已经删除，不留常驻写权限流程。

## 13. 接管顺序

1. 读当前main bootstrap、治理、本计划和PR #236实际diff。
2. 核对main/head、开放PR和CI，不用本计划初始SHA代替当前事实。
3. 读当前失败或未完成阶段的完整源/测试，不只看摘要。
4. 如新增修复改变协议或范围，先更新裁决，再实现。
5. 专项→完整基础→生成物→最终head CI；记录实际命令和结果。
6. 核对临时文件已删除、文件白名单与测试保护无无关变更。
7. 只有完整验证和审查满足后才结束draft/合并；是否合并及merge SHA以GitHub实际结果记录，不提前宣称进入main。
8. 不自动发布Release，也不顺手合并#235。

## 14. 完成判据与剩余边界

- [x] AUD-01公共实际输入前提及相关本地反例通过。
- [x] AUD-02主/辅助身份、回执、Python原生、同步/打包/迁移本地闭环。
- [x] AUD-03严格revision及真实CLI回归通过。
- [x] AUD-04新中立/旧兼容差分通过。
- [x] AUD-05职责委托回归通过。
- [x] 实现冻结1724项及接续1730项本地完整测试均通过，lint/索引通过。
- [x] 两份临时workflow从分支删除，正式CI保留新增原生测试。
- [x] 功能提交`1ca2aea`的远程完整CI与MATLAB原生结果已逐项核实，见第16节。
- [x] 功能提交相对初始main的66路径差异与原有测试修订已经审阅，未夹带#235或用户数据。

**发布操作边界：** 上述勾选表示修复内容验收，不表示写入本文时已经合并。本文回填会形成新head，现有自动流程必须重新生成元数据并验证最终head，随后才能正常合并；最终head、CI、merge SHA和主干验证结果写入PR #236的最后验收记录。既有Release/tag不动，不用反复修改本文制造“记录自身提交”的自引用循环。

静态检查仍不是任意程序与数学模型等价证明；仓库合成fixture不是用户赛题验收；本轮没有宣称性能提升或全仓绝对无缺陷。

## 15. 固定基线来源

以下文件均对应 `0fc52fa47abf457ef4e180ac7a291583cd9be68f`，修复以完整源码和调用链为准：

- `core/user_execution_contract.yaml`、`core/global_preprocessing_contract.yaml`；
- `scripts/stage_inputs.py`、`scripts/analysis_prerequisites.py`、`scripts/stage_code.py`；
- `scripts/validate_model_approval.py`、`scripts/runtime_assurance.py`、`scripts/validate_semantic_governance.py`；
- `scripts/resolve_runtime.py`、`scripts/resolve_workflow.py`、`scripts/README.md`。

原审计仅提供线索；修复是否完成由本轮实际代码、反例、回归和最终CI决定。完整逐提交过程保留在 [PR #236](https://github.com/Vexushi1/mathmodel-skill/pull/236)。

## 16. S5 接续核验记录：2026-09-25

### 16.1 对象和来源

本次接续没有重新实现五项功能，而是核对已存在的PR、原始源码、测试和远程结果。功能head为`1ca2aea15f76d09664a66b9e019f3bc000a29342`，完整Git tree为`84dec4ff462d46eaca61b80ffffd6f0e1a7e0531`。

通过现有优化基线run `36104014476`下载源码artifact `10850602108`，ZIP SHA-256为`0ef14e3128efb7ada481a1c8157f5f88980d374936a7a7f43aa70ad8eded4d6b`，与GitHub摘要一致。解包后重建Git index，`git write-tree`与上述远程tree完全一致；原始main快照重建tree为`cf55378e46d949fd60679c86e507d9a0cc8fd69d`。这证明本地复验对应完整原始树，不是手工拼接片段；不表示普通网络git clone已经恢复。

### 16.2 本地和远程结果

本地重新运行lint、索引检查和完整单元测试，退出码均为0；单元测试实际输出为`Ran 1730 tests in 311.047s`、`OK (skipped=3)`。测试结束后工作树相对原始index无改动。此前1724项是较早的真实运行记录；1730项还包括随后补充的6项测量差异防放宽回归，不删除原失败历史。

远程[完整主CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36104012555)对同一功能head的13个jobs均成功，逐项包括Python3.10—3.14、Windows Python3.14、静态合同lint、生成文件、MATLAB R2024b数值链、三种LaTeX模板和正式编译证明。MATLAB job内新增的辅助输入1.2步骤确实执行成功，不是静态检查或skip。

远程[优化基线](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36104014476)的characterize与source_snapshot成功；Real MATLAB publication preview按条件跳过，因此只记2项成功、1项跳过。该跳过不是MATLAB数值验收失败，也不能冒称出版图外观已重新审核。本轮没有修改出版图样式实现。

同一head另有bot触发的PR事件记录`36104014797`、`36104014829`为`action_required`；未将其计为成功。上述实际完成的完整workflow_dispatch runs才是本节验证依据，不能用空事件状态替代jobs证据，也不能绕过平台实际要求的合并保护。

### 16.3 差异和测试保护审阅

相对初始main核对66条变更路径，内容限定于本计划的Authority、共享检查、执行/验收/同步/打包/迁移消费、双后端模板、回归、版本载体和生成元数据。不存在两份临时维护workflow的最终源码差异，未修改#235的新增功能计划，未引入用户赛题资料。

原测试修订主要为真实输入fixture、当前版本断言及实际改动保护文件的精确摘要。测量中只登记固定案例的版本和AUD-04中立后端投影，报告仍保留`legacy_behavior_equal=false`及逐项已批准差异；未知案例/版本、伪造环境验证、额外字段、selection_complete、实际资格和gate变化仍有失败断言。没有删掉整个assurance或solver子树来换取绿色结果。

本次收尾仅回填本文和PR验收记录，不再改变功能实现。文档及生成元数据形成的新head仍须通过既有CI后才能合并；不创建新一轮功能改造，不声明零风险或任意模型正确性。
