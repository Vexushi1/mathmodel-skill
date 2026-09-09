---
status: planning_only
baseline_skill_version: 9.0.0
candidate_target_skill_version: 9.1.0
change_level: minor
baseline_main_commit: 202b9e18505657ba7cf8a08a66c068855078cec8
runtime_authority: false
source_archive: figures_for_papers-main.zip
source_archive_sha256: 9e206cfa429514549c74eb19deb177642cc8cd558c273173de80f2b3d0a34295
---

# MATLAB Publication Figure Rendering v9.1 详细修改计划

> 本文件是本轮 Figure / MATLAB 绘图增强的 planning-only scope anchor，不是 Runtime Authority，不进入默认加载链，也不改变当前 9.0.0 的任何执行行为。正式实施前与每个实施阶段开始前，都必须重新读取当前 `main` 的 `core/bootstrap.yaml`、`SKILL_CHANGE_GOVERNANCE.md` 和本阶段涉及的 Figure Authority；不得根据聊天记忆直接扩张范围。

## 0. 计划目标

本轮的核心目标不是重新设计数学建模工作流，也不是把外部 Python 绘图仓库原样移植为 MATLAB，而是在**保持现有 HSK Figure Evidence 体系基本不变**的前提下，把外部 `figures4papers` 压缩包中已经被大量成品图验证过的 publication rendering 经验吸收进当前 MATLAB 绘图层，使 `qX_plot.m` / `data_process.m` 在完成数据绑定后，默认更容易直接产出成熟、统一、少人工返工的正式论文图。

希望最终形成的效果是：

```text
现有 Figure Evidence 决策链（保持）
Core conclusion
→ Evidence structure
→ Scientific Figure Synthesis
→ Basic-form Challenge
→ Composite Encoding
→ Scientific Rendering Profile
→ Figure Layout Gate
→ Figure Enhancement Gate

新增/强化的实现层（不新增项目状态，不建立第二套 Authority）
→ Publication Rendering Grammar
   ├─ palette profile
   ├─ typography / axes grammar
   ├─ adaptive canvas
   ├─ legend strategy
   ├─ panel spacing / alignment
   ├─ annotation budget
   ├─ print-safe encoding
   └─ chart-family rendering pattern
→ MATLAB rendering
→ existing Figure QA / Portfolio Gate
```

换言之：**决策逻辑仍由现有 Module 04 决定；本轮主要提升“选定图以后，MATLAB 怎样稳定画得像成熟论文图”。**

---

# 1. 当前仓库基线与不可破坏边界

当前基线：

- Skill：`9.0.0`
- `main`：`202b9e18505657ba7cf8a08a66c068855078cec8`
- Figure Evidence 唯一 Authority：`modules/04_figure_evidence.md`
- Figure pattern 实现参考：`templates/figure/figure_enhancement_patterns.md`
- 图型索引：`templates/figure/chart_selection.md`
- MATLAB 当前活动说明：`templates/matlab/README.md`
- MATLAB 样式 helper：`templates/matlab/hsk_apply_scientific_style.m`
- 每问正式绘图入口：`问题X求解/qX_plot.m`
- 项目级预处理绘图入口：`数据预处理/data_process.m`

本轮必须保持以下硬边界：

1. **不改变 Python / MATLAB 职责边界。** MATLAB 仍只读取 accepted workbook / 当前合法数据事实源，不重新求解、重新清洗、重新做敏感性、重新估计模型或重建参数。
2. **不改变 03A / 03B 边界。** 主求解 current-run evidence 与结果深化 alternative-world evidence 的职责不因绘图增强而变化。
3. **不改变每问五文件结构。** 仍是两个 Python、两个标准工作簿、一个 `qX_plot.m`。
4. **不改变 Figure Evidence Authority 层级。** Module 04 继续拥有通用 Figure 决策权；template/helper 只能实现，不得反向决定图型。
5. **不改变 Model Approval、Semantic Governance、Runtime Assurance、State Transition、Project Transaction。**
6. **不改变 Workbook Schema / Project State Schema，除非实施过程中出现不可避免的真实接口需求；本计划默认不需要。**
7. **不恢复 MATLAB 自动求解或自动分析。**
8. **不恢复正式图内整体 `title` / `sgtitle`。** 正式图名继续由 DOCX/LaTeX caption 承担。
9. **不恢复默认批量自动导出。** 默认仍保留可见图窗供人工检查；仅在用户明确要求正式导出时使用 publication export 规则。
10. **不以“必须使用 N 种图型”制造机械多样性。** 科学证据结构优先于视觉炫技。

---

# 2. 外部压缩包审计范围

本计划基于用户提供的 `figures_for_papers-main.zip`，SHA-256：

`9e206cfa429514549c74eb19deb177642cc8cd558c273173de80f2b3d0a34295`

审计对象包括：

- 压缩包总计约 95 个文件；
- 25 个 `figure_*/*.py` 绘图脚本；
- 29 个 PNG 成品图；
- 3 个 PDF 成品图；
- `scientific-figure-making/SKILL.md`；
- `references/design-theory.md`；
- `references/common-patterns.md`；
- `references/api.md`；
- `references/tutorials.md`；
- 多类 comparison / ablation / heatmap / trend / radar / manifold / conceptual illustration 成品。

从 25 个脚本中可重复观察到的风格规律包括：

- 23/25 脚本显式执行 `tight_layout`；
- 18/25 脚本使用 frameless legend；
- 15/25 脚本显式控制 y 轴范围；
- 11/25 脚本存在 axis-off 面板，其中相当一部分用于 legend-only 或概念布局；
- 5 个脚本使用 hatch / pattern encoding；
- 大量 comparison 图采用极宽画布，成品宽高比常在 3:1--6:1，极端多类别图可达到约 8:1；
- dense comparison bars 使用 600 DPI，常规图多为 300 DPI；
- house style 高频使用 Helvetica / sans-serif、top/right spine 隐藏、2--3 pt 轴线/主线、无边框 legend；
- 多指标 comparison 经常采用“一个指标一个 panel + 最后一个 panel 只放 legend”的布局；
- ablation 常使用同一主色的深浅/alpha 层级表示有序完整度；
- composition 类图用 color + hatch 双编码提高黑白打印可辨识度；
- heatmap 会把 cell 数值、行列统计和方法/指标结构同时组织到一个视觉矩阵中；
- trend 图常把主轨迹、阶段/事件、面积或区间、关键 milestone 结合，而不是只画普通折线。

这些规律构成本轮“可迁移视觉工程经验”的主要来源。

---

# 3. 外部绘图体系中值得吸收的核心原则

## 3.1 Minimalist publication frame

外部仓库的成熟感很大程度不是来自复杂装饰，而来自稳定的基础 frame：

- 白底；
- top / right spine 默认隐藏；
- 左/下轴线清楚但不过粗；
- 默认无网格；
- legend 无边框；
- 字体、tick、line width 在整个 figure 内一致；
- 颜色数量有限且角色稳定；
- panel 间距紧凑；
- 不让 legend 挤占数据区。

**采纳方式：** 数据驱动正式 Figure 默认采用 open-axis publication frame；机理图继续服从 Module 04 monochrome-first 规则，不强制使用同一数据图样式。

## 3.2 Semantic palette instead of arbitrary palette

外部仓库不是每张图随机换颜色，而是重复使用一套具有角色感的 palette：

| 角色 | 源仓库代表色 |
|---|---|
| 主方法 / anchor | `#0F4D92` |
| 次主蓝 | `#3775BA` |
| 正向层级浅→深 | `#DDF3DE`, `#AADCA9`, `#8BCF8B` |
| 对照层级浅→深 | `#F6CFCB`, `#E9A6A1`, `#B64342` |
| 中性 | `#CFCECE` |
| 单点强调 | `#FFD700` |
| 补充 accent | `#42949E`, `#9A4D8E` |

**采纳方式：** 不替换当前 v9 高对比主色，而是引入第二套 `journal_balanced` rendering palette；由证据结构和对象数量选择 palette profile。

## 3.3 Ultra-wide multi-metric composition

对于 3--4 个不同量纲指标，外部仓库常用：

```text
Metric A | Metric B | Metric C | Legend-only
```

每个 panel 只承担一个 metric，同一方法跨 panel 保持相同颜色，避免把不同量纲硬塞同一坐标轴。

**采纳方式：** 新增 `Multi-Metric Comparison Strip` 实现模式；它只是 Layout / Rendering pattern，不创建新的 Figure level。

## 3.4 Dedicated legend panel

复杂图的 legend 被从数据区剥离，单独占一个 axes/tile。

**采纳方式：** 新增 Legend Strategy：`direct_label / in_axis / shared_outer / dedicated_tile`，但不把它写入项目状态或模型语义合同。

## 3.5 Ordered ablation visual hierarchy

有真实嵌套关系的 ablation 不使用多种互不相关颜色，而使用同 hue 的明暗/alpha 表示“从不完整到完整”。

**采纳方式：** 新增 `Ordered Ablation Ladder` pattern，并建立强准入条件：只有 `M0 ⊂ M1 ⊂ ... ⊂ Mk` 或等价的有序组件累加语义才允许使用单 hue progression。

## 3.6 Print-safe composition

stacked composition 用 fill color 表示一级类别，用 hatch / edge pattern 表示第二语义，使黑白打印后仍能区分。

**采纳方式：** 新增 `Composition / Decomposition` rendering pattern；MATLAB 实现优先无外部依赖。若内部 hatch helper 无法做到稳定、可维护，则 v9.1 首版使用“颜色 + 深浅 + 清晰边界/直接标签”的 print-safe fallback，hatch 作为可选增强而不是硬依赖。

## 3.7 Milestone-aware trend

trend 不只画线，而把真实 event / milestone / phase boundary 与主轨迹结合。

**采纳方式：** 强化现有 Dynamic profile，增加 `Milestone-Aware Trend` pattern。

## 3.8 Matrix as evidence summary

源仓库的成熟 heatmap 不只是颜色矩阵，还会同时呈现 cell 数值、方法/指标结构、样本量或 improvement-over-best。

**采纳方式：** 新增 `Evidence Matrix` family，并对 normalization / colorbar 诚实性设硬规则。

---

# 4. 明确不直接照搬的外部规则

## 4.1 不默认照搬“紧 y 轴”到柱状图

外部仓库经常为了强调小差异对 bar chart 采用紧 y-limits。数学建模正式论文中，如果柱长承担绝对量比较，这可能放大视觉差异。

本 Skill 的实现原则应更严格：

- line / dot / interval / scatter 可按数据范围合理缩放；
- bar 若长度本身是主要视觉编码，默认优先零基线；
- 若指标天然只在窄范围内变化且零基线严重压缩信息，优先考虑 interval dot / sorted dot，而不是直接截断 bar；
- 确需截断时必须显式、可解释，并避免让读者误认为比例差异更大；
- Local Zoom 仍服从现有 Data Honesty 规则。

## 4.2 不默认给每根柱标数字

源仓库部分 comparison 图会把所有柱值直接标在柱顶。当前 Skill 的 Annotation Budget 更适合数模论文：关键标注通常 3--5 个，不把 Figure 变成数据表。

因此：

- 少量类别、精确值本身就是核心结论时可直接标值；
- 大量类别只标推荐点、极值、阈值、基准差异；
- 其余精确数字交给表格/caption/正文。

## 4.3 不把 3D sphere / conceptual shading 变成通用风格

源仓库部分概念图采用 3D-like sphere shading。当前 Module 04 的 Conditional 3D 更科学，本轮保持：第三维无真实数学/物理意义时不使用 3D。

## 4.4 不默认启用 TeX 字体链

源仓库部分脚本启用 `text.usetex=True`。当前 Skill 需要中文标签和竞赛环境可移植性，因此：

- 中文正文标签继续使用 CJK fallback；
- 公式或短数学符号可按 MATLAB Interpreter 使用 TeX/LaTeX；
- 不要求系统必须安装额外 LaTeX 字体才能看图。

---

# 5. 目标版本与变更等级

正式实施建议：

- 当前：`9.0.0`
- 候选目标：`9.1.0`
- 等级：`minor`

原因：本轮新增向后兼容的 Figure rendering capability、palette profile、layout pattern 和 MATLAB helper 行为，但不破坏现有项目目录、工作簿、CLI、Project State、模型审批和用户执行接口。

本 plan PR 本身仍属于 docs-only，不提前修改版本 carrier；只有实施内容与测试完成后才进行 9.1.0 release carrier 更新。

---

# 6. 目标架构：不新增第二套 Figure Authority

实施后仍保持：

```text
modules/04_figure_evidence.md
    = 唯一通用 Figure 决策 Authority

    ↓ references / implementation only

templates/figure/chart_selection.md
    = Evidence Structure → visual candidate 索引

templates/figure/figure_enhancement_patterns.md
    = MATLAB / scientific visual implementation patterns

templates/matlab/README.md
    = MATLAB 使用说明与职责边界

templates/matlab/hsk_apply_scientific_style.m
    = rendering style kernel

qX_plot.m / data_process.m
    = 项目实例入口，不拥有图型决策权
```

不新建独立 `figure_style_contract.yaml`、不新建 Project State 字段、不让 resolver 多加载一个重型合同。

---

# 7. 新增 Publication Rendering Grammar 的定位

`Publication Rendering Grammar` 不是一个新的 workflow gate，不增加项目状态，也不触发 stale / semantic revision。它是 Selected visual structure 已确定后的统一 rendering 规则层。

它负责回答：

1. 当前图应该用哪套 palette profile；
2. 字号 / 线宽 / marker / errorbar 的层级如何统一；
3. axes 是否 open-frame；
4. figure canvas 如何按 panel 数与标签密度自适应；
5. legend 应放数据区、外侧还是专用 tile；
6. panel 间距如何保持一致；
7. 何时隐藏冗余 x-ticks；
8. 何时使用 direct label；
9. 何时使用 print-safe secondary encoding；
10. annotation 只突出哪些不可替代对象；
11. 明确 export 时怎样 vector-first / 300--600 DPI。

这些都是视觉实现参数，不应进入 Semantic Identity，也不触发 Model Approval。

---

# 8. Palette Profiles 设计

## 8.1 `competition_high_contrast`（保留当前默认语义）

继续保留当前 v9 主色：

- brightBlue `#1478FF`
- vividRed `#F04444`
- brightGreen `#16B364`
- brightOrange `#F79009`
- brightPurple `#7A5AF8`
- darkGray `#252B37`
- lightGray `#E9EAEB`

适用：

- 2--4 个核心对象强比较；
- 推荐方案 / 关键曲线需要第一眼识别；
- 竞赛论文快速阅读优先；
- 重点对象少、视觉层级清晰。

## 8.2 `journal_balanced`（新增，吸收源仓库成熟 palette）

建议新增：

- navy `#0F4D92`
- blue `#3775BA`
- greenLight `#DDF3DE`
- greenMid `#AADCA9`
- greenStrong `#8BCF8B`
- redLight `#F6CFCB`
- redMid `#E9A6A1`
- redStrong `#B64342`
- neutral `#CFCECE`
- teal `#42949E`
- violet `#9A4D8E`
- highlight `#FFD700`

适用：

- 4--8 个方法/类别；
- ultra-wide multi-panel；
- 多 metric comparison；
- 方法较多且高饱和五色会造成竞争；
- 需要更接近期刊/顶会的 muted-but-distinct 视觉。

## 8.3 `monochrome_print`

沿用当前正式机理图 monochrome-first 思路，并为数据图提供可选打印模式：

- black / dark gray / medium gray / light gray；
- linestyle / marker / edge / hatch 作为辅助编码；
- 不依赖红绿色差。

## 8.4 Palette 自动选择原则

建议 Authority 只写高层规则：

```text
2--3 个核心对象且需强比较
→ competition_high_contrast

4--8 个并列对象 / 多 panel / 长 legend
→ journal_balanced

有序 ablation
→ 单 hue progression，不使用无序多色

黑白打印或颜色不应承担唯一语义
→ monochrome / pattern-safe secondary encoding
```

不把 palette selection 变成硬编码题型映射；Figure Contract 仍记录证据职责，不记录十六进制实现参数。

---

# 9. Typography / Axes 规范

## 9.1 字体层级

建议将当前单一 18pt 默认扩展成 profile-aware 层级：

- compact analytic figure：base 15--16
- normal competition figure：base 17--18
- ultra-wide metric strip：base 18--20
- 大型 bar / short-label comparison：metric label 可 22--26
- legend：通常比 axes base 小 1--2 级
- panel label：与 axes label 同级或略大，不建立巨大标题层级

中文 fallback 保留：

`Microsoft YaHei → SimHei → Noto Sans CJK SC → Arial Unicode MS → Helvetica → Arial`

英文/数字优先保持 sans-serif publication look。

## 9.2 Axes frame

数据驱动正式 Figure 建议默认：

- `Box = off`；
- top/right spine 不显示；
- left/bottom 轴线清楚；
- `Layer = top`；
- 默认 `grid off`；
- tick 长度、方向、线宽统一；
- background 为 white。

例外：

- heatmap / matrix 可使用 frame-off；
- exact geometry / mechanism 服从各自 profile；
- 需要完整边界表示的坐标域不机械隐藏边界。

## 9.3 Line / marker / errorbar hierarchy

建议统一范围而非固定一个值：

- 主线：约 2.0--2.8
- 次线：约 1.4--2.0
- reference / threshold：约 1.0--1.5 + dashed
- marker：按 canvas 自适应，核心点略大、context 点更小/更透明
- errorbar：深灰或对象色，cap 清楚但不抢主视觉
- CI / PI band：透明度显著低于主线

目标是让“主对象 > 次对象 > context > reference”形成稳定视觉层级。

---

# 10. Adaptive Canvas 与 panel spacing

外部仓库大量使用 28×6、36×6、45×12、52×12 甚至更宽的 canvas。不能原样把 inch 数搬到 MATLAB，但应吸收其原则：**canvas 由 panel 数、label 长度、legend 复杂度决定，不固定为 960×620。**

建议新增 Adaptive Canvas 规则：

| 结构 | 建议逻辑 |
|---|---|
| 单 panel | 标准论文比例，约 1.3--1.7:1 |
| 1×2 | width ≈ 单 panel 的 1.8--2.1 倍 |
| 1×3 | width ≈ 单 panel的 2.5--3.0 倍 |
| 3 metric + legend tile | ultra-wide，约 3.5--4.8:1 |
| 大量 horizontal labels | 增加高度与 left margin，而不是缩小字体 |
| 规则 matrix | 按 rows × cols 增长，不让单 cell 被压扁 |
| radar / square diagnostic | 接近 1:1--1.4:1 |

MATLAB 优先使用：

- `tiledlayout(..., "TileSpacing", "compact", "Padding", "compact")`；
- 只有非规则 composite geometry 才使用手动 axes `Position`；
- 不使用固定 2×2 作为默认模板。

---

# 11. Legend Strategy

新增统一 Legend Strategy，实现源仓库最显著的成熟排版特征之一。

## 11.1 `direct_label`

适用：

- 2--3 条主曲线；
- 曲线末端分离清楚；
- direct label 能降低 legend 搜索成本。

## 11.2 `in_axis`

适用：

- legend 项少；
- 有明确空白区域；
- 不遮挡数据、CI、阈值和 annotation。

## 11.3 `shared_outer`

适用：

- 多 panel 共用同一方法颜色；
- legend 中等长度；
- 可放于 figure 外侧上下区域且不显著压缩数据区。

## 11.4 `dedicated_tile`

适用：

- 多 metric panel；
- 5 个以上 legend item；
- color + linestyle / marker / hatch 双编码；
- legend 会遮挡数据；
- 多 panel 需要一处统一语义说明。

实现时：

- 最后一个 tile `axis off`；
- 从数据 axes 收集 handles / labels；
- legend 只出现一次；
- 专用 legend tile 不承担新的数据结论。

---

# 12. X tick / category label 策略

源仓库在 multi-metric method comparison 中经常隐藏 x tick labels，依赖共享 legend。这种方式只有在映射不会丢失时才准入。

准入：

- 各 metric panel 的 category 顺序完全相同；
- 颜色映射稳定；
- legend 清楚；
- category 名称较长、重复写在每 panel 会显著拥挤。

禁止：

- 不同 panel category 顺序不同；
- category identity 只能靠位置猜；
- 色弱/黑白模式下没有辅助编码；
- legend 被裁剪或不在同一 Figure 中。

---

# 13. Annotation 规范

保留当前 Annotation Budget，同时吸收源仓库“精确数字直接服务阅读”的优点。

统一决策：

```text
少量对象 + 数值本身是结论
→ direct value annotation 可用

大量对象 / 数值很多
→ 只标推荐点、极值、阈值、交点、关键提升

matrix
→ cell annotation 可用，但字体颜色根据背景亮度自适应

trend
→ milestone / event annotation 优先于每个点的数值
```

禁止：

- 给所有 dense scatter 点贴标签；
- annotation 与数据线重叠；
- 为了展示精确值牺牲图形结构；
- 同一图同时出现大量 legend、数据标签、说明框竞争注意力。

---

# 14. 新增/强化的 Chart-family Rendering Patterns

## 14.1 C9 — Multi-Metric Comparison Strip

**目标：** 解决多模型 × 多指标 × 不同量纲 comparison。

结构：

```text
Metric 1 | Metric 2 | Metric 3 | Legend
```

规则：

- 每个 metric 独立 y 轴；
- 同一方法跨 panel 颜色完全一致；
- category 顺序保持一致；
- x tick 可在满足第 12 节条件时隐藏；
- errorbar / CI 保留；
- dedicated legend tile 优先；
- panel label 只在论文排版需要时使用；
- 不使用整体 `sgtitle`。

典型用途：多模型性能、方案多指标、不同量纲评价、算法基准。

## 14.2 C10 — Ordered Ablation Ladder

**目标：** 表达组件逐步加入/删除的有序模型完整度。

规则：

- 必须存在真实顺序/嵌套关系；
- 单 hue 用 lightness/alpha 递进；
- 完整模型视觉权重最高；
- horizontal bar 优先用于长组件名称；
- 多 metric 时可 1×N 并排，并只在第一个 panel 保留完整 y labels；
- 没有真实顺序时不得使用该语法。

## 14.3 C11 — Composition / Decomposition + Print-safe Encoding

适用：比例构成、成本构成、资源分配、概率组成、风险来源。

优先结构：

- 100% stacked bar；
- stacked bar；
- composition heatmap；
- small-multiple composition。

规则：

- stack 必须有真实可加和整体；
- 总和/分母口径明确；
- color 表示一级 category；
- 第二语义优先 hatch / edge / lightness；
- 不允许 color + hatch + marker + alpha 四重叠加；
- MATLAB 不依赖 File Exchange；若 hatch helper 不稳定，使用内部可维护 fallback。

## 14.4 C12 — Evidence Matrix / Marginal-Annotated Heatmap

适用：方法×指标、区域×状态、场景×风险、类别×阶段。

核心元素：

- matrix color field；
- cell numeric annotation；
- row/column label；
- 可选 row/column sample size / totals；
- 可选 benchmark / improvement row；
- annotation text color 根据 cell luminance 自动黑/白切换。

Data Honesty：

- 如果每列独立 normalization，禁止共享一个暗示“颜色可跨列比较”的统一 colorbar；
- 更推荐把颜色编码成统一 dimensionless quantity（如 standardized score / relative improvement），原始值用文本显示；
- 正负差值用 diverging colormap 且中心固定在真实基准 0。

## 14.5 C13 — Milestone-Aware Trend

扩展现有 Dynamic profile：

```text
trajectory
+ uncertainty / interval（若真实存在）
+ event / threshold
+ phase background（若真实存在）
+ milestone annotation
+ Local Zoom（必要时）
```

规则：

- event 来自真实时间/状态；
- milestone 不超过少量关键位置；
- 背景阶段必须有真实业务/数学定义；
- 不使用 spline 美化离散实验点。

## 14.6 C14 — Normalized Multi-Criteria Radar（条件准入）

仅作为受控高级候选，不作为默认多指标图。

准入条件：

- 5--8 个指标为宜；
- 指标方向已统一；
- normalization 公式明确；
- 半径使用 normalized value，而不是不同量纲原始值；
- 2--4 个 series 为宜；
- 原始数值必须在表格/正文/caption 可核对；
- 不以多边形面积作为定量结论。

不满足时优先：heatmap、parallel coordinates、standardized dot。

## 14.7 C15 — Density / Manifold / State-Space Evidence

适用：仿真样本云、候选解空间、降维、状态空间、粒子分布、搜索轨迹。

结构：

```text
context samples (low alpha)
+ density / contour
+ trajectory / ridge / cluster focus
+ critical states
```

规则：

- dense samples 不用巨大 marker；
- density 只能来自真实样本；
- 关键 trajectory 用高对比；
- context 保留，不为突出目标删除不利样本。

## 14.8 C16 — Publication Comparison Heatmap

针对多方法 benchmark 的专用 matrix：

- 原始值；
- best baseline；
- improvement over best；
- 正/负 improvement 的明确语义；
- 方法行排序有依据；
- 推荐方法可用字体加粗/边界强调，但不隐藏 baseline。

---

# 15. Scientific Rendering Profile 扩展建议

当前 Profile：

- Distribution
- Regression / Prediction
- Dynamic
- Parameter Surface
- Spatial
- Optimization / Pareto
- High-density Scatter

建议在不重构现有枚举的情况下增加：

- `Multi-Metric Comparison`
- `Composition / Decomposition`
- `Evidence Matrix`
- `Ordered Ablation`
- `Multi-Criteria`（radar / standardized dot / parallel coordinates 共享）

这些只是图型专属 rendering 语法，不改变 Evidence Structure taxonomy。

---

# 16. `hsk_apply_scientific_style.m` 改造设计

当前 helper 已有统一字体、白底、legend、colorbar 和高对比 palette，但仍存在三个问题：

1. 只返回一套高对比 palette；
2. 默认 `Box=on`，与源仓库成熟 open-axis house style 不一致；
3. `q1_plot.m` / `data_process.m` 又各自复制本地 `apply_scientific_style`，导致样式 Authority 在模板层重复。

建议正式实施：

### 16.1 向后兼容扩展函数签名

概念接口：

```matlab
palette = hsk_apply_scientific_style(fig, profile)
```

其中 `profile` 可选，默认保持当前兼容行为，例如：

- `"competition_high_contrast"`
- `"journal_balanced"`
- `"monochrome_print"`

旧调用 `hsk_apply_scientific_style(fig)` 必须继续工作。

### 16.2 返回 semantic role aliases

除保留旧字段外，新增稳定语义角色：

```text
palette.primary
palette.secondary
palette.positive
palette.negative
palette.context
palette.neutral
palette.highlight
palette.dark
palette.light
```

旧字段 `brightBlue / vividRed / ...` 保留兼容，避免历史模板断裂。

### 16.3 统一 axes style

helper 负责：

- font fallback；
- font size baseline；
- open axes / box policy；
- line width baseline；
- legend frameless；
- colorbar typography；
- grid default；
- white background。

helper **不负责**：

- 决定画什么图；
- 自动改 y-limits；
- 自动删除 x ticks；
- 自动决定 legend tile；
- 自动选择数据字段；
- 自动导出。

这些仍由 Figure Contract / pattern 实例决定。

---

# 17. MATLAB 入口模板去重

## 17.1 `templates/matlab/q1_plot.m`

实施目标：

- 删除本地复制的 `apply_scientific_style` / `select_font`；
- 改为调用共享 `hsk_apply_scientific_style.m`；
- 示例图仍只是 plumbing smoke，不成为默认 line chart；
- comments 增加 publication rendering grammar 提示；
- 示例使用 semantic palette role，而不是硬编码 RGB；
- 保持真实表头唯一匹配、title/sgtitle 禁止、图窗可见、默认不导出。

## 17.2 `templates/matlab/data_process.m`

同样去除本地 style duplicate，统一共享 helper。

注意：这只是样式实现去重，不改变数据处理边界。

---

# 18. Figure Authority / reference 文件修改范围

## 18.1 `modules/04_figure_evidence.md`

只增加高层 Authority 规则：

- Publication Rendering Grammar 的定位；
- palette profile 选择原则；
- legend strategy 原则；
- adaptive canvas 原则；
- open-axis publication frame；
- multi-metric / composition / evidence matrix / ordered ablation 的准入原则；
- dynamic y-range 的 data honesty 修正；
- vector-first export（仅在明确导出时）。

不得把具体 MATLAB API、figure Position、RGB 细节大量复制进 Authority。

## 18.2 `templates/figure/figure_enhancement_patterns.md`

作为主要实现模式库新增 C9--C16 章节，保存 MATLAB 级 pattern 和边界。

## 18.3 `templates/figure/chart_selection.md`

只扩展 Evidence Structure → candidate visual structure 映射，不复制完整风格规则。

## 18.4 `templates/figure/result_figure_qa.md`

新增少量 publication QA：

- palette profile 是否与对象数量/图型匹配；
- 是否存在 legend 遮挡；
- multi-panel 是否统一对象颜色与字号；
- dedicated legend tile 是否真正降低搜索成本；
- bar baseline / y-range 是否诚实；
- heatmap normalization / colorbar 是否可比较；
- open-axis / white background / frameless legend 是否符合数据图 profile；
- print-safe secondary encoding 是否在需要时存在；
- panel spacing 是否紧凑但不裁剪标签。

不把 QA 变成像素级固定样式断言。

## 18.5 `templates/matlab/README.md`

增加 palette/layout/legend/pattern 快速说明，继续强调 helper 不是 Authority。

---

# 19. Figure Contract 是否新增字段

默认**不新增必填字段**。

原因：

- palette、legend、canvas 属于 rendering implementation；
- 不应让 `模型论文框架.md` 被 RGB、透明度、subplot Position 等样式参数污染；
- 当前 Figure Contract 已经有 Selected visual structure / Rendering Profile / Layout / Enhancement，可承载高层设计决策。

只有实施过程中发现必须记录一个稳定、可审查的高层 rendering choice 时，才考虑增加一个可选字段：

`Publication rendering profile: auto / competition_high_contrast / journal_balanced / monochrome_print`

该字段即使新增，也必须是可选、非 semantic，不影响 Model Approval / stale。

---

# 20. Export 规则增强（不改变默认“不自动导出”）

当用户明确要求正式导出时：

优先：

- PDF / SVG / EPS 等 vector-first；
- PNG 作为预览/提交要求时使用；
- 普通数据图 300 DPI；
- 极密集 bar / matrix 或明确 raster 需求可 600 DPI；
- 白底、字体可读；
- 避免裁剪 legend / annotation；
- 不自动生成大量无用格式。

MATLAB 实现优先 `exportgraphics` / vector content，不在默认 `qX_plot.m` smoke 中自动执行。

---

# 21. 实施阶段划分

## Phase A — Baseline / visual inventory

目标：冻结当前 9.0 Figure 行为与源压缩包审计结论。

工作：

- 记录当前 helper / q1_plot / data_process / Module 04 基线；
- 增加针对 style helper 的静态/文本测试基线；
- 明确不改 Schema / State / Python contracts。

完成标准：不改变 runtime。

## Phase B — Authority-level publication grammar

修改：

- `modules/04_figure_evidence.md`
- `templates/figure/chart_selection.md`
- `templates/figure/figure_enhancement_patterns.md`

目标：先把“何时可用”写正确，再写 MATLAB helper。

完成标准：无第二 Authority、无规则重复冲突。

## Phase C — MATLAB style kernel

修改：

- `templates/matlab/hsk_apply_scientific_style.m`
- `templates/matlab/README.md`

目标：

- palette profiles；
- semantic aliases；
- open-axis publication frame；
- typography hierarchy；
- backward compatibility。

## Phase D — Entry-template consolidation

修改：

- `templates/matlab/q1_plot.m`
- `templates/matlab/data_process.m`

目标：删除本地 style duplicate，统一共享 helper。

## Phase E — Pattern implementation references

把 C9--C16 的 MATLAB 实现 skeleton / pseudo-code 写入 `figure_enhancement_patterns.md`，必要时才新增极少量 helper。

原则：优先文档 pattern，不为每一种图新建一个 `.m` 模板。

## Phase F — QA / static tests

修改候选：

- `templates/figure/result_figure_qa.md`
- `tests/...` 与 `scripts/lint_skill_checks.py`（仅实际需要）

检查：

- helper profile 名称存在；
- 旧调用仍兼容；
- q1/data_process 不再复制 style helper；
- title/sgtitle prohibition 未回退；
- MATLAB 仍不导出/关闭默认图窗；
- Figure Authority 单一性。

## Phase G — Version / release carriers

只有 Phase A--F 全部通过后：

- 更新 Skill carrier 到 9.1.0；
- 更新 Changelog；
- 运行版本一致性检查；
- 生成 indexes / MANIFEST；
- 完整 CI。

---

# 22. 文件级预计修改矩阵

| 文件 | 预计动作 | 是否 Authority | 目的 |
|---|---|---:|---|
| `modules/04_figure_evidence.md` | 修改 | 是 | 增加 publication rendering 高层规则 |
| `templates/figure/figure_enhancement_patterns.md` | 修改 | 否 | 增加 C9--C16 实现模式 |
| `templates/figure/chart_selection.md` | 修改 | 否 | 增加新候选视觉结构索引 |
| `templates/figure/result_figure_qa.md` | 修改 | 否 | 增加出版级视觉 QA |
| `templates/matlab/README.md` | 修改 | 否 | MATLAB quick reference |
| `templates/matlab/hsk_apply_scientific_style.m` | 修改 | 否 | palette profile + style kernel |
| `templates/matlab/q1_plot.m` | 修改 | 否 | 删除重复 style，使用 shared helper |
| `templates/matlab/data_process.m` | 修改 | 否 | 删除重复 style，使用 shared helper |
| `tests/...` | 按需修改/新增 | 否 | backward/static regression |
| `scripts/lint_skill_checks.py` | 仅必要时 | 否 | contract/template 静态检查 |
| `CHANGELOG.md` | release 阶段修改 | 否 | 9.1.0 变更说明 |
| 版本 carriers | release 阶段修改 | 是/入口 | 9.1.0 一致性 |
| 生成索引 / MANIFEST | 生成器自动 | 否 | repository metadata |

默认禁止为了本次视觉增强去修改：

- `core/model_approval_contract.yaml`
- `core/runtime_assurance_contract.yaml`
- `core/state_transition_contract.yaml`
- `core/project_state.schema.yaml`
- `core/workbook_schema.yaml`
- `core/numerical_verification_contract.yaml`
- `core/user_execution_contract.yaml`
- `scripts/project_transaction.py`
- `scripts/state_transitions.py`
- Python solve / analysis contract

若实施中发现必须触碰这些文件，应停止当前 PR，重新评估 scope，而不是顺手扩大。

---

# 23. 测试计划

最低完整回归：

```bash
python scripts/lint_skill.py
python -m unittest discover -s tests
python scripts/generate_indexes.py --check
```

Figure/MATLAB 重点检查：

1. `q1_plot.m` 仍含精确表头唯一匹配；
2. `data_process.m` 仍只读取 `数据预处理结果.xlsx`；
3. `q1_plot.m` / `data_process.m` 不调用求解、优化、训练、敏感性逻辑；
4. 正式图 title / sgtitle prohibition 不回退；
5. helper 默认调用保持兼容；
6. helper palette 旧字段仍存在；
7. 新 palette profile 名称可静态解析；
8. shared helper 后不再在两个入口模板复制 `select_font` / `apply_scientific_style`；
9. generated metadata current；
10. `sync_project --delivery-scope figures` 既有检查保持通过。

若 CI 环境没有 MATLAB，不应伪装成已经做了真实 MATLAB rendering。需要额外安排**人工 MATLAB visual smoke**：

- 运行至少一个单 panel；
- 一个 multi-metric strip + dedicated legend；
- 一个 evidence matrix；
- 一个 milestone-aware trend；
- 一个 ordered ablation；
- 检查中文字体 fallback、legend 裁剪、axes spacing、颜色与 annotation。

人工 visual smoke 只验证 rendering，不替代 workbook / evidence 正确性。

---

# 24. Visual Acceptance Checklist

正式 9.1.0 Figure rendering 的验收目标：

## 一致性

- 同一方法跨 panel 颜色一致；
- 同一语义跨整篇论文颜色一致；
- font / line width / tick / legend hierarchy 一致；
- panel label 位置一致；
- multi-panel 不重复学习新视觉语法。

## 成熟度

- legend 不遮挡核心数据；
- 复杂 legend 有 shared / dedicated 方案；
- 长 category label 不被强行缩小到难读；
- 多 metric 不硬塞同一 y 轴；
- panel spacing 紧凑但不裁剪；
- background / CI / context 不与主对象竞争；
- 成品无需为了“把 legend 移一下、统一字体、换颜色、拉宽画布”再做大量人工修图。

## 科学诚实

- bar baseline 不误导；
- heatmap color normalization 可解释；
- radar normalization 明确；
- event / milestone / semantic background 都来自真实证据；
- 离散点不为美观擅自 spline；
- context 不被选择性隐藏。

## 打印安全

- 红绿不作为唯一语义；
- 必要时加入 marker / linestyle / edge / pattern；
- 黑白打印仍能区分关键组。

---

# 25. 兼容与迁移

本轮设计目标是向后兼容：

- 旧项目目录不变；
- 旧 workbook 不变；
- 旧 `qX_plot.m` 不要求自动迁移；
- 旧调用 `hsk_apply_scientific_style(fig)` 继续工作；
- 新 profile 只影响新生成/新实例化脚本；
- 旧 Figure 不因版本升级自动 stale；
- 纯视觉改动不增加 semantic_revision，不触发 Model Approval；
- Figure hash / Framework 登记按现有规则更新。

不建立 legacy style compatibility layer；只保留 helper 字段别名即可。

---

# 26. 主要风险与控制

## 风险 1：风格规则膨胀成第二套 Figure Authority

控制：所有“是否应该用”仍放 Module 04；template 只写“怎样实现”。

## 风险 2：为了像源仓库而牺牲数据诚实

控制：y-axis、radar、heatmap normalization、hatch、3D 都增加明确准入条件；现有 Data Honesty 优先级高于美观。

## 风险 3：helper 自动化过度，反而限制题目特异性

控制：helper 只统一基础 frame/palette/typography，不自动决定图型、数据、ylim、legend strategy。

## 风险 4：MATLAB 版本兼容

控制：优先使用稳定基础 API；任何较新的 graphics feature 必须有 fallback 或不作为硬依赖。

## 风险 5：大量新增 `.m` helper 导致维护复杂

控制：原则上只扩展现有 `hsk_apply_scientific_style.m`；只有 dedicated legend / hatch 等存在明显重复且内部实现稳定时才新增极少 helper。

## 风险 6：CI 无 MATLAB，视觉质量无法自动证明

控制：静态 contract test + 人工 MATLAB visual smoke 双轨；不得把静态通过宣称为“视觉已验证”。

---

# 27. 回滚方式

若 9.1.0 实施后发现新 style 降低可读性：

1. helper 默认 profile 可回退到 `competition_high_contrast`；
2. 新 `journal_balanced` / pattern 只是可选能力，可禁用而不影响数据与项目状态；
3. entry template 去重可 revert 到前一版本 helper 调用；
4. 不涉及 workbook / state migration，因此回滚不需要项目数据转换；
5. 最终可整 PR revert，不影响 9.0.0 数值与语义体系。

---

# 28. 明确不做

本轮不做：

- 把用户压缩包复制进仓库；
- 把 Matplotlib 代码直接翻译成一一对应 MATLAB 脚本库；
- 为每一种图型建立独立模板文件；
- 改变 MATLAB 只读 accepted evidence 的职责；
- 让 MATLAB 重新计算统计量以“补图”；
- 新建 Figure Project State；
- 新建第二套 palette Authority；
- 修改模型、算法、预处理、求解工作流；
- 改变 LaTeX/DOCX caption-owned title 规则；
- 默认强制导出；
- 默认强制 600 DPI；
- 默认强制雷达图、3D、桑基图或任何高级图；
- 为了追求“图型多样”降低科学表达准确性。

---

# 29. 实施前最终 Gate

真正开始改活动文件前，必须再次确认：

- [ ] 当前 `main` HEAD 未变化，或已基于最新 `main` 重新检查；
- [ ] 没有新的重叠 Figure / MATLAB PR；
- [ ] `core/bootstrap.yaml` 仍指向 `modules/04_figure_evidence.md` 为 figure Authority；
- [ ] 当前 Skill 版本仍与 plan baseline 可解释；
- [ ] 用户已批准本 plan 的范围；
- [ ] 实施目标仍是 9.1.0 minor，而非扩展成 workflow refactor；
- [ ] 不需要 Workbook / State / Model Approval schema 变更；
- [ ] 先做 Authority，再做 helper，再做 template，最后做 release carrier；
- [ ] 每个阶段完成后运行针对性测试；
- [ ] 最终生成索引只由 `scripts/generate_indexes.py` 产生。

---

# 30. 最终预期结果

如果本计划按范围实施，9.1.0 的 Figure 体系应从当前的：

> **科学证据结构选择已经较强，但 MATLAB 最终 rendering 仍较依赖每次手工写样式和排版**

提升为：

> **科学证据决策保持不变 + publication rendering 有稳定 house style + palette/legend/canvas/panel/annotation 有明确条件 + 常见高价值 Figure 有成熟 pattern + MATLAB 入口共享统一 style kernel**

最终目标不是让所有图“长得一样”，而是让不同图在保持科学语义差异的同时具有同一套成熟论文视觉语言，从而明显减少人工移动 legend、换颜色、调字体、拉画布、改 panel 间距和重做基础样式的次数。
