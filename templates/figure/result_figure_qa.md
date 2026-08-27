# 结果图 QA

| 检查项 | 状态 | 备注 |
|---|---|---|
| 数据是否来自本问 accepted 标准工作簿或当前合法数据事实源 |  |  |
| 是否记录源工作表、真实表头和可选固定列位置 |  |  |
| Python 主求解是否保留了本次运行真实产生且有解释/绘图价值的状态、过程或结构数据，而不是只剩摘要 |  |  |
| 03B 若适用，是否保留参数/场景/算法/seed/阈值等细粒度分析证据，而不是只写“稳定” |  |  |
| MATLAB 是否只绘图、不重算核心结果或重新做深化分析 |  |  |
| 是否先识别 Evidence structure，再选择视觉结构 |  |  |
| 正文核心图若为 plain bar/line/scatter/box/histogram，是否完成 Basic-form Challenge |  |  |
| 是否检查时间、空间、分布、不确定性、约束边界、机制、多目标、全局—局部等可用维度是否被错误压扁 |  |  |
| 同一证据空间内是否优先评估 Composite Encoding，如 box+scatter、violin+scatter、line+interval、heatmap+contour |  |  |
| Scientific Rendering Profile 是否与当前证据结构匹配 |  |  |
| 若使用 Local Zoom，是否确有局部判别价值且 ROI 与主图对应清楚 |  |  |
| 若使用 Small Multiples，跨面板比较所需坐标尺度是否一致或已明确说明差异 |  |  |
| 若使用 Focus Highlighting，是否保留必要上下文而未选择性隐藏不利对象 |  |  |
| 若使用 Semantic Background，背景是否对应真实阈值、状态或阶段而非装饰 |  |  |
| 若使用 Composite Diagnostic / 3D，是否仍只有一个一级阅读任务且高级形式确实提高信息效率 |  |  |
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
| caption—工作簿—脚本—结论是否已同步到 `模型论文框架.md` |  |  |
| 是否能绑定正文结论 |  |  |
| Figure Portfolio Gate 是否检查整篇核心图是否大量退化为基础图型 |  |  |
| 是否检查 Missing Scientific Evidence：机制/空间/动态/阈值/分布等核心结论是否缺直接图证据 |  |  |

Portfolio Review 不以“必须 N 种不同图型”为通过标准，而检查基础图是否来自真实简单数据结构，还是因为 Python 丢失状态、Figure Synthesis 被跳过或复杂证据被过度聚合。
