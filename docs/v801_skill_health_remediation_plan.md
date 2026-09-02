# v8.0.1 Skill Health Remediation Plan

> 状态：**PLANNING ONLY / 待用户审批**  
> 基线仓库：`Vexushi1/mathmodel-skill`  
> 基线 Skill：`8.0.1`  
> 基线 `main`：`529d54730171271281b5d420233ab1d2b24d22a1`  
> 基线仓库可见性：`public`  
> 基线 `main` 保护：`protected=false`，required status checks enforcement=`off`  
> 计划分支：`docs/v801-skill-health-remediation-plan`  
> 本文件用途：作为后续仓库健康修复的统一上下文、范围边界、实施顺序和验收依据。**本文件本身不授权任何运行语义、CI、工作流、分支保护、Skill 内容或版本修改。**  
> 审批门：只有用户明确批准本计划后，才允许进入任何实施 PR；审批前不得修改除本计划及其自动生成元数据外的活动文件，不得修改 GitHub Repository Settings，不得合并实施性 PR。

---

## 0. 修改简报

```text
修改主题：v8.0.1 Skill 健康修复与长期语义漂移防护
当前版本：8.0.1
总体目标版本：分阶段实施；仓库治理/CI-only 阶段原则上不升级 Skill 版本，
              会改变活动 LLM 入口语义表面的阶段必须按 SKILL_CHANGE_GOVERNANCE.md 单独评估 patch 版本。
变更等级：multi-PR remediation program；每个实施 PR 仍保持单主题

直接目标：
1. 把 main 的 PR + CI 治理从软约束升级为 GitHub 平台硬约束；
2. 使 generated metadata 在 feature branch/PR 阶段闭环，避免 main 依赖补救性 bot push；
3. 清除活动文档中已经发生的仓库事实漂移；
4. 缩小 SKILL.md / PROJECT_INSTRUCTIONS.md 的重复业务摘要，降低 LLM 上下文语义混合风险；
5. 明确 core-model-summary 的“语义需求状态”与“模板渲染状态”两层词汇，避免 required/displayed 双词汇歧义；
6. 处理 GitHub Actions Node 兼容警告与长期维护风险；
7. 清理少量 current-health 测试的历史版本命名债务，并评估 release/tag provenance。

明确不做：
- 不重新设计数学建模流程；
- 不改变 Problem Contract、Model Challenge、Human Model Approval、03A/03B、PQS、Workbook Schema、Project State Schema 的业务语义；
- 不把 MATLAB 改回数值求解；
- 不改变 Python full-fidelity 用户执行所有权；
- 不重新设计 v8 Template-First 写作架构；
- 不清理 legacy 内容本身，只处理“活动 surface 错把历史计划当 current fact”的问题；
- 不顺手加入新模型、新算法、新图表能力、新竞赛规则或新交付格式；
- 不为通过测试而删除/弱化已有约束。

权威事实源：
- core/bootstrap.yaml
- SKILL_CHANGE_GOVERNANCE.md
- .github/workflows/ci.yml
- .github/workflows/refresh-generated.yml
- GitHub main branch protection read-back
- SKILL.md / skills/mathmodel-skill/SKILL.md
- PROJECT_INSTRUCTIONS.md
- core/writing_reasoning_contract.yaml
- templates/latex/cumcm/hsk/template_manifest.yaml
- modules/05_writing/paper_writing_protocol.md
- scripts/generate_indexes.py
- 当前相关 tests

兼容性要求：
- v8.0.1 当前 runtime route、CLI、项目目录、Workbook、Project State、Python/MATLAB/LaTeX ownership 保持兼容；
- root/package Skill entrypoint parity 必须持续成立；
- V622 / legacy 默认隔离不改变；
- 已 accepted 的历史项目不因纯仓库治理、CI 或说明性整理自动 stale；
- 任何会改变活动 LLM 行为表面的修改必须单独评估版本升级与回归。

迁移要求：
- 仓库治理/CI/文档事实修复：无项目迁移；
- 入口 surface slimming：不得改变 current Authority，只减少重复摘要并增加引用；
- core-model-summary 词汇：保留 v7 只读兼容映射，禁止破坏旧项目读取。

总体验收：
- python scripts/lint_skill.py
- python -m unittest discover -s tests
- python scripts/generate_indexes.py --check
- 受影响专项测试
- 代表性 scripts/resolve_runtime.py / resolve_workflow.py smoke
- CUMCM/MCM-ICM/Diangong LaTeX CI 与 production attestation
- GitHub branch protection read-back
- generated metadata PR 闭环验证

回滚原则：
- 每个实施 PR 单独可回滚；
- GitHub settings-only 变更单独回滚，不通过改 Skill 源码模拟；
- 不进行跨主题巨型提交，避免需要整体回退。
```

---

## 1. 已确认的当前健康基线

### 1.1 当前没有发现需要立即重建的核心业务语义

本轮健康审计确认以下主链当前保持闭合：

- `core/bootstrap.yaml → core/workflow_router.yaml → route-specific contracts/modules/packs/templates`；
- root `SKILL.md` 与 `skills/mathmodel-skill/SKILL.md` 当前保持精确 parity；
- release carriers 当前统一为 `8.0.1`；
- generated indexes / `MANIFEST.sha256` 当前由 CI 重建并检查；
- Model Challenge → explicit Human Approval → current `locked_model_spec` 的 revision/hash 绑定未发现漂移；
- Module 03A 仍只负责 current-run primary computation admissibility + Primary Evidence Capture；
- Module 03B 仍独占 accepted 后的敏感性、压力场景、替代算法/结构、多 seed/初值 claim stability 等 alternative-world analysis；
- MATLAB 仍只消费 accepted workbook 绘图；
- DOCX 仍为显式可选分支，不是 LaTeX 前置；
- legacy / V622 默认不进入 active runtime。

因此，本计划**不以“重写 Skill”作为目标**。优先处理仓库治理、活动 surface 新鲜度和长期漂移风险。

### 1.2 当前明确问题

#### P0-A：GitHub `main` 未受平台保护

当前 `core/bootstrap.yaml` 已声明：

```text
branch_required: true
pull_request_required: true
direct_main_write_allowed: false
```

但 GitHub read-back 为：

```text
main.protected = false
required_status_checks.enforcement_level = off
```

即：

```text
Repository Policy != GitHub Enforcement
```

这是当前最高优先级仓库治理缺口。

#### P0-B：`refresh-generated.yml` 仍可在 `main` 上使用 `contents: write` 并执行 `git push`

当前 workflow 同时监听 `main` 与 feature branches，并在生成文件发生变化时直接 commit + push。

这与目标治理模型存在张力：

```text
期望：source change on feature branch
   → generated metadata refreshed on feature branch
   → PR CI / Generated file contract
   → merge
   → main already current

当前兜底：main push
   → generator detects drift
   → bot may write another main commit
```

Branch Protection 上线前必须先保证 feature-branch generated metadata 闭环可靠，否则保护后可能暴露现有补救性写入依赖。

#### P1-A：活动分支保护计划已经发生事实漂移

`docs/main-branch-protection-hardening-plan.md` 当前仍写：

- baseline Skill `7.16.0`；
- baseline main `9df210...`；
- repository `private`；
- private repository 套餐/Rulesets 403 是实施限制；
- implementation pending。

当前实际基线为：

- Skill `8.0.1`；
- main `529d547...`；
- repository `public`；
- main 仍未保护。

因此该文档的问题目标仍然相关，但 factual baseline 已不再 current。它不应继续作为活动事实说明长期存在。

#### P1-B：活动入口 surface 过重，存在未来 LLM 语义混合风险

当前 `core/bootstrap.yaml` 明确要求 `minimal_route_specific`，但 `SKILL.md` 与 `PROJECT_INSTRUCTIONS.md` 仍保存大量业务级摘要、版本演进说明、03A/03B、Figure、Writing、历史迁移等内容。

这些文本即使声明“非 Authority”，仍会先进入 LLM context。长期风险是：

```text
旧摘要 + 新 Authority → 隐性语义混合
```

目标不是删除必要入口，而是把活动入口收缩为：

```text
发现/触发
→ startup delegation
→ invariant boundaries
→ Authority pointers
→ resolver usage
```

具体业务规则回到唯一 Authority。

#### P1-C：core-model-summary 存在受控但容易误读的双词汇

当前兼容层同时存在：

```text
v7 semantic modes:
required / inline / not_applicable

v8 template rendering modes:
displayed / inline / omitted
```

当前映射是正确且有测试的：

```text
required       → displayed
inline         → inline
not_applicable → omitted
```

问题不是当前行为错误，而是维护者容易把两套词当成同一级 current enum。后续应显式命名为：

```text
semantic_summary_mode
rendering_mode
```

并保留 v7 read compatibility。

#### P2-A：GitHub Actions Node 兼容警告

当前 `.github/workflows/ci.yml` / `refresh-generated.yml` 使用 `actions/checkout@v4`、`actions/setup-python@v5`、`actions/upload-artifact@v4` 等。当前 runner 已出现 Node 20 deprecation / force-to-Node-24 warning。

目前 CI 仍通过，因此不是 blocker；但应在官方 action 原生 Node 24 版本稳定可用时升级，避免未来 runner hard failure。

#### P3-A：少量 current-health 测试仍使用历史版本文件名

例如某些 `test_v7141_*` 文件实际已经验证 current `8.0.1` 规则。功能没有错误，但文件名会让维护者误以为其只服务历史版本。

#### P3-B：GitHub Release provenance 可进一步增强

当前 release carriers、CHANGELOG、commit、CI 均存在，但 GitHub Releases 当前没有正式 release object。该项不影响 runtime，应保持低优先级，并在确认 tag 策略后另行处理。

---

## 2. 总体实施策略：禁止一个巨型 PR

本计划只是总控上下文。后续必须拆成单主题 PR。

推荐顺序：

```text
Phase 0  本计划审批
   ↓
Phase 1  Generated Metadata / Main Admission Hardening
   ↓
Phase 2  Stale Governance Doc Cleanup
   ↓
Phase 3  Active Entrypoint Surface Slimming
   ↓
Phase 4  Core Model Summary Vocabulary Clarification
   ↓
Phase 5  GitHub Actions Runtime Modernization
   ↓
Phase 6  Low-priority Hygiene / Release Provenance
```

任何阶段发现上游假设不成立时，停止该阶段，不带病进入后续 PR。

---

# Phase 1：Main Admission + Generated Metadata Hardening

## 3. 目标

把仓库治理从“文档要求 PR”升级为：

```text
feature branch
→ generated metadata current
→ pull request
→ required HSK Skill CI checks pass
→ merge main
→ main remains generated-current
```

并最终实现 GitHub 平台层：

```text
main.protected == true
```

### 3.1 本阶段的关键设计原则

1. **先修 generated metadata 闭环，再开启 strict branch protection。**
2. main 不应依赖 bot 在 merge 后补写 generated metadata。
3. `Generated file contract` 是 PR admission check；`refresh-generated` 是 feature branch convenience writer，不是 main bypass 通道。
4. Branch Protection 只消费现有经过验证的 check 名称，不通过改 CI job 名来迎合错误 settings。
5. 单维护者仓库不强制 reviewer approval 数量，避免把自己锁死；目标是 PR + CI，不是强制第二维护者。

## 4. 拟修改范围

### 4.1 PR 1A：generated metadata workflow hardening

**预计文件：**

- `.github/workflows/refresh-generated.yml`
- 必要时新增/调整 workflow tests 或静态测试
- generated files（仅由 `scripts/generate_indexes.py` / workflow 自动产生）

**不修改：**

- `core/**`
- `modules/**`
- `packs/**`
- 数学/写作业务 Authority
- Skill version carriers（除非实施时发现 workflow 行为被仓库治理定义为 release-visible 行为且 Governance 要求 patch；默认不升级）

### 4.2 推荐 workflow 目标行为

候选方案优先级：

#### 方案 A（推荐）：feature branch writer + main check-only

```text
push to supported feature branch
→ generate_indexes.py
→ changed? bot commit/push to same feature branch

push to main
→ generate_indexes.py --check or equivalent diff check
→ never commit/push
```

优点：

- 与 Branch Protection 完全一致；
- merge 后 main 不应发生二次 bot commit；
- 如果 main 出现 drift，会显式失败，而不是静默补救。

#### 方案 B：完全取消 writer，全部由开发者手工生成

不优先。会增加人工遗漏概率，也削弱现有 convenience workflow。

### 4.3 PR 1A 验收

至少验证：

- feature branch 修改活动源文件后，generated metadata 能自动更新；
- bot commit 只发生在 feature branch；
- main 路径不存在 `git push`；
- `Generated file contract` 对 stale metadata 仍 blocking；
- no recursive bot loop；
- no generated-only infinite trigger；
- `python scripts/generate_indexes.py --check` 通过；
- full unit tests 通过；
- current CI job names 未改变。

## 5. PR 1B / Repository Settings：Branch Protection

Branch Protection 属于 GitHub settings，不属于 Git tree。当前已连接 GitHub 工具可 read-back，但未暴露 branch-protection write action，因此实施时必须：

- 由仓库所有者在 GitHub Repository Settings 设置；或
- 使用经确认具备对应写权限且符合用户授权的官方 GitHub API/CLI 路径。

不得通过修改 Skill 代码“模拟”保护。

### 5.1 推荐配置

针对 `main`：

- Require a pull request before merging：**ON**
- Required approvals：**0**（单维护者场景）
- Require status checks to pass before merging：**ON**
- Require branch to be up to date before merging：优先 ON（若不会引入不可操作死锁）
- Allow force pushes：**OFF**
- Allow deletions：**OFF**
- Admin bypass：优先禁止；若平台选项与个人仓库权限模型冲突，记录实际可用配置

Required checks 以实施时 `main` 最近稳定 CI 的**实际 check 名称 read-back**为准，候选包括：

```text
Static contract lint
Python 3.10
Python 3.11
Python 3.12
Python 3.13
Python 3.14
LaTeX CUMCM
LaTeX MCM-ICM
LaTeX Diangong
Production LaTeX attestation
Generated file contract
```

### 5.2 Branch Protection Blocking 验收

- [ ] `main.protected == true`
- [ ] PR requirement enabled
- [ ] required checks 与实际 CI 名称完全一致
- [ ] force push disabled
- [ ] deletion disabled
- [ ] normal PR path remains usable
- [ ] generated metadata can close on feature branch without main bot write
- [ ] merge 后 main 不出现补救性 generated bot commit

### 5.3 回滚

若 settings 造成合并死锁：

1. 仅回滚/放宽冲突 protection setting；
2. 不改 Skill runtime；
3. 找到具体 check / permission 冲突；
4. 重新启用最小保护配置；
5. read-back + PR smoke 后再宣布完成。

---

# Phase 2：Stale Governance Documentation Cleanup

## 6. 目标

解决 `docs/main-branch-protection-hardening-plan.md` 仍以 v7.16/private facts 描述当前仓库的问题，同时避免活动索引继续把历史施工计划当 current reference。

## 7. 推荐处理

在 Phase 1 完成后执行，而不是提前改写历史事实。

推荐：

1. 将旧计划移动/归档到 `legacy/architecture/`，保留 provenance；
2. 在旧位置如需兼容，保留极短 pointer，而不是继续维护双份完整计划；
3. 若 Branch Protection 已完成，新增/更新 current repository governance summary 只记录**最终状态和 Authority pointer**，不再保留大量一次性施工步骤；
4. 重新生成 Active Index / MANIFEST。

### 7.1 预计文件

- `docs/main-branch-protection-hardening-plan.md`（移动、缩短为 pointer 或删除 active copy，具体按 generator/引用情况决定）
- `legacy/architecture/...`（历史归档）
- `REPOSITORY_INDEX.md` / `SKILL_FILE_INDEX.md` 仅在生成器或当前导航确实需要时更新
- generated metadata 自动更新

### 7.2 不允许

- 不把历史计划内容复制到多个 current docs；
- 不让 active runtime 依赖 legacy；
- 不修改 Skill version；
- 不改变数学建模业务语义。

### 7.3 验收

- Active Index 不再把过时 v7.16/private 计划呈现为 current operational fact；
- legacy provenance 可追溯；
- repository search 中 current docs 不再声称 repo private / baseline 7.16；
- `generate_indexes.py --check` 通过。

---

# Phase 3：Active Entrypoint Surface Slimming

## 8. 目标

使“minimal bootstrap”在 LLM 上下文层真正成立，而不仅是 resolver 层成立。

目标结构：

```text
SKILL.md
├─ metadata / triggers
├─ runtime entry contract
├─ capability-level summary（短）
├─ authority delegation
├─ compatibility boundary
└─ release note pointer

PROJECT_INSTRUCTIONS.md
├─ startup procedure
├─ project-memory recovery procedure
├─ pre-delivery-gate rule
├─ user execution ownership pointer
├─ repository modification procedure pointer
└─ no duplicated domain rulebook
```

详细业务规则继续只存在于 rightful Authority。

## 9. 风险等级与版本建议

虽然目标是“减少重复、不改变 Authority”，但 `SKILL.md` / packaged Skill / Agent-facing instructions 是 LLM 实际入口文本，缩减内容可能改变模型行为分布。

因此本阶段**不能简单按纯 docs 处理**。

实施前应按 `SKILL_CHANGE_GOVERNANCE.md` 重新评估；默认建议：

```text
8.0.1 → 8.0.2 patch
```

理由：修复活动入口重复语义和未来漂移风险，保持所有既有接口兼容。

## 10. 拟修改文件

核心：

- `SKILL.md`
- `skills/mathmodel-skill/SKILL.md`
- `PROJECT_INSTRUCTIONS.md`
- 必要时 `AGENTS.md` / `agents/openai.yaml` 只做 pointer 对齐，不扩张内容
- `CHANGELOG.md`
- release carriers（若最终定为 patch）
- entrypoint parity / current health / read-path tests

原则上不修改：

- `core/workflow_router.yaml` 的业务 route
- Module 01/02/03/04/05/06 业务内容
- Workbook / Project State Schema
- template topology

## 11. 删除/压缩标准

### 11.1 应从入口移除的内容类型

- v7.16 / v7.18 / v7.19 / v8.0.0 / v8.0.1 的长篇历史演进正文；
- 已由 `core/numerical_verification_contract.yaml` 权威定义的 03A PQS 详细清单；
- 已由 `modules/03_result_analysis.md` 定义的 03B 详细分析类别；
- 已由 Figure Authority 定义的组合图型细节；
- 已由 writing contracts 定义的详细章节写法；
- 任何“为保持同步而复制”的业务枚举。

这些应改成简短 pointer，例如：

```text
Primary numerical validity follows core/numerical_verification_contract.yaml.
Post-acceptance analysis follows modules/03_result_analysis.md.
```

### 11.2 必须保留的入口硬边界

- bootstrap-first；
- use `resolve_runtime.py`；
- do not preload repository；
- explicit Model Approval before current primary/preprocessing code；
- user owns task-specific numerical execution；
- current framework / accepted workbook / project state 三种事实源边界；
- legacy not default；
- resolver-returned pre-delivery gates authoritative；
- root/package parity。

## 12. 防回归测试

新增或加强：

- entrypoint maximum allowed duplicated authority fragments（基于禁止出现完整 policy blocks，而不是脆弱字数阈值）；
- root/package exact parity；
- entry contract includes mandatory pointers；
- no V622/legacy active pointer leakage；
- representative resolver output unchanged；
- version carrier parity；
- current runtime semantic fixtures unchanged。

### 12.1 关键验收

必须证明：

```text
before and after:
resolver route plan == semantically equivalent
Model Approval boundary == unchanged
03A/03B ownership == unchanged
Python/MATLAB ownership == unchanged
writing Authority chain == unchanged
legacy isolation == unchanged
```

如果任何业务行为需要“顺便调整”，停止该 PR，另开单主题修复。

---

# Phase 4：Core Model Summary Vocabulary Clarification

## 13. 目标

把当前兼容映射从“读者自己理解两套 enum”升级为显式两层概念：

```text
semantic_summary_mode:
  required
  inline
  not_applicable

rendering_mode:
  displayed
  inline
  omitted
```

核心含义：

- semantic mode 回答“数学叙事上是否需要独立收束”；
- rendering mode 回答“CUMCM 模板最终怎样呈现”；
- 二者通过唯一映射连接；
- v7 项目继续只读兼容。

## 14. Authority 边界

建议继续保持：

- semantic compatibility / mapping：`core/writing_reasoning_contract.yaml`
- actual CUMCM rendering authority：`templates/latex/cumcm/hsk/template_manifest.yaml#core_model_summary_rendering`
- ordinary prose consumer：`modules/05_writing/paper_writing_protocol.md`

不得在 `SKILL.md`、review、LaTeX Adapter、DOCX、模板示例里重新定义独立 enum。

## 15. 版本建议

如果 Phase 3 已发布 `8.0.2`，本阶段默认建议单独 patch：

```text
8.0.2 → 8.0.3
```

原因：虽然结果呈现预期不变，但 Authority field naming / compatibility semantics 会发生规范化，属于可验证的语义修复。

若实施前确认只需 consumer 文案澄清而无需 Authority/schema-like field 改名，则可重新评估为 docs-only；不得预先强行定级。

## 16. 拟修改文件

可能包括：

- `core/writing_reasoning_contract.yaml`
- `templates/latex/cumcm/hsk/template_manifest.yaml`（只有需要明确 mapping pointer 时）
- `modules/05_writing/paper_writing_protocol.md`
- `core/output_contract.yaml` pointer 字段
- relevant tests：template authority、writing structure、current health
- `CHANGELOG.md` / version carriers（若 patch）

### 16.1 兼容要求

- v7 `required/inline/not_applicable` 旧项目读取继续成立；
- new CUMCM rendering 仍输出 `displayed/inline/omitted`；
- 不自动重排历史论文；
- 不自动增加/删除“核心模型汇总”小节；
- simple-problem anti-bloat 不变。

### 16.2 验收

- compatibility mapping 只有一个 Authority；
- consumer 不复制 enum business rule；
- template tests 通过；
- old project fixture readable；
- new project rendering unchanged。

---

# Phase 5：GitHub Actions Runtime Modernization

## 17. 目标

消除当前 runner 的 Node compatibility warning，降低未来 Actions runtime hard failure 风险。

## 18. 原则

1. **先查官方 action 当前稳定 major 与 runtime requirement，再升级。**
2. 不凭猜测把 `checkout@v4` 机械改成不存在/未稳定的版本。
3. 每个 action 升级都检查 release notes / breaking changes。
4. 本 PR 只处理 action runtime modernization，不重构 CI 业务逻辑。
5. 不改变 CI job display names，避免 Branch Protection required checks 漂移。

## 19. 预计文件

- `.github/workflows/ci.yml`
- `.github/workflows/refresh-generated.yml`
- 其他使用同一 action major 的 workflow（实施时 repository search 确认）

可选后续项：

- 将第三方 Actions 从 floating major 进一步 pin 到 commit SHA；
- 该供应链硬化若范围较大，应另开 PR，不与 Node upgrade 混合。

## 20. 验收

- Node deprecation warning 消失或显著减少；
- current job names unchanged；
- full CI green；
- generated metadata writer behavior unchanged；
- LaTeX actions still compile all 3 competition templates；
- production attestation unchanged。

Skill runtime 不变时原则上不升级 Skill version；若 Governance 实施时判断 CI contract 属于 release-visible interface，再单独决定。

---

# Phase 6：Low-priority Hygiene

## 21. Current-health 测试命名

目标：把实际上维护 current rules 的历史命名测试重命名，例如：

```text
test_v7141_skill_health.py
→ test_current_skill_health.py
```

只重命名真正已经变成 permanent current-health guard 的文件。

不得：

- 把真实历史迁移回归测试全部去版本化；
- 顺手重写断言；
- 以“清洁”为由删除历史兼容测试。

此阶段应是纯维护 PR。

## 22. Release / Tag Provenance

当前 GitHub Releases 没有正式 release object。后续可评估：

```text
release carrier version
↔ immutable git tag
↔ GitHub Release
↔ CHANGELOG
↔ release commit CI status
```

该项不影响 runtime，不进入前五阶段 blocking path。

在制定 tag/release 自动化前必须确认：

- 当前是否已有 tags；
- tag 命名策略；
- release 是否需要 assets；
- 是否与 Codex plugin distribution 有绑定要求。

---

## 23. 明确不修的“假问题”

以下项目在审计中当前是健康的，不应因本计划产生无意义重构：

### 23.1 subordinate contract 中的旧版本号

例如：

```text
introduced_in_skill_version: 7.4.2
skill_compatibility: >=7.4.2,<9.0.0
```

这是 introduction/compatibility metadata，不是 current release carrier。禁止全仓库盲目替换成 `8.0.1`。

### 23.2 legacy 文件大量存在

legacy 是 provenance / migration archive。目标是保持默认隔离，不是“为了干净全部删除”。

### 23.3 03A/03B 当前边界

当前未发现需要重写。不得借健康修复把敏感性/稳健性重新塞回主求解质量门。

### 23.4 Writing Template-First 架构

v8.0.1 已有 chapter capability preservation tests；本计划不重新推翻 Template Authority / Writing Protocol / Reasoning Authority / Adapter 分工。

---

## 24. 每个实施 PR 的强制模板

后续每个 PR 都必须在描述中填写：

```text
变更背景：
直接目标：
明确不做：
当前 main SHA：
当前 Skill version：
目标 Skill version：
变更等级：
权威事实源：
本 PR 修改文件：
检查但不修改的关联文件：
兼容与迁移：
测试：
生成文件状态：
GitHub settings 依赖：
风险：
回滚：
```

并附：

```text
python scripts/lint_skill.py
python -m unittest discover -s tests
python scripts/generate_indexes.py --check
```

的真实结果；不得在 CI 尚未完成时声明全部通过。

---

## 25. 每阶段开始前重新冻结事实

由于本计划可能跨多个 PR，任何阶段开始前必须重新读取 `main`，禁止直接沿用本计划里的旧 SHA。

每次至少确认：

1. `core/bootstrap.yaml`；
2. `SKILL_CHANGE_GOVERNANCE.md`；
3. current Skill version；
4. current `main` SHA；
5. open overlapping PR；
6. 本阶段 Authority 文件；
7. GitHub platform state（涉及 settings 时）。

如果 current `main` 已经通过其他 PR 修复了本阶段问题，应更新/缩小范围，不重复实施。

---

## 26. 完成定义

本 remediation program 只有在以下条件成立时才能宣布完成：

### Repository Governance

- [ ] `main` 受平台保护；
- [ ] 正常维护必须经过 PR；
- [ ] required CI checks 实际生效；
- [ ] force push / deletion 受限制；
- [ ] main 不依赖 generated bot 补救性写入。

### Active Surface

- [ ] stale v7.16/private branch-protection plan 不再作为 current active fact；
- [ ] SKILL / PROJECT_INSTRUCTIONS 不再复制大段业务 Authority；
- [ ] root/package entrypoint parity 保持；
- [ ] minimal-route-specific 原则在 LLM context 层更可信。

### Semantic Hygiene

- [ ] core-model-summary semantic/rendering mode 边界明确；
- [ ] v7 compatibility 保持；
- [ ] 03A/03B、Model Approval、Workbook/Project State 等既有业务边界未受影响。

### CI / Maintenance

- [ ] Actions runtime 警告已处理或有明确仍受官方依赖限制的记录；
- [ ] full CI green；
- [ ] generated files current；
- [ ] current health tests 命名不再误导（若 Phase 6 被批准执行）。

---

## 27. 审批选项

用户审批时建议明确选择：

### A. 批准完整计划

按 Phase 1 → 6 顺序逐阶段实施；每个阶段仍先给出对应 PR 范围与 diff 摘要，不自动合并。

### B. 仅批准 P0/P1

只执行：

- Phase 1 Main Admission + Generated Metadata Hardening；
- Phase 2 stale governance doc cleanup；
- Phase 3 active entrypoint surface slimming；
- Phase 4 vocabulary clarification。

暂不执行 Actions / test naming / release provenance。

### C. 仅批准 P0

只执行：

- generated metadata workflow hardening；
- Branch Protection settings；
- 完成后归档旧 branch-protection plan。

### D. 修改计划后再审批

用户可直接指出：

- 删除某 Phase；
- 合并/拆分某 PR；
- 修改版本策略；
- 调整 Branch Protection 配置；
- 不允许触碰的文件；
- 希望优先处理的风险。

在获得明确审批前，本计划保持 `PLANNING ONLY`。

---

## 28. 实施记录

```text
计划审批：pending
审批范围：pending

Phase 1：pending
Phase 2：pending
Phase 3：pending
Phase 4：pending
Phase 5：pending
Phase 6：pending

最终 main SHA：pending
最终 Skill version：pending
最终 Branch Protection read-back：pending
最终 CI：pending
```
