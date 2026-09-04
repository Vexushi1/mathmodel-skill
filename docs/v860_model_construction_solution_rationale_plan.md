# v8.6.0 Model Construction & Solution Rationale 修改计划

> 状态：Approved implementation scope
>
> 基线：`main@6951b8f5d7526332abc821bcb6d1ef8f6f8bc3af`（v8.5.0）
>
> 工作分支：`upgrade/v8.6.0-model-construction-solution-rationale`
>
> 参考：A196 的模型准备、问题一至问题五模型建立及求解部分。参考论文只用于抽象跨题型写作/建模结构，不复制其题目对象、算法、章节编号、标题或句式。

## 1. 目标

v8.5.0 已完成 Author Reasoning Voice。本轮不再以“多写我们”或“更像人”为目标，而把模型建立及求解继续深化为：

```text
当前问题结构
→ 当前还缺什么数学关系
→ 为什么建立这一模型/判据
→ 利用什么性质完成简化/转化
→ 简化为何成立或证据等级是什么
→ 模型最终变成什么计算问题
→ solver 真正需要什么前提
→ 为什么当前 solver 适配
→ 关键离散/精度参数为什么这样选
→ 结果
→ 验证与适用边界
```

这是一条逻辑闭环，不是固定章节模板。

同时强化小节导航：

- 标题服务当前数学任务；
- 父标题已经提供的背景不重复；
- 简单模型不机械切碎；
- 复杂模型也不为减少标题而过度合并；
- 不设置固定标题数量或硬字符数。

## 2. 核心能力

### 2.1 Model Construction Rationale

重要模型结构需要能够恢复：

```text
current_problem_structure
→ modeling_gap
→ chosen_mathematical_structure
→ why_structure_closes_gap
→ applicability_condition
→ downstream_role
```

适用于非平凡模型选择、事件判据、状态关系、近似、surrogate、结构化简和后问模型增量。

简单解析/直接计算允许 `not_applicable`，不得为了填理由制造复杂性。

### 2.2 Local Applicability

模型适用性优先贴近模型第一次实质出现的位置，以一到数句说明：

- 本题结构是什么；
- 当前方法依赖什么；
- 本题满足到什么范围；
- 哪些条件变化会使当前结构失效或需要修改。

默认不机械增加“模型适用性分析”独立小节。

禁止只写：

- 模型适用范围广；
- 模型精度高；
- 模型科学合理；
- 模型简单有效。

### 2.3 Solver Preconditions

solver 之前闭合当前真正依赖的关键条件，而不是复述算法教材：

- 根/边界搜索：局部 bracket、相位/单调/符号变化等实际条件；
- 梯度类：可用局部变化、可微/次梯度和可行更新结构；
- 枚举：候选集合的完整性或明确搜索 scope；
- 分解：子问题定义、回到 original model 的映射与遗漏耦合；
- 局部搜索：初值/邻域/步长与局部 claim scope；
- 启发式/群体搜索：搜索域、可行性处理、目标评价、终止与 claim scope。

若前提只局部成立，solver 和结论也只能局部成立。

### 2.4 Structural Reduction Provenance

沿用并强化：

```text
exact
proven_sufficient
heuristic
```

正文措辞必须与证据等级一致：

- `exact` 才能使用等价转化等严格措辞；
- `proven_sufficient` 需要证明/命题说明保留所需解；
- `heuristic` 必须保留弃置域风险、验证范围和 claim scope。

### 2.5 Numerical Parameter Rationale

对会改变主计算精度/近似/搜索分辨率的关键参数，记录：

```text
parameter_role
→ candidate_range_or_source
→ evidence_metric
→ selection_rule
→ final_value
→ conclusion_effect_if_relevant
```

例如网格、离散点、时间步、搜索步长、窗口、邻域、容差等。

03A/PQS 负责当前主计算精度；accepted 后现实参数扰动与结论稳健性仍属于 03B。比较多个网格值不自动等于鲁棒性分析。

### 2.6 Section Title Minimality

执行 Heading Compression Test：

> 删除父标题已经提供的“问题X、模型建立及求解、优化模型”等上下文以及不增加数学信息的“基于/视角下/研究”等包装后，如果当前数学任务仍完整，则优先使用更短标题。

不设置硬字符数。

### 2.7 Adaptive Subsection Separation

两侧同时治理。

适合拆分：

- 独立公式组/非平凡定义；
- 独立命题或关键判据；
- 独立结构化简；
- 独立参数证据；
- 独立 solver stage；
- 后文需要明确回指；
- 不拆会明显降低导航性。

适合连续：

- 同一论证链；
- 每个候选标题只有很薄内容；
- 不需要后文单独回指。

因此“决策变量 / 目标函数 / 关键约束 / 模型汇总”既不机械要求，也不机械禁止。

## 3. Authority 拓扑

继续使用单一 Authority：

```text
core/writing_reasoning_contract.yaml
        ↓
modules/02_model_design.md
        ↓
modules/05_writing/paper_writing_protocol.md
        ↓
optional examples
        ↓
ai_cleanup.md / review_delivery.md
```

不得新建平行 `model_applicability_contract`、`heading_quality_contract` 或第二套正文规则。

## 4. 拟修改文件

核心：

- `core/writing_reasoning_contract.yaml`
- `core/writing_runtime_contract.yaml`
- `modules/02_model_design.md`
- `modules/05_writing/paper_writing_protocol.md`
- `modules/05_writing/ai_cleanup.md`
- `modules/06_review_delivery.md`
- `templates/model/model_paper_framework.md`

新增 optional examples：

- `modules/05_writing/references/model_construction_solution_rationale_examples.md`

测试：

- `tests/test_v718_model_solution_writing_style.py`
- `tests/test_v719_intra_question_writing_closure.py`
- `tests/test_v840_author_reasoning_writing.py`
- `tests/test_v850_author_reasoning_speech_acts.py`
- `tests/test_v860_model_construction_solution_rationale.py`
- `tests/fixtures/model_construction_solution_cases.yaml`

实施后：

- `docs/v860_model_construction_solution_rationale_evaluation.md`
- release carriers / generated indexes / manifest

## 5. 明确非目标

本轮不得：

1. 复制 A196 的具体算法、标题或章节编号；
2. 把二分、DE、多起点搜索设为默认 solver；
3. 所有优化题强制“决策变量/目标函数/约束/汇总”四段；
4. 所有模型新增“模型适用性分析”；
5. 给标题设置硬字数；
6. 用“标题越短越好”删除必要对象；
7. 为连续叙事强行合并真实独立证明/参数分析；
8. 为导航机械拆出一句话小节；
9. 让 solver precondition 变成算法百科；
10. 把 heuristic 缩域写成严格等价；
11. 把参数选择比较自动包装成鲁棒性；
12. 修改 v8.5 Author Reasoning Voice 的语义边界；
13. 重排问题一、问题二等一级章节；
14. 修改绘图、LaTeX 模板、工作簿或数值验收等无关系统。

## 6. 测试案例

固定覆盖：

1. 已有轨迹但缺事件判据；
2. 多区间事件的局部边界定位；
3. proven-sufficient reduction；
4. heuristic reduction；
5. 离散点数选择；
6. 低维连续黑箱 solver fit；
7. 后问维度/离散/耦合增加后的 solver escalation；
8. 复杂优化允许短三级标题；
9. 简单优化连续组织；
10. Heading Compression；
11. 空泛 applicability；
12. 简单解析 anti-bloat。

测试只保护语义合同与固定事实，不通过正则、标题数量或字数判断论文质量。

## 7. 验收标准

必须满足：

- 重要模型选择能恢复 modeling gap 和 why-this-structure；
- 适用性绑定当前结构和范围；
- Reduction Provenance 与正文强度一致；
- solver 前提和 fit 均可恢复；
- 后问 solver 沿用/更换有结构增量理由；
- 关键数值参数有证据；
- 复杂模型可使用短小导航标题；
- 简单模型不机械切碎；
- 无标题字数/数量 Hard Rule；
- v8.5 Author Voice、Claim Strength、证据治理不降级；
- Runtime 只条件加载新示例，不增加 startup preload 或新 stage；
- 全量 CI 通过后才允许进入 merge 审批。

## 8. 失败条件

出现以下任一情况暂停合并：

- 参考论文具体算法/标题成为模板；
- 固定四段式三级标题；
- 固定“模型适用性”小节；
- 标题字符数 Hard Fail；
- 为减少标题造成复杂模型过度合并；
- 为导航造成一句话碎片小节；
- solver 前提被算法名自动推断；
- heuristic 被升级为严格/全局 claim；
- 关键参数依据被压缩成“综合考虑”；
- v8.5 Author Voice 或现有证据门被削弱；
- top-level skeleton 被重排；
- unrelated figure/LaTeX/workbook systems 出现无必要 diff。

## 9. 最终原则

本轮不追求模型建立部分“写得更长”，而追求评委能够恢复：

```text
为什么这样建
为什么这样简化
当前结构什么时候成立
为什么这个 solver 在这里适用
关键数值参数为什么这样选
为什么这个小节需要独立存在
```

最终目标：

```text
问题结构
→ 建模理由
→ 数学结构
→ 结构化简
→ 适用条件
→ solver 前提与适配
→ 结果
→ 验证
```

这是逻辑闭环，不是固定章节模板。
