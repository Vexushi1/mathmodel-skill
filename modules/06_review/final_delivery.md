# Module 06：终稿证据与交付审查

本文件只在 `final_review_and_delivery` 消费，并须同时读取 [`modules/06_review_delivery.md`](../06_review_delivery.md) 与 [`content_review.md`](content_review.md)。草稿审查不提前要求本文件的最终编译、证据与提交闭合。

## 八、编译、复现与提交包

交付前核对当前 LaTeX 源码、真实编译日志与 PDF，处理未解析引用、编译错误及源码与成品不一致。每问文件、目录和提交内容按 `core/output_contract.yaml#per_question`、Artifact Packs 与已核验赛事规则逐项检查。PDF 逐页检查由助手按 Module 05D 执行。

## 九、Final Submission Compliance & Evidence Sweep

### 1. 恢复终审上下文

final review 读取 current framework、active assembly、题目要求、verified competition rules、真实图表与编译证据；数值按 `core/user_execution_contract.yaml#result_handoff` 从工作簿核对，已有工具报告一并读取。

### 2. 动态检查族

终审必须覆盖题意/输出、模型语义、数值与精度、写作能力激活、术语/claim、图表、引用、编译和提交合规。可按 physical file / question / check family 分批读取以控制上下文，但必须维护 coverage ledger；每个 active file、current question、headline claim 与 required gate 都有明确 covered 状态，**不得抽样几个章节就宣称全文通过**。

机器检查族：`edition_compliance`、`anonymity_and_metadata`、`ai_disclosure`、`citation_entity_integrity`、`rendered_page_surface`、`figure_table_information_value`、`reproducibility_and_package`、`cross_question_dynamic_coverage`。仅供 `templates/review/final_review_matrix.yaml` 覆盖闭合，不复制正文规则。finding 标明 `machine / manual / hybrid` 来源；赛事规则只有 `verification_status=verified` 才可形成官方 Hard，`unverified / expired` 只能进入复核。已核实官方硬违规统一记为 `verified_official_rule_violation`。内部矩阵与中间材料不进入 Project State，不得自动加入 official package；C1 回执仅按 `core/review_receipt_contract.yaml` 入 State，不替代矩阵或人审。

### 3. 原子 finding 与评分关系

finding 定位到最小可修复对象，并记录 evidence/authority/severity/repair/status。评分只消费已完成 findings，不以总分掩盖 blocking。

### 4. 已核验规则与 Hard Fail

当届官方页数、匿名、提交文件或 AI 披露只在 competition profile 已 verified 且有来源/核验日期时作为官方 Hard；未核验时标 review_required，不凭历史记忆创造规则。

### 5. 机器与人工边界

机器检查文件、hash、引用、状态、Schema、coverage 与显式冲突；人工作数学合理性、因果/机制、claim 支持、正文连续性与视觉质量判断。机器不得把“检查脚本成功”当论文内容正确的证明。
