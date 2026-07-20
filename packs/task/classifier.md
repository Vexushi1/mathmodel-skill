# 题型分类器

根据目标变量、约束结构、数据组织、状态转移和交付要求分类，不按模型名称反推题型。

## 允许标签

`mechanism`、`optimization`、`prediction`、`evaluation`、`statistics_ml`、`simulation`、`spatial`、`graph_network`、`scheduling`、`game_decision`。

W-DRO、CVaR、MPEC、Stackelberg、ALNS、GNN、DML、强化学习和深度学习是候选方法，不是题型标签。用户提出这些方法时，先完成题型分类，再加载 `advanced_method_gate.md` 审查准入。

## 输出格式

```yaml
primary: mechanism
secondary: [optimization]
confidence:
  mechanism: 0.92
  optimization: 0.76
reason:
  mechanism: 题目要求依据几何与运动关系建立判定条件
  optimization: 后续需要在约束下选择投放参数
```

`primary` 只能有一个；`secondary` 默认为空，通常不超过两个。只有当次标签会改变变量、约束、验证方法或交付物时才加载对应 Pack。置信度低于 0.55 时，优先依据题目对象与输出重新判定，而不是一次加载全部题型包。

## 判定抓手

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