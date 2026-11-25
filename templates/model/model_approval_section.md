#### 模型挑战与人工锁模

> 保存当前模型的双审结论与用户批准，规则见 `core/model_approval_contract.yaml#human_approval`。

- Model Challenge：`pending / passed / revision_required / stale`
- Human Model Approval：`pending / approved / revision_required / stale`
- 当前 semantic revision：
- Semantic identity schema version：
- 当前 semantic identity hash：
- Validated semantic identity hash：
- Approved semantic revision：
- 批准小问：
- 用户批准原话与来源：
- Approved semantic identity hash：
- Legacy semantic/text hash（只读兼容，不授权新代码）：

机器身份字段由实际验证和绑定结果填写。

**Model Reviewer**

- verdict：`passed / revision_required`
- 核心结论：
- required actions：

**Devil's Advocate**

- verdict：`passed / revision_required`
- 核心反例/风险：
- required actions：

**Residual warnings**

- 

**Model Approval Brief**

| 项目 | 当前待批准口径 |
|---|---|
| 研究对象 |  |
| selected model（当前最小充分主模型） |  |
| 核心变量 |  |
| objective |  |
| 关键约束 |  |
| preprocessing_decision |  |
| 结构化简 / Reduction Provenance / 最小充分性 |  |
| 求解器/算法 |  |
| algorithm presentation | `not_needed / stepwise / pseudocode` |
| Comparator Envelope / 未采用 alternative 或未主模型化理由 | `not_applicable` /  |
| residual warnings |  |
| 下一阶段实现范围 | 已选后端、具体求解器、选择理由、所需依赖及未核验条件 |

- 当前模型状态：`proposed_model_spec / locked_model_spec / stale`
- 等待用户确认：`yes / no`
