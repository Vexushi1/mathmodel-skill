# 题型、结构与验证能力分类器 v2.1

分类按小问执行，不按模型名称反推。当前分类采用三个正交维度，定义以 `core/task_taxonomy.yaml` 为准。

## 1. Objective：任务目标

每问只能选择一个：

- `explanation`：解释机制并推导关系；
- `inference`：估计、检验、关联或因果识别；
- `prediction`：预测未来或未观测样本；
- `evaluation`：评分、排序、等级或综合指数；
- `optimization`：在可行域内选择决策；
- `simulation`：通过状态转移或随机试验生成系统行为。

## 2. Structures：问题结构

按实际需要选择 0--3 项：`physical_mechanism`、`temporal`、`spatial`、`network`、`scheduling`、`game`、`stochastic`、`static_tabular`。

结构标签只有在它改变变量、约束、验证方法或交付物时才保留。空间、网络、调度和博弈不再与预测、优化或评价争夺主题型位置。

## 3. Capabilities：必做验证能力

独立判断：

- 显式约束与可行性；
- 均衡、守恒、离散与收敛；
- 外样本验证与不确定性量化；
- 数据泄漏与概率校准；
- 参数或因果效应可识别性。

Capability 决定必须输出的工作表和验证证据，不能仅凭题型名称机械推断。项目状态中的唯一权威位置是小问顶层 `capabilities`。

## 4. 输出格式

```yaml
问题一:
  classification:
    objective: prediction
    structures: [temporal, spatial]
    confidence:
      objective: 0.94
      temporal: 0.86
      spatial: 0.78
  capabilities:
    has_explicit_constraints: false
    requires_feasibility_check: false
    requires_equilibrium_residual: false
    requires_conservation_residual: false
    requires_discretization_check: false
    requires_convergence_diagnostic: false
    requires_out_of_sample_validation: true
    requires_uncertainty_quantification: true
    requires_leakage_check: true
    requires_calibration_check: false
    requires_identifiability_check: false
  reason:
    objective: 输出未观测时空单元的目标变量
    temporal: 使用滞后与滚动验证
    spatial: 邻接和距离改变解释变量关系
```

旧版 `classification.capabilities`、`problem_types.primary/secondary` 和 `legacy_task_packs` 只允许作为派生兼容字段。若兼容字段仍存在，必须与 objective、structures 和顶层 capabilities 完全一致，不得独立编辑。

高级方法不是题型标签；只有明确提出高级方法或路线 B 作为主模型时才加载 `advanced_method_gate.md`。
