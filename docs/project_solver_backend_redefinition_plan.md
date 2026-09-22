# 项目级唯一求解后端：清理与重新定义计划

> 状态：待审议计划，不是当前执行 Authority，不代表实现已经修改。
>
> 本轮授权：重新阅读仓库，记录问题，写修改计划。未授权修改实现、升级版本、执行迁移或合并。
>
> **全仓逐字阅读尚未完成。** 已完成完整文件清单、全部 UTF-8 文本的主题扫描，以及下述核心链路全文阅读；不能将下载成功、哈希一致、关键词扫描或旧 CI 通过当作全仓内容读完。

## 0. 修改简报与固定基线

| 项目 | 内容 |
|---|---|
| 仓库 | `Vexushi1/mathmodel-skill` |
| 当前默认分支 / Skill 版本 | `main` / `9.7.1` |
| 固定审阅提交 | `34deb02ff590d061fc7ca36f9bd2742a6653c797` |
| 固定完整文件树 | `9c8e9e02786c54f902b1eb6296801f3f1233ae9d` |
| 本轮文档分支 | `docs/project-solver-backend-redefinition-plan` |
| 本轮变更等级 | `docs`，仅新增本计划；不修改当前规则 |
| 实现版本 | 尚未冻结；见第 12 节，不提前承诺为 v9.8.0 小版本兼容变更 |
| 直接目标 | 将新项目的数值求解后端改为全赛题唯一选择，取消逐问、逐阶段重新选择；清除旧活动表述和重复选择路径 |
| 明确不做 | 不改变数学模型审批、数值质量标准、用户执行所有权；不把所有代码合成一个文件；不强制同一算法；不取消条件式深化；不运行用户赛题 |
| 权威来源 | `core/user_execution_contract.yaml` 定义行为；Project State Schema 定义字段；Runtime Assurance 定义恢复；State Transition 定义失效。计划本身不另立规则 |
| 迁移原则 | 一个当前语义、一条当前写路径；历史记录可读但不能伪装成新协议已验收；不批量修改历史工作簿和用户源码 |
| 验收原则 | 先补齐直接影响面的未读部分；实现后新增正反测试并保留原有身份/数值/读取保护，再跑最终提交全套检查 |
| 回滚 | 本轮仅撤回计划提交；未来实现用正常 revert 与明确迁移回滚，保留历史证据，不移动旧标签 |

开始及写文档前均重新读取了 `main`；上述 SHA 未变化，当时 open PR 集合为空。原 PR #229 已合并，不在旧 PR 上追加新的作用域重构。

程序化阅读使用此前 CI 的候选源码归档，但不是依据归档名称认定版本：重新计算所有文件及模式组成的 Git tree，与当前 main 的 tree 完全相同后才作为本轮静态阅读副本。此结论只证明文件身份相同，不证明语义全部读完。

## 1. 实际阅读范围、未完成部分与证据等级

### 1.1 覆盖统计

| 阅读层次 | 数量 | 可以作出的结论 |
|---|---:|---|
| 全部 tracked 文件清单 | 549 个 | 文件路径、类型、大小和快照身份已核对 |
| UTF-8 文本 | 534 个，共 102442 行 | 全部完成解码与后端相关模式扫描；不是全部逐行理解 |
| 全文展开并阅读 | 106 个 | 具体文件见附录 A，覆盖核心 Authority、状态、运行时、交付、回执、同步、打包、主要模板和后端专项测试 |
| 部分区段阅读 | 2 个 | `CHANGELOG.md` 1—94/639；`scripts/lint_skill_checks.py` 790—860、1295—1415/1443 |
| 仅清单和主题扫描 | 426 个文本 | 未作全文审读，不能宣称没有相关隐患 |
| 二进制或非 UTF-8 内容 | 15 个 | 未做内容/视觉审读，仅文件身份层核对 |
| 实际已展开阅读的去重源文件行 | 26771 行 | 包含上述全文和部分区段；不把重复读取累计成更多覆盖 |

主题扫描同时考虑 `backend`、`solver_execution`、混合语言、逐问选择、固定 Python/MATLAB 和项目级预处理等表述；关键词命中用来定位，不用来证明未命中文件没有问题。绘图渲染后端、draw.io 后端和文献编译 backend 不等同于数值求解后端。

### 1.2 这份计划的可信范围

以下发现分为三类：

- **F：已读源码或文档中的事实。** 可以按本计划给出的固定版本路径及行号核对。
- **D：根据用户目标提出的设计。** 是待确认的目标，不冒称当前仓库已支持。
- **R：由静态衔接分析发现的风险。** 本轮没有执行端到端故障复现，不写成已发生的数据损坏或运行失败。

本轮没有重跑全量单元测试、MATLAB、LaTeX 或用户模型。旧版“1354 项测试”等数字不是新定义的验收证据。文档 PR 自动触发的仓库检查即使成功，也只说明该文档提交与当前代码相容，不能证明本计划已经实现。

### 1.3 尚未全文阅读的范围

包括大部分历史计划与 `legacy/`、大部分非后端专项测试、完整写作推理/写作运行时合同、完整 Paper Writing Protocol，以及不少图表、LaTeX、审查和领域 Pack。不能笼统说“写作、图表、终审全部读完”。

实施前至少继续补读：`scripts/lint_skill_checks.py` 剩余区段；涉及当前配置和状态字段的 Schema/交易/读取测试；`tests/test_audit_a7_entry_consistency.py` 等独立支撑包测试；将被改动的写作/终审读取配置及其真实引用者。具体路径须先从当时的完整树确认，不靠旧聊天猜文件名。若进一步扩大删除范围，必须先读完扩大的文件及其引用关系。

## 2. 重新审阅后的关键判断

当前 per-question/per-stage 行为不是孤立的注释错误，而是 v9.7.1 有意实现的能力：不同问题可选不同语言，深化可另选语言。用户现在要求改变这一设计，必须连同状态写入和消费者一起重新定义，不能把原设计全部追认成过去的实现 bug。[S01][S02]

本计划修正上一轮建议中的四点：

1. **不新增一套 Project Backend Selection Gate 或独立审批系统。** 选择发生在全题需求审视和现有 Model Approval Brief 中，工程一致性由现有门执行。当前 Authority 明确要求不另加审批。
2. **不把根后端与每阶段 backend/reason 长期一起写成“双份投影”。** 新活动状态只有一个选择来源；旧字段只在显式历史读取/迁移边界解释，不继续作为当前写入目标。
3. **不删除运行事实。** `RUN_CONFIG.solver_backend`、`RUN_RECEIPT.solver_backend`、源码 bundle 和主工作簿摘要不是重复政策，而是实际执行证据，必须保留。
4. **不先定 v9.8.0 再强说兼容。** 删除现有 Schema/CLI 行为可能属于破坏性变更；须完成迁移边界设计后按治理规范确定版本。

干净的目标是：**删除分散的选择权，保留必要的逐问执行证据和阶段职责。**

## 3. 问题台账：已发现什么、应如何处理

下表的行号均指第 0 节固定提交的源文件，不是未来修改后的行号。

| ID / 类型 | 位置 | 发现及后续动作 |
|---|---|---|
| B01 / F | `core/user_execution_contract.yaml:4,6—35` | 明确 per-question/per-stage，允许跨问混用和 analysis 脱离 primary。整体重写该政策块为项目级，不在旧条款后追加优先级例外 |
| B02 / F | `core/runtime_assurance_contract.yaml` 的 `input_resolution.rules` | 明确要求恢复逐问选择且不把不同问题合并成一个后端。删除该旧语义，定义根策略恢复、冲突阻断和全题范围一致性 |
| B03 / F | `core/project_state.schema.yaml:124—134,435—441,540—559` | stage 记录要求 backend/reason，根 execution 没有统一后端字段，且禁止额外字段。不能只往 YAML 随意塞根字段；须同步 Schema 与所有 writer |
| B04 / F | `scripts/resolve_runtime.py:173—210,329—341` | 逐问/阶段解析，analysis 可覆盖 primary，集合可能混合；实际恢复阶段已修复，应保留。改为项目策略单一解析、实际阶段只选同语言对应模板 |
| B05 / F | `scripts/runtime_assurance.py:420—487` | 按 question scope 过滤后构造 `solver_backends[q][stage]`，也有历史 `.py` 推断。新增项目策略检查不能放在单问过滤之后，否则请求 Q1 会漏掉 Q2 的冲突 |
| B06 / F | `scripts/validate_code_delivery.py:631—633,693—699` | 交付器可从 RUN_CONFIG 写回 stage.backend，并补“按已交付RUN_CONFIG确定实现后端”的理由。**这条反向选择写路径必须删除**；交付只验证既定项目选择并登记源码身份 [S03] |
| B07 / F | `scripts/stage_code.py:104—166,481—566` | 共享解析和 binding 只拿本问 entry/stage 判断；现代协议检测与 stage 状态有关。接口须显式接受当前项目策略；删旧字段不能把 1.1 降成 legacy |
| B08 / F | `scripts/validate_user_execution.py:242—296,446—575` | 回执与交付源码及本阶段选择比较，没有项目级唯一来源。补项目策略一致性，保留实际 receipt.backend 与成功验收才更新 validated bundle 的边界 |
| B09 / F | `scripts/analysis_prerequisites.py`；`scripts/validate_project_state.py:414—567` | 前置核验/状态校验没有项目级同后端约束。共享前提应接受项目快照，不能每个调用点又自行猜后端 |
| B10 / F | `scripts/project_snapshot.py:179—223,414`；`scripts/sync_project.py:280—307,625—713` | 当前 observed 实现与逐阶段 backend 比较。旧字段直接删除将造成误判或漏判；同步改为与根策略比较，但不能替项目作选择或刷新交付/验收身份 |
| B11 / F | `scripts/submission_requirements.py:164—215` | `require_stage` 读取阶段选择，含 Python 默认回退。新项目不能缺策略就按 Python 找文件；复现要求必须由同一个根策略和实际激活阶段派生 |
| B12 / F | `agents/openai.yaml:4` | 仍硬写“Generate full-fidelity Python code”，并把 MATLAB 不重算写成过宽表述；与当前 MATLAB 数值求解已冲突。缩短为当前 Authority 委托，禁止复制另一份长业务规则 [S04] |
| B13 / F | `SKILL.md:6,32,96` 及 packaged Skill；`AGENTS.md:13`；`PROJECT_INSTRUCTIONS.md:15` | 存在 per-question 摘要、current-stage 选择和 Python 名称兼容发现 token。分别清理政策与纯发现词，不能用全仓字符串替换处理所有 Python 字样 |
| B14 / F | `modules/02_model_design.md:139`；03A；`modules/03_result_analysis.md:36,47`；03P | “本问实现后端”“确需另一后端时记录理由”继续授予重新选择权。按第 5 节就地重写/删除；保留每问数学方法和条件式 03B |
| B15 / F | `templates/model/model_paper_framework.md:16,253—433,408` | 全局当前口径没有项目选择；后端/reason 被放在每问当前模型口径中。移到全局工程记录一次，数学 SIB 不纳入语言/环境；算法语义仍逐问管理 |
| B16 / F | `README.md:536—557,599—625,655—656` | 当前流程仍固定 `.py`、无条件“五文件”示意；写作 Authority 前后还不一致。删除冗长重复说明，保留一份当前导航。不是靠底部再加“新版本以此为准” [S05] |
| B17 / F | `RUNTIME_ROUTER.md`；code/full_submission/review Pack；代码模板 README | 后端选择和目录规则被多处重复讲述。删重复政策和硬编码目录树，读者引用唯一 Authority；不要新增一份“统一后端规范.md”作为平行来源 |
| B18 / F | `core/workflow_router.yaml:430—434`；`scripts/reading_plan.py` | 返回工作簿的范围读取只选 assistant_policy/returned_workbook，未包含选择政策。新规则必须进入相关 read_now/dependency closure；删标题或 YAML key 要同步精确选择器 [S06] |
| B19 / F | `tests/test_solver_backend_downstream_identity.py:85`；runtime_resume/boundaries/integration | 某些公共夹具默认令 analysis 使用相反语言。不能只改业务代码后逐个放宽断言；先使正常夹具继承项目选择，混合仅用于显式拒绝或历史读取测试 |
| B20 / F | `tests/solver_backend_mixed_smoke.py`；`.github/workflows/ci.yml:158—165` | 跨问/同问混合被作为 native 正例。改为 Python、MATLAB 两个独立同后端项目的完整正例，加混合拒绝负例；不能简单删掉 CI 能力和历史证据 |
| B21 / F | `templates/code/hsk_pipeline/main_pipeline.py:306—348,368—412,458` | 支撑模板仍直接 safe_dump/write_text 项目状态，并重复失效和字段写入；不经过仓库项目事务。不是只改根字段就能统一写权 [S07] |
| B22 / R | 同 B21；`scripts/project_transaction.py:322—332,384—489` | 用户求解模板写回旧状态可能与新的项目后端锁/状态 generation 竞争。此为静态并发风险，未复现丢失更新。新活动数值模板应只产出工作簿/回执，由既有事务门登记，不复制事务引擎进赛题代码 |
| B23 / F+R | `templates/code/hsk_pipeline/result_io.py:13—26`；`scripts/python_source_checks.py` | 支撑助手通过 spec_from_file_location/module_from_spec/exec_module/sys.modules 动态加载。若作为项目 helper 纳入 1.1 闭包，将遇到检查器明确禁止的形式。源码形式已确认；完整复制包交付尚未端到端复现。应改静态导入或停用该动态装载路径，**不得豁免模板来放宽来源门** [S08] |
| B24 / F | `templates/code/hsk_pipeline/main_pipeline.py:500—532`；其 README；5 个 starter | combined runner 和旧 analysis API 已有 legacy 限定，starter 也明确是需实例化的骨架。不能误称它们已自动成为新 1.1 正式交付；但须从新默认路径剥离，避免作为现成工程整包复制 |
| B25 / F | `core/user_execution_contract.yaml:132—143,419—421`；v970 迁移说明 | 当前兼容窗口与旧 P9 裁决表述并存。整理成一份明确迁移边界；不要在多个说明中各自维护退出条件 |
| B26 / F | `scripts/generate_indexes.py:46—51,142`；refresh-generated workflow | 维护文档分类使用已有规则；新计划可能落入 historical_provenance，不等于应进入 runtime。实现前审视该分类是否需调整；本轮不改生成器，更不能手填 MANIFEST |
| B27 / R | `scripts/reading_plan.py:175—216`；快照/同步文本读取 | 读取计划还会重新读项目状态；一些发现路径有宽松文本解码。须测试快照之后状态变化及非法编码的影响。本轮未证明故障，不将其写成“已复现漏洞”，不混成新的无边界安全重构 |

## 4. 新定义：只有项目选择权，仍有各阶段执行事实

### 4.1 唯一不变量

设当前赛题项目为 P，小问集合为 Q，s 为 primary 或已由 Analysis Necessity Gate 激活的 analysis：

$$
B_{q,s}=B_P,\qquad B_P\in\{\mathrm{python},\mathrm{matlab}\}.
$$

没有“必要时本问覆盖”“写个理由就能改深化后端”“自动发现哪个更方便就换”的新活动例外。

后端固定不限制模型和算法：同一 Python 项目可按问题使用不同 SciPy/优化/统计方法；同一 MATLAB 项目也可使用不同 solver。语言、算法和数值精度必须分别定义，不能因统一语言擅自改变数学保证。

### 4.2 范围边界

| 对象 | 新定义 |
|---|---|
| 全部问题的主求解 | 必须使用 B_P |
| required 的结果深化分析 | 必须使用 B_P；未激活时不生成分析入口或空工作簿 |
| 问题局部数值变换、求解 helper、数值检验 | 跟随 B_P；不能借 helper/shell/engine 隐藏另一数值后端 |
| 项目级预处理 | 本次保留当前 Python、receipt 1.0 和独立状态；不是逐问求解选择权 |
| 正式图表 | 保留 MATLAB 只读已验收数据的职责；不能把 MATLAB 求解函数误认为绘图脚本 |
| draw.io / 机理图渲染 / 文献编译 | 独立工具职责，不接受数值后端的全仓替换 |
| LaTeX / 可选 DOCX | 保留既有论文主链，不与 B_P 混为唯一工具语言 |
| 外部已安装数值库内部实现 | 不因其底层 C/Fortran/C++ 就判为切换后端；依赖可用性和来源证明仍按原能力边界 |

**一赛题一后端，不等于一赛题一个大脚本。** 保留各问独立主求解入口、条件式分析入口和结果工作簿。统一的是选择和环境组织，不是将无关模型拼进同一入口。

### 4.3 选择时机

完整读取题面并审视所有小问的数值能力需求后，在第一次正式任务代码交付前选定一次。无需把所有小问最终模型都做完才开始任何工作，但不能只看 Q1 就无条件冻结全题后端。

需求审视至少回答：哪些方程/优化/统计/离散结构必须支持；预计会用到哪些不可替代数值保证；已知规模和运行环境；用户明确偏好；必要依赖与未核验条件。可预见的后续分析能力应纳入评估，但不得提前创建 required 分析计划或运行分析。

选择理由放入既有 Model Approval Brief 的实现范围和全局工程记忆。`auto` 只是请求，不是持久化的已选结果。运行时不得以路由输出冒充包、工具箱、许可证已验证。

若以后发现 B_P 无法可靠支持不可替代方法，应停止并提出全项目迁移或数学方案重审，不得静默换语言，也不得仅为了维持语言而偷偷降精度、缩范围或换成不等价模型。

## 5. 文档清理：删旧表述、改 Authority，不堆例外

### 5.1 逐类处置矩阵

| 文件/组 | 应删除或退出活动路径的内容 | 应保留或重新定义的内容 |
|---|---|---|
| `core/user_execution_contract.yaml` | 每问/每阶段选 backend；analysis 可另选的许可；过时且重复的兼容裁决文字 | 就地重写 `solver_backends` 为项目政策，指向根状态；保留 source bundle、用户执行和阶段回执事实 |
| `core/runtime_assurance_contract.yaml` | “不将不同问题合并为一个后端”的恢复规则 | 根策略恢复、冲突阻断、缺失策略的处理、当前/历史边界 |
| 根/packaged `SKILL.md` | per-question summary、current-stage 选择许可；无必要的固定 Python 发现约束 | 两入口逐字一致；一处简短项目策略委托；保留所有其他能力发现与稳定导航 |
| `agents/openai.yaml` | 固定“生成 Python”、过宽“MATLAB 不重算”和重复业务长链 | 短启动指令、当前项目策略、user execution、绘图角色的精确边界 |
| `AGENTS.md` | 独立的每问选择要求 | 引用执行 Authority 的项目唯一策略；不再次复制全部状态规则 |
| `PROJECT_INSTRUCTIONS.md` | 重复五文件树与逐问后端政策 | 目录委托 output contract，执行委托 user_execution |
| `RUNTIME_ROUTER.md`、`scripts/README.md` | 每一阶段再裁决语言的说明 | 只说明 CLI 请求、项目恢复、实际阶段模板与错误诊断 |
| `modules/02_model_design.md` | 为“本问”选语言的动作 | 全题需求审视中一次选择；每问仍说明自己的数学 solver 和验证条件 |
| `modules/03_solve_validate.md` | 暗示每问可重新选语言的语句 | 验证已锁项目策略、按本问生成独立源码及 PQS |
| `modules/03_result_analysis.md` | “确需另一后端时记录理由”及 stage override | required 时只继承 B_P；保持 accepted 主簿只读、独立分析源码与 bundle |
| `modules/03_data_preprocessing.md` | 本问后端另选表述 | 区分全局 Python 预处理和随 B_P 的局部数值变换 |
| `templates/model/model_paper_framework.md` | 每问重复 backend/reason 行 | 全局当前口径中记录一次项目后端；各问保留算法、代码锚点和证据 |
| `templates/writing/code_appendix_description.md` | 逐问选择语言的讲法 | 报告共同 B_P 和各问不同算法、源码路径；不强制一种代码组织 |
| code/full_submission/review Pack | 复制选择许可、硬编码求解 `.py`、固定五文件树 | 简短角色说明及 Authority 指针；独立“阶段入口”不写成独立“选择后端” |
| starter / hsk_pipeline / MATLAB README | 多处重复选择流程、混合后端当前推荐、combined runner 默认误导 | 模板的数学适配、明确可用边界及实例化检查；旧 API 仅保留在明确历史边界 |
| `README.md` | 重复版本长史、第二份数值流程树、过期当前写作 Authority | 重新组织为当前简介→启动→职责→唯一来源导航→安装/兼容/历史链接；历史本身仍由 CHANGELOG/Git 保存 |

### 5.2 README 的具体重写方式

本轮已阅读全文 681 行。建议不在原末尾再加“vNext 特别说明”，而是整体整理其组织：

1. 顶部只说明当前能力与最短启动步骤，不复制几十个版本的演进。
2. 当前数值流程使用“项目策略→各问主求解→accepted→按需深化”的角色表达，不硬编码所有入口为 `.py`。
3. 删除无条件“每问唯一五文件目录”；精确数量交给 `core/output_contract.yaml` 的基础产物与条件式产物定义。
4. 当前写作导航只保留一份：普通正文委托 Paper Writing Protocol，LaTeX 为 Adapter，复杂证据裁决回到 Writing Reasoning Authority。仅修导航冲突，不顺带重写写作方法。
5. 版本历史链接到 CHANGELOG 和 Git，不新增另一份同内容历史 MD。

不能把所有含 Python 的段落一概删除：项目级预处理、历史命名、真实回执、测试环境和 Python 示例可能完全正确。也不能删除所有写着 backend 的字段：draw.io/图形/文献等后端属于另一职责。

### 5.3 历史文件如何处理

`docs/v970_solver_backends_migration.md` 和 `docs/v971_backend_contract_audit.md` 记录了真实历史设计与修复，不应改成“当时已经是一题一后端”。未来版本可从活动导航移出、明确历史适用范围，并指向当前 Authority。未完整阅读的其他历史计划不在本轮列为整文件删除对象。

任何整段/整文件删除前必须检查：所有 Markdown 链接、bootstrap/manifest 指针、heading/YAML selector、lint 发现 token、CI 文档分类和模板引用。删除有价值的数学/证据规则来缩短文档，不属于本计划。

## 6. 状态结构与写入权：清洁目标

### 6.1 建议的当前状态形态

以下为待实施 Schema 示例，不是可以直接写入 v9.7.1 的有效状态：

```yaml
execution:
  solver_backend: python
  solver_backend_selection_reason: "基于全题需求、用户环境及必要数值能力完成一次选择"

subproblems:
  Q1:
    solver_execution:
      primary:
        bundle_sha256: "...真实源码集合摘要..."
        validated_bundle_sha256: "...只由成功验收写入..."
      # analysis 仅在确实激活时存在
```

新活动结构不再在每个 stage 存一个拥有选择意义的 `backend` / `selection_reason`。`execution.solver_backend` 只能为 python 或 matlab；缺失表示尚未选择或需要历史迁移，不能等同于 Python。`auto`、空字符串、未验证自由文本不是已锁后端。

选择与非空理由共同校验；不要为了一个选择引入多层 policy 包装、另一个项目 JSON、长期 shadow 字段或重复 trust token。

### 6.2 谁能写

| 动作 | 允许写入项目选择吗 | 说明 |
|---|---|---|
| 显式完成首次项目后端选择 | 是 | 在已有模型设计/批准衔接中，用当前项目事务提交；须有需求/理由而非由首份源码倒推 |
| `resolve_runtime` / hydration / reading plan | 否 | 只恢复、报告候选和冲突，不偷偷保存 |
| 代码交付 / 工作簿回执 | 否 | 验证项目选择；登记本阶段实际身份和执行状态 |
| sync / snapshot / pack | 否 | 观察和判定，不替缺失字段补 Python |
| 用户赛题数值模板 | 否 | 不拥有整个项目状态的写入权 |
| 明确授权的项目级后端迁移 | 是 | 与受影响产物失效一次性提交，绝不只修改一个字符串 |

实现上优先在现有共享 stage/状态基础设施中集中纯策略解析和一致性检查，再由现有项目事务承载首次选择/迁移写入。不为 resolver、delivery、receipt、sync 各造一个后端管理器。

### 6.3 为什么运行配置中仍保留 backend

项目根策略回答“这个赛题应使用什么”，RUN_CONFIG/RECEIPT 回答“这一份代码和这一轮执行实际使用什么”。必须满足：

```text
project policy
    = delivered source backend
    = RUN_CONFIG.solver_backend
    = RUN_RECEIPT.solver_backend
```

其中后面三者是证据，不是新的选择权。不能删掉回执字段后，只凭当前根字段断言历史工作簿由该语言生成。

源码 bundle、输入摘要、analysis 的 primary_workbook_sha256、数值证据和已有 accepted 条件继续有效。不要把整个频繁变化的 Project State 文件做成新的自引用摘要塞入入口，也不要新建专门“后端回执工作表”。

## 7. 运行时、验证器与模板的详细改法

### 7.1 运行时解析

`runtime_assurance.py` 先加载并验证项目策略，再处理本次 question scope。项目范围只检查选择/状态声明的一致性，不借机把所有小问工作簿都重新做数值计算或全文读取。

`resolve_runtime.py` 收敛到一个项目选择结果：scope=project、resolved、source、selection_complete、conflicts；实际 resumed stage 仍单独保留。`by_question` 若为历史调用做只读诊断投影，不能是新活动事实源，也不能继续持久化不同选择。

`resolve_workflow.py` 只保留已声明的无状态/历史规划边界；当前正式交付不能通过省略新参数绕过项目策略。模板加载使用一个数值后端和实际恢复阶段，不取多后端集合的并集。

| 请求场景 | 目标行为 |
|---|---|
| 项目已锁 Python；请求 auto 或省略参数 | 使用项目 Python，不再问每一问 |
| 项目已锁 MATLAB；进入 Q2 或 analysis | 继承 MATLAB，不能从旧 `.py` 默认改回 Python |
| 项目已锁 Python；请求 MATLAB | 明确冲突/review_required；不写 state、不产出另一后端代码、不自动使旧结果失效 |
| 新项目尚未选择；请求 auto | 返回一次项目选择待办，不输出已确定语言的正式求解代码 |
| 新项目尚未选择；明确请求 Python | 作为候选进入可行性与既有批准衔接；不能把参数本身冒称已完成依赖验证 |
| 无项目根、只有泛化方法咨询 | 可作候选规划，不能声称已为某真实项目持久锁定后端或允许正式交付 |
| 请求 Q1，而 Q2 存在与根策略冲突的当前声明 | 项目策略冲突可见；不能被 Q1 scope 隐藏 |
| 请求 analysis 但主结果失效 | 回到实际需要的 primary 阶段，仍使用同一 B_P |

### 7.2 共享源码解析与代码交付

`stage_code.py` 的 stage resolver/binding 接收当前项目策略或由一个统一上层传入的不可变快照，不在每个下层函数重新读磁盘状态。所有源码命名、扩展名、RUN_CONFIG、helper 声明必须与当前 B_P 匹配。

保留新协议不能缺元数据降级的防线。取消 stage.selector 后，`requires_bundle_binding` 不能仅因该 selector 不再存在，就将现代入口当作旧协议。

`validate_code_delivery.py` 删除从配置产生 backend/reason 的写入段；缺项目选择即阻断当前正式交付。继续做 accepted 主代码冻结、静态检查、MATLAB Code Analyzer、源码变化重检、bundle 记录和项目事务。纯配置解析工具可在无 state 时检查字面量，但必须与“正式交付通过”明确区分。

求解 helper 不能暗中执行另一后端；然而绘图 `.m`、历史证据文件和已安装数值库不能仅因扩展名被全工程禁用。限制针对实际求解执行闭包，不是 ZIP 或目录中所有文件。

### 7.3 回执与主结果前提

`validate_user_execution.py` 在入口/配置/回执一致之外，核对项目策略；失败不能刷新 delivered 或 validated 身份。

`analysis_prerequisites.py` 和其 runtime/delivery/receipt 调用者使用同一份当前项目上下文；主簿 accepted、质量通过、无 stale、源码/输入/主簿摘要匹配等现有条件全部保留。统一语言不是降低这些条件的理由。

MATLAB 数值入口继续独立原生运行，不为读取 Python 风格项目状态而偷偷调用 Python。项目策略由交付与验收门强制，入口中的语言事实受源码和回执绑定；不把“不能单独证明项目授权的原生运行”声称为已验收。

### 7.4 快照、同步与打包

`project_snapshot.py` 把根策略用于 observed implementation 与合法入口判定；保留真实文件身份，不从目录中的第一份文件建立策略。

`sync_project.py` 用候选状态验证当前政策，不能继续比较已删除的 stage.backend，也不能无变化就重绑定。CLI 偏好冲突是请求冲突；真实迁移是状态变更，两者不能都触发全题 stale。

`submission_requirements.py` 去掉新项目缺策略时的 Python 回退，统一以 B_P 和 stage activation 派生必需文件，再加入真实输入和 helper。`hsk_pack_submission.py` 能创建 ZIP 不等于包已验收；不要通过粗暴删除所有另一语言文件“制造一致”。正式包资格仍由 submission validator 判定，official allowlist 与复现包范围继续分开。

### 7.5 Python 支撑模板的清理

这里是减少工程混乱的重点，而不是新增更多兼容 wrapper：

1. 当前新数值模板原则上只产生工作簿及回执，不直接写整份 Project State。剥离新默认调用链中的 `_write_state`、`_update_primary_state`、`_update_analysis_state`；由已存在的交付/回执/同步事务负责状态登记。
2. 不应误称旧模板直接把结果设为 accepted：已读代码设置的是 workbook_received/pending 等。问题是它仍是第二条状态写链，缺少当前事务/代际约束。
3. `run_pipeline` 主求解后自动串 analysis 的旧组合 API，不再作为新默认导出/示例入口；旧文档已将其限定为 legacy，应把实际入口和说明也隔离清楚。新 03B 只能在 accepted + Gate=required 后独立生成。
4. `result_io.py` 的动态加载改为可被共享闭包识别的静态导入组织；或不再向新项目复制该动态支持包。保留 workbook_validation 的字段、主键、有限值、残差/质量校验能力，不通过关闭来源门解决模板冲突。
5. 五类 starter 只保存有价值的数学模式与实例化要点，不能把历史 PipelineConfig 骨架当作已经具备 RUN_CONFIG/RECEIPT 1.1 的正式工程。
6. 默认允许自包含入口；确需复用时声明真实 helper 及摘要。不要强制每问复制一大套同名支撑包，也不要为了共享而让所有小问 import 一个有副作用的全局执行脚本。

第 4 点在实施前补一个真实“复制到干净项目→声明 helper→交付→只运行维护微例→回执”的回归，确认具体拒绝路径后再改；本轮只有源码对照结论。

## 8. 历史项目与项目级迁移

### 8.1 不能保留永久双模式

新活动路径不得出现 `allow_stage_override`、`allow_mixed_backend` 或“未填根字段就继续逐问选择”等默认逃生口。否则只是给旧架构加了一层根字段。

旧 1.0/1.1 回执和 per-stage 状态可通过显式历史读取或迁移输入被理解；它们是历史事实，不是当前项目选择的另一 Authority。迁移器应位于清晰边界，完成后只输出新 canonical 状态。不要把 legacy 判断复制到全部消费者。

### 8.2 迁移分类

| 旧项目情况 | 拟定处理 |
|---|---|
| 无数值代码、无后端记录 | 正常作一次项目选择 |
| 所有可信阶段一致为 Python 或 MATLAB | 只可提出一致候选；读取本身不写根策略。确认后迁移，核验合法产物是否可保留 |
| 不同问题/主深化混用 | 保留历史读取；暂停新数值交付，用户确认统一目标后分类迁移，不投票、不按 Q1、不以文件数最多决定 |
| 声明、扩展名、RUN_CONFIG、回执互相冲突 | 先报告来源冲突；不能通过填根字段覆盖冲突证据 |
| 只有 python_version/matlab_version 环境信息 | 不是项目选择证据 |
| 存在旧 `.py` 命名、无新选择记录 | 仅供历史解释，不自动取得新活动资格 |

读取历史报告不等于允许生成新的混合后端结果，也不等于把所有历史工作簿删除。

### 8.3 真正更换已锁后端

同一当前项目不能维持两个 active 数值后端。确需变更时须由用户明确确认项目级迁移：

- 先计算全部受影响问题和 stage，而非只沿 Q1 依赖图传播；后端是项目范围依赖。
- 对需重新实现的主/深化源码、数值结果，以及依赖这些结果的图表和论文片段，按现有 typed stale 合同失效。
- 原始源码和回执作为历史证据保留；不能修改历史回执的 backend 或 validated 哈希。
- 同语言、身份完整且无需改变实现的历史产物是否可保留，逐项核验；不得仅凭“语言相同”直接继承 accepted。
- 更换实现语言本身不进入数学 SIB；若数学模型、算法语义、离散方案或保证也变了，则回到现有语义审查和批准。
- 全局 Python 预处理或未依赖被改数值结果的独立机理图，不因语言字符串变化被无条件删除。

写入采用现有 `project_transaction` 的锁、generation 与候选状态验证。优先由一个项目级协调动作组合已有 `primary_code_changed` / `analysis_code_changed` 及相关失效规则；仅在确有无法表达的项目作用域事实时最小扩展 State Transition Authority。不得凭本计划假装仓库已有 `project_solver_backend_changed` 事件，也不得平行维护第二套状态机。

必须测试事务中验证候选新状态而不是磁盘旧状态，避免“先改选择、后改 stale”的半完成提交。

## 9. 读取和语义恢复的同步修改

新项目后端事实既要进入机器一致性核验，也要让模型在继续 Q2/Q3、跨聊天恢复和接收工作簿时实际读到。

- 框架全局当前口径只记录一次项目后端及决策证据；机器真值仍是 Project State，不从叙述文字推断已验收。
- `reading_policy` 针对模型设计、求解、深化、返回工作簿和相关状态冲突，加入必需的 solver policy 子树或明确依赖。不要为一个字段强制每轮读取整个仓库。
- 删除/改名 MD 标题和 YAML key 后同步 exact selector；保留缺失/歧义时的明确错误或完整读取回退，不能返回空规则并继续交付。
- 读取计划和文件哈希只是导航/身份，不能填成“助手已经读完”。继续保留未实际测得的 reading consumption 指标为空。
- 测试快照与后续 reading_plan 重新读 state 的一致性；发生 generation 变化则重新解析或停止，不混用旧后端与新状态。
- 将 `solver backend`、`figure/rendering backend`、`LaTeX bibliography backend` 的测试和描述分开，避免误删非数值能力。

## 10. 实施文件清单与“不改”清单

### 10.1 必须连贯修改的核心组

| 组 | 文件 | 主要职责 |
|---|---|---|
| 政策 / 数据结构 | user_execution、runtime_assurance、project_state Schema、必要的 state_transition | 唯一选择、无 override、迁移和字段边界 |
| 解析 | runtime_assurance.py、resolve_runtime.py、resolve_workflow.py、stage_code.py | 根策略恢复、全局检查、实际阶段模板和共享绑定 |
| 写入与前提 | validate_code_delivery.py、validate_user_execution.py、validate_project_state.py、analysis_prerequisites.py | 删除反向选择 writer；一致性与证据验收 |
| 下游 | project_snapshot.py、sync_project.py、submission_requirements.py | 正确观察/失效/必需包内容，不回退猜语言 |
| 框架 | model_paper_framework.md、instantiate_model_paper_framework.py、validate_model_paper_framework.py | 全局工程记忆、源码锚点与项目策略上下文 |
| 活动说明 | 第 5 节列出的入口、模块、Pack、模板 README | 删除旧许可并去重复，非同义替换补丁 |
| 支撑模板 | hsk_pipeline/main_pipeline.py、__init__.py、result_io.py、starter 示例 | 移除新默认链中的副作用状态 writer 和动态导入障碍，保留数学与 IO 能力 |
| 读取 / 治理 | workflow_router、module_manifest、reading_plan、lint 与相关测试 | 新策略实际可读，引用完整，字段删除不导致默认路径漂移 |
| 测试 / CI | 第 11 节相关 fixture、专项测试与 native jobs | 正例同后端化，混合行为转负例或历史读取，保留其他防线 |

这是影响面，不要求每个文件机械修改。例：`project_transaction.py` 主要复用现有事务机制，只有证实接口不足才改；`workbook_validation.py` 主要保留业务校验，不为后端政策重写数值表。

### 10.2 明确保留的能力

保留源文件原始字节绑定、项目 helper 摘要、相对导入/父包识别、危险动态引用拒绝、MATLAB fresh batch 与不支持解析的阻断、输入身份、analysis 主簿绑定、主质量证据、条件式深化、跨问依赖、Windows 路径/事务保护、工作簿精确字段、正式图文交接、LaTeX 来源证明和 official allowlist。

不把 `solver_execution` 整个删除：逐阶段 bundle 与验收状态依然必要。也不把 `state.project_state`、workbook Schema、receipt 协议的独立版本号全仓替换成 Skill 版本。

## 11. 未来验收矩阵（本轮均未执行）

每个正式变更必须有对应正/反测试。下表是验收要求，不是已通过结果。

| 组 | 必须覆盖的用例与通过条件 |
|---|---|
| T01 项目选择 | 新项目缺策略不能正式交付；明确候选经过既有批准衔接后一次写入；auto 不可作为已锁值 |
| T02 Schema | 根枚举/理由校验；新状态不接受 stage 选择权；旧状态仅在明确历史入口解释；未知字段不能吞掉 |
| T03 同后端正例 | 一个 Python 项目含 Q1/Q2/required analysis 全通过；另一个 MATLAB 项目同样全通过 |
| T04 跨问负例 | 根 Python + Q2 MATLAB 拒绝；请求 Q1 时也能发现项目范围声明冲突 |
| T05 跨阶段负例 | primary Python + analysis MATLAB 拒绝；不生成另一语言分析模板 |
| T06 恢复 | 跨聊天、只指定 Q3、auto、省略 CLI 参数均继承根选择；不按扩展名或当前选中问重选 |
| T07 请求冲突 | 显式相反 CLI 返回 review_required，state/源码/工作簿字节完全不变，不自动 stale |
| T08 实际恢复阶段 | analysis 因主结果失效回到 primary；模板为同一 B_P 的 primary，不回退成 request stage |
| T09 现代协议 | 删除 stage selector 后仍不能把 1.1/MATLAB 无元数据降级；无 state 的解析成功不等于正式交付成功 |
| T10 交付写权 | 移除从 RUN_CONFIG 自创后端/理由；交付仅更新正确阶段源码/bundle/等待执行状态 |
| T11 回执四方一致 | 项目、源码、RUN_CONFIG、RUN_RECEIPT 任一不一致均拒绝；失败不刷新 validated 身份 |
| T12 原身份防线 | helper 缺失/变化、相对导入、bundle 次序与哈希、输入变化、主簿变化、危险动态引用继续拒绝 |
| T13 历史真实负例 | 保留原 3→6 别名/反射维护微例和旧工作簿拒绝，不把新 policy 缺失变成唯一失败原因从而遮住原漏洞回归 |
| T14 同步 | 无变化不误撤 accepted；观察不重绑定；候选 state 中项目策略和 typed stale 一致 |
| T15 迁移 | 同后端旧项目候选需确认；混合旧项目不投票；不同后端受影响产物和图文下游正确失效 |
| T16 事务 | stale generation、并发修改、验证失败回滚、Windows 文件生命周期，均保持原保护；不存在半切换项目 |
| T17 模板副作用 | 新 Python/MATLAB 数值入口只写约定运行产物，不直接写整个项目状态或批准记录 |
| T18 支撑包闭包 | 真正复制 Python 支撑包到新 1.1 项目，显式 helper + 静态导入可交付；未声明/动态装载不通过 |
| T19 条件深化 | not_required 无 analysis 文件；required 必須独立入口、当前 accepted 主簿；不调用主入口重算伪造主结果 |
| T20 跨问数据 | 同 B_P 的 Q2 合法读取 Q1 当前 accepted 工作簿；不因统一后端丢掉跨问输入支持 |
| T21 预处理与绘图 | 全局 Python 预处理→MATLAB 求解仍有效；Python 求解→正式 MATLAB 绘图仍有效，均不是混合数值后端许可 |
| T22 包验收 | 两种同后端项目完整包通过；缺 helper、错语言入口、缺声明输入拒绝；历史文件不能冒充当前必需入口 |
| T23 精确读取 | 所有改动标题/key 的 read_now/conditional 正确；缺文件、越界、歧义标题、无效编码明确处理 |
| T24 读取快照 | hydration 后 state 变化时重新解析或阻断；不混合旧 B_P 与新 generation；不伪造实际已读指标 |
| T25 图文隔离 | draw.io 后端、颜色配置、LaTeX/bib backend 不受 solver backend 扫描替换影响 |
| T26 框架语义 | 全局后端事实可恢复；纯语言变化不改数学 SIB；真实算法/离散变化仍触发语义审批 |
| T27 文档一致 | 无活动“每问可选/analysis可覆盖/固定Python求解/无条件五文件”许可；允许精确标注的历史说明与职责正确的 Python 文字 |
| T28 native 保留 | Python/Windows/MATLAB 原生同后端交付与回执、SHA 大小写、8.3 路径和 fresh batch 等原场景保留 |
| T29 历史基线 | 对指定不可变基线重新表征；新策略造成的有意差异逐项登记，不能宣称所有历史输出必须逐字相同 |
| T30 全量放行 | 最终完整树运行 lint、完整单测、生成索引、受影响专项/native CI；记录实际数目与跳过理由，不复用旧 SHA 的绿色状态 |

具体测试维护：

- `test_solver_backend_downstream_identity.py` 的 analysis 反语言默认夹具先重构；正例默认同项目策略，负例显式制造冲突。
- runtime_resume/runtime_boundaries 中原来以跨语言作为阶段恢复条件的用例，改成同语言不同阶段，继续检验原修复目标。
- `solver_backend_mixed_smoke.py` 的复用 helper 还被源码引用回归使用；重构前检查所有 imports，不直接删文件导致其他测试丢失。
- `.github/workflows/ci.yml` 保留 native MATLAB 数值任务、Python 版本矩阵、Windows 和 LaTeX；只替换已退役的混合正例语义，不减少必要任务以求变绿。
- 全局 Python 预处理→MATLAB 求解 native 场景与数值跨语言混用区分；不能误删前者。
- 测试若只因“根策略缺失”就提前失败，必须补上正确策略，确认仍实际触发原来的 helper/receipt/数值负例；避免表面通过而原断言被短路。

## 12. 实施顺序、版本和停止条件

### 12.1 顺序

| 阶段 | 交付与退出条件 |
|---|---|
| P0 本轮计划 | 完成固定基线阅读与问题台账，明确未读完；只新增计划，不实现、不合并 |
| P1 补读与定稿 | 补读直接修改面的剩余全文和所有引用；确认预处理/绘图边界、一次选择写入者、历史迁移、版本；用户批准后才写实现 |
| P2 契约与状态设计 | 就地重写唯一政策和新 canonical Schema；同时定义旧输入迁移及当前资格，不开启永久双写 |
| P3 共享实现 | 一处策略解析，接通 runtime/stage/delivery/receipt/snapshot/sync/package；项目事务与实际阶段恢复保持闭合 |
| P4 文档与模板清理 | 执行删除/重写矩阵，剥离支撑模板副作用与动态装载；更新框架、精确读取选择器和实例化路径 |
| P5 回归与 native | 按第 11 节新增/调整测试；补真实支撑包复制链路，保留旧已确认漏洞和平台保护 |
| P6 生成与独立验收 | 运行生成器并单独提交派生文件，核对入口、版本、引用、源码树；在最终 head 跑全部检查 |
| P7 有条件合并 | 仅当另行获得实现/合并授权、无阻断项、最终提交验收通过；合并后主干另行核验 |

P2—P4 可以拆清晰提交供审查，但不能把互相矛盾的半套政策分别合并成可用主干。若跨 PR 分阶段，第一阶段不得对外宣称已经支持新默认语义，也不得留下未约束的阶段 override。

### 12.2 版本裁决

本轮只写 docs，当前 Skill 仍为 9.7.1。

后续若删除当前 stage selector、改变旧 CLI 默认和阻断曾合法的新混合执行，按现有治理属于需要严肃评估的破坏性行为。**倾向按 major 迁移设计清洁目标，但不在此强行冻结发布号。** major 不意味着顺便删除所有历史协议或其他领域兼容，也不授权无关全仓重构。

若坚持 v9.8.0 minor，须具体证明旧接口的受支持兼容边界、当前新项目选择和迁移行为不会造成未声明破坏。不能仅因为“旧文件还能打开”就声称全部向后兼容；也不能为满足 minor 标签而永久双写两个后端来源。

### 12.3 停止条件

遇到下列任一情况不得进入实现完成/合并声明：直接影响文件尚未读完；活动规则同时允许旧混合与新唯一选择；新模板仍可自选后端；新 policy 缺失被解释成 Python；现代协议被降级；原负例被新前置条件短路；候选/主干 SHA 变化未复验；native 未运行却宣称通过；标题删除造成空规则读取；迁移可部分提交；任何未知问题仅用一条“例外”掩盖。

## 13. 本轮交付与后续审议结论

本轮完成的是**有明确阅读边界的仓库审阅计划**，不是“全仓零问题证明”，更不是项目级后端已经实现。全仓逐字未完成的状态保留在文档开头和附录中，不在交付时隐藏。

推荐批准的设计方向：在既有 Authority 中重新定义一次项目选择；新活动状态只保留一个根选择来源；取消逐问/逐阶段 override 和反向选择 writer；保留每问独立代码、条件式分析和实际运行证据；清理重复 MD，而不是叠加更多层。

本轮源码、Schema、模板、测试、版本、用户项目与 main 均不由本计划修改。若仓库自动工作流为文档更新派生索引/哈希，应单独列为生成变更，不把它宣称为实现完成，也不手工修改这些文件。

## 附录 A. 已全文阅读的 106 个文件

以下列表仅表示本轮全文阅读范围，不意味着每个文件都需要修改。

```text
.codex-plugin/plugin.json
.github/pull_request_template.md
.github/workflows/ci.yml
.github/workflows/optimization-baseline.yml
.github/workflows/refresh-generated.yml
AGENTS.md
PROJECT_INSTRUCTIONS.md
README.md
RUNTIME_ROUTER.md
SKILL.md
SKILL_CHANGE_GOVERNANCE.md
agents/openai.yaml
core/bootstrap.yaml
core/code_quality_contract.yaml
core/global_preprocessing_contract.yaml
core/hsk_core_policy.md
core/model_approval_contract.yaml
core/module_manifest.yaml
core/numerical_verification_contract.yaml
core/output_contract.yaml
core/project_state.schema.yaml
core/runtime_assurance_contract.yaml
core/state_transition_contract.yaml
core/task_taxonomy.yaml
core/user_execution_contract.yaml
core/workbook_schema.yaml
core/workflow_router.yaml
docs/v970_solver_backends_migration.md
docs/v971_backend_contract_audit.md
modules/01_problem_audit.md
modules/02_model_design.md
modules/03_data_preprocessing.md
modules/03_result_analysis.md
modules/03_solve_validate.md
modules/04_figure_evidence.md
modules/05_latex_compile_quality.md
modules/05_writing/ai_cleanup.md
modules/05_writing/docx.md
modules/05_writing/latex.md
modules/06_review_delivery.md
packs/artifact/code.md
packs/artifact/figure.md
packs/artifact/full_submission.md
packs/artifact/review.md
scripts/README.md
scripts/analysis_prerequisites.py
scripts/generate_indexes.py
scripts/hsk_pack_submission.py
scripts/instantiate_model_paper_framework.py
scripts/lint_skill.py
scripts/matlab_code_checks.py
scripts/project_snapshot.py
scripts/project_transaction.py
scripts/python_source_checks.py
scripts/reading_plan.py
scripts/resolve_runtime.py
scripts/resolve_workflow.py
scripts/run_config_parser.py
scripts/runtime_assurance.py
scripts/stage_code.py
scripts/state_transitions.py
scripts/submission_requirements.py
scripts/sync_project.py
scripts/validate_code_delivery.py
scripts/validate_model_approval.py
scripts/validate_model_paper_framework.py
scripts/validate_project_state.py
scripts/validate_submission_package.py
scripts/validate_user_execution.py
skills/mathmodel-skill/SKILL.md
state/project_state.example.yaml
templates/code/hsk_pipeline/README.md
templates/code/hsk_pipeline/__init__.py
templates/code/hsk_pipeline/main_pipeline.py
templates/code/hsk_pipeline/result_io.py
templates/code/hsk_pipeline/workbook_validation.py
templates/code/matlab/README.md
templates/code/matlab/q1_analysis.m
templates/code/matlab/q1_solver.m
templates/code/starter/README.md
templates/code/starter/classification.py
templates/code/starter/evaluation.py
templates/code/starter/optimization.py
templates/code/starter/prediction.py
templates/code/starter/simulation.py
templates/model/model_approval_section.md
templates/model/model_paper_framework.md
templates/writing/code_appendix_description.md
tests/fixtures/solver_backends/python_primary.py
tests/matlab/run_solver_backend_mixed_smoke.m
tests/matlab/run_solver_backend_smoke.m
tests/solver_backend_hash_smoke.py
tests/solver_backend_mixed_smoke.py
tests/test_python_execution_reference_closure.py
tests/test_python_matlab_ownership.py
tests/test_python_reference_followup.py
tests/test_solver_backend_contract_alignment.py
tests/test_solver_backend_downstream_identity.py
tests/test_solver_backend_end_to_end.py
tests/test_solver_backend_integration.py
tests/test_solver_backend_legacy_evidence.py
tests/test_solver_backend_preprocessing.py
tests/test_solver_backend_runtime_boundaries.py
tests/test_solver_backend_runtime_resume.py
tests/test_solver_backend_source_closure.py
tests/test_solver_backends.py
```

部分阅读两个文件的剩余范围不能标成已读：CHANGELOG 95—639；lint_skill_checks 1—789、861—1294、1416—1443。其他 426 个文本仅清单/主题扫描，15 个二进制未内容审读。某些按猜测大小写/路径发起的本地展开曾失败，已按清单纠正后重读；过长展开也已拆分，失败调用没有记入全文覆盖。

## 附录 B. 固定版本源码定位

正文中的其他源文件行号也全部绑定于同一提交。下列重点链接用于核对核心事实；未来实施后不能拿新的行号解释这里的旧版本证据。

[S01]: https://github.com/Vexushi1/mathmodel-skill/blob/34deb02ff590d061fc7ca36f9bd2742a6653c797/core/user_execution_contract.yaml#L6-L35
[S02]: https://github.com/Vexushi1/mathmodel-skill/blob/34deb02ff590d061fc7ca36f9bd2742a6653c797/core/runtime_assurance_contract.yaml
[S03]: https://github.com/Vexushi1/mathmodel-skill/blob/34deb02ff590d061fc7ca36f9bd2742a6653c797/scripts/validate_code_delivery.py#L631-L706
[S04]: https://github.com/Vexushi1/mathmodel-skill/blob/34deb02ff590d061fc7ca36f9bd2742a6653c797/agents/openai.yaml#L1-L9
[S05]: https://github.com/Vexushi1/mathmodel-skill/blob/34deb02ff590d061fc7ca36f9bd2742a6653c797/README.md#L536-L625
[S06]: https://github.com/Vexushi1/mathmodel-skill/blob/34deb02ff590d061fc7ca36f9bd2742a6653c797/core/workflow_router.yaml#L430-L434
[S07]: https://github.com/Vexushi1/mathmodel-skill/blob/34deb02ff590d061fc7ca36f9bd2742a6653c797/templates/code/hsk_pipeline/main_pipeline.py#L306-L348
[S08]: https://github.com/Vexushi1/mathmodel-skill/blob/34deb02ff590d061fc7ca36f9bd2742a6653c797/templates/code/hsk_pipeline/result_io.py#L13-L26
