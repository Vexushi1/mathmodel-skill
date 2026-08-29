# 模型建立与求解写作风格硬化计划（WRT-02）

> 状态：PLANNING ONLY / 仅建立实施上下文，尚未修改活动写作语义  
> 适用仓库：`Vexushi1/mathmodel-skill`  
> 基线 Skill：`7.17.0`  
> 基线 `main`：`c9dc64aa81164717e332027842eb17b304faee9a`  
> 工作分支：`upgrade/v7.18.0-model-solution-writing-style`  
> 预期目标版本：`7.18.0`（新增向后兼容的写作能力，实际版本升级只在实现与测试通过后执行）  
> 修改主题：只强化“模型建立—模型求解—结果解释”的数学建模论文叙事、标题、衔接和语言风格；不修题意、公式、约束、算法或数值语义本身。  
> 主要参考材料：用户提供的国赛优秀论文 `A066.pdf`、`A196.pdf`，以及用户提供的“模型的建立 / 模型的求解”提示词。  

---

## 1. 修改简报

```text
修改主题：Model Establishment & Solution Writing Style Hardening
当前版本：7.17.0
目标版本：7.18.0（暂定，待语义实现与完整测试通过后再正式 bump）
变更等级：minor / writing behavior only
直接目标：让模型建立与求解部分从“信息完整但报告式、公式块式、算法介绍式”升级为“连续推演、自然衔接、专业标题、结果邻接解释”的国赛论文式正文
明确不做：不改变题意、变量、公式、约束、模型选择、Model Approval、03A/03B、数值验证、Python/MATLAB 分工、Workbook Schema、Project State、Router、Task Taxonomy、LaTeX 模板结构
权威事实源：core/writing_reasoning_contract.yaml（新增写作叙事权威）；modules/05_writing/latex.md（正文落地）；modules/05_writing/ai_cleanup.md（表现层风险审计）
预计修改文件：core/writing_reasoning_contract.yaml、modules/05_writing/latex.md、modules/05_writing/ai_cleanup.md、tests/test_v718_model_solution_writing_style.py；必要时 PROJECT_INSTRUCTIONS.md 做轻量入口摘要；正式 release 时再同步版本载体和 CHANGELOG
禁止触碰文件：core/task_taxonomy.yaml、core/model_approval_contract.yaml、core/numerical_verification_contract.yaml、core/workbook_schema.yaml、core/project_state.schema.yaml、scripts/resolve_runtime.py、modules/02_model_design.md 的数学语义、modules/03_result_analysis.md、Python/MATLAB/LaTeX 模板主体
兼容性要求：旧项目无需迁移；旧框架无需新增必填字段；不新增生命周期 Gate；不新增模型审批字段；不要求重跑已 accepted 的数值结果
迁移要求：无 Schema / CLI / Workbook / Project State 迁移
验收测试：Authority 唯一性 + 写作行为回归 + 旧 v7.17 写作测试 + 全量 Python 3.10--3.14 + Static lint + Generated contract + 三套 LaTeX + Production attestation
回滚方式：回退 writing_reasoning_contract / latex / ai_cleanup 的新增叙事规则和对应测试；不触发模型、结果、工作簿或项目状态 stale
```

---

## 2. 本轮真正要解决的问题

本轮不把“模型建立写得不好”误判为模型数学语义错误。

v7.17.0 已经能较严格地保证：

- 模型语义闭合；
- Formula Trace 有来源、推导、去向；
- 优化模型有决策变量、目标函数、约束与 Model/Solver/Validator 分离；
- solver 第一次出现有适配理由；
- 结果有图表、工作簿和 claim evidence；
- AI Cleanup 会删除算法百科、空泛评价和模板化元话语。

但当前写作层仍可能产生以下问题：

1. **段落之间像“技术报告拼接”，不像连续数学论证。**
   - 一段讲变量；
   - 下一段突然给公式；
   - 再下一段突然介绍算法；
   - 结果单独放表；
   - 每一块各自正确，但读者不知道为什么此时需要下一块。

2. **模型建立容易重复前面的“问题分析”和“模型假设”。**
   - 再次重述题目；
   - 再次解释难点；
   - 再次写“为了简化问题作如下假设”；
   - 导致正文冗余，真正数学建立反而被稀释。

3. **公式前后语言信息密度不足。**
   - 公式前只有“根据相关理论可得”；
   - 公式后只翻译符号；
   - 缺少“当前还缺什么”“得到该关系后问题怎样推进”。

4. **Solver 语言仍可能是“算法先行”。**
   - “本文采用粒子群算法……”直接开场；
   - 写一段算法优点；
   - 没有先交代目标函数结构、是否可导、维度、离散性、搜索域、可利用性质和直接法为何不足。

5. **标题虽然数量受控，但命名仍可能泛化。**
   - “模型建立”“模型分析”“参数处理”“算法设计”“结果说明”；
   - 看标题无法知道该节具体处理了什么数学对象或数学动作。

6. **结果与解释分离。**
   - 表格/图片先堆积；
   - 后面统一写一段“由图可知”；
   - 没有做到关键结果出现后立即解释实际决策、约束满足、机制原因和设问含义。

7. **AI Cleanup 偏重“删坏话”，缺少“保留必要衔接”的正向准则。**
   - “下面进行求解”应该删；
   - “由于目标函数由离散遮蔽判据积分得到，难以直接求导，因此采用无梯度搜索”则必须保留；
   - 当前还缺少清晰的功能区分。

本轮的核心目标 therefore 是：

```text
不改变“写什么”
→ 明确“这些正确内容应该怎样连续写出来”
→ 让正文读起来像完整的数学建模推演，而不是模型合同的逐项转写
```

---

## 3. 两篇优秀论文的写作方法研究结论

### 3.1 A066：长链条模型建立的“对象—关系—判定—目标—求解”推进

重点参考范围：正文第 5 部分“模型的建立与求解”及后续各问，约 PDF 第 5--33 页。

可迁移的写作特征：

1. **先恢复研究对象的状态，再推进目标量。**
   - 导弹、无人机、烟幕弹分别建立运动关系；
   - 得到位置后才进入有效遮蔽判定；
   - 判定完成后才定义有效时长；
   - 有效时长再进入优化目标。

2. **公式之间存在下游关系。**
   正文不是“公式 1、公式 2、公式 3”的集合，而是：

   ```text
   位置关系
   → 相对几何关系
   → 遮蔽成立条件
   → 时间指示/时长
   → 优化目标
   ```

3. **方法介绍服务当前问题，而不是独立百科。**
   算法说明通常紧邻当前计算困难、变量和目标，不先写通用算法历史。

4. **结果图后有即时解释。**
   速度、时刻、投放参数与有效时长之间的变化关系会在相邻位置解释，不完全推迟到章节结尾。

5. **后问主要写新增结构。**
   已经建立的运动关系会复用，后问更多增加新变量、新目标或新组合约束，而不是从零重新解释所有物理关系。

应吸收：连续推进、公式用途、局部结果解释、跨问增量。  
不应复制：具体烟幕弹对象、具体公式、Case 编号、Step 句式、流程图形式或任何题目专属措辞。

### 3.2 A196：模型准备—结构证明—算法引出的“数学结构先于求解器”写法

重点参考范围：

- PDF 第 5--10 页：模型准备、运动轨迹、有效遮挡判定；
- PDF 第 11--16 页：问题一建立与求解，包含有效时长模型、连续区间说明、二分搜索、圆周离散、精度验证、结果展示；
- PDF 第 17--24 页：问题二优化模型、目标/约束与求解策略；
- PDF 第 25--33 页：多无人机、多烟幕、多目标的增量式模型建立和求解。

可迁移的写作特征：

1. **共享关系先集中建立，单问正文只写增量。**
   轨迹关系、有效遮挡的几何定义等先形成共同基础，避免问题一到问题五重复推导。

2. **算法出现之前先解释数学结构。**
   例如先论证有效遮蔽时间区间的结构，再把求解转成边界时刻定位，之后才自然引出二分搜索。

3. **必要的命题/几何论证承担“把问题变简单”的作用。**
   证明不是装饰，而是用于离散化、降维或把连续空间判定转换为有限检查。

4. **求解写作不是“调用算法”，而是“把模型变成可计算步骤”。**
   可读顺序更接近：

   ```text
   当前模型结构
   → 哪一部分难直接求
   → 利用什么性质简化
   → 搜索/离散/迭代怎样执行
   → 精度怎样控制
   → 结果怎样解释
   ```

5. **标题多用具体数学任务命名。**
   如轨迹、判定式、有效时长、起止时刻求解、搜索寻优等，标题能直接告诉评委本节在处理什么对象。

6. **结果展示紧跟定量分析和必要验证。**
   不是只报最优值，而会说明参数组合、有效时长、不同算法或不同离散精度之间的关系。

应吸收：共享基础、数学结构先于算法、算法由困难自然引出、专业标题、结果邻接解释。  
不应复制：该论文的章节编号、烟幕弹专属命名、二分法/PSO/GA 作为固定算法模板、具体句式与数值。

### 3.3 两篇论文共同体现的核心风格

两篇论文虽然技术细节不同，但共同表现出以下“国赛建模正文”特征：

```text
不是“作者介绍模型”
而是“问题对象经过数学化后自然向下一关系推进”
```

常见逻辑不是：

```text
本文建立 A 模型。
本文建立 B 模型。
本文采用 C 算法。
最后得到 D 结果。
```

而是：

```text
已得到 A
→ 为确定 B 还需要 C
→ 根据当前机制得到 C
→ C 使 B 可计算/可判定
→ 由此问题转成 D
→ D 的结构决定采用 E 求解
→ 得到 F 后立即解释其现实/数学意义
```

本轮 Skill 优化必须学习这种**逻辑功能**，不能学习固定句式。

---

## 4. 用户提示词中应吸收的要求

用户给出的提示词不是直接作为 runtime prompt 写入 Skill，而应抽象为以下长期规则。

### 4.1 必须吸收

1. **模型建立与求解只写本阶段内容。**
   - 不重复“问题分析”；
   - 不重新列“模型假设”；
   - 不重新大段重述题目。

2. **整合思路，必要步骤不能遗漏。**
   - 删除重复定义和重复说明；
   - 保留决定模型推进、算法选择、结果解释的步骤。

3. **模型建立与模型求解之间需要自然衔接。**
   - 不是额外加“下面进行求解”这种管理句；
   - 而是通过模型的可计算结构自然进入 solver。

4. **小节数量不能过多，但过程必须清楚。**
   - 二级/三级标题服务独立数学任务；
   - 不按“变量 / 目标 / 约束 / 参数 / 结果”机械切碎。

5. **标题专业、简洁、可恢复内容。**
   - 优先“对象 + 数学关系/数学动作”；
   - 例如“有效遮蔽条件的构造”“边界时刻的求解”“投放参数的联合优化”；
   - 避免“模型处理”“算法设计”“结果说明”等空泛标题。

6. **结果出现时要有适当分析。**
   - 最优值后解释对应决策；
   - 图后解释关键趋势/阈值；
   - 表后解释约束、机制或设问含义。

7. **语言要符合数学建模论文，不写成熟期刊式概念包装。**
   - 规范、具体、朴素；
   - 专业术语稳定；
   - 保留清晰的推理路径。

### 4.2 不直接吸收为硬规则

以下内容不得机械化：

- “越详细越好”；
- 每个模型必须单独写方法介绍；
- 每个问题必须放流程图；
- 每个公式必须有固定两句解释；
- 所有标题都使用“XX 的建立 / XX 的求解”；
- 所有求解都使用 Step 1...n；
- 所有结果都套“由图可知—结果表明—因此”；
- 固定使用 A066/A196 的章节结构。

原因：本轮目标是提高连贯性，而不是创造新的模板感。

---

## 5. 拟新增的正文叙事权威

建议在 `core/writing_reasoning_contract.yaml` 中新增一个统一的写作层权威，暂定名称：

```yaml
model_establishment_solution_narrative:
```

其下包含若干子规则。名称可在实施时微调，但**不得拆成多个互相竞争的 Authority**。

### 5.1 Continuous Mathematical Narrative

目标：模型建立按数学任务自然推进，而不是按合同字段罗列。

默认叙事链：

```text
承接当前对象/上一关系
→ 指出当前还需要确定的量或判据
→ 引入必要数学对象
→ 建立/推导关系
→ 说明该关系改变了什么
→ 导向下一关系、最终模型或求解
```

要求：

- 一个段落可包含“解释 + 公式 + 下游用途”，不要求公式一段、解释一段；
- 相邻公式若服务同一数学任务，优先连续推演；
- 不用“首先建立 XX 模型、其次建立 YY 模型”代替真实数学关系；
- 不要求每个关系都命名成一个“模型”。

### 5.2 Problem-analysis / Assumption Separation

进入“问题 X 模型建立与求解”后：

默认禁止重复完整的问题分析和模型假设。

允许的开场信息只有当前数学推进真正需要的短承接，例如：

```text
根据前文分析，有效时长取决于 A、B、C 的时空关系，因此先确定三者的状态方程，再建立有效判定。
```

允许局部重申某个假设的**后果**，但不重新列假设本身。例如：

```text
在忽略空气阻力的假设下，烟幕弹释放后的竖直运动可按抛体关系表示为……
```

不允许：

- “本问题要求……”重新重述题目；
- “本问题难点是……”重新写问题分析；
- “为了简化问题，作如下假设……”重新列模型假设。

### 5.3 Formula Prose Rhythm

核心公式正文表现采用五步节奏，但不是固定句式：

```text
Need：为什么此时需要该关系
→ Basis：依据哪个对象/机制/前式
→ Formula：给出关系
→ Meaning：说明它在数学上/现实上表达什么
→ Consequence：说明它使下一步变成什么
```

其中 Need / Basis / Meaning / Consequence 可以合并，不要求四句齐全；但核心公式周围至少要让读者恢复“为什么出现”和“出现后做什么”。

重点禁止两类低价值文字：

1. 公式前：
   - “根据相关理论可得”；
   - “由数学知识可知”；
   - 没有具体来源的“显然有”。

2. 公式后：
   - 已经定义过符号后再次逐个翻译符号；
   - 只写“式（x）即为所求模型”；
   - 没有说明该式如何进入后续判定、目标、约束或算法。

优先的公式后解释是：

```text
由此，原连续空间判定被转化为两个临界时刻的定位问题。
```

而不是：

```text
其中 t1 为开始时刻，t2 为结束时刻。
```

如果符号确实第一次出现，则先定义，再解释结构作用。

### 5.4 Transition Function Governance

不建立“推荐连接词词库”，只定义衔接句允许承担的逻辑功能。

模型建立与求解中的过渡句应至少承担以下一种作用：

1. `inherit`：承接上一关系；
2. `gap`：指出当前缺少哪个量/判据；
3. `introduce`：引入新的数学对象；
4. `transform`：说明问题被转化/化简成什么；
5. `solve_entry`：由模型结构自然进入数值求解；
6. `result_entry`：由算法执行进入结果证据；
7. `interpret`：由结果进入机制/设问解释；
8. `increment`：后问说明继承什么、新增什么。

低价值元话语：

- “下面建立模型”；
- “下面进行求解”；
- “接下来分析结果”；
- “为了更好地解决问题”；
- “本节主要研究……”。

这些句子只有在同时承担上述实质逻辑功能时才保留。

### 5.5 Professional Heading Semantics

标题按照**独立数学任务**划分，不按照论文元素划分。

优先模式：

```text
研究对象 + 数学关系/动作
```

可使用的动作类型包括但不限于：

- 确定 / 表征 / 构造 / 推导 / 判定；
- 离散 / 降维 / 分解 / 转化；
- 估计 / 求解 / 搜索 / 优化 / 校准；
- 验证 / 比较 / 灵敏度分析（仅确有独立证据任务时）。

较好：

```text
烟幕云团运动轨迹的确定
有效遮蔽条件的构造
临界边界时刻的求解
投放参数的联合优化
有效时长的计算与验证
```

较差：

```text
模型分析
模型处理
参数处理
算法设计
结果说明
```

不建立机械语法检查“标题必须含 的 / 必须名词+动词”，机器只能对泛化标题给 review 提示。

### 5.6 Subsection Granularity for Model/Solution Narrative

保留现有“复杂问题约 3--4 个主要二级小节”的 Default，不新增硬上限。

新增原则：

```text
标题对应独立论证单元，而不是对应一个公式、一类变量或一个论文合同字段。
```

默认不机械拆成：

```text
决策变量
目标函数
约束条件
模型汇总
算法介绍
参数设置
```

如果这些本来属于一条连续模型建立链，应在“模型建立”或一个更具体的对象标题下连续完成。

三级标题是否出现由以下条件决定：

- 是否存在独立数学任务；
- 是否需要单独引用图/命题/算法；
- 是否不拆分会导致正文过长且难以恢复论证结构。

不得为了标题整齐而拆分。

### 5.7 Solver Narrative

第一次引入主 solver 时，正文顺序默认强化为：

```text
当前模型结构/计算困难
→ 可利用的性质或已完成的化简
→ 为什么直接解析法/常规方法不足（若确实不足）
→ 当前算法族为什么适配
→ 本题中的变量编码/搜索对象/约束处理
→ 参数、精度、停止或收敛条件
→ 输出如何回到模型变量
```

禁止：

```text
本文采用 PSO/GA/DE/ALNS……
该算法具有全局搜索能力强、收敛速度快等优点。
```

作为算法段的主要内容。

方法介绍的篇幅由当前问题决定：

- 标准算法、无修改：只写与本题有关的变量、更新对象、参数和停止规则；
- 算法本身经过改进：说明改了什么、为什么改、对应什么模型困难；
- 结构性求解方法（二分、分解、动态规划、解析边界）：优先说明数学性质与可计算结构，而不是算法百科。

### 5.8 Model-to-Solver Bridge

在模型建立末尾进入求解时，不使用纯管理句。

桥接句至少回答以下之一：

- 最终模型是什么类型；
- 哪个结构导致需要数值求解；
- 哪个性质允许使用特定算法；
- 哪些变量构成搜索空间；
- 哪个目标/判据由 solver 直接评价。

例如可生成类似（仅示意，不作为固定模板）：

```text
至此，投放参数与有效遮蔽时长之间的映射已经闭合。由于目标值需通过逐时遮蔽判定计算，难以获得便于直接求导的显式表达，因此后续采用无梯度搜索对四个连续决策变量进行联合优化。
```

机器不得要求出现“至此”等特定词。

### 5.9 Result-adjacent Interpretation

关键结果出现后，应在邻近位置完成解释，不把所有分析集中到章节末尾。

#### A. 单点最优/参数结果

优先链：

```text
关键数值/参数组合
→ 对应实际决策含义
→ 主要约束是否满足
→ 为什么该组合在模型机制上合理
→ 直接回答设问
```

#### B. 曲线/图像结果

优先链：

```text
关键趋势/极值/拐点/区间
→ 关键数值
→ 形成该现象的模型原因
→ 对最终决策/结论的影响
```

#### C. 算法对照/精度结果

优先链：

```text
比较指标
→ 差异量
→ 是否改变主结论
→ 该证据 support / modify / reject 哪个 claim
```

不要求每张图都机械重复完整五步；但核心结果不能只靠 caption 存在。

### 5.10 Cross-question Narrative Progression

在已有 `shared_foundation` / `cross_question_progression` 基础上增加语言层要求：

后问开头只需短句恢复增量：

```text
在问题二已有运动关系的基础上，本问进一步允许三架无人机分别选择投放参数，因此新增……
```

不重新完整推导共同轨迹、共同概率关系、共同网络结构。

若后问改变了前问关键机制，则明确指出“继承部分”和“失效/新增部分”，不能用“同理”掩盖真实结构变化。

---

## 6. 数学建模论文语言风格的正向定义

本轮不通过大量禁词定义风格，而要给生成端一个正向目标。

### 6.1 目标风格

```text
具体对象
→ 明确数学困难
→ 直接数学处理
→ 关系的作用
→ 下一步或结果
```

语言应当：

- 规范；
- 朴素；
- 专业；
- 有本科竞赛论文的推理痕迹；
- 不用成熟期刊式宏大包装；
- 不把软件、算法名和“创新”当作语言中心。

### 6.2 主语优先级

优先让句子的主语是：

- 当前对象；
- 当前关系；
- 当前条件；
- 当前结果；
- 当前数学任务。

减少连续多句以“本文 / 本问 / 该模型 / 我们”作为主语。

示意：

较弱：

```text
本文首先建立无人机运动模型。然后本文建立烟幕运动模型。最后本文建立遮蔽模型。
```

较强：

```text
无人机在投放前保持定高直线飞行，其位置可由初始位置和航向速度直接确定。烟幕弹脱离无人机后还受到重力作用，因此其轨迹需进一步按释放后的运动阶段描述。得到云团中心位置后，即可继续判断其与目标视线之间是否形成有效遮蔽。
```

该示例仅用于规则解释，不作为必须复用的句式。

### 6.3 分析语句的最低信息量

“适当分析”必须带来新信息，至少完成一种：

- 解释公式为何需要；
- 解释参数/约束来源；
- 说明结构被化简；
- 说明算法为何适配；
- 解释结果为何合理；
- 说明结果怎样回答设问；
- 说明边界/异常如何影响结论。

以下内容不算有效分析：

- “结果较好”；
- “模型有效”；
- “算法性能优异”；
- “由图可知变化明显”；
- “符合实际情况”但没有具体机制或基线。

---

## 7. AI Cleanup 的调整方向

`modules/05_writing/ai_cleanup.md` 不新增第二套 Authority，只消费新的 narrative contract。

### 7.1 新增应检查的表现风险

1. `report_like_model_listing`
   - 连续出现“建立 A / 建立 B / 采用 C”但无数学承接。

2. `formula_without_need_or_consequence`
   - 核心公式前后只有符号解释，没有当前需求与下游用途。

3. `solver_first_narrative`
   - 求解小节第一信息是算法名，当前数学困难和可利用结构缺失。

4. `generic_heading_density`
   - 大量“模型分析 / 参数处理 / 算法设计 / 结果说明”等泛标题。

5. `management_transition`
   - “下面进行……”“本节主要……”高密度，但不承担逻辑功能。

6. `detached_result_interpretation`
   - 核心图表/最优值附近没有解释，分析被统一推迟或缺失。

7. `repeated_problem_analysis_in_model_section`
   - 模型建立开头重新完整复述设问、难点和假设。

### 7.2 明确不能误杀

- 有实际逻辑作用的过渡句不能因为包含“因此 / 进一步 / 下面”就删；
- 结果附近为解释机制而重复一个关键数值是允许的；
- 复杂模型中必要的局部方法说明不能因“算法介绍”标签全部删除；
- 标题数量超过默认建议不能自动判错；
- 机器不得仅凭词汇猜测一段是否“像优秀论文”。

---

## 8. `latex.md` 的落地修改建议

实现时优先在现有章节中增强，不无节制增加新章节。

建议重点修改：

### 8.1 4.6 模型推导

在现有 Source → Derivation → Destination 后增加正文表现层：

```text
需求/承接 → 建式依据 → 公式 → 结构含义 → 下一用途
```

强调“公式后的结构作用优先于符号翻译”。

### 8.2 4.7 模型名称、优化模型建立与角色分离

保留现有数学完整性规则；增加：

- 模型建立不重复问题分析和假设；
- 决策变量/目标/约束应在同一连续论证链中组织；
- 标题按独立数学任务划分，而不是按合同字段划分。

### 8.3 4.9 求解段与算法流程

强化 solver narrative：

```text
结构/困难 → 可利用性质 → 算法需求 → 本题实现 → 参数/终止 → 输出
```

加入 Model-to-Solver Bridge。

### 8.4 4.11 求解结果

增加 result-adjacent interpretation，区分：

- 单点最优；
- 图像趋势；
- 算法/精度验证。

### 8.5 4.13 学术表达

把“证据驱动的本科生学术表达”进一步落到模型建立与求解：

- 主语从“本文”转向对象/关系；
- 分析句必须推进数学或证据；
- 不建连接词词库；
- 不照搬优秀论文句式。

### 8.6 4.14 小节颗粒度

加入 heading semantics：

- 标题对应数学任务；
- 泛化标题只 review；
- 不按变量/目标/约束机械拆三级标题。

---

## 9. 是否修改 DOCX 模块

默认 **不在第一轮修改 `modules/05_writing/docx.md`**。

原因：DOCX 已明确只负责载体和排版，正文内容统一服从 LaTeX + reasoning contract。若后续检查发现 DOCX 的描述会让 consumer 误以为 Word 有独立模型建立风格，再只增加一句 authority pointer，不复制规则。

---

## 10. 是否修改 Module 02

默认 **不修改 `modules/02_model_design.md`**。

本轮不是模型语义设计升级。

以下仍由 Module 02 负责且保持不变：

- 路线比较；
- 变量/假设；
- Formula Trace；
- Semantic Closure；
- Complexity Sanity；
- Model Challenge；
- Human Model Approval；
- PQS；
- Algorithm Trace。

写作模块只把已批准的 current 模型**组织成更自然的论文叙事**，不得借“润色”新增公式、替换 solver、修改约束或重新定义模型。

---

## 11. 预期测试设计

新增：

```text
tests/test_v718_model_solution_writing_style.py
```

测试重点是**架构与规则边界**，不是用正则判一篇论文“写得好不好”。

### 11.1 Authority 回归

断言：

- 新 narrative authority 只在 `core/writing_reasoning_contract.yaml` 定义；
- `latex.md` 与 `ai_cleanup.md` 只引用/消费；
- 不新增独立第二写作合同；
- 不新增 lifecycle gate。

### 11.2 非目标回归

断言没有修改/扩张：

- `core/task_taxonomy.yaml`；
- `core/model_approval_contract.yaml`；
- `core/numerical_verification_contract.yaml`；
- Workbook Schema；
- Project State Schema；
- runtime route。

### 11.3 语义存在性回归

至少检查以下概念进入 Authority：

- continuous mathematical narrative；
- formula need / consequence；
- transition logical function；
- professional heading semantics；
- solver narrative；
- model-to-solver bridge；
- result-adjacent interpretation；
- no repeated problem analysis / assumptions；
- anti-template / no phrase-bank boundary。

### 11.4 AI Cleanup 边界回归

检查：

- management transition 可提示；
- solver-first 可提示；
- detached result interpretation 可提示；
- 但不能根据连接词、标题数量、算法名直接 blocking。

### 11.5 旧功能回归

继续通过：

- v7.16 writing spec tests；
- v7.17 mechanism structural validity tests；
- Skill health；
- Root/package SKILL identity；
- Full CI。

---

## 12. 人工写作样例验收矩阵

自动测试不能判断语言是否真正变好，因此实现完成后必须人工做 6 类 smoke review。只使用虚构/通用小片段，不绑定烟幕弹题。

### Case A：公式密集的机理/几何问题

检查：

- 是否从对象关系自然推到判据；
- 公式之间是否有“当前缺口 → 建式 → 化简结果”；
- 是否避免逐公式翻译。

### Case B：连续优化问题

检查：

- 决策变量、目标、约束是否连续表达；
- solver 是否在模型闭合后出现；
- 是否先说不可导/非凸/低维/搜索域等真实困难，再引出算法。

### Case C：统计/回归问题

检查：

- 是否从响应变量/解释变量关系进入模型；
- 参数估计方法是否由统计结构自然引出；
- 不把“建立回归模型”写成独立空句。

### Case D：解析或简单数值问题

检查：

- 是否允许不写算法流程；
- 是否不会为了统一格式强行制造“模型建立—算法介绍—结果分析”三段。

### Case E：多问递进问题

检查：

- 后问是否只恢复继承与新增；
- 是否避免把共同基础从头复制；
- 若结构改变，是否明确指出失效部分。

### Case F：图表结果密集问题

检查：

- 关键图后是否立即有趋势 + 机制 + 决策解释；
- 是否避免所有图统一“由图可知”；
- 是否没有逐点复述图表。

人工验收通过标准不是“像某一篇论文”，而是：

```text
逻辑连续
+ 数学对象清楚
+ 过渡有功能
+ 标题能恢复任务
+ 算法由结构引出
+ 结果就近解释
+ 无明显 AI 报告腔
```

---

## 13. 反模板边界

本轮必须特别防止“优化写作风格”反而创造第二套模板。

禁止：

1. 从 A066/A196 复制句子；
2. 固定要求每个公式前出现“根据上述分析”；
3. 固定要求每段出现“因此 / 进一步 / 从而”；
4. 固定要求三级标题数；
5. 固定要求每问有流程图；
6. 固定要求模型建立末尾写“综上”；
7. 固定要求求解段使用 Step 1--n；
8. 固定要求图表分析使用统一三句式；
9. 把 PSO、GA、二分法、坐标搜索等参考论文算法写成 Skill 默认；
10. 把烟幕弹题的“轨迹—遮挡—时长”顺序当作所有机理题模板。

正确抽象对象是**逻辑功能**，不是句型。

---

## 14. 实施阶段

### Phase 0：恢复上下文与冻结基线

后续任何聊天/接管者开始修改前必须：

1. 从最新 `main` 读取 `core/bootstrap.yaml`；
2. 读取 `SKILL_CHANGE_GOVERNANCE.md`；
3. 读取本计划全文；
4. 检查当前 `main` 是否仍基于/包含 `c9dc64aa...` 之后的变更；
5. 检查是否存在 overlapping writing PR；
6. 若 main 已前进，重新读取当前 `writing_reasoning_contract.yaml`、`latex.md`、`ai_cleanup.md`；
7. 不得仅依据聊天摘要开始写。

### Phase 1：Authority 设计

只修改 `core/writing_reasoning_contract.yaml`：

- 加入新的 model-establishment/solution narrative 权威；
- 与现有 `formula_reasoning_chain`、`solver_justification`、`subsection_granularity`、`paragraph_necessity` 对齐；
- 避免复制已有规则；
- 明确 rule level：大多数为 Default / Recommendation，只有事实或语义扭曲才 Hard。

完成后先做人工 authority overlap review。

### Phase 2：LaTeX 正文落地

修改 `modules/05_writing/latex.md`：

- 在 4.6/4.7/4.9/4.11/4.13/4.14 消费新权威；
- 不另建第二合同；
- 加少量示例，示例必须是通用虚构句，不从两篇论文逐句搬运；
- 控制文件增长，优先改现有段落而非无限新增小节。

### Phase 3：AI Cleanup 表现审计

修改 `modules/05_writing/ai_cleanup.md`：

- 增加报告式罗列、solver-first、空过渡、泛标题、脱离结果解释等风险；
- 明确机器只能 warning/review，不能凭表面词汇改数学语义；
- 保留有逻辑功能的自然过渡。

### Phase 4：回归测试

新增 `tests/test_v718_model_solution_writing_style.py`。

先执行：

```text
python scripts/lint_skill.py
python -m unittest discover -s tests
python scripts/generate_indexes.py --check
```

若 generated metadata stale，只能由 generator / refresh workflow 更新，禁止手工改 `MANIFEST.sha256` 或索引。

### Phase 5：人工 prose smoke

执行第 12 节 6 类样例。

重点比较：

```text
v7.17 风格输出
vs
v7.18 candidate 风格输出
```

只评价：连续性、标题、公式前后解释、solver 引入、结果邻接解释、重复度。不得为了“更像优秀论文”改变数学事实。

### Phase 6：入口摘要与版本影响

若语义稳定：

- `PROJECT_INSTRUCTIONS.md` 增加一条轻量摘要；
- 判断 README 是否需要用户可见说明；
- 不在入口复制完整规则。

随后才确认目标版本 `7.18.0`。

### Phase 7：Release bump

仅当 Phase 1--6 通过后：

同步版本载体：

- `SKILL.md`；
- `skills/mathmodel-skill/SKILL.md`；
- `core/bootstrap.yaml`；
- `core/output_contract.yaml`；
- `core/module_manifest.yaml`；
- `core/workflow_router.yaml`（只做版本载体更新，不顺手重构路由）；
- `.codex-plugin/plugin.json`；
- `CHANGELOG.md`；
- 现有健康测试中的硬编码版本；
- README/PROJECT_INSTRUCTIONS 中需要同步的当前版本文字。

Root 与 packaged `SKILL.md` 必须保持 byte-identical。

### Phase 8：Generated metadata + Full CI

由 generator/automation 更新：

- `SKILL_FILE_INDEX.md`；
- `MANIFEST.sha256`；
- 其他 generator-managed metadata。

完整 CI 必须通过：

```text
Static contract lint
Python 3.10
Python 3.11
Python 3.12
Python 3.13
Python 3.14
Generated file contract
LaTeX CUMCM
LaTeX MCM-ICM
LaTeX Diangong
Production LaTeX attestation
```

### Phase 9：PR 终审与合并

合并前：

- 检查 changed files 是否只属于本主题；
- 检查无 unresolved review thread；
- 检查无 overlapping PR；
- 检查 full CI green；
- 检查没有把两篇参考论文的题目专属规则写进 runtime；
- 检查版本号只在 release 阶段 bump；
- Squash merge；
- 合并后再检查 main Skill version 与 main CI。

### Phase 10：计划归档

若 v7.18 正式合并并完成 main CI：

- 将本计划从 active `docs/` 移入 `legacy/architecture/`；
- 更新 `legacy/architecture/README.md`；
- generator 刷新 active index；
- 不让完成计划继续留在 Active Skill surface。

---

## 15. 明确不做的关联优化

本轮即使发现，也不得顺手处理：

- Branch Protection；
- GitHub Actions Node warning；
- dependency pinning；
- Python / MATLAB 代码风格；
- 图表配色；
- LaTeX 页面样式；
- 新模型族 taxonomy；
- 机理结构 v7.17 语义；
- 03A/03B 范围；
- PQS；
- Workbook Schema；
- Project State；
- Citation 系统重构；
- 摘要结构大改；
- 新增论文结论章节；
- 任何烟幕弹题专属模型规则。

如果后续发现这些问题，单独建计划/PR。

---

## 16. 风险与防护

### R1：写作规范变成固定模板

表现：不同题目生成相同句式、相同三级标题、相同过渡结构。

防护：只定义逻辑功能；示例明确 non-binding；AI Cleanup 不按关键词强制改写。

### R2：新 narrative 与旧 Formula Trace 重复

表现：同一规则在 `formula_reasoning_chain` 和新区域各写一套。

防护：Formula Trace 继续负责数学证据闭环；新区域只负责正文叙事顺序，并通过引用连接。

### R3：为了流畅而改变模型语义

表现：润色时添加不存在的机制、删掉真实边界、把 heuristic 写成 proof。

防护：新规则明确“流畅不能覆盖事实”；Hard integrity 仍由现有 writing contract + accepted workbook 控制。

### R4：标题规则过强

表现：所有标题被机械改成“XX 的 XX”。

防护：标题语义只做 Default/Review；允许短名词标题，只要能准确恢复数学任务。

### R5：结果解释过多导致重复

表现：摘要、表格、正文、图注反复报同一数字。

防护：result-adjacent interpretation 要解释“为什么/意味着什么”，而不是重复所有数字；Paragraph Necessity 继续生效。

### R6：优秀论文被错误当作唯一标准

表现：Skill 只能写机理/优化题，统计、预测、网络题被烟幕弹写法污染。

防护：人工 smoke 覆盖机理、优化、统计、解析、多问和图表结果六类；参考论文只提供叙事方法，不提供具体模型结构。

---

## 17. 回滚策略

若 v7.18 candidate 出现以下任一问题：

- 文本更模板化；
- 规则与现有 writing authority 冲突；
- 旧项目被强制迁移；
- AI Cleanup 误删必要过渡；
- 写作规则意外改变模型/求解/验证语义；
- full CI 出现无法解释的跨模块破坏；

则优先回退：

1. 新增 narrative authority；
2. latex 对应消费规则；
3. ai_cleanup 新风险项；
4. v7.18 测试；
5. 若已 bump 版本，则同步回退版本载体。

不回滚模型、工作簿、Python、MATLAB 或数值结果，因为本轮不应修改这些对象。

---

## 18. 后续聊天/Agent 的上下文恢复说明

任何后续实施者只要读取本文件，应恢复以下关键信息：

1. **用户当前不满意的是模型建立与求解的语言连续性，而不是数学正确性。**
2. **两篇优秀论文是主要写作参考，用户提示词是辅助约束。**
3. **目标是学习叙事方法，不复制句子/算法/题目结构。**
4. **最重要的六个改进：**
   - Continuous Mathematical Narrative；
   - Formula Prose Rhythm；
   - Transition Function Governance；
   - Professional Heading Semantics；
   - Solver Narrative + Model-to-Solver Bridge；
   - Result-adjacent Interpretation。
5. **模型建立中默认不重复问题分析和模型假设。**
6. **小节按独立数学任务划分，不按变量/目标/约束机械拆分。**
7. **算法必须由当前数学结构和计算困难自然引出。**
8. **结果出现后就近解释实际含义和机制原因。**
9. **Authority 只放 `core/writing_reasoning_contract.yaml`；latex/ai_cleanup 消费，不复制。**
10. **不改 Module 02 数学语义，不改 Model Approval / 03A/03B / Numerical / Workbook / Project State。**
11. **正式版本暂定 7.18.0，只有实现、人工 prose smoke 和完整 CI 通过后才 bump。**
12. **完成后本计划必须归档到 `legacy/architecture/`，不能长期留在 Active Skill surface。**

---

## 19. 计划完成判定

当前阶段只要求：

- [x] 研究两篇参考论文的模型建立与求解写法；
- [x] 抽取用户提示词中的可泛化要求；
- [x] 区分“数学语义正确性”和“正文叙事质量”；
- [x] 明确 Authority 与非目标；
- [x] 明确分阶段实施与测试；
- [x] 将本计划写入独立 GitHub 分支，作为后续修改的持久上下文；
- [ ] 尚未修改 `writing_reasoning_contract.yaml`；
- [ ] 尚未修改 `latex.md`；
- [ ] 尚未修改 `ai_cleanup.md`；
- [ ] 尚未新增 v7.18 runtime 写作语义；
- [ ] 尚未 bump 版本；
- [ ] 尚未进入 release。

在用户明确批准“按本计划开始实施”之前，保持 **PLANNING ONLY**。
