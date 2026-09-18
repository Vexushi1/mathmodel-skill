# HSK 主模型与 Comparator 比较表

> 本模板保留 `route_comparison` 兼容产物名称，但不再要求“经典稳健 + 高级创新”固定双路线。每问先形成一个 current 最小充分主模型；Comparator 为 `0..N`，只有在能回答明确比较问题时才保留。高级方法可以是主模型或 comparator，但“更高级”本身不是角色或准入理由。

| 小问 | 角色 | 模型/结构 | 题目条件与数学后果 | Reduction Provenance | 回答目的 / comparison question | 数据与计算支撑 | 关键局限 | 是否当前主模型 |
|---|---|---|---|---|---|---|---|---|
| Q1 | main_model |  |  | exact / proven_sufficient / heuristic / not_applicable | 完整回答本问 |  |  | yes |
| Q1 | comparator（可选） |  |  | exact / proven_sufficient / heuristic / not_applicable |  |  |  | no |
| Q2 | main_model |  |  | exact / proven_sufficient / heuristic / not_applicable | 完整回答本问 |  |  | yes |
| Q2 | comparator（可选） |  |  | exact / proven_sufficient / heuristic / not_applicable |  |  |  | no |

## 使用说明

- `main_model`：当前题意下的最小充分主模型，不是“最简单模型”的同义词。
- `comparator`：数量可以为 0；启用时必须写清 comparison question、相对主模型增加/删除的结构、证据目标和为什么不作为当前主模型。
- simple baseline、high-fidelity、advanced method、ablation、alternative structure、bound、independent solver 等都可以成为 comparator。
- 若 comparator 证明主模型遗漏题面必要结构，应返回模型设计并只加回最小必要结构，而不是自动把最复杂模型升级为主模型。
- 本表不是 Model Approval Authority；Challenge 与 Human Approval 仍服从 `core/model_approval_contract.yaml`。
