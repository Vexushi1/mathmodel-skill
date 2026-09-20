# 结果图 QA

| 检查项 | 状态 | 备注 |
|---|---|---|
| 数据是否来自本问 accepted 标准工作簿或当前合法数据事实源 |  |  |
| 是否记录源工作表、真实表头和可选固定列位置 |  |  |
| Python 主求解是否保留了本次运行真实产生且有解释/绘图价值的状态、过程或结构数据，而不是只剩摘要 |  |  |
| 03B 若适用，是否保留参数/场景/算法/seed/阈值等细粒度分析证据，而不是只写“稳定” |  |  |
| MATLAB 是否只绘图、不重算核心结果或重新做深化分析 |  |  |
| 是否先识别 Evidence structure，再选择视觉结构 |  |  |
| 核心图是否通过 Basic-form Challenge 检查必要关系与证据覆盖，而未按基础/复合图型判定高低 |  |  |
| 当前结论所需的时间、空间、分布、不确定性、边界或多目标关系是否充分表达，且未为无关维度加图 |  |  |
| Composite Encoding 是否有真实互补信息和可读性增益；同一 x/y 的线与点是否未冒充独立证据 |  |  |
| Scientific Rendering Profile 是否与当前证据结构匹配；未因模式清单虚构区间、拟合或配对 |  |  |
| 若使用 Local Zoom，是否确有局部判别价值且 ROI 与主图对应清楚 |  |  |
| 若使用 Small Multiples，跨面板比较所需坐标尺度是否一致或已明确说明差异 |  |  |
| 若使用 Focus Highlighting，是否保留必要上下文而未选择性隐藏不利对象 |  |  |
| 若使用 Semantic Background，背景是否对应真实阈值、状态或阶段而非装饰 |  |  |
| 若使用 Composite Diagnostic / 3D，是否只有一个一级阅读任务且额外结构确实提高信息效率 |  |  |
| 是否避免为美观对离散点擅自平滑并制造新峰谷/拐点 |  |  |
| 图窗是否默认可见并保留 |  |  |
| 是否避免默认自动导出和关闭 |  |  |
| 正式论文图是否未设置整体 `title` / `sgtitle` |  |  |
| 多面板是否仅按需保留 a/b/c/d 等 panel label，而未重复写总标题 |  |  |
| DOCX/LaTeX caption 是否承担正式图号、图名和必要统计口径 |  |  |
| 中文坐标轴、单位、图例、colorbar 是否按实际需要完整 |  |  |
| 字号、线宽、边框和白底是否符合规范 |  |  |
| 主结果是否采用高对比、中高饱和且语义一致的颜色；强比较是否可优先亮蓝/鲜红 |  |  |
| 辅助对象、CI、背景、参考线是否灰化/浅化/透明度降权，避免全图同时争夺注意力 |  |  |
| 红绿等颜色是否未承担唯一语义，并辅以 marker/linestyle/shape |  |  |
| 是否避免 rainbow/jet 与无序彩虹色图 |  |  |
| 网格是否默认关闭；确需网格时是否足够浅、稀且位于数据后方 |  |  |
| Publication palette profile 是否与对象数量、图型密度和输出介质匹配，而非所有图机械使用同一色盘 |  |  |
| 普通二维数据图是否采用清爽 open-axis / frameless legend；heatmap/3D/polar 等保留 frame 是否有结构理由 |  |  |
| multi-panel 是否保持同一对象颜色/marker/字号语义一致 |  |  |
| legend 是否遮挡核心证据；复杂共享 legend 是否评估 shared / dedicated legend tile |  |  |
| Adaptive Canvas / panel spacing 是否足够容纳标签、legend、annotation、colorbar，且未靠缩小字号硬塞 |  |  |
| bar / stacked bar 的零基线与 y-range 是否诚实；局部差异是否优先用 dot/zoom/detail 而非误导性截轴 |  |  |
| heatmap / performance matrix 的 normalization 与 colorbar 是否真实可比较；列内标准化是否明确标注 |  |  |
| radar 若使用，指标方向、归一化、轴数和对象数是否通过严格准入，且未用 polygon area 作定量结论 |  |  |
| 需要黑白打印/色觉安全时是否有 marker/linestyle/edge/hatch 等次级编码，红绿未承担唯一语义 |  |  |
| caption—工作簿—脚本—结论是否已同步到 `模型论文框架.md` |  |  |
| 是否能绑定正文结论 |  |  |
| Figure Portfolio Gate 是否检查论证覆盖、重复图/面板和跨图一致性，未按 plain 图占比返工 |  |  |
| 是否检查 Missing Scientific Evidence：必要关系是否缺可核对证据；已有图、表和正文充分时不补图，仅补必要视觉缺口 |  |  |

Portfolio Review 按论证覆盖、真实性、可读性和重复程度检查；不设图型数量、复杂度或 F2/F3 占比要求。清楚的简单图可承担核心论证；只有必要关系缺失时才回到数据与 Figure Synthesis。单面板合理时不强加 hero panel 或不对称布局，也不凑第二候选。
