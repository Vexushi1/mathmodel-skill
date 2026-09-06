---
status: planning
baseline_skill_version: 8.7.4
baseline_main_commit: 3d4b25403808e99892aeefdfaf791d00675765bd
plan_scope: semantic_identity_state_transitions_runtime_assurance_sync_refactor
change_class: multi_pr_program
candidate_final_version: 9.0.0
branch_protection_issue_92: out_of_scope_due_to_platform_permission
---

# HSK MathModel Skill：语义身份、状态传播与运行时可信性整体重构计划

> 本文是实施蓝图，不是新的运行时 Authority。任何真正改变 Skill 行为的规则必须落回现有或本计划明确指定的权威事实源，并遵守 `SKILL_CHANGE_GOVERNANCE.md` 的单一事实源、独立分支、单主题 PR、真实测试与生成文件规则。

## 0. 修改简报

**修改主题：** 语义身份、Model Approval 绑定、artifact identity、stale propagation、runtime assurance、项目同步事务性、竞赛写作运行时解耦与 `sync_project.py` 职责收敛。

**当前版本：** `8.7.4`

**候选最终版本：** `9.0.0`。但禁止一次性大爆炸升级；先用 patch/minor PR 建立兼容层和验证能力，只有在删除旧字段、旧 alias 或改变外部 Schema/CLI 时才进入 major 清理。

**变更等级：** 多 PR 迁移计划，包含 patch / minor / major 三个阶段。

**直接目标：**

1. `locked_model_spec` 必须绑定当前磁盘上的真实模型语义，而不是仅由 `project_state.yaml` 内部字段互相相等来自证；
2. 将“数学语义身份”与“Markdown 文字表现”分离，使纯措辞/排版调整不再误触发模型重新审批；
3. 消除 `model` / `model_hash` / `semantic_hash` / `primary_code_sha256` 等命名层次混淆；
4. 建立唯一 stale transition Authority，消除多个脚本重复维护失效层集合；
5. 真正使用 `depends_on.kind = data / parameter / model / result` 做有类型的下游失效传播；
6. 让 `state/project_state.yaml`、`模型论文框架.md`、`sync_report.yaml` 的写入具备可恢复事务语义和并发覆盖检测；
7. 把 CUMCM 特判从通用 Resolver 下沉到 competition profile；
8. 在行为稳定以后拆分过胖的 `scripts/sync_project.py`，降低规则漂移风险；
9. 全程保持旧项目只读兼容，并为需要重新进入模型设计/求解的旧项目提供显式迁移路径。

**明确不做：**

- 不处理 GitHub Issue #92 的 `main` Branch Protection；该项因平台/账户权限限制继续作为治理债务记录，不允许通过修改 Skill 代码“模拟 Branch Protection”；
- 不在本计划中扩充新的数学模型库、知识图谱、答辩 Agent、竞赛评分 Agent；
- 不改变 Python 主求解 / 结果深化分析 / MATLAB 正式绘图的既有职责边界；
- 不修改 workbook 数值事实原则，不让 Markdown 或 state 代替 accepted workbook；
- 不让 `legacy/` 成为活动代码依赖；
- 不手工编辑 `MANIFEST.sha256`、`HSK_*INDEX*` 等生成文件；
- 不把所有修改塞进一个巨型 PR。

**当前权威事实源：**

- 启动与 Authority 指针：`core/bootstrap.yaml`
- 修改治理：`SKILL_CHANGE_GOVERNANCE.md`
- 项目状态结构：`core/project_state.schema.yaml`
- Model Approval：`core/model_approval_contract.yaml`
- Runtime Assurance：`core/runtime_assurance_contract.yaml`
- 语义变更检测实现：`scripts/validate_semantic_governance.py`
- Model Approval 校验：`scripts/validate_model_approval.py`
- 项目同步：`scripts/sync_project.py`
- 代码交付校验：`scripts/validate_code_delivery.py`
- Runtime Resolver：`scripts/resolve_runtime.py`
- 竞赛 profile：`config/competition_profiles.yaml`
- 运行时 artifact graph：`core/module_manifest.yaml`

**禁止直接触碰：**

- `main`；
- `legacy/`；
- 与当前重构无关的 task packs、LaTeX 模板、MATLAB 图形风格、数值验证阈值；
- 生成文件的手工内容。

**兼容性要求：**

- v8.7.x 当前项目可以继续只读审查；
- 旧项目若只查看历史结果，不强制追溯迁移；
- 旧项目一旦重新进入 `model_design / data_preprocessing / solve_validate`，必须迁移到新的 semantic identity / approval binding；
- 兼容层必须有明确退出条件，不能永久双写。

**迁移要求：**

- 先加读兼容，再切新写入，再停止旧写入，最后才删除旧字段；
- 每一次 Schema 变更都必须有 fixture、migration test 和 rollback path；
- 不允许通过全仓库字符串替换完成状态字段迁移。

**基础验收：**

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/generate_indexes.py --check
```

并按阶段追加专项测试。任何失败都不得通过降低断言、删除测试、加入宽松例外来“修复”。

**回滚方式：** 每个实现 PR 必须可独立 revert。兼容阶段不得要求不可逆的数据迁移；major 删除动作只能在至少一个稳定兼容窗口后执行。

---

# 1. 基线事实与当前实现问题

本节只记录已经在 `main@3d4b254` 中核实的实现事实。

## 1.1 Runtime Assurance 对 locked model 存在 state self-attestation

当前 `scripts/runtime_assurance.py::_semantic_lock_evidence()` 的核心判断是：

- `model_challenge_status == passed`；
- `human_model_approval_status == approved`；
- `approved_semantic_revision == semantic_revision`；
- `approved_semantic_hash == semantic_hash`。

满足后，返回：

```text
status = verified
expected_sha256 = semantic_hash
actual_sha256 = semantic_hash
```

这里的 `actual_sha256` 没有重新从当前 `模型论文框架.md` 读取并计算；因此它证明的是 state 内部一致，而不是“当前磁盘语义 = 已批准语义”。

### 风险场景

```text
A. 当前框架语义 = A
B. state.semantic_hash = H(A)
C. user approval 绑定 H(A)
D. 框架被直接修改为 B
E. semantic validator/sync 尚未执行
F. resolve_runtime(project_root=...) 先 hydrate state
G. locked_model_spec 仍可能被 runtime assurance 视为 verified
```

这必须先修，因为后续所有更复杂 semantic identity 设计都依赖 runtime assurance 的可信根。

---

## 1.2 当前 `semantic_hash` 实际是 Markdown 片段文本 Hash

`validate_semantic_governance.py` 当前从每问 `#### 当前模型口径` 到 `#### 结果摘要` 之间截取 Markdown 原文，然后对规范化换行后的文本做 SHA-256。

因此：

```text
“本模型以系统总成本最小为目标”
```

改成：

```text
“模型目标为最小化系统总成本”
```

即使数学模型没有变化，Hash 仍会变化。

但 `core/model_approval_contract.yaml` 已明确规定：

- `wording_only_change`
- `markdown_formatting`
- `caption_only_change`
- `formula_numbering_only_change`
- 不改变语义的 LaTeX 文件拆分

不应该使 approval stale。

因此当前“合同语义”和“实现判定”存在结构性张力。

---

## 1.3 artifact identity 命名混淆

当前 `core/project_state.schema.yaml` 同时存在：

```text
semantic_hash / validated_semantic_hash
model_hash / validated_model_hash
artifact_hashes.model
primary_code_sha256
analysis_code_sha256
```

但 `scripts/sync_project.py::_snapshot_question()` 实际写入：

```python
artifact_hashes["model"] = sha256_file(primary_code)
```

也就是说 `artifact_hashes.model` 实际表示 primary Python implementation，而不是数学模型身份。

这与仓库反复强调的：

```text
Model != Solver != Implementation
```

不够一致，容易让维护者在 stale / approval / artifact 校验中误用字段。

---

## 1.4 stale rules 已经出现多处复制并且不完全一致

至少当前三处活动脚本分别定义 stale layer 集合：

- `scripts/validate_semantic_governance.py`
- `scripts/sync_project.py`
- `scripts/validate_code_delivery.py`

其中 `PRIMARY_STALE_LAYERS` 并不完全相同；例如 semantic/sync 路径包含 `model`，code-delivery 路径的 primary stale 集合不包含同名层。

当前项目治理规则要求同一硬规则只有一个 Authority，因此 stale transition 应从散落常量升级为统一状态转换机制。

---

## 1.5 `depends_on.kind` 已建模，但下游传播基本退化为无类型图

Schema 已经定义：

```yaml
depends_on:
  - question: Q1
    kind: data | parameter | model | result
```

但是 `validate_semantic_governance.py::_dependency_questions()` 只抽取 `question`，`kind` 被丢弃；随后 `_dependent_closure()` 对所有依赖统一传播。

这会把本应不同的情况统一处理：

- 依赖上游模型结构；
- 只读取上游最终结果；
- 共享某个参数；
- 共享数据。

结果是下游容易过度 stale，失去局部重算能力。

---

## 1.6 `sync_project --write` 多文件写入不是一个可恢复事务

当前写入顺序包含：

1. 直接更新 `模型论文框架.md` header；
2. 计算 framework hash；
3. 直接写 `state/project_state.yaml`；
4. 直接写 `sync_report.yaml`；
5. 再做写后 hash 自检。

若进程在第 1 步后、第 3 步前异常终止，可能形成 framework/state 跨文件不一致。

此外当前没有显式 `state_generation` / compare-and-swap 机制阻止两个会话基于同一旧 state 互相覆盖。

---

## 1.7 通用 Runtime Resolver 内有 CUMCM 专用分支

`scripts/resolve_runtime.py` 当前直接定义：

```text
COMPACT_WRITING_INTENTS
COMPACT_WRITING_COMPETITIONS = {cumcm}
CUMCM_WRITING_PACKAGE_INTENTS
```

并在 `_apply_v8_writing_runtime()` 中写死 CUMCM Template-First package 与 manifest 路径。

当前这样做有历史合理性，但继续扩展 MCM/ICM、Diangong 等竞赛的 Template-First runtime 时，会让通用 Resolver 逐步变成 competition-specific if/else 集合。

竞赛差异本来已经有 `config/competition_profiles.yaml` Authority，因此该策略应逐步配置化。

---

## 1.8 `sync_project.py` 已经承担过多职责

当前文件同时承担：

- 项目数据源发现；
- artifact hash；
- workbook 检查；
- Python 主/分析代码 identity；
- MATLAB 静态职责检查；
- figure export 检查；
- stale propagation；
- framework header 写入；
- LaTeX/DOCX/submission 检查；
- project state 写入；
- sync report 写入。

本次不先“为了优雅”拆文件；必须等 identity / stale / transaction 规则稳定后再拆，否则会把行为重构和结构重构混在一起，增加回归风险。

---

# 2. 重构硬不变量

整个计划必须遵守以下不变量。任一阶段违反，立即停止并回滚该 PR。

## I1. 三类 Truth 继续严格分离

```text
模型论文框架.md       = 人/Agent 可读的语义事实源
state/project_state   = 生命周期/机器状态事实源
accepted workbooks    = 数值事实源
```

新 semantic identity 只能用于“证明当前语义身份”，不能让 state 变成第二套完整模型描述。

## I2. Model Approval 绑定的是数学语义，不是 Markdown 文案

纯措辞、排版、caption、公式编号、文件拆分不能触发重新锁模。

## I3. 机器不能声称比证据更强的 verified

任何 `verified` 状态必须有可复核的当前 evidence；state 内字段互相相等不够。

## I4. 旧项目只读兼容，新写入逐步单轨化

兼容策略采用：

```text
read old + read new
→ write new + read old/new
→ stop writing old
→ migration window
→ remove old in major
```

禁止长期双写两套真相。

## I5. stale transition 只能有一个 Authority

脚本不得各自维护一份 `PRIMARY_STALE_LAYERS`。

## I6. typed dependency 默认保守

如果旧项目只有字符串依赖，或 `kind` 缺失/不可判断，按“更保守的 legacy invalidation”处理，不能为了减少重算而冒险保留可能失效的结果。

## I7. 结构重构晚于行为稳定

先测试和修规则，再拆 `sync_project.py`。不在同一 PR 同时改字段语义、状态传播和文件组织。

## I8. 生成文件永远由生成器维护

源文件修改完成后运行 `scripts/generate_indexes.py`；禁止手改 hash。

---

# 3. 目标架构

## 3.1 Semantic Identity：采用“Framework 内嵌结构化身份块”，不建立第二份外部模型真相

### 选择

在每问 `模型论文框架.md` 的“当前模型口径”区域内增加一个机器可读的 **Semantic Identity Block（SIB）**。

示意：

```markdown
#### 当前模型口径

<!-- HSK_SEMANTIC_IDENTITY_BEGIN Q1 -->
```yaml
schema_version: 1.0.0
question: Q1
research_object: ...
data_scope:
  - ...
variables:
  - id: x_i
    role: decision
    domain: nonnegative_integer
    unit: vehicle
parameters:
  - id: c_i
    unit: CNY
assumptions:
  - id: A1
objective:
  sense: minimize
  expression: C(x)
constraints:
  - id: C1
    expression: ...
preprocessing_decision: question_local
algorithm_semantics:
  family: MILP
  decomposition: none
dependencies:
  - question: Q0
    kind: data
```
<!-- HSK_SEMANTIC_IDENTITY_END Q1 -->

其余说明性 prose...
```

### 为什么不单独创建 `model_ir.yaml`

单独文件会天然产生：

```text
模型论文框架.md 语义
vs
model_ir.yaml 语义
```

两份真相。把 SIB 内嵌在 framework 中，可以继续保持“framework 是模型语义事实源”，同时让机器拥有稳定身份表示。

### SIB 不是完整模型 AST

第一版只记录**足以判断 approval 是否失效的语义维度**，不尝试自动证明两个任意数学表达式代数等价。

例如：

```text
x+y 与 y+x
```

如果 SIB 的表达式字符串真的变化，第一版可以保守视为 identity change；目标只是消除 prose wording 的误报，而不是实现符号代数定理证明器。

### Canonicalization

SIB Hash 必须使用稳定 canonical serialization：

1. UTF-8；
2. mapping key 稳定排序；
3. 明确哪些 list 是集合语义，按稳定 `id` 排序；
4. 明确哪些 list 顺序具有语义，不得自动排序；
5. 去除 YAML 注释和无关格式；
6. canonical JSON/YAML 后 SHA-256；
7. canonicalizer 必须有 fixture 测试，不能依赖 Python dict 偶然顺序。

推荐新字段：

```yaml
semantic_identity_schema_version: 1.0.0
semantic_identity_hash: <sha256>
validated_semantic_identity_hash: <sha256>
approved_semantic_identity_hash: <sha256>
semantic_text_hash: <sha256>
```

保留：

```yaml
semantic_revision
validated_semantic_revision
approved_semantic_revision
```

迁移期旧字段：

```yaml
semantic_hash
validated_semantic_hash
approved_semantic_hash
```

只作为 v8 compatibility alias，不再承担长期 identity Authority。

---

## 3.2 Runtime Assurance：从 state equality 升级为 evidence-backed semantic verification

新的 locked model 证据链必须是：

```text
当前模型论文框架.md
      ↓ parse SIB
current_semantic_identity_hash
      ↓ compare
state.semantic_identity_hash
      ↓ compare
state.validated_semantic_identity_hash
      ↓ compare
state.approved_semantic_identity_hash
      +
challenge=passed
approval=approved
revision binding current
```

只有全部通过才能：

```text
locked_model_spec = verified
```

Runtime evidence 至少返回：

```yaml
artifact: locked_model_spec
source: framework+project_state
scope: Q1
status: verified | stale | unapproved | legacy_review_required | malformed
path: 模型论文框架.md
expected_sha256: <approved identity hash>
actual_sha256: <current identity hash>
identity_schema_version: 1.0.0
```

### 迁移前临时修复

在 SIB 尚未上线前，先用当前 legacy text-hash 算法重新读取 framework 做现场比对，修复 state self-attestation。该 patch 不等待 v9。

---

## 3.3 Artifact Identity：数学语义、代码实现、数值证据三层命名彻底分开

目标状态：

```text
Semantic identity
  semantic_identity_hash

Implementation identity
  artifact_hashes.primary_code
  artifact_hashes.analysis_code

Numerical evidence identity
  artifact_hashes.solution_workbook
  artifact_hashes.result_analysis_workbook

Presentation evidence
  artifact_hashes.matlab_script
  artifact_hashes.figure_bundle
  artifact_hashes.framework
```

### v8 compatibility

旧：

```yaml
artifact_hashes:
  model: <primary code hash>
```

新版本先：

- **读** `model` 时映射为 legacy `primary_code`；
- **写** 新项目时写 `primary_code`；
- major 前不直接删除旧读取能力；
- 禁止同一新项目同时写 `model` 和 `primary_code` 两个可独立变化的值。

`model_hash / validated_model_hash` 必须先做全仓库引用盘点：

- 如果只是 legacy primary-code identity，迁移后废弃；
- 如果存在独立、明确的语义职责，重命名为不会和数学模型混淆的字段；
- 在引用盘点完成前禁止直接删除。

---

## 3.4 单一 State Transition Engine

### 新 Authority

建议新增：

```text
core/state_transition_contract.yaml
```

理由：`project_state.schema.yaml` 应继续负责“状态长什么样”，而 stale/transition 是“状态如何变化”的行为规则；把 transition matrix 塞进 JSON Schema 会混淆结构验证与行为 Authority。

同时更新：

- `core/bootstrap.yaml` Authority 指针；
- `SKILL_CHANGE_GOVERNANCE.md` Authority 表；
- `core/module_manifest.yaml` 必要 dependency；
- `tests/test_authority_single_source.py`。

### 共享实现

新增纯逻辑模块：

```text
scripts/state_transitions.py
```

禁止它直接读写磁盘。输入 `event + current_state + dependency_graph`，输出 transition result。

建议事件：

```text
semantic_identity_changed
primary_code_changed
analysis_code_changed
data_changed
solution_workbook_changed
analysis_workbook_changed
matlab_script_changed
figure_bundle_changed
paper_fragment_changed
```

### Own-question transition 示例

`semantic_identity_changed(Q1)`：

```text
model_challenge_status -> stale
human_model_approval_status -> stale
primary execution -> pending
analysis execution -> pending
result_quality -> pending
result_analysis -> pending
result_summary -> stale
primary_code -> stale
solution_workbook -> stale
analysis_code -> review_required/stale according to implementation dependency
result_analysis_workbook -> stale
matlab_script -> stale
figure_bundle -> stale
framework-dependent fragments -> stale
```

`primary_code_changed(Q1)`：

```text
不自动使 mathematical approval stale
solution_workbook -> stale
result_analysis_workbook -> stale
matlab_script -> stale
figure_bundle -> stale
result text fragments -> stale
```

`analysis_code_changed(Q1)`：

```text
primary solution remains valid
analysis workbook -> stale
analysis-backed figures/text -> stale
```

关键要求：模型 approval 和 implementation freshness 不再共用含混的 `model` layer。

---

## 3.5 Typed Dependency Propagation

依赖边：

```text
(Q_source, Q_target, kind)
```

而不是只保留：

```text
(Q_source, Q_target)
```

### 初始安全矩阵

| 上游变化 | 下游 `kind=model` | `kind=result` | `kind=parameter` | `kind=data` |
|---|---|---|---|---|
| semantic identity 改变 | 下游 semantic review/approval stale | 下游执行/结果 stale；模型 approval 默认保留 | 仅当暴露参数定义/值变化时传播到消费者 | 数据口径变化时传播 |
| accepted result 改变 | 只有显式模型依赖结果结构时处理 | 下游重新执行，代码可保持 current | 参数提取者重算 | 通常不传播 |
| data identity 改变 | 按模型是否绑定该数据口径判断 | 结果消费者按需 | 参数消费者重估 | 下游执行与数据相关 evidence stale |

### 保守规则

- 旧字符串依赖：按 legacy full invalidation；
- 未知 `kind`：blocking 或保守 full invalidation，禁止默认为“不影响”；
- dependency cycle：validator 必须报告，不能无限传播；
- 传播结果必须可解释：报告“由哪条 edge、哪种 event 导致 stale”。

### Result-level 精细化（第二阶段，可选）

只有基础 typed propagation 稳定后，才考虑：

```yaml
depends_on:
  - question: Q1
    kind: result
    selector: recommended_solution.alpha
```

第一版不要直接上 field-level dependency，避免过度复杂。

---

## 3.6 项目写入事务与并发保护

### 新 helper

建议新增：

```text
scripts/project_transaction.py
```

职责：

- `atomic_write_text(path, content)`；
- staged write；
- fsync；
- same-filesystem `os.replace`；
- transaction journal；
- crash recovery；
- optimistic generation check。

### 新 state 字段

```yaml
project:
  state_generation: <non-negative integer>
```

写入流程：

```text
1. 读取 generation=N
2. 在内存计算新 framework/state/report
3. 写 staged temp files
4. 对 staged files 做 schema/hash/self-check
5. 再次读取当前 generation
6. 若 != N：abort（说明另一写入者已更新）
7. 写 transaction journal = prepared
8. 依次 atomic replace
9. journal = committed
10. generation = N+1
11. 清理 journal
```

由于多个文件无法获得真正单系统调用原子提交，journal 必须让下一次 sync 能识别并恢复“上一次提交做到一半”的状态。

### 必测故障注入点

- framework replace 前失败；
- framework replace 后、state replace 前失败；
- state replace 后、report replace 前失败；
- generation 被其他进程改变；
- temp file fsync/rename 失败；
- recovery 后再次 sync 必须幂等。

---

## 3.7 Resolver 竞赛策略配置化

在 `config/competition_profiles.yaml` 的 `stable` 下增加运行时写作 profile，例如：

```yaml
profiles:
  cumcm:
    stable:
      writing_runtime:
        mode: template_first_progressive
        template_manifest: templates/latex/cumcm/hsk/template_manifest.yaml
        supported_intents: [latex, review, full_submission, full_workflow]
        compact_intents: [latex]
```

MCM/ICM、Diangong 在能力未就绪时显式：

```yaml
writing_runtime:
  mode: full_reasoning_fallback
```

`scripts/resolve_runtime.py` 改为 generic profile consumer，不再维护：

```text
COMPACT_WRITING_COMPETITIONS
CUMCM_WRITING_PACKAGE_INTENTS
```

行为迁移必须先写 parity tests，确保 CUMCM 现有 runtime plan 在配置化前后等价。

---

## 3.8 `sync_project.py` 最终职责收敛

只有前面规则稳定后才拆。

建议最终结构：

```text
scripts/
  sync_project.py              # CLI + orchestration only
  project_snapshot.py          # artifact discovery / snapshot
  artifact_fingerprint.py      # file/bundle hashing
  state_transitions.py         # pure stale/transition logic
  project_transaction.py       # safe multi-file writes/recovery
```

MATLAB policy、workbook validation 已有现有 Authority/模块时优先复用，不为拆文件再复制新规则。

### `sync_project.py` 目标

- 只负责 orchestrate；
- 不重复定义 stale layer 常量；
- 不拥有 competition-specific policy；
- 不重新实现 workbook schema；
- 不直接裸 `write_text()` 修改项目核心状态文件。

---

# 4. 分阶段实施与 PR 切分

> 本计划本身只提交文档。后续每一阶段使用新的独立分支和单主题 PR；前一基础 PR 合并后，下一个分支必须重新从最新 `main` 建立。

## Phase A — Characterization / Regression Baseline

**建议版本：** 不升版或 patch 测试-only。

**直接目标：** 在改行为前，把当前关键边界固定成可复现实验。

### 新增/扩展测试

1. runtime self-attestation reproduction；
2. framework 被修改但 state 未同步时，当前实现行为 fixture；
3. wording-only text hash change characterization；
4. semantic content change characterization；
5. current stale-set differences across three scripts inventory test（先记录，不把差异强行统一）；
6. legacy project fixture：无 v7.11 approval 字段；
7. v8.7.4 current project fixture；
8. `depends_on.kind` 四种边 fixture；
9. sync twice idempotence baseline；
10. CUMCM runtime output golden fixture。

**预计文件：**

- `tests/test_runtime_assurance.py` 或当前对应 runtime test；
- `tests/test_v711_model_approval_gate.py`；
- `tests/test_sync_project.py`；
- `tests/test_schemas.py`；
- 新的 fixtures（仅必要最小项目）。

**禁止：** 此 PR 不修实现。

**退出条件：** 所有 characterization test 能稳定复现当前行为。

---

## Phase B — Runtime Assurance 立即加固

**建议版本：** `8.7.5` patch。

**目标：** 不等待新 Schema，先修“state 自证”。

### 修改

- 抽取当前 legacy semantic section hash helper；
- `hydrate_project_context()` 读取当前 `模型论文框架.md`；
- `_semantic_lock_evidence()` 使用当前文件实际 hash；
- expected = approved/current state hash；
- actual = current framework semantic section hash；
- mismatch 必须返回 `hash_mismatch`/`stale_or_unapproved`，不能 `verified`；
- evidence path 指向 framework；
- malformed/missing question section fail closed。

### 预计文件

- `scripts/runtime_assurance.py`
- `core/runtime_assurance_contract.yaml`
- runtime assurance tests
- 必要的 `CHANGELOG.md`

### 不做

- 不改 Schema 字段名；
- 不引入 SIB；
- 不拆 sync。

### 验收

- 已批准 A，磁盘改成 B，未 sync：resolver 不再提供 verified `locked_model_spec`；
- 文件未改：行为保持；
- 无 framework 的 legacy/stateless 调用保持现有兼容逻辑。

### 回滚

该 patch 可独立 revert，不产生项目数据迁移。

---

## Phase C — Semantic Identity Block + Dual-Read Compatibility

**建议版本：** `8.8.0` minor。

**目标：** 建立新的数学语义身份，不删除 legacy `semantic_hash`。

### 修改

1. 定义 SIB schema/canonicalization；
2. Framework 模板增加 SIB 槽位；
3. 增加 parser/canonicalizer；
4. state schema 增加新 identity 字段；
5. semantic validator 优先新 identity，legacy 项目 fallback old text hash；
6. model approval contract 改为新项目绑定 `semantic_identity_hash`；
7. runtime assurance 优先验证 identity hash；
8. 旧项目重新进入 model design 时触发迁移要求。

### Authority 决策

- SIB 内容仍位于 `模型论文框架.md`，避免第二语义事实源；
- canonicalization 规则必须只有一个实现入口；
- 不允许 resolver、approval validator、sync 各写一份 parser。

### 预计文件

- `core/project_state.schema.yaml`
- `core/model_approval_contract.yaml`
- `core/runtime_assurance_contract.yaml`
- `scripts/validate_semantic_governance.py`
- `scripts/validate_model_approval.py`
- `scripts/runtime_assurance.py`
- `templates/model/model_paper_framework.md`（若当前活动模板确为此路径，实施前再次核实 Authority）
- `modules/02_model_design.md`（仅说明新绑定语义）
- tests / fixtures / changelog / generated indexes

### 必测语义

| 修改 | identity hash | text hash | approval |
|---|---:|---:|---|
| 改空格/排版 | 不变 | 可变 | 保留 |
| 纯措辞 | 不变 | 变 | 保留 |
| 改 caption | 不变 | 变 | 保留 |
| 改 decision variable domain | 变 | 变 | stale |
| 改 objective sense/expression | 变 | 变 | stale |
| 改 constraint | 变 | 变 | stale |
| 改 preprocessing decision | 变 | 变 | stale |
| 改 dependency kind | 变 | 变 | stale |

### 兼容

- 无 SIB 的旧项目：只读继续可用；
- 要生成新主代码：必须先迁移/重新确认 current SIB；
- 不自动根据旧 prose 猜完整 SIB 并声称 verified；可以生成候选 migration draft，但必须经过 model-design/approval gate。

---

## Phase D — State Transition Authority + Typed Stale Engine

**建议版本：** `8.8.1` 或 `8.9.0`，取决于是否新增外部可见字段。

**目标：** 消除 stale 规则复制，真正使用 dependency kind。

### 修改

- 新增 `core/state_transition_contract.yaml`；
- 新增纯逻辑 `scripts/state_transitions.py`；
- `validate_semantic_governance.py`、`sync_project.py`、`validate_code_delivery.py` 改为调用 shared engine；
- 任何旧 `PRIMARY_STALE_LAYERS` / `ANALYSIS_STALE_LAYERS` 常量删除；
- transition report 返回 event/source/edge/reason；
- dependency cycle 检测；
- legacy untyped dependency conservative fallback。

### 关键验收

1. `semantic_identity_changed(Q1)` 使 Q1 approval stale；
2. Q2 `kind=model`：Q1 semantic change -> Q2 semantic approval stale；
3. Q2 `kind=result`：Q1 result change -> Q2 rerun required，但 Q2 model approval 保持；
4. Q2 `kind=parameter`：仅相关 parameter event 传播；
5. Q2 `kind=data`：data event 传播，纯图/文变化不传播；
6. 依赖环必须 deterministic report；
7. 同一事件重复 apply 幂等；
8. 三个入口对同一 event 产生同一 stale result。

---

## Phase E — Artifact Naming Migration

**建议版本：** `8.9.0` minor（additive）；最终删除旧字段留给 9.0.0。

### 修改

Schema 新增：

```yaml
artifact_hashes:
  primary_code:
  analysis_code:
```

并逐步停止新项目写：

```yaml
artifact_hashes.model
```

### 迁移规则

```text
legacy artifact_hashes.model -> primary_code
```

只有在没有新字段时读取 alias；若新旧同时存在且值不同：

```text
blocking inconsistency
```

### `model_hash` 处理

实施前执行全仓库引用盘点，形成记录：

```text
field -> readers -> writers -> semantic meaning -> migration action
```

没有引用证据前不删除。

### 验收

- 新项目状态输出没有含混 `model` artifact；
- old project 仍能读取；
- primary code change 不会自动等价为 mathematical semantic change；
- code delivery、sync、runtime assurance 命名一致。

---

## Phase F — Transactional Project Writes

**建议版本：** `8.9.x` minor。

### 修改

- 新增 `project.state_generation`；
- 新增 `scripts/project_transaction.py`；
- `sync_project --write` 全部走 staged + validated + recoverable commit；
- semantic governance `--write` 也不得继续直接裸写 state；
- 其他活动脚本若会更新同一 state，逐一纳入共享 transaction helper。

### 测试

- atomic single-file replace；
- simulated crash recovery；
- generation conflict；
- concurrent stale writer rejection；
- transaction journal cleanup；
- repeated sync idempotence；
- failed validation 不留下半写 framework/state。

### 明确不做

不引入数据库，不引入外部锁服务；保持仓库文件型工作流。

---

## Phase G — Competition Writing Runtime De-Hardcode

**建议版本：** `8.9.x` patch/minor。

### 修改

- `competition_profiles.yaml` 增加 `stable.writing_runtime`；
- Resolver 通用加载；
- CUMCM 当前行为 golden parity；
- MCM/ICM、Diangong 未声明 Template-First 时继续 full reasoning fallback；
- 未来新增竞赛不需要改 Resolver Python 常量。

### 验收

- CUMCM `latex/review/full_submission/full_workflow` 的 load order、writing runtime mode 与改前 golden 等价；
- 非 CUMCM 行为不被意外 compact；
- 缺失 profile 时明确 fail/fallback，不静默猜测。

---

## Phase H — `sync_project.py` 结构拆分

**建议版本：** `8.9.x` refactor，行为不变。

### 前置条件

Phase D、E、F 必须已经稳定并合并。

### 拆分原则

只做 mechanical extraction：

```text
sync_project.py
  -> project_snapshot.py
  -> artifact_fingerprint.py
  -> state_transitions.py (already introduced)
  -> project_transaction.py (already introduced)
```

禁止在该 PR 再改变 stale matrix、Schema、Hash 意义或 resolver 行为。

### 验收

- golden sync report 完全一致（允许非语义时间戳字段单独处理）；
- CLI 参数兼容；
- 所有原 sync tests 不改语义断言仍通过；
- 文件体积下降只是结果，不是验收目标；行为 parity 才是目标。

---

## Phase I — v9.0.0 Compatibility Removal

只有以下条件同时满足才允许：

1. 至少一个稳定版本已写新字段；
2. migration fixtures 全绿；
3. 仓库活动代码不再写旧字段；
4. code search 证明旧字段只剩 compatibility reader / docs；
5. 用户确认可以结束 v8 project write compatibility；
6. Changelog 和 migration doc 完整。

### 候选删除

- `artifact_hashes.model` 新写支持；
- legacy `semantic_hash` 作为 approval identity 的含义；
- 经引用盘点确认无独立意义的 `model_hash / validated_model_hash`；
- 过期 stale alias。

### v9 迁移文档必须回答

- 如何从 v8.7.x 项目升级；
- read-only 历史项目是否仍可打开；
- 哪些字段自动迁移；
- 哪些语义必须重新 Human Approval；
- 如何回滚到最后一个 v8.x；
- compatibility reader 何时彻底删除。

---

# 5. 测试矩阵

## 5.1 Semantic Identity

- canonical serialization deterministic；
- mapping key reorder 不改 hash；
- 明确声明为 set 的 collection reorder 不改 hash；
- order-sensitive field reorder 必须改 hash；
- prose wording 变化不改 identity hash；
- variable domain / objective / constraint / assumption / preprocessing / dependency 改变必须改 hash；
- malformed SIB fail closed；
- duplicate variable/constraint ID fail；
- unknown SIB schema version fail/review_required，不能 silently accept。

## 5.2 Model Approval

- approval 绑定 current identity hash/revision；
- stale identity 不可通过；
- pure wording 不 stale；
- old approval fields read-only compatibility；
- old project re-enter solve requires migration。

## 5.3 Runtime Assurance

- current file hash 必须参与证据；
- framework missing；
- wrong Q section；
- state hash mismatch；
- approved hash mismatch；
- current/validated/approved 三层完全一致才 verified；
- evidence report 中 expected/actual 不得来自同一未经重算变量伪装成比对。

## 5.4 Transition Engine

至少覆盖：

```text
8 event types
x
4 dependency kinds
x
own/downstream
```

不要求所有笛卡尔积都产生不同动作，但必须有 table-driven tests 覆盖每个规则分支。

## 5.5 Artifact Identity

- primary code / analysis code 分离；
- old `model` alias 一致时可读；
- alias 冲突 blocking；
- primary change 不误判为 semantic change；
- analysis change 不使 primary result stale。

## 5.6 Transaction

- prepare failure；
- commit middle failure；
- recovery；
- concurrent generation conflict；
- repeated command idempotence；
- no partial state accepted by resolver after recovery。

## 5.7 Resolver

- CUMCM golden；
- MCM/ICM fallback；
- Diangong fallback；
- unknown competition；
- explicit competition vs project-state conflict；
- profile missing manifest。

## 5.8 全仓库回归

每 PR 至少：

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/generate_indexes.py --check
```

影响 LaTeX / template manifest 时再跑对应编译矩阵；纯状态/运行时 PR 不应无理由改论文模板。

---

# 6. Migration / Compatibility 规则

## 6.1 旧项目分类

### L0 — 历史只读项目

- 可以继续查看状态、workbook、论文；
- 不强制补 SIB；
- runtime 报告可以标记 `legacy`，但不能伪装成新 identity-level verified。

### L1 — 旧项目重新写论文但不改模型

- 若写作只消费 accepted workbooks，允许最小迁移；
- 如果 Resolver 需要 `locked_model_spec` 证明，必须确认 legacy approval 是否足够，必要时生成 SIB 并重新确认。

### L2 — 旧项目重新进入模型设计/主求解

- 必须建立 SIB；
- 必须通过 semantic validator；
- 必须重新绑定 Model Approval；
- 之后写新字段。

## 6.2 Migration tool 原则

如果后续确认需要 migration CLI，新增一个通用、版本化入口，例如：

```text
scripts/migrate_project_state.py
```

而不是每次版本建立一个永久的一次性脚本。

Migration 必须支持：

```text
--check
--write
--from-version
--to-version
```

并在 `--write` 前输出 planned changes；不能静默改变数学语义。

自动迁移只允许机械字段映射；SIB 若无法从旧状态确定，不得自动猜测并标记 approved。

---

# 7. Authority 变更计划

## 保持不变

- `core/project_state.schema.yaml`：状态结构 Authority；
- `core/model_approval_contract.yaml`：approval 行为 Authority；
- `core/runtime_assurance_contract.yaml`：runtime evidence Authority。

## 新增一个必要 Authority

```text
core/state_transition_contract.yaml
```

仅拥有：

```text
state_transition_events
stale_layer_mapping
dependency_kind_propagation
legacy_fallback
transition_report_semantics
```

不拥有：

- model semantics；
- workbook schema；
- code quality；
- writing semantics。

## Semantic identity policy 放置

优先扩展 `core/model_approval_contract.yaml` + `project_state.schema.yaml`，不轻易再增加 `semantic_identity_contract.yaml`。

只有当实施中发现 canonicalization / SIB schema 已经形成独立且跨 approval/runtime/state 三方复用的复杂契约，才允许在独立设计 PR 中提议新 Authority；不得在实现途中随手新增。

---

# 8. 文件级影响清单

| 文件 | 预期动作 | 阶段 |
|---|---|---|
| `core/bootstrap.yaml` | 增加 state transition Authority 指针；版本 carrier 按 release 更新 | D/版本 PR |
| `core/project_state.schema.yaml` | identity/artifact/state_generation 字段；legacy alias | C/E/F |
| `core/model_approval_contract.yaml` | approval 从 text hash 迁到 identity hash | C |
| `core/runtime_assurance_contract.yaml` | locked model 变为 current-framework evidence-backed | B/C |
| `core/module_manifest.yaml` | 注册 transition/migration gate dependency（若需要） | D |
| `core/state_transition_contract.yaml` | 新增唯一 transition Authority | D |
| `config/competition_profiles.yaml` | writing_runtime profile | G |
| `scripts/runtime_assurance.py` | 实时重算 semantic evidence | B/C |
| `scripts/validate_semantic_governance.py` | SIB parse/hash + shared transition engine | C/D |
| `scripts/validate_model_approval.py` | 新 identity binding | C |
| `scripts/validate_code_delivery.py` | 删除本地 stale 常量，调用 shared engine | D/E |
| `scripts/sync_project.py` | 新 artifact names + shared transition + transaction，后期拆分 | D/E/F/H |
| `scripts/state_transitions.py` | 新纯函数 transition engine | D |
| `scripts/project_transaction.py` | 新原子/恢复写入 helper | F |
| `scripts/project_snapshot.py` | 后期从 sync extraction | H |
| `scripts/artifact_fingerprint.py` | 后期从 sync extraction | H |
| `scripts/resolve_runtime.py` | competition profile 驱动 | G |
| `templates/model/...` | SIB slot，实施前核实当前模板 Authority | C |
| `modules/02_model_design.md` | identity/approval 新术语的最小说明 | C |
| `SKILL_CHANGE_GOVERNANCE.md` | 新 transition Authority 登记 | D |
| `CHANGELOG.md` | 每个行为版本真实记录 | 各 release |
| `tests/...` | characterization、migration、transition、transaction、resolver parity | 全程 |
| 生成索引/manifest | 仅生成器刷新 | 各涉及文件变更 PR |

---

# 9. PR 纪律

本次整体重构不能违反仓库“一 PR 一主题”。推荐顺序：

```text
PR-PLAN   docs plan only                     ← 当前
PR-A      characterization tests
PR-B      runtime assurance live hash fix
PR-C      semantic identity + compatibility
PR-D      state transition engine
PR-E      artifact naming migration
PR-F      transactional writes
PR-G      competition runtime configuration
PR-H      sync_project mechanical split
PR-I      v9 compatibility removal
```

每个 PR 必须重新基于当时最新 `main`，不得让多个聊天并发写同一未合并实现分支。

如果任何阶段发现与未合并 PR 重叠：

```text
STOP → 先处理重叠 PR → 更新 main → 重建/变基 → 重跑完整测试
```

---

# 10. CI / Branch Protection 权限限制下的人工替代纪律

Issue #92 当前因平台权限无法完成，不把它混入代码重构。

在 Branch Protection 不能强制的期间，所有实现 PR 仍执行以下人工纪律：

1. 禁止直接写 main；
2. PR 创建后先检查 changed files；
3. CI 未完成前不 merge；
4. CI 失败不 merge；
5. merge 前再次确认 PR head SHA 未变化；
6. 使用 expected head SHA 合并（工具支持时）；
7. 合并后核实 main commit 与 CI；
8. 不以“本地测试通过”代替 GitHub Actions；
9. 不写代码模拟 GitHub branch rules。

这只是流程控制，不等同于 Branch Protection，本计划不会声称已经解决 #92。

---

# 11. 风险登记

## R1. SIB 与 prose 漂移

**风险：** 人修改 prose 但忘了更新 SIB。

**控制：**

- model design 写作流程明确 SIB 是 semantic identity；
- semantic closure validator 检查关键 ID/变量/目标/约束的框架引用一致性；
- 不尝试用 LLM 自动判等替代 deterministic gate；
- 最终 Human Approval brief 必须展示 SIB 核心摘要。

## R2. 过细 stale matrix 导致漏失效

**控制：**

- 第一版 typed propagation 宁可保守；
- legacy/unknown kind 全失效；
- 每个优化传播规则必须有负向测试证明不会保留错误结果。

## R3. Schema 迁移破坏旧项目

**控制：**

- additive first；
- fixtures；
- read-old/write-new；
- major removal 延后；
- migration dry-run。

## R4. transaction 机制复杂化

**控制：**

- 不引入数据库；
- journal 格式最小化；
- recovery 状态机必须 table-driven 测试；
- transaction helper 不混入业务规则。

## R5. 重构 `sync_project.py` 时行为漂移

**控制：**

- 结构拆分最后做；
- golden/parity tests 先固定；
- H 阶段只 mechanical extraction。

## R6. Authority 数量继续膨胀

**控制：**

- 本计划只预批准一个新 Authority：`state_transition_contract.yaml`；
- 其他新 contract 必须单独论证不可由现有 Authority 承担；
- 每次新增 Authority 同时更新 single-source test。

---

# 12. Stop Conditions

出现以下任一情况必须停止当前 PR，而不是继续补丁叠补丁：

1. 发现同一 Authority 正被另一个未合并 PR 修改；
2. 旧项目 migration 无法做到 deterministic；
3. 新 identity 需要从自由文本自动猜数学语义才能工作；
4. typed propagation 无法证明不会漏掉关键 stale；
5. transaction recovery 不能在故障注入测试中恢复一致状态；
6. 为通过测试需要删除既有有效约束；
7. 一个 PR 开始同时改变 Schema、transition 语义、Resolver、论文模板等多个不相关主题；
8. 生成文件需要手工修改才能通过；
9. 完整测试出现无法解释的既有能力回归。

---

# 13. 每阶段完成报告模板

每个实现 PR 合并前/后必须记录：

```text
分支：
PR：
基线 main SHA：
当前 Skill 版本：
目标版本：
本 PR 只解决：
明确未解决：
权威文件变化：
Schema 变化：
兼容行为：
迁移行为：
新增测试：
完整测试：
专项测试：
生成文件状态：
CI run：
风险：
回滚方法：
合并 commit SHA：
后续下一阶段：
```

---

# 14. 实施前最终检查清单

在开始 **PR-A 以外的任何代码修改** 前，再次逐项确认：

- [ ] 从最新 `main` 重新读取 `core/bootstrap.yaml`
- [ ] 从最新 `main` 重新读取 `SKILL_CHANGE_GOVERNANCE.md`
- [ ] 确认 Skill version 与 main SHA
- [ ] 检查 open PR
- [ ] 检查重叠 branch/PR
- [ ] 读取本阶段相关 Authority，而非依赖本计划中的旧快照
- [ ] 先写/更新 characterization test
- [ ] 确认本 PR 的直接目标只有一个
- [ ] 明确禁止触碰文件
- [ ] 明确 backward compatibility
- [ ] 明确 migration path
- [ ] 明确 rollback
- [ ] 运行基础 lint/unit/generated check
- [ ] 运行专项测试
- [ ] 检查 generated diff 只来自生成器
- [ ] 创建 PR 后等待真实 CI
- [ ] CI 通过后才允许 merge

---

# 15. 最终成功判据

整个重构项目只有在以下条件全部成立时才算完成：

1. 纯 wording/formatting 不再使数学模型 approval stale；
2. 真实数学语义变化一定使对应 identity 改变；
3. `locked_model_spec=verified` 必须能够从当前 framework evidence 独立复核；
4. mathematical model identity 与 Python implementation hash 不再共用 `model` 含混命名；
5. stale transition 只有一个 Authority/实现入口；
6. `depends_on.kind` 对实际传播结果产生可测试影响；
7. primary-code change、analysis-code change、semantic change 的失效范围不同且合理；
8. 项目核心文件异常中断后能够恢复一致状态；
9. 并发 stale writer 会被 generation check 拒绝；
10. Resolver 不再硬编码 CUMCM runtime policy；
11. `sync_project.py` 拆分后行为 parity；
12. v8 old projects 仍可只读，重新求解有明确 migration；
13. 所有活动测试、lint、generated check、真实 CI 全绿；
14. 生成文件无手工伪造；
15. #92 仍被诚实标记为平台治理债务，未被错误宣称“已通过代码解决”。

---

## 结论

本次重构的核心不是增加更多功能，而是先把以下四个底层等式做实：

```text
当前语义事实 = 当前 semantic identity
当前 identity = validated identity
validated identity = approved identity（需要 locked model 时）
当前 artifact 文件 = state 中记录的 artifact evidence
```

然后让所有 stale / rerun / rewrite 决策都通过一个有类型、可测试、可解释的 state transition engine 传播。

只要这一底层治理层闭合，后续再扩展数学智能、竞赛能力或写作能力，才不会继续放大状态漂移和规则重复。