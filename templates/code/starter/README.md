# 题型 Starter 使用说明 v7.0.0

本目录中的 `classification.py`、`evaluation.py`、`optimization.py`、`prediction.py` 和 `simulation.py` 只用于生成主求解脚本 `问题X求解.py`。主工作簿验收后，不覆盖主脚本；根据真实主结果单独生成 `问题X结果深化分析.py`。

## 推荐项目结构

```text
项目根目录/
├─ hsk_pipeline/
├─ 问题一求解/
│  ├─ 问题一求解.py
│  ├─ 问题一求解结果.xlsx
│  ├─ 问题一结果深化分析.py
│  ├─ 问题一结果深化分析.xlsx
│  └─ q1_plot.m
├─ 模型论文框架.md
└─ 赛题附件.xlsx
```

## 使用步骤

1. 将 `templates/code/hsk_pipeline/` 复制到项目根目录的 `hsk_pipeline/`；
2. 新建 `问题一求解/`，把一个题型 starter 复制为 `问题一求解/问题一求解.py`；
3. 在主脚本中实例化 `FULL_FIDELITY_CONFIG`，锁定数据路径、哈希、求解器、随机种子、容差和完整运行规模，`stage="primary"`；
4. 实现数据处理、模型求解、约束或残差检查、主结果质量门和 `运行配置` 工作表；
5. 执行 `validate_code_delivery.py`，同时检查执行配置与 `core/code_quality_contract.yaml` 的工程质量要求；
6. 用户运行主脚本并返回 `问题一求解结果.xlsx`；
7. 主工作簿 accepted 后冻结 `问题一求解.py`，依据主结果和评委风险单独生成 `问题一结果深化分析.py`；
8. 深化分析脚本的 `FULL_FIDELITY_CONFIG.stage` 设为 `analysis`，读取已验收主工作簿和必要原始数据，只实现题目专属敏感性、鲁棒性、多算法、阈值、结构或场景分析；
9. 深化分析脚本再次通过代码交付质量门后由用户运行，并返回 `问题一结果深化分析.xlsx`；
10. 两类工作簿 accepted 后生成同目录 `q1_plot.m`，MATLAB 只读工作簿绘图。

不生成独立运行配置、运行说明或校验报告。不得把主求解与深化分析重新拼成一个大脚本；若深化分析表明主模型必须修改，应回退主求解阶段，而不是在深化分析脚本中偷偷重写主模型。
