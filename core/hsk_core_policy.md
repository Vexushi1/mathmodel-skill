# HSK Core Policy v6.5.0

本文件只保存全局硬规则。用户执行合同以 `core/user_execution_contract.yaml` 为准；路由、产物图、输出、工作簿和项目状态分别以对应 `core/` 文件为准。

## 1. 总目标与优先级

数学建模任务必须形成题意正确、机制闭合、数值可信、可复现和可审查的成果链。优先级为：

$$
\text{题意正确}>\text{机制与变量闭合}>\text{数据可信}>\text{完整版数值求解}>\text{结果证据}>\text{图表}>\text{论文表达}>\text{形式创新}.
$$

不能落地、不能解释、不能检验或不能复现的模型必须否决、降级或重构。

## 2. 默认执行所有权

新项目默认采用 `execution_owner=user`、`execution_profile=full_fidelity`。助手负责审题、模型设计、公式闭环、生成可以直接本地运行的完整版 Python 代码、静态审查和返回工作簿验收；用户负责实际运行赛题主求解与结果深化分析代码。

助手不得运行、导入或间接执行 `问题X求解.py`、`问题X结果深化分析.py`，不得为了计算时间缩减数据、网格、时域、场景、重复次数、随机种子、迭代次数或放宽容差，也不得静默切换求解器或轻量近似。仓库自身 lint、单元测试、索引生成和 LaTeX CI 不属于赛题数值执行，可以运行。

## 3. 默认工作顺序

```text
审题与数据协议
→ 模型路线比较与模型锁定
→ 更新模型论文框架.md
→ 输出问题X求解.py、完整运行配置和本地运行说明
→ 状态停在awaiting_user_execution
→ 用户本地完整运行并返回问题X求解结果.xlsx
→ 验收运行配置、代码/数据哈希和主结果质量门
→ 仅在主工作簿accepted后设计并输出问题X结果深化分析.py
→ 用户本地完整运行并返回问题X结果深化分析.xlsx
→ 验收分析设计、稳定性结论和运行配置
→ MATLAB读取真实工作簿绘图
→ 直接编写并持续修改LaTeX
→ 编译与终审
```

一个聊天不能伪造越过用户执行门。完整工作流允许在两个执行门处暂停，用户返回工作簿后从当前状态继续。

## 4. 代码交付门

每次正式代码交付必须同时包含：题目专属 Python 代码、完整版运行配置、本地运行说明和代码交付报告。配置必须显式记录求解器、版本、随机种子、模型专属容差、完整迭代/时间限制、完整场景或重复次数、完整网格/时域、预期工作簿和代码/数据哈希。

所有 `allow_reduced_*`、`allow_coarser_grid`、`allow_shorter_horizon`、`allow_fewer_repetitions`、`allow_relaxed_tolerance` 和 `allow_silent_solver_fallback` 必须为 `false`。正式代码不得含 TODO、FIXME、`__QUESTION_NAME__` 或 `NotImplementedError` 占位。

代码交付只把执行状态改为 `awaiting_user_execution`，不得把小问提升为 `solved` 或 `analyzed`。

## 5. 用户返回工作簿验收

两类工作簿都必须包含 `运行配置` 工作表，记录实际求解器版本、停止原因、平台、容差、随机种子、重复/场景、网格/时域、fallback 状态以及代码/数据哈希。工作簿中的 `code_sha256` 必须与已交付代码一致，`fallback_used` 必须为 `false`。

主工作簿还必须通过 `主结果质量门`，之后 `primary_execution_status` 才可变为 `accepted`、小问状态才可进入 `solved`。主工作簿未验收前，只能列出候选深化方向，不得生成依赖实际结果的最终深化分析代码。

分析工作簿必须包含 `分析设计`、至少一个实质分析表和 `结论稳定性汇总`。通过后 `analysis_execution_status=accepted` 且状态进入 `analyzed`；若核心结论在合理变化下失效，必须标记 `redo_required` 和下游 stale，回退模型设计或主求解。

## 6. 事实源与软件职责

- 模型语义和论文结构：`模型论文框架.md`；
- 机器状态、执行所有权、哈希和 stale：`state/project_state.yaml`；
- 主数值事实：用户返回并验收的 `问题X求解结果.xlsx`；
- 稳定范围与失效边界：用户返回并验收的 `问题X结果深化分析.xlsx`。

Python 代码负责完整数据处理、主求解、质量门、结果深化分析和工作簿输出，但由用户本地执行。MATLAB 只读取验收后的真实工作簿绘制正式结果图；LaTeX 负责终稿；DOCX 仅显式按需。

## 7. 正式交付同步

- 代码交付使用 `scripts/validate_code_delivery.py`，不得执行赛题代码；
- 用户返回工作簿使用 `scripts/validate_user_execution.py`，只读工作簿并在通过后更新执行状态；
- 图表、论文和提交包继续使用 `scripts/sync_project.py` 检查完整证据链。

`results`、`figures`、`docx`、`latex` 和 `submission` 交付仍要求两类工作簿通过且下游非 stale。缺失用户返回结果时必须暂停，而不是生成示意数值。

## 8. 图表、写作与终审

MATLAB 字段定位采用精确表头唯一匹配，不得模糊匹配或根据摘要反推数据。LaTeX 只能引用验收后的数值和已批准图表。终稿必须核对题意覆盖、模型闭合、执行配置、主结果质量门、结果深化选择理由、代码—工作簿—MATLAB—图表—正文证据链和编译状态。
