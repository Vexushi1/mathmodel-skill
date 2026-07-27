---
name: mathmodel-skill
version: 6.3.1
summary: Lightweight-bootstrap HSK mathematical-modeling workflow with orthogonal task classification, explicit pre-delivery synchronization, layered artifact freshness, Python-to-Excel-to-MATLAB evidence chains, DOCX draft and LaTeX final delivery.
triggers: [数学建模, 数模, CUMCM, 国赛, MCM, ICM, 电工杯, 认证杯, 建模论文, 模型论文框架, 项目同步, 结果摘要, 模型选择, 敏感性分析, 鲁棒性分析, 机理图, MATLAB绘图, LaTeX, DOCX]
---

# HSK 数学建模模块化工作流 v6.3.1

## 启动

1. 先读 `core/bootstrap.yaml`；
2. 用 `scripts/resolve_workflow.py` 解析一个或多个意图；
3. 只加载解析结果列出的 Core、模块、Pack 和模板；
4. 不默认读取 `legacy/` 或全部视觉资产。

```bash
python scripts/resolve_workflow.py full_solution \
  --objective optimization \
  --structures physical_mechanism \
  --competition CUMCM

python scripts/resolve_workflow.py \
  --request "继续求解问题三并生成MATLAB敏感性图" \
  --objective optimization \
  --structures stochastic
```

## 三轴分类

每个小问分别记录：一个 `classification.objective`、至多三个 `classification.structures`、一份顶层 `capabilities`。顶层 capabilities 是唯一权威源；`classification.capabilities`、`problem_types` 和 `legacy_task_packs` 仅用于旧项目兼容，存在时必须由当前三轴事实派生。

定义见 `core/task_taxonomy.yaml`，执行模板见 `packs/task/classifier.md`。

## 工作流

```text
逐字审题
→ 每问目标、结构、能力与依赖
→ 两条模型路线与高级方法准入
→ 变量、假设、公式、目标和约束闭环
→ 锁定模型并维护当前版模型论文框架.md
→ Python求解、适用检查、多算法、敏感性与鲁棒性
→ 每问两类中文Excel工作簿
→ MATLAB读取真实工作簿绘制带简洁标题的正式结果图
→ DOCX草稿
→ LaTeX终稿与AI模板感清除
→ 显式project_sync gate、编译和终审
```

路由停止在用户要求的交付物，不为凑流程伪造后续成果。

## 正式交付同步门槛

解析器对正式交付返回 `pre_delivery_gates`，其中 `project_sync` 必须在模块执行完成后、交付前成功运行：

```bash
python scripts/sync_project.py <project_root> \
  --write --strict --delivery-scope <scope>
```

`scope` 为 `design`、`results`、`figures`、`docx`、`latex` 或 `submission`。同步器按阶段检查必需产物和工作簿 Schema，核对 MATLAB—图表链，计算 data、model、两类工作簿、MATLAB、图表包和框架分层哈希，并保守传播 stale。它不会生成模型语义、填写结果或把验证状态提升为 passed。`sync_report.yaml` 只有在 gate 成功后才视为可用产物。

## 当前模型框架

`locked_model_spec` 形成后创建项目根目录 `模型论文框架.md`。日常迭代采用 compact，跨聊天交接、完整复现、终稿和终审采用 full。校验器按模式应用不同章节集合。同步器先更新框架头部，再计算并写入最终 SHA-256。

## 软件职责

- Python：数据处理、模型求解、优化、仿真、统计检验、约束/残差、敏感性、鲁棒性和两类工作簿；
- MATLAB：与工作簿同目录，精确匹配真实表头绘制正式图，不重新计算结果；
- DOCX：修改与逻辑检查；
- LaTeX：最终论文和 PDF；中文国赛保留 `cumcmthesis`。

## 命题

命题可为 0，全文最多 4 个。只有命题计划非零或用户明确要求证明时加载 `packs/artifact/proposition_proof.md`。数值实验不能替代证明。

## 固定目录

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

全局硬规则见 `core/hsk_core_policy.md`；机器产物闭环见 `core/module_manifest.yaml`；工作簿字段见 `core/workbook_schema.yaml`；仓库修改必须先读 `SKILL_CHANGE_GOVERNANCE.md`。
