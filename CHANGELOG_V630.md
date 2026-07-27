# v6.3.0 lightweight-bootstrap-sync-router 变更记录

## 目标

本版本不继续增加建模名词和流程层级，集中降低启动成本、解决多意图路由、拆分混杂题型维度，并把框架—状态—工作簿—MATLAB—图表的一致性检查落实为可执行同步器。

## P0：轻量启动

- 新增 `core/bootstrap.yaml`，只保存权威源指针、六条硬不变量和工具入口；
- 根 Skill、插件 shim 与 Agent 入口改为先读 bootstrap，再调用解析器；
- 不再在路由前默认通读 Skill、Core、Router、Manifest 和全部模块；
- `legacy/` 与视觉资产继续按需加载。

## P0：多意图解析器

- `scripts/resolve_workflow.py` 支持多个 intent；
- 支持 `--request` 自然语言关键词解析；
- 支持 objective、structures、capabilities 与旧版 primary/secondary 兼容参数；
- 多意图模块按工作流顺序合并、Pack 和 terminal outputs 去重；
- 输出缺失前置产物、计划结束后的可用产物及是否需要同步；
- 所有正式交付自动保留 `model_paper_framework` 与 `sync_report`。

## P0：统一项目同步器

- 新增 `scripts/sync_project.py`；
- 自动发现根目录问题 Python、每问两类工作簿、同目录 MATLAB 和正式图；
- 使用 openpyxl 读取真实工作表、表头和数据行数；
- 计算项目输入、问题代码、工作簿和框架 SHA-256；
- 已验证数据或模型哈希变化时传播 stale，并撤销 passed 状态；
- 更新状态中的产物路径与 evidence；
- 输出 `sync_report.yaml`；
- 同步器不自动生成模型语义、结果数值或验证成功。

## P1：正交分类

- 新增 `core/task_taxonomy.yaml`；
- 每问分类拆为 objective、structures、capabilities；
- objective 只描述任务目标，structures 描述时空、网络、调度、博弈、机理等结构，capabilities 决定必做验证；
- 旧十类题型只保留为现有 Pack 的兼容映射；
- 项目状态 Schema 同时支持 v6.3 classification 和 v6.2 problem_types 迁移。

## P1：契约与同步闭环

- `core/module_manifest.yaml` 新增 `sync_report` 与项目同步 utility gate；
- `core/output_contract.yaml` 新增框架 compact/full 模式和同步器职责边界；
- `core/workbook_schema.yaml` 改用独立 `schema_version` 与 `skill_compatibility`；
- capability 增加外样本、不确定性、泄漏、校准和可识别性；
- 正式交付前必须执行同步器，但同步不能替代模型验证。

## P1：MATLAB 实表读取

- 由“真实表头 + 固定列号”改为“精确表头唯一匹配”；
- 期望列号降级为可选结构漂移警告；
- 继续禁止模糊匹配、别名猜测、相似字段回退和自动改变语义映射；
- 更新 Module 04、MATLAB README 与 `q1_plot.m` 模板。

## P2：命题懒加载

- 全局只保留三条命题硬规则；
- 新增 `packs/artifact/proposition_proof.md` 保存完整准入、证明等级、排版和失效规则；
- 仅在明确证明请求或非零命题计划时加载。
