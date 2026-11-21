# 11.0.0 重构前的规则来源与保全映射

基线为 v10.35.3，提交 `4f765d3e1326d3ca7555933059e9313f99b86347`，Git 树 `40078ae3c017a4ee3b52a9ef8ce4c82a641e37d7`。本表供维护者在移动规则、变更入口和核查遗漏时使用。正式任务的读取清单、gate 顺序及项目批准仍由相应运行合同提供。[固定基线](https://github.com/Vexushi1/mathmodel-skill/tree/4f765d3e1326d3ca7555933059e9313f99b86347) · [获准实施的计划](https://github.com/Vexushi1/mathmodel-skill/pull/336)

## 固定树的每项如何处置

以下第一列只匹配该提交的 Git 路径，大小写敏感，每格用空格分隔多个选择式，按表从上到下首次命中。星号可跨目录，含义同 Python 标准库 `fnmatchcase`。计数为去除前面已命中项后的文件数。全集为 `git ls-tree -r --name-only 4f765d3e1326d3ca7555933059e9313f99b86347` 的 805 项，含 789 份文本、15 张 PNG 与 1 个测试 ZIP。在新提交评估增删项时，先与此树作差，逐一判断新增文件，避免通过已有通配式自动承认新来源。

“原位”表示旧路径的连续范围从第一行到 EOF，含前言、父级作用域、数据字段、阈值与例外，后续仍以该路径承载。只在明确登记了迁移或替换的范围内改变去向。表中的正反对照列给出审改时应验证的行为，本表不记录任何比赛项目的通过状态。

| 路径选择式（依次匹配） | 文件数 | 原文去向与消费者 | 可分辨的结果 |
|---|---:|---|---|
| `SKILL.md skills/mathmodel-skill/SKILL.md` | 2 | 双入口镜像。取原字节，别名计一次正文。P2 同步修改委托和触发条件。 | 同一正式任务由两入口获得同一范围。 |
| `core/bootstrap.yaml core/hsk_core_policy.md core/workflow_router.yaml core/runtime_assurance_contract.yaml` | 4 | 原位。P2/P3/P4 仅改开场、正文取回和相应接线，见下表。 | 局部色彩修改无需启动整题。待批准任务全读后仍在等待。 |
| `core/module_manifest.yaml core/task_taxonomy.yaml` | 2 | 原位。模块输入输出/工具门契约与每问分类分别保留。 | 流程别名、旧题型标签不得升级为当前路径或批准。 |
| `core/project_state.schema.yaml core/state_transition_contract.yaml core/model_approval_contract.yaml` | 3 | 原位。状态结构、typed stale、双审和批准各有所有者。 | 上游目标变化影响依赖题。纯排版与无关小问分开。 |
| `core/output_contract.yaml core/global_preprocessing_contract.yaml core/user_execution_contract.yaml core/workbook_schema.yaml core/numerical_verification_contract.yaml core/code_quality_contract.yaml` | 6 | 原位。产物、源选择、执行所有权、表结构、质量和静态交付分别保留。 | 主结果合格与稳健性证明分开。独立辅助输入与重复使用已覆盖原始数据分开。 |
| `core/model_code_conformance_contract.yaml core/claim_evidence_contract.yaml core/claim_consumption_contract.yaml` | 3 | 原位。按具体协议与选择器区分核查及消费。 | 单位、统计口径、项目身份和源选择一致。结构检查不能授予数值资格。 |
| `core/review_receipt_contract.yaml core/review_receipt_consumption_contract.yaml` | 2 | 原位。回执结构与指定阶段的消费分开。 | 无显式策略和绑定当前小问/阶段者分别处理。 |
| `core/literature_research_contract.yaml core/case_memory_retrieval_contract.yaml` | 2 | 原位。分别支撑外部研究及有界案例。 | 撤稿分流与拒绝记录分开。案例推荐不成为已执行证据。 |
| `core/writing_runtime_contract.yaml core/writing_reasoning_contract.yaml core/compile_profiles.yaml` | 3 | 原位。写作阶段、论证语义、编译配置分别保留。 | 换小问取回对应原文。编译成功不授予 PDF 视觉资格。 |
| `core/stage_reading_guide.md HSK_SKILL_FILE_INDEX_V622.md HSK_TEMPLATE_INDEX_V622.md SKILL_FILE_INDEX.md TEMPLATE_INDEX.md MANIFEST.sha256` | 6 | 派生文件或受管旧指针。按 generate_indexes 的原始来源重新生成。 | 导航、文件分发摘要不作为正文或门禁结果。 |
| `modules/05_writing/references/*` | 2 | 例文及使用边界。保留前言和使用边界，按事实选择示例。 | 简单解析题不因例文增设小节。 |
| `modules/01_problem_audit.md modules/02_model_design.md` | 2 | 原位。题意冻结、替代方案、审查、求解器前提。 | 没有官方模板仍可审题。未明确批准只交付候选方案。 |
| `modules/03_data_preprocessing.md modules/03_solve_validate.md modules/03_result_analysis.md` | 3 | 原位。条件式统一预处理、03A 主求解、03B 独立实验。 | not_required 分支不伪造工作簿。已承诺实验有独立结果。 |
| `modules/04_figure_evidence.md` | 1 | 原位。图区分数据来源、后端、证据深度与渲染。 | 同问两类图分别满足证据资格。 |
| `modules/05_writing/* modules/05_latex_compile_quality.md` | 5 | 原位。逐问写作协议、载体、清理、05D。 | 初稿先作语义审查。定稿只对相同 PDF 逐页覆盖。 |
| `modules/06_review*` | 3 | 原位。保留入口的共同分级与 blocking 条件，初审取 content，终验同时取 final。 | 初稿不会因终稿尚无 PDF 而被当作无法开始。 |
| `packs/task/*` | 12 | 原位。classifier、题型与 advanced_method_gate 在其适用条件下消费。 | 网络结构依据题面。算法必要性不能由高级名称推出。 |
| `packs/competition/* config/competition_profiles.yaml` | 6 | 原位。稳定赛事 profile 与特定届次规则分离。 | 认证杯无专属模板可继续。未核实届次规则不得升为官方约束。 |
| `packs/artifact/*` | 10 | 原位。根据请求的 LaTeX、DOCX、代码、图、证明、算法、文献、案例或提交动作消费。 | 只有数学论证、算法追溯需要时才实际生成相应成果。 |
| `config/prose_audit_patterns.yaml config/review_weights.json` | 2 | 原位。文本审计模式和终审评分配置，按其指标定义读取。 | 排版警报与阻断问题区分。评分不能代替视觉检查。 |
| `assets/figure_assets.yaml assets/nature_figure/README.md` | 2 | 保留资源使用条件、索引及来源角色。资料说明中的旧后端示意服从现行 Figure Authority。 | 根据 reference_index 选取 atlas 或 gallery 中适用的素材。示例不提供项目数值。 |
| `assets/nature_figure/*` | 15 | 按索引选择的 PNG 素材原位。 | 即使取齐所有规则，15 张素材也无须全部载入。 |
| `knowledge/case_memory/schema.yaml knowledge/case_memory/README.md` | 2 | 原位。D1 准入、许可、合成证据边界和使用说明，D2 行为回到 retrieval 合同。 | 纳入索引不等于真实项目验收。 |
| `knowledge/case_memory/index.json` | 1 | 派生索引。由案例维护工具及仓库生成链保证与真实案例输入一致。 | 案例字节变化不能沿用旧索引结果。 |
| `knowledge/case_memory/*` | 4 | 案例、来源、检索特征和开发查询原位，按案例/开发用途消费。 | 故意排除的案例保持排除。开发查询不授予独立效果验证。 |
| `templates/figure/mechanism_placeholder.md templates/figure/per_question_mechanism_plan.md` | 2 | 原路径保留为旧指针。机理图合同回到当前模板，规划回到项目框架。 | 不恢复独立机理占位表或第二套项目记忆。 |
| `templates/figure/*` | 11 | 原位。保留图类合同、选择、增强、draw.io 规格、QA、图文闭合及各自父级触发。 | 机理图可用模型信息。结果图必须据已验收数据。结构检查后仍需看渲染。 |
| `templates/model/* templates/problem/*` | 9 | 原位。字段及语义骨架供初始化、审题、建模使用。 | 只在形成候选方案后按现行合同建框架。模板中没有项目批准或数值。 |
| `templates/review/final_review_matrix.yaml templates/review/result_manifest.yaml templates/review/*.md templates/writing/*` | 8 | 原位。分别保留终审矩阵和工具约束、结果清单触发条件、写作检查说明。 | 审查矩阵区别未核验与已核验。只在对应交付生成项目清单。 |
| `templates/code/*/README.md templates/matlab/README.md templates/plot/python/README.md` | 5 | 原位。保留模板前言、语言/后端条件、交付与孤立复制要求。 | 已锁 Python 求解与 MATLAB 绘图可组合，不能从绘图语言推出求解语言。 |
| `templates/code/hsk_pipeline/* templates/code/starter/* templates/code/matlab/* templates/code/requirements.txt` | 16 | 可实例化源码及依赖原位。检查独有可观察行为后更新对应合同或实现，见下文。 | 同一训练和留出集合置换后核心、明细和比较基线一致。 |
| `templates/plot/python/* templates/matlab/*` | 9 | 绘图实现原位，实例化时保留读取与样式约束，适用规则由图合同持有。 | 可区分缓存缺失的公式与合法空值。不能重算任务数据。 |
| `templates/latex/cumcm/hsk/template_manifest.yaml templates/latex/cumcm/hsk/README.md` | 2 | 原位。物理装配、可变和固定槽位、模板与写作权威边界。 | 启用模板时核对真实 input 顺序。示例标题不自动成为强制小节。 |
| `templates/latex/cumcm/hsk/reference/* templates/latex/cumcm/cumcmthesis/*` | 6 | 参考样稿、上游类和说明原位。注明许可及参考用途。类文件及示例分别按构建/参考使用。 | 参考样稿中的题目、假设和结论不迁入当前论文。 |
| `templates/latex/*` | 22 | 实际载体源码、编译输入、节片和示例书目原位，受所选赛事/真实装配及相关元数据控制。 | 旧的未装配数据节不强制入文。合规附录须在实际环境内。 |
| `docs/stage_reading_execution_refactor_plan.md` | 1 | 当前 §13.2 的可复制入口迁往 PROJECT_INSTRUCTIONS.md。其余计划保留原位。 | 网页用户有唯一复制位置。原固定提交仍能恢复旧文本。 |
| `docs/semantic_state_runtime_refactor_plan.md docs/v8_writing_migration.md docs/v900_migration_contract.md docs/v970_solver_backends_migration.md docs/v871_writing_reasoning_schema_version_policy.md` | 5 | 保留受委托的迁移/版本决定，按下表的范围和适用时期消费。 | 换版本不自动授予项目批准或覆盖已有正文。 |
| `docs/*` | 88 | 余下设计、记录、研究评估、发布说明或管理材料原位，由其引用者按用途取读。 | 维护计划中的候选能力、历史达标记录和开发题库不能当本项目行为。 |
| `scripts/*.py` | 78 | 实现、校验、生成和维护脚本原位。本表下方登记跨层委托。 | 每次运行按其权限，程序字节可核对不等于实际运行。 |
| `scripts/README.md README.md PROJECT_INSTRUCTIONS.md RUNTIME_ROUTER.md REPOSITORY_INDEX.md` | 5 | 当前导航原位。P2 简化用户指令与指向的正文来源。 | 可定位固定版本。网页环境无执行条件时仍可取原文。 |
| `SKILL_CHANGE_GOVERNANCE.md AGENTS.md .github/*` | 6 | 仓库治理、协作、PR 与 CI 规则原位。仅在维护变更、生成、验收与发行时执行。 | 正式门用对应最终 head 的实际远端记录。 |
| `skills/* agents/* .codex-plugin/*` | 2 | 剩余客户端入口元数据，保持发现/版本对应关系。 | 插件安装信息与项目模型批准各有来源。 |
| `HSK_RUNTIME_ROUTER_V622.md PROJECT_INSTRUCTIONS_HSK_V622.md legacy/*` | 96 | 历史材料与兼容跳转原位。 | 固定旧项目可读。归档不升级成默认动作。 |
| `state/*` | 1 | 示例项目状态原位。 | 示例状态不能代替比赛项目的 current State。 |
| `tests/*` | 323 | 测试、合成项目、ZIP、衡量材料与独立预期原位，供开发和 CI。 | 合成批准、数值及视觉样例不能成为比赛证据。 |
| `.gitattributes .gitignore requirements-dev.txt requirements-plot-python.txt LICENSE THIRD_PARTY_NOTICES.md CHANGELOG.md` | 7 | 保留构建、依赖、许可与版本历史，按分发或维护动作使用。 | 可追溯上游类及视觉素材，历史 release 信息不能改变固定 commit。 |

本次路径核算共 46 组、805 项。P1 新增的维护地图和夹具属于本基线之后的增量。

## 有明确目标位置的条文

范围均按上面的固定提交定位。尚未在候选分支完成的迁移以下列正反例验收，原批准、执行和交付边界随原条文保留。

| 旧位置及父级条件 | 候选位置或处置 | 调用者与正反例 |
|---|---|---|
| 两份 `SKILL.md` 第 12–28 行的运行时入口、`core/bootstrap.yaml` 的 purpose / startup_contract / hard_invariants、`core/workflow_router.yaml` 的 default_load / load_policy、`core/hsk_core_policy.md` §3 最后一段 | P2 由 bootstrap 持有正式任务全文启动、范围明确的局部维护、恢复三类入口。全局政策持有边界，router 继续选择当前业务动作。两份入口同步委托。 | 首次正式题获得全套现行规范。只修配色或一次维护咨询仅取对应原文。变化影响数据和结论则重新判定范围。 |
| `docs/stage_reading_execution_refactor_plan.md` §13.1–13.3，特别是 497–520 行可复制正文。README、项目指令、脚本说明所指向的同一入口 | P2 在 `PROJECT_INSTRUCTIONS.md` 持有一份网页/App 可复制正文。旧页的当前分支给出迁入位置，历史 commit 仍可复现既有指令。 | 从 README、项目页或插件进入均执行同一版本。入口复制时保留“由用户执行数值代码”“审批绑定当前身份”“部分页不可报全页”等父条件。 |
| `core/runtime_assurance_contract.yaml` 的 reading_plan.consumer_protocol 及其父节点。`scripts/reading_plan.py` 的 SourceReader、范围选择和 validate_chunk_coverage | P3 由原运行合同持有分块、缺块、重取及证据强度，来源组成由 module manifest 承载。只读读取器按独立的预期字节身份核对返回内容。 | 行数相同但末行少半句仍要重取。完整返回只说明本次取得该来源，不能推断会话一直保留它或已经执行业务门。 |
| `core/workflow_router.yaml` 第 24–41 行 project_memory_contract。`scripts/reading_plan.py` 的 _scope / _project_reads / build_reading_plan | P4 将现有 full_read_when 接到真实初读。混合意图按交付分别带入已触发的图合同。保持 resolver 按当前项目给出门序。 | 有当前框架时，全文终审初读整份。单问局审有边界。混合图缺误差工作簿时，机理图仍能推进到其自身允许的环节。 |
| `templates/figure/figure_plan.md` 的前言、登记表及“要求”。`modules/05_writing/paper_writing_protocol.md` §13.0 | 原位。前者保存 Figure ID、数据、用途与待定位置。写作方盘点、定位及回填依后一来源。 | 预登记文件名并非导出证据。写作后用真实图、正文和引用核对，允许某问没有所需图表。 |
| `core/state_transition_contract.yaml` 的 authority_boundary.delegates 指到 `docs/semantic_state_runtime_refactor_plan.md` 的 Phase E（959–1009 行）与 Phase F（1010–1037 行） | 原位保留命名迁移与事务设计的受委托范围。历史计划要与当前 state_transition 合同、`scripts/artifact_identity.py`、`scripts/project_transaction.py` 核对，对后续已明确退役的行为服从当前实现和兼容条款。 | 只读审计历史别名，当前写入使用受支持身份。事务失败以后不可恢复未提交的批准。其余阶段标题本身不会激活新业务门。 |
| `core/writing_reasoning_contract.yaml` 的 v8_compatibility.project_migration、LaTeX adapter 的迁移说明 → `docs/v8_writing_migration.md` 全文。`docs/v900_migration_contract.md`、`docs/v871_writing_reasoning_schema_version_policy.md` 的维护适用范围 | 原位。`scripts/generate_indexes.py` 的 CURRENT_REFERENCE_DOCS 只标记索引参考角色。P5 按实际历史族分别处理正文、身份与解析协议。`docs/v970_solver_backends_migration.md` 只记录 v9.7 逐问后端的历史原貌，项目根后端的现行选择与迁移取自 user_execution_contract。 | 旧正文只读，保留历史 hash，不自动搬已填内容。首次选后端与更换已有后端走各自条件。固定版本身份和各合同版本分别核查。 |
| `templates/latex/cumcm/hsk/template_manifest.yaml` 中 authority_boundary、paper_skeleton、fixed_template_checks、runtime_contract。`config/competition_profiles.yaml` 中 stable 与 edition_rules | 原位。固定装配槽归模板，论证语义归写作合同，当届硬约束归已核实的届次来源，`hsk_main.tex` 的实际活动输入决定检查对象。 | 国赛示例稿件、A196 参考及维护 smoke 的标题不能一律强加给认证杯或同类简单问题。编译需按活跃装配和相应届次判断。 |

**P4 实施调整。** 原计划中将图规则列为“只回归”，但基线 [Figure Authority 第 43 行](../modules/04_figure_evidence.md#L43) 明确把与数值图混合的请求整体交给数值前置链。补齐读取来源本身不会改变交付资格。P4 应同步修订这个条款，并核对 `scripts/resolve_workflow.py` 的 scope 合并、`core/output_contract.yaml` 的 mechanism_scope 和 `scripts/sync_project.py` 的实际消费者。若用户要两张可以独立交付的图，分别落实各自条件。纯机理图仍要求当前已批准模型、Spec、可编辑源、绑定的实际预览和登记的导出。一张图只要使用 result_evidence，整张图就走数值证据链。P1 的混合图探针只测规则取回。两类交付在 P4 分别验证，不能由 P1 测试推定已通过。

## 合同外还要核对哪些实现

下面列出对 v11 改动有直接影响的程序或模板边界。登记位置是为了对照真实调用路径并找回独有约束。源码不整体纳入正式任务的开场正文。

| 行为及源码入口 | 规则去向与可运行的对照 |
|---|---|
| 核心状态与批准。 `scripts/semantic_identity.py`、`scripts/validate_semantic_governance.py`、`scripts/runtime_assurance.py`、`scripts/state_transitions.py`、`scripts/validate_model_approval.py` | 语义投影和持久化顺序在既有治理/事务入口实现，stale 含义归状态转换合同，明示批准条件归批准合同。框架有上游边但 State 漏记，或仅提升修订，分别与两侧一致、初建、未升版和独立分支对照。 |
| 预处理、主工作簿与普通深化工作簿。 `scripts/validate_user_execution.py` 的 preprocessing_passed / validate_one，`templates/code/hsk_pipeline/workbook_validation.py` 的 _check_ordinary_evidence、_check_missing_value_audit、有限值/残差检查。`templates/code/hsk_pipeline/result_io.py` 的独立运行回退 | 返回入口与读写库按同一 workbook schema 解释必需行、可选空值、真实数据来源、验证项与单位。正常 0、合理逻辑字段、合法缺测，与唯一必答值为空、索引自引、同方法当中漏一个承诺实验等对照。切换独立目录与两种运行后端也需核对相同字段。 |
| 数值证据与示例。 `scripts/validate_numerical_evidence.py`、`scripts/primary_quality_specification.py`、`templates/code/starter/analysis_comparison.py` 和 `templates/code/matlab/analysis_comparison_example.m` | 量纲、能力、方向及旧协议标记分别回到数值合同和表结构。换算后的同一距离应同判，米与秒单独处理。倒序区间与合法等端点分开。显式绑定严格协议与历史真空编号分开。留出点通过真实键定位，更换行序后主指标仍对应同一行。 |
| 工作簿证据投影。 `scripts/claim_values.py` 的 _comparable / _derive 及 `scripts/claim_evidence.py`，`templates/plot/python/q1_plot.py` 和 `templates/plot/python/data_process.py` | 主张合同负责可比较的单位与统计口径，图合同负责可读值与所选图的资格。均值与总和应能区分，交换求均值的输入顺序不应改变结果身份。真正空单元与无缓存公式分别验证。 |
| 文献与引用。 `scripts/literature_search.py`、`scripts/literature_evidence.py`、`scripts/literature_snapshot.py`、`scripts/audit_paper_prose.py` | 方法候选的适用条件归文献合同。明确撤稿与未知分开，导入与检索一致地保留拒绝记录。书目引用与图号引用分别测无前注、带前后注、多键和缺键。 |
| 载体与终审。 `scripts/audit_latex_project.py`、`scripts/score_submission.py`、`templates/review/final_review_matrix.yaml`，最终包另走 `scripts/validate_submission_package.py` | 2026 国赛附录环境外的说明与环境内正文分开。沿 05D 与现有矩阵绑定 PDF 哈希及助手看过的页面，核对 1/3、3/3、重复页、仅有日志和更换 PDF 五种结果。 |

## 迁移时如何核对增减

本次 P1 仅登记，不删改基线条文。后续实际移动条文时，在对应行补记新提交、原父节点和连续范围、目标节点、保留或经批准改变的单位/阈值/例外、受影响调用者及正反两项实测。保持原位的条文沿用固定提交中的原有全文。若实现与合同已经冲突，保留原始反例及其作用范围，再由所属工作包修实际消费者。仓库维护的验收记录独立于具体比赛的项目批准、工作簿及逐页审查。

## 怎样复做 P1 的基线

| 维护侧入口 | 实际测到什么 | 结果如何使用 |
|---|---|---|
| `python tests/v11_reading_baseline.py` | 同时运行全文终审、混合图、分块与普通 03B 四组。使用 `--checkout` 可指向单独的历史 checkout。 | JSON 保存当前源身份、实际输入、对照和观察结果。工作簿例只到普通结构检查，不能据此授予整问验收。 |
| `python tests/v11_business_baseline.py` | 使用开发与 Python 绘图依赖，在临时项目重放 01–14。历史观测和目标在 [逐案预期](../tests/fixtures/v11_business_baseline.yaml)。例如 `--case 05` 对照米、千米、厘米及不相容的秒；`--case 13` 只测试评分矩阵。 | 常规退出码检验对照是否有效；每一项的目标差异单列。对适用的新接口可用 `--require-target` 显式检查目标。改变版本化协议时增加新写入/验收入口的正反例，并独立保留旧协议的读取能力。 |
| [网页/App 输入](../tests/fixtures/v11_web_app_cases.yaml)、[材料导出器](../tests/v11_web_app_packet.py)、[独立评分册](../tests/fixtures/v11_web_app_rubric.yaml) | 共 10 个场景、12 轮请求。维护方按 case/turn 导出确定性 ZIP，只向测试会话提供该轮用户请求及附件。评分册有 34 个判据，预置答案与候选输出分开。 | 旧默认、旧版显式全文、候选入口三组使用相同材料。记录实际客户端、规则版本、操作数、漏项和用时。没有真实会话的组保留空白。 |

固定 v10.35.3 的对照包含已复现的错误；仅对照成立，不能把 18 项标成已修。远端 Windows 专项保存读取与业务 JSON，绘图矩阵另运行第 10 项并输出真实工作簿的两种读取结果。实际题目、模型批准、用户数值执行和 PDF 逐页查看均沿用原项目流程。
