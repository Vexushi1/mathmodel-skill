# 题型 Starter 使用说明 v6.6.0

本目录包含五个主求解入口：`classification.py`、`evaluation.py`、`optimization.py`、`prediction.py` 和 `simulation.py`。Starter 首次版本只调用 `run_primary_pipeline()`；主工作簿验收后，在同一个问题脚本中加入 `run_result_analysis_pipeline()`。

## 推荐项目结构

```text
项目根目录/
├─ hsk_pipeline/
├─ 问题一求解/
│  ├─ 问题一求解.py
│  ├─ 问题一求解结果.xlsx
│  ├─ 问题一结果深化分析.xlsx
│  └─ q1_plot.m
├─ 模型论文框架.md
└─ 赛题附件.xlsx
```

## 使用步骤

1. 将 `templates/code/hsk_pipeline/` 复制到项目根目录的 `hsk_pipeline/`；
2. 新建 `问题一求解/`，把一个 starter 复制为 `问题一求解/问题一求解.py`；
3. 在脚本中实例化 `FULL_FIDELITY_CONFIG`，锁定数据路径、哈希、求解器、随机种子、容差和完整运行规模；
4. 实现数据处理、模型求解、约束或残差检查、主结果质量门和 `运行配置` 工作表；
5. 执行 `validate_code_delivery.py`，校验结果只输出到终端；
6. 用户运行脚本并返回 `问题一求解结果.xlsx`；
7. 主工作簿 accepted 后覆盖更新同一个 `问题一求解.py`，加入题目专属结果深化分析；
8. 用户再次运行该脚本并返回 `问题一结果深化分析.xlsx`；
9. 两类工作簿 accepted 后生成同目录 `q1_plot.m`，MATLAB 只读工作簿绘图。

不生成独立运行配置、运行说明、深化分析脚本或校验报告。不得把多个 starter 拼接到同一问题脚本，也不得在主工作簿验收前写入依赖真实结果的最终深化分析实现。
