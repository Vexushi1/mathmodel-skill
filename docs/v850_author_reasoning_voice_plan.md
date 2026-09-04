# v8.5.0 Author Reasoning Voice 细化升级计划

> 状态：实施参考 / Scope Contract  
> 基线：`main` v8.4.0  
> 工作分支：`upgrade/v8.5.0-author-reasoning-voice`

## 1. 目标

v8.4.0 已允许有依据的作者判断、自然发问与适度第一人称。本轮不重新引入“口语化写作”，而把作者声音细化为**可核查的建模认知行为**，形成更适合高水平本科数学建模论文的自然、朴素、严谨表达。

核心原则：

```text
作者声音 != 第一人称词频
作者声音 = 可核查的观察、发问、判断、选择、简化、引入、推导、解释、检验与限定
```

目标包括：

1. 建立 Author Reasoning Speech Acts；
2. 建立 Question Closure；
3. 建立 Claim Strength / Evidence Alignment；
4. 明确“我们 / 本文 / 数学对象主语”的功能分工；
5. 建立 Reasoning Necessity 与 Problem-Specificity 两个语义自检；
6. 保留本科生自然探究感，但不牺牲公式、数据、证明、引用和验证边界；
7. 简单解析或直接计算问题继续允许“不改”。

## 2. 非目标

本轮明确不做：

- “我们/本文”出现次数或比例门槛；
- `first_person_ratio`、`human_like_score`、`AI_like_score`；
- 作者身份或 AI 使用情况推断；
- 固定句式轮换表、连接词词库或优秀论文原句复制；
- 强制每段提问、每个公式写“我们可以得到”；
- 为制造“人工感”编造团队共识、失败实验或试错时间线；
- 仅因文风问题新增 Hard Fail；
- 修改模板、绘图、模型审批、数值验收、工作簿或命题/伪代码载体规则。

## 3. Single Source of Truth

```text
core/writing_reasoning_contract.yaml
        ↓ 跨题型语义边界
modules/05_writing/paper_writing_protocol.md §7.3
        ↓ 普通正文执行 Authority
modules/05_writing/references/model_solution_reasoning_examples.md
        ↓ 仅示例，不新增规则
ai_cleanup.md / modules/06_review_delivery.md
        ↓ 消费，不复制第二套 Authority
```

## 4. Author Reasoning Speech Acts

统一定义 11 类功能：

1. `observation`：观察 current 数据、图像、结构或结果；
2. `open_question`：暴露当前尚缺的量、关系或判据；
3. `inquiry`：把观察转成后续可执行验证问题；
4. `judgment`：基于已有证据作建模判断；
5. `choice`：解释为什么选择当前变量、方案、指标或 solver；
6. `reduction`：解释降维、候选域缩减或问题转化；
7. `introduction`：解释引入变量/函数/指标解决的真实缺口；
8. `derivation`：承接真实推导，不能跨过关键步骤；
9. `interpretation`：说明公式/结果的下游数学作用；
10. `validation`：明确正在挑战哪个风险或 claim；
11. `qualification`：限定结论的样本、参数、假设与证据边界。

这些类别是语义 repertoire，不是句式模板，也不要求逐类出现。

## 5. Question Closure

正文主动提出的问题必须满足以下之一：

```text
Question -> Mathematical Operation -> Result -> Answer
```

或明确指向已规划的真实 validator；若当前证据不足，则保留为未验证问题，不得补造答案。

禁止：

```text
“我们希望知道模型是否稳定”
-> 无检验
-> “模型具有良好稳定性”
```

## 6. Claim Strength Alignment

作者声音不改变证据等级：

1. 数学事实：证明/严格推导，直接陈述；
2. 数据事实：current 图表/数值，直接报告；
3. 有证据支持的建模判断：可用“我们认为”；
4. 解释性推测：必须限定范围；
5. 待验证猜想：只作为后续任务或未决方向。

原则：

```text
prose_claim_strength <= available_evidence_strength
```

“我们认为”不能把启发式解变成全局最优，也不能把图像共现变成因果。

## 7. 主语功能分工

- “我们”：局部观察、判断、取舍、探究与检验；
- “本文”：研究范围、论文整体方法与贡献；
- 对象/结果主语：已经证明的数学事实与已经核验的数据事实。

不机械执行“我们→本文”或“无人称→我们”，不设置 pronoun quota。

## 8. 两个语义自检

### Reasoning Necessity

删掉作者声音句后，是否会丢失：

- 变量/约束选择理由；
- 简化依据；
- solver 适配理由；
- 当前缺口；
- 公式下游作用；
- validation 目标；
- claim 边界。

若全部不丢失，则压缩、换主语或删除。

### Problem-Specificity

替换研究对象后，如果句子仍能原样用于任何赛题，则优先视为模板化空话，应回到本题机制、数据结构、约束或评价目标重写。

## 9. 口语化边界

允许自然，不允许聊天。

“说白了、我们觉得、大家都知道、为了更好地解决问题”等不是机械禁词，但若没有可恢复的数学信息，应压缩或删除。

清理时采用：

```text
Keep / Compress / Re-subject / Delete
```

并明确“不改”也是合法结果。

## 10. 实施文件

核心修改：

- `core/writing_reasoning_contract.yaml`
- `modules/05_writing/paper_writing_protocol.md`
- `modules/05_writing/references/model_solution_reasoning_examples.md`
- `modules/05_writing/ai_cleanup.md`
- `modules/06_review_delivery.md`

测试：

- 保留并更新 `tests/test_v831_author_reasoning_voice.py`
- 保留并更新 `tests/test_v840_author_reasoning_writing.py`
- 新增 `tests/test_v850_author_reasoning_speech_acts.py`
- 新增 `tests/fixtures/writing_reasoning_voice_cases.yaml`

实施后新增：

- `docs/v850_author_reasoning_voice_evaluation.md`

## 11. 固定测试情境

至少覆盖：

- 已证明单调性：不应用“我们认为”降低事实强度；
- 有限候选枚举：solver 理由必须恢复候选完整性；
- 预测局部误差：平均指标不能掩盖局部最大误差；
- 启发式最好解：不能升级全局最优；
- 空间共现：可以提出猜想，不能直接因果化；
- 逐期供给：自然作者声音解释局部约束必要性；
- 直接热平衡：不强行加入第一人称和追问；
- 无团队记录：禁止编造“我们一致认为/反复尝试”。

## 12. 验收与失败条件

通过条件：

- Author Voice 已成为认知行为体系，而不是词频体系；
- Question Closure、Claim Strength、Reasoning Necessity、Problem-Specificity 可恢复；
- “我们/本文/对象主语”均合法；
- 不产生固定句式轮换；
- 不降低原 Formula、Algorithm、Proof、Citation、Numerical Evidence 与 Global Optimum 门禁；
- 简单问题不膨胀；
- Runtime 不新增无必要 stage，examples 不进入 startup preload；
- 旧章节、模板、命题、伪代码与数值/模型契约保持保全。

出现以下情况暂停合并：

- 按代词词频评分；
- 生成固定句式轮换器；
- 批量删除或插入第一人称；
- 图像观察被写成因果；
- 启发式因“我们认为”升级全局最优；
- 编造团队经历；
- 用 regex 冒充语义正确性判断；
- 无授权修改模板、绘图、模型或数值系统。

## 13. 最终判据

每个作者声音句都回答五个问题：

1. 它是否承担真实建模认知动作？
2. 删除后是否会丢失必要理由？
3. 提出的问题是否有数学去向？
4. 主张强度是否不超过证据？
5. 是否包含本题特异信息而非跨题套话？

最终目标：

> 评委能够看出作者在观察什么、疑惑什么、为什么作出选择、怎样把问题转成数学关系、如何验证自己的判断；但全文仍由模型、公式、数据、算法和证据主导，而不是由“我们认为”主导。
