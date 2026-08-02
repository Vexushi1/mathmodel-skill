# Module 03A：完整版主求解代码交付与用户执行门

本模块生成当前题意、数据和模型口径下可直接本地运行的完整版主求解代码，但助手不得运行、导入或间接执行该代码。

## 主链

```text
锁定数据协议、变量、公式、目标和约束
→ 生成问题X求解.py
→ 生成问题X完整运行配置.yaml
→ 生成问题X本地运行说明.md
→ 静态检查代码、依赖、哈希、占位符和完整精度标志
→ primary_execution_status = awaiting_user_execution
→ 用户本地运行
→ 返回问题X求解结果.xlsx
→ 验收运行配置与主结果质量门
```

正式代码必须包含完整数据检查、模型、求解器状态、容差、停止条件、约束/残差、收敛或外样本检查、随机种子、底层结果和标准工作簿输出。禁止演示数据、抽样运行、粗网格、短时域、少场景、少重复、宽容差和静默 fallback。

## 代码交付

固定交付：

- `问题X求解.py`；
- `问题X完整运行配置.yaml`；
- `问题X本地运行说明.md`；
- `code_delivery_report.yaml`；
- 当前版 `模型论文框架.md`。

使用 `scripts/validate_code_delivery.py` 做静态交付检查。代码交付不得生成工作簿，不得把状态标记为 solved。

## 工作簿验收

用户返回的 `问题X求解结果.xlsx` 必须含 `运行配置`、`核心指标`、`数据审计`、`主结果质量门` 和题型专项底层表。`运行配置` 中的代码哈希必须匹配已交付代码，所有缩减和回退标志必须为 false。

只有 `scripts/validate_user_execution.py` 验收通过后，`primary_execution_status=accepted`、`result_quality_status=passed`、状态进入 solved，并允许生成最终结果深化分析代码。
