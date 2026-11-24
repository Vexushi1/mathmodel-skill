# PR #356 · 逐问依赖准入与证据一致性结构修复计划

> **文档属性：实施设计／待执行，不是 Runtime Authority，也不是代码修复、测试 PASS 或合并批准。**  
> **用户范围裁决：** 保留“明确指定 Q1/Q2/Q3，逐问求解、逐问验收”的工作方式。本轮仅研究和实施参数 selector 一致性、上游证据 read-set 一致性两项；不实施第三条自动选问审查意见。  
> **编制基线：** `main` = `87ed5bbd173c02472a9e85cb09bdc4188d37a8bf`（Skill `11.0.0`）；实施分支 `refactor/v11-question-scoped-mainflow`，PR #356，审计 head `64317321aa8b83fbf1cf18feb415ecdeb5b3fac1`。  
> **参考计划：** PR #355 的 `docs/v11_0_0_postrelease_mainflow_refactor_plan.md`（`79032090aad319f3d15e553e919164ec4943bcb5`），特别是 `0.2、3.3、5、7、11、12、14`。该计划是参考而非执行 Authority；如其历史假设与当前 Schema/SIB 冲突，遵守当前真实实现与正式 Authority。

## 0. 变更简报与授权边界

| 项目 | 约束 |
|---|---|
| 修改主题 | 以**当前问的真实必要上游**为范围，把 selector 逐项核验与“读取即固定证据身份”衔接到既有 Code Delivery 事务 |
| 当前版本 | `11.0.0`，当前未发布主流程 PR #356 |
| 本计划变更等级／目标版本 | `docs`，仅新增本计划，不修改 Skill 版本；未来代码修复为兼容性缺陷修正，整体主流程发布等级需另行裁决 |
| 直接目标 | 解决两个 P2 review：多 selector 错误拒绝；核验后重新哈希造成的 read-set 与实际证据错配 |
| 用户明确不做 | 不修 `question_scheduler.py`，不开发新自动选问行为，不新增用户本地 checker/同步/审计任务，不强制从 Q1 重做至 Qn，不扩大检查到无关小问 |
| 权威事实源 | `core/hsk_core_policy.md`、`core/project_state.schema.yaml`、`core/state_transition_contract.yaml`、`core/runtime_assurance_contract.yaml`、`core/model_approval_contract.yaml`、`core/user_execution_contract.yaml`、`core/output_contract.yaml`、`SKILL_CHANGE_GOVERNANCE.md` |
| 预计直接修改（**实施阶段**） | `scripts/question_dependency_gate.py`；必要时 `scripts/runtime_assurance.py` 中读取时证据收集的内部接口；`scripts/validate_code_delivery.py` 只做已有消费者的 read-set 贯通；现有专项与事务测试 |
| 只检查、不默认改动 | `scripts/semantic_identity.py`、`scripts/conformance_gate.py`、`scripts/project_transaction.py`、`scripts/stage_inputs.py`、`scripts/state_transitions.py`、`scripts/resolve_runtime.py` |
| 禁止改动 | 自动选问器、State/Workbook Schema、全局路由策略、求解器和数据计算模板、MATLAB/LaTeX、真实用户项目、`main`、手工受管索引与 MANIFEST |
| 兼容要求 | SIB 当前多 selector 表达合法；State typed edge 仍是 `(upstream, kind)` 投影；旧 CLI/RUN_CONFIG/RUN_RECEIPT 不变；已批准模型、accepted 工作簿及 stale 不被修复器“补写”或提升 |
| 迁移要求 | 无真实项目自动迁移；旧项目及 legacy untyped 仍按既有只读／保守边界处理 |
| 验收 | GitHub 上先故障复现、再定向测试、再最终 head 的正式 Windows 双版本四分片、MATLAB/LaTeX、生成/静态与适用 Optimization baseline |
| 回滚 | 本计划可独立撤回；实施代码作为 PR #356 内独立审查的提交组可反向 revert；回滚不得撤销已真实发生的用户项目 stale |

**现状说明：** PR #356 在旧 head `64317321…` 的正式 HSK Skill CI `#45048209510` 与 Optimization baseline `#45048209420` 已完成成功；这不代表下列两个缺陷已修复，也不能作为未来新 head 的验收凭据。三条 P2 review 中本轮处理前两条；第三条仍保留为未解决的审查事实。

## 1. 仓库结构与职责分界（依据真实调用链）

### 1.1 四层，不再叠加新流程

| 层 | 现有文件 | 唯一责任 | 本次处理方式 |
|---|---|---|---|
| 用户请求／逐问范围 | `core/workflow_router.yaml`、`scripts/resolve_runtime.py`、`scripts/question_scheduler.py` | 确定问题范围，明确 Qn 优先；选问只读，不授权执行 | **不改**；显式 Qn 回归只验证未被覆盖 |
| 项目语义及状态 | `模型论文框架.md` 内的 SIB、`scripts/semantic_identity.py`、`core/project_state.schema.yaml`、`core/state_transition_contract.yaml` | SIB 保存参数 selector；State 保存 typed 依赖端点、批准身份及 stale | **复用**，不能在 gate 自创第二套依赖定义 |
| 依赖资格消费 | `scripts/question_dependency_gate.py`；`scripts/runtime_assurance.py` | 当前问+必要上游，核对 approved model / validated results / provenance | 两项问题的核心修复位置 |
| 正式代码交付与提交 | `scripts/validate_code_delivery.py`、`scripts/conformance_gate.py`、`scripts/project_transaction.py` | 静态交付、合并原始 read-set、提交前比较和原子 State 事务 | **沿用**已有事务；必要时修正接线，不新增写入器 |

当前真实链路：

```text
用户显式 Qn + 当前 stage
  → 同一 ProjectStateSnapshot（项目级 State、backend、generation）
  → Code Delivery：validate_script() 只读检查
      ↳ question_dependency_gate.inspect(Qn)
          ↳ Runtime Assurance：上游 approved model / accepted workbook 资格
          ↳ Semantic Identity：framework SIB 与 parameter selector
  → update_state() 重新取得当前快照和当前问的必要证据
      ↳ question_dependency_gate.inspect(Qn)
      ↳ CONFORMANCE.merge_read_sets()
      ↳ project_transaction.commit_project_state(expected_file_hashes=...)
  → 交付本问代码；实际 full_fidelity 数值执行仍由用户负责
```

**禁止角色穿透：** Resolver 不授予批准；SIB 不代替数值回执；代码交付不得重新批准模型；依赖 gate 不产生新的全局 stale 引擎；Sync 不重演求解。

### 1.2 关键身份分离

- **SIB `dependencies`：** 保留 `(question, kind, selector)` 的完整数学语义。当前 `validate_semantic_identity` 按这一三元组去重，允许同一 upstream/kind 下的不同 selector。
- **State `depends_on`：** `core/project_state.schema.yaml#/$defs/dependency_kind` 声明 `data/parameter/model/result`；`semantic_identity.dependency_alignment_issues` 比较去除 selector 的 `(question, kind)` 端点。这是传播范围，而不是每个参数的字段级表。
- **批准身份：** 上游 `locked_model_spec` 来自当下 SIB、revision 与显式 Human Approval 的已核验一致，不以 State 自报字符串代替。
- **数值身份：** `validated_results` 与已验收工作簿/必要 03B 由 Runtime Assurance 验证；本轮不把参数 SIB 修复扩大成“任意 XLSX 字段自动提取”能力。
- **文件身份：** `ProjectStateSnapshot` 只保护 State 原始字节；`project_transaction._check_read_set` 保护由消费方提供的**原始期望文件身份**，不能证明一个晚于资格核验才生成的期望哈希是正确的。

## 2. 缺陷 A：多参数 selector 语义被错误压缩

### 2.1 源码事实与反例

当前 `scripts/question_dependency_gate.py` 的 `parameter` 分支收集所有下游声明的 selector，并在已核验上游 SIB 中筛选合法参数，最终要求：

```python
len(selectors) == 1 and len(param_items) == 1
```

这与 `semantic_identity.validate_semantic_identity` 已支持多个不同 `(Q1, parameter, selector)` 的语义冲突：假定 Q2 合法引用 Q1 的 `P1`、`P2` 且两者均有有限数值和非空来源，依赖 gate 仍拒绝 Q2。影响 `validate_script` 与 `update_state` 两个真实 Code Delivery 消费端。

### 2.2 正确判定契约

对指定下游 Qn 和**当前**上游 U 的一条 `kind=parameter` 依赖：

1. 从 Qn 当前结构化 SIB 取得对 U 的所有 `parameter` 声明，得到非空、去重后的 selector 集合 `S`。声明的合法性仍由既有 Semantic Identity 规则负责；State typed endpoint 必须与 SIB 投影一致。
2. 上游 U 必须为当前、真实 file-backed `locked_model_spec`；不能仅凭 `human_model_approval_status: approved` 或旧哈希放行。
3. 对每个 `s ∈ S`，在 U 同一当前 SIB `parameters` 内寻找**唯一** `id == s` 的记录；要求数值类型为 `int/float` 但非布尔值、数值有限、`source` 为非空可追溯字段。
4. **所有** selector 均满足条件才通过；任一 selector 缺失/未知/无效、上游 SIB 失效、框架与 State 对齐冲突，均不能把部分通过当整体 PASS。
5. 空 selector、重复依赖、别名歧义、非数值来源、已失效批准仍拒绝；不修改 `state_transitions` 对 `(U, parameter)` 的下游 stale 传播。
6. 对 `kind=result/model/data` 不应用这段 selector 解析，也不自动把参数值从当前无法证明来源的工作簿中推断出来。

形式上，本轮资格仅要求：`S ≠ ∅` 且 `∀ s∈S, ∃! p∈P_U : p.id=s ∧ finite(p.value) ∧ nonempty(p.source)`，并且 U 的模型身份当前有效。此式只是**已有 SIB 参数来源可核验时**的资格规则，不是给参数新增统计/数值推断机制。

### 2.3 两种实现候选与裁决

- **A（推荐）：** 将当前单个计数判断改为**逐 selector 验证并形成结构化逐项失败原因**，沿用已有 SIB 解析、去重和 approved 身份。无 Schema 变化；代码集中于 `question_dependency_gate.py`。错误信息说明哪个 selector、哪个上游无效。
- **B（否决，除非发现已有强制消费者）：** 给 `State.depends_on` 新增 selector 列，或建立另一套 `parameter_registry`。这会重复 SIB 权威并引入迁移成本，也不解决目前已存在的合法表达被拒问题。

**完成判据：** 两个以上合法参数全部通过；任何一个参数无效时对应 Qn 拒绝，且不改变别的问的 approved/accepted/stale。

## 3. 缺陷 B：资格判断与文件 read-set 的证据错位

### 3.1 当前故障序列（已在源码中存在窗口）

`question_dependency_gate.inspect()` 先通过 `source(upstream)` 调用 `hydrate_project_context`，必要时读取框架 SIB 进行资格判断；直到结尾才调用 `_observed(root, state, tracked)` 为上游文件计算哈希。`current.assert_current` 仅重读 State 字节，不证明框架/工作簿在中途未改变。

```text
t0  State snapshot 固定
t1  上游 framework / accepted workbook 的旧字节 A 被读入并判定通过
t2  其他写入方把某个上游文件改为 B（State 本身不变）
t3  _observed 才把 B 的哈希当作“已验证期望”
t4  事务检查 B==B，可能提交以 A 作出判断的旧资格
```

这是“**证据核验发生在前，期望证据身份捕获发生在后**”的时序错误。单纯在 `_observed` 之后再调用一次 `_check_read_set`，只会复核新的 B，不能关闭漏洞。

### 3.2 结构性目标：读取—资格—绑定是一条链

推荐的目标结构：

```text
同一个 ProjectStateSnapshot
  → 按 Qn + typed incoming edges 确定真正需要的上游角色
  → evidence reader 在首次实际读取每个必要来源时记录
       {canonical_project_relative_path: original_SHA256_or_None}
  → 用被记录的原始字节/同一资格来源做 SIB、批准、工作簿、数据核验
  → 校验过程完成前 recheck 已捕获 read-set 和同一 State snapshot
  → inspect() 返回既有 observed_sources 结构，不新授予资格
  → validate_code_delivery.update_state() 合并其他既有 source read-set
  → 现有 project_transaction 对原始 read-set 再检并提交
```

**不可变要求：** 期望哈希必须绑定“当时实际用于证明通过的字节”，而不是资格结束后的另一轮目录扫描。新增的任何文件证据需要在**消费该文件之前或同一次读时**捕获；缺失文件的 `None` 语义亦应在首次观察时固定。

### 3.3 文件与职责的精确范围

实施前首先列出每种 typed edge 实际触发的读取：

| 依赖 | 最小必要来源 | 不应顺带打开 |
|---|---|---|
| `model` | 上游已批准 SIB、项目 State、当前框架；身份校验实际需要的来源 | 上游无关数值工作簿；其他独立小问文件 |
| `parameter` | 当前下游 selector、上游已批准 SIB 与被选中的参数证据 | 未被引用的其他问的参数/结果；全部项目数据 |
| `result` | 上游当前 `validated_results` 所需的 primary/必要 analysis 工作簿及已有执行身份/数据来源 | 无关兄弟小问的图、论文、工作簿 |
| `data` | 当前声明的真实输入身份；`project_level` 情况下已验收统一预处理工作簿 | 每问全部结果分析/绘图 |
| 当前问自身 | 当前 Qn 的 State、代码 bundle、适用模型/审批/质量门 | 默认把 Q1..Qn 全部作为工作簿检查范围 |

若 `Runtime Assurance` 内部消费源码 helper、analysis comparison 或扩展数据来源，必须在真正读取时将其纳入本次原始观察记录。只枚举 `code/solution_workbook/result_analysis_workbook` 三个名称而忽略实际辅助文件，不具备完整资格证明。反之，**不能为了方便保证完整而遍历所有小问所有文件**。

### 3.4 优先选择的工程方案与保底方案

**推荐方案 A：沿现有证据读取链传播“原始观察记录”。**

- 复用 `runtime_assurance.py` 现有证据验证器、`semantic_identity.framework_semantic_evidence(text)`、`stage_inputs.py` 的真实输入观察和 `project_transaction` 的路径/哈希检查。
- 在现有资格读取路径内部，必要时增加**仅用于当前消费者、默认兼容的只读观察传递**；不得把“资格 PASS”缓存到全局。优先利用既有 `observed_sources` 输出结构以及 `conformance_gate.merge_read_sets / assert_observed`。
- 让读取的原始 framework 文本与用于 SIB 解析的文本一致；对于工作簿、源码依赖和预处理文件，读取时的具体哈希必须进入同一集合。最后直接把这一集合传给当前 `inspect` 的既有返回接口。
- `update_state` 继续原封不动使用一份 `expected_file_hashes` 和 `project_transaction.commit_project_state`；如有必要，只调整现有 `CONFORMANCE.merge_read_sets` 的衔接，不另建事务系统。
- 必须检查现有纯只读调用方对额外返回字段/参数的兼容性；若不能保证默认行为不变，则采用保底方案。

**保底方案 B：预先捕获必要来源，核验后比较同一预捕获集合。**

- 只允许在能够**证明完整列出当前资格所读取的必要路径**的前提下使用。
- `_observed` 的作用调整为资格前的原始捕获，资格后、交付前检查原集合。动态读取出的新来源必须在读取前追加捕获，否则 fail-closed。
- 不能通过“先检查→最后重新计算哈希→再检查一次”的三段式伪闭环替代真实读集。

方案选择须在 R0 源码调用审计后记录：**覆盖哪些实际来源、为何无需新增字段、静态读取与事务写入如何使用同一原始证据、哪些只读消费者没有改变**。不得为做“架构修复”硬新增独立 Snapshot 类、全局缓存、并行审批器或第二个 State writer。

### 3.5 安全性、异常与竞争写入语义

- 路径需是规范项目相对 POSIX 路径；别名、符号链接、越界、重复/大小写歧义不能绕过现有 `project_transaction._guarded_path`/输入路径安全策略。
- 对当前资格必须存在的文件：缺失即明确阻断；对当前声明需要观察“预期不存在”的文件，记录 `None`，若随后出现也须冲突；不能把非必要文件设为强制存在。
- 初次读取后证据变化、同 generation 的 State 字节变化、提交前变化，都要拒绝本次**新的**代码交付；不得修改现有 accepted 结果或自行触发模型重批准。
- 项目级共享预处理仅在实际依赖时加入 read-set；不重新验收不相关兄弟小问的全部产物。
- 沿用现有事务的**乐观一致性**边界：能识别前后观察与提交时的漂移，不虚称对不合作的外部进程具备操作系统级全文件原子快照保证。
- 保持单次有效证据的读取成本有界；不按每个 selector 重新打开/解析整个框架或每个上游工作簿。

## 4. 当前用户流程的“不改变”验收

用户工作方式：

```text
项目级逐字审题、登记全部必需小问
  → 用户明确“现在做 Q1”
  → Q1 模型设计、双审、本人明确批准
  → Q1 主求解代码交付 → 用户本地完整执行
  → 返回 Q1 工作簿 → 当前问结果验收/必要深化/绘图
  → 用户明确“现在做 Q2”……
  → 全题论文、终审与提交仍按全项目
```

不改变以下合同：

1. 用户明确说 `Q2` 就只围绕 Q2 和它真实必要的上游做交付资格检查。Q2 被阻断必须说明 Q2 的具体缺项，不切换成 Q3。
2. 选问器的默认/自动推导代码本轮**不动**；不引入新的自动选号、等待点、任务优先级或用户确认。`resolve_runtime.py` 仍只作现有选择，执行准入属于 Code Delivery。
3. 完整 State schema、项目唯一 solver backend、共享预处理决策、generation、模型批准及全图 typed stale 仍有效；但无关 Q3 缺图/缺结果不能阻断 Q2 的无关依赖路径。
4. unchanged/current 的模型不重做 Human Model Approval；每个已 accepted 的结果不因“我们新增了一个检查”自动作废。
5. 数值代码仍由用户运行，系统不要求用户执行新 checker、提交额外审计回执或迁移项目。正式验收仍以既有工作簿、回执与当前项目证据为准。

**明确未完成事项：** PR #356 另有一条 P2 review 指向 `scripts/question_scheduler.py` 的自动选问阻断传播；该问题**仍存在、未修复、不得标记为 resolved**。本轮不会把它纳入代码范围，也不会宣称三条 review 均已关闭。将来是否影响合并，须按实际正式审查和用户坚持显式逐问的使用边界另行裁决；不以跳过审查伪造安全结论。

## 5. 分阶段施工卡（同一 PR 内、小提交、不得顺手扩大）

### R0 — 影响面与真实读取路径审计（不修改运行时）

- 以最新 `main`/PR #356 head、当前 Authority、测试为唯一基线，明确 `parameter/result/model/data` 的真实读取调用图和路径清单；标记哪些读取已经有原始 read-set、哪些仅有事后 hash。
- 把两个独立 P2 失效场景固定为最小三问合成项目，观察 `validate_script`（只读）与 `update_state`（写入）各自的行为；无用户赛题数值执行。
- 盘点 `hydrate_project_context` 的 SIB、accepted XLSX、代码 bundle、data/auxiliary、comparison 取读，确认如何在不遍历无关小问的前提下正确捕获实际消费的字节。
- 记录采用 3.4 哪条方案及技术理由，并核对相邻 PR/文件重叠；不因为旧计划假设“没有 selector”而新增 State Schema。

**进入 R1 条件：** 精确复现当前缺陷、定义实际 read-set 覆盖范围。无法完整确认资格输入时停止**该资格的写入实现**，先补读取证据设计。

### R1 — 参数 selector 语义归一（限消费层）

- 先添加合法 `P1+P2` 正例和 `P2` 无效反例，验证旧 gate 的真实错误。
- 在 `question_dependency_gate.py` 中将 selector 校验与 SIB 原有投影一致化；严格逐项匹配和有限来源。
- 只检查已有 approved/current 上游 SIB，不新定义参数格式、第二份模型真相或独立审批。
- 保留 `model/result/data/legacy` 的原错误/阻断语义；复核同 Qn 多 selector 不导致重复资格读取。

**验收：** 参数全部合法时通过；空/未知/重复/失效批准/非有限/空来源拒绝；下游 State/model/stale 无额外写入。此阶段本身不是整个 PR 的正式可合并状态。

### R2 — 文件身份捕获与资格绑定结构修复（核心阶段）

- 先以确定性故障注入复现“旧 A 资格、晚捕 B read-set”的竞态，锁定受影响文件类型。
- 按 3.4 执行**捕获、资格、复核、传递**的一条链。原始 byte/hash observation 由真正的来源读取者产生，避免消费者重复采集后续版本。
- `inspect()` 输出沿用当前 `observed_sources` 结构，包含当前本次消费的项目文件及必要 skill 来源；捕获失败或冲突必须有明确具体路径。
- `validate_code_delivery.update_state` 继续使用 `CONFORMANCE.merge_read_sets`、既有 `assert_observed` 和 `project_transaction.commit_project_state(expected_file_hashes=...)`；如多个消费者对同一路径观察到不同 SHA，必须报冲突而非取最后值。
- 对 `validate_script` 保持只读；不得让一次静态通过被持久化成后续 write 的永久 PASS。正式写入必须在自己的新快照上重新资格确认并绑定读集。

**验收：** 框架/上游 workbook/必需代码或输入在读取期间、核验之后、事务提交前变化均不产生新的 code-delivered 权限；无变化时正常交付。除当前 Qn 必要来源外不额外扩大观察。

### R3 — 消费者与跨问非回归

- 覆盖 `validate_script`、`update_state`、`project_transaction`、Runtime Assurance、SIB/State alignment 和 typed stale。
- 证明 Q2 的参数/结果资格不会要求 Q3 的代码或工作簿；Q2 上游模型有效但数值结果未完成时，`model` 依赖不被误当 `result`。
- 证明 Q1 变化只按原 State Transition Authority 失效真正受影响下游，不自动失效独立 Q3。
- 保留既有合法 Q1-only/Q2-only 正例，避免反复全项目扫描造成性能和流程退化。

### R4 — GitHub-only 冻结与验收

- 本分支在开发期间保持 Draft；每个源提交只改有关文件，并等待 GitHub `refresh-generated` 更新受管生成物。
- 针对生成后最终 head 跑已有 Windows 定向模块：`test_question_dependency_gate`、`test_question_runtime_integration`、`test_project_transaction_read_set`、`test_project_state_read_snapshot`、`test_v900_semantic_governance` 及确有调用受影响的 Code Delivery/Runtime Assurance 测试。
- 定向成功后才转 Ready；最终 head 必须完成 Windows Python 3.10 与 3.14 各四分片的全量回归和汇总、MATLAB R2024b native、LaTeX/production attestation、Generated/Static/Figure，以及适用 Optimization baseline。
- 核对每个正式 job 的 checkout commit 与结果，并逐条处理前两条 review thread。`question_scheduler.py` 的第三条 review 不得假称已修复/关闭。
- 有任何新 source 或 bot head，先重核对应检查，不复用旧 head PASS；合并和版本另待明确授权。

## 6. 具体回归矩阵（预登记，实施时逐项落地）

| ID | 输入/故障场景 | 预期判定 | 原有/拟落测试 |
|---|---|---|---|
| S01 | Q2 消费 Q1 当前合法 P1、P2 | PASS，且每个 selector 均核验 | `test_question_dependency_gate.py` |
| S02 | 合法 P1、缺失 P2 | FAIL，指出 P2 | 同上 |
| S03 | 一个 selector 非数值/布尔/NaN/Inf | FAIL，不因其他 selector 合法而放行 | 同上 |
| S04 | 其中一个参数 `source` 空缺 | FAIL | 同上 |
| S05 | Q2 SIB 缺 selector / 重复 selector / State endpoint 冲突 | FAIL；沿用原 SIB/State 规则 | 同上 + `test_v900_semantic_governance.py` |
| S06 | Q1 模型批准 stale，但参数看似完整 | FAIL，不提升 `locked_model_spec` | 同上 |
| S07 | Q2 只依赖 Q1/model；Q1 没有 validated result | 不因数值缺失误拒 | 同上 |
| S08 | Q2 依赖 Q1/result；仅 primary accepted，必要 03B 未完成 | FAIL | 同上 |
| B01 | SIB 资格读到 A；框架随后变 B，State 不变 | FAIL；不能把 B 作为 A 的证明 | `test_question_dependency_gate.py` + 故障注入 |
| B02 | accepted workbook 资格读到 A；随后替换 B | FAIL | 同上 |
| B03 | 依赖源码 bundle/helper 读取期间变化 | FAIL | Code Delivery/Stage Code 相关测试 |
| B04 | 项目级预处理工作簿/必要 data 变化 | FAIL，报告当前必要数据 | `test_question_runtime_integration.py` |
| B05 | 期望不存在的必需来源突然出现；已存在来源被删 | FAIL，含存在性身份 | `test_project_transaction_read_set.py` |
| B06 | 已读取路径变 symlink、大小写别名或越界 | FAIL，不通过别名接受 | 同上 + 依赖 gate |
| B07 | State 同 generation 但原始字节变化 | FAIL，要求重取快照 | `test_project_state_read_snapshot.py` |
| B08 | 资格结束到 `commit_project_state` 之间的文件漂移 | FAIL，无新 `state_generation` / code-delivered | `test_project_transaction_read_set.py` |
| B09 | 多消费者对同一文件形成不同原始哈希 | FAIL，不能后写覆盖先读 | `conformance_gate.merge_read_sets` 相关用例 |
| W01 | 显式 Q2、独立 Q3 缺工作簿/图表 | Q2 本轮不被 Q3 阻断，也不自动切换 Q3 | `test_question_runtime_integration.py` |
| W02 | 合法 Q2 输入全部未变，重复只读检查 | 结果一致；不触发额外 State 写入/人工批准 | 同上 |
| W03 | 真实已 accepted 旧项目仅阅读兼容 | 不强制本轮 Schema/回执迁移 | 现有 compat 回归 |
| W04 | 参数来源明确但超出现有 SIB 协议（例如非注册工作簿字段） | 明确未核验，不“猜”参数，不隐性扩展协议 | `test_question_dependency_gate.py` |

**故障注入必须有明确时间点：** (a) 来源读取前，(b) 首次来源读取后/资格结束前，(c) 资格后 read-set 合并前，(d) 写入事务准备后/提交前。只凭普通正例或笼统的 `assertRaises` 不算覆盖 B01/B02。

## 7. 文件级交付清单与不改理由

| 文件 | 阶段 | 预计动作／理由 |
|---|---|---|
| `docs/v11_question_dependency_evidence_integrity_plan.md` | 当前 | **唯一新增计划正文**；非 Authority，不授予门禁 |
| `scripts/question_dependency_gate.py` | R1/R2 | 修复逐 selector 资格、原始证据观察与结果回传 |
| `scripts/runtime_assurance.py` | R2 条件触发 | 若只有在这里才能取得被实际消费的字节/原始哈希，则增加默认兼容的只读证据传递，不另建 qualification 引擎 |
| `scripts/validate_code_delivery.py` | R2 条件触发 | 既有静态与事务消费者接线；保留双边界各自 current 资格 |
| `scripts/conformance_gate.py` | 原则不改 | 已有 merge/assert 机制；无需复制 |
| `scripts/project_transaction.py` | 原则不改 | 已有 guarded read-set、generation 与提交前复核，漏洞在调用方提供了错误期望 |
| `scripts/semantic_identity.py` | 原则不改 | 三元组和多 selector 已合法；问题是 gate 消费方式 |
| `core/project_state.schema.yaml`、`core/state_transition_contract.yaml` | 不改 | State edge 和 typed stale 的定义无需第二份 selector |
| `scripts/question_scheduler.py`、`scripts/resolve_runtime.py` | **不改** | 用户拒绝本轮自动选问优化；保持显式 Qn 权限 |
| `scripts/sync_project.py` | 不改 | 本轮不是同步器、框架自动修复或批量迁移 |
| `tests/test_question_dependency_gate.py` 等第 6 节指定测试 | R0–R3 | 先证明两类缺陷，再验证修复与负例 |
| `MANIFEST.sha256`、索引、full-reading 生成物 | 只允许 GitHub bot 更新 | Agent 不手工改写 |

对新增的接口、Helper 或测试文件，只有在现有文件职责确实无法安全表达而**有可复现证明**时才允许增补，并在本计划记录必要性、影响范围与回滚。不因“工程化”而引入全局服务层、第二套 Schema 或缓存 gate PASS 的机制。

## 8. 质量、时间成本与停止条件

- **必须阻断：** 被用于授权的原始证据发生变化、任一参数 selector 无合法来源、缺少当前 approved/accepted 身份、State snapshot 漂移、路径越界/别名、正式代码与数据身份不符。
- **不应阻断：** 当前问与无关兄弟问没有真实依赖，仅缺图/论文/代码；仅对未使用参数的上游字段做额外扫描；已有 current 已批准模型的重复人工双审。
- **不得伪降级：** 不把模型批准、validated_results、source bundle、用户本地 full_fidelity、必要 03B、typed stale 或提交前 read-set 降成 warning。
- **性能边界：** 用文件级必要来源数和实际核验次数解释新增成本，不设置“每个 selector 重新核验所有上游”的算法；正式 wall time/runner time 以 GitHub 真实 run 为准，不凭局部微基准夸大效率。
- **停止并重新审查范围的条件：** 发现目前已验收结果依赖一种未建模的工作簿参数提取协议；Runtime Assurance 无法提供真实消费来源的稳定观察；修复需要破坏 Schema/CLI；现有开放 PR 与本轮拟修改权威文件发生新的未合并内容重叠；新反例证明必须处理的关键缺陷不在批准范围。不得静默扩大。
- **自动选问 review 的处置：** 第三条 P2 保留为未关闭的 review，单独说明在本轮风险登记中。既不能为使 PR 看似干净而静默关闭，也不能借此本轮擅自改 scheduler。真正合并前单独作出处置和授权裁决。

## 9. 先做计划，再做代码：当前完成状态

- [x] 从 `main` 读取 `core/bootstrap.yaml`、`SKILL_CHANGE_GOVERNANCE.md`，确认 Skill `11.0.0`、`main` 与 PR #356 原 head。
- [x] 对照 PR #355 原主计划和本次两条具体 P2 review；读取现有 Runtime Assurance、Semantic Identity、State/Transition、Code Delivery、Transaction 的相关源码与合同。
- [x] 遵照用户裁决把自动选问修复排除，保留显式 Qn 逐问求解与必要上游限制。
- [x] 形成结构性修复范围、工作包、原始 read-set 设计、故障注入和回归矩阵。
- [ ] R0 最小失败反例在 GitHub 执行并获得真实日志。
- [ ] R1/R2 源码修复、R3 跨消费者回归。
- [ ] GitHub bot 生成后的最新 head 定向与正式验收。
- [ ] 两条目标 review 依据真实修复结果处置；第三条仅记录未解决，不声称完成。
- [ ] 版本、合并批准、合并后 main CI 与发布收尾。

**本计划仅约束后续被授权的实现工作，不声称已执行任何未标记的测试、任务数值求解、项目迁移、正式交付或审查通过。**
