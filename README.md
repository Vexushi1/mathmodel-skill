# mathmodel-skill v6.6.0

当前活动工作流采用 **高质量主求解 + 独立结果深化分析 + MATLAB证据图 + LaTeX直写**。DOCX 保留为显式按需分支，活动说明使用稳定、无版本文件名。

## 核心架构

- **轻量启动**：先读取 `core/bootstrap.yaml`，再由解析器按需加载；
- **正交分类**：objective、structures、顶层 capabilities 分离；
- **主求解质量门**：先保证当前模型下的精度、收敛、可行性、残差或基础外样本要求；
- **自适应结果分析**：根据题目、模型、数据、主结果表现和评委风险选择分析方法；
- **反馈重算**：结果分析发现主结论不可靠时，回退模型设计或主求解；
- **Python—Excel—MATLAB 证据链**：Python计算并输出中文工作簿，MATLAB精确读取真实表头绘图；
- **LaTeX-first**：默认完整流程不经过 DOCX 中间稿；
- **DOCX 按需**：仅由显式 Word/DOCX 请求触发，不是 LaTeX 前置。

## 默认工作流

```text
逐字审题
→ 每问目标、结构、能力与依赖
→ 两条模型路线与高级方法准入
→ 变量、假设、公式、目标和约束闭环
→ 锁定模型并维护模型论文框架.md
→ Python完整主求解
→ 主结果质量门
→ 问题X求解结果.xlsx
→ 选择题目专属结果深化分析
→ 问题X结果深化分析.xlsx
→ MATLAB读取真实工作簿绘图
→ 直接编写并持续修改LaTeX
→ AI模板感清除
→ project_sync gate、编译和终审
```

主求解阶段不得因模块分离而削弱。求解器状态、最优间隙、约束违反、KKT或残差、离散精度、收敛、无泄漏外样本精度和基础不确定性均属于主结果质量门。

后续结果深化分析可能采用：

- 参数与机制敏感性；
- 场景压力测试和不确定性鲁棒性；
- 多算法、多初值、上下界和数值一致性；
- 结构、约束、赋权或分布假设稳健性；
- 阈值与失效边界；
- 异质性与误差分解；
- 外样本、滚动或迁移稳定性。

不要求固定三件套，不允许所有题统一做 ±5%、±10% 扰动。

## 两类标准工作簿

```text
问题一求解/
├─ 问题一求解结果.xlsx
│  ├─ 核心指标
│  ├─ 数据审计
│  ├─ 主结果质量门
│  └─ 题型专项结果
├─ 问题一结果深化分析.xlsx
│  ├─ 分析设计
│  ├─ 至少一个实质分析表
│  └─ 结论稳定性汇总
├─ q1_plot.m
└─ 图表/
```

旧 `问题X敏感性与鲁棒性结果.xlsx` 只作历史项目读取兼容，新项目不再生成。

## 快速使用

```bash
python scripts/resolve_workflow.py full_workflow \
  --objective optimization \
  --structures scheduling stochastic \
  --capabilities has_explicit_constraints requires_feasibility_check \
  --competition CUMCM
```

正式同步：

```bash
python scripts/sync_project.py D:/A_model_project \
  --write --strict --delivery-scope results
```

可选 scope：`design`、`results`、`figures`、`docx`、`latex`、`submission`。`results` 要求主结果质量门和结果深化分析均已完成；`docx` 是独立按需 scope。

## 事实源

- 模型语义与论文组织：`模型论文框架.md`；
- 主结果和质量门：`问题X求解结果.xlsx`；
- 稳定范围、阈值和结果解释：`问题X结果深化分析.xlsx`；
- objective 与 structures：`subproblem.classification`；
- 主结果能力要求：`subproblem.capabilities`；
- 状态、路径、分层哈希与 stale：`state/project_state.yaml`；
- 本次同步结果：`sync_report.yaml`。

## 活动入口

- `PROJECT_INSTRUCTIONS.md`：项目调用说明；
- `RUNTIME_ROUTER.md`：运行时路由说明；
- `SKILL_FILE_INDEX.md`：活动 Skill 文件索引；
- `TEMPLATE_INDEX.md`：活动模板索引；
- `core/bootstrap.yaml`：最小启动契约；
- `core/workflow_router.yaml`：多意图路由；
- `core/module_manifest.yaml`：模块与产物闭环；
- `core/output_contract.yaml`：目录、写作模式、哈希和同步门槛；
- `core/workbook_schema.yaml`：两类工作簿和 MATLAB 交接；
- `SKILL_CHANGE_GOVERNANCE.md`：仓库修改治理。

## 本地检查

```bash
python -m pip install -r requirements-dev.txt
python scripts/lint_skill.py
python -m unittest discover -s tests -p "test_*.py"
python scripts/generate_indexes.py --check
```
## v6.6.0 用户执行完整版代码

默认不由助手运行赛题主求解或结果深化分析程序。助手交付题目专属完整版代码、嵌入式完整运行配置和聊天内运行说明，用户运行后返回标准工作簿；工作簿通过运行配置、代码/数据哈希和质量门验收后，工作流才继续。禁止自动降采样、粗网格、短时域、少重复、宽容差、静默求解器 fallback 或用轻量结果代替正式结果。
