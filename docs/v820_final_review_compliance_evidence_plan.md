# v8.2.0 Final Review Compliance & Evidence Sweep 修改计划

> 状态：**DRAFT / AWAITING USER APPROVAL**  
> 当前 Skill：`8.1.1`  
> 计划目标版本：`8.2.0`（候选，新增向后兼容的终审能力）  
> 计划基线：`main@d30b861f55e78d7ca8a4e991034a6019f560b5c6`  
> 计划分支：`docs/v820-final-review-compliance-plan`  
> 本计划 PR 只承载实施上下文，不修改终审 Authority、评分器、模板、版本载体或运行时行为。用户批准且计划进入 `main` 后，实施必须从当时最新、干净的 `main` 重新冻结基线并建立独立功能分支。

---

## 目录

1. 背景与输入证据
2. 当前能力与已确认缺口
3. 修改简报
4. Authority 与职责边界
5. 目标终审流程
6. Final Review Matrix 设计
7. 分级与规则来源
8. 自动检查与人工检查边界
9. 逐文件实施方案
10. 版本、兼容与迁移
11. 明确不做
12. 受保护语义冻结
13. 实施顺序
14. 测试矩阵
15. 验收标准
16. 风险与抑制措施
17. 回滚与后续扩展

---

## 1. 背景与输入证据

本计划来自对外部《数学建模论文自查表.xlsx》的只读审计。该工作簿包含：

- 1 个工作表；
- `A1:G291` 的使用范围；
- 287 个原子检查项；
- 25 个固定或动态检查分组；
- “编号、板块、原子检查点、状态、页码/原文证据、扣分、修改建议”7 列；
- 面向摘要、页面结构、标题、模型、问题重述、问题分析、假设、符号、求解验证、模型评价、字体、图、表、公式、页面视觉、匿名、AI 使用、参考文献、附录及动态逐问检查的覆盖。

该工作簿的主要价值不是新增建模方法，而是把终稿容易遗漏的交付风险显式列出，特别是：

1. 匿名性与身份信息泄露；
2. PDF/文件元数据与隐藏批注、修订记录；
3. AI 使用声明及支撑材料的一致性；
4. 文献实体、DOI/URL、访问日期与正文引用关系；
5. 图表重复表达、孤行、标题悬空、裁切、溢出和跨页缺陷；
6. 逐问、逐模型、逐跨问题依赖的动态检查；
7. 每个问题保留证据位置和修改动作。

但该工作簿本身不能直接成为 Skill Authority，原因包括：

- 把一般问题统一扣 1 分、严重问题扣 2 分，会压平 Hard / Default / Recommendation 的治理差异；
- 声称“资格风险另行标记”，实际没有资格风险专列；
- 状态与扣分没有公式联动，也没有总分和分组汇总；
- “关键词 4--5 个”“正文 30 页”“主体 22--25 页”“每页三级标题不超过 2 个”等包含赛事特定规则或经验阈值；
- 摘要禁止一切行内符号、希腊字母和关系式等规则过于绝对；
- 动态检查预置 5 问、6 个优化模型、8 组图表和 6 个跨问联动，不能替代按实际论文结构生成检查范围；
- “满足 / 不满足 / 部分满足”的条件格式存在子串重叠，不应充当机器判定；
- 21 页长表不适合直接进入运行时上下文。

因此实施原则是：**吸收检查能力，不复制工作簿；吸收证据结构，不继承扣分逻辑；消费已核验赛事规则，不把经验阈值升级为通用 Hard。**

外部工作簿不进入仓库，不进入正式提交包，也不成为后续运行时依赖。

---

## 2. 当前能力与已确认缺口

### 2.1 当前已经具备的能力

当前 `modules/06_review_delivery.md` 已经覆盖：

- `draft_semantic_review` 与 `final_review_and_delivery` 两个审查时点；
- `blocking / review_required / warning` 三层治理；
- 题意覆盖、附件使用、输出格式和数值精度；
- Model / Solver / Validator、Formula Trace、Algorithm Trace；
- 命题、证明、Claim Strength、Title Claim、Terminology、Numeric Style；
- Cross-File Assembled Seam Sweep；
- 摘要逐问、问题重述、问题分析、假设、符号、模型建立与求解、结果验证；
- 图表、工作簿、MATLAB、正文和结论的证据映射；
- Citation Evidence 与 BibTeX key 结构检查；
- LaTeX audit、compile report、PDF、提交包与复现材料；
- Hard Fail 不能被加权总分抵消。

当前 `scripts/audit_paper_prose.py` 已经能够确定性检查：

- 重复/缺失 label 和 citation key；
- 未使用 BibTeX 条目与 `\\nocite{*}` 风险；
- 摘要中的图表或展示公式；
- 默认关键词数量；
- 图题/表题位置；
- 部分结构、术语、数值、强主张和章节颗粒度风险。

当前 `scripts/audit_latex_project.py` 已经统一执行 LaTeX include graph、prose、BibTeX、framework 和 source-bundle 审计，并生成正式 `latex_audit_report.yaml`。

当前 `scripts/score_submission.py` 已经：

- 按六个权重维度评分；
- 验证维度齐全、分数范围和 Hard Fail code；
- 将 `hard_fail` 与加权总分分离；
- 原样携带 report-level `evidence`。

当前 `config/competition_profiles.yaml` 已经为每个赛事预留：

```text
edition
verification_status
verified_at
source
page_limit
anonymity
submission_files
ai_disclosure
```

并明确规定：未达到 `verified` 时，不得把默认值表述为当届官方要求。

### 2.2 已确认的真实缺口

现有能力强在数学、证据、写作与编译闭环，但 Final Review 仍缺少以下明确的消费与报告协议：

1. **Edition Rule Consumption Gap**  
   配置已经有页数、匿名和 AI 披露字段，但 Final Review 没有逐项说明如何消费、无法核验时如何分级、违反已核验规则时如何进入 Hard Fail。

2. **Anonymity & Metadata Gap**  
   “PDF 逐页检查”没有显式覆盖 PDF 作者/公司/标题元数据、图中姓名、代码截图路径、账户名、隐藏批注和修订记录。

3. **AI Disclosure Consistency Gap**  
   缺少“当届规则—正文声明—独立支撑材料—真实使用事实”四者一致性检查。当前配置字段存在，但没有终审落点。

4. **Citation Entity Integrity Gap**  
   现有机器审计能证明 key 结构闭合，不能证明作者、题名、年份、期刊、DOI、URL、访问日期相互匹配，也不能证明来源真正支持对应 claim。

5. **Rendered Surface Gap**  
   当前要求逐页看 PDF，但没有统一记录孤行、标题悬空、对象裁切、横向溢出、跨页表头、大面积无意义空白和打印可辨识性。

6. **Figure/Table Redundancy Gap**  
   当前审查重视邻近解释和证据闭环，但没有显式要求核对图与表是否重复承担同一信息任务。

7. **Atomic Review Evidence Gap**  
   当前评分器只携带 report-level evidence，没有通用的“检查范围—规则来源—验证方式—证据定位—严重级—状态—修改动作”结构。评分结果可能正确，但难以证明每个高风险面都实际检查过。

---

## 3. 修改简报

```text
修改主题：Final Review Compliance & Evidence Sweep
当前版本：8.1.1
目标版本：8.2.0
变更等级：minor
直接目标：让最终审查显式消费已核验赛事规则，并形成可追溯、不可被总分掩盖的原子证据报告
明确不做：不复制 287 条清单；不修改 AI Cleanup；不新增 PDF 解析依赖；不新增 Project State 字段；不新增 pre-delivery gate；不改变模型/数值/写作 Authority
权威事实源：modules/06_review_delivery.md；config/competition_profiles.yaml；core/writing_reasoning_contract.yaml；现有 compile/submission attestation
预计修改文件：Review Authority、Review Pack、可选 review matrix 模板、评分器、评分配置、测试、最小 lint、版本载体、生成索引
禁止触碰文件：模型审批、数值验证、工作簿、项目状态、03A、03B、Figure Evidence、Template Manifest、Paper Writing Protocol、AI Cleanup、现有 LaTeX 审计与编译实现
兼容性要求：旧评分报告和旧项目继续可读；新字段为向后兼容增量；现有六维权重不变；official package allowlist 不变
迁移要求：无强制迁移；新生成的正式终审报告使用 v1 matrix；旧报告仅作为兼容输入
验收测试：评分兼容、矩阵结构、Hard Fail 映射、规则核验边界、无自动扣分、无提交包泄漏、Authority 防重复、版本同步、全量 CI
回滚方式：整体回滚单一 v8.2.0 功能 PR；旧项目、模型、工作簿、PDF 和提交包无需迁移
```

---

## 4. Authority 与职责边界

本修改必须保持单一事实源，不新增平行终审规则体系。

| 职责 | Authority / Consumer | v8.2.0 边界 |
|---|---|---|
| 当届页数、匿名、文件命名、附件、AI 披露 | `config/competition_profiles.yaml` + 当前 competition Pack | 继续作为赛事规则唯一来源；Review 只消费，不复制固定值 |
| 正文写作与跨章节表达 | `modules/05_writing/paper_writing_protocol.md` | 不修改；Final Review 只引用 |
| 数学、证据、Claim、Citation 语义 | `core/writing_reasoning_contract.yaml` | 不修改；Final Review 继续回退到该 Authority |
| 最终审查语义与分级 | `modules/06_review_delivery.md` | 新增 Final Review Compliance & Evidence Sweep 的唯一语义定义 |
| 用户可读审查报告适配 | `packs/artifact/review.md` | 规定怎样呈现 matrix、finding、评分和返修顺序，不重新定义规则 |
| 评分权重与允许的 Hard Fail code | `config/review_weights.json` | 六维权重不变；只新增必要的已核验官方规则违规 code |
| 评分与 matrix 结构校验 | `scripts/score_submission.py` | 保持旧输入兼容；校验新 matrix，不推断论文语义 |
| 正式 LaTeX 源审计 | `scripts/audit_latex_project.py` / `scripts/audit_paper_prose.py` | 第一版冻结，不把元数据、文献真实性或图表冗余误做成字符串机器结论 |
| 编译与 PDF 证明链 | `scripts/render_paper.py` / `scripts/latex_delivery.py` | 第一版冻结，不新增第三方 PDF 解析依赖，不改变 report schema |
| 项目状态与模型语义 | `core/project_state.schema.yaml` 及模型/数值 Authority | 完全不变；review matrix 不进入模型 semantic hash |

目标链路：

```text
已核验 edition rules + 当前 competition Pack
                    ↓
modules/06_review_delivery.md
Final Review Compliance & Evidence Sweep
                    ↓
review_report / Final Review Matrix
                    ↓
scripts/score_submission.py
结构校验 + 六维评分 + Hard Fail 隔离
                    ↓
现有 official/reproducibility package 流程
```

Review Matrix 是终审报告的结构化载体，不是新的规则 Authority，不是新的项目事实源，也不得进入只允许 PDF 的 official package。

---

## 5. 目标终审流程

`final_review_and_delivery` 在 AI Cleanup、正式 LaTeX 审计与编译之后执行，新增以下顺序：

### 5.1 恢复审查上下文

读取：

- 当前完整 `模型论文框架.md`；
- 当前论文源文件和最终 PDF；
- `latex_audit_report.yaml`；
- `compile_report.yaml`；
- 当前 competition profile 与实际加载的 competition Pack；
- `edition_rules.verification_status / verified_at / source`；
- official 或 reproducibility 的目标交付模式；
- 已存在的 draft review findings 及其处置状态。

不得仅根据赛事名称、往届经验或外部自查表推定当届规则。

### 5.2 先执行现有语义审查

完整保留当前数学、模型、数值、Claim、引用、图表、跨文件 seam、编译和交付审查。新增能力不能降低、跳过或替代现有检查。

### 5.3 再执行 Compliance & Evidence Sweep

按实际适用性生成以下检查族，而不是展开固定 287 行：

1. `edition_compliance`
2. `anonymity_and_metadata`
3. `ai_disclosure`
4. `citation_entity_integrity`
5. `rendered_page_surface`
6. `figure_table_information_value`
7. `reproducibility_and_package`
8. `cross_question_dynamic_coverage`

每个检查族必须给出：适用性、规则来源、验证方式、状态和证据。存在问题时再生成原子 finding。

### 5.4 形成返修顺序

继续遵守当前返修优先级：

```text
改变答案/数学语义/事实来源
→ 已核验官方规则或匿名性违规
→ 核心结果、stale、模型/算法/代码/工作簿不一致
→ Claim / Citation / Title / Evidence 断链
→ 页面对象不可读、裁切或提交材料缺失
→ 结构、冗余与一般视觉 warning
```

不得因为新增了视觉和合规清单，就先修排版再修数学错误。

### 5.5 交付判定

- unresolved `blocking`：不得交付；
- unresolved `review_required`：正式 review report 必须明确要求补证据、修复或记录有依据的例外；
- `warning`：不自动阻断，但必须记录是否接受；
- `unverifiable`：不得伪装成 `passed`；
- Hard Fail 继续独立于加权总分；
- review report 不自动加入 official package。

---

## 6. Final Review Matrix 设计

新增 `templates/review/final_review_matrix.yaml`，作为新正式终审报告的可选、机器可读模板。它不进入 Project State Schema，也不成为所有旧项目的强制迁移对象。

建议结构：

```yaml
review_schema_version: 1.0.0
review_context:
  skill_version: 8.2.0
  competition_profile: null
  edition: null
  rule_verification_status: unverified
  rule_verified_at: null
  rule_source: null
  delivery_mode: null
  source_bundle_sha256: null
  compiled_pdf_sha256: null

coverage:
  - check_family: edition_compliance
    applicability: applicable
    verification_mode: hybrid
    status: unverifiable
    rule_source: null
    evidence: null

findings: []

scores: {}
hard_fail: []
evidence: {}
```

### 6.1 Coverage 字段

每个检查族使用：

- `check_family`：稳定标识；
- `applicability`：`applicable / not_applicable`；
- `verification_mode`：`machine / manual / hybrid`；
- `status`：`passed / findings_present / unverifiable / not_applicable`；
- `rule_source`：官方来源、Authority 锚点或审计报告位置；
- `evidence`：页码、文件、hash、报告字段、图号/表号或人工检查记录。

`not_applicable` 必须有理由；`unverifiable` 不能留空 evidence，至少说明缺少什么。

### 6.2 Finding 字段

每个非通过问题至少包含：

```yaml
- check_id: FR-001
  check_family: anonymity_and_metadata
  dimension: reproduction_and_delivery
  severity: review_required
  status: open
  hard_fail_code: null
  rule_source: config/competition_profiles.yaml#profiles.<name>.edition_rules
  verification_mode: manual
  location: final_latex/main.pdf#metadata
  evidence: "Author 字段仍含身份信息"
  action: "清理元数据后重新编译并刷新 compile/submission hashes"
```

字段约束：

- `check_id` 在单份报告中唯一；
- `dimension` 必须来自当前六维评分配置；
- `severity` 只能为 `blocking / review_required / warning`；
- `status` 只能为 `open / resolved / accepted_exception`；
- `blocking + open` 必须给出允许的 `hard_fail_code`；
- 非 `resolved` finding 必须有具体 evidence、location 和 action；
- `accepted_exception` 不能用于绕过已核验 Hard 规则；
- 不根据 finding 数量自动扣 1/2 分；
- 不根据字符串命中自动判断数学正确性、文献支持性或身份泄露。

### 6.3 与六维评分的关系

保持现有六维权重不变：

- 题意与机制；
- 数学闭环；
- 数据与验证；
- 结果与图表；
- 写作与排版；
- 复现与交付。

Matrix 为评分提供证据，不反向用固定扣分生成评分。`scores` 仍由评委式判断形成，但每个维度必须能指向 coverage 或 findings 中的证据。

---

## 7. 分级与规则来源

### 7.1 规则来源优先级

```text
当届已核验官方规则 / 题面
→ 当前 competition Pack 的稳定模板约束
→ Template Manifest
→ Writing / Reasoning Authority
→ Review 默认规则
→ 经验建议
```

低层规则不得覆盖高层规则，经验建议不得伪装成官方要求。

### 7.2 Edition Rules

- `verification_status=verified` 且有 `verified_at + source`：可以据此判定 Hard 违规；
- `unverified / expired`：不得把页数、匿名或 AI 披露默认值写成已满足；official package 继续服从现有阻断逻辑；
- 未核验时可以记录一般隐私或表达风险，但不能声称违反当届规则；
- 页数、目录、页码起始、页眉页脚、AI 声明位置等只按当届来源执行。

### 7.3 建议新增的 Hard Fail code

在 `config/review_weights.json` 中只新增一个通用 code：

```text
verified_official_rule_violation
```

使用条件：

1. 规则来源为当前 profile 的已核验 `edition_rules` 或其官方来源；
2. 规则适用于当前 delivery mode；
3. finding 有明确证据；
4. 违规未解决；
5. 不能被现有更具体 Hard Fail code 更准确表示。

不得为页数、匿名、AI 披露分别无限扩张 Hard Fail code 列表。身份泄露、缺少强制 AI 声明或超出官方页数可在满足上述条件时映射到同一官方规则违规 code，并在 finding 中保留具体类别。

### 7.4 默认严重级示例

| 情况 | 分级 |
|---|---|
| 违反当前已核验、适用且强制的匿名/页数/AI 披露规则 | `blocking` |
| 官方规则未核验，却准备生成 official package | 由现有 package 流程阻断；Review 记录 `review_required / unverifiable` |
| PDF 作者元数据含身份信息，但赛事匿名规则尚未核验 | `review_required`，不得宣称官方违规 |
| 核心参考文献无法确认真实存在或不能支持核心 claim | 按 Citation Evidence Authority 判 `blocking` 或 `review_required` |
| DOI/卷期页码格式不完整但不影响核心来源定位 | `review_required` 或 `warning` |
| 图和表完全重复且无独立信息价值 | `warning`；若挤占篇幅或导致核心证据不可读则升级 `review_required` |
| 图表裁切、关键数值不可读或跨页导致结论不可恢复 | `review_required`；若破坏核心答案交付可映射现有 Hard Fail |
| 一般孤行、局部空白或风格不统一 | `warning` |

---

## 8. 自动检查与人工检查边界

第一版不新增 PDF 解析库，不调用网络作为评分器的隐藏依赖，也不让简单字符串匹配替代语义审查。

| 检查对象 | 第一版方式 | 原因 |
|---|---|---|
| LaTeX label/citation key/结构 | 继续使用现有机器审计 | 已有确定性实现和测试 |
| compile/PDF/source hash | 继续使用现有 attestation | 已有 current/stale 证明链 |
| 当届 edition rule 是否 verified | 机器读取配置 | 字段明确、可确定 |
| official package allowlist | 继续使用现有 package validator | 已有正式 gate |
| PDF 作者/公司/标题元数据 | 可用工具读取时记录机器证据；否则人工检查并标记方式 | 不引入新的强制依赖 |
| 图片、代码截图、路径、账户中的身份信息 | 人工/视觉检查 | 语义与视觉判断，字符串规则误报高 |
| AI 声明是否符合真实使用 | 用户事实 + 当届规则 + 人工核对 | Skill 不能猜测用户真实使用历史 |
| DOI、作者、题名、卷期页码是否真实匹配 | 人工或可用外部检索；记录来源 | 不把网络可用性变成评分器运行前提 |
| 文献是否支持对应 claim | 人工语义检查 | citation 存在不等于支持 |
| 图表是否重复表达 | 人工语义检查 | 物理相邻和数值相似不能证明冗余 |
| 孤行、标题悬空、裁切、溢出、空白 | 最终 PDF 逐页视觉检查 | 源码字符串不足以判断渲染结果 |

如果实现阶段发现当前仓库已有跨平台、无新增依赖且有稳定测试夹具的 PDF 元数据读取能力，可另写后续 patch 计划；不得在本次功能 PR 中临时扩展依赖和 compile report schema。

---

## 9. 逐文件实施方案

### 9.1 `modules/06_review_delivery.md`

作为本次唯一终审语义 Authority，新增：

1. `Final Submission Compliance & Evidence Sweep`；
2. edition rule 恢复与 verified/unverified 分流；
3. 匿名/元数据、AI 披露、Citation Entity、Rendered Surface、图表信息价值检查族；
4. coverage 与 finding 的最小证据要求；
5. `unverifiable` 不得当作 `passed`；
6. 已核验官方规则违规与 Hard Fail 的映射；
7. 自动/人工边界；
8. review matrix 不进入 official package、模型 hash 或 project state。

不得在本文件复制具体赛事年度数值，不得把自查表中的经验阈值升级为 Hard。

### 9.2 `packs/artifact/review.md`

更新 Review Adapter：

- 指向 `modules/06_review_delivery.md` 的新 sweep；
- 要求报告先给 Hard/重要/一般问题，再给六维评分；
- 对新正式报告使用 `templates/review/final_review_matrix.yaml`；
- 每个 finding 给出位置、证据、原因、动作和规则来源；
- 不在 Pack 内重复检查规则；
- 不把 review matrix 加入 official package。

### 9.3 `templates/review/final_review_matrix.yaml`

新增一个最小模板：

- 只提供字段和稳定枚举；
- 不预置 287 条检查；
- 不预置 1/2 分扣分；
- 不预置 5 问或固定模型数量；
- 不包含赛事年度值；
- 动态生成 coverage 和 findings；
- 保留旧 `scores / hard_fail / evidence` 输入结构。

### 9.4 `scripts/score_submission.py`

保持现有函数和 CLI 兼容，增加可选 matrix 校验：

1. 没有 `review_schema_version` 的旧报告继续按原逻辑评分；
2. `review_schema_version=1.0.0` 时校验 context、coverage 和 findings；
3. 检查稳定检查族、枚举、唯一 ID、已知评分维度；
4. 检查 open blocking finding 必须映射允许的 Hard Fail code；
5. 检查每个评分维度都有 evidence；
6. 在输出中附加 `review_status`、规范化 `coverage` 和 `findings`；
7. 不从 finding 数量自动计算分数；
8. 不读取论文正文、PDF 或互联网；
9. 不推断官方规则是否真实，只校验报告声明的 rule context 是否结构闭合。

若新 matrix 结构错误，明确报错；不得静默丢弃未知字段或未知严重级。

### 9.5 `config/review_weights.json`

- 六个维度、权重、100 分量表和现有 Hard Fail code 全部保持；
- 新增 `verified_official_rule_violation`；
- 配置自身 version 按该配置既有版本策略最小递增，不能机械等同 Skill 版本；
- `hard_fail_action` 保持 `reject_or_major_rework`。

### 9.6 测试

新增 `tests/test_v820_final_review_compliance.py`，覆盖新能力；在 `tests/test_tooling.py` 只补评分器兼容与集成断言，不重写既有测试。

测试不得调用互联网，不依赖真实 PDF 解析器，不修改用户项目。

### 9.7 `scripts/lint_skill_checks.py`

只增加最小静态合同检查：

- Review Authority 必须包含新 sweep、verified/unverified、machine/manual boundary；
- Review Pack 必须引用 Authority 和 matrix 模板；
- matrix 模板存在且不含固定 287 行、固定问数或 `扣 1 / 扣 2` 逻辑；
- root/package Skill 版本和 Authority parity 保持；
- 禁止把新规则复制进 AI Cleanup 或 Paper Writing Protocol。

不进行大规模 lint 重构。

### 9.8 版本载体与说明

实施完成并通过专项测试后，按现有 release 规则更新 `8.2.0` 载体：

- `.codex-plugin/plugin.json`；
- `SKILL.md`；
- `skills/mathmodel-skill/SKILL.md`；
- `core/bootstrap.yaml`；
- `core/hsk_core_policy.md`；
- `core/workflow_router.yaml`；
- `core/module_manifest.yaml`；
- `core/output_contract.yaml`；
- `core/writing_runtime_contract.yaml`；
- `README.md`；
- `CHANGELOG.md`；
- 受影响的精确版本测试。

除明确新增 Review 指针或运行时读取说明外，上述合同文件只允许版本字段和最小集成指针变化。不得全仓库盲目替换版本号，不得修改历史版本文本。

### 9.9 生成文件

手工修改完成后只通过现有生成器刷新：

- `SKILL_FILE_INDEX.md`；
- `TEMPLATE_INDEX.md`；
- compatibility indexes（仅生成器确实产生差异时）；
- `MANIFEST.sha256`。

禁止手工修改哈希。

### 9.10 第一版明确冻结的活动文件

以下文件在 v8.2.0 第一版只做 SHA 防漂移检查，不实施功能修改：

- `config/competition_profiles.yaml`；
- `scripts/audit_paper_prose.py`；
- `scripts/audit_latex_project.py`；
- `scripts/latex_delivery.py`；
- `scripts/render_paper.py`；
- `modules/05_latex_compile_quality.md`；
- `modules/05_writing/ai_cleanup.md`；
- `modules/05_writing/paper_writing_protocol.md`；
- `core/writing_reasoning_contract.yaml`；
- `core/project_state.schema.yaml`。

这样可避免把“终审报告结构增强”扩大成 PDF 工具链、写作规则、项目状态和语义 Authority 的同时重构。

---

## 10. 版本、兼容与迁移

### 10.1 版本判断

该能力新增：

- 终审检查族；
- Review Matrix 模板；
- 评分器的可选结构校验；
- 新的官方规则 Hard Fail 映射。

它是向后兼容的新能力，因此候选版本为：

```text
8.1.1 → 8.2.0
```

### 10.2 旧项目

- 不新增 Project State 必填字段；
- 不改变 Model Paper Framework schema；
- 不改变工作簿或每问五文件结构；
- 不改变 LaTeX audit/compile report schema；
- 不改变 submission manifest；
- 旧评分报告没有 matrix 时继续可评分；
- 新正式终审建议生成 v1 matrix，但不要求旧报告批量迁移。

### 10.3 新项目

新生成的正式 final review report 使用 v1 matrix，并在 official delivery 前明确记录：

- competition profile；
- edition rule verification 状态；
- delivery mode；
- source/PDF 证明链；
- 8 个检查族覆盖状态；
- unresolved findings；
- 六维评分与 Hard Fail。

---

## 11. 明确不做

本修改明确禁止：

- 不修改 AI Cleanup，不把自查表改造成 AI 痕迹识别规则；
- 不把外部工作簿加入仓库、Skill、模板或提交包；
- 不复制全部 287 项；
- 不使用固定 1/2 分扣分；
- 不改变六维评分权重；
- 不把 4--5 个关键词、30 页、22--25 页、标题密度等经验值写成通用 Hard；
- 不添加另一套 `final_review_contract.yaml`；
- 不修改 Paper Writing Protocol 或 Writing Reasoning Authority；
- 不新增 Project State / Framework 字段；
- 不把 review matrix 加入模型 semantic hash；
- 不因纯 Review 文案和报告变化使 `locked_model_spec` stale；
- 不触发 Model Approval、03A 重算、03B 重算或 Figure Evidence 重做；
- 不新增 pre-delivery gate；
- 不改变 official/reproducibility package allowlist；
- 不把内部 review report 自动打进 official ZIP；
- 不新增 PDF 解析库、网络检索库或外部服务依赖；
- 不修改 compile/audit report schema；
- 不让机器按关键词判定文献真假、AI 使用事实、身份泄露或图表语义重复；
- 不修改 `legacy/` 并让活动运行时依赖历史材料；
- 不混入 CI、LaTeX 字体、模板、索引结构或无关清理。

---

## 12. 受保护语义冻结

以下基线 blob SHA 来自 `main@d30b861f55e78d7ca8a4e991034a6019f560b5c6`。实施前必须从最新 `main` 重新冻结；如果计划合并后基线已变化，以重新冻结结果为准，并记录原因。

### 12.1 必须逐字节保持的模型、数值与写作语义

| 受保护文件 | 基线 blob SHA |
|---|---|
| `core/model_approval_contract.yaml` | `7d97255dde9cf780755bab896964e905066bf4b8` |
| `core/numerical_verification_contract.yaml` | `b901923edf38112cbc922f51d1157265fe1931bd` |
| `core/workbook_schema.yaml` | `2422bbfa8cb3fad3b5b04c12de21c954ec8b3723` |
| `core/project_state.schema.yaml` | `fa12de39d7bbdc2e014b2912a186834b941b28d4` |
| `modules/03_solve_validate.md` | `f49480d96e6a491255010868e409b2d64d620f5e` |
| `modules/03_result_analysis.md` | `f43d21dc99d71e6b19baeec7af66cbf334da13a7` |
| `modules/04_figure_evidence.md` | `3a34af07c7c8f58769e28dc22ab3b712481107f7` |
| `templates/latex/cumcm/hsk/template_manifest.yaml` | `32402842ea88c2a4ce3df052f6c01534b357549f` |
| `core/writing_reasoning_contract.yaml` | `adb962b3b764c08f78fdb002b97401adde693856` |
| `modules/05_writing/paper_writing_protocol.md` | `5404b1dc891227249644b040c40482bd6065b81a` |
| `modules/05_writing/ai_cleanup.md` | `c5200f4f1513c6770952284ac2d49e3db7bef273` |
| `config/competition_profiles.yaml` | `fcddec42a30ad4d4bc760dc8322cc13a998a6ebd` |

### 12.2 第一版必须保持的审计与编译实现

| 受保护文件 | 基线 blob SHA |
|---|---|
| `scripts/audit_paper_prose.py` | `6ef6f56308f467d5f457a444de332eee76b457fe` |
| `scripts/audit_latex_project.py` | `a72da641274e8515780b68699b50624b1e29dadf` |
| `scripts/latex_delivery.py` | `c86f1d3e3ea6dd8cd934484df9359a23e5951b49` |
| `scripts/render_paper.py` | `000d60e092ff2942f5a1de582cb2492f6c21ea34` |

### 12.3 允许按本计划修改的核心基线

| 目标文件 | 基线 blob SHA | 允许变化 |
|---|---|---|
| `modules/06_review_delivery.md` | `7c703a27301634bac6b71fa183b88e8f8048258e` | 新 sweep、matrix 语义、分级与人工/机器边界 |
| `packs/artifact/review.md` | `e4b93d1a3f02173af9aae30ef05ec798f6070e69` | 报告适配与 Authority 指针 |
| `scripts/score_submission.py` | `9861893ba7ddc0fe0f24f2d2f583b1f37bb0fd27` | 向后兼容的 matrix 校验 |
| `config/review_weights.json` | `73c7835f15d7643baaaf90e63a474118a6ec3ea3` | 单一官方规则 Hard Fail code；权重不变 |

Release carriers 只允许目标版本、最小能力摘要和必要指针变化。对 `core/writing_runtime_contract.yaml` 等载体执行 version-normalized diff，证明没有夹带业务语义改写。

---

## 13. 实施顺序

### 阶段 A：计划批准与干净基线

1. 合并本计划 PR 前不写功能代码；
2. 用户明确批准计划；
3. 计划进入 `main`；
4. 从最新 `main` 重新确认版本、提交、开放 PR 和 Authority；
5. 重新冻结所有受保护 blob SHA；
6. 创建 `upgrade/v820-final-review-compliance`。

### 阶段 B：先写失败测试

1. 新增 matrix 模板结构测试；
2. 新增旧评分报告兼容测试；
3. 新增未知枚举、重复 ID、缺证据、未知 dimension 拒绝测试；
4. 新增 open blocking 与 Hard Fail 映射测试；
5. 新增 verified/unverified 官方规则上下文测试；
6. 新增“finding 数量不自动扣分”测试；
7. 新增 review matrix 不进入 official package 的回归。

### 阶段 C：最小实现

1. 新增 `templates/review/final_review_matrix.yaml`；
2. 扩展 `scripts/score_submission.py`；
3. 更新 `config/review_weights.json`；
4. 更新 `modules/06_review_delivery.md`；
5. 更新 `packs/artifact/review.md`；
6. 加入最小 lint contract；
7. 运行专项测试，先确认旧输入兼容。

### 阶段 D：版本与生成文件

1. 确认功能边界没有扩大；
2. 更新精确 release carriers 到 `8.2.0`；
3. 更新 README/CHANGELOG 的当前版本说明；
4. 运行生成器；
5. 检查生成 diff 只包含预期索引和 hash。

### 阶段 E：全量验收

1. 运行基础 lint、完整单元测试、生成文件检查；
2. 运行 Review/Score/Submission 专项测试；
3. 运行三套 LaTeX 和 Production attestation；
4. 比较受保护 blob SHA；
5. 检查 root/package Skill byte parity；
6. 检查版本载体同步；
7. 确认 PR 没有外部工作簿、临时文件、无关格式化或生成噪声；
8. 全部 CI 通过后才合并；
9. 合并后执行一次 current-main 健康审计。

---

## 14. 测试矩阵

### 14.1 评分兼容

- 旧格式 `scores + hard_fail + evidence` 输出与 v8.1.1 一致；
- 旧报告不因缺少 matrix 而报错；
- 六维权重仍精确和为 1；
- 分数范围仍为 0--100；
- 现有 Hard Fail code 全部继续可用。

### 14.2 Matrix 正向测试

- 完整 v1 context/coverage/findings 可通过；
- 8 个检查族可以按实际情况标记 applicable/not_applicable；
- resolved warning 不阻断评分；
- open review_required 进入 `review_status`；
- open blocking 及其 hard-fail code 触发 `reject_or_major_rework`；
- 每个 dimension 能恢复 evidence；
- normalized output 保留 rule source、location、evidence 和 action。

### 14.3 Matrix 反向测试

- 重复 `check_id` 失败；
- 未知 `dimension / severity / status / verification_mode / check_family` 失败；
- open finding 缺 location/evidence/action 失败；
- open blocking 缺 hard-fail code 失败；
- 使用未知 hard-fail code 失败；
- 声称 `verified_official_rule_violation` 但缺 verification status/source 失败；
- `unverifiable` 被写成 `passed` 的矛盾结构失败；
- finding 数量变化不改变显式 scores；
- review matrix 出现在 official allowlist 时由现有 package 边界测试拒绝。

### 14.4 Authority 防漂移

- `config/competition_profiles.yaml` 仍是 edition rules 唯一机器来源；
- `modules/06_review_delivery.md` 是新 sweep 唯一语义 Authority；
- `packs/artifact/review.md` 只适配，不复制规则；
- AI Cleanup 与 Paper Writing Protocol 不出现新终审合同；
- Writing Reasoning Contract 不被重复或改写；
- review matrix 不进入 model semantic hash；
- review-only finding 不使 `locked_model_spec` stale；
- 不新增 Project State 字段或 pre-delivery gate。

### 14.5 必跑命令

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/generate_indexes.py --check
python -m unittest tests.test_tooling
python -m unittest tests.test_v820_final_review_compliance
```

### 14.6 必须通过的 CI

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

---

## 15. 验收标准

v8.2.0 只有同时满足以下条件才算完成：

1. Final Review 能显式恢复当前 competition profile、edition verification 和 delivery mode；
2. 未核验赛事规则不会被误报为官方要求；
3. 已核验强制规则的未解决违规不能被总分抵消；
4. Review Matrix 能记录覆盖范围和原子 finding；
5. 每个 finding 具有规则来源、位置、证据、严重级、状态和修改动作；
6. 旧评分报告继续可用；
7. 六维权重和旧 Hard Fail 语义不变；
8. 没有复制 287 条清单或固定问数；
9. 没有新增 PDF/网络依赖；
10. 没有改变 audit/compile report schema；
11. review matrix 没有进入 Project State、模型 hash 或 official package；
12. AI Cleanup、Paper Writing Protocol 和 Writing Reasoning Authority 保持不变；
13. Model Approval、Numerical Verification、Workbook、03A、03B、Figure Evidence 与 Template Manifest 的冻结 SHA 保持；
14. release carriers 全部同步到 8.2.0；
15. 生成索引和 `MANIFEST.sha256` 由生成器产生且 current；
16. 全部单元测试与 CI 通过；
17. PR 只包含本主题，无无关清理、格式化或工具链重构。

---

## 16. 风险与抑制措施

| 风险 | 抑制措施 |
|---|---|
| 把经验清单升级成 Hard | Hard 必须绑定 verified edition rule 或现有 Authority；测试 unverified 分流 |
| Review Authority 与 Writing Authority 重复 | Review 只定义检查与分级；正文规则继续引用现有 Authority |
| 287 条导致上下文膨胀 | 使用 8 个动态检查族 + 问题触发的原子 findings |
| 评分被 checklist 数量操纵 | 禁止固定扣分；scores 显式给出并以 evidence 支撑 |
| 新报告破坏旧项目 | matrix 可选；旧报告路径保持 |
| PDF 元数据检查引入依赖 | 第一版人工/可用工具检查，不改编译工具链 |
| 网络不可用导致评分失败 | 文献实体核验记录验证方式；评分器不联网 |
| AI 使用事实被模型猜测 | 必须读取用户确认和当届规则；无法确认则 unverifiable |
| 内部报告泄漏进 official ZIP | Pack 明确禁止，并保留 package allowlist 回归 |
| 新 review 状态触发模型 stale | 测试锁死 review-only 不进入 semantic hash |
| 版本载体出现漂移 | 精确载体清单 + lint + version-normalized diff |
| 修改范围失控 | 第一版冻结 audit/compile/profile/project-state/writing 文件；超过治理阈值即停止拆分 |

---

## 17. 回滚与后续扩展

### 17.1 回滚

如果 matrix 校验、评分输出或 Review Runtime 出现非预期影响：

1. 回滚单一 v8.2.0 功能 PR；
2. 旧报告继续使用 v8.1.1 的 `scores + hard_fail + evidence` 路径；
3. 不迁移或回滚项目状态、模型审批、工作簿、LaTeX 源码、PDF 或 submission manifest；
4. 重新生成当前索引和 manifest；
5. 运行全量测试确认恢复。

### 17.2 明确推迟到后续独立评估的能力

以下内容不属于 v8.2.0 第一版；只有出现稳定、跨平台、低误报实现后再单独计划：

- PDF 元数据的内置解析器；
- DOCX 隐藏批注/修订记录机器扫描；
- DOI/Crossref/官方页面的在线实体核验；
- 图表数据重复度的半自动比较；
- PDF 版面对象检测；
- review report 纳入 formal attestation hash 链；
- 新的 pre-delivery compliance gate；
- Project State 中的 review artifact 字段。

这些扩展不得以“顺手补上”为由混入第一版。

---

## 计划批准后的准确状态语义

本计划文件进入 `main` 只表示实施范围已获得仓库级上下文，不表示 v8.2.0 已实施。后续状态必须区分：

```text
详细计划      ✅ 已写入 / 待批准或已批准
计划入 main   ⏳ 取决于计划 PR 状态
实施前冻结    ⏳ 功能分支建立前重新执行
v8.2.0 实施   ⏳ 尚未写入
v8.2.0 PR     ⏳ 尚未建立
完整 CI       ⏳ 尚未执行
最终健康审计  ⏳ 尚未执行
正式 Skill    8.1.1（直到功能 PR 合并并验证）
```

不得把“计划已批准”或“计划已合并”表述为“终审能力已经进入正式运行链”。
