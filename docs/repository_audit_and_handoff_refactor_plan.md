# 全仓库 Skill 审查与衔接修复详细计划

> 状态：18 项审计问题已落实修复和回归，4 项观察已形成有边界的裁决。A1–A7 已通过各自 PR 检查并合入 main；A8 本地收口验证已完成，其远端发布结果通过下列检查链接追溯。本文是维护计划和实施记录，不是新的 Runtime Authority；未执行事项不计为通过。

| 项目 | 本轮记录 |
|---|---|
| 审查日期 | 2026-09-20 |
| 仓库 | Vexushi1/mathmodel-skill |
| 原审查基线 | main，Skill 9.5.2，提交 `f6f64887bd5e4ca8ec00fbd10c33308aa3ade660` |
| 本计划版本 | 1.1（实施与收口记录） |
| 本次变更等级 | docs / tests closeout；最终 Skill 9.6.1；A6 的编译报告升级按 minor 发布 |
| 本次交付 | 18 项修复的实现/回归/迁移索引、4 项观察裁决及发布验证记录 |
| 优先顺序 | 状态写入与错误验收 → 结果/路由/同步衔接 → 编译与提交完整性 → 模板与入口一致性 |
| 审查结论 | 18 项确认问题（含静态格式/指针不一致），4 项观察（裁决见第 8 节）；未证明用户数据已损坏或真实赛事漏交 |

## 1. 目标、范围与保留边界

本轮从绘图扩展至仓库内全部活动能力：入口与能力发现、审题、模型设计与审批、数据处理、主求解、结果分析、绘图与机理图、论文与证明/算法、LaTeX/DOCX、状态同步、终审、提交和维护工具。重点检查同一事实在 Authority、模板、实现、状态与下游 consumer 之间是否一致，而不只检查文件存在或规则文本包含某个词。

继续保留用户已经确认的工作方式：

- 题目专属数值代码由用户本地运行；本次只运行仓库检查器及合成测试夹具，不复算用户模型、敏感性或数值结果。
- 当前任务不运行 MATLAB，不自动看图、打分或迭代图像。MATLAB 代码静态检查与用户本地运行、人工调图分别记录。
- 图表按证据和版面选择；SCI/Nature 可以作为逐图配色参考，没有统一默认配色，不强迫复合图、多面板或装饰性升级。
- accepted 工作簿仍是具体数值事实源；框架是语义导航，state 是状态事实源。修复验证器不得通过改数值、伪造 receipt、补写 passed 或放宽模型精度实现。
- 普通正文 Authority 仍为 `modules/05_writing/paper_writing_protocol.md`；不新增平行写作规范或第二套 gate 清单。
- 本轮不改既有用户项目、历史结果、论文或旧图，不删除历史证据，不批量迁移旧状态。

此前的[绘图技巧与衔接计划](figure_technique_and_handoff_refactor_plan.md)保留其已完成记录。本计划处理此次新发现的跨阶段问题；例如图文件哈希发现遗漏属于状态/证据绑定问题，不重新开启自动图像检查或更换绘图风格。

## 2. 审查方式与覆盖

### 2.1 方法

1. 核对远端 main、当前版本、未合并 PR、Bootstrap 和修改治理规范。
2. 沿 producer → artifact/schema → state → consumer → gate 阅读活动合同和实现，复核相关模板、Pack 与回归测试。
3. 运行现有 lint、生成文件检查、完整 Python 单测及有针对性的反例探针；探针使用临时合成项目和工作簿。
4. 对 LaTeX 来源绑定与局部编译问题，额外真实编译两个小型合成工程，并提取 PDF 文本确认实际输入/输出；这不是用户论文编译或图像 QA。
5. 将已复现缺陷、静态确认的格式/合同差异、未验证集成边界分开记录。已有测试通过只说明已有案例通过，不否定新反例。

### 2.2 覆盖清单

以下数量是审查基线的目录清单，排除运行产生的缓存；覆盖并不表示穷举了全部状态组合或证明每条文字规则正确。

| 范围 | 数量/入口 | 本轮检查重点 |
|---|---|---|
| Skill/插件入口 | 两份 SKILL.md、plugin.json、agents/openai.yaml | 宿主发现字段、根入口一致性、启动与路径委托 |
| core | 18 个文件 | Bootstrap、路由、分类、审批、状态、执行、数值、工作簿、写作及交付合同 |
| modules | 14 个文件 | 从审题到交付的输入输出、暂停条件与跨阶段一致性 |
| task Packs | 12 个 | 分类与模型/结构匹配、capability 激活、复杂度与比较边界 |
| artifact Packs | 8 个 | 代码、图、算法、证明、LaTeX、DOCX、review、submission |
| competition Packs | 5 个 | 通用与各竞赛稳定规则/当届规则分离、模板和载体边界 |
| scripts | 38 个 | 路由、校验、状态事务、同步、图源、编译证明及打包 |
| templates | 79 个文件 | Python/workbook、MATLAB、绘图/机理、模型框架、写作、LaTeX、终审 |
| config / state | 3 / 1 个文件 | 竞赛 profile、状态示例与实际 consumer |
| tests / CI | 144 个文件及 3 个 workflow | 现有行为覆盖、Windows 盲区、负例与真实编译证据 |

绘图和 MATLAB 延续上一阶段完整静态审查，本轮重点复核它们与结果资格、状态、写作和打包的交接。历史 release 说明与 legacy 归档只作来源追踪，不把历史规则误报为当前默认。外部安装的所有 Codex 插件不在此次仓库审查范围内。

### 2.3 已执行的基线验证

| 验证 | 实际结果 | 可以/不可以推出的结论 |
|---|---|---|
| `python scripts/lint_skill.py` | 通过 | 当前仓库 lint 未发现违规；不能证明宿主格式或业务反例正确 |
| `python scripts/generate_indexes.py --check` | 通过 | 审查前生成文件与源码一致 |
| `python -m unittest discover -s tests` | 1088 项，2 failures + 38 errors | 本机 Windows / Python 3.14.5 未全绿；与上一阶段相同的 40 个失败用例 ID，无新增基线失败 |
| 全路由资源 smoke | 21 条 route × 4 个 competition profile，共 84 组均解析成功、资源存在 | 固定 optimization/not_needed 输入下的加载闭合；不代表生命周期门均正确 |
| 定向反例 | 见第 3 节 | 多处问题在现有正常用例通过时仍可复现 |
| 两个合成 LaTeX 工程 | 正式编译入口返回 0，报告 passed；PDF 文本核对完成 | 证明两个编译边界缺口；不是所有模板或用户论文的完整运行验收 |

对 Windows 失败重新定性：`project_transaction.py` 的备份 fsync 已复现真实写入故障；工作簿读取后句柄未释放也有真实文件重命名失败证据。不能继续把全部 40 项统称为环境问题。符号链接测试的 WinError 1314 则属于当前账户缺少创建符号链接权限，应独立处理，不能据此删除路径边界检查。

加入本计划并生成元数据后，再次执行完整 1088 项单测，仍为 2 failures + 38 errors，失败用例 ID 与本轮审查基线完全一致；未新增失败，但不能称本机全量测试通过。文档 lint、生成文件检查与 diff 检查通过。GitHub PR CI 的结果另以该 PR 当前 head 的实际记录为准。

## 3. 问题台账与最小修改方案

优先级是本项目的修复排期：P0 优先恢复可写状态并阻止错误验收；P1 修复正式交付/证据完整性和主要兼容问题；P2 修复误报和发现/诊断一致性。每项都必须先加入能失败的行为案例，再实现最小修复。不要通过删断言、放宽 strict 或改写测试预期掩盖问题。

### AUD-01 · P0 · Windows 已有状态的事务更新失败

- **证据：已复现。** `scripts/project_transaction.py:351–359` 复制备份后以 `rb` 打开并 fsync。本机对已有 state 执行 `commit_project_state` 得到 `OSError(9, 'Bad file descriptor')`；原文件未变，但留下 `.stage/.bak`，尚未生成 journal。同目录 `atomic_write_text` 对照成功。
- **影响：** 同步、模型审批和回执验收等事务 writer 可能无法更新已有项目；异常发生在 journal 前，残留文件也不属于正常可恢复提交。
- **最小修改：** 在现有 transaction Authority 内采用 Windows/Linux 均合法的持久化备份方式；为 staging 准备阶段增加确定性清理；保持 generation conflict、进程锁、journal 恢复及现有各目标提交顺序（包括允许 state 之后写入的报告），不借此重排事务。
- **验收：** 新建/更新已有 state、多个目标、备份阶段故障、journal 前/后中断、恢复、并发旧 generation 均有正反例；Windows 与 Linux 实际文件系统测试通过，无不可解释残留。不能通过忽略全部 fsync 异常实现。
- **兼容：** 原 state 字段与 generation 含义保持；旧残留只在证据明确时清理，不遍历删除用户文件。

### AUD-02 · P0 · 布尔数值证据可被普通比较关系错误放行

- **证据：已复现。** 底层收敛/泄漏证据为 `False`，质量行设置实际值 0、阈值 1、关系 `<=`、是否通过 True，严格 numerical validator 仍返回 `passed=True, issues=[]`。独立复算得到 False 与 0 相等，未强制消费合同中 `quality_relation=bool_true`。
- **定位：** `scripts/validate_numerical_evidence.py:301–364`；合同 `core/numerical_verification_contract.yaml:179–188`。
- **影响：** 工作簿写出的通过标记和任意比较关系可能把未收敛或泄漏检查失败变成合格主结果。
- **最小修改：** `scripts/validate_numerical_evidence.py` 按 `core/numerical_verification_contract.yaml` 中每个 verification 的归约类型与关系约束独立裁决；布尔型必须满足布尔真值，不允许借用数值宽松阈值绕过。复用现有 Verification ID，不新增平行质量规则。
- **验收：** 对当前 active 且参与主判定的布尔证据，False、0、空、非法类型、伪造关系、伪造通过列均拒绝；真实 True 的规范记录通过；收敛过程里 `用于主判定=False` 的中间失败行保留为合法正例，不能一律拒绝全部历史迭代；残差类的合法数值比较不受影响。检查验收链不会在 numerical gate 失败后写 accepted。
- **迁移：** 不宣布历史 accepted 全部失效；按相关 capability 与 verification 模式识别受影响记录，在再次正式使用前针对性复核，记录“待复核”而不猜测重算结果。

### AUD-03 · P0 · 03B 回执可以越过主结果与必要性门

- **证据：已复现。** 主执行与分析均为 pending 时，一个字段/哈希/receipt 有效的 analysis 工作簿经 `validate_user_execution.py --strict` 返回 0 和 passed；直接调用写模式会把内存状态推进 `analysis_execution_status=accepted`、`status=analyzed`。已有 not_required 理由时也会被相同验收覆盖。Windows 事务故障阻止了正式落盘，本轮没有声称 CLI 成功写入磁盘。
- **下游证据：** 把该探针内存结果保存到临时夹具后，`hydrate_project_context` 生成 `validated_results`，但不存在 verified accepted primary。`scripts/runtime_assurance.py:516–525` 的分析完成聚合没有同时要求主结果 verified。
- **定位与协议：** `scripts/validate_user_execution.py:357–400,475–491,547–550`；探针采用当前 RUN_CONFIG 与版本 1.0.0 的 RUN_RECEIPT，并非仅旧兼容路径。
- **最小修改：** 在既有 user-execution validator 的读、写、CLI 路径共用业务前置条件：主结果仍 current/accepted，Analysis Necessity Gate 已明确 required，project_level 前置证据适用且 current。`validated_results` 按“accepted primary AND（accepted analysis OR 合法 not_required）”逐问求值。
- **状态实现边界：** 这里 required 是现有必要性决策语义，不是当前 `result_analysis_status` 枚举值；该字段目前只有 pending/passed/failed/redo_required/not_required。实施时先用既有框架、state 和代码交付证据定义“未裁决/已激活”的可验证映射，不把 pending 自动当 required，也不默认新增必填字段。确需 schema 扩展时另作最小版本/兼容评估。
- **验收：** pending/rejected/stale primary、未裁决 Gate、not_required、缺主工作簿、哈希不符、预处理失效均不能接受 analysis；合法 required 链可通过。读写路径判定一致，失败不覆盖原 Gate 理由或 accepted 证据。
- **兼容：** not_required 不是 passed；真正重新开启分析先显式更新必要性决定及理由，再接受新分析回执。

### AUD-04 · P1 · 合法 not_required 分支仍被旧状态必填项阻断

- **证据：已复现。** `result_analysis_status=not_required` 且理由完整的 validated 项目仍被状态检查要求 analysis workbook、analysis_methods、分析哈希和 result_analysis_status=passed。
- **定位：** `scripts/validate_project_state.py:20,366–370,450–457`；written/completed 也使用该同源阶段要求，实际最小探针为 validated。
- **影响：** 规则允许基础三文件交付，状态实现却要求补齐五文件，诱导无必要分析或伪填通过。
- **最小修改：** `scripts/validate_project_state.py` 与 state/output/user-execution 相关 consumer 一起采用已有条件分支；analyzed 与 validated 的语义分别处理，不把两个阶段简单合并。检查 sync、code delivery、framework 和 submission 是否仍复制旧无条件要求。
- **验收：** accepted primary + not_required + 非空理由可进入允许的后续状态；空理由、pending primary、声称已验证稳健性、required 但缺分析仍失败；旧有效五文件项目继续通过。

### AUD-05 · P0 · runtime 别名可抵消已知无效的当前证据

- **证据 A：已复现。** 当前主结果 pending、无工作簿时，传入 `available_artifacts=['solution_workbook','result_quality_report']`，figures route 返回 `assurance=pass`、`missing_prerequisites=[]`；传规范名 `accepted_solution_workbook` 则正确报告冲突。`runtime_assurance.py:548–581` 只按相同名字比较，遗漏别名/派生资格。
- **影响边界：** 已证明 resolver 错误清除了 prerequisite，不等于已执行 MATLAB 或完成正式交付。不能把 assurance=pass 单独当成全部 gate 已通过。
- **最小修改：** 在既有 runtime assurance 中归一化 artifact 别名和派生依赖；project_root 已加载时，未验证的名称不得抵消当前已知无效证据。结果图何时要求 03B 先按后文 O-01 裁决，不能借修别名问题一律强制全部图等待分析。
- **验收：** canonical/alias/派生 token 的成对反例；primary accepted + analysis pending/required missing/not_required 有无理由；跨问部分合格；缺省无项目兼容输入；单独机理图正例。不要删除全部 legacy 只读兼容。

### AUD-06 · P0 · sync 在 stale 传播前完成交付判定

- **证据：已复现。** 一个完整有效的 DOCX 交付夹具先通过；修改其 primary code 后，同次 strict 只读 sync 仍报告 `status=passed, issues=[]`，同时报告 `stale_questions=[Q1]` 与主结果、图、框架失效事件。
- **定位：** `scripts/sync_project.py:612,620–666`；此处 DOCX/PDF 为文件存在性/哈希测试载体，不代表合成论文已做视觉或内容验收。
- **影响：** 本次同步明知来源已变，交付状态却基于旧状态通过；仅提醒 stale 不能代替阻止相关正式交付。
- **最小修改：** `scripts/sync_project.py` 按“发现 → 快照/差异 → transition/stale → 状态与交付 gate → 报告/事务提交”的顺序，用同一 candidate state 判定。只读与写入报告保持一致。
- **验收：** 首次发现变更的同一次调用即拒绝受影响 delivery scope；只改措辞/SIB 外文本不错误失效模型；独立小问不被无差别连带阻断；后续完成真实重验后才能恢复 current。

### AUD-07 · P1 · 根目录 figures 内正式图未进入 scoped 哈希

- **证据：已复现。** 已批准的项目根 `figures/q1.pdf` 改动后，snapshot 的 discovered figures 为空、figure_bundle 为空，sync 仍通过且不产生 stale。
- **定位：** `scripts/project_snapshot.py:188–195,351,374`；`scripts/sync_project.py:368–372`。证据聚焦图状态与 DOCX scope，不声称同样绕过了 LaTeX 自身的图依赖哈希。
- **最小修改：** `scripts/project_snapshot.py`、sync 与 reading-plan 的图绑定共享同一当前 Figure ID/approved path 发现逻辑；覆盖现有合法图目录及同一图的必要载体，拒绝越界路径，去重，避免把无关图片全纳入每问哈希。
- **验收：** question folder、项目 figures、中文名、同名不同目录、增删/修改、跨问共享图、孤立未批准图片、路径越界分别验证；实际字节变化必须进入其声明依赖的 stale 传播。
- **兼容：** 旧合法路径继续读取；新哈希覆盖扩大时显式记录需重新绑定/复核，不自动批准图片。验收只比较文件身份，不做自动看图。

### AUD-08 · P1 · 复现 ZIP 只检查存在某类文件，遗漏具体问题与阶段

- **证据：已复现。** project state 有 Q1、Q2，ZIP 仅包含 Q1 基础 `.py/.xlsx/.m` 与 PDF/框架，缺 Q2 全部文件和 required 的分析产物，`validate_submission_package` 仍 passed。manifest 准确登记了实际入包成员及哈希；缺陷是未验证项目必需集合，不是 manifest 被篡改。
- **定位：** `scripts/validate_submission_package.py:239–245`；现有 archive/member 哈希、重复成员等保护应继续保留。
- **最小修改：** package manifest 从当前项目与 output contract 推导逐问、逐阶段的必要文件集合；validator 同时核对 manifest 来源、路径、成员、哈希及条件性完整性。生成者和验证者不能仅相互相信同一份不完整清单。
- **验收：** 两问完整、少任意一问、required analysis 缺任一文件、not_required 合法三文件、嵌套附件、中文路径、同扩展名替代品、篡改/重复/越界成员。不能用顶层文件名搜索误判合法嵌套附件。

### AUD-09 · P1 · official 精确清单缺文件仍可打包通过

- **证据：已复现。** 合成 verified 规则清单要求 `main.pdf` 与 `required-disclosure.txt`，目录中只有 PDF，official 生成器和 validator 均 passed；不存在的清单项被静默遗漏。
- **定位：** `scripts/hsk_pack_submission.py:76–93,109–111`；`scripts/validate_submission_package.py:48–62,221–227`。
- **最小修改：** 对已核验规则明确必需的精确文件逐项检查，缺失必须失败，不能过滤成较短清单。先澄清已有 submission_files/allowlist 的“允许”和“必须”语义；可选项与通配符零匹配仅按实际规则裁决，不因本反例默认新增 optional schema 或发明赛事要求。
- **验收：** 精确文件完整/缺失、合法 PDF-only、可选项、模式匹配零项/多项、未 verified 规则均有行为用例；生成前与独立 ZIP 验证判定一致。
- **边界：** 上述 disclosure 文件是测试假设，不是任何真实赛事的当届官方要求。

### AUD-10 · P1 · LaTeX 实际输入依赖未完全绑定编译证据

- **证据：已真实编译复现。** 本地 `.sty` 用标准 `\InputIfFileExists` 载入 `values.cfg`；PDF 显示系数 2。随后 cfg 改为 3、不重编译，source hash 不变，旧 audit/compile verification 均返回空 issues。
- **定位与编译条件：** `scripts/latex_delivery.py:21,133–150,330–334,447–456`。合成无文献工程通过 `render_paper.py --profile mcm_icm --bibliography none --runs 1 --clean` 显式参数编译，未更改竞赛默认 profile。
- **影响：** 源码已变化但旧 PDF 仍被当前证明链接受；文件存在且主 tex hash 没变不足以证明来源一致。
- **最小修改：** `scripts/latex_delivery.py` 的依赖发现与 `audit_latex_project.py` / `render_paper.py` 协作，覆盖支持的静态输入，并利用编译实际输入记录核对工程内依赖。遇到无法证明的动态路径，不得标记正式 current/passed，并提示补全来源绑定；避免声称正则能解析全部 TeX。
- **验收：** `.tex/.sty/.cls/.cfg/.def` 条件/嵌套本地依赖、增删/修改、工程外依赖边界、源文件与 PDF 绑定；修改任何实际本地输入后旧报告必须失效。记录实际编译命令、profile 与 source bundle。
- **迁移：** 依赖集合或报告语义改变时显式识别旧报告缺少绑定证据，需要重审/重编译；不伪造新哈希承接旧 PDF。

### AUD-11 · P1 · includeonly 局部编译可被标为全量正式通过

- **证据：已真实编译复现。** main 包含 q1、q2，但 `\includeonly{sections/q1}` 使 PDF 仅有 Question one；静态 source graph 却把两问均视为 active，正式编译仍 passed。
- **定位：** `scripts/audit_latex_project.py:88–139`、`scripts/latex_delivery.py:73–102`、`scripts/render_paper.py:235–255,298–310`；使用与 AUD-10 相同的合成编译参数。
- **最小修改：** 区分局部预览与完整正式编译；formal 模式识别局部排除并拒绝全量 attestation，或要求完整重编译。开发态 includeonly 继续允许，但报告不得宣传完整正文已交付。active assembly 与实际编译范围需一致。
- **验收：** 无 includeonly 全量通过；排除一问或全部内容时 formal 拒绝；仅注释中的命令不误报；局部预览不能升级为 submission 合格证据；分文件章节和条件附录覆盖。

### AUD-12 · P2 · 正文合法引用附录被 prose audit 误报

- **证据：已复现。** `audit_paper_prose.py` 在处理引用前截断 appendix，正文指向附录实际存在标签的引用被报 blocking。
- **定位：** `scripts/audit_paper_prose.py:127–128,200–206,461–471`。
- **最小修改：** 将全文符号/标签解析与正文 prose 检查范围分开；正文表达规则仍可排除附录，但合法引用目标从完整 active assembly 建立。
- **验收：** 正文→附录、附录→正文、跨文件合法引用通过；真正缺失/重复标签仍报错；关闭的附录不得冒充可用目标。

### AUD-13 · P2 · 全文关键词组合误判跨问与否定结论

- **证据：已复现。** 框架中一问出现 HEURISTIC，另一问有可证明的全局最优，或框架明确写“不声称全局最优”，均可被全文关键词检查组成 blocking 冲突。
- **定位：** `scripts/audit_paper_prose.py:443–458`，实际被搜索的是 framework 全文；普通论文中的任意句子不应被描述成相同入口的全部触发条件。
- **最小修改：** `audit_paper_prose.py` 与 framework consumer 按 question、claim、对应 reduction/proof evidence 绑定检查；无法可靠静态判定的语言交人工语义审查，不直接制造 Hard 冲突。保留对真正无依据全局结论的拒绝能力。
- **验收：** 同一 claim 无证明却肯定全局最优为反例；不同问、明确否定、有效 proof binding 为正例。外部引用/条件性结论只有作用域明确、没有被升级成本问已证全局最优时才是正例；无法判定转 review，不能一概放行，也不能全局关闭规则。

### AUD-14 · P1 · 工作簿只读校验未可靠释放文件句柄

- **证据：已复现。** `validate_user_execution.configuration_map` 对缺运行配置表的文件提前返回后，立即重命名 XLSX 报 WinError 32，执行 gc.collect 后才成功。探针为稳定观察生命周期先暂禁自动 cyclic GC，随后恢复并作 collect 对照；不表示每次普通调用必然锁文件或永久锁死。
- **定位：** `scripts/validate_user_execution.py:90–113,264–279,296–326,333–354` 的四个自持有 workbook reader。
- **最小修改：** 审查所有 openpyxl reader 的正常、异常、提前返回路径，用可靠 finally/统一封装关闭 workbook；包括 user-execution、numerical/state/sync 相关读取器，避免依赖垃圾回收或 sleep。
- **验收：** 成功、缺 sheet、坏 header、异常解析后立即重命名/替换工作簿均成功；批量多文件无句柄持续增长；Windows 原生文件操作验证。测试夹具自身句柄泄漏单独修，不混淆产品问题。

### AUD-15 · P1 · 独立代码包 fallback schema 拒绝当前分析工作簿

- **证据：已复现。** 同一含当前运行配置 sheet 的结果分析工作簿，加载仓库 schema 时通过，走 `templates/code/hsk_pipeline/result_io.py` 内置 fallback 时被判“包含未登记工作表：运行配置”。
- **定位与隔离：** `result_io.py:61–66,117–137,192–209`、`workbook_validation.py:259–267`；探针实际复制支持文件到仓库树外、没有 HSK_WORKBOOK_SCHEMA，未 mock schema 选择。primary fallback 也未强制当前必需运行配置表。
- **影响：** 仓库内测试成功不代表复制到用户项目、脱离完整仓库后能正常导出/验证。
- **最小修改：** fallback 与当前 canonical workbook schema 在必要字段、公共 receipt sheet、conditional analysis 上对齐；可由事实源生成或验证最小投影，避免又维护一份会漂移的业务 Authority。
- **验收：** 在临时隔离目录中运行独立支持包的纯工作簿 I/O；repository schema 与 fallback 的同一正反用例判定一致；不导入/运行用户求解代码。

### AUD-16 · P1 · Skill 发现字段与当前宿主格式不一致

- **证据：静态确认，尚未做真实宿主安装。** 两份 SKILL.md 的 frontmatter 有 name/version/summary/triggers，但没有 description，且仓库 lint 仍通过。官方文档说明技能由 name 与 description 开始，description 用于决定何时考虑该技能，见 [OpenAI Build skills](https://developers.openai.com/plugins/build/skills)。
- **最小修改：** 两份入口统一添加符合当前格式、清楚表达工作流/触发条件的 description；自定义 release/兼容 metadata 如何保留需按实际宿主 schema 决定，不仅凭仓库自测。保持 Bootstrap 委托和根/包入口一致。
- **同步小项：** `.codex-plugin/plugin.json:4` 仍宣传 high-contrast composite figures，应改成当前按证据选图、逐图选色的准确描述；历史 release 说明不需批量重写。
- **验收：** 宿主格式校验、根/包入口一致、能力发现正反请求，以及安装后从实际 skill 目录定位仓库资源的 smoke。本文没有把“缺 description”夸大成已观测到插件无法安装；包路径是否失败也仅列集成验证项。

### AUD-17 · P2 · 显式分类冲突漏报、竞赛别名等价却误报

- **证据：已复现。** state 为 optimization/stochastic 且带验证 capabilities，显式 objective=prediction 后 assurance=pass/conflicts=[]，structures/capabilities 变空；state CUMCM 与显式“国赛”又被判冲突，尽管它们属于同一 profile。
- **最小修改：** `resolve_runtime.py:220–259` 使用 canonical competition identity 比较；对显式分类与当前状态的真实差异报告需协调的冲突及来源。继续尊重用户显式新意图，不静默覆盖，也不把未完成的模型迁移说成当前状态已经一致。
- **验收：** 真正不同竞赛/分类、合法别名、集合顺序差异、部分显式字段、多问不一致、旧 primary/secondary 输入分别覆盖，防止错误丢失既有 capability。

### AUD-18 · P2 · 算法与图文模板残留旧正文 Authority 指针

- **证据：静态确认。** `packs/artifact/algorithm_flow.md:3` 将正文位置与表达指向 LaTeX Adapter；`templates/writing/caption_explanation.md:87` 同样把终稿表达指向 Adapter。该 Adapter 已明确正文 Authority 是 Paper Writing Protocol。
- **最小修改：** 只纠正这两处普通正文指针；复杂算法语义继续指向 reasoning contract，LaTeX 环境/编译仍指向 Adapter，不复制规则正文。
- **验收与兼容：** 两个入口均能直接定位正确 Authority，现有能力和模板结构不变；补针对性的活动引用检查，不批量重写历史文档。

### 3.1 原审查观察，不计入已确认缺陷（当前裁决见第 8 节）

| 编号 | 观察与已有证据 | 后续处理边界 |
|---|---|---|
| O-01 | accepted primary + pending analysis 的 figures route 无缺项；workflow 总规则要求 validated_results，但两个 Python README 明确“只消费主结果的图只需 accepted 主工作簿” | 先区分必要性未决、主结果预览、正式图及真正消费 03B 的图，依据现有 Figure Authority 裁决并同步文字/测试。不得先假定全部图必须等待分析；独立机理图保持合法 |
| O-02 | sync 的旧 `_submission_zip_issues` 直接调用时要求 py/xlsx/m，会拒绝 PDF-only；但当前 submission 必需名是 submission_package，该分支仅对 validated_submission_package 名触发 | 尚未证明当前默认链会走到该分支，不列为当前交付故障。A5 做调用可达性审查，确认 legacy 实际用法后再决定兼容或清理 |
| O-03 | 通用表准备层 `dropna(how='all')` 确实把三行中的全空行变成两行；带真实 record key 的缺测行不属于该触发 | 无法仅凭这个案例判定被删的是有效观测还是空白 padding。先明确不同表的记录语义、首尾格式空行/内部缺测区别，再决定是否修改；不批量改变导出行为 |
| O-04 | 缺 description 静态已确认；从实际插件 skill 子目录解析共享资源是否失败尚未做宿主安装实验 | 静态格式及现有复制布局已验证；实际宿主安装/激活未执行，不声称曾经无法加载或当前已动态通过；见第 8 节 O-04 |

## 4. 分阶段实施顺序

每阶段单独形成可审计 PR；同一阶段如果代码与合同范围过大，进一步拆分。P0 阶段完成前不因美化、瘦身或新能力绕过它们。

| 阶段 | 任务 | 依赖 | 完成条件 | 当前状态 |
|---|---|---|---|---|
| A0 | 固定本计划中的反例、整理基线失败原因、增设 Windows 关键检查 | 本计划 | 反例随各阶段补齐；本阶段新增 Windows CI 与事务/句柄反例 | 已验证 |
| A1 | AUD-01 事务；AUD-14 workbook 生命周期 | A0 | 两平台真实读写/故障恢复通过，Windows 失败重新分类 | 已验证 |
| A2 | AUD-02 主数值布尔资格 | A0，落盘验收依赖 A1 | 错误证据不能 accepted；数值型正常规则保持 | 已验证 |
| A3 | AUD-03/04/05 的 03A→Gate→03B→Figure/Writing 条件链 | A1、A2 | required/not_required/pending 各分支及读写一致，别名不能绕过 | 已验证 |
| A4 | AUD-06/07 同步顺序与图来源绑定 | A1、A3 | 首次变更即阻断对应交付，合法 scoped 图完整发现 | 已验证 |
| A5 | AUD-08/09 提交集合与 official 必需项；核实 O-02 可达性 | A3、A4 | 逐问逐阶段完整性与模式一致，缺件/旧证据不通过 | 已验证 |
| A6 | AUD-10/11 编译依赖与完整范围；AUD-12/13 prose 误报 | A0，可与 A2–A4 独立开发；最终接 A5 | 实际依赖变化令旧报告失效；局部 PDF 不当作全量 | 已验证 |
| A7 | AUD-15 独立模板；AUD-16/17/18 入口、上下文与 Authority 指针 | A3 后定稿接口 | 隔离支持包、宿主格式、别名/分类正反例通过 | 已验证 |
| A8 | 跨链集成、兼容矩阵、release carrier、计划收口 | A1–A7 | 全部必需 gate 的真实结果可追溯，未验证项明确交接 | 已验证（本地）；远端发布状态见第 8 节链接 |

版本记录：A1–A5 依次为 9.5.3–9.5.7；A6 为 9.6.0（编译证明 v4 的显式迁移），A7 为 9.6.1；A8 仅补回归和收口文档，不另升版本。各阶段从当时最新 main 串行发布。若修改报告/状态/manifest 的 required 字段或枚举，先评估 schema 版本与显式迁移，不能以修 bug 名义静默破坏旧项目；也不机械把所有配置的独立版本同步成 Skill 版本。

A0 的失败反例先在修复分支记录旧行为，再与对应修复一起通过后合并；不单独往 main 合并必然失败的检查，也不把反例永久 skip/改成通过旧错误行为的断言。O-01–O-03 必须先形成有依据的裁决，只有确认需要改动后才进入对应阶段，不自动当作已授权的重构任务。

## 5. 联合验收矩阵

实现者应将以下场景放进现有测试家族或小型集成 fixture，避免只增加“某文件包含某词”的测试。每个反例都要有邻近正例，防止一律拒绝看似更安全却破坏合法工作流。

| 场景 | 必须满足的行为 |
|---|---|
| Primary pending + 有 analysis receipt | 只读/写入均拒绝 analysis 验收，不产生 validated_results |
| Primary current + analysis required + 有效 evidence | 按序验收，Figure/Writing 可用 |
| Primary current + not_required + 非空理由 | 不索要不存在的分析文件；不宣称稳健性通过 |
| 多问中一问不 current | 相关聚合正式交付不能借另一问通过；独立 scoped 工作保持可用 |
| 伪造 alias/比较关系/通过列 | 不得抵消真实失败的当前证据 |
| 仅修改主代码、accepted workbook 或已批准图 | 同一次 sync 计算 stale 后再判定交付；不沿用旧资格 |
| 仅修改不影响数学语义的说明 | 不无理由升级 revision 或触发整条数值链重算 |
| root figures / question figures | 声明依赖的图均纳入正确 scoped hash；不自动视觉批准 |
| 复现包缺一问或一个 required 阶段 | 明确列出缺失实体；有同扩展名文件也不能替代 |
| verified PDF-only official 包 | 按真实规则允许；不能强塞代码/Excel/MATLAB |
| 未核验竞赛规则 | 不能宣称 official 合规，不能杜撰当届要求 |
| 支持文件改动、includeonly 局部编译 | 旧 attestation 失效或不具全量正式资格 |
| 正文指向附录、不同问结论、明确否定句 | 合法引用和语义不误报，真实缺证据仍被发现 |
| 独立复制的 Python 支持包 | 当前公共 sheet/receipt/schema 判定与仓库一致 |
| Windows 正常与异常返回 | 文件立即可替换，事务可恢复，状态 generation 不丢失 |

## 6. 检查策略、证据与停止条件

### 6.1 各 PR 的最低检查

```text
python scripts/lint_skill.py
python -m unittest discover -s tests
python scripts/generate_indexes.py --check
git diff --check
```

生成索引通过 `scripts/generate_indexes.py`，不手工改 Manifest。源码/文档与生成元数据分开提交。对每次 PR 保存 base/head、专项反例结果、完整测试结果及与基线差异；PR CI 与合并后的 main CI 分别记录。新测试的断言应验证业务状态、文件内容、退出码和来源绑定，不仅验证一个字符串。

Windows 检查不要求把全部 LaTeX 作业搬到 Windows，但 transaction、workbook 句柄、路径/中文名、独立模板和相关 CLI 必须有原生 Windows 覆盖。权限受限的 symlink 用例可根据真实能力明确跳过，并保持有权限平台的路径逃逸用例；不能无条件吞掉所有 OSError。

### 6.2 本轮证据的可重建方式

本地探针与日志保存在维护工作区 `work/repository-audit/`，未混入活动包，也不含用户项目数据。GitHub 上本计划保留了各案例的输入条件、实际错误结果及拟新增断言；实施阶段已把最小反例整理进下列仓库测试，不能依赖某位维护者的绝对路径。

- root 探针：使用 `tests/test_v712_runtime_assurance.py` 的基础 state，改变显式参数/available_artifacts，检查 assurance、missing_prerequisites 与 effective_artifacts。
- model 探针：构造 current schema 的合成工作簿，分别改变底层布尔证据、质量比较关系及 03A/03B 状态；只调用读取/验收器，不执行任务脚本。
- delivery 探针：用临时项目复现 transaction、sync stale、图路径、逐问 ZIP 缺件和 verified 假设规则；所有“官方规则”均为 fixture。
- writing 探针：一个局部 sty→cfg 工程与一个 includeonly 工程，通过真实编译及 PDF 文本提取证实 active source 与实际 PDF 的差异；编译设置和报告不得宣传成用户正式论文验收。

### 6.3 不作超范围保证

本轮未做实际插件安装/能力激活、MATLAB 运行、人工图形观感判断、用户数据端到端复算，也没有穷举 TeX 宏或全部状态组合。这些限制不能通过“静态检查不报错”改写为动态保证。未证实的包路径/宿主行为保持待验证，不直接列为已失败。

如果修复触及模型数学含义、accepted 数值、当届官方规则或用户未授权的真实数据处理，应回到相应已有 Authority 与用户事实，先形成具体可审阅方案。不得为赶阶段完成而自动补结果或增加新的通用强制步骤。

## 7. 迁移、回滚与计划更新

- **读兼容优先：** 保留已声明的 legacy read-only 边界；规范别名和当前证据资格时，明确区分“读得到历史记录”与“能授权当前正式交付”。
- **受影响项目识别：** 针对布尔 verification、not_required、root figures、旧 compile report/ZIP manifest 分别给出识别条件；不要把全仓库历史项目统一标失效。
- **收紧验证：** 先补诊断和受影响报告，保持不改 accepted 文件；必须重验的项目明确原因、所需最小材料与步骤。报告 schema 变动须有旧/新 reader 用例。
- **回滚：** 每阶段以单主题 PR 回滚；涉及新字段/报告时同时说明旧 reader 能否读取。不要回滚成继续接受已证实错误证据的静默行为，应保留清晰阻断或诊断。
- **完成记录：** 每个 AUD-ID 补充 PR/commit、新增测试、Windows/Linux 结果、是否需要用户操作与残留限制。阶段状态仅允许“待实施 / 实施中 / 已验证 / 有明确阻塞”，不把计划文档完成写成缺陷修复完成。

本轮按上述顺序完成仓库修复。后续项目按下面的受影响条件做最小迁移；MATLAB 运行、人工调图及真实宿主使用仍由对应环境验证，不通过仓库测试代替。

## 8. 实施记录

### A7 · 9.6.1

- AUD-15：standalone `result_io` 的最小 fallback 投影补齐运行配置及五类既有 task_profiles 必需任选表；测试对照 canonical 的实际验证字段，并在仓库外隔离进程通过真实 XLSX I/O 比较正负例。没有复制整份规则形成平行 Authority。
- AUD-16：两份 SKILL 入口字节一致，新增简明 `description`；原 version/summary/triggers 内容迁到标准 `metadata`，仓库消费者兼容新 metadata/历史顶层读取。plugin 描述改为逐图选型/选色；不恢复默认高对比。入口说明明确根入口与 packaged 上两级根，通过 bootstrap/plugin 标记定位资源。
- AUD-17：objective/structures/capabilities 按显式轴比较并报告冲突，保持用户显式值、不覆盖未指定轴；`None`/未提供继续 hydrate，显式空列表表示清空并参与冲突检查。legacy labels 先用既有 taxonomy 映射，structures/capabilities 按集合比较，已登记 competition alias 先规范化；多问分类不同保留 ambiguity。
- AUD-18：算法流程和 caption 模板的普通正文指针回到唯一 `modules/05_writing/paper_writing_protocol.md`；不修改该 Authority 本身或增加新的写作规则。
- O04 限定结论：两份实际入口通过 skill-creator quick_validate，已有 plugin 布局复制后的资源路径 smoke 通过；未实际安装/激活宿主，不能宣称全部宿主已发现该 skill。第三方若直接读取旧顶层 version，需改读 metadata.version 或使用本仓库兼容读取方式。
- 新增 12 项专项，含仓库外运行配置正负例与 canonical 投影、格式缺失诊断、显式分轴/清空/生成器/legacy/别名/多问；集成全量和CI记入本阶段 PR。用户模型、MATLAB、宿主安装和图像 QA 均未执行。

### A6 · 9.6.0（compile report v4）

- AUD-10：静态 source bundle 纳入本地 `.sty/.cls` 的字面 `InputIfFileExists/IfFileExists` 依赖及递归引用；原本可选且不存在的配置后来出现也使旧报告 stale。引擎使用 `-recorder`，新编译先移除旧 recorder；v4 绑定 `recorder`、`recorder_sha256`、`actual_input_files`，正式状态要求 `dependency_issues=[]`。
- 实际读入的项目来源必须由预审计覆盖，所有静态正文必须实际读取；未知/动态且无法绑定的项目输入、工程外非安装环境输入、坏或缺失 recorder 不取得正式通过。TeX/标准字体安装文件保持环境边界，不声称逐一内容绑定。
- AUD-11：排除正文的 includeonly、多处/动态且不能确认范围的选择不具全量资格；列齐全部章节的合法正例允许，宏间接漏章也由实际输入核对识别。template_smoke 可作局部预览，正式 reader 仍拒绝其证明。
- AUD-12：label 唯一性与引用在完整 assembled 正文（含附录）中核对；普通正文风格检查仍保持原范围。AUD-13：证据级别与明确主张按小问配对，确定性冲突 blocking，明确否定允许，引用/条件/不清楚作用域交人工 review。
- 迁移：本阶段采用 minor 发布，项目 state/workbook/CLI 不变。旧 v3 及更早报告可读作历史记录，但再次正式交付需运行当前 render_paper.py 重新审计、完整编译，不能只改报告版本；保留当前绑定 `.fls/.log`。不重写旧 PDF 或用户论文。
- 新增 17 项边界测试；七组合成场景通过实际编译、PDF **文本提取**及正式模式提前拒绝，覆盖 cfg 从 2 改 3、可选配置出现、未知实际输入、局部/完整 includeonly、正文指向附录等正负例。不是用户论文验收，也未执行图像 QA。集成完整回归及各 profile CI 见阶段 PR。
- 另按 CI 的 CUMCM + biblatex 最小工程，在本机 TeX Live 2025 实际运行默认编译序列并独立验证 v4 报告。此正例发现并修复 logreq `main.run.xml` 的误报：仅当前主文件对应且同轮 recorder 同时记为 OUTPUT 时视为生成辅助文件；仅 INPUT、用户 XML 和其他 job 名仍拒绝。修复后正式审计、编译与独立证明验证均通过，相关 86 项 LaTeX 测试通过。
- 保留边界：常规正式 render 布局的 main/report 同目录；特殊 main 子目录而报告在上层的历史布局未获本轮完整证明，不新增兼容承诺。不是通用 TeX 宏解释器。

### A5 · 9.5.7

- AUD-08：required set 从当前 state 与既有 output contract 独立推导，逐问 `base3 + conditional2`、project_level 三件套、当前 state/框架/论文、声明数据/批准图片、已登记编译证明与其 source/actual inputs 均按精确路径核对，不能由 ZIP manifest 自证完整。
- 数据源目录按已有 data_source_files 语义展开真实文件，包含中文嵌套路径；不要求 ZIP 中的伪目录条目，不启动未声明数据回退扫描；目录缺失、漏成员、越界明确报错。
- AUD-09：两端复用同一 allowlist resolver，精确路径缺失拒绝；wildcard 保留零匹配可选语义。verified PDF-only official 不强塞内部代码/Excel/MATLAB，未核验规则仍不能生成 official 合规结论。
- v4 报告绑定的实际 `.fls/.log` 仅在精确路径/hash 当前时解除打包排除；不放开全部日志。复现包还核对已登记审计及来源成员；v3 不虚构 recorder，正式证明升级由 A6 负责。
- O02 裁决：旧 `_submission_zip_issues` 对 PDF-only 的反对只存在于非当前默认 required 名称路径；现行 dedicated validator 保持单一提交校验入口，本阶段不加重复 gate。
- 迁移：缺当前 subproblems/必要性判定或逐问材料的旧包可读，但不能再标完整通过；根据明确缺件清单补齐真实材料、重新打包验证。ZIP 生成不等于 validated，不改已有 ZIP 或用户文件。新增正负例与完整回归/CI 见阶段 PR。

### A4 · 9.5.6

- AUD-06：snapshot 更新和 typed stale、paper fragment 传播先完成，再运行状态/框架/正式 scope gate；readonly 与 write 使用相同候选状态，首次文件变化即在同次正式检查失败。只读不写磁盘，写入仍走现有事务。
- AUD-07：snapshot 与 reading_plan 复用 `scoped_figure_files`。既有本问目录图保留；根目录图通过框架“图表证据链”的精确绘图程序/导出路径、脚本字面导出或本问 Figure ID 引用绑定，支持共享或非 MATLAB 图片载体，不猜 q1 文件名前缀、不把所有根图分配给每问。
- 明确本问映射不存在、越界或无有效图哈希时，正式图文 scope 拒绝；新发现图片绝不补 validated hash/批准。旧项目若此前漏跟踪根图，需要按真实来源完善框架映射并由用户核对后绑定已有批准。
- 独立项目级机理/预处理图没有本问映射时给出 warning，注明未覆盖本问 bundle；不强分小问，也不声称存在新的全局图 bundle 验证。
- 12 项新增测试覆盖首次主代码变化、typed 依赖/独立问、根图变化、精确同名路径、Figure ID、literal export、missing validated hash、独立图、readonly fragment 传播及正式/普通 scope；完整回归与 CI 见本阶段 PR。MATLAB 与图像 QA 未执行。

### A3 · 9.5.5

- AUD-03/04/05：代码交付、回执与 runtime 共享当前主结果资格检查。新 03B 必须有 accepted/passed 的主工作簿、有效路径/hash、当前数据身份、非空 necessity reason 与 analysis_methods；回执还需已交付分析代码身份。pending 本身不代表已判 required；not_required 不会被意外回执覆盖。
- 合法 not_required + reason + current primary 可处于 validated/written/completed；不要求分析文件或哈希，不冒充实际 analyzed。历史同一 accepted 分析工作簿只读兼容不追补新 reason；新交付/验收依当前规则。
- 主结果、代码、数据或上游结果变化按已有 typed transition 清除过期 necessity reason。内容改变的主工作簿回执也触发既有 solution_workbook_changed；成功回执仅关闭已验证数值层，保留下游图/框架失效。分析 RUN_CONFIG 不得覆盖主结果 data_hash。
- 状态校验承认完整适用 transition profile 及已明确验收数值层关闭后的剩余传播集，仍拒绝任意无依据 stale 层；与 A4 候选状态检查共同工作。
- O01 裁决：选择绘图规划路由不等于正式图件交付批准。正式数值图依 Module 04/现有 output gate，只有实际消费 03B evidence 的图才要求该工作簿；独立机理图保留自身路由，不统一强制替代世界分析。
- 新边界测试涵盖未验收/缺失/篡改主工作簿、required 未裁决、not_required、只读与写入、别名绕过、多问聚合、相关数值 stale、图件单独 stale、数据身份及验收后状态闭合。未新增 state 字段/枚举、未修改 accepted 用户文件；完整回归/CI 见本阶段 PR。

### 已验证阶段链接

- A0/A1 已合并：[PR #220](https://github.com/Vexushi1/mathmodel-skill/pull/220)，main `06b224d`。本机运行 1103 项，结果 OK（1 项权限限定 skip）；最终 PR 原生 Windows、Linux Python 3.10–3.14、LaTeX 与生成文件作业全部成功。
- A2：[PR #221](https://github.com/Vexushi1/mathmodel-skill/pull/221)，本机运行 1111 项，结果 OK（1 项权限限定 skip）；远端结果以该 PR 当前提交为准。

### A2 · 9.5.4

- AUD-02：严格模式按既有 `recheck_modes.*.quality_relation` 验证；主判定布尔复核为 false 时直接拒绝，不能用 `==`、`<=` 等数值关系绕过。保留数值关系、legacy 只读和非主判定历史失败记录。
- 新增旧版反例涵盖 24 个子场景；修复后检查三类布尔证据、true 正例、缺少主判定行、非主判定 false、混合行以及数值合法关系。回执测试覆盖 readonly 不写、write 后 rejected 且工作簿字节不变、true 后 accepted。
- 受影响项目：采用严格数值验证且主判定布尔证据为 false，或质量行判定关系与 mode 合同不符。先修正证据/结论再重新验收；不会重写历史 accepted 工作簿或自动补真值。完整回归与远端 CI 随本阶段 PR 记实。
- 无 CLI、Schema、真实模型运行、MATLAB 或图像 QA 改动。

### A0/A1 · 9.5.3

- AUD-01：备份改用可写句柄 fsync；staging 内部登记并清理未交给外层的临时文件。保留 writes-before/state/writes-after 次序。
- AUD-14：四个 workbook reader 以 finally 关闭自有文件，业务返回与异常含义不变。
- 原生 Windows CI 覆盖完整 Python 单测；符号链接权限用例独立，只有 WinError 1314 按真实能力 skip，普通路径检查仍执行。
- 事务新增失败注入在旧代码上复现残留，修复后 12 项通过；Windows 完整回归运行 1101 项，结果 OK（1 项仅因 WinError 1314 缺少 symlink 权限跳过），原 40 个失败不再出现；reader 专项 102 项通过。远端 CI 在对应 PR 中记实。
- 无 CLI、state/workbook schema 或用户文件迁移；MATLAB/图像 QA 未执行。
- 首轮远端 Windows CI 另发现 8 fail / 2 error：runner 临时目录的 `RUNNER~1` 与 `runneradmin` 被当成不同根路径。补充规范化数据发现、打包和组合哈希的根路径，以及测量日志路径；增加等价路径与越界反例，保留完整 Windows CI。Linux 各 Python 与 LaTeX 作业首轮已通过；补丁后重新核验。


### A8 · 跨链验证与有限收口

A1–A7 的实现已串行发布；下表记录的是各阶段最终 PR 与其合并后 main 的独立成功检查。早期失败及修正保留在对应 PR 中。A8 的本地验证与远端发布分开：本文在提交前完成本地收口；本次 PR / main 的后续状态由 [PR 检查记录](https://github.com/Vexushi1/mathmodel-skill/pulls?q=is%3Apr+in%3Atitle+A8) 和 [main CI](https://github.com/Vexushi1/mathmodel-skill/actions/workflows/ci.yml?query=branch%3Amain) 追溯，不预填尚未发生的成功。

| 阶段 / 版本 | PR | 合并后 main | 最终 PR CI | main CI |
|---|---|---|---|---|
| A0/A1 / 9.5.3 | [#220](https://github.com/Vexushi1/mathmodel-skill/pull/220) | `06b224d` | [success](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35498113912) | [success](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35498280468) |
| A2 / 9.5.4 | [#221](https://github.com/Vexushi1/mathmodel-skill/pull/221) | `5548069` | [success](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35498304288) | [success](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35498534060) |
| A3 / 9.5.5 | [#222](https://github.com/Vexushi1/mathmodel-skill/pull/222) | `5780c8c` | [success](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35499023010) | [success](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35499222093) |
| A4 / 9.5.6 | [#223](https://github.com/Vexushi1/mathmodel-skill/pull/223) | `371f042` | [success](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35499593565) | [success](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35499763986) |
| A5 / 9.5.7 | [#224](https://github.com/Vexushi1/mathmodel-skill/pull/224) | `bdb9fbd` | [success](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35499803559) | [success](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35500895718) |
| A6 / 9.6.0 | [#225](https://github.com/Vexushi1/mathmodel-skill/pull/225) | `09463a8` | [success](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35501089518) | [success](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35501291528) |
| A7 / 9.6.1 | [#226](https://github.com/Vexushi1/mathmodel-skill/pull/226) | `aabd822` | [success](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35501373349) | [success](https://github.com/Vexushi1/mathmodel-skill/actions/runs/35501539226) |
| A8 / 9.6.1 | 本次收口 PR（发布状态见文件历史与 PR 检查） | 合并提交及后续 CI 见下方动态入口 | 以当前 PR checks 为准 | 以当前 main run 为准 |

- 稳定 A1–A8 源码组合在本机 Python 3.14.5 运行 **1205 项测试**，结果 OK，其中 1 项因 Windows symlink 权限条件跳过；保留普通路径越界检查。不是 1205 项全部实际执行，也不是用户模型复算。
- `lint_skill.py`、`generate_indexes.py --check`、`git diff --check` 及两份入口 `quick_validate.py` 按当前提交核验；远端 CI 包含原生 Windows Python 3.14、Linux Python 3.10–3.14、三个 LaTeX profile 与生产编译证明。
- 21 个声明 intent × 4 个 canonical 竞赛 profile 的 84 场景解析通过；1085 次 load_order 引用（51 个去重文件）均存在。参数为 objective=optimization、project_root=None、preprocessing_decision=not_needed；不表示任意真实项目或全部状态组合已经完成 gate。
- immutable P1 基线的 19 案例保持原始 legacy_behavior_equal=false；24 处 A3 预期版本/资格变化和 36 处 A7 字段来源新增逐项登记，合计 60 处 expected、0 unexpected。负控制继续拒绝其他状态、依赖、来源或分类值差异，没有覆盖整份 golden 或宣称行为完全未变。
- 七组合成 TeX 场景包含真实编译/PDF 文本提取与 formal 提前拒绝；另一个 CUMCM+biblatex 工程在 TeX Live 2025 通过默认完整编译与 v4 独立证明校验。它们不是用户论文，未执行图像检查。
- O-03 增加 4 项结构 I/O 回归，覆盖 keyed 缺测保留、顺序、原输入不变、真实 XLSX 往返和缺审计负例。两份 Skill 静态格式/复制布局通过；真实宿主安装或技能激活未执行。

#### 18 项问题的最终实现索引

原第 3 节是 9.5.2 审查时的反例与定位，不代表当前版本仍有同一缺陷。以下索引定位修复后的生产逻辑与回归。

| 编号 | 实施结果 | 核验入口 |
|---|---|---|
| AUD-01 | 事务 staging 在 I/O 前登记清理对象；Windows 可写备份句柄 fsync；保留事务提交顺序、generation 与恢复语义 | `project_transaction.py`；`test_v900_project_transaction.py`、`test_v900_transactional_writers.py` |
| AUD-02 | 布尔主判定必须服从原合同 bool_true；False 不能借数值比较和伪造 summary 成为合格结果；合法数值规则及未参与主判定的历史失败保留 | `validate_numerical_evidence.py`；`test_v714_numerical_verification.py` 与回执拒绝/接受用例 |
| AUD-03 | code delivery、receipt、runtime 共用当前 primary/Gate 前置资格；03B 不得越过未验收主结果、未决定必要性或失效预处理，不覆盖 primary 数据身份 | `analysis_prerequisites.py`、`validate_user_execution.py`；`test_audit_analysis_boundaries.py` |
| AUD-04 | 合法 not_required+理由+current primary 可进入允许的后续状态，不索要 03B 文件/哈希；不冒充 analyzed 或 accepted analysis；主源变化撤销旧 Gate 决定 | `validate_project_state.py`、state transitions；同一 analysis boundary 测试家族 |
| AUD-05 | 别名和派生 token 不能抵消已知无效证据；validated_results 按每问 primary AND（accepted analysis OR 合法 exempt）聚合 | `runtime_assurance.py`；`test_audit_runtime_qualification.py` |
| AUD-06 | snapshot/transition/stale 先于正式 scope 判定；读写使用一致的候选状态，首次来源变化在同一次检查中阻断受影响交付 | `sync_project.py`；`test_audit_current_artifacts.py` |
| AUD-07 | 根 figures 与本问图按精确 Figure ID/导出路径及 scope 进入 hash；支持共享载体，拒绝缺映射/越界；不从文件名猜依赖或自动批准 | `project_snapshot.py::scoped_figure_files`、reading plan/sync consumer；同一 current-artifacts 测试家族 |
| AUD-08 | 复现包按 current state+output contract 核对每问/每阶段真实必需文件，含嵌套/目录数据源、已批准图和登记编译来源；manifest 自洽不能代替完整性 | `submission_requirements.py`、pack/validate 脚本；`test_audit_package_completeness.py` |
| AUD-09 | verified official 清单中的精确文件缺失即拒绝；wildcard 保留既有可选语义；合法 PDF-only 不强塞内部材料 | 同一 submission resolver/validator 与 package-completeness 正反例；竞赛规则仅使用合成假设 |
| AUD-10 | 受支持的静态条件/嵌套依赖与实际 recorder 输入共同绑定；v4 显式记录 recorder/hash/actual inputs；无法证明来源不获 formal passed | `latex_delivery.py`、`render_paper.py`；`test_audit_a6_latex_boundaries.py` 与七组合成 TeX 编译/提前拒绝场景 |
| AUD-11 | 局部 includeonly 保留开发预览能力，formal 不接受遗漏章节；实际 recorder 再核对主文件和正文输入 | formal audit/assembly consumer；局部/全量/注释/宏隐藏遗漏正反例及合成 PDF 文本提取 |
| AUD-12 | 全文标签和引用命名空间包含附录；普通正文风格检查仍保持原作用域；真正 missing/duplicate 仍报错 | `audit_paper_prose.py`；正文↔附录正反例及合成附录引用编译 |
| AUD-13 | evidence level 与 claim 按同问声明绑定；跨问/明确否定不误判；确定冲突仍 blocking，不确定语言转 review | 同一 prose consumer；同问、跨问、否定、条件、模板提示、legacy flat claim 用例 |
| AUD-14 | 自持有 workbook reader 在成功、提前返回和异常路径可靠关闭文件；不依赖 gc/sleep | `validate_user_execution.py`；`test_audit_workbook_lifecycle.py` 的 Windows 即时 rename/replace |
| AUD-15 | 独立支持包的最小 fallback 投影补当前运行配置与既有 legacy profile 必需表；与 canonical 消费字段保持一致 | `templates/code/hsk_pipeline/result_io.py`；A7 隔离支持包 19 组真实 I/O 正反 case 与投影对照 |
| AUD-16 | 两份入口有有效 description；原 version/summary/triggers 保留于 metadata，consumer 兼容读取；plugin 宣传对齐逐图选色；入口字节一致 | `SKILL.md`/packaged copy、lint；两份实际 quick_validate、当前 package 布局静态 smoke |
| AUD-17 | 显式分类按字段比较且保留未指定项；真实差异报告 provenance/conflict，登记竞赛别名按 canonical 身份比较；集合顺序不造冲突 | `resolve_runtime.py`、scope classification；A7 部分/清空/别名/legacy/多问/单次 iterable 回归 |
| AUD-18 | 算法与图注模板的普通正文指向 Paper Writing Protocol；复杂推理和载体 adapter 的职责不变 | `packs/artifact/algorithm_flow.md`、`templates/writing/caption_explanation.md`；指针回归与保留的整文件漂移守护 |

#### 四项观察的有限裁决

| 观察 | 收口文本 |
|---|---|
| O-01 | 选择 figures 规划路由不等于正式图件交付批准。正式数值图和写作需 scoped current primary，以及 accepted analysis 或带理由的 not_required。只有 Figure Contract 实际消费 03B 才索要该工作簿；独立机理图保留自身非数值路线。not_required 不能证明稳健性、稳定性或替代算法一致性。已补合同和资格边界回归，不统一新增 03B 要求 |
| O-02 | 旧 `_submission_zip_issues` 的扩展名要求属于非当前默认 required-token 路径；现行 submission scope 和 dedicated package validator 未因此禁止 verified PDF-only。保留兼容 helper，没有新增重复 Gate；直接调用旧 helper 的行为不作为当前默认故障 |
| O-03 | 通用表准备层全空行删除按结构 padding 清理保留；带非空记录键的缺测观测不得删。新增 4 项纯 I/O 回归确认 A/B/C 及逆序、B 的 NaN、原输入保留、前中尾全空 padding 清理；生产 XLSX 往返和直接写有空行 XLSX 都覆盖，缺失说明不足仍拒绝。此结论限定于显式记录身份；不声称所有无键全空行在用户项目中无语义，也不修改 MATLAB reader 的全记录保留策略 |
| O-04 | description/metadata 的静态格式差异已修。根入口按自身目录、packaged skill 按上两级现有插件根定位，检查 bootstrap/plugin 标记；两份 quick_validate 和复制现有布局的静态资源路径检查通过。**没有实际 host 安装或技能激活实验**，不宣称曾经必然无法安装，也不宣称当前宿主已动态验证 |

#### 受影响项目的最小迁移

| 受影响对象 | 最小迁移/复核操作 |
|---|---|
| 严格布尔数值证据 | 识别相关 capability/verification 的底层 false 或关系不符记录，按现有合同重新核验真实证据与结论；不把全部历史 accepted 一概撤销，也不补 True 承接旧结论 |
| 03B 与 not_required | 新分析先明确 necessity reason、methods、current primary 和代码交付；不把 pending 自动当 required。合法 not_required 不补伪分析文件，也不宣称稳定性通过。主源/上游数值变化后重新裁决；相同已验收历史 artifact 只读兼容保持 |
| 原漏绑的根目录图 | 完善真实 Figure ID、scope、导出路径和人工确认，再刷新当前来源绑定；新发现图不自动补批准/validated hash，不从名称猜问号 |
| 旧提交包 | 依据 current state 补登记实际问题、分析/预处理决定及数据路径；按明确缺件清单补真实材料后重新打包验证。生成 ZIP 不等于 validated；官方包仍只遵从已核验清单 |
| 编译报告 v3→v4 | v3 保留为可读历史，正式交付需当前源码重审、完整重编译得到 v4 recorder/actual-input 证明，不能直接给旧 PDF 写新 hash。复现包保留精确绑定的 fls/log/audit/source；不向 PDF-only official 强塞内部证明文件 |
| 独立支持文件 | 更新同版 result_io/workbook_validation 支持文件；按既有 canonical 合同提供运行配置和对应专项表。更严一致性校验不授权导出器自动编造 receipt 或用户重算 |
| Skill 入口 metadata | version/summary/triggers 内容保留在 metadata；发布更新器读取/更新 metadata.version，保持两入口一致，历史顶层 reader 兼容不等于继续生成不合格式入口 |
| 显式分类参数 | 未提供 structures/capabilities（None）使用当前 scope；显式空列表/空 flag 表示清空并报告差异。旧调用若本意是“未指定”应省略参数，不能通过 resolver 静默改项目语义 |

无需批量重算或覆盖用户 accepted 数据。编译输入的验证不是完整 TeX 解释器；main 与 report 位于同一工程目录的标准路径已覆盖，历史特殊跨目录布局没有获得额外保证。O-03 只裁决带真实记录键的缺测观测与匿名全空 padding，不替用户定义位置型记录语义。

本轮未执行 MATLAB、自动图像检查或审美评分、用户模型复算、用户正式论文编译、实际宿主插件安装/激活或当届官方规则核验。图表配色仍逐图选择，人工外观调整由用户在 MATLAB 完成；未自动批准任何图件。
