# mathmodel-skill v6.3.4

v6.3.4 是 v6.3 系列的 starter-cleanup 补丁：五类 Python starter 统一接入 `run_pipeline()`，导入阶段不再创建目录、设置随机种子或直接写工作簿；活动包同时清理可再生文件和已退出默认链路的 MATLAB 辅助项。

## v6.3 核心架构

- **轻量启动**：只先读取 `core/bootstrap.yaml`，再由解析器按需加载；
- **多意图解析**：支持多个 intent、自然语言 request、目标/结构/能力和前置产物；
- **正交分类**：objective、structures、顶层 capabilities 分离，旧题型标签只作兼容派生；
- **统一项目同步器**：按交付阶段发现并校验产物、计算分层哈希、传播 stale、生成 `sync_report.yaml`；
- **MATLAB 精确表头读取**：按真实表头唯一匹配，列号仅作漂移警告；
- **命题懒加载**：详细规则只在命题计划非零或明确证明任务时加载。

## v6.3.4 Starter Cleanup

- `templates/code/starter/` 五类入口改为题型配置与题目专属钩子，不再复制输出和校验逻辑；
- `templates/code/hsk_pipeline/main_pipeline.py` 新增统一 `run_pipeline()`；
- starter 显式传递 objective、structures 和完整 capabilities；
- 删除冗余 `.gitkeep`、可再生 `example.pdf`，迁移非默认 MATLAB 辅助函数；
- 新增 starter 导入副作用、能力配置和活动残留回归测试。

## v6.3.3 Gate Hardening

- `project_sync` 内部强制执行项目状态 Schema/语义校验与模型论文框架校验；
- figures scope 无条件执行 MATLAB、正式图与 figure evidence 检查；
- 同步器只传播或保持 stale，不自动清除 stale；
- `core/output_contract.yaml` 成为 stage requirements 唯一事实源，Manifest 仅保存引用；
- 首次生成 `figure_evidence.yaml` 后立即写入 `subproblem.evidence`。

## v6.3.2 修复

- compact/full 框架按模式使用不同章节集合；
- 同步器更新框架头部后再写入最终框架 SHA-256；
- `subproblem.capabilities` 成为唯一权威能力字段；
- 新增 data、model、两类工作簿、MATLAB、图表包和 framework 分层哈希；
- 工作簿 Schema、capability 条件、主键、非有限数值和约束判定进入同步检查；
- MATLAB 工作簿引用、声明导出图、图文件存在性和时间新旧关系进入同步检查；
- 正式交付计划显式返回 `pre_delivery_gates`，`sync_report` 仅在 gate 后可用；
- 静态 Lint 恢复产物生产者—消费者、terminal output、Schema 语义和框架模式闭环检查。

## 快速使用

```bash
python scripts/resolve_workflow.py full_workflow \
  --objective optimization \
  --structures scheduling stochastic \
  --capabilities has_explicit_constraints requires_feasibility_check \
  --competition CUMCM
```

解析结果包含：

```yaml
module_terminal_outputs: [...]
pre_delivery_gates:
  - name: project_sync
    delivery_scope: submission
    command: python scripts/sync_project.py <project_root> --write --strict --delivery-scope submission
terminal_outputs: [..., project_state, sync_report]
```

直接同步：

```bash
python scripts/sync_project.py D:/A_model_project \
  --write --strict --delivery-scope results
```

可选 scope：`design`、`results`、`figures`、`docx`、`latex`、`submission`。未显式指定时根据 `project.current_phase` 推断。

## 事实源

- 模型语义与论文组织：`模型论文框架.md`；
- 数值事实：每问两类标准工作簿；
- objective 与 structures：`subproblem.classification`；
- 验证能力：`subproblem.capabilities`；
- 路径、分层哈希与 stale：`state/project_state.yaml`；
- 本次同步结果：`sync_report.yaml`。

## 目录

```text
项目根目录/
├─ 赛题与附件
├─ 模型论文框架.md
├─ 问题一求解.py
├─ state/project_state.yaml
├─ sync_report.yaml
└─ 结果数据表/问题一/
   ├─ 问题一求解结果.xlsx
   ├─ 问题一敏感性与鲁棒性结果.xlsx
   ├─ q1_plot.m
   └─ 图表/
```

## 入口

- `core/bootstrap.yaml`：最小启动契约；
- `core/task_taxonomy.yaml`：正交分类；
- `core/workflow_router.yaml`：多意图路由与交付 scope；
- `core/module_manifest.yaml`：模块与 utility gate 产物闭环；
- `core/output_contract.yaml`：目录、框架模式、分层哈希和同步门槛；
- `core/workbook_schema.yaml`：工作簿三轴规则和 MATLAB 交接；
- `scripts/resolve_workflow.py`：确定性执行计划；
- `scripts/sync_project.py`：项目同步与交付检查；
- `SKILL_CHANGE_GOVERNANCE.md`：跨聊天仓库修改治理。

本地检查：

```bash
python -m pip install -r requirements-dev.txt
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/generate_indexes.py --check
```
