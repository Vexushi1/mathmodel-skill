# B2 主张消费与片段失效：接续实施指南

> 阶段指南，不是运行时 Authority。B2 的只读审计、状态写入、正式门禁和跨格式覆盖须分别以实际提交、测试和 CI 证明；完成首个切片不等于完成 B2。

> **2026-09-26 接续：** B2a [PR #240](https://github.com/Vexushi1/mathmodel-skill/pull/240) 已合并为 `b7c0f6827fdab4319c504f9f1592a59096fef265`；最终 head 的 [CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36215999744) 和 [优化基线](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36215999692) 成功，主干 [CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36216997615) 13/13 成功。B2b1 [PR #241](https://github.com/Vexushi1/mathmodel-skill/pull/241) 已合并为 `a17a1d539519fc7c662a73fb957871c822aadf36`；精确 head 的 [CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36220676500) 13/13、[优化基线](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36220676509) 和主干 [CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36221675161) 13/13 均成功，合并树与已测 head 树一致。下面 B2a/B2b1 简报保留为实施记录；当前进入单独的 B2b2 模块化 LaTeX 文本门切片。

日期：2026-09-26。基线 main=`a7ff4b792c4f0dac92bb7cd5b4569cf0de03967d`，Skill 10.4.0 / State 8.3.0；B1 PR #239 已合并，主干 CI [36212303219](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36212303219) 13/13 成功，合并树与最终 B1 head 树一致。开始本阶段时没有其他开放 PR。本指南落实原计划第 7、11—16、19 节，保留 B1 的 accepted 资格与语义支持边界。

## 1. 修改简报

| 项目 | 决定 |
|---|---|
| 主题 | B2 主张到实际论文片段的只读消费核验，随后单独接入失效写入和正式门 |
| 目标版本 | 首切片暂定 Skill 10.5.0、State 8.4.0、独立 B2 observe 协议 1.0.0 |
| 直接目标 | 对明确启用的模块化 LaTeX 项目定位已登记 claim 的活动源码、片段、物理行及可核对数值；报告覆盖缺口和解释性影响路径 |
| Authority | B1 Claim Contract、现有 State/Fragment、Writing Reasoning、accepted workbook、Figure Evidence、原状态转移/事务 |
| 保留边界 | 旧项目和默认路由、A2/B1 资格、数学批准、数值结果、原 artifact stale、现有唯一写入协调器 |
| 首切片不做 | 不写用户项目、不生成/重算模型或图、不自动宣称语义成立、不接正式写作/交付 gate、不执行 B12 的 stale 写入 |
| 回滚 | 未合并时撤回独立 PR；已声明的 opt-in 新记录不靠删字段伪装旧版本兼容 |

预计首切片文件组：可选 State Schema、独立小型 B2 合同、只读 LaTeX scanner 与审计入口、显式 route/manifest、必要版本载体、专项/兼容测试及自动生成索引。原则上不改 `scripts/sync_project.py`、`project_transaction.py`、A2/B1 来源资格实现、MATLAB/绘图模板或用户项目。超过 20 路径时按合同/消费者/测试/载体/生成物逐组解释，不做全仓格式化。

## 2. 阶段拆分与完成条件

1. **B2a 只读 observe：** 新 opt-in 仅接受 `mode: observe`，通过独立只读路由。以现有 `paper_fragments[].depends_on: claim:<id>` 为唯一实际消费边；覆盖义务只声明哪些已登记 claim 需要哪类 fragment。扫描器现场核验 B1 来源并读取可证明活动的静态 LaTeX 图，报告 source→claim→fragment、位置、数值冲突、登记覆盖与未登记候选。全部项目字节不变。
2. **B2b 状态传播与正式消费：** 另经协议/兼容评审决定 enforce 激活，扩原状态 Authority 的纯转移和现有 coordinator 写入；B12 的实际局部 stale、正式写作/图表/交付门与 transaction/read-set 故障注入在此验收。不得用细粒度结果清除原 artifact stale。
3. **B2 完成复核：** 按原 B01、B09—B12、B16 的完整场景，检查选定论文格式与 Figure ID→脚本→accepted 来源→真实图片→caption 的消费链。未覆盖 DOCX、单文件 TeX、复杂宏或人工语义判定时逐项标未完成，不提前进入 C1。

B2a 和 B2b 可以分 PR 串行；每个 PR 都须有精确 head CI、完整基础回归、相关专项测试和主干复验。B2 台账在全部目标达成前保持“进行中”。

## 3. 协议与单一事实源

新增 `paper_framework.claim_consumption_policy` 仅作显式激活与关键消费义务，闭合形状：

```yaml
claim_consumption_policy:
  protocol_version: 1.0.0
  mode: observe
  required_consumptions:
    - claim_id: Q1_answer
      fragment_kinds: [abstract_claim, question_result_text]
```

不增 `claims[].consumed_by`、第二数值表或作者可自签的“已证明语义”。首切片不持久化 `criticality` 或 `source_format`：核心/辅助处置继续服从现有 Analysis Necessity、Claim Strength 和审查判断，实际格式由当前源码图核验。无 policy 的项目继续旧路径；显式 null、未知/残缺版本或重复/未知引用在 B2 显式审计中 fail closed。B1 `claim_evidence` 仍为 1.0.0，A2/B1 旧协议不自动迁移。

State 的 fragment 记录是机器位置事实；当前 Framework Markdown 的 Paper Fragment Dependency Map 必须逐字段与 opt-in 范围的 State 行一致，包含 ID、种类、范围、依赖、锚点、源码路径和状态。缺行、重复行、字段冲突均不能任选一侧继续。旧无 policy 项目维持现有宽度。来源数值仍只来自经 B1/原 runtime 验收的 accepted 工作簿；`claim.text` 与断言是作者声明，不是事实替身。

## 4. 只读扫描与报告

扫描器仅承认可静态确定活动性的模块化 `final_latex/main.tex` include 图。保留原始源码字节、相对路径、偏移和物理行号，屏蔽注释/verbatim 时保持位置。遇 `\includeonly`、条件或动态包含、宏生成目标以及不能明确解析的文本结构时，报告 `not_assessed/unsupported`；越界路径、冲突记录或读集变化则阻断。静态源码定位不等于最终 PDF 已渲染文字。

B2 入口内部现场调用 B1，而不接受外部“已通过”报告。逐条检查来源资格、唯一选择与断言；对摘要、正文、图注分别从当次原值及适用 Numeric Profile 核对明确显示形式，不把某一位置的已舍入断言借给另一位置。B1 与 B2 的 State、Framework、工作簿和 LaTeX 读集合并后在返回前重检。机器报告分别列出已登记义务定位情况、可疑未登记主张、人工语义覆盖 `not_assessed`；不把正则命中数称为全文召回率。

B2a 对 `analysis_evidence_dispositions` 的 `modify/reject` 仅给出影响 claim、关联及下游 fragment 和原因路径，字段名须表明是 `suggested_stale`。报告不修改 fragment status、不清 accepted/stale，也不决定核心答案是否重算。

## 5. 验收与停点

首切片至少有下列独立合成正反例：B01 摘要 100/正文 110 的真实位置和同值合法格式；B09 启发式结果与明确肯定“全局最优”冲突；B10 未做深化却声称广泛稳健；B11 工作簿其他单元格改变而目标值不变仍先被原资格拒绝；B12 current analysis 否证只报告影响路径且项目字节不变；B16 登记义务缺片段、未登记候选与人工覆盖未评估分列。再测未知协议、State/Framework 不一致、歧义锚点、非活动文件、条件包含、CRLF/BOM 行号、注释/verbatim 假数值、路径/符号链接越界及扫描中改写。

禁用路径差分不加载新合同或扫描论文；独立 route 没有 `--write`，不插入普通 LaTeX、绘图或交付强制门。运行 `lint_skill.py`、全量 `unittest discover`、`generate_indexes.py --check`、B2 专项与受影响旧测试；仅精确提交的 Linux 多版本、Windows、原生 MATLAB 和 LaTeX CI 全通过后才合并。主干合并树与已测 head 树核对，合并后 CI 再复验。没有真实执行证据时在台账写未运行或进行中。

合并前记录：B2a 的 Schema/合同、位置 scanner、现场 B1 组合审计、显式路由、合成反例与版本载体已在独立分支实现；当时合并资格仍取决于精确 head 的全量回归和 CI。该验收与合并现已完成，见页首接续记录。C/D/E 保持未开始。

## 6. B2b1 局部失效写入的修改简报

| 项目 | 决定 |
|---|---|
| 当前基线 | `main@b7c0f6827fdab4319c504f9f1592a59096fef265`，Skill 10.5.0 / State 8.4.0；无开放 PR |
| 目标 | Skill 10.6.0 / State 8.5.0，独立 B2 `propagate` 1.1.0 协议；`observe` 1.0.0 不迁移 |
| 直接目标 | 对显式启用的项目，在现有 `sync_project --write` 中把当前 `modify/reject` 处置的精确 B1 claim ID 扩散到全部登记 fragment，并与 Framework 表行同事务写 stale |
| Authority | `core/project_state.schema.yaml`、B1/B2 合同、`core/state_transition_contract.yaml`、`scripts/state_transitions.py`、现有 `sync_project.py`/`project_transaction.py`；Framework 表是 State 的可核对投影 |
| 明确不做 | 不对普通项目和 `observe` 项目新增 claim 驱动失效；保留旧问题级同步写入；不按自由文本猜测 claim ID，不清除既有 artifact stale，不续签 accepted/approval，不接正式写作/图表/交付 gate，不宣称 B2 完成 |
| 兼容与迁移 | 新策略必须精确配对协议和 mode；未知/残缺记录 fail closed。已有 `observe` 不自动升级；需要持久化失效的项目显式选择新策略并复核当前处置的目标 ID |
| 验收 | B12 辅助否决只失效相关片段、依赖扇出、未知/歧义目标拒写、旧问题级失效并集、State/Framework 同步、generation/read-set 冲突与事务故障注入；完整基础回归、lint、索引、精确 head CI 和主干复验 |
| 回滚 | 未合并时撤回独立 PR；合并后不能删除已经声明的 1.1.0 记录来伪装兼容，保留旧 stale 与项目事务恢复边界 |

预计文件组为可选 State/B2 协议、纯失效闭包、原同步器中的唯一 writer、Frame 表投影校验、专项及历史兼容测试、版本载体和生成元数据。不另造第二个写入器或默认路由门。正式消费门、DOCX/单文件 TeX、Figure ID→脚本→accepted 来源→图片→caption 另阶段处理；这些验收完成前 B2 台账保持进行中，C/D/E 不启动。

## 7. B2b2 模块化 LaTeX 文本门的修改简报

| 项目 | 决定 |
|---|---|
| 当前基线 | `main@a17a1d539519fc7c662a73fb957871c822aadf36`，Skill 10.6.0 / State 8.5.0；2026-09-26 查询无开放 PR，主干 CI 36221675161 成功 |
| 目标 | 向后兼容的 Skill 10.7.0 / State 8.6.0，B2 精确 `1.2.0/enforce_latex_text` 配对；只在明示项目的模块化 LaTeX 文本范围执行机器门 |
| 直接目标 | 现场重检 B1 当前来源、已登记 claim 到活动摘要/正文 fragment 的消费、数值与过强措辞；正式 LaTeX 审计、编译证明、显式 latex/submission 同步和提交验证均不可绕过；旧证明绑定当前 State、Framework、workbook、源码和 Skill 读集 |
| Authority | B1 来源资格、B2 消费合同、State/fragment、现有 Writing Reasoning 与 LaTeX 审计/编译/提交链；Framework 表仍是 State 投影 |
| 明确不做 | 不宣称人工语义覆盖、全文召回或 Figure ID→脚本→accepted 来源→图片→caption；不把 DOCX、单文件/动态 TeX 纳入新门，不改数值求解或接受资格 |
| 兼容与迁移 | 无 policy、`1.0.0/observe`、`1.1.0/propagate` 保持原门；新模式继承 claim 局部 stale 写入；未知/错配协议 fail closed。项目须显式选择新模式并复核义务与活动模块化源码，不能自动升级 |
| 验收 | B01、B09—B12、B16 的选定文本范围正反例；旧项目差分、跨格式未评估、read-set 改写和旧证明重放；lint、全量单测、索引检查、精确 head CI、合并树与主干复验 |
| 回滚 | 未合并撤回本主题 PR；已声明新协议的项目保留可解释状态及原 stale，不能删除字段冒充旧项目 |

本切片只授予“已声明模块化 LaTeX 文本消费机器门通过”的有限判定。任何图注或其他未支持的 claim 消费义务均不能从文本门取得通过；B2 完成复核和 C1 继续等待后续独立验收。
