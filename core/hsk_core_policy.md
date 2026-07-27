# HSK Core Policy v6.3.1

本文件只保存全局硬规则。任务路由、产物图、分类、输出、工作簿和项目状态分别以 `core/workflow_router.yaml`、`core/module_manifest.yaml`、`core/task_taxonomy.yaml`、`core/output_contract.yaml`、`core/workbook_schema.yaml` 和 `core/project_state.schema.yaml` 为准，其他文件不得复制出第二套冲突规则。

## 1. 总目标与优先级

数学建模任务必须形成可提交、可复现、可解释、可审查、可答辩的闭环。优先级为：

$$
\text{题意正确}>\text{机制与变量闭合}>\text{数据可信}>\text{求解可靠}>\text{结果可验证}>\text{图表证据}>\text{论文表达}>\text{形式创新}.
$$

不能落地、不能解释、不能检验、不能复现的模型必须否决、降级或重构。禁止为了高级模型、复杂图表、代码规模、命题数量或排版炫技偏离题意。

## 2. 启动与按需加载

1. 首先读取 `core/bootstrap.yaml`；
2. 使用 `scripts/resolve_workflow.py` 根据一个或多个用户意图生成确定性执行计划；
3. 只加载命中的模块、题型 Pack、竞赛 Pack、交付 Pack 和必要模板；
4. `legacy/` 不参与默认执行；
5. 不再要求在路由前通读整个 Skill、所有模块或全部资产。

## 3. 逐问正交分类

每个小问分别记录：

- `classification.objective`：explanation、inference、prediction、evaluation、optimization、simulation 之一；
- `classification.structures`：physical_mechanism、temporal、spatial、network、scheduling、game、stochastic、static_tabular 中至多三项；
- 小问顶层 `capabilities`：独立决定必须执行的可行性、残差、离散、收敛、外样本、不确定性、泄漏、校准或可识别性检查。

顶层 `capabilities` 是唯一权威能力事实源。`classification.capabilities`、`problem_types` 和 `legacy_task_packs` 只允许作为旧项目兼容派生字段，存在时必须与当前三轴事实完全一致。

## 4. 工作顺序与最小闭环

默认顺序：审题 → 模型设计与锁定 → 创建或重写 `模型论文框架.md` → Python 求解验证 → 两类中文结果工作簿 → 同步逐问结果摘要 → MATLAB 结果图 → DOCX 草稿 → 核心机理图精修 → LaTeX 草稿 → AI 模板感清除 → 编译 → 终审提交。

每问至少闭合：目标与依赖、两条实质路线、数据协议、变量、3--5 个关键假设、核心公式与约束、Python 实现、适用检查、敏感性与鲁棒性、结果工作簿、图表证据和最终结论。

任务可直接跳转，但不得伪造缺失前置结果。已有可靠成果必须复用。

## 5. 当前模型框架与三类事实源

`locked_model_spec` 形成后，项目根目录必须创建 `模型论文框架.md`。该文件只保留当前有效模型语义、论文结构、逐问结果摘要、必要命题规划和图表映射，旧版本由 Git 历史保存。

框架分为 compact 与 full。compact 用于日常迭代，full 用于跨聊天交接、完整写作、终审和提交；校验器必须读取 mode 并应用对应章节集合。

事实源边界：

- 模型语义与论文组织：`模型论文框架.md`；
- 数值事实：每问两类标准工作簿；
- 分类、分层哈希、新旧状态与产物路径：`state/project_state.yaml`。

三者冲突时停止下游写作，回到源产物修正。

## 6. 正式交付同步门槛

所有正式模型、代码、工作簿、验证、MATLAB 图、DOCX、LaTeX 或提交包交付，必须执行解析器返回的 `pre_delivery_gates`。`project_sync` 使用：

```bash
python scripts/sync_project.py <project_root> --write --strict --delivery-scope <scope>
```

scope 为 design、results、figures、docx、latex 或 submission。同步器按阶段检查必需产物、工作簿 Schema、MATLAB 工作簿引用、图表存在性与时间新旧关系；计算 data、model、solution_workbook、robustness_workbook、matlab_script、figure_bundle 和 framework 分层哈希；只允许保守传播 stale，不得生成模型语义、伪造结果或将未验证状态提升为 passed。

写入顺序固定为：发现与检查 → 计算当前哈希 → 传播 stale → 更新框架头部 → 计算最终框架哈希 → 写 project_state → 写 sync_report → 写后自检。`sync_report.yaml` 只有在 gate 成功后才视为可用产物。

## 7. 软件职责与目录

- Python：数据读取、预处理、特征构造、模型求解、优化、仿真、检验、敏感性、鲁棒性、工作簿输出；正式求解脚本默认不绘制论文图。
- MATLAB：读取同目录两类工作簿绘制正式结果图，不重新计算核心结果。
- GeoGebra、PPT、draw.io、SVG、TikZ：按需绘制非数据驱动机理图。
- DOCX：前期修改与逻辑检查；LaTeX：终稿与 PDF。

```text
项目根目录/
├─ 赛题与附件
├─ 模型论文框架.md
├─ 问题一求解.py
├─ state/project_state.yaml
├─ sync_report.yaml
└─ 结果数据表/问题一/
   ├─ 问题一求解结果.xlsx
   ├─ 问题一敏感性与鲁棒性结果.xlsx
   ├─ q1_plot.m
   └─ 图表/
```

## 8. 求解与验证

- 精确或凸问题报告求解器状态、最优间隙、KKT 或理论条件；
- 非凸问题使用多初值、全局启发式加局部精修、上下界或网格/分支复核；无证明不得写“全局最优”；
- 组合优化保留下界、松弛、重复运行和基准算法；
- 预测与机器学习必须检查泄漏、外样本、误差、校准与不确定性；
- 仿真必须给随机种子、重复试验、置信区间和收敛；
- 数值机理必须检查量纲、边界、守恒和离散精度。

工作簿由 objective 决定主要结果类型，structures 决定结构专项，capabilities 决定强制验证工作表。旧 task_profiles 仅兼容历史项目。

## 9. 图表

正式 MATLAB 代码生成前必须读取实际工作簿。字段定位采用“精确表头唯一匹配”，允许记录期望列号作结构漂移警告，但不得模糊匹配、别名猜测或自动回退。MATLAB 只能引用本问标准工作簿；声明导出的图必须存在，正式图不得早于其工作簿或脚本。单图保留简洁 `title`，多面板保留一个 `sgtitle`；图注补充统计口径和解释，不与标题逐字重复。

机理图必须服务对象关系、公式来源、约束来源、临界状态或策略机制，不用通用“输入—模型—输出”流程图替代。

## 10. 命题与证明

全局只保留三条硬规则：命题可以为 0 且全文最多 4 个；命题必须实际简化问题、说明模型必要性、识别关键点、降维、删减约束、保持可行或给出理论边界；数值实验不能替代证明。只有命题计划非零或用户明确要求证明时，加载 `packs/artifact/proposition_proof.md`。

## 11. 写作与终审

DOCX 与 LaTeX 必须先读取当前框架，再从标准工作簿复核数值。LaTeX 草稿必须先清除空泛价值判断、机械连接词、无证据的“显著提高”、无作用命题和模板化检查表，再进行最终编译。中文国赛保留 `cumcmthesis`。

信息充分时直接推进；只有关键歧义会改变模型、数据口径、约束或交付时才提问。
