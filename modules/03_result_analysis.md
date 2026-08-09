# Module 03B：独立结果深化分析代码

本模块只接受已验收的主工作簿。根据真实主结果选择参数敏感性、场景压力、多算法/多初值、结构稳健性、阈值、异质性、误差分解或外样本稳定性。

## 执行规则

```text
主工作簿accepted
→ 冻结问题X求解.py
→ 建立result_analysis_plan
→ 新建问题X求解/问题X结果深化分析.py
→ 读取已验收问题X求解结果.xlsx与必要原始数据
→ validate_code_delivery.py静态验收analysis阶段代码
→ 用户本地full_fidelity运行
→ 同目录问题X结果深化分析.xlsx
→ validate_user_execution.py验收
→ analyzed或redo_required
```

`问题X结果深化分析.py` 是独立可复现程序，不复制主求解主链，不通过改写 `问题X求解.py` 实现深化分析。其 `FULL_FIDELITY_CONFIG.stage` 必须为 `analysis`，工作簿中的 `code_sha256` 必须对应该深化分析脚本。

若核心结论未保持，必须回退模型设计或主求解并标记下游 stale。默认不生成独立运行配置、运行说明或校验报告。
