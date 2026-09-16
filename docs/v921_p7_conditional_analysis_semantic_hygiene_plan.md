# v9.2.1 P7 条件式结果分析语义卫生修复计划

> 状态：**planning_only / implementation_not_started**  
> 计划基线：`main@86a8b54e761021cdbe15d8eb879068895d049326`  
> 当前 Skill release：`9.2.0`  
> 候选修复 release：`9.2.1`（仅在实际行为修复进入 release carrier 时执行）  
> 本文件角色：**维护计划与验收锚点，不是 Runtime / Workflow / Numerical / Writing Authority**  
> 当前实现状态：**本计划落库时不修改任何运行代码、Authority、模板、测试或 release carrier**

---

## 0. 修改简报

### 修改主题

收口 v9.2.0 发布后发现的 **P7 条件式结果深化分析（Analysis Necessity Gate）迁移残留**，使 Authority、执行合同、MATLAB 活动模板、Artifact Packs、Agent/项目说明与回归测试统一服从同一语义：

> 每问基础交付为主求解 Python + 主工作簿 + `qX_plot.m` 三文件；主工作簿 accepted 后先执行 Analysis Necessity Gate；仅当 Gate=`required` 时，才增加独立 03B Python + 结果深化工作簿两文件；Gate=`not_required` 时必须有非空理由，不生成或伪造 03B 文件，也不得声称已验证稳健性/稳定性。

### 当前版本

`9.2.0`

### 候选目标版本

`9.2.1`

### 变更等级

**patch 候选**。

理由：当前已确认至少存在一个会让合法 `not_required` 项目在 Figure Evidence 阶段失败的活动 MATLAB 模板行为错误，同时存在 User Execution Authority 与已发布 P7 Output/Router 语义不一致。修复目标是恢复 v9.2.0 已声明能力的一致实现，不新增新的业务能力、目录、Schema、CLI 或流程阶段。

若后续实施审查发现仅需文档改写且不存在行为修复，则重新裁决版本；不得为了预设 `9.2.1` 而机械 bump。

### 直接目标

1. 建立 P7 条件式 03B 的**单一、可执行语义闭环**；
2. 修复 `result_analysis_status=not_required` 时 MATLAB 活动模板仍无条件要求 03B 工作簿的问题；
3. 让 `core/user_execution_contract.yaml` 的 analysis activation 与 Router/Manifest/Output Contract 一致；
4. 清除活动说明、Pack、README 中“新项目固定五文件 / 两个工作簿必然存在 / accepted 后必然生成 03B”的旧口径；
5. 用行为级回归锁定 `3 + conditional 2`，替换仍在维护固定五文件文本的旧断言；
6. 清理 `lint_skill.py` 中仅用于屏蔽旧固定五文件错误的 P7 适配债务，但**只能在底层检查已迁移并有等价/更强回归后执行**；
7. 更新 P9/优化状态记录，使发布状态与当前 `main` 一致；
8. 修复本轮审计确认的低风险卫生项，例如同一 YAML 映射中的重复键，但不得扩大为通用清仓。

### 明确不做

本轮不得顺手执行以下事项：

- 不重新设计 Analysis Necessity Gate 的业务判据；
- 不把 03B 恢复成所有小问必做；
- 不把 `not_required` 解释为“稳健性通过”；
- 不修改主求解 PQS / Numerical Verification 判据；
- 不修改 Model Approval、SIB、semantic revision/identity、typed stale 的业务语义；
- 不修改 Workbook Schema 2.3.0 的表结构，除非实施时发现真实 schema 冲突且经过独立裁决；
- 不删除或降低任何 CI、gate、测试、断言强度；
- 不为了让 CI 通过新增无依据 allowlist/exception；
- 不拆 `scripts/lint_skill_checks.py`；P8 已基于 host-adapter 耦合裁决“不做机械拆分”；
- 不删除 V622 compatibility pointers；
- 不删除 `legacy/` 历史材料；
- 不机械删除 P1–P9 维护证据文档；
- 不处理 v10 才允许裁决的 `FULL_FIDELITY_CONFIG / FULL_RUN_CONFIG`、P5a versionless receipt 等只读兼容 reader；
- 不全仓库盲目替换“5 文件”“9.2.0”“v7.x”等字符串；每一处必须先按 runtime / active consumer / compatibility / history provenance 分类。

### 权威事实源

实施前必须从最新 `main` 重新读取，不得只依赖本计划：

- `core/bootstrap.yaml`
- `SKILL_CHANGE_GOVERNANCE.md`
- `core/workflow_router.yaml`
- `core/module_manifest.yaml`
- `core/output_contract.yaml`
- `core/project_state.schema.yaml`
- `core/runtime_assurance_contract.yaml`
- `core/user_execution_contract.yaml`
- `modules/03_result_analysis.md`
- `modules/04_figure_evidence.md`
- `core/workbook_schema.yaml`（仅用于核对 MATLAB/工作簿接口，不默认改）

### 预计修改范围

见第 5 节。该清单是**候选影响面**而非授权一次性修改全部文件；每个实施 PR 只修改其职责必要文件。

### 禁止触碰文件/区域

除非实施中发现本计划未覆盖的真实阻塞并停止等待裁决，否则不修改：

- `legacy/**`
- `core/model_approval_contract.yaml`
- `core/state_transition_contract.yaml`
- `core/numerical_verification_contract.yaml`
- `core/workbook_schema.yaml` 的现有 schema/version 语义
- competition edition rules
- LaTeX 模板结构（P7 appendix 已有独立条件语义，不在本轮重构）
- P8 validator architecture
- v10 compatibility removal surface

### 兼容性要求

- v9.2.0 已生成的五文件项目继续可读、可运行；
- Gate=`required` 的新项目仍形成五文件；
- Gate=`not_required` 的新项目形成基础三文件，后续 Figure/Writing/Review/Submission 不得因缺 03B 文件而误报；
- 旧 v6.6/v7.x 只读兼容不因本 patch 被强制迁移；
- `FULL_*` / versionless RUN_RECEIPT 兼容窗口维持 P9 已发布裁决；
- 不改变公共 CLI 参数与目录根命名。

### 迁移要求

本 patch **不要求用户批量迁移历史项目**。

只对“重新进入当前流程”的项目按 current state 判定：

- `result_analysis_status=passed`：03B 工作簿/代码按现有 accepted/stale/hash 规则消费；
- `result_analysis_status=not_required`：要求非空 `result_analysis_requirement_reason`，不得要求不存在的 03B 文件；
- 旧项目没有 P7 字段：继续走既有 compatibility/read path；不得由文档修复自动改写项目状态。

### 验收测试

至少包括：

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests
python scripts/generate_indexes.py --check
```

并增加第 7 节定义的 P7 跨表面行为回归、MATLAB 静态/真实 preview 相关检查、代表性 resolver/sync 场景以及最终 GitHub Actions 全量门禁。

### 回滚方式

每个实施 PR 独立可回滚；release carrier 只在所有语义/模板/回归 PR 完成后进入最后收尾 PR。任何阶段若发现业务语义需要重新裁决，停止后续 PR，不用 release bump 掩盖未决问题。

---

## 1. 背景与问题定义

v9.2.0 已发布 P7 的核心能力：结果深化分析不再是所有 accepted 主结果之后的固定步骤，而由 **Analysis Necessity Gate** 决定 `required` / `not_required`。当前核心主干已经存在正确语义：

- Router 将 `result_analysis` 标记为 conditional module；
- Module Manifest 仅在 Gate=`required` 时生成/消费真实 03B artifact；
- Output Contract 定义基础三文件与 required 时追加两文件；
- Project State 支持 `result_analysis_status=not_required` 与 `result_analysis_requirement_reason`；
- Runtime Assurance 可以在不伪造 03B workbook 的前提下把“accepted primary + reasoned not_required”提升为 `validated_results`；
- Figure Evidence 的 manifest input 已把 `result_analysis_workbook` 改为 `result_analysis_status == passed` 时的 conditional input；
- CUMCM appendix 已是按真实材料启用，而非默认生成空附录。

但 post-release 仓库级审计发现，P7 的迁移没有完整传播到所有活动消费者。问题不是“核心 P7 没实现”，而是：

> **核心 Authority 已经进入 3 + conditional 2；若干执行合同、模板、Pack、说明和旧回归仍假设 fixed five-file。**

因此当前状态属于 **post-release semantic hygiene defect cluster**，不是重新设计 P7，也不是推倒 P1–P9。

---

## 2. 已确认问题清单

### 2.1 高优先级：User Execution Authority 的 analysis activation 仍偏旧

当前 `core/user_execution_contract.yaml` 仍存在类似：

```yaml
stage_activation:
  analysis: accepted_primary_workbook_required
```

以及“主工作簿 accepted 后新建问题X结果深化分析.py”的无条件措辞。

这与当前 Router / Manifest / Output Contract 的 published semantics 不一致。正确关系应体现：

```text
accepted primary workbook
        ↓
Analysis Necessity Gate
   ├─ required     → activate 03B execution
   └─ not_required → persist reason; no 03B code/workbook
```

**修复原则：** User Execution Authority 只定义“03B 被激活后的用户执行所有权/协议”，是否激活必须服从 Gate；不能在 Execution Authority 内重新创造第二套 Gate 判据。

### 2.2 高优先级：`q1_plot.m` 对 03B workbook 无条件 `assert`

当前活动模板会构造：

```matlab
resultAnalysisBook = fullfile(resultDir, "问题一结果深化分析.xlsx");
assert(isfile(resultAnalysisBook), ...)
```

这会导致一个完全合法的 P7 项目：

```text
accepted primary
+ result_analysis_status=not_required
+ non-empty reason
+ no 03B workbook
```

在 Figure Evidence 阶段直接失败。

这是本轮最明确的**功能性 bug**。

**修复原则：**

- 主工作簿始终是正式 Figure 的可用事实源；
- 03B 工作簿只有在当前状态/证据要求其存在时才可要求；
- generic MATLAB template 不得因为定义了 `resultAnalysisBook` 变量就无条件把它变成必需文件；
- 如果实例化后的某张图明确引用深化证据，则该实例必须 fail closed 地要求 03B workbook，而不是静默回退到主工作簿；
- 不允许“缺 03B 就用主工作簿伪装敏感性/稳健性图”。

### 2.3 中高优先级：活动说明/Packs 仍硬编码固定五文件

已确认需逐项复核的活动表面包括但不限于：

- `PROJECT_INSTRUCTIONS.md`
- `AGENTS.md`
- `RUNTIME_ROUTER.md`
- `packs/artifact/code.md`
- `packs/artifact/figure.md`
- `packs/artifact/review.md`
- `packs/artifact/full_submission.md`
- `templates/code/starter/README.md`
- `templates/code/hsk_pipeline/README.md`
- `templates/matlab/README.md`
- `templates/writing/code_appendix_description.md`
- 可能引用固定五文件语义的其它 active templates / scripts README

典型旧口径包括：

- “新项目每问必须五文件”；
- “每问两个标准工作簿”；
- “主工作簿 accepted 后生成深化脚本”；
- “两类工作簿均验收后再生成 qX_plot.m”；
- reproducibility package 把每问 03B 文件当成无条件标准结构。

**修复原则：** 非 Authority consumer 不复制完整目录合同；应引用 `core/output_contract.yaml`，必要时只给最小摘要：

```text
基础三文件；Gate=required 时追加 03B 两文件。
```

### 2.4 中高优先级：回归测试同时维护新旧两套语义

当前已存在新 P7 测试验证：

- `not_required` + reason 可以产生 `validated_results`；
- 不生成 fake analysis workbook；
- Router/Manifest/Appendix 已条件化。

但 `tests/test_repository_hygiene.py` 等仍存在要求活动说明包含“五文件合同”的断言。

这造成：

> **CI 全绿 ≠ 跨表面语义一致。**

更具体地说，测试一边验证 `core/output_contract.yaml` 的 3+2 条件结构，一边又要求 `PROJECT_INSTRUCTIONS.md` / Review Pack 继续出现 fixed-five 文本。

**修复原则：** 不删除回归覆盖，而是把旧断言替换为更强的条件式不变量。

### 2.5 中优先级：`lint_skill.py` 仍通过 wrapper 屏蔽旧 fixed-five 错误

当前 `scripts/lint_skill_checks.py` 仍含历史 fixed-five 检查；`scripts/lint_skill.py` 用 `_P7_OBSOLETE_CONTRACT_ERRORS` 过滤这些错误，同时新增 P7 current-contract 检查。

这在 P7 迁移期是合理桥接，但不能长期成为“新语义靠 wrapper 抵消旧语义”的结构。

**修复原则：**

1. 先把底层 `lint_skill_checks.py` 的相关检查改成 current 3+2 semantics；
2. 保留或增强 P7 断言覆盖；
3. 确认错误集合/调用顺序/host-adapter 行为没有意外变化；
4. 再删除只用于 suppress obsolete fixed-five errors 的过滤项；
5. 不借机拆大型 validator。

### 2.6 中低优先级：优化状态记录未闭合

`docs/skill_optimization_status.md` 仍记录 P9“实施中，PR #171，目标 v9.2.0”，而当前 P9 已合并、release 已是 9.2.0。

该文件不是 Runtime Authority，但属于维护证据漂移。

**修复原则：** 只更新最终状态，不重写 P1–P8 历史过程。

### 2.7 低优先级：Output Contract 存在重复 YAML key

`core/output_contract.yaml#per_question` 当前同一映射中重复出现 `no_auxiliary_files_by_default: true`。

当前两个值一致，现用 parser 下不造成业务差异，但重复 key 会：

- 增加严格 parser/未来 tooling 风险；
- 降低 contract 可读性；
- 掩盖未来“一处改、一处没改”的漂移。

**修复原则：** 只删除重复定义，不改变值与语义；增加/利用 duplicate-key hygiene 检查时，不得扩大成 YAML parser 全仓重构。

### 2.8 低优先级：活动模板 README 标题带旧 release-like 版本

已确认：

- `templates/code/starter/README.md` 标题仍含 `v7.15.0`；
- `templates/code/hsk_pipeline/README.md` 标题仍含 `v7.0.0`。

这些可能表示 template lineage，而非 Skill release carrier，因此**不能机械改成 9.2.1**。

**修复候选：** 改成 release-neutral 标题，或明确写“template lineage / not Skill release”。只有在当前 tests/文档能证明不依赖旧标题语义时才处理。

---

## 3. 目标状态与核心不变量

### 3.1 唯一生命周期语义

每问必须满足：

```text
proposed/locked model
→ primary code
→ user full-fidelity primary execution
→ accepted primary workbook
→ Analysis Necessity Gate
   ├─ required
   │    → 03B code
   │    → user full-fidelity analysis execution
   │    → accepted 03B workbook
   │    → result_analysis_status=passed
   └─ not_required
        → non-empty result_analysis_requirement_reason
        → no 03B code required
        → no 03B workbook required
        → no robustness/stability claim implied
→ validated_results
→ Figure / Writing / Review / Submission
```

### 3.2 文件布局不变量

```text
问题X求解/
├─ 问题X求解.py                       # always after applicable approval/data gates
├─ 问题X求解结果.xlsx                 # required after primary execution
├─ qX_plot.m                           # Figure stage
├─ [问题X结果深化分析.py]             # only Gate=required
└─ [问题X结果深化分析.xlsx]           # only Gate=required and analysis executed
```

不得把这解释为“新标准三文件，五文件废弃”。正确语义是：

- **base = 3**；
- **required-analysis extension = +2**；
- total = 5 only when analysis is required。

### 3.3 Figure 不变量

- 主结果图只需要主工作簿即可成立；
- 只有真实 03B 证据存在且被目标 Figure 使用时才要求 03B workbook；
- `not_required` 项目不得因为缺 03B workbook 阻塞 Figure；
- 如果脚本/图合同声明使用 03B sheet/header，则缺 workbook 必须 fail closed；
- MATLAB 不重新执行 03B 或从主结果猜测 03B 数据。

### 3.4 Review/Submission 不变量

- Review 检查 Output Contract，而不是自建 fixed-five Authority；
- reproducibility package 收集“当前项目实际存在且 current 的必要复现文件”，不凭固定模板要求伪造 03B；
- official package 完全服从 verified edition rules，不受 3/5 文件内部结构影响；
- `not_required` 必须保留 reason 的审计链。

### 3.5 Test/Lint 不变量

不得出现以下反模式：

```text
新测试：assert 3+2 conditional
旧测试：assert active docs still say fixed five
lint wrapper：delete obsolete fixed-five errors after they are produced
```

目标是所有检查直接验证同一 current contract。

---

## 4. 根因分析

### 4.1 直接根因

P7 主要修改集中在 Output Contract、Router、Manifest、State、Runtime Assurance、Sync 与 Appendix gate；外围 active consumers 没有作为一个完整 impact matrix 被全部纳入专项回归。

### 4.2 为什么 CI 没发现

1. P7 专项测试覆盖了核心状态机，但没有覆盖所有 consumer surfaces；
2. repository hygiene 中仍有历史 fixed-five 正向断言；
3. `lint_skill.py` 用 wrapper/filter 临时兼容旧 validator 断言；
4. MATLAB 模板的真实行为检查更侧重 publication rendering/profile，而没有建立 `not_required` 无 03B workbook 的代表 fixture。

### 4.3 本轮必须避免的错误修复方式

- 只改文档，不修 q1_plot 行为；
- 只把 `assert(isfile(resultAnalysisBook))` 删除，却允许脚本在需要 03B 数据时静默回退；
- 全仓 `五文件 -> 三文件` 替换；
- 删除旧测试而不新增条件式等价覆盖；
- 保留底层旧 fixed-five validator，仅继续扩大 wrapper/filter；
- 为了“顺便干净”删除 legacy/V622/history；
- 把 patch 扩成 lint architecture refactor。

---

## 5. 候选影响面清单

> 实施时必须从最新 main 重新搜索。下表是当前审计形成的候选范围，不保证每个文件最终都需要修改。

### 5.1 Authority / core

| 文件 | 当前风险 | 候选动作 |
|---|---|---|
| `core/user_execution_contract.yaml` | analysis activation 无条件化残留 | 对齐 Gate activation；不复制 Gate 判据 |
| `core/output_contract.yaml` | 重复 key；作为目标语义事实源 | 仅去重复 key；保持 3+2 语义不变 |
| `core/workflow_router.yaml` | 当前语义基本正确 | 只核对，不默认修改 |
| `core/module_manifest.yaml` | 当前语义基本正确 | 只核对，不默认修改 |
| `core/project_state.schema.yaml` | current `not_required` 已存在 | 只核对，不默认修改 |
| `core/runtime_assurance_contract.yaml` | current conditional evidence 已存在 | 只核对，不默认修改 |
| `core/workbook_schema.yaml` | schema 不是当前根因 | 只核对，不默认修改 |

### 5.2 Runtime/maintenance scripts

| 文件 | 当前风险 | 候选动作 |
|---|---|---|
| `scripts/lint_skill_checks.py` | 仍产生 fixed-five obsolete errors | 原位升级检查到 current 3+2，不拆模块 |
| `scripts/lint_skill.py` | P7 obsolete-error filtering 债务 | 底层迁移完成后删除对应 suppress；保留 current P7 checks |
| `scripts/sync_project.py` | current P7 语义基本正确 | 代表性回归核对，不默认修改 |
| `scripts/runtime_assurance.py` | current `not_required` hydration 正确 | 回归核对，不默认修改 |
| `scripts/project_snapshot.py` | current skip logic 已存在 | 回归核对，不默认修改 |
| `scripts/validate_submission_package.py` | generic reproducibility validator 不强制 03B specifically | 核对即可，除非新 fixture 发现真实问题 |

### 5.3 MATLAB / Figure consumers

| 文件 | 当前风险 | 候选动作 |
|---|---|---|
| `templates/matlab/q1_plot.m` | 无条件 assert 03B workbook | 修复为条件存在；真实使用 03B 时仍 fail closed |
| `templates/matlab/README.md` | fixed-five / two-workbook 表述 | 改为 base3 + conditional2 |
| `packs/artifact/figure.md` | “两个标准工作簿”默认存在 | 明确主 workbook required、03B conditional |
| `templates/figure/result_figure_contract.md` | Source workbook 可选项需核对 | 保持条件选择，不把 03B 设为必需 |
| `templates/figure/figure_plan.md` | wording 基本可兼容 | 核对是否暗示 03B 必然存在 |
| `templates/figure/figure_paper_closure.md` | wording 基本可兼容 | 同上 |

### 5.4 Code generation consumers

| 文件 | 当前风险 | 候选动作 |
|---|---|---|
| `packs/artifact/code.md` | 默认维护两个 Python / 两工作簿 | 改为 03A always + 03B conditional |
| `templates/code/starter/README.md` | accepted 后无条件生成 03B；推荐固定五文件 | 加 Gate 分支；候选 release-neutral 标题 |
| `templates/code/hsk_pipeline/README.md` | 03B/两工作簿无条件化说明 | 明确兼容 API 与 Gate activation；候选 release-neutral 标题 |
| `templates/code/hsk_pipeline/main_pipeline.py` | legacy/explicit orchestration API 存在 | **默认不改**；只验证它不会成为新项目默认自动 03B 路径 |

### 5.5 Agent / navigation / review / submission consumers

| 文件 | 当前风险 | 候选动作 |
|---|---|---|
| `AGENTS.md` | “two current standard workbooks” 等旧口径 | 改为 primary required / analysis conditional |
| `PROJECT_INSTRUCTIONS.md` | 明确“最终默认恰好五个文件” | 改为引用 Output Contract + 3+2 摘要 |
| `RUNTIME_ROUTER.md` | 概念完整链中 result_analysis 看似无条件 | 显式插入 Analysis Necessity Gate 分支 |
| `modules/06_review_delivery.md` | 用“五文件合同”概称但声明回指 Output Contract | 候选改成“per-question conditional layout contract” |
| `packs/artifact/review.md` | 硬编码 fixed-five tree | 删除平行 Authority，改为引用 Output Contract + conditional audit |
| `packs/artifact/full_submission.md` | reproducibility 固定五文件 | 按 current state 收集 base3/+2，不伪造 missing 03B |
| `templates/writing/code_appendix_description.md` | 描述两个工作簿/两个 Python 必然存在 | 按 Gate 条件写作 |
| `README.md` | 历史章节大量 five-file provenance | 只改 current v9.2.x active guidance；历史 release 记录不机械重写 |
| `scripts/README.md` | “五文件合同”概称 | 改成 conditional per-question contract |

### 5.6 Tests

重点复核：

- `tests/test_p7_conditional_analysis_appendix.py`
- `tests/test_repository_hygiene.py`
- `tests/test_schemas.py`
- `tests/test_v700_two_stage_question_folder.py`
- `tests/test_v700_two_stage_execution.py`
- `tests/test_v715_scientific_figure_elevation.py`
- `tests/test_v830_editable_mechanism_diagram.py`
- `tests/test_v910_publication_rendering.py`
- `tests/test_tooling.py`
- 任何读取 `q1_plot.m` / fixed-five 文本 / result-analysis workbook existence 的测试

目标不是按文件名“版本太老”删除测试，而是让历史能力回归仍验证 current semantics。

### 5.7 Maintenance evidence / release docs

- `docs/skill_optimization_status.md`：补 P9 merged/released 最终状态；
- `CHANGELOG.md`：仅在实际 9.2.1 实施完成时新增 patch release；
- `docs/p9_release_closeout.md`：历史 PR 证据默认保留；若需补 final merged note，必须以追加方式记录，不改写当时事实；
- 本计划：实施完成后更新状态，但不把它升级为 Authority。

---

## 6. 建议实施拆分

为避免一个 PR 同时改 Authority、模板、文档、validator、release carrier，建议使用 **3 个实现 PR + 1 个 release closeout PR**。实际开始前必须确认没有重叠 PR，并从最新 main 建分支。

### PR A：P7 Runtime Truth Closure

**主题：** 修复会改变真实执行行为的核心残留。

候选修改：

- `core/user_execution_contract.yaml`
- `templates/matlab/q1_plot.m`
- 必要的最小专项测试
- `core/output_contract.yaml` duplicate key（若可与同一 contract patch 安全合并）

必须证明：

1. Gate=`required` 路径行为不退化；
2. Gate=`not_required` 无 03B 文件时 Figure template 不误失败；
3. 如果实例 Figure 声明读取 03B evidence，缺 03B 仍 fail closed；
4. User Execution 不重新定义 Gate 判据，只消费 activation result；
5. 旧五文件项目继续兼容。

### PR B：Active Consumer Surface Alignment

**主题：** 把所有活动说明/Pack/template guidance 从 fixed-five 收敛到 Output Contract。

候选修改：

- `AGENTS.md`
- `PROJECT_INSTRUCTIONS.md`
- `RUNTIME_ROUTER.md`
- `packs/artifact/code.md`
- `packs/artifact/figure.md`
- `packs/artifact/review.md`
- `packs/artifact/full_submission.md`
- `templates/code/starter/README.md`
- `templates/code/hsk_pipeline/README.md`
- `templates/matlab/README.md`
- `templates/writing/code_appendix_description.md`
- `modules/06_review_delivery.md`（如仅需术语改写）
- 其它搜索确认的 active consumer

原则：

- 不复制 Output Contract 完整列表；
- 用引用 + 最小摘要替代平行 Authority；
- 不改历史 changelog/release provenance；
- 不删除 compatibility pointers。

### PR C：Regression & Lint Debt Closure

**主题：** 让测试/lint 直接验证 current semantics，不再靠 obsolete-error suppress。

候选修改：

- `scripts/lint_skill_checks.py`
- `scripts/lint_skill.py`
- repository hygiene / P7 / MATLAB / submission 等相关 tests

要求：

1. 先新增/改写更强的 3+2 条件断言；
2. 再删除 obsolete fixed-five 断言/过滤；
3. 不减少检查数量或错误覆盖；
4. 不拆 validator；
5. 保持 module-aware `read_text` host adapter 行为；
6. 所有失败必须根据真实 job log 修复，禁止加宽 exemption。

### PR D：v9.2.1 Release Closeout

只有 A/B/C 全部合并并在最新 main 上完整通过后才建立。

职责：

- bump 真实 release carriers 9.2.0 → 9.2.1；
- `CHANGELOG.md` 记录该 patch 只修复条件式 03B 一致性；
- `docs/skill_optimization_status.md` 补 P9 与 post-release patch 状态；
- 更新 P9/release regression；
- generator 管理的 Index / MANIFEST 正常刷新；
- 完整 CI + Optimization baseline final-head 验收。

**禁止**在 PR A/B/C 提前混入 release bump，以免中间 main 出现“版本已宣称修复但 consumer 未闭合”。

---

## 7. 必须新增/强化的行为测试矩阵

### 7.1 Scenario A：Gate required

状态：

```text
primary accepted
result_analysis_status = passed
analysis_execution_status = accepted
03B code/workbook exist and current
```

预期：

- `validated_results` 成立；
- Figure 可消费主 + 03B workbook；
- qX_plot 实例若使用 03B evidence，要求 workbook 存在；
- reproducibility package 包含当前存在的 03B 文件；
- Review 不报 layout 缺失。

### 7.2 Scenario B：Gate not_required

状态：

```text
primary accepted
result_analysis_status = not_required
result_analysis_requirement_reason != ""
analysis_execution_status may remain pending/not activated
03B code/workbook absent
```

预期：

- `validated_results` 成立；
- 不产生 accepted_result_analysis_workbook；
- qX_plot 可以只使用主工作簿；
- Figure / Writing / Review / Submission 不因 03B 缺失失败；
- 不允许新增“鲁棒性通过/稳定性验证” claim；
- reproducibility package 不伪造 03B 文件。

### 7.3 Scenario C：not_required without reason

预期：fail closed。

- 不产生 `validated_results`；
- formal sync 阻断；
- Review/Submission 不得绕过。

### 7.4 Scenario D：Figure 明确声明 03B source，但文件缺失

即使项目其它地方为 current，也必须 fail closed；不能静默换成主 workbook。

### 7.5 Scenario E：legacy five-file project

已有 03B code/workbook 的历史项目继续读取；不得因 9.2.1 把其强制删除或改成三文件。

### 7.6 Scenario F：fixed-five wording hygiene

对 active runtime/consumer surfaces 建立精确检查：

- 禁止“所有新项目默认/必须五文件”式绝对表述；
- 允许历史 Changelog、legacy、明确 provenance 语境出现“five-file”；
- 允许“Gate=required 时 total five files”式条件表达。

不得用简单全仓禁词实现。

### 7.7 Scenario G：release consistency

仅 PR D：

- Bootstrap/plugin/root+packaged SKILL/current Changelog/current README/current release carriers = 9.2.1；
- subordinate schema/version lineage 不机械 bump；
- root 与 packaged `SKILL.md` 保持一致；
- generated indexes/MANIFEST current。

---

## 8. MATLAB 专项修复设计约束

本节只定义验收，不预写最终代码。

### 8.1 Generic template source selection

候选原则：

```text
solutionBook: required
resultAnalysisBook: optional existence at generic template level
sourceBook: selected by instantiated Figure Contract / actual evidence need
```

### 8.2 禁止的实现

- `if ~isfile(resultAnalysisBook), sourceBook = solutionBook; end` 这种无语义 fallback；
- catch 掉 03B sheet/header 缺失；
- 把 `not_required` 写死在 MATLAB 文件而不读当前实例证据；
- 用占位空 workbook 满足模板；
- 在 MATLAB 内重新做结果深化分析。

### 8.3 必须保留

- exact unique header matching；
- 真实工作表存在检查；
- Figure Contract / Evidence Structure 驱动；
- publication profile/style 现有行为；
- title/sgtitle formal prohibition；
- standalone fallback 仅针对 style helper，不改变 evidence source semantics。

---

## 9. Lint / Test 迁移策略

### 9.1 先增后删

任何 obsolete assertion/filter 的删除必须满足：

1. current semantic replacement test 已存在；
2. replacement test 在故意构造错误 contract 时确实失败；
3. current main 正确 contract 时通过；
4. full suite 通过；
5. lint error coverage 没有减少。

### 9.2 `_P7_OBSOLETE_CONTRACT_ERRORS`

该集合只能在 `lint_skill_checks.py` 已不再生成对应 obsolete errors 后缩减/删除。

不得直接删除 wrapper 来“简化代码”，也不得在原错误列表上继续添加更多 suppress。

### 9.3 P7 专项回归扩展

当前 P7 测试应扩展到：

- User Execution activation；
- qX_plot optional 03B semantics；
- active packs/docs no fixed-five contradiction；
- reproducibility current-file behavior；
- validator no obsolete fixed-five requirement。

---

## 10. 版本与 release carrier 策略

### 10.1 为什么候选为 9.2.1

本轮不是新增 P7 能力，而是修复 v9.2.0 已发布能力的实现与 consumer 一致性，符合 patch 定义。

### 10.2 何时不能发布 9.2.1

出现以下任一情况应停止并重新裁决：

- 需要修改 Project State Schema 的 breaking field semantics；
- 需要改变 `not_required` 的业务判据；
- 需要删除旧五文件项目 reader；
- 需要改变公共 CLI/目录；
- 需要把 03B 从 conditional 改回 mandatory；
- 发现当前 Authority 无法判定“Gate 由谁拥有”。

### 10.3 不机械同步的版本

以下 subordinate lineage 默认不因 Skill patch bump：

- Workbook schema version；
- RUN_RECEIPT protocol version；
- User Execution contract 自身 schema/version（除非其版本政策要求 patch）；
- competition profile lineage；
- compile profile lineage；
- historical plan/release 文档中的当时版本。

---

## 11. 残余/无用文件处理政策

本轮审计未发现应立即删除的 `.bak/.orig/.tmp/.swp/.DS_Store/__pycache__` 类明显仓库垃圾。

以下对象**不是无用文件**：

- `HSK_*_V622.md`：明确 compatibility pointer；
- `legacy/**`：历史迁移/provenance；
- `docs/p3*`–`docs/p9*`：实施证据/决策记录；
- `docs/main-branch-protection-hardening-plan.md`：明确 historical pointer；
- `docs/matlab_publication_rendering_v91_plan.md`：虽为 planning_only，但带 `runtime_authority:false` 的历史规划证据。

若未来要做 archive cleanup，应另立独立计划并满足：

1. repository-reference graph 证明无 active consumer；
2. provenance/compatibility 价值已评估；
3. generated index/manifest/links 可闭合；
4. 不与本 v9.2.1 patch 混合。

---

## 12. 验收门禁

### 每个实现 PR

至少：

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests
python scripts/generate_indexes.py --check
```

并运行影响面专项测试。

### PR A

额外要求：

- P7 `required/not_required` runtime tests；
- MATLAB template static contract；
- 若 CI 支持真实 MATLAB preview，则加入 `not_required` representative fixture；若当前真实 MATLAB workflow 只覆盖 rendering API，则不得伪称行为已由真实 MATLAB 证明，需保留静态 + integration evidence 边界。

### PR B

额外要求：

- active reference/link health；
- no contradictory fixed-five active guidance；
- history/legacy allow boundary 精确测试。

### PR C

额外要求：

- validator negative fixtures；
- old suppress 已无必要的证明；
- Static contract lint error set 不因迁移被弱化。

### PR D

最终必须：

- HSK Skill CI 全部 jobs success；
- Optimization baseline evidence success；
- Generated file contract success；
- Python 3.10–3.14 matrix success；
- CUMCM / MCM-ICM / Diangong LaTeX smoke success；
- Production LaTeX attestation success；
- version consistency regression success；
- generated bot 若刷新 metadata，最终验证必须落在 generated final head；不得跳过 action_required 或降低门禁。

---

## 13. 实施时的停止条件

遇到以下任一情况，停止写入并通知用户：

1. `not_required` 的业务定义在 current Authorities 间出现无法自动裁决的差异；
2. 修 q1_plot 需要新增新的 Project State 字段或新的 Figure Authority；
3. 修复要求改变 Workbook Schema 物理结构；
4. 发现 03B 必选/可选关系与用户此前批准 P7 意图相冲突；
5. 需要破坏旧项目兼容；
6. 出现与本范围重叠的开放 PR；
7. CI 暴露与 P7 无关但需要业务决策的失败；
8. 预计修改范围扩展到无关模型、数值、写作或 competition semantics。

普通明确代码错误、旧断言、文档残留、generated metadata refresh 不属于业务裁决，可按治理规则修复并完整重跑。

---

## 14. 完成定义（Definition of Done）

只有以下全部满足，才能宣布 v9.2.1 条件式分析卫生修复完成：

- [ ] User Execution analysis activation 明确受 Analysis Necessity Gate 控制；
- [ ] Output/Router/Manifest/State/User Execution 不再存在 fixed-five vs conditional-three-five 冲突；
- [ ] Gate=`not_required` 且无 03B workbook 的合法项目可以进入 Figure Evidence；
- [ ] qX_plot 在真实需要 03B evidence 时仍 fail closed；
- [ ] Active Agent/Project/Runtime/Pack/Template guidance 不再声称所有新项目固定五文件；
- [ ] Review/Submission 不会要求 `not_required` 项目伪造 03B 文件；
- [ ] 旧五文件项目继续兼容；
- [ ] P7 tests 覆盖 required/not_required/invalid-reason/figure-source 四类关键行为；
- [ ] fixed-five 旧断言已被等价或更强的 conditional invariants 替换，而不是简单删除；
- [ ] `lint_skill.py` 不再需要为 current P7 语义过滤底层 obsolete fixed-five errors；
- [ ] Output Contract duplicate key 清理完成且语义不变；
- [ ] P9 优化状态记录与 merged/released 事实一致；
- [ ] 若实际行为修复成立，release carriers 一致升级到 9.2.1；
- [ ] generated indexes / MANIFEST current；
- [ ] final generated head 上 HSK Skill CI + Optimization baseline 全绿；
- [ ] 无 unresolved review thread；
- [ ] 无范围外语义变更。

---

## 15. 后续执行顺序

用户明确要求开始实施后，每个 PR 都必须重新从最新 `main` 执行：

```text
read core/bootstrap.yaml
→ read SKILL_CHANGE_GOVERNANCE.md
→ confirm current version / main SHA
→ inspect open overlapping PRs
→ read current-stage Authorities
→ confirm this plan still matches repository facts
→ create one dedicated branch
→ implement only that PR's scope
→ run local/static/full tests
→ inspect generated metadata
→ open PR / update evidence
→ final-head CI
→ merge with expected head SHA
→ reread latest main before next PR
```

本计划本身**不授权自动实施**。若未来仓库事实已经变化，以最新 main Authority 和用户最新批准范围为准；本文件作为修改参考与审计 checklist 使用，不得凌驾于 current Authority。
