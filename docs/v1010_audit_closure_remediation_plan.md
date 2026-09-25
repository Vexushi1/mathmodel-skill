# v10.1.0 仓库审计闭环修复计划与执行台账

> 本计划只处理 2026-09-25 只读审计确认的 AUD-01—AUD-05。用户已授权“先写详细计划，再依据计划修正”。计划中尚未完成的阶段不构成已实现能力；所有测试、提交和验收结果必须按实际执行回填。

## 0. 基线、授权和修改简报

| 项目 | 记录 |
|---|---|
| 仓库 | `Vexushi1/mathmodel-skill` |
| 基线 | `main@0fc52fa47abf457ef4e180ac7a291583cd9be68f` |
| 当前 Skill | `10.0.1` |
| 本轮分支 | `upgrade/v10.1.0-audit-closure` |
| 计划目标版本 | `10.1.0`；辅助输入的可选协议扩展按 minor 评审，不把新增能力伪装成 patch |
| 授权范围 | 编写本计划、复现和修复五项审计问题、增加回归测试、核对完整 CI |
| 开放 PR | 本次读取仅 #235，为新增功能计划文档；不接管、不合并、不修改其内容 |
| 当前状态 | 计划已编写，功能实现尚未开始 |

**直接目标：** 将“真实输入 → 当前执行资格 → 项目后端 → 模型批准 → 下游消费”的已有可信链补齐；修正文档职责错指。不推翻 v10 项目统一后端设计。

**明确不做：** Case Memory、Claim-Evidence Graph、Independent Reviewer Receipt、通用 Code↔Model 新系统；不改用户赛题、数据、数学模型、数值结果；不自动迁移具体项目，不自动批准模型，不变更 GitHub Settings，不扩大到无关模板重构。

**权威来源：** `core/bootstrap.yaml`、`SKILL_CHANGE_GOVERNANCE.md`、`core/user_execution_contract.yaml`、`core/global_preprocessing_contract.yaml`、`core/runtime_assurance_contract.yaml`、`core/project_state.schema.yaml`、`core/model_approval_contract.yaml`、`core/output_contract.yaml`、`core/state_transition_contract.yaml`；普通正文职责以 `modules/05_writing/paper_writing_protocol.md` 为准。

**兼容策略：** 旧 `resolve_workflow.py` 无状态接口与旧 1.0/P5a/FULL 读取仍按原规则保留；不倒填历史字段。新 assured 入口不再让省略后端参数隐含 Python 规划。无辅助输入的现有 1.1 主/深化项目应保持可用；部分新字段和未知组合必须失败，不能回退旧协议。

**版本纪律：** Skill 载体统一到经过验证的目标版本；State Schema、回执、契约等独立协议只在各自实际需要时升级。不会批量替换所有版本数字，不移动既有 tag，不在未验证时发布 Release。

**回滚：** PR 未合并可撤回分支改动；合并后以 revert 恢复已验证基线。没有用户项目迁移，无需修改用户数值文件。若产生新可选辅助输入实例，旧版本不应将其误读为无辅助输入，必须保留协议识别与拒绝说明。

## 1. 审计发现与证据强度

| ID | 发现 | 已知证据 | 本轮必须补充 |
|---|---|---|---|
| AUD-01 | 直接原始输入被修改/删除但未同步状态时，共享 `primary_issues` 仍可能无错误 | 上轮原始源码组件隔离复现；`stage_inputs.observe_inputs` 单独可检出 | 在真实仓库 fixture 上复现 runtime、分析交付、回执和后续消费；证明无写副作用 |
| AUD-02 | preprocessing 合同允许独立辅助附件，但执行合同/输入观察器要求唯一预处理 XLSX | 合同对照及 `observe_inputs` 拒绝两文件复现 | 设计最小身份扩展，同时贯穿交付、回执、同步、打包和 MATLAB/Python 模板 |
| AUD-03 | bool 修订号被当作整数；批准修订 `true` 与 `1` 相等 | 原 `validate_model_approval.py --strict` 实际错误 PASS | current/approved/validated 三类 revision 在独立入口和恢复链统一严格类型检查 |
| AUD-04 | 无项目、无后端参数的 assured 调用仍保留旧 Python 产物投影 | 入口及源码对照 | 在完整 resolver 上做省略/auto/显式/继承/冲突差分及旧入口兼容测试 |
| AUD-05 | `scripts/README.md` 把普通正文职责交给旧 LaTeX Adapter | 当前 Authority 与导航全文对照 | 修复错指并防止同型委托回流；不复制正文规则 |

上轮的组件复现不等于整条正式交付已被绕过；本轮不得夸大安全影响。绿色历史 CI 也不替代新增反例。先冻结可复现失败，再修改实现。

## 2. 必须保持的设计不变量

1. 项目数值后端由全题模型、求解器能力、依赖/许可证和复现成本判断；不按题型名称机械映射语言，不因绘图使用 MATLAB 而偏选 MATLAB。
2. `execution.solver_backend` 是当前项目唯一选择；主求解和条件式深化统一继承。`auto` 只表示待选择；配置/回执不得反选项目政策。
3. 项目级预处理仍为 Python，正式数据图仍为 MATLAB；本问内部数学变换随已选后端。此职责分离不等于逐问混合求解。
4. 模型批准不能由代码、工作簿或迁移自动制造；普通实现/数据新鲜度变化与数学语义变化分开。
5. 任何 accepted 资格依赖的实际输入变化必须被观察；相互一致的旧状态字段不是当前磁盘事实。
6. 新检查默认只读，不刷新已交付/已验收哈希，不修改附件、工作簿或模型框架；需要状态失效的写入口仍走现有状态转移和事务。
7. 工作簿数值验收、来源身份验收、图形渲染和论文语义审查不相互替代。
8. 单一 Authority、共享解析器、共享哈希算法、共享前置核验；不在多个 consumer 各写一套宽松逻辑。
9. 新字段必须成对完整、边界明确；空值、未知模式、路径逃逸、别名、已覆盖原始源不能被静默忽略。
10. 不降低完整精度、网格、时域、重复次数或数值阈值以通过测试；合成仓库维护 fixture 不代表用户正式计算。

## 3. 实施顺序与阶段退出条件

| 阶段 | 目标 | 退出条件 |
|---|---|---|
| S0 | 固定基线、取得可信源码副本、复核上轮证据 | main/PR 已核实；源码与固定提交可对照；记录无法执行的环境项 |
| S1 | 冻结新增正负例，读完受影响调用链 | 反例可在基线重现，既有正常路径有控制组 |
| S2 | 修复 AUD-01、AUD-03 的资格漏检 | 当前输入观察与 revision 类型修复；专项回归通过，不篡改资格状态 |
| S3 | 修复 AUD-02 的辅助输入合同闭环 | 字段、source scope、receipt、共享核验、同步/打包、双后端实例一致 |
| S4 | 修复 AUD-04、AUD-05 的入口/职责衔接 | assured 中立，legacy 明确隔离，正文委托唯一；差分测试通过 |
| S5 | 全量验证、版本同步、生成文件与 PR | 完整 lint/unittest/生成检查及最终 head CI；准确报告未核验项 |

每阶段使用独立提交；它们属于同一“既有资格证明链闭环”主题。不混入 #235 的新增功能。若变更规模使某阶段无法充分验证，先保留已完成提交和精确阻塞，不能跳过测试宣称整轮完成。

## 4. 源码获取与执行环境边界

当前容器 `git clone` 因 `Could not resolve host: github.com` 失败；GitHub Connector 可以读取/写入。优先通过固定提交的仓库内容或 GitHub Actions 取得完整原始文件，再在本地运行仓库维护测试。

允许为本轮在唯一分支建立一次性、分支限定的源码快照工作流：只读 `contents` 权限，固定基线 SHA，`persist-credentials: false`，仅归档 Git 跟踪的公开仓库内容；不导出 `.git`、凭证、环境变量或用户项目。下载后核对基线与文件摘要。该临时工作流在最终 PR diff 前删除，不成为正式功能，不绕过原 CI。若不能取得快照，必须明确仅完成的组件测试，不能伪称完整 clone 或整仓本地通过。

若离线环境只能通过 Connector 提交多文件补丁，可用分支限定、基线绑定、白名单文件检查的临时维护桥接；执行内容必须是已审阅的精确补丁，不能获取任意外部代码。临时桥接及补丁文件最终删除，远程最终 diff 仅包含本计划、修复源码、合同、测试和生成物。不得将维护桥接升级为常驻写权限自动化。

## 5. AUD-01：实际输入新鲜度

### 5.1 根因与最小修复

`analysis_prerequisites.primary_issues` 已核对主源码和工作簿，但实际原始输入观察没有在公共 accepted 资格链中闭合。复用 `stage_inputs.observe_inputs`，在适用的 1.1 当前阶段检查声明输入的真实字节、路径和哈希。

初步影响面：`scripts/analysis_prerequisites.py`、`scripts/stage_inputs.py`、`scripts/runtime_assurance.py`、`scripts/validate_code_delivery.py`、`scripts/validate_user_execution.py`、`scripts/validate_project_state.py`、`scripts/project_snapshot.py`、`scripts/submission_requirements.py` 及现有 backend/analysis fixtures。不是所有文件都必须改；S1 确认直接调用关系后缩减。

### 5.2 检查规则

- 新 1.1 主结果必须同时满足当前 policy、source bundle、真实输入、工作簿及 accepted 状态。
- 原始输入改动、删除、路径别名、越界、配置输入与已验收身份冲突时，资格检查失败。
- project_level 继续核查 accepted 预处理工作簿；不得把其普通文件 SHA 改算为全局集合摘要。
- 分析阶段仍首先要求主结果 current；分析自身的真实输入和 accepted primary 绑定也需有效。
- 旧 1.0 来源只能使用其已声明的兼容范围，不以新增 1.1 要求追认或伪造历史证据。
- 不通过观察函数更新 `data_hash`、`validated_data_hash`、`bundle_sha256` 或 `validated_bundle_sha256`。

### 5.3 最低回归

A01 未变输入通过；A02 原文件改动未 sync 失败；A03 原文件删除未 sync 失败；A04 helper 变动失败；A05 结果工作簿变动失败；A06 显式 stale 失败；A07 resolver 不再提升旧结果；A08 分析交付/receipt 不能消费旧主结果；A09 Python/MATLAB 都覆盖；A10 错误检查后项目文件逐字节不变；A11 旧协议合法读取不被无关破坏；A12 实际来源与当前状态不一致时不静默回退全局数据集合。

## 6. AUD-02：预处理基础来源与辅助输入分离

### 6.1 设计裁决

不能只把 `len(files) != 1` 删除，因为当前 `data_hash` 与 accepted 预处理 XLSX 绑定，变更为混合集合摘要会破坏现有 primary/analysis 身份。采用最小、可选的辅助输入身份扩展：保留 `data_paths`/`data_sha256` 的主来源语义，为独立辅助附件单独登记路径和身份，并由当前源码 bundle 与运行回执共同绑定。

拟议字段为 `auxiliary_data_paths` 与 `auxiliary_data_sha256`。S1 必须先追完配置、receipt、源码读取检查和双后端模板；若现有接口支持更小的等价表示，先修订本节再实现，不无说明更换字段。

### 6.2 语义与资格

- 两字段仅在新 1.1、project_level、`data_identity_mode=preprocessing_workbook` 路径按需使用；没有辅助输入时完全省略，原合法实例保持可用。
- 主 `data_paths` 仍恰含当前 accepted 预处理 XLSX；主 `data_sha256` 仍为其普通 SHA。
- 辅助路径必须非空、项目相对、存在、唯一，不与主来源重叠、不为符号链接/大小写别名、不越界；不能包含 `covered_raw_sources` 已覆盖的原始数据。
- 复用现有 `artifact_fingerprint.combined_hash` 计算辅助集合摘要，不定义第二算法。
- 不能只声明哈希不声明路径，不能只声明路径不声明哈希，不能把辅助源伪装成 code_dependencies。
- 运行前绑定、输出成功回执前再次核对主与辅助输入；配置和回执中的辅助事实必须相符。
- 分析的主数据身份仍继承主结果；独立辅助输入的范围必须显式，不能借辅助通道偷偷更改本题数据口径。辅助源变化不会刷新任何 accepted 身份。
- 使用相同主工作簿但改变辅助约束，是不同计算输入，不得继续消费旧结果。
- 旧 reader 不认识已声明的新辅助扩展时不得声称完整支持；兼容说明必须明确新实例需当前工具链核验。

### 6.3 完整调用链

| 层 | 修复内容 |
|---|---|
| 全局 preprocessing Authority | 保留独立附件允许原则，指向执行合同具体身份机制 |
| User Execution Authority | 唯一字段定义、条件、校验和回执要求 |
| 配置/代码交付 | 解析完整字段对、路径边界、禁止已覆盖原源、实际读取范围 |
| Python/MATLAB 实例 | 运行前后真实输入绑定和成功 receipt，不只回显预期元数据 |
| 共享前置/runtime | 当前主/分析资格观察两类输入，不依赖曾经 sync |
| 回执验收 | 字段缺失/篡改/与源码不符及源变动时拒绝，不覆写主数据身份 |
| 同步 | 观察并失效，不能将新输入自动标为已验收 |
| 复现包 | 包含所有已声明辅助文件；遗漏应被独立 requirements 检查拒绝 |
| 历史迁移 | 归档完整源集合，不产生静默丢失；如不支持则明确阻断 |

### 6.4 最低回归

B01 单预处理 XLSX 原路径通过；B02 加合法独立约束文件通过；B03 多辅助文件排序可复算；B04 任一辅助文件改变失败；B05 删除失败；B06 半字段失败；B07 空列表失败；B08 与主输入重复失败；B09 覆盖原始源失败；B10 越界/符号链接/大小写歧义失败；B11 回执伪造辅助摘要失败；B12 分析仍绑定 accepted primary；B13 复现包遗漏辅助文件失败；B14 Python 原生合成执行；B15 MATLAB 原生合成执行；B16 无辅助字段的 1.0/1.1 历史控制组；B17 修改辅助附件不导致数学批准自动变为通过或失效，按真实数据/语义类别处理；B18 源变动后同步不得重新洗白旧运行。

## 7. AUD-03：修订号严格类型

### 7.1 修复准则

current、approved、validated revision 必须为真正的正整数；bool、浮点、字符串、零、负数、null 都不能通过。比较修订号前先验证两端类型，不能只使用 `==`。

在现有语义 helper 或一个无业务副作用的共享 helper 中定义检查，避免各入口各自实现。独立批准 CLI、semantic governance、runtime lock evidence 和状态验证使用一致的最小类型规则。Schema 已正确的约束不得删除。

候选影响文件：`scripts/validate_model_approval.py`、`scripts/validate_semantic_governance.py`、`scripts/runtime_assurance.py`、`scripts/semantic_identity.py`（共享位置优先）及必要的 `validate_project_state.py`；仅修改 revision 类字段，不把其他计数/指标顺手重构。

### 7.2 最低回归

C01 1/1 通过；C02 true/true 失败；C03 1/true 失败；C04 true/1 失败；C05 1/1.0 失败；C06 字符串失败；C07 0/负数失败；C08 修订不同失败；C09 hash 不同失败；C10 validated revision 布尔/浮点失败；C11 真实 CLI `--strict` 返回非零；C12 runtime 不提升错误 lock；C13 检查不写文件；C14 既有合法 structured 和 legacy read-only 控制。

## 8. AUD-04：新入口中立、旧入口显式兼容

### 8.1 行为目标

- `resolve_runtime.py` 作为新 assured 入口，在数值相关任务上省略 `solver_backend` 时，应与 `auto` 一样保留 unresolved/当前项目继承状态，而不是先投影 Python。
- 有当前项目选择则继承；显式相反请求报告冲突，不改状态；没有选择则在适用阶段显示 selection prerequisite。
- 不影响与数值无关的纯写作/绘图入口，不因为全局缺后端而强加无关模板或数值 gate。
- `resolve_workflow.py` 保留旧无状态产物别名行为，并在帮助和导航明确其兼容性质。
- `selection_complete`、`assurance.status`、`missing_prerequisites` 分别表示不同事实；不能把没有冲突的 plan 当作已授权数值执行。

如确需保留新函数的历史调用形状，必须使用明确兼容开关/入口，而不是继续隐藏默认 Python；不得通过修改 golden 文件掩盖未经说明的接口变化。

### 8.2 最低回归

D01 新项目省略参数中立；D02 显式 auto 同等；D03 显式 python 候选；D04 显式 matlab 候选；D05 当前 Python/MATLAB 继承；D06 反向请求冲突；D07 后问请求不能绕过全项目混用检查；D08 分析恢复实际回主求解时 stage 正确；D09 旧 `resolve_workflow` 省略参数仍兼容；D10 纯写作/图样式不增加无关数值模板；D11 所有入口文档和示例一致；D12 不自动执行 select/migrate。

## 9. AUD-05：职责委托修正

将脚本导航中“普通正文结构与表达由 LaTeX Adapter 管理”的陈旧描述改为 `paper_writing_protocol.md`；LaTeX Adapter 只负责载体；复杂数学与证据由 reasoning Authority；固定骨架由 Template Manifest。

定向检查 README、两份 Skill 入口、PROJECT_INSTRUCTIONS、RUNTIME_ROUTER、scripts README、输出合同和 Review。只修同型职责错指，不复制规则、不改论文风格、不重写历史记录。

最低回归 E01 正确 prose Authority 存在；E02 陈旧委托表述不再出现；E03 两份 Skill 入口保持一致；E04 所有引用路径存在；E05 全局版本载体与独立协议版本不混用。

## 10. 变更白名单与单一事实源

直接实现按 S1 阅读结果收敛，预计涉及以下已有文件组：

- 输入资格：analysis_prerequisites、stage_inputs、stage_code 及其现有 consumers；
- 配置和回执：validate_code_delivery、validate_user_execution、RUN_CONFIG parser、Python support/README、MATLAB q1_solver/q1_analysis；
- 语义类型：semantic_identity、validate_model_approval、validate_semantic_governance、runtime_assurance；
- 入口：resolve_runtime、必要 legacy help、Skill 两入口与导航；
- Authority：user_execution、global_preprocessing、runtime_assurance、output；没有实际字段变化不改 State Schema；
- 测试：新的 audit regression 和受影响 fixture；不删除有效断言，不改测试以容许错误；
- 版本/说明：bootstrap、plugin、manifest/router/output 的 Skill carriers、CHANGELOG、当前维护说明；
- 生成物：仅通过 `scripts/generate_indexes.py` 或仓库现有自动生成流程更新。

若超过 20 个活动文件，PR 必须按“Authority → producer → consumer → tests → carriers”解释必要性。不能为了减少文件数而遗漏 receipt、MATLAB 或 package 消费者。`MANIFEST.sha256` 绝不手改。

## 11. 测试层级与真实通过标准

1. **基线复现**：正常/失败控制组，记录真实输出；不能复制旧报告当新测试。
2. **纯函数专项**：输入路径/字节、辅助集合、revision 类型、无写副作用。
3. **真实入口集成**：resolver、代码交付、receipt、sync、package；不只 assert 文本关键词。
4. **双后端 fixture**：仓库合成问题，Python 本地可执行；MATLAB 无原生环境时由现有 native CI 核验，未运行明确记录。
5. **完整基础检查**：`python scripts/lint_skill.py`；`python -m unittest discover -s tests -p 'test_*.py'`；`python scripts/generate_indexes.py --check`。
6. **专用边界**：来源变动未 sync、无副作用、bool revision、半字段、新旧兼容、Windows 路径、无辅助输入控制、完整归档。
7. **最终远程检查**：仅最终 head 的完整 CI/索引/基线结果有效；旧 SHA 绿色不能替代。

测试文件或临时 log 不得改变 baseline 文件清单而污染索引测量；维护 log 写到 checkout 外或现有排除路径。结果报告分清本地、远程、静态、原生与未执行。

## 12. 安全、失败和禁止降级

读取/检查函数不能通过导入用户求解脚本获得数据；不得执行附件中的代码。原始路径校验应先于文件读取，辅助输入的符号链接、硬链接别名/重复、大小写冲突处理与主输入一致或更严格。出现非法字段、未知协议、非有限值或哈希冲突应给出可定位错误，不吞异常后 PASS。

更新源码而未重跑时，旧 accepted 结果必须仍旧；不把输入观察写成新验收。修复失败后不得降容差、删除反例、手写 PASS 或覆盖原始数据。模型审批存在 material blocker 时，用户的仓库修复授权也不能变成具体模型批准。

## 13. 进度台账（只填真实事实）

| 阶段 | 状态 | 提交/证据 | 未完成项 |
|---|---|---|---|
| PLAN | 已编写 | 本文首次提交 | 进入源码/fixture 核对 |
| S0 | 进行中 | main 与开放 PR 已核实；clone DNS 失败 | 取得完整快照 |
| S1 | 未开始 | — | 基线回归和字段最终裁决 |
| S2 | 未开始 | — | AUD-01 / AUD-03 |
| S3 | 未开始 | — | AUD-02 全链 |
| S4 | 未开始 | — | AUD-04 / AUD-05 |
| S5 | 未开始 | — | 全量、版本、最终 CI |

后续每次接管必须先从当前 main 读取 bootstrap、治理、本计划和当前 PR 实际 diff；确认 head 与阶段，再继续。不能从旧聊天“已修复”摘要直接打勾。

## 14. 完成清单

- [ ] AUD-01：未同步的原始/辅助输入漂移被公共前提拒绝，资格与同步一致。
- [ ] AUD-02：合法独立辅助附件有完整身份，回执/双后端/复现包闭环。
- [ ] AUD-03：所有修订号入口拒绝 bool/float/string，不产生误 PASS。
- [ ] AUD-04：新 assured 入口后端中立，当前项目统一继承，旧兼容明示。
- [ ] AUD-05：正文/模板/Adapter 权限委托无错指。
- [ ] 新旧协议控制组与模型批准/数值验收/stale/只读边界保持。
- [ ] 完整测试与最终 head CI 已核实；未核验项准确说明。
- [ ] 自动索引/MANIFEST 正确；临时快照/桥接文件不在最终 diff。
- [ ] PR 明确是否合并；没有发布或移动未经授权的 tag/Release。

## 15. 固定基线源索引

以下路径均对应 `0fc52fa47abf457ef4e180ac7a291583cd9be68f`，实施时补读全文及调用者：

- [执行合同](https://github.com/Vexushi1/mathmodel-skill/blob/0fc52fa47abf457ef4e180ac7a291583cd9be68f/core/user_execution_contract.yaml)
- [预处理合同](https://github.com/Vexushi1/mathmodel-skill/blob/0fc52fa47abf457ef4e180ac7a291583cd9be68f/core/global_preprocessing_contract.yaml)
- [输入观察器](https://github.com/Vexushi1/mathmodel-skill/blob/0fc52fa47abf457ef4e180ac7a291583cd9be68f/scripts/stage_inputs.py)
- [公共分析前提](https://github.com/Vexushi1/mathmodel-skill/blob/0fc52fa47abf457ef4e180ac7a291583cd9be68f/scripts/analysis_prerequisites.py)
- [实现与 bundle](https://github.com/Vexushi1/mathmodel-skill/blob/0fc52fa47abf457ef4e180ac7a291583cd9be68f/scripts/stage_code.py)
- [模型审批核验](https://github.com/Vexushi1/mathmodel-skill/blob/0fc52fa47abf457ef4e180ac7a291583cd9be68f/scripts/validate_model_approval.py)
- [运行时恢复](https://github.com/Vexushi1/mathmodel-skill/blob/0fc52fa47abf457ef4e180ac7a291583cd9be68f/scripts/runtime_assurance.py)
- [默认 resolver](https://github.com/Vexushi1/mathmodel-skill/blob/0fc52fa47abf457ef4e180ac7a291583cd9be68f/scripts/resolve_runtime.py)
- [兼容 resolver](https://github.com/Vexushi1/mathmodel-skill/blob/0fc52fa47abf457ef4e180ac7a291583cd9be68f/scripts/resolve_workflow.py)
- [脚本导航](https://github.com/Vexushi1/mathmodel-skill/blob/0fc52fa47abf457ef4e180ac7a291583cd9be68f/scripts/README.md)

外部审计报告只提供问题线索。修复完成与否必须由本轮实际代码差异、复现、回归和 CI 决定。
