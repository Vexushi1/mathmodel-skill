# v10.18.2 默认论文路由与当前提交包证据闭合修改计划

本计划依据 2026-10-07 实时读取的 `main` 制定。用户已授权先形成详细计划，再依计划实施。本文件是维护记录，不是新增 Runtime Authority；执行规则仍由下列权威文件定义。计划先于实现提交，实施结果另行记录，任何尚未执行的测试均不得标为通过。

## 1. 修改简报

| 项目 | 内容 |
|---|---|
| 修改主题 | 默认论文路由与当前提交包证据闭合 |
| 仓库 | `Vexushi1/mathmodel-skill` |
| 基线 | `main@e8d7a24374974fcaa17e6e5c51a23cc06c40b9f0` |
| 当前版本 / 目标版本 | `10.18.1` / `10.18.2` |
| 变更等级 | patch；修复既有契约的实现偏差，不引入破坏性接口 |
| 分支 | `fix/v10.18.2-routing-submission-closure` |
| 开始前 PR 状态 | 实时查询未发现未合并 PR，未发现重叠修改 |
| 直接目标 | 修正普通论文草稿的默认载体；按当前分析状态选择复现产物；补齐提交校验实际读集；统一附录提示与证明正文规范 |
| 明确不做 | A2 比较模型新增支持、MATLAB package/private 解析、DOCX 最终提交证明、案例效果宣称、竞赛规则臆测、用户项目迁移、数值模型重写 |
| 兼容要求 | 保持现有 CLI、项目布局、Excel 命名/列契约、语义身份、审批和用户执行边界；显式 Word/DOCX 请求继续可用 |
| 迁移要求 | 不要求用户项目迁移；重建提交包即可使用修复后的选择与校验 |
| 验收 | GitHub 受影响专项回归、最终 head 完整 Python 矩阵、lint、生成契约、原生 MATLAB、LaTeX、适用 Optimization 检查 |
| 回滚 | 合并前修正或关闭 PR；未来合并后通过独立 revert PR 恢复源文件及远端重新生成的受管文件，不直接写 main |

### 1.1 预计修改范围

- 路由 Authority：`core/workflow_router.yaml`；只有现有规则无法表达正确选择时才调整 `scripts/runtime_assurance.py`。
- 复现包收集器：`scripts/hsk_pack_submission.py`。
- 提交共同要求：`scripts/submission_requirements.py`，承载收集与验证共用的当前分析产物判定，避免两套规则。
- 提交包校验器：`scripts/validate_submission_package.py`。
- 附录提示：`templates/latex/cumcm/hsk/appendices/appendices.tex`。
- 回归测试：现有路由、运行保障、提交包完整性与读集测试，必要时新增紧凑专项模块。
- 开发专项 CI：只有现有 targeted 列表遗漏受影响测试时，补充 `.github/workflows/ci.yml` 中的模块列表，不改变 full/discovery/shard 规则。
- 版本载体、`CHANGELOG.md`、本计划及实施记录；严格按现有版本矩阵更新。
- 分支保护状态记录：既有历史指针仅纠正当前可确认的事实，保留 Issue #92 导航。

### 1.2 禁止触碰范围

- 不改 `core/workbook_schema.yaml` 的工作簿结构、列名、单位和 accepted-workbook 契约。
- 不改用户项目、历史结果、原始附件、实际论文和现有运行凭证。
- 不降低 Model Challenge、Human Approval、语义一致性、B2/C2 或数值验收门槛。
- 不自动开启结果深化分析，不删除磁盘上的旧分析文件。
- 不运行真实用户问题的求解/分析代码，不缩小数据或数值精度生成替代证据。
- 不手工编辑 `MANIFEST.sha256`、四类受管索引、case-memory 生成索引。
- 不批量替换历史版本号；独立协议版本和历史维护记录保留原版本。
- 不改 Release/tag，也不把 PR 完成等同于发布或本机升级。

## 2. 权威与消费者追踪

| 修复 | 权威来源 | 必查消费者 | 不应新增的第二套定义 |
|---|---|---|---|
| 论文载体推断 | `core/output_contract.yaml#paper_mode`、`core/hsk_core_policy.md`、`modules/05_writing/docx.md` | router、runtime assurance、resolve_runtime、legacy resolver、writing runtime、路由测试 | 独立的默认载体配置或重复意图算法 |
| 当前复现产物 | `packs/artifact/full_submission.md`、`core/output_contract.yaml#per_question`、当前项目 Analysis Necessity 状态 | collector、submission_requirements、validator、各 backend 的分析入口与 workbook | 仅收集器识别的隐藏黑名单或仅验证器识别的另一套规则 |
| 读集闭合 | `SKILL_CHANGE_GOVERNANCE.md`、现有 project_transaction 读集契约、claim consumption | validator、safe_yaml、B2/C2 上游读集、compile dependencies、competition profiles | PASS 缓存、解析缓存作为原始字节身份、覆盖旧观察以掩盖变化 |
| 正文/附录分工 | `modules/05_writing/paper_writing_protocol.md`、`core/writing_reasoning_contract.yaml`、命题 Pack | cumcm appendix 模板、模板说明、写作运行 gate | 按长度/难度迁走核心证明的新规则 |

实施前确认每个文件的实际函数和现有测试，不凭历史聊天推断代码。已在 v10.18.1 修复的动态导入闭包、数值证据重算等问题不重复改动。

## 3. 修复 R1：普通论文草稿回到默认 LaTeX 路径

### 3.1 当前事实与触发条件

`docx.infer_keywords` 包含“草稿论文”“论文草稿”。推断器按关键词命中选择意图，因此请求“请写论文草稿”会选择 `docx`，返回 DOCX 交付范围和 `docx_draft`，并遗漏 LaTeX 写作运行序列。这个行为与默认 LaTeX、DOCX explicit-only 的 Authority 冲突。

本问题已经通过 resolver 动态探测确认；探测没有运行数值代码。不能只删除关键词后让请求变成无意图，必须验证默认论文路由实际可达。

### 3.2 实现步骤

1. 从 DOCX 路由的 triggers/infer_keywords 移除不包含载体信息的通用草稿词。
2. 将通用论文草稿语义纳入既有 LaTeX 路由，不新增独立“草稿载体”意图。
3. 保留明确 DOCX/Word 关键词和显式 `docx` intent 的优先级。
4. 检查混合请求“Word 论文草稿”“DOCX 草稿论文”是否因关键词累计长度而错误选择 LaTeX。
5. 若需增强特异性，优先使用路由中已有、可审计的明确载体短语；只有契约表达确实不足时才更改推断器，并说明影响面。
6. 检查显式 LaTeX 请求和已有多意图/歧义行为，不靠模糊关键词获得模型审批或代码执行授权。
7. 检查 assured resolver 和 legacy stateless resolver 的加载结果、terminal outputs、delivery scope、writing runtime 与 gates。

### 3.3 关键回归用例

| 请求/调用 | 期望 |
|---|---|
| 请写论文草稿 | LaTeX 写作路径，载入 writing runtime |
| 请写草稿论文 | 同上 |
| 用 LaTeX 写论文草稿 | LaTeX，不混入 DOCX 分支 |
| 请写 Word 论文草稿 | DOCX review 分支 |
| 输出 DOCX 草稿论文 | DOCX review 分支 |
| 显式 intent=docx，描述为论文草稿 | 尊重显式选择 |
| 显式 intent=latex，描述含草稿 | 尊重显式选择 |
| 与论文无关的“草稿”或代码注释 | 不扩大为论文正式交付 |
| 现有 full_workflow/review/算法展示请求 | 保持原有加载与安全边界 |

不以仅检查 YAML 字面量代替 resolver 行为验证。不宣称任意自然语言都可无歧义推断。

## 4. 修复 R2：复现包遵守当前分析启用状态

### 4.1 当前事实与风险

`reproducibility_files()` 遍历项目根下全部文件，主要仅排除缓存与 submission 目录。当前状态为 `not_required` 时，磁盘上残留的旧分析脚本/工作簿仍可能入包。当前 validator 只要求必需文件齐全，对这类额外文件没有当前状态检查。

已动态确认 collector 会选择残留文件；尚未把这个单独探测描述为完整提交包验收。修复必须补全真实 ZIP + manifest + validator 场景。

### 4.2 设计原则

- 保留复现所需附件、主求解代码、合法 helper、模型框架、LaTeX 源码/图表与被当前 compile report 绑定的日志和 recorder。
- 当前有效状态决定当前 03B 产物是否属于交付；目录中“存在”不等于“已启用/已接受”。
- 识别应使用当前状态登记路径、当前输出契约的 Python/MATLAB 命名与专用兼容入口，不做“文件名含分析就排除”的宽泛匹配。
- 路径必须经项目根边界校验与规范化；不得通过 `..`、绝对越界、符号链接或大小写别名绕过。
- 不删除原文件；只控制 ZIP 选入及验证结果。
- 对缺少现代项目状态的旧备份调用保留明确兼容边界；不得把旧 broad backup 宣称为已通过现代完整交付 gate。

### 4.3 实现步骤

1. 追踪当前分析状态、登记路径、stage execution record 与输出模板之间的关系。
2. 在 submission_requirements 中建立可复用的当前分析产物选择/拒绝判定，返回规范化相对路径和诊断。
3. collector 调用同一判定，排除当前明确未启用的 03B 产物，保留被当前合法产物依赖的 helper/输入。
4. 对 `required`、accepted 和 pending 等状态分别保留现有语义：pending 可供诊断/备份，但不能获得最终“完整可复现”资格。
5. validator 对现代 reproducibility ZIP 中显式不属于当前交付的 03B 文件给出失败诊断，阻止手工构造 ZIP 绕过 collector。
6. 检查 active backend 与 historical backend 入口的边界，不能因迁移残留而把旧入口误当当前分析已验收。
7. 更新 collector docstring，清楚区分兼容备份与当前状态提交语义。
8. CLI 参数、默认输出路径、manifest 结构和 SHA 校验接口保持兼容。

### 4.4 测试矩阵

| 场景 | 检查点 |
|---|---|
| not_required + 原目录残留 Python 分析脚本和 workbook | collector 排除；源文件仍存在；正常包通过 |
| not_required + MATLAB 分析入口残留 | 同样排除，不影响 qN_solver.m |
| 手工向 ZIP 加入不启用的分析文件并更新 manifest | validator 明确拒绝，不能仅凭 manifest/hash 一致通过 |
| required + 当前 accepted analysis | 当前代码/workbook 入包，遗漏任一必需文件被拒绝 |
| 多问题：Q1 required、Q2 not_required | 按问题分别判定，不全局关闭分析 |
| 根目录与嵌套附件中的普通文件 | 合法原始输入保留；名字偶然相似不被无依据丢弃 |
| 当前 source helper / backend bundle / provenance | 必需依赖不丢失，历史路径不冒充当前身份 |
| 当前 compile report 绑定 .log/.fls | 保留既有例外和编译证据闭合 |
| pending、无理由 not_required、缺少问题状态 | 继续 fail closed，不把收集成功等同验收成功 |
| legacy 无当前状态 | 保持专用兼容备份边界；现代验证仍按既有要求拒绝不完整状态 |
| 非法/别名路径 | 明确失败或拒绝越界，不静默丢失安全诊断 |

不要求每个矩阵格单独建立冗余测试；合并相邻用例，但覆盖每项不同失败模式。

## 5. 修复 R3：提交校验完整观察实际读取的字节

### 5.1 当前事实与风险

validator 的 finish 已重检 ZIP、项目读集、Skill 读集，并绑定项目状态。但归档成员对应当前文件和 current PDF 的观察仅在 B2 gate 为 passed 时记录；B2 默认未启用的路径存在检查期间变化而未在 finish 捕获的静态缺口。official 分支还读取 competition profiles，却没有把对应原始字节身份加入 Skill 读集。

这一项当前依据代码追踪确认。必须使用受控 hook/mocking 在读取后、finish 前改变文件，形成实际回归证据，不能把静态分析称为已复现竞态。

### 5.2 实现设计

1. 读集记录与 B2 功能启用解耦：基础包校验读取了什么，就观察什么。
2. 复用 project_transaction 的最终 `_check_read_set`，不另造第二套 race 检查框架。
3. 对当前 archived member、current PDF、competition profiles 和实际 consumed requirements/compile 输入，在首次语义消费前后合理位置绑定原始字节。
4. 对需要解析的 YAML，尽可能一次读取原始字节、哈希、严格解析同一批字节，防止 hash 与解析对象来自不同版本。
5. 合并来自 B2/C2 的 observed_sources 时保留首次观察；同一路径再次见到不同 SHA 应报告变化，不得覆盖后继续通过。
6. 记录路径应相对各自 root、规范化并限制边界；绝对/相对别名归并，避免同一文件多个键掩盖冲突。
7. required-file helper 若读取额外文件，允许接收观察回调或返回 consumed sources；优先最小接口，不为本次修复引入一般化事务抽象。
8. 保留现有 ZIP 本体重检、project state 起始身份、compile 文件绑定、lock/journal 和 C2 上游依赖检查。
9. 不观察与本次验证无关的整个项目或整个 Skill；避免无关文件变化导致误拒绝。
10. 不缓存 gate PASS、项目资格或读集验证结论；safe_yaml 缓存只能用于严格解析且返回独立对象。

### 5.3 动态回归场景

| 初始资格 | 在 finish 前改变 | 期望 |
|---|---|---|
| B2 未启用，reproducibility 合法包 | 已校验的当前归档成员 | 失败并指明文件变化 |
| B2 未启用，合法包 | 已校验的 current PDF | 失败 |
| official，明确 verified profile | 本次读取的 competition profile 原始字节 | 失败 |
| 任一路径 | ZIP 字节或 project_state.yaml | 继续失败，保留既有保护 |
| B2/C2 已启用 | 已观察源发生冲突 | 保留失败语义 |
| 稳定输入 | 无变化 | 通过，返回既有结构 |
| 稳定相关输入 | 无关说明文件变化 | 不无故失败 |
| 错误状态/坏 YAML/缺失文件 | 读取异常 | 返回可理解失败，不抛出未处理异常冒充成功 |

测试只使用临时项目及 fixture，不改真实竞争配置、不触碰用户数据。修复后重新审查每个返回路径，确保成功出口执行 finish。

## 6. 修复 R4：附录提示按数学作用表述

### 6.1 修改

只改 cumcm appendix 模板中“技术证明超过正文安全长度时放在此处”的提示。替换为核心命题、关键推导及直接支撑模型结论的证明保留正文；附录仅放非核心补充证明、辅助材料和正文不宜展开但仍有证据价值的图表，并引用现有 protocol。

### 6.2 验证

- 对照协议中的正文保留、证明作用和 appendix 允许内容，不新增长度阈值。
- 检查 main 默认 appendices 开关、标签、环境、模板 assembly 均保持原样。
- 由既有 LaTeX compile/Production CI 验证模板仍能编译。
- 不为一句注释创建只镜像文本的孤立测试；如现有语义一致性测试已有适当契约范围，最小更新即可。

## 7. 平台事项：主分支保护

### 7.1 已确认与限制

此前只读结果显示 main 未受保护、rulesets 为空。本轮 repository metadata 返回 admin/maintain/push 为 true，不能沿用历史文件中“当前账号权限不足”的解释。当前 GitHub 插件只提供 protection/ruleset GET，没有对应写入工具；仓库权限与工具能力必须区分。

因此本次可以完成只读核验、准备设置清单和纠正历史状态记录，不能声称已启用平台保护。代码修复和 PR 验证照常推进，不通过 Skill 代码模拟 protection。

### 7.2 有设置写入通道时的配置与验收

1. 只针对 main 创建/更新一套有效 ruleset 或 branch protection，先导出旧设置便于恢复。
2. 要求通过 PR；禁止 force push 和删除 main；审查管理员/应用 bypass 范围。
3. 以本次实际 full CI checks 的准确名称确认 required checks，包含完整 Python 汇总、lint、generated，以及按平台支持设置必需专项。
4. 不把 targeted、skipped 或旧 SHA green 设为完成依据。
5. 审查 approvals/CODEOWNERS 与当前单维护者工作方式，避免机械开启无人能满足的自审要求。
6. 设置后用 API read-back 确认 enforcement=active、target/include/ref、required checks 与 bypass actors。
7. 测试不能绕过 main 的规定入口；不以故意推送危险提交验证。
8. 若未实际写入，实施记录列为“工具能力受限，未启用”，附 Issue #92 和精确设置入口。

## 8. 版本与生成闭合

1. 只更新当前发布矩阵要求的 Skill 载体：bootstrap、plugin、router、module manifest、output、writing runtime、prose audit patterns、根/嵌套 SKILL、README 标题、policy 标题与版本回归断言。
2. Changelog 顶部新增 10.18.2，陈述实际修复及兼容边界，不声称 Release 已发布。
3. 不更改 schema/protocol 的独立版本，因为本次没有对应数据结构破坏性变更。
4. 提交源文件推送后，等待 `refresh-generated` 自动更新受管索引和 manifest。
5. 获取 bot commit，检查只改允许的生成文件，记录最终 head。
6. generator 无变化也必须记录实际 final head，不假定没有变化。
7. 所有正式证据绑定最终 head；source head、PR source SHA、merge checkout SHA 分别记录。

## 9. 实施顺序与分工

### 阶段 P0：计划冻结

- 核对 live main、版本、PR、Authority、治理规范，建立独立分支。
- 先提交本计划，并向用户提供输出副本。
- 明确四项修复的已复现/静态风险边界及平台工具限制。

### 阶段 P1：独立实现

- 路由/写作任务：R1、R4 及相关 resolver 行为测试。
- 包选择任务：R2；负责 hsk_pack_submission、submission_requirements 的选择部分及 package completeness 测试。
- 读集任务：R3；负责 validator 和 read-set 专项测试，与包选择任务协调共用接口，避免并发覆盖。
- 主维护任务：版本载体、Changelog、CI 专项列表、平台事实记录与最终集成审查。
- 同一文件多人修改前先划定归属；依赖接口通过明确消息协调，不抢写。

### 阶段 P2：集成审查

- 查看逐项 diff；核对 helper/import/path/return/error 行为。
- 检查 R2 选择与 validator 的规则一致，R3 没有依赖 B2 才观察文件。
- 对照测试矩阵审查缺口；必要的漏洞修复仍属于既定主题，扩展能力则另列后续。
- 检查版本载体和历史版本未误改，generated 文件未手工改。
- 提交源文件、推送、创建 draft PR，PR 描述包含简报和计划链接。

### 阶段 P3：远端开发验证

- 等待 refresh-generated，回读 bot head 并 fetch 本地。
- GitHub targeted 运行必须覆盖新回归，检查实际测试数和结果。
- 如失败，读取具体日志定位原因，最小修复并重走 generated/head 验证。
- 每次新增源码提交失效旧 head 证据；不得复用旧绿灯。

### 阶段 P4：最终 head 正式验收

- 在代码冻结后将 PR 设为 ready，使 full 路径执行。
- Windows Python 3.10/3.14 各四 shard；两个 preserved 汇总 checks 校验 commit、version、标准 discovery IDs 与全部结果。
- 检查 Static contract lint、Generated files、Windows MATLAB native、Linux LaTeX/Production 和适用 Optimization 的实际 conclusion。
- 区分 success、skipped、cancelled、action_required；不能把总体绿色代替逐项必要 gate。
- 下载/读取必要证据以核验当前版本、checkout commit 与正式执行范围。
- 如任何 head 改变，重新验收该最终 head；PR 描述更新为最终实现而非过程堆砌。

### 阶段 P5：交付

- 用户获得详细计划、实际变更清单、PR 链接、最终 head 和 CI 证据。
- 未请求发布，保持现有 Release/tag；不宣称 v10.18.2 已正式发布。
- 未执行 merge 时，明确 PR 已验证/待合并，不写“main 已修复”。
- 平台保护未启用必须单独记录；不让它掩盖已完成的代码修复。

## 10. 完成判据

以下条件全部满足，才能称“本次代码修复已完成并通过正式 PR 验证”：

- R1 通用草稿实际走默认 LaTeX，明确 Word/DOCX 和显式 intent 保留。
- R2 collector 与 validator 共用当前状态判定；正反 ZIP 场景验证；旧文件未删除，复现依赖未丢失。
- R3 默认 B2-off 和 applicable official 分支捕获相关输入变化，稳定输入保持通过，原有 guards 保留。
- R4 附录提示与现有数学作用规范一致，模板仍通过正式编译。
- 版本、source、索引、manifest 在最终 head 闭合；新回归进入正式 discovery。
- GitHub 所有必需 full gates 在最终 head 成功，或对确实不适用的 gate 提供具体契约依据。
- PR、计划、实施记录与实际结果一致，无夸大动态覆盖、平台设置、合并或发布状态。

## 11. 风险与最小回滚

| 风险 | 防护 | 回滚粒度 |
|---|---|---|
| 新草稿关键词压过明确 Word/DOCX | resolver 混合短语测试，显式载体优先 | R1 路由/测试独立提交 |
| 排除规则误伤原始附件/helper | 路径及阶段契约约束，附件/依赖正例 | R2 collector/共享选择/验证协同 revert |
| 读集过宽导致误拒绝或过窄漏 race | consumed-source 原则、无关变化正例、受控变化反例 | R3 validator 与接口一起 revert |
| 同路径不同 SHA 被覆盖 | 首次观察固定、冲突失败、别名规范化 | 保留现有事务检查，局部修正 observation 合并 |
| 版本/生成不一致 | version matrix + remote generator + final head read-back | 恢复 source 载体并远端重新生成 |
| CI 尚未完成却交付为成功 | exact-head 记录及必要 gates 逐项确认 | 保持 PR 未合并，不发布 |
| 主分支保护错误归因 | 当前权限与工具能力分开记录 | 仅纠正状态说明，无平台写入时无设置回滚 |

后续能力应独立提案：比较模型 conformance 的数学/代码身份扩展、MATLAB package/private 闭包、DOCX 终稿证明、真实案例效果评估。每项先定义支持范围、独立审批与目标环境证据，不混入本次 patch。
