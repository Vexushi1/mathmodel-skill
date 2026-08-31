# v8.0.0 Writing Capability Inventory Baseline

## Purpose

本文件用于 v8.0.0 写作模块重构前的能力冻结。目标不是删除章节级写作规则，而是在 Template Authority 与 Writing Skill 解耦后，明确每项能力的归属和保留方式。

核心原则：

- 章节写作规则必须保留；
- 模板规则与写作逻辑分离；
- 审查规则与写作规则分离；
- 瘦身只删除重复，不降低论文生成能力。

---

## 1. Abstract / 摘要

保留能力：

- 覆盖全部问题的模型、算法、结果、结论；
- 压缩表达而非简单介绍方法；
- 关键数值进入摘要；
- 避免空泛评价和 AI 模板语言。

归属：Writing Chapter Rule。

不迁移至 Template。

---

## 2. Problem Analysis / 问题分析

保留能力：

- 解释题目机制；
- 建立问题之间的依赖关系；
- 说明模型选择依据；
- 体现人工建模思考过程；
- 连接变量、假设和后续求解。

归属：Writing Chapter Rule + Narrative Core。

---

## 3. Assumptions / 模型假设

保留能力：

- 假设来源；
- 合理性说明；
- 失效影响；
- 检验方式。

归属：Writing Chapter Rule。

---

## 4. Symbols / 符号说明

保留能力：

- 符号统一；
- 单位明确；
- 与代码变量、公式变量对应。

归属：Writing Chapter Rule。

---

## 5. Model Establishment / 模型建立

保留能力：

- 对象到数学变量的映射；
- 决策变量、状态变量、中间变量区分；
- 公式来源解释；
- 目标函数现实意义；
- 约束现实含义。

归属：Writing Chapter Rule + Formula Reasoning。

---

## 6. Solution / 模型求解

保留能力：

- 算法选择理由；
- 求解流程；
- 参数说明；
- 计算可行性说明。

归属：Writing Chapter Rule + Algorithm Narrative。

---

## 7. Results and Validation / 结果分析与验证

保留能力：

- 结果不能只罗列；
- 解释变量影响和机制；
- 结合敏感性、鲁棒性、多算法验证；
- 图表必须服务结论。

归属：Writing Chapter Rule + Result Narrative。

---

## 8. Evaluation / 模型评价

保留能力：

- 优点、局限、改进方向；
- 避免无依据夸大结论。

归属：Writing Chapter Rule。

---

## 9. Migration Rules

迁移到 Template Authority：

- 章节名称；
- LaTeX 结构；
- 页面格式；
- 图表环境。

迁移到 Audit：

- AI 模板检测；
- 禁用表达检查；
- 格式检查。

保留 Writing Skill：

- 如何分析；
- 如何建模；
- 如何解释；
- 如何形成论文叙事闭环。
