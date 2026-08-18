# Module 03B：独立结果深化分析代码

本模块只接受已验收的主工作簿。根据真实主结果选择参数敏感性、场景压力、多算法/多初值、结构稳健性、阈值、异质性、误差分解或外样本稳定性。若 current `模型论文框架.md` 已存在，制定分析计划前先读取本问当前模型、验证方案、主结果摘要、适用/失效边界和跨问依赖，再用已验收主工作簿复核具体数值；不得脱离框架按聊天印象选择分析对象。

数据事实源必须继承当前 `preprocessing_decision`，不得在深化分析阶段重新决定数据清洗口径：

- `not_needed`：可读取必要原始数据 + 已验收主工作簿；
- `question_local`：可读取必要原始数据，并仅复现本问数学层已经定义的局部变换；
- `project_level`：读取 `数据预处理/数据预处理结果.xlsx` + 已验收主工作簿，禁止再次直接读取对应共享原始数据。

## 一、执行规则

```text
主工作簿accepted
→ 冻结问题X求解.py
→ 继承preprocessing_decision与当前数据事实源
→ 建立result_analysis_plan
→ 为每项计划声明target claim与判定准则
→ 新建问题X求解/问题X结果深化分析.py
→ 读取当前数据事实源 + 已验收问题X求解结果.xlsx + 必要前问标准工作簿
→ validate_code_delivery.py静态验收analysis阶段代码
→ 用户本地full_fidelity运行
→ 同目录问题X结果深化分析.xlsx
→ validate_user_execution.py验收
→ 对每项证据给出support / modify / reject
→ analyzed或redo_required
```

`问题X结果深化分析.py` 是独立可复现程序，不复制主求解主链，不通过改写 `问题X求解.py` 实现深化分析。其 `FULL_FIDELITY_CONFIG.stage` 必须为 `analysis`，工作簿中的 `code_sha256` 必须对应该深化分析脚本，并记录当前数据事实源的哈希。

## 二、Analysis Evidence Disposition

深化分析的每一项敏感性、鲁棒性、外样本、压力测试、多算法或多初值证据都必须说明它**作用于哪个具体主张**，并给出以下三种 disposition 之一：

- `support`：目标主张在该检验下保持，可作为正文增强证据，但不得自动扩大适用范围；
- `modify`：目标主张主体仍可使用，但区间、阈值、置信度、排序、边界或文字必须修改，并使依赖的 paper fragments 在完成同步前保持 stale；
- `reject`：目标主张不能继续原样使用。若否决的是核心答案、核心模型结构或关键可行性判断，必须 `redo_required` 并按原因回退；若只是否决一个附加的“稳定性很强”等非核心 claim，可以删除/重写该 claim，而不强迫整题重算。

每项证据至少记录：

```text
Evidence ID
→ method/source
→ target claim
→ disposition
→ key finding
→ required action
→ paper/figure anchor
```

禁止只写“通过敏感性分析验证了模型稳定性”而不说明：分析了什么、支持/修改/否决了哪个主张、变化范围多大以及正文应怎样处理。

## 三、数据与模型边界

数据处理边界：

- `project_level` 项目不得重复公共去缺失、异常处理、单位换算、统一滤波、统一重采样或坐标修正；
- `question_local` 项目只能复现当前小问已有数学来源的局部变换，不得新增全局清洗；
- `not_needed` 项目不得为了深化分析方便而擅自补值、删异常、平滑或滤波。

若深化分析发现公共数据处理口径本身导致结论不稳定，且当前为 `project_level`，应回退 `data_preprocessing`；若发现 `not_needed/question_local` 的判定本身错误，则回退 `model_design` 修改 `preprocessing_decision`；若发现模型语义问题，则回退 `model_design`；若仅主求解数值质量不足，则回退 `solve_validate`。任何回退都必须按依赖传播下游 stale。

若核心结论未保持，必须回退相应阶段并标记真实依赖的下游 stale。默认不生成独立运行配置、运行说明或校验报告。
