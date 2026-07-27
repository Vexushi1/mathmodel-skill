# v6.3.x lightweight-bootstrap-sync-router 变更记录

## v6.3.1 contract-closure

本补丁不新增模型、目录或工作流层级，集中修复 v6.3.0 的机器契约断裂。

### 框架模式

- `validate_model_paper_framework.py` 按 compact/full 使用不同必需章节集合；
- mode 判定顺序为 CLI、项目状态、框架头部、默认 compact；
- compact 未设置命题规划时不再被 full 规则误判。

### 项目同步

- 修正“先写状态哈希、后修改框架”的顺序错误；
- 固定为：检查产物 → 计算 stale → 更新框架头部 → 计算最终框架哈希 → 写状态 → 写报告 → 写后自检；
- 新增 design/results/figures/docx/latex/submission 交付 scope；
- solved 及后续状态或 results 及后续 scope 强制两类标准工作簿；
- 同步器执行工作簿必需表、字段、capability 条件、主键、非有限数值和约束判定检查；
- 核对 MATLAB 工作簿引用、标题、声明导出图、正式图存在性及图与源文件时间关系。

### 分层哈希与状态

- 新增 data、model、solution_workbook、robustness_workbook、matlab_script、figure_bundle、framework 分层哈希；
- 工作簿、MATLAB 或正式图变化可独立传播 stale；
- `subproblem.capabilities` 成为唯一权威能力字段；
- `classification.capabilities`、`problem_types`、`legacy_task_packs` 仅保留兼容读取，存在时必须与三轴事实一致。

### 三轴下游闭环

- `workbook_schema.yaml` 升级为 2.1.0，增加 objective_profiles 和 structure_profiles；
- Module 02/03 改为 objective、structures、顶层 capabilities 驱动模型、验证和工作簿；
- 旧 task_profiles 仅作为历史项目兼容层。

### 路由与 Lint

- 正式交付计划显式返回 `pre_delivery_gates`；
- `project_sync` 作为真实 utility gate 生产 project_state 和 sync_report；
- `sync_report` 只有在 gate 执行后才进入 available_after_plan；
- Lint 恢复模块生产者—消费者顺序、workflow terminal output、utility gate、compact/full、状态语义和声明路径检查。

## v6.3.0 lightweight-bootstrap-sync-router

### 目标

本版本不继续增加建模名词和流程层级，集中降低启动成本、解决多意图路由、拆分混杂题型维度，并把框架—状态—工作簿—MATLAB—图表的一致性检查落实为可执行同步器。

### P0：轻量启动

- 新增 `core/bootstrap.yaml`，只保存权威源指针、六条硬不变量和工具入口；
- 根 Skill、插件 shim 与 Agent 入口改为先读 bootstrap，再调用解析器；
- 不再在路由前默认通读 Skill、Core、Router、Manifest 和全部模块；
- `legacy/` 与视觉资产继续按需加载。

### P0：多意图解析器

- `scripts/resolve_workflow.py` 支持多个 intent；
- 支持 `--request` 自然语言关键词解析；
- 支持 objective、structures、capabilities 与旧版 primary/secondary 兼容参数；
- 多意图模块按工作流顺序合并、Pack 和 terminal outputs 去重；
- 输出缺失前置产物、计划结束后的可用产物及是否需要同步；
- 所有正式交付自动保留 `model_paper_framework` 与 `sync_report`。

### P0：统一项目同步器

- 新增 `scripts/sync_project.py`；
- 自动发现根目录问题 Python、每问两类工作簿、同目录 MATLAB 和正式图；
- 使用 openpyxl 读取真实工作表、表头和数据行数；
- 计算项目输入、问题代码、工作簿和框架 SHA-256；
- 已验证数据或模型哈希变化时传播 stale，并撤销 passed 状态；
- 更新状态中的产物路径与 evidence；
- 输出 `sync_report.yaml`；
- 同步器不自动生成模型语义、结果数值或验证成功。

### P1：正交分类

- 新增 `core/task_taxonomy.yaml`；
- 每问分类拆为 objective、structures、capabilities；
- objective 只描述任务目标，structures 描述时空、网络、调度、博弈、机理等结构，capabilities 决定必做验证；
- 旧十类题型只保留为现有 Pack 的兼容映射；
- 项目状态 Schema 同时支持 v6.3 classification 和 v6.2 problem_types 迁移。

### P1：契约与同步闭环

- `core/module_manifest.yaml` 新增 `sync_report` 与项目同步 utility gate；
- `core/output_contract.yaml` 新增框架 compact/full 模式和同步器职责边界；
- `core/workbook_schema.yaml` 改用独立 `schema_version` 与 `skill_compatibility`；
- capability 增加外样本、不确定性、泄漏、校准和可识别性；
- 正式交付前必须执行同步器，但同步不能替代模型验证。

### P1：MATLAB 实表读取

- 由“真实表头 + 固定列号”改为“精确表头唯一匹配”；
- 期望列号降级为可选结构漂移警告；
- 继续禁止模糊匹配、别名猜测、相似字段回退和自动改变语义映射；
- 更新 Module 04、MATLAB README 与 `q1_plot.m` 模板。

### P2：命题懒加载

- 全局只保留三条命题硬规则；
- 新增 `packs/artifact/proposition_proof.md` 保存完整准入、证明等级、排版和失效规则；
- 仅在明确证明请求或非零命题计划时加载。
