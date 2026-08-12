# Module 03B：独立结果深化分析代码

本模块只接受已验收的主工作簿。根据真实主结果选择参数敏感性、场景压力、多算法/多初值、结构稳健性、阈值、异质性、误差分解或外样本稳定性。

若项目启用了统一数据预处理，本模块的数据事实源为 `数据预处理/数据预处理结果.xlsx`；不得再次直接读取共享原始 CSV/XLSX/TXT 等附件。只有未启用全局预处理且确有单问局部数据时，才允许读取必要原始数据。

## 执行规则

```text
主工作簿accepted
→ 冻结问题X求解.py
→ 建立result_analysis_plan
→ 新建问题X求解/问题X结果深化分析.py
→ 读取统一预处理工作簿 + 已验收问题X求解结果.xlsx + 必要前问标准工作簿
→ validate_code_delivery.py静态验收analysis阶段代码
→ 用户本地full_fidelity运行
→ 同目录问题X结果深化分析.xlsx
→ validate_user_execution.py验收
→ analyzed或redo_required
```

`问题X结果深化分析.py` 是独立可复现程序，不复制主求解主链，不重复项目级清洗、单位换算、统一滤波、统一重采样、坐标修正或异常处理，不通过改写 `问题X求解.py` 实现深化分析。其 `FULL_FIDELITY_CONFIG.stage` 必须为 `analysis`，工作簿中的 `code_sha256` 必须对应该深化分析脚本，并记录统一预处理工作簿哈希。

若深化分析发现统一预处理口径本身导致结论不稳定，应回退 `data_preprocessing`；若发现模型语义问题，则回退 `model_design`；若仅主求解数值质量不足，则回退 `solve_validate`。任何回退都必须按依赖传播下游 stale。

若核心结论未保持，必须回退相应阶段并标记下游 stale。默认不生成独立运行配置、运行说明或校验报告。
