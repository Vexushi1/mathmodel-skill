# HSK Python 用户执行管线 v6.5.1

本目录提供可由用户本地运行的完整数值底座：

- `run_primary_pipeline()`：数据审计、完整版主求解、主结果质量门和主工作簿；
- `run_result_analysis_pipeline()`：在主工作簿 accepted 后，执行题目专属结果深化并写入深化工作簿；
- `run_pipeline()`：仅保留为旧项目和用户本地显式编排的兼容 API，不是新项目默认入口。

新项目的题型 starter 只调用 `run_primary_pipeline()`。助手交付主代码、完整运行配置和说明后停在 `awaiting_user_execution`；用户运行产生工作簿后，状态只到 `workbook_received`，必须由 `validate_user_execution.py` 验收后才进入 `accepted/solved`。

## 推荐复制结构

```text
项目根目录/
├─ hsk_pipeline/
│  ├─ __init__.py
│  ├─ main_pipeline.py
│  ├─ result_io.py
│  └─ workbook_validation.py
├─ 问题一求解.py
├─ 问题一完整运行配置.yaml
├─ 问题一本地运行说明.md
├─ 模型论文框架.md
└─ 赛题附件.xlsx
```

## 主求解阶段

```text
config.validate
→ set_random_seed
→ load_data / preprocess / build_features
→ solve_model / check_constraints
→ evaluate_primary_quality
→ 写入运行配置、核心指标、数据审计、主结果质量门和底层表
→ primary_execution_status = workbook_received
→ 用户返回工作簿
→ validate_user_execution.py
→ accepted / solved
```

主工作簿必须包含 `运行配置`，并记录代码/数据 SHA-256、求解器版本、容差、停止原因、随机种子、场景或重复次数、网格或时域、平台以及全部禁止降级标志。

## 结果深化阶段

主工作簿 accepted 后，依据真实主结果单独生成 `问题X结果深化分析.py`、深化完整运行配置和本地说明。用户本地运行后返回 `问题X结果深化分析.xlsx`；该工作簿同样必须包含 `运行配置`、`分析设计`、至少一个实质分析表和 `结论稳定性汇总`。验收通过后才进入 `analyzed`。

`run_pipeline()` 不得被助手调用，也不得作为新 starter 的默认入口。Python 不生成正式论文图；MATLAB 只读取两类 accepted 工作簿。

正式代码交付：

```bash
python scripts/sync_project.py <project_root> --write --strict --delivery-scope code
```

两类工作簿均验收后，正式结果交付才使用 `--delivery-scope results`。
