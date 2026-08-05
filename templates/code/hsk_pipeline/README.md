# HSK Python 用户执行管线 v6.6.1

本目录提供用户本地运行的数值底座：

- `run_primary_pipeline()`：数据审计、完整版主求解、主结果质量门和主工作簿；
- `run_result_analysis_pipeline()`：主工作簿 accepted 后执行题目专属深化分析并写入第二工作簿；
- `run_pipeline()`：仅保留为旧项目显式编排的兼容 API，不是新项目默认入口。

## 推荐复制结构

```text
项目根目录/
├─ hsk_pipeline/
│  ├─ __init__.py
│  ├─ main_pipeline.py
│  ├─ result_io.py
│  └─ workbook_validation.py
├─ 问题一求解/
│  └─ 问题一求解.py
├─ 模型论文框架.md
└─ 赛题附件.xlsx
```

运行配置以 `FULL_FIDELITY_CONFIG` 字典嵌入 `问题一求解.py`，并写入工作簿 `运行配置` 表；不生成独立 YAML 或说明文件。

## 主求解阶段

```text
config.validate
→ set_random_seed
→ load_data / preprocess / build_features
→ solve_model / check_constraints
→ evaluate_primary_quality
→ 写入运行配置、核心指标、数据审计、主结果质量门和底层表
→ 问题一求解/问题一求解结果.xlsx
→ validate_user_execution.py
→ accepted / solved
```

## 结果深化阶段

主工作簿 accepted 后覆盖更新同一个 `问题一求解/问题一求解.py`，将配置中的 `stage` 改为 `analysis`，加入实际需要的敏感性、阈值、算法一致性、结构稳健性、异质性或误差分析，并输出 `问题一求解/问题一结果深化分析.xlsx`。不得创建第二个 Python 文件。

两类工作簿均验收后，`q1_plot.m` 与它们置于同一目录。Python 不生成正式论文图；MATLAB 不重新求解，默认不创建图表目录或自动导出文件。
