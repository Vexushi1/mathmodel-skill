# HSK Core Policy v7.2.1

本文件只保存全局硬规则。题意口径、语义闭环和语义变更状态以 `模型论文框架.md`、`core/project_state.schema.yaml` 与 `scripts/validate_semantic_governance.py` 为准；目录与交付文件以 `core/output_contract.yaml` 为准；数据审计、`preprocessing_decision` 与条件式统一数据预处理以 `core/global_preprocessing_contract.yaml` 为准；用户本地执行与工作簿验收以 `core/user_execution_contract.yaml` 为准；题目专属 Python 工程质量以 `core/code_quality_contract.yaml` 为准。本文件不复制这些合同的完整字段。

## 1. 总目标与优先级

数学建模任务必须形成题意正确、机制闭合、数据可信、数值可复现和结果可审查的成果链。优先级为：

$$
\text{题意正确}>\text{语义与机制闭合}>\text{数据可信}>\text{完整版数值求解}>\text{结果证据}>\text{图表}>\text{论文表达}>\text{形式创新}.
$$

不能落地、不能解释、不能检验或不能复现的模型必须否决、降级或重构。运行成功、结果合理、多个算法一致都不能替代题意和模型语义正确性。

## 2. 四项前置语义治理硬规则

### 2.1 Problem Contract：题意口径冻结

进入模型设计前，每问必须冻结研究对象、原始/派生对象、已知/可计算量、决策/状态/输出量、显式/隐含约束、禁止假设、数据角色与小问依赖。不得根据附件呈现方式、已有程序、求解方便性或结果表象反推题意。关键歧义未解决时不得锁模。

### 2.2 题面—数学—代码三层闭环

每个核心对象、条件、变量、目标、约束和输出必须形成：

$$
\text{题面对象与要求}
\rightarrow
\text{数学变量/关系/目标/约束}
\rightarrow
\text{Python变量/函数}
\rightarrow
\text{工作簿输出或验证证据}.
$$

出现“题目要求有、代码没有”“代码有、数学层无来源”“数学关系无题意/机制依据”或单位、粒度、索引含义断裂时，正式代码交付必须停止。

### 2.3 模型语义修改治理

题意解释、数据范围、变量、参数、假设、目标函数、约束、`preprocessing_decision`、实际预处理、算法语义或小问依赖发生变化时，必须递增当前小问 `semantic_revision` 并记录变更类别。`模型论文框架.md` 只保留当前有效版本，历史由 Git 保存。

已验证语义发生变化时，先将受影响结果及下游标记 stale，再按 `depends_on` 的 `data / parameter / model / result` 依赖递归传播。不得因为项目存在共享数据，就无差别失效所有小问。

### 2.4 Complexity Sanity Check

复杂赛题异常退化为低维直接计算、弱耦合独立求解、动态转静态、多主体转单主体，或题目专门条件/附件字段大量闲置、关键约束长期不生效、后问近乎复制前问时，必须触发复审。无法证明简化合理时，`complexity_sanity_status=review_required`，禁止进入主求解。

上述语义治理由 `scripts/validate_semantic_governance.py` 在正式模型、代码、返回工作簿和下游交付前执行。该门不运行赛题代码、不生成数值结果，也不清除数值 stale。

## 3. 数据审计与条件式预处理

**所有数据题先审计，但不是所有数据题都要清洗或建立统一预处理工作簿。**

模型设计阶段必须形成 `preprocessing_decision`：

```text
not_needed
question_local
project_level
```

硬规则如下：

1. 字段、维度、单位、主键、NaN/Inf、重复、时间/空间粒度等非破坏性数据审计默认执行；
2. 两个及以上小问共享同一原始数据源，只触发统一口径审计，**不能单独推出需要项目级预处理**；
3. 原始数据已满足模型要求时，`decision=not_needed`，不创建 `数据预处理/`，各问可直接读取原始数据；
4. 仅某一问需要对数、标准化、滞后、窗口或专属派生特征时，`decision=question_local`，由本问脚本在数学层有来源的前提下构造，不建立全局预处理目录；
5. 只有多个小问确实依赖同一公共单位、坐标、时间、主键、采样、缺失、异常、滤波或其他有依据的数据变换时，才使用 `decision=project_level`；
6. `project_level` 才创建：

```text
数据预处理/
├─ 数据预处理.py
└─ 数据预处理结果.xlsx
```

7. 缺失填补、异常删除、插值、平滑、滤波、去噪、标准化、归一化、重采样等修改数据的操作必须逐项有数据、机理或模型必要性证据；统计极端值不得直接等价为错误数据；
8. `project_level` 的统一工作簿通过质量门后，依赖该公共数据口径的下游脚本不得重新读取对应共享原始数据；`not_needed` 与 `question_local` 不受此限制；
9. 地震、时序、空间、传感器等题的去趋势、滤波、插值、坏道修复、taper 等均为条件操作，不得写成默认模板步骤。

完整判定、操作四问门、地震审计和 stale 规则以 `core/global_preprocessing_contract.yaml` 为唯一事实源。

## 4. 每问唯一数值交付目录

新项目每个小问只建立一个 `问题X求解/`，最终默认恰好包含：

```text
问题X求解/
├─ 问题X求解.py
├─ 问题X求解结果.xlsx
├─ 问题X结果深化分析.py
├─ 问题X结果深化分析.xlsx
└─ qX_plot.m
```

两个 Python 文件职责分离。`问题X求解.py` 只负责主求解；主工作簿 accepted 后冻结。随后单独生成 `问题X结果深化分析.py`，继承当前 `preprocessing_decision` 与数据事实源，完成题目专属深化分析。不得为了深化分析覆盖改写主求解脚本，也不得在该目录增加独立配置、运行说明、校验报告、图表目录或元数据文件。

## 5. 用户执行与质量门

实际生成的 `数据预处理.py`、`问题X求解.py` 与 `问题X结果深化分析.py` 均由助手生成和静态检查、由用户本地 full-fidelity 执行。

- `project_level`：预处理工作簿 accepted 且 `预处理质量门` passed 后才能进入依赖主求解；
- `not_needed/question_local`：没有预处理工作簿门槛，不能因为该文件不存在而阻塞；
- 主工作簿通过当前语义、运行配置、代码/数据哈希与 `主结果质量门` 后才进入 `solved`；
- 深化工作簿通过运行配置、代码/数据哈希、`分析设计` 与 `结论稳定性汇总` 后才进入 `analyzed`。

助手不得运行、导入或间接执行题目专属预处理、主求解或深化分析脚本，不得自动缩减数据、网格、时域、场景、重复次数、迭代次数或放宽容差，也不得静默切换求解器或轻量近似。

## 6. 软件职责

- Python 条件式项目级预处理：仅 `project_level` 时读取共享原始数据，执行已批准公共处理，输出 `数据预处理结果.xlsx`；
- Python 主求解：按 `preprocessing_decision` 读取原始数据或统一工作簿，完成模型求解、质量门和主工作簿；
- Python 深化分析：继承同一数据事实源，读取已验收主结果与必要前问结果，完成题目专属深化分析；
- MATLAB：优先读取本问标准结果工作簿；只有图确实需要底层数据时，才按 `preprocessing_decision` 读取原始数据或统一预处理工作簿；不重新求解；
- LaTeX：默认论文主链；
- DOCX：仅用户明确要求时加载，不是 LaTeX 前置。

MATLAB 默认只保留图窗，不自动创建图表目录或批量导出正式图片。

## 7. 元数据与兼容边界

`run_info.json`、`result_manifest.yaml` 和 `matlab_figure_handoff.json` 只在用户明确要求完整复现包时生成，并放入项目级内部元数据目录，不得放入 `问题X求解/` 或 `数据预处理/`。

v7.2.0 项目重新进入模型设计或求解时，先补齐 `preprocessing_decision`；不得因为历史上存在共享数据就默认迁移为 `project_level`。v7.1.x 及更早项目继续只读兼容；重新进入当前流程时先审计数据并形成判定。v7.0.x 缺少语义治理字段的项目按既有兼容规则迁移；v6.6.x 单脚本四文件项目和旧 `结果数据表/问题X/` 继续只读兼容。

## 8. 正式交付同步

- 语义治理：`scripts/validate_semantic_governance.py`；
- 条件式项目级数据预处理：`modules/03_data_preprocessing.md` + `core/global_preprocessing_contract.yaml`；
- 代码交付：`scripts/validate_code_delivery.py`；
- 用户返回工作簿：`scripts/validate_user_execution.py`；
- 图表、论文和提交包：`scripts/sync_project.py`。

同步器必须根据 `preprocessing_decision` 判断数据事实源和条件产物：`project_level` 才要求预处理脚本/工作簿；`not_needed/question_local` 不得因不存在预处理目录而失败。同步器只做发现、校验、哈希与 stale 传播，不自动生成模型语义、数据处理决策、数值结果或 passed 状态。
