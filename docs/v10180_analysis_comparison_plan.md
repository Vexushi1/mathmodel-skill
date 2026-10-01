# mathmodel-skill：03B 多模型检验与同模型多算法检验详细修改计划

> 实施授权补记（2026-10-01）：用户已明确要求依据此计划开始修改仓库。本文件保留计划编写时的基线和设计；下文“本轮只写计划／未实施”均指原计划编写阶段。实际实现、接口细化及 GitHub 验收状态以本主题 PR 的当前 diff 和验收记录为准，计划中的候选字段不替代实现 Authority。

> 本文件是后续实施的上下文参考和范围约束。当前已完成内部结构阅读与计划编写，尚未实施源码修改，也未运行新增功能测试。

## 0. 用户目标、授权范围和使用方法

用户已确认优化方向。本轮明确要求：先读取 Skill 内部结构，针对原有结果深化分析编写详细修改计划 Markdown 文件。新增能力限于两个方面：

1. **多模型检验**：不同合理数学模型对同一题目对象进行真实求解，在共同评价口径下检验核心结论或模型选择。
2. **同模型多算法检验**：保持同一个数学模型，使用不同真实求解算法，检验结果对求解方法的依赖。

原有参数敏感性、场景压力、阈值、结构稳健性、异质性、误差分解和外样本稳定性继续保留。此次不重构所有检验类型，不要求每问都执行上述两类新检验。

本轮授权是**读取结构并写计划文件**。本文件中的字段、函数、专项表、协议扩展和测试均为拟议设计，不代表仓库已经具有这些实现。后续实施应先读取本文件，再刷新 GitHub main、治理文件和重叠 PR；若基线有变化，更新本文件中的受影响结论后再实施。不要依据聊天摘要直接开始改代码。

### 后续接手时先读

1. 本文件第 1—4 节：基线、真实结构、缺口和范围。
2. 第 5—12 节：两类检验的身份、计划、证据、验收和失效设计。
3. 第 13—16 节：文件改动清单、分阶段执行、验收和兼容要求。
4. 第 17 节：尚须在实施中核实的接口与停止条件。

## 1. 已核对的当前基线

| 项目 | 本轮读取事实 |
|---|---|
| 仓库 | `Vexushi1/mathmodel-skill` |
| 基线分支 | `main` |
| 基线提交 | `e2135a74ba83f08259c766e534b61e85467cd02e` |
| 基线 tree | `f7971ba483a14c09d1c6f184ebb0a6c6bc078ae3` |
| Skill 版本 | `10.17.1` |
| 读取日期 | `2026-10-01`，Asia/Shanghai |
| 当前 open PR | 本轮 GitHub 查询返回为空；实施前仍须刷新 |
| 当前工作簿 Schema | `2.3.1` |
| 当前 Project State Schema | `8.15.0` |
| 当前 User Execution Contract | `3.2.0` |
| 当前 Model Approval Contract | `1.1.0` |
| 正式主求解／分析回执 | 无辅助输入为 `1.1.0`；符合现行辅助输入合同的路径为 `1.2.0` |
| 项目级预处理回执 | `1.0.0` |
| 建议功能版本 | `10.18.0`，只是候选；实施时以届时 main 和治理规则确定 |

本轮使用的只读 checkout：

`C:\Users\Acer\Documents\Codex\2026-10-01\https-chatgpt-com-share-6abde7f6-a8c8\work\mathmodel-skill-audit`

本轮查到当前提交的 [HSK Skill CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36811464786) 和 [生成物工作流](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36811464798) 均为 completed/success。这仅是既有基线的远端状态，不能作为新功能验收证据。本轮没有执行 resolver、lint、unittest、MATLAB 或用户赛题代码。

实施前必须重新读取 current main 的 `core/bootstrap.yaml`、`SKILL_CHANGE_GOVERNANCE.md` 和 `AGENTS.md`。本计划遵循当前 GitHub-only 仓库验收规则；记忆中的旧本地验收流程不作为实施依据。

## 2. 实际内部结构与职责边界

下表中的路径均为仓库根相对路径，用于定位未来修改。链接固定到本轮提交，行号是当前定位点，未来版本可能变化。

| 层次 | 当前文件／入口 | 当前职责与此次关联 |
|---|---|---|
| 启动 | [core/bootstrap.yaml](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/core/bootstrap.yaml) | 最小启动、Authority 指针；不应在入口重抄业务规则 |
| 路由 | [core/workflow_router.yaml:308](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/core/workflow_router.yaml#L308) | `result_analysis` 和 `validation` 已进入 03B，已有 model_approval/code_delivery 等门 |
| 模块图 | [core/module_manifest.yaml:160](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/core/module_manifest.yaml#L160) | 03B 条件启用，消费 accepted 主工作簿和当前框架 |
| 模型设计 | [modules/02_model_design.md:104](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/modules/02_model_design.md#L104) | `0..N` Comparison Envelope；有比较目的和证据阶段要求 |
| 主数值验证 | [core/numerical_verification_contract.yaml:25](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/core/numerical_verification_contract.yaml#L25) | 仅判断当前计算内在数值资格；两类新对照不转移到主质量门 |
| 03B 业务 Authority | [modules/03_result_analysis.md:21](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/modules/03_result_analysis.md#L21) | Analysis Necessity Gate、真实后置分析、support/modify/reject、回退 |
| 执行 Authority | [core/user_execution_contract.yaml:209](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/core/user_execution_contract.yaml#L209) | 用户 full-fidelity 执行、项目唯一 backend、配置／回执／源码 bundle／主工作簿身份 |
| 工作簿 Authority | [core/workbook_schema.yaml:206](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/core/workbook_schema.yaml#L206) | 03B 表名、列、至少一项实质表、MATLAB 交接 |
| 机器状态 | [core/project_state.schema.yaml:1776](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/core/project_state.schema.yaml#L1776) | analysis status、methods、requirement reason、dispositions；尚无逐项比较清单 |
| 主模型身份 | [scripts/semantic_identity.py:24](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/scripts/semantic_identity.py#L24) | 主 SIB 包含模型数学字段及 `algorithm_semantics`；不能简单用整个 SIB hash 判断“模型是否相同” |
| 主语义文本范围 | [scripts/semantic_identity.py:73](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/scripts/semantic_identity.py#L73) | `#### 当前模型口径` 到 `#### 结果摘要`；新增比较记录应放在这一范围之外 |
| 模型批准 | [core/model_approval_contract.yaml](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/core/model_approval_contract.yaml) | 当前主要绑定主模型；比较范围批准需要窄范围补充定义 |
| 分析前置 | [scripts/analysis_prerequisites.py:115](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/scripts/analysis_prerequisites.py#L115) | 主 accepted 资格、分析激活、数据／源码／输入前提 |
| 代码交付 | [scripts/validate_code_delivery.py:357](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/scripts/validate_code_delivery.py#L357) | 静态读取 RUN_CONFIG、检查真实 bundle、登记已交付实现 |
| 回执验收 | [scripts/validate_user_execution.py:461](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/scripts/validate_user_execution.py#L461) | 核对候选工作簿、配置、执行来源，最后推进接受状态 |
| 当前分析判定 | [scripts/validate_user_execution.py:389](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/scripts/validate_user_execution.py#L389) | 主要依据汇总表的“是否保持”；新比较分支须增加证据覆盖与处置判断 |
| Runtime 资格 | [core/runtime_assurance_contract.yaml:152](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/core/runtime_assurance_contract.yaml#L152) | accepted-analysis 与 reasoned not_required 共同决定下游 validated_results |
| 项目同步 | [scripts/sync_project.py:1306](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/scripts/sync_project.py#L1306) | 发现 artifact、核验来源、传播 stale；不能生成比较结果或自填 PASS |
| 失效 | [core/state_transition_contract.yaml:236](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/core/state_transition_contract.yaml#L236) | 已有 analysis 输入／代码变更与分析 profile，可保持主结果 |
| 事务 | [scripts/project_transaction.py:918](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/scripts/project_transaction.py#L918) | generation、read-set、原子写入；此次复用，不另造 writer |
| Python IO | [templates/code/hsk_pipeline/workbook_validation.py:259](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/templates/code/hsk_pipeline/workbook_validation.py#L259) | 当前拒绝未登记分析表，至少一项检查不等于逐项计划覆盖 |
| Python Schema 投影 | [templates/code/hsk_pipeline/result_io.py:119](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/templates/code/hsk_pipeline/result_io.py#L119) | 用户项目无仓库 Schema 时有 fallback；必须同步新表投影 |
| Python 03B 模式 | [templates/code/starter/README.md:40](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/templates/code/starter/README.md#L40) | 当前是生成指导；不存在现成的 Python `q1_analysis.py` 模板 |
| MATLAB 03B 模板 | [templates/code/matlab/q1_analysis.m](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/templates/code/matlab/q1_analysis.m) | 当前真实系数敏感性示例、1.1 回执、主簿保护 |
| 当前框架模板 | [templates/model/model_paper_framework.md:288](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/templates/model/model_paper_framework.md#L288) | Comparator 人可读表；需关联稳定检验 ID |
| compact/full | [scripts/instantiate_model_paper_framework.py:151](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/scripts/instantiate_model_paper_framework.py#L151) | 从一个 canonical 模板按 H2 投影，没有独立 compact 模板 |
| 证据选取／运算 | [scripts/claim_workbook.py](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/scripts/claim_workbook.py)、[scripts/claim_values.py](https://github.com/Vexushi1/mathmodel-skill/blob/e2135a74ba83f08259c766e534b61e85467cd02e/scripts/claim_values.py) | 可复用 captured-bytes、精确 selector、有限 Decimal 运算，不能绕过来源资格 |

### 实际调用链

```text
bootstrap → router → resolve_runtime → reading_plan / ordered pre_delivery_gates
                                      │
Module 02：主模型 + 按需比较候选 → Challenge / Human Approval
                                      │
03A 用户执行 → receipt + numerical verification → accepted 主工作簿
                                      │
03B Analysis Necessity Gate → 具体结果分析计划 → code delivery
                                      │
用户 full-fidelity 执行独立 analysis 入口 → 03B 工作簿 + RUN_RECEIPT
                                      │
validate_user_execution → state / stale / disposition
                                      │
runtime assurance + project sync → 已验收证据 → 图表 / 写作 / 终审
```

新增比较能力应接进这条链，不新建独立求解主链或另一套交付门。

## 3. 当前缺口：哪些已经有，哪些需要补

### 3.1 已有能力

- Module 02 已允许 baseline、高保真、消融、替代结构、独立 solver 等 comparator，数量为 `0..N`。
- 03B 已规定重大风险和超出主计算世界的 claim 必须处理；允许有理由的 `not_required`。
- 工作簿已有“算法一致性”和“结构稳健性”。
- 已有 `support / modify / reject`、核心否证回退、artifact 身份、源码闭包和 typed stale。
- 预测等 task Pack 已有基准／替代模型比较要求。

### 3.2 需要补的实际接口

1. Comparator 登记缺少到具体检验计划、真实证据和处置的稳定逐项关联。
2. “至少一项实质分析表”不能检查必要模型对照是否被另一张敏感性表替代。
3. 旧“算法一致性”要求 `算法 / 重复编号 / 目标值 / 是否可行`，不适合所有预测、评价和仿真问题。
4. 缺少跨题型的共同评价口径及模型／算法对象身份。
5. 当前 Boolean 汇总容易将有效负结果与技术失败混在一起。
6. 新计划缺少冻结身份，事后删项或改判据可能没有针对性的绑定检查。
7. 主 SIB 包含算法语义，新增比较对象不能塞入主身份，也不能用主 SIB 全 hash 相等直接表示“同一数学模型”。

本轮补接口和两类执行模式，不重复创建现有敏感性、结构稳健性和否证规则。

## 4. 范围与硬边界

### 本轮要做

- 为 03B 增加 `model_comparison` 和 `algorithm_comparison` 两种明确检验类型。
- 建立必要比较项的设计—计划—真实运行—证据—处置覆盖检查。
- 增加两张跨题型专项证据表，Python/MATLAB 使用同一合同。
- 在当前交付、回执、Runtime、同步和下游消费入口检查当前资格。
- 保证新增比较范围不会无依据改变主 SIB 或取消未变化的主结果。
- 为完整负结果定义合理处理，并保留核心否证回退。

### 本轮不做

- 不强制每问至少两个模型，也不强制两类新检验同时执行。
- 不把原有全部分析方法迁移为新的注册系统。
- 不改变项目根一次选择 Python/MATLAB 的政策，不做逐检验混合后端。
- 不改主 SIB schema、原主数值质量门或数值精度要求。
- 不重命名既有 `result_analysis_*`、脚本入口和 `问题X结果深化分析.xlsx`。
- 不新增独立模型检验 Gate、独立用户回执文件或另一套全局状态机。
- 不重构 B1/B2、C 回执、Case Memory、论文固定骨架或图形 Authority。
- 不运行真实赛题、不替用户执行数值代码、不自动迁移历史项目。

## 5. 两类新增检验的业务定义

| 类型 | 数学对象要求 | 至少需要的真实对象 | 可支持的主张 |
|---|---|---|---|
| `model_comparison` | 同一题目对象和共同评价问题；模型假设、机制、关系式、目标或约束有实质差异 | 一个主模型 + 至少一个合理对照模型；每个被使用模型均有合法数值结果 | 指定模型选择下的差异、改进、依赖、适用边界或交叉佐证 |
| `algorithm_comparison` | 同一个原始数学模型；目标、硬约束、数据口径和现实参数保持一致 | 至少两个不同求解方法的真实执行证据；可复用 accepted 主算法结果作基准 | 对指定算法、搜索／数值方法的依赖，以及目标、决策、可行性、成本等差异 |

### 必须明确的区别

- 同一 MILP 用不同求解算法，是算法检验；改目标或硬约束后再求解，是模型检验。
- 同一 PDE 改数值离散或积分方法，一般是求解方法变化；增删物理机制才是模型变化。
- 同一算法换 seed、初值、容差，不单独计为多算法；仍按原分析类型处理。
- 不同模型名字、不同函数名或重复执行同一代码，不构成多模型／多算法证据。
- 可逆等价变换和已证明等价的降维不自动构成不同模型。算法使用 reformulation 时必须保留到原模型的映射和原模型回算。
- 对照角色 `simple_baseline / high_fidelity / independent_solver / ablation` 是目的描述，不替代上述检验类型判断。
- “高保真”若仅指同一方程的离散精度，仍遵守 03A 数值充分性边界；增加机制的高保真对照才可能进入模型检验。
- 两模型一致不能证明现实正确；差异本身也不能自动否决主模型。按具体比较问题和证据处置。

### 必要性

沿用现有 Analysis Necessity Gate。明确题目／用户要求、material residual risk、需要比较证据的正文主张，或主结果暴露出的实质风险，才将相应比较项设为 `required`。

探索候选设为 `exploratory`，未执行可以不阻塞当前答案，但不能写成已经验证。一旦被用于正式比较主张或关闭核心风险，必须转为 `required`。

存在 current required 比较项时，不允许整体 `not_required`。撤销附加 claim 的专属比较可以记录理由；题目／用户的明确要求和仍存在的核心风险不能因算不出来而撤销。

## 6. 目标工作流：先候选规范，后真实分析计划

1. Module 02 根据题意和主模型登记按需比较候选、具体 comparison question 和预期信息价值。
2. 已足够明确的比较数学／算法范围随 Model Approval Brief 一次审查；不能提前生成已完成的正式结果分析计划或比较结果。
3. 03A 按原流程执行和验收。只有主工作簿 accepted 后，才建立当前 03B 的具体检验项、共同评价和冻结判据。
4. 如真实主结果发现新的必要比较对象，集中补充审查相应范围；主模型未变时保持主审批和主 accepted。
5. analysis 入口只生成必要的比较分支，继承项目 backend、数据事实源、accepted 主簿及声明源码 helper。
6. 交付时冻结比较计划身份；用户按 full-fidelity 执行，写出真实逐模型／逐算法／逐实例／逐重复／逐指标记录。
7. 回执先核对来源，再检查每个 required ID 的真实覆盖和处置，最后更新状态。
8. 图表、论文和终审只消费当前合法证据；未完成的必要比较不能以格式通过进入下游。

独立 analysis 入口不调用主入口重新算基准，不覆盖主工作簿。基准若直接来自当前 accepted 主簿，应引用真实字段；确需补充同模型重复实验时在 analysis 内登记其目的、输入及实际子运行，不能冒充原主运行。

## 7. 身份和登记设计

### 7.1 一个比较清单，保留现有总体状态

建议在每问机器状态新增可选对象 `analysis_comparison`。它只服务两类新比较，不替代其他旧分析方法。激活后使用严格 schema，不接受部分字段、未知版本或仅写 passed 的自报。

拟议结构如下，省略的 hash 和 selector 是实施时必须计算／填写的内容，不是合法交付占位符：

```yaml
subproblems:
  Q1:
    analysis_methods: [多模型检验, 同模型多算法检验]
    analysis_comparison:
      protocol_version: 1.0.0
      scope_ref: Q1-analysis-comparison-scope
      scope_sha256: <validated-and-approved-scope-digest>
      baseline_semantic_identity_hash: <current-approved-main-SIB-digest>
      approval_binding: <existing-approval-authority-scoped-record>
      checks:
        - id: CMP-Q1-01
          kind: model_comparison
          requirement: required
          requirement_source: <prompt/user/material-risk/claim-anchor>
          question: <specific-comparison-question>
          target_claim: <current-claim-reference>
          baseline_ref: MAIN-Q1
          candidate_refs: [MODEL-Q1-02]
          comparison_protocol_ref: EVAL-Q1-01
          criterion: <predeclared-bounded-criterion>
          evidence_refs: <expected-sheet-row-key-column-selectors>
        - id: CMP-Q1-02
          kind: algorithm_comparison
          requirement: required
          requirement_source: <anchor>
          question: <specific-algorithm-question>
          target_claim: <current-claim-reference>
          baseline_ref: ALGO-Q1-01
          candidate_refs: [ALGO-Q1-02]
          comparison_protocol_ref: EVAL-Q1-02
          criterion: <predeclared-bounded-criterion>
          evidence_refs: <expected-selectors>
```

`checks` 是唯一的机器覆盖清单；框架里的表是其人可读投影。数学规范保存在框架，state 保存引用、绑定和机器状态。输出结果和处置关联到现有 `analysis_evidence_dispositions`；不再为每项保存另一份总体 passed/failed。

每项最终应能关联 `disposition_ref`，以及必要时的具体撤销理由和关联主张动作。运行后处置和撤销审计不能参与运行前冻结计划的 hash。撤销导致 current 计划改变时，必须使旧分析资格失效，不能用删除一行规避历史承诺。

### 7.2 比较规范放在主语义范围之外

在 canonical 框架每问 `#### 结果摘要` 之后增加 `#### 03B比较计划与证据`，包含比较对象定义、共同评价、检验 ID、当前证据和处置导航。

模型比较对象用独立的 analysis marker／ID 命名，不能重复主 `HSK_SEMANTIC_IDENTITY_BEGIN/END Qn`，不能放进主 SIB `extensions`。复用现有数学字段校验和规范化的公开纯函数，不复制一套主身份实现。

框架新增内容位于“各问模型与结果”共用 H2 内，compact/full 都应保留。通常无需改实例化投影算法，只补模板与投影回归。

### 7.3 “同模型”不能按完整主 SIB hash 比较

现有主 SIB 包含 `algorithm_semantics`。因此算法不同可能改变完整 SIB 的结构身份；直接要求两个完整 SIB hash 相等，会把合法算法对照误判为换模型。

建议在比较 helper 内计算一个**仅用于本次比较的数学模型投影身份**：先通过现有完整 SIB 校验，保留 `schema_version / question / research_object / data_scope / variables / parameters / assumptions / objective / constraints / preprocessing_decision / dependencies` 以及存在时的完整 `extensions`。对 `algorithm_semantics` 不能整字段无条件排除：其中可能承载缩域、数学判据、离散近似、原模型回算或输出定义。只有被审查为纯求解实现的内容才能排除；具有模型含义的内容应作为明确、可追溯的保留项加入投影。按 analysis comparison 协议版本规范化并计算摘要。

保留项与纯实现项的划分必须在比较规范中显式登记，并进入 scope 审查；机器不能按字段名猜测其数学作用。无法完整划分、某项仍有数学含义争议时报告 `review_required`，不授予同模型资格。算法专属扩展应放入比较方法规范，不能悄悄删除 `extensions` 内容。

这不是新的全局 `semantic_identity_hash`，不替代主批准身份。完整主 hash 仍绑定基准；数学投影只辅助检查比较对象是否声明为同一模型。

算法对照的每个算法引用同一份主数学规范，方法定义单独记录。算法重写模型时必须登记等价映射与原模型评价，不另造改了约束的“同模型”。模型对照若两边规范投影完全相同，则不能据此自称不同模型；不同文字规范是否数学等价，仍需要审查。

### 7.4 算法身份

方法定义记录方法原理、更新／搜索规则、停止语义和实现 anchor。seed、初值、普通重复编号、运行环境单独作为运行条件；不能仅因这些条件不同生成“新算法”。

机器可以发现相同规范重复登记或引用缺失，不能从算法名字判断算法独立性，也不能自动证明模型数学等价或正确。

## 8. 比较范围审查与批准

该部分需要对现有 Model Approval Authority 作窄范围补充，不建立新的比较 Gate。

- 基准主模型的 current = validated = approved identity 必须继续成立。
- 比较范围由基准主身份、候选数学／算法规范、改变与保持的条件、拟检验问题以及共用评价范围形成 scope digest。
- scope digest 不包含尚未存在的主结果值、accepted 主簿 hash 或具体输出行位置，因此可以在 Module 02 随主 Brief 审查。
- 具体实验判据和 selectors 在 accepted 后、analysis 代码交付前冻结为 plan digest；其设计应在已经审查的比较范围内。
- Model Reviewer 和 Devil's Advocate 对比较对象闭合性、实质差异、共同评价、信息价值和共享缺陷作明确审查；用户的范围批准绑定当前 scope digest。
- 如新增模型或算法超出批准范围，复用同一 Authority 补充审查和明确范围批准；不能用主 accepted 或仓库修改批准替代具体项目的比较范围批准。
- 比较 scope 变化只使比较批准及分析链失效；主模型确实改变时才走原主语义修订、重新批准和 stale。

当前 `validate_model_approval.py::validate_question()` 和 `validate_state()` 只有小问范围及主模型批准参数，没有比较 scope 消费接口。实施时需要新增窄范围的分析比较批准消费函数，或由共享 helper 提供范围资格，再接入现有 Authority、validator 和 gate；不能把本计划的 scope 写成既有功能，也不能让状态自报 `approved` 成为证明。model_approval gate 名称和顺序继续由 resolver 管理。

当前可选 C 回执消费把 Model Challenge 对象固定为 `Qn:model`。只有项目显式采用新比较审查对象时，才扩展相同 gate 内的对象／规范 hash 覆盖；不无条件使旧 C 回执失效，也不强制所有项目启用 C policy。若实施阶段不能正确绑定新增对象，该比较范围应报告未批准，不得伪装复用旧主回执。

## 9. 工作簿设计：新增两张通用长表

### 9.1 保留原表

原“算法一致性”和“结构稳健性”的表名、必需列及历史读取继续保留。不能给旧目标值列塞 0，也不能把 RMSE 更名为优化目标值来满足格式。

建议新增正式表名：

- `多模型检验`
- `同模型多算法检验`

使用“一项检验 × 一个比较对象 × 一个实例／场景／重复 × 一个指标”一行的长表。每行使用唯一 `记录键`，避免多指标和重复样本被合并成不可复查的摘要。

### 9.2 新表字段

| 表 | 必需列建议 | 条件／可选列建议 |
|---|---|---|
| 多模型检验 | 检验ID、记录键、主模型ID、对照模型ID、评价协议ID、实例或场景、指标、单位、主模型数值、对照模型数值、差异类型、差异、判据ID、判定 | 模型族、对照角色、结构差异、数据划分、重复编号、随机种子、可行性、残差、gap、运行时间、求解器及版本、停止原因、子运行ID、源码／证据位置 |
| 同模型多算法检验 | 检验ID、记录键、模型ID、基准算法ID、对照算法ID、评价协议ID、实例或场景、重复编号、指标、单位、基准数值、对照数值、差异类型、差异、判据ID、判定 | seed、初值、计算预算、可行性、残差、gap、决策差异、运行时间、求解器版本、停止原因、子运行ID、源码／证据位置 |

无量纲指标也显式使用合同约定的单位标签，不能将单位缺失默认成一致。具体可行性、残差、gap、时间等是否必需，由该检验的评价协议按题型和 claim 声明；不让所有题目填写所有指标。

需要新模型／算法真实子运行时，应有可复查的执行记录和细粒度底层结果。可在这两张表中提供实例／重复／指标记录，不默认增设用户运行日志、配置或报告文件。

### 9.3 设计与汇总的关联

- 在 `分析设计` 为新类型增加检验 ID、比较类型、对象引用和判据引用；旧必需列保持兼容。
- 在 `结论稳定性汇总` 为新类型增加检验 ID／Evidence ID／处置关联；新协议不再将所有“是否保持=False”解释成技术失败。
- `required model_comparison` 必须有对应模型证据；`required algorithm_comparison` 必须有对应算法证据。
- 单纯“至少一张实质表”只作为旧基础结构门，不再代表两类新检验的覆盖完成。
- 每项 required 都必须有准确 evidence selector 和对应 disposition，不能仅有表头、任意行或汇总文字。

### 9.4 共同评价协议

协议至少声明题目对象、输入来源与时间因果、实例集合、输出映射、指标定义／方向／单位、允许改变和必须保持的条件、判定准则及来源。

算法检验应在共同原模型下核对可行性、目标／误差及必要结构结果；仅比较目标值相近，不自动表示决策相同或全局最优。

模型检验在不同模型有不同自然输出或目标时，使用预先定义的共同现实指标／共同输出映射；不直接相减不可比的目标函数。同一数据事实源允许已声明、合法且无泄漏的模型专属变换。

性能优劣主张还需要记录适用的硬件、预算、停止条件、重复与随机性；不是所有比较都必须强制相同耗时。

## 10. 配置、回执和计划冻结

### 10.1 复用既有回执版本

不整体升级 RUN_RECEIPT。保留 preprocessing 1.0、primary/analysis 1.1、合法辅助输入 1.2 的现行语义。

为选用新比较能力的 analysis 添加独立的小型协议标记，拟定：

```text
analysis_comparison_protocol_version = "1.0.0"
analysis_comparison_plan_sha256 = <canonical frozen plan digest>
```

RUN_CONFIG 和现有 `运行配置(项目, 值)` 中的 RUN_RECEIPT 回显相同字段。只允许 analysis 使用；不加入所有阶段的通用必需字段。

**旧读取工具限制**：保留基础 receipt 1.1/1.2 并增加独立标记时，旧 `v10.17.1` 校验器不保证拒绝额外字段，也不具有本轮比较覆盖语义。因此，所有新比较的代码交付、候选验收和正式下游资格检查必须使用明确支持该扩展的版本；项目交接应登记最低支持版本／能力。协议未知或部分字段失败关闭的保证属于实现本计划后的读取器，不是对未修改旧工具的追溯保证。部署与回滚前须检查工具能力，禁止用旧 Boolean 分析验收代替新比较验收。

协议语义归 `core/user_execution_contract.yaml`，业务检验规则归 Module 03B，列结构归 workbook Schema。`scripts/execution_protocol.py` 实现字段和版本检查，不能成为第二个 Authority。

### 10.2 冻结内容

plan digest 包含：新协议版本、小问、基准主语义身份、比较 scope digest、按 ID 规范排序的检验类型／必要性来源／目标主张／对象引用／共同评价／判据／预期 evidence selectors。

不包含：运行后结果值、disposition、action 完成状态、论文排版位置、actual workbook hash、入口自身 bundle hash。主簿身份继续使用现有 `primary_workbook_sha256`，代码与数据身份继续用原 bundle／输入协议，避免循环摘要。

验收时重新计算 current 计划，核对已交付源码配置和返回回执中的冻结摘要。源码、state 或回执任一激活新协议，就要求完整一致；未知版本、部分字段、删掉一端标记、缺失必要项均不能退回旧兼容分支。

新两类方法／新证据表已经出现但没有协议标记时也要报错。仅有真正已经 accepted、passed 且同文件 hash 的历史分析，才保留明确只读兼容。

### 10.3 多个子运行与源码闭包

- 顶层仍只有一个 RUN_CONFIG。
- `solver / tolerance / iteration_or_time_limit` 保持当前标量合同；各子模型／算法的实际设置和停止原因写到专项证据，不能将全局字段改成列表。
- 多模型、多个算法都继承同一个项目 backend。
- helper 继续通过 `code_dependencies` 和 stage bundle 登记；运行前绑定、写出前复核。
- 不让用户项目代码依赖 Skill 安装目录。复制到用户项目的实际支持源码要纳入闭包。
- 同一 dataset／evaluation helper 可以合理共享；需要独立模型解释力时，必须说明共享与独立部分，不把复制主核心改名当作独立检验。

## 11. 共享检查器和函数级接入

### 11.1 拟新增共享实现

建议新增 `scripts/analysis_comparison.py`，只负责两类新增比较。它不导入 runtime 的资格提升函数、不导入项目 writer、不执行用户数值脚本。

```python
inspect_plan(entry, *, question, specs, config=None, receipt=None)
canonical_plan(plan, *, question, baseline_identity, scope_identity)
inspect_evidence(plan, *, primary_bytes, analysis_bytes,
                 dispositions, workbook_contract, comparison_rules)
```

输出至少包含 `issues / covered_ids / uncovered_required_ids / computed_metrics / criterion_results / disposition_impacts`。`issues` 表示缺失、歧义、身份失效、口径冲突、错误算术等技术／资格问题。`criterion_met=False` 是实验结果，应交给处置逻辑，不能直接混入技术错误。

检查器使用调用者捕获的字节和 state；捕获、资格判断、read-set 及事务写入由当前控制面负责。不能缓存 PASS 或 accepted 资格。

### 11.2 精确接入位置

| 文件／函数 | 修改内容 |
|---|---|
| `analysis_prerequisites.py::analysis_issues()`，当前 115—153 | 检查 registry、范围批准及 required/not_required；保留当前主资格和历史同 hash 只读例外 |
| `validate_model_approval.py::validate_question()/validate_state()` | 根据分析 scope 消费比较批准绑定；保持原主模型批准语义 |
| `validate_code_delivery.py::validate_script()`，当前 357 起 | analysis 协议、current plan digest、合法对象和预期 selectors；不要求结果已经存在 |
| `validate_code_delivery.py::update_state()`，当前 588—795 | 捕获与复核比较来源，变更时失效 analysis，原事务提交 |
| `validate_user_execution.py::validate_run_receipt_binding()`，当前 256—310 | analysis 条件字段绑定，不影响 primary/preprocessing |
| `validate_user_execution.py::validate_one()`，当前 461—697 | 既有 receipt/bundle/input/upstream 检查后、写 accepted 前检查候选 bytes 和逐项证据 |
| `validate_user_execution.py::analysis_passed()`，当前 389—411 | 新协议按覆盖和 disposition 判定；旧协议保留原行为 |
| `validate_project_state.py` | 检查注册项唯一性、批准／计划绑定、required 与 not_required 冲突、非法自报完成 |
| `runtime_assurance.py::hydrate_project_context()`，当前 analysis 资格 966—995 | 当前合法来源后再核对新计划／覆盖；失败不能提升 accepted-analysis |
| 同函数 not_required 分支，当前 998—1036 | current required 项存在时，非空 reason 也不能提升 validated_results |
| `project_snapshot.py::_validate_workbook()`／analysis 快照 | 传递当前两类方法和新计划要求；不按文件存在认定完成 |
| `sync_project.py::synchronize()` | 将计划／规范／证据 observations 加入 question snapshot 和 read-set；同步只传播失效 |
| `sync_project.py::_formal_state_issues()` | 调用相同覆盖检查，避免再次复制另一份规则 |
| `state_transitions.py` | 通过已声明 analysis profile 处理计划变化和否证；不在纯状态引擎内读工作簿 |

### 11.3 候选验收不能调用 accepted-analysis 资格器验收自身

`claim_sources.Sources.qualify()` 通过 runtime 要求来源已经 accepted。直接用它验收候选 analysis 工作簿，会产生循环；先写 accepted 再检查则绕过原门。

正确顺序是：既有回执协调器先验证候选代码、输入、主簿和回执来源；共享检查器从同一份 captured bytes 复用 `claim_workbook.Workbook.select()` 的精确选取和 `claim_values.derive()` 的有限运算；全部条件满足后，原协调器最后提交接受状态。

专项表中的“主模型数值／基准数值”必须逐项核对准确的 accepted-primary selector；若基准来自补充运行，则核对合法登记的 03B 基准子运行和对应底层记录。专项表只承载比较展示，不成为另一份基准事实源。即使把伪造基准与差异一起改得算术一致，也必须因来源值不一致而失败。

复用低层组件不等于启用 B2 policy。论文阶段仍按原 B1/B2 规则消费 accepted 来源，不扩大证据合法性范围。

有限运算至少处理已声明 difference／relative change／improvement；零分母、百分比与百分点、单位、方向、NaN/Inf、字符串数字和不可用公式缓存都不能自动补齐或默认为合法。输出真实 numeric literal，保留底层数值。

### 11.4 read-set 保护不能依赖 A2 开关

当前代码交付／回执 writer 的部分严格快照保护受 A2 激活控制。新比较协议必须独立触发 guarded-write，而不是挂到 A2 分支里。

实际读到的 state、框架比较规范、analysis 入口/helper、输入、accepted 主簿、候选分析簿和相关 Authority 都应纳入相同 read-set。读取前捕获，读取后及提交前复核，禁止读取结束后才补抓摘要。

复用 `ProjectStateSnapshot.capture` 和 `commit_project_state(... expected_file_hashes=..., validators=...)`。generation 相同但字节变化也必须拒绝。只读 inspector 不自动恢复 prepared journal、不持 writer lock、不写项目。

## 12. 完成、负结果与 stale

### 12.1 判断表

| 情况 | 检验是否已完成 | 整体处理 |
|---|---|---|
| required 对照缺失、空数据、子运行失败、来源失效、差值错误 | 否 | 验收失败／保持未完成，不伪装语义 reject |
| 有效证据支持目标主张 | 是 | support；在声明范围内可用 |
| 有效证据要求缩小范围、调整区间／排名／措辞 | 是 | modify；相关主张和正文处理完成前保持 stale |
| 有效证据否定附加主张 | 是 | reject/auxiliary_wording；删除或重写该 claim，不默认整题重算 |
| 有效证据否定核心答案 | 是，但当前成果需回退 | redo_required，按原 solve_validate 路径 |
| 有效证据否定主模型有效性 | 是，但当前成果需回退 | redo_required，按原 model_design 路径 |
| exploratory 未执行 | 不作为必要覆盖欠项 | 不能声称已经比较 |

“证据已核验”与“当前成果具有 accepted-analysis／validated_results 资格”必须分开。核心否证时保留证据，整体仍不能被提升为合法当前成果。

### 12.2 比较计划与主语义分开失效

建议新增窄范围 `analysis_comparison_plan_changed` 事件，复用 `analysis_result` profile。比较数学 scope 改变时还清除该范围批准绑定；只改具体实验计划时使分析代码／证据及真实下游失效。

新增比较对象、方法、判据或 selectors，不自动触发 `semantic_identity_changed`；保持未变的主 approved identity、主 quality 和主 accepted 工作簿。若比较发现主模型需要改变，才按原语义事件和依赖传播。

现有结构化核心否证事件的 caller_scope 部分限定 B2 policy。新比较协议使用这些回退语义前，必须在同一个 state-transition Authority 明确扩展合法 caller scope，并同步 runtime 识别；不能从非 B2 分支擅自调用，也不另造回退算法。

主数据、主代码、主模型或 accepted 主簿变化时，仍按原规则使相关比较计划／证据失效。其他独立问题不应被无差别失效。

### 12.3 合法撤销

撤销必须保留检验 ID、原理由、撤销理由及关联 claim／语义替代动作。技术失败、预算不足和“不想再算”不能当作撤销依据。

明确要求未完成或核心风险仍存在时，不允许撤销使成果合格。辅助 claim 被删除后，其专属检验可退出；主语义版本被替代时，旧比较退休，新版本重新判断必要性。

## 13. 文件改动清单与责任

### A. 必改业务和字段

| 文件 | 具体改动 |
|---|---|
| `modules/03_result_analysis.md` | 两类业务定义、条件启用、必要项覆盖、共同评价、真实子运行、处置与完成条件；作为业务 Authority |
| `modules/02_model_design.md` | Comparison Envelope 关联检验 ID／范围引用；保留 0..N，候选不伪装已执行 |
| `core/workbook_schema.yaml` | 注册两张新表、条件必需列、设计／汇总关联；建议兼容 minor 版本 |
| `core/project_state.schema.yaml` | 可选 strict analysis_comparison 对象、引用和绑定；整体旧 status 不改 |
| `core/user_execution_contract.yaml` | analysis 专属协议标记和 plan digest；现有回执版本不整体升级 |
| `core/model_approval_contract.yaml` | 比较范围批准与主身份隔离的窄范围规则 |
| `core/state_transition_contract.yaml` | 分析计划变更事件及合法核心否证 caller scope |
| `core/runtime_assurance_contract.yaml` | 新激活项目的当前比较资格及 not_required 冲突条件 |

### B. 必改控制面／新增共享实现

`scripts/analysis_comparison.py` 为拟新增文件。接入现有 `analysis_prerequisites.py`、`validate_model_approval.py`、`validate_model_paper_framework.py`、`validate_project_state.py`、`validate_code_delivery.py`、`validate_user_execution.py`、`runtime_assurance.py`、`project_snapshot.py`、`sync_project.py`、`execution_protocol.py` 和必要的 `state_transitions.py` 分支。

`semantic_identity.py` 仅在确需公开复用规范化函数时最小改动；主 SIB schema 和 hash 语义不改。`project_transaction.py`、`run_config_parser.py`、`stage_code.py`、`stage_inputs.py` 原算法原则上复用，先用新增回归核查，不把“必查”当成“必改”。

### C. 模板和 IO

| 文件 | 具体改动 |
|---|---|
| `templates/model/model_paper_framework.md` | 主语义范围之外增加比较规范／清单／证据导航；保留现有 Envelope |
| `templates/model/model_approval_section.md` | Brief 展示范围、信息价值和共享／独立部分 |
| `templates/review/result_analysis_check.md` | 两类逐项审查、负结果处理、真实源和可比性；至少一项不能替代必要项 |
| `templates/code/hsk_pipeline/workbook_validation.py` | 新表、条件字段、非空／键／有限数；支持调用方传入比较方法／计划 |
| `templates/code/hsk_pipeline/result_io.py` | 外层参数传递和 fallback Schema 投影同步；不在 writer 发明 accepted |
| `templates/code/starter/README.md` | Python 03B 实例化说明和两类证据生成要求 |
| `templates/code/matlab/README.md` | MATLAB 同合同、独立入口、子运行记录和协议回显 |
| Python／MATLAB 比较示例，拟新增 | 各实现同一个小型可核验案例，输出真实两类证据；保留原敏感性示例 |

Python 目前没有现成 `q1_analysis.py`，不能写成修改一个不存在的模板。拟在 `templates/code/starter/analysis_comparison.py` 增加可实例化模式；MATLAB 拟在 `templates/code/matlab/analysis_comparison_example.m` 增加对应模式，实例化时仍生成项目规定的 `qX_analysis.m`。最终新增路径须符合索引／starter 扫描合同，并在实施第一阶段冻结。

历史 `main_pipeline.run_result_analysis_pipeline()` 只是兼容内存分析 API，不是当前独立 03B 入口。不能在该历史路径里实现新能力后宣称默认 assured 链完成。

### D. 必查消费者，按需要最小适配

- `core/workflow_router.yaml`、`core/module_manifest.yaml`：新增两类发现词、当前输入／输出描述，门名和 resolver-owned 顺序不另起一套。
- `core/output_contract.yaml`：仅更新 03B 能力摘要及当前框架段落合同，不改变用户文件名。
- `modules/04_figure_evidence.md`、`packs/artifact/figure.md`、`templates/matlab/hsk_read_result_workbooks.m`：新合法证据表导航／合同消费；不增加绘图求解。
- `core/writing_reasoning_contract.yaml`：两类比较各自的 claim strength 和范围；保留现有唯一写作证据 Authority。
- `modules/05_writing/paper_writing_protocol.md`、`core/writing_runtime_contract.yaml`：按当前证据消费，不改论文章节骨架，不将检验 ID／hash／状态词写入论文。
- `modules/06_review_delivery.md`、`templates/review/final_review_matrix.yaml`：检查必要比较覆盖和当前处置。
- `packs/task/optimization.md`、`packs/task/prediction.md`、`packs/task/statistics_ml.md`、`packs/task/mechanism.md`：澄清已有比较要求的类型与阶段，不全面重写 Packs。
- `packs/artifact/code.md`：新能力导航、配置和用户执行摘要。
- `core/model_code_conformance_contract.yaml`、`scripts/conformance_gate.py`、`scripts/model_code_conformance.py`：A2 启用时核查新分析 helper 的范围，不把 comparator 错当主模型变化；不扩成一般数学等价证明。
- `core/review_receipt_consumption_contract.yaml`、`scripts/review_receipt_consumption.py`、`scripts/review_receipts.py`：仅在显式比较审查 scope 激活时适配对象／规范绑定，保留旧 opt-in。
- `scripts/claim_sources.py`、`claim_workbook.py`、`claim_values.py`、`claim_consumption.py`：优先低层复用和来源资格回归，不另造 B2 消费链。
- `SKILL.md`、`skills/mathmodel-skill/SKILL.md`、`README.md`、`AGENTS.md`：只有确需能力发现或版本同步时更新精简摘要，不能重复业务规则。
- `.github/workflows/ci.yml`：开发 targeted 测试接线，以及新增 MATLAB 原生比较 smoke 的实际调用、报告检查、产物上传和成功断言；正式平台矩阵不扩张。

## 14. 分阶段实施顺序

### P0：合同与数学身份边界

交付：冻结类型、ID／引用、两张表、比较 scope 与 plan digest 的 canonical 字段、严格激活条件、同模型投影身份、负结果语义。

先改 Module 03B／Module 02／批准 Authority，再改 Schema 和 framework。明确哪些方法生成新协议，哪些旧分析保留原流程。加入必要的 schema／主身份／compact 投影测试。

验收重点：主 SIB 不被新增比较改变；算法检验保持同一数学对象；必要项的类型和退出规则可判定。

### P1：共享检查器和交付／候选验收

交付：共享纯 API、限定指标复算、代码静态交付、scope/plan/source binding、read-set、candidate 验收及 disposition。

不能先接 accepted-source 资格器绕过 candidate 来源验证；不能只增加新表和模板而遗漏覆盖检查。

验收重点：必要项缺失、类型误用、口径冲突、事后改判据、source drift 均能阻断；有效负结果有正确处理。

### P2：Runtime、同步、失效和下游

交付：current qualification、not_required 冲突、plan-change event、核心否证范围、framework 投影、受影响 claim／figure／paper stale。

验收重点：绕过代码交付直接手填 accepted 不能提升资格；添加比较不废未变主结果；核心否证正确回退。

### P3：Python/MATLAB 实例和消费者

交付：两端可真实实例化的 03B 模式、同一字段合同、细粒度输出和子运行记录；task Pack／绘图／写作／终审的最小适配。

验收重点：两端同一小案例有可独立核查的数值，主簿不改、helper 纳入 bundle、用户运行代码不依赖 Skill 安装路径。

### P4：冻结验收与收口

完成 targeted 远端验证后冻结 PR，GitHub 自动生成受管文件，核对最终 source head 和实际 checkout commit，执行正式完整验收。只有最终 head 通过后才进入合并；合并后复核 main。

是否发布新 release 由后续明确实施／发布授权确定。本文件不把计划编写当作发布授权。

## 15. 测试与正式验收方案

### 15.1 增量测试位置

| 测试面 | 建议复用／新增文件 |
|---|---|
| 新检查器、计划规范化、类型、指标与覆盖 | 拟新增 `tests/test_analysis_comparison.py` |
| 工作簿新表及历史列兼容 | `tests/test_result_io.py` |
| 代码／回执协议、plan hash、负结果 | `tests/test_user_execution_contract.py`、`tests/test_audit_analysis_boundaries.py` |
| 主数学身份与范围批准隔离 | `tests/test_v900_semantic_identity.py`、`tests/test_v900_semantic_identity_binding.py`、`tests/test_v711_model_approval_gate.py` |
| compact/full 和框架对齐 | `tests/test_p4_compact_framework.py`、`tests/test_framework_project_memory_contract.py` |
| required/not_required 与下游资格 | `tests/test_p7_conditional_analysis_appendix.py`、`tests/test_audit_runtime_qualification.py` |
| stale／核心否证／辅助主张 | `tests/test_v900_state_transitions.py`、`tests/test_b2b_claim_stale_transition.py`、`tests/test_b2b6_rejection_return.py` |
| 读取漂移和事务 | `tests/test_project_transaction_read_set.py`、`tests/test_sync_project_source_read_set.py`、`tests/test_project_state_read_snapshot.py` |
| 原生执行与源码 helper | `tests/test_solver_backend_end_to_end.py`、`tests/test_solver_backend_source_closure.py`、`tests/test_copied_support_source_closure.py` |
| MATLAB 真运行 | `tests/matlab/run_solver_backend_smoke.m`；拟新增两类比较原生 smoke |
| A2／C／B1/B2 兼容 | 现有 conformance、review receipt、claim workbook／values／consumption 专项测试 |
| 保留最小充分／无固定双路线 | `tests/test_v930_initial_modeling_core.py`、`tests/test_v930_domain_reduction_cues.py` |

测试应覆盖行为边界和真实回归，不堆仅复述字段定义的测试。开发 targeted 清单应加入新增测试；正式 discovery 必须包含新文件，不手工漏选。

### 15.2 必须覆盖的验收反例

| 编号 | 输入或行为 | 预期 |
|---|---|---|
| T01 | 必要多模型项已登记，但只有参数敏感性 | 拒绝覆盖验收 |
| T02 | 必要多算法项已登记，但只有结构／敏感性表 | 拒绝覆盖验收 |
| T03 | 两类均 required，但只完成其中一类 | 精确报告欠缺 ID |
| T04 | exploratory 未运行 | 不阻塞必要答案；不得声明已比较 |
| T05 | required 存在却整体 not_required | Runtime／state／sync 均不能提升资格 |
| T06 | 同算法仅换 seed、函数名或重复编号 | 不能计为两个算法 |
| T07 | 模型定义相同、只换算法却标多模型 | 机器发现相同声明时拒绝类型；不明数学等价交给审查 |
| T08 | 改了原目标／硬约束却标同模型算法检验 | 不授予同模型资格；等价 reformulation 须有映射和原模型回算 |
| T09 | 目标值接近但策略／可行性有重大差异 | 保留差异并按预设判据处置，不自动 support |
| T10 | 不同窗口／实例／单位／输出口径直接相减 | 拒绝不可比记录 |
| T11 | 相对差值分母为零、方向反了、百分点混淆 | 限定复算失败；不自动改公式或判据 |
| T12 | 表头齐全但空行／重复键／错误 selector | 拒绝；不能由汇总“通过”覆盖 |
| T13 | 有效比较得到 modify／辅助 reject | 检验可完成；关联 claim 动作未完成前正文 stale |
| T14 | 有效比较得到 core_answer／model_validity reject | 整体 redo_required，正确阶段和依赖回退 |
| T15 | 子运行崩溃后标 retired 或语义 reject | 拒绝伪装；证据未完成 |
| T16 | 运行后删除 required、修改对象／阈值／selectors | frozen plan 不匹配，旧回执不能通过 |
| T17 | registry、源码、回执只留一端 marker／未知协议 | fail closed，不降级 legacy |
| T18 | 原主簿、input 或 helper 漂移 | 旧比较证据失效；保持实际依赖范围 |
| T19 | 同 generation 下框架／计划／候选字节改变 | read-set 冲突，事务不提交 |
| T20 | 新增比较 scope，主模型与主簿未变 | 主 approved／quality／accepted 保持；分析链失效 |
| T21 | 主模型真正改变 | 原主批准与依赖比较证据均失效 |
| T22 | 历史 accepted 同 hash 分析只读 | 按原明确兼容路径读取，不伪称新两类已验证 |
| T23 | Python 和 MATLAB 相同新协议／表格 | 同一验收条件；不能有 MATLAB 宽松旁路 |
| T24 | 比较 helper 调用主入口或覆盖主簿 | 静态／执行测试发现并拒绝对应交付 |
| T25 | 新比较协议但未启用 A2／B2／C | 严格来源和覆盖仍生效；不暗中强启可选协议 |
| T26 | 已启用 A2／C／B2 且新范围不支持／对象错配 | 报未核验或不合格，不假造结构／独立性 PASS |
| T27 | 缩域、判据、近似或输出定义变化藏在 algorithm_semantics | 不因排除算法字段而授予同模型资格；保留模型相关项或要求复审 |
| T28 | 篡改表内基准值并同步改差异，算术仍正确 | 来源 selector 值核对失败，不能验收 |

### 15.3 小型真实数值案例

建议用同一组完全声明的合成数据，分别在两个 backend 的独立项目中测试：

- 训练点 `t=0,1,2,3`，`y=t^2`，共同留出点 `t=4`。
- 主数学模型是二次最小二乘回归；主算法使用明确 QR 求解，主结果预测 `16`。
- **多模型分支**：对照一阶线性最小二乘模型。训练拟合为 `y=-1+3t`，留出预测 `11`，同一留出真值为 `16`。比较共同误差，声明结构差异来自是否保留二次项。
- **多算法分支**：同一二次最小二乘模型用明确 SVD 求解，与 accepted QR 基准比较系数、残差和留出预测，按预设浮点容差核验。
- 两分支都消费同一个 accepted 主簿；不调用主入口、不覆写主簿。线性模型与二次模型不是“换一个函数名”；QR 与 SVD 是不同分解求解方法。
- 多模型出现差异可以支持“本案例二次表达改善共同误差”，不能要求两个模型一致才 passed，也不能推广为所有真实任务上二次模型更好。

这是拟议维护 fixture，不是现实赛题建模质量认证。实施时必须实际生成回执和非空底层记录，按相同字段／身份链验收，并保留 primary SHA 不变证据。

### 15.4 正式平台与证据

- 开发分支／draft PR：GitHub targeted、静态与生成检查。
- 冻结 ready PR：Windows Python 3.10 与 3.14 各四个分片，完整标准 discovery，无重复遗漏，精确记录 source/checkout/event SHA。
- Windows MATLAB R2024b：原生 primary/analysis、XLSX、receipt、两类新比较、helper 身份、主簿保护和适用 A2/B1 同链验证。
- 新增 MATLAB 比较 smoke 必须由现有原生 runner 明确调用，或由 `.github/workflows/ci.yml` 增加实际 MATLAB 执行步骤，并同步报告／产物／断言。Python discovery 不会自动执行新增 `.m` 文件，不能只提交例子而继续仅运行旧系数敏感性。
- Linux LaTeX／Production LaTeX attestation、Static contract lint、Generated file contract，以及适用 Optimization baseline 继续执行。
- 生成索引与 MANIFEST 交给 GitHub `refresh-generated`，不本地手改 hash，不另增 Python full 矩阵。
- 报告分别写清 targeted、最终 head full、conditional skip、合并和 main 验证；旧基线 success 不代替新增验收。

## 16. 兼容、版本与回滚

### 16.1 兼容

- 旧分析表和旧已验收数值不批量迁移。
- 旧已 accepted、同 hash 证据可按历史资格只读；不能从它推出新模型／算法检验已完成。
- 只重新进入旧敏感性等原有分析流程时，不无条件要求新比较清单。
- 选用新的两类方法、声明新比较协议或新专项表时，必须满足完整新合同；不能借兼容缺字段。
- 框架增量更新只替换受影响小问的比较段，保护主 SIB、独立问题和既有结果。
- 继续使用现有 result_analysis 总体字段、文件名和 backend；工作簿 Schema 可做向后兼容 minor 升级，其他合同只按实质变更升级。

### 16.2 版本

建议此主题作为一个向后兼容 minor 功能。候选 Skill 版本为 `10.18.0`，最终实施前重新核对 main。工作簿／state／execution／approval 等独立版本按各自实际字段及行为变化确定，不全部机械同步成 Skill 版本。

不得把新强制运行要求藏成 docs；不得因新增可选功能把旧项目无条件判不合格。

### 16.3 回滚

- 单主题分支／PR；每一阶段可审查提交，生成物仍由 GitHub 管理。
- 仓库回滚采用 revert 对应功能提交，再由远端重新生成和验收。
- 不删除用户项目的比较规范／结果／否证记录，不移动已发布标签。
- 已有新协议项目回到未支持扩展的旧工具时，不能假定旧工具天然报告不支持。回滚操作须先确认读取／验收工具能力；不支持时停止新比较的正式验收，只保留查看证据与明确兼容提示，不允许用旧验收替代。不能保证能力检查的环境不得把回滚后的项目报告为已验证。
- 不把 rollback 自动解释为用户项目迁移或恢复数值有效性。

## 17. 实施时必须复核的具体接口

1. **同模型投影**：原 SIB 的 extensions 及 algorithm_semantics 中哪些内容具有模型含义，显式保留项如何规范化；无法划分时不授予资格，新投影不改变主身份。
2. **范围批准**：在当前仅有小问范围的 Model Approval API 中，如何新增比较范围消费，并最小扩展可选 C 对象；历史主批准不能自动授权新数学对象。
3. **比较规范存储**：框架采用独立严格 marker 的具体解析形式；单份语义规范与 state 引用对齐，避免多个可编辑事实源。
4. **来源选择器**：复用 B1 的 bounded selector/Decimal 哪些算子已支持；不支持的指标须保留底层证据并标需人工审查，不静默执行任意表达式。
5. **事务激活**：无 A2 时，新增比较协议是否能捕获同一 state/framework/source/input/workbook read-set。
6. **回退授权**：扩展现有核心否证 caller_scope 后，runtime、sync 和所有依赖检查是否消费同一处置语义。
7. **新表与 fallback**：仓库 Schema 和复制到用户项目的 IO 投影是否完全一致；不能只修一端。
8. **模板位置**：新增 Python/MATLAB 模式能否被现有 starter／索引／代码质量扫描正确识别；不存在的 q1_analysis.py 不列为现有修改对象。
9. **两端真实执行**：合成案例是否产生真实 QR/SVD 和不同模型结果，还是只写固定数字；必须通过实际执行证据核实。
10. **消费者范围**：普通写作保持渐进读取，绘图只读 accepted 新表；不为新能力默认加载全仓库。
11. **旧工具能力**：基础 receipt 版本不变时，旧工具不具有新扩展校验保证；部署／回滚的最低版本与能力检查必须在交接中明确，测试不得把旧工具的忽略扩展报告为成功兼容。

上述是实施前后要解决的工程接口，不是本轮已验证的功能结果。如果发现共享组件存在无法满足的边界，先更新这一计划的具体设计与受影响验收，不扩大为无关重构，不降低精度或来源要求。

## 18. 修改简报模板与完成标准

### 实施 PR 简报

```text
修改主题：03B 增加多模型检验与同模型多算法检验，并补逐项证据闭环
当前版本：实施前刷新
目标版本：候选 10.18.0，实施前确定
变更等级：minor
直接目标：两类条件式检验、合法对象与共同评价、必要项覆盖、真实证据和正确处置
明确不做：全面检验重构、固定双模型、混合 backend、主SIB/主质量门重定义、旧项目批量迁移
权威事实源：Module03B、模型设计/批准、workbook/state/user-execution/runtime/state-transition Authorities
预计修改文件：按本文件第13节冻结实际清单
禁止触碰文件：无关 Case Memory、旧论文正文、真实赛题结果、legacy默认链和未批准用户项目
兼容性要求：旧表/文件名/status保留，新增能力严格激活，既有 accepted 只读资格不伪扩张
迁移要求：无自动迁移；新功能进入时按当前合同补充
验收测试：第15节增量行为、真实Python/MATLAB与最终head远端完整验收
回滚方式：单主题提交revert，保留用户证据，未知协议失败关闭
```

### 计划执行完成标准

- [ ] 新类型按数学对象区分，种子／改名不冒充模型或算法变化。
- [ ] necessary 比较问题都有合法对象、预设判据、真实细粒度证据和处置。
- [ ] 敏感性表不能替代缺失的新 required 项。
- [ ] 两张新表可跨题型使用，原算法／结构表保持兼容。
- [ ] scope／plan／source／input／主簿／回执身份闭合，candidate 不存在 acceptance 循环。
- [ ] 无 A2/B2/C 时新能力的严格检查仍有效，启用时又保持其边界。
- [ ] 添加比较不废未变主结果，真正主变更和核心否证正确失效与回退。
- [ ] 有效负结果与技术失败区分，修改／删除主张动作可追溯。
- [ ] Python/MATLAB 分别真实执行两类小案例，主簿不变，产物非空且数值可核查。
- [ ] 图表／写作／终审只使用当前合法证据，不夸大一致性或独立性。
- [ ] 最终 PR head 的正式 GitHub 验收通过；若合并，main 已复核；release 状态单独报告。

**本轮状态：结构审阅与计划完成；源码实施、测试、合并和发布均未进行。**
