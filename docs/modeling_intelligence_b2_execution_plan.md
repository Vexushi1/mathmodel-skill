# B2 主张消费与片段失效：接续实施指南

> 阶段指南，不是运行时 Authority。B2 的只读审计、状态写入、正式门禁和跨格式覆盖须分别以实际提交、测试和 CI 证明；完成首个切片不等于完成 B2。

> **2026-09-27 接续：** B2a [PR #240](https://github.com/Vexushi1/mathmodel-skill/pull/240) 已合并为 `b7c0f6827fdab4319c504f9f1592a59096fef265`；最终 head 的 [CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36215999744) 和 [优化基线](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36215999692) 成功，主干 [CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36216997615) 13/13 成功。B2b1 [PR #241](https://github.com/Vexushi1/mathmodel-skill/pull/241) 已合并为 `a17a1d539519fc7c662a73fb957871c822aadf36`；精确 head 的 [CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36220676500) 13/13、[优化基线](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36220676509) 和主干 [CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36221675161) 13/13 均成功，合并树与已测 head 树一致。B2b2 [PR #242](https://github.com/Vexushi1/mathmodel-skill/pull/242) 已合并为 `431839d4cb77440bffc2c6f1fcac7c2279b3ab10`；精确 head 的 [CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36226883079) 13/13、[优化基线](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36226883018) 和主干 [CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36235022833) 13/13 均成功，合并树与已测 head 树一致。B2b3a [PR #243](https://github.com/Vexushi1/mathmodel-skill/pull/243) 已合并为 `1428b9c7309aefdb6a76409f904543daf989c20b`；精确 head 的 [CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36241117504) 13/13、[优化基线](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36241117468) 和主干 [CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36242410758) 13/13 均成功，合并树与已测 head 树一致。下面 B2a/B2b1/B2b2/B2b3a 简报保留为实施记录；B2b3b [PR #244](https://github.com/Vexushi1/mathmodel-skill/pull/244) 已合并为 `4033896b4e3b7c4c897bfc9528c9ec826b5d83cf`；精确 head `ad158ea42e16d1debe3dcd248addaf76c8434d04` 的 [CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36247446351) 13/13 与 [优化基线](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36247446381) 均成功，合并树 `383574dd04ce5643c810c2c773d5a99114ac3e8a` 与已测 head 树一致；合并后主干 [CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36286699465) 13/13 成功。B2b3c [PR #245](https://github.com/Vexushi1/mathmodel-skill/pull/245) 已合并为 `360caee92aa8d33d9ff856e5abf03bf8768bf4eb`，精确 head CI 与合并后主干 CI 均 13/13 成功；B2b3d [PR #246](https://github.com/Vexushi1/mathmodel-skill/pull/246) 已合并至 `main@53263841053765a956759be1757ff7630e995187`；精确 head [CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36294611029) 13/13、[优化基线](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36294611040) 成功，已测 head tree 与合并树同为 `82d116765f33c26b7edfbc0f845df4aecdbbcb5a`；合并后主干 [CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36295956023) 13/13 成功。B2b4 #247 已合并并完成主干复验，证据见第 12 节；当前接续第 13 节 B2b5 连续验收。

> **2026-09-28 接续（覆盖上一段的当前状态）：** B2b6 [PR #249](https://github.com/Vexushi1/mathmodel-skill/pull/249) 已合并至 `main@86fedb04fa4ace5ce27ba5f65a804ab82b306f09`；精确 head CI 13/13、优化基线、合并树一致性与合并后主干 CI 13/13 均已复核。当前进入第 15 节 B2c 跨载体消费与总验收；本节不预写该切片后续的 PR、CI、合并或主干复验结果，C1 在 B2 总验收关闭前不启动。

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

## 8. B2b3a Figure 身份只读绑定的修改简报

| 项目 | 决定 |
|---|---|
| 当前基线 | `main@431839d4cb77440bffc2c6f1fcac7c2279b3ab10`，Skill 10.7.0 / State 8.6.0 / B2 合同 1.2.0；B2b2 的精确 head 与合并后主干 CI 均 13/13 成功 |
| 目标 | 向后兼容的 Skill 10.8.0 / State 8.7.0 / B2 合同 1.3.0；原有 `1.0.0/observe`、`1.1.0/propagate`、`1.2.0/enforce_latex_text` 配对和旧正式门不变 |
| 直接目标 | 在项目显式声明的工作簿驱动结果图范围，以同一 Figure ID 只读核对 typed binding、当前 Framework 图表登记、State 片段依赖、活动模块化 LaTeX 的图标签/图片引用和当前已批准图片路径；报告具体身份缺口和未评估项 |
| Authority | `modules/04_figure_evidence.md` 的 Figure 链、`core/project_state.schema.yaml` 的可选绑定形状、`core/claim_consumption_contract.yaml` 的 B2 只读审计边界；Framework 图表登记与 `artifacts.approved_figures` 保持原有职责 |
| 明确不做 | 不写项目、不生成/重绘图片、不凭文件名视作实际批准；不核准 accepted 工作簿来源或绘图脚本内容，不判断图像/图注语义、不接入 LaTeX/提交正式门；机理图、全局示意图、表格、DOCX、单文件/动态 TeX 留待后续 |
| 兼容与迁移 | `figure_bindings` 可选，无记录的旧项目保持原路径；项目选择绑定时逐项显式登记并核对，不自动迁移、不新增 policy mode、不把只读观察升级为正式通过 |
| 验收 | 正常 Figure ID 闭合、错误/重复 ID、未批准或路径错配、非活动 TeX、label/图片歧义、State/Framework 失配、读集漂移、旧 mode/无 policy 兼容；专项、全量测试、lint、索引、精确 head CI 和主干复验分别记录 |
| 回滚 | 未合并时撤回本主题 PR；已声明的绑定保留可解释记录，移除新审计功能不能伪称图形证据资格已验证 |

本切片只增加**身份与路径的只读观察**。采用绑定的项目在 Framework“正文引用位置”填写当前活动源码的 `final_latex/...tex:物理行号`，供字面引用定位；活动 `\graphicspath`、符号链接入口和无法静态解析的结构保持未核验或阻断。`identity_status=matched` 仅说明本次路径/字面关系匹配，既往图片批准对当前字节的有效性仍为 `approval_freshness=not_assessed`。本切片不授予 Figure 证据链完整通过、正文/图注语义支持或新的交付资格。B2 仍在进行中；B16 全场景、跨格式 Figure 链和 C1 均等待后续独立验收。

## 9. B2b3b Figure 来源与批准 bundle 当前性只读观察的修改简报

| 项目 | 决定 |
|---|---|
| 当前基线 | `main@1428b9c7309aefdb6a76409f904543daf989c20b`，Skill 10.8.0 / State 8.7.0 / B2 合同 1.3.0；B2b3a 精确 head 与合并后主干 CI 均 13/13 成功 |
| 目标 | 向后兼容的 Skill 10.9.0 / State 8.8.0 / B2 合同 1.4.0；原 `observe`、`propagate`、`enforce_latex_text` 协议/mode 配对及正式文本门不变 |
| 直接目标 | 工作簿驱动结果图的现有 `figure_bindings` 行可选声明非空 `source_bindings`，以 `{source_id, sheet, required_headers}` 绑定 Figure 关联 claim 的当前 B1 来源闭包；只读核对所选工作表/精确表头，观察原 State 已验证脚本与图片 bundle 哈希是否匹配当前字节，并要求本次 scoped Figure bundle 的全部发现路径属于原 `approved_figures` |
| Authority | B1 Claim 来源资格、`core/project_state.schema.yaml` 可选绑定、`core/claim_consumption_contract.yaml` B2 审计、Figure Evidence Authority；不建立第二套来源或批准状态 |
| 明确不做 | 不重算 accepted 工作簿、不执行绘图脚本、不生成或重绘图、不续签原入文批准、不判断图片/图注语义；不扩 LaTeX/提交正式门、不覆盖机理/全局示意图、表格或其他论文格式 |
| 兼容与迁移 | `source_bindings` 可选；只有 B2b3a 旧身份绑定而无来源记录的行继续报告来源 `not_assessed`，旧项目和 policy 三配对不自动迁移或改变资格 |
| 验收 | 当前 B1 source_id、sheet、required_headers 的正反例，缺失/歧义/漂移来源，脚本或图片 bundle 与批准路径的当前性，旧身份行 `not_assessed`、只读字节不变与读集改写；专项、全量、lint、索引、精确 head CI 和主干复验分别记录 |
| 回滚 | 未合并撤回本主题 PR；已声明来源绑定不得通过删字段假装曾获来源或视觉语义核准 |

报告新增 `figure_source_checks`，每张图来源观察为 `current`、`needs_review` 或 `not_assessed`；`approval_freshness=current` 只说明原已验证 bundle 的脚本/图片哈希匹配当前字节，且本次 scoped bundle 的全部发现路径属于原 `approved_figures`，绝不代表新批准或全局批准路径复验。`identity_status` 保留 B2b3a 的身份意义，`source_and_visual_semantics` 仍为 `not_assessed`。本切片没有正式 Figure 门；B2 总验收和 C1 继续等待后续阶段。

同一次只读审计按唯一来源计共享预算：accepted 工作簿最多 8 本、合计沿用 B1 `total_workbook_bytes` 64 MiB；图片最多 512 张、合计 256 MiB；脚本最多 16 份、合计 16 MiB。超限返回 `needs_review`，不截断为成功。同一 Figure 来源可复用已捕获哈希、工作簿解析对象和 scoped discovery；返回前仍逐项复核完整项目/Skill 读集与 Figure discovery，不能因缓存跳过漂移检查。

## 10. B2b3c Figure 图注标量数值只读观察的修改简报

| 项目 | 决定 |
|---|---|
| 当前基线 | B2b3b [PR #244](https://github.com/Vexushi1/mathmodel-skill/pull/244) 已合并为 `4033896b4e3b7c4c897bfc9528c9ec826b5d83cf`；精确 head `ad158ea42e16d1debe3dcd248addaf76c8434d04`，Skill 10.9.0 / State 8.8.0 / B2 合同 1.4.0，head CI 36247446351 13/13、优化基线 36247446381 成功，合并树 `383574dd04ce5643c810c2c773d5a99114ac3e8a` 与 head 树一致；合并后 main CI 36286699465 13/13 成功 |
| 目标 | 向后兼容 minor：Skill 10.10.0 / State 8.9.0 / B2 合同 1.5.0；原三对 policy/mode 与 `enforce_latex_text` 门不变 |
| 直接目标 | Numeric Profile 增可选 `figure_caption_decimals`（0—30），仅对已绑定 Figure 的可证明活动静态模块化 LaTeX 长图注观察当前 B1 标量的声明位置数值形式；使用 profile 原有单位和显示形式，从当次 accepted 原值换算与舍入 |
| Authority | `core/project_state.schema.yaml` 的 Numeric Profile、B1 accepted 来源资格、`core/claim_consumption_contract.yaml` 的只读审计、Figure Evidence Authority |
| 明确不做 | 不借摘要/正文/表格/提交精度，不借 `claim.assertion` 中另一位置的已舍入数字；不判定多值图注、单位/宏语义、短图注、渲染视觉与正文语义，不续签图片批准、不新增正式 Figure 门、不改求解和绘图 |
| 兼容与迁移 | 字段可选；旧项目无字段仍按原 B2b3b 来源与 bundle 观察，图注数值为 `not_assessed`；不自动迁移旧 Numeric Profile 或改变原三种 mode |
| 验收 | 图注专属精度的正反例、缺失/越界字段、与 body/table 精度不同、B1 原值变化、静态活动源码与多值/单位/宏/短图注未评估、只读与读集漂移；专项/全量/lint/索引及精确 head CI 后分别补证 |
| 回滚 | 未合并撤回本主题 PR；旧字段不需迁移，新字段审计不能通过删除精度记录伪装曾核准图注数值 |

**2026-09-27 验收闭环：** B2b3c [PR #245](https://github.com/Vexushi1/mathmodel-skill/pull/245) 已合并为 `360caee92aa8d33d9ff856e5abf03bf8768bf4eb`。独立复审先后修复数字落在绑定 claim 片段之前、`per/each/every/每` 复合单位后缀误报匹配；最终 head `d8e371f2424dd0325065900179b5911c1547d8d9` 本地全量 2057 项通过（10 skipped），[head CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36289746721) 13/13 和 [优化基线](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36289746750) 成功，合并树 `12306314c4d2831c152f072009e779a75f222ad0` 与已测 head 树一致，[合并后 main CI](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36291224490) 13/13 成功。

`figure_caption_numeric_checks` 是独立只读观察。局部数值形式匹配不表示图注整体主张获语义支持，也不表示图片视觉充分或渲染后版式合格。B2 台账继续“进行中”；DOCX、单文件 TeX、复杂宏、Figure 正式门与完整 B01/B09—B12/B16 场景验收仍需后续独立证据。

## 11. B2b3d 未登记强断言候选漏检修复的修改简报

| 项目 | 决定 |
|---|---|
| 当前基线 | B2b3c `main@360caee92aa8d33d9ff856e5abf03bf8768bf4eb`；Skill 10.10.0 / State 8.9.0 / B2 合同 1.5.0；精确 head、合并树与主干 CI 证据见第 10 节 |
| 目标与等级 | patch：Skill 10.10.1 / State 8.9.0 / B2 合同 1.5.1；保留现有三对 policy/mode 与正式门的激活范围 |
| 可复现缺口 | 已登记数值片段均正确时，活动 `extra.tex` 的无数字“globally optimal / robust across all”未登记声明被现有纯数字候选扫描漏过；同一数值片段内额外追加而未在直连 claim.text 登记的强断言也会被整段豁免；直连 claim.text 否定该断言、正文却肯定时仍可能误豁免，1.2.0 文本门误报通过 |
| 直接目标 | 对已证明活动的静态 LaTeX 正文，只读定位既有全局最优/广泛稳健模式中未由直连 claim.text 登记的候选及物理位置；候选或显式报告上限溢出均为 `needs_review`，已激活的 1.2.0 文本门阻断 |
| Authority | `core/claim_consumption_contract.yaml`、现有 `claim_tex` 活动源码/屏蔽规则、B1/fragment 与 Writing Reasoning 主张强度边界 |
| 明确不做 | 不推断句子真假或宣称全文召回，不改 B1 accepted 来源、State/Framework writer、Figure 正式门、DOCX/单文件/动态 TeX 或原无 policy 路由 |
| 兼容与迁移 | 旧项目无 policy 不加载新扫描；1.0/1.1 正式门仍 `not_applicable`；1.2 显式文本门对此前漏报的活动强断言保守拒绝，作者复核后需更新登记/正文并重审，无 Schema 迁移 |
| 验收 | 活动额外文件中英文强断言、数值片段内未登记附加断言、否定/未证明登记不豁免肯定正文、注释/verbatim/导言区及未绑定 Figure 环境排除、直连 claim.text 同类肯定措辞不重复、CRLF/BOM 物理位置、100 条上限溢出、全量/专项/lint/索引/精确 head CI 与主干复验 |
| 回滚 | 未合并撤回本主题 PR；已选择 1.2 文本门的项目保留当前源码证据并重新审计，不通过删候选伪造旧通过 |

本切片只补 B09/B10/B16 在有限静态文本子集中的候选漏检。B2 完整 Figure 证明与正式门、B12 连续场景、DOCX、单文件 TeX、复杂宏及人工语义覆盖仍待后续独立验收；C1 不提前启动。

兼容边界：活动正文完全没有目标强措辞时，无需 Figure 区间清单；有目标措辞却因跨 `\input` 等结构无法确认 Figure 区间时保守 `needs_review`，不据此认定图注属于正式文本门。

## 12. B2b4 显式 Figure 机器链与精确图片输入证明的修改简报

| 项目 | 决定 |
|---|---|
| 当前基线 | B2b3d [PR #246](https://github.com/Vexushi1/mathmodel-skill/pull/246) 已合并为 `main@53263841053765a956759be1757ff7630e995187`；已测 head tree 与合并树同为 `82d116765f33c26b7edfbc0f845df4aecdbbcb5a`，精确 head CI 36294611029 13/13、优化基线 36294611040 与合并后 main CI 36295956023 13/13 均成功；Skill 10.10.1 / State 8.9.0 / B2 合同 1.5.1 |
| 目标与等级 | minor：Skill 10.11.0 / State 8.10.0 / B2 合同 1.6.0；新增显式 `1.3.0/enforce_latex_text_and_figure_chain` 配对，沿用原 stale-only writer；在同一次审计复核 1.2.0 文本条件并仅豁免精确匹配的 Figure 图注标量候选，1.2.0 文本门入口自身保持只接受 1.2.0 |
| 可复现缺口 | 1.2.0 文本门明确排除 Figure；既有 Figure 身份、B1 来源、原批准 bundle 和图注标量只读观察无法阻止显式 Figure 链缺口进入正式交付。v4 LaTeX 证明的根目录为 `final_latex`，无法将 `../figures/...` 纳入受约束的源码、实际编译输入与提交包同一证明链 |
| 直接目标 | 对显式 1.3.0 且显式 latex/submission 范围，在同一次审计完成原文本条件复核后，要求已绑定的工作簿驱动结果图当前 Figure ID、片段定位、B1 来源、原批准脚本/图片 bundle 及长图注标量形式全部闭合；通过的 `formal_figure_gate` 只提供精确 `figure_image_paths` 与 `{figure_id,image_token,image_path}` 图形绑定，供随后 v5 正式审计、实际编译输入和提交包复核 |
| Authority | `core/claim_consumption_contract.yaml` 定义 B2 Figure 机器门；`core/project_state.schema.yaml` 定义可选新策略形状；Figure Evidence Authority 定义图的来源与批准；原 `latex_delivery.py`/正式编译及提交包链只消费门给出的当前图片身份 |
| 明确不做 | 不让未编译的 `.fls` 成为审计前置条件，不改 B1 accepted 来源或原批准写入者，不运行求解/绘图，不把视觉充分性或图注整体语义称作机器通过，不自动覆盖旧策略；DOCX、单文件/动态 TeX、机理/全局示意图与人工语义仍待独立验收 |
| 兼容与迁移 | 原 `1.0.0/observe`、`1.1.0/propagate`、`1.2.0/enforce_latex_text` 配对及其 v4 证明路径保持原行为。旧项目无自动迁移；选择 1.3.0 的项目需显式登记 Figure 与来源绑定、图注专属数值精度，v5 只接受字面 `../figures/...` 且解析到项目根 `figures/` 下已批准图片的受限静态路径，并重新取得当前正式证明；不以删字段绕过缺口 |
| 验收 | 正常 Figure 链、同一 Figure claim 的摘要/结果正文/Figure 义务、缺 ID/来源/批准当前性/图注形式/活动片段、100 条数字候选截断保守拒绝、旧策略兼容、审计与编译之间图片或读集漂移、v5 实际输入和提交包图片一致性、路径穿越与符号链接、全量与专项测试、lint、索引、精确 head CI 与合并后主干复验分别记录 |
| 回滚 | 未合并时撤回本主题 PR；已显式采用 1.3.0 的项目须通过受审迁移恢复旧策略或修复 Figure 证据，不在消费者中默认降级为 v4 |

预计文件组按协议与 State、B2 审计/门、LaTeX 审计与编译证明、提交包消费者、专项/兼容测试、版本载体、生成索引分别说明，超过 20 路径逐组核对；不改数值求解、绘图脚本或用户项目。`formal_figure_gate.status=passed` 仅是当前机器链判断，`v5` 证明须在之后绑定编译器实际图片输入和最终提交包；完整视觉与图注语义、B12 连续场景、跨格式及 B2 总验收继续列为未完成，C1 不提前启动。

**B2b4 验收记录：** [PR #247](https://github.com/Vexushi1/mathmodel-skill/pull/247) 已合并为 `7d5eec484b2e2033246f86fb23f2c22b49df807d`。最终 head `f1e0b44c9ec42614ee14daf59e5462f098e28d20` 本地全量 2096 项通过（12 skipped）；[head CI 36303730157](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36303730157) 13/13、[优化基线 36303730239](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36303730239) 成功（可选真实 MATLAB publication preview 未执行）；合并树与已测 head 同为 `16bdc6a747cb62cd86c19d7dcba88ce215fc39e7`，[main CI 36305730258](https://github.com/Vexushi1/mathmodel-skill/actions/runs/36305730258) 13/13 成功，含真实 XeLaTeX Figure 编译。当前接续 B2b5。

## 13. B2b5 辅助主张否证连续验收的修改简报

| 项目 | 决定 |
|---|---|
| 当前基线 | `main@7d5eec484b2e2033246f86fb23f2c22b49df807d`，Skill 10.11.0 / State 8.10.0 / B2 合同 1.6.0；主干 CI 13/13 成功，无开放 PR |
| 目标与等级 | patch：Skill 10.11.1；修复测试缺口，State 与 B2 协议保持现有版本 |
| 直接目标 | 按原 B12 与第 14.4 节，连续验收真实合成 accepted primary/analysis → 辅助 modify/reject → 只读影响路径 → 原事务局部 stale → 正式 Figure/旧交付证明拒绝 → 显式修订复核及新证明；核对未受影响主解、模型批准与原来源字节保持有效 |
| Authority | 原 Claim/State/Fragment、Writing Reasoning、accepted qualification、`state_transitions.py`、`sync_project.py`/`project_transaction.py` 与正式 LaTeX/提交证明；测试不新增 Authority |
| 文件白名单 | 新 B2b5 连续验收测试、两份计划进度、Changelog、当前版本载体及其精确版本测试、生成索引；如发现真实缺陷，先记录复现再限定修改相应消费者 |
| 明确不做 | 不新增 mode/Schema，不扩大允许 fragment 种类，不自动清 stale/重算/续签批准，不修改数值或绘图算法、用户项目、旧策略行为；不进入 C1 |
| 兼容与迁移 | 四对既有 policy/mode 与 v4/v5 适用范围不变，无项目迁移；resolved 处置本身不能把 stale fragment 重新确认为 current |
| 验收 | 新连续正反例须使用实际 accepted 来源与原 sync/gate；编译器合成输入和真实编译分开报告。运行专项、全量、lint、索引、精确 head CI、合并树比较和主干复验 |
| 回滚 | 未合并撤回本主题 PR；已存在的项目状态、原 artifact stale、accepted 与批准不因本测试补丁改写 |

版本载体、历史兼容差分的精确版本许可及生成索引须随同一补丁闭合，因此预计超过 20 路径；按测试/计划/载体/生成物四组审查，避免拆出版本不一致的中间提交作为发布状态。B12 连续验收结果完成后补记；Figure 人工语义、跨格式及 B2 总验收仍未完成。

**连续验收发现的限定修复：** 未模拟的 `sync → reproducibility_files → validate_package` 链可复现：正常事务留下 `state/.project_transaction.lock`，打包器把它收入 manifest，随后原 `project_transaction._canonical_relative_name` 正确拒绝将事务内部文件放入证据读集，导致合法复现包失败。白名单增补 `scripts/hsk_pack_submission.py` 与 `tests/test_audit_package_completeness.py`：复用原 `LOCK_RELATIVE_PATH` 常量，仅排除项目根的该精确内部路径；不删除锁、不泛排除同名文件、不隐藏 pending journal，不改变 validator/read-set/事务规则。另把新增真实 XeLaTeX 连续用例接入现有 CI 的生产编译任务。该修复属于同一连续交付验收的必要闭环，保持 patch 等级。


B2b5 实现对应 `tests/test_b2b5_continuous_acceptance.py`：

| 场景 | 行为验收 |
|---|---|
| 辅助 reject 连续链 | 实际 accepted 来源、精确影响路径、State/Framework 局部 stale、resolved 不清 stale、显式修订复核、旧 audit/compile/ZIP 拒绝、新证明及新包通过 |
| 辅助 modify | 实际正式门拒绝、原 writer 精确局部失效、完整消费清单及原数值/批准身份保持；公共恢复路径由 reject 连续链验收 |
| 核心 claim 对照 | 本切片只验证摘要/正文/Figure 消费闭包，不能据此宣布原计划“核心答案否证后返回求解/模型阶段”完整验收关闭 |
| B11 与 B12 并存 | 工作簿目标值不变但其他字节变化，原 artifact/accepted 失效仍保留，辅助局部失效不得覆盖它 |
| 真实 XeLaTeX variant | 同一 reject 链实际编译修前/修后源码，并重建当前 Figure 证明和完整复现包；普通无编译器测试的合成记录不算真实编译 |

合成模型/图片批准为明确 fixture 输入，数值主解及深化由既有合成执行/接受链产生；测试没有实际人工复核或视觉语义判定。测试实现、专项结果、最终 head 全量/CI 与合并后主干复验分开记录于本切片 PR，不凭本段宣称全量验收已经通过。

## 14. B2b6 核心否证返回切片的修改简报

| 项目 | 决定 |
|---|---|
| 当前基线 | B2b5 [PR #248](https://github.com/Vexushi1/mathmodel-skill/pull/248) 已合并至 `main@52502e701ba3e21104db75b3e34661a1bfb60047`；Skill 10.11.1 / State 8.10.0 / B2 合同 1.6.0 / State Transition 1.4.0 / Runtime Assurance 2.2.0 |
| 目标与等级 | 向后兼容 minor：Skill 10.12.0 / State 8.11.0 / B2 合同 1.7.0 / State Transition 1.5.0 / Writing Reasoning 1.9.0 / Runtime Assurance 2.3.0 |
| 可复现缺口 | 当前 `reject` disposition 可以只把论文 fragment 标为 stale，同时仍保留 `result_analysis_status=passed`、accepted solution 与原阶段；若用自由文本 `required_action` 推断影响级别，核心答案或模型有效性否证可能被误作辅助文字重写，形成 fail-open |
| 直接目标 | 为当前 B2 策略增加结构化 `impact_scope` 与受约束 `return_stage`：`auxiliary_wording` 只局部失效；`core_answer` 撤销已接受主结果、标记结果重做并回到 `solve_validate`；`model_validity` 同时撤销语义闭包和模型批准并回到 `model_design` |
| Authority 与写入 | State Schema 定义合法形状，B2 合同定义分类语义，State Transition 定义失效与阶段回退；Runtime Assurance 在 sync 前先按 State Schema 核验精确 1.4.0 策略，再按同一转换 Authority 撤销旧资格，并将两项 Authority 纳入运行时指纹；现有 `sync_project.py` / `project_transaction.py` 事务统一写入 fragment stale、`redo_required`、阶段回退及跨问传播，不另设第二 writer |
| 兼容与迁移 | 只有精确 `1.4.0/enforce_latex_text_and_figure_chain` 采用结构化否证；旧 `1.0.0`—`1.3.0` 项目保持原行为，不自动迁移。新策略下当前 modify/reject 缺少影响分类须 fail closed，不从自然语言猜测核心程度 |
| 明确不做 | 不重算数值、不运行求解或绘图、不自动清 stale、不续签模型或结果批准、不修改算法或用户项目；不扩展 DOCX、单文件/动态/复杂宏 TeX，不进入 C1，不发布 Release |
| 验收条件 | 覆盖三类否证、缺字段拒绝、核心与模型回退、多个否证时 `model_design` 优先、跨问传播、`redo_required` 粘性、真实分析结论失败回执、resolver 下一门、正式 Figure/旧交付证明拒绝，以及旧策略兼容；专项、全量、lint、索引、精确 head CI、合并树比较和主干复验须分别形成证据 |
| 回滚 | 未合并撤回本主题改动；已选 1.4.0 的项目保留其结构化否证与 stale 事实，不能通过删除分类、降级策略或改写自然语言伪装通过 |

本节只关闭“核心答案或模型有效性被否证后应返回哪里、哪些资格必须撤销”的结构化状态链。Figure 视觉充分性与图注整体语义、DOCX、单文件/动态/复杂宏 TeX、跨格式闭包和 B2 的 B01/B09—B12/B16 总验收仍待后续独立证据；在这些项目关闭前，B2 继续标记为进行中，C1 保持未开始。

## 15. B2c 跨载体消费与总验收的修改简报

| 项目 | 决定 |
|---|---|
| 当前基线 | B2b6 [PR #249](https://github.com/Vexushi1/mathmodel-skill/pull/249) 已合并至 `main@86fedb04fa4ace5ce27ba5f65a804ab82b306f09`；Skill 10.12.0 / State 8.11.0 / B2 合同 1.7.0，旧 `1.0.0`—`1.4.0` 策略保持原语义 |
| 目标与等级 | 向后兼容 minor：Skill 10.13.0 / State 8.12.0 / B2 合同 1.8.0 / State Transition 1.6.0 / Writing Reasoning 1.10.0 / Runtime Assurance 2.4.0；新增精确 `1.5.0/enforce_selected_paper_claim_chain`，不自动迁移旧项目；后三者只扩展新策略对既有结构化否证语义的继承，不改变事件或判断含义 |
| 可复现缺口 | 显式 DOCX 交付当前只检查文件存在，未现场消费 B1/fragment；静态单文件 TeX 已可扫描却被旧正式门按“至少两个活动文件”拒绝；动态或复杂宏 TeX 只有分散的未核验反例，尚未纳入 B2 总验收；B16 的机器链与人工视觉/语义边界尚未形成一张完整验收矩阵 |
| 直接目标 | 项目显式选择一个论文载体后，以同一 B1、paper fragment、Figure binding 与现有批准 bundle 为 Authority：有界只读核验模块化/单文件静态 LaTeX 或 DOCX OOXML 的实际正文消费和 Figure 身份；对动态包含、宏生成 claim/caption、DOCX 动态字段/修订等不可确定结构 fail closed；按 B01、B09—B12、B16 形成跨载体连续验收并关闭 B2 台账 |
| Authority 与集成 | State Schema 只定义新 opt-in 形状；B2 合同定义载体能力和结果边界；B1 accepted 来源、Writing Reasoning、Figure Evidence、State Transition 与原项目事务保持单一事实源。显式 `docx`、`latex`、`submission` scope 由现有 project sync 消费同一只读门，不新增写入器 |
| Figure 人工边界 | B2 只验收机器链会消费已有 `approved_figures` 与 current `figure_bundle`，并始终把视觉充分性、图注整体语义和人工语义覆盖分列为 `not_assessed`；真实项目仍须按 Module 04 与最终人工审查查看当前图片和 caption。不得新增作者可自签的语义 PASS、独立审查回执或第二套图形状态体系，C1/C2 职责不提前实现 |
| 兼容与迁移 | `1.0.0`—`1.4.0` 的激活、静态模块化范围、结构化否证与 v4/v5 证明行为不变；新策略必须声明单一 `paper_source`，未知/残缺/错配载体 fail closed。动态或复杂宏只在相关 fragment、caption 与图片关系仍可字面且唯一核对时允许继续，否则明确阻断，不宣称通用 TeX 宏求值 |
| 明确不做 | 不重算数值、不执行求解/绘图、不生成或修改用户论文、不续签图片批准、不自动判断审美/数学语义、不创建 C1 回执、不进入 C/D/E、不发布 Release |
| 验收条件 | B01、B09—B12、B16 覆盖模块化 TeX、单文件 TeX、DOCX 与动态/复杂结构的正反例；DOCX 追踪修订、字段、外部关系、ZIP/路径预算和读集漂移必须 fail closed；Figure ID→脚本→accepted 来源→当前批准图片→caption/正文引用闭合；旧策略差分、状态传播、正式 gate、编译/包重放、只读性、lint、全量、索引、精确 head CI、合并树比较和主干复验分别形成证据 |
| 回滚 | 未合并撤回本主题改动；已显式选择 1.5.0 的项目保留可解释记录并回到人工复核，不能删除载体声明或降级策略来伪装旧路径通过 |

复杂宏与动态包含的“覆盖”是可判定边界验收：不受相关动态结构影响且可证明为新建、显式调用的字面宏可以在活动载体内核对；动态命名、控制符定义、无界重定义、前言/全局渲染副作用，或宏直接生成或改变 claim、caption、图片关系时必须失败或要求人工，不把编译成功、PDF 存在或人工职责写成机器语义 PASS。DOCX 的 Figure 绑定还必须由规范 DrawingML picture 子树、当前批准图片的逐字节哈希、同一书签内的 caption 和指向该书签的正文内部超链接共同证明；图表、SmartArt、自动编号、替代 SVG/备用表示、错位 blip 或任意同文字符串都不能替代这条关系。B2 完成表示上述行为和边界均有实际测试与 CI 证据，不表示任一具体用户项目已经完成视觉审阅。
