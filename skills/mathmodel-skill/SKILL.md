---
name: mathmodel-skill
version: 6.5.1
summary: Lightweight-bootstrap HSK mathematical-modeling workflow with high-quality primary solving, an explicit result-quality gate, adaptive result analysis, Python-to-Excel-to-MATLAB evidence chains, LaTeX-first authoring and optional DOCX review.
triggers: [数学建模, 数模, CUMCM, 国赛, MCM, ICM, 电工杯, 认证杯, 建模论文, 模型论文框架, 项目同步, 主结果质量, 结果深化分析, 敏感性分析, 鲁棒性分析, 多算法验证, 机理图, MATLAB绘图, LaTeX, DOCX]
---

# HSK 数学建模模块化工作流 v6.5.1

## v6.5.1 默认执行方式

赛题数值代码默认由用户本地以 `full_fidelity` 模式运行。助手输出完整版代码、运行配置和说明后停在 `awaiting_user_execution`；用户返回主工作簿并验收后，才输出最终结果深化分析代码。助手不得运行赛题代码或自动采用轻量近似。

## 启动

1. 读取 `core/bootstrap.yaml`；
2. 使用 `scripts/resolve_workflow.py` 解析用户意图；
3. 只加载命中的模块、Pack 和模板；
4. `legacy/` 不参与默认执行。

## 核心主链

```text
审题与模型锁定
→ Python完整主求解
→ 主结果质量门
→ 问题X求解结果.xlsx
→ 按题选择结果深化分析
→ 问题X结果深化分析.xlsx
→ MATLAB正式图
→ LaTeX直写与持续修改
→ 编译终审
```

主求解必须先保证当前模型口径下的精度、收敛、可行性、外样本或残差要求。敏感性、鲁棒性、多算法、结构稳健性、阈值、异质性和误差分解属于后续可选结果深化方法，不得以统一扰动模板替代题目专属设计。

结果深化分析发现主结论不可靠时，必须标记下游 stale，回退模型设计或主求解并重新计算。

## 工作簿合同

- `问题X求解结果.xlsx`：核心指标、数据审计、主结果质量门和题型专项结果；
- `问题X结果深化分析.xlsx`：分析设计、至少一个实质分析表和结论稳定性汇总；
- 旧 `问题X敏感性与鲁棒性结果.xlsx` 仅作只读兼容。

## 软件职责

- Python：数据、主求解、质量门、结果深化分析和工作簿；
- MATLAB：只读真实工作簿绘制正式图；
- LaTeX：默认论文主链；
- DOCX：显式按需，不是 LaTeX 前置。

## 正式交付

所有正式产物在交付前执行：

```bash
python scripts/sync_project.py <project_root> --write --strict --delivery-scope <scope>
```

同步器只检查、哈希和传播 stale，不自动提升主结果质量或结果分析状态。

命题允许为 0，全文最多 4 个；数值实验不能替代证明。活动入口使用稳定文件名，详细规则以 `core/` 下权威合同为准。
