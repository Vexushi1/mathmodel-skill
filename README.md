# mathmodel-skill v8.1.0

HSK 数学建模工作流：**审题与 Problem Contract 冻结 → 非破坏性数据审计 + 模型路线/数据需求比较 → `preprocessing_decision` → 语义闭环 + 按需机理/几何结构有效性闭合 + 复杂度复审 → 标准模型类型 + Model/Solver/Validator 身份闭合 → 结构化简与 Algorithm Trace → `proposed_model_spec` → Model Reviewer + Devil's Advocate → Model Approval Brief → `awaiting_model_approval` → 用户明确批准当前 `semantic_revision/hash` → `locked_model_spec` → 条件式预处理 → Primary Quality Specification → 用户本地 full-fidelity Python 主求解 + Primary Evidence Capture → 主结果质量门 + 独立数值证据复核 → accepted solution workbook → 独立结果深化分析 + Analysis Evidence Capture → MATLAB Scientific Figure Synthesis + Composite/Enhancement → Figure Portfolio Review → Template-First 逐章读取/写入 → final-order Cross-File Chapter Handoff assembled seam sweep → draft semantic review → AI cleanup → LaTeX project audit attestation → profile-bound compile attestation → final review → submission package generation → resolver-returned `pre_delivery_gates` → validated submission package**。

## v8.1.0：Cross-File Chapter Handoff

本版本为模块化 CUMCM LaTeX 增加最终装配顺序的章节文件承接能力。Paper Writing Protocol 是唯一普通正文语义 Authority；Runtime 从现有 Template Manifest 的 `ordered_slots + activation` 恢复 actual active adjacency，并在逐章写作前后读取、更新和 gate；`模型论文框架.md#Chapter Handoff Map` 只保存 writing-only 项目事实；Review 对装配全文执行 assembled seam sweep。

该能力检查对象、符号/术语、真实依赖、claim、重复和桥接必要性，但不强制每个文件边界生成过渡段，也不按连接词频率判断连贯。摘要按最终阅读顺序检查 `abstract → problem_statement`，条件章节关闭后不生成虚假 seam。纯 handoff wording/status 不进入模型语义哈希，不触发 Model Approval 或 03A；旧 framework 继续可读，单文件论文保持 `not_applicable`。

## v8.0.2：Entrypoint Surface Slimming

本补丁不改变数学建模 runtime、Model Approval、03A/03B、Workbook/Project State、Python/MATLAB/LaTeX ownership 或写作 Authority。它把 `SKILL.md` 与 `PROJECT_INSTRUCTIONS.md` 收缩为启动程序、稳定硬边界和 Authority 指针，删除此前复制在入口中的版本演进、数值阶段、Figure 与逐章写作细则；root/package Skill 继续完全一致，resolver 仍决定最小 route-specific load。历史 v8.0.1 能力保全说明保留在下方和对应审计文档中。

## v8.0.1：Chapter Capability Preservation

在 v8.0.0 Template-First 架构上完成 v7.19 章节写法与 v7.20 R1 的逐项能力保全：普通 CUMCM 路由保留标题/摘要、问题重述与分析、假设/符号、数据与共享基础、模型建立、模型求解、数值/术语、结果/验证、图叙事、评价、引用、结论/附录和篇幅诊断的详细规则。默认运行时先读模板但不生成正文，随后按“读当前章节规则 → 写当前章节 → gate”逐章推进；模型建立及求解中的命题/证明与 stepwise/pseudocode 均有显式条件加载分支。另新增 Q3 后问模板、v7.20 终审清单和功能次序/solver-first/连续图裸堆行为审计。迁移矩阵见 `docs/v801_chapter_capability_preservation_audit.md`，旧 v8.0.0 项目不自动改写。

## v7.19.0：Intra-Question Writing Closure

本版本在 v7.18.0 连续“模型建立 → 模型求解 → 结果解释”叙事基础上，进一步治理**既定一级论文骨架内部**的小节顺序、详略分配和图结果表达；不改变模型数学语义、Human Model Approval、03A/03B、Workbook/Project State Schema、Python/MATLAB 分工或运行时 Gate。

- 新增 **Within-Question Subsection Architecture**：中文国赛既定“符号说明 → 数据说明/必要数据预处理 → 共享基础模型/模型准备 → 问题一 → 问题二 → ……”一级骨架和问题顺序保持不变；新规则只在当前大章节内部按真实局部数学依赖与求解认知顺序安排二级/三级小节、公式、solver、结果与验证。
- 数据说明/必要数据预处理与共享基础模型一旦启用，只规范各自**内部**的依赖顺序；不得因为后续求解依赖而重排一级章节，也不得把后问专属内容提前到前问章节。
- 新增 **Detail Allocation Governance**：正文篇幅按内容对模型结构、判据/边界、可行域、solver 适配、最终答案和验证 claim 的决定性分配；关键推导保留完整信息链，Routine algebra、重复符号、算法百科、未变化继承关系和无新解释价值的数字优先压缩。
- Detail Allocation 同步约束 solver 段：重点写当前模型为何需要该 solver、本题变量/状态怎样编码、目标怎样评价、约束怎样处理、关键参数/精度/终止条件及输出怎样回到模型变量；算法历史、通用优点和未修改标准算子不占正文主体。
- 对简单解析或直接计算问题执行 **simple-problem anti-bloat**：不强制多个小节、算法段、核心模型汇总、图表或额外验证；“详写”指决定性信息链完整，不等于统一增加字数、公式数或标题数。
- 新增 **Figure Result Narrative**：核心结果图在邻近正文中自适应完成“图展示什么关系及当前作用 → 决定性特征 → 必要关键数值 → 与当前设问的联系 → 有证据支持时解释原因 → 必要收束”；它是信息功能链，不是固定六句话或统一曲线模板。
- 图的原因解释只能来自当前模型方程、约束活跃性、物理/几何机制、统计结构或已证实数据规律；证据不足时只描述可确认现象和设问含义，不为了“分析充分”编造机制。多面板图先说明共同问题，只展开对结论有独立贡献的 panel 差异。
- 新增 **Question-Section Narrative Closure**：每个“问题X模型建立及求解”结束前，应能从本章内部恢复“局部任务 → 模型闭合 → solver 消费 → 结果解释 → 直接回答本问”；若最后一个结果段已经完成 answer link，不机械追加固定“小问结论”。
- 新规则只进入 `core/writing_reasoning_contract.yaml` 及其 LaTeX/AI-cleanup consumers；不新增第二套 writing contract、runtime Gate、CLI、项目必填字段或数值迁移。历史 accepted 结果不因本次写作升级自动 stale。

## v7.18.0：Model Establishment & Solution Writing Style Hardening

本版本只强化“模型建立—模型求解—结果解释”的论文叙事和表达，不改变模型数学语义、求解所有权、Model Approval、03A/03B、Workbook Schema、Project State 或运行时 Gate。

- 新增 **Continuous Mathematical Narrative**：模型建立围绕当前对象、下一数学需要、建式依据、关系后果和下游用途连续推进，避免“建立 A 模型—建立 B 模型—采用 C 算法”的报告式拼接。
- 新增 **Formula Prose Rhythm**：核心公式正文按 `Need / Basis / Formula / Meaning / Consequence` 的信息功能闭合，但不要求固定五句话；已定义符号后优先解释公式带来的判据、可行域、目标或计算结构变化。
- 新增 **Transition Function Governance**：衔接句按 `inherit / gap / introduce / transform / solve_entry / result_entry / interpret / increment` 的逻辑功能判断，不维护“首先—其次—因此”连接词模板。
- 新增 **Professional Heading Semantics**：标题按独立数学任务组织，优先恢复“处理哪个对象、完成什么关系/计算动作”；不强制“XX 的 XX”语法，也不把决策变量、目标函数、约束和模型汇总机械拆成多个小节。
- 新增 **Model-to-Solver Bridge**：solver 首次出现前先说明真实模型结构、计算困难、已完成化简或搜索对象，再写本题编码、约束处理、参数/精度/终止条件；算法通用优点不能替代本题理由。
- 新增 **Result-adjacent Interpretation**：单点最优、曲线/图像、算法/精度验证分别使用自适应解释功能，关键结果出现后就近说明决策含义、形成机制、可行性和对设问的回答，不把图表集中堆放后统一“由图可知”。
- 明确模型建立部分默认不重新完整复述问题分析、模型假设或题面，后问只恢复真实继承与新增结构；AI Cleanup 只审计表现风险，不成为第二写作 Authority。
- 规则来源主要抽象自优秀国赛论文的连续论证方法，但 runtime 不包含参考论文名称、固定句式、具体算法、题目专属对象或章节模板。

## v7.17.0：Mechanism Structural Validity Hardening

本版本面向机理、几何、连续事件与混合优化题补强 Solver 之前最容易被忽略的结构层，同时保持现有 Problem Contract、Model Challenge、Human Approval、03A/03B、Workbook Schema、Project State 和用户 full-fidelity 执行边界不变。

- Module 02 新增按需 **Predicate Closure**：明确 physical event、object domain / active-visible subset、reference frame、exact predicate、quantifier order，以及 line/ray/segment/surface/volume 的真实语义；独立等价判据可用于实现交叉复核，但数值一致不能替代数学等价证明。
- 新增 **Event Topology / Boundary** 协议：连续事件允许由多个区间组成；二分、牛顿或局部搜索必须给出有效 bracket、局部结构、端点更新、容差与 fallback，禁止把全局 `0→1→0` 事件直接当成单调区间二分。
- 新增 **Reduction Provenance**：结构缩域明确区分 `exact / proven_sufficient / heuristic`。heuristic 缩域必须记录弃置域检查与真实 claim scope，有限采样未发现反例不能升级成全域证明。
- 新增 **Solver Applicability / Objective Landscape**：先从平滑性、凸性、可行域稀疏、平台、事件跳变、维数和单次评价成本解释 Solver 适配；必要的 empirical probe 必须作为 Human Approval 后的预先定义条件分支，禁止跨赛题固定阈值和 post-hoc 判据。
- 新增 **Multi-resource Composition**：显式区分 `sum / union / intersection / max / min / forall-exists / exists-forall / custom`，避免把并集写成简单时长相加、把 `∀x∃i` 错写成 `∃i∀x` 或把真实协同错误解耦。
- 新增 **Surrogate / Decomposition → Original Model Reevaluation**：由 surrogate、pairwise capability、relaxation 或分解得到的最终候选必须回到原始目标函数和全部原始硬约束重新计算，surrogate score 不得冒充 headline result。
- mechanism / optimization Task Pack 明确 03A 只承担当前 locked model 的内在有效性；参数敏感性、压力场景、替代模型/算法、多 seed / 多初值 claim stability 与更广失效边界继续属于 accepted 后的 03B。
- `模型论文框架.md` 继续使用 `v0.8-project-memory`，只增加按需结构有效性事实与 evidence anchor，不新增 Schema、Gate、项目级报告或 taxonomy capability。
- 新增 v7.17 回归测试，锁定 Shared Foundation、Model Approval、Numerical Verification、PQS 和 03A/03B 单一 Authority 边界，防止后续 architecture creep。

## v7.16.0：Paper Writing Specification & Model Expression Closure

本版本针对实际教师评阅暴露出的论文表达缺口，在不改变数值求解、Workbook Schema、Figure Evidence、用户 full-fidelity 执行和 v7.15 Evidence Capture 的前提下，恢复并强化“评委如何快速读懂数学模型”的写作闭环。

- `core/writing_reasoning_contract.yaml` 新增 **Model / Solver / Validator** 角色分离：模型回答“数学上求什么”，solver 回答“怎样求”，validator 回答“怎样独立检查”；求解器、软件或验证算法不再允许冒充标准模型类型。
- 新增 **Model Naming** 规则：题目专属模型名可以保留，但首次正式出现必须邻近给出标准数学类型，例如连续优化、非线性/非光滑优化、混合整数优化、微分方程、回归、时间序列、图模型或仿真系统等。
- 优化、调度、路径、分配和控制类正文默认按“**标准模型类型与现实目标 → 决策变量/决策对象 → 目标函数 → 目标含义 → 约束来源 → 核心模型汇总 → solver/validator**”展开；核心模型汇总仍保留，但作为 recap，不替代变量、目标和约束解释。
- 优化类摘要新增 objective closure：至少交代标准模型类型、主要决策变量/对象、**优化什么**、主求解方式、headline result 和对设问的直接回答；只写“若干变量 + 某算法”而不说明目标函数含义不再视为模型信息闭合。
- 新增 **Solver Justification**：主 solver 第一次出现必须从本题数学结构解释适配性；跨问复用只说明继承结构和新增变化；更换 solver 说明新增离散性、非光滑、规模、不确定性或分解结构；“另用某算法”只有实际运行并有 artifact、角色和可比指标时才能进入正文。
- 新增 **Subsection Granularity**：只治理每个问题章节内部的二级小节，不限制全文一级章节数量。约 3--4 个主要小节是默认阅读颗粒度而不是 Hard 上限；变量/目标/约束/汇总、或多个同类验证若属于同一论证链，优先合并而不是机械切标题。
- 新增 **Claim Strength Calibration**：`PROVEN / VERIFIED_NUMERIC / COMPARATIVE / OBSERVED / HEURISTIC` 五级证据范围控制摘要和正文措辞。独立算法未发现更优、多启动一致或有限扰动稳定不得自动升级为“证明全局最优”“鲁棒性很强”等超范围结论。
- `模型论文框架.md` 继续沿用 `v0.8-project-memory`，新增标准模型类型、正式模型名称、Model/Solver/Validator、优化 objective 摘要口径、算法角色/evidence anchor、问题章节小节规划以及 headline claim Evidence Level/Scope，避免跨聊天写作时重新从记忆猜模型。
- `scripts/audit_paper_prose.py` 增加保守的 subsection granularity、framework objective status 和 claim-scope 检查；纯关键词只能触发 warning/review，机器仍不得从算法名、标题数或正则推断数学模型类型、正确性或全局最优性。
- 问题重述、问题分析、共享基础、Formula Trace、Algorithm Trace、Citation Evidence、Terminology、Numeric Profile、Title Claim、AI Cleanup、caption-owned figure、LaTeX attestation 与 submission provenance 继续沿用现行 Authority；不恢复旧版全自动写作或文件数量主义。
- v7.15.x 及更早项目继续只读兼容；历史 accepted 数值结果不因本次写作升级强制重算。旧项目重新进入当前模型设计/写作/终审时，只按需补齐模型类型、角色、objective、claim scope 和小节规划。

## v7.15.0：Scientific Evidence Capture & Figure Synthesis

本版本解决“主求解只留下最终数字、MATLAB 因证据不足而退化为基础图”的双端信息损失，同时保持 v7.14 主数值有效性协议和 03A/03B 边界不变。

- 主求解新增 **Primary Evidence Capture**：在当前 locked model + 当前声明数值方法的一次正式运行中已经真实产生的决策变量、状态、逐对象/逐时刻/空间结果、约束裕量、候选解、求解轨迹、逐样本预测/残差/区间和关键事件等，可按 capability 保留为 evidence-ready 工作簿底表，而不是只输出最终汇总数字。
- 03A/03B 判界继续按“是否需要改变参数、场景、seed、初值、算法、模型结构或验证窗口并重新运行新的计算世界”判断；需要重新运行 alternative world 的敏感性、压力场景、替代算法/结构、多 seed/多初值稳定性、异质性、阈值搜索和广义 OOS 仍只属于 accepted 后的 03B。
- 03B 同步升级为 **Analysis Evidence Capture**，保留逐参数、逐场景、逐算法、逐 seed、逐区域、逐阈值等细粒度证据，避免只输出“稳定”“变化不大”等摘要。
- Module 04 新增 **Scientific Figure Synthesis Gate、Basic-form Challenge、Composite Encoding Preference、Scientific Rendering Profiles、Missing Scientific Evidence Check 与 Figure Portfolio Scientific Quality Gate**。核心图从证据结构出发选择表达，不再把丰富问题默认压成 plain bar / plain line / plain scatter。
- 主证据恢复高对比亮蓝/鲜红等中高饱和主色，辅助元素继续降权；正式图仍为白底、`grid off`、caption-owned title，不恢复 MATLAB 整体 `title/sgtitle`。
- MATLAB 仍只读 Python 已验收工作簿，不重新求解、不重做分析、不从摘要数字反推数据；组合图、局部放大、全局—局部、Pareto/边界/轨迹/场/分布/不确定性等表达只有在真实证据支持时才使用。
- Workbook Schema 2.3.0、Project State Schema、v7.14 PQS/Verification ID/独立数值证据复核、每问五文件、用户 full-fidelity 执行、LaTeX attestation/submission provenance、V622 兼容指针均保持兼容。

## v7.14.1：Skill Health & Semantic Hygiene

本补丁不新增模型、求解器或数值协议，重点清理 v7.14.0 后暴露的活动语义漂移和维护噪声，同时保持主求解数值有效性与 accepted 后结果深化分析的边界不变。

- 正式 MATLAB 论文图统一采用 **caption-owned formal title**：`qX_plot.m` 与 `data_process.m` 不再设置整体 `title/sgtitle`，DOCX/LaTeX caption 承担正式图号与图名；多面板按需保留 panel label，坐标轴、单位、图例和必要直接标注继续服务证据读取。
- `scripts/sync_project.py --delivery-scope figures` 的严格规则同步反转：保留 `matlab_has_title` 报告字段用于兼容读取，但正式 Figure delivery 会拒绝实际可执行的整体 `title/sgtitle`，而不是要求它存在；MATLAB 注释中的同名文本不会误触发。
- Module 04 与 MATLAB 模板恢复白底、实体、深色、低饱和的科研默认风格，默认 `grid off`；预处理合同只引用 Figure Evidence Authority，不再维护第二套高饱和配色规则。
- `PROJECT_INSTRUCTIONS.md` 和 `REPOSITORY_INDEX.md` 补齐 v7.14 主数值有效性语义与 `core/numerical_verification_contract.yaml` / `scripts/validate_numerical_evidence.py` 导航。
- 一次性架构/施工记录从活动 `docs/architecture/` 移入 `legacy/architecture/`，保留 provenance 但退出 Active Skill Index、默认 Router load 和正式交付依赖。
- 增加回归约束，锁定 root/package Skill 一致性、正式 MATLAB 模板无整体标题、caption-owned Figure 语义、归档边界和 v7.14 primary/result-analysis 分工。

## v7.14.0：Primary Numerical Validity & Quality Gate

本版本把主求解阶段从“工作簿自报质量门通过”升级为**capability-driven 的主数值有效性规格 + 返回工作簿底层证据独立复核**，同时明确保护结果深化分析的独立职责。目录结构、用户 full-fidelity 执行所有权、每问五文件、MATLAB 只绘图、LaTeX/submission provenance 均保持兼容。

- 新增 `core/numerical_verification_contract.yaml`，作为主求解数值有效性的唯一字段级 Authority。它只回答：在当前 locked model 与当前声明 numerical method 下，这一次主计算是否有资格成为 accepted solution workbook。
- Module 02 在正式主求解代码前形成 **Primary Quality Specification (PQS)**，按当前 capability 选择可行性、均衡/守恒残差、离散精度、收敛、最低不确定性精度、主 OOS、泄漏、校准或可识别性等必要证据；阈值必须有题面、数学定义、模型/求解器容差、数值精度目标或明确项目依据。
- 新增 `scripts/validate_numerical_evidence.py`。`validate_user_execution.py` 在主工作簿验收时调用它，独立复算 `违反量/残差/容差/是否满足`、离散与收敛主判定行，并核对 `Verification ID → 实际值 → 阈值 → 判定关系 → 证据工作表 → 阈值来源`，不能只相信 Excel 中写了“通过”。
- `问题X求解.py` 仍只负责主求解及**当前结果 accepted 所必需的内在数值正确性**。参数敏感性、压力场景、替代算法/结构、多 seed/多初值结论稳定性、异质性、误差分解和更广泛外样本稳定性明确保留给主工作簿 accepted 后的 `问题X结果深化分析.py`。
- 数值步长/网格是否足以支撑当前答案属于主质量；现实/模型参数变化是否改变结论属于深化分析。当前 solver 的 stop reason、bound/gap 可作为主求解状态证据；MILP vs ALNS/GA/greedy 等跨算法一致性仍属于深化分析。
- v7.13 及更早工作簿继续只读兼容；历史 accepted 工作簿不批量迁移。旧项目只有在重新进入当前小问主求解时，才把该问迁入 v7.14 Verification ID 严格轨迹。

## v7.13.0：Evidence-driven Figure Enhancement

本版本在现有 Figure Layout Gate 后增加一层**按证据问题触发、默认关闭**的 Figure Enhancement，不改变 Workbook Schema、Project State Schema、Python/MATLAB 职责、每问五文件接口或 LaTeX/submission provenance。

- `modules/04_figure_evidence.md` 继续作为唯一绘图决策 Authority；新增 Figure Enhancement Gate，按需选择 Local Zoom、Small Multiples、Focus Highlighting、Semantic Background、Composite Diagnostic 与 Conditional 3D，默认 `none`。
- 新增 `templates/figure/figure_enhancement_patterns.md`，集中保存 embedded/detached zoom、selective detail、overview + detail、stacked strips、联合预测诊断、语义背景带和条件式 3D 等实现模式，不建立第二套规则源。
- Figure Contract 只增加可选 `Enhancement` 与 `Enhancement rationale`，QA 增加 ROI、跨面板尺度、视觉主次、语义背景和 3D/联合诊断的信息效率检查，不把 inset 坐标、透明度等实现参数塞进合同。
- 加入数据诚实边界：离散实验点、独立场景点、参数扫描点和迭代记录不得仅为美观使用 spline 等平滑制造新峰谷或拐点；局部放大必须保留全局上下文并明确 ROI。
- 多对象限制改为“同一视觉层级中同时竞争注意力的主要对象通常不超过 2--3 个”；结构化 small multiples / matrix 可以超过 4 个 axes，只要共享一个 Primary question 和稳定视觉语法。
- `figures` route 与 `full_workflow_resume` 现在显式加载 enhancement patterns，确保局部放大、分面与联合诊断在实际绘图阶段可被调用。

## v7.12.0：Declarative Runtime & Assurance

本版本把 v7.11.2 体检中确认的运行时设计债务收口为一个可解释、可验证且向后兼容的 assurance layer；不改变数学模型、Project State Schema、Workbook Schema、每问五文件、Python/MATLAB 职责或 LaTeX/submission provenance。

- 新增默认入口 `scripts/resolve_runtime.py`，旧 `scripts/resolve_workflow.py` 保留为兼容 resolver；Bootstrap 只指向新的 assured runtime。
- 可选 `--project-root` / `--question` 从 current `state/project_state.yaml` 恢复 competition、preprocessing decision、单问 classification 与 verified artifact availability，显式 CLI/API 参数优先且冲突进入 assurance diagnostics。
- intent 推断现在记录 matched keywords、deterministic score、confidence band、ambiguity 与 selection reason，不再只返回不可解释的 route 名称。
- project-state artifact assurance 对 locked model 使用 challenge/approval 与 semantic revision/hash 绑定，对工作簿使用 accepted status + 路径 + SHA-256 闭环；已知 stale/hash mismatch 不能被 legacy name-only artifact 声明静默覆盖。
- 新增 `core/runtime_assurance_contract.yaml`，声明 selected modules/gates 所需 contract dependencies；runtime 自动补齐缺失 contract，Router 的显式 core loads 只作为兼容提示而不是正确性前提。
- resolver 输出保留全部旧顶层字段，并增量增加 `runtime_plan` 与 `assurance`，其中 authority fingerprint 绑定 Bootstrap、Router、Manifest 与 Runtime Assurance Contract。

## v7.11.2：Runtime Health & Semantic Coherence

本补丁在进入 v7.12.0 Declarative Runtime & Assurance 规划前做一次运行时体检，不新增业务模型或数值接口。重点修复 Skill 调取面与生命周期摘要中的语义漂移，并把当前可运行基线进一步收紧。

- 扩展 root/packaged Skill 的高频触发词，覆盖审题、建模思路/方案、完整求解、结果分析、终审和提交包等常见自然语言入口；插件关键词补充 problem-audit、model-design 与 workflow-routing。
- 统一 `preprocessing_decision` 生命周期：先做非破坏性数据审计并比较模型路线/输入需求，在 Module 02 内锁定判定，再完成 current proposed model、Model Challenge 与 Human Approval；不再在 Runtime Router 中把该判定误写成锁模后的步骤。
- 修复 Module 03A 的示意链，使正式主求解代码前的 gate 顺序与 Router 一致：`semantic_governance → model_approval → code_delivery`，并保持 project-level 预处理位于人工锁模之后、主求解之前。
- 将三个 v7.4.2 引入的长期合同中的旧 `skill_version` 元数据改为 `introduced_in_skill_version + skill_compatibility`，避免把合同引入版本误读为当前 Skill 版本；合同自身 version、Schema、CLI 与执行语义不变。
- 增加 runtime-health 回归，锁定 root/packaged Skill 全文件一致、常用触发面、预处理生命周期与主求解 gate 顺序，防止后续声明式运行时重构再次产生入口/语义漂移。

本补丁明确不实现 state-aware resolver hydration、artifact project/hash binding、intent confidence/ambiguity diagnostics 或新的 runtime assurance schema；这些进入 v7.12.0 规划。

## v7.11.1：Single-Authority Stabilization

本补丁不新增建模功能，重点收口 v7.11.0 之后暴露出的第二事实源和失效测试：Router 负责多意图路由、加载顺序与运行边界声明；Manifest 只保存模块/产物/Gate 图；Resolver 只解释声明并生成 plan。Model Approval 的字段级规则继续只由 `core/model_approval_contract.yaml` 定义，Output Contract 只保留交付集成所需的 authority pointer 与运行开关。CLI、项目状态 Schema、Workbook Schema、每问五文件接口、Python/MATLAB 分工、full-fidelity 用户执行和 LaTeX/submission provenance 均保持不变。

## v7.11.0：Model Challenge & Human Approval Closure

本版本在 Problem Contract、Semantic Closure 与 Complexity Sanity 之后增加两层正式锁模治理，不改变数值模型接口、Workbook Schema、Python/MATLAB 职责、用户 full-fidelity 执行、LaTeX attestation v3、submission provenance 或每问五文件合同。

- Module 02 在 `locked_model_spec` 前新增 `proposed_model_spec`，并执行相互独立的 Model Reviewer 与 Devil's Advocate 两次挑战审查；blocking 不能由用户批准绕过。
- Challenge passed 后生成 Model Approval Brief，并停在 `awaiting_model_approval`；只有用户明确批准当前 `semantic_revision/hash` 后，`locked_model_spec` 才成为 current。
- 新增 `core/model_approval_contract.yaml` 与 `scripts/validate_model_approval.py`；项目级预处理和主求解代码交付前必须验证 challenge/approval 与当前 revision/hash 完全一致。
- 语义 revision/hash 变化会使旧 challenge、approval 与 locked model stale；纯排版、措辞、caption、公式编号或不改变语义的 LaTeX 文件拆分不触发重新审批。
- 旧项目保持只读兼容；只有重新进入模型设计、项目级预处理、主求解或语义变化后的重算时才迁入新 approval gate。
- 不迁移旧 V2 的 `HUMAN_MODEL_REVIEW.md`、`MODEL_REVIEW_AI.md`、`AGENT_RUNS.md` 等 reports 文件体系，也不绑定特定 multi-agent runtime。

## v7.10.1：Read-Path & Gate Dispatch Closure

本补丁不改变数学模型、数值求解、Workbook Schema、Python/MATLAB 职责、LaTeX attestation v3、submission validator 语义或每问五文件接口；只修复 v7.10.0 后的读取路径、入口说明和维护版本源漂移。

- Agent、Bootstrap 与项目入口统一把 resolver 返回的 `pre_delivery_gates` 视为**完整且有序的唯一 gate 列表**，不再维护容易漏掉新 gate 的固定枚举。
- Root Skill、Runtime Router 与 Project Instructions 统一终端顺序：正式编译证明 → 评委式终审 → 生成 official/reproducibility package → 执行 resolver gates → `validated_submission_package`。
- `REPOSITORY_INDEX.md` 与 `scripts/README.md` 补齐 formal delivery、package generation 与 package validation 的活动工具导航。
- `templates/review/result_manifest.yaml` 的内部复现元数据位置统一为项目级 `internal_metadata/`。
- `scripts/lint_skill_checks.py` 的 release version 直接读取 `core/bootstrap.yaml`，直接运行后端也不会停留在旧版本常量。
- 新增跨层 regression，锁定 gate dispatch、导航、内部元数据路径与 lint version source，降低后续 release 再次漂移的概率。

## v7.10.0：Delivery Attestation & Submission Closure

本版本继续收口 v7.9.0 之后的终稿交付证明链，不改变数学模型、数值求解、Workbook Schema、Python/MATLAB 职责、用户 full-fidelity 执行、framework `v0.8-project-memory` 或每问五文件接口。

- 正式 LaTeX 审计现在可持久化 `latex_audit_report.yaml`，并同时绑定 active source bundle 与当前 `模型论文框架.md`；正式编译不得跳过该证明。
- `compile_report.yaml` 升级为 v3 attestation：除 source/PDF hash 外，继续绑定 audit-report hash、compile-profile fingerprint、实际 engine/bibliography/sequence 与有效编译日志；缺失 log 不再默认视为 passed。
- `scripts/render_paper.py` 的 formal 模式负责“先审计、再按 profile 编译、再写 compile report”；template smoke 与正式交付证明显式分离。
- CUMCM class materialization 由正式编译链统一处理，不再依赖调用者手工复制 class 才能跑通。
- `full_workflow` 在进入 submission scope 后同时加载 `packs/artifact/full_submission.md`，并增加 `submission_package_validation` gate；`validated_submission_package` 只有在包级 provenance 验证成功后才成立。
- `hsk_pack_submission.py` 显式区分 `official` 与 `reproducibility`。official 模式只接受当前 competition profile 中**已核验**的 `edition_rules.submission_files` allowlist；规则未核验时拒绝自动猜测提交物。
- ZIP 自动携带 `submission_manifest.yaml` 与逐文件 SHA-256；`validate_submission_package.py` 会核对 manifest、ZIP 实际内容、当前项目同路径文件以及当前 `compiled_pdf` 哈希，旧 PDF/旧代码/旧工作簿即使文件名正确也不能通过。
- 旧无 `--mode` 的打包调用继续按 reproducibility 语义兼容；旧 v2 compile report 可读，但正式交付要求重新生成 v3 attestation。

## v7.9.0：模块化 LaTeX 运行时闭环

本版本把 v7.8.1 之后已经进入模板/Artifact 层的模块化 LaTeX 能力正式闭合到运行时、编译报告和项目同步层，不改变数学模型、数值求解、工作簿 Schema、Python/MATLAB 职责或每问五文件接口。

- 正式 LaTeX 审计统一从 `scripts/audit_latex_project.py` 进入：模块化工程递归展开 `\input/\include`，兼容单文件工程退化为单文件审计；`audit_paper_prose.py` 保留为底层 prose/BibTeX/framework 审查实现，不再作为活动 LaTeX 运行时的默认入口。
- `full_workflow` 在跨过用户执行边界后显式补齐 Figure、LaTeX 和 Review Artifact Packs，避免“直接 latex route 能读规则、完整流程反而漏读 Pack”的分流。
- CUMCM 当前项目模板统一指向 `templates/latex/cumcm/hsk/`；`cumcmthesis/` 仅保留上游 class/基础模板资源。
- 新增 `scripts/latex_delivery.py`，对 active `.tex` 图、参考文献、本地 class/style 和正式图片建立 source bundle hash；`render_paper.py` 自动生成 `compile_report.yaml`，记录 source/PDF hash、实际编译序列和未解析引用。
- `sync_project.py` 在 LaTeX/提交 scope 重新计算当前 source bundle，并要求与 `compile_report.compiled_from_source_sha256` 及 PDF hash 一致；任一 active 源文件或正式图片在编译后改变都会使旧 PDF 失效。
- Paper Fragment 的 `source_file` 在项目审计时与真实 `final_latex/` 文件和当前 main include graph 做确定性闭环检查。
- `full_workflow` 的最终 terminal outputs 补齐 `validated_submission_package`。
- 增加跨层回归测试，覆盖 audit 入口、Pack closure、CUMCM 模板权威、fragment 物理映射、source/PDF freshness 与 compile report。

## v7.8.1：Algorithm Trace 闭环补强

本补丁不改变模型、数值接口或项目结构，主要修复 v7.8.0 的最后一层读取与终审缺口：

- `review / full_submission` 显式加载 `core/writing_reasoning_contract.yaml`，不再依赖模块内部二次跳转寻找写作 Authority；
- `full_workflow / latex / docx / review / full_submission` 在需要整篇写作或终审时均可直接读取 `packs/artifact/algorithm_flow.md`；
- `scripts/validate_model_paper_framework.py` 对 `stepwise/pseudocode` 的 Algorithm ID、必填字段、模式一致性、current 状态和已求解后的 Python 锚点做确定性校验，`not_needed` 不强制算法框；
- 终审模块和审查 Pack 正式检查“模型/公式/命题/约束 → Algorithm Trace → 论文算法 → Python → 工作簿证据”是否闭合，同时保留机器不推断算法正确性或收敛性的边界；
- 修复提交 Pack 中残留的“命题最多 4 个”旧规则，重新统一为 **0--4 只是默认正文阅读预算，P5+ 经必要性审查和 justification 后允许保留**；
- 修复 framework validator 漏掉 `analyzed` 状态的 current 结果摘要检查。

Workbook Schema、三态预处理、semantic-governance 1.0.0、Python/MATLAB 职责、用户 full-fidelity 执行、`v0.8-project-memory` 和每问五文件接口均保持不变。

## v7.8.0：Algorithm Trace 与自适应算法流程呈现

本版本补齐“数学模型已经建立，但论文怎样把真实求解逻辑讲清楚”的中间层。它不新增求解器，不改变数值模型，而是让**模型结构、命题/公式、论文算法流程、Python 实现和工作簿结果**形成可追溯闭环。

### 1. Algorithm Trace

当某问确实需要正式算法流程时，在 current `模型论文框架.md` 中记录轻量 Algorithm Trace：算法作用、输入/状态、核心操作、循环/分支或阶段转换、Formula/Proposition/Constraint 锚点、终止条件、输出、Python 实现锚点、论文呈现模式和状态。

核心链为：

```text
模型结构 / 已证明性质 / 约束
→ Algorithm Trace
→ 论文算法流程
→ Python 真实实现
→ 工作簿结果或验证证据
```

Formula Trace 负责“关系为什么成立、进入哪里”，Algorithm Trace 负责“这些关系以什么顺序、状态和判定被真正计算”。

### 2. `not_needed / stepwise / pseudocode` 三态

算法流程不再机械设置为“每问一个 Algorithm 1”，而是按真实求解结构选择：

```text
not_needed
  直接计算、解析解、一次标准求解器调用，或相邻公式与短正文已能恢复求解逻辑。

stepwise
  数学阶段传递比程序控制流更重要，例如全局搜索→局部精修、标定→反演→后处理、分层优化。

pseudocode
  循环、分支、候选筛选、图搜索、动态规划、Monte Carlo、邻域更新、可行性修复或停止规则本身就是方法信息。
```

只有 `stepwise/pseudocode` 建立正式 Algorithm Trace；`not_needed` 不生成装饰性算法框。

### 3. 两种论文算法风格

新增按需 Pack：`packs/artifact/algorithm_flow.md`。

它支持两类常见数学建模论文表达：

- **控制流伪代码**：算法标题、输入/输出、行号、`foreach / while / if / return` 等必要控制结构，适合图搜索、动态规划、仿真、启发式和自定义筛选/修复；
- **分阶段数学步骤**：`Step 1 ... Step n`，每一步直接写当前数学操作、公式、参数和向下一阶段传递的对象，适合全局+局部、标定+反演、训练+校准等多阶段方法。

阶段数量和行数均不设机械预算，由当前求解链决定。

### 4. 伪代码不是 Python 缩写

论文算法写数学对象和控制逻辑，不搬入：

```text
range(len(...))
DataFrame 列操作
文件路径
日志/异常捕获
缓存/并行池
其他纯工程细节
```

完整 Python/MATLAB 仍放附录或附件。若算法框替换题目对象名后可以无修改用于任何赛题，应重写或改为 `not_needed`。

### 5. 命题与算法真正连接

若命题证明了降维、候选域缩减、可行保持、阈值或停止条件，则 Algorithm Trace 记录该命题真正改变的算法步骤。这样论文可以形成：

```text
题目条件
→ 公式推导
→ 命题/结构性质
→ 搜索空间或判定规则变化
→ 算法流程
→ Python
→ 结果
```

命题不再停在“命题得证”，算法也不再从“问题复杂”直接跳到 GA/PSO/DE。

### 6. 兼容边界

v7.8.0 不改变：

- `not_needed / question_local / project_level` 三态预处理；
- Workbook Schema；
- Python 主求解 / 独立结果深化分析职责；
- MATLAB 只读结果绘图职责；
- 用户 full-fidelity 本地执行；
- 每问五文件接口；
- semantic-governance 1.0.0；
- framework 仍为 `v0.8-project-memory`；
- `project_state.schema.yaml` 不为算法呈现新增强制字段。

算法状态、搜索域、更新、分支、修复或终止条件发生实质变化时，继续使用已有 `semantic_change_categories=algorithm` 传播 stale；仅字号、缩进、换行和行号变化不触发数值重算。

## v7.7.0：论文语义与终稿一致性治理

v7.7.0 继续收紧长论文写作语义，但不改变数值求解、工作簿 Schema、MATLAB 结果计算职责、三态预处理或每问五文件接口。

### Terminology Registry

`模型论文框架.md` 增加项目级自然语言术语表。对容易混淆的对象、指标、时间量、比例量、场景和样本单元，分别登记标准术语、定义、量纲/单位、允许简称、不推荐别名、易混术语、对应符号和适用范围。机器只检查已经登记的冲突和漂移，不从词形相似自动判断两个术语数学等价。

### 高精度 Numeric Profile

核心评分结果不按“摘要简洁”主动降位数：题面、官方规则、官方评讲或已核验评分口径指定精度时严格服从；没有更具体口径时，对决定答案、排名、阈值、最优值、时间、坐标、概率、误差等评分型连续结果，摘要和正文默认优先保留小数点后 **6--7 位**。整数、精确离散量或本身没有更高分辨率的数据不机械补无意义小数。

### Title Claim Gate

标题中的研究对象、主方法、核心机制或核心贡献必须和摘要、关键词、正文主模型、结果证据闭环。仅在末尾附带出现的方法不能包装成全文主方法。

### 局部 paper-fragment stale

某一问变化时，只沿真实依赖使对应模型/结果/图、摘要该问片段、相关模型评价句和相关 Title Claim stale；无关背景和独立小问保持 current。

### 深化证据 `support / modify / reject`

每项准备进入论文的敏感性、鲁棒性、外样本、多算法或压力测试必须指出目标主张，并记录 support / modify / reject 与 required action。reject 核心答案或模型结构才触发 redo；次要评价 claim 可以删除或改写。

### Paragraph Necessity Test 与 AI Cleanup

删除某段后若不丢失题意、机制、数学关系、求解/参数依据、结果/验证证据或必要边界，则优先删、并或移附录。机器只给 warning，不自动删文。AI Cleanup 仍按 Integrity / Evidence / Style & Necessity / Optional machine diagnostics 分层。

## 当前写作权威

写作规则由两个 Authority 收口，Algorithm Flow 为按需载体 Pack：

```text
core/writing_reasoning_contract.yaml
├─ Source → Derivation → Destination
├─ Algorithm Trace / adaptive algorithm presentation
├─ Model/Solver/Validator / optimization expression
├─ Continuous narrative / within-question local dependency
├─ Detail Allocation / Figure Result Narrative / question-section closure
├─ Hard / Default / Recommendation
├─ Terminology / Numeric / Title Claim
├─ 命题、深化证据、Paragraph Necessity
└─ Citation Evidence

modules/05_writing/latex.md
└─ 正文章节组织与表达权威

packs/artifact/algorithm_flow.md
└─ stepwise / pseudocode 的按需呈现细则
```

`ai_cleanup.md`、`docx.md`、`review_delivery.md`、Artifact Packs 和检查表只消费这些 Authority，不维护第二套正文规范。

## 当前数值工作流

### 数据审计、人工锁模与三态预处理

所有数据题都先做非破坏性审计，但不默认清洗。数据审计与 `preprocessing_decision` 属于模型设计语义；在项目级预处理或主求解代码前，还必须完成 current Model Challenge 与 Human Model Approval：

```text
proposed_model_spec
→ Model Reviewer + Devil's Advocate
→ Model Approval Brief
→ awaiting_model_approval
→ explicit approval(current semantic revision/hash)
→ locked_model_spec
→ preprocessing_decision 对应执行路径
```

三态预处理为：

```text
preprocessing_decision
├─ not_needed
├─ question_local
└─ project_level
```

共享数据、缺失值或某类赛题的历史经验都不能单独推出 `project_level`。任何改变模型输入的数据处理必须有数据、机理或模型必要性、参数依据和验证证据。

只有 `project_level` 创建：

```text
数据预处理/
├─ 数据预处理.py
├─ 数据预处理结果.xlsx
└─ data_process.m
```

### 主求解数值有效性、Evidence Capture 与结果深化分析

每问正式主求解前形成 PQS。主求解阶段只做当前计算 accepted 所必需的内在数值质量证据，同时把本次运行已经产生且对解释/绘图/验证有价值的 current-run 状态保存为 Primary Evidence Capture；返回主工作簿后由独立 validator 复核。主质量门通过后才进入结果深化分析：

```text
locked model + declared numerical method
→ Primary Quality Specification
→ 问题X求解.py + Primary Evidence Capture
→ 主结果底层证据 + 主结果质量门
→ validate_numerical_evidence.py 独立复核
→ accepted solution workbook
→ 问题X结果深化分析.py + Analysis Evidence Capture
→ sensitivity / stress / alternatives / robustness / boundaries
```

主质量与深化分析不互相替代。离散步长、网格、残差、当前 solver gap/termination 等“本次计算能否接受”的问题属于主质量；参数敏感性、替代算法、压力场景和结论稳定性属于深化分析。Primary Evidence Capture 不允许通过新参数/新场景/新 seed 等另起一次 alternative-world 计算来扩张 03A。

### 每问唯一五文件目录

```text
问题X求解/
├─ 问题X求解.py
├─ 问题X求解结果.xlsx
├─ 问题X结果深化分析.py
├─ 问题X结果深化分析.xlsx
└─ qX_plot.m
```

主求解与结果深化分析是两个独立 Python 阶段。主工作簿 accepted 后冻结主脚本，再生成深化分析脚本。赛题代码由用户本地 full-fidelity 执行，助手只生成、静态检查并验收返回工作簿。

### MATLAB Scientific Figure Evidence

MATLAB 只读取 Python 输出的数据和标准工作簿绘图，不重新求解或重新分析。正式论文图不设置整体 `title/sgtitle`，由 DOCX/LaTeX caption 承担正式图号和图名；多面板按需只保留 panel label。核心图先识别 Evidence Structure，再通过 Scientific Figure Synthesis / Basic-form Challenge 决定单图、组合编码、多面板、局部放大和 Rendering Profile；只有真实证据支持时才使用 uncertainty band、distribution + raw samples、heatmap + contour、Pareto + recommendation、trajectory + field + boundary 等科研表达。主证据采用高对比亮蓝/鲜红等颜色，辅助元素降权，默认白底与 `grid off`，并保留图窗供人工调整，不批量自动导出。整篇论文在写作前还执行 Figure Portfolio Scientific Quality Review，避免所有核心图即使技术正确也共同退化成低信息密度基础图。

## 运行时权威链

```text
SKILL.md / skills/mathmodel-skill/SKILL.md
        ↓
core/bootstrap.yaml
        ↓
core/workflow_router.yaml
        ↓
scripts/resolve_runtime.py
        ↓
route-specific contracts / modules / packs / templates
```

全局硬规则：`core/hsk_core_policy.md`。

主要合同：

- `core/model_approval_contract.yaml`：独立 Model Challenge、Model Approval Brief、Human Model Approval 与 current revision/hash 绑定；
- `core/global_preprocessing_contract.yaml`：条件式数据预处理；
- `core/numerical_verification_contract.yaml`：主求解数值有效性、PQS 映射与 strict Verification ID 证据复核；
- `core/code_quality_contract.yaml`：Python 工程质量；
- `core/user_execution_contract.yaml`：用户本地执行与工作簿验收；
- `core/writing_reasoning_contract.yaml`：推理、Model/Solver/Validator、优化模型表达、Algorithm Trace、连续模型建立/求解叙事、问题章节内部局部依赖、详略分配、Figure Result Narrative、问题章节闭环、术语、数值、Title Claim、Claim Strength、规则等级和 Citation Evidence；
- `modules/05_writing/latex.md`：正文结构与表达；
- `core/output_contract.yaml`：目录、产物和正式交付；
- `core/project_state.schema.yaml`：机器状态；
- `templates/model/model_paper_framework.md`：项目记忆模板。

## 关键检查命令

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests
python scripts/generate_indexes.py --check
python scripts/validate_model_approval.py <project_root> --strict
python scripts/validate_numerical_evidence.py <primary_workbook> --strict
python scripts/validate_model_paper_framework.py 模型论文框架.md --strict
python scripts/audit_latex_project.py final_latex/main.tex --bib final_latex/references.bib --framework 模型论文框架.md --require-framework --write-report --strict
python scripts/render_paper.py final_latex --profile <profile>
python scripts/validate_submission_package.py . --strict
```

正式项目交付还按实际阶段执行 resolver 返回的完整 `pre_delivery_gates`；项目级预处理或主求解代码阶段包含 `semantic_governance → model_approval → code_delivery`，已有 accepted 主结果的独立结果深化分析不要求历史追溯审批。

## 兼容与历史

`legacy/` 只读，不进入默认执行链。v7.18.x 及更早项目保持只读兼容；历史 accepted 主工作簿不要求反向补 Evidence Capture、Verification ID 或 v7.19 写作治理字段，重新进入当前小问主求解或写作/终审时才按 current 规则按需迁移。Figure Enhancement、Scientific Figure Synthesis、Algorithm Trace、Within-Question Subsection Architecture、Detail Allocation 与 Figure Result Narrative 都按需应用，不要求历史项目反向补写。Model Approval 同样不要求历史项目倒填，只有重新进入当前模型设计、项目级预处理、主求解或语义变化后的重算时迁入新门。历史版本说明保留在 Git 历史和 `CHANGELOG.md`。

许可证与第三方声明见 `LICENSE`、`THIRD_PARTY_NOTICES.md`。
