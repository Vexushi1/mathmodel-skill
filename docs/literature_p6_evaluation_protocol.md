# P6-A 文献增强型模型设计：历史赛题成对评估协议

> 状态：PILOT PROTOCOL — REAL PAIRED RUNS NOT YET RECORDED。
> 本文件定义独立仓库维护实验，不是模型批准、Project State、SIB 或论文 Citation Evidence 的新 Authority。参考原计划 §11–14；当前核心 Authority 永远优先。

## P5 必要性裁决

**暂不增加独立文献机器门禁。** 现有 Model Challenge 已要求关键外部方法具备来源定位、迁移条件、未解决风险处置。检索报告与快照结构 PASS 不证明原文真实、方法适配或人工锁模。缺少真实对照证据时再强制加门，会错误阻断无需外部文献的纯数学题、历史项目，并造成双重权限。P5 状态为 **not_activated_no_demonstrated_need**。若日后实证证明旧门禁稳定漏掉可机器识别的重大文献误用，才另立 PR 测试误报、漏报、运行成本及兼容性。

## 真实历史题的官方来源目录

目录：docs/literature_p6_historical_case_catalog.json，使用 COMAP 官方 2024 年问题页面，涵盖三个异质结构：

| ID | 官方赛题 | 结构性挑战 |
|---|---|---|
| COMAP-2024-MCM-A | Resource Availability and Sex Ratios | 生态系统耦合、资源依赖性别比、稳定性 |
| COMAP-2024-MCM-C | Momentum in Tennis | 逐分时序、发球优势、随机性检验、预测 |
| COMAP-2024-ICM-D | Great Lakes Water Problem | 湖泊水量网络、利益相关方、多目标流量调度 |

官方页面：
- https://www.comap.org/membership/member-resources/item/resource-availability-and-sex-ratios
- https://www.comap.org/membership/member-resources/item/momentum-in-tennis
- https://www.comap.org/membership/member-resources/item/great-lakes-water-problem

目录保存官方网页、PDF 下载网址和必要附件类型，**不复制题目全文，也不存基线答案或增强答案**。必须从官方页面实际取得完整 PDF、题设数据和附录；MCM C 的点级数据及字典、ICM D 的五大湖数据和 Addendum 必须分别绑定本地原始字节 SHA-256。只看到官方网页摘要不构成完整赛题输入。

## 试验和独立评分

基线条件：在独立模型设计过程中不使用新增文献检索能力。增强条件：审题冻结后，评估是否需要文献、开展真实定向检索、分级核验方法及适用前提，保留自主模型推导与 Model Challenge。

同一 Case 的两组必须获得同一 PDF/附件原始文件哈希、同一模型配置标识、同一基础提示模板 SHA-256、同一总时间预算、互不泄漏的隔离上下文。搜索请求、阅读耗时、总耗时、设计 token 数如实记录。先冻结评分规则和原题，再运行；评审者在揭盲之前对 X/Y 分别完成评估。每题至少两位独立评审。对称预算是必要条件，不能凭布尔声明证明实际遵守。

七个并列质量轴均用 0–4 整数评分，0 为核心失败，4 为证据充分、可实施的完整闭环，不使用机械加权总分：

1. requirements_coverage：题设目标、条件和交付逐项覆盖。
2. mathematical_sufficiency：变量、方程、约束、简化与数学充分性。
3. method_transfer_and_assumptions：外部方法及假设与本题对象、量纲、信息边界相符。
4. comparison_and_validation：必要基线、独立验证、敏感性与残差检查设计。
5. source_verifiability：E0/E1/E2/E3 来源分级、原文定位和可信度。
6. solver_feasibility：计算资源、数值条件、工程实现和复现。
7. challenge_resolution：两轮独立质询识别与修复阻断问题。

另记录 blocking_issues、unsupported_assumptions 以及真实搜索与时间成本。评分须附具体依据和可定位错误；不按引用篇数、算法新颖程度、答案长度奖励。

样本量仅三题时**只报告逐题与逐轴的描述性差异**，不宣称统计显著、因果改进或普适优势；文献增强增加成本而无稳定质量收益时应收窄 Targeted/Lightweight 搜索，而非强制 Deep Search。

## 可复现实验工具与输入

在完整 Skill 根目录：

~~~text
python scripts/literature_p6_benchmark.py catalog
python scripts/literature_p6_benchmark.py evaluate --study study.json --study-root path/to/paired-study
~~~

catalog 命令仅显示来源目录，返回 catalog_metadata_only、零对照结果，不访问网络也不下载 PDF。

evaluate 输入 JSON 顶层恰含 protocol_version、study_id、catalog_version、protocol_pre_registered、cases。每 Case 包含：case_id、official_page_url、task（path/sha256）、attachments（kind/path/sha256）、budget_minutes、controls、arms（X/Y）、unblinding（X/Y 分别映射 baseline 与 literature_enhanced）、reviews。

每个 Arm 含 model_runtime、prompt_sha256、design_path、design_sha256、elapsed_minutes、research_read_minutes、external_queries 和 design_tokens。每名评审包含 reviewer_id、scored_before_unblinding、两个 Arm 的七维 scores、blocking_issues、unsupported_assumptions、review_evidence。

工具只读取本地原始文件，拒绝路径越界、符号链接、重复 JSON 键、非有限数字、缺失或变更的 SHA-256、原题非 PDF、缺失附件、不同模型或提示、资源预算越界、单评委或未声明先盲评。三题缺任意一题返回 not_ready，不计算差异；三题完整则返回 descriptive_only、逐轴差异和成本。原文真实性、盲评独立性、语义评分正确性与因果归因仍属人工审查范围。

CI 的成对数据为 **synthetic controls**，只验证脚本逻辑。不得把模拟分数当成历史赛题实测，更不得将工具的 descriptive_only 视为模型批准或发布资格。该工具不写 Project State、框架、工作簿、论文或官方提交包。

## P6 最终结束条件

1. 从官方来源取得三份完整题面及适用附件，校验原始字节和来源。
2. 对每题实际形成可追溯、隔离的基线和增强两套完整设计；保留预算、搜索记录和产物摘要。
3. 两位以上独立评审针对三题的两套设计进行盲评，保留明确的审题、公式和来源质询锚点。
4. 运行脚本生成真实成对比较并独立复核来源与数学；报告效果、退化、时间成本及 P5 是否值得新增 Gate。
5. 核对现有 SIB、Human Approval、Project State、03A/03B、Figure、Writing、数值验收与最终 Head CI 不退化。

**本 P6-A PR 只交付“官方来源目录 + 可执行对照核验工具 + 拒绝虚报的安全边界”。尚无真实成对设计/评委数据，因此 P6 实测和完整发布尚未完成。**
