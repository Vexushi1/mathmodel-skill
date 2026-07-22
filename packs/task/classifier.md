# 题型与验证能力分类器

根据目标变量、约束结构、数据组织、状态转移和交付要求分类，不按模型名称反推题型。分类必须逐小问执行。

## 允许题型标签

`mechanism`、`optimization`、`prediction`、`evaluation`、`statistics_ml`、`simulation`、`spatial`、`graph_network`、`scheduling`、`game_decision`。

W-DRO、CVaR、MPEC、Stackelberg、ALNS、GNN、DML、强化学习和深度学习是候选方法，不是题型标签。用户提出这些方法时，先完成题型分类，再加载 `advanced_method_gate.md`。

## 输出格式

```yaml
问题一:
  problem_types:
    primary: mechanism
    secondary: [optimization]
    confidence:
      mechanism: 0.92
      optimization: 0.76
  capabilities:
    has_explicit_constraints: true
    requires_feasibility_check: true
    requires_equilibrium_residual: false
    requires_conservation_residual: false
    requires_discretization_check: false
    requires_convergence_diagnostic: false
  reason:
    mechanism: 题目要求依据几何与运动关系建立判定条件
    optimization: 后续需要在可行域内选择参数
```

`primary` 只能有一个；`secondary` 默认为空且最多两个。只有次标签会改变变量、约束、验证方法或交付物时才加载对应 Pack。置信度低于 0.55 时优先依据题目对象与输出重新判定，而不是一次加载全部题型包。

## 题型判定抓手

- 机理：需要从物理、几何、守恒、动力学或对象关系推导公式；
- 优化：存在可控决策变量、目标函数和可行域；
- 预测：输出是未来或未观测时点的数值、类别或区间；
- 评价：输出是评分、排序、等级或指标体系；
- 统计/机器学习：核心是估计、推断、分类、回归或因果识别；
- 仿真：通过状态转移、随机试验或离散事件生成系统行为；
- 空间：邻接、距离、坐标或空间权重改变模型关系；
- 图网络：对象明确映射为节点与边，输出依赖路径、流、匹配或网络结构；
- 调度：作业、资源、工序和时间冲突是核心约束；
- 博弈决策：多个主体的策略与收益相互依赖。

## capability 判定

- `has_explicit_constraints`：模型存在可计算左端、右端/界和违反量的显式约束；
- `requires_feasibility_check`：即使没有标准优化约束，也必须验证方案、路径、几何或资源可行性；
- `requires_equilibrium_residual`：结论依赖 Nash、Stackelberg、MPEC 或其他均衡条件；
- `requires_conservation_residual`：结论依赖质量、能量、流量、概率或数量守恒；
- `requires_discretization_check`：结果依赖时间步、空间步、网格或离散粒度；
- `requires_convergence_diagnostic`：结果依赖迭代、样本数、仿真长度或随机重复收敛。

capability 决定必须输出的检查表，不能仅凭“机理、仿真、网络”等题型名称机械推断。
