---
name: mathmodel-skill
version: 6.4.0
summary: Lightweight-bootstrap HSK mathematical-modeling workflow with high-quality primary solving, an explicit result-quality gate, adaptive result analysis, Python-to-Excel-to-MATLAB evidence chains, LaTeX-first authoring and optional DOCX review.
triggers: [数学建模, 数模, CUMCM, 国赛, MCM, ICM, 电工杯, 认证杯, 建模论文, 模型论文框架, 项目同步, 主结果质量, 结果深化分析, 敏感性分析, 鲁棒性分析, 多算法验证, 机理图, MATLAB绘图, LaTeX, DOCX]
---

# HSK 数学建模模块化工作流 v6.4.0

## 启动

1. 先读 `core/bootstrap.yaml`；
2. 用 `scripts/resolve_workflow.py` 解析一个或多个意图；
3. 只加载解析结果列出的 Core、模块、Pack 和模板；
4. 不默认读取 `legacy/` 或全部视觉资产。

```bash
python scripts/resolve_workflow.py full_solution \
  --objective optimization \
  --structures scheduling stochastic \
  --competition CUMCM
```

## 三轴分类

每个小问分别记录一个 `classification.objective`、至多三个 `classification.structures` 和一份顶层 `capabilities`。顶层 capabilities 是主结果必须完成的可行性、残差、收敛、外样本、泄漏、校准或可识别性要求，不是固定的结果分析方法清单。

## 默认工作流

```text
逐字审题
→ 每问目标、结构、能力与依赖
→ 两条模型路线与高级方法准入
→ 变量、假设、公式、目标和约束闭环
→ 锁定模型并维护当前版模型论文框架.md
→ Python完整主求解
→ 主结果质量门
→ 问题X求解结果.xlsx
→ 根据题目、模型、数据、主结果与评委风险选择结果深化分析
→ 问题X结果深化分析.xlsx
→ MATLAB读取真实工作簿绘图
→ 直接编写并持续修改LaTeX
→ AI模板感清除
→ project_sync gate、编译和终审
```

主求解必须先把结果算准。后续结果深化分析可以是敏感性、鲁棒性、多算法、结构稳健性、阈值、异质性、误差分解或外样本稳定性，不要求固定三件套，也不允许所有题统一参数扰动。

若深化分析发现主结论在合理条件下失效，必须标记主结果和下游产物 stale，回退模型设计或主求解并重新计算。

## 两类工作簿

```text
结果数据表/问题一/
├─ 问题一求解结果.xlsx
│  ├─ 核心指标
│  ├─ 数据审计
│  ├─ 主结果质量门
│  └─ 题型专项结果
├─ 问题一结果深化分析.xlsx
│  ├─ 分析设计
│  ├─ 至少一个题目专属实质分析表
│  └─ 结论稳定性汇总
├─ q1_plot.m
└─ 图表/
```

旧 `问题X敏感性与鲁棒性结果.xlsx` 仅作历史项目只读兼容，新项目不得继续生成。

## 软件职责

- Python：数据处理、主求解、质量门、结果深化分析和中文工作簿；不生成正式论文图。
- MATLAB：与工作簿同目录，精确匹配真实表头绘图，不重新计算核心结果。
- LaTeX：从首个论文正文版本开始直接编写并持续修改；中文国赛保留 `cumcmthesis`。
- DOCX：仅在用户明确要求 Word 审阅、批注或特定提交格式时作为独立可选分支，不是 LaTeX 前置。

## 正式交付同步门槛

```bash
python scripts/sync_project.py <project_root> \
  --write --strict --delivery-scope <scope>
```

`scope` 为 `design`、`results`、`figures`、`docx`、`latex` 或 `submission`。同步器按 exact scope 检查产物、工作簿 Schema、MATLAB 图表链和分层哈希，只传播 stale，不生成模型语义、不填写结果，也不把质量门或结果分析状态自动提升为 passed。

## 当前模型框架

`locked_model_spec` 形成后创建项目根目录 `模型论文框架.md`。日常采用 compact，跨聊天交接、完整复现、终稿和终审采用 full。主结果或深化分析变化时，完整替换受影响章节，不并列保留旧版本。

## 命题

命题可为 0，全文最多 4 个。只有命题计划非零或用户明确要求证明时加载 `packs/artifact/proposition_proof.md`。数值实验不能替代证明。

## 活动入口

活动说明使用稳定文件名：`PROJECT_INSTRUCTIONS.md`、`RUNTIME_ROUTER.md`、`SKILL_FILE_INDEX.md` 和 `TEMPLATE_INDEX.md`。旧版本化文件名只保留兼容指针。

全局硬规则见 `core/hsk_core_policy.md`；产物闭环见 `core/module_manifest.yaml`；工作簿字段见 `core/workbook_schema.yaml`；仓库修改必须先读 `SKILL_CHANGE_GOVERNANCE.md`。
