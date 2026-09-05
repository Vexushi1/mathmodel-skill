# Module 04：MATLAB 结果图、预处理图证据与机理图精修

本模块是当前 Figure Evidence 的单一通用 Authority。`packs/artifact/figure.md`、`templates/figure/*.md` 与 MATLAB 模板只能引用或实现这里的规则，不得建立第二套绘图决策权威。

## 正确顺序

进入本模块时先读取 current `模型论文框架.md` 中的当前有效口径、相关小问结果摘要、待办缺口和既有图表映射，用于确定“哪些结论需要图证据”；随后再从真实工作簿读取具体数值和底层序列。不得仅凭聊天记忆或框架摘要数字反推图数据。

1. 继承已经锁定的 `preprocessing_decision`；若为 `project_level`，确认 `数据预处理结果.xlsx` 已 accepted 且预处理质量门通过；
2. Python 完成完整主求解并通过主结果质量门；03A 应已经保存本次主计算真实产生且具有解释/绘图/验证价值的状态、过程与结构证据；
3. Python 基于题目风险完成实际需要的结果深化分析，并验收 `问题X求解/` 中两个标准工作簿；03B 应保存参数、场景、阈值、算法、结构、异质性等分析的细粒度底层证据；
4. 只有上述数值阶段完成后才进入 Figure Evidence；先明确每张图读取原始数据、统一预处理工作簿或两个标准结果工作簿中的哪一种事实源；
5. 若为 `project_level`，此时生成并人工检查 `数据预处理/data_process.m`，只把已验收预处理工作簿中的底层证据转成图；
6. 为每个候选 Figure 先写 Core conclusion、Evidence level、Primary question、Available evidence dimensions；
7. 先执行 **Scientific Figure Synthesis Gate**，识别证据结构并设计候选视觉结构；不得先问“bar 还是 line”；
8. 若候选核心图退化为 plain bar / plain line / plain scatter / plain box / plain histogram，执行 **Basic-form Challenge**；
9. 若多个视觉编码能在同一证据空间互补表达，执行 **Composite Encoding Preference**；
10. 选定视觉结构后进入对应 **Scientific Rendering Profile**；
11. 再通过 Figure Layout Gate 动态选择单图、1×2、2×1、1×3、2×2 或拆分为多张 Figure；不得先决定版式再硬塞证据；
12. 基础布局确定后执行 Figure Enhancement Gate；只有在增加可验证信息、降低视觉搜索成本或强化关键证据时增加 Local Zoom、Small Multiples、Focus Highlighting、Semantic Background、Composite Diagnostic 或 Conditional 3D；
13. 生成 MATLAB 代码前实际读取工作簿，锁定工作簿名、工作表名、真实表头、单位和数据类型；
14. 拟定 DOCX/LaTeX 正式 caption；正式论文图不设置整体 `title` / `sgtitle`，多面板按需只保留 a/b/c/d 等 panel label；
15. 将各问 `q{x}_plot.m` 与两类 Python 脚本、两类结果工作簿放在同一 `问题X求解/`；项目级预处理图脚本固定为 `数据预处理/data_process.m`；
16. 完成单图 QA 后执行 **Figure Portfolio Scientific Quality Gate**，检查整篇核心图是否出现基础图型退化；
17. 检查核心结论是否有图或表证据，并同步 `模型论文框架.md`；
18. 默认只保留图窗供人工检查，不自动创建图表子目录或批量导出图片。

## A 类：机理与推导图

优先表达公式来源、约束来源、临界状态和策略机制。图内只放对象、变量、方向、边界、距离、角度、流向和临界状态，完整推导留在正文。禁止用通用“输入—模型—输出”流程图替代题目专属机理图。

正式机理/推导图采用 **monochrome-first（黑白线稿优先）** 视觉语法：默认白底、黑色或深灰轮廓/箭头/文字，次级结构仅用灰度、线宽、虚实、形状和留白降权；不得用蓝/绿/红等多色填充替代语义结构。只有黑白线型与形状仍不足以区分且确有论证收益时，才允许加入 1 个强调色；极少数复杂图最多 2 个强调色，并必须保证转灰度或黑白打印后仍能无损辨识。

对象表达优先使用与题意实体一致的规则几何图元：圆/椭圆、矩形、三角形、四边形/多边形、圆柱投影、球体的圆形/椭圆轮廓等；几何精度要求高时继续交给 MATLAB / TikZ / GeoGebra。禁止用渐变、阴影、拟物 3D、高饱和色块或无来源图标制造“立体感”；球体、圆柱等三维对象在机理图中优先用可解释的二维投影轮廓和必要辅助线表达。

视觉层级的优先顺序为 `shape / geometry → line style / line width → grayscale → optional accent color`。同一对象和同一机制在全文保持一致的形状与线型；颜色不是默认语义载体。

### Mechanism Diagram Backend Selection Gate

机理图先根据证据结构选后端，不按“哪个工具显得高级”选后端：

| 证据结构 | 首选后端 | 准入理由 |
|---|---|---|
| 题目对象关系、机制作用链、反馈、状态切换、约束来源，且赛中需要快速修改对象/箭头/文字 | draw.io | 离散关系适合可编辑矢量图元 |
| 工作簿驱动的主结果、分布、误差、敏感性、空间场、Pareto 或网络权重 | MATLAB | 数值、坐标、统计量和区间必须来自已验收事实源 |
| 精确二维几何、连续函数、切线、坐标变换或按比例边界 | MATLAB / TikZ / GeoGebra | 需要解析或坐标精度 |
| 简短公式依赖且必须与 LaTeX 字体一致 | TikZ | 直接服从论文公式环境 |
| 临时讨论草图 | PPT / 手绘 | 只能作为草案，入文前转为正式后端 |

draw.io 仅适用于**非数据驱动、题目专属且能绑定模型/公式/约束/判定条件**的机理图。只有通用研究阶段、算法名称或“输入—处理—输出”盒子的图不得作为核心机理图。一个直接二维图已经能更准确证明结论时，应否决 draw.io。

### Editable draw.io 生产链

draw.io 路径按以下状态推进：

```text
current Framework + Mechanism Contract
→ backend selected
→ mechanism_drawio_spec v1
→ deterministic uncompressed .drawio
→ structure_checked
→ preview_rendered
→ visual_reviewed
→ approved_for_paper
→ formal PDF/SVG/PNG + Framework登记
```

执行要求：

1. 先读取 current `模型论文框架.md` 与 `templates/figure/mechanism_contract.md`，恢复题目对象、符号、公式、约束、判断条件和 Core conclusion；具体数值仍只能来自 accepted workbook；
2. 复制 `templates/figure/mechanism_drawio_spec.yaml` 到项目 `figures/source/`，所有节点、边和语义锚点必须题目专属；Spec 只是渲染输入，不是模型或数值事实源；
3. 使用 `scripts/generate_mechanism_drawio.py` 生成确定性的未压缩 XML；生成器不得发明对象、关系、公式、阈值或结论，也不得读取工作簿和求解模型；
4. 使用 `scripts/validate_drawio_figure.py` 检查结构、几何、安全与 hash current 状态；检查结果只表示 `structure_checked`；
5. 打开最新 `.drawio` 或预览图，先执行语义真实性复核，再执行版式复核；未查看最新渲染预览时不得进入 `approved_for_paper` 或 `approved_figures`；
6. 人工通过后按需导出 `figures/qX_<slug>.pdf|svg|png`，同步 Mechanism Contract 与 Framework 图表登记。

项目级建议路径为：`figures/source/qX_<slug>.mechanism.yaml`、`figures/source/qX_<slug>.drawio`、`figures/preview/qX_<slug>.png` 和 `figures/qX_<slug>.pdf|svg|png`。这些路径只在实际选择 draw.io 时创建，不改变每问两个 Python、两个工作簿和一个 `qX_plot.m` 的五文件结构。Spec、`.drawio` 与 preview 默认是内部编辑/复核材料，不自动加入 official package。

### 机器检查与人工审查边界

静态校验器可以检查唯一未压缩 `mxGraphModel`、ID、端点、画布、越界、文字确定性溢出、普通实体实质重叠、明确连线穿盒、外部/位图资源、声明路径与 hash。它**不判断箭头方向是否符合真实机制**，不判断变量、公式、约束、阈值或数学结论是否正确，也不判断是否遗漏关键对象、图是否美观或能否支撑正文 claim。

人工复核必须先确认对象、端点、方向、符号、单位、临界侧、反馈、公式/约束锚点和数值事实源，再确认缩放后的文字、留白、对齐、颜色、端点、交叉和视觉层级。`structure_checked` 绝不等同于 `approved_for_paper`。无法渲染时可以交付 `.drawio` 草稿与结构检查结果，但必须明确等待用户预览，不得宣称机理图已经完成。

### 视觉修改与语义修改分流

移动节点、调整画布/间距/颜色/字体/线宽/圆角、只改变换行、改变不影响端点的连线路径、caption/编号/文件名或导出设置，属于纯视觉/交付修改：不递增模型 `semantic_revision`，不使 `locked_model_spec` stale，也不触发重新 Model Approval、03A 或 03B 重算；但正式图、Framework 登记和引用 hash 仍应刷新。

新增、删除或替换对象/状态/变量，改变边的 source、target、direction、relation type，改变公式、约束、假设、阈值、判定条件、反馈或可行侧，必须与 current Framework 和模型 Authority 比较。若 Framework 正确而图画错，只修图并刷新 Figure Evidence；若图暴露模型/Framework 冲突，则按现有 semantic change category 回退模型设计或求解。draw.io 工具不得自行裁决数学语义。

具体字段、基础图元和 CLI 参考 `templates/figure/mechanism_drawio_spec.yaml` 与 `templates/figure/mechanism_drawio_patterns.md`；它们只实现本节，不拥有独立 Figure 决策权。

## B 类：项目级预处理证据图

当 `preprocessing_decision=project_level` 时，必须生成独立 MATLAB 脚本 `数据预处理/data_process.m`，只读取 `数据预处理/数据预处理结果.xlsx`。其职责是把 Python 已经保存的处理前/后、诊断和验证底层数据转成论文证据图。MATLAB 不允许重新清洗、插值、滤波、重采样、预测填补、训练模型或重新确定参数。

至少有一张图直接回答下列问题之一：为什么原始数据需要处理；当前处理是否解决已审计问题；插值/填补恢复误差是否可接受；滤波是否保留所需信息；重采样/时间/空间对齐是否满足模型输入；异常处理是否有清晰边界并避免误删真实结构。

优先考虑处理前后时序/轨迹/空间场、缺失与恢复、分布 + 原始点、真实值—恢复值 + 误差、频谱、重采样覆盖、阈值边界等证据。正式图同样执行 Synthesis、Basic-form Challenge、Rendering Profile、Layout 与 Enhancement；不能因为是预处理图就默认画两根柱或两条普通折线。

## C 类：各问结果图合同

每张结果图至少记录：Core conclusion、Evidence level、Primary question、Figure role、Available evidence dimensions、Evidence structure、Figure level、Candidate visual structures、Selected visual structure、Basic-form challenge、Composite encoding、Scientific Rendering Profile、In-figure title=`none`、论文 caption、Panel map、Layout decision、Split decision、Enhancement、Enhancement rationale、Source workbook、Worksheet、Required headers、Expected positions（可选）、MATLAB script、Statistics/error、Reviewer risk、Paper location 和 Caption duty。

结果证据优先来自本问标准工作簿：

- 主结果、决策变量、状态轨迹、空间/网络状态、预测明细、基础误差和主质量证据来自 `问题X求解结果.xlsx`；
- 参数、场景、算法、结构、阈值、异质性和稳定范围证据来自 `问题X结果深化分析.xlsx`。

只有图本身确实需要底层数据时，才按 `preprocessing_decision` 追加数据事实源：

- `not_needed`：允许读取必要原始数据；
- `question_local`：允许读取必要原始数据，但不得在 MATLAB 中重新构造模型变换；若局部处理需要图证据，应由 Python 将处理前后底层数据写入本问工作簿；
- `project_level`：各问需要底层公共数据时读取 `数据预处理结果.xlsx`，不得绕回共享原始附件。

不得为了统一脚本结构而强制所有 `q{x}_plot.m` 读取统一预处理工作簿。不得在 MATLAB 中重新求解、重新做敏感性/统计分析或从摘要数字反推绘图序列。

## Figure Evidence 层级

```text
L1 主结果证据       → 直接回答本问主要数值/结构结论
L2 机制或异质性证据 → 解释结论为何发生、发生在哪里、对谁成立
L3 稳健性证据       → 敏感性、阈值、场景、多算法、结构稳定范围
L4 数值合法性证据   → 收敛、频带、残差、可行性、预处理有效性等方法后盾
```

同一 Figure 可以包含多个 panel，但默认应属于同一 Evidence level 并共同回答一个 Primary question。跨层级合图只有在必须同屏直接比较、或多个统计视角共同完成同一可信度判断且拆分会明显损失证据关系时才允许，并须在 Figure Contract 中说明原因。

## Scientific Figure Synthesis Gate：从证据结构设计 Figure

正式绘图前先识别 Evidence Structure，而不是从软件默认函数反推图型。至少检查：

- 简单离散比较；
- 分布；
- 时间演化；
- 空间结构；
- 机制关系；
- 约束边界 / 可行域；
- 参数响应 / 参数交互；
- 不确定性；
- 多目标权衡；
- 稳定 / 风险 / 失效区域；
- 网络流；
- 调度与资源占用；
- 模型诊断；
- 全局—局部结构。

每个候选核心图至少比较两种合理视觉结构，选择依据是：能否揭示模型结构、是否保留真实数据粒度、是否提高可验证信息密度、是否降低评委搜索成本、是否更直接支撑当前 Core conclusion。高级不是复杂；若一个直接二维图已经完整表达本题结构，不能为了“高级感”强行 3D 或堆编码。

## Basic-form Challenge：基础图只在信息结构确实简单时保留

plain bar / barh、plain line、plain scatter、plain boxplot、plain histogram 允许使用，但默认属于 F1 基础表达。若它们准备进入正文核心 Figure，必须检查当前 accepted 数据是否还包含：

- 时间或空间结构；
- 原始样本分布；
- 不确定性/误差；
- 约束、可行域或临界边界；
- 机制变量；
- 参数交互；
- 多目标关系；
- 全局—局部差异；
- 关键事件、阈值或策略切换。

只要存在这些结构且能提高可验证信息密度，就优先升级表达。**不禁止柱状图，但禁止明明有更丰富证据，却只用一个普通柱状图结束核心结论。**

### Figure 表达等级

- **F1 基础表达**：普通柱状、条形、折线、散点、箱线、直方；适合真正的一维简单事实、辅助图和附录；
- **F2 增强科研表达**：box + raw scatter、violin + raw scatter + median/quartile、line + uncertainty band、scatter + fit/identity + CI、scatter + marginal histogram/KDE、bar + errorbar + benchmark、heatmap + contour、ECDF + quantile、Gantt + resource utilization、network + weighted flow、Pareto + highlighted recommendation；
- **F3 核心科学综合图**：spatial field + trajectory + boundary + critical state；Pareto + feasible/infeasible + knee + recommendation + zoom；response surface + contour + stable/failure region + current point；prediction relation + uncertainty + residual/marginal diagnostic；candidate cloud + constraint structure + recommendation。

F2/F3 的“高级”来自证据结构和联合解释，不来自装饰数量。

## Composite Encoding Preference：同一证据空间优先融合互补编码

若多种视觉编码共同回答同一个 Primary question，且共享同一坐标/统计语义，优先融合，而不是拆成多个低信息密度单图。重点支持：

```text
箱线 + 原始散点
小提琴 + 原始散点 + 中位数/四分位
折线 + CI/预测区间
散点 + 拟合/1:1线 + CI
散点 + 边际直方图/KDE
柱状 + 误差棒 + 基准线
柱状 + 折线（只有联合语义清楚时）
热力图 + 等高线
热力图 + 阈值/可行边界
3D surface + 2D contour projection
Pareto + 推荐点 + Local Zoom
轨迹 + 空间场 + 边界
真实—预测 + 区间 + 残差/边际结构
```

柱状 + 折线、双 Y 轴等组合只有在指标关系明确、量纲和阅读任务清楚时才允许；不得为了“显得高级”把互不相关指标强行叠加。

## Scientific Rendering Profiles：选定视觉结构后的专属科研表达

### Distribution Profile

优先让 raw samples 可见；根据样本量和分布目标选择 box/violin + scatter、ECDF + quantile 或 histogram/density + raw context。KDE 样本不足或带宽会误导时改用 ECDF、直方或原始点。

### Regression / Prediction Profile

优先组合 observed-vs-predicted / scatter、identity 或合法 fit line、CI/prediction interval、residual 或 marginal 结构。训练/测试可用颜色 + marker/linestyle 联合编码；只保留直接支撑可信度判断的少量统计量。

### Dynamic Profile

优先 trajectory/state curve + uncertainty（真实存在时）+ event/threshold + critical point；关键窗口被全局尺度压缩时使用 Local Zoom / Global–Detail；阶段背景只有真实状态/阈值语义时才使用。

### Parameter Surface Profile

双参数有完整响应网格时优先 heatmap + contour + current/recommended point + feasible boundary。只有第三维确有数学/物理意义且二维投影会丢失关键结构时，才使用 3D surface + contour projection + colorbar。

### Spatial Profile

优先 spatial field + path/flow + critical nodes + boundary + colorbar；关键对象可以 Focus Highlighting，但不得隐藏不利区域。

### Optimization / Pareto Profile

优先 candidate solutions + Pareto set/front + feasible/infeasible state + recommendation + knee/threshold + global/detail。只画“算法 A/B/C 三根柱”通常不足以承担优化核心证据。

### High-density Scatter Profile

点严重遮挡时按真实数据规模考虑 alpha scatter、binned/hexbin density、2D histogram、density contour；不得让大样本散点退化成不可读色块。

## Figure Layout Gate：单图 / 1×2 / 2×2 动态判断

**不存在固定默认版式。** 先做 Scientific Figure Synthesis，再根据证据关系决定布局。

### 1. 单图

优先使用单图，当满足任一条件：一个二维/组合图已经完整回答 Primary question；第二 panel 只是重复趋势；增加 panel 不改变结论强度、边界或机制解释；单图配合正文一句解释更清楚。

### 2. 1×2 或 2×1

两个证据单元强配对、互补或前后关系时使用，例如 A vs B、主结果 vs 残差、连续变化 vs 分布总结、处理前 vs 后、全局 vs 局部。横向比较优先 1×2；长 y 标签或栏宽限制时可 2×1。

### 3. 1×3

只有三个 panel 形成不可拆同一序列时使用，例如三阶段演化、基准—改进—误差。第三 panel 属于不同证据层级或可独立解释时应拆图。

### 4. 2×2

只有同时满足以下条件才保留：四个 panel 服务一个 Core conclusion；存在清楚的 2×2 对称/交叉/配对结构；主要视觉编码原则上不超过 2 类；拆成两个 1×2 会显著损失直接比较；每个 panel 不可替代；一个主 caption 句可以统领全部 panel。**任一条件不满足，优先拆成两个 1×2**、单图 + 1×2 或其他更轻结构。

### 5. 超过 4 个 panel

正文核心 Figure 原则上不超过 4 个 panel。只有地图阵列、参数矩阵、时序快照、共享坐标 small multiples 等“多 panel 本身就是研究对象/比较矩阵”的情形可以例外，并保持统一视觉语法和尺度规则。

### 6. 动态判定顺序

```text
先问：单图能否闭合核心结论？
  ├─ 能 → 单图
  └─ 不能
      ↓
两个 panel 是否形成强配对/互补？
  ├─ 是 → 1×2 或 2×1
  └─ 否
      ↓
三个 panel 是否属于不可拆的同一序列？
  ├─ 是 → 1×3
  └─ 否
      ↓
四个 panel 是否同时通过 2×2 六项条件？
  ├─ 是 → 2×2
  └─ 否 → 按 Primary question / Evidence level 拆成多张 Figure
```

评委阅读效率优先：每张 Figure 应让读者在数秒内知道比较对象、主要差异和下一步该看哪里。

## Figure Enhancement Gate：焦点—上下文信息增强

Figure Enhancement 发生在 Synthesis、Rendering Profile 和基础布局确定之后。默认状态为 `none`；只有增强后能增加可验证信息、降低视觉搜索成本或强化关键证据时才启用。具体实现模式参考 `templates/figure/figure_enhancement_patterns.md`。

### 1. Local Zoom

关键差异、交点、临界阈值、Pareto 膝点、残差尾部或局部波动被全局尺度压缩时可使用。主图必须保留全局上下文，ROI 与 zoom 必须可追溯；可使用 Embedded inset、Detached zoom、Selective detail 或 ROI + semantic zoom。不得通过任意截轴夸大差异。

### 2. Small Multiples

多条曲线大量交叉、遮挡或 legend 搜索成本过高时优先分面。跨 panel 比较幅度时保持统一 `xlim/ylim`；只比较各自形态才允许自由 y 轴，并在 caption 说明。必要时采用 overview + detail。

### 3. Focus Highlighting

对象很多但核心判断只依赖少量对象时，核心对象用高对比主色和主线宽，基准/上下文对象用灰色、浅色、细线或透明度降权；不得选择性隐藏不利对象。

### 4. Semantic Background

稳定区、风险区、可行区、临界区或阶段区间可以使用浅色背景，但必须对应真实数学阈值、题面状态或可解释阶段；纯装饰背景禁止。

### 5. Composite Diagnostic

多个 axes 从中心关系、边际结构与诊断结构共同回答同一 Primary question 时允许非规则 Figure geometry。例如真实—预测散点 + 边际分布 + residual。**一张 Figure 可以包含多个 axes**，但只能承担一个一级阅读任务。

### 6. Conditional 3D

3D 曲面、可行域、空间场只有在第三维具有真实数学/物理意义且二维投影损失关键结构时才准入。普通分类比较不得为了高级感立体化。3D 造成遮挡、尺度误判或精确比较困难时优先降级为 heatmap、contour、2D slices 或排序图。

### 7. 数据诚实与增强边界

对离散实验点、独立场景点、参数扫描点或迭代记录，**不得仅为了美观使用 spline**、Bezier 等平滑制造新的峰值、谷值或拐点；只有对象本身是连续函数、模型定义连续响应或 Python 已输出连续预测网格时才允许连续平滑。关键标注通常只保留极值、交点、阈值、推荐点等 3--5 个不可替代位置。

## 视觉注意力预算

- 一张 Figure 原则上只有 1 个一级 Core conclusion / 一级阅读任务；
- **同一视觉层级中同时竞争注意力的主要对象通常不超过 2--3 个**；对象更多时优先分组、small multiples、focus highlighting 或拆图；
- 主要视觉编码原则上不超过 2 类；Composite Diagnostic 可有多个 axes，但共享同一 Primary question；
- 主色可以高对比、中高饱和，但真正竞争注意力的主对象通常不超过 2--3 个；辅助对象必须灰化、浅化或透明；
- 信息密度可以高，但读者不应在不同 panel 反复学习新的颜色、线型和指标语法。

## 实表读取规则

正式脚本必须：

1. 使用已核对的真实工作簿名、工作表名和表头；
2. 读取第一行原始表头并做空白归一化；
3. 对每个要求字段执行精确相等匹配，并断言只出现一次；
4. 可登记期望列号，当实际位置变化时给出结构漂移警告；
5. 禁止模糊匹配、别名词典、相似字段猜测和自动回退；
6. 工作簿变化后重新读取并更新 Figure Contract；
7. 检查文件、工作表、非空、主键、非法值和排序。

```matlab
headers = strtrim(string(raw(1, :)));
xMatches = find(headers == xHeader);
assert(numel(xMatches) == 1, "字段缺失或重复: %s", xHeader);
xColumn = xMatches(1);
if isfinite(expectedXColumn) && xColumn ~= expectedXColumn
    warning("字段%s由第%d列移动到第%d列", xHeader, expectedXColumn, xColumn);
end
```

## 图题、配色与风格

正式论文图不设置整体 `title` 或 `sgtitle`。DOCX/LaTeX caption 承担正式图号、图名与必要统计口径；多面板按需只保留 a/b/c/d 等 panel label，坐标轴、单位、图例、阈值线和必要直接标注用于读图。若本地探索阶段临时加调试标题，进入正式 `figures` 交付前必须移除。

默认白底、清晰细轴、中文坐标轴和单位、字号 18，网格关闭；确需网格时必须浅、稀并置于数据后方。主结果恢复**高对比、中高饱和**科研主色，优先让评委第一眼识别关键对象；辅助元素保持克制。此处高对比科研配色针对数据驱动结果 Figure；A 类正式机理/推导图优先遵循前述 monochrome-first 规则，不自动继承蓝/红/绿/橙/紫主色。

```text
亮蓝   #1478FF   RGB [20,120,255]
鲜红   #F04444   RGB [240,68,68]
亮绿   #16B364   RGB [22,179,100]
亮橙   #F79009   RGB [247,144,9]
亮紫   #7A5AF8   RGB [122,90,248]
深灰   #252B37   RGB [37,43,55]
浅灰   #E9EAEB   RGB [233,234,235]
```

配色动态规则：

- 两对象强比较优先 **亮蓝 vs 鲜红**；
- 正向/改善/可行可使用亮绿，风险/恶化优先鲜红；第三、第四主对象可使用亮橙、亮紫；
- 主结果、推荐方案、关键曲线和临界点可以使用高对比实体色；背景、参考线、CI、次要对象和上下文用深灰/浅灰/透明度降权；
- 同一对象和同一语义一旦建立颜色映射，全文保持一致；
- 红绿不得承担唯一语义，需配合 marker、linestyle、shape 或明暗；
- 禁止 rainbow、jet、HSV 无序彩虹和无语义的高饱和渐变；
- 连续场使用与物理量语义匹配的 sequential colormap，正负偏差/相对基准使用 diverging colormap，并保留完整 colorbar 与单位；
- 高对比 ≠ 全图所有元素都鲜艳。若所有元素同时争夺注意力，说明视觉层级失败。

图窗默认可见，不批量自动导出。

## Figure Portfolio Scientific Quality Gate

进入 DOCX/LaTeX 前，对正文核心 Figure 集合做论文级复审。如果出现大量 plain bar / plain line / plain scatter / plain box 等，即使每张单独没有技术错误，也必须检查：

1. Python 主求解是否只输出摘要而丢失本次运行已经产生的状态、轨迹、空间、约束或逐样本证据；
2. 03B 是否只输出“稳定”等摘要而未保留参数/场景/seed/算法/阈值底层记录；
3. 是否存在时间、空间、分布、边界、机制、不确定性或多目标结构却被压成一维比较；
4. 是否跳过 Scientific Figure Synthesis / Basic-form Challenge / Rendering Profile；
5. 是否可以通过 Composite Encoding、Global–Detail、Local Zoom 或合理拆图提高证据表达；
6. 是否有核心机制、空间、动态、阈值或不确定性结论只有文字/表格而缺直接 Figure 证据。

不得设置“必须有 N 种图型”的机械多样性指标。多张基础图只有在数据结构本身确实都是简单一维比较时才合理；不能为了多样性强行雷达图、桑基图或 3D。

## Missing Scientific Evidence Check

不按章节字数或图文比例机械补图，而按核心结论检查：核心机制是否无图；空间结构是否只有汇总数；动态过程是否被压成最终值；关键阈值/边界是否无直接视觉证据；重要分布/不确定性是否只报均值；主结果是否只有表格而明显存在更有效的科研图表达。只有存在真实证据源时才补图，不编造数据。

## 分析图准入

结果深化分析不是每种方法都要画图。只有分析方法与风险来源匹配、图能展示稳定范围/阈值/算法一致性/结构差异/异质性、底层数据完整写入分析工作簿且图能支撑正文核心判断时才入图。统一扰动曲线、无解释的算法柱状图和只展示“结果变化不大”的装饰图删除。

## 入文闭环

预处理图后正文必须解释原始问题、处理机制、关键参数、验证误差或信息保留情况，以及处理后数据为何可以进入后续模型；结果图后解释趋势、关键数值、机制、稳定范围或失效边界。正式图片进入 LaTeX 时按需人工导出。
