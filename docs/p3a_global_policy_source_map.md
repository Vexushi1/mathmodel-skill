# P3a 全局政策去重来源映射

## 目的

P3a 只压缩默认必读的 `core/hsk_core_policy.md`，不减少任何模型、数值、绘图、写作或交付规则。本文件是维护证据，不是新的业务 Authority。每一类从全局政策删除的阶段细节都必须在现有活动 Authority 中保持唯一、可达定义。

基线：main `2a9cb227067d58d52471f164d317be3b4be330fe`；旧 Core Policy Git blob `5616e090814831f0637fa8de6e365e35d6f8099f`，20,016 bytes。

## 保留在全局政策中的内容

只保留真正跨阶段且必须默认可见的硬边界：题意/语义优先级、Problem Contract 与闭环、Complexity Sanity、显式 Human Model Approval 与 structured identity、typed stale、四类项目事实源、三态预处理原则、用户 full-fidelity 执行、主质量与 accepted 后分析的边界、MATLAB 不重算、论文/图表证据与 claim 强度硬边界、resolver gate 与 legacy 只读边界。

全局政策不再维护目录树、工作簿列名、预处理方法清单、Figure pattern、普通段落写法、兼容迁移逐版本说明或工具列表；这些内容继续由现有 Authority 负责。

## 删除细节的唯一来源

| 旧 Core Policy 区域 | P3a 处理 | Current Authority |
|---|---|---|
| §2.1 Problem Contract 详细字段 | 全局仅保留“先冻结题意”硬边界 | `modules/01_problem_audit.md` |
| §2.2–2.4 Closure / Complexity 实现细节 | 全局保留 hard gap 与异常退化原则 | `modules/02_model_design.md` + `scripts/validate_semantic_governance.py` |
| §2.5 challenge / approval 字段级条件 | 全局保留“显式批准 current identity” | `core/model_approval_contract.yaml` |
| §2.6 框架字段全集与读取模式 | 全局保留四类事实源与 read-before-use | `core/output_contract.yaml`、`core/workflow_router.yaml`、框架模板 |
| §3 12 条预处理规则、目录与图证据 | 全局保留“三态 + 有证据才改数据” | `core/global_preprocessing_contract.yaml` |
| §4 五文件目录树与阶段职责全文 | 从全局删除目录细节 | `core/output_contract.yaml` + `core/user_execution_contract.yaml` |
| §5 工作簿 acceptance、Verification ID 等 | 全局保留 user/full-fidelity 与主/深化边界 | `core/user_execution_contract.yaml` + `core/numerical_verification_contract.yaml` |
| §6 Python/MATLAB/写作详细职责与 Default | 全局只保留跨阶段证据硬边界 | `modules/03_*`、`modules/04_figure_evidence.md`、writing Authorities |
| §7 内部 metadata 与逐版本 compatibility | 从默认全文删除，只保留 legacy 只读原则 | `core/output_contract.yaml` 及各合同 compatibility |
| §8 具体同步工具与 stage 规则 | 全局只保留 resolver gates 必须执行 | `core/output_contract.yaml`、`core/workflow_router.yaml`、`modules/06_review_delivery.md` |

机器映射保存在 `tests/fixtures/p3a_global_policy_source_map.yaml`，测试检查目标 Authority 存在并仍包含对应核心标记。它只防止“删掉摘要同时删掉唯一来源”的回归，不重新定义任何业务规则。

## 兼容与回滚

P3a 不改路由、CLI、Schema、目录、工作簿、审批、求解、写作能力或 gate。旧项目无需迁移。若发现某一移除条款没有唯一来源，恢复该条款或先修复对应 Authority，再重新验收；不得因为默认政策更短而接受语义缺口。
