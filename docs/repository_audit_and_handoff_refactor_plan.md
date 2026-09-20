# 全仓库 Skill 审查与衔接修复详细计划

> 状态：审查完成，修复待实施。本文是维护计划，不是新的 Runtime Authority，也不表示下列缺陷已经修复。后续按本文件逐项推进，并在各阶段补录 PR、验证证据与剩余限制。

| 项目 | 本轮记录 |
|---|---|
| 审查日期 | 2026-09-20 |
| 仓库 | Vexushi1/mathmodel-skill |
| 基线 | main，Skill 9.5.2，提交 `f6f64887bd5e4ca8ec00fbd10c33308aa3ade660` |
| 本计划版本 | 1.0 |
| 本次变更等级 | docs / planning-only；Skill 保持 9.5.2 |
| 本次交付 | 本计划及自动生成的索引/Manifest；不实施新的业务修复 |
| 优先顺序 | 状态写入与错误验收 → 结果/路由/同步衔接 → 编译与提交完整性 → 模板与入口一致性 |
| 审查结论 | 18 项确认问题（含静态格式/指针不一致），4 项待裁决观察；未证明用户数据已损坏或真实赛事漏交 |

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

### 3.1 待裁决观察，不计入已确认缺陷

| 编号 | 观察与已有证据 | 后续处理边界 |
|---|---|---|
| O-01 | accepted primary + pending analysis 的 figures route 无缺项；workflow 总规则要求 validated_results，但两个 Python README 明确“只消费主结果的图只需 accepted 主工作簿” | 先区分必要性未决、主结果预览、正式图及真正消费 03B 的图，依据现有 Figure Authority 裁决并同步文字/测试。不得先假定全部图必须等待分析；独立机理图保持合法 |
| O-02 | sync 的旧 `_submission_zip_issues` 直接调用时要求 py/xlsx/m，会拒绝 PDF-only；但当前 submission 必需名是 submission_package，该分支仅对 validated_submission_package 名触发 | 尚未证明当前默认链会走到该分支，不列为当前交付故障。A5 做调用可达性审查，确认 legacy 实际用法后再决定兼容或清理 |
| O-03 | 通用表准备层 `dropna(how='all')` 确实把三行中的全空行变成两行；带真实 record key 的缺测行不属于该触发 | 无法仅凭这个案例判定被删的是有效观测还是空白 padding。先明确不同表的记录语义、首尾格式空行/内部缺测区别，再决定是否修改；不批量改变导出行为 |
| O-04 | 缺 description 静态已确认；从实际插件 skill 子目录解析共享资源是否失败尚未做宿主安装实验 | 在入口阶段做真实安装/路径 smoke；未验证前不声称无法加载 |

## 4. 分阶段实施顺序

每阶段单独形成可审计 PR；同一阶段如果代码与合同范围过大，进一步拆分。P0 阶段完成前不因美化、瘦身或新能力绕过它们。

| 阶段 | 任务 | 依赖 | 完成条件 | 当前状态 |
|---|---|---|---|---|
| A0 | 固定本计划中的反例、整理基线失败原因、增设 Windows 关键检查 | 本计划 | 反例能证明旧行为；不通过删测试获得全绿 | 待实施 |
| A1 | AUD-01 事务；AUD-14 workbook 生命周期 | A0 | 两平台真实读写/故障恢复通过，Windows 失败重新分类 | 待实施 |
| A2 | AUD-02 主数值布尔资格 | A0，落盘验收依赖 A1 | 错误证据不能 accepted；数值型正常规则保持 | 待实施 |
| A3 | AUD-03/04/05 的 03A→Gate→03B→Figure/Writing 条件链 | A1、A2 | required/not_required/pending 各分支及读写一致，别名不能绕过 | 待实施 |
| A4 | AUD-06/07 同步顺序与图来源绑定 | A1、A3 | 首次变更即阻断对应交付，合法 scoped 图完整发现 | 待实施 |
| A5 | AUD-08/09 提交集合与 official 必需项；核实 O-02 可达性 | A3、A4 | 逐问逐阶段完整性与模式一致，缺件/旧证据不通过 | 待实施 |
| A6 | AUD-10/11 编译依赖与完整范围；AUD-12/13 prose 误报 | A0，可与 A2–A4 独立开发；最终接 A5 | 实际依赖变化令旧报告失效；局部 PDF 不当作全量 | 待实施 |
| A7 | AUD-15 独立模板；AUD-16/17/18 入口、上下文与 Authority 指针 | A3 后定稿接口 | 隔离支持包、宿主格式、别名/分类正反例通过 | 待实施 |
| A8 | 跨链集成、兼容矩阵、release carrier、计划收口 | A1–A7 | 全部必需 gate 的真实结果可追溯，未验证项明确交接 | 待实施 |

版本安排：本计划不预占具体发布号。后续各 PR 从最新 main 开始，按治理判定 patch/minor；一般缺陷修复优先兼容 patch。若修改报告/状态/manifest 的 required 字段或枚举，先评估 schema 版本与显式迁移，不能以修 bug 名义静默破坏旧项目；也不机械把所有配置的独立版本同步成 Skill 版本。

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

本地探针与日志保存在维护工作区 `work/repository-audit/`，未混入活动包，也不含用户项目数据。GitHub 上本计划保留了各案例的输入条件、实际错误结果及拟新增断言；后续实施 A0 时把最小反例整理进仓库测试，不能依赖某位维护者的绝对路径。

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

下一轮从 A0/A1 开始，先恢复 Windows 状态更新与工作簿释放能力，再推进数值资格和 03A/03B 条件链；不要先做大规模代码精简或整包重构。
