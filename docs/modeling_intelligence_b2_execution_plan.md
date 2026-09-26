# B2 主张消费与片段失效：接续实施指南

> 阶段指南，不是运行时 Authority。B2 的只读审计、状态写入、正式门禁和跨格式覆盖须分别以实际提交、测试和 CI 证明；完成首个切片不等于完成 B2。

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

B2a 的 Schema/合同、位置 scanner、现场 B1 组合审计、显式路由、合成反例与版本载体已在独立分支实现；合并资格仍取决于精确 head 的全量回归和 CI。下一动作是完成该验收，再单独裁决 B2b 的状态写入及正式门。C/D/E 保持未开始。
