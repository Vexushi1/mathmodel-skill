# HSK Python 用户执行管线 v7.0.0

本目录提供用户本地运行的数值底座：

- `run_primary_pipeline()`：数据审计、完整版主求解、主结果质量门和主工作簿；
- `run_result_analysis_pipeline()`：保留为旧项目或显式本地编排的兼容 API；新项目默认由独立 `问题X结果深化分析.py` 读取已验收主工作簿完成深化分析；
- `run_pipeline()`：仅保留为旧项目显式编排的兼容 API，不是新项目默认入口。

题目专属两个阶段脚本在各自交付前都必须通过 `scripts/validate_code_delivery.py`；工程质量细则只由 `core/code_quality_contract.yaml` 定义，本管线不复制阈值。

## 推荐复制结构

```text
项目根目录/
├─ hsk_pipeline/
│  ├─ __init__.py
│  ├─ main_pipeline.py
│  ├─ result_io.py
│  └─ workbook_validation.py
├─ 问题一求解/
│  ├─ 问题一求解.py
│  ├─ 问题一求解结果.xlsx
│  ├─ 问题一结果深化分析.py
│  ├─ 问题一结果深化分析.xlsx
│  └─ q1_plot.m
├─ 模型论文框架.md
└─ 赛题附件.xlsx
```

运行配置以 `FULL_FIDELITY_CONFIG` 字典分别嵌入对应阶段 Python，并写入对应工作簿 `运行配置` 表；不生成独立 YAML 或说明文件。

## 主求解阶段

```text
主代码工程质量门
→ config.validate
→ set_random_seed
→ load_data / preprocess / build_features
→ solve_model / check_constraints
→ evaluate_primary_quality
→ 写入运行配置、核心指标、数据审计、主结果质量门和底层表
→ 问题一求解/问题一求解结果.xlsx
→ validate_user_execution.py
→ accepted / solved
→ 冻结问题一求解.py
```

## 结果深化阶段

主工作簿 accepted 后单独生成 `问题一求解/问题一结果深化分析.py`。该脚本读取已验收 `问题一求解结果.xlsx` 和必要原始数据，根据实际风险完成敏感性、阈值、算法一致性、结构稳健性、异质性或误差分析；再次通过代码工程质量门后由用户运行，并输出 `问题一求解/问题一结果深化分析.xlsx`。不得通过覆盖更新 `问题一求解.py` 实现深化分析。

两类工作簿均验收后，`q1_plot.m` 与它们置于同一目录。Python 不生成正式论文图；MATLAB 不重新求解，默认不创建图表目录或自动导出文件。
