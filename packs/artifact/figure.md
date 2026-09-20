# Artifact Pack：图表

## 进入条件

用户要求结果图、敏感性图、鲁棒性图、多算法图、机理图或 MATLAB 代码时加载。图表必须服务明确结论，不以复杂图型、固定版式或面板数量替代证据。

本 Pack 只做阶段摘要，不重新定义 Figure Evidence 规则。Scientific Figure Synthesis、Basic-form Challenge、Composite Encoding、Scientific Rendering Profiles、布局、证据层级、数据事实源、Figure Enhancement Gate、配色、Portfolio Gate 和 Figure Contract 的**唯一权威为 `modules/04_figure_evidence.md`**；每问文件是否存在只服从 `core/output_contract.yaml` 与 current project state。若本文件与这些 Authority 不一致，以 Authority 为准。高级增强的实现模式集中在 `templates/figure/figure_enhancement_patterns.md`，该模板只提供实现参考，不拥有独立决策权。

## 数据前置条件

正式结果图从本问 `问题X求解/` 的 current 合法工作簿集合读取：

- `问题X求解结果.xlsx`：主结果、当前运行真实产生的状态/过程/结构证据、题型专项结果和主结果质量门；主结果图的必需事实源；
- `问题X结果深化分析.xlsx`：仅当 Analysis Necessity Gate=`required` 且 03B 已实际执行、验收时存在，保存分析设计、参数/场景/算法/阈值/异质性等细粒度深化数据和结论稳定性汇总。

Gate=`not_required` 且有非空理由时，缺少 03B workbook 是合法状态，Figure 不得因此失败，也不得据此生成敏感性、稳健性或替代算法一致性图。若某张 Figure 的 Figure Contract 明确声明消费 03B evidence，则该 workbook 必须真实存在且 current；缺失时 fail closed，不允许回退主工作簿伪装深化证据。

只有图本身确实需要底层事实源时，才继承当前 `preprocessing_decision` 追加数据：

- `not_needed`：允许读取必要原始数据；
- `question_local`：允许读取必要原始数据，但 MATLAB 不得重新构造局部模型变换；该变换若需图证据，必须由 Python 先把处理前后底层数据写入本问工作簿；
- `project_level`：需要公共底层数据时读取 `数据预处理结果.xlsx`，禁止绕回对应共享原始附件。

深化分析方法只在 Gate=`required` 时根据具体风险选择，可包括参数敏感性、阈值与失效边界、场景压力测试、多算法一致性、结构稳健性、异质性和误差分解。未执行某类分析时不得生成对应占位图；深化分析要求回退重算时不得继续绘图。

## MATLAB 规则

- 每问入口统一为 `问题X求解/qX_plot.m`；通用模板记为 `q{x}_plot.m`；
- 生成代码前确认真实工作簿名、工作表、表头、单位和数据类型；
- 字段定位采用精确表头唯一匹配，列号只作结构漂移警告；
- 禁止模糊匹配、别名猜测、自动回退和在 MATLAB 中重新求解/重新做深化分析；
- 先执行 `modules/04_figure_evidence.md` 的 Scientific Figure Synthesis，识别时间、空间、分布、边界、机制、不确定性、多目标等 Evidence Structure；
- 核心 Figure 执行 Basic-form Challenge，检查必要关系是否充分表达；清楚的 plain bar / line / scatter / box / histogram 可直接承担核心论证，F1/F2/F3 标签不作质量排序；
- 同一证据空间内仅在真实互补信息和可读性增益同时存在时采用 Composite Encoding；同一数据的线与点不是独立证据，没有实际区间不画带；
- 选定视觉结构后进入对应 Scientific Rendering Profile，再通过 Figure Layout Gate 动态选择单图、1×2、2×1、1×3、2×2 或拆图；不存在固定默认版式；
- 基础布局后按 Figure Enhancement Gate 判断是否需要 Local Zoom、Small Multiples、Focus Highlighting、Semantic Background、Composite Diagnostic 或 Conditional 3D；默认不增强；
- 一张 Figure 原则上只承担一个一级 Core conclusion / 一级阅读任务；不同 Evidence level 默认不混装，必要联合诊断仍须共享同一 Primary question；
- 正式论文图不设置整体 `title` / `sgtitle`；DOCX/LaTeX caption 承担正式图号和图名，多面板按需只保留 a/b/c/d 等 panel label；
- 数据驱动结果 Figure 的配色与排版只服从 Module 04 的 Publication Rendering Grammar：不设默认色板；SCI / Nature 论文可作逐图参考，不代表官方统一配色；`competition_high_contrast`、`journal_balanced`、`monochrome_print` 只保留为显式兼容候选；
- 相同对象和相同语义全文一致，categorical / sequential / diverging 按变量类型选择；脚本显式配置 RGB / colormap，并为灰度与色觉辨识辅以线型、marker 等；禁止 rainbow/jet 与无序彩虹；
- 颜色、字号、线宽、网格与边框按图选择，集中配置供人工调整；基础样式在对象和标签齐备后只调用一次，再做局部覆盖。没有 profile 时仅应用基础排版，不自动取色或改色；
- 默认只保留图窗，不创建图表子目录，不自动批量导出。

进入论文阶段后，人工确认并按需导出的正式图片放在项目级 `figures/`。每张图的结论、Evidence level、Primary question、Evidence structure、Figure level、Selected visual structure、Composite encoding、Rendering Profile、布局、Enhancement、源工作簿、工作表、真实表头、脚本、论文 caption 和正文位置登记在 `模型论文框架.md`，不额外生成证据 YAML。

## Portfolio 级质量门

Figure Portfolio Scientific Quality Gate 检查整篇核心论证的图/表覆盖、必要证据缺口、跨图一致性以及重复图和 panel；不按 plain 图数量或占比判断质量。只有当前判断所需关系缺失时，才回查主求解 Evidence Capture、已激活的深化分析底层记录和 Synthesis/Rendering 的选择理由。

不设图型种类、复杂度或 F2/F3 占比配额。清楚的简单图可完整承担核心论证；候选只有一种时不凑第二种，单面板合理时不强制 hero panel、多面板或不对称布局。

## 信息效率与删除规则

高级图表准入检查的标准不是“看起来复杂”，而是是否增加可验证信息、揭示模型结构或降低阅读成本。局部放大、分面、联合诊断和 3D 等增强只有在实际增益存在时才保留。饼图、雷达图、3D 曲面和复杂网络图必须通过高级图表准入检查，否则降级或删除。统一扰动模板、无通过标准、只说明“变化不大”、从摘要手工录入数据或无法支持正文判断的图全部删除。

## 机理图

机理图服务公式来源、约束来源、对象关系、临界状态和策略机制。图中只保留对象、变量、方向、边界、距离、角度和临界状态，完整解释放正文。禁止通用“输入—模型—输出”流程图替代题目专属图。

正式机理图服从 Module 04 的 **monochrome-first** 规则：白底、黑/深灰线条和文字为主，灰度、线型、线宽与规则几何形状承担主要区分；默认不使用蓝/绿/红多色语义填充。只有确有证据增益时才允许 1 个强调色，极少数复杂图最多 2 个，并须保证黑白打印仍可辨识。对象优先画成圆/椭圆、矩形、三角形、四边形/多边形、圆柱投影、球体轮廓等题意一致的规则几何图形，禁止渐变、拟物阴影和装饰性 3D。

需要可编辑的非数据驱动对象关系、约束关系、反馈或临界状态图时，先按 `modules/04_figure_evidence.md` 的 Mechanism Diagram Backend Selection Gate 判断是否进入 draw.io 路径。选中后读取 `templates/figure/mechanism_contract.md` 与 `templates/figure/mechanism_drawio_spec.yaml`；只有实际生成或返修 draw.io 时再读取 `templates/figure/mechanism_drawio_patterns.md`。数据、坐标、误差、区间与工作簿结果仍由 MATLAB 路径负责。

draw.io 的 `Spec → generate → validate → preview → semantic/visual QA → export` 只是一条实现链。静态检查通过不表示箭头、公式或机制正确；没有查看最新渲染预览时不得把图登记为 `approved_figures`。
