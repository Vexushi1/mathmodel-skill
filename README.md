# mathmodel-skill v6.4.0

v6.4.0 将默认论文写作链改为 LaTeX-first：结果工作簿、验证和正式图表锁定后，直接编写并持续修改 LaTeX。DOCX 模块、路由和交付 scope 保留，但仅在用户明确要求 Word 审阅、批注、协作或特定提交格式时启用。

同时，活动说明和索引改用稳定、无版本文件名；旧 `V622` 文件仅保留兼容指针。

## 核心架构

- **轻量启动**：先读取 `core/bootstrap.yaml`，再由解析器按需加载；
- **多意图解析**：支持多个 intent、自然语言 request、目标/结构/能力和前置产物；
- **正交分类**：objective、structures、顶层 capabilities 分离，旧题型标签只作兼容派生；
- **统一项目同步器**：按交付阶段发现并校验产物、计算分层哈希、传播 stale、生成 `sync_report.yaml`；
- **Python—Excel—MATLAB 证据链**：Python 求解与验证，中文工作簿交换结果，MATLAB 精确读取真实表头绘图；
- **LaTeX-first 写作**：默认完整流程不再经过 DOCX 中间稿；
- **DOCX 按需**：仅由显式 Word/DOCX 请求触发，不是 LaTeX 前置；
- **命题懒加载**：详细规则只在命题计划非零或明确证明任务时加载。

## 默认工作流

```text
逐字审题
→ 每问目标、结构、能力与依赖
→ 两条模型路线与高级方法准入
→ 变量、假设、公式、目标和约束闭环
→ 锁定模型并维护模型论文框架.md
→ Python求解、适用检查、多算法、敏感性与鲁棒性
→ 每问两类中文Excel工作簿
→ MATLAB读取真实工作簿绘制正式结果图
→ 直接编写并持续修改LaTeX
→ AI模板感清除
→ project_sync gate、编译和终审
```

## 快速使用

```bash
python scripts/resolve_workflow.py full_workflow \
  --objective optimization \
  --structures scheduling stochastic \
  --capabilities has_explicit_constraints requires_feasibility_check \
  --competition CUMCM
```

直接同步：

```bash
python scripts/sync_project.py D:/A_model_project \
  --write --strict --delivery-scope results
```

可选 scope：`design`、`results`、`figures`、`docx`、`latex`、`submission`。`docx` 是独立按需 scope，不进入默认 `full_workflow`。

## 事实源

- 模型语义与论文组织：`模型论文框架.md`；
- 数值事实：每问两类标准工作簿；
- objective 与 structures：`subproblem.classification`；
- 验证能力：`subproblem.capabilities`；
- 路径、分层哈希与 stale：`state/project_state.yaml`；
- 本次同步结果：`sync_report.yaml`。

## 活动入口

- `PROJECT_INSTRUCTIONS.md`：项目调用说明；
- `RUNTIME_ROUTER.md`：运行时路由说明；
- `SKILL_FILE_INDEX.md`：活动 Skill 文件索引；
- `TEMPLATE_INDEX.md`：活动模板索引；
- `core/bootstrap.yaml`：最小启动契约；
- `core/workflow_router.yaml`：多意图路由与交付 scope；
- `core/module_manifest.yaml`：模块与 utility gate 产物闭环；
- `core/output_contract.yaml`：目录、写作模式、分层哈希和同步门槛；
- `core/workbook_schema.yaml`：工作簿三轴规则和 MATLAB 交接；
- `SKILL_CHANGE_GOVERNANCE.md`：跨聊天仓库修改治理。

旧 `PROJECT_INSTRUCTIONS_HSK_V622.md`、`HSK_RUNTIME_ROUTER_V622.md`、`HSK_SKILL_FILE_INDEX_V622.md` 和 `HSK_TEMPLATE_INDEX_V622.md` 仅用于历史链接兼容。

## 本地检查

```bash
python -m pip install -r requirements-dev.txt
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/generate_indexes.py --check
```
