# 数学建模 Skill 11.0.0 重构实施计划

**待审批 · 2026-11-20。** 行为基线为 [v10.35.3 的固定提交](https://github.com/Vexushi1/mathmodel-skill/tree/4f765d3e1326d3ca7555933059e9313f99b86347)。本 PR 的交付物是一份维护计划，变更等级为 `docs`。以下工作包是拟议的 `major` 升级，当前发行和比赛项目仍使用各自已固定的规则。

**阅读顺序**　先看第 1 节判断使用体验，第 2 节了解现有调用关系，第 3 节逐文件审改法，第 4 节审批实施顺序和兼容窗口。

## 1. 审批摘要

用户在网页和 App 里应能说“把题读完，先给我建模方案”，随后直接看到逐问题意、附件口径和模型选择理由。助手负责找规则、补缺和定位项目证据。用户仍负责批准当前模型、实际运行题目数值代码并返回产物。日常使用无须安装本地 Codex、运行仓库检查、确认每章已读或逐图批准放置位置。正常情况下只简短交代当前小问和结果；出现缺口才说明缺哪份材料、影响哪项结论，以及还能推进什么。

| 用户的实际动作 | 11.0.0 拟提供的体验 | 怎样判断改好了 |
|---|---|---|
| 发题或继续一项正式建模任务 | 固定项目版本，开场取得全部现行规范正文，再进入审题。 | 首次审题能落实题面末页限制、附件单位和跨问依赖；可定位确实取齐的正文和缺块。 |
| 换问、换章、新图设计；或换会话回来 | 同一连续任务重取当前动作完整原文与证据。跨会话、只余摘要或已丢失整体规则范围时重建整套覆盖。 | 同版本、同哈希也会按场景重取；不会要求用户复述批准状态、数值或阅读清单。 |
| 一句话同时要机理图和误差图 | 分别取得机理图和数据图的依据，按各自条件推进。 | 有模型而缺已验收工作簿时，可以做有依据的机理图；待工作簿验收后再生成误差图及其数值解读。 |
| 只查某字段、改已定型图的配色，或做维护咨询 | 直接完成所请求范围。如果升级成正式建模，由助手自动补齐开场。 | 局部动作不会让用户等一遍整仓读取；改变单位、数据或结论时能识别范围已扩大。 |

建议审批三件事：采用正式任务全文启动；让阶段读取、项目证据和业务批准继续各有明确职责；将生产默认的一次切换安排在网页、原生 App 和远端仓库验收之后。批准本计划可以授权分支实施，具体比赛项目的模型批准、历史项目迁移和正式发行分别依其条件办理。

## 2. 现有结构与调用关系

固定树共有 **805** 个文件。前序审查取得并核对了全部 **789** 份文本，合计 11,044,557 字节、194,043 行；另有 15 张视觉参考图和 1 个含 11 个成员的合成测试 ZIP。重点精读的是合同、调用链、相关实现、测试和治理文档。完整取回不等同于对每句历史文字作语义裁决。下面的分组覆盖全部 805 项；各目录的职能决定修改位置。

| 位置 / 文件数 | 当前职责 | 实施时由谁消费 |
|---|---|---|
| 根目录 21，`.codex-plugin/`、`agents/`、`skills/` 各 1 | 仓库说明、入口、发布、索引、治理与兼容指针；两份 SKILL 是受版本控制的入口。 | 网页/App 项目指令、插件发现、仓库维护。 |
| `core/` 26 | 启动、路由、全局政策、领域合同、状态与工作簿 schema、运行保障、写作时序及生成导航。 | 解析器、验证器、业务模块。 |
| `modules/` 16，`packs/` 27 | 从审题到交付的业务正文、专题规则、竞赛差异、证明与算法呈现。 | 对应阶段和已激活分支。 |
| `templates/` 90，`config/` 3，`state/` 1 | 代码/工作簿、图表、论文载体、验证模板、赛事配置、项目状态示例。部分模板包含唯一行为定义。 | Python/MATLAB、文稿装配和项目初始化。 |
| `scripts/` 79 | 业务路由、取源、同步、数值证据检查、文章审计、打包、索引生成。 | 助手具备执行条件时使用；仓库维护由 GitHub Actions 验收。 |
| `tests/` 323，`.github/` 4 | 行为测试、反例、合成项目、性能证据、PR 模板与三个工作流。 | 开发专项、候选冻结、合并后复核。 |
| `docs/` 94，`legacy/` 94 | 设计、迁移、维护记录及归档。有当前合同引用的迁移文档，也有已被替代的旧默认。 | 维护与显式兼容读取；旧约束的效力须回查当前权威。 |
| `knowledge/` 7，`assets/` 17 | 案例、检索登记、图示及其使用条件。 | 规范性的使用条件进入规则目录；示例按具体需求调用。 |

**当前真实调用路径。** 根或插件入口 → `core/bootstrap.yaml` → `core/workflow_router.yaml` 的默认全局政策。有完整资源根、依赖及项目材料时，`scripts/resolve_runtime.py` 先调用 `scripts/resolve_workflow.py` 中的基础路由，再加入项目状态、当前等待点、有序门禁与 `build_reading_plan()`。有实际计划和正确 Git HEAD 时，`scripts/read_stage.py` 按指定来源返回一块正文。只有 GitHub 读权限时，生成的 `core/stage_reading_guide.md` 导航到原文。现在网页用户复制的指令位于一份历史计划 §13.2，README、项目说明和脚本说明均指向那里。[启动入口](../SKILL.md) · [运行时](../scripts/resolve_runtime.py) · [阶段读取器](../scripts/read_stage.py) · [现有可复制指令](stage_reading_execution_refactor_plan.md#132-可复制正文)

**目标调用路径。** 入口先区分正式任务与范围明确的局部任务。正式任务固定版本后，先从该版本的规则目录取得全部规范正文。开始业务动作后，现有路由继续根据项目事实决定“小问、动作、所需证据、允许推进到哪里”。阶段原文、结果与检查分别回到所属源。全文启动只授予阅读覆盖，不授予模型批准、数值验收或正式交付资格。

**四类资料分开处理。** 跨项目规则在仓库权威文档。具体项目语义在当前 `模型论文框架.md`，身份、用户批准和 stale 在项目的 `state/project_state.yaml`，具体数值在 accepted 工作簿。空白模板和仓库内的状态示例只用作结构依据。恢复、全文写作、跨问综合和终审读取完整当前框架；普通单问按范围取读。尚无框架时，由业务阶段决定何时建立。

### 已复现的四个基线反例

| 实际测试 | 当前结果 | 影响边界 |
|---|---|---|
| 有当前框架的合成项目请求全文终审 | 初始 `review` 读集缺整份框架，路由的 `full_read_when` 已要求终审全读。 | 是初读缺口，不能推出最终终审必然放行。 |
| 同一问要机理图和误差分布图 | 单独要误差图会选结果图合同；混合时进入 `mechanism`，该例初读及条件清单均缺结果图合同。 | 两项用户意图被一个分支覆盖。 |
| 给覆盖函数两份同为两行的文本，第二份末行少半句话 | 两份均得到 `complete=True`。正常本地提取还有 Git 源字节核对。 | 接收端的行范围检查漏掉行内损失。 |
| 普通敏感性方法设计了 a、b 两个实验，明细只回传 a | 工作簿结构接口正常返回；它检查所选普通方法至少有一条实质记录。 | 不能仅凭此接口认定 b 已验收，或认定完整项目实际会通过。 |

前序固定版本四个读取专项在 Linux Python 3.12.14 上共 77 项成功，是基线诊断。现有生产测试与新增反例应并行保留。正式 Windows、MATLAB、LaTeX 及候选版本两端体验需在对应提交上再验。[阅读范围选择](../scripts/reading_plan.py#L631-L670) · [分块覆盖](../scripts/reading_plan.py#L48-L181) · [普通证据表校验](../templates/code/hsk_pipeline/workbook_validation.py#L249-L275)

## 3. 逐文件实施表

下表描述**未来实施分支**。同一行的文件负责同一次变更。标明“只回归”的文件仅检查既有行为；标明“条件改”的文件必须先出现表中条件。审批本文件不会立即开始改动这些源码。

### P1　先定规范范围及反例基线

| 文件及处理 | 具体动作 | 完成证据 |
|---|---|---|
| 拟新增维护文档 `docs/v11_rule_preservation_map.md` | 按“旧位置与父级条件 → 新权威 → 谁调用 → 正例/反例”登记拟合并和搬迁条文；对保持原位的规则按来源及连续范围登记。分类覆盖全树，追查跨文件引用、模板或代码中唯一的规则。 | 每个规范来源有去向。每个被删句子的单位、阈值、例外、作用范围和等待点都有明确保留或经批准变更的依据。 |
| `core/module_manifest.yaml`、`core/bootstrap.yaml`、`core/task_taxonomy.yaml`、`config/competition_profiles.yaml`、`assets/figure_assets.yaml`、`knowledge/case_memory/schema.yaml`（本步核对） | 将现有登记与实际模块、模板、配置和程序逐项交叉检查。不能用旧解析器返回的集合自证没有漏源。 | 例如绘图资产的使用条件入范围，15 张示例图作为素材；一份 docs 里的当前迁移约定追到其真实消费者。 |
| 拟新增 `tests/fixtures/v11_web_app_cases.yaml` | 固定小题、末页限制、表头单位、项目快照、已有批准和停止点，登记独立参考答案和评分项目。候选运行时不读答案。 | 三个对照组用相同材料。建立正式/局部/恢复/图文/终审各场景的旧版行为和操作数。 |

规则保全有两个最低反例。主结果通过数值检查，但新增“换参数仍稳健”的结论时，需深化证据或收窄结论。项目级预处理已覆盖的原始附件禁止重复读取，确属独立且符合回执协议的辅助附件仍可读取。若合并后的规则会让这两组情况得到相同处置，退回该次合并。[深化判定](../modules/03_result_analysis.md) · [执行合同](../core/user_execution_contract.yaml)

### P2　让网页、App 与插件共用一个启动说明

| 文件及处理 | 具体改动 | 用户看见的效果 / 验收 |
|---|---|---|
| `core/bootstrap.yaml`、`core/hsk_core_policy.md`（改） | bootstrap 定义正式全文、局部、恢复和能力不足的入口；全局政策明确阶段缩读的边界，继续委托原业务合同。 | “开新题”和“解释字段”进入相应范围；不会要求先交赛事专属模板才能审题。 |
| `SKILL.md`、`skills/mathmodel-skill/SKILL.md`（两份同步改），`agents/openai.yaml`、`.codex-plugin/plugin.json`、`AGENTS.md`（改入口描述） | 清掉与新默认冲突的“只加载路由返回内容”指令，保留双入口根目录解析、平台优先级和维护入口。两份 SKILL 仍需原始字节一致。 | 同一版本从根、插件、项目指令进来的首次正式动作一致。 |
| `PROJECT_INSTRUCTIONS.md`（改，作为网页/App 唯一可复制正文），`README.md`、`scripts/README.md`、`RUNTIME_ROUTER.md`、`REPOSITORY_INDEX.md`（改导航），`docs/stage_reading_execution_refactor_plan.md`（改 §13.2 的当前导航） | 设固定锚点 `web-app-start`，给出一段短指令和已保存旧指令的一次性替换说明；保留历史 commit 的旧说明。CLI 用法下沉到脚本说明。 | 新用户从 README 一次找到入口。已有项目继续原固定版本；主动升级的人知道旧指令不会被远端自动改写。 |
| `tests/test_v752_entrypoint_parity.py`、`tests/test_v802_entrypoint_surface_slimming.py`、`tests/test_audit_a7_entry_consistency.py`、`scripts/lint_skill_checks.py`（按新双入口边界改断言） | 对正式与局部各测一次，继续验证字节一致、资源根、唯一可复制入口和单一权威。 | 任一入口仍引导正式任务按需开工、或两个入口内容漂移，检查能指出位置。 |

### P3　让助手拿到正文，并能找回漏掉的内容

| 文件及处理 | 具体改动 | 验收 |
|---|---|---|
| `core/module_manifest.yaml`（改登记），`core/runtime_assurance_contract.yaml`（改读取协议） | 前者登记全文成员职责与物理别名；后者定义版本、来源、块范围、缺口、重取触发和证据强度。前言、父级适用条件和例外与正文一起投递。 | 新增未归类的规范会在构建时暴露；规范清单的预期来源可独立核对。 |
| 拟新增内部模块 `scripts/rule_corpus.py`，改 `scripts/generate_indexes.py` | 从同一组声明构建稳定顺序的阅读卷、源到卷的定位和分块摘要。建议生成 `core/full_reading/manifest.json` 与 `core/full_reading/volumes/NNN.md`，其中 NNN 为确定性卷号。按实测传输能力定卷，不预设全仓文件数为规则数。 | 原文逐段可定位、跨卷可重建。旧卷退出后删除过期生成件。清单不把自己或派生阅读卷再次当规范，也不嵌入包含自身的未来提交 SHA。 |
| `scripts/reading_plan.py`、`scripts/read_stage.py`（改），`scripts/resolve_runtime.py`（接线） | 复用 SourceReader 与区间整理，增加独立于业务计划的正式开场读取模式。原阶段 CLI 的参数、失败语义及输出兼容。接收端与从固定源独立取得的预期原始字节摘要比对；Git blob、分发清单的换行归一化和实际返回字节分别标记。 | 同长度改字、末行缺字、整卷缺失、错提交、重复返回、超长中文行和中断续取均有结果。重复请求幂等，不能用同一份已截短响应自行生成“预期”。 |
| `scripts/resolve_workflow.py`（只回归；只有抽出共享基础逻辑时才移动实现） | 保留旧 CLI 和现有调用者。现有 assured resolver 仍负责编排真实业务门；GitHub 只读入口按固定源取得正文。 | 无执行工具时只报告可见范围。可验证字节、当前上下文实际可见、不可观测的平台内部保留、业务验收分别记录。 |
| `.github/workflows/refresh-generated.yml`、`.github/workflows/ci.yml`（改），`.github/workflows/optimization-baseline.yml`（条件改） | 前者扩充忽略路径、生成差异检测和 bot 暂存；CI 同步扩充生成件上传、差异及未跟踪文件检查。性能工作流仅在新文件应触发既有性能检查而路径未覆盖时调整。 | bot 提交范围仅含预期生成物；新卷、卷减少、空差异、陈旧卷分别验证。 |
| 生成件 `core/stage_reading_guide.md`、`SKILL_FILE_INDEX.md`、`TEMPLATE_INDEX.md`、`MANIFEST.sha256` 及相应兼容指针（由 bot 按真实差异更新） | 旧导航指向新入口和相应阶段原文。完整性清单与规范清单分工，保留原有分发摘要算法。 | 本地或网页手写摘要不能替代远端生成。 |
| 拟新增 `tests/test_rule_corpus.py`；改 `tests/test_read_stage.py`、`tests/test_reading_plan.py`、`tests/test_stage_reading_lifecycle.py`、`tests/test_stage_reading_guide_lifecycle.py`、`tests/test_generated_workflow_hardening.py` | 复用原测试工程，覆盖上述正反例、固定 Git 身份、旧项目来源快照和两种入口。 | 缺块会指明缺哪一段；错误内容不会因行数一致而认定完整。 |

**取不到怎么办。** 清单与正文都绑定同一提交。能定位缺口则只补缺块；当前规则全貌已丢失则重建全套。续传状态只用于诊断，跨会话不据此直接继承“已读”；项目批准和数值另按事实源恢复。若目标端有持续容量限制，说明受影响动作，继续可独立完成的已授权工作。容量不足时以来源去重、分卷和复测改善能力。同一失败循环不会成为用户的新操作。

### P4　把项目证据接回图表、写作和终审

| 文件及处理 | 具体改动 | 验收 |
|---|---|---|
| `core/workflow_router.yaml`、`scripts/reading_plan.py`（改） | 将现有 `project_memory_contract.full_read_when` 接入实际项目读取。拆开仅表示“整套路由资源”的 full 与“完整当前框架”。图形请求保留多项交付意图，分别合并所需原文，按动作核对证据资格。 | 全文终审拿到完整框架。局部评阅范围仍有限。混合图得到两套合同，缺结果证据不会连带阻断可成立的机理图。 |
| `core/writing_runtime_contract.yaml`、`scripts/resolve_runtime.py`（改）；`modules/05_writing/paper_writing_protocol.md`（只回归，若需改唯一图文交接规则才改） | 区分开场预读、每章取回本章原文、允许写作三个时点。每问前盘点预登记图表及可能为空的放置位置，按实际骨架写入并回填引用。共用逐问论证步骤只定义一次。 | 未完成前一问的必要证据时不预写下一问结论。已有图表不漏、计划图不冒充成图、无图题也能完成论证。 |
| `config/competition_profiles.yaml`、`templates/latex/cumcm/hsk/template_manifest.yaml`（条件改） | 当实际文件槽位还绑在通用步骤里，将映射放回对应赛事的载体配置；尽量复用现有键。 | 国赛保留既有实际装配顺序，认证杯无专属模板时回到通用论证，国际赛与显式 DOCX 分支不受国赛物理路径约束。 |
| `modules/04_figure_evidence.md`、`templates/figure/mechanism_contract.md`、`templates/figure/result_figure_contract.md`、`modules/05_latex_compile_quality.md`、`modules/06_review/final_delivery.md`、`templates/review/final_review_matrix.yaml`（只回归） | 现行文件已定义图类、证据、编译与逐页审查。使用它们校验新调用链是否消费了真正的要求。 | 结果图只用当前 accepted 来源；机理图核对关系及渲染。05D 由助手查看相同哈希的 PDF 全部页面。换 PDF 后旧覆盖失效，缺页明确登记。 |
| `tests/test_reading_plan.py`、`tests/test_framework_project_memory_contract.py`、`tests/test_v800_writing_runtime.py`、`tests/test_v870_question_writing_capability_preflight.py`、`tests/test_v810_cross_file_chapter_handoff.py`、`tests/test_v900_phase_g_competition_runtime.py`（增补或回归） | 对真实解析入口、当前项目和组装后的正文做行为断言。 | 新增场景覆盖终审/局审、两图/单图、恢复/单问、国赛/认证杯、图引用与实际文件。 |

**独立子项 P4b：同一方法里的多个承诺实验。** 单独一个功能 PR，可与读取重构并行。新格式优先复用已交付分析代码中可静态读取且与源代码摘要绑定的配置，冻结“本问须做哪些检验”。工作簿记录设计、观测和处置，通过检验 ID 关联。一个实验可以有多行观测；零、False 和真实否定都是结果。每个必需 ID 都要有设计、实质观测、对应主张及其 support / modify / reject 处置。缺任一环都列出该 ID 和缺项。探索项或技术失败保留真实状态，不能充作验证完成。运行后删掉设计行和观测行，仍能从运行前配置发现缺失。

| 文件及处理 | 具体改动与资格 |
|---|---|
| `modules/03_result_analysis.md`、`core/workbook_schema.yaml`（改业务定义）；`core/user_execution_contract.yaml`（为新绑定协议改相应条款） | 只覆盖已激活、已承诺的普通深化实验。运行前定义检验 ID 和目标，返回表记录证据与处置，写清版本适用范围。现有专用多模型/多算法比较继续沿用本身协议。 |
| `scripts/validate_code_delivery.py`、`scripts/validate_user_execution.py`（改交付与验收） | 交付时静态验证必需集合，返回时从已交付且身份匹配的来源恢复预期，核对缺失 ID 及受影响主张。验证时不执行赛题脚本。 |
| `templates/code/hsk_pipeline/workbook_validation.py`、`templates/code/hsk_pipeline/result_io.py`（改读写及独立运行的 schema 回退）；`templates/code/matlab/q1_analysis.m`（按该模板是否生产新协议字段相应更新） | 预期与实际逐项连接，验证一个 ID 多条观测的正常情况；写入、读回、孤立目录及两种后端一致。现有分析设计/汇总可以复用已定义的可选检验 ID。 |
| `scripts/execution_protocol.py`（新协议改变版本/字段组合时改）；`scripts/run_config_parser.py`、`scripts/matlab_code_checks.py`（回归） | 在现有协议分派处注册新组合，分别验证 Python 与 MATLAB 能从已交付源码静态还原预期检验集合；缺能力的入口保留待验资格。 |
| `scripts/analysis_prerequisites.py`、`scripts/analysis_comparison_gate.py`（只回归），`core/project_state.schema.yaml`（条件改） | 同一路径、同一既有已验收摘要的历史记录保持只读。只有源绑定的运行前配置无法为两种后端提供一致身份时，才提单独的 schema 变更和迁移简报。旧项目新提稳健性主张时核验证据；不凭文本相似或行号推断历史匹配。 |
| `tests/test_result_io.py`、`tests/test_user_execution_contract.py`、`tests/test_analysis_comparison_integration.py`、`tests/test_p5a_run_config.py`、`tests/test_matlab_code_checks.py`（测试） | 同方法含 a、b 而只返回 a 应报缺 b；同时删除 b 的设计和明细仍能发现；a、b 均有数但 b 无处置时报告处置缺失；同一实验多行、有效零值、未激活 03B、旧项目只读和专用比较需分别通过原有适用检验。 |

**只回归的数模硬边界。** 使用 `modules/01_problem_audit.md`、`modules/02_model_design.md`、`core/model_approval_contract.yaml`、`core/model_code_conformance_contract.yaml`、`modules/03_solve_validate.md` 和 `core/state_transition_contract.yaml` 检验全文预读之后的实际行为。审题仍要冻结对象、约束、输出与依赖；两个候选路线可以各自比较适配性，其中一条可以被否决。正式建模保留一个最小充分主模型、独立双审与用户对当前身份的明确批准。求解后端由项目选择，项目级预处理沿用 Python，绘图后端独立。助手生成、静态检查和验收，用户运行完整精度的赛题代码。任何正式门仍只按该次 resolver 返回的顺序和资格执行。

### P5　旧项目与版本迁移

| 文件及处理 | 做什么 | 验收 |
|---|---|---|
| `SKILL_CHANGE_GOVERNANCE.md`（先审适用范围），`assets/figure_assets.yaml`、`core/code_quality_contract.yaml`、`core/global_preprocessing_contract.yaml`、`core/numerical_verification_contract.yaml`、`core/runtime_assurance_contract.yaml`、`core/task_taxonomy.yaml`、`core/user_execution_contract.yaml`、`core/workbook_schema.yaml`（逐项续定适用范围） | 九处现行上界都排除 11.0.0。先按有效治理审查治理自身的续期，再按各合同实测兼容性决定新范围及例外。 | 九处均有依据；工作簿、状态、执行、回执只在格式或语义真的改变时升各自协议号。 |
| 正式切换的 12 个版本载体：`core/bootstrap.yaml`、`.codex-plugin/plugin.json`、`core/workflow_router.yaml`、`core/module_manifest.yaml`、`core/output_contract.yaml`、`core/writing_runtime_contract.yaml`、`config/prose_audit_patterns.yaml`、两份 `SKILL.md`、`README.md`、`CHANGELOG.md`、`core/hsk_core_policy.md` | 候选阶段把切换和版本改动隔离，发行提交一次对齐。以 `tests/test_v1000_release_version_matrix.py` 的载体表与独立协议表核对，并复查 `scripts/lint_skill_checks.py`。 | 旧的状态 8.16.0、工作簿 2.4.0、执行合同 3.3.0 等不用新 Skill 版本号覆盖；确需升级者有具体兼容路径。 |
| 拟新增 `docs/v11_0_0_migration.md`；只读参考 `docs/v900_migration_contract.md`、`docs/v10_32_0_release_notes.md` | 给出正在做的 10.x 项目、历史只读项目、新项目三种操作方式。说明如何识别实际使用的固定提交、更换旧项目指令、恢复旧入口及数据快照。 | 演练迁移、失败恢复和重复进入。历史文本哈希不能升级为有效批准；未变化且证据仍有效的独立小问不会被无差别作废。 |

**兼容窗口建议。** 整个 11.x 保留承诺的旧 CLI、旧固定来源用法和只读适配。新建项目在正式切换后采用 11.0 默认。进行中的旧项目继续使用原固定版本；经项目所有人选择升级，先预览、保全原始状态与产物，再按契约处理真正受影响的依赖。下一个主版本才评估兼容层退出，依据是已知消费者、迁移回归和单独的移除决定。

### P6　按网页和原生 App 的表现决定是否切换

相同题包做三组：A 用 v10.35.3 原按需路径，B 在相同旧版正文上显式强制全文，C 用 11.0 候选入口。网页和原生 App 分开记录版本、设置、项目快照、工具能力、等待点与输出。测试由实施侧组织；没有可用的真实原生 App 会话时，保留其未测状态。手机尺寸网页和 CI 不能代替该项。

| 场景 | 预期证据 / 判定 |
|---|---|
| 无模板新题、题面末页有精度限制，工作簿表头标分钟，第二问依赖第一问 | 逐问将硬要求定位到页段/字段、单位、约束和交付位置；可从条件消元时说明推导。既无题面也无官方依据的赛事要求不得升为硬门。 |
| 模型批准与程序 | 给出目标方向写反、索引错位、漏一条约束的小例。参考答案由独立人或独立评阅步骤在运行前冻结。比较代码入口与数学小例，未批准处保持停止；静态通过不能代替数学等价证明。 |
| 只改配色、局部咨询扩大到正式任务、中途只剩摘要 | 局部请求操作数低；扩范围或丢全貌时主动重建全文，当前版本、批准与数值均从对应源重取。对已知缺块只补相应原文。 |
| 两类图同问、晚插入图表、认证杯写作、替换了最终 PDF | 机理与工作簿证据各归其位，正文按实际位置回填；结论有证据；同一哈希的 PDF 由助手逐页看完并记录页范围。 |
| 一个方法两个实验，或者旧项目只有旧哈希 | 报告缺失实验及其影响；保留能独立成立的结果。旧哈希保持历史身份，不授权新代码。 |

**比较方法。** 每个适用场景在各端重复，同一场景用同等重复次数；题包、材料、允许用户交互与评判项预先冻结。分别列出命中的硬条件数/总数、关键错误发现数/植入数、首次正确审题时间、恢复后首次正确动作时间、实际取回字节、尝试次数和额外用户操作。记录重复结果的离散和失败案例。耗时预算在 A/B 基线可测后、看 C 结果前冻结。对硬约束遗漏、虚构批准或数值、擅自运行用户代码、未看全页却报通过，发布容许数为零。C 每个关键场景须达到旧全文组的有效覆盖，并满足独立题面标准。若质量或容量不合格，修正正文归属或投递方式后重跑对应场景。仓库不保证宿主内部 Token 保留情况或自动记忆跨会话。

## 4. 工作顺序、治理与回滚

**候选与生产的分界。** P2–P5 中会改变默认行为的提交投向同一候选集成分支，网页和 App 试用都显式固定候选提交。可独立合入 main 的准备项仅限保持旧默认的文档、测试和未激活能力。P6 验收通过后才将新入口与 11.0.0 版本载体一次切入 main。

| 里程碑 | 前置 | 本阶段结束时维护者拿到什么 |
|---|---|---|
| P1 范围和基线 | 设计获批 | 全树角色、逐条迁移去向、已冻结的题包与基线限制。未解释的独有规则继续保留。 |
| P2 入口归一 | P1 定义明确 | 可复制的稳定入口、旧路径升级说明、入口一致性测试。 |
| P3 正文投递 | P1 完成，P2 的入口约定已定 | 来源清单、分卷、接收端校验、故障重取、真实网页取回证据。 |
| P4 阶段接线 | P2，及 P3 可用的读取接口 | 终审完整框架、混合图两套来源、逐问图文引用；P4b 独立交付逐实验验收证据。 |
| P5 迁移与候选 | 受影响的合同已定 | 兼容矩阵、旧项目恢复演练与候选发布说明。 |
| P6 默认为新架构 | P1–P5 有证据 | A/B/C 两端报告、最终 PR head 的远端正式验收、合并后 main 复核，以及发行决策。 |

**分支与重叠。** [#335](https://github.com/Vexushi1/mathmodel-skill/pull/335) 提供全文启动的架构草案，当前 diff 为计划及两份生成件；[#326](https://github.com/Vexushi1/mathmodel-skill/pull/326) 提供问题范围与数值验收的旧计划。v10.32.1–10.35.3 已实现的事项进入非退化回归，P4b 只处理尚存的逐实验缺口。本文件是文件级实施清单。后续各工作包从届时已核实的主干或经批准的集成分支串行衔接，同一权威文件有重叠时先处理基础变更，再重基、重新生成和验收。生产默认在准入之后一次切换。

**仓库交付。** 各 PR 附修改简报、文件清单与验收，超过 20 个活动文件时解释分组、不可拆的原因。人工提交源文件，GitHub 的 refresh-generated 生成受管文件。草稿用相应专项；冻结后的实际最终 head 接受 Windows Python 3.10/3.14 各四分片和汇总、静态合同、生成件、MATLAB 原生、LaTeX 模板与生产证明及适用的性能检查。合并后再核对 main；正式发行需将标签固定到最终已验收提交。比赛项目的交付仍服从其当次 resolver 的门序。[治理流程](../SKILL_CHANGE_GOVERNANCE.md) · [远端生成](../.github/workflows/refresh-generated.yml) · [正式 CI](../.github/workflows/ci.yml)

**回滚。** 候选阶段可逐个撤回未通过的工作包并保留旧默认。正式切换有问题时恢复切换前已验收的入口和固定提交；计划比较基线为 v10.35.3。若实施前主干前进，发布说明同时记录那个实际回滚 SHA。上一正式 Release v10.32.0 与当前基线相距 40 个提交、8 次主线合并，需避免连带撤销其间改进。已写新协议的具体项目使用迁移前快照恢复并核对实际证据，已发行的标签保持可追溯。

**本次审批点。** 是否按 P1–P6 推进，以及是否接受整个 11.x 的旧项目只读和旧 CLI 兼容窗口。批准后首先提交 P1 的规则去向和冻结的场景；网页/App 使用效果、实现测试和发行资格以届时的真实成果分别验收。
