# Module 03A：主求解代码交付

本模块在 `问题X求解/` 中生成 `问题X求解.py`。助手只生成和静态检查，不运行赛题代码。

```text
锁定模型
→ 生成问题X求解.py
→ validate_code_delivery.py：执行配置 + 代码工程质量门
→ 用户本地full_fidelity运行
→ 问题X求解结果.xlsx
→ validate_user_execution.py验收运行配置、哈希与主结果质量门
→ accepted后冻结问题X求解.py
```

脚本必须保留数据读取与审计、随机种子、模型与求解器、目标/约束或题型核心检查、停止条件、约束/残差/收敛或外样本证据、结果整理、中文工作簿输出和主入口。代码规模、函数规模、参数数量、复杂度与反模式以 `core/code_quality_contract.yaml` 为唯一事实源。

完整运行配置嵌入 `FULL_FIDELITY_CONFIG` 并写入主工作簿，不生成独立 YAML、运行说明或校验报告。主工作簿 accepted 后不得为了结果深化分析覆盖更新 `问题X求解.py`；深化分析进入 Module 03B，并生成独立 `问题X结果深化分析.py`。若后续发现主模型必须修改，应显式回退本模块并重新验收主结果。
