# v8.0.0 Writing Capability Inventory Baseline

## Purpose

v8.0.0 重构前能力冻结。目标不是删除章节级写作规则，而是在 Template Authority 与 Writing Skill 解耦后明确能力归属。

原则：

- 章节写作规则必须保留；
- 模板规则与写作逻辑分离；
- 审查规则与写作规则分离；
- 瘦身只删除重复，不降低论文生成能力。

## Chapter-level Writing Rules

### 摘要

保留：覆盖全部问题的模型、方法、关键结果和结论；优化类说明决策对象与目标；关键数字来自有效结果；避免算法堆砌和空泛评价。

归属：Writing Chapter Rule。

### 问题分析

保留：解释题目机制；识别真实困难；连接变量、模型和求解；说明模型选择依据；体现人工建模思考。

归属：Writing Chapter Rule + Narrative Core。

### 模型假设

保留：假设来源、合理性、失效影响和检验方式；禁止无依据增加假设。

归属：Writing Chapter Rule。

### 符号说明

保留：符号、单位、公式变量、代码变量和结果变量一致；区分决策变量、状态变量和中间变量。

归属：Writing Chapter Rule。

### 模型建立

保留：对象到数学结构映射；变量定义；公式来源—推导—去向；目标函数含义；约束来源；核心模型汇总按复杂度自适应。

归属：Writing Chapter Rule + Formula Reasoning。

### 模型求解

保留：从模型说明计算困难；算法选择理由；参数与终止条件；区分 model、solver、validator。

归属：Writing Chapter Rule + Algorithm Narrative。

### 结果分析与验证

保留：结果解释不能只罗列；图表服务结论；验证针对风险；敏感性、鲁棒性、多算法验证按需使用。

归属：Writing Chapter Rule + Result Narrative。

### 模型评价与推广

保留：优势、限制、适用条件和改进方向必须有依据。

归属：Writing Chapter Rule。

### 结论与附录

保留：结论回答题目，不新增未证明内容；附录承担代码、参数和补充推导。

归属：Writing Chapter Rule + Adapter。

## Migration Boundary

迁移至 Template Authority：章节名称、LaTeX 文件组织、页面格式、公式图表环境。

迁移至 Audit：AI模板检测、禁用表达、格式一致性检查。

保留 Writing Skill：问题分析、模型建立、公式解释、算法说明、结果解释、验证组织和数学叙事闭环。

## Refactor Constraint

任何删除必须证明：规则不影响论文质量、已有唯一 Authority 替代、删除不会降低章节写作能力。