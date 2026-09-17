# v9.3.0 初始化建模深度与条件驱动化简重构计划

> 仓库：`Vexushi1/mathmodel-skill`  
> 基线：`v9.2.1`  
> 性质：实施指南，不是活动 Authority  
> 核心主题：**初始化建模深度、条件驱动化简、最小充分主模型、结构匹配求解器**

## 1. 核心决议

本次重构不新增 workflow stage、pre-delivery gate 或第二套 Model Review，而是直接修改模型生成的前端逻辑。

```text
旧：
逐字审题
→ 题型识别
→ 经典/高级两条路线
→ 选模型
→ 结构化简
→ solver

新：
逐字审题
→ 问题对象与定义初始化
→ 题目条件数学化
→ 条件 → 数学后果
→ 结构发现
→ 精确化简 / 充分性缩减 / 等价变换
→ 化简后的真实问题
→ 最小充分主模型
→ Comparison Envelope（0..N）
→ 结构匹配 solver
```

主模型始终定义为：**在题意、精度、机制、约束和输出要求全部满足前提下，不能再合理降低结构而不损失必要信息的最小充分模型。**

高级模型不被禁止。它可以作为高保真参照、机制增强、随机/鲁棒对照、高维参照、替代算法、上下界或压力模型。只有当这些比较证明当前主模型遗漏了必要结构时，才回到模型设计，把“最小必要结构”加回并重新形成最小充分主模型。

## 2. 三项核心能力

### 2.1 初始化建模深度

在模型名称之前识别：研究对象、索引、状态量、决策量、外生输入、观测量、输出量、定义关系、守恒/不变量、硬约束、本构/经验关系、时空/图/信息/随机结构、变量基准、参考系、边界、初始与终止条件。

严格区分：`definition / hard_condition / invariant / constitutive / observation / assumption / approximation / decision`。

### 2.2 条件驱动化简

逐条尝试：

```text
题目条件
→ 数学命题或性质
→ 对变量、状态空间、可行域或计算域的影响
→ 是否可精确化简或充分性缩减
```

题目条件优先被视为“降复杂度信息”，而不只是新增约束。

### 2.3 最小充分主模型

模型评价优先级：

```text
题意完整性
> 关键机制闭合
> 条件利用程度
> 可解释性
> 结构简洁性
> 求解效率
> 形式复杂度
```

## 3. 通用结构原语

模型设计阶段在提出模型名之前，按相关性寻找：

1. 定义与恒等关系：比率、总和、归一化、几何恒等、指标定义；
2. 守恒与不变量：质量、能量、流量、库存、资金、概率、人员、资源；
3. 对称性与等价类：几何、周期、同质个体、可交换主体、重复结构；
4. 单调性与支配：边界最优、阈值结构、dominance pruning；
5. 凸性/凹性/拟凸性：优先全局结构与精确法，避免无必要元启发式；
6. 可分离性与分解：按主体、时间、区域、资源、耦合约束分解；
7. 排序与交换结构：exchange argument，尝试把组合搜索转为排序；
8. 稀疏性与局部性：三对角、块带状、稀疏图、有限邻域；
9. 拓扑结构：tree、DAG、bipartite、flow、matching、cut；
10. 尺度与极限结构：无量纲量、快慢尺度、准稳态、小参数；
11. 最小充分状态/充分统计量：完整历史压缩为未来所需状态；
12. 概率结构：独立性、条件独立、期望线性、可解析矩、确定性等价；
13. 等价变量与坐标变换：log、比值、累计量、势函数、无量纲、参考域；
14. 边界、阈值和事件：首次、各处、低于、持续满足等转成 predicate/event；
15. 信息方向与因果时间：决策时点可知信息、泄漏、先后决策、状态递推。

这些是**生成原语**，不是新的 runtime Gate。

## 4. Reduction Provenance

复用 `core/writing_reasoning_contract.yaml` 现有三类，不新增分类：

- `exact`：可逆等价、定义消元、守恒消元、完全对称降维；
- `proven_sufficient`：证明缩减后仍保留最优/临界/可行对象；
- `heuristic`：近似、缩域、surrogate、主成分、小参数截断，必须保留失效边界。

## 5. 主模型与对照模型

不再固定：

```text
Route A = 经典稳健
Route B = 高级创新
```

改为：

```text
Main Model:
  当前最小充分主模型（必须）

Comparators:
  0..N 个按信息价值选择的对照模型（可选）
```

Comparator 角色包括：`simple_baseline / high_fidelity / advanced_method / ablation / alternative_structure / upper_bound / lower_bound / deterministic / stochastic / low_dim / high_dim / analytic / numerical / exact / heuristic / independent_solver / stress_model`。

对照模型只在能回答明确比较问题时保留，例如：

- 化简是否损失重要信息；
- 更高保真结构是否显著改变结论；
- 高级算法是否真的提升；
- 某机制是否必要；
- 某不确定性是否改变决策；
- 主模型是否接近理论边界。

若 comparator 暴露主模型不足，应回到模型设计，识别缺失结构并只加回最小必要结构，而不是自动把最复杂模型升级为主模型。

## 6. Solver 选择

solver 后于结构发现和主模型形成。

若结构允许，优先顺序是：

```text
解析 / 半解析
→ 专用结构算法
→ 低维确定性数值法
→ 标准精确优化 / 稀疏数值法
→ 通用 solver
→ 启发式 / 元启发式
→ 大型机器学习 / 深度模型
```

后一级只有在前一级不足以满足当前问题时才成为主 solver 候选。高级不等于高效；高效优先来自降维、消元、稀疏、递推、分解、排序、凸性和图结构。

## 7. 题型 Pack 的初始化扩展

不新增万能大 Pack。只在 resolver 已按需加载的现有 task pack 增加短小的“初始化结构化简优先项”。

- `mechanism.md`：控制体、守恒、参考系、对称、尺度、本构 vs 守恒、移动边界、势变换；
- `optimization.md`：消元、活跃约束、单调、凸性、分解、支配、交换、网络等价；
- `prediction.md`：趋势/周期/regime、horizon、充分滞后、分组、可知时点、baseline；
- `evaluation.md`：是否真需综合评价、阈值、dominance、指标冗余、无量纲业务指标；
- `statistics_ml.md`：可识别性、充分统计量、设计秩、分层结构、低维模型是否已充分；
- `graph_network.md`：tree/DAG/bipartite/flow/matching/cut/locality；
- `scheduling.md`：precedence DAG、机器同质性、交换规则、dominance、事件点、DP；
- `game_decision.md`：dominant strategy、zero-sum、potential、best response、先后决策真实性；
- `simulation.md`：最小状态、Markov、event-driven、renewal/queue analytic、mean-field；
- `spatial.md`：对称、局部性、尺度、边界、稀疏权重、图等价。

## 8. 文件级计划

### PR A：Core Modeling Semantics

主改：

- `modules/02_model_design.md`
- `core/hsk_core_policy.md`
- `RUNTIME_ROUTER.md`
- `SKILL.md`
- `core/module_manifest.yaml`
- `templates/model/model_paper_framework.md`
- `packs/task/classifier.md`
- `docs/v9_3_initial_modeling_structural_reduction_refactor_plan.md`
- 对应兼容测试

### PR B：Domain Reduction Cues

修改现有 task packs 和 `advanced_method_gate.md`，不新增大而全的 task pack。

### PR C：Release Closeout

前两批合并后再更新版本载体、CHANGELOG、README、生成索引/Manifest 和最终 release regression；PR C 不再引入新的建模语义规则。

## 9. 接口与兼容硬边界

本轮默认不修改：

- `core/workflow_router.yaml` route id；
- `scripts/resolve_runtime.py` CLI；
- `core/project_state.schema.yaml`；
- `core/state_transition_contract.yaml`；
- `core/workbook_schema.yaml`；
- `core/output_contract.yaml`；
- `core/user_execution_contract.yaml`；
- `core/numerical_verification_contract.yaml`；
- 03A / 03B / Figure Evidence / Writing / Review 的职责边界。

保留 artifact key：`route_comparison / selected_models / proposed_model_spec / locked_model_spec`。

### Semantic Identity

优先保持 SIB root schema `1.0.0` 不变。若需要机器绑定新语义，只使用现有 `extensions`，因为 `extensions` 已参与 canonical semantic hash。旧项目只读不批量迁移；重新进入 current model design 时按现有 v9 规则形成当前身份。

## 10. 现有检查体系继续工作

不新增后置体系：

- Semantic Closure：继续检查题面 → 数学 → 代码 → 输出；
- Complexity Sanity：继续作为防止无依据过度简化的 safety net，但不承担生成化简方案；
- Model Reviewer / Devil's Advocate：继续检查 structure-before-algorithm、unused conditions、hidden coupling、simpler baseline 等；
- Human Approval：继续绑定 current semantic revision + structured identity；
- pre-delivery gates：完全按 resolver 当前返回顺序执行。

关键区分：

```text
初始化结构发现 = generative capability
现有检查/挑战 = safety net
```

## 11. 第一次建模方案的用户输出

推荐顺序：

1. 题目真正要求什么；
2. 关键条件及数学后果；
3. 可以精确化简什么；
4. 化简后真正剩下什么；
5. 最小充分主模型；
6. 为什么不能再继续简化；
7. 结构匹配的求解器；
8. 可选对照模型及比较目的；
9. 需要人工确认的口径。

## 12. 行为回归样例

至少覆盖：

- 物理传递 + 移动边界；
- 交换论证可化简的调度；
- 树网络优化；
- 周期/分组预测；
- 明确阈值的评价问题；
- 可确定性等价的随机问题；
- 空间/图结构；
- 统计推断与可识别性。

目标：验证新 Skill 能否在**第一次模型设计**就发现结构，而不是依赖后置审查补救。

## 13. 测试与验收

所有修改至少运行：

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/generate_indexes.py --check
```

新增专项测试建议：

- `test_v930_initial_modeling_core.py`
- `test_v930_runtime_interface_compatibility.py`
- `test_v930_semantic_identity_compatibility.py`
- `test_v930_model_approval_compatibility.py`
- `test_v930_task_pack_reduction_cues.py`

必须证明：

- 无新增 lifecycle gate；
- resolver 接口不漂移；
- Model Challenge / Human Approval 正常；
- Semantic Identity / typed stale 正常；
- 旧项目可读；
- 工作簿、目录、用户执行边界不受影响。

## 14. 版本建议

若 route / CLI / required schema / project state / workbook / output contract 均保持兼容，建议：

```text
9.2.1 → 9.3.0
```

若实施中发现必须破坏 required Schema 或旧 framework 解析，应停止并重新评估版本等级，不得把破坏性修改伪装成 minor。

## 15. 三条核心原则

1. **在提出任何模型名称之前，先问：题目给出的条件已经替我们解决了多少问题？**
2. **主模型不是“最简单模型”，而是“满足全部要求后不能再合理简化的最小充分模型”。**
3. **高级模型可以很重要，但它必须说明作为主模型或 comparator 增加了什么必要信息，而不能只增加复杂度。**

## 16. 最终预期主链

```text
逐字审题
↓
Problem Contract
↓
对象 / 定义 / 状态 / 决策 / 基准 / 约束初始化
↓
题目条件数学化
↓
Condition → Consequence
↓
结构发现
↓
exact / proven_sufficient / heuristic reduction
↓
化简后的真实问题
↓
Minimal Sufficient Main Model
↓
Comparison Envelope（0..N）
↓
结构匹配 Solver
↓
Formula / Algorithm Trace
↓
Semantic Closure
↓
Complexity Sanity
↓
Model Reviewer + Devil's Advocate
↓
Human Approval
↓
locked_model_spec
↓
现有后续主链保持
```
