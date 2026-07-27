# mathmodel-skill v6.3.0

HSK 数学建模工作流的本次升级集中解决四个问题：启动上下文过重、单意图路由不足、题型标签维度混杂、框架—状态—工作簿—图表依赖人工同步。

## v6.3 核心

- **轻量启动**：只先读取 `core/bootstrap.yaml`，再由解析器按需加载；
- **多意图解析**：`resolve_workflow.py` 支持多个 intent、自然语言 request、目标/结构/能力和前置产物；
- **正交分类**：objective、structures、capabilities 分离，旧题型标签只作 Pack 兼容；
- **统一项目同步器**：发现产物、读取 Excel 结构、计算哈希、传播 stale、生成 `sync_report.yaml`；
- **MATLAB 精确表头读取**：按真实表头唯一匹配，列号仅作漂移警告；
- **命题懒加载**：全局只保留三条硬规则，详细规则仅在需要时加载。

## 快速使用

```bash
python scripts/resolve_workflow.py full_workflow \
  --objective optimization \
  --structures scheduling stochastic \
  --capabilities has_explicit_constraints requires_feasibility_check \
  --competition CUMCM
```

```bash
python scripts/resolve_workflow.py \
  --request "继续求解问题三并生成MATLAB鲁棒性图" \
  --objective optimization \
  --structures stochastic
```

```bash
python scripts/sync_project.py D:/A_model_project --write --strict
```

`sync_project.py` 默认 dry-run。`--write` 才会写回状态、框架头部和同步报告；它不会自动认定模型正确或验证通过。

## 事实源

- 模型语义与论文组织：`模型论文框架.md`；
- 数值事实：每问两类标准工作簿；
- 哈希、路径与 stale：`state/project_state.yaml`；
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
- `core/hsk_core_policy.md`：全局硬规则；
- `core/task_taxonomy.yaml`：正交分类；
- `core/workflow_router.yaml`：多意图路由；
- `core/module_manifest.yaml`：产物生产者—消费者闭环；
- `scripts/resolve_workflow.py`：确定性加载计划；
- `scripts/sync_project.py`：项目同步；
- `REPOSITORY_INDEX.md`：语义导航。

本地检查：

```bash
python -m pip install -r requirements-dev.txt
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/generate_indexes.py --check
```
