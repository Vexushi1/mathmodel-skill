# HSK Python 用户执行管线（template lineage v7.0.0）

本目录提供用户本地运行的数值底座：

- `run_primary_pipeline()`：数据审计、完整版主求解、主结果质量门和主工作簿；
- `run_result_analysis_pipeline()`：保留为旧项目或显式本地编排的兼容 API；新项目只有在主工作簿 accepted 且 Analysis Necessity Gate=`required` 时，才由独立 `问题X结果深化分析.py` 读取已验收主工作簿完成深化分析；
- `run_pipeline()`：仅保留为旧项目显式编排的兼容 API，不是新项目默认入口。

题目专属的实际激活阶段脚本在各自交付前都必须通过 `scripts/validate_code_delivery.py`；工程质量细则只由 `core/code_quality_contract.yaml` 定义，本管线不复制阈值。用户执行、`full_fidelity`、禁止降级/静默 fallback 与版本化 RUN_RECEIPT 的全局政策只由 `core/user_execution_contract.yaml` 定义，`PipelineConfig` 不重复承载这些不可变政策字段。

## 推荐复制结构

每问 current layout 只服从 `core/output_contract.yaml`；基础三文件始终存在，方括号内 03B 文件只在 Gate=`required` 时存在：

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
│  ├─ q1_plot.m
│  ├─ [问题一结果深化分析.py]
│  └─ [问题一结果深化分析.xlsx]
├─ 模型论文框架.md
└─ 赛题附件.xlsx
```

新生成阶段脚本使用唯一顶层 `RUN_CONFIG` 声明 stage/problem/data/hash/solver/seed/tolerance/limit/workbook/protocol 等任务可变输入，并写 `run_receipt_protocol_version="1.0.0"`；不再重复 owner/profile/六个 `allow_*` no-degradation 字段，也不把 `solver_version` 当运行前必填任务参数。旧 `FULL_FIDELITY_CONFIG` / `FULL_RUN_CONFIG` 仅作只读兼容。

用户运行后构造逻辑 `RUN_RECEIPT`，**仍序列化到既有工作簿 `运行配置(项目, 值)`**，不新增第二张回执工作表或独立 YAML/JSON。P5b 新脚本对应的回执写 `run_receipt_version="1.0.0"`，完整记录 owner/profile、solver/version、实际停止原因、平台、fallback 和 no-degradation 标志等实际运行事实，并回显 `stage/problem_name/data_sha256/solver/random_seed/tolerance/iteration_or_time_limit` 与已交付 RUN_CONFIG 对齐。P5a 过渡 RUN_CONFIG 和旧 `FULL_*` 的无版本历史回执继续只读兼容；一旦任一端显式声明未知或不匹配版本则 fail closed。

## 主求解阶段

```text
主代码工程质量门
→ config.validate
→ set_random_seed
→ load_data / preprocess / build_features
→ solve_model / check_constraints
→ evaluate_primary_quality
→ 构造RUN_RECEIPT并写入运行配置、核心指标、数据审计、主结果质量门和底层表
→ 问题一求解/问题一求解结果.xlsx
→ validate_user_execution.py
→ RUN_CONFIG↔RUN_RECEIPT握手 / 数值证据验收
→ accepted / solved
→ 冻结问题一求解.py
→ Analysis Necessity Gate
```

`run_receipt_protocol_version` 只标识运行事实协议，不替代主求解专用 `primary_quality_protocol_version`。新 primary RUN_CONFIG 同时携带两者；前者约束 RUN_RECEIPT，后者约束主数值证据复核。

## 条件式结果深化阶段

主工作簿 accepted 后先执行 Analysis Necessity Gate：

- `not_required`：必须记录非空 `result_analysis_requirement_reason`；不生成 `问题一结果深化分析.py` 或 `问题一结果深化分析.xlsx`，也不得把该状态表述为稳健性、稳定性或替代算法一致性已通过；
- `required`：单独生成 `问题一求解/问题一结果深化分析.py`。该脚本读取已验收 `问题一求解结果.xlsx` 和必要当前数据事实源，根据实际风险完成敏感性、阈值、算法一致性、结构稳健性、异质性或误差分析；再次通过代码工程质量门后由用户运行，并输出 `问题一求解/问题一结果深化分析.xlsx`。analysis RUN_CONFIG 同样声明 `run_receipt_protocol_version="1.0.0"`，返回分析工作簿写 `run_receipt_version="1.0.0"`；不得通过覆盖更新 `问题一求解.py` 实现深化分析。

Figure 阶段的 `q1_plot.m` 始终与主工作簿同目录。主结果图只要求 accepted 主工作簿；只有目标 Figure 实际消费 03B evidence 时才要求条件存在的分析工作簿，缺失时必须 fail closed。Python 不生成正式论文图；MATLAB 不重新求解，默认不创建图表目录或自动导出文件。
