# 题型 Starter 使用说明（template lineage v7.15.0）

本目录仅在项目根已锁定 Python 求解后端时提供 Python 数学实现骨架；新03A/03B配置/回执按 `core/user_execution_contract.yaml` 使用1.1和源码依赖绑定，项目级预处理仍1.0。项目根已锁定 MATLAB 时使用 `templates/code/matlab/` 的数值模板。starter 不回写项目状态、审批或框架，也不自动连跑分析。

本目录中的 `classification.py`、`evaluation.py`、`optimization.py`、`prediction.py` 和 `simulation.py` 只用于生成主求解脚本 `问题X求解.py`。主工作簿验收后，不覆盖主脚本；先执行 Analysis Necessity Gate，仅在 Gate=`required` 时根据真实主结果单独生成 `问题X结果深化分析.py`。

普通 03B 的可运行示例是 `q1_analysis.py`。主簿验收且需要深化分析时，可把它实例化为本问的 `问题X结果深化分析.py`。示例读取已验收的方程解，对每个声明的系数分别记录实际解及其相对基准的绝对偏离，并据此判断两条主张。换题时，在静态 `RUN_CONFIG.ordinary_experiments` 中更新检验目标、主张与 ID，同时替换对应计算和判据。运行配置与返回表字段见 `core/user_execution_contract.yaml` 和 `core/workbook_schema.yaml`。

旧 `sync_primary_framework` 钩子及 `framework_sync_hook` 参数已经退出；移除旧调用后，由工作簿回执验收与项目同步控制面登记结果，不能自行把本地成功写成 accepted。新实例必须按下面步骤补齐 RUN_CONFIG、实际执行前后源码/输入绑定与 1.1 RUN_RECEIPT，并把运行事实写入 `运行配置`；不能只替换版本字符串。共用 `hsk_pipeline.result_io.write_workbook()` 接收调用方提供的工作表，因此可原样写入新 1.1 字段，但不会替入口自动生成或验证回执身份。

新 1.1 实例的数据身份模式服从执行 Authority：`project_level` 显式写 `data_identity_mode="preprocessing_workbook"`，只以已验收预处理 XLSX 作为 `data_paths`，沿用其普通文件 SHA；其他两种预处理决策默认 `combined`。不能把预处理工作簿改算为输入集合摘要来迁就模板。

## 推荐项目结构

每问布局只服从 `core/output_contract.yaml`。基础结构为三文件；方括号内 03B 文件只在 Gate=`required` 时存在：

```text
项目根目录/
├─ [hsk_pipeline/]  # 可选；只保留实际使用且已声明的源码
├─ 问题一求解/
│  ├─ 问题一求解.py
│  ├─ 问题一求解结果.xlsx
│  ├─ <绘图后端对应 q1_plot.py 或 q1_plot.m>
│  ├─ [问题一结果深化分析.py]
│  └─ [问题一结果深化分析.xlsx]
├─ 模型论文框架.md
└─ 赛题附件.xlsx
```

## 使用步骤

1. 优先提取题目所需数学模式形成自包含入口；确有复用需要时，按 `templates/code/hsk_pipeline/README.md` 复制实际依赖并静态声明，不默认复制旧 runner；
2. 新建 `问题一求解/`，把一个题型 starter 复制为 `问题一求解/问题一求解.py`；
3. 在新生成主脚本中实例化唯一顶层 `RUN_CONFIG`，锁定 `stage/problem_name/data_paths/data_sha256/solver/random_seed/tolerance/iteration_or_time_limit/expected_workbook` 等任务会变化的输入，`stage="primary"`、`solver_backend="python"`，并按执行合同选择回执协议。常规路径写入 `run_receipt_protocol_version="1.1.0"` 与 `primary_quality_protocol_version="1.0.0"`。选用已批准的质量规范绑定时，使用回执 1.3.0，在配置及回执中声明质量协议及摘要，并在回执中回显 JSON 路径列表 `data_paths` 和实际采用的 `data_identity_mode`。在 `主结果质量门` 写入已批准数值项的 `单位`。`code_dependencies` 列出实际使用的项目内源码，每项含项目相对 POSIX `path` 和文件 `sha256`，不含入口自身；复制的 `hsk_pipeline` 中实际依赖的源码也须纳入闭包。不要把最终 bundle 摘要写回它自身覆盖的 RUN_CONFIG，也不要重复声明 owner/profile/六个 no-degradation 标志；这些全局规则由执行 Authority 继承。`solver_version` 等实际运行事实留在返回工作簿中；
4. 按框架需求编号将各项必答量落实到 `solve_model` 的返回值和最终工作表，逐项追踪计算、返回、组表与写出。完整管线用 `answer_sheets=("站点峰值", ...)` 声明题目专属答案表，独立 IO 入口先调用 `validate_answer_tables`，自包含入口列入同一输出集合；再按 `modules/03_solve_validate.md#Primary Evidence Capture` 保留当前计算的状态与过程数据；
5. 主求解工作簿除核心指标外，应按题型实际存在情况保留决策变量、逐对象/逐时刻/逐节点状态、路径/流量/资源占用、目标分项、约束状态、候选解/Pareto candidate、求解轨迹、逐样本预测/残差/区间、关键事件等 current-run evidence。优先复用 `core/workbook_schema.yaml` 已登记的 `明细结果`、`状态明细`、`逐时刻结果`、`节点结果`、`边结果`、`路径或流结果`、`预测明细`、`决策变量明细`、`方案对比`、`Pareto结果`、`收敛诊断` 等表；不存在的结构不创建空表；
6. 03A/03B 边界按“是否改变当前主计算条件并重新运行”判断：保存当前运行已经产生的状态属于主求解；参数敏感性、压力场景、替代算法/结构、多 seed/初值结论稳定性、异质性、阈值搜索等不能因为计算便宜就提前塞入 03A；是否需要实际执行这些 alternative-world 分析由主工作簿 accepted 后的 Analysis Necessity Gate 决定；
7. 按 `core/numerical_verification_contract.yaml` 与当前 Primary Quality Specification，只实现本次主计算 accepted 所必需的内在数值有效性检查，例如可行性、方程/守恒残差、离散精度、迭代收敛、最低采样精度或其他已激活 capability；把底层证据与带 Verification ID 的 `主结果质量门` 写入主工作簿；
8. 助手按 `core/user_execution_contract.yaml` 与 `core/code_quality_contract.yaml` 检查并登记实际交付代码；
9. 用户运行主脚本，代码自动构造逻辑 `RUN_RECEIPT` 并写入既有工作簿 `运行配置(项目, 值)`，随后用户返回工作簿。新实例按执行 Authority 写所选版本的回执和真实源码／输入身份，保留运行前绑定、写出前重检及实际运行事实；助手再验收回执和主数值证据，不能只依赖工作簿自报“通过”；
10. 主工作簿 accepted 后冻结 `问题一求解.py`，执行 Analysis Necessity Gate。Gate=`not_required` 时记录非空 `result_analysis_requirement_reason`，不生成 `问题一结果深化分析.py/.xlsx`，也不得声称稳健性/稳定性已经验证；Gate=`required` 时依据真实主结果和评委风险单独生成 `问题一结果深化分析.py`；
11. 仅 Gate=`required` 且项目根已锁定 Python 后端时，深化分析脚本使用唯一顶层 `RUN_CONFIG`，写 `stage="analysis"`、`solver_backend="python"`、`run_receipt_protocol_version="1.1.0"` 及本阶段 `code_dependencies`，不写 `primary_quality_protocol_version`，以 `primary_workbook_sha256` 绑定已验收主工作簿。它继承当前数据事实源，只实现题目专属敏感性、鲁棒性、多算法、阈值、结构或场景分析；逐参数/逐场景/逐 seed/逐算法/逐区域/逐阈值真实底层数据也应落入分析工作簿，而不是只输出“稳定”；
12. Gate=`required` 时，深化分析脚本再次通过代码交付质量门后由用户运行，并返回 `问题一结果深化分析.xlsx`；该工作簿以 `run_receipt_version="1.1.0"` 记录本阶段后端、入口/bundle 摘要、主工作簿摘要和其他运行事实。原 1.0、P5a 与旧 `FULL_*` 只按原历史分支兼容；新 03A/03B 不主动写旧版本或省略握手，项目级 Python 预处理仍使用 1.0；
13. Figure 阶段按项目绘图后端生成同目录 `q1_plot.py` 或 `q1_plot.m`。主结果图可只读 accepted 主工作簿；若目标 Figure 明确使用 03B evidence，则必须读取真实、current 的 `问题一结果深化分析.xlsx`，缺失时 fail closed。当前 qX_plot.py/m 只读工作簿绘图，并按 Scientific Figure Synthesis / Composite Encoding / Rendering Profile 选择科研表达。

影响本次主计算能否验收的检查归主求解质量。检验扰动、替代方法、压力条件或扩展范围下的结论稳定性，须在主簿验收后经 Analysis Necessity Gate 判定。Primary Evidence Capture 保存本次运行已有状态。

选用正式执行规模时，按 `core/user_execution_contract.yaml` 为当前主求解或深化分析实例化回执 1.4.0，冻结 `execution_scale_plan` 和 `execution_scale_plan_sha256`。实际回执回显摘要、JSON 路径列表 `data_paths`、`data_identity_mode`，并用实际记录计算整数 `actual_scale_count`。按所选轴写入 `重复试验结果` 或 `场景压力测试`。自适应主求解按已批准的数值 PQS 判据记录 `执行停止证据` 的检查点、指标、数值和单位。与已批准质量规范组合时，继续输出该规范要求的字段。

不生成独立运行配置、RUN_RECEIPT 文件、运行说明或校验报告。不得把主求解与已激活的深化分析重新拼成一个大脚本；若深化分析表明主模型必须修改，应回退主求解或模型设计阶段，而不是在深化分析脚本中偷偷重写主模型。

## 可选辅助输入：回执 1.2

项目级预处理已验收后，主求解或深化分析只将该 XLSX 路径及其普通 SHA 登入 `data_paths`、`data_sha256`。若另需未覆盖的独立附件，按 `core/user_execution_contract.yaml#code_delivery.auxiliary_inputs` 使用 1.2，成对登记 `auxiliary_data_paths` 与 `auxiliary_data_sha256`，排除主来源及已覆盖原始数据。辅助值实际进入模型；运行前后核对主数据、附件和源码。回执在工作簿“运行配置”按 JSON 文本写路径数组，摘要与交付配置一致。本节基础回执无辅助输入时用 1.1，项目级预处理本身用 1.0。旧读取器须拒绝不支持的 1.2 回执，不得略去附件或降版。合成用例见 `tests/audit_auxiliary_smoke.py`。

## 两类条件式比较例子

`analysis_comparison.py` 与 `comparison_numerics.py` 是可实例化的微型模式，不是任意题目的默认模型。复制入口及实际 helper 到本问目录；Python 入口仍按输出 Authority 命名，helper 路径与原始 SHA 必须加入 `code_dependencies`。入口包含维护 fixture 所用 primary 分支；正式 analysis 实例只读取已验收主簿，不调用主入口、不重算其 QR 基准。

例子在声明训练点上分别真实执行一阶 QR 和二阶 SVD，并与 accepted 二阶 QR 基准比较；没有固定填入 11 或 16。多模型表呈报冻结留出点，同模型多算法表呈报全部声明评价点，保留实际差异、残差、方法／版本和停止原因。实例化时替换数学规范、输入、评价、判据和预期 selectors，按现行 Authority 完成范围审查、冻结计划、代码交付与用户执行。选用本扩展的配置及回执声明 `analysis_comparison_protocol_version` 和 `analysis_comparison_plan_sha256`；不整体改 receipt 1.1/1.2。

维护运行入口是 `tests/analysis_comparison_smoke.py`，分别在独立 Python/MATLAB 项目里验证真实求解、交付／回执和主簿保护。旧敏感性模式继续保留。无支持扩展的工具不能用旧 Boolean 校验代替新比较验收。
