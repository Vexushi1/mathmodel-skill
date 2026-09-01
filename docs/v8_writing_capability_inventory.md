# v8 Writing Capability Inventory Baseline（非 Authority）

## Purpose

v8.0.0 重构前能力冻结。目标不是删除章节级写作规则，而是在 Template Authority 与 Writing Skill 解耦后明确能力归属。

本文件只记录迁移盘点，不参与运行时加载。当前普通写作规则以 `modules/05_writing/paper_writing_protocol.md` 为准，复杂语义以 `core/writing_reasoning_contract.yaml` 为准；实际读取/写入时机以 `core/writing_runtime_contract.yaml#template_first_progressive_authoring` 为准，不能从本盘点文件恢复执行顺序。

v8.0.1 已完成逐项章节能力保全审计与 v7.20 R1 执行映射，详见 `docs/v801_chapter_capability_preservation_audit.md`。

原则：

- 章节写作规则必须保留；
- 模板规则与写作逻辑分离；
- 审查规则与写作规则分离；
- 瘦身只删除重复，不降低论文生成能力。

## Chapter-level Writing Rules

### 摘要

保留：覆盖全部问题的任务/对象、模型、目标或关键条件/约束、方法、关键结果、真实检验证据（若有）和结论；优化类说明决策对象与目标；关键数字来自有效结果；不得虚构敏感性或鲁棒性；避免算法堆砌和空泛评价。

归属：Writing Chapter Rule。

### 问题重述

保留：问题背景收束到本题对象；问题提出准确恢复对象、条件、范围、量词、单位和待求输出；先抽取语义再按小问逻辑重组，不照抄原题、不沿原句序逐句换词，也不因改写遗漏关键条件。

归属：Writing Chapter Rule。

### 问题分析

保留：解释题目机制；识别真实困难；连接变量、模型和求解；说明模型选择依据；以连续自然段形成对象/条件—困难—数学抓手—建模转化—准备结构—跨问关系，不写成散乱清单或软件流水线；体现人工建模思考。

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

保留 Writing Skill：摘要、问题重述、问题分析、模型假设、符号说明、模型建立、公式解释、算法说明、结果解释、验证组织、模型评价、结论/附录边界和数学叙事闭环。

## Refactor Constraint

任何删除必须证明：规则不影响论文质量、已有唯一 Authority 替代、删除不会降低章节写作能力。
