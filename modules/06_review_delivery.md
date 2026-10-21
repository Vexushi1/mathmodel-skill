# Module 06：评委式终审与交付

本模块只负责**检查、分级、返修排序和交付判定**，**不重新定义正文写作规则**。普通正文写法只消费 `modules/05_writing/paper_writing_protocol.md`，作者声音检查直接消费 `paper_writing_protocol.md#7.3-作者视角与建模解释`，复杂数学/证据语义只消费 `core/writing_reasoning_contract.yaml`，固定 CUMCM 骨架只消费 Template Manifest；Review 不复制这些规则。

消费时机只有两类：

- `draft_semantic_review`：正文初稿完成、AI Cleanup 前，检查数学/证据/能力激活/结构/引用风险，不要求 compile report，也不做最终交付判定；
- `final_review_and_delivery`：Cleanup、装配、正式 audit/compile 后，覆盖全文 active scope、所有 assembled seam 与机器证据，给出最终 delivery decision。

## 一、评审分级

- **blocking**：已有 Hard 违规，修复前不得交付；
- **review_required**：Default 偏离或语义裁决未闭合，需要修复或可验证 justification；
- **warning**：Recommendation / 表面风险，不阻断交付。

每个 finding 至少记录 `scope / location / authority / evidence / severity / repair / status`。机器能够证明的只按确定性证据定级；不能由关键词、词频或句式推断数学正确性。

## 二、题意、框架与局部 stale 审查

正文已移至 [共用内容审查](06_review/content_review.md#二题意框架与局部-stale-审查)。

### Cross-File Assembled Seam Sweep

正文见 [共用内容审查的 assembled seam 检查](06_review/content_review.md#cross-file-assembled-seam-sweep)。

## 三、公式、模型角色、算法、命题与数值证据审查

正文已移至 [共用内容审查](06_review/content_review.md#三公式模型角色算法命题与数值证据审查)。

### Question Writing Capability Activation Review

正文见 [能力激活检查](06_review/content_review.md#question-writing-capability-activation-review)。

### Author Reasoning Semantic Review

正文见 [作者推理语义检查](06_review/content_review.md#author-reasoning-semantic-review)。

### Formula-Rich Narrative Readability Review

正文见 [公式叙事可读性检查](06_review/content_review.md#formula-rich-narrative-readability-review)。

### Core Derivation Body Closure Review

正文见 [核心推导正文闭合检查](06_review/content_review.md#core-derivation-body-closure-review)。

### Model Construction & Solution Rationale Review

正文见 [建模与求解理由检查](06_review/content_review.md#model-construction--solution-rationale-review)。

## 四、Terminology、Numeric Style 与 Claim Strength 审查

正文已移至 [共用内容审查](06_review/content_review.md#四terminologynumeric-style-与-claim-strength-审查)。

### Terminology

正文见 [术语检查](06_review/content_review.md#terminology)。

### Numeric Style

正文见 [数值风格检查](06_review/content_review.md#numeric-style)。

### Claim Strength

正文见 [主张强度检查](06_review/content_review.md#claim-strength)。

## 五、Title Claim、正文结构与 Paragraph Necessity

正文已移至 [共用内容审查](06_review/content_review.md#五title-claim正文结构与-paragraph-necessity)。

### v7.20/v8.0.1 章节能力保全检查

正文见 [章节能力保全检查](06_review/content_review.md#v720v801-章节能力保全检查)。

## 六、深化分析、图表与结果证据审查

正文已移至 [共用内容审查](06_review/content_review.md#六深化分析图表与结果证据审查)。

## 七、Citation Evidence 与参考文献审查

正文已移至 [共用内容审查](06_review/content_review.md#七citation-evidence-与参考文献审查)。

## 八、编译、复现与提交包

正文已移至 [终稿证据与交付审查](06_review/final_delivery.md#八编译复现与提交包)。

## 九、Final Submission Compliance & Evidence Sweep

<a id="Final-Submission-Compliance-Evidence-Sweep"></a>

正文已移至 [终稿证据与交付审查](06_review/final_delivery.md#九final-submission-compliance--evidence-sweep)。

### 1. 恢复终审上下文

正文见 [恢复终审上下文](06_review/final_delivery.md#1-恢复终审上下文)。

### 2. 动态检查族

正文见 [动态检查族](06_review/final_delivery.md#2-动态检查族)。

### 3. 原子 finding 与评分关系

正文见 [原子 finding 与评分](06_review/final_delivery.md#3-原子-finding-与评分关系)。

### 4. 已核验规则与 Hard Fail

正文见 [已核验规则与 Hard Fail](06_review/final_delivery.md#4-已核验规则与-hard-fail)。

### 5. 机器与人工边界

正文见 [机器与人工边界](06_review/final_delivery.md#5-机器与人工边界)。

## 十、返修优先级

按 `blocking → review_required → warning`，并优先修复会使大量下游 stale 的上游问题。数学/事实错误先回模型或数值阶段；写作语义缺口回对应 Authority；纯表达问题交 Cleanup；LaTeX/提交问题交载体或 package gate。修复后只重审真实受影响范围及必要跨文件 seam/全篇一致性，不机械全文重写。

## 十一、Blocking 条件

以下任一成立不得最终交付：题意/输出硬要求缺失；current claim 使用 stale/未验收事实；必要模型/公式/约束、非显然核心推导或证明逻辑断裂；关键数值/单位/精度错误；局部/启发式结果被宣称为严格全局结论；外部核心 claim 无必要来源；正式引用/编译/包级 gate 失败；verified official rule 明确违规；或 required delivery gate 尚未成功执行。

除此之外的标题数量、第一人称、连接词、普通风格偏好等不得自动升级为 blocking。
## 阅读调度与兼容入口

实际来源集合由 `core/module_manifest.yaml#modules.review_delivery.reading_sources` 唯一定义：

- `draft_semantic_review` 读取本入口与 `modules/06_review/content_review.md`；
- `final_review_and_delivery` 读取本入口、共用内容审查与 `modules/06_review/final_delivery.md`。

本页保留旧标题与锚点供已有引用定位；搬出的段落仅在叶文件维护。读取兼容入口或旧锚点时，必须按既有 reading plan／正文提取接口展开并取得对应真实正文，不能把本页的指针视为审查已完成。未限定阶段的旧整文件请求读取完整三文件闭包；缺源或歧义不得以 stub 通过。
