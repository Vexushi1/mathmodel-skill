# 题型 Starter 使用说明 v7.14.1

本目录中的 `classification.py`、`evaluation.py`、`optimization.py`、`prediction.py` 和 `simulation.py` 只用于生成主求解脚本 `问题X求解.py`。主工作簿验收后，不覆盖主脚本；根据真实主结果单独生成 `问题X结果深化分析.py`。

## 推荐项目结构

```text
项目根目录/
├─ hsk_pipeline/
├─ 问题一求解/
│  ├─ 问题一求解.py
│  ├─ 问题一求解结果.xlsx
│  ├─ 问题一结果深化分析.py
│  ├─ 问题一结果深化分析.xlsx
│  └─ q1_plot.m
├─ 模型论文框架.md
└─ 赛题附件.xlsx
```

## 使用步骤

1. 将 `templates/code/hsk_pipeline/` 复制到项目根目录的 `hsk_pipeline/`；
2. 新建 `问题一求解/`，把一个题型 starter 复制为 `问题一求解/问题一求解.py`；
3. 在主脚本中实例化 `FULL_FIDELITY_CONFIG`，锁定数据路径、哈希、求解器、随机种子、容差和完整运行规模，`stage="primary"`，并写入 `primary_quality_protocol_version="1.0.0"`；
4. 在正式编写 `solve_model` 前按 `modules/03_solve_validate.md#Primary Evidence Capture` 列出本次主计算会真实产生、且对解释模型/科研绘图/验证/复现有价值的状态与过程数据；不要只设计“最终答案表”；
5. 主求解工作簿除核心指标外，应按题型实际存在情况保留决策变量、逐对象/逐时刻/逐节点状态、路径/流量/资源占用、目标分项、约束状态、候选解/Pareto candidate、求解轨迹、逐样本预测/残差/区间、关键事件等 current-run evidence。优先复用 `core/workbook_schema.yaml` 已登记的 `明细结果`、`状态明细`、`逐时刻结果`、`节点结果`、`边结果`、`路径或流结果`、`预测明细`、`决策变量明细`、`方案对比`、`Pareto结果`、`收敛诊断` 等表；不存在的结构不创建空表；
6. 03A/03B 边界按“是否改变当前主计算条件并重新运行”判断：保存当前运行已经产生的状态属于主求解；参数敏感性、压力场景、替代算法/结构、多 seed/初值结论稳定性、异质性、阈值搜索等必须等主工作簿 accepted 后进入 03B，不能因为计算便宜就提前塞入；
7. 按 `core/numerical_verification_contract.yaml` 与当前 Primary Quality Specification，只实现本次主计算 accepted 所必需的内在数值有效性检查，例如可行性、方程/守恒残差、离散精度、迭代收敛、最低采样精度或其他已激活 capability；把底层证据与带 Verification ID 的 `主结果质量门` 写入主工作簿；
8. 执行 `validate_code_delivery.py`，同时检查执行配置与 `core/code_quality_contract.yaml` 的工程质量要求；
9. 用户运行主脚本并返回 `问题一求解结果.xlsx`；`validate_user_execution.py` 会调用 `validate_numerical_evidence.py` 独立复核主质量底层证据，不能只依赖工作簿自报“通过”；
10. 主工作簿 accepted 后冻结 `问题一求解.py`，依据真实主结果和评委风险单独生成 `问题一结果深化分析.py`；
11. 深化分析脚本的 `FULL_FIDELITY_CONFIG.stage` 设为 `analysis`，不写 `primary_quality_protocol_version`，读取已验收主工作簿和必要当前数据事实源，只实现题目专属敏感性、鲁棒性、多算法、阈值、结构或场景分析；分析中已真实产生的逐参数/逐场景/逐 seed/逐算法/逐区域/逐阈值底层数据也应落入分析工作簿，而不是只输出“稳定”；
12. 深化分析脚本再次通过代码交付质量门后由用户运行，并返回 `问题一结果深化分析.xlsx`；
13. 两类工作簿 accepted 后生成同目录 `q1_plot.m`，MATLAB 只读工作簿绘图，并按 Scientific Figure Synthesis / Composite Encoding / Rendering Profile 选择科研表达。

边界判据：若某检查失败会使**当前这一次主计算本身不能 accepted**，它属于主求解质量；若当前结果本身仍然有效，只是在参数扰动、替代方法、压力条件或更广范围下的结论稳定性需要研究，则属于结果深化分析。Primary Evidence Capture 只是把当前运行已经得到的真实状态保存下来，不是提前执行深化分析。

不生成独立运行配置、运行说明或校验报告。不得把主求解与深化分析重新拼成一个大脚本；若深化分析表明主模型必须修改，应回退主求解或模型设计阶段，而不是在深化分析脚本中偷偷重写主模型。
