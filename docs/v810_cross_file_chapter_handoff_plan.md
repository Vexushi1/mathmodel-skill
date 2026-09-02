# v8.1.0 Cross-File Chapter Handoff 修改计划

> 状态：**APPROVED / IMPLEMENTATION AUTHORIZED**  
> 当前 Skill：`8.0.3`  
> 计划目标版本：`8.1.0`（候选，原因见“版本策略”）  
> 计划基线：`main@9c28c17d4ce1f2c7b896c1aca5450c709f0ffc4e`  
> 计划分支：`docs/v810-cross-file-chapter-handoff-plan`  
> 用户已于 2026-09-02 明确批准完整计划；本文件记录已批准实施边界。计划 PR 本身仍只承载上下文，不在本分支实施 Runtime Authority、写作行为、项目 Schema、模板输出或版本载体修改。

---

## 1. 背景与问题定义

当前 CUMCM LaTeX 写作采用 Template-First + progressive authoring。一级章节通常分别写入独立 `.tex` 文件，再由 `hsk_main.tex` 通过 `\input{...}` 装配成全文。

现有 Skill 已经较强地保证：

- 单个问题章节内部 `MODEL → SOLVE → RESULT → VALIDATE` 的功能闭环；
- `Local Narrative Chain`：`previous_output → current_gap → current_operation → current_output → next_use`；
- `Paragraph Handoff Test`：相邻主要段落必须有真实数学承接或局部闭合；
- `Result → Validation Bridge`；
- `cross_question_progression`：后问只继承真实结构并写增量；
- Terminology / Numeric / Formula / Model-Solver-Validator 等跨正文一致性；
- `draft_semantic_review` 与最终全文 review。

但当前还缺一个**显式的“物理 LaTeX 文件边界”连续性契约**。因此理论上可能出现：每个 `.tex` 单独看都正确，但装配后在相邻章节交界处存在以下问题：

1. 上一章产生的数学对象、结果或开放问题，在下一章没有正确继承；
2. 下一章无解释改变符号、单位、canonical term 或模型称谓；
3. Q2/Q3 实际依赖前问，却以“针对问题二，建立新模型”重新开始，丢失真实继承；
4. 为了连贯反而机械加入“下面进行”“接下来”等无信息过渡句；
5. 上一章已完成的分析、假设或共享关系在下一章被重复抄写；
6. 条件章节（数据说明 / 模型准备）开关变化后，原本设计的章节承接对象不再是实际相邻文件；
7. 摘要虽然最后写，但在成品中位于第一章之前，若只按“写作顺序”判断 handoff，会得到错误 seam；
8. 单问/多问、简单题/复杂题、无共享基础/有共享基础情况下，需要检查的 seam 类型不同，不能统一强迫正文桥接。

本计划拟新增 **Cross-File Chapter Handoff**：在不改变现有数学建模主流程、不新增第二套写作 Authority 的前提下，把“章节文件交界处是否连续”从隐式要求提升为显式、可恢复、可审查的写作能力。

---

## 2. 直接目标

新增一个向后兼容的 Cross-File Chapter Handoff 能力，使每个活动 `.tex` 章节在最终装配顺序中都能回答：

```text
上一文件关闭了什么
→ 哪些对象/结论/约束继续有效
→ 当前文件为什么在这里出现
→ 是否存在仍待解决的 gap
→ 当前文件应从什么对象/任务进入
→ 当前文件结束后向下一活动文件交接什么
```

但这些是**内部写作/审查状态**，不得直接打印成论文中的固定模板句。

最终目标不是增加连接词，而是保证：

```text
多个独立 .tex 文件
        ↓
装配后的整篇论文
        ↓
仍表现为一条连续数学论证链，而不是若干独立回答的拼接
```

---

## 3. 明确不做

本修改不得顺手扩展为全文写作重构。明确禁止：

- 不改变 Problem Contract、Model Challenge、Human Model Approval；
- 不改变 `semantic_revision/hash`、Model Approval stale 语义；
- 不改变数据审计 / `preprocessing_decision`；
- 不改变 03A Primary Quality、03B Result Analysis 边界；
- 不改变用户 full-fidelity 执行所有权；
- 不改变 Workbook Schema、数值事实源、MATLAB Figure Evidence；
- 不改变 CUMCM 固定一级章节骨架；
- 不重排 Q1/Q2/Q3；
- 不把每个章节改成一个新的模型模块；
- 不新建独立 `cross_file_handoff_contract.yaml`，除非实施阶段证明现有 Authority 无法承载；默认禁止新增第二套 Authority；
- 不把 handoff 写成固定连接词库；
- 不要求每个 `.tex` 边界都出现正文过渡段；
- 不将 handoff 状态加入模型语义哈希；
- 不因纯写作 handoff 更新触发 Model Approval / primary solve stale；
- 不让旧项目因缺少 handoff 字段而不可读取；
- 不创建新的正式提交文件或新的论文可见附录。

---

## 4. 权威事实源与职责分配

遵循单一事实源原则，不新建平行写作体系。

### 4.1 `modules/05_writing/paper_writing_protocol.md`

拟作为 **Cross-File Chapter Handoff 的普通正文语义 Authority**。

新增一节，建议位于 Local Narrative Chain / Paragraph Handoff Test 之后，负责定义：

- 什么是跨文件 seam；
- seam continuity 的信息功能；
- 何时需要正文桥接、何时只需一致性检查；
- 不允许使用固定连接词代替真实逻辑；
- 与 `cross_question_progression`、共享基础、Result→Validation 的关系。

它不保存项目实际 handoff 内容。

### 4.2 `core/writing_runtime_contract.yaml`

拟负责 **读取时机、写入时机和 gate**，不重新定义 prose 规则。

主要增加：

- final assembled order 与 authoring order 分离；
- 每次写当前文件前读取 relevant previous/next seam context；
- 写完后更新 handoff record；
- 当前 stage gate 附带 seam gate；
- `draft_semantic_review` 对 assembled document 执行全局 seam review。

### 4.3 `templates/model/model_paper_framework.md`

拟增加一个**项目实际状态容器**，暂定名：

```text
### Chapter Handoff Map
```

它只保存本项目各活动 `.tex` 的真实交接信息，不复制通用规则。

该部分属于写作项目记忆，不属于模型语义哈希区。

### 4.4 `templates/latex/cumcm/hsk/template_manifest.yaml`

只提供结构事实：

- active / conditional slot；
- final assembled order；
- 目标 physical source file。

若现有 manifest 信息已足够解析实际顺序，则不新增字段；只有实施测试证明不能可靠恢复真实 active adjacency 时，才增加最小结构字段。

禁止让 Manifest 定义 prose handoff 语义。

### 4.5 `core/writing_reasoning_contract.yaml`

默认**不新增另一套完整规则**。

只在需要时增加最小 delegate / capability pointer，使复杂语义终审能够识别 Cross-File Chapter Handoff 由 Paper Writing Protocol 管理，并继续复用：

- `cross_question_progression`；
- Terminology Registry；
- Numeric Profile；
- Formula Trace；
- Claim Strength；
- Paper Fragment Dependency Map。

若 Protocol 已能完整消费上述能力，则这里可不改。

### 4.6 `modules/06_review_delivery.md`

作为 consumer 增加全文 seam 检查项，不复制 Authority。

---

## 5. 核心设计：区分两种顺序

这是本修改的关键约束。

### 5.1 Authoring Order

当前普通写作实际顺序大致为：

```text
问题重述
→ 问题分析
→ 假设/符号/条件式准备
→ Q1 → Q2 → ...
→ 评价/引用/附录
→ 最后写摘要/标题/关键词
```

这是生成顺序。

### 5.2 Final Reading / Assembly Order

最终 `hsk_main.tex` 装配顺序是：

```text
摘要
→ 问题重述
→ 问题分析
→ 假设
→ 符号
→ [数据说明]
→ [模型准备]
→ Q1 → Q2 → ...
→ 模型评价
→ 参考文献
→ 附录
```

Cross-File seam 必须以**最终实际活动文件顺序**为主，而不能把“摘要最后写”误认为“摘要位于正文末尾”。

因此计划中 handoff 必须有两个概念：

```text
authoring_predecessor
assembled_predecessor
```

真正的正文 seam gate 使用 `assembled_predecessor / assembled_successor`。

---

## 6. Seam 分类：禁止“一刀切过渡句”

拟定义至少四种 seam profile。

### 6.1 `narrative`

适用示例：

- 问题重述 → 问题分析；
- 问题分析 → 模型准备（若存在真实共享结构）；
- 模型准备 → Q1；
- Q1 → Q2；
- Q2 → Q3；
- 最后一问 → 模型评价。

检查重点：数学对象、真实依赖、当前 gap、结构增量、结论延续。

正文桥接：**按需**。只有缺少桥接会造成对象/任务跳跃时才需要。

### 6.2 `registry_or_definition`

适用示例：

- 假设 → 符号说明；
- 符号 → 数据/模型准备。

检查重点：符号、单位、术语、假设作用域一致。

正文桥接通常不需要；禁止为了 seam gate 生成“基于上述假设，下面给出符号说明”。

### 6.3 `frontmatter_consistency`

适用：

- 摘要 → 问题重述。

摘要虽然最后生成，但最终阅读时位于最前。

检查重点：摘要中的对象、模型名称、结果、验证边界、关键词与正文一致；不要求摘要末句显式引出“问题重述”。

### 6.4 `structural_terminal`

适用：

- 模型评价 → 参考文献；
- 参考文献 → 附录。

主要检查结构合法性、引用/附录边界，不制造语义过渡句。

必要时可进一步把 Qn→Qn+1 标为 `cross_question_increment` 子型，但不新建第二套 cross-question 规则，继续消费现有 `cross_question_progression`。

---

## 7. Chapter Handoff Map 候选数据结构

拟在 `模型论文框架.md` 中新增非模型语义区：

```markdown
### Chapter Handoff Map

| Seam ID | Profile | Source File | Target File | Source Closure | Carry Forward | Open Gap / Entry Reason | Consistency Anchors | Bridge Need | Status |
|---|---|---|---|---|---|---|---|---|---|
| seam.q1_q2 | cross_question_increment | ... | ... | ... | ... | ... | ... | required / not_needed | current / stale / not_applicable |
```

### 7.1 字段语义

`Seam ID`
- 稳定标识实际相邻活动文件的交界；
- 示例：`seam.problem_analysis_assumptions`、`seam.q1_q2`。

`Profile`
- 使用上节 seam profile；
- 只决定检查重点，不决定固定句式。

`Source File / Target File`
- 必须指向最终 assembly 中实际相邻的 active `.tex`；
- 条件章节关闭后必须重新解析邻接关系。

`Source Closure`
- 上一章节已经闭合的任务/结论；
- 不复制整章摘要，只保留影响下一文件的内容。

`Carry Forward`
- 下一章节仍有效并需要消费的对象，例如共享状态、已确定参数、判据、前问结果、术语或符号。

`Open Gap / Entry Reason`
- 当前文件之所以出现的数学/写作理由；
- 如果没有需要填补的 gap，可记录结构性 entry reason。

`Consistency Anchors`
- 可记录 Term ID / Formula ID / Result ID / Claim ID / Paper Fragment ID 等已有锚点；
- 不发明新的模型锚点系统。

`Bridge Need`
- `required / optional / not_needed`；
- `required` 只表示需要真实语义桥，不表示必须单独写“过渡段”。

`Status`
- `current / stale / not_applicable`；
- 只属于写作状态。

---

## 8. 六类 Cross-File Seam Gate

实现后每个 relevant seam 至少按以下六项审查。

### 8.1 `object_continuity`

检查数学对象、研究对象、状态空间、时间/空间范围是否无说明突然改变。

### 8.2 `symbol_term_continuity`

检查：

- 同一量是否突然换符号；
- 相同符号是否换含义；
- 单位是否漂移；
- canonical term 是否在新章节被 AI 同义词替换。

### 8.3 `dependency_continuity`

若下一章真实依赖上一章结果/共享关系：

- 是否明确继承；
- 是否消费正确 current result；
- 是否遗漏 dependency；
- 是否把已 stale 前问结果继续当 current。

### 8.4 `claim_continuity`

检查上一章已闭合的结论/边界是否在下一章：

- 被正确沿用；
- 没有无证据升级；
- 没有遗忘验证边界；
- 没有与摘要/评价冲突。

### 8.5 `duplication_control`

检查下一文件是否无必要重新复制：

- 问题分析；
- 假设；
- 共享基础；
- 前问完整模型；
- 已解释公式。

允许必要 recap，但必须服务当前新任务。

### 8.6 `transition_necessity`

判断该 seam 是否真正需要正文桥接。

规则：

```text
需要桥接时没有桥接 → review_required
不需要桥接时强行加入管理型过渡句 → cleanup/review risk
```

不得把“因此、下面、接下来、进一步”等词出现与否作为 machine correctness 判断。

---

## 9. Runtime 行为计划

### 9.1 Template Inspection

在现有 `template_inspection` 后解析：

```text
active final assembly sequence
→ actual adjacent source-file pairs
→ seam profiles
```

条件章节关闭时只对实际相邻文件建立 seam。

例如：

```text
04_symbols.tex
05_data.tex [inactive]
05_model_preparation.tex [inactive]
06_question1.tex
```

实际 seam 是：

```text
04_symbols.tex → 06_question1.tex
```

而不是生成两个不存在的中间 seam。

### 9.2 写当前章节前

除第一个实际 frontmatter/body slot 外，读取：

```text
current project facts
+ current target section rule
+ relevant assembled predecessor handoff
+ relevant cross-question/shared dependency
```

不要求加载 predecessor 的全文；默认优先消费 Handoff Map + necessary paper fragment / project fact anchors。

当 handoff 信息不足或冲突时，允许定点回读 source `.tex` 尾部和 target `.tex` 当前开头，而不是预载整篇论文。

### 9.3 写当前章节后

更新：

- 当前文件的 incoming seam status；
- 当前文件对 assembled successor 的 outgoing handoff；
- 相关 paper fragment anchor；
- 若章节内容变化使 downstream seam 不再成立，则只标记真实依赖的 handoff/paper fragment stale。

### 9.4 摘要特殊处理

摘要在 authoring order 中最后写，但写完后必须检查：

```text
abstract.tex → 01_problem_statement.tex
```

的 final-reading seam，以及摘要与全部问题答案、Title Claim、Numeric Profile、Claim Strength 的一致性。

不得检查：

```text
09_evaluation.tex → abstract.tex
```

因为这不是最终文档阅读顺序。

### 9.5 Draft Semantic Review

新增“assembled seam sweep”：

```text
按照最终 main.tex active order
逐对检查相邻 physical files
```

输出 blocking / review_required / warning 仍服从现有治理等级，不新建第四套等级。

---

## 10. 与现有 Paper Fragment Dependency Map 的关系

Cross-File Handoff 不取代 Paper Fragment Dependency Map。

两者职责：

```text
Paper Fragment Dependency Map
= 某段正文依赖哪些模型/结果/证据，负责局部 stale

Chapter Handoff Map
= 相邻最终章节文件之间要继承/关闭/进入什么，负责 seam continuity
```

计划要求尽量通过现有 Fragment ID 建立联系，例如：

```text
seam.q1_q2
  consistency_anchors:
    - paper.q1.result
    - paper.q2.model.entry
    - Q1.result_summary
```

禁止新建一套重复的正文依赖图。

---

## 11. Stale 与语义哈希边界

这是实施时必须写死的边界。

### 11.1 不触发模型语义 stale 的变化

以下变化属于写作层：

- 桥接句重写；
- chapter handoff record wording；
- source/target prose entry 优化；
- 纯术语统一且未改变数学含义；
- `.tex` 文件边界处的重复删除；
- seam status 更新。

它们不得递增模型 `semantic_revision`，不得使 `locked_model_spec` stale。

### 11.2 上游语义变化导致 handoff stale

若模型/结果/依赖发生真实变化，则已有项目状态机制先传播模型/结果/paper fragment stale；Chapter Handoff 作为下游写作状态随真实依赖变 stale。

例如：Q1 关键结果修改且 Q2 继承该结果：

```text
Q1 result stale/current change
→ relevant paper fragments stale
→ seam.q1_q2 stale
→ Q2 related entry/claim review
```

但无关 Q3、背景、符号章节不得全篇机械 stale。

---

## 12. Review / Audit 设计

### 12.1 人工/语义 review 是主判断

以下项目不能由关键词机器判定：

- 两章是否真的数学连续；
- 是否真正需要桥接；
- Q2 是否应该继承 Q1；
- 当前过渡是否只是管理型话术；
- 省略重复内容后信息是否仍足够。

### 12.2 可机器检查的结构项

计划允许测试/审计检查：

- active source/target file 是否存在；
- final assembly adjacency 是否匹配 `hsk_main.tex` / manifest；
- handoff `status` 是否存在；
- stale fragment 被标 current 的确定性冲突；
- 已声明 `required` seam 是否完全没有 handoff record；
- 非 active conditional file 是否错误出现在 current handoff map；
- root/package/版本/manifest 等现有 invariants。

### 12.3 不计划第一版新增重型审计脚本

优先复用：

- `draft_semantic_review`；
- `modules/06_review_delivery.md`；
- 现有 `audit_v8_writing_surface.py` 的职责边界。

第一版若只需结构测试，不新增 `audit_cross_file_handoff.py`。

只有实施后证明“状态结构需要独立 deterministic validator”时，再另开后续单主题 PR，不塞进本次能力 PR。

---

## 13. 拟修改文件

审批后预计检查/修改：

### 核心修改

1. `modules/05_writing/paper_writing_protocol.md`
   - 新增 Cross-File Chapter Handoff 语义规范；
   - 明确 seam profile / six checks / no phrase bank。

2. `core/writing_runtime_contract.yaml`
   - 增加 final assembly adjacency、incoming/outgoing handoff 读写时机；
   - stage gate 增加 seam continuity；
   - 摘要特殊处理；
   - draft semantic review 增加 assembled seam sweep。

3. `templates/model/model_paper_framework.md`
   - 增加 `Chapter Handoff Map` 项目状态区；
   - 明确非 semantic-hash、非 Model Approval 状态。

4. `modules/06_review_delivery.md`
   - 增加 consumer checklist；
   - 不复制完整 Authority。

### 条件修改

5. `templates/latex/cumcm/hsk/template_manifest.yaml`
   - 仅当现有字段无法可靠恢复 active final order 时，增加最小 assembly-order metadata；
   - 如果现有信息足够，则不改。

6. `core/writing_reasoning_contract.yaml`
   - 仅增加必要 delegate/capability pointer；
   - 不复制 Chapter Handoff 规则。

7. `core/output_contract.yaml` / `core/module_manifest.yaml`
   - 只有现有 artifact declarations 必须识别新 framework section / writing output 时才做最小更新；
   - 不改变文件目录和正式交付文件数量。

### 新增测试

建议新增：

```text
tests/test_v810_cross_file_chapter_handoff.py
```

必要时扩展：

- `tests/test_v800_writing_runtime.py`
- `tests/test_v801_chapter_capability_preservation.py`
- `tests/test_v750_writing_reasoning_architecture.py`
- template manifest / framework validation 相关现有测试。

### Release carriers（若最终确认 minor）

按仓库现行版本一致性测试显式枚举并更新 current release carriers，禁止全仓库盲替换。

包括但不限于实际 current-version Authority/consumer：

- `core/bootstrap.yaml`
- root/package `SKILL.md`
- `.codex-plugin/plugin.json`
- `README.md`
- `CHANGELOG.md`
- Router/Manifest/Output/Writing Runtime 等当前版本载体（以实施前实际测试与 current main 为准）。

### Generated files

由 `scripts/generate_indexes.py` / feature workflow 自动更新：

- `SKILL_FILE_INDEX.md`
- `MANIFEST.sha256`
- 其他明确 generated 文件。

禁止人工修改哈希。

---

## 14. 明确禁止触碰的文件/语义

除非实施前发现当前 main 与本计划基线发生上游变化且必须重新审批，否则不修改：

- `core/model_approval_contract.yaml`
- `core/numerical_verification_contract.yaml`
- `core/workbook_schema.yaml`
- `core/project_state.schema.yaml`
- `core/global_preprocessing_contract.yaml`
- `core/user_execution_contract.yaml`
- `core/code_quality_contract.yaml`
- `modules/02_model_design.md`
- `modules/03_solve_validate.md`
- `modules/03_result_analysis.md`
- `modules/04_figure_evidence.md`
- Python / MATLAB 求解与绘图业务模板
- 赛事题型 taxonomy / model packs

如果实施时发现必须改上述文件之一，应停止当前 PR，说明原因并重新取得用户批准。

---

## 15. 兼容性要求

### 15.1 旧项目

旧 `模型论文框架.md` 没有 `Chapter Handoff Map` 时：

- 必须仍可读取；
- 首次进入新的 writing route 时按 current active LaTeX slots 增量初始化；
- 不要求重新设计/重新求解模型；
- 不自动改写旧正文；
- 不自动提高 Claim Strength；
- 不自动制造章节过渡句。

### 15.2 单文件 LaTeX / 非 CUMCM

Cross-File Handoff 仅在存在实际多文件 assembly 时激活。

- 单文件论文：`not_applicable`，继续使用 Paragraph Handoff / global review；
- DOCX：当前版本不把 physical `.tex` seam 规则硬套到 DOCX；
- MCM/ICM/电工杯：若尚无对应 manifest，保持 full reasoning fallback，不错误使用 CUMCM 文件序列。

### 15.3 简单问题

简单题不因为新增 seam 机制而强制：

- 单独 VALIDATE 小节；
- 核心模型汇总；
- 算法框；
- 人工过渡段。

---

## 16. 版本策略

按照 `SKILL_CHANGE_GOVERNANCE.md`：

- docs：只改说明，不改变执行行为；
- patch：修复错误，保持现有接口；
- minor：新增向后兼容能力、可选字段或工作流。

本计划拟新增：

- Cross-File writing capability；
- runtime seam gate；
- framework 可选写作状态区；
- review consumer。

因此初步判定为：

```text
8.0.3 → 8.1.0
```

即 **minor**。

如果实施前进一步证明：无需新增 framework section / runtime state，只是在现有 Paragraph Handoff 的遗漏处补一个纯 bugfix gate，则可以重新提出 patch 方案，但不得在未说明的情况下自行改成 8.0.4。

---

## 17. 测试矩阵

### 17.1 Authority / structure tests

必须验证：

- Cross-File Chapter Handoff 只有一个普通正文 Authority；
- Runtime 只控制 timing/gate，不复制 prose rules；
- Framework 只保存项目事实；
- Review 只消费，不成为第二 Authority；
- 不新增平行 contract。

### 17.2 Assembly-order tests

至少覆盖：

#### Case A：最简 CUMCM

```text
abstract
→ problem_statement
→ problem_analysis
→ assumptions
→ symbols
→ Q1
→ evaluation
```

数据与模型准备关闭。

#### Case B：有 project-level data

```text
symbols → data → Q1
```

#### Case C：有 shared model preparation

```text
symbols → model_preparation → Q1
```

#### Case D：data + model preparation 同时启用

确保实际 adjacency 正确。

#### Case E：Q1/Q2/Q3

验证：

```text
Q1 → Q2 → Q3
```

只在真实 dependency 存在时要求 inherited structure。

#### Case F：摘要特殊顺序

确保 handoff 检查的是：

```text
abstract → problem_statement
```

而不是 authoring order 的：

```text
evaluation → abstract
```

### 17.3 No-forced-transition tests

必须有负向测试防止：

- 假设→符号自动生成管理型桥句；
- 参考文献前自动生成“下面给出参考文献”；
- 用连接词出现频率判断连贯性；
- simple problem 被强制添加过渡段。

### 17.4 Compatibility tests

- 无 `Chapter Handoff Map` 的旧 framework 可读；
- existing Paper Fragment Dependency Map 保持可用；
- no semantic revision bump from pure handoff update；
- root/package Skill parity；
- legacy pointers 仍隔离。

### 17.5 Protected semantic regression

至少确认以下核心文件没有业务 diff，或对其做 byte/hash compare：

- Model Approval；
- Numerical Verification；
- Workbook Schema；
- Project State；
- 03A；
- 03B；
- Figure Evidence。

### 17.6 全量仓库验收

必须执行：

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/generate_indexes.py --check
```

并通过现有完整 HSK Skill CI：

- Static contract lint
- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13
- Python 3.14
- Generated file contract
- LaTeX CUMCM
- LaTeX MCM-ICM
- LaTeX Diangong
- Production LaTeX attestation

不得为了新能力降低旧测试断言。

---

## 18. 实施顺序

审批后建议一个单主题 implementation PR 完成，因为所有修改均围绕同一 Cross-File writing capability；如最终修改面超过 20 个活动文件则按治理规范重新评估拆分。

### Step 0：重新冻结 main

实施前重新读取：

- `main` SHA；
- `core/bootstrap.yaml`；
- `SKILL_CHANGE_GOVERNANCE.md`；
- open PR；
- writing Authority / runtime / template manifest 当前版本。

若 main 已有重叠写作修改，停止并重建计划基线。

### Step 1：先写测试骨架

先定义：

- Authority separation；
- assembly order；
- no-forced-transition；
- old-framework compatibility；
- no semantic-state expansion。

### Step 2：Protocol 语义

新增 Cross-File Handoff 章节，定义 seam profile、六项 gate、桥接必要性原则。

### Step 3：Framework storage

新增 Chapter Handoff Map，明确 writing-only / non-hash / optional-read compatibility。

### Step 4：Runtime progressive authoring

将 incoming/outgoing handoff 加入每个 relevant stage，区分 authoring order 与 assembly order。

### Step 5：Review consumer

增加 assembled seam sweep 和 stale / continuity 检查。

### Step 6：条件调整 Manifest / delegate

仅按真实必要性最小修改。

### Step 7：版本与 Changelog

如果实现保持本计划能力范围，发布 8.1.0；显式更新 current release carriers。

### Step 8：generated metadata + full CI

只在所有 test/CI 通过后合并。

### Step 9：post-merge health audit

合并后重新检查：

- Skill 能读取；
- root/package parity；
- resolver representative route；
- ordinary CUMCM writing route；
- Model Approval / 03A / 03B 未漂移；
- generated main 仍 check-only；
- Cross-File Handoff 没有成为新的模型状态机。

---

## 19. 风险分析

### 风险 A：规则过度复杂化

如果 handoff 变成新的大型 Schema，会违背刚完成的 active-surface slimming。

**控制：**只在 Protocol + Runtime + Framework 中最小实现，不新建 contract。

### 风险 B：强迫每章写过渡句

可能让论文更像 AI。

**控制：**`Bridge Need` 明确允许 `not_needed`，registry/frontmatter/terminal seam 默认只检查一致性。

### 风险 C：把写作状态混入模型 semantic revision

可能导致只改一句过渡话就要求重新 Model Approval。

**控制：**Chapter Handoff Map 明确位于非语义哈希写作区；纯 handoff 修改不得触发 model stale。

### 风险 D：摘要 authoring order 误导 final seam

**控制：**所有 seam 以 final assembly order 解析；摘要写完后补做前置 seam check。

### 风险 E：条件章节造成错误邻接

**控制：**只对 active slots 计算 adjacency；inactive file 不得出现在 current map。

### 风险 F：与 Paper Fragment Dependency Map 重复

**控制：**Handoff Map 只记录 seam，不再复制 fragment dependency；通过现有 Fragment ID/结果锚点引用。

### 风险 G：跨问连贯被错误理解为强制继承

**控制：**继续服从 `cross_question_progression.activate_when=actual_dependency_exists`；独立问题明确允许 independent seam。

---

## 20. 回滚方案

如果 implementation PR 出现不可接受副作用：

1. 整体 revert 单一实现 PR；
2. 删除新增 Handoff Map section / runtime handoff steps / review consumer；
3. 恢复原 `8.0.3` writing runtime 行为；
4. 不需要回滚任何模型、工作簿、求解结果或 Model Approval；
5. 已有项目中若曾写入 optional Chapter Handoff Map，可被旧版忽略，不影响模型语义。

若已经发布 8.1.0 后回滚，则按仓库 release governance 决定发布修复版本，不通过篡改历史 commit 伪装未发生。

---

## 21. 验收标准

只有同时满足以下条件，才可宣称 Cross-File Chapter Handoff 完成：

1. 每个 actual active CUMCM `.tex` 邻接 seam 可从 final assembly order 恢复；
2. 条件章节开关不会产生虚假 seam；
3. Q1→Q2 等真实依赖能恢复 carry-forward + increment；
4. 独立问题不会被强制虚构依赖；
5. 符号/术语/单位/结果/claim continuity 有明确检查入口；
6. 不需要桥接的 seam 不生成管理型过渡句；
7. 摘要按最终阅读顺序与问题重述形成 consistency seam；
8. Framework 可持久化 handoff 以支持跨聊天/长任务恢复；
9. old framework 无新 section 时仍可读取；
10. handoff wording 修改不影响 model semantic hash / approval；
11. Paper Fragment Dependency Map 不被复制或取代；
12. draft semantic review 对全文 final-order seam 做 sweep；
13. root/package Skill、版本载体、generated metadata 全部同步；
14. 完整 11-job CI 全绿；
15. 合并后独立健康审计未发现 Skill 不可读取、Router/Approval/03A/03B/Writing Authority 漂移。

---

## 22. 审批边界

用户已于 2026-09-02 明确回复“批准完整计划”。因此后续实施可按本文件全部范围执行，无需再次审批；若实施时必须修改第 14 节列出的禁止触碰文件/语义，或扩大为新的独立 Authority / Schema / 正式交付物，则必须停止并重新取得用户批准。
