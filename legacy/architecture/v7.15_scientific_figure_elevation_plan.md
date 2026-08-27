# HSK Skill 科研证据型绘图升级实施计划

> 状态：implementation plan / scope anchor  
> 当前活动版本：v7.14.1  
> 目标版本建议：v7.15.0（minor）  
> 当前实施分支：`fix/v7.14.2-chart-selection-degeneracy`  
> 说明：分支名沿用本聊天前期创建名称；由于本次范围已从“修复图型退化”扩大为“新增主求解证据保留能力 + 科研图综合表达能力”，按 `SKILL_CHANGE_GOVERNANCE.md` 的版本规则，实施目标建议由 patch 重分类为 minor，即 v7.14.1 → v7.15.0。正式实施前不修改 release carrier。

## 0. 本文件用途与上下文隔离规则

本文件是本轮仓库修改的**唯一实施范围锚点**。后续每一批修改开始前都先重新读取本文件，再读取本批次涉及的当前 `main` Authority；不得依赖聊天记忆补全规则，不得边改边扩张范围。

本文件不是 Runtime Authority，不进入最终 Skill 默认加载链。活动行为仍以 `core/bootstrap.yaml` 指向的 Authority、modules、packs、scripts、schemas 和 tests 为准。

实施阶段结束、代码与 CI 完成后，本文件应从根目录退出活动表面，并原样归档到 `legacy/architecture/` 作为 provenance；最终活动规则必须落在唯一 Authority，而不是让运行时代码依赖本计划。

若后续讨论出现新的无关需求，必须另开主题，不得混入本计划。

---

# 1. 修改主题

**主求解 Evidence-ready 输出 + MATLAB Scientific Evidence Visualization 升级 + 高对比科研配色恢复。**

当前主要问题不是“缺少几个图型”，而是两端同时存在信息损失：

1. Python 主求解常把已经真实产生的状态、过程和结构数据压缩成少量最终指标，导致 MATLAB 到绘图阶段可用证据不足；
2. MATLAB 当前虽然具备 Layout Gate 和 Enhancement Gate，但仍可能把丰富问题退化为普通柱状图、条形图、普通折线、普通散点等低信息密度表达；
3. v7.14.1 将配色收敛到深色低饱和后，与当前用户明确要求的“高对比、鲜红、亮蓝、第一眼可识别主次”的视觉目标不一致；
4. 组合图、局部放大、全局—局部、多视角和图型专属科研表达尚未形成足够强的优先规则。

本轮目标不是增加装饰，而是让：

```text
模型设计
→ 主求解保留真实状态证据
→ 结果深化分析保留改变条件后的细粒度证据
→ MATLAB 从证据结构出发合成科研级 Figure
→ 高对比视觉强化关键结果
→ Figure Portfolio 终审
```

形成闭环。

---

# 2. 直接目标

## 2.1 Python 主求解：从 final-answer-only 升级为 evidence-ready output

`问题X求解.py` 除最终答案外，应按模型 capability 尽可能保存**本次正式主计算已经真实产生、且对解释模型、绘图、数值验证、复现或避免昂贵重算有价值的数据**。

典型数据包括但不限于：

- 决策变量；
- 状态变量；
- 逐对象结果；
- 逐时刻状态；
- 空间节点/网格状态；
- 路径、流量、覆盖、资源占用；
- 目标函数分项；
- 约束实际值、违反量、裕量、active/binding 状态；
- 当前算法自然产生的候选解/可行解池；
- 当前算法自然产生的迭代 objective、gap、residual、feasibility trace；
- 预测任务中的逐样本真实值、预测值、残差、合法区间、数据分组/时间/区域键；
- 关键事件、临界状态、几何位置、距离、角度等主模型内部状态。

### 03A/03B 硬边界

判断一份数据是否允许在 03A 产生，不按“便宜/昂贵”区分，而按：

> 为得到该数据，是否需要改变当前 accepted-candidate 主计算的输入、参数、场景、seed、初值、算法、模型结构或验证窗口，然后再运行一次新的世界？

- **否**：属于 current-run capture，可进入 03A；
- **是**：属于 alternative-world analysis，必须留在 03B。

因此以下仍只属于 03B：

- 参数敏感性；
- 现实扰动；
- 场景压力；
- 阈值/失效边界搜索；
- 替代算法；
- 替代模型结构；
- 多 seed / 多初值稳定性；
- 异质性；
- 误差分解；
- 广义 OOS / 跨年份 / 跨区域稳定性；
- claim stability。

本轮不得削弱 v7.14 主数值有效性协议，也不得把 03B 内容提前塞回主结果质量门。

---

# 3. Python 工作簿输出策略

不建立“所有问题都必须有几十张 Sheet”的固定模板。

采用 capability-driven Evidence Tables：

```text
核心指标                 必需时存在
推荐方案                 适用时存在
决策变量                 适用时存在
逐对象状态               适用时存在
逐时刻状态               适用时存在
空间状态                 适用时存在
候选解集                 适用时存在
约束状态                 适用时存在
误差与残差               适用时存在
求解轨迹                 适用时存在
主结果质量门底层证据     按现有协议存在
```

原则：

1. 不保存纯 debug 噪声；
2. 不为绘图伪造额外数据；
3. 不保存 MATLAB 可以安全完成的纯视觉变换；
4. 优先保存“一旦丢失就需要昂贵重算”的 current-run 状态；
5. 摘要表服务论文表格，细粒度 Evidence Tables 服务科研绘图、验证与复现。

若需要修改 `core/workbook_schema.yaml`，优先采用向后兼容的可选 capability/worksheet 语义，不破坏 v7.14.x 历史工作簿只读兼容。

---

# 4. 03B 结果深化分析保持独立，但同步提高证据粒度

03B 职责不变：只在主工作簿 accepted 后，基于真实主结果建立 `result_analysis_plan`。

但分析输出不能只保留“模型稳定”“变化不大”等摘要结论，应尽量保留完整底层证据，例如：

```text
参数值 × 响应
场景ID × 结果
seed × 结果
算法 × 实例 × 指标
区域/对象 × 参数 × 响应
阈值扫描状态
可行/失效标记
排名/策略切换
失败标记
```

MATLAB 后续只读取这些已验收工作簿完成表达，不重新做分析。

---

# 5. MATLAB 职责重新定义

MATLAB 不再只被描述为“读取 Excel 后美化绘图”。

新职责定义：

> **MATLAB 基于 Python 已验收的细粒度证据数据，完成 Scientific Evidence Visualization：科学视觉编码、组合表达、结构表达、全局—局部组织、统计/不确定性表达与论文证据强化；不得重新计算核心结果。**

继续保留：

- 不重新求解；
- 不重做 Python 数据变换；
- 不从摘要数字反推数据；
- 不篡改数据；
- 正式论文图不设置整体 `title` / `sgtitle`；
- DOCX/LaTeX caption 承担正式图号和图名；
- 默认图窗可见；
- 默认不批量自动导出；
- 默认 `grid off`，确需网格时浅、稀、置于数据后方。

---

# 6. 新增 Scientific Figure Synthesis Gate

正式绘图前，不先问“bar 还是 line”，而先识别 Evidence Structure：

- 简单离散比较；
- 分布；
- 时间演化；
- 空间结构；
- 机制关系；
- 约束边界；
- 可行域；
- 参数响应；
- 不确定性；
- 多目标权衡；
- 稳定/风险/失效区域；
- 网络流；
- 资源调度；
- 诊断结构；
- 全局—局部结构。

流程：

```text
Core conclusion
→ Evidence level / Primary question
→ Available evidence dimensions
→ Scientific Figure Synthesis Gate
→ Candidate visual structures
→ Selected visual structure
→ Figure Layout Gate
→ Figure Enhancement Gate
→ QA
```

图型选择必须从“证据结构”推导，而不是从模板默认函数推导。

---

# 7. Basic-form Challenge：尽量避免基础图敷衍核心结论

以下形式允许存在，但默认只属于 F1 基础表达：

- plain bar / barh；
- plain line；
- plain scatter；
- plain boxplot；
- plain histogram。

如果它们准备进入正文核心 Figure，必须检查当前数据是否还包含：

- 时间结构；
- 空间结构；
- 原始样本分布；
- 不确定性；
- 误差；
- 约束/可行边界；
- 机制变量；
- 参数交互；
- 多目标关系；
- 全局—局部差异；
- 关键事件/阈值。

只要存在这些结构且能提高可验证信息密度，就优先升级表达。

**不禁止柱状图，但禁止“明明有更丰富证据，却只用一个普通柱状图结束”。**

---

# 8. Figure 表达等级

## F1：基础表达

普通柱状、条形、折线、散点、箱线、直方。

适合：简单事实、辅助图、附录、真正的一维离散比较。

## F2：增强科研表达

优先候选：

- box + raw scatter；
- violin + raw scatter + median/quartile；
- line + uncertainty band；
- scatter + fit/identity line + CI；
- scatter + marginal histogram/KDE；
- bar + errorbar + benchmark/reference；
- bar + line（仅当二者共享清晰语义，谨慎双轴）；
- heatmap + annotation；
- heatmap + contour；
- ECDF + quantile；
- Gantt + resource utilization；
- network + weighted flow；
- Pareto + highlighted recommendation。

## F3：核心科学综合图

优先用于正文 S 级 Figure：

- spatial field + trajectory + boundary + critical state；
- Pareto front + feasible/infeasible state + knee + recommendation + zoom；
- response surface + contour + current point + stable/failure region；
- prediction relation + uncertainty + residual/marginal diagnostic；
- trajectory/state evolution + event/threshold + local detail；
- optimization candidate cloud + constraint/feasible structure + recommended solution。

F3 的“高级”来自证据结构，不来自 3D、渐变或装饰数量。

---

# 9. Composite Encoding Preference：正式提高组合图优先级

如果多个视觉编码在**同一证据空间**共同回答一个 Primary Question，优先考虑融合，而不是机械拆成多个低级图。

重点支持：

```text
箱线 + 散点
小提琴 + 散点 + 中位数/四分位
折线 + CI/预测区间
散点 + 拟合/1:1线 + CI
散点 + marginal density/histogram
柱状 + 误差棒 + 基准线
柱状 + 折线（有明确联合语义时）
热力图 + 等高线
热力图 + 阈值/可行边界
3D surface + 2D contour projection
Pareto + 推荐点 + Local Zoom
轨迹 + 空间场 + 边界
真实—预测 + 区间 + 残差结构
```

禁止为了“看起来高级”强行组合互不相关的指标、滥用双 Y 轴、堆叠过多视觉编码。

---

# 10. Scientific Rendering Profiles：图型专属科研表达

在选定视觉结构后，进入对应 Rendering Profile，而不是所有图都调用同一基础模板。

建议至少覆盖：

## 10.1 Distribution Profile

- raw samples 优先可见；
- box/violin 与 scatter/swarm/jitter 组合；
- 明确 median / quartile / sample size；
- 小提琴 KDE 带宽必须反映真实分布，不得制造假结构。

## 10.2 Regression / Prediction Profile

- scatter；
- fit 或 identity line；
- 合法 CI / prediction interval；
- residual 或 marginal 结构；
- 必要时标出异常点，但不堆标签。

## 10.3 Dynamic Profile

- trajectory / state curve；
- uncertainty band（若真实存在）；
- event / threshold line；
- phase/stable-risk background（有真实语义时）；
- critical point；
- Local Zoom。

## 10.4 Parameter Surface Profile

优先：

- heatmap + contour + current/recommended point + feasible boundary；

第三维真实且二维投影损失结构时才：

- 3D surface + contour projection + colorbar。

## 10.5 Spatial Profile

- spatial field；
- path / flow；
- critical nodes；
- boundary；
- colorbar；
- focus highlighting。

## 10.6 Optimization / Pareto Profile

- candidate solutions；
- Pareto set/front；
- feasible/infeasible state；
- recommendation；
- knee / threshold；
- global + zoom/detail。

## 10.7 High-density Scatter Profile

样本量大、点严重遮挡时，按数据结构考虑：

- alpha scatter；
- hexbin / binned density；
- 2D histogram；
- density contour；

不得让大样本散点退化成一团不可读的颜色块。

---

# 11. Figure Layout、局部放大与单图拆分

继续保留当前 Layout Gate，不设置固定 2×2 默认模板。

但强化以下优先级：

1. 能在同一证据空间融合 → 优先组合编码；
2. 观察空间不同但共同证明一个结论 → 多面板；
3. 关键差异被全局尺度压缩 → Local Zoom / detached detail；
4. 一张图压缩后只能退化成低信息密度基础图 → 允许拆成 2–3 张高价值科研图；
5. 正文核心 Figure 原则上仍不超过 4 panels，small multiples 等有真实矩阵语义时例外。

Local Zoom 重点适用于：

- Pareto 膝点；
- 临界阈值；
- 轨迹交汇；
- 碰撞/遮挡临界状态；
- 局部误差；
- 关键时间窗；
- 残差尾部；
- 算法接近区域。

禁止通过任意截轴、缩放或放大窗口制造虚假差异。

---

# 12. 高对比配色恢复

用户明确要求恢复**高对比、中高饱和、鲜红/亮蓝等主色**，让评委第一眼识别差异。

恢复 v7.14.0 之前活动 helper 的高对比基线：

```text
亮蓝        #1478FF   RGB [20,120,255]
鲜红        #F04444   RGB [240,68,68]
亮绿        #16B364   RGB [22,179,100]
亮橙        #F79009   RGB [247,144,9]
亮紫        #7A5AF8   RGB [122,90,248]
深灰        #252B37   RGB [37,43,55]
浅灰        #E9EAEB   RGB [233,234,235]
```

配色原则：

- 主比较优先亮蓝 vs 鲜红；
- 正向/可行可使用亮绿；风险/恶化可使用鲜红；
- 第三、第四主对象可使用亮橙、亮紫；
- 参考、背景、辅助对象用深灰/浅灰或透明度降权；
- 主结果颜色允许鲜明，但背景保持白色、边框和辅助元素克制；
- 主数据与背景保持高明度对比；
- 同一对象/语义全文颜色一致；
- 不使用 rainbow / jet / HSV 无序彩虹；
- 红绿不得作为唯一可辨识编码，需辅以 marker/linestyle/shape；
- 连续量使用连续色图，正负/偏差量使用发散色图；连续色图选择机制可以吸收用户提供的 Python 绘图总结，但 MATLAB 具体 colormap 必须服从数据语义。

本轮应把 v7.14.1 中“主色默认低饱和”的活动规则改回“主结果高对比、中高饱和；辅助元素克制”。

注意：高对比 ≠ 全图所有元素都鲜艳。视觉注意力仍必须集中在核心证据上。

---

# 13. 从用户提供的《2026国赛超精美图表AI自动优化升级提示词》吸收的技巧

该文档作为**设计参考源**，不是仓库 Authority。只吸收与 HSK 证据驱动规则兼容的技巧：

吸收：

- Data First；
- Less is More；
- 高对比主数据 + 低权重辅助元素；
- 颜色 + marker + linestyle 联合编码；
- errorbar / CI / uncertainty 可视化；
- scatter + fit + CI；
- marginal histogram/KDE；
- box/violin + raw scatter；
- heatmap + annotation；
- surface + contour projection；
- high-density scatter → hexbin / density；
- 关键点 annotation hierarchy；
- colorbar 完整标注；
- 连续/发散/分类色图按数据语义选择；
- 图型专属 Rendering Profile；
- Missing Scientific Evidence Check。

不吸收：

- “原图类型必须保持”——HSK 允许在数据不变时重新设计更优视觉结构；
- 图内总标题——继续坚持 caption-owned title；
- 默认开启主网格——HSK 继续默认 grid off；
- 对离散实验点使用 spline 美化——HSK 继续禁止无数学依据平滑；
- 机械按字数/图文比自动补图；
- 通用装饰流程图；
- 默认 9-panel；
- 3D 柱状图；
- 为“顶刊感”增加无证据复杂元素。

---

# 14. Figure Contract 扩展方向

在现有字段基础上，建议增加或强化：

```text
Evidence structure
Available evidence dimensions
Figure level: F1 / F2 / F3
Candidate visual structures
Selected visual structure
Basic-form challenge
Composite encoding
Scientific Rendering Profile
Global/detail strategy
Scientific value rationale
Rejected alternatives
```

Figure Contract 不记录大量 MATLAB 实现参数，避免把项目语义合同变成样式配置文件。

---

# 15. Figure Portfolio Scientific Quality Gate

进入 DOCX/LaTeX 前，检查正文核心 Figure 集合。

如果出现大量：

```text
plain bar
plain bar
plain line
plain scatter
```

即使单图没有技术错误，也触发 Portfolio Review，检查：

1. Python 是否只输出摘要而丢失状态；
2. 是否存在时间/空间/分布/边界/机制/不确定性证据但未使用；
3. 是否跳过 Scientific Figure Synthesis；
4. 是否可以使用组合编码；
5. 是否需要 Global–Detail / Local Zoom；
6. 是否存在更适合的图型专属 Rendering Profile。

不得设置“必须有 N 种不同图型”这种机械多样性指标。

---

# 16. Missing Scientific Evidence Check

不按“章节字数/图文比”机械补图，而按核心结论检查：

- 核心机制是否只有文字而无机理图；
- 核心空间结构是否只有汇总数字；
- 核心动态过程是否被压成最终值；
- 关键阈值/边界是否无直接视觉证据；
- 重要不确定性/分布是否只报均值；
- 主结果是否只有表格、但存在明显更有效的科研图表达。

只有存在真实证据源时才补图，不编造数据。

---

# 17. 明确不做

本轮禁止：

- 改变 03A / 03B 语义边界；
- 修改 `core/numerical_verification_contract.yaml` 的主协议语义；
- 把敏感性/鲁棒性提前塞入主求解；
- 让 MATLAB 重新求解或重新分析；
- 强制每问固定一种图型；
- 禁止所有柱状图/折线图；
- 强制每问使用 3D；
- 强制每张图使用组合图；
- 强制每张图高饱和多色；
- 使用 rainbow/jet 作为默认色图；
- 滥用双 Y 轴；
- 对离散数据无依据平滑；
- 为了“高级”制造不存在的数据；
- 机械按图文比补图；
- 新建庞大的独立 Figure 配置系统；
- 破坏历史工作簿读取兼容；
- 删除 V622 compatibility pointers；
- 删除 `assets/nature_figure/**`。

---

# 18. 预计影响文件

正式实施前仍需按当前 `main` Authority 逐项核验，预计重点涉及：

```text
modules/03_solve_validate.md
modules/03_result_analysis.md
modules/04_figure_evidence.md

core/workbook_schema.yaml              # 仅在 capability-driven evidence schema 确有需要时
core/module_manifest.yaml              # 若 artifact contract 需同步
core/output_contract.yaml              # 仅在交付语义需同步时

packs/artifact/figure.md

templates/figure/result_figure_contract.md
templates/figure/result_figure_qa.md
templates/figure/chart_selection.md
templates/figure/figure_plan.md
templates/figure/figure_enhancement_patterns.md

templates/matlab/README.md
templates/matlab/q1_plot.m
templates/matlab/data_process.m
templates/matlab/hsk_apply_scientific_style.m

Python starter / workbook output templates（仅实际相关者）
相关 lint / sync_project / schema / structure / tooling / figure tests
README.md
CHANGELOG.md
版本载体（只有正式确认 minor 后才更新）
```

同一通用规则只允许一个 Authority 定义，其他位置引用或摘要，避免再次产生 semantic duplication。

---

# 19. 兼容性要求

1. v7.14.x 历史工作簿继续只读兼容；
2. 新增状态证据优先采用可选 capability-driven 结构，不要求旧项目补齐全部 Sheet；
3. v7.14 Primary Numerical Validity / PQS / Verification ID / accepted semantics 不变；
4. 正式 MATLAB caption-owned title 语义不回退；
5. 默认 grid off 不回退；
6. 当前项目目录结构原则上不改变；
7. 若确实需要 schema 新字段，必须提供默认/可选兼容语义与回归测试。

---

# 20. 实施阶段

## Phase A：Authority 与数据边界

- 更新 03A current-run Evidence Capture 语义；
- 更新 03B 细粒度 analysis evidence 输出要求；
- 必要时扩展 workbook capability schema；
- 回归 03A/03B 硬边界。

## Phase B：Scientific Figure Authority

- Module 04 增加 Scientific Figure Synthesis；
- Basic-form Challenge；
- Composite Encoding Preference；
- Scientific Rendering Profiles；
- Missing Scientific Evidence Check；
- Portfolio Gate；
- 恢复高对比主色规则。

## Phase C：MATLAB 模板与实现模式

- helper 恢复高对比 palette；
- q1/data_process 示例不再把 plain bar/line 当默认思路；
- 扩展 enhancement patterns / composite patterns；
- 保留 caption-owned title、grid off、visible figure、no auto-export。

## Phase D：Figure Contract / QA / downstream consumers

- Contract 增加证据结构和科研表达选择字段；
- QA 增加基础图挑战、组合图、Rendering Profile、Portfolio Review；
- 写作/评审 consumer 只引用 Figure Authority，不复制完整规则。

## Phase E：测试与版本收口

- 运行 lint / unit tests / generated metadata check；
- 运行 Figure/Workbook/Sync/Structure 影响测试；
- 若确认新增能力属于 minor，则更新版本到 v7.15.0；
- 更新 README / CHANGELOG；
- 自动刷新生成索引与 MANIFEST；
- 完整 GitHub CI；
- 本计划从根目录移入 `legacy/architecture/` 保存 provenance。

---

# 21. 验收标准

本轮成功不以“新增多少图型”衡量，而以以下结果衡量：

## Python

- 主求解不再只保留几个最终汇总数字；
- 对适用题型，状态、轨迹、约束、空间、逐样本等真实证据可直接用于后续绘图；
- 不提前执行 03B 内容。

## 03B

- 仍只在 accepted 后运行；
- 深化分析底层数据足以支撑稳定区、阈值、场景、分布、多算法等科研图。

## MATLAB

- 正文核心图不再默认退化为 plain bar/line/scatter；
- 组合图、Rendering Profile、局部放大和结构型可视化成为优先候选；
- 高对比亮蓝/鲜红等主色恢复；
- 视觉主次清楚，不因高饱和导致全图争抢注意力。

## 整篇论文

- 核心 Figure 能更多回答“为什么、在哪里、如何变化、边界在哪里、什么时候失效”，而不是只回答“数值是多少”；
- 图型丰富来自模型和证据结构，而不是机械追求多样性；
- 工作簿 → MATLAB → Figure → caption → 正文结论继续可追溯。

---

# 22. 必须执行的测试

基础治理测试：

```text
python scripts/lint_skill.py
python -m unittest discover -s tests
python scripts/generate_indexes.py --check
```

按影响面追加：

- workbook schema / result_io / artifact checker；
- 03A/03B boundary regressions；
- MATLAB static template tests；
- Figure semantic closure；
- sync_project figure scope；
- structure / content packs / tooling；
- version consistency；
- 完整 Python 3.10–3.14 CI；
- 现有 LaTeX CUMCM / MCM-ICM / Diangong / Production attestation 回归。

不得通过删除测试、降低现有有效断言或增加无原则例外来掩盖冲突。

---

# 23. 回滚方式

若新增 Evidence Capture 或 Figure Synthesis 引发不可接受回归：

1. 整体 revert 本轮 PR；
2. 不迁移、不破坏用户已有项目数据；
3. v7.14.1 历史工作簿与 Figure 语义可继续使用；
4. 不需要回滚 numerical verification 协议。

---

# 24. 后续执行纪律

后续修改严格遵循：

```text
每批修改前读取本计划
→ 读取当前 main 对应 Authority
→ 只做本批范围
→ 运行对应测试
→ 检查差异是否符合计划
→ 再进入下一批
```

如果实现过程中发现必须改变本计划中的 03A/03B 边界、工作簿兼容策略、Figure Authority 边界或版本等级，应先暂停修改，回到用户审查，不得自行扩张。

本计划当前只完成“范围冻结”；除本文件外，本次提交不应修改任何活动 Skill 文件。
