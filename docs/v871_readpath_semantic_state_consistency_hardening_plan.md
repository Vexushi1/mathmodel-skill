# v8.7.1 Active Read-Path, Semantic State & Version Consistency Hardening Plan

> 状态：**审批前 / Plan Only / Implementation Not Started**  
> 基线：`main@fb1d14f98572237da937c4e3bf978ec8ecb793e0`  
> 当前 Skill：**v8.7.0**  
> 建议目标版本：**v8.7.1 patch**  
> 实施分支：`fix/v8.7.1-readpath-semantic-state-consistency`  
> 本文件角色：本轮维护的 Scope Contract / 审批依据，不是 runtime Authority。  
> 当前阶段禁止：修改实际 runtime 语义、升级 release carriers、修改 generated hashes、合并 PR。

---

# 0. Executive Summary

本轮不是继续增加新的数学建模或论文写作能力，而是对 v8.7.0 发布后的 active Skill 做一次**读取路径、状态语义、版本载体与验证覆盖收口**。

整体审计结论是：

- v8.7.0 的主启动链、root/package Skill 入口、Bootstrap、Router、Writing Reasoning、Writing Runtime、CUMCM Template、Generated Index 主体仍然健康；
- 没有发现 `main` 上 root/package `SKILL.md` 版本漂移，也没有发现当前 open PR 与本轮范围重叠；
- 但发现若干 active integration gap，其中至少有三类会导致“规则存在但下游读不到 / 读到旧值 / 状态无法确定映射”的实际风险：
  1. 正式终审模板仍固定携带旧 Skill 版本；
  2. v8.7 Formula Role 已成为 Writing Preflight 必需事实，但 Module 02 的 Formula Trace 生产接口仍是旧列结构；
  3. Proposition / Proof 在 Project State、单命题记录与 Writing Preflight 中使用不同状态词表，却缺少确定性映射；
  4. mandatory Per-Question Writing Capability Preflight 目前主要由静态测试保护，项目框架 validator 尚未形成相称的行为级校验；
  5. repository reference lint 只校验 `#fragment` 前的文件是否存在，不能发现 Authority fragment / Markdown heading / YAML key 已漂移；
  6. 少量 active module/template 仍以旧 release 号作为标题或注释，没有明确标记“历史架构来源”与“当前 Skill 版本”的区别；
  7. `writing_reasoning_contract.yaml` 的 `schema_version` 是否应随 v8.7 的 additive structure 变化而升级，目前没有足够明确的版本策略，旧测试又直接 pin `1.8.0`。

因此本轮建议定义为 **v8.7.1 patch**：修复 v8.7.0 已发布能力的 integration / validation / active-state drift，不改变模型、solver、validator、Workbook、Project State 公共 schema、Model Approval、03A/03B、Figure 或交付目录语义。

本轮最终目标不是“让 grep 看起来一致”，而是形成如下闭环：

```text
Authority / Project Fact Producer
        ↓
明确字段与状态来源
        ↓
Runtime / Consumer 可确定读取
        ↓
Validator 能发现 missing / stale / drift
        ↓
Lint 能发现 file + fragment 失效
        ↓
Release carrier / active template 不携带陈旧当前态
```

---

# 1. Governance Baseline

本计划按当前 `main` 中的治理要求制定。

## 1.1 当前事实

```text
repository = Vexushi1/mathmodel-skill
default_branch = main
main_head = fb1d14f98572237da937c4e3bf978ec8ecb793e0
current_skill = 8.7.0
open_pull_requests = 0
```

当前历史分支中仍可见已完成的 v8.7.0 implementation / post-merge branches，但没有 open PR；本轮不得复用旧分支。

## 1.2 Governance 要求

本轮继续遵守：

- 写前读取 `core/bootstrap.yaml` 与 `SKILL_CHANGE_GOVERNANCE.md`；
- 不直接修改 `main`；
- 一个聊天一个分支；
- 一个 PR 一个主题；
- generated files 只能由 `scripts/generate_indexes.py` 或正常 generated workflow 产生；
- release carrier 只在 implementation + tests 稳定后同步；
- CI 未完成前不得宣称发布；
- 合并必须再次得到用户明确批准。

---

# 2. Change Brief

```text
修改主题：v8.7.1 Active Read-Path, Semantic State & Version Consistency Hardening
当前版本：8.7.0
目标版本：8.7.1（审批并实施成功后）
变更等级：patch

直接目标：
1. 修复 active final review template 的旧 Skill version 漂移；
2. 打通 Module 02 Formula Trace → Formula Role → Writing Preflight 的生产/消费闭环；
3. 明确 Proposition / Proof 多层状态到 Preflight activation 的确定性映射；
4. 为 mandatory Per-Question Preflight 增加真实项目框架行为校验；
5. 增加 active Authority pointer 的 fragment-level read-path health 检查；
6. 清理或标注 active 文件中容易被误读为 current Skill version 的旧 release label；
7. 对 writing_reasoning schema_version 的版本策略做一次明确裁决；
8. 增加专门的 v8.7.1 drift regression，防止同类问题再次出现。

明确不做：
- 不新增模型、solver、validator；
- 不改变 Formula Role 四级语义本身；
- 不改变 Core Model Summary required/inline/not_applicable 数学判断；
- 不改变 Proposition 的数学准入与 proof-level 规则；
- 不改变 Algorithm not_needed/stepwise/pseudocode 的数学含义；
- 不改变 Model Approval / Human Approval；
- 不改变 preprocessing 三态；
- 不改变 03A/03B；
- 不改变 Workbook Schema、数值验收、Figure Evidence、MATLAB 交接；
- 不改变五文件交付合同、目录结构、CLI 公共调用；
- 不对 legacy/ 做语义迁移；
- 不把历史 docs 中旧版本号批量替换成当前版本。

权威事实源：
- core/bootstrap.yaml
- SKILL_CHANGE_GOVERNANCE.md
- core/hsk_core_policy.md
- core/writing_reasoning_contract.yaml
- core/writing_runtime_contract.yaml
- core/project_state.schema.yaml（只读核对；原则上不修改）
- core/output_contract.yaml
- modules/02_model_design.md
- modules/05_writing/paper_writing_protocol.md
- modules/06_review_delivery.md
- templates/model/model_paper_framework.md
- templates/review/final_review_matrix.yaml
- scripts/validate_model_paper_framework.py
- scripts/lint_skill_checks.py
- scripts/score_submission.py

兼容性要求：
- v8.7.0 项目仍可读取；
- 历史 final-review matrix 仍可作为历史/兼容输入，不因其记录旧 Skill 版本被无条件拒绝；
- old framework 缺少 v8.7 Preflight section 时不得被错误解释为 not_applicable；
- 不改变现有 Project State 公共 enum，除非后续证据证明不改 schema 无法闭环；若必须改 schema，停止 patch 并重新评估版本等级；
- 不删除现有 deprecated v7 read compatibility；
- root/package Skill entrypoints 必须继续字节级一致。

迁移要求：
- active template 不再携带会随 release 自动过期的硬编码 current Skill 版本；
- old framework 可在下一次 writing route 中增量初始化 Preflight，而不是要求重做模型；
- 不强制迁移历史终审报告。

验收测试：
- lint_skill.py
- unittest discover
- generate_indexes.py --check
- v8.7.1 dedicated read-path/state tests
- current skill health / entrypoint parity
- writing preflight regression
- final review compliance regression
- framework validation regression
- representative CUMCM LaTeX route resolution
- existing CI full matrix

回滚方式：
- 整个 PR 可单独 revert；
- 不改变 Project State/Workbook 公共 schema时无需数据迁移回滚；
- 若 fragment validator 产生大规模非本轮问题，缩回仅检查 current critical pointer registries，不扩大 PR。
```

---

# 3. Risk Inventory

## R1 — Active Final Review Template 固定携带 v8.3.0

**等级：High / Definite**

当前：

```yaml
templates/review/final_review_matrix.yaml
review_context:
  skill_version: 8.3.0
```

而当前 Bootstrap 为：

```yaml
skill_version: 8.7.0
```

这不是历史 docs，而是 `core/module_manifest.yaml`、Review Pack、Final Review Authority 和 Template Index 会实际引用的 active template。

更关键的是，`scripts/score_submission.py` 对新 matrix 的要求目前是：

```text
review_context.skill_version 必须非空
```

但没有要求它与本次 active Skill 一致。因此如果使用者直接复制模板并只填其他字段，`8.3.0` 可以作为看似合法的终审 provenance 一路保留下来。

### 风险表现

```text
current runtime = 8.7.0
formal review report = 8.3.0
↓
报告看起来 schema 合法
↓
但 provenance 已失真
```

这属于 active template state drift，不只是展示问题。

### 首选修复

不要每个 release 都把模板中的 `8.3.0 → 8.7.1` 手工追着改，因为下一版本仍会漂移。

建议改为：

```yaml
review_context:
  skill_version: null
```

模板明确保持“待实例化”；`modules/06_review_delivery.md` 要求正式终审实例化时从当前 `core/bootstrap.yaml` 恢复 Skill 版本。

最终 report 仍由 `score_submission.py` 要求 `skill_version` 非空，因此模板不能被误当作完成态报告。

### 回归要求

- active template 不得 pin 一个历史 Skill release；
- runtime/handoff 测试将 bootstrap 版本填入模板后可通过 scorer；
- 历史 8.2/8.3 matrix fixture 继续用于 compatibility 测试，不全局替换。

---

## R2 — Module 02 Formula Trace Producer 未同步 v8.7 Formula Role

**等级：High / Definite**

v8.7.0 已经把 Formula Trace 扩展为：

```text
final_model_relation
key_bridge_relation
supporting_derivation
routine_algebra
```

`core/writing_reasoning_contract.yaml` 的 `internal_trace.required_fields` 已要求：

```text
formula_id
question
role
source
derivation
destination
status
```

`templates/model/model_paper_framework.md` 也已经有 `Role` 列。

但是 `modules/02_model_design.md#4.1 核心 Formula Trace` 当前生产表仍是旧结构：

```text
Formula ID | Source | Depends on | Derivation | Destination | 代码/证据锚点 | 状态
```

缺少至少：

```text
对应小问
Role
```

而 Writing Runtime 又规定：

```text
missing_role → needs_adjudication
```

### 典型失败链

```text
Module 02 正常完成 Formula Trace
↓
按 Module 02 表格没有 Role
↓
进入论文写作
↓
Per-Question Preflight 要求 Formula Roles
↓
missing_role = needs_adjudication
↓
本应在模型设计时完成的分类被拖到写作阶段
```

这正是“规则存在，但上游生产端没有同步”的典型 integration drift。

### 修复原则

- Formula Role 的**定义仍只在** `writing_reasoning_contract.yaml`；
- Module 02 只增加项目事实登记字段，不复制四类角色的完整解释；
- Module 02 Formula Trace 列结构与 framework / internal_trace 对齐；
- `routine_algebra` 仍默认不进入 Core Formula Trace，不因加列导致公式膨胀。

### 回归要求

增加 producer/consumer contract test：

```text
Reasoning internal_trace.required_fields
⊆ Module 02 recordable fields
⊆ Model Paper Framework trace surface
```

测试只检查字段闭环，不从文本正则判断公式数学角色是否正确。

---

## R3 — Proposition / Proof 状态存在三层词表，但没有确定性映射

**等级：High / Semantic Ambiguity**

当前有三层状态：

### Project State 顶层计划状态

```text
not_assessed / planned / current / stale
```

### 单个 proposition record 状态

```text
candidate / current / stale / removed
```

### Writing Preflight 当前接受的综合状态

```text
not_assessed / candidate / planned / current / stale / removed / missing
```

这三套值各自都合理，但现在缺少一个正式 mapping，说明：

- `planned` 来自哪里；
- 一个 `candidate` item 如何覆盖/不覆盖 top-level `not_assessed`；
- top-level `current` 与某个 item `stale` 冲突时谁优先；
- `removed` 是“某个命题被删除”还是“本问无需命题”；
- `missing` 与 `not_assessed` 有什么区别；
- 哪个状态触发 Pack、哪个只触发 necessity review。

同时，Writing Runtime 中存在字段：

```yaml
dispatch_from_project_state: true
```

但 Preflight 的直接事实又主要来自 `模型论文框架.md#逐问写作能力预检` 和 Proposition Plan。若把这里的 `project_state` 理解成 `state/project_state.yaml`，会和 Core Policy 对“机器状态 / 项目语义记忆”的区分产生歧义。

### 修复原则

不优先修改 `core/project_state.schema.yaml`。

在 `writing_runtime_contract.yaml` 定义一个**derived activation view**，明确：

```text
plan_state
+ proposition item states
+ stale/missing condition
→ effective_preflight_state
→ activation
```

推荐不要把 top-level 和 item-level enum 强行改成一套，而是保留来源语义，再做 deterministic derivation。

示意：

```text
plan=current/planned
→ proof branch active

plan=not_assessed + candidate item exists
→ necessity_review only

relevant current/planned proposition becomes stale
→ review_required

all relevant items explicitly removed + no active plan
→ no proof branch, but record explicit adjudication

source absent
→ missing / needs_adjudication
```

实际优先级在实现前必须根据当前 schema、Module 02 和 validator 再核定。

### 兼容原则

- 不删除任何现有 enum；
- 不把 `candidate` 自动升级成 `planned`；
- 不把 `removed` 自动解释为本问永远 `not_applicable`；
- 不让 `missing` 静默变成 `not_assessed`。

---

## R4 — Mandatory Preflight 有 Runtime 规则，但 Framework Validator 没有相称行为校验

**等级：High / Enforcement Gap**

v8.7.0 已经明确：

```text
Per-Question Writing Capability Preflight
= mandatory_before_each_question_write
```

Paper Writing Protocol 也要求进入每问正文前必须消费该状态。

当前 v8.7 tests 已经很好地证明：

- capability branch 存在；
- resolver 会暴露 `before_write_preflight`；
- summary/proposition/algorithm activation 映射存在；
- stepwise/pseudocode 资源激活不同。

但当前 `scripts/validate_model_paper_framework.py` 的已知强校验重点仍集中在 Algorithm Trace 等既有结构；没有看到对 `### 逐问写作能力预检`、Formula Role enum、Core Model Summary state、Proposition effective state、Preflight Status 的完整行为级校验。

因此现在更接近：

```text
Runtime 说“必须裁决”
↓
测试说“这个门存在”
↓
但真实 framework 写成 missing/stale/非法 role 时
机器层未必能明确报告
```

### 修复原则

扩展 `validate_model_paper_framework.py`，但保持“机器不判断数学正确性”：

可检查：

- Preflight section 是否存在；
- Qx row 是否可解析；
- Formula Role 是否属于合法 enum；
- Core Model Summary 是否属于 `required/inline/not_applicable/missing`；
- Algorithm Presentation 是否属于合法 enum；
- Preflight Status 是否合法；
- `stepwise/pseudocode` 是否存在 current Algorithm Trace；
- `missing/stale` 与 `current` 是否存在确定性冲突；
- proposition derived state 与 proposition section 是否明显矛盾。

不得检查：

- 某公式数学上是否真是 bridge；
- 某问题是否“应该”有命题；
- 某算法是否“应该”写 pseudocode；
- summary 是否数学正确。

### 旧项目兼容

旧 framework 缺少整个 v8.7 Preflight section 时：

- read/migration 模式：允许读取，但标记需要增量初始化；
- strict current writing / final review：不得当作 `not_applicable`，应返回 `needs_adjudication / review_required` 类结果；
- 不要求重做 Model Approval 或主求解，只初始化写作层项目事实。

如果当前 validator API 无法表达 warning/review_required，实施时应优先增加兼容的分类接口，而不是把所有旧项目直接 hard fail。

---

## R5 — 当前 Reference Health 只验证文件，不验证 `#fragment`

**等级：Medium-High / Systemic Read-Path Risk**

当前 `scripts/lint_skill_checks.py::_check_repo_reference()` 会：

```text
path#fragment
→ 去掉 #fragment
→ 只检查 path exists
```

因此：

```text
文件存在
≠
Authority fragment 仍然可定位
```

当前 active 仓库中大量关键指针采用：

```text
core/writing_reasoning_contract.yaml#adaptive_core_model_summary
modules/05_writing/latex.md#5-图表命题和算法环境
templates/model/model_paper_framework.md#逐问写作能力预检
modules/06_review_delivery.md#Final-Submission-Compliance-Evidence-Sweep
```

其中最后一类还存在“pointer fragment 与实际 heading 带中文章节编号”的可读性差异。当前 CI 不会判断该 fragment 是否能稳定定位。

### 修复原则

只对**active critical pointer registries**做 fragment-level validation，不对整个仓库所有 prose 盲扫。

优先来源：

- `core/bootstrap.yaml`
- `core/output_contract.yaml`
- `core/writing_runtime_contract.yaml`
- `templates/latex/cumcm/hsk/template_manifest.yaml`
- `templates/review/final_review_matrix.yaml`
- 必要的 Module/Pack machine-like pointer fields

### Fragment 规则

#### Markdown

接受：

- 可规范化匹配真实 heading；或
- 显式稳定 anchor。

对于带“九、”“7.3”等展示性前缀、但长期被机器引用的关键节，优先增加稳定 anchor 或统一 pointer convention，而不是让每个 consumer 猜 GitHub slug。

#### YAML

支持：

```text
file.yaml#top_level_key
file.yaml#top.child.key
```

必须实际存在。

动态占位：

```text
#profiles.<name>.edition_rules
```

允许作为 declared dynamic fragment，不做静态实例 key 校验，但必须明确识别为动态语法，不能因为含 `< >` 就完全跳过所有检查。

### 回归要求

新增以下 fixture：

```text
valid file + valid fragment       → pass
valid file + missing fragment     → fail
missing file                       → fail
valid dynamic placeholder          → pass
legacy/docs-only pointer            → 不进入 active hard check
```

若实施后一次暴露大量历史 fragment 问题，本 PR 不扩展为全仓库重构；只修 current critical pointer surface，其余另列 debt。

---

## R6 — Active 文件中的旧 release label 容易被误读成 current version

**等级：Medium / Human-Maintainability Drift**

当前示例：

```text
modules/05_writing/latex.md
# Module 05B：LaTeX Adapter（v8.0.1）
```

以及：

```text
templates/latex/cumcm/hsk/hsk_main.tex
% v8.0.1 A196-inspired canonical template:
```

这些内容大概率是在记录“这一架构何时引入”，并不是 release carrier；但它们没有统一标记为：

```text
introduced_in / architecture_lineage / provenance
```

因此维护者在做全局版本健康审计时，很容易把它们解释为未同步模块版本。

### 修复原则

不做“把所有旧版本号替换成 8.7.1”。

建议：

- active 模块标题移除 release 号，标题只保留职责：`# Module 05B：LaTeX Adapter`；
- 若确有历史意义，在正文写：`Template-First adapter architecture introduced in v8.0.1`；
- template comment 改为 provenance 语句，而不是看起来像当前模板版本；
- 历史 docs / CHANGELOG / post-merge record 中旧版本号保持不变。

### 测试边界

只检查 active module/template 的**current-title/current-header carrier ambiguity**，不禁止历史说明出现旧版本。

---

## R7 — Writing Reasoning `schema_version: 1.8.0` 的版本策略不明确

**等级：Medium / Decision Required**

v8.6.0 审计时 `writing_reasoning_contract.yaml` 已经是：

```yaml
schema_version: 1.8.0
```

v8.7.0 又新增了 Formula Role Taxonomy、summary role integration 等结构化节点，但该 schema version 仍是 `1.8.0`。

同时，多份历史回归测试直接：

```python
assert schema_version == "1.8.0"
```

这里存在两种可能：

1. **1.8.0 是真正结构 schema 版本**：那么 additive structure 应至少考虑 minor bump；
2. **1.8.0 只是当前兼容族标识**：那么应明确文档化“何时才 bump”，避免未来每次维护者自行猜测。

本计划不预判哪一个正确。

### 实施前决策

先通过历史 diff / consumer 读取方式确认：

- 是否有代码按 `schema_version` 选择字段解析路径；
- v8.7 新字段是否改变 machine-readable consumer 的结构预期；
- exact `1.8.0` tests 是兼容保证，还是无意把 schema freeze 死。

### 两种合法结果

#### A. 应 bump

```text
1.8.0 → 1.9.0
```

并把历史测试从“永远要求当前 schema=1.8.0”改成：

- 测试自己关心的语义节点仍存在；
- schema 兼容范围合法；
- 只有专门 current-schema test 检查最新值。

#### B. 不应 bump

则在 contract 或维护说明明确：

```text
schema_version only changes when parser compatibility changes;
additive semantic nodes do not require a bump
```

并保留 1.8.0。

### Stop Condition

若发现 schema version 与外部/未知 consumer 有兼容依赖，且修改会改变公共接口，本项从 v8.7.1 移出，单独立项，不为“版本看起来整齐”冒险。

---

# 4. Positive Findings / Explicit Non-Issues

本轮不能把所有旧数字或旧文档都误判为问题。

当前确认不属于 blocking drift 的内容：

1. `core/bootstrap.yaml` 当前为 v8.7.0；
2. root / packaged `SKILL.md` 当前为 v8.7.0，现有 lint 有字节级 parity 保护；
3. `.codex-plugin/plugin.json` 由 current health 检查保护；
4. `core/code_quality_contract.yaml`、`core/user_execution_contract.yaml`、`core/runtime_assurance_contract.yaml`、`core/numerical_verification_contract.yaml` 等使用自己的 subordinate contract version / compatibility，不要求等于 Skill 8.7.0；
5. `templates/latex/cumcm/hsk/template_manifest.yaml#schema_version=1.0.0` 属于模板 schema，不是 Skill release carrier；
6. v8.6.1 / v8.7.0 post-merge verification records 中旧 SHA 和旧版本是 time-stable historical evidence，不应改成 current；
7. `legacy/` 中旧路径、旧规则和旧版本号继续保持历史材料角色；
8. v8.7.0 plan 仍保留审批前文字，但已有独立 post-merge verification record 说明它是 Scope Contract / 历史阶段状态，因此本轮不重写历史计划。

---

# 5. Proposed Implementation Phases

## Phase 0 — Baseline Reconfirmation

用户批准实施后，写任何 active source 前再次：

1. 读取 `main` bootstrap + governance；
2. 获取 live `main` HEAD；
3. 检查 open PR；
4. 若 main 已前进：
   - 比较是否触及本计划文件；
   - 若相关，停止并重建/rebase 分支；
   - 若无关，更新 baseline 后继续；
5. 读取本轮实际目标文件完整内容；
6. 不依赖本计划中的旧 SHA 作为永久 current pointer。

---

## Phase 1 — Final Review Template Version Provenance Closure

预计修改：

- `templates/review/final_review_matrix.yaml`
- `modules/06_review_delivery.md`
- `tests/test_v820_final_review_compliance.py` 或新 v8.7.1 test
- 如确有必要，`scripts/score_submission.py`

实施顺序：

1. 将 active template `review_context.skill_version` 从历史固定值改成待 hydration 状态；
2. Module 06 明确正式 matrix 从 current Bootstrap 恢复版本；
3. 写 current-template test；
4. 写“模板未 hydration 不能作为 final matrix 通过 scorer”测试；
5. 写“填 current version 后可通过”测试；
6. 保留 legacy matrix compatibility test；
7. 不给历史报告做全局重写。

是否修改 scorer：

- 优先不破坏现有 API；
- 若需要 active-delivery mismatch 检查，应以兼容方式增加 current-context validation，而不是让所有保存的历史 matrix 因旧版本被拒绝。

---

## Phase 2 — Formula Trace Producer/Consumer Closure

预计修改：

- `modules/02_model_design.md`
- `templates/model/model_paper_framework.md`（仅在列名/说明需要精确对齐时）
- `tests/test_v871_readpath_semantic_state_consistency.py`
- 可能增加 lint invariant

目标结构：

```text
Formula ID
Question
Role
Source
Depends on
Derivation
Destination
Code/Evidence Anchor
Status
```

约束：

- `Role` 定义不复制到 Module 02；只引用 Reasoning Authority；
- `routine_algebra` 默认不登记；
- `question` 对单问模块可由上下文推断，但正式 trace 表仍保持显式字段，以便跨问 framework 合并；
- 不改变已有 Formula ID 规则。

新增 regression：

- Module 02 producer 字段覆盖 reasoning contract required trace fields；
- Framework trace 能承接 Role；
- Runtime `missing_role` 仍 fail-closed；
- AI Cleanup / Review 对 bridge 的保护规则不变。

---

## Phase 3 — Proposition State Derivation Closure

预计修改：

- `core/writing_runtime_contract.yaml`
- `templates/model/model_paper_framework.md`
- `scripts/validate_model_paper_framework.py`
- v8.7.1 tests / fixtures

原则上不修改：

- `core/project_state.schema.yaml`

新增一个明确 source map：

```text
project proposition plan status
individual proposition records
framework preflight record
→ effective proposition writing state
→ activated resources
```

测试至少覆盖：

1. `not_assessed + no candidate` → no pack；
2. `not_assessed + candidate` → full reasoning necessity review only；
3. `planned` → proposition pack；
4. `current` → proposition pack；
5. relevant `stale` → review_required，不能 current；
6. explicit removed item without active proposition → no stale resurrection；
7. source missing → needs_adjudication；
8. user explicitly requests proof 时，仍允许进入 proof review branch，但不得绕过 stale factual conflict。

同时澄清 `dispatch_from_project_state` 的语义：

- 若它只是“项目事实状态”的泛称，改为更准确字段或增加解释；
- 若它真指 `state/project_state.yaml`，则明确与 framework 的 hydration 顺序。

为了 patch 兼容，优先采用 additive/alias 方式，不直接删除现有字段。

---

## Phase 4 — Framework Validator Preflight Enforcement

预计修改：

- `scripts/validate_model_paper_framework.py`
- tests / fixtures

新增 parser/validator，读取：

```text
### 逐问写作能力预检
```

建议校验：

- question id；
- Formula Role declaration；
- summary state；
- proposition effective state；
- algorithm presentation；
- full reasoning flag；
- preflight status；
- Algorithm Trace existence / mode consistency；
- stale/missing conflict。

兼容模式：

```text
legacy framework without v8.7 preflight
→ readable
→ writing preflight initialization required
→ not silently not_applicable
```

严格交付模式：

```text
current v8.7+ framework
+ target question being written/reviewed
+ missing/stale unresolved
→ review_required / validation issue
```

机器边界写进测试：

```text
validator can validate state vocabulary and cross-record consistency
validator cannot decide mathematical necessity/correctness
```

---

## Phase 5 — Fragment-Aware Active Reference Health

预计修改：

- `scripts/lint_skill_checks.py`
- 可能抽出小型内部 helper，但不新增新的公共 CLI
- 受影响的 active pointer source
- tests

实施策略：

### 5.1 Registry-based，禁止全仓库 prose grep 当 Hard Gate

建立明确的 pointer extraction 范围。

### 5.2 Markdown resolver

规范化 heading / stable anchor，验证 fragment 存在。

### 5.3 YAML resolver

解析 dotted key，动态 placeholder 明确豁免。

### 5.4 修复当前真正失效或不稳定的 critical pointers

特别复核：

- Final Submission Compliance & Evidence Sweep；
- LaTeX algorithm environment；
- Model Paper Framework Preflight；
- Output Contract writing pointers；
- Template Manifest runtime pointers。

若 fragment 只是逻辑 key 而不是 GitHub heading，应明确一种 convention，不能同一字段有时表示 GitHub anchor、有时表示自然语言搜索词。

---

## Phase 6 — Active Version-Label Hygiene

预计只改极少 active 文件：

- `modules/05_writing/latex.md`
- `templates/latex/cumcm/hsk/hsk_main.tex`
- 如检查发现同类 active header，再按相同规则处理

规则：

```text
current release carrier
→ 必须与 bootstrap 一致

schema/contract/template independent version
→ 保留自己的版本，并明确字段类型

historical introduction/provenance
→ 可以保留旧版本，但必须显式写 introduced in / provenance

active module title
→ 不再用旧 Skill release 号伪装成当前模块版本
```

不扫描、重写：

- CHANGELOG historical sections；
- post-merge verification records；
- legacy；
- plan/evaluation historical snapshots。

---

## Phase 7 — Writing Reasoning Schema Version Decision Gate

先做证据审查，再决定是否动文件。

检查：

1. v8.6 → v8.7 diff 中 `writing_reasoning_contract.yaml` 的结构变化；
2. code consumers 是否按 schema_version 分支；
3. tests pin 1.8.0 的原始意图；
4. 是否存在对外 consumer。

结果 A：需要 bump

- bump subordinate schema；
- 更新 current schema test；
- 历史语义测试不再直接锁死最新 schema，只锁自己关心的节点；
- 不把 subordinate schema 当 Skill 8.7.1 carrier。

结果 B：不需要 bump

- 明确 schema-version policy；
- 保留 1.8.0；
- 增加测试保证 policy 本身可读。

若不能高置信确定，默认 **不 bump**，把它作为文档化 debt，而不是冒险改变接口。

---

## Phase 8 — Dedicated v8.7.1 Regression Suite

建议新增：

```text
tests/test_v871_readpath_semantic_state_consistency.py
```

至少覆盖：

1. active final-review template no stale hardcoded Skill release；
2. hydrated final-review matrix uses current bootstrap version；
3. historical review matrix compatibility preserved；
4. Module 02 Formula Trace producer has Role + Question integration；
5. framework Formula Role enum accepted/rejected correctly；
6. summary state missing cannot become not_applicable；
7. proposition plan/item/effective state mapping；
8. stale proposition cannot surface current；
9. stepwise/pseudocode still require current Algorithm Trace；
10. missing Preflight section is visible in strict writing context；
11. valid Markdown critical fragment resolves；
12. invalid Markdown critical fragment fails；
13. valid YAML dotted pointer resolves；
14. missing YAML key fails；
15. dynamic placeholder pointer remains allowed；
16. root/package Skill parity unchanged；
17. current release carriers synchronized at release stage；
18. legacy/historical old version mentions are not falsely rejected；
19. current Template Manifest/A196 semantic isolation remains unchanged；
20. Model Approval / preprocessing / user execution resolver boundaries remain unchanged。

保留并运行现有：

- `tests/test_current_skill_health.py`
- `tests/test_read_path_semantic_closure.py`
- `tests/test_v861_active_consistency_semantic_drift.py`
- `tests/test_v870_question_writing_capability_preflight.py`
- `tests/test_v820_final_review_compliance.py`
- `tests/test_v780_algorithm_presentation.py`
- `tests/test_v850_author_reasoning_speech_acts.py`
- `tests/test_v860_model_construction_solution_rationale.py`
- template / resolver / LaTeX / generated-file suites

不得为了 v8.7.1 删除旧保护测试；如果旧测试与新事实冲突，先判断它锁的是“历史语义”还是“错误的当前常量”。

---

# 6. Full Validation Strategy

最低本地/CI 命令：

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests
python scripts/generate_indexes.py --check
```

代表性 runtime：

```bash
python scripts/resolve_runtime.py latex --competition CUMCM
python scripts/resolve_workflow.py full_solution --objective optimization
```

Framework tests：

- current v8.7 preflight fully adjudicated；
- missing role；
- stale proposition；
- candidate proposition；
- pseudocode without Algorithm Trace；
- old framework without Preflight section。

Release candidate 必须继续通过现有完整 CI matrix：

- Python 3.10–3.14
- Static contract lint
- Generated file contract
- LaTeX CUMCM
- LaTeX MCM/ICM
- LaTeX Diangong
- Production LaTeX attestation

---

# 7. Generated Files Policy

本计划本身以及后续 source 修改可能触发：

- `SKILL_FILE_INDEX.md`
- `TEMPLATE_INDEX.md`
- `MANIFEST.sha256`

这些文件不得手工编辑。

流程固定为：

```text
source change
→ normal generator / refresh-generated workflow
→ inspect generated-only diff
→ generate_indexes.py --check
```

若 bot 自动提交 generated metadata，在下一次 source 写入前必须重新读取 branch head / target file SHA，避免 contents API 与 bot commit race。

---

# 8. Version Strategy

## Plan stage

保持：

```text
current Skill = 8.7.0
```

本计划文件创建不升级版本。

## Implementation stage

先修复与测试，仍不立即 bump release carriers。

## Release stage

只有以下全部成立后：

```text
R1-R6 closed or explicitly deferred
R7 decision recorded
new dedicated tests green
full unit suite green
lint green
generated check green
stable candidate CI green
```

才执行：

```text
8.7.0 → 8.7.1
```

版本同步必须使用现有 carrier parity tests 确认，不做全仓库盲目替换。

---

# 9. Expected Files During Implementation

预计可能修改：

```text
modules/02_model_design.md
modules/05_writing/latex.md
modules/06_review_delivery.md
core/writing_runtime_contract.yaml
templates/model/model_paper_framework.md
templates/review/final_review_matrix.yaml
templates/latex/cumcm/hsk/hsk_main.tex
scripts/validate_model_paper_framework.py
scripts/lint_skill_checks.py
scripts/score_submission.py              # only if current-context check is required
tests/test_v871_readpath_semantic_state_consistency.py
tests/test_v820_final_review_compliance.py # only minimal current-template regression if needed
```

条件修改：

```text
core/writing_reasoning_contract.yaml
```

只在 R7 证据确认需要 schema-version policy/bump 时修改；不得借机重写 Formula Role / Summary / Proposition Authority。

Release stage 才修改 current release carriers。

Generated files 只由 generator 管理。

---

# 10. Forbidden / Protected Files Unless Scope Is Reopened

本 patch 原则上不得修改：

```text
core/model_approval_contract.yaml
core/numerical_verification_contract.yaml
core/workbook_schema.yaml
core/project_state.schema.yaml
core/user_execution_contract.yaml
core/global_preprocessing_contract.yaml
modules/03_data_preprocessing.md
modules/03_solve_validate.md
modules/03_result_analysis.md
modules/04_figure_evidence.md
templates/matlab/*
templates/code/hsk_pipeline/*
```

特别说明：

`core/project_state.schema.yaml` 本轮作为 proposition state 来源进行只读核对。若 deterministic mapping 必须通过改 enum 才能成立，立即触发 Stop Condition，不在 patch 中直接改 schema。

---

# 11. Stop Conditions

遇到以下任一情况停止实施并报告：

1. `main` 在实施前出现相关更新或重叠 PR；
2. Formula Role producer closure 需要改变旧 Formula Trace 公共文件格式或旧项目不可读；
3. Proposition state closure 必须修改 Project State schema enum；
4. Preflight validator 只能通过把旧 framework 全部 hard fail 才能实现；
5. fragment-aware lint 一次暴露大量跨版本历史 pointer，导致本 PR 不再是单主题 patch；
6. final review template 的 null hydration 会破坏已知外部 consumer，且无兼容处理；
7. writing_reasoning schema bump 会影响未知外部 consumer；
8. 测试发现 Model Approval、preprocessing、user-execution 或 numerical boundary 真实回归；
9. 需要公共 CLI/schema rename；
10. 预计 active file 修改超过约 20 个且无法合理解释单一主题。

触发 Stop Condition 后不得为了“顺手修完”扩大范围，应拆分新计划或重新评估 minor/major 版本。

---

# 12. Definition of Done

v8.7.1 只有满足以下全部条件才算完成：

- [ ] active final-review template 不再固定携带历史 Skill release；
- [ ] 正式终审实例能够恢复 current Bootstrap Skill version；
- [ ] 历史 review matrix compatibility 未破坏；
- [ ] Module 02 Formula Trace producer 已包含 v8.7 Formula Role 所需项目字段；
- [ ] Reasoning Authority 仍是 Formula Role 唯一定义源；
- [ ] Proposition plan/item/preflight 状态存在确定性 derivation；
- [ ] `missing` 与 `not_assessed` 不再混淆；
- [ ] `candidate` 不自动变 `planned/current`；
- [ ] `stale` 不得激活 current proof；
- [ ] Framework validator 能发现 preflight missing/stale/illegal state；
- [ ] validator 不声称从字符串判断数学正确性；
- [ ] active critical file+fragment references 可验证；
- [ ] 当前已知 critical fragments 全部可定位或有 stable anchor；
- [ ] active old-version title/comment 已消除 current-version 歧义或明确标成 provenance；
- [ ] writing_reasoning schema-version policy 已明确裁决；
- [ ] root/package Skill 保持字节级一致；
- [ ] Model Approval / preprocessing / user execution boundaries 无回归；
- [ ] `python scripts/lint_skill.py` 通过；
- [ ] `python -m unittest discover -s tests` 通过；
- [ ] `python scripts/generate_indexes.py --check` 通过；
- [ ] generated files fresh；
- [ ] release carriers 只在最终阶段同步为 8.7.1；
- [ ] stable release-candidate full CI 全绿；
- [ ] PR Ready for Review 前没有临时脚本/临时 workflow hook；
- [ ] 合并仅在用户再次明确批准后执行；
- [ ] merge 后重新验证 live main、generated metadata、版本与完整 CI。

---

# 13. Recommended Implementation Order After Approval

```text
Step 0   Fresh baseline / overlap check
Step 1   R1 final-review active version provenance
Step 2   R2 Formula Trace producer closure
Step 3   R3 proposition state derivation
Step 4   R4 framework validator enforcement
Step 5   R5 fragment-aware pointer health
Step 6   R6 active version-label hygiene
Step 7   R7 schema-version decision
Step 8   dedicated regression + targeted suites
Step 9   full unit/lint/generated checks
Step 10  fixed runtime/write-path trials
Step 11  release sync 8.7.0 → 8.7.1
Step 12  stable-head full CI
Step 13  PR finalization / Ready for Review
Step 14  only after explicit merge approval: merge + post-merge verification
```

该顺序优先修复**真实数据/状态生产与消费断点**，最后才做版本同步。这样如果 R2–R5 中发现更深层 schema 问题，不会先产生一个“版本已经升级但功能仍在调试”的半发布状态。

---

# 14. Approval Boundary

当前仅完成计划与分支初始化。

在用户明确批准本计划前，不执行：

- active runtime / Authority 修改；
- validator/lint behavior 修改；
- release version bump；
- PR Ready；
- merge。

审批后仍从 Phase 0 重新确认 live `main`，不得把本文件中的 baseline SHA 当成永久 current state。
