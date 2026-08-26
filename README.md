# mathmodel-skill v7.13.0

HSK 数学建模工作流：**审题与 Problem Contract 冻结 → 非破坏性数据审计 + 模型路线/数据需求比较 → `preprocessing_decision` → 语义闭环与复杂度复审 → 结构化简与 Algorithm Trace → `proposed_model_spec` → Model Reviewer + Devil's Advocate → Model Approval Brief → `awaiting_model_approval` → 用户明确批准当前 `semantic_revision/hash` → `locked_model_spec` → 条件式预处理 → 用户本地 full-fidelity Python 主求解 → 独立结果深化分析 → MATLAB Figure Evidence + 按需 Figure Enhancement → LaTeX 终稿 → AI cleanup → LaTeX project audit attestation → profile-bound compile attestation → 评委式终审 → submission package generation → resolver-returned `pre_delivery_gates` → validated submission package**。

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

### MATLAB Figure Evidence

MATLAB 只读取 Python 输出的数据和标准工作簿绘图，不重新求解。图形布局按核心结论、证据等级和主要问题动态选择；基础布局后再通过 Figure Enhancement Gate 判断是否需要局部放大、分面、焦点高亮、语义背景、联合诊断或条件式 3D；默认保留图窗供人工调整，不批量自动导出。

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
- `core/code_quality_contract.yaml`：Python 工程质量；
- `core/user_execution_contract.yaml`：用户本地执行与工作簿验收；
- `core/writing_reasoning_contract.yaml`：推理、Algorithm Trace、术语、数值、Title Claim、规则等级和 Citation Evidence；
- `modules/05_writing/latex.md`：正文结构与表达；
- `core/output_contract.yaml`：目录、产物和正式交付；
- `core/project_state.schema.yaml`：机器状态；
- `templates/model/model_paper_framework.md`：项目记忆模板。

## 关键检查命令

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests
python scripts/validate_model_approval.py <project_root> --strict
python scripts/validate_model_paper_framework.py 模型论文框架.md --strict
python scripts/audit_latex_project.py final_latex/main.tex --bib final_latex/references.bib --framework 模型论文框架.md --require-framework --write-report --strict
python scripts/render_paper.py final_latex --profile <profile>
python scripts/validate_submission_package.py . --strict
```

正式项目交付还按实际阶段执行 resolver 返回的完整 `pre_delivery_gates`；项目级预处理或主求解代码阶段包含 `semantic_governance → model_approval → code_delivery`，已有 accepted 主结果的独立结果深化分析不要求历史追溯审批。

## 兼容与历史

`legacy/` 只读，不进入默认执行链。v7.12 及更早项目保持只读兼容；Figure Enhancement 与 Algorithm Trace 都是按需能力，不要求历史项目反向补写。Model Approval 同样不要求历史项目倒填，只有重新进入当前模型设计、项目级预处理、主求解或语义变化后的重算时迁入新门。历史版本说明保留在 Git 历史和 `CHANGELOG.md`。

许可证与第三方声明见 `LICENSE`、`THIRD_PARTY_NOTICES.md`。